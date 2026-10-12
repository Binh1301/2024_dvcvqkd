"""Budgeted orchestration around unchanged original ALT_OPT and source children."""
import time
ORIGIN = time.monotonic()
import argparse
import csv as csvlib
from contextlib import ExitStack
import datetime
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_full_51_grid as b

BASE = b.OUT.parent / 'grid_timeout_retry_1'
OUT = ROOT / 'results/theta10_D55_objective_C_multistart_alt_opt'
CACHE = OUT / 'exact_source_cache'
b.OUT, b.CACHE = OUT, CACHE
STARTS = [(.165, 5.5), (.16, 6.), (.17, 5.), (.15, 6.5), (.175, 4.5)]
TOTAL, RESERVE, MAX_AP, STAGE1_AP = 129600., 1800., 36, 12
READ, JSON, CSV = b.read, b.atomic_json, b.atomic_csv
STATE = OUT / 'objective_c_checkpoint.json'


def verify():
    manifest = READ(OUT / 'protected_input_manifest.json')
    assert all(b.grid.audit.digest(ROOT / p) == h for p, h in manifest.items()), 'SCIENTIFIC_PROVENANCE_DRIFT'
    return len(manifest)


def save(state):
    state['updated_UTC'] = b.utc()
    JSON(STATE, state)
    CSV(OUT / 'new_validated_exact_sources.csv', [r for r in state['sources'] if r['source_validation'] == 'VERIFIED'])
    CSV(OUT / 'failed_or_timeout_sources.csv', [r for r in state['sources'] if r['status'] in ('TIMEOUT', 'FAILED', 'SAFETY_ABORT')])


def append_csv(name, rows):
    path = OUT / name
    previous = []
    if path.exists():
        with path.open(newline='', encoding='utf-8') as stream:
            previous = list(csvlib.DictReader(stream))
    CSV(path, previous + rows)


def failed_history(bank):
    blocked = set()
    for path in (ROOT / 'results').glob('**/source_result.json'):
        result = READ(path)
        if result.get('status') != 'COMPLETED_EXACT':
            n, v = result.get('nu_raw'), result.get('V_A')
            if n is not None and v is not None:
                key = b.saved.pair(float(n), float(v))
                if key not in bank:
                    blocked.add(key)
    return sorted(blocked)


