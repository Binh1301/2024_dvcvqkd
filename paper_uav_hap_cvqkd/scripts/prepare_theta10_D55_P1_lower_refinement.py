"""Reconcile catalog150 and replay original P1 requests; never generate AP/SKR."""
from contextlib import ExitStack
import json
import math
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_P1_upper_refinement as upper

saved, prior = upper.saved, upper.prior
provenance, storage = upper.prep.provenance, upper.prep.storage
OUT = upper.prep.OUT.parent / 'b2_P1_lower_refinement'
INPUT = upper.OUT
DIRS = upper.DIRS
NU, VA = .165, 5.496875
KEY = '9b0e009b708f2099ccf64c1bfdcf1d6d121cf2e85f59a93f5ca6cda53c2e7db3'


def write_json(name, data):
    (OUT / name).write_text(storage.checked_json(data), encoding='utf-8')


def write_csv(name, rows):
    with patch.object(saved, 'OUT', OUT):
        saved.write_csv(name, rows)


def reconcile(config):
    settings = provenance.source_settings(config)
    paths = sorted((ROOT / 'results').glob('**/exact_source_cache/*.json'))
    bank, uniform = {}, 0
    for path in paths:
        payload = saved.read(path)
        verified = provenance.verify_source_payload(payload, settings)
        assert math.isfinite(payload['C']) and math.isfinite(payload['w'])
        assert payload['C'] >= 0 and payload['w'] >= 0 and payload['support_size'] == 256
        n, v = float.fromhex(payload['nu_mb_raw_hex']), float.fromhex(payload['V_A_hex'])
        candidate = saved.source.candidate_from_payload(config,
            {payload['ensemble_hash']: {**payload, '_path': path.relative_to(ROOT).as_posix(), '_provenance': verified}},
            'MB' if n > 0 else 'Uniform', n, v)
        assert candidate is not None
        if n == 0:
            uniform += 1
            continue
        upper.prep.merge_source(bank, {'payload': payload, 'verification': verified,
            'path': path.relative_to(ROOT).as_posix(), 'sha256': saved.sweep.sha256(path)})
    reference = next(e for e in saved.read(INPUT / 'objective_checkpoint.json') if e['L_km'] == saved.REF)
    assert len(bank) == 150 and set(bank) == {saved.pair(r['nu_raw'], r['V_A']) for r in reference['rows']}
    assert len({r[0]['verification']['canonical_source_cache_key'] for r in bank.values()}) == 150
    assert saved.pair(NU, VA) not in bank, 'Do not regenerate a valid source'
    roster = [{'nu_raw_hex': key[0], 'V_A_hex': key[1], 'C': records[0]['payload']['C'],
        'w': records[0]['payload']['w'], 'canonical_cache_key': records[0]['verification']['canonical_source_cache_key'],
        'files': [{n: r[n] for n in ('path', 'sha256')} for r in records]}
        for key, records in sorted(bank.items())]
    return bank, roster, {'unique_MB_sources': len(bank), 'cache_files_scanned': len(paths),
        'Uniform_files_not_counted_as_MB': uniform, 'duplicate_MB_files_not_double_counted': sum(len(r)-1 for r in bank.values()),
        'incompatible_or_incomplete_sources_counted': 0, 'source_already_present': False}


