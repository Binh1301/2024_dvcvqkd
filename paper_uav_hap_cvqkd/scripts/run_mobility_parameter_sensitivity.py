"""Approved Stage A: archived masks and source rates, existing mobility solvers only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import time

import numpy as np
from scipy.sparse.csgraph import connected_components

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.uav_mobility import best_stationary, optimize_trajectory, transition_distances
from src.manuscript_mobility import greedy_trajectory

METHODS=('Stationary','Greedy','DP')
METRICS=('K','U','D','availability','unavailability_percent','repositionings','blocked_slots','positive_slots')
LAMBDAS=(0.,9.468026677248516e-6)
AXES=('J','speed','horizon','probability','spatial')
CODE=('configs/mobility_parameter_sensitivity.json','scripts/run_mobility_parameter_sensitivity.py',
      'scripts/plot_mobility_parameter_sensitivity.py','tests/test_mobility_parameter_sensitivity.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save_json(path,value):Path(path).write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def same(a,b):return np.allclose(a,b,atol=1e-12,rtol=1e-12)
def require(condition,message):
    if not bool(np.all(condition)):raise ValueError(message)


def validate_config(c):
    expected={'candidate_counts':[10,20,40,60,80,100],'speeds_m_per_s':[0,2.5,5,7.5,10,15,20,25],
        'horizons':[5,10,15,20,25,30],'probabilities':[.1,.2,.4,.6,.8],
        'spatial_lengths_m':[50,100,250,500,1000],'lambda_values':list(LAMBDAS),
        'missions':100,'slot_duration_s':20,'reference_distance_m':1000,'stage':'A',
        'new_cloud_generation_allowed':False,'new_physical_skr_allowed':False,'stage_b_allowed':False,
        'absolute_tolerance':1e-12,'relative_tolerance':1e-12,
        'reference_directory':'results/manuscript_mobility_p1_p2_p3_20261019',
        'archive_directory':'results/binary_cloud_skr_20261015',
        'output_directory':'results/mobility_parameter_sensitivity_20261020',
        'availability_rule':'S > 0; no engineering threshold'}
    require(all(c.get(k)==v for k,v in expected.items()),'Configuration differs from explicit Stage A approval')
    require(c['bootstrap']=={'resamples':20000,'seed':20261020,'unit':'whole paired mission','interval':'pointwise percentile 95%'},'Bootstrap identity differs')
    require(c['security_status']=='UNVALIDATED_SECURITY_MODEL' and c['lifecycle']=='NOT_READY_FOR_PUBLICATION_SCALE_RUNS','Scope status differs')


def preserve(out):
    startup=read_json(out/'startup_manifest.json');changed=[]
    for name,digest in startup['protected_files'].items():
        if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:changed.append(name)
    require(set(changed)<=set(startup['allowed_changed']),'Protected existing files changed: '+str(changed))
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--','.'],cwd=ROOT,text=True).splitlines()
    new=set(names)-set(startup['protected_files'])
    require(all(n in startup['allowed_new_code'] or n.startswith(startup['allowed_output_prefix']) for n in new),'Unexpected new project files')
    for command,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        require(subprocess.check_output(command,cwd=ROOT,text=True).strip()==startup[key],'Git '+key+' changed')
    return dict(protected_files=len(startup['protected_files']),allowed_changed_files=startup['allowed_changed'],
                frozen_sha256_actual=sha(ROOT/'docs/FINAL_MODEL_SPEC.md'),historical_hash_conflict_preserved=True)


def nested_order(positions):
    p=np.asarray(positions,dtype=float)
    expected=np.array([(x,y) for y in range(50,1000,100) for x in range(50,1000,100)],dtype=float)
    require(np.array_equal(p,expected),'Nested design requires the original x-first 100-cell grid')
    quadrants=(p[:,0]>=500).astype(int)+2*(p[:,1]>=500).astype(int)
    d2=np.sum((p[:,None]-p[None,:])**2,axis=-1)
    order=[0,9,90,99]
    while len(order)<100:
        counts=np.bincount(quadrants[order],minlength=4)
        candidates=[j for j in range(100) if j not in order and counts[quadrants[j]]==counts.min()]
        chosen=min(candidates,key=lambda j:(-float(d2[j,order].min()),j))
        order.append(chosen)
    return order


def make_cases(c,positions,scenarios):
    order=nested_order(positions)
    base=dict(case_id='base',J=100,Nt=30,speed=15.,scenario_id=0,probability=.4,spatial=250.,rho=.9,indices=list(range(100)))
    cases=[base];members=[]
    specifications=[('J',c['candidate_counts']),('speed',c['speeds_m_per_s']),('horizon',c['horizons']),
                    ('probability',c['probabilities']),('spatial',c['spatial_lengths_m'])]
    defaults={'J':100,'speed':15,'horizon':30,'probability':.4,'spatial':250}
    for axis,values in specifications:
        for value in values:
            if value==defaults[axis]:case=base
            else:
                case=dict(base,case_id=axis+'_'+str(value).replace('.','p'),indices=base['indices'].copy())
                if axis=='J':case.update(J=int(value),indices=sorted(order[:int(value)]))
                elif axis=='speed':case['speed']=float(value)
                elif axis=='horizon':case['Nt']=int(value)
                else:
                    case[axis]=float(value)
                    matches=[s for s in scenarios if (s['probability'],s['correlation_length_m'],s['temporal_rho'])==(case['probability'],case['spatial'],case['rho'])]
                    require(len(matches)==1,'Approved scenario missing or ambiguous: '+str((axis,value)))
                    case['scenario_id']=matches[0]['scenario_id']
                cases.append(case)
            members.append(dict(axis=axis,value=value,case_id=case['case_id']))
    require(len(cases)==26 and len({x['case_id'] for x in cases})==26,'Case coverage differs')
    return cases,members,order


def path_metrics(S,C,positions,path,penalty,speed,dt=20,reference=1000):
    path=np.asarray(path)
    require(path.shape==(S.shape[1],) and np.issubdtype(path.dtype,np.integer),'Invalid path shape or dtype')
    require((path>=0)&(path<len(S)),'Path index outside subset')
    rates=S[path,np.arange(S.shape[1])]
    legs=np.linalg.norm(np.diff(positions[path],axis=0),axis=1)
    require(legs<=speed*dt+1e-12,'Infeasible path')
    distance=float(legs.sum());positive=int(np.count_nonzero(rates>0))
    return dict(K=float(rates.mean()),U=float(rates.mean())-penalty*distance/reference,D=distance,
        availability=positive/len(path),unavailability_percent=100*(1-positive/len(path)),
        repositionings=int(np.count_nonzero(np.diff(path))),blocked_slots=int(C[path,np.arange(len(path))].sum()),
        positive_slots=positive,initial_position_index=int(path[0]),final_position_index=int(path[-1]),
        max_transition_m=float(legs.max()) if len(legs) else 0.)


def solve(S,C,positions,penalty,speed):
    kwargs=dict(slot_duration_s=20,max_speed_m_per_s=speed,penalty_bits_per_use=penalty,reference_distance_m=1000)
    stationary=best_stationary(S)[0]
    paths=[np.full(S.shape[1],stationary,dtype=int),greedy_trajectory(S,positions,**kwargs)['path'],optimize_trajectory(S,positions,**kwargs)['path']]
    result=[path_metrics(S,C,positions,p,penalty,speed) for p in paths]
    require(all(result[2]['U']>=r['U']-1e-12-1e-12*abs(r['U']) for r in result[:2]),'DP objective dominance violation')
    return result,paths


def literal_dp(S,positions,penalty,speed):
    distance=np.linalg.norm(positions[:,None]-positions[None,:],axis=-1)
    F=S[:,0].copy();nt=S.shape[1]
    for n in range(1,nt):F=S[:,n]+np.max(np.where(distance<=20*speed,F[:,None]-nt*penalty*distance/1000,-np.inf),axis=0)
    return float(F.max()/nt)


def inputs(c,out,bind=False):
    base=ROOT/c['reference_directory'];archive=ROOT/c['archive_directory'];bindings={};verified=0
    for receipt,folder,field in ((base/'validation/final_verification.json',base,'artifacts_sha256'),
            (base/'analysis/analysis_receipt.json',base/'analysis','artifact_sha256'),
            (base/'analysis/comparison_figures/validation_receipt.json',base/'analysis/comparison_figures','artifact_sha256')):
        record=read_json(receipt);require(record['status']=='CURRENTLY_VERIFIED_PASS','Prior receipt not PASS')
        bindings[receipt.relative_to(ROOT).as_posix()]=sha(receipt)
        for name,digest in record[field].items():
            require(sha(folder/name)==digest,'Prior artifact hash mismatch: '+name)
            bindings[(folder/name).relative_to(ROOT).as_posix()]=digest;verified+=1
    protocol=read_json(base/'protocol.json');old=read_json(archive/'inputs.json');receipt=read_json(archive/'experiment_receipt.json')
    require(read_json(archive/'final_validation.json')['status']=='CURRENTLY_VERIFIED_PASS','Cloud archive not independently verified')
    for name in ('cloud_states.npz','cloud_scenarios.json'):
        require(sha(archive/name)==receipt['output_sha256'][name],'Cloud archive hash mismatch')
        bindings[(archive/name).relative_to(ROOT).as_posix()]=sha(archive/name)
    require(sha(ROOT/'src/binary_cloud.py')==receipt['producers']['src/binary_cloud.py'],'Archived generator identity mismatch')
    for name in ('inputs.json','experiment_receipt.json','final_validation.json','positions.csv'):
        bindings[(archive/name).relative_to(ROOT).as_posix()]=sha(archive/name)
    # Rendering and independent verification have separate producer receipts.
    for name in (*CODE[:2],'src/uav_mobility.py','src/manuscript_mobility.py','src/binary_cloud.py'):
        bindings[name]=sha(ROOT/name)
    positions_rows=read_csv(base/'positions.csv');positions=np.array([[float(r['x_m']),float(r['y_m'])] for r in positions_rows])
    oldpositions=np.array([[float(r['x_m']),float(r['y_m'])] for r in read_csv(archive/'positions.csv')])
    require(np.array_equal(positions,oldpositions),'Cloud coordinate identity differs')
    require(protocol['mission']=={'slots':30,'slot_duration_s':20,'max_speed_m_per_s':15},'Unexpected base mission')
    require(protocol['cloud']==read_json(ROOT/'configs/manuscript_mobility.json')['cloud'],'Base cloud protocol differs')
    require(old['settings']['cloud']['seed']==20261015 and old['settings']['cloud']['realizations']==100,'Archive mission identities differ')
    roster=read_csv(base/'source_roster.csv');require(len(roster)==233,'233-source roster missing')
    require(sum(r['family']=='MB' for r in roster)==197 and sum(r['family']=='Uniform' for r in roster)==36,'Source families differ')
    roster_by_hash={r['ensemble_hash']:r for r in roster};require(len(roster_by_hash)==233,'Duplicate ensemble identities')
    for r in roster:
        p=ROOT/r['source_path'];require(sha(p)==r['source_sha256'],'Exact-source payload changed')
        bindings[p.relative_to(ROOT).as_posix()]=r['source_sha256']
    winners=read_csv(base/'p1/winners.csv');require([int(r['position_index']) for r in winners]==list(range(100)),'P1 position coverage differs')
    for r in winners:
        parent=roster_by_hash[r['ensemble_hash']]
        require(all(float(r[k])==float(parent[k]) for k in ('VA','nu_raw','C','w')),'P1 source payload semantics differ')
        require(float(r['K_star'])==max(0,float(r['K_raw'])),'P1 clipping identity differs')
    K=np.array([float(r['K_star']) for r in winners]);require(np.isfinite(K).all() and np.all(K>0),'Invalid or unexpected P1 rates')
    with np.load(archive/'cloud_states.npz',allow_pickle=False) as z:C=z['blocked']
    require(C.shape==(16,100,100,30) and C.dtype==np.bool_,'Archive mask shape/type differs')
    with np.load(base/'clouds/states.npz',allow_pickle=False) as z:
        require(np.array_equal(C[0],z['blocked']) and np.array_equal((~C[0])*K[None,:,None],z['usable_skr']),'Base source/mask rates differ')
    schedule=read_json(base/'mobility/lambda_schedule.json');require(schedule['representative']==LAMBDAS[1],'Exact representative lambda differs')
    scenarios=read_json(archive/'cloud_scenarios.json');cases,members,order=make_cases(c,positions,scenarios)
    provenance=dict(bindings=bindings,prior_hash_members=verified,archive_masks=16,used_scenario_ids=sorted({x['scenario_id'] for x in cases}),
        mask_shape=list(C.shape),source_count=233,new_clouds=0,new_physical_SKR=0,new_source_moments=0,
        transfer_rule='Boolean masks only; historical optical SKR, thresholds and trajectories are not transferred')
    if bind:save_json(out/'input_manifest.json',provenance)
    else:require(provenance==read_json(out/'input_manifest.json'),'Input/producer identity changed; resume refused')
    return base,positions,C,K,cases,members,order,protocol


def audit(c,out):
    require(not (out/'validation/audit.json').exists(),'Audit already complete; do not overwrite')
    begin=time.perf_counter();preserve(out)
    base,positions,C,K,cases,members,order,protocol=inputs(c,out,True)
    save_json(out/'protocol.json',dict(settings=c,parent_protocol=protocol,cases=cases,memberships=members,selection_order=order,
        authorized_scope='Stage A only; no cloud generation, physical SKR or C,w recalculation',
        subset_identity='spatial-only, quadrant-balanced maximin; four original corners; sorted solver coordinates',
        comparisons='pointwise paired whole-mission bootstrap; descriptive finite-range sensitivity',
        fixed_lambda_across_all_cases=True,baseline_reproduction_lambda_count=10))
    write_csv(out/'case_membership.csv',members)
    subset_rows=[];diagnostics=[]
    for J in c['candidate_counts']:
        ids=np.array(sorted(order[:J]));p=positions[ids];distance=transition_distances(p);graph=distance<=300
        components,_=connected_components(graph,directed=False)
        quadrants=(p[:,0]>=500).astype(int)+2*(p[:,1]>=500).astype(int)
        counts=np.bincount(quadrants,minlength=4);require(counts.max()-counts.min()<=1,'Unbalanced subset')
        coverage=np.linalg.norm(positions[:,None]-p[None,:],axis=-1).min(axis=1).max()
        diagnostics.append(dict(J=J,components=int(components),isolated_positions=int(np.sum(graph.sum(axis=1)==1)),
            feasible_directed_edges_including_stay=int(graph.sum()),coverage_radius_m=float(coverage),quadrant_counts=json.dumps(counts.tolist())))
        for j in ids:subset_rows.append(dict(J=J,selection_rank=order.index(int(j))+1,position_index=int(j),j=int(j)+1,x_m=float(positions[j,0]),y_m=float(positions[j,1]),quadrant=int((positions[j,0]>=500)+2*(positions[j,1]>=500))))
    write_csv(out/'subsets.csv',subset_rows);write_csv(out/'subset_diagnostics.csv',diagnostics)
    with np.load(base/'mobility/paths.npz',allow_pickle=False) as z:oldpaths=z['paths'];penalties=z['lambda_values']
    oldmetrics={(int(r['realization_id']),int(r['lambda_index']),r['strategy']):r for r in read_csv(base/'mobility/mission_metrics.csv')}
    fields=dict(K='average_skr_bits_per_use',U='objective_bits_per_use',D='total_distance_m',availability='availability',
                repositionings='repositionings',blocked_slots='blocked_slots',positive_slots='positive_slots')
    checks=[];exact_paths=0
    for rid in range(100):
        S=(~C[0,rid])*K[:,None]
        for li,lam in enumerate(penalties):
            result,paths=solve(S,C[0,rid],positions,float(lam),15.)
            literal=literal_dp(S,positions,float(lam),15.)
            require(same(literal,result[2]['U']),'Baseline literal Bellman differs')
            for si,method in enumerate(METHODS):
                original=oldmetrics[rid,li,method]
                for key,field in fields.items():require(same(result[si][key],float(original[field])),'Baseline metric differs '+str((rid,li,method,key)))
                exact_paths+=int(np.array_equal(paths[si],oldpaths[rid,li,si]))
                checks.append(dict(realization_id=rid,lambda_index=li,lambda_bits_per_use=float(lam),method=method,
                    **result[si],literal_DP_objective=literal,max_abs_metric_residual=max(abs(result[si][k]-float(original[f])) for k,f in fields.items())))
        if rid%20==0:print('BASELINE_REPLAY',rid+1,'/100',flush=True)
    write_csv(out/'validation/baseline_reproduction.csv',checks)
    for sid in (1,7):
        require(np.all(C[sid]==(sid==7)),'Archived deterministic cloud control invalid')
        for lam in LAMBDAS:
            result,_=solve((~C[sid,0])*K[:,None],C[sid,0],positions,lam,15)
            require(all(r['D']==0 and same(r['K'],0 if sid==7 else K.max()) for r in result),'Clear/blocked mobility control failed')
    audit_files=['protocol.json','input_manifest.json','case_membership.csv','subsets.csv','subset_diagnostics.csv','validation/baseline_reproduction.csv']
    save_json(out/'validation/audit.json',dict(status='CURRENTLY_VERIFIED_PASS',baseline_records=3000,baseline_DP_calls=1000,
        baseline_Greedy_calls=1000,literal_Bellman_checks=1000,identical_baseline_paths=exact_paths,deterministic_control_solver_pairs=4,
        max_abs_metric_residual=max(r['max_abs_metric_residual'] for r in checks),elapsed_seconds=time.perf_counter()-begin,
        old_file_integrity=preserve(out),new_clouds=0,new_physical_SKR=0,new_source_moments=0,
        artifact_sha256={name:sha(out/name) for name in audit_files}))
    print('AUDIT_PASS',len(checks),'baseline records; exact paths',exact_paths,flush=True)


def compute(c,out):
    require(read_json(out/'validation/audit.json')['status']=='CURRENTLY_VERIFIED_PASS','Audit gate failed')
    require(not (out/'validation/compute.json').exists(),'Completed compute stage is immutable')
    begin=time.perf_counter();base,p,C,K,cases,members,order,protocol=inputs(c,out)
    with np.load(base/'mobility/paths.npz',allow_pickle=False) as z:
        oldpaths=z['paths'];oldlambda=z['lambda_values'];base_paths=oldpaths[:,[int(np.flatnonzero(oldlambda==x)[0]) for x in LAMBDAS]]
    rows=[];saved={};calls=0
    for case in cases:
        checkpoint=out/'existing_data'/('checkpoint_'+case['case_id']+'.npz')
        case_hash=hashlib.sha256(json.dumps(case,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ids=np.array(case['indices']);coords=p[ids];nt=case['Nt'];sid=case['scenario_id'];paths=np.empty((100,2,3,nt),dtype=np.int16)
        if checkpoint.exists():
            with np.load(checkpoint,allow_pickle=False) as z:
                require(str(z['input_sha256'])==sha(out/'input_manifest.json') and str(z['case_sha256'])==case_hash,'Checkpoint identity differs')
                paths=z['paths']
            require(paths.shape==(100,2,3,nt),'Checkpoint shape differs')
        else:
            for rid in range(100):
                blocked=C[sid,rid,ids,:nt];S=(~blocked)*K[ids,None]
                for li,lam in enumerate(LAMBDAS):
                    if case['case_id']=='base':paths[rid,li]=base_paths[rid,li]
                    else:
                        _,local=solve(S,blocked,coords,lam,case['speed']);calls+=1
                        paths[rid,li]=np.array([ids[path] for path in local])
            np.savez_compressed(checkpoint,paths=paths,input_sha256=np.array(sha(out/'input_manifest.json')),case_sha256=np.array(case_hash))
        inverse={int(j):i for i,j in enumerate(ids)}
        for rid in range(100):
            blocked=C[sid,rid,ids,:nt];S=(~blocked)*K[ids,None]
            for li,lam in enumerate(LAMBDAS):
                results=[]
                for si,method in enumerate(METHODS):
                    local=np.array([inverse[int(j)] for j in paths[rid,li,si]])
                    result=path_metrics(S,blocked,coords,local,lam,case['speed']);results.append(result)
                    result['initial_position_index']=int(paths[rid,li,si,0]);result['final_position_index']=int(paths[rid,li,si,-1])
                    rows.append(dict(case_id=case['case_id'],realization_id=rid,lambda_index=li,lambda_bits_per_use=lam,method=method,
                        J=case['J'],Nt=nt,max_speed_m_per_s=case['speed'],scenario_id=sid,probability=case['probability'],
                        correlation_length_m=case['spatial'],temporal_rho=case['rho'],**result,
                        origin='authenticated_original_baseline' if case['case_id']=='base' else 'Stage_A_mobility_recomputation'))
                require(all(results[2]['U']>=x['U']-1e-12-1e-12*abs(x['U']) for x in results[:2]),'Stored path dominance failed')
        saved['paths_'+case['case_id']]=paths
        print('CASE_COMPLETE',case['case_id'],'J',case['J'],'Nt',nt,'speed',case['speed'],'scenario',sid,flush=True)
    np.savez_compressed(out/'existing_data/paths.npz',lambda_values=np.array(LAMBDAS),realization_ids=np.arange(100),**saved)
    write_csv(out/'existing_data/mission_metrics.csv',rows)
    write_csv(out/'existing_data/lambda_reference.csv',read_csv(base/'analysis/tables/method_comparison.csv'))
    compute_files=list((out/'existing_data').glob('checkpoint_*.npz'))+[out/'existing_data/paths.npz',out/'existing_data/mission_metrics.csv',out/'existing_data/lambda_reference.csv']
    save_json(out/'validation/compute.json',dict(status='CURRENTLY_VERIFIED_PASS',unique_cases=26,records=len(rows),
        new_solver_pairs_this_invocation=calls,completed_new_solver_pairs=5000,baseline_solver_pairs=1000,
        existing_lambda_values_reused=10,elapsed_seconds=time.perf_counter()-begin,
        new_clouds=0,new_physical_SKR=0,new_source_moments=0,stage_b_executed=False,old_file_integrity=preserve(out),
        artifact_sha256={p.relative_to(out).as_posix():sha(p) for p in compute_files}))


def bootstrap_summary(values,boot):
    q=np.quantile(boot,[.025,.975],axis=0)
    return dict(mean=float(np.mean(values)),sd=float(np.std(values,ddof=1)),median=float(np.median(values)),
        ci95_low=float(q[0]),ci95_high=float(q[1]))


def aggregate(c,out):
    require(read_json(out/'validation/compute.json')['status']=='CURRENTLY_VERIFIED_PASS','Compute gate failed')
    require(not (out/'validation/aggregate.json').exists(),'Completed aggregate stage is immutable')
    begin=time.perf_counter();inputs(c,out);proto=read_json(out/'protocol.json');cases=proto['cases']
    rows=read_csv(out/'existing_data/mission_metrics.csv')
    lookup={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in rows}
    require(len(lookup)==len(rows)==15600,'Metric record coverage differs')
    rng=np.random.Generator(np.random.PCG64(c['bootstrap']['seed']))
    draws=rng.integers(0,100,size=(c['bootstrap']['resamples'],100))
    counts=np.zeros((len(draws),100),dtype=np.int16)
    np.add.at(counts,(np.arange(len(draws))[:,None],draws),1)
    np.savez_compressed(out/'existing_data/bootstrap_counts.npz',counts=counts)
    weights=counts.astype(float)/100;summary=[];paired=[]
    for case in cases:
        cid=case['case_id']
        for li,lam in enumerate(LAMBDAS):
            values=np.array([[[float(lookup[cid,rid,li,m][key]) for key in METRICS] for m in METHODS] for rid in range(100)])
            boots=(weights@values.reshape(100,-1)).reshape(len(weights),3,len(METRICS))
            for si,method in enumerate(METHODS):
                row=dict(case_id=cid,lambda_index=li,lambda_bits_per_use=lam,method=method,missions=100)
                for ki,key in enumerate(METRICS):row.update({key+'_'+name:v for name,v in bootstrap_summary(values[:,si,ki],boots[:,si,ki]).items()})
                summary.append(row)
            for bi,base in enumerate(METHODS[:2]):
                for key in ('K','U','D','availability'):
                    ki=METRICS.index(key);delta=values[:,2,ki]-values[:,bi,ki];delta_boot=boots[:,2,ki]-boots[:,bi,ki]
                    den=float(values[:,bi,ki].mean());valid=key in ('K','U') and den>1e-12
                    ratio=100*float(delta.mean())/den if valid else None
                    ratio_ci=np.quantile(100*delta_boot/boots[:,bi,ki],[.025,.975]) if valid and np.all(boots[:,bi,ki]>1e-12) else [None,None]
                    tol=1e-9 if key=='D' else 1e-12
                    paired.append(dict(case_id=cid,lambda_index=li,lambda_bits_per_use=lam,baseline=base,metric=key,missions=100,
                        **bootstrap_summary(delta,delta_boot),strict_positive=int(np.sum(delta>tol)),ties=int(np.sum(abs(delta)<=tol)),
                        negative=int(np.sum(delta<-tol)),ratio_of_means_percent=ratio,ratio_ci95_low=ratio_ci[0],ratio_ci95_high=ratio_ci[1],
                        ratio_status='VALID_POSITIVE_BASELINE' if valid else 'UNDEFINED_OR_NOT_APPLICABLE',
                        baseline_mean=den,bootstrap_resamples=len(weights),bootstrap_seed=c['bootstrap']['seed']))
    write_csv(out/'existing_data/aggregate_statistics.csv',summary);write_csv(out/'existing_data/paired_improvements.csv',paired)
    summaries={(r['case_id'],r['lambda_index'],r['method']):r for r in summary}
    pairs={(r['case_id'],r['lambda_index'],r['baseline'],r['metric']):r for r in paired}
    effects=[];increments=[]
    for axis in AXES:
        members=sorted([m for m in proto['memberships'] if m['axis']==axis],key=lambda m:m['value'])
        for method in METHODS:
            for key in ('K','U','D','availability'):
                y=np.array([summaries[m['case_id'],1,method][key+'_mean'] for m in members]);default=summaries['base',1,method][key+'_mean']
                effects.append(dict(axis=axis,method=method,metric=key,minimum=float(y.min()),maximum=float(y.max()),span=float(np.ptp(y)),
                    argmin=members[int(y.argmin())]['value'],argmax=members[int(y.argmax())]['value'],
                    endpoint_change=float(y[-1]-y[0]),baseline_mean=default,span_percent_of_default=100*float(np.ptp(y))/default if default>1e-12 else None))
        for baseline in METHODS[:2]:
            for key in ('K','U'):
                y=np.array([pairs[m['case_id'],1,baseline,key]['mean'] for m in members]);default=pairs['base',1,baseline,key]['mean']
                effects.append(dict(axis=axis,method='DP-minus-'+baseline,metric=key,minimum=float(y.min()),maximum=float(y.max()),span=float(np.ptp(y)),
                    argmin=members[int(y.argmin())]['value'],argmax=members[int(y.argmax())]['value'],endpoint_change=float(y[-1]-y[0]),
                    baseline_mean=default,span_percent_of_default=100*float(np.ptp(y))/default if default>1e-12 else None))
        if axis=='J':
            for before,after in zip(members,members[1:]):
                for method in METHODS:
                    x=np.array([float(lookup[after['case_id'],rid,1,method]['U'])-float(lookup[before['case_id'],rid,1,method]['U']) for rid in range(100)])
                    bs=weights@x
                    increments.append(dict(J_before=before['value'],J_after=after['value'],method=method,**bootstrap_summary(x,bs),gain_per_added_position=float(x.mean()/(after['value']-before['value']))))
    write_csv(out/'existing_data/parameter_effects.csv',effects);write_csv(out/'existing_data/J_incremental_gains.csv',increments)
    aggregate_files=['aggregate_statistics.csv','paired_improvements.csv','parameter_effects.csv','J_incremental_gains.csv','bootstrap_counts.npz']
    save_json(out/'validation/aggregate.json',dict(status='CURRENTLY_VERIFIED_PASS',summary_rows=len(summary),paired_rows=len(paired),
        resamples=20000,seed=20261020,bootstrap_counts_sha256=sha(out/'existing_data/bootstrap_counts.npz'),
        interval='pointwise paired whole-mission percentile; not simultaneous or security confidence',
        scope='Ranges over approved parameter domains, not normalized universal causal sensitivities',elapsed_seconds=time.perf_counter()-begin,
        artifact_sha256={'existing_data/'+name:sha(out/'existing_data'/name) for name in aggregate_files}))
    print('AGGREGATE_PASS',len(summary),'method summaries;',len(paired),'paired comparisons',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,choices=('audit','compute','aggregate','verify'))
    parser.add_argument('--config',type=Path,default=ROOT/'configs/mobility_parameter_sensitivity.json')
    args=parser.parse_args();c=read_json(args.config);validate_config(c);out=ROOT/c['output_directory']
    require(out.is_dir() and (out/'startup_manifest.json').exists(),'Startup protection manifest is required')
    if (out/'validation/final_receipt.json').exists() and args.stage!='verify':raise FileExistsError('Completed Stage A package is immutable')
    if args.stage=='verify':runpy.run_path(str(out/'validation/verify_stage_a.py'))['verify'](c,out)
    else:{'audit':audit,'compute':compute,'aggregate':aggregate}[args.stage](c,out)


if __name__=='__main__':main()
