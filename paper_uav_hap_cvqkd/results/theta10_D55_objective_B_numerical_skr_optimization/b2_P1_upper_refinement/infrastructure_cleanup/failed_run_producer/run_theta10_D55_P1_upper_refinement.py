"""One approved original-API upper P1 probe; no retries or extra AP."""
import time
ORIGIN = time.monotonic()  # Includes imports/native preflight in total budget.
import datetime
ORIGIN_UTC = datetime.datetime.now(datetime.timezone.utc)
import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_theta10_D55_P1_upper_refinement as prep

saved, prior = prep.saved, prep.prior
NU, VA, KEY = prep.NU, prep.VA, prep.KEY
OUT = prep.OUT / 'approved_run'
CACHE = prep.OUT / 'exact_source_cache'  # Keep validated Windows path length.
DIRS = (*prior.DIRS, CACHE)
TOTAL, SUPERVISOR_MAX, RESERVE = 7200., 5400., 1800.


def save(name, data):
    (OUT / name).write_text(prep.storage.checked_json(data), encoding='utf-8')


def csv(name, data):
    with patch.object(saved, 'OUT', OUT):
        saved.write_csv(name, data)


def probe_limit(now, deadline):
    return max(0., min(SUPERVISOR_MAX, deadline - now - RESERVE))


def verify():
    manifest = saved.read(OUT / 'protected_input_manifest.json')
    assert all(saved.sweep.sha256(ROOT / n) == h for n, h in manifest.items()), 'Protected input drift'
    return len(manifest)


def supervise(phase, limit):
    command = [sys.executable, '-B', '-X', 'utf8', '-u', str(Path(__file__).resolve()), '--child', phase]
    with (OUT / (phase + '.log')).open('w', encoding='utf-8') as log:
        receipt = prior.safe.supervised_process(command, limit, log)
    save(phase + '_supervision.json', receipt)
    assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
    assert receipt['sleep_prevention']['active_verified'] and receipt['sleep_prevention']['released_verified']
    assert receipt['supervision'] == 'ABSOLUTE_DEADLINE_AND_WINDOWS_JOB'
    assert receipt.get('cpu_measurement') == 'WINDOWS_JOB_BASIC_ACCOUNTING'
    assert receipt['power_watch']['abort_reason'] in (None, 'ABSOLUTE_DEADLINE'), receipt['power_watch']
    return receipt


def source_child():
    verify()
    authorization = saved.read(OUT / 'execution_authorization.json')
    assert authorization['maximum_attempts'] == saved.read(OUT / 'source_attempt_started.json')['attempt_number'] == 1
    assert authorization['source_cache_key'] == KEY
    assert not (CACHE / (KEY + '.json')).exists(), 'Source already exists; never regenerate'
    prior.torch.set_num_threads(1)
    config = saved.source.unconstrained_config()
    evaluator = saved.ao.ExactMBEvaluator(config, {'T_eff': 0., 'epsilon_base': .0186, 'c_phi': 0.}, OUT,
        source_cache_dir=CACHE, allow_legacy_exact_import=False)
    ensemble = saved.source.make_ensemble(config, 'MB', NU, VA)
    identity = evaluator._source_identity(ensemble, NU, VA)
    assert identity == saved.read(prep.OUT / 'confirmed_candidate.json')['original_source_identity']
    assert saved.ao.json_hash(identity) == KEY
    start = time.monotonic()
    try:
        # Original API/fallback/internal3600s timeout/precision context unchanged.
        moment = evaluator.source_moments(ensemble, NU, VA)
        provenance = prep.provenance.verify_source_payload(moment, prep.provenance.source_settings(config))
        assert moment['cache_key'] == KEY and moment['support_size'] == 256
        result = {'status': 'COMPLETED_EXACT', 'C': moment['C'], 'w': moment['w'],
            'source_moment_route': moment['source_moment_route'], 'provenance': provenance,
            'source_path': (CACHE / (KEY + '.json')).relative_to(ROOT).as_posix()}
    except Exception as error:
        result = {'status': 'TIMEOUT_INTERNAL_EVALUATOR' if 'timeout' in str(error).lower() else 'SOURCE_EVALUATOR_OR_PROVENANCE_FAILURE',
            'error': f'{type(error).__name__}: {error}'}
    result.update(nu_raw=NU, V_A=VA, cache_key=KEY, source_API_wall_seconds=time.monotonic() - start,
        original_internal_timeout_seconds=3600, source_method_modified=False, profiler_or_observer_used=False)
    save('source_result.json', result)
    print(prep.storage.checked_json(result), flush=True)
    return 0 if result['status'] == 'COMPLETED_EXACT' else 2


