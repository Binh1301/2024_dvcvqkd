"""Historical-C,w-only SKR-versus-distance diagnostic.

This runner intentionally has no source-moment generation path.  It loads only
current-compatible audit rows, reconstructs the lightweight ensemble/hash, and
evaluates downstream MI/Holevo/SKR for the distance/channel sweep.
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
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.run_exact_mb_test2 import build_mb_ensemble, ensemble_hash
from scripts.run_skr_vs_link_distance import _channel_moments, _grid
from src.channel.phase_noise import phase_distortion_variance, phase_noise_coefficient
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information
from src.modulation.joint_ps_gs import reference_ensemble


OUTPUT = ROOT / "results" / "skr_vs_link_distance"
AUDIT = OUTPUT / "historical_source_moment_audit.csv"
DEFAULT_TAU_ZEN = 0.92
DEFAULT_CN2_PHASE = 1.0e-16
DEFAULT_ETA_AO = 0.95
DEFAULT_START_KM = 19.0
DEFAULT_STOP_KM = 100.0
DEFAULT_DISTANCE_STEP_KM = 2.0
GH_ORDER = 8
CURVE_NAMES = ("Uniform", "MB with AO", "MB without AO")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def candidate_key(nu: float, va: float) -> tuple[float, float]:
    return round(float(nu), 14), round(float(va), 14)


def load_candidates(config: dict) -> tuple[list[dict], list[dict]]:
    rows = read_csv(AUDIT)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        if row.get("source_semantics_status") != "SOURCE_SEMANTICS_EXACT_MATCH":
            continue
        family = row.get("shaping_family")
        if family not in {"Uniform", "MB"}:
            continue
        if not row.get("V_A") or not row.get("original_ensemble_hash"):
            continue
        nu = 0.0 if family == "Uniform" else float(row["shaping_parameter_raw"])
        if family == "MB" and not 0.05 <= nu <= 0.20:
            continue
        va = float(row["V_A"])
        # Keep the exact decimal-to-binary64 value used by the historical hash;
        # decimal rounding here would create a different ensemble hash.
        grouped.setdefault((family, float(nu).hex(), float(va).hex()), []).append(row)

    candidates = []
    skipped = []
    for (family, _nu_hex, _va_hex), records in sorted(grouped.items(), key=lambda item: (item[0][0], float.fromhex(item[0][1]), float.fromhex(item[0][2]))):
        nu = float(records[0]["shaping_parameter_raw"])
        va = float(records[0]["V_A"])
        c_values = [float(row["C"]) for row in records]
        w_values = [float(row["w"]) for row in records]
        original_hashes = {row["original_ensemble_hash"] for row in records}
        if len(original_hashes) != 1 or max(c_values) != min(c_values) or max(w_values) != min(w_values):
            skipped.append({"family": family, "nu_raw": nu, "V_A": va, "reason": "historical duplicate C,w/hash disagreement"})
            continue
        if family == "MB":
            ensemble = build_mb_ensemble(config, nu, va)
        else:
            cvqkd = config["cvqkd"]
            ensemble = reference_ensemble(
                "uniform",
                batch_size=1,
                modulation_variance=va,
                v_min=float(cvqkd["v_min_snu"]),
                v_max=float(cvqkd["v_max_snu"]),
                n_peak_photons=float(cvqkd["n_peak_photons"]),
            )
        reconstructed = ensemble_hash(ensemble)
        if reconstructed != next(iter(original_hashes)):
            skipped.append({"family": family, "nu_raw": nu, "V_A": va, "reason": "current ensemble hash mismatch"})
            continue
        candidates.append({
            "family": family,
            "nu_raw": nu,
            "nu_repo": None if family == "Uniform" else 42.5 * nu,
            "V_A": va,
            "C": c_values[0],
            "w": w_values[0],
            "ensemble_hash": reconstructed,
            "ensemble": ensemble,
            "historical_record_count": len(records),
        })
    return candidates, skipped


def evaluate_candidate(candidate: dict, channel: dict, config: dict, *, ao: bool, cn2_phase: float, eta_ao: float) -> dict:
    va = float(candidate["V_A"])
    link_length_m = float(channel["link_distance_m"])
    tau_raw = phase_distortion_variance(cn2_phase, float(config["channel"]["wavelength_m"]), link_length_m)
    tau_phase = (1.0 - eta_ao) * tau_raw if ao else tau_raw
    c_phi = phase_noise_coefficient(tau_phase)
    epsilon_total = float(config["channel"]["excess_noise_distribution"]["epsilon_ch_snu"]) + c_phi * va
    transmittance = torch.tensor([float(channel["T_eff"])], dtype=torch.float64)
    epsilon = torch.tensor([epsilon_total], dtype=torch.float64)
    mi = deterministic_mutual_information(
        candidate["ensemble"], transmittance, epsilon,
        quadrature_order=GH_ORDER, implementation="product",
    )
    numerical = holevo_numerical_kwargs(config)
    holevo = _holevo_from_source_moments(
        candidate["ensemble"], transmittance, epsilon,
        coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
        w_raw=torch.tensor([candidate["w"]], dtype=torch.float64),
        tau=None,
        tau_trace=candidate["ensemble"].probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False,
        diagnostics={"backend": "historical_cw_distance_reuse", "ensemble_hash": candidate["ensemble_hash"]},
    )
    beta = float(config["cvqkd"]["beta_reconciliation"])
    return {
        "distance_km": float(channel["distance_km"]),
        "zeta_deg": float(channel["zeta_deg"]),
        "curve": "MB with AO" if ao and candidate["family"] == "MB" else "MB without AO" if not ao and candidate["family"] == "MB" else "Uniform",
        "shaping_family": candidate["family"],
        "nu_raw": candidate["nu_raw"],
        "nu_repo": candidate["nu_repo"],
        "V_A": va,
        "C": candidate["C"],
        "w": candidate["w"],
        "ensemble_hash": candidate["ensemble_hash"],
        "T_mean": float(channel["T_mean"]),
        "sqrtT_mean": float(channel["sqrtT_mean"]),
        "T_eff": float(channel["T_eff"]),
        "epsilon_total": epsilon_total,
        "c_phi": c_phi,
        "I_AB": float(mi[0]),
        "Z_star": float(holevo.z[0]),
        "chi_BE": float(holevo.chi_be[0]),
        "SKR": beta * float(mi[0]) - float(holevo.chi_be[0]),
        "source_policy": "historical_exact_audit_only",
        "source_record_count": candidate["historical_record_count"],
        "status": "PASS",
    }


def envelope(rows: list[dict], curve: str) -> list[dict]:
    result = []
    for distance in sorted({float(row["distance_km"]) for row in rows}):
        group = [row for row in rows if float(row["distance_km"]) == distance]
        winner = max(group, key=lambda row: float(row["SKR"]))
        result.append({"curve": curve, **winner})
    return result


def crossing(rows: list[dict], curve: str) -> dict:
    ordered = sorted(rows, key=lambda row: float(row["distance_km"]))
    for left, right in zip(ordered, ordered[1:]):
        k_left = float(left["SKR"])
        k_right = float(right["SKR"])
        if k_left > 0.0 and k_right <= 0.0:
            l_left = float(left["distance_km"])
            l_right = float(right["distance_km"])
            estimate = l_left + (0.0 - k_left) * (l_right - l_left) / (k_right - k_left)
            return {
                "curve": curve,
                "status": "HISTORICAL_EXACT_OPERATION_DISTANCE_ESTIMATE",
                "bracket_left_km": l_left,
                "bracket_right_km": l_right,
                "K_left": k_left,
                "K_right": k_right,
                "operation_distance_estimate_km": estimate,
                "winner_left_nu_raw": left.get("nu_raw"),
                "winner_left_V_A": left.get("V_A"),
                "winner_right_nu_raw": right.get("nu_raw"),
                "winner_right_V_A": right.get("V_A"),
            }
    return {"curve": curve, "status": "NO_SIGN_CHANGE_IN_GRID", "operation_distance_estimate_km": None}


def plot(path: Path, envelopes: dict[str, list[dict]], summaries: list[dict]) -> None:
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
    ax.set_title("Historical exact C,w diagnostic: SKR vs link distance", weight="bold")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="both", color="#cbd5e1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=True)
    figure.text(0.5, 0.018, "Historical exact C,w reuse only; no new source moments, no interpolation.", ha="center", va="bottom", fontsize=8.5, color="#475569")
    figure.subplots_adjust(left=0.10, right=0.96, bottom=0.14, top=0.90)
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-km", type=float, default=19.0)
    parser.add_argument("--stop-km", type=float, default=100.0)
    parser.add_argument("--distance-step-km", type=float, default=2.0)
    parser.add_argument("--tau-zen", type=float, default=0.92)
    parser.add_argument("--cn2-phase", type=float, default=1.0e-16)
    parser.add_argument("--eta-ao", type=float, default=0.95)
    args = parser.parse_args()
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    candidates, skipped = load_candidates(config)
    uniform = [row for row in candidates if row["family"] == "Uniform"]
    mb = [row for row in candidates if row["family"] == "MB"]
    if not uniform or not mb:
        raise RuntimeError("Historical exact candidate audit did not provide Uniform and MB rows.")
    distances = tuple(sorted(set(_grid(args.start_km, args.stop_km, args.distance_step_km) + (21.939310229205777,))))
    rows_by_curve = {curve: [] for curve in CURVE_NAMES}
    for distance in distances:
        channel = _channel_moments(config, distance_km=distance, tau_zen=args.tau_zen, sample_count=0, seed=0)
        for candidate in uniform:
            rows_by_curve["Uniform"].append(evaluate_candidate(candidate, channel, config, ao=True, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao))
        for candidate in mb:
            rows_by_curve["MB with AO"].append(evaluate_candidate(candidate, channel, config, ao=True, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao))
            rows_by_curve["MB without AO"].append(evaluate_candidate(candidate, channel, config, ao=False, cn2_phase=args.cn2_phase, eta_ao=args.eta_ao))

    envelopes = {curve: envelope(rows, curve) for curve, rows in rows_by_curve.items()}
    summaries = [crossing(envelopes[curve], curve) for curve in CURVE_NAMES]
    source_labels = {
        "Uniform": f"historical exact Uniform V_A set ({len(uniform)} pairs)",
        "MB with AO": f"historical exact MB nu_raw 0.05-0.20 ({len(mb)} pairs)",
        "MB without AO": f"historical exact MB nu_raw 0.05-0.20 ({len(mb)} pairs)",
    }
    for summary in summaries:
        summary["source_candidate_set"] = source_labels[summary["curve"]]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "historical_exact_uniform_envelope.csv", envelopes["Uniform"])
    write_csv(OUTPUT / "historical_exact_mb_ao_envelope.csv", envelopes["MB with AO"])
    write_csv(OUTPUT / "historical_exact_mb_noao_envelope.csv", envelopes["MB without AO"])
    write_csv(OUTPUT / "historical_exact_operation_distance_summary.csv", summaries)
    plot(OUTPUT / "historical_exact_distance_plot", envelopes, summaries)
    report = {
        "status": "HISTORICAL_EXACT_DISTANCE_DIAGNOSTIC_COMPLETE",
        "new_source_moments_computed": False,
        "source_policy": "historical_source_moment_audit_only",
        "channel": {"tau_zen": args.tau_zen, "cn2_phase": args.cn2_phase, "eta_ao": args.eta_ao, "maximize_full_interval": False, "T_convention": "<sqrt(T_raw)>^2"},
        "distance_grid_km": list(distances),
        "candidate_counts": {"uniform": len(uniform), "mb_raw_0p05_to_0p20": len(mb), "skipped_hash_or_duplicate_rows": len(skipped)},
        "curves": CURVE_NAMES,
        "operation_distance_summary": summaries,
        "missing_before_final_figure": [
            "Uniform V_A search remains sparse and not globally optimized.",
            "PCS is represented by historical MB candidates only.",
            "Binomial has no safe current-compatible exact C,w match.",
        ],
    }
    (OUTPUT / "historical_exact_distance_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
