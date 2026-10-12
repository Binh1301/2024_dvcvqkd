"""Audit persisted continuation artifacts only; never run scientific evaluators."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_unconstrained_three_scheme as source
from scripts import run_theta10_D55_alt_opt_convergence_validation as io


def read(name):
    with Path(name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def search_key(row):
    distance = row.get("L_km", row.get("distance_km"))
    fixed = row.get("fixed_value")
    return (float(distance).hex(), row["start_id"], str(row["iteration"]), row["variable"],
            None if fixed is None else float(fixed).hex())


ledger = json.loads((OUT / "source_generation_ledger.json").read_text())
if "controller_finished_utc" not in ledger:
    raise SystemExit("Controller still active: final artifact audit refuses to run early")
manifest = json.loads((OUT / "protected_input_manifest.json").read_text())
for name, expected in manifest.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
executed = OUT / "script_snapshots/run_theta10_D55_alt_opt_closure_continuation_executed.py"
assert io.digest(executed) == ledger["producer_sha256"]
config = source.unconstrained_config()
base = source.load_source_payloads(config)
payloads = source.load_source_payloads(config, (source.SOURCE_CACHE, OUT / "exact_source_cache"))
new_hashes = set(payloads) - set(base)
for row in ledger["attempts"]:
    assert row["status"] != "RUNNING"
    assert row["wall_seconds"] <= row["timeout_seconds"] + 2
    assert row["supervision"]["cpu_measurement"] == "WINDOWS_JOB_BASIC_ACCOUNTING"
    if row["status"] == "COMPLETED_EXACT":
        assert row["source_payload_verified"]
        payload = json.loads((OUT / "exact_source_cache" / (row["cache_key"] + ".json")).read_text())
        assert payload["ensemble_hash"] in new_hashes
        assert float(payload["C"]) == row["C"] and float(payload["w"]) == row["w"]
report = json.loads((OUT / "convergence_report.json").read_text())
old = read(ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun/mb_alt_opt_distance_summary.csv")
old_searches = read(OUT / "unresolved_search_inventory.csv")
dependencies = read(OUT / "missing_source_dependency_map.csv")
adaptive_dependencies = read(OUT / "current_missing_source_dependency_map.csv")
for name in ("missing_source_dependency_map.csv", "unresolved_search_inventory.csv",
             "new_exact_source_moments.csv", "source_generation_ledger.json",
             "ao_coordinate_search_status.csv", "ao_boundary_closure_status.csv",
             "ao_iteration_history.csv", "ao_26distance_results.csv",
             "previous_vs_continued_results.csv", "convergence_report.md", "convergence_report.json"):
    assert (OUT / name).is_file(), name
latest = {}
for path in sorted((OUT / "coordinate_batches").glob("batch_*/batch_results.json"),
                   key=lambda p: int(p.parent.name.split("_")[1])):
    data = json.loads(path.read_text())
    for r in data["records"]:
        latest[float(r["L_km"])] = (r, data, path.parent.name)
results, resolutions = [], []
old_keys = {search_key(r): r for r in old_searches}
for r in old:
    l = float(r["L_km"])
    row = dict(r)
    if l in latest:
        current, data, batch = latest[l]
        # Preserve old diagnostics under explicit lineage, never relabel them fresh.
        diagnostic_fields = ("aggregate_search_status", "best_run_status", "cache_hits", "initial_V_A", "initial_nu",
            "missing_exact_source_probes", "monotonicity_violations", "numerical_failures", "requested_objective_calls",
            "selected_initialization", "unique_exact_SKR_evaluations", "unresolved_boundary_directions",
            "unresolved_inner_search_directions", "warm_start_used")
        for field in diagnostic_fields:
            row["previous_" + field] = row.pop(field, None)
        row.update(current)
        row["execution"] = "CONTINUED_EXACT_" + batch
        row["AO_iterations"] = current["outer_iterations"]
        row["selected_initialization"] = current["selected_start"]
        row["cache_hits"] = current["objective_cache_hits"]
        row["missing_exact_source_probes"] = current["missing_source_attempts"]
        row["unique_exact_SKR_evaluations"] = current["new_exact_objective_evaluations"]
        row["unresolved_inner_search_directions"] = current["unresolved_coordinate_invocations"]
        row["unresolved_boundary_directions"] = current["unresolved_boundary_invocations"]
        runs = [run for run in data["runs"] if run["L_km"] == l]
        final_pairs = {(float(run["final_nu"]).hex(), float(run["final_V_A"]).hex())
                       for run in runs if run["K"] is not None}
        row["multi_start_same_candidate"] = len(final_pairs) == 1
        row["multi_start_final_pairs"] = json.dumps(sorted(final_pairs))
        postchecks = [b for b in data["boundaries"] if b["L_km"] == l and b["start_id"] == "final_pair_verification"]
        for b in postchecks:
            prefix = "V_A" if b["variable"] == "V_A" else "nu"
            row["final_" + prefix + "_boundary_status"] = b["boundary_status"]
            row["final_" + prefix + "_refinement_status"] = b["refinement_status"]
        # Only compare genuinely identical historical slices/invocations.
        for it in data["iterations"]:
            if it["distance_km"] != l:
                continue
            for prefix, variable in (("V_A", "V_A"), ("nu", "nu_raw")):
                key = (l.hex(), it["start_id"], str(it["iteration"]), variable,
                       float(it["nu_before"] if prefix == "V_A" else it["optimized_V_A"]).hex())
                previous = old_keys.get(key)
                if previous:
                    resolutions.append({"L_km": l, "start_id": it["start_id"], "iteration": it["iteration"],
                        "variable": variable, "same_slice_verified": True,
                        "previous_search_status": previous["search_status"], "new_search_status": it[prefix + "_search_status"],
                        "previous_boundary_status": previous["boundary_status"], "new_boundary_status": it[prefix + "_boundary_status"],
                        "coordinate_resolved": it[prefix + "_search_status"] == "NUMERICALLY_CLOSED_LOCAL_BRACKET",
                        "boundary_resolved": previous["boundary_status"] == "BOUNDARY_NOT_CLOSED"
                                             and it[prefix + "_boundary_status"] != "BOUNDARY_NOT_CLOSED"})
    else:
        row["execution"] = "LAST_KNOWN_STRICT_RERUN_NOT_CONTINUED"
    row["selection_claim"] = "BEST_EXACT_TESTED_CANDIDATE_ONLY"
    row["numeric_convergence_verdict"] = "NOT_ESTABLISHED" if row["status"] != "CONVERGED_NUMERICALLY" else "CONVERGED_NUMERICALLY"
    row["condition_A_VA_search_complete"] = row["final_V_A_search_status"] == "NUMERICALLY_CLOSED_LOCAL_BRACKET"
    row["condition_B_nu_search_complete"] = row["final_nu_search_status"] == "NUMERICALLY_CLOSED_LOCAL_BRACKET"
    row["condition_C_scalar_epsilon_satisfied"] = abs(float(row["final_delta_K"])) <= 1e-8
    row["condition_D_no_invalidating_unresolved_search"] = row["status"] == "CONVERGED_NUMERICALLY"
    row["condition_E_cap_not_premature"] = row["status"] != "MAX_ITERATIONS_REACHED"
    missing_keys = {d["source_cache_key"] for d in dependencies + adaptive_dependencies
                    if float(d["L_km"]) == l and d["ensemble_hash"] not in payloads}
    row["missing_source_ensembles"] = len(missing_keys)
    row["missing_source_keys"] = json.dumps(sorted(missing_keys))
    row["missing_source_count_scope"] = "HISTORICAL_PLUS_LATEST_ADAPTIVE_REQUESTS_CURRENT_SOURCE_AVAILABILITY"
    if row["status"] == "CONVERGED_NUMERICALLY":
        assert all(row["condition_" + letter + suffix] for letter, suffix in (
            ("A", "_VA_search_complete"), ("B", "_nu_search_complete"), ("C", "_scalar_epsilon_satisfied"),
            ("D", "_no_invalidating_unresolved_search"), ("E", "_cap_not_premature")))
    for key in ("I_AB", "beta_I_AB", "chi_BE", "K"):
        row[key] = float(row[key])
    assert row["beta_I_AB"] == .95 * row["I_AB"]
    assert row["K"] == row["beta_I_AB"] - row["chi_BE"]
    results.append(row)
remaining = [d for d in dependencies if d["ensemble_hash"] not in payloads]
original_missing_hashes = {d["ensemble_hash"] for d in remaining}
adaptive_missing_hashes = {d["ensemble_hash"] for d in adaptive_dependencies if d["ensemble_hash"] not in payloads}
all_missing_hashes = original_missing_hashes | adaptive_missing_hashes
for d in dependencies:
    d["source_availability_after"] = "VALIDATED_EXACT_AVAILABLE" if d["ensemble_hash"] in payloads else "EXACT_SOURCE_STILL_MISSING"
io.write_csv(OUT / "missing_source_dependency_map_after.csv", dependencies)
io.write_csv(OUT / "same_slice_resolution_comparison.csv", resolutions)
io.write_csv(OUT / "ao_26distance_results.csv", results)
metrics = [
    {"metric": "Missing historical dependency requests without exact source", "before": 836, "after": len(remaining), "scope": "SOURCE_AVAILABILITY_NOT_NEW_OBJECTIVE_CALLS"},
    {"metric": "Original unique missing ensembles", "before": 50, "after": len({d["ensemble_hash"] for d in remaining}), "scope": "ORIGINAL_50_ONLY"},
    {"metric": "Unique missing ensembles including newly requested adaptive probes", "before": 50, "after": len(all_missing_hashes), "scope": "ORIGINAL_PLUS_CURRENT_ADAPTIVE_DEPENDENCIES"},
    {"metric": "Unresolved inner invocations", "before": 558, "after": "NOT_FULL_26_RERUN", "scope": "See current executed subgroup and same-slice comparison"},
    {"metric": "Unresolved boundary invocations", "before": 280, "after": "NOT_FULL_26_RERUN", "scope": "Do not mix cumulative batch/postcheck counts with old counts"},
    {"metric": "Catalog stagnation distances", "before": 5, "after": sum(r["status"] == "STAGNATED_IN_EXACT_CATALOG" for r in results), "scope": "UPDATED_5_PLUS_LAST_KNOWN_21"},
    {"metric": "Unresolved boundary distances", "before": 21, "after": sum(r["status"] == "UNRESOLVED_BOUNDARY" for r in results), "scope": "UPDATED_5_PLUS_LAST_KNOWN_21"},
    {"metric": "Newly numerically converged distances", "before": 0, "after": sum(r["status"] == "CONVERGED_NUMERICALLY" for r in results if float(r["L_km"]) in latest), "scope": "ACTUALLY_EXECUTED_CONTINUATION"},
]
io.write_csv(OUT / "before_after_metrics.csv", metrics)
report.update(status=ledger["status"], final_audit_status="CURRENTLY_VERIFIED_PASS", final_controller_status=ledger["status"],
    results=results, before_after_metrics=metrics, status_counts_with_execution_scope=dict(Counter(r["status"] for r in results)),
    source_ensembles_completed_total=len(new_hashes), source_ensembles_completed_original_50=len(new_hashes & {d["ensemble_hash"] for d in dependencies}),
    remaining_unique_including_adaptive=len(all_missing_hashes),
    newly_requested_missing_ensembles=len(adaptive_missing_hashes - original_missing_hashes),
    newly_resolved_same_slice_coordinate_invocations=sum(r["coordinate_resolved"] for r in resolutions),
    newly_resolved_same_slice_boundary_invocations=sum(r["boundary_resolved"] for r in resolutions),
    same_slice_comparisons=len(resolutions), all_new_rows_validated=True,
    checkpoint_artifacts_verified=True, source_method_security_physical_files_unchanged=True,
    unbounded_global_certificate="NOT_AVAILABLE", after_full26_fresh_status="NOT_RUN_REPRESENTATIVE_GATE_FAILED")
io.save_json(OUT / "convergence_report.json", report)
md = ["# Exact ALT_OPT closure continuation — final stored-artifact audit", "",
    f"Controller: {ledger['status']}; scope DIAGNOSTIC_ONLY.",
    f"Exact sources completed: {len(new_hashes)} total; {report['source_ensembles_completed_original_50']}/50 original dependencies.",
    f"Missing unique ensembles: {len(original_missing_hashes)} original plus {len(adaptive_missing_hashes - original_missing_hashes)} newly requested adaptive ensembles = {len(all_missing_hashes)} known remaining.",
    f"Same-slice coordinate/boundary invocations resolved: {report['newly_resolved_same_slice_coordinate_invocations']}/{report['newly_resolved_same_slice_boundary_invocations']}.",
    "Epsilon_opt=1e-8; epsilon_param=1e-6; outer cap=6; source precision ladder 1050/1250/1450 unchanged.",
    f"Protected files verified: {len(manifest)}; all newly completed source rows verified.",
    "Updated rows are labeled CONTINUED_EXACT; other 21 are LAST_KNOWN, not fresh optimization.", "",
    "| L (km) | nu | VA | K | Delta K | VA search | nu search | Boundary (VA/nu) | Final status | Execution |",
    "|---:|---:|---:|---:|---:|---|---|---|---|---|"]
md += ["| " + " | ".join(str(r.get(k, "NOT_RUN")) for k in
       ("L_km", "nu_raw_star", "V_A_star", "K", "final_delta_K", "final_V_A_search_status", "final_nu_search_status"))
       + f" | {r['final_V_A_boundary_status']}/{r['final_nu_boundary_status']} | {r['status']} | {r['execution']} |" for r in results]
md += ["", "## Before / after with explicit execution scopes", "",
       "| Metric | Before | After | Scope |", "|---|---:|---|---|"]
md += [f"| {m['metric']} | {m['before']} | {m['after']} | {m['scope']} |" for m in metrics]
md += ["", "## Exact-source batches", "", "| nu | VA | Status | Wall (s) | Job CPU (s) |", "|---:|---:|---|---:|---:|"]
md += [f"| {r['nu_raw']} | {r['V_A']} | {r['status']} | {r['wall_seconds']} | {r.get('cpu_seconds')} |" for r in ledger["attempts"]]
md += ["", "No missing source gets K=0 or any inferior score. No interpolation or alternate method was used.",
       "Incomplete two-sided brackets, remaining exact-source requests and unresolved trajectories prevent numerical convergence.",
       "Finite exact local brackets cannot certify a global optimum on the unbounded positive domain; no analytic certificate is supplied.",
       "Timeouts are computational limits, not evidence of invalid ensembles. Further runtime is unknown and must be explicitly authorized.",
       "Historical frozen-spec hash discrepancy remains open; publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.",
       f"Regression tests PASS={report['regression_tests_pass']}; git diff --check PASS={report['git_diff_check_pass']}."]
(OUT / "convergence_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("final_audit_status", "source_ensembles_completed_total",
    "source_ensembles_completed_original_50", "newly_resolved_same_slice_coordinate_invocations", "newly_resolved_same_slice_boundary_invocations")}, indent=2))
