"""Approved three-source Phase2A; original AP/Job/evaluator/AO, no extra probes."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import prepare_theta10_D55_ao_phase2a as prep

OUT, BASE=prep.OUT,prep.SCIENCE
ao,io,source,sweep,safe=prep.ao,prep.io,prep.source,prep.sweep,prep.safe
supervisor=prep.native.supervisor
DIRS=(*prep.audit.baseline.DIRS,OUT/'exact_source_cache')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def budget_limit(deadline,now):
    return min(3600.,deadline-now-480.)


def points():
    rows=io.read_csv(OUT/'selected_exact_probes.csv')
    assert tuple((float(r['nu_raw']),float(r['V_A'])) for r in rows)==prep.PAIRS
    assert prep.HARD_PAIR not in prep.PAIRS
    for r in rows:
        assert (r['nu_raw_hex'],r['V_A_hex'])==prep.audit.pair(r['nu_raw'],r['V_A'])
        assert r['raw_current_cache_key']==r['source_cache_key']
    return rows


def process(with_ao=False):
    """Only new valid sources receive fresh SKR; AO itself is the original callable."""
    import torch
    torch.set_num_threads(1)
    supervisor.verify_protected(OUT)
    config=source.unconstrained_config()
    bank=source.load_source_payloads(config,DIRS)
    mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    assert 146<=len(mb)<=149
    original=read(BASE/'objective_checkpoint.json')
    saved=read(OUT/'objective_checkpoint.json') if (OUT/'objective_checkpoint.json').exists() else {}
    old={float(r['L_km']):r for r in io.read_csv(prep.BASE/'optimized_skr_26_distances.csv')}
    selected=points()
    allowed={prep.audit.pair(r['nu_raw'],r['V_A']) for r in selected}
    original_pairs={prep.audit.pair(r['nu_raw'],r['V_A']) for r in original['20.0']['rows']}
    assert {prep.audit.pair(float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])) for p in mb}-original_pairs<=allowed
    io.write_csv(OUT/'expanded_source_catalog.csv',[{'nu_raw':float.fromhex(p['nu_mb_raw_hex']),'V_A':float.fromhex(p['V_A_hex']),
        'C':p['C'],'w':p['w'],'source_cache_key':p['cache_key'],'ensemble_hash':p['ensemble_hash'],'provenance':p['_provenance']['status']} for p in mb])
    comparisons,newrows,records,runs_all,searches,objects,maxima=[],[],[],[],[],{},{}
    original_search=ao.adaptive_maximize_1d
    def recording_search(**kw):
        result=original_search(**kw)
        searches.append({'L_km':kw['objective'].channel['distance_km'],**result})
        return result
    warm=None
    with patch.object(ao.ExactMBEvaluator,'source_moments',prep.audit.forbidden), \
         patch.object(prep.gram_moments,'_fallback',prep.audit.forbidden), \
         patch.object(ao,'adaptive_maximize_1d',recording_search),patch.object(sweep,'adaptive_maximize_1d',recording_search):
        for distance in sweep.DISTANCES_KM:
            obj=ao.ExactObjective(config,sweep.make_channel(config,distance),OUT,allow_new_source=False,source_cache_dirs=DIRS)
            cached=original[str(distance)]
            assert obj.restore_objective_rows(cached['rows'],cached['identity'])==146
            if str(distance) in saved:
                obj.restore_objective_rows(saved[str(distance)]['rows'],saved[str(distance)]['identity'])
            for p in mb:
                n,v=float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])
                obj.register_catalog(n,v);obj(n,v)
            ranked=sorted(obj.rows.values(),key=lambda r:r['SKR'],reverse=True)
            assert len(ranked)==len(mb)
            best,second=ranked[:2];maxima[distance]=best;objects[distance]=obj
            for p in selected:
                if source.candidate_from_payload(config,bank,'MB',float(p['nu_raw']),float(p['V_A'])):
                    newrows.append(obj(float(p['nu_raw']),float(p['V_A'])))
            comparisons.append({'L_km':distance,'old_nu':old[distance]['nu_raw'],'old_V_A':old[distance]['V_A'],'old_K':old[distance]['K'],
                'new_nu':best['nu_raw'],'new_V_A':best['V_A'],'new_K':best['SKR'],'delta_K':best['SKR']-float(old[distance]['K']),
                'I_AB':best['I_AB'],'beta_I_AB':best['beta_I_AB'],'chi_BE':best['chi_BE'],'runner_up_K':second['SKR'],
                'top_two_gap':best['SKR']-second['SKR'],'MB_count':len(mb),'AO_match':'NOT_RUN' if not with_ao else '',
                'claim':'FINITE_CATALOG_NUMERIC_ORDER_NOT_CONTINUOUS_OPTIMUM'})
            saved[str(distance)]={'identity':obj.objective_identity,'rows':list(obj.rows.values())}
            io.save_json(OUT/'objective_checkpoint.json',saved)
            io.write_csv(OUT/'new_exact_skr_26_distances.csv',newrows)
            io.write_csv(OUT/'old_vs_new_skr_optimum.csv',comparisons)
            if with_ao:
                starts=[(f'nu_{n:g}',n,None) for n in sweep.BASE_STARTS]
                if warm:
                    starts.append(('warm_previous_distance',*warm))
                runs=[sweep.run_single_distance_ao(distance_km=distance,start_id=sid,start_nu=n,start_va=v,objective=obj,
                    max_iterations=ao.MAX_AO_ITERATIONS) for sid,n,v in starts]
                chosen=max((r for r in runs if r['final']),key=lambda r:r['final']['SKR'])
                final=chosen['final'];warm=(float(final['nu_raw']),float(final['V_A']))
                checks=[recording_search(variable=v,fixed=f,values=obj.catalog_values(v,f),objective=obj)
                    for v,f in (('V_A',warm[0]),('nu_raw',warm[1]))]
                complete=all(ao.coordinate_search_complete(s) for s in checks)
                status=chosen['status']
                if status=='CONVERGED_NUMERICALLY' and (not complete or any(s['best_K']>final['SKR']+ao.K_TOLERANCE for s in checks)):
                    status='STAGNATED_IN_EXACT_CATALOG'
                records.append({'L_km':distance,'nu_raw':warm[0],'V_A':warm[1],'I_AB':final['I_AB'],'beta_I_AB':final['beta_I_AB'],
                    'chi_BE':final['chi_BE'],'K':final['SKR'],'AO_validation_status':status,'selected_start':chosen['start_id'],
                    'catalog_K':best['SKR'],'matches_catalog_maximum':final['SKR']==best['SKR'],'coordinate_complete':complete,
                    'claim':'FINITE_CATALOG_BEST_OBSERVED_ONLY','source_cache_key':final['source_cache_key']})
                comparisons[-1]['AO_match']=final['SKR']==best['SKR']
                runs_all.extend({'L_km':distance,**r} for r in runs)
                io.save_json(OUT/'cache_only_runs.json',runs_all);io.save_json(OUT/'cache_only_searches.json',searches)
                io.write_csv(OUT/'optimized_skr_26_distances.csv',records)
            print(f'Phase2A L={distance}: MB={len(mb)}, K={best["SKR"]}, AO={with_ao}',flush=True)
    io.write_csv(OUT/'old_vs_new_skr_optimum.csv',comparisons)
    summary={'MB_count':len(mb),'new_objective_rows':len(newrows),'improved_distances':[r['L_km'] for r in comparisons if r['delta_K']>0],
        'reference':next(r for r in comparisons if r['L_km']==prep.audit.REF),'at22km':next(r for r in comparisons if r['L_km']==22.),
        'AO_rechecked':with_ao,'AO_catalog_matches':sum(r['matches_catalog_maximum'] for r in records),
        'closed_selected_directions':0,'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'}
    if with_ao:
        aligned,finals=prep.audit.align_searches(runs_all,searches)
        diagnostics=[prep.audit.diagnostic(s,saved[str(d)]['rows']) for d,ss in finals.items() for s in ss]
        previous=read(BASE/'cache_only_searches.json')
        progress=[]
        for d,ss in finals.items():
            oldchecks=[s for s in previous if s['L_km']==d][-2:]
            for before,after in zip(oldchecks,ss):
                recovered=[]
                for e in before['source_missing']:
                    n,v=(before['fixed'],e['value']) if before['variable']=='V_A' else (e['value'],before['fixed'])
                    if source.candidate_from_payload(config,bank,'MB',n,v): recovered.append(e['value'])
                progress.append({'L_km':d,'coordinate':after['variable'],'old_fixed':before['fixed'],'new_fixed':after['fixed'],
                    'same_slice':before['fixed']==after['fixed'],'old_bracket':json.dumps(before['bracket']),
                    'new_bracket':json.dumps(after['bracket']),'old_status':before['status'],'new_status':after['status'],
                    'old_refinement_stages':before['refinement_stages'],'new_refinement_stages':after['refinement_stages'],
                    'previous_missing_now_measured':json.dumps(recovered),'previous_paired_step_now_covered':
                        len(recovered)==2 and len(before['source_missing'])==2 and before['refinement_status']=='SOURCE_MISSING_REFINEMENT',
                    'newly_closed_same_slice':before['fixed']==after['fixed'] and not ao.coordinate_search_complete(before) and ao.coordinate_search_complete(after),
                    'missing_next':json.dumps(after['source_missing'])})
        io.write_csv(OUT/'coordinate_completion_status.csv',diagnostics)
        io.write_csv(OUT/'coordinate_refinement_progress.csv',progress)
        io.save_json(OUT/'aligned_search_history.json',aligned)
        io.write_csv(OUT/'ao_multistart_recheck.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],'start_nu':r['start_nu'],
            'initial_V_A':r['start_V_A'],'final_nu':r['final']['nu_raw'],'final_V_A':r['final']['V_A'],'K':r['final']['SKR'],
            'iterations':len(r['iterations']),'status':r['status'],'missing_source_events':sum(len(json.loads(it['numerical_warning']).get('V_A_failures',[]))+len(json.loads(it['numerical_warning']).get('nu_failures',[])) for it in r['iterations']),
            'matches_catalog':r['final']['SKR']==maxima[r['L_km']]['SKR']} for r in runs_all])
        io.write_csv(OUT/'ao_iteration_history.csv',[it for r in runs_all for it in r['iterations']])
        io.save_json(OUT/'nu08_trajectories_after_phase2A.json',[r for r in runs_all if r['start_id']=='nu_0.8' and r['L_km'] in (prep.audit.REF,22.)])
        missing={}
        for s in aligned:
            for e in s['source_missing']:
                n,v=(s['fixed'],e['value']) if s['variable']=='V_A' else (e['value'],s['fixed'])
                k=prep.audit.pair(n,v)
                row=missing.setdefault(k,{'nu_raw':n,'V_A':v,'nu_raw_hex':k[0],'V_A_hex':k[1],'requests':[]})
                row['requests'].append({'L_km':s['L_km'],'variable':s['variable'],'start_id':s['start_id'],'iteration':s['iteration'],'role':s['role']})
        io.write_csv(OUT/'remaining_missing_exact_pairs.csv',[{**r,'requests':json.dumps(r['requests'])} for r in missing.values()])
        # Targeted baseline slices are separate from final-pair postchecks if the winner moves.
        obj=objects[prep.audit.REF]
        targeted=[]
        for variable,fixed,label in (('V_A',.165,'P1'),('nu_raw',5.5,'P2')):
            s=original_search(variable=variable,fixed=fixed,values=obj.catalog_values(variable,fixed),objective=obj)
            targeted.append({'L_km':prep.audit.REF,'label':label,**s})
            exact=sorted((r for r in obj.rows.values() if float(r['nu_raw' if variable=='V_A' else 'V_A']).hex()==fixed.hex()),key=lambda r:r[variable])
            io.write_csv(OUT/f'reference_{label}_coordinate_trace.csv',[{**r,'K':r['SKR'],'slice_fixed':fixed,'post_search_status':s['status']} for r in exact])
        io.save_json(OUT/'reference_targeted_coordinate_searches.json',targeted)
        io.write_csv(OUT/'reference_targeted_coordinate_diagnostics.csv',[prep.audit.diagnostic(s,saved[str(prep.audit.REF)]['rows']) for s in targeted])
        # Independent saved-matrix restoration/ranking and original-evaluator repeatability.
        independently_verified,repeats=[],[]
        with patch.object(ao.ExactMBEvaluator,'source_moments',prep.audit.forbidden):
            for d in sweep.DISTANCES_KM:
                entry=saved[str(d)]
                verify=ao.ExactObjective(config,entry['identity']['identity']['channel'],OUT,allow_new_source=False,source_cache_dirs=DIRS)
                verify.restore_objective_rows(entry['rows'],entry['identity'])
                assert len(verify.rows)==len(mb)
                assert {prep.audit.pair(r['nu_raw'],r['V_A']) for r in verify.rows.values()}=={prep.audit.pair(float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])) for p in mb}
                best=max(verify.rows.values(),key=lambda r:r['SKR'])
                actual=next(r for r in records if r['L_km']==d)
                independently_verified.append({'L_km':d,'catalog_K':best['SKR'],'AO_K':actual['K'],'AO_matches_catalog':best['SKR']==actual['K'],
                    'nu_raw':best['nu_raw'],'V_A':best['V_A'],'objective_identity_sha256':verify.context_hash,'rows':len(verify.rows)})
                if d in (20.,prep.audit.REF,22.,40.):
                    for r in (r for r in newrows if r['L_km']==d):
                        c=source.candidate_from_payload(config,bank,'MB',float(r['nu_raw']),float(r['V_A']))
                        repeat=ao.evaluate_candidate(c,verify.channel,config)
                        repeats.append({'L_km':d,'nu_raw':r['nu_raw'],'V_A':r['V_A'],'source_cache_key':r['source_cache_key'],
                            **{'delta_'+k:float(repeat[k])-float(r[k]) for k in ('I_AB','beta_I_AB','chi_BE','SKR')}})
        io.write_csv(OUT/'independent_catalog_verification.csv',independently_verified)
        io.write_csv(OUT/'original_evaluator_reproducibility.csv',repeats)
        assert all(r['delta_'+k]==0 for r in repeats for k in ('I_AB','beta_I_AB','chi_BE','SKR'))
        comparison=[r for r in io.read_csv(prep.BASE/'three_scheme_comparison.csv') if r['scheme'] in (sweep.UNIFORM_SCHEME,sweep.FIXED_MB_SCHEME)]
        comparison += [{'scheme':'AO MB: finite-catalog best',**r} for r in records]
        io.write_csv(OUT/'three_scheme_comparison.csv',comparison)
        with patch.object(prep.audit,'OUT',OUT):
            figures=prep.audit.make_plots(runs_all,maxima,saved,comparison)
        summary.update(AO_catalog_matches=sum(r['AO_matches_catalog'] for r in independently_verified),
            closed_selected_directions=sum(ao.coordinate_search_complete(s) for ss in finals.values() for s in ss),
            coordinate_status_counts=dict(Counter(s['status'] for s in searches)),unique_missing_pairs=len(missing),
            original_starts=len(runs_all),outer_iterations=sum(len(r['iterations']) for r in runs_all),
            coordinate_refinement_progress=progress,figures=figures,targeted_reference_statuses=[{'coordinate':s['label'],'best_value':s['best_value'],'K':s['best_K'],'status':s['status'],'bracket':s['bracket'],'missing':s['source_missing']} for s in targeted])
        test_results=[]
        for pattern in ('test_ao_phase2a_execution.py','test_ao_phase2a_preparation.py','test_ao_numerical_optimum_audit.py',
            'test_windows_sleep_safe_supervision.py','test_alt_opt_provenance_and_stopping.py','test_mb_batch3_resume.py'):
            done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
            test_results.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
        io.save_json(OUT/'final_regression_tests.json',test_results)
        assert all(r['returncode']==0 for r in test_results)
        done=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
        assert done.returncode==0,done.stdout+done.stderr
        summary['tests']='CURRENTLY_VERIFIED_PASS';summary['git_diff_check']='CURRENTLY_VERIFIED_PASS'
    io.save_json(OUT/'postprocess_report.json',summary)
    supervisor.verify_protected(OUT)
    return 0


def save_report(ledger):
    post=read(OUT/'postprocess_report.json') if (OUT/'postprocess_report.json').exists() else None
    summary={**ledger,'new_budget_approved':True,'stage2':'EXECUTED','successful_probes':sum(r['status']=='COMPLETED_EXACT' for r in ledger['attempts']),
        'timeout_probes':sum(r['status']=='TIMEOUT' for r in ledger['attempts']),
        'stopped_probes':sum(r['status'] not in ('COMPLETED_EXACT','TIMEOUT') for r in ledger['attempts']),
        'not_run_probes':3-len(ledger['attempts']),'postprocess':post,'protected_files_unchanged':supervisor.verify_protected(OUT),
        'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','continuous_global_optimum':False,
        'scientific_implementation_changed':False,'no_interpolation':True,'phase2B_executed':False,
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','frozen_spec_discrepancy':'PREEXISTING_UNCHANGED'}
    io.save_json(OUT/'phase_2A_report.json',summary)
    lines=['# Phase2A actual execution report','',summary['status'],'',
        f"Success={summary['successful_probes']}, timeout={summary['timeout_probes']}, stopped={summary['stopped_probes']}, not run={summary['not_run_probes']}.",
        f"Authorization wall={ledger.get('budget_session_wall_seconds')}s/10800s; measured Job+controllerCPU={ledger.get('total_CPU_seconds')}s.",
        'CPU excludes setup/interactive diagnostic processes; all supervised AP/objective/AO/test workers included in Job CPU where captured.',
        'Deadline not reset;480s final reserve; no automatic retry or extra AP/Phase2B.',
        f"Sleep restoration={ledger.get('sleep_prevention',{}).get('released_verified')}; no scientific workers={ledger.get('worker_cleanup_verified')}.",
        '', '|Probe|nu_raw|VA|status|C|w|wall s|CPU s|','|---|---|---|---|---|---|---|---|']
    for r in ledger['attempts']:
        lines.append(f"|{r['batch']}|{r['nu_raw']}|{r['V_A']}|{r['status']}|{r.get('C','')}|{r.get('w','')}|{r.get('wall_seconds','')}|{r.get('cpu_seconds','')}|")
    if post:
        lines += ['',f"Catalog MB={post['MB_count']}; new objective rows={post['new_objective_rows']}; improved distances={post['improved_distances']}.",
            f"Reference best=({post['reference']['new_nu']},{post['reference']['new_V_A']}),K={post['reference']['new_K']}.",
            f"22km best=({post['at22km']['new_nu']},{post['at22km']['new_V_A']}),K={post['at22km']['new_K']}.",
            f"Genuine originalAO rechecked={post['AO_rechecked']}; independently matched={post['AO_catalog_matches']}/26; closed final directions={post['closed_selected_directions']}.",
            'Detailed actual P1/P2 bracket widths/gaps/next dependencies are in coordinate_completion_status.csv and reference_targeted_coordinate_searches.json.',
            'coordinate_refinement_progress.csv distinguishes old paired-source coverage from current invocation stage counters; narrower catalog brackets do not mean a complete coordinate search.',
            'All starts, especiallynu0=.8, have real updates in cache_only_runs.json/ao_iteration_history.csv; no catalog-winner copying.',
            '', '|L km|nu|VA|I_AB|betaI|chi|K|AO match|','|---|---|---|---|---|---|---|---|']
        for r in io.read_csv(OUT/'old_vs_new_skr_optimum.csv'):
            lines.append(f"|{r['L_km']}|{r['new_nu']}|{r['new_V_A']}|{r['I_AB']}|{r['beta_I_AB']}|{r['chi_BE']}|{r['new_K']}|{r['AO_match']}|")
    lines += ['', 'Original physics/source1050/1250/1450/GH8/directZminus/ALT_OPT unchanged. No interpolation or continuous/global optimality claim.',
        'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED: original-evaluator repeatability is not a whole-objective numerical error bound.',
        'Nu=0 compatible storedUniform comparison remains useful but does not close continuousnu=0/Uniformoptimization. Strictpositive optimizer not changed.',
        'Current outputs are finite-catalog best-observed candidates unless actual closure/error evidence supports stronger claims.',
        f"Error={ledger.get('error')}; frozen-spec discrepancy/lifecycle restrictions unchanged."]
    (OUT/'phase_2A_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'numerical_accuracy_status.md').write_text('# Numerical accuracy\n\nORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED.\n'
        'Unchanged original AP/source support and provenance verified for successes. Retained receipts do not enclose per-precision whole-K error.\n'
        'Original-evaluator repeats (if final postprocessing succeeded) are in original_evaluator_reproducibility.csv.\n'
        'No precision/quadrature/method changes, no certified numerical/global optimum.\n',encoding='utf-8')
    if post and post['AO_rechecked']:
        ref=post['reference'];unchanged=ref['new_V_A']==5.5
        target=next(s for s in post['targeted_reference_statuses'] if s['coordinate']=='P2')
        still_missing=any(float(e['value']).hex()==(.16375).hex() for e in target['missing'])
        (OUT/'phase_2B_hard_probe_plan.md').write_text('# Phase2B: actual post-Phase2A necessity review\n\n'
            f"Finalreference pair=({ref['new_nu']},{ref['new_V_A']}); originalVA5.5 P2 still requests lowernu.16375={still_missing}.\n"
            f"FinalselectedVA remains5.5={unchanged}. IfFalse, the hardpair is not automatically a dependency of the selected newVA slice.\n"
            'Consult final selected-coordinate requests separately from the old target5.5 diagnostic. Do not execute this pair blindly for catalog size.\n'
            'Prior3600s timeout/measured3595.75s,CPU3469.96875s gives a runtime lower-limit risk, no predicted completiontime.\n'
            'If its actual dependency/sensitivity purpose remains justified, a separate120min ceiling plus processing allowance may be considered; fresh explicitapproval required.\n'
            'No auto retry, precision increase or different source method. Coordinate coverage and total numerical error control are BOTH needed for reliability.\n',encoding='utf-8')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-approved-phase2a',action='store_true')
    parser.add_argument('--process',action='store_true');parser.add_argument('--ao',action='store_true')
    args=parser.parse_args()
    if args.process or args.ao:
        return process(args.ao)
    if not args.execute_approved_phase2a:
        parser.error('Explicit approved execution flag required')
    if (OUT/'source_generation_ledger.json').exists():
        raise SystemExit('Existing execution checkpoint: never automatically repeat or reset authorization')
    auth=read(OUT/'execution_authorization.json')
    assert auth['status']=='EXPLICITLY_APPROVED_PHASE2A' and auth['pairs']==[list(p) for p in prep.PAIRS]
    deadline=auth['deadline_monotonic']; assert budget_limit(deadline,time.monotonic())>60
    supervisor.verify_protected(OUT)
    assert not prep.worker_inventory() and safe.safe_power(safe.WindowsPower().read())
    snapshot=OUT/'preparation_snapshot';snapshot.mkdir()
    for path in list(OUT.iterdir()):
        if path.is_file():shutil.copy2(path,snapshot/path.name)
    manifest=read(OUT/'protected_input_manifest.json')
    manifest.update(io.raw_snapshot([*snapshot.rglob('*'),Path(__file__),ROOT/'tests/test_ao_phase2a_execution.py']))
    io.save_json(OUT/'protected_input_manifest.json',manifest)
    stop=threading.Event();cpu_start=time.process_time()
    ledger={'status':'APPROVED_PHASE2A_STARTING','controller_pid':os.getpid(),'attempts':[],'used_wall_seconds':0,
        'completed_unique_ensembles':0,'authorization':auth,'budget_reset':False,'authorization_session_origin_utc':auth['origin_utc'],
        'absolute_deadline_monotonic':deadline,'started_utc':datetime.now(timezone.utc).isoformat(),'supervision_receipts':[]}
    io.save_json(OUT/'source_generation_ledger.json',ledger)
    io.save_json(OUT/'phase_2A_report.json',{**ledger,'status':'RUNNING_APPROVED_PHASE2A','new_budget_approved':True,'stage2':'RUNNING',
        'live_checkpoint':'source_generation_ledger.json and probe_results/*.json','preparation_snapshot_preserved':True})
    def heartbeat():
        while not stop.wait(45):
            print(f'Phase2A remaining={deadline-time.monotonic():.1f}s, saved probes={len(ledger["attempts"])}',flush=True)
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
    original_supervisor=supervisor.supervised_probe
    def guarded(command,timeout,log):
        with patch.object(supervisor,'supervised_probe',original_supervisor):
            return safe.supervised_process(command,timeout,log)
    lease=safe.AwakeOnAC();error=None
    try:
        with lease:
            io.save_json(OUT/'active_power_preflight.json',{'AC':safe.WindowsPower().read(),'lease':lease.receipt,'deadline_monotonic':deadline})
            with patch.object(prep.native,'OUT',OUT):
                ledger['supervision_receipts'].extend(prep.native.native_wall_preflight())
            for number,p in enumerate(points(),1):
                limit=budget_limit(deadline,time.monotonic())
                if limit<=10:break
                supervisor.verify_protected(OUT)
                assert safe.safe_power(safe.WindowsPower().read()) and not prep.worker_inventory()
                assert not (OUT/'probe_results'/f"{p['source_cache_key']}.json").exists()
                bank=source.load_source_payloads(source.unconstrained_config(),DIRS)
                assert source.candidate_from_payload(source.unconstrained_config(),bank,'MB',float(p['nu_raw']),float(p['V_A'])) is None
                with patch.object(supervisor,'supervised_probe',guarded):
                    record=supervisor.run_batch(OUT,p,limit,number,ledger)
                rec=record['supervision'];ledger['supervision_receipts'].append(rec)
                io.write_csv(OUT/'execution_ledger.csv',[{k:r.get(k) for k in ('batch','nu_raw','V_A','cache_key','status','C','w','wall_seconds','cpu_seconds','timeout_seconds','source_payload_verified','error')} for r in ledger['attempts']])
                assert not prep.worker_inventory(),'Scientific worker remains after source Job'
                if not rec['wall_limit_respected'] or not rec['no_watchdog_thread_remaining'] or rec['power_watch']['abort_reason'] not in (None,'ABSOLUTE_DEADLINE'):
                    raise RuntimeError('Unsafe power/deadline/worker cleanup: stop all, no auto retry')
                if record['status'] not in ('COMPLETED_EXACT','TIMEOUT'):
                    raise RuntimeError('Serious source/provenance failure: '+record['status'])
                if record['status']=='COMPLETED_EXACT':
                    with (OUT/f'objectives_after_probe_{number}.log').open('w',encoding='utf-8') as log:
                        rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--process'],deadline-time.monotonic()-60,log)
                    ledger['supervision_receipts'].append(rec)
                    io.save_json(OUT/f'objectives_after_probe_{number}_supervision.json',rec)
                    if rec['returncode']!=0 or not rec['wall_limit_respected']:
                        raise RuntimeError('New26distance objective/provenance processing failed')
                io.save_json(OUT/'source_generation_ledger.json',ledger)
            if deadline-time.monotonic()<=60:raise RuntimeError('Budget exhausted before final AO')
            with (OUT/'final_alt_opt.log').open('w',encoding='utf-8') as log:
                rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--ao'],deadline-time.monotonic()-45,log)
            ledger['supervision_receipts'].append(rec);io.save_json(OUT/'final_AO_supervision.json',rec)
            if rec['returncode']!=0 or not rec['wall_limit_respected']:raise RuntimeError('Original AO/final validation failed')
            ledger['status']='PHASE2A_COMPLETE_FINITE_CATALOG_SCOPE'
    except BaseException as exc:
        error=repr(exc);ledger['status']='STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET';print(error,flush=True)
    finally:
        stop.set();thread.join(timeout=2)
        ledger.update(error=error,sleep_prevention=lease.receipt,budget_session_wall_seconds=time.monotonic()-auth['origin_monotonic'],
            controller_cpu_seconds=time.process_time()-cpu_start,total_job_cpu_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in ledger['supervision_receipts']),
            worker_cleanup_verified=not prep.worker_inventory(),wall_budget_respected=time.monotonic()<=deadline)
        ledger['total_CPU_seconds']=ledger['controller_cpu_seconds']+ledger['total_job_cpu_seconds']
        io.save_json(OUT/'source_generation_ledger.json',ledger)
        summary=save_report(ledger)
        io.save_json(OUT/'sleep_prevention_final_receipt.json',lease.receipt)
        io.save_json(OUT/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in manifest})
        print(json.dumps({k:summary[k] for k in ('status','successful_probes','timeout_probes','stopped_probes','not_run_probes','budget_session_wall_seconds','error')}),flush=True)
    return 1 if error else 0


if __name__=='__main__':
    raise SystemExit(main())
