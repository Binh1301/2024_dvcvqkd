"""Saved-artifact diagnostic only: no imports/calls to scientific evaluators."""
import ast
import cProfile
import csv
import hashlib
import inspect
import json
import math
from pathlib import Path
import pstats
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload

BASE = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation'
PHASE = BASE / 'phase_2A'
OUT = BASE / 'source_bottleneck_diagnostic'
REF = 21.9393102292
PAIRS = {'A': (.165, 5.49375), 'B': (.16375, 5.5),
         'C': (.16531250000000003, 5.5)}
SETTINGS = {'density_eigenvalue_tolerance': 1e-12,
            'physicality_tolerance': 1e-10, 'precision_ladder': [1050,1250,1450]}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                      allow_nan=False) + '\n', encoding='utf-8')


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return 'Infinity' if value > 0 else '-Infinity' if value < 0 else 'NaN'
    if isinstance(value, dict):
        return {k: clean(v) for k,v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def write_csv(name, data):
    fields = list(dict.fromkeys(k for row in data for k in row))
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(clean(v)) if isinstance(v,(dict,list))
                         else clean(v) for k,v in row.items()} for row in data)


def profile_summary(path):
    stats = pstats.Stats(str(path))
    def record(item):
        (file, line, function), v = item
        return {'file':file, 'line':line, 'function':function, 'calls':v[1],
                'self_seconds':v[2], 'cumulative_seconds':v[3]}
    return {'path':relative(path), 'sha256':digest(path),
            'captured_self_seconds':stats.total_tt,
            'top_self': [record(x) for x in sorted(stats.stats.items(),
                        key=lambda item:item[1][2], reverse=True)[:12]],
            'worker_frames':[record(x) for x in stats.stats.items()
                             if x[0][0].endswith('full_support_c4_worker.py')],
            'eighe_calls':sum(v[1] for k,v in stats.stats.items() if k[2]=='eighe')}


def dummy_profile_check():
    """Reproduce existing collector behavior using only trivial dummy work."""
    profiler = cProfile.Profile()
    def before_dump():
        return sum(range(1000))
    def after_dump():
        return sum(range(1000))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)/'dummy.prof'
        profiler.enable()
        before_dump()
        thread = threading.Thread(target=lambda:profiler.dump_stats(str(path)))
        thread.start()
        thread.join(timeout=3)
        assert not thread.is_alive()
        after_dump()
        profiler.dump_stats(str(path))
        functions = {k[2] for k in pstats.Stats(str(path)).stats}
    return {'before_dump_recorded':'before_dump' in functions,
            'after_dump_recorded':'after_dump' in functions,
            'real_AP_invoked':False,
            'dump_stats_source':inspect.getsource(cProfile.Profile.dump_stats),
            'create_stats_source':inspect.getsource(cProfile.Profile.create_stats)}


def halving_analysis(radius, tolerance=1e-6, cap=4):
    """Conditional geometric arithmetic, never an SKR prediction."""
    n=max(0,math.ceil(math.log2(radius/tolerance)))
    return {'radius':radius, 'tolerance':tolerance,
            'conditional_halving_steps':n, 'radius_after_four':radius/2**cap,
            'entry_check_steps_allowed':cap-1,
            'qualification':'Incumbent unchanged; both exact midpoint partners valid. Not a convergence/runtime guarantee.'}


def original_settings():
    tree=ast.parse((ROOT/'scripts/run_theta10_D55_alt_opt.py').read_text())
    names={'K_TOLERANCE','PARAMETER_TOLERANCE','MAX_AO_ITERATIONS',
           'MAX_BOUNDARY_EXPANSIONS','MAX_REFINEMENT_STAGES'}
    return {node.targets[0].id:ast.literal_eval(node.value)
            for node in tree.body if isinstance(node,ast.Assign)
            and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and node.targets[0].id in names}


