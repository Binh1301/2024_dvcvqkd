"""Lightweight assertions for the one-point negative-SKR diagnostic."""

from __future__ import annotations

import unittest
import json

from scripts.run_negative_skr_diagnostic import OUTPUT_DIR, _covariance, _verify_hashes


class NegativeSkrDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((OUTPUT_DIR / "diagnostic_result.json").read_text(encoding="utf-8"))

    def test_source_identity_and_status(self):
        provenance = self.result["provenance"]
        self.assertEqual(provenance["source_cache_key"],
                         "77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c")
        self.assertEqual(provenance["ensemble_hash"],
                         "430914e792382cce5d92b0ff5ba4e8a641e912bce78c8565dbc18540b92b2faa")
        self.assertEqual(self.result["status"], "CONFIGURATION_MISMATCH")

    def test_corrected_noise_and_moment_identities(self):
        moments = self.result["pdf_and_moments"]["corrected"]
        noise = self.result["noise"]
        self.assertAlmostEqual(moments["physical_T_eff"],
                               moments["physical_mean_sqrt_eta"] ** 2, places=15)
        self.assertAlmostEqual(noise["N_eff"], noise["N_eff_from_three_moments"], places=15)
        self.assertGreater(noise["fading_fraction_of_N_eff"], 0.98)

    def test_covariance_entropy_and_skr_reproduction(self):
        covariance = self.result["covariance"]
        self.assertAlmostEqual(covariance["historical"]["chi_BE"],
                               0.5244988060866094, places=14)
        self.assertAlmostEqual(covariance["corrected"]["chi_BE"],
                               1.2195896239728028, places=14)
        self.assertTrue(covariance["historical"]["physicality"])
        self.assertTrue(covariance["corrected"]["physicality"])
        skr = self.result["skr_decomposition"]
        self.assertAlmostEqual(skr["historical_K"], 0.07798099387393764, places=14)
        self.assertAlmostEqual(skr["mixture_delta_K"],
                               -0.8555700086093022, places=14)

    def test_unresolved_precision_is_preserved(self):
        validation = self.result["validation"]
        self.assertTrue(validation["all_boolean_checks_pass"])
        self.assertEqual(validation["corrected_MI_precision_status"],
                         "SAMPLING_PRECISION_NOT_MET")
        self.assertEqual(validation["corrected_security_bound_status"],
                         "NOT_ESTABLISHED")

    def test_independent_uncertainty_and_symplectic_spectrum(self):
        import numpy as np
        omega = np.kron(np.eye(2), [[0., 1.], [-1., 0.]])
        for mode in ("historical", "corrected"):
            cov = self.result["covariance"][mode]
            gamma = np.array(cov["Gamma_AB"])
            self.assertGreater(float(np.linalg.eigvalsh(gamma + 1j*omega).min()), 0.)
            spectrum = sorted(abs(np.linalg.eigvals(1j*omega @ gamma)))
            np.testing.assert_allclose(
                spectrum, [cov["lambda_2"]]*2 + [cov["lambda_1"]]*2,
                atol=1e-13, rtol=0.)

    def test_full_support_and_retained_moments_are_distinguished(self):
        audit = self.result["configuration_audit"]["current_producer_audit"]
        stages = audit["PDF_moment_stages_order_dependent"]
        self.assertGreater(stages[2]["T_eff"], stages[3]["T_eff"])
        self.assertGreater(stages[4]["T_eff"], stages[3]["T_eff"])
        self.assertAlmostEqual(sum(row["delta_Teff_from_previous"] for row in stages),
                               stages[-1]["T_eff"]-stages[0]["T_eff"], places=15)
        for row in audit["corrected_full_support_quadrature"].values():
            self.assertLess(abs(row["residual_against_full_support_formula"]), 1e-13)

    def test_covariance_sensitivities_do_not_replace_protocols(self):
        controls = self.result["covariance_sensitivities"]
        self.assertIn("not protocols", controls["interpretation"])
        rows = controls["rows"]
        self.assertTrue(all(row["physicality"] for row in rows))
        self.assertLess(rows[1]["chi_BE"], rows[0]["chi_BE"])
        self.assertGreater(rows[3]["chi_BE"]-rows[2]["chi_BE"], .7)

    def test_invalid_covariance_and_provenance_fail_closed(self):
        with self.assertRaises(ValueError):
            _covariance(.2, .0186, 6.)
        with self.assertRaisesRegex(ValueError, "Protected input"):
            _verify_hashes({"configs/default.yaml": "0"*64})


if __name__ == "__main__":
    unittest.main()
