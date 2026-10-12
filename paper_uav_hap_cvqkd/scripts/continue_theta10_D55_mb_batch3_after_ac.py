"""Resume unattempted Batch3 points only, under the original absolute deadline."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import uuid
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_mb_batch3 as run

OUT, io, safe, supervisor = run.OUT, run.io, run.safe, run.supervisor


def unattempted_points(points, attempts):
    tried = {r['cache_key'] for r in attempts}
    return [(i,p) for i,p in enumerate(points,1) if p['raw_current_cache_key'] not in tried]


def probe_limit(deadline_monotonic, current_monotonic):
    return min(3600., deadline_monotonic-current_monotonic-480.)


def native_wall_preflight():
    """Same supervisor, CPU-busy parent + idle live child to isolate wall deadline."""
    receipts=[]
    for limit,tree in ((2.,False),(4.,True)):
        marker='batch3_resume_wall_'+uuid.uuid4().hex
        code='while True: pass'
        if tree:
            code="import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)',sys.argv[1]]); print('CHILD_PID='+str(p.pid),flush=True); exec('while True: pass')"
        with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as log:
            rec=safe.supervised_process([sys.executable,'-B','-c',code,marker],limit,log)
            log.seek(0)
            rec['dummy_log']=log.read()
        io.save_json(OUT/'resume_native_wall_preflight.json',{'status':'PREFLIGHT_RUNNING','dummy_jobs':receipts+[rec]})
        assert rec['returncode']==124 and rec['deadline_exceeded'],rec
        assert rec['wall_limit_respected'] and rec['no_watchdog_thread_remaining'],rec
        assert rec['sleep_prevention']['active_verified'] and rec['sleep_prevention']['released_verified']
        if tree:
            assert 'CHILD_PID=' in rec['dummy_log']
        command="$n=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*"+marker+"*'}).Count; if($n -ne 0){throw 'Dummy tree remains'}; 'CLEAN'"
        check=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
        assert check.stdout.strip()=='CLEAN'
        rec['worker_cleanup_verified']=True
        rec['dummy_child_role']='ALIVE_IDLE_DESCENDANT' if tree else 'NO_DESCENDANT'
        receipts.append(rec)
    io.save_json(OUT/'resume_native_wall_preflight.json',{'status':'CURRENTLY_VERIFIED_PASS','dummy_jobs':receipts,
        'original_supervisor_unchanged':True,'CPU_guard_still_enabled':True,
        'reason':'Isolate wall deadline with one busy parent and live idle child; earlier two-busy-process test hit aggregate Job CPU limit first.',
        'Microsoft_reference':'https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information'})
    return receipts


def main():
    supervisor.verify_protected(OUT)
    ledger = json.loads((OUT/'source_generation_ledger.json').read_text())
    assert not supervisor.controller_alive(ledger['controller_pid']), 'Controller is still active'
    assert ledger['status'] == 'STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET'
    origin = datetime.strptime(ledger['authorization_session_origin_utc'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    absolute_deadline = origin+timedelta(seconds=10800)
    remaining = (absolute_deadline-datetime.now(timezone.utc)).total_seconds()
    assert remaining > 495, 'Original authorization expired or lacks finalization reserve; do not reset budget'
    deadline = time.monotonic()+remaining
    points = unattempted_points(run.points(), ledger['attempts'])
    assert [i for i,p in points] == [2,3], 'Only approved unattempted probes2/3 may resume'
    assert safe.safe_power(safe.WindowsPower().read()), 'Connected safe AC power is required'
    archive = OUT/'checkpoint_before_AC_resume_wall_preflight'
    archive.mkdir()  # Existence rejects accidental duplicate resume.
    for path in list(OUT.iterdir()):
        if path.is_file():
            shutil.copy2(path,archive/path.name)
    manifest = json.loads((OUT/'protected_input_manifest.json').read_text())
    manifest.update(io.raw_snapshot([*archive.rglob('*'),*(OUT/'probe_results').rglob('*'),Path(__file__)]))
    io.save_json(OUT/'protected_input_manifest.json',manifest)
    supervisor.verify_protected(OUT)
    # Preserve and account native preflight measurements saved by the previous
    # failed assertion. No real probe was attempted by that resume.
    preflight_failed=json.loads((archive/'native_job_sleep_preflight.json').read_text())
    recovered_dummy_receipts=preflight_failed.get('dummy_jobs',[])
    previous_measured_CPU = ledger['total_CPU_seconds']
    previous_controller_CPU = ledger['controller_cpu_seconds']
    receipts = list(ledger['supervision_receipts'])+recovered_dummy_receipts
    start = time.monotonic()
    cpu_start = time.process_time()
    lease = safe.AwakeOnAC()
    ledger.update(status='BATCH3_RESUMED_UNATTEMPTED_PROBES_RUNNING',controller_pid=os.getpid(),
        resumed_utc=datetime.now(timezone.utc).isoformat(),
        prior_failed_resume_preflight='Preserved;0 AP attempts, aggregate CPU quota ended two-busy-process dummy',
        recovered_failed_dummy_Job_CPU_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in recovered_dummy_receipts),resume_producer_sha256=io.digest(__file__),
        original_absolute_deadline_utc=absolute_deadline.isoformat(),budget_reset=False)
    stop = threading.Event()
    def heartbeat():
        while not stop.wait(45):
            print(f'Batch3 resumed: remaining={deadline-time.monotonic():.1f}s, saved attempts={len(ledger["attempts"])}',flush=True)
    threading.Thread(target=heartbeat,daemon=True).start()
    original_supervisor = supervisor.supervised_probe
    def guarded(command,timeout,log):
        with patch.object(supervisor,'supervised_probe',original_supervisor):
            return safe.supervised_process(command,timeout,log)
    error = None
    try:
        with lease:
            io.save_json(OUT/'resume_active_power_preflight.json',{'status':'CURRENTLY_VERIFIED_PASS',
                'lease':lease.receipt,'original_absolute_deadline_utc':absolute_deadline.isoformat(),'budget_reset':False})
            io.save_json(OUT/'source_generation_ledger.json',ledger)
            receipts.extend(native_wall_preflight())
            for number,point in points:
                limit = probe_limit(deadline,time.monotonic())
                if limit <= 10:
                    break
                assert not (OUT/'probe_results'/f"{point['raw_current_cache_key']}.json").exists()
                with patch.object(supervisor,'supervised_probe',guarded):
                    record = supervisor.run_batch(OUT,point,limit,number,ledger)
                rec = record['supervision']
                receipts.append(rec)
                io.write_csv(OUT/'probe_execution_ledger.csv',[{k:r.get(k) for k in
                    ('batch','nu_raw','V_A','cache_key','status','C','w','wall_seconds','cpu_seconds',
                     'timeout_seconds','source_payload_verified','error')} for r in ledger['attempts']])
                io.write_csv(OUT/'new_exact_mb_sources.csv',[{k:r.get(k) for k in
                    ('batch','nu_raw','V_A','C','w','cache_key','status','source_payload_verified')} for r in ledger['attempts']])
                if not rec['wall_limit_respected'] or rec['power_watch']['abort_reason'] not in (None,'ABSOLUTE_DEADLINE') or not rec['no_watchdog_thread_remaining']:
                    raise RuntimeError('Unsafe power/deadline or cleanup during resumed probe')
                if record['status'] not in ('COMPLETED_EXACT','TIMEOUT'):
                    raise RuntimeError('Serious source/provenance failure: '+record['status'])
                if record['status'] == 'COMPLETED_EXACT':
                    with (OUT/f'objectives_after_probe_{number}.log').open('w',encoding='utf-8') as log:
                        rec = safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(run.__file__)),
                            '--evaluate'],deadline-time.monotonic()-15,log)
                    receipts.append(rec)
                    io.save_json(OUT/f'objectives_after_probe_{number}_supervision.json',rec)
                    if rec['returncode'] != 0 or not rec['wall_limit_respected']:
                        raise RuntimeError('Exact objective expansion failed or exceeded original deadline')
                    run.reassess([p for i,p in points if i>number],number)
            if deadline-time.monotonic() <= 15:
                raise RuntimeError('Original deadline exhausted before final cache-only AO')
            with (OUT/'final_alt_opt.log').open('w',encoding='utf-8') as log:
                rec = safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(run.__file__)),'--ao'],
                    deadline-time.monotonic()-10,log)
            receipts.append(rec)
            io.save_json(OUT/'final_AO_supervision.json',rec)
            if rec['returncode'] != 0 or not rec['wall_limit_respected']:
                raise RuntimeError('Final original AO failed or exceeded original deadline')
            ledger['status'] = 'BATCH3_FINISHED_WITH_POWER_ABORT_AND_FINITE_CATALOG_SCOPE'
    except BaseException as exc:
        error = repr(exc)
        ledger['status'] = 'STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET'
        print(error,flush=True)
    finally:
        stop.set()
        ledger.update(error=error,budget_session_wall_seconds=(datetime.now(timezone.utc)-origin).total_seconds(),
            resume_wall_seconds=time.monotonic()-start,sleep_prevention=lease.receipt,supervision_receipts=receipts,
            controller_cpu_seconds=previous_controller_CPU+time.process_time()-cpu_start,
            total_job_cpu_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in receipts))
        ledger['total_CPU_seconds']=ledger['total_job_cpu_seconds']+ledger['controller_cpu_seconds']
        ledger['wall_budget_respected']=ledger['budget_session_wall_seconds']<=10800
        ledger['previous_measured_current_campaign_CPU_seconds']=previous_measured_CPU
        io.save_json(OUT/'source_generation_ledger.json',ledger)
        result=json.loads((OUT/'postprocess_report.json').read_text()) if (OUT/'postprocess_report.json').exists() else None
        report={**ledger,'successful_probes':sum(r['status']=='COMPLETED_EXACT' for r in ledger['attempts']),
            'timeout_probes':sum(r['status']=='TIMEOUT' for r in ledger['attempts']),
            'power_aborted_probes':sum(r.get('supervision',{}).get('power_watch',{}).get('abort_reason')=='AC_LOST_OR_CRITICAL_BATTERY' for r in ledger['attempts']),
            'postprocess':result,'protected_files_unchanged':supervisor.verify_protected(OUT),
            'numerical_ranking_status':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED',
            'scientific_implementation_changed':False,'no_interpolation':True,
            'publication':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','continuous_global_optimality':False,
            'frozen_spec_discrepancy':'PREEXISTING_UNCHANGED'}
        io.save_json(OUT/'run_report.json',report)
        io.save_json(OUT/'sleep_prevention_final_receipt.json',lease.receipt)
        io.save_json(OUT/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in manifest})
        run.render_report(report)
        print(json.dumps({k:report[k] for k in ('status','successful_probes','timeout_probes','power_aborted_probes',
              'budget_session_wall_seconds','postprocess','error')}),flush=True)
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
