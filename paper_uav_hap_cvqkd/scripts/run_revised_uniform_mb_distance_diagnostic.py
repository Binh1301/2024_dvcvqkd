"""Diagnostic-only Uniform/MB SKR comparison for the revised optical baseline.

The channel is recomputed at every link distance.  Security evaluation is
restricted to current-compatible historical C,w rows, so every envelope point
is the best exact-tested candidate in the available cache, not a continuous
optimization result.  No source moments, interpolation, or Binomial rows are
created here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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
from scripts import run_hap_uav_sayat_forensic_diagnostic as forensic
from scripts import run_uniform_beam_waist_diagnostic as optical
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates


OUTPUT = ROOT / "results" / "revised_uniform_mb_distance_diagnostic"
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
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
    30.0,
)
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
EXACT_STATUS = "SAFE_CURRENT_HASH_MATCHED_EXACT_CW"
SOURCE_POLICY = "historical_exact_audit_only"
PLOT_TITLE_SUFFIX = "Diagnostic-only, exact-available candidates"


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


def _protocol(candidate: dict) -> str:
    return "Uniform 256-QAM" if candidate["family"] == "Uniform" else "MB-shaped 256-QAM"


def _configure() -> None:
    optical.TAU_ZEN = TAU_ZEN
    optical.EPSILON = EPSILON
    forensic.BETA = BETA


def _channel(config: dict, distance_km: float) -> dict:
    row, _ = optical._channel_row(
        config,
        w0_m=W0_M,
        receiver_diameter_m=RECEIVER_DIAMETER_M,
        distance_km=float(distance_km),
    )
    return row


def _candidate_row(candidate: dict, config: dict, channel: dict) -> dict:
    evaluated = forensic.evaluate(
        candidate,
        config,
        float(channel["T_eff"]),
        EPSILON,
        compare_full_interval=False,
    )
    is_uniform = candidate["family"] == "Uniform"
    identifier = candidate["ensemble_hash"]
    row = {
        "distance_km": float(channel["distance_km"]),
        "zeta_deg": float(channel["zeta_deg"]),
        "protocol": _protocol(candidate),
        "family": candidate["family"],
        "V_A": float(candidate["V_A"]),
        "nu": None if is_uniform else float(candidate["nu_raw"]),
        "nu_repo": None if is_uniform else float(candidate["nu_repo"]),
        "C": float(candidate["C"]),
        "w": float(candidate["w"]),
        "I_AB": float(evaluated["I_AB"]),
        "beta_I_AB": float(evaluated["beta_I_AB"]),
        "chi_BE": float(evaluated["chi_BE_direct"]),
        "SKR": float(evaluated["SKR_direct"]),
        "Z_star": float(evaluated["Z_direct"]),
        "source/cache identifier": identifier,
        "source_cache_identifier": identifier,
        "exact-status": EXACT_STATUS,
        "exact_status": EXACT_STATUS,
        "source_policy": SOURCE_POLICY,
        "source_record_count": int(candidate["historical_record_count"]),
        "security_evaluator": "historical_exact_cw_direct_Z",
        "channel_recomputed_at_distance": True,
        "T_eff": float(channel["T_eff"]),
        "loss_dB": float(channel["loss_dB"]),
        "w0_m": float(channel["w0_m"]),
        "receiver_diameter_m": float(channel["receiver_diameter_m"]),
        "omega_L_eq_m": float(channel["omega_L_eq_m"]),
        "A0": float(channel["A0"]),
        "mean_T_raw": float(channel["mean_T_raw"]),
        "mean_sqrt_T_raw": float(channel["mean_sqrt_T_raw"]),
        "p_in": float(channel["p_in"]),
        "p_out": float(channel["p_out"]),
        "epsilon": EPSILON,
        "beta": BETA,
        "AO": "OFF",
        "phase_noise": "OFF",
        "budget_snu": float(config["cvqkd"]["v_a_budget_snu"]),
        "budget_feasible": float(candidate["V_A"]) <= float(config["cvqkd"]["v_a_budget_snu"]),
    }
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
        "T_eff": float(row["T_eff"]),
        "loss_dB": float(row["loss_dB"]),
        "source_cache_identifier": row["source_cache_identifier"],
        "exact_status": row["exact_status"],
    }


def _best(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("No exact candidate rows are available.")
    return max(rows, key=lambda row: float(row["SKR"]))


def _sign_endpoint(rows: list[dict], *, positive: bool) -> dict | None:
    ordered = sorted(rows, key=lambda row: float(row["distance_km"]))
    matching = [
        row for row in ordered
        if (float(row["SKR"]) > 0.0 if positive else float(row["SKR"]) < 0.0)
    ]
    if not matching:
        return None
    row = matching[-1] if positive else matching[0]
    return {
        "distance_km": float(row["distance_km"]),
        "SKR": float(row["SKR"]),
        "V_A": float(row["V_A"]),
        "nu": row["nu"],
    }


def _protocol_summary(protocol: str, envelope: list[dict]) -> dict:
    rows = [row for row in envelope if row["protocol"] == protocol]
    ordered = sorted(rows, key=lambda row: float(row["distance_km"]))
    at_22 = next(row for row in ordered if math.isclose(float(row["distance_km"]), 22.0, abs_tol=1e-12))
    at_25 = next(row for row in ordered if math.isclose(float(row["distance_km"]), 25.0, abs_tol=1e-12))
    last_positive = _sign_endpoint(ordered, positive=True)
    first_negative = _sign_endpoint(ordered, positive=False)
    return {
        "protocol": protocol,
        "exact_candidate_count": int(ordered[0]["candidate_count"]),
        "distance_count": len(ordered),
        "last_exact_positive": last_positive,
        "first_exact_negative": first_negative,
        "zero_crossing_report": "LAST_EXACT_POSITIVE_AND_FIRST_EXACT_NEGATIVE_ONLY_NO_INTERPOLATION",
        "at_22km": _selection(at_22),
        "at_25km": _selection(at_25),
        "source_policy": SOURCE_POLICY,
        "optimization_status": "BEST_EXACT_TESTED_CANDIDATE_ONLY",
    }


def _comparison(envelope: list[dict]) -> dict:
    grouped: dict[float, dict[str, dict]] = {}
    for row in envelope:
        grouped.setdefault(float(row["distance_km"]), {})[row["protocol"]] = row
    mb_above = []
    uniform_above = []
    ties = []
    differences = []
    for distance in sorted(grouped):
        uniform = grouped[distance]["Uniform 256-QAM"]
        mb = grouped[distance]["MB-shaped 256-QAM"]
        delta = float(mb["SKR"]) - float(uniform["SKR"])
        differences.append({"distance_km": distance, "MB_minus_Uniform_SKR": delta})
        if delta > 0.0:
            mb_above.append(distance)
        elif delta < 0.0:
            uniform_above.append(distance)
        else:
            ties.append(distance)
    if mb_above and not uniform_above and not ties:
        assessment = "MB envelope above Uniform at every tested distance"
    elif uniform_above and not mb_above and not ties:
        assessment = "Uniform envelope above MB at every tested distance"
    elif mb_above:
        assessment = "MB advantage is visible at some tested distances, but not all"
    else:
        assessment = "No MB-above-Uniform exact-tested distance was observed"
    return {
        "basis": "best exact-tested candidate at each distance",
        "assessment": assessment,
        "mb_above_uniform_distances_km": mb_above,
        "uniform_above_mb_distances_km": uniform_above,
        "tie_distances_km": ties,
        "differences": differences,
    }


def _save_plot(path: Path, x: list[float], series: dict[str, list[float]], *, ylabel: str, title: str, zero_line: bool = False) -> None:
    colors = {
        "Uniform 256-QAM": "#2563eb",
        "MB-shaped 256-QAM": "#dc2626",
    }
    markers = {
        "Uniform 256-QAM": "o",
        "MB-shaped 256-QAM": "s",
    }
    figure, axis = plt.subplots(figsize=(8.8, 5.4), dpi=160)
    for protocol in PROTOCOLS:
        axis.plot(
            x,
            series[protocol],
            color=colors[protocol],
            marker=markers[protocol],
            markersize=5.0,
            linewidth=1.5,
            label=protocol,
        )
    if zero_line:
        axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9, label="zero SKR")
    axis.set_xlabel("HAP-UAV link distance (km)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(alpha=0.3)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def _plots(output: Path, envelope: list[dict], distances: list[float]) -> None:
    ordered = {
        protocol: sorted(
            [row for row in envelope if row["protocol"] == protocol],
            key=lambda row: float(row["distance_km"]),
        )
        for protocol in PROTOCOLS
    }
    x = [float(distance) for distance in distances]
    _save_plot(
        output / "diagnostic_skr_vs_distance",
        x,
        {protocol: [float(row["SKR"]) for row in ordered[protocol]] for protocol in PROTOCOLS},
        ylabel="SKR (bits/use)",
        title=f"SKR vs HAP-UAV link distance — {PLOT_TITLE_SUFFIX}",
        zero_line=True,
    )
    _save_plot(
        output / "diagnostic_beta_iab_vs_distance",
        x,
        {protocol: [float(row["beta_I_AB"]) for row in ordered[protocol]] for protocol in PROTOCOLS},
        ylabel=r"$\beta I_{AB}$ (bits/use)",
        title=f"$\\beta I_{{AB}}$ vs HAP-UAV link distance — {PLOT_TITLE_SUFFIX}",
    )
    _save_plot(
        output / "diagnostic_chi_be_vs_distance",
        x,
        {protocol: [float(row["chi_BE"]) for row in ordered[protocol]] for protocol in PROTOCOLS},
        ylabel=r"$\chi_{BE}$ (bits/use)",
        title=f"$\\chi_{{BE}}$ vs HAP-UAV link distance — {PLOT_TITLE_SUFFIX}",
    )


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
    mb = [candidate for candidate in candidates if candidate["family"] == "MB"]
    if not uniform or not mb:
        raise RuntimeError(f"Expected exact Uniform and MB rows; got Uniform={len(uniform)}, MB={len(mb)}.")

    details = []
    envelope = []
    channel_rows = []
    for distance in DISTANCES_KM:
        channel = _channel(config, distance)
        channel_rows.append(channel)
        for family_candidates in (uniform, mb):
            candidate_rows = [_candidate_row(candidate, config, channel) for candidate in family_candidates]
            details.extend(candidate_rows)
            best = _best(candidate_rows)
            envelope.append({
                **best,
                "candidate_count": len(candidate_rows),
                "all_exact_candidates_evaluated": True,
                "selection_status": "BEST_EXACT_TESTED_CANDIDATE_ONLY",
                "optimization_status": "NOT_CONTINUOUS_OPTIMIZATION",
            })

    envelope = sorted(envelope, key=lambda row: (float(row["distance_km"]), row["protocol"]))
    details = sorted(details, key=lambda row: (float(row["distance_km"]), row["protocol"], float(row["V_A"]), float(row["nu"] or 0.0)))
    summaries = [_protocol_summary(protocol, envelope) for protocol in PROTOCOLS]
    comparison = _comparison(envelope)

    availability = [
        {
            "family": "Uniform",
            "protocol": "Uniform 256-QAM",
            "available_exact_candidate_count": len(uniform),
            "included": True,
            "safe_current_hash_match": True,
            "reason": "Current-compatible exact historical C,w rows evaluated.",
        },
        {
            "family": "MB",
            "protocol": "MB-shaped 256-QAM",
            "available_exact_candidate_count": len(mb),
            "included": True,
            "safe_current_hash_match": True,
            "reason": "Current-compatible exact historical C,w rows evaluated.",
        },
        {
            "family": "Binomial",
            "protocol": "Binomial 256-QAM",
            "available_exact_candidate_count": 0,
            "included": False,
            "safe_current_hash_match": False,
            "reason": "No safe current-compatible exact C,w dataset; excluded from this diagnostic.",
        },
    ]

    write_csv(OUTPUT / "diagnostic_candidate_details.csv", details)
    write_csv(OUTPUT / "diagnostic_distance_envelope.csv", envelope)
    write_csv(OUTPUT / "protocol_summary.csv", summaries)
    write_csv(OUTPUT / "availability.csv", availability)
    write_csv(OUTPUT / "channel_by_distance.csv", channel_rows)
    _plots(OUTPUT, envelope, list(DISTANCES_KM))

    final_model_spec = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    expected_spec_hash = "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    actual_spec_hash = sha256(final_model_spec)
    report = {
        "status": "REVISED_UNIFORM_MB_DISTANCE_DIAGNOSTIC_COMPLETE_CACHE_ONLY",
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
        },
        "distances_km": list(DISTANCES_KM),
        "channel_recomputed_at_each_distance": True,
        "candidate_counts": {"Uniform": len(uniform), "MB": len(mb), "Binomial": 0},
        "skipped_historical_rows": skipped,
        "source_policy": SOURCE_POLICY,
        "new_source_moments_computed": False,
        "interpolation_used": False,
        "fixed_T_eff_reused": False,
        "optimization_status": "BEST_EXACT_TESTED_CANDIDATE_ONLY; NO_CONTINUOUS_SEARCH",
        "security_evaluator": "historical_exact_cw_direct_Z",
        "protocol_summaries": summaries,
        "qualitative_comparison": comparison,
        "availability": availability,
        "blockers": [
            "tau_zen authorization remains unresolved for publication use",
            "cn_phi2_m_minus_two_thirds authorization remains unresolved",
            "revised optical baseline approval is not recorded",
            "FINAL_MODEL_SPEC hash differs from the historical expected hash",
            "Uniform exact C,w coverage is incomplete for the requested V_A domain",
            "optimized-MB search is not authorized and was not run",
            "Binomial has no safe current-compatible exact C,w dataset",
            "a common feasible grid across all protocols is not established",
        ],
        "provenance": {
            "producer_sha256": sha256(Path(__file__).resolve()),
            "historical_runner_sha256": sha256(ROOT / "scripts" / "run_historical_exact_skr_vs_link_distance.py"),
            "channel_helper_sha256": sha256(ROOT / "scripts" / "run_uniform_beam_waist_diagnostic.py"),
            "final_model_spec_sha256": actual_spec_hash,
            "historical_expected_final_model_spec_sha256": expected_spec_hash,
            "final_model_spec_status": "BLOCKED_BY_HASH_MISMATCH" if actual_spec_hash != expected_spec_hash else "MATCH",
        },
        "plot_title_phrase": PLOT_TITLE_SUFFIX,
        "limitations": [
            "All reported envelopes are maxima over the available exact-tested cache rows only.",
            "The zero-crossing report contains only the last exact positive and first exact negative points; no interpolation was used.",
            "This result does not select a baseline or authorize publication-scale evaluation.",
        ],
    }
    (OUTPUT / "revised_uniform_mb_distance_report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
