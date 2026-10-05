"""Resume the redesigned MB/V_A search along the unresolved high-V_A ridge."""

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

from scripts.run_redesigned_global_mb_va_optimization import (
    OUTPUT,
    SOURCE_CACHE,
    cache_path,
    channel_audit,
    distinct_best,
    evaluate_points,
    load_frozen_config,
    make_figures,
    model_identity,
    write_csv,
)
from scripts.run_exact_mb_test2 import ExactMBEvaluator


PRIMARY = tuple((nu, va) for nu in (0.10, 0.15) for va in (4.5, 5.0, 6.0))
RIDGE_NUS = (0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20)


def read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def point_key(nu: float, va: float) -> tuple[str, str]:
    return float(nu).hex(), float(va).hex()


def append_rows(path: Path, rows: list[dict]) -> list[dict]:
    existing = read_csv(path)
    merged = {point_key(float(row["nu_raw"]), float(row["VA"])): dict(row) for row in existing}
    for row in rows:
        merged[point_key(float(row["nu_raw"]), float(row["VA"]))] = row
    result = sorted(merged.values(), key=lambda row: (float(row["nu_raw"]), float(row["VA"])))
    write_csv(path, result)
    return result


def best(rows: list[dict]) -> dict | None:
    return max(rows, key=lambda row: float(row["SKR"])) if rows else None


def continuation_targets(stage: int, rows: list[dict]) -> list[tuple[float, float]]:
    if stage == 1:
        return list(PRIMARY)
    current = best([row for row in rows if float(row["nu_raw"]) > 0.0])
    if current is None:
        return []
    if stage == 2:
        # Stage 1 rose through VA=6; close the ridge at VA=6 and probe the
        # next requested outer branch at VA=8 before any further expansion.
        return [(nu, 6.0) for nu in RIDGE_NUS] + [(0.10, 8.0), (0.15, 8.0)]
    if stage == 3:
        # Coarse local bracket first: two VA sides around the ridge plus a
        # narrow nu stencil at VA=6.  Fine refinement follows only if this
        # bracket leaves a competitive tie.
        return (
            [(nu, va) for nu in (0.125, 0.15, 0.175) for va in (5.5, 6.0, 6.5)]
            + [(nu, 6.0) for nu in (0.14, 0.145, 0.155, 0.16)]
        )
    if stage == 4:
        return [(0.25, 5.5), (0.3, 5.5), (0.4, 5.5), (0.1, 0.025), (0.165, 0.025), (0.3, 0.025), (0.165, 8.0)]
    if stage == 5:
        return [(nu, 5.5) for nu in (0.16, 0.17, 0.18, 0.19)] + [(0.175, 5.25), (0.175, 5.75)]
    if stage == 6:
        return [(0.16, 5.4), (0.16, 5.6), (0.165, 5.4), (0.165, 5.5), (0.165, 5.6)]
    if stage == 7:
        return [(0.165, 5.55)]
    if stage == 8:
        return [
            (0.145, 5.5), (0.155, 5.3), (0.155, 5.7),
            (0.160, 5.3), (0.160, 5.7),
            (0.165, 5.3), (0.165, 5.7),
            (0.175, 5.3), (0.175, 5.7), (0.185, 5.5),
        ]
    if stage == 9:
        return [(nu, va) for nu in (0.5, 0.6, 0.8) for va in (5.0, 5.5, 6.0)]
    if stage == 10:
        return [(nu, va) for nu in (0.5, 0.6, 0.8) for va in (1.5, 3.0)]
    if stage == 11:
        return [(0.4, 3.0)]
    raise ValueError(stage)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, choices=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), default=1)
    parser.add_argument("--max-new-source-points", type=int, default=None)
    parser.add_argument("--source-workers", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config, freeze = load_frozen_config()
    audit, channel = channel_audit(config, freeze)
    identity = model_identity()
    previous = json.loads((output / "final_summary.json").read_text(encoding="utf-8"))
    if previous["model_identity"]["composite_sha256"] != identity["composite_sha256"]:
        raise RuntimeError("Continuation model hash does not match existing artifacts.")
    csv_path = output / "evaluated_points.csv"
    rows_before = read_csv(csv_path)
    targets = continuation_targets(args.stage, rows_before)
    evaluator = ExactMBEvaluator(config, channel, output, source_cache_dir=SOURCE_CACHE, allow_legacy_exact_import=False)
    missing_all = [point for point in targets if not cache_path(evaluator, config, *point).is_file()]
    missing = missing_all
    if args.max_new_source_points is not None:
        missing = missing[:max(0, args.max_new_source_points)]
    attempted = list(missing)
    if attempted:
        evaluator.prepare_sources(attempted, args.source_workers)
    rows_new = evaluate_points(config, channel, evaluator, targets)
    for row in rows_new:
        row["continuation_stage"] = args.stage
    rows_all = append_rows(csv_path, rows_new)
    exact_candidates = [{"scheme": "Uniform", **max((row for row in rows_all if float(row["nu_raw"]) == 0.0), key=lambda row: float(row["SKR"]))}] if any(float(row["nu_raw"]) == 0.0 for row in rows_all) else []
    exact_candidates += [{"scheme": "MB", **row} for row in distinct_best([row for row in rows_all if float(row["nu_raw"]) > 0.0])]
    write_csv(output / "exact_candidates.csv", exact_candidates)
    best_mb = best([row for row in rows_all if float(row["nu_raw"]) > 0.0])
    best_uniform = best([row for row in rows_all if float(row["nu_raw"]) == 0.0])
    continuation = {
        "status": "CONTINUATION_COMPLETE" if not missing_all else "CONTINUATION_INCOMPLETE",
        "stage": args.stage,
        "model_composite_sha256": identity["composite_sha256"],
        "targets": [{"nu_raw": nu, "V_A": va, "cached_before": (nu, va) not in missing_all} for nu, va in targets],
        "attempted_new_source_points": attempted,
        "remaining_missing_source_points": [list(point) for point in missing_all if point not in attempted],
        "new_exact_rows": len(rows_new),
        "total_exact_rows": len(rows_all),
        "best_uniform": best_uniform,
        "best_mb": best_mb,
        "ridge_direction": "UNRESOLVED_UNTIL_STAGE_1_EXACT_ROWS" if args.stage == 1 and len(rows_new) < len(targets) else "TO_BE_CLASSIFIED_FROM_EXACT_POINTS",
        "global_status": "GLOBAL_OPTIMUM_UNRESOLVED",
        "audit_status": audit["audit_status"],
    }
    (output / f"continuation_stage_{args.stage}.json").write_text(json.dumps(continuation, indent=2) + "\n", encoding="utf-8")
    (output / "continuation_latest.json").write_text(json.dumps(continuation, indent=2) + "\n", encoding="utf-8")
    if rows_new:
        write_csv(output / f"continuation_stage_{args.stage}_new_points.csv", rows_new)
        make_figures(output, rows_all, best_mb)
    print(json.dumps(continuation, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