def preflight():
    assert not OUT.exists(), 'Output exists: no duplicate controller or automatic restart'
    state_b = READ(BASE / 'final_report.json')
    assert state_b['status'] == 'VALIDATED_SUCCESS' and state_b['controller_pid'] == 0
    assert state_b['outer_Sleep_lease']['released_verified']
    assert all(b.safety_ok(r) for r in state_b['queue'][0]['supervision_receipts'])
    original_manifest = READ(BASE / 'protected_input_manifest.json')
    assert all(b.grid.audit.digest(ROOT / p) == h for p, h in original_manifest.items())
    entries = READ(BASE / 'objective_checkpoint.json')
    config = b.saved.source.unconstrained_config()
    bank = b.cache_bank(config)
    assert len(bank) == 182 and [e['L_km'] for e in entries] == list(b.saved.sweep.DISTANCES_KM)
    spec = {b.grid.audit.pair(r) for r in b.grid.grid_specification()}
    for e in entries:
        keys = {b.saved.pair(r['nu_raw'], r['V_A']) for r in e['rows']}
        assert len(e['rows']) == len(keys) == 182 and spec <= keys
        assert all(r['status'] == 'PASS' and r['SKR'] == r['beta_I_AB'] - r['chi_BE'] for r in e['rows'])
    ref = next(e for e in entries if e['L_km'] == b.saved.REF)
    best = b.grid.audit.ranked(ref['rows'])[0]
    assert (best['nu_raw'], best['V_A'], best['SKR']) == (.165, 5.5, .07798099387393764)
    assert all(b.saved.pair(*p) in bank for p in STARTS)
    OUT.mkdir(); CACHE.mkdir()
    # Keep cache filenames short enough for the unchanged Windows source writer.
    assert len(str(CACHE / ('0' * 64 + '.json.tmp'))) <= 247
    for path in BASE.rglob('*'):
        if path.is_file():
            original_manifest[path.relative_to(ROOT).as_posix()] = b.grid.audit.digest(path)
    for path in (Path(__file__), ROOT / 'tests/test_objective_c.py'):
        original_manifest[path.relative_to(ROOT).as_posix()] = b.grid.audit.digest(path)
    JSON(OUT / 'protected_input_manifest.json', original_manifest)
    JSON(OUT / 'baseline182.json', entries)
    JSON(OUT / 'expanded_objectives.json', entries)
    initialization = [dict(start_id=f'S{i}', nu_raw=n, V_A=v,
        SKR=next(r['SKR'] for r in ref['rows'] if b.saved.pair(r['nu_raw'], r['V_A']) == b.saved.pair(n, v)))
        for i, (n, v) in enumerate(STARTS, 1)]
    CSV(OUT / 'reference_multistart_initialization.csv', initialization)
    lease = b.prior.safe.AwakeOnAC()
    with lease:
        samples = []
        for _ in range(3):
            samples.append(lease.power.read()); time.sleep(.25)
        assert all(b.prior.safe.safe_power(p) for p in samples)
    state = dict(status='PREPARED_NO_AP', controller_pid=0, AP_attempts=0, stage=1,
        sources=[], stage1_attempts=0, stage2_attempts=0, epochs=0,
        historical_failed_pairs=failed_history(bank), baseline_catalog=182,
        preflight_AC=samples, preflight_Sleep=lease.receipt,
        nu_zero_boundary='NOT_ADMITTED_BY_UNCHANGED_ORIGINAL_AO; NO_GLOBAL_CLOSURE_CLAIM',
        total_numerical_error_bound='UNAVAILABLE; convergence is conditional',
        authorization=None)
    save(state)
    JSON(OUT / 'preflight.json', dict(status='CURRENTLY_VERIFIED_PASS', source_count=182,
        objective_rows=4732, grid_complete=51, reference=best, protected_files=verify(),
        AC_samples=samples, Sleep=lease.receipt, maximum_AP=36, stage1_ceiling=12,
        total_wall_seconds=TOTAL, reserve_seconds=RESERVE, original_internal_timeout_seconds=3600,
        source_precision=[1050,1250,1450], scientific_methods_changed=False,
        frozen_historical_hash_discrepancy='PREEXISTING_UNCHANGED_EXPERIMENT_SCOPE'))
    return state


def make_objective(entry):
    dirs = tuple(sorted({p.parent for p in (ROOT / 'results').glob('**/exact_source_cache/*.json')}))
    objective = b.saved.ao.ExactObjective(b.saved.source.unconstrained_config(),
        entry['identity']['identity']['channel'], OUT, allow_new_source=False, source_cache_dirs=dirs)
    assert objective.restore_objective_rows(entry['rows'], entry['identity']) == len(entry['rows'])
    for row in entry['rows']:
        objective.register_catalog(row['nu_raw'], row['V_A'])
    return objective


def convergence(run):
    it = run['iterations']
    if run['status'] == 'NUMERICAL_FAILURE':
        return 'SOURCE_FAILED'
    stable = len(it) >= 2 and all(
        abs(r['delta_K']) <= max(b.saved.ao.K_TOLERANCE, 1e-5 * abs(r['K_before'])) and
        r['V_A_search_status'] == r['nu_search_status'] == 'NUMERICALLY_CLOSED_LOCAL_BRACKET'
        for r in it[-2:])
    return 'NUMERICALLY_CONVERGED_ON_TESTED_MESH' if stable and not run['warnings'] else 'APPARENTLY_STABLE_BUT_UNRESOLVED'


