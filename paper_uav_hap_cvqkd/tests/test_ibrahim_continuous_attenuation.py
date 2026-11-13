import unittest
import numpy as np

from src.ibrahim_continuous_attenuation import (
    AttenuationScenario, gaussian_to_clwc, visibility_km, kim_exponent,
    specific_attenuation_db_km, path_attenuation_db, transmittance_from_db,
    combine_clear_cloud, layer_intersection, sample_clwc,
    representative_link_attenuation, pooled_pearson,
)


class ContinuousAttenuationTests(unittest.TestCase):
    def test_fixed_positive_part_mapping_and_reproducibility(self):
        rng = np.random.default_rng(20261111)
        g = rng.normal(size=(10, 5, 5))
        original = g.copy()
        l = gaussian_to_clwc(g, .1, .7)
        np.testing.assert_array_equal(l, .1*np.maximum(g-.7, 0))
        np.testing.assert_array_equal(l, gaussian_to_clwc(g, .1, .7))
        np.testing.assert_array_equal(g, original)
        self.assertGreater(len(np.unique(l)), 2)

    def test_visibility_equation7_units(self):
        self.assertAlmostEqual(float(visibility_km(.1, 100)), 1.002/(.1*100)**.6473, places=14)
        self.assertAlmostEqual(float(visibility_km(.001, 100)), 1.002/(.001*100)**.6473, places=13)
        self.assertTrue(np.isposinf(visibility_km(0, 100)))

    def test_all_printed_exponent_branches_and_boundaries(self):
        below6, above6 = np.nextafter(6., 0), np.nextafter(6., np.inf)
        below50, above50 = np.nextafter(50., 0), np.nextafter(50., np.inf)
        v = [1e-12, .5, 1, 2, 5, below6, 6, above6, below50, 50, above50, np.inf]
        expected = [.585*np.cbrt(a) if a < 6 else (1.3 if a <= 50 else 1.6) for a in v]
        np.testing.assert_array_equal(kim_exponent(v), expected)
        # In particular V<.5 does NOT use the unrelated five-branch Kim x=0.
        self.assertGreater(float(kim_exponent(.1)), 0)

    def test_equation5_and_wavelength_nm(self):
        l, n = .2, 150
        v = 1.002/(l*n)**.6473
        x = .585*v**(1/3)
        expected = 3.91/v*(1550/550)**(-x)
        self.assertAlmostEqual(float(specific_attenuation_db_km(l,n)), expected, places=13)
        self.assertAlmostEqual(float(specific_attenuation_db_km(l,n,550)), 3.91/v, places=13)

    def test_continuity_inside_regimes_and_documented_jumps(self):
        def omega_v(v):
            l = (1.002/v)**(1/.6473)/100
            return float(specific_attenuation_db_km(l,100))
        for v in [1., 10., 100.]:
            self.assertAlmostEqual(omega_v(v*(1-1e-9)), omega_v(v*(1+1e-9)), delta=1e-7)
        self.assertGreater(abs(omega_v(6-1e-7)-omega_v(6+1e-7)), .01)
        self.assertGreater(abs(omega_v(50-1e-7)-omega_v(50+1e-7)), .001)

    def test_zero_and_approach_zero_without_numerical_errors(self):
        l = np.array([0.,1e-300,1e-200,1e-100,1e-20,1e-8])
        with np.errstate(all='raise'):
            w = specific_attenuation_db_km(l,100)
            a = path_attenuation_db(w,.5)
            t = transmittance_from_db(a)
        self.assertEqual(w[0], 0)
        self.assertEqual(t[0], 1)
        self.assertTrue(np.all(np.diff(w)>0))
        self.assertTrue(np.isfinite(w).all())
        self.assertLess(w[1],1e-190)

    def test_full_slab_secant_and_thickness_units(self):
        w = np.array([0.,3.,30.])
        np.testing.assert_array_equal(path_attenuation_db(w,.5),w*.5)
        np.testing.assert_allclose(path_attenuation_db(w,.5,60),w,rtol=5e-16)
        np.testing.assert_array_equal(path_attenuation_db(w,0),0*w)

    def test_transmittance_inverse_and_no_clipping(self):
        a = np.array([0.,1.,10.,100.,1000.])
        t = transmittance_from_db(a)
        np.testing.assert_allclose(-10*np.log10(t),a,rtol=1e-14,atol=1e-14)
        np.testing.assert_array_equal(combine_clear_cloud(.8,t),.8*t)
        self.assertEqual(float(combine_clear_cloud(0,1)),0)
        with self.assertRaises(ValueError): transmittance_from_db(4000)
        with self.assertRaises(ValueError): combine_clear_cloud(1e-300,1e-300)

    def test_geometry_intersection_miss_partial_reverse(self):
        g = layer_intersection([0,0,1000],[19000,0,20000],2000,2500)
        self.assertAlmostEqual(g['path_length_km'],.5*np.sqrt(2))
        np.testing.assert_allclose(g['representative_xyz_m'],[1250,0,2250])
        r = layer_intersection([19000,0,20000],[0,0,1000],2000,2500)
        np.testing.assert_allclose(g['representative_xyz_m'],r['representative_xyz_m'])
        self.assertAlmostEqual(g['path_length_km'],r['path_length_km'])
        self.assertFalse(layer_intersection([0,0,3000],[0,0,20000],2000,2500)['intersects'])
        p = layer_intersection([0,0,2250],[0,0,20000],2000,2500)
        self.assertAlmostEqual(p['path_length_km'],.25)

    def test_geometry_horizontal_and_boundary_contact(self):
        self.assertAlmostEqual(layer_intersection([0,0,2200],[1000,0,2200],2000,2500)['path_length_km'],1)
        self.assertFalse(layer_intersection([0,0,2000],[1000,0,2000],2000,2500)['intersects'])
        self.assertFalse(layer_intersection([0,0,1000],[0,0,2000],2000,2500)['intersects'])

    def test_bilinear_cloud_coordinate_and_no_wrap(self):
        x, y = np.array([0.,1.,2.]), np.array([0.,1.,2.])
        l = y[:,None]+2*x[None,:]
        self.assertAlmostEqual(sample_clwc(l,x,y,[.5,1.2]),2.2)
        self.assertEqual(sample_clwc(l,x,y,[2,2]),6)
        with self.assertRaises(ValueError): sample_clwc(l,x,y,[-.01,1])

    def test_link_no_intersection_zero_even_outside_map(self):
        result = representative_link_attenuation(np.ones((2,2)),[0,1],[0,1],
                    [10000,10000,3000],[10000,10000,20000],2000,2500,100)
        self.assertEqual(result['attenuation_db'],0)
        self.assertEqual(result['transmittance'],1)

    def test_link_constant_clwc_and_representative_coordinate(self):
        l = np.full((2,2),.1)
        result = representative_link_attenuation(l,[0,2000],[0,2000],
                  [0,1000,1000],[19000,1000,20000],2000,2500,100)
        expected = float(specific_attenuation_db_km(.1,100))*.5*np.sqrt(2)
        self.assertAlmostEqual(result['attenuation_db'],expected)
        self.assertAlmostEqual(result['geometry']['representative_xyz_m'][0],1250)

    def test_mapping_commutes_with_wind_permutation_without_threshold_mask(self):
        g = np.random.default_rng(42).normal(size=(15,15))
        for f in [lambda z: gaussian_to_clwc(z,.1,.5),
                  lambda z: specific_attenuation_db_km(gaussian_to_clwc(z,.1,.5),100)]:
            np.testing.assert_array_equal(f(np.roll(g,-1,axis=1)),np.roll(f(g),-1,axis=1))

    def test_empirical_correlation_changes_after_nonlinear_mapping(self):
        rng=np.random.default_rng(77)
        a=rng.normal(size=50000);b=.8*a+.6*rng.normal(size=a.size)
        raw=pooled_pearson(a,b)
        mapped=pooled_pearson(gaussian_to_clwc(a,.1,.7),gaussian_to_clwc(b,.1,.7))
        self.assertGreater(raw-mapped,.05)
        self.assertEqual(pooled_pearson(a,a),1)
        with self.assertRaises(ValueError): pooled_pearson(np.ones(3),np.ones(3))

    def test_invalid_parameters_and_nonfinite_rejected(self):
        for v in [-1,np.nan,np.inf]:
            with self.assertRaises(ValueError): specific_attenuation_db_km(v,100)
        for n in [0,-1,np.nan,np.inf]:
            with self.assertRaises(ValueError): visibility_km(.1,n)
        for z in [-1,90,180,np.nan]:
            with self.assertRaises(ValueError): path_attenuation_db(1,.5,z)
        for v in [0,-1,np.nan]:
            with self.assertRaises(ValueError): kim_exponent(v)
        for t in [-1,0,1.1,np.nan]:
            with self.assertRaises(ValueError): combine_clear_cloud(.8,t)
        with self.assertRaises(ValueError): AttenuationScenario('bad',-1,100,.5)
        with self.assertRaises(ValueError): gaussian_to_clwc([1,np.nan],.1,.5)
        with self.assertRaises(ValueError): layer_intersection([0,0,0],[0,0,0],0,1)


if __name__ == '__main__':
    unittest.main()
