"""Verify saved Batch3 results independently; no AP or optimization is invoked."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_mb_batch3 as run


def main():
    import torch
    torch.set_num_threads(1)
    out,io,ao=run.OUT,run.io,run.ao
    report=json.loads((out/'run_report.json').read_text())
    assert report['postprocess'] and report['postprocess']['AO_rechecked'], 'Final AO must actually finish'
    assert report['wall_budget_respected'] and report['sleep_prevention']['released_verified']
    assert report['authorization_session_origin_utc']=='2026-10-09T07:56:11Z' and report['budget_reset'] is False
    for name,expected in json.loads((out/'protected_input_manifest.json').read_text()).items():
        assert io.digest(ROOT/name)==expected,name
    config=run.source.unconstrained_config()
    bank=run.source.load_source_payloads(config,run.DIRS)
    mb={ (float.fromhex(p['nu_mb_raw_hex']).hex(),float.fromhex(p['V_A_hex']).hex()):p
         for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0 }
    successful=[r for r in report['attempts'] if r['status']=='COMPLETED_EXACT']
    assert len(mb)==145+len(successful)<=148
    assert len({r['cache_key'] for r in report['attempts']})==len(report['attempts'])<=3
    assert report['attempts'][0]['status']=='PROCESS_FAILURE' and len([r for r in report['attempts'] if r['batch']==1])==1
    saved=json.loads((out/'objective_checkpoint.json').read_text())
    comparisons={float(r['L_km']):r for r in io.read_csv(out/'old_vs_new_optimum.csv')}
    old={float(r['L_km']):r for r in io.read_csv(run.BASE/'previous_vs_new_optimum.csv')}
    records={float(r['L_km']):r for r in io.read_csv(out/'alt_opt_validation.csv')}
    catalog=io.read_csv(out/'expanded_mb_catalog.csv')
    assert len(catalog)==len(mb)
    tops=io.read_csv(out/'top_two_candidates.csv')
    new_rows=io.read_csv(out/'exact_skr_26_distances.csv') if successful else []
    assert len(new_rows)==26*len(successful)
    expected_new={r['cache_key'] for r in successful}
    assert {r['source_cache_key'] for r in new_rows}==expected_new
    verified,repeats=[],[]
    def forbidden(*a,**kw):
        raise AssertionError('Final verification cannot generate source moments')
    with patch.object(ao.ExactMBEvaluator,'source_moments',forbidden):
        for distance in run.sweep.DISTANCES_KM:
            cache=saved[str(distance)]
            obj=ao.ExactObjective(config,cache['identity']['identity']['channel'],out,
                allow_new_source=False,source_cache_dirs=run.DIRS)
            obj.restore_objective_rows(cache['rows'],cache['identity'])
            assert len(obj.rows)==len(mb)
            assert {(float(r['nu_raw']).hex(),float(r['V_A']).hex()) for r in obj.rows.values()}==set(mb)
            ranked=sorted(obj.rows.values(),key=lambda r:float(r['SKR']),reverse=True)
            best,second=ranked[:2]
            c=comparisons[distance]
            assert float(c['old_K'])==float(old[distance]['new_K'])
            assert float(c['new_K'])==best['SKR'] and float(c['runner_up_K'])==second['SKR']
            assert float(c['delta_K'])==best['SKR']-float(c['old_K'])
            for rank,row in enumerate((best,second),1):
                t=next(t for t in tops if float(t['L_km'])==distance and int(t['rank'])==rank)
                assert float(t['SKR'])==row['SKR'] and t['source_cache_key']==row['source_cache_key']
            selected=records[distance]
            selected_row=obj(float(selected['nu_raw_star']),float(selected['V_A_star']))
            matches=selected_row['SKR']==float(selected['K'])==best['SKR']
            assert (selected['matches_catalog_maximum']=='True')==matches
            verified.append({'L_km':distance,'MB_count':len(mb),'best_nu':best['nu_raw'],'best_V_A':best['V_A'],
                'best_K':best['SKR'],'runner_up_nu':second['nu_raw'],'runner_up_V_A':second['V_A'],
                'runner_up_K':second['SKR'],'top_two_gap':best['SKR']-second['SKR'],
                'AO_matches_catalog':matches,'objective_identity_sha256':obj.context_hash})
            for row in [r for r in new_rows if float(r['L_km'])==distance]:
                assert obj(float(row['nu_raw']),float(row['V_A']))['SKR']==float(row['SKR'])
            if distance in (20.,21.9393102292,22.,23.,24.,40.):
                for attempt in successful:
                    nu,va=attempt['nu_raw'],attempt['V_A']
                    candidate=run.source.candidate_from_payload(config,bank,'MB',nu,va)
                    stored=obj(nu,va)
                    repeated=ao.evaluate_candidate(candidate,obj.channel,config)
                    repeats.append({'L_km':distance,'nu_raw':nu,'V_A':va,
                        **{'delta_'+k:float(repeated[k])-float(stored[k]) for k in ('I_AB','beta_I_AB','chi_BE','SKR')},
                        'source_cache_key':candidate['source_cache_key']})
            assert obj.unique_exact_evaluations==0
    searches=json.loads((out/'cache_only_searches.json').read_text())
    runs=json.loads((out/'cache_only_runs.json').read_text())
    assert len(runs)==129 and sum(int(r['multistart_runs']) for r in records.values())==129
    assert sum(int(r['total_outer_iterations']) for r in records.values())==sum(len(r['iterations']) for r in runs)
    for distance,row in records.items():
        if row['status']=='CONVERGED_NUMERICALLY':
            final_checks=[s for s in searches if s['L_km']==distance][-2:]
            assert len(final_checks)==2 and all(ao.coordinate_search_complete(s) for s in final_checks)
        assert row['global_optimum_resolved']=='False'
    missing=set()
    for s in searches:
        for event in s['history']:
            if event['status']=='EXACT_SOURCE_MISSING':
                nu,va=(s['fixed'],event['value']) if s['variable']=='V_A' else (event['value'],s['fixed'])
                missing.add((float(nu).hex(),float(va).hex()))
    inventory=io.read_csv(out/'remaining_missing_exact_pairs.csv')
    assert missing=={(float(r['nu_raw']).hex(),float(r['V_A']).hex()) for r in inventory}
    repeated_order=(all(r['delta_'+k]==0 for r in repeats for k in ('I_AB','beta_I_AB','chi_BE','SKR'))
                    if repeats else None)
    classification=('NO_NEW_VALID_SOURCE_NO_NEW_GAIN_TO_CLASSIFY' if not repeats else
                    'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED' if repeated_order else 'NUMERICAL_RANKING_INCONCLUSIVE')
    for attempt in report['attempts']:
        rec=attempt['supervision']
        assert attempt['wall_seconds']<=attempt['timeout_seconds']<=3600
        assert rec['wall_limit_respected'] and rec['no_watchdog_thread_remaining']
    # No live producer or worker may remain at handoff; never kill unrelated processes.
    assert not run.supervisor.controller_alive(report['controller_pid'])
    patterns=('test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py',
              'test_mb_sleep_safe_expansion.py','test_mb_batch2.py','test_mb_batch3_preparation.py',
              'test_mb_batch3.py','test_mb_batch3_resume.py')
    checks=[]
    for pattern in patterns:
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],
            cwd=ROOT,capture_output=True,text=True)
        checks.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
    io.save_json(out/'final_regression_tests.json',checks)
    assert all(c['returncode']==0 for c in checks)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    io.write_csv(out/'independent_catalog_verification.csv',verified)
    if repeats:
        io.write_csv(out/'new_source_objective_reproducibility.csv',repeats)
    final={'status':'CURRENTLY_VERIFIED_PASS','compatible_MB_count':len(mb),
        'verified_objectives':26*len(mb),'new_exact_sources':len(successful),'new_exact_objectives':len(new_rows),
        'independent_AO_matches_catalog':sum(r['AO_matches_catalog'] for r in verified),
        'new_source_metric_repeats':len(repeats),'repeats_bit_exact':repeated_order,
        'numerical_ranking_status':classification,'remaining_unique_missing_sources':len(missing),
        'coordinate_status_counts':dict(Counter(s['status'] for s in searches)),
        'fully_closed_coordinate_invocations':sum(ao.coordinate_search_complete(s) for s in searches),
        'multistart_runs':len(runs),'outer_iterations':sum(len(r['iterations']) for r in runs),
        'numerically_converged_distances':[d for d,r in records.items() if r['status']=='CONVERGED_NUMERICALLY'],
        'tests_pass':True,'git_diff_check_pass':True,'original_deadline_preserved':True,
        'Sleep_original_state_restored':True,'producer_sha256':io.digest(__file__)}
    io.save_json(out/'completed_independent_verification.json',final)
    # Preserve the execution report verbatim; this is a separate independent audit.
    lines=['# Completed Batch3 independent validation','',json.dumps(final,indent=2),'',
        'Prior power-aborted source1 was not retried. Unattempted points may be skipped for remaining budget; no missing K was inferred.',
        'Six representative distances re-evaluate each valid new source using original GH8/direct-Zminus evaluator, not new C,w.',
        'Numerical total-error bound absent; no continuous convergence or global optimality.',
        'Original formulas/source/precision/quadrature/MI/Holevo/ALT_OPT and historical artifacts unchanged.']
    (out/'completed_independent_verification.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(final,indent=2))


if __name__=='__main__':
    main()
