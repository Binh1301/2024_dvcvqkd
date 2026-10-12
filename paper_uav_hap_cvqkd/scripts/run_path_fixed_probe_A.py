"""Fresh 150-minute path-repair/pilot budget, original scientific helpers only."""
import argparse
from contextlib import ExitStack
import csv
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation/observer_v2_recovery/path_fixed_probe_A'
sys.path.insert(0, str(ROOT))
from scripts import run_controlled_observer_v2_probe_A as pilot
from scripts import observer_v2_short_path_entry as entry
from scripts import observer_v2_recovery_entry as old_entry
from scripts import windows_sleep_safe_supervision as safe
from scripts import recover_theta10_D55_observer_v2 as recovery
from scripts.overnight_source_observer import atomic_json
from scripts.diagnose_theta10_D55_source_bottlenecks import read, digest, clean, rows
from scripts.exact_cache_provenance import json_hash, verify_source_payload, source_settings

KEY = pilot.KEY
REQUIRED = ('windows_path_root_cause.md', 'production_path_preflight.csv',
    'observer_v2_integration_tests.csv', 'execution_ledger.csv', 'profiling_manifest.json',
    'profiling_summary.csv', 'new_exact_source_moments.csv', 'new_exact_skr_26_distances.csv',
    'old_vs_new_optimum.csv', 'reference_P1_refinement.csv', 'ao_multistart_recheck.csv',
    'coordinate_search_status.csv', 'scientific_provenance_audit.md', 'run_report.md', 'run_report.json')


def save(name, data):
    atomic_json(OUT / name, clean(data))


def table(name, data):
    pilot.csv(name, data)


def bind():
    pilot.OUT = OUT
    pilot.DIRS = pilot.DIRS[:-1] + (OUT / 'exact_source_cache',)


def budget():
    return read(OUT / 'budget.json')


def remaining():
    b = budget()
    return min(b['origin_monotonic'] + 9000 - time.monotonic(),
               (datetime.fromisoformat(b['deadline_utc']) - datetime.now(timezone.utc)).total_seconds())


def prefix(stage, label):
    if not re.fullmatch(r'[a-z_]{1,24}', label):
        raise ValueError('Short ASCII observer name required')
    return stage / 'obs' / label


