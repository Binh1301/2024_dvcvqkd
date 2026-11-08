"""Exploratory sensitivity of the existing finite-key proxy, not security evidence.

Run: python -m uav_qkd.finite_size_feasibility --output results/phase5d_finite_size_20261108
No signal rate or mission scenario is assigned by this diagnostic.
"""
import argparse
import csv
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
import json
import math
from pathlib import Path

from .finite_size import finite_key
from .finite_size_reference import delta_per_signal, load_finite_reference


def positive_block_threshold(r, epsilon):
    """Strict n>n_crit for constant clear raw rate; preserve float input exactly."""
    if not math.isfinite(r) or not math.isfinite(epsilon) or not 0 < epsilon < 1:
        raise ValueError('Require finite raw rate and 0<epsilon<1')
    if r <= 0:
        return dict(n_crit=None, n_crit_decimal=None, n_min=None, positive_possible=False)
    # Decimal guards floor+1 when float n_crit rounds onto an integer boundary.
    with localcontext() as ctx:
        ctx.prec = 80
        logterm = 1 - Decimal.from_float(float(epsilon)).ln() / Decimal(2).ln()
        critical = 49 * logterm / Decimal.from_float(float(r)) ** 2
        if critical > Decimal(2**53 - 2):
            raise ValueError('Threshold exceeds exact integer resolution of the float proxy')
        minimum = int(critical.to_integral_value(rounding=ROUND_FLOOR)) + 1
        return dict(n_crit=float(critical), n_crit_decimal=str(critical),
                    n_min=minimum, positive_possible=True)


def block_proxy(r, n, epsilon):
    """One terminal penalty; n already counts VALID signals, with no cloud factor."""
    if isinstance(n, bool) or not math.isfinite(n) or n < 0 or int(n) != n or n > 2**53 - 1:
        raise ValueError('Require integer valid-signal count in [0, 2**53-1]')
    if not math.isfinite(r):
        raise ValueError('Require finite raw rate')
    result = finite_key(r if n else 0., 1 if n else 0, n if n else 1., epsilon)
    return dict(result, r_clear_raw=float(r), n_valid=int(n))


def mission_requirements(r, epsilon, T, clear_fraction):
    """n=f_s*eta_valid*c*T; report required product without assigning either factor."""
    if not math.isfinite(T) or T <= 0 or not math.isfinite(clear_fraction) or not 0 <= clear_fraction <= 1:
        raise ValueError('Require finite T>0 and clear_fraction in [0,1]')
    threshold = positive_block_threshold(r, epsilon)
    base = dict(threshold, T_s=T, clear_fraction=clear_fraction,
                required_product_strict_gt_per_s=None, integer_budget_product_ge_per_s=None)
    if clear_fraction == 0 or not threshold['positive_possible']:
        return dict(base, feasible=False, key_bits=0.)
    exposure = clear_fraction * T
    return dict(base, feasible=None,
                required_product_strict_gt_per_s=threshold['n_crit'] / exposure,
                integer_budget_product_ge_per_s=threshold['n_min'] / exposure)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def verify_pilot(directory):
    """Verify the sealed Phase5C outputs and exact raw-rate borrowing, fail closed."""
    directory = Path(directory)
    manifest = _read(directory / 'output_manifest.json')
    for name, expected in manifest.items():
        path = directory / Path(name.replace('\\', '/'))
        if _sha(path) != expected:
            raise ValueError('Pilot output hash mismatch: ' + name)
    covered = {name.replace('\\', '/') for name in manifest}
    required = {'summary.json', 'input_manifest.json', 'config.json'}
    required.update(f'{stage}/p{i}{suffix}' for stage in ('reproduction', 'target')
                    for i in range(5) for suffix in ('.json', '.seal.json'))
    if not required.issubset(covered):
        raise ValueError('Pilot output manifest coverage incomplete')
    summary = _read(directory / 'summary.json')
    if summary['input_manifest_sha256'] != _sha(directory / 'input_manifest.json'):
        raise ValueError('Pilot input manifest hash mismatch')
    if len(summary['comparisons']) != 5 or not all(c['passed'] for c in summary['reproduction_checks']):
        raise ValueError('Require five reproduced pilot points')
    for row in summary['comparisons']:
        for case, stage in [('historical', 'reproduction'), ('target', 'target')]:
            path = directory / stage / (row['point']['point_id'] + '.json')
            if _read(path.with_suffix('.seal.json'))['sha256'] != _sha(path):
                raise ValueError('Pilot checkpoint seal hash mismatch')
            record = _read(path)
            if record['input_manifest_sha256'] != summary['input_manifest_sha256'] or record['trial_config_sha256'] != summary['config_sha256']:
                raise ValueError('Pilot checkpoint provenance hash mismatch')
            if row[case] != record['winners']['MB']:
                raise ValueError('Pilot borrowed winner differs from sealed checkpoint')
    return summary


