"""Find a tested aperture that makes the historical exact envelopes positive.

This is a downstream diagnostic only: it reuses audited historical C,w rows
and changes the receiver aperture in the existing deterministic channel path.
It never builds new source moments.
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
from scripts.calculate_channel_pdf_and_moments import (
    _tail_probability,
    closed_form_channel_moments,
    derive_physical_inputs,
)
from scripts.run_historical_exact_skr_vs_link_distance import (
CURVE_NAMES,
    _grid,
    crossing,
    envelope,
    evaluate_candidate,
    load_candidates,
)

OUTPUT = ROOT / "results" / "skr_vs_link_distance" / "aperture_all_positive_diagnostic"
DEFAULT_DIAMETERS_M = (0.08, 0.10, 0.12, 0.14, 0.16)
DEFAULT_TAU_ZEN = 0.92
DEFAULT_CN2_PHASE = 9.4e-18
DEFAULT_ETA_AO = 0.95
MIN_DISTANCE_KM = 19.0
BASELINE_DISTANCE_KM = 21.939310229205777


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def channel_moments(config: dict, distance_km: float, tau_zen: float, radius_m: float) -> dict:
    channel = config["channel"]
    vertical_m = float(channel["h_hap_m"]) - float(channel["h_uav_m"])
    distance_m = 1_000.0 * float(distance_km)
    if distance_m < vertical_m:
        raise ValueError("Distance is shorter than the HAP-UAV vertical separation.")
    zeta_rad = math.acos(min(1.0, max(-1.0, vertical_m / distance_m)))
    physical = derive_physical_inputs(
        float(tau_zen),
        zenith_angle_rad_override=zeta_rad,
        aperture_radius_m_override=float(radius_m),
    )
    moments = closed_form_channel_moments(
        physical,
        epsilon_total=float(physical["epsilon_ch_snu"]),
    )
    return {
        "distance_km": float(distance_km),
        "zeta_deg": math.degrees(zeta_rad),
        "link_distance_m": float(physical["link_length_m"]),
        "T_mean": float(moments["mean_T_raw"]),
        "sqrtT_mean": float(moments["mean_sqrt_T_raw"]),
        "T_eff": float(moments["T_eff"]),
        "p_raw_gt_1": float(_tail_probability(float(physical["v_sc"]), physical)),
        "physical": physical,
        "moments": moments,
    }


def physical_summary(channel: dict, radius_m: float) -> dict:
    physical = channel["physical"]
    moments = channel["moments"]
    return {
        "distance_km": channel["distance_km"],
        "zeta_deg": channel["zeta_deg"],
        "link_distance_m": channel["link_distance_m"],
        "receiver_radius_m": radius_m,
        "receiver_diameter_m": 2.0 * radius_m,
        "eta_atm": physical["eta_atm"],
        "A_ap": physical["A_ap"],
        "sigma_R0_squared": physical["sigma_R0_squared"],
        "v_sc": physical["v_sc"],
        "sigma_X2": moments["sigma_X2"],
        "A0": moments["A0"],
        "sigma_jt": moments["sigma_jt"],
        "omega_L_eq": moments["omega_L_eq"],
        "chi": moments["chi"],
        "p_in": moments["p_in"],
        "p_out": moments["p_out"],
        "mean_T_raw": moments["mean_T_raw"],
        "mean_sqrt_T_raw": moments["mean_sqrt_T_raw"],
        "T_eff": moments["T_eff"],
        "mean_T_epsilon": moments["mean_T_epsilon"],
        "P_T_raw_gt_1": channel["p_raw_gt_1"],
    }


def evaluate_curve(candidates: list[dict], channel: dict, config: dict, *, ao: bool, cn2_phase: float, eta_ao: float) -> tuple[list[dict], list[dict]]:
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
            row.update({
                "receiver_radius_m": channel["receiver_radius_m"],
                "receiver_diameter_m": channel["receiver_diameter_m"],
                "P_T_raw_gt_1": channel["p_raw_gt_1"],
            })
            rows.append(row)
        except Exception as exc:  # Keep the diagnostic fail-closed per candidate.
            errors.append({
                "family": candidate["family"],
                "nu_raw": candidate["nu_raw"],
                "V_A": candidate["V_A"],
                "error": f"{type(exc).__name__}: {exc}",
            })
    return rows, errors


def evaluate_aperture(config: dict, uniform: list[dict], mb: list[dict], *, diameter_m: float, distance_km: float, tau_zen: float, cn2_phase: float, eta_ao: float) -> tuple[dict, dict[str, list[dict]], list[dict]]:
    radius_m = float(diameter_m) / 2.0
    channel = channel_moments(config, distance_km, tau_zen, radius_m)
    channel["receiver_radius_m"] = radius_m
    channel["receiver_diameter_m"] = float(diameter_m)
    raw = {curve: [] for curve in CURVE_NAMES}
    errors = []
    rows, failed = evaluate_curve(uniform, channel, config, ao=True, cn2_phase=cn2_phase, eta_ao=eta_ao)
    raw["Uniform"].extend(rows)
    errors.extend({"curve": "Uniform", **item} for item in failed)
    rows, failed = evaluate_curve(mb, channel, config, ao=True, cn2_phase=cn2_phase, eta_ao=eta_ao)
    raw["MB with AO"].extend(rows)
    errors.extend({"curve": "MB with AO", **item} for item in failed)
    rows, failed = evaluate_curve(mb, channel, config, ao=False, cn2_phase=cn2_phase, eta_ao=eta_ao)
    raw["MB without AO"].extend(rows)
    errors.extend({"curve": "MB without AO", **item} for item in failed)
    return physical_summary(channel, radius_m), raw, errors


def plot_distance(path: Path, envelopes: dict[str, list[dict]], summaries: list[dict], diameter_m: float) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
    figure, ax = plt.subplots(figsize=(10.5, 6.3), dpi=160)
    colors = {"Uniform": "#64748b", "MB with AO": "#2563eb", "MB without AO": "#dc2626"}
    for curve in CURVE_NAMES:
        rows = envelopes[curve]
        ax.plot(
            [row["distance_km"] for row in rows],
            [row["SKR"] for row in rows],
            label=curve,
            color=colors[curve],
            linewidth=1.8,
            marker="o",
            markersize=3.5,
        )
        summary = next(item for item in summaries if item["curve"] == curve)
        estimate = summary.get("operation_distance_estimate_km")
        if estimate is not None:
            ax.axvline(estimate, color=colors[curve], linestyle="--", linewidth=0.8, alpha=0.65)
            ax.text(estimate, 0.02, f"{curve}: {estimate:.1f} km", rotation=90, color=colors[curve], fontsize=8, va="bottom", ha="right")
    ax.axhline(0.0, color="#111827", linewidth=0.9, linestyle=(0, (4, 3)))
    ax.set_xlabel("Link distance L (km)")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title(f"Historical exact SKR vs link distance (D_r={diameter_m:.2f} m)", weight="bold")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="both", color="#cbd5e1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=True)
    figure.text(0.5, 0.018, "Historical exact C,w reuse only; no new source moments or interpolation.", ha="center", va="bottom", fontsize=8.5, color="#475569")
    figure.subplots_adjust(left=0.10, right=0.96, bottom=0.14, top=0.90)
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-zen", type=float, default=DEFAULT_TAU_ZEN)
    parser.add_argument("--cn2-phase", type=float, default=DEFAULT_CN2_PHASE)
    parser.add_argument("--eta-ao", type=float, default=DEFAULT_ETA_AO)
    args = parser.parse_args()
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    uniform = [row for row in candidates if row["family"] == "Uniform"]
    mb = [row for row in candidates if row["family"] == "MB"]
    if not uniform or not mb:
        raise RuntimeError("Historical exact audit did not provide Uniform and MB candidates.")

    sensitivity = []
    tested_details = []
    selected = None
    for diameter_m in DEFAULT_DIAMETERS_M:
        physical, raw, errors = evaluate_aperture(
            config,
            uniform,
            mb,
            diameter_m=diameter_m,
            distance_km=MIN_DISTANCE_KM,
            tau_zen=args.tau_zen,
            cn2_phase=args.cn2_phase,
            eta_ao=args.eta_ao,
        )
        row = {"receiver_diameter_m": diameter_m, "receiver_radius_m": diameter_m / 2.0, "distance_km": MIN_DISTANCE_KM, **{key: value for key, value in physical.items() if key not in {"distance_km", "receiver_radius_m", "receiver_diameter_m"}}}
        row["all_three_positive"] = bool(all(float(max(rows, key=lambda item: float(item["SKR"]))["SKR"]) > 0.0 for rows in raw.values()))
        for curve in CURVE_NAMES:
            best = max(raw[curve], key=lambda item: float(item["SKR"]))
            prefix = curve.lower().replace(" ", "_")
            row[f"{prefix}_SKR"] = float(best["SKR"])
            row[f"{prefix}_nu_raw"] = float(best["nu_raw"])
            row[f"{prefix}_V_A"] = float(best["V_A"])
        row["candidate_failures"] = len(errors)
        sensitivity.append(row)
        tested_details.append({"diameter_m": diameter_m, "physical": physical, "errors": errors})
        if selected is None and row["all_three_positive"]:
            selected = diameter_m
            break

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "aperture_sensitivity.csv", sensitivity)
    metadata = {
        "status": "ALL_THREE_POSITIVE_APERTURE_FOUND" if selected is not None else "NO_ALL_POSITIVE_DIAMETER_IN_TESTED_RANGE",
        "new_source_moments_computed": False,
        "source_policy": "historical_source_moment_audit_only",
        "channel": {
            "tau_zen": args.tau_zen,
            "cn2_phase": args.cn2_phase,
            "eta_ao": args.eta_ao,
            "beta": float(config["cvqkd"]["beta_reconciliation"]),
            "epsilon_ch_snu": float(config["channel"]["excess_noise_distribution"]["epsilon_ch_snu"]),
            "maximize_full_interval": False,
            "T_convention": "<sqrt(T_raw)>^2",
        },
        "radius_diameter_convention": "config aperture_radius_m is receiver radius; receiver diameter is 2*radius and is passed to finite-aperture scintillation",
        "minimum_distance_km": MIN_DISTANCE_KM,
        "tested_diameters_m": list(DEFAULT_DIAMETERS_M),
        "selected_diameter_m": selected,
        "selected_radius_m": None if selected is None else selected / 2.0,
        "candidate_counts": {"uniform": len(uniform), "mb_nu_raw_0p05_to_0p20": len(mb), "skipped": len(skipped)},
        "sensitivity": sensitivity,
        "tested_details": tested_details,
        "full_sweep_written": selected is not None,
    }
    (OUTPUT / "selected_aperture_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if selected is None:
        print(json.dumps(metadata, indent=2))
        return 0

    distances = tuple(sorted(set(_grid(19.0, 100.0, 2.0) + (BASELINE_DISTANCE_KM,))))
    radius_m = selected / 2.0
    rows_by_curve = {curve: [] for curve in CURVE_NAMES}
    errors = []
    for distance_km in distances:
        channel = channel_moments(config, distance_km, args.tau_zen, radius_m)
        channel["receiver_radius_m"] = radius_m
        channel["receiver_diameter_m"] = selected
        rows, failed = evaluate_curve(uniform, channel, config, ao=True, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao)
        rows_by_curve["Uniform"].extend(rows)
        errors.extend({"curve": "Uniform", "distance_km": distance_km, **item} for item in failed)
        rows, failed = evaluate_curve(mb, channel, config, ao=True, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao)
        rows_by_curve["MB with AO"].extend(rows)
        errors.extend({"curve": "MB with AO", "distance_km": distance_km, **item} for item in failed)
        rows, failed = evaluate_curve(mb, channel, config, ao=False, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao)
        rows_by_curve["MB without AO"].extend(rows)
        errors.extend({"curve": "MB without AO", "distance_km": distance_km, **item} for item in failed)

    envelopes = {curve: envelope(rows, curve) for curve, rows in rows_by_curve.items()}
    summaries = [crossing(envelopes[curve], curve) for curve in CURVE_NAMES]
    source_labels = {
        "Uniform": f"historical exact Uniform V_A set ({len(uniform)} pairs)",
        "MB with AO": f"historical exact MB nu_raw 0.05-0.20 ({len(mb)} pairs)",
        "MB without AO": f"historical exact MB nu_raw 0.05-0.20 ({len(mb)} pairs)",
    }
    for summary in summaries:
        summary["source_candidate_set"] = source_labels[summary["curve"]]
        summary["receiver_diameter_m"] = selected
    combined = [row for curve in CURVE_NAMES for row in envelopes[curve]]
    write_csv(OUTPUT / "skr_vs_link_distance_all_positive.csv", combined)
    write_csv(OUTPUT / "operation_distance_summary.csv", summaries)
    plot_distance(OUTPUT / "skr_vs_link_distance_all_positive", envelopes, summaries, selected)
    metadata["operation_distance_summary"] = summaries
    metadata["full_sweep_distance_grid_km"] = list(distances)
    metadata["full_sweep_candidate_failures"] = errors
    metadata["full_sweep_status"] = "COMPLETE" if not errors else "COMPLETE_WITH_CANDIDATE_ERRORS"
    (OUTPUT / "selected_aperture_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
