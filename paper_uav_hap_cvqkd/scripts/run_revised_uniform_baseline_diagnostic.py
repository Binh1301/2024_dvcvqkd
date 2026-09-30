"""Cache-only diagnostic for the revised Uniform optical baseline.

The channel is recomputed for every optical geometry. Security evaluation is
restricted to current hash-matched historical Uniform C,w rows; missing V_A
points are reported, never interpolated or generated here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates
from scripts.run_hap_uav_sayat_forensic_diagnostic import evaluate
from scripts import run_uniform_beam_waist_diagnostic as optical


OUTPUT = ROOT / "results" / "revised_uniform_baseline_diagnostic"
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
ZENITH_DEG = 30.0
OLD_W0 = 0.004424935637532516
OLD_DR = 0.08
NEW_W0 = 0.10
NEW_DR = 0.55
REQUESTED_VA = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.075, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0)
APERTURES = (0.45, 0.50, 0.525, 0.55, 0.575, 0.60)
WAISTS = (0.05, 0.075, 0.10, 0.125, 0.15)
DISTANCES_KM = (19.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 35.0, 40.0, 50.0)


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
    optical.TAU_ZEN = TAU_ZEN
    optical.EPSILON = EPSILON


def _channel(config: dict, w0_m: float, receiver_diameter_m: float, distance_km: float | None = None) -> dict:
    row, _ = optical._channel_row(
        config,
        w0_m=float(w0_m),
        receiver_diameter_m=float(receiver_diameter_m),
        distance_km=distance_km,
    )
    return row


def _exact_rows(config: dict, candidates: list[dict], channel: dict, *, full_interval: bool = False) -> list[dict]:
    rows = []
    for candidate in candidates:
        evaluated = evaluate(
            candidate,
            config,
            float(channel["T_eff"]),
            EPSILON,
            compare_full_interval=full_interval,
        )
        rows.append({
            **channel,
            **evaluated,
            "Z_star": evaluated["Z_direct"],
            "chi_BE": evaluated["chi_BE_direct"],
            "SKR": evaluated["SKR_direct"],
            "source_policy": "historical_exact_audit_only",
        })
    return rows


def _best(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("No exact Uniform candidate is available.")
    return max(rows, key=lambda row: float(row["SKR_direct"]))


def _summary(config: dict, candidates: list[dict], *, label: str, w0_m: float, receiver_diameter_m: float, distance_km: float | None = None, full_interval: bool = False) -> tuple[dict, list[dict]]:
    channel = _channel(config, w0_m, receiver_diameter_m, distance_km)
    rows = _exact_rows(config, candidates, channel, full_interval=full_interval)
    best = _best(rows)
    summary = {
        **channel,
        "label": label,
        "exact_uniform_candidate_count": len(rows),
        "V_A_opt_best_tested": best["V_A"],
        "I_AB_best_tested": best["I_AB"],
        "beta_I_AB_best_tested": best["beta_I_AB"],
        "chi_BE_best_tested": best["chi_BE_direct"],
        "SKR_max_best_tested": best["SKR_direct"],
        "Z_star_best_tested": best["Z_direct"],
        "positive_best_tested": bool(float(best["SKR_direct"]) > 0.0),
        "optimization_status": "BEST_TESTED_EXACT_UNIFORM_CANDIDATE_NOT_CONTINUOUS_OPTIMUM",
    }
    if full_interval:
        full_best = max(rows, key=lambda row: float(row["SKR_full_interval"]))
        summary.update({
            "V_A_opt_best_tested_full_interval": full_best["V_A"],
            "chi_BE_best_tested_full_interval": full_best["chi_BE_full_interval"],
            "SKR_max_best_tested_full_interval": full_best["SKR_full_interval"],
            "direct_full_winner_agree": bool(best["V_A"] == full_best["V_A"]),
        })
    return summary, rows


def _requested_status(candidates: list[dict]) -> list[dict]:
    exact = {round(float(candidate["V_A"]), 14): candidate for candidate in candidates}
    rows = []
    for value in REQUESTED_VA:
        candidate = exact.get(round(float(value), 14))
        rows.append({
            "V_A_requested": float(value),
            "status": "EXACT_CW_AVAILABLE" if candidate is not None else "MISSING_EXACT_CW",
            "C": None if candidate is None else candidate["C"],
            "w": None if candidate is None else candidate["w"],
            "ensemble_hash": None if candidate is None else candidate["ensemble_hash"],
        })
    return rows


def _positive_interval(rows: list[dict]) -> list[float]:
    return [float(row["V_A"]) for row in sorted(rows, key=lambda row: float(row["V_A"])) if float(row["SKR_direct"]) > 0.0]


def _bisection(config: dict, candidates: list[dict], *, parameter: str, low: float, high: float, fixed_w0: float | None = None, fixed_dr: float | None = None, low_km: float | None = None, high_km: float | None = None) -> dict | None:
    def score(value: float) -> tuple[float, dict]:
        if parameter == "receiver_diameter_m":
            summary, _ = _summary(config, candidates, label="receiver_bisection", w0_m=float(fixed_w0), receiver_diameter_m=value)
        elif parameter == "distance_km":
            summary, _ = _summary(config, candidates, label="distance_bisection", w0_m=float(fixed_w0), receiver_diameter_m=float(fixed_dr), distance_km=value)
        else:
            raise ValueError(parameter)
        return float(summary["SKR_max_best_tested"]), summary

    low_score, low_row = score(low if low_km is None else low_km)
    high_score, high_row = score(high if high_km is None else high_km)
    if not (low_score <= 0.0 < high_score or low_score > 0.0 >= high_score):
        return None
    increasing = low_score <= 0.0 < high_score
    for _ in range(40):
        midpoint = 0.5 * (low + high)
        mid_score, mid_row = score(midpoint)
        if increasing:
            if mid_score > 0.0:
                high, high_score, high_row = midpoint, mid_score, mid_row
            else:
                low, low_score, low_row = midpoint, mid_score, mid_row
        else:
            if mid_score > 0.0:
                low, low_score, low_row = midpoint, mid_score, mid_row
            else:
                high, high_score, high_row = midpoint, mid_score, mid_row
    threshold = 0.5 * (low + high)
    threshold_score, threshold_row = score(threshold)
    return {
        "status": "SPARSE_EXACT_CANDIDATE_BISECTION",
        "parameter": parameter,
        "low": low,
        "high": high,
        "estimate": threshold,
        "K_low": low_score,
        "K_high": high_score,
        "K_estimate": threshold_score,
        "V_A_opt_at_estimate": threshold_row["V_A_opt_best_tested"],
        "T_eff_at_estimate": threshold_row["T_eff"],
        "loss_dB_at_estimate": threshold_row["loss_dB"],
    }


def _save_plot(path: Path, figure: plt.Figure) -> None:
    figure.tight_layout()
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def _plots(output: Path, va_rows: list[dict], aperture_rows: list[dict], waist_rows: list[dict], distance_rows: list[dict]) -> None:
    va_rows = sorted(va_rows, key=lambda row: float(row["V_A"]))
    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot([row["V_A"] for row in va_rows], [row["SKR_direct"] for row in va_rows], marker="o", color="#2563eb")
    axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    axis.set(xlabel=r"$V_A$ (SNU)", ylabel="Uniform SKR (bits/use)")
    axis.grid(alpha=0.3)
    _save_plot(output / "uniform_skr_vs_va", figure)

    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot([row["V_A"] for row in va_rows], [row["beta_I_AB"] for row in va_rows], marker="o", label=r"$\beta I_{AB}$", color="#2563eb")
    axis.plot([row["V_A"] for row in va_rows], [row["chi_BE_direct"] for row in va_rows], marker="o", label=r"$\chi_{BE}$", color="#dc2626")
    axis.set(xlabel=r"$V_A$ (SNU)", ylabel="bits/use")
    axis.grid(alpha=0.3)
    axis.legend()
    _save_plot(output / "uniform_security_terms_vs_va", figure)

    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot([row["receiver_diameter_m"] for row in aperture_rows], [row["SKR_max_best_tested"] for row in aperture_rows], marker="o", color="#2563eb")
    axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    axis.set(xlabel=r"$D_r$ (m)", ylabel="Optimized Uniform SKR (bits/use)")
    axis.grid(alpha=0.3)
    _save_plot(output / "uniform_skr_vs_receiver_diameter", figure)

    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot([1000.0 * row["w0_m"] for row in waist_rows], [row["SKR_max_best_tested"] for row in waist_rows], marker="o", color="#2563eb")
    axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    axis.set(xlabel=r"$w_0$ (mm)", ylabel="Optimized Uniform SKR (bits/use)")
    axis.grid(alpha=0.3)
    _save_plot(output / "uniform_skr_vs_beam_waist", figure)

    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot([row["distance_km"] for row in distance_rows], [row["SKR_max_best_tested"] for row in distance_rows], marker="o", color="#2563eb")
    axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    axis.set(xlabel="HAP-UAV link distance (km)", ylabel="Optimized Uniform SKR (bits/use)")
    axis.grid(alpha=0.3)
    _save_plot(output / "uniform_skr_vs_distance", figure)


def main() -> int:
    global OUTPUT, TAU_ZEN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-zen", type=float, default=TAU_ZEN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    TAU_ZEN = float(args.tau_zen)
    if not 0.0 < TAU_ZEN <= 1.0:
        raise ValueError("tau-zen must lie in (0,1].")
    OUTPUT = args.output_dir.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    _configure()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    uniform = [candidate for candidate in candidates if candidate["family"] == "Uniform"]
    if not uniform:
        raise RuntimeError("No current-compatible historical exact Uniform candidates found.")

    requested_status = _requested_status(uniform)
    old_summary, _ = _summary(config, uniform, label="A_old_w0_old_Dr", w0_m=OLD_W0, receiver_diameter_m=OLD_DR, full_interval=True)
    new_summary, new_rows = _summary(config, uniform, label="C_new_w0_new_Dr", w0_m=NEW_W0, receiver_diameter_m=NEW_DR, full_interval=True)
    middle_summary, _ = _summary(config, uniform, label="B_new_w0_old_Dr", w0_m=NEW_W0, receiver_diameter_m=OLD_DR)
    case_rows = [old_summary, middle_summary, new_summary]

    aperture_rows = [_summary(config, uniform, label=f"w0=0.10m_Dr={diameter:g}m", w0_m=NEW_W0, receiver_diameter_m=diameter)[0] for diameter in APERTURES]
    waist_rows = [_summary(config, uniform, label=f"w0={waist:g}m_Dr=0.55m", w0_m=waist, receiver_diameter_m=NEW_DR)[0] for waist in WAISTS]
    distance_rows = [_summary(config, uniform, label="new_baseline_distance", w0_m=NEW_W0, receiver_diameter_m=NEW_DR, distance_km=distance)[0] for distance in DISTANCES_KM]

    receiver_crossing = _bisection(config, uniform, parameter="receiver_diameter_m", low=0.50, high=0.525, fixed_w0=NEW_W0)
    distance_brackets = []
    for left, right in zip(sorted(distance_rows, key=lambda row: float(row["distance_km"])), sorted(distance_rows, key=lambda row: float(row["distance_km"]))[1:]):
        if float(left["SKR_max_best_tested"]) > 0.0 >= float(right["SKR_max_best_tested"]):
            distance_brackets.append((float(left["distance_km"]), float(right["distance_km"])))
    distance_crossing = None
    if distance_brackets:
        low, high = distance_brackets[0]
        distance_crossing = _bisection(config, uniform, parameter="distance_km", low=low, high=high, fixed_w0=NEW_W0, fixed_dr=NEW_DR)

    wavelength_m = float(config["channel"]["wavelength_m"])
    physical = optical._transmitter_rows(NEW_W0, wavelength_m)
    table1 = []
    for label, row in (("old", old_summary), ("new", new_summary)):
        table1.append({
            "baseline": label,
            "w0_m": row["w0_m"],
            "receiver_diameter_m": row["receiver_diameter_m"],
            "omega_L_eq_m": row["omega_L_eq_m"],
            "A0": row["A0"],
            "mean_T_raw": row["mean_T_raw"],
            "mean_sqrt_T_raw": row["mean_sqrt_T_raw"],
            "T_eff": row["T_eff"],
            "loss_dB": row["loss_dB"],
            "V_A_opt_best_tested": row["V_A_opt_best_tested"],
            "SKR_max_best_tested": row["SKR_max_best_tested"],
        })
    table1.append({
        "baseline": "new_minus_old_or_ratio",
        "omega_L_eq_ratio": new_summary["omega_L_eq_m"] / old_summary["omega_L_eq_m"],
        "A0_ratio": new_summary["A0"] / old_summary["A0"],
        "mean_T_raw_ratio": new_summary["mean_T_raw"] / old_summary["mean_T_raw"],
        "mean_sqrt_T_raw_ratio": new_summary["mean_sqrt_T_raw"] / old_summary["mean_sqrt_T_raw"],
        "T_eff_ratio": new_summary["T_eff"] / old_summary["T_eff"],
        "loss_recovered_dB": old_summary["loss_dB"] - new_summary["loss_dB"],
        "SKR_delta": new_summary["SKR_max_best_tested"] - old_summary["SKR_max_best_tested"],
    })

    write_csv(OUTPUT / "table1_revised_channel.csv", table1)
    write_csv(OUTPUT / "table2_uniform_va_sweep_exact_available.csv", new_rows)
    write_csv(OUTPUT / "table2_requested_va_status.csv", requested_status)
    write_csv(OUTPUT / "table3_nearby_receiver_aperture.csv", aperture_rows)
    write_csv(OUTPUT / "table4_nearby_beam_waist.csv", waist_rows)
    write_csv(OUTPUT / "case_ABC.csv", case_rows)
    write_csv(OUTPUT / "distance_sweep.csv", distance_rows)
    write_csv(OUTPUT / "receiver_crossing.csv", [] if receiver_crossing is None else [receiver_crossing])
    write_csv(OUTPUT / "distance_crossing.csv", [] if distance_crossing is None else [distance_crossing])
    write_csv(OUTPUT / "transmitter_plausibility.csv", physical)
    _plots(OUTPUT, new_rows, aperture_rows, waist_rows, distance_rows)

    new_positive = _positive_interval(new_rows)
    available_requested_positive = [value for value in new_positive if value in REQUESTED_VA]
    final_model_spec = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    report = {
        "status": "REVISED_OPTICAL_BASELINE_DIAGNOSTIC_COMPLETE_CACHE_ONLY",
        "source_policy": "historical_exact_uniform_cw_only",
        "new_source_moments_computed": False,
        "interpolation_used_for_cw": False,
        "security_formula_changed": False,
        "lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "fixture": {
            "tau_zen": TAU_ZEN,
            "zenith_deg_primary": ZENITH_DEG,
            "epsilon_ch_snu": EPSILON,
            "beta": BETA,
            "AO": "OFF",
            "phase_noise": "OFF",
            "wavelength_m": wavelength_m,
            "h_hap_m": config["channel"]["h_hap_m"],
            "h_uav_m": config["channel"]["h_uav_m"],
        },
        "requested_V_A": list(REQUESTED_VA),
        "exact_uniform_V_A_available": sorted(float(candidate["V_A"]) for candidate in uniform),
        "requested_V_A_exact_coverage": requested_status,
        "requested_positive_exact_V_A": available_requested_positive,
        "positive_available_exact_V_A": new_positive,
        "continuous_uniform_optimum": "UNRESOLVED_MISSING_EXACT_CW_FOR_REQUESTED_DOMAIN",
        "case_A_old_old": old_summary,
        "case_B_new_w0_old_Dr": case_rows[1],
        "case_C_new_new": new_summary,
        "table1": table1,
        "nearby_receiver_rows": aperture_rows,
        "nearby_w0_rows": waist_rows,
        "receiver_crossing": receiver_crossing,
        "distance_rows": distance_rows,
        "distance_crossing": distance_crossing,
        "physical_plausibility": {
            "w0_m": NEW_W0,
            "transmitter_rows": physical,
            "assessment": "reasonable_0.25_to_0.30m_Gaussian_transmitter_class_at_2.5_to_3_w0",
        },
        "provenance": {
            "producer_sha256": sha256(Path(__file__).resolve()),
            "final_model_spec_sha256": sha256(final_model_spec),
            "historical_expected_final_model_spec_sha256": "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1",
            "final_model_spec_status": "BLOCKED_BY_HASH_MISMATCH" if sha256(final_model_spec) != "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1" else "MATCH",
            "skipped_historical_rows": len(skipped),
        },
        "limitations": [
            "Only eight current hash-matched historical Uniform C,w rows are available.",
            "The requested missing V_A points were not interpolated or generated.",
            "Adaptive V_A refinement was not run because exact C,w are missing at the requested refinement points.",
            "All positive/optimum statements are best-tested exact-candidate statements, not continuous-domain claims.",
            "This is not baseline selection, certification, training, final-test, or publication-scale evaluation.",
        ],
    }
    (OUTPUT / "revised_uniform_baseline_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
