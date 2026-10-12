"""Verify the 145-source finite catalog and plan three probes; AP is forbidden."""
from collections import Counter
from contextlib import ExitStack
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_mb_batch2 as previous
from src.cvqkd import gram_moments

ao, io, source, sweep = previous.ao, previous.io, previous.source, previous.sweep
BASE = previous.OUT
OUT = BASE.parent / 'batch_3_preparation'
REF = 21.9393102292
PRIORITY = ((.165, (5.45 + 5.475) / 2), (.165, (5.475 + 5.5) / 2),
            ((.165 + .16562500000000002) / 2, 5.5))
REASONS = (
    'Lower VA midpoint of the sampled22km maximum; tests the5.45/5.475 shoulder.',
    'Upper VA midpoint; shared22km/reference shoulder distinguishes the distance-dependent ordering.',
    'Nu midpoint on VA5.5 reference ridge; complementary shaping refinement, not another VA probe. '
    'Avoids the previously timed-out lower-nu midpoint(.16375,5.5).',
)


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def forbidden(*args, **kwargs):
    raise AssertionError('New source moments/AP are not authorized in batch3 preparation')


def classify_accuracy(reproduced, total_error_bound=None):
    if not reproduced:
        return 'NUMERICAL_RANKING_INCONCLUSIVE'
    return ('NUMERICALLY_RESOLVED_IMPROVEMENT' if total_error_bound is not None
            else 'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED')


def slice_rows(rows, variable, fixed):
    other = 'nu_raw' if variable == 'V_A' else 'V_A'
    return sorted((r for r in rows if float(r[other]).hex() == float(fixed).hex()),
                  key=lambda r: float(r[variable]))


def neighbors(rows, variable, fixed, value):
    exact = slice_rows(rows, variable, fixed)
    lower = max((r for r in exact if float(r[variable]) < value),
                key=lambda r: float(r[variable]), default=None)
    upper = min((r for r in exact if float(r[variable]) > value),
                key=lambda r: float(r[variable]), default=None)
    return [{'side': side, 'nu_raw': r['nu_raw'], 'V_A': r['V_A'], 'K': r['SKR'],
             'source_cache_key': r['source_cache_key']} for side, r in
            (('lower', lower), ('upper', upper)) if r is not None]


def export_slice(rows, best, mb):
    return [{'nu_raw': r['nu_raw'], 'V_A': r['V_A'], 'I_AB': r['I_AB'],
             'beta_I_AB': r['beta_I_AB'], 'chi_BE': r['chi_BE'], 'K': r['SKR'],
             'delta_K_from_best': r['SKR'] - best['SKR'],
             'nu_raw_hex': float(r['nu_raw']).hex(), 'V_A_hex': float(r['V_A']).hex(),
             'source_cache_key': r['source_cache_key'], 'source_path': r['source_path'],
             'source_provenance': mb[pair(r['nu_raw'], r['V_A'])]['_provenance']['status'],
             'evaluation_status': 'COMPATIBLE_EXACT_SOURCE_AND_OBJECTIVE'} for r in rows]


