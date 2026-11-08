"""Read saved results and independently recompute every selected trajectory metric."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from .config import build_scenario
from .evaluation import evaluate_path
from .experiments import write_json


def verify_results(directory) -> dict:
    directory = Path(directory)
    report = json.loads((directory/'results.json').read_text(encoding='utf-8'))
    manifest = json.loads((directory/'output_manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest.items():
        actual = hashlib.sha256((directory/name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Output hash mismatch: {name}')
    inputs = json.loads((directory/'input_manifest.json').read_text(encoding='utf-8'))
    package = Path(__file__).resolve().parents[2]
    for name, expected in inputs['source_sha256'].items():
        if hashlib.sha256((package/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Source producer hash mismatch: {name}')
    for name, expected in inputs['input_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Input hash mismatch: {name}')
    scenario, _ = build_scenario(report['config'])
    checks = 0
    for run in report['runs']:
        for objective, solution in run['solutions'].items():
            recalculated = evaluate_path(scenario, solution['path_indices'])
            for key in ('K', 'energy_j', 'remaining_energy_j', 'unblocked_slots', 'blocked_slots',
                        'valid_signals', 'asymptotic_bits', 'penalty_bits', 'key_bits', 'average_skr_bits_s'):
                if not np.isclose(recalculated[key], solution[key], rtol=1e-12, atol=1e-8):
                    raise ValueError(f'Trajectory metric mismatch: {run["method"]}/{objective}/{key}')
                checks += 1
            if recalculated['series'] != solution['series']:
                raise ValueError('Stored cumulative trajectory series differs from recomputation')
    for path in directory.glob('*.csv'):
        with path.open(encoding='utf-8') as f:
            if any(row.get('data_status') != report['data_status'] for row in csv.DictReader(f)):
                raise ValueError(f'Table status missing or mismatched: {path.name}')
    return dict(status='CURRENTLY_VERIFIED_PASS', trajectory_metric_checks=checks,
                output_hash_checks=len(manifest), table_status='CURRENTLY_VERIFIED_PASS',
                producer_hash_checks=len(inputs['source_sha256']), input_hash_checks=len(inputs['input_sha256']),
                scope='saved-output integrity and metric replay; not a security or global-optimality certificate')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = verify_results(args.output)
    write_json(Path(args.output)/'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
