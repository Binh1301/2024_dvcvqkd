"""Author-scoped Phase6A diagnostic, using sealed rates and existing solvers only."""
import argparse
import ast
import copy
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import threading
import time
import platform
from importlib.metadata import version

import numpy as np
import psutil

from .phase5f_integration import ROOT, load_phase5e_lookup, _scenario_digest, _sha
from .rotor_reference import load_reference
from .propulsion import EnergyModel
from .waypoint_graph import WaypointGraph
from .cloud_model import CloudField, GaussianCluster
from .blockage import BlockageModel
from .evaluation import Scenario, evaluate_path
from .finite_size import finite_key
from .baselines import solve_baseline
from .dp_solver import solve_dp
from .experiments import measured, write_json, write_csv

CONFIG = ROOT/'configs/integration/phase6a_numerical_diagnostic.json'
APPROVAL = ROOT/'docs/approvals/phase6a_author_approval.json'
RECIPE = ROOT.parent/'dynamic_gaussian_cloud_figure/create_figure.py'
RECIPE_SHA = '9a010f772d45430cf3abc53ec6f4187bd5060edbc412174eaaf29671dd3e785d'
STATUS = 'NUMERICAL_DIAGNOSTIC — UNVALIDATED_SECURITY_MODEL — NOT PAPER READY'


def read_config():
    return json.loads(CONFIG.read_text(encoding='utf-8'))


def config_hash(config):
    return hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_approval(config):
    if (config.get('mode')!='NUMERICAL_DIAGNOSTIC' or config.get('scope')!='AUTHOR_APPROVED_PHASE6A'
            or config.get('paper_mode')!='NOT_RUN' or config.get('paper_admissible') is not False):
        raise ValueError('Only approved NUMERICAL_DIAGNOSTIC scope; paper-mode forbidden')
    approval=json.loads(APPROVAL.read_text(encoding='utf-8'))
    request=APPROVAL.with_name('phase6a_author_request.txt')
    if (approval.get('author_approved') is not True or approval.get('scope')!=config['scope']
            or approval.get('config_sha256')!=config_hash(config) or approval.get('request_sha256')!=_sha(request)):
        raise ValueError('Explicit approval/configuration/request hash mismatch')
    return approval


def generate_cloud(seed):
    """Execute only the pinned original recipe's pure NumPy generation statements."""
    if _sha(RECIPE)!=RECIPE_SHA:raise ValueError('Cloud generation source changed')
    tree=ast.parse(RECIPE.read_text(encoding='utf-8'))
    def assigns(node,name):
        return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)
    start=next(i for i,n in enumerate(tree.body) if assigns(n,'rng'))
    end=next(i for i,n in enumerate(tree.body) if assigns(n,'masks'))
    scope=dict(np=np,SEED=seed,COMPONENTS=400,NX=400,NY=50,CELL=40,WIDTH=16000,HEIGHT=2000)
    exec(compile(ast.Module(body=tree.body[start:end],type_ignores=[]),str(RECIPE),'exec'),scope)
    scope['threshold']=float(np.percentile(scope['field'],90,method='linear'))
    return scope


def los_samples(model,positions,spacing):
    """Reuse slab intersection, then bound spacing along the full3D segment."""
    if not np.isfinite(spacing) or spacing<=0:raise ValueError('Positive LOS spacing required')
    nodes=[];groups=[];offset=0
    for q in positions:
        segment=model.projected_segment(q)
        if segment is None:raise ValueError('This approved mission requires LOS intersection with the slab')
        dz=model.hap[2]-model.uav_altitude_m
        lo=max(min(model.bottom,model.top),min(model.hap[2],model.uav_altitude_m))
        hi=min(max(model.bottom,model.top),max(model.hap[2],model.uav_altitude_m))
        length=np.hypot(np.linalg.norm(segment[1]-segment[0]),hi-lo)
        if dz==0:raise ValueError('Phase6A requires distinct fixed HAP/UAV altitudes')
        count=max(2,int(np.ceil(length/spacing))+1)
        nodes.append(np.linspace(segment[0],segment[1],count))
        groups.append(np.arange(offset,offset+count));offset+=count
    return np.vstack(nodes),groups


def los_sequence(model,positions,slots,dt,spacing):
    nodes,groups=los_samples(model,positions,spacing)
    z=[]
    for k in range(1,slots+1):
        values=model.field.evaluate(nodes,k*dt)
        z.append([not np.any(values[g]>=model.threshold) for g in groups])
    return np.asarray(z,dtype=np.int8)


