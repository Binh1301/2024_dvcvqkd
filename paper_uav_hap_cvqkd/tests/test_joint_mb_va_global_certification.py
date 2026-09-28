import csv
import math
import tempfile
import unittest
from pathlib import Path

import torch

from scripts import run_joint_mb_va_global_certification as runner
from scripts import run_joint_mb_va_optimization as joint
from scripts import run_exact_mb_test2 as exact
from src.cvqkd.mutual_information import deterministic_mutual_information


class JointMBVAGlobalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = exact.load_yaml(exact.ROOT / "configs" / "default.yaml")
        cls.channel = exact.channel_fixture()

    def test_raw_repo_chain_and_positive_normalized_ensemble(self):
        self.assertEqual(exact.nu_mb_repo(0.24), 10.2)
        ensemble = exact.build_mb_ensemble(self.config, 0.24, 1.95)
        self.assertAlmostEqual(float(ensemble.probabilities.sum()), 1.0, places=14)
        self.assertGreater(float(ensemble.probabilities.min()), 0.0)
        self.assertAlmostEqual(float(ensemble.computed_va()[0]), 1.95, places=13)

    def test_va_scaling_noise_and_peak_boundary(self):
        low = exact.build_mb_ensemble(self.config, 0.24, 1.90)
        high = exact.build_mb_ensemble(self.config, 0.24, 1.95)
        ratio = float(high.amplitudes.abs().square().max() / low.amplitudes.abs().square().max())
        self.assertAlmostEqual(ratio, 1.95 / 1.90, places=12)
        self.assertAlmostEqual(
            self.channel["epsilon_base"] + self.channel["c_phi"] * 1.95,
            0.02911275902783573,
            places=14,
        )
        bound = joint.feasible_vmax(self.config, 0.24)
        self.assertLess(float(high.amplitudes.abs().square().max()), 30.0)
        boundary = exact.build_mb_ensemble(self.config, 0.24, bound["V_A_max_feasible"])
        self.assertLessEqual(float(boundary.amplitudes.abs().square().max()), 30.0 + 1e-10)

    def test_analytic_boundary_matches_direct_peak(self):
        bound = joint.feasible_vmax(self.config, 0.25)
        ensemble = exact.build_mb_ensemble(self.config, 0.25, bound["V_A_max_feasible"])
        self.assertAlmostEqual(
            float(ensemble.amplitudes.abs().square().max()),
            30.0,
            places=10,
        )

    def test_common_hash_and_deterministic_mi_reproducibility(self):
        ensemble = exact.build_mb_ensemble(self.config, 0.24, 1.95)
        t = torch.tensor([self.channel["T_eff"]], dtype=torch.float64)
        epsilon = torch.tensor(
            [self.channel["epsilon_base"] + self.channel["c_phi"] * 1.95],
            dtype=torch.float64,
        )
        first = deterministic_mutual_information(ensemble, t, epsilon, quadrature_order=8, implementation="product")
        second = deterministic_mutual_information(ensemble, t, epsilon, quadrature_order=8, implementation="product")
        torch.testing.assert_close(first, second, rtol=0.0, atol=0.0)
        self.assertEqual(exact.ensemble_hash(ensemble), exact.ensemble_hash(ensemble))

    def test_cache_identity_includes_va_and_ensemble(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = exact.ExactMBEvaluator(
                self.config,
                self.channel,
                Path(directory),
                source_cache_dir=Path(directory),
                source_evaluator=lambda ensemble, **_: None,
            )
            first = runner.cache_identity(evaluator, self.config, 0.24, 1.90)
            second = runner.cache_identity(evaluator, self.config, 0.24, 1.95)
            self.assertNotEqual(first["source_cache_key"], second["source_cache_key"])
            self.assertNotEqual(first["ensemble_hash"], second["ensemble_hash"])

    def test_report_is_fail_closed_when_cache_is_incomplete(self):
        report_path = exact.ROOT / "results" / "joint_mb_va_global" / "run_report.json"
        if not report_path.is_file():
            self.skipTest("global certification runner has not been executed")
        report = __import__("json").loads(report_path.read_text(encoding="utf-8"))
        if report["coverage"]["full_global_grid"]:
            self.assertIn(report["status"], {"GLOBAL_OPTIMUM_UNRESOLVED", "INTERIOR_GLOBAL_OPTIMUM", "PEAK_BOUNDARY_GLOBAL_OPTIMUM", "NU_ENDPOINT_GLOBAL_OPTIMUM", "VA_ENDPOINT_GLOBAL_OPTIMUM"})
        else:
            self.assertEqual(report["status"], "GLOBAL_OPTIMUM_UNRESOLVED")
            self.assertEqual(report["global_certification"], "NOT_CERTIFIED")


if __name__ == "__main__":
    unittest.main()
