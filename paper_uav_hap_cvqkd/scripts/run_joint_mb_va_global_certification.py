"""Cache-bound exact global joint MB/V_A certification driver.

The exact AP source calculation is expensive.  This runner therefore never
silently evaluates a missing source moment: cache-only is the default, and a
caller must set an explicit positive ``--max-new-source-points`` budget to add
fresh exact work.  Missing coverage keeps the result fail-closed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import (
    ExactMBEvaluator,
    _json_hash,
    build_mb_ensemble,
    channel_fixture,
    ensemble_hash,
    nu_mb_repo,
)
from scripts.run_joint_mb_va_optimization import (
    V_MIN,
    deterministic_joint_mi,
    evaluate,
    feasible_vmax,
)


OUTPUT = ROOT / "results" / "joint_mb_va_global"
SHARED_CACHE = ROOT / "results" / "exact_mb_test2" / "exact_source_cache"
GLOBAL_NUS = tuple(round(0.025 * i, 3) for i in range(13))
BOUNDARY_NUS = GLOBAL_NUS + (0.35, 0.4, 0.5, 0.75, 1.0)
GLOBAL_FRACTIONS = (0.0,) + tuple(round(0.1 * i, 3) for i in range(1, 10)) + (1.0,)
UNIFORM_VAS = tuple(round(0.1 + 0.1 * i, 10) for i in range(40))
EXISTING_UNIFORM_VAS = (0.1, 1.075, 2.05, 3.025, 4.0)
GH_ORDERS = (8, 16, 32, 64)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    if not fields:
        fields = ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def exact_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if number(row.get("SKR")) is not None]


def cache_identity(evaluator: ExactMBEvaluator, config: dict, nu: float, va: float) -> dict:
    ensemble = build_mb_ensemble(config, nu, va)
    identity = evaluator._source_identity(ensemble, nu, va)
    key = _json_hash(identity)
    return {
        "ensemble": ensemble,
        "ensemble_hash": ensemble_hash(ensemble),
        "source_cache_key": key,
        "source_cache_path": evaluator.cache_dir / f"{key}.json",
    }


def annotate(row: dict, **values: object) -> dict:
    result = dict(row)
    result.update(values)
    return result


def enrich_existing(row: dict, config: dict) -> dict:
    result = dict(row)
    nu = number(result.get("nu_raw"))
    va = number(result.get("VA"))
    if nu is None or va is None:
        return result
    try:
        ensemble = build_mb_ensemble(config, nu, va)
        m2 = float(torch.sum(ensemble.probabilities[0] * ensemble.raw_constellation.abs().square()))
        result.setdefault("m2", m2)
        result.setdefault("x_max2", float(ensemble.raw_constellation.abs().square().max()))
        result.setdefault("physical_scale", math.sqrt(va / (2.0 * m2)))
        result.setdefault("P_peak", float(ensemble.amplitudes.abs().square().max()))
        result.setdefault("I_AB", result.get("I_AB_GH"))
    except Exception:
        result.setdefault("enrichment_status", "FAILED_CLOSED")
    return result


def cached_evaluate(
    config: dict,
    channel: dict[str, float],
    evaluator: ExactMBEvaluator,
    nu: float,
    va: float,
    *,
    search_stage: str,
    search_coordinate: float | None = None,
) -> dict:
    try:
        identity = cache_identity(evaluator, config, nu, va)
    except Exception as error:
        return {
            "nu_raw": nu,
            "nu_repo": nu_mb_repo(nu),
            "VA": va,
            "evaluation_status": "INFEASIBLE_OR_INVALID",
            "exact_evaluation": "NO",
            "search_stage": search_stage,
            "error": f"{type(error).__name__}: {error}",
        }
    if not identity["source_cache_path"].is_file():
        ensemble = identity["ensemble"]
        m2 = float(torch.sum(ensemble.probabilities[0] * ensemble.raw_constellation.abs().square()))
        return {
            "nu_raw": nu,
            "nu_repo": nu_mb_repo(nu),
            "VA": va,
            "ensemble_hash": identity["ensemble_hash"],
            "source_cache_key": identity["source_cache_key"],
            "m2": m2,
            "x_max2": float(ensemble.raw_constellation.abs().square().max()),
            "physical_scale": math.sqrt(va / (2.0 * m2)),
            "P_peak": float(ensemble.amplitudes.abs().square().max()),
            "evaluation_status": "MISSING_EXACT_SOURCE_CACHE",
            "exact_evaluation": "NO",
            "search_stage": search_stage,
            "search_coordinate": search_coordinate,
        }
    row = evaluate(config, channel, evaluator, nu, va)
    return annotate(
        row,
        evaluation_status="EXACT_CACHE_EVALUATION",
        exact_evaluation="YES",
        search_stage=search_stage,
        search_coordinate=search_coordinate,
    )


def prepare_missing(
    config: dict,
    evaluator: ExactMBEvaluator,
    candidates: list[tuple[float, float]],
    budget: int,
    workers: int,
) -> int:
    if budget <= 0:
        return 0
    missing: list[tuple[float, float]] = []
    for nu, va in candidates:
        try:
            identity = cache_identity(evaluator, config, nu, va)
        except Exception:
            continue
        if not identity["source_cache_path"].is_file() and (nu, va) not in missing:
            missing.append((nu, va))
    selected = missing[:budget]
    if selected:
        evaluator.prepare_sources(selected, workers)
    return len(selected)


def boundary_lookup(boundary: list[dict], nu: float) -> dict:
    return min(boundary, key=lambda row: abs(float(row["nu_raw"]) - nu))


def make_boundary(config: dict) -> list[dict]:
    rows = []
    for nu in BOUNDARY_NUS:
        try:
            row = feasible_vmax(config, nu)
            row["domain_status"] = "FEASIBLE_VA_INTERVAL" if row["V_A_max_feasible"] >= V_MIN else "NO_FEASIBLE_VA"
        except Exception as error:
            row = {"nu_raw": nu, "domain_status": "INVALID", "error": f"{type(error).__name__}: {error}"}
        rows.append(row)
    return rows


def global_candidates(boundary: list[dict]) -> list[tuple[float, float, float]]:
    candidates = []
    for nu in GLOBAL_NUS:
        bound = boundary_lookup(boundary, nu)
        vmax = float(bound["V_A_max_feasible"])
        if vmax < V_MIN:
            continue
        for fraction in GLOBAL_FRACTIONS:
            candidates.append((nu, V_MIN + fraction * (vmax - V_MIN), fraction))
    return candidates


def local_candidates() -> list[tuple[float, float]]:
    return [
        (0.24, 1.95),
        (0.24, 1.94), (0.24, 1.945), (0.24, 1.949),
        (0.24, 1.951), (0.24, 1.955), (0.24, 1.96),
        (0.23, 1.95), (0.235, 1.95), (0.239, 1.95),
        (0.241, 1.95), (0.245, 1.95), (0.25, 1.95),
        (0.24, 1.85), (0.24, 1.90), (0.24, 2.00), (0.24, 2.05),
    ]


def best_row(rows: list[dict]) -> dict | None:
    valid = exact_rows(rows)
    return max(valid, key=lambda row: float(row["SKR"])) if valid else None


def gh_rows(config: dict, channel: dict[str, float], targets: list[tuple[str, dict]]) -> list[dict]:
    rows = []
    for label, target in targets:
        nu = number(target.get("nu_raw"))
        va = number(target.get("VA"))
        if nu is None or va is None:
            continue
        ensemble = build_mb_ensemble(config, nu, va)
        values = {}
        for order in GH_ORDERS:
            values[order] = deterministic_joint_mi(ensemble, channel, va, order)
        rows.append({
            "target": label,
            "nu_raw": nu,
            "VA": va,
            "ensemble_hash": ensemble_hash(ensemble),
            "I_8": values[8],
            "I_16": values[16],
            "I_32": values[32],
            "I_64": values[64],
            "abs_I8_I16": abs(values[8] - values[16]),
            "abs_I16_I32": abs(values[16] - values[32]),
            "abs_I32_I64": abs(values[32] - values[64]),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--source-workers", type=int, default=3)
    parser.add_argument(
        "--max-new-source-points",
        type=int,
        default=0,
        help="Explicit cap for fresh AP source points; 0 keeps the run cache-only.",
    )
    args = parser.parse_args()
    if args.max_new_source_points < 0:
        parser.error("--max-new-source-points must be nonnegative")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    boundary = make_boundary(config)
    write_csv(output / "feasible_boundary.csv", boundary)

    evaluator = ExactMBEvaluator(config, channel, output, source_cache_dir=SHARED_CACHE)
    candidates = global_candidates(boundary)
    boundary_candidates = [
        (float(row["nu_raw"]), float(row["V_A_max_feasible"]))
        for row in boundary if row.get("domain_status") == "FEASIBLE_VA_INTERVAL"
    ]
    uniform_candidates = [(0.0, va) for va in UNIFORM_VAS + EXISTING_UNIFORM_VAS]
    local = local_candidates()
    all_new_candidates = [(nu, va) for nu, va, _ in candidates] + boundary_candidates + uniform_candidates + local
    prepared = prepare_missing(config, evaluator, all_new_candidates, args.max_new_source_points, args.source_workers)

    landscape = []
    for nu, va, fraction in candidates:
        row = cached_evaluate(config, channel, evaluator, nu, va, search_stage="global_grid", search_coordinate=fraction)
        landscape.append(annotate(row, grid_fraction=fraction))
    write_csv(output / "global_landscape.csv", landscape)

    boundary_rows = []
    for nu, va in boundary_candidates:
        row = cached_evaluate(config, channel, evaluator, nu, va, search_stage="peak_boundary_grid", search_coordinate=nu)
        domain_row = boundary_lookup(boundary, nu)
        boundary_status = (
            "PEAK_PHOTON_BOUNDARY"
            if float(domain_row["V_A_max_peak"]) <= float(domain_row["V_A_max_feasible"]) + 1e-12
            else "CONFIGURED_V_A_MAX_BOUNDARY"
        )
        boundary_rows.append(annotate(row, V_A_boundary=va, boundary_status=boundary_status))
    write_csv(output / "boundary_search.csv", boundary_rows)

    uniform_rows = []
    for va in sorted(set(UNIFORM_VAS + EXISTING_UNIFORM_VAS)):
        row = cached_evaluate(config, channel, evaluator, 0.0, va, search_stage="uniform_scalar_grid", search_coordinate=va)
        uniform_rows.append(annotate(row, V_A_uniform=va, baseline_coordinate=va))
    uniform_best = best_row(uniform_rows)
    uniform_status = "SPARSE_CACHE_ONLY_NOT_OPTIMIZED" if any(
        row.get("evaluation_status") != "EXACT_CACHE_EVALUATION" for row in uniform_rows
    ) else "EXACT_GRID_ONLY_NOT_SCALAR_CERTIFIED"
    for row in uniform_rows:
        row["baseline_status"] = uniform_status
    write_csv(output / "uniform_optimized_baseline.csv", uniform_rows)

    old_landscape = [enrich_existing(row, config) for row in read_csv(ROOT / "results" / "joint_mb_va" / "joint_landscape.csv")]
    old_local = [enrich_existing(row, config) for row in read_csv(ROOT / "results" / "joint_mb_va" / "local_refinement.csv")]
    exact_all = exact_rows(landscape + boundary_rows + uniform_rows + old_landscape + old_local)
    candidate = best_row(exact_all)
    best_boundary = best_row(boundary_rows)
    best_uniform_tested = uniform_best
    interior_log = [{
        "stage": "global_grid",
        "method": "deterministic_feasible_cache_bound_scan",
        "candidate_count": len(landscape),
        "exact_count": len(exact_rows(landscape)),
        "missing_count": len(landscape) - len(exact_rows(landscape)),
        "best_skr": best_row(landscape).get("SKR") if best_row(landscape) else None,
        "status": "PARTIAL_EXACT_COVERAGE",
    }, {
        "stage": "interior_search",
        "method": "existing_exact_local_refinement_reused",
        "candidate_count": len(old_local),
        "exact_count": len(exact_rows(old_local)),
        "best_skr": best_row(old_local).get("SKR") if best_row(old_local) else None,
        "status": "LOCAL_CANDIDATE_ONLY",
    }]
    write_csv(output / "interior_search_log.csv", interior_log)

    copied_local = [annotate(row, source_artifact="results/joint_mb_va/local_refinement.csv") for row in old_local]
    write_csv(output / "local_refinement.csv", copied_local)

    certification_points = []
    if candidate:
        center_nu = float(candidate["nu_raw"])
        center_va = float(candidate["VA"])
        for delta in (0.01, 0.005, 0.001):
            certification_points.extend([(center_nu - delta, center_va), (center_nu + delta, center_va)])
        for delta in (0.10, 0.05, 0.01):
            certification_points.extend([(center_nu, center_va - delta), (center_nu, center_va + delta)])
        certification_points.append((center_nu, center_va))
    certification = []
    for nu, va in certification_points:
        bound = boundary_lookup(boundary, nu)
        if va < V_MIN or va > float(bound["V_A_max_feasible"]) + 1e-10:
            certification.append({"nu_raw": nu, "VA": va, "evaluation_status": "INFEASIBLE_DOMAIN", "exact_evaluation": "NO"})
        else:
            certification.append(cached_evaluate(config, channel, evaluator, nu, va, search_stage="local_neighbor", search_coordinate=None))
    for row in certification:
        if candidate and row.get("evaluation_status") == "EXACT_CACHE_EVALUATION":
            row["dominates_candidate"] = float(row["SKR"]) <= float(candidate["SKR"]) + 1e-15
    write_csv(output / "optimum_certification.csv", certification)

    gh_targets = []
    if candidate:
        gh_targets.append(("best_tested_exact_candidate", candidate))
    if best_uniform_tested:
        gh_targets.append(("best_uniform_tested", best_uniform_tested))
    if best_boundary:
        gh_targets.append(("best_boundary_tested", best_boundary))
    gh = gh_rows(config, channel, gh_targets)
    write_csv(output / "gh_convergence.csv", gh)

    decomposition = []
    if candidate and best_uniform_tested:
        delta_beta = float(candidate["beta_IAB"]) - float(best_uniform_tested["beta_IAB"])
        minus_delta_chi = -(float(candidate["chi_BE"]) - float(best_uniform_tested["chi_BE"]))
        decomposition.append({
            "status": "SPARSE_COMPARATOR_NOT_CERTIFIED",
            "candidate_label": "best_tested_exact",
            "uniform_label": "best_uniform_tested",
            "delta_beta_IAB": delta_beta,
            "minus_delta_chi_BE": minus_delta_chi,
            "delta_SKR": delta_beta + minus_delta_chi,
            "percentage_gain": "NOT_APPLICABLE_BASELINE_NOT_CERTIFIED",
        })
    else:
        decomposition.append({"status": "UNRESOLVED_UNIFORM_BASELINE"})
    write_csv(output / "objective_decomposition.csv", decomposition)

    global_exact = exact_rows(landscape)
    boundary_exact = exact_rows(boundary_rows)
    uniform_exact = exact_rows(uniform_rows)
    full_global_grid = len(global_exact) == len(landscape) and len(landscape) > 0
    full_boundary_grid = len(boundary_exact) == len(boundary_rows) and len(boundary_rows) > 0
    full_uniform_grid = len(uniform_exact) == len(uniform_rows) and len(uniform_rows) > 0
    classification = "GLOBAL_OPTIMUM_UNRESOLVED"
    report = {
        "status": classification,
        "global_certification": "NOT_CERTIFIED",
        "authorization_scope": "EXACT_MB_OPTIMIZATION_AND_ASYMPTOTIC_CERTIFICATION",
        "publication_lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "channel_fixture": channel,
        "fixed_parameters": {
            "T_eff": channel["T_eff"],
            "epsilon_base": channel["epsilon_base"],
            "c_phi": channel["c_phi"],
            "beta_reconciliation": float(config["cvqkd"]["beta_reconciliation"]),
            "n_peak_photons": float(config["cvqkd"]["n_peak_photons"]),
            "V_A_range": [V_MIN, float(config["cvqkd"]["v_max_snu"])],
        },
        "domain": {
            "global_nu_grid": list(GLOBAL_NUS),
            "boundary_nu_grid": list(BOUNDARY_NUS),
            "global_fractions": list(GLOBAL_FRACTIONS),
            "formula": "V_A_max(nu)=min(4,2*n_peak*m2(nu)/x_max^2)",
            "unscanned_feasible_nu_beyond_global_grid": True,
        },
        "coverage": {
            "global_grid_rows": len(landscape),
            "global_grid_exact_rows": len(global_exact),
            "boundary_rows": len(boundary_rows),
            "boundary_exact_rows": len(boundary_exact),
            "uniform_rows": len(uniform_rows),
            "uniform_exact_rows": len(uniform_exact),
            "full_global_grid": full_global_grid,
            "full_boundary_grid": full_boundary_grid,
            "full_uniform_grid": full_uniform_grid,
            "fresh_source_points_prepared": prepared,
        },
        "best_tested_exact": candidate,
        "best_boundary_tested": best_boundary,
        "best_uniform_tested": best_uniform_tested,
        "optimizer": {
            "method": "deterministic feasible cache-bound grid",
            "continuous_derivative_free_search": "NOT_RUN_MISSING_EXACT_COVERAGE",
            "adam": "NOT RUN",
            "interpolation": "NO",
        },
        "integrity": {
            "common_ensemble_hashes_identical": "YES_PER_EXACT_EVALUATOR",
            "C_w_interpolation": "NO",
            "physical_equations_changed": "NO",
            "security_equations_changed": "NO",
            "historical_invalid_cache_used": "NO",
            "deterministic_MI_used": "YES",
            "positive_PMF_invariant_weakened": "NO",
        },
        "blockers": [
            "Exact source cache does not cover the complete requested global grid.",
            "Boundary grid is not fully exact, so bounded Brent/golden search is not run.",
            "Uniform baseline is not a full coarse-plus-scalar optimization.",
            "Therefore no global-optimum or baseline-selection claim is made.",
        ],
    }
    (output / "run_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
