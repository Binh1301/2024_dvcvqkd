import math
import unittest

import torch

from src.modulation.qam256 import binomial_pmf, maxwell_boltzmann_pmf, square_qam256, uniform_pmf


class Qam256Tests(unittest.TestCase):
    def test_exact_16_by_16_grid_and_order(self):
        points = square_qam256()
        self.assertEqual(tuple(points.shape), (256,))
        scaled = points * math.sqrt(30.0)
        expected = torch.arange(16, dtype=torch.float64) - 7.5
        self.assertTrue(torch.allclose(torch.unique(scaled.real), expected, atol=1e-14, rtol=0.0))
        self.assertTrue(torch.allclose(torch.unique(scaled.imag), expected, atol=1e-14, rtol=0.0))
        self.assertTrue(
            torch.allclose(
                scaled[0], torch.tensor(-7.5 - 7.5j, dtype=torch.complex128), atol=1e-14, rtol=0.0
            )
        )
        self.assertTrue(
            torch.allclose(
                scaled[-1], torch.tensor(7.5 + 7.5j, dtype=torch.complex128), atol=1e-14, rtol=0.0
            )
        )

    def test_reference_probabilities(self):
        for pmf in (uniform_pmf(), binomial_pmf(), maxwell_boltzmann_pmf(0.1)):
            self.assertAlmostEqual(float(pmf.sum()), 1.0, places=14)
            self.assertTrue(bool(torch.all(pmf > 0.0)))
        self.assertTrue(torch.allclose(maxwell_boltzmann_pmf(0.0), uniform_pmf()))


if __name__ == "__main__":
    unittest.main()
