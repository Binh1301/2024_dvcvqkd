import math
import unittest
from dataclasses import replace

import torch

from src.channel.phase_noise import (
    optical_wavenumber_per_m,
    phase_distortion_variance,
    phase_excess_noise,
    phase_noise_coefficient,
    phase_noise_scenario,
    phase_noise_scenario_from_channel_config,
    phase_noise_scenario_sha256,
    total_excess_noise,
    validate_phase_noise_scenario_binding,
)


class PhaseNoiseTests(unittest.TestCase):
    def test_phase_distortion_variance_uses_the_exact_si_formula(self):
        cn_phi2 = 1.0e-20
        wavelength_m = 1.55e-6
        link_distance_m = 19_000.0
        expected = (
            2.46
            * cn_phi2
            * (2.0 * math.pi / wavelength_m) ** (7.0 / 6.0)
            * link_distance_m ** (11.0 / 6.0)
        )
        actual = phase_distortion_variance(cn_phi2, wavelength_m, link_distance_m)
        self.assertAlmostEqual(actual, expected, places=18)

    def test_coefficient_squares_the_stored_variance_once(self):
        tau_phi2 = 0.37
        self.assertAlmostEqual(
            phase_noise_coefficient(tau_phi2),
            tau_phi2 + 0.25 * tau_phi2**2,
            places=15,
        )

    def test_zero_turbulence_reference_has_no_phase_contribution(self):
        scenario = phase_noise_scenario(
            0.0,
            1.55e-6,
            19_000.0,
            allow_zero_turbulence_reference=True,
        )
        epsilon_base = torch.tensor([0.001, 0.02], dtype=torch.float64)
        va = torch.tensor([0.1, 2.0], dtype=torch.float64)
        torch.testing.assert_close(phase_excess_noise(va, scenario.c_phi), torch.zeros_like(va))
        torch.testing.assert_close(total_excess_noise(epsilon_base, va, scenario.c_phi), epsilon_base)

    def test_total_noise_keeps_the_va_autograd_path(self):
        c_phi = 0.03125
        va = torch.tensor([0.2, 1.4, 3.0], dtype=torch.float64, requires_grad=True)
        epsilon = total_excess_noise(torch.tensor([0.001, 0.002, 0.003]), va, c_phi)
        epsilon.sum().backward()
        torch.testing.assert_close(va.grad, torch.full_like(va, c_phi))

    def test_scenario_terms_are_constant_but_action_noise_varies(self):
        scenario = phase_noise_scenario(1e-20, 1.55e-6, 19_000.0)
        va = torch.tensor([0.1, 1.0, 3.0], dtype=torch.float64)
        epsilon_base = torch.tensor([0.001, 0.004, 0.009], dtype=torch.float64)
        xi = phase_excess_noise(va, scenario.c_phi)
        total = total_excess_noise(epsilon_base, va, scenario.c_phi)
        self.assertEqual(scenario.tau_phi2, phase_distortion_variance(1e-20, 1.55e-6, 19_000.0))
        self.assertEqual(scenario.c_phi, phase_noise_coefficient(scenario.tau_phi2))
        self.assertGreater(float(xi.max() - xi.min()), 0.0)
        torch.testing.assert_close(total, epsilon_base + scenario.c_phi * va)

    def test_wavelength_conversion_and_wavenumber_are_si(self):
        wavelength_nm = 1550.0
        wavelength_m = wavelength_nm * 1.0e-9
        self.assertAlmostEqual(wavelength_m, 1.55e-6, places=20)
        self.assertAlmostEqual(
            optical_wavenumber_per_m(wavelength_m),
            4.053667940115862e6,
            places=6,
        )

    def test_phase_parameter_is_independent_of_beam_wander_cn2(self):
        base = {
            "wavelength_m": 1.55e-6,
            "phase_noise": {
                "cn_phi2_m_minus_two_thirds": 1e-20,
                "units": "m^-2/3",
                "allow_zero_turbulence_reference": False,
            },
        }
        low_beam_wander = base | {"cn2_m_minus_two_thirds": 1e-18}
        high_beam_wander = base | {"cn2_m_minus_two_thirds": 1e-14}
        left = phase_noise_scenario_from_channel_config(
            low_beam_wander, link_distance_m=19_000.0
        )
        right = phase_noise_scenario_from_channel_config(
            high_beam_wander, link_distance_m=19_000.0
        )
        self.assertEqual(left.tau_phi2, right.tau_phi2)
        self.assertEqual(left.c_phi, right.c_phi)

    def test_phase_scenario_rejects_an_unresolved_or_ambiguous_input(self):
        with self.assertRaisesRegex(ValueError, "unresolved"):
            phase_noise_scenario_from_channel_config(
                {
                    "wavelength_m": 1.55e-6,
                    "phase_noise": {
                        "cn_phi2_m_minus_two_thirds": None,
                        "units": "m^-2/3",
                    },
                },
                link_distance_m=19_000.0,
            )

    def test_standalone_optics_schema_resolves_with_explicit_units(self):
        scenario = phase_noise_scenario_from_channel_config(
            {
                "geometry": {"h_hap_m": 20_000.0, "h_uav_m": 1_000.0},
                "optics": {
                    "wavelength_m": 1.55e-6,
                    "phase_noise": {
                        "cn_phi2_m_minus_two_thirds": 1e-20,
                        "units": "m^-2/3",
                        "allow_zero_turbulence_reference": False,
                    },
                },
            },
            link_distance_m=19_000.0,
        )
        self.assertEqual(scenario.wavelength_m, 1.55e-6)
        self.assertEqual(len(phase_noise_scenario_sha256(scenario)), 64)

    def test_phase_scenario_binding_rejects_geometry_or_derived_value_mismatch(self):
        scenario = phase_noise_scenario(1e-20, 1.55e-6, 19_000.0)
        with self.assertRaisesRegex(ValueError, "wavelength_m"):
            validate_phase_noise_scenario_binding(
                scenario, wavelength_m=1.54e-6, link_distance_m=19_000.0
            )
        with self.assertRaisesRegex(ValueError, "link_distance_m"):
            validate_phase_noise_scenario_binding(
                scenario, wavelength_m=1.55e-6, link_distance_m=18_999.0
            )
        tampered = replace(scenario, c_phi=scenario.c_phi * 1.01)
        with self.assertRaisesRegex(ValueError, "derived"):
            validate_phase_noise_scenario_binding(
                tampered, wavelength_m=1.55e-6, link_distance_m=19_000.0
            )
        with self.assertRaisesRegex(ValueError, "units"):
            phase_noise_scenario_from_channel_config(
                {
                    "wavelength_m": 1.55e-6,
                    "phase_noise": {
                        "cn_phi2_m_minus_two_thirds": 1e-20,
                        "units": "unspecified",
                    },
                },
                link_distance_m=19_000.0,
            )


if __name__ == "__main__":
    unittest.main()
