import math
import unittest

import numpy as np

from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.pointing_error import pointing_parameters, pointing_power_transmittance
from src.channel.turbulence import turbulence_beam_wander_variance_m2


class ChannelTests(unittest.TestCase):
    def _sample(self, count=1000):
        return sample_fso_channel(
            geometry=LinkGeometry(20_000.0, 0.0, 0.0),
            wavelength_m=1550e-9,
            visibility_km=10.0,
            beam_waist_m=0.0626,
            aperture_radius_m=0.2,
            cn2_m_minus_two_thirds=1e-15,
            sample_count=count,
            rng=np.random.default_rng(2026),
        )

    def test_transmittance_support(self):
        result = self._sample()
        upper = result.atmospheric_transmittance * result.pointing.t0_power
        self.assertTrue(np.all(result.transmittance >= 0.0))
        self.assertTrue(np.all(result.transmittance <= upper))
        self.assertTrue(result.exact_csi_oracle)

    def test_rayleigh_scale_matches_per_axis_variance(self):
        result = self._sample(200_000)
        expected_mean = result.sigma_axis_m * math.sqrt(math.pi / 2.0)
        expected_second_moment = 2.0 * result.sigma_axis_m**2
        self.assertLess(abs(result.radial_displacement_m.mean() / expected_mean - 1.0), 0.01)
        self.assertLess(
            abs(np.mean(result.radial_displacement_m**2) / expected_second_moment - 1.0), 0.01
        )

    def test_zero_displacement_has_maximum_coupling(self):
        parameters = pointing_parameters(0.2, 0.0626, 1550e-9, 20_000.0)
        self.assertAlmostEqual(float(pointing_power_transmittance(0.0, parameters)), parameters.t0_power)

    def test_cosine_to_minus_four_factor(self):
        vertical = turbulence_beam_wander_variance_m2(1e-15, 20_000.0, 0.0626, 0.0)
        angle = math.radians(30.0)
        tilted = turbulence_beam_wander_variance_m2(1e-15, 20_000.0, 0.0626, angle)
        self.assertAlmostEqual(tilted / vertical, math.cos(angle) ** -4, places=12)


if __name__ == "__main__":
    unittest.main()

