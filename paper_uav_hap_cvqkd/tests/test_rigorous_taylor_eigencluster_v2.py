"""Synthetic tests for the V2 fixed-basis eigencluster/Schur core."""

from __future__ import annotations

import unittest

try:
    from flint import acb, arb
except ImportError:  # python-flint remains isolated from production
    acb = arb = None


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class RigorousTaylorEigenclusterV2Tests(unittest.TestCase):
    @staticmethod
    def _diagonal(values):
        return [[acb(values[row]) if row == column else acb(0)
                 for column in range(len(values))] for row in range(len(values))]

    def test_complex128_components_are_embedded_as_exact_dyadics(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import exact_acb_from_complex128

        value = exact_acb_from_complex128(complex(0.1, -0.3))
        real_n, real_d = float(0.1).as_integer_ratio()
        imag_n, imag_d = float(-0.3).as_integer_ratio()
        self.assertEqual(value.real, arb(real_n) / arb(real_d))
        self.assertEqual(value.imag, arb(imag_n) / arb(imag_d))

    def test_rounded_basis_nonsingularity_is_certified(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import certify_rounded_basis

        q = [[1 / 2**0.5, 1 / 2**0.5], [1 / 2**0.5, -1 / 2**0.5]]
        result = certify_rounded_basis(q, precision_bits=256)
        self.assertEqual(result["status"], "CERTIFIED_NONSINGULAR")
        self.assertEqual(result["gram_inertia"]["n_positive"], 2)

    def test_singular_rounded_basis_fails_closed(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import certify_rounded_basis

        result = certify_rounded_basis([[1, 1], [1, 1]], precision_bits=256)
        self.assertEqual(result["status"], "UNCERTIFIED_BASIS")

    def test_exact_congruence_preserves_known_inertia(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import (
            certify_clustered_inertia, exact_congruence_enclosure,
        )

        source = self._diagonal([3, -2, 1])
        q = [[1, 1, 0], [1, -1, 0], [0, 0, 2]]
        transformed = exact_congruence_enclosure(source, q)
        result = certify_clustered_inertia(
            transformed, far_indices=[0, 1], cluster_indices=[2], precision_bits=256
        )
        self.assertEqual(result["status"], "CERTIFIED_CLUSTERED_INERTIA")
        self.assertEqual((result["n_positive"], result["n_negative"]), (2, 1))

    def test_cluster_partition_is_deterministic_at_ties(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import deterministic_cluster_partition

        result = deterministic_cluster_partition(
            [-2.0, -1.0, 1.0, 2.0], threshold=0.0, cluster_size=2
        )
        self.assertEqual(result["cluster_indices"], [1, 2])
        self.assertEqual(result["far_indices"], [0, 3])

    def test_cluster_schedule_includes_cap_without_exceeding_it(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import deterministic_cluster_sizes

        self.assertEqual(
            deterministic_cluster_sizes(20, seed_size=3, expansion_step=4, maximum_size=12),
            [3, 7, 11, 12],
        )

    def test_validated_schur_complement_has_zero_containing_residual(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import validated_far_schur_reduction

        matrix = [
            [acb(2), acb(0), acb(1)],
            [acb(0), acb(-3), acb(1)],
            [acb(1), acb(1), acb(2)],
        ]
        result = validated_far_schur_reduction(
            matrix, far_indices=[0, 1], cluster_indices=[2], precision_bits=256
        )
        self.assertEqual(result["status"], "CERTIFIED_SCHUR_REDUCTION")
        self.assertTrue(result["solve"]["all_residual_entries_contain_zero"])
        self.assertTrue(result["solve"]["all_solution_and_residual_entries_finite"])

    def test_exact_zero_far_block_fails_closed(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import validated_far_schur_reduction

        result = validated_far_schur_reduction(
            self._diagonal([0, 1]), far_indices=[0], cluster_indices=[1], precision_bits=256
        )
        self.assertEqual(result["status"], "UNCERTIFIED_FAR_BLOCK")

    def test_exact_zero_reduced_cluster_fails_closed(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import certify_clustered_inertia

        result = certify_clustered_inertia(
            self._diagonal([2, 0]), far_indices=[0], cluster_indices=[1], precision_bits=256
        )
        self.assertEqual(result["status"], "UNCERTIFIED_CLUSTERED_INERTIA")
        self.assertEqual(result["failure_reason"], "REDUCED_CLUSTER_INERTIA_UNCERTIFIED")

    def test_end_to_end_fixed_basis_cluster_certifies_support_count(self) -> None:
        from src.validation.rigorous_taylor_eigencluster_v2 import certify_fixed_basis_eigencluster

        result = certify_fixed_basis_eigencluster(
            self._diagonal([0.2, 0.8, 1.4]),
            rounded_q=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            midpoint_eigenvalues=[0.2, 0.8, 1.4],
            threshold=0.5,
            precision_bits=256,
            seed_size=1,
            expansion_step=1,
            maximum_cluster_size=2,
        )
        self.assertEqual(result["status"], "CERTIFIED_FIXED_BASIS_INERTIA")
        self.assertEqual(result["certified_support_count"], 2)


if __name__ == "__main__":
    unittest.main()