def analyze_child():
    verify(); b.prior.torch.set_num_threads(1)
    state = READ(STATE); entries = READ(OUT / 'expanded_objectives.json')
    stage, epoch = state['stage'], state['epochs']
    reference = next(e for e in entries if e['L_km'] == b.saved.REF)
    baseline = {e['L_km']: b.grid.audit.ranked(e['rows'])[0] for e in READ(OUT / 'baseline182.json')}
    targets = [reference] if stage == 1 else entries
    ledger, requests, runs, comparisons = [], [], [], []
    previous_ref = READ(OUT / 'stage1_analysis.json') if (OUT / 'stage1_analysis.json').exists() else None
    ref_pair = (previous_ref['best']['nu_raw'], previous_ref['best']['V_A']) if previous_ref else (.165,5.5)
    with ExitStack() as guards:
        for obj, name in ((b.saved.ao.ExactMBEvaluator,'source_moments'), (b.prior.gram_moments,'_fallback'),
                          (b.saved.sweep,'make_channel')):
            guards.enter_context(patch.object(obj, name, b.prior.preparation.forbidden))
        for entry in targets:
            L = entry['L_km']; objective = make_objective(entry)
            maximum = b.grid.audit.ranked(entry['rows'])[0]
            starts = [(f'S{i}',n,v) for i,(n,v) in enumerate(STARTS,1)] if stage == 1 else [
                ('catalog', maximum['nu_raw'], maximum['V_A']), ('reference', *ref_pair)]
            if stage == 2:
                j = entries.index(entry)
                for k in (j-1,j+1):
                    if 0 <= k < len(entries):
                        neighbor = b.grid.audit.ranked(entries[k]['rows'])[0]
                        starts.append((f'neighbor_{entries[k]["L_km"]}',neighbor['nu_raw'],neighbor['V_A']))
                starts.extend((f'S{i}',n,v) for i,(n,v) in enumerate(STARTS,1))
            unique_starts, seen = [], set()
            for start in starts:
                key = b.saved.pair(start[1],start[2])
                if key not in seen:
                    unique_starts.append(start); seen.add(key)
            for start_id,n,v in unique_starts:
                searches = []
                original_search = b.saved.ao.adaptive_maximize_1d
                def observed_search(**kwargs):
                    result = original_search(**kwargs)
                    coordinate = result['variable']
                    running = None
                    for point in result['history']:
                        pn = result['fixed'] if coordinate == 'V_A' else point['value']
                        pv = point['value'] if coordinate == 'V_A' else result['fixed']
                        value = objective.rows.get(objective.key(pn,pv))
                        old_incumbent = running
                        if value is not None:
                            running = max(running if running is not None else -math.inf, value['SKR'])
                        ledger.append(dict(stage=stage,epoch=epoch,L_km=L,start_id=start_id,
                            iteration=len(searches)//2,coordinate=coordinate,fixed=result['fixed'],
                            nu_raw=pn,V_A=pv,nu_raw_hex=float(pn).hex(),V_A_hex=float(pv).hex(),
                            status=point['status'],cache_hit=value is not None,new_AP_attempt=False,
                            previous_incumbent=old_incumbent,updated_incumbent=running,
                            accepted=value is not None and (old_incumbent is None or value['SKR']>old_incumbent),
                            C=objective.payloads[value['ensemble_hash']]['C'] if value else '',
                            w=objective.payloads[value['ensemble_hash']]['w'] if value else '',
                            I_AB=value['I_AB'] if value else '',beta_I_AB=value['beta_I_AB'] if value else '',
                            chi_BE=value['chi_BE'] if value else '',SKR=value['SKR'] if value else '',
                            source_cache_key=value['source_cache_key'] if value else '',timestamp=b.utc()))
                    for missing in result['source_missing']:
                        pn = result['fixed'] if coordinate=='V_A' else missing['value']
                        pv = missing['value'] if coordinate=='V_A' else result['fixed']
                        requests.append(dict(nu_raw=pn,V_A=pv,L_km=L,start_id=start_id,
                            coordinate=coordinate,fixed=result['fixed'],coordinate_best_K=result['best_K'],
                            current_catalog_K=maximum['SKR'],bracket=result['bracket'],
                            search_status=result['status'],timestamp=b.utc()))
                    searches.append(result)
                    JSON(OUT / 'coordinate_progress.json',dict(stage=stage,epoch=epoch,L_km=L,
                        start_id=start_id,completed_coordinate_searches=searches))
                    return result
                with patch.object(b.saved.sweep,'adaptive_maximize_1d',observed_search):
                    run = b.saved.sweep.run_single_distance_ao(distance_km=L,start_id=start_id,
                        start_nu=n,start_va=v,objective=objective,max_iterations=b.saved.ao.MAX_AO_ITERATIONS)
                # A second original invocation confirms a closed run without changing its stop rule.
                if run['status'] == 'CONVERGED_NUMERICALLY' and len(run['iterations']) < 2:
                    final = run['final']
                    with patch.object(b.saved.sweep,'adaptive_maximize_1d',observed_search):
                        confirm = b.saved.sweep.run_single_distance_ao(distance_km=L,start_id=start_id+'_confirmation',
                            start_nu=final['nu_raw'],start_va=final['V_A'],objective=objective,
                            max_iterations=b.saved.ao.MAX_AO_ITERATIONS)
                    run['confirmation_original_run'] = confirm
                    run['iterations'] += confirm['iterations']; run['warnings'] += confirm['warnings']
                    run['final'] = confirm['final']; run['status'] = confirm['status']
                initial = objective(n,v)
                run.update(stage=stage,epoch=epoch,L_km=L,initial=initial,searches=searches,
                    classification=convergence(run),numerical_error_bound_available=False)
                runs.append(run)
                JSON(OUT / 'iteration_checkpoint.json',dict(stage=stage,epoch=epoch,runs=runs,requests=requests))
            local = [r for r in runs if r['L_km']==L and r['final'] is not None]
            winner = max(local,key=lambda r:r['final']['SKR'])
            final = winner['final']; previous = baseline[L]
            comparisons.append(dict(L_km=L,nu_raw=final['nu_raw'],V_A=final['V_A'],SKR=final['SKR'],
                catalog_nu_raw=previous['nu_raw'],catalog_V_A=previous['V_A'],catalog_SKR=previous['SKR'],
                delta_K=final['SKR']-previous['SKR'],relative_gain_percent=100*(final['SKR']-previous['SKR'])/previous['SKR'] if previous['SKR']>0 else '',
                iterations=len(winner['iterations']),classification=winner['classification'],
                winner_start=winner['start_id'],catalog_maximum_current=maximum['SKR'],
                retained_catalog_incumbent=final['SKR'] < maximum['SKR'],new_AP_attempts=state['AP_attempts']))
    result = dict(stage=stage,epoch=epoch,runs=runs,requests=requests,comparisons=comparisons,execution_ledger=ledger,
        best=max((r['final'] for r in runs if r['L_km']==b.saved.REF),key=lambda r:r['SKR']) if stage==1 else None,
        cache_hits=sum(r['cache_hits'] for r in runs),new_AP_in_child=0)
    JSON(OUT / f'stage{stage}_analysis.json',result)
    JSON(OUT / f'analysis_stage{stage}_epoch{epoch}.json',result)
    trajectories=[dict(stage=stage,epoch=epoch,**it) for r in runs for it in r['iterations']]
    append_csv('reference_alt_opt_trajectories.csv' if stage==1 else 'distance_alt_opt_trajectories.csv',trajectories)
    append_csv('objective_c_execution_ledger.csv', ledger)
    CSV(OUT / ('reference_alt_opt_comparison.csv' if stage==1 else 'distance_alt_opt_results.csv'), comparisons if stage==2 else [
        dict(start_id=r['start_id'],start_nu=r['start_nu'],start_V_A=r['start_V_A'],
            final_nu=r['final']['nu_raw'],final_V_A=r['final']['V_A'],SKR=r['final']['SKR'],
            gain_from_start=r['final']['SKR']-r['initial']['SKR'],gain_from_catalog=r['final']['SKR']-baseline[b.saved.REF]['SKR'],
            completed_iterations=len(r['iterations']),classification=r['classification'],original_status=r['status']) for r in runs])
    CSV(OUT / 'convergence_diagnostics.csv',[dict(stage=stage,epoch=epoch,L_km=r['L_km'],start_id=r['start_id'],
        classification=r['classification'],original_status=r['status'],searches=r['searches'],error_bound='UNAVAILABLE') for r in runs])
    if stage==2:
        CSV(OUT / 'catalog_vs_alt_opt_26_distances.csv',comparisons)
    print(f'CACHE_ONLY_STAGE_{stage}_EPOCH_{epoch}: runs={len(runs)},missing_requests={len(requests)}',flush=True)
    return 0


