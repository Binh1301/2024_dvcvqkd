"""Optimistic source-backed HAP-UAV VA=2 diagnostic benchmark."""

from __future__ import annotations

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import sys
import tempfile
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    _untruncated_moment,
    analyze_product,
    derive_physical_inputs,
)
from scripts.run_effective_channel_va2 import physical_channel_parameters
from src.channel.atmospheric_loss import atmospheric_transmittance
from src.channel.phase_noise import phase_parameter_provenance
import src.cvqkd.holevo as holevo_module
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator


VA = 2.0
BETA = 0.95
THETA_DIV = 33e-6
APERTURE_RADIUS = 0.10
SIGMA_H = 0.10
SIGMA_HAP_ANG = 1e-6
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
L_KM = tuple(17.0 + 0.5 * index for index in range(15))
SOURCE = {
    "uniform": (
        "1.4019995788968011700681192152159252514555640211395",
        "0.026543338228713932540445642845440478987301227896247",
        None,
    ),
    "binomial": (
        "1.41414750131106445213245972871615156498",
        "1.13331366963443032864740272931418486e-4",
        None,
    ),
    "mb": (None, None, 0.20),
}


def _forbidden(*_args, **_kwargs):
    raise RuntimeError("Optimistic benchmark reached a forbidden AP/full-Z path.")


def _load_mb_source(ensemble) -> tuple[str, str, dict]:
    checkpoint = Path(tempfile.gettempdir()) / "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json"
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    rows = payload["rows"]
    final = rows[-1]
    if not final["resolved"] or Decimal(final["C"]) != Decimal("1.4142135560377151402791686003423073594184222417457"):
        raise RuntimeError("The validated nu=0.20 checkpoint is not the expected source reference.")
    return final["C"], final["w"], {
        "checkpoint": str(checkpoint),
        "accepted_precision_pair": [rows[-2]["digits"], rows[-1]["digits"]],
        "worst_log10_kappa": max(
            float(s["log10_kappa"])
            for row in rows[-2:]
            for s in row["sector_diagnostics"]
        ),
        "source_runtime_seconds": sum(float(row["runtime_seconds"]) for row in rows),
    }