def path_operations(path, roots, margin=250, preserve_existing=False):
    """Actual create/flush/read/atomic replace/rename/hash/delete on this path."""
    path = Path(path).resolve()
    if not any(path.is_relative_to(r.resolve()) for r in roots):
        raise ValueError('Path escapes exact authorized new staging/output roots')
    temporary = path.with_suffix(path.suffix + '.tmp')
    renamed = path.with_suffix(path.suffix + '.move')
    longest = max(len(str(p)) for p in (path, temporary, renamed))
    if longest > margin:
        raise ValueError(f'Path exceeds conservative {margin}-character margin: {path}')
    if path.exists() and preserve_existing and not temporary.exists() and not renamed.exists():
        original = path.read_bytes();sha = digest(path)
        with temporary.open('xb') as stream:
            stream.write(original);stream.flush();os.fsync(stream.fileno())
        assert digest(temporary) == sha
        temporary.replace(path);path.replace(renamed)
        assert digest(renamed) == sha
        renamed.replace(path)
        assert digest(path) == sha
        return {'path': str(path), 'max_path_characters': longest,
                'creation_flush_read_atomic_replace_rename_hash_delete': 'PASS_PRESERVED_IDENTICAL_CURRENT_RUN_INPUT',
                'dummy_only': True}
    if any(p.exists() for p in (path, temporary, renamed)):
        raise FileExistsError('Preflight must never overwrite existing data: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write('DUMMY_PERSISTENCE_ONLY');stream.flush();os.fsync(stream.fileno())
    assert path.read_text() == 'DUMMY_PERSISTENCE_ONLY'
    dummy = {'dummy_only': True, 'scientific_output': False, 'source_computations': 0}
    atomic_json(path, dummy)
    assert read(path) == dummy and not temporary.exists()
    sha = digest(path)
    path.replace(renamed)
    assert digest(renamed) == sha
    renamed.unlink()
    assert not any(p.exists() for p in (path, temporary, renamed))
    return {'path': str(path), 'max_path_characters': longest,
            'creation_flush_read_atomic_replace_rename_hash_delete': 'PASS', 'dummy_only': True}


def prepare_paths(stage):
    labels = ('a', 'normal', 'disabled', 'instrumentation_failure', 'numerical_failure',
              'deadline', 'ac_loss', 'watchdog_gap')
    mapping = {str(prefix(stage, label).resolve()): {
        'AP_candidate': label == 'a', 'source_cache_key': KEY,
        'pair_hex': [n.hex() for n in pilot.PAIR],
        'scientific_run_identity': 'HAP_UAV_256_QAM_MB_EXACT_' + KEY * 6,
        'short_name': label} for label in labels}
    manifest = {'stage': str(stage), 'prefixes': mapping,
                'production_prefix': str(prefix(stage, 'a')),
                'fallback': str(stage / 'failure.json'),
                'original_cache_key_unchanged': KEY,
                'telemetry_separate_from_scientific_cache': True,
                'conservative_max_path_characters_including_suffix': 250}
    paths = [stage / 'paths.json', stage / 'failure.json', stage / 'manifest.json']
    for p in mapping:
        for suffix in ('_stage_snapshot.json', '_heartbeats.jsonl', '_worker_result.json',
                       '_snapshots.json', '.prof'):
            path = Path(p + suffix);paths += [path, OUT / 'staging_archive' / path.relative_to(stage)]
    paths += [OUT / name for name in REQUIRED]
    paths += [OUT / name for name in ('protected_input_manifest.json', 'execution_authorization.json',
        'path_manifest.json', 'source_result.json', 'source_numerical_diagnostics.json',
        'source_A.log', 'source_supervision.json', 'postprocess.log', 'postprocess_supervision.json',
        'regression_tests.json', 'readiness.json', 'transfer_verification.json', 'profiling_coverage_report.json',
        'objective_checkpoint.json', 'cache_only_runs.json', 'cache_only_searches.json',
        'coordinate_search_completion.csv', 'aligned_search_history.json', 'expanded_source_catalog.csv',
        'remaining_source_dependencies.csv', 'reference_P1_trace.csv', 'reference_P2_trace.csv',
        'reference_targeted_coordinate_searches.json', 'optimized_skr_26_distances.csv',
        'old_vs_new_optimization.csv', 'ao_multistart_history.csv', 'independent_catalog_verification.csv',
        'postprocess_report.json', 'exact_source_request.json', 'exact_source_identity.json', 'budget.json', 'execution_status.json',
        'source_parent_stdout.log', 'source_parent_stderr.log', 'profiling_stage_summary.csv')]
    paths += [OUT / 'exact_source_cache' / (KEY + '.json')]
    records = [path_operations(p, (stage, OUT), preserve_existing=p.name in ('protected_input_manifest.json', 'budget.json')) for p in paths]
    # Stage->archive transfer tested independently, not merely counted.
    fixture = stage / 'obs' / 'archive_control.json';atomic_json(fixture, {'dummy_only': True})
    target = OUT / 'staging_archive' / fixture.relative_to(stage)
    target.parent.mkdir(parents=True, exist_ok=True);shutil.copy2(fixture, target)
    assert digest(fixture) == digest(target)
    fixture.unlink();target.unlink()
    table('production_path_preflight.csv', records)
    atomic_json(stage / 'paths.json', manifest);save('path_manifest.json', manifest)
    os.environ['AO_OBSERVER_PATH_MANIFEST'] = str(stage / 'paths.json')
    return manifest


def native_tests(stage):
    # Original recovery safety harness, but NEW real short-path generator and
    # guarded v2 wrapper. Every dummy fixture remains quarantined.
    results = []
    class NativeOut:
        def __truediv__(self, label):
            return stage / 'obs' if label == 'dummy' else stage / 'obs' / label[6:] if label.startswith('dummy/') else stage / label
    (stage / 'obs').mkdir(exist_ok=True)
    with patch.object(recovery, 'OUT', NativeOut()), patch.object(recovery, 'entry', entry):
        for label, kw in [('a', {'duration': .8}), ('normal', {}), ('disabled', {'disabled': True}),
            ('instrumentation_failure', {'mode': 'instrumentation_failure'}),
            ('numerical_failure', {'mode': 'numerical_failure'}),
            ('deadline', {'duration': 30, 'wall': 3, 'inject': 'TIMEOUT'}),
            ('ac_loss', {'duration': 30, 'wall': 12, 'inject': 'AC'}),
            ('watchdog_gap', {'duration': 30, 'wall': 20, 'inject': 'WATCHDOG'})]:
            result = recovery.native_case(label, **kw);results.append(result)
            table('observer_v2_integration_tests.csv', results)
            print('Short production dummy ' + label + ': ' + result['actual'] + ' PASS', flush=True)
    # Preserve completed production-prefix dummy snapshots, then clear ONLY
    # those copied files before the one real attempt (no stale heartbeat).
    for path in (stage / 'obs').glob('a*'):
        target = OUT / 'dummy_production_path' / path.name
        target.parent.mkdir(exist_ok=True);shutil.copy2(path, target)
        assert digest(path) == digest(target)
        path.unlink()
    fallback = stage / 'failure.json'
    if fallback.exists():
        target = OUT / 'dummy_fallback.json';shutil.copy2(fallback, target)
        assert digest(fallback) == digest(target);fallback.unlink()
    return results


def source_child():
    """Original source_moments; only subprocess observer routing/path differs."""
    import torch
    torch.set_num_threads(1);bind();pilot.verify_inputs()
    auth = read(OUT / 'execution_authorization.json')
    stage = Path(budget()['stage']);p = prefix(stage, 'a')
    config, ensemble, evaluator, identity, request = pilot.request_and_identity()
    assert json_hash(request) == auth['request_sha256']
    real_run = subprocess.run
    def observed_run(command, *args, **kwargs):
        if isinstance(command, (list, tuple)) and len(command) > 1 and Path(command[1]).name == 'full_support_c4_worker.py':
            assert json_hash(json.loads(kwargs['input'])) == auth['request_sha256']
            command = [sys.executable, '-B', '-X', 'utf8', '-u', str(Path(entry.__file__)),
                       '--approved-ap', '--authorization', str(OUT / 'execution_authorization.json'),
                       '--prefix', str(p)]
            kwargs['timeout'] = max(1., auth['deadline_monotonic'] - time.monotonic() - 8)
        return real_run(command, *args, **kwargs)
    original = evaluator.source_evaluator
    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        save('source_numerical_diagnostics.json', list(result.diagnostics));return result
    evaluator.source_evaluator = capture
    start = time.monotonic();cpu = time.process_time()
    try:
        with patch.object(pilot.gram_moments.subprocess, 'run', observed_run):
            payload = evaluator.source_moments(ensemble, *pilot.PAIR)
        proof = verify_source_payload(payload, source_settings(config))
        result = {'status': 'SUCCESS', 'nu_raw': pilot.PAIR[0], 'V_A': pilot.PAIR[1],
                  'source_cache_key': KEY, 'C': payload['C'], 'w': payload['w'],
                  'source_path': str((OUT / 'exact_source_cache' / (KEY + '.json')).relative_to(ROOT)),
                  'provenance': proof, 'source_support_size': payload['support_size']}
    except Exception as exc:
        worker_path = Path(str(p) + '_worker_result.json')
        worker = read(worker_path) if worker_path.exists() else read(stage / 'failure.json') if (stage / 'failure.json').exists() else None
        status = worker['status'] if worker and worker['status'] in ('INSTRUMENTATION_FAILURE', 'NUMERICAL_FAILURE') else 'TIMEOUT' if isinstance(exc, subprocess.TimeoutExpired) else 'INSTRUMENTATION_FAILURE'
        result = {'status': status, 'error': repr(exc), 'worker_result': worker}
    result.update(parent_wall_seconds=time.monotonic() - start,
                  parent_CPU_seconds=time.process_time() - cpu, ended_utc=datetime.now(timezone.utc).isoformat())
    save('source_result.json', result);print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'SUCCESS' else 1


def transfer_stage(stage):
    records = []
    for path in sorted(stage.rglob('*')):
        if not path.is_file():
            continue
        target = OUT / 'staging_archive' / path.relative_to(stage)
        assert len(str(target.resolve())) <= 250
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError('Archive collision ' + str(target))
        shutil.copy2(path, target)
        assert digest(path) == digest(target)
        records.append({'staged_path': str(path), 'archive': str(target.relative_to(ROOT)),
                        'sha256': digest(path), 'verified': True})
    save('transfer_verification.json', records)
    # Delete only verified per-run copies; keep small staging directory as an
    # identity marker. Never recursively delete C:\aoobs or repository roots.
    for record in records:
        path = Path(record['staged_path']).resolve()
        assert path.is_relative_to(stage.resolve()) and digest(path) == record['sha256']
        path.unlink()
    return records


def finalize(ledger, stage):
    transfers = transfer_stage(stage)
    post = read(OUT / 'postprocess_report.json') if (OUT / 'postprocess_report.json').exists() else None
    result = read(OUT / 'source_result.json') if (OUT / 'source_result.json').exists() else None
    snapshot_path = OUT / 'staging_archive/obs/a_stage_snapshot.json'
    profile = {'coverage': 'NO_AP_OBSERVATIONS', 'bottleneck': 'BOTTLENECK_NOT_LOCALIZED', 'full_run_profile': False}
    if snapshot_path.exists() and ledger['AP_attempts']:
        snap = read(snapshot_path);groups = {}
        for r in snap['completed_stages']:
            g = groups.setdefault(r['name'], {'calls': 0, 'wall_exclusive': 0., 'CPU_exclusive': 0.})
            g['calls'] += int(r['completed_normally']);g['wall_exclusive'] += r['wall_seconds_exclusive'];g['CPU_exclusive'] += r['CPU_seconds_exclusive']
        complete = snap['finished'] and not snap['observer_error'] and all(r['completed_normally'] for r in snap['completed_stages'])
        profile = {'coverage': 'AP_MAIN_STAGE_INTERVAL_VALID' if complete else 'PARTIAL_AP_STAGE_INTERVAL',
            'snapshot_count': snap['snapshot_count'], 'covered_wall_seconds': snap['wall_seconds'],
            'covered_process_CPU_seconds': snap['process_cpu_seconds'], 'open_stages': snap['open_stages'],
            'full_run_profile': False, 'completed_stage_groups': groups,
            'collector_thread_CPU_seconds_partial': snap['snapshot_CPU_seconds_measured'],
            'collector_wall_seconds_partial': snap['snapshot_wall_seconds_measured'],
            'independent_total_observer_overhead': 'NOT_MEASURED',
            'bottleneck': max(groups, key=lambda n: groups[n]['CPU_exclusive']) if complete and groups else 'BOTTLENECK_NOT_LOCALIZED',
            'limits': 'Stage coverage only AP main; no full detailed call profile. Cumulative snapshots not summed; collector last write/hook overhead excluded. Open stages are unfinished lower bounds.'}
        table('profiling_summary.csv', [{'stage': n, **g} for n, g in groups.items()] or [{'status': 'NO_COMPLETED_STAGES', 'open_stages': snap['open_stages']}])
        save('profiling_coverage_report.json', profile)
    else:
        table('profiling_summary.csv', [{'status': 'NO_AP_OBSERVATIONS'}])
    save('profiling_manifest.json', {'mapping': read(OUT / 'path_manifest.json') if (OUT / 'path_manifest.json').exists() else {},
        'transfers': transfers, 'profile': profile})
    table('new_exact_source_moments.csv', [result] if result and result['status'] == 'SUCCESS' else [{'status': ledger['status'], 'C': '', 'w': '', 'new_sources': 0}])
    aliases = {'old_vs_new_optimum.csv': 'old_vs_new_optimization.csv',
               'reference_P1_refinement.csv': 'reference_P1_trace.csv',
               'ao_multistart_recheck.csv': 'ao_multistart_history.csv',
               'coordinate_search_status.csv': 'coordinate_search_completion.csv'}
    for dest, original in aliases.items():
        if (OUT / original).exists():
            shutil.copy2(OUT / original, OUT / dest)
        else:
            table(dest, [{'status': 'NOT_RUN_NO_VALID_NEW_SOURCE', 'baseline_MB_count': 147}])
    if not (OUT / 'new_exact_skr_26_distances.csv').exists():
        table('new_exact_skr_26_distances.csv', [{'status': 'NOT_RUN_NO_VALID_NEW_SOURCE', 'L_km': '', 'K': ''}])
    table('execution_ledger.csv', [ledger])
    manifest = read(OUT / 'protected_input_manifest.json')
    unchanged = pilot.verify_inputs()
    (OUT / 'scientific_provenance_audit.md').write_text(
        f'# Scientific provenance audit\n\n{unchanged} protected hashes unchanged; exact cache key {KEY}, binary64 {[n.hex() for n in pilot.PAIR]}. Original source/precision1050,1250,1450/quadrature/MI/direct Z-minus/AO settings unchanged. No interpolation or other AP. Scientific source caches not relocated. Historical frozen-spec hash discrepancy remains unchanged; lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS.\n', encoding='utf-8')
    if not (OUT / 'windows_path_root_cause.md').exists():
        (OUT / 'windows_path_root_cause.md').write_text('NOT_READY_FOR_AP: ' + str(ledger.get('error')), encoding='utf-8')
    if not (OUT / 'production_path_preflight.csv').exists():
        table('production_path_preflight.csv', [{'status': 'NOT_READY_FOR_AP', 'error': ledger.get('error')}])
    if not (OUT / 'observer_v2_integration_tests.csv').exists():
        table('observer_v2_integration_tests.csv', [{'status': 'NOT_RUN_PREPARATION_FAILURE'}])
    ledger.update(final_wall_seconds_since_origin=9000 - remaining(), wall_budget_respected=remaining() >= 0,
                  protected_hashes_unchanged=unchanged, stage_files_preserved_and_deleted=len(transfers),
                  no_worker_remaining=not pilot.workers(), postprocess=post, source_result=result, profiling=profile,
                  MB_exact_count=148 if result and result['status'] == 'SUCCESS' else 147,
                  science_precision_quadrature_AO_changed=False, global_optimum_claimed=False)
    save('run_report.json', ledger)
    report = ['# Path-fixed observer-v2 Probe A run', '', ledger['status'], '',
        f"Fresh origin={budget()['origin_utc']}, deadline={budget()['deadline_utc']}; elapsed={ledger['final_wall_seconds_since_origin']}s<=9000. One A attempt ceiling4500s, reserve1800s; no retries/other AP.",
        f"Production path readiness={ledger.get('readiness')}; stage={stage}; original observer v2 used through validated short-prefix binding. Registry and permanent power unchanged.",
        f"Source={result}; MB catalog={ledger['MB_exact_count']}; no C,w inferred on failure.",
        f"SKR/AO/P1/P2={post}; if null: no new evaluations, old147 catalog/26matches/ref(.165,5.5)K.07798099387393764/22km(.165,5.475)K.07661740491526092 unchanged,0 new refinement/closures. Missing P1(.165,5.49375),(.165,5.50625); P2(.16375,5.5),(.16531250000000003,5.5).", 
        f"Profiling={profile}; no AP full-detailed profile/independent overhead claimed.",
        f"Runtime/controllerCPU/JobCPU/cleanup/tests/provenance: {ledger}",
        'One measured midpoint is not continuous convergence. Original inner4/outer6/stagnation/unresolved-source/remote-boundary/wholeK-error limitations remain. Fresh AO catalog agreement is reported only if actually run.',
        'Ponytail reused original observer/source/AO/native Job+Sleep; only execution paths, gates and reports added. All previous artifacts preserved.']
    (OUT / 'run_report.md').write_text('\n\n'.join(report) + '\n', encoding='utf-8')
    assert all((OUT / name).is_file() for name in REQUIRED)
    return ledger


def execute():
    bind();b = budget();stage = Path(b['stage'])
    if (OUT / 'run_report.json').exists() or b['AP_attempts']:
        raise FileExistsError('Attempt/report exists: no automatic retry or deadline reset')
    ledger = {'status': 'PREPARING', 'AP_attempts': 0, 'receipts': [], 'controller_pid': os.getpid()}
    lease = safe.AwakeOnAC();cpu = time.process_time();error = None
    stage.mkdir(parents=True, exist_ok=False)
    (OUT / 'exact_source_cache').mkdir(exist_ok=False)
    old = OUT.parent / 'controlled_probe_A_20261010'
    protected = read(old / 'protected_input_manifest.json')
    for p in old.rglob('*'):
        if p.is_file():protected[p.relative_to(ROOT).as_posix()] = digest(p)
    for name in ('scripts/run_path_fixed_probe_A.py', 'scripts/observer_v2_short_path_entry.py', 'tests/test_observer_short_paths.py'):
        protected[name] = digest(ROOT / name)
    save('protected_input_manifest.json', protected)
    try:
        pilot.verify_inputs();assert not pilot.workers()
        assert safe.safe_power(safe.WindowsPower().read())
        paths = prepare_paths(stage)
        (OUT / 'windows_path_root_cause.md').write_text(
            '# Windows path root cause and repair\n\nPrior snapshot/sidecar temporary names265/264 characters failed with LongPathsEnabled0. Atomic writer adds only .tmp; deep parent plus64-character identity created overflow, including sidecar failure reporting. New per-run ASCII staging with short observer names and hash-bound scientific identity mapping; exact source keys/cache stay in repository. Actual create/fsync/read/atomic rename/hash/delete tests and archive transfer exercised before AP. No registry/global long-path/power changes.\n', encoding='utf-8')
        tests = []
        patterns = ('test_observer_short_paths.py', 'test_controlled_observer_v2_pilot.py', 'test_observer_v2_recovery.py',
            'test_overnight_observer_integration.py', 'test_overnight_source_observer.py', 'test_source_bottleneck_diagnostic.py',
            'test_ao_phase2a_execution.py', 'test_ao_phase2a_preparation.py', 'test_ao_phase2a_resume.py',
            'test_ao_numerical_optimum_audit.py', 'test_windows_sleep_safe_supervision.py',
            'test_alt_opt_provenance_and_stopping.py', 'test_mb_batch3_resume.py')
        for pattern in patterns:
            done = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
                cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
            output = done.stdout + done.stderr
            match = re.search(r'Ran (\d+) tests?', output)
            tests.append({'pattern': pattern, 'returncode': done.returncode, 'count': int(match[1]) if match else 0, 'output': output})
            save('regression_tests.json', tests);assert done.returncode == 0, tests[-1]
        native = native_tests(stage)
        config, ensemble, evaluator, identity, request = pilot.request_and_identity()
        bank = pilot.source.load_source_payloads(config, pilot.DIRS)
        assert sum(float.fromhex(p['nu_mb_raw_hex']) > 0 for p in bank.values()) == 147
        assert pilot.source.candidate_from_payload(config, bank, 'MB', *pilot.PAIR) is None
        pilot.verify_inputs();subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
        assert datetime.now(timezone.utc) < datetime.fromisoformat(b['preparation_deadline_utc'])
        assert remaining() >= 4500 + 1800, 'Not enough AP ceiling plus finalization reserve'
        ledger.update(readiness='READY_FOR_CONTROLLED_AP_PILOT', regression_tests=sum(t['count'] for t in tests),
                      native_tests=native, provenance_sources_verified=147, protected_inputs=len(protected))
        save('readiness.json', ledger)
        auth = {'status': 'EXPLICITLY_APPROVED_CONTROLLED_PROBE_A_OBSERVER_V2',
            'source_cache_key': KEY, 'pair_hex': [v.hex() for v in pilot.PAIR],
            'request_sha256': json_hash(request), 'path_manifest_sha256': digest(stage / 'paths.json'),
            'deadline_monotonic': time.monotonic() + 4500,
            'deadline_utc': (datetime.now(timezone.utc) + timedelta(seconds=4500)).isoformat(),
            'overall_deadline_utc': b['deadline_utc'], 'overall_deadline_monotonic': b['origin_monotonic'] + 9000,
            'probe_wall_limit_seconds': 4500, 'max_attempts': 1, 'fresh_user_authorization': True}
        save('execution_authorization.json', auth);save('exact_source_request.json', request);save('exact_source_identity.json', identity)
        assert safe.safe_power(safe.WindowsPower().read());time.sleep(.5);assert safe.safe_power(safe.WindowsPower().read())
        with lease:
            assert not pilot.workers();pilot.verify_inputs()
            ledger.update(status='SOURCE_A_RUNNING', AP_attempts=1, source_started_utc=datetime.now(timezone.utc).isoformat())
            b.update(AP_attempts=1, status='SOURCE_A_RUNNING');save('budget.json', b)
            save('execution_status.json', ledger);table('execution_ledger.csv', [ledger])
            with (OUT / 'source_A.log').open('w', encoding='utf-8') as log:
                with patch.object(safe, 'WindowsPower', pilot.watched_power(prefix(stage, 'a'))):
                    receipt = safe.supervised_process([sys.executable, '-B', '-X', 'utf8', '-u', __file__, '--source-child'], 4500, log)
            ledger['receipts'].append(receipt);save('source_supervision.json', receipt)
            assert not pilot.workers() and receipt['no_watchdog_thread_remaining']
            result = read(OUT / 'source_result.json') if (OUT / 'source_result.json').exists() else None
            ledger['source_status'] = old_entry.classify(receipt, result)
            reason = receipt.get('power_watch', {}).get('abort_reason') or ''
            if 'OBSERVER_MONITORING' in reason:ledger['source_status'] = 'WATCHDOG_ABORT'
            if 'OBSERVER_INSTRUMENTATION' in reason:ledger['source_status'] = 'INSTRUMENTATION_FAILURE'
            assert receipt['wall_limit_respected']
            if ledger['source_status'] == 'SUCCESS':
                assert result['status'] == 'SUCCESS' and receipt['returncode'] == 0
                with (OUT / 'postprocess.log').open('w', encoding='utf-8') as log:
                    receipt = safe.supervised_process([sys.executable, '-B', '-X', 'utf8', '-u', __file__, '--postprocess'], remaining() - 300, log)
                ledger['receipts'].append(receipt);save('postprocess_supervision.json', receipt)
                assert receipt['returncode'] == 0 and receipt['wall_limit_respected']
                ledger['status'] = 'SOURCE_SUCCESS_26_DISTANCE_AO_VALIDATED'
            else:
                ledger['status'] = 'STOPPED_' + ledger['source_status']
    except BaseException as exc:
        error = repr(exc);ledger['status'] = 'STOPPED_ERROR' if ledger['AP_attempts'] else 'NOT_READY_FOR_AP'
        print(error, flush=True)
    finally:
        ledger.update(error=error, sleep_prevention=lease.receipt, controller_CPU_seconds_since_execute=time.process_time() - cpu,
                      recorded_Job_CPU_seconds=sum(r.get('aggregate_cpu_seconds', 0) for r in ledger['receipts']),
                      CPU_scope='Execute parent and supervised source/postprocess Jobs; regression child CPU and initialization/repair CPU excluded')
        save('execution_status.json', ledger)
        report = finalize(ledger, stage)
        print(json.dumps({k: report[k] for k in ('status', 'AP_attempts', 'MB_exact_count', 'final_wall_seconds_since_origin', 'error')}, indent=2), flush=True)
    return 1 if error else 0


def initialize():
    if OUT.exists():
        raise FileExistsError('Fresh output already exists: never reset budget or retry')
    OUT.mkdir()
    now = datetime.now(timezone.utc)
    ledger = {'origin_utc': now.isoformat(), 'origin_monotonic': time.monotonic(),
              'deadline_utc': (now + timedelta(seconds=9000)).isoformat(),
              'preparation_deadline_utc': (now + timedelta(seconds=2700)).isoformat(),
              'stage': 'C:/aoobs/p' + uuid.uuid4().hex[:10],
              'status': 'PREPARING_PATH_FIX', 'AP_attempts': 0,
              'total_budget_seconds': 9000, 'AP_max_seconds': 4500,
              'final_reserve_seconds': 1800, 'fresh_user_authorization': True,
              'budget_reset': False}
    (OUT / 'budget.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    print(json.dumps(ledger, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-child', action='store_true')
    parser.add_argument('--postprocess', action='store_true')
    args = parser.parse_args()
    if args.init:
        initialize()
    elif args.execute:
        return execute()
    elif args.source_child:
        return source_child()
    elif args.postprocess:
        bind();return pilot.process_success()
    else:
        parser.error('Fresh initialization required')


if __name__ == '__main__':
    raise SystemExit(main())
