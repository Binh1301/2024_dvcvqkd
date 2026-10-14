"""Ideal-receiver checks for the single authorized existing-source reference.

No AP, source evaluation, reference MI, AO, or distance/candidate sweep is
performed here. Historical/literal regression and full file preservation
remain in the existing validation suite and the single-point receipt.
"""
import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from scipy.integrate import quad

from src.manuscript_literal_3moments import LiteralChannel, detector_noise, entropy
from src.manuscript_corrected_3moments import (
    PhysicalFadingDistribution, admissible_correlation_interval,
    corrected_covariance, corrected_z_star, effective_fading_channel,
    holevo_interval_maximizer,
)
from src.manuscript_corrected_mi import _mixture_log_likelihood, receiver_parameters


ROOT = Path(__file__).resolve().parents[1]
DISTANCE_KM = 21.9393102292
VA = 5.5
XI_CH = .0186


def independent_holevo(a, b, z):
    """Independent direct invariant/eigenvalue and elementary entropy route."""
    delta = a * a + b * b - 2 * z * z
    determinant = (a * b - z * z) ** 2
    discriminant = delta * delta - 4 * determinant
    if discriminant < 0:
        raise AssertionError('Independent discriminant is negative')
    root = math.sqrt(discriminant)
    eigenvalues = (math.sqrt((delta + root) / 2), math.sqrt((delta - root) / 2),
                   a - z * z / (b + 1))
    if min(eigenvalues) < 1:
        raise AssertionError('Independent covariance is nonphysical')

    def g(n):
        return 0. if n == 0 else (n + 1) * math.log2(n + 1) - n * math.log2(n)

    value = g((eigenvalues[0] - 1) / 2) + g((eigenvalues[1] - 1) / 2) - g((eigenvalues[2] - 1) / 2)
    return value, eigenvalues


