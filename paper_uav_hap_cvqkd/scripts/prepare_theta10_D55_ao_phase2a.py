"""Phase2A preparation and short native safety tests; AP requires NEW approval."""
from contextlib import ExitStack
import csv
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import audit_theta10_D55_ao_numerical_optimum as audit
from scripts import continue_theta10_D55_mb_batch3_after_ac as native
from scripts.exact_cache_provenance import verify_source_payload, source_settings
from src.cvqkd import gram_moments

BASE, SCIENCE = audit.OUT, audit.BASE
OUT = BASE / 'phase_2A'
PAIRS = ((.165,5.49375), (.165,5.5125), (.16531250000000003,5.5))
HARD_PAIR = (.16375,5.5)
ao, io, source, sweep, safe = audit.ao, audit.io, audit.source, audit.sweep, native.safe


def empty(name, fields):
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        csv.DictWriter(stream,fieldnames=fields).writeheader()


def worker_inventory():
    command = "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--probe|full_support_c4_worker\\.py|run_theta10_D55_mb_.*\\.py|continue_theta10_D55_mb_.*\\.py|resume_theta10_D55_mb_.*\\.py'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
    result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    return json.loads(result.stdout) if result.stdout.strip() else []


def main():
    if OUT.exists():
        raise SystemExit('Phase2A preparation exists; refuse overwriting or starting AP')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    torch.set_num_threads(1)
    config=source.unconstrained_config()
    assert PAIRS == ((.165,(5.4875+5.5)/2),(.165,(5.5+5.525)/2),((.165+.16562500000000002)/2,5.5))
    assert HARD_PAIR not in PAIRS
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES,ao.MAX_BOUNDARY_EXPANSIONS)==(1e-8,1e-6,6,4,3)
    manifest=audit.read(BASE/'protected_input_manifest.json')
    for name,digest in manifest.items():
        assert io.digest(ROOT/name)==digest,name
    manifest.update(io.raw_snapshot(p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts))
    manifest.update(io.raw_snapshot([Path(__file__),ROOT/'tests/test_ao_phase2a_preparation.py']))
    # The old scientific checkpoint and all source banks already belong to this manifest.
    OUT.mkdir()
    io.save_json(OUT/'protected_input_manifest.json',manifest)
    worktree=subprocess.run(['git','diff'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (OUT/'preexisting_worktree.diff').write_text(worktree.stdout,encoding='utf-8')
    checkpoint=audit.read(SCIENCE/'objective_checkpoint.json')
    history=io.read_csv(BASE/'ao_multistart_history.csv')
    diagnostics=io.read_csv(BASE/'coordinate_search_diagnostics.csv')
    priorities=io.read_csv(BASE/'missing_source_priority.csv')
    table=io.read_csv(BASE/'optimized_skr_26_distances.csv')
    assert (len(history),len(diagnostics),len(priorities),len(table))==(1713,52,55,26)
    runs=audit.read(SCIENCE/'cache_only_runs.json')
    searches=audit.read(SCIENCE/'cache_only_searches.json')
    aligned,finals=audit.align_searches(runs,searches)
    selected=[]
    with ExitStack() as guard:
        for obj, method in ((ao.ExactMBEvaluator,'source_moments'),(gram_moments,'_fallback'),
                            (ao,'evaluate_candidate'),(sweep,'make_channel'),(ao,'adaptive_maximize_1d')):
            guard.enter_context(patch.object(obj,method,audit.forbidden))
        bank=source.load_source_payloads(config,audit.baseline.DIRS)
        mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
        assert len(mb)==146
        caches=[]
        for path in (ROOT/'results').rglob('exact_source_cache/*.json'):
            payload=audit.read(path)
            verification=verify_source_payload(payload,source_settings(config))
            caches.append({'path':str(path.relative_to(ROOT)),'nu_hex':payload['nu_mb_raw_hex'],
                'va_hex':payload['V_A_hex'],'cache_key':payload['cache_key'],'status':verification['status']})
        io.save_json(OUT/'all_cache_identity_check.json',caches)
        for distance in sweep.DISTANCES_KM:
            stored=checkpoint[str(distance)]
            objective=ao.ExactObjective(config,stored['identity']['identity']['channel'],OUT,allow_new_source=False,
                source_cache_dirs=audit.baseline.DIRS)
            assert objective.restore_objective_rows(stored['rows'],stored['identity'])==146
            best=max(objective.rows.values(),key=lambda r:r['SKR'])
            old=next(r for r in table if float(r['L_km'])==distance)
            assert old['source_cache_key']==best['source_cache_key'] and float(old['K'])==best['SKR']
            assert objective.requested_calls==objective.unique_exact_evaluations==0
        for index,(nu,va) in enumerate(PAIRS,1):
            key=audit.pair(nu,va)
            old=next(r for r in priorities if audit.pair(r['nu_raw'],r['V_A'])==key)
            assert source.candidate_from_payload(config,bank,'MB',nu,va) is None
            assert not any((c['nu_hex'],c['va_hex'])==key for c in caches)
            identity=objective.evaluator._source_identity(source.make_ensemble(config,'MB',nu,va),nu,va)
            assert source.json_hash(identity)==old['source_cache_key'] and identity['ensemble_hash']==old['ensemble_hash']
            deps=json.loads(old['dependencies'])
            required=[d for d in deps if d['L_km']==audit.REF and d['role']=='SELECTED_FINAL']
            assert required and not json.loads(old['previous_attempts'])
            selected.append({'probe_order':index,'nu_raw':nu,'V_A':va,'nu_raw_hex':key[0],'V_A_hex':key[1],
                'source_cache_key':old['source_cache_key'],'raw_current_cache_key':old['source_cache_key'],
                'ensemble_hash':identity['ensemble_hash'],'coordinate':'P1' if index<3 else 'P2',
                'required_reference_searches':json.dumps(required),'all_affected_searches':old['dependencies'],
                'available_in_compatible_caches':False,'status':'NOT_RUN_AWAITING_EXPLICIT_NEW_AUTHORIZATION'})
    io.write_csv(OUT/'selected_exact_probes.csv',selected)
    io.write_csv(OUT/'execution_ledger.csv',[{**p,'C':'','w':'','wall_seconds':'','CPU_seconds':'','termination_reason':'NOT_STARTED'} for p in selected])
    empty('new_exact_source_moments.csv',['nu_raw','V_A','nu_raw_hex','V_A_hex','source_cache_key','C','w','status','wall_seconds','CPU_seconds','provenance'])
    empty('new_exact_skr_26_distances.csv',['L_km','nu_raw','V_A','I_AB','beta_I_AB','chi_BE','K','source_cache_key','status'])
    io.write_csv(OUT/'expanded_source_catalog.csv',[{'nu_raw':float.fromhex(p['nu_mb_raw_hex']),'V_A':float.fromhex(p['V_A_hex']),
        'C':p['C'],'w':p['w'],'source_cache_key':p['cache_key'],'ensemble_hash':p['ensemble_hash'],
        'snapshot':'VERIFIED_BASELINE_146_NOT_EXPANDED'} for p in mb])
    io.write_csv(OUT/'old_vs_new_skr_optimum.csv',[{'L_km':r['L_km'],'old_nu':r['nu_raw'],'old_V_A':r['V_A'],'old_K':r['K'],
        'new_nu':'','new_V_A':'','new_K':'','delta_K':'','AO_match':'','status':'NOT_RUN_STAGE2_PENDING'} for r in table])
    io.write_csv(OUT/'baseline_optimization_table_26_distances.csv',[{**r,'snapshot':'BASELINE_NOT_NEW_OPTIMIZATION'} for r in table])
    for var,label,fixed in (('V_A','P1',.165),('nu_raw','P2',5.5)):
        rows=[r for r in checkpoint[str(audit.REF)]['rows'] if float(r['nu_raw' if var=='V_A' else 'V_A']).hex()==fixed.hex()]
        io.write_csv(OUT/f'reference_{label}_coordinate_trace.csv',[{**r,'snapshot':'BASELINE_EXACT_SLICE_NO_NEW_PROBE'} for r in sorted(rows,key=lambda r:r[var])])
    io.write_csv(OUT/'coordinate_completion_status.csv',[{**r,'snapshot':'BASELINE_NO_COORDINATE_RECHECK','Phase2A_completed':'NOT_RUN'} for r in diagnostics])
    io.write_csv(OUT/'ao_multistart_recheck.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],'start_nu':r['start_nu'],
        'initial_V_A':r['start_V_A'],'final_nu':r['final']['nu_raw'],'final_V_A':r['final']['V_A'],'K':r['final']['SKR'],
        'iterations':len(r['iterations']),'baseline_status':r['status'],'recheck_status':'NOT_RUN_STAGE2_PENDING'} for r in runs])
    hard=next(r for r in priorities if audit.pair(r['nu_raw'],r['V_A'])==audit.pair(*HARD_PAIR))
    io.save_json(OUT/'phase_2B_previous_timeout_evidence.json',json.loads(hard['previous_attempts']))
    io.save_json(OUT/'baseline_nu08_trajectories.json',[{'run':r,'searches':[s for s in aligned if s['L_km']==r['L_km'] and s['start_id']==r['start_id'] and s['role']=='ITERATION']}
        for r in runs if r['L_km'] in (audit.REF,22.) and r['start_id']=='nu_0.8'])
    uniforms=[r for r in io.read_csv(BASE/'three_scheme_comparison.csv') if r['scheme']==sweep.UNIFORM_SCHEME]
    io.write_csv(OUT/'nu_zero_boundary_comparison.csv',[{'L_km':r['L_km'],'Uniform_V_A':r['V_A'],'Uniform_K':r['K'],
        'MB_nu':next(v['nu_raw'] for v in table if v['L_km']==r['L_km']),
        'MB_K':next(v['K'] for v in table if v['L_km']==r['L_km']),
        'scope':'STORED_COMPATIBLE_UNIFORM_CANDIDATE_NOT_CONTINUOUS_NU_ZERO_CLOSURE'} for r in uniforms])
    workers=worker_inventory()
    power=safe.WindowsPower().read()
    preflight={'status':'BLOCKED_BY_ENVIRONMENT','AC':power,'workers_before':workers,'AP_started':False,
        'sleep_request_held_after_preflight':False,'dummy_jobs':[],'scope':'SHORT_PREFLIGHT_NOT_FULL_DURATION_GUARANTEE'}
    if safe.safe_power(power) and not workers:
        io.save_json(OUT/'power_and_supervisor_preflight.json',preflight)
        try:
            # Only the preflight helper output directory changes; old supervisor/math are untouched.
            with patch.object(native,'OUT',OUT):
                preflight['dummy_jobs']=native.native_wall_preflight()
            lease=safe.AwakeOnAC()
            try:
                with lease:
                    raise ValueError('Intentional native lease-cleanup preflight')
            except ValueError:
                pass
            assert lease.receipt['released_verified']
            preflight['exception_cleanup']=lease.receipt
            preflight['status']='CURRENTLY_VERIFIED_PASS'
        except Exception as error:
            preflight['status']='FAILED';preflight['error']=str(error)
    preflight['workers_after']=worker_inventory()
    assert not preflight['workers_after'],'Scientific workers present; fail closed'
    preflight['AC_after']=safe.WindowsPower().read()
    if not safe.safe_power(preflight['AC_after']):
        preflight['status']='BLOCKED_BY_ENVIRONMENT_AC_REQUIRED'
    io.save_json(OUT/'power_and_supervisor_preflight.json',preflight)
    checks=[]
    for pattern in ('test_ao_phase2a_preparation.py','test_ao_numerical_optimum_audit.py','test_windows_sleep_safe_supervision.py',
                    'test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        checks.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
    io.save_json(OUT/'regression_tests.json',checks)
    assert all(c['returncode']==0 for c in checks)
    for name,digest in manifest.items():
        assert io.digest(ROOT/name)==digest,name
    io.save_json(OUT/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in manifest})
    done=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    report={'status':'AWAITING_EXPLICIT_NEW_PHASE2A_AUTHORIZATION' if preflight['status']=='CURRENTLY_VERIFIED_PASS' else 'BLOCKED_BY_ENVIRONMENT_PREFLIGHT',
        'stage1_preparation':'CURRENTLY_VERIFIED_PASS','native_preflight':preflight,'stage2':'NOT_RUN',
        'new_budget_approved':False,'proposed_total_wall_seconds':10800,'proposed_probe_wall_seconds':3600,
        'max_probes':3,'sequential_only':True,'proposed_postprocessing_cleanup_reserve_seconds':480,
        'budget_scope':'FUTURE_EXECUTION_INCLUDING_POSTPROCESSING_AND_CLEANUP_NO_FRESH_3H_PER_PROBE',
        'probe_pairs':PAIRS,'excluded_phase2B_pair':HARD_PAIR,'sources_generated':0,'new_objectives':0,'AO_rechecked':False,
        'MB_catalog_count':146,'validated_saved_objectives':3796,'baseline_AO_catalog_matches':26,'baseline_closed_directions':0,
        'compatible_cache_files_checked':len(caches),'science_and_old_artifacts_unchanged':True,'protected_files_unchanged':len(manifest),
        'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','baseline_checkpoint':str((SCIENCE/'objective_checkpoint.json').relative_to(ROOT)),
        'settings':{'epsilon_opt':1e-8,'parameter_tolerance':1e-6,'max_outer_iterations':6,'max_inner_refinement_steps':4},
        'tests':'CURRENTLY_VERIFIED_PASS','git_diff_check':'CURRENTLY_VERIFIED_PASS','producer_sha256':io.digest(__file__),
        'frozen_spec_sha256':io.digest(ROOT/'docs/FINAL_MODEL_SPEC.md'),'frozen_spec_hash_blocker':'PREEXISTING_UNCHANGED',
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','wall_seconds':time.monotonic()-started,'controller_CPU_seconds':time.process_time()-cpu}
    io.save_json(OUT/'phase_2A_report.json',report)
    (OUT/'numerical_accuracy_status.md').write_text('# Numerical accuracy\n\nORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED. No new AP or objective evaluation in preparation.\n'
        'Existing source/precision/quadrature/Holevo checks and repeatability evidence are in ../numerical_accuracy_assessment.md.\n'
        'Candidate-specific AP per-precision residuals and total objective error bounds are not retained. No numerical/global convergence claim.\n',encoding='utf-8')
    (OUT/'phase_2B_hard_probe_plan.md').write_text('# Phase2B hard-source plan (provisional)\n\n'
        '(.16375,5.5) remains a current reference P2 lower-midpoint dependency; excluded from Phase2A.\n'
        'Prior timeout:3600s approved,3595.75s measured source wall,3469.96875s JobCPU; no valid C,w. See timeout evidence JSON.\n'
        'After Phase2A, check actual new selected pair and original P2 requests before recommending a retry.\n'
        'No post-Phase2A necessity decision exists yet. Runtime has no demonstrated completion bound.\n'
        'If still required, a separately approved120-minute probe ceiling plus explicit postprocessing/cleanup allowance is a planning option, not a completion prediction.\n'
        'Preserve precision/method. Require new explicit scope/budget, safeAC/Sleep/Job, sequential execution; no automatic retry.\n',encoding='utf-8')
    lines=['# Phase2A — preparation only','',report['status'],'',
        'Stage1 baseline/source checks complete. Stage2 AP/SKR/AO NOT_RUN pending new explicit authorization.',
        f"Native preflight={preflight['status']}; AC before/after={power['ac']}/{preflight['AC_after']['ac']}; worker cleanup verified.",
        'Temporary Sleep prevention tested/restored, no permanent power-plan change; reacquire/recheck before every real probe.',
        'Original Job wall deadline and live-descendant cleanup tested with dummy jobs only. No scientific worker launched.',
        f"146 compatible MB sources/3796 saved objectives/26 finite maxima verified; {len(manifest)} protected hashes unchanged.",
        '','## Proposed fresh budget','',
        '10800s total including postprocessing/cleanup; <=3600s/source; at most3 serial probes. Proposed480s final-processing reserve.',
        'Each allowed probe gets min(3600s,remaining_total-reserve), potentially less than60min. No promise all3 finish.',
        'No timeout/AC-abort retry; no Phase2B; expired Batch3 approval never reused.',
        '','## Exactly selected missing sources','', '|Order|nu_raw|VA|coordinate|raw source key|','|---|---|---|---|---|']
    lines += [f"|{p['probe_order']}|{p['nu_raw']}|{p['V_A']}|{p['coordinate']}|{p['source_cache_key']}|" for p in selected]
    lines += ['', 'All178 cache files checked; selected binary64/ensemble/raw keys equal original missing dependency identities.',
        'No changes to physical/source/security/MI/quadrature/precision/AO/stopping settings.',
        '','## Baseline and limitations','',
        'Reference(.165,5.5),K=.07798099387393764;22km(.165,5.475),K=.07661740491526092, unchanged saved values.',
        'P1 bracket[5.4875,5.525], width.0375; P2[.1625,.16562500000000002], width.003125.0 fully closed directions.',
        'Pairs1/2 could advance P1 coverage; pair3 could refine uppernu shoulder. Actual changes depend on measured K.',
        'Missing lowernu.16375 prevents asserting P2 complete. Stage2 original searches must report actual next dependencies.',
        'All129 baseline starts retained in ao_multistart_recheck.csv; NOT a fresh recheck.',
        'Nu0=.8 actual trajectories/searches saved. They terminate UNRESOLVED_BOUNDARY at(.4,3.0),',
        'not demonstrated separate continuous attraction basin: source/boundary blockers and early epsilon stopping remain.',
        'Uniform storednu=0 comparisons share validated context but do not close the continuous Uniform/nu boundary.',
        '','## Execution-dependent questions (not fabricated)','',
        '0 probes started/completed; no new C,w/K, catalog146. No post-expansion AO/rank/parameter/improvement result exists.',
        'reference_P1/P2 traces and coordinate_completion_status are labeled BEFORE_EXECUTION baseline snapshots.',
        'new_exact_source_moments/new_exact_skr CSVs contain headers only; old_vs_new new fields are blank/NOT_RUN.',
        'Phase2A final15 answers and updated figures/TableA require Stage2. Existing figures retained, not relabeled as new.',
        'Numerical reliability remains ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED. Finite-catalog maximum only.',
        'Source/precision/quadrature error evidence, coordinate closure, multistart/boundary coverage andnu=0 scope still required.',
        '','Regression tests/current provenance/diff checks PASS. Pre-existing frozen-spec historical hash mismatch unchanged;',
        'NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Stop and request fresh approval for the specified Phase2A budget only.']
    (OUT/'phase_2A_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
