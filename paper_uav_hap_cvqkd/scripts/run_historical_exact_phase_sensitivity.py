"""Phase-noise-only sensitivity for the historical exact distance diagnostic.

The script reuses audited historical C,w and the current deterministic
closed-form channel moments.  It changes only C_n,phi^2; it never computes
new source moments and never changes the configured receiver aperture.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_historical_exact_skr_vs_link_distance import (
    CURVE_NAMES,
    _grid,
    _channel_moments,
    crossing,
    envelope,
    evaluate_candidate,
    load_candidates,
)
from src.channel.phase_noise import phase_distortion_variance, phase_noise_coefficient

OUTPUT = ROOT / "results" / "skr_vs_link_distance" / "phase_noise_sensitivity"
DEFAULT_CN2_VALUES = (9.4e-18, 7.0e-18, 5.0e-18, 3.0e-18, 2.0e-18, 1.0e-18)
DEFAULT_TAU_ZEN = 0.92
DEFAULT_ETA_AO = 0.95
DISTANCE_KM = 19.0
BASELINE_RADIUS_M = 0.04
BASELINE_DIAMETER_M = 0.08
BASELINE_DISTANCE_KM = 21.939310229205777


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def phase_values(candidate: dict, channel: dict, config: dict, *, cn2_phase: float, ao: bool, eta_ao: float) -> dict:
    link_length_m = float(channel["link_distance_m"])
    wavelength_m = float(config["channel"]["wavelength_m"])
    tau_phi2 = phase_distortion_variance(cn2_phase, wavelength_m, link_length_m)
    tau_ao2 = (1.0 - eta_ao) * tau_phi2 if ao else None
    tau_used = tau_ao2 if ao else tau_phi2
    c_phi = phase_noise_coefficient(tau_used)
    va = float(candidate["V_A"])
    epsilon_ch = float(config["channel"]["excess_noise_distribution"]["epsilon_ch_snu"])
    return {
        "AO_status": "AO enabled" if ao else "AO disabled",
        "tau_phi2": float(tau_phi2),
        "tau_AO2": None if tau_ao2 is None else float(tau_ao2),
        "tau_phase2_used": float(tau_used),
        "c_phi": float(c_phi),
        "epsilon_ch": epsilon_ch,
        "xi_phase": float(c_phi * va),
        "epsilon_total_recomputed": float(epsilon_ch + c_phi * va),
    }


def evaluate_set(candidates: list[dict], channel: dict, config: dict, *, curve: str, ao: bool, cn2_phase: float, eta_ao: float) -> tuple[list[dict], list[dict]]:
    rows = []
    errors = []
    for candidate in candidates:
        try:
            row = evaluate_candidate(
                candidate,
                channel,
                config,
                ao=ao,
                cn2_phase=cn2_phase,
                eta_ao=eta_ao,
            )
            row.update(phase_values(candidate, channel, config, cn2_phase=cn2_phase, ao=ao, eta_ao=eta_ao))
            row["curve"] = curve
            row["beta_I_AB"] = float(config["cvqkd"]["beta_reconciliation"]) * float(row["I_AB"])
            row["epsilon_total"] = row["epsilon_total_recomputed"]
            rows.append(row)
        except Exception as exc:
            errors.append({
                "curve": curve,
                "family": candidate["family"],
                "nu_raw": candidate["nu_raw"],
                "V_A": candidate["V_A"],
                "error": f"{type(exc).__name__}: {exc}",
            })
    return rows, errors


def evaluate_phase(config: dict, uniform: list[dict], mb: list[dict], *, cn2_phase: float, tau_zen: float, eta_ao: float, distance_km: float = DISTANCE_KM) -> tuple[dict[str, list[dict]], list[dict], dict]:
    channel = _channel_moments(config, distance_km=distance_km, tau_zen=tau_zen, sample_count=0, seed=0)
    rows_by_curve = {curve: [] for curve in CURVE_NAMES}
    errors = []
    rows, failed = evaluate_set(uniform, channel, config, curve="Uniform", ao=True, cn2_phase=cn2_phase, eta_ao=eta_ao)
    rows_by_curve["Uniform"].extend(rows)
    errors.extend(failed)
    rows, failed = evaluate_set(mb, channel, config, curve="MB with AO", ao=True, cn2_phase=cn2_phase, eta_ao=eta_ao)
    rows_by_curve["MB with AO"].extend(rows)
    errors.extend(failed)
    rows, failed = evaluate_set(mb, channel, config, curve="MB without AO", ao=False, cn2_phase=cn2_phase, eta_ao=eta_ao)
    rows_by_curve["MB without AO"].extend(rows)
    errors.extend(failed)
    channel_summary = {
        "distance_km": distance_km,
        "link_distance_m": channel["link_distance_m"],
        "zeta_deg": channel["zeta_deg"],
        "aperture_radius_m": config["channel"]["aperture_radius_m"],
        "aperture_diameter_m": 2.0 * float(config["channel"]["aperture_radius_m"]),
        "T_mean": channel["T_mean"],
        "sqrtT_mean": channel["sqrtT_mean"],
        "T_eff": channel["T_eff"],
        "P_T_raw_gt_1": channel["p_above_one"],
    }
    return rows_by_curve, errors, channel_summary


def winners(rows_by_curve: dict[str, list[dict]]) -> dict[str, dict]:
    result = {}
    for curve, rows in rows_by_curve.items():
        if not rows:
            raise RuntimeError(f"No successful rows for {curve}.")
        result[curve] = max(rows, key=lambda row: float(row["SKR"]))
    return result


def phase_summary_row(cn2_phase: float, rows_by_curve: dict[str, list[dict]], channel: dict, errors: list[dict]) -> dict:
    best = winners(rows_by_curve)
    row = {
        "C_nphi2": float(cn2_phase),
        "tau_phi2": float(best["Uniform"]["tau_phi2"]),
        "tau_AO2": float(best["MB with AO"]["tau_AO2"]),
        "T_eff": float(channel["T_eff"]),
        "K_uniform": float(best["Uniform"]["SKR"]),
        "K_MB_AO": float(best["MB with AO"]["SKR"]),
        "K_MB_noAO": float(best["MB without AO"]["SKR"]),
        "uniform_V_A": float(best["Uniform"]["V_A"]),
        "mb_AO_nu_raw": float(best["MB with AO"]["nu_raw"]),
        "mb_AO_V_A": float(best["MB with AO"]["V_A"]),
        "mb_noAO_nu_raw": float(best["MB without AO"]["nu_raw"]),
        "mb_noAO_V_A": float(best["MB without AO"]["V_A"]),
        "all_three_positive": all(float(best[curve]["SKR"]) > 0.0 for curve in CURVE_NAMES),
        "candidate_failures": len(errors),
    }
    return row


def plot_distance(path: Path, envelopes: dict[str, list[dict]], summaries: list[dict], cn2_phase: float) -> None:
    colors = {"Uniform": "#64748b", "MB with AO": "#2563eb", "MB without AO": "#dc2626"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
    figure, ax = plt.subplots(figsize=(10.5, 6.3), dpi=160)
    for curve in CURVE_NAMES:
        rows = envelopes[curve]
        ax.plot([row["distance_km"] for row in rows], [row["SKR"] for row in rows], color=colors[curve], marker="o", markersize=3.5, linewidth=1.8, label=curve)
        summary = next(item for item in summaries if item["curve"] == curve)
        estimate = summary.get("operation_distance_estimate_km")
        if estimate is not None:
            ax.axvline(estimate, color=colors[curve], linestyle="--", linewidth=0.8, alpha=0.65)
    ax.axhline(0.0, color="#111827", linewidth=0.9, linestyle=(0, (4, 3)))
    ax.set_xlabel("Link distance L (km)")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title(f"Phase-noise sensitivity diagnostic (C_n,phi²={cn2_phase:.3g})", weight="bold")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="both", color="#cbd5e1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=True)
    figure.text(0.5, 0.018, "Favorable phase-noise diagnostic; historical exact C,w reuse only.", ha="center", va="bottom", fontsize=8.5, color="#475569")
    figure.subplots_adjust(left=0.10, right=0.96, bottom=0.14, top=0.90)
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def print_diagnosis(row: dict) -> None:
    fields = (
        "curve", "AO_status", "shaping_family", "nu_raw", "V_A", "T_eff",
        "tau_phi2", "tau_AO2", "epsilon_ch", "xi_phase", "epsilon_total",
        "I_AB", "beta_I_AB", "C", "w", "Z_star", "chi_BE", "SKR",
    )
    print("\n19-km winning-candidate diagnosis")
    for field in fields:
        print(f"{field:>18}: {row.get(field)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-zen", type=float, default=DEFAULT_TAU_ZEN)
    parser.add_argument("--eta-ao", type=float, default=DEFAULT_ETA_AO)
    args = parser.parse_args()
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    radius_m = float(config["channel"]["aperture_radius_m"])
    if not math.isclose(radius_m, BASELINE_RADIUS_M, rel_tol=0.0, abs_tol=1.0e-15):
        raise RuntimeError(f"Expected original aperture radius {BASELINE_RADIUS_M}, found {radius_m}.")
    candidates, skipped = load_candidates(config)
    uniform = [row for row in candidates if row["family"] == "Uniform"]
    mb = [row for row in candidates if row["family"] == "MB"]
    if not uniform or not mb:
        raise RuntimeError("Historical exact audit did not provide Uniform and MB candidates.")

    baseline_rows, baseline_errors, channel = evaluate_phase(
        config, uniform, mb, cn2_phase=DEFAULT_CN2_VALUES[0], tau_zen=args.tau_zen, eta_ao=args.eta_ao
    )
    baseline_winners = winners(baseline_rows)
    for row in baseline_winners.values():
        print_diagnosis(row)

    sweep_rows = []
    evaluated = {}
    for cn2_phase in DEFAULT_CN2_VALUES:
        rows_by_curve, errors, channel_summary = evaluate_phase(
            config, uniform, mb, cn2_phase=cn2_phase, tau_zen=args.tau_zen, eta_ao=args.eta_ao
        )
        evaluated[float(cn2_phase)] = (rows_by_curve, errors, channel_summary)
        sweep_rows.append(phase_summary_row(cn2_phase, rows_by_curve, channel_summary, errors))

    threshold = None
    threshold_row = None
    positive_indices = [index for index, row in enumerate(sweep_rows) if row["all_three_positive"]]
    if positive_indices:
        index = min(positive_indices)
        threshold_row = sweep_rows[index]
        threshold = float(threshold_row["C_nphi2"])
        if index > 0:
            high = float(sweep_rows[index - 1]["C_nphi2"])
            low = threshold
            for _ in range(12):
                midpoint = 0.5 * (low + high)
                rows_by_curve, errors, channel_summary = evaluate_phase(
                    config, uniform, mb, cn2_phase=midpoint, tau_zen=args.tau_zen, eta_ao=args.eta_ao
                )
                midpoint_row = phase_summary_row(midpoint, rows_by_curve, channel_summary, errors)
                if midpoint_row["all_three_positive"]:
                    low = midpoint
                    threshold_row = midpoint_row
                else:
                    high = midpoint
            threshold = low

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "phase_sensitivity.csv", sweep_rows)
    diagnosis = {
        "status": "ALL_POSITIVE_PHASE_THRESHOLD_FOUND" if threshold is not None else "STOP_PHASE_SWEEP_INSUFFICIENT",
        "new_source_moments_computed": False,
        "source_policy": "historical_source_moment_audit_only",
        "channel": {
            "tau_zen": args.tau_zen,
            "cn2_phase_baseline": DEFAULT_CN2_VALUES[0],
            "eta_ao": args.eta_ao,
            "beta": float(config["cvqkd"]["beta_reconciliation"]),
            "epsilon_ch_snu": float(config["channel"]["excess_noise_distribution"]["epsilon_ch_snu"]),
            "T_convention": "<sqrt(T_raw)>^2",
            "maximize_full_interval": False,
        },
        "aperture": {"radius_m": radius_m, "diameter_m": BASELINE_DIAMETER_M},
        "distance_km": DISTANCE_KM,
        "candidate_counts": {"uniform": len(uniform), "mb_nu_raw_0p05_to_0p20": len(mb), "skipped": len(skipped)},
        "channel_summary": channel,
        "baseline_winners": baseline_winners,
        "baseline_errors": baseline_errors,
        "sweep": sweep_rows,
        "C_nphi2_all_positive_threshold": threshold,
        "threshold_row": threshold_row,
        "full_distance_sweep_written": False,
    }

    if threshold is None:
        diagnosis["stop_reason"] = "C_n,phi^2=1e-18 did not make all three historical-exact envelopes positive."
        diagnosis["remaining_negative_decomposition"] = {
            row["C_nphi2"]: {
                curve: {"beta_I_AB": max(evaluated[row["C_nphi2"]][0][curve], key=lambda item: float(item["SKR"]))["beta_I_AB"], "chi_BE": max(evaluated[row["C_nphi2"]][0][curve], key=lambda item: float(item["SKR"]))["chi_BE"], "SKR": row[key]}
                for curve, key in (("Uniform", "K_uniform"), ("MB with AO", "K_MB_AO"), ("MB without AO", "K_MB_noAO"))
                if row[key] <= 0.0
            }
            for row in sweep_rows[-1:]
        }
    else:
        distances = tuple(sorted(set(_grid(19.0, 100.0, 2.0) + (BASELINE_DISTANCE_KM,))))
        rows_by_curve = {curve: [] for curve in CURVE_NAMES}
        full_errors = []
        for distance_km in distances:
            rows, errors, _ = evaluate_phase(config, uniform, mb, cn2_phase=threshold, tau_zen=args.tau_zen, eta_ao=args.eta_ao, distance_km=distance_km)
            for curve in CURVE_NAMES:
                rows_by_curve[curve].extend(rows[curve])
            full_errors.extend({"distance_km": distance_km, **error} for error in errors)
        envelopes = {curve: envelope(rows, curve) for curve, rows in rows_by_curve.items()}
        summaries = [crossing(envelopes[curve], curve) for curve in CURVE_NAMES]
        for summary in summaries:
            summary["source_candidate_set"] = "historical exact audit only"
            summary["C_nphi2"] = threshold
        write_csv(OUTPUT / "skr_vs_link_distance_phase_favorable.csv", [row for curve in CURVE_NAMES for row in envelopes[curve]])
        write_csv(OUTPUT / "operation_distance_summary.csv", summaries)
        plot_distance(OUTPUT / "skr_vs_link_distance_phase_favorable", envelopes, summaries, threshold)
        diagnosis["full_distance_sweep_written"] = True
        diagnosis["full_distance_grid_km"] = list(distances)
        diagnosis["operation_distance_summary"] = summaries
        diagnosis["full_distance_candidate_errors"] = full_errors

    (OUTPUT / "phase_sensitivity_report.json").write_text(json.dumps(diagnosis, indent=2) + "\n", encoding="utf-8")
    print("\nPhase sensitivity summary")
    for row in sweep_rows:
        print(f"C_nphi2={row['C_nphi2']:.3g} | tau_phi2={row['tau_phi2']:.9g} | Uniform={row['K_uniform']:.9g} | MB+AO={row['K_MB_AO']:.9g} | MB-noAO={row['K_MB_noAO']:.9g} | all_positive={row['all_three_positive']}")
    print(f"C_nphi2_all_positive_threshold={threshold}")
    if threshold is None:
        print("STOP: C_nphi2=1e-18 did not make all three schemes positive; no full distance sweep.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