def choose_request(analysis, state, bank):
    attempted = {b.saved.pair(r['nu_raw'],r['V_A']) for r in state['sources']}
    blocked = {tuple(p) for p in state['historical_failed_pairs']}
    grouped = {}
    for request in analysis['requests']:
        key = b.saved.pair(request['nu_raw'],request['V_A'])
        if key in bank or key in attempted or key in blocked:
            continue
        grouped.setdefault(key,[]).append(request)
    if not grouped:
        return None
    # Prefer exact requests near an evaluated basin, shared across runs/distances.
    last_coordinate = state['sources'][-1].get('coordinate') if state['sources'] else None
    def priority(group):
        closest = min(abs(r['current_catalog_K']-r['coordinate_best_K']) for r in group)
        alternate = 0 if group[0]['coordinate'] != last_coordinate else 1
        return (closest, alternate, -len({r['L_km'] for r in group}), -len(group))
    group = min(grouped.values(),key=priority)
    return {**group[0], 'request_origins':group}


def supervised(phase, state, deadline, row=None):
    directory = b.stage_path(row) if row else OUT
    limit = min(b.SOURCE_OUTER if phase=='source' else (1200. if phase=='analyze' else b.POST_OUTER),
                deadline-time.monotonic()-RESERVE)
    assert limit>0
    command=[sys.executable,'-B','-X','utf8','-u',str(Path(__file__).resolve()),'--child',phase]
    with (directory / (phase+'.log')).open('w',encoding='utf-8') as log:
        receipt=b.original.checked_supervised_process(command,limit,log)
    JSON(directory / (phase+'_supervision.json'),receipt)
    state['supervision_receipts'].append(receipt)
    if row is not None:
        row['supervision_receipts'].append(receipt)
    assert b.safety_ok(receipt), 'MANDATORY_ACTUAL_JOB_POWER_SLEEP_SAFETY_FAILED'
    return receipt


