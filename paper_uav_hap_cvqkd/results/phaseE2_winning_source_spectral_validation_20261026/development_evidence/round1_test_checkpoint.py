"""Cheap checkpoint fault injections and M<=16 scientific equivalence checks."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

import mpmath as mp
import numpy as np
import checkpoint_wrapper as cw

BASE = cw.OUT / 'stub_checkpoints'


class Checkpoints(unittest.TestCase):
    def setUp(self):
        self.directory = BASE / self._testMethodName
        self.directory.mkdir(parents=True, exist_ok=False)
        self.path = self.directory / 'sector.json'
        self.ident = dict(digits=50, sector=0, input_sha256='STUB_NOT_A_PHYSICAL_SOURCE', producer='v1')

    def builder(self):
        return mp.matrix([[2, mp.mpc(0, 1)], [mp.mpc(0, -1), 3]]), mp.mpf(0)

    def make(self):
        return cw.checkpoint_sector(self.path, self.ident, self.builder)[0]

    def test_roundtrip(self):
        result = self.make()
        self.assertEqual(result, cw.load_checkpoint(self.path, self.ident))
        self.assertEqual(result['payload']['diagnostics']['effective_rank'], 2)

    def test_resume_does_not_build_or_eigh(self):
        self.make(); original = cw.sha(self.path)
        def forbidden():
            raise AssertionError('A completed sector must be reused')
        _, reused = cw.checkpoint_sector(self.path, self.ident, forbidden)
        self.assertTrue(reused); self.assertEqual(original, cw.sha(self.path))

    def test_first_write_interruption(self):
        with self.assertRaises(InterruptedError):
            cw.checkpoint_sector(self.path, self.ident, self.builder, True)
        self.assertFalse(self.path.exists())
        self.assertTrue(self.path.with_suffix('.json.pending').exists())
        _, reused = cw.checkpoint_sector(self.path, self.ident, self.builder)
        self.assertFalse(reused); cw.load_checkpoint(self.path, self.ident)

    def test_interrupted_replace_preserves_old_file(self):
        self.make(); old = self.path.read_bytes()
        with self.assertRaises(InterruptedError):
            cw.atomic_json(self.path, dict(broken=True), True)
        self.assertEqual(self.path.read_bytes(), old)
        cw.load_checkpoint(self.path, self.ident)

    def test_bad_source_rejected(self):
        self.make()
        with self.assertRaises(ValueError):
            cw.load_checkpoint(self.path, dict(self.ident, input_sha256='DIFFERENT'))

    def test_bad_precision_rejected(self):
        self.make()
        with self.assertRaises(ValueError):
            cw.load_checkpoint(self.path, dict(self.ident, digits=70))

    def test_bad_producer_rejected(self):
        self.make()
        with self.assertRaises(ValueError):
            cw.load_checkpoint(self.path, dict(self.ident, producer='v2'))

    def test_corruption_rejected(self):
        data = self.make(); data['payload']['eigenvalues'][0] = '99'
        cw.atomic_json(self.path, data)
        with self.assertRaises(ValueError):
            cw.load_checkpoint(self.path, self.ident)

    def test_checksum_is_not_a_consistency_check(self):
        data = self.make(); data['payload']['eigenvalues'][0] = '-99'
        data['payload_sha256'] = cw.digest(data['payload']); cw.atomic_json(self.path, data)
        with self.assertRaises(ArithmeticError):
            cw.load_checkpoint(self.path, self.ident)

    def test_incomplete_rejected(self):
        data = self.make(); data['complete'] = False; cw.atomic_json(self.path, data)
        with self.assertRaises(ValueError):
            cw.load_checkpoint(self.path, self.ident)

    def test_failed_checks_never_complete(self):
        with self.assertRaises(ArithmeticError):
            cw.checkpoint_sector(self.path, self.ident,
                                 lambda: (mp.matrix([[1, 9], [0, 2]]), mp.mpf(0)))
        self.assertFalse(self.path.exists())

    def test_actual_process_interruption_and_resume(self):
        # Kill only this stub's actual interpreter, while no atomic final exists.
        script = ('import sys,time; from pathlib import Path; '
                  'p=Path(sys.argv[1]); p.write_text("partial"); print("READY",flush=True); time.sleep(10)')
        pending = self.path.with_suffix('.json.pending')
        process = subprocess.Popen([getattr(sys, '_base_executable', sys.executable), '-c', script, str(pending)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            limit = time.monotonic() + 3
            while not pending.exists() and process.poll() is None and time.monotonic() < limit:
                time.sleep(.01)
            self.assertTrue(pending.exists()); process.kill(); process.wait(timeout=3)
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=3)
            process.communicate(timeout=3)
        self.assertFalse(self.path.exists())
        self.make(); cw.load_checkpoint(self.path, self.ident)

    def test_authorization_gate(self):
        plan = self.directory / 'plan.json'; authorization = self.directory / 'authorization.json'
        cw.atomic_json(plan, dict(stub=True)); cw.atomic_json(authorization, dict(decision='NOT_APPROVED'))
        with self.assertRaises(PermissionError):
            cw.controlled_run(plan, authorization)
        self.assertFalse((self.directory / 'controlled_checkpoints').exists())

    def test_small_scientific_equivalence(self):
        results = []
        for name in ['Uniform_4', 'MB_16']:
            path = cw.PRIOR / 'inputs' / (name + '.npz')
            original = cw.sha(path); p, alpha, groups = cw.input_source(path)
            for digits in [50, 70]:
                target = self.directory / f'{name}_{digits}'
                for sector in range(4):
                    cw.sector_job(path, digits, sector, target)
                output = cw.moment_job(path, digits, target)
                same = cw.moment_job(path, digits, target)
                self.assertEqual(output, same)
                old, _ = cw.prior_module('independent_gram_Cw').arbitrary(p, alpha, digits)
                with mp.workdps(80):
                    self.assertLess(abs(mp.mpf(output['C']) - mp.mpf(old[0]['C'])), mp.mpf('1e-39'))
                    self.assertLess(abs(mp.mpf(output['w_residual']) - mp.mpf(old[0]['w_residual'])), mp.mpf('1e-39'))
                    self.assertLess(abs(mp.mpf(output['direct_residual_difference'])), mp.mpf('1e-39'))
                self.assertEqual(output['effective_rank'], len(p))
                results.append(dict(source=name, digits=digits, output=output,
                                    original_Gram_C=old[0]['C'], original_Gram_w=old[0]['w_residual']))
            # The earlier independent Fock route is used unchanged on this small case only.
            fock, _ = cw.prior_module('independent_fock_Cw').arbitrary(p, alpha, 48, 70)
            with mp.workdps(80):
                self.assertLess(abs(mp.mpf(fock[0]['C']) - mp.mpf(output['C'])), mp.mpf('1e-30'))
                self.assertLess(abs(mp.mpf(fock[0]['w_residual']) - mp.mpf(output['w_residual'])), mp.mpf('1e-30'))
            self.assertEqual(cw.sha(path), original)
        cw.atomic_json(self.directory / 'scientific_comparison.json', results)


if __name__ == '__main__':
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checkpoints)
    names = [test.id() for test in suite]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    cw.atomic_json(cw.OUT / 'checkpoint_test_results.json',
        dict(status='CURRENTLY_VERIFIED_PASS' if result.wasSuccessful() else 'FAILED',
             checks=names, tests_run=result.testsRun,
             failures=[name.id() for name, _ in result.failures], errors=[name.id() for name, _ in result.errors],
             wall_seconds=time.perf_counter() - start_wall, CPU_seconds=time.process_time() - start_cpu,
             maximum_source_size=16, maximum_digits=70, maximum_Fock_cutoff=48,
             target_source_Cw_computations=0, producer_sha256=cw.sha(__file__), wrapper_sha256=cw.sha(cw.__file__)))
    sys.exit(not result.wasSuccessful())
