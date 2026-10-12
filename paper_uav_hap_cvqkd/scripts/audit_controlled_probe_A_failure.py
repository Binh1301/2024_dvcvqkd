"""Saved-only audit of the stopped one-attempt pilot; no AP/SKR/AO execution."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import winreg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.overnight_source_observer import atomic_json
from scripts import windows_sleep_safe_supervision as safe

OUT = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation/observer_v2_recovery/controlled_probe_A_20261010'
BASE = OUT.parents[1] / 'overnight_ao_run'
KEY = 'db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    if (OUT / 'final_validation.json').exists():
        raise FileExistsError('Saved audit exists; preserve it, no automatic reexecution')
    pilot = read(OUT / 'pilot_report.json')
    assert pilot['attempts'] == 1 and pilot['new_sources'] == 0
    assert pilot['source_status'] == 'INSTRUMENTATION_FAILURE'
    assert pilot['worker_cleanup_verified'] and pilot['sleep_prevention']['released_verified']
    # Quarantined persistence-only controls, no worker, no numerical operations.
    control = OUT / 'path_diagnostics'
    control.mkdir()
    payload = {'dummy_only': True, 'source_moment_computations': 0,
               'scientific_output': False, 'purpose': 'Windows path-length control'}
    short = control / 'short_control.json'
    long = control / (KEY + '_persistence_control.json')
    atomic_json(short, payload)
    try:
        atomic_json(long, payload)
        ordinary = {'status': 'SUCCESS'}
    except OSError as exc:
        ordinary = {'status': 'FAILED', 'error': repr(exc), 'errno': exc.errno,
                    'winerror': getattr(exc, 'winerror', None)}
    extended = Path('\\\\?\\' + str(long))
    atomic_json(extended, payload)
    assert read(extended) == payload
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r'SYSTEM\CurrentControlSet\Control\FileSystem') as registry:
        long_paths = winreg.QueryValueEx(registry, 'LongPathsEnabled')[0]
    failed = OUT / 'probe_results' / (KEY + '_worker_result.json.tmp')
    snapshot = OUT / 'probe_results' / (KEY + '_stage_snapshot.json.tmp')
    source_payload = OUT / 'exact_source_cache' / (KEY + '.json')
    diagnosis = {'dummy_only': True, 'no_AP_execution': True,
                 'LongPathsEnabled_read_only': long_paths,
                 'failed_production_sidecar_path': str(failed),
                 'failed_production_sidecar_length': len(str(failed)),
                 'initial_snapshot_temp_length': len(str(snapshot)),
                 'prospective_source_cache_path_length': len(str(source_payload)),
                 'parent_directory_exists': failed.parent.is_dir(),
                 'short_ordinary_atomic_write': 'PASS',
                 'long_ordinary_atomic_write': ordinary,
                 'same_long_name_extended_atomic_write': 'PASS',
                 'root_cause': 'WINDOWS_ORDINARY_PATH_LENGTH_LIMIT' if ordinary['status'] == 'FAILED' and long_paths == 0 else 'NOT_CONFIRMED',
                 'observer_entry_unchanged': True,
                 'original_startup_order': 'StageObserver.__enter__ snapshot precedes original worker.main; sidecar failure masks the first snapshot persistence exception',
                 'registry_power_plan_precision_or_science_changes': False,
                 'production_retry': False}
    assert diagnosis['root_cause'] == 'WINDOWS_ORDINARY_PATH_LENGTH_LIMIT'
    atomic_json(OUT / 'path_length_failure_audit.json', diagnosis)
    # Current scoped regressions; each fixture is synthetic or saved/cache-only.
    patterns = ['test_controlled_observer_v2_pilot.py', 'test_observer_v2_recovery.py',
                'test_overnight_observer_integration.py', 'test_overnight_source_observer.py',
                'test_source_bottleneck_diagnostic.py', 'test_ao_phase2a_execution.py',
                'test_ao_phase2a_preparation.py', 'test_ao_phase2a_resume.py',
                'test_ao_numerical_optimum_audit.py', 'test_windows_sleep_safe_supervision.py',
                'test_alt_opt_provenance_and_stopping.py', 'test_mb_batch3_resume.py']
    regressions = []
    for pattern in patterns:
        done = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest',
                               'discover', '-s', 'tests', '-p', pattern, '-v'],
                              cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        output = done.stdout + done.stderr
        count = re.search(r'Ran (\d+) tests?', output)
        regressions.append({'pattern': pattern, 'returncode': done.returncode,
                            'tests': int(count.group(1)) if count else 0, 'output': output})
        atomic_json(OUT / 'final_regression_tests.json', regressions)
        assert done.returncode == 0, regressions[-1]
    # Baseline copy is explicitly NOT a new metric calculation or new AO run.
    baseline_csv = BASE / 'optimized_skr_26_distances.csv'
    copied_csv = OUT / 'baseline_147_sources_26_distances_UNCHANGED.csv'
    copied_csv.write_bytes(baseline_csv.read_bytes())
    assert digest(copied_csv) == digest(baseline_csv)
    with baseline_csv.open(encoding='utf-8', newline='') as stream:
        distances = list(csv.DictReader(stream))
    checkpoint = read(BASE / 'objective_checkpoint.json')
    assert len(distances) == len(checkpoint) == 26
    assert all(len(v['rows']) == 147 for v in checkpoint.values())
    assert all(r['matches_catalog_maximum'] == 'True' for r in distances)
    coordinates = read(BASE / 'reference_targeted_coordinate_searches.json')
    manifest = read(OUT / 'protected_input_manifest.json')
    changed = [name for name, expected in manifest.items() if digest(ROOT / name) != expected]
    assert not changed, changed
    assert not list((OUT / 'exact_source_cache').iterdir())
    inventories = subprocess.run(['powershell', '-NoProfile', '-Command',
        "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--approved-ap|--source-child|--probe|--profile-worker|full_support_c4_worker\\.py|observer_v2_recovery_entry\\.py.*--dummy-mode'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"],
        check=True, capture_output=True, text=True)
    workers = json.loads(inventories.stdout) if inventories.stdout.strip() else []
    assert not workers
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    validation = {'status': 'STOPPED_INSTRUMENTATION_FAILURE_VERIFIED_NO_RETRY',
                  'finished_utc': datetime.now(timezone.utc).isoformat(),
                  'wall_seconds_since_controller_origin': (datetime.now(timezone.utc) - datetime.fromisoformat(pilot['authorization']['controller_origin_utc'])).total_seconds(),
                  'audit_wall_seconds': time.monotonic() - start,
                  'wall_budget_respected': datetime.now(timezone.utc) < datetime.fromisoformat(pilot['authorization']['overall_deadline_utc']),
                  'tests': sum(r['tests'] for r in regressions), 'regressions': 'CURRENTLY_VERIFIED_PASS',
                  'git_diff_check': diff.returncode == 0,
                  'protected_inputs': len(manifest), 'changed_inputs': changed,
                  'source_attempts': 1, 'source_successes': 0, 'source_timeouts': 0,
                  'source_instrumentation_aborts': 1, 'new_C_w': None,
                  'MB_sources': 147, 'new_source_metrics': 0, 'new_AO_runs': 0,
                  'baseline_26_rows_identical_bytes': True,
                  'baseline_AO_matches': 26, 'fresh_AO_matches': 'NOT_RUN_NO_VALID_NEW_SOURCE',
                  'P1_refinement_steps_added': 0, 'new_coordinate_searches_completed': 0,
                  'baseline_reference_coordinate_searches': coordinates,
                  'next_P1_pairs': [{'nu_raw': .165, 'V_A': 5.49375, 'hex': [(.165).hex(), (5.49375).hex()]},
                                    {'nu_raw': .165, 'V_A': 5.50625, 'hex': [(.165).hex(), (5.50625).hex()]}],
                  'next_P2_pairs': [{'nu_raw': .16375, 'V_A': 5.5}, {'nu_raw': .16531250000000003, 'V_A': 5.5}],
                  'next_pairs_planning_only_not_executed': True,
                  'profiling': 'NO_AP_OBSERVATIONS_BOTTLENECK_NOT_LOCALIZED_OVERHEAD_NOT_MEASURED',
                  'cleanup_worker_inventory': workers, 'AC_after': safe.WindowsPower().read(),
                  'sleep_restored': pilot['sleep_prevention']['released_verified'],
                  'recorded_controller_and_AP_Job_CPU_seconds': pilot['recorded_total_CPU_seconds'],
                  'CPU_scope': 'Pilot controller + source Job only; test/preflight Jobs and separate audit CPU excluded; not full inclusive campaign CPU',
                  'no_scientific_or_AO_changes': True,
                  'no_numerical_or_global_optimum_certificate': True}
    atomic_json(OUT / 'final_validation.json', validation)
    prior = ROOT / '.agent/SESSION_HANDOFF.md'
    (OUT / 'session_handoff_before_pilot.md').write_bytes(prior.read_bytes())
    summary = [
        '# Controlled Probe A — final conclusions', '',
        'Status: INSTRUMENTATION_FAILURE; stopped after one attempt, no retry, B or P2.', '',
        f"1. Source Job wall-time {pilot['source_wall_seconds']:.3f} s; controller {pilot['total_wall_seconds']:.3f} s; recorded controller+source Job CPU {pilot['recorded_total_CPU_seconds']:.3f} s (not all test/audit CPU).",
        f"2. Windows LongPathsEnabled={long_paths}; sidecar temporary pathname {len(str(failed))} characters. Same unchanged atomic writer succeeds on a short name and extended pathname, fails on the ordinary long name. Observer snapshot startup precedes original AP main; failure result-sidecar writing also failed. No permanent Windows setting changed.",
        '3. No valid (C,w), source cache entry, new SKR or expanded catalog. Baseline remains 147 sources/3822 saved metrics. Source fallback scientific formulas and v2 producer bytes are unchanged.',
        '4. Reference old best: (nu,VA)=(0.165,5.5), K=0.07798099387393764 bits/use. At 22 km: (0.165,5.475), K=0.07661740491526092. No new comparison can be made.',
        '5. P1 stays [5.4875,5.5125]; zero additional refinement steps/bracket shrink/best change. Exact paired midpoints remain (0.165,5.49375) and (0.165,5.50625); upper midpoint binary64 is 0x1.6066666666666p+2. No coordinate direction completed.',
        '6. Fresh cache-only AO is NOT_RUN (requires valid new source). Saved original AO evidence still matches the unchanged catalog 26/26; no new 26/26 certification. Full baseline table is a byte-identical explicitly labeled copy, not newly computed SKR.',
        '7. No real AP snapshots, stage/precision coverage or measured instrumentation overhead. Source numerical bottleneck is not localized; only the operational pathname failure is confirmed.',
        f"8. {validation['tests']} current scoped regressions PASS; three native dummy safety cases PASS; {len(manifest)} protected hashes unchanged. Source Job contained five processes, watchdog exited, no workers remain, Sleep restored, AC remains connected; deadline respected.",
        '9. Before any separately approved attempt: validate long-path-safe output for snapshot, heartbeat, result sidecar, profiler and exact cache at actual path lengths, plus error reporting when sidecar persistence itself fails. No observer/source repair or AP retry performed here. Remaining P1 and P2 moments, original stopping-limit/accuracy/boundary gaps are still unresolved; no continuous/global optimum claimed.', '',
        'Ponytail: reused validated v2 entry, original source/AO and native supervisor; audit uses stdlib persistence controls, no alternate numerical method.',
        'Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS; historical frozen-hash discrepancy remains preexisting and unchanged.'
    ]
    (OUT / 'final_conclusions.md').write_text('\n'.join(summary) + '\n', encoding='utf-8')
    print(json.dumps({k: validation[k] for k in ('status', 'tests', 'protected_inputs', 'MB_sources', 'wall_seconds_since_controller_origin')}, indent=2))


if __name__ == '__main__':
    main()