def objective_child():
    verify(); state=READ(STATE); row=state['sources'][-1]; stage=b.stage_path(row)
    b.prior.torch.set_num_threads(1)
    with ExitStack() as guards:
        for obj,name in ((b.saved.ao.ExactMBEvaluator,'source_moments'),(b.prior.gram_moments,'_fallback'),(b.saved.sweep,'make_channel')):
            guards.enter_context(patch.object(obj,name,b.prior.preparation.forbidden))
        outputs=[]
        for entry in READ(OUT / 'expanded_objectives.json'):
            objective=make_objective(entry)
            result=objective(row['nu_raw'],row['V_A'])
            assert result['status']=='PASS' and result['SKR']==result['beta_I_AB']-result['chi_BE']
            assert result['source_cache_key']==row['resolved_source_cache_key']
            outputs.append(result); CSV(stage / 'new_exact_skr_26_distances.csv',outputs)
        assert [r['L_km'] for r in outputs]==list(b.saved.sweep.DISTANCES_KM)
        JSON(stage / 'validated_objectives.json',outputs)
    return 0


def source_child():
    verify(); state=READ(STATE); row=state['sources'][-1]
    assert row['status']=='RUNNING' and row['attempt_number']==1
    stage=b.stage_path(row)
    context=SimpleNamespace(OUT=stage,storage=b.original.prep.storage,provenance=b.original.prep.provenance)
    with patch.multiple(b.original,prep=context,NU=row['nu_raw'],VA=row['V_A'],KEY=row['source_cache_key'],OUT=stage,CACHE=CACHE):
        return b.original.source_child()


