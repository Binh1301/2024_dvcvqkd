"""Direct physical-noise distance diagnostic using cached source moments."""

from __future__ import annotations

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import tempfile
import time
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_optimistic_hapuav_beam_search import (
    _channel,
    _evaluate_scheme,
    APERTURE_RADIUS_M,
    MI_SAMPLES_PER_SYMBOL,
    MI_SEEDS,
    RHO_M,
    SIGMA_HAP_ANG_RAD,
    SIGMA_H_M,
)
from src.modulation.joint_ps_gs import reference_ensemble
from src.cvqkd.mutual_information import standard_complex_noise
from src.utils.random import torch_generator
import src.cvqkd.holevo as holevo_module


VA = 2.0
BETA = 0.95
THETA_DIV_FULL_URAD = 50.0
CN2_GROUND_ACTIVE = 5.0e-14
L_KM = tuple(19.0 + 0.5 * index for index in range(11))
MB_NUS = (0.02, 0.05, 0.075, 0.0875, 0.090625, 0.09375, 0.10, 0.125, 0.15, 0.20)
SOURCE_FILES = {
    "uniform": "cvqkd_uniform_va2_c4_checkpoint.json",
    "binomial": "cvqkd_binomial_va2_c4_checkpoint.json",
    0.02: "cvqkd_mb_nu_0p020000_va2_c4_checkpoint.json",
    0.05: "cvqkd_mb_nu_0p050000_va2_c4_checkpoint.json",
    0.075: "cvqkd_mb_nu_0p075000_va2_c4_checkpoint.json",
    0.0875: "cvqkd_mb_nu_0p087500_va2_c4_checkpoint.json",
    0.090625: "cvqkd_mb_nu_0p090625_va2_c4_checkpoint.json",
    0.09375: "cvqkd_mb_nu_0p093750_va2_c4_checkpoint.json",
    0.10: "cvqkd_fixed_mb_va2_c4_checkpoint.json",
    0.125: "cvqkd_mb_nu_0p125000_va2_c4_checkpoint.json",
    0.15: "cvqkd_mb_nu_0p150000_va2_c4_checkpoint.json",
    0.20: "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json",
}


