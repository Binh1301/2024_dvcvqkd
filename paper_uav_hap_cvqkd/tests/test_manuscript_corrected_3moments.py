"""Lightweight A--K/M--O checks; no AP, source recomputation, or sweep.

The full protected-file receipt (B/O) and actual fading-mixture MI (L) are
validated separately by the corrected-mode validation runner.
"""
import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from scipy.special import log_ndtr

from src.manuscript_literal_3moments import (
    LiteralChannel, ManuscriptModelError, detector_noise, evaluate_candidate as literal_evaluate,
)
from src.manuscript_corrected_3moments import (
    CorrectedModelError, PhysicalFadingDistribution,
    deterministic_moments, effective_fading_channel, corrected_z_star, corrected_covariance,
    admissible_correlation_interval, holevo_interval_maximizer,
)

ROOT = Path(__file__).resolve().parents[1]


def raw_integral(channel, power, *, lower=-math.inf, upper=0.):
    """Integrate Eq. (10) in log eta without using Q or active_moment."""
    B = channel.A0 * channel.eta_atm
    d = channel.w_eq ** 2 / (4 * channel.sigma_s ** 2)
    log_C1 = channel.rho ** 2 / channel.sigma_s ** 2 + .5 * channel.sigma_R2 * d * (1+d)
    C3 = (32 * channel.rho**2 * channel.sigma_s**2 / channel.w_eq**4 + 2*channel.sigma_R2)**(-.5)
    mu = 6*channel.rho**2/channel.w_eq**2 + .5*channel.sigma_R2*(1+2*d)

    def integrand(y):
        log_erfc = math.log(2.) + float(log_ndtr(-math.sqrt(2.)*C3*(y-math.log(B)+mu)))
        return math.exp(math.log(d/2.) + log_C1 - d*math.log(B) + (d+power)*y + log_erfc)

    return quad(integrand, lower, upper, epsabs=2e-11, epsrel=2e-11, limit=500)


def synthetic_moments(m1=.4, mh=.5, *, xi_ch=.0186, R=.7, xi_det=.0135):
    chi = detector_noise(R, xi_det)
    return dict(mean_eta=m1, mean_sqrt_eta=mh,
                mean_eta_xi_total=1+chi+(xi_ch-1)*m1,
                chi_het=chi, xi_ch=xi_ch, R=R, xi_det=xi_det,
                physical_probability_mass=1., normalized=True,
                normalization_status='WITHIN_TOLERANCE')


def independent_holevo(a, b, z):
    """Independent ideal-heterodyne scalar entropy calculation."""
    delta = a*a+b*b-2*z*z
    determinant = (a*b-z*z)**2
    root = math.sqrt(delta*delta-4*determinant)
    eigenvalues = (math.sqrt((delta+root)/2), math.sqrt((delta-root)/2),
                   a-z*z/(b+1))
    if min(eigenvalues) < 1:
        raise AssertionError('Independent diagnostic encountered a nonphysical covariance')

    def g(x):
        return 0. if x == 0 else ((x+1)*math.log2(x+1)-x*math.log2(x))

    return g((eigenvalues[0]-1)/2)+g((eigenvalues[1]-1)/2)-g((eigenvalues[2]-1)/2)


