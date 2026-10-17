"""Noise-accounting, heterodyne and legacy-preservation regressions."""
import copy
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import torch
from scipy.integrate import quad
from scripts import run_ao_effective_channel_no_fading_noise_reference as legacy
from src.binary_cloud_skr import load_sources,mission_results
from src.manuscript_corrected_3moments import deterministic_moments
from src.fading_effective_skr import effective_channel,evaluate_candidate,evaluate_batch,heterodyne_likelihood
from src.cvqkd.mutual_information import deterministic_mutual_information

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'results/fading_effective_binary_cloud_20261016'


class FadingEffectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.hashes=legacy.read_json(OUTPUT/'startup_manifest.json')['protected_hashes']
        cls.settings=legacy.read_json(ROOT/'configs/binary_cloud_skr_demo.json')
        cls.groups,cls.config,_=load_sources(cls.settings,cls.hashes)
        cls.candidate=next(c for c in cls.groups['MB'] if (c['nu_raw'],c['V_A'])==(.17,5.046875))
        cls.states=legacy.read_json(ROOT/'results/binary_cloud_skr_20261015/clear_channel_states.json')
        cls.moments=cls.states[44]['moments']

    def test_deterministic_limit_and_legacy_result(self):
        for t in (.25,.0625,1e-8):
            m=deterministic_moments(t,R=1.,xi_det=0.,xi_ch=.0186)
            new=evaluate_candidate(self.candidate,m,self.config,self.hashes)
            old=legacy.evaluate_authenticated(self.candidate,m,self.config,self.hashes)
            self.assertEqual(new['fading_variance'],0.);self.assertEqual(new['Delta_fad'],0.)
            for name in ('I_AB','chi_BE','SKR','Z_star','b'):
                self.assertAlmostEqual(new[name],old[name],places=10)

    def test_tagged_delta_uses_exact_identity_despite_sqrt_roundoff(self):
        for t in (.16,.5):
            mapping=effective_channel(deterministic_moments(t,R=1.,xi_det=0.,xi_ch=.0186),2.)
            self.assertEqual(mapping['T_eff'],t);self.assertEqual(mapping['fading_variance'],0.)

    def test_reference_decomposition_signed_and_clipped(self):
        result=evaluate_candidate(self.candidate,self.moments,self.config,self.hashes)
        self.assertLess(result['K_raw'],0.);self.assertEqual(result['K_usable'],0.)
        self.assertEqual(result['SKR'],.95*result['I_AB']-result['chi_BE'])
        self.assertAlmostEqual(result['b'],1+self.moments['mean_eta']*(self.candidate['V_A']+.0186),places=13)
        self.assertGreater(result['Delta_fad'],0.)

    def test_total_noise_counted_once(self):
        m=effective_channel(self.moments,5.)
        self.assertAlmostEqual(m['m_excess'],self.moments['mean_eta']*.0186,places=14)
        self.assertAlmostEqual(m['m_xi_total']-(2-self.moments['mean_eta']),m['m_excess'],places=14)
        self.assertAlmostEqual(m['N_eff'],m['fading_variance']*5+m['m_excess'],places=14)
        self.assertAlmostEqual(1+m['T_eff']*5/2+m['N_eff']/2,(m['b']+1)/2,places=14)
        self.assertGreater(abs((1+m['T_eff']*5+m['m_xi_total'])-m['b']),1.)

    def test_reject_unsupported_detector_and_nonphysical_variance(self):
        for changed in (dict(self.moments,R=.7),dict(self.moments,xi_det=.0135),dict(self.moments,chi_het=0.)):
            with self.assertRaises(ValueError):effective_channel(changed,2.)
        with self.assertRaises(ValueError):effective_channel(dict(self.moments,mean_sqrt_eta=1.),2.)

    def test_zero_transmission_skips_qkd_expressions(self):
        m=deterministic_moments(0.,R=1.,xi_det=0.,xi_ch=.0186)
        with patch('src.fading_effective_skr._holevo_from_source_moments',side_effect=AssertionError('No zero-T security call')):
            result=evaluate_candidate(self.candidate,m,self.config,self.hashes)
        self.assertFalse(result['QKD_expressions_evaluated']);self.assertEqual(result['K_usable'],0.)
        self.assertEqual(result['m_xi_total'],2.);self.assertEqual(result['m_excess'],0.)

    def test_heterodyne_likelihood_normalizes_two_quadratures(self):
        alpha=.3+.2j;t=.2;n=.4;variance=1+n/2;mean=math.sqrt(t)*alpha
        normalization=quad(lambda x: quad(lambda y:float(heterodyne_likelihood(x+1j*y,alpha,t,n)),mean.imag-10,mean.imag+10,epsabs=1e-10)[0],mean.real-10,mean.real+10,epsabs=1e-10)[0]
        self.assertAlmostEqual(normalization,1.,places=10)
        self.assertAlmostEqual(float(heterodyne_likelihood(mean,alpha,t,n)),1/(math.pi*variance),places=14)

    def test_same_ensemble_object_reaches_mi_and_holevo(self):
        from src.fading_effective_skr import _holevo_from_source_moments as security
        with patch('src.fading_effective_skr._holevo_from_source_moments',wraps=security) as h,patch('src.fading_effective_skr.deterministic_mutual_information',wraps=deterministic_mutual_information) as mi:
            evaluate_batch(self.candidate,[self.moments,self.states[0]['moments']],self.config,self.hashes)
        for call in mi.call_args_list:self.assertIs(call.args[0],h.call_args.args[0])

    def test_covariance_physicality_and_heterodyne_conditional(self):
        row=evaluate_candidate(self.candidate,self.moments,self.config,self.hashes)
        matrix=np.asarray(row['Gamma_AB']);omega=np.kron(np.eye(2),[[0,1],[-1,0]])
        self.assertGreaterEqual(np.linalg.eigvalsh(matrix+1j*omega).min(),-1e-10)
        values=np.sort(np.abs(np.linalg.eigvals(1j*omega@matrix)))[::2]
        np.testing.assert_allclose(values,sorted([row['lambda_1'],row['lambda_2']]),atol=1e-12)
        self.assertAlmostEqual(row['lambda_3'],row['a']-row['Z_star']**2/(row['b']+1),places=13)
        self.assertGreater(abs(row['lambda_3']-math.sqrt(row['a']*(row['a']-row['Z_star']**2/row['b']))),.01)

    def test_batch_scalar_and_full_product_quadrature_agree(self):
        ms=[self.states[j]['moments'] for j in (0,44,99)]
        batch=evaluate_batch(self.candidate,ms,self.config,self.hashes)
        for m,row in zip(ms,batch):
            single=evaluate_candidate(self.candidate,m,self.config,self.hashes)
            self.assertAlmostEqual(single['SKR'],row['SKR'],places=12)
        row=batch[1];ens=self.candidate['ensemble'];t=torch.tensor([row['T_eff']],dtype=torch.float64);eps=torch.tensor([row['xi_eff']],dtype=torch.float64)
        full=deterministic_mutual_information(ens,t,eps,quadrature_order=16,implementation='full')
        product=deterministic_mutual_information(ens,t,eps,quadrature_order=16,implementation='product')
        self.assertAlmostEqual(float(full[0]),float(product[0]),places=11)

    def test_exact_source_moments_and_historical_results_preserved(self):
        row=evaluate_candidate(self.candidate,self.moments,self.config,self.hashes)
        self.assertEqual(row['C'],self.candidate['C']);self.assertEqual(row['w'],self.candidate['w'])
        for p in ('src/effective_channel_no_fading_noise.py','src/binary_cloud.py','src/uav_mobility.py','results/binary_cloud_skr_20261015/summary.csv'):
            self.assertEqual(legacy.digest(ROOT/p),self.hashes[p])

    def test_very_small_transmission_remains_finite(self):
        for t in (1e-10,1e-14):
            row=evaluate_candidate(self.candidate,deterministic_moments(t,R=1,xi_det=0,xi_ch=.0186),self.config,self.hashes)
            self.assertTrue(all(math.isfinite(row[k]) for k in ('N_eff','I_AB','chi_BE','SKR')))

    def test_analytic_moments_against_independent_physical_sampler(self):
        from src.manuscript_literal_3moments import LiteralChannel
        from src.manuscript_corrected_3moments import PhysicalFadingDistribution
        from src.manuscript_corrected_mi import _physical_fading_samples
        fading=PhysicalFadingDistribution(LiteralChannel(**self.states[44]['clear_raw_channel']))
        from scripts.run_fading_effective_binary_cloud import physical_samples
        values=physical_samples(fading,65536,np.random.default_rng(20261020))
        vectors=(values,np.sqrt(values),2+(.0186-1)*values)
        targets=(self.moments['mean_eta'],self.moments['mean_sqrt_eta'],self.moments['mean_eta_xi_total'])
        for vector,target in zip(vectors,targets):
            se=float(vector.std(ddof=1)/math.sqrt(len(vector)))
            self.assertLessEqual(abs(float(vector.mean())-target),5*se+1e-10)

    def test_binary_no_cloud_and_all_blocked_limits(self):
        from src.uav_mobility import candidate_grid
        positions=candidate_grid();settings=copy.deepcopy(self.settings)
        winner=dict(K_star_raw=-.01,K_star=0.,nu_raw=.17,V_A=5.,ensemble_hash='fixture',objective_key='fixture')
        for blocked in (False,True):
            with patch('src.fading_effective_skr.evaluate_candidate',side_effect=AssertionError('No slot QKD calls')):
                rows,_=mission_results(settings,positions,[winner]*100,np.full((100,30),blocked,dtype=bool))
            self.assertTrue(all(r['average_skr_bits_per_use']==0 and r['availability']==0 for r in rows))
            self.assertTrue(all(r['improvement_vs_reference_percent'] is None for r in rows))


if __name__=='__main__':unittest.main()
