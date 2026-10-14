"""Lightweight unit/regression checks plus protected-file receipt; no production run."""
import argparse
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / 'results/manuscript_corrected_3moments/implementation_validation'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1:
        raise ValueError('Positive attempt required')
    out = BASE / f'attempt_{args.attempt}'
    if out.exists():
        raise FileExistsError('Preserve receipts; choose a new attempt')
    baseline = json.loads((BASE / 'baseline_manifest.json').read_text(encoding='utf-8'))
    before = [rel for rel, digest in baseline['protected_hashes'].items()
              if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest]
    if before:
        raise ValueError(f'Protected inputs changed before validation: {before}')
    modules = [importlib.import_module(name) for name in [
        'tests.test_manuscript_corrected_3moments', 'tests.test_manuscript_corrected_mi',
        'tests.test_manuscript_corrected_evaluator']]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules)
    log = io.StringIO()
    start = time.monotonic()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    metrics = {}
    for module in modules:
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and hasattr(obj, 'metrics'):
                metrics[obj.__name__] = obj.metrics
    changed = [rel for rel, digest in baseline['protected_hashes'].items()
               if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest]
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    producers = [str(p.relative_to(ROOT)).replace('\\', '/') for folder, pattern in [
        ('src', 'manuscript_corrected*.py'), ('scripts', '*manuscript_corrected*.py'),
        ('tests', 'test_manuscript_corrected*.py'), ('configs', 'manuscript_corrected*.json')]
        for p in sorted((ROOT / folder).glob(pattern))]
    report = dict(status='CURRENTLY_VERIFIED_PASS' if result.wasSuccessful() and not changed and diff.returncode == 0 else 'FAILED',
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        elapsed_seconds=time.monotonic()-start, metrics=metrics,
        protected_files_verified=len(baseline['protected_hashes']), protected_changes=changed,
        frozen_sha256=hashlib.sha256((ROOT/'docs/FINAL_MODEL_SPEC.md').read_bytes()).hexdigest(),
        frozen_historical_hash_discrepancy='PREEXISTING_UNCHANGED',
        producer_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in producers},
        source_oracle_AP='NOT_RUN', AO='NOT_RUN', full26='NOT_RUN', catalog182_sweep='NOT_RUN',
        corrected_reference_production_entry='NOT_RUN', publication='NOT_RUN',
        readiness='BLOCKED_BY_SCIENTIFIC_MODEL',
        scientific_blockers=['No verified trusted nonideal receiver Holevo model for R=.7/xi_det=.0135',
                             'MI reference256 sampling precision not certified; no production point run'],
        git_diff_check_exit=diff.returncode, git_diff_check_output=diff.stdout+diff.stderr)
    out.mkdir(parents=True)
    (out/'test_output.txt').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    (out/'validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
    print(log.getvalue())
    print(out/'validation.json')
    return 0 if report['status']=='CURRENTLY_VERIFIED_PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
