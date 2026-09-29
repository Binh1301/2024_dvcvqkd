"""Read-only HAP-UAV/Sayat link and exact-cache SKR forensic diagnostic.

No source moments are built.  Every Uniform/MB security evaluation uses an
existing hash-matched historical C,w pair at its stored (nu_raw, V_A).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfinv
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    closed_form_channel_moments,
    derive_physical_inputs,
)
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates
from scripts.run_skr_vs_link_distance import _channel_moments
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information


OUTPUT = ROOT / "results" / "hap_uav_sayat_forensics"
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
BASELINE_DISTANCE_KM = 21.939310229205777
SAYAT_URL = "https://arxiv.org/html/2211.16862v3"


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(candidate: dict, config: dict, transmittance: float, epsilon: float, *, compare_full_interval: bool = False) -> dict:
    t = torch.tensor([transmittance], dtype=torch.float64)
    e = torch.tensor([epsilon], dtype=torch.float64)
    mi = float(deterministic_mutual_information(
        candidate["ensemble"], t, e, quadrature_order=8, implementation="product"
    )[0])
    numerical = holevo_numerical_kwargs(config)
    values = {}
    for full_interval in ((False, True) if compare_full_interval else (False,)):
        result = _holevo_from_source_moments(
            candidate["ensemble"],
            t,
            e,
            coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
            w_raw=torch.tensor([candidate["w"]], dtype=torch.float64),
            tau=None,
            tau_trace=candidate["ensemble"].probabilities.sum(dim=-1),
            require_supported_symmetry=True,
            symmetry_tolerance=numerical["symmetry_tolerance"],
            physicality_tolerance=numerical["physicality_tolerance"],
            maximize_full_interval=full_interval,
            diagnostics={"backend": "forensic_existing_historical_cw"},
        )
        name = "full_interval" if full_interval else "direct"
        values[f"Z_{name}"] = float(result.z[0])
        values[f"chi_BE_{name}"] = float(result.chi_be[0])
        values[f"SKR_{name}"] = BETA * mi - float(result.chi_be[0])
    return {
        "family": candidate["family"],
        "nu_raw": candidate["nu_raw"],
        "V_A": candidate["V_A"],
        "C": candidate["C"],
        "w": candidate["w"],
        "ensemble_hash": candidate["ensemble_hash"],
        "T_eff": transmittance,
        "epsilon": epsilon,
        "I_AB": mi,
        "beta_I_AB": BETA * mi,
        **values,
    }


def exact_envelope(candidates: list[dict], config: dict, transmittance: float, epsilon: float, *, compare_full_interval: bool = False) -> tuple[dict, list[dict]]:
    rows = [evaluate(candidate, config, transmittance, epsilon, compare_full_interval=compare_full_interval) for candidate in candidates]
    return max(rows, key=lambda row: row["SKR_direct"]), rows


def threshold_transmittance(candidates: list[dict], config: dict, current_t: float) -> dict:
    current, _ = exact_envelope(candidates, config, current_t, EPSILON)
    grid = np.geomspace(current_t, 1.0, 28)
    previous_t, previous_k = current_t, current["SKR_direct"]
    bracket = None
    for value in grid[1:]:
        best, _ = exact_envelope(candidates, config, float(value), EPSILON)
        if previous_k <= 0.0 < best["SKR_direct"]:
            bracket = [previous_t, float(value)]
            break
        previous_t, previous_k = float(value), best["SKR_direct"]
    if bracket is None:
        return {"status": "NO_POSITIVE_THRESHOLD_UP_TO_T_1", "T_eff_threshold": None}
    low, high = bracket
    best = None
    for _ in range(28):
        midpoint = 0.5 * (low + high)
        best, _ = exact_envelope(candidates, config, midpoint, EPSILON)
        if best["SKR_direct"] > 0.0:
            high = midpoint
        else:
            low = midpoint
    best, _ = exact_envelope(candidates, config, high, EPSILON)
    return {
        "status": "SPARSE_EXACT_CANDIDATE_THRESHOLD",
        "T_eff_threshold": high,
        "loss_threshold_dB": -10.0 * math.log10(high),
        "bracket": bracket,
        "winner_V_A": best["V_A"],
        "winner_SKR": best["SKR_direct"],
    }


def threshold_epsilon(candidates: list[dict], config: dict, transmittance: float) -> dict:
    zero, _ = exact_envelope(candidates, config, transmittance, 0.0)
    baseline, _ = exact_envelope(candidates, config, transmittance, EPSILON)
    if zero["SKR_direct"] <= 0.0:
        return {"status": "NO_NONNEGATIVE_EPSILON_RESCUES_TESTED_UNIFORM", "epsilon_threshold": None}
    if baseline["SKR_direct"] > 0.0:
        return {"status": "POSITIVE_AT_BASELINE_EPSILON", "epsilon_threshold": EPSILON}
    low, high = 0.0, EPSILON
    best = zero
    for _ in range(28):
        midpoint = 0.5 * (low + high)
        candidate, _ = exact_envelope(candidates, config, transmittance, midpoint)
        if candidate["SKR_direct"] > 0.0:
            low = midpoint
            best = candidate
        else:
            high = midpoint
    return {
        "status": "SPARSE_EXACT_CANDIDATE_EPSILON_THRESHOLD",
        "epsilon_threshold": low,
        "winner_V_A": best["V_A"],
        "winner_SKR": best["SKR_direct"],
    }


def current_link_budget(physical: dict, moments: dict) -> list[dict]:
    chi = moments["chi"]
    factors = [
        ("Atmospheric transmittance", moments["eta_atm"]),
        ("Finite-aperture / beam coupling A0", moments["A0"]),
        ("Pointing-jitter moment", (chi**2 / (chi**2 + 0.5)) ** 2),
        ("Scintillation sqrt-moment", math.exp(-moments["sigma_X2"])),
        ("AoA/FOV active probability moment", moments["p_in"] ** 2),
    ]
    rows = [{"component": name, "factor": value, "loss_dB": -10.0 * math.log10(value)} for name, value in factors]
    rows.append({
        "component": "TOTAL T_eff",
        "factor": moments["T_eff"],
        "loss_dB": -10.0 * math.log10(moments["T_eff"]),
    })
    rows.append({
        "component": "Mean raw transmittance",
        "factor": moments["mean_T_raw"],
        "loss_dB": -10.0 * math.log10(moments["mean_T_raw"]),
    })
    return rows


def sayat_scintillation_loss(receiver_diameter_m: float) -> tuple[float, float, float]:
    wavelength = 1.55e-6
    atmosphere_m = 20_000.0
    k = 2.0 * math.pi / wavelength
    sigma_r2 = 2.25 * k ** (7.0 / 6.0) * 1.0e-16 * (6.0 / 11.0) * atmosphere_m ** (11.0 / 6.0)
    d = receiver_diameter_m * math.sqrt(math.pi / (2.0 * wavelength * atmosphere_m))
    sigma_i2 = math.exp(
        0.20 * sigma_r2 / (1.0 + 0.18 * d**2 + 0.20 * sigma_r2 ** (6.0 / 5.0)) ** (7.0 / 6.0)
        + 0.21 * sigma_r2 * (1.0 + 0.24 * sigma_r2 ** (6.0 / 5.0)) ** (-5.0 / 6.0)
        / (1.0 + 0.90 * d**2 + 0.21 * d**2 * sigma_r2 ** (6.0 / 5.0))
    ) - 1.0
    signed_equation = 4.343 * (
        float(erfinv(2.0e-6 - 1.0)) * math.sqrt(2.0 * math.log1p(sigma_i2))
        - 0.5 * math.log1p(sigma_i2)
    )
    return sigma_r2, sigma_i2, -signed_equation


def sayat_link_budget() -> list[dict]:
    wavelength = 1.55e-6
    transmitter_diameter = 0.3
    optics_pointing = 0.9 * 0.9 * (1.0 - 0.1)
    visibility_km = 200.0
    scattering_per_km = 10.0 * math.log10(math.e) * (3.912 / visibility_km) * (1550.0 / 550.0) ** (-1.6)
    rows = []
    for receiver_diameter in (1.0, 2.0):
        sigma_r2, sigma_i2, scintillation_loss = sayat_scintillation_loss(receiver_diameter)
        far_field_km = receiver_diameter * transmitter_diameter / wavelength / 1000.0
        for distance_km in (200.0, 300.0, 500.0, 1000.0):
            geometric = 10.0 * math.log10(
                (distance_km * 1000.0) ** 2 * wavelength**2
                / (transmitter_diameter**2 * receiver_diameter**2 * optics_pointing)
            )
            scattering = scattering_per_km * 20.0
            total = geometric + scattering + scintillation_loss
            valid = distance_km >= far_field_km and total >= 0.0
            rows.append({
                "distance_km": distance_km,
                "receiver_diameter_m": receiver_diameter,
                "far_field_minimum_km": far_field_km,
                "far_field_valid": valid,
                "geometric_loss_dB": geometric,
                "scattering_loss_dB": scattering,
                "scintillation_margin_dB": scintillation_loss,
                "sigma_R2": sigma_r2,
                "sigma_I2": sigma_i2,
                "total_loss_dB": total if valid else None,
                "transmittance": 10.0 ** (-total / 10.0) if valid else None,
            })
    return rows


def aperture_rows(config: dict, candidates: list[dict]) -> tuple[list[dict], dict | None]:
    rows = []
    for diameter in (0.08, 0.10, 0.20, 0.30, 0.50, 1.00, 1.50, 2.00):
        physical = derive_physical_inputs(
            TAU_ZEN,
            zenith_angle_rad_override=math.radians(30.0),
            aperture_radius_m_override=diameter / 2.0,
        )
        moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
        best, _ = exact_envelope(candidates, config, moments["T_eff"], EPSILON)
        rows.append({
            "receiver_diameter_m": diameter,
            "T_eff": moments["T_eff"],
            "loss_dB": -10.0 * math.log10(moments["T_eff"]),
            "best_V_A": best["V_A"],
            "beta_I_AB": best["beta_I_AB"],
            "chi_BE": best["chi_BE_direct"],
            "SKR": best["SKR_direct"],
        })
    crossing = None
    for left, right in zip(rows, rows[1:]):
        if left["SKR"] <= 0.0 < right["SKR"]:
            low, high = left["receiver_diameter_m"], right["receiver_diameter_m"]
            for _ in range(24):
                midpoint = 0.5 * (low + high)
                physical = derive_physical_inputs(
                    TAU_ZEN,
                    zenith_angle_rad_override=math.radians(30.0),
                    aperture_radius_m_override=midpoint / 2.0,
                )
                moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
                best, _ = exact_envelope(candidates, config, moments["T_eff"], EPSILON)
                if best["SKR_direct"] > 0.0:
                    high = midpoint
                else:
                    low = midpoint
            physical = derive_physical_inputs(TAU_ZEN, zenith_angle_rad_override=math.radians(30.0), aperture_radius_m_override=high / 2.0)
            moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
            best, _ = exact_envelope(candidates, config, moments["T_eff"], EPSILON)
            crossing = {
                "status": "SPARSE_EXACT_CANDIDATE_APERTURE_THRESHOLD",
                "diameter_m": high,
                "T_eff": moments["T_eff"],
                "loss_dB": -10.0 * math.log10(moments["T_eff"]),
                "winner_V_A": best["V_A"],
            }
            break
    return rows, crossing


def distance_sweep(config: dict, uniform: list[dict], mb: list[dict]) -> tuple[list[dict], list[dict]]:
    rows = []
    summaries = []
    for distance in np.arange(19.0, 50.0 + 1.0e-9, 1.0):
        channel = _channel_moments(config, distance_km=float(distance), tau_zen=TAU_ZEN, sample_count=0, seed=0)
        for name, candidates in (("Uniform", uniform), ("MB historical exact", mb)):
            best, _ = exact_envelope(candidates, config, channel["T_eff"], EPSILON)
            rows.append({"curve": name, "distance_km": float(distance), **best})
    for name in ("Uniform", "MB historical exact"):
        curve = [row for row in rows if row["curve"] == name]
        summary = {"curve": name, "status": "NO_POSITIVE_TO_NONPOSITIVE_CROSSING"}
        for left, right in zip(curve, curve[1:]):
            if left["SKR_direct"] > 0.0 >= right["SKR_direct"]:
                estimate = left["distance_km"] + (-left["SKR_direct"]) * (right["distance_km"] - left["distance_km"]) / (right["SKR_direct"] - left["SKR_direct"])
                summary = {
                    "curve": name,
                    "status": "SPARSE_HISTORICAL_EXACT_LINEAR_ESTIMATE",
                    "left_km": left["distance_km"],
                    "right_km": right["distance_km"],
                    "operation_distance_estimate_km": estimate,
                }
                break
        summaries.append(summary)
    return rows, summaries


def plots(uniform_rows: list[dict], distance_rows: list[dict]) -> None:
    figure, ax = plt.subplots(figsize=(8.3, 5.2), dpi=160)
    ax.plot([row["V_A"] for row in uniform_rows], [row["SKR_direct"] for row in uniform_rows], marker="o", color="#475569")
    ax.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set(xlabel=r"$V_A$ (SNU)", ylabel="SKR (bits/use)", title="Uniform 256-QAM: available exact historical points")
    ax.grid(alpha=0.3)
    figure.tight_layout()
    figure.savefig(OUTPUT / "uniform_skr_vs_va_existing_exact.png", dpi=300)
    figure.savefig(OUTPUT / "uniform_skr_vs_va_existing_exact.pdf")
    plt.close(figure)

    figure, axes = plt.subplots(2, 1, figsize=(9.2, 7.6), sharex=True, dpi=160)
    colors = {"Uniform": "#64748b", "MB historical exact": "#2563eb"}
    for name in colors:
        rows = [row for row in distance_rows if row["curve"] == name]
        axes[0].plot([row["distance_km"] for row in rows], [row["SKR_direct"] for row in rows], label=name, color=colors[name])
        axes[1].plot([row["distance_km"] for row in rows], [row["beta_I_AB"] for row in rows], color=colors[name], label=f"{name}: beta I_AB")
        axes[1].plot([row["distance_km"] for row in rows], [row["chi_BE_direct"] for row in rows], color=colors[name], linestyle="--", label=f"{name}: chi_BE")
    axes[0].axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    axes[0].set_ylabel("SKR (bits/use)")
    axes[0].legend()
    axes[1].set_xlabel("Physical link distance (km)")
    axes[1].set_ylabel("Information (bits/use)")
    axes[1].legend(ncol=2, fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.3)
        axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    figure.suptitle("Phase-off, no-AO historical exact candidate envelopes")
    figure.tight_layout()
    figure.savefig(OUTPUT / "distance_skr_and_security_terms.png", dpi=300)
    figure.savefig(OUTPUT / "distance_skr_and_security_terms.pdf")
    plt.close(figure)


def main() -> int:
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    uniform = [candidate for candidate in candidates if candidate["family"] == "Uniform"]
    mb = [candidate for candidate in candidates if candidate["family"] == "MB"]
    physical = derive_physical_inputs(TAU_ZEN)
    moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
    uniform_best, uniform_rows = exact_envelope(
        uniform, config, moments["T_eff"], EPSILON, compare_full_interval=True
    )
    mb_best, mb_rows = exact_envelope(mb, config, moments["T_eff"], EPSILON)
    mb_budget = [candidate for candidate in mb if candidate["V_A"] <= float(config["cvqkd"]["v_a_budget_snu"])]
    mb_budget_best, _ = exact_envelope(mb_budget, config, moments["T_eff"], EPSILON)
    t_threshold = threshold_transmittance(uniform, config, moments["T_eff"])
    epsilon_zero_best, _ = exact_envelope(uniform, config, moments["T_eff"], 0.0)
    epsilon_threshold = threshold_epsilon(uniform, config, moments["T_eff"])
    aperture, aperture_threshold = aperture_rows(config, uniform)
    distances, distance_summary = distance_sweep(config, uniform, mb)
    current_budget = current_link_budget(physical, moments)
    sayat_budget = sayat_link_budget()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "uniform_existing_exact_phase_off.csv", uniform_rows)
    write_csv(OUTPUT / "mb_existing_exact_phase_off.csv", mb_rows)
    write_csv(OUTPUT / "current_hap_link_budget.csv", current_budget)
    write_csv(OUTPUT / "sayat_good_channel_budget.csv", sayat_budget)
    write_csv(OUTPUT / "uniform_aperture_counterfactual.csv", aperture)
    write_csv(OUTPUT / "distance_phase_off_existing_exact.csv", distances)
    write_csv(OUTPUT / "distance_operation_summary.csv", distance_summary)
    plots(uniform_rows, distances)

    detector_rows = []
    for eta in (0.7, 0.8, 0.9, 0.95):
        detector_rows.append({
            "eta_det": eta,
            "epsilon_det": 0.0135,
            "sayat_chi_het": (1.0 + (1.0 - eta) + 2.0 * 0.0135) / eta,
            "current_repo_evaluation": "NOT_IMPLEMENTED_IDEAL_HETERODYNE_ONLY",
        })
    write_csv(OUTPUT / "detector_convention_audit.csv", detector_rows)

    report = {
        "status": "FORENSIC_DIAGNOSTIC_COMPLETE_WITH_EXACT_CW_COVERAGE_LIMIT",
        "new_source_moments_computed": False,
        "primary_fixture": {
            "phase_noise": "OFF",
            "AO": "OFF / not used to rescue result",
            "tau_zen": TAU_ZEN,
            "epsilon": EPSILON,
            "beta": BETA,
            "T_eff": moments["T_eff"],
            "loss_dB": -10.0 * math.log10(moments["T_eff"]),
        },
        "coverage": {
            "uniform_exact_V_A": [candidate["V_A"] for candidate in uniform],
            "mb_exact_pair_count": len(mb),
            "skipped_candidate_count": len(skipped),
            "requested_uniform_0p01_to_5_exact_sweep": "NOT_RUN_MISSING_EXACT_CW_AND_OUTSIDE_FROZEN_VA_DOMAIN",
        },
        "uniform_best_tested": uniform_best,
        "uniform_any_positive_tested": any(row["SKR_direct"] > 0.0 for row in uniform_rows),
        "uniform_full_interval_equals_direct_at_tested_points": all(abs(row["SKR_direct"] - row["SKR_full_interval"]) <= 1.0e-15 for row in uniform_rows),
        "mb_best_tested": mb_best,
        "mb_best_tested_within_V_A_budget": mb_budget_best,
        "transmittance_threshold": t_threshold,
        "epsilon_zero_counterfactual": epsilon_zero_best,
        "epsilon_threshold": epsilon_threshold,
        "aperture_threshold": aperture_threshold,
        "distance_summary": distance_summary,
        "invalid_requested_distance_range": "5-18 km is shorter than the fixed 19 km HAP-UAV vertical separation",
        "convention_audit": {
            "T": "power transmittance; signal amplitude uses sqrt(T)",
            "effective_fading_T": "<sqrt(T_raw)>^2 in the current scalar experiment",
            "detector": "ideal heterodyne; eta_det and epsilon_det are absent",
            "epsilon": "input-referred channel excess noise in the current ideal-detector model",
            "V_A": "2*sum_i p_i*|alpha_i|^2",
            "same_ensemble": "enforced by reconstructed ensemble hash for historical C,w reuse",
            "beta": "multiplies I_AB only",
            "security_authority_conflict": "frozen spec requests full-Z interval; distance runner uses direct Z_minus; tested Uniform rows select the same lower endpoint numerically",
        },
        "sayat_reproduction": {
            "source": SAYAT_URL,
            "scope": "Eqs. 29-33 at zenith, good atmosphere, constant Cn2, positive scintillation fading margin",
            "warning": "Sayat M-QAM uses binomial/discrete-Gaussian PMFs, not Uniform 256-QAM",
        },
        "optics": {
            "current_receiver_diameter_m": physical["receiver_diameter_m"],
            "current_beam_radius_receiver_m": physical["pointing"]["beam_radius_receiver_m"],
            "current_beam_waist_m": physical["beam_waist_m"],
            "current_divergence_rad": physical["theta_div_rad"],
            "receiver_1m_area_gain_dB_small_aperture": 20.0 * math.log10(1.0 / physical["receiver_diameter_m"]),
            "receiver_2m_area_gain_dB_small_aperture": 20.0 * math.log10(2.0 / physical["receiver_diameter_m"]),
            "paper_diffraction_scale_rad_lambda_over_Dt": 1.55e-6 / 0.3,
            "current_to_paper_divergence_ratio_dB": 20.0 * math.log10(physical["theta_div_rad"] / (1.55e-6 / 0.3)),
        },
    }
    (OUTPUT / "forensic_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "uniform_best_tested": uniform_best,
        "mb_best_tested": mb_best,
        "mb_best_tested_within_V_A_budget": mb_budget_best,
        "T_threshold": t_threshold,
        "aperture_threshold": aperture_threshold,
        "epsilon_zero": epsilon_zero_best,
        "epsilon_threshold": epsilon_threshold,
        "distance_summary": distance_summary,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