def build_scenario(config):
    approval=validate_approval(config)
    m,c,f=config['mission'],config['cloud'],config['finite_size']
    source=load_phase5e_lookup(config['lookup'],CONFIG.parent)
    if (tuple(m['hap_m'])!=source.hap_m or m['uav_altitude_m']!=source.uav_altitude_m or tuple(m['area_m'])!=source.area_m):
        raise ValueError('Approved geometry must match sealed lookup')
    rotor=load_reference(CONFIG.parent/m['rotor_profile'])
    if rotor['params'].v_max!=m['vmax_m_s']:raise ValueError('Rotor speed mismatch')
    axis=np.arange(m['graph_side_nodes'])*m['spacing_m']
    X,Y=np.meshgrid(axis,axis);points=np.c_[X.ravel(),Y.ravel()]
    rates=np.array([source.node(q)['rate'] for q in points])
    graph=WaypointGraph.build(points,m['initial_m'],m['area_m'],m['dt_s'],
        EnergyModel(rotor['params'],m['velocity_samples']),energy_tolerance_j=m['energy_tolerance_j'])
    distance=np.abs(points[:,None,:]-points[None,:,:])
    allowed=(distance.sum(axis=-1)==m['spacing_m'])|(distance.sum(axis=-1)==0)
    graph.costs[~allowed]=np.inf
    graph.successors=[np.flatnonzero(row).tolist() for row in allowed]
    if not np.isfinite(graph.costs[allowed]).all():raise ValueError('An approved cardinal edge is not feasible')
    speeds=np.linalg.norm(distance,axis=-1)[allowed]/graph.dt
    if max(speeds)>m['vmax_m_s']:raise ValueError('Edge speed violates rotor maximum')
    graph.diagnostics.update(movement_edges=int(allowed.sum()-len(points)),successors=list(map(len,graph.successors)),
                             adjacency='four cardinal neighbors plus hover; diagonals forbidden')
    if c['recipe_sha256']!=RECIPE_SHA:raise ValueError('Cloud recipe identity mismatch')
    generated=generate_cloud(c['realization_seed'])
    field=CloudField([GaussianCluster(float(a),(float(x),float(y)),(float(sx),float(sy)))
                     for a,x,y,sx,sy in zip(generated['amplitude'],generated['cx'],generated['cy'],generated['sx'],generated['sy'])],
                     velocity=c['velocity_m_s'],clip_max=15.)
    # Match the actual initial recipe before using its frozen empirical quantile.
    grid=field.evaluate(np.stack((generated['X'],generated['Y']),axis=-1),0)
    np.testing.assert_allclose(grid,generated['field'],rtol=2e-14,atol=2e-14)
    threshold=generated['threshold']
    model=BlockageModel(field,threshold,m['hap_m'],m['uav_altitude_m'],mode='layer',
                       layer_bottom_m=c['layer_bottom_m'],layer_top_m=c['layer_top_m'],sample_spacing_m=c['sample_spacing_3d_m'])
    z=los_sequence(model,points,m['slots'],graph.dt,c['sample_spacing_3d_m'])
    fine=los_sequence(model,points,m['slots'],graph.dt,c['comparison_spacing_3d_m'])
    mismatch=np.argwhere(z!=fine)
    if len(mismatch):raise ValueError(f'LOS convergence failed at {len(mismatch)} node-times; no tuning')
    m0=f['key_allocation_fraction']*f['symbol_rate_uses_s']*graph.dt
    if (m0!=f['m0_signals_per_clear_slot'] or m['slots']*graph.dt!=m['duration_s']
            or not np.isclose(f['epsilon_PE']+f['epsilon_EC']+f['epsilon_PA'],f['epsilon_total'],rtol=1e-15,atol=0)):
        raise ValueError('Mission signal/time/error-budget mismatch')
    budget=m['energy_budget_hover_multiplier']*rotor['derived']['hover_power_W']*m['duration_s']
    s=Scenario(graph,rates,z,budget,m0,f['epsilon_total'])
    scale=dict(reward_scale_bits=float(max(m0*rates)),energy_scale_j=float(max(graph.costs[allowed])),
               normalized_balance_weight=config['greedy']['normalized_balance_weight'])
    w=scale['normalized_balance_weight']
    if not 0<w<1:raise ValueError('Normalized balance weight must lie strictly inside(0,1)')
    scale['lambda_bits_per_j']=w/(1-w)*scale['reward_scale_bits']/scale['energy_scale_j']
    scale['score_equivalence']='w*r/Rmax-(1-w)*E/Emax proportional to r-lambda*E'
    initial=s.graph.initial
    clear=finite_key(float(100*rates[initial]),100,m0,s.epsilon)
    if s.horizon!=100 or graph.costs[initial,initial]*100>budget:raise ValueError('Full stationary mission must be feasible')
    preflight=dict(status='CURRENTLY_VERIFIED_PASS',config_sha256=config_hash(config),approval=approval,
        lookup_package_sha256=source.package_sha256,graph=graph.diagnostics,graph_nodes=121,slots=100,
        edge_speed_max_m_s=float(max(speeds)),hover_power_W=rotor['derived']['hover_power_W'],energy_budget_j=budget,
        lambda_definition=scale,clear_sky_reference=clear,
        emitted_uses_full_horizon=f['symbol_rate_uses_s']*m['duration_s'],allocated_clear_signals_full_horizon=m0*100,
        cloud=dict(seed=c['realization_seed'],original_artifact_seed=42,components=400,threshold_mg_m3=threshold,
            percentile=90,method='linear',domain_m=c['domain_m'],initial_grid_shape=[50,400],clip_max_mg_m3=15,
            fraction_below_threshold=float(np.mean(grid<threshold)),fraction_at_threshold=float(np.mean(grid==threshold)),
            fraction_ge_threshold=float(np.mean(grid>=threshold)),source='New author-approved seed; exact pinned original recipe',
            vertical_assumption=c['vertical_assumption']),
        los_convergence=dict(node_times=int(z.size),disagreements=0,spacing_3d_m=[20,10],all_nodes_all_slots=True,
            limitation='Sampled agreement at declared nodes/times is not a continuous intersection certificate'),
        scenario_sha256=_scenario_digest(s),parent_frozen_spec_sha256=_sha(ROOT.parent/'paper_uav_hap_cvqkd/docs/FINAL_MODEL_SPEC.md'),
        parent_frozen_spec_historical_hash_mismatch=True,paper_mode='NOT_RUN',paper_admissible=False,
        authorization_scope='Synthetic trajectory numerical diagnostic only; parent source/model/publication gates unchanged')
    return s,dict(source=source,rotor=rotor,field=field,model=model,generated=generated,preflight=preflight,**{'lambda':scale})