class ManuscriptCorrectedTests(unittest.TestCase):
    metrics = {}

    @classmethod
    def setUpClass(cls):
        from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        cls.config = unconstrained_config()
        checkpoint_path = ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization/grid_timeout_retry_1/objective_checkpoint.json'
        cls.checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        cls.entry = next(e for e in cls.checkpoint if e['L_km'] == 21.9393102292)
        cls.reference = next(r for r in cls.entry['rows'] if r['nu_raw'] == .165 and r['V_A'] == 5.5)
        cls.source_path = ROOT / cls.reference['source_path']
        cls.source_hash = hashlib.sha256(cls.source_path.read_bytes()).hexdigest()
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            cls.candidate = verified_candidate(cls.source_path, cls.config)
        physical = derive_physical_inputs(.92,
            zenith_angle_rad_override=math.acos(19000/(21.9393102292*1000)),
            aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
        cls.raw = LiteralChannel.from_physical(physical)
        cls.physical = PhysicalFadingDistribution(cls.raw)

    def test_A_centered_MB_and_existing_source_identity(self):
        from scripts.exact_cache_provenance import source_settings, verify_source_payload
        from scripts.run_exact_mb_test2 import RAW_TO_REPO_MB_SCALE, nu_mb_repo, ensemble_hash
        from src.modulation.qam256 import square_qam256
        ensemble = self.candidate['ensemble']
        probabilities = ensemble.probabilities[0].detach().cpu().numpy()
        amplitudes = ensemble.amplitudes[0].detach().cpu().numpy()
        raw = square_qam256(alpha0=math.sqrt(30.)).detach().cpu().numpy()
        levels = np.arange(16, dtype=float)-7.5
        coordinates = np.array([complex(x, y) for x in levels for y in levels])
        np.testing.assert_allclose(raw, coordinates, atol=1e-14, rtol=0)
        expected = np.exp(-.165*np.abs(coordinates)**2)
        expected /= expected.sum()
        self.assertEqual(len(probabilities), 256)
        np.testing.assert_allclose(probabilities, expected, atol=1e-14, rtol=1e-14)
        self.assertAlmostEqual(float(probabilities.sum()), 1., places=14)
        np.testing.assert_allclose(probabilities.reshape(16, 16),
                                   probabilities.reshape(16, 16)[::-1, ::-1], atol=1e-14, rtol=0)
        self.assertLess(abs(np.sum(probabilities*amplitudes)), 1e-14)
        self.assertLess(abs(np.sum(probabilities*amplitudes**2)), 1e-13)
        photons = float(np.sum(probabilities*np.abs(amplitudes)**2))
        self.assertAlmostEqual(2*photons, 5.5, places=13)
        self.assertEqual(RAW_TO_REPO_MB_SCALE, 42.5)
        self.assertEqual(nu_mb_repo(.165), 42.5*.165)
        payload = json.loads(self.source_path.read_text(encoding='utf-8'))
        verified = verify_source_payload(payload, source_settings(self.config))
        self.assertIn(self.candidate['source_cache_key'],
                      (verified['historical_cache_key'], verified['canonical_source_cache_key']))
        self.assertEqual(ensemble_hash(ensemble), payload['ensemble_hash'])
        self.assertEqual((self.candidate['C'], self.candidate['w']), (payload['C'], payload['w']))
        self.metrics['A_source'] = dict(symbols=256, nu_raw=.165, nu_repo=nu_mb_repo(.165),
            average_photon_number=photons, VA=2*photons,
            source_cache_key=self.candidate['source_cache_key'], source_sha256=self.source_hash)

    def test_B_C_raw_tail_and_separate_physical_normalization(self):
        retained, retained_error = raw_integral(self.raw, 0.)
        tail, tail_error = raw_integral(self.raw, 0., lower=0., upper=math.inf)
        raw_mass = self.raw.P0+self.raw.P1*retained
        self.assertAlmostEqual(raw_mass, .9841200272202841, places=12)
        self.assertAlmostEqual(retained+tail, 1., places=10)
        self.assertGreater(tail, 0)
        diagnostics = self.physical.diagnostics()
        self.assertAlmostEqual(diagnostics['raw_probability_mass'], raw_mass, places=10)
        self.assertAlmostEqual(diagnostics['discarded_raw_mass'], self.raw.P1*tail, places=10)
        self.assertAlmostEqual(diagnostics['physical_probability_mass'], 1., places=10)
        self.assertAlmostEqual(self.raw.P0+self.raw.P1*retained/retained, 1., places=14)
        coefficients = self.raw.coefficients()
        self.assertAlmostEqual(retained, coefficients['C1']*math.exp(self.raw.log_Q(coefficients['chi2'])), places=10)
        # The active normalization preserves P0, unlike normalizing the mixture.
        self.assertNotAlmostEqual(self.raw.P0/raw_mass, self.raw.P0, places=8)
        self.metrics['B_C_normalization'] = dict(diagnostics=diagnostics,
            independently_retained_active_mass=retained, independently_raw_tail=tail,
            independent_raw_full_mass=self.raw.P0+self.raw.P1*(retained+tail),
            quadrature_errors=[retained_error, tail_error], preserved_outage_atom=self.raw.P0)

    def test_D_three_moments_independent_integrals(self):
        records = []
        for raw in (self.raw, LiteralChannel(.85, .91, 1.4, 1., .12, 0., .02, .98)):
            distribution = PhysicalFadingDistribution(raw)
            actual = distribution.moments(R=.7, xi_det=.0135, xi_ch=.0186)
            f1 = raw_integral(raw, 0.)[0]
            eta = raw.P1*raw_integral(raw, 1.)[0]/f1
            sqrt_eta = raw.P1*raw_integral(raw, .5)[0]/f1
            chi = detector_noise(.7, .0135)
            # At the outage atom use the continuous limit of eta*xi_total.
            noise = raw.P0*(1+chi) + raw.P1*((1+chi)*f1+(.0186-1)*raw_integral(raw, 1.)[0])/f1
            self.assertAlmostEqual(actual['mean_eta'], eta, places=10)
            self.assertAlmostEqual(actual['mean_sqrt_eta'], sqrt_eta, places=10)
            self.assertAlmostEqual(actual['mean_eta_xi_total'], noise, places=10)
            self.assertAlmostEqual(actual['mean_eta_xi_total'], 1+chi+(.0186-1)*eta, places=13)
            records.append(dict(closed_forms=actual, independent_mean_eta=eta,
                                independent_mean_sqrt_eta=sqrt_eta, independent_noise=noise))
        self.metrics['D_independent_moments'] = records

    def test_E_F_G_H_corrected_reference_and_equivalent_paths(self):
        moments = self.physical.moments()
        effective = effective_fading_channel(moments, 5.5)
        m1, mh, mn = (moments[key] for key in ('mean_eta', 'mean_sqrt_eta', 'mean_eta_xi_total'))
        t = mh**2
        noise_direct = (m1-t)*5.5+m1*.0186
        noise_third = (m1-t)*5.5+mn+m1-1-moments['chi_het']
        self.assertEqual(effective['T_eff'], t)
        self.assertGreaterEqual(t, 0.)
        self.assertLessEqual(t, m1)
        self.assertLessEqual(m1, 1.)
        self.assertAlmostEqual(effective['output_excess_noise'], noise_direct, places=13)
        self.assertAlmostEqual(effective['output_excess_noise_from_third'], noise_third, places=13)
        self.assertAlmostEqual(noise_direct, noise_third, places=13)
        self.assertAlmostEqual(effective['xi_eff'], noise_direct/t, places=13)
        c, w = self.candidate['C'], self.candidate['w']
        z = corrected_z_star(effective, c, w)
        self.assertAlmostEqual(z, 2*math.sqrt(t)*c-math.sqrt(2*t*effective['xi_eff']*w), places=13)
        self.assertAlmostEqual(z, 2*mh*c-math.sqrt(2*w*noise_third), places=13)
        cov = corrected_covariance(effective, 5.5, z)
        self.assertAlmostEqual(cov['a'], 6.5, places=13)
        self.assertAlmostEqual(cov['b'], 1+m1*(5.5+.0186), places=13)
        self.assertAlmostEqual(cov['b'], (5.5+1)*m1+mn-moments['chi_het'], places=13)
        self.assertTrue(np.isfinite(np.array(cov['Gamma_AB'])).all())
        self.assertGreater(min(cov['lambda_1'], cov['lambda_2'], cov['lambda_3']), 1.)
        self.metrics['E_F_G_H_reference_algebra'] = dict(moments=moments, effective=effective,
            covariance=cov, source_C=c, source_w=w, Z_star=z,
            literal_third_moment=self.raw.moments()['mean_eta_xi'],
            corrected_minus_literal_third_moment=mn-self.raw.moments()['mean_eta_xi'],
            corrected_SKR_evaluation='NOT_RUN')

    def test_I_deterministic_and_noiseless_limits(self):
        results = []
        for t in (.0625, .25, 1.):
            for xi in (.0186, 0.):
                effective = effective_fading_channel(synthetic_moments(t, math.sqrt(t), xi_ch=xi), 2.)
                z = corrected_z_star(effective, 1., .01)
                self.assertEqual(effective['T_eff'], t)
                self.assertEqual(effective['variance_sqrt_eta'], 0.)
                self.assertAlmostEqual(effective['xi_eff'], xi, places=13)
                self.assertAlmostEqual(z, 2*math.sqrt(t)-math.sqrt(2*t*xi*.01), places=14)
                if xi == 0:
                    self.assertEqual(z, 2*math.sqrt(t))
                results.append(dict(T0=t, xi_ch=xi, effective=effective, Z_star=z))
        zero = effective_fading_channel(synthetic_moments(0., 0.), 2.)
        self.assertEqual(zero['T_eff'], 0.)
        self.assertIsNone(zero['xi_eff'])
        self.assertEqual(zero['output_excess_noise'], 0.)
        self.assertEqual(corrected_z_star(zero, 1., .01), 0.)
        self.metrics['I_limits'] = results
        self.metrics['I_zero_effective'] = zero

    def test_I_nonbinary_analytic_deterministic_limits(self):
        results = []
        for t in (.07, .2, .3, .7):
            for xi in (.0186, 0.):
                moments = deterministic_moments(t, R=.7, xi_det=.0135, xi_ch=xi)
                self.assertEqual(moments['moment_law'], 'deterministic_delta')
                self.assertEqual(moments['deterministic_transmissivity'], t)
                effective = effective_fading_channel(moments, 2.)
                self.assertEqual(effective['T_eff'], t)
                self.assertEqual(effective['variance_sqrt_eta'], 0.)
                self.assertAlmostEqual(effective['xi_eff'], xi, places=14)
                self.assertEqual(effective['amplitude_square_rounding_residual'], math.sqrt(t)**2-t)
                self.assertEqual(effective['effective_transmittance_evaluation_method'],
                                 'analytic_deterministic_delta_identity')
                self.assertTrue(effective['deterministic_channel_handling'])
                self.assertEqual(effective['output_excess_noise'], t*xi)
                z = corrected_z_star(effective, 1., .01)
                self.assertAlmostEqual(z, 2*math.sqrt(t)-math.sqrt(2*t*xi*.01), places=14)
                if xi == 0:
                    self.assertEqual(z, 2*math.sqrt(t))
                results.append(dict(T0=t, xi_ch=xi, effective=effective, Z_star=z))
        # The analytic delta representation is explicit: arbitrary rounded
        # moment inputs do not acquire an automatic no-fading classification.
        self.assertGreater(math.sqrt(.7)**2, .7)
        self.assertRaises(CorrectedModelError, effective_fading_channel,
                          synthetic_moments(.7, math.sqrt(.7)), 2.)
        tampered = deterministic_moments(.3)
        self.assertRaises(ManuscriptModelError, effective_fading_channel,
                          {**tampered, 'mean_eta': .4}, 2.)
        self.metrics['I_nonbinary_analytic_delta_limits'] = results

    def test_J_quantum_covariance_and_no_repairs(self):
        effective = effective_fading_channel(synthetic_moments(), 2.)
        cov = corrected_covariance(effective, 2., 1.)
        matrix = np.array(cov['Gamma_AB'])
        omega = np.kron(np.eye(2), np.array([[0., 1.], [-1., 0.]]))
        self.assertGreater(np.linalg.eigvalsh(matrix).min(), 0.)
        self.assertGreater(np.linalg.eigvalsh(matrix+1j*omega).min(), 0.)
        self.assertGreaterEqual(min(cov['lambda_1'], cov['lambda_2'], cov['lambda_3']), 1.)
        self.assertEqual(cov.get('numerical_repairs', []), [])
        cap = math.sqrt(cov['a']*cov['b']-1-abs(cov['a']-cov['b']))
        self.assertRaises(CorrectedModelError, corrected_covariance, effective, 2., cap*(1+1e-10))
        self.assertRaises(CorrectedModelError, corrected_covariance, effective, 2., 100.)
        self.assertRaises(ManuscriptModelError, corrected_covariance, effective, 2., math.nan)

    def test_K_theory_interval_and_independent_ideal_maximization(self):
        effective = effective_fading_channel(synthetic_moments(R=1., xi_det=0.), 2.)
        c, w = 1., .01
        interval = admissible_correlation_interval(effective, 2., c, w)
        center = 2*math.sqrt(effective['T_eff'])*c
        radius = math.sqrt(2*effective['output_excess_noise']*w)
        a, b = 3., 1+.4*(2+.0186)
        cap = math.sqrt(min((a+1)*(b-1), (a-1)*(b+1)))
        self.assertAlmostEqual(interval['theoretical_lower'], center-radius, places=13)
        self.assertAlmostEqual(interval['theoretical_upper'], center+radius, places=13)
        self.assertAlmostEqual(interval['lower'], max(center-radius, -cap), places=13)
        self.assertAlmostEqual(interval['upper'], min(center+radius, cap), places=13)
        self.assertAlmostEqual(interval['Z_star'], corrected_z_star(effective, c, w), places=13)
        result = holevo_interval_maximizer(effective, 2., c, w,
            detector_security_convention='ideal', R=1., xi_det=0., grid_size=257, tolerance=1e-8)
        self.assertEqual(result['status'], 'NUMERICALLY_VERIFIED')
        lo, hi = interval['lower'], interval['upper']
        grid = np.linspace(lo, hi, 4097)
        dense = max(independent_holevo(a, b, float(z)) for z in grid)
        refinement = minimize_scalar(lambda z: -independent_holevo(a, b, float(z)),
                                     bounds=(lo, hi), method='bounded', options={'xatol': 1e-12})
        expected = max(dense, -float(refinement.fun), independent_holevo(a, b, lo), independent_holevo(a, b, hi))
        self.assertAlmostEqual(result['chi_BE'], expected, delta=1e-8)
        self.assertGreaterEqual(result['chi_BE']+1e-10, dense)
        self.assertGreaterEqual(result['Z_worst'], lo)
        self.assertLessEqual(result['Z_worst'], hi)
        self.metrics['K_ideal_maximizer'] = dict(result=result, independent_dense_max=dense,
            independent_bounded_max=-float(refinement.fun), independent_expected=expected,
            independent_grid_size=4097, interval=interval)

    def test_K_nonideal_detector_fails_closed(self):
        effective = effective_fading_channel(synthetic_moments(), 2.)
        result = holevo_interval_maximizer(effective, 2., 1., .01,
            detector_security_convention='trusted', R=.7, xi_det=.0135)
        self.assertEqual(result['status'], 'SCIENTIFICALLY_UNRESOLVED')
        self.assertIsNone(result['chi_BE'])
        self.metrics['K_nonideal_detector'] = result
        # An ideal label cannot silently enable the ideal formula for R=.7.
        mislabeled = holevo_interval_maximizer(effective, 2., 1., .01,
            detector_security_convention='ideal', R=.7, xi_det=.0135)
        self.assertEqual(mislabeled['status'], 'SCIENTIFICALLY_UNRESOLVED')
        self.assertIsNone(mislabeled['chi_BE'])

    def test_K_interval_intersection_and_interior_optimum(self):
        effective = effective_fading_channel(synthetic_moments(R=1., xi_det=0.), 2.)
        clipped = admissible_correlation_interval(effective, 2., .1, 5.)
        self.assertGreater(clipped['theoretical_upper'], clipped['Z_physical_cap'])
        self.assertEqual(clipped['upper'], clipped['Z_physical_cap'])
        self.assertRaises(CorrectedModelError, admissible_correlation_interval,
                          effective, 2., 100., .01)
        # A synthetic interval across zero requires an interior maximizer;
        # checking only a lower endpoint or assuming monotonicity fails here.
        result = holevo_interval_maximizer(effective, 2., .1, .5,
            detector_security_convention='ideal', R=1., xi_det=0., tolerance=1e-8)
        self.assertEqual(result['status'], 'NUMERICALLY_VERIFIED')
        self.assertLess(abs(result['Z_worst']), 2e-7)
        self.assertAlmostEqual(result['chi_BE'], independent_holevo(3., effective['b'], 0.), delta=1e-8)
        self.assertGreater(result['chi_BE'], max(result['endpoint_chi']))
        self.metrics['K_interior_maximizer'] = result

    def test_fail_closed_moments_source_and_boresight(self):
        for changes in (dict(mean_eta=.1, mean_sqrt_eta=.5), dict(mean_eta=1.1),
                        dict(mean_sqrt_eta=math.nan), dict(mean_eta_xi_total=math.inf),
                        dict(mean_eta_xi_total=-1.)):
            with self.subTest(changes=changes):
                self.assertRaises(ManuscriptModelError, effective_fading_channel,
                                  {**synthetic_moments(), **changes}, 2.)
        eff = effective_fading_channel(synthetic_moments(), 2.)
        self.assertRaises(ManuscriptModelError, corrected_z_star, eff, 1., -.01)
        nonzero = LiteralChannel(.85, .91, 1.4, 1., .12, .2, .02, .98)
        with self.assertRaisesRegex(CorrectedModelError, '(?i)(rho|boresight|unsupported)'):
            PhysicalFadingDistribution(nonzero).diagnostics()
        with patch.object(LiteralChannel, 'active_moment', return_value=0.):
            with self.assertRaises(ManuscriptModelError):
                PhysicalFadingDistribution(self.raw).moments()

    def test_M_historical_actual_reference_and_contexts(self):
        from scripts.exact_cache_provenance import objective_compatible, objective_identity
        from scripts.run_skr_vs_link_distance_theta10urad import evaluate_candidate as historical
        for entry in self.checkpoint:
            identity = entry['identity']['identity']
            self.assertTrue(objective_compatible(entry['identity'], objective_identity(identity['config'], identity['channel'])))
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            result = historical(self.candidate, self.entry['identity']['identity']['channel'], self.config)
        self.assertAlmostEqual(result['SKR'], .07798099387393764, places=13)
        self.assertAlmostEqual(result['I_AB'], self.reference['I_AB'], places=13)
        self.metrics['M_historical_regression'] = dict(result=result, compatible_historical_contexts=26)

    def test_N_literal_actual_reference_and_local_source_preservation(self):
        from scripts.exact_cache_provenance import json_hash
        moments = self.raw.moments()
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            result = literal_evaluate(self.candidate, moments, distance_km=21.9393102292,
                physical_config_hash=json_hash(self.raw.__dict__),
                numerical_config_hash=json_hash(json.loads((ROOT/'configs/manuscript_literal_3moments.json').read_text(encoding='utf-8'))))
        self.assertAlmostEqual(result['pdf_mass'], .9841200272202841, places=13)
        self.assertAlmostEqual(result['SKR'], -2.454774809836829, places=12)
        self.assertEqual(result['eta_f'], result['mean_sqrt_eta'])
        self.assertFalse(result['normalized'])
        self.assertEqual(result['numerical_repairs'], [])
        self.assertEqual(hashlib.sha256(self.source_path.read_bytes()).hexdigest(), self.source_hash)
        self.metrics['N_literal_regression'] = result


if __name__ == '__main__':
    unittest.main()
