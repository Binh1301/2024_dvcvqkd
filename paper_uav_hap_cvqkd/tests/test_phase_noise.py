import math
import unittest

import torch

from src.channel.phase_noise import (
    phase_coefficient_from_parameters,
    phase_distortion_variance,
    phase_excess_noise,
    phase_noise_coefficient,
    total_excess_noise,
)


class PhaseNoiseTests(unittest.TestCase):
    def test_phase_variance_uses_si_wavelength_and_link_distance(self):
        value = phase_distortion_variance(2.0e-16, 1.55e-6, 19_000.0)
        expected = (
            2.46
            * 2.0e-16
            * (2.0 * math.pi / 1.55e-6) ** (7.0 / 6.0)
            * 19_000.0 ** (11.0 / 6.0)
        )
        self.assertAlmostEqual(value, expected)

    def test_c_phi_squares_tau_phi_squared_once(self):
        self.assertEqual(phase_noise_coefficient(3.0), 3.0 + 0.25 * 3.0**2)

    def test_zero_phase_is_explicitly_valid(self):
        tau = phase_distortion_variance(0.0, 1.55e-6, 19_000.0)
        c_phi = phase_noise_coefficient(tau)
        base = torch.tensor([0.01, 0.02], dtype=torch.float64)
        va = torch.tensor([0.5, 1.5], dtype=torch.float64)
        self.assertEqual(tau, 0.0)
        self.assertEqual(c_phi, 0.0)
        torch.testing.assert_close(total_excess_noise(base, va, c_phi), base)
        torch.testing.assert_close(phase_excess_noise(va, c_phi), torch.zeros_like(va))

    def test_total_noise_and_v_a_gradient(self):
        base = torch.tensor([0.01, 0.02], dtype=torch.float64)
        va = torch.tensor([0.5, 1.5], dtype=torch.float64, requires_grad=True)
        result = total_excess_noise(base, va, 0.25)
        torch.testing.assert_close(result, base + 0.25 * va)
        result.sum().backward()
        torch.testing.assert_close(va.grad, torch.full_like(va, 0.25))

    def test_coefficient_from_parameters_matches_two_stage_formula(self):
        tau = phase_distortion_variance(1.0e-16, 1.55e-6, 19_000.0)
        self.assertEqual(
            phase_coefficient_from_parameters(1.0e-16, 1.55e-6, 19_000.0),
            phase_noise_coefficient(tau),
        )

    def test_invalid_physical_parameters_fail_closed(self):
        with self.assertRaises(ValueError):
            phase_distortion_variance(-1.0, 1.55e-6, 19_000.0)
        with self.assertRaises(ValueError):
            phase_distortion_variance(1.0e-16, 0.0, 19_000.0)
        with self.assertRaises(ValueError):
            phase_distortion_variance(1.0e-16, 1.55e-6, 0.0)


if __name__ == "__main__":
    unittest.main()
