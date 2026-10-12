"""Operational batch2 contract; no physical or source computation."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_theta10_D55_mb_batch2 as run


class Batch2Contract(unittest.TestCase):
    def test_exact_binary64_and_source_dirs(self):
        self.assertEqual(run.PAIRS,((.165,5.475),(.165,5.425000000000001),(.15,6.25)))
        self.assertNotEqual(run.PAIRS[1][1].hex(),float('5.425').hex())
        self.assertEqual(run.PAIRS[1][1].hex(),'0x1.5b33333333334p+2')
        self.assertEqual(len(run.DIRS),4)
        self.assertTrue(all(p.is_absolute() for p in run.DIRS))
        self.assertIn(run.BASE/'exact_source_cache',run.DIRS)

    def test_original_algorithm_parameters(self):
        self.assertEqual((run.ao.K_TOLERANCE,run.ao.PARAMETER_TOLERANCE,
            run.ao.MAX_AO_ITERATIONS,run.ao.MAX_REFINEMENT_STAGES),(1e-8,1e-6,6,4))
        self.assertIs(run.ao,run.previous.ao)
        self.assertIs(run.supervisor,run.previous.supervisor)
        self.assertEqual(len(run.sweep.DISTANCES_KM)*len(run.sweep.BASE_STARTS)+25,129)


if __name__=='__main__':
    unittest.main()
