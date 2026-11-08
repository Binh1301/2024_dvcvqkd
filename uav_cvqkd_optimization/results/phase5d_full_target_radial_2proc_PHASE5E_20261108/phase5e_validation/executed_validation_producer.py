"""Full-lookup integrity, pilot checks and fresh coordinate-derived spot checks.

Only run AFTER the separately authorized full job is sealed. No core/source
formula is changed; direct checks call the native full212-candidate evaluator.
"""
import argparse
import csv
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from . import lookup_benchmark as b
from .skr_pilot import ROOT,LOOKUP,read,read_rows,sha,compare_candidate
from .hap_uav_channel import waypoint_geometry
from .config import load_config
from .skr_lookup import SKRLookup

METRICS=('eta_f','xi_f','I_AB','chi_BE','K_raw')


def direct_positions(config):
    """Original lookup projection is a dataset property, not a new mission qH."""
    xy=[(1000.,1000.),(2000.,2000.),(1960.,2000.),(1000.,1040.),
        (520.,1000.),(280.,1720.),(1880.,400.)]
    points=[]
    for i,q in enumerate(xy):
        geometry=waypoint_geometry((1000.,1000.,config['hap_altitude_m']),q,
                                  config['uav_altitude_m'],config['zenith_atmospheric_transmittance'])
        points.append(dict(point_id=f'd{i}',x_m=q[0],y_m=q[1],
            zenith_deg=math.degrees(geometry.zenith_angle_rad),distance_m=geometry.slant_distance_m,
            geometry_origin='independent_coordinate_geometry_not_lookup_mapping'))
    return points


def compare_winner(actual,expected):
    return compare_candidate(actual,expected)


def _winner_from_csv(row,family):
    r={k:float(row[family+'_'+k]) for k in (*METRICS,'VA','nu_raw')}
    r['ensemble_hash']=row[family+'_ensemble_hash']
    return r


def normalized_output_seal(seal):
    normalized={name.replace('\\','/'):digest for name,digest in seal.items()}
    if len(normalized)!=len(seal):raise ValueError('Output manifest path normalization collision')
    return normalized


def check_npz_metadata(data,manifest,input_hash,producer_hash,rows):
    expected=dict(config_sha256=manifest['config_sha256'],input_manifest_sha256=input_hash,
        candidate_pool_sha256=manifest['candidate_pool_sha256'],producer_sha256=producer_hash,
        geometry_mode='radial_exact',coordinate_units='m',rate_units='bits/use',xi_ch=.0136,xi_det=.005)
    for name,value in expected.items():
        if data[name].item()!=value:raise ValueError('NPZ metadata mismatch: '+name)
    if data['paper_admissible'].item() is not False:raise ValueError('NPZ metadata evidence promoted')
    for family in ('MB','Uniform'):
        if not np.array_equal(data[family+'_source_evidence_class'],np.array([r[family+'_source_evidence_class'] for r in rows])):
            raise ValueError('NPZ metadata evidence array mismatch')


def require_pilot_positions(pilot,config):
    points=config['points']
    if (len(points)!=5 or len({p['point_id'] for p in points})!=5 or len(pilot['comparisons'])!=5
            or len(pilot['reproduction_checks'])!=5 or not all(c.get('passed') is True for c in pilot['reproduction_checks'])):
        raise ValueError('Require exactly five original reproduced pilot positions')
    if [r['point'] for r in pilot['comparisons']]!=points:raise ValueError('Pilot positions differ from sealed config')


def load_verified_pilot(directory):
    directory=Path(directory)
    if not (directory/'output_manifest.json').is_file():raise ValueError('Pilot requires original output seal')
    seal=normalized_output_seal(read(directory/'output_manifest.json'))
    if not {'summary.json','config.json','input_manifest.json'}<=set(seal):raise ValueError('Pilot output seal coverage incomplete')
    for name,h in seal.items():
        path=(directory/name).resolve()
        if not path.is_relative_to(directory.resolve()) or sha(path)!=h:raise ValueError('Pilot output seal mismatch')
    pilot=read(directory/'summary.json');config=read(directory/'config.json');manifest=read(directory/'input_manifest.json')
    digest=hashlib.sha256(json.dumps(config,sort_keys=True,allow_nan=False).encode()).hexdigest()
    if (digest!=manifest['config_sha256'] or digest!=pilot['config_sha256']
            or pilot['input_manifest_sha256']!=sha(directory/'input_manifest.json')):
        raise ValueError('Pilot config/input binding mismatch')
    require_pilot_positions(pilot,config)
    return pilot,config,manifest


