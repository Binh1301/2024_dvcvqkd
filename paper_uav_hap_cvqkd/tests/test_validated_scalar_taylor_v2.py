"""Synthetic regressions for the certification-only scalar Taylor V2 core."""

from __future__ import annotations

from fractions import Fraction
import math
import unittest

try:
    from flint import acb, arb, ctx
except ImportError:  # production intentionally omits python-flint
    acb = arb = ctx = None


def _hex(values):
    return [float(value).hex() for value in values]


def _parameter(shape, values):
    return {"shape": list(shape), "float64_hex": _hex(values)}


def _synthetic_payload(*, zero_geometry: bool = False):
    start = {
        "ps_network.network.0.weight": _parameter([2, 2], [-1, 0, 0, 0]),
        "ps_network.network.0.bias": _parameter([2], [0, 1]),
        "ps_network.network.2.weight": _parameter([2, 2], [1, 0, -1, 0]),
        "ps_network.network.2.bias": _parameter([2], [0, 0]),
        "va_network.network.0.weight": _parameter([1, 2], [0, 0]),
        "va_network.network.0.bias": _parameter([1], [1]),
        "va_network.network.2.weight": _parameter([1, 1], [0.25]),
        "va_network.network.2.bias": _parameter([1], [0]),
        "gs_model.raw_coordinates": _parameter(
            [2, 2], [0, 0, 0, 0] if zero_geometry else [1, 0, 0, 1]
        ),
    }
    end = {
        name: {"shape": list(row["shape"]), "float64_hex": list(row["float64_hex"])}
        for name, row in start.items()
    }
    end["ps_network.network.0.weight"] = _parameter([2, 2], [1, 0, 0, 0])
    state = {"channel_features_float64_hex": _hex([1, 0])}
    return start, end, state


@unittest.skipIf(arb is None, "python-flint is isolated from production")
class ValidatedScalarTaylorV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctx.prec = 256

    def _path(self, *, zero_geometry: bool = False):
        from src.validation.validated_scalar_taylor_v2 import TaylorTransmitterPath

        start, end, state = _synthetic_payload(zero_geometry=zero_geometry)
        return TaylorTransmitterPath(start, end, state, float(0.1).hex(), float(1.5).hex())

    def test_affine_jet_is_exact(self):
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet

        variable = NormalizedJet.variable(arb("0.25"), 3)
        affine = 2 + 3 * variable
        self.assertTrue(affine.coefficients[0].contains(arb("2.75")))
        self.assertTrue(affine.coefficients[1].contains(3))
        self.assertTrue(affine.coefficients[2].is_zero())
        self.assertTrue(affine.coefficients[3].is_zero())

    def test_second_order_exp_remainder_contains_samples(self):
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet, taylor_enclosure

        center = arb("0.5")
        radius = arb("0.25")
        point = NormalizedJet.variable(center, 3).exp()
        interval = NormalizedJet.variable(arb(center, radius), 3).exp()
        enclosure = taylor_enclosure(point, interval, arb(0, radius), order=2)
        for value in (0.25, 0.375, 0.5, 0.625, 0.75):
            self.assertTrue(enclosure.contains(arb(value).exp()))

    def test_reciprocal_sqrt_and_complex_exp_enclose_samples(self):
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet, taylor_enclosure

        center, radius = arb(1), arb("0.125")
        point_var = NormalizedJet.variable(center, 3)
        interval_var = NormalizedJet.variable(arb(center, radius), 3)
        point = ((1 + point_var).sqrt().reciprocal() * acb(0, 1)).exp()
        interval = ((1 + interval_var).sqrt().reciprocal() * acb(0, 1)).exp()
        enclosure = taylor_enclosure(point, interval, arb(0, radius), order=2)
        for value in (0.875, 1.0, 1.125):
            expected = acb(0, 1 / math.sqrt(1 + value)).exp()
            self.assertTrue(enclosure.contains(expected))

    def test_relu_transition_is_exact_and_partitions_path(self):
        path = self._path()
        self.assertEqual(path.relu_transition_points(), [Fraction(1, 2)])
        self.assertEqual(
            path.smooth_cells(),
            [(Fraction(0), Fraction(1, 2)), (Fraction(1, 2), Fraction(1))],
        )

    def test_cell_may_not_cross_relu_transition(self):
        path = self._path()
        with self.assertRaises(ValueError):
            path.cell_enclosures(Fraction(0), Fraction(1), order=2)

    def test_softmax_and_energy_normalization_are_enclosed(self):
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet

        path = self._path()
        row = path.cell_enclosures(Fraction(0), Fraction(1, 2), order=2)
        self.assertTrue(all(value.lower() > 0 for value in row["orbit_masses"]))
        self.assertTrue(sum(row["orbit_masses"], arb(0)).contains(1))
        self.assertTrue(row["variance"].lower() > 0)
        self.assertTrue(row["raw_mean_energy"].lower() > 0)
        self.assertTrue(row["physical_energy"].lower() > 0)
        for endpoint in (Fraction(0), Fraction(1, 2)):
            point_path = NormalizedJet.variable(
                arb(endpoint.numerator) / endpoint.denominator, 3
            )
            exact = path.outputs(point_path, midpoint=Fraction(1, 4))
            self.assertTrue(row["variance"].contains(exact.variance.coefficients[0]))
            self.assertTrue(all(
                enclosure.contains(value.coefficients[0])
                for enclosure, value in zip(row["orbit_masses"], exact.orbit_masses)
            ))
            self.assertTrue(all(
                enclosure.contains(value.coefficients[0])
                for enclosure, value in zip(
                    row["physical_prototypes"], exact.physical_prototypes
                )
            ))

    def test_path_domain_certifies_valid_synthetic_transmitter(self):
        result = self._path().certify_path_domain(order=2, maximum_depth=4)
        self.assertEqual(result["status"], "PATH_DOMAIN_CERTIFIED")
        self.assertEqual(result["unresolved_leaf_count"], 0)
        self.assertGreaterEqual(result["certified_leaf_count"], 2)

    def test_zero_geometry_fails_path_domain(self):
        result = self._path(zero_geometry=True).certify_path_domain(order=2, maximum_depth=1)
        self.assertEqual(result["status"], "PATH_DOMAIN_UNCERTIFIED")
        self.assertGreater(result["unresolved_leaf_count"], 0)

    def test_c4_sectors_are_hermitian_and_contain_endpoints(self):
        from src.validation.validated_scalar_taylor_v2 import NormalizedJet

        path = self._path()
        left, right = Fraction(0), Fraction(1, 2)
        enclosed = path.c4_sector_enclosures(left, right, order=2)
        for sector in enclosed:
            for row in range(len(sector)):
                self.assertTrue(sector[row][row].imag.contains(0))
                for column in range(len(sector)):
                    self.assertTrue(sector[row][column].overlaps(
                        sector[column][row].conjugate()
                    ))
        for endpoint in (left, right):
            point_path = NormalizedJet.variable(arb(endpoint.numerator) / endpoint.denominator, 3)
            outputs = path.outputs(point_path, midpoint=Fraction(1, 4))
            self.assertTrue(all(value.coefficients[0].is_finite()
                                for value in outputs.physical_prototypes))


if __name__ == "__main__":
    unittest.main()
