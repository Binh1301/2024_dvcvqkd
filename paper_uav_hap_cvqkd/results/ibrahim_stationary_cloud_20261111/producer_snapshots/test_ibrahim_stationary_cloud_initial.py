import unittest
from dataclasses import replace
import numpy as np
from scipy.signal import resample
from src.ibrahim_stationary_cloud import (StationaryCloudConfig, SpectralDomain,
                                         StationaryCloudSimulator, relative_intensity)


class StationaryCloudTests(unittest.TestCase):
    def setUp(self):
        self.c = StationaryCloudConfig(nx=10, ny=10, slots=12, guard_m=160)

    def test_reproducibility_finite_shapes_and_fixed_threshold(self):
        a, b = StationaryCloudSimulator(self.c), StationaryCloudSimulator(self.c)
        gamma = a.gamma
        for k in range(self.c.slots):
            xa = a.latent() if k == 0 else a.step()
            xb = b.latent() if k == 0 else b.step()
            np.testing.assert_array_equal(xa, xb)
            self.assertEqual(xa.shape, (10, 10))
            self.assertTrue(np.isfinite(xa).all())
            self.assertEqual(a.gamma, gamma)
            self.assertTrue((relative_intensity(xa, self.c) >= 0).all())
        self.assertFalse(np.array_equal(a.initial, StationaryCloudSimulator(replace(self.c, seed=1)).initial))
        with self.assertRaises(ValueError):
            a.step()

    def test_fourier_coarse_interpolation_and_combination(self):
        d = SpectralDomain(self.c)
        rng = np.random.Generator(np.random.PCG64(4))
        combined, fine, coarse = d.draw(rng, components=True)
        control = np.random.Generator(np.random.PCG64(4))
        fine_raw = control.standard_normal(d.shape)
        coarse_raw = control.standard_normal(d.coarse_shape)
        fine_expected = (fine_raw-fine_raw.mean())/np.sqrt(1-1/fine_raw.size)
        coarse_expected = (coarse_raw-coarse_raw.mean())/np.sqrt(1-1/coarse_raw.size)
        up = resample(resample(coarse_expected, d.ny, axis=0), d.nx, axis=1)
        np.testing.assert_allclose(d.to_real(fine), fine_expected, atol=2e-15)
        np.testing.assert_allclose(d.to_real(coarse), up, atol=2e-15)
        np.testing.assert_allclose(d.to_real(coarse)[::self.c.u, ::self.c.u], coarse_expected, atol=2e-15)
        np.testing.assert_allclose(d.to_real(combined), (.35*fine_expected+up)/np.hypot(.35,1), atol=3e-15)
        self.assertAlmostEqual(d.to_real(combined).mean(), 0, places=14)

    def test_target_covariance_and_multiscale_spectra(self):
        d = SpectralDomain(self.c)
        f, g, combined = [d.covariance(s) for s in ("fine", "coarse", "combined")]
        self.assertAlmostEqual(combined[0, 0], 1, places=14)
        self.assertAlmostEqual(f[0, 1], -1/(d.nx*d.ny-1), places=14)
        self.assertGreater(g[0, 1], .8)
        np.testing.assert_allclose(combined, (.35**2*f+g)/(.35**2+1), atol=1e-15)
        rng = np.random.default_rng(16)
        estimates = np.array([d.empirical_covariance(d.draw(rng)) for _ in range(256)])
        for y, x in ((0,0), (0,1), (0,3), (1,2)):
            values = estimates[:,y,x]
            self.assertLess(abs(values.mean()-combined[y,x]), 4*values.std(ddof=1)/16)

    def test_exact_fractional_sign_and_eight_second_shift(self):
        d = SpectralDomain(self.c)
        x = d.draw(np.random.default_rng(3))
        one_step = d.phase[0,1]
        displacement = -np.angle(one_step)/(2*np.pi/d.nx)
        self.assertAlmostEqual(displacement, -.125, places=14)
        self.assertAlmostEqual(displacement*self.c.dx_m, -5, places=12)
        eight = d.to_real(x*d.phase**8)
        np.testing.assert_allclose(eight, np.roll(d.to_real(x), -1, axis=1), atol=5e-15)
        self.assertAlmostEqual(8*displacement*self.c.dx_m, -40, places=12)

    def test_unitary_shift_variance_covariance_and_inverse(self):
        d = SpectralDomain(self.c)
        start = d.draw(np.random.default_rng(5))
        moved = start.copy()
        for _ in range(1000):
            moved *= d.phase
        covariance = d.empirical_covariance(start)
        np.testing.assert_allclose(d.empirical_covariance(moved), covariance, atol=5e-13, rtol=1e-12)
        np.testing.assert_allclose(d.to_real(moved*np.conjugate(d.phase)**1000), d.to_real(start), atol=7e-13)
        dy = d.shift_phase(0, .25)
        np.testing.assert_allclose(d.to_real(start*dy**4), np.roll(d.to_real(start), 1, axis=0), atol=5e-15)

    def test_stationary_ensemble_and_motion_compensated_rho(self):
        c = replace(self.c, tau_c_s=5, slots=4)
        d = SpectralDomain(c)
        first, last, correlation = [], [], []
        for seed in range(160):
            sim = StationaryCloudSimulator(replace(c, seed=seed))
            initial = d.to_real(sim.coefficients)
            for _ in range(3):
                sim.step()
            compensated = d.to_real(sim.coefficients*np.conjugate(d.phase)**3)
            first.append(np.mean(initial**2)); last.append(np.mean(compensated**2))
            correlation.append(np.mean(initial*compensated)/np.mean(initial**2))
        for values, target in ((first,1), (last,1), (np.array(last)-first,0), (correlation,c.rho**3)):
            values = np.asarray(values)
            self.assertLess(abs(values.mean()-target), 4*values.std(ddof=1)/np.sqrt(len(values))+1e-12)

    def test_covariance_invariant_under_fractional_shift(self):
        d = SpectralDomain(self.c)
        # An unchanged power spectrum means A C A*=C, including subpixel shifts.
        np.testing.assert_allclose(abs(d.phase)**2, 1, atol=3e-16)
        self.assertGreater(d.expected_crop_variance(), 0)
        self.assertLess(d.expected_crop_variance(), 1)

    def test_no_reentry_400_and_999_seconds(self):
        d = SpectralDomain(StationaryCloudConfig())
        receipt = d.boundary_receipt()
        self.assertEqual(receipt["status"], "CURRENTLY_VERIFIED_PASS")
        self.assertEqual(d.shape, (105,225))
        self.assertEqual(d.coarse_shape, (21,45))
        by_time = {r["time_s"]:r for r in receipt["backtraces"]}
        self.assertEqual(by_time[400]["x_backtrace_interval_m"], [3000,5000])
        self.assertEqual(by_time[999]["x_backtrace_interval_m"], [5995,7995])
        # Periodic smooth Gaussian packet starts at the synthetic seam, downstream
        # of the crop. Its wrapped image never returns to the crop in this horizon.
        marker = np.exp(-2*np.pi**2*9*(d.fx**2+d.fy**2))
        marker = marker.astype(complex)
        marker /= d.to_real(marker).max()
        for k in (0, 400, 999, 1000):
            self.assertLess(abs(d.crop(d.to_real(marker*d.phase**k))).max(), 1e-10)

    def test_boundary_other_wind_directions(self):
        for vx, vy in ((5,0),(0,-8),(5,7),(-12,-3),(0,0)):
            d = SpectralDomain(replace(self.c,vx_m_s=vx,vy_m_s=vy))
            self.assertEqual(d.boundary_receipt()["status"], "CURRENTLY_VERIFIED_PASS")

    def test_intensity_choices_and_no_latent_mutation(self):
        x = np.array([[-1000.,0,1000.]])
        original = x.copy()
        softplus = relative_intensity(x,self.c)
        self.assertTrue(np.isfinite(softplus).all())
        self.assertAlmostEqual(softplus[0,1], np.log(2))
        positive = relative_intensity(x,replace(self.c,intensity_transform="positive_part"))
        np.testing.assert_array_equal(positive, [[0,0,1000]])
        np.testing.assert_array_equal(x,original)

    def test_invalid_configuration(self):
        for kwargs in ({"u":4},{"u":1},{"tau_c_s":0},{"guard_m":0},{"slots":True},
                       {"seed":-1},{"initial_fraction":1},{"w_f":0,"w_c":0},
                       {"vx_m_s":float('nan')},{"intensity_transform":"CLWC"}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                replace(self.c,**kwargs)


if __name__ == "__main__":
    unittest.main()
