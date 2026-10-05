"""Transition-region theta/D_r Uniform feasibility frontier diagnostic."""

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
from scripts import run_joint_theta_dr_optical_search as joint


OUTPUT = ROOT / "results" / "transition_theta_dr_frontier"
THETA_URAD = (15, 20, 25, 30, 35, 40, 45, 50)
DIAMETERS_M = (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80)
SCREEN_DISTANCES_KM = (20.0, 25.0)
REFINED_DISTANCES_KM = (20.0, 25.0, 30.0, 32.0, 34.0, 35.0, 36.0, 38.0, 40.0)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tier(diameter: float) -> str:
    return "compact/moderate" if diameter <= 0.30 else "large" if diameter <= 0.55 else "very-large"


def classify(k20: float, k25: float) -> str:
    if k20 <= 0.0:
        return "FAIL_20"
    if k25 <= 0.0:
        return "POSITIVE_20_ONLY"
    return "POSITIVE_THROUGH_25"


def bisection(config: dict, bank: list[dict], theta: float, distance: float) -> dict:
    low, high = DIAMETERS_M[0], DIAMETERS_M[-1]
    low_row = joint.evaluate_uniform(config, bank, theta, low, distance)
    high_row = joint.evaluate_uniform(config, bank, theta, high, distance)
    if float(low_row["K_Uniform"]) > 0.0:
        return {"theta_div_urad": theta, "distance_km": distance, "status": "POSITIVE_AT_LOWER_BOUNDARY", "lower_nonpositive": None, "upper_positive": low_row}
    if float(high_row["K_Uniform"]) <= 0.0:
        return {"theta_div_urad": theta, "distance_km": distance, "status": "NO_POSITIVE_AT_0P80M", "lower_nonpositive": high_row, "upper_positive": None}
    for _ in range(32):
        mid = 0.5 * (low + high)
        row = joint.evaluate_uniform(config, bank, theta, mid, distance)
        if float(row["K_Uniform"]) > 0.0:
            high, high_row = mid, row
        else:
            low, low_row = mid, row
    return {"theta_div_urad": theta, "distance_km": distance, "status": "EXACT_CHANNEL_BISECTION_BRACKET", "lower_nonpositive": low_row, "upper_positive": high_row, "bracket_width_m": high - low, "no_skr_interpolation": True}


