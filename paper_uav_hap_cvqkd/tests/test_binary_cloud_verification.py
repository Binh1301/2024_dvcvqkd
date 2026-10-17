"""Regression for C/F-order roundoff in otherwise equivalent stationary optima."""
import unittest
import numpy as np
from scripts.verify_binary_cloud_skr_results import stationary_gap


class StationaryVerificationTests(unittest.TestCase):
    def test_two_ulp_symmetric_optimum_is_accepted(self):
        a=.04711277444659672;b=.047112774446596735
        self.assertEqual(stationary_gap(np.array([0,0,0]),np.array([a,b])),b-a)

    def test_genuine_suboptimal_stationary_is_rejected(self):
        with self.assertRaises(ValueError):stationary_gap(np.array([0,0,0]),np.array([.04,.047]))

    def test_nonstationary_path_rejected_even_with_equal_values(self):
        with self.assertRaises(ValueError):stationary_gap(np.array([0,1,0]),np.array([.047,.047]))


if __name__=='__main__':unittest.main()
