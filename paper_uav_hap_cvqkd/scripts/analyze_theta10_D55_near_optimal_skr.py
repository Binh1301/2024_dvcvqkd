"""Read stored objectives only: no scientific evaluator, source generation or AO."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exact_cache_provenance import canonical_bytes, json_hash, verify_source_payload

BASE = ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization'
INPUT = BASE / 'b2_P1_lower_refinement/minimal_run'
OUT = BASE / 'near_optimal_skr_analysis'
REF = 21.9393102292
DISTANCES = [20., 21., REF, 22., 23., 24., 25., 25.5, 26., 26.5, 27., 27.5,
             28., 29., 30., 30.5, 31., 31.5, 32., 32.5, 33., 34., 35., 36., 38., 40.]
THRESHOLDS = [1e-6, 1e-7, 1e-8, 1e-9, 1e-10]
ORDERING = 'NUMERICALLY_UNCERTIFIED'
COLS = ['rank', 'nu_raw', 'V_A', 'SKR', 'delta_K', 'relative_delta_K_percent',
        'delta_nu', 'delta_VA']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def pair(row):
    return float(row['nu_raw']).hex(), float(row['V_A']).hex()


def ranked(rows):
    if len({pair(r) for r in rows}) != len(rows):
        raise ValueError('Duplicate binary64 parameter pair')
    return sorted(rows, key=lambda r: (-float(r['SKR']), float(r['V_A']), float(r['nu_raw'])))


def reference_rows(rows):
    ordered = ranked(rows)
    best = ordered[0]
    return [dict(rank=i, nu_raw=r['nu_raw'], V_A=r['V_A'], SKR=r['SKR'],
                 delta_K=best['SKR'] - r['SKR'],
                 relative_delta_K_percent=(best['SKR'] - r['SKR']) / abs(best['SKR']) * 100,
                 delta_nu=abs(r['nu_raw'] - best['nu_raw']), delta_VA=abs(r['V_A'] - best['V_A']),
                 ordering_status=ORDERING, nu_raw_hex=pair(r)[0], V_A_hex=pair(r)[1],
                 source_cache_key=r['source_cache_key']) for i, r in enumerate(ordered, 1)]


def neighbors(rows):
    best = rows[0]
    groups = []
    for variable, delta, fixed in [('V_A', 'delta_VA', 'nu_raw'), ('nu_raw', 'delta_nu', 'V_A')]:
        candidates = sorted((r for r in rows if r[fixed] == best[fixed] and pair(r) != pair(best)),
                            key=lambda r: (r[delta], r[variable]))
        groups.extend(dict(group=f'nearest10_{variable}', neighbor_rank=i, **r)
                      for i, r in enumerate(candidates[:10], 1))
        for side, sign in [('below', -1), ('above', 1)]:
            options = [r for r in candidates if sign * (r[variable] - best[variable]) > 0]
            if options:
                groups.append(dict(group=f'{variable}_{side}', neighbor_rank=1, **options[0]))
    return groups


def table(rows, columns):
    return '\n'.join(['| ' + ' | '.join(columns) + ' |',
                      '| ' + ' | '.join('---' for _ in columns) + ' |'] +
                     ['| ' + ' | '.join(str(r.get(c, '')) for c in columns) + ' |' for r in rows])


def write_csv(name, rows):
    with (OUT / name).open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_verified():
    """Reconcile current source roster, protected science and compatible saved tables."""
    protected = read(INPUT / 'protected_input_manifest.json')
    assert len(protected) == 1870
    receipt = read(INPUT / 'final_cleanup.json')
    assert receipt['status'] == 'CURRENTLY_VERIFIED_PASS_COMPLETED_SINGLE_ATTEMPT_STOPPED'
    for name, sha in receipt['final_output_hashes'].items():
        protected[(INPUT / name).relative_to(ROOT).as_posix()] = sha
    for path in INPUT.rglob('*'):
        if path.is_file():
            protected.setdefault(path.relative_to(ROOT).as_posix(), digest(path))
    assert all(digest(ROOT / n) == sha for n, sha in protected.items()), 'Protected artifact drift'
    entries = read(INPUT / 'objective_checkpoint.json')
    assert [e['L_km'] for e in entries] == DISTANCES
    source_paths = sorted((ROOT / 'results').glob('**/exact_source_cache/*.json'))
    settings = {'density_eigenvalue_tolerance': 1e-12, 'physicality_tolerance': 1e-10,
                'precision_ladder': [1050, 1250, 1450]}
    sources, bank, uniform = {}, {}, 0
    for path in source_paths:
        payload = read(path)
        verification = verify_source_payload(payload, settings)
        assert verification['status'] == 'VERIFIED' and payload['C'] >= 0 and payload['w'] >= 0
        key = (payload['nu_mb_raw_hex'], payload['V_A_hex'])
        protected[path.relative_to(ROOT).as_posix()] = digest(path)
        sources[path.relative_to(ROOT).as_posix()] = payload
        if float.fromhex(key[0]) == 0:
            uniform += 1
            continue
        if key in bank:
            assert all(bank[key][f] == payload[f] for f in ('C', 'w', 'ensemble_hash', 'cache_key'))
        bank[key] = payload
    assert len(bank) == 151 and len(source_paths) == 182 and uniform == 29
    lookup, identities = {}, {}
    for entry in entries:
        identity = entry['identity']
        model = identity['identity']
        assert identity['sha256'] == json_hash(model)
        assert model['security'] == 'direct_Z_minus' and model['MI'] == 'deterministic_heterodyne_product'
        assert (model['quadrature_order'], model['beta'], model['epsilon']) == (8, .95, .0186)
        channel = model['channel']
        assert channel['distance_km'] == entry['L_km']
        assert (channel['AO'], channel['phase_noise']) == ('OFF', 'OFF')
        assert channel['receiver_diameter_m'] == .55 and channel['theta_div_full_rad'] == 1e-5
        assert channel['w0_m'] == .0986760647169751
        for name, sha in model['scientific_implementation'].items():
            assert hashlib.sha256(canonical_bytes((ROOT / name).read_bytes())).hexdigest() == sha
        identities[entry['L_km']] = identity
        assert len(entry['rows']) == 151 and {pair(r) for r in entry['rows']} == set(bank)
        for row in entry['rows']:
            assert row['L_km'] == entry['L_km'] and row['channel_hash'] == channel['channel_hash']
            assert row['status'] == 'PASS' and row['security_evaluator'] == 'current_exact_direct_Z_minus'
            assert all(math.isfinite(row[f]) for f in ('SKR', 'I_AB', 'beta_I_AB', 'chi_BE', 'nu_raw', 'V_A'))
            assert row['SKR'] == row['beta_I_AB'] - row['chi_BE']
            assert abs(row['beta_I_AB'] - .95 * row['I_AB']) < 5e-15
            payload = sources[row['source_path']]
            assert (payload['nu_mb_raw_hex'], payload['V_A_hex']) == pair(row)
            assert row['source_cache_key'] == payload['cache_key'] and row['ensemble_hash'] == payload['ensemble_hash']
            lookup[(entry['L_km'], *pair(row))] = row
    verification = read(INPUT / 'final_verification.json')
    assert verification['certified_total_K_error_bound'] is False
    with (INPUT / 'optimized_skr_26_distances.csv').open(encoding='utf-8', newline='') as stream:
        selections = list(csv.DictReader(stream))
    assert len(selections) == 26
    for entry, selected in zip(entries, selections):
        best = ranked(entry['rows'])[0]
        assert float(selected['L_km']) == entry['L_km']
        assert float(selected['best_SKR']) == best['SKR'] and pair(selected) == pair(best)

    # Audit every available identity-bearing objective JSON and every identifiable
    # objective CSV in this experiment family; they are not used to downgrade151.
    audit = []
    paths = sorted(set((ROOT / 'results').rglob('objective_checkpoint.json')) |
                   set((ROOT / 'results').glob('**/exact_objective_cache/*.json')) |
                   set((ROOT / 'results').glob('**/objective_*.json')))
    for path in paths:
        data = read(path)
        if isinstance(data, list) and data and all(isinstance(g, dict) and 'identity' in g and 'rows' in g for g in data):
            groups = data
        elif isinstance(data, dict) and 'identity' in data and 'rows' in data:
            groups = [data]
        elif isinstance(data, dict) and data and all(isinstance(v, dict) and 'identity' in v and 'rows' in v for v in data.values()):
            groups = list(data.values())
        else:
            continue
        matched, excluded = 0, 0
        for group in groups:
            ident = group['identity']
            if not isinstance(ident, dict) or 'identity' not in ident:
                excluded += len(group['rows'])
                continue
            distance = ident['identity']['channel']['distance_km']
            if ident != identities.get(distance):
                excluded += len(group['rows'])
                continue
            assert ident['sha256'] == json_hash(ident['identity'])
            for row in group['rows']:
                key = (distance, *pair(row))
                assert key in lookup, f'Compatible objective absent from151: {path}: {key}'
                current = lookup[key]
                assert all(float(row[f]) == current[f] for f in ('SKR', 'I_AB', 'beta_I_AB', 'chi_BE'))
                assert row['ensemble_hash'] == current['ensemble_hash'] and row['source_cache_key'] == current['source_cache_key']
                matched += 1
        protected[path.relative_to(ROOT).as_posix()] = digest(path)
        audit.append(dict(path=path.relative_to(ROOT).as_posix(), matched_rows=matched, excluded_rows=excluded, format='JSON'))
    for path in sorted((ROOT / 'results').rglob('*.csv')):
        if not ('theta10_D55' in str(path) or 'D55cm_unconstrained' in str(path)):
            continue
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            fields = {'nu_raw', 'V_A', 'SKR', 'channel_hash', 'source_cache_key', 'ensemble_hash'}
            if not fields.issubset(reader.fieldnames or []):
                continue
            matched, excluded = 0, 0
            for row in reader:
                try:
                    distance = float(row.get('L_km') or row.get('distance_km'))
                    key = (distance, *pair(row))
                except (ValueError, TypeError):
                    excluded += 1
                    continue
                if distance not in identities or row['channel_hash'] != identities[distance]['identity']['channel']['channel_hash']:
                    excluded += 1
                    continue
                if float(row['nu_raw']) == 0:
                    excluded += 1
                    continue
                assert key in lookup, f'Additional matching-channel MB point: {path}: {key}'
                current = lookup[key]
                assert row['ensemble_hash'] == current['ensemble_hash'] and row['source_cache_key'] == current['source_cache_key']
                assert all(float(row[f]) == current[f] for f in ('SKR', 'I_AB', 'beta_I_AB', 'chi_BE'))
                matched += 1
        protected[path.relative_to(ROOT).as_posix()] = digest(path)
        audit.append(dict(path=path.relative_to(ROOT).as_posix(), matched_rows=matched, excluded_rows=excluded, format='CSV'))
    return entries, protected, audit, verification


def main():
    if OUT.exists():
        raise SystemExit('Analysis directory already exists; preserve outputs, do not overwrite')
    start, cpu = time.monotonic(), time.process_time()
    entries, protected, audit, prior = load_verified()
    reference = reference_rows(next(e['rows'] for e in entries if e['L_km'] == REF))
    best, second = reference[:2]
    assert (best['nu_raw'], best['V_A'], best['SKR']) == (.165, 5.5, .07798099387393764)
    expected = {5.49375: .07798098033334322, 5.496875: .07798099350667076,
                5.5: .07798099387393764, 5.50625: .07798095622951573}
    p1 = [r for r in reference if r['nu_raw'] == .165 and r['V_A'] in expected]
    assert len(p1) == 4 and all(r['SKR'] == expected[r['V_A']] for r in p1)
    p1.sort(key=lambda r: r['V_A'])
    counts = [dict(threshold=t, distinct_candidates_including_best=sum(0 <= r['delta_K'] <= t for r in reference),
                   other_candidates=sum(0 <= r['delta_K'] <= t for r in reference)-1, ordering_status=ORDERING)
              for t in THRESHOLDS]
    near = [dict(r, **{f'within_{t}': 0 <= r['delta_K'] <= t for t in THRESHOLDS})
            for r in reference if 0 <= r['delta_K'] <= max(THRESHOLDS)]
    close = neighbors(reference)
    nu_slice = [r for r in reference if r['V_A'] == best['V_A']]
    nu_nearest = sorted(nu_slice, key=lambda r: (r['delta_nu'], r['nu_raw']))
    missing = [dict(coordinate='V_A', nu_raw=r['nu_raw'], V_A=r['V_A'], status='MISSING', SKR='')
               for r in prior['next_original_P1_candidates']]
    missing += [dict(coordinate='nu_raw', nu_raw=r['value'], V_A=5.5, status='MISSING', SKR='')
                for r in prior['P2_missing']]
    available = {pair(r) for r in reference}
    assert all(pair(r) not in available for r in missing)
    distances = []
    for entry in entries:
        a, b = ranked(entry['rows'])[:2]
        distances.append(dict(L_km=entry['L_km'], best_nu=a['nu_raw'], best_VA=a['V_A'], best_SKR=a['SKR'],
                              second_nu=b['nu_raw'], second_VA=b['V_A'], second_SKR=b['SKR'],
                              delta_K=a['SKR'] - b['SKR'], delta_nu=abs(a['nu_raw'] - b['nu_raw']),
                              delta_VA=abs(a['V_A'] - b['V_A']),
                              number_within_1e8=sum(0 <= a['SKR'] - r['SKR'] <= 1e-8 for r in entry['rows']),
                              ordering_status=ORDERING))
    OUT.mkdir()
    for name, rows in [('top20_skr_reference.csv', reference[:20]), ('near_equal_skr_points.csv', near),
                       ('closest_parameter_neighbors.csv', close), ('near_optimal_threshold_counts.csv', counts),
                       ('best_vs_second_best_26_distances.csv', distances), ('all151_skr_reference.csv', reference),
                       ('known_P1_points.csv', p1), ('nu_slice_by_skr.csv', nu_slice),
                       ('nu_slice_by_parameter_distance.csv', nu_nearest), ('missing_coordinate_points.csv', missing),
                       ('compatible_objective_table_audit.csv', audit)]:
        write_csv(name, rows)
    accuracy_paths = ['results/theta10_D55_mb_exact_targeted_expansion/batch_3_preparation/numerical_accuracy_audit.md',
                      'results/theta10_D55_ao_numerical_optimum_validation/phase_2A/numerical_accuracy_status.md',
                      'results/theta10_D55_ao_numerical_optimum_validation/overnight_ao_run/numerical_accuracy_assessment.md']
    for name in accuracy_paths:
        assert 'ERROR_UNBOUNDED' in (ROOT / name).read_text(encoding='utf-8')
        protected[name] = digest(ROOT / name)
    report = [f'# Near-optimal exact-catalog SKR analysis\n\nReference L={REF} km; CACHE-ONLY; 151 distinct binary64 MB pairs x26 distances =3926 stored objectives.',
              f'Independent ranking confirms best ({best["nu_raw"]}, {best["V_A"]}), K={best["SKR"]} bits/use. '
              f'Second ({second["nu_raw"]}, {second["V_A"]}), K={second["SKR"]}; gap={second["delta_K"]}, '
              f'relative gap={second["relative_delta_K_percent"]}%; delta_nu={second["delta_nu"]}, delta_VA={second["delta_VA"]}.',
              'All rankings: NUMERICALLY_UNCERTIFIED. BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY. '
              'Exact means the original exact-method stored result, not exact real arithmetic. Python binary64 differences, '
              'unrounded comparisons/sorting and round-trip CSV decimal output; displayed digits do not certify accuracy. '
              'Deterministic ties: lower VA then lower nu. No interpolated/fitted values.',
              '## Table A - Top20\n\n' + table(reference[:20], COLS),
              '## Table B - Inclusive threshold counts\n\nCounts include the incumbent; nested sets are not added together. '
              'The union equals delta_K<=1e-6; each binary64 parameter pair is counted once.\n\n' + table(counts, list(counts[0])),
              '### All qualifying points\n\n' + table(near, COLS),
              '## Table C - Parameter neighbors\n\nThe incumbent is excluded from nearest10 and side-neighbor lists. '
              'Ten distinct evaluated neighbors per coordinate (when available); ties by smaller coordinate. '
              'Groups intentionally overlap; their entries are not additional sources.\n\n' + table(close, ['group', 'neighbor_rank'] + COLS[1:]),
              '## Known P1 points independently verified\n\nStored SKR and source-record identities match all four supplied values.\n\n' + table(p1, COLS[1:]),
              'These four discrete samples have gaps between0 and3.7644421913007875e-8. '
              'Only VA5.496875 and the incumbent fall within1e-8. Eight evaluated points at fixed nu=.165, '
              'VA5.475 through5.525, are within1e-6; their largest gap is4.5690643701856715e-7. '
              'The evaluated VA neighborhood is near-flat at these stated tolerances, not a proved continuous plateau.',
              '## Shaping direction, fixed VA=5.5\n\nAll20 available exact nu values, including the incumbent.\n\n'
              '### Sorted by stored SKR\n\n' + table(nu_slice, COLS[1:]),
              '### Sorted by absolute delta_nu\n\n' + table(nu_nearest, COLS[1:]),
              'Nearest upper nu=.16562500000000002 has gap4.930175926398661e-7; nearest lower nu=.1625 '
              'has gap1.9377536388809347e-6. Neither other nu lies within1e-8. '
              'The nine points within1e-6 comprise the incumbent, seven other VA-only changes and one nu-only change. '
              'At1e-8 there are two points, both nu=.165. Thus close evaluated points mostly differ in VA. '
              'Coverage is anisotropic and sparse, particularly below nu=.165; this does not establish curvature, '
              'a broad continuous two-dimensional region or a sharply localized continuous maximum.',
              '### Missing original coordinate requests (no SKR estimated)\n\n' + table(missing, list(missing[0])),
              'P1 bracket remains[5.496875,5.50625]; P2[.1625,.16562500000000002]. '
              'This analysis neither advances refinement nor completes any coordinate search.',
              '## Best versus second distinct pair at26 distances\n\nEach distance is ranked independently '
              'against its own stored maximum, not the reference incumbent.\n\n' + table(distances, list(distances[0])[:-1]),
              '## Accuracy and provenance limitations\n\nExisting batch3 accuracy audit reports bit-exact original-evaluator '
              'repeats but ERROR_UNBOUNDED. AP cache serialization lacks the per-precision fallback observable/residual '
              'records needed for a source-specific total-K enclosure. Fixed-order GH8 equivalence and repeats are '
              'software/reproducibility evidence, not quadrature or entropy error bounds. GH convergence records for '
              'other ensembles/channels cannot resolve these gaps. Phase2A/overnight records and latest '
              'final_verification.json likewise certify no total-K error bound. Consequently no reported pairwise gap, '
              'including3.6726688357191506e-10, is a rigorously or statistically resolved ordering under these records. '
              'epsilon_opt=1e-8 is an objective stopping tolerance, never a numerical-error bound. '
              'Threshold membership describes literal stored differences only.',
              'Accuracy records inspected:\n\n' + '\n'.join('- ' + p for p in accuracy_paths),
              f'## Validation\n\nFull current source roster:182 files,29 Uniform excluded,153 MB files =151 distinct pairs '
              f'plus2 consistent duplicates. Reconciled every current pair at all26 saved channels. '
              f'Audited{len(audit)} identifiable objective tables, '
              f'{sum(a["matched_rows"] for a in audit)} compatible repeated rows: no value conflicts or additional '
              'compatible candidates. Uniform/other-channel/other-identity records are excluded and counted in '
              'compatible_objective_table_audit.csv. Latest saved AO selections agree with independent stored maximum '
              'at26/26; no AO rerun. Old metrics and source bytes are hash-checked before/after. '
              'AP/new moments/new SKR evaluation/new AO=0; no scientific code/config/default changes; no plots/fits. '
              'Historical FINAL_MODEL_SPEC hash discrepancy remains unchanged: '
              'df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15 versus historical AGENTS561fecc...; '
              'cache-only diagnostic scope only, NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged. STOP.']
    (OUT / 'near_optimal_skr_report.md').write_text('\n\n'.join(report) + '\n', encoding='utf-8')
    assert all(digest(ROOT / n) == sha for n, sha in protected.items()), 'Input changed during analysis'
    result = dict(status='CURRENTLY_VERIFIED_PASS_CACHE_ONLY_ANALYSIS', source_pairs=151, stored_objectives=3926,
                  distances=26, protected_files=len(protected), protected_drift=[], original_protected_count=1870,
                  input_hashes=protected, table_audit=audit, best=best, second=second, threshold_counts=counts,
                  saved_AO_selection_matches_catalog=26, AP_attempts=0, new_source_moments=0,
                  new_SKR_evaluations=0, AO_runs=0, interpolation=False, scientific_changes=False,
                  total_K_error_bound_certified=False, ordering_status=ORDERING,
                  producer_sha256=digest(Path(__file__)), verification_helper_sha256=digest(ROOT / 'scripts/exact_cache_provenance.py'),
                  test_sha256=digest(ROOT / 'tests/test_near_optimal_skr_analysis.py'),
                  wall_seconds=time.monotonic()-start, CPU_seconds=time.process_time()-cpu,
                  output_hashes={p.name: digest(p) for p in OUT.iterdir() if p.is_file()})
    (OUT / 'analysis_verification.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(table(reference[:20], COLS))
    print('\nThreshold counts:\n' + table(counts, list(counts[0])))
    print('\n26 distances:\n' + table(distances, list(distances[0])[:-1]))
    print('\n' + json.dumps({k: result[k] for k in ('status', 'source_pairs', 'stored_objectives', 'protected_files',
                                                  'AP_attempts', 'AO_runs', 'wall_seconds', 'CPU_seconds')}))


if __name__ == '__main__':
    main()
