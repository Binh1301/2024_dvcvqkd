"""Tests for guard-band and subdivision semantics of shifted inertia."""

from __future__ import annotations

from fractions import Fraction
import unittest

try:
    from flint import acb, arb
except ImportError:
    acb = arb = None


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class RigorousShiftedInertiaSegmentTests(unittest.TestCase):
    @staticmethod
    def _diagonal(values):
        return [[acb(values[row]) if row == column else acb(0)
                 for column in range(len(values))] for row in range(len(values))]

    def test_equal_guard_band_counts_certify_fixed_inertia(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_sector_guard_band

        result = certify_sector_guard_band(
            self._diagonal([arb("0.2"), arb("0.8")]), arb("0.1"), arb("0.5"),
            precision_bits=256,
        )
        self.assertEqual(result["status"], "CERTIFIED_FIXED_INERTIA")
        self.assertEqual(result["certified_support_count"], 1)

    def test_unequal_guard_band_counts_are_unresolved_not_crossing(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_sector_guard_band

        result = certify_sector_guard_band(
            self._diagonal([arb("0.49"), arb("0.8")]), arb("0.02"), arb("0.5"),
            precision_bits=256,
        )
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertFalse(result["zero_included_proves_crossing"])

    def test_no_crossing_interval_tree_certifies(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_interval_tree

        def evaluator(left, right):
            return {"left": str(left), "right": str(right), "status": "CERTIFIED_FIXED_INERTIA",
                    "certified_support_count": 3, "sector_rows": []}

        result = certify_interval_tree(
            evaluator, start_rank=3, end_rank=3, maximum_depth=4,
            minimum_width=Fraction(1, 16), maximum_nodes=15, maximum_seconds=5,
        )
        self.assertEqual(result["status"], "WHOLE_SEGMENT_FIXED_INERTIA_CERTIFIED")

    def test_endpoint_rank_change_is_a_rigorous_crossing(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_interval_tree

        result = certify_interval_tree(
            lambda left, right: {}, start_rank=2, end_rank=3, maximum_depth=4,
            minimum_width=Fraction(1, 16), maximum_nodes=15, maximum_seconds=5,
        )
        self.assertEqual(result["status"], "RIGOROUS_ENDPOINT_INERTIA_CROSSING")

    def test_unresolved_nodes_subdivide_deterministically_and_fail_closed(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_interval_tree

        def evaluator(left, right):
            return {"left": str(left), "right": str(right), "status": "UNRESOLVED",
                    "certified_support_count": None, "sector_rows": []}

        result = certify_interval_tree(
            evaluator, start_rank=3, end_rank=3, maximum_depth=2,
            minimum_width=Fraction(1, 4), maximum_nodes=15, maximum_seconds=5,
        )
        self.assertEqual(result["status"], "UNCERTIFIED_FAIL_CLOSED")
        self.assertEqual(result["maximum_depth_reached"], 2)
        self.assertGreater(result["unresolved_leaf_count"], 0)

    def test_resource_limit_never_passes(self) -> None:
        from src.validation.rigorous_shifted_inertia_segment import certify_interval_tree

        result = certify_interval_tree(
            lambda left, right: {}, start_rank=1, end_rank=1, maximum_depth=20,
            minimum_width=Fraction(1, 2**20), maximum_nodes=0, maximum_seconds=5,
        )
        self.assertEqual(result["status"], "UNCERTIFIED_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