def render_and_report(state):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    plt.rcParams.update({'font.family':'serif','pdf.fonttype':42})
    ref=READ(OUT/'stage1_analysis.json') if (OUT/'stage1_analysis.json').exists() else None
    dist=READ(OUT/'stage2_analysis.json') if (OUT/'stage2_analysis.json').exists() else None
    figures=[]
    if ref:
        fig,ax=plt.subplots(layout='constrained')
        for run in ref['runs']:
            ax.plot(range(1,len(run['iterations'])+1),[r['K_after_nu'] for r in run['iterations']],marker='o',label=run['start_id'])
        ax.set(xlabel='ALT_OPT iteration',ylabel='Secret Key Rate (bits/use)',title='Reference multi-start ALT_OPT');ax.legend();figures.append(('reference_multistart_convergence',fig))
    if dist:
        rows=dist['comparisons'];fig,ax=plt.subplots(layout='constrained')
        ax.plot([r['L_km'] for r in rows],[r['catalog_SKR'] for r in rows],marker='o',label='Objective B catalog')
        ax.plot([r['L_km'] for r in rows],[max(r['SKR'],r['catalog_maximum_current']) for r in rows],marker='x',linestyle='--',label='ALT_OPT + retained catalog incumbent')
        unresolved=[r for r in rows if r['classification']!='NUMERICALLY_CONVERGED_ON_TESTED_MESH']
        ax.scatter([r['L_km'] for r in unresolved],[max(r['SKR'],r['catalog_maximum_current']) for r in unresolved],facecolors='none',edgecolors='red',label='Unresolved')
        ax.set(xlabel='Link Distance (km)',ylabel='Secret Key Rate (bits/use)',title='SKR versus Link Distance');ax.legend();figures.append(('skr_vs_link_distance',fig))
        fig,axes=plt.subplots(2,1,sharex=True,layout='constrained')
        for ax,key,label in zip(axes,('nu_raw','V_A'),('MB shaping parameter','Modulation variance (SNU)')):
            ax.plot([r['L_km'] for r in rows],[r[key] for r in rows],marker='o');ax.set_ylabel(label)
        axes[-1].set_xlabel('Link Distance (km)');figures.append(('optimal_parameters_vs_distance',fig))
    for name,fig in figures:
        fig.savefig(OUT/(name+'.png'),dpi=400);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)
    bank=b.cache_bank(b.saved.source.unconstrained_config())
    CSV(OUT/'expanded_exact_source_catalog.csv',[dict(nu_raw=float.fromhex(key[0]),V_A=float.fromhex(key[1]),
        source_cache_key=v['payload']['cache_key'],C=v['payload']['C'],w=v['payload']['w'],source_path=v['path']) for key,v in bank.items()])
    summary=dict(status=state['status'],AP_attempts=state['AP_attempts'],
        successes=sum(r['status']=='VALIDATED_SUCCESS' for r in state['sources']),
        timeouts=sum(r['status']=='TIMEOUT' for r in state['sources']),
        failures=sum(r['status']=='FAILED' for r in state['sources']),catalog_size=len(bank),
        reference=ref['best'] if ref else None,stage2_completed=bool(dist),
        measured_job_CPU_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in state['supervision_receipts']),
        controller_CPU_seconds=time.process_time(),wall_seconds=time.monotonic()-ORIGIN,
        outer_Sleep_lease=state.get('outer_Sleep_lease'),scientific_methods_changed=False,
        global_optimum_certified=False,total_error_bound_available=False,
        nu_zero_boundary=state['nu_zero_boundary'],all_actual_jobs_empty_closed=all(b.safety_ok(r) for r in state['supervision_receipts']))
    JSON(OUT/'final_report.json',summary)
    JSON(OUT/'report_payload.json',dict(summary=summary,reference=ref,distances=dist))
    report = '# Objective C: multi-start ALT_OPT\n\n'+b.original.prep.storage.checked_json(summary)
    report += '\n\nOriginal AO defaults unchanged. Mesh convergence is conditional on unbounded total numerical error; no global certificate.\n'
    report += '\nStage 1 comparison: reference_alt_opt_comparison.csv. Stage 2 comparison: catalog_vs_alt_opt_26_distances.csv.\n'
    report += '\nFull trajectories, coordinate histories and request origins are in analysis_stage*_epoch*.json. Never interpret exhausted source budgets or catalog agreement as closure.\n'
    (OUT/'objective_c_report.md').write_text(report,encoding='utf-8')


