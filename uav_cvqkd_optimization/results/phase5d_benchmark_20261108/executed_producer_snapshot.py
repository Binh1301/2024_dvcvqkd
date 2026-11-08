"""Phase5D full-search benchmark and separately gated full-lookup executor.

Benchmark only: python -B -m uav_qkd.lookup_benchmark benchmark --output results/phase5d_benchmark_20261108
Full requires a separate, explicit author approval file bound to config/pool.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import threading
import time
import numpy as np
import psutil
from .config import load_config
from .phase5b_audit import audit_lookup_noise
from .skr_lookup import compare_lookup_setup
from .skr_pilot import (ROOT,PARENT,LOOKUP,read,read_rows,sha,effective_protocol,
                        compare_candidate,repository_producers,verify_historical_file,validate_checkpoint)

_ENGINE=None


def benchmark_points(rows,count=50):
    if isinstance(count,bool) or not isinstance(count,int) or not 50<=count<=100:
        raise ValueError('Bounded benchmark requires 50..100 spatial points')
    groups={}
    for row in rows:
        x,y=float(row['x_m']),float(row['y_m']);r2=(x-1000)**2+(y-1000)**2
        groups.setdefault(r2,dict(x_m=x,y_m=y,radius2_m2=r2,zenith_deg=float(row['zenith_deg']),distance_m=float(row['distance_m'])))
    ordered=[groups[k] for k in sorted(groups)]
    return [dict(ordered[int(i)],point_id=f'b{n:03d}') for n,i in enumerate(np.linspace(0,len(ordered)-1,count,dtype=int))]


def require_full_approval(approval,config_hash,pool_hash):
    if approval is None:raise ValueError('Full regeneration requires separate explicit author approval')
    a=read(approval)
    if (a.get('author_approved') is not True or a.get('scope')!='PHASE5D_FULL_LOOKUP'
            or a.get('config_sha256')!=config_hash or a.get('candidate_pool_sha256')!=pool_hash):
        raise ValueError('Full approval must bind exact scope, config and candidate pool')


def full_configuration(geometry_mode='per_point'):
    if geometry_mode not in ('per_point','radial_exact'):raise ValueError('Unknown geometry mode')
    return dict(mode='FULL_TARGET_LOOKUP',geometry_mode=geometry_mode,xi_ch=.0136,xi_det=.005,
        candidates_per_context=212,MB_candidates=179,Uniform_candidates=33,
        candidate_pool_sha256=sha(LOOKUP/'source_pool.csv'),
        original_protocol_sha256=sha(LOOKUP/'execution_physical_protocol.json'),
        optimized_setup_sha256=sha(ROOT/'configs/channel/optimized_physical_setup.yaml'),
        geometry_source_sha256=sha(LOOKUP/'skr_map.csv'),
        numerical_tolerances='native GH64/128 2e-10; native 80/110 digits 2e-11; scalar/identity checkpoint validation',
        coordinate_units='m',rate_units='bits/use',selection='full per-family signed-K argmax; first tie retained',
        requires_explicit_separate_approval=True,source_evidence_promoted=False,paper_mode='NOT_RUN')


def compare_modes(serial,parallel):
    if len(serial)!=len(parallel):return dict(passed=False,reason='Point count mismatch')
    checks=[]
    for a,b in zip(serial,parallel):
        if a['point']!=b['point'] or len(a['candidates'])!=len(b['candidates']):return dict(passed=False,reason='Point/roster mismatch')
        rows=[compare_candidate(x,y) for x,y in zip(a['candidates'],b['candidates'])]
        winners=(set(a['winners'])==set(b['winners']) and all(a['winners'][f]['ensemble_hash']==b['winners'][f]['ensemble_hash'] for f in a['winners']))
        checks.append(dict(point_id=a['point']['point_id'],passed=bool(all(c['passed'] for c in rows) and winners),
                           max_deviation={k:max(c['absolute_deviation'][k] for c in rows) for k in ('eta_f','xi_f','I_AB','chi_BE','K_raw')}))
    return dict(passed=all(c['passed'] for c in checks),checks=checks)


def _write_new(path,data):
    path=Path(path)
    if path.exists():raise FileExistsError('Immutable artifact exists: '+str(path))
    temporary=path.with_name(path.name+'.partial')
    with temporary.open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)
        f.flush();os.fsync(f.fileno())
    temporary.replace(path)


def _output_directory(path,*,resume=False):
    path=Path(path).resolve()
    if not path.is_relative_to((ROOT/'results').resolve()) or not path.name.startswith('phase5d_'):
        raise ValueError('Use a new phase5d_ namespace in this package results directory')
    if (path/'summary.json').exists():raise FileExistsError('Completed result is immutable')
    if path.exists() and any(path.iterdir()) and (not resume or not (path/'config.json').exists()):
        raise FileExistsError('Only matching owned input manifests may be resumed')
    path.mkdir(parents=True,exist_ok=True)
    return path


def _init_engine():
    global _ENGINE
    began=time.perf_counter()
    spec=importlib.util.spec_from_file_location('_phase5d_original_producer',LOOKUP/'run.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);old=native.helpers()
    original=read(LOOKUP/'execution_physical_protocol.json');pool=[]
    for r in read_rows(LOOKUP/'source_pool.csv'):
        path=PARENT/r['source_path']
        if sha(path)!=r['source_sha256']:raise ValueError('Native source payload changed')
        s=dict(r,VA=float.fromhex(r['VA_hex']),nu_raw=float.fromhex(r['nu_raw_hex']),
               C=float.fromhex(r['C_hex']),w=float.fromhex(r['w_hex']),classification=r['source_evidence_class'])
        old.historical.verify_source_payload(read(path),json.loads(r['source_settings_json']))
        s=old.historical.with_ensemble(s)
        if old.historical.input_digests(s)!=json.loads(r['input_digests_json']):raise ValueError('Native source vector changed')
        pool.append(s)
    if len(pool)!=212 or sum(s['family']=='MB' for s in pool)!=179 or sum(s['family']=='Uniform' for s in pool)!=33:
        raise ValueError('Full 212-source roster is mandatory')
    torch=sys.modules.get('torch')
    info=dict(pid=os.getpid(),initialization_s=time.perf_counter()-began,
              torch_threads=torch.get_num_threads() if torch else None,
              thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    _ENGINE=dict(old=old,original=original,pool=pool,protocol=effective_protocol(original,.0136),info=info)
    return info


def _evaluate_job(job):
    stage,point,config_hash,input_hash=job
    e=_ENGINE;began=time.perf_counter();cpu0=time.process_time()
    context=e['old'].canonical.channel_context(point['zenith_deg'],e['original'])
    context_s=time.perf_counter()-began;tick=time.perf_counter();candidates=[]
    for s in e['pool']:
        value=e['old'].evaluator.evaluate(s,context,e['protocol'])
        candidates.append(dict(family=s['family'],ensemble_hash=s['ensemble_hash'],VA=s['VA'],nu_raw=s['nu_raw'],
            source_path=s['source_path'],source_sha256=s['source_sha256'],source_evidence_class=s['classification'],
            **{k:v for k,v in value.items() if k!='decimal'}))
    winners={f:max((c for c in candidates if c['family']==f),key=lambda c:c['K_raw']) for f in ('MB','Uniform')}
    return e['old'].clean(dict(stage=stage,point=point,trial_config_sha256=config_hash,input_manifest_sha256=input_hash,
        active_effective_protocol=e['protocol'],context=context,candidates=candidates,winners=winners,
        context_s=context_s,evaluator_s=time.perf_counter()-tick,point_wall_s=time.perf_counter()-began,
        point_process_cpu_s=time.process_time()-cpu0,worker_initialization=e['info'],fresh_candidate_calls=212,
        seed=None,security_valid=False,paper_admissible=False))


def _measured(function):
    """50ms sampled aggregate RSS/process CPU, including spawned descendants."""
    process=psutil.Process();baseline=sum(process.cpu_times()[:2]);cpu_max={};rss_peak=0;samples=0
    stop=threading.Event();began=time.perf_counter()
    def sample():
        nonlocal rss_peak,samples
        rss=0
        for child in [process,*process.children(recursive=True)]:
            try:
                rss+=child.memory_info().rss
                cpu=sum(child.cpu_times()[:2])-(baseline if child.pid==process.pid else 0.)
                cpu_max[child.pid]=max(cpu,cpu_max.get(child.pid,0.))
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        rss_peak=max(rss_peak,rss);samples+=1
    def loop():
        while not stop.wait(.05):sample()
    sample();thread=threading.Thread(target=loop,daemon=True);thread.start()
    try:result=function()
    finally:
        sample();stop.set();thread.join()
    wall=time.perf_counter()-began;cpu=sum(cpu_max.values())
    return result,dict(wall_s=wall,sampled_tree_peak_rss_bytes=rss_peak,sampled_process_cpu_s=cpu,
        cpu_percent_one_core=100*cpu/wall,cpu_percent_host_capacity=100*cpu/wall/psutil.cpu_count(),
        sampling_interval_s=.05,sample_count=samples,
        memory_scope='Sampled sum of parent+descendant RSS; shared pages may be counted repeatedly; not exact continuous/system physical peak',
        cpu_scope='Process CPU-time deltas; child lifetime maxima sampled while present; short exited processes can be missed')


def _prepare(output,config,*,resume=False):
    output=_output_directory(output,resume=resume)
    audit=audit_lookup_noise(LOOKUP);original=read(LOOKUP/'execution_physical_protocol.json')
    setup=load_config(ROOT/'configs/channel/optimized_physical_setup.yaml')
    compatible=compare_lookup_setup(setup,original)
    if setup['channel_excess_noise_snu']!=.0136 or compatible['physical_mismatches'] or compatible['noise_mismatches']!=['channel_excess_noise_snu']:
        raise ValueError('Only the unchanged author optics and target noise .0136 are benchmarked')
    config_path=output/'config.json'
    if config_path.exists():
        if read(config_path)!=config:raise ValueError('Resume config mismatch')
    else:_write_new(config_path,config)
    config_hash=sha(config_path)
    info,init_resource=_measured(_init_engine)
    inputs=dict(audit['verified_inputs_and_producers'])
    for path in (LOOKUP/'source_pool.csv',LOOKUP/'skr_map.csv',LOOKUP/'final_manifest.json',ROOT/'configs/channel/optimized_physical_setup.yaml'):
        if path.name in ('source_pool.csv','skr_map.csv'):verify_historical_file(path)
        inputs[str(path)]=sha(path)
    for source in _ENGINE['pool']:inputs[str(PARENT/source['source_path'])]=source['source_sha256']
    manifest=dict(config_sha256=config_hash,candidate_pool_sha256=sha(LOOKUP/'source_pool.csv'),
        input_sha256=inputs,producer_sha256=repository_producers(list(sys.modules.values())),
        roster=[{k:s[k] for k in ('family','ensemble_hash','VA','nu_raw','source_path','source_sha256','classification')} for s in _ENGINE['pool']],
        python=sys.version,platform=platform.platform(),logical_cpus=psutil.cpu_count(),physical_cpus=psutil.cpu_count(logical=False),
        available_ram_before_stages_bytes=psutil.virtual_memory().available,seed=None,
        active_noise=dict(xi_ch=.0136,xi_det=.005),physical=original['physical'],security_valid=False,paper_admissible=False)
    path=output/'input_manifest.json'
    if path.exists():
        # RAM availability is telemetry, not a scientific resume identity.
        previous=read(path)
        manifest['available_ram_before_stages_bytes']=previous['available_ram_before_stages_bytes']
        if previous!=manifest:raise ValueError('Resume input/producer manifest mismatch')
    else:_write_new(path,manifest)
    snap=output/'executed_producer_snapshot.py'
    if snap.exists():
        if sha(snap)!=sha(__file__):raise ValueError('Resume producer snapshot mismatch')
    else:snap.write_bytes(Path(__file__).read_bytes())
    return output,config_hash,sha(path),manifest,dict(native=info,resource=init_resource)


def _run_stage(output,points,stage,config_hash,input_hash,manifest,workers=1):
    directory=output/stage;directory.mkdir(exist_ok=True);records={};jobs=[]
    for point in points:
        path=directory/(point['point_id']+'.json')
        if path.exists():
            if read(path.with_suffix('.seal.json'))['sha256']!=sha(path):raise ValueError('Checkpoint seal mismatch')
            record=read(path);validate_checkpoint(record,stage,point,input_hash,config_hash,_ENGINE['protocol'],manifest['roster']);records[point['point_id']]=record
        else:jobs.append((stage,point,config_hash,input_hash))
    def consume(iterator):
        for record in iterator:
            validate_checkpoint(record,stage,record['point'],input_hash,config_hash,_ENGINE['protocol'],manifest['roster'])
            path=directory/(record['point']['point_id']+'.json')
            _write_new(path,record);_write_new(path.with_suffix('.seal.json'),dict(sha256=sha(path)))
            records[record['point']['point_id']]=record
            if len(records)%10==0 or len(records)==len(points):print(stage,len(records),'/',len(points),flush=True)
    def execute():
        if workers==1:consume(map(_evaluate_job,jobs))
        else:
            with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn'),initializer=_init_engine) as executor:
                consume(executor.map(_evaluate_job,jobs,chunksize=1))
    _,resource=_measured(execute)
    result=[records[p['point_id']] for p in points]
    return result,dict(resource,fresh_evaluator_calls=len(jobs)*212,completed_points=len(result),
                       evaluations_per_second=len(jobs)*212/resource['wall_s'],workers=workers)


def _seal(output):
    _write_new(output/'output_manifest.json',{str(f.relative_to(output)):sha(f) for f in sorted(output.rglob('*')) if f.is_file() and f.name!='output_manifest.json'})


def benchmark(output,*,count=50,workers=2):
    if workers!=2:raise ValueError('This bounded comparison measures serial versus exactly two processes')
    points=benchmark_points(read_rows(LOOKUP/'skr_map.csv'),count)
    config=dict(scope='EXPLICIT_PHASE5D_BOUNDED_RUNTIME_BENCHMARK',points=points,serial_workers=1,parallel_workers=2,
        xi_ch=.0136,xi_det=.005,candidates=212,MB_candidates=179,Uniform_candidates=33,
        candidate_pool_sha256=sha(LOOKUP/'source_pool.csv'),policy='full per-family signed-K argmax; no candidate pruning',
        cloud='NOT_USED',finite_size='NOT_USED',paper_mode='NOT_RUN',full_regeneration_authorized=False)
    began=time.perf_counter();output,c_hash,i_hash,manifest,initialization=_prepare(output,config)
    serial,s_resource=_run_stage(output,points,'serial',c_hash,i_hash,manifest)
    parallel,p_resource=_run_stage(output,points,'parallel_2',c_hash,i_hash,manifest,workers=2)
    comparison=compare_modes(serial,parallel)
    if not comparison['passed']:raise ValueError('Serial/parallel full-search results disagree')
    summary=dict(status='CURRENTLY_VERIFIED_PASS',config_sha256=c_hash,input_manifest_sha256=i_hash,
        distinct_spatial_points=count,total_point_passes=2*count,fresh_evaluator_calls=2*count*212,
        initialization=initialization,serial=s_resource,parallel_2=p_resource,comparison=comparison,
        elapsed_s=time.perf_counter()-began,
        paper_mode='NOT_RUN',full_regeneration_executed=False,source_evidence_promoted=False,paper_admissible=False)
    for name,h in {**manifest['input_sha256'],**manifest['producer_sha256']}.items():
        if sha(name)!=h:raise ValueError('Input or producer changed during benchmark: '+name)
    _write_new(output/'summary.json',summary);_seal(output)
    return summary


def full_regeneration(config_path,output,*,approval=None,resume=False):
    config=read(config_path)
    require_full_approval(approval,sha(config_path),config['candidate_pool_sha256'])
    if config.get('mode')!='FULL_TARGET_LOOKUP' or config.get('geometry_mode') not in ('per_point','radial_exact'):
        raise ValueError('Explicit full config/geometry mode required')
    if config!=full_configuration(config['geometry_mode']):
        raise ValueError('Full scientific configuration/input binding mismatch')
    if config['candidate_pool_sha256']!=sha(LOOKUP/'source_pool.csv'):
        raise ValueError('Full configuration candidate pool changed')
    rows=read_rows(LOOKUP/'skr_map.csv');points=[];mapping=[];groups={}
    for n,row in enumerate(rows):
        x,y=float(row['x_m']),float(row['y_m']);r2=(x-1000)**2+(y-1000)**2
        key=n if config['geometry_mode']=='per_point' else r2
        if key not in groups:
            point=dict(point_id=f'f{n:04d}',x_m=x,y_m=y,radius2_m2=r2,zenith_deg=float(row['zenith_deg']),distance_m=float(row['distance_m']))
            groups[key]=point['point_id'];points.append(point)
        mapping.append(groups[key])
    if len(rows)!=2601:raise ValueError('Expected full2601 nodes')
    job_config=dict(config,points=points,approval_sha256=sha(approval),source_config_sha256=sha(config_path))
    output,c_hash,i_hash,manifest,initialization=_prepare(output,job_config,resume=resume)
    result,resource=_run_stage(output,points,'full',c_hash,i_hash,manifest,workers=1)
    by_id={r['point']['point_id']:r for r in result};out_rows=[]
    for row,group_id in zip(rows,mapping):
        result_row={k:float(row[k]) for k in ('x_m','y_m','distance_m','zenith_deg')}
        result_row.update(group_id=group_id,xi_ch=.0136,xi_det=.005,source_evidence_promoted=False)
        for family,winner in by_id[group_id]['winners'].items():
            for key in ('K_raw','I_AB','chi_BE','eta_f','xi_f','VA','nu_raw','ensemble_hash','source_evidence_class'):
                result_row[family+'_'+key]=winner[key]
        result_row['K_raw_bits_per_use']=result_row['MB_K_raw'];result_row['K_potential_bits_per_use']=max(0.,result_row['MB_K_raw'])
        out_rows.append(result_row)
    import csv
    with (output/'skr_map.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(out_rows[0]));writer.writeheader();writer.writerows(out_rows)
    if (output/'skr_map.npz').exists():raise FileExistsError('Immutable NPZ exists')
    np.savez_compressed(output/'skr_map.npz',points=np.array([[r['x_m'],r['y_m']] for r in out_rows]),
                        rates=np.array([r['K_raw_bits_per_use'] for r in out_rows]),paper_admissible=False,
                        rate_units='bits/use',coordinate_units='m',xi_ch=.0136,xi_det=.005)
    summary=dict(status='CURRENTLY_VERIFIED_PASS',spatial_points=2601,evaluated_contexts=len(points),
        geometry_mode=config['geometry_mode'],candidates_per_context=212,initialization=initialization,resource=resource,
        paper_mode='NOT_RUN',paper_admissible=False,source_evidence_promoted=False,input_manifest_sha256=i_hash)
    for name,h in {**manifest['input_sha256'],**manifest['producer_sha256']}.items():
        if sha(name)!=h:raise ValueError('Full input or producer changed during execution: '+name)
    _write_new(output/'summary.json',summary);_seal(output)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('benchmark');b.add_argument('--output',required=True);b.add_argument('--points',type=int,default=50)
    f=sub.add_parser('full');f.add_argument('--config',required=True);f.add_argument('--output',required=True)
    f.add_argument('--approval-file');f.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    r=benchmark(args.output,count=args.points) if args.mode=='benchmark' else full_regeneration(args.config,args.output,approval=args.approval_file,resume=args.resume)
    print(json.dumps({k:r[k] for k in ('status','paper_mode')},indent=2))


if __name__=='__main__':main()
