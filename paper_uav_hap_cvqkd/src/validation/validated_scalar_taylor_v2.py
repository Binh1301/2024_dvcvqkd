"""Validated scalar Taylor arithmetic for the certification-only V2 path.

This module is deliberately independent of PyTorch and the production CV-QKD
implementation.  It interprets fixture parameters as exact IEEE-754 dyadics,
propagates normalized derivatives in Arb/acb arithmetic, and encloses a smooth
one-dimensional path cell by Taylor's theorem.  ReLU transition locations are
computed exactly and used as mandatory cell boundaries.

The code supplies numerical building blocks, not a threshold approval or a
whole-segment inertia certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Any, Iterable, Sequence

from flint import acb, arb

from .rigorous_flint_support import (
    exact_arb_from_float_hex,
    exact_arb_from_fraction,
    fraction_ball,
)


I = acb(0, 1)


def _is_complex(value: Any) -> bool:
    return isinstance(value, acb)


def _promote(value: Any, complex_output: bool) -> arb | acb:
    if complex_output:
        return value if isinstance(value, acb) else acb(value)
    if isinstance(value, acb):
        if not value.imag.contains(0):
            raise ValueError("Cannot demote a non-real acb value to arb.")
        return value.real
    return value if isinstance(value, arb) else arb(value)


def _fraction_from_float_hex(value: str) -> Fraction:
    binary = float.fromhex(value)
    if not math.isfinite(binary):
        raise ValueError("Certification inputs must be finite binary64 values.")
    numerator, denominator = binary.as_integer_ratio()
    return Fraction(numerator, denominator)


@dataclass(frozen=True)
class NormalizedJet:
    """Truncated normalized derivatives ``f^(k) / k!``.

    Coefficients may be point balls or interval balls.  Instantiating a
    variable jet with an interval zeroth coefficient therefore encloses the
    corresponding derivative at every base point in that interval.
    """

    coefficients: tuple[arb | acb, ...]

    def __post_init__(self) -> None:
        if not self.coefficients:
            raise ValueError("A jet must contain at least its zeroth coefficient.")
        complex_output = any(_is_complex(value) for value in self.coefficients)
        object.__setattr__(
            self,
            "coefficients",
            tuple(_promote(value, complex_output) for value in self.coefficients),
        )

    @property
    def degree(self) -> int:
        return len(self.coefficients) - 1

    @property
    def is_complex(self) -> bool:
        return _is_complex(self.coefficients[0])

    @classmethod
    def constant(cls, value: Any, degree: int) -> "NormalizedJet":
        if degree < 0:
            raise ValueError("Jet degree must be nonnegative.")
        base = value if isinstance(value, (arb, acb)) else arb(value)
        zero = base * 0
        return cls((base,) + tuple(zero for _ in range(degree)))

    @classmethod
    def variable(cls, value: arb, degree: int) -> "NormalizedJet":
        if degree < 1:
            raise ValueError("A variable jet needs degree at least one.")
        return cls((value, arb(1)) + tuple(arb(0) for _ in range(degree - 1)))

    def _coerce(self, other: Any) -> "NormalizedJet":
        if isinstance(other, NormalizedJet):
            if other.degree != self.degree:
                raise ValueError("Jet degrees differ.")
            if self.is_complex == other.is_complex:
                return other
            if self.is_complex:
                return NormalizedJet(tuple(acb(value) for value in other.coefficients))
            return other
        complex_output = self.is_complex or isinstance(other, acb)
        value = _promote(other, complex_output)
        return NormalizedJet.constant(value, self.degree)

    def _paired(self, other: Any) -> tuple["NormalizedJet", "NormalizedJet"]:
        right = self._coerce(other)
        if self.is_complex or right.is_complex:
            left = self if self.is_complex else NormalizedJet(
                tuple(acb(value) for value in self.coefficients)
            )
            right = right if right.is_complex else NormalizedJet(
                tuple(acb(value) for value in right.coefficients)
            )
            return left, right
        return self, right

    def __add__(self, other: Any) -> "NormalizedJet":
        left, right = self._paired(other)
        return NormalizedJet(tuple(a + b for a, b in zip(left.coefficients, right.coefficients)))

    __radd__ = __add__

    def __neg__(self) -> "NormalizedJet":
        return NormalizedJet(tuple(-value for value in self.coefficients))

    def __sub__(self, other: Any) -> "NormalizedJet":
        return self + (-self._coerce(other))

    def __rsub__(self, other: Any) -> "NormalizedJet":
        return (-self) + other

    def __mul__(self, other: Any) -> "NormalizedJet":
        left, right = self._paired(other)
        output = []
        for order in range(self.degree + 1):
            value = left.coefficients[0] * right.coefficients[order]
            for index in range(1, order + 1):
                value += left.coefficients[index] * right.coefficients[order - index]
            output.append(value)
        return NormalizedJet(tuple(output))

    __rmul__ = __mul__

    def reciprocal(self) -> "NormalizedJet":
        output = [1 / self.coefficients[0]]
        for order in range(1, self.degree + 1):
            value = self.coefficients[1] * output[order - 1]
            for index in range(2, order + 1):
                value += self.coefficients[index] * output[order - index]
            output.append(-output[0] * value)
        return NormalizedJet(tuple(output))

    def __truediv__(self, other: Any) -> "NormalizedJet":
        return self * self._coerce(other).reciprocal()

    def __rtruediv__(self, other: Any) -> "NormalizedJet":
        return self._coerce(other) * self.reciprocal()

    def exp(self) -> "NormalizedJet":
        output = [self.coefficients[0].exp()]
        for order in range(1, self.degree + 1):
            value = self.coefficients[1] * output[order - 1]
            for index in range(2, order + 1):
                value += index * self.coefficients[index] * output[order - index]
            output.append(value / order)
        return NormalizedJet(tuple(output))

    def sqrt(self) -> "NormalizedJet":
        output = [self.coefficients[0].sqrt()]
        for order in range(1, self.degree + 1):
            correction = output[1] * output[order - 1] if order > 1 else output[0] * 0
            for index in range(2, order):
                correction += output[index] * output[order - index]
            output.append((self.coefficients[order] - correction) / (2 * output[0]))
        return NormalizedJet(tuple(output))

    def conjugate(self) -> "NormalizedJet":
        if not self.is_complex:
            return self
        return NormalizedJet(tuple(value.conjugate() for value in self.coefficients))

    def abs_squared(self) -> "NormalizedJet":
        product = self * self.conjugate()
        if not product.is_complex:
            return product
        # z*conj(z) is mathematically real.  Interval multiplication can leave
        # a harmless imaginary-radius enclosure, so retain its rigorous real
        # projection for the real-valued energy path.
        return NormalizedJet(tuple(value.real for value in product.coefficients))


def taylor_enclosure(
    point_jet: NormalizedJet,
    derivative_interval_jet: NormalizedJet,
    delta: arb,
    *,
    order: int = 2,
) -> arb | acb:
    """Enclose a smooth scalar on one cell by Taylor's theorem.

    ``point_jet`` is based at the cell center.  The coefficient of degree
    ``order + 1`` in ``derivative_interval_jet`` must enclose that normalized
    derivative for every base point in the cell.
    """

    if order < 0:
        raise ValueError("Taylor order must be nonnegative.")
    if point_jet.degree < order or derivative_interval_jet.degree < order + 1:
        raise ValueError("Jets do not contain the requested Taylor remainder.")
    complex_output = point_jet.is_complex or derivative_interval_jet.is_complex
    result = _promote(point_jet.coefficients[0], complex_output)
    power: arb | acb = _promote(arb(1), complex_output)
    promoted_delta = _promote(delta, complex_output)
    for degree in range(1, order + 1):
        power *= promoted_delta
        result += _promote(point_jet.coefficients[degree], complex_output) * power
    power *= promoted_delta
    result += _promote(
        derivative_interval_jet.coefficients[order + 1], complex_output
    ) * power
    return result


@dataclass
class TaylorTransmitterOutputs:
    orbit_masses: list[NormalizedJet]
    variance: NormalizedJet
    variance_unit: NormalizedJet
    raw_mean_energy: NormalizedJet
    relative_prototypes: list[NormalizedJet]
    physical_energy: NormalizedJet
    physical_scale: NormalizedJet
    orbit_probabilities: list[NormalizedJet]
    physical_prototypes: list[NormalizedJet]


class TaylorTransmitterPath:
    """Certification-only normalized-derivative form of the frozen path."""

    REQUIRED_PARAMETERS = {
        "ps_network.network.0.weight", "ps_network.network.0.bias",
        "ps_network.network.2.weight", "ps_network.network.2.bias",
        "gs_model.raw_coordinates",
        "va_network.network.0.weight", "va_network.network.0.bias",
        "va_network.network.2.weight", "va_network.network.2.bias",
    }

    def __init__(
        self,
        start: dict[str, Any],
        end: dict[str, Any],
        state: dict[str, Any],
        v_min_hex: str,
        v_max_hex: str,
    ) -> None:
        if set(start) != set(end) or set(start) != self.REQUIRED_PARAMETERS:
            raise ValueError("Path payload does not match the frozen transmitter parameter names.")
        self.start = start
        self.end = end
        self.feature_fractions = [
            _fraction_from_float_hex(value) for value in state["channel_features_float64_hex"]
        ]
        self.features = [exact_arb_from_fraction(value) for value in self.feature_fractions]
        self.v_min = exact_arb_from_float_hex(v_min_hex)
        self.v_max = exact_arb_from_float_hex(v_max_hex)
        if not bool(self.v_min.lower() > 0) or not bool(self.v_max.lower() > self.v_min.upper()):
            raise ValueError("VA bounds must satisfy 0 < V_min < V_max.")
        self._validate_payloads()

    @staticmethod
    def _shape_size(shape: Sequence[int]) -> int:
        size = 1
        for value in shape:
            size *= int(value)
        return size

    def _validate_payloads(self) -> None:
        for name in self.REQUIRED_PARAMETERS:
            left, right = self.start[name], self.end[name]
            if left["shape"] != right["shape"]:
                raise ValueError(f"Endpoint shape mismatch for {name}.")
            expected = self._shape_size(left["shape"])
            if len(left["float64_hex"]) != expected or len(right["float64_hex"]) != expected:
                raise ValueError(f"Malformed flattened payload for {name}.")

    def _parameter(self, name: str, path: NormalizedJet) -> tuple[list[int], list[NormalizedJet]]:
        left, right = self.start[name], self.end[name]
        values = []
        for initial_hex, final_hex in zip(left["float64_hex"], right["float64_hex"]):
            initial = exact_arb_from_float_hex(initial_hex)
            final = exact_arb_from_float_hex(final_hex)
            values.append(initial + path * (final - initial))
        return [int(value) for value in left["shape"]], values

    def _linear(
        self, prefix: str, inputs: list[NormalizedJet], path: NormalizedJet
    ) -> list[NormalizedJet]:
        shape, weights = self._parameter(prefix + ".weight", path)
        bias_shape, biases = self._parameter(prefix + ".bias", path)
        if len(shape) != 2 or shape[1] != len(inputs) or bias_shape != [shape[0]]:
            raise ValueError(f"Invalid affine shape for {prefix}.")
        outputs = []
        for row in range(shape[0]):
            value = biases[row]
            offset = row * shape[1]
            for column, input_value in enumerate(inputs):
                value += weights[offset + column] * input_value
            outputs.append(value)
        return outputs

    def _first_layer_affines(self, prefix: str) -> list[tuple[Fraction, Fraction]]:
        weight_name, bias_name = prefix + ".weight", prefix + ".bias"
        shape = [int(value) for value in self.start[weight_name]["shape"]]
        if len(shape) != 2 or shape[1] != len(self.feature_fractions):
            raise ValueError(f"Invalid first-layer shape for {prefix}.")
        rows = []
        for row in range(shape[0]):
            intercept = _fraction_from_float_hex(self.start[bias_name]["float64_hex"][row])
            final = _fraction_from_float_hex(self.end[bias_name]["float64_hex"][row])
            slope = final - intercept
            for column, feature in enumerate(self.feature_fractions):
                index = row * shape[1] + column
                initial_weight = _fraction_from_float_hex(
                    self.start[weight_name]["float64_hex"][index]
                )
                final_weight = _fraction_from_float_hex(
                    self.end[weight_name]["float64_hex"][index]
                )
                intercept += feature * initial_weight
                slope += feature * (final_weight - initial_weight)
            rows.append((intercept, slope))
        return rows

    def relu_transition_points(self) -> list[Fraction]:
        roots = set()
        for prefix in ("ps_network.network.0", "va_network.network.0"):
            for intercept, slope in self._first_layer_affines(prefix):
                if slope:
                    root = -intercept / slope
                    if Fraction(0) < root < Fraction(1):
                        roots.add(root)
        return sorted(roots)

    def smooth_cells(self) -> list[tuple[Fraction, Fraction]]:
        boundaries = [Fraction(0), *self.relu_transition_points(), Fraction(1)]
        return list(zip(boundaries[:-1], boundaries[1:]))

    def _activation_mask(self, prefix: str, midpoint: Fraction) -> list[bool]:
        result = []
        for intercept, slope in self._first_layer_affines(prefix):
            value = intercept + slope * midpoint
            result.append(value > 0)
        return result

    @staticmethod
    def _softmax(logits: list[NormalizedJet]) -> list[NormalizedJet]:
        if not logits:
            raise ValueError("Softmax requires at least one logit.")
        # The fixed shift is an exact algebraic invariance and is not used for
        # a proof decision.  It only keeps exponentials near unit scale.
        shift = max(float(value.coefficients[0].mid()) for value in logits)
        exponentials = [(value - arb(shift)).exp() for value in logits]
        denominator = sum(exponentials[1:], exponentials[0])
        return [value / denominator for value in exponentials]

    @staticmethod
    def _sigmoid(value: NormalizedJet) -> NormalizedJet:
        if float(value.coefficients[0].mid()) >= 0:
            return 1 / (1 + (-value).exp())
        exponential = value.exp()
        return exponential / (1 + exponential)

    def outputs(self, path: NormalizedJet, *, midpoint: Fraction) -> TaylorTransmitterOutputs:
        ps_hidden_raw = self._linear("ps_network.network.0", [
            NormalizedJet.constant(value, path.degree) for value in self.features
        ], path)
        ps_mask = self._activation_mask("ps_network.network.0", midpoint)
        ps_hidden = [value if active else NormalizedJet.constant(0, path.degree)
                     for value, active in zip(ps_hidden_raw, ps_mask)]
        orbit_masses = self._softmax(self._linear("ps_network.network.2", ps_hidden, path))

        va_hidden_raw = self._linear("va_network.network.0", [
            NormalizedJet.constant(value, path.degree) for value in self.features
        ], path)
        va_mask = self._activation_mask("va_network.network.0", midpoint)
        va_hidden = [value if active else NormalizedJet.constant(0, path.degree)
                     for value, active in zip(va_hidden_raw, va_mask)]
        va_raw = self._linear("va_network.network.2", va_hidden, path)[0]
        variance_unit = self._sigmoid(va_raw)
        log_ratio = (self.v_max / self.v_min).log()
        variance = self.v_min * (log_ratio * variance_unit).exp()

        shape, coordinates = self._parameter("gs_model.raw_coordinates", path)
        if shape != [len(orbit_masses), 2]:
            raise ValueError("GS orbit count must equal the PS orbit count.")
        raw = [NormalizedJet(tuple(
            acb(
                coordinates[2 * index].coefficients[degree],
                coordinates[2 * index + 1].coefficients[degree],
            )
            for degree in range(path.degree + 1)
        ))
               for index in range(len(orbit_masses))]
        raw_mean_energy = sum((value.abs_squared() for value in raw),
                              NormalizedJet.constant(0, path.degree)) / len(raw)
        gauge = raw_mean_energy.sqrt()
        relative = [value / gauge for value in raw]
        physical_energy = sum(
            (mass * prototype.abs_squared() for mass, prototype in zip(orbit_masses, relative)),
            NormalizedJet.constant(0, path.degree),
        )
        physical_scale = (variance / (2 * physical_energy)).sqrt()
        probabilities = [mass / 4 for mass in orbit_masses]
        # Cancel the global gauge only in the final physical amplitudes.  The
        # frozen gauge and its domain are still evaluated above.  This exact
        # identity avoids introducing the same uncertain scalar twice:
        # (raw/g)*sqrt(VA/(2*sum q*|raw/g|^2))
        # = raw*sqrt(VA/(2*sum q*|raw|^2)).
        weighted_raw_energy = sum(
            (mass * prototype.abs_squared()
             for mass, prototype in zip(orbit_masses, raw)),
            NormalizedJet.constant(0, path.degree),
        )
        raw_physical_scale = (variance / (2 * weighted_raw_energy)).sqrt()
        prototypes = [raw_physical_scale * value for value in raw]
        return TaylorTransmitterOutputs(
            orbit_masses=orbit_masses,
            variance=variance,
            variance_unit=variance_unit,
            raw_mean_energy=raw_mean_energy,
            relative_prototypes=relative,
            physical_energy=physical_energy,
            physical_scale=physical_scale,
            orbit_probabilities=probabilities,
            physical_prototypes=prototypes,
        )

    @staticmethod
    def _enclose_output(
        point: NormalizedJet, interval: NormalizedJet, delta: arb, order: int
    ) -> arb | acb:
        return taylor_enclosure(point, interval, delta, order=order)

    def cell_enclosures(
        self, left: Fraction, right: Fraction, *, order: int = 2
    ) -> dict[str, Any]:
        if left >= right:
            raise ValueError("A smooth cell must have positive width.")
        if any(left < root < right for root in self.relu_transition_points()):
            raise ValueError("A Taylor cell may not cross a ReLU transition.")
        midpoint = (left + right) / 2
        degree = order + 1
        point_path = NormalizedJet.variable(exact_arb_from_fraction(midpoint), degree)
        interval_path = NormalizedJet.variable(fraction_ball(left, right), degree)
        point = self.outputs(point_path, midpoint=midpoint)
        interval = self.outputs(interval_path, midpoint=midpoint)
        delta = fraction_ball(left - midpoint, right - midpoint)

        def scalar(name: str) -> arb | acb:
            return self._enclose_output(getattr(point, name), getattr(interval, name), delta, order)

        def vector(name: str) -> list[arb | acb]:
            return [self._enclose_output(a, b, delta, order)
                    for a, b in zip(getattr(point, name), getattr(interval, name))]

        return {
            "left": left,
            "right": right,
            "midpoint": midpoint,
            "order": order,
            "orbit_masses": vector("orbit_masses"),
            "variance": scalar("variance"),
            "variance_unit": scalar("variance_unit"),
            "raw_mean_energy": scalar("raw_mean_energy"),
            "relative_prototypes": vector("relative_prototypes"),
            "physical_energy": scalar("physical_energy"),
            "physical_scale": scalar("physical_scale"),
            "orbit_probabilities": vector("orbit_probabilities"),
            "physical_prototypes": vector("physical_prototypes"),
            "point_outputs": point,
            "interval_outputs": interval,
            "delta": delta,
        }

    def certify_path_domain(self, *, order: int = 2, maximum_depth: int = 8) -> dict[str, Any]:
        """Fail-closed physical-domain proof over all ReLU-smooth cells."""

        pending = [(left, right, 0) for left, right in reversed(self.smooth_cells())]
        certified = []
        unresolved = []
        while pending:
            left, right, depth = pending.pop()
            try:
                row = self.cell_enclosures(left, right, order=order)
                masses = row["orbit_masses"]
                unit = row["variance_unit"]
                raw_energy = row["raw_mean_energy"]
                scale = row["physical_scale"]
                prototypes = row["physical_prototypes"]
                q_min = min((value.lower() for value in masses), key=float)
                # The gauge gives sum |z_k|^2 = n exactly.  Thus this bound is
                # stronger than independently interval-evaluating sum q_k|z_k|^2.
                energy_lower = (len(masses) * q_min).lower()
                checks = {
                    "finite_orbit_masses": all(value.is_finite() for value in masses),
                    "strictly_positive_orbit_masses": bool(q_min > 0),
                    "softmax_normalized_by_construction": True,
                    "variance_unit_strictly_inside_zero_one": (
                        unit.is_finite() and bool(unit.lower() > 0) and bool(unit.upper() < 1)
                    ),
                    "raw_gauge_energy_positive": (
                        raw_energy.is_finite() and bool(raw_energy.lower() > 0)
                    ),
                    "physical_energy_positive_from_gauge_bound": bool(energy_lower > 0),
                    "physical_scale_positive_finite": (
                        scale.is_finite() and bool(scale.lower() > 0)
                    ),
                    "physical_prototypes_finite": all(value.is_finite() for value in prototypes),
                }
                row = {
                    "left": str(left), "right": str(right), "depth": depth,
                    "checks": checks,
                    "minimum_orbit_mass_lower": q_min.str(18, radius=False),
                    "physical_energy_gauge_lower": energy_lower.str(18, radius=False),
                }
                if all(checks.values()):
                    row["status"] = "PATH_DOMAIN_CERTIFIED"
                    certified.append(row)
                    continue
                failure = "DOMAIN_BOUND_UNRESOLVED"
            except (ArithmeticError, ValueError, ZeroDivisionError) as error:
                row = {"left": str(left), "right": str(right), "depth": depth}
                failure = f"ARITHMETIC_UNRESOLVED: {error}"

            if depth >= maximum_depth:
                row.update({"status": "PATH_DOMAIN_UNCERTIFIED", "reason": failure})
                unresolved.append(row)
            else:
                middle = (left + right) / 2
                pending.append((middle, right, depth + 1))
                pending.append((left, middle, depth + 1))

        return {
            "status": "PATH_DOMAIN_CERTIFIED" if not unresolved else "PATH_DOMAIN_UNCERTIFIED",
            "relu_transition_points": [str(value) for value in self.relu_transition_points()],
            "certified_leaf_count": len(certified),
            "unresolved_leaf_count": len(unresolved),
            "certified_leaves": certified,
            "unresolved_leaves": unresolved,
            "relu_is_continuous_but_not_assumed_differentiable": True,
            "coherent_overlap_is_entire_on_finite_amplitudes": not unresolved,
        }

    @staticmethod
    def _overlap(left: NormalizedJet, right: NormalizedJet) -> NormalizedJet:
        exponent = -(left.abs_squared() + right.abs_squared()) / 2 + left.conjugate() * right
        return exponent.exp()

    def c4_sector_enclosures(
        self, left: Fraction, right: Fraction, *, order: int = 2
    ) -> list[list[list[acb]]]:
        """Return four Taylor-enclosed C4 Gram sectors on one smooth cell."""

        cell = self.cell_enclosures(left, right, order=order)
        point: TaylorTransmitterOutputs = cell["point_outputs"]
        interval: TaylorTransmitterOutputs = cell["interval_outputs"]
        delta: arb = cell["delta"]
        rotations = [acb(1), I, acb(-1), -I]

        def build(outputs: TaylorTransmitterOutputs) -> list[list[list[NormalizedJet]]]:
            size = len(outputs.orbit_probabilities)
            sectors = []
            for sector in range(4):
                matrix = [[NormalizedJet.constant(acb(0), outputs.variance.degree)
                           for _ in range(size)] for _ in range(size)]
                for row in range(size):
                    for column in range(size):
                        root_probability = (
                            outputs.orbit_probabilities[row]
                            * outputs.orbit_probabilities[column]
                        ).sqrt()
                        value = NormalizedJet.constant(acb(0), outputs.variance.degree)
                        for difference in range(4):
                            value += (
                                root_probability
                                * self._overlap(
                                    outputs.physical_prototypes[row],
                                    rotations[difference] * outputs.physical_prototypes[column],
                                )
                                * (I ** (sector * difference))
                            )
                        matrix[row][column] = value
                sectors.append(matrix)
            return sectors

        point_sectors, interval_sectors = build(point), build(interval)
        enclosed = []
        for point_matrix, interval_matrix in zip(point_sectors, interval_sectors):
            size = len(point_matrix)
            raw = [[acb(taylor_enclosure(
                point_matrix[row][column], interval_matrix[row][column], delta, order=order
            )) for column in range(size)] for row in range(size)]
            enclosed.append([[
                (raw[row][column] + raw[column][row].conjugate()) / 2
                for column in range(size)
            ] for row in range(size)])
        return enclosed


__all__ = [
    "NormalizedJet",
    "TaylorTransmitterOutputs",
    "TaylorTransmitterPath",
    "taylor_enclosure",
]
