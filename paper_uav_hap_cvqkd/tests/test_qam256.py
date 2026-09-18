import math
import unittest

import torch

from src.modulation.qam256 import (
    binomial_pmf,
    canonical_square_qam256,
    c4_orbit_indices,
    c4_orbit_masses,
    expand_c4_orbit_masses,
    expand_c4_orbit_values,
    maxwell_boltzmann_pmf,
    square_qam256,
    uniform_pmf,
)


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

    def test_mb_uses_unscaled_square_grid_indices(self):
        nu = 0.37
        levels = torch.arange(16, dtype=torch.float64) - 7.5
        i_grid, q_grid = torch.meshgrid(levels, levels, indexing="ij")
        expected = torch.exp(-nu * (i_grid.square() + q_grid.square())).reshape(-1)
        expected = expected / expected.sum()
        self.assertTrue(
            torch.allclose(maxwell_boltzmann_pmf(nu), expected, atol=1e-15, rtol=0.0)
        )

    def test_fixed_mb_nu_point_one_energy_coefficient(self):
        probabilities = maxwell_boltzmann_pmf(0.1)
        coefficient = 2.0 * torch.sum(probabilities * square_qam256().abs().square())
        self.assertAlmostEqual(float(coefficient), 0.6637540564063298, places=14)

    def test_c4_mapping_preserves_row_major_labels(self):
        indices = c4_orbit_indices()
        self.assertEqual(tuple(indices.shape), (64, 4))
        self.assertEqual(torch.unique(indices).numel(), 256)
        points = square_qam256()
        representatives = points[indices[:, 0]]
        self.assertTrue(
            torch.allclose(expand_c4_orbit_values(representatives), points, atol=1e-14, rtol=0.0)
        )
        for row in indices.tolist():
            a, b = divmod(row[0], 16)
            self.assertGreaterEqual(a, 8)
            self.assertGreaterEqual(b, 8)
            self.assertEqual(
                row,
                [a * 16 + b, (15 - b) * 16 + a,
                 (15 - a) * 16 + (15 - b), b * 16 + (15 - a)],
            )

    def test_reference_pmf_orbit_round_trip_and_entropy_identity(self):
        for pmf in (uniform_pmf(), binomial_pmf(), maxwell_boltzmann_pmf(0.1)):
            q = c4_orbit_masses(pmf)
            restored = expand_c4_orbit_masses(q)
            self.assertTrue(torch.allclose(restored, pmf, atol=1e-14, rtol=0.0))
            hp = -torch.sum(torch.special.xlogy(pmf, pmf)) / math.log(2.0)
            hq = -torch.sum(torch.special.xlogy(q, q)) / math.log(2.0)
            self.assertAlmostEqual(float(hp - hq), 2.0, places=12)


if __name__ == "__main__":
    unittest.main()
