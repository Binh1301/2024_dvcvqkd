"""Resume the saved AO, sequential exact sources, durable precision checkpoints."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_ao_effective_channel_no_fading_noise_reference as d
OUT=ROOT/"results/ao_effective_channel_no_fading_noise_reference_continuation"
CONFIG=ROOT/"configs/ao_effective_channel_no_fading_noise_continuation.json"
ATTACHMENT=Path("C:/Users/HP/.codex/attachments/5c582d16-533e-4e84-a899-e8b95b5458f0/Pasted text.txt")
NEW=["scripts/continue_ao_effective_channel_no_fading_noise.py",
     "configs/ao_effective_channel_no_fading_noise_continuation.json",
     "tests/test_ao_no_fading_noise_continuation.py",
     "docs/AO_NO_FADING_NOISE_CONTINUATION_REPORT_VI.md"]


def save(path,value,exclusive=False):
    d.save(path,d.config_identity(value),exclusive=exclusive)


def check_prior():
    prior=d.read_json(d.OUT/"optimization_result.json")
    receipt=d.read_json(d.OUT/"final_validation.json")
    for name,digest in receipt["output_sha256"].items():
        if d.digest(ROOT/name)!=digest:raise ValueError("Prior result changed: "+name)
    for name,digest in receipt["producer_sha256"].items():
        if d.digest(ROOT/name)!=digest:raise ValueError("Prior producer changed: "+name)
    if d.digest(ROOT/"docs/AO_EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md")!=receipt["report_sha256"]:
        raise ValueError("Prior report changed")
    d.verify_protected(d.read_json(d.OUT/"startup_manifest.json"))
    if prior["status"]!="AO_RESOURCE_LIMITED" or len(prior["runs"])!=9:
        raise ValueError("Unexpected prior checkpoint or multistart roster")
    return prior


def matching_caches(points,config,excluded=()):
    from scripts.exact_cache_provenance import source_settings,verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble
    keys={(float(n).hex(),float(v).hex()) for n,v in points}
    matches=[];rejected=[]
    for directory in sorted((ROOT/"results").rglob("exact_source_cache")):
        if any(Path(p) in directory.parents for p in excluded):continue
        for path in sorted(directory.glob("*.json")):
            payload=d.read_json(path)
            if (payload.get("nu_mb_raw_hex"),payload.get("V_A_hex")) not in keys:continue
            try:
                verify_source_payload(payload,source_settings(config))
                n,v=float.fromhex(payload["nu_mb_raw_hex"]),float.fromhex(payload["V_A_hex"])
                ensemble=make_ensemble(config,"Uniform" if n==0 else "MB",n,v)
                if ensemble_hash(ensemble)!=payload["ensemble_hash"]:raise ValueError("Ensemble mismatch")
                matches.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=d.digest(path),nu_raw=n,VA=v))
            except Exception as error:
                rejected.append(dict(path=path.relative_to(ROOT).as_posix(),error=str(error)))
    return matches,rejected


def prepare():
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    prior=check_prior()
    OUT.mkdir(exist_ok=False)
    (OUT/"exact_source_cache").mkdir()
    (OUT/"precision_checkpoints").mkdir()
    settings=d.read_json(CONFIG)
    if (settings["exact_source_timeout_seconds"],settings["ao_continuation_budget_seconds"],
        settings["max_concurrent_exact_source_jobs"])!=(7200,43200,1):
        raise ValueError("Continuation limits differ from explicit user authorization")
    paths=[p for folder in ("src","scripts","configs","tests","results","docs",".agent")
           for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
           and OUT not in p.parents and p.relative_to(ROOT).as_posix() not in d.STATE+NEW]
    manifest=dict(protected_hashes={p.relative_to(ROOT).as_posix():d.digest(p) for p in sorted(paths)},
        branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),
        HEAD=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
        git_diff=subprocess.check_output(["git","diff"],cwd=ROOT).decode("utf-8"),
        state_before={n:(ROOT/n).read_text(encoding="utf-8") for n in d.STATE},
        attachment_sha256=d.digest(ATTACHMENT),config=settings,
        frozen_sha256=d.digest(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        frozen_expected="561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1",
        producers={n:d.digest(ROOT/n) for n in NEW[:3]})
    save(OUT/"startup_manifest.json",manifest,True)
    objective=d.Objective()
    points=[(a["nu_raw"],a["V_A"]) for a in prior["source_attempts"]]
    matches,rejected=matching_caches(points,objective.config,(OUT,))
    candidate=next(p for p in objective.payloads.values() if p["cache_key"]==prior["best_AO_MB"]["source_cache_key"])
    from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
    c=candidate_from_payload(objective.config,objective.payloads,"MB",.17,5.)
    regression=d.evaluate_authenticated(c,objective.moments,objective.config,manifest["protected_hashes"])
    residuals={k:regression[k]-prior["best_AO_MB"][k] for k in
               ("T_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3","I_AB","chi_BE","SKR")}
    if any(abs(v)>5e-12 for v in residuals.values()):raise ValueError("Continuation regression failed")
    identity=dict(previous_scientific_context=prior["scientific_context_hash"],
        previous_checkpoint_sha256=d.digest(d.OUT/"checkpoint.json"),
        previous_objectives_sha256=d.digest(d.OUT/"objective_evaluations.json"),
        config=settings,producers=manifest["producers"],attachment_sha256=manifest["attachment_sha256"])
    save(OUT/"continuation_identity.json",dict(identity=identity,sha256=d.hash_json(identity)),True)
    save(OUT/"preparation.json",dict(status="CURRENTLY_VERIFIED_PASS",previous_best=prior["best_AO_MB"],
        loaded_multistarts=[r for r in prior["runs"] if r["start"]["start_id"]!="best_MB_refinement"],
        previous_objective_rows=211,timed_out_probes=prior["source_attempts"],
        matching_complete_caches=matches,rejected_caches=rejected,
        previous_partial_state="NONE; old AP worker had no durable numeric checkpoint",
        new_partial_resume="Completed original precision rows, input/producer/runtime hash-bound",
        regression=regression,regression_residuals=residuals,
        timeout_audit=dict(old_controller_total=1800,old_per_sources=[720,480,600],
            original_inner_AP=3600,new_inner_AP=7200,new_outer_source=7200,new_total=43200,
            sequential_jobs=1,precision_unchanged=[1050,1250,1450]),
        protected_changes=d.verify_protected(manifest)),True)
    print("CONTINUATION_PREPARATION_PASS",len(paths),"protected; caches",len(matches),flush=True)


def extended_ap_run(original,command,args,kwargs,journal,timeout):
    """Change transport/deadline only; same binary64 request and original AP math."""
    original_worker=ROOT/"scripts/full_support_c4_worker.py"
    if len(command)>=2 and Path(command[1]).resolve()==original_worker.resolve():
        rewritten=[command[0],"-B",str(Path(__file__).resolve()),"--ap-worker",str(journal)]
        options=dict(kwargs,timeout=timeout)
        return original(rewritten,*args,**options)
    return original(command,*args,**kwargs)


def checkpointed_precision_row(original,p,z,digits,request,journal):
    import mpmath as mp
    producer=d.digest(ROOT/"scripts/full_support_c4_worker.py")
    identity=dict(request=request,producer_sha256=producer,mpmath_version=mp.__version__,
                  ambient_decimal_digits=mp.mp.dps,digits=digits)
    key=d.hash_json(identity);path=journal/(str(digits)+".json")
    if path.exists():
        saved=d.read_json(path)
        if saved["identity"]!=identity or saved["identity_sha256"]!=key or saved["row_sha256"]!=d.hash_json(saved["row"]):
            raise ValueError("Precision checkpoint provenance mismatch")
        return saved["row"]
    row=original(p,z,digits)
    save(path,dict(identity=identity,identity_sha256=key,row=row,row_sha256=d.hash_json(row),
         completed_utc=datetime.now(timezone.utc).isoformat()),True)
    return row


def ap_worker(journal):
    from scripts import full_support_c4_worker as worker
    raw=sys.stdin.read();request=json.loads(raw)
    if request["precision_ladder_decimal_digits"]!=[1050,1250,1450]:
        raise ValueError("Precision ladder mutation rejected")
    journal=Path(journal).resolve()
    if OUT not in journal.parents:raise ValueError("Precision journal outside continuation namespace")
    journal.mkdir(parents=True,exist_ok=True)
    save(journal/"request.json",request) if not (journal/"request.json").exists() else None
    if d.read_json(journal/"request.json")!=request:raise ValueError("Partial request changed")
    original=worker._row
    with patch.object(worker,"_row",lambda p,z,n:checkpointed_precision_row(original,p,z,n,request,journal)):
        sys.stdin=io.StringIO(raw)
        worker.main()


def source_worker(nu,va):
    import torch
    from scripts.run_exact_mb_test2 import ExactMBEvaluator
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config,make_ensemble
    from src.cvqkd import gram_moments
    torch.set_num_threads(1)
    settings=d.read_json(CONFIG);config=unconstrained_config()
    manifest=d.read_json(OUT/"startup_manifest.json")
    d.verify_protected(manifest)
    for name,expected in manifest["producers"].items():
        if d.digest(ROOT/name)!=expected:raise ValueError("Continuation producer changed")
    diagnostics=[]
    def observed(*args,**kwargs):
        result=gram_moments.c4_gram_source_moments(*args,**kwargs)
        diagnostics.extend(result.diagnostics)
        return result
    evaluator=ExactMBEvaluator(config,dict(T_eff=0.,epsilon_base=.0186,c_phi=0.),OUT,
        source_cache_dir=OUT/"exact_source_cache",source_evaluator=observed,
        allow_legacy_exact_import=False,crn_seeds=(),mi_samples=1)
    ensemble=make_ensemble(config,"Uniform" if nu==0 else "MB",nu,va)
    identity=evaluator._source_identity(ensemble,nu,va);key=d.hash_json(identity)
    journal=OUT/"precision_checkpoints"/key;journal.mkdir(exist_ok=True)
    original=gram_moments.subprocess.run
    started=time.monotonic()
    with patch.object(gram_moments.subprocess,"run",lambda command,*a,**kw:
         extended_ap_run(original,command,a,kw,journal,settings["exact_source_timeout_seconds"])):
        source=evaluator.source_moments(ensemble,nu,va)
    path=OUT/"exact_source_cache"/(key+".json")
    save(OUT/"source_result_{}.json".format(key),dict(source_path=path.relative_to(ROOT).as_posix(),
        source_sha256=d.digest(path),cache_key=key,C=source["C"],w=source["w"],
        source_runtime_seconds=time.monotonic()-started,diagnostics=diagnostics,
        partial_checkpoint_path=journal.relative_to(ROOT).as_posix()),True)


class ContinuationObjective(d.Objective):
    def __init__(self):
        super().__init__()
        self.prior=check_prior();self.prepared=d.read_json(OUT/"preparation.json")
        self.baseline=d.read_json(OUT/"startup_manifest.json")
        self.hashes=dict(self.baseline["protected_hashes"])
        self.runtime=d.read_json(CONFIG);self.lock=threading.RLock()
        self.continuation_context=d.read_json(OUT/"continuation_identity.json")["sha256"]
        self.rows={(r["nu_raw"].hex(),r["V_A"].hex()):r for r in d.read_json(d.OUT/"objective_evaluations.json")}
        self.attempts=[];self.requests=[];self.iterations=[];self.pending=None
        self.current=self.prior["best_AO_MB"];self.best=self.current;self.allow_new=True
        self.phase="COMPLETE_PREVIOUS_TIMEOUTS";self.status="RUNNING"
        self.monotonic_started=time.monotonic();self.elapsed_before=0.
        self.started_utc=datetime.now(timezone.utc);self.owner_pid=os.getpid()
        if (OUT/"checkpoint.json").exists():
            saved=d.read_json(OUT/"checkpoint.json")
            if saved["status"] in ("AO_CONVERGED_COORDINATE_LOCAL","AO_RESOURCE_LIMITED","AO_NUMERICAL_UNRESOLVED") and not saved.get("resume_allowed"):
                raise ValueError("Continuation finished; a new explicit run is required")
            from scripts.run_theta10_D55_alt_opt_closure_continuation import controller_alive
            if saved["owner_pid"]!=os.getpid() and controller_alive(saved["owner_pid"]):
                raise ValueError("Continuation checkpoint owner is still alive")
            self.started_utc=datetime.fromisoformat(saved["started_utc"])
            self.elapsed_before=max(saved["elapsed_seconds"],(datetime.now(timezone.utc)-self.started_utc).total_seconds())
            self.attempts=saved["source_attempts"];self.requests=saved["missing_requests"]
            self.iterations=saved["iterations"];self.current=saved["current"];self.phase=saved["phase"]
            self.pending=saved["pending_iteration"];self.best=saved["best_exact"]
            for a in self.attempts:
                if a["status"]=="RUNNING":a["status"]="INTERRUPTED_RESUMABLE"
            self.rows={(r["nu_raw"].hex(),r["V_A"].hex()):r for r in d.read_json(OUT/"objective_evaluations.json")}
        self.restore_overlay()
        for item in self.prepared["matching_complete_caches"]:
            self.adopt(ROOT/item["path"],item["sha256"],"REUSED_VALID_CACHE")
        if self.context_hash!=self.prior["scientific_context_hash"]:
            raise ValueError("Inherited scientific objective changed")
        for name,expected in self.baseline["producers"].items():
            if d.digest(ROOT/name)!=expected:raise ValueError("Continuation producer changed")

    def elapsed(self):
        return self.elapsed_before+time.monotonic()-self.monotonic_started

    def remaining(self):
        return self.runtime["ao_continuation_budget_seconds"]-self.elapsed()-self.runtime["finalization_reserve_seconds"]

    def adopt(self,path,expected,origin):
        from scripts.exact_cache_provenance import source_settings,verify_source_payload
        payload=d.read_json(path)
        if d.digest(path)!=expected:raise ValueError("Source bytes changed")
        payload["_provenance"]=verify_source_payload(payload,source_settings(self.config))
        payload["_path"]=path.relative_to(ROOT).as_posix()
        self.hashes[payload["_path"]]=expected
        self.payloads[payload["ensemble_hash"]]=payload
        n,v=float.fromhex(payload["nu_mb_raw_hex"]),float.fromhex(payload["V_A_hex"])
        self.points.add((n,v))
        return payload

    def restore_overlay(self):
        for path in (OUT/"exact_source_cache").glob("*.json"):
            self.adopt(path,d.digest(path),"RESUMED_LOCAL_EXACT")

    def catalog_values(self,variable,fixed):
        values=super().catalog_values(variable,fixed)
        if len(values)<3:
            center=self.current["V_A"] if variable=="V_A" else self.current["nu_raw"]
            global_values={v if variable=="V_A" else n for n,v in self.points}
            lower=max((x for x in global_values if 0<x<center),default=None)
            upper=min((x for x in global_values if x>center),default=None)
            values=sorted(set(values+[x for x in (lower,upper) if x is not None]))
        return values

    def checkpoint(self):
        if not hasattr(self,"lock"):return
        with self.lock:
            if self.rows:
                winner=max(self.rows.values(),key=lambda r:r["SKR"])
                if winner["SKR"]>self.best["SKR"]:self.best=winner
            precisions={p.parent.name:[int(q.stem) for q in p.parent.glob("*.json") if q.stem.isdigit()]
                        for p in (OUT/"precision_checkpoints").rglob("request.json")}
            record=dict(status=self.status,owner_pid=self.owner_pid,started_utc=self.started_utc.isoformat(),
                elapsed_seconds=self.elapsed(),continuation_context=self.continuation_context,
                inherited_scientific_context=self.context_hash,current=self.current,best_exact=self.best,
                phase=self.phase,pending_iteration=self.pending,iterations=self.iterations,
                source_attempts=self.attempts,missing_requests=self.requests,precision_checkpoints=precisions,
                loaded_prior_multistarts=8,restarted_multistarts=0,previous_best=self.prior["best_AO_MB"],
                resume_allowed=getattr(self,"resume_allowed",False))
            save(OUT/"checkpoint.json",record)
            save(OUT/"objective_evaluations.json",list(self.rows.values()))

    def generate(self,nu,va):
        from scripts.windows_sleep_safe_supervision import supervised_process
        from scripts.run_exact_mb_test2 import ExactMBEvaluator
        from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble
        remaining=self.remaining()
        if remaining<20:return False
        evaluator=ExactMBEvaluator(self.config,dict(T_eff=0.,epsilon_base=.0186,c_phi=0.),OUT,
            source_cache_dir=OUT/"exact_source_cache",allow_legacy_exact_import=False,crn_seeds=(),mi_samples=1)
        ensemble=make_ensemble(self.config,"Uniform" if nu==0 else "MB",nu,va)
        key=d.hash_json(evaluator._source_identity(ensemble,nu,va))
        used=sum(a.get("elapsed_seconds",0.) for a in self.attempts if a["nu_raw"]==nu and a["V_A"]==va)
        limit=min(self.runtime["exact_source_timeout_seconds"]-used,remaining)
        if limit<20:return False
        number=len(self.attempts)+1
        record=dict(attempt=number,nu_raw=nu,V_A=va,source_cache_key=key,
            status="RUNNING",phase=self.phase,deadline_seconds=limit,
            started_utc=datetime.now(timezone.utc).isoformat(),scientific_context=self.context_hash,
            continuation_context=self.continuation_context)
        with self.lock:self.attempts.append(record)
        self.checkpoint()
        print(f"EXACT_SOURCE {number}: nu={nu:.17g} VA={va:.17g}; outer<= {limit:.1f}s; inner=7200s",flush=True)
        with (OUT/f"source_attempt_{number}.log").open("x",encoding="utf-8") as log:
            receipt=supervised_process([sys.executable,"-B",str(Path(__file__).resolve()),
                     "--source-worker",str(nu),str(va)],limit,log)
        with self.lock:record.update(receipt)
        local=OUT/"exact_source_cache"/(key+".json")
        if local.is_file():
            payload=self.adopt(local,d.digest(local),"FRESH_EXACT_CONTINUATION")
            record.update(status="COMPLETED_EXACT",C=payload["C"],w=payload["w"],
                source_path=local.relative_to(ROOT).as_posix(),source_hash=d.digest(local),
                checkpoint_path=str((OUT/"checkpoint.json").relative_to(ROOT)))
        else:
            reason=receipt.get("power_watch",{}).get("abort_reason")
            record.update(status="TIMEOUT" if receipt["deadline_exceeded"] or receipt["returncode"]==124
                 else "ENVIRONMENT_INTERRUPTED" if reason else "SOURCE_FAILURE",precise_reason=reason)
        self.checkpoint()
        print("SOURCE_RESULT",number,record["status"],receipt["elapsed_seconds"],flush=True)
        if record["status"]=="ENVIRONMENT_INTERRUPTED":
            raise RuntimeError("BLOCKED_BY_ENVIRONMENT: "+str(record["precise_reason"]))
        return record["status"]=="COMPLETED_EXACT"

    def __call__(self,nu,va):
        from scripts.run_theta10_D55_alt_opt import ExactSourceUnavailable,ExactCandidateFailure
        from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
        nu,va=float(nu),float(va)
        if not math.isfinite(nu) or not math.isfinite(va) or nu<0 or va<=0:
            raise ValueError("nu>=0, VA>0 required")
        pair=(nu.hex(),va.hex())
        if pair in self.rows:return self.rows[pair]
        family="Uniform" if nu==0 else "MB"
        candidate=candidate_from_payload(self.config,self.payloads,family,nu,va)
        exhausted=any(a["nu_raw"]==nu and a["V_A"]==va and a["status"] in
            ("TIMEOUT","SOURCE_FAILURE") for a in self.attempts)
        if candidate is None and self.allow_new and not exhausted:
            if self.generate(nu,va):
                candidate=candidate_from_payload(self.config,self.payloads,family,nu,va)
        if candidate is None:
            with self.lock:self.requests.append(dict(nu_raw=nu,V_A=va,status="EXACT_SOURCE_MISSING",
                phase=self.phase,reason="Resource/transport interruption, not a negative or invalid SKR"))
            self.checkpoint()
            raise ExactSourceUnavailable(f"Missing exact source: {nu:.17g}, {va:.17g}")
        try:
            row=d.evaluate_authenticated(candidate,self.moments,self.config,self.hashes)
        except Exception as error:
            with self.lock:self.requests.append(dict(nu_raw=nu,V_A=va,status="NUMERICAL_FAILURE",error=str(error)))
            self.checkpoint()
            raise ExactCandidateFailure(str(error)) from error
        row.update(scientific_context_hash=self.context_hash,continuation_context=self.continuation_context,
            distance_km=21.9393102292,source_origin="CONTINUATION_EXACT" if OUT in
            (ROOT/row["source_path"]).parents else "PROTECTED_EXISTING")
        with self.lock:
            self.rows[pair]=row
            for a in self.attempts:
                if a["nu_raw"]==nu and a["V_A"]==va and a["status"]=="COMPLETED_EXACT":
                    a.update(I_AB=row["I_AB"],chi_BE=row["chi_BE"],SKR=row["SKR"])
        self.checkpoint()
        return row


def heartbeat(objective,stop):
    while not stop.wait(objective.runtime["heartbeat_seconds"]):
        objective.checkpoint()
        active=[a for a in objective.attempts if a["status"]=="RUNNING"]
        print("HEARTBEAT",datetime.now(timezone.utc).isoformat(),"phase",objective.phase,
              "active",[(a["nu_raw"],a["V_A"]) for a in active],
              "bestK",objective.best["SKR"],"remaining_s",round(objective.remaining(),1),flush=True)


def finish(objective):
    from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
    best=objective.best
    candidate=candidate_from_payload(objective.config,objective.payloads,"Uniform" if best["nu_raw"]==0 else "MB",
                                     best["nu_raw"],best["V_A"])
    fresh=d.evaluate_authenticated(candidate,objective.moments,objective.config,objective.hashes)
    if abs(fresh["SKR"]-best["SKR"])>5e-12:objective.status="AO_NUMERICAL_UNRESOLVED"
    result=dict(status=objective.status,previous_best=objective.prior["best_AO_MB"],best_exact=best,
        source_attempts=objective.attempts,iterations=objective.iterations,requests=objective.requests,
        current=objective.current,pending_iteration=objective.pending,elapsed_seconds=objective.elapsed(),
        delta_K=best["SKR"]-objective.prior["best_AO_MB"]["SKR"],
        relative_improvement_percent=100*(best["SKR"]-objective.prior["best_AO_MB"]["SKR"])/abs(objective.prior["best_AO_MB"]["SKR"]),
        inherited_scientific_context=objective.context_hash,continuation_context=objective.continuation_context,
        final_GH_check=fresh,restarted_multistarts=0,protected_changes=d.verify_protected(objective.baseline),
        certified_fading_security_lower_bound=False,global_optimum=False)
    save(OUT/"continuation_result.json",result)
    d.write_csv(OUT/"continuation_iterations.csv",objective.iterations)
    d.write_csv(OUT/"exact_source_results.csv",objective.attempts)
    objective.checkpoint()
    print("CONTINUATION_FINAL",objective.status,"best",best["nu_raw"],best["V_A"],best["SKR"],flush=True)


def execute():
    import torch
    from scripts.run_theta10_D55_alt_opt import ExactSourceUnavailable,ExactCandidateFailure,coordinate_search_complete
    torch.set_num_threads(1)
    objective=ContinuationObjective();stop=threading.Event()
    observer=threading.Thread(target=heartbeat,args=(objective,stop),daemon=True);observer.start()
    objective.checkpoint()
    try:
        if objective.phase=="COMPLETE_PREVIOUS_TIMEOUTS":
            for probe in objective.prepared["timed_out_probes"]:
                try:objective(probe["nu_raw"],probe["V_A"])
                except (ExactSourceUnavailable,ExactCandidateFailure):pass
            objective.phase="P1";objective.checkpoint()
        while objective.remaining()>0 and len(objective.iterations)<objective.runtime["max_continuation_iterations"]:
            rows_before=len(objective.rows)
            before=objective.current
            if objective.phase=="P1":
                p1=d.search_coordinate(objective,"V_A",before["nu_raw"],before)
                after=p1.get("best") or before
                if after["SKR"]<before["SKR"]:after=before
                objective.pending=dict(before=before,P1=p1,after_P1=after)
                objective.phase="P2";objective.checkpoint()
            else:
                before=objective.pending["before"]
                p1=objective.pending["P1"];after=objective.pending["after_P1"]
            p2=d.search_coordinate(objective,"nu_raw",after["V_A"],after)
            updated=p2.get("best") or after
            if updated["SKR"]<after["SKR"]:updated=after
            delta=updated["SKR"]-before["SKR"]
            parameter_change=max(abs(updated["nu_raw"]-before["nu_raw"]),abs(updated["V_A"]-before["V_A"]))
            closed=coordinate_search_complete(p1) and coordinate_search_complete(p2) and p2.get("zero_endpoint_status")=="EXACT_CHECKED"
            row=dict(iteration=len(objective.iterations)+1,nu_before=before["nu_raw"],VA_before=before["V_A"],
                K_before=before["SKR"],VA_after_P1=after["V_A"],K_after_P1=after["SKR"],
                nu_after_P2=updated["nu_raw"],K_after_P2=updated["SKR"],delta_K=delta,
                parameter_change=parameter_change,P1=p1,P2=p2,source_cache_key=updated["source_cache_key"],
                MI_integration_order=32,coordinate_brackets_complete=closed)
            objective.iterations.append(row);objective.current=updated
            objective.pending=None;objective.phase="P1";objective.checkpoint()
            print("CONTINUATION_AO",row["iteration"],updated["nu_raw"],updated["V_A"],updated["SKR"],
                  "delta",delta,"closed",closed,flush=True)
            if closed and abs(delta)<=1e-8 and parameter_change<=1e-6:
                objective.status="AO_CONVERGED_COORDINATE_LOCAL";break
            if objective.remaining()<20:
                objective.status="AO_RESOURCE_LIMITED";break
            # A complete repeated coordinate attempt with no new information cannot
            # resolve failed neighbors. Preserve uncertainty rather than busy-loop.
            if abs(delta)<=1e-8 and parameter_change<=1e-6 and not closed and len(objective.rows)==rows_before:
                objective.status="AO_RESOURCE_LIMITED" if any(a["status"]=="TIMEOUT" for a in objective.attempts) else "AO_BEST_EXACT_CANDIDATE"
                if any(a["status"]=="SOURCE_FAILURE" for a in objective.attempts):objective.status="AO_NUMERICAL_UNRESOLVED"
                break
        else:objective.status="AO_RESOURCE_LIMITED"
    except KeyboardInterrupt:
        objective.status="INTERRUPTED_RESUMABLE";objective.resume_allowed=True
        objective.checkpoint();raise
    except Exception as error:
        objective.status="AO_RESOURCE_LIMITED" if "BLOCKED_BY_ENVIRONMENT" in str(error) else "AO_NUMERICAL_UNRESOLVED"
        objective.resume_allowed="BLOCKED_BY_ENVIRONMENT" in str(error)
        save(OUT/"execution_failure.json",dict(error=str(error),resumable=objective.resume_allowed))
    finally:
        stop.set();observer.join(timeout=5)
        finish(objective)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--ap-worker")
    parser.add_argument("--source-worker",nargs=2,type=float)
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.ap_worker:ap_worker(args.ap_worker)
    elif args.source_worker:source_worker(*args.source_worker)
    else:execute()
