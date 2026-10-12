"""Verify142-source baseline and select original missing requests; no AP/SKR/AO."""
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_mb_sleep_safe_expansion as previous
from scripts.windows_sleep_safe_supervision import WindowsPower, AwakeOnAC

ao,io,source,sweep=previous.ao,previous.io,previous.source,previous.sweep
BASE=previous.OUT
OUT=BASE.parent/'batch_2'
PROPOSED=((.165,5.475),(.165,5.425),(.15,6.25))


def pair(nu,va):
    return float(nu).hex(),float(va).hex()


def forbidden(*args,**kwargs):
    raise AssertionError('Preparation uses saved artifacts only; no science/AP rerun')


def main():
    if OUT.exists():
        raise SystemExit('Batch2 exists; preserve artifacts and do not repeat preparation')
    config=source.unconstrained_config()
    manifest=json.loads((BASE/'input_manifest_after.json').read_text())
    manifest.update(io.raw_snapshot([p for p in BASE.rglob('*') if '__pycache__' not in p.parts]))
    manifest.update(io.raw_snapshot([Path(__file__)]))
    for name,expected in manifest.items():
        assert io.digest(ROOT/name)==expected,name
    old_report=json.loads((BASE/'run_report.json').read_text())
    assert old_report['successful_probes']==3 and old_report['postprocess']['MB_count']==142
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES)==(1e-8,1e-6,6,4)
    checkpoint=json.loads((BASE/'objective_checkpoint.json').read_text())
    optimum={float(r['L_km']):r for r in io.read_csv(BASE/'old_vs_new_mb_skr.csv')}
    tops=io.read_csv(BASE/'top_two_candidates.csv')
    old_ao=io.read_csv(BASE/'alt_opt_recheck.csv')
    searches=json.loads((BASE/'cache_only_searches.json').read_text())
    dependencies=io.read_csv(BASE/'remaining_missing_exact_pairs.csv')
    with patch.object(ao.ExactMBEvaluator,'source_moments',forbidden),patch.object(sweep,'make_channel',forbidden),patch.object(ao,'evaluate_candidate',forbidden):
        bank=source.load_source_payloads(config,previous.SOURCE_DIRS)
        mb={pair(float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])):p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0}
        stored=io.read_csv(BASE/'updated_mb_catalog.csv')
        assert len(mb)==len(stored)==142 and set(mb)=={pair(r['nu_raw'],r['V_A']) for r in stored}
        for r in stored:
            p=mb[pair(r['nu_raw'],r['V_A'])]
            assert r['source_cache_key']==p['cache_key'] and r['ensemble_hash']==p['ensemble_hash']
            assert float(r['C'])==p['C'] and float(r['w'])==p['w']
        for distance in sweep.DISTANCES_KM:
            saved=checkpoint[str(distance)]
            channel=saved['identity']['identity']['channel']
            expected=ao.objective_identity(config,channel)
            assert ao.objective_compatible(saved['identity'],expected)
            assert len(saved['rows'])==142 and {pair(r['nu_raw'],r['V_A']) for r in saved['rows']}==set(mb)
            for r in saved['rows']:
                p=mb[pair(r['nu_raw'],r['V_A'])]
                assert r['source_cache_key']==p['cache_key'] and r['ensemble_hash']==p['ensemble_hash'] and r['channel_hash']==channel['channel_hash']
                ao.finite_metrics(r)
                assert abs(float(r['SKR'])-(float(r['beta_I_AB'])-float(r['chi_BE'])))<1e-14
            ranked=sorted(saved['rows'],key=lambda r:float(r['SKR']),reverse=True)
            assert float(ranked[0]['SKR'])==float(optimum[distance]['new_K'])
            assert float(ranked[1]['SKR'])==float(next(r for r in tops if float(r['L_km'])==distance and r['rank']=='2')['SKR'])
        assert float(optimum[22.]['new_K'])==.07661714229913241
        # Identity construction only; source moments are forbidden above.
        evaluator=ao.ExactMBEvaluator(config,{'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},BASE,
            source_cache_dir=BASE/'exact_source_cache',allow_legacy_exact_import=False)
        selected=[]
        local=[]
        for priority,(nu,proposed_va) in enumerate(PROPOSED,1):
            matches=[r for r in dependencies if float(r['nu_raw'])==nu and abs(float(r['V_A'])-proposed_va)<1e-13]
            assert len(matches)==1,'Missing request ambiguous or absent'
            dep=matches[0]
            va=float(dep['V_A'])
            assert pair(nu,va) not in mb and source.candidate_from_payload(config,bank,'MB',nu,va) is None
            ensemble=source.make_ensemble(config,'MB',nu,va)
            identity=evaluator._source_identity(ensemble,nu,va)
            cache_key=source.json_hash(identity)
            affected=json.loads(dep['distances'])
            for distance in affected:
                neighbors=sorted([r for r in checkpoint[str(distance)]['rows'] if float(r['nu_raw'])==nu],key=lambda r:float(r['V_A']))
                lower=max((r for r in neighbors if float(r['V_A'])<va),key=lambda r:float(r['V_A']))
                upper=min((r for r in neighbors if float(r['V_A'])>va),key=lambda r:float(r['V_A']))
                local.append({'priority':priority,'L_km':distance,'nu_raw':nu,'missing_V_A':va,
                    'lower_V_A':lower['V_A'],'lower_K':lower['SKR'],'upper_V_A':upper['V_A'],'upper_K':upper['SKR'],
                    'neighbor_delta_K':float(upper['SKR'])-float(lower['SKR']),
                    'catalog142_nu':optimum[distance]['new_nu'],'catalog142_V_A':optimum[distance]['new_V_A'],
                    'catalog142_K':optimum[distance]['new_K'],'missing_K':'UNKNOWN_NOT_MEASURED'})
            reason=('Refine between exact5.45/5.5: winners switch between baseline21.939 and22km;14 missing requests.' if priority==1 else
                'Exact original lower midpoint5.425000000000001, not decimal5.425:9 requests on new22km ridge.' if priority==2 else
                'Keep short-distance coverage: exact midpoint6.0/6.5 atnu=.15,7 requests at20/21km; no evidence justifies replacing it with another speculative point.')
            selected.append({'pilot_priority':priority,'nu_raw':nu,'V_A':va,'proposed_V_A':proposed_va,
                'nu_raw_hex':nu.hex(),'V_A_hex':va.hex(),'source_cache_key':cache_key,'raw_current_cache_key':cache_key,
                'ensemble_hash':identity['ensemble_hash'],'affected_distances':json.dumps(affected),
                'missing_requests':int(dep['requests']),'source_availability':'EXACT_SOURCE_MISSING',
                'selection_reason':reason,'status':'NOT_RUN_AWAITING_EXPLICIT_BATCH2_APPROVAL','predicted_K':'UNKNOWN'})
        assert len({pair(r['nu_raw'],r['V_A']) for r in selected})==3
    # Record relevant alternatives from ACTUALLY executed searches, without predicting K.
    alternatives=[]
    for r in dependencies:
        if float(r['nu_raw']) in (.165,.15) and float(r['V_A']) in (5.5125,4.75,5.35,5.25):
            alternatives.append({**r,'decision':'DEFER','reason':'Not stronger measured evidence than selected ridge midpoints/diversified20km coverage; K missing'})
    attempts=json.loads((previous.prior.CONT/'source_generation_ledger.json').read_text())['attempts']
    for p in selected:
        history=[a for a in attempts if pair(a['nu_raw'],a['V_A'])==pair(p['nu_raw'],p['V_A'])]
        assert not history,'Selected point had previous expensive attempt; reconsider explicitly'
        p['prior_exact_attempts']='[]'
    OUT.mkdir()
    io.save_json(OUT/'protected_input_manifest.json',manifest)
    io.save_json(OUT/'input_manifest_before.json',manifest)
    io.write_csv(OUT/'selected_probes.csv',selected)
    io.write_csv(OUT/'local_exact_neighbor_gaps.csv',local)
    io.write_csv(OUT/'alternative_candidates.csv',alternatives)
    io.write_csv(OUT/'baseline142_optima.csv',list(optimum.values()))
    io.write_csv(OUT/'baseline142_top_two.csv',tops)
    io.write_csv(OUT/'baseline142_alt_opt.csv',old_ao)
    power=WindowsPower().read()
    lease=AwakeOnAC()
    with lease:
        pass
    io.save_json(OUT/'power_preflight.json',{'power':power,'temporary_sleep_lease':lease.receipt,
        'active_now':False,'reacquire_before_AP':True,'no_permanent_power_change':True,'AP_started':False})
    checks=[]
    for pattern in ('test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_sleep_safe_expansion.py'):
        test=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True)
        checks.append({'pattern':pattern,'returncode':test.returncode,'output':test.stdout+test.stderr})
    io.save_json(OUT/'planning_regression_tests.json',checks)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert all(r['returncode']==0 for r in checks) and diff.returncode==0
    for name,expected in manifest.items():
        assert io.digest(ROOT/name)==expected,name
    report={'status':'PREPARED_AWAITING_EXPLICIT_BATCH2_APPROVAL','catalog_MB_count':142,'new_sources':0,
        'AP_probes_started':0,'new_SKR_evaluations':0,'ALT_OPT_rerun':False,'baseline_objectives_verified':26*142,
        'baseline22_reference_K':.07661714229913241,'selected_probes':selected,
        'proposed_total_seconds':10800,'proposed_probe_seconds':3600,'max_new_probes':3,'fresh_budget_confirmed':False,
        'old_unused_budget_reused':False,'protected_files_verified':len(manifest),'tests_pass':True,
        'git_diff_check_pass':True,'scientific_implementation_changed':False,'no_interpolation':True,
        'source_precision_ladder':ao.source_settings(config)['precision_ladder'],
        'frozen_spec_discrepancy':'PREEXISTING_UNCHANGED_DIAGNOSTIC_ONLY','publication':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    io.save_json(OUT/'run_report.json',report)
    io.save_json(OUT/'input_manifest_after.json',manifest)
    lines=['# Batch2: candidate preparation only','',report['status'],'',
        'Verified142 unique compatible exact MB pairs and3692 saved objective rows. No AP, new SKR, channel or ALT_OPT execution.',
        'Current22km reference K=0.07661714229913241, not obsolete139-catalog value.','',
        '| Priority | nu_raw | V_A exact binary64 | Reason |','|---|---|---|---|']
    lines += [f"| {r['pilot_priority']} | {r['nu_raw']} | {r['V_A']} | {r['selection_reason']} |" for r in selected]
    lines += ['', 'Local exact values and actual missing dependencies saved in local_exact_neighbor_gaps.csv; missing objective values remain UNKNOWN.',
        '5.425000000000001 differs by1 ULP from proposed5.425. Use actual original search key, without altering the scientific algorithm.',
        'Other missing points inspected; no unknown K was predicted/interpolated. Known expensive(.16375,5.5) and(.15,4.75) are not selected.',
        'Fresh proposed10800s/3600s/max3 batch requires explicit approval; previous authorization is complete and not reused.',
        'AC and temporary sleep request verified/released in preflight; recheck/reacquire for actual execution. No permanent power plan changes.',
        f"All {len(manifest)} protected hashes unchanged;30 scoped regressions and diff check PASS.",
        'Original science/settings/precision/quadrature/MI/direct-Zminus/AO/provenance unchanged. No source generation, optimization or interpolation.',
        'Frozen-spec discrepancy/publication restrictions remain. Numerical convergence/global optimality NOT_PROVEN.']
    (OUT/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','catalog_MB_count','baseline_objectives_verified','selected_probes','protected_files_verified')},indent=2))


if __name__=='__main__':
    main()
