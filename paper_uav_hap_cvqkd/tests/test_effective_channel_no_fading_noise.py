"""One-reference checks; no source oracle, sampling, sweeps or optimization."""
import copy
import json
import math
import unittest
from unittest.mock import patch

import numpy as np
import torch

from scripts.run_effective_channel_no_fading_noise import ROOT, OUTPUT, SOURCE
from src.effective_channel_no_fading_noise import effective_channel


class NoFadingNoiseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((OUTPUT/"reference_result.json").read_text(encoding="utf-8"))
        cls.row = cls.result["record"]

    def test_physical_law_and_three_moments_preserved(self):
        row = self.row
        self.assertTrue(all(value == 0 for value in row["channel_moment_preservation_residuals"].values()))
        self.assertEqual(row["T_eff"], row["mean_sqrt_eta"]**2)
        self.assertEqual(row["mean_eta_xi_total"], 2+(.0186-1)*row["mean_eta"])
        self.assertAlmostEqual(row["physical_probability_mass"], 1., places=13)
        self.assertGreater(row["outage_atom"], 0.)

    def test_noise_covariance_and_eq20_consistent(self):
        row = self.row
        self.assertEqual(row["xi_eff"], .0186)
        self.assertEqual(row["N_eff"], row["T_eff"]*.0186)
        self.assertEqual(row["b"], 1+row["T_eff"]*(row["VA"]+.0186))
        self.assertAlmostEqual(row["Z_star"], 2*math.sqrt(row["T_eff"])*row["C"]
                               -math.sqrt(2*row["T_eff"]*.0186*row["w"]), places=13)
        self.assertFalse(row["fading_noise_included"])
        self.assertGreater(row["physical_Bob_variance_diagnostic"]-row["b"], .4)

    def test_independent_quantum_covariance_spectrum_entropy(self):
        row = self.row
        matrix = np.array(row["Gamma_AB"])
        omega = np.kron(np.eye(2), [[0.,1.],[-1.,0.]])
        self.assertGreater(float(np.linalg.eigvalsh(matrix+1j*omega).min()), 0.)
        np.testing.assert_allclose(sorted(abs(np.linalg.eigvals(1j*omega@matrix))),
            [row["lambda_2"]]*2+[row["lambda_1"]]*2, atol=1e-12, rtol=0.)
        g = lambda n: 0. if n == 0 else (n+1)*math.log2(n+1)-n*math.log2(n)
        chi = g((row["lambda_1"]-1)/2)+g((row["lambda_2"]-1)/2)-g((row["lambda_3"]-1)/2)
        self.assertAlmostEqual(chi, row["chi_BE"], places=13)
        self.assertAlmostEqual(row["SKR"], .95*row["I_AB"]-chi, places=13)

    def test_fresh_discrete_mi_against_full_complex_mixture(self):
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        from src.cvqkd.mutual_information import deterministic_mutual_information
        with patch("src.cvqkd.gram_moments._fallback", side_effect=AssertionError("AP forbidden")):
            candidate = verified_candidate(SOURCE, unconstrained_config())
        self.assertEqual(candidate["ensemble_hash"], self.row["ensemble_hash"])
        full = float(deterministic_mutual_information(candidate["ensemble"],
            torch.tensor([self.row["T_eff"]],dtype=torch.float64),
            torch.tensor([.0186],dtype=torch.float64),quadrature_order=8,implementation="full")[0])
        self.assertAlmostEqual(full, self.row["MI_orders"][0]["I_AB"], places=12)
        self.assertTrue(self.row["MI_computed_fresh"])
        self.assertLess(self.row["MI_last_refinement_difference"], 1e-8)

    def test_mapping_does_not_mutate_moments_and_rejects_nonideal_input(self):
        original = copy.deepcopy(self.row)
        effective_channel(self.row, self.row["VA"])
        self.assertEqual(self.row, original)
        wrong = dict(original, chi_het=0.)
        with self.assertRaises(ValueError):
            effective_channel(wrong, self.row["VA"])
        with self.assertRaises(ValueError):
            effective_channel(dict(original, physical_probability_mass=.98), self.row["VA"])
        self.assertEqual(self.row["validated_fading_security_lower_bound"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
