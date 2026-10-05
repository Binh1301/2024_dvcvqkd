"""Author-frozen redesigned-baseline adaptive exact MB/V_A search.

The runner reuses exact ensemble-bound C,w cache entries, evaluates every SKR
with the redesigned channel and direct Z_minus, and fails closed when exact
coverage cannot close all adaptive numerical boundaries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
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
from scripts.run_exact_mb_test2 import ExactMBEvaluator, _json_hash, build_mb_ensemble
from scripts.run_joint_mb_va_optimization import evaluate


FREEZE = ROOT / "configs" / "redesigned_baseline_global_mb_va.yaml"
BASE_CONFIG = ROOT / "configs" / "default.yaml"
SOURCE_CACHE = ROOT / "results" / "exact_mb_test2" / "exact_source_cache"
OUTPUT = ROOT / "results" / "redesigned_baseline_global_mb_va"
EXPECTED = {
    "omega_L_eq_m": 1.41806995,
    "A0": 0.998118728,
    "T_eff": 0.203227370,
    "loss_dB": 6.920178,
}
PRIORITY_NEW_POINTS = (
    # Uniform refinement and lower boundary.
    (0.0, 0.05), (0.0, 0.9), (0.0, 1.0), (0.0, 1.1),
    (0.0, 1.2), (0.0, 1.3), (0.0, 1.4), (0.0, 1.6),
    # Known MB basin refinement.
    (0.2, 1.0), (0.2, 1.2), (0.2, 1.4), (0.2, 1.6),
    (0.15, 1.3833230302980657), (0.18, 1.3833230302980657),
    (0.22, 1.3833230302980657), (0.25, 1.3833230302980657),
    (0.30, 1.3833230302980657),
    # Initial-domain boundaries.
    (0.4, 0.05), (0.4, 1.0), (0.4, 1.3833230302980657),
    (0.4, 2.0), (0.4, 3.0), (0.0, 3.0), (0.2, 3.0),
    # First adaptive expansion.
    (0.8, 0.025), (0.8, 1.0), (0.8, 1.3833230302980657),
    (0.8, 3.0), (0.8, 6.0), (0.0, 6.0), (0.2, 6.0),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load_frozen_config() -> tuple[dict, dict]:
    freeze = load_yaml(FREEZE)
    config = merge(load_yaml(BASE_CONFIG), {
        "channel": {
            "tau_zen": freeze["channel"]["tau_zen"],
            "beam_waist_m": freeze["channel"]["beam_waist_m"],
            "aperture_radius_m": freeze["channel"]["aperture_radius_m"],
            "adaptive_optics_enabled": False,
            "phase_noise_enabled": False,
        },
        "cvqkd": freeze["cvqkd"],
    })
    return config, freeze


def model_identity() -> dict:
    paths = (
        ROOT / "docs" / "FINAL_MODEL_SPEC.md",
        ROOT / "docs" / "SECURITY_SCOPE_FREEZE.md",
        BASE_CONFIG,
        FREEZE,
        Path(__file__).resolve(),
        ROOT / "scripts" / "run_exact_mb_test2.py",
        ROOT / "src" / "cvqkd" / "holevo.py",
        ROOT / "src" / "cvqkd" / "mutual_information.py",
        ROOT / "src" / "cvqkd" / "gram_moments.py",
    )
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in paths}
    return {
        "schema": "redesigned-baseline-model-identity-v1",
        "files": files,
        "composite_sha256": _json_hash(files),
        "previous_final_model_spec_sha256": "8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843",
        "new_final_model_spec_sha256": files["docs/FINAL_MODEL_SPEC.md"],
    }


def channel_audit(config: dict, freeze: dict) -> tuple[dict, dict]:
    channel = freeze["channel"]
    physical = derive_physical_inputs(
        float(channel["tau_zen"]),
        aperture_radius_m_override=float(channel["aperture_radius_m"]),
        beam_waist_m_override=float(channel["beam_waist_m"]),
    )
    epsilon = float(channel["epsilon_total_snu"])
    moments = closed_form_channel_moments(physical, epsilon_total=epsilon)
    audit = {
        "tau_zen": float(channel["tau_zen"]),
        "w0_m": float(channel["beam_waist_m"]),
        "D_r_m": float(channel["receiver_diameter_m"]),
        "r_ap_m": float(channel["aperture_radius_m"]),
        "omega_L_eq_m": float(physical["pointing"]["omega_L_eq_m"]),
        "A0": float(moments["A0"]),
        "T_eff": float(moments["T_eff"]),
        "loss_dB": -10.0 * math.log10(float(moments["T_eff"])),
        "epsilon_total_snu": epsilon,
        "beta_reconciliation": float(config["cvqkd"]["beta_reconciliation"]),
        "AO": "OFF",
        "phase_noise": "OFF",
        "peak_constraint": "OFF",
        "budget_constraint": "OFF",
        "holevo": "DIRECT_Z_MINUS",
    }
    comparisons = {}
    for name, expected in EXPECTED.items():
        actual = audit[name]
        comparisons[name] = {
            "actual": actual,
            "expected": expected,
            "absolute_error": abs(actual - expected),
            "relative_error": abs(actual - expected) / abs(expected),
            "pass": math.isclose(actual, expected, rel_tol=5e-7, abs_tol=5e-9),
        }
    epsilon_checks = {str(va): epsilon for va in (0.05, 1.0, 3.0, 12.0)}
    unconstrained_checks = []
    for nu, va in ((0.0, 0.05), (0.4, 3.0), (1.6, 12.0)):
        ensemble = build_mb_ensemble(config, nu, va)
        unconstrained_checks.append({
            "nu_raw": nu,
            "V_A": va,
            "accepted": True,
            "peak_photon_diagnostic_only": float(ensemble.amplitudes.abs().square().max()),
        })
    audit.update({
        "channel_regression": comparisons,
        "epsilon_by_V_A": epsilon_checks,
        "ao_effect_on_channel": "NONE_BY_CONSTRUCTION",
        "phase_coefficient": 0.0,
        "unconstrained_candidate_checks": unconstrained_checks,
        "audit_status": "CURRENTLY_VERIFIED_PASS" if all(row["pass"] for row in comparisons.values()) else "FAILED",
    })
    if audit["audit_status"] != "CURRENTLY_VERIFIED_PASS":
        raise RuntimeError("Redesigned channel regression failed; optimization stopped.")
    return audit, {
        "T_eff": audit["T_eff"],
        "epsilon_base": epsilon,
        "c_phi": 0.0,
        "tau_zen": audit["tau_zen"],
        "eta_AO": 1.0,
        "AO": "OFF",
        "phase_noise": "OFF",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def cache_points() -> list[tuple[float, float]]:
    points = []
    for path in SOURCE_CACHE.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        try:
            points.append((float.fromhex(payload["nu_mb_raw_hex"]), float.fromhex(payload["V_A_hex"])))
        except (KeyError, ValueError):
            continue
    return list(dict.fromkeys(points))


def cache_path(evaluator: ExactMBEvaluator, config: dict, nu: float, va: float) -> Path:
    ensemble = build_mb_ensemble(config, nu, va)
    identity = evaluator._source_identity(ensemble, nu, va)
    return evaluator.cache_dir / f"{_json_hash(identity)}.json"


def evaluate_points(config: dict, channel: dict, evaluator: ExactMBEvaluator, points: list[tuple[float, float]]) -> list[dict]:
    rows = []
    for nu, va in sorted(points):
        if not cache_path(evaluator, config, nu, va).is_file():
            continue
        row = evaluate(config, channel, evaluator, nu, va)
        row.update({
            "holevo_mode": "DIRECT_Z_MINUS",
            "peak_constraint_active": False,
            "budget_constraint_active": False,
            "model_composite_sha256": model_identity()["composite_sha256"],
        })
        rows.append(row)
    return rows


def distinct_best(rows: list[dict], count: int = 7) -> list[dict]:
    selected = []
    for row in sorted(rows, key=lambda item: float(item["SKR"]), reverse=True):
        if any(
            abs(float(row["nu_raw"]) - float(old["nu_raw"])) < 0.005
            and abs(float(row["VA"]) - float(old["VA"])) < 0.02
            for old in selected
        ):
            continue
        selected.append(row)
        if len(selected) == count:
            break
    return selected


def boundary_rows(rows: list[dict], nu_max: float, va_min: float, va_max: float) -> dict[str, list[dict]]:
    tol = 1e-12
    return {
        "nu_min": [row for row in rows if abs(float(row["nu_raw"])) <= tol and va_min - tol <= float(row["VA"]) <= va_max + tol],
        "nu_max": [row for row in rows if abs(float(row["nu_raw"]) - nu_max) <= tol and va_min - tol <= float(row["VA"]) <= va_max + tol],
        "va_min": [row for row in rows if abs(float(row["VA"]) - va_min) <= tol and float(row["nu_raw"]) <= nu_max + tol],
        "va_max": [row for row in rows if abs(float(row["VA"]) - va_max) <= tol and float(row["nu_raw"]) <= nu_max + tol],
    }


def domain_history(rows: list[dict], freeze: dict) -> tuple[list[dict], dict]:
    opt = freeze["optimization"]
    minimum = int(opt["boundary_min_exact_points"])
    absolute = float(opt["boundary_closure_absolute_margin"])
    relative = float(opt["boundary_closure_relative_margin"])
    domains = [
        (float(opt["initial_nu_max"]), float(opt["initial_va_min"]), float(opt["initial_va_max"])),
        (0.8, 0.025, 6.0),
    ]
    history = []
    final_boundaries = {}
    for iteration, (nu_max, va_min, va_max) in enumerate(domains):
        inside = [row for row in rows if 0.0 <= float(row["nu_raw"]) <= nu_max and va_min <= float(row["VA"]) <= va_max]
        best = max(inside, key=lambda row: float(row["SKR"])) if inside else None
        boundaries = boundary_rows(inside, nu_max, va_min, va_max)
        margin = math.inf if best is None else max(absolute, relative * abs(float(best["SKR"])))
        status = {}
        for name, values in boundaries.items():
            if best is None or len(values) < minimum:
                status[name] = "UNRESOLVED"
                continue
            boundary_best = max(float(row["SKR"]) for row in values)
            if name == "nu_max":
                inner_band = [row for row in inside if 0.5 * nu_max <= float(row["nu_raw"]) < nu_max]
            elif name == "va_max":
                inner_band = [row for row in inside if 0.5 * va_max <= float(row["VA"]) < va_max]
            elif name == "va_min":
                inner_band = [row for row in inside if va_min < float(row["VA"]) <= 2.0 * va_min]
            else:
                inner_band = [row for row in inside if 0.0 < float(row["nu_raw"]) <= 0.5 * nu_max]
            turned_down = bool(inner_band) and boundary_best + margin < max(float(row["SKR"]) for row in inner_band)
            status[name] = "CLOSED" if boundary_best + margin < float(best["SKR"]) and turned_down else "UNRESOLVED"
        history.append({
            "iteration": iteration,
            "nu_min": 0.0,
            "nu_max": nu_max,
            "VA_min": va_min,
            "VA_max": va_max,
            "best_nu": None if best is None else best["nu_raw"],
            "best_VA": None if best is None else best["VA"],
            "best_SKR": None if best is None else best["SKR"],
            "boundary_status": ";".join(f"{name}={value}" for name, value in status.items()),
            "expansion_reason": "initial domain" if iteration == 0 else "initial boundaries lacked complete exact closure",
        })
        final_boundaries = {name: {"status": value, "exact_points": len(boundaries[name])} for name, value in status.items()}
    return history, final_boundaries


def save_figure(path: Path, figure: plt.Figure) -> None:
    figure.tight_layout()
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def make_figures(output: Path, rows: list[dict], best: dict | None) -> None:
    uniform = sorted((row for row in rows if float(row["nu_raw"]) == 0.0), key=lambda row: float(row["VA"]))
    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    axis.plot([row["VA"] for row in uniform], [row["SKR"] for row in uniform], "o-")
    axis.set(xlabel=r"$V_A$ (SNU)", ylabel="SKR (bits/use)", title="Uniform 256-QAM: direct $Z_-$")
    axis.grid(alpha=0.3)
    save_figure(output / "uniform_skr_vs_va", figure)

    nus = np.asarray([float(row["nu_raw"]) for row in rows])
    vas = np.asarray([float(row["VA"]) for row in rows])
    skrs = np.asarray([float(row["SKR"]) for row in rows])
    figure, axis = plt.subplots(figsize=(7.4, 5.2))
    scatter = axis.scatter(nus, vas, c=skrs, cmap="viridis", s=32)
    figure.colorbar(scatter, ax=axis, label="SKR (bits/use)")
    if best is not None:
        axis.scatter([best["nu_raw"]], [best["VA"]], marker="*", s=180, color="red")
    axis.set(xlabel=r"$\nu_{\rm raw}$", ylabel=r"$V_A$ (SNU)", title="Exact evaluated MB landscape")
    save_figure(output / "mb_skr_landscape", figure)

    figure, axis = plt.subplots(figsize=(7.4, 5.0))
    for nu in (0.0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.8):
        line = sorted((row for row in rows if abs(float(row["nu_raw"]) - nu) < 1e-12), key=lambda row: float(row["VA"]))
        if line:
            axis.plot([row["VA"] for row in line], [row["SKR"] for row in line], "o-", label=f"nu={nu:g}")
    axis.set(xlabel=r"$V_A$ (SNU)", ylabel="SKR (bits/use)", title=r"$V_A$ slices")
    axis.grid(alpha=0.3); axis.legend(fontsize=8)
    save_figure(output / "skr_vs_va_slices", figure)

    figure, axis = plt.subplots(figsize=(7.4, 5.0))
    for va in (0.1, 1.0, 1.3833230302980657, 2.0, 3.0, 6.0):
        line = sorted((row for row in rows if abs(float(row["VA"]) - va) < 1e-9), key=lambda row: float(row["nu_raw"]))
        if line:
            axis.plot([row["nu_raw"] for row in line], [row["SKR"] for row in line], "o-", label=f"VA={va:g}")
    axis.set(xlabel=r"$\nu_{\rm raw}$", ylabel="SKR (bits/use)", title=r"$\nu_{\rm raw}$ slices")
    axis.grid(alpha=0.3); axis.legend(fontsize=8)
    save_figure(output / "skr_vs_nu_slices", figure)

    local = [row for row in rows if 0.1 <= float(row["nu_raw"]) <= 0.35 and 0.7 <= float(row["VA"]) <= 2.2]
    figure, axis = plt.subplots(figsize=(7.2, 5.0))
    local_scatter = axis.scatter([row["nu_raw"] for row in local], [row["VA"] for row in local], c=[row["SKR"] for row in local], cmap="plasma", s=45)
    figure.colorbar(local_scatter, ax=axis, label="SKR (bits/use)")
    axis.set(xlabel=r"$\nu_{\rm raw}$", ylabel=r"$V_A$ (SNU)", title="Local exact landscape")
    save_figure(output / "local_landscape_zoom", figure)

    figure, axis = plt.subplots(figsize=(7.4, 5.0))
    for nu in sorted(set(float(row["nu_raw"]) for row in rows)):
        line = sorted((row for row in rows if float(row["nu_raw"]) == nu), key=lambda row: float(row["VA"]))
        if nu in {0.0, 0.2, 0.3, 0.4, 0.8}:
            axis.plot([row["VA"] for row in line], [row["SKR"] for row in line], "o-", label=f"nu={nu:g}")
    axis.set(xlabel=r"$V_A$ (SNU)", ylabel="SKR (bits/use)", title="Boundary-validation coverage")
    axis.grid(alpha=0.3); axis.legend(fontsize=8)
    save_figure(output / "boundary_validation", figure)


def markdown_report(audit: dict, summary: dict, candidates: list[dict], history: list[dict]) -> str:
    lines = [
        "# Redesigned-baseline global MB/V_A numerical optimization",
        "", "## A. Baseline audit", "",
        f"- tau_zen: {audit['tau_zen']}", f"- w0: {audit['w0_m']} m",
        f"- D_r: {audit['D_r_m']} m", f"- r_ap: {audit['r_ap_m']} m",
        f"- omega_L,eq: {audit['omega_L_eq_m']:.12g} m", f"- A0: {audit['A0']:.12g}",
        f"- T_eff: {audit['T_eff']:.12g}", f"- loss: {audit['loss_dB']:.12g} dB",
        f"- epsilon_total: {audit['epsilon_total_snu']} SNU", f"- beta: {audit['beta_reconciliation']}",
        "- AO = OFF", "- PHASE NOISE = OFF", "- PEAK CONSTRAINT = OFF",
        "- BUDGET CONSTRAINT = OFF", "- HOLEVO = DIRECT Z_MINUS", "",
        "## B. Uniform optimum", "",
        json.dumps(summary.get("best_uniform_exact"), indent=2), "",
        "## C. MB global search", "",
    ]
    lines.extend(f"- iteration {row['iteration']}: {row['boundary_status']}" for row in history)
    lines.extend(["", "## D. Best exact candidates", "", "|nu_raw|V_A|I_AB|beta I_AB|chi_BE(Z-)|SKR|", "|---:|---:|---:|---:|---:|---:|"])
    lines.extend(f"|{row['nu_raw']}|{row['VA']}|{row['I_AB']}|{row['beta_IAB']}|{row['chi_BE']}|{row['SKR']}|" for row in candidates)
    lines.extend(["", "## E. Boundary diagnostics", "", json.dumps(summary["boundary_diagnostics"], indent=2), "", "## F. Final result", "", json.dumps(summary.get("best_mb_exact"), indent=2), "", summary["status"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--max-new-source-points", type=int, default=0)
    parser.add_argument("--source-workers", type=int, default=1)
    args = parser.parse_args()
    if args.max_new_source_points < 0:
        parser.error("--max-new-source-points must be nonnegative")
    torch.set_num_threads(1)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config, freeze = load_frozen_config()
    audit, channel = channel_audit(config, freeze)
    identity = model_identity()
    (output / "parameter_audit.json").write_text(json.dumps({"freeze": freeze, "model_identity": identity}, indent=2) + "\n", encoding="utf-8")
    (output / "channel_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (output / "resolved_config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(FREEZE, output / FREEZE.name)
    print(json.dumps({"model_identity": identity, "channel_audit": audit}, indent=2), flush=True)
    if args.audit_only:
        return 0

    evaluator = ExactMBEvaluator(config, channel, output, source_cache_dir=SOURCE_CACHE, allow_legacy_exact_import=False)
    points = cache_points()
    missing = [point for point in PRIORITY_NEW_POINTS if not cache_path(evaluator, config, *point).is_file()]
    selected = missing[:args.max_new_source_points]
    if selected:
        evaluator.prepare_sources(selected, args.source_workers)
        points.extend(selected)
    rows = evaluate_points(config, channel, evaluator, list(dict.fromkeys(points)))
    write_csv(output / "evaluated_points.csv", rows)
    history, boundaries = domain_history(rows, freeze)
    write_csv(output / "adaptive_domain_history.csv", history)
    ranked = distinct_best([row for row in rows if float(row["nu_raw"]) > 0.0])
    uniform = [row for row in rows if float(row["nu_raw"]) == 0.0]
    best_uniform = max(uniform, key=lambda row: float(row["SKR"])) if uniform else None
    best_mb = ranked[0] if ranked else None
    boundary_candidates = []
    for name, values in boundary_rows(rows, 0.8, 0.025, 6.0).items():
        if values:
            boundary_candidates.append({**max(values, key=lambda row: float(row["SKR"])), "boundary": name})
    final_rows = ([{"scheme": "Uniform", **best_uniform}] if best_uniform else []) + [
        {"scheme": "MB", **row} for row in ranked
    ] + [{"scheme": "Boundary", **row} for row in boundary_candidates]
    write_csv(output / "exact_candidates.csv", final_rows)
    all_closed = all(item["status"] == "CLOSED" for item in boundaries.values())
    status = "GLOBAL_OPTIMUM_RESOLVED" if all_closed and best_mb is not None else "GLOBAL_OPTIMUM_UNRESOLVED"
    summary = {
        "status": status,
        "audit_status": audit["audit_status"],
        "model_identity": identity,
        "authorization": "AUTHOR_MODEL_LEVEL_RE_FREEZE_AND_GLOBAL_OPTIMIZATION",
        "evaluated_exact_points": len(rows),
        "fresh_source_points_requested": len(selected),
        "best_uniform_exact": best_uniform,
        "best_mb_exact": best_mb,
        "delta_K_mb_minus_uniform": None if best_mb is None or best_uniform is None else float(best_mb["SKR"]) - float(best_uniform["SKR"]),
        "boundary_diagnostics": boundaries,
        "limitations": [
            "A boundary is unresolved unless at least three exact points exist on it and a numerical closure rule is certified.",
            "Missing source moments are never interpolated or replaced by historical SKR values.",
            "Exact source C,w cache reuse is allowed only by exact ensemble and implementation identity; SKR is recomputed under the new model hash.",
        ],
    }
    (output / "final_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output / "final_report.md").write_text(markdown_report(audit, summary, final_rows, history), encoding="utf-8")
    (output / "cache_metadata.json").write_text(json.dumps({
        "source_cache": str(SOURCE_CACHE.relative_to(ROOT)).replace("\\", "/"),
        "source_cache_policy": "exact ensemble/source-implementation identity only",
        "evaluated_point_model_hash": identity["composite_sha256"],
        "cache_point_count_before": len(cache_points()),
    }, indent=2) + "\n", encoding="utf-8")
    make_figures(output, rows, best_mb)
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
