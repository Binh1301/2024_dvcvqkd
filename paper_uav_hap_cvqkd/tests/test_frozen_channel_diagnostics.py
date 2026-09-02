import math
import unittest

from src.channel.diagnostics import (
    frozen_channel_diagnostics,
    transformed_rayleigh_transmittance_quantile,
)
from src.channel.geometry import LinkGeometry
from src.channel.turbulence import UavMotion


class FrozenChannelDiagnosticsTests(unittest.TestCase):
    def _diagnostics(self, seed=202612):
        return frozen_channel_diagnostics(
            geometry=LinkGeometry(20_000.0, 1_000.0, 0.0),
            wavelength_m=1.55e-6,
            visibility_km=200.0,
            beam_waist_m=0.0157,
            aperture_radius_m=0.075,
            cn2_m_minus_two_thirds=1.0e-16,
            motion=UavMotion(),
            epsilon_minimum_snu=0.001,
            epsilon_maximum_snu=0.04,
            sample_count=20_000,
            seed=seed,
            quantile_probabilities=(0.1, 0.5, 0.9),
        )

    def test_approved_physical_derivations_and_support(self):
        result = self._diagnostics()
        derived = result["derived"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(derived["link_length_m"], 19_000.0)
        self.assertAlmostEqual(derived["atmospheric_power_transmittance"], 0.9316271221108952)
        self.assertAlmostEqual(derived["beam_radius_receiver_m"], 0.5972908436983067)
        self.assertAlmostEqual(
            derived["centered_aperture_power_coupling_t0_squared"], 0.031042111435033548
        )
        self.assertAlmostEqual(derived["sigma_turbulence_m"], 0.06459213118645223)
        self.assertAlmostEqual(derived["sigma_uav_m"], 0.10087960227047885)
        self.assertAlmostEqual(derived["sigma_r_rayleigh_scale_m"], 0.11978663350081199)
        support = derived["transmittance_support"]
        self.assertEqual(support["lower"], 0.0)
        self.assertFalse(support["lower_inclusive"])
        self.assertTrue(support["upper_inclusive"])
        self.assertGreater(support["upper"], 0.0)
        self.assertLessEqual(support["upper"], 1.0)

    def test_reproducible_namespaced_realization(self):
        first = self._diagnostics()
        second = self._diagnostics()
        left = first["monte_carlo_diagnostic"]
        right = second["monte_carlo_diagnostic"]
        self.assertEqual(left["joint_realization_sha256"], right["joint_realization_sha256"])
        self.assertEqual(left["transmittance_seed"], right["transmittance_seed"])
        self.assertEqual(left["excess_noise_seed"], right["excess_noise_seed"])
        self.assertNotEqual(
            left["joint_realization_sha256"],
            self._diagnostics(seed=202613)["monte_carlo_diagnostic"]["joint_realization_sha256"],
        )

    def test_analytic_quantile_is_monotone_and_matches_closed_gamma_two_case(self):
        upper = 0.2
        sigma = 0.1
        scale = 0.4
        probabilities = (0.1, 0.5, 0.9)
        quantiles = [
            transformed_rayleigh_transmittance_quantile(
                probability,
                upper_transmittance=upper,
                sigma_axis_m=sigma,
                scale_radius_m=scale,
                gamma=2.0,
            )
            for probability in probabilities
        ]
        self.assertTrue(all(left < right for left, right in zip(quantiles, quantiles[1:])))
        exponent = 2.0 * sigma**2 / scale**2
        for probability, quantile in zip(probabilities, quantiles):
            self.assertAlmostEqual(quantile, upper * probability**exponent, places=14)

    def test_independent_epsilon_is_nonconstant_and_in_support(self):
        result = self._diagnostics()["monte_carlo_diagnostic"]
        self.assertGreater(result["empirical_epsilon_variance_snu2"], 0.0)
        self.assertTrue(math.isfinite(result["empirical_t_epsilon_correlation"]))


if __name__ == "__main__":
    unittest.main()
