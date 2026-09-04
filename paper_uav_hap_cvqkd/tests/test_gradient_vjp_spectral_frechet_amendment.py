import json
from pathlib import Path
import unittest
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]

def _frechet_inverse_sqrt(matrix, direction):
    values, vectors = torch.linalg.eigh(matrix)
    roots = torch.sqrt(values)
    loewner = -1.0 / (roots[:, None] * roots[None, :] * (roots[:, None] + roots[None, :]))
    local = vectors.mH @ ((direction + direction.mH) / 2) @ vectors
    return vectors @ (loewner * local) @ vectors.mH

def _inverse_sqrt(matrix):
    values, vectors = torch.linalg.eigh(matrix)
    return vectors @ torch.diag(torch.rsqrt(values)).to(torch.complex128) @ vectors.mH

class SpectralFrechetAmendmentTests(unittest.TestCase):
    def test_distinct_and_repeated_loewner_identity(self):
        values = torch.tensor([1.0, 4.0], dtype=torch.float64)
        roots = torch.sqrt(values)
        loewner = -1 / (roots[:, None] * roots[None, :] * (roots[:, None] + roots[None, :]))
        self.assertAlmostEqual(loewner[0, 1].item(), ((values[0] ** -0.5 - values[1] ** -0.5) / (values[0] - values[1])).item())
        self.assertAlmostEqual(loewner[0, 0].item(), -0.5)

    def test_identity_and_cluster_are_finite_and_basis_invariant(self):
        matrix = torch.diag(torch.tensor([2.0, 2.0, 5.0], dtype=torch.float64)).to(torch.complex128)
        direction = torch.tensor([[1, 1j, 0], [-1j, 2, 0], [0, 0, 3]], dtype=torch.complex128)
        rotation = torch.tensor([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=torch.complex128)
        left = _frechet_inverse_sqrt(matrix, direction)
        right = rotation @ _frechet_inverse_sqrt(rotation.mH @ matrix @ rotation, rotation.mH @ direction @ rotation) @ rotation.mH
        self.assertTrue(torch.isfinite(left).all())
        torch.testing.assert_close(left, right, atol=1e-10, rtol=1e-9)

    def test_complex_spd_matches_central_difference(self):
        matrix = torch.tensor([[3, 1j], [-1j, 4]], dtype=torch.complex128)
        direction = torch.tensor([[1, 0.5j], [-0.5j, -1]], dtype=torch.complex128)
        h = 1e-6
        numerical = (_inverse_sqrt(matrix + h * direction) - _inverse_sqrt(matrix - h * direction)) / (2 * h)
        torch.testing.assert_close(_frechet_inverse_sqrt(matrix, direction), numerical, atol=1e-10, rtol=1e-9)

    def test_protocol_contract_and_lifecycle(self):
        config = yaml.safe_load((ROOT / "configs/gradient_vjp_spectral_frechet_amendment_v1.yaml").read_text())
        json.loads((ROOT / "schemas/gradient_vjp_spectral_frechet_amendment_v1.schema.json").read_text())
        self.assertEqual(config["eigenvalue_gap_threshold"], "forbidden")
        self.assertEqual(config["synthetic_preflight"]["absolute_tolerance"], 1e-10)
        self.assertIn("torch_eigh_eigenvector_backward", config["forbidden"])
        self.assertFalse(any(config["lifecycle_guards"].values()))
