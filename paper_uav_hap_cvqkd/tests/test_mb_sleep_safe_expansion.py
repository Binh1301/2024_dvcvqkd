"""Operational coordinator contract; no AP, channel or SKR evaluation."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_theta10_D55_mb_sleep_safe_expansion as run


class ExpansionContract(unittest.TestCase):
    def test_exact_order_and_original_search_settings(self):
        self.assertEqual(tuple((n.hex(),v.hex()) for n,v in run.PAIRS), (
            (float('0.16562500000000002').hex(),float('5.5').hex()),
            (float('0.165').hex(),float('5.45').hex()),
            (float('0.165').hex(),float('5.525').hex())))
        self.assertEqual((run.ao.K_TOLERANCE,run.ao.PARAMETER_TOLERANCE,
            run.ao.MAX_AO_ITERATIONS,run.ao.MAX_REFINEMENT_STAGES),(1e-8,1e-6,6,4))
        self.assertEqual(len(run.sweep.DISTANCES_KM),26)
        self.assertEqual(len(run.sweep.BASE_STARTS)*26+25,129)

    def test_scientific_routines_are_original_imports(self):
        self.assertIs(run.source,run.prior.source)
        self.assertIs(run.ao,run.prior.ao)
        self.assertIs(run.supervisor,run.prior.supervisor)
        self.assertTrue(all(p.is_absolute() for p in run.SOURCE_DIRS))
        with self.assertRaises(AssertionError):
            run.prior.forbidden()


if __name__=='__main__':
    unittest.main()
