"""Scientific checks for cloud generation and common-objective positioning."""
import inspect
import itertools
import json
from pathlib import Path
import time
import unittest
import numpy as np
from scipy.stats import kstest
import new_cloud_model as cloud
import compare_algorithms as algorithms

OUT=Path(__file__).resolve().parent


class ModelTests(unittest.TestCase):
    def test_covariance(self):
        gamma,factor=cloud.covariance();i=np.arange(100)
        np.testing.assert_array_equal(gamma,9*.9**abs(i[:,None]-i[None,:]))
        np.testing.assert_array_equal(gamma,gamma.T)
        np.testing.assert_array_equal(np.diag(gamma),np.full(100,9.))
        self.assertGreater(np.linalg.eigvalsh(gamma).min(),0)
        np.testing.assert_allclose(factor@factor.T,gamma,atol=2e-13,rtol=0)

    def test_threshold_and_no_temporal_state(self):
        self.assertEqual(list(inspect.signature(cloud.latent).parameters),['slots','seed','mission_id'])
        a=cloud.generate(30,20261015,0);b=cloud.generate(30,20261015,0)
        for k in ['G','mu','epsilon','C']:np.testing.assert_array_equal(a[k],b[k])
        self.assertFalse(np.array_equal(a['mu'][:,0],a['mu'][:,1]))
        self.assertEqual(a['C'].dtype,np.dtype(bool));np.testing.assert_array_equal(a['C'],a['G']>0)
        np.testing.assert_array_equal(a['G'],a['mu']+a['epsilon'])
        for p in [.1,.2,.3,.4,.5,.6,.7,.8]:
            self.assertLess(abs(cloud.blockage_probability(cloud.calibrated_threshold(p))-p),1e-12)
        with self.assertRaises(ValueError):cloud.threshold(a['G'],mode='zero',probability=.4)

    def test_dp_bruteforce_common_objective_and_diagonal(self):
        positions=np.array([[0.,0.],[100.,0.],[0.,100.],[100.,100.]])
        distance=algorithms.transition_distances(positions)
        self.assertLess(distance[0,3],150)
        S=np.random.default_rng(193).uniform(0,.001,(4,4));C=np.zeros_like(S,dtype=bool)
        mission=dict(slot_duration_s=20,max_speed_m_per_s=7.5,reference_distance_m=1000)
        for penalty in [0.,9.468026677248516e-6,.001]:
            records,paths=algorithms.compare(S,C,positions,penalty,mission)
            brute=max(float(S[np.array(path),np.arange(4)].mean())-
                penalty*sum(distance[path[n-1],path[n]] for n in range(1,4))/1000
                for path in itertools.product(range(4),repeat=4))
            self.assertAlmostEqual(records[2]['objective_U'],brute,places=15)
            self.assertEqual(records[0]['total_distance_m'],0)
            for path in paths.values():self.assertTrue(np.all(distance[path[:-1],path[1:]]<=150))

    def test_greedy_uses_no_future_cloud_values(self):
        S=np.random.default_rng(92).uniform(0,.001,(4,10));changed=S.copy();changed[:,5:]=100
        positions=np.array([[0.,0.],[100.,0.],[0.,100.],[100.,100.]])
        distance=algorithms.transition_distances(positions);feasible=distance<=150
        a=algorithms.greedy(S,distance,feasible,1e-5,1000)
        b=algorithms.greedy(changed,distance,feasible,1e-5,1000)
        np.testing.assert_array_equal(a[:5],b[:5])
        ties=np.zeros((4,10));np.testing.assert_array_equal(algorithms.greedy(ties,distance,feasible,0,1000),np.zeros(10,dtype=int))


