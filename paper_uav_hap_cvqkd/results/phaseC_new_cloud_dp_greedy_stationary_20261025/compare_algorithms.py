"""Paired synthetic missions with a common saved clear-sky map; no QKD imports."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.uav_mobility import candidate_grid,transition_distances,best_stationary,optimize_trajectory
from src.binary_cloud import generate_cloud as old_cloud,mean_statistics
import new_cloud_model as cloud

ALGORITHMS=['Stationary','Greedy','DP']
METRICS=['average_usable_skr','objective_U','total_distance_m','zero_rate_unavailability',
    'availability','blocked_fraction','position_changes','runtime_s']


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,value):(OUT/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,records):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)));w.writeheader();w.writerows(records)
def digest(array):return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def greedy(S,distances,feasible,penalty,reference):
    slots=S.shape[1];path=np.empty(slots,dtype=int)
    path[0]=int(np.argmax(S[:,0]))
    for n in range(1,slots):
        previous=path[n-1]
        scores=S[:,n]/slots-penalty*distances[previous]/reference
        path[n]=int(np.argmax(np.where(feasible[previous],scores,-np.inf)))
    return path


def compare(S,C,positions,penalty,mission):
    if S.shape!=C.shape or not np.isfinite(S).all() or np.any(S<0) or np.any(S[C]!=0):raise ValueError('Invalid shared S/C')
    original=digest(S),digest(C)
    distance=transition_distances(positions);dt=mission['slot_duration_s'];speed=mission['max_speed_m_per_s']
    feasible=distance<=speed*dt;reference=mission['reference_distance_m']
    slots=S.shape[1];paths={};elapsed={}
    start=time.perf_counter();j,_=best_stationary(S);paths['Stationary']=np.full(slots,j,dtype=int);elapsed['Stationary']=time.perf_counter()-start
    start=time.perf_counter();paths['Greedy']=greedy(S,distance,feasible,penalty,reference);elapsed['Greedy']=time.perf_counter()-start
    start=time.perf_counter();result=optimize_trajectory(S,positions,slot_duration_s=dt,max_speed_m_per_s=speed,
        penalty_bits_per_use=penalty,reference_distance_m=reference)
    paths['DP']=result['path'];elapsed['DP']=time.perf_counter()-start
    records=[]
    for algorithm,path in paths.items():
        legs=distance[path[:-1],path[1:]];rate=S[path,np.arange(slots)];blocked=C[path,np.arange(slots)]
        if not feasible[path[:-1],path[1:]].all():raise ValueError('Infeasible '+algorithm+' path')
        flight=float(legs.sum());mean=float(rate.mean());objective=mean-penalty*flight/reference
        records.append(dict(algorithm=algorithm,average_usable_skr=mean,objective_U=objective,total_distance_m=flight,
            zero_rate_unavailability=float(np.mean(rate<=0)),availability=float(np.mean(rate>0)),
            blocked_fraction=float(blocked.mean()),blocked_or_zero_fraction=float(np.mean(blocked|(rate<=0))),
            position_changes=int(np.count_nonzero(np.diff(path))),runtime_s=elapsed[algorithm],
            maximum_leg_m=float(legs.max()),C_sha256=original[1],S_sha256=original[0]))
    assert records[0]['total_distance_m']==0
    assert all(records[2]['objective_U']>=r['objective_U']-1e-12 for r in records[:2])
    assert original==(digest(S),digest(C))
    return records,paths


def summarize(data):
    groups={}
    for r in data:groups.setdefault((r['geometry'],r['case_id'],r['algorithm']),[]).append(r)
    output=[]
    for (geometry,case,algorithm),records in groups.items():
        assert len(records)==100
        for metric in METRICS:
            stats=mean_statistics(np.array([r[metric] for r in records]))
            output.append(dict(result_scope='DIAGNOSTIC_ONLY',geometry=geometry,case_id=case,algorithm=algorithm,
                p_target=records[0]['p_target'],threshold_mode=records[0]['threshold_mode'],
                lambda_bits_per_use=records[0]['lambda_bits_per_use'],metric=metric,**stats))
    return output


def paired(data):
    lookup={(r['geometry'],r['case_id'],r['mission_id'],r['algorithm']):r for r in data}
    output=[]
    for (geometry,case,mission_id,algorithm),dp in lookup.items():
        if algorithm!='DP':continue
        for baseline in ['Greedy','Stationary']:
            b=lookup[(geometry,case,mission_id,baseline)]
            for metric in ['objective_U','average_usable_skr','zero_rate_unavailability','total_distance_m']:
                delta=dp[metric]-b[metric]
                improvement=-delta if metric in ['zero_rate_unavailability','total_distance_m'] else delta
                output.append(dict(result_scope='DIAGNOSTIC_ONLY',geometry=geometry,case_id=case,mission_id=mission_id,
                    baseline=baseline,metric=metric,DP_value=dp[metric],baseline_value=b[metric],
                    DP_minus_baseline=delta,improvement_absolute=improvement,
                    improvement_percent=100*improvement/abs(b[metric]) if b[metric]!=0 else '',
                    percent_status='DEFINED' if b[metric]!=0 else 'ZERO_BASELINE_USE_ABSOLUTE'))
    return output


def execute():
    config=read('experiment_config.json');mc=config['Monte_Carlo'];mission=dict(config['mission'],reference_distance_m=config['reference_distance_m'])
    previous=read('execution_summary.json') if (OUT/'execution_summary.json').exists() else None
    pending=[g for g in config['geometry_cases'] if previous is None or g not in previous['geometry_cases']]
    if not pending:raise FileExistsError('All approved geometry cases are already complete')
    positions=candidate_grid(1000.,10);count=mc['missions'];slots=mission['slots'];seed=mc['seed']
    assert count==100 and slots==30
    begin=time.perf_counter();probability=mc['probabilities']
    if previous is None:
        gaussian=[];means=[];residual=[];old_latent=[];old_masks=[]
        for mission_id in range(count):
            values=cloud.generate(slots,seed,mission_id);gaussian.append(values['G']);means.append(values['mu']);residual.append(values['epsilon'])
            c,z=old_cloud(positions,slots,.4,250.,.9,seed,mission_id,return_latent=True);old_masks.append(c);old_latent.append(z)
        gaussian,means,residual,old_latent,old_masks=map(np.asarray,[gaussian,means,residual,old_latent,old_masks])
        masks=np.array([[cloud.threshold(g,mode='calibrated',probability=p)[0] for g in gaussian] for p in probability])
        zero=gaussian>0
        archive=dict(G_new=gaussian,mu_new=means,epsilon_new=residual,C_zero=zero,
            probabilities=np.array(probability),thresholds=np.array([cloud.calibrated_threshold(p) for p in probability]),
            C_calibrated=masks,C_old_p04=old_masks,G_old=old_latent,positions=positions,
            mission_ids=np.arange(count),seed=np.array(seed),Gamma=cloud.covariance()[0])
    else:
        with np.load(OUT/'cloud_realizations.npz') as stored:archive={k:stored[k] for k in stored.files}
        assert int(archive['seed'])==seed and archive['C_zero'].shape==(count,100,slots)
        gaussian,means,residual,old_latent,old_masks=[archive[k] for k in ['G_new','mu_new','epsilon_new','G_old','C_old_p04']]
        masks,zero=archive['C_calibrated'],archive['C_zero']
        assert archive['probabilities'].tolist()==probability
    assert np.array_equal(zero,masks[probability.index(.5)])
    cases=[dict(case_id='new_zero',model='NEW',threshold_mode='zero',p_target=.5,threshold=0.,C=zero,penalty=config['lambda_ref_bits_per_use'])]
    for i,p in enumerate(probability):cases.append(dict(case_id=f'new_calibrated_p{p:.1f}',model='NEW',threshold_mode='calibrated',p_target=p,
        threshold=cloud.calibrated_threshold(p),C=masks[i],penalty=config['lambda_ref_bits_per_use']))
    cases.append(dict(case_id='old_p0.4',model='OLD',threshold_mode='old_standard_normal_lower_tail',p_target=.4,
        threshold=float(__import__('scipy.special',fromlist=['ndtri']).ndtri(.4)),C=old_masks,penalty=config['lambda_ref_bits_per_use']))
    for i,penalty in enumerate(config['lambda_values_bits_per_use']):
        if penalty==config['lambda_ref_bits_per_use']:continue
        cases.append(dict(case_id=f'new_p0.4_lambda{i}',model='NEW',threshold_mode='calibrated',p_target=.4,
            threshold=cloud.calibrated_threshold(.4),C=masks[probability.index(.4)],penalty=penalty))
    all_records=[];trajectory=[];cache={};reused=0;executions=0;blockage=[]
    if previous is not None:
        all_records=rows('simulation_results.csv');trajectory=rows('algorithm_trajectories.csv')
        for r in all_records:
            for k in METRICS+['p_target','lambda_bits_per_use','threshold','empirical_mission_blockage','maximum_leg_m','blocked_or_zero_fraction']:r[k]=float(r[k])
            r['mission_id']=int(r['mission_id']);r['seed']=int(r['seed'])
        executions=previous['unique_algorithm_triplet_executions'];reused=previous['reused_triplet_views']
    for case in cases:
        stats=mean_statistics(case['C'].mean(axis=(1,2)))
        blockage.append({k:case[k] for k in ['case_id','model','threshold_mode','p_target','threshold']}|stats)
    for geometry in pending:
        sky=rows(f'clear_sky_map_{geometry}.csv');K=np.array([float(r['K_star']) for r in sky]);assert len(K)==100
        archive[f'K_star_{geometry}']=K
        archive[f'S_zero_{geometry}']=(~zero)*K[None,:,None]
        archive[f'S_calibrated_{geometry}']=(~masks)*K[None,None,:,None]
        archive[f'S_old_p04_{geometry}']=(~old_masks)*K[None,:,None]
        for case in cases:
            for mission_id,C in enumerate(case['C']):
                S=(~C)*K[:,None];C.setflags(write=False);S.setflags(write=False)
                key=geometry,digest(C),float(case['penalty']).hex()
                if key in cache:records,paths=cache[key];reused+=1
                else:
                    records,paths=compare(S,C,positions,case['penalty'],mission);cache[key]=(records,paths);executions+=1
                common=dict(result_scope='DIAGNOSTIC_ONLY',geometry=geometry,case_id=case['case_id'],model=case['model'],
                    threshold_mode=case['threshold_mode'],threshold=case['threshold'],p_target=case['p_target'],
                    lambda_bits_per_use=case['penalty'],mission_id=mission_id,seed=seed,
                    empirical_mission_blockage=float(C.mean()),algorithm_results_reused=key in cache and records[0].get('_seen',False))
                for r in records:all_records.append({**common,**{k:v for k,v in r.items() if k!='_seen'}})
                for algorithm,path in paths.items():
                    for n,j in enumerate(path):
                        trajectory.append(dict(result_scope='DIAGNOSTIC_ONLY',geometry=geometry,case_id=case['case_id'],mission_id=mission_id,
                            algorithm=algorithm,slot=n+1,position_index=int(j),j=int(j)+1,x_m=float(positions[j,0]),y_m=float(positions[j,1]),
                            blocked=bool(C[j,n]),usable_skr=float(S[j,n]),lambda_bits_per_use=case['penalty']))
                for r in records:r['_seen']=True
            print(json.dumps(dict(geometry=geometry,case=case['case_id'],missions=count,lambda_value=case['penalty'])),flush=True)
    np.savez_compressed(OUT/'cloud_realizations.npz',**archive)
    write('simulation_results.csv',all_records);write('algorithm_trajectories.csv',trajectory)
    write('summary_comparison.csv',summarize(all_records));write('paired_mission_results.csv',paired(all_records))
    write('empirical_blockage.csv',blockage)
    summary=dict(result_scope='DIAGNOSTIC_ONLY',independent_mission_ids_per_case=count,time_slots=slots,candidate_positions=100,
        cases_per_geometry=len(cases),geometry_cases=list(config['geometry_cases']),mission_case_views=len(all_records)//3,
        unique_algorithm_triplet_executions=executions,reused_triplet_views=reused,
        algorithm_execution_count=3*executions,simulation_result_rows=len(all_records),trajectory_rows=len(trajectory),
        cloud_new_G_missions=100,cloud_old_G_missions=100,white_innovations_paired_across_models=True,
        source_moment_computations=0,seed=seed,elapsed_seconds=time.perf_counter()-begin+(previous['elapsed_seconds'] if previous else 0),
        prior_geometry_runs_preserved=previous['geometry_cases'] if previous else [],
        cloud_archive_reused_without_resampling=previous is not None,
        DP_objective_failures=0,movement_failures=0,primary_geometry=config['primary_geometry'])
    save('execution_summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':execute()
