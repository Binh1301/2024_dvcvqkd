import unittest

import numpy as np

from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.turbulence import UavMotion


class ChannelProvenanceTests(unittest.TestCase):
    def _sample(self, **changes):
        values = {
            "geometry": LinkGeometry(20_000.0, 1_000.0, 0.0),
            "wavelength_m": 1.55e-6,
            "visibility_km": 200.0,
            "beam_waist_m": 0.0157,
            "aperture_radius_m": 0.075,
            "cn2_m_minus_two_thirds": 1.0e-16,
            "sample_count": 16,
            "rng": np.random.default_rng(12),
            "uav_motion": UavMotion(),
            "scintillation_log_variance": 0.0,
            "aoa_model": "disabled",
        }
        values.update(changes)
        return sample_fso_channel(**values)

    def test_provenance_contains_active_physical_choices(self):
        result = self._sample()
        provenance = result.metadata["provenance"]
        for key in (
            "geometry",
            "wavelength_m",
            "visibility_km",
            "atmospheric_model",
            "turbulence_source",
            "scintillation_model",
            "aperture_averaging_status",
            "pointing_model",
            "jitter_convention",
            "aoa_model",
            "physical_domain_rule",
        ):
            self.assertIn(key, provenance)

    def test_relevant_provenance_inputs_change_record(self):
        first = self._sample().metadata["provenance"]
        second = self._sample(wavelength_m=1.50e-6).metadata["provenance"]
        self.assertNotEqual(first, second)

        third = self._sample(sigma_hap_ang_rad=1.0e-6).metadata["provenance"]
        self.assertNotEqual(first, third)

    def test_legacy_scalar_cn2_is_not_active_pointing_turbulence(self):
        first = self._sample(cn2_m_minus_two_thirds=1.0e-16)
        second = self._sample(cn2_m_minus_two_thirds=1.0e-14)
        self.assertEqual(first.metadata["beam_wander_status"], "LEGACY_NOT_USED")
        self.assertEqual(first.metadata["sigma2_turbulence_m2"], 0.0)
        self.assertEqual(second.metadata["sigma2_turbulence_m2"], 0.0)


if __name__ == "__main__":
    unittest.main()
