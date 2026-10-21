import math
import unittest
from dataclasses import replace

import numpy as np
from scipy.integrate import quad
from scipy.special import i0e

from src.full_fading_channel import (APERTURE_CORRECTED, PDF_ORIGINAL, OpticalConfig,
    FullFadingLaw, aperture_collection)
from src.full_fading_evaluator import effective_channel, evaluate_ideal_security, mixture_mi
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]


class FullFadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=OpticalConfig('narrow_10urad_D55',10e-6,.55)
        cls.law=FullFadingLaw(cls.config)

    def test_aperture_center_and_bessel(self):
        w,a=.14974341909718897,.275
        self.assertAlmostEqual(float(aperture_collection(0,w,a)),-math.expm1(-2*a*a/w**2),14)
        for r in (0.,.1,.275,.5,1.):
            ref=quad(lambda s:4*s/w**2*math.exp(-2*(s-r)**2/w**2)*i0e(4*s*r/w**2),0,a,epsabs=1e-13)[0]
            self.assertAlmostEqual(float(aperture_collection(r,w,a)),ref,12)

    def test_mean_pointing_identity(self):
        g=self.law.geometry; s=g['sigma_s_m']; a=g['radius_m']; w=g['w_eff_m']
        actual=quad(lambda r:float(self.law.hp(r))*float(self.law.radial_density(r)),0,12*s,epsabs=1e-13)[0]
        expected=-math.expm1(-2*a*a/(w*w+4*s*s))
        self.assertAlmostEqual(actual,expected,12)
        self.assertAlmostEqual(actual,.03311350682836657,12)

    def test_normalization_support_outage(self):
        nodes,weights,diagnostics=self.law.quadrature(40)
        self.assertAlmostEqual(float(weights.sum()),1.,13)
        self.assertTrue(np.all((0<=nodes)&(nodes<=1)))
        self.assertEqual(weights[0],self.law.P0)
        self.assertEqual(self.law.cdf(0),self.law.P0)
        self.assertAlmostEqual(self.law.cdf(1),1.,13)
        with self.assertRaises(ValueError): self.law.cdf(1.01)
        self.assertLess(max(diagnostics['errors'].values()),2e-9)
        for t in (.01,.1,.5):
            step=1e-5*t
            derivative=(self.law.cdf(t+step)-self.law.cdf(t-step))/(2*step)
            self.assertAlmostEqual(derivative,self.law.density(t),places=7)

    def test_moments_independent_product_quadrature(self):
        for mode in (PDF_ORIGINAL,APERTURE_CORRECTED):
            law=FullFadingLaw(self.config,mode)
            nodes,weights,_=law.quadrature(48)
            self.assertAlmostEqual(float(weights@nodes),law.mean_eta,9)
            self.assertAlmostEqual(float(weights@np.sqrt(nodes)),law.mean_sqrt_eta,9)
            self.assertGreaterEqual(law.mean_eta-law.mean_sqrt_eta**2,0)

    def test_old_model_only_old_checkpoint(self):
        old=FullFadingLaw(self.config,PDF_ORIGINAL)
        self.assertAlmostEqual(old.mean_eta,.2379088678213789,11)
        self.assertGreater(old.mean_eta,5*self.law.mean_eta)

    def test_rician_and_invalid_settings(self):
        law=FullFadingLaw(replace(self.config,boresight_m=.1))
        self.assertAlmostEqual(law.cdf(1),1.,12)
        with self.assertRaises(ValueError): FullFadingLaw(replace(self.config,boresight_m=.1),PDF_ORIGINAL)
        with self.assertRaises(ValueError): replace(self.config,support_policy='clip')
        with self.assertRaises(ValueError): replace(self.config,h_hap_m=21000)

    def test_effective_full_noise_and_b_identity(self):
        m=self.law.moments(); e=effective_channel(m,5.046875)
        self.assertGreater(e['variance_sqrt_eta'],0)
        self.assertAlmostEqual(e['b'],1+m['mean_eta']*(5.046875+.0186),13)
        self.assertAlmostEqual(e['b'],1+e['T_eff']*5.046875+e['N_eff'],13)
        self.assertGreater(e['xi_eff'],.0186)

    def test_no_fading_and_pure_loss_limits(self):
        for t in (.01,.5,1.):
            m=dict(mean_eta=t,mean_sqrt_eta=math.sqrt(t),moment_law='deterministic_delta',
                   deterministic_transmissivity=t,physical_probability_mass=1.,xi_ch=.0186,R=1.,xi_det=0.)
            e=effective_channel(m,2.)
            self.assertEqual(e['T_eff'],t)
            self.assertAlmostEqual(e['xi_eff'],.0186,14)
        m.update(mean_eta=0.,mean_sqrt_eta=0.,deterministic_transmissivity=0.,xi_ch=0.)
        e=effective_channel(m,2.)
        self.assertEqual(e['b'],1.)
        self.assertEqual(e['N_eff'],0.)

    def test_interval_and_heterodyne_independent_spectrum(self):
        e=effective_channel(FullFadingLaw(self.config,PDF_ORIGINAL).moments(),5.046875)
        security=evaluate_ideal_security(e,5.046875,2.9818069279923307,6.190945650452507e-7)
        c=security['covariance']
        self.assertAlmostEqual(c['lambda_3'],c['a']-c['Z']**2/(c['b']+1),13)
        omega=np.kron(np.eye(2),np.array([[0,1],[-1,0]]))
        spectrum=np.sort(np.abs(np.linalg.eigvals(1j*omega@np.array(c['Gamma_AB']))))[::2]
        np.testing.assert_allclose(spectrum,sorted([c['lambda_1'],c['lambda_2']]),atol=1e-12)
        self.assertGreaterEqual(min(c['lambda_1'],c['lambda_2'],c['lambda_3']),1)
        self.assertAlmostEqual(security['n_B']-security['c2']**2/(5.046875/2),e['N_eff']/2,13)
        self.assertGreaterEqual(security['chi_BE']+1e-12,max(security['endpoint_chi']))

    def test_mixture_zero_signal_and_deterministic_awgn(self):
        p=np.array([.5,.5]); alpha=np.array([-.3,.3],complex)
        mi=mixture_mi(p,alpha,np.array([0.]),np.array([1.]),output_order=20)
        self.assertAlmostEqual(mi,0.,14)
        values=[mixture_mi(p,alpha,np.array([.5]),np.array([1.]),output_order=n) for n in (24,40)]
        self.assertGreater(values[-1],0.)
        self.assertAlmostEqual(*values,places=10)

    def test_exact_256_source_normalization_energy_and_tampering(self):
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        from src.full_fading_evaluator import authenticate_source
        settings=json.loads((ROOT/'configs/corrected_full_fading.json').read_text())
        candidate=verified_candidate(ROOT/settings['source_payload'],unconstrained_config())
        ensemble=authenticate_source(candidate,settings['source_payload_sha256'])
        self.assertEqual(ensemble.probabilities.shape[-1],256)
        self.assertAlmostEqual(float(ensemble.probabilities.sum()),1.,14)
        self.assertAlmostEqual(float(ensemble.computed_va()[0]),5.046875,13)
        for field in ('C','w','V_A','nu_raw'):
            with self.assertRaises(ValueError):
                authenticate_source({**candidate,field:candidate[field]+.01},settings['source_payload_sha256'])
        with self.assertRaises(ValueError): authenticate_source(candidate,'0'*64)

    def test_detector_and_protocol_cannot_be_mixed(self):
        from src.full_fading_evaluator import evaluate_candidate
        settings=json.loads((ROOT/'configs/corrected_full_fading.json').read_text())
        for key,value in [('R',.7),('xi_det',.0135),('phase_noise','ON'),('xi_ch',0.)]:
            with self.assertRaises(ValueError):
                evaluate_candidate({},self.law,{**settings,key:value})

    def test_original_formula_moments_match_only_mode_A(self):
        from src.manuscript_literal_3moments import LiteralChannel
        law=FullFadingLaw(self.config,PDF_ORIGINAL); g=law.geometry
        raw=LiteralChannel(g['eta_atm'],g['A0'],g['w_eq_m'],g['sigma_s_m'],g['sigma_R2'],0.,law.P0,1-law.P0)
        self.assertAlmostEqual(raw.active_moment(0),law.retained,11)
        self.assertAlmostEqual((1-law.P0)*raw.active_moment(1)/law.retained,law.mean_eta,11)
        self.assertGreater(abs(self.law.mean_eta-law.mean_eta),.1)

    def test_main_corrected_caller_routes_new_pipeline(self):
        from unittest.mock import patch
        from scripts.run_manuscript_corrected_3moments import main
        with patch('sys.argv',['run_manuscript_corrected_3moments.py','--output','unused']), \
             patch('scripts.run_full_fading_model.main',return_value=0) as target:
            self.assertEqual(main(),0)
            target.assert_called_once()
        with patch('sys.argv',['runner','--scientific-model=manuscript_corrected_3moments']), \
             patch('scripts.run_manuscript_corrected_3moments.legacy_main',return_value=0) as legacy:
            self.assertEqual(main(),0)
            legacy.assert_called_once()


if __name__=='__main__': unittest.main()
