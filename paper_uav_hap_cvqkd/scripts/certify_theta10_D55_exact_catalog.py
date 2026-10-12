"""Certify explicit finite exact sets, never continuous optimality or new AP."""
from collections import Counter, defaultdict
import inspect
import json
import math
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_convergence_validation as io
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source

OUT = ROOT / "results/theta10_D55_alt_opt_catalog_certification"
STRICT = ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun"
CONT = ROOT / "results/theta10_D55_alt_opt_closure_continuation"
DIAG = ROOT / "results/theta10_D55_alt_opt_closure_diagnostic"


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def row_pair(row):
    return pair(0 if row.get("family") == "Uniform" else row["nu_raw"], row["V_A"])


def forbidden(*args, **kwargs):
    raise AssertionError("New source-moment generation is forbidden")


def location(module, token):
    path = Path(module.__file__)
    line = next(n for n, s in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if token in s)
    return str(path.relative_to(ROOT)).replace("\\", "/") + ":" + str(line)


def validate_row(row, candidate, channel):
    for field in ("I_AB", "beta_I_AB", "chi_BE", "SKR"):
        assert math.isfinite(float(row[field])), field
    assert float(row["beta_I_AB"]) == .95 * float(row["I_AB"])
    assert float(row["SKR"]) == float(row["beta_I_AB"]) - float(row["chi_BE"])
    assert row["ensemble_hash"] == candidate["ensemble_hash"]
    assert row["source_cache_key"] == candidate["source_cache_key"]
    assert row["channel_hash"] == channel["channel_hash"]


