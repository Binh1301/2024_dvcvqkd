import unittest
from pathlib import Path

from scripts._common import load_yaml
from scripts.run_mb_sweep_fixed_zeta30_va2 import NU_VALUES, _raw_mb_ensemble


class FixedMBSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_yaml(Path("configs/default.yaml"))

    def test_requested_grid_and_per_nu_va_normalization(self):
        self.assertEqual(NU_VALUES, tuple(round(0.05 + 0.01 * i, 2) for i in range(16)))
        entropies = []
        for nu in NU_VALUES:
            ensemble, checks = _raw_mb_ensemble(self.config, nu)
            self.assertAlmostEqual(checks["pmf_normalization"], 1.0, places=12)
            self.assertAlmostEqual(checks["VA_actual"], 2.0, places=10)
            self.assertTrue(bool((ensemble.probabilities >= 0.0).all()))
            entropies.append(checks["entropy_bits"])
        self.assertTrue(all(left >= right for left, right in zip(entropies, entropies[1:])))


if __name__ == "__main__":
    unittest.main()
