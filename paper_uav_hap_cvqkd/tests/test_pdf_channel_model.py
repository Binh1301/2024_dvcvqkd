import math
import unittest

import numpy as np
from scipy.integrate import quad

from src.channel.diagnostics import (
    active_transmittance_pdf_eq49,
    active_transmittance_pdf_eq50,
)
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.pointing_error import (
    pointing_parameters,
    pointing_pdf,
    pointing_power_transmittance,
    rician_pdf,
)
from src.channel.scintillation import (
    hufnagel_valley_beam_spreading,
    hufnagel_valley_scintillation,
    lognormal_pdf,
)
from src.channel.turbulence import UavMotion


class PdfChannelModelTests(unittest.TestCase):
    def _parameters(self):
        geometry = LinkGeometry(20_000.0, 1_000.0, 0.0)
        scintillation = hufnagel_valley_scintillation(
            1_000.0, 20_000.0, 1.55e-6, 0.0, 21.0, 5.0e-14, 0.08
        )
        spreading = hufnagel_valley_beam_spreading(
            1_000.0, 20_000.0, 1.55e-6, 0.0, 21.0, 5.0e-14, 223.0e-6
        )
        pointing = pointing_parameters(
            0.04,
            4.425e-3,
            1.55e-6,
            geometry.link_length_m,
            theta_div_rad=223.0e-6,
            beam_spreading_factor=spreading["G_d"],
        )
        return geometry, scintillation, pointing

    def test_table_i_derived_quantities(self):
        _, scintillation, pointing = self._parameters()
        self.assertAlmostEqual(scintillation["sigma_R0_squared"], 0.04145444025152738)
        self.assertAlmostEqual(scintillation["A_ap"], 0.6964115179570911)
        self.assertAlmostEqual(scintillation["v_sc"], 0.02886934966162772)
        self.assertAlmostEqual(pointing.omega_0_m, 0.004424935637532516)
        self.assertAlmostEqual(pointing.beam_radius_receiver_m, 2.118504621202276)
        self.assertAlmostEqual(pointing.g_d, 0.00024089665983497693)
        self.assertAlmostEqual(pointing.t0_power, 0.0007127365410377602)
        self.assertAlmostEqual(pointing.omega_L_eq_m, 2.1191553233134117)

    def test_analytical_pdf_normalization_and_eq49_eq50(self):
        _, scintillation, pointing = self._parameters()
        v_sc = scintillation["v_sc"]
        sigma_jt = math.sqrt(1.0**2 + (19_000.0 * 15.61e-6) ** 2)
        hsc_mass = quad(
            lambda h: float(lognormal_pdf(np.asarray([h]), v_sc)[0]),
            0.0,
            math.inf,
        )[0]
        hp_mass = quad(
            lambda u: float(pointing_pdf(np.asarray([u]), pointing, sigma_jt)[0]),
            0.0,
            pointing.t0_power,
        )[0]
        x_mass = quad(
            lambda log_t: active_transmittance_pdf_eq50(
                math.exp(log_t),
                eta_atm=0.9316271221,
                v_sc=v_sc,
                pointing=pointing,
                sigma_jt_m=sigma_jt,
            )
            * math.exp(log_t),
            -40.0,
            0.0,
            limit=200,
        )[0]
        self.assertAlmostEqual(hsc_mass, 1.0, places=9)
        self.assertAlmostEqual(hp_mass, 1.0, places=9)
        self.assertAlmostEqual(x_mass, 1.0, places=4)
        for t in (1.0e-4, 3.0e-4, 6.0e-4):
            eq49 = active_transmittance_pdf_eq49(
                t,
                eta_atm=0.9316271221,
                v_sc=v_sc,
                pointing=pointing,
                sigma_jt_m=sigma_jt,
            )
            eq50 = active_transmittance_pdf_eq50(
                t,
                eta_atm=0.9316271221,
                v_sc=v_sc,
                pointing=pointing,
                sigma_jt_m=sigma_jt,
            )
            self.assertAlmostEqual(eq49, eq50, places=6)

    def test_exact_sampler_baseline_and_outage(self):
        geometry, scintillation, pointing = self._parameters()
        result = sample_fso_channel(
            geometry=geometry,
            wavelength_m=1.55e-6,
            visibility_km=200.0,
            beam_waist_m=4.425e-3,
            aperture_radius_m=0.04,
            cn2_m_minus_two_thirds=1.0e-16,
            sample_count=10_000,
            rng=np.random.default_rng(42),
            turbulence_profile_model="hufnagel_valley",
            wind_speed_m_per_s=21.0,
            ground_cn2_m_minus_two_thirds=5.0e-14,
            aperture_averaging_model="hufnagel_valley_finite_aperture",
            eta_atm=0.9316271221,
            theta_div_rad=223.0e-6,
            sigma_h_m=1.0,
            sigma_hap_ang_rad=15.61e-6,
            sigma_o_rad=1.5e-3,
            aoa_model="external_validated",
            sigma_turb_AoA2=0.0,
            turbulence_aoa_provenance="PDF Table I zero turbulence AoA fixture",
            theta_fov_rad=6.25e-3,
        )
        self.assertAlmostEqual(result.sigma_axis_m, 1.0430559084248552)
        self.assertAlmostEqual(result.pointing.t0_power, pointing.t0_power)
        self.assertAlmostEqual(
            result.metadata["provenance"]["scintillation_model"]["v_sc"],
            scintillation["v_sc"],
        )
        self.assertTrue(np.all(np.isin(result.aoa_gate, (0, 1))))
        self.assertTrue(np.all(result.transmittance[result.aoa_gate == 0] == 0.0))
        self.assertTrue(np.all(result.transmittance <= 1.0))
        expected_raw = 0.9316271221 * result.scintillation_factor * pointing_power_transmittance(
            result.radial_displacement_m, result.pointing
        ) * result.aoa_gate
        np.testing.assert_allclose(result.raw_transmittance, expected_raw)
        self.assertEqual(result.metadata["pointing_model"], "pdf_gaussian_beam_eq27_39")
        self.assertAlmostEqual(result.metadata["p_out_analytic"], math.exp(-(6.25e-3) ** 2 / (2.0 * (1.5e-3) ** 2)))

    def test_rician_pdf_rayleigh_limit(self):
        values = np.linspace(0.0, 8.0, 1000)
        observed = rician_pdf(values, 1.0430559084248552, 0.0)
        expected = values / (1.0430559084248552**2) * np.exp(
            -values**2 / (2.0 * 1.0430559084248552**2)
        )
        np.testing.assert_allclose(observed, expected)


if __name__ == "__main__":
    unittest.main()
