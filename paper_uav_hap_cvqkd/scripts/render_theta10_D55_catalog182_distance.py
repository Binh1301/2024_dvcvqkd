"""Redraw the three saved SKR curves, updating MB to the 182-source catalog.

Data-only export: no source computation, SKR evaluation, or AO execution.
"""
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import exact_cache_provenance as provenance
from scripts import render_theta10_D55_three_scheme_log10 as plot

BASE = ROOT / 'results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme'
CHECKPOINT = ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization/grid_timeout_retry_1/objective_checkpoint.json'
CATALOG = ROOT / 'results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv'
STOPPED = ROOT / 'results/theta10_D55_objective_C_multistart_alt_opt/objective_c_checkpoint.json'
MANIFEST = STOPPED.parent / 'protected_input_manifest.json'
OUT = ROOT / 'results/skr_vs_distance_theta10urad_D55cm_catalog182_20261012'


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def pair(row, va='V_A'):
    return float(row['nu_raw']).hex(), float(row[va]).hex()


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row})
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    assert not OUT.exists(), 'Preserve prior exports; output directory already exists'
    manifest = read_json(MANIFEST)
    protected = {**manifest, str(STOPPED.relative_to(ROOT)): plot.sha256(STOPPED),
                 str(CATALOG.relative_to(ROOT)): plot.sha256(CATALOG),
                 str(CHECKPOINT.relative_to(ROOT)): plot.sha256(CHECKPOINT)}

    def verify_unchanged():
        for name, digest in protected.items():
            assert plot.sha256(ROOT / name) == digest, f'Protected input changed: {name}'

    verify_unchanged()
    assert read_json(STOPPED)['status'] == 'USER_STOPPED'
    entries, baseline = read_json(CHECKPOINT), read_csv(BASE / 'skr_vs_distance_three_scheme.csv')
    candidates, catalog = read_csv(BASE / 'candidate_evaluations.csv'), read_csv(CATALOG)
    assert len(entries) == 26 and len(baseline) == 78 and len(catalog) == 182
    sources = {}
    for row in catalog:
        payload = read_json(ROOT / row['source_path'])
        verified = provenance.verify_source_payload(payload, payload['source_settings'])
        assert row['cache_key'] in (verified['historical_cache_key'], verified['canonical_source_cache_key'])
        assert pair(row, 'VA') == (payload['nu_mb_raw_hex'], payload['V_A_hex'])
        assert float(row['C']) == payload['C'] and float(row['w']) == payload['w']
        sources[pair(row, 'VA')] = payload
    assert len(sources) == 182
    output, changes = [], []
    for entry in entries:
        distance, rows = entry['L_km'], entry['rows']
        context = entry['identity']
        identity = context['identity']
        assert context['sha256'] == provenance.json_hash(identity)
        assert identity['security'] == 'direct_Z_minus'
        assert identity['MI'] == 'deterministic_heterodyne_product' and identity['quadrature_order'] == 8
        assert identity['epsilon'] == .0186 and identity['beta'] == .95
        for name, digest in identity['scientific_implementation'].items():
            assert provenance.source_hashes((ROOT / name).read_bytes())['canonical_lf_sha256'] == digest
        assert len(rows) == 182 and {pair(row) for row in rows} == set(sources)
        for row in rows:
            source = sources[pair(row)]
            assert row['status'] == 'PASS' and float(row['L_km']) == distance
            assert row['channel_hash'] == identity['channel']['channel_hash']
            assert float(row['T_eff']) == identity['channel']['T_eff']
            assert row['ensemble_hash'] == source['ensemble_hash']
            # Compact saved objective rows can omit C,w; validate the linked
            # exact source, and compare objective copies only when recorded.
            for key in ('C', 'w'):
                if row.get(key) not in (None, ''):
                    assert float(row[key]) == source[key]
            assert math.isfinite(float(row['SKR']))
            assert float(row['SKR']) == float(row['beta_I_AB']) - float(row['chi_BE'])
            assert math.isclose(float(row['beta_I_AB']), .95 * float(row['I_AB']), abs_tol=1e-15)
        prior = {r['scheme']: r for r in baseline if float(r['distance_km']) == distance}
        assert set(prior) == set(plot.SCHEMES)
        uniform = prior[plot.SCHEMES[0]]
        uniform_bank = [r for r in candidates if r['family'] == 'Uniform' and float(r['L_km']) == distance]
        assert len(uniform_bank) == 29
        assert float(uniform['K']) == max(float(r['SKR']) for r in uniform_bank)
        payload = read_json(ROOT / uniform['source_path'])
        provenance.verify_source_payload(payload, payload['source_settings'])
        assert uniform['ensemble_hash'] == payload['ensemble_hash']
        assert float(uniform['C']) == payload['C'] and float(uniform['w']) == payload['w']
        assert uniform['channel_hash'] == identity['channel']['channel_hash']
        fixed = prior[plot.SCHEMES[1]]
        assert pair(fixed) == (.2.hex(), 1.3833230302980657.hex())
        fixed_saved = next(r for r in rows if pair(r) == pair(fixed))
        for key in ('SKR', 'I_AB', 'beta_I_AB', 'chi_BE'):
            assert float(fixed[key]) == float(fixed_saved[key])
        assert fixed['ensemble_hash'] == fixed_saved['ensemble_hash']
        best = max(rows, key=lambda r: (float(r['SKR']), -float(r['V_A']), -float(r['nu_raw'])))
        output.extend([uniform, fixed, {**best, 'K': best['SKR'], 'distance_km': distance,
                       'scheme': plot.SCHEMES[2], 'selection': 'BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
                       'selection_origin': 'validated_182_MB_source_catalog'}])
        old = float(prior[plot.SCHEMES[2]]['K'])
        changes.append({'distance_km': distance, 'nu_raw': best['nu_raw'], 'V_A': best['V_A'],
                        'old_MB_SKR': old, 'updated_MB_SKR': best['SKR'],
                        'delta_SKR': float(best['SKR']) - old})
    assert list(plot.positive_runs([{'distance_km': i, 'K': k} for i, k in enumerate([1., 0., -1., 2.])])) == [[(0., 1.)], [(3., 2.)]]
    OUT.mkdir()
    csv_path = OUT / 'skr_vs_distance_three_scheme.csv'
    write_csv(csv_path, output)
    write_csv(OUT / 'updated_MB_parameters_and_comparison.csv', changes)
    png, pdf, report_path = plot.render(csv_path, OUT)
    exported = read_csv(csv_path)
    assert len(exported) == 78
    assert [float(r['K']) for r in exported] == [float(r['K']) for r in output]
    verify_unchanged()
    report = read_json(report_path)
    report.update(status='CURRENTLY_VERIFIED_PASS', MB_sources=182, Uniform_sources=29,
                  stored_MB_SKR_rows_checked=4732, distances=26, protected_hashes_verified=len(protected),
                  Objective_C_status='USER_STOPPED', optimized_scope='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
                  updated_MB_distances_vs_original_plot=sum(r['delta_SKR'] != 0 for r in changes),
                  input_hashes={str(p.relative_to(ROOT)): plot.sha256(p) for p in
                                (CHECKPOINT, CATALOG, BASE / 'skr_vs_distance_three_scheme.csv', BASE / 'candidate_evaluations.csv')},
                  renderer_sha256=plot.sha256(Path(__file__)), reused_renderer_sha256=plot.sha256(Path(plot.__file__)),
                  scientific_model_changed=False, AP='NOT_RUN', AO='NOT_RUN', new_SKR='NOT_RUN',
                  png_dpi=300, PDF='vector',
                  frozen_spec_hash_discrepancy='Pre-existing; renderer-only task does not amend or certify model')
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'png': str(png), 'pdf': str(pdf), 'csv': str(csv_path),
                      'report': str(report_path), 'updated_distances': report['updated_MB_distances_vs_original_plot']}))


if __name__ == '__main__':
    main()