def main():
    started=time.monotonic()
    if OUT.exists():
        raise FileExistsError('Diagnostic output exists; preserve previous artifacts')
    protected=read(PHASE/'protected_input_manifest.json')
    # Freeze every prior Phase1/2A artifact as well as all actually inspected records.
    for path in BASE.rglob('*'):
        if path.is_file(): protected[relative(path)]=digest(path)
    ledger_paths=list((ROOT/'results').glob('**/source_generation_ledger.json'))
    histories=[]
    for path in ledger_paths:
        if 'checkpoint' in path.as_posix(): continue
        protected[relative(path)]=digest(path)
        for index,attempt in enumerate(read(path).get('attempts',[])):
            histories.append({'ledger':relative(path),'index':index, **attempt})
    current=rows(PHASE/'expanded_source_catalog.csv')
    checkpoint=read(PHASE/'objective_checkpoint.json')
    comparisons=rows(PHASE/'old_vs_new_skr_optimum.csv')
    assert len(current)==147 and len(checkpoint)==26
    assert sum(len(v['rows']) for v in checkpoint.values())==3822
    assert all(float(r['delta_K'])==0 and r['AO_match']=='True' for r in comparisons)
    settings=original_settings()
    assert settings=={'K_TOLERANCE':1e-8,'PARAMETER_TOLERANCE':1e-6,
                     'MAX_AO_ITERATIONS':6,'MAX_BOUNDARY_EXPANSIONS':3,'MAX_REFINEMENT_STAGES':4}
    inventory={}
    for path in (ROOT/'results').glob('**/exact_source_cache/*.json'):
        if 'checkpoint' not in path.as_posix(): inventory.setdefault(path.stem,[]).append(path)
    provenance=[]
    for row in current:
        candidates=inventory[row['source_cache_key']]
        payload=read(candidates[0]); verified=verify_source_payload(payload,SETTINGS)
        assert payload['ensemble_hash']==row['ensemble_hash']
        assert pair(float.fromhex(payload['nu_mb_raw_hex']),float.fromhex(payload['V_A_hex']))==pair(row['nu_raw'],row['V_A'])
        assert all(float(payload[k])==float(row[k]) for k in ('C','w'))
        for path in candidates: protected[relative(path)]=digest(path)
        provenance.append({'cache_key':row['source_cache_key'],'source_path':relative(candidates[0]),
                           'source_sha256':digest(candidates[0]),'verification':verified})
    timeline=[]; profiles=[]; selected_history=[]
    for label,(nu,va) in PAIRS.items():
        matching=[r for r in histories if pair(r.get('nu_raw',-1),r.get('V_A',-1))==pair(nu,va)]
        assert matching
        attempt=matching[-1]; key=attempt['cache_key']
        records=[]
        for path in (ROOT/'results').glob('**/probe_results/'+key+'*'):
            if not path.is_file():continue
            protected[relative(path)]=digest(path)
            records.append(relative(path))
            if path.suffix=='.prof':profiles.append(profile_summary(path))
        supervision=attempt.get('supervision',{}); watch=supervision.get('power_watch',{})
        p=next(p for p in profiles if Path(p['path']).stem==key)
        selected_history.append({'probe':label,'attempt_records':matching,'all_probe_artifacts':records})
        timeline.append({'probe':label,'nu_raw':nu,'V_A':va,'nu_raw_hex':nu.hex(),'V_A_hex':va.hex(),
            'cache_key':key,'started_utc':attempt.get('started_utc','NOT_RECORDED_IN_FINAL_RECORD'),
            'stopped_utc':'NOT_RECORDED_AS_A_DISTINCT_TIMESTAMP',
            'wall_seconds':attempt['wall_seconds'],'cpu_seconds':attempt.get('cpu_seconds'),
            'cpu_scope':'WINDOWS_JOB_BASIC_ACCOUNTING_AGGREGATE_NOT_EXCLUSIVE_AP',
            'aggregate_cpu_to_wall_ratio':attempt['cpu_seconds']/attempt['wall_seconds'],
            'raw_status':attempt['status'],'interpreted_status':'SAFETY_ABORT' if label=='A' else attempt['status'],
            'termination_reason':watch.get('abort_reason') or attempt.get('error') or 'UNKNOWN',
            'wrapper_returncode':supervision.get('returncode'),'AP_worker_exit_status':'NOT_SEPARATELY_RECORDED',
            'AP_child_pid':'NOT_RECORDED','probe_wrapper_pid':24332 if label=='A' else 'NOT_RECORDED',
            'pid_evidence':'docs/PROJECT_STATE.md historical EVID-0146 snapshot' if label=='A' else 'NOT_RECORDED',
            'deadline_seconds':attempt.get('timeout_seconds'),
            'internal_instrumented_AP_timeout_seconds':attempt.get('timeout_seconds',3600)-8,
            'AC_before':supervision.get('sleep_prevention',{}).get('power_before',{}).get('ac','NOT_RECORDED'),
            'AC_last':watch.get('last_power',{}).get('ac','NOT_RECORDED'),
            'sleep_active':supervision.get('sleep_prevention',{}).get('active_verified','NOT_RECORDED'),
            'sleep_restored':supervision.get('sleep_prevention',{}).get('released_verified','NOT_RECORDED'),
            'watchdog_gaps':watch.get('poll_gaps','NOT_RECORDED'),
            'memory_measurements':'NOT_RECORDED','numerical_precision_progress':'NOT_RECORDED',
            'last_verified_progress':'Initial AP _row/_sectors, first ~10s; no retained eighe calls; later stage UNKNOWN',
            'captured_profile_seconds':p['captured_self_seconds'],
            'final_valid_C_w':False,'evidence':attempt['ledger'],'profile':p['path']})
    nearby=[]
    for row in current:
        nu,va=float(row['nu_raw']),float(row['V_A'])
        if not ((nu==.165 and va in (5.475,5.4875,5.5,5.5125,5.525)) or (va==5.5 and .15<=nu<=.17)):continue
        matches=[r for r in histories if pair(r.get('nu_raw',-1),r.get('V_A',-1))==pair(nu,va)]
        successes=[r for r in matches if r['status']=='COMPLETED_EXACT']
        done=successes[-1] if successes else {}
        source=next(r for r in provenance if r['cache_key']==row['source_cache_key'])
        nearby.append({**row,'wall_seconds':done.get('wall_seconds','NOT_RECORDED'),
             'Job_CPU_seconds':done.get('cpu_seconds','NOT_RECORDED'),
             'runtime_evidence':done.get('ledger','NOT_RECORDED'),
             'all_historical_attempts':[{k:r.get(k) for k in ('ledger','status','wall_seconds','cpu_seconds','timeout_seconds')} for r in matches],
             'precision_ladder':[1050,1250,1450], 'source_path':source['source_path'],
             'source_sha256':source['source_sha256'],'source_evaluator_identity':source['verification']['implementation'],
             'validation':'VERIFIED_FULL_SUPPORT_CACHE; full precision rows not serialized in payload'})
    searches=read(PHASE/'reference_targeted_coordinate_searches.json')
    priorities=[]
    ordered=[(.165,5.49375,'P1','SAFETY_ABORT_NOT_TIMEOUT'),
             (.165,5.50625,'P1','UNMEASURED_RUNTIME'),
             (.16531250000000003,5.5,'P2','PRIOR_60MIN_TIMEOUT'),
             (.16375,5.5,'P2','PRIOR_60MIN_TIMEOUT'),
             (.165,5.4625,'22km P1','PRIOR_AC_ABORT'),
             (.165,5.481249999999999,'22km P1','UNMEASURED_RUNTIME'),
             (.0825,5.475,'22km P2','UNMEASURED_OUTER'),
             (.4,1.5,'nu0=.8 P1','UNMEASURED_OUTER'),
             (.2,3.,'nu0=.8 P2','UNMEASURED_OUTER')]
    missing=rows(PHASE/'remaining_missing_exact_pairs.csv')
    for i,(nu,va,coord,risk) in enumerate(ordered,1):
        found=next((r for r in missing if pair(r['nu_raw'],r['V_A'])==pair(nu,va)),None)
        assert found is not None
        requests=json.loads(found['requests'])
        priorities.append({'priority':i,'nu_raw':nu,'V_A':va,'nu_raw_hex':nu.hex(),'V_A_hex':va.hex(),
            'coordinate':coord,'blocking_condition':'Missing original paired midpoint' if i<=6 else 'Missing original outer request',
            'diagnostic_value':'Unblock relevant coordinate evidence; gain UNKNOWN; closure not guaranteed',
            'runtime_risk':risk,'affected_distances':sorted({r['L_km'] for r in requests}),
            'recorded_request_count':len(requests),'execution':'NOT_RUN_NEW_APPROVAL_REQUIRED'})
    blockers={}
    for s in searches:
        data=[]
        for event in s['source_missing']:
            value=float(event['value']);nu,va=(s['fixed'],value) if s['variable']=='V_A' else (value,s['fixed'])
            data.append({'L_km':REF,'coordinate':s['label'],'nu_raw':nu,'V_A':va,
              'nu_raw_hex':float(nu).hex(),'V_A_hex':float(va).hex(), 'bracket':s['bracket'],
              'best_value':s['best_value'],'best_K':s['best_K'],'status':s['status'],
              'blocked_step':'FIRST_PAIRED_MIDPOINT_REQUEST_IN_CURRENT_CALL',
              'both_partners_required_for_completed_step':True,'evidence':'phase_2A/reference_targeted_coordinate_searches.json'})
        blockers[s['label']]=data
    reproduction=dummy_profile_check()
    assert reproduction['before_dump_recorded'] and not reproduction['after_dump_recorded']
    OUT.mkdir()
    save('protected_input_manifest.json',protected)
    save('execution_history_and_profiles.json',clean({'histories':selected_history,'profiles':profiles,
                                                   'dummy_profile_reproduction':reproduction,'nearby_source_provenance':provenance}))
    write_csv('failed_probe_timeline.csv',timeline)
    write_csv('source_runtime_comparison.csv',nearby)
    write_csv('reference_P1_blockers.csv',blockers['P1'])
    write_csv('reference_P2_blockers.csv',blockers['P2'])
    write_csv('missing_source_priority.csv',priorities)
    for name,body in DOCUMENTS.items():
        (OUT/name).write_text(body.strip()+'\n',encoding='utf-8')
    test_records=[]
    for pattern in ('test_source_bottleneck_diagnostic.py','test_ao_phase2a_execution.py',
                    'test_ao_phase2a_preparation.py','test_ao_phase2a_resume.py',
                    'test_ao_numerical_optimum_audit.py','test_windows_sleep_safe_supervision.py',
                    'test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
        result=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover',
                    '-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        test_records.append({'pattern':pattern,'returncode':result.returncode,'output':result.stdout+result.stderr})
        if result.returncode:raise AssertionError(test_records[-1])
    save('regression_tests.json',test_records)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,(diff.stdout,diff.stderr)
    after={name:digest(ROOT/name) for name in protected}
    assert protected==after,'Protected scientific or prior artifact bytes changed'
    save('input_manifest_after.json',after)
    report={'status':'CURRENTLY_VERIFIED_PASS_FOR_CACHE_ONLY_DIAGNOSTIC',
      'scientific_computation_executed':False,'AP_workers_launched':0,'new_source_moments':0,
      'new_SKR_evaluations':0,'new_AO_runs':0,'operational_fixes_implemented':False,
      'MB_sources':147,'saved_objective_rows':3822,'AO_catalog_matches':26,'new_coordinate_closures':0,
      'bottleneck_status':'BOTTLENECK_NOT_LOCALIZED', 'profile_collector_status':'FIRST_DUMP_DISABLES_PROFILER_REPRODUCED',
      'timeline':timeline,'priority':priorities,'source_runtime_comparison':nearby,
      'refinement_arithmetic':{'P1':halving_analysis(.0125),'P2':halving_analysis(.0025)},
      'settings':settings,'conclusions':CONCLUSIONS,
      'precision_progress_before_timeout':'UNKNOWN_BEYOND_STARTUP_SECTOR_CONSTRUCTION',
      'safe_partial_AP_resume':'NOT_SUPPORTED_OR_PROVEN_EQUIVALENT',
      'recommended_plan':'Plan A after separate approval for minimal observability fixes and exact probes',
      'regression_test_count':sum(int(line.split()[1]) for r in test_records for line in r['output'].splitlines() if line.startswith('Ran ')),
      'tests':'CURRENTLY_VERIFIED_PASS','git_diff_check':'CURRENTLY_VERIFIED_PASS',
      'protected_hashes_unchanged':len(protected),'diagnostic_wall_seconds':time.monotonic()-started,
      'producer_sha256':digest(Path(__file__)), 'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
      'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'dirty_worktree':'PREEXISTING_PRESERVED',
      'frozen_spec_sha256':digest(ROOT/'docs/FINAL_MODEL_SPEC.md'),
      'historical_frozen_hash_discrepancy':'PREEXISTING_UNCHANGED',
      'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS', 'outputs':sorted([*DOCUMENTS,'failed_probe_timeline.csv',
        'source_runtime_comparison.csv','reference_P1_blockers.csv','reference_P2_blockers.csv','missing_source_priority.csv','diagnostic_report.md','diagnostic_report.json'])}
    save('diagnostic_report.json',clean(report))
    lines=['# Exact source bottleneck diagnostic','',report['status'],'',
      'Cache/log/code inspection only. No AP, new source, channel, MI/Holevo, SKR or AO execution; no operational fix applied.',
      '', '| Probe | Wall seconds | Job CPU seconds | Termination | Last verified progress | Evidence |',
      '|---|---:|---:|---|---|---|']
    lines += [f"| {r['probe']} ({r['nu_raw']!r},{r['V_A']!r}) | {r['wall_seconds']} | {r['cpu_seconds']} | {r['interpreted_status']} | Initial sector construction ~10s; later UNKNOWN | {r['evidence']} |" for r in timeline]
    lines += ['', '## Twelve required conclusions','']
    for i,c in enumerate(CONCLUSIONS,1):
        lines += [f"{i}. {c['question']}",f"   VERIFIED: {c['verified']}",f"   INFERENCE: {c['inference']}",
                  f"   UNKNOWN: {c['unknown']}",f"   PROPOSED: {c['proposed']}",f"   EVIDENCE: {c['evidence']}",'']
    lines += ['## Validation','',f"{report['regression_test_count']} current regression tests PASS; {len(protected)} protected hashes unchanged; git diff --check PASS.",
      'Prior Phase1/2A files preserved. Existing frozen-spec historical hash discrepancy unchanged; no lifecycle promotion.',
      'All plans NOT_RUN, require explicit separate scope/budget approval. Current finite maximum is not a continuous/global certificate.',
      'Ponytail: stdlib pstats/cProfile and original provenance checker reused; no scientific driver imported or new dependency installed.']
    (OUT/'diagnostic_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','bottleneck_status','MB_sources','regression_test_count','protected_hashes_unchanged','diagnostic_wall_seconds')},indent=2))