def generate(root, output):
    """Generate tables only from existing sealed pilot rates and reference inputs."""
    root, output = Path(root).resolve(), Path(output).resolve()
    pilot_dir = root / 'results/phase5c_skr_noise_pilot_20261107'
    pilot = verify_pilot(pilot_dir)
    reference_path = root / 'configs/finite_size/ieee_2025_reference.yaml'
    reference = load_finite_reference(reference_path)
    axes = dict(n_valid=[10**5, 10**6, 10**7, 8*10**7, 10**8, 10**9, 10**10],
                epsilon=[1e-6, 3e-8, 1e-10], T_s=[1, 10, 100, 300, 1000],
                clear_fraction=[0., .25, .5, .75, 1.],
                role='EXPLORATORY_ANALYSIS_AXES_NOT_AUTHOR_SELECTED_MISSION')
    rates, block_rows, mission_rows = [], [], []
    for row in pilot['comparisons']:
        for case in ('historical', 'target'):
            rate = row[case]['K_raw']
            identity = dict(point_id=row['point']['point_id'], noise_case=case, r_clear_raw=rate)
            rates.append(dict(identity, source_evidence_class=row[case]['source_evidence_class'],
                              security_valid=False, **positive_block_threshold(rate, 3e-8)))
            for epsilon in axes['epsilon']:
                threshold = positive_block_threshold(rate, epsilon)
                for n in axes['n_valid']:
                    block_rows.append(dict(identity, epsilon=epsilon, **threshold,
                                           **{k:v for k,v in block_proxy(rate, n, epsilon).items() if k!='r_clear_raw'},
                                           delta_bits_per_signal=delta_per_signal(n, epsilon)))
                for T in axes['T_s']:
                    for c in axes['clear_fraction']:
                        mission_rows.append(dict(identity, epsilon=epsilon,
                                                 **mission_requirements(rate, epsilon, T, c)))
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [('block_sensitivity', block_rows), ('mission_sensitivity', mission_rows)]:
        columns = list(dict.fromkeys(k for row in rows for k in row))
        with (output / (name + '.csv')).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    summary = dict(status='CURRENTLY_VERIFIED_PASS',
        scope='EXPLORATORY_EXISTING_PROXY_SENSITIVITY_ONLY_NO_SKR_REEVALUATION',
        formula='L=max(0,n*r-7*sqrt(n*log2(2/epsilon)))',
        threshold='n>n_crit=49*log2(2/epsilon)/r^2; n_min=floor(n_crit)+1; r>0',
        numerical_policy='80-digit Decimal threshold guards integer rounding; proxy uses unchanged float finite_key; cancellation near n_min may yield zero at float precision',
        mission_formula='n=f_s*eta_valid*clear_fraction*T',
        mission_product_condition='f_s*eta_valid>n_crit/(clear_fraction*T); integer budget >=n_min/(clear_fraction*T)',
        cloud_policy='n_valid is already retained; no second multiplication by clear_fraction',
        rates=rates, axes=axes, mission_parameters=dict(f_s=None, eta_valid=None, m0=None),
        reference_only=dict(role=reference['role'], key_fraction=reference['key_fraction'], **reference['derived']),
        row_counts=dict(block_sensitivity=len(block_rows), mission_sensitivity=len(mission_rows)),
        limitations=['Constant clear raw rate per pilot point; no trajectory or variable-rate mission assertion',
                     'Reference epsilon is a proxy sensitivity input, not a composed security proof',
                     'Positive proxy is not certified extractable key; pilot security_valid=false and INSUFFICIENT_EVIDENCE',
                     'No f_s, eta_valid, mission duration, clear fraction or mission m0 has been selected'],
        paper_mode='NOT_RUN', security_valid=False, paper_admissible=False, evidence_labels_promoted=False)
    _write(output / 'summary.json', summary)
    inputs = [p for p in pilot_dir.rglob('*') if p.is_file()] + [reference_path]
    producers = [Path(__file__), root/'src/uav_qkd/finite_size.py', root/'src/uav_qkd/finite_size_reference.py',
                 root/'src/uav_qkd/config.py']
    _write(output / 'input_manifest.json', dict(schema='phase5d_finite_size_v1',
        inputs={p.relative_to(root).as_posix(): _sha(p) for p in sorted(inputs)},
        producers={p.relative_to(root).as_posix(): _sha(p) for p in producers},
        pilot_seals_verified=True, original_sources_recomputed=False,
        source_role='Borrowed sealed pilot scalar outputs only; no new physical/security evaluation'))
    _write(output / 'output_manifest.json', {name:_sha(output/name) for name in
        ['block_sensitivity.csv', 'mission_sensitivity.csv', 'summary.json', 'input_manifest.json']})
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    generate(Path(__file__).resolve().parents[2], args.output)