def run(approved=False):
    if not approved:
        raise SystemExit('AP NOT_RUN: explicit Objective C authorization required')
    state=preflight() if not OUT.exists() else READ(STATE)
    assert state['authorization'] is None, 'No duplicate or automatic restart'
    origin=datetime.datetime.now(datetime.timezone.utc)
    deadline=ORIGIN+TOTAL
    state.update(controller_pid=os.getpid(),status='STAGE1_INITIAL_ALT_OPT',supervision_receipts=[],
        authorization=dict(origin_UTC=origin.isoformat(),deadline_UTC=(origin+datetime.timedelta(seconds=deadline-time.monotonic())).isoformat(),
            maximum_AP_attempts=36,stage1_ceiling=12,stage2_initial_ceiling=24,internal_timeout_seconds=3600,
            total_seconds=TOTAL,reserve_seconds=RESERVE,parallel_workers=1,no_retry=True))
    save(state);lease=b.prior.safe.AwakeOnAC()
    try:
        with lease:
            for stage in (1,2):
                state.update(stage=stage,status=f'STAGE{stage}_ALT_OPT')
                while True:
                    verify();save(state)
                    receipt=supervised('analyze',state,deadline)
                    assert receipt['returncode']==0 and not receipt['deadline_exceeded'],'ANALYSIS_FAILED'
                    analysis=READ(OUT/f'stage{stage}_analysis.json'); state['epochs']+=1;save(state)
                    if state['AP_attempts']>=MAX_AP or (stage==1 and state['stage1_attempts']>=STAGE1_AP):
                        break
                    if deadline-time.monotonic()<b.SOURCE_OUTER+1200.+RESERVE:
                        state['status']='BUDGET_EXHAUSTED';break
                    bank=b.cache_bank(b.saved.source.unconstrained_config())
                    request=choose_request(analysis,state,bank)
                    if request is None:
                        break
                    n,v=request['nu_raw'],request['V_A']
                    evaluator=b.saved.ao.ExactMBEvaluator(b.saved.source.unconstrained_config(),
                        {'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},OUT,source_cache_dir=CACHE,allow_legacy_exact_import=False)
                    identity=evaluator._source_identity(b.saved.source.make_ensemble(b.saved.source.unconstrained_config(),'MB',n,v),n,v)
                    row=dict(request,index=len(state['sources'])+1,stage=stage,attempt_number=1,status='RUNNING',
                        started_UTC=b.utc(),source_cache_key=b.saved.ao.json_hash(identity),original_source_identity=identity,
                        nu_raw_hex=float(n).hex(),V_A_hex=float(v).hex(),source_validation='NOT_RUN',
                        SKR_status='PENDING',supervision_receipts=[],C='',w='',error='')
                    state['sources'].append(row);state['AP_attempts']+=1;state[f'stage{stage}_attempts']+=1
                    directory=b.stage_path(row);directory.mkdir()
                    JSON(directory/'protected_input_manifest.json',READ(OUT/'protected_input_manifest.json'))
                    JSON(directory/'confirmed_candidate.json',{'original_source_identity':identity})
                    JSON(directory/'execution_authorization.json',dict(maximum_attempts=1,source_cache_key=row['source_cache_key']))
                    JSON(directory/'source_attempt_started.json',dict(attempt_number=1));save(state)
                    print(f'STAGE{stage}_AP_STARTED {state["AP_attempts"]}/36: ({n!r},{v!r});internal3600s',flush=True)
                    started=time.monotonic()
                    try:
                        receipt=supervised('source',state,deadline,row)
                        result=READ(directory/'source_result.json') if (directory/'source_result.json').exists() else {}
                        if receipt['deadline_exceeded'] or result.get('status')=='TIMEOUT_INTERNAL_EVALUATOR':
                            row.update(status='TIMEOUT',SKR_status='NOT_RUN',error=result.get('error','SUPERVISOR_TIMEOUT'))
                        elif receipt['returncode']!=0 or result.get('status')!='COMPLETED_EXACT':
                            row.update(status='FAILED',SKR_status='NOT_RUN',error=result.get('error','SOURCE_FAILED'))
                            if any(s in row['error'].upper() for s in ('PROVENANCE','IDENTITY','INCOMPATIBLE','CORRUPT')):
                                raise RuntimeError('MANDATORY_PROVENANCE_FAILED')
                        else:
                            b.validate_source(row);save(state)
                            receipt=supervised('objectives',state,deadline,row)
                            assert receipt['returncode']==0 and not receipt['deadline_exceeded'],'SOURCE_VALID_OBJECTIVES_FAILED'
                            entries=READ(OUT/'expanded_objectives.json'); values=READ(directory/'validated_objectives.json')
                            for entry,value in zip(entries,values):
                                assert entry['L_km']==value['L_km'];entry['rows'].append(value)
                            JSON(OUT/'expanded_objectives.json',entries)
                            row.update(status='VALIDATED_SUCCESS',SKR_status='VALIDATED_26_DISTANCES')
                    finally:
                        row.update(finished_UTC=b.utc(),wall_seconds=time.monotonic()-started,
                            CPU_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in row['supervision_receipts']),
                            worker_cleanup='VERIFIED_EMPTY_CLOSED' if row['supervision_receipts'] and all(b.safety_ok(r) for r in row['supervision_receipts']) else 'UNVERIFIED')
                        save(state)
                        append_csv('objective_c_execution_ledger.csv',[dict(row,event='NEW_SOURCE_OUTCOME',cache_hit=False,
                            new_AP_attempt=True,previous_incumbent=request['current_catalog_K'],updated_incumbent='SEE_26_DISTANCE_VALIDATED_OBJECTIVES')])
                    print(f'AP_SAVED: {row["status"]}; ({n!r},{v!r});C={row["C"]};w={row["w"]}',flush=True)
                if state['status']=='BUDGET_EXHAUSTED':
                    break
            else:
                state['status']='AUTHORIZED_STAGES_COMPLETE_WITH_REPORTED_UNRESOLVED_DIRECTIONS'
    except BaseException as error:
        state.update(status='SAFETY_ABORT',error=f'{type(error).__name__}: {error}')
        for row in state['sources']:
            if row['status']=='RUNNING':row.update(status='SAFETY_ABORT',error=state['error'])
    finally:
        state.update(controller_pid=0,outer_Sleep_lease=lease.receipt,wall_seconds=time.monotonic()-ORIGIN)
        save(state)
        try:
            verify();render_and_report(state)
        except BaseException as error:
            JSON(OUT/'finalization_failure.json',dict(error=f'{type(error).__name__}: {error}',scientific_results_preserved=True))
        state['wall_seconds_including_finalization']=time.monotonic()-ORIGIN
        if state['wall_seconds_including_finalization']>TOTAL:state['status']='FAILED_TOTAL_WALL_OVERRUN'
        save(state)
    return 0 if state['status'].startswith('AUTHORIZED_STAGES_COMPLETE') else 2


if __name__=='__main__':
    b.OUT,b.CACHE=OUT,CACHE
    parser=argparse.ArgumentParser();parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--approved-objective-c',action='store_true')
    parser.add_argument('--child',choices=['source','objectives','analyze'])
    args=parser.parse_args()
    if args.child:
        raise SystemExit({'source':source_child,'objectives':objective_child,'analyze':analyze_child}[args.child]())
    if args.preflight_only:
        preflight();raise SystemExit(0)
    raise SystemExit(run(approved=args.approved_objective_c))
