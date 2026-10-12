"""Reconcile exact identities and reconstruct P1/P2; no AP or fresh SKR/AO."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_objective_B_pilot as prior
from scripts import recover_theta10_D55_objective_B_postprocess as storage

saved, provenance = prior.saved, prior.provenance
OUT = prior.BASE / 'b2_P1_upper_refinement'
INPUT = prior.OUT / 'postprocess_recovery'
NU, VA = .165, 5.50625
KEY = 'dbb7a2a7024f84f97c455b0b3b564e9a307f369b362f80e055dfbf1e5d49497f'


def write_json(name, value):
    (OUT / name).write_text(storage.checked_json(value), encoding='utf-8')


def write_csv(name, rows):
    with patch.object(saved, 'OUT', OUT):
        saved.write_csv(name, rows)


def merge_source(bank, record):
    p, verification = record['payload'], record['verification']
    key = saved.pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex']))
    if key in bank:
        previous = bank[key][0]
        assert verification['canonical_source_identity'] == previous['verification']['canonical_source_identity'], 'Binary64 identity collision'
        assert (p['C'], p['w']) == (previous['payload']['C'], previous['payload']['w']), 'Conflicting duplicate source moments'
    bank.setdefault(key, []).append(record)


def reconcile(config):
    settings = provenance.source_settings(config)
    bank, excluded, uniform_count = {}, [], 0
    paths = sorted((ROOT / 'results').glob('**/exact_source_cache/*.json'))
    for path in paths:
        try:
            p = saved.read(path)
            verification = provenance.verify_source_payload(p, settings)
            n, v = float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])
            assert p['C'] >= 0 and p['w'] >= 0
            candidate = saved.source.candidate_from_payload(config,
                {p['ensemble_hash']: {**p, '_path': path.relative_to(ROOT).as_posix(), '_provenance': verification}},
                'MB' if n > 0 else 'Uniform', n, v)
            assert candidate is not None, 'Ensemble could not be reconstructed'
        except (ValueError, KeyError, TypeError, AssertionError) as exc:
            excluded.append({'path': path.relative_to(ROOT).as_posix(), 'reason': str(exc)})
            continue
        if n == 0:
            uniform_count += 1
            continue
        merge_source(bank, {'payload': p, 'verification': verification, 'path': path.relative_to(ROOT).as_posix(),
            'sha256': saved.sweep.sha256(path)})
    old = saved.read(saved.BASE / 'objective_checkpoint.json')
    baseline = {saved.pair(r['nu_raw'], r['V_A']) for r in old[str(saved.REF)]['rows']}
    assert len(baseline) == 147 and len(bank) == 149
    additions = {saved.pair(.25, 2.), saved.pair(.165, 5.49375)}
    assert set(bank) - baseline == additions and baseline <= set(bank)
    assert len({rs[0]['verification']['canonical_source_cache_key'] for rs in bank.values()}) == 149
    assert len({rs[0]['payload']['ensemble_hash'] for rs in bank.values()}) == 149
    for distance, entry in old.items():
        assert {saved.pair(r['nu_raw'], r['V_A']) for r in entry['rows']} == baseline
    extra = next(rs for key, rs in bank.items() if key == saved.pair(.25, 2.))
    assert any(r['path'] == 'results/exact_mb_asymptotic/exact_source_cache/133063dc28f59ac4a75205ec41c12906ab149aa4111e5c5c2f25dd4b9628abd4.json' for r in extra)
    assert saved.read(prior.BASE / 'objective_B_verification.json')['additional_reference_existing_source_checks'][0]['source_cache_key'] == extra[0]['payload']['cache_key']
    new = bank[saved.pair(.165, 5.49375)][0]
    assert new['payload']['cache_key'] == prior.KEY
    assert saved.read(prior.OUT / 'source_checkpoint.json')['cache_key'] == prior.KEY
    roster = []
    for key, records in sorted(bank.items()):
        p = records[0]['payload']
        roster.append({'nu_raw_hex': key[0], 'V_A_hex': key[1], 'cache_key': p['cache_key'],
            'canonical_cache_key': records[0]['verification']['canonical_source_cache_key'],
            'ensemble_hash': p['ensemble_hash'], 'C': p['C'], 'w': p['w'], 'support_size': p['support_size'],
            'origin': 'BASELINE147' if key in baseline else 'PREEXISTING_OUTSIDE147' if key == saved.pair(.25, 2.) else 'NEW_COMPLETED_B2_A',
            'physical_file_copies': len(records), 'provenance_files': [{k: r[k] for k in ('path', 'sha256')} for r in records]})
    return bank, roster, {'cache_files_scanned': len(paths), 'Uniform_files_not_counted_as_MB': uniform_count,
        'excluded_files': excluded, 'unique_MB_sources': len(bank), 'baseline_sources': len(baseline),
        'consistent_duplicate_MB_files_not_double_counted': sum(len(rs) - 1 for rs in bank.values()),
        'conflicting_duplicate_identities': 0, 'incompatible_or_incomplete_sources_counted': 0}


def main():
    if OUT.exists():
        raise SystemExit('Refuse to overwrite existing upper-refinement preparation')
    prior.torch.set_num_threads(1)
    prior.verify_protected()
    protected = saved.read(prior.OUT / 'protected_input_manifest.json')
    for path in prior.OUT.rglob('*'):
        if path.is_file():
            protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    for path in (Path(__file__), ROOT / 'tests/test_P1_upper_refinement_preparation.py'):
        protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    config = saved.source.unconstrained_config()
    OUT.mkdir()
    with ExitStack() as guards:
        for obj, name in ((saved.ao.ExactMBEvaluator, 'source_moments'), (prior.gram_moments, '_fallback'),
            (saved.ao, 'evaluate_candidate'), (saved.sweep, 'make_channel'), (saved.sweep, 'run_single_distance_ao')):
            guards.enter_context(patch.object(obj, name, prior.preparation.forbidden))
        bank, roster, reconciliation = reconcile(config)
        checkpoints = saved.read(INPUT / 'objective_checkpoint.json')
        selected = saved.rows(INPUT / 'optimized_skr_26_distances.csv')
        runs = saved.read(INPUT / 'cache_only_runs.json')
        searches = saved.read(INPUT / 'cache_only_searches.json')
        aligned, _ = saved.audit.align_searches(runs, searches)
        assert len(runs) == 129 and len(aligned) == 618
        assert [e['L_km'] for e in checkpoints] == list(saved.sweep.DISTANCES_KM)
        reference_obj, rankings = None, {}
        for entry, chosen in zip(checkpoints, selected):
            d = entry['L_km']
            obj = saved.ao.ExactObjective(config, entry['identity']['identity']['channel'], OUT,
                allow_new_source=False, source_cache_dirs=prior.DIRS)
            assert obj.restore_objective_rows(entry['rows'], entry['identity']) == 149
            index = {saved.pair(r['nu_raw'], r['V_A']): r for r in entry['rows']}
            assert len(index) == len(entry['rows']) == 149 and set(index) == set(bank)
            for key, row in index.items():
                assert row['source_cache_key'] in {r['payload']['cache_key'] for r in bank[key]}
                assert row['SKR'] == row['beta_I_AB'] - row['chi_BE']
                assert abs(row['beta_I_AB'] - .95 * row['I_AB']) < 5e-15
                obj.register_catalog(row['nu_raw'], row['V_A'])
            maximum = max(index.values(), key=lambda r: r['SKR'])
            genuine = max((r for r in runs if r['L_km'] == d), key=lambda r: r['final']['SKR'])
            assert genuine['final']['SKR'] == float(chosen['best_SKR']) == maximum['SKR']
            assert saved.pair(chosen['nu_raw'], chosen['V_A']) == saved.pair(maximum['nu_raw'], maximum['V_A'])
            rankings[d] = maximum
            if d == saved.REF:
                reference_obj = obj
        assert len(rankings) == len(selected) == 26
        coords = [saved.ao.adaptive_maximize_1d(variable=v, fixed=f, values=reference_obj.catalog_values(v, f), objective=reference_obj)
            for v, f in (('V_A', NU), ('nu_raw', 5.5))]
        for result in coords:
            historical = next(s for s in searches if s['L_km'] == saved.REF and s['role'] == 'SELECTED_FINAL' and s['variable'] == result['variable'])
            assert result['history'] == historical['history'] and result['bracket'] == historical['bracket']
        assert reference_obj.unique_exact_evaluations == 0
        assert coords[0]['bracket'] == [5.49375, 5.5125]
        assert [r['value'] for r in coords[0]['source_missing']] == [5.496875, VA]
        assert coords[0]['refinement_stages'] == 1 and coords[0]['refinement_status'] == 'SOURCE_MISSING_REFINEMENT'
        ensemble = saved.source.make_ensemble(config, 'MB', NU, VA)
        identity = reference_obj.evaluator._source_identity(ensemble, NU, VA)
        assert saved.ao.json_hash(identity) == KEY
        assert saved.pair(NU, VA) not in bank
        plan = {'nu_raw': NU, 'V_A': VA, 'nu_raw_hex': NU.hex(), 'V_A_hex': VA.hex(), 'compatible_cache_key': KEY,
            'original_source_identity': identity, 'P1_request_ordinal': 2, 'required_by_original_search': True,
            'source_exists': False, 'fresh_AP_authorized': False, 'maximum_new_attempts': 1,
            'proposed_total_seconds': 7200, 'proposed_outer_AP_ceiling_seconds': 5400,
            'postprocessing_cleanup_reserve_seconds': 1800, 'original_internal_fallback_timeout_seconds': 3600,
            'effective_original_AP_timeout_at_most_seconds': 3600, 'timeout_change_authorized': False,
            'other_AP_allowed': False, 'retry_allowed': False}
    lease = prior.safe.AwakeOnAC()
    with lease:
        samples = []
        for _ in range(3):
            samples.append(lease.power.read())
            time.sleep(.25)
        assert all(prior.safe.safe_power(s) for s in samples)
    write_json('catalog_reconciliation.json', {'summary': reconciliation, 'roster': roster})
    write_json('confirmed_candidate.json', plan)
    write_json('live_reference_searches.json', coords)
    diagnostics = [{**saved.audit.diagnostic({**s, 'L_km': saved.REF}, list(reference_obj.rows.values())),
        'candidate_history': s['history'], 'scope': 'LIVE_CACHE_ONLY_NO_FRESH_SKR_OR_AP'} for s in coords]
    write_csv('reference_P1_refinement.csv', [diagnostics[0]])
    write_csv('coordinate_search_status.csv', diagnostics)
    write_csv('execution_ledger.csv', [{'attempts': 0, 'status': 'NOT_RUN_AWAITING_FRESH_COMPUTE_APPROVAL',
        'nu_raw': NU, 'V_A': VA, 'source_cache_key': KEY, 'wall_seconds': 'NOT_RUN', 'CPU_seconds': 'NOT_RUN'}])
    write_csv('ao_multistart_recheck.csv', [{'L_km': r['L_km'], 'start_id': r['start_id'],
        'nu_raw': r['final']['nu_raw'], 'V_A': r['final']['V_A'], 'K': r['final']['SKR'], 'status': r['status'],
        'matches_saved_catalog': r['final']['SKR'] == rankings[r['L_km']]['SKR'],
        'scope': 'EXISTING_GENUINE_AO_VALIDATED_NOT_FRESH_AO'} for r in runs])
    assert all(saved.sweep.sha256(ROOT / n) == h for n, h in protected.items())
    write_json('protected_input_manifest.json', protected)
    verification = {'status': 'CURRENTLY_VERIFIED_PASS_SCIENTIFIC_PREFLIGHT_ONLY', **reconciliation,
        'protected_count': len(protected), 'fresh_AP_authorized': False, 'new_AP_attempts': 0,
        'new_source_moments': 0, 'new_SKR_evaluations': 0, 'fresh_AO_runs': 0, 'live_coordinate_calls': 2,
        'validated_saved_metrics': 3874, 'validated_saved_AO_starts': 129, 'saved_catalog_maximum_matches': 26,
        'completed_coordinate_searches': 0, 'AC_samples': samples, 'temporary_Sleep_lease': lease.receipt,
        'native_AP_Job_readiness': 'RECHECK_AFTER_FRESH_APPROVAL_BEFORE_AP',
        'frozen_historical_hash_discrepancy': 'PREEXISTING_UNCHANGED', 'scientific_method_changed': False,
        'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    write_json('preflight_verification.json', verification)
    print(json.dumps(verification), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
