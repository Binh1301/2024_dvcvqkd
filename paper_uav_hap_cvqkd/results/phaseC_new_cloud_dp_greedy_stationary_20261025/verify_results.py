"""Saved-record scientific/provenance checks; no physical/source evaluations."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def verify():
    cfg=read(OUT/'experiment_config.json');start=read(OUT/'startup_manifest.json')
    for name,digest in start['protected'].items():assert sha(ROOT.parent/name)==digest,name
    for name,digest in cfg['bindings'].items():assert sha(ROOT/name)==digest,name
    assert cfg['primary_geometry']=='centered' and cfg['geometry_cases']['centered']['hap_horizontal_m']==[500.,500.]
    assert cfg['mission']=={'slots':30,'slot_duration_s':20,'max_speed_m_per_s':15}
    pool={r['ensemble_hash']:r for r in rows(ROOT/cfg['source_pool_path'])}
    assert len(pool)==212 and sha(ROOT/cfg['source_pool_path'])==cfg['source_pool_sha256']
    physical_rows=0;physical_groups={}
    for path in sorted((OUT/'physical_records').glob('*.csv')):
        records=rows(path);assert len(records)==212
        physical_groups[path.stem]=records;physical_rows+=len(records)
        assert len({r['ensemble_hash'] for r in records})==212
        for r in records:
            source=pool[r['ensemble_hash']]
            assert r['source_sha256']==source['source_sha256']==sha(ROOT/r['source_path'])
            for key in ['C','w','VA','nu_raw']:assert float(r[key]).hex()==float(source[key]).hex()
            assert r['source_evidence_class']==source['source_evidence_class']
            assert r['source_Cw_recomputed']=='False' and r['numerical_status']=='CURRENTLY_VERIFIED_PASS'
            assert r['correlation_policy']=='manuscript_eq14_direct'
        ctx=read(OUT/'physical_records'/f'{path.stem}_context.json')
        assert ctx['numerical_status']=='CURRENTLY_VERIFIED_PASS' and ctx['numerical_experiment_accepted']
        assert not ctx['renormalized'] and not ctx['clipped']
    assert physical_rows==15688 and len(physical_groups)==74
    maps={g:rows(OUT/f'clear_sky_map_{g}.csv') for g in cfg['geometry_cases']}
    for g,points in maps.items():
        assert len(points)==100 and [int(r['position_index']) for r in points]==list(range(100))
        for r in points:
            candidates=physical_groups[r['geometry_id']];best=max(candidates,key=lambda a:float(a['K_raw']))
            assert r['ensemble_hash']==best['ensemble_hash'] and float(r['K_raw']).hex()==float(best['K_raw']).hex()
            assert float(r['K_star'])==max(0,float(r['K_raw']))
    assert all(float(r['K_star'])>0 for r in maps['centered'])
    assert all(float(r['K_star'])==0 and float(r['K_raw'])<0 for r in maps['historical'])
    with np.load(OUT/'cloud_realizations.npz') as archive:
        C0=archive['C_zero'];Cp=archive['C_calibrated'];Cold=archive['C_old_p04'];G=archive['G_new']
        assert C0.shape==(100,100,30) and Cp.shape==(8,100,100,30)
        assert C0.dtype==Cp.dtype==Cold.dtype==np.dtype(bool)
        assert np.array_equal(C0,G>0)
        assert np.array_equal(G,archive['mu_new']+archive['epsilon_new'])
        for i,t in enumerate(archive['thresholds']):assert np.array_equal(Cp[i],G>t)
        assert np.array_equal(C0,Cp[4])
        Csha={}
        for g,points in maps.items():
            K=np.array([float(r['K_star']) for r in points]);assert np.array_equal(K,archive[f'K_star_{g}'])
            assert np.array_equal(archive[f'S_zero_{g}'],(~C0)*K[None,:,None])
            assert np.array_equal(archive[f'S_calibrated_{g}'],(~Cp)*K[None,None,:,None])
            assert np.array_equal(archive[f'S_old_p04_{g}'],(~Cold)*K[None,:,None])
        with np.load(OUT/'secondary_historical_completed/cloud_realizations.npz') as prior:
            for key in prior.files:assert np.array_equal(archive[key],prior[key]),'Prior paired archive changed: '+key
    records=rows(OUT/'simulation_results.csv');assert len(records)==11400
    groups=defaultdict(list)
    for r in records:groups[(r['geometry'],r['case_id'],int(r['mission_id']))].append(r)
    assert len(groups)==3800
    minimum_delta=float('inf')
    for key,group in groups.items():
        assert {r['algorithm'] for r in group}=={'Stationary','Greedy','DP'}
        assert len({r['C_sha256'] for r in group})==len({r['S_sha256'] for r in group})==1
        by={r['algorithm']:r for r in group};assert float(by['Stationary']['total_distance_m'])==0
        dp=float(by['DP']['objective_U'])
        for name in ['Greedy','Stationary']:
            delta=dp-float(by[name]['objective_U']);minimum_delta=min(minimum_delta,delta);assert delta>=-1e-12
        for r in group:
            mean=float(r['average_usable_skr']);distance=float(r['total_distance_m']);penalty=float(r['lambda_bits_per_use'])
            assert abs(float(r['objective_U'])-(mean-penalty*distance/1000))<1e-15
            assert abs(float(r['availability'])+float(r['zero_rate_unavailability'])-1)<1e-14
            assert float(r['maximum_leg_m'])<=300
    old=rows(OUT/'secondary_historical_completed/simulation_results.csv')
    lookup={(r['geometry'],r['case_id'],r['mission_id'],r['algorithm']):r for r in records}
    for r in old:
        now=lookup[(r['geometry'],r['case_id'],r['mission_id'],r['algorithm'])]
        for key in ['average_usable_skr','objective_U','total_distance_m','zero_rate_unavailability','availability','blocked_fraction','position_changes','runtime_s']:
            assert float(r[key]).hex()==float(now[key]).hex(),key
    paths=defaultdict(list)
    for r in rows(OUT/'algorithm_trajectories.csv'):paths[(r['geometry'],r['case_id'],int(r['mission_id']),r['algorithm'])].append(r)
    assert len(paths)==11400
    for key,path in paths.items():
        assert len(path)==30 and [int(r['slot']) for r in path]==list(range(1,31))
        x=np.array([float(r['x_m']) for r in path]);y=np.array([float(r['y_m']) for r in path])
        legs=np.hypot(np.diff(x),np.diff(y));assert np.all(legs<=300+1e-12)
        metric=lookup[(key[0],key[1],str(key[2]),key[3])]
        assert abs(float(legs.sum())-float(metric['total_distance_m']))<1e-8
        assert abs(float(np.mean([float(r['usable_skr']) for r in path]))-float(metric['average_usable_skr']))<1e-15
    mc=read(OUT/'execution_summary.json')
    assert mc['source_moment_computations']==0 and mc['algorithm_execution_count']==10800
    manifest=OUT/'artifact_manifest.json'
    if manifest.exists():
        for name,digest in read(manifest)['files'].items():assert sha(OUT/name)==digest,name
    return dict(status='CURRENTLY_VERIFIED_PASS',result_scope='DIAGNOSTIC_ONLY',
        protected_historical_files=len(start['protected']),source_pool_count=212,new_Cw_computations=0,
        new_channel_SKR_evaluations=physical_rows,unique_channel_contexts=74,primary_positive_positions=100,secondary_positive_positions=0,
        mission_case_views=len(groups),algorithm_records=len(records),trajectory_records=342000,
        DP_objective_inequalities_checked=2*len(groups),minimum_DP_objective_advantage=minimum_delta,
        source_evidence_classes_unchanged=True,prior_secondary_numeric_records_unchanged=len(old),
        movement_failures=0,DP_dominance_failures=0,strict_Phase_B_ready=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
