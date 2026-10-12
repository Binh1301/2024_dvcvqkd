"""Saved-only final audit; reproduce persistence contention on dummy data only."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_path_fixed_probe_A as run
from scripts.overnight_source_observer import atomic_json
from scripts.diagnose_theta10_D55_source_bottlenecks import read, digest, rows

OUT = run.OUT


def main():
    started = time.monotonic();cpu = time.process_time()
    if (OUT / 'final_saved_verification.json').exists():
        raise FileExistsError('Preserve final audit; no reexecution')
    run.bind();report = read(OUT / 'run_report.json')
    assert report['status'] == 'STOPPED_WATCHDOG_ABORT' and report['AP_attempts'] == 1
    receipt = read(OUT / 'source_supervision.json')
    assert receipt['power_watch']['abort_reason'] == 'POWER_CHECK_FAILED: OBSERVER_MONITORING_HEARTBEAT_LOST'
    assert not receipt['power_watch']['poll_gaps'] and not receipt['deadline_exceeded']
    snapshot = read(OUT / 'staging_archive/obs/a_stage_snapshot.json')
    temporary = read(OUT / 'staging_archive/obs/a_stage_snapshot.json.tmp')
    heartbeats = [json.loads(s) for s in (OUT / 'staging_archive/obs/a_heartbeats.jsonl').read_text().splitlines()]
    assert snapshot['snapshot_count'] == len(heartbeats) == 31
    assert temporary['snapshot_count'] == 32 and heartbeats[-1]['snapshot_count'] == 31
    # The identical writer, OS user and new-run filesystem; no scientific worker.
    dummy = OUT / 'postmortem_dummy';dummy.mkdir()
    path = dummy / 'a_stage_snapshot.json'
    atomic_json(path, {'dummy_only': True, 'counter': 1})
    with path.open('r', encoding='utf-8') as reader:
        try:
            atomic_json(path, {'dummy_only': True, 'counter': 2})
            held_reader = {'status': 'SUCCESS'}
        except OSError as exc:
            held_reader = {'status': 'FAILED', 'error': repr(exc), 'errno': exc.errno,
                           'winerror': getattr(exc, 'winerror', None)}
        old_after = read(path)
        temp_after = read(path.with_suffix('.json.tmp')) if path.with_suffix('.json.tmp').exists() else None
    atomic_json(path, {'dummy_only': True, 'counter': 3})
    assert read(path)['counter'] == 3
    evidence = {'status': 'WATCHDOG_ABORT_FROM_STALE_OBSERVER_SNAPSHOT',
        'last_committed_snapshot': snapshot['snapshot_count'], 'heartbeat_lines': len(heartbeats),
        'fully_written_uncommitted_temporary_snapshot': temporary['snapshot_count'],
        'committed_wall_seconds': snapshot['wall_seconds'],
        'temporary_wall_seconds_UNCOMMITTED': temporary['wall_seconds'],
        'last_committed_UTC': snapshot['utc'], 'temporary_UTC_UNCOMMITTED': temporary['utc'],
        'max_successive_heartbeat_gap_seconds': max(b['wall_seconds'] - a['wall_seconds'] for a, b in zip(heartbeats, heartbeats[1:])),
        'published_snapshot_error': snapshot['observer_error'],
        'production_error_type_or_holder_identity': 'NOT_CAPTURED',
        'known_failure_interval': 'Snapshot32 temporary write completed but atomic publication/heartbeat did not; observer watch catches error only in memory, subsequently killed before shutdown persistence',
        'dummy_reader_held_atomic_replace': held_reader,
        'dummy_old_snapshot_after_failed_replace': old_after,
        'dummy_temp_after_failed_replace': temp_after,
        'dummy_reader_released_atomic_write': 'PASS',
        'production_cause_inference': 'File-open/replace contention is reproduced and matches saved old/temp/heartbeat pattern; production exception and lock holder unrecorded, so exact causal attribution is not proven',
        'original_long_path_overflow': 'RESOLVED_FOR_THIS_RUN_GENERATED_PATHS',
        'monitoring_persistence_robustness': 'NOT_RESOLVED_END_TO_END',
        'physical_AC_loss_or_scheduler_gap': False,
        'source_moment_computations_in_dummy': 0, 'AP_retry': False,
        'original_observer_v2_bytes_changed_after_execution': False}
    run.save('heartbeat_abort_audit.json', evidence)
    regressions = []
    for prior in read(OUT / 'regression_tests.json'):
        done = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest',
            'discover', '-s', 'tests', '-p', prior['pattern'], '-v'], cwd=ROOT,
            capture_output=True, text=True, encoding='utf-8')
        output = done.stdout + done.stderr
        count = re.search(r'Ran (\d+) tests?', output)
        regressions.append({'pattern': prior['pattern'], 'returncode': done.returncode,
                           'count': int(count[1]) if count else 0, 'output': output})
        run.save('final_regression_tests.json', regressions)
        assert done.returncode == 0, regressions[-1]
    run.pilot.verify_inputs()
    transfer = read(OUT / 'transfer_verification.json')
    assert all(digest(ROOT / r['archive']) == r['sha256'] for r in transfer)
    assert not list(Path(run.budget()['stage']).rglob('*.*'))
    assert not run.pilot.workers()
    assert not list((OUT / 'exact_source_cache').iterdir())
    assert report['sleep_prevention']['released_verified'] and receipt['no_watchdog_thread_remaining']
    old = run.pilot.BASE / 'optimized_skr_26_distances.csv'
    copied = OUT / 'baseline_147_source_26_distance_SAVED_ONLY.csv'
    copied.write_bytes(old.read_bytes());assert digest(copied) == digest(old)
    baseline = rows(old)
    assert len(baseline) == 26 and all(r['matches_catalog_maximum'] == 'True' for r in baseline)
    profiles = read(OUT / 'path_manifest.json')
    preflight_paths = rows(OUT / 'production_path_preflight.csv')
    assert all(r['creation_flush_read_atomic_replace_rename_hash_delete'].startswith('PASS') for r in preflight_paths)
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    final = {'status': 'STOPPED_WATCHDOG_ABORT_FINAL_VERIFIED_NO_RETRY',
        'UTC': datetime.now(timezone.utc).isoformat(), 'wall_since_controller_origin_seconds': 9000 - run.remaining(),
        'within_150_minute_original_deadline': run.remaining() >= 0,
        'audit_wall_seconds': time.monotonic() - started, 'audit_parent_CPU_seconds': time.process_time() - cpu,
        'tests': sum(t['count'] for t in regressions), 'git_diff_check': True,
        'protected_hashes_unchanged': run.pilot.verify_inputs(), 'validated_production_paths': len(preflight_paths),
        'maximum_tested_path_length_including_temp_or_move': max(int(r['max_path_characters']) for r in preflight_paths),
        'native_integration_cases_PASS': len(report['native_tests']),
        'transferred_files_verified': len(transfer), 'all_15_required_files_present': all((OUT / n).is_file() for n in run.REQUIRED),
        'source_successes': 0, 'source_timeouts': 0, 'source_watchdog_aborts': 1,
        'MB_sources': 147, 'new_C_w': None, 'new_SKR_evaluations': 0, 'new_AO_runs': 0,
        'saved_only_catalog_matches': 26, 'fresh_catalog_matches': 'NOT_RUN_NO_VALID_SOURCE',
        'P1_refinement_steps_added': 0, 'new_coordinate_searches_completed': 0,
        'baseline_CSV_identical': True, 'no_workers': True, 'Sleep_restored': True,
        'source_Job_CPU_seconds': receipt['aggregate_cpu_seconds'],
        'execute_parent_CPU_seconds': report['controller_CPU_seconds_since_execute'],
        'native_dummy_Job_CPU_seconds': sum(r['Job_CPU_seconds'] for r in report['native_tests']),
        'inclusive_entire_campaign_CPU_seconds': 'NOT_MEASURED_REGRESSION_CHILD_AND_REPAIR_CPU_EXCLUDED',
        'profiler_snapshots_committed': 31, 'uncommitted_snapshot32_not_counted': True,
        'full_run_profiling': False, 'bottleneck': 'BOTTLENECK_NOT_LOCALIZED',
        'operational_repair_next': 'Shared-file atomic replacement under concurrent readers plus durable error/health reporting must be validated; no AP retry authorized under consumed one-attempt budget',
        'P1_missing_pairs': [[.165, 5.49375], [.165, 5.50625]],
        'P2_missing_pairs': [[.16375, 5.5], [.16531250000000003, 5.5]],
        'scientific_precision_quadrature_AO_changes': False}
    run.save('final_saved_verification.json', final)
    text = [
        '# Final answers — path-fixed controlled Probe A', '',
        '1. Long-path overflow resolved on this run: short staging names, full identity manifest, verified archive. End-to-end instrumentation is NOT fully reliable: a separate atomic-publication/heartbeat failure occurred.',
        f"2. Actual production preflight PASS: {len(preflight_paths)} real path-operation tests, max {final['maximum_tested_path_length_including_temp_or_move']} chars including suffix, archive transfer, 8 native mapped-entry cases, {final['tests']} regressions. Passing short workloads did not cover all concurrent-reader timing cases.",
        '3. Real AP entry used: thin short-prefix binding delegates unchanged observer-v2 production main, original gate, original full-support worker. No v1 controller.',
        '4. One A attempt aborted WATCHDOG_ABORT after 339.265 s, not timeout/numerical failure/AC loss; stale heartbeat30s triggered successful full-Job termination. No retry/other AP.',
        '5. No validated C,w or complete source output; AP forced stop prevented parent/observer final callbacks.',
        '6. Catalog remains147, not148; source cache empty for this attempt.',
        '7. No new SKR evaluated; improvement unknown, not evidence that A has lower/equal K. Saved baseline values remain authoritative.',
        '8. Reference best unchanged(.165,5.5),K.07798099387393764;22km(.165,5.475),K.07661740491526092.',
        '9. P1 adds0 valid paired refinement steps; bracket[5.4875,5.5125], width.025 unchanged; exact missing midpoints5.49375 and5.50625 (upper binary64 0x1.6066666666666p+2).',
        '10. No coordinate search completed.',
        '11. Fresh AO NOT_RUN because no valid source; saved original finitecatalogmaximum agreement26/26 remains, not new convergence evidence.',
        '12. Partial AP coverage31 committed snapshots/305.375 wall s/297.203125 processCPU s at1050digits; uncommitted snapshot32 excluded. Completed Gram1call23.890625exclusiveCPU s, eigensystem4calls169.390625, LU2calls50.34375; another LU open. No1250/1450/fullrun coverage, no independent total overhead. BOTTLENECK_NOT_LOCALIZED; measured eigensystem time leads only in completed observed subset.',
        f"13. Budget origin01:14:24.465780Z unchanged; controller finish705.179007s, saved finalaudit{final['wall_since_controller_origin_seconds']}s, all<9000s. SourceJobCPU329.828125s, executeparent6.78125s, native preflightJobCPU{final['native_dummy_Job_CPU_seconds']}s; separate auditparent{final['audit_parent_CPU_seconds']}s. Inclusive campaignCPU not measured (repair/regression children excluded).",
        f"14. Five-process Job closed, no worker/watchdog, Sleep restored, AC remained safe. All29 staging files hash-verified in archive then per-file removed; no recursive/broad deletion. {final['protected_hashes_unchanged']} protected hashes unchanged; all15 outputs present/diffPASS. No registry/powerplan/scientific producer changes.",
        '15. P1 still needs(.165,5.49375),(.165,5.50625); P2(.16375,5.5),(.16531250000000003,5.5). Any new AP requires separate authority after robust atomic/error/heartbeat validation. Moments alone do not close inner4/outer6/stagnation/source-coverage/remote-boundary/error-budget limitations.', '',
        'Evidence: fully written temporary snapshot32 remained beside committed31/31heartbeat lines; read-held dummy reproduces atomic replace PermissionError and succeeds after reader release. Exact production exception/lock holder was not recorded, so contention causality is an inference, not a proven attribution.',
        'Ponytail reused original source/AO/v2/native supervisor and stdlib-only path control. Scientific/security/precision/quadrature/AO/binary64/cache identities unchanged; no interpolation or numerical/global convergence claim. Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS; frozen historical-hash discrepancy preexisting unchanged.'
    ]
    (OUT / 'final_answers.md').write_text('\n\n'.join(text) + '\n', encoding='utf-8')
    print(json.dumps({k: final[k] for k in ('status', 'tests', 'protected_hashes_unchanged', 'wall_since_controller_origin_seconds')}, indent=2))


if __name__ == '__main__':main()
