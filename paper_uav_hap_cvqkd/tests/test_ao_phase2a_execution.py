import unittest
from scripts import run_theta10_D55_ao_phase2a as run


class Phase2AExecution(unittest.TestCase):
    def test_approved_pairs_budget_and_original_routines(self):
        self.assertEqual(tuple((float(p['nu_raw']),float(p['V_A'])) for p in run.points()),run.prep.PAIRS)
        self.assertNotIn(run.prep.HARD_PAIR,run.prep.PAIRS)
        self.assertEqual(run.budget_limit(8000,1000),3600)
        self.assertEqual(run.budget_limit(1500,1000),20)
        self.assertLess(run.budget_limit(1500,1100),0)
        self.assertIs(run.ao,run.prep.audit.baseline.ao)
        self.assertIs(run.safe.supervised_process,run.prep.safe.supervised_process)


if __name__=='__main__':
    unittest.main()