def postprocess_child():
    verify()
    prior.torch.set_num_threads(1)
    config = saved.source.unconstrained_config()
    payload = saved.read(CACHE / (KEY + '.json'))
    prep.provenance.verify_source_payload(payload, prep.provenance.source_settings(config))
    assert payload['cache_key'] == KEY
    previous = {e['L_km']: e for e in saved.read(prep.INPUT / 'objective_checkpoint.json')}
    old = {float(r['L_km']): r for r in saved.rows(prep.INPUT / 'optimized_skr_26_distances.csv')}
    runs, searches, catalogs, selected, comparisons, objectives, coords = [], [], [], [], [], [], []
    metadata, warm = {}, None
    original_search = saved.ao.adaptive_maximize_1d

    def record(**kwargs):
        result = original_search(**kwargs)
        searches.append({**result, **metadata})
        return result

    with ExitStack() as guards:
        for obj, name in ((saved.ao.ExactMBEvaluator, 'source_moments'), (prior.gram_moments, '_fallback'), (saved.sweep, 'make_channel')):
            guards.enter_context(patch.object(obj, name, prior.preparation.forbidden))
        guards.enter_context(patch.object(saved.sweep, 'adaptive_maximize_1d', record))
        for distance in saved.sweep.DISTANCES_KM:
            entry = previous[distance]
            objective = saved.ao.ExactObjective(config, entry['identity']['identity']['channel'], OUT,
                allow_new_source=False, source_cache_dirs=DIRS)
            assert objective.restore_objective_rows(entry['rows'], entry['identity']) == 149
            for row in entry['rows']:
                objective.register_catalog(row['nu_raw'], row['V_A'])
            new = objective(NU, VA)  # One new original SKR per distance, no AP.
            assert len(objective.rows) == len(objective.catalog) == 150
            objectives.append(new)
            rank = sorted(objective.rows.values(), key=lambda r: r['SKR'], reverse=True)
            starts = [(f'nu_{n:g}', n, None) for n in saved.sweep.BASE_STARTS]
            if warm is not None:
                starts.append(('warm_previous_distance', *warm))
            local = []
            for start_id, nu, va in starts:
                metadata.update(L_km=distance, start_id=start_id, role='ITERATION')
                run = saved.sweep.run_single_distance_ao(distance_km=distance, start_id=start_id,
                    start_nu=nu, start_va=va, objective=objective, max_iterations=6)
                assert not run['warnings'] and run['final'] is not None
                local.append({'L_km': distance, **run})
            chosen = max(local, key=lambda r: r['final']['SKR'])
            best = chosen['final']
            warm = (best['nu_raw'], best['V_A'])
            metadata.update(L_km=distance, start_id=chosen['start_id'], role='SELECTED_FINAL')
            checks = [record(variable=v, fixed=f, values=objective.catalog_values(v, f), objective=objective)
                for v, f in (('V_A', warm[0]), ('nu_raw', warm[1]))]
            coords.extend({**saved.audit.diagnostic({**s, 'L_km': distance}, list(objective.rows.values())),
                'candidate_history': s['history']} for s in checks)
            match = saved.pair(*warm) == saved.pair(rank[0]['nu_raw'], rank[0]['V_A']) and best['SKR'] == rank[0]['SKR']
            selected.append({'L_km': distance, 'nu_raw': warm[0], 'V_A': warm[1], 'I_AB': best['I_AB'],
                'beta_I_AB': best['beta_I_AB'], 'chi_BE': best['chi_BE'], 'best_SKR': best['SKR'],
                'AO_status': chosen['status'], 'selected_start': chosen['start_id'], 'catalog_maximum': rank[0]['SKR'],
                'AO_matches_catalog': match, 'catalog_size': 150, 'coordinate_complete': all(saved.ao.coordinate_search_complete(s) for s in checks),
                'source_cache_key': best['source_cache_key'], 'scope': 'GENUINE_ORIGINAL_AO_FINITE_CATALOG_ONLY'})
            comparisons.append({'L_km': distance, 'old_nu_raw': old[distance]['nu_raw'], 'old_V_A': old[distance]['V_A'],
                'old_K': old[distance]['best_SKR'], 'new_nu_raw': warm[0], 'new_V_A': warm[1], 'new_K': best['SKR'],
                'delta_K': best['SKR'] - float(old[distance]['best_SKR']), 'new_probe_K': new['SKR'],
                'AO_matches_catalog': match, 'total_K_discrimination_accuracy': 'NOT_ESTABLISHED'})
            runs.extend(local)
            catalogs.append({'L_km': distance, 'identity': objective.objective_identity, 'rows': list(objective.rows.values())})
            csv('new_exact_skr_26_distances.csv', objectives)
            csv('optimized_skr_26_distances.csv', selected)
            csv('old_vs_new_skr.csv', comparisons)
            save('objective_checkpoint.json', catalogs)
            print(f'L={distance}; K={best["SKR"]!r}; pair={warm}; catalog_match={match}', flush=True)
    save('cache_only_runs.json', runs)
    save('cache_only_searches.json', searches)
    csv('coordinate_search_status.csv', coords)
    csv('reference_P1_refinement.csv', [r for r in coords if r['L_km'] == saved.REF and r['coordinate'] == 'V_A'])
    csv('ao_iteration_history.csv', [{'L_km': r['L_km'], 'start_id': r['start_id'], **it} for r in runs for it in r['iterations']])
    csv('ao_multistart_recheck.csv', [{'L_km': r['L_km'], 'start_id': r['start_id'], 'nu_raw': r['final']['nu_raw'],
        'V_A': r['final']['V_A'], 'K': r['final']['SKR'], 'status': r['status'], 'iterations': len(r['iterations'])} for r in runs])
    aligned, _ = saved.audit.align_searches(runs, searches)
    report = {'status': 'COMPLETED_ORIGINAL_26DISTANCE_AO_FINITE_CATALOG_ONLY', 'baseline_MB_sources': 149,
        'available_MB_sources': 150, 'new_AP_sources': 1, 'fresh_SKR_evaluations': len(objectives),
        'distances': len(selected), 'starts': len(runs), 'iterations': sum(len(r['iterations']) for r in runs),
        'catalog_matches': sum(r['AO_matches_catalog'] for r in selected), 'coordinate_searches': len(aligned),
        'coordinate_closures': sum(saved.ao.coordinate_search_complete(s) for s in aligned),
        'improved_distances': [r['L_km'] for r in comparisons if r['delta_K'] > 0],
        'reference': next(r for r in selected if r['L_km'] == saved.REF),
        'reference_new_probe': next(r for r in objectives if r['L_km'] == saved.REF),
        'reference_coordinates': [r for r in coords if r['L_km'] == saved.REF],
        'at_22_km': next(r for r in selected if r['L_km'] == 22.), 'protected_count': verify(),
        'continuous_or_global_optimum_certified': False, 'extra_AP_attempts': 0}
    save('postprocess_report.json', report)
    return 0