class ManuscriptCorrectedIdealReferenceTests(unittest.TestCase):
    metrics = {}

    @classmethod
    def setUpClass(cls):
        from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config

        checkpoint = json.loads((ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization/'
                                 'grid_timeout_retry_1/objective_checkpoint.json').read_text(encoding='utf-8'))
        entry = next(row for row in checkpoint if row['L_km'] == DISTANCE_KM)
        reference = next(row for row in entry['rows'] if row['nu_raw'] == .165 and row['V_A'] == VA)
        cls.source_path = ROOT / reference['source_path']
        cls.source_sha256 = hashlib.sha256(cls.source_path.read_bytes()).hexdigest()
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            cls.candidate = verified_candidate(cls.source_path, unconstrained_config())
        physical = derive_physical_inputs(.92,
            zenith_angle_rad_override=math.acos(19000 / (DISTANCE_KM * 1000)),
            aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
        cls.fading = PhysicalFadingDistribution(LiteralChannel.from_physical(physical))
        cls.moments = cls.fading.moments(R=1., xi_det=0., xi_ch=XI_CH)
        cls.effective = effective_fading_channel(cls.moments, VA)
        cls.z = corrected_z_star(cls.effective, cls.candidate['C'], cls.candidate['w'])

    def test_ideal_third_moment_and_normalized_law_including_outage(self):
        self.assertEqual(detector_noise(1., 0.), 1.)
        self.assertEqual(self.moments['chi_het'], 1.)
        self.assertEqual(self.moments['mean_eta_xi_total'], 2 + (XI_CH - 1) * self.moments['mean_eta'])
        raw = self.fading.raw

        def integrate(factor):
            return quad(lambda y: math.exp(self.fading.log_physical_active_density_in_log_eta(y)) * factor(y),
                        -math.inf, 0., epsabs=2e-11, epsrel=2e-11, limit=400)

        mass, mass_error = integrate(lambda y: 1.)
        m1, m1_error = integrate(math.exp)
        mh, mh_error = integrate(lambda y: math.exp(y / 2))
        mn, mn_error = integrate(lambda y: 2 + (XI_CH - 1) * math.exp(y))
        independent = dict(physical_pdf_mass=raw.P0 + raw.P1 * mass,
                           mean_eta=raw.P1 * m1, mean_sqrt_eta=raw.P1 * mh,
                           mean_eta_xi_total=2 * raw.P0 + raw.P1 * mn)
        self.assertAlmostEqual(independent['physical_pdf_mass'], 1., places=10)
        self.assertEqual(self.moments['outage_atom'], raw.P0)
        self.assertEqual(self.moments['outage_eta_xi_total_limit'], 2.)
        for key in ('mean_eta', 'mean_sqrt_eta', 'mean_eta_xi_total'):
            self.assertAlmostEqual(self.moments[key], independent[key], places=10)
        self.metrics['ideal_moments'] = dict(closed=self.moments, independent=independent,
            quadrature_errors=[mass_error, m1_error, mh_error, mn_error])

    def test_dual_noise_identities_and_detector_independent_covariance(self):
        nonideal = effective_fading_channel(self.fading.moments(R=.7, xi_det=.0135, xi_ch=XI_CH), VA)
        m1, mh, mn = (self.moments[key] for key in ('mean_eta', 'mean_sqrt_eta', 'mean_eta_xi_total'))
        t = mh * mh
        direct = (m1 - t) * VA + m1 * XI_CH
        recovered = (m1 - t) * VA + mn + m1 - 1 - self.moments['chi_het']
        self.assertEqual(self.effective['T_eff'], t)
        self.assertAlmostEqual(direct, recovered, places=13)
        self.assertAlmostEqual(self.effective['output_excess_noise'], direct, places=13)
        self.assertAlmostEqual(self.effective['xi_eff'], direct / t, places=13)
        self.assertEqual(nonideal['T_eff'], t)
        self.assertEqual(nonideal['output_excess_noise'], direct)
        self.assertEqual(nonideal['b'], self.effective['b'])
        self.assertEqual(corrected_z_star(nonideal, self.candidate['C'], self.candidate['w']), self.z)
        self.assertAlmostEqual(nonideal['mean_eta_xi_total'] - mn, nonideal['chi_het'] - 1., places=13)
        self.assertAlmostEqual(t, .160920291, delta=1e-9)
        self.assertAlmostEqual(self.z, 2.575487382, delta=1e-9)
        self.assertEqual(hashlib.sha256(self.source_path.read_bytes()).hexdigest(), self.source_sha256)
        self.metrics['detector_noise_audit'] = dict(ideal_effective=self.effective,
            nonideal_total_noise_moment=nonideal['mean_eta_xi_total'],
            ideal_total_noise_moment=mn, Z_star=self.z, direct_noise=direct, recovered_noise=recovered,
            source_sha256=self.source_sha256)

    def test_quantum_covariance_spectrum_and_stable_entropy(self):
        covariance = corrected_covariance(self.effective, VA, self.z)
        matrix = np.asarray(covariance['Gamma_AB'])
        omega = np.kron(np.eye(2), np.array([[0., 1.], [-1., 0.]]))
        self.assertGreater(float(np.linalg.eigvalsh(matrix).min()), 0.)
        self.assertGreater(float(np.linalg.eigvalsh(matrix + 1j * omega).min()), 0.)
        independent_spectrum = np.sort(np.abs(np.linalg.eigvals(1j * omega @ matrix)))
        np.testing.assert_allclose(independent_spectrum,
            sorted([covariance['lambda_1']] * 2 + [covariance['lambda_2']] * 2), atol=1e-12, rtol=1e-12)
        independent_chi, eigenvalues = independent_holevo(covariance['a'], covariance['b'], self.z)
        for index, expected in enumerate(eigenvalues, start=1):
            self.assertGreaterEqual(covariance[f'lambda_{index}'], 1.)
            self.assertAlmostEqual(covariance[f'lambda_{index}'], expected, places=12)
        chi = entropy((covariance['lambda_1'] - 1) / 2) + entropy((covariance['lambda_2'] - 1) / 2) - entropy((covariance['lambda_3'] - 1) / 2)
        self.assertTrue(math.isfinite(chi))
        self.assertAlmostEqual(chi, independent_chi, places=12)
        self.assertEqual(entropy(0.), 0.)
        for n in (1e-250, 1e-12, 1., 1e6):
            self.assertTrue(math.isfinite(entropy(n)))
            self.assertGreaterEqual(entropy(n), 0.)
        self.assertEqual(covariance['numerical_repairs'], [])
        self.metrics['ideal_covariance'] = dict(covariance=covariance, chi_BE_at_Z_star=chi,
            independently_computed_chi_BE_at_Z_star=independent_chi)

    def test_theoretical_interval_and_independent_dense_holevo(self):
        c, w = self.candidate['C'], self.candidate['w']
        interval = admissible_correlation_interval(self.effective, VA, c, w)
        m1, mh = self.moments['mean_eta'], self.moments['mean_sqrt_eta']
        nbar = VA / 2
        c1, c2, n_b = mh * c, mh * nbar, m1 * (VA + XI_CH) / 2
        spread = math.sqrt(w * (n_b - c2 * c2 / nbar))
        self.assertAlmostEqual(interval['theoretical_lower'], 2 * c1 - 2 * spread, places=12)
        self.assertAlmostEqual(interval['theoretical_upper'], 2 * c1 + 2 * spread, places=12)
        result = holevo_interval_maximizer(self.effective, VA, c, w,
            detector_security_convention='ideal', R=1., xi_det=0., grid_size=257, tolerance=1e-8)
        self.assertEqual(result['status'], 'NUMERICALLY_VERIFIED')
        lo, hi = interval['lower'], interval['upper']
        a, b = VA + 1, 1 + m1 * (VA + XI_CH)
        dense = max(independent_holevo(a, b, float(z))[0] for z in np.linspace(lo, hi, 4097))
        self.assertAlmostEqual(result['chi_BE'], dense, delta=1e-8)
        self.assertGreaterEqual(result['Z_worst'], lo)
        self.assertLessEqual(result['Z_worst'], hi)
        self.assertGreaterEqual(result['chi_BE'] + 1e-12, independent_holevo(a, b, self.z)[0])
        self.assertFalse(result['rigorous_global_error_enclosure'])
        self.assertFalse(result['monotonicity_assumed'])
        self.metrics['ideal_interval_holevo'] = dict(result=result, independent_grid_size=4097,
            independent_grid_max=dense, interval=interval)

    def test_ideal_complex_receiver_shot_noise_and_outage_likelihood(self):
        alpha = self.candidate['ensemble'].amplitudes.detach().cpu().numpy().reshape(-1)
        eta = np.array([0., .3, 1.])
        means, variance = receiver_parameters(alpha, eta, R=1., xi_det=0., xi_ch=XI_CH)
        np.testing.assert_allclose(means, alpha[:, None] * np.sqrt(eta), rtol=0, atol=0)
        np.testing.assert_allclose(variance, 1 + eta * XI_CH / 2, rtol=0, atol=0)
        np.testing.assert_allclose(variance, (1 + detector_noise(1., 0.) + eta * XI_CH) / 2)
        self.assertEqual(variance[0], 1.)
        _, noiseless = receiver_parameters(alpha, eta, R=1., xi_det=0., xi_ch=0.)
        np.testing.assert_array_equal(noiseless, np.ones(3))
        weights, y = np.array([.2, .35, .45]), np.array([.1 + .3j, -.9 + .2j])
        actual = np.exp(_mixture_log_likelihood(y, alpha, eta, weights, R=1., xi_det=0., xi_ch=XI_CH))
        independent = np.zeros((len(y), len(alpha)))
        for t, weight in zip(eta, weights):
            sigma2 = 1 + t * XI_CH / 2
            independent += weight * np.exp(-np.abs(y[:, None] - math.sqrt(t) * alpha)**2 / sigma2) / (math.pi * sigma2)
        np.testing.assert_allclose(actual, independent, rtol=2e-14, atol=1e-14)
        self.assertTrue(np.all(actual > .2 * np.exp(-np.abs(y)**2)[:, None] / math.pi))
        self.metrics['ideal_receiver'] = dict(complex_variances=variance.tolist(),
            intrinsic_complex_shot_noise=1., nonideal_detector_noise_added=0., reference_MI='NOT_RUN_IN_TESTS')


if __name__ == '__main__':
    unittest.main()
