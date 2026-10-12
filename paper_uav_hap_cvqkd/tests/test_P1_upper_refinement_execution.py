"""Fixed approval/budget and original numerical defaults; no AP."""
import unittest
import sys
import tempfile
from unittest.mock import patch
from scripts import run_theta10_D55_P1_upper_refinement as run


class UpperExecutionTests(unittest.TestCase):
    def test_no_automatic_ap(self):
        with patch.object(run.OUT.__class__, 'mkdir') as mkdir:
            with self.assertRaisesRegex(SystemExit, 'AP NOT_RUN'):
                run.main()
            mkdir.assert_not_called()

    def test_actual_supervisor_cleans_descendants(self):
        # Short integration workers only: no source moments, channel, SKR or AO.
        for root_sleep, timeout in ((.5, False), (30, True)):
            with self.subTest(timeout=timeout), tempfile.TemporaryFile(mode='w+', encoding='utf-8') as log:
                code = ('import subprocess,sys,time; '
                    'subprocess.Popen([sys.executable,"-B","-c","import time; time.sleep(30)"]); '
                    f'time.sleep({root_sleep})')
                receipt = run.checked_supervised_process([sys.executable, '-B', '-c', code], 6., log)
                self.assertEqual(receipt['deadline_exceeded'], timeout)
                self.assertTrue(receipt['wall_limit_respected'])
                self.assertTrue(receipt['no_watchdog_thread_remaining'])
                self.assertTrue(receipt['sleep_prevention']['active_verified'])
                self.assertTrue(receipt['sleep_prevention']['released_verified'])
                self.assertIn(receipt['power_watch']['abort_reason'], (None, 'ABSOLUTE_DEADLINE'))
                self.assertGreaterEqual(receipt['accounted_processes'], 2)
                self.assertTrue(receipt['actual_job_cleanup'])
                for cleanup in receipt['actual_job_cleanup']:
                    self.assertTrue(cleanup['verified'])
                    self.assertTrue(cleanup['handle_closed'])
                    self.assertEqual(cleanup['active_processes_remaining'], 0)

    def test_unverified_cleanup_blocks_progress(self):
        receipt = {'actual_job_cleanup': [{'verified': False, 'handle_closed': True}]}
        with tempfile.TemporaryDirectory() as directory, patch.object(run, 'OUT', run.Path(directory)), \
                patch.object(run, 'checked_supervised_process', return_value=receipt), patch.object(run, 'save') as save:
            with self.assertRaisesRegex(AssertionError, 'Actual worker cleanup not verified'):
                run.supervise('source', 6.)
            save.assert_called_once_with('source_supervision.json', receipt)

    def test_deadline_preserves_reserve(self):
        self.assertEqual(run.probe_limit(0., 7200.), 5400.)
        self.assertEqual(run.probe_limit(25., 7200.), 5375.)
        self.assertEqual(run.probe_limit(6000., 7200.), 0.)

    def test_original_identity_and_defaults(self):
        p = run.saved.read(run.prep.OUT / 'confirmed_candidate.json')
        self.assertEqual(run.saved.ao.json_hash(p['original_source_identity']), run.KEY)
        self.assertEqual((run.NU.hex(), run.VA.hex()), ('0x1.51eb851eb851fp-3', '0x1.6066666666666p+2'))
        self.assertEqual((run.saved.ao.MAX_AO_ITERATIONS, run.saved.ao.K_TOLERANCE,
            run.saved.ao.PARAMETER_TOLERANCE, run.saved.ao.MAX_REFINEMENT_STAGES), (6, 1e-8, 1e-6, 4))
        self.assertLessEqual(len(str(run.CACHE / (run.KEY + '.json.tmp'))), 247)


if __name__ == '__main__':
    unittest.main()
