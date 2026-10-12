"""Cheap retry scope checks; never launches AP or native dummy processes."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import retry_theta10_D55_grid_timeout as retry


class RetryScopeTests(unittest.TestCase):
    def test_exact_timeout_identity_and_old_record_not_mutated(self):
        old = retry.batch.read(retry.BASE / 'batch_checkpoint.json')
        _, row = retry.candidate()
        previous = old['queue'][27]
        self.assertEqual((row['nu_raw_hex'], row['V_A_hex']), (.25.hex(), 3.5.hex()))
        self.assertEqual(row['source_cache_key'], previous['source_cache_key'])
        self.assertEqual(row['original_source_identity'], previous['original_source_identity'])
        self.assertEqual(row['attempt_number'], 0)
        self.assertEqual(previous['status'], 'TIMEOUT')

    def test_same_internal_evaluator_and_existing_safety_limits(self):
        self.assertEqual(retry.batch.INTERNAL, 3600.)
        self.assertEqual(retry.batch.SOURCE_OUTER, 3720.)
        self.assertEqual(retry.TOTAL, 7200.)
        self.assertEqual(retry.RESERVE, 1800.)

    def test_existing_retry_output_blocks_repeat_before_any_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(retry, 'OUT', Path(directory)), patch.object(retry, 'supervise') as launch:
                with self.assertRaises(AssertionError):
                    retry.run()
                launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