CONCLUSIONS = [
    {'question':'Why did the two P2 sources time out?',
     'verified':'B and C exhausted the instrumented AP limit (~3592s); B wrapper exited0 after reporting TIMEOUT, C Job returned124. Both lack final valid C,w.',
     'inference':'Job CPU/wall ~0.965 and ~0.978 is consistent with expensive active computation, not a mostly idle worker.',
     'unknown':'Exact late-stage cause, completed precision rows and remaining work; timeout is not mathematical impossibility.',
     'proposed':'Obtain valid full-duration observations before attributing delay or predicting runtime.',
     'evidence':'failed_probe_timeline.csv; original probe JSON/error; execution_history_and_profiles.json'},
    {'question':'Were the failed probes making numerical progress?',
     'verified':'Their first ~10s profiles record original _row/_sectors and exp/sqrt arithmetic; Job CPU accumulated for most of the run.',
     'inference':'They entered genuine AP computation; aggregate CPU is not proof of later precision/eigenvalue convergence.',
     'unknown':'Progress after the first profile dump; no rank/C/w milestones survive.',
     'proposed':'Original-operation stage/precision milestones and independent CPU/working-set samples, approval required.',
     'evidence':'profiles and dummy reproduction; full_support_c4_worker.py main/_row'},
    {'question':'Which stage is the primary bottleneck?',
     'verified':'All retained target profiles stop at initial sector construction; dump_stats calls create_stats which disables the profiler, reproduced on dummy work.',
     'inference':'exp/sqrt dominate only the captured startup interval; spectral/LU/matrix stages are static cost candidates, not measured bottlenecks.',
     'unknown':'BOTTLENECK_NOT_LOCALIZED for the full computation.',
     'proposed':'Approve minimal observer correction; never substitute formulas/precision or claim eighe is the measured bottleneck.',
     'evidence':'source_evaluator_stage_audit.md; stdlib cProfile source; execution_history_and_profiles.json'},
    {'question':'Resource exhaustion, suspension or numerical difficulty?',
     'verified':'A has15.578s watchdog gap/AC0 and safety Job125; B/C recorded float64 gate rejection with tiny negative eigenvalues. C AC1/no recorded gap; B has no power watch.',
     'inference':'Gate rejection explains why original AP fallback is required; it does not quantify physical AP conditioning or prove singularity.',
     'unknown':'No RSS/commit/page-fault time series, AP eigenspectrum or OS suspend event record; no supported OOM/stall diagnosis.',
     'proposed':'Retain safety stop classification and add approved nonnumerical resource telemetry.',
     'evidence':'supervisor receipts; fast_path_gate; supervisor_and_power_audit.md'},
    {'question':'Can operational improvements reduce runtime?',
     'verified':'Collector loses profiling after its first dump; redundant preflight gate and unused MI-noise allocation exist outside source evaluation. No timing establishes their material overhead.',
     'inference':'Stable AC and valid observability can prevent wasted interruptions; speedup of the mathematical worker is unmeasured.',
     'unknown':'Magnitude of profiling overhead or setup savings; no promised runtime reduction.',
     'proposed':'Approve observer/ledger improvements separately; do not replace LU, precision, quadrature, backend or scientific operations.',
     'evidence':'probe_worker; ExactMBEvaluator.__init__; profile_worker; local mpmath linalg.py'},
    {'question':'Is safe partial AP checkpoint/resume feasible?',
     'verified':'Existing .prof is timing data, not matrices/arbitrary-precision state. Full source JSON commits atomically only after successful evaluator validation.',
     'inference':'Completed-source reuse/campaign continuation is safe under exact identity; within-source resume is not supported.',
     'unknown':'No demonstrated bit-consistent AP continuation checkpoint schema or round-trip equivalence.',
     'proposed':'Restart an approved failed source from original inputs; do not resume partial numeric state.',
     'evidence':'checkpoint_resume_feasibility.md; worker.main; source_moments atomic source write'},
    {'question':'Which source should be prioritized next?',
     'verified':'(.165,5.49375) is still the current lower P1 midpoint and was safety-aborted, not numerically timed out.',
     'inference':'It is a defensible lower demonstrated timeout-risk first attempt, followed conditionally by current upper partner(.165,5.50625).',
     'unknown':'Its completion time and K; the unmeasured partner can also be costly.',
     'proposed':'Plan A, only after new scope/budget and stable AC/approved observations.',
     'evidence':'missing_source_priority.csv; reference_P1_blockers.csv'},
    {'question':'Minimum useful source set for P1/P2 advancement?',
     'verified':'Current paired-step dependencies are four missing sources: (.165,5.49375),(.165,5.50625),(.16375,5.5),(.16531250000000003,5.5). The old VA5.5125 is already measured.',
     'inference':'One source gives useful evidence; both current partners per coordinate allow one paired stage on that fixed slice. If an incumbent moves, recalculate actual dependencies.',
     'unknown':'Whether any source changes the incumbent, which may change the next P2 fixed VA.',
     'proposed':'Follow original midpoint requests adaptively, not an automatic stale rectangular batch.',
     'evidence':'reference_P1_blockers.csv; reference_P2_blockers.csv; original adaptive_maximize_1d'},
    {'question':'What further refinement is needed?',
     'verified':'Current reference radii .0125/.0025 exceed1e-6. Unchanged-best paired halving needs14/12 total stages, or13/11 after one successful pair.',
     'inference':'More exact moments are needed; four-step inner cap is insufficient on those current brackets. Tolerance is checked at next loop entry, not after the fourth pair.',
     'unknown':'Actual refined path and source count when winners move; geometric counts are conditional.',
     'proposed':'Prepopulate only original requested exact points with approval and rerun original AO on progressively narrowed cache; settings changes require separate decision.',
     'evidence':'ao_optimum_completion_criteria.md; original search loop; diagnostic_report.json refinement_arithmetic'},
    {'question':'What prevents a numerical coordinate optimum claim?',
     'verified':'Both selected searches have missing partners,0 closed selected directions; nu0=.8 remains boundary-blocked; strictnu>0 excludes mathematicalnu=0.',
     'inference':'Catalog maximum and DeltaK0 are not coordinate convergence. Local bracketing also does not exclude remote nonmonotone maxima.',
     'unknown':'Continuous coordinate/global maxima and boundary limits.',
     'proposed':'Complete both searches at the actual selected pair, verify boundaries, stopping/status history and justify competing starts.',
     'evidence':'saved original AO/P1/P2 histories; ao_optimum_completion_criteria.md'},
    {'question':'Which numerical accuracy evidence is missing?',
     'verified':'Four prior metric repeats were bit-exact; source identity/support valid; smallest relevant top-two K gaps ~7.83e-8(reference)/1.73e-7(22km).',
     'inference':'Repeatability is not a totalK error enclosure. Declared C/w comparison tolerances cannot be directly interpreted as a K uncertainty.',
     'unknown':'Candidate-specific AP/MI-quadrature/entropy/roundoff error propagation sufficient for1e-8 stopping or displayed digits.',
     'proposed':'Plan separate approved accuracy evidence without lowering precision or changing evaluators; withhold unsupported digits/ordering confidence.',
     'evidence':'Phase1/2A numerical_accuracy_status.md and original_evaluator_reproducibility.csv'},
    {'question':'Which continuation plan supports manuscript optimization?',
     'verified':'147-source AO/catalog agreement26/26 is finite evidence, not convergence. Neither plan is authorized to execute here.',
     'inference':'Plan A plus valid observation is the best first cost-controlled step; Plan B is necessary if actual selected P2 dependencies persist.',
     'unknown':'Whether any finite planned batch completes the numerical optimum.',
     'proposed':'Request separate approval for minimal operational observation fixes, then Plan A; dedicated120min P2 attempt conditional on real progress/safety and approval, not a completion promise.',
     'evidence':'conservative_continuation_plan.md; difficult_P2_continuation_plan.md'}
]

