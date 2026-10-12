"""Three explicitly authorized serial probes; original scientific routines only."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_mb_targeted_probe1 as prior
from scripts import windows_sleep_safe_supervision as safe

ao, io, sweep, source, supervisor = prior.ao, prior.io, prior.sweep, prior.source, prior.supervisor
OUT = prior.PLAN / "resumed_sleep_safe_run"
PAIRS = ((.16562500000000002, 5.5), (.165, 5.45), (.165, 5.525))
SOURCE_DIRS = (source.SOURCE_CACHE, prior.CONT / "exact_source_cache", OUT / "exact_source_cache")


def evaluate(run_ao=False):
    """Cache-only expansion and original sweep starts/previous-distance continuation."""
    import torch
    torch.set_num_threads(1)
    supervisor.verify_protected(OUT)
    config = source.unconstrained_config()
    bank = source.load_source_payloads(config, SOURCE_DIRS)
    mb = [p for p in bank.values() if float.fromhex(p["nu_mb_raw_hex"]) > 0]
    assert 139 <= len(mb) <= 142
    io.write_csv(OUT / "updated_mb_catalog.csv", [{"nu_raw":float.fromhex(p["nu_mb_raw_hex"]),
        "V_A":float.fromhex(p["V_A_hex"]), "C":p["C"], "w":p["w"],
        "ensemble_hash":p["ensemble_hash"], "source_cache_key":p["cache_key"]} for p in mb])
    originals = io.read_csv(prior.CERT / "catalog_exact_objectives.csv")
    old_best = {float(r["L_km"]):r for r in io.read_csv(prior.CERT / "catalog_maximum_certificate.csv")}
    old_report = json.loads((sweep.OUTPUT / "run_report.json").read_text())
    audit = json.loads(io.AUDIT.read_text())
    comparisons, top_two, new_rows, identities, records, runs_all, iterations, searches = [], [], [], [], [], [], [], []
    existing = json.loads((OUT / "objective_checkpoint.json").read_text()) if (OUT / "objective_checkpoint.json").exists() else {}
    warm = None
    original_search = ao.adaptive_maximize_1d
    def record_search(**kwargs):
        result = original_search(**kwargs)
        searches.append({"L_km":kwargs["objective"].channel["distance_km"], **result})
        return result
    with patch.object(ao.ExactMBEvaluator, "source_moments", prior.forbidden), \
         patch.object(ao, "adaptive_maximize_1d", record_search), patch.object(sweep, "adaptive_maximize_1d", record_search):
        for distance in sweep.DISTANCES_KM:
            obj = ao.ExactObjective(config, sweep.make_channel(config, distance), OUT,
                allow_new_source=False, source_cache_dirs=SOURCE_DIRS)
            attestation = io.attest_old_objectives(config, obj.channel, audit, old_report)
            assert obj.restore_objective_rows([r for r in originals if float(r["L_km"]) == distance and r["family"] == "MB"], attestation) == 139
            saved = existing.get(str(distance))
            if saved:
                obj.restore_objective_rows(saved["rows"], saved["identity"])
            for p in mb:
                nu, va = float.fromhex(p["nu_mb_raw_hex"]), float.fromhex(p["V_A_hex"])
                obj.register_catalog(nu, va)
                obj(nu, va)
            ranked = sorted(obj.rows.values(), key=lambda r:float(r["SKR"]), reverse=True)
            assert len(ranked) == len(mb)
            best, second = ranked[:2]
            old = old_best[distance]
            comparisons.append({"L_km":distance, "old_nu":old["available_best_nu"], "old_V_A":old["available_best_V_A"],
                "old_K":old["available_best_K"], "new_nu":best["nu_raw"], "new_V_A":best["V_A"],
                "I_AB":best["I_AB"], "beta_I_AB":best["beta_I_AB"], "chi_BE":best["chi_BE"],
                "new_K":best["SKR"], "delta_K":float(best["SKR"])-float(old["available_best_K"]), "MB_count":len(mb),
                "scope":"FINITE_EXACT_CATALOG_NUMERIC_MAXIMUM_NOT_CONTINUOUS_GLOBAL"})
            top_two.extend({"L_km":distance, "rank":rank, **r} for rank,r in enumerate((best,second),1))
            for nu,va in PAIRS:
                if source.candidate_from_payload(config,bank,"MB",nu,va) is not None:
                    new_rows.append(obj(nu,va))
            existing[str(distance)] = {"rows":list(obj.rows.values()), "identity":obj.objective_identity}
            identities.append({"L_km":distance, "identity":obj.objective_identity, "old_attestation":attestation})
            io.save_json(OUT / "objective_checkpoint.json", existing)
            io.write_csv(OUT / "old_vs_new_mb_skr.csv", comparisons)
            io.write_csv(OUT / "top_two_candidates.csv", top_two)
            if new_rows:
                io.write_csv(OUT / "new_pair_26distance_objectives.csv", new_rows)
            if run_ao:
                # Exact original full-sweep policy: four starts, then previous-distance winner.
                starts = [(f"nu_{nu:g}",nu,None) for nu in sweep.BASE_STARTS]
                if warm is not None:
                    starts.append(("warm_previous_distance", *warm))
                runs = [sweep.run_single_distance_ao(distance_km=distance, start_id=sid, start_nu=nu,
                    start_va=va, objective=obj, max_iterations=ao.MAX_AO_ITERATIONS) for sid,nu,va in starts]
                chosen = max((r for r in runs if r.get("final")), key=lambda r:float(r["final"]["SKR"]))
                final = chosen["final"]
                warm = (float(final["nu_raw"]),float(final["V_A"]))
                checks = [record_search(variable=variable, fixed=fixed, values=obj.catalog_values(variable,fixed), objective=obj)
                    for variable,fixed in (("V_A",warm[0]),("nu_raw",warm[1]))]
                complete = all(ao.coordinate_search_complete(s) for s in checks)
                status = chosen["status"]
                if status == "CONVERGED_NUMERICALLY" and not complete:
                    status = "STAGNATED_IN_EXACT_CATALOG"
                records.append({"L_km":distance,"nu_raw_star":warm[0],"V_A_star":warm[1],
                    "I_AB":final["I_AB"],"beta_I_AB":final["beta_I_AB"],"chi_BE":final["chi_BE"],"K":final["SKR"],
                    "catalog_K":best["SKR"],"matches_catalog_maximum":float(final["SKR"])==float(best["SKR"]),
                    "status":status,"local_coordinate_search_complete":complete,
                    "selected_start":chosen["start_id"],"missing_source_attempts":len(obj.source_missing),
                    "global_optimum_resolved":False,"execution":"FRESH_CACHE_ONLY_ORIGINAL_129_START_SWEEP"})
                runs_all.extend({"L_km":distance,**r} for r in runs)
                iterations.extend(row for r in runs for row in r["iterations"])
                io.write_csv(OUT / "alt_opt_recheck.csv", records)
                io.write_csv(OUT / "ao_iteration_history.csv", iterations)
                io.save_json(OUT / "cache_only_searches.json", searches)
                io.save_json(OUT / "cache_only_runs.json", runs_all)
            print(f"Exact catalog L={distance}: MB={len(mb)}, K={best['SKR']}, AO={run_ao}",flush=True)
    old_searches = json.loads((prior.DIAG / "cache_only_searches.json").read_text())
    newly_closed=[]
    if run_ao:
        for distance in sweep.DISTANCES_KM:
            before=[s for s in old_searches if s["L_km"]==distance][-2:]
            after=[s for s in searches if s["L_km"]==distance][-2:]
            for old,new in zip(before,after):
                newly_closed.append({"L_km":distance,"coordinate":new["variable"],"before_fixed":old["fixed"],
                    "after_fixed":new["fixed"],"same_slice":old["fixed"]==new["fixed"],
                    "before_status":old["status"],"after_status":new["status"],"boundary_status":new.get("boundary_status"),
                    "newly_numerically_closed":old["fixed"]==new["fixed"] and not ao.coordinate_search_complete(old) and ao.coordinate_search_complete(new)})
        io.write_csv(OUT / "coordinate_search_status_after_expansion.csv", newly_closed)
    report={"MB_count":len(mb),"distances_evaluated":len(comparisons),"new_source_objective_rows":len(new_rows),
        "improved_distances":[r["L_km"] for r in comparisons if r["delta_K"]>0],
        "largest_numeric_gain":max(r["delta_K"] for r in comparisons),"AO_rechecked":run_ao,
        "AO_matches_catalog":sum(r["matches_catalog_maximum"] for r in records),"AO_distances":len(records),
        "newly_closed_selected_searches":[r for r in newly_closed if r["newly_numerically_closed"]],
        "numerically_converged_distances":[r["L_km"] for r in records if r["status"]=="CONVERGED_NUMERICALLY"],
        "global_optimum_claimed":False,"total_objective_error_bound":"NOT_ESTABLISHED"}
    io.save_json(OUT / "postprocess_report.json", report)
    io.save_json(OUT / "objective_compatibility_manifest.json", identities)
    supervisor.verify_protected(OUT)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate",action="store_true")
    parser.add_argument("--ao",action="store_true")
    parser.add_argument("--execute-approved-three",action="store_true")
    args=parser.parse_args()
    if args.evaluate or args.ao:
        return evaluate(args.ao)
    if not args.execute_approved_three:
        parser.error("Explicit execute flag required")
    if (OUT / "source_generation_ledger.json").exists():
        raise SystemExit("Execution checkpoint already exists; never automatically retry")
    # Preserve all preflight bytes before replacing requested mutable result paths.
    snapshot=OUT / "preflight_snapshot"
    snapshot.mkdir()
    for p in list(OUT.iterdir()):
        if p.is_file():
            shutil.copy2(p,snapshot / p.name)
    manifest=json.loads((OUT / "input_manifest_before.json").read_text())
    manifest.update(io.raw_snapshot(list(snapshot.rglob("*"))+[Path(__file__),ROOT / "scripts/windows_sleep_safe_supervision.py"]))
    io.save_json(OUT / "protected_input_manifest.json",manifest)
    supervisor.verify_protected(OUT)
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES)==(1e-8,1e-6,6,4)
    preflight=json.loads((snapshot / "power_and_supervisor_preflight.json").read_text())
    assert preflight["status"] == "CURRENTLY_VERIFIED_PASS"
    points=sorted(io.read_csv(prior.PLAN / "selected_mb_candidates.csv"),key=lambda r:int(r["pilot_priority"]))
    assert tuple((float(p["nu_raw"]),float(p["V_A"])) for p in points)==PAIRS
    config=source.unconstrained_config()
    bank=source.load_source_payloads(config,SOURCE_DIRS)
    assert all(source.candidate_from_payload(config,bank,"MB",nu,va) is None for nu,va in PAIRS)
    ledger={"status":"AUTHORIZED_THREE_SERIAL_PROBES","attempts":[],"used_wall_seconds":0.,
        "total_compute_budget_seconds":10800.,"per_probe_timeout_seconds":3600.,"final_AO_cleanup_reserve_seconds":360.,
        "controller_pid":os.getpid(),"authorized_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "authorization":"Fresh explicit user approval all3; continue after timeout; never retry within this run",
        "source_method_precision_quadrature_MI_Holevo_ALT_OPT_changed":False}
    lease=safe.AwakeOnAC()
    start=time.monotonic()
    deadline=start+10800.
    controller_cpu_start=time.process_time()
    heartbeat_stop=threading.Event()
    def heartbeat():
        while not heartbeat_stop.wait(45):
            print(f"Serial expansion: wall={time.monotonic()-start:.1f}s/10800s; attempts saved={len(ledger['attempts'])}",flush=True)
    threading.Thread(target=heartbeat,daemon=True).start()
    original_supervisor=supervisor.supervised_probe
    def safe_delegate(command,timeout,log):
        # Delegate to original supervisor inside sleep wrapper; no recursive patch.
        with patch.object(supervisor,"supervised_probe",original_supervisor):
            return safe.supervised_process(command,timeout,log)
    receipts=[]
    error=None
    try:
        with lease:
            io.save_json(OUT / "active_power_preflight.json",{"status":"CURRENTLY_VERIFIED_PASS","lease":lease.receipt,
                "fresh_budget_confirmed":True,"total_seconds":10800,"probe_seconds":3600})
            io.save_json(OUT / "source_generation_ledger.json",ledger)
            for number,point in enumerate(points,1):
                limit=min(3600.,deadline-time.monotonic()-360.)
                if limit <= 10:
                    ledger["status"]="SOURCE_BUDGET_EXHAUSTED_RESERVED_FINAL_RECHECK"
                    break
                with patch.object(supervisor,"supervised_probe",safe_delegate):
                    record=supervisor.run_batch(OUT,{**point,"raw_current_cache_key":point["source_cache_key"]},limit,number,ledger)
                receipts.append(record["supervision"])
                io.write_csv(OUT / "probe_execution_ledger.csv",ledger["attempts"])
                io.write_csv(OUT / "new_exact_mb_sources.csv",[{k:r.get(k) for k in
                    ("batch","nu_raw","V_A","status","C","w","cache_key","wall_seconds","cpu_seconds","source_payload_verified")} for r in ledger["attempts"]])
                receipt=record["supervision"]
                reason=receipt["power_watch"]["abort_reason"]
                if not receipt["wall_limit_respected"] or reason not in (None,"ABSOLUTE_DEADLINE") or not receipt["no_watchdog_thread_remaining"]:
                    raise RuntimeError("Unsafe power/deadline supervision; stop entire campaign")
                if record["status"] not in ("COMPLETED_EXACT","TIMEOUT"):
                    raise RuntimeError("Serious exact/provenance/worker failure: "+record["status"])
                if record["status"]=="COMPLETED_EXACT":
                    with (OUT / f"postprocess_after_probe_{number}.log").open("w",encoding="utf-8") as log:
                        receipt=safe.supervised_process([sys.executable,"-X","utf8","-u",str(Path(__file__)),"--evaluate"],
                            max(1,deadline-time.monotonic()-15),log)
                    receipts.append(receipt)
                    io.save_json(OUT / f"postprocess_after_probe_{number}_supervision.json",receipt)
                    if receipt["returncode"]!=0 or not receipt["wall_limit_respected"]:
                        raise RuntimeError("Exact SKR postprocessing failed or exceeded deadline")
            if deadline-time.monotonic()>15:
                with (OUT / "final_cache_only_alt_opt.log").open("w",encoding="utf-8") as log:
                    receipt=safe.supervised_process([sys.executable,"-X","utf8","-u",str(Path(__file__)),"--ao"],
                        deadline-time.monotonic()-10,log)
                receipts.append(receipt)
                io.save_json(OUT / "final_AO_supervision.json",receipt)
                if receipt["returncode"]!=0 or not receipt["wall_limit_respected"]:
                    raise RuntimeError("Final cache-only AO incomplete within budget")
            else:
                raise RuntimeError("Total budget exhausted before final AO")
            ledger["status"]="THREE_PROBE_CAMPAIGN_FINISHED_WITH_FINITE_CATALOG_SCOPE"
    except BaseException as exc:
        error=repr(exc)
        ledger["status"]="STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET"
        print(error,flush=True)
    finally:
        heartbeat_stop.set()
        ledger.update(budget_session_wall_seconds=time.monotonic()-start,sleep_prevention=lease.receipt,
            total_job_cpu_seconds=sum(r.get("aggregate_cpu_seconds",0) for r in receipts),
            controller_cpu_seconds=time.process_time()-controller_cpu_start,supervision_receipts=receipts,error=error)
        ledger["total_CPU_seconds"]=ledger["total_job_cpu_seconds"]+ledger["controller_cpu_seconds"]
        ledger["wall_budget_respected"]=ledger["budget_session_wall_seconds"]<=10800
        io.save_json(OUT / "source_generation_ledger.json",ledger)
        outcome=json.loads((OUT / "postprocess_report.json").read_text()) if (OUT / "postprocess_report.json").exists() else None
        report={**ledger,"successful_probes":sum(r["status"]=="COMPLETED_EXACT" for r in ledger["attempts"]),
            "timeout_probes":sum(r["status"]=="TIMEOUT" for r in ledger["attempts"]),"postprocess":outcome,
            "protected_files_unchanged":supervisor.verify_protected(OUT),"publication":"NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
            "global_continuous_convergence_claimed":False}
        io.save_json(OUT / "run_report.json",report)
        io.save_json(OUT / "input_manifest_after.json",{n:io.digest(ROOT/n) for n in manifest})
        io.save_json(OUT / "sleep_prevention_final_receipt.json",lease.receipt)
        io.write_csv(OUT / "probe_execution_ledger.csv",ledger["attempts"])
        text=["# Sleep-safe three-probe exact expansion", "",ledger["status"],
            f"Successful={report['successful_probes']}; timeout={report['timeout_probes']}; attempts={len(ledger['attempts'])}.",
            f"Wall={ledger['budget_session_wall_seconds']}s/10800s; aggregate CPU={ledger['total_CPU_seconds']}s; wall compliance={ledger['wall_budget_respected']}.",
            f"Sleep lease={json.dumps(lease.receipt)}; error={error}.",f"Exact catalog/AO outcome={json.dumps(outcome)}.",
            "Original scientific formulas/source method/precision/quadrature/MI/Holevo/AO unchanged; no interpolation.",
            "Final AO uses original four starts and preceding-distance warm continuation (129 starts).",
            "360s reserved for final cache-only recheck/cleanup; final source limit may be shorter than3600s.",
            "Temporary request prevents idle sleep, not manual suspend/shutdown/critical power. No power plan modified.",
            "Finite exact catalog ranking only. Missing moments/open boundaries preclude continuous/global convergence.",
            f"Historical/preflight protected hashes unchanged={report['protected_files_unchanged']}."]
        # Report is an output artifact, not a source/config edit.
        (OUT / "run_report.md").write_text("\n".join(text)+"\n",encoding="utf-8")
        print(json.dumps({k:report[k] for k in ("status","successful_probes","timeout_probes","budget_session_wall_seconds","postprocess","error")}),flush=True)
    return 1 if error else 0


if __name__=="__main__":
    raise SystemExit(main())
