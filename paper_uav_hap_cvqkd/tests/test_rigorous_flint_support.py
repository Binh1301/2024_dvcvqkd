"""Regression tests for the isolated Arb whole-segment certifier.

These tests skip in the production environment when python-flint is absent.
The pinned certification environment runs them without importing PyTorch.
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import unittest

try:
    from flint import acb, arb, ctx
except ImportError:  # pragma: no cover - exercised by the production environment
    acb = arb = ctx = None


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class RigorousFlintSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.validation.rigorous_flint_support import BallTransmitterPath

        cls.bundle = json.loads(
            (ROOT / "results" / "rigorous_segment_fixture_bundle.json").read_text(encoding="utf-8")
        )
        cls.BallTransmitterPath = BallTransmitterPath

    def _path(self, family: str):
        segment = next(row for row in self.bundle["segments"] if row["family"] == family)
        return self.BallTransmitterPath(
            self.bundle["start_parameters"],
            segment["end_parameters"],
            self.bundle["states"][1],
            self.bundle["v_min_float64_hex"],
            self.bundle["v_max_float64_hex"],
        )

    def _assert_full_segment_contains_endpoints(self, family: str) -> None:
        from src.validation.rigorous_flint_support import exact_arb_from_fraction, fraction_ball

        path = self._path(family)
        interval_q, interval_alpha = path.physical_ensemble(fraction_ball(Fraction(0), Fraction(1)))
        for endpoint in (Fraction(0), Fraction(1)):
            point_q, point_alpha = path.physical_ensemble(exact_arb_from_fraction(endpoint))
            self.assertTrue(all(whole.contains(point) for whole, point in zip(interval_q, point_q)))
            self.assertTrue(all(whole.contains(point) for whole, point in zip(interval_alpha, point_alpha)))

    def test_01_scalar_obvious_no_crossing(self) -> None:
        from src.validation.rigorous_flint_support import certify_affine_scalar_segment

        result = certify_affine_scalar_segment(float(0.8).hex(), float(0.9).hex(), float(0.5).hex())
        self.assertEqual(result["status"], "WHOLE_SEGMENT_SUPPORT_CERTIFIED")

    def test_02_scalar_known_crossing(self) -> None:
        from src.validation.rigorous_flint_support import certify_affine_scalar_segment

        result = certify_affine_scalar_segment(float(0.6).hex(), float(0.4).hex(), float(0.5).hex())
        self.assertEqual(result["status"], "RIGOROUS_ENDPOINT_RANK_CHANGE_CROSSING")

    def test_03_scalar_near_boundary_non_crossing(self) -> None:
        from src.validation.rigorous_flint_support import certify_affine_scalar_segment

        result = certify_affine_scalar_segment(
            float(0.500001).hex(), float(0.500002).hex(), float(0.5).hex()
        )
        self.assertEqual(result["status"], "WHOLE_SEGMENT_SUPPORT_CERTIFIED")

    def test_04_ps_path_interval_includes_endpoints(self) -> None:
        self._assert_full_segment_contains_endpoints("ps")

    def test_05_gs_path_interval_includes_endpoints(self) -> None:
        self._assert_full_segment_contains_endpoints("gs")

    def test_06_va_path_interval_includes_endpoints(self) -> None:
        self._assert_full_segment_contains_endpoints("va")

    def test_07_mixed_path_interval_includes_endpoints(self) -> None:
        self._assert_full_segment_contains_endpoints("mixed")

    def test_08_ambiguous_relu_is_an_enclosure(self) -> None:
        from src.validation.rigorous_flint_support import _relu

        output = _relu(arb(0, 1))
        self.assertTrue(output.contains(0))
        self.assertTrue(output.contains(1))
        self.assertFalse(output.contains(-0.25))

    def test_09_complex_gram_sectors_are_hermitian_enclosures(self) -> None:
        from src.validation.rigorous_flint_support import exact_arb_from_fraction

        sectors = self._path("mixed").sectors(exact_arb_from_fraction(Fraction(1, 2)))
        for sector in sectors:
            for row in range(len(sector)):
                self.assertTrue(sector[row][row].imag.contains(0))
                for column in range(len(sector)):
                    self.assertTrue(sector[row][column].overlaps(sector[column][row].conjugate()))

    def test_10_precision_increase_preserves_validated_eigenvalue_enclosures(self) -> None:
        from src.validation.rigorous_flint_support import validated_eigenvalue_balls

        matrix = [[acb("0.2"), acb("0.01", "0.02")],
                  [acb("0.01", "-0.02"), acb("0.8")]]
        low, _ = validated_eigenvalue_balls(
            matrix, precision_bits=128, algorithms=["vdhoeven_mourrain", "rump"]
        )
        high, _ = validated_eigenvalue_balls(
            matrix, precision_bits=256, algorithms=["vdhoeven_mourrain", "rump"]
        )
        low = sorted(low, key=lambda value: float(value.real.mid()))
        high = sorted(high, key=lambda value: float(value.real.mid()))
        self.assertTrue(all(left.overlaps(right) for left, right in zip(low, high)))

    def test_11_subdivision_depth_consistency(self) -> None:
        from src.validation.rigorous_flint_support import certify_affine_scalar_segment

        shallow = certify_affine_scalar_segment(
            float(0.500001).hex(), float(0.500002).hex(), float(0.5).hex(), maximum_depth=4
        )
        deep = certify_affine_scalar_segment(
            float(0.500001).hex(), float(0.500002).hex(), float(0.5).hex(), maximum_depth=12
        )
        self.assertEqual(shallow["status"], deep["status"])
        self.assertEqual(shallow["status"], "WHOLE_SEGMENT_SUPPORT_CERTIFIED")


if __name__ == "__main__":
    unittest.main()