DOCUMENTS = {
'source_evaluator_stage_audit.md': """
# Original source evaluator stage audit

Status: BOTTLENECK_NOT_LOCALIZED. Code inspection and saved profiles only.

## Actual call graph and stages

`probe_worker -> build_mb_ensemble/reference_ensemble -> ExactMBEvaluator.source_moments
-> c4_gram_source_moments -> _fast gate -> _fallback subprocess
-> profile_worker -> original full_support_c4_worker.main -> _row`.

1. qam256.py constructs16x16 points, canonical normalization and normalized MB PMF.
   run_exact_mb_test2.py mapsnu_repo=42.5nu_raw and uses reference_ensemble at VA.
   No peak/VA box in this experiment; original ensemble validation preserved.
2. gram_moments.py extracts64 C4 prototypes/probabilities and four64x64 complex128
   Gram sectors. Detached eigh gate checks positivity/condition<=1e6/residual<=1e-12.
   B/C and completed5.5125 reject the gate (tiny negative binary64 eigenvalues),
   so the AP fallback is justified by actual route records. GateInfinity is not a
   measured AP condition number, nor proof of physical singularity.
3. Exact float.hex input goes to worker; original mp.workdps1050/1250/1450.
   Each row rebuilds four rotational overlap blocks (64x64), projects four
   Hermitian C4 sectors, then calls mp.eighe on each. 12 eighe calls if all rows finish.
4. Rank/minimum eigenvalue are checked. Rank!=256 returns unresolved row; resolved
   row performs original eigenbasis operator transforms, diagonal roots, two
   64-right-hand-side _lu_solve_matrix operations per sector and matrix products.
   Up to512 scalar-RHS lu_solve calls per resolved precision row (1536 if all3
   resolved). This is static work count, not actual retained run progress.
   Installed mpmath lu_solve copies A/b and adds10 bits inside each solve;
   LU_decomp caches on its copy. No evidence that sibling RHS solves share a
   factorization. Potential repeated work INSIDE the scientific evaluator is
   not authorized for replacement, including diagonal division/factor reuse.
5. C is computed by the original trace sums; w is the nonnegative weighted
   residual norm after original a/q/t/d transforms. No alternative formula.
6. Last two precision rows must have rank256/resolved and C/w agree under
   original1e-7+1e-6*max(abs(values)). JSON is emitted only after all rows.
   Parent converts C/w to float64, checks finite/physical values, ensemble hash
   consistency/support and atomically commits source cache. Cache retains final
   C/w, support and precision identity, NOT full intermediate convergence rows.

## Timing evidence and the collector defect

All target profiles, including SUCCESSFUL(.165,5.5125), have only about10s
captured self-time and one _row/_sectors frame, zero retained eighe calls.
They are fresh/long-lived files, but a recent mtime does not mean a full profile.
profile_worker snapshots every10s using profiler.dump_stats from a thread.
Installed stdlib dump_stats calls create_stats; create_stats calls disable().
Dummy-only reproduction confirms before-dump work recorded and after-dump work
absent. No reenabling is present in the original collector. This is a verified
OBSERVABILITY defect, not a proven numerical evaluator stall: completed source2
works despite the same truncated profile. Do not assign first10s hotspots to the
whole60min computation. Stage timings, precision completion/rank histories and
AP eigenspectra are NOT_RECORDED after that interval.

High precision is required by the preserved policy/float64 gate failure, but
these records do not prove exactly how many digits each failed source needs.
Neighboring successes and failures demonstrate heterogeneous elapsed outcomes;
without full-stage measurements, cannot distinguish intrinsic parameter cost,
precision-row resolution pattern, profiler effect or machine contention.

## Minimum proposed observations (NOT IMPLEMENTED)

Approve a separate execution-only observer change: profiler owned/reset/enabled
on its computation thread or independent stack sampling; dummy-validate full
capture first. Add stderr-only stage/precision start/end milestones without
changing call order/values, rank summaries already computed by original worker,
and external PID/Job CPU, monotonic+UTC, working set/commit and power samples.
Keep stdout result protocol and exact identity untouched. Any instrumented run
must prove same source inputs/operations/precision/validation/provenance; logging
overhead is measured, not assumed harmless or a speedup. No real AP launched.

Evidence: original worker/gram_moments.py/probe_worker/profile_worker,
execution_history_and_profiles.json and source_runtime_comparison.csv.
""",
'supervisor_and_power_audit.md': """
# Supervisor and Windows power audit

Verified original bounded_process uses absolute monotonic polling, Windows Job
KILL_ON_JOB_CLOSE plus aggregate Job user-CPU ceiling, process wait and final
handle/worker cleanup. Windows Job CPU accounting is aggregate, not exclusive
AP timing. Starts process before Job assignment: a small containment setup race
is a code-level concern, not evidence of escaped workers in these runs. A
suspended-start/assign/resume operational design would require separate approval.

Sleep-safe layer requests ES_CONTINUOUS|ES_SYSTEM_REQUIRED on the owning thread,
verifies/restores prior state and checks AC/noncritical battery before run.
Watchdog polls0.2s, aborts on ACunsafe/readfailure or gap>5s, records gap/lastpower;
5s operational deadline margin and full Job termination remain. This prevents
automatic idle Sleep, not manual suspend, critical hibernation/shutdown or power
loss. A watchdog cannot run during OS suspension; no universal strict wall-time
guarantee during suspension. Overrun must fail even if cleanup later succeeds.

A: initialAC1, laterAC0,15.578s gap, Job125 safety stop at1799.031s; actual
suspension versus scheduler delay UNKNOWN. Do not relabel numerical timeout.
B: old Job return0 after internal AP timeout; no AC/Sleep monitoring receipt
retained for this attempt, so do not infer AC1 or absence of sleep from missing
fields. C: AC1 before/last, no recorded gap, Sleep acquired/restored; AP timeout
and Job124. No stored periodic CPU/RSS/heartbeat history localizes a stall.
Outer45s heartbeat messages, if surfaced in a transient session, report only
elapsed supervision, not numerical progress; retained probe logs only final JSON
or are empty. Missing start/stop timestamps/PIDs explicitly labeled in CSV.

Operational proposals ONLY: stable wiredAC/user no manual Sleep, durable
start/end UTC+monotonic/PID and periodic JobCPU/power/resource/event logs,
atomic append/update ledgers, explicit stop-reason precedence and time reserve.
Use rising CPU and stack changes as diagnostics, not proof of numerical
convergence; no automatic kill/retry of a slow active evaluator based solely on
CPU. Separate source/objective/AO/report workers already exist and should keep
one absolute deadline, final reserve and fulltree cleanup. No power plan changed,
no real AP run or supervisor fix here. Existing scoped dummy regression tests
are run; native continuous heartbeat telemetry remains a proposed enhancement.

Timeout interaction: gram_moments default subprocess timeout3600s, BUT approved
probe_worker intercepts that exact worker launch and sets per_probe_timeout-8s.
Thus a separately approved120min outer limit can actually extend inner AP in
that instrumented path, without changing numerical worker. Increasing ONLY an
unintercepted outer supervisor would leave inner3600s ceiling in place. Inspect
the actual chosen command path before any future dedicated budget approval.
""",
'checkpoint_resume_feasibility.md': """
# Checkpoint and resume feasibility

VERIFIED: exact source caches commit temporary JSON then atomic replace after
final validation. Objective checkpoints and attempted-source ledgers preserve
completed identities; campaign continuation skips attempted sources, retains
original deadline and protects old results. This is resume BETWEEN completed
probes, not resume WITHIN an arbitrary-precision operation. Preserved .prof files
hold timings/call counters only, not eigenvectors/matrices/precision state.

Worker.main builds all rows in memory and emits only final JSON; no persisted
precision/sector/eighe/LU position or resumption API. No serialized active
mpmath context, exact binary operands, convergence loops, intermediate state
and validation equivalence proof. Purely partial precision rows also do not
exist as validated durable checkpoints for the failed sources.

Conclusion: safe partial-source resume NOT_SUPPORTED_OR_PROVEN_EQUIVALENT.
Use valid completed source cache under original provenance; an explicitly
approved retry must restart original calculation from original binary64 inputs.
Do not reconstruct moments/eigenvectors from profiles or use lower precision.

A future checkpoint proposal would need exact round-trip mp numbers (not float
or limited nstr decimals), context/operation position, all validation state,
code/settings/source identity, atomic durable commit and interrupted-versus-
uninterrupted equivalence on representative full-support runs. Intra-eighe state
is not exposed by this implementation. Such engineering is out of scope and may
cost more than an uninterrupted restart; it is not recommended as the immediate
path. No checkpoint/resume changes implemented.
""",
'conservative_continuation_plan.md': """
# Plan A: conservative coordinate progress (PROPOSED, NOT_RUN)

Recommended first plan. First obtain explicit approval for minimal execution-only
observability correction/durable telemetry, test on dummy work, then fresh exact
probe budget. No existing source evaluator/settings change or automatic retry.
AC stable/Sleep+Job native safety checks before each attempt. Reserve>=8min final
processing/cleanup and include all work in a single newly approved wall budget.

1. (.165,5.49375), exactbinary64hex from missing_source_priority.csv. Directly
   measures lower P1; its prior1799s safety-abort is NOT a60min numerical timeout.
   Recommend60min ceiling, because nearby successful P1 measured2159/2178/2723s,
   not as a completion prediction. Inspect valid C/w/provenance and full-duration
   original-operation observations, compute original26 SKRs and genuine cache-only
   AO only if separately authorized. Reassess actual selected pair/searches.
2. Conditional: (.165,5.50625), binary64VA5.5062499999999996, only if still the
   original selected P1 upper midpoint after1. It is unmeasured, so runtime risk
   UNKNOWN; recommend another60min ceiling, not extrapolated runtime. If winner
   changes, follow newly returned original dependencies; do not automatically
   execute a different unapproved pair.
3. Stop after the approved pair set, report actual bracket/status/remaining
   dependencies/error evidence. If a probe safety-aborts, stop campaign and
   restore safe conditions; no automatic retry. On timeout, no invented moments;
   record observations and request direction rather than escalating automatically.

Suggested fresh envelope if BOTH P1 sources approved:130min total (2x60min+
10min processing), sequential, no otherAP, deadline of last probe shortened for
reserve. This is a proposal only, not a carryover of the expired3h Phase2A budget.
Either source may fail within60min. Minimum useful evidence is one source;
complete current paired P1 stage requires both if the fixedslice/incumbent stays.
No promise of improved K or coordinate closure. After these, prioritize actual
P2 dependencies, then22km and unresolved nu0=.8 searches. Numerical error evidence
must be planned alongside coverage, not after many catalog-growth batches.
""",
'difficult_P2_continuation_plan.md': """
# Plan B: complete the difficult P2 paired step (PROPOSED, NOT_RUN)

Only if the selected/reference P2 remains fixedVA5.5 after Plan A. The current
pair is lowernu.16375 and uppernu.16531250000000003. Both are required for the
next complete paired inner stage; original list evaluates lower then upper,
but independent source precomputation can acquire either first without changing
AO when both are subsequently supplied. Neither missing K can be predicted;
either could move bestnu and change future P1/P2 targets.

Recommended first dedicated source: upper(.16531250000000003,5.5), because its
Phase2A AC1/zero-gap/fulltree/sleep receipt is stronger than the older lower
probe's unrecorded power history. This is an observability-risk choice, NOT
evidence it is cheaper or more beneficial. Lower(.16375,5.5) comes next only if
still the required partner, with its own explicit authorization. Lower60min
attempt used3469.96875JobCPU/3595.75wall; upper3516.90625/3595wall. Both need
more than their observed unsuccessful windows OR a resolution of unknown late
stage behavior. No final AP precision progress survived; completion cannot be
predicted and active CPU does not exclude an expensive numerical loop.

Conditional recommendation: dedicated120min ceiling for ONE previously timed-out
source +>=10min processing envelope (130min total), only after approved valid
full-duration observations and stable safety gates. Evidence of near-full CPU
and nearby successful sources makes a bounded longer investigation reasonable,
not a guarantee. If both sources are separately approved together, suggest
250min total=2x120min+10min, never reuse old3h budget. No launch in this task.
The existing instrumented probe_worker passes per-probe-timeout-8 to inner AP;
if choosing an uninstrumented source path, its inner3600s cap would still abort.
Any observer correction remains a separately approved operational change.

If it times out again: save true full-duration stage/progress/resources/CPU/
power, kill wholeJob, restoreSleep, retain failed receipt, no automatic retry,
no invented C/w. Decide whether more time is justified by measured completion
milestones. If stalled/unsafe/provenance failure, stop and diagnose, not extend.

No alternate source pair can substitute a REQUIRED original midpoint merely
because it is faster. Original AO may legitimately request another slice if a
measured optimum moves; follow that logic, not a surrogate. Completed-source
cache avoids duplicate AP; no equivalent partial-resume path currently exists.
If bestnu stays.165 and both partners have no better K, next P2 bracket becomes
[.16375,.16531250000000003] and next partners are(.164375,5.5) and
(.16515625000000003,5.5). These are conditional arithmetic, uncomputed and
NOT preapproved. Safe source completion still does not certify final optimum.
""",
'ao_optimum_completion_criteria.md': """
# AO numerical-optimum completion criteria: unchanged implementation

Finite current facts:147 compatible MB sources/3822 stored objectives,26/26 AO
catalog agreement,0 closed final directions. Reference best(.165,5.5),
K=.07798099387393764;22km(.165,5.475),K=.07661740491526092.

## Labels and evidence

| Label | Necessary evidence | Current status |
|---|---|---|
| FINITE_CATALOG_MAXIMUM | Independent ranking of valid hash-matched stored rows | Verified26/26 |
| COORDINATE_SEARCH_INCOMPLETE | Missing values/open boundary/refinement cap/failure | Current P1 and P2 |
| COORDINATE_WISE_NUMERICAL_OPTIMUM | Both original searches complete at the SAME actual selected pair; two-sided radius<=1e-6, no missing/numerical failures; error sufficient | Not established |
| AO_NUMERICALLY_CONVERGED | Original real updates, absDeltaK<=1e-8, both complete searches, no earlier unresolved or monotonic warning | Not established |
| GLOBAL_OPTIMUM_NOT_CERTIFIED | No proof remote extrema/unbounded boundaries excluded | Remains true even after local closure |

Original settings unchanged:epsilon1e-8,param1e-6,outer6,inner4,boundary3.
Reference P1 [5.4875,5.5125] radius.0125, P2 [.1625,.16562500000000002]
radius.0025. If incumbent remains unchanged and exact paired midpoints halve
both gaps,14 and12 reductions respectively are needed for radius<=1e-6.
After one completed pair13/11 further stages remain; these are conditional,
not lower bounds for every moving-incumbent landscape. Four successful stages
leave radii.00078125 and.00015625. Four-step cap cannot close these current
brackets in one call. Tolerance checked only on entry: crossing tolerance on
fourth pair still returns REFINE_LIMIT/INNER_SEARCH_FAILURE; only after<=3
reductions can current4-stage call observe the tolerance on a later entry.

Unchanged-best conditional P1 after BOTH current missing partners measured:
bracket[5.49375,5.50625], radius.00625; next VA5.496875 and5.503125.
P2 conditional bracket[.16375,.16531250000000003], radius.00125;
nextnu.164375/.16515625000000003. No candidate K inferred. If incumbent moves,
actual nearest measured neighbors and new fixed parameter determine requests.
Measuring A alone can narrow one side or change incumbent; because missing
partner stops the paired stage, it does not complete P1. Existing AO still
returns a finite best and follows genuine next P2 at newly selectedVA.

Six outer calls must not be assumed to provide24 useful refinements: small
DeltaK with incomplete searches stops as catalog stagnation/boundary unresolved;
run's unresolved_inner latch does not clear. Prior cache additions can narrow
initial brackets on a new approved original invocation, without changing algorithm,
but within one trajectory earlier unresolved evidence cannot be relabeled closed.
One authorized strategy is adaptive original-request cache prepopulation before
the final genuine AO replay, until initial slices sufficiently narrow. A prospective
cap increase or revised reset/stopping policy would be a separate algorithm/settings
decision and is NOT implemented/recommended as silently necessary here.

P2 reference's current selected best is interior among measured nu points, so
its immediate local boundary_status is INTERIOR, NOT BOUNDARY_NOT_CLOSED;
missing midpoint refinement is the active local block. Remote nu->0+,nu->infty,
VA->0+,VA->infty directions are NOT globally closed by that local bracket.
Implemented strictnu>0 does not include mathematicalnu=0. Compatible stored
Uniform comparison does not optimize/close the continuousnu=0 boundary.
At22km nu slice singleton remains lowerouter.0825 missing/opposite.33 unchecked.
nu0=.8 run is still boundary-blocked(.4,3.0), lastmissing(.4,1.5)/(.2,3.0);
its lower value is not proof of a distinct continuous basin. Four other starts
agree at each priority distance. Consistent starts are useful, not a requirement
that every nonconvex trajectory reach one point or a global proof.

Required accuracy: candidate-specific full-support AP convergence/provenance,
adequate GH8 MI discretization error evidence without changing the current rule,
entropy/roundoff/covariance checks and propagated totalK error. Four stored
bit-exact metric repeats establish determinism only. Near ties7.834476867e-8
and1.733217454e-7 and epsilon1e-8 need appropriate error control; current
ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED cannot support all displayed optimal
digits. No such new accuracy calculation authorized here. Final manuscript may
present finite best observed results with limitations, not convergence certificate.
"""
}


if __name__ == '__main__':
    main()
