"""Regression tests for validated threshold-shifted Hermitian inertia."""

from __future__ import annotations

import unittest

try:
    from flint import acb, arb
except ImportError:  # production environment intentionally excludes python-flint
    acb = arb = None


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class RigorousShiftedInertiaTests(unittest.TestCase):
    def _certify(self, matrix, bits: int = 256, maximum_seconds=None):
        from src.validation.rigorous_shifted_inertia import verified_block_ldl_inertia

        return verified_block_ldl_inertia(
            matrix, precision_bits=bits, maximum_seconds=maximum_seconds
        )

    @staticmethod
    def _diagonal(values):
        size = len(values)
        return [[acb(values[row]) if row == column else acb(0)
                 for column in range(size)] for row in range(size)]

    def test_repeated_positive_eigenvalues(self) -> None:
        result = self._certify(self._diagonal([2, 2, 2, 2]))
        self.assertEqual((result["n_positive"], result["n_negative"], result["n_zero_or_unresolved"]),
                         (4, 0, 0))

    def test_repeated_negative_eigenvalues(self) -> None:
        result = self._certify(self._diagonal([-3, -3, -3]))
        self.assertEqual((result["n_positive"], result["n_negative"], result["n_zero_or_unresolved"]),
                         (0, 3, 0))

    def test_tight_nonzero_cluster_around_zero(self) -> None:
        tiny = arb((1, -120))
        result = self._certify(self._diagonal([tiny, tiny, -tiny, -tiny]), bits=384)
        self.assertEqual(result["status"], "CERTIFIED_INERTIA")
        self.assertEqual((result["n_positive"], result["n_negative"]), (2, 2))

    def test_exact_zero_fails_closed(self) -> None:
        result = self._certify(self._diagonal([1, 0, -1]))
        self.assertNotEqual(result["status"], "CERTIFIED_INERTIA")
        self.assertGreater(result["n_zero_or_unresolved"], 0)

    def test_one_mode_just_above_candidate_threshold(self) -> None:
        from src.validation.rigorous_shifted_inertia import shift_hermitian

        tau = arb((1, -40))
        delta = arb((1, -100))
        result = self._certify(shift_hermitian(self._diagonal([tau + delta, 2 * tau]), tau), bits=384)
        self.assertEqual((result["status"], result["n_positive"]), ("CERTIFIED_INERTIA", 2))

    def test_one_mode_just_below_candidate_threshold(self) -> None:
        from src.validation.rigorous_shifted_inertia import shift_hermitian

        tau = arb((1, -40))
        delta = arb((1, -100))
        result = self._certify(shift_hermitian(self._diagonal([tau - delta, 2 * tau]), tau), bits=384)
        self.assertEqual((result["status"], result["n_positive"], result["n_negative"]),
                         ("CERTIFIED_INERTIA", 1, 1))

    def test_multiple_modes_straddle_threshold(self) -> None:
        from src.validation.rigorous_shifted_inertia import shift_hermitian

        tau = arb((1, -30))
        delta = arb((1, -70))
        gram = self._diagonal([tau - 2 * delta, tau - delta, tau + delta, tau + 2 * delta])
        result = self._certify(shift_hermitian(gram, tau), bits=384)
        self.assertEqual((result["n_positive"], result["n_negative"]), (2, 2))

    def test_real_exchange_forces_certified_two_by_two_pivot(self) -> None:
        result = self._certify([[acb(0), acb(1)], [acb(1), acb(0)]])
        self.assertEqual((result["n_positive"], result["n_negative"]), (1, 1))
        self.assertEqual(result["pivot_rows"][0]["block_size"], 2)

    def test_complex_exchange_forces_certified_two_by_two_pivot(self) -> None:
        result = self._certify([[acb(0), acb(0, 1)], [acb(0, -1), acb(0)]])
        self.assertEqual((result["n_positive"], result["n_negative"]), (1, 1))
        self.assertEqual(result["pivot_rows"][0]["block_size"], 2)

    def test_constructed_rank_change_has_different_endpoint_inertia(self) -> None:
        left = self._certify(self._diagonal([1, -1]))
        right = self._certify(self._diagonal([1, 1]))
        self.assertEqual(left["n_positive"], 1)
        self.assertEqual(right["n_positive"], 2)

    def test_ill_conditioned_psd_gram_like_matrix(self) -> None:
        delta = arb((1, -80))
        correlation = arb(1) - delta
        gram = [[acb(1), acb(correlation)], [acb(correlation), acb(1)]]
        result = self._certify(gram, bits=384)
        self.assertEqual((result["status"], result["n_positive"], result["n_negative"]),
                         ("CERTIFIED_INERTIA", 2, 0))

    def test_exact_dyadic_congruence_preserves_repeated_cluster_inertia(self) -> None:
        # P* diag(2,2,-1,-1) P with a nonsingular integer P.
        diagonal = [arb(2), arb(2), arb(-1), arb(-1)]
        p = [[1, 1, 0, 0], [1, -1, 0, 0], [0, 0, 1, 1], [0, 0, 1, -1]]
        matrix = [[acb(sum(p[k][row] * diagonal[k] * p[k][column] for k in range(4)))
                   for column in range(4)] for row in range(4)]
        result = self._certify(matrix)
        self.assertEqual((result["n_positive"], result["n_negative"]), (2, 2))

    def test_interval_pivot_containing_zero_fails_closed(self) -> None:
        result = self._certify([[acb(arb(0, 1))]])
        self.assertEqual(result["status"], "UNCERTIFIED_PIVOT")
        self.assertEqual(result["n_zero_or_unresolved"], 1)

    def test_nonhermitian_enclosure_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._certify([[acb(1), acb(1)], [acb(2), acb(1)]])

    def test_resource_limit_fails_closed(self) -> None:
        result = self._certify(self._diagonal([1, -1]), maximum_seconds=0.0)
        self.assertEqual(result["status"], "UNCERTIFIED_RESOURCE_LIMIT")


if __name__ == "__main__":
    unittest.main()
