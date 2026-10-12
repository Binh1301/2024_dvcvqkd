"""One explicitly approved A pilot; new validated v2 entry, original science/AO."""
import argparse
from collections import Counter
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

# Budget starts with this new controller process, includes imports and preflight.
PROCESS_ORIGIN=time.monotonic()
PROCESS_UTC=datetime.now(timezone.utc)
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import observer_v2_recovery_entry as entry
from scripts import windows_sleep_safe_supervision as safe
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source
from scripts import audit_theta10_D55_ao_numerical_optimum as audit
from scripts import recover_theta10_D55_observer_v2 as recovery
from scripts.exact_cache_provenance import verify_source_payload,source_settings,json_hash
from scripts.overnight_source_observer import atomic_json
from scripts.diagnose_theta10_D55_source_bottlenecks import read,rows,digest,clean
from src.cvqkd import gram_moments
from src.modulation.qam256 import c4_orbit_indices

RECOVERY=ROOT/'results/theta10_D55_ao_numerical_optimum_validation/observer_v2_recovery'
BASE=RECOVERY.parent/'overnight_ao_run'  # Saved scientific data ONLY, never old controller.
OUT=RECOVERY/'controlled_probe_A_20261010'
PAIR=(.165,5.49375)
KEY='db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59'
REF=21.9393102292
DIRS=tuple(ROOT/'results'/p/'exact_source_cache' for p in (
    'exact_mb_test2','theta10_D55_alt_opt_closure_continuation',
    'theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run',
    'theta10_D55_mb_exact_targeted_expansion/batch_2','theta10_D55_mb_exact_targeted_expansion/batch_3',
    'theta10_D55_ao_numerical_optimum_validation/phase_2A'))+(OUT/'exact_source_cache',)


def save(name,value):atomic_json(OUT/name,clean(value))


def csv(name,data):
    import csv as c
    fields=list(dict.fromkeys(k for r in data for k in r)) or ['status','note']
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        writer=c.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:json.dumps(clean(v)) if isinstance(v,(dict,list)) else clean(v) for k,v in r.items()} for r in data)


def workers():
    command="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--approved-ap|--source-child|--probe|--profile-worker|full_support_c4_worker\\.py|observer_v2_recovery_entry\\.py.*--dummy-mode'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
    result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    return json.loads(result.stdout) if result.stdout.strip() else []


def remaining(auth):
    return min(auth['overall_deadline_monotonic']-time.monotonic(),
      (datetime.fromisoformat(auth['overall_deadline_utc'])-datetime.now(timezone.utc)).total_seconds())


def verify_inputs():
    manifest=read(OUT/'protected_input_manifest.json')
    for name,expected in manifest.items():assert digest(ROOT/name)==expected,name
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES,ao.MAX_BOUNDARY_EXPANSIONS)==(1e-8,1e-6,6,4,3)
    return len(manifest)


