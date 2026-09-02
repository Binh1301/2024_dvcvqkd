"""Synthetic tests for deterministic signed sequential Schur reduction."""

from __future__ import annotations

import unittest

try:
    from flint import acb, arb, ctx
except ImportError:  # certification dependencies remain isolated from production
    acb = arb = ctx = None


def _diagonal(values):
    return [[acb(values[row]) if row == column else acb(0)
             for column in range(len(values))] for row in range(len(values))]


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class SequentialSchurV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctx.prec = 256

    def test_signed_partition_is_deterministic_at_ties(self):
        from src.validation.sequential_schur_v3 import deterministic_signed_partition

        result = deterministic_signed_partition(
            [-3.0, -1.0, 1.0, 3.0], threshold=0.0, near_size=2
        )
        self.assertEqual(result["near_indices"], [1, 2])
        self.assertEqual(result["far_positive_indices"], [3])
        self.assertEqual(result["far_negative_indices"], [0])
        self.assertTrue(result["midpoint_labels_are_diagnostic_only"])

    def test_exact_threshold_tie_is_forced_into_residual(self):
        from src.validation.sequential_schur_v3 import deterministic_signed_partition

        result = deterministic_signed_partition(
            [0.0, 0.0, 2.0, -2.0], threshold=0.0, near_size=1
        )
        self.assertEqual(set(result["near_indices"]), {0, 1})
        self.assertEqual(result["actual_near_size"], 2)

    def test_signed_schur_step_accounts_for_all_coupling(self):
        from src.validation.sequential_schur_v3 import validated_signed_schur_step

        matrix = [
            [acb(4), acb(1), acb(2)],
            [acb(1), acb(-3), acb("0.5")],
            [acb(2), acb("0.5"), acb(2)],
        ]
        result = validated_signed_schur_step(
            matrix, block_indices=[0], expected_sign="POSITIVE", precision_bits=256
        )
        self.assertEqual(result["status"], "CERTIFIED_SIGNED_SCHUR_STEP")
        schur = result["schur_complement"]
        # D-E*E/4 = [[-3.25, 0], [0, 1]] exactly.
        self.assertTrue(schur[0][0].real.contains(arb("-3.25")))
        self.assertTrue(schur[0][1].real.contains(0))
        self.assertTrue(schur[1][1].real.contains(1))

    def test_wrong_midpoint_sign_cannot_force_acceptance(self):
        from src.validation.sequential_schur_v3 import validated_signed_schur_step

        result = validated_signed_schur_step(
            _diagonal([-2, 1]),
            block_indices=[0], expected_sign="POSITIVE", precision_bits=256,
        )
        self.assertEqual(result["status"], "UNCERTIFIED_SIGN_BLOCK")
        self.assertEqual(result["failure_reason"], "BLOCK_NOT_CERTIFIED_SIGN_HOMOGENEOUS")

    def test_sequential_reduction_matches_full_point_inertia(self):
        from src.validation.sequential_schur_v3 import sequential_signed_schur_reduction

        matrix = [
            [acb(4), acb("0.5"), acb(1)],
            [acb("0.5"), acb(-3), acb("0.75")],
            [acb(1), acb("0.75"), acb("0.2")],
        ]
        result = sequential_signed_schur_reduction(
            matrix,
            midpoint_eigenvalues=[4.0, -3.0, 0.2],
            threshold=0.0,
            near_size=1,
            block_sizes=[2, 1],
            precision_bits=256,
            maximum_residual_dimension=2,
        )
        self.assertEqual(result["status"], "CERTIFIED_SEQUENTIAL_INERTIA")
        self.assertEqual((result["n_positive"], result["n_negative"]), (2, 1))
        self.assertEqual(result["sequential_certified_positive"], 1)
        self.assertEqual(result["sequential_certified_negative"], 1)
        self.assertTrue(result["all_couplings_accounted_by_schur_updates"])

    def test_uncertified_residual_fails_closed_and_keeps_far_diagnostics(self):
        from src.validation.sequential_schur_v3 import sequential_signed_schur_reduction

        result = sequential_signed_schur_reduction(
            _diagonal([2, -2, 0]),
            midpoint_eigenvalues=[2.0, -2.0, 0.0],
            threshold=0.0,
            near_size=1,
            block_sizes=[1],
            precision_bits=256,
            maximum_residual_dimension=2,
        )
        self.assertEqual(result["status"], "UNCERTIFIED_SEQUENTIAL_INERTIA")
        self.assertIsNone(result["n_positive"])
        self.assertEqual(result["failure_reason"], "RESIDUAL_INERTIA_UNCERTIFIED")
        self.assertEqual(result["residual_original_labels"], [2])
        self.assertEqual(result["unresolved_far_positive_indices"], [])
        self.assertEqual(result["unresolved_far_negative_indices"], [])

    def test_residual_dimension_cap_is_fail_closed(self):
        from src.validation.sequential_schur_v3 import sequential_signed_schur_reduction

        result = sequential_signed_schur_reduction(
            _diagonal([3, 2, -3, -2, 1]),
            midpoint_eigenvalues=[3.0, 2.0, -3.0, -2.0, 1.0],
            threshold=0.0,
            near_size=5,
            block_sizes=[2, 1],
            precision_bits=256,
            maximum_residual_dimension=4,
        )
        self.assertEqual(result["status"], "UNCERTIFIED_SEQUENTIAL_INERTIA")
        self.assertEqual(result["failure_reason"], "RESIDUAL_DIMENSION_LIMIT")
        self.assertEqual(result["n_zero_or_unresolved"], 5)

    def test_invalid_nonfrozen_block_schedule_is_rejected(self):
        from src.validation.sequential_schur_v3 import sequential_signed_schur_reduction

        with self.assertRaises(ValueError):
            sequential_signed_schur_reduction(
                _diagonal([1, -1]), midpoint_eigenvalues=[1.0, -1.0],
                threshold=0.0, near_size=1, block_sizes=[1, 2], precision_bits=256,
            )


if __name__ == "__main__":
    unittest.main()