def dummy_child():
    child = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(30)'],
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    save('dummy_pids.json', {'root': os.getpid(), 'child': child.pid})
    time.sleep(30)
    return 0


def main():
    if OUT.exists():
        raise SystemExit('One-attempt output exists; no overwrite/retry')
    OUT.mkdir()
    deadline = ORIGIN + TOTAL
    protected = saved.read(prep.OUT / 'protected_input_manifest.json')
    for path in prep.OUT.iterdir():
        if path.is_file():
            protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    for path in (Path(__file__), ROOT / 'tests/test_P1_upper_refinement_execution.py'):
        protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    save('protected_input_manifest.json', protected)
    save('execution_authorization.json', {'status': 'APPROVED_ONE_AP_ATTEMPT_PENDING_NATIVE_PREFLIGHT',
        'controller_pid': os.getpid(), 'controller_origin_UTC': ORIGIN_UTC.isoformat(),
        'deadline_UTC': (ORIGIN_UTC + datetime.timedelta(seconds=TOTAL)).isoformat(),
        'origin_monotonic': ORIGIN, 'deadline_monotonic': deadline, 'total_seconds': TOTAL,
        'supervisor_ceiling_seconds': SUPERVISOR_MAX, 'reserve_seconds': RESERVE,
        'original_internal_evaluator_timeout_seconds': 3600, 'maximum_attempts': 1,
        'nu_raw_hex': NU.hex(), 'V_A_hex': VA.hex(), 'source_cache_key': KEY,
        'retry_allowed': False, 'other_AP_allowed': False, 'old_budget_reused': False,
        'scientific_method_or_defaults_changed': False})
    lease = prior.safe.AwakeOnAC()
    status, error, attempts = 'PREFLIGHT_FAILED_NO_AP', None, 0
    try:
        verify()
        config = saved.source.unconstrained_config()
        bank, _, reconciliation = prep.reconcile(config)
        assert saved.pair(NU, VA) not in bank and not (CACHE / (KEY + '.json')).exists()
        assert (saved.ao.MAX_AO_ITERATIONS, saved.ao.K_TOLERANCE, saved.ao.PARAMETER_TOLERANCE, saved.ao.MAX_REFINEMENT_STAGES) == (6, 1e-8, 1e-6, 4)
        with lease:
            samples = []
            for _ in range(3):
                samples.append(lease.power.read())
                time.sleep(.25)
            assert all(prior.safe.safe_power(s) for s in samples)
            dummy = supervise('dummy', 12.)
            assert dummy['deadline_exceeded'] and dummy['returncode'] != 0 and dummy['accounted_processes'] >= 2
            pids = saved.read(OUT / 'dummy_pids.json')
            assert all(not prior.alive(pid) for pid in pids.values()), 'Dummy tree escaped'
            longest = max(len(str(CACHE / (KEY + suffix))) for suffix in ('.json', '.json.tmp'))
            assert longest <= 247, 'Unsafe source path length'
            save('native_preflight.json', {'status': 'CURRENTLY_VERIFIED_PASS', 'AC_samples': samples,
                'Sleep_lease': lease.receipt, 'dummy_tree_stopped': True, 'dummy_pids': pids,
                'maximum_source_path_length': longest, 'source_reconciliation': reconciliation})
            limit = probe_limit(time.monotonic(), deadline)
            assert limit > 30
            attempts, status = 1, 'SOURCE_RUNNING'
            save('source_attempt_started.json', {'attempt_number': 1, 'nu_raw': NU, 'V_A': VA, 'cache_key': KEY,
                'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'supervisor_wall_seconds': limit,
                'original_internal_timeout_seconds': 3600, 'actual_source_deadline_monotonic': time.monotonic() + limit})
            print(f'ONE_SOURCE_STARTED; key={KEY}; supervisor={limit:.3f}s; internal timeout3600s UNCHANGED', flush=True)
            receipt = supervise('source', limit)
            verify()
            result = saved.read(OUT / 'source_result.json') if (OUT / 'source_result.json').exists() else {}
            if receipt['deadline_exceeded']:
                status = 'TIMEOUT_SUPERVISOR_WHOLE_JOB_STOPPED'
            elif receipt['returncode'] == 0 and result.get('status') == 'COMPLETED_EXACT':
                save('source_checkpoint.json', result)
                csv('new_exact_source_moments.csv', [{k: result[k] for k in ('nu_raw', 'V_A', 'cache_key', 'C', 'w', 'source_path', 'source_moment_route')}])
                status = 'SOURCE_SUCCEEDED_POSTPROCESS_RUNNING'
                post = supervise('postprocess', deadline - time.monotonic() - 90.)
                assert post['returncode'] == 0 and not post['deadline_exceeded'], 'Postprocess failed; preserve source'
                status = 'COMPLETED_SINGLE_SOURCE_AND_ORIGINAL_AO'
            else:
                status = result.get('status', 'SOURCE_PROCESS_FAILURE_STOPPED')
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        status = 'STOPPED_PREFLIGHT_FAILURE_NO_AP' if not attempts else 'STOPPED_SAFETY_OR_POSTPROCESS_FAILURE'
    finally:
        receipts = {phase: saved.read(OUT / (phase + '_supervision.json'))
            for phase in ('dummy', 'source', 'postprocess') if (OUT / (phase + '_supervision.json')).exists()}
        try:
            count = verify()
        except Exception as drift:
            status, error, count = 'PROVENANCE_FAILURE_STOPPED', str(drift), 'FAILED'
        elapsed = time.monotonic() - ORIGIN
        if elapsed > TOTAL:
            status = 'FAILED_TOTAL_WALL_OVERRUN'
        csv('execution_ledger.csv', [{'attempts': attempts, 'nu_raw': NU, 'V_A': VA, 'cache_key': KEY,
            'status': status, 'retry': False, 'controller_total_wall_seconds': elapsed,
            'source_Job_wall_seconds': receipts.get('source', {}).get('measured_wall_seconds_including_cleanup', ''),
            'source_Job_CPU_seconds': receipts.get('source', {}).get('aggregate_cpu_seconds', '')}])
        report = {'status': status, 'error': error, 'AP_attempts': attempts, 'retry': False,
            'total_wall_seconds': elapsed, 'within_total_budget': elapsed <= TOTAL,
            'controller_CPU_seconds': time.process_time(), 'supervision_receipts': receipts,
            'outer_Sleep_lease': lease.receipt, 'protected_count': count, 'scientific_methods_changed': False,
            'extra_AP_or_P2_attempts': 0, 'continuous_or_global_optimum_certified': False,
            'frozen_historical_discrepancy': 'PREEXISTING_UNCHANGED', 'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
        save('final_report.json', report)
        print(prep.storage.checked_json(report), flush=True)
    return 0 if status in ('COMPLETED_SINGLE_SOURCE_AND_ORIGINAL_AO', 'TIMEOUT_INTERNAL_EVALUATOR', 'TIMEOUT_SUPERVISOR_WHOLE_JOB_STOPPED') else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', choices=('source', 'postprocess', 'dummy'))
    args = parser.parse_args()
    raise SystemExit({'source': source_child, 'postprocess': postprocess_child, 'dummy': dummy_child}[args.child]() if args.child else main())
