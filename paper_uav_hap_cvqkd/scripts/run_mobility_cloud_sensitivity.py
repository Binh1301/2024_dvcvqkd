"""Stage B: missing cloud probabilities and temporal sensitivity; reuse exact P1."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import runpy
import subprocess
import sys
import time

import numpy as np
from scipy.special import ndtri

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_mobility_parameter_sensitivity import (
    METHODS, METRICS, bootstrap_summary, path_metrics, read_csv, read_json,
    require, same, save_json, sha, solve, write_csv,
)
from src.binary_cloud import generate_cloud, bernoulli_correlation, mean_statistics

CODE = ('configs/mobility_parameter_sensitivity_stage_b.json', 'scripts/run_mobility_cloud_sensitivity.py',
        'scripts/plot_mobility_cloud_sensitivity.py', 'tests/test_mobility_cloud_sensitivity.py')


def validate(c):
    locked = dict(stage='B', probabilities=[.1,.2,.3,.4,.5,.6,.7,.8], spatial_lengths_m=[50,100,250,500,1000],
                  temporal_rhos=[0,.3,.6,.9,.98], defaults=dict(probability=.4,spatial_length_m=250,temporal_rho=.9),
                  missions=100, positions=100, slots=30, slot_duration_s=20, max_speed_m_per_s=15,
                  reference_distance_m=1000, lambda_values=[0,9.468026677248516e-6], cloud_seed=20261015,
                  new_cloud_parameters=[[.3,250,.9],[.5,250,.9],[.7,250,.9]],
                  new_cloud_generation_allowed=True, new_physical_skr_allowed=False,
                  availability_rule='S > 0; no engineering threshold', absolute_tolerance=1e-12,relative_tolerance=1e-12,
                  security_status='UNVALIDATED_SECURITY_MODEL', lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
                  reference_directory='results/manuscript_mobility_p1_p2_p3_20261019',
                  stage_a_directory='results/mobility_parameter_sensitivity_20261020',
                  archive_directory='results/binary_cloud_skr_20261015',
                  output_directory='results/mobility_parameter_sensitivity_stage_b_20261020')
    require(all(c.get(k)==v for k,v in locked.items()), 'Stage B configuration differs from preregistered choices')
    require(c['bootstrap']==dict(resamples=20000,seed=20261020,reuse_stage_a_counts=True,unit='whole paired mission',interval='pointwise percentile 95%'), 'Bootstrap identity differs')
    require(c['correlation_diagnostic']==dict(missions=100,slots=30,tolerance='5 times mission-cluster standard error + 1e-10; fixed before outcomes'), 'Cloud diagnostic rule changed')


def cases_for(c, archive_scenarios):
    default=(.4,250,.9); lookup={tuple(s['parameters']):s['scenario_id'] for s in archive_scenarios}
    cases=[dict(case_id='base',parameters=list(default),archive_id=lookup[default],stage_a_case_id='base')];members=[]
    for axis, values, column in (('probability',c['probabilities'],0),('spatial',c['spatial_lengths_m'],1),('temporal',c['temporal_rhos'],2)):
        for value in values:
            parameters=list(default);parameters[column]=value
            if tuple(parameters)==default:case=cases[0]
            else:
                cid=axis+'_'+str(value).replace('.','p')
                sid=lookup.get(tuple(parameters))
                case=dict(case_id=cid,parameters=parameters,archive_id=sid,
                          stage_a_case_id=cid if axis in ('probability','spatial') and sid is not None else None)
                cases.append(case)
            members.append(dict(axis=axis,value=value,case_id=case['case_id']))
    require(len(cases)==16 and len({r['case_id'] for r in cases})==16,'Case coverage differs')
    require([r['parameters'] for r in cases if r['archive_id'] is None]==c['new_cloud_parameters'],'New cloud scope differs')
    return cases,members


def usable_rates(blocked, K):
    C=np.asarray(blocked);k=np.asarray(K)
    require(C.dtype==np.bool_ and C.ndim==2 and k.shape==(len(C),) and np.isfinite(k).all() and np.all(k>=0),'Invalid cloud/P1 input')
    return (~C)*k[:,None]


def preserve(out):
    s=read_json(out/'startup_manifest.json')
    changed=[n for n,h in s['protected_files'].items() if n not in s['allowed_changed'] and (not (ROOT/n).is_file() or sha(ROOT/n)!=h)]
    require(not changed,'Protected files changed: '+str(changed[:3]))
    for cmd,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        require(subprocess.check_output(cmd,cwd=ROOT,text=True).strip()==s[key],'Git identity changed')
    return len(s['protected_files'])


def authenticate(c,out,bind=False):
    A=ROOT/c['stage_a_directory'];base=ROOT/c['reference_directory'];archive=ROOT/c['archive_directory'];bindings={}
    for path,folder in ((A/'validation/final_receipt.json',A),
                        (A/'analysis/figure_report_review_20261020/validation_receipt.json',A/'analysis/figure_report_review_20261020')):
        receipt=read_json(path);require(receipt['status']=='CURRENTLY_VERIFIED_PASS','Previous receipt not PASS')
        bindings[path.relative_to(ROOT).as_posix()]=sha(path)
        for name,digest in receipt['artifact_sha256'].items():
            require(sha(folder/name)==digest,'Previous artifact changed: '+name);bindings[(folder/name).relative_to(ROOT).as_posix()]=digest
    for name,digest in read_json(A/'input_manifest.json')['bindings'].items():
        require(sha(ROOT/name)==digest,'Stage A input changed: '+name);bindings[name]=digest
    old=read_json(archive/'experiment_receipt.json')
    require(read_json(archive/'final_validation.json')['status']=='CURRENTLY_VERIFIED_PASS','Archive validation missing')
    for name in ('cloud_states.npz','cloud_scenarios.json'):
        require(sha(archive/name)==old['output_sha256'][name],'Archive changed: '+name)
        bindings[(archive/name).relative_to(ROOT).as_posix()]=sha(archive/name)
    require(sha(ROOT/'src/binary_cloud.py')==old['producers']['src/binary_cloud.py'],'Generator changed')
    for name in (*CODE[:2],CODE[3],'scripts/run_mobility_parameter_sensitivity.py','src/binary_cloud.py','src/uav_mobility.py','src/manuscript_mobility.py'):
        bindings[name]=sha(ROOT/name)
    positions=np.array([[float(r['x_m']),float(r['y_m'])] for r in read_csv(base/'positions.csv')])
    expected=np.array([(x,y) for y in range(50,1000,100) for x in range(50,1000,100)])
    require(np.array_equal(positions,expected),'Position identity differs')
    winners=read_csv(base/'p1/winners.csv');K=np.array([float(r['K_star']) for r in winners])
    require(len(K)==100 and np.isfinite(K).all() and np.all(K>0),'Current P1 missing')
    require(all(float(r['K_star'])==max(0,float(r['K_raw'])) for r in winners),'P1 clipping differs')
    cases,members=cases_for(c,read_json(archive/'cloud_scenarios.json'))
    record=dict(bindings=bindings,transfer_rule='Authenticated boolean masks and Stage A current-P1 trajectories only; historical optical SKR never transferred',
                new_cloud_configurations=3,new_cloud_missions=300,reused_archive_configurations=13,reused_Stage_A_cases=9,new_mobility_cases=7)
    if bind:save_json(out/'input_manifest.json',record)
    else:require(record==read_json(out/'input_manifest.json'),'Input/producer identity changed; resume refused')
    return A,base,archive,positions,K,cases,members


def audit(c,out):
    require(not (out/'validation/audit.json').exists(),'Audit complete; immutable')
    started=time.perf_counter();preserve(out)
    A,base,archive,xy,K,cases,members=authenticate(c,out,True)
    test=read_json(out/'validation/tests.json');require(test['status']=='CURRENTLY_VERIFIED_PASS','Tests not passed')
    require(test['producer_sha256']=={n:sha(ROOT/n) for n in (CODE[0],CODE[1],CODE[3])},'Tested producer changed')
    protocol=dict(settings=c,cases=cases,memberships=members,parent_protocol=read_json(base/'protocol.json'),
                  equations=dict(S='(1-C)*K_star',U='mean(S_path)-lambda*D/1000',Greedy='S_now-Nt*lambda*d/1000',
                                 latent='Z_t=rho*Z_(t-1)+sqrt(1-rho^2)*epsilon_t; Cov(epsilon)=exp(-d/ell)',
                                 cloud='C=(Z<Phi_inverse(p)); True=blocked'),
                  scope='User-approved Stage B; cloud-only additions and lightweight mobility; no quantum/source recalculation',
                  temporal_design='Existing archive grid0,.3,.6,.9,.98; treats persistence relative to mission600s without presupposing trend',
                  preregistration='Parameters,seed,IDs,penalties,figure roles and tolerances fixed before Stage B outcomes',
                  figures=['probability K/availability/paired-U-gap','spatial K/availability/paired-U-gap','temporal K/availability/paired-U-gap','travel distance at both penalties'])
    save_json(out/'protocol.json',protocol);write_csv(out/'case_membership.csv',members)
    with np.load(A/'existing_data/paths.npz',allow_pickle=False) as z:oldpaths=z['paths_base']
    with np.load(archive/'cloud_states.npz',allow_pickle=False) as z:cloud=z['blocked'][0]
    oldrows={(int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in read_csv(A/'existing_data/mission_metrics.csv') if r['case_id']=='base'}
    checks=[]
    for rid in range(100):
        for li,lam in enumerate(c['lambda_values']):
            metrics,paths=solve(usable_rates(cloud[rid],K),cloud[rid],xy,lam,15)
            for si,method in enumerate(METHODS):
                old=oldrows[rid,li,method]
                residual=max(abs(metrics[si][key]-float(old[key])) for key in METRICS)
                require(same(residual,0) and np.array_equal(paths[si],oldpaths[rid,li,si]),'Baseline reproduction failed')
                checks.append(dict(realization_id=rid,lambda_index=li,method=method,max_abs_residual=residual,identical_path=True))
    write_csv(out/'validation/baseline_reproduction.csv',checks)
    save_json(out/'validation/audit.json',dict(status='CURRENTLY_VERIFIED_PASS',baseline_records=600,baseline_solver_pairs=200,
        max_abs_residual=max(r['max_abs_residual'] for r in checks),protected_files=preserve(out),elapsed_seconds=time.perf_counter()-started,
        artifact_sha256={n:sha(out/n) for n in ('protocol.json','input_manifest.json','case_membership.csv','validation/baseline_reproduction.csv')}))
    print('AUDIT_PASS',len(cases),'cases;600 baseline records and paths reproduced',flush=True)


def clouds(c,out):
    require(not (out/'validation/cloud.json').exists(),'Cloud stage complete; immutable')
    authenticate(c,out);started=time.perf_counter();proto=read_json(out/'protocol.json');cases=proto['cases']
    base=ROOT/c['reference_directory'];archive=ROOT/c['archive_directory']
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in read_csv(base/'positions.csv')])
    with np.load(archive/'cloud_states.npz',allow_pickle=False) as z:archived=z['blocked']
    C=np.empty((16,100,100,30),dtype=bool);Z=np.empty(C.shape);checks=[]
    for ci,case in enumerate(cases):
        p,ell,rho=case['parameters'];latent_near=math.exp(-100/ell);latent_far=math.exp(-math.hypot(900,900)/ell)
        targets=dict(blockage_probability=p,latent_spatial_near=latent_near,latent_spatial_far=latent_far,latent_temporal=rho,
                     binary_spatial_near=bernoulli_correlation(p,latent_near),binary_spatial_far=bernoulli_correlation(p,latent_far),binary_temporal=bernoulli_correlation(p,rho))
        values={k:[] for k in targets}
        for rid in range(100):
            generated,z=generate_cloud(xy,30,p,ell,rho,c['cloud_seed'],rid,return_latent=True)
            if case['archive_id'] is not None:
                require(np.array_equal(generated,archived[case['archive_id'],rid]),'Archived mask replay differs')
                C[ci,rid]=archived[case['archive_id'],rid]
            else:C[ci,rid]=generated
            Z[ci,rid]=z
            require(np.array_equal(C[ci,rid],z<ndtri(p)),'Threshold identity failed')
            values['blockage_probability'].append(float(generated.mean()))
            binary=(generated.astype(float)-p)/math.sqrt(p*(1-p))
            for prefix,data in (('latent',z),('binary',binary)):
                values[prefix+'_spatial_near'].append(float(np.mean(data[0]*data[1])))
                values[prefix+'_spatial_far'].append(float(np.mean(data[0]*data[99])))
                values[prefix+'_temporal'].append(float(np.mean(data[:,:-1]*data[:,1:])))
        for metric,target in targets.items():
            stats=mean_statistics(values[metric]);tol=5*stats['se']+1e-10;passed=abs(stats['mean']-target)<=tol
            checks.append(dict(case_id=case['case_id'],metric=metric,target=target,**stats,tolerance=tol,passed=passed))
            require(passed,'Cloud cluster-SE diagnostic failed '+case['case_id']+'/'+metric)
        print('CLOUD_READY',case['case_id'],'new' if case['archive_id'] is None else 'exact archived replay',flush=True)
    members=sorted([m for m in proto['memberships'] if m['axis']=='probability'],key=lambda r:r['value'])
    index={r['case_id']:i for i,r in enumerate(cases)}
    require(all(np.all(C[index[a['case_id']]]<=C[index[b['case_id']]]) for a,b in zip(members,members[1:])),'Probability masks not nested')
    np.savez_compressed(out/'clouds/states.npz',blocked=C,latent=Z,realization_ids=np.arange(100),case_ids=np.array([r['case_id'] for r in cases]))
    write_csv(out/'clouds/correlation_diagnostics.csv',checks)
    save_json(out/'validation/cloud.json',dict(status='CURRENTLY_VERIFIED_PASS',new_cloud_missions=300,archived_mask_replays=1300,
        diagnostic_checks=len(checks),new_configurations=3,seed=c['cloud_seed'],elapsed_seconds=time.perf_counter()-started,
        artifact_sha256={n:sha(out/n) for n in ('clouds/states.npz','clouds/correlation_diagnostics.csv')}))


def compute(c,out):
    require(not (out/'validation/compute.json').exists(),'Compute complete; immutable')
    require(read_json(out/'validation/cloud.json')['status']=='CURRENTLY_VERIFIED_PASS','Cloud gate failed')
    started=time.perf_counter();A,base,archive,xy,K,cases,members=authenticate(c,out)
    with np.load(out/'clouds/states.npz',allow_pickle=False) as z:C=z['blocked']
    old={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in read_csv(A/'existing_data/mission_metrics.csv')}
    paths=np.empty((16,100,2,3,30),dtype=np.int16);records=[];calls=0
    identity=sha(out/'input_manifest.json')
    with np.load(A/'existing_data/paths.npz',allow_pickle=False) as saved:
        for ci,case in enumerate(cases):
            cid=case['case_id'];checkpoint=out/'mobility'/('checkpoint_'+cid+'.npz')
            if checkpoint.exists():
                with np.load(checkpoint,allow_pickle=False) as z:
                    require(str(z['identity'])==identity and str(z['case_id'])==cid,'Checkpoint identity mismatch')
                    paths[ci]=z['paths']
            elif case['stage_a_case_id'] is not None:paths[ci]=saved['paths_'+case['stage_a_case_id']]
            else:
                for rid in range(100):
                    for li,lam in enumerate(c['lambda_values']):
                        _,pp=solve(usable_rates(C[ci,rid],K),C[ci,rid],xy,lam,15);paths[ci,rid,li]=pp;calls+=1
            for rid in range(100):
                S=usable_rates(C[ci,rid],K)
                for li,lam in enumerate(c['lambda_values']):
                    result=[]
                    for si,method in enumerate(METHODS):
                        rr=path_metrics(S,C[ci,rid],xy,paths[ci,rid,li,si],lam,15);result.append(rr)
                        if case['stage_a_case_id'] is not None:
                            original=old[case['stage_a_case_id'],rid,li,method]
                            require(all(same(rr[key],float(original[key])) for key in METRICS),'Shared Stage A metrics differ')
                        records.append(dict(case_id=cid,realization_id=rid,lambda_index=li,lambda_bits_per_use=lam,method=method,
                                            probability=case['parameters'][0],correlation_length_m=case['parameters'][1],temporal_rho=case['parameters'][2],
                                            **rr,origin='authenticated_Stage_A' if case['stage_a_case_id'] is not None else 'Stage_B_mobility_recomputation'))
                    require(all(result[2]['U']>=r['U']-1e-12 for r in result[:2]),'DP dominance failed')
            if not checkpoint.exists():np.savez_compressed(checkpoint,paths=paths[ci],identity=np.array(identity),case_id=np.array(cid))
            print('MOBILITY_READY',cid,'reused' if case['stage_a_case_id'] is not None else 'Stage B',flush=True)
    write_csv(out/'mobility/mission_metrics.csv',records)
    np.savez_compressed(out/'mobility/paths.npz',paths=paths,case_ids=np.array([r['case_id'] for r in cases]),lambda_values=np.array(c['lambda_values']),realization_ids=np.arange(100))
    files=list((out/'mobility').glob('*.npz'))+[out/'mobility/mission_metrics.csv']
    save_json(out/'validation/compute.json',dict(status='CURRENTLY_VERIFIED_PASS',records=len(records),reused_records=5400,new_records=4200,
        new_solver_pairs_this_invocation=calls,new_solver_pairs_total=1400,elapsed_seconds=time.perf_counter()-started,protected_files=preserve(out),
        new_physical_SKR=0,new_source_moments=0,artifact_sha256={p.relative_to(out).as_posix():sha(p) for p in files}))


def aggregate(c,out):
    require(not (out/'validation/aggregate.json').exists(),'Aggregate complete; immutable')
    require(read_json(out/'validation/compute.json')['status']=='CURRENTLY_VERIFIED_PASS','Compute gate failed')
    authenticate(c,out);started=time.perf_counter();proto=read_json(out/'protocol.json')
    with np.load(ROOT/c['stage_a_directory']/'existing_data/bootstrap_counts.npz',allow_pickle=False) as z:counts=z['counts']
    require(counts.shape==(20000,100) and np.all(counts.sum(axis=1)==100),'Bootstrap identity invalid')
    weights=counts.astype(float)/100
    lookup={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in read_csv(out/'mobility/mission_metrics.csv')}
    require(len(lookup)==9600,'Record coverage differs');summary=[];paired=[]
    for case in proto['cases']:
        cid=case['case_id']
        for li,lam in enumerate(c['lambda_values']):
            values=np.array([[[float(lookup[cid,rid,li,m][key]) for key in METRICS] for m in METHODS] for rid in range(100)])
            boots=(weights@values.reshape(100,-1)).reshape(20000,3,len(METRICS))
            for si,method in enumerate(METHODS):
                row=dict(case_id=cid,lambda_index=li,lambda_bits_per_use=lam,method=method,missions=100)
                for ki,key in enumerate(METRICS):row.update({key+'_'+n:v for n,v in bootstrap_summary(values[:,si,ki],boots[:,si,ki]).items()})
                summary.append(row)
            for bi,baseline in enumerate(METHODS[:2]):
                for key in ('K','U','D','availability'):
                    ki=METRICS.index(key);delta=values[:,2,ki]-values[:,bi,ki];bb=boots[:,2,ki]-boots[:,bi,ki]
                    den=float(values[:,bi,ki].mean());valid=key in ('K','U') and den>1e-12
                    ratio=100*float(delta.mean())/den if valid else None
                    ci=np.quantile(100*bb/boots[:,bi,ki],[.025,.975]) if valid and np.all(boots[:,bi,ki]>1e-12) else [None,None]
                    tol=1e-9 if key=='D' else 1e-12
                    paired.append(dict(case_id=cid,lambda_index=li,lambda_bits_per_use=lam,baseline=baseline,metric=key,missions=100,
                        **bootstrap_summary(delta,bb),ratio_of_means_percent=ratio,ratio_ci95_low=ci[0],ratio_ci95_high=ci[1],
                        ratio_status='VALID_POSITIVE_BASELINE' if valid else 'UNDEFINED_OR_NOT_APPLICABLE',
                        strict_positive=int(np.sum(delta>tol)),ties=int(np.sum(abs(delta)<=tol)),negative=int(np.sum(delta<-tol)),baseline_mean=den))
    write_csv(out/'mobility/aggregate_statistics.csv',summary);write_csv(out/'mobility/paired_improvements.csv',paired)
    files=['mobility/aggregate_statistics.csv','mobility/paired_improvements.csv']
    save_json(out/'validation/aggregate.json',dict(status='CURRENTLY_VERIFIED_PASS',summary_rows=len(summary),paired_rows=len(paired),
        bootstrap_counts_reused_from_Stage_A=True,new_bootstrap_draws=0,elapsed_seconds=time.perf_counter()-started,
        artifact_sha256={n:sha(out/n) for n in files}))
    print('AGGREGATE_PASS',len(summary),'summaries;',len(paired),'paired contrasts',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,choices=('audit','cloud','compute','aggregate','verify'))
    args=parser.parse_args();c=read_json(ROOT/CODE[0]);validate(c);out=ROOT/c['output_directory']
    require((out/'startup_manifest.json').exists(),'Startup protection required')
    if (out/'validation/final_receipt.json').exists() and args.stage!='verify':raise FileExistsError('Completed Stage B is immutable')
    if args.stage=='verify':runpy.run_path(str(out/'validation/verify_stage_b.py'))['verify']()
    else:globals()[{'audit':'audit','cloud':'clouds','compute':'compute','aggregate':'aggregate'}[args.stage]](c,out)


if __name__=='__main__':main()
