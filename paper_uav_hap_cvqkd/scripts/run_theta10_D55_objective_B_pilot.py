"""One approved B2 source attempt: original API, existing Sleep/Job supervisor."""
import time
CONTROLLER_ORIGIN = time.monotonic()  # Includes project-import/preflight time.
import datetime
ORIGIN_UTC = datetime.datetime.now(datetime.timezone.utc)
import argparse
from contextlib import ExitStack
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_theta10_D55_ao_scientific_results as saved
from scripts import exact_cache_provenance as provenance
from scripts import windows_sleep_safe_supervision as safe
from scripts import prepare_theta10_D55_objective_B as preparation
from src.cvqkd import gram_moments
import torch

BASE = preparation.OUT
OUT = BASE / 'b2_A'
NU, VA = .165, 5.49375
KEY = 'db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59'
TOTAL_SECONDS, PROBE_SECONDS, RESERVE_SECONDS = 4500., 3600., 900.
DIRS = (*saved.DIRS, ROOT / 'results/exact_mb_asymptotic/exact_source_cache', OUT / 'exact_source_cache')


def save(name, data):
    # Single-writer, distinct stage files; no concurrent observer snapshots.
    (OUT / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(name, rows):
    with patch.object(saved, 'OUT', OUT):
        saved.write_csv(name, rows)


def remaining_probe_seconds(now, deadline):
    return max(0., min(PROBE_SECONDS, deadline - now - RESERVE_SECONDS))


def alive(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes, kernel.OpenProcess.restype = [w.DWORD, w.BOOL, w.DWORD], w.HANDLE
    kernel.WaitForSingleObject.argtypes, kernel.WaitForSingleObject.restype = [w.HANDLE, w.DWORD], w.DWORD
    kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [w.HANDLE], w.BOOL
    handle = kernel.OpenProcess(0x100000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error in (87, 1168):
            return False
        raise OSError(error, 'Cannot verify child cleanup')
    try:
        result = kernel.WaitForSingleObject(handle, 0)
        if result not in (0, 258):
            raise OSError(ctypes.get_last_error(), 'Cannot query child state')
        return result == 258
    finally:
        kernel.CloseHandle(handle)


def supervised(phase, seconds):
    command = [sys.executable, '-B', '-X', 'utf8', '-u', str(Path(__file__).resolve()), '--child', phase]
    with (OUT / (phase + '.log')).open('w', encoding='utf-8') as log:
        receipt = safe.supervised_process(command, seconds, log)
    save(phase + '_supervision.json', receipt)
    assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
    assert receipt['sleep_prevention']['active_verified'] and receipt['sleep_prevention']['released_verified']
    assert receipt['supervision'] == 'ABSOLUTE_DEADLINE_AND_WINDOWS_JOB'
    assert receipt.get('cpu_measurement') == 'WINDOWS_JOB_BASIC_ACCOUNTING'
    reason = receipt['power_watch']['abort_reason']
    assert reason in (None, 'ABSOLUTE_DEADLINE'), f'Unsafe {phase}: {reason}'
    return receipt


def source_child():
    authorization = saved.read(OUT / 'execution_authorization.json')
    started = saved.read(OUT / 'source_attempt_started.json')
    assert authorization['maximum_attempts'] == started['attempt_number'] == 1
    assert authorization['source_cache_key'] == KEY
    verify_protected()
    torch.set_num_threads(1)  # Original diagnostic worker policy, not AP precision.
    config = saved.source.unconstrained_config()
    evaluator = saved.ao.ExactMBEvaluator(config, {'T_eff': 0., 'epsilon_base': .0186, 'c_phi': 0.}, OUT,
        source_cache_dir=OUT / 'exact_source_cache', allow_legacy_exact_import=False)
    ensemble = saved.source.make_ensemble(config, 'MB', NU, VA)
    identity = evaluator._source_identity(ensemble, NU, VA)
    plan = saved.rows(BASE / 'targeted_exact_probe_plan.csv')[0]
    assert saved.ao.json_hash(identity) == KEY and identity == json.loads(plan['original_source_identity'])
    clock, cpu = time.monotonic(), time.process_time()
    try:
        # Unmodified API: no subprocess monkeypatch, profiling, or observer.
        moment = evaluator.source_moments(ensemble, NU, VA)
        verification = provenance.verify_source_payload(moment, provenance.source_settings(config))
        assert moment['cache_key'] == KEY and moment['support_size'] == 256
        result = {'status': 'COMPLETED_EXACT', 'nu_raw': NU, 'V_A': VA, 'cache_key': KEY,
            'C': moment['C'], 'w': moment['w'], 'source_path': str((OUT / 'exact_source_cache' / (KEY + '.json')).relative_to(ROOT)),
            'provenance': verification, 'source_moment_route': moment['source_moment_route']}
    except Exception as error:
        result = {'status': 'TIMEOUT_INTERNAL_FALLBACK' if 'timeout' in str(error).lower() else 'NUMERICAL_FAILURE',
            'error': f'{type(error).__name__}: {error}', 'cache_key': KEY, 'nu_raw': NU, 'V_A': VA}
    result.update(wall_seconds=time.monotonic() - clock, source_parent_cpu_seconds=time.process_time() - cpu,
        profiler_used=False, observer_used=False, source_method_modified=False)
    save('source_result.json', result)
    print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'COMPLETED_EXACT' else 2


def verify_protected():
    protected = saved.read(OUT / 'protected_input_manifest.json')
    assert all(saved.sweep.sha256(ROOT / n) == h for n, h in protected.items()), 'Protected input drift'
    return len(protected)


def postprocess_child():
    torch.set_num_threads(1)
    verify_protected()
    payload = saved.read(OUT / 'exact_source_cache' / (KEY + '.json'))
    config = saved.source.unconstrained_config()
    provenance.verify_source_payload(payload, provenance.source_settings(config))
    assert payload['cache_key'] == KEY
    checkpoint = saved.read(saved.BASE / 'objective_checkpoint.json')
    old = {float(r['L_km']): r for r in saved.rows(saved.OUT / 'optimized_skr_26_distances.csv')}
    searches, runs, selected, comparison, objectives, coordinates, catalogs = [], [], [], [], [], [], []
    metadata = {}
    warm = None
    original_search = saved.ao.adaptive_maximize_1d

    def record(**kwargs):
        result = original_search(**kwargs)
        searches.append({**result, **metadata})
        return result

    with ExitStack() as guards:
        guards.enter_context(patch.object(saved.ao.ExactMBEvaluator, 'source_moments', preparation.forbidden))
        guards.enter_context(patch.object(gram_moments, '_fallback', preparation.forbidden))
        guards.enter_context(patch.object(saved.sweep, 'adaptive_maximize_1d', record))
        for distance in saved.sweep.DISTANCES_KM:
            previous = checkpoint[str(distance)]
            channel = previous['identity']['identity']['channel']
            obj = saved.ao.ExactObjective(config, channel, OUT, allow_new_source=False, source_cache_dirs=DIRS)
            assert obj.restore_objective_rows(previous['rows'], previous['identity']) == 147
            for r in previous['rows']:
                obj.register_catalog(r['nu_raw'], r['V_A'])
            # Baseline147 + the preexisting B1-discovered source + this one new source.
            extra = [obj(.25, 2.), obj(NU, VA)]
            assert len(obj.rows) == len(obj.catalog) == 149
            objectives.extend(extra)
            catalogs.append({'L_km': distance, 'identity': obj.objective_identity, 'rows': list(obj.rows.values())})
            rank = sorted(obj.rows.values(), key=lambda r: r['SKR'], reverse=True)
            starts = [(f'nu_{n:g}', n, None) for n in saved.sweep.BASE_STARTS]
            if warm:
                starts.append(('warm_previous_distance', *warm))
            local = []
            for sid, nu, va in starts:
                metadata.update(L_km=distance, start_id=sid, role='ITERATION')
                run = saved.sweep.run_single_distance_ao(distance_km=distance, start_id=sid, start_nu=nu,
                    start_va=va, objective=obj, max_iterations=6)
                assert not run['warnings'] and run['final'] is not None
                local.append({'L_km': distance, **run})
            chosen = max(local, key=lambda r: r['final']['SKR'])
            final = chosen['final']
            warm = (final['nu_raw'], final['V_A'])
            metadata.update(L_km=distance, start_id=chosen['start_id'], role='SELECTED_FINAL')
            checks = [record(variable=v, fixed=f, values=obj.catalog_values(v, f), objective=obj)
                for v, f in (('V_A', warm[0]), ('nu_raw', warm[1]))]
            for s in checks:
                coordinates.append(saved.audit.diagnostic({**s, 'L_km': distance}, list(obj.rows.values())))
            match = saved.pair(*warm) == saved.pair(rank[0]['nu_raw'], rank[0]['V_A']) and final['SKR'] == rank[0]['SKR']
            selected.append({'L_km': distance, 'nu_raw': warm[0], 'V_A': warm[1], 'I_AB': final['I_AB'],
                'beta_I_AB': final['beta_I_AB'], 'chi_BE': final['chi_BE'], 'best_SKR': final['SKR'],
                'AO_status': chosen['status'], 'selected_start': chosen['start_id'], 'catalog_maximum': rank[0]['SKR'],
                'AO_matches_catalog': match, 'catalog_size': 149,
                'coordinate_complete': all(saved.ao.coordinate_search_complete(s) for s in checks),
                'source_cache_key': final['source_cache_key'], 'scope': 'FRESH_ORIGINAL_AO_FINITE_CATALOG_ONLY'})
            comparison.append({'L_km': distance, 'old_nu_raw': old[distance]['best_nu_raw'], 'old_V_A': old[distance]['best_V_A'],
                'old_K': old[distance]['best_SKR'], 'new_nu_raw': warm[0], 'new_V_A': warm[1], 'new_K': final['SKR'],
                'delta_K': final['SKR'] - float(old[distance]['best_SKR']), 'probe_K': extra[1]['SKR'],
                'preexisting_025_2_K': extra[0]['SKR'], 'AO_matches_catalog': match,
                'gain_accuracy': 'UNRESOLVED_TOTAL_OBJECTIVE_ERROR_NOT_BOUNDED'})
            runs.extend(local)
            write_csv('optimized_skr_26_distances.csv', selected)
            write_csv('old_vs_new_skr.csv', comparison)
            save('objective_checkpoint.json', catalogs)
            print(f'Postprocess L={distance}: K={final["SKR"]!r}, pair={warm}, catalog match={match}', flush=True)
    save('cache_only_runs.json', runs)
    save('cache_only_searches.json', searches)
    save('new_pair_26distance_objectives.json', objectives)
    write_csv('reference_ao_coordinate_search.csv', [r for r in coordinates if r['L_km'] == saved.REF])
    write_csv('coordinate_search_status.csv', coordinates)
    write_csv('ao_iteration_history.csv', [it for r in runs for it in r['iterations']])
    write_csv('ao_multistart_validation.csv', [{'L_km': r['L_km'], 'start_id': r['start_id'],
        'nu_raw': r['final']['nu_raw'], 'V_A': r['final']['V_A'], 'K': r['final']['SKR'],
        'status': r['status'], 'iterations': len(r['iterations'])} for r in runs])
    aligned, _ = saved.audit.align_searches(runs, searches)
    report = {'status': 'POSTPROCESS_COMPLETE_FINITE_CATALOG_ONLY', 'available_MB_sources': 149,
        'baseline_sources': 147, 'preexisting_source_outside_baseline': 1, 'new_AP_sources': 1,
        'distances': len(selected), 'starts': len(runs), 'outer_iterations': sum(len(r['iterations']) for r in runs),
        'catalog_matches': sum(r['AO_matches_catalog'] for r in selected),
        'coordinate_searches': len(aligned), 'completed_coordinate_searches': sum(saved.ao.coordinate_search_complete(s) for s in aligned),
        'distances_improved': [r['L_km'] for r in comparison if r['delta_K'] > 0],
        'reference': next(r for r in selected if r['L_km'] == saved.REF),
        'next_reference_requests': [r['missing_exact_points'] for r in coordinates if r['L_km'] == saved.REF],
        'continuous_or_global_optimum_certified': False, 'protected_count': verify_protected()}
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
        raise SystemExit('One-attempt output exists: no overwrite or automatic retry')
    OUT.mkdir()
    deadline = CONTROLLER_ORIGIN + TOTAL_SECONDS
    authorization = {'status': 'APPROVED_ONE_ATTEMPT_PENDING_PREFLIGHT', 'user_approval': 'chạy',
        'approval_scope': 'Accepted B1 proposal: one exact(.165,5.49375),75min total/60min source/15min reserve',
        'controller_pid': os.getpid(), 'controller_origin_UTC': ORIGIN_UTC.isoformat(),
        'deadline_UTC': (ORIGIN_UTC + datetime.timedelta(seconds=TOTAL_SECONDS)).isoformat(),
        'origin_monotonic': CONTROLLER_ORIGIN, 'deadline_monotonic': deadline,
        'total_seconds': TOTAL_SECONDS, 'per_probe_seconds': PROBE_SECONDS, 'reserve_seconds': RESERVE_SECONDS,
        'maximum_attempts': 1, 'nu_raw_hex': NU.hex(), 'V_A_hex': VA.hex(), 'source_cache_key': KEY,
        'old_budget_reused': False, 'profiler_or_observer_allowed': False, 'scientific_method_or_AO_modified': False}
    save('execution_authorization.json', authorization)
    protected = saved.read(BASE / 'objective_B_verification.json')['protected_input_hashes']
    for p in BASE.iterdir():
        if p.is_file():
            protected[p.relative_to(ROOT).as_posix()] = saved.sweep.sha256(p)
    protected[str(Path(__file__).relative_to(ROOT)).replace('\\', '/')] = saved.sweep.sha256(Path(__file__))
    for rel in ('scripts/windows_sleep_safe_supervision.py', 'scripts/run_theta10_D55_alt_opt_convergence_validation.py',
                'scripts/run_theta10_D55_alt_opt_closure_continuation.py'):
        protected[rel] = saved.sweep.sha256(ROOT / rel)
    save('protected_input_manifest.json', protected)
    lease = safe.AwakeOnAC()
    status, error, source_receipt, post_receipt = 'PREFLIGHT_FAILED_NO_AP', None, None, None
    attempts = 0
    try:
        verify_protected()
        assert (saved.ao.MAX_AO_ITERATIONS, saved.ao.K_TOLERANCE, saved.ao.PARAMETER_TOLERANCE,
                saved.ao.MAX_REFINEMENT_STAGES) == (6, 1e-8, 1e-6, 4)
        plan = saved.rows(BASE / 'targeted_exact_probe_plan.csv')[0]
        assert saved.pair(plan['nu_raw'], plan['V_A']) == saved.pair(NU, VA)
        assert plan['compatible_current_cache_key'] == KEY
        assert preparation.source.candidate_from_payload(preparation.source.unconstrained_config(),
            preparation.scan_caches(preparation.source.unconstrained_config())[0], 'MB', NU, VA) is None
        with lease:
            samples = []
            for _ in range(3):
                samples.append(lease.power.read())
                time.sleep(.25)
            assert all(safe.safe_power(p) for p in samples)
            dummy = supervised('dummy', 12.)
            assert dummy['deadline_exceeded'] and dummy['returncode'] != 0
            pids = saved.read(OUT / 'dummy_pids.json')
            time.sleep(.2)
            assert all(not alive(pid) for pid in pids.values()), 'Dummy tree escaped Job cleanup; no AP permitted'
            assert dummy['accounted_processes'] >= 2
            longest_path = max(len(str(OUT / 'exact_source_cache' / (KEY + suffix))) for suffix in ('.json', '.json.tmp'))
            assert longest_path <= 247, 'Generated source path exceeds validated Windows length'
            save('preflight.json', {'status': 'CURRENTLY_VERIFIED_PASS', 'AC_samples': samples,
                'outer_sleep_lease': lease.receipt, 'dummy_receipt': dummy, 'dummy_pids': pids,
                'dummy_tree_terminated': True, 'source_identity_verified': KEY,
                'maximum_generated_path_length': longest_path})
            limit = remaining_probe_seconds(time.monotonic(), deadline)
            assert limit > 30, 'No safe source time remains after preflight'
            attempts = 1
            status = 'SOURCE_RUNNING'
            save('source_attempt_started.json', {'attempt_number': 1, 'nu_raw': NU, 'V_A': VA,
                'source_cache_key': KEY, 'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'probe_wall_limit_seconds': limit, 'actual_source_deadline_monotonic': time.monotonic() + limit})
            print(f'SOURCE_STARTED {KEY}; limit={limit:.3f}s; total budget=4500s; reserve=900s; original unprofiled worker', flush=True)
            source_receipt = supervised('source', limit)
            verify_protected()
            result = saved.read(OUT / 'source_result.json') if (OUT / 'source_result.json').exists() else {}
            if source_receipt['deadline_exceeded']:
                status = 'TIMEOUT_EXTERNAL_JOB_STOPPED'
            elif result.get('status') == 'COMPLETED_EXACT' and source_receipt['returncode'] == 0:
                provenance.verify_source_payload(saved.read(OUT / 'exact_source_cache' / (KEY + '.json')),
                    provenance.source_settings(saved.source.unconstrained_config()))
                status = 'SOURCE_COMPLETED_POSTPROCESS_RUNNING'
            else:
                status = result.get('status', 'SOURCE_PROCESS_FAILURE')
            write_csv('source_execution_ledger.csv', [{'attempt': 1, 'status': status, 'nu_raw': NU, 'V_A': VA,
                'cache_key': KEY, 'wall_seconds': source_receipt['measured_wall_seconds_including_cleanup'],
                'CPU_seconds': source_receipt.get('aggregate_cpu_seconds'), 'retry': False}])
            write_csv('new_exact_sources.csv', [{k: result.get(k, '') for k in ('status', 'nu_raw', 'V_A', 'C', 'w', 'cache_key', 'source_path')}])
            if status == 'SOURCE_COMPLETED_POSTPROCESS_RUNNING':
                save('source_checkpoint.json', result)
                post_limit = deadline - time.monotonic() - 30.
                assert post_limit > 10
                post_receipt = supervised('postprocess', post_limit)
                assert post_receipt['returncode'] == 0 and not post_receipt['deadline_exceeded']
                status = 'COMPLETED_ONE_SOURCE_AND_ORIGINAL_AO'
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        status = 'ABORTED_UNSAFE_OR_NUMERICAL_FAILURE' if attempts else 'PREFLIGHT_FAILED_NO_AP'
    finally:
        # Existing supervised_process closes every Job before returning/raising.
        if source_receipt is None and (OUT / 'source_supervision.json').exists():
            source_receipt = saved.read(OUT / 'source_supervision.json')
        if post_receipt is None and (OUT / 'postprocess_supervision.json').exists():
            post_receipt = saved.read(OUT / 'postprocess_supervision.json')
        try:
            count = verify_protected()
        except Exception as drift:
            count = 'FAILED_PROVENANCE_DRIFT'
            status = 'PROVENANCE_FAILURE_STOPPED'
            error = str(drift)
        elapsed = time.monotonic() - CONTROLLER_ORIGIN
        if elapsed > TOTAL_SECONDS:
            status = 'FAILED_TOTAL_WALL_OVERRUN'
        report = {'status': status, 'error': error, 'attempts': attempts, 'retry': False,
            'total_wall_seconds': elapsed, 'controller_CPU_seconds': time.process_time(),
            'source_supervision': source_receipt, 'postprocess_supervision': post_receipt,
            'outer_sleep_lease': lease.receipt, 'protected_count': count,
            'within_total_budget': elapsed <= TOTAL_SECONDS, 'profiler_or_observer_used': False,
            'frozen_historical_discrepancy': 'PREEXISTING_UNCHANGED', 'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
            'continuous_or_global_optimum_certified': False, 'no_additional_AP_attempts': True}
        save('final_report.json', report)
        (OUT / 'run_report.md').write_text('# One-attempt Objective B2 pilot\n\n' + json.dumps(report, indent=2) +
            '\n\nNo continuous/global certificate. Old outputs and Objective A remain untouched. '
            'If postprocessing succeeded, read postprocess_report.json for original26-distance AO and actual remaining coordinate requests.\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    return 0 if status in ('COMPLETED_ONE_SOURCE_AND_ORIGINAL_AO', 'TIMEOUT_EXTERNAL_JOB_STOPPED', 'TIMEOUT_INTERNAL_FALLBACK') else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', choices=('source', 'postprocess', 'dummy'))
    args = parser.parse_args()
    raise SystemExit({'source': source_child, 'postprocess': postprocess_child, 'dummy': dummy_child}[args.child]() if args.child else main())
