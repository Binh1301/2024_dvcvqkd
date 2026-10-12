"""Saved-record final failure audit, dummy tests only; never launches AP/objectives."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.diagnose_theta10_D55_source_bottlenecks import clean,rows,digest
from scripts.overnight_source_observer import atomic_json

OUT=ROOT/'results/theta10_D55_ao_numerical_optimum_validation/overnight_ao_run'


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def main():
    assert not (OUT/'production_failure_audit.json').exists(),'Preserve completed failure audit'
    raw=read(OUT/'ao_overnight_report.json');ledger=read(OUT/'source_generation_ledger.json')
    assert len(ledger['attempts'])==1 and ledger['attempts'][0]['status']=='NUMERICAL_FAILURE'
    assert "module 'mpmath' has no attribute 'dps'" in ledger['attempts'][0]['error']
    assert ledger['worker_cleanup_verified'] and ledger['sleep_prevention']['released_verified']
    # Original executed producers/receipts remain unchanged and hash-bound.
    for name in ('ao_overnight_report.json','ao_overnight_report.md','profiling_fix_audit.md','profiling_stage_summary.csv'):
        shutil.copy2(OUT/name,OUT/('raw_before_failure_audit_'+name))
    manifest=read(OUT/'protected_input_manifest.json')
    for name,expected in manifest.items():assert digest(ROOT/name)==expected,name
    post=read(OUT/'postprocess_report.json');assert post['MB_count']==147 and post['new_metric_rows']==0
    compared=rows(OUT/'old_vs_new_optimization.csv')
    assert len(compared)==26 and all(float(r['delta_K'])==0 and r['AO_matches_catalog']=='True' for r in compared)
    verified=rows(OUT/'independent_catalog_verification.csv')
    assert len(verified)==26 and all(r['AO_matches_catalog']=='True' and int(r['rows'])==147 for r in verified)
    tests=[]
    patterns=('test_overnight_observer_integration.py','test_overnight_source_observer.py',
       'test_source_bottleneck_diagnostic.py','test_ao_phase2a_execution.py','test_ao_phase2a_preparation.py',
       'test_ao_phase2a_resume.py','test_ao_numerical_optimum_audit.py',
       'test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py')
    for pattern in patterns:
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],
                cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        tests.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
        assert done.returncode==0,tests[-1]
    atomic_json(OUT/'final_regression_tests.json',tests)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    command="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--probe|--profile-worker|full_support_c4_worker\\.py|overnight_source_observer.*--ap|run_theta10_D55_overnight_ao\\.py.*--execute'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
    proc=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    assert proc.stdout.strip() in ('','[]','null'),proc.stdout
    after={name:digest(ROOT/name) for name in manifest};assert after==manifest
    atomic_json(OUT/'input_manifest_after_final_audit.json',after)
    count=sum(int(m.group(1)) for r in tests for m in re.finditer(r'^Ran (\d+) tests?',r['output'],re.M))
    runs=read(OUT/'cache_only_runs.json')
    starts=[]
    for r in runs:
        if r['L_km'] in (21.9393102292,22.):
            best=next(row for row in compared if float(row['L_km'])==r['L_km'])
            starts.append({'L_km':r['L_km'],'start_id':r['start_id'],'nu_raw':r['final']['nu_raw'],
              'V_A':r['final']['V_A'],'K':r['final']['SKR'],'status':r['status'],
              'matches_finite_catalog':r['final']['SKR']==float(best['new_K']),
              'last_missing':r['iterations'][-1]['numerical_warning']})
    authority=read(OUT/'execution_authorization.json')
    conclusions=[
      'Snapshot-disable bug repaired/dummy-tested; production stage metadata getter failed; v2 fixes module.mp.dps and passes real-module dummy integration, NOT real AP validation.',
      'No full-run AP coverage. Only two start/exception snapshots ~0.016s, no original AP Gram/eighe/LU execution completed. Detailed call profiling not used.',
      'BOTTLENECK_NOT_LOCALIZED. This attempt cannot localize expensive C,w stages; metadata AttributeError is an instrumentation root cause, not numerical impossibility.',
      '0 successful AP,0 timeouts,0 AC/watchdog safety-aborts,1 INSTRUMENTATION_FAILURE attempt A,3 not run. No retry or later AP after observer failure.',
      'No new valid C,w; none inferred or interpolated.',
      'Compatible MB catalog unchanged147, stored exact objectives3822.',
      'No best SKR improvement at26/26 distances; every exact deltaK0.',
      'Reference(.165,5.5),K=.07798099387393764;22km(.165,5.475),K=.07661740491526092 remain finite maxima.',
      'P1 unchanged[5.4875,5.5125], missingVA5.49375/5.50625,0 complete new paired stages.',
      'P2 unchanged[.1625,.16562500000000002], missingnu.16375/.16531250000000003,0 complete new paired stages.',
      '0 genuinely completed selected coordinate searches; incomplete calls are not convergence.',
      'Fresh genuine originalAO129starts/283iterations and independent147-row restoration match catalog26/26 BEFORE failed A.',
      '4/5 starts match each priority distance;nu0=.8 remains(.4,3.0) with open boundaries/missing(.4,1.5)/(.2,3.0), not proof of a separate continuous basin.',
      'Missing source moments, open/remote boundary coverage, strictnu>0 versusnu>=0, inner4 cap and earlier-unresolved latch prevent convergence claim. Stable K alone insufficient.',
      'No totalK numerical error bound. Bit-exact saved repeats/provenance do not establish accuracy of tiny ranking gaps or all displayed digits.',
      'One valid source gives evidence; current complete paired steps on both fixed reference slices need four missing pairsA/B/C/D. Conditional fixed-incumbent14P1/12P2 halvings remain, not guaranteed.',
      'Stop AP after this observability failure per user instruction. Versioned v2 correction is dummy-tested only; preserve failed attempt. A new explicit retry/scope authorization is needed before production continuation; no reset or auto-retry now.'
    ]
    report={**raw,'status':'OVERNIGHT_STOPPED_INSTRUMENTATION_FAILURE_CACHE_ONLY_COMPLETE',
       'production_failure_classification':'INSTRUMENTATION_FAILURE_NOT_MATHEMATICAL_NUMERICAL_FAILURE',
       'raw_status_preserved':'NUMERICAL_FAILURE','first_attempt_label':'A',
       'AP_attempts':1,'successful_probes':0,'timeout_probes':0,'safety_aborted_probes':0,
       'instrumentation_failed_probes':1,'not_run_probes':3,'new_exact_sources':0,'new_exact_SKR_rows':0,
       'profile_snapshot_disable_bug_dummy_repaired':True,'stage_wrapper_v1_failed':True,
       'stage_wrapper_v2_dummy_fixed':True,'stage_wrapper_v2_AP_run':'NOT_RUN',
       'full_run_AP_profile_coverage':False,'source_bottleneck_status':'BOTTLENECK_NOT_LOCALIZED',
       'all_17_conclusions':conclusions,'priority_multistart_actual_results':starts,
       'final_test_count':count,'final_tests':'CURRENTLY_VERIFIED_PASS','git_diff_check':'CURRENTLY_VERIFIED_PASS',
       'protected_hashes_unchanged':len(manifest),'no_orphan_AP_or_controller':True,
       'final_audit_utc':datetime.now(timezone.utc).isoformat(),
       'total_wall_through_final_audit_seconds':time.monotonic()-authority['origin_monotonic'],
       'final_audit_before_absolute_deadline':time.monotonic()<=authority['deadline_monotonic'],
       'recorded_CPU_scope':'Controller plus actual source/objective/AO Jobs; independent repair/preflight/final-audit/tests outside Jobs not all captured',
       'executed_controller_sha256':digest(ROOT/'scripts/run_theta10_D55_overnight_ao.py'),
       'executed_failed_observer_sha256':digest(ROOT/'scripts/overnight_source_observer.py'),
       'dummy_corrected_observer_v2_sha256':digest(ROOT/'scripts/overnight_source_observer_v2.py'),
       'source_retry_or_continuation':'NOT_RUN_AFTER_INSTRUMENTATION_FAILURE'}
    atomic_json(OUT/'ao_overnight_report.json',clean(report))
    atomic_json(OUT/'production_failure_audit.json',clean({k:report[k] for k in ('status','final_test_count',
        'protected_hashes_unchanged','total_wall_through_final_audit_seconds','final_audit_before_absolute_deadline',
        'production_failure_classification','executed_controller_sha256','executed_failed_observer_sha256',
        'dummy_corrected_observer_v2_sha256','no_orphan_AP_or_controller')}))
    lines=['# Overnight AO run: stopped observer failure, cache-only handoff','',report['status'],'',
       'The first production observer was defective. The dummy preflight39 tests did not cover its mpmath-module precision getter; this was an implementation/testing gap, not an environmental or mathematical source failure.',
       'A launched once, stopped after3.438s wall/3.234375s aggregateJobCPU with AttributeError before original AP Gram construction. No valid C,w. B/C/D NOT_RUN; failed A not retried.',
       'Executed producers/raw receipts/raw_before_failure_audit_* preserved. Versioned v2 accesses module.mp.dps; real-module1050/1250/1450 DUMMY operations prove wrappers preserve call/arguments/results/precision/restoration; no real AP run of v2.',
       '', '## Seventeen required conclusions','']
    lines += [f'{i}. {text}' for i,text in enumerate(conclusions,1)]
    lines += ['', '## Actual priority starts','', '| L km | start | nu | VA | K | status | catalog match |',
       '|---|---|---|---|---|---|---|']
    lines += [f"|{r['L_km']}|{r['start_id']}|{r['nu_raw']}|{r['V_A']}|{r['K']}|{r['status']}|{r['matches_finite_catalog']}|" for r in starts]
    lines += ['', '## Validation, time and safety','',
       f"Final{count} regression tests PASS;{len(manifest)} protected hashes unchanged; git diff --check PASS.",
       f"Controller wall including repair={ledger['wall_seconds_including_repair']}s; total through final audit={report['total_wall_through_final_audit_seconds']}s/28800.",
       f"Recorded controller+JobCPU={ledger['recorded_total_CPU_seconds']}s; excludes independent repair/preflight/final-audit/test CPU. Absolute deadline{authority['deadline_utc']} never reset.",
       'AC1/no recorded gap throughout failed A; native Job cleanup verified, outerSleep restored2147483648, no AP/controller remains. No permanent power-plan change.',
       'No unauthorized scientific/AO/precision/quadrature/MI/Holevo/provenance change, no interpolation. Original frozen historical-hash discrepancy unchanged; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.',
       '', '## Artifacts and figure scope','',
       'All17 requested files exist. exact_skr_26_distances.csv explicitly empty/new-source NOT_RUN header; optimized_skr_26_distances.csv has26 actual baseline rechecked AO selections.',
       'ao_multistart_history.csv contains283 genuine iterations/129starts; independent_catalog_verification.csv verifies26 matrices. P1/P2 traces and55 remaining dependencies retain exact values.',
       'Four requested300dpiPNG/vectorPDF pairs are genuine baseline-cache AO data, NOT new-source refinement or convergence. Parameter-evolution pair uses actual VA history; separate figure_B_nu_iterations.png/pdf includes actualnu evolution.',
       'Algorithm1 TeX describes unchanged actual incomplete algorithm; TeX compilation NOT_RUN. Positive-only distance figure base10log uses exact K values, no interpolation.',
       'Ponytail reused original source/AO/provenance/Job/Sleep and stdlib observers; no alternative scientific method. Stop here; no automatic retries, additional AP or resumed campaign.']
    (OUT/'ao_overnight_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with (OUT/'profiling_fix_audit.md').open('a',encoding='utf-8') as stream:
        stream.write('\n## Production failure and versioned correction\n\nFirst-stage wrapper used worker.mp.dps on a module, raising AttributeError before AP Gram construction. Initial39 dummy tests missed this integration. Executed observer v1 is preserved, not silently repaired/retried. v2 uses worker.mp.mp.dps and passes real-module dummy operations at all3 original precisions. Full AP coverage and v2 real-source equivalence remain NOT_RUN; no real AP launched after failure. Final41 tests include2 integration checks; no source-moment computation in those tests.\n')
    # Never mislabel exception-unwound frames as successful completed numerical stages.
    (OUT/'profiling_stage_summary.csv').write_text('stage,digits,completed_numeric_stage_calls,outcome,bottleneck_status\nprecision_row,1050,0,INSTRUMENTATION_FAILURE_BEFORE_AP_GRAM,BOTTLENECK_NOT_LOCALIZED\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','final_test_count','protected_hashes_unchanged',
             'total_wall_through_final_audit_seconds','no_orphan_AP_or_controller')},indent=2))


if __name__=='__main__':main()
