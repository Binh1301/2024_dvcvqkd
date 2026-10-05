"""Joint full-angle divergence / receiver-diameter optical diagnostic."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
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
from scripts.run_exact_mb_test2 import ExactMBEvaluator
from scripts.run_uniform_va_optimization_theta10 import load_cached_uniform, uniform_ensemble


OUTPUT = ROOT / "results" / "joint_theta_dr_optical_search"
WAVELENGTH_M = 1.55e-6
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
PEAK_PHOTONS = 30.0
THETA_URAD = (50, 75, 100, 125, 150, 175, 200, 223, 250)
DIAMETERS_M = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55)
COARSE_DISTANCES_KM = (20.0, 25.0, 30.0, 35.0, 40.0)
FULL_DISTANCES_KM = (
    20.0, 21.0, 21.9393102292, 22.0, 23.0, 24.0, 25.0, 26.0,
    27.0, 28.0, 29.0, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5,
    33.0, 34.0, 35.0, 36.0, 38.0, 40.0,
)
# Existing exact Uniform cache plus the requested local refinement points.
UNIFORM_VA_BANK = (0.05, 0.08, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.18, 0.20, 0.60, 0.70, 0.80, 1.075, 2.05, 3.025, 4.0)


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


def configure() -> None:
    old.optical.TAU_ZEN = TAU_ZEN
    old.optical.EPSILON = EPSILON
    old.forensic.BETA = BETA


def build_one_source(config: dict, va: float, output: Path) -> dict:
    evaluator = ExactMBEvaluator(
        config,
        {"T_eff": 0.0, "epsilon_base": EPSILON, "c_phi": 0.0},
        output,
        source_cache_dir=ROOT / "results" / "exact_mb_test2" / "exact_source_cache",
        allow_legacy_exact_import=False,
    )
    ensemble = uniform_ensemble(config, va)
    payload = evaluator.source_moments(ensemble, 0.0, va)
    return {
        "V_A": va,
        "cache_key": payload["cache_key"],
        "ensemble_hash": payload["ensemble_hash"],
        "C": payload["C"],
        "w": payload["w"],
        "support_size": payload["support_size"],
        "route": payload["source_moment_route"],
        "cache_origin": payload["cache_origin"],
    }


def load_or_build_uniform_bank(config: dict, output: Path, build_missing: bool) -> tuple[list[dict], list[float], list[dict]]:
    bank = []
    missing = []
    for va in UNIFORM_VA_BANK:
        candidate = load_cached_uniform(config, va)
        if candidate is None:
            missing.append(va)
            continue
        candidate["historical_record_count"] = 1
        bank.append(candidate)
    built = []
    if missing and build_missing:
        with ThreadPoolExecutor(max_workers=min(3, len(missing))) as pool:
            built = list(pool.map(lambda va: build_one_source(config, va, output), missing))
        for va in missing:
            candidate = load_cached_uniform(config, va)
            if candidate is None:
                raise RuntimeError(f"Source build did not produce an exact cache row for V_A={va}")
            candidate["historical_record_count"] = 1
            bank.append(candidate)
        missing = []
    return sorted(bank, key=lambda row: float(row["V_A"])), missing, built


def channel_row(config: dict, theta_urad: float, diameter_m: float, distance_km: float) -> dict:
    theta = float(theta_urad) * 1e-6
    w0 = 2.0 * WAVELENGTH_M / (math.pi * theta)
    row, _ = old.optical._channel_row(
        config,
        w0_m=w0,
        receiver_diameter_m=float(diameter_m),
        distance_km=float(distance_km),
    )
    if abs(float(row["theta_div_full_angle_rad"]) - theta) > 1e-15:
        raise AssertionError("full-angle divergence/waist derivation mismatch")
    row["theta_div_urad"] = float(theta_urad)
    row["theta_div_full_rad"] = theta
    return row


def evaluate_uniform(config: dict, bank: list[dict], theta_urad: float, diameter_m: float, distance_km: float) -> dict:
    channel = channel_row(config, theta_urad, diameter_m, distance_km)
    rows = [old._candidate_row(candidate, config, channel) for candidate in bank]
    best = max(rows, key=lambda row: float(row["SKR"]))
    return {
        "theta_div_urad": float(theta_urad),
        "theta_div_full_rad": float(channel["theta_div_full_rad"]),
        "w0_m": float(channel["w0_m"]),
        "w0_mm": 1000.0 * float(channel["w0_m"]),
        "receiver_diameter_m": float(diameter_m),
        "receiver_radius_m": float(diameter_m) / 2.0,
        "distance_km": float(distance_km),
        "zeta_deg": float(channel["zeta_deg"]),
        "T_eff": float(channel["T_eff"]),
        "eta_atm": float(channel["eta_atm"]),
        "sigma_X2": float(channel["sigma_X2"]),
        "G_d": float(channel["G_d"]),
        "omega_L_m": float(channel["omega_L_m"]),
        "omega_L_eq_m": float(channel["omega_L_eq_m"]),
        "A0": float(channel["A0"]),
        "sigma_jt_m": float(channel["sigma_jt_m"]),
        "chi_channel": float(channel["chi"]),
        "p_in": float(channel["p_in"]),
        "p_out": float(channel["p_out"]),
        "V_A_star": float(best["V_A"]),
        "I_AB": float(best["I_AB"]),
        "beta_I_AB": float(best["beta_I_AB"]),
        "chi_BE": float(best["chi_BE"]),
        "K_Uniform": float(best["SKR"]),
        "source_hash": best["source_cache_identifier"],
        "source_policy": "EXACT_HASH_MATCHED_UNIFORM_CACHE",
        "security_evaluator": "historical_exact_cw_direct_Z",
        "candidate_count": len(rows),
        "epsilon_ch": EPSILON,
        "beta": BETA,
        "AO": "OFF",
        "phase_noise": "OFF",
        "peak_photons": PEAK_PHOTONS,
        "status": "PASS",
    }


def category(rows: list[dict]) -> str:
    by_l = {float(row["distance_km"]): float(row["K_Uniform"]) for row in rows}
    if by_l[20.0] <= 0.0:
        return "NONPOSITIVE_AT_20"
    if by_l[30.0] > 0.0 and by_l[40.0] <= 0.0:
        return "TARGET_CROSSING_30_40"
    if by_l[40.0] > 0.0:
        return "POSITIVE_THROUGH_40"
    return "CROSSING_20_30"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--build-missing-uniform-source", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(1)
    configure()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    bank, missing, built = load_or_build_uniform_bank(config, output, args.build_missing_uniform_source)

    coarse_rows = [
        evaluate_uniform(config, bank, theta, diameter, distance)
        for theta in THETA_URAD
        for diameter in DIAMETERS_M
        for distance in COARSE_DISTANCES_KM
    ]
    write_csv(output / "uniform_coarse_exact.csv", coarse_rows)
    summary_rows = []
    for theta in THETA_URAD:
        for diameter in DIAMETERS_M:
            rows = [row for row in coarse_rows if float(row["theta_div_urad"]) == theta and float(row["receiver_diameter_m"]) == diameter]
            row_by_distance = {float(row["distance_km"]): row for row in rows}
            summary_rows.append({
                "theta_div_urad": theta,
                "w0_mm": rows[0]["w0_mm"],
                "receiver_diameter_m": diameter,
                "K_Uni_20": row_by_distance[20.0]["K_Uniform"],
                "K_Uni_25": row_by_distance[25.0]["K_Uniform"],
                "K_Uni_30": row_by_distance[30.0]["K_Uniform"],
                "K_Uni_35": row_by_distance[35.0]["K_Uniform"],
                "K_Uni_40": row_by_distance[40.0]["K_Uniform"],
                "VA_star_30": row_by_distance[30.0]["V_A_star"],
                "T_eff_20": row_by_distance[20.0]["T_eff"],
                "T_eff_30": row_by_distance[30.0]["T_eff"],
                "T_eff_40": row_by_distance[40.0]["T_eff"],
                "status": category(rows),
                "physical_tier": "A" if diameter <= .30 else "B" if diameter <= .40 else "C",
            })
    write_csv(output / "uniform_coarse_summary.csv", summary_rows)

    candidates = sorted(summary_rows, key=lambda row: (-float(row["K_Uni_30"]), float(row["receiver_diameter_m"]), abs(float(row["theta_div_urad"]) - 150.0)))[:10]
    write_csv(output / "uniform_coarse_top_candidates.csv", candidates)
    config_sha = sha256(ROOT / "configs" / "default.yaml")
    experiment_payload = {
        "schema": "joint-theta-dr-uniform-coarse-v1",
        "config_sha256": config_sha,
        "model_composite_sha256": "a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58",
        "theta_div_urad": list(THETA_URAD),
        "receiver_diameter_m": list(DIAMETERS_M),
        "distances_km": list(COARSE_DISTANCES_KM),
        "uniform_bank": [(float(row["V_A"]), row["ensemble_hash"]) for row in bank],
    }
    experiment_hash = hashlib.sha256(json.dumps(experiment_payload, sort_keys=True).encode()).hexdigest()
    report = {
        "status": "JOINT_THETA_DR_UNIFORM_COARSE_COMPLETE",
        "scope": "DIAGNOSTIC_ONLY",
        "fixed": {"h_HAP_m": 20000.0, "h_UAV_m": 1000.0, "wavelength_m": WAVELENGTH_M, "tau_zen": TAU_ZEN, "epsilon_ch": EPSILON, "beta": BETA, "AO": "OFF", "phase_noise": "OFF", "holevo": "direct Z_minus", "peak_photons": PEAK_PHOTONS},
        "model_composite_sha256": experiment_payload["model_composite_sha256"],
        "config_sha256": config_sha,
        "experiment_hash": experiment_hash,
        "theta_div_urad": list(THETA_URAD),
        "receiver_diameter_m": list(DIAMETERS_M),
        "coarse_distances_km": list(COARSE_DISTANCES_KM),
        "uniform_exact_VA_bank": sorted(float(row["V_A"]) for row in bank),
        "missing_uniform_VA_source_points": sorted(set(missing)),
        "new_source_points_built": built,
        "channel_recomputed_for_every_pair": True,
        "T_eff_reused": False,
        "interpolation_used": False,
        "uniform_optimization_scope": "best exact-tested Uniform cache candidate; continuous VA unresolved if source missing",
        "follow_up_status": {
            "uniform_local_refinement": "NOT_RUN_NO_CROSSING_CANDIDATE",
            "full_distance_refinement": "NOT_RUN_NO_CROSSING_CANDIDATE",
            "MB_fixed_and_optimized": "NOT_RUN_NO_CROSSING_CANDIDATE",
        },
        "artifacts": {"rows": "uniform_coarse_exact.csv", "summary": "uniform_coarse_summary.csv", "top": "uniform_coarse_top_candidates.csv"},
        "provenance": {"config_sha256": config_sha, "runner_sha256": sha256(Path(__file__).resolve()), "source_cache": "results/exact_mb_test2/exact_source_cache"},
    }
    (output / "joint_theta_dr_uniform_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output_dir": str(output), "missing": report["missing_uniform_VA_source_points"], "top": candidates[:5]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
