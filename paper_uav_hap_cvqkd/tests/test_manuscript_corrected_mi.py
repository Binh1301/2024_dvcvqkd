"""Cheap receiver/mixture/precision checks; no reference SKR or source solve."""
import math
import unittest

import numpy as np

from src.manuscript_literal_3moments import LiteralChannel, detector_noise
from src.manuscript_corrected_mi import (
    FadingMIError, _mixture_log_likelihood, _physical_fading_samples,
    _quadrature, discrete_fading_mutual_information, receiver_parameters,
)


class _PhysicalFixture:
    """Independent test adapter using protected analytical primitives only."""
    def __init__(self, *, outage=.02, rho=0):
        self.raw = LiteralChannel(.85, .91, 1.4, 1., .12, rho, outage, 1 - outage)
        self.active_normalization = self.raw.active_moment(0.)

    def log_physical_active_density_in_log_eta(self, y):
        c = self.raw.coefficients()
        from scipy.special import erfc
        return (math.log(c['chi2']) + c['log_C1'] - math.log(2.)
                - c['chi2'] * math.log(c['B']) + c['chi2'] * y
                + math.log(erfc(c['C3'] * (y - math.log(c['B']) + c['mu'])))
                - math.log(self.active_normalization))


class CorrectedMITests(unittest.TestCase):
    def test_receiver_snu_detector_and_outage_variance(self):
        eta = np.array([0., .3, 1.])
        alpha = np.array([-.2 + .1j, .2 - .1j])
        means, variance = receiver_parameters(alpha, eta)
        np.testing.assert_allclose(means, alpha[:, None] * np.sqrt(.7 * eta))
        np.testing.assert_allclose(variance, 1 + .0135 + .7 * eta * .0186 / 2)
        np.testing.assert_allclose(variance, .7 / 2 * (1 + detector_noise() + eta * .0186))
        self.assertEqual(variance[0], 1.0135)
        _, ideal = receiver_parameters(alpha, eta, R=1., xi_det=0., xi_ch=0.)
        np.testing.assert_array_equal(ideal, np.ones(3))

    def test_actual_joint_likelihood_includes_outage_atom(self):
        alpha = np.array([-.7 - .4j, .7 + .4j])
        eta, weights = np.array([0., .4, .9]), np.array([.2, .35, .45])
        y = np.array([.1 + .3j, -.9 + .2j])
        receiver = dict(R=.7, xi_det=.0135, xi_ch=.0186)
        actual = np.exp(_mixture_log_likelihood(y, alpha, eta, weights, **receiver))
        independent = np.zeros((len(y), len(alpha)))
        for k, a in enumerate(alpha):
            for t, weight in zip(eta, weights):
                variance = 1 + .0135 + .7 * t * .0186 / 2
                independent[:, k] += weight * np.exp(-np.abs(y - math.sqrt(.7 * t) * a)**2 / variance) / (math.pi * variance)
        np.testing.assert_allclose(actual, independent, atol=1e-14, rtol=1e-14)
        outage_term = .2 * np.exp(-np.abs(y)**2 / 1.0135) / (math.pi * 1.0135)
        self.assertTrue(np.all(actual > outage_term[:, None]))

    def test_node_mass_and_moments_agree_with_conditioned_law(self):
        fading = _PhysicalFixture()
        nodes, weights, diagnostic = _quadrature(fading, 128, 1e-6)
        self.assertTrue(diagnostic['validation_pass'], diagnostic)
        self.assertAlmostEqual(float(weights.sum()), 1., places=13)
        self.assertEqual(nodes[0], 0.)
        self.assertEqual(weights[0], .02)
        self.assertLessEqual(max(diagnostic[k] for k in ('mass_error', 'mean_eta_error', 'mean_sqrt_eta_error')), 1e-6)

    def test_exact_physical_sampler_is_bounded_and_normalized(self):
        fading = _PhysicalFixture(outage=.2)
        eta, diagnostic = _physical_fading_samples(fading, 2048, np.random.default_rng(246))
        self.assertTrue(np.all((eta >= 0) & (eta <= 1)))
        self.assertEqual(diagnostic['active_samples'] + diagnostic['outage_samples'], 2048)
        self.assertLess(diagnostic['rejection_draws'], diagnostic['rejection_budget'] + 1)
        self.assertAlmostEqual(np.count_nonzero(eta == 0) / 2048, .2, delta=.025)
        target = fading.raw.P1 * fading.raw.active_moment(1.) / fading.active_normalization
        self.assertAlmostEqual(float(eta.mean()), target, delta=.025)

    def test_256_symbol_all_outage_mi_is_zero(self):
        levels = np.arange(16) - 7.5
        alpha = .001 * (levels[:, None] + 1j * levels[None, :]).reshape(-1)
        p = np.full(256, 1 / 256)
        result = discrete_fading_mutual_information(p, alpha, _PhysicalFixture(outage=1.),
                  samples=16, quadrature_order=8, max_quadrature_order=16)
        self.assertEqual(result['I_AB'], 0.)
        self.assertEqual(result['stderr'], 0.)
        self.assertTrue(result['MI_valid'])
        self.assertEqual(result['status'], 'VALID_NUMERICAL_ESTIMATE')
        self.assertEqual(result['sampling_diagnostics']['outage_samples'], 16)
        self.assertFalse(result['detector_security_verified'])

    def test_256_symbol_active_mixture_uses_real_physical_wrapper(self):
        from src.manuscript_corrected_3moments import PhysicalFadingDistribution
        raw = _PhysicalFixture().raw
        fading = PhysicalFadingDistribution(raw)
        levels = np.arange(16) - 7.5
        alpha = .001 * (levels[:, None] + 1j * levels[None, :]).reshape(-1)
        result = discrete_fading_mutual_information(np.full(256, 1 / 256), alpha, fading,
                  samples=8, quadrature_order=32, max_quadrature_order=128)
        self.assertGreater(result['sampling_diagnostics']['active_samples'], 0)
        self.assertIsNotNone(result['I_AB'])
        self.assertAlmostEqual(result['symbol_entropy_bits'], 8.)
        self.assertFalse(result['total_error_certified'])

    def test_reproducible_estimator_context_and_precision_gate(self):
        p, alpha, fading = [.5, .5], [-.25, .25], _PhysicalFixture()
        settings = dict(samples=32, quadrature_order=32, max_quadrature_order=128,
                        sampling_stderr_tolerance=1e-10)
        first = discrete_fading_mutual_information(p, alpha, fading, **settings)
        repeat = discrete_fading_mutual_information(p, alpha, fading, **settings)
        self.assertEqual(first, repeat)
        self.assertIsNotNone(first['I_AB'])
        self.assertGreater(first['stderr'], 1e-10)
        self.assertFalse(first['MI_valid'])
        self.assertIn(first['status'], ('SAMPLING_PRECISION_NOT_MET', 'SAMPLING_BOUND_NOT_ESTABLISHED', 'QUADRATURE_NOT_CONVERGED'))
        changed = discrete_fading_mutual_information(p, alpha, fading, xi_det=.02, **settings)
        self.assertNotEqual(first['MI_context_hash'], changed['MI_context_hash'])
        self.assertFalse(first['total_error_certified'])

    def test_invalid_probability_and_workloads_fail_closed(self):
        for p in ([.4, .4], [-.1, 1.1]):
            with self.assertRaises(FadingMIError):
                discrete_fading_mutual_information(p, [-.2, .2], _PhysicalFixture(), samples=16)
        for settings in ({'samples': 5000}, {'R': 0}, {'xi_det': -.1}, {'quadrature_order': 256}):
            with self.assertRaises(FadingMIError):
                discrete_fading_mutual_information([.5, .5], [-.2, .2], _PhysicalFixture(), **settings)
        with self.assertRaisesRegex(FadingMIError, 'Unsupported nonzero'):
            discrete_fading_mutual_information([.5, .5], [-.2, .2], _PhysicalFixture(rho=.1), samples=16)


if __name__ == '__main__':
    unittest.main()
