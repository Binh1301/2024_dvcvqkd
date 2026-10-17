"""Versioned trusted heterodyne audit and matched synthetic regression stages."""
import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from src.binary_cloud_skr import load_sources,read_csv,select_winner,mission_results,grouped_statistics
from src.uav_mobility import candidate_grid,optimize_trajectory
from src.manuscript_literal_3moments import LiteralChannel
from src.manuscript_corrected_3moments import PhysicalFadingDistribution
from scripts.run_fading_effective_binary_cloud import physical_samples
from src.trusted_heterodyne_skr import MODEL,SECURITY_STATUS,evaluate_batch,evaluate_candidate

DEFAULT=ROOT/'results/trusted_heterodyne_skr_20261016'
CONFIG=ROOT/'configs/trusted_heterodyne_skr.json'
PRODUCERS=('src/trusted_heterodyne_skr.py','scripts/run_trusted_heterodyne_skr.py','tests/test_trusted_heterodyne_skr.py','configs/trusted_heterodyne_skr.json')
METRICS=('average_skr_bits_per_use','availability','total_flight_distance_m','penalized_objective_bits_per_use')


def producers():return {p:saved.digest(ROOT/p) for p in PRODUCERS}


def context(out):
    cfg=saved.read_json(CONFIG);s=saved.read_json(ROOT/cfg['binary_config'])
    h=saved.read_json(out/'startup_manifest.json')['protected_hashes']
    expected=dict(config=cfg,binary_settings=s,producers=producers(),protected_inputs=saved.digest(out/'startup_manifest.json'))
    if (out/'inputs.json').exists():
        if saved.read_json(out/'inputs.json')!=expected:raise ValueError('Input/producer changed; new namespace required')
    else:saved.save(out/'inputs.json',expected,exclusive=True)
    groups,c,aliases=load_sources(s,h)
    states=saved.read_json(ROOT/cfg['matched_cloud_results']/'clear_channel_states.json')
    tests=saved.read_json(out/'test_receipt.json')
    if tests['status']!='CURRENTLY_VERIFIED_PASS' or tests['producers']!=producers():raise ValueError('Current tests required')
    torch.set_num_threads(1)
    return cfg,s,h,groups,c,states,aliases


