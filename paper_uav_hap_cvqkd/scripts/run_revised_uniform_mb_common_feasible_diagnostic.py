"""Fair, exact-cache Uniform/MB comparison on the common V_A budget.

Only current hash-matched C,w rows with 0 < V_A <= 1.5 SNU are evaluated.
Plots use exact markers only; no connecting curve or zero-crossing
interpolation is produced.
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
from scripts import run_revised_uniform_mb_distance_diagnostic as previous
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates
from src.modulation.joint_ps_gs import enforce_peak_photon_constraint


OUTPUT = ROOT / "results" / "revised_uniform_mb_common_feasible_diagnostic"
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
MAX_VA = 1.5
W0_M = 0.10
RECEIVER_DIAMETER_M = 0.55
DISTANCES_KM = (
    19.0,
    20.0,
    21.0,
    21.939310229205777,
    22.0,
    23.0,
    24.0,
    25.0,
    26.0,
    27.0,
    28.0,
    29.0,
    30.0,
)
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
EXACT_STATUS = "SAFE_CURRENT_HASH_MATCHED_EXACT_CW"
SOURCE_POLICY = "historical_exact_audit_only"
PLOT_TITLE = "Diagnostic-only common-feasible comparison"


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _protocol(candidate: dict) -> str:
    return "Uniform 256-QAM" if candidate["family"] == "Uniform" else "MB-shaped 256-QAM"


def _feasible_candidates(candidates: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    n_peak = float(config["cvqkd"]["n_peak_photons"])
    feasible = []
    excluded = []
    for candidate in candidates:
        va = float(candidate["V_A"])
        if not 0.0 < va <= MAX_VA:
            excluded.append({
                "protocol": _protocol(candidate),
                "family": candidate["family"],
                "V_A": va,
                "nu": None if candidate["family"] == "Uniform" else float(candidate["nu_raw"]),
                "source_cache_identifier": candidate["ensemble_hash"],
                "exact_status": EXACT_STATUS,
                "feasibility_status": "EXCLUDED_VA_ABOVE_COMMON_BUDGET",
            })
            continue
        try:
            candidate["ensemble"].validate(tolerance=1e-12)
            enforce_peak_photon_constraint(candidate["ensemble"], n_peak)
        except Exception as error:
            excluded.append({
                "protocol": _protocol(candidate),
                "family": candidate["family"],
                "V_A": va,
                "nu": None if candidate["family"] == "Uniform" else float(candidate["nu_raw"]),
                "source_cache_identifier": candidate["ensemble_hash"],
                "exact_status": EXACT_STATUS,
                "feasibility_status": "EXCLUDED_PEAK_CONSTRAINT",
                "reason": f"{type(error).__name__}: {error}",
            })
            continue
        feasible.append(candidate)
    return feasible, excluded


def _row(candidate: dict, config: dict, channel: dict) -> dict:
    row = previous._candidate_row(candidate, config, channel)
    row.update({
        "common_budget_max_V_A": MAX_VA,
        "common_budget_feasible": True,
        "peak_constraint_feasible": True,
        "peak_constraint_n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
        "selection_scope": "COMMON_FEASIBLE_EXACT_CACHE",
    })
    if float(row["V_A"]) > MAX_VA:
        raise AssertionError("A budget-infeasible candidate entered the fair diagnostic.")
    return row


def _selection(row: dict) -> dict:
    return {
        "distance_km": float(row["distance_km"]),
        "protocol": row["protocol"],
        "V_A": float(row["V_A"]),
        "nu": row["nu"],
        "I_AB": float(row["I_AB"]),
        "beta_I_AB": float(row["beta_I_AB"]),
        "chi_BE": float(row["chi_BE"]),
        "SKR": float(row["SKR"]),
        "source_cache_identifier": row["source_cache_identifier"],
        "exact_status": row["exact_status"],
    }


def _endpoint(rows: list[dict], positive: bool) -> dict | None:
    ordered = sorted(rows, key=lambda row: float(row["distance_km"]))
    matches = [
        row for row in ordered
        if (float(row["SKR"]) > 0.0 if positive else float(row["SKR"]) < 0.0)
    ]
    if not matches:
        return None
    row = matches[-1] if positive else matches[0]
    return {
        "distance_km": float(row["distance_km"]),
        "SKR": float(row["SKR"]),
        "V_A": float(row["V_A"]),
        "nu": row["nu"],
    }


def _summary(protocol: str, envelope: list[dict], total_count: int, excluded_count: int) -> dict:
    rows = sorted(
        [row for row in envelope if row["protocol"] == protocol],
        key=lambda row: float(row["distance_km"]),
    )
    at_22 = next(row for row in rows if math.isclose(float(row["distance_km"]), 22.0))
    at_25 = next(row for row in rows if math.isclose(float(row["distance_km"]), 25.0))
    last_positive = _endpoint(rows, True)
    first_negative = _endpoint(rows, False)
    row = {
        "protocol": protocol,
        "total_safe_exact_candidates": total_count,
        "feasible_exact_candidates": rows[0]["feasible_candidate_count"],
        "excluded_candidates": excluded_count,
        "last_exact_positive_distance_km": None if last_positive is None else last_positive["distance_km"],
        "last_exact_positive_SKR": None if last_positive is None else last_positive["SKR"],
        "first_exact_negative_distance_km": None if first_negative is None else first_negative["distance_km"],
        "first_exact_negative_SKR": None if first_negative is None else first_negative["SKR"],
        "zero_crossing_status": "ENDPOINTS_ONLY_NO_INTERPOLATION",
        "source_policy": SOURCE_POLICY,
        "optimization_status": "BEST_EXACT_TESTED_FEASIBLE_CANDIDATE_ONLY",
    }
    for label, selected in (("22km", at_22), ("25km", at_25)):
        row.update({
            f"V_A_{label}": float(selected["V_A"]),
            f"nu_{label}": selected["nu"],
            f"I_AB_{label}": float(selected["I_AB"]),
            f"beta_I_AB_{label}": float(selected["beta_I_AB"]),
            f"chi_BE_{label}": float(selected["chi_BE"]),
            f"SKR_{label}": float(selected["SKR"]),
            f"source_cache_identifier_{label}": selected["source_cache_identifier"],
        })
    return row


def _attribution(envelope: list[dict]) -> tuple[list[dict], dict]:
    grouped: dict[float, dict[str, dict]] = {}
    for row in envelope:
        grouped.setdefault(float(row["distance_km"]), {})[row["protocol"]] = row
    rows = []
    for distance in sorted(grouped):
        uniform = grouped[distance]["Uniform 256-QAM"]
        mb = grouped[distance]["MB-shaped 256-QAM"]
        delta_beta = float(mb["beta_I_AB"]) - float(uniform["beta_I_AB"])
        delta_chi = float(mb["chi_BE"]) - float(uniform["chi_BE"])
        delta_skr = float(mb["SKR"]) - float(uniform["SKR"])
        rows.append({
            "distance_km": distance,
            "uniform_beta_I_AB": float(uniform["beta_I_AB"]),
            "mb_beta_I_AB": float(mb["beta_I_AB"]),
            "delta_beta_I_AB_MB_minus_Uniform": delta_beta,
            "uniform_chi_BE": float(uniform["chi_BE"]),
            "mb_chi_BE": float(mb["chi_BE"]),
            "delta_chi_BE_MB_minus_Uniform": delta_chi,
            "lower_chi_BE_contribution_to_delta_SKR": -delta_chi,
            "larger_beta_I_AB_contribution_to_delta_SKR": delta_beta,
            "delta_SKR_MB_minus_Uniform": delta_skr,
            "decomposition_error": delta_skr - (delta_beta - delta_chi),
        })
    beta_contribution = sum(max(0.0, row["larger_beta_I_AB_contribution_to_delta_SKR"]) for row in rows)
    lower_chi_contribution = sum(max(0.0, row["lower_chi_BE_contribution_to_delta_SKR"]) for row in rows)
    if beta_contribution > 1.05 * lower_chi_contribution:
        driver = "larger_beta_I_AB"
    elif lower_chi_contribution > 1.05 * beta_contribution:
        driver = "lower_chi_BE"
    else:
        driver = "both_comparable"
    summary = {
        "identity": "delta_SKR = delta_beta_I_AB - delta_chi_BE",
        "driver_rule": "compare summed positive contributions over tested distances with a 5 percent margin",
        "larger_beta_I_AB_positive_contribution_sum": beta_contribution,
        "lower_chi_BE_positive_contribution_sum": lower_chi_contribution,
        "primary_driver": driver,
        "at_22km": next(row for row in rows if math.isclose(row["distance_km"], 22.0)),
        "at_25km": next(row for row in rows if math.isclose(row["distance_km"], 25.0)),
    }
    return rows, summary


def _save_scatter(path: Path, envelope: list[dict], metric: str, ylabel: str, title: str, zero_line: bool = False) -> None:
    colors = {"Uniform 256-QAM": "#2563eb", "MB-shaped 256-QAM": "#dc2626"}
    markers = {"Uniform 256-QAM": "o", "MB-shaped 256-QAM": "s"}
    figure, axis = plt.subplots(figsize=(8.8, 5.4), dpi=160)
    for protocol in PROTOCOLS:
        rows = sorted(
            [row for row in envelope if row["protocol"] == protocol],
            key=lambda row: float(row["distance_km"]),
        )
        axis.scatter(
            [row["distance_km"] for row in rows],
            [row[metric] for row in rows],
            color=colors[protocol],
            marker=markers[protocol],
            s=42,
            label=protocol,
        )
    if zero_line:
        axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9, label="zero SKR")
    axis.set_xlabel("HAP-UAV link distance (km)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    # Keep the extra 21.939-km fixture in the exact data while avoiding a
    # colliding label next to the 22-km tick.
    axis.set_xticks(list(range(19, 31)))
    axis.tick_params(axis="x", labelrotation=45)
    axis.grid(alpha=0.3)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def _sha256(path: Path) -> str:
    return previous.sha256(path)


def main() -> int:
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    OUTPUT = args.output_dir.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    previous._configure()

    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    all_uniform = [candidate for candidate in candidates if candidate["family"] == "Uniform"]
    all_mb = [candidate for candidate in candidates if candidate["family"] == "MB"]
    uniform, uniform_excluded = _feasible_candidates(all_uniform, config)
    mb, mb_excluded = _feasible_candidates(all_mb, config)
    if not uniform or not mb:
        raise RuntimeError(f"No feasible exact rows: Uniform={len(uniform)}, MB={len(mb)}")
    if any(float(candidate["V_A"]) > MAX_VA for candidate in (*uniform, *mb)):
        raise AssertionError("Budget filter failed closed.")

    details = []
    envelope = []
    channel_rows = []
    for distance in DISTANCES_KM:
        channel = previous._channel(config, distance)
        channel_rows.append({
            **channel,
            "common_budget_max_V_A": MAX_VA,
            "channel_recomputed_at_distance": True,
        })
        for family_candidates in (uniform, mb):
            candidate_rows = [_row(candidate, config, channel) for candidate in family_candidates]
            details.extend(candidate_rows)
            best = previous._best(candidate_rows)
            envelope.append({
                **best,
                "feasible_candidate_count": len(candidate_rows),
                "all_feasible_exact_candidates_evaluated": True,
                "selection_status": "BEST_EXACT_TESTED_FEASIBLE_CANDIDATE_ONLY",
                "optimization_status": "NOT_CONTINUOUS_OPTIMIZATION",
            })

    if any(float(row["V_A"]) > MAX_VA for row in details + envelope):
        raise AssertionError("An over-budget row entered the output.")
    envelope = sorted(envelope, key=lambda row: (float(row["distance_km"]), row["protocol"]))
    details = sorted(details, key=lambda row: (float(row["distance_km"]), row["protocol"], float(row["V_A"]), float(row["nu"] or 0.0)))
    attribution_rows, attribution_summary = _attribution(envelope)
    summaries = [
        _summary("Uniform 256-QAM", envelope, len(all_uniform), len(uniform_excluded)),
        _summary("MB-shaped 256-QAM", envelope, len(all_mb), len(mb_excluded)),
    ]

    availability = [
        {
            "family": "Uniform",
            "protocol": "Uniform 256-QAM",
            "total_safe_exact_candidates": len(all_uniform),
            "feasible_exact_candidates_V_A_le_1_5": len(uniform),
            "excluded_over_budget_or_peak_candidates": len(uniform_excluded),
            "included": True,
            "common_budget_max_V_A": MAX_VA,
            "peak_constraint_n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
            "reason": "All included rows pass exact hash, common V_A budget, ensemble validation, and peak guard.",
        },
        {
            "family": "MB",
            "protocol": "MB-shaped 256-QAM",
            "total_safe_exact_candidates": len(all_mb),
            "feasible_exact_candidates_V_A_le_1_5": len(mb),
            "excluded_over_budget_or_peak_candidates": len(mb_excluded),
            "included": True,
            "common_budget_max_V_A": MAX_VA,
            "peak_constraint_n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
            "reason": "All included rows pass exact hash, common V_A budget, ensemble validation, and peak guard.",
        },
        {
            "family": "Binomial",
            "protocol": "Binomial 256-QAM",
            "total_safe_exact_candidates": 0,
            "feasible_exact_candidates_V_A_le_1_5": 0,
            "excluded_over_budget_or_peak_candidates": 0,
            "included": False,
            "common_budget_max_V_A": MAX_VA,
            "peak_constraint_n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
            "reason": "No safe current-compatible exact C,w dataset; excluded from this diagnostic.",
        },
    ]

    write_csv(OUTPUT / "diagnostic_candidate_details.csv", details)
    write_csv(OUTPUT / "diagnostic_distance_envelope.csv", envelope)
    write_csv(OUTPUT / "protocol_summary.csv", summaries)
    write_csv(OUTPUT / "security_term_attribution.csv", attribution_rows)
    write_csv(OUTPUT / "availability.csv", availability)
    write_csv(OUTPUT / "excluded_candidates.csv", uniform_excluded + mb_excluded)
    write_csv(OUTPUT / "channel_by_distance.csv", channel_rows)
    _save_scatter(OUTPUT / "diagnostic_skr_vs_distance", envelope, "SKR", "SKR (bits/use)", PLOT_TITLE, zero_line=True)
    _save_scatter(
        OUTPUT / "diagnostic_beta_iab_vs_distance",
        envelope,
        "beta_I_AB",
        r"$\beta I_{AB}$ (bits/use)",
        r"$\beta I_{AB}$ versus distance — " + PLOT_TITLE,
    )
    _save_scatter(
        OUTPUT / "diagnostic_chi_be_vs_distance",
        envelope,
        "chi_BE",
        r"$\chi_{BE}$ (bits/use)",
        r"$\chi_{BE}$ versus distance — " + PLOT_TITLE,
    )

    final_model_spec = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    expected_spec_hash = "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    actual_spec_hash = _sha256(final_model_spec)
    report = {
        "status": "COMMON_FEASIBLE_UNIFORM_MB_DISTANCE_DIAGNOSTIC_COMPLETE_CACHE_ONLY",
        "scope": "DIAGNOSTIC_ONLY",
        "lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "baseline": {
            "w0_m": W0_M,
            "receiver_diameter_m": RECEIVER_DIAMETER_M,
            "tau_zen": TAU_ZEN,
            "epsilon_ch_snu": EPSILON,
            "beta": BETA,
            "AO": "OFF",
            "phase_noise": "OFF",
            "detection": "heterodyne",
            "reconciliation": "reverse",
        },
        "common_feasible_budget": {
            "V_A_domain": "0 < V_A <= 1.5 SNU",
            "max_V_A": MAX_VA,
            "same_budget_for_both_protocols": True,
            "peak_constraint_n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
            "peak_constraint_enforced": True,
            "previous_unconstrained_MB_winner_excluded": 3.5548673905,
        },
        "distances_km": list(DISTANCES_KM),
        "channel_recomputed_at_each_distance": True,
        "fixed_T_eff_reused": False,
        "candidate_counts": {
            "Uniform_total_safe_exact": len(all_uniform),
            "Uniform_feasible": len(uniform),
            "MB_total_safe_exact": len(all_mb),
            "MB_feasible": len(mb),
            "Binomial_feasible": 0,
        },
        "skipped_historical_rows": skipped,
        "source_policy": SOURCE_POLICY,
        "new_source_moments_computed": False,
        "interpolation_used": False,
        "plot_mode": "EXACT_MARKERS_ONLY_NO_INTERPOLATION",
        "optimization_status": "BEST_EXACT_TESTED_FEASIBLE_CANDIDATE_ONLY",
        "security_evaluator": "historical_exact_cw_direct_Z",
        "protocol_summaries": summaries,
        "security_term_attribution": attribution_summary,
        "availability": availability,
        "excluded_candidates": uniform_excluded + mb_excluded,
        "blockers": [
            "tau_zen authorization remains unresolved for publication use",
            "cn_phi2_m_minus_two_thirds authorization remains unresolved",
            "revised optical baseline approval is not recorded",
            "FINAL_MODEL_SPEC hash differs from the historical expected hash",
            "Uniform exact C,w coverage remains sparse outside the common feasible cache",
            "optimized-MB search is not authorized and was not run",
            "Binomial has no safe current-compatible exact C,w dataset",
            "a common exact V_A candidate grid is not established; only the common budget is enforced",
        ],
        "provenance": {
            "producer_sha256": _sha256(Path(__file__).resolve()),
            "previous_diagnostic_runner_sha256": _sha256(ROOT / "scripts" / "run_revised_uniform_mb_distance_diagnostic.py"),
            "historical_runner_sha256": _sha256(ROOT / "scripts" / "run_historical_exact_skr_vs_link_distance.py"),
            "channel_helper_sha256": _sha256(ROOT / "scripts" / "run_uniform_beam_waist_diagnostic.py"),
            "final_model_spec_sha256": actual_spec_hash,
            "historical_expected_final_model_spec_sha256": expected_spec_hash,
            "final_model_spec_status": "BLOCKED_BY_HASH_MISMATCH" if actual_spec_hash != expected_spec_hash else "MATCH",
        },
        "limitations": [
            "The comparison is over available exact-tested rows within the common V_A budget only.",
            "No C,w interpolation, source-moment generation, global optimization, or precise L_max interpolation was used.",
            "No publication claim is made and no baseline is selected.",
        ],
    }
    artifact_names = (
        "diagnostic_candidate_details.csv",
        "diagnostic_distance_envelope.csv",
        "protocol_summary.csv",
        "security_term_attribution.csv",
        "availability.csv",
        "excluded_candidates.csv",
        "channel_by_distance.csv",
        "diagnostic_skr_vs_distance.png",
        "diagnostic_skr_vs_distance.pdf",
        "diagnostic_beta_iab_vs_distance.png",
        "diagnostic_beta_iab_vs_distance.pdf",
        "diagnostic_chi_be_vs_distance.png",
        "diagnostic_chi_be_vs_distance.pdf",
    )
    report["artifact_sha256"] = {name: _sha256(OUTPUT / name) for name in artifact_names}
    (OUTPUT / "revised_uniform_mb_common_feasible_report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
