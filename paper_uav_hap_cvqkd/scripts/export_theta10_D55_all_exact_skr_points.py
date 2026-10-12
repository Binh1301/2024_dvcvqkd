"""Export every stored151x26 SKR value; no numerical evaluator or AO is called."""
import csv
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import analyze_theta10_D55_near_optimal_skr as stored

OUT = stored.BASE / 'all_exact_skr_points'
PREVIOUS = stored.BASE / 'near_optimal_skr_analysis'
COLS = ['rank', 'nu_raw', 'V_A', 'SKR', 'delta_K', 'relative_loss_percent',
        'delta_nu', 'delta_VA', 'near_optimal']
THRESHOLDS = [(0.0001, 1e-6), (0.001, 1e-5), (0.01, 1e-4)]


def classify(rows, distance):
    ordered = stored.ranked(rows)
    best = ordered[0]
    result = []
    for rank, row in enumerate(ordered, 1):
        gap = best['SKR'] - row['SKR']
        loss = gap / best['SKR'] if best['SKR'] > 0 else None
        result.append(dict(L_km=distance, rank=rank, nu_raw=row['nu_raw'], V_A=row['V_A'],
                           SKR=row['SKR'], K_best=best['SKR'], delta_K=gap,
                           relative_loss_fraction=loss if loss is not None else '',
                           relative_loss_percent=100 * loss if loss is not None else '',
                           delta_nu=abs(row['nu_raw'] - best['nu_raw']),
                           delta_VA=abs(row['V_A'] - best['V_A']),
                           near_optimal='UNDEFINED' if loss is None else ('YES' if loss <= 1e-5 else 'NO'),
                           relative_loss_status='DEFINED' if loss is not None else 'UNDEFINED_NONPOSITIVE_K_BEST',
                           ordering_status=stored.ORDERING,
                           nu_raw_hex=stored.pair(row)[0], V_A_hex=stored.pair(row)[1],
                           source_cache_key=row.get('source_cache_key', '')))
    return result


def missing_combinations(entries, roster):
    present = {(entry['L_km'], *stored.pair(row)) for entry in entries for row in entry['rows']}
    return [dict(L_km=distance, nu_raw=float.fromhex(nu), V_A=float.fromhex(va),
                 nu_raw_hex=nu, V_A_hex=va, status='MISSING')
            for distance in stored.DISTANCES for nu, va in sorted(roster)
            if (distance, nu, va) not in present]


def threshold_counts(rows):
    return [dict(relative_loss_percent=percent, relative_loss_fraction=fraction,
                 count_including_best=sum(r['relative_loss_status'] == 'DEFINED' and
                                          r['relative_loss_fraction'] <= fraction for r in rows))
            for percent, fraction in THRESHOLDS]


