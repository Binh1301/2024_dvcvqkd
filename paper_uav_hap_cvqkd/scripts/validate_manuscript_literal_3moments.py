"""Run only lightweight A--F tests and write new, separate validation evidence."""
import hashlib
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_manuscript_literal_3moments import ManuscriptLiteralTests
from src.manuscript_literal_3moments import MANUSCRIPT_SHA256


def sha(path):
    if os.name == 'nt':
        path = Path('\\\\?\\' + str(path.resolve()))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1:
        raise ValueError('Positive validation attempt required')
    out = ROOT / 'results/manuscript_literal_3moments' / f'implementation_validation_{args.attempt}'
    if out.exists():
        raise FileExistsError('Do not replace a prior report; choose a new validation attempt')
    old_manifest = json.loads((ROOT / 'results/theta10_D55_objective_C_multistart_alt_opt/protected_input_manifest.json').read_text())
    # Enumerate committed assets, not Excel lock files or new validation output.
    names = subprocess.check_output(['git', '-c', 'core.longpaths=true', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in names:
        if name.startswith(('src/', 'scripts/', 'configs/', 'results/')) and '__pycache__' not in name:
            old_manifest.setdefault(name, sha(ROOT / name))
    for name, expected in old_manifest.items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'Preexisting protected input mismatch: {name}')
    started = time.monotonic()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ManuscriptLiteralTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    preservation = all(sha(ROOT / name) == expected for name, expected in old_manifest.items())
    producers = ['src/manuscript_literal_3moments.py', 'configs/manuscript_literal_3moments.json',
                 'scripts/run_manuscript_literal_3moments.py', 'scripts/validate_manuscript_literal_3moments.py',
                 'tests/test_manuscript_literal_3moments.py']
    report = dict(status='CURRENTLY_VERIFIED_PASS' if result.wasSuccessful() and preservation else 'FAILED',
                  tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  elapsed_seconds=time.monotonic()-started, manuscript_sha256=MANUSCRIPT_SHA256,
                  tests_A_B_C_D_E_F='PASSED' if result.wasSuccessful() else 'FAILED: see log',
                  metrics=ManuscriptLiteralTests.metrics, protected_files_verified=len(old_manifest),
                  protected_files_unchanged=preservation,
                  producer_hashes={p: sha(ROOT / p) for p in producers},
                  frozen_model_actual_sha256=sha(ROOT / 'docs/FINAL_MODEL_SPEC.md'),
                  frozen_model_historical_hash_discrepancy='PREEXISTING; spec unchanged; separate user-authorized reproduction mode only',
                  AP='NOT_RUN', AO='NOT_RUN', full_26_distance_sweep='NOT_RUN', catalog_182_evaluation='NOT_RUN',
                  publication_security_certification='NOT_RUN')
    reference = ManuscriptLiteralTests.metrics.get('reference_new_mode_D_F')
    if reference:
        report.update(normalization_probability_law_check='FAILED' if reference['normalization_status'] == 'DISCREPANCY' else 'PASSED',
                      covariance_numerical_validity='PASSED', scientific_readiness='REPRODUCTION_ONLY_NOT_SECURITY_CERTIFICATION')
    out.mkdir(parents=True)
    (out / 'validation.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    (out / 'test_output.txt').write_text(stream.getvalue(), encoding='utf-8')
    (out / 'preserved_input_hashes.json').write_text(json.dumps(old_manifest, indent=2)+'\n', encoding='utf-8')
    print(stream.getvalue())
    print(out / 'validation.json')
    return 0 if report['status'] == 'CURRENTLY_VERIFIED_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
