"""Independent A-K regressions for channel-only noise and trusted detection."""
import copy
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import torch
from scipy.integrate import quad
from src import trusted_heterodyne_skr as corrected
from src import fading_effective_skr as previous
from src.binary_cloud_skr import load_sources
from src.manuscript_corrected_3moments import deterministic_moments
from src.manuscript_literal_3moments import LiteralChannel, entropy
from src.manuscript_corrected_mi import receiver_parameters
from scripts.run_fading_effective_binary_cloud import physical_samples
from src.manuscript_corrected_3moments import PhysicalFadingDistribution
from src.cvqkd.mutual_information import deterministic_mutual_information

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/trusted_heterodyne_skr_20261016'


class TrustedHeterodyneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.hashes=json.loads((OUT/'startup_manifest.json').read_text())['protected_hashes']
        cls.settings=json.loads((ROOT/'configs/binary_cloud_skr_demo.json').read_text())
        cls.groups,cls.config,_=load_sources(cls.settings,cls.hashes)
        cls.source=next(x for x in cls.groups['MB'] if (x['nu_raw'],x['V_A'])==(.17,5.046875))
        cls.states=json.loads((ROOT/'results/binary_cloud_skr_20261015/clear_channel_states.json').read_text())
        cls.m=cls.states[44]['moments']

    def row(self,**kw):
        return corrected.evaluate_candidate(self.source,self.m,self.config,self.hashes,**kw)

    def test_A_no_fading(self):
        for t in (.16,.25,.5,1e-14):
            m=corrected.effective_channel(deterministic_moments(t,R=1,xi_det=0,xi_ch=.0186),2.)
            self.assertEqual(m['T_eff'],t)
            self.assertEqual(m['fading_excess_output'],0.)
            self.assertAlmostEqual(m['effective_excess_input'],.0186,places=14)

    def test_B_pure_loss_and_zero_limit(self):
        for t in (.25,1e-10,0.):
            m=corrected.effective_channel(deterministic_moments(t,R=1,xi_det=0,xi_ch=0),2.)
            self.assertEqual(m['W_pre'],1+2*t)
            self.assertEqual(m['N_eff'],0.)
        self.assertEqual(m['W_pre'],1.)
        self.assertIsNone(m['xi_eff'])

    def test_C_moment_identity_and_invalid_inputs(self):
        m=corrected.effective_channel(self.m,5.)
        self.assertEqual(m['m_xi'],self.m['mean_eta']*.0186)
        self.assertAlmostEqual(m['T_eff']*m['xi_eff'],m['fading_excess_output']+m['channel_excess_output'],places=14)
        for bad in (dict(self.m,mean_sqrt_eta=1.),dict(self.m,mean_eta=-1.),dict(self.m,physical_probability_mass=.98)):
            with self.assertRaises(ValueError):corrected.effective_channel(bad,2.)
        with self.assertRaises(ValueError):corrected.effective_channel(dict(mean_eta=.5,mean_sqrt_eta=.5,chi_tot=5.),2.)

    def test_C_eta_dependent_noise_and_atom_quadrature(self):
        # P0=.2 plus .8*Uniform[0,1], xi_ch(eta)=.03*eta.
        m1=.8*quad(lambda t:t,0,1)[0];mh=.8*quad(math.sqrt,0,1)[0]
        mxi=.8*quad(lambda t:t*(.03*t),0,1)[0]
        m=corrected.effective_channel(dict(mean_eta=m1,mean_sqrt_eta=mh,mean_eta_xi_channel=mxi),2.)
        self.assertAlmostEqual(m['m_xi'],.008,places=14)
        self.assertAlmostEqual(m['N_eff'],(m1-mh*mh)*2+.008,places=14)

    def test_D_bob_variance_and_example_fixture_only(self):
        m=corrected.effective_channel(self.m,5.046875)
        self.assertEqual(m['W_pre'],1+self.m['mean_eta']*(5.046875+.0186))
        self.assertAlmostEqual(m['W_pre'],1+m['T_eff']*5.046875+m['N_eff'],places=14)
        fixture=dict(mean_eta=2.6407446657e-4,mean_sqrt_eta=math.sqrt(2.4357648533e-4),xi_ch=.0186)
        a=corrected.effective_channel(fixture,.025)
        self.assertAlmostEqual(a['N_eff'],5.4242346092e-6,delta=1e-15)
        self.assertAlmostEqual(a['W_pre'],1.000011513647,delta=5e-13)

    def test_E_detector_independence(self):
        a,b=self.row(),self.row(eta_B=.7,nu_B=.0135)
        for k in ('T_eff','xi_eff','m_xi','W_pre','Z_star','C','w','ensemble_hash'):
            self.assertEqual(a[k],b[k])
        self.assertLess(b['I_AB'],a['I_AB'])
        self.assertGreater(abs(b['chi_BE']-a['chi_BE']),.01)

    def test_F_ideal_heterodyne_regression(self):
        old=previous.evaluate_candidate(self.source,self.m,self.config,self.hashes);new=self.row()
        for k in ('I_AB','chi_BE','K_raw','Z_star','b'):
            self.assertAlmostEqual(old[k],new[k],places=12)
        self.assertAlmostEqual(new['conditional_symplectic_eigenvalues'][0],new['a']-new['Z_star']**2/(new['b']+1),places=13)
        self.assertNotAlmostEqual(new['conditional_symplectic_eigenvalues'][0],math.sqrt(new['a']*(new['a']-new['Z_star']**2/new['b'])),places=5)

    def test_G_appendix_independent_block_algebra(self):
        r=self.row(eta_B=.7,nu_B=.0135);a,b,z=r['a'],r['b'],r['Z_star'];e=.7;n=.0135
        I=np.eye(2);S=np.diag([1.,-1.]);v=1+2*n/(1-e);c=math.sqrt(v*v-1)
        # Analytically expanded A,F,G blocks, independent of implementation's beam splitter.
        afg=np.block([[a*I,-math.sqrt(1-e)*z*S,np.zeros((2,2))],
                      [-math.sqrt(1-e)*z*S,((1-e)*b+e*v)*I,math.sqrt(e)*c*S],
                      [np.zeros((2,2)),math.sqrt(e)*c*S,v*I]])
        cross=np.vstack([math.sqrt(e)*z*S,math.sqrt(e*(1-e))*(v-b)*I,math.sqrt(1-e)*c*S])
        conditional=afg-cross@cross.T/(e*b+(1-e)*v+1)
        np.testing.assert_allclose(conditional,r['conditional_covariance_AFG'],atol=2e-14,rtol=0)
        omega=np.kron(np.eye(3),[[0.,1.],[-1.,0.]])
        values=np.sort(np.abs(np.linalg.eigvals(1j*omega@conditional)))[::2]
        np.testing.assert_allclose(values,r['conditional_symplectic_eigenvalues'],atol=1e-13,rtol=0)
        direct=sum(entropy(max(0.,(v-1)/2)) for v in (r['lambda_1'],r['lambda_2']))-sum(entropy(max(0.,(v-1)/2)) for v in values)
        self.assertAlmostEqual(r['chi_BE'],direct,places=12)
        self.assertLess(r['appendix_purification_spectrum_residual'],1e-13)

    def test_G_unit_efficiency_electronic_limit(self):
        r=self.row(eta_B=1.,nu_B=.0135)
        q=self.row(eta_B=1-1e-8,nu_B=.0135)
        self.assertAlmostEqual(r['chi_BE'],q['chi_BE'],delta=2e-8)
        self.assertTrue(all(math.isfinite(v) for v in r['conditional_eve_symplectic_eigenvalues']))

    def test_H_noise_not_duplicated_and_detector_normalization(self):
        m=corrected.effective_channel(self.m,2.)
        # Wrong old total fields cannot alter a channel-only computation.
        changed=corrected.effective_channel(dict(self.m,mean_eta_xi_total=999.,chi_line=999.,chi_tot=999.),2.)
        self.assertEqual(m,changed)
        r=corrected.receiver(m,.8,.0135)
        self.assertAlmostEqual(r['chi_het'],1.53375,places=14)
        self.assertAlmostEqual(r['chi_line'],1/m['T_eff']-1+m['xi_eff'],places=14)
        self.assertAlmostEqual(2*r['sigma2_complex'],.8*m['T_eff']*(1+r['chi_tot']),places=13)
        self.assertAlmostEqual(r['V_B2']+1,2*r['sigma2_complex']+.8*m['T_eff']*2.,places=13)
        mean,var=receiver_parameters(np.array([.3+.2j]),np.array([m['T_eff']]),R=.8,xi_det=.0135,xi_ch=m['xi_eff'])
        self.assertAlmostEqual(var[0],r['sigma2_complex'],places=14)
        center=math.sqrt(r['detector_gain_squared'])*(.3+.2j)
        norm=quad(lambda x:quad(lambda y:float(corrected.heterodyne_likelihood(center+x+1j*y,.3+.2j,m,.8,.0135)),-12,12,epsabs=1e-10)[0],-12,12,epsabs=1e-10)[0]
        self.assertAlmostEqual(norm,1.,places=10)

    def test_I_monte_carlo_channel_moments(self):
        for j in (0,9,44,90,99):
            state=self.states[j];fading=PhysicalFadingDistribution(LiteralChannel(**state['clear_raw_channel']))
            values=physical_samples(fading,65536,np.random.default_rng(20261020+j))
            for vector,target in ((values,state['moments']['mean_eta']),(np.sqrt(values),state['moments']['mean_sqrt_eta']),(.0186*values,.0186*state['moments']['mean_eta'])):
                blocks=vector.reshape(16,-1).mean(axis=1);se=blocks.std(ddof=1)/4
                self.assertLessEqual(abs(vector.mean()-target),5*se+1e-10)

    def test_J_source_preservation_and_mutation_rejection(self):
        row=self.row()
        for k in ('C','w','ensemble_hash'):self.assertEqual(row[k],self.source[k])
        np.testing.assert_allclose(self.source['ensemble'].computed_va(),self.source['V_A'],rtol=1e-13)
        bad=copy.copy(self.source);bad['w']+=1e-6
        with self.assertRaises(ValueError):corrected.evaluate_candidate(bad,self.m,self.config,self.hashes)
        self.assertEqual([len(self.groups[k]) for k in ('MB','Uniform')],[197,30])

    def test_K_limits_and_zero_short_circuit(self):
        with patch('src.trusted_heterodyne_skr.trusted_holevo',side_effect=AssertionError('No zero-T evaluation')):
            zero=corrected.evaluate_candidate(self.source,deterministic_moments(0,R=1,xi_det=0,xi_ch=0),self.config,self.hashes,eta_B=.7,nu_B=.0135)
        self.assertEqual(zero['K_raw'],0.);self.assertFalse(zero['QKD_expressions_evaluated'])
        weak=min(self.groups['MB'],key=lambda x:x['V_A'])
        for t in (1e-10,1e-14):
            row=corrected.evaluate_candidate(weak,deterministic_moments(t,R=1,xi_det=0,xi_ch=0),self.config,self.hashes,eta_B=.7,nu_B=.0135)
            self.assertTrue(all(math.isfinite(row[k]) for k in ('chi_BE','I_AB','K_raw')))
            slope=.7*t*weak['V_A']/(2*(1+.0135)*math.log(2))
            self.assertAlmostEqual(row['I_AB']/slope,1.,delta=1e-6)
        with self.assertRaises(ValueError):corrected.trusted_holevo(2.,2.,2.)

    def test_nonideal_discrete_full_product_mi_agreement(self):
        row=self.row(eta_B=.7,nu_B=.0135)
        t=torch.tensor([row['MI_detector_gain_squared']],dtype=torch.float64)
        eps=torch.tensor([row['MI_kernel_epsilon']],dtype=torch.float64)
        value=deterministic_mutual_information(self.source['ensemble'],t,eps,quadrature_order=16,implementation='full')
        self.assertAlmostEqual(float(value[0]),row['MI_orders'][1]['I_AB'],places=12)


if __name__=='__main__':unittest.main()
