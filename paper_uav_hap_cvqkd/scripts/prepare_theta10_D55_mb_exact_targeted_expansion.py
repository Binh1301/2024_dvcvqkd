"""Prepare a three-source pilot only; never generate AP or evaluate SKR/AO."""
import csv
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_convergence_validation as io
from scripts import run_theta10_D55_unconstrained_three_scheme as source

OUT = ROOT / "results/theta10_D55_mb_exact_targeted_expansion"
CERT = ROOT / "results/theta10_D55_alt_opt_catalog_certification"
DIAG = ROOT / "results/theta10_D55_alt_opt_closure_diagnostic"
CONT = ROOT / "results/theta10_D55_alt_opt_closure_continuation"
STATUS = "PLAN_PREPARED_AWAITING_NEW_COMPUTE_BUDGET"


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def forbidden(*args, **kwargs):
    raise AssertionError("This is planning only; AP requires a new explicit budget")


def empty_csv(name, fields):
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields).writeheader()


def main():
    if OUT.exists():
        raise SystemExit("Output exists: preserve the plan, do not overwrite it")
    config = source.unconstrained_config()
    manifest = json.loads((CERT / "input_manifest_after.json").read_text())
    manifest.update(io.raw_snapshot([p for p in CERT.rglob("*") if "__pycache__" not in p.parts]))
    for name, expected in manifest.items():
        assert io.digest(ROOT / name) == expected, name
    certificate = json.loads((CERT / "final_report.json").read_text())
    old_ledger = json.loads((CONT / "source_generation_ledger.json").read_text())
    # Existing 3600s watchdog settings are numerical/operational limits, not
    # approval for a new run. The only scoped approved session is exhausted.
    assert old_ledger["status"] == "STOPPED_AT_HARD_BUDGET"
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            ao.MAX_REFINEMENT_STAGES) == (1e-8, 1e-6, 6, 4)
    with patch.object(ao.ExactMBEvaluator, "source_moments", forbidden):
        bank = source.load_source_payloads(config, (source.SOURCE_CACHE, CONT / "exact_source_cache"))
        mb = {pair(float.fromhex(p["nu_mb_raw_hex"]), float.fromhex(p["V_A_hex"])): p
              for p in bank.values() if float.fromhex(p["nu_mb_raw_hex"]) > 0}
        previous_pairs = {pair(r["nu_raw"], r["V_A"]) for r in io.read_csv(CERT / "catalog_definition.csv")
                          if r["in_C_available_MB_positive_nu"] == "True"}
        assert previous_pairs <= mb.keys(), "Certified source disappeared"
        baseline = io.read_csv(CERT / "catalog_maximum_certificate.csv")
        # New sources appearing outside the certified set would require an
        # explicit refreshed baseline; do not silently use stale maxima.
        if mb.keys() != previous_pairs:
            raise SystemExit("Compatible MB catalog changed: refresh finite-set coverage before preparing this pilot")
        ranked = {pair(r["nu_raw"], r["V_A"]): r for r in io.read_csv(DIAG / "ranked_missing_source_probes.csv")}
        identities = {pair(r["nu_raw"], r["V_A"]): r for r in io.read_csv(CONT / "current_missing_source_priorities.csv")}
        searches = json.loads((DIAG / "cache_only_searches.json").read_text())
        slices = [s for s in searches if s["L_km"] == 21.9393102292][-2:]
        nu_slice = next(s for s in slices if s["variable"] == "nu_raw")
        va_slice = next(s for s in slices if s["variable"] == "V_A")
        nu_missing = [(h["value"], nu_slice["fixed"]) for h in nu_slice["history"] if h["status"] == "EXACT_SOURCE_MISSING"]
        va_missing = [(va_slice["fixed"], h["value"]) for h in va_slice["history"] if h["status"] == "EXACT_SOURCE_MISSING"]
        has_long_timeout = lambda p: any(pair(a["nu_raw"], a["V_A"]) == pair(*p)
            and a["status"] == "TIMEOUT" and a["timeout_seconds"] >= 3590 for a in old_ledger["attempts"])
        eligible_nu = [p for p in nu_missing if not has_long_timeout(p)]
        selected_pairs = eligible_nu[:1] + va_missing
        assert len(selected_pairs) == len({pair(*p) for p in selected_pairs}) == 3
        evaluator = ao.ExactMBEvaluator(config, {"T_eff": 0., "epsilon_base": .0186, "c_phi": 0.},
            OUT, source_cache_dir=CONT / "exact_source_cache", allow_legacy_exact_import=False)
        selected = []
        for priority, (nu, va) in enumerate(selected_pairs, 1):
            key = pair(nu, va)
            assert key not in mb and key in ranked and key in identities
            assert source.candidate_from_payload(config, bank, "MB", nu, va) is None
            identity = evaluator._source_identity(source.make_ensemble(config, "MB", nu, va), nu, va)
            cache_key = source.json_hash(identity)
            assert cache_key == identities[key]["raw_current_cache_key"] == ranked[key]["source_cache_key"]
            attempts = [a for a in old_ledger["attempts"] if pair(a["nu_raw"], a["V_A"]) == key]
            reason = "Closest missing upper-nu midpoint; prior failure had only 33.781s remaining budget, not a 60-minute feasibility test" if key in {pair(*p) for p in eligible_nu} else "Original lower/upper VA midpoint; together with its paired neighbor covers both sides of selected VA=5.5, but further refinement remains"
            selected.append({**ranked[key], "pilot_priority": priority, "nu_raw": nu, "V_A": va,
                "nu_raw_hex": key[0], "V_A_hex": key[1], "canonical_source_cache_key": identities[key]["canonical_source_cache_key"],
                "ensemble_hash": identities[key]["ensemble_hash"], "source_availability": "EXACT_SOURCE_MISSING",
                "selection_reason": reason, "generation_status": "NOT_RUN_AWAITING_NEW_BUDGET",
                "prior_attempts": json.dumps([{k: a.get(k) for k in ("status", "wall_seconds", "timeout_seconds", "cpu_seconds", "error")} for a in attempts]),
                "predicted_K_or_runtime": "UNKNOWN_NO_PREDICTION", "complete_search_guaranteed": False})
    OUT.mkdir()
    io.save_json(OUT / "input_manifest_before.json", manifest)
    io.write_csv(OUT / "selected_mb_candidates.csv", selected)
    io.write_csv(OUT / "exact_source_generation_ledger.csv", [{
        "pilot_priority": s["pilot_priority"], "nu_raw": s["nu_raw"], "V_A": s["V_A"],
        "source_cache_key": s["source_cache_key"], "status": s["generation_status"],
        "wall_seconds": None, "cpu_seconds": None, "new_total_budget_seconds": None,
        "new_per_probe_timeout_seconds": None, "prior_attempts": s["prior_attempts"]} for s in selected])
    empty_csv("new_exact_mb_sources.csv", ["nu_raw", "V_A", "source_cache_key", "C", "w", "wall_seconds", "cpu_seconds", "status"])
    io.write_csv(OUT / "expanded_mb_catalog.csv", [{"nu_raw": float.fromhex(k[0]), "V_A": float.fromhex(k[1]),
        "nu_raw_hex": k[0], "V_A_hex": k[1], "source_cache_key": p["cache_key"], "ensemble_hash": p["ensemble_hash"],
        "C": p["C"], "w": p["w"], "provenance": p["_provenance"]["status"], "is_new_this_run": False,
        "execution": "CURRENT_VALIDATED_CATALOG_SNAPSHOT_NOT_EXPANDED"} for k, p in mb.items()])
    io.write_csv(OUT / "expanded_catalog_26distance_results.csv", [{**r,
        "execution": "LAST_KNOWN_CERTIFICATE_NOT_REEVALUATED", "expansion_status": "NOT_RUN", "current_MB_count": len(mb)} for r in baseline])
    io.write_csv(OUT / "old_vs_new_mb_optimum.csv", [{"L_km": r["L_km"], "old_nu": r["best_nu"], "old_V_A": r["best_V_A"],
        "old_K": r["best_K"], "new_nu": None, "new_V_A": None, "new_K": None, "absolute_improvement": None,
        "execution": "EXPANSION_NOT_RUN"} for r in baseline])
    io.write_csv(OUT / "top_two_candidates_by_distance.csv", [{**r, "execution": "LAST_KNOWN_AVAILABLE_SET_NOT_EXPANDED"}
        for r in io.read_csv(CERT / "catalog_top_two_candidates.csv") if r["catalog"] == "C_available_all"])
    io.write_csv(OUT / "alt_opt_expanded_catalog_comparison.csv", [{"L_km": r["L_km"],
        "baseline_matches_available_set": r["ALT_OPT_attains_reference_maximum"], "after_expansion_matches": None,
        "execution": "ALT_OPT_NOT_RERUN_NO_NEW_SOURCE"} for r in baseline])
    io.write_csv(OUT / "coordinate_search_status_after_expansion.csv", [
        {"scope": "LAST_KNOWN_FULL_26_STRICT_RERUN", "before_unresolved_coordinates": 558,
         "before_unresolved_boundaries": 280, "after_unresolved_coordinates": None, "after_unresolved_boundaries": None, "execution": "NOT_RUN"},
        {"scope": "LAST_KNOWN_FIVE_REPRESENTATIVES_WITH_POSTCHECKS", "before_unresolved_coordinates": len(searches),
         "before_unresolved_boundaries": sum(s["boundary_status"] == "BOUNDARY_NOT_CLOSED" for s in searches),
         "after_unresolved_coordinates": None, "after_unresolved_boundaries": None, "execution": "NOT_RUN"}])
    tests = subprocess.run([sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-p",
        "test_alt_opt_provenance_and_stopping.py","-v"], cwd=ROOT,capture_output=True,text=True)
    (OUT / "regression_tests.txt").write_text(tests.stdout+tests.stderr,encoding="utf-8")
    diff = subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,text=True)
    for name, expected in manifest.items():
        assert io.digest(ROOT / name) == expected, name
    io.save_json(OUT / "input_manifest_after.json", {n: io.digest(ROOT/n) for n in manifest})
    report = {"status": STATUS, "plan_validation": "CURRENTLY_VERIFIED_PASS" if tests.returncode==diff.returncode==0 else "FAILED",
        "scope": "STAGE_1_PLAN_ONLY", "compatible_MB_before": len(mb), "compatible_MB_after": len(mb),
        "new_exact_MB_pairs": 0, "source_attempts_this_run": 0, "new_SKR_evaluations": 0, "ALT_OPT_reruns": 0,
        "selected": selected, "deferred_candidate": {"nu_raw": .16375,"V_A": 5.5,
            "reason": "Original 3600s probe timed out; do not automatically retry. It remains the missing partner on the nu slice."},
        "last_known_catalog_matching_distances": certificate["reference_pair_matches"], "after_expansion_matching_distances": "NOT_RUN",
        "after_expansion_improved_distances": "NOT_RUN", "after_expansion_converged_distances": "NOT_RUN",
        "old_budget_status": old_ledger["status"], "new_compute_budget_approved": False,
        "new_total_budget_seconds": None, "new_per_probe_timeout_seconds": None, "planned_batch_size": 1,
        "first_probe_requires_result_and_benefit_review_before_next": True,
        "accuracy_policy": "Use unchanged evaluator and existing validation. Epsilon_opt is not an error bound; tiny deltas need demonstrated reliability or INCONCLUSIVE ranking. No uncertainty or improvement invented.",
        "runtime_freeze": {"epsilon_opt": 1e-8,"parameter_tolerance": 1e-6,"outer_cap":6,"inner_cap":4,
                           "source_precision_ladder": ao.source_settings(config)["precision_ladder"]},
        "protected_files_verified": len(manifest), "producer_sha256": io.digest(__file__),
        "frozen_spec_discrepancy": "PREEXISTING_UNCHANGED", "publication": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "regression_tests_pass": tests.returncode==0,"git_diff_check_pass":diff.returncode==0,
        "continuation_policy": "Only after fresh explicit runtime approval; original evaluator/Job supervisor, validate/checkpoint each source, evaluate only new SKR pairs at 26 distances, then unchanged cache-only AO on affected distances. Do not reuse the exhausted controller budget."}
    io.save_json(OUT / "run_report.json", report)
    md = ["# Targeted exact MB expansion — candidate plan only", "", STATUS, "",
        f"Currently verified MB catalog: {len(mb)} unique pairs. No newer compatible source in the scoped validated cache directories. No AP/SKR/AO rerun.",
        "No new total/per-probe budget was approved. Previous 14400s/3600s session is STOPPED_AT_HARD_BUDGET; configuration watchdogs do not constitute new authorization.", "",
        "| Priority | nu_raw | VA | Current affected searches | Selection reason |", "|---:|---:|---:|---:|---|"]
    md += [f"| {s['pilot_priority']} | {s['nu_raw']} | {s['V_A']} | {s['current_affected_searches']} | {s['selection_reason']} |" for s in selected]
    md += ["", "All three are actual midpoint requests at baseline/22 km, with exact hex/cache/ensemble identities verified. No arbitrary candidate was invented.",
        "(.16375,5.5) is deferred because its unchanged evaluator already timed out at 3600s. It is not declared invalid/inferior and will still block the other side of the nu search.",
        "C/D form the two missing VA midpoint sides; their completion can enable another refinement attempt, not guarantee a completed search. Further exact midpoint levels and other branches remain unresolved.",
        "After authorization: start serially with ONE probe, validate original source checks/provenance, checkpoint and measure CPU/wall time, then evaluate its newly enabled SKR at all 26 distances using compatible old objectives. Review actual benefit/cost before another probe.",
        "Retain epsilon=1e-8, parameter tolerance=1e-6, outer cap6, inner cap4, original starts/continuation and source ladder1050/1250/1450. No peak/budget constraints or interpolation added.",
        "Very small positive numerical deltas are not automatically meaningful; no demonstrated uncertainty bound is invented from epsilon_opt. Comparisons without adequate reliability evidence remain INCONCLUSIVE.", "",
        "| Metric | Before | After this planning turn |", "|---|---:|---|",
        f"| Compatible MB exact pairs | {len(mb)} | {len(mb)} (measured cache) |", "| New exact MB pairs | 0 | 0 |",
        "| Distances matching catalog maximum | 26/26 last known | Expansion NOT_RUN |",
        "| Distances with improved SKR | 0 last known | Expansion NOT_RUN |",
        "| Numerically converged distances | 0 last known | ALT_OPT NOT_RUN |",
        "| Unresolved coordinate directions | 558 full26 /130 five+postchecks last known | NOT_RUN |",
        "| Unresolved boundary directions | 280 full26 /35 five+postchecks last known | NOT_RUN |", "",
        "Files named expanded/after contain explicit unexpanded baseline snapshots or NOT_RUN fields, not fabricated after results. New-source CSV is header-only; per-probe new wall/CPU values are blank.",
        "No figure generated: no new best curve. Uniform/fixed-MB were neither recalculated nor modified.",
        f"Protected files unchanged={len(manifest)}; regressions PASS={tests.returncode==0}; git diff --check PASS={diff.returncode==0}.",
        "Scientific computation, frozen specification, training/test access, baseline selection and threshold approval unchanged. Frozen-spec discrepancy remains open; publication lifecycle unchanged.",
        "STOP for user approval of total hard runtime and maximum per-probe runtime. No expensive computation started."]
    (OUT / "run_report.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","plan_validation","compatible_MB_before","new_exact_MB_pairs","new_compute_budget_approved","protected_files_verified")},indent=2))
    return 0 if report["plan_validation"]=="CURRENTLY_VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
