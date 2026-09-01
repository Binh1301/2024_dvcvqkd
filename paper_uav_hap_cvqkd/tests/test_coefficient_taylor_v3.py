"""Synthetic tests for coefficient-preserving C4 Taylor congruence."""

from __future__ import annotations

from fractions import Fraction
import unittest

try:
    from flint import acb, arb, ctx
except ImportError:  # certification dependencies remain isolated from production
    acb = arb = ctx = None


def _hex(values):
    return [float(value).hex() for value in values]


def _parameter(shape, values):
    return {"shape": list(shape), "float64_hex": _hex(values)}


def _synthetic_payload():
    start = {
        "ps_network.network.0.weight": _parameter([2, 2], [-1, 0, 0, 0]),
        "ps_network.network.0.bias": _parameter([2], [0, 1]),
        "ps_network.network.2.weight": _parameter([2, 2], [1, 0, -1, 0]),
        "ps_network.network.2.bias": _parameter([2], [0, 0]),
        "va_network.network.0.weight": _parameter([1, 2], [0, 0]),
        "va_network.network.0.bias": _parameter([1], [1]),
        "va_network.network.2.weight": _parameter([1, 1], [0.25]),
        "va_network.network.2.bias": _parameter([1], [0]),
        "gs_model.raw_coordinates": _parameter([2, 2], [1, 0, 0, 1]),
    }
    end = {
        name: {"shape": list(row["shape"]), "float64_hex": list(row["float64_hex"])}
        for name, row in start.items()
    }
    end["ps_network.network.0.weight"] = _parameter([2, 2], [1, 0, 0, 0])
    end["gs_model.raw_coordinates"] = _parameter([2, 2], [1, 0.25, -0.25, 1])
    state = {"channel_features_float64_hex": _hex([1, 0])}
    return start, end, state


def _constant_model(matrix):
    from src.validation.coefficient_taylor_v3 import HermitianTaylorModel

    size = len(matrix)
    zero = [[acb(0) for _ in range(size)] for _ in range(size)]
    return HermitianTaylorModel(
        left=Fraction(0), right=Fraction(1), center=Fraction(1, 2), order=2,
        coefficients=(matrix, zero, zero), remainder_coefficient=zero,
    )


