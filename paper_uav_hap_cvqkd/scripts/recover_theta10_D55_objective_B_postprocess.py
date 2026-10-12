"""Recover checkpoint I/O only; reuse completed AP and original deadline/AO."""
import argparse
import json
import math
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_objective_B_pilot as pilot

OUT = pilot.OUT / 'postprocess_recovery'


def checked_json(data):
    # Original identities encode the parallel wavefront as +Infinity. Never
    # relax finiteness of moments, objective values, or arbitrary metadata.
    def check(value, key=None):
        if isinstance(value, dict):
            for k, v in value.items():
                check(v, k)
        elif isinstance(value, (list, tuple)):
            for v in value:
                check(v, key)
        elif isinstance(value, float) and not math.isfinite(value):
            if key != 'radius_of_curvature_m' or value != math.inf:
                raise ValueError(f'Unexpected nonfinite value: {key}')
    check(data)
    return json.dumps(data, indent=2, allow_nan=True) + '\n'


def save(name, data):
    (OUT / name).write_text(checked_json(data), encoding='utf-8')


def write_csv(name, rows):
    with patch.object(pilot.saved, 'OUT', OUT):
        pilot.saved.write_csv(name, rows)


def main(child=False):
    authorization = pilot.saved.read(pilot.OUT / 'execution_authorization.json')
    deadline = authorization['deadline_monotonic']
    assert time.monotonic() < deadline, 'Original budget exhausted; no recovery'
    assert pilot.saved.read(pilot.OUT / 'source_result.json')['status'] == 'COMPLETED_EXACT'
    pilot.verify_protected()
    if child:
        # No new scientific implementation or source attempt; the original
        # postprocess already guards source_moments and AP fallback calls.
        with patch.object(pilot, 'save', save), patch.object(pilot, 'write_csv', write_csv):
            return pilot.postprocess_child()
    if OUT.exists():
        raise SystemExit('Recovery output exists; preserve it, do not retry')
    OUT.mkdir()
    started, receipt, error = time.monotonic(), None, None
    lease = pilot.safe.AwakeOnAC()
    try:
        with lease:
            samples = []
            for _ in range(3):
                samples.append(lease.power.read())
                time.sleep(.25)
            assert all(pilot.safe.safe_power(s) for s in samples)
            limit = deadline - time.monotonic() - 90.
            assert limit > 10
            save('authorization.json', {'original_deadline_monotonic': deadline,
                'original_deadline_UTC': authorization['deadline_UTC'], 'AC_samples': samples,
                'new_AP_allowed': False, 'original_producer_preserved': True,
                'serialization_fix': 'ONLY_POSITIVE_INFINITY_RADIUS_OF_CURVATURE_METADATA'})
            command = [sys.executable, '-B', '-X', 'utf8', '-u', str(Path(__file__).resolve()), '--child']
            with (OUT / 'postprocess.log').open('w', encoding='utf-8') as log:
                receipt = pilot.safe.supervised_process(command, limit, log)
            assert receipt['returncode'] == 0 and not receipt['deadline_exceeded']
            assert receipt['wall_limit_respected'] and receipt['no_watchdog_thread_remaining']
            assert receipt['power_watch']['abort_reason'] is None
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
    finally:
        protected_count = pilot.verify_protected()
        save('recovery_execution.json', {'status': 'COMPLETED_CACHE_ONLY_RECOVERY' if error is None else 'RECOVERY_FAILED',
            'error': error, 'supervision': receipt, 'sleep_lease': lease.receipt,
            'wall_seconds': time.monotonic() - started, 'controller_CPU_seconds': time.process_time(),
            'elapsed_from_original_origin': time.monotonic() - authorization['origin_monotonic'],
            'within_original_budget': time.monotonic() <= deadline, 'protected_count': protected_count,
            'new_AP_attempts': 0, 'scientific_method_modified': False})
    return 0 if error is None else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', action='store_true')
    raise SystemExit(main(parser.parse_args().child))