def endpoint(row: dict, positive: bool) -> float | None:
    hits = [r for r in row if (float(r["K_Uniform"]) > 0.0 if positive else float(r["K_Uniform"]) <= 0.0)]
    return max((float(r["distance_km"]) for r in hits), default=None) if positive else min((float(r["distance_km"]) for r in hits), default=None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    joint.configure()
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    bank, missing, built = joint.load_or_build_uniform_bank(config, output, False)
    if missing:
        raise RuntimeError(f"Transition search missing exact source moments: {missing}")

    screen_rows = [joint.evaluate_uniform(config, bank, theta, diameter, distance) | {"tier": tier(diameter)} for theta in THETA_URAD for diameter in DIAMETERS_M for distance in SCREEN_DISTANCES_KM]
    write_csv(output / "transition_screen_exact.csv", screen_rows)
    screen_summary = []
    for theta in THETA_URAD:
        for diameter in DIAMETERS_M:
            rows = [r for r in screen_rows if float(r["theta_div_urad"]) == theta and float(r["receiver_diameter_m"]) == diameter]
            by_d = {float(r["distance_km"]): r for r in rows}
            screen_summary.append({
                "theta_div_urad": theta, "w0_mm": rows[0]["w0_mm"], "receiver_diameter_m": diameter, "tier": tier(diameter),
                "T_eff_20": by_d[20.0]["T_eff"], "K_Uniform_20": by_d[20.0]["K_Uniform"], "VA_star_20": by_d[20.0]["V_A_star"],
                "T_eff_25": by_d[25.0]["T_eff"], "K_Uniform_25": by_d[25.0]["K_Uniform"], "VA_star_25": by_d[25.0]["V_A_star"],
                "status": classify(float(by_d[20.0]["K_Uniform"]), float(by_d[25.0]["K_Uniform"])),
            })
    write_csv(output / "transition_screen_summary.csv", screen_summary)

    positive_thetas = sorted({int(row["theta_div_urad"]) for row in screen_summary if row["status"] != "FAIL_20"})
    brackets = []
    for theta in positive_thetas:
        brackets.append(bisection(config, bank, theta, 20.0))
        brackets.append(bisection(config, bank, theta, 25.0))
    bracket_rows = []
    for item in brackets:
        for side in ("lower_nonpositive", "upper_positive"):
            row = item.get(side)
            if row is not None:
                bracket_rows.append({"theta_div_urad": item["theta_div_urad"], "distance_km": item["distance_km"], "status": item["status"], "side": side, **row})
    write_csv(output / "transition_aperture_bisection_exact.csv", bracket_rows)

    # Select a small, explicit frontier set after the first screen.
    frontier = []
    for theta in positive_thetas:
        b20 = next(x for x in brackets if x["theta_div_urad"] == theta and x["distance_km"] == 20.0)
        b25 = next(x for x in brackets if x["theta_div_urad"] == theta and x["distance_km"] == 25.0)
        if b20.get("upper_positive") is None:
            continue
        frontier.append({
            "theta_div_urad": theta,
            "w0_mm": b20["upper_positive"]["w0_mm"],
            "Dcrit_20_m": b20["upper_positive"]["receiver_diameter_m"],
            "Dcrit_25_m": None if b25.get("upper_positive") is None else b25["upper_positive"]["receiver_diameter_m"],
            "VA_star": b20["upper_positive"]["V_A_star"],
            "tier_at_Dcrit20": tier(float(b20["upper_positive"]["receiver_diameter_m"])),
        })
    frontier.sort(key=lambda r: (float(r["Dcrit_20_m"]), float(r["theta_div_urad"])))
    write_csv(output / "transition_pareto_frontier.csv", frontier)
    selected_specs = [(15, 0.60), (15, 0.65), (15, 0.70), (20, 0.80)]
    selected = [
        {"theta_div_urad": theta, "receiver_diameter_m": diameter, "tier_at_Dcrit20": tier(diameter)}
        for theta, diameter in selected_specs
    ]

    refined_rows = []
    for candidate in selected:
        theta = float(candidate["theta_div_urad"]); diameter = float(candidate["receiver_diameter_m"])
        refined_rows.extend(joint.evaluate_uniform(config, bank, theta, diameter, distance) | {"tier": tier(diameter)} for distance in REFINED_DISTANCES_KM)
    write_csv(output / "transition_refined_distance_exact.csv", refined_rows)
    refined_summary = []
    for candidate in selected:
        theta = float(candidate["theta_div_urad"])
        rows = [r for r in refined_rows if float(r["theta_div_urad"]) == theta]
        refined_summary.append({**candidate, "last_exact_positive_km": endpoint(rows, True), "first_exact_nonpositive_km": endpoint(rows, False), "status": "TARGET_CANDIDATE"})
    write_csv(output / "transition_refined_summary.csv", refined_summary)

    experiment_payload = {"schema": "transition-theta-dr-frontier-v1", "config_sha256": joint.sha256(ROOT / "configs" / "default.yaml"), "model_composite_sha256": "a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58", "theta_div_urad": list(THETA_URAD), "receiver_diameter_m": list(DIAMETERS_M), "screen_distances_km": list(SCREEN_DISTANCES_KM), "uniform_bank": [(float(row["V_A"]), row["ensemble_hash"]) for row in bank]}
    experiment_hash = hashlib.sha256(json.dumps(experiment_payload, sort_keys=True).encode()).hexdigest()
    report = {
        "status": "TRANSITION_THETA_DR_FRONTIER_COMPLETE",
        "scope": "DIAGNOSTIC_ONLY",
        "model_composite_sha256": experiment_payload["model_composite_sha256"], "config_sha256": experiment_payload["config_sha256"], "experiment_hash": experiment_hash,
        "theta_div_urad": list(THETA_URAD), "receiver_diameter_m": list(DIAMETERS_M), "screen_distances_km": list(SCREEN_DISTANCES_KM),
        "uniform_exact_VA_bank": sorted(float(row["V_A"]) for row in bank), "missing_uniform_VA_source_points": missing, "new_source_points_built": built,
        "classification_counts": {status: sum(row["status"] == status for row in screen_summary) for status in ("FAIL_20", "POSITIVE_20_ONLY", "POSITIVE_THROUGH_25")},
        "positive_theta_values": positive_thetas,
        "frontier_count": len(frontier), "selected_refinement_count": len(selected), "selected_refinement_specs": selected_specs,
        "critical_Teff_reference": 0.08982746,
        "follow_up_status": "NO_FRONTIER_IF_ZERO; MB_NOT_RUN_UNTIL_UNIFORM_FRONTIER_EXISTS",
        "artifacts": {"screen_rows": "transition_screen_exact.csv", "screen_summary": "transition_screen_summary.csv", "bisection": "transition_aperture_bisection_exact.csv", "frontier": "transition_pareto_frontier.csv", "refined_rows": "transition_refined_distance_exact.csv", "refined_summary": "transition_refined_summary.csv"},
        "provenance": {"runner_sha256": joint.sha256(Path(__file__).resolve()), "source_cache": "results/exact_mb_test2/exact_source_cache"},
    }
    (output / "transition_theta_dr_frontier_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["classification_counts"], "positive_theta_values": positive_thetas, "frontier": frontier}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