def request_and_identity():
    config=source.unconstrained_config();ensemble=source.make_ensemble(config,'MB',*PAIR)
    evaluator=ao.ExactMBEvaluator(config,{'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},OUT,
        source_cache_dir=OUT/'exact_source_cache',allow_legacy_exact_import=False)
    identity=evaluator._source_identity(ensemble,*PAIR);assert json_hash(identity)==KEY
    indices=c4_orbit_indices();p=ensemble.probabilities[0,indices[:,0]];z=ensemble.amplitudes[0,indices[:,0]]
    request={'probabilities_float64_hex':[float(x).hex() for x in p.tolist()],
      'prototypes_float64_hex':[[complex(x).real.hex(),complex(x).imag.hex()] for x in z.tolist()],
      'precision_ladder_decimal_digits':list(gram_moments.PRECISION_LADDER)}
    return config,ensemble,evaluator,identity,request


class ObserverHealth:
    def __init__(self,prefix,clock=time.monotonic,grace=30):
        self.prefix=Path(prefix);self.clock=clock;self.grace=grace;self.last=clock();self.counter=-1
    def check(self):
        result_path=Path(str(self.prefix)+'_worker_result.json')
        if result_path.exists() and read(result_path).get('status')=='INSTRUMENTATION_FAILURE':
            raise RuntimeError('OBSERVER_INSTRUMENTATION_FAILURE')
        path=Path(str(self.prefix)+'_stage_snapshot.json')
        if path.exists():
            data=read(path)
            if data.get('observer_error'):raise RuntimeError('OBSERVER_INSTRUMENTATION_FAILURE: '+str(data['observer_error']))
            if data['snapshot_count']!=self.counter:
                self.counter=data['snapshot_count'];self.last=self.clock()
            if data['finished']:return
        if self.clock()-self.last>self.grace:raise RuntimeError('OBSERVER_MONITORING_HEARTBEAT_LOST')


def watched_power(prefix):
    Native=safe.WindowsPower
    class WatchedPower(Native):
        def __init__(self):super().__init__();self.observer_health=ObserverHealth(prefix)
        def read(self):
            status=super().read();self.observer_health.check();return status
    return WatchedPower


def source_child():
    """Original source_moments and original fallback request; ONLY observer launch changes."""
    import torch
    torch.set_num_threads(1);verify_inputs()
    auth=read(OUT/'execution_authorization.json');config,ensemble,evaluator,identity,request=request_and_identity()
    assert json_hash(request)==auth['request_sha256']
    real_run=subprocess.run
    def approved_entry(command,*args,**kwargs):
        if isinstance(command,(tuple,list)) and len(command)>1 and Path(command[1]).name=='full_support_c4_worker.py':
            assert json_hash(json.loads(kwargs['input']))==auth['request_sha256']
            command=[sys.executable,'-B','-X','utf8','-u',str(Path(entry.__file__)),
                '--approved-ap','--authorization',str(OUT/'execution_authorization.json'),
                '--prefix',str(OUT/'probe_results'/KEY)]
            kwargs['timeout']=max(1.,min(auth['deadline_monotonic']-time.monotonic()-8,
                                       auth['probe_wall_limit_seconds']-8))
        return real_run(command,*args,**kwargs)
    original_evaluator=evaluator.source_evaluator
    def capture(*args,**kwargs):
        result=original_evaluator(*args,**kwargs)
        save('source_numerical_diagnostics.json',list(result.diagnostics));return result
    evaluator.source_evaluator=capture
    started=time.monotonic();cpu=time.process_time()
    try:
        with patch.object(gram_moments.subprocess,'run',approved_entry):
            payload=evaluator.source_moments(ensemble,*PAIR)
        proof=verify_source_payload(payload,source_settings(config))
        result={'status':'SUCCESS','nu_raw':PAIR[0],'V_A':PAIR[1],'source_cache_key':KEY,
          'C':payload['C'],'w':payload['w'],'source_path':str((OUT/'exact_source_cache'/(KEY+'.json')).relative_to(ROOT)),
          'provenance':proof,'source_support_size':payload['support_size']}
    except Exception as exc:
        worker=read(OUT/'probe_results'/(KEY+'_worker_result.json')) if (OUT/'probe_results'/(KEY+'_worker_result.json')).exists() else None
        if worker:status=worker['status'] if worker['status'] in ('INSTRUMENTATION_FAILURE','NUMERICAL_FAILURE') else 'NUMERICAL_FAILURE'
        elif 'timeout' in str(exc).lower():status='TIMEOUT'
        else:status='INSTRUMENTATION_FAILURE'
        result={'status':status,'error':repr(exc),'worker_result':worker}
    result.update(ended_utc=datetime.now(timezone.utc).isoformat(),parent_wall_seconds=time.monotonic()-started,
                  parent_process_CPU_seconds=time.process_time()-cpu)
    save('source_result.json',result);print(json.dumps({k:result.get(k) for k in ('status','C','w','error')}),flush=True)
    return 0 if result['status']=='SUCCESS' else 1


def process_success():
    """Original exact objective, original AO/multistart/warm search; implicit AP forbidden."""
    import torch
    torch.set_num_threads(1);verify_inputs()
    config=source.unconstrained_config();bank=source.load_source_payloads(config,DIRS)
    mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    assert len(mb)==148 and source.candidate_from_payload(config,bank,'MB',*PAIR)
    baseline=read(BASE/'objective_checkpoint.json')
    old={float(r['L_km']):r for r in rows(BASE/'optimized_skr_26_distances.csv')}
    before_pairs={(float(r['nu_raw']).hex(),float(r['V_A']).hex()) for r in baseline['20.0']['rows']}
    assert {(p['nu_mb_raw_hex'],p['V_A_hex']) for p in mb}-before_pairs=={(PAIR[0].hex(),PAIR[1].hex())}
    csv('expanded_source_catalog.csv',[{'nu_raw':float.fromhex(p['nu_mb_raw_hex']),'V_A':float.fromhex(p['V_A_hex']),
      'C':p['C'],'w':p['w'],'source_cache_key':p['cache_key'],'ensemble_hash':p['ensemble_hash'],'provenance':p['_provenance']['status']} for p in mb])
    matrices,metrics,selections,comparisons,runs,searches,objects={},[],[],[],[],[],{}
    original_search=ao.adaptive_maximize_1d
    def record_search(**kw):
        result=original_search(**kw);searches.append({'L_km':kw['objective'].channel['distance_km'],**result});return result
    warm=None
    with patch.object(ao.ExactMBEvaluator,'source_moments',audit.forbidden),patch.object(gram_moments,'_fallback',audit.forbidden), \
         patch.object(ao,'adaptive_maximize_1d',record_search),patch.object(sweep,'adaptive_maximize_1d',record_search):
        for distance in sweep.DISTANCES_KM:
            obj=ao.ExactObjective(config,sweep.make_channel(config,distance),OUT,allow_new_source=False,source_cache_dirs=DIRS)
            cache=baseline[str(distance)];assert obj.restore_objective_rows(cache['rows'],cache['identity'])==147
            for p in mb:
                n,v=float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex']);obj.register_catalog(n,v);obj(n,v)
            metrics.append(obj(*PAIR));ranked=sorted(obj.rows.values(),key=lambda r:r['SKR'],reverse=True)
            assert len(ranked)==148
            matrices[str(distance)]={'identity':obj.objective_identity,'rows':list(obj.rows.values())};objects[distance]=obj
            save('objective_checkpoint.json',matrices);csv('new_exact_skr_26_distances.csv',metrics)
            starts=[(f'nu_{n:g}',n,None) for n in sweep.BASE_STARTS]
            if warm:starts.append(('warm_previous_distance',*warm))
            actual=[sweep.run_single_distance_ao(distance_km=distance,start_id=sid,start_nu=n,start_va=v,
                    objective=obj,max_iterations=ao.MAX_AO_ITERATIONS) for sid,n,v in starts]
            chosen=max((r for r in actual if r['final']),key=lambda r:r['final']['SKR']);final=chosen['final']
            warm=(float(final['nu_raw']),float(final['V_A']))
            checks=[record_search(variable=v,fixed=f,values=obj.catalog_values(v,f),objective=obj)
                    for v,f in (('V_A',warm[0]),('nu_raw',warm[1]))]
            selections.append({'L_km':distance,'nu_raw':warm[0],'V_A':warm[1],'I_AB':final['I_AB'],'beta_I_AB':final['beta_I_AB'],
               'chi_BE':final['chi_BE'],'K':final['SKR'],'selected_start':chosen['start_id'],'AO_status':chosen['status'],
               'coordinate_complete':all(ao.coordinate_search_complete(s) for s in checks),
               'matches_catalog_maximum':final['SKR']==ranked[0]['SKR'],'source_cache_key':final['source_cache_key'],
               'claim':'FINITE_CATALOG_BEST_OBSERVED_ONLY'})
            comparisons.append({'L_km':distance,'old_nu':old[distance]['nu_raw'],'old_V_A':old[distance]['V_A'],'old_K':old[distance]['K'],
               'new_nu':ranked[0]['nu_raw'],'new_V_A':ranked[0]['V_A'],'new_K':ranked[0]['SKR'],
               'delta_K':ranked[0]['SKR']-float(old[distance]['K']),'runner_up_K':ranked[1]['SKR'],
               'top_two_gap':ranked[0]['SKR']-ranked[1]['SKR'],'accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'})
            runs.extend({'L_km':distance,**r} for r in actual)
            save('cache_only_runs.json',runs);save('cache_only_searches.json',searches)
            csv('optimized_skr_26_distances.csv',selections);csv('old_vs_new_optimization.csv',comparisons)
            print(f'Pilot L={distance}, MB=148, K={ranked[0]["SKR"]}, AO match={final["SKR"]==ranked[0]["SKR"]}',flush=True)
    aligned,finals=audit.align_searches(runs,searches)
    save('aligned_search_history.json',aligned)
    csv('coordinate_search_completion.csv',[audit.diagnostic(s,matrices[str(d)]['rows']) for d,ss in finals.items() for s in ss])
    csv('ao_multistart_history.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],**it} for r in runs for it in r['iterations']])
    missing={}
    for s in aligned:
        for e in s['source_missing']:
            n,v=(s['fixed'],e['value']) if s['variable']=='V_A' else (e['value'],s['fixed'])
            row=missing.setdefault((float(n).hex(),float(v).hex()),{'nu_raw':n,'V_A':v,'nu_raw_hex':float(n).hex(),'V_A_hex':float(v).hex(),'requests':[]})
            row['requests'].append({k:s[k] for k in ('L_km','variable','start_id','iteration','role')})
    csv('remaining_source_dependencies.csv',list(missing.values()))
    targeted=[]
    for variable,fixed,label in (('V_A',.165,'P1'),('nu_raw',5.5,'P2')):
        obj=objects[REF];s=original_search(variable=variable,fixed=fixed,values=obj.catalog_values(variable,fixed),objective=obj)
        targeted.append({'L_km':REF,'label':label,**s})
        exact=sorted((r for r in obj.rows.values() if float(r['nu_raw' if variable=='V_A' else 'V_A']).hex()==fixed.hex()),key=lambda r:r[variable])
        csv('reference_'+label+'_trace.csv',[{**r,'K':r['SKR'],'post_search_status':s['status']} for r in exact])
    save('reference_targeted_coordinate_searches.json',targeted)
    independent=[]
    for d in sweep.DISTANCES_KM:
        saved=matrices[str(d)];verify=ao.ExactObjective(config,saved['identity']['identity']['channel'],OUT,
                   allow_new_source=False,source_cache_dirs=DIRS)
        assert verify.restore_objective_rows(saved['rows'],saved['identity'])==148
        best=max(verify.rows.values(),key=lambda r:r['SKR']);selected=next(r for r in selections if r['L_km']==d)
        independent.append({'L_km':d,'catalog_K':best['SKR'],'AO_K':selected['K'],'AO_matches_catalog':best['SKR']==selected['K'],
             'rows':148,'identity_sha256':verify.context_hash})
    csv('independent_catalog_verification.csv',independent)
    prior=read(BASE/'reference_targeted_coordinate_searches.json');progress=[]
    for before,after in zip(prior,targeted):
        recovered=[e['value'] for e in before['source_missing'] if (float(before['fixed']).hex(),float(e['value']).hex())==(PAIR[0].hex(),PAIR[1].hex()) and before['variable']=='V_A']
        progress.append({'coordinate':after['label'],'old_bracket':before['bracket'],'new_bracket':after['bracket'],
             'old_best_value':before['best_value'],'new_best_value':after['best_value'],
             'prior_missing_now_measured':recovered,'prior_pair_covered':len(recovered)==2,
             'current_call_attempted_stages':after['refinement_stages'],
             'current_call_completed_pairs':after['refinement_stages']-int(after['refinement_status']=='SOURCE_MISSING_REFINEMENT'),
             'status':after['status'],'next_missing':after['source_missing']})
    save('postprocess_report.json',{'MB_count':148,'new_metric_rows':len(metrics),
        'reference':next(r for r in comparisons if r['L_km']==REF),'at22km':next(r for r in comparisons if r['L_km']==22.),
        'improved_distances':[r['L_km'] for r in comparisons if r['delta_K']>0],
        'AO_catalog_matches':sum(r['AO_matches_catalog'] for r in independent),
        'AO_starts':len(runs),'AO_iterations':sum(len(r['iterations']) for r in runs),
        'closed_selected_directions':sum(ao.coordinate_search_complete(s) for ss in finals.values() for s in ss),
        'unique_missing_pairs':len(missing),'reference_progress':progress,
        'final_reference_coordinate_searches':finals[REF],'coordinate_status_counts':dict(Counter(s['status'] for s in searches))})
    verify_inputs();return 0


def profile_summary():
    path=OUT/'probe_results'/(KEY+'_stage_snapshot.json')
    if not path.exists():return {'coverage':'NO_AP_OBSERVATIONS','bottleneck':'BOTTLENECK_NOT_LOCALIZED'}
    data=read(path);groups={}
    for r in data['completed_stages']:
        g=groups.setdefault(r['name'],{'completed_calls':0,'wall_seconds_exclusive':0.,'CPU_seconds_exclusive':0.})
        g['completed_calls']+=int(r['completed_normally']);g['wall_seconds_exclusive']+=r['wall_seconds_exclusive'];g['CPU_seconds_exclusive']+=r['CPU_seconds_exclusive']
    csv('profiling_stage_summary.csv',[{'stage':name,**v} for name,v in groups.items()])
    deepest=data['open_stages'][-1] if data['open_stages'] else None
    complete=data['finished'] and not data.get('observer_error') and all(r['completed_normally'] for r in data['completed_stages'])
    leader=max(groups,key=lambda n:groups[n]['CPU_seconds_exclusive']) if groups else None
    summary={'mode':data['mode'],'coverage':'AP_WORKER_MAIN_STAGE_INTERVAL_VALID' if complete else 'PARTIAL_AP_STAGE_INTERVAL',
       'full_detailed_call_profile':False,'observer_snapshots':data['snapshot_count'],'worker_PID':data['pid'],
       'last_observed_wall_seconds':data['wall_seconds'],'last_observed_AP_process_CPU_seconds':data['process_cpu_seconds'],
       'dominant_completed_exclusive_CPU_stage':leader,'completed_stage_groups':groups,'unfinished_deepest_stage':deepest,
       'observed_snapshot_collector_thread_CPU_seconds':data['snapshot_CPU_seconds_measured'],
       'observed_snapshot_wall_seconds':data['snapshot_wall_seconds_measured'],
       'bottleneck':leader if complete and leader else 'BOTTLENECK_NOT_LOCALIZED',
       'limits':'Coverage only original AP worker main, not parent/setup/full cProfile. Completed exclusive times not summed with cumulative snapshots or open parent intervals. Collector measurement excludes last write/hook overhead; no total uninstrumented comparison.'}
    save('profiling_coverage_report.json',summary);return summary


def finish(ledger):
    post=read(OUT/'postprocess_report.json') if (OUT/'postprocess_report.json').exists() else None
    source_result=read(OUT/'source_result.json') if (OUT/'source_result.json').exists() else None
    summary={**ledger,'postprocess':post,'source_result':source_result,'profiling':profile_summary(),
       'protected_hashes_unchanged':verify_inputs(),'new_sources':int(ledger.get('source_status')=='SUCCESS'),
       'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','continuous_global_optimum':False,
       'scientific_or_AO_changes':False,'no_interpolation':True,'other_AP_attempts':0,
       'frozen_historical_hash_discrepancy':'PREEXISTING_UNCHANGED','lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    save('pilot_report.json',summary)
    lines=['# Controlled observer-v2 Probe A pilot','',ledger['status'],'',
      f"Source status={ledger.get('source_status')}; exactly{ledger.get('attempts',0)}attempt, no retries/B/P2.",
      f"Totalwall={ledger['total_wall_seconds']}s/5400, sourceceiling={ledger.get('source_wall_limit_seconds')}s<=4500, finalreserve900s.",
      f"Recordedcontroller+JobCPU={ledger['recorded_total_CPU_seconds']}s; excludes interactive implementation and independent checks outside controller."]
    if source_result:lines += ['',f'Source result: {source_result}']
    if post:lines += ['',f"Catalog={post['MB_count']}, newmetrics={post['new_metric_rows']}, improveddistances={post['improved_distances']}.",
      f"Reference={post['reference']}",f"22km={post['at22km']}",
      f"P1/P2={post['reference_progress']}",f"OriginalAO{post['AO_starts']}starts/{post['AO_iterations']}iterations; independentmatches{post['AO_catalog_matches']}/26; closedselecteddirections{post['closed_selected_directions']}.",
      f"Next current exactdependencies in remaining_source_dependencies.csv;{post['unique_missing_pairs']} unique missingpairs."]
    else:lines += ['', 'No completed new26distance/AO result; previous147catalog maxima remain baseline, not fresh convergence evidence.']
    lines += ['',f"Profiling={summary['profiling']}",
       f"Cleanup no worker={ledger['worker_cleanup_verified']}; Sleep restored={ledger['sleep_prevention'].get('released_verified')}; deadline respected={ledger['wall_budget_respected']}.",
       'Source refinement coverage and objective error/boundaries remain distinct. No numerical/global optimum claimed; unchanged inner4/outer6/epsilon1e-8/param1e-6.',
       'If successfulA is the only new point, a bracket side may narrow but old pairedP1 stage still lacks partner unless actual search says otherwise. No nextsource launched.',
       'Ponytail: original source/provenance/evaluator/AO/Job/Sleep reused; observer-v2 only, never overnight-v1 controller.',
       f"Error={ledger.get('error')}. Allpreviousscientificartifacts preserved."]
    (OUT/'pilot_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save('input_manifest_after.json',{n:digest(ROOT/n) for n in read(OUT/'protected_input_manifest.json')})


def run_approved():
    if OUT.exists():raise FileExistsError('Pilot output exists: never reset or retry')
    OUT.mkdir();(OUT/'exact_source_cache').mkdir();(OUT/'probe_results').mkdir()
    origin=PROCESS_ORIGIN;deadline=origin+5400
    auth={'status':'EXPLICITLY_APPROVED_CONTROLLED_PROBE_A_OBSERVER_V2',
       'controller_origin_monotonic':origin,'controller_origin_utc':PROCESS_UTC.isoformat(),
       'overall_deadline_monotonic':deadline,'overall_deadline_utc':(PROCESS_UTC+timedelta(seconds=5400)).isoformat(),
       'pair_hex':[PAIR[0].hex(),PAIR[1].hex()],'source_cache_key':KEY,'max_attempts':1,
       'total_budget_seconds':5400,'source_max_seconds':4500,'final_reserve_seconds':900,
       'old_overnight_budget_reused':False,'fresh_explicit_user_approval':True}
    manifest=read(RECOVERY/'protected_input_manifest.json')
    for p in RECOVERY.parent.rglob('*'):
        if p.is_file() and OUT not in p.parents:manifest[p.relative_to(ROOT).as_posix()]=digest(p)
    manifest.update({Path(__file__).relative_to(ROOT).as_posix():digest(Path(__file__)),
       'tests/test_controlled_observer_v2_pilot.py':digest(ROOT/'tests/test_controlled_observer_v2_pilot.py')})
    save('protected_input_manifest.json',manifest)
    ledger={'status':'APPROVED_PILOT_PREFLIGHT','controller_pid':os.getpid(),'attempts':0,'authorization':auth,
            'supervision_receipts':[],'source_status':'NOT_RUN','budget_reset':False}
    save('execution_authorization.json',auth);save('execution_ledger.json',ledger)
    cpu=time.process_time();lease=safe.AwakeOnAC();error=None
    try:
        assert read(RECOVERY/'observer_v2_recovery_report.json')['status']=='READY_FOR_CONTROLLED_AP_PILOT'
        assert not workers();verify_inputs()
        preflight_tests=[]
        for pattern in ('test_controlled_observer_v2_pilot.py','test_observer_v2_recovery.py','test_overnight_observer_integration.py','test_overnight_source_observer.py'):
            done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
            preflight_tests.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr});assert done.returncode==0,preflight_tests[-1]
        save('preflight_regression_tests.json',preflight_tests)
        # Refresh native wall/AC/gap tests in an isolated subdirectory; no AP.
        (OUT/'dummy').mkdir()
        with patch.object(recovery,'OUT',OUT):
            native=[recovery.native_case('deadline',duration=30,wall=3,inject='TIMEOUT'),
                    recovery.native_case('AC_loss',duration=30,wall=12,inject='AC'),
                    recovery.native_case('watchdog_gap',duration=30,wall=20,inject='WATCHDOG')]
        save('native_safety_preflight.json',native)
        config,ensemble,evaluator,identity,request=request_and_identity()
        bank=source.load_source_payloads(config,DIRS)
        assert len([p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0])==147
        assert source.candidate_from_payload(config,bank,'MB',*PAIR) is None
        assert safe.safe_power(safe.WindowsPower().read());time.sleep(.5);assert safe.safe_power(safe.WindowsPower().read())
        limit=min(4500.,remaining(auth)-900);assert limit>30
        auth.update(probe_wall_limit_seconds=limit,deadline_monotonic=time.monotonic()+limit,
           deadline_utc=(datetime.now(timezone.utc)+timedelta(seconds=limit)).isoformat(),request_sha256=json_hash(request))
        save('execution_authorization.json',auth);save('exact_source_request.json',request);save('exact_source_identity.json',identity)
        with lease:
            save('active_power_preflight.json',{'utc':datetime.now(timezone.utc).isoformat(),'power':safe.WindowsPower().read(),'lease':lease.receipt})
            verify_inputs();assert not workers()
            ledger.update(status='SOURCE_A_RUNNING',attempts=1,source_started_utc=datetime.now(timezone.utc).isoformat(),source_wall_limit_seconds=limit)
            save('execution_ledger.json',ledger)
            with (OUT/'source_A.log').open('w',encoding='utf-8') as log:
                with patch.object(safe,'WindowsPower',watched_power(OUT/'probe_results'/KEY)):
                    receipt=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--source-child'],limit,log)
            ledger['supervision_receipts'].append(receipt);save('source_supervision.json',receipt)
            assert not workers(),'Source worker remains after Job close'
            result=read(OUT/'source_result.json') if (OUT/'source_result.json').exists() else None
            ledger['source_status']=entry.classify(receipt,result)
            reason=receipt.get('power_watch',{}).get('abort_reason') or ''
            if 'OBSERVER_MONITORING' in reason:ledger['source_status']='WATCHDOG_ABORT'
            if 'OBSERVER_INSTRUMENTATION' in reason:ledger['source_status']='INSTRUMENTATION_FAILURE'
            ledger['source_wall_seconds']=receipt['measured_wall_seconds_including_cleanup'];save('execution_ledger.json',ledger)
            assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
            if ledger['source_status']=='SUCCESS':
                assert result and result['status']=='SUCCESS' and receipt['returncode']==0
                with (OUT/'postprocess.log').open('w',encoding='utf-8') as log:
                    receipt=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--postprocess'],remaining(auth)-180,log)
                ledger['supervision_receipts'].append(receipt);save('postprocess_supervision.json',receipt)
                assert receipt['returncode']==0 and receipt['wall_limit_respected'],'26distance/AO validation failed'
                ledger['status']='CONTROLLED_PILOT_SOURCE_SUCCESS_VALIDATED'
            else:ledger['status']='CONTROLLED_PILOT_STOPPED_'+ledger['source_status']
    except BaseException as exc:
        error=repr(exc);ledger['status']='CONTROLLED_PILOT_STOPPED_ERROR';print(error,flush=True)
    finally:
        ledger.update(error=error,ended_utc=datetime.now(timezone.utc).isoformat(),
           total_wall_seconds=time.monotonic()-origin,controller_CPU_seconds=time.process_time()-cpu,
           Job_CPU_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in ledger['supervision_receipts']),
           sleep_prevention=lease.receipt,worker_cleanup_verified=not workers(),wall_budget_respected=remaining(auth)>=0)
        ledger['recorded_total_CPU_seconds']=ledger['controller_CPU_seconds']+ledger['Job_CPU_seconds']
        save('execution_ledger.json',ledger);save('sleep_prevention_final_receipt.json',lease.receipt)
        finish(ledger)
        print(json.dumps({k:ledger[k] for k in ('status','source_status','attempts','total_wall_seconds','error')},indent=2),flush=True)
    return 1 if error else 0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-approved',action='store_true')
    parser.add_argument('--source-child',action='store_true');parser.add_argument('--postprocess',action='store_true')
    args=parser.parse_args()
    if args.source_child:return source_child()
    if args.postprocess:return process_success()
    if args.run_approved:return run_approved()
    parser.error('Explicit approved mode required')


if __name__=='__main__':raise SystemExit(main())
