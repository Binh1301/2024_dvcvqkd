import math
import unittest

from scripts.calculate_channel_pdf_and_moments import (
    closed_form_channel_moments,
    derive_physical_inputs,
)


class ClosedFormChannelMomentTests(unittest.TestCase):
    def _physical(self, degrees: float = 30.0):
        return derive_physical_inputs(
            0.92,
            zenith_angle_rad_override=math.radians(degrees),
        )

    def test_baseline_values_and_teff_identity(self):
        values = closed_form_channel_moments(
            self._physical(), epsilon_total=0.0186
        )
        self.assertAlmostEqual(values["mean_T_raw"], 2.7796727740239506e-4, places=15)
        self.assertAlmostEqual(values["mean_sqrt_T_raw"], 0.01596454918487076, places=14)
        self.assertAlmostEqual(values["T_eff"], 2.548668306761576e-4, places=15)
        self.assertEqual(values["T_eff"], values["mean_sqrt_T_raw"] ** 2)

    def test_beam_waist_override_preserves_default_and_updates_divergence(self):
        default = self._physical()
        overridden = derive_physical_inputs(
            0.92,
            zenith_angle_rad_override=math.radians(30.0),
            beam_waist_m_override=0.010,
        )
        self.assertAlmostEqual(default["beam_waist_m"], 0.004424935637532516)
        self.assertAlmostEqual(
            overridden["theta_div_rad"],
            2.0 * overridden["wavelength_m"] / (math.pi * 0.010),
        )
        self.assertNotEqual(
            overridden["pointing"]["omega_L_m"],
            default["pointing"]["omega_L_m"],
        )

    def test_zero_boresight_reduces_exactly_to_zero_rho_forms(self):
        physical = self._physical()
        values = closed_form_channel_moments(physical, epsilon_total=0.2, rho_m=0.0)
        chi2 = values["chi"] ** 2
        mean_t = values["p_in"] * values["A0"] * values["eta_atm"] * chi2 / (chi2 + 1.0)
        mean_sqrt = (
            values["p_in"]
            * math.sqrt(values["A0"] * values["eta_atm"])
            * chi2 / (chi2 + 0.5)
            * math.exp(-values["sigma_X2"] / 2.0)
        )
        self.assertEqual(values["mean_T_raw"], mean_t)
        self.assertEqual(values["mean_sqrt_T_raw"], mean_sqrt)

    def test_general_finite_boresight_terms(self):
        physical = self._physical()
        rho = 0.35
        values = closed_form_channel_moments(physical, epsilon_total=0.2, rho_m=rho)
        chi2 = values["chi"] ** 2
        chi4 = chi2**2
        mean_t = (
            values["p_in"] * values["A0"] * values["eta_atm"]
            * chi2 / (chi2 + 1.0)
            * math.exp(rho**2 * (1.0 - chi2) / (2.0 * values["sigma_jt"]**2 * chi4))
        )
        mean_sqrt = (
            values["p_in"] * math.sqrt(values["A0"] * values["eta_atm"])
            * chi2 / (chi2 + 0.5)
            * math.exp(
                -values["sigma_X2"] / 2.0
                + rho**2 * (1.0 - 2.0 * chi2)
                / (8.0 * values["sigma_jt"]**2 * chi4)
            )
        )
        self.assertAlmostEqual(values["mean_T_raw"], mean_t, places=15)
        self.assertAlmostEqual(values["mean_sqrt_T_raw"], mean_sqrt, places=15)

    def test_t_epsilon_moment_is_linear(self):
        values = closed_form_channel_moments(self._physical(), epsilon_total=0.37)
        self.assertEqual(values["mean_T_epsilon"], 0.37 * values["mean_T_raw"])

    def test_distance_changes_physical_moments(self):
        vertical = self._physical(0.0)
        oblique = self._physical(50.0)
        vertical_values = closed_form_channel_moments(vertical, epsilon_total=0.0186)
        oblique_values = closed_form_channel_moments(oblique, epsilon_total=0.0186)
        self.assertNotEqual(vertical["link_length_m"], oblique["link_length_m"])
        self.assertNotEqual(vertical_values["T_eff"], oblique_values["T_eff"])

    def test_result_is_deterministic(self):
        physical = self._physical()
        first = closed_form_channel_moments(physical, epsilon_total=0.0186)
        second = closed_form_channel_moments(physical, epsilon_total=0.0186)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