def _channel(config: dict, link_m: float) -> tuple[dict, dict, dict]:
    h_uav = float(config["channel"]["h_uav_m"])
    wavelength = float(config["channel"]["wavelength_m"])
    visibility = float(config["channel"]["visibility_km"])
    eta_atm = atmospheric_transmittance(link_m, visibility, wavelength)
    physical = derive_physical_inputs(
        h_hap_m_override=h_uav + link_m,
        eta_atm_override=eta_atm,
        beam_waist_m_override=2.0 * wavelength / (math.pi * THETA_DIV),
        theta_div_rad_override=THETA_DIV,
        aperture_radius_m_override=APERTURE_RADIUS,
        sigma_h_m_override=SIGMA_H,
        sigma_hap_ang_rad_override=SIGMA_HAP_ANG,
    )
    analysis = analyze_product(physical["v_sc"], physical)
    phase_config = config["channel"]["phase_noise"]
    phase = phase_parameter_provenance(
        phase_config["cn2_phase_m_minus_two_thirds"],
        physical["wavelength_m"],
        phase_config["l_phase_m"],
    )
    moments = analysis["moments"]
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"],
        float(physical["epsilon_base_snu"]),
        phase["c_phi"],
        VA,
    )
    return physical, phase, {"analysis": analysis, "security": security}


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    output_dir = ROOT / "results" / "optimistic_hapuav_va2"
    output_dir.mkdir(parents=True, exist_ok=True)
    ensembles = {
        scheme: reference_ensemble(
            scheme,
            batch_size=1,
            modulation_variance=VA,
            nu_mb=nu,
            v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        )
        for scheme, (_, _, nu) in SOURCE.items()
    }
    mb_c, mb_w, mb_source_meta = _load_mb_source(ensembles["mb"])
    source = {
        "uniform": (SOURCE["uniform"][0], SOURCE["uniform"][1]),
        "binomial": (SOURCE["binomial"][0], SOURCE["binomial"][1]),
        "mb": (mb_c, mb_w),
    }
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    rows = []
    channel_rows = []
    for L_km in L_KM:
        physical, phase, channel = _channel(config, L_km * 1000.0)
        security = channel["security"]
        sigma_hap_footprint = L_km * 1000.0 * SIGMA_HAP_ANG
        expected_sigma_m = math.sqrt(SIGMA_H ** 2 + sigma_hap_footprint ** 2)
        if not math.isclose(physical["sigma_m"], expected_sigma_m, rel_tol=0.0, abs_tol=1e-12):
            raise RuntimeError("Optimistic HAP residual-jitter geometry check failed.")
        hsc_mean = 1.0
        hp_mean = _untruncated_moment(1.0, physical["v_sc"], physical) / physical["eta_atm"]
        channel_rows.append({
            "L_km": L_km,
            "h_HAP_m": physical["h_hap_m"],
            "eta_atm": physical["eta_atm"],
            "w0_m": physical["pointing"]["omega_0_m"],
            "wL_m": physical["pointing"]["beam_radius_receiver_m"],
            "wL_eq_m": physical["pointing"]["omega_L_eq_m"],
            "sigma_h_m": SIGMA_H,
            "sigma_hap_footprint_m": sigma_hap_footprint,
            "sigma_m": physical["sigma_m"],
            "A0": physical["pointing"]["eta_p0"],
            "E_Hp": hp_mean,
            "mean_eta": channel["analysis"]["moments"]["mean_eta"],
            "mean_sqrt_eta": channel["analysis"]["moments"]["mean_sqrt_eta"],
            "T": security["T"],
            "epsilon": security["epsilon"],
            "c_phi": phase["c_phi"],
        })
        for scheme, (c_text, w_text) in source.items():
            ensemble = ensembles[scheme]
            t = torch.tensor([security["T"]], dtype=torch.float64)
            epsilon = torch.tensor([security["epsilon"]], dtype=torch.float64)
            c = torch.tensor([float(c_text)], dtype=torch.float64)
            w = torch.tensor([float(w_text)], dtype=torch.float64)
            mi_values = []
            for seed in MI_SEEDS:
                mi_values.append(float(discrete_mutual_information(
                    ensemble, t, epsilon,
                    noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
                    standard_noise_samples=noises[seed],
                )[0]))
            mi = sum(mi_values) / len(mi_values)
            holevo = _holevo_from_source_moments(
                ensemble, t, epsilon,
                coherent_correlation=c,
                w_raw=w,
                tau=None,
                tau_trace=ensemble.probabilities.sum(dim=-1),
                require_supported_symmetry=True,
                symmetry_tolerance=1e-8,
                physicality_tolerance=1e-10,
                maximize_full_interval=False,
                diagnostics={
                    "backend": "optimistic_hapuav_va2",
                    "source_moment_recomputed": False,
                    "phase_noise_already_in_epsilon": True,
                },
            )
            chi = float(holevo.chi_be[0])
            rows.append({
                "L_km": L_km,
                "scheme": scheme,
                "C": c_text,
                "w": w_text,
                "I_AB": mi,
                "Z_star": float(holevo.z[0]),
                "chi_BE": chi,
                "beta_I_AB": BETA * mi,
                "K_raw": BETA * mi - chi,
                "physicality_pass": min(float(holevo.covariance.lambda1[0]), float(holevo.covariance.lambda2[0]), float(holevo.covariance.lambda3[0])) >= 1.0 - 1e-10,
                "holevo_mode": holevo.diagnostics["mode"],
            })
    fields = list(rows[0])
    with (output_dir / "optimistic_hapuav_va2.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "artifact": "OPTIMISTIC_SOURCE_BACKED_HAP_UAV_VA2",
        "scenario_label": "optimistic source-backed HAP-UAV benchmark with nonzero residual HAP fine-pointing error",
        "changed_values": {
            "theta_div_rad": THETA_DIV,
            "receiver_aperture_radius_m": APERTURE_RADIUS,
            "sigma_h_m": SIGMA_H,
            "sigma_hap_ang_rad": SIGMA_HAP_ANG,
            "theta_jt_rad": SIGMA_HAP_ANG,
            "nu_MB": 0.20,
        },
        "unchanged_values": {
            "wavelength_m": float(config["channel"]["wavelength_m"]),
            "visibility_km": float(config["channel"]["visibility_km"]),
            "beta_rec": BETA,
            "VA": VA,
            "h_UAV_m": float(config["channel"]["h_uav_m"]),
            "zenith_angle_rad": 0.0,
        },
        "source_moment_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "mb_source": mb_source_meta,
        "channel_rows": channel_rows,
        "rows": rows,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output_dir / "optimistic_hapuav_va2.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "runtime_seconds": time.perf_counter() - started,
        "rows": len(rows),
        "output_dir": str(output_dir),
        "K_min": min(row["K_raw"] for row in rows),
        "K_max": max(row["K_raw"] for row in rows),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