def validate(out):
    if (out/'validation_receipt.json').exists():raise ValueError('Validation already complete')
    cfg,s,h,groups,c,states,aliases=context(out)
    ref=saved.read_json(ROOT/cfg['reference_pair_from'])['reference_pair']
    source=next(x for x in groups['MB'] if all(x[k]==v for k,v in ref.items()))
    detector=saved.read_json(ROOT/cfg['diagnostic_detector_from'])
    pair=dict(eta_B=detector['R'],nu_B=detector['xi_det'])
    primary=dict(eta_B=s['channel']['R'],nu_B=s['channel']['xi_det'])
    previous=saved.read_json(ROOT/cfg['previous_effective_results']/'reference_fixed_source.json')
    rows={name:evaluate_candidate(source,states[44]['moments'],c,h,**d) for name,d in [('corrected_primary',primary),('trusted_detector_diagnostic',pair)]}
    rows.update(previous_ideal=previous['updated'],legacy_no_fading_variance=previous['legacy'])
    saved.save(out/'reference_decomposition.json',rows,exclusive=True)
    quantities=('V_A','nu_raw','mean_eta','mean_sqrt_eta','T_eff','fading_variance','m_xi','N_eff','xi_eff','C','w','W_pre','Z_star','lambda_1','lambda_2','conditional_symplectic_eigenvalues','I_AB','beta_I_AB','chi_BE','K_raw','K_usable','chi_het','chi_line','chi_tot')
    table=[]
    aliases_old={'m_xi':'m_excess','W_pre':'b','K_raw':'SKR'}
    for k in quantities:
        old=previous['updated'].get(aliases_old.get(k,k))
        if k=='conditional_symplectic_eigenvalues':old=[previous['updated']['lambda_3']]
        new=rows['corrected_primary'][k]
        diff=new-old if isinstance(new,(int,float)) and isinstance(old,(int,float)) else None
        table.append(dict(quantity=k,previous_moment_ideal=old,corrected_primary=new,difference=diff,trusted_diagnostic=rows['trusted_detector_diagnostic'][k]))
    saved.write_csv(out/'reference_comparison.csv',table)
    small=[]
    for family in ('MB','Uniform'):
        sources=[groups[family][0],groups[family][len(groups[family])//2],groups[family][-1]]
        for x in sources:
            for name,d in [('primary',primary),('trusted_diagnostic',pair)]:
                for j,row in zip((0,9,44,90,99),evaluate_batch(x,[states[j]['moments'] for j in (0,9,44,90,99)],c,h,**d)):
                    small.append(dict(family=family,position_index=j,detector_case=name,**row))
    saved.save(out/'small_evaluations.json',small,exclusive=True)
    mc=[];law=[]
    for j in cfg['MC']['positions']:
        raw=LiteralChannel(**states[j]['clear_raw_channel']);fading=PhysicalFadingDistribution(raw)
        actual=fading.moments(R=1,xi_det=0,xi_ch=s['channel']['xi_ch'])
        if actual!=states[j]['moments']:raise ValueError('Analytical physical law/moments changed')
        law.append(dict(position_index=j,**fading.diagnostics(),moment_quadrature_errors=actual['moment_quadrature_errors'],
                        mean_eta=actual['mean_eta'],mean_sqrt_eta=actual['mean_sqrt_eta'],m_xi=actual['mean_eta']*s['channel']['xi_ch']))
        values=physical_samples(fading,cfg['MC']['samples_per_position'],np.random.default_rng(cfg['MC']['seed_base']+j))
        vectors=(values,np.sqrt(values),s['channel']['xi_ch']*values)
        targets=(actual['mean_eta'],actual['mean_sqrt_eta'],s['channel']['xi_ch']*actual['mean_eta'])
        for name,vector,target in zip(('m1','mhalf','m_xi_channel'),vectors,targets):
            blocks=vector.reshape(cfg['MC']['independent_blocks'],-1).mean(axis=1)
            se=float(blocks.std(ddof=1)/math.sqrt(len(blocks)));error=float(vector.mean())-target
            if abs(error)>cfg['MC']['sigma_acceptance']*se+1e-10:raise ValueError('Physical MC moment check failed')
            mc.append(dict(position_index=j,moment=name,analytic=target,MC=float(vector.mean()),SE=se,error=error,status='CURRENTLY_VERIFIED_PASS'))
    saved.write_csv(out/'MC_channel_moments.csv',mc);saved.save(out/'physical_law_audit.json',law)
    saved.save(out/'source_alias_audit.json',aliases)
    saved.save(out/'validation_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',producers=producers(),small_evaluations=len(small),MC_samples=5*65536,MC_moment_checks=len(mc),security_status=SECURITY_STATUS,full_nonideal_catalog=False,primary_detector=primary,diagnostic_detector=pair),exclusive=True)
    print('VALIDATION_PASS',rows['corrected_primary']['K_raw'],rows['trusted_detector_diagnostic']['K_raw'],flush=True)


def journal_rows(out):
    inputs=saved.hash_json(saved.read_json(out/'inputs.json'));records={}
    path=out/'objective_batches.jsonl'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            x=json.loads(line)
            if x['inputs_sha256']!=inputs or saved.hash_json(x['rows'])!=x['rows_sha256'] or x['source_id'] in records:raise ValueError('Journal provenance or duplicate source failure')
            records[x['source_id']]=x
    return inputs,records


def full(out):
    if (out/'full_receipt.json').exists():raise ValueError('Completed experiment is immutable')
    cfg,s,h,groups,c,states,_=context(out)
    gate=saved.read_json(out/'validation_receipt.json')
    if gate['status']!='CURRENTLY_VERIFIED_PASS' or gate['producers']!=producers():raise ValueError('Validation gate failed')
    identity,records=journal_rows(out);initial=len(records);start=time.perf_counter()
    detector=dict(eta_B=s['channel']['R'],nu_B=s['channel']['xi_det'])
    for family in ('MB','Uniform'):
        for x in groups[family]:
            source_id=family+':'+x['ensemble_hash']
            if source_id not in records:
                rows=[]
                for j,r in enumerate(evaluate_batch(x,[st['moments'] for st in states],c,h,**detector)):
                    key=saved.hash_json(dict(model=MODEL,inputs_sha256=identity,ensemble=x['ensemble_hash'],position=j,detector=detector))
                    rows.append(dict(r,family=family,position_index=j,objective_key=key))
                record=dict(source_id=source_id,inputs_sha256=identity,rows=rows,rows_sha256=saved.hash_json(rows))
                with (out/'objective_batches.jsonl').open('a',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(record,allow_nan=False)+'\n')
                records[source_id]=record
            if len(records)%20==0:print('SOURCE_BATCHES',len(records),'/227',flush=True)
    allrows=[r for rec in records.values() for r in rec['rows']]
    winners={f:[dict(select_winner([r for r in allrows if r['family']==f and r['position_index']==j])) for j in range(100)] for f in groups}
    for f in groups:
        for winner in winners[f]:winner.update(K_star_raw=winner['K_raw'],K_star=winner['K_usable'])
    saved.save(out/'clear_winners.json',winners,exclusive=True)
    flatkeys=('family','position_index','nu_raw','V_A','C','w','ensemble_hash','source_cache_key','source_payload_sha256','mean_eta','mean_sqrt_eta','m_xi','T_eff','fading_variance','fading_excess_output','channel_excess_output','N_eff','xi_eff','W_pre','Z_star','lambda_1','lambda_2','I_AB','beta_I_AB','chi_BE','K_raw','K_usable','objective_key','security_status')
    saved.write_csv(out/'all_candidate_evaluations.csv',[{k:r[k] for k in flatkeys} for r in allrows])
    saved.write_csv(out/'clear_winners.csv',[{**{k:r[k] for k in flatkeys},'K_star':r['K_star'],'K_star_raw':r['K_star_raw']} for pool in winners.values() for r in pool])
    old=ROOT/cfg['matched_cloud_results'];clouds=np.load(old/'cloud_states.npz',allow_pickle=False)['blocked'];scenarios=saved.read_json(old/'cloud_scenarios.json')
    positions=candidate_grid();paths=np.zeros((16,100,2,4,30),dtype=np.int16);summaries=[];series=[]
    for scenario in scenarios:
        sid=scenario['scenario_id']
        for realization in range(100):
            for f,family in enumerate(('MB','Uniform')):
                summary,ts=mission_results(s,positions,winners[family],clouds[sid,realization])
                meta=dict(scenario_id=sid,realization_id=realization,family=family)
                summaries.extend(dict(meta,**r) for r in summary)
                for k,scheme in enumerate(('S1','S2','S3','S4')):paths[sid,realization,f,k]=[r['position_index'] for r in ts if r['scheme']==scheme]
                if sid==0 and realization==0:series.extend(dict(meta,**r) for r in ts)
        print('MISSION_SCENARIO',sid+1,'/16',flush=True)
    penalties=s['sweeps']['lambda_bits_per_use'];lpaths=np.zeros((100,2,len(penalties),30),dtype=np.int16);lrows=[]
    for realization in range(100):
        for f,family in enumerate(('MB','Uniform')):
            table=(~clouds[0,realization])*np.array([r['K_star'] for r in winners[family]])[:,None]
            for k,penalty in enumerate(penalties):
                result=optimize_trajectory(table,positions,slot_duration_s=s['mission']['slot_duration_s'],max_speed_m_per_s=s['mission']['max_speed_m_per_s'],penalty_bits_per_use=penalty,reference_distance_m=s['optimization']['reference_distance_m'])
                lpaths[realization,f,k]=result['path'];lrows.append(dict(realization_id=realization,family=family,lambda_bits_per_use=penalty,average_skr_bits_per_use=result['average_skr'],availability=float(np.mean(result['rates']>=s['optimization']['K_min_bits_per_use'])),total_flight_distance_m=result['total_flight_distance_m'],penalized_objective_bits_per_use=result['penalized_objective']))
    np.savez_compressed(out/'trajectories.npz',paths=paths,lambda_paths=lpaths)
    saved.write_csv(out/'summary.csv',summaries);saved.write_csv(out/'time_series.csv',series);saved.write_csv(out/'lambda_sweep.csv',lrows)
    saved.write_csv(out/'summary_statistics.csv',grouped_statistics(summaries,('scenario_id','family','scheme'),METRICS))
    saved.write_csv(out/'lambda_statistics.csv',grouped_statistics(lrows,('family','lambda_bits_per_use'),METRICS))
    saved.save(out/'full_receipt.json',dict(status='COMPUTED_PENDING_INDEPENDENT_VERIFICATION',producers=producers(),clear_evaluations=len(allrows),new_evaluations=(len(records)-initial)*100,legacy_K_reuse=0,source_moments_generated=0,missions=1600,detector=detector,matched_cloud_sha256=saved.digest(old/'cloud_states.npz'),security_status=SECURITY_STATUS,elapsed_seconds=time.perf_counter()-start,output_sha256={p:saved.digest(out/p) for p in ('objective_batches.jsonl','all_candidate_evaluations.csv','clear_winners.csv','clear_winners.json','summary.csv','summary_statistics.csv','lambda_sweep.csv','lambda_statistics.csv','trajectories.npz','time_series.csv')}),exclusive=True)
    print('FULL_COMPUTED',len(allrows),flush=True)


def verify(out):
    from scripts.verify_binary_cloud_skr_results import optimal_value,path_metrics,assert_metrics,stationary_gap,verify_statistics
    cfg,s,h,groups,c,states,_=context(out);receipt=saved.read_json(out/'full_receipt.json')
    if receipt['producers']!=producers():raise ValueError('Scientific producer changed')
    for name,digest in receipt['output_sha256'].items():
        if saved.digest(out/name)!=digest:raise ValueError('Output hash changed: '+name)
    _,records=journal_rows(out);rows=[r for x in records.values() for r in x['rows']]
    prior={(r['family'],int(r['position_index']),r['ensemble_hash']):r for r in read_csv(ROOT/cfg['previous_effective_results']/'all_candidate_evaluations.csv')}
    maximum=0.
    for row in rows:
        m=states[row['position_index']]['moments'];t=m['mean_sqrt_eta']**2;noise=(m['mean_eta']-t)*row['V_A']+m['mean_eta']*s['channel']['xi_ch']
        assert_metrics(row,dict(T_eff=t,N_eff=noise,W_pre=1+m['mean_eta']*(row['V_A']+s['channel']['xi_ch']),Z_star=2*math.sqrt(t)*row['C']-math.sqrt(2*noise*row['w']),K_raw=s['channel']['beta_rec']*row['I_AB']-row['chi_BE'],K_usable=max(0.,row['K_raw'])))
        before=prior[row['family'],row['position_index'],row['ensemble_hash']]
        maximum=max(maximum,max(abs(row[k]-float(before[k])) for k in ('I_AB','chi_BE','K_raw','Z_star')))
    if len(rows)!=22700 or maximum>1e-10:raise ValueError('Full ideal regression mismatch')
    winners=saved.read_json(out/'clear_winners.json')
    for family,pool in winners.items():
        for j,w in enumerate(pool):
            source=select_winner([r for r in rows if r['family']==family and r['position_index']==j])
            if source['ensemble_hash']!=w['ensemble_hash'] or source['K_raw']!=w['K_star_raw']:raise ValueError('P1 maximum mismatch')
    clouds=np.load(ROOT/cfg['matched_cloud_results']/'cloud_states.npz',allow_pickle=False)['blocked'];archive=np.load(out/'trajectories.npz',allow_pickle=False)
    positions=candidate_grid();distance=np.linalg.norm(positions[:,None]-positions[None,:],axis=2);limit=s['mission']['slot_duration_s']*s['mission']['max_speed_m_per_s'];feasible=distance<=limit
    summaries=read_csv(out/'summary.csv');lookup={(int(r['scenario_id']),int(r['realization_id']),r['family'],r['scheme']):r for r in summaries};checks=0
    for sid in range(16):
        for realization in range(100):
            for f,family in enumerate(('MB','Uniform')):
                table=(~clouds[sid,realization])*np.array([r['K_star'] for r in winners[family]])[:,None]
                for k,scheme in enumerate(('S1','S2','S3','S4')):
                    penalty=s['optimization']['positive_lambda_bits_per_use'] if k==3 else 0.;path=archive['paths'][sid,realization,f,k]
                    metrics=path_metrics(path,table,positions,distance,limit,s['optimization']['K_min_bits_per_use'],penalty,s['optimization']['reference_distance_m']);assert_metrics(lookup[sid,realization,family,scheme],metrics)
                    if k==0 and not (path==44).all():raise ValueError('Reference changed')
                    if k==1:stationary_gap(path,table.mean(axis=1))
                    if k>=2:
                        checks+=1
                        if abs(metrics['penalized_objective_bits_per_use']-optimal_value(table,distance,feasible,penalty,s['optimization']['reference_distance_m']))>1e-11:raise ValueError('Bellman mismatch')
    lrows=read_csv(out/'lambda_sweep.csv');llookup={(int(r['realization_id']),r['family'],float(r['lambda_bits_per_use'])):r for r in lrows}
    for realization in range(100):
        for f,family in enumerate(('MB','Uniform')):
            table=(~clouds[0,realization])*np.array([r['K_star'] for r in winners[family]])[:,None]
            for k,penalty in enumerate(s['sweeps']['lambda_bits_per_use']):
                path=archive['lambda_paths'][realization,f,k];metrics=path_metrics(path,table,positions,distance,limit,s['optimization']['K_min_bits_per_use'],penalty,s['optimization']['reference_distance_m']);assert_metrics(llookup[realization,family,penalty],metrics)
                if penalty not in (0.,s['optimization']['positive_lambda_bits_per_use']):
                    checks+=1
                    if abs(metrics['penalized_objective_bits_per_use']-optimal_value(table,distance,feasible,penalty,s['optimization']['reference_distance_m']))>1e-11:raise ValueError('Lambda Bellman mismatch')
    verify_statistics(out/'summary_statistics.csv',summaries,('scenario_id','family','scheme'));verify_statistics(out/'lambda_statistics.csv',lrows,('family','lambda_bits_per_use'))
    protected=saved.verify_protected(saved.read_json(out/'startup_manifest.json'))
    result=dict(status='CURRENTLY_VERIFIED_PASS',security_status=SECURITY_STATUS,producers=producers(),clear_evaluations=22700,P1_maxima=200,matched_missions=1600,Bellman_checks=checks,maximum_ideal_regression_difference=maximum,protected_files=len(h),protected_changes=protected,all_usable_zero=all(w['K_star']==0 for pool in winners.values() for w in pool),maximum_raw={f:max(w['K_star_raw'] for w in pool) for f,pool in winners.items()},full_nonideal_catalog=False,production_default_changed=False,publication_ready=False)
    saved.save(out/'final_validation.json',result,exclusive=True);print(json.dumps(result),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('validate','full','verify'),required=True);parser.add_argument('--output',type=Path,default=DEFAULT);args=parser.parse_args()
    globals()[args.stage](args.output)

if __name__=='__main__':main()
