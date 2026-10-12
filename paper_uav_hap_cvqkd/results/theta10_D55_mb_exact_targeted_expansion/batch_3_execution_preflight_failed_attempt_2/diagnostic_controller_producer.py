"""Approved Batch3: original exact probes/AO, strict145 baseline and power guards."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import threading
import time
import tempfile
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_mb_batch2 as previous
from scripts import windows_sleep_safe_supervision as safe

ao,io,source,sweep,supervisor=previous.ao,previous.io,previous.source,previous.sweep,previous.supervisor
BASE=previous.OUT
OUT=BASE.parent/'batch_3'
PAIRS=((.165,5.4625),(.165,5.4875),(.16531250000000003,5.5))
DIRS=(*previous.DIRS,OUT/'exact_source_cache')


def points():
    rows=io.read_csv(OUT/'preparation_snapshot/batch_3_final_selected_probes.csv')
    assert tuple((float(r['nu_raw']),float(r['V_A'])) for r in rows)==PAIRS
    for r in rows:
        r['raw_current_cache_key']=r['source_cache_key']
        assert r['nu_raw_hex']==float(r['nu_raw']).hex() and r['V_A_hex']==float(r['V_A']).hex()
    return rows


def evaluate(run_ao=False):
    import torch
    torch.set_num_threads(1)
    supervisor.verify_protected(OUT)
    config=source.unconstrained_config()
    bank=source.load_source_payloads(config,DIRS)
    mb=[p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex'])>0]
    assert 145<=len(mb)<=148
    io.write_csv(OUT/'expanded_mb_catalog.csv',[{'nu_raw':float.fromhex(p['nu_mb_raw_hex']),'V_A':float.fromhex(p['V_A_hex']),
        'C':p['C'],'w':p['w'],'source_cache_key':p['cache_key'],'ensemble_hash':p['ensemble_hash']} for p in mb])
    original=json.loads((BASE/'objective_checkpoint.json').read_text())
    baseline={float(r['L_km']):r for r in io.read_csv(BASE/'previous_vs_new_optimum.csv')}
    old_top=io.read_csv(BASE/'top_two_candidates.csv')
    historical={float(r['L_km']):r for r in io.read_csv(previous.previous.prior.CERT/'catalog_maximum_certificate.csv')}
    saved=json.loads((OUT/'objective_checkpoint.json').read_text()) if (OUT/'objective_checkpoint.json').exists() else {}
    comparisons,top,new_rows,records,runs_all,searches=[],[],[],[],[],[]
    warm=None
    original_search=ao.adaptive_maximize_1d
    def record_search(**kw):
        result=original_search(**kw)
        searches.append({'L_km':kw['objective'].channel['distance_km'],**result})
        return result
    with patch.object(ao.ExactMBEvaluator,'source_moments',previous.previous.prior.forbidden), \
         patch.object(ao,'adaptive_maximize_1d',record_search),patch.object(sweep,'adaptive_maximize_1d',record_search):
        for distance in sweep.DISTANCES_KM:
            obj=ao.ExactObjective(config,sweep.make_channel(config,distance),OUT,allow_new_source=False,source_cache_dirs=DIRS)
            cached=original[str(distance)]
            assert obj.restore_objective_rows(cached['rows'],cached['identity'])==145
            if str(distance) in saved:
                obj.restore_objective_rows(saved[str(distance)]['rows'],saved[str(distance)]['identity'])
            for p in mb:
                nu,va=float.fromhex(p['nu_mb_raw_hex']),float.fromhex(p['V_A_hex'])
                obj.register_catalog(nu,va)
                obj(nu,va)
            ranked=sorted(obj.rows.values(),key=lambda r:float(r['SKR']),reverse=True)
            assert len(ranked)==len(mb)
            best,second=ranked[:2]
            old=baseline[distance]
            old_second=next(r for r in old_top if float(r['L_km'])==distance and r['rank']=='2')
            old_gap=float(old['new_K'])-float(old_second['SKR'])
            comparisons.append({'L_km':distance,'old_nu':old['new_nu'],'old_V_A':old['new_V_A'],'old_K':old['new_K'],
                'new_nu':best['nu_raw'],'new_V_A':best['V_A'],'I_AB':best['I_AB'],'beta_I_AB':best['beta_I_AB'],'chi_BE':best['chi_BE'],
                'new_K':best['SKR'],'delta_K':float(best['SKR'])-float(old['new_K']),
                'historical136_K':historical[distance]['best_K'],'runner_up_nu':second['nu_raw'],'runner_up_V_A':second['V_A'],
                'runner_up_K':second['SKR'],'old_top_two_gap':old_gap,'new_top_two_gap':float(best['SKR'])-float(second['SKR']),
                'top_two_gap_change':float(best['SKR'])-float(second['SKR'])-old_gap,'MB_count':len(mb),
                'scope':'FINITE_EXACT_CATALOG_NUMERIC_ORDER_NOT_CONTINUOUS_GLOBAL'})
            top.extend({'L_km':distance,'rank':rank,**r} for rank,r in enumerate((best,second),1))
            for nu,va in PAIRS:
                if source.candidate_from_payload(config,bank,'MB',nu,va) is not None:
                    new_rows.append(obj(nu,va))
            saved[str(distance)]={'identity':obj.objective_identity,'rows':list(obj.rows.values())}
            io.save_json(OUT/'objective_checkpoint.json',saved)
            io.write_csv(OUT/'old_vs_new_optimum.csv',comparisons)
            io.write_csv(OUT/'top_two_candidates.csv',top)
            if new_rows:
                io.write_csv(OUT/'exact_skr_26_distances.csv',new_rows)
            if run_ao:
                starts=[(f'nu_{nu:g}',nu,None) for nu in sweep.BASE_STARTS]
                if warm:
                    starts.append(('warm_previous_distance',*warm))
                runs=[sweep.run_single_distance_ao(distance_km=distance,start_id=sid,start_nu=nu,start_va=va,
                    objective=obj,max_iterations=ao.MAX_AO_ITERATIONS) for sid,nu,va in starts]
                chosen=max((r for r in runs if r.get('final')),key=lambda r:float(r['final']['SKR']))
                final=chosen['final']
                warm=float(final['nu_raw']),float(final['V_A'])
                checks=[record_search(variable=v,fixed=f,values=obj.catalog_values(v,f),objective=obj)
                    for v,f in (('V_A',warm[0]),('nu_raw',warm[1]))]
                complete=all(ao.coordinate_search_complete(s) for s in checks)
                winners=all(s.get('best') and float(s['best']['SKR'])<=float(final['SKR'])+ao.K_TOLERANCE for s in checks)
                status=chosen['status']
                if status=='CONVERGED_NUMERICALLY' and not (complete and winners):
                    status='STAGNATED_IN_EXACT_CATALOG'
                records.append({'L_km':distance,'nu_raw_star':warm[0],'V_A_star':warm[1],'K':final['SKR'],
                    'catalog_K':best['SKR'],'matches_catalog_maximum':float(final['SKR'])==float(best['SKR']),
                    'I_AB':final['I_AB'],'beta_I_AB':final['beta_I_AB'],'chi_BE':final['chi_BE'],'status':status,
                    'local_coordinate_search_complete':complete,'selected_start':chosen['start_id'],
                    'missing_source_attempts':len(obj.source_missing),'global_optimum_resolved':False,
                    'total_outer_iterations':sum(len(r['iterations']) for r in runs), 'multistart_runs':len(runs),
                    'objective_requested_calls':obj.requested_calls,'unique_exact_objective_evaluations':obj.unique_exact_evaluations,
                    'objective_cache_hits':obj.cache_hits})
                runs_all.extend({'L_km':distance,**r} for r in runs)
                io.write_csv(OUT/'alt_opt_validation.csv',records)
                io.save_json(OUT/'cache_only_searches.json',searches)
                io.save_json(OUT/'cache_only_runs.json',runs_all)
            print(f'Batch3 L={distance}: MB={len(mb)}, K={best["SKR"]}, AO={run_ao}',flush=True)
    local22=list(saved['22.0']['rows'])
    selected22=max(local22,key=lambda r:float(r['SKR']))
    for name,variable,fixed in (('exact_va_slice_22km.csv','nu_raw',float(selected22['nu_raw'])),
                               ('exact_nu_slice_22km.csv','V_A',float(selected22['V_A']))):
        rows=sorted((r for r in local22 if float(r[variable]).hex()==fixed.hex()),
                    key=lambda r:float(r['V_A' if variable=='nu_raw' else 'nu_raw']))
        io.write_csv(OUT/name,[{**r,'K':r['SKR'],'delta_to_best22':float(r['SKR'])-float(selected22['SKR'])} for r in rows])
    io.write_csv(OUT/'catalog_exact_objectives.csv',[r for p in saved.values() for r in p['rows']])
    if run_ao:
        io.write_csv(OUT/'coordinate_search_status.csv',[
            {k:s.get(k) for k in ('L_km','variable','fixed','status','best_value','best_K','boundary_status',
                'refinement_status','evaluated','refinement_stages','boundary_expansions','bracket','range')}
            | {'numeric_coordinate_complete':ao.coordinate_search_complete(s)} for s in searches])
    old_searches=json.loads((BASE/'cache_only_searches.json').read_text())
    changed=[]
    if run_ao:
        for distance in sweep.DISTANCES_KM:
            before=[s for s in old_searches if s['L_km']==distance][-2:]
            after=[s for s in searches if s['L_km']==distance][-2:]
            for a,b in zip(before,after):
                changed.append({'L_km':distance,'coordinate':b['variable'],'before_fixed':a['fixed'],'after_fixed':b['fixed'],
                    'before_status':a['status'],'after_status':b['status'],'boundary_status':b.get('boundary_status'),
                    'same_slice':a['fixed']==b['fixed'],'newly_closed':a['fixed']==b['fixed'] and not ao.coordinate_search_complete(a) and ao.coordinate_search_complete(b)})
        io.write_csv(OUT/'coordinate_changes.csv',changed)
    missing={}
    for s in searches:
        for e in s['history']:
            if e['status']=='EXACT_SOURCE_MISSING':
                nu,va=(s['fixed'],e['value']) if s['variable']=='V_A' else (e['value'],s['fixed'])
                item=missing.setdefault((float(nu).hex(),float(va).hex()),{'nu_raw':nu,'V_A':va,'requests':0,'distances':set()})
                item['requests']+=1
                item['distances'].add(s['L_km'])
    if run_ao:
        io.write_csv(OUT/'remaining_missing_exact_pairs.csv',[{**r,'distances':json.dumps(sorted(r['distances']))} for r in missing.values()])
    result={'MB_count':len(mb),'new_source_objectives':len(new_rows),'distances_evaluated':len(comparisons),
        'improved_distances':[r['L_km'] for r in comparisons if r['delta_K']>0],
        'largest_numeric_gain':max(r['delta_K'] for r in comparisons),'reference22_K':float(baseline[22.]['new_K']),
        'AO_rechecked':run_ao,'AO_matches_catalog':sum(r['matches_catalog_maximum'] for r in records),'AO_distances':len(records),
        'coordinate_calls':len(searches),'coordinate_status_counts':dict(Counter(s['status'] for s in searches)),
        'selected_status_counts':dict(Counter(r['status'] for r in records)),
        'newly_closed_selected_searches':[r for r in changed if r['newly_closed']],
        'unique_missing_pairs':len(missing) if run_ao else None,'continuous_global_optimum_claimed':False,
        'total_objective_error_bound':'NOT_ESTABLISHED',
        'numerical_ranking_status':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED',
        'total_outer_iterations':sum(len(r['iterations']) for r in runs_all),
        'total_multistart_runs':len(runs_all),
        'newly_closed_coordinate_invocations':sum(ao.coordinate_search_complete(s) for s in searches),
        'baseline_closed_coordinate_invocations':sum(ao.coordinate_search_complete(s) for s in old_searches)}
    io.save_json(OUT/'postprocess_report.json',result)
    supervisor.verify_protected(OUT)


def reassess(remaining,after_probe):
    """Retain authorized order absent measured redundancy; never predict missing K."""
    if not (OUT/'objective_checkpoint.json').exists():
        return
    saved=json.loads((OUT/'objective_checkpoint.json').read_text())
    comparisons=io.read_csv(OUT/'old_vs_new_optimum.csv')
    log=[]
    for p in remaining:
        nu,va=float(p['nu_raw']),float(p['V_A'])
        neighborhoods=[]
        for distance in json.loads(p.get('affected_distances','[21.9393102292,22.0]')):
            candidates=[r for r in saved[str(distance)]['rows'] if float(r['nu_raw']).hex()==nu.hex()]
            lower=max((r for r in candidates if float(r['V_A'])<va),key=lambda r:float(r['V_A']),default=None)
            upper=min((r for r in candidates if float(r['V_A'])>va),key=lambda r:float(r['V_A']),default=None)
            best=next(r for r in comparisons if float(r['L_km'])==distance)
            neighborhoods.append({'L_km':distance,'lower_V_A':lower['V_A'] if lower else None,'lower_K':lower['SKR'] if lower else None,
                'upper_V_A':upper['V_A'] if upper else None,'upper_K':upper['SKR'] if upper else None,
                'current_best_nu':best['new_nu'],'current_best_V_A':best['new_V_A'],'current_best_K':best['new_K']})
        log.append({'nu_raw':nu,'V_A':va,'decision':'RETAIN_AUTHORIZED_PRIORITY',
            'reason':'Independent originally unresolved midpoint remains unmeasured; actual updated neighbors do not establish redundancy. No monotonicity/error-bound assumption.',
            'observed_neighborhoods':neighborhoods,'unknown_candidate_K':'NOT_PREDICTED'})
    io.save_json(OUT/f'reassessment_after_probe_{after_probe}.json',{'remaining':log,'scope':'MEASURED_EXACT_DATA_ONLY'})
    print(f'Reassessment after probe{after_probe}: retain{len(remaining)} remaining original priorities, no missing K predicted',flush=True)


def native_preflight():
    """Original native supervisor: real busy Job and descendant deadline checks."""
    receipts=[]
    for limit,tree in ((.8,False),(1.2,True)):
        marker='batch3_dummy_'+uuid.uuid4().hex
        code='while True: pass'
        if tree:
            code="import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','while True: pass',sys.argv[1]]); print('CHILD_PID='+str(p.pid),flush=True); exec('while True: pass')"
        with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as log:
            rec=safe.supervised_process([sys.executable,'-B','-c',code,marker],limit,log)
            log.seek(0)
            rec['dummy_log']=log.read()
        io.save_json(OUT/'native_job_sleep_preflight.json',{'status':'PREFLIGHT_RUNNING','dummy_jobs':receipts+[rec]})
        assert rec['deadline_exceeded'] and rec['returncode']==124, ('Dummy deadline did not terminate',rec)
        assert rec['wall_limit_respected'] and rec['no_watchdog_thread_remaining'], ('Dummy deadline/cleanup failed',rec)
        assert rec['sleep_prevention']['active_verified'] and rec['sleep_prevention']['released_verified']
        if tree:
            assert 'CHILD_PID=' in rec['dummy_log'], ('Dummy descendant not started',rec)
        command="$n=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*"+marker+"*'}).Count; if ($n -ne 0) {throw 'Dummy tree remains'}; 'CLEAN'"
        check=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
        assert check.stdout.strip()=='CLEAN'
        rec['worker_cleanup_verified']=True
        receipts.append(rec)
    io.save_json(OUT/'native_job_sleep_preflight.json',{'status':'CURRENTLY_VERIFIED_PASS','dummy_jobs':receipts,
        'scope':'SHORT_NATIVE_DEADLINE_AND_DESCENDANT_TEST_NOT_FULL_DURATION_GUARANTEE'})
    return receipts


def render_report(report):
    lines=['# Batch3 exact MB refinement','','Status: '+report['status'],'',
        'Original scientific implementation,1050/1250/1450 policy,GH8/direct-Zminus and ALT_OPT unchanged. No interpolation.',
        'Numerical ranking: ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no total objective error bound or continuous/global claim.','',
        '## Probe outcomes','',
        '| Probe | nu_raw | VA | C | w | Status | Wall seconds | Job CPU seconds |',
        '|---|---|---|---|---|---|---|---|']
    for r in report['attempts']:
        lines.append('| '+' | '.join(str(r.get(k,'NOT_AVAILABLE')) for k in
            ('batch','nu_raw','V_A','C','w','status','wall_seconds','cpu_seconds'))+' |')
    lines += ['',f"Successful={report['successful_probes']}; timeout={report['timeout_probes']}.",
        f"Wall={report['budget_session_wall_seconds']}s/10800s; measured Job+controller CPU={report['total_CPU_seconds']}s.",
        f"Wall compliance={report['wall_budget_respected']}; error={report['error']}.",
        'Total includes execution and between-probe processing; preparation/tests before session are excluded.',
        'Sleep prevention active across campaign, restored in finally; no permanent power-plan change.',
        'See individual supervision receipts for real deadlines, power watches and worker cleanup.','']
    if report['postprocess']:
        lines += ['## Expanded finite catalog and original ALT_OPT','','```json',
            json.dumps(report['postprocess'],indent=2),'```','',
            '| L km | Old nu | Old VA | New nu | New VA | Old K | New K | Delta K |',
            '|---|---|---|---|---|---|---|---|']
        for r in io.read_csv(OUT/'old_vs_new_optimum.csv'):
            lines.append('| '+' | '.join(r[k] for k in
                ('L_km','old_nu','old_V_A','new_nu','new_V_A','old_K','new_K','delta_K'))+' |')
        lines += ['','Runner-up/top-two gaps: top_two_candidates.csv and old_vs_new_optimum.csv.',
            'Full histories: cache_only_runs.json/cache_only_searches.json. Coordinate final-pair changes compare same slices only.',
            'Local exact VA/nu slices at22km and all new successful source objectives at26 distances are saved; missing K is never inferred.',
            'Further expansion is conditional coverage/sensitivity work, not a promised gain or convergence certificate.']
    lines += ['',f"Protected files unchanged={report['protected_files_unchanged']}.",
        'Earlier selection snapshots and all previous numerical artifacts preserved.',
        'Frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain; no training/test/baseline/threshold approval.']
    (OUT/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-approved-batch3',action='store_true')
    parser.add_argument('--evaluate',action='store_true')
    parser.add_argument('--ao',action='store_true')
    args=parser.parse_args()
    if args.evaluate or args.ao:
        return evaluate(args.ao)
    if not args.execute_approved_batch3:
        parser.error('Explicit approved execution flag required')
    if (OUT/'source_generation_ledger.json').exists():
        raise SystemExit('Execution checkpoint exists; never automatically repeat')
    supervisor.verify_protected(OUT)
    # Refuse a stale baseline or any prior attempt: no automatic AP replay.
    baseline=json.loads((BASE/'run_report.json').read_text())
    assert baseline['postprocess']['MB_count']==145
    snapshot=OUT/'preparation_snapshot'
    snapshot.mkdir()
    for p in list(OUT.iterdir()):
        if p.is_file():
            shutil.copy2(p,snapshot/p.name)
    manifest=json.loads((OUT/'protected_input_manifest.json').read_text())
    manifest.update(io.raw_snapshot(list(snapshot.rglob('*'))+[Path(__file__)]))
    io.save_json(OUT/'protected_input_manifest.json',manifest)
    supervisor.verify_protected(OUT)
    selected=points()
    assert (ao.K_TOLERANCE,ao.PARAMETER_TOLERANCE,ao.MAX_AO_ITERATIONS,ao.MAX_REFINEMENT_STAGES)==(1e-8,1e-6,6,4)
    config=source.unconstrained_config()
    bank=source.load_source_payloads(config,previous.DIRS)
    assert sum(float.fromhex(p['nu_mb_raw_hex'])>0 for p in bank.values())==145
    identity_evaluator=ao.ExactMBEvaluator(config,{'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},OUT,
        source_cache_dir=OUT/'exact_source_cache',allow_legacy_exact_import=False)
    for p in selected:
        nu,va=float(p['nu_raw']),float(p['V_A'])
        assert source.candidate_from_payload(config,bank,'MB',nu,va) is None
        identity=identity_evaluator._source_identity(source.make_ensemble(config,'MB',nu,va),nu,va)
        assert source.json_hash(identity)==p['raw_current_cache_key'] and identity['ensemble_hash']==p['ensemble_hash']
    lease=safe.AwakeOnAC()
    started=time.monotonic()
    recovery=OUT.parent/'batch_3_execution_preflight_failed_attempt_1/source_generation_ledger.json'
    prior_preflight=None
    if recovery.exists():
        prior_preflight=json.loads(recovery.read_text())
        assert not prior_preflight['attempts'], 'Never automatically repeat a prior AP attempt'
        origin=datetime.strptime(prior_preflight['started_utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        started-=(datetime.now(timezone.utc)-origin).total_seconds()
    deadline=started+10800.
    cpu_start=time.process_time()
    ledger={'status':'AUTHORIZED_BATCH3_RUNNING','attempts':[],'used_wall_seconds':0.,'total_compute_budget_seconds':10800.,
        'per_probe_timeout_seconds':3600.,'controller_pid':os.getpid(),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'baseline_MB_count':145,'final_AO_cleanup_reserve_seconds':480.,'authorization':'Explicit user approval batch3 all up-to3 serial probes; continue independent probes after timeout, no retries',
        'scientific_implementation_changed':False,'producer_sha256':io.digest(__file__)}
    receipts=[]
    if prior_preflight is not None:
        ledger.update(authorization_session_origin_utc=prior_preflight['started_utc'],
            preflight_recovery='Original session deadline retained, zero prior AP attempts; failed preflight archived',
            prior_failed_preflight_CPU_seconds='NOT_FULLY_MEASURED_EXCLUDED_FROM_MEASURED_SUM')
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(45):
            print(f'Batch3 supervised: wall={time.monotonic()-started:.1f}s/10800s, saved attempts={len(ledger["attempts"])}',flush=True)
    threading.Thread(target=heartbeat,daemon=True).start()
    original_supervisor=supervisor.supervised_probe
    def guarded(command,timeout,log):
        with patch.object(supervisor,'supervised_probe',original_supervisor):
            return safe.supervised_process(command,timeout,log)
    error=None
    try:
        with lease:
            io.save_json(OUT/'active_power_preflight.json',{'status':'CURRENTLY_VERIFIED_PASS','lease':lease.receipt,'fresh_budget_confirmed':True})
            io.save_json(OUT/'source_generation_ledger.json',ledger)
            io.save_json(OUT/'run_report.json',{'status':'AUTHORIZED_BATCH3_RUNNING','controller_pid':os.getpid(),'fresh_budget_confirmed':True,'live_checkpoint':'source_generation_ledger.json'})
            receipts.extend(native_preflight())
            # Approval begins a NEW session; no carried-over time from prior batches.
            for number,p in enumerate(selected,1):
                limit=min(3600.,deadline-time.monotonic()-480.)
                if limit<=10:
                    break
                with patch.object(supervisor,'supervised_probe',guarded):
                    record=supervisor.run_batch(OUT,p,limit,number,ledger)
                receipts.append(record['supervision'])
                io.write_csv(OUT/'probe_execution_ledger.csv',[{k:r.get(k) for k in ('batch','nu_raw','V_A','cache_key','status','C','w','wall_seconds','cpu_seconds','timeout_seconds','source_payload_verified','error')} for r in ledger['attempts']])
                io.write_csv(OUT/'new_exact_mb_sources.csv',[{k:r.get(k) for k in ('batch','nu_raw','V_A','C','w','cache_key','status','source_payload_verified')} for r in ledger['attempts']])
                rec=record['supervision']
                if not rec['wall_limit_respected'] or rec['power_watch']['abort_reason'] not in (None,'ABSOLUTE_DEADLINE') or not rec['no_watchdog_thread_remaining']:
                    raise RuntimeError('Unsafe power/deadline or cleanup')
                if record['status'] not in ('COMPLETED_EXACT','TIMEOUT'):
                    raise RuntimeError('Serious source/provenance failure: '+record['status'])
                if record['status']=='COMPLETED_EXACT':
                    with (OUT/f'objectives_after_probe_{number}.log').open('w',encoding='utf-8') as log:
                        rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--evaluate'],deadline-time.monotonic()-15,log)
                    receipts.append(rec)
                    io.save_json(OUT/f'objectives_after_probe_{number}_supervision.json',rec)
                    if rec['returncode']!=0 or not rec['wall_limit_respected']:
                        raise RuntimeError('Exact objective expansion failed or exceeded deadline')
                    reassess(selected[number:],number)
            if deadline-time.monotonic()<=15:
                raise RuntimeError('Total deadline exhausted before final AO')
            with (OUT/'final_alt_opt.log').open('w',encoding='utf-8') as log:
                rec=safe.supervised_process([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),'--ao'],deadline-time.monotonic()-10,log)
            receipts.append(rec)
            io.save_json(OUT/'final_AO_supervision.json',rec)
            if rec['returncode']!=0 or not rec['wall_limit_respected']:
                raise RuntimeError('Final AO failed or exceeded deadline')
            ledger['status']='BATCH3_FINISHED_FINITE_CATALOG_SCOPE'
    except BaseException as exc:
        error=repr(exc)
        ledger['status']='STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET'
        print(error,flush=True)
    finally:
        stop.set()
        ledger.update(error=error,budget_session_wall_seconds=time.monotonic()-started,sleep_prevention=lease.receipt,
            supervision_receipts=receipts,total_job_cpu_seconds=sum(r.get('aggregate_cpu_seconds',0) for r in receipts),
            controller_cpu_seconds=time.process_time()-cpu_start)
        ledger['total_CPU_seconds']=ledger['total_job_cpu_seconds']+ledger['controller_cpu_seconds']
        ledger['wall_budget_respected']=ledger['budget_session_wall_seconds']<=10800.
        io.save_json(OUT/'source_generation_ledger.json',ledger)
        result=json.loads((OUT/'postprocess_report.json').read_text()) if (OUT/'postprocess_report.json').exists() else None
        report={**ledger,'successful_probes':sum(r['status']=='COMPLETED_EXACT' for r in ledger['attempts']),
            'timeout_probes':sum(r['status']=='TIMEOUT' for r in ledger['attempts']),'postprocess':result,
            'protected_files_unchanged':supervisor.verify_protected(OUT),'publication':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
        report.update(numerical_ranking_status='ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED',
            continuous_global_optimality=False,scientific_implementation_changed=False,no_interpolation=True,
            frozen_spec_discrepancy='PREEXISTING_UNCHANGED',baseline_MB_count=145)
        io.save_json(OUT/'run_report.json',report)
        io.save_json(OUT/'sleep_prevention_final_receipt.json',lease.receipt)
        io.save_json(OUT/'input_manifest_after.json',{n:io.digest(ROOT/n) for n in manifest})
        (OUT/'run_report.md').write_text('# Batch3 exact expansion\n\n'+json.dumps({k:report[k] for k in ('status','successful_probes','timeout_probes','budget_session_wall_seconds','total_CPU_seconds','postprocess','error')},indent=2)+'\nOriginal science/settings/precision/quadrature/MI/Holevo/ALT_OPT unchanged. No interpolation. Finite catalog ranking only.\n',encoding='utf-8')
        print(json.dumps({k:report[k] for k in ('status','successful_probes','timeout_probes','budget_session_wall_seconds','postprocess','error')}),flush=True)
        render_report(report)
    return 1 if error else 0


if __name__=='__main__':
    raise SystemExit(main())
