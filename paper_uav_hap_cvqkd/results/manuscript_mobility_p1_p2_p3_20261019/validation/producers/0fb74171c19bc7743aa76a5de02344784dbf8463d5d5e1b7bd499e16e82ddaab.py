"""Staged, provenance-bound manuscript P1/P2/Greedy/DP numerical comparison.

Historical scientific helpers and data are read-only. No source-moment build,
training/test access, security certification or publication promotion occurs.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import mpmath as mp
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.special import log_ndtr
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src import manuscript_mobility as mm
from src.binary_cloud import generate_cloud, mean_statistics, bernoulli_correlation
from src.uav_mobility import transition_distances
from scripts.recheck_manuscript_homodyne_noise import M, converted, mi_gh, security

DEFAULT=ROOT/'results/manuscript_mobility_p1_p2_p3_20261019'
CONFIG=ROOT/'configs/manuscript_mobility.json'
STRATEGIES=('Stationary','Greedy','DP')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_json(path,value):
    data=json.dumps(converted(value,precise=True),indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(data,encoding='utf-8',newline='\n');temp.replace(path)


def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text('',encoding='utf-8');return
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def bind_inputs(output,identity):
    path=output/'input_manifest.json'
    if path.exists():
        if read_json(path)!=identity:raise ValueError('Resume input/scientific identity changed; preserve this namespace')
    else:save_json(path,identity)
    return json_hash(identity)


def stage_receipt(output,stage,identity_hash,metadata,files):
    path=output/'validation'/('stage_'+stage+'.json')
    if path.exists():raise FileExistsError('Completed stage is immutable: '+stage)
    producer=sha(Path(__file__))
    snapshot=output/'validation/producers'/(producer+'.py')
    snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not snapshot.exists():snapshot.write_bytes(Path(__file__).read_bytes())
    files=list(files)+[snapshot.relative_to(output).as_posix()]
    receipt=dict(status='CURRENTLY_VERIFIED_PASS',stage=stage,input_identity_sha256=identity_hash,
        producer_sha256=producer,created_utc=datetime.now(timezone.utc).isoformat(),**metadata,
        artifact_sha256={str(name):sha(output/name) for name in files})
    save_json(path,receipt)
    return receipt


def require_stage(output,stage,identity_hash):
    receipt=read_json(output/'validation'/('stage_'+stage+'.json'))
    if receipt['status']!='CURRENTLY_VERIFIED_PASS' or receipt['input_identity_sha256']!=identity_hash:
        raise ValueError('Previous stage identity/status failed: '+stage)
    for name,value in receipt['artifact_sha256'].items():
        if sha(output/name)!=value:raise ValueError('Stage artifact changed: '+name)
    return receipt


def protect_old_files(output):
    startup=read_json(output/'startup_manifest.json');changed=[]
    for name,value in startup['protected_files'].items():
        p=ROOT/name
        if not p.is_file() or sha(p)!=value:changed.append(name)
    bad=set(changed)-set(startup['allowed_changed'])
    if bad:raise ValueError('Protected historical files changed: '+str(sorted(bad)))
    return dict(protected_files=len(startup['protected_files']),unchanged_files=len(startup['protected_files'])-len(changed),
                allowed_changed_files=changed)


def input_identity(settings,catalog,output):
    files={p for folder in ('src/channel','src/cvqkd','src/modulation') for p in (ROOT/folder).glob('*.py')}
    files.update(ROOT/name for name in ('src/manuscript_mobility.py','src/uav_mobility.py','src/binary_cloud.py',
        'scripts/exact_cache_provenance.py','scripts/recheck_manuscript_homodyne_noise.py',
        'scripts/optimize_uniform_manuscript_2d.py','scripts/run_exact_mb_test2.py',
        'scripts/run_theta10_D55_unconstrained_three_scheme.py','scripts/_common.py',
        'scripts/full_support_c4_worker.py','configs/default.yaml','configs/channel.yaml',
        settings['reference_directory']+'/run_sweep.py'))
    inputs={ROOT/item['path'] for item in settings['source_rosters'].values()}
    ref=ROOT/settings['reference_directory'];cloud=ROOT/settings['cloud']['archive_directory']
    inputs.update(ref/name for name in ('protocol.json','validation_receipt.json','all_candidate_evaluations.csv',
                                      'source_roster.csv','channel_by_angle.json'))
    inputs.update(cloud/name for name in ('inputs.json','experiment_receipt.json','cloud_scenarios.json',
                                        'cloud_states.npz','positions.csv','correlation_audit.json','final_validation.json'))
    inputs.update(ROOT/name for name in ('results/manuscript_homodyne_noise_recheck_20261019/result.json',
                                       'results/uniform_manuscript_2d_optimization_20261019/summary.json'))
    startup=read_json(output/'startup_manifest.json')
    if sha(Path(startup['manuscript_path']))!=settings['manuscript_sha256']:
        raise ValueError('Manuscript identity changed')
    return dict(schema='manuscript-mobility-identity-v1',settings=settings,
        scientific_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
        input_artifact_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(inputs)},
        source_payload_sha256={c['source_path']:c['source_sha256'] for c in catalog},
        versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                      mpmath=mp.__version__,torch=torch.__version__),
        manuscript_sha256=settings['manuscript_sha256'],git_commit=startup['commit'])


def reference_gate(output,catalog):
    ch=mm.channel_at_angle(30)
    old=read_json(ROOT/'results/manuscript_homodyne_noise_recheck_20261019/result.json')
    uni=read_json(ROOT/'results/uniform_manuscript_2d_optimization_20261019/summary.json')
    checks=[];rows=[]
    for key in ('mean_eta','mean_sqrt_eta'):
        if abs(ch[key]-M(old['high_precision_model'][key]))>=M('1e-60'):raise ValueError('Reference channel mismatch')
        checks.append(key)
    for family,nu,va,expected in [('MB',.165,5.475,old['model']['K']),('Uniform',0.,.0475,uni['best']['K_raw'])]:
        c=next(c for c in catalog if c['family']==family and c['nu_raw']==nu and c['VA']==va)
        row,_=mm.evaluate_source(c,ch)
        if abs(row['K_raw']-expected)>2e-13:raise ValueError('Reference SKR mismatch')
        rows.append(dict(**row,stored_K=expected,residual=row['K_raw']-expected));checks.append(family)
    save_json(output/'validation/reference_gate.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,
              channel=converted(ch,precise=True),rows=rows))
    return rows


def audit(output,settings,catalog,identity_hash):
    if (output/'validation/stage_audit.json').exists():raise FileExistsError('Audit already completed')
    start=time.perf_counter()
    protect_old_files(output)
    positions,geometries=mm.geometry_table(settings)
    if len(positions)!=100 or len(geometries)!=60 or len(catalog)!=233:raise ValueError('Approved coverage mismatch')
    ref=ROOT/settings['reference_directory'];receipt=read_json(ref/'validation_receipt.json')
    for name,value in receipt['artifact_sha256'].items():
        if sha(ROOT/name)!=value:raise ValueError('Historical zenith artifact changed: '+name)
    refs=reference_gate(output,catalog)
    roster=[{k:v for k,v in c.items() if k not in ('p','alpha')} for c in catalog]
    write_csv(output/'source_roster.csv',roster);write_csv(output/'positions.csv',positions)
    save_json(output/'geometry_groups.json',geometries);save_json(output/'protocol.json',settings)
    save_json(output/'environment.json',dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,
        scipy=scipy.__version__,mpmath=mp.__version__,torch=torch.__version__,torch_threads=torch.get_num_threads()))
    return stage_receipt(output,'audit',identity_hash,dict(source_count=233,positions=100,unique_geometries=60,
        reference_K=[r['K_raw'] for r in refs],elapsed_seconds=time.perf_counter()-start,
        preservation=protect_old_files(output)),['source_roster.csv','positions.csv','geometry_groups.json',
        'protocol.json','environment.json','validation/reference_gate.json'])


def rank_stability(rows):
    identities={}
    for family in ('Union','MB','Uniform'):
        subset=[r for r in rows if family=='Union' or r['family']==family]
        selected=[]
        for order in (16,32,64):
            r=min(subset,key=lambda r:(-(.95*r['MI_GH'+str(order)]-r['chi_BE']),r['nu_raw'],r['VA'],r['ensemble_hash']))
            selected.append(r['ensemble_hash'])
        if len(set(selected))!=1:raise ValueError('Unresolved GH source ranking: '+family)
        identities[family]=selected[-1]
    return identities


def numerical_controls(catalog,records,positions):
    controls=[];by_id={c['ensemble_hash']:c for c in catalog}
    chosen={min(positions,key=lambda p:p['distance_km'])['geometry_id'],
            max(positions,key=lambda p:p['distance_km'])['geometry_id'],positions[44]['geometry_id']}
    for gid in sorted(chosen):
        record=records[gid];deg=record['geometry']['zenith_deg'];ch=mm.channel_at_angle(deg)
        for family in ('Uniform','MB'):
            row=mm.select_winner([r for r in record['rows'] if r['family']==family]);c=by_id[row['ensemble_hash']]
            direct=mi_gh(c['p'],c['alpha'],row['eta_f'],row['N'],16,dimension=2)
            delta=direct-row['MI_GH16']
            if abs(delta)>2e-13:raise ValueError('Full defining2D mixture control failed')
            with mp.workdps(110):
                hi=mm.channel_at_angle(deg)
                high=security(hi['mean_eta'],hi['mean_sqrt_eta'],M(c['VA']),M(c['C']),M(c['w']))
                entropy_delta=abs(high['chi_BE']-M(record['selected_models'][family]['chi_BE']))
            # Saved models have 65-digit decimal mantissas, not all 80 working digits.
            if entropy_delta>M('1e-60'):raise ValueError('80/110-digit entropy control failed')
            controls.append(dict(kind='full_mixture_and_entropy',geometry_id=gid,family=family,
                                 MI_residual=delta,entropy_residual=mp.nstr(entropy_delta,12),passed=True))
        for q,key in ((0,'pdf_mass'),(.5,'mean_sqrt_eta'),(1,'mean_eta')):
            d,b,c1,c3,mu,p1=[float(ch[k]) for k in ('chi2','B','C1','C3','mu','P1')]
            def integrand(y):
                return math.exp(math.log(p1*d*c1/2)-d*math.log(b)+(d+q)*y+math.log(2)
                                +float(log_ndtr(-math.sqrt(2)*c3*(y-math.log(b)+mu))))
            value,error=quad(integrand,-np.inf,0,epsabs=2e-15,epsrel=2e-13,limit=400)
            if q==0:value+=float(ch['P0'])
            residual=value-float(ch[key])
            if abs(residual)>2e-13:raise ValueError('Closed/direct PDF control failed')
            controls.append(dict(kind='PDF_direct_integral',geometry_id=gid,quantity=key,
                                 residual=residual,error_estimate=error,passed=True))
    return controls


def p1(output,settings,catalog,identity_hash):
    require_stage(output,'audit',identity_hash)
    if (output/'validation/stage_p1.json').exists():raise FileExistsError('P1 is already completed')
    test=read_json(output/'validation/test_receipt.json')
    if test['status']!='CURRENTLY_VERIFIED_PASS' or test['backend_sha256']!=sha(ROOT/'src/manuscript_mobility.py'):
        raise ValueError('Current scoped tests required before P1')
    positions,geometries=mm.geometry_table(settings);records={};began=time.perf_counter()
    directory=output/'p1/geometry_records';directory.mkdir(parents=True,exist_ok=True)
    checkpoint_path=output/'p1/checkpoint.json'
    checkpoint=read_json(checkpoint_path) if checkpoint_path.exists() else dict(input_identity_sha256=identity_hash,completed={})
    if checkpoint['input_identity_sha256']!=identity_hash:raise ValueError('P1 resume identity mismatch')
    for g in geometries:
        gid=g['geometry_id'];path=directory/(gid+'.json')
        if gid in checkpoint['completed']:
            if sha(path)!=checkpoint['completed'][gid]:raise ValueError('Completed geometry record corrupted')
            record=read_json(path)
            if record['geometry']!=g or record['input_identity_sha256']!=identity_hash:raise ValueError('Geometry identity changed')
        else:
            if path.exists():raise ValueError('Uncommitted geometry record; preserve it before resuming')
            ch=mm.channel_at_angle(g['zenith_deg'])
            if abs(ch['pdf_mass']-1)>M('1e-25') or not 0<ch['mean_sqrt_eta']**2<=ch['mean_eta']<=ch['P1']<=1:
                raise ValueError('Invalid retained channel moments')
            if abs(float(ch['L_m']/1000)-g['distance_km'])>1e-10:raise ValueError('Geometry/channel distance mismatch')
            rows=[];models={}
            for c in catalog:
                row,model=mm.evaluate_source(c,ch);rows.append(row);models[c['ensemble_hash']]=model
            stable=rank_stability(rows)
            record=dict(input_identity_sha256=identity_hash,geometry=g,channel=converted(ch,precise=True),rows=rows,
                GH_winner_identities=stable,selected_models={family:converted(models[eh],precise=True) for family,eh in stable.items()},
                backend_sha256=sha(ROOT/'src/manuscript_mobility.py'))
            save_json(path,record)
            checkpoint['completed'][gid]=sha(path);save_json(checkpoint_path,checkpoint)
        records[gid]=record
        best=mm.select_winner(record['rows'])
        print('P1',len(records),'/',len(geometries),gid,'angle',g['zenith_deg'],'best',best['nu_raw'],best['VA'],best['K_raw'],flush=True)
    all_rows=[];winners=[];families=[]
    for p in positions:
        record=records[p['geometry_id']]
        for r in record['rows']:
            all_rows.append(dict(**p,**r,evaluation_origin='DIRECT' if p['position_index']==record['geometry']['position_index'] else 'EXACT_GEOMETRY_REUSE'))
        for family in ('Union','MB','Uniform'):
            subset=[r for r in record['rows'] if family=='Union' or r['family']==family]
            r=mm.select_winner(subset)
            row=dict(**p,source_group=family,**r,K_star=max(0.,r['K_raw']))
            (winners if family=='Union' else families).append(row)
    write_csv(output/'p1/candidate_evaluations.csv',all_rows)
    write_csv(output/'p1/winners.csv',winners);write_csv(output/'p1/family_winners.csv',families)
    controls=numerical_controls(catalog,records,positions)
    save_json(output/'validation/numerical_controls.json',dict(status='CURRENTLY_VERIFIED_PASS',controls=controls))
    schedule=mm.lambda_schedule([r['K_star'] for r in winners],np.array([[p['x_m'],p['y_m']] for p in positions]),settings['optimization']['reference_distance_m'])
    save_json(output/'mobility/lambda_schedule.json',schedule)
    checkpoint['status']='COMPLETE';save_json(checkpoint_path,checkpoint)
    metadata=dict(positions=100,source_count=233,unique_geometries=60,unique_source_channel_evaluations=13980,
        expanded_position_source_rows=len(all_rows),source_moments_computed=0,
        GH_max_difference=max(r['GH_max_difference'] for r in all_rows),
        minimum_uncertainty_eigenvalue=min(r['uncertainty_min_eigenvalue'] for r in all_rows),
        maximum_spectrum_residual=max(r['matrix_spectrum_max_difference'] for r in all_rows),
        raw_minimum=min(r['K_raw'] for r in winners),raw_maximum=max(r['K_raw'] for r in winners),
        family_positive_positions={f:sum(r['K_raw']>0 for r in families if r['family']==f) for f in ('MB','Uniform')},
        elapsed_seconds=time.perf_counter()-began,preservation=protect_old_files(output))
    files=['p1/candidate_evaluations.csv','p1/winners.csv','p1/family_winners.csv','p1/checkpoint.json',
           'mobility/lambda_schedule.json','validation/numerical_controls.json']
    files.extend(p.relative_to(output).as_posix() for p in sorted(directory.glob('*.json')))
    return stage_receipt(output,'p1',identity_hash,metadata,files)


def cloud(output,settings,catalog,identity_hash):
    require_stage(output,'p1',identity_hash)
    if (output/'validation/stage_cloud.json').exists():raise FileExistsError('Cloud stage completed')
    old=ROOT/settings['cloud']['archive_directory'];receipt=read_json(old/'experiment_receipt.json')
    if read_json(old/'final_validation.json')['status']!='CURRENTLY_VERIFIED_PASS':
        raise ValueError('Cloud archive independent validation is not PASS')
    original=read_json(old/'inputs.json')['settings'];positions=mm.validate_config(settings)
    for name in ('cloud_states.npz','cloud_scenarios.json'):
        if sha(old/name)!=receipt['output_sha256'][name]:raise ValueError('Cloud archive hash mismatch')
    if sha(ROOT/'src/binary_cloud.py')!=receipt['producers']['src/binary_cloud.py']:raise ValueError('Cloud generator changed')
    saved_positions=mm.read_csv(old/'positions.csv')
    if not np.array_equal(positions,np.array([[float(r['x_m']),float(r['y_m'])] for r in saved_positions])):raise ValueError('Cloud positions changed')
    cset=settings['cloud'];mission=settings['mission']
    for key in ('probability','correlation_length_m','temporal_rho','seed','realizations'):
        if cset[key]!=original['cloud'][key]:raise ValueError('Cloud scenario changed')
    if mission!=original['mission']:raise ValueError('Cloud timing changed')
    scenario=read_json(old/'cloud_scenarios.json')[cset['scenario_id']]
    if [scenario[k] for k in ('probability','correlation_length_m','temporal_rho')]!=[cset[k] for k in ('probability','correlation_length_m','temporal_rho')]:
        raise ValueError('Cloud scenario index mismatch')
    with np.load(old/'cloud_states.npz',allow_pickle=False) as data:blocked=data['blocked'][cset['scenario_id']].copy()
    if blocked.dtype!=np.bool_ or blocked.shape!=(100,100,30):raise ValueError('Cloud shape/value mismatch')
    replays=[]
    for rid in (0,1,99):
        fresh=generate_cloud(positions,mission['slots'],cset['probability'],cset['correlation_length_m'],cset['temporal_rho'],cset['seed'],rid)
        if not np.array_equal(fresh,blocked[rid]):raise ValueError('Cloud seed replay failed')
        replays.append(rid)
    winners=mm.read_csv(output/'p1/winners.csv');K=np.array([float(r['K_star']) for r in winners])
    S=(~blocked)*K[None,:,None]
    if np.any(S[blocked]!=0):raise ValueError('Complete blockage failed')
    (output/'clouds').mkdir(exist_ok=True)
    np.savez_compressed(output/'clouds/states.npz',blocked=blocked,usable_skr=S)
    free=(~blocked).mean(axis=2)
    write_csv(output/'clouds/cloud_free_fraction.csv',[dict(realization_id=rid,position_index=j,clear_fraction=float(free[rid,j])) for rid in range(100) for j in range(100)])
    p=cset['probability'];standard=(blocked.astype(float)-p)/math.sqrt(p*(1-p))
    distance=transition_distances(positions);near=int(np.argsort(distance[0])[1]);far=int(np.argmax(distance[0]))
    stats=[]
    values={'blockage_probability':blocked.mean(axis=(1,2)),
            'binary_spatial_near':np.mean(standard[:,0,:]*standard[:,near,:],axis=1),
            'binary_spatial_far':np.mean(standard[:,0,:]*standard[:,far,:],axis=1),
            'binary_temporal':np.mean(standard[:,:,:-1]*standard[:,:,1:],axis=(1,2))}
    targets={'blockage_probability':p,'binary_spatial_near':bernoulli_correlation(p,math.exp(-distance[0,near]/cset['correlation_length_m'])),
             'binary_spatial_far':bernoulli_correlation(p,math.exp(-distance[0,far]/cset['correlation_length_m'])),
             'binary_temporal':bernoulli_correlation(p,cset['temporal_rho'])}
    for key,values_at_mission in values.items():
        s=mean_statistics(values_at_mission);tol=5*s['se']+1e-10
        if abs(s['mean']-targets[key])>tol:raise ValueError('Cloud cluster correlation audit failed: '+key)
        stats.append(dict(metric=key,target=targets[key],**s,tolerance=tol,passed=True))
    save_json(output/'clouds/correlation_audit.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=stats,
        tau_latent_s=-mission['slot_duration_s']/math.log(cset['temporal_rho']),seed_replays=replays,
        independent_missions=100,latent_parameters_are_not_Bernoulli_correlations=True))
    return stage_receipt(output,'cloud',identity_hash,dict(reused_missions=100,seed_replays=replays,
        complete_blockage=True,source_or_SKR_evaluations=0,preservation=protect_old_files(output)),
        ['clouds/states.npz','clouds/cloud_free_fraction.csv','clouds/correlation_audit.json'])


def literal_dp_score(S,positions,settings,penalty):
    d=transition_distances(positions);m=settings['mission'];opt=settings['optimization'];nt=S.shape[1]
    feasible=d<=m['slot_duration_s']*m['max_speed_m_per_s'];F=S[:,0].copy()
    for n in range(1,nt):
        proposal=F[:,None]-nt*penalty*d/opt['reference_distance_m']
        F=S[:,n]+np.max(np.where(feasible,proposal,-np.inf),axis=0)
    return float(F.max()/nt)


def compare(output,settings,catalog,identity_hash):
    require_stage(output,'cloud',identity_hash)
    if (output/'validation/stage_compare.json').exists():raise FileExistsError('Comparison already completed')
    began=time.perf_counter();positions=mm.validate_config(settings);m=settings['mission'];opt=settings['optimization']
    schedule=read_json(output/'mobility/lambda_schedule.json');penalties=schedule['values']
    with np.load(output/'clouds/states.npz',allow_pickle=False) as z:C=z['blocked'];S=z['usable_skr']
    winners=mm.read_csv(output/'p1/winners.csv');summaries=[];series=[];checks=[]
    paths_all=np.empty((100,len(penalties),3,30),dtype=np.int16)
    for rid in range(100):
        previous_distance=math.inf
        stationary_reference=None
        for li,penalty in enumerate(penalties):
            summary,paths,steps=mm.compare_paths(S[rid],C[rid],positions,slot_duration_s=m['slot_duration_s'],
                max_speed_m_per_s=m['max_speed_m_per_s'],penalty_bits_per_use=penalty,reference_distance_m=opt['reference_distance_m'])
            meta=dict(realization_id=rid,lambda_index=li,lambda_bits_per_use=penalty,
                      lambda_multiplier=schedule['multipliers'][li])
            lookup={r['strategy']:r for r in summary};dp=lookup['DP']
            if dp['total_distance_m']>previous_distance+1e-9:raise ValueError('DP distance increased with penalty')
            previous_distance=dp['total_distance_m']
            stationary=lookup['Stationary']
            if stationary_reference is None:stationary_reference=stationary
            elif stationary['average_skr_bits_per_use']!=stationary_reference['average_skr_bits_per_use'] or stationary['initial_position_index']!=stationary_reference['initial_position_index']:
                raise ValueError('P2 changed with lambda')
            literal=literal_dp_score(S[rid],positions,settings,penalty)
            if not math.isclose(literal,dp['objective_bits_per_use'],abs_tol=1e-12,rel_tol=1e-12):raise ValueError('Literal Nt-lambda Bellman mismatch')
            checks.append(dict(realization_id=rid,lambda_index=li,DP_objective=dp['objective_bits_per_use'],
                               literal_cumulative_objective=literal,residual=dp['objective_bits_per_use']-literal))
            for si,name in enumerate(STRATEGIES):paths_all[rid,li,si]=paths[name]
            for r in summary:
                delta=r['average_skr_bits_per_use']-stationary['average_skr_bits_per_use']
                ud=r['objective_bits_per_use']-stationary['objective_bits_per_use']
                summaries.append(dict(**meta,**r,improvement_vs_stationary_absolute=delta,
                    improvement_vs_stationary_percent=100*delta/stationary['average_skr_bits_per_use'] if stationary['average_skr_bits_per_use']>0 else None,
                    objective_improvement_vs_stationary_absolute=ud,
                    objective_improvement_vs_stationary_percent=100*ud/stationary['objective_bits_per_use'] if stationary['objective_bits_per_use']>0 else None))
            for r in steps:
                source=winners[r['position_index']]
                series.append(dict(**meta,**r,nu_raw=float(source['nu_raw']),VA=float(source['VA']),
                                   ensemble_hash=source['ensemble_hash'],clear_raw_skr=float(source['K_raw'])))
        if rid%10==0:print('MISSIONS',rid+1,'/100',flush=True)
    np.savez_compressed(output/'mobility/paths.npz',paths=paths_all,lambda_values=np.array(penalties))
    write_csv(output/'mobility/mission_metrics.csv',summaries);write_csv(output/'mobility/time_series.csv',series)
    selected=[r for r in summaries if r['lambda_bits_per_use']==schedule['representative']]
    demo=[r for r in series if r['realization_id']==0 and r['lambda_bits_per_use']==schedule['representative']]
    write_csv(output/'mobility/representative_metrics.csv',[r for r in selected if r['realization_id']==0])
    write_csv(output/'mobility/representative_paths.csv',demo)
    write_csv(output/'mobility/p2_positions.csv',[r for r in summaries if r['strategy']=='Stationary' and r['lambda_index']==0])
    statistics=[];paired=[]
    metrics=('average_skr_bits_per_use','total_distance_m','objective_bits_per_use','availability','repositionings','blocked_slots','positive_slots')
    for li,penalty in enumerate(penalties):
        for name in STRATEGIES:
            group=[r for r in summaries if r['lambda_index']==li and r['strategy']==name]
            for metric in metrics:
                statistics.append(dict(lambda_index=li,lambda_bits_per_use=penalty,strategy=name,metric=metric,
                                       **mean_statistics([r[metric] for r in group])))
        for left,right in (('DP','Stationary'),('DP','Greedy'),('Greedy','Stationary')):
            a=sorted([r for r in summaries if r['lambda_index']==li and r['strategy']==left],key=lambda r:r['realization_id'])
            b=sorted([r for r in summaries if r['lambda_index']==li and r['strategy']==right],key=lambda r:r['realization_id'])
            for metric in ('average_skr_bits_per_use','objective_bits_per_use'):
                paired.append(dict(lambda_index=li,lambda_bits_per_use=penalty,comparison=left+'-'+right,metric=metric,
                                   **mean_statistics([x[metric]-y[metric] for x,y in zip(a,b)])))
    write_csv(output/'mobility/lambda_statistics.csv',statistics);write_csv(output/'mobility/paired_statistics.csv',paired)
    write_csv(output/'validation/literal_Bellman_checks.csv',checks)
    return stage_receipt(output,'compare',identity_hash,dict(missions=100,penalties=len(penalties),DP_calls=100*len(penalties),
        Greedy_calls=100*len(penalties),literal_Bellman_checks=len(checks),maximum_Bellman_residual=max(abs(r['residual']) for r in checks),
        elapsed_seconds=time.perf_counter()-began,preservation=protect_old_files(output)),
        ['mobility/paths.npz','mobility/mission_metrics.csv','mobility/time_series.csv','mobility/representative_metrics.csv',
         'mobility/representative_paths.csv','mobility/p2_positions.csv','mobility/lambda_statistics.csv',
         'mobility/paired_statistics.csv','validation/literal_Bellman_checks.csv'])


def distance_comparison(output,settings,catalog,identity_hash):
    path=output/'validation/stage_distance.json'
    if path.exists():return require_stage(output,'distance',identity_hash)
    old=ROOT/settings['reference_directory'];rows=mm.read_csv(old/'all_candidate_evaluations.csv')
    current={c['ensemble_hash']:c for c in catalog};old_ids={r['ensemble_hash'] for r in rows}
    numeric=('zenith_deg','distance_km','nu_raw','VA','C','w','I_AB_2D','beta_I_AB','chi_BE','K_raw','eta_f','xi_f','N',
             'V','W','Z','nu_1','nu_2','nu_3','MI_GH16','MI_GH32','MI_GH64','GH_max_difference',
             'uncertainty_min_eigenvalue','matrix_spectrum_max_difference')
    imported=[]
    for r in rows:
        c=current[r['ensemble_hash']]
        if r['source_sha256']!=c['source_sha256'] or any(float(r[k])!=c[k] for k in ('nu_raw','VA','C','w')):
            raise ValueError('Distance source reuse mismatch')
        imported.append(dict(**{k:float(r[k]) for k in numeric},family=r['family'],ensemble_hash=r['ensemble_hash'],
                             source_sha256=r['source_sha256'],evaluation_origin='VERIFIED_ZENITH_REUSE'))
    extra=[c for c in catalog if c['ensemble_hash'] not in old_ids]
    if len(imported)!=6758 or len(extra)!=15:raise ValueError('Distance reuse coverage mismatch')
    additions=[];table=[]
    for deg in range(0,61,2):
        ch=mm.channel_at_angle(deg)
        for c in extra:
            row,_=mm.evaluate_source(c,ch)
            additions.append(dict(zenith_deg=float(deg),distance_km=float(ch['L_m']/1000),**row,evaluation_origin='NEW_EXISTING_SOURCE'))
        group=[r for r in imported+additions if r['zenith_deg']==deg]
        if len(group)!=233:raise ValueError('Distance catalog incomplete')
        uniform=mm.select_winner([r for r in group if r['family']=='Uniform'])
        mb=mm.select_winner([r for r in group if r['family']=='MB'])
        fixed=next(r for r in group if r['nu_raw']==.165 and r['VA']==5.475)
        table.append(dict(distance_km=float(ch['L_m']/1000),zenith_deg=deg,Uniform_optimal_VA=uniform['VA'],
            Uniform_K_raw=uniform['K_raw'],Fixed_MB_K_raw=fixed['K_raw'],MB_optimal_nu_raw=mb['nu_raw'],
            MB_optimal_VA=mb['VA'],Optimized_MB_K_raw=mb['K_raw']))
        print('DISTANCE_EXTRA',deg,'/60',flush=True)
    write_csv(output/'figures/figure1_candidate_evaluations.csv',imported+additions)
    write_csv(output/'figures/figure1_distance.csv',table)
    regions=[]
    for scheme,key in zip(('Optimized Uniform','Fixed MB','Optimized MB'),('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw')):
        positive=[r for r in table if r[key]>0]
        brackets=[dict(lower_km=a['distance_km'],upper_km=b['distance_km'],direction='positive_to_nonpositive' if a[key]>0 else 'nonpositive_to_positive')
                  for a,b in zip(table,table[1:]) if (a[key]>0)!=(b[key]>0)]
        regions.append(dict(scheme=scheme,first_tested_positive_km=positive[0]['distance_km'] if positive else None,
            last_tested_positive_km=positive[-1]['distance_km'] if positive else None,
            positive_through_upper_boundary=bool(table[-1][key]>0),tested_sign_change_brackets=json.dumps(brackets)))
    write_csv(output/'figures/figure1_operating_regions.csv',regions)
    return stage_receipt(output,'distance',identity_hash,dict(reused_candidate_rows=6758,new_candidate_rows=465,source_moments_computed=0),
        ['figures/figure1_candidate_evaluations.csv','figures/figure1_distance.csv','figures/figure1_operating_regions.csv'])


def write_report(output,settings):
    p1r=read_json(output/'validation/stage_p1.json');compare_r=read_json(output/'validation/stage_compare.json')
    schedule=read_json(output/'mobility/lambda_schedule.json');metrics=mm.read_csv(output/'mobility/representative_metrics.csv')
    winners=mm.read_csv(output/'p1/winners.csv');families=mm.read_csv(output/'p1/family_winners.csv')
    stats=mm.read_csv(output/'mobility/lambda_statistics.csv')
    lines=['# P1–P2–P3 và Greedy: so sánh số HAP–UAV theo bản thảo','',
      '**UNVALIDATED_SECURITY_MODEL — NOT_READY_FOR_PUBLICATION_SCALE_RUNS**. '
      'MI 2D/Holevo homodyne là quy ước so sánh số theo yêu cầu; chưa phải chứng minh an toàn homodyne.','',
      '## Mô hình và nguồn','',
      'HAP (11419.65511459133,450,20000) m; UAV cao1000m,100 tâm ô50–950m. '
      '30slot×20s, vmax15m/s, Dref1000m, khởi đầu tự chọn, không chi phí triển khai/đường về. '
      'Hình học và mây là giả định tổng hợp được người dùng chọn; bản thảo chưa cho số cụ thể.','',
      'Quang học1550nm, phân kỳ toàn phần233µrad, đường kính thu.08m, tauzen.92, jitter15.61µrad, '
      'sigma_h1m, boresight0, AoA1.5mrad, FOV nửa góc6.25mrad, HV/gió21m/s/Cn2ground1e-14. '
      'HV/Gd dùng cùng closure repository đã công khai trong lần recheck. beta.95, xi_ch.0186, R1/xi_det0.','',
      'eta_f=<sqrt(eta)>²; N=(<eta>−eta_f)VA+.0186<eta>; xi_f=N/eta_f. '
      'MI chuẩn hóa2D, trung bình2sqrt(eta_f)alpha, phương sai từng trục1+N, không chia2; '
      'Holevo giữ nu3=sqrt[V(V−Z²/W)]. VA=2<n>. PDF[0,1] giữ nguyên tử outage, không chuẩn hóa lại.','',
      f'233 nguồn exact(197MB+36Uniform), không tính C,w/AP/AO mới. '
      f'P1 có100 vị trí,60 hình học chính xác,13980 lượt SKR và23300 hàng vị trí–nguồn. '
      f'RawK tốt nhất theo vị trí từ{p1r["raw_minimum"]:.12g} đến{p1r["raw_maximum"]:.12g} bits/use. '
      f'Số vị trí dương theo họ: {p1r["family_positive_positions"]}.','',
      'P1 tối đa raw trước khi lấy phần dương. Hòa theo ν,VA,ensemble hash tăng dần. '
      'N và xi_f tính lại theo VA từng nguồn; chỉ moment kênh được chia sẻ theo danh tính hình học chính xác. '
      'Catalog MBnu.05–.8/VA.025–8, UniformVA.02–12; biên catalog không phải tối ưu liên tục.','',
      '## Mây và thông tin','',
      'Dùng lại đúng100 ma trận mây scenario0 đã xác thực: PCG64 SeedSequence([20261015,id]), '
      'p.4, ell250m, AR1rho.9; replayID0,1,99. Covariance Gaussian exp(−d/ell); '
      'c=1[z<Phi^-1(p)]. Thời gian tương quan tiềm ẩn khoảng190s; hệ số Bernoulli được tính từ tích phân ngưỡng. '
      'S=(1−c)Kstar, chặn hoàn toàn bằng0; không tính kênh lượng tử lần nữa khi chặn.','',
      'P2 và DP biết toàn bộ cloud horizon, là benchmark offline. Greedy chỉ nhận slot hiện tại. '
      'Nguồn được tối ưu một lần mỗi vị trí, dùng lại ở các slot thông thoáng; không tối ưu nguồn theo slot.','',
      '## P2, Greedy và DP','',
      'U=mean(S_path)−lambda*D/Dref. DP hiện có lưu F/Nt; đã đối chiếu recursion tích lũy '
      'F1=S1 và penalty Nt*lambda với đánh giá trực tiếp. Greedy dùng cùng Nt*lambda, speed và free-start. '
      'Không ép các chiến lược chọn cùng điểm đầu. Availability=mean(S>0), không dùng ngưỡng demo0.001.','',
      f'lambda_hi=2*Kmax*Dref/dmin={schedule["lambda_hi"]:.12g} bits/use; '
      f'dmin={schedule["d_min_m"]}m. Dải hệ số {schedule["multipliers"]}; '
      f'hình quỹ đạo dùng lambda={schedule["representative"]:.12g}, nhiệm vụID0, chốt trước khi xem đường đi.','',
      '| Phương án | SKR trung bình | Khoảng cách (m) | U | Slot dương | Điểm đầu→cuối (index0) |',
      '|---|---:|---:|---:|---:|---|']
    for r in metrics:lines.append(f'|{r["strategy"]}|{float(r["average_skr_bits_per_use"]):.12g}|{float(r["total_distance_m"]):.6g}|{float(r["objective_bits_per_use"]):.12g}|{r["positive_slots"]}|{r["initial_position_index"]}→{r["final_position_index"]}|')
    lines+=['','Đây là nhiệm vụ minh họa đã chọn trước. Thống kê chính dùng100 nhiệm vụ độc lập và CI95% t-Student; '
      'chênh lệch so sánh theo cặp cùng seed/ID. Phần trăm chỉ có khi mẫu số dương.','',
      '| Phương án | Mean SKR tại λ minh họa | Mean distance (m) | Mean U |','|---|---:|---:|---:|']
    for name in STRATEGIES:
        selected={r['metric']:float(r['mean']) for r in stats if r['strategy']==name and float(r['lambda_bits_per_use'])==schedule['representative']}
        lines.append(f'|{name}|{selected["average_skr_bits_per_use"]:.12g}|{selected["total_distance_m"]:.6g}|{selected["objective_bits_per_use"]:.12g}|')
    lines+=['','DP tối đa U, không nhất thiết tối đa SKR trung bình khi lambda>0. '
      'Giá trị dương/nâng cao thống kê không suy ra bảo mật hoặc hiệu quả năng lượng đẩy.','',
      '## Kiểm chứng và truy vết','',
      f'Reference30deg được kiểm tra trước P1; GH16/32/64 trên mọi ứng viên: max delta{p1r["GH_max_difference"]:.6g} bit. '
      f'Min eig(Gamma+iOmega)={p1r["minimum_uncertainty_eigenvalue"]:.6g}; '
      f'phổ symplectic sai khác tối đa{p1r["maximum_spectrum_residual"]:.6g}. '
      'Đối chiếu PDF bằng tích phân trực tiếp, MI bằng hỗn hợp256 đầy đủ và entropy80/110digit ở ba vị trí đại diện.','',
      f'{compare_r["literal_Bellman_checks"]} đối chiếu Bellman độc lập, sai khác lớn nhất'
      f'{compare_r["maximum_Bellman_residual"]:.6g}. Vét cạn nhỏ, v0, N1, lambda0/cao, '
      'P1 toàn âm, mây toàn chặn/thông, Greedy causal và kiểm tra provenance nằm trong tests/receipts.','',
      'Figure1 dùng6758 hàng đã xác thực và thêm465 lượt cho15 nguồn MB sẵn có; '
      'xếp hạng lại toàn catalog ở31 khoảng cách. Đây là biểu diễn khoảng cách của cùng hình học h20/1km, '
      'không lấy đường SKR từ cấu hình.55m/10µrad cũ. Vùng dương chỉ báo theo các điểm và khoảng đổi dấu đã đo.','',
      '## Giới hạn và bảo toàn','',
      'Finite-catalog best-tested và finite-grid offline optimum cho ma trận mây đã cho; '
      'không có tối ưu liên tục/toàn miền hoặc matched-energy shaping claim. Chưa có propagation/transit '
      'time overhead, calibration propulsion, channel-use rate hay finite-size/composable key proof. '
      'Không suy ra tổng bits hoặc bits/J từ bits/use.','',
      'Chênh lệch hash frozen lịch sử vẫn giữ nguyên; không chỉnh frozen, mô hình production, '
      'source/security helpers, dữ liệu/cache cũ hoặc ObjectiveC. Không training/test-data/final-test/held-out/ '
      'publication evaluation, baseline/threshold certification, external manuscript edit, commit/push.','',
      '## Hình và dữ liệu','',
      '![Figure1](figures/fig1_skr_distance.png)','',
      '![Figure2](figures/fig2_cloud_trajectories.png)','',
      '![Figure3](figures/fig3_mobility_tradeoff.png)','',
      'CSV/NPZ ở p1/,clouds/,mobility/,figures/plot_data; mọi hình có vectorPDF vàPNG350dpi. '
      'validation/stage_*.json ràng buộc artifact và producer snapshot; validation/final_verification.json '
      'kiểm tra dữ liệu đã lưu mà không chạy lại SKR.']
    (output/'report_vi.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


def export(output,settings,catalog,identity_hash):
    require_stage(output,'compare',identity_hash)
    if (output/'validation/stage_export.json').exists():raise FileExistsError('Export already completed')
    distance_comparison(output,settings,catalog,identity_hash)
    from scripts.plot_manuscript_mobility import export_results
    export_results(output,settings)
    write_report(output,settings)
    files=[p.relative_to(output).as_posix() for p in sorted((output/'figures').rglob('*')) if p.is_file()]
    files+=['report_vi.md']
    return stage_receipt(output,'export',identity_hash,dict(plot_producer_sha256=sha(ROOT/'scripts/plot_manuscript_mobility.py'),
        preservation=protect_old_files(output)),files)


def verify(output,settings,catalog,identity_hash):
    checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    for stage in ('audit','p1','cloud','compare','distance','export'):require_stage(output,stage,identity_hash)
    check('stage_hashes',True)
    identities=read_json(output/'input_manifest.json')
    for field in ('scientific_files_sha256','input_artifact_sha256','source_payload_sha256'):
        for name,digest in identities[field].items():check('input:'+name,sha(ROOT/name)==digest)
    preservation=protect_old_files(output);positions=mm.validate_config(settings)
    rows=mm.read_csv(output/'p1/candidate_evaluations.csv');winners=mm.read_csv(output/'p1/winners.csv')
    check('complete_P1',len(rows)==23300 and len(winners)==100)
    source={c['ensemble_hash']:c for c in catalog}
    channel_records={p.stem:read_json(p)['channel'] for p in (output/'p1/geometry_records').glob('*.json')}
    groups={j:[] for j in range(100)}
    for r in rows:
        c=source[r['ensemble_hash']];groups[int(r['position_index'])].append(r)
        assert all(float(r[k])==c[k] for k in ('VA','nu_raw','C','w'))
        assert r['source_sha256']==c['source_sha256']
        assert abs(.95*float(r['I_AB_2D'])-float(r['chi_BE'])-float(r['K_raw']))<1e-17
        assert max(abs(float(r['MI_GH'+str(q)])-float(r['MI_GH64'])) for q in (16,32,64))<=2e-13
        assert float(r['uncertainty_min_eigenvalue'])>0 and min(float(r[k]) for k in ('nu_1','nu_2','nu_3'))>=1
        ch=channel_records[r['geometry_id']];m1,mh=float(ch['mean_eta']),float(ch['mean_sqrt_eta'])
        noise=(m1-mh*mh)*float(r['VA'])+.0186*m1
        assert abs(noise-float(r['N']))<1e-18 and abs(float(r['eta_f'])-mh*mh)<1e-18
        assert abs(float(r['W'])-(1+float(r['eta_f'])*float(r['VA'])+noise))<1e-14
    for w in winners:
        group=groups[int(w['position_index'])];assert len(group)==233
        best=min(group,key=lambda r:(-float(r['K_raw']),float(r['nu_raw']),float(r['VA']),r['ensemble_hash']))
        assert w['ensemble_hash']==best['ensemble_hash'] and float(w['K_raw'])==float(best['K_raw'])
        assert float(w['K_star'])==max(0.,float(w['K_raw']))
    check('all_source_identity_raw_argmax_GH_physicality',True)
    with np.load(output/'clouds/states.npz',allow_pickle=False) as z:C=z['blocked'];S=z['usable_skr']
    rates=np.array([float(w['K_star']) for w in winners])
    check('cloud_and_S',C.dtype==np.bool_ and C.shape==(100,100,30) and np.array_equal(S,(~C)*rates[None,:,None]))
    schedule=read_json(output/'mobility/lambda_schedule.json');metrics=mm.read_csv(output/'mobility/mission_metrics.csv')
    with np.load(output/'mobility/paths.npz',allow_pickle=False) as z:paths=z['paths'];lambdas=z['lambda_values']
    d=transition_distances(positions)
    for r in metrics:
        rid,li,si=int(r['realization_id']),int(r['lambda_index']),STRATEGIES.index(r['strategy'])
        path=paths[rid,li,si];legs=d[path[:-1],path[1:]];selected=S[rid,path,np.arange(30)]
        assert np.all((path>=0)&(path<100)) and np.all(legs<=300)
        assert math.isclose(float(r['average_skr_bits_per_use']),float(selected.mean()),abs_tol=1e-12,rel_tol=1e-12)
        assert math.isclose(float(r['total_distance_m']),float(legs.sum()),abs_tol=1e-9,rel_tol=1e-12)
        assert math.isclose(float(r['objective_bits_per_use']),float(selected.mean())-lambdas[li]*legs.sum()/1000,abs_tol=1e-12,rel_tol=1e-12)
        assert int(r['positive_slots'])==int(sum(selected>0)) and int(r['blocked_slots'])==int(sum(C[rid,path,np.arange(30)]))
        if si==0:assert len(set(path))==1 and legs.sum()==0
    check('every_saved_path_feasible_and_metric_exact',True)
    check('visual_review',read_json(output/'validation/visual_review.json')['status']=='CURRENTLY_VERIFIED_PASS')
    from PIL import Image
    figures=[]
    for p in sorted((output/'figures').glob('*.png')):
        with Image.open(p) as im:
            check('PNG:'+p.name,min(im.info['dpi'])>=349)
            figures.append(dict(name=p.name,pixels=list(im.size),dpi=list(im.info['dpi'])))
        pdf=p.with_suffix('.pdf');raw=pdf.read_bytes()
        check('PDF:'+pdf.name,raw.startswith(b'%PDF') and b'/Subtype /Image' not in raw)
    check('scientific_scope',settings['lifecycle']=='NOT_READY_FOR_PUBLICATION_SCALE_RUNS' and settings['security_status']=='UNVALIDATED_SECURITY_MODEL')
    result=dict(status='CURRENTLY_VERIFIED_PASS',checks=len(checks),check_names=checks,preservation=preservation,
        figures=figures,saved_artifact_verification_only=True,source_moments_recomputed=False,
        artifacts_sha256={p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*'))
                          if p.is_file() and p.name not in ('final_verification.json',) and p.suffix!='.log'},
        scope='MANUSCRIPT_STYLE_NUMERICAL_COMPARISON_NOT_VALIDATED_HOMODYNE_SECURITY')
    final=output/'validation/final_verification.json'
    if final.exists():
        if read_json(final)!=result:raise ValueError('Saved final verification receipt changed')
    else:save_json(final,result)
    print('FINAL_VERIFICATION PASS',len(checks),'checks;',preservation,flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('audit','p1','cloud','compare','export','verify'),required=True)
    parser.add_argument('--config',type=Path,default=CONFIG);parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args();output=args.output.resolve()
    if not output.is_relative_to(ROOT/'results'):raise ValueError('Use an isolated project results namespace')
    if not (output/'startup_manifest.json').exists():raise ValueError('Create and review startup manifest before numerical execution')
    torch.set_num_threads(1);mp.mp.dps=80
    settings=read_json(args.config);mm.validate_config(settings);catalog=mm.load_catalog(settings)
    identity=input_identity(settings,catalog,output);identity_hash=bind_inputs(output,identity)
    function={'audit':audit,'p1':p1,'cloud':cloud,'compare':compare,'export':export,'verify':verify}[args.stage]
    receipt=function(output,settings,catalog,identity_hash)
    print('STAGE',args.stage,'CURRENTLY_VERIFIED_PASS',flush=True)


if __name__=='__main__':main()