def main():
    if OUT.exists():
        raise SystemExit('Preparation exists; preserve it, no overwrite')
    prior.torch.set_num_threads(1)
    protected = saved.read(INPUT / 'protected_input_manifest.json')
    for directory in (INPUT, upper.CACHE):
        for path in directory.rglob('*'):
            if path.is_file():
                protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    for path in (Path(__file__), ROOT / 'tests/test_P1_lower_refinement_preparation.py'):
        protected[path.relative_to(ROOT).as_posix()] = saved.sweep.sha256(path)
    assert all(saved.sweep.sha256(ROOT/n) == h for n, h in protected.items())
    assert (saved.ao.MAX_AO_ITERATIONS, saved.ao.K_TOLERANCE, saved.ao.PARAMETER_TOLERANCE,
        saved.ao.MAX_REFINEMENT_STAGES) == (6, 1e-8, 1e-6, 4)
    config = saved.source.unconstrained_config()
    OUT.mkdir()
    with ExitStack() as guards:
        for obj, name in ((saved.ao.ExactMBEvaluator, 'source_moments'), (prior.gram_moments, '_fallback'),
            (saved.ao, 'evaluate_candidate'), (saved.sweep, 'make_channel'), (saved.sweep, 'run_single_distance_ao')):
            guards.enter_context(patch.object(obj, name, prior.preparation.forbidden))
        bank, roster, reconciliation = reconcile(config)
        entries = saved.read(INPUT / 'objective_checkpoint.json')
        selections = saved.rows(INPUT / 'optimized_skr_26_distances.csv')
        runs = saved.read(INPUT / 'cache_only_runs.json')
        searches = saved.read(INPUT / 'cache_only_searches.json')
        assert [e['L_km'] for e in entries] == list(saved.sweep.DISTANCES_KM)
        assert len(runs) == 129 and len(selections) == 26
        for entry, chosen in zip(entries, selections):
            obj = saved.ao.ExactObjective(config, entry['identity']['identity']['channel'], OUT,
                allow_new_source=False, source_cache_dirs=DIRS)
            assert obj.restore_objective_rows(entry['rows'], entry['identity']) == 150
            assert {saved.pair(r['nu_raw'], r['V_A']) for r in entry['rows']} == set(bank)
            for row in entry['rows']:
                assert row['source_cache_key'] in {r['payload']['cache_key'] for r in bank[saved.pair(row['nu_raw'],row['V_A'])]}
                assert row['SKR'] == row['beta_I_AB'] - row['chi_BE']
                assert abs(row['beta_I_AB'] - .95 * row['I_AB']) < 5e-15
                obj.register_catalog(row['nu_raw'], row['V_A'])
            best = max(entry['rows'], key=lambda r:r['SKR'])
            terminal = max((r for r in runs if r['L_km'] == entry['L_km']), key=lambda r:r['final']['SKR'])
            assert terminal['final']['SKR'] == float(chosen['best_SKR']) == best['SKR']
            assert saved.pair(chosen['nu_raw'],chosen['V_A']) == saved.pair(best['nu_raw'],best['V_A'])
            if entry['L_km'] == saved.REF:
                reference_obj = obj
        coords = [saved.ao.adaptive_maximize_1d(variable=v, fixed=f,
            values=reference_obj.catalog_values(v,f), objective=reference_obj)
            for v,f in (('V_A',NU),('nu_raw',5.5))]
        for result in coords:
            old = next(s for s in searches if s['L_km'] == saved.REF and s['role'] == 'SELECTED_FINAL' and s['variable'] == result['variable'])
            assert result['history'] == old['history'] and result['bracket'] == old['bracket']
        assert reference_obj.unique_exact_evaluations == 0
        p1 = coords[0]
        assert p1['best_value'] == 5.5 and p1['best_K'] == .07798099387393764
        assert p1['bracket'] == [5.49375,5.50625]
        assert [r['value'] for r in p1['source_missing']] == [VA,5.503125]
        assert not saved.ao.coordinate_search_complete(p1)
        identity = reference_obj.evaluator._source_identity(saved.source.make_ensemble(config,'MB',NU,VA),NU,VA)
        assert saved.ao.json_hash(identity) == KEY
        reference = [{'L_km':saved.REF, **r} for r in reference_obj.rows.values()
            if r['nu_raw'] == NU and r['V_A'] in (5.49375,5.5,5.50625)]
    lease = prior.safe.AwakeOnAC()
    with lease:
        samples = []
        for _ in range(3):
            samples.append(lease.power.read())
            time.sleep(.25)
        assert all(prior.safe.safe_power(s) for s in samples)
    plan = {'nu_raw':NU,'V_A':VA,'nu_raw_hex':NU.hex(),'V_A_hex':VA.hex(),'compatible_cache_key':KEY,
        'original_source_identity':identity,'P1_request_ordinal':1,'source_exists':False,'fresh_AP_authorized':False,
        'maximum_new_attempts':1,'proposed_total_seconds':7200,'proposed_outer_AP_ceiling_seconds':5400,
        'postprocessing_cleanup_reserve_seconds':1800,'original_internal_fallback_timeout_seconds':3600,
        'other_AP_allowed':False,'retry_allowed':False}
    write_json('catalog_reconciliation.json', {'summary':reconciliation,'roster':roster})
    write_json('confirmed_candidate.json', plan)
    write_json('live_reference_searches.json', coords)
    write_json('protected_input_manifest.json', protected)
    write_csv('reference_P1_comparison.csv', reference)
    write_csv('execution_ledger.csv', [{'AP_attempts':0,'nu_raw':NU,'V_A':VA,'status':'NOT_RUN_AWAITING_FRESH_EXECUTION_APPROVAL','cache_key':KEY}])
    diagnostic = saved.audit.diagnostic({**p1,'L_km':saved.REF},list(reference_obj.rows.values()))
    write_json('preflight_verification.json', {'status':'CURRENTLY_VERIFIED_PASS_SCIENTIFIC_PREFLIGHT_ONLY',
        **reconciliation,'protected_count':len(protected),'saved_exact_metrics_verified':3900,
        'actual_saved_AO_starts_verified':129,'saved_catalog_matches':26,'original_live_coordinate_calls':2,
        'new_AP_attempts':0,'new_source_moments':0,'new_SKR_evaluations':0,'fresh_AO_runs':0,
        'fresh_AP_authorized':False,'P1_diagnostic':diagnostic,'AC_samples':samples,'temporary_Sleep_lease':lease.receipt,
        'scientific_method_changed':False,'frozen_historical_hash_discrepancy':'PREEXISTING_UNCHANGED',
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'})
    print(json.dumps({'status':'CURRENTLY_VERIFIED_PASS_SCIENTIFIC_PREFLIGHT_ONLY',**reconciliation,
        'P1_bracket':p1['bracket'],'next_original_requests':[r['value'] for r in p1['source_missing']],
        'candidate_key':KEY,'protected_count':len(protected),'AP_attempts':0,'fresh_AP_authorized':False}),flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
