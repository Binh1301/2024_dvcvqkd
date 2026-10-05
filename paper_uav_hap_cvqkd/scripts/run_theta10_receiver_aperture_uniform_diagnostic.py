"""Exact-cache Uniform receiver-aperture diagnostic for the theta10 baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts import run_revised_uniform_mb_distance_diagnostic as old
from scripts.run_uniform_va_optimization_theta10 import load_cached_uniform


OUTPUT = ROOT / "results" / "theta10_receiver_aperture_uniform_diagnostic"
WAVELENGTH_M = 1.55e-6
THETA_DIV_FULL_RAD = 10.0e-6
W0_M = 2.0 * WAVELENGTH_M / (math.pi * THETA_DIV_FULL_RAD)
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
PEAK_PHOTONS = 30.0
VA_BUDGET = 1.5
DIAMETERS_M = (0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55)
MINIMUM_DISTANCES_KM = (19.0, 20.0, 22.0, 25.0, 30.0)
DISTANCE_GRID_KM = (
    19.0, 20.0, 21.0, 21.9393102292, 22.0, 23.0, 24.0, 25.0,
    26.0, 27.0, 28.0, 29.0, 30.0, 30.5, 31.0, 31.5, 32.0,
    32.5, 33.0, 34.0, 35.0, 36.0, 38.0, 40.0,
)
EXACT_VA_BANK = (0.05, 0.08, 0.10, 0.11, 0.12, 0.13, 0.15, 0.60, 0.70, 0.80, 1.075)
REQUESTED_VA_DOMAIN = (0.02, 0.04, 0.05, 0.06, 0.08, 0.10, 0.11, 0.12, 0.13, 0.15, 0.20, 0.30, 0.50, 0.60, 0.70, 0.75, 0.80, 1.0, 1.075, 1.25, 1.5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _configure() -> None:
    old.optical.TAU_ZEN = TAU_ZEN
    old.optical.EPSILON = EPSILON
    old.forensic.BETA = BETA


def channel_row(config: dict, diameter_m: float, distance_km: float) -> dict:
    row, _ = old.optical._channel_row(
        config,
        w0_m=W0_M,
        receiver_diameter_m=float(diameter_m),
        distance_km=float(distance_km),
    )
    if abs(float(row["theta_div_full_angle_rad"]) - THETA_DIV_FULL_RAD) > 1e-15:
        raise AssertionError("theta_div convention drifted")
    return row


def load_uniform_bank(config: dict) -> tuple[list[dict], list[float]]:
    candidates = []
    missing = []
    for va in EXACT_VA_BANK:
        candidate = load_cached_uniform(config, va)
        if candidate is None:
            missing.append(va)
            continue
        candidate["historical_record_count"] = 1
        if not 0.0 < float(candidate["V_A"]) <= VA_BUDGET:
            continue
        candidates.append(candidate)
    if not candidates:
        raise RuntimeError("No exact Uniform source moments are available.")
    return candidates, missing


def evaluate_point(config: dict, bank: list[dict], diameter_m: float, distance_km: float) -> dict:
    channel = channel_row(config, diameter_m, distance_km)
    rows = [old._candidate_row(candidate, config, channel) for candidate in bank]
    best = max(rows, key=lambda row: float(row["SKR"]))
    return {
        "receiver_diameter_m": float(diameter_m),
        "receiver_radius_m": float(diameter_m) / 2.0,
        "distance_km": float(distance_km),
        "zeta_deg": float(channel["zeta_deg"]),
        "T_eff": float(channel["T_eff"]),
        "w0_m": W0_M,
        "theta_div_full_rad": THETA_DIV_FULL_RAD,
        "V_A_star": float(best["V_A"]),
        "I_AB": float(best["I_AB"]),
        "beta_I_AB": float(best["beta_I_AB"]),
        "chi_BE": float(best["chi_BE"]),
        "K_max": float(best["SKR"]),
        "source_hash": best["source_cache_identifier"],
        "source_policy": "EXACT_HASH_MATCHED_UNIFORM_CACHE",
        "security_evaluator": "historical_exact_cw_direct_Z",
        "AO": "OFF",
        "phase_noise": "OFF",
        "epsilon_ch": EPSILON,
        "beta": BETA,
        "peak_photons": PEAK_PHOTONS,
        "VA_budget": VA_BUDGET,
        "candidate_count": len(rows),
        "status": "PASS",
    }


def threshold(config: dict, bank: list[dict], distance_km: float) -> dict:
    low = DIAMETERS_M[0]
    high = DIAMETERS_M[-1]
    low_row = evaluate_point(config, bank, low, distance_km)
    high_row = evaluate_point(config, bank, high, distance_km)
    if float(low_row["K_max"]) > 0.0:
        return {"distance_km": distance_km, "status": "POSITIVE_AT_LOWER_SWEEP_BOUNDARY", "lower_nonpositive": None, "upper_positive": low_row}
    if float(high_row["K_max"]) <= 0.0:
        return {"distance_km": distance_km, "status": "NO_POSITIVE_AT_UPPER_SWEEP_BOUNDARY", "lower_nonpositive": high_row, "upper_positive": None}
    for _ in range(32):
        mid = 0.5 * (low + high)
        row = evaluate_point(config, bank, mid, distance_km)
        if float(row["K_max"]) > 0.0:
            high, high_row = mid, row
        else:
            low, low_row = mid, row
    return {
        "distance_km": distance_km,
        "status": "EXACT_CHANNEL_BISECTION_BRACKET",
        "lower_nonpositive": low_row,
        "upper_positive": high_row,
        "bracket_width_m": float(high - low),
        "no_skr_interpolation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    _configure()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    bank, missing = load_uniform_bank(config)

    sweep_rows = [
        evaluate_point(config, bank, diameter, distance)
        for diameter in DIAMETERS_M
        for distance in MINIMUM_DISTANCES_KM
    ]
    write_csv(output / "aperture_sweep_exact.csv", sweep_rows)

    thresholds = [threshold(config, bank, distance) for distance in (20.0, 22.0, 25.0)]
    threshold_rows = []
    for item in thresholds:
        for label in ("lower_nonpositive", "upper_positive"):
            row = item.get(label)
            if row is not None:
                threshold_rows.append({"distance_km": item["distance_km"], "status": item["status"], "side": label, **row})
    write_csv(output / "threshold_bisection_exact.csv", threshold_rows)

    representative = []
    for diameter in (0.10, 0.15, 0.20, 0.30, 0.50, 0.55):
        rows = [evaluate_point(config, bank, diameter, distance) for distance in DISTANCE_GRID_KM]
        representative.extend(rows)
    write_csv(output / "representative_aperture_distance_exact.csv", representative)

    sanity = [evaluate_point(config, bank, 0.55, distance) for distance in MINIMUM_DISTANCES_KM]
    write_csv(output / "diameter_055_sanity_exact.csv", sanity)
    old_table = list(csv.DictReader((ROOT / "results" / "revised_hap_uav_optical_baseline_figure" / "skr_distance_table_extended.csv").open(newline="", encoding="utf-8")))
    old_uniform = {
        float(row["distance_km"]): row
        for row in old_table
        if row["protocol"] == "Uniform 256-QAM"
    }
    write_csv(output / "diameter_055_vs_old_provenance.csv", [
        {
            "distance_km": row["distance_km"],
            "current_theta10_Dr055_K": row["K_max"],
            "current_theta10_Dr055_VA": row["V_A_star"],
            "old_provenance_K": old_uniform[float(row["distance_km"])]["SKR"],
            "old_provenance_VA": old_uniform[float(row["distance_km"])]["V_A"],
            "delta_current_minus_old_K": float(row["K_max"]) - float(old_uniform[float(row["distance_km"])]["SKR"]),
            "status": "PASS_SIGN_SANITY" if (float(row["K_max"]) > 0.0) == (float(old_uniform[float(row["distance_km"])]["SKR"]) > 0.0) else "SIGN_DIFF",
        }
        for row in sanity
    ])

    report = {
        "status": "THETA10_RECEIVER_APERTURE_UNIFORM_DIAGNOSTIC_COMPLETE",
        "scope": "DIAGNOSTIC_ONLY",
        "configuration": {
            "h_HAP_m": 20000.0,
            "h_UAV_m": 1000.0,
            "wavelength_m": WAVELENGTH_M,
            "theta_div_full_rad": THETA_DIV_FULL_RAD,
            "w0_m": W0_M,
            "tau_zen": TAU_ZEN,
            "epsilon_ch": EPSILON,
            "beta": BETA,
            "AO": "OFF",
            "phase_noise": "OFF",
            "holevo": "direct Z_minus",
            "peak_photons": PEAK_PHOTONS,
            "VA_budget": VA_BUDGET,
        },
        "receiver_diameters_m": list(DIAMETERS_M),
        "minimum_distance_grid_km": list(MINIMUM_DISTANCES_KM),
        "distance_grid_for_operational_summary_km": list(DISTANCE_GRID_KM),
        "exact_VA_bank": sorted(float(row["V_A"]) for row in bank),
        "missing_requested_or_refinement_VA": missing + [va for va in REQUESTED_VA_DOMAIN if va not in {float(row["V_A"]) for row in bank}],
        "optimization_status": "BEST_EXACT_TESTED_UNIFORM_CACHE_CANDIDATE; CONTINUOUS_VA_DOMAIN_NOT_COVERED",
        "channel_recomputed_for_each_diameter_and_distance": True,
        "T_eff_reused": False,
        "interpolation_used": False,
        "new_source_moments_computed": False,
        "thresholds": thresholds,
        "sanity_055_rows": sanity,
        "artifacts": {
            "sweep": str((output / "aperture_sweep_exact.csv").relative_to(ROOT)).replace("\\", "/"),
            "thresholds": str((output / "threshold_bisection_exact.csv").relative_to(ROOT)).replace("\\", "/"),
            "representative_distance": str((output / "representative_aperture_distance_exact.csv").relative_to(ROOT)).replace("\\", "/"),
            "sanity_055": str((output / "diameter_055_sanity_exact.csv").relative_to(ROOT)).replace("\\", "/"),
            "sanity_055_vs_old": str((output / "diameter_055_vs_old_provenance.csv").relative_to(ROOT)).replace("\\", "/"),
        },
        "provenance": {
            "config_sha256": sha256(ROOT / "configs" / "default.yaml"),
            "runner_sha256": sha256(Path(__file__).resolve()),
            "channel_helper_sha256": sha256(ROOT / "scripts" / "run_uniform_beam_waist_diagnostic.py"),
            "source_cache": "results/exact_mb_test2/exact_source_cache",
        },
        "limitations": [
            "Thresholds are exact channel bisection brackets over the available exact Uniform VA bank, not continuous-VA certification.",
            "No new C,w source moments were generated; missing requested VA rows remain fail-closed.",
            "No publication figure, baseline selection, training, or final-test evaluation occurred.",
        ],
    }
    (output / "theta10_receiver_aperture_uniform_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output_dir": str(output), "thresholds": thresholds}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
