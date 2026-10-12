"""Exact-cache-only dependency inventory; no objective or source generation.

Stage 1 of the requested closure continuation. Expensive source execution
needs an explicit new wall-time budget; the expired pilot budget is not reused.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_convergence_validation as validation
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source

REFERENCE = ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun"
OUTPUT = ROOT / "results/theta10_D55_alt_opt_closure_continuation"
STAGNATED = (20., 21.9393102292, 22., 23., 24.)


def inventory(iterations, summary, ranked):
    """Map each missing request to its exact slice/iteration and source identity."""
    selected = {float(r["L_km"]): r for r in summary}
    identities = {(float(p["nu_raw"]).hex(), float(p["V_A"]).hex()): p for p in ranked}
    searches, dependencies = [], []
    for it in iterations:
        distance = float(it["distance_km"])
        best = selected[distance]
        final_selected = (it["start_id"] == best["selected_initialization"]
                          and int(it["iteration"]) == int(best["AO_iterations"]) - 1)
        for prefix, variable in (("V_A", "V_A"), ("nu", "nu_raw")):
            history = json.loads(it[prefix + "_candidate_history"])
            bracket = json.loads(it[prefix + "_bracket"])
            extent = json.loads(it[prefix + "_search_range"])
            winner = float(it["optimized_V_A"] if prefix == "V_A" else it["optimized_nu"])
            search_id = f"{distance.hex()}:{it['start_id']}:{it['iteration']}:{variable}"
            missing = [p for p in history if p["status"] == "EXACT_SOURCE_MISSING"]
            failures = [p for p in history if p["status"] == "NUMERICAL_FAILURE"]
            keys, sides = [], []
            for request_index, p in enumerate(missing):
                assert "K" not in p
                value = float(p["value"])
                nu, va = ((float(it["nu_before"]), value) if prefix == "V_A"
                          else (value, float(it["optimized_V_A"])))
                identity = identities[(nu.hex(), va.hex())]
                key = identity["raw_current_cache_key"]
                keys.append(key)
                direction = ("LOWER_BOUNDARY" if value < extent[0] else
                             "UPPER_BOUNDARY" if value > extent[1] else
                             "LOWER_BRACKET_REFINEMENT" if value < winner else
                             "UPPER_BRACKET_REFINEMENT" if value > winner else "INITIAL_SLICE_PROBE")
                sides.append(direction)
                essential = final_selected
                competitive = float(it["K_after_nu"]) >= float(best["K"]) - max(.002, .05 * abs(float(best["K"])))
                dependencies.append({
                    "source_cache_key": key, "canonical_source_cache_key": identity["canonical_source_cache_key"],
                    "ensemble_hash": identity["ensemble_hash"], "nu_raw": nu, "V_A": va,
                    "nu_raw_hex": nu.hex(), "V_A_hex": va.hex(), "search_id": search_id,
                    "L_km": distance, "start_id": it["start_id"], "iteration": int(it["iteration"]),
                    "variable": variable, "request_index_in_search": request_index, "direction": direction,
                    "source_status": "MISSING_EXACT_SOURCE", "essential_to_selected_terminal_search": essential,
                    "stagnated_distance": distance in STAGNATED,
                    "priority_class": ("STAGNATED_SELECTED_TERMINAL" if essential and distance in STAGNATED else
                                       "SELECTED_TERMINAL" if essential else "COMPETITIVE_TRAJECTORY" if competitive else
                                       "EXPLORATORY_NONCOMPETITIVE_BRANCH"),
                    "search_status": it[prefix + "_search_status"],
                    "boundary_status": it[prefix + "_boundary_status"],
                    "refinement_status": it[prefix + "_refinement_status"],
                    "exact_reason": p["error"], "K": None,
                    "scope": "STRICT_RERUN_HISTORY_DEPENDENCY_NOT_NEW_OBJECTIVE_CALL",
                })
            radius = (max(winner - bracket[0], bracket[1] - winner)
                      if None not in bracket else None)
            reasons = []
            if missing:
                reasons.append("MISSING_EXACT_SOURCE_FOR_" + ",".join(sorted(set(sides))))
            if it[prefix + "_boundary_status"] == "BOUNDARY_NOT_CLOSED":
                reasons.append("OUTER_DIRECTION_NOT_CLOSED_BY_EXACT_PROBE")
            if radius is not None and radius > ao.PARAMETER_TOLERANCE:
                reasons.append("LOCAL_BRACKET_RADIUS_EXCEEDS_PARAMETER_TOLERANCE")
            if failures:
                reasons.append("NUMERICAL_FAILURE")
            searches.append({
                "search_id": search_id, "L_km": distance, "start_id": it["start_id"],
                "iteration": int(it["iteration"]), "variable": variable,
                "fixed_value": float(it["nu_before"] if prefix == "V_A" else it["optimized_V_A"]),
                "winner_value": winner, "search_status": it[prefix + "_search_status"],
                "boundary_status": it[prefix + "_boundary_status"],
                "refinement_status": it[prefix + "_refinement_status"],
                "search_range": json.dumps(extent), "local_bracket": json.dumps(bracket),
                "local_bracket_radius": radius, "parameter_tolerance": ao.PARAMETER_TOLERANCE,
                "lower_local_side": "BRACKET_SIDE_PRESENT" if bracket[0] is not None else "OPEN",
                "upper_local_side": "BRACKET_SIDE_PRESENT" if bracket[1] is not None else "OPEN",
                "missing_source_requests": len(missing), "missing_source_keys": json.dumps(keys),
                "missing_directions": json.dumps(sides), "numerical_failures": len(failures),
                "essential_to_selected_terminal_search": final_selected,
                "numeric_local_completion": it[prefix + "_search_status"] == "NUMERICALLY_CLOSED_LOCAL_BRACKET",
                "global_continuous_certificate": "NOT_AVAILABLE",
                "exact_reason": ";".join(reasons) or it[prefix + "_search_status"],
                "execution": "HISTORICAL_EXACT_LOG_AUDITED_NO_NEW_COORDINATE_SEARCH",
            })
    for point in ranked:
        affected = [d for d in dependencies if d["source_cache_key"] == point["raw_current_cache_key"]]
        point["affected_coordinate_searches"] = len({d["search_id"] for d in affected})
        point["stagnated_selected_terminal_requests"] = sum(
            d["stagnated_distance"] and d["essential_to_selected_terminal_search"] for d in affected)
        point["essential_selected_terminal_requests"] = sum(d["essential_to_selected_terminal_search"] for d in affected)
        point["priority_classes"] = json.dumps(sorted({d["priority_class"] for d in affected}))
        point["directions"] = json.dumps(sorted({d["direction"] for d in affected}))
    ranked.sort(key=lambda p: (not bool(p["stagnated_selected_terminal_requests"]),
                              not bool(p["essential_selected_terminal_requests"]),
                              not bool(p["competitive_requests"]), -p["affected_coordinate_searches"],
                              -p["essential_selected_terminal_requests"], p["nu_raw"], p["V_A"]))
    for rank, point in enumerate(ranked, 1):
        point["priority_rank"] = rank
    ranks = {p["raw_current_cache_key"]: p["priority_rank"] for p in ranked}
    for d in dependencies:
        d["priority_rank"] = ranks[d["source_cache_key"]]
    return searches, dependencies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() and not args.resume:
        parser.error("Output exists: use --resume for the unchanged Stage-1 inventory")
    out.mkdir(parents=True, exist_ok=True)
    config = source.unconstrained_config()
    payloads = source.load_source_payloads(config)
    assert len(payloads) == 165
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            ao.MAX_BOUNDARY_EXPANSIONS, ao.MAX_REFINEMENT_STAGES) == (1e-8, 1e-6, 6, 3, 4)
    frozen = json.loads((REFERENCE / "input_manifest_after.json").read_text(encoding="utf-8"))
    for name, expected in frozen.items():
        if validation.digest(ROOT / name) != expected:
            raise ValueError("Strict-rerun protected input has changed: " + name)
    protected = {**frozen, **validation.raw_snapshot(list(REFERENCE.rglob("*")) + [Path(__file__)])}
    manifest_path = out / "protected_input_manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != protected:
            raise ValueError("Resume checkpoint input identity changed")
    else:
        validation.save_json(manifest_path, protected)
    ledger_path = out / "source_generation_ledger.json"
    if ledger_path.exists() and json.loads(ledger_path.read_text()).get("attempts"):
        raise ValueError("Source continuation already started; do not overwrite it with Stage-1 inventory")
    summary = validation.read_csv(REFERENCE / "mb_alt_opt_distance_summary.csv")
    iterations = validation.read_csv(REFERENCE / "ao_iterations.csv")
    # Identity construction only: source_moments/evaluate_candidate are not called.
    evaluator = ao.ExactMBEvaluator(config, {"T_eff": 0., "epsilon_base": .0186, "c_phi": 0.},
                                    out, source_cache_dir=source.SOURCE_CACHE, allow_legacy_exact_import=False)
    ranked = validation.priorities(config, evaluator, iterations, summary)
    searches, dependencies = inventory(iterations, summary, ranked)
    assert len(ranked) == 50 and len(dependencies) == 836 and len(searches) == 558
    assert sum(s["boundary_status"] == "BOUNDARY_NOT_CLOSED" for s in searches) == 280
    assert len({d["ensemble_hash"] for d in dependencies}) == 50
    for point in ranked:
        assert source.candidate_from_payload(config, payloads, "MB", point["nu_raw"], point["V_A"]) is None
    prior_pilot = json.loads((validation.OUTPUT / "validation_report.json").read_text(encoding="utf-8"))
    for point in ranked:
        point["previous_timeout"] = any(r["status"] == "TIMEOUT" and r["cache_key"] == point["raw_current_cache_key"]
                                       for r in prior_pilot["new_exact_source_failures"])
        point["generation_status"] = "NOT_RUN_AWAITING_EXPLICIT_COMPUTE_BUDGET"
    write = validation.write_csv
    write(out / "missing_source_dependency_map.csv", dependencies)
    write(out / "unresolved_search_inventory.csv", searches)
    write(out / "missing_source_priorities.csv", ranked)
    write(out / "ao_coordinate_search_status.csv", searches)
    write(out / "ao_boundary_closure_status.csv", searches)
    write(out / "ao_iteration_history.csv", [{**r, "execution": "LAST_KNOWN_STRICT_RERUN_LOG"} for r in iterations])
    results = []
    for r in summary:
        l = float(r["L_km"])
        missing_keys = sorted({d["source_cache_key"] for d in dependencies if d["L_km"] == l})
        results.append({**r, "execution": "LAST_KNOWN_STRICT_RERUN_NO_CONTINUATION_YET",
                        "continuation_status": "NOT_RUN_AWAITING_EXPLICIT_COMPUTE_BUDGET",
                        "numeric_convergence_verdict": "NOT_ESTABLISHED",
                        "missing_source_ensembles": len(missing_keys), "missing_source_keys": json.dumps(missing_keys)})
    write(out / "ao_26distance_results.csv", results)
    write(out / "previous_vs_continued_results.csv", [{"L_km": r["L_km"],
          "previous_nu": r["nu_raw_star"], "previous_V_A": r["V_A_star"], "previous_K": r["K"],
          "continued_nu": None, "continued_V_A": None, "continued_K": None, "delta_K": None,
          "execution": "NOT_RUN", "reason": "NEW_EXACT_SOURCE_EXECUTION_BUDGET_NOT_SPECIFIED"} for r in summary])
    write(out / "new_exact_source_moments.csv", [{"status": "NOT_RUN", "nu_raw": None, "V_A": None,
          "C": None, "w": None, "wall_seconds": None, "cpu_seconds": None,
          "reason": "NO_SOURCE_GENERATION_ATTEMPTED_NO_BUDGET_SPECIFIED"}])
    validation.save_json(ledger_path, {"status": "STAGE_1_COMPLETE_AWAITING_COMPUTE_BUDGET",
        "attempts": [], "completed_unique_ensembles": 0, "used_wall_seconds": 0,
        "total_compute_budget_seconds": None, "per_probe_timeout_seconds": None,
        "prior_pilot": {"path": str(validation.OUTPUT), "measured_wall_seconds": prior_pilot["source_compute_elapsed_seconds"],
                        "retry_requires_explicit_new_budget": True},
        "original_evaluator": "scripts/run_exact_mb_test2.py:ExactMBEvaluator.source_moments",
        "supervisor": "scripts/run_theta10_D55_alt_opt_convergence_validation.py:bounded_process",
        "batch_size": 1, "source_precision_ladder": ao.source_settings(config)["precision_ladder"],
        "checkpoint_input_manifest": manifest_path.name})
    tests = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                            "-p", "test_alt_opt_provenance_and_stopping.py", "-v"], cwd=ROOT, capture_output=True, text=True)
    (out / "regression_tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    preserved = all(validation.digest(ROOT / name) == value for name, value in protected.items())
    report = {
        "status": "STAGE_1_COMPLETE_SOURCE_CONTINUATION_NOT_RUN_BUDGET_REQUIRED", "scope": "DIAGNOSTIC_ONLY",
        "producer_sha256": validation.digest(__file__), "protected_files": len(protected),
        "provenance_verified_sources": len(payloads), "old_artifacts_preserved": preserved,
        "measured_inventory": {"missing_requests": len(dependencies), "unique_missing_ensembles": len(ranked),
            "unresolved_coordinate_invocations": len(searches),
            "unresolved_boundary_invocations": sum(s["boundary_status"] == "BOUNDARY_NOT_CLOSED" for s in searches)},
        "continuation_execution": "NOT_RUN", "new_exact_sources_completed": 0,
        "coordinate_searches_resolved_by_continuation": None, "boundary_searches_resolved_by_continuation": None,
        "after_metrics": None, "new_parameter_or_SKR_change_verdict": "NOT_RUN",
        "historical_status_counts": dict(Counter(r["status"] for r in summary)),
        "historically_numerically_converged_distances": 0,
        "priority_distances": list(STAGNATED), "top_probes": ranked[:8],
        "epsilon_opt": ao.K_TOLERANCE, "epsilon_param": ao.PARAMETER_TOLERANCE, "max_outer_iterations": ao.MAX_AO_ITERATIONS,
        "max_refinement_stages": ao.MAX_REFINEMENT_STAGES, "max_boundary_expansions": ao.MAX_BOUNDARY_EXPANSIONS,
        "verification": {"protected_model_security_source_optimizer_bytes": preserved, "exact_source_identity": True,
            "no_interpolation_no_new_evaluation": True, "checkpoint_resume_input_identity": True,
            "new_source_rows_validated": "NOT_RUN_NO_NEW_ROWS", "regression_tests": tests.returncode == 0,
            "git_diff_check": diff.returncode == 0},
        "limitations": ["Stages 2-8 require an explicit new source-generation budget; none was silently assumed.",
            "Stage-1 counts audit immutable histories, not a new AO replay or convergence verdict.",
            "Resolving one dependency does not necessarily resolve its coordinate search; further exact midpoints can be required.",
            "Four refinement stages and radius<=1e-6 are retained unchanged; no iteration/precision policy relaxed.",
            "Exact local brackets and decreasing tail samples cannot certify an unbounded global optimum.",
            "The historical frozen-spec hash discrepancy remains open; publication lifecycle is NOT_READY_FOR_PUBLICATION_SCALE_RUNS."],
    }
    validation.save_json(out / "convergence_report.json", report)
    md = ["# ALT_OPT closure continuation: Stage 1", "", report["status"], "",
          "Dependency inventory is complete; AP generation and all new coordinate searches are NOT_RUN.",
          "A new explicit total/per-probe hard budget is required before the expensive original evaluator is launched.",
          "Historical timeout is preserved; no invalid ensemble or inferior SKR is inferred from it.", "",
          "## Measured inventory", "", "836 missing requests -> 50 unique sources -> 558 coordinate invocations; 280 open boundary invocations.",
          "Each request links exact binary64 parameters, source hashes, slice, start, iteration, distance, direction and failure reason.", "",
          "## Source priority (five stagnated distances first)", "",
          "| Rank | nu | VA | Shared searches | Terminal stagnation requests | Distances |", "|---:|---:|---:|---:|---:|---|"]
    md += [f"| {p['priority_rank']} | {p['nu_raw']!r} | {p['V_A']!r} | {p['affected_coordinate_searches']} | {p['stagnated_selected_terminal_requests']} | {p['distances_km']} |" for p in ranked[:8]]
    md += ["", "## All 26 distances: LAST_KNOWN, NOT newly continued", "",
           "VA/nu search and boundary statuses below are from the strict rerun. No after metrics are inferred.", "",
           "| L | nu | VA | K | Delta K | VA search | nu search | Boundary (VA/nu) | Last-known final status |",
           "|---:|---:|---:|---:|---:|---|---|---|---|"]
    md += ["| " + " | ".join([r[k] for k in ("L_km", "nu_raw_star", "V_A_star", "K", "final_delta_K",
           "final_V_A_search_status", "final_nu_search_status")]) + f" | {r['final_V_A_boundary_status']}/{r['final_nu_boundary_status']} | {r['status']} |" for r in results]
    md += ["", "## Before / after", "", "| Metric | Before (verified strict rerun) | After continuation |", "|---|---:|---|"]
    md += [f"| {name} | {value} | NOT_RUN |" for name, value in (
        ("Missing source requests", 836), ("Unique missing ensembles", 50), ("Unresolved inner directions", 558),
        ("Unresolved boundary directions", 280), ("Catalog stagnation distances", 5),
        ("Unresolved boundary distances", 21), ("Numerically converged distances", 0))]
    md += ["", "## Verification", ""] + [f"- {k}: {v}" for k, v in report["verification"].items()]
    md += ["", "## Remaining limitations", ""] + ["- " + s for s in report["limitations"]]
    (out / "convergence_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "measured_inventory", "historical_status_counts", "protected_files", "verification")}, indent=2))
    return 0 if preserved and tests.returncode == 0 and diff.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
