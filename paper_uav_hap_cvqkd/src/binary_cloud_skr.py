"""Read-only exact clear-source integration and offline binary-cloud diagnostics."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import numpy as np

from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.exact_cache_provenance import source_hashes, source_settings, verify_source_payload
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config, candidate_from_payload
from src.mobility_skr import channel_state, objective_key, validate_result
from src.uav_mobility import candidate_grid, best_stationary, optimize_trajectory, scalar
from src.binary_cloud import cloud_parameters, positive_integer, mean_statistics

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'results/mobility_aware_skr_20261014'
UNIFORM=ROOT/'results/mobility_numerical_results_package_20261014/uniform'
STATUS='PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE'
SCHEMES=('S1','S2','S3','S4')


def read_csv(path):
    with Path(path).open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def verify_alias(path, expected):
    """Only byte-identical or provable line-ending aliases; never JSON reserialization."""
    hashes=source_hashes(Path(path).read_bytes())
    if expected not in hashes.values():
        raise ValueError(f'Historical content changed: {path}')
    return dict(path=str(Path(path).relative_to(ROOT)).replace('\\','/'),historical_sha256=expected,
                **hashes,verification='RAW_BYTE_MATCH' if expected==hashes['raw_sha256'] else 'VERIFIED_NEWLINE_EQUIVALENT')


def validate_settings(settings):
    if settings.get('schema')!='binary-cloud-skr-v1' or settings.get('scientific_model')!='effective_channel_no_fading_noise':
        raise ValueError('Unsupported binary-cloud experiment/model')
    old=saved.read_json(OLD/'full/inputs.json')['settings']
    if settings['geometry']!=old['geometry'] or settings['channel']!=old['channel']:
        raise ValueError('Approved reference geometry and clear-channel conventions must be preserved')
    positions=candidate_grid(1000.,10)
    mission=settings['mission']; opt=settings['optimization']; cloud=settings['cloud']
    positive_integer(mission['slots'],'slots'); positive_integer(cloud['realizations'],'realizations')
    if cloud['realizations']<2:raise ValueError('At least two independent missions are required')
    scalar(mission['slot_duration_s'],'slot duration',positive=True)
    scalar(mission['max_speed_m_per_s'],'maximum speed',nonnegative=True)
    scalar(opt['reference_distance_m'],'reference distance',positive=True)
    scalar(opt['positive_lambda_bits_per_use'],'positive lambda',positive=True)
    scalar(opt['K_min_bits_per_use'],'availability threshold',positive=True)
    if opt['initial_position_freely_selectable'] is not True or opt['deployment_cost_included'] is not False:
        raise ValueError('Free initial position and excluded deployment are required')
    if opt['channel_use_rate_per_s'] is not None:raise ValueError('No physical channel-use rate was approved')
    if cloud['model']!='stationary_gaussian_copula_ar1_complete_blockage':raise ValueError('Unsupported cloud model')
    allowed={'model','probability','correlation_length_m','temporal_rho','seed','realizations','parameter_origin'}
    if set(cloud)!=allowed:raise ValueError('Cloud config must not contain geometric-cloud parameters')
    cloud_parameters(cloud['probability'],cloud['correlation_length_m'],cloud['temporal_rho'])
    if type(cloud['seed']) is not int or cloud['seed']<0:raise ValueError('Invalid seed')
    for p in settings['sweeps']['probability']:cloud_parameters(p,cloud['correlation_length_m'],cloud['temporal_rho'])
    for ell in settings['sweeps']['correlation_length_m']:cloud_parameters(cloud['probability'],ell,cloud['temporal_rho'])
    for rho in settings['sweeps']['temporal_rho']:cloud_parameters(cloud['probability'],cloud['correlation_length_m'],rho)
    penalties=settings['sweeps']['lambda_bits_per_use']
    if penalties!=sorted(penalties) or len(set(penalties))!=len(penalties) or 0. not in penalties or opt['positive_lambda_bits_per_use'] not in penalties:
        raise ValueError('Lambda sweep must be unique and include zero/default')
    for penalty in penalties:scalar(penalty,'lambda',nonnegative=True)
    return positions


def load_sources(settings, protected_hashes):
    roster_path=ROOT/settings['source_roster']; receipt=saved.read_json(ROOT/settings['source_roster_receipt'])
    aliases=[verify_alias(roster_path,receipt['source_roster_sha256'])]
    roster=read_csv(roster_path); config=unconstrained_config(); groups={'MB':[],'Uniform':[]}
    for row in roster:
        family=row['family']
        if family not in groups:raise ValueError('Unexpected source family')
        path=ROOT/row['source_path']; aliases.append(verify_alias(path,row['source_payload_sha256']))
        if protected_hashes.get(row['source_path'])!=saved.digest(path):raise ValueError('Source changed since startup')
        payload=saved.read_json(path)
        payload['_provenance']=verify_source_payload(payload,source_settings(config));payload['_path']=row['source_path']
        candidate=candidate_from_payload(config,{payload['ensemble_hash']:payload},family,
            float.fromhex(payload['nu_mb_raw_hex']),float.fromhex(payload['V_A_hex']))
        if candidate is None:raise ValueError('Exact ensemble missing from source payload')
        saved.authenticate(candidate,protected_hashes,config)
        if any(candidate[k]!=float(row[k]) for k in ('C','w','nu_raw','V_A')) or candidate['ensemble_hash']!=row['ensemble_hash']:
            raise ValueError('Source roster numerical/ensemble mismatch')
        groups[family].append(candidate)
    for family,count in (('MB',197),('Uniform',30)):
        groups[family].sort(key=lambda c:(c['nu_raw'],c['V_A'],c['ensemble_hash']))
        if len(groups[family])!=count or len({c['ensemble_hash'] for c in groups[family]})!=count:
            raise ValueError(f'Incomplete or duplicate {family} source catalog')
    return groups,config,aliases


def clear_state(settings, position, index):
    # The legacy clear builder reads attenuation even for blocked=False; no cloud loss is applied.
    adapter=dict(settings,cloud={'attenuation_db':0.})
    state=channel_state(adapter,position,False);state['position_index']=index
    if state['cloud_transmittance']!=1. or state['blocked']:raise ValueError('Clear state required')
    return state


def select_winner(rows):
    if not rows:raise ValueError('Empty P1 catalog')
    return min(rows,key=lambda r:(-r['SKR'],r['nu_raw'],r['V_A'],r['ensemble_hash']))


def covariance_check(row):
    a,b,z=(row[k] for k in ('a','b','Z_star'))
    matrix=np.array([[a,0,z,0],[0,a,0,-z],[z,0,b,0],[0,-z,0,b]],dtype=float)
    omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]]))
    physical_min=float(np.linalg.eigvalsh(matrix+1j*omega).min())
    spectrum=np.sort(np.abs(np.linalg.eigvals(1j*omega@matrix)))[::2]
    expected=sorted([row['lambda_1'],row['lambda_2']])
    residual=float(np.max(np.abs(spectrum-expected)))
    conditional=a-z*z/(b+1)
    def entropy(value):
        if value<1.-1e-12:raise ValueError('Nonphysical entropy argument')
        n=max(0.,(value-1)/2)
        return (n+1)*math.log2(n+1)-(n*math.log2(n) if n else 0.)
    chi=entropy(spectrum[0])+entropy(spectrum[1])-entropy(conditional)
    if physical_min < -1e-11 or residual>1e-10 or abs(conditional-row['lambda_3'])>1e-10 or abs(chi-row['chi_BE'])>1e-10:
        raise ValueError('Independent covariance/spectrum/entropy check failed')
    return dict(spectrum_residual=residual,entropy_residual=abs(chi-row['chi_BE']),minimum_uncertainty_eigenvalue=physical_min)


def load_clear_bank(settings, protected_hashes):
    """Import only authenticated clear rows; preserve every historical byte/key."""
    positions=validate_settings(settings)
    groups,config,aliases=load_sources(settings,protected_hashes)
    inputs=saved.read_json(OLD/'full/inputs.json');identity=inputs['scientific_identity']
    if identity['baseline_config']!=saved.config_identity(config):raise ValueError('Scientific config differs from cached config')
    for name,h in identity['scientific_implementation'].items():aliases.append(verify_alias(ROOT/name,h))
    aliases.append(verify_alias(ROOT/'scripts/build_mobility_numerical_package.py',saved.read_json(UNIFORM/'receipt.json')['adapter_sha256']))
    aliases.append(verify_alias(ROOT/'scripts/run_mobility_skr_experiment.py',inputs['producer_sha256']))
    original_receipt=saved.read_json(OLD/'full/experiment_receipt.json')
    for name in ('inputs.json','channel_states.json'):
        aliases.append(verify_alias(OLD/'full'/name,original_receipt['output_sha256'][name]))
    old_states=saved.read_json(OLD/'full/channel_states.json')
    states={s['position_index']:s for s in old_states if s['blocked'] is False and s['cloud_transmittance']==1.}
    if len(states)!=100:raise ValueError('Incomplete historical clear geometry')
    fresh_states=[];moment_residual=0.
    for j,position in enumerate(positions):
        old=states[j];fresh=clear_state(settings,position,j);fresh_states.append(fresh)
        if old['position_m']!=list(position) or not math.isclose(old['distance_m'],fresh['distance_m'],rel_tol=0.,abs_tol=1e-9):
            raise ValueError('Cached clear position/distance differs')
        if old['clear_raw_channel']!=fresh['clear_raw_channel']:raise ValueError('Cached physical fading law differs')
        for name in ('mean_eta','mean_sqrt_eta','mean_eta_xi_total'):
            residual=abs(old['moments'][name]-fresh['moments'][name]);moment_residual=max(moment_residual,residual)
            if residual>1e-12:raise ValueError('Clear physical moments changed')
    source_aliases={(a['path'],a['historical_sha256']):a for a in aliases}
    current_source_hashes={c['source_path']:saved.digest(ROOT/c['source_path']) for group in groups.values() for c in group}
    all_rows=[];winners={};reuse=[];gh=[];max_spectrum=max_entropy=0.;min_uncertainty=math.inf
    for family,directory in (('MB',OLD/'full'),('Uniform',UNIFORM)):
        receipt=saved.read_json(directory/('experiment_receipt.json' if family=='MB' else 'receipt.json'))
        for name in ('objective_cache.jsonl','all_candidate_evaluations.csv'):
            aliases.append(verify_alias(directory/name,receipt['output_sha256'][name]))
        journal={}
        with (directory/'objective_cache.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                record=json.loads(line)
                if record['row_sha256']!=saved.hash_json(record['row']) or record['key'] in journal:
                    raise ValueError('Historical objective journal corruption')
                journal[record['key']]=record
        clear_csv=[r for r in read_csv(directory/'all_candidate_evaluations.csv') if r['blocked']=='False']
        lookup={(int(r['position_index']),r['ensemble_hash']):r for r in clear_csv}
        if len(lookup)!=100*len(groups[family]) or len(lookup)!=len(clear_csv):raise ValueError('Clear-only catalog coverage incomplete')
        historical_identity=identity if family=='MB' else dict(identity,source_family='Uniform',adapter_sha256=receipt['adapter_sha256'])
        winners[family]=[]
        for j in range(100):
            rows=[]
            for candidate in groups[family]:
                cell=lookup[j,candidate['ensemble_hash']];record=journal[cell['objective_key']];row=record['row']
                if any(row[k]!=float(cell[k]) for k in ('C','w','V_A','nu_raw','SKR','I_AB','chi_BE')):
                    raise ValueError('CSV and objective journal disagree')
                alias_id=(candidate['source_path'],row['source_payload_sha256'])
                if alias_id not in source_aliases:
                    source_aliases[alias_id]=verify_alias(ROOT/candidate['source_path'],row['source_payload_sha256'])
                    aliases.append(source_aliases[alias_id])
                expected=objective_key(historical_identity,states[j],candidate,row['source_payload_sha256'])
                if expected!=record['key']:raise ValueError('Historical clear objective key failed')
                validate_result(row,candidate,states[j])
                if row['Holevo_target']!='chi_BE_at_direct_Z_star' or row['certified_fading_security_lower_bound'] is not False:
                    raise ValueError('Different scientific interpretation')
                orders=row['MI_orders']
                if [r['order'] for r in orders]!=[8,16,32] or abs(orders[2]['I_AB']-orders[1]['I_AB'])>1e-8:
                    raise ValueError('MI quadrature refinement failed')
                checks=covariance_check(row);max_spectrum=max(max_spectrum,checks['spectrum_residual']);max_entropy=max(max_entropy,checks['entropy_residual'])
                min_uncertainty=min(min_uncertainty,checks['minimum_uncertainty_eigenvalue'])
                flat=dict(row,family=family,position_index=j,objective_key=record['key'],row_sha256=record['row_sha256'])
                rows.append(flat);all_rows.append(flat)
                reuse.append(dict(family=family,position_index=j,ensemble_hash=row['ensemble_hash'],historical_objective_key=record['key'],
                    historical_row_sha256=record['row_sha256'],historical_source_payload_sha256=row['source_payload_sha256'],
                    current_source_payload_sha256=current_source_hashes[candidate['source_path']],origin=directory.relative_to(ROOT).as_posix(),blocked=False,cloud_transmittance=1.))
            winner=select_winner(rows)
            winner=dict(winner,K_star_raw=winner['SKR'],K_star=max(0.,winner['SKR']))
            winners[family].append(winner)
            hashes=[]
            for order_index in (1,2):
                best=min(rows,key=lambda r:(-r['MI_orders'][order_index]['SKR'],r['nu_raw'],r['V_A'],r['ensemble_hash']))
                hashes.append(best['ensemble_hash'])
            if hashes[0]!=hashes[1]:raise ValueError('GH16/32 P1 winner unresolved')
            gh.append(dict(family=family,position_index=j,GH16_32_winner_stable=True))
    aliases=list({(a['path'],a['historical_sha256']):a for a in aliases}.values())
    audit=dict(status='CURRENTLY_VERIFIED_PASS',scientific_status=STATUS,positions=100,MB_sources=197,Uniform_sources=30,
        reused_clear_MB=19700,reused_clear_Uniform=3000,new_P1_evaluations=0,new_source_moments=0,
        aliases=aliases,GH_winners=gh,physical_moment_maximum_residual=moment_residual,
        maximum_spectrum_residual=max_spectrum,maximum_entropy_residual=max_entropy,
        minimum_uncertainty_eigenvalue=min_uncertainty,interpolation=False,blocked_rows_imported=0)
    return dict(positions=positions,sources=groups,config=config,states=fresh_states,winners=winners,rows=all_rows,reuse=reuse,audit=audit)


def slot_table(clear_rates, blocked):
    clear_rates=np.asarray(clear_rates,dtype=float);blocked=np.asarray(blocked)
    if clear_rates.ndim!=1 or not np.isfinite(clear_rates).all() or blocked.dtype!=np.bool_ or blocked.ndim!=2 or blocked.shape[0]!=len(clear_rates) or not blocked.shape[1]:
        raise ValueError('Expected finite J-vector rates and nonempty boolean JxN cloud table')
    return (~blocked)*np.maximum(clear_rates,0.)[:,None]


def mission_results(settings, positions, winners, blocked, *, penalty=None, include_series=True):
    rates=slot_table([r['K_star_raw'] for r in winners],blocked)
    opt=settings['optimization'];mission=settings['mission'];slots=rates.shape[1]
    threshold=scalar(opt['K_min_bits_per_use'],'availability threshold',positive=True)
    penalty=opt['positive_lambda_bits_per_use'] if penalty is None else scalar(penalty,'lambda',nonnegative=True)
    stationary,means=best_stationary(rates)
    kwargs=dict(slot_duration_s=mission['slot_duration_s'],max_speed_m_per_s=mission['max_speed_m_per_s'],reference_distance_m=opt['reference_distance_m'])
    moving=optimize_trajectory(rates,positions,penalty_bits_per_use=0.,**kwargs)
    regularized=optimize_trajectory(rates,positions,penalty_bits_per_use=penalty,**kwargs)
    reference=settings['geometry']['reference_position_index']
    paths=[np.full(slots,reference,dtype=int),np.full(slots,stationary,dtype=int),moving['path'],regularized['path']]
    if means[stationary]+1e-12<means[reference] or moving['average_skr']+1e-12<means[stationary] or regularized['penalized_objective']+1e-12<means[stationary]:
        raise ValueError('P2/P3 dominance failed')
    summaries=[];series=[]
    for scheme,path in zip(SCHEMES,paths):
        selected=rates[path,np.arange(slots)];coordinates=positions[path]
        legs=np.r_[0.,np.linalg.norm(np.diff(coordinates,axis=0),axis=1)]
        if np.max(legs)>kwargs['slot_duration_s']*kwargs['max_speed_m_per_s']+1e-10:raise ValueError('Infeasible trajectory')
        distance=float(legs.sum());mean=float(selected.mean());own_lambda=penalty if scheme=='S4' else 0.
        summaries.append(dict(scheme=scheme,average_skr_bits_per_use=mean,availability=float(np.mean(selected>=threshold)),
            K_min_bits_per_use=threshold,total_flight_distance_m=distance,lambda_bits_per_use=own_lambda,
            penalized_objective_bits_per_use=mean-own_lambda*distance/opt['reference_distance_m'],
            objective_at_common_positive_lambda=mean-penalty*distance/opt['reference_distance_m'],
            initial_position_index=int(path[0]),final_position_index=int(path[-1]),max_transition_m=float(legs.max())))
        if include_series:
            cumulative=np.cumsum(selected)/slots
            for n,j in enumerate(path):
                source=winners[int(j)];active=not bool(blocked[j,n])
                series.append(dict(scheme=scheme,slot=n+1,slot_end_s=(n+1)*mission['slot_duration_s'],position_index=int(j),
                    x_m=float(positions[j,0]),y_m=float(positions[j,1]),blocked=not active,source_active=active,
                    clear_raw_skr=source['K_star_raw'],usable_skr=float(selected[n]),available=bool(selected[n]>=threshold),
                    nu_raw=source['nu_raw'],V_A=source['V_A'],mean_photons=source['V_A']/2,
                    ensemble_hash=source['ensemble_hash'],objective_key=source['objective_key'],leg_distance_m=float(legs[n]),
                    cumulative_normalized_skr=float(cumulative[n])))
    baseline=summaries[0]['average_skr_bits_per_use']
    for row in summaries:
        delta=row['average_skr_bits_per_use']-baseline
        row.update(improvement_vs_reference_absolute=delta,improvement_vs_reference_percent=100*delta/baseline if baseline>0 else None,
                   improvement_percent_status='DEFINED' if baseline>0 else 'UNDEFINED_ZERO_REFERENCE')
    return summaries,series


def cloud_scenarios(settings):
    cloud=settings['cloud'];base=(cloud['probability'],cloud['correlation_length_m'],cloud['temporal_rho'])
    scenarios=[]
    def add(values,axis):
        if values not in [r['parameters'] for r in scenarios]:
            scenarios.append(dict(scenario_id=len(scenarios),axis=axis,parameters=values,
                probability=values[0],correlation_length_m=values[1],temporal_rho=values[2]))
    add(base,'default')
    for p in settings['sweeps']['probability']:add((p,base[1],base[2]),'probability')
    for ell in settings['sweeps']['correlation_length_m']:add((base[0],ell,base[2]),'spatial')
    for rho in settings['sweeps']['temporal_rho']:add((base[0],base[1],rho),'temporal')
    return scenarios


def grouped_statistics(rows, group_fields, metric_fields):
    groups={}
    for row in rows:groups.setdefault(tuple(row[k] for k in group_fields),[]).append(row)
    output=[]
    for key,group in groups.items():
        for metric in metric_fields:
            output.append(dict(zip(group_fields,key),metric=metric,**mean_statistics([r[metric] for r in group])))
    return output
