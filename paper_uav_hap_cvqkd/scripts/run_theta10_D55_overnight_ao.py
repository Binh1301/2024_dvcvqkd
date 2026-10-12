"""Approved overnight execution glue; all science/AO calls use original routines."""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_ao_phase2a as original
from scripts import overnight_source_observer as observer

ao,io,source,sweep,safe=original.ao,original.io,original.source,original.sweep,original.safe
supervisor=original.supervisor
BASE=original.OUT
OUT=BASE.parent/'overnight_ao_run'
DIRS=(*original.DIRS,OUT/'exact_source_cache')
REF=21.9393102292
PAIRS=((.165,5.49375),(.165,5.50625),(.16531250000000003,5.5),(.16375,5.5))
LIMITS=(4500.,3600.,7200.,7200.)


def now_utc():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data):observer.atomic_json(path,data)
def key(n,v):return float(n).hex(),float(v).hex()


def write_csv(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r)) or ['status','note']
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def remaining(auth):
    utc=(datetime.fromisoformat(auth['deadline_utc'])-datetime.now(timezone.utc)).total_seconds()
    return min(auth['deadline_monotonic']-time.monotonic(),utc)


def workers():
    command="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--probe|--profile-worker|full_support_c4_worker\\.py|overnight_source_observer\\.py.*--ap'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
    result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    return json.loads(result.stdout) if result.stdout.strip() else []


def check_science():
    count=supervisor.verify_protected(OUT)
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,
            ao.MAX_REFINEMENT_STAGES,ao.MAX_BOUNDARY_EXPANSIONS)==(1e-8,1e-6,6,4,3)
    return count


def selected_points():
    return io.read_csv(OUT/'selected_exact_probes.csv')


def profile_probe(args):
    """Reuse original probe setup/source validation; replace ONLY observer launch."""
    validation=original.prep.native.supervisor.validation
    real_run=subprocess.run
    def redirect(command,*a,**kw):
        if isinstance(command,(tuple,list)) and '--profile-worker' in command:
            prefix=Path(command[command.index('--profile-worker')+1]).with_suffix('')
            command=[sys.executable,'-B','-X','utf8','-u',str(Path(observer.__file__)),
                     '--ap','--prefix',str(prefix)]
        return real_run(command,*a,**kw)
    args.output_dir=OUT
    with patch.object(validation.subprocess,'run',redirect):
        result=validation.probe_worker(args)
    # Existing source identity and precision untouched. Record actual observation mode.
    points=selected_points();point=next(p for p in points if key(p['nu_raw'],p['V_A'])==key(args.nu,args.va))
    path=OUT/'probe_results'/(point['source_cache_key']+'.json')
    record=read(path);record.update(observer_mode='LIGHTWEIGHT_EXECUTION_STAGE_TIMING',
        stage_snapshot=str((OUT/'probe_results'/(point['source_cache_key']+'_stage_snapshot.json')).relative_to(ROOT)),
        full_detailed_cProfile_used=False,ended_utc=now_utc())
    save(path,record)
    return result


