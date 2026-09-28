"""Restartable exact AP coverage for the fixed-channel joint MB/V_A study.

This runner processes the requested regions in scientific priority order and
never substitutes a missing C,w source moment.  Source files are written by
the shared evaluator as each AP job finishes, so an interrupted batch can be
restarted safely.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import ExactMBEvaluator, channel_fixture
from scripts.run_joint_mb_va_global_certification import (
    cache_identity,
    EXISTING_UNIFORM_VAS,
    SHARED_CACHE,
    UNIFORM_VAS,
    V_MIN,
    best_row,
    boundary_lookup,
    cached_evaluate,
    global_candidates,
    make_boundary,
    prepare_missing,
    read_csv,
    write_csv,
)


OUTPUT = ROOT / "results" / "joint_mb_va_global" / "ap_coverage"
LOCAL_NUS = tuple(round(0.20 + 0.01 * i, 2) for i in range(9))
LOCAL_VAS = tuple(round(1.80 + 0.05 * i, 2) for i in range(8))


def local_candidates(config: dict, boundary: list[dict]) -> list[tuple[float, float]]:
    points = []
    for nu in LOCAL_NUS:
        vmax = float(boundary_lookup(boundary, nu)["V_A_max_feasible"])
        for va in LOCAL_VAS:
            if V_MIN <= va <= vmax + 1e-10:
                points.append((nu, va))
    return points


def boundary_candidates(boundary: list[dict]) -> list[tuple[float, float]]:
    return [
        (float(row["nu_raw"]), float(row["V_A_max_feasible"]))
        for row in boundary
        if row.get("domain_status") == "FEASIBLE_VA_INTERVAL"
    ]


def uniform_candidates() -> list[tuple[float, float]]:
    return [(0.0, va) for va in sorted(set(UNIFORM_VAS + EXISTING_UNIFORM_VAS))]


def global_priority(points: list[tuple[float, float, float]], boundary: list[dict]) -> list[dict]:
    rows = []
    for nu, va, fraction in points:
        bound = boundary_lookup(boundary, nu)
        near_candidate = 0.20 <= nu <= 0.28 and 1.75 <= va <= 2.15
        near_boundary = abs(va - float(bound["V_A_max_feasible"])) <= 0.15
        if near_candidate or near_boundary:
            priority = "HIGH_PRIORITY"
            reason = "current_best_region_or_peak_boundary"
        elif 0.10 <= nu <= 0.30:
            priority = "MEDIUM_PRIORITY"
            reason = "near_current_global_scan_region"
        else:
            priority = "LOW_PRIORITY"
            reason = "distant_from_current_incumbent"
        rows.append({
            "nu_raw": nu,
            "VA": va,
            "grid_fraction": fraction,
            "priority": priority,
            "reason": reason,
        })
    return rows


def pair_key(row: dict) -> tuple[float, float] | None:
    try:
        return float(row["nu_raw"]), float(row.get("VA", row.get("V_A")))
    except (TypeError, ValueError, KeyError):
        return None


def existing_incumbent() -> dict | None:
    rows = []
    for path in (
        ROOT / "results" / "joint_mb_va" / "joint_landscape.csv",
        ROOT / "results" / "joint_mb_va" / "local_refinement.csv",
        ROOT / "results" / "joint_mb_va_global" / "global_landscape.csv",
    ):
        rows.extend(read_csv(path))
    return best_row(rows)


def annotate_exact(row: dict, stage: str, fresh_pairs: set[tuple[float, float]]) -> dict:
    result = dict(row)
    key = pair_key(row)
    if result.get("evaluation_status") == "EXACT_CACHE_EVALUATION":
        result["coverage_status"] = "EXACT_AP_COMPLETE"
        result["fresh_or_cache"] = "FRESH_EXACT_EVALUATION" if key in fresh_pairs else "CACHE_EXACT_SOURCE"
    elif result.get("evaluation_status") == "MISSING_EXACT_SOURCE_CACHE":
        result["coverage_status"] = "INCOMPLETE_AP_MISSING"
        result["fresh_or_cache"] = "NOT_AVAILABLE"
    else:
        result["coverage_status"] = "FAILED_CLOSED"
        result["fresh_or_cache"] = "NOT_AVAILABLE"
    result["coverage_stage"] = stage
    return result


def update_incumbent(rows: list[dict], incumbent: dict | None, stage: str) -> tuple[list[dict], dict | None]:
    progress = []
    current = incumbent
    for row in rows:
        if row.get("coverage_status") != "EXACT_AP_COMPLETE":
            row["classification"] = "INCOMPLETE_AP"
            continue
        value = float(row["SKR"])
        improved = current is None or value > float(current["SKR"])
        if improved:
            current = row
        row["classification"] = "INCUMBENT_UPDATED" if improved else "EXACT_NONINCUMBENT"
        row["best_so_far"] = float(current["SKR"])
        progress.append({
            "stage": stage,
            "nu_raw": row["nu_raw"],
            "VA": row["VA"],
            "SKR": row["SKR"],
            "best_so_far": row["best_so_far"],
            "classification": row["classification"],
        })
    return progress, current


def stage_points(stage: str, config: dict, boundary: list[dict]) -> tuple[list[tuple[float, float]], list[dict]]:
    if stage == "local":
        points = local_candidates(config, boundary)
        return points, [{"nu_raw": nu, "VA": va, "priority": "HIGH_PRIORITY", "reason": "requested_local_mesh"} for nu, va in points]
    if stage == "boundary":
        points = boundary_candidates(boundary)
        return points, [{"nu_raw": nu, "VA": va, "priority": "HIGH_PRIORITY", "reason": "requested_boundary"} for nu, va in points]
    if stage == "uniform":
        points = uniform_candidates()
        return points, [{"nu_raw": nu, "VA": va, "priority": "HIGH_PRIORITY", "reason": "requested_uniform_baseline"} for nu, va in points]
    if stage == "global-high":
        all_points = global_candidates(boundary)
        priority = global_priority(all_points, boundary)
        selected = [row for row in priority if row["priority"] == "HIGH_PRIORITY"]
        return [(float(row["nu_raw"]), float(row["VA"])) for row in selected], selected
    raise ValueError(f"unknown stage: {stage}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("local", "boundary", "uniform", "global-high"), required=True)
    parser.add_argument("--source-workers", type=int, default=4)
    parser.add_argument(
        "--max-new-source-points",
        type=int,
        default=None,
        help="Cap fresh AP jobs; omit for all missing stage points, use 0 for cache-only.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Roster/cache check only; do not launch AP jobs.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.max_new_source_points is not None and args.max_new_source_points < 0:
        parser.error("--max-new-source-points must be nonnegative")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    boundary = make_boundary(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.stage == "global-high":
        write_csv(args.output_dir / "global_priority.csv", global_priority(global_candidates(boundary), boundary))
    points, roster = stage_points(args.stage, config, boundary)
    write_csv(args.output_dir / f"{args.stage}_roster.csv", roster)
    evaluator = ExactMBEvaluator(config, channel, args.output_dir, source_cache_dir=SHARED_CACHE)

    missing_before = []
    for nu, va in points:
        try:
            identity = cache_identity(evaluator, config, nu, va)
            if not identity["source_cache_path"].is_file():
                missing_before.append((nu, va))
        except Exception:
            pass
    budget = 0 if args.dry_run else (
        len(missing_before) if args.max_new_source_points is None else args.max_new_source_points
    )
    source_error = None
    prepared = 0
    try:
        prepared = prepare_missing(config, evaluator, points, budget, args.source_workers)
    except Exception as error:
        source_error = f"{type(error).__name__}: {error}"
    fresh_pairs = set()
    for point in missing_before:
        try:
            identity = cache_identity(evaluator, config, *point)
            if identity["source_cache_path"].is_file():
                fresh_pairs.add(point)
        except Exception:
            pass
    prepared = len(fresh_pairs)

    rows = []
    for nu, va in points:
        row = cached_evaluate(config, channel, evaluator, nu, va, search_stage=f"ap_coverage_{args.stage}")
        rows.append(annotate_exact(row, args.stage, fresh_pairs))
    if source_error is not None:
        for row in rows:
            if row.get("coverage_status") == "INCOMPLETE_AP_MISSING":
                row["coverage_status"] = "AP_FAILED_CLOSED"
                row["failure_reason"] = source_error
    rows.sort(key=lambda row: (float(row["nu_raw"]), float(row["VA"])))
    write_csv(args.output_dir / f"{args.stage}.csv", rows)

    incumbent = existing_incumbent()
    progress_path = args.output_dir / "incumbent_progress.csv"
    progress = read_csv(progress_path)
    new_progress, incumbent = update_incumbent(rows, incumbent, args.stage)
    seen = {(str(row.get("stage")), str(row.get("nu_raw")), str(row.get("VA"))) for row in progress}
    progress.extend(
        row for row in new_progress
        if (str(row["stage"]), str(row["nu_raw"]), str(row["VA"])) not in seen
    )
    write_csv(progress_path, progress)

    exact = [row for row in rows if row.get("coverage_status") == "EXACT_AP_COMPLETE"]
    incomplete = [
        row for row in rows
        if row.get("coverage_status") in {"INCOMPLETE_AP_MISSING", "AP_FAILED_CLOSED", "FAILED_CLOSED"}
    ]
    write_csv(
        args.output_dir / f"{args.stage}_failed_or_incomplete.csv",
        [
            {
                "stage": args.stage,
                "nu_raw": row.get("nu_raw"),
                "VA": row.get("VA"),
                "coverage_status": row.get("coverage_status"),
                "failure_reason": row.get("failure_reason", "missing exact source cache"),
                "source_cache_key": row.get("source_cache_key"),
                "ensemble_hash": row.get("ensemble_hash"),
            }
            for row in incomplete
        ],
    )
    report = {
        "status": "CURRENTLY_VERIFIED_PASS" if not incomplete and source_error is None else "INCOMPLETE_AP_COVERAGE",
        "stage": args.stage,
        "channel_fixture": channel,
        "requested_points": len(points),
        "exact_points": len(exact),
        "missing_points": len(incomplete),
        "failed_or_incomplete_points": [
            {
                "nu_raw": row.get("nu_raw"),
                "VA": row.get("VA"),
                "status": row.get("coverage_status"),
                "reason": row.get("failure_reason", "missing exact source cache"),
            }
            for row in incomplete
        ],
        "fresh_source_points_prepared": prepared,
        "source_error": source_error,
        "incumbent": incumbent,
        "cache_dir": str(SHARED_CACHE.relative_to(ROOT)).replace("\\", "/"),
        "no_interpolation": True,
        "no_surrogate": True,
        "adam": "NOT RUN",
    }
    (args.output_dir / f"{args.stage}_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return 0 if source_error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
