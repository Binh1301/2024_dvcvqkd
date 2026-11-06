"""Fresh receiver30 catalog SKR evaluations; no interpolation or new C,w."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
PRIOR=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024'
PASS='CURRENTLY_VERIFIED_PASS'


def angle_samples():
    last=math.degrees(math.acos(19/22))
    return [float(a) for a in range(math.floor(last)+1)]+[last]


def geometry_groups(rows):
    groups={}
    for i,row in enumerate(rows):
        radius2=(float(row['x_m'])-1000)**2+(float(row['y_m'])-1000)**2
        group=groups.setdefault(radius2,dict(angle=float(row['zenith_deg']),indices=[]))
        if abs(float(row['zenith_deg'])-group['angle'])>1e-12:
            raise ValueError('Equal-radius grid geometry mismatch')
        group['indices'].append(i)
    return groups


def select_family(rows,family):
    candidates=[r for r in rows if r['family']==family]
    if not candidates or any(r['numerical_status']!=PASS for r in candidates):
        return None
    return max(candidates,key=lambda r:r['K_raw'])


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write(name,records):
    fields=list(dict.fromkeys(k for row in records for k in row))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)


def helpers():
    spec=importlib.util.spec_from_file_location('_receiver30_existing_sweep',PRIOR/'sweep.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def dependency_status(raw,expected):
    if hashlib.sha256(raw).hexdigest()==expected:return 'IDENTICAL'
    lf=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
    if expected in {hashlib.sha256(lf).hexdigest(),hashlib.sha256(lf.replace(b'\n',b'\r\n')).hexdigest()}:
        return 'VERIFIED_NEWLINE_EQUIVALENT'
    return 'CHANGED'


def bind_execution_protocol(physical):
    # Two unused validation entry points changed after the historical snapshot.
    # Bind this run to current bytes; never accept changed scientific producers.
    unused={'scripts/validate_fock_convergence.py','scripts/validate_holevo_threshold_sensitivity.py'}
    audit=[];dependencies={}
    for name,expected in physical['dependency_sha256'].items():
        path=ROOT/name;raw=path.read_bytes();status=dependency_status(raw,expected)
        if status=='CHANGED':
            if name not in unused:raise ValueError('Scientific dependency differs: '+name)
            if any(getattr(m,'__file__',None) and Path(m.__file__).resolve()==path.resolve() for m in list(sys.modules.values())):
                raise ValueError('Changed validation entry point unexpectedly imported: '+name)
            status='UNUSED_VALIDATION_ENTRY_CURRENT_BYTES_BOUND'
        digest=hashlib.sha256(raw).hexdigest();dependencies[name]=digest
        audit.append(dict(path=name,historical_sha256=expected,current_sha256=digest,status=status))
    bound={**physical,'dependency_sha256':dependencies}
    for path_key,hash_key in [('experiment_spec_path','experiment_spec_sha256'),('frozen_history_path','frozen_history_sha256')]:
        path=ROOT/physical[path_key]
        if dependency_status(path.read_bytes(),physical[hash_key])=='CHANGED':
            raise ValueError('Experimental metadata content changed: '+path_key)
        bound[hash_key]=sha(path)
    spec=read(ROOT/physical['experiment_spec_path'])
    frozen=spec['historical_spec'];raw=(ROOT/frozen['path']).read_bytes()
    lf=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
    if hashlib.sha256(lf).hexdigest()!=frozen['sha256']:
        raise ValueError('Historical frozen specification cannot be reconstructed exactly')
    (OUT/'historical_frozen_spec_exact.md').write_bytes(lf)
    spec['historical_spec']={**frozen,'path':(OUT/'historical_frozen_spec_exact.md').relative_to(ROOT).as_posix()}
    save('execution_experiment_spec.json',spec)
    bound['experiment_spec_path']=(OUT/'execution_experiment_spec.json').relative_to(ROOT).as_posix()
    bound['experiment_spec_sha256']=sha(OUT/'execution_experiment_spec.json')
    save('execution_dependency_binding.json',dict(policy='NEW_TASK_CURRENT_BYTE_BINDING_WITH_UNCHANGED_SCIENTIFIC_IMPLEMENTATION',
        dependencies=audit,original_files_modified=False))
    save('execution_physical_protocol.json',bound)
    return bound


def current_sources(old,physical):
    pool=[];binding=[];domain=physical['source_domain']
    for row in rows(old.BASE/'exact_source_inventory.csv'):
        if not domain['VA'][0]<=float(row['VA'])<=domain['VA'][1] or not domain['nu_raw'][0]<=float(row['nu_raw'])<=domain['nu_raw'][1]:
            continue
        path=ROOT/row['source_path'];status=dependency_status(path.read_bytes(),row['source_sha256'])
        if status=='CHANGED':raise ValueError('Source payload content changed: '+row['source_path'])
        if row['compatibility_status']!=PASS or row['source_evidence_class'] not in old.STRICT|{'INSUFFICIENT_EVIDENCE'}:
            raise ValueError('Incompatible source inventory')
        source=dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),
                    C=float(row['C']),w=float(row['w']),classification=row['source_evidence_class'],source_sha256=sha(path))
        old.historical.verify_source_payload(read(path),json.loads(row['source_settings_json']))
        if source['C'].hex()!=row['C_hex'] or source['w'].hex()!=row['w_hex']:
            raise ValueError('Source moment bit identity mismatch')
        source=old.historical.with_ensemble(source)
        old.canonical.prior_model.helpers().validate_source(source)
        if old.historical.input_digests(source)!=json.loads(row['input_digests_json']):
            raise ValueError('Source p/alpha input digest mismatch')
        binding.append(dict(path=row['source_path'],historical_sha256=row['source_sha256'],current_sha256=source['source_sha256'],status=status))
        pool.append(source)
    if len(pool)!=212:raise ValueError('Expected unchanged 212-source catalog')
    save('source_payload_binding.json',binding)
    return pool


def execute():
    if (OUT/'summary.json').exists():raise FileExistsError('Completed results are immutable')
    old=helpers();physical=read(ROOT/read(PRIOR/'protocol.json')['physical_protocol_path'])
    physical=bind_execution_protocol(physical)
    old.canonical.validate_protocol(physical)
    sources=current_sources(old,physical)
    assert len(sources)==212
    input_grid=ROOT/'results/skr_lookup_readiness_20261105/geometry_only.csv'
    grid=rows(input_grid);assert len(grid)==2601
    groups=geometry_groups(grid)
    angles=angle_samples()
    producer_files=[Path(__file__),PRIOR/'sweep.py',old.BASE/'diagnostic_model.py',
                    old.BASE/'inventory.py',old.historical.PRIOR/'model.py',
                    OUT/'execution_physical_protocol.json',OUT/'execution_experiment_spec.json',
                    ROOT/read(PRIOR/'protocol.json')['physical_protocol_path']]
    identity=dict(producers={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in producer_files},
                  geometry_sha256=sha(input_grid),source_hashes={s['source_path']:s['source_sha256'] for s in sources})
    if (OUT/'execution_identity.json').exists():
        if read(OUT/'execution_identity.json')!=identity:raise ValueError('Resume identity changed')
    else:
        save('execution_identity.json',identity)
        save('authorization.json',dict(date='2026-11-06',user_request='Proceed directly with numerical zenith sweep and 51x51 heatmap',
            scope='Existing receiver30 diagnostic evaluator; preserve original assumptions and source evidence; no new C,w',
            physical=physical['physical'],xi_ch=physical['xi_ch'],xi_det=physical['xi_det'],beta=physical['beta'],
            source_domain=physical['source_domain'],correlation_policy=physical['correlation_policy'],
            truncation_policy=physical['truncation_policy'],source_count=len(sources),
            source_evidence_promoted=False,publication_or_security_certification=False,
            zenith_angles_deg=angles,grid_shape=[51,51],unique_map_geometries=len(groups)))
        write('source_pool.csv',[{k:v for k,v in s.items() if k not in ('p','alpha')} for s in sources])
    (OUT/'contexts').mkdir(exist_ok=True)
    evaluated={};new_count=0;failures=[];began=time.perf_counter()

    # Two mandatory fresh benchmark calls, independently of catalog ranking.
    if not (OUT/'benchmark_recheck.json').exists():
        source=next(s for s in sources if s['nu_raw']==.3 and s['VA']==1.358333319784304)
        saved=rows(old.BASE/'diagnostic_selected_schemes.csv');bench=[]
        for angle in (0.,30.):
            context=old.canonical.channel_context(angle,physical)
            actual=old.evaluator.evaluate(source,context,physical)
            target=next(r for r in saved if float(r['zenith_deg'])==angle and r['scheme']=='Optimized MB-shaped 256-QAM')
            delta={k:actual[k]-float(target[k]) for k in ('I_AB','chi_BE','K_raw')}
            if max(abs(v) for v in delta.values())>2e-10:raise ValueError('Benchmark mismatch: '+str(delta))
            bench.append(dict(zenith_deg=angle,VA=source['VA'],nu_raw=source['nu_raw'],
                calculated={k:actual[k] for k in ('I_AB','beta_I_AB','chi_BE','K_raw')},
                absolute_deviation={k:abs(v) for k,v in delta.items()},
                relative_deviation={k:abs(v/float(target[k])) for k,v in delta.items()},
                status=PASS,source_evidence_class=source['classification']))
        save('benchmark_recheck.json',bench)
        print('Fresh benchmarks 0 and 30 degrees reproduced',flush=True)

    def evaluate_angle(angle):
        nonlocal new_count
        key=float(angle).hex()
        if key in evaluated:return evaluated[key]
        tag=hashlib.sha256(key.encode()).hexdigest()[:18]
        path=OUT/'contexts'/f'{tag}.json'
        if path.exists():
            result=read(path)
            if result['angle_hex']!=key or result['execution_identity_sha256']!=sha(OUT/'execution_identity.json'):
                raise ValueError('Cached context identity mismatch')
            evaluated[key]=result;return result
        context=old.canonical.channel_context(angle,physical)
        data=[]
        for source in sources:
            row={k:source[k] for k in ('family','VA','nu_raw','C','w','ensemble_hash','source_path','source_sha256')}
            row['source_evidence_class']=source['classification']
            try:
                value=old.evaluator.evaluate(source,context,physical)
                row.update({k:v for k,v in value.items() if k!='decimal'},numerical_status=PASS)
            except ValueError as error:
                row.update(numerical_status='FAILED_NUMERICAL_VALIDATION',error=str(error),K_raw=None)
                failures.append(dict(zenith_deg=angle,ensemble_hash=source['ensemble_hash'],error=str(error)))
            data.append(row);new_count+=1
        write(f'contexts/{tag}_candidates.csv',data)
        winners={family:select_family(data,family) for family in ('Uniform','MB')}
        result=dict(angle_hex=key,zenith_deg=angle,distance_m=19000/math.cos(math.radians(angle)),
                    moments=context['moments'],probability_deficit=context['probability_deficit'],
                    winners=winners,execution_identity_sha256=sha(OUT/'execution_identity.json'))
        save(f'contexts/{tag}.json',result);evaluated[key]=result
        save('checkpoint.json',dict(completed_contexts=len(list((OUT/'contexts').glob('*.json'))),
            current_angle_deg=angle,new_evaluations_this_process=new_count,elapsed_s=time.perf_counter()-began))
        print(json.dumps(dict(angle_deg=angle,contexts=len(evaluated),MB_K=winners['MB']['K_raw'] if winners['MB'] else None,
                              elapsed_s=round(time.perf_counter()-began,1))),flush=True)
        return result

    sweep=[]
    for angle in angles:
        context=evaluate_angle(angle)
        for family,winner in context['winners'].items():
            sweep.append(dict(zenith_deg=angle,distance_m=context['distance_m'],scheme=family,
                nu_raw=winner['nu_raw'] if winner else None,VA=winner['VA'] if winner else None,
                I_AB=winner['I_AB'] if winner else None,chi_BE=winner['chi_BE'] if winner else None,
                K_raw_bits_per_use=winner['K_raw'] if winner else None,
                numerical_status=PASS if winner else 'FAILED_NUMERICAL_VALIDATION',
                source_evidence_class=winner['source_evidence_class'] if winner else None))
    write('skr_vs_zenith.csv',sweep)
    position_results={}
    for radius2,group in sorted(groups.items()):
        context=evaluate_angle(group['angle'])
        for i in group['indices']:position_results[i]=context
    map_rows=[]
    for i,point in enumerate(grid):
        context=position_results[i]
        if abs(float(point['distance_m'])-context['distance_m'])>1e-7:raise ValueError('Grid distance mismatch')
        record={k:float(point[k]) for k in ('x_m','y_m','distance_m','zenith_deg')}
        record.update(mean_eta=context['moments']['m1'],eta_f=context['moments']['mh']**2,
                      context_angle_hex=context['angle_hex'])
        for family,winner in context['winners'].items():
            prefix='MB' if family=='MB' else 'Uniform'
            record.update({prefix+'_'+k:(winner[k] if winner else None) for k in
                           ('K_raw','I_AB','chi_BE','VA','nu_raw','source_evidence_class','ensemble_hash')})
            record[prefix+'_numerical_status']=PASS if winner else 'FAILED_NUMERICAL_VALIDATION'
        record['K_raw_bits_per_use']=record['MB_K_raw']
        record['K_potential_bits_per_use']=max(0.,record['MB_K_raw']) if record['MB_K_raw'] is not None else None
        map_rows.append(record)
    write('skr_map.csv',map_rows)
    import numpy as np
    def array(key):return np.array([r[key] if r[key] is not None else np.nan for r in map_rows],dtype=float).reshape(51,51)
    np.savez_compressed(OUT/'skr_map.npz',x_m=array('x_m'),y_m=array('y_m'),distance_m=array('distance_m'),
        zenith_deg=array('zenith_deg'),mean_eta=array('mean_eta'),eta_f=array('eta_f'),nu_opt=array('MB_nu_raw'),
        VA_opt=array('MB_VA'),IAB_opt=array('MB_I_AB'),chiBE_opt=array('MB_chi_BE'),
        K_raw_bits_per_use=array('K_raw_bits_per_use'),K_potential_bits_per_use=array('K_potential_bits_per_use'),
        K_raw_uniform_bits_per_use=array('Uniform_K_raw'),
        numerical_status=np.array([r['MB_numerical_status'] for r in map_rows]).reshape(51,51))
    values=array('K_raw_bits_per_use')
    summary=dict(result_scope='EXISTING_RECEIVER30_FINITE_CATALOG_NUMERICAL_OBJECTIVE',
        modulation_selection='best-tested signed raw K in 179 MB and 33 Uniform sources, not a continuous optimum',
        zenith_samples=len(angles),max_zenith_deg=angles[-1],max_slant_distance_m=22000.,
        map_points=len(grid),unique_map_geometries=len(groups),total_unique_contexts=len(evaluated),
        catalog_candidates_per_context=len(sources),new_evaluations_this_process=new_count,
        min_map_MB_K=float(np.nanmin(values)),max_map_MB_K=float(np.nanmax(values)),center_map_MB_K=float(values[25,25]),
        map_numerical_failures=int(np.isnan(values).sum()),new_Cw=0,interpolation_used=False,
        source_evidence_classes_preserved=True,security_valid=False,elapsed_s=time.perf_counter()-began)
    save('evaluation_errors.json',failures);save('summary.json',summary)
    plot(sweep,map_rows)
    print(json.dumps(summary,indent=2),flush=True)


def plot(sweep,map_rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.labelsize':11,
                         'savefig.facecolor':'white','figure.facecolor':'white'})
    fig,ax=plt.subplots(figsize=(6.1,4.0))
    for family,color in [('Uniform','#2864a0'),('MB','#b54c2f')]:
        data=[r for r in sweep if r['scheme']==family]
        ax.plot([r['zenith_deg'] for r in data],[r['K_raw_bits_per_use'] if r['K_raw_bits_per_use'] is not None else np.nan for r in data],
                label=family+' (best-tested catalog)',color=color,lw=1.7)
    ax.axhline(0,color='0.5',lw=.6);ax.set(xlabel='Zenith angle (degrees)',ylabel='SKR (bits/use)',xlim=(0,angle_samples()[-1]))
    ax.legend(fontsize=9);ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0),useMathText=True)
    ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'skr_vs_zenith.png',dpi=300);plt.close(fig)
    x=np.array([r['x_m'] for r in map_rows]).reshape(51,51)/1000
    y=np.array([r['y_m'] for r in map_rows]).reshape(51,51)/1000
    z=np.array([r['K_raw_bits_per_use'] if r['K_raw_bits_per_use'] is not None else np.nan for r in map_rows]).reshape(51,51)
    fig,ax=plt.subplots(figsize=(5.5,4.5))
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('0.75')
    image=ax.pcolormesh(x,y,np.ma.masked_invalid(z),shading='nearest',cmap=cmap,vmin=min(0.,float(np.nanmin(z))),vmax=float(np.nanmax(z)))
    ax.plot(1,1,'x',color='black',ms=7,mew=1.4,label='HAP projection / center')
    ax.set(xlabel='UAV horizontal X (km)',ylabel='UAV horizontal Y (km)',xlim=(0,2),ylim=(0,2),aspect='equal')
    ax.legend(loc='upper right',fontsize=8,framealpha=.85)
    cbar=fig.colorbar(image,ax=ax,pad=.035);cbar.set_label('MB SKR (bits/use)')
    cbar.formatter.set_powerlimits((0,0));cbar.update_ticks()
    fig.tight_layout();fig.savefig(OUT/'skr_heatmap.png',dpi=300);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true',required=True)
    parser.parse_args()
    try:execute()
    except Exception as error:
        save('execution_failure.json',dict(error_type=type(error).__name__,error=str(error)))
        raise
