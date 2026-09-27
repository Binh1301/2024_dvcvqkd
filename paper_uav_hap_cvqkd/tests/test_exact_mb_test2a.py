import unittest
from pathlib import Path

import torch

from scripts import run_exact_mb_test2a as runner
from scripts._common import load_yaml
from src.cvqkd.mutual_information import deterministic_mutual_information


class DeterministicMBMITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_yaml(runner.ROOT / "configs" / "default.yaml")
        cls.channel = runner.channel_fixture()

    def test_raw_repo_chain_and_exact_va(self):
        ensemble = runner.differentiable_mb_ensemble(torch.tensor(0.16, dtype=torch.float64))
        self.assertAlmostEqual(float(ensemble.probabilities.sum()), 1.0, places=14)
        self.assertGreater(float(ensemble.probabilities.min()), 0.0)
        self.assertAlmostEqual(float(ensemble.computed_va()[0]), 2.0, places=13)
        self.assertEqual(runner.nu_mb_repo(0.16), 6.8)

    def test_analytic_pmf_derivative_and_chain_factor(self):
        row = runner.pmf_derivative_checks(0.16)
        self.assertLess(row["max_abs_repo_error"], 1e-14)
        self.assertLess(row["max_abs_raw_chain_error"], 1e-12)
        self.assertAlmostEqual(row["sum_p"], 1.0, places=14)

    def test_deterministic_mi_repeats_and_full_matches_product(self):
        ensemble = runner.differentiable_mb_ensemble(0.16)
        t, epsilon = runner._channel_tensors(self.channel)
        full = deterministic_mutual_information(
            ensemble, t, epsilon, quadrature_order=8, implementation="full", noise_chunk_size=32
        )
        product = deterministic_mutual_information(
            ensemble, t, epsilon, quadrature_order=8, implementation="product"
        )
        repeat = deterministic_mutual_information(
            ensemble, t, epsilon, quadrature_order=8, implementation="product"
        )
        torch.testing.assert_close(full, product, rtol=1e-11, atol=1e-12)
        torch.testing.assert_close(product, repeat, rtol=0.0, atol=0.0)

    def test_autodiff_matches_deterministic_central_difference(self):
        value, gradient = runner.deterministic_value_and_gradient(0.16, self.channel, 16)
        h = 1e-3
        plus = runner.deterministic_value(0.16 + h, self.channel, 16, "product")
        minus = runner.deterministic_value(0.16 - h, self.channel, 16, "product")
        finite_difference = (plus - minus) / (2.0 * h)
        self.assertTrue(abs(value) > 0.0)
        self.assertLess(abs(finite_difference - gradient), 1e-8)

    def test_factorization_and_gh_convergence(self):
        factorization = runner.factorization_check(self.channel, order=8)
        self.assertTrue(factorization["cartesian_factorization"])
        self.assertTrue(factorization["pmf_factorization"])
        self.assertTrue(factorization["I_256_equals_2I_16PAM"])
        rows, selected = runner.gh_convergence(self.channel)
        self.assertIsNotNone(selected)
        self.assertEqual(len(rows), len(runner.GH_ORDERS) * len(runner.GRAD_VALUES))


if __name__ == "__main__":
    unittest.main()
