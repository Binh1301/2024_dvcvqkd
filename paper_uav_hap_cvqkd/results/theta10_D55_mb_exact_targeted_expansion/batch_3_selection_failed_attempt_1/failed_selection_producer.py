"""Finalize Batch3 selection before separate budget approval; never execute AP."""
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_theta10_D55_mb_batch3 as prep
from scripts.windows_sleep_safe_supervision import AwakeOnAC

ao, io, source, sweep = prep.ao, prep.io, prep.source, prep.sweep
OUT = prep.BASE.parent / 'batch_3'


def main():
    if OUT.exists():
        raise SystemExit('Batch3 directory exists; preserve it, do not restart selection')
    started = time.monotonic()
    import torch
    torch.set_num_threads(1)
    config = source.unconstrained_config()
    manifest = prep.read_json(prep.OUT / 'input_manifest_after.json')
    manifest.update(io.raw_snapshot(p for p in prep.OUT.rglob('*') if '__pycache__' not in p.parts))
    manifest.update(io.raw_snapshot([Path(__file__)]))
    for name, expected in manifest.items():
        assert io.digest(ROOT / name) == expected, name
    check = prep.read_json(prep.OUT / 'final_preparation_verification.json')
    for name, expected in check['output_artifact_sha256'].items():
        assert io.digest(ROOT / name) == expected, name
    OUT.mkdir()
    io.save_json(OUT / 'protected_input_manifest.json', manifest)
    checkpoint = prep.read_json(prep.BASE / 'objective_checkpoint.json')
    catalog = io.read_csv(prep.BASE / 'expanded_catalog.csv')
    certificates = {float(r['L_km']): r for r in io.read_csv(prep.OUT / 'catalog_145_verification.csv')}
    baseline_ao = {float(r['L_km']): r for r in io.read_csv(prep.BASE / 'alt_opt_validation.csv')}
    baseline_best = {float(r['L_km']): r for r in io.read_csv(prep.BASE / 'previous_vs_new_optimum.csv')}
    recorded = io.read_csv(prep.OUT / 'batch_3_selected_probes.csv')
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            ao.MAX_REFINEMENT_STAGES) == (1e-8, 1e-6, 6, 4)
    histories, selected = [], []
    with ExitStack() as stack:
        stack.enter_context(patch.object(ao.ExactMBEvaluator, 'source_moments', prep.forbidden))
        stack.enter_context(patch.object(prep.gram_moments, '_fallback', prep.forbidden))
        stack.enter_context(patch.object(ao, 'evaluate_candidate', prep.forbidden))
        stack.enter_context(patch.object(sweep, 'make_channel', prep.forbidden))
        bank = source.load_source_payloads(config, prep.previous.DIRS)
        mb = {prep.pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])): p
              for p in bank.values() if float.fromhex(p['nu_mb_raw_hex']) > 0}
        assert len(mb) == len(catalog) == 145
        assert set(mb) == {prep.pair(r['nu_raw'], r['V_A']) for r in catalog}
        for r in catalog:
            p = mb[prep.pair(r['nu_raw'], r['V_A'])]
            assert r['source_cache_key'] == p['cache_key'] and r['ensemble_hash'] == p['ensemble_hash']
            assert float(r['C']) == float(p['C']) and float(r['w']) == float(p['w'])
            c = source.candidate_from_payload(config, bank, 'MB', float(r['nu_raw']), float(r['V_A']))
            assert c and c['source_cache_key'] == p['cache_key']
        for distance in sweep.DISTANCES_KM:
            saved = checkpoint[str(distance)]
            channel = saved['identity']['identity']['channel']
            assert ao.objective_compatible(saved['identity'], ao.objective_identity(config, channel))
            assert len(saved['rows']) == 145
            assert {prep.pair(r['nu_raw'], r['V_A']) for r in saved['rows']} == set(mb)
            for r in saved['rows']:
                p = mb[prep.pair(r['nu_raw'], r['V_A'])]
                assert r['source_cache_key'] == p['cache_key'] and r['ensemble_hash'] == p['ensemble_hash']
                assert r['channel_hash'] == channel['channel_hash']
                ao.finite_metrics(r)
                assert float(r['SKR']) == float(r['beta_I_AB']) - float(r['chi_BE'])
            best = max(saved['rows'], key=lambda r: float(r['SKR']))
            assert best['SKR'] == float(certificates[distance]['best_K'])
            assert best['SKR'] == float(baseline_ao[distance]['K']) == float(baseline_best[distance]['new_K'])
        saved = checkpoint['22.0']
        obj = ao.ExactObjective(config, saved['identity']['identity']['channel'], OUT,
                               allow_new_source=False, source_cache_dirs=prep.previous.DIRS)
        obj.restore_objective_rows(saved['rows'], saved['identity'])
        for key in mb:
            obj.register_catalog(*map(float.fromhex, key))
        for variable, fixed in (('nu_raw', 5.475), ('V_A', .165), ('nu_raw', 5.5)):
            result = ao.adaptive_maximize_1d(variable=variable, fixed=fixed,
                values=obj.catalog_values(variable, fixed), objective=obj)
            histories.append({'L_km': 22., **result})
        updated_nu = histories[0]
        assert obj.catalog_values('nu_raw', 5.475) == [.165]
        assert updated_nu['bracket'] == [None, None] and updated_nu['refinement_stages'] == 0
        assert [e['value'] for e in updated_nu['source_missing']] == [.0825]
        # .0825 is an OUTER half-value, not a bracket midpoint. No appropriate
        # midpoint at VA5.475 currently exists under the frozen generator.
        for priority, (nu, va) in enumerate(prep.PRIORITY, 1):
            key = prep.pair(nu, va)
            assert key not in mb and source.candidate_from_payload(config, bank, 'MB', nu, va) is None
            identity = obj.evaluator._source_identity(source.make_ensemble(config, 'MB', nu, va), nu, va)
            original = next(r for r in recorded if prep.pair(r['nu_raw'], r['V_A']) == key)
            assert original['source_cache_key'] == source.json_hash(identity)
            assert (original['nu_raw_hex'], original['V_A_hex']) == key
            search = histories[1 if priority < 3 else 2]
            expected_value = va if priority < 3 else nu
            assert any(float(e['value']).hex() == expected_value.hex() for e in search['source_missing'])
            reason = (prep.REASONS[priority - 1] if priority < 3 else
                'Retain original nu midpoint atVA5.5: VA5.475 has onlynu=.165. Original '
                'generator requests missing lower OUTERnu=.0825, then stops before refinement; '
                'no appropriate nu midpoint atVA5.475 exists. Do not invent a midpoint or '
                'replace it with the far outer point. This probe does not close theVA5.475 nu slice.')
            selected.append({'priority': priority, 'nu_raw': nu, 'V_A': va, 'nu_raw_hex': key[0],
                'V_A_hex': key[1], 'source_cache_key': source.json_hash(identity),
                'ensemble_hash': identity['ensemble_hash'], 'reason': reason,
                'source_availability': 'EXACT_SOURCE_MISSING',
                'status': 'NOT_RUN_AWAITING_EXPLICIT_BATCH3_BUDGET_APPROVAL'})
        assert len({r['source_cache_key'] for r in selected}) == 3
        assert obj.unique_exact_evaluations == 0
    io.write_csv(OUT / 'batch_3_final_selected_probes.csv', selected)
    io.save_json(OUT / 'probe3_coordinate_reconsideration.json', histories)
    # Temporary native safety preflight only. Release now and reacquire before AP.
    lease = AwakeOnAC()
    with lease:
        pass
    io.save_json(OUT / 'selection_power_preflight.json', {'temporary_lease': lease.receipt,
        'active_now': False, 'must_recheck_and_reacquire_before_AP': True,
        'AP_started': False, 'permanent_power_settings_changed': False})
    tests = []
    for pattern in ('test_windows_sleep_safe_supervision.py', 'test_alt_opt_provenance_and_stopping.py',
                    'test_mb_sleep_safe_expansion.py', 'test_mb_batch2.py', 'test_mb_batch3_preparation.py'):
        done = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover',
                               '-s', 'tests', '-p', pattern, '-v'], cwd=ROOT, capture_output=True, text=True)
        tests.append({'pattern': pattern, 'returncode': done.returncode, 'output': done.stdout + done.stderr})
    io.save_json(OUT / 'selection_regression_tests.json', tests)
    assert all(t['returncode'] == 0 for t in tests)
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    for name, expected in manifest.items():
        assert io.digest(ROOT / name) == expected, name
    report = {'status': 'SELECTION_COMPLETE_AWAITING_EXPLICIT_BATCH3_BUDGET_APPROVAL',
        'fresh_budget_confirmed': False, 'proposed_total_wall_seconds': 10800,
        'proposed_per_probe_wall_seconds': 3600, 'max_unique_new_sources': 3,
        'AP_probes_started': 0, 'new_source_moments': 0, 'new_SKR_evaluations': 0,
        'baseline_MB_count': 145, 'baseline_objectives_verified': 3770,
        'stored_ALT_OPT_matches_catalog_verified': 26, 'full_ALT_OPT_revalidation': 'NOT_RUN',
        'cache_only_coordinate_calls_for_selection': len(histories), 'final_selected_probes': selected,
        'probe3_nu_slice_5p475': {'values': [.165], 'bracket': updated_nu['bracket'],
            'missing_outer_value': .0825, 'missing_midpoint': None, 'still_unchecked_opposite_outer': .33},
        'safety_preflight': lease.receipt, 'sleep_lease_active_after_preflight': False,
        'execution_safety_supervisor_preflight': 'REQUIRED_AGAIN_AFTER_APPROVAL_BEFORE_AP',
        'protected_files_verified': len(manifest), 'protected_files_unchanged': True,
        'regression_tests_pass': True, 'git_diff_check_pass': True,
        'scientific_implementation_changed': False, 'no_interpolation': True,
        'frozen_spec_discrepancy': 'PREEXISTING_UNCHANGED',
        'publication': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
        'producer_sha256': io.digest(__file__), 'selection_wall_seconds': time.monotonic() - started}
    io.save_json(OUT / 'run_report.json', report)
    io.save_json(OUT / 'input_manifest_after_selection.json', manifest)
    lines = ['# Batch3: final selection only', '', report['status'], '',
        'Verified145 compatible source pairs and3770 existing objectives; existing ALT_OPT maximum26/26. '
        'No AP/newC,w/newSKR/full ALT_OPT run. Separate explicit budget approval is required by the current attachment.', '',
        '| Priority | nu_raw | VA | Reason |', '|---|---|---|---|']
    lines += [f"| {r['priority']} | {r['nu_raw']} | {r['V_A']} | {r['reason']} |" for r in selected]
    lines += ['', 'Original nu slice atVA5.475 contains onlynu=.165. Missing.0825 is an outer probe, '
        'not a midpoint; upper.33 remains unchecked. No midpoint generated on this slice, so retain original third.',
        'AC and temporary Sleep-prevention lease verified/released; recheck/reacquire and run native Job '
        'deadline/descendant-cleanup preflight immediately before AP after approval. No permanent power changes.',
        f"33 scoped regression tests and git diff --check PASS;{len(manifest)} protected files unchanged.",
        'Proposed NEW total10800s, per-probe<=3600s, max3 unique sources, sequential; no automatic timeout retry. '
        'Remaining budget must include full26distance postprocessing/ALT_OPT/cleanup. Not approved yet.',
        'Frozen-spec discrepancy and publication restrictions unchanged; no numerical/continuous/global convergence claim.']
    (OUT / 'run_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'baseline_MB_count', 'baseline_objectives_verified',
          'AP_probes_started', 'final_selected_probes', 'protected_files_verified')}, indent=2))


if __name__ == '__main__':
    main()
