"""Coefficient-preserving Taylor congruence for C4 Gram sectors.

The V2 certifier enclosed every sector entry over a path cell before applying
the fixed rounded-basis congruence.  That is rigorous, but it discards the
shared scalar Taylor dependence before the large matrix sums in ``Q* H Q``.
This module keeps the normalized Taylor coefficient matrices separate through
that congruence and widens to a cell enclosure only afterwards.

This is a certification-only numerical layer.  It does not change the C4
ensemble, the candidate threshold, or the production security functional.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Sequence

from flint import acb, arb

from .rigorous_flint_support import exact_arb_from_fraction, fraction_ball
from .rigorous_shifted_inertia import canonicalize_hermitian
from .rigorous_taylor_eigencluster_v2 import exact_congruence_enclosure
from .validated_scalar_taylor_v2 import (
    NormalizedJet,
    TaylorTransmitterOutputs,
    TaylorTransmitterPath,
)


I = acb(0, 1)
Matrix = list[list[acb]]


def _zero_matrix(size: int) -> Matrix:
    return [[acb(0) for _ in range(size)] for _ in range(size)]


def _identity_matrix(size: int) -> Matrix:
    return [[acb(1 if row == column else 0) for column in range(size)]
            for row in range(size)]


def _copy_matrix(values: Sequence[Sequence[acb]]) -> Matrix:
    return [[acb(value) for value in row] for row in values]


def _overlap(left: NormalizedJet, right: NormalizedJet) -> NormalizedJet:
    exponent = -(left.abs_squared() + right.abs_squared()) / 2
    exponent += left.conjugate() * right
    return exponent.exp()


def _c4_sector_jets(outputs: TaylorTransmitterOutputs) -> list[list[list[NormalizedJet]]]:
    """Build the exact four C4 sector jet matrices before scalar widening."""

    size = len(outputs.orbit_probabilities)
    rotations = [acb(1), I, acb(-1), -I]
    sectors: list[list[list[NormalizedJet]]] = []
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
                        * _overlap(
                            outputs.physical_prototypes[row],
                            rotations[difference] * outputs.physical_prototypes[column],
                        )
                        * (I ** (sector * difference))
                    )
                matrix[row][column] = value
        sectors.append(matrix)
    return sectors


def _jet_coefficient_matrix(
    values: Sequence[Sequence[NormalizedJet]], degree: int,
) -> Matrix:
    raw = [[acb(value.coefficients[degree]) for value in row] for row in values]
    # Every derivative of a Hermitian matrix-valued path is Hermitian.  The
    # intersection removes only independently accumulated arithmetic radius.
    return canonicalize_hermitian(raw)


@dataclass(frozen=True)
class HermitianTaylorModel:
    """A normalized matrix Taylor model on one ReLU-smooth path cell.

    ``coefficients[k]`` encloses ``H^(k)(center)/k!``.  The remainder matrix
    encloses ``H^(order+1)(s)/(order+1)!`` for every ``s`` in the complete
    cell.  All matrices are explicitly Hermitian inclusion enclosures.
    """

    left: Fraction
    right: Fraction
    center: Fraction
    order: int
    coefficients: tuple[Matrix, ...]
    remainder_coefficient: Matrix

    def __post_init__(self) -> None:
        if self.left >= self.right or self.center != (self.left + self.right) / 2:
            raise ValueError("Taylor model requires a positive cell and its exact midpoint.")
        if self.order < 0 or len(self.coefficients) != self.order + 1:
            raise ValueError("Taylor coefficient count does not match the model order.")
        size = len(self.remainder_coefficient)
        if size == 0:
            raise ValueError("Taylor matrix dimension must be positive.")
        for matrix in (*self.coefficients, self.remainder_coefficient):
            if len(matrix) != size or any(len(row) != size for row in matrix):
                raise ValueError("All Taylor coefficient matrices must have one square shape.")
        # Make the public model invariant explicit even for direct synthetic
        # construction, not only for models produced by the C4 builder.
        object.__setattr__(
            self,
            "coefficients",
            tuple(canonicalize_hermitian(matrix) for matrix in self.coefficients),
        )
        object.__setattr__(
            self,
            "remainder_coefficient",
            canonicalize_hermitian(self.remainder_coefficient),
        )

    @property
    def dimension(self) -> int:
        return len(self.remainder_coefficient)


def build_c4_sector_taylor_models(
    path: TaylorTransmitterPath,
    left: Fraction,
    right: Fraction,
    *,
    order: int = 2,
) -> list[HermitianTaylorModel]:
    """Return four coefficient-level C4 sector models on one smooth cell."""

    if left >= right:
        raise ValueError("A smooth Taylor cell must have positive width.")
    if order < 0:
        raise ValueError("Taylor order must be nonnegative.")
    if any(left < root < right for root in path.relu_transition_points()):
        raise ValueError("A coefficient Taylor cell may not cross a ReLU transition.")
    center = (left + right) / 2
    degree = order + 1
    point_path = NormalizedJet.variable(exact_arb_from_fraction(center), degree)
    interval_path = NormalizedJet.variable(fraction_ball(left, right), degree)
    point_outputs = path.outputs(point_path, midpoint=center)
    interval_outputs = path.outputs(interval_path, midpoint=center)
    point_sectors = _c4_sector_jets(point_outputs)
    interval_sectors = _c4_sector_jets(interval_outputs)

    models = []
    for point_sector, interval_sector in zip(point_sectors, interval_sectors):
        coefficients = tuple(
            _jet_coefficient_matrix(point_sector, derivative)
            for derivative in range(order + 1)
        )
        remainder = _jet_coefficient_matrix(interval_sector, order + 1)
        models.append(HermitianTaylorModel(
            left=left,
            right=right,
            center=center,
            order=order,
            coefficients=coefficients,
            remainder_coefficient=remainder,
        ))
    return models


def congruence_taylor_model(
    model: HermitianTaylorModel,
    rounded_q: Sequence[Sequence[complex]],
) -> HermitianTaylorModel:
    """Apply exact-rounded ``Q* H(t) Q`` to every Taylor coefficient."""

    coefficients = tuple(
        exact_congruence_enclosure(matrix, rounded_q)
        for matrix in model.coefficients
    )
    remainder = exact_congruence_enclosure(model.remainder_coefficient, rounded_q)
    return replace(model, coefficients=coefficients, remainder_coefficient=remainder)


def shifted_rounded_congruence_taylor_model(
    model: HermitianTaylorModel,
    rounded_q: Sequence[Sequence[complex]],
    threshold: arb,
) -> HermitianTaylorModel:
    """Return ``Q* (H(t)-threshold I) Q`` without assuming ``Q`` unitary.

    The rounded midpoint basis is certified nonsingular but is not exactly
    unitary.  Consequently the constant term is ``Q*H_0 Q-threshold Q*Q``;
    subtracting ``threshold I`` after congruence would be mathematically wrong.
    """

    transformed = congruence_taylor_model(model, rounded_q)
    q_star_q = exact_congruence_enclosure(_identity_matrix(model.dimension), rounded_q)
    constant = _copy_matrix(transformed.coefficients[0])
    for row in range(model.dimension):
        for column in range(model.dimension):
            constant[row][column] -= threshold * q_star_q[row][column]
    constant = canonicalize_hermitian(constant)
    return replace(
        transformed,
        coefficients=(constant, *transformed.coefficients[1:]),
    )


def evaluate_taylor_model_enclosure(model: HermitianTaylorModel) -> Matrix:
    """Widen a coefficient model to one Hermitian enclosure for its cell.

    Horner evaluation delays scalar interval widening until all fixed-basis
    matrix sums have already been performed coefficient by coefficient.
    """

    delta = fraction_ball(model.left - model.center, model.right - model.center)
    output = _zero_matrix(model.dimension)
    for row in range(model.dimension):
        for column in range(model.dimension):
            value = model.remainder_coefficient[row][column]
            for degree in range(model.order, -1, -1):
                value = value * delta + model.coefficients[degree][row][column]
            output[row][column] = value
    return canonicalize_hermitian(output)


__all__ = [
    "HermitianTaylorModel",
    "build_c4_sector_taylor_models",
    "congruence_taylor_model",
    "evaluate_taylor_model_enclosure",
    "shifted_rounded_congruence_taylor_model",
]