def validate_full_data(directory):
    directory=Path(directory)
    if not (directory/'output_manifest.json').is_file():raise ValueError('Require a sealed completed full lookup before validation')
    seal=normalized_output_seal(read(directory/'output_manifest.json'))
    required={'config.json','input_manifest.json','summary.json','skr_map.csv','skr_map.npz','executed_producer_snapshot.py'}
    if not required<=set(seal):raise ValueError('Full lookup seal lacks required artifacts')
    for name,h in seal.items():
        path=(directory/name).resolve()
        if not path.is_relative_to(directory.resolve()) or sha(path)!=h:raise ValueError('Full output hash/path mismatch: '+name)
    config=read(directory/'config.json');manifest=read(directory/'input_manifest.json');summary=read(directory/'summary.json')
    if sha(directory/'config.json')!=manifest['config_sha256'] or sha(directory/'input_manifest.json')!=summary['input_manifest_sha256']:
        raise ValueError('Full config/input identity mismatch')
    for group in ('input_sha256','producer_sha256'):
        for name,h in manifest[group].items():
            if sha(name)!=h:raise ValueError('Full input/producer changed: '+name)
    old=read_rows(LOOKUP/'skr_map.csv');rows=read_rows(directory/'skr_map.csv')
    if len(rows)!=2601 or len({(r['x_m'],r['y_m']) for r in rows})!=2601:raise ValueError('Incomplete spatial map')
    for a,c in zip(old,rows):
        if any(float(a[k])!=float(c[k]) for k in ('x_m','y_m','distance_m','zenith_deg')):
            raise ValueError('Original grid coordinate/order changed')
    points=config['points']
    if len(points)!=294 or summary['evaluated_contexts']!=294:raise ValueError('Expected294 full geometry records')
    records={};gh=0.;labels=Counter();global_by_group={}
    for point in points:
        name='full/'+point['point_id']+'.json';seal_name='full/'+point['point_id']+'.seal.json'
        if name not in seal or seal_name not in seal:raise ValueError('Unsealed geometry checkpoint')
        path=directory/name;r=read(path)
        if read(directory/seal_name)['sha256']!=sha(path):raise ValueError('Geometry checkpoint seal mismatch')
        b._validate_record(r,'full',point,sha(directory/'input_manifest.json'),manifest['config_sha256'],
                           r['active_effective_protocol'],manifest['roster'])
        if (r['active_effective_protocol']['xi_ch'],r['active_effective_protocol']['xi_det'])!=(.0136,.005):raise ValueError('Wrong active noise')
        if r['fresh_candidate_calls']!=212:raise ValueError('Candidate count changed')
        for c in r['candidates']:
            if not np.isfinite([c[k] for k in METRICS]).all():raise ValueError('Nonfinite candidate quantity')
            gh=max(gh,c['MI_GH64_128_difference']);labels[c['source_evidence_class']]+=1
        records[point['point_id']]=r
        global_by_group[point['point_id']]=max(r['candidates'],key=lambda c:c['K_raw'])
    families=Counter();parameters=Counter()
    for row in rows:
        if (float(row['xi_ch']),float(row['xi_det']))!=(.0136,.005) or row['source_evidence_promoted']!='False':
            raise ValueError('CSV noise/evidence metadata mismatch')
        r=records[row['group_id']]
        if float(row['zenith_deg']).hex()!=float(r['point']['zenith_deg']).hex():raise ValueError('Non-identical grouped native angle')
        for family in ('MB','Uniform'):
            check=compare_winner(r['winners'][family],_winner_from_csv(row,family))
            if not check['passed'] or max(check['absolute_deviation'].values())!=0.:raise ValueError('Map/winner reconstruction changed')
            if row[family+'_source_evidence_class']!=r['winners'][family]['source_evidence_class']:raise ValueError('Spatial evidence changed')
        if float(row['skr_bits_per_use'])!=float(row['MB_K_raw']) or float(row['K_raw_bits_per_use'])!=float(row['MB_K_raw']):raise ValueError('Signed raw MB alias mismatch')
        if float(row['K_potential_bits_per_use'])!=max(0.,float(row['MB_K_raw'])):raise ValueError('Raw/potential policy mismatch')
        winner=global_by_group[row['group_id']];families[winner['family']]+=1
        parameters[(winner['family'],winner['VA'],winner['nu_raw'])]+=1
    with np.load(directory/'skr_map.npz',allow_pickle=False) as data:
        np.testing.assert_array_equal(data['points'],np.array([[float(r['x_m']),float(r['y_m'])] for r in rows]))
        np.testing.assert_array_equal(data['rates'],np.array([float(r['skr_bits_per_use']) for r in rows]))
        check_npz_metadata(data,manifest,sha(directory/'input_manifest.json'),sha(directory/'executed_producer_snapshot.py'),rows)
    pilot,pilot_config,pilot_manifest=load_verified_pilot(ROOT/'results/phase5c_skr_noise_pilot_20261107')
    if pilot_config['physical']!=manifest['physical'] or pilot_config['effective_protocols']['target']!=next(iter(records.values()))['active_effective_protocol']:
        raise ValueError('Pilot/full physical or active noise protocol mismatch')
    for name,h in pilot_manifest['producers'].items():
        if Path(name).resolve().is_relative_to(b.PARENT) and sha(name)!=h:raise ValueError('Pilot numerical producer changed')
    if sha(LOOKUP/'source_pool.csv')!=manifest['candidate_pool_sha256']:raise ValueError('Pilot/full catalog mismatch')
    by_xy={(float(r['x_m']),float(r['y_m'])):r for r in rows}
    pilot_checks=[]
    for row in pilot['comparisons']:
        q=row['point'];check=compare_winner(_winner_from_csv(by_xy[(q['x_m'],q['y_m'])],'MB'),row['target'])
        pilot_checks.append(dict(point_id=q['point_id'],x_m=q['x_m'],y_m=q['y_m'],**check))
    if not all(c['passed'] for c in pilot_checks):raise ValueError('Phase5C target pilot mismatch')
    rates=np.array([float(r['MB_K_raw']) for r in rows])
    loader_checks={}
    for extension in ('csv','npz'):
        table=SKRLookup.load(directory/('skr_map.'+extension),coordinate_units='m',rate_units='bits/use')
        np.testing.assert_array_equal(table.points,np.array([[float(r['x_m']),float(r['y_m'])] for r in rows]))
        np.testing.assert_array_equal(table.rates,rates)
        np.testing.assert_allclose(table(table.points),rates,rtol=1e-12,atol=1e-14)
        loader_checks[extension]='CURRENTLY_VERIFIED_PASS_NUMERIC_API_ONLY'
    result=dict(status='CURRENTLY_VERIFIED_PASS',spatial_positions=2601,unique_geometries=294,
        full_search_candidate_evaluations=sum(r['fresh_candidate_calls'] for r in records.values()),
        candidates_per_geometry=212,MB_candidates=179,Uniform_candidates=33,
        MB_raw_bits_per_use=dict(min=float(rates.min()),mean=float(rates.mean()),max=float(rates.max())),
        negative_MB_positions=int(np.sum(rates<0)),zero_MB_positions=int(np.sum(rates==0)),
        overall_family_winner_positions={f:families[f] for f in ('MB','Uniform')},overall_family_winner_definition='Compare all212 candidates in original order, signed K; primary map still preserves original separate MB/Uniform policy',
        overall_winner_by_geometry={g:{k:c[k] for k in ('family','VA','nu_raw','K_raw','ensemble_hash','source_evidence_class')} for g,c in global_by_group.items()},
        winning_parameters=[dict(family=f,VA=va,nu_raw=nu,spatial_positions=n) for (f,va,nu),n in sorted(parameters.items())],
        source_evidence_labels=dict(labels),max_GH64_128_difference=gh,pilot_checks=pilot_checks,
        numeric_loader_round_trip=loader_checks,
        output_hash_checks=len(seal),input_hash_checks=len(manifest['input_sha256']),producer_hash_checks=len(manifest['producer_sha256']),
        resource=summary['resource'],initialization=summary['initialization'],paper_mode='NOT_RUN',paper_admissible=False)
    return result,rows,manifest