def reduced_scenario(s):
    indices=np.flatnonzero(np.all((s.graph.positions>=600)&(s.graph.positions<=1400),axis=1))
    costs=s.graph.costs[np.ix_(indices,indices)].copy()
    graph=WaypointGraph(s.graph.positions[indices].copy(),int(np.flatnonzero(indices==s.graph.initial)[0]),costs,
        [np.flatnonzero(np.isfinite(row)).tolist() for row in costs],s.graph.dt,s.graph.energy,
        dict(waypoints=len(indices),scope='REDUCED_BENCHMARK_ONLY'))
    return Scenario(graph,s.rates[indices],s.z[:20,indices],s.budget,s.m0,s.epsilon)


def validate_output(output):
    output=Path(output).resolve()
    if output.parent!=(ROOT/'results').resolve() or not output.name.startswith('phase6a_baseline_20261109'):
        raise ValueError('New Phase6A output must use approved results namespace')
    if output.exists():raise FileExistsError('Never overwrite existing diagnostic results')
    return output


def _atomic(path,data):
    temp=path.with_suffix('.tmp');write_json(temp,data);temp.replace(path)


def _worker(s,method,weight,out):
    out=Path(out);start=time.perf_counter();stop=threading.Event();main_ident=threading.get_ident()
    def sample():
        while not stop.wait(1):
            frame=sys._current_frames().get(main_ident)
            while frame is not None:
                if frame.f_code.co_name=='solve_dp':
                    values=frame.f_locals
                    progress={k:values.get(k) for k in ('k','generated','dominated','discarded','peak')}
                    progress['elapsed_s']=time.perf_counter()-start
                    _atomic(out/'progress.json',progress)
                    break
                frame=frame.f_back
    thread=threading.Thread(target=sample,daemon=True);thread.start()
    try:
        fn=(lambda:solve_dp(s)) if method=='Pareto DP' else (lambda:solve_baseline(s,method,weight))
        result=measured(fn);result['status']='FEASIBLE'
        write_json(out/'result.json',result)
    except Exception as error:
        write_json(out/'result.json',dict(method=method,status='FAILED',error=repr(error),solutions={}))
        raise
    finally:
        stop.set();thread.join()


