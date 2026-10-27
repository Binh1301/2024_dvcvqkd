"""New position-dependent v43 rate evaluations, historical C,w only."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
PRIOR=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024'
sys.path.insert(0,str(ROOT))
from src.uav_mobility import candidate_grid,link_geometry
spec=importlib.util.spec_from_file_location('_historical_v43_source_helpers',PRIOR/'sweep.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
PASS='CURRENTLY_VERIFIED_PASS'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(name,value):
    (OUT/name).parent.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes((json.dumps(old.clean(value),indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def write(name,records):
    fields=list(dict.fromkeys(k for r in records for k in r))
    (OUT/name).parent.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(old.clean(records))
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def run(geometry):
    config=read(OUT/'experiment_config.json')
    if geometry not in config['geometry_cases']:raise ValueError('Geometry is not explicitly approved')
    if (OUT/f'clear_sky_map_{geometry}.csv').exists():raise FileExistsError('Preserve completed geometry map')
    task=read(PRIOR/'protocol.json');physical=read(ROOT/task['physical_protocol_path'])
    assert sha(ROOT/task['physical_protocol_path'])==task['physical_protocol_sha256']
    old.canonical.validate_protocol(physical)
    sources=list(old.source_pool(physical));assert len(sources)==212
    source_map={s['ensemble_hash']:s for s in sources}
    g=config['geometry_cases'][geometry]
    positions=candidate_grid(1000.,10)
    distances,angles=link_geometry(positions,g['hap_horizontal_m'],20000.,1000.)
    candidates_saved=old.numeric(rows(PRIOR/'diagnostic_skr_61_angles.csv'))
    cached={}
    for r in candidates_saved:cached.setdefault(float(r['zenith_deg']).hex(),[]).append(r)
    groups={};position_rows=[]
    for j,(point,distance,angle) in enumerate(zip(positions,distances,angles)):
        angle_deg=float(np.degrees(angle));angle_hex=angle_deg.hex()
        identity=hashlib.sha256((angle_hex+task['physical_protocol_sha256']+sha(PRIOR/'source_pool.csv')).encode()).hexdigest()[:20]
        groups.setdefault(identity,dict(zenith_deg=angle_deg,zenith_hex=angle_hex))
        position_rows.append(dict(position_index=j,j=j+1,row=j//10,column=j%10,x_m=float(point[0]),
            y_m=float(point[1]),z_m=1000.,horizontal_m=float(np.linalg.norm(point-g['hap_horizontal_m'])),
            link_distance_m=float(distance),zenith_deg=angle_deg,zenith_hex=angle_hex,geometry_id=identity))
    write(f'positions_{geometry}.csv',position_rows)
    began=time.perf_counter();new_count=reused_count=0;selected={};independent=[]
    for identity,angle in groups.items():
        target=OUT/f'physical_records/{identity}.csv'
        if target.exists():
            data=old.numeric(rows(target));context=read(OUT/f'physical_records/{identity}_context.json')
            reused_count+=len(data)
        elif angle['zenith_hex'] in cached:
            data=cached[angle['zenith_hex']]
            assert len(data)==212
            context=old.canonical.channel_context(angle['zenith_deg'],physical)
            save(f'physical_records/{identity}_context.json',context)
            write(f'physical_records/{identity}.csv',data);reused_count+=len(data)
        else:
            context=old.canonical.channel_context(angle['zenith_deg'],physical)
            assert abs(context['channel']['L_km']*1000-19000/np.cos(np.deg2rad(angle['zenith_deg'])))<1e-8
            save(f'physical_records/{identity}_context.json',context)
            data=[]
            for source in sources:
                record={k:source[k] for k in ['family','VA','VA_hex','nu_raw','nu_raw_hex','nu_repo',
                    'C','w','C_hex','w_hex','ensemble_hash','source_path','source_sha256','canonical_source_identity']}
                record.update(result_scope='DIAGNOSTIC_ONLY',zenith_deg=angle['zenith_deg'],
                    zenith_hex=angle['zenith_hex'],source_evidence_class=source['classification'],
                    correlation_policy='manuscript_eq14_direct',Cw_reused=True,source_Cw_recomputed=False,
                    channel_protocol_sha256=task['physical_protocol_sha256'])
                try:
                    result=old.evaluator.evaluate(source,context,physical);decimals=result.pop('decimal')
                    record.update(result,numerical_status=PASS,reason='')
                    record.update({'decimal_'+k:v for k,v in decimals.items()})
                except ValueError as error:
                    record.update(numerical_status='FAILED_NUMERICAL_VALIDATION',reason=str(error),K_raw=None)
                data.append(record)
            write(f'physical_records/{identity}.csv',data);new_count+=len(data)
        valid=[r for r in data if r['numerical_status']==PASS]
        if len(valid)!=212:raise ValueError('Incomplete geometry evaluation; failed rows retained: '+identity)
        winner=max(valid,key=lambda r:float(r['K_raw']))
        selected[identity]=winner
        source=source_map[winner['ensemble_hash']]
        p,alpha=source['p'],source['alpha']
        mi,error=old.canonical.prior_model.helpers().independent_mi(p,alpha,float(winner['eta_f']),1+float(winner['N_effective']))
        delta=abs(mi-float(winner['I_AB']));assert delta<=2e-10
        independent.append(dict(geometry_id=identity,zenith_deg=angle['zenith_deg'],ensemble_hash=source['ensemble_hash'],
            adaptive_MI_difference=delta,adaptive_error_estimate=error,status=PASS))
        print(json.dumps(dict(geometry=geometry,angle=angle['zenith_deg'],evaluated=212,best_raw_K=winner['K_raw'])),flush=True)
    output=[]
    for position in position_rows:
        winner=selected[position['geometry_id']]
        output.append({**position,**{k:winner[k] for k in ['VA','nu_raw','C','w','ensemble_hash',
            'source_path','source_sha256','source_evidence_class','eta_f','xi_f','I_AB','beta_I_AB','chi_BE','K_raw']},
            'K_star':max(0.,float(winner['K_raw'])),'result_scope':'DIAGNOSTIC_ONLY'})
    write(f'clear_sky_map_{geometry}.csv',output)
    write(f'physical_independent_checks_{geometry}.csv',independent)
    save(f'physical_summary_{geometry}.json',dict(geometry=geometry,positions=100,unique_channel_geometries=len(groups),
        historical_sources_reused=212,new_Cw_computations=0,new_SKR_evaluations=new_count,
        reused_SKR_evaluations=reused_count,channel_protocol_sha256=task['physical_protocol_sha256'],
        source_pool_sha256=sha(PRIOR/'source_pool.csv'),new_angle_range_deg=[min(r['zenith_deg'] for r in output),max(r['zenith_deg'] for r in output)],
        raw_K_range=[min(float(r['K_raw']) for r in output),max(float(r['K_raw']) for r in output)],
        positive_clear_sky_positions=sum(r['K_star']>0 for r in output),numerical_status=PASS,
        elapsed_seconds=time.perf_counter()-began))


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Specify an explicitly approved geometry case')
    run(sys.argv[1])
