"""Fixed approval/budget and original numerical defaults; no AP."""
import unittest
from scripts import run_theta10_D55_P1_upper_refinement as run


class UpperExecutionTests(unittest.TestCase):
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