def _load_source(path: Path) -> tuple[str, str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    final = payload["rows"][-1]
    if not final.get("resolved"):
        raise RuntimeError(f"Unresolved source checkpoint: {path}")
    return final["C"], final["w"], {
        "checkpoint": str(path),
        "accepted_precision_pair": [payload["rows"][-2]["digits"], final["digits"]],
        "C": final["C"],
        "w": final["w"],
    }


def _load_sources() -> tuple[dict[str, tuple[str, str]], dict[str, dict]]:
    sources: dict[str, tuple[str, str]] = {}
    metadata: dict[str, dict] = {}
    for key, filename in SOURCE_FILES.items():
        scheme = "uniform" if key == "uniform" else "binomial" if key == "binomial" else f"mb_{key:g}"
        c, w, record = _load_source(Path(tempfile.gettempdir()) / filename)
        sources[scheme] = (c, w)
        metadata[scheme] = record
    return sources, metadata


def _scheme_records(config: dict, sources: dict[str, tuple[str, str]]) -> dict[str, object]:
    records = {
        "uniform": reference_ensemble(
            "uniform", batch_size=1, modulation_variance=VA,
            nu_mb=None, v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        ),
        "binomial": reference_ensemble(
            "binomial", batch_size=1, modulation_variance=VA,
            nu_mb=None, v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        ),
    }
    for nu in MB_NUS:
        records[f"mb_{nu:g}"] = reference_ensemble(
            "mb", batch_size=1, modulation_variance=VA, nu_mb=nu,
            v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        )
    return records


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    output_dir = ROOT / "results" / "direct_noise_distance_va2_compare"
    output_dir.mkdir(parents=True, exist_ok=True)
    sources, source_metadata = _load_sources()
    ensembles = _scheme_records(config, sources)
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    original_maximizer = holevo_module._maximize_bounded_scalar
    holevo_module._maximize_bounded_scalar = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        RuntimeError("Direct-noise sweep reached forbidden full-Z maximization.")
    )

    def evaluate_distance(L_km: float) -> tuple[dict, list[dict]]:
        physical, phase, channel = _channel(
            config,
            L_km * 1000.0,
            THETA_DIV_FULL_URAD,
            aperture_radius_m=APERTURE_RADIUS_M,
            sigma_h_m=SIGMA_H_M,
            rho_m=RHO_M,
            sigma_hap_ang_rad=SIGMA_HAP_ANG_RAD,
            cn2_ground=CN2_GROUND_ACTIVE,
        )
        security = channel["security"]
        channel_row = {
            "L_km": L_km,
            "mean_eta": channel["analysis"]["moments"]["mean_eta"],
            "mean_sqrt_eta": channel["analysis"]["moments"]["mean_sqrt_eta"],
            "T": security["T"],
            "epsilon_base": security["epsilon_base"],
            "xi_phase": security["xi_phase"],
            "epsilon": security["epsilon"],
            "tau_phi2": phase["tau_phi2"],
        }
        distance_rows = []
        for scheme, ensemble in ensembles.items():
            result = _evaluate_scheme(
                ensemble,
                sources[scheme],
                security,
                noises,
                "mb" if scheme.startswith("mb_") else scheme,
                THETA_DIV_FULL_URAD,
                L_km,
            )
            nu = None if not scheme.startswith("mb_") else float(scheme[3:])
            distance_rows.append({
                "L_km": L_km,
                "modulation": "Uniform" if scheme == "uniform" else "Binomial" if scheme == "binomial" else "MB",
                "nu_MB": nu,
                "T": security["T"],
                "epsilon": security["epsilon"],
                "I_AB": result["I_AB"],
                "beta_I_AB": result["beta_I_AB"],
                "C": result["C"],
                "w": result["w"],
                "Z_star": result["Z_star"],
                "chi_BE": result["chi_BE"],
                "K_raw": result["K_raw"],
                "holevo_mode": result["holevo_mode"],
                "physicality_pass": result["physicality_pass"],
            })
        return channel_row, distance_rows

    expected_19 = {
        "Uniform": -0.004196789481,
        "Binomial": 0.003958973306,
        "MB_0.2": 0.004327928681,
    }
    rows: list[dict] = []
    channel_rows: list[dict] = []
    try:
        channel_row, distance_rows = evaluate_distance(19.0)
        observed_19 = {
            "Uniform": next(r["K_raw"] for r in distance_rows if r["modulation"] == "Uniform"),
            "Binomial": next(r["K_raw"] for r in distance_rows if r["modulation"] == "Binomial"),
            "MB_0.2": next(r["K_raw"] for r in distance_rows if r["modulation"] == "MB" and r["nu_MB"] == 0.2),
        }
        deltas = {key: observed_19[key] - value for key, value in expected_19.items()}
        if any(abs(value) > 5.0e-12 for value in deltas.values()):
            raise RuntimeError(f"19 km regression mismatch: {deltas}")
        channel_rows.append(channel_row)
        rows.extend(distance_rows)
        print(f"19 km regression passed: {observed_19}", flush=True)
        completed = 1
        for L_km in L_KM:
            if L_km == 19.0:
                continue
            channel_row, distance_rows = evaluate_distance(L_km)
            channel_rows.append(channel_row)
            rows.extend(distance_rows)
            completed += 1
            print(f"completed L={L_km:.1f} km ({completed}/{len(L_KM)})", flush=True)
    finally:
        holevo_module._maximize_bounded_scalar = original_maximizer

    payload = {
        "artifact": "DIRECT_PHYSICAL_NOISE_DISTANCE_VA2_COMPARE",
        "status": "DIAGNOSTIC_ONLY",
        "scenario": {
            "VA": VA,
            "beta_rec": BETA,
            "theta_div_full_urad": THETA_DIV_FULL_URAD,
            "h_UAV_m": 1000.0,
            "h_HAP_m": 20000.0,
            "geometry_rule": "L_m = (20000 - h_UAV_m) / cos(zenith_angle_rad)",
            "aperture_radius_m": APERTURE_RADIUS_M,
            "sigma_h_m": SIGMA_H_M,
            "rho_m": RHO_M,
            "sigma_hap_ang_rad": SIGMA_HAP_ANG_RAD,
            "cn2_ground_m_minus_two_thirds": CN2_GROUND_ACTIVE,
            "epsilon_base": 0.0186,
            "cn2_phase_m_minus_two_thirds": 1.0e-16,
            "phase_distance_rule": "link_distance_m = L_m",
            "wavelength_m": 1.55e-6,
            "visibility_km": 200.0,
            "security_model": "T=mean_sqrt_eta^2; epsilon=epsilon_base+xi_phase",
        },
        "source_moments_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "regression_19km": {
            "expected": expected_19,
            "observed": observed_19,
            "deltas": deltas,
            "passed": True,
        },
        "channel_rows": channel_rows,
        "rows": rows,
        "source_moments": source_metadata,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output_dir / "direct_noise_distance_va2.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (output_dir / "direct_noise_distance_va2.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "rows": len(rows),
        "channel_rows": len(channel_rows),
        "regression_19km": payload["regression_19km"],
        "output_dir": str(output_dir),
        "runtime_seconds": payload["runtime_seconds"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
