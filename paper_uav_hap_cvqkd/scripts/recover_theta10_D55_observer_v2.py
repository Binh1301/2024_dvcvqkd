"""Observer recovery/preflight only. Native supervised DUMMY workers, never AP."""
import ast
from collections import Counter
from contextlib import ExitStack
from datetime import datetime,timezone
import inspect
import json
from pathlib import Path
import pstats
import statistics
import subprocess
import sys
import threading
import time
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import observer_v2_recovery_entry as entry
from scripts import windows_sleep_safe_supervision as safe
from scripts.overnight_source_observer import OwnerProfiler,atomic_json,dummy_work
from scripts.diagnose_theta10_D55_source_bottlenecks import digest,read,rows,write_csv as unused_writer
from scripts.exact_cache_provenance import verify_source_payload,json_hash

BASE=ROOT/'results/theta10_D55_ao_numerical_optimum_validation'
OLD=BASE/'overnight_ao_run'
OUT=BASE/'observer_v2_recovery'
REF=21.9393102292


def save(name,data):atomic_json(OUT/name,data)


def csv(name,data):
    import csv as library
    fields=list(dict.fromkeys(k for r in data for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        writer=library.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data)


def no_workers(marker=None):
    match="*"+marker+"*" if marker else '*full_support_c4_worker*'
    condition="$_.CommandLine -like '"+match+"'" if marker else "$_.CommandLine -match '--approved-ap|--probe|--profile-worker|full_support_c4_worker\\.py|run_theta10_D55_overnight_ao\\.py.*--execute'"
    command="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {"+condition+"} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
    done=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    return not done.stdout.strip() or done.stdout.strip() in ('[]','null')


def native_case(label,mode='success',duration=.4,wall=8,inject=None,disabled=False):
    prefix=OUT/'dummy'/label;marker='observer_v2_recovery_'+uuid.uuid4().hex
    command=[sys.executable,'-B','-X','utf8','-u',str(Path(entry.__file__)),
         '--dummy-mode',mode,'--prefix',str(prefix),'--duration',str(duration),
         '--spawn-child','--marker',marker]
    if disabled:command.append('--without-observer')
    NativePower=safe.WindowsPower;monotonic=time.monotonic;clock_calls={}
    class FakeACLoss(NativePower):
        def __init__(self):super().__init__();self.calls=0
        def read(self):
            state=super().read();self.calls+=1
            return {**state,'ac':0} if self.calls>=5 else state
    def interrupted_clock():
        value=monotonic()
        if '(watchdog)' in threading.current_thread().name:
            ident=threading.get_ident();clock_calls[ident]=clock_calls.get(ident,0)+1
            if clock_calls[ident]>=5:return value+6.25
        return value
    # Only inject in supervisor harness; no actual AC disconnect or OS suspension.
    with ExitStack() as stack:
        if inject=='AC':stack.enter_context(patch.object(safe,'WindowsPower',FakeACLoss))
        if inject=='WATCHDOG':stack.enter_context(patch.object(safe.time,'monotonic',interrupted_clock))
        with (OUT/'dummy'/(label+'.log')).open('w+',encoding='utf-8') as log:
            receipt=safe.supervised_process(command,wall,log)
            log.seek(0);text=log.read()
    result_file=Path(str(prefix)+'_worker_result.json')
    result=read(result_file) if result_file.exists() else None
    classification=entry.classify(receipt,result)
    assert 'DUMMY_CHILD_PID=' in text,'Dummy must exercise live descendant containment'
    assert no_workers(marker),'Dummy tree/orphan remains'
    assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
    assert receipt['sleep_prevention']['active_verified'] and receipt['sleep_prevention']['released_verified']
    expected={'TIMEOUT':'TIMEOUT','AC':'AC_SAFETY_ABORT','WATCHDOG':'WATCHDOG_ABORT'}.get(inject)
    if inject is None:expected={'success':'SUCCESS','instrumentation_failure':'INSTRUMENTATION_FAILURE','numerical_failure':'NUMERICAL_FAILURE'}[mode]
    assert classification==expected,(label,classification,expected,receipt)
    if result:
        assert result['context_before']==result['context_after'] and result['original_hooks_restored']
        assert result['native_job_contains_worker'] and result['original_AP_source_moments_executed']==0
    snapshot_path=Path(str(prefix)+'_stage_snapshot.json')
    snapshot=read(snapshot_path) if snapshot_path.exists() else None
    if snapshot and classification=='SUCCESS':assert snapshot['finished'] and snapshot['snapshot_count']>=2
    if inject:
        assert snapshot and not snapshot['finished'],'Partial snapshot must survive forced stop'
        assert snapshot['open_stages'],'Interrupted dummy interval must remain explicitly open'
    record={'test':label,'expected':expected,'actual':classification,'PASS':True,'dummy_only':True,
        'wall_seconds':receipt['measured_wall_seconds_including_cleanup'],
        'Job_CPU_seconds':receipt.get('aggregate_cpu_seconds'),'worker_returncode':receipt['returncode'],
        'worker_tree_cleanup':True,'Sleep_restored':receipt['sleep_prevention']['released_verified'],
        'watchdog_remaining':not receipt['no_watchdog_thread_remaining'],'injection':inject,
        'source_moment_computations':0,'worker_result':result_file.name if result else 'NOT_RECORDED_DUE_TO_FORCED_STOP',
        'snapshot_count':snapshot['snapshot_count'] if snapshot else 0,
        'coverage':'DUMMY_INTERVAL_VALID' if snapshot and classification=='SUCCESS' else 'PARTIAL_DUMMY_INTERVAL' if snapshot else 'NO_SNAPSHOT',
        'NOT_REAL_AP_FULL_RUN_PROFILE_VALID':True}
    save('dummy/'+label+'_supervision.json',receipt)
    return record


def lifecycle():
    prefix=OUT/'dummy'/'owner_profile'
    def after_first():return dummy_work(150000)
    with OwnerProfiler(prefix) as profiler:
        for i in range(6):
            if i:after_first()
            else:dummy_work(150000)
            profiler.snapshot()
    data=read(Path(str(prefix)+'_snapshots.json'))
    stats=pstats.Stats(str(prefix)+'.prof')
    assert next(v[1] for k,v in stats.stats.items() if k[2]=='after_first')==5
    assert len(data)==7 and data[-1]['final']
    assert abs(sum(r['delta_profile_self_seconds'] for r in data)-data[-1]['cumulative_profile_self_seconds'])<1e-10
    assert all(b['wall_seconds']>=a['wall_seconds'] and b['process_cpu_seconds']>=a['process_cpu_seconds'] for a,b in zip(data,data[1:]))
    csv('profiling_lifecycle_tests.csv',[{'snapshot':i+1,**r,'dummy_only':True,'late_work_verified':True,
             'measurement':'Owner-thread accumulated cProfile; dump pauses explicitly excluded; not AP coverage'} for i,r in enumerate(data)])
    return data


def overhead():
    results=[]
    # Fixed equal operation counts; common imports are warmed. No AP numerical operations.
    for repetition in range(7):
        local={}
        for enabled in ((False,True) if repetition%2==0 else (True,False)):
            wall,cpu=time.perf_counter(),time.process_time()
            value=entry.dummy_entry(OUT/'dummy'/f'overhead_{repetition}_{enabled}',enabled=enabled,iterations=1500000,interval=10)
            local[enabled]=(time.perf_counter()-wall,time.process_time()-cpu,value)
        assert local[True][2]['worker_stdout']==local[False][2]['worker_stdout']
        assert local[True][2]['calls']==local[False][2]['calls']
        results.append({'repetition':repetition+1,'fixed_dummy_iterations_per_precision':1500000,
            'precision_contexts':[1050,1250,1450],'plain_wall_seconds':local[False][0],
            'observed_wall_seconds':local[True][0],'plain_process_CPU_seconds':local[False][1],
            'observed_process_CPU_seconds':local[True][1],'outputs_and_calls_equal':True,'dummy_only':True})
    wall_ratio=statistics.median(r['observed_wall_seconds'] for r in results)/statistics.median(r['plain_wall_seconds'] for r in results)-1
    cpu_ratio=statistics.median(r['observed_process_CPU_seconds'] for r in results)/statistics.median(r['plain_process_CPU_seconds'] for r in results)-1
    csv('instrumentation_overhead.csv',results)
    return {'median_wall_overhead_fraction':wall_ratio,'median_process_CPU_overhead_fraction':cpu_ratio,
            'prospective_dummy_acceptance_wall_fraction':.10,'acceptable_for_controlled_pilot':wall_ratio<=.10,
            'limits':'Seven paired warmed fixed-work DUMMY trials. AP overhead UNKNOWN until actual separately approved source run; snapshot CPU uses collector thread_time, numeric stageCPU process aggregate.'}


def baseline_audit():
    cp=read(OLD/'objective_checkpoint.json');table=rows(OLD/'optimized_skr_26_distances.csv')
    catalog=rows(OLD/'expanded_source_catalog.csv');assert len(catalog)==147 and len(table)==26 and len(cp)==26
    assert sum(len(v['rows']) for v in cp.values())==3822
    independent=rows(OLD/'independent_catalog_verification.csv');assert all(r['AO_matches_catalog']=='True' for r in independent)
    reference=next(r for r in table if float(r['L_km'])==REF);at22=next(r for r in table if float(r['L_km'])==22.)
    assert (float(reference['nu_raw']),float(reference['V_A']),float(reference['K']))==(.165,5.5,.07798099387393764)
    assert (float(at22['nu_raw']),float(at22['V_A']),float(at22['K']))==(.165,5.475,.07661740491526092)
    for distance,saved in cp.items():
        assert len(saved['rows'])==147
        best=max(saved['rows'],key=lambda r:float(r['SKR']))
        actual=next(r for r in table if float(r['L_km'])==float(distance))
        assert float(actual['K'])==float(best['SKR'])
    searches=read(OLD/'reference_targeted_coordinate_searches.json')
    runs=read(OLD/'cache_only_runs.json');assert len(runs)==129 and sum(len(r['iterations']) for r in runs)==283
    warnings=[]
    for r in runs:
        for it in r['iterations']:
            if float(it['K_afterVA'] if 'K_afterVA' in it else it['K_after_VA'])<float(it['K_before'])-1e-8 or float(it['K_after_nu'])<float(it['K_after_VA'])-1e-8:
                warnings.append({'L_km':r['L_km'],'start':r['start_id'],'iteration':it['iteration']})
    settings={node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse((ROOT/'scripts/run_theta10_D55_alt_opt.py').read_text()).body
       if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
       and node.targets[0].id in ('K_TOLERANCE','PARAMETER_TOLERANCE','MAX_AO_ITERATIONS','MAX_REFINEMENT_STAGES','MAX_BOUNDARY_EXPANSIONS')}
    assert settings=={'K_TOLERANCE':1e-8,'PARAMETER_TOLERANCE':1e-6,'MAX_AO_ITERATIONS':6,'MAX_REFINEMENT_STAGES':4,'MAX_BOUNDARY_EXPANSIONS':3}
    return {'reference':reference,'at22km':at22,'source_count':147,'stored_objectives':3822,
            'AO_matches_saved_catalog':26,'starts':129,'iterations':283,'new_AO_invocations':0,
            'coordinate_searches':searches,'monotonicity_violations_over_existing_tolerance':warnings,
            'settings':settings,'missing_pairs':len(rows(OLD/'remaining_source_dependencies.csv')),
            'claim':'FINITE_CATALOG_MAXIMUM; COORDINATE_SEARCH_INCOMPLETE; GLOBAL_OPTIMUM_NOT_CERTIFIED'}


def main():
    if OUT.exists():raise FileExistsError('Recovery artifacts exist; refuse overwrite')
    started=time.monotonic();OUT.mkdir();(OUT/'dummy').mkdir()
    manifest=read(OLD/'protected_input_manifest.json')
    for path in BASE.rglob('*'):
        if path.is_file() and OUT not in path.parents:manifest[path.relative_to(ROOT).as_posix()]=digest(path)
    for path in [Path(entry.__file__),Path(__file__),ROOT/'tests/test_observer_v2_recovery.py']:
        manifest[path.relative_to(ROOT).as_posix()]=digest(path)
    save('protected_input_manifest.json',manifest)
    for name,expected in manifest.items():assert digest(ROOT/name)==expected,name
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    diff=subprocess.run(['git','diff'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
    (OUT/'preexisting_worktree.diff').write_text(diff.stdout,encoding='utf-8')
    # Statically inspect the ACTIVE observer body; archived broken v1.main is never called.
    active=[ROOT/'scripts/overnight_source_observer_v2.py',Path(entry.__file__)]
    invalid=[]
    for path in active:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Attribute) and node.attr=='dps':
                spelling=ast.unparse(node)
                if spelling in ('mpmath.dps','mp.dps','worker.mp.dps'):invalid.append((path.name,node.lineno,spelling))
    assert not invalid,invalid
    audit=baseline_audit();save('cache_only_AO_audit.json',audit)
    cycle=lifecycle();perf=overhead();save('instrumentation_overhead_summary.json',perf)
    test_results=[]
    for pattern in ('test_observer_v2_recovery.py','test_overnight_observer_integration.py','test_overnight_source_observer.py',
        'test_source_bottleneck_diagnostic.py','test_ao_phase2a_execution.py','test_ao_phase2a_preparation.py',
        'test_ao_phase2a_resume.py','test_ao_numerical_optimum_audit.py','test_windows_sleep_safe_supervision.py',
        'test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],
              cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        test_results.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
        save('regression_tests.json',test_results)
        assert done.returncode==0,test_results[-1]
    native=[];blocker=None
    power=safe.WindowsPower().read()
    if not safe.safe_power(power):blocker='BLOCKED_BY_ENVIRONMENT: live stable AC required for native Sleep/Job tests'
    if not no_workers():blocker='BLOCKED_BY_ENVIRONMENT: existing source worker'
    if blocker is None:
        try:
            for label,kwargs in [('normal',{}),('disabled',{'disabled':True}),
                 ('instrumentation_failure',{'mode':'instrumentation_failure'}),
                 ('numerical_failure',{'mode':'numerical_failure'}),
                 ('deadline',{'duration':30,'wall':3,'inject':'TIMEOUT'}),
                 ('AC_loss',{'duration':30,'wall':12,'inject':'AC'}),
                 ('watchdog_gap',{'duration':30,'wall':20,'inject':'WATCHDOG'})]:
                record=native_case(label,**kwargs);native.append(record)
                csv('dummy_worker_integration_results.csv',native)
                print('Native dummy '+label+': '+record['actual']+' PASS',flush=True)
        except BaseException as exc:
            blocker=repr(exc);native.append({'test':label,'PASS':False,'error':blocker})
            csv('dummy_worker_integration_results.csv',native)
    native.append({'test':'not_run_no_start','expected':'NOT_RUN','actual':entry.classify({},started=False),'PASS':True,
                   'dummy_only':True,'source_moment_computations':0})
    csv('dummy_worker_integration_results.csv',native)
    unchanged=[]
    for name,expected in manifest.items():
        actual=digest(ROOT/name);unchanged.append({'path':name,'before_sha256':expected,'after_sha256':actual,'unchanged':actual==expected})
    csv('protected_hash_audit.csv',unchanged);assert all(r['unchanged'] for r in unchanged)
    test_count=sum(int(line.split()[1]) for r in test_results for line in r['output'].splitlines() if line.startswith('Ran '))
    ready=blocker is None and len(native)==8 and all(r['PASS'] for r in native) and perf['acceptable_for_controlled_pilot'] and no_workers()
    report={'status':'READY_FOR_CONTROLLED_AP_PILOT' if ready else 'NOT_READY_FOR_AP','utc':datetime.now(timezone.utc).isoformat(),
       'AP_authorized_now':False,'AP_workers_launched':0,'new_source_moments':0,'new_SKR_evaluations':0,
       'new_AO_invocations':0,'native_tests':native,'blocker':blocker,'overhead':perf,'baseline':audit,
       'active_invalid_mpmath_attribute_accesses':invalid,'profiling_snapshots':len(cycle),'dummy_observation_lifecycle':'PASS',
       'full_real_AP_profile_status':'NOT_RUN','historical_broken_paths':'Preserved v1.main/old overnight redirect NEVER called; not declared repaired globally',
       'original_science_and_AO_hashes_unchanged':True,'protected_hash_count':len(manifest),
       'test_count':test_count,'regression_tests':'CURRENTLY_VERIFIED_PASS','no_orphan_workers':no_workers(),
       'power_at_start':power,'power_at_end':safe.WindowsPower().read(),'dummy_only_readiness_not_real_AP_equivalence':True,
       'proposed_A_pair_hex':[float(.165).hex(),float(5.49375).hex()],
       'proposed_A_cache_key':'db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59',
       'proposed_A_probe_wall_seconds':4500,'proposed_total_wall_seconds':5400,'proposed_final_reserve_seconds':900,
       'fresh_explicit_approval_required':True,'old_overnight_budget_reused':False,
       'whole_K_error_bound':'NOT_ESTABLISHED','global_optimum_certified':False,
       'frozen_historical_hash_discrepancy':'PREEXISTING_UNCHANGED','lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
       'diagnostic_wall_seconds':time.monotonic()-started,
       'producer_sha256':digest(Path(__file__)),'prepared_entry_sha256':digest(Path(entry.__file__))}
    documents(report)
    save('observer_v2_recovery_report.json',report)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    print(json.dumps({k:report[k] for k in ('status','test_count','protected_hash_count','AP_workers_launched','blocker','diagnostic_wall_seconds')},indent=2))


def documents(report):
    status=report['status'];perf=report['overhead'];baseline=report['baseline']
    outputs={
    'observer_v2_code_audit.md':f'''# Observer v2 code audit

Active entry: scripts/observer_v2_recovery_entry.py -> overnight_source_observer_v2.run_observed
-> original full_support_c4_worker.main. Recovery CLI exercises original JSON/input/precision-loop/output
entry with dummy row/Gram/eigen/LU leaves, not a SimpleNamespace-only substitute.
No source-moment arithmetic is performed. All fake row values are quarantined in dummy/ and NEVER
enter source/objective caches. Production --approved-ap remains NOT_RUN and requires fresh probeA
authority, exacthex/cachekey/request hash, unexpired deadlines and native Job containment.

Active metadata accesses worker.mp.mp.dps (mpmath module context), not module.dps. Static active
invalid count0. Historical executed observer v1 retains3 invalid accesses; the old overnight
controller still routesv1 and MUST NOT be reused. These immutable forensic paths are preserved,
not described as globally fixed. v2 imports StageObserver fromv1 module but never callsv1.main.

CheckedStageObserver separates metadata/startup/persistence/shutdown exceptions as
INSTRUMENTATION_FAILURE; original numerical operation exceptions are NUMERICAL_FAILURE.
Supervision takes precedence for TIMEOUT/AC_SAFETY_ABORT/WATCHDOG_ABORT. Unknown process failures
are conservatively instrumentation failures, never inferred mathematical impossibility.
Observer disabled path calls same original main once without hooks/profile; dummy results/calls
equal enabled path. No scientific code changed. Future controlled parent MUST consume worker_result
status before the historical generic probe_worker classifier; no string-timeout heuristics.

Ready status: {status}, limited to this prepared entry and controlled pilot, not old controller/AP proof.
''',
    'mpmath_context_validation.md':'''# mpmath context protection

Dummy entry imports the real original worker/module, records context object identity, dps, prec,
_prec_rounding and libmp backend before/after. Actual worker main consumes exact float.hex input and
original precision ladder; only numerical leaves are dummy-patched. During dummy rows original
workdps1050/1250/1450 restores context. Observer only READS precision; it never calls workdps,
sets dps or swaps the active context. Dummy fixture is not a full-support convergence oracle.

Initialization, normal completion, original failure, injected observer failure and disabled observer
all verify restored module/context/hooks. Native subprocess results persist before/after metadata
and job containment. Native killed workers cannot report after-context, explicitly NOT_RECORDED;
their process ends and original scientific file/settings hashes remain identical.
''',
    'supervisor_safety_tests.md':f'''# Native supervisor dummy safety tests

{status}. Full results in dummy_worker_integration_results.csv and dummy/*_supervision.json.
Same original Windows Job supervisor/Sleep/AC watchdog, not a reimplemented safety mock.
Live idle child + worker tests normal exit, observer failure, numerical failure, wall deadline,
AC status injection and synthetic watchdog clock gap>5s. No real AC disconnection or suspension.
Watchdog clock injection is thread-selective so controller clock/deadline remains real.
Native Job membership verified by IsProcessInJob; marker/PID inventory confirms complete tree
cleanup, owning-thread Sleep request acquired/restored and no watchdog thread left.

Return/status map: success0; observer70; numerical71; deadline124; unsafeAC/gap125 with explicit
recorded reason. NOT_RUN starts no process. Measurement scope Job aggregateCPU versus worker
processCPU/thread collector overhead is explicit. Forced termination leaves valid prior snapshot
with OPEN interval, never invents final callback or full-run coverage. Automatic Sleep lease does
not prevent manual suspend/shutdown; actual OS suspension can prevent watchdog scheduling and
strict deadlines. Any gap/overrun must fail closed in the future pilot. No permanent power plan change.
''',
    'ap_readiness_checklist.md':f'''# AP readiness checklist

{status}

Only execution readiness for ONE separately authorized controlledAP pilot; not numerical convergence,
full realAP profiling, production equivalence or publication readiness. Ten required gates: activev2
initialization/context/static API, repeated snapshots, science/provenance, nativeJob, AC monitoring,
Sleep restoration, orphan cleanup, regressions/hashes all recorded in machine report/dummy files.
Overhead gate prospectively median fixed-dummy wall <=10%; measured {perf['median_wall_overhead_fraction']:.6g}.
Blocker: {report['blocker']}. Actual longAP overhead/stage coverage UNKNOWN until pilot.
Fresh AC/Job/Sleep/provenance/orphan/deadline checks must be repeated immediately before any AP.
Old overnight authorization NEVER reused; no AP approved or run in recovery.
''',
    'probe_A_execution_plan.md':'''# Proposed controlled Probe A (NOT_RUN; explicit approval required)

Pair(nu_raw,VA)=(0.165,5.49375), hex(0x1.51eb851eb851fp-3,0x1.5f9999999999ap+2).
Cachekey db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59.
Recommend FRESH90min TOTAL wall including last preflight/startup/75min source maximum/26 exact
metrics/original cache-onlyAO/final validation/cleanup; reserve>=15min, shorten AP if needed.
Sequential ONE source only, original binary64 inputs/precision1050/1250/1450/GH8/directZminus.
This proposal is NOT execution authority, no authfile generated. No failed-state AP resume or retry.

Before launch explicit fresh authority+absolute deadline, stableAC, temporarySleep verified nativeJob,
no orphan, all protected hashes/cache/provenance verified; use new preparedentry/common execute_worker,
NEVER old overnightv1 redirect. Bind source request/hash/cachekey; parent supplies fresh authorization
to guarded production entry and consumes typed worker-result sidecar for classification.
Keep supervisor limit=min4500s,remaining-900s; source inner timeout follows validated operational
deadline, not an accidentally retained3600s hardcoded fallback; no numerical precision change.

First pilot validates actual entry/progress only by real evidence, never assumes dummy proves longAP.
SourceC/w accepted only original full-support/provenance validation. Compute26 exact metrics and
original multi-startAO with implicitAP forbidden; compare independent catalog, reference/22km,
P1/P2 brackets/missing/stopping, total-error evidence and genuine histories. On observer/AC/gap/
provenance/numerical/deadline error stop fulltree, preserve receipts and restoreSleep; no automaticretry.
No guarantee source finishes within75min or improves K. Readiness must be refreshed at execution.
''',
    'conditional_P1_P2_continuation_plan.md':'''# Conditional AO continuation, not catalog growth

Reference best(.165,5.5),K.07798099387393764; P1[5.4875,5.5125],width.025/radius.0125,
first paired stage blocked by5.49375 and5.50625; 1 attemptedstage/0 completedpairs.
P2[.1625,.16562500000000002],width.003125/radius.0025; blockednu.16375/.16531250000000003,
1 attemptedstage/0 completedpairs. Both SOURCE_MISSING_REFINEMENT;0 coordinateclosure.
These are exact saved records, not a fresh optimizer run.

SuccessfulA supplies one side. If no new best and upperpartner5.50625 remains required by ORIGINAL
activeP1 search, propose it later with separate approval; check actual selectednu,VA, bracket and
compatiblecache afterA. A alone does not complete the current paired stage. If both partners not
better, P1bracket[5.49375,5.50625], then next5.496875/5.503125, conditional ONLY. Winner changes
can alter targetP2fixedVA and all requests; don't preapprove arbitrary substitution.

No difficultP2 AP here. Prior lowernu3595.75wall/3469.96875JobCPU and upper3595wall/3516.90625CPU
60min timeouts do not predict completion or locate late-stage bottleneck. Need valid pilot profile
before a dedicated larger-runtime plan. P2 currentpair is necessary only if actual selectedVA stays5.5.

Originaleps1e-8,param1e-6,outer6,inner4,boundary3 unchanged. Fixed-incumbent halving requires14P1/
12P2 stages from currentradii, conditional; cap4 insufficient onecall. Tolerance checked at next
entry, earlier-unresolved latch/catalog stagnation can stop before6outer calls; repeated calls only
help with genuinely added exact requested moments, not replaying identicalcache. Prospective
configuration experiment needs separateapproval, no silent cap increase. Strictnu>0 excludes
mathematicalnu=0; remote boundaries/wholeKerror andnu0=.8 missing branches remain unresolved.
'''}
    for name,text in outputs.items():(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
    answers=[
        'Invalid module.dps fixed on active observer-v2/checkedentry paths; historical immutablev1 still contains3 invalid dormant accesses and oldcontroller must not be used.',
        'Observer initializes through original worker main/JSON entry under actual native supervisor with dummy numerical leaves. Real AP entry remains NOT_RUN.',
        f'Owner cProfile continues through{report["profiling_snapshots"]} snapshots, late calls verified, cumulative/delta not double-counted; native lightweight heartbeats continue and survive forced termination.',
        'Context identity/dps/prec/rounding/backend and original file/settings hashes unchanged; exceptions/disabled path restorehooks, no observer precision setter.',
        'Native normal/failure/deadline/live-child/AC-injection/watchdog-injection/Sleep tests and classification pass only if status READY; exact per-test evidence retained.',
        f'Comparable seven-pair warmed dummy overhead:wall{perf["median_wall_overhead_fraction"]:.6g},processCPU{perf["median_process_CPU_overhead_fraction"]:.6g}; acceptable gate={perf["acceptable_for_controlled_pilot"]}. APoverheadUNKNOWN.',
        'Typed observer70/instrumentation status versus originalnumeric71 and explicit supervisor reasons separate all7 requested statuses; no generic scientific-failure relabeling.',
        'C/w evaluator and AO/source/provenance/precision/quadrature unchanged. Dummy fixture outputs never enter scientific cache.',
        status+' for controlled separately authorized pilot only; not AP convergence/full-run profile/publication certification.',
        'Fresh explicitapproval/exactpair/request/cachekey/deadline, stableAC/nativeJob/temporarySleep/noorphan/provenance/revalidatedentry required beforeA.',
        'Recommend fresh90min total wall, sourceA<=75min, finalreserve>=15min, sequential1attempt, noauto retry. No currentAPauthorization.',
        'A may narrow one bracket side or change selectedVA; evaluate original26metrics/AO afterward. Completing one paired P1step still conditionally needs5.50625; no guaranteedKgain or convergence.'
    ]
    report['all_12_answers']=answers
    lines=['# Observer v2 recovery readiness','',status,'',
       'No AP/source/MI/Holevo/SKR rerun or new optimization invocation. Dummy numerical leaves only; old scientific artifacts preserved.',
       '', '## Twelve required answers','']
    lines += [f'{i}. {answer}' for i,answer in enumerate(answers,1)]
    lines += ['', '## Verified saved AO baseline','',
      f"147 sources/3822savedobjective rows;129starts/283iterations/26catalogmatches; actual saved monotonicity violations={len(baseline['monotonicity_violations_over_existing_tolerance'])}.",
      'Reference(.165,5.5),K.07798099387393764;22km(.165,5.475),K.07661740491526092. Both finitecatalog maxima only.',
      '0 completed coordinate searches,55 missingpairs, numerical ordering error-unbounded. No interpolation, fitting, changedsettings or globaloptimum claim.',
      '', '## Validation and safety','',
      f"{report['test_count']} regression tests PASS;{report['protected_hash_count']} protected hashes unchanged; native tests recorded individually. No orphan={report['no_orphan_workers']}.",
      'Native temporary Sleep restoration receipts retained; no permanent powerplan changes. Frozen historicalhash discrepancy remains PREEXISTING_UNCHANGED; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.',
      'Ponytail: reuse original provenance/supervisor/observer and stdlib, with only typedexecutionentry/harness added. Readiness is transient and not permission to launch AP.',
      'STOP. Proposed90min/75minA pilot requires explicit approval. Old overnight8h budget not reused.']
    (OUT/'observer_v2_recovery_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