def main():
    if OUT.exists():
        raise SystemExit('Preparation already exists; preserve artifacts, do not overwrite')
    started, cpu_started = time.monotonic(), time.process_time()
    import torch
    torch.set_num_threads(1)
    config = source.unconstrained_config()
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            ao.MAX_REFINEMENT_STAGES, ao.MAX_BOUNDARY_EXPANSIONS) == (1e-8, 1e-6, 6, 4, 3)
    assert sweep.BASE_STARTS == (.1, .15, .3, .8)
    old_manifest = read_json(BASE / 'input_manifest_after.json')
    protected = dict(old_manifest)
    protected.update(io.raw_snapshot(p for directory in (BASE, previous.BASE,
        previous.previous.prior.CERT) for p in directory.rglob('*') if '__pycache__' not in p.parts))
    protected.update(io.raw_snapshot([Path(__file__), ROOT / 'docs/FINAL_MODEL_SPEC.md']))
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    checkpoint = read_json(BASE / 'objective_checkpoint.json')
    searches = read_json(BASE / 'cache_only_searches.json')
    inventory = io.read_csv(BASE / 'remaining_missing_exact_pairs.csv')
    old_ao = {float(r['L_km']): r for r in io.read_csv(BASE / 'alt_opt_validation.csv')}
    old_best = {float(r['L_km']): r for r in io.read_csv(BASE / 'previous_vs_new_optimum.csv')}
    stored_top = io.read_csv(BASE / 'top_two_candidates.csv')
    # Explicitly open and verify the78 added objective rows, not just the report.
    added = io.read_csv(BASE / 'exact_skr_26_distances.csv')
    assert len(added) == 78 and set(float(r['L_km']) for r in added) == set(sweep.DISTANCES_KM)
    assert len(searches) == 618
    OUT.mkdir()
    io.save_json(OUT / 'protected_input_manifest.json', protected)
    fresh, repeats, slice_searches, matrix, certificates, source_records = [], [], [], [], [], []
    objectives, maxima = {}, {}
    with ExitStack() as stack:
        # Guard BOTH public entry and underlying subprocess fallback; no worker is launched.
        stack.enter_context(patch.object(ao.ExactMBEvaluator, 'source_moments', forbidden))
        stack.enter_context(patch.object(gram_moments, '_fallback', forbidden))
        bank = source.load_source_payloads(config, previous.DIRS)
        mb = {pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])): p
              for p in bank.values() if float.fromhex(p['nu_mb_raw_hex']) > 0}
        catalog = io.read_csv(BASE / 'expanded_catalog.csv')
        assert len(mb) == len(catalog) == 145 and set(mb) == {pair(r['nu_raw'], r['V_A']) for r in catalog}
        for r in catalog:
            p = mb[pair(r['nu_raw'], r['V_A'])]
            for k in ('C', 'w'):
                assert float(r[k]) == float(p[k])
            assert r['source_cache_key'] == p['cache_key'] and r['ensemble_hash'] == p['ensemble_hash']
            c = source.candidate_from_payload(config, bank, 'MB', float(r['nu_raw']), float(r['V_A']))
            assert c is not None and c['source_cache_key'] == p['cache_key']
            source_records.append({**r, 'nu_raw_hex': p['nu_mb_raw_hex'], 'V_A_hex': p['V_A_hex'],
                'source_path': p['_path'], 'source_file_sha256': io.digest(ROOT / p['_path']),
                'canonical_source_cache_key': p['_provenance']['canonical_source_cache_key'],
                'provenance': p['_provenance']['status'], 'source_moment_route': p['source_moment_route'],
                'retained_precision_rows': bool(p.get('fallback_rows')), 'status': 'CURRENTLY_VERIFIED_PASS'})
        for distance in sweep.DISTANCES_KM:
            saved = checkpoint[str(distance)]
            channel = saved['identity']['identity']['channel']
            obj = ao.ExactObjective(config, channel, OUT, allow_new_source=False, source_cache_dirs=previous.DIRS)
            obj.restore_objective_rows(saved['rows'], saved['identity'])
            saved_pairs = [pair(r['nu_raw'], r['V_A']) for r in saved['rows']]
            assert len(saved_pairs) == len(set(saved_pairs)) and set(saved_pairs) <= set(mb)
            for key in mb:
                nu, va = map(float.fromhex, key)
                obj.register_catalog(nu, va)
                missing = obj.key(nu, va) not in obj.rows
                row = obj(nu, va)
                assert row['SKR'] == row['beta_I_AB'] - row['chi_BE']
                assert row['beta_I_AB'] == .95 * row['I_AB']
                if missing:
                    fresh.append(row)
            ranked = sorted(obj.rows.values(), key=lambda r: r['SKR'], reverse=True)
            assert len(ranked) == 145
            best, second = ranked[:2]
            assert best['SKR'] == float(old_best[distance]['new_K'])
            for rank, actual in enumerate((best, second), 1):
                recorded = next(r for r in stored_top if float(r['L_km']) == distance and int(r['rank']) == rank)
                assert pair(actual['nu_raw'], actual['V_A']) == pair(recorded['nu_raw'], recorded['V_A'])
                assert actual['SKR'] == float(recorded['SKR'])
            record = old_ao[distance]
            ao_row = obj(float(record['nu_raw_star']), float(record['V_A_star']))
            matches = ao_row['SKR'] == best['SKR'] == float(record['K'])
            certificates.append({'L_km': distance, 'candidate_count': len(ranked),
                'best_nu': best['nu_raw'], 'best_V_A': best['V_A'], 'best_K': best['SKR'],
                'runner_up_nu': second['nu_raw'], 'runner_up_V_A': second['V_A'], 'runner_up_K': second['SKR'],
                'gap': best['SKR'] - second['SKR'], 'AO_matches_catalog_maximum': matches,
                'objective_identity_sha256': obj.context_hash, 'AO_evidence': 'STORED_ORIGINAL_145_CATALOG_RUN_REVALIDATED',
                'continuous_global_optimum': 'NOT_PROVEN'})
            matrix.extend(ranked)
            objectives[distance], maxima[distance] = obj, best
            print(f'Catalog verified: L={distance}, candidates={len(ranked)}, AO match={matches}', flush=True)
        for r in added:
            actual = objectives[float(r['L_km'])](float(r['nu_raw']), float(r['V_A']))
            assert all(float(r[k]) == actual[k] for k in ('I_AB', 'beta_I_AB', 'chi_BE', 'SKR'))
        va_slice = slice_rows(list(objectives[22.].rows.values()), 'V_A', .165)
        nu_slice = slice_rows(list(objectives[22.].rows.values()), 'nu_raw', 5.475)
        va_best = max(va_slice, key=lambda r: r['SKR'])
        ref_rows = {float(r['V_A']).hex(): r for r in slice_rows(list(objectives[REF].rows.values()), 'V_A', .165)}
        comparison = [{ 'V_A': r['V_A'], 'nu_raw': .165, 'K_22km': r['SKR'],
            'K_reference': ref_rows[float(r['V_A']).hex()]['SKR'], 'source_cache_key': r['source_cache_key'],
            'delta_to_best22': r['SKR'] - maxima[22.]['SKR'],
            'delta_to_best_reference': ref_rows[float(r['V_A']).hex()]['SKR'] - maxima[REF]['SKR']} for r in va_slice]
        channel_checks = []
        for distance in (REF, 22.):
            recomputed = sweep.make_channel(config, distance)
            assert recomputed == objectives[distance].channel, 'Original channel replay differs'
            channel_checks.append({'L_km': distance, 'original_implementation_replay_matches': True, **recomputed})
            # Two independent calls from reconstructed ensembles/cached C,w, bypassing objective cache.
            for va in (5.425000000000001, 5.45, 5.475, 5.5, 5.525, 5.55):
                candidate = source.candidate_from_payload(config, bank, 'MB', .165, va)
                if candidate is None:
                    continue
                old = objectives[distance](.165, va)
                for repeat in (1, 2):
                    new = ao.evaluate_candidate(candidate, recomputed, config)
                    ao.finite_metrics(new)
                    repeats.append({'repeat': repeat, 'L_km': distance, 'nu_raw': .165, 'V_A': va,
                        **{k: new[k] for k in ('I_AB', 'beta_I_AB', 'chi_BE', 'SKR')},
                        **{'delta_' + k: new[k] - old[k] for k in ('I_AB', 'beta_I_AB', 'chi_BE', 'SKR')},
                        'subtraction_input_ulp_scale': math.ulp(new['beta_I_AB']) + math.ulp(new['chi_BE']),
                        'cancellation_ratio': (abs(new['beta_I_AB']) + abs(new['chi_BE'])) / abs(new['SKR']),
                        'source_cache_key': candidate['source_cache_key'], 'channel_hash': recomputed['channel_hash']})
        # Original generator replay at the two ridge distances and20/23/24, no multistart/update change.
        for distance in (20., REF, 22., 23., 24.):
            obj, best = objectives[distance], maxima[distance]
            for variable, fixed in (('V_A', best['nu_raw']), ('nu_raw', best['V_A'])):
                result = ao.adaptive_maximize_1d(variable=variable, fixed=fixed,
                    values=obj.catalog_values(variable, fixed), objective=obj)
                assert result['best']['SKR'] <= best['SKR']
                slice_searches.append({'L_km': distance, **result})
        # Dependencies derive from all618 actually executed calls; inventory is independently checked.
        deps = {}
        for index, search in enumerate(searches):
            for event in search['history']:
                if event['status'] != 'EXACT_SOURCE_MISSING':
                    continue
                nu, va = (search['fixed'], event['value']) if search['variable'] == 'V_A' else (event['value'], search['fixed'])
                key = pair(nu, va)
                dep = deps.setdefault(key, {'nu_raw': nu, 'V_A': va, 'requests': 0, 'searches': set(),
                    'distances': set(), 'directions': set(), 'events': []})
                dep['requests'] += 1
                dep['searches'].add(index)
                dep['distances'].add(search['L_km'])
                dep['directions'].add(search['variable'])
                dep['events'].append({'search_index': index, 'L_km': search['L_km'],
                    'direction': search['variable'], 'fixed': search['fixed'], 'bracket': search.get('bracket'),
                    'boundary_status': search.get('boundary_status')})
        assert len(deps) == len(inventory) == 54
        assert set(deps) == {pair(r['nu_raw'], r['V_A']) for r in inventory}
        for r in inventory:
            dep = deps[pair(r['nu_raw'], r['V_A'])]
            assert dep['requests'] == int(r['requests']) and dep['distances'] == set(json.loads(r['distances']))
        attempts = []
        ledger_roots = (ROOT / 'results/theta10_D55_alt_opt_closure_continuation',
                        ROOT / 'results/theta10_D55_alt_opt_convergence_validation', BASE.parent)
        for directory in ledger_roots:
            for path in directory.rglob('source_generation_ledger.json'):
                attempts.extend({**r, 'ledger_path': str(path.relative_to(ROOT)).replace('\\', '/')}
                                for r in read_json(path).get('attempts', []))
        ranking = []
        evaluator = objectives[22.].evaluator
        selected_keys = [pair(*p) for p in PRIORITY]
        for key, dep in deps.items():
            nu, va = float(dep['nu_raw']), float(dep['V_A'])
            assert key not in mb and source.candidate_from_payload(config, bank, 'MB', nu, va) is None
            identity = evaluator._source_identity(source.make_ensemble(config, 'MB', nu, va), nu, va)
            nearby, matched_ridges, bracketed = [], 0, False
            unique_events = {(e['L_km'], e['direction'], e['fixed']) for e in dep['events']}
            for distance, variable, fixed in sorted(unique_events):
                value = va if variable == 'V_A' else nu
                ns = neighbors(list(objectives[distance].rows.values()), variable, fixed, value)
                nearby.append({'L_km': distance, 'direction': variable, 'fixed': fixed, 'neighbors': ns})
                bracketed |= len(ns) == 2
                selected_fixed = maxima[distance]['nu_raw' if variable == 'V_A' else 'V_A']
                matched_ridges += int(float(selected_fixed).hex() == float(fixed).hex())
            prior_attempts = [{'status': r['status'], 'wall_seconds': r.get('wall_seconds'),
                               'timeout_seconds': r.get('timeout_seconds'), 'ledger_path': r['ledger_path']}
                              for r in attempts if pair(r['nu_raw'], r['V_A']) == key]
            timed_out = any(r['status'] == 'TIMEOUT' for r in prior_attempts)
            chosen = key in selected_keys
            representative = sorted(dep['distances'] & {20., REF, 22., 23., 24.})
            tier = (selected_keys.index(key) if chosen else 3 if key == pair(.15, 6.375)
                    else 4 if key == pair(.165, 5.5125) else 5 if key == pair(.165, 5.35)
                    else 6 if matched_ridges and bracketed else 7 if matched_ridges else 8)
            if timed_out:
                tier = 9
            ranking.append({'nu_raw': nu, 'V_A': va, 'nu_raw_hex': key[0], 'V_A_hex': key[1],
                'source_cache_key': source.json_hash(identity), 'ensemble_hash': identity['ensemble_hash'],
                'source_settings_sha256': source.json_hash(identity['source_settings']),
                'affected_distances': json.dumps(sorted(dep['distances'])), 'representative_distances': json.dumps(representative),
                'coordinate_directions': json.dumps(sorted(dep['directions'])), 'missing_requests': dep['requests'],
                'affected_coordinate_searches': len(dep['searches']), 'selected_ridge_slice_count': matched_ridges,
                'has_two_evaluated_neighbors': bracketed, 'neighbor_exact_K': json.dumps(nearby),
                'dependency_events': json.dumps(dep['events']), 'prior_attempts': json.dumps(prior_attempts),
                'prior_timeout': timed_out, 'priority_tier': tier,
                'selection_reason': REASONS[selected_keys.index(key)] if chosen else
                    'DEFER: known timeout' if timed_out else
                    'Short-distance20/21km VA midpoint with measured6.25/6.5 neighbors; wider spacing, alternative fourth priority.' if tier == 3 else
                    'Actual bracket/outer dependency; priority reflects selected-ridge coverage and complementary information, not request frequency.',
                'diagnostic_benefit': 'Adds an exact value to an existing bracket' if bracketed else
                    'Tests one missing outer direction; cannot alone establish two-sided closure',
                'runtime_risk': 'HIGH: prior timeout; no automatic retry' if timed_out else
                    'UNKNOWN per source; nearby completed AP probes took2148.906..3203.765s, other points timed out at3600s; no guaranteed60min completion',
                'source_availability': 'EXACT_SOURCE_MISSING', 'unknown_K': 'NOT_PREDICTED',
                'status': 'SELECTED_NOT_RUN' if chosen else 'DEFERRED_NOT_RUN'})
        ranking.sort(key=lambda r: (r['priority_tier'], -r['selected_ridge_slice_count'],
                                  -len(json.loads(r['representative_distances'])), r['nu_raw'], r['V_A']))
        for rank, row in enumerate(ranking, 1):
            row['rank'] = rank
        selected = [next(r for r in ranking if pair(r['nu_raw'], r['V_A']) == key) for key in selected_keys]
        assert len(selected) == len({r['source_cache_key'] for r in selected}) == 3
        assert all(not r['prior_timeout'] and r['status'] == 'SELECTED_NOT_RUN' for r in selected)
        # Validate each selected point is an EXACT original midpoint, not rounded decimal replacement.
        for r in selected:
            found = False
            for e in deps[pair(r['nu_raw'], r['V_A'])]['events']:
                ns = neighbors(list(objectives[e['L_km']].rows.values()), e['direction'], e['fixed'],
                               r['V_A'] if e['direction'] == 'V_A' else r['nu_raw'])
                if len(ns) == 2:
                    midpoint = (ns[0][e['direction']] + ns[1][e['direction']]) / 2
                    found |= float(midpoint).hex() == float(r[e['direction']]).hex()
            assert found, 'Selected point is not an original nearest-neighbor midpoint'
    # Pure stored-evidence comparison: enumerate the older snapshots independently.
    old_snapshots = (previous.previous.prior.CERT / 'catalog_exact_objectives.csv',
                     previous.BASE / 'objective_checkpoint.json', BASE / 'objective_checkpoint.json')
    comparison_batches = []
    old139 = io.read_csv(old_snapshots[0])
    for count, rows in ((139, [r for r in old139 if float(r['L_km']) == 22. and float(r['nu_raw']) > 0]),
                        (142, read_json(old_snapshots[1])['22.0']['rows']), (145, checkpoint['22.0']['rows'])):
        # Historical certification CSV contains scope duplicates: deduplicate exact binary64 pairs.
        unique = {pair(r['nu_raw'], r['V_A']): r for r in rows}
        assert len(unique) == count
        ordered = sorted(unique.values(), key=lambda r: float(r['SKR']), reverse=True)
        best, second = ordered[:2]
        baseline = comparison_batches[0]['best_K'] if comparison_batches else float(best['SKR'])
        prior = comparison_batches[-1]['best_K'] if comparison_batches else baseline
        comparison_batches.append({'catalog_count': count, 'best_nu': float(best['nu_raw']),
            'best_V_A': float(best['V_A']), 'best_K': float(best['SKR']),
            'runner_up_nu': float(second['nu_raw']), 'runner_up_V_A': float(second['V_A']),
            'runner_up_K': float(second['SKR']), 'gap': float(best['SKR']) - float(second['SKR']),
            'gain_vs_previous_batch': float(best['SKR']) - prior, 'gain_vs139': float(best['SKR']) - baseline})
    reproduced = all(r['delta_' + k] == 0 for r in repeats for k in ('I_AB', 'beta_I_AB', 'chi_BE', 'SKR'))
    classification = classify_accuracy(reproduced)
    io.write_csv(OUT / 'catalog_145_verification.csv', certificates)
    io.write_csv(OUT / 'source_145_provenance.csv', source_records)
    io.write_csv(OUT / 'catalog_145_exact_objectives.csv', matrix)
    io.write_csv(OUT / 'exact_va_slice_22km.csv', export_slice(va_slice, va_best, mb))
    io.write_csv(OUT / 'exact_nu_slice_22km.csv', export_slice(nu_slice, max(nu_slice, key=lambda r: r['SKR']), mb))
    io.write_csv(OUT / 'reference_distance_comparison.csv', comparison)
    io.write_csv(OUT / 'channel_reference_vs22.csv', channel_checks)
    io.write_csv(OUT / 'objective_reproducibility.csv', repeats)
    io.write_csv(OUT / 'missing_source_ranking.csv', ranking)
    io.write_csv(OUT / 'batch_3_selected_probes.csv', selected)
    io.write_csv(OUT / 'batch_1_batch_2_comparison.csv', comparison_batches)
    io.save_json(OUT / 'local_original_coordinate_searches.json', slice_searches)
    if fresh:
        io.write_csv(OUT / 'missing_objectives_completed_from_cached_sources.csv', fresh)
    report = {'status': 'CURRENTLY_VERIFIED_PASS_CACHE_ONLY_DIAGNOSTIC', 'catalog_MB_count': len(mb),
        'verified_objectives': len(matrix), 'missing_objectives_evaluated_from_existing_sources': len(fresh),
        'new_AP_sources': 0, 'AP_probes_started': 0, 'new_AP_authorized': False,
        'unchanged_evaluator_repeats': len(repeats), 'reproduced_bit_exact': reproduced,
        'numerical_accuracy_classification': classification, 'total_objective_error_bound': 'NOT_ESTABLISHED',
        'AO_matches_catalog_maximum': sum(r['AO_matches_catalog_maximum'] for r in certificates),
        'AO_scope': 'Existing original129-start145-catalog result revalidated against all3770 rows; not a new full AO run',
        'original_local_coordinate_calls_replayed': len(slice_searches), 'missing_unique_sources': len(deps),
        'stored_coordinate_calls': len(searches), 'stored_coordinate_status_counts': dict(Counter(s['status'] for s in searches)),
        'best22': maxima[22.], 'best_reference': maxima[REF],
        'VA22_nearest_neighbors': neighbors(va_slice, 'V_A', .165, va_best['V_A']),
        'nu22_evaluated_values': [r['nu_raw'] for r in nu_slice],
        'nu22_local_bracket': next(s['bracket'] for s in slice_searches if s['L_km'] == 22. and s['variable'] == 'nu_raw'),
        'selected_probes': selected, 'batch_comparison': comparison_batches,
        'continuous_convergence': 'NOT_ESTABLISHED', 'global_optimality': 'NOT_PROVEN',
        'original_science_settings_unchanged': True, 'no_interpolation': True,
        'protected_files_count': len(protected), 'frozen_spec_sha256': io.digest(ROOT / 'docs/FINAL_MODEL_SPEC.md'),
        'frozen_spec_discrepancy': 'PREEXISTING_UNCHANGED; diagnostic-only, no model or lifecycle promotion',
        'publication': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS', 'producer_sha256': io.digest(__file__)}
    audit = ['# Numerical accuracy audit', '', classification, '',
        f'{len(repeats)} originalGH8/directZ-minus evaluations from compatible cached C,w; bit-exact repeats={reproduced}.',
        'Independent here means bypassing the objective cache and reconstructing the original inputs; it is NOT an independent arithmetic algorithm.',
        f"Maximum delta K={max(abs(r['delta_SKR']) for r in repeats)}; maximum subtraction input-ULP scale={max(r['subtraction_input_ulp_scale'] for r in repeats)}.",
        'The input-ULP scale characterizes final subtraction only, NOT errors in computing MI, C,w, eigenvalues or entropies.',
        '', '## Source checks and retained evidence',
        'All145 source identities,256 support, binary64 parameters, ensemble hashes, source settings and exact implementation/newline aliases verified.',
        'Source precision ladder is1050/1250/1450. Original full_support_c4_worker.py requires final1250/1450 rows resolved with rank256 and C,w agreement within1e-7+1e-6*max(abs(C,w)).',
        'The production cache producer discards per-precision fallback_rows and residual diagnostics when serializing C,w. Current new-probe receipts retain the rejected complex128 fast gate but NOT the AP per-precision observables.',
        'The fast reconstruction residual belongs to the rejected fast route: small residual with nonpositive computed eigenvalues is NOT an AP accuracy bound.',
        'Thus the unchanged worker acceptance rule is provenance-supported, but measured per-precision error at these exact145 sources cannot be reconstructed from the retained payload alone. No new AP is permitted.',
        '', '## MI/quadrature and Holevo evidence',
        'Existing tests/test_exact_mb_test2a.py provides deterministic full/product GH8 equivalence and bit-exact repeats on its own fixture. Only fixed-order tests are run here; no new quadrature sweep.',
        'Existing results/exact_mb_test2a/gh_convergence.json and joint_mb_va_global/gh_convergence.csv cover other ensembles/channel fixtures; not a bound for the22km ridge.',
        'Existing redesigned_baseline_global_mb_va/continuation_final_summary.json reports top10 GH8-to64 MI delta1.498e-10, but uses w0=.10 and a different channel/K. It does not bind the new5.475/5.425 sources or current22/reference context; no generic error guarantee is imported.',
        'Original evaluate_candidate invokes _holevo_from_source_moments with maximize_full_interval=False and rejects a mode other than zstar. Existing synthetic direct-Z and physicality tests are relevant software evidence, not high-precision entropy/covariance error enclosures.',
        'Original channel replay matches saved reference/22 dictionaries exactly. No precision/order/formula/security variant used.',
        '', '## Interpretation',
        'Repeated ordering and final subtraction precision do not establish a rigorous total objective error bound. In particular epsilon_opt=1e-8 and physicality tolerances are not total objective accuracy bounds.',
        'The1e-7 gains are reproduced under the frozen evaluator; their distinction from ALL numerical errors and physical significance remain unproven.',
        'Further probes can characterize coverage/sensitivity, not remedy absent total error control by themselves. No continuous fit, extrapolation, predicted gain or convergence claim.']
    (OUT / 'numerical_accuracy_audit.md').write_text('\n'.join(audit) + '\n', encoding='utf-8')
    checks = []
    for pattern in ('test_windows_sleep_safe_supervision.py', 'test_alt_opt_provenance_and_stopping.py',
                    'test_mb_sleep_safe_expansion.py', 'test_mb_batch2.py', 'test_mb_batch3_preparation.py'):
        done = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
                              cwd=ROOT, capture_output=True, text=True)
        checks.append({'pattern': pattern, 'returncode': done.returncode, 'output': done.stdout + done.stderr})
    fixed_checks = [ 'tests.test_exact_mb_test2a.DeterministicMBMITests.test_deterministic_mi_repeats_and_full_matches_product',
                    'tests.test_holevo_interval.HolevoIntervalTests.test_primary_uses_exact_zstar_without_interval_maximization']
    done = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', '-v', *fixed_checks], cwd=ROOT, capture_output=True, text=True)
    checks.append({'pattern': 'fixed_GH8_and_direct_Z_tests', 'returncode': done.returncode, 'output': done.stdout + done.stderr})
    io.save_json(OUT / 'regression_tests.json', checks)
    assert all(r['returncode'] == 0 for r in checks), 'Regression failure: inspect regression_tests.json'
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    for name, digest in protected.items():
        assert io.digest(ROOT / name) == digest, name
    report.update(tests_pass=True, git_diff_check_pass=True, protected_files_unchanged=True,
                  diagnostic_wall_seconds=time.monotonic() - started, diagnostic_CPU_seconds=time.process_time() - cpu_started)
    io.save_json(OUT / 'input_manifest_after.json', protected)
    io.save_json(OUT / 'batch_3_preparation_report.json', report)
    lines = ['#145 MB exact catalog: cache-only validation and Batch3 plan', '', report['status'], '',
        f"Verified145 pairs and{len(matrix)} objectives, AO/catalog matches={report['AO_matches_catalog_maximum']}/26 (existing AO, freshly verified catalog).",
        f"Original evaluator repeats={len(repeats)}, missing objective completions={len(fresh)}, new AP=0.",
        'Full26-distance maxima/runner-up/gaps in catalog_145_verification.csv; exact identities in source_145_provenance.csv.',
        '', '## Answers to the10 requested questions',
        f"1. Existing ALT_OPT attains the current145-catalog maximum at{report['AO_matches_catalog_maximum']}/26 distances; no new full multistart AO execution.",
        f"2.22km best currently exact-tested pair=({va_best['nu_raw']},{va_best['V_A']}), K={va_best['SKR']}.",
        f"3. Nearest evaluated VA neighbors: {json.dumps(report['VA22_nearest_neighbors'])}.",
        '4. Both immediate VA neighbors and further available shoulders are lower: sampled local maximum. Not a continuous maximum certificate.',
        f"5. Reference best=({maxima[REF]['nu_raw']},{maxima[REF]['V_A']}), K={maxima[REF]['SKR']}. Distance changes channel inputs: exact original reference/22 replay and pairwise ordering saved; no evidence of a coding error.",
        f'6. {classification}: all24 reevaluations reproduce stored metrics, but no compatible rigorous total-objective bound exists; gains are numeric ordering only.',
        '7.54 unique missing pairs, independently recovered from618 calls;312 boundary/306 bracket-source-missing invocations are different units.',
        f'8. Exactly3 missing original midpoint ensembles: {PRIORITY!r}; binary64 hashes in batch_3_selected_probes.csv. NOT_RUN.',
        '9. TwoVA shoulders refine the22km peak (upper shared with reference); one nu midpoint on5.5 reference ridge gives complementary shaping coverage. No guaranteed improvement or closure.',
        '10. Conditionally justified for targeted coverage/sensitivity, not another expensive run merely to reproduce the finite maximum. Total-error evidence is still insufficient to certify tiny physical gains. Stop: no new AP authorized.',
        '', '## Both directions and alternative distances',
        f"AtVA5.475 the only evaluated nu={report['nu22_evaluated_values']}; bracket={report['nu22_local_bracket']}. Original lower outer request(.0825,5.475) is missing. Opposite(.33,5.475) is not yet requested because the original search stops on the missing lower side; it remains unchecked, not closed.",
        'Selected third nu midpoint(.16531250000000003,5.5) closes neither side atVA5.475. It is selected because a true two-sided local bracket already exists onVA5.5 with fine neighboring nu values;(.16375,5.5) is deferred for prior3600s timeout.',
        '20/21 alternative(.15,6.375) ranks next, between measured6.25/6.5 (20km currentrunner-up/best); broader sampling and no cross-reference shaping information.23km(.165,5.35) and24km(.15,5.25) remain ranked alternatives with measured neighbors; unknownK is never predicted.',
        'Missing_source_ranking.csv provides all54 keys/hex representations, unique affected-call counts, original events, distances, measured neighborK, timeout history and qualitative runtime risk.',
        '', '##139 ->142 ->145 at22km',
        '| Catalog | best nu | best VA | K | runner-up gap | increment | cumulative |',
        '|---|---|---|---|---|---|---|']
    lines += [f"|{r['catalog_count']}|{r['best_nu']}|{r['best_V_A']}|{r['best_K']}|{r['gap']}|{r['gain_vs_previous_batch']}|{r['gain_vs139']}|" for r in comparison_batches]
    lines += ['', 'Second measured increment is smaller than the first, but two increments do not establish an asymptotic diminishing-gain law or predict Batch3.',
        'No source/scientific/optimization/settings changes or interpolation.145 catalog unchanged. Existing source moments reused only for24 diagnostic reevaluations and any missing valid objectives; all prior artifacts hash-protected.',
        f"Tests/diff PASS;{len(protected)} protected files unchanged. Diagnostic wall={report['diagnostic_wall_seconds']}s, main-process CPU={report['diagnostic_CPU_seconds']}s (test subprocess CPU excluded).",
        'Frozen-spec historical hash discrepancy remains PREEXISTING_UNCHANGED; no publication/training/test/baseline/threshold approval. Stop after planning.']
    (OUT / 'batch_3_preparation_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'catalog_MB_count', 'verified_objectives',
          'reproduced_bit_exact', 'numerical_accuracy_classification', 'AO_matches_catalog_maximum', 'missing_unique_sources', 'AP_probes_started')}, indent=2))


if __name__ == '__main__':
    main()
