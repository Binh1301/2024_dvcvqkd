import math
from pathlib import Path
import unittest

import numpy as np
import yaml

from src.channel.atmospheric_loss import atmospheric_transmittance
from src.channel.aoa import aoa_outage_probability
from src.channel.geometry import LinkGeometry
from src.channel.state_distribution import (
    FixedExcessNoise,
    sample_channel_state_distribution,
)
from src.channel.turbulence import UavMotion


ROOT = Path(__file__).resolve().parents[1]


class FinalHapUavBaselineTests(unittest.TestCase):
    @staticmethod
    def _configs():
        channel = yaml.safe_load(
            (ROOT / "configs" / "channel.yaml").read_text(encoding="utf-8")
        )
        default = yaml.safe_load(
            (ROOT / "configs" / "default.yaml").read_text(encoding="utf-8")
        )["channel"]
        return channel, default

    def test_canonical_inputs_and_derived_optics(self):
        channel, default = self._configs()
        self.assertAlmostEqual(channel["geometry"]["zenith_angle_rad"], math.pi / 6.0)
        self.assertEqual(channel["optics"]["visibility_km"], 20.0)
        self.assertEqual(channel["optics"]["aperture_radius_m"], 0.04)
        self.assertAlmostEqual(channel["optics"]["theta_div_rad"], 223.0e-6)
        self.assertEqual(channel["pointing"]["sigma_h_m"], 1.0)
        self.assertAlmostEqual(channel["pointing"]["theta_jt_rad"], 15.61e-6)
        self.assertAlmostEqual(channel["aoa"]["sigma_o_rad"], 1.5e-3)
        self.assertAlmostEqual(channel["aoa"]["theta_fov_rad"], 6.25e-3)
        self.assertAlmostEqual(
            channel["excess_noise_distribution"]["epsilon_ch_snu"], 0.0186
        )

        geometry = LinkGeometry(
            channel["geometry"]["h_hap_m"],
            channel["geometry"]["h_uav_m"],
            channel["geometry"]["zenith_angle_rad"],
        )
        self.assertAlmostEqual(geometry.link_length_m, 21939.31022920578)
        self.assertAlmostEqual(2.0 * channel["optics"]["aperture_radius_m"], 0.08)
        omega_0 = 2.0 * channel["optics"]["wavelength_m"] / (
            math.pi * channel["optics"]["theta_div_rad"]
        )
        self.assertAlmostEqual(omega_0, 0.004424935637532516)
        self.assertAlmostEqual(
            atmospheric_transmittance(
                geometry.link_length_m,
                channel["optics"]["visibility_km"],
                channel["optics"]["wavelength_m"],
            ),
            0.3276145376743964,
        )

        # The train/evaluation config resolves the same baseline values.
        self.assertEqual(default["visibility_km"], 20.0)
        self.assertEqual(default["aperture_radius_m"], 0.04)
        self.assertEqual(default["excess_noise_distribution"]["kind"], "fixed")

    def test_active_state_sampler_uses_fixed_excess_noise_and_direct_jitter(self):
        _, values = self._configs()
        geometry = LinkGeometry(
            values["h_hap_m"], values["h_uav_m"], values["zenith_angle_rad"]
        )
        sigma_h = values["pointing"]["sigma_h_m"]
        sigma_o = values["aoa"]["sigma_o_rad"]
        states = sample_channel_state_distribution(
            geometry=geometry,
            wavelength_m=values["wavelength_m"],
            visibility_km=values["visibility_km"],
            beam_waist_m=2.0 * values["wavelength_m"] / (
                math.pi * values["theta_div_rad"]
            ),
            aperture_radius_m=values["aperture_radius_m"],
            cn2_m_minus_two_thirds=values["turbulence_profile"][
                "cn2_ground_m_minus_two_thirds"
            ],
            excess_noise=FixedExcessNoise(0.0186),
            sample_count=128,
            seed=202612,
            uav_motion=UavMotion(
                sigma_x_m=sigma_h,
                sigma_y_m=sigma_h,
                sigma_z_m=0.0,
                sigma_theta_rad=sigma_o,
                sigma_phi_rad=sigma_o,
                sigma_psi_rad=0.0,
            ),
            aperture_averaging_model=values["scintillation"][
                "aperture_averaging_model"
            ],
            turbulence_profile_model=values["turbulence_profile"]["model"],
            wind_speed_m_per_s=values["turbulence_profile"]["wind_speed_m_per_s"],
            ground_cn2_m_minus_two_thirds=values["turbulence_profile"][
                "cn2_ground_m_minus_two_thirds"
            ],
            sigma_hap_ang_rad=values["pointing"]["theta_jt_rad"],
            hap_angular_jitter_convention=values["pointing"][
                "hap_angular_jitter_convention"
            ],
            aoa_model=values["aoa"]["model"],
            sigma_turb_AoA2=values["aoa"]["sigma_turb_AoA2_rad2"],
            turbulence_aoa_provenance=values["aoa"]["provenance"],
            theta_fov_rad=values["aoa"]["theta_fov_rad"],
        )
        np.testing.assert_allclose(states.excess_noise_snu, 0.0186)
        self.assertEqual(states.metadata["epsilon_model"], "fixed")
        self.assertLess(states.metadata["empirical_epsilon_base_variance_snu2"], 1.0e-30)
        sigma_o2 = sigma_o**2
        p_out = aoa_outage_probability(values["aoa"]["theta_fov_rad"], sigma_o2)
        self.assertAlmostEqual(states.metadata["p_out_analytic"], p_out)
        self.assertAlmostEqual(states.metadata["p_in"], 1.0 - states.metadata["p_out"])


if __name__ == "__main__":
    unittest.main()
