"""Approved synthetic binary-cloud diagnostic; preserves old experiments."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from src.binary_cloud import generate_cloud, correlation_audit
from src.binary_cloud_skr import (STATUS,load_clear_bank,validate_settings,mission_results,
                                 cloud_scenarios,grouped_statistics,slot_table)
from src.uav_mobility import optimize_trajectory

DEFAULT=ROOT/'results/binary_cloud_skr_20261015'
CONFIG=ROOT/'configs/binary_cloud_skr_demo.json'
PRODUCERS=('src/binary_cloud.py','src/binary_cloud_skr.py',
    'scripts/run_binary_cloud_skr_experiment.py','tests/test_binary_cloud.py','tests/test_binary_cloud_skr.py')
METRICS=('average_skr_bits_per_use','availability','total_flight_distance_m','penalized_objective_bits_per_use')


def producers():return {p:saved.digest(ROOT/p) for p in PRODUCERS}


def verify_protected(output):
    return saved.verify_protected(saved.read_json(Path(output)/'startup_manifest.json'))


def ensure_startup(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (output/'startup_manifest.json').exists():return
    hashes={}
    for folder in ('src','scripts','configs','tests','results'):
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and '.pytest_cache' not in path.parts and not path.is_relative_to(output):
                hashes[path.relative_to(ROOT).as_posix()]=saved.digest(path)
    for p in ('docs/FINAL_MODEL_SPEC.md','docs/SECURITY_SCOPE_FREEZE.md','docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md'):
        hashes[p]=saved.digest(ROOT/p)
    saved.save(output/'startup_manifest.json',dict(schema='binary-cloud-startup-v1',
        created_utc=datetime.now(timezone.utc).isoformat(),protected_hashes=hashes,
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','-c','core.longpaths=true','status','--short','--branch'],cwd=ROOT,text=True),
        frozen_sha256=hashes['docs/FINAL_MODEL_SPEC.md'],frozen_historical_discrepancy=True,
        scope='Explicitly approved preliminary binary-cloud diagnostic; no publication/security promotion',
        lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS'),exclusive=True)


def identity(settings):return dict(settings=settings,producers=producers(),scope=STATUS)


def bind_inputs(output,settings):
    expected=identity(settings);path=output/'inputs.json'
    if path.exists():
        if saved.read_json(path)!=expected:raise ValueError('Input/producer identity changed; choose a new output namespace')
    else:saved.save(path,expected,exclusive=True)
    return expected


def audit(output,settings):
    ensure_startup(output);verify_protected(output)
    inputs=bind_inputs(output,settings)
    if (output/'audit_receipt.json').exists():raise ValueError('Audit already completed; preserve it')
    bank=load_clear_bank(settings,saved.read_json(output/'startup_manifest.json')['protected_hashes'])
    saved.save(output/'clear_channel_states.json',bank['states'])
    saved.write_csv(output/'clear_candidate_evaluations.csv',bank['rows'])
    saved.write_csv(output/'cache_reuse_audit.csv',bank['reuse'])
    saved.write_csv(output/'clear_winners.csv',[r for family in bank['winners'].values() for r in family])
    saved.write_csv(output/'source_roster.csv',[{k:c[k] for k in ('family','nu_raw','nu_repo','V_A','C','w','ensemble_hash','source_cache_key','canonical_source_cache_key','source_path')} for group in bank['sources'].values() for c in group])
    saved.write_csv(output/'positions.csv',[dict(position_index=j,x_m=p[0],y_m=p[1]) for j,p in enumerate(bank['positions'])])
    spread=[]
    for family,winners in bank['winners'].items():
        values=np.array([r['K_star'] for r in winners])
        spread.append(dict(family=family,minimum=float(values.min()),maximum=float(values.max()),mean=float(values.mean()),
            population_sd=float(values.std()),CV=float(values.std()/values.mean()) if values.mean() else None,
            range_over_mean=float(np.ptp(values)/values.mean()) if values.mean() else None,
            distinct_source_pairs=len({(r['nu_raw'],r['V_A']) for r in winners})))
    saved.write_csv(output/'clear_sky_spatial_variation.csv',spread)
    omissions=[]
    for family,group in bank['winners'].items():
        for j,row in enumerate(group):
            m1=bank['states'][j]['moments']['mean_eta'];t=row['T_eff'];va=row['V_A']
            omissions.append(dict(family=family,position_index=j,V_A=va,T_eff=t,mean_eta=m1,adopted_noise=t*.0186,
                omitted_fading_variance=(m1-t)*va,omitted_channel_noise_difference=(m1-t)*.0186,
                full_fading_security='NOT_ESTABLISHED'))
    saved.write_csv(output/'fading_omission_audit.csv',omissions)
    statistics=correlation_audit(bank['positions'])
    saved.save(output/'correlation_audit.json',statistics)
    if statistics['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Cloud statistics failed')
    receipt=dict(bank['audit'],input_sha256=saved.hash_json(inputs),protected_changes=verify_protected(output),
                 correlation_audit_sha256=saved.digest(output/'correlation_audit.json'),
                 output_sha256={n:saved.digest(output/n) for n in ('clear_channel_states.json','clear_candidate_evaluations.csv',
                    'clear_winners.csv','source_roster.csv','positions.csv','cache_reuse_audit.csv','clear_sky_spatial_variation.csv','correlation_audit.json','fading_omission_audit.csv')})
    saved.save(output/'audit_receipt.json',receipt,exclusive=True)
    print('AUDIT_COMPLETE',len(bank['rows']),'clear rows; cloud statistics',statistics['status'],flush=True)


def load_winners(output):
    from src.binary_cloud_skr import read_csv
    rows=read_csv(output/'clear_winners.csv');groups={family:[] for family in ('MB','Uniform')}
    numeric=('nu_raw','V_A','C','w','K_star_raw','K_star','SKR','I_AB','chi_BE','T_eff','xi_eff','N_eff','a','b','Z_star','lambda_1','lambda_2','lambda_3')
    for row in rows:
        for name in numeric:row[name]=float(row[name])
        row['position_index']=int(row['position_index']);groups[row['family']].append(row)
    for rows in groups.values():
        rows.sort(key=lambda r:r['position_index'])
        if [r['position_index'] for r in rows]!=list(range(100)):raise ValueError('Winner positions incomplete')
    return groups


def require_stage(output,settings,stage):
    if saved.read_json(output/'inputs.json')!=identity(settings):raise ValueError('Producer/config identity changed')
    if saved.read_json(output/stage)['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Previous stage did not pass')
    verify_protected(output)


def smoke(output,settings):
    require_stage(output,settings,'audit_receipt.json')
    if (output/'smoke_receipt.json').exists():raise ValueError('Smoke already complete')
    from src.binary_cloud_skr import load_sources,clear_state,read_csv
    import torch
    torch.set_num_threads(1)
    hashes=saved.read_json(output/'startup_manifest.json')['protected_hashes']
    groups,config,_=load_sources(settings,hashes);positions=validate_settings(settings)
    cached={(r['family'],int(r['position_index']),r['ensemble_hash']):float(r['SKR']) for r in read_csv(output/'clear_candidate_evaluations.csv')}
    selected={'MB':{(.165,5.5),(.17,5.046875),(.2,1.3833230302980657)},'Uniform':{(0.,.5),(0.,1.),(0.,1.25)}}
    began=time.perf_counter();rows=[]
    for family in groups:
        candidates=[c for c in groups[family] if (c['nu_raw'],c['V_A']) in selected[family]]
        if len(candidates)!=3:raise ValueError('Smoke candidates missing')
        for j in (0,9,44,90,99):
            state=clear_state(settings,positions[j],j)
            for candidate in candidates:
                result=saved.evaluate_authenticated(candidate,state['moments'],config,hashes)
                residual=abs(result['SKR']-cached[family,j,candidate['ensemble_hash']])
                if residual>1e-11:raise ValueError('Fresh clear evaluator and cache disagree')
                rows.append(dict(family=family,position_index=j,nu_raw=candidate['nu_raw'],V_A=candidate['V_A'],
                    ensemble_hash=candidate['ensemble_hash'],SKR=result['SKR'],I_AB=result['I_AB'],chi_BE=result['chi_BE'],residual=residual))
    saved.write_csv(output/'smoke_evaluations.csv',rows)
    saved.save(output/'smoke_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',clear_evaluations=len(rows),
        elapsed_seconds=time.perf_counter()-began,maximum_residual=max(r['residual'] for r in rows),
        producer_sha256=producers(),protected_changes=verify_protected(output),new_source_moments=0,blocked_evaluations=0),exclusive=True)
    print('SMOKE_COMPLETE',len(rows),flush=True)


def experiment(output,settings):
    require_stage(output,settings,'smoke_receipt.json')
    tests=saved.read_json(output/'test_receipt.json')
    if tests['status']!='CURRENTLY_VERIFIED_PASS' or tests['producers']!=producers():raise ValueError('Current scoped tests required')
    if (output/'experiment_receipt.json').exists():raise ValueError('Completed experiment is immutable')
    positions=validate_settings(settings);winners=load_winners(output);scenarios=cloud_scenarios(settings)
    cloud=settings['cloud'];mission=settings['mission'];opt=settings['optimization'];count=cloud['realizations'];slots=mission['slots']
    shape=(len(scenarios),count,2,4,slots)
    clouds=np.zeros((len(scenarios),count,len(positions),slots),dtype=bool);paths=np.zeros(shape,dtype=np.int16)
    checkpoint=output/'checkpoint.json';summaries=[];demo=[];completed=0;began=time.perf_counter()
    partial=output/'partial_state.npz';journal=output/'partial_summary.json'
    if checkpoint.exists():
        state=saved.read_json(checkpoint)
        if state['input_sha256']!=saved.hash_json(identity(settings)):raise ValueError('Resume identity changed')
        saved_state=np.load(partial,allow_pickle=False)
        if str(saved_state['input_sha256'])!=saved.hash_json(identity(settings)):raise ValueError('Committed partial identity changed')
        completed=int(saved_state['completed_scenarios'])
        clouds[:]=saved_state['clouds'];paths[:]=saved_state['paths']
        summaries=json.loads(str(saved_state['summaries_json']))
    for scenario in scenarios[completed:]:
        sid=scenario['scenario_id'];p,ell,rho=scenario['parameters']
        for realization in range(count):
            blocked=generate_cloud(positions,slots,p,ell,rho,cloud['seed'],realization);clouds[sid,realization]=blocked
            for f,family in enumerate(('MB','Uniform')):
                summary,series=mission_results(settings,positions,winners[family],blocked,include_series=True)
                for k,scheme in enumerate(('S1','S2','S3','S4')):
                    group=[r for r in series if r['scheme']==scheme]
                    paths[sid,realization,f,k]=[r['position_index'] for r in group]
                meta=dict(scenario_id=sid,probability=p,correlation_length_m=ell,temporal_rho=rho,
                          realization_id=realization,family=family,cloud_blocked_fraction=float(blocked.mean()))
                summaries.extend(dict(meta,**r) for r in summary)
                if sid==0 and realization==0:demo.extend(dict(meta,**r) for r in series)
        # Checkpoints are at complete scenarios; incomplete scenarios are safely replayed on resume.
        temp=partial.with_suffix('.tmp.npz')
        np.savez_compressed(temp,clouds=clouds,paths=paths,completed_scenarios=sid+1,
            summaries_json=json.dumps(summaries,allow_nan=False),input_sha256=saved.hash_json(identity(settings)))
        temp.replace(partial)
        saved.save(checkpoint,dict(status='RUNNING',completed_scenarios=sid+1,total_scenarios=len(scenarios),
            input_sha256=saved.hash_json(identity(settings)),elapsed_seconds=time.perf_counter()-began))
        print('SCENARIO',sid+1,'/',len(scenarios),'p/ell/rho',p,ell,rho,flush=True)
    # Reconstruct the designated first mission even after resuming a checkpoint.
    if not demo:
        for family in ('MB','Uniform'):
            _,series=mission_results(settings,positions,winners[family],clouds[0,0])
            demo.extend(dict(scenario_id=0,realization_id=0,family=family,**r) for r in series)
    lambda_rows=[];lambda_paths=np.zeros((count,2,len(settings['sweeps']['lambda_bits_per_use']),slots),dtype=np.int16)
    penalties=settings['sweeps']['lambda_bits_per_use']
    default_index={(r['realization_id'],r['family'],r['scheme']):r for r in summaries if r['scenario_id']==0}
    for realization in range(count):
        for f,family in enumerate(('MB','Uniform')):
            table=slot_table([r['K_star_raw'] for r in winners[family]],clouds[0,realization])
            for k,penalty in enumerate(penalties):
                if penalty in (0.,opt['positive_lambda_bits_per_use']):
                    scheme='S3' if penalty==0. else 'S4';scheme_index=2 if penalty==0. else 3
                    path=paths[0,realization,f,scheme_index];row=default_index[realization,family,scheme]
                    metrics={name:row[name] for name in METRICS}
                else:
                    result=optimize_trajectory(table,positions,slot_duration_s=mission['slot_duration_s'],
                        max_speed_m_per_s=mission['max_speed_m_per_s'],penalty_bits_per_use=penalty,reference_distance_m=opt['reference_distance_m'])
                    path=result['path'];metrics=dict(average_skr_bits_per_use=result['average_skr'],availability=float(np.mean(result['rates']>=opt['K_min_bits_per_use'])),
                        total_flight_distance_m=result['total_flight_distance_m'],penalized_objective_bits_per_use=result['penalized_objective'])
                lambda_paths[realization,f,k]=path
                lambda_rows.append(dict(realization_id=realization,family=family,lambda_bits_per_use=penalty,**metrics))
            own=lambda_rows[-len(penalties):]
            for a,b in zip(own,own[1:]):
                if b['total_flight_distance_m']>a['total_flight_distance_m']+1e-8:raise ValueError('Flight increases with lambda')
    np.savez_compressed(output/'cloud_states.npz',blocked=clouds)
    np.savez_compressed(output/'trajectories.npz',paths=paths,lambda_paths=lambda_paths)
    saved.save(output/'cloud_scenarios.json',scenarios)
    saved.write_csv(output/'summary.csv',summaries);saved.write_csv(output/'scheme_time_series.csv',demo)
    saved.write_csv(output/'lambda_sweep.csv',lambda_rows)
    stats=grouped_statistics(summaries,('scenario_id','probability','correlation_length_m','temporal_rho','family','scheme'),METRICS)
    saved.write_csv(output/'summary_statistics.csv',stats)
    saved.write_csv(output/'lambda_statistics.csv',grouped_statistics(lambda_rows,('family','lambda_bits_per_use'),METRICS))
    paired=[]
    for scenario in scenarios:
        sid=scenario['scenario_id']
        lookup={(r['realization_id'],r['family'],r['scheme']):r for r in summaries if r['scenario_id']==sid}
        for scheme in ('S1','S2','S3','S4'):
            for realization in range(count):
                for name,fa,sa,fb,sb in [('MB_minus_Uniform','MB',scheme,'Uniform',scheme),
                                         ('MB_'+scheme+'_minus_S1','MB',scheme,'MB','S1')]:
                    paired.append(dict(scenario_id=sid,scheme=scheme,contrast=name,realization_id=realization,
                        **{metric:lookup[realization,fa,sa][metric]-lookup[realization,fb,sb][metric] for metric in METRICS}))
    saved.write_csv(output/'paired_statistics.csv',grouped_statistics(paired,('scenario_id','scheme','contrast'),METRICS))
    saved.save(checkpoint,dict(status='COMPLETE',completed_scenarios=len(scenarios),input_sha256=saved.hash_json(identity(settings))))
    names=('cloud_states.npz','trajectories.npz','cloud_scenarios.json','summary.csv','scheme_time_series.csv','lambda_sweep.csv',
           'summary_statistics.csv','lambda_statistics.csv','paired_statistics.csv')
    receipt=dict(status='COMPUTED_PENDING_INDEPENDENT_VERIFICATION',scientific_status=STATUS,scenarios=len(scenarios),
        missions_per_scenario=count,missions=len(scenarios)*count,DP_calls=len(scenarios)*count*4+count*2*(len(penalties)-2),
        source_candidates={'MB':197,'Uniform':30},clear_rows_reused=22700,new_P1_evaluations=0,
        elapsed_seconds=time.perf_counter()-began,new_source_moments=0,blocked_QKD_evaluations=0,
        cloud_RNG='PCG64 SeedSequence([20261015,realization_id]); common innovations across configurations',
        time_series_scope='Default scenario realization 0 only; all mission paths/cloud matrices preserved in NPZ',
        producers=producers(),input_sha256=saved.hash_json(identity(settings)),protected_changes=verify_protected(output),
        output_sha256={n:saved.digest(output/n) for n in names},lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    saved.save(output/'experiment_receipt.json',receipt,exclusive=True)
    print('EXPERIMENT_COMPLETE',receipt['missions'],'missions',receipt['DP_calls'],'DP',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,choices=('audit','smoke','experiment','export'))
    parser.add_argument('--config',type=Path,default=CONFIG);parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args();output=args.output.resolve();settings=saved.read_json(args.config)
    import torch
    torch.set_num_threads(1)
    try:
        if args.stage=='audit':audit(output,settings)
        elif args.stage=='smoke':smoke(output,settings)
        elif args.stage=='experiment':experiment(output,settings)
        else:
            from scripts.plot_binary_cloud_skr_results import export
            export(output,settings)
    except Exception as error:
        output.mkdir(parents=True,exist_ok=True)
        saved.save(output/(args.stage+'_failure_receipt.json'),dict(status='FAILED',stage=args.stage,error=str(error),producers=producers()))
        raise


if __name__=='__main__':main()