def execute_method(s,method,weight,out,wall_limit,rss_limit):
    out=Path(out);out.mkdir()
    proc=mp.get_context('spawn').Process(target=_worker,args=(s,method,weight,str(out)))
    start=time.perf_counter();proc.start();peak=0;reason=None
    while proc.is_alive():
        try:peak=max(peak,psutil.Process(proc.pid).memory_info().rss)
        except psutil.NoSuchProcess:pass
        elapsed=time.perf_counter()-start
        if elapsed>wall_limit:reason='WALL_CLOCK_LIMIT'
        if peak>rss_limit:reason='RSS_LIMIT'
        if reason:
            proc.terminate();break
        proc.join(.1)
    proc.join()
    telemetry=dict(process_wall_s=time.perf_counter()-start,parent_sampled_peak_rss_bytes=peak,
                   child_exitcode=proc.exitcode,wall_limit_s=wall_limit,rss_limit_bytes=rss_limit,
                   rss_sampling_interval_s=.1)
    file=out/'result.json'
    if reason or not file.exists():
        result=dict(method=method,status='FAILED_COMPUTATIONAL_LIMIT' if reason else 'FAILED_PROCESS',
            reason=reason or 'Child produced no completed result',solutions={},classification='NO_FULL_OPTIMUM_RETURNED',
            telemetry=telemetry)
        progress=out/'progress.json'
        if progress.exists():result['last_observed_dp_progress']=json.loads(progress.read_text(encoding='utf-8'))
        write_json(file,result)
    else:
        result=json.loads(file.read_text(encoding='utf-8'));result['telemetry']=telemetry;write_json(file,result)
    return result


def export_run(s,run,directory):
    directory=Path(directory);summaries=[]
    for obj in ('P1','P2'):
        if obj not in run['solutions']:
            summaries.append(dict(method=run['method'],objective=obj,status=run['status'],key_bits=None,
                objective_value=None,reason=run.get('reason',run.get('error')),classification=run.get('classification')))
            continue
        sol=run['solutions'][obj];checked=evaluate_path(s,sol['path_indices'])
        for key in ('key_bits','valid_signals','asymptotic_bits','energy_j','mission_time_s'):
            if checked[key]!=sol[key]:raise ValueError('Selected solution arithmetic mismatch: '+key)
        rows=[]
        q0=s.graph.positions[s.graph.initial]
        rows.append(dict(k=0,time_s=0,x_m=float(q0[0]),y_m=float(q0[1]),clear=None,
                         raw_clear_skr_bits_use=None,effective_skr_bits_scheduled_use=None,
                         emitted_uses=0,allocated_signals_before_cloud=0,valid_signals=0,key_bits=0,energy_j=0))
        for row in sol['series']:
            r=s.rate_at(row['k']-1,row['waypoint']);z=row['clear']
            rows.append(dict(row,raw_clear_skr_bits_use=r,effective_skr_bits_scheduled_use=z*r,
                             raw_key_contribution_bits=s.m0*z*r,emitted_uses=row['time_s']*100000,
                             allocated_signals_before_cloud=row['k']*s.m0))
        write_csv(directory/(obj+'_trajectory.csv'),rows,data_status=STATUS)
        summaries.append(dict(method=run['method'],objective=obj,status=run['status'],
            classification=run['classification'],objective_value=sol['objective_value'],key_bits=sol['key_bits'],
            average_skr_bits_s=sol['average_skr_bits_s'],valid_signals=sol['valid_signals'],energy_j=sol['energy_j'],
            stopping_time_s=sol['mission_time_s'],K=sol['K'],clear_fraction=sol['unblocked_slots']/sol['K'],
            runtime_joint_P1_P2_s=run['runtime_s'],python_peak_bytes=run['python_peak_bytes'],
            sampled_peak_rss_bytes=run['sampled_peak_rss_bytes']))
    return summaries


