"""Verify saved selections, geometry, hashes, and independent selected MI."""
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

from run import OUT, ROOT, PASS, angle_samples, helpers, read, rows, sha


def main():
    summary=read(OUT/'summary.json')
    identity=read(OUT/'execution_identity.json')
    checks={}
    checks['producer_hashes']=all(sha(ROOT/path)==digest for path,digest in identity['producers'].items())
    checks['source_payload_hashes']=all(sha(ROOT/path)==digest for path,digest in identity['source_hashes'].items())
    binding=read(OUT/'execution_dependency_binding.json')
    checks['all_current_dependency_hashes']=all(sha(ROOT/r['path'])==r['current_sha256'] for r in binding['dependencies'])
    sweep=rows(OUT/'skr_vs_zenith.csv');positions=rows(OUT/'skr_map.csv')
    grid_path=ROOT/'results/skr_lookup_readiness_20261105/geometry_only.csv'
    grid=rows(grid_path)
    checks['input_geometry_hash_and_order']=sha(grid_path)==identity['geometry_sha256'] and len(grid)==len(positions) and all(
        all(float(p[k])==float(g[k]) for k in ('x_m','y_m','distance_m','zenith_deg')) for p,g in zip(positions,grid))
    pool={r['ensemble_hash']:r for r in rows(OUT/'source_pool.csv')}
    inventory={r['ensemble_hash']:r for r in rows(ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/exact_source_inventory.csv')}
    source_values_valid=len(pool)==212
    for ensemble,s in pool.items():
        original=inventory[ensemble];payload=read(ROOT/s['source_path'])
        source_values_valid &= all(float(s[k])==payload[k] for k in ('C','w'))
        source_values_valid &= float(s['VA']).hex()==payload['V_A_hex'] and float(s['nu_raw']).hex()==payload['nu_mb_raw_hex']
        source_values_valid &= s['classification']==original['source_evidence_class'] and s['family']==original['family']
    checks['source_values_and_evidence']=bool(source_values_valid)
    checks['angle_sampling']=len(sweep)==2*len(angle_samples()) and sorted({float(r['zenith_deg']) for r in sweep})==angle_samples()
    checks['slant_endpoint']=abs(max(float(r['distance_m']) for r in sweep)-22000)<1e-7
    checks['numerical_rows']=all(r['numerical_status']==PASS for r in sweep) and len(positions)==2601
    contexts={};candidate_checks=[];candidate_count=0
    for path in sorted((OUT/'contexts').glob('*.json')):
        context=read(path);contexts[context['angle_hex']]=context
        candidates=rows(path.with_name(path.stem+'_candidates.csv'));candidate_count+=len(candidates)
        valid=(len(candidates)==212 and {r['ensemble_hash'] for r in candidates}==set(pool)
               and context['execution_identity_sha256']==sha(OUT/'execution_identity.json')
               and all(r['numerical_status']==PASS for r in candidates))
        for r in candidates:
            source=pool[r['ensemble_hash']]
            valid &= all(float(r[k])==float(source[k]) for k in ('VA','nu_raw','C','w'))
            valid &= r['family']==source['family'] and r['source_evidence_class']==source['classification']
        for family,winner in context['winners'].items():
            subset=[r for r in candidates if r['family']==family]
            if not subset or winner is None:valid=False;continue
            best=max(subset,key=lambda r:float(r['K_raw']))
            valid &= float(best['K_raw'])==winner['K_raw'] and best['ensemble_hash']==winner['ensemble_hash']
        candidate_checks.append(bool(valid))
    checks['all_context_catalog_maxima']=all(candidate_checks) and len(contexts)==summary['total_unique_contexts']
    checks['candidate_counts']=candidate_count==212*len(contexts)
    sweep_valid=True
    for r in sweep:
        context=contexts[float(r['zenith_deg']).hex()]
        winner=context['winners'][r['scheme']]
        sweep_valid &= winner is not None and abs(float(r['distance_m'])-context['distance_m'])<1e-7
        for key,saved_key in [('K_raw_bits_per_use','K_raw'),('nu_raw','nu_raw'),('VA','VA'),('I_AB','I_AB'),('chi_BE','chi_BE')]:
            sweep_valid &= winner is not None and float(r[key])==winner[saved_key]
        sweep_valid &= winner is not None and r['source_evidence_class']==winner['source_evidence_class']
    checks['sweep_context_winners']=bool(sweep_valid)
    map_valid=True
    for p in positions:
        x,y=float(p['x_m']),float(p['y_m'])
        distance=math.sqrt(19000**2+(x-1000)**2+(y-1000)**2)
        angle=math.degrees(math.atan2(math.hypot(x-1000,y-1000),19000))
        context=contexts[p['context_angle_hex']]
        map_valid &= abs(distance-float(p['distance_m']))<1e-7 and abs(angle-float(p['zenith_deg']))<1e-12
        map_valid &= abs(context['zenith_deg']-angle)<1e-12 and abs(context['distance_m']-distance)<1e-7
        for family in ('MB','Uniform'):
            winner=context['winners'][family]
            map_valid &= winner is not None and float(p[family+'_K_raw'])==winner['K_raw'] and p[family+'_ensemble_hash']==winner['ensemble_hash']
    checks['map_direct_geometry_and_contexts']=bool(map_valid)
    with np.load(OUT/'skr_map.npz',allow_pickle=False) as data:
        raw=data['K_raw_bits_per_use'];potential=data['K_potential_bits_per_use']
        checks['NPZ_CSV_identical']=np.array_equal(raw,np.array([float(r['K_raw_bits_per_use']) for r in positions]).reshape(51,51))
        checks['finite_grid_and_potential']=raw.shape==(51,51) and np.isfinite(raw).all() and np.array_equal(potential,np.maximum(raw,0))
        checks['symmetry']=np.array_equal(raw,raw[::-1]) and np.array_equal(raw,raw[:,::-1]) and np.array_equal(raw,raw.T)
        checks['summary_extrema']=float(raw.min())==summary['min_map_MB_K'] and float(raw.max())==summary['max_map_MB_K'] and float(raw[25,25])==summary['center_map_MB_K']
    checks['benchmark_reproduction']=all(r['status']==PASS and max(r['absolute_deviation'].values())<=2e-10 for r in read(OUT/'benchmark_recheck.json'))
    checks['no_candidate_errors']=read(OUT/'evaluation_errors.json')==[]
    # Separate adaptive integration of the output density at center/corner and endpoint.
    old=helpers();a=old.canonical.prior_model.helpers()
    sources={r['ensemble_hash']:r for r in rows(OUT/'source_pool.csv')}
    angles_to_check={0.,max(float(p['zenith_deg']) for p in positions),angle_samples()[-1]}
    independent=[]
    for angle in sorted(angles_to_check):
        context=next(c for c in contexts.values() if abs(c['zenith_deg']-angle)<1e-12)
        for family,winner in context['winners'].items():
            source=dict(sources[winner['ensemble_hash']])
            for key in ('VA','nu_raw','C','w'):source[key]=float(source[key])
            source=old.historical.with_ensemble(source)
            p,alpha=a.validate_source(source)
            mi,error=a.independent_mi(p,alpha,winner['eta_f'],1+winner['N_effective'])
            independent.append(dict(zenith_deg=angle,family=family,difference=abs(mi-winner['I_AB']),
                                    adaptive_error_estimate=error,status=PASS if abs(mi-winner['I_AB'])<=2e-10 else 'FAILED'))
    checks['independent_adaptive_MI']=all(r['status']==PASS for r in independent)
    checks={k:bool(v) for k,v in checks.items()}
    test_suite=unittest.defaultTestLoader.discover(str(OUT),pattern='test_run.py')
    test_result=unittest.TextTestRunner(verbosity=2).run(test_suite)
    result=dict(status=PASS if all(checks.values()) and test_result.wasSuccessful() else 'FAILED',
                checks=checks,independent_selected_MI=independent,unit_tests_run=test_result.testsRun,
                context_count=len(contexts),candidate_count=candidate_count,
                source_and_security_evidence_promoted=False)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']==PASS else 1


if __name__=='__main__':raise SystemExit(main())
