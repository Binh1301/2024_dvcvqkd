import unittest

from scripts import run_exact_mb_reconciliation as reconciliation
from scripts.run_exact_mb_test2 import build_mb_ensemble
from scripts._common import load_yaml


class ExactMBReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_yaml(reconciliation.ROOT / "configs" / "default.yaml")

    def test_same_fixture_uses_exact_raw_repo_and_common_ensemble_inputs(self):
        ensemble = build_mb_ensemble(self.config, 0.16, 2.0)
        self.assertAlmostEqual(float(ensemble.probabilities.sum()), 1.0, places=14)
        self.assertAlmostEqual(float(ensemble.computed_va()[0]), 2.0, places=13)
        self.assertEqual(reconciliation.channel_fixture()["T_eff"], 0.0002548668306761576)
        self.assertEqual(42.5 * 0.16, 6.8)

    def test_historical_coarse_rows_are_available_for_reconciliation(self):
        rows = reconciliation.load_old_rows()
        self.assertEqual(set(rows), {0.10, 0.13, 0.14, 0.15, 0.16, 0.17, 0.20})
        self.assertAlmostEqual(float(rows[0.16]["I_AB"]), 0.00043076173163427713)


if __name__ == "__main__":
    unittest.main()
