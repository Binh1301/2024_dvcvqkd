"""Saved numeric CSV results must retain numeric ranking and signed gaps."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import inventory
from extend_catalog import numeric_records
import run
from inventory import read,PRIOR


class SavedResultCheck(unittest.TestCase):
    def test_numeric_CSV_ranking_and_negative_gap(self):
        base=dict(zenith_deg='0',numerical_status='CURRENTLY_VERIFIED_PASS',source_evidence_class='VERIFIED_EXACT',family='Uniform')
        records=numeric_records([dict(base,ensemble_hash='worse',K_raw='-0.9'),dict(base,ensemble_hash='better',K_raw='-0.1')])
        result=run.select(records,read(PRIOR/'protocol.json'))
        self.assertEqual(result[0]['ensemble_hash'],'better')
        self.assertEqual(result[0]['K_raw'],-.1)
        self.assertAlmostEqual(result[0]['best_second_gap'],.8)
        self.assertIsInstance(result[0]['K_raw'],float)

    def test_numpy_summary_counts_are_saved_without_recomputing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(inventory,'OUT',Path(directory)):
                inventory.save('summary.json',dict(positive_candidate_rows=np.int64(12),strict_ready=np.bool_(False)))
            restored=inventory.read(Path(directory)/'summary.json')
        self.assertEqual(restored,dict(positive_candidate_rows=12,strict_ready=False))


if __name__=='__main__':unittest.main(verbosity=2)
