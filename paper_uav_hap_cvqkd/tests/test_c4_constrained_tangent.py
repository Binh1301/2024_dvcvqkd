import unittest

import mpmath as mp

from scripts.validate_corrected_ap_custom_backward import _fixture_inputs, _generic_ap_row
from src.cvqkd.c4_constrained_tangent import EXPERIMENTAL_DIAGNOSTIC_ONLY, forward_tangent


mp.mp.dps = 80


class C4ConstrainedTangentTests(unittest.TestCase):
    def test_constrained_products_match_explicit_products_on_all_cheap_fixtures(self):
        for name, (p, z, dp, dz) in _fixture_inputs().items():
            result = forward_tangent(
                p,
                z,
                dp,
                dz,
                digits=70,
                instrument_explicit=True,
            )
            comparison = result.diagnostics["constrained_vs_explicit"]
            for quantity in ("B", "dB", "A", "dA", "C", "w", "dC", "dw"):
                self.assertLess(
                    mp.mpf(comparison[quantity]["relative"]),
                    mp.mpf("1e-45"),
                    f"{name}:{quantity}",
                )
            self.assertEqual(result.diagnostics["support"]["rank"], 16)

    def test_sylvester_and_all_constrained_solve_residuals_are_small(self):
        for name, (p, z, dp, dz) in _fixture_inputs().items():
            result = forward_tangent(p, z, dp, dz, digits=70)
            for equation, rows in result.diagnostics["solve_residuals"].items():
                for row in rows:
                    self.assertLess(
                        mp.mpf(row["relative"]),
                        mp.mpf("1e-45"),
                        f"{name}:{equation}",
                    )

    def test_tangent_matches_independent_ap_central_difference(self):
        h = mp.mpf("1e-5")
        for name, (p, z, dp, dz) in _fixture_inputs().items():
            tangent = forward_tangent(p, z, dp, dz, digits=70)
            plus = _generic_ap_row(
                [p[i] + float(h) * dp[i] for i in range(len(p))],
                [z[i] + complex(h) * dz[i] for i in range(len(z))],
                70,
            )
            minus = _generic_ap_row(
                [p[i] - float(h) * dp[i] for i in range(len(p))],
                [z[i] - complex(h) * dz[i] for i in range(len(z))],
                70,
            )
            ap_dC = (mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * h)
            ap_dw = (mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * h)
            for observed, reference, quantity in (
                (tangent.dC, ap_dC, "dC"),
                (tangent.dw, ap_dw, "dw"),
            ):
                error = abs(observed - reference) / max(abs(reference), mp.mpf("1e-40"))
                self.assertLess(error, mp.mpf("1e-8"), f"{name}:{quantity}")

    def test_forward_values_match_corrected_ap_and_api_is_diagnostic_only(self):
        self.assertTrue(EXPERIMENTAL_DIAGNOSTIC_ONLY)
        for name, (p, z, dp, dz) in _fixture_inputs().items():
            result = forward_tangent(p, z, dp, dz, digits=70)
            oracle = _generic_ap_row(p, z, 70)
            self.assertLess(
                abs(result.C - mp.mpf(oracle["C"])),
                mp.mpf("1e-45"),
                name,
            )
            self.assertLess(
                abs(result.w - mp.mpf(oracle["w"])),
                mp.mpf("1e-45"),
                name,
            )
            self.assertEqual(result.diagnostics["marker"], "EXPERIMENTAL_DIAGNOSTIC_ONLY")
            self.assertEqual(result.diagnostics["reverse"], "not_implemented")


if __name__ == "__main__":
    unittest.main()
