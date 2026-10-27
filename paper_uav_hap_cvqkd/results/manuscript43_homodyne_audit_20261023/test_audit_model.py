"""Outcome-independent checks of homodyne normalization, planes and fail-closed guards."""
import copy
import math
import unittest

import mpmath as mp
import numpy as np
from scipy.integrate import quad
import audit_model as a


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = a.legacy.load_catalog(a.read(a.ROOT/'configs/manuscript_mobility.json'))
        cls.mb = next(c for c in cls.catalog if c['nu_raw']==.25 and c['VA']==1.6249995399703647)
        cls.uniform = next(c for c in cls.catalog if c['family']=='Uniform' and 1<=c['VA']<=3)
        cls.moments = dict(M0=1., m1=.11, mh=.3, P0=.01, law='normalized_unit_fixture')

    def test_source_units_and_identity(self):
        for c in [self.mb, self.uniform]:
            p, alpha = a.validate_source(c)
            x=2*alpha.real
            self.assertLess(abs(p@x), 1e-12)
            self.assertAlmostEqual(float(p@(x*x)), c['VA'], delta=2e-12)
            self.assertAlmostEqual(2*float(p@(abs(alpha)**2)), c['VA'], delta=2e-12)

    def test_tampered_source_rejected(self):
        c=copy.deepcopy(self.mb);c['C']+=.01
        with self.assertRaises(ValueError):a.validate_source(c)
        c=copy.deepcopy(self.mb);c['alpha']*=2
        with self.assertRaises(ValueError):a.validate_source(c)

    def test_centered_MB_mapping(self):
        for c in [self.mb,self.uniform]:
            p,alpha=a.validate_source(c);raw=np.arange(16)-7.5
            q=np.exp(-c['nu_raw']*raw**2);q/=q.sum()
            _,px=a.marginal(p,alpha)
            self.assertLess(float(max(abs(px-q))),2e-14)
            self.assertAlmostEqual(c['nu_raw']*42.5, c['nu_raw']*float(np.mean(raw[:,None]**2+raw[None,:]**2)))

    def test_each_conditional_PDF_normalized(self):
        for c in [self.mb,self.uniform]:
            p,alpha=a.validate_source(c);e=a.effective(self.moments,c['VA'],.8,.0135)
            for x in np.unique(2*alpha.real):
                mean=math.sqrt(e['T_quantum'])*x
                mass,error=quad(lambda y:a.conditional_pdf(y,mean,e['sigma2_output']),-math.inf,math.inf,epsabs=1e-12,epsrel=1e-12)
                self.assertAlmostEqual(mass,1.,delta=2e-10)
                self.assertLess(error,2e-10)
        with self.assertRaises(ValueError):a.conditional_pdf(0.,1j,1.)

    def test_256_symbols_equal_16_levels(self):
        for c in [self.mb,self.uniform]:
            p,alpha=a.validate_source(c)
            i=a.homodyne_mi(p,alpha,.3,1.02)
            self.assertAlmostEqual(i,a.homodyne_mi(p,alpha,.3,1.02,grouped=False),delta=2e-12)

    def test_real_MI_bounds_and_X_P_symmetry(self):
        for c in [self.mb,self.uniform]:
            p,alpha=a.validate_source(c);i=a.homodyne_mi(p,alpha,.3,1.02)
            self.assertGreaterEqual(i,0.)
            _,px=a.marginal(p,alpha);entropy=-float(px@np.log2(px))
            self.assertLessEqual(i,entropy+2e-12)
            self.assertLessEqual(i,4.+2e-12)
            self.assertLessEqual(i,.5*math.log2(1+.3*c['VA']/1.02)+2e-10)
            self.assertAlmostEqual(i,a.homodyne_mi(p,alpha,.3,1.02,axis='P'),delta=2e-12)

    def test_zero_and_low_signal_limits(self):
        p,alpha=a.validate_source(self.mb)
        self.assertAlmostEqual(a.homodyne_mi(p,alpha,0.,1.01),0.,delta=2e-12)
        self.assertLess(abs(a.homodyne_mi(p,alpha,1e-12,1.01)),2e-10)

    def test_equal_16_level_entropy_ceiling(self):
        # MI-only high-SNR fixture; no new source moments or security evaluation.
        x=np.arange(16)-7.5;alpha=(20*x).astype(complex);p=np.full(16,1/16)
        self.assertAlmostEqual(a.homodyne_mi(p,alpha,1.,1.),4.,delta=2e-10)

    def test_independent_output_integration(self):
        for c in [self.mb,self.uniform]:
            p,alpha=a.validate_source(c);other,error=a.independent_mi(p,alpha,.3,1.02)
            self.assertAlmostEqual(a.homodyne_mi(p,alpha,.3,1.02,order=128),other,delta=2e-10)
            self.assertLess(error,2e-10)

    def test_invertible_classical_rescaling(self):
        p,alpha=a.validate_source(self.mb);i=a.homodyne_mi(p,alpha,.3,1.02)
        for scale in [.37,-2.,1/math.sqrt(.8)]:
            self.assertAlmostEqual(i,a.homodyne_mi(p,alpha,.3,1.02,scale=scale),delta=2e-12)

    def test_noise_reference_planes_and_no_double_count(self):
        e=a.effective(self.moments,self.mb['VA'],.8,.005)
        expected=.8*((.11-.09)*self.mb['VA']+.11*.0186)+.005
        self.assertAlmostEqual(e['N_post'],expected,delta=1e-15)
        self.assertAlmostEqual(e['T_quantum'],.8*.09,delta=1e-15)
        self.assertAlmostEqual(e['sigma2_rescaled'],1/.8+(.11-.09)*self.mb['VA']+.11*.0186+.005/.8,delta=1e-15)
        self.assertEqual(e['vacuum_output'],1.)
        self.assertAlmostEqual(e['b'],1+e['T_quantum']*self.mb['VA']+expected,delta=1e-15)

    def test_xi_conventions_and_outage_extension(self):
        self.assertEqual(a.xi_detector(.8,.0135,'A_epsilon_over_eta'),.0135/.8)
        self.assertEqual(a.xi_detector(.8,.0135,'B_chi_hom'),(1-.8+.0135)/.8)
        with self.assertRaises(ValueError):a.xi_detector(.8,.0135,'independent_explicit')
        full=a.literal_noise(self.moments,self.mb['VA'],.8,.0135,'A_epsilon_over_eta')
        active=a.literal_noise(self.moments,self.mb['VA'],.8,.0135,'A_epsilon_over_eta',outage='active_only')
        self.assertAlmostEqual(full['third_noise_moment']-active['third_noise_moment'],self.moments['P0']*.0135/.8,delta=1e-15)

    def test_invalid_mass_and_moments_fail_closed(self):
        for changes in [dict(M0=.98),dict(mh=.5),dict(m1=1.1)]:
            with self.assertRaises(ValueError):a.effective({**self.moments,**changes},self.mb['VA'],.8,.005)
        for eta,epsilon in [(0.,.005),(1.1,.005),(.8,-.01)]:
            with self.assertRaises(ValueError):a.effective(self.moments,self.mb['VA'],eta,epsilon)

    def test_literal_complex_mean_failure_visible(self):
        r=a.evaluate_literal(self.mb,self.moments,.8,.005,'A_epsilon_over_eta')
        self.assertEqual(r['status'],'FAILED_COMPLEX_MEAN_IN_REAL_PDF')
        self.assertIsNone(r['K_raw'])
        self.assertLess(r['maximum_printed_conditional_mass'],1.)

    def test_literal_real_projection_is_distinct_variant(self):
        literal=a.evaluate_literal(self.mb,self.moments,.8,.005,'A_epsilon_over_eta',real_projection=True)
        physical=a.evaluate_physical(self.mb,self.moments,.8,.005)
        self.assertAlmostEqual(literal['quantum_T'],physical['eta_f'],delta=1e-15)
        self.assertNotEqual(literal['quantum_T'],physical['T_quantum'])
        self.assertAlmostEqual(physical['sigma2_rescaled']-literal['sigma2'],1/.8-1,delta=1e-14)
        self.assertFalse(literal['security_valid'])

    def test_quantum_covariance_and_untrusted_loss(self):
        r=a.evaluate_physical(self.mb,self.moments,.8,.005)
        gamma=np.array([[r['a'],0,r['Z_worst'],0],[0,r['a'],0,-r['Z_worst']],
                        [r['Z_worst'],0,r['b'],0],[0,-r['Z_worst'],0,r['b']]])
        omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
        self.assertGreaterEqual(float(np.linalg.eigvalsh(gamma+1j*omega).min()),-1e-11)
        spectrum=np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
        self.assertLess(float(max(abs(spectrum-np.sort([r['nu_1'],r['nu_2']])))),1e-10)
        self.assertAlmostEqual(r['nu_3'],math.sqrt(r['a']*(r['a']-r['Z_worst']**2/r['b'])),delta=1e-13)
        self.assertAlmostEqual(r['I_AB'],r['I_AB_rescaled'],delta=2e-12)
        self.assertAlmostEqual(r['K_raw'],.95*r['I_AB']-r['chi_BE'],delta=1e-13)

    def test_low_transmittance_security_stability(self):
        for t in [1e-12,1e-8,.1]:
            moments=dict(M0=1.,m1=t,mh=math.sqrt(t),P0=0.,law='deterministic_delta')
            r=a.evaluate_physical(self.mb,moments,.95,.005)
            self.assertTrue(math.isfinite(r['chi_BE']) and r['chi_BE']>=0)
            self.assertGreaterEqual(min(r[k] for k in ['nu_1','nu_2','nu_3']),1.)
            self.assertFalse(r['security_valid'])

    def test_original_PDF_factory_and_independent_moments(self):
        import run_audit as runner
        p=(20.,1.,30.,233.,15.61,1.,.8,.0135,.92,.08)
        raw=a.raw_pdf_moments(runner.raw_channel(p))
        self.assertLess(max(abs(r['residual']) for r in raw['direct'].values()),2e-10)
        self.assertTrue(raw['normalized_within_tolerance'])
        passive_geometry,_=runner.adapter().optical(.08,233.,15.61,1.,30.)
        with self.assertRaises(ValueError):a.raw_pdf_moments(passive_geometry)


if __name__=='__main__':unittest.main()
