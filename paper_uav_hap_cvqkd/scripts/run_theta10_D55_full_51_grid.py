"""Approved31-source sequential batch; original source child and Job safety reused."""
import time
ORIGIN = time.monotonic()
import datetime
ORIGIN_UTC = datetime.datetime.now(datetime.timezone.utc)
import argparse
from contextlib import ExitStack
import csv
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_P1_upper_refinement as original
from scripts import build_theta10_D55_two_level_skr_grid as grid

saved, prior = original.saved, original.prior
OUT = grid.audit.BASE/'full_51_grid_exact_completion'
CACHE = OUT/'exact_source_cache'
TOTAL, RESERVE, INTERNAL, SOURCE_OUTER, POST_OUTER = 36*3600.,1800.,3600.,3720.,600.
QUEUE_B = [(.16,4.5),(.16,5.),(.16,6.5),(.165,4.5),(.165,5.),(.165,6.),(.165,6.5),
           (.17,4.5),(.17,5.),(.17,6.),(.17,6.5),(.175,4.5)]
QUEUE_A = [(.10,3.5),(.10,6.5),(.125,2.),(.125,3.5),(.125,5.),(.125,8.),(.15,3.5),
           (.175,2.),(.175,3.5),(.175,5.),(.175,8.),(.20,3.5),(.20,5.),(.20,6.5),(.20,8.),
           (.25,3.5),(.25,5.),(.25,6.5),(.25,8.)]
