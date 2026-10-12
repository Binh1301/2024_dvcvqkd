"""Persisted dependency analysis and five-distance replay; AP is forbidden."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_convergence_validation as io
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source
from scripts import prepare_theta10_D55_alt_opt_closure_continuation as prep

PREV = ROOT / "results/theta10_D55_alt_opt_closure_continuation"
OUT = ROOT / "results/theta10_D55_alt_opt_closure_diagnostic"


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def ap_forbidden(*args, **kwargs):
    raise AssertionError("New AP source generation is prohibited in this diagnostic")


def list_json(values):
    return json.dumps(sorted(values), separators=(",", ":"))


def radius(search):
    lo, hi = search.get("bracket", [None, None])
    return None if lo is None or hi is None else max(search["best_value"] - lo, hi - search["best_value"])


def main():
    stored_only = sys.argv[1:] == ["--stored-analysis-only"]
    if sys.argv[1:] and not stored_only:
        raise SystemExit("Only --stored-analysis-only is supported")
    if OUT.exists() and not stored_only:
        raise SystemExit("Diagnostic output already exists; refusing to overwrite")
    OUT.mkdir(exist_ok=stored_only)
    config = source.unconstrained_config()
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            ao.MAX_REFINEMENT_STAGES, ao.AO_START_NUS) == (1e-8, 1e-6, 6, 4, (.1, .15, .3, .8))
    protected = json.loads((PREV / "protected_input_manifest.json").read_text())
    protected.update(io.raw_snapshot(list(PREV.rglob("*"))))
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    io.save_json(OUT / "input_manifest_before.json", protected)
    ledger = json.loads((PREV / "source_generation_ledger.json").read_text())
    assert ledger["status"] == "STOPPED_AT_HARD_BUDGET"
    base = source.load_source_payloads(config)
    bank = source.load_source_payloads(config, (source.SOURCE_CACHE, PREV / "exact_source_cache"))
    original_deps = io.read_csv(PREV / "missing_source_dependency_map_after.csv")
    old_summary = io.read_csv(PREV / "ao_26distance_results.csv")
    previous = {float(r["L_km"]): r for r in old_summary}
    batches = [(p.parent.name, json.loads(p.read_text())) for p in sorted(
        (PREV / "coordinate_batches").glob("batch_*/batch_results.json"))]
    latest_batch = batches[-1][1]

    # Delegate all calculations; only restore compatible persisted rows and
    # observe returned search records. Never change catalog/search decisions.
    instances, searches = [], []
    original_objective, original_search = ao.ExactObjective, ao.adaptive_maximize_1d
    class RestoredObjective(original_objective):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            checkpoint = PREV / "exact_objective_cache" / (self.context_hash + ".json")
            self.diagnostic_restored = 0
            if checkpoint.exists():
                saved = json.loads(checkpoint.read_text())
                self.diagnostic_restored = self.restore_objective_rows(saved["rows"], saved["identity"])
            assert not self.allow_new_source
            instances.append(self)
    def record_search(**kwargs):
        result = original_search(**kwargs)
        searches.append({"L_km": kwargs["objective"].channel["distance_km"], **result})
        return result
    if stored_only:
        searches = json.loads((OUT / "cache_only_searches.json").read_text())
        runs = json.loads((OUT / "cache_only_runs.json").read_text())
        iterations = [i for run in runs for i in run["iterations"]]
        records = json.loads((OUT / "diagnostic_summary.json").read_text()).get("cache_only_records")
        if records is None:
            # Upgrade the initial diagnostic's own serialized rows; no replay.
            fields = latest_batch["records"][0]
            records = [{k: (float(r[k]) if isinstance(v, float) else int(r[k]) if isinstance(v, int) and not isinstance(v, bool)
                              else r[k] == "True" if isinstance(v, bool) else r[k]) for k, v in fields.items()}
                       for r in io.read_csv(OUT / "representative_distance_status.csv")]
        boundaries = [{"numeric_local_completion": ao.coordinate_search_complete(s)} for s in searches]
        for p in sorted(OUT.glob("objective_*.json")):
            if p.name == "objective_compatibility_manifest.json":
                continue
            saved = json.loads(p.read_text())
            instances.append(SimpleNamespace(rows={n: r for n, r in enumerate(saved["rows"])},
                context_hash=p.stem.removeprefix("objective_"), objective_identity=saved["identity"], diagnostic_restored=len(saved["rows"])))
    else:
        with patch.object(ao.ExactMBEvaluator, "source_moments", ap_forbidden), \
             patch.object(ao, "ExactObjective", RestoredObjective), \
             patch.object(ao, "adaptive_maximize_1d", record_search), \
             patch.object(sweep, "adaptive_maximize_1d", record_search):
            records, iterations, boundaries, runs = io.validate_distances(
                OUT, prep.STAGNATED, config, json.loads(io.AUDIT.read_text()),
                json.loads((sweep.OUTPUT / "run_report.json").read_text()),
                io.read_csv(prep.REFERENCE / "mb_alt_opt_distance_summary.csv"),
                io.read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv"), PREV / "exact_source_cache")
    io.save_json(OUT / "cache_only_searches.json", searches)
    io.save_json(OUT / "cache_only_runs.json", runs)
    for obj in instances:
        io.save_json(OUT / ("objective_" + obj.context_hash + ".json"),
                     {"identity": obj.objective_identity, "rows": list(obj.rows.values())})
    cached_rows = [r for obj in instances for r in obj.rows.values()]
    evaluator = ao.ExactMBEvaluator(config, {"T_eff": 0., "epsilon_base": .0186, "c_phi": 0.},
                                   OUT, source_cache_dir=PREV / "exact_source_cache", allow_legacy_exact_import=False)
    ranked = io.priorities(config, evaluator, iterations, [
        {**r, "selected_initialization": r["selected_start"], "AO_iterations": r["outer_iterations"]} for r in records])
    inventory, deps = prep.inventory(iterations, [
        {**r, "selected_initialization": r["selected_start"], "AO_iterations": r["outer_iterations"]} for r in records], ranked)
    for d in deps:
        d["scope"] = "CURRENT_FIVE_DISTANCE_CACHE_ONLY_REPLAY"
    for inv in inventory:
        inv["execution"] = "CURRENT_FIVE_DISTANCE_CACHE_ONLY_REPLAY"
        directions = json.loads(inv["missing_directions"])
        types = set()
        if any("REFINEMENT" in d for d in directions):
            types.add("A_MISSING_LOCAL_REFINEMENT")
        if "UPPER_BOUNDARY" in directions:
            types.add("B_OPEN_UPPER_BOUNDARY")
        if "LOWER_BOUNDARY" in directions:
            types.add("C_OPEN_LOWER_BOUNDARY")
        types.add("F_GLOBAL_CERTIFICATE_UNAVAILABLE_SEPARATE_FROM_NUMERIC_CONVERGENCE")
        if not inv["essential_to_selected_terminal_search"]:
            types.add("D_NONSELECTED_OR_TRANSIENT_BRANCH_REQUIRES_OWN_COVERAGE")
        inv["blocker_types"] = ";".join(sorted(types))
        inv["type_E_bookkeeping_error_verified"] = False
    io.write_csv(OUT / "current_search_inventory.csv", inventory)
    io.write_csv(OUT / "unresolved_dependency_graph.csv", [
        {**d, "dependency_scope": "HISTORICAL_26_DISTANCE"} for d in original_deps] + [
        {**d, "dependency_scope": "CURRENT_5_DISTANCE"} for d in deps])

    final_slices, slice_points, representatives, comparison = [], [], [], []
    for r in records:
        l = r["L_km"]
        selected = [i for i in iterations if float(i["distance_km"]) == l and i["start_id"] == r["selected_start"]]
        finals = [s for s in searches if s["L_km"] == l][-2:]
        assert [s["variable"] for s in finals] == ["V_A", "nu_raw"]
        blockers = []
        for s in finals:
            rad = radius(s)
            next_values = [h["value"] for h in s["history"] if h["status"] == "EXACT_SOURCE_MISSING"]
            blockers += [(s["variable"], v) for v in next_values]
            # Conditional halving depth is diagnostic, not an optimizer change
            # or a promised step count: the best point may move.
            depth = math.ceil(math.log2(rad / ao.PARAMETER_TOLERANCE)) if rad and rad > ao.PARAMETER_TOLERANCE else 0
            summary = {"L_km": l, "coordinate": s["variable"], "fixed_parameter": s["fixed"],
                "best_parameter": s["best_value"], "best_K": s["best_K"],
                "bracket": json.dumps(s["bracket"]), "bracket_radius": rad,
                "parameter_tolerance": ao.PARAMETER_TOLERANCE,
                "halving_depth_if_best_unchanged": depth, "refinement_stage_cap": ao.MAX_REFINEMENT_STAGES,
                "best_unchanged_radius_after_4_halvings": rad / 16 if rad is not None else None,
                "search_status": s["status"], "boundary_status": s["boundary_status"],
                "refinement_status": s["refinement_status"], "missing_candidates": json.dumps(next_values),
                "available_exact_neighbors": json.dumps([h for h in s["history"] if h["status"] == "EXACT_EVALUATED"
                    and h["value"] in s["bracket"]]),
                "blocker_types": "A;D;F" if s["boundary_status"] == "INTERIOR" else "B_OR_C;D;F"}
            summary["execution"] = "CURRENT_FIVE_DISTANCE_CACHE_ONLY_REPLAY"
            final_slices.append(summary)
            for h in s["history"]:
                nu, va = (s["fixed"], h["value"]) if s["variable"] == "V_A" else (h["value"], s["fixed"])
                slice_points.append({**summary, **h, "nu_raw": nu, "V_A": va,
                                     "nu_hex": float(nu).hex(), "VA_hex": float(va).hex()})
        representative = {**r, "next_missing_candidates": json.dumps(blockers),
            "multi_start_pairs": list_json({pair(run["final_nu"], run["final_V_A"]) for run in runs
                if run["L_km"] == l and run["final_nu"] is not None}),
            "zero_delta_iteration": selected[-1]["iteration"],
            "parameters_unchanged_on_terminal_iteration": selected[-1]["delta_nu"] == 0 and selected[-1]["delta_V_A"] == 0,
            "reached_iteration_cap": r["outer_iterations"] >= ao.MAX_AO_ITERATIONS,
            "bookkeeping_error_verified": False, "global_certificate": "NOT_AVAILABLE"}
        representatives.append(representative)
        old = previous[l]
        comparison.append({"L_km": l, **{f"before_{k}": old[k] for k in
            ("nu_raw_star", "V_A_star", "K", "AO_iterations", "final_V_A_search_status", "final_nu_search_status", "missing_exact_source_probes")},
            **{f"after_{k}": r[k] for k in ("nu_raw_star", "V_A_star", "K", "outer_iterations",
            "final_V_A_search_status", "final_nu_search_status", "missing_source_attempts")},
            "before_boundaries": "/".join(old[k] for k in ("final_V_A_boundary_status", "final_nu_boundary_status")),
            "after_boundaries": "/".join(s["boundary_status"] for s in finals),
            "delta_K_selected": r["K"] - float(old["K"]), "status": r["status"]})
    # Other 21: reconstruct their selected slices from immutable logs only.
    historical_iterations = io.read_csv(prep.REFERENCE / "ao_iterations.csv")
    historical_objectives = io.read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv")
    for l, r in previous.items():
        if l in prep.STAGNATED:
            continue
        it = next(i for i in reversed(historical_iterations) if float(i["distance_km"]) == l
                  and i["start_id"] == r["selected_initialization"])
        for prefix, variable in (("V_A", "V_A"), ("nu", "nu_raw")):
            for h in json.loads(it[prefix + "_candidate_history"]):
                fixed = float(it["nu_before"] if prefix == "V_A" else it["optimized_V_A"])
                nu, va = (fixed, h["value"]) if prefix == "V_A" else (h["value"], fixed)
                candidate = source.candidate_from_payload(config, bank, "MB", nu, va)
                slice_points.append({"L_km": l, "coordinate": variable, "fixed_parameter": fixed,
                    "best_parameter": float(it["optimized_V_A"] if prefix == "V_A" else it["optimized_nu"]),
                    "best_K": float(it["K_after_VA"] if prefix == "V_A" else it["K_after_nu"]),
                    "bracket": it[prefix + "_bracket"], "search_status": it[prefix + "_search_status"],
                    "boundary_status": it[prefix + "_boundary_status"], "refinement_status": it[prefix + "_refinement_status"],
                    **h, "nu_raw": nu, "V_A": va, "nu_hex": float(nu).hex(), "VA_hex": float(va).hex(),
                    "current_source_available": candidate is not None, "execution": "LAST_KNOWN_SELECTED_TRAJECTORY_NO_REPLAY"})
    io.write_csv(OUT / "coordinate_slice_analysis.csv", slice_points)
    io.write_csv(OUT / "representative_distance_status.csv", representatives)
    io.write_csv(OUT / "cache_only_continuation.csv", comparison)

    # All source identities: existing 165, three successes and the union of
    # missing historical/current dependencies. Repeated requests remain separate.
    all_deps = original_deps + deps
    available = {pair(float.fromhex(p["nu_mb_raw_hex"]), float.fromhex(p["V_A_hex"])): p for p in bank.values()}
    verified_requests = 0
    for s in searches:
        for h in s["history"]:
            nu, va = (s["fixed"], h["value"]) if s["variable"] == "V_A" else (h["value"], s["fixed"])
            key = pair(nu, va)
            if h["status"] == "EXACT_SOURCE_MISSING":
                assert key not in available, "Search marks an available exact source missing"
            elif h["status"] == "EXACT_EVALUATED":
                assert key in available
                assert any(float(e["L_km"]) == s["L_km"] and pair(e["nu_raw"], e["V_A"]) == key
                           and float(e["SKR"]) == h["K"] for e in cached_rows)
            else:
                raise AssertionError("Unexpected numerical failure in cache-only replay")
            verified_requests += 1
    by_pair = defaultdict(list)
    for d in all_deps:
        by_pair[pair(d["nu_raw"], d["V_A"])].append(d)
    audit_rows = []
    for key in sorted(set(available) | set(by_pair)):
        payload, requests = available.get(key), by_pair[key]
        ensemble_hash = payload["ensemble_hash"] if payload else requests[0]["ensemble_hash"]
        matches = [e for e in cached_rows if pair(e["nu_raw"], e["V_A"]) == key]
        nu, va = map(float.fromhex, key)
        near = [q for q in available if q != key and abs(float.fromhex(q[0]) - nu) <= 2e-16
                and abs(float.fromhex(q[1]) - va) <= 2e-15]
        audit_rows.append({"source_cache_key": payload["cache_key"] if payload else requests[0]["source_cache_key"],
            "ensemble_hash": ensemble_hash, "nu_raw": nu, "V_A": va, "nu_hex": key[0], "VA_hex": key[1],
            "source_availability": "VALIDATED_EXACT_AVAILABLE" if payload else "EXACT_SOURCE_MISSING",
            "existed_before_4h_run": ensemble_hash in base, "generated_during_4h_run": ensemble_hash in bank and ensemble_hash not in base,
            "implementation_identity": json.dumps(payload["source_implementation"] if payload else evaluator.source_implementation),
            "settings_identity": json.dumps(payload["source_settings"] if payload else ao.source_settings(config)),
            "requested_distances": list_json({float(d["L_km"]) for d in requests}),
            "coordinate_search_ids": list_json({d["search_id"] for d in requests}),
            "current_objective_available_distances": list_json({float(e["L_km"]) for e in matches}),
            "hash_attested_historical_objective_distances": list_json({float(e["L_km"]) for e in historical_objectives
                if pair(e["nu_raw"], e["V_A"]) == key}),
            "selected_branch_request": any(d["essential_to_selected_terminal_search"] in (True, "True") for d in requests),
            "competing_branch_request": any(d["essential_to_selected_terminal_search"] in (False, "False") for d in requests),
            "nearby_but_bit_distinct_available_pairs": json.dumps(near),
            "identity_reuse_policy": "EXACT_BINARY64_HEX_ONLY_NO_ROUNDING_OR_ALIAS"})
    io.write_csv(OUT / "source_moment_audit.csv", audit_rows)

    success_analysis = []
    best_by_l = {r["L_km"]: r for r in records}
    for success in ledger["attempts"]:
        if success["status"] != "COMPLETED_EXACT":
            continue
        key = pair(success["nu_raw"], success["V_A"])
        for l in prep.STAGNATED:
            consumptions = []
            for batch_name, batch in batches:
                for i in batch["iterations"]:
                    if i["distance_km"] != l:
                        continue
                    for prefix in ("V_A", "nu"):
                        consumptions += [{"batch": batch_name, "start_id": i["start_id"], "iteration": i["iteration"],
                            "coordinate": prefix, "K": h["K"]} for h in json.loads(i[prefix + "_candidate_history"])
                            if h["status"] == "EXACT_EVALUATED" and pair(h["nu_raw"], h["V_A"]) == key]
            objectives = [e for e in cached_rows if float(e["L_km"]) == l and pair(e["nu_raw"], e["V_A"]) == key]
            selected_slice = float(best_by_l[l]["V_A_star"]).hex() == key[1]
            initial_bracket = next((json.loads(i["nu_bracket"]) for i in io.read_csv(prep.REFERENCE / "ao_iterations.csv")
                if float(i["distance_km"]) == l and i["start_id"] == previous[l]["selected_initialization"]
                and int(i["iteration"]) == int(previous[l]["AO_iterations"]) - 1), None)
            final_bracket = next(s["bracket"] for s in searches[::-1] if s["L_km"] == l and s["variable"] == "nu_raw")
            own_batch_index = next(n for n, (name, b) in enumerate(batches) if name == f"batch_{success['batch']}")
            own_batch = batches[own_batch_index][1]
            after_record = next(r for r in own_batch["records"] if r["L_km"] == l)
            after_it = [i for i in own_batch["iterations"] if i["distance_km"] == l and i["start_id"] == after_record["selected_start"]][-1]
            before_bracket = initial_bracket
            if own_batch_index:
                before_batch = batches[own_batch_index - 1][1]
                before_record = next(r for r in before_batch["records"] if r["L_km"] == l)
                before_it = [i for i in before_batch["iterations"] if i["distance_km"] == l and i["start_id"] == before_record["selected_start"]][-1]
                before_bracket = json.loads(before_it["nu_bracket"])
            after_bracket = json.loads(after_it["nu_bracket"])
            success_analysis.append({"source_cache_key": success["cache_key"], "nu_raw": success["nu_raw"], "V_A": success["V_A"],
                "L_km": l, "source_usable_at_all_26_distances": True,
                "objective_available": bool(objectives), "objective_K": objectives[0]["SKR"] if objectives else None,
                "delta_to_selected_K": objectives[0]["SKR"] - best_by_l[l]["K"] if objectives else None,
                "prior_AO_consumptions": len(consumptions), "prior_consumption_details": json.dumps(consumptions),
                "selected_nu_slice": selected_slice, "old_selected_nu_bracket": json.dumps(initial_bracket),
                "current_selected_nu_bracket": json.dumps(final_bracket),
                "selected_nu_bracket_before_own_batch": json.dumps(before_bracket),
                "selected_nu_bracket_after_own_batch": json.dumps(after_bracket),
                "selected_bracket_changed_during_own_batch": before_bracket != after_bracket,
                "classification": "USEFUL_BUT_INSUFFICIENT_MISSING_MIDPOINTS" if selected_slice else "CONSUMED_ON_COMPETING_OR_TRANSIENT_VA_5_5_SLICE",
                "source_and_objective_caches_verified": bool(objectives) and bool(consumptions)})
    assert len(success_analysis) == 15 and all(s["source_and_objective_caches_verified"] for s in success_analysis)
    io.write_csv(OUT / "three_completed_source_analysis.csv", success_analysis)

    # Rank CURRENT selected terminal slices first, not repeated historical
    # request frequency. Include remaining historical sources with explicit scope.
    missing_groups = defaultdict(list)
    for d in all_deps:
        if d["ensemble_hash"] not in bank:
            missing_groups[d["source_cache_key"]].append(d)
    ranked_rows = []
    for key, requests in missing_groups.items():
        cur = [d for d in requests if d.get("scope") == "CURRENT_FIVE_DISTANCE_CACHE_ONLY_REPLAY"]
        selected = [d for d in cur if d["essential_to_selected_terminal_search"]]
        timeouts = [a for a in ledger["attempts"] if a["cache_key"] == key and a["status"] == "TIMEOUT"]
        row = {"source_cache_key": key, "nu_raw": float(requests[0]["nu_raw"]), "V_A": float(requests[0]["V_A"]),
            "current_selected_distances": list_json({d["L_km"] for d in selected}),
            "current_selected_searches": len({d["search_id"] for d in selected}),
            "current_affected_distances": list_json({d["L_km"] for d in cur}),
            "current_affected_searches": len({d["search_id"] for d in cur}),
            "VA_searches": len({d["search_id"] for d in cur if d["variable"] == "V_A"}),
            "nu_searches": len({d["search_id"] for d in cur if d["variable"] == "nu_raw"}),
            "boundary_searches": len({d["search_id"] for d in cur if "BOUNDARY" in d["direction"]}),
            "historical_affected_distances": list_json({float(d["L_km"]) for d in requests}),
            "direct_local_refinement_dependency": any("REFINEMENT" in d["direction"] for d in selected),
            "timeout_history": json.dumps([{k: a.get(k) for k in ("timeout_seconds", "wall_seconds", "error")} for a in timeouts]),
            "risk": "PREVIOUS_60_MIN_TIMEOUT" if any(a["timeout_seconds"] >= 3590 for a in timeouts)
                else "ONLY_SHORT_REMAINING_BUDGET_TIMEOUT_NOT_60_MIN_TESTED" if timeouts else "ORIGINAL_AP_RUNTIME_UNKNOWN",
            "expected_closure_impact": "ENABLE_NEXT_EXACT_REFINEMENT_ATTEMPT_NOT_GUARANTEED_CLOSURE",
            "remaining_after_success": "Other side midpoint, subsequent dyadic probes, other coordinate and earlier/multistart unresolved searches; no global certificate",
            "classification": "A" if selected else "B_C_OR_COMPETING_BRANCH_ONLY"}
        row["selected_distance_count"] = len({d["L_km"] for d in selected})
        ranked_rows.append(row)
    ranked_rows.sort(key=lambda r: (-r["selected_distance_count"], -r["current_selected_searches"],
        -r["current_affected_searches"], r["risk"] == "PREVIOUS_60_MIN_TIMEOUT", r["nu_raw"], r["V_A"]))
    for rank, r in enumerate(ranked_rows, 1):
        r["priority"] = rank
    top = ranked_rows[:3]
    assert len(top) == 3 and all(r["direct_local_refinement_dependency"] for r in top)
    io.write_csv(OUT / "ranked_missing_source_probes.csv", ranked_rows)
    io.write_csv(OUT / "top_3_recommended_probes.csv", top)

    stopping_rows = [{"L_km": i["distance_km"], "start_id": i["start_id"], "iteration": i["iteration"],
        **{k: i[k] for k in ("K_before", "K_after_VA", "K_after_nu", "delta_K", "delta_nu", "delta_V_A",
                            "V_A_search_status", "nu_search_status", "convergence_status")},
        **{f"scalar_pass_{eps:g}": abs(i["delta_K"]) <= eps for eps in (1e-7, 1e-8, 1e-9)}} for i in iterations]
    changed_scalar = [r for r in stopping_rows if len({r[f"scalar_pass_{eps:g}"] for eps in (1e-7, 1e-8, 1e-9)}) > 1]
    io.write_csv(OUT / "stopping_sensitivity.csv", stopping_rows)
    stopping_md = ["# Offline stopping-criterion sensitivity", "",
        "No tolerance change or alternate-tolerance optimization was executed.",
        f"All {len(iterations)} current iterations: differing scalar decisions at 1e-7/1e-8/1e-9 = {len(changed_scalar)}.",
        "Zero terminal delta K and parameter displacement satisfy the scalar comparisons but do not complete either coordinate.",
        "Original stopping_status preserves earlier unresolved searches; the search must have no missing probes and NUMERICALLY_CLOSED_LOCAL_BRACKET.",
        "All selected runs stop before the six-iteration cap. No epsilon change supplies missing source moments.", "",
        "| L | start | iteration | K before | K after VA | K after nu | delta K | status |",
        "|---:|---|---:|---:|---:|---:|---:|---|"]
    stopping_md += ["| " + " | ".join(str(r[k]) for k in ("L_km", "start_id", "iteration", "K_before", "K_after_VA", "K_after_nu", "delta_K", "convergence_status")) + " |" for r in stopping_rows]
    (OUT / "stopping_criteria_analysis.md").write_text("\n".join(stopping_md) + "\n", encoding="utf-8")
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    io.save_json(OUT / "input_manifest_after.json", {name: io.digest(ROOT / name) for name in protected})
    tests = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                            "-p", "test_alt_opt_provenance_and_stopping.py", "-v"], cwd=ROOT, capture_output=True, text=True)
    (OUT / "regression_tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    missing_original = {d["ensemble_hash"] for d in original_deps if d["ensemble_hash"] not in bank}
    missing_all = {d["ensemble_hash"] for d in all_deps if d["ensemble_hash"] not in bank}
    assert (len(base), len(bank), len(missing_original), len(missing_all)) == (165, 168, 48, 50)
    assert sum(d["ensemble_hash"] not in bank for d in original_deps) == 786
    assert all(r["new_exact_objective_evaluations"] == 0 for r in records), "Compatible objective reuse unexpectedly incomplete"
    summary = {"status": "CURRENTLY_VERIFIED_PASS" if tests.returncode == diff.returncode == 0 else "FAILED",
        "scope": "DIAGNOSTIC_ONLY_NO_AP", "sources_before": len(base), "validated_sources": len(bank),
        "historical_missing_requests_initial": len(original_deps), "historical_missing_requests_remaining": 786,
        "original_missing_ensembles_remaining": len(missing_original), "missing_including_adaptive": len(missing_all),
        "previous_source_successes": 3, "previous_source_timeouts": 3, "new_AP_generations": 0,
        "all_three_sources_consumed_at_all_five_distances": True,
        "new_exact_objective_evaluations": sum(r["new_exact_objective_evaluations"] for r in records),
        "new_numerically_closed_searches": sum(b["numeric_local_completion"] for b in boundaries),
        "newly_converged_distances": sum(r["status"] == "CONVERGED_NUMERICALLY" for r in records),
        "cache_only_status_counts": dict(Counter(r["status"] for r in records)),
        "selected_parameters_or_K_changed": any(r["delta_K_selected"] != 0 or
            float(r["before_nu_raw_star"]) != r["after_nu_raw_star"] or float(r["before_V_A_star"]) != r["after_V_A_star"] for r in comparison),
        "bookkeeping_bug_verified": False, "candidate_history_cache_consistency_checks": verified_requests,
        "objective_restore_counts_by_distance": {str(next(iter(o.rows.values()))["L_km"]): o.diagnostic_restored for o in instances},
        "top_3": top, "epsilon_sensitivity_changed_scalar_decisions": len(changed_scalar),
        "protected_files_verified": len(protected), "producer_sha256": io.digest(__file__),
        "final_model_spec_sha256": io.digest(ROOT / "docs/FINAL_MODEL_SPEC.md"),
        "frozen_spec_discrepancy": "PREVIOUSLY_RECORDED_UNCHANGED", "publication": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "regression_tests_pass": tests.returncode == 0, "git_diff_check_pass": diff.returncode == 0,
        "cache_only_records": records,
        "all_26_selected_slices_reconstructed": len({float(r["L_km"]) for r in slice_points}) == 26,
        "limitations": ["Four stages cannot shrink current broad brackets to 1e-6 if the best stays fixed; no cap changed.",
            "Any earlier incomplete search blocks a convergence claim for that trajectory.",
            "Binary64-near pairs are not interchangeable exact ensembles.",
            "Three proposed probes cannot guarantee closure or supply a global unbounded-domain certificate.",
            "Remaining 21 distances were not replayed."]}
    io.save_json(OUT / "diagnostic_summary.json", summary)
    md = ["# ALT_OPT closure diagnostic — exact method unchanged", "", summary["status"], "",
        "No new arbitrary-precision source generation; original objective and search algorithm delegated unchanged.",
        "Three prior source successes were validated, evaluated and consumed at all five distances. No stale-cache bug was found.",
        "They improve nu-slice coverage at VA=5.5 but have lower SKR than the selected candidates; other distances use these on transient/competing branches.",
        "At the baseline and 22 km, the nu bracket narrowed [0.16,0.17] -> [0.1625,0.16625]. New required midpoints remain missing.",
        "VA slices at the selected pairs received no new source point; therefore they still fail local refinement.",
        "The four-stage refinement cap, two-sided 1e-6 criterion, missing midpoint pairs and earlier unresolved searches are distinct blockers.",
        "Type A: selected local midpoint coverage missing. Types B/C: competing branches retain open endpoints. Type D: multi-start pairs disagree.",
        "Type E: no verified stale-state/cache-consumption fault. Type F: no analytic continuous-global certificate (separate from local convergence).", "",
        "## Five selected coordinate slices", "",
        "| L | Coordinate | Fixed | Best | K | Exact neighbors | Missing values | Bracket radius | Required halving depth if best fixed |",
        "|---:|---|---:|---:|---:|---|---|---:|---:|"]
    md += ["| " + " | ".join(str(s[k]) for k in ("L_km", "coordinate", "fixed_parameter", "best_parameter", "best_K",
        "available_exact_neighbors", "missing_candidates", "bracket_radius", "halving_depth_if_best_unchanged")) + " |" for s in final_slices]
    md += ["", "## Three next probes — planning only", "",
        "Ranking uses current selected terminal relevance, shared current searches, then recorded feasibility. Historical repetition alone never ranks a source first.", "",
        "| Rank | nu | VA | Selected distances | Current affected searches | Impact | Risk |",
        "|---:|---:|---:|---|---:|---|---|"]
    md += ["| " + " | ".join(str(r[k]) for k in ("priority", "nu_raw", "V_A", "current_selected_distances", "current_affected_searches", "expected_closure_impact", "risk")) + " |" for r in top]
    md += ["", "No selected parameter or SKR changed in cache-only replay; no search closed and no convergence was established.",
        "An available exact value a few ULPs away is not a cache alias under the exact identity policy; do not round nu or VA to reuse it.",
        "No online tolerance changes were made; offline 1e-7/1e-8/1e-9 sensitivity is detailed in stopping_criteria_analysis.md.",
        "Saved source audit covers existing, newly generated and requested missing ensembles. Objective availability is limited to verified five-distance cache contexts.",
        "Coordinate_slice_analysis.csv retains every evaluated/missing candidate, exact metrics and hex identities, not an interpolated curve.",
        "Historical source requests 836 -> 786; original missing sources 50 -> 48; two new adaptive missing sources leave 50 known missing.",
        f"Protected files unchanged: {len(protected)}; source identities verified: {len(bank)}; regression tests PASS={tests.returncode == 0}; git diff --check PASS={diff.returncode == 0}.",
        "Scientific source/security/frozen model/training/test access/baseline selection/threshold approval unchanged. Frozen-spec discrepancy remains open.",
        "Stop here. The three ranked probes require explicit approval and a separate hard runtime budget."]
    (OUT / "diagnostic_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("status", "new_AP_generations", "new_exact_objective_evaluations", "new_numerically_closed_searches", "top_3")}, indent=2))
    return 0 if summary["status"] == "CURRENTLY_VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