def process():
    """Fresh metrics ONLY for newly valid sources; original cache-only multi-start AO."""
    import torch
    torch.set_num_threads(1);check_science()
    config=source.unconstrained_config();bank=source.load_source_payloads(config,DIRS)
    mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    baseline=read(BASE/'objective_checkpoint.json')
    checkpoint=read(OUT/'objective_checkpoint.json') if (OUT/'objective_checkpoint.json').exists() else {}
    old={float(r['L_km']):r for r in io.read_csv(BASE/'optimized_skr_26_distances.csv')}
    baseline_pairs={key(r['nu_raw'],r['V_A']) for r in baseline['20.0']['rows']}
    assert len(baseline_pairs)==147 and 147<=len(mb)<=151
    newpairs={key(float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])) for p in mb}-baseline_pairs
    assert newpairs<={key(n,v) for n,v in PAIRS}
    write_csv('expanded_source_catalog.csv',[{'nu_raw':float.fromhex(p['nu_mb_raw_hex']),'V_A':float.fromhex(p['V_A_hex']),
        'C':p['C'],'w':p['w'],'source_cache_key':p['cache_key'],'ensemble_hash':p['ensemble_hash'],
        'provenance':p['_provenance']['status']} for p in mb])
    metrics,optimized,comparison,runs,searches,maxima,objects=[],[],[],[],[],{},{}
    original_search=ao.adaptive_maximize_1d
    def recording(**kwargs):
        result=original_search(**kwargs)
        searches.append({'L_km':kwargs['objective'].channel['distance_km'],**result});return result
    warm=None
    with patch.object(ao.ExactMBEvaluator,'source_moments',original.prep.audit.forbidden), \
         patch.object(original.prep.gram_moments,'_fallback',original.prep.audit.forbidden), \
         patch.object(ao,'adaptive_maximize_1d',recording),patch.object(sweep,'adaptive_maximize_1d',recording):
        for distance in sweep.DISTANCES_KM:
            obj=ao.ExactObjective(config,sweep.make_channel(config,distance),OUT,allow_new_source=False,source_cache_dirs=DIRS)
            entry=baseline[str(distance)];assert obj.restore_objective_rows(entry['rows'],entry['identity'])==147
            if str(distance) in checkpoint:
                obj.restore_objective_rows(checkpoint[str(distance)]['rows'],checkpoint[str(distance)]['identity'])
            for p in mb:
                n,v=float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])
                obj.register_catalog(n,v);row=obj(n,v)
                if key(n,v) in newpairs:metrics.append(row)
            ranked=sorted(obj.rows.values(),key=lambda r:r['SKR'],reverse=True)
            assert len(ranked)==len(mb)
            best=ranked[0];maxima[distance]=best;objects[distance]=obj
            checkpoint[str(distance)]={'identity':obj.objective_identity,'rows':list(obj.rows.values())}
            save(OUT/'objective_checkpoint.json',checkpoint)
            starts=[(f'nu_{n:g}',n,None) for n in sweep.BASE_STARTS]
            if warm:starts.append(('warm_previous_distance',*warm))
            actual=[sweep.run_single_distance_ao(distance_km=distance,start_id=sid,start_nu=n,start_va=v,
                objective=obj,max_iterations=ao.MAX_AO_ITERATIONS) for sid,n,v in starts]
            chosen=max((r for r in actual if r['final']),key=lambda r:r['final']['SKR'])
            final=chosen['final'];warm=(float(final['nu_raw']),float(final['V_A']))
            checks=[recording(variable=variable,fixed=fixed,values=obj.catalog_values(variable,fixed),objective=obj)
                    for variable,fixed in (('V_A',warm[0]),('nu_raw',warm[1]))]
            complete=all(ao.coordinate_search_complete(s) for s in checks)
            status=chosen['status']
            if status=='CONVERGED_NUMERICALLY' and not complete:status='STAGNATED_IN_EXACT_CATALOG'
            optimized.append({'L_km':distance,'nu_raw':warm[0],'V_A':warm[1],'I_AB':final['I_AB'],
                'beta_I_AB':final['beta_I_AB'],'chi_BE':final['chi_BE'],'K':final['SKR'],
                'AO_validation_status':status,'selected_start':chosen['start_id'],'coordinate_complete':complete,
                'matches_catalog_maximum':final['SKR']==best['SKR'],'catalog_K':best['SKR'],
                'source_cache_key':final['source_cache_key'],'claim':'FINITE_CATALOG_BEST_OBSERVED_ONLY'})
            comparison.append({'L_km':distance,'old_nu':old[distance]['nu_raw'],'old_V_A':old[distance]['V_A'],
                'old_K':old[distance]['K'],'new_nu':best['nu_raw'],'new_V_A':best['V_A'],'new_K':best['SKR'],
                'delta_K':best['SKR']-float(old[distance]['K']),'AO_matches_catalog':final['SKR']==best['SKR'],
                'runner_up_K':ranked[1]['SKR'],'top_two_gap':best['SKR']-ranked[1]['SKR'],
                'accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'})
            runs.extend({'L_km':distance,**r} for r in actual)
            save(OUT/'cache_only_runs.json',runs);save(OUT/'cache_only_searches.json',searches)
            write_csv('exact_skr_26_distances.csv',metrics);write_csv('optimized_skr_26_distances.csv',optimized)
            write_csv('old_vs_new_optimization.csv',comparison)
            print(f'Overnight L={distance}, MB={len(mb)}, bestK={best["SKR"]}, AOmatch={final["SKR"]==best["SKR"]}',flush=True)
    aligned,finals=original.prep.audit.align_searches(runs,searches)
    save(OUT/'aligned_search_history.json',aligned)
    diagnostics=[original.prep.audit.diagnostic(s,checkpoint[str(d)]['rows']) for d,ss in finals.items() for s in ss]
    write_csv('coordinate_search_completion.csv',diagnostics)
    write_csv('ao_multistart_history.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],**it} for r in runs for it in r['iterations']])
    targeted=[]
    for variable,fixed,label in (('V_A',.165,'P1'),('nu_raw',5.5,'P2')):
        obj=objects[REF];s=original_search(variable=variable,fixed=fixed,values=obj.catalog_values(variable,fixed),objective=obj)
        targeted.append({'L_km':REF,'label':label,**s})
        exact=sorted((r for r in obj.rows.values() if float(r['nu_raw' if variable=='V_A' else 'V_A']).hex()==fixed.hex()),key=lambda r:r[variable])
        write_csv(f'reference_{label}_trace.csv',[{**r,'K':r['SKR'],'fixed':fixed,'search_status':s['status']} for r in exact])
    save(OUT/'reference_targeted_coordinate_searches.json',targeted)
    missing={}
    for s in aligned:
        for e in s['source_missing']:
            n,v=(s['fixed'],e['value']) if s['variable']=='V_A' else (e['value'],s['fixed'])
            row=missing.setdefault(key(n,v),{'nu_raw':n,'V_A':v,'nu_raw_hex':float(n).hex(),'V_A_hex':float(v).hex(),'requests':[]})
            row['requests'].append({k:s[k] for k in ('L_km','variable','start_id','iteration','role')})
    write_csv('remaining_source_dependencies.csv',[{**r,'requests':json.dumps(r['requests'])} for r in missing.values()])
    independent=[]
    for d in sweep.DISTANCES_KM:
        entry=checkpoint[str(d)]
        obj=ao.ExactObjective(config,entry['identity']['identity']['channel'],OUT,allow_new_source=False,source_cache_dirs=DIRS)
        assert obj.restore_objective_rows(entry['rows'],entry['identity'])==len(mb)
        best=max(obj.rows.values(),key=lambda r:r['SKR']);selected=next(r for r in optimized if r['L_km']==d)
        independent.append({'L_km':d,'catalog_K':best['SKR'],'AO_K':selected['K'],
            'AO_matches_catalog':best['SKR']==selected['K'],'rows':len(mb),'identity_sha256':obj.context_hash})
    write_csv('independent_catalog_verification.csv',independent)
    positive_comparison=[{**r,'L_km':float(r['L_km']),'K':float(r['K'])} for r in io.read_csv(BASE/'three_scheme_comparison.csv')
                          if r['scheme'] in (sweep.UNIFORM_SCHEME,sweep.FIXED_MB_SCHEME)]
    positive_comparison += [{'scheme':'AO MB: finite-catalog best',**r} for r in optimized]
    with patch.object(original.prep.audit,'OUT',OUT):
        original.prep.audit.make_plots(runs,maxima,checkpoint,positive_comparison)
    for before,after in (('figure_A_skr_iterations','ao_skr_vs_iterations'),('figure_B_VA_iterations','ao_parameter_evolution'),
                         ('figure_C_reference_V_A','reference_coordinate_refinement'),('skr_vs_distance_positive_only','optimized_skr_vs_distance')):
        for ext in ('.png','.pdf'):shutil.copy2(OUT/(before+ext),OUT/(after+ext))
    progress=[]
    prior=read(BASE/'reference_targeted_coordinate_searches.json')
    for before,after in zip(prior,targeted):
        recovered=[]
        for e in before['source_missing']:
            n,v=(before['fixed'],e['value']) if before['variable']=='V_A' else (e['value'],before['fixed'])
            if key(n,v) in newpairs:recovered.append(e['value'])
        progress.append({'coordinate':after['label'],'old_bracket':before['bracket'],'new_bracket':after['bracket'],
            'old_best_value':before['best_value'],'new_best_value':after['best_value'],
            'old_status':before['status'],'new_status':after['status'],'prior_missing_now_measured':recovered,
            'prior_pair_covered':len(before['source_missing'])==2 and len(recovered)==2,
            'current_call_refinement_stages_attempted':after['refinement_stages'],
            'fully_valid_midpoint_pairs_this_call':after['refinement_stages']-int(after['refinement_status']=='SOURCE_MISSING_REFINEMENT'),
            'current_call_status':after['refinement_status'],'next_missing':after['source_missing']})
    summary={'MB_count':len(mb),'new_source_count':len(newpairs),'new_metric_rows':len(metrics),
        'reference':next(r for r in comparison if r['L_km']==REF),'at22km':next(r for r in comparison if r['L_km']==22.),
        'improved_distances':[r['L_km'] for r in comparison if r['delta_K']>0],
        'AO_catalog_matches':sum(r['AO_matches_catalog'] for r in independent),'AO_starts':len(runs),
        'AO_iterations':sum(len(r['iterations']) for r in runs),'coordinate_status_counts':dict(Counter(s['status'] for s in searches)),
        'closed_selected_directions':sum(ao.coordinate_search_complete(s) for ss in finals.values() for s in ss),
        'remaining_missing_pairs':len(missing),'reference_progress':progress,'AO_rechecked':True,
        'selected_final_searches':{str(d):ss for d,ss in finals.items() if d in (REF,22.)}}
    save(OUT/'postprocess_report.json',summary);check_science()
    return 0


def needed(index,ledger):
    if index==1 and not any(r['batch']==1 and r['status']=='COMPLETED_EXACT' for r in ledger['attempts']):return False
    if index not in (1,3):return True
    if not (OUT/'postprocess_report.json').exists():return index==3
    ss=read(OUT/'postprocess_report.json')['selected_final_searches'][str(REF)]
    s=next(s for s in ss if s['variable']==('V_A' if index==1 else 'nu_raw'))
    n,v=PAIRS[index];fixed=n if index==1 else v
    return key(s['fixed'],1)[0]==key(fixed,1)[0] and any(float(e['value']).hex()==float(v if index==1 else n).hex() for e in s['source_missing'])


def dummy_preflight():
    receipts=[]
    for timeout,AC_loss in ((3.,False),(4.,True)):
        marker='overnight_dummy_'+uuid.uuid4().hex
        code="import subprocess,sys; p=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)',sys.argv[1]]); print('CHILD_PID='+str(p.pid),flush=True); exec('while True: pass')"
        NativePower=safe.WindowsPower
        class SimulatedAC(NativePower):
            def __init__(self):super().__init__();self.calls=0
            def read(self):
                status=super().read();self.calls+=1
                if self.calls>=5:status={**status,'ac':0}
                return status
        with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as log:
            with patch.object(safe,'WindowsPower',SimulatedAC if AC_loss else NativePower):
                receipt=safe.supervised_process([sys.executable,'-B','-c',code,marker],timeout,log)
            log.seek(0);receipt['dummy_log']=log.read()
        assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
        assert receipt['sleep_prevention']['active_verified'] and receipt['sleep_prevention']['released_verified']
        assert 'CHILD_PID=' in receipt['dummy_log']
        if AC_loss:
            assert receipt['returncode']==125 and receipt['power_watch']['abort_reason']=='AC_LOST_OR_CRITICAL_BATTERY'
        else:assert receipt['returncode']==124 and receipt['deadline_exceeded']
        check=subprocess.run(['powershell','-NoProfile','-Command',"$n=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*"+marker+"*'}).Count; if($n){throw 'Orphan dummy'}; 'CLEAN'"],capture_output=True,text=True,check=True)
        assert check.stdout.strip()=='CLEAN'
        receipt.update(dummy_only=True,simulated_AC_loss=AC_loss,full_tree_cleanup_verified=True)
        receipts.append(receipt)
    return receipts


def preflight():
    assert not (OUT/'preflight_report.json').exists(),'Preflight already attempted; do not reset'
    auth=read(OUT/'execution_authorization.json');assert remaining(auth)>900
    assert tuple(map(tuple,auth['pairs']))==PAIRS
    manifest=read(BASE.parent/'source_bottleneck_diagnostic/protected_input_manifest.json')
    for path in BASE.parent.rglob('*'):
        if path.is_file() and OUT not in path.parents:manifest[str(path.relative_to(ROOT)).replace('\\','/')]=io.digest(path)
    manifest.update(io.raw_snapshot([Path(__file__),Path(observer.__file__),ROOT/'tests/test_overnight_source_observer.py']))
    save(OUT/'protected_input_manifest.json',manifest);check_science()
    assert not workers() and safe.safe_power(safe.WindowsPower().read())
    points=[]
    config=source.unconstrained_config()
    obj=ao.ExactObjective(config,read(BASE/'objective_checkpoint.json')['20.0']['identity']['identity']['channel'],OUT,
                          allow_new_source=False,source_cache_dirs=DIRS)
    for i,(n,v) in enumerate(PAIRS):
        identity=obj.evaluator._source_identity(source.make_ensemble(config,'MB',n,v),n,v)
        cache_key=source.json_hash(identity)
        points.append({'probe_order':i+1,'nu_raw':n,'V_A':v,'nu_raw_hex':n.hex(),'V_A_hex':v.hex(),
            'source_cache_key':cache_key,'raw_current_cache_key':cache_key,'ensemble_hash':identity['ensemble_hash'],
            'per_probe_max_seconds':LIMITS[i]})
    write_csv('selected_exact_probes.csv',points)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    test_results=[]
    for pattern in ('test_overnight_source_observer.py','test_source_bottleneck_diagnostic.py','test_ao_phase2a_execution.py',
                    'test_ao_phase2a_preparation.py','test_ao_phase2a_resume.py','test_ao_numerical_optimum_audit.py',
                    'test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        test_results.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
        save(OUT/'preflight_regression_tests.json',test_results)
        assert done.returncode==0,test_results[-1]
    overhead=observer.benchmark();save(OUT/'profiling_overhead_benchmark.json',overhead)
    receipts=dummy_preflight();save(OUT/'native_dummy_supervision.json',receipts)
    assert not workers();check_science()
    baseline=io.read_csv(BASE/'optimized_skr_26_distances.csv')
    assert float(next(r for r in baseline if float(r['L_km'])==REF)['K'])==.07798099387393764
    assert float(next(r for r in baseline if float(r['L_km'])==22.)['K'])==.07661740491526092
    save(OUT/'preflight_report.json',{'status':'CURRENTLY_VERIFIED_PASS','utc':now_utc(),'remaining_seconds':remaining(auth),
        'test_count':sum(int(line.split()[1]) for r in test_results for line in r['output'].splitlines() if line.startswith('Ran ')),
        'AC':safe.WindowsPower().read(),'native_dummy_tests':receipts,'overhead':overhead,
        'scientific_hashes_unchanged':check_science(),'no_orphan_workers':True})
    (OUT/'profiling_fix_audit.md').write_text('# Profiling lifecycle repair\n\n'
        'Original frozen forensic collector is not edited. Overnight launch redirects ONLY instrumentation to overnight_source_observer.py.\n'
        'Owner-thread cProfile dumps immediately reenable profiling; multi-snapshot dummy confirms late work and cumulative/non-double-counted totals.\n'
        'Long AP uses lightweight original-operation stage wrappers plus10s timestamped heartbeats rather than detailed cProfile. Dummy overhead in profiling_overhead_benchmark.json is not an AP runtime prediction.\n'
        'No numerical operations repeated for snapshots; precision/arguments/order/return values unchanged. Completed inclusive/exclusive times and explicitly open stages survive partial timeout.\n'
        'No full detailed call-profile claim. Full-run stage coverage is assessed from actual final/partial records, never assumed.\n',encoding='utf-8')
    print('OVERNIGHT PREFLIGHT PASS; AP not yet launched',flush=True)


def command_process(ledger,auth,label):
    allowance=remaining(auth)-120
    if allowance<=30:raise RuntimeError('Insufficient final-processing budget')
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as log:
        receipt=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--process'],allowance,log)
    ledger['supervision_receipts'].append(receipt);save(OUT/(label+'_supervision.json'),receipt)
    assert receipt['returncode']==0 and receipt['wall_limit_respected'],'Exact/AO postprocessing failed'
    assert receipt['power_watch']['abort_reason'] in (None,'ABSOLUTE_DEADLINE')


def execute():
    auth=read(OUT/'execution_authorization.json')
    assert read(OUT/'preflight_report.json')['status']=='CURRENTLY_VERIFIED_PASS'
    assert not (OUT/'source_generation_ledger.json').exists(),'Never reset/retry existing overnight controller'
    assert remaining(auth)>900 and not workers();check_science()
    ledger={'status':'OVERNIGHT_APPROVED_RUNNING','controller_pid':os.getpid(),'started_utc':now_utc(),
        'authorization':auth,'attempts':[],'skipped':[],'used_wall_seconds':0.,'completed_unique_ensembles':0,
        'supervision_receipts':[],'budget_reset':False,'worker_cleanup_verified':False}
    save(OUT/'source_generation_ledger.json',ledger)
    cpu=time.process_time();lease=safe.AwakeOnAC();error=None
    original_supervised=supervisor.supervised_probe
    def guarded(command,limit,log):
        command=list(command)
        if '--probe' in command:
            command[command.index(str(Path(supervisor.validation.__file__).resolve()))]=str(Path(__file__))
        with patch.object(supervisor,'supervised_probe',original_supervised):
            return safe.supervised_process(command,limit,log)
    try:
        with lease:
            save(OUT/'active_power_preflight.json',{'utc':now_utc(),'power':safe.WindowsPower().read(),'lease':lease.receipt})
            command_process(ledger,auth,'baseline_original_AO_recheck')
            for i,p in enumerate(selected_points()):
                if not needed(i,ledger):
                    ledger['skipped'].append({'probe':i+1,'reason':'Conditional source no longer required or A not successful'});continue
                allowance=min(LIMITS[i],remaining(auth)-900)
                if allowance<=30:
                    ledger['skipped'].append({'probe':i+1,'reason':'Insufficient remaining budget/reserve'});break
                check_science();assert not workers() and safe.safe_power(safe.WindowsPower().read())
                # Stable AC sampled before each attempt without permanent settings changes.
                time.sleep(.5);assert safe.safe_power(safe.WindowsPower().read())
                bank=source.load_source_payloads(source.unconstrained_config(),DIRS)
                if source.candidate_from_payload(source.unconstrained_config(),bank,'MB',float(p['nu_raw']),float(p['V_A'])):
                    ledger['skipped'].append({'probe':i+1,'reason':'Already compatible exact cache'});continue
                assert p['source_cache_key'] not in {r['cache_key'] for r in ledger['attempts']}
                with patch.object(supervisor,'supervised_probe',guarded):
                    record=supervisor.run_batch(OUT,p,allowance,i+1,ledger)
                receipt=record['supervision'];ledger['supervision_receipts'].append(receipt)
                write_csv('overnight_execution_ledger.csv',[{k:r.get(k) for k in ('batch','nu_raw','V_A','cache_key','status','C','w',
                    'wall_seconds','cpu_seconds','timeout_seconds','source_payload_verified','error')} for r in ledger['attempts']])
                assert not workers() and receipt['no_watchdog_thread_remaining']
                if receipt['power_watch']['abort_reason'] not in (None,'ABSOLUTE_DEADLINE') or not receipt['wall_limit_respected']:
                    raise RuntimeError('SAFETY_ABORT: stop campaign, no automatic resume')
                if record['status'] not in ('COMPLETED_EXACT','TIMEOUT'):
                    raise RuntimeError('Serious source/numerical/provenance failure: '+record['status'])
                if record['status']=='COMPLETED_EXACT':command_process(ledger,auth,'after_probe_'+str(i+1))
                save(OUT/'source_generation_ledger.json',ledger)
            command_process(ledger,auth,'final_original_AO_recheck')
            ledger['status']='OVERNIGHT_COMPLETE_FINITE_SCOPE'
    except BaseException as exc:
        error=repr(exc);ledger['status']='OVERNIGHT_STOPPED_SAFETY_PROVENANCE_OR_BUDGET';print(error,flush=True)
    finally:
        ledger.update(error=error,ended_utc=now_utc(),controller_cpu_seconds=time.process_time()-cpu,
            wall_seconds_including_repair=time.monotonic()-auth['origin_monotonic'],wall_budget_respected=remaining(auth)>=0,
            sleep_prevention=lease.receipt,worker_cleanup_verified=not workers())
        ledger['job_CPU_seconds']=sum(r.get('aggregate_cpu_seconds',0) for r in ledger['supervision_receipts'])
        ledger['recorded_total_CPU_seconds']=ledger['job_CPU_seconds']+ledger['controller_cpu_seconds']
        save(OUT/'source_generation_ledger.json',ledger);save(OUT/'sleep_prevention_final_receipt.json',lease.receipt)
        finalize(ledger)
    return 1 if error else 0


def finalize(ledger):
    """Report only actual durable evidence; no AP or new objective calculation."""
    post=read(OUT/'postprocess_report.json') if (OUT/'postprocess_report.json').exists() else None
    stages=[];coverage=[]
    for path in (OUT/'probe_results').glob('*_stage_snapshot.json'):
        data=read(path);cache_key=path.name.split('_stage_snapshot')[0]
        grouped={}
        for r in data['completed_stages']:
            group=grouped.setdefault((r['name'],r['digits']),{'count':0,'wall':0.,'cpu':0.})
            group['count']+=1;group['wall']+=r['wall_seconds_exclusive'];group['cpu']+=r['CPU_seconds_exclusive']
        for (name,digits),v in grouped.items():
            stages.append({'cache_key':cache_key,'stage':name,'digits':digits,'completed_calls':v['count'],
                'exclusive_completed_wall_seconds':v['wall'],'exclusive_completed_CPU_seconds':v['cpu'],
                'measurement_scope':data['scope'],'unfinished_intervals_not_counted':json.dumps(data['open_stages'])})
        coverage.append({'cache_key':cache_key,'finished':data['finished'],'snapshots':data['snapshot_count'],
            'last_observed_wall_seconds':data['wall_seconds'],'last_process_CPU_seconds':data['process_cpu_seconds'],
            'open_stages':data['open_stages'],'snapshot_CPU_overhead':data['snapshot_CPU_seconds_measured'],
            'observer_error':data['observer_error'],'full_detailed_call_profile':False})
    write_csv('profiling_stage_summary.csv',stages)
    for name in ('overnight_execution_ledger.csv','new_exact_source_moments.csv','expanded_source_catalog.csv',
                 'exact_skr_26_distances.csv','old_vs_new_optimization.csv','reference_P1_trace.csv','reference_P2_trace.csv',
                 'ao_multistart_history.csv','coordinate_search_completion.csv','remaining_source_dependencies.csv','optimized_skr_26_distances.csv'):
        if not (OUT/name).exists():write_csv(name,[{'status':'NOT_RUN','note':'No validated execution result; see final report'}])
    report={**ledger,'postprocess':post,'successful_probes':sum(r['status']=='COMPLETED_EXACT' for r in ledger['attempts']),
        'timeout_probes':sum(r['status']=='TIMEOUT' for r in ledger['attempts']),
        'safety_or_failure_stops':sum(r['status'] not in ('COMPLETED_EXACT','TIMEOUT') for r in ledger['attempts']),
        'profiling_bug_fixed_for_overnight_path':True,'stage_coverage':coverage,
        'full_detailed_call_profile_used':False,'protected_hashes_unchanged':check_science(),
        'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','global_optimum_certified':False,
        'continuous_convergence_certified':False,'no_interpolation':True,'science_and_AO_changed':False,
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','frozen_historical_hash_discrepancy':'PREEXISTING_UNCHANGED'}
    save(OUT/'ao_overnight_report.json',report)
    lines=['# Overnight AO numerical SKR run','',ledger['status'],'',
        f"Success={report['successful_probes']}, timeout={report['timeout_probes']}, safety/failure={report['safety_or_failure_stops']}.",
        f"Wall including repair/preflight={ledger.get('wall_seconds_including_repair')}s/28800; recorded controller+JobCPU={ledger.get('recorded_total_CPU_seconds')}s.",
        'CPU excludes independent interactive repair/preflight/test processes outside the controller Job. No budget reset.',
        'Stage timing, not full detailed cProfile. Last open intervals are partial; never claim complete killed-stage coverage.',
        '', '| Probe | nu | VA | Status | C | w | Wall seconds | Job CPU seconds |',
        '|---|---|---|---|---|---|---|---|']
    for r in ledger['attempts']:
        lines.append('| '+' | '.join(str(r.get(k,'')) for k in ('batch','nu_raw','V_A','status','C','w','wall_seconds','cpu_seconds'))+' |')
    if post:
        lines += ['',f"MB catalog={post['MB_count']}; new26-distance rows={post['new_metric_rows']}; improved distances={post['improved_distances']}.",
          f"Reference={post['reference']}",f"22km={post['at22km']}",
          f"ActualAO matches independent catalog {post['AO_catalog_matches']}/26; closed selected directions={post['closed_selected_directions']}.",
          f"P1/P2 actual progress={post['reference_progress']}",
          f"Missing pairs={post['remaining_missing_pairs']}; inspect actual nu0=.8 histories rather than assuming every start matches."]
    lines += ['', '## Limits and next steps','',
        'Finite-catalog maximum and locally narrowed brackets are not continuous/global convergence. Original inner cap4/outer6/epsilon1e-8/parameter1e-6 unchanged.',
        'Strictnu>0 still differs from mathematicalnu>=0; outer-domain and tiny-gap total error control remain unresolved.',
        'Current source dependency file identifies minimum next original requests. Additional AP or cap/configuration experiments require separate authority.',
        f"Sleep restored={ledger.get('sleep_prevention',{}).get('released_verified')}; no workers={ledger.get('worker_cleanup_verified')}; deadline respected={ledger.get('wall_budget_respected')}.",
        f"Error={ledger.get('error')}. Earlier artifacts/source moments/provenance preserved."]
    (OUT/'ao_overnight_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'numerical_accuracy_assessment.md').write_text('# Numerical accuracy\n\nORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED.\n'
        'Exact AP/precision/support/provenance validated on successful sources, original GH8/directZminus retained. No totalK enclosure or invented error bounds.\n'
        'Bit-exact repeats and finite catalog order are not enough for continuous optimum or all displayed digits. Strictnu>0 and unbounded remote extrema remain limitations.\n',encoding='utf-8')
    (OUT/'algorithm1_ao.tex').write_text(r'''% Actual original AO, not a convergence certificate
\begin{enumerate}
\item Use the unchanged exact source cache and common physical ensemble; evaluate $K=0.95I_{AB}-\chi_{BE}(Z_-)$.
\item Start at $\nu_0\in\{0.1,0.15,0.3,0.8\}$ and previous-distance warm start; repeat at most six outer iterations.
\item P1 fixes the previous $\nu$ and runs the original adaptive exact $V_A$ search.
\item P2 fixes the newly selected $V_A$ and runs the original adaptive exact $\nu>0$ search.
\item Exact endpoint expansion and paired midpoint refinement retain caps three/four and parameter tolerance $10^{-6}$.
\item Missing moments, failed evaluations and unresolved boundaries remain explicitly incomplete; no interpolation.
\item Stop numerically only when both searches are complete, no earlier unresolved or numerical warning remains, and $|\Delta K|\le10^{-8}$.
\item Select the best actually obtained start and independently compare against the finite exact catalog. Local numerical closure does not certify a global maximum.
\end{enumerate}
''',encoding='utf-8')
    save(OUT/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in read(OUT/'protected_input_manifest.json')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--execute',action='store_true');parser.add_argument('--process',action='store_true')
    parser.add_argument('--probe',action='store_true');parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--nu',type=float);parser.add_argument('--va',type=float);parser.add_argument('--per-probe-timeout',type=float)
    args=parser.parse_args()
    if args.preflight:
        try:preflight();return 0
        except BaseException as exc:
            save(OUT/'preflight_report.json',{'status':'FAILED','error':repr(exc),'utc':now_utc(),'AP_launched':False})
            print(repr(exc),flush=True);return 1
    if args.probe:return profile_probe(args)
    if args.process:return process()
    if args.execute:return execute()
    parser.error('Explicit execution mode required')


if __name__=='__main__':raise SystemExit(main())
