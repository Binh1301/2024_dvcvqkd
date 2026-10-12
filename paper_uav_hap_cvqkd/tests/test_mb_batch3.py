"""Frozen-method Batch3 orchestration contract; no source or channel computation."""
import unittest
from scripts import run_theta10_D55_mb_batch3 as run


class Batch3Contract(unittest.TestCase):
    def test_exact_order_baseline_and_cache_directories(self):
        self.assertEqual(run.PAIRS, ((.165,5.4625),(.165,5.4875),(.16531250000000003,5.5)))
        self.assertEqual(run.PAIRS[2][0].hex(), '0x1.528f5c28f5c2ap-3')
        self.assertEqual(run.BASE.name, 'batch_2')
        self.assertEqual(run.OUT.name, 'batch_3')
        self.assertEqual(len(run.DIRS), 5)
        self.assertTrue(all(p.is_absolute() for p in run.DIRS))
        self.assertIn(run.BASE/'exact_source_cache', run.DIRS)

    def test_original_scientific_and_optimizer_modules(self):
        self.assertIs(run.ao, run.previous.ao)
        self.assertIs(run.source, run.previous.source)
        self.assertIs(run.supervisor, run.previous.supervisor)
        self.assertEqual((run.ao.K_TOLERANCE, run.ao.PARAMETER_TOLERANCE,
                          run.ao.MAX_AO_ITERATIONS, run.ao.MAX_REFINEMENT_STAGES), (1e-8,1e-6,6,4))
        self.assertEqual(len(run.sweep.DISTANCES_KM)*len(run.sweep.BASE_STARTS)+25, 129)


if __name__ == '__main__':
    unittest.main()
