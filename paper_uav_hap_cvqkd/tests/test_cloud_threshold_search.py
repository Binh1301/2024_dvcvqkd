import unittest
import numpy as np
from src.cloud_threshold_search import attenuate_realizations,attenuate_moments,search_raw_threshold


class SearchTests(unittest.TestCase):
    def test_bracket_and_raw_negatives(self):
        r=search_raw_threshold(lambda a:2.123456-a)
        lo,hi=r['critical_interval_db']
        self.assertLess(lo,2.123456);self.assertGreaterEqual(hi,2.123456)
        self.assertLess(hi-lo,.01);self.assertTrue(any(p['K_raw']<0 for p in r['samples']))
        self.assertFalse(r['threshold_outage_rule_certified'])

    def test_no_positive_margin_is_not_a_root_at_zero(self):
        for k in [0,-1]:
            r=search_raw_threshold(lambda a:k-a)
            self.assertEqual(r['status'],'NO_POSITIVE_CLEAR_MARGIN')
            self.assertIsNone(r['critical_interval_db'])

    def test_unbracketed_is_right_censored(self):
        r=search_raw_threshold(lambda a:200-a)
        self.assertEqual(r['status'],'RIGHT_CENSORED');self.assertIsNone(r['critical_interval_db'])

    def test_multiple_crossings_refuse_single_rule(self):
        r=search_raw_threshold(lambda a:-(a-2)*(a-4)*(a-6),upper_db=8)
        self.assertEqual(r['status'],'SAMPLED_NONMONOTONIC')
        self.assertEqual(len(r['positive_to_nonpositive_crossings']),2)
        self.assertIsNone(r['critical_interval_db'])

    def test_numerical_errors_fail_closed(self):
        for f in [lambda a:float('nan'),lambda a:float('inf')]:
            with self.assertRaises(ValueError):search_raw_threshold(f)
        with self.assertRaises(ValueError):search_raw_threshold(lambda a:a,width_db=.01)

    def test_pushforward_moments_and_zero_atom(self):
        x=np.array([0,.2,.4,.8]);original=x.copy();y=attenuate_realizations(x,10)
        m=attenuate_moments(x.mean(),np.sqrt(x).mean(),1.,10)
        self.assertAlmostEqual(m['m1'],y.mean());self.assertAlmostEqual(m['mh'],np.sqrt(y).mean())
        self.assertEqual(m['M0'],1);self.assertEqual(y[0],0)
        np.testing.assert_array_equal(original,x)
        np.testing.assert_allclose(y,x*.1)
        outage=attenuate_moments(0.,0.,1.,100)
        self.assertEqual(outage['m1'],0);self.assertEqual(outage['mh'],0)

    def test_detector_noise_remains_unscaled(self):
        m1,mh,mass,va,xi,det=.23,.47,.9999999999,1.3,.0186,.005
        m=attenuate_moments(m1,mh,mass,10)
        n=(m['m1']-m['mh']**2)*va+xi*m['m1']+det*m['M0']
        expected=.1*((m1-mh**2)*va+xi*m1)+det*mass
        self.assertAlmostEqual(n,expected)
        self.assertGreater(abs(n-.1*((m1-mh**2)*va+xi*m1+det*mass)),.004)

    def test_invalid_samples(self):
        for x in [[-1],[1.1],[np.nan]]:
            with self.assertRaises(ValueError):attenuate_realizations(x,1)
        with self.assertRaises(ValueError):attenuate_realizations([.2],-1)
        with self.assertRaises(ValueError):attenuate_moments(.1,.8,1.,1)
        with self.assertRaises(ValueError):attenuate_moments(.5,-.2,1.,1)


if __name__=='__main__':unittest.main()