def run_validation(directory):
    directory=Path(directory).resolve();result,rows,manifest=validate_full_data(directory)
    out=directory/'phase5e_validation'
    if out.exists():raise FileExistsError('Use a fresh separately named validation attempt; never overwrite validation')
    out.mkdir();setup=load_config(ROOT/'configs/channel/optimized_physical_setup.yaml');points=direct_positions(setup)
    config=dict(scope='PHASE5E_INDEPENDENT_ORIGINAL_POSITION_DIRECT_RECOMPUTATION',points=points,
        original_full_input_manifest_sha256=sha(directory/'input_manifest.json'),validation_producer_sha256=sha(__file__),
        native_executor_sha256=sha(ROOT/'src/uav_qkd/lookup_benchmark.py'),active_noise=dict(xi_ch=.0136,xi_det=.005),
        position_to_angle='waypoint_geometry HAP(1000,1000,20000),UAV(qx,qy,1000); no group mapping read to produce angle',
        atol=2e-10,rtol=0.,paper_admissible=False,security_valid=False)
    b._write_new(out/'direct_config.json',config)
    init,init_resource=b._measured(b._init_engine)
    direct,resource=b._run_stage(out,points,'independent_direct',sha(out/'direct_config.json'),
        sha(directory/'input_manifest.json'),manifest,workers=2)
    by_xy={(float(r['x_m']),float(r['y_m'])):r for r in rows};checks=[]
    for r in direct:
        p=r['point'];expected=by_xy[(p['x_m'],p['y_m'])]
        for family in ('MB','Uniform'):
            checks.append(dict(point_id=p['point_id'],x_m=p['x_m'],y_m=p['y_m'],family=family,
                independently_derived_zenith_deg=p['zenith_deg'],lookup_zenith_deg=float(expected['zenith_deg']),
                **compare_winner(r['winners'][family],_winner_from_csv(expected,family))))
    if not all(c['passed'] for c in checks):raise ValueError('Independent direct geometry recomputation differs; do not relax tolerance')
    result.update(independent_original_positions=len(points),independent_candidate_evaluations=resource['fresh_evaluator_calls'],
        independent_checks=checks,independent_resource=resource,independent_initialization=dict(native=init,resource=init_resource),
        technical_integration_status='READY_FOR_MATCHED_CONTEXT_NUMERICAL_SOLVER_INTEGRATION_ONLY',
        integration_limits='Clear-sky static rate input only; no cloud approval, no mission/paper/security admissibility promotion')
    b._write_new(out/'validation_summary.json',result)
    analysis=[]
    for r in rows:
        winner=result['overall_winner_by_geometry'][r['group_id']];f=winner['family']
        analysis.append(dict(x_m=r['x_m'],y_m=r['y_m'],group_id=r['group_id'],overall_winning_family=f,
            selected_raw_bits_per_use=winner['K_raw'],selected_VA=winner['VA'],selected_nu_raw=winner['nu_raw'],
            source_evidence_class=r[f+'_source_evidence_class'],paper_admissible=False))
    with (out/'spatial_winner_analysis.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(analysis[0]));writer.writeheader();writer.writerows(analysis)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--lookup',required=True)
    args=parser.parse_args();r=run_validation(args.lookup)
    print({k:r[k] for k in ('status','spatial_positions','unique_geometries','full_search_candidate_evaluations','independent_candidate_evaluations')})
