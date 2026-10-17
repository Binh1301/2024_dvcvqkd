import unittest
import numpy as np
from src.binary_cloud import generate_cloud, spatial_covariance, bernoulli_correlation, correlation_audit, mean_statistics
from src.uav_mobility import candidate_grid


class BinaryCloudTests(unittest.TestCase):
    def test_seed_binary_and_stationary_initialization(self):
        p=candidate_grid()
        first,z=generate_cloud(p,30,.4,250.,.9,return_latent=True)
        second=generate_cloud(p,30,.4,250.,.9)
        self.assertEqual(first.shape,(100,30));self.assertEqual(first.dtype,np.bool_)
        np.testing.assert_array_equal(first,second)
        self.assertFalse(np.array_equal(first,generate_cloud(p,30,.4,250.,.9,realization_id=1)))
        _,z2=generate_cloud(p,30,.7,250.,.9,return_latent=True)
        np.testing.assert_array_equal(z,z2)
        self.assertTrue((first<=generate_cloud(p,30,.7,250.,.9)).all())

    def test_probability_endpoints(self):
        for p in (0.,1.):
            c=generate_cloud([[0,0],[100,0]],3,p,250.,.9)
            self.assertTrue((c==bool(p)).all())
            self.assertIsNone(bernoulli_correlation(p,.5))

    def test_covariance_uses_geographic_distances(self):
        covariance,factor=spatial_covariance([[0,0],[100,0],[0,300]],250)
        self.assertAlmostEqual(covariance[0,1],np.exp(-.4))
        self.assertAlmostEqual(covariance[0,2],np.exp(-1.2))
        np.testing.assert_allclose(factor@factor.T,covariance,atol=1e-14)
        with self.assertRaises(np.linalg.LinAlgError):spatial_covariance([[0,0],[0,0]],250)

    def test_threshold_correlation_integral(self):
        self.assertAlmostEqual(bernoulli_correlation(.4,0.),0.,places=12)
        self.assertAlmostEqual(bernoulli_correlation(.5,.7),2*np.arcsin(.7)/np.pi,places=11)
        self.assertEqual(bernoulli_correlation(.4,1.),1.)
        self.assertLess(bernoulli_correlation(.4,.8),.8)

    def test_cluster_uncertainty_checks_512_independent_missions(self):
        audit=correlation_audit(candidate_grid(),missions=512,slots=64)
        self.assertEqual(audit['status'],'CURRENTLY_VERIFIED_PASS',audit['checks'])
        for check in audit['checks']:self.assertTrue(check['passed'])

    def test_invalid_parameters(self):
        for p,ell,rho in ((-1,1,0),(.4,0,.9),(.4,2,1),(.4,2,-.1),(float('nan'),2,.9)):
            with self.assertRaises(ValueError):generate_cloud([[0,0]],3,p,ell,rho)
        for slots in (0,True,2.5):
            with self.assertRaises(ValueError):generate_cloud([[0,0]],slots,.4,250.,.9)
        with self.assertRaises(ValueError):generate_cloud([[0,0]],3,.4,250.,.9,realization_id=-1)
        with self.assertRaises(ValueError):mean_statistics([1.])


if __name__=='__main__':unittest.main()
