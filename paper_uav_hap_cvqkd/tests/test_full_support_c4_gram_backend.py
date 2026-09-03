import unittest
from unittest.mock import patch

import torch

from src.cvqkd import gram_moments as gm
from src.modulation.joint_ps_gs import reference_ensemble


class FullSupportC4GramTests(unittest.TestCase):
    def test_fast_path_keeps_all_256_modes_on_well_conditioned_synthetic_sectors(self):
        p = torch.full((64,), 1 / 64, dtype=torch.float64)
        z = torch.zeros(64, dtype=torch.complex128)
        with patch.object(gm, "_sectors", return_value=[torch.eye(64, dtype=torch.complex128) / 64 for _ in range(4)]):
            result, gate = gm._fast(p, z)
        self.assertIsNotNone(result)
        self.assertTrue(gate["all_sectors_positive"])
        self.assertEqual(result["C"].item(), 0.0)
        self.assertEqual(result["w"].item(), 0.0)

    def test_fallback_is_deterministic_and_threshold_is_diagnostic_only(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=0.1)
        response = {"status": "FULL_SUPPORT_CONVERGED", "C": "0.2", "w": "0.01", "rows": [{"digits": 1050}, {"digits": 1250}, {"digits": 1450}]}
        with patch.object(gm, "_fast", return_value=(None, {"all_sectors_positive": False})), patch.object(gm, "_fallback", return_value=response):
            left = gm.c4_gram_source_moments(ensemble, density_eigenvalue_tolerance=1e-13)
            right = gm.c4_gram_source_moments(ensemble, density_eigenvalue_tolerance=1e-10)
        self.assertEqual(left.diagnostics[0]["route"], "ARBITRARY_PRECISION_FALLBACK")
        self.assertEqual(left.diagnostics[0]["support_size"], 256)
        torch.testing.assert_close(left.coherent_correlation, right.coherent_correlation)
        torch.testing.assert_close(left.w, right.w)

    def test_fallback_refuses_gradient_authorization(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=0.1)
        ensemble.probabilities.requires_grad_()
        with patch.object(gm, "_fast", return_value=(None, {})):
            with self.assertRaisesRegex(gm.FullSupportGradientUnavailable, "EVALUATION_ONLY"):
                gm.c4_gram_source_moments(ensemble, density_eigenvalue_tolerance=1e-13)

    def test_worker_request_is_float_hex_and_has_no_regularization(self):
        source = (gm.Path(__file__).parents[1] / "src/cvqkd/gram_moments.py").read_text()
        self.assertIn("float.hex", source)
        self.assertNotIn("epsilon I", source)
        self.assertNotIn("lambda >", source)


if __name__ == "__main__":
    unittest.main()
