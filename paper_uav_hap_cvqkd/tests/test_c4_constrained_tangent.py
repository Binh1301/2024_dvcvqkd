import unittest

import mpmath as mp

from scripts.validate_corrected_ap_custom_backward import (
    _fixture_inputs,
    _generic_ap_row,
    _target_directional_inputs,
    _target_structure_record,
)
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

    def test_remaining_target_direction_mappings_preserve_full_support(self):
        structures = {
            family: _target_structure_record(family)
            for family in ("gs_real", "gs_imag", "va")
        }
        for family, structure in structures.items():
            self.assertEqual(structure["prototype_count"], 64, family)
            self.assertTrue(structure["positive_probabilities"], family)
            self.assertEqual(structure["probability_sum"], 1.0, family)
            self.assertEqual(structure["unique_state_count"], 256, family)
            self.assertGreater(structure["directional_z_norm"], 0.0, family)
        self.assertNotEqual(
            structures["gs_real"]["direction_sha256"],
            structures["gs_imag"]["direction_sha256"],
        )
        self.assertNotEqual(
            structures["gs_real"]["direction_sha256"],
            structures["va"]["direction_sha256"],
        )

    def test_va_direction_propagates_only_through_physical_amplitudes(self):
        p, z, dp, dz = _target_directional_inputs("va")
        for probability in dp:
            self.assertAlmostEqual(probability, 0.0, places=15)
        for observed, amplitude in zip(dz, z):
            self.assertAlmostEqual(observed.real, 0.5 * amplitude.real, places=15)
            self.assertAlmostEqual(observed.imag, 0.5 * amplitude.imag, places=15)


if __name__ == "__main__":
    unittest.main()
