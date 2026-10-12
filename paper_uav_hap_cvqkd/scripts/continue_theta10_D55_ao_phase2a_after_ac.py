"""Resume only unattempted Phase2A sources; retain the original total deadline."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil
import sys
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_ao_phase2a as run


def unattempted(points,attempts):
    tried={r['cache_key'] for r in attempts}
    return [(i,p) for i,p in enumerate(points,1) if p['source_cache_key'] not in tried]


def process(with_ao):
    # Renderer-only numeric decoding. No original calculation or source CSV changes.
    original=run.prep.audit.make_plots
    def numeric_plots(runs,maxima,checkpoint,comparison):
        numeric=[{**r,'L_km':float(r['L_km']),'K':float(r['K'])} for r in comparison]
        return original(runs,maxima,checkpoint,numeric)
    with patch.object(run.prep.audit,'make_plots',numeric_plots):
        return run.process(with_ao)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--process',action='store_true');parser.add_argument('--ao',action='store_true')
    args=parser.parse_args()
    if args.process or args.ao:
        return process(args.ao)
    out,io,safe,supervisor=run.OUT,run.io,run.safe,run.supervisor
    supervisor.verify_protected(out)
    ledger=run.read(out/'source_generation_ledger.json')
    assert not supervisor.controller_alive(ledger['controller_pid']) and not run.prep.worker_inventory()
    assert ledger['status']=='STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET'
    assert ledger['authorization']['origin_monotonic']==126545.75 and ledger['absolute_deadline_monotonic']==137345.75
    deadline=ledger['absolute_deadline_monotonic']
    assert run.budget_limit(deadline,time.monotonic())>30,'Original authorization expired/insufficient reserve; no reset'
    points=unattempted(run.points(),ledger['attempts'])
    assert [i for i,p in points]==[2,3] and len(ledger['attempts'])==1,'Never retry source1 or duplicate an attempt'
    assert safe.safe_power(safe.WindowsPower().read()),'Safe AC is mandatory'
    archive=out/'checkpoint_before_AC_resume';archive.mkdir()
    for p in list(out.iterdir()):
        if p.is_file():shutil.copy2(p,archive/p.name)
    manifest=run.read(out/'protected_input_manifest.json')
    manifest.update(io.raw_snapshot([*archive.rglob('*'),*(out/'probe_results').rglob('*'),Path(__file__),ROOT/'tests/test_ao_phase2a_resume.py']))
    io.save_json(out/'protected_input_manifest.json',manifest)
    previous_cpu=ledger['controller_cpu_seconds'];cpu_start=time.process_time()
    receipts=list(ledger['supervision_receipts']);previous_pid=ledger['controller_pid']
    ledger.update(status='RESUMED_UNATTEMPTED_PHASE2A_RUNNING',controller_pid=os.getpid(),previous_controller_pid=previous_pid,
        resumed_utc=datetime.now(timezone.utc).isoformat(),budget_reset=False,resume_producer_sha256=io.digest(__file__),error=None)
    io.save_json(out/'source_generation_ledger.json',ledger)
    io.save_json(out/'phase_2A_report.json',{**ledger,'stage2':'RUNNING','new_budget_approved':True,
        'live_checkpoint':'source_generation_ledger.json and probe_results/*.json','old_stop_preserved':str(archive.relative_to(ROOT))})
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(45):
            print(f'Phase2A resumed: remaining={deadline-time.monotonic():.1f}s, saved attempts={len(ledger["attempts"])}',flush=True)
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
    original_supervisor=supervisor.supervised_probe
    def guarded(command,limit,log):
        with patch.object(supervisor,'supervised_probe',original_supervisor):
            return safe.supervised_process(command,limit,log)
    lease=safe.AwakeOnAC();error=None
    try:
        with lease:
            io.save_json(out/'resume_active_power_preflight.json',{'AC':safe.WindowsPower().read(),'lease':lease.receipt,
                'original_deadline_monotonic':deadline,'budget_reset':False})
            with patch.object(run.prep.native,'OUT',out):
                receipts.extend(run.prep.native.native_wall_preflight())
            for number,p in points:
                limit=run.budget_limit(deadline,time.monotonic())
                if limit<=10:break
                supervisor.verify_protected(out)
                assert safe.safe_power(safe.WindowsPower().read()) and not run.prep.worker_inventory()
                assert not (out/'probe_results'/f"{p['source_cache_key']}.json").exists()
                bank=run.source.load_source_payloads(run.source.unconstrained_config(),run.DIRS)
                assert run.source.candidate_from_payload(run.source.unconstrained_config(),bank,'MB',float(p['nu_raw']),float(p['V_A'])) is None
                with patch.object(supervisor,'supervised_probe',guarded):
                    record=supervisor.run_batch(out,p,limit,number,ledger)
                rec=record['supervision'];receipts.append(rec)
                io.write_csv(out/'execution_ledger.csv',[{k:r.get(k) for k in ('batch','nu_raw','V_A','cache_key','status','C','w','wall_seconds','cpu_seconds','timeout_seconds','source_payload_verified','error')} for r in ledger['attempts']])
                assert not run.prep.worker_inventory()
                if not rec['wall_limit_respected'] or not rec['no_watchdog_thread_remaining'] or rec['power_watch']['abort_reason'] not in (None,'ABSOLUTE_DEADLINE'):
                    raise RuntimeError('Unsafe power/deadline/worker cleanup; no automatic retry')
                if record['status'] not in ('COMPLETED_EXACT','TIMEOUT'):
                    raise RuntimeError('Serious exact-source failure: '+record['status'])
                if record['status']=='COMPLETED_EXACT':
                    with (out/f'objectives_after_probe_{number}.log').open('w',encoding='utf-8') as log:
                        rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--process'],deadline-time.monotonic()-60,log)
                    receipts.append(rec);io.save_json(out/f'objectives_after_probe_{number}_supervision.json',rec)
                    if rec['returncode']!=0 or not rec['wall_limit_respected']:raise RuntimeError('26distance exact objective/provenance processing failed')
            if deadline-time.monotonic()<=60:raise RuntimeError('Original total budget exhausted before final AO')
            with (out/'final_alt_opt.log').open('w',encoding='utf-8') as log:
                rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--ao'],deadline-time.monotonic()-45,log)
            receipts.append(rec);io.save_json(out/'final_AO_supervision.json',rec)
            if rec['returncode']!=0 or not rec['wall_limit_respected']:raise RuntimeError('Original AO/final validation failed')
            ledger['status']='PHASE2A_FINISHED_WITH_PRIOR_SAFETY_ABORT_FINITE_SCOPE'
    except BaseException as exc:
        error=repr(exc);ledger['status']='STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET';print(error,flush=True)
    finally:
        stop.set();thread.join(timeout=2)
        ledger.update(error=error,sleep_prevention=lease.receipt,supervision_receipts=receipts,
            budget_session_wall_seconds=time.monotonic()-ledger['authorization']['origin_monotonic'],
            controller_cpu_seconds=previous_cpu+time.process_time()-cpu_start,
            total_job_cpu_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in receipts),
            worker_cleanup_verified=not run.prep.worker_inventory(),wall_budget_respected=time.monotonic()<=deadline)
        ledger['total_CPU_seconds']=ledger['controller_cpu_seconds']+ledger['total_job_cpu_seconds']
        io.save_json(out/'source_generation_ledger.json',ledger)
        summary=run.save_report(ledger)
        io.save_json(out/'sleep_prevention_final_receipt.json',lease.receipt)
        io.save_json(out/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in manifest})
        print({k:summary[k] for k in ('status','successful_probes','timeout_probes','stopped_probes','not_run_probes','budget_session_wall_seconds','error')},flush=True)
    return 1 if error else 0


if __name__=='__main__':
    raise SystemExit(main())
