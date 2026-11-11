import unittest
from dataclasses import replace
import numpy as np
from scipy.stats import kstest
from src.stochastic_cloud_grf import (GRFConfig,CirculantGRF,CloudGRFSimulator,
                                      checked_eigenvalues,relative_intensity,components,DiagnosticTracker)


class StochasticCloudGRFTests(unittest.TestCase):
    def setUp(self):
        self.c=GRFConfig(nx=8,ny=8,slots=12,guard_m=400,ell_c_m=80)
        self.e=CirculantGRF(self.c)

    def test_positive_embedding_and_exact_kernel(self):
        self.assertGreater(self.e.spectrum_receipt['minimum_eigenvalue'],0)
        self.assertEqual(self.e.spectrum_receipt['clipped_eigenvalues'],0)
        for hx,hy in ((0,0),(40,0),(0,40),(80,120),(200,0)):
            self.assertAlmostEqual(self.e.embedded_covariance(hx,hy),np.exp(-np.hypot(hx,hy)/80),places=14)
        with self.assertRaises(ValueError):checked_eigenvalues(np.array([1.,-.01],complex))
        with self.assertRaises(ValueError):checked_eigenvalues(np.array([1.,-1e-18],complex))

    def test_reproducibility_shapes_finiteness_and_dtype(self):
        a=CloudGRFSimulator(self.c,self.e);b=CloudGRFSimulator(self.c,self.e)
        for k in range(self.c.slots):
            x=a.initial if k==0 else a.step();y=b.initial if k==0 else b.step()
            np.testing.assert_array_equal(x,y)
            self.assertEqual(x.shape,(8,8));self.assertEqual(x.dtype,np.float64)
            self.assertTrue(np.isfinite(x).all())
            intensity=relative_intensity(x,a.theta,self.c)
            self.assertTrue(np.isfinite(intensity).all());self.assertTrue((intensity>=0).all())
        other=CloudGRFSimulator(replace(self.c,seed=1),self.e)
        self.assertFalse(np.array_equal(a.initial,other.initial))
        with self.assertRaises(ValueError):a.step()

    def test_marginal_gaussian_independent_draws(self):
        rng=np.random.default_rng(1501)
        values=np.array([self.e.draw(rng)[3,4] for _ in range(384)])
        for samples,target in ((values,0),(values**2,1),(values**3,0),(values**4,3)):
            self.assertLess(abs(samples.mean()-target),4*samples.std(ddof=1)/np.sqrt(len(values)))
        self.assertGreater(kstest(values,'norm').pvalue,1e-4)

    def test_monte_carlo_spatial_covariance(self):
        rng=np.random.default_rng(241)
        estimates=[]
        for _ in range(160):
            field=self.e.draw(rng)
            estimates.append([np.mean(field*np.roll(field,(iy,ix),axis=(0,1))) for iy,ix in ((0,0),(0,8),(1,0),(2,16))])
        estimates=np.array(estimates)
        for j,(hx,hy) in enumerate(((0,0),(40,0),(0,40),(80,80))):
            v=estimates[:,j]
            self.assertLess(abs(v.mean()-self.e.covariance(hx,hy)),4*v.std(ddof=1)/np.sqrt(len(v)))

    def test_exact_advection_sign_speed_and_no_diffusion(self):
        field=self.e.draw(np.random.default_rng(23))
        first=self.e.sample(field)
        moved=self.e.advect(field,8)
        np.testing.assert_array_equal(self.e.sample(moved)[:,:-1],first[:,1:])
        self.assertEqual(self.e.step_x*self.e.dx/self.c.dx_m,-.125)
        self.assertEqual(self.e.step_x*self.e.dx*8,-40)
        np.testing.assert_array_equal(np.sort(self.e.advect(field,1000).ravel()),np.sort(field.ravel()))
        np.testing.assert_array_equal(self.e.sample(moved),self.e.sample(field,offset_x=40))

    def test_ar_stationarity_and_material_correlation(self):
        c=replace(self.c,tau_c_s=20,slots=9)
        e=CirculantGRF(c);before=[];after=[];corr=[]
        for seed in range(96):
            sim=CloudGRFSimulator(replace(c,seed=seed),e)
            initial=e.sample(sim.field,material_slot=0)
            before.append(np.mean(sim.initial**2))
            for _ in range(8):sim.step()
            final=e.sample(sim.field,material_slot=8)
            after.append(np.mean(e.sample(sim.field)**2))
            corr.append(np.sum(initial*final)/np.sum(initial**2))
        for values,target in ((before,1),(after,1),(np.array(after)-before,0),(corr,c.rho**8)):
            values=np.array(values)
            self.assertLess(abs(values.mean()-target),4*values.std(ddof=1)/np.sqrt(len(values))+1e-12)

    def test_space_time_minus_sign(self):
        expected=self.c.rho**8
        self.assertAlmostEqual(self.e.covariance(-40,0,8),expected)
        self.assertAlmostEqual(self.e.covariance(40,0,8),expected*np.exp(-80/self.c.ell_c_m))
        for h in ((-40,0),(40,0),(0,40)):
            self.assertAlmostEqual(self.e.covariance(*h,8),self.e.embedded_covariance(*h,8),places=14)

    def test_no_reentry_and_positive_control(self):
        e=CirculantGRF(GRFConfig())
        receipt=e.boundary_receipt()
        self.assertEqual(receipt['status'],'CURRENTLY_VERIFIED_PASS')
        marker=np.zeros(e.shape);marker[e.y0+10,e.nx-10]=1
        for k in (0,400,999):
            self.assertEqual(e.sample(e.advect(marker,k)).max(),0)
        inside=np.zeros(e.shape);inside[e.y0,e.x0]=1
        self.assertEqual(e.sample(inside).max(),1)
        # All 1000 source positions are distinct and never modulo-wrap in the crop.
        sources=e.ix[0]-e.step_x*np.arange(1000)
        self.assertEqual(len(np.unique(sources)),1000)
        self.assertGreaterEqual(sources.min(),0);self.assertLess(sources.max(),e.nx)

    def test_intensity_thresholds_are_fixed_and_separate(self):
        a=CloudGRFSimulator(self.c,self.e);theta=a.theta
        self.assertAlmostEqual(theta,.5244005127080407)
        x=np.array([[-1.,theta,theta+2]])
        np.testing.assert_allclose(relative_intensity(x,theta,replace(self.c,A=3,q=2)),[[0,0,12]])
        initial=CloudGRFSimulator(replace(self.c,threshold_mode='initial'),self.e)
        self.assertAlmostEqual((initial.initial>initial.theta).mean(),.3,delta=1/64)
        a.step();self.assertEqual(a.theta,theta)

    def test_track_segments_and_censoring(self):
        c=replace(self.c,vx_m_s=0,slots=5)
        tracker=DiagnosticTracker(c)
        mask=np.zeros((8,8),np.uint8);mask[2:4,2:4]=1
        lab,count=components(mask)
        for k in range(5):tracker.update(lab,k)
        records=tracker.finish()
        self.assertEqual(count,1);self.assertEqual(len(records),1)
        self.assertEqual(records[0]['observed_span_s'],4)
        self.assertTrue(records[0]['left_time_censored']);self.assertTrue(records[0]['right_time_censored'])
        self.assertFalse(records[0]['roi_censored'])

    def test_tracker_split_and_nonperiodic_edges(self):
        c=replace(self.c,vx_m_s=0)
        tracker=DiagnosticTracker(c)
        old=np.zeros((8,8),bool);old[2:5,1:7]=1
        new=old.copy();new[:,3:5]=0
        tracker.update(components(old)[0],0);tracker.update(components(new)[0],1)
        records=tracker.finish()
        self.assertEqual(len(records),3)
        self.assertEqual(records[0]['end_reason'],'merge_split_or_ambiguous')
        edge=np.zeros((8,8),bool);edge[0,0]=edge[-1,-1]=1
        self.assertEqual(components(edge)[1],2)

    def test_invalid_settings_and_sampling(self):
        for kwargs in ({'ell_c_m':0},{'tau_c_s':0},{'A':0},{'q':-1},{'refine_x':1},
                       {'vx_m_s':-3.7},{'slots':True},{'initial_fraction':1},{'seed':-1},
                       {'threshold_mode':'CLWC'},{'threshold_mode':'fixed'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):replace(self.c,**kwargs)
        with self.assertRaises(ValueError):self.e.sample(np.zeros((3,3)))
        with self.assertRaises(ValueError):components(np.array([[.5]]))
        with self.assertRaises(ValueError):relative_intensity(np.array([[np.nan]]),0,self.c)


if __name__=='__main__':unittest.main()