def run(output):
    output=validate_output(output);config=read_config();s,ctx=build_scenario(config)
    output.mkdir();write_json(output/'preflight.json',ctx['preflight']);write_json(output/'config.json',config)
    np.savez_compressed(output/'scenario.npz',positions=s.graph.positions,rates=s.rates,z=s.z,costs=s.graph.costs,
        initial=s.graph.initial,dt=s.graph.dt,budget=s.budget,m0=s.m0,epsilon=s.epsilon,data_status=STATUS)
    g=ctx['generated']
    np.savez_compressed(output/'cloud_realization.npz',seed=config['cloud']['realization_seed'],field=g['field'],
        component_x=g['cx'],component_y=g['cy'],sigma_x=g['sx'],sigma_y=g['sy'],amplitude=g['amplitude'],
        threshold_mg_m3=g['threshold'],x=g['x'],y=g['y'],data_status=STATUS)
    inputs=[CONFIG,APPROVAL,APPROVAL.with_name('phase6a_author_request.txt'),RECIPE,
        CONFIG.parent/config['mission']['rotor_profile'],ROOT/config['finite_size']['reference'],
        ctx['source'].directory/'phase5e_package_manifest.json']
    write_json(output/'input_manifest.json',dict(inputs={str(p.resolve()):_sha(p) for p in inputs},
        producers={str(p.relative_to(ROOT)):_sha(p) for p in sorted((ROOT/'src/uav_qkd').glob('*.py'))},
        environment=dict(python=platform.python_version(),platform=platform.platform(),logical_cpus=psutil.cpu_count(),
            dependencies={name:version(name) for name in ('numpy','scipy','psutil','PyYAML')})))
    shared=_scenario_digest(s);runs=[];summary=[];dp=config['dp'];weight=ctx['lambda']['lambda_bits_per_j']
    for method in ('Stationary','SKR-Greedy','Energy-Aware Greedy','Pareto DP'):
        name=method.lower().replace(' ','_');path=output/name
        print('START '+method,flush=True)
        result=execute_method(s,method,weight,path,dp['operational_wall_limit_s'],dp['operational_rss_limit_bytes'])
        if _scenario_digest(s)!=shared:raise ValueError('Shared scenario changed across methods')
        result['shared_scenario_sha256']=shared;write_json(path/'result.json',result)
        runs.append(result);summary+=export_run(s,result,path)
        print('END '+method+' '+result['status'],flush=True)
    write_csv(output/'comparison_P1.csv',[r for r in summary if r['objective']=='P1'],data_status=STATUS)
    write_csv(output/'comparison_P2.csv',[r for r in summary if r['objective']=='P2'],data_status=STATUS)
    reduced=None
    if runs[-1]['status']!='FEASIBLE':
        small=reduced_scenario(s);path=output/'REDUCED_BENCHMARK_ONLY'
        print('START reduced DP benchmark (not a full comparison replacement)',flush=True)
        reduced=execute_method(small,'Pareto DP',weight,path,dp['operational_wall_limit_s'],dp['operational_rss_limit_bytes'])
        reduced.update(workload='REDUCED_BENCHMARK_ONLY',nodes=25,slots=20,duration_s=200,
                       not_substituted_into_full_comparison=True)
        write_json(path/'result.json',reduced);export_run(small,reduced,path)
    report=dict(data_status=STATUS,preflight_status=ctx['preflight']['status'],config_sha256=config_hash(config),
        paper_mode='NOT_RUN',paper_admissible=False,source_evidence_promoted=False,cloud_approval_scope='PHASE6A_SYNTHETIC_SCENARIO_ONLY',
        shared_scenario_sha256=shared,runs=runs,comparison=summary,reduced_benchmark=reduced,
        completed_algorithm_objective_pairs=sum(len(r['solutions']) for r in runs),
        information_scope='DP perfect full forecast oracle; greedy current-slot actions; all methods retrospective best feasible prefix',
        timing_scope='Each method computes P1/P2 jointly; tracemalloc instrumentation included; shared preflight excluded',
        memory_scope='Python allocation peak and10ms sampled child process RSS; parent watchdog RSS100ms; not exact continuous peak',
        security_scope='Finite-size research-performance proxy, no composable security proof; original evidence labels unchanged',
        source_scope='Best tested finite catalog of212 candidates, no continuous/global modulation optimum claim')
    write_json(output/'results.json',report)
    write_json(output/'output_manifest.json',{str(p.relative_to(output)).replace('\\','/'):_sha(p)
        for p in sorted(output.rglob('*')) if p.is_file() and p.name!='output_manifest.json'})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    args=parser.parse_args();report=run(args.output)
    print(json.dumps(dict(status=report['data_status'],completed_pairs=report['completed_algorithm_objective_pairs'])))
