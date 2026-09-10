import unittest

import mpmath as mp

from src.cvqkd.ap_custom_backward import source_moments_vjp


class APSourceMomentBackwardTests(unittest.TestCase):
    def test_small_c4_vjp_returns_finite_forward_and_gradients(self):
        p = [0.20, 0.25, 0.30, 0.25]
        z = [
            mp.mpc("0.35", "0.10"),
            mp.mpc("0.75", "-0.20"),
            mp.mpc("1.10", "0.45"),
            mp.mpc("1.45", "-0.55"),
        ]

        result = source_moments_vjp(p, z, digits=80, upstream_c=1, upstream_w=1)

        self.assertTrue(mp.isfinite(result.c))
        self.assertTrue(mp.isfinite(result.w))
        self.assertEqual(len(result.grad_p), len(p))
        self.assertEqual(len(result.grad_z), len(z))
        self.assertTrue(all(mp.isfinite(value) for value in result.grad_p))
        self.assertTrue(all(mp.isfinite(value.real) and mp.isfinite(value.imag) for value in result.grad_z))
        self.assertGreater(float(result.w), -1e-40)

    def test_combined_vjp_matches_central_difference(self):
        with mp.workdps(80):
            p = [mp.mpf("0.20"), mp.mpf("0.25"), mp.mpf("0.30"), mp.mpf("0.25")]
            z = [
                mp.mpc("0.35", "0.10"),
                mp.mpc("0.75", "-0.20"),
                mp.mpc("1.10", "0.45"),
                mp.mpc("1.45", "-0.55"),
            ]
            dp = [mp.mpf("0.03"), mp.mpf("-0.02"), mp.mpf("0.01"), mp.mpf("-0.01")]
            dz = [mp.mpc("0.01", "-0.02"), mp.mpc("-0.03", "0.01"), mp.mpc("0.02", "0.03"), mp.mpc("-0.01", "-0.02")]
            a = mp.mpf("1.7")
            b = mp.mpf("-0.8")
            h = mp.mpf("1e-20")

            result = source_moments_vjp(p, z, digits=80, upstream_c=a, upstream_w=b)
            plus = source_moments_vjp(
                [p[i] + h * dp[i] for i in range(4)],
                [z[i] + h * dz[i] for i in range(4)],
                digits=80,
                upstream_c=0,
                upstream_w=0,
            )
            minus = source_moments_vjp(
                [p[i] - h * dp[i] for i in range(4)],
                [z[i] - h * dz[i] for i in range(4)],
                digits=80,
                upstream_c=0,
                upstream_w=0,
            )
            finite_difference = (
                a * (plus.c - minus.c) + b * (plus.w - minus.w)
            ) / (2 * h)
            vjp = mp.fsum(
                result.grad_p[i] * dp[i]
                + mp.re(mp.conj(result.grad_z[i]) * dz[i])
                for i in range(4)
            )

            self.assertLess(float(abs(finite_difference - vjp)), 1e-25)


if __name__ == "__main__":
    unittest.main()
