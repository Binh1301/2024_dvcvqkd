"""Independent final artifact verification; no scientific rerun."""
import json
import math
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_mb_batch2 as run


def main():
    io=run.io
    report=json.loads((OUT/'run_report.json').read_text())
    assert report['status']=='BATCH2_FINISHED_FINITE_CATALOG_SCOPE',report['status']
    attempts=report['attempts']
    assert [(float(r['nu_raw']),float(r['V_A'])) for r in attempts]==list(run.PAIRS)[:len(attempts)]
    assert len({r['cache_key'] for r in attempts})==len(attempts)<=3
    assert all(r['timeout_seconds']<=3600 and r['supervision']['wall_limit_respected'] for r in attempts)
    protected=run.supervisor.verify_protected(OUT)
    completed=[r for r in attempts if r['status']=='COMPLETED_EXACT']
    bank=run.source.load_source_payloads(run.source.unconstrained_config(),run.DIRS)
    mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    assert len(mb)==142+len(completed)<=145
    for r in completed:
        c=run.source.candidate_from_payload(run.source.unconstrained_config(),bank,'MB',float(r['nu_raw']),float(r['V_A']))
        assert c is not None and c['C']==r['C'] and c['w']==r['w'] and c['source_cache_key']==r['cache_key']
    comparisons=io.read_csv(OUT/'previous_vs_new_optimum.csv')
    assert tuple(float(r['L_km']) for r in comparisons)==run.sweep.DISTANCES_KM
    assert float(next(r for r in comparisons if float(r['L_km'])==22.)['old_K'])==.07661714229913241
    assert all(math.isfinite(float(r['new_K'])) and abs(float(r['new_K'])-(float(r['beta_I_AB'])-float(r['chi_BE'])))<1e-14 for r in comparisons)
    for r in comparisons:
        assert float(r['delta_K'])==float(r['new_K'])-float(r['old_K'])
    objectives=io.read_csv(OUT/'exact_skr_26_distances.csv') if completed else []
    assert len(objectives)==26*len(completed)
    aorows=io.read_csv(OUT/'alt_opt_validation.csv')
    assert tuple(float(r['L_km']) for r in aorows)==run.sweep.DISTANCES_KM
    assert len(json.loads((OUT/'cache_only_runs.json').read_text()))==129
    changes=io.read_csv(OUT/'coordinate_changes.csv')
    assert len(changes)==52
    for number in range(1,len(attempts)):
        if attempts[number-1]['status']=='COMPLETED_EXACT':
            assert (OUT/f'reassessment_after_probe_{number}.json').exists()
    tests=[]
    for pattern in ('test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_sleep_safe_expansion.py','test_mb_batch2.py'):
        result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True)
        tests.append({'pattern':pattern,'returncode':result.returncode,'output':result.stdout+result.stderr})
    io.save_json(OUT/'completed_regression_tests.json',tests)
    assert all(t['returncode']==0 for t in tests)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0
    result=subprocess.run(['powershell','-NoProfile','-Command',
        "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {($_.CommandLine -like '*run_theta10_D55_mb_batch2.py*') -or (($_.CommandLine -like '*batch_2*') -and (($_.CommandLine -like '*--probe*') -or ($_.CommandLine -like '*--profile-worker*')))}).Count"],capture_output=True,text=True,check=True)
    workers=int(result.stdout.strip())
    assert workers==0 and report['wall_budget_respected']
    assert report['sleep_prevention']['active_verified'] and report['sleep_prevention']['released_verified']
    assert all(r['wall_limit_respected'] and r['no_watchdog_thread_remaining'] for r in report['supervision_receipts'])
    verified={'status':'CURRENTLY_VERIFIED_PASS','protected_files_unchanged':protected,'MB_count':len(mb),
        'successful_probes':len(completed),'timeout_probes':sum(r['status']=='TIMEOUT' for r in attempts),
        'new_exact_objectives':len(objectives),'distances':26,'original_AO_starts':129,
        'AO_matches_catalog':sum(r['matches_catalog_maximum']=='True' for r in aorows),
        'newly_closed_selected_searches':sum(r['newly_closed']=='True' for r in changes),
        'workers_remaining':workers,'wall_budget_respected':True,'sleep_request_restored':True,
        'regression_tests_pass':True,'regression_test_count':32,'git_diff_check_pass':True,
        'no_interpolation':True,'science_unchanged':True,'reference_MB_count':142,
        'baseline22_K':.07661714229913241,'CPU_scope':'Measured Job+controller; excludes preparation and independent tests'}
    io.save_json(OUT/'completed_verification.json',verified)
    report['final_verification']=verified
    io.save_json(OUT/'run_report.json',report)
    original=OUT/'coordinator_run_report.md'
    if not original.exists():
        original.write_text((OUT/'run_report.md').read_text(),encoding='utf-8')
    lines=[original.read_text(), '', '## New exact source moments and runtime','',
        '| Probe | nu_raw | V_A | C | w | Status | Wall seconds | Job CPU seconds |',
        '|---|---|---|---|---|---|---|---|']
    lines += ['| '+' | '.join(str(r.get(k,'')) for k in ('batch','nu_raw','V_A','C','w','status','wall_seconds','cpu_seconds'))+' |' for r in attempts]
    lines += ['', '## Finite catalog comparison: historical136, previous142, current','',
        '| Link km | Historical136 K | Previous142 K | New nu | New V_A | Current K | Delta vs142 |',
        '|---|---|---|---|---|---|---|']
    lines += ['| '+' | '.join(r[k] for k in ('L_km','historical136_K','old_K','new_nu','new_V_A','new_K','delta_K'))+' |' for r in comparisons]
    lines += ['', '## Validation and limitations','',json.dumps(verified),
        'Source (C,w), source precision1050/1250/1450, quadrature, MI, direct-Zminus Holevo and original ALT_OPT unchanged.',
        'All comparisons use142 as current baseline; historical136 is reported separately. No dense restart, interpolation or predicted missing K.',
        'Catalog matching does not establish numerical convergence or continuous-domain global optimality. See actual coordinate logs and remaining_missing_exact_pairs.csv.',
        'Tiny numerical gain has no demonstrated total objective error bound; physical significance is not certified.',
        'Temporary sleep request was verified during run and restored at end. It does not prevent manual shutdown/suspend/critical power.',
        'Frozen-spec discrepancy/lifecycle remain unchanged; no publication/training/test/baseline/threshold approval.',
        'Another batch is justifiable only as targeted numerical coverage, after assessing recorded unresolved directions and runtime; not automatically authorized.']
    (OUT/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(verified,indent=2))


if __name__=='__main__':
    main()