@unittest.skipIf(arb is None, "python-flint is isolated from the production environment")
class CoefficientTaylorV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctx.prec = 256

    def _path(self):
        from src.validation.validated_scalar_taylor_v2 import TaylorTransmitterPath

        start, end, state = _synthetic_payload()
        return TaylorTransmitterPath(start, end, state, float(0.1).hex(), float(1.5).hex())

    def test_four_c4_models_preserve_hermitian_coefficients(self):
        from src.validation.coefficient_taylor_v3 import build_c4_sector_taylor_models

        models = build_c4_sector_taylor_models(
            self._path(), Fraction(0), Fraction(1, 2), order=2
        )
        self.assertEqual(len(models), 4)
        for model in models:
            self.assertEqual(model.dimension, 2)
            for matrix in (*model.coefficients, model.remainder_coefficient):
                for row in range(model.dimension):
                    self.assertTrue(matrix[row][row].imag.is_zero())
                    for column in range(model.dimension):
                        self.assertTrue(
                            (matrix[row][column] - matrix[column][row].conjugate()).contains(0)
                        )

    def test_cell_enclosure_contains_direct_point_sector_values(self):
        from src.validation.coefficient_taylor_v3 import (
            _c4_sector_jets,
            build_c4_sector_taylor_models,
            evaluate_taylor_model_enclosure,
        )
        from src.validation.rigorous_flint_support import exact_arb_from_fraction
        from src.validation.rigorous_shifted_inertia import canonicalize_hermitian
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet

        path = self._path()
        left, right = Fraction(0), Fraction(1, 2)
        models = build_c4_sector_taylor_models(path, left, right, order=2)
        enclosures = [evaluate_taylor_model_enclosure(model) for model in models]
        for sample in (left, Fraction(1, 8), Fraction(1, 4), Fraction(3, 8), right):
            point_path = NormalizedJet.variable(exact_arb_from_fraction(sample), 3)
            outputs = path.outputs(point_path, midpoint=Fraction(1, 4))
            direct = _c4_sector_jets(outputs)
            for sector, enclosure in zip(direct, enclosures):
                direct_matrix = canonicalize_hermitian([
                    [acb(value.coefficients[0]) for value in row] for row in sector
                ])
                for row in range(2):
                    for column in range(2):
                        self.assertTrue(enclosure[row][column].contains(
                            direct_matrix[row][column]
                        ))

    def test_shifted_congruence_subtracts_tau_q_star_q(self):
        from src.validation.coefficient_taylor_v3 import (
            evaluate_taylor_model_enclosure,
            shifted_rounded_congruence_taylor_model,
        )

        model = _constant_model([[acb(3), acb(0)], [acb(0), acb(4)]])
        transformed = shifted_rounded_congruence_taylor_model(
            model, [[2, 0], [0, 1]], arb(1)
        )
        enclosure = evaluate_taylor_model_enclosure(transformed)
        self.assertTrue(enclosure[0][0].real.contains(8))
        self.assertFalse(enclosure[0][0].real.contains(11))
        self.assertTrue(enclosure[1][1].real.contains(3))

    def test_shift_then_congruence_matches_direct_nonunitary_algebra(self):
        from src.validation.coefficient_taylor_v3 import (
            evaluate_taylor_model_enclosure,
            shifted_rounded_congruence_taylor_model,
        )

        source = [[acb(2), acb(1)], [acb(1), acb(3)]]
        model = _constant_model(source)
        transformed = shifted_rounded_congruence_taylor_model(
            model, [[1, 1], [0, 2]], arb("0.5")
        )
        enclosure = evaluate_taylor_model_enclosure(transformed)
        # Direct exact arithmetic gives Q*(H-tau I)Q =
        # [[1.5, 3.5], [3.5, 15.5]].
        expected = [[arb("1.5"), arb("3.5")], [arb("3.5"), arb("15.5")]]
        for row in range(2):
            for column in range(2):
                self.assertTrue(enclosure[row][column].real.contains(expected[row][column]))
                self.assertTrue(enclosure[row][column].imag.contains(0))

    def test_congruence_before_widening_preserves_a_shared_scalar_cancellation(self):
        from src.validation.coefficient_taylor_v3 import (
            HermitianTaylorModel,
            congruence_taylor_model,
            evaluate_taylor_model_enclosure,
        )
        from src.validation.rigorous_taylor_eigencluster_v2 import (
            exact_congruence_enclosure,
        )

        zero = [[acb(0), acb(0)], [acb(0), acb(0)]]
        slope = [[acb(1), acb(-1)], [acb(-1), acb(1)]]
        model = HermitianTaylorModel(
            left=Fraction(-1), right=Fraction(1), center=Fraction(0), order=1,
            coefficients=(zero, slope), remainder_coefficient=zero,
        )
        q = [[1, 1], [1, -1]]
        coefficient_first = evaluate_taylor_model_enclosure(
            congruence_taylor_model(model, q)
        )
        widened_first = exact_congruence_enclosure(
            evaluate_taylor_model_enclosure(model), q
        )
        # The first transformed coordinate is identically zero.  Independent
        # entry balls cannot see that cancellation after source-space widening.
        self.assertTrue(coefficient_first[0][0].is_zero())
        self.assertGreater(
            float(widened_first[0][0].real.rad()),
            float(coefficient_first[0][0].real.rad()),
        )

    def test_relu_crossing_cell_fails_closed(self):
        from src.validation.coefficient_taylor_v3 import build_c4_sector_taylor_models

        with self.assertRaises(ValueError):
            build_c4_sector_taylor_models(
                self._path(), Fraction(0), Fraction(1), order=2
            )


if __name__ == "__main__":
    unittest.main()
