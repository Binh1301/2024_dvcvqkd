"""Audit saved Phase2A safety stop; no source/channel/objective/AO calculation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime,timezone
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_ao_phase2a as run


def main():
    out=run.OUT
    if (out/'safety_stop_audit.json').exists():
        raise SystemExit('Existing safety audit: preserve it')
    report=run.read(out/'phase_2A_report.json')
    ledger=run.read(out/'source_generation_ledger.json')
    assert not run.supervisor.controller_alive(ledger['controller_pid'])
    assert len(ledger['attempts'])==1 and ledger['attempts'][0]['status']=='PROCESS_FAILURE'
    attempt=ledger['attempts'][0]; receipt=attempt['supervision'];watch=receipt['power_watch']
    assert receipt['returncode']==125 and not receipt['deadline_exceeded'] and receipt['wall_limit_respected']
    assert watch['abort_reason']=='UNEXPECTED_SUSPEND_OR_SCHEDULER_GAP' and watch['last_power']['ac']==0
    assert watch['termination_request_succeeded'] and receipt['no_watchdog_thread_remaining']
    assert report['sleep_prevention']['released_verified'] and report['worker_cleanup_verified']
    assert not run.prep.worker_inventory()
    assert not list((out/'exact_source_cache').glob('*.json'))
    protected=run.supervisor.verify_protected(out)
    table=run.io.read_csv(run.prep.BASE/'optimized_skr_26_distances.csv')
    reference=next(r for r in table if float(r['L_km'])==run.prep.audit.REF)
    at22=next(r for r in table if float(r['L_km'])==22.)
    snapshot=out/'checkpoint_at_safety_stop';snapshot.mkdir()
    for name in ('phase_2A_report.json','phase_2A_report.md','source_generation_ledger.json','execution_ledger.csv','new_exact_source_moments.csv'):
        shutil.copy2(out/name,snapshot/name)
    checks=[]
    for pattern in ('test_ao_phase2a_execution.py','test_ao_phase2a_preparation.py','test_ao_numerical_optimum_audit.py',
        'test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
        assert time.monotonic()<ledger['absolute_deadline_monotonic']-20
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
        checks.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
    run.io.save_json(out/'safety_stop_regression_tests.json',checks)
    assert all(c['returncode']==0 for c in checks)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    assert run.supervisor.verify_protected(out)==protected
    power=run.safe.WindowsPower().read()
    audit={'status':'CURRENTLY_VERIFIED_PASS_FOR_SAFETY_STOP','execution_status':'BLOCKED_BY_ENVIRONMENT_AC_REQUIRED',
        'audit_utc':datetime.now(timezone.utc).isoformat(),'power_now':power,
        'abort_reason':watch['abort_reason'],'poll_gaps':watch['poll_gaps'],'AC_at_abort':watch['last_power']['ac'],
        'source_status':'SAFETY_ABORT_NO_SOURCE_MOMENTS','successful_probes':0,'timeout_probes':0,'safety_aborted_probes':1,'not_run_probes':2,
        'C':None,'w':None,'new_source_count':0,'new_objective_rows':0,'MB_catalog_count':146,
        'reference_stored_best':reference,'at22km_stored_best':at22,'SKR_improvement_assessment':'NOT_RUN_NO_NEW_VALID_SOURCE',
        'P1_new_refinement_steps':0,'P2_new_refinement_steps':0,'new_closed_directions':0,
        'AO_rechecked':False,'last_validated_AO_matches':26,'last_validated_AO_scope':'PREVIOUS146_CATALOG_NOT_A_FRESH_RECHECK',
        'phase2B_executed':False,'hard_source_necessity':'BASELINE_DEPENDENCY_UNCHANGED_NO_POST_EXPANSION_DECISION',
        'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','continuous_convergence':False,'global_optimum':False,
        'probe_wall_seconds':attempt['wall_seconds'],'probe_Job_CPU_seconds':attempt['cpu_seconds'],
        'execution_wall_seconds':report['budget_session_wall_seconds'],'execution_measured_CPU_seconds':report['total_CPU_seconds'],
        'audit_elapsed_from_authorization_seconds':time.monotonic()-ledger['authorization']['origin_monotonic'],
        'remaining_original_budget_seconds':ledger['absolute_deadline_monotonic']-time.monotonic(),
        'original_deadline_monotonic':ledger['absolute_deadline_monotonic'],'budget_reset':False,
        'CPU_scope':'Recorded controller plus supervised Job CPU; setup and separate audit/tests CPU not fully included',
        'all_workers_terminated':True,'sleep_restored':True,'no_watchdog_threads':True,'protected_files_unchanged':protected,
        'tests':'CURRENTLY_VERIFIED_PASS','git_diff_check':'CURRENTLY_VERIFIED_PASS','no_interpolation':True,
        'producer_sha256':run.io.digest(__file__),'executed_wrapper_sha256':run.io.digest(run.__file__),
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','frozen_spec_discrepancy':'PREEXISTING_UNCHANGED'}
    run.io.save_json(out/'safety_stop_audit.json',audit)
    lines=['# Phase2A safety-stop audit','',audit['status'],'',
        'Watchdog return125 on unexpected15.578s suspend/scheduler gap; lastAC0. Actual suspend vs scheduler delay is not distinguished.',
        'This is a SAFETY_ABORT, not timeout or numerical source failure. No fullC,w obtained. RawPROCESS_FAILURE retained.',
        'Successful0/timeout0/safetyabort1/notrun2. No newsource/objective or AO calculation after unsafe stop.',
        f"Probe wall={attempt['wall_seconds']}s, JobCPU={attempt['cpu_seconds']}s; executionwall={report['budget_session_wall_seconds']}s/10800s, measuredCPU={report['total_CPU_seconds']}s.",
        'CPU scope excludes setup/separate audit/test CPU; execution wall includes setup/preflight and stop cleanup.',
        f"Allworkers stopped; Sleepprevention restored; ACnow={power['ac']}; {protected} protectedhashes unchanged.",
        '', '## Requested final conclusions','',
        '1.0 successful sources,0timeouts,1safetyabort (probe1),2unattempted (probe2/3).',
        '2.No new exactC,w; unavailable values stayblank/None, never approximated.',
        '3.Catalog remains146. Stored reference(.165,5.5),K=.07798099387393764;22km(.165,5.475),K=.07661740491526092.',
        '4.No newSKR; improvement assessmentNOT_RUN, not a computed zero-gain optimization.',
        '5.P1 advanced0, P2 advanced0 new refinement steps.',
        '6.0 newlycompletedcoordinate directions; baseline directions remainincomplete.',
        '7.FreshAO/catalog comparisonNOT_RUN. Lastvalidated146catalog agreement26/26 remains prior evidence only.',
        '8.Hard(.16375,5.5) remains a baselineP2 dependency; Phase2A cannot yet decide post-expansion necessity. Phase2B never executed.',
        '9.Runtime/safety above; currentregressiontests anddiffcheckPASS. Sourceworker/controllerdead; no backgroundworker.',
        '', '## Continuation boundary','',
        'Keep originalauthorization origin11:46:13.577171Z/deadline14:46:13.577171Z. Do not reset the3h budget.',
        'Require physically reconnectedstableAC and freshnativepreflight before considering onlyunattemptedprobes2/3 within remainingbudget.',
        'Neverautomaticallyretryabortedprobe1; neverrunexcludedhardPhase2B or additionalAP. If originalbudget expires, require freshauthority.',
        'No reliable continuous/numerical/globaloptimum claimed; sourcecoverage, numericalaccuracy and boundaries remain unresolved.',
        'No scientificmodel/APprecision/quadrature/MI/Holevo/AO/threshold/lifecycle change. Olderresults/preflight/runreceipt preserved.']
    text='\n'.join(lines)+'\n'
    (out/'safety_stop_audit.md').write_text(text,encoding='utf-8')
    (out/'phase_2A_report.md').write_text(text,encoding='utf-8')
    run.io.save_json(out/'phase_2A_report.json',{**report,'safety_stop_audit':audit,'execution_classification':'SAFETY_ABORT',
        'new_budget_approved':True,'stage2':'STOPPED_BLOCKED_BY_ENVIRONMENT_AC_REQUIRED','fresh_AO_validation':'NOT_RUN'})
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    main()