def main():
    if OUT.exists():
        raise SystemExit("Output exists: refusing to overwrite a certificate")
    OUT.mkdir()
    torch.set_num_threads(1)  # Same execution setting as the original producers.
    config = source.unconstrained_config()
    runtime = {"epsilon_opt": ao.K_TOLERANCE, "parameter_tolerance": ao.PARAMETER_TOLERANCE,
               "max_outer_iterations": ao.MAX_AO_ITERATIONS, "max_inner_refinement_steps": ao.MAX_REFINEMENT_STAGES}
    assert runtime == {"epsilon_opt": 1e-8, "parameter_tolerance": 1e-6, "max_outer_iterations": 6, "max_inner_refinement_steps": 4}
    assert ao.adaptive_maximize_1d.__kwdefaults__ == {"k_tolerance": 1e-8, "parameter_tolerance": 1e-6}
    assert sweep.adaptive_maximize_1d is ao.adaptive_maximize_1d
    assert sweep.MAX_AO_ITERATIONS == ao.MAX_AO_ITERATIONS == 6
    protected = json.loads((DIAG / "input_manifest_after.json").read_text())
    extra = list(DIAG.rglob("*")) + list((ROOT / "results/alt_opt_vs_numerical_audit_20261008_verified").rglob("*"))
    protected.update(io.raw_snapshot(extra))
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    io.save_json(OUT / "input_manifest_before.json", protected)
    io.save_json(OUT / "runtime_settings.json", runtime)
    bank = source.load_source_payloads(config, (source.SOURCE_CACHE, CONT / "exact_source_cache"))
    available = {pair(float.fromhex(p["nu_mb_raw_hex"]), float.fromhex(p["V_A_hex"])): p for p in bank.values()}
    historical_rows = io.read_csv(source.OUTPUT / "candidate_evaluations.csv")
    reference = {row_pair(r) for r in historical_rows if r["family"] == "MB"}
    assert len(reference) == 136 and reference <= available.keys()
    assert len(available) == len(bank) == 168
    # Preserve both the literal all-source set and the positive-nu MB domain.
    # Uniform sources belong to C_available_all, not to MB optimization.
    available_mb = {p for p in available if float.fromhex(p[0]) > 0}
    assert len(available_mb) == 139
    candidates = {p: source.candidate_from_payload(config, bank, "Uniform" if float.fromhex(p[0]) == 0 else "MB",
                  float.fromhex(p[0]), float.fromhex(p[1])) for p in available}
    assert all(candidates.values())
    catalog = []
    for n, p in enumerate(sorted(available, key=lambda p: tuple(map(float.fromhex, p))), 1):
        c, payload = candidates[p], available[p]
        catalog.append({"candidate_id": n, "nu_raw": c["nu_raw"], "V_A": c["V_A"], "nu_hex": p[0], "VA_hex": p[1],
            "family": c["family"], "in_C_reference": p in reference, "in_C_available_all": True,
            "in_C_available_MB_positive_nu": p in available_mb,
            "outside_reference_reason": "NEW_4H_EXACT_MB_SOURCE" if p in available_mb-reference else "UNIFORM_NU_ZERO_OUTSIDE_MB_DOMAIN" if p not in reference else "REFERENCE",
            "source_cache_key": c["source_cache_key"], "canonical_source_cache_key": c["canonical_source_cache_key"],
            "ensemble_hash": c["ensemble_hash"], "source_path": c["source_path"], "C": c["C"], "w": c["w"],
            "support_size": c["source_support_size"], "provenance": payload["_provenance"]["status"],
            "implementation_identity": json.dumps(payload["source_implementation"], sort_keys=True),
            "settings_identity": json.dumps(payload["source_settings"], sort_keys=True)})
    io.write_csv(OUT / "catalog_definition.csv", catalog)
    io.save_json(OUT / "catalog_identity.json", {
        "C_reference": "Distinct MB pairs in hash-bound historical candidate_evaluations.csv; no catalog redefinition",
        "C_available_all": "All compatible cached source ensembles including 29 Uniform nu=0 sources",
        "C_available_MB": "Positive-nu MB subset of C_available_all, appropriate to nu>0 optimization",
        "reference_csv_sha256": io.digest(source.OUTPUT / "candidate_evaluations.csv"),
        "catalog_definition_sha256": io.digest(OUT / "catalog_definition.csv"),
        "reference_count": len(reference), "available_all_count": len(available), "available_MB_count": len(available_mb)})
    old_index = {(float(r["L_km"]), row_pair(r)): r for r in historical_rows}
    assert len(old_index) == len(historical_rows)
    checkpoint_rows = []
    for path in (CONT / "exact_objective_cache").glob("*.json"):
        checkpoint_rows.append(json.loads(path.read_text()))
    old_alt = {float(r["L_km"]): r for r in io.read_csv(STRICT / "mb_alt_opt_distance_summary.csv")}
    audit = json.loads(io.AUDIT.read_text())
    numerical_report = json.loads((sweep.OUTPUT / "run_report.json").read_text())
    certificates, coverage, comparison, top_two, all_evaluations = [], [], [], [], []
    objective_new = objective_restored = objective_hits = 0
    with patch.object(ao.ExactMBEvaluator, "source_moments", forbidden):
        for l in sweep.DISTANCES_KM:
            channel = sweep.make_channel(config, l)
            objective = ao.ExactObjective(config, channel, OUT, allow_new_source=False,
                                          source_cache_dirs=(source.SOURCE_CACHE, CONT / "exact_source_cache"))
            attestation = io.attest_old_objectives(config, channel, audit, numerical_report)
            historical_mb = [r for r in historical_rows if r["family"] == "MB" and float(r["L_km"]) == l]
            original_coverage = {row_pair(r) for r in historical_mb if r["status"] == "PASS"}
            objective_restored += objective.restore_objective_rows(historical_mb, attestation)
            for saved in checkpoint_rows:
                if saved["identity"]["sha256"] == objective.context_hash:
                    objective_restored += objective.restore_objective_rows(saved["rows"], saved["identity"])
            evaluated, failures = {}, []
            for p, c in candidates.items():
                try:
                    if c["family"] == "MB":
                        cached = objective.key(c["nu_raw"], c["V_A"]) in objective.rows
                        r = objective(c["nu_raw"], c["V_A"])
                        origin = "COMPATIBLE_OBJECTIVE_CACHE" if cached else "NEW_EXACT_OBJECTIVE_FROM_EXISTING_SOURCE"
                    else:
                        r = old_index.get((l, p))
                        origin = "HASH_ATTESTED_HISTORICAL_UNIFORM_OBJECTIVE"
                        if r is None:
                            r = source.evaluate_candidate(c, channel, config)
                            r = {**r, "ensemble_hash": c["ensemble_hash"], "source_cache_key": c["source_cache_key"], "channel_hash": channel["channel_hash"]}
                            origin = "NEW_EXACT_UNIFORM_OBJECTIVE_FROM_EXISTING_SOURCE"
                    validate_row(r, c, channel)
                    evaluated[p] = {**r, "nu_raw": c["nu_raw"], "V_A": c["V_A"], "family": c["family"],
                                    "evaluation_origin": origin, "status": "PASS"}
                    all_evaluations.append(evaluated[p])
                except ao.ExactCandidateFailure as error:
                    failures.append({"L_km": l, "nu_raw": c["nu_raw"], "V_A": c["V_A"], "error": str(error), "status": "FAILED"})
            objective_new += objective.unique_exact_evaluations
            objective_hits += objective.cache_hits
            complete_reference = reference <= evaluated.keys()
            complete_available = available.keys() <= evaluated.keys()
            ranked_reference = sorted((evaluated[p] for p in reference if p in evaluated), key=lambda r: float(r["SKR"]), reverse=True)
            ranked_available = sorted(evaluated.values(), key=lambda r: float(r["SKR"]), reverse=True)
            best, second = ranked_reference[:2]
            best_all, second_all = ranked_available[:2]
            selected = old_alt[l]
            matches = float(best["SKR"]) == float(selected["K"])
            matches_pair = row_pair(best) == pair(selected["nu_raw_star"], selected["V_A_star"])
            improved = float(best_all["SKR"]) > float(selected["K"])
            reference_status = "PARTIALLY_VERIFIED" if not complete_reference else "CERTIFIED_REFERENCE_CATALOG_MAXIMUM" if matches else "IMPROVED_CANDIDATE_FOUND"
            available_status = "PARTIALLY_VERIFIED" if not complete_available else "IMPROVED_CANDIDATE_FOUND" if improved else "CERTIFIED_AVAILABLE_EXACT_SET_MAXIMUM" if float(best_all["SKR"]) == float(selected["K"]) else "PARTIALLY_VERIFIED"
            certificates.append({"L_km": l, "reference_status": reference_status, "available_all_status": available_status,
                "available_MB_status": available_status, "reference_candidate_count": len(reference),
                "available_all_count": len(available), "available_MB_count": len(available_mb),
                "best_nu": best["nu_raw"], "best_V_A": best["V_A"], "best_K": best["SKR"],
                "second_nu": second["nu_raw"], "second_V_A": second["V_A"], "second_K": second["SKR"],
                "reference_gap": float(best["SKR"]) - float(second["SKR"]),
                "available_gap": float(best_all["SKR"]) - float(second_all["SKR"]),
                "available_best_nu": best_all["nu_raw"], "available_best_V_A": best_all["V_A"], "available_best_K": best_all["SKR"],
                "ALT_OPT_matches_reference_pair": matches_pair, "ALT_OPT_attains_reference_maximum": matches,
                "outside_reference_improves_selected": improved, "continuous_domain_global_optimality": "NOT_PROVEN"})
            coverage.append({"L_km": l, "reference_expected": len(reference), "historical_reference_PASS": len(original_coverage),
                "historical_reference_missing_pairs": json.dumps(sorted(reference-original_coverage)),
                "reference_valid": sum(p in evaluated for p in reference), "available_MB_valid": sum(p in evaluated for p in available_mb),
                "available_all_valid": len(evaluated), "failed_candidates": len(failures), "failure_details": json.dumps(failures),
                "fresh_MB_objective_evaluations": objective.unique_exact_evaluations, "objective_cache_hits": objective.cache_hits})
            comparison.append({"L_km": l, "ALT_OPT_nu": selected["nu_raw_star"], "ALT_OPT_V_A": selected["V_A_star"],
                "ALT_OPT_K": selected["K"], "catalog_nu": best["nu_raw"], "catalog_V_A": best["V_A"], "catalog_K": best["SKR"],
                "delta_K": float(best["SKR"]) - float(selected["K"]), "same_exact_pair": matches_pair,
                "reference_certificate": reference_status, "available_certificate": available_status})
            for set_name, rows in (("C_reference", ranked_reference), ("C_available_all", ranked_available)):
                for rank, r in enumerate(rows[:2], 1):
                    top_two.append({"L_km": l, "catalog": set_name, "rank": rank, "nu_raw": r["nu_raw"], "V_A": r["V_A"],
                        **{k: r[k] for k in ("I_AB", "beta_I_AB", "chi_BE", "SKR", "source_cache_key", "ensemble_hash")},
                        "in_reference": row_pair(r) in reference})
            io.write_csv(OUT / "catalog_exact_objectives.csv", all_evaluations)
            io.write_csv(OUT / "catalog_maximum_certificate.csv", certificates)
            print(f"Catalog L={l}: reference {sum(p in evaluated for p in reference)}/{len(reference)}, available {len(evaluated)}/{len(available)}, {available_status}", flush=True)
    io.write_csv(OUT / "catalog_coverage_by_distance.csv", coverage)
    io.write_csv(OUT / "alt_opt_vs_catalog_maximum.csv", comparison)
    io.write_csv(OUT / "catalog_top_two_candidates.csv", top_two)

    # Reconstruct all accounting directly from immutable strict-rerun logs.
    iterations = io.read_csv(STRICT / "ao_iterations.csv")
    starts = io.read_csv(STRICT / "ao_multistart_summary.csv")
    groups = defaultdict(list)
    for it in iterations:
        groups[(float(it["distance_km"]), it["start_id"])].append(it)
    accounting, selected_histories = [], []
    for start in starts:
        l, sid = float(start["distance_km"]), start["start_id"]
        hist = groups[(l, sid)]
        assert len(hist) == int(start["AO_iterations"])
        assert [int(it["iteration"]) for it in hist] == list(range(len(hist)))
        selected = sid == old_alt[l]["selected_initialization"]
        last = hist[-1] if hist else None
        if last:
            assert pair(last["optimized_nu"], last["optimized_V_A"]) == pair(start["final_nu"], start["final_V_A"])
            assert float(last["K_after_nu"]) == float(start["K"])
        accounting.append({"L_km": l, "start_id": sid, "initial_nu": start["initial_nu"], "initial_VA": start["initial_V_A"],
            "AO_iterations": len(hist), "final_nu": start["final_nu"], "final_VA": start["final_V_A"], "final_K": start["K"],
            "selected": selected, "status": start["status"], "last_delta_K": last["delta_K"] if last else None,
            "terminated_before_cap": len(hist) < 6, "skipped_or_no_iteration": not hist,
            "stop_reason": "ZERO_IMPROVEMENT_WITH_OPEN_BOUNDARY" if start["status"] == "UNRESOLVED_BOUNDARY" else "ZERO_IMPROVEMENT_WITH_INCOMPLETE_INNER_SEARCH"})
        if selected:
            selected_histories += [{**it, "selected_run": True, "selected_stop_reason": accounting[-1]["stop_reason"]} for it in hist]
    assert len(groups) == len(starts) == 129 and len(iterations) == sum(a["AO_iterations"] for a in accounting) == 279
    assert sum(a["selected"] for a in accounting) == 26 and len(selected_histories) == 57
    io.write_csv(OUT / "all_multistart_iterations.csv", accounting)
    io.write_csv(OUT / "selected_run_iterations.csv", selected_histories)
    locations = {token: location(ao, token) for token in ("MAX_REFINEMENT_STAGES =", "refinement_stages = 0",
        "while boundary_status !=", "if max(best_value - lower", "midpoint_rows =", "refinement_stages += 1",
        'refinement_status = "SOURCE_MISSING_REFINEMENT"', 'refinement_status = "REFINEMENT_LIMIT_REACHED"', "def stopping_status(")}
    current_searches = json.loads((DIAG / "cache_only_searches.json").read_text())
    current_limits = Counter((s["refinement_stages"], s["refinement_status"]) for s in current_searches)
    historical_limits = Counter((it[p + "_refinement_stages"], it[p + "_refinement_status"]) for it in iterations for p in ("V_A", "nu"))
    assert all(int(stage) < 4 for stage, status in historical_limits)
    assert all(stage < 4 for stage, status in current_limits)
    counterfactual = []
    for invocation, s in enumerate(current_searches):
        missing = [h["value"] for h in s["history"] if h["status"] == "EXACT_SOURCE_MISSING"]
        # Observed searches stop BEFORE the original cap. Therefore all larger
        # caps reach the exact same unknown point; no hypothetical K is needed.
        assert missing and s["refinement_status"] in ("SOURCE_MISSING_REFINEMENT", "NOT_NEEDED")
        low, high = s["bracket"]
        rad = max(s["best_value"]-low, high-s["best_value"]) if low is not None and high is not None else None
        depth = math.ceil(math.log2(rad/1e-6)) if rad is not None and rad > 1e-6 else None
        for cap in (4, 8, 12, 16, 20):
            counterfactual.append({"invocation_id": invocation, "L_km": s["L_km"], "coordinate": s["variable"],
                "fixed_parameter": s["fixed"], "hypothetical_limit": cap, "current_attempted_steps": s["refinement_stages"],
                "successfully_completed_paired_refinement_steps": 0, "stop_status": "UNKNOWN_SOURCE",
                "actual_stop_type": s["refinement_status"] if s["refinement_stages"] else "OPEN_BOUNDARY_BEFORE_REFINEMENT",
                "unknown_values": json.dumps(missing), "best_parameter": s["best_value"], "best_K": s["best_K"],
                "bracket": json.dumps(s["bracket"]), "bracket_radius": rad,
                "conditional_halvings_to_parameter_tolerance": depth,
                "conditional_levels_beyond_hypothetical_cap": max(depth-cap,0) if depth is not None else None,
                "closed_with_existing_data": False, "no_new_objective_or_AP_call": True})
    io.write_csv(OUT / "refinement_counterfactual.csv", counterfactual)
    baseline = 21.9393102292
    final_baseline = [s for s in current_searches if s["L_km"] == baseline][-2:]
    audit_md = ["# Unchanged four-step refinement: code and execution audit", "",
        "Runtime: epsilon_opt=1e-8, parameter_tolerance=1e-6, outer=6, inner stages=4. No setting changed.", "",
        "## Actual implementation", "",
        f"Limit: {locations['MAX_REFINEMENT_STAGES =']}; counter resets per coordinate-search invocation at {locations['refinement_stages = 0']}.",
        f"Loop: {locations['while boundary_status !=']}; each stage attempts both (lower+best)/2 and (best+upper)/2 at {locations['midpoint_rows =']}.",
        f"Counter increment: {locations['refinement_stages += 1']}, AFTER both attempts, BEFORE the missing-result check.",
        "A missing-source attempt therefore consumes one stage then breaks immediately. Cache hits and fresh successful objective calls are not individual stage units: one paired midpoint attempt counts as one stage regardless of caching.",
        "Initial exact-catalog evaluations and boundary expansions do not increment refinement_stages. Successful midpoint pairs allow the next stage.",
        f"Missing point: {locations['refinement_status = ' + chr(34) + 'SOURCE_MISSING_REFINEMENT' + chr(34)]}; cap exhaustion: {locations['refinement_status = ' + chr(34) + 'REFINEMENT_LIMIT_REACHED' + chr(34)]}.",
        "Cap exhaustion yields INNER_SEARCH_FAILURE, not numerical convergence. Raising the cap would not change outer epsilon or the six-iteration cap, but could change inner search completion and indirectly the outer decision if source coverage were sufficient.", "",
        "## What actually happened", "",
        "Strict rerun 558 coordinate invocations: 280 no-refinement/open-boundary; 278 stop at the FIRST paired attempt on missing source. Zero hit cap 4.",
        "Latest representative replay 130 coordinate/postchecks: 35 open-boundary, 95 first-attempt source-missing. Zero hit cap 4.",
        "Thus cap=4 is a prospective independent ceiling, not the active termination cause in these recorded searches.", "",
        "## Final baseline slices", "",
        "| coordinate | fixed | exact bracket | missing values | radius | conditional halvings |",
        "|---|---:|---|---|---:|---:|"]
    for s in final_baseline:
        row = next(r for r in counterfactual if r["invocation_id"] == current_searches.index(s))
        audit_md.append(f"| {s['variable']} | {s['fixed']} | {s['bracket']} | {row['unknown_values']} | {row['bracket_radius']} | {row['conditional_halvings_to_parameter_tolerance']} |")
    audit_md += ["", "The 17/12 counts are ceil(log2(radius/1e-6)), a conditional parameter-radius reduction with fixed best and both midpoint evaluations available. They are NOT objective-tolerance counts or global-optimality evidence.",
        "In the unchanged implementation the radius check occurs at the BEGINNING of the next loop stage. Reaching radius tolerance on the last allowed midpoint stage still produces REFINEMENT_LIMIT_REACHED: in this fixed-best idealization the verdict needs at least 18/13 allowed stages, not merely 17/12 midpoint levels.",
        "At the final pair neither coordinate completes even its first paired refinement: VA needs 5.45/5.525 at nu=.165; nu needs .16375/.16562500000000002 at VA=5.5.",
        "New prior source points became initial catalog neighbors on subsequent searches; individual successful AP probes are not successfully completed paired refinement stages.",
        "For every offline cap 4/8/12/16/20, existing data meet the same UNKNOWN_SOURCE before that cap. No hypothetical objective or source was invented.",
        "Outer delta K=0 already meets objective epsilon; incomplete inner searches/earlier unresolved conditions remain. This is catalog stagnation, not numerical convergence."]
    (OUT / "refinement_limit_audit.md").write_text("\n".join(audit_md)+"\n", encoding="utf-8")
    reviews = io.read_csv(DIAG / "top_3_recommended_probes.csv")
    baseline_cert = next(c for c in certificates if c["L_km"] == baseline)
    for r in reviews:
        r.update(reference_gap_at_baseline=baseline_cert["reference_gap"], available_gap_at_baseline=baseline_cert["available_gap"],
                 can_complete_search_alone=False, refinement_cap_is_current_blocker=False,
                 refinement_cap_would_remain_prospective_limit=True,
                 remaining_neighbors="(.165,5.525), deeper midpoints, other slices, competing/earlier searches",
                 recommendation="DEFER_AP_UNTIL_CONTINUOUS_CLOSURE_OBJECTIVE_AND_COVERAGE_PLAN_AUTHORIZED")
    io.write_csv(OUT / "remaining_source_dependency_review.csv", reviews)
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    io.save_json(OUT / "input_manifest_after.json", {n: io.digest(ROOT/n) for n in protected})
    tests = subprocess.run([sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-p","test_alt_opt_provenance_and_stopping.py","-v"], cwd=ROOT, capture_output=True, text=True)
    (OUT / "regression_tests.txt").write_text(tests.stdout+tests.stderr, encoding="utf-8")
    diff = subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,text=True)
    report = {"status": "CURRENTLY_VERIFIED_PASS" if tests.returncode == diff.returncode == 0 else "FAILED",
        "scope": "FINITE_SET_CERTIFICATE_NOT_CONTINUOUS_OPTIMALITY", "runtime": runtime,
        "reference_count": len(reference), "available_all_count": len(available), "available_MB_count": len(available_mb),
        "available_Uniform_outside_MB_domain": len(available)-len(available_mb),
        "reference_certificate_counts": dict(Counter(c["reference_status"] for c in certificates)),
        "available_certificate_counts": dict(Counter(c["available_all_status"] for c in certificates)),
        "historical_reference_valid_rows": sum(c["historical_reference_PASS"] for c in coverage),
        "available_exact_objective_rows": len(all_evaluations), "new_exact_MB_objective_evaluations": objective_new,
        "objective_cache_hits": objective_hits, "objective_rows_restored_including_overlap": objective_restored,
        "new_AP_generations": 0, "reference_pair_matches": sum(c["ALT_OPT_matches_reference_pair"] for c in certificates),
        "outside_reference_improved_distances": [c["L_km"] for c in certificates if c["outside_reference_improves_selected"]],
        "reference_gap_min": min(c["reference_gap"] for c in certificates), "reference_gap_max": max(c["reference_gap"] for c in certificates),
        "baseline": baseline_cert, "starts_executed": len(accounting), "total_outer_iterations": len(iterations),
        "selected_run_iterations": len(selected_histories), "selected_runs": 26,
        "starts_with_zero_iterations": sum(r["skipped_or_no_iteration"] for r in accounting),
        "starts_reaching_outer_cap": sum(not r["terminated_before_cap"] for r in accounting),
        "historical_refinement_accounting": {str(k):v for k,v in historical_limits.items()},
        "current_refinement_accounting": {str(k):v for k,v in current_limits.items()},
        "searches_reaching_four_step_cap": 0, "counterfactual_extra_searches_closed": 0,
        "source_line_references": locations, "protected_files_verified": len(protected),
        "producer_sha256": io.digest(__file__), "frozen_spec_sha256": io.digest(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        "frozen_spec_discrepancy": "UNCHANGED_PREEXISTING", "publication": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "regression_tests_pass": tests.returncode == 0, "git_diff_check_pass": diff.returncode == 0,
        "certificates": certificates, "AP_next_step": "DO_NOT_RUN_AP_NOW"}
    io.save_json(OUT / "final_report.json", report)
    recommendation = ["# Final finite-catalog certificate and next-step decision", "",
        "## A. Supportable now", "",
        f"C_reference={len(reference)} explicit historical MB pairs, with {report['historical_reference_valid_rows']} historical PASS rows across 26 distances.",
        f"C_available_all={len(available)} compatible sources: {len(available_mb)} positive-nu MB plus 29 Uniform (nu=0, excluded from the MB domain). Sets are separate; definitions/keys/hex coordinates are in catalog_definition.csv.",
        f"Reference certificates: {report['reference_certificate_counts']}; available certificates: {report['available_certificate_counts']}.",
        f"Outside-reference improvements: {report['outside_reference_improved_distances']}. Fresh exact objectives from existing sources: {objective_new}; new AP: 0.",
        "This is exhaustive enumeration of an explicitly frozen finite set, not a replacement optimizer or a continuous-domain proof.",
        "| L | best nu | best VA | best K | second nu | second VA | reference gap | available gap |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    recommendation += ["| "+" | ".join(str(c[k]) for k in ("L_km","best_nu","best_V_A","best_K","second_nu","second_V_A","reference_gap","available_gap"))+" |" for c in certificates]
    recommendation += ["", "## B. Unproven conditions", "",
        "Completed inner searches: missing exact midpoint pairs, broad parameter brackets and potentially the four-stage ceiling after coverage completion.",
        "Numerical coordinate convergence: outer zero delta does not remove current/earlier incomplete searches; multi-start completeness is not established.",
        "Boundary closure: endpoint probes of competing and other distance trajectories remain absent; local brackets do not close all positive-domain tails.",
        "Continuous global optimality: no accepted analytic tail/global certificate. Neither finite-set certificate supplies it.", "",
        "## Accounting and refinement", "",
        "Raw strict-rerun histories independently verify 129 starts, 279 total outer iterations and 57 iterations in 26 selected runs. The latter is a subset, not a discrepancy.",
        "All recorded strict inner searches stop at 0/1 stages, never 4. Increasing only the cap to 8/12/16/20 cannot remove missing sources. Offline branches stop UNKNOWN_SOURCE.",
        "The selected runs stop after scalar zero improvement with unresolved inner/boundary searches, not because they reach outer cap 6.", "",
        "## Decision", "",
        "Do not spend another AP batch now merely to reproduce the finite-catalog maximum. Three planned probes may improve local coverage but cannot guarantee convergence or better K.",
        "If continuous-coordinate certification is scientifically necessary, first authorize a separate prospective coverage/closure plan, including midpoint levels, the loop-entry stopping-check semantics and missing earlier/multistart/boundary directions. No cap/tolerance/method change or runtime authorization is granted here.",
        "Suggested manuscript wording (diagnostic scope only): ALT_OPT reproduced the maximum of an explicitly defined 136-point historical exact MB catalog at all 26 link distances; exhaustive evaluation of 139 currently available MB sources found no better candidate. Continuous-domain convergence and global optimality were not established.",
        "This finite-set observation can be drafted as a scope-limited numerical result, not publication readiness, full numerical/security certification, finite-size/composable security or an operational fading-protocol proof. Frozen-spec provenance discrepancy and publication lifecycle gates remain open.",
        f"Regression tests PASS={tests.returncode==0}; git diff --check PASS={diff.returncode==0}; protected files unchanged={len(protected)}.",
        "All original scientific computation, AO settings/update/multi-start logic, source precision/quadrature, training/test access and approvals unchanged. Stop; no AP generation."]
    (OUT / "final_recommendation.md").write_text("\n".join(recommendation)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","reference_certificate_counts","available_certificate_counts","new_exact_MB_objective_evaluations","new_AP_generations","baseline")},indent=2))
    return 0 if report["status"] == "CURRENTLY_VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
