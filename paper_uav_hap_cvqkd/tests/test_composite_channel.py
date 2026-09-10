import math
import unittest
from unittest.mock import patch

import numpy as np

from src.channel.aoa import (
    aoa_outage_probability,
    aoa_variance_rad2,
    sample_aoa_gate,
)
from src.channel.fso_channel import (
    compose_raw_transmittance,
    physicalize_raw_transmittance,
    sample_fso_channel,
)
from src.channel.diagnostics import composite_transmittance_diagnostics
from src.channel.scintillation import (
    UnsupportedApertureAveragingError,
    normalized_lognormal_samples,
    resolve_scintillation_variance,
    rytov_variance_from_profile,
)
from src.channel.geometry import LinkGeometry
from src.channel.turbulence import UavMotion


class CompositeChannelTests(unittest.TestCase):
    def _kwargs(self):
        return {
            "geometry": LinkGeometry(20_000.0, 1_000.0, 0.0),
            "wavelength_m": 1.55e-6,
            "visibility_km": 200.0,
            "beam_waist_m": 0.0157,
            "aperture_radius_m": 0.075,
            "cn2_m_minus_two_thirds": 1.0e-16,
            "sample_count": 4096,
            "rng": np.random.default_rng(20260910),
            "scintillation_log_variance": 0.0,
            "aoa_model": "disabled",
        }

    def test_log_normal_scintillation_is_positive_and_unit_mean(self):
        values = normalized_lognormal_samples(
            0.25, np.random.default_rng(1001), 100_000
        )
        self.assertTrue(np.all(values > 0.0))
        self.assertAlmostEqual(float(values.mean()), 1.0, delta=0.01)

    def test_rytov_profile_integral_uses_si_wavelength_and_path_weight(self):
        heights = np.array([1_000.0, 2_000.0, 3_000.0])
        profile = np.array([1.0e-16, 2.0e-16, 3.0e-16])
        observed = rytov_variance_from_profile(
            heights,
            profile,
            wavelength_m=1.55e-6,
            link_length_m=19_000.0,
            h_uav_m=1_000.0,
            zenith_angle_rad=0.0,
        )
        expected = 2.25 * (2.0 * math.pi / 1.55e-6) ** (7.0 / 6.0) * np.trapezoid(
            profile * (heights - 1_000.0) ** (5.0 / 6.0), heights
        )
        self.assertAlmostEqual(observed, float(expected), places=12)

    def test_aperture_averaging_mapping_fails_closed_when_unresolved(self):
        with self.assertRaises(UnsupportedApertureAveragingError):
            resolve_scintillation_variance(
                sigma_R0_squared=0.5,
                aperture_averaging_model=None,
                v_sc_override=None,
            )

    def test_active_sampler_does_not_use_legacy_beam_wander(self):
        with patch(
            "src.channel.fso_channel.turbulence_beam_wander_variance_m2",
            side_effect=AssertionError("legacy beam wander entered active path"),
            create=True,
        ):
            result = sample_fso_channel(**self._kwargs())
        self.assertEqual(result.metadata["beam_wander_status"], "LEGACY_NOT_USED")

    def test_pointing_uses_rician_displacement_and_excludes_sigma_z(self):
        first_kwargs = self._kwargs()
        first_kwargs["uav_motion"] = UavMotion(sigma_z_m=0.0)
        first = sample_fso_channel(**first_kwargs)
        second_kwargs = self._kwargs()
        second_kwargs["uav_motion"] = UavMotion(sigma_z_m=100.0)
        second = sample_fso_channel(**second_kwargs)
        np.testing.assert_array_equal(first.radial_displacement_m, second.radial_displacement_m)
        self.assertEqual(first.metadata["displacement_law"], "Rician")
        self.assertEqual(first.metadata["sigma_z_included"], False)

    def test_generalized_pointing_support_and_boresight(self):
        kwargs = self._kwargs()
        kwargs["boresight_x_m"] = 0.3
        result = sample_fso_channel(**kwargs)
        self.assertGreater(result.radial_displacement_m.mean(), result.sigma_axis_m)
        self.assertTrue(np.all(result.pointing.t0_power >= result.transmittance / result.atmospheric_transmittance))
        self.assertEqual(result.metadata["pointing_model"], "generalized_gaussian_beam")

    def test_aoa_variance_excludes_yaw_and_outage_matches_rayleigh(self):
        motion = UavMotion(
            sigma_theta_rad=0.2,
            sigma_phi_rad=0.3,
            sigma_psi_rad=100.0,
        )
        observed = aoa_variance_rad2(
            motion,
            sigma_turb_AoA2=0.4,
            model="external_validated",
            provenance="test fixture",
        )
        self.assertAlmostEqual(observed, (0.2**2 + 0.3**2) / 2.0 + 0.4)
        expected_outage = math.exp(-(0.1**2) / (2.0 * observed))
        self.assertAlmostEqual(aoa_outage_probability(0.1, observed), expected_outage)
        gates = sample_aoa_gate(
            sample_count=4096,
            rng=np.random.default_rng(7),
            sigma_o2=observed,
            theta_fov_rad=0.1,
        )
        self.assertIn(0, gates)
        self.assertIn(1, gates)

    def test_nonzero_unvalidated_turbulence_aoa_fails_closed(self):
        with self.assertRaises(ValueError):
            aoa_variance_rad2(UavMotion(), sigma_turb_AoA2=0.1, model="unsupported")

    def test_aoa_outage_is_zero_transmittance_without_a_floor(self):
        kwargs = self._kwargs()
        kwargs.update(
            {
                "aoa_model": "external_validated",
                "sigma_turb_AoA2": 0.0,
                "turbulence_aoa_provenance": "explicit test fixture",
                "theta_fov_rad": 0.0,
            }
        )
        result = sample_fso_channel(**kwargs)
        self.assertTrue(np.all(result.aoa_gate == 0))
        self.assertTrue(np.all(result.transmittance == 0.0))
        self.assertEqual(result.metadata["p_out_analytic"], 1.0)

    def test_active_rejection_preserves_the_aoa_outage_atom(self):
        kwargs = self._kwargs()
        sigma_o2 = aoa_variance_rad2(UavMotion())
        kwargs.update(
            {
                "sample_count": 4,
                "aoa_model": "external_validated",
                "sigma_turb_AoA2": 0.0,
                "turbulence_aoa_provenance": "explicit test fixture",
                "theta_fov_rad": math.sqrt(2.0 * sigma_o2 * math.log(2.0)),
            }
        )

        def fake_scintillation(_v_sc, _rng, count):
            values = np.ones(count, dtype=np.float64)
            values[0] = 1.0e6
            return values

        with patch(
            "src.channel.fso_channel.sample_aoa_gate",
            return_value=np.array([0, 1, 0, 1], dtype=np.int8),
        ), patch(
            "src.channel.fso_channel.normalized_lognormal_samples",
            side_effect=fake_scintillation,
        ):
            result = sample_fso_channel(**kwargs)

        self.assertAlmostEqual(result.metadata["p_out"], 0.5)
        self.assertAlmostEqual(result.metadata["p_in"], 0.5)
        self.assertAlmostEqual(result.metadata["p_out_analytic"], 0.5)
        self.assertGreater(result.metadata["p_above_one"], 0.0)
        self.assertTrue(np.all(result.transmittance[result.aoa_gate == 0] == 0.0))

    def test_composition_and_physical_domain_have_no_clipping_or_floor(self):
        raw = compose_raw_transmittance(
            eta_atm=0.8,
            scintillation=np.array([1.0, 2.0, 0.5]),
            pointing=np.array([0.5, 0.5, 0.5]),
            aoa_gate=np.array([1, 1, 0]),
        )
        np.testing.assert_allclose(raw, [0.4, 0.8, 0.0])
        np.testing.assert_allclose(
            physicalize_raw_transmittance(raw), [0.4, 0.8, 0.0]
        )
        with self.assertRaises(ValueError):
            physicalize_raw_transmittance(np.array([0.2, 1.0001]))
        self.assertEqual(float(physicalize_raw_transmittance(np.array([0.0]))[0]), 0.0)

        diagnostics = composite_transmittance_diagnostics(
            [0.4, 1.2, 0.0], [0.4, 0.8, 0.0], aoa_gate=[1, 1, 0]
        )
        self.assertAlmostEqual(diagnostics["p_above_one"], 1.0 / 3.0)
        self.assertAlmostEqual(diagnostics["p_out"], 1.0 / 3.0)
        self.assertAlmostEqual(
            diagnostics["mean_difference_T"],
            (0.4 + 1.2 + 0.0) / 3.0 - (0.4 + 0.8 + 0.0) / 3.0,
        )
        self.assertGreater(float(diagnostics["delta_T"]), 0.0)

    def test_sampled_transmittance_is_physical_and_has_no_unit_atom(self):
        result = sample_fso_channel(**self._kwargs())
        self.assertTrue(np.all(result.transmittance >= 0.0))
        self.assertTrue(np.all(result.transmittance <= 1.0))
        self.assertFalse(np.any(result.transmittance == 1.0))
        self.assertEqual(result.metadata["physical_domain_rule"], "truncated_renormalized_active_law")
        self.assertIn("mean_difference_T", result.metadata)
        self.assertAlmostEqual(result.metadata["delta_T"], 0.0)
        self.assertIn("proposal_delta_T", result.metadata)


if __name__ == "__main__":
    unittest.main()
