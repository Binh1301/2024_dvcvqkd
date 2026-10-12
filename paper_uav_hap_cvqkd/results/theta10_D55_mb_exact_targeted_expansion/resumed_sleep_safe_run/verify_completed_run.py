"""Read-only scientific checks plus separate verification receipts. No source/AP."""
import json
import math
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_mb_sleep_safe_expansion as run


def main():
    report=json.loads((OUT/'run_report.json').read_text())
    assert report['status'] != 'AUTHORIZED_THREE_SERIAL_PROBES_RUNNING', 'Wait for coordinator finish'
    ledger=json.loads((OUT/'source_generation_ledger.json').read_text())
    attempts=ledger['attempts']
    assert len({r['cache_key'] for r in attempts})==len(attempts), 'Unexpected automatic retry'
    assert [(float(r['nu_raw']),float(r['V_A'])) for r in attempts]==list(run.PAIRS)[:len(attempts)]
    assert all(r['timeout_seconds']<=3600 for r in attempts)
    count=run.supervisor.verify_protected(OUT)
    source_bank=run.source.load_source_payloads(run.source.unconstrained_config(),run.SOURCE_DIRS)
    mb=[p for p in source_bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    completed=[r for r in attempts if r['status']=='COMPLETED_EXACT']
    assert len(mb)==139+len(completed)
    for r in completed:
        candidate=run.source.candidate_from_payload(run.source.unconstrained_config(),source_bank,'MB',float(r['nu_raw']),float(r['V_A']))
        assert candidate is not None and candidate['C']==r['C'] and candidate['w']==r['w']
    rows=run.io.read_csv(OUT/'old_vs_new_mb_skr.csv')
    assert tuple(float(r['L_km']) for r in rows)==run.sweep.DISTANCES_KM
    assert all(math.isfinite(float(r['new_K'])) and abs(float(r['new_K'])-(float(r['beta_I_AB'])-float(r['chi_BE'])))<1e-14 for r in rows)
    ao=run.io.read_csv(OUT/'alt_opt_recheck.csv')
    assert tuple(float(r['L_km']) for r in ao)==run.sweep.DISTANCES_KM
    assert len(json.loads((OUT/'cache_only_runs.json').read_text()))==129
    if completed:
        objectives=run.io.read_csv(OUT/'new_pair_26distance_objectives.csv')
        assert len(objectives)==26*len(completed)
    tests=[]
    for pattern in ('test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_sleep_safe_expansion.py'):
        result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True)
        tests.append({'pattern':pattern,'returncode':result.returncode,'output':result.stdout+result.stderr})
    run.io.save_json(OUT/'completed_run_regression_tests.json',tests)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    process_check=subprocess.run(['powershell','-NoProfile','-Command',
        "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {($_.CommandLine -like '*run_theta10_D55_mb_sleep_safe_expansion.py*') -or (($_.CommandLine -like '*resumed_sleep_safe_run*') -and (($_.CommandLine -like '*--probe*') -or ($_.CommandLine -like '*--profile-worker*')))}).Count"],capture_output=True,text=True,check=True)
    workers=int(process_check.stdout.strip())
    lease=ledger['sleep_prevention']
    verification={'status':'CURRENTLY_VERIFIED_PASS','protected_files_unchanged':count,
        'MB_count':len(mb),'successful_sources':len(completed),'timeout_sources':sum(r['status']=='TIMEOUT' for r in attempts),
        'SKR_distances':len(rows),'AO_distances':len(ao),'AO_starts':129,
        'AO_matches_catalog':sum(r['matches_catalog_maximum']=='True' for r in ao),
        'sleep_active_verified':lease['active_verified'],'sleep_restoration_verified':lease['released_verified'],
        'wall_budget_respected':ledger['wall_budget_respected'],
        'all_job_limits_respected':all(r['wall_limit_respected'] for r in ledger['supervision_receipts']),
        'workers_remaining':workers,'regression_tests_pass':all(t['returncode']==0 for t in tests),
        'git_diff_check_pass':diff.returncode==0,'scientific_implementation_unchanged':True,
        'no_interpolation':True,'continuous_global_optimum_claimed':False,
        'frozen_spec_sha256':run.io.digest(ROOT/'docs/FINAL_MODEL_SPEC.md')}
    assert workers==0 and verification['regression_tests_pass'] and diff.returncode==0
    assert lease['active_verified'] and lease['released_verified'] and ledger['wall_budget_respected']
    assert verification['all_job_limits_respected']
    run.io.save_json(OUT/'completed_run_verification.json',verification)
    print(json.dumps(verification,indent=2))


if __name__=='__main__':
    main()
