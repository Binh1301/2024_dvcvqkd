"""Cache-only Uniform beam-waist/receiver-aperture SKR diagnostic.

The optical channel is recomputed for every ``w0`` and receiver diameter.
Security evaluation is deliberately limited to current hash-matched historical
Uniform C,w rows; no source moments are generated, interpolated, or migrated.
Consequently every optimization result is labelled ``best_tested_exact`` and
cannot establish the continuous Uniform V_A optimum or a publication baseline.
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
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    closed_form_channel_moments,
    derive_physical_inputs,
)
from scripts.run_hap_uav_sayat_forensic_diagnostic import evaluate
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates


OUTPUT = ROOT / "results" / "beam_waist_diagnostic"
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
ZENITH_DEG = 30.0
BASELINE_W0 = 0.004424935637532516
REQUESTED_W0 = (
    0.0044,
    0.0075,
    0.010,
    0.015,
    0.020,
    0.030,
    0.040,
    0.050,
    0.075,
    0.100,
    0.125,
    0.150,
)
HEATMAP_W0 = (0.005, 0.010, 0.020, 0.030, 0.050, 0.075, 0.100, 0.150)
HEATMAP_DIAMETERS = (0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00)
DISTANCES_KM = (19.0, 22.0, 25.0, 30.0, 35.0, 40.0, 50.0)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _loss_db(value: float) -> float:
    return -10.0 * math.log10(float(value))


def _channel_row(
    config: dict,
    *,
    w0_m: float,
    receiver_diameter_m: float,
    distance_km: float | None = None,
) -> tuple[dict, dict]:
    channel = config["channel"]
    vertical_m = float(channel["h_hap_m"]) - float(channel["h_uav_m"])
    if distance_km is None:
        zenith_rad = math.radians(ZENITH_DEG)
    else:
        distance_m = 1000.0 * float(distance_km)
        if distance_m < vertical_m:
            raise ValueError("Distance is shorter than the fixed vertical separation.")
        zenith_rad = math.acos(vertical_m / distance_m)
    physical = derive_physical_inputs(
        TAU_ZEN,
        zenith_angle_rad_override=zenith_rad,
        aperture_radius_m_override=receiver_diameter_m / 2.0,
        beam_waist_m_override=w0_m,
    )
    moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
    pointing = physical["pointing"]
    chi = float(moments["chi"])
    pointing_factor = (chi**2 / (chi**2 + 0.5)) ** 2
    row = {
        "w0_m": float(w0_m),
        "w0_mm": 1000.0 * float(w0_m),
        "receiver_diameter_m": float(receiver_diameter_m),
        "distance_km": None if distance_km is None else float(distance_km),
        "zeta_deg": math.degrees(zenith_rad),
        "rayleigh_range_m": float(pointing["rayleigh_range_m"]),
        "theta_G_half_angle_rad": float(physical["wavelength_m"] / (math.pi * w0_m)),
        "theta_div_full_angle_rad": float(physical["theta_div_rad"]),
        "omega_L_m": float(pointing["omega_L_m"]),
        "omega_L_eq_m": float(pointing["omega_L_eq_m"]),
        "G_d": float(pointing["G_d"]),
        "nu_aperture": float(pointing["nu"]),
        "A0": float(moments["A0"]),
        "chi": chi,
        "mean_T_raw": float(moments["mean_T_raw"]),
        "mean_sqrt_T_raw": float(moments["mean_sqrt_T_raw"]),
        "T_eff": float(moments["T_eff"]),
        "loss_dB": _loss_db(moments["T_eff"]),
        "atmosphere_loss_dB": _loss_db(moments["eta_atm"]),
        "finite_aperture_beam_loss_dB": _loss_db(moments["A0"]),
        "pointing_jitter_loss_dB": _loss_db(pointing_factor),
        "scintillation_loss_dB": _loss_db(math.exp(-float(moments["sigma_X2"]))),
        "aoa_active_probability_loss_dB": _loss_db(float(moments["p_in"]) ** 2),
        "sigma_jt_m": float(moments["sigma_jt"]),
        "eta_atm": float(moments["eta_atm"]),
        "p_in": float(moments["p_in"]),
        "p_out": float(moments["p_out"]),
        "sigma_X2": float(moments["sigma_X2"]),
        "epsilon": EPSILON,
        "AO": "OFF",
        "phase_noise": "OFF",
    }
    return row, physical


def _source_candidate_rows(candidates: list[dict], config: dict, channel_row: dict) -> list[dict]:
    rows = []
    for candidate in candidates:
        evaluated = evaluate(
            candidate,
            config,
            float(channel_row["T_eff"]),
            EPSILON,
            compare_full_interval=True,
        )
        rows.append({
            **channel_row,
            "family": candidate["family"],
            "V_A": float(candidate["V_A"]),
            "C": float(candidate["C"]),
            "w": float(candidate["w"]),
            "ensemble_hash": candidate["ensemble_hash"],
            "I_AB": evaluated["I_AB"],
            "beta_I_AB": evaluated["beta_I_AB"],
            "chi_BE_direct": evaluated["chi_BE_direct"],
            "SKR_direct": evaluated["SKR_direct"],
            "Z_direct": evaluated["Z_direct"],
            "chi_BE_full_interval": evaluated["chi_BE_full_interval"],
            "SKR_full_interval": evaluated["SKR_full_interval"],
            "Z_full_interval": evaluated["Z_full_interval"],
            "source_policy": "historical_exact_audit_only",
        })
    return rows


def _best(rows: list[dict], metric: str = "SKR_direct") -> dict:
    if not rows:
        raise ValueError("No exact candidate rows are available.")
    return max(rows, key=lambda row: float(row[metric]))


def _summary_row(channel_row: dict, candidate_rows: list[dict]) -> dict:
    direct = _best(candidate_rows, "SKR_direct")
    full = _best(candidate_rows, "SKR_full_interval")
    return {
        **channel_row,
        "exact_uniform_candidate_count": len(candidate_rows),
        "V_A_opt_best_tested_direct": direct["V_A"],
        "beta_I_AB_best_tested_direct": direct["beta_I_AB"],
        "chi_BE_best_tested_direct": direct["chi_BE_direct"],
        "SKR_max_best_tested_direct": direct["SKR_direct"],
        "V_A_opt_best_tested_full_interval": full["V_A"],
        "beta_I_AB_best_tested_full_interval": full["beta_I_AB"],
        "chi_BE_best_tested_full_interval": full["chi_BE_full_interval"],
        "SKR_max_best_tested_full_interval": full["SKR_full_interval"],
        "direct_full_winner_agree": bool(direct["V_A"] == full["V_A"]),
        "any_positive_best_tested_direct": bool(direct["SKR_direct"] > 0.0),
        "optimization_status": "BEST_TESTED_EXACT_UNIFORM_CANDIDATE_NOT_CONTINUOUS_OPTIMUM",
    }


def _unique_sorted(values: list[float]) -> list[float]:
    return sorted({round(float(value), 14) for value in values})


def _evaluate_w0_grid(config: dict, candidates: list[dict], values: list[float], receiver_diameter_m: float) -> tuple[list[dict], list[dict]]:
    summaries = []
    details = []
    for w0_m in _unique_sorted(values):
        channel_row, _ = _channel_row(
            config,
            w0_m=w0_m,
            receiver_diameter_m=receiver_diameter_m,
        )
        candidate_rows = _source_candidate_rows(candidates, config, channel_row)
        summaries.append(_summary_row(channel_row, candidate_rows))
        details.extend(candidate_rows)
    return summaries, details


def _refine_crossings(config: dict, candidates: list[dict], rows: list[dict], receiver_diameter_m: float) -> list[dict]:
    ordered = sorted(rows, key=lambda row: float(row["w0_m"]))
    refined = []
    for left, right in zip(ordered, ordered[1:]):
        k_left = float(left["SKR_max_best_tested_direct"])
        k_right = float(right["SKR_max_best_tested_direct"])
        if not (k_left <= 0.0 < k_right or k_right <= 0.0 < k_left):
            continue
        low, high = float(left["w0_m"]), float(right["w0_m"])
        low_k, high_k = k_left, k_right
        for _ in range(32):
            midpoint = 0.5 * (low + high)
            point, details = _evaluate_w0_grid(config, candidates, [midpoint], receiver_diameter_m)
            candidate = point[0]
            refined.append(candidate)
            if low_k <= 0.0 < high_k:
                if float(candidate["SKR_max_best_tested_direct"]) > 0.0:
                    high, high_k = midpoint, float(candidate["SKR_max_best_tested_direct"])
                else:
                    low, low_k = midpoint, float(candidate["SKR_max_best_tested_direct"])
            else:
                if float(candidate["SKR_max_best_tested_direct"]) > 0.0:
                    low, low_k = midpoint, float(candidate["SKR_max_best_tested_direct"])
                else:
                    high, high_k = midpoint, float(candidate["SKR_max_best_tested_direct"])
    return refined


def _transmitter_rows(w0_m: float, wavelength_m: float) -> list[dict]:
    rows = []
    for truncation_radius_over_w0 in (1.0, 1.25, 1.5):
        rows.append({
            "w0_m": float(w0_m),
            "w0_mm": 1000.0 * float(w0_m),
            "truncation_radius_over_w0": truncation_radius_over_w0,
            "estimated_transmitter_diameter_m": 2.0 * truncation_radius_over_w0 * float(w0_m),
            "power_inside_aperture": 1.0 - math.exp(-2.0 * truncation_radius_over_w0**2),
            "theta_G_half_angle_rad": wavelength_m / (math.pi * w0_m),
            "theta_div_full_angle_rad": 2.0 * wavelength_m / (math.pi * w0_m),
        })
    return rows


def _classification(diameter_m: float | None) -> str:
    if diameter_m is None:
        return "UNRESOLVED_NO_POSITIVE_TESTED_CANDIDATE"
    if diameter_m <= 0.10:
        return "physically_easy"
    if diameter_m <= 0.30:
        return "realistic"
    if diameter_m <= 0.50:
        return "challenging"
    return "unrealistic_for_0p3m_class_reference"


def _receiver_threshold(config: dict, candidates: list[dict], w0_m: float) -> dict:
    low, high = 0.08, 1.0

    def score(diameter_m: float) -> tuple[float, dict]:
        channel_row, _ = _channel_row(
            config,
            w0_m=w0_m,
            receiver_diameter_m=diameter_m,
        )
        details = _source_candidate_rows(candidates, config, channel_row)
        best = _best(details, "SKR_direct")
        return float(best["SKR_direct"]), best

    low_score, low_best = score(low)
    high_score, high_best = score(high)
    if low_score > 0.0:
        return {
            "w0_m": w0_m,
            "status": "POSITIVE_AT_LOWER_TESTED_RECEIVER_DIAMETER",
            "receiver_diameter_threshold_m": low,
            "SKR_at_threshold": low_score,
            "V_A_at_threshold": low_best["V_A"],
        }
    if high_score <= 0.0:
        return {
            "w0_m": w0_m,
            "status": "NO_POSITIVE_TESTED_UP_TO_1M_RECEIVER",
            "receiver_diameter_threshold_m": None,
            "SKR_at_threshold": high_score,
            "V_A_at_threshold": high_best["V_A"],
        }
    best = high_best
    for _ in range(32):
        midpoint = 0.5 * (low + high)
        midpoint_score, midpoint_best = score(midpoint)
        if midpoint_score > 0.0:
            high, high_score, best = midpoint, midpoint_score, midpoint_best
        else:
            low, low_score = midpoint, midpoint_score
    return {
        "w0_m": w0_m,
        "status": "SPARSE_EXACT_CANDIDATE_RECEIVER_THRESHOLD",
        "receiver_diameter_threshold_m": high,
        "SKR_at_threshold": high_score,
        "V_A_at_threshold": best["V_A"],
    }


def _distance_rows(
    config: dict,
    candidates: list[dict],
    w0_m: float,
    label: str,
    receiver_diameter_m: float = 0.08,
) -> list[dict]:
    rows = []
    for distance_km in DISTANCES_KM:
        channel_row, _ = _channel_row(
            config,
            w0_m=w0_m,
            receiver_diameter_m=receiver_diameter_m,
            distance_km=distance_km,
        )
        details = _source_candidate_rows(candidates, config, channel_row)
        best = _best(details, "SKR_direct")
        rows.append({
            **channel_row,
            "w0_label": label,
            "V_A_opt_best_tested": best["V_A"],
            "beta_I_AB": best["beta_I_AB"],
            "chi_BE": best["chi_BE_direct"],
            "SKR": best["SKR_direct"],
            "source_policy": "historical_exact_audit_only",
        })
    return rows


def _direct_distance_score(
    config: dict,
    candidates: list[dict],
    *,
    w0_m: float,
    receiver_diameter_m: float,
    distance_km: float,
) -> tuple[float, dict]:
    channel_row, _ = _channel_row(
        config,
        w0_m=w0_m,
        receiver_diameter_m=receiver_diameter_m,
        distance_km=distance_km,
    )
    best = None
    for candidate in candidates:
        evaluated = evaluate(
            candidate,
            config,
            float(channel_row["T_eff"]),
            EPSILON,
            compare_full_interval=False,
        )
        row = {**channel_row, **evaluated}
        if best is None or float(row["SKR_direct"]) > float(best["SKR_direct"]):
            best = row
    if best is None:
        raise RuntimeError("No exact Uniform candidate was available for distance scoring.")
    return float(best["SKR_direct"]), best


def _distance_crossing(
    config: dict,
    candidates: list[dict],
    *,
    w0_m: float,
    receiver_diameter_m: float,
    low_km: float = 19.0,
    high_km: float = 50.0,
) -> dict:
    low_score, low_best = _direct_distance_score(
        config,
        candidates,
        w0_m=w0_m,
        receiver_diameter_m=receiver_diameter_m,
        distance_km=low_km,
    )
    high_score, high_best = _direct_distance_score(
        config,
        candidates,
        w0_m=w0_m,
        receiver_diameter_m=receiver_diameter_m,
        distance_km=high_km,
    )
    if not (low_score > 0.0 and high_score <= 0.0):
        return {
            "status": "NO_POSITIVE_TO_NONPOSITIVE_BRACKET",
            "w0_m": w0_m,
            "receiver_diameter_m": receiver_diameter_m,
            "low_km": low_km,
            "high_km": high_km,
            "K_low": low_score,
            "K_high": high_score,
            "operation_distance_estimate_km": None,
            "V_A_low": low_best["V_A"],
            "V_A_high": high_best["V_A"],
        }
    for _ in range(32):
        midpoint = 0.5 * (low_km + high_km)
        midpoint_score, midpoint_best = _direct_distance_score(
            config,
            candidates,
            w0_m=w0_m,
            receiver_diameter_m=receiver_diameter_m,
            distance_km=midpoint,
        )
        if midpoint_score > 0.0:
            low_km, low_score, low_best = midpoint, midpoint_score, midpoint_best
        else:
            high_km, high_score, high_best = midpoint, midpoint_score, midpoint_best
    return {
        "status": "SPARSE_EXACT_CANDIDATE_DISTANCE_BISECTION",
        "w0_m": w0_m,
        "receiver_diameter_m": receiver_diameter_m,
        "low_km": low_km,
        "high_km": high_km,
        "K_low": low_score,
        "K_high": high_score,
        "operation_distance_estimate_km": 0.5 * (low_km + high_km),
        "V_A_low": low_best["V_A"],
        "V_A_high": high_best["V_A"],
    }


def _plot_sweep(rows: list[dict]) -> None:
    x = np.asarray([float(row["w0_mm"]) for row in rows])
    metrics = (
        ("loss_dB", "Total channel loss (dB)", "beam_waist_loss_dB"),
        ("T_eff", r"$T_{\mathrm{eff}}$", "beam_waist_T_eff"),
        ("SKR_max_best_tested_direct", "Best-tested Uniform SKR (bits/use)", "beam_waist_skr"),
        ("V_A_opt_best_tested_direct", r"Best-tested $V_A$ (SNU)", "beam_waist_va"),
    )
    for key, ylabel, stem in metrics:
        figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
        axis.plot(x, [float(row[key]) for row in rows], marker="o", color="#2563eb", linewidth=1.6)
        if key == "SKR_max_best_tested_direct":
            axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
        axis.set_xlabel(r"$w_0$ (mm)")
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.3)
        axis.set_xscale("log")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        figure.tight_layout()
        figure.savefig(OUTPUT / f"{stem}.png", dpi=300, facecolor="white")
        figure.savefig(OUTPUT / f"{stem}.pdf", facecolor="white")
        plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    axis.plot(x, [float(row["beta_I_AB_best_tested_direct"]) for row in rows], label=r"$\beta I_{AB}$", color="#2563eb")
    axis.plot(x, [float(row["chi_BE_best_tested_direct"]) for row in rows], label=r"$\chi_{BE}$", color="#dc2626")
    axis.set_xscale("log")
    axis.set_xlabel(r"$w_0$ (mm)")
    axis.set_ylabel("bits/use")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUTPUT / "beam_waist_security_terms.png", dpi=300, facecolor="white")
    figure.savefig(OUTPUT / "beam_waist_security_terms.pdf", facecolor="white")
    plt.close(figure)


def _plot_distance(rows: list[dict]) -> None:
    figure, axis = plt.subplots(figsize=(8.2, 5.2), dpi=160)
    for label in sorted({row["w0_label"] for row in rows}):
        series = [row for row in rows if row["w0_label"] == label]
        axis.plot([row["distance_km"] for row in series], [row["SKR"] for row in series], marker="o", label=label)
    axis.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    axis.set_xlabel("HAP-UAV link distance (km)")
    axis.set_ylabel("Best-tested Uniform SKR (bits/use)")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUTPUT / "beam_waist_distance_skr.png", dpi=300, facecolor="white")
    figure.savefig(OUTPUT / "beam_waist_distance_skr.pdf", facecolor="white")
    plt.close(figure)


def _plot_heatmap(rows: list[dict]) -> None:
    w0_values = list(HEATMAP_W0)
    diameter_values = list(HEATMAP_DIAMETERS)
    values = np.asarray([
        [float(next(row["SKR_max_best_tested_direct"] for row in rows if row["w0_m"] == w0 and row["receiver_diameter_m"] == diameter)) for w0 in w0_values]
        for diameter in diameter_values
    ])
    figure, axis = plt.subplots(figsize=(8.4, 5.8), dpi=160)
    mesh = axis.pcolormesh(
        np.asarray(w0_values) * 1000.0,
        diameter_values,
        values,
        shading="nearest",
        cmap="RdYlGn",
    )
    if np.nanmin(values) <= 0.0 <= np.nanmax(values):
        contour = axis.contour(np.asarray(w0_values) * 1000.0, diameter_values, values, levels=[0.0], colors="#111827", linewidths=1.2)
        axis.clabel(contour, fmt={0.0: "K=0"}, inline=True, fontsize=8)
    axis.set_xlabel(r"$w_0$ (mm)")
    axis.set_ylabel("Receiver diameter D_r (m)")
    axis.set_xscale("log")
    axis.set_title("Best-tested exact Uniform SKR: beam waist / receiver aperture")
    figure.colorbar(mesh, ax=axis, label="SKR (bits/use)")
    figure.tight_layout()
    figure.savefig(OUTPUT / "beam_waist_receiver_heatmap.png", dpi=300, facecolor="white")
    figure.savefig(OUTPUT / "beam_waist_receiver_heatmap.pdf", facecolor="white")
    plt.close(figure)


def main() -> int:
    global OUTPUT, TAU_ZEN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-zen", type=float, default=TAU_ZEN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    OUTPUT = args.output_dir.resolve()
    TAU_ZEN = float(args.tau_zen)
    if not 0.0 < TAU_ZEN <= 1.0:
        raise ValueError("tau-zen must lie in (0,1].")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    uniform = [candidate for candidate in candidates if candidate["family"] == "Uniform"]
    if not uniform:
        raise RuntimeError("No current-compatible historical exact Uniform candidates found.")

    log_grid = np.geomspace(min(REQUESTED_W0), max(REQUESTED_W0), 61).tolist()
    sweep_rows, detail_rows = _evaluate_w0_grid(
        config,
        uniform,
        [BASELINE_W0, *REQUESTED_W0, *log_grid],
        0.08,
    )
    refined_rows = _refine_crossings(config, uniform, sweep_rows, 0.08)
    all_rows = sweep_rows + refined_rows
    all_rows = sorted({float(row["w0_m"]): row for row in all_rows}.values(), key=lambda row: float(row["w0_m"]))

    positive = [row for row in all_rows if float(row["SKR_max_best_tested_direct"]) > 0.0]
    selected = min(positive, key=lambda row: float(row["w0_m"])) if positive else None
    wavelength_m = float(config["channel"]["wavelength_m"])
    selected_w0 = None if selected is None else float(selected["w0_m"])
    comparison_w0 = _unique_sorted([BASELINE_W0, 0.10, 0.12, 0.15] + ([] if selected_w0 is None else [selected_w0]))
    comparison = []
    for w0_m in comparison_w0:
        channel_row, _ = _channel_row(config, w0_m=w0_m, receiver_diameter_m=0.08)
        comparison.append({
            **channel_row,
            "label": "current_baseline" if abs(w0_m - BASELINE_W0) < 1e-12 else f"w0={1000.0*w0_m:g}mm",
            "D_t_for_2w0_m": 2.0 * w0_m,
            "D_t_for_2p5w0_m": 2.5 * w0_m,
            "D_t_for_3w0_m": 3.0 * w0_m,
            "classification_at_2p5w0": _classification(2.5 * w0_m),
            "theta_reference_lambda_over_0p3m_rad": wavelength_m / 0.3,
            "theta_full_to_reference_ratio": channel_row["theta_div_full_angle_rad"] / (wavelength_m / 0.3),
        })

    heatmap = []
    for diameter in HEATMAP_DIAMETERS:
        rows, _ = _evaluate_w0_grid(config, uniform, list(HEATMAP_W0), diameter)
        heatmap.extend(rows)

    receiver_thresholds = [
        _receiver_threshold(config, uniform, w0_m)
        for w0_m in HEATMAP_W0
    ]
    positive_heatmap = [
        row for row in heatmap
        if float(row["SKR_max_best_tested_direct"]) > 0.0
    ]
    coarse_positive = (
        min(positive_heatmap, key=lambda row: (float(row["receiver_diameter_m"]), float(row["w0_m"])))
        if positive_heatmap else None
    )

    distance_rows = _distance_rows(
        config,
        uniform,
        BASELINE_W0,
        "current w0=4.425 mm, Dr=0.08 m",
    )
    if selected_w0 is not None:
        distance_rows.extend(_distance_rows(
            config,
            uniform,
            selected_w0,
            f"selected sparse-exact w0={1000.0*selected_w0:.4g} mm, Dr=0.08 m",
        ))
    if coarse_positive is not None:
        distance_rows.extend(_distance_rows(
            config,
            uniform,
            float(coarse_positive["w0_m"]),
            f"coarse-positive w0={1000.0*float(coarse_positive['w0_m']):.4g} mm, Dr={float(coarse_positive['receiver_diameter_m']):g} m",
            receiver_diameter_m=float(coarse_positive["receiver_diameter_m"]),
        ))
    distance_crossing = None if coarse_positive is None else _distance_crossing(
        config,
        uniform,
        w0_m=float(coarse_positive["w0_m"]),
        receiver_diameter_m=float(coarse_positive["receiver_diameter_m"]),
    )

    crossing_rows = []
    for left, right in zip(all_rows, all_rows[1:]):
        if float(left["SKR_max_best_tested_direct"]) <= 0.0 < float(right["SKR_max_best_tested_direct"]):
            crossing_rows.append({
                "left_w0_m": left["w0_m"],
                "right_w0_m": right["w0_m"],
                "left_SKR": left["SKR_max_best_tested_direct"],
                "right_SKR": right["SKR_max_best_tested_direct"],
                "status": "SPARSE_EXACT_CANDIDATE_BRACKET",
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "beam_waist_sweep.csv", all_rows)
    write_csv(OUTPUT / "beam_waist_candidate_details.csv", detail_rows)
    write_csv(OUTPUT / "beam_waist_crossing.csv", crossing_rows)
    write_csv(OUTPUT / "beam_waist_transmitter_scale.csv", comparison)
    write_csv(OUTPUT / "beam_waist_receiver_heatmap.csv", heatmap)
    write_csv(OUTPUT / "beam_waist_receiver_thresholds.csv", receiver_thresholds)
    write_csv(OUTPUT / "beam_waist_distance_skr.csv", distance_rows)
    if distance_crossing is not None:
        write_csv(OUTPUT / "beam_waist_distance_crossing.csv", [distance_crossing])
    _plot_sweep(all_rows)
    _plot_heatmap(heatmap)
    _plot_distance(distance_rows)

    baseline = next(row for row in all_rows if abs(float(row["w0_m"]) - BASELINE_W0) < 1e-12)
    report = {
        "status": "BEAM_WAIST_DIAGNOSTIC_COMPLETE_CACHE_ONLY",
        "source_policy": "historical_exact_uniform_cw_only",
        "new_source_moments_computed": False,
        "interpolation_used_for_cw": False,
        "security_formula_changed": False,
        "primary_fixture": {
            "tau_zen": TAU_ZEN,
            "zenith_deg": ZENITH_DEG,
            "receiver_diameter_m": 0.08,
            "epsilon_ch_snu": EPSILON,
            "beta": BETA,
            "AO": "OFF",
            "phase_noise": "OFF",
        },
        "uniform_exact_candidate_count": len(uniform),
        "uniform_exact_V_A": sorted(float(candidate["V_A"]) for candidate in uniform),
        "skipped_historical_rows": len(skipped),
        "baseline_current_w0": baseline,
        "sparse_exact_candidate_positive_threshold": selected,
        "continuous_uniform_w0_critical": "UNRESOLVED_MISSING_EXACT_CW_OVER_V_A_DOMAIN",
        "selected_w0_for_distance_diagnostic": selected_w0,
        "physical_classification_at_2p5w0": None if selected is None else _classification(2.5 * selected_w0),
        "coarse_positive_combination": coarse_positive,
        "receiver_thresholds": receiver_thresholds,
        "coarse_positive_distance_crossing": distance_crossing,
        "distance_scope": "best-tested exact Uniform candidate at each distance; not continuous V_A optimization",
        "required_V_A_domain_status": "CONFIG_FROZEN_DOMAIN_IS_0.1_TO_4.0; requested_0.01_to_5.0_not_authorized_or_covered",
        "reference_transmitter": {
            "D_t_m": 0.3,
            "theta_lambda_over_D_rad": wavelength_m / 0.3,
            "current_full_divergence_to_reference_ratio": baseline["theta_div_full_angle_rad"] / (wavelength_m / 0.3),
        },
        "artifact_paths": {
            "sweep": str(OUTPUT / "beam_waist_sweep.csv"),
            "heatmap": str(OUTPUT / "beam_waist_receiver_heatmap.png"),
            "distance": str(OUTPUT / "beam_waist_distance_skr.csv"),
            "distance_crossing": str(OUTPUT / "beam_waist_distance_crossing.csv") if distance_crossing is not None else None,
        },
        "limitations": [
            "Only eight hash-matched historical Uniform C,w rows are available.",
            "No continuous V_A optimum or exact w0 critical point is claimed.",
            "Existing distance/forensic security path uses direct Z_minus; full-interval values are recorded as a comparison diagnostic.",
            "This is not baseline selection, certification, training, final-test, or publication-scale evaluation.",
        ],
    }
    (OUTPUT / "beam_waist_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
