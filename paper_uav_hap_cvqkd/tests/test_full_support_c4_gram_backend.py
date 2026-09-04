import unittest
from unittest.mock import patch
import inspect

import torch

from src.cvqkd import gram_moments as gm
from src.modulation.joint_ps_gs import reference_ensemble


class FullSupportC4GramTests(unittest.TestCase):
    def test_matrix_function_c_and_residual_w_match_full_support_eigenbasis_reference(self):
        torch.manual_seed(17)
        p = torch.full((64,), 1 / 64, dtype=torch.float64)
        z = torch.arange(1, 65, dtype=torch.float64).to(torch.complex128)
        sectors = gm._sectors(p, z)

        values, vectors = zip(*(torch.linalg.eigh(matrix) for matrix in sectors))
        a_blocks = []
        coefficients = []
        reference_c = torch.zeros((), dtype=torch.float64)
        for sector in range(4):
            previous = (sector - 1) % 4
            matrix_element = vectors[sector].mH @ (z[:, None] * vectors[previous])
            a_support = torch.sqrt(values[sector])[:, None] * matrix_element / torch.sqrt(values[previous])[None, :]
            reference_c += torch.sum(torch.sqrt(values[sector])[:, None] * torch.sqrt(values[previous])[None, :] * a_support.abs().square()).real
            a_blocks.append(torch.sqrt(values[sector])[:, None] * a_support / torch.sqrt(values[previous])[None, :])
            coefficients.append(torch.sqrt(values[sector])[:, None] * vectors[sector].mH / (2 * torch.sqrt(p))[None, :])
        transformed = [a_blocks[sector] @ coefficients[(sector - 1) % 4] for sector in range(4)]
        inner = sum(torch.sum(coefficients[sector].conj() * transformed[sector], dim=0) for sector in range(4))
        first = sum(torch.sum(values[(sector - 1) % 4][None, :] * a_blocks[sector].abs().square()).real for sector in range(4))
        reference_w = first - torch.sum(4 * p * inner.abs().square()).real

        result, gate = gm._fast(p, z)
        self.assertIsNotNone(result, gate)
        torch.testing.assert_close(result["C"], reference_c, atol=1e-10, rtol=1e-10)
        torch.testing.assert_close(result["w"], reference_w, atol=1e-10, rtol=1e-10)

    def test_fast_path_vjp_is_finite_at_repeated_sector_spectrum(self):
        p = torch.full((64,), 1 / 64, dtype=torch.float64)
        z = torch.linspace(0.1, 0.2, 64, dtype=torch.float64).to(torch.complex128).requires_grad_()
        identity = torch.eye(64, dtype=torch.complex128) / 64

        def repeated_sectors(_p, prototypes):
            delta = prototypes[0].real - 0.1
            direction = torch.diag(torch.linspace(-0.2, 0.2, 64, dtype=torch.float64)).to(torch.complex128)
            return [identity + delta * direction for _ in range(4)]

        with patch.object(gm, "_sectors", side_effect=repeated_sectors):
            result, _ = gm._fast(p, z)
            self.assertIsNotNone(result)
            gradient, = torch.autograd.grad(result["C"] + result["w"], z)
        self.assertTrue(torch.isfinite(gradient).all())

    def test_fast_path_differentiable_graph_does_not_use_eigenvectors(self):
        source = inspect.getsource(gm._fast)
        self.assertNotIn("vectors[", source)

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
        response = {
    "status": "FULL_SUPPORT_CONVERGED",
    "C": "0.2",
    "w": "0.01",
    "rows": [
        {
            "digits": 1050,
            "rank": 256,
            "resolved": True,
            "minimum_eigenvalue": "1e-20",
        },
        {
            "digits": 1250,
            "rank": 256,
            "resolved": True,
            "minimum_eigenvalue": "1e-20",
        },
        {
            "digits": 1450,
            "rank": 256,
            "resolved": True,
            "minimum_eigenvalue": "1e-20",
        },
    ],}
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