TERMINAL = {'VALIDATED_SUCCESS','TIMEOUT','FAILED','SAFETY_ABORT','INTERRUPTED'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return grid.audit.read(path)


def atomic_json(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        stream.write(original.prep.storage.checked_json(data));stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def atomic_csv(path,rows,fields=None):
    fields=fields or sorted({k for r in rows for k in r}) or ['status']
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        writer.writerows({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def persist(state):
    state['updated_UTC']=utc()
    atomic_json(OUT/'batch_checkpoint.json',state)
    atomic_csv(OUT/'batch_execution_ledger.csv',state['queue'])


def verify():
    manifest=read(OUT/'protected_input_manifest.json')
    assert all(grid.audit.digest(ROOT/n)==sha for n,sha in manifest.items()),'PROTECTED_SCIENTIFIC_PROVENANCE_DRIFT'
    return len(manifest)


def cache_bank(config):
    bank={}
    for path in sorted((ROOT/'results').glob('**/exact_source_cache/*.json')):
        payload=read(path)
        provenance=original.prep.provenance.verify_source_payload(payload,original.prep.provenance.source_settings(config))
        assert payload['C']>=0 and payload['w']>=0 and payload['support_size']==256
        n,v=float.fromhex(payload['nu_mb_raw_hex']),float.fromhex(payload['V_A_hex'])
        if n==0:continue
        candidate=saved.source.candidate_from_payload(config,
            {payload['ensemble_hash']:{**payload,'_path':path.relative_to(ROOT).as_posix(),'_provenance':provenance}},'MB',n,v)
        assert candidate is not None
        record=dict(payload=payload,provenance=provenance,path=path.relative_to(ROOT).as_posix())
        if saved.pair(n,v) in bank:
            previous=bank[saved.pair(n,v)]
            assert provenance['canonical_source_identity']==previous['provenance']['canonical_source_identity']
            assert (payload['C'],payload['w'])==(previous['payload']['C'],previous['payload']['w'])
        bank[saved.pair(n,v)]=record
    assert len({r['provenance']['canonical_source_cache_key'] for r in bank.values()})==len(bank)
    return bank


def enough_time(now,deadline):
    # Do not shorten/extend the original internal3600s evaluator budget.
    return deadline-now>=SOURCE_OUTER+POST_OUTER+RESERVE


def safety_ok(receipt):
    return bool(receipt.get('actual_job_cleanup')) and all(r.get('verified') and r.get('handle_closed') and
        r.get('active_processes_remaining')==0 for r in receipt['actual_job_cleanup']) and receipt.get('wall_limit_respected') and \
        receipt.get('no_watchdog_thread_remaining') and receipt.get('sleep_prevention',{}).get('released_verified') and \
        receipt.get('sleep_prevention',{}).get('active_verified') and \
        receipt.get('power_watch',{}).get('abort_reason') in (None,'ABSOLUTE_DEADLINE') and \
        receipt.get('supervision')=='ABSOLUTE_DEADLINE_AND_WINDOWS_JOB' and \
        receipt.get('cpu_measurement')=='WINDOWS_JOB_BASIC_ACCOUNTING'


def preflight():
    if OUT.exists():raise SystemExit('Batch output exists;use explicitly authorized continuation,never overwrite/retry')
    baseline=read(grid.OUT/'grid_verification.json')
    assert all(grid.audit.digest(ROOT/n)==sha for n,sha in baseline['input_hashes'].items())
    assert all(grid.audit.digest(grid.OUT/n)==sha for n,sha in baseline['output_hashes'].items())
    assert grid.audit.digest(Path(grid.__file__))==baseline['producer_sha256']
    spec=grid.grid_specification();keys={grid.audit.pair(r) for r in spec}
    queue=QUEUE_B+QUEUE_A
    assert len(queue)==len({saved.pair(*p) for p in queue})==31
    with (grid.OUT/'missing_source_priority.csv').open(encoding='utf-8',newline='') as stream:
        missing={grid.audit.pair(r) for r in csv.DictReader(stream)}
    assert {saved.pair(*p) for p in queue}==missing and missing<=keys
    prior.torch.set_num_threads(1)
    config=saved.source.unconstrained_config();bank=cache_bank(config)
    base=read(grid.audit.INPUT/'objective_checkpoint.json')
    assert [e['L_km'] for e in base]==list(saved.sweep.DISTANCES_KM)
    assert all(len(e['rows'])==151 for e in base)
    OUT.mkdir();CACHE.mkdir()
    manifest=dict(baseline['input_hashes'])
    for folder in (grid.OUT,grid.audit.OUT,grid.export.OUT):
        for path in folder.iterdir():
            if path.is_file():manifest[path.relative_to(ROOT).as_posix()]=grid.audit.digest(path)
    for path in (Path(__file__),ROOT/'tests/test_full_51_grid_execution.py',Path(original.__file__),Path(grid.__file__)):
        manifest[path.relative_to(ROOT).as_posix()]=grid.audit.digest(path)
    for record in bank.values():manifest[record['path']]=grid.audit.digest(ROOT/record['path'])
    atomic_json(OUT/'protected_input_manifest.json',manifest)
    verify()
    evaluator=saved.ao.ExactMBEvaluator(config,{'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},OUT,
        source_cache_dir=CACHE,allow_legacy_exact_import=False)
    plan=[]
    for index,(n,v) in enumerate(queue,1):
        identity=evaluator._source_identity(saved.source.make_ensemble(config,'MB',n,v),n,v)
        key=saved.ao.json_hash(identity)
        assert len(str(CACHE/(key+'.json.tmp')))<=247,'UNSAFE_SOURCE_PATH'
        existing=bank.get(saved.pair(n,v))
        plan.append(dict(index=index,group='B' if index<=12 else 'A',nu_raw=n,V_A=v,
            nu_raw_hex=n.hex(),V_A_hex=v.hex(),original_source_identity=identity,source_cache_key=key,
            attempt_number=0,status='PENDING',started_UTC='',finished_UTC='',wall_seconds='',CPU_seconds='',
            C=existing['payload']['C'] if existing else '',w=existing['payload']['w'] if existing else '',
            source_validation='VERIFIED_EXISTING' if existing else 'NOT_RUN',
            source_path=existing['path'] if existing else '',SKR_status='PENDING',worker_cleanup='NOT_RUN',
            skip_AP_existing=bool(existing),error=''))
    lease=prior.safe.AwakeOnAC()
    with lease:
        samples=[]
        for _ in range(3):samples.append(lease.power.read());time.sleep(.25)
        assert all(prior.safe.safe_power(s) for s in samples)
    state=dict(status='PREPARED_NO_AP',controller_pid=0,queue=plan,AP_attempts=0,
               authorization=None,baseline_source_count=len(bank),initial_grid_cached=sum(k in bank for k in keys),
               initial_grid_missing=sum(k not in bank for k in keys),saved_baseline_objective_rows=3926)
    persist(state)
    atomic_json(OUT/'preflight.json',dict(status='CURRENTLY_VERIFIED_PASS_SCIENTIFIC_PREFLIGHT',
        AC_samples=samples,Sleep_lease=lease.receipt,protected_files=len(manifest),initial_source_catalog=len(bank),
        initial_grid_cached=state['initial_grid_cached'],initial_grid_missing=state['initial_grid_missing'],
        maximum_source_path_length=max(len(str(CACHE/(p['source_cache_key']+'.json.tmp'))) for p in plan),
        original_internal_evaluator_timeout_seconds=3600,maximum_attempts=31,total_wall_seconds=TOTAL,reserve_seconds=RESERVE,
        source_entry='UNCHANGED_ORIGINAL_UPPER_SOURCE_CHILD_WITH_TARGET_IO_BINDING',
        actual_job_cleanup_verification_required=True,dummy_gate=False,AO_refinement=False,
        frozen_historical_hash_discrepancy='PREEXISTING_UNCHANGED',new_AP_attempts=0))
    print(f'PREFLIGHT_PASS;catalog={len(bank)};grid={state["initial_grid_cached"]}/51;missing={state["initial_grid_missing"]};AP0',flush=True)
    return state


def stage_path(row):return OUT/f'p{row["index"]:02d}'


def source_child(index):
    state=read(OUT/'batch_checkpoint.json');row=state['queue'][index-1];stage=stage_path(row)
    assert row['index']==index and row['status']=='RUNNING' and row['attempt_number']==1
    context=SimpleNamespace(OUT=stage,storage=original.prep.storage,provenance=original.prep.provenance)
    with patch.multiple(original,prep=context,NU=row['nu_raw'],VA=row['V_A'],KEY=row['source_cache_key'],OUT=stage,CACHE=CACHE):
        return original.source_child()  # Scientific API/internaltimeout/precision unchanged.


def objective_child(index):
    verify();state=read(OUT/'batch_checkpoint.json');row=state['queue'][index-1];stage=stage_path(row)
    config=saved.source.unconstrained_config();prior.torch.set_num_threads(1)
    payload=read(ROOT/row['source_path'])
    original.prep.provenance.verify_source_payload(payload,original.prep.provenance.source_settings(config))
    dirs=tuple(sorted({p.parent for p in (ROOT/'results').glob('**/exact_source_cache/*.json')}))
    outputs=[]
    with ExitStack() as guards:
        for obj,name in ((saved.ao.ExactMBEvaluator,'source_moments'),(prior.gram_moments,'_fallback'),
                         (saved.sweep,'make_channel'),(saved.sweep,'run_single_distance_ao')):
            guards.enter_context(patch.object(obj,name,prior.preparation.forbidden))
        for entry in read(grid.audit.INPUT/'objective_checkpoint.json'):
            objective=saved.ao.ExactObjective(config,entry['identity']['identity']['channel'],stage,
                allow_new_source=False,source_cache_dirs=dirs)
            assert objective.restore_objective_rows(entry['rows'],entry['identity'])==151
            result=objective(row['nu_raw'],row['V_A'])
            assert result['SKR']==result['beta_I_AB']-result['chi_BE'] and result['status']=='PASS'
            assert saved.pair(result['nu_raw'],result['V_A'])==saved.pair(row['nu_raw'],row['V_A'])
            assert result['ensemble_hash']==payload['ensemble_hash'] and result['source_cache_key']==payload['cache_key']
            outputs.append(result)
            atomic_csv(stage/'new_exact_skr_26_distances.csv',outputs)
    assert [r['L_km'] for r in outputs]==list(saved.sweep.DISTANCES_KM)
    atomic_json(stage/'validated_objectives.json',outputs)
    print(f'OBJECTIVES_VALIDATED:{index};26distances;noAP/noAO',flush=True)
    return 0


def supervise(row,phase,limit):
    stage=stage_path(row)
    command=[sys.executable,'-B','-X','utf8','-u',str(Path(__file__).resolve()),'--child',phase,'--index',str(row['index'])]
    with (stage/(phase+'.log')).open('w',encoding='utf-8') as log:
        result=original.checked_supervised_process(command,limit,log)
    atomic_json(stage/(phase+'_supervision.json'),result)
    return result


def validate_source(row):
    config=saved.source.unconstrained_config();bank=cache_bank(config)
    record=bank.get(saved.pair(row['nu_raw'],row['V_A']))
    if record is None:raise ValueError('SOURCE_PROVENANCE_OR_IDENTITY_FAILURE')
    p=record['payload'];canonical=record['provenance']['canonical_source_identity']
    expected={**row['original_source_identity'],'source_implementation':
        {n:r['canonical_lf_sha256'] for n,r in record['provenance']['implementation'].items()}}
    assert expected==canonical,'SOURCE_IDENTITY_COLLISION'
    row.update(C=p['C'],w=p['w'],source_path=record['path'],resolved_source_cache_key=p['cache_key'],source_validation='VERIFIED')
    atomic_json(stage_path(row)/'source_checkpoint.json',record)


def summarize(state,make_figures=True):
    entries=read(grid.audit.INPUT/'objective_checkpoint.json')
    keyed={e['L_km']:{saved.pair(r['nu_raw'],r['V_A']):r for r in e['rows']} for e in entries}
    successful=[];sources=[]
    for row in state['queue']:
        if row['source_validation']=='VERIFIED':sources.append(row)
        path=stage_path(row)/'validated_objectives.json'
        if row['status']=='VALIDATED_SUCCESS':
            values=read(path);assert len(values)==26
            assert [v['L_km'] for v in values]==list(saved.sweep.DISTANCES_KM)
            for value in values:
                key=saved.pair(value['nu_raw'],value['V_A']);old=keyed[value['L_km']].get(key)
                assert old is None or all(old[f]==value[f] for f in ('I_AB','beta_I_AB','chi_BE','SKR'))
                keyed[value['L_km']][key]=value
            successful.append(row)
    spec=grid.grid_specification();grid_keys={grid.audit.pair(r) for r in spec}
    grid_values=[];offgrid=[];best_rows=[];expanded=[]
    for entry in entries:
        L=entry['L_km'];raw=list(keyed[L].values());rank=grid.audit.ranked(raw);best,second=rank[:2]
        classified=grid.export.classify(raw,L)
        local=[]
        for value in classified:
            original_row=keyed[L][saved.pair(value['nu_raw'],value['V_A'])]
            record={**original_row,**value}
            if grid.audit.pair(record) in grid_keys:grid_values.append(record);local.append(record)
            else:offgrid.append(record)
        near=[r for r in local if r['near_optimal']=='YES']
        previous=grid.audit.ranked(entry['rows'])[0]
        best_rows.append(dict(L_km=L,nu_raw=best['nu_raw'],V_A=best['V_A'],SKR=best['SKR'],
            second_nu_raw=second['nu_raw'],second_V_A=second['V_A'],second_SKR=second['SKR'],
            delta_K=best['SKR']-second['SKR'],relative_loss_fraction=(best['SKR']-second['SKR'])/best['SKR'] if best['SKR']>0 else '',
            near_optimal_grid_count=len(near),near_nu_min=min((r['nu_raw'] for r in near),default=''),
            near_nu_max=max((r['nu_raw'] for r in near),default=''),near_VA_min=min((r['V_A'] for r in near),default=''),
            near_VA_max=max((r['V_A'] for r in near),default=''),previous_nu_raw=previous['nu_raw'],previous_V_A=previous['V_A'],
            previous_SKR=previous['SKR'],improved=best['SKR']>previous['SKR'],
            best_parameters_changed=saved.pair(best['nu_raw'],best['V_A'])!=saved.pair(previous['nu_raw'],previous['V_A']),
            ordering_status='NUMERICALLY_UNCERTIFIED'))
        expanded.append(dict(L_km=L,identity=entry['identity'],rows=raw))
    reference=[r for r in grid_values if r['L_km']==saved.REF]
    reference_keys={grid.audit.pair(r) for r in reference}
    statuses={saved.pair(r['nu_raw'],r['V_A']):r for r in state['queue']}
    coverage=[]
    for r in spec:
        q=statuses.get(grid.audit.pair(r),{})
        coverage.append(dict(r,status='EXACT_CACHED' if grid.audit.pair(r) in reference_keys else q.get('status','MISSING_SOURCE'),
            source_validation=q.get('source_validation','VERIFIED_BASELINE'),validated_distances=26 if grid.audit.pair(r) in reference_keys else 0))
    for name,rows in [('validated_new_sources.csv',sources),('failed_or_timeout_sources.csv',[r for r in state['queue'] if r['status'] in TERMINAL-{'VALIDATED_SUCCESS'}]),
                     ('final_grid_51_coverage.csv',coverage),('complete_grid_reference.csv',reference),
                     ('complete_grid_26_distances.csv',grid_values),('best_skr_26_distances.csv',best_rows),
                     ('near_optimal_grid_candidates.csv',[r for r in grid_values if r['near_optimal']=='YES']),
                     ('offgrid_existing_exact_candidates.csv',offgrid)]:atomic_csv(OUT/name,rows)
    atomic_json(OUT/'objective_checkpoint.json',expanded)
    pending=[dict(nu_raw=r['nu_raw'],V_A=r['V_A'],status=r['status']) for r in coverage if r['validated_distances']!=26]
    atomic_csv(OUT/'remaining_missing_pairs.csv',pending,['nu_raw','V_A','status'])
    bank=cache_bank(saved.source.unconstrained_config())
    summary=dict(status=state['status'],AP_attempts=state['AP_attempts'],successful_new_sources=len(sources),
        completely_validated_new_sources=len(successful),timeouts=sum(r['status']=='TIMEOUT' for r in state['queue']),
        other_failures=sum(r['status'] in {'FAILED','SAFETY_ABORT','INTERRUPTED'} for r in state['queue']),
        unresolved_grid_points=len(pending),source_catalog_size=len(bank),grid_complete_points=len(reference),
        grid_coverage_percent=100*len(reference)/51,grid_objective_rows=len(grid_values),pending_pairs=pending,
        reference=next(r for r in best_rows if r['L_km']==saved.REF),improved_distances=[r['L_km'] for r in best_rows if r['improved']],
        changed_parameter_distances=[r['L_km'] for r in best_rows if r['best_parameters_changed']],
        Job_CPU_seconds=sum(float(r['CPU_seconds'] or 0) for r in state['queue']),
        AO_runs=0,scientific_methods_changed=False,total_K_error_bound_certified=False)
    if make_figures:
        render_figures(coverage,reference,[r for r in offgrid if r['L_km']==saved.REF],summary['reference'])
        summary['figure_pairs_produced']=3
    return summary


def render_figures(coverage,reference,offgrid,best):
    from matplotlib import pyplot as plt
    plt.rcParams.update({'font.family':'serif','font.size':10,'legend.fontsize':8,'pdf.fonttype':42})
    for name,title in [('grid_coverage_final','Exact grid completion'),('skr_landscape_final','Exact-data SKR landscape'),
                       ('near_optimal_region_final','Exact near-optimal samples')]:
        fig,ax=plt.subplots(figsize=(7.5,4.6),layout='constrained')
        ax.set(xlabel=r'Modulation variance $V_A$ (SNU)',ylabel=r'MB shaping parameter $\nu_{\rm raw}$',
               title=f'{title}: L={saved.REF} km')
        ax.grid(alpha=.15);ax.set_axisbelow(True)
        def scatter(rows,**kwargs):return ax.scatter([r['V_A'] for r in rows],[r['nu_raw'] for r in rows],**kwargs)
        missing=[r for r in coverage if r['validated_distances']!=26]
        if name=='grid_coverage_final':
            scatter([r for r in coverage if r['Grid_A']],marker='s',s=100,facecolors='none',edgecolors='tab:blue',label='Broad grid A')
            scatter([r for r in coverage if r['Grid_B']],marker='o',s=65,facecolors='none',edgecolors='tab:orange',label='Focused grid B')
            scatter([r for r in coverage if r['validated_distances']==26],marker='.',s=28,color='black',label='Validated exact')
        elif name=='skr_landscape_final':
            colored=scatter(reference,c=[r['SKR'] for r in reference],cmap='viridis',s=38,marker='s',label='Exact grid SKR')
            cb=fig.colorbar(colored,ax=ax,label='Secret Key Rate (bits/use)',shrink=.85)
            cb.solids.set_rasterized(False)
        else:
            scatter([r for r in reference if r['near_optimal']!='YES'],s=28,color='0.65',label='Other exact grid')
            scatter([r for r in reference if r['near_optimal']=='YES'],s=70,marker='o',facecolors='none',edgecolors='tab:green',label='Near-optimal grid')
            scatter([r for r in offgrid if r['near_optimal']=='YES'],s=40,marker='^',color='tab:green',label='Near-optimal off-grid')
        scatter(missing,marker='x',s=28,color='tab:red',label='Missing/failed grid')
        ax.scatter([best['V_A']],[best['nu_raw']],marker='*',s=130,color='gold',edgecolors='black',label='Best exact-tested')
        ax.legend(loc='upper center',bbox_to_anchor=(.5,-.21),ncol=3)
        fig.savefig(OUT/(name+'.png'),dpi=400);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)


def run(*,approved=False,resume=False):
    if not approved:raise SystemExit('AP NOT_RUN:explicit batch authorization required')
    if not OUT.exists():state=preflight()
    else:state=read(OUT/'batch_checkpoint.json')
    if state.get('controller_pid') and prior.alive(state['controller_pid']):raise SystemExit('Checkpoint owner is alive;no duplicate controller')
    if state['authorization'] is not None and not resume:raise SystemExit('Explicit continuation invocation required;no automatic relaunch')
    if state['authorization'] is None:
        state['authorization']=dict(origin_UTC=ORIGIN_UTC.isoformat(),deadline_UTC=(ORIGIN_UTC+datetime.timedelta(seconds=TOTAL)).isoformat(),
            origin_monotonic=ORIGIN,deadline_monotonic=ORIGIN+TOTAL,maximum_attempts=31,total_seconds=TOTAL,reserve_seconds=RESERVE,
            internal_timeout_seconds=INTERNAL,retry_allowed=False,parallel_workers=1)
    deadline_utc=datetime.datetime.fromisoformat(state['authorization']['deadline_UTC'])
    remaining=(deadline_utc-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    deadline=min(state['authorization']['deadline_monotonic'],time.monotonic()+remaining)
    state.update(controller_pid=os.getpid(),status='RUNTIME_PREFLIGHT')
    for row in state['queue']:
        if row['status']=='RUNNING':row.update(status='INTERRUPTED',finished_UTC=utc(),error='Previous attempt interrupted;no retry')
    persist(state);lease=prior.safe.AwakeOnAC();fatal=None
    try:
        verify()
        with lease:
            state['status']='RUNNING_SEQUENTIAL_BATCH';persist(state)
            for row in state['queue']:
                if row['status'] in TERMINAL:continue
                if not enough_time(time.monotonic(),deadline):state['status']='STOPPED_GLOBAL_BUDGET_RESERVE';break
                samples=[]
                for _ in range(3):samples.append(lease.power.read());time.sleep(.25)
                if not all(prior.safe.safe_power(s) for s in samples):raise RuntimeError('MANDATORY_AC_SAFETY_FAILED')
                verify();bank=cache_bank(saved.source.unconstrained_config());existing=bank.get(saved.pair(row['nu_raw'],row['V_A']))
                stage=stage_path(row);stage.mkdir(exist_ok=True)
                atomic_json(stage/'protected_input_manifest.json',read(OUT/'protected_input_manifest.json'))
                atomic_json(stage/'confirmed_candidate.json',{'original_source_identity':row['original_source_identity']})
                atomic_json(stage/'execution_authorization.json',{'maximum_attempts':1,'source_cache_key':row['source_cache_key']})
                row.update(status='RUNNING',started_UTC=utc(),worker_cleanup='PENDING',AC_samples=samples)
                persist(state);started=time.monotonic();receipts=[]
                try:
                    if not existing:
                        assert row['attempt_number']==0 and state['AP_attempts']<31
                        row['attempt_number']=1;state['AP_attempts']+=1;persist(state)
                        atomic_json(stage/'source_attempt_started.json',{'attempt_number':1})
                        print(f'SOURCE_STARTED {row["index"]}/31 ({row["nu_raw"]!r},{row["V_A"]!r});internal3600s unchanged',flush=True)
                        receipt=supervise(row,'source',SOURCE_OUTER);receipts.append(receipt)
                        if not safety_ok(receipt):raise RuntimeError('MANDATORY_WORKER_JOB_POWER_OR_SLEEP_SAFETY_FAILED')
                        result=read(stage/'source_result.json') if (stage/'source_result.json').exists() else {}
                        if receipt['deadline_exceeded'] or result.get('status')=='TIMEOUT_INTERNAL_EVALUATOR':
                            row.update(status='TIMEOUT',SKR_status='NOT_RUN',error=result.get('error','SUPERVISOR_TIMEOUT'));continue
                        if receipt['returncode']!=0 or result.get('status')!='COMPLETED_EXACT':
                            row.update(status='FAILED',SKR_status='NOT_RUN',error=result.get('error','SCIENTIFIC_SOURCE_PROCESS_FAILED'))
                            if any(s in row['error'].upper() for s in ('PROVENANCE','INCOMPATIBLE','IDENTITY','CORRUPT')):
                                raise RuntimeError('MANDATORY_SCIENTIFIC_PROVENANCE_FAILED:'+row['error'])
                            continue
                    else:row['skip_AP_existing']=True
                    validate_source(row);persist(state)
                    limit=min(POST_OUTER,deadline-time.monotonic()-RESERVE)
                    if limit<=0:row.update(status='FAILED',SKR_status='INCOMPLETE_BUDGET');state['status']='STOPPED_GLOBAL_BUDGET_RESERVE';break
                    receipt=supervise(row,'objectives',limit);receipts.append(receipt)
                    if not safety_ok(receipt):raise RuntimeError('MANDATORY_OBJECTIVE_JOB_SAFETY_FAILED')
                    if receipt['returncode']!=0 or receipt['deadline_exceeded']:
                        row.update(status='FAILED',SKR_status='INCOMPLETE_VALID_SOURCE_PRESERVED',error='OBJECTIVE_PROCESS_FAILED_NO_AP_RETRY')
                    else:
                        values=read(stage/'validated_objectives.json');assert len(values)==26
                        row.update(status='VALIDATED_SUCCESS',SKR_status='VALIDATED_26_DISTANCES')
                finally:
                    row.update(finished_UTC=utc(),wall_seconds=time.monotonic()-started,
                        CPU_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in receipts),
                        worker_cleanup='VERIFIED_EMPTY_CLOSED' if receipts and all(safety_ok(r) for r in receipts) else 'UNVERIFIED',
                        supervision_receipts=receipts)
                    persist(state)
                    summarize(state,make_figures=False)
                    print(f'SOURCE_SAVED {row["index"]}/31: {row["status"]};wall={row["wall_seconds"]:.3f}s;C={row["C"]};w={row["w"]}',flush=True)
            else:state['status']='ALL_31_QUEUE_ITEMS_PROCESSED'
    except BaseException as error:
        fatal=f'{type(error).__name__}:{error}';state.update(status='STOPPED_MANDATORY_SAFETY_OR_PROVENANCE',error=fatal)
        for row in state['queue']:
            if row['status']=='RUNNING':row.update(status='SAFETY_ABORT',error=fatal,finished_UTC=utc())
    finally:
        state['outer_Sleep_lease']=lease.receipt;state['controller_pid']=0
        state['batch_wall_seconds']=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(state['authorization']['origin_UTC'])).total_seconds()
        state['controller_CPU_seconds']=time.process_time()
        if state['batch_wall_seconds']>TOTAL:state['status']='FAILED_TOTAL_WALL_OVERRUN'
        persist(state)
        try:
            protected=verify();summary=summarize(state)
            summary.update(batch_wall_seconds=state['batch_wall_seconds'],controller_CPU_seconds=state['controller_CPU_seconds'],
                total_measured_CPU_seconds=summary['Job_CPU_seconds']+state['controller_CPU_seconds'],
                outer_Sleep_lease=lease.receipt,protected_files=protected,
                        every_actual_Job_empty_closed=all(r['worker_cleanup']=='VERIFIED_EMPTY_CLOSED' for r in state['queue']
                            if r['attempt_number'] or r.get('supervision_receipts')),
                within_36hour_budget=state['batch_wall_seconds']<=TOTAL)
            atomic_json(OUT/'final_report.json',summary)
            text='# Full51-grid exact completion\n\n'+original.prep.storage.checked_json(summary)+\
                '\n\nFinite exact-tested catalog only;NUMERICALLY_UNCERTIFIED ordering,no continuous/global certificate. '
            (OUT/'full_grid_completion_report.md').write_text(text,encoding='utf-8')
            final_elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(state['authorization']['origin_UTC'])).total_seconds()
            summary.update(batch_wall_seconds_including_finalization=final_elapsed,
                           within_36hour_budget=final_elapsed<=TOTAL,controller_CPU_seconds_including_finalization=time.process_time())
            atomic_json(OUT/'final_report.json',summary)
            state['batch_wall_seconds_including_finalization']=final_elapsed;persist(state)
            print(original.prep.storage.checked_json(summary),flush=True)
        except BaseException as error:
            atomic_json(OUT/'finalization_failure.json',{'error':f'{type(error).__name__}:{error}','state':state,'scientific_results_preserved':True})
            print(f'FINALIZATION_FAILURE:{error}',flush=True)
    return 0 if state['status']=='ALL_31_QUEUE_ITEMS_PROCESSED' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--approved-batch',action='store_true');parser.add_argument('--resume-approved',action='store_true')
    parser.add_argument('--child',choices=['source','objectives']);parser.add_argument('--index',type=int)
    args=parser.parse_args()
    if args.child:raise SystemExit(source_child(args.index) if args.child=='source' else objective_child(args.index))
    if args.preflight_only:preflight();raise SystemExit(0)
    raise SystemExit(run(approved=args.approved_batch or args.resume_approved,resume=args.resume_approved))
