"""Component/gate checks only; no HAP-UAV candidate search or source generation."""
import copy
import unittest
from unittest.mock import patch

import mpmath as mp
import numpy as np
from scipy.special import xlogy

import model as m


class Eq14Tests(unittest.TestCase):
    def test_exact_expression_and_precision(self):
        for digits in (80, 110):
            with mp.workdps(digits):
                t, xi, c, w = map(mp.mpf, (".25", ".125", ".75", ".0625"))
                self.assertEqual(m.correlation_eq14(t, xi, c, w),
                                 2*mp.sqrt(t)*c-mp.sqrt(2*t*xi*w))
        a = m.components(2, .2, .02, .7, .01, digits=80)
        b = m.components(2, .2, .02, .7, .01, digits=110)
        with mp.workdps(120):
            for k in a["decimal"]:
                self.assertLess(abs(mp.mpf(a["decimal"][k])-mp.mpf(b["decimal"][k])), mp.mpf("1e-68"))

    def test_zero_noise_and_zero_w(self):
        with mp.workdps(80):
            self.assertEqual(m.correlation_eq14(".25", 0, ".75", 1), mp.mpf(".75"))
            self.assertEqual(m.correlation_eq14(".25", 20, ".75", 0), mp.mpf(".75"))

    def test_subtraction_and_negative_Z_not_clamped(self):
        with mp.workdps(110):
            c = mp.mpf(".125") + mp.mpf("1e-60")
            z = m.correlation_eq14(".25", ".125", c, ".25")
            self.assertLess(abs(z-mp.mpf("1e-60")), mp.mpf("1e-109"))
        self.assertLess(m.components(2, .2, .1, 0, 1)["Z_manuscript_eq14"], 0)

    def test_invalid_inputs(self):
        for t, xi, c, w in [(1.1, 0, 1, 0), (.2, -.1, 1, 0), (.2, .1, -1, 0),
                            (.2, .1, 1, -1), (float("nan"), 0, 1, 0), (.2, 0, float("inf"), 0)]:
            with self.subTest(values=(t, xi, c, w)), self.assertRaises(ValueError):
                m.correlation_eq14(t, xi, c, w)

    def test_vacuum_entropy_boundary(self):
        x = m.components(0, 1, 0, 0, 0)
        self.assertEqual([x[k] for k in ["nu_1", "nu_2", "nu_3"]], [1., 1., 1.])
        self.assertEqual(x["chi_BE"], 0.)
        self.assertEqual(m.entropy_g(0), 0)
        with self.assertRaises(ValueError):
            m.entropy_g(-1e-30)

    def test_thermal_product_exact_limit(self):
        x = m.components(1, .25, 0, 0, 0)
        self.assertEqual([x[k] for k in ["nu_1", "nu_2", "nu_3"]], [2., 1.25, 2.])
        self.assertAlmostEqual(x["chi_BE"], float(m.entropy_g(mp.mpf(".125"))), places=14)

    def test_covariance_and_homodyne_schur_spectrum(self):
        for args in [(2, .2, .02, .7, .01), (1, .5, .01, .86602539, 0),
                     (1, 1e-6, .005, .5, .001)]:
            x = m.components(*args)
            a, b, z = x["V"], x["W"], x["Z_manuscript_eq14"]
            gamma = np.array([[a, 0, z, 0], [0, a, 0, -z], [z, 0, b, 0], [0, -z, 0, b]])
            omega = np.kron(np.eye(2), [[0., 1.], [-1., 0.]])
            self.assertGreaterEqual(np.linalg.eigvalsh(gamma+1j*omega).min(), -1e-11)
            spectrum = np.sort(np.abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
            np.testing.assert_allclose(spectrum, sorted([x["nu_1"], x["nu_2"]]), rtol=0, atol=1e-10)
            conditional = gamma[:2, :2] - gamma[:2, 2:] @ np.diag([1/b, 0]) @ gamma[2:, :2]
            self.assertAlmostEqual(np.sqrt(np.linalg.det(conditional)), x["nu_3"], places=12)
            n = (np.array([x["nu_1"], x["nu_2"], x["nu_3"]])-1)/2
            g = (xlogy(n+1, n+1)-xlogy(n, n))/np.log(2)
            self.assertAlmostEqual(g[0]+g[1]-g[2], x["chi_BE"], places=12)

    def test_nonphysical_covariance_rejected(self):
        for c in [100, 2]:
            with self.assertRaises(ValueError):
                m.components(1, 1, 0, c, 0)
        with self.assertRaises(ValueError):
            m.components(1, 0, .1, .5, .1)

    def test_no_full_Z_calls(self):
        helper = m.helpers()
        with patch.object(helper.legacy, "full_holevo", side_effect=AssertionError("full-Z forbidden")), \
             patch.object(helper.legacy, "spectrum", side_effect=AssertionError("cap branch forbidden")):
            self.assertTrue(np.isfinite(m.components(2, .2, .02, .7, .01)["chi_BE"]))

    def test_real_discrete_MI(self):
        raw = np.arange(16)-7.5
        alpha = (raw[:, None]+1j*raw[None, :]).ravel()/np.sqrt(85)
        p = np.full(256, 1/256)
        a = m.helpers()
        self.assertLess(abs(a.homodyne_mi(p, alpha, 0., 1.01)), 2e-12)
        values = [a.homodyne_mi(p, alpha, .2, 1.01, order=n) for n in [64, 128]]
        independent, error = a.independent_mi(p, alpha, .2, 1.01)
        self.assertLess(abs(values[0]-values[1]), 2e-10)
        self.assertLess(abs(values[1]-independent), 2e-10)
        self.assertLess(error, 2e-10)
        self.assertLess(abs(values[1]-a.homodyne_mi(p, alpha, .2, 1.01, grouped=False, order=128)), 2e-12)
        self.assertLess(abs(values[1]-a.homodyne_mi(p, alpha, .2, 1.01, axis="P", order=128)), 2e-12)
        from scipy.integrate import quad
        for mean in 2*np.sqrt(.2)*np.unique(alpha.real):
            mass, err = quad(lambda y: a.conditional_pdf(y, mean, 1.01), -np.inf, np.inf)
            self.assertLess(abs(mass-1), 2e-10)

    def test_model_gate_precedes_all_rate_calculations(self):
        protocol = m.read(m.OUT/"protocol.json")
        for ctx in [{}, dict(channel_law=m.LAW, law_mathematically_valid=False,
                              moments=dict(M0=1-1e-12, normalized_within_tolerance=True))]:
            with patch.object(m, "components", side_effect=AssertionError("SKR component called")), \
                 self.assertRaises(m.ModelBlocked):
                m.evaluate({}, ctx, protocol)

    def test_unresolved_VA_mapping_rejected(self):
        with self.assertRaisesRegex(m.ModelBlocked, "mapping"):
            m.evaluate({}, dict(channel_law=m.LAW, law_mathematically_valid=True),
                       m.read(m.OUT/"protocol.json"))

    def test_old_policy_and_changed_physics_rejected(self):
        p = m.read(m.OUT/"protocol.json")
        for field, value in [("correlation_policy", "full_Z"), ("xi_det", .001)]:
            bad = copy.deepcopy(p); bad[field] = value
            with self.assertRaises(ValueError): m.validate_protocol(bad)
        bad = copy.deepcopy(p); bad["physical"]["Dr_m"] = .55
        with self.assertRaises(ValueError): m.validate_protocol(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
