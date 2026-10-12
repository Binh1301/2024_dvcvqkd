import unittest
from scripts import prepare_theta10_D55_ao_phase2a as prep


class Phase2APreparation(unittest.TestCase):
    def test_original_binary64_pairs_and_excluded_hard_source(self):
        self.assertEqual(prep.PAIRS,((.165,(5.4875+5.5)/2),(.165,(5.5+5.525)/2),((.165+.16562500000000002)/2,5.5)))
        self.assertNotIn(prep.HARD_PAIR,prep.PAIRS)
        self.assertEqual(prep.OUT,prep.audit.OUT/'phase_2A')
        self.assertEqual((prep.ao.K_TOLERANCE,prep.ao.PARAMETER_TOLERANCE,prep.ao.MAX_AO_ITERATIONS,prep.ao.MAX_REFINEMENT_STAGES),(1e-8,1e-6,6,4))
        with self.assertRaises(AssertionError):
            prep.audit.forbidden()


if __name__=='__main__':
    unittest.main()
