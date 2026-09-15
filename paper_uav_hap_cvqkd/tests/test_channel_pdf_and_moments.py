import unittest

import numpy as np
from scipy.integrate import quad

from scripts.calculate_channel_pdf_and_moments import (
    EXPECTED_NEW_V_SC,
    _pointing_pdf_normalization,
    _product_kernel,
    analyze_product,
    derive_physical_inputs,
    hsc_statistics,
    pointing_pdf,
    product_pdf,
)


class ChannelPdfAndMomentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physical = derive_physical_inputs()
        cls.analysis = analyze_product(EXPECTED_NEW_V_SC, cls.physical)

    def test_scintillation_and_pointing_normalization(self):
        hsc = hsc_statistics(EXPECTED_NEW_V_SC)
        self.assertAlmostEqual(hsc["pdf_normalization"], 1.0, places=10)
        self.assertAlmostEqual(hsc["mean_integral"], 1.0, places=10)
        self.assertAlmostEqual(_pointing_pdf_normalization(self.physical), 1.0, places=10)

    def test_product_pdf_keeps_transformation_jacobian(self):
        t = 0.02
        physical = self.physical
        kernel = _product_kernel(EXPECTED_NEW_V_SC, physical)
        eta_atm = physical["eta_atm"]
        eta_p0 = physical["pointing"]["eta_p0"]
        normalizer = np.sqrt(2.0 * np.pi * EXPECTED_NEW_V_SC)

        def transformed_integrand(s):
            u = eta_p0 * np.exp(-s)
            log_h = np.log(t / (eta_atm * u))
            hsc_value = np.exp(
                -log_h
                - np.log(normalizer)
                - (log_h + EXPECTED_NEW_V_SC / 2.0) ** 2
                / (2.0 * EXPECTED_NEW_V_SC)
            )
            hp_value = pointing_pdf(np.asarray([u]), physical)[0]
            return hsc_value / (eta_atm * u) * hp_value * u

        direct = quad(transformed_integrand, 0.0, np.inf, epsabs=1e-10, epsrel=1e-8)[0]
        mixture = product_pdf(np.asarray([t]), kernel)[0]
        self.assertAlmostEqual(float(mixture), float(direct), places=7)

    def test_mixed_pdf_normalization_and_reference_moments(self):
        quadrature = self.analysis["quadrature"]
        moments = self.analysis["moments"]
        self.assertAlmostEqual(quadrature["f_X_normalization"], 1.0, places=8)
        self.assertAlmostEqual(quadrature["active_pdf_normalization"], 1.0, places=8)
        self.assertAlmostEqual(moments["active_mean_eta"], 0.02562693657, places=9)
        self.assertAlmostEqual(moments["mean_eta"], 0.01922020243, places=9)
        self.assertAlmostEqual(moments["mean_sqrt_eta"], 0.1196294585, places=9)
        self.assertLessEqual(moments["mean_sqrt_eta"], moments["sqrt_mean_eta"])
        self.assertAlmostEqual(self.physical["p_out"] + self.physical["p_in"], 1.0)


if __name__ == "__main__":
    unittest.main()
