import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.ibrahim_binary_qkd import classify_attenuation,frame_statistics,binary_effective_approximations


class BinaryQKDTests(unittest.TestCase):
    def classify(self,a,th=.1,cs=1,mode='diagnostic'):
        return classify_attenuation(a,th,cs,mode=mode)

    def test_threshold_equality_and_neighbors(self):
        a=np.array([[[0,np.nextafter(.1,0),.1,np.nextafter(.1,np.inf),1]]])
        r=self.classify(a);np.testing.assert_array_equal(r['binary_blockage'],[[[0,0,1,1,1]]])

    def test_clear_sky_unavailable_even_zero_attenuation(self):
        r=self.classify(np.zeros((2,3,4)),np.nan,0)
        self.assertTrue((r['binary_blockage']==1).all());self.assertFalse(r['qkd_available'].any())
        self.assertTrue((r['classification_status']==1).all())

    def test_unknown_threshold_never_available(self):
        for th in [np.nan,np.inf,-np.inf,0,-1]:
            r=self.classify(np.zeros((2,3,4)),th)
            self.assertTrue((r['binary_blockage']==255).all());self.assertFalse(r['qkd_available'].any())

    def test_unknown_baseline_never_available(self):
        r=self.classify(np.zeros((2,3,4)),.1,255,mode='validated_input')
        self.assertTrue((r['classification_status']==2).all());self.assertFalse(r['resolved_mask'].any())

    def test_invalid_attenuation_is_unknown(self):
        a=np.array([[[0,np.nan,np.inf,-np.inf,-1]]]);r=self.classify(a)
        np.testing.assert_array_equal(r['binary_blockage'],[[[0,255,255,255,255]]])
        np.testing.assert_array_equal(r['qkd_available'],[[[True,False,False,False,False]]])

    def test_arrays_are_not_modified(self):
        a=np.arange(24).reshape(2,3,4)/10;th=np.full((3,4),.1);cs=np.ones((3,4));copies=[x.copy() for x in [a,th,cs]]
        self.classify(a,th,cs)
        for original,copy in zip([a,th,cs],copies):np.testing.assert_array_equal(original,copy)

    def test_nonsquare_axes_and_time_order(self):
        a=np.zeros((3,2,4));a[1,0,3]=1;a[2,1,0]=2;r=self.classify(a)
        self.assertEqual(r['binary_blockage'].shape,(3,2,4))
        self.assertEqual(np.argwhere(r['binary_blockage']==1).tolist(),[[1,0,3],[2,1,0]])

    def test_1000_frames_and_reproducibility(self):
        a=np.linspace(0,1,1000*50*50).reshape(1000,50,50)
        r=self.classify(a);s=self.classify(a)
        np.testing.assert_array_equal(r['binary_blockage'],s['binary_blockage'])
        self.assertEqual(r['binary_blockage'].dtype,np.uint8);self.assertEqual(r['qkd_available'].dtype,np.bool_)
        self.assertTrue(np.isin(r['binary_blockage'],[0,1]).all())

    def test_npz_roundtrip_without_pickle(self):
        r=self.classify(np.array([[[0,.1],[.2,0]]]))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.npz';np.savez_compressed(path,**r)
            with np.load(path,allow_pickle=False) as loaded:
                for name,value in r.items():np.testing.assert_array_equal(loaded[name],value)

    def test_diagnostic_and_official_status_separated(self):
        a=np.zeros((2,3,4));diag=self.classify(a);pending=self.classify(a,np.nan,255,mode='validated_input')
        self.assertTrue((diag['classification_status']==3).all());self.assertTrue((pending['classification_status']==2).all())
        self.assertFalse(pending['qkd_available'].any());self.assertTrue(diag['qkd_available'].all())

    def test_optional_approximations_are_separate_arrays(self):
        b=np.array([[[0,1],[1,0]]],dtype=np.uint8);t=np.full((2,2),.7);r=np.full((2,2),.001)
        result=binary_effective_approximations(b,t,r)
        np.testing.assert_array_equal(result['T_binary_approximation'],[[[.7,0],[0,.7]]])
        self.assertTrue((t==.7).all());self.assertTrue((r==.001).all())

    def test_optional_approximation_rejects_unresolved(self):
        with self.assertRaises(ValueError):binary_effective_approximations(np.full((1,2,2),255),np.ones((2,2)),np.ones((2,2)))

    def test_statistics_exclude_baseline_unavailability(self):
        a=np.array([[[1,1,0,1]]]);r=self.classify(a,.1,[[0,1,1,255]])
        s=frame_statistics(a,r)[0]
        self.assertIsNone(s['blockage_ratio']);self.assertEqual(s['blocked_cells'],2)
        self.assertEqual(s['cloud_induced_blocked_cells'],1)
        self.assertEqual(s['cloud_induced_ratio_given_clear'],.5)
        self.assertEqual(s['blocked_ratio_given_cloud_affected_clear'],1)

    def test_undefined_populations_are_null_not_zero(self):
        a=np.zeros((1,2,2));s=frame_statistics(a,self.classify(a,.1,0))[0]
        self.assertIsNone(s['cloud_induced_ratio_given_clear']);self.assertIsNone(s['blocked_ratio_given_cloud_affected_clear'])
        json.dumps(s,allow_nan=False)

    def test_unresolved_clear_population_not_dropped_silently(self):
        a=np.array([[[1,np.nan]]]);r=self.classify(a);s=frame_statistics(a,r)[0]
        self.assertIsNone(s['cloud_induced_ratio_given_clear']);self.assertEqual(s['unresolved_cells'],1)

    def test_shape_errors(self):
        for a in [np.zeros((2,3)),np.zeros((0,2,3))]:
            with self.assertRaises(ValueError):self.classify(a)
        with self.assertRaises(ValueError):self.classify(np.zeros((2,3,4)),np.zeros((4,3)))

    def test_invalid_baseline_and_mode(self):
        for cs in [np.nan,2,-1]:
            with self.assertRaises(ValueError):self.classify(np.zeros((1,2,2)),.1,cs)
        with self.assertRaises(ValueError):self.classify(np.zeros((1,2,2)),mode='official_fallback')

    def test_spatially_varying_thresholds(self):
        a=np.full((2,2,3),.2);th=np.array([[.1,.2,.3],[.4,.5,.6]])
        np.testing.assert_array_equal(self.classify(a,th)['binary_blockage'][0],[[1,1,0],[0,0,0]])


if __name__=='__main__':unittest.main()