def stochastic_audit():
    config=algorithms.read('experiment_config.json');mc=config['Monte_Carlo'];M=mc['audit_missions'];slots=30
    gamma,_=cloud.covariance();outer=[];outer_g=[];uniform=[];metrics=[];all_g=[];all_c=[]
    horizontal=np.array([j for j in range(100) if j%10!=9]);vertical=np.arange(90)
    for mission_id in range(M):
        a=cloud.generate(slots,mc['audit_seed'],mission_id)
        e,g,mu,C=[a[k] for k in ['epsilon','G','mu','C']]
        outer.append(e@e.T/slots);outer_g.append(g@g.T/slots);uniform.append(mu.reshape(-1));all_g.append(g);all_c.append(C)
        B=(C.astype(float)-.5)/.5
        metrics.append(dict(blockage=float(C.mean()),mean_mu=float(mu.mean()),mu_second=float(np.mean(mu*mu)),
            G_temporal=float(np.mean(g[:,:-1]*g[:,1:])/(9+1/3)),epsilon_temporal=float(np.mean(e[:,:-1]*e[:,1:])/9),
            binary_temporal=float(np.mean(B[:,:-1]*B[:,1:])),
            G_horizontal=float(np.mean(g[horizontal]*g[horizontal+1])/(9+1/3)),
            G_vertical=float(np.mean(g[vertical]*g[vertical+10])/(9+1/3)),
            binary_horizontal=float(np.mean(B[horizontal]*B[horizontal+1])),binary_vertical=float(np.mean(B[vertical]*B[vertical+10]))))
    covariance=[]
    for name,values,target in [('conditional_residual',outer,gamma),('unconditional_mixture',outer_g,gamma+np.eye(100)/3)]:
        values=np.asarray(values);estimate=values.mean(axis=0);se=values.std(axis=0,ddof=1)/np.sqrt(M)
        z=float(np.max(abs(estimate-target)/se));assert z<=6,(name,z)
        covariance.append(dict(kind=name,max_abs_error=float(np.max(abs(estimate-target))),
            max_mission_cluster_standardized_error=z,acceptance='<=6 cluster SE per entry',passed=True))
        np.save(OUT/f'cloud_covariance_{name}_empirical.npy',estimate)
    checks=[]
    targets=dict(blockage=.5,mean_mu=0.,mu_second=1/3,G_temporal=0.,epsilon_temporal=0.,binary_temporal=0.,
        G_horizontal=9*.9/(9+1/3),G_vertical=9*.9**10/(9+1/3))
    for name in metrics[0]:
        stats=algorithms.mean_statistics([r[name] for r in metrics]);target=targets.get(name)
        passed=abs(stats['mean']-target)<=6*stats['se']+1e-12 if target is not None else True
        assert passed,(name,stats,target)
        checks.append(dict(metric=name,theoretical_target=target,**stats,passed=passed,
            interpretation='known-marginal normalized cross-moment' if 'temporal' in name or 'horizontal' in name or 'vertical' in name else 'mission statistic'))
    means=np.concatenate(uniform);D=float(kstest(means,'uniform',args=(-1,2)).statistic)
    bound=float(np.sqrt(np.log(2/1e-6)/(2*len(means))));assert D<=bound and means.min()>=-1 and means.max()<=1
    all_g=np.asarray(all_g);all_c=np.asarray(all_c,dtype=float)
    pearson=[]
    for name,values in [('G',all_g),('binary',all_c)]:
        for direction,a,b in [('horizontal',values[:,horizontal,:],values[:,horizontal+1,:]),
            ('vertical',values[:,vertical,:],values[:,vertical+10,:]),('temporal',values[:,:,:-1],values[:,:,1:])]:
            pearson.append(dict(variable=name,direction=direction,empirical_Pearson=float(np.corrcoef(a.reshape(-1),b.reshape(-1))[0,1])))
    result=dict(status='CURRENTLY_VERIFIED_PASS',result_scope='DIAGNOSTIC_ONLY',audit_missions=M,slots=slots,
        seed=mc['audit_seed'],covariance_checks=covariance,checks=checks,pooled_Pearson_correlations=pearson,
        mean_uniform_KS_D=D,mean_uniform_DKW_bound_alpha_1e_minus6=bound,
        conditional_diagonal=9,unconditional_diagonal=9+1/3,
        mean_resampled_every_position_and_slot=True,previous_state_parameter=False,
        binary_correlations_not_equal_to_Gaussian_correlations=True)
    algorithms.save('cloud_validation.json',result)
    return result


if __name__=='__main__':
    began=time.perf_counter();suite=unittest.defaultTestLoader.loadTestsFromTestCase(ModelTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    audit=stochastic_audit()
    algorithms.save('focused_tests.json',dict(status='CURRENTLY_VERIFIED_PASS',test_count=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),cloud_stochastic_audit=audit['status'],
        elapsed_seconds=time.perf_counter()-began))
    print('Cloud and positioning tests PASS; no QKD/source kernel used.')
