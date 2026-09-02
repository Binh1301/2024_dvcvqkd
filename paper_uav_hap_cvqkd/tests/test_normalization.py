import unittest

import torch

from src.modulation.geometric_shaping import GlobalGeometricShaping
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import (
    c4_orbit_masses,
    expand_c4_orbit_masses,
    maxwell_boltzmann_pmf,
    square_qam256,
)


class NormalizationTests(unittest.TestCase):
    def test_scalar_normalization_exact_moments_and_gradients(self):
        logits = torch.linspace(-1.0, 1.0, 64, dtype=torch.float64, requires_grad=True)
        q = torch.softmax(logits, dim=0).unsqueeze(0)
        probabilities = expand_c4_orbit_masses(q)
        geometry = GlobalGeometricShaping(square_qam256())
        relative = geometry()
        variance = torch.tensor([2.7], dtype=torch.float64)
        amplitudes = physical_amplitudes(probabilities, relative, variance)

        mean = torch.sum(probabilities * amplitudes, dim=-1)
        pseudomoment = torch.sum(probabilities * amplitudes.square(), dim=-1)
        computed_va = 2.0 * torch.sum(probabilities * amplitudes.abs().square(), dim=-1)
        self.assertLess(float(mean.abs().max().detach()), 1e-12)
        self.assertLess(float(pseudomoment.abs().max().detach()), 1e-12)
        self.assertTrue(torch.allclose(computed_va, variance, atol=1e-12, rtol=0.0))

        objective = amplitudes[0, 0].abs().square() + probabilities[0, 0]
        objective.backward()
        self.assertGreater(float(torch.linalg.vector_norm(logits.grad).detach()), 0.0)
        self.assertGreater(
            float(torch.linalg.vector_norm(geometry.raw_coordinates.grad).detach()), 0.0
        )

    def test_mb_round_trip_and_exact_variance(self):
        probabilities = maxwell_boltzmann_pmf(0.1).unsqueeze(0)
        q = c4_orbit_masses(probabilities)
        self.assertTrue(
            torch.allclose(expand_c4_orbit_masses(q), probabilities, atol=1e-14, rtol=0.0)
        )
        variance = torch.tensor([3.0], dtype=torch.float64)
        relative = GlobalGeometricShaping(square_qam256())()
        amplitudes = physical_amplitudes(probabilities, relative, variance)
        computed = 2.0 * torch.sum(probabilities * amplitudes.abs().square(), dim=-1)
        self.assertTrue(torch.allclose(computed, variance, atol=1e-12, rtol=0.0))

    def test_no_state_dependent_relative_geometry(self):
        geometry = GlobalGeometricShaping(square_qam256())
        first = geometry()
        second = geometry()
        self.assertTrue(torch.equal(first, second))
        self.assertEqual(tuple(geometry.raw_coordinates.shape), (64, 2))


if __name__ == "__main__":
    unittest.main()
