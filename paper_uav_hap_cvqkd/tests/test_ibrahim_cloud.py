import unittest
from dataclasses import replace
import numpy as np
from src.ibrahim_cloud import (CloudConfig, CloudSimulator, advect_periodic,
                                blur_noise, coverage_threshold, motion_diagnostic)


class IbrahimCloudTests(unittest.TestCase):
    def setUp(self):
        self.c = CloudConfig(p=.002, P=.05)

    def test_shapes_binary_and_reproducibility(self):
        a, b = CloudSimulator(self.c), CloudSimulator(self.c)
        for _ in range(12):
            fa, fb = a.step(), b.step()
            for name in ("raw_noise", "mask", "blurred_noise", "intensity"):
                x, y = getattr(fa, name), getattr(fb, name)
                self.assertEqual(x.shape, (50, 50))
                np.testing.assert_array_equal(x, y)
                self.assertTrue(np.isfinite(x).all())
            self.assertTrue(set(np.unique(fa.mask)).issubset({0, 1}))
        other = CloudSimulator(replace(self.c, seed=self.c.seed + 1))
        self.assertFalse(np.array_equal(a.reference_field, other.reference_field))

    def test_multiscale_knots_and_initial_expression(self):
        sim = CloudSimulator(self.c)
        rng = np.random.Generator(np.random.PCG64(self.c.seed))
        fine = rng.standard_normal((50, 50))
        coarse = rng.standard_normal((10, 10))
        np.testing.assert_array_equal(sim.initial_fine, fine)
        np.testing.assert_array_equal(sim.initial_coarse[::5, ::5], coarse)
        np.testing.assert_array_equal(sim.frame().raw_noise, fine + sim.initial_coarse)
        # Interpolate across the periodic coarse seam rather than clamp the last knot.
        self.assertAlmostEqual(sim.initial_coarse[0, 49], .2 * coarse[0, 9] + .8 * coarse[0, 0])

    def test_left_fractional_displacement(self):
        field = np.zeros((50, 50)); field[25, 25] = 1
        moved = advect_periodic(field, vx_m_s=-5, vy_m_s=0, dt_s=1, dx_m=40, dy_m=40)
        self.assertEqual(moved[25, 24], .125)
        self.assertEqual(moved[25, 25], .875)
        self.assertEqual(moved[25, 26], 0)
        self.assertAlmostEqual(moved.sum(), 1)
        audit = motion_diagnostic(self.c)
        self.assertEqual(audit["status"], "CURRENTLY_VERIFIED_PASS")
        self.assertAlmostEqual(audit["measured_x_displacement_after_8s_m"], -40)

    def test_integer_periodic_wrapping_and_y_convention(self):
        field = np.arange(2500.).reshape(50, 50)
        moved = advect_periodic(field, vx_m_s=-40, vy_m_s=40, dt_s=1, dx_m=40, dy_m=40)
        np.testing.assert_array_equal(moved, np.roll(field, (1, -1), axis=(0, 1)))
        full = advect_periodic(field, vx_m_s=-5, vy_m_s=0, dt_s=400, dx_m=40, dy_m=40)
        np.testing.assert_array_equal(full, field)
        seam = np.zeros((50, 50)); seam[2, 0] = 1
        wrapped = advect_periodic(seam, vx_m_s=-5, vy_m_s=0, dt_s=1, dx_m=40, dy_m=40)
        self.assertEqual(wrapped[2, 49], .125)
        self.assertEqual(wrapped[2, 0], .875)

    def test_exact_update_expression_separate_p_and_P(self):
        c = replace(self.c, p=.23, P=.17)
        sim = CloudSimulator(c)
        rng = np.random.Generator(np.random.PCG64(c.seed))
        rng.standard_normal((50, 50)); rng.standard_normal((10, 10))
        from src.ibrahim_cloud import multiscale_noise
        fine, coarse = multiscale_noise(rng, c)
        old = sim.frame().raw_noise
        moved = advect_periodic(old, vx_m_s=-5, vy_m_s=0, dt_s=1, dx_m=40, dy_m=40)
        np.testing.assert_array_equal(sim.step().raw_noise, (1-c.p)*moved+c.P*fine+c.P*coarse)

    def test_noise_strength_and_shape_evolution(self):
        old = CloudSimulator(self.c).frame().raw_noise
        def next_field(strength):
            return CloudSimulator(replace(self.c, p=0, P=strength)).step().raw_noise
        zero, weak, strong = [next_field(p) for p in (0, .01, .1)]
        expected = advect_periodic(old, vx_m_s=-5, vy_m_s=0, dt_s=1, dx_m=40, dy_m=40)
        np.testing.assert_array_equal(zero, expected)
        self.assertGreater(np.linalg.norm(weak-zero), 0)
        np.testing.assert_allclose(strong-zero, 10*(weak-zero), atol=1e-14)

    def test_fixed_quantile_coverage_and_extremes(self):
        for target in (0., .1, .3, .8, 1.):
            sim = CloudSimulator(replace(self.c, target_coverage=target))
            self.assertAlmostEqual(sim.frame().mask.mean(), target, delta=1/2500)
            gamma = sim.gamma
            for _ in range(20):
                frame = sim.step()
                self.assertEqual(sim.gamma, gamma)
                np.testing.assert_array_equal(frame.mask, frame.raw_noise > gamma)
        reference = np.arange(2500.).reshape(50, 50)
        self.assertEqual(coverage_threshold(reference, .3), np.quantile(reference, .7))
        fixed = CloudSimulator(replace(self.c, threshold_mode="fixed", gamma=.7))
        self.assertEqual(fixed.gamma, .7)

    def test_blur_normalization_do_not_modify_mask_or_recurrence(self):
        a = CloudSimulator(self.c)
        b = CloudSimulator(replace(self.c, blur_sigma_cells=2, normalization="none"))
        for _ in range(3):
            fa, fb = a.step(), b.step()
            np.testing.assert_array_equal(fa.raw_noise, fb.raw_noise)
            np.testing.assert_array_equal(fa.mask, fb.mask)
            np.testing.assert_array_equal(fb.intensity, fb.blurred_noise)
            np.testing.assert_array_equal(fa.mask, fa.raw_noise > a.gamma)
            lo, hi = a.normalization_bounds
            np.testing.assert_allclose(fa.intensity, np.clip((fa.blurred_noise-lo)/(hi-lo), 0, 1))
            self.assertFalse(np.shares_memory(fa.mask, fa.intensity))
        np.testing.assert_allclose(blur_noise(np.ones((50, 50)), 1, 4), 1, atol=1e-15)
        impulse = np.zeros((50, 50)); impulse[0, 0] = 1
        self.assertAlmostEqual(blur_noise(impulse, 1, 4).sum(), 1)

    def test_snapshots_are_immutable_and_independent(self):
        sim = CloudSimulator(self.c)
        frame = sim.frame(); saved = frame.raw_noise.copy()
        with self.assertRaises(ValueError):
            frame.raw_noise[0, 0] = 3
        sim.step()
        np.testing.assert_array_equal(frame.raw_noise, saved)

    def test_invalid_settings(self):
        for kwargs in ({"u": 3}, {"nx": True}, {"seed": -1}, {"p": -1}, {"P": -1},
                       {"dt_s": 0}, {"width_m": 0}, {"duration_s": 1.5}, {"target_coverage": 2},
                       {"vx_m_s": float("nan")}, {"normalization": "clwc"},
                       {"threshold_mode": "per_slot_quantile"}, {"threshold_mode": "fixed"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.c, **kwargs)
        with self.assertRaises(ValueError):
            CloudSimulator(self.c, initial_field=np.zeros((2, 2)))


if __name__ == "__main__":
    unittest.main()
