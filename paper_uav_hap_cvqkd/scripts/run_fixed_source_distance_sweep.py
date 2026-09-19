"""Distance sweep for validated fixed VA=2 source moments."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    analyze_product,
    derive_physical_inputs,
)
from src.channel.atmospheric_loss import (
    atmospheric_transmittance,
    extinction_coefficient_per_km,
    kruse_q,
)
from scripts.run_effective_channel_va2 import (
    physical_channel_parameters,
)
from src.channel.phase_noise import phase_parameter_provenance
import src.cvqkd.holevo as holevo_module
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator


VA = 2.0
BETA = 0.95
MB_NU = 0.1
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
    "mb": (
        "1.4141975446461088728099397679159500271185396830827",
        "3.5382188425273695384131484143796774042381888693943e-5",
        MB_NU,
    ),
}
SCHEMES = tuple(SOURCE)
COLORS = {"uniform": "#4C78A8", "binomial": "#F58518", "mb": "#54A24B"}
LABELS = {"uniform": "Uniform", "binomial": "Binomial", "mb": "Fixed MB"}
ANCHOR = {
    "T": 2.990280293659837e-4,
    "epsilon": 0.026571745339178013,
}


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _channel_at_distance(config: dict, link_m: float) -> tuple[dict, dict, dict]:
    h_uav = float(config["channel"]["h_uav_m"])
    wavelength_m = float(config["channel"]["wavelength_m"])
    visibility_km = float(config["channel"]["visibility_km"])
    eta_atm = atmospheric_transmittance(link_m, visibility_km, wavelength_m)
    physical = derive_physical_inputs(
        h_hap_m_override=h_uav + link_m,
        eta_atm_override=eta_atm,
    )
    if not math.isclose(physical["link_length_m"], link_m, rel_tol=0.0, abs_tol=1e-9):
        raise RuntimeError("Distance override did not produce the requested vertical link length.")
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


def _mi(ensemble, transmittance: float, epsilon: float, noises: dict[int, torch.Tensor]) -> tuple[float, float]:
    values = []
    t = torch.tensor([transmittance], dtype=torch.float64)
    e = torch.tensor([epsilon], dtype=torch.float64)
    for seed in MI_SEEDS:
        values.append(float(discrete_mutual_information(
            ensemble,
            t,
            e,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=noises[seed],
        )[0]))
    mean = sum(values) / len(values)
    stderr = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return mean, stderr / len(values) ** 0.5


def _plot(path: Path, rows: list[dict], field: str, ylabel: str, title: str) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for scheme in SCHEMES:
        selected = [row for row in rows if row["scheme"] == scheme]
        ax.plot(
            [row["L_km"] for row in selected],
            [row[field] for row in selected],
            marker="o",
            markersize=3.5,
            label=LABELS[scheme],
            color=COLORS[scheme],
        )
    ax.axhline(0.0, color="black", linewidth=0.8) if field == "K_raw" else None
    ax.set_xlabel("Link distance L (km)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> int:
    started = time.perf_counter()
    def forbidden(*_args, **_kwargs):
        raise RuntimeError("Distance sweep attempted a forbidden AP/full-Z path.")

    holevo_module.c4_gram_source_moments = forbidden
    holevo_module._maximize_bounded_scalar = forbidden
    config = load_yaml(ROOT / "configs" / "default.yaml")
    output_dir = ROOT / "results" / "fixed_source_distance_va2_kruse"
    output_dir.mkdir(parents=True, exist_ok=True)

    anchor_physical, anchor_phase, anchor_channel = _channel_at_distance(config, 19_000.0)
    anchor_security = anchor_channel["security"]
    for key, expected in ANCHOR.items():
        if not math.isclose(anchor_security[key], expected, rel_tol=0.0, abs_tol=1e-14):
            raise RuntimeError(
                f"19 km anchor mismatch for {key}: "
                f"got {anchor_security[key]!r}, expected {expected!r}"
            )

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
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    rows = []
    for L_km in L_KM:
        link_m = L_km * 1000.0
        physical, phase, channel = _channel_at_distance(config, link_m)
        security = channel["security"]
        transmittance = security["T"]
        epsilon = security["epsilon"]
        for scheme, (c_text, w_text, _) in SOURCE.items():
            c = torch.tensor([float(c_text)], dtype=torch.float64)
            w = torch.tensor([float(w_text)], dtype=torch.float64)
            ensemble = ensembles[scheme]
            mi, mi_stderr = _mi(ensemble, transmittance, epsilon, noises)
            t = torch.tensor([transmittance], dtype=torch.float64)
            epsilon_tensor = torch.tensor([epsilon], dtype=torch.float64)
            holevo = _holevo_from_source_moments(
                ensemble,
                t,
                epsilon_tensor,
                coherent_correlation=c,
                w_raw=w,
                tau=None,
                tau_trace=ensemble.probabilities.sum(dim=-1),
                require_supported_symmetry=True,
                symmetry_tolerance=1e-8,
                physicality_tolerance=1e-10,
                maximize_full_interval=False,
                diagnostics={
                    "backend": "fixed_source_distance_va2",
                    "source_moment_recomputed": False,
                    "phase_noise_already_in_epsilon": True,
                },
            )
            covariance = holevo.covariance
            lambdas = [
                float(covariance.lambda1[0]),
                float(covariance.lambda2[0]),
                float(covariance.lambda3[0]),
            ]
            z_signal = float(2.0 * torch.sqrt(t) * c)
            z_penalty = float(torch.sqrt(2.0 * t * epsilon * w))
            z_star = float(holevo.z[0])
            rows.append({
                "L_m": link_m,
                "L_km": L_km,
                "h_UAV_m": physical["h_uav_m"],
                "h_HAP_m": physical["h_hap_m"],
                "link_length_m": physical["link_length_m"],
                "scheme": scheme,
                "C": c_text,
                "w": w_text,
                "eta_atm": physical["eta_atm"],
                "xi_per_km": extinction_coefficient_per_km(
                    float(config["channel"]["visibility_km"]),
                    float(config["channel"]["wavelength_m"]) * 1e9,
                ),
                "v_sc": physical["v_sc"],
                "c_phi": phase["c_phi"],
                "mean_eta": channel["analysis"]["moments"]["mean_eta"],
                "mean_sqrt_eta": channel["analysis"]["moments"]["mean_sqrt_eta"],
                "T": transmittance,
                "epsilon": epsilon,
                "I_AB": mi,
                "I_AB_stderr": mi_stderr,
                "Z_signal": z_signal,
                "Z_penalty": z_penalty,
                "Z_star": z_star,
                "chi_BE_bound": float(holevo.chi_be[0]),
                "beta_I_AB": BETA * mi,
                "K_raw": BETA * mi - float(holevo.chi_be[0]),
                "physicality_pass": min(lambdas) >= 1.0 - 1e-10,
                "minimum_symplectic_lambda": min(lambdas),
                "symmetry_supported": covariance.symmetry.standard_form_supported,
                "outage": False,
                "holevo_mode": holevo.diagnostics["mode"],
                "numerical_repairs": list(holevo.diagnostics["numerical_repairs"]),
            })

    fields = list(rows[0])
    with (output_dir / "fixed_source_distance_va2.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "artifact": "FIXED_SOURCE_DISTANCE_SWEEP_VA2",
        "distance_grid_km": list(L_KM),
        "geometry_rule": "h_HAP_m = h_UAV_m + L_m; zenith_angle_rad = 0",
        "atmospheric_model": {
            "source": "src.channel.atmospheric_loss.atmospheric_transmittance",
            "visibility_km": float(config["channel"]["visibility_km"]),
            "wavelength_nm": float(config["channel"]["wavelength_m"]) * 1e9,
            "kruse_q": kruse_q(float(config["channel"]["visibility_km"])),
            "xi_per_km": extinction_coefficient_per_km(
                float(config["channel"]["visibility_km"]),
                float(config["channel"]["wavelength_m"]) * 1e9,
            ),
            "eta_atm_19km": atmospheric_transmittance(
                19_000.0,
                float(config["channel"]["visibility_km"]),
                float(config["channel"]["wavelength_m"]),
            ),
        },
        "VA": VA,
        "beta_rec": BETA,
        "source_moments_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "mi_seeds": list(MI_SEEDS),
        "mi_samples_per_symbol": MI_SAMPLES_PER_SYMBOL,
        "anchor_19km": {
            "T": anchor_security["T"],
            "epsilon": anchor_security["epsilon"],
            "phase": anchor_phase,
            "physical": {
                "h_HAP_m": anchor_physical["h_hap_m"],
                "h_UAV_m": anchor_physical["h_uav_m"],
                "link_length_m": anchor_physical["link_length_m"],
            },
        },
        "channel_path": {
            "physical_inputs": "scripts.calculate_channel_pdf_and_moments.derive_physical_inputs",
            "effective_moments": "scripts.calculate_channel_pdf_and_moments.analyze_product",
            "phase": "src.channel.phase_noise.phase_parameter_provenance",
            "security_channel": "scripts.run_effective_channel_va2.physical_channel_parameters",
        },
        "rows": rows,
        "runtime_seconds": time.perf_counter() - started,
    }
    _write_json(output_dir / "fixed_source_distance_va2.json", metadata)
    _plot(output_dir / "K_raw_vs_distance.png", rows, "K_raw", "Raw K (bits/use)", "Fixed-source VA=2 raw SKR vs distance")
    _plot(output_dir / "I_AB_vs_distance.png", rows, "I_AB", "I_AB (bits/use)", "Fixed-source VA=2 mutual information vs distance")
    _plot(output_dir / "chi_BE_bound_vs_distance.png", rows, "chi_BE_bound", "chi_BE bound (bits/use)", "Fixed-source VA=2 Holevo bound vs distance")
    _plot(output_dir / "Z_star_vs_distance.png", rows, "Z_star", "Z_star", "Fixed-source VA=2 primary correlation vs distance")
    print(json.dumps({
        "runtime_seconds": time.perf_counter() - started,
        "anchor": {"T": anchor_security["T"], "epsilon": anchor_security["epsilon"]},
        "rows": len(rows),
        "output_dir": str(output_dir),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
