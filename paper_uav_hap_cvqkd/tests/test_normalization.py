import unittest

import torch

from src.modulation.normalization import weighted_center_and_normalize
from src.modulation.qam256 import maxwell_boltzmann_pmf, square_qam256


class NormalizationTests(unittest.TestCase):
    def test_weighted_mean_energy_and_gradients(self):
        logits = torch.linspace(-1.0, 1.0, 256, dtype=torch.float64, requires_grad=True)
        probabilities = torch.softmax(logits, dim=0).unsqueeze(0)
        coordinates = torch.view_as_real(square_qam256()).clone().requires_grad_(True)
        raw = torch.view_as_complex(coordinates.contiguous())
        unit = weighted_center_and_normalize(probabilities, raw)
        mean = torch.sum(probabilities * unit, dim=-1)
        energy = torch.sum(probabilities * unit.abs().square(), dim=-1)
        self.assertLess(float(mean.abs().max().detach()), 1e-12)
        self.assertTrue(torch.allclose(energy, torch.ones_like(energy), atol=1e-12, rtol=0.0))
        objective = unit.real.square().mean() + 0.7 * unit.imag.square().mean()
        objective.backward()
        self.assertGreater(float(torch.linalg.vector_norm(logits.grad).detach()), 0.0)
        self.assertGreater(float(torch.linalg.vector_norm(coordinates.grad).detach()), 0.0)

    def test_mb_normalization(self):
        probabilities = maxwell_boltzmann_pmf(0.1).unsqueeze(0)
        unit = weighted_center_and_normalize(probabilities, square_qam256())
        self.assertAlmostEqual(
            float(torch.sum(probabilities * unit.abs().square())), 1.0, places=12
        )


if __name__ == "__main__":
    unittest.main()