def save_csv(name, rows):
    with (OUT / name).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    if OUT.exists():
        raise SystemExit('Output already exists; preserve it without overwriting')
    start, cpu = time.monotonic(), time.process_time()
    prior = stored.read(PREVIOUS / 'analysis_verification.json')
    assert all(stored.digest(ROOT / n) == sha for n, sha in prior['input_hashes'].items())
    assert all(stored.digest(PREVIOUS / n) == sha for n, sha in prior['output_hashes'].items())
    assert stored.digest(Path(stored.__file__)) == prior['producer_sha256']
    with (PREVIOUS / 'all151_skr_reference.csv').open(encoding='utf-8', newline='') as stream:
        roster = {stored.pair(row) for row in csv.DictReader(stream)}
    assert len(roster) == 151
    entries = stored.read(stored.INPUT / 'objective_checkpoint.json')
    missing = missing_combinations(entries, roster)
    if missing:
        OUT.mkdir()
        save_csv('missing_source_distance_records.csv', missing)
        (OUT / 'full_catalog_analysis.md').write_text(
            '# Missing source-distance records\n\nCACHE-ONLY; no missing values invented.\n\n' +
            stored.table(missing, list(missing[0])) + '\n', encoding='utf-8')
        print(stored.table(missing, list(missing[0])))
        raise SystemExit('Incomplete151x26 coverage; missing combinations reported, no evaluation attempted')
    entries, protected, audit, _ = stored.load_verified()
    for path in PREVIOUS.iterdir():
        if path.is_file():
            protected[path.relative_to(ROOT).as_posix()] = stored.digest(path)
    assert all({stored.pair(r) for r in e['rows']} == roster for e in entries)
    assert all(len({r['source_cache_key'] for r in e['rows']}) == 151 for e in entries)
    by_distance = {entry['L_km']: classify(entry['rows'], entry['L_km']) for entry in entries}
    reference = by_distance[stored.REF]
    assert (reference[0]['nu_raw'], reference[0]['V_A'], reference[0]['SKR']) == (.165, 5.5, .07798099387393764)
    all_rows = [row for distance in stored.DISTANCES for row in by_distance[distance]]
    assert len(all_rows) == 3926 and len({(r['L_km'], *stored.pair(r)) for r in all_rows}) == 3926
    near = [r for r in reference if r['near_optimal'] == 'YES']
    near_all = [r for r in all_rows if r['near_optimal'] == 'YES']
    counts = threshold_counts(reference)
    deviations = dict(max_delta_nu=max(r['delta_nu'] for r in near), max_delta_VA=max(r['delta_VA'] for r in near),
                      nu_range=[min(r['nu_raw'] for r in near), max(r['nu_raw'] for r in near)],
                      VA_range=[min(r['V_A'] for r in near), max(r['V_A'] for r in near)])
    summary = [dict(L_km=distance, K_best=rows[0]['K_best'],
                    source_distance_rows=len(rows), near_optimal_count=sum(r['near_optimal'] == 'YES' for r in rows),
                    relative_loss_status=rows[0]['relative_loss_status']) for distance, rows in by_distance.items()]
    text = ('# Full exact SKR catalog analysis\n\nCACHE-ONLY.151 distinct compatible exact MB source identities '
            'at26 distances;3926 saved results,0 missing combinations. Full binary64 parameter/cache keys retained. '
            'Stored values are sorted without pre-rounding; ties use lowerVA then lowernu.\n\n'
            'Near-optimal YES means (K_best(L)-K)/K_best(L)<=1e-5 (0.001%). '
            'Relative fractions and percentages are different columns. Each distance uses its own finite-catalog maximum. '
            'For K_best<=0 the relative columns are blank and classification UNDEFINED; '
            'all26 current K_best values are positive. Negative candidate SKR values remain unchanged. '
            'Counts include the incumbent and are nested,not additive.\n\n'
            '## Complete151-row reference table\n\n' + stored.table(reference, COLS) + '\n\n'
            '## Current best-found point\n\nL=21.9393102292km;nu_raw=.165,VA=5.5,'
            'K=.07798099387393764bits/use.\n\n'
            '## All candidates within0.001% loss\n\n' + stored.table(near, COLS) + '\n\n'
            '## Relative performance threshold counts\n\n' + stored.table(counts, list(counts[0])) + '\n\n'
            '## Largest reference near-set parameter deviations\n\n' + json.dumps(deviations, indent=2) + '\n\n'
            '## Coverage and near-optimal counts by distance\n\n' + stored.table(summary, list(summary[0])) + '\n\n'
            '## Validation and scope\n\nReused the existing read-only provenance/identity audit; '
            f'{len(audit)} identifiable objective tables reconciled.151 parameter pairs and151 source keys '
            'are unique at each distance; support256/source method/settings/scientific producer hashes compatible. '
            'All previous near-optimal-analysis artifacts and protected scientific inputs hash-checked before/after. '
            'No AP,Cw generation,SKR evaluation,AO,interpolation,fitting or scientific code/config changes. '
            'Performance thresholds are relative to the finite tested catalog,not the unknown continuous optimum '
            'or certified numerical-error bounds. Ordering remains NUMERICALLY_UNCERTIFIED; no totalK enclosure. '
            'Historical frozen-spec hash discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged. STOP.\n')
    OUT.mkdir()
    for name, rows in [('all_151_points_reference.csv', reference), ('all_near_optimal_points_reference.csv', near),
                       ('all_3926_points_26_distances.csv', all_rows), ('near_optimal_points_by_distance.csv', near_all),
                       ('relative_threshold_counts_reference.csv', counts)]:
        save_csv(name, rows)
    (OUT / 'full_catalog_analysis.md').write_text(text, encoding='utf-8')
    assert all(stored.digest(ROOT / n) == sha for n, sha in protected.items()), 'Input drift during export'
    verification = dict(status='CURRENTLY_VERIFIED_PASS_CACHE_ONLY_FULL_CATALOG', source_pairs=151,
                        unique_source_keys=151, distances=26, source_distance_rows=3926, missing_records=[],
                        protected_files=len(protected), input_hashes=protected, protected_drift=[],
                        threshold_counts_reference=counts, near_optimal_reference_count=len(near),
                        near_optimal_all_distances_count=len(near_all), deviations=deviations, coverage=summary,
                        AP_attempts=0, new_source_moments=0, new_SKR_evaluations=0, AO_runs=0,
                        scientific_changes=False, interpolation=False, total_K_error_bound_certified=False,
                        ordering_status=stored.ORDERING, producer_sha256=stored.digest(Path(__file__)),
                        reused_audit_sha256=stored.digest(Path(stored.__file__)),
                        test_sha256=stored.digest(ROOT / 'tests/test_all_exact_skr_points.py'),
                        wall_seconds=time.monotonic()-start, CPU_seconds=time.process_time()-cpu,
                        output_hashes={p.name: stored.digest(p) for p in OUT.iterdir() if p.is_file()})
    (OUT / 'catalog_verification.json').write_text(json.dumps(verification, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    # str(float) round-trips binary64. No dataframe display or row-limit options.
    print('COMPLETE151-ROW REFERENCE TABLE\n' + stored.table(reference, COLS))
    print('\nCURRENT BEST:nu_raw=0.165,VA=5.5,K=0.07798099387393764bits/use')
    print('\nALL NEAR-OPTIMAL POINTS (<=0.001%)\n' + stored.table(near, COLS))
    print('\nTHRESHOLD COUNTS\n' + stored.table(counts, list(counts[0])))
    print('\nLARGEST PARAMETER DEVIATIONS\n' + json.dumps(deviations))
    print(f'\nVERIFIED151 UNIQUE SOURCES x26 DISTANCES =3926 ROWS; MISSING=0; '
          f'ALL-DISTANCE NEAR-OPTIMAL ROWS={len(near_all)}; AP/SKR/AO RUNS=0; STOP.')


if __name__ == '__main__':
    main()
