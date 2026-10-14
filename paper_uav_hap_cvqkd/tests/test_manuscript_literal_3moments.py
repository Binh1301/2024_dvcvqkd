"""Lightweight A--F checks; source moments always come from existing cache."""
import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from scipy.integrate import quad
from scipy.special import erfc

from src.manuscript_literal_3moments import (
    LiteralChannel, ManuscriptModelError, covariance, detector_noise,
    effective_channel, entropy, evaluate_candidate, holevo, total_input_noise, z_star,
)

ROOT = Path(__file__).resolve().parents[1]


class ManuscriptLiteralTests(unittest.TestCase):
    metrics = {}

    @classmethod
    def setUpClass(cls):
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        cls.config = unconstrained_config()
        checkpoint = json.loads((ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization/grid_timeout_retry_1/objective_checkpoint.json').read_text())
        cls.checkpoint = checkpoint
        cls.entry = next(e for e in checkpoint if e['L_km'] == 21.9393102292)
        cls.reference = next(r for r in cls.entry['rows'] if r['nu_raw'] == .165 and r['V_A'] == 5.5)
        cls.candidate = verified_candidate(ROOT / cls.reference['source_path'], cls.config)

    def test_A_B_C_literal_algebra(self):
        moments = dict(mean_eta=.4, mean_sqrt_eta=.5, mean_eta_xi=.25)
        eff = effective_channel(moments, 2.)
        self.assertEqual(eff['eta_f'], .5)
        self.assertAlmostEqual(eff['variance_sqrt_eta'], .15)
        self.assertAlmostEqual(eff['eta_f_xi_f'], .55)
        expected_z = 2 * math.sqrt(.5) - math.sqrt(2 * .55 * .01)
        self.assertEqual(z_star(eff, 1., .01), expected_z)
        cov = covariance(moments, 2., 1., .01)
        self.assertEqual(cov['a'], 3.)
        self.assertAlmostEqual(cov['b'], 2.55)
        self.assertEqual(cov['Z_star'], expected_z)
        self.assertNotAlmostEqual(expected_z, 2 * .5 - math.sqrt(2 * .55 * .01))
        a, b = 3., 2.55
        delta, determinant = a*a + b*b - 2*expected_z**2, (a*b - expected_z**2)**2
        self.assertAlmostEqual(cov['lambda_1'], math.sqrt((delta + math.sqrt(delta**2 - 4*determinant))/2))
        self.assertAlmostEqual(cov['lambda_2'], math.sqrt((delta - math.sqrt(delta**2 - 4*determinant))/2))
        self.assertAlmostEqual(cov['lambda_3'], a - expected_z**2/(b+1))
        self.assertTrue(math.isfinite(holevo(cov)))
        self.metrics['synthetic_C'] = cov

    def test_D_independent_finite_integrals(self):
        discrepancies = []
        for rho in (0., .2):
            channel = LiteralChannel(.85, .91, 1.4, 1., .12, rho, .02, .98)
            B, a = .85 * .91, (1.4 / 2.)**2
            C1 = math.exp(rho*rho + .5*.12*a*(1+a))
            C3 = (32*rho*rho/1.4**4 + 2*.12)**(-.5)
            mu = 6*rho*rho/1.4**2 + .5*.12*(1+2*a)

            def independent_integral(q):
                def integrand(eta):
                    return .98*a*C1/(2*B**a) * eta**(a-1+q) * erfc(C3*(math.log(eta/B)+mu))
                return quad(integrand, 0., 1., epsabs=1e-10, epsrel=1e-10, limit=500)[0]

            moments = channel.moments()
            i0, i1, ih = (independent_integral(q) for q in (0., 1., .5))
            self.assertAlmostEqual(moments['mean_eta'], i1, places=9)
            self.assertAlmostEqual(moments['mean_sqrt_eta'], ih, places=9)
            self.assertAlmostEqual(moments['pdf_mass'], .02 + i0, places=9)
            noise_integral = (1 + detector_noise()) * .02 + quad(
                lambda eta: eta * total_input_noise(eta) * .98*a*C1/(2*B**a) * eta**(a-1)
                * erfc(C3*(math.log(eta/B)+mu)), 0., 1., epsabs=1e-9, epsrel=1e-9, limit=500)[0]
            self.assertAlmostEqual(moments['mean_eta_xi'], noise_integral, places=8)
            self.assertFalse(moments['normalized'])
            self.assertNotEqual(moments['normalization_discrepancy'], 0.)
            discrepancies.append(dict(rho=rho, **moments))
        self.assertEqual(discrepancies[1]['normalization_status'], 'DISCREPANCY')
        self.metrics['independent_integrals_D'] = discrepancies

    def test_E_historical_reference_and_contexts(self):
        from scripts.exact_cache_provenance import objective_compatible, objective_identity
        from scripts.run_skr_vs_link_distance_theta10urad import evaluate_candidate as original
        for entry in self.checkpoint:
            expected = objective_identity(entry['identity']['identity']['config'], entry['identity']['identity']['channel'])
            self.assertTrue(objective_compatible(entry['identity'], expected))
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            old = original(self.candidate, self.entry['identity']['identity']['channel'], self.config)
        self.assertAlmostEqual(old['SKR'], .07798099387393764, places=13)
        self.assertAlmostEqual(old['I_AB'], self.reference['I_AB'], places=13)
        self.metrics['historical_E'] = old
        self.metrics['historical_contexts_verified'] = 26

    def test_D_F_single_reference_new_backend(self):
        from scripts.calculate_channel_pdf_and_moments import closed_form_channel_moments, derive_physical_inputs
        from scripts.exact_cache_provenance import json_hash
        physical = derive_physical_inputs(.92, zenith_angle_rad_override=math.acos(19000/(21.9393102292*1000)),
                                         aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
        channel = LiteralChannel.from_physical(physical)
        moments = channel.moments()
        self.assertEqual(channel.sigma_R2, physical['sigma_R0_squared'])
        self.assertNotEqual(channel.A0, physical['pointing']['A0'])
        self.assertAlmostEqual(moments['chi_het'], 1.8957142857142857, places=14)
        with patch('src.cvqkd.gram_moments._fallback', side_effect=AssertionError('AP forbidden')):
            result = evaluate_candidate(self.candidate, moments, distance_km=21.9393102292,
                                        physical_config_hash=json_hash(channel.__dict__),
                                        numerical_config_hash=json_hash(json.loads((ROOT / 'configs/manuscript_literal_3moments.json').read_text())))
        self.assertTrue(result['status'].startswith('PASS'))
        self.assertEqual(result['eta_f'], result['mean_sqrt_eta'])
        self.assertEqual(result['SKR'], .95 * result['I_AB'] - result['chi_BE'])
        self.assertEqual(result['numerical_repairs'], [])
        self.metrics['reference_new_mode_D_F'] = result
        self.metrics['historical_raw_moments_D'] = closed_form_channel_moments(physical, epsilon_total=.0186)

    def test_F_fail_closed_domains_and_zero(self):
        self.assertEqual(entropy(0.), 0.)
        self.assertTrue(math.isfinite(entropy(1e-300)))
        self.assertTrue(math.isfinite(entropy(1e-12)))
        self.assertRaises(ManuscriptModelError, entropy, -1e-15)
        self.assertRaises(ManuscriptModelError, detector_noise, 0.)
        self.assertRaises(ManuscriptModelError, total_input_noise, 0.)
        self.assertRaises(ManuscriptModelError, effective_channel,
                          dict(mean_eta=.1, mean_sqrt_eta=.5, mean_eta_xi=.25), 2.)
        self.assertRaises(ManuscriptModelError, effective_channel,
                          dict(mean_eta=.4, mean_sqrt_eta=1e-300, mean_eta_xi=1e308), 2.)
        self.assertRaises(ManuscriptModelError, covariance,
                          dict(mean_eta=.4, mean_sqrt_eta=.5, mean_eta_xi=.25), 2., 100., .01)
        # Positive definite but violates the uncertainty condition: reject,
        # rather than raise lambda_2 to one.
        c_for_z_2_5 = (2.5 + math.sqrt(.011)) / (2 * math.sqrt(.5))
        self.assertRaises(ManuscriptModelError, covariance,
                          dict(mean_eta=.4, mean_sqrt_eta=.5, mean_eta_xi=.25), 2., c_for_z_2_5, .01)
        self.assertRaises(ManuscriptModelError, LiteralChannel(.8, .9, 2., 1., .1, 100., .02, .98).moments)
        self.assertRaises(ManuscriptModelError, z_star, dict(eta_f=.5, eta_f_xi_f=.55), 1., -.01)
        modified = {**self.candidate, 'C': self.candidate['C'] + .01}
        self.assertRaises(ManuscriptModelError, evaluate_candidate, modified,
                          dict(mean_eta=.4, mean_sqrt_eta=.5, mean_eta_xi=.25), distance_km=21.9393102292,
                          physical_config_hash='TAMPER_TEST', numerical_config_hash='TAMPER_TEST')
        zero = dict(mean_eta=0., mean_sqrt_eta=0., mean_eta_xi=1+detector_noise(), normalization_status='WITHIN_TOLERANCE')
        record = evaluate_candidate(self.candidate, zero, distance_km=21.9393102292,
                                    physical_config_hash='ZERO_TEST', numerical_config_hash='ZERO_TEST')
        self.assertEqual(record['status'], 'ZERO_EFFECTIVE_TRANSMISSION')
        self.assertIsNone(record['xi_f'])
        self.assertIsNone(record['SKR'])
        self.metrics['zero_effective_F'] = record


if __name__ == '__main__':
    unittest.main()
