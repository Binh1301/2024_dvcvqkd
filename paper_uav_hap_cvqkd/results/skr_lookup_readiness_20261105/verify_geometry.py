"""Read-only validation of geometry-only artifacts and source provenance."""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((OUT/'geometry_receipt.json').read_text(encoding='utf-8'))
    checks = {}
    checks['source_hashes'] = all(sha(ROOT/path) == digest for path, digest in receipt['source_hashes'].items())
    checks['output_hashes'] = all(sha(OUT/path) == digest for path, digest in receipt['outputs'].items())
    with (OUT/'geometry_only.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    rates = ['transmittance', 'received_power', 'nu_opt', 'VA_opt', 'IAB_opt', 'chiBE_opt',
             'K_raw_opt_bits_per_use', 'K_potential_bits_per_use']
    checks['csv_uncomputed'] = len(rows) == 2601 and all(
        r['numerical_status'] == 'NOT_RUN' and all(r[k] == '' for k in rates) for r in rows)
    with np.load(OUT/'geometry_only.npz', allow_pickle=False) as data:
        checks['array_uncomputed'] = all(np.isnan(data[k]).all() for k in rates)
        checks['grid_shape'] = data['x_m'].shape == (51, 51) and data['y_m'].shape == (51, 51)
        checks['grid_spacing'] = np.array_equal(data['x_m'][0], np.arange(51)*40) and np.array_equal(data['y_m'][:,0], np.arange(51)*40)
        radius = np.hypot(data['x_m']-1000, data['y_m']-1000)
        checks['geometry'] = bool(np.allclose(data['distance_m'], np.hypot(19000, radius), rtol=0, atol=1e-11)
                                  and np.allclose(data['zenith_deg'], np.degrees(np.arctan2(radius, 19000)), rtol=0, atol=1e-12))
        checks['center_and_edge'] = data['distance_m'][25,25] == 19000 and data['zenith_deg'][25,25] == 0 and 4.25 < data['zenith_deg'].max() < 4.27
    expected = {0: (.1787939813, .1779978935, .0007960878), 30: (None, None, -.00303173)}
    benchmark_checks = []
    for row in receipt['historical_benchmarks']:
        angle = int(row['zenith_deg'])
        differences = {}
        for key, target in zip(('beta_I_AB','chi_BE','K_raw'), expected[angle]):
            if target is not None:
                value = float(row[key]); diff = value-target
                differences[key] = dict(absolute=abs(diff), relative=abs(diff/target) if target else None)
        benchmark_checks.append(dict(zenith_deg=angle, differences=differences,
                                     source_evidence_class=row['source_evidence_class'], reevaluated=False))
    checks['archived_benchmarks'] = len(benchmark_checks) == 2 and all(
        diff['absolute'] < 2e-9 for row in benchmark_checks for diff in row['differences'].values())
    checks['gates'] = receipt['phase_B_ready'] is False and receipt['map_ready'] is False and receipt['SKR_evaluations'] == 0
    checks = {name: bool(value) for name, value in checks.items()}
    result = dict(status='CURRENTLY_VERIFIED_PASS' if all(checks.values()) else 'FAILED',
                  scope='GEOMETRY_AND_ARCHIVE_ONLY', checks=checks, benchmarks=benchmark_checks,
                  scientific_rate_map_status='NOT_RUN', benchmark_reevaluation='NOT_RUN',
                  independent_source_validation='NOT_RUN')
    path = OUT/'verification.json'
    with path.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(result, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
