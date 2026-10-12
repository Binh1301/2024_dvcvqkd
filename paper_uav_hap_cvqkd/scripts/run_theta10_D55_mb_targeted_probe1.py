"""One approved exact probe; stop for review, never automatically run probe 2."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_convergence_validation as io
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_alt_opt_closure_continuation as supervisor
from scripts import run_theta10_D55_unconstrained_three_scheme as source

PLAN = ROOT / "results/theta10_D55_mb_exact_targeted_expansion"
OUT = PLAN / "probe_1_authorized_3h"
CONT = ROOT / "results/theta10_D55_alt_opt_closure_continuation"
CERT = ROOT / "results/theta10_D55_alt_opt_catalog_certification"
DIAG = ROOT / "results/theta10_D55_alt_opt_closure_diagnostic"
NU, VA = .16562500000000002, 5.5


def forbidden(*args, **kwargs):
    raise AssertionError("No source generation during SKR/coordinate postprocessing")


def postprocess(out):
    torch.set_num_threads(1)
    supervisor.verify_protected(out)
    config = source.unconstrained_config()
    bank = source.load_source_payloads(config, (source.SOURCE_CACHE, CONT / "exact_source_cache", out / "exact_source_cache"))
    candidate = source.candidate_from_payload(config, bank, "MB", NU, VA)
    assert candidate is not None
    old_rows = io.read_csv(CERT / "catalog_exact_objectives.csv")
    old_best = {float(r["L_km"]): r for r in io.read_csv(CERT / "catalog_maximum_certificate.csv")}
    audit = json.loads(io.AUDIT.read_text())
    old_report = json.loads((sweep.OUTPUT / "run_report.json").read_text())
    config_manifest = []
    comparisons, evaluations = [], []
    instances = {}
    with patch.object(ao.ExactMBEvaluator, "source_moments", forbidden):
        for l in sweep.DISTANCES_KM:
            channel = sweep.make_channel(config, l)
            obj = ao.ExactObjective(config, channel, out, allow_new_source=False,
                source_cache_dirs=(source.SOURCE_CACHE, CONT / "exact_source_cache", out / "exact_source_cache"))
            attestation = io.attest_old_objectives(config, channel, audit, old_report)
            restored = obj.restore_objective_rows([r for r in old_rows if float(r["L_km"]) == l and r["family"] == "MB"], attestation)
            assert restored == 139
            new_row = obj(NU, VA)
            candidates = sorted(obj.rows.values(), key=lambda r: float(r["SKR"]), reverse=True)
            best, second = candidates[:2]
            delta = float(best["SKR"]) - float(old_best[l]["available_best_K"])
            comparisons.append({"L_km": l, "old_nu": old_best[l]["available_best_nu"], "old_V_A": old_best[l]["available_best_V_A"],
                "old_K": old_best[l]["available_best_K"], "new_nu": best["nu_raw"], "new_V_A": best["V_A"],
                "new_K": best["SKR"], "absolute_improvement": delta, "probe_K": new_row["SKR"],
                "probe_delta_to_old_max": float(new_row["SKR"])-float(old_best[l]["available_best_K"]),
                "runner_up_nu": second["nu_raw"], "runner_up_V_A": second["V_A"], "runner_up_K": second["SKR"],
                "top_two_gap": float(best["SKR"])-float(second["SKR"]), "exact_MB_count": len(candidates),
                "ranking_scope": "EXACT_NUMERIC_VALUES_OF_FINITE_CATALOG_NOT_CONTINUOUS_GLOBAL",
                "meaningful_improvement_verdict": "INCONCLUSIVE_TOTAL_OBJECTIVE_ERROR_BOUND_NOT_ESTABLISHED" if delta>0 else "NO_POSITIVE_NUMERICAL_IMPROVEMENT"})
            evaluations.append(new_row)
            instances[l] = obj
            config_manifest.append({"L_km": l, "identity": obj.objective_identity, "historical_attestation": attestation})
            io.write_csv(out / "new_pair_26distance_objectives.csv", evaluations)
            io.write_csv(out / "old_vs_new_mb_optimum.csv", comparisons)
            io.save_json(out / "objective_checkpoint.json", {"rows": evaluations, "identities": config_manifest})
    affected = sorted(set(json.loads(io.read_csv(PLAN / "selected_mb_candidates.csv")[0]["current_affected_distances"]))
        | {r["L_km"] for r in comparisons if r["absolute_improvement"]>0})
    stage = out / "coordinate_revalidation"
    stage.mkdir()
    original_objective = ao.ExactObjective
    class CachedObjective(original_objective):
        def __init__(self, *args, **kwargs):
            kwargs["source_cache_dirs"] = (source.SOURCE_CACHE, CONT / "exact_source_cache", out / "exact_source_cache")
            super().__init__(*args, **kwargs)
            previous = instances[self.channel["distance_km"]]
            self.restore_objective_rows(list(previous.rows.values()), previous.objective_identity)
    searches = []
    original_search = ao.adaptive_maximize_1d
    def record_search(**kwargs):
        result = original_search(**kwargs)
        searches.append({"L_km": kwargs["objective"].channel["distance_km"], **result})
        return result
    with patch.object(ao.ExactMBEvaluator, "source_moments", forbidden), patch.object(ao, "ExactObjective", CachedObjective), \
         patch.object(ao,"adaptive_maximize_1d",record_search), patch.object(sweep,"adaptive_maximize_1d",record_search):
        records, iterations, boundaries, runs = io.validate_distances(stage, affected, config, audit, old_report,
            io.read_csv(ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun/mb_alt_opt_distance_summary.csv"),
            io.read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv"), out / "exact_source_cache")
    io.save_json(stage / "full_results.json", {"records":records,"iterations":iterations,"boundaries":boundaries,"runs":runs,"searches":searches})
    old_searches = json.loads((DIAG / "cache_only_searches.json").read_text())
    changed_slices = []
    for l in affected:
        old_final = [s for s in old_searches if s["L_km"]==l][-2:]
        new_final = [s for s in searches if s["L_km"]==l][-2:]
        for prior, current in zip(old_final,new_final):
            changed_slices.append({"L_km":l,"coordinate":current["variable"],"before_fixed":prior["fixed"],"after_fixed":current["fixed"],
                "same_slice":prior["fixed"]==current["fixed"],"before_bracket":json.dumps(prior["bracket"]),"after_bracket":json.dumps(current["bracket"]),
                "before_status":prior["status"],"after_status":current["status"],"after_boundary":current["boundary_status"],
                "remaining_missing_values":json.dumps([h["value"] for h in current["history"] if h["status"]=="EXACT_SOURCE_MISSING"]),
                "newly_numerically_closed":not ao.coordinate_search_complete(prior) and ao.coordinate_search_complete(current)})
    io.write_csv(out / "coordinate_search_status_after_expansion.csv", changed_slices)
    after_by_l = {r["L_km"]:r for r in records}
    old_selected = {float(r["L_km"]):r for r in io.read_csv(ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun/mb_alt_opt_distance_summary.csv")}
    matching = []
    for c in comparisons:
        l = c["L_km"]
        result = after_by_l.get(l)
        rnu = result["nu_raw_star"] if result else float(old_selected[l]["nu_raw_star"])
        rva = result["V_A_star"] if result else float(old_selected[l]["V_A_star"])
        rk = result["K"] if result else float(old_selected[l]["K"])
        matching.append({"L_km":l,"AO_nu":rnu,"AO_V_A":rva,"AO_K":rk,"expanded_catalog_K":c["new_K"],
            "matches_catalog_maximum":float(rk)==float(c["new_K"]),"AO_status":result["status"] if result else old_selected[l]["status"],
            "execution":"REVALIDATED_EXPANDED_CACHE" if result else "LAST_KNOWN_AO_PAIR_COMPARED_ONLY_NOT_RERUN"})
    io.write_csv(out / "alt_opt_expanded_catalog_comparison.csv",matching)
    io.write_csv(out / "expanded_catalog_26distance_results.csv",comparisons)
    io.write_csv(out / "expanded_mb_catalog.csv", [{"nu_raw":float.fromhex(p["nu_mb_raw_hex"]),"V_A":float.fromhex(p["V_A_hex"]),
        "source_cache_key":p["cache_key"],"ensemble_hash":p["ensemble_hash"],"C":p["C"],"w":p["w"],
        "is_new_this_probe":p["ensemble_hash"]==candidate["ensemble_hash"]} for p in bank.values() if float.fromhex(p["nu_mb_raw_hex"])>0])
    figure = None
    if any(r["absolute_improvement"]>0 for r in comparisons):
        from scripts.render_theta10_D55_three_scheme_log10 import render, SCHEMES
        prior_curve = io.read_csv(source.OUTPUT / "skr_vs_distance_three_scheme.csv")
        curve=[]
        by_l={r["L_km"]:r for r in comparisons}
        for r in prior_curve:
            if r["scheme"]==SCHEMES[2]:
                c=by_l[float(r["distance_km"])]
                r={**r,"nu_raw":c["new_nu"],"V_A":c["new_V_A"],"K":c["new_K"],
                   "selection_claim":"FINITE_EXPANDED_EXACT_MB_CATALOG_MAXIMUM_NUMERIC_ORDER_ONLY"}
            curve.append(r)
        path=out / "three_scheme_expanded_catalog.csv"
        io.write_csv(path,curve)
        png,pdf,receipt=render(path,out)
        figure={"png":str(png),"pdf":str(pdf),"receipt":str(receipt),"Uniform_and_fixed_MB_not_recomputed":True}
    outcome={"source_candidate":{k:candidate[k] for k in ("nu_raw","V_A","C","w","ensemble_hash","source_cache_key")},
        "new_exact_objectives":len(evaluations),"before_MB_count":139,"after_MB_count":140,
        "distances_with_positive_numeric_gain":[r["L_km"] for r in comparisons if r["absolute_improvement"]>0],
        "largest_numeric_gain":max(r["absolute_improvement"] for r in comparisons),
        "directly_revalidated_distances":affected,"last_known_other_distances":[l for l in sweep.DISTANCES_KM if l not in affected],
        "matching_catalog_maximum_updated_and_last_known":sum(r["matches_catalog_maximum"] for r in matching),
        "newly_numerically_closed_selected_searches":sum(r["newly_numerically_closed"] for r in changed_slices),
        "numerically_converged_revalidated_distances":sum(r["status"]=="CONVERGED_NUMERICALLY" for r in records),
        "remaining_open_boundary_invocations_revalidated":sum(r["boundary_status"]=="BOUNDARY_NOT_CLOSED" for r in boundaries),
        "representative_record_statuses":{str(r["L_km"]):r["status"] for r in records},
        "precision_quadrature_source_and_AO_unchanged":True,"total_objective_error_bound":"NOT_ESTABLISHED_NO_UNCERTAINTY_INVENTED", "figure":figure,
        "information_for_refinement":"VALID_EXACT_NEIGHBOR_ADDED; inspect before/after slices; numerical/global convergence not asserted"}
    supervisor.verify_protected(out)
    io.save_json(out / "postprocess_report.json",outcome)
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--total-budget",type=float)
    parser.add_argument("--probe-budget",type=float)
    parser.add_argument("--postprocess",action="store_true")
    args=parser.parse_args()
    if args.postprocess:
        return postprocess(OUT)
    if (args.total_budget,args.probe_budget)!=(10800.,3600.):
        parser.error("Require the explicit new approved total10800s/probe3600s budgets")
    if OUT.exists():
        parser.error("Probe-1 output exists; do not overwrite or automatically repeat")
    start=time.monotonic()
    deadline=start+args.total_budget
    manifest=json.loads((PLAN / "input_manifest_after.json").read_text())
    manifest.update(io.raw_snapshot([p for p in PLAN.rglob("*") if "__pycache__" not in p.parts]))
    for name,digest in manifest.items():
        assert io.digest(ROOT/name)==digest,name
    config=source.unconstrained_config()
    selected=next(r for r in io.read_csv(PLAN / "selected_mb_candidates.csv") if r["pilot_priority"]=="1")
    assert float(selected["nu_raw"]).hex()==NU.hex() and float(selected["V_A"])==VA
    bank=source.load_source_payloads(config,(source.SOURCE_CACHE,CONT / "exact_source_cache"))
    assert source.candidate_from_payload(config,bank,"MB",NU,VA) is None
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES)==(1e-8,1e-6,6,4)
    OUT.mkdir()
    io.save_json(OUT / "protected_input_manifest.json",manifest)
    supervisor.self_check()
    ledger={"status":"AUTHORIZED_PROBE_1_RUNNING","attempts":[],"used_wall_seconds":0.,
        "total_compute_budget_seconds":args.total_budget,"per_probe_timeout_seconds":args.probe_budget,
        "controller_pid":__import__('os').getpid(),"authorized_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "producer_sha256":io.digest(__file__),"probe_2_and_3_not_started":True,
        "authorization":"User explicitly approves new3h total/60min probe; probe1 result must be reported before deciding probe2"}
    io.save_json(OUT / "source_generation_ledger.json",ledger)
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(45):
            print(f"Probe1 supervised: elapsed={time.monotonic()-start:.1f}s; no later probe scheduled",flush=True)
    thread=threading.Thread(target=heartbeat,daemon=True)
    thread.start()
    try:
        point={**selected,"raw_current_cache_key":selected["source_cache_key"]}
        record=supervisor.run_batch(OUT,point,min(args.probe_budget,deadline-time.monotonic()-5),1,ledger)
    finally:
        stop.set()
    io.write_csv(OUT / "exact_source_generation_ledger.csv",[record])
    io.write_csv(OUT / "new_exact_mb_sources.csv",[{k:record.get(k) for k in
        ("nu_raw","V_A","C","w","cache_key","status","wall_seconds","cpu_seconds","source_payload_verified")}])
    receipt=None
    if record["status"]=="COMPLETED_EXACT":
        with (OUT / "postprocessing.log").open("w",encoding="utf-8") as log:
            receipt=supervisor.supervised_probe([sys.executable,"-X","utf8","-u",str(Path(__file__)),"--postprocess"],
                max(1,deadline-time.monotonic()-5),log)
        ledger["postprocessing_supervision"]=receipt
    ledger.update(status="PROBE_1_FINISHED_AWAITING_USER_REVIEW",controller_finished_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        budget_session_wall_seconds=time.monotonic()-start,used_wall_seconds=time.monotonic()-start)
    ledger["remaining_approved_compute_seconds"]=max(0,args.total_budget-ledger["used_wall_seconds"])
    io.save_json(OUT / "source_generation_ledger.json",ledger)
    protected_count=supervisor.verify_protected(OUT)
    tests=subprocess.run([sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-p",
        "test_alt_opt_provenance_and_stopping.py","-v"],cwd=ROOT,capture_output=True,text=True)
    (OUT / "regression_tests.txt").write_text(tests.stdout+tests.stderr,encoding="utf-8")
    diff=subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,text=True)
    result=json.loads((OUT / "postprocess_report.json").read_text()) if (OUT / "postprocess_report.json").exists() else None
    report={"status":ledger["status"],"probe_status":record["status"],"source_attempt":record,
        "total_budget_seconds":args.total_budget,"per_probe_budget_seconds":args.probe_budget,
        "budget_session_wall_seconds":ledger["budget_session_wall_seconds"],
        "remaining_approved_compute_seconds":ledger["remaining_approved_compute_seconds"],"postprocess":result,
        "postprocess_status":"COMPLETE" if result and receipt["returncode"]==0 else "FAILED_OR_TIMED_OUT" if receipt else "NOT_RUN_PROBE_DID_NOT_COMPLETE",
        "protected_files_unchanged":protected_count,"regression_tests_pass":tests.returncode==0,"git_diff_check_pass":diff.returncode==0,
        "probe_2_and_3_started":False,"decision":"REPORT_PROBE_1_AND_STOP; user review before probe2",
        "scope":"DIAGNOSTIC_ONLY_NOT_CONTINUOUS_CONVERGENCE","publication":"NOT_READY_FOR_PUBLICATION_SCALE_RUNS"}
    io.save_json(OUT / "run_report.json",report)
    md=["# Authorized targeted MB probe1", "",report["status"],
        f"Source outcome={record['status']}; nu={NU!r}; VA={VA!r}; wall={record['wall_seconds']}s; Job CPU={record.get('cpu_seconds')}s.",
        f"Budget total10800s; per-probe3600s. Session used={report['budget_session_wall_seconds']}s; remaining={report['remaining_approved_compute_seconds']}s.",
        f"Postprocess={report['postprocess_status']}; result={json.dumps(result,ensure_ascii=False)}.",
        f"Protected files unchanged={protected_count}; tests PASS={tests.returncode==0}; diff check PASS={diff.returncode==0}.",
        "Original equations, source method/precision/quadrature/evaluator/AO preserved. No interpolation. Old plan/caches/results not overwritten.",
        "Timeouts receive no fabricated source moments/SKR. No continuous convergence or global optimum claimed.",
        "Probes2/3 NOT_RUN. Stop for result review before any next probe."]
    (OUT / "run_report.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","probe_status","postprocess_status","budget_session_wall_seconds","postprocess")},indent=2),flush=True)
    return 0 if tests.returncode==diff.returncode==0 and report["postprocess_status"]!="FAILED_OR_TIMED_OUT" else 1


if __name__=="__main__":
    raise SystemExit(main())
