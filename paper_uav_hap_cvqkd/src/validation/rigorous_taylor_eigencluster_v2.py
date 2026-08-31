"""Rigorous fixed-basis eigencluster reduction for V2 segment certificates.

The rounded complex128 basis supplied by the caller is interpreted as an
*exact* dyadic matrix.  Its nonsingularity is certified before Sylvester's
law of inertia is used.  All matrix-family operations after that point use
Arb/acb inclusion arithmetic and fail closed.

This module deliberately does not construct transmitter or Taylor models.
It consumes only a Hermitian matrix enclosure, so the validated scalar
propagator remains a separate proof layer.
"""

from __future__ import annotations

import math
import time
from typing import Any, Sequence

from flint import acb, acb_mat, arb, ctx

from .rigorous_shifted_inertia import (
    canonicalize_hermitian,
    shift_hermitian,
    verified_block_ldl_inertia,
)


def _text(value: arb, digits: int = 24) -> str:
    return value.str(digits, radius=False)


def _exact_arb_from_float64(value: float) -> arb:
    """Return the exact dyadic real represented by a finite binary64 value."""

    rounded = float(value)
    if not math.isfinite(rounded):
        raise ValueError("Rounded basis entries must be finite complex128 values.")
    numerator, denominator = rounded.as_integer_ratio()
    return arb(numerator) / arb(denominator)


def exact_acb_from_complex128(value: complex) -> acb:
    """Embed the two rounded binary64 components as exact dyadic Arb values."""

    rounded = complex(value)
    return acb(
        _exact_arb_from_float64(rounded.real),
        _exact_arb_from_float64(rounded.imag),
    )


def exact_rounded_basis(values: Sequence[Sequence[complex]]) -> list[list[acb]]:
    """Convert a nonempty square rounded basis to an exact acb matrix."""

    size = len(values)
    if size == 0 or any(len(row) != size for row in values):
        raise ValueError("Rounded basis must be a nonempty square matrix.")
    return [[exact_acb_from_complex128(value) for value in row] for row in values]


def _adjoint(values: Sequence[Sequence[acb]]) -> list[list[acb]]:
    return [
        [values[row][column].conjugate() for row in range(len(values))]
        for column in range(len(values[0]))
    ]


def _matmul(
    left: Sequence[Sequence[acb]], right: Sequence[Sequence[acb]]
) -> list[list[acb]]:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("Incompatible nonempty matrix dimensions.")
    rows = len(left)
    shared = len(right)
    columns = len(right[0])
    if any(len(row) != shared for row in left) or any(len(row) != columns for row in right):
        raise ValueError("Ragged matrices are not supported.")
    return [
        [
            sum(
                (left[row][index] * right[index][column] for index in range(shared)),
                acb(0),
            )
            for column in range(columns)
        ]
        for row in range(rows)
    ]


def _frobenius_upper(values: Sequence[Sequence[acb]]) -> arb:
    total = arb(0)
    for row in values:
        for value in row:
            upper = value.abs_upper()
            total += upper * upper
    return total.sqrt().upper()


def _compact_inertia(result: dict[str, Any]) -> dict[str, Any]:
    pivots = result.get("pivot_rows", [])
    return {
        key: value for key, value in result.items() if key != "pivot_rows"
    } | {
        "pivot_count": len(pivots),
        "scalar_pivot_count": sum(row["block_size"] == 1 for row in pivots),
        "block_2x2_pivot_count": sum(row["block_size"] == 2 for row in pivots),
    }


def certify_rounded_basis(
    rounded_q: Sequence[Sequence[complex]], *, precision_bits: int,
    maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Prove that the exact matrix represented by rounded ``Q`` is nonsingular.

    The primary certificate is positive definiteness of ``Q* Q`` using the
    validated block-LDL inertia engine.  A Frobenius bound smaller than one on
    ``Q*Q-I`` is also reported when available, but is not required.
    """

    started = time.perf_counter()
    ctx.prec = int(precision_bits)
    q = exact_rounded_basis(rounded_q)
    gram = canonicalize_hermitian(_matmul(_adjoint(q), q))
    inertia = verified_block_ldl_inertia(
        gram,
        precision_bits=int(precision_bits),
        maximum_seconds=maximum_seconds,
    )
    defect = [[gram[row][column] - (1 if row == column else 0)
               for column in range(len(q))] for row in range(len(q))]
    defect_upper = _frobenius_upper(defect)
    positive_definite = (
        inertia["status"] == "CERTIFIED_INERTIA"
        and int(inertia["n_positive"]) == len(q)
        and int(inertia["n_negative"]) == 0
        and int(inertia["n_zero_or_unresolved"]) == 0
    )
    norm_proof = bool(defect_upper < 1)
    return {
        "status": "CERTIFIED_NONSINGULAR" if positive_definite else "UNCERTIFIED_BASIS",
        "dimension": len(q),
        "proof_method": (
            "GRAM_POSITIVE_DEFINITE_AND_FROBENIUS_DEFECT_LT_ONE"
            if positive_definite and norm_proof
            else "GRAM_POSITIVE_DEFINITE"
            if positive_definite
            else None
        ),
        "frobenius_q_star_q_minus_i_upper": _text(defect_upper),
        "frobenius_defect_lt_one": norm_proof,
        "gram_inertia": _compact_inertia(inertia),
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": None if positive_definite else "Q_STAR_Q_NOT_CERTIFIED_POSITIVE_DEFINITE",
    }


def exact_congruence_enclosure(
    hermitian_values: Sequence[Sequence[acb]],
    rounded_q: Sequence[Sequence[complex]],
) -> list[list[acb]]:
    """Return the inclusion enclosure ``Q* H Q`` for exact rounded ``Q``."""

    matrix = canonicalize_hermitian(hermitian_values)
    q = exact_rounded_basis(rounded_q)
    if len(q) != len(matrix):
        raise ValueError("Basis and Hermitian matrix dimensions differ.")
    return canonicalize_hermitian(_matmul(_matmul(_adjoint(q), matrix), q))


def deterministic_cluster_sizes(
    dimension: int, *, seed_size: int, expansion_step: int, maximum_size: int,
) -> list[int]:
    """Return the preregisterable deterministic cluster expansion schedule."""

    if dimension <= 0:
        raise ValueError("Dimension must be positive.")
    if seed_size <= 0 or expansion_step <= 0 or maximum_size <= 0:
        raise ValueError("Cluster sizes and expansion step must be positive.")
    cap = min(int(dimension), int(maximum_size))
    first = min(int(seed_size), cap)
    sizes = list(range(first, cap + 1, int(expansion_step)))
    if sizes[-1] != cap:
        sizes.append(cap)
    return sizes


def deterministic_cluster_partition(
    midpoint_eigenvalues: Sequence[float], *, threshold: float, cluster_size: int,
) -> dict[str, Any]:
    """Select modes nearest the threshold with index-stable tie breaking."""

    dimension = len(midpoint_eigenvalues)
    if dimension == 0 or cluster_size <= 0 or cluster_size > dimension:
        raise ValueError("Cluster size must lie in [1, dimension].")
    eigenvalues = [float(value) for value in midpoint_eigenvalues]
    if not math.isfinite(float(threshold)) or not all(math.isfinite(v) for v in eigenvalues):
        raise ValueError("Threshold and midpoint eigenvalues must be finite.")
    order = sorted(range(dimension), key=lambda index: (abs(eigenvalues[index] - threshold), index))
    cluster = sorted(order[:cluster_size])
    cluster_set = set(cluster)
    far = [index for index in range(dimension) if index not in cluster_set]
    return {
        "rule": "NEAREST_ABSOLUTE_THRESHOLD_DISTANCE_THEN_ORIGINAL_INDEX",
        "cluster_size": int(cluster_size),
        "cluster_indices": cluster,
        "far_indices": far,
        "cluster_distances": [abs(eigenvalues[index] - threshold) for index in cluster],
        "nearest_far_distance": (
            min(abs(eigenvalues[index] - threshold) for index in far) if far else None
        ),
    }


def _principal(values: Sequence[Sequence[acb]], indices: Sequence[int]) -> list[list[acb]]:
    return [[values[row][column] for column in indices] for row in indices]


def _rectangular(
    values: Sequence[Sequence[acb]], rows: Sequence[int], columns: Sequence[int]
) -> list[list[acb]]:
    return [[values[row][column] for column in columns] for row in rows]


def _as_acb_mat(values: Sequence[Sequence[acb]]) -> acb_mat:
    return acb_mat([[value for value in row] for row in values])


def _as_lists(values: acb_mat) -> list[list[acb]]:
    return [[values[row, column] for column in range(values.ncols())]
            for row in range(values.nrows())]


def _solve_diagnostics(a: acb_mat, x: acb_mat, e: acb_mat) -> dict[str, Any]:
    residual = a * x - e
    entries = residual.nrows() * residual.ncols()
    contains_zero = 0
    finite = True
    maximum_abs_upper = arb(0)
    maximum_radius = arb(0)
    for row in range(residual.nrows()):
        for column in range(residual.ncols()):
            value = residual[row, column]
            finite = finite and bool(value.is_finite())
            if value.contains(0):
                contains_zero += 1
            absolute = value.abs_upper()
            radius = value.real.rad() + value.imag.rad()
            if bool(absolute > maximum_abs_upper):
                maximum_abs_upper = absolute
            if bool(radius > maximum_radius):
                maximum_radius = radius
    return {
        "method": "PYTHON_FLINT_ACB_MAT_VALIDATED_SOLVE_PRECOND",
        "entry_count": entries,
        "residual_entries_containing_zero": contains_zero,
        "all_residual_entries_contain_zero": contains_zero == entries,
        "all_solution_and_residual_entries_finite": finite and all(
            bool(x[row, column].is_finite())
            for row in range(x.nrows()) for column in range(x.ncols())
        ),
        "maximum_residual_abs_upper": _text(maximum_abs_upper),
        "maximum_residual_component_radius": _text(maximum_radius),
    }


def validated_far_schur_reduction(
    shifted_congruence: Sequence[Sequence[acb]], *,
    far_indices: Sequence[int], cluster_indices: Sequence[int],
    precision_bits: int, maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Certify far inertia and enclose its Schur complement on the cluster."""

    started = time.perf_counter()
    ctx.prec = int(precision_bits)
    values = canonicalize_hermitian(shifted_congruence)
    dimension = len(values)
    far = list(far_indices)
    cluster = list(cluster_indices)
    if not cluster or sorted(far + cluster) != list(range(dimension)) or set(far) & set(cluster):
        raise ValueError("Far and cluster indices must form a disjoint full partition.")

    if not far:
        return {
            "status": "CERTIFIED_SCHUR_REDUCTION",
            "far_inertia": {
                "status": "CERTIFIED_INERTIA", "n_positive": 0, "n_negative": 0,
                "n_zero_or_unresolved": 0, "pivot_count": 0,
            },
            "solve": {
                "method": "EMPTY_FAR_BLOCK", "entry_count": 0,
                "residual_entries_containing_zero": 0,
                "all_residual_entries_contain_zero": True,
                "all_solution_and_residual_entries_finite": True,
                "maximum_residual_abs_upper": "0",
                "maximum_residual_component_radius": "0",
            },
            "schur_complement": canonicalize_hermitian(_principal(values, cluster)),
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": None,
        }

    a_values = canonicalize_hermitian(_principal(values, far))
    remaining = maximum_seconds
    far_inertia_full = verified_block_ldl_inertia(
        a_values, precision_bits=int(precision_bits), maximum_seconds=remaining
    )
    far_inertia = _compact_inertia(far_inertia_full)
    if far_inertia_full["status"] != "CERTIFIED_INERTIA":
        return {
            "status": "UNCERTIFIED_FAR_BLOCK",
            "far_inertia": far_inertia,
            "solve": None,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "FAR_BLOCK_INERTIA_OR_NONSINGULARITY_UNCERTIFIED",
        }
    if maximum_seconds is not None and time.perf_counter() - started >= maximum_seconds:
        return {
            "status": "UNCERTIFIED_RESOURCE_LIMIT",
            "far_inertia": far_inertia,
            "solve": None,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "MAXIMUM_SECONDS",
        }

    e_values = _rectangular(values, far, cluster)
    d_values = canonicalize_hermitian(_principal(values, cluster))
    try:
        a = _as_acb_mat(a_values)
        e = _as_acb_mat(e_values)
        # ``precond`` is an inclusion-producing Arb solve.  Never use the
        # available ``approx`` algorithm here because it carries no bounds.
        solution = a.solve(e, algorithm="precond")
        solve = _solve_diagnostics(a, solution, e)
    except (ValueError, ZeroDivisionError, RuntimeError) as error:
        return {
            "status": "UNCERTIFIED_SOLVE",
            "far_inertia": far_inertia,
            "solve": {
                "method": "PYTHON_FLINT_ACB_MAT_VALIDATED_SOLVE_PRECOND",
                "exception": str(error),
            },
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "VALIDATED_SOLVE_FAILED",
        }
    if not (
        solve["all_residual_entries_contain_zero"]
        and solve["all_solution_and_residual_entries_finite"]
    ):
        return {
            "status": "UNCERTIFIED_SOLVE",
            "far_inertia": far_inertia,
            "solve": solve,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "SOLVE_ENCLOSURE_DIAGNOSTICS_FAILED",
        }

    e_star = _as_acb_mat(_adjoint(e_values))
    schur_raw = _as_acb_mat(d_values) - e_star * solution
    try:
        schur = canonicalize_hermitian(_as_lists(schur_raw))
    except ValueError:
        return {
            "status": "UNCERTIFIED_SCHUR_HERMITICITY",
            "far_inertia": far_inertia,
            "solve": solve,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "SCHUR_CONJUGATE_ENCLOSURES_DO_NOT_INTERSECT",
        }
    return {
        "status": "CERTIFIED_SCHUR_REDUCTION",
        "far_inertia": far_inertia,
        "solve": solve,
        "schur_complement": schur,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": None,
    }


def certify_clustered_inertia(
    shifted_congruence: Sequence[Sequence[acb]], *,
    far_indices: Sequence[int], cluster_indices: Sequence[int],
    precision_bits: int, maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Certify full inertia by far-block congruence and reduced-cluster LDL."""

    started = time.perf_counter()
    reduction = validated_far_schur_reduction(
        shifted_congruence,
        far_indices=far_indices,
        cluster_indices=cluster_indices,
        precision_bits=int(precision_bits),
        maximum_seconds=maximum_seconds,
    )
    if reduction["status"] != "CERTIFIED_SCHUR_REDUCTION":
        return {
            "status": "UNCERTIFIED_CLUSTERED_INERTIA",
            "n_positive": None, "n_negative": None, "n_zero_or_unresolved": len(shifted_congruence),
            "reduction": {key: value for key, value in reduction.items() if key != "schur_complement"},
            "cluster_inertia": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": reduction["failure_reason"],
        }
    remaining = None
    if maximum_seconds is not None:
        remaining = max(0.0, maximum_seconds - (time.perf_counter() - started))
    cluster_full = verified_block_ldl_inertia(
        reduction["schur_complement"],
        precision_bits=int(precision_bits),
        maximum_seconds=remaining,
    )
    cluster = _compact_inertia(cluster_full)
    reduction_public = {key: value for key, value in reduction.items() if key != "schur_complement"}
    if cluster_full["status"] != "CERTIFIED_INERTIA":
        return {
            "status": "UNCERTIFIED_CLUSTERED_INERTIA",
            "n_positive": None, "n_negative": None,
            "n_zero_or_unresolved": int(cluster_full["n_zero_or_unresolved"]),
            "reduction": reduction_public,
            "cluster_inertia": cluster,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "REDUCED_CLUSTER_INERTIA_UNCERTIFIED",
        }
    far_inertia = reduction["far_inertia"]
    return {
        "status": "CERTIFIED_CLUSTERED_INERTIA",
        "n_positive": int(far_inertia["n_positive"]) + int(cluster_full["n_positive"]),
        "n_negative": int(far_inertia["n_negative"]) + int(cluster_full["n_negative"]),
        "n_zero_or_unresolved": 0,
        "reduction": reduction_public,
        "cluster_inertia": cluster,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": None,
    }


def certify_fixed_basis_eigencluster(
    hermitian_enclosure: Sequence[Sequence[acb]], *,
    rounded_q: Sequence[Sequence[complex]], midpoint_eigenvalues: Sequence[float],
    threshold: float, precision_bits: int, seed_size: int,
    expansion_step: int, maximum_cluster_size: int,
    maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Run the deterministic fixed-basis cluster schedule for one sector."""

    started = time.perf_counter()
    basis = certify_rounded_basis(
        rounded_q, precision_bits=int(precision_bits), maximum_seconds=maximum_seconds
    )
    if basis["status"] != "CERTIFIED_NONSINGULAR":
        return {
            "status": "UNCERTIFIED_BASIS", "basis": basis, "attempts": [],
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": basis["failure_reason"],
        }
    if len(midpoint_eigenvalues) != len(hermitian_enclosure):
        raise ValueError("Midpoint eigenvalue count differs from sector dimension.")
    ctx.prec = int(precision_bits)
    shifted = shift_hermitian(hermitian_enclosure, _exact_arb_from_float64(float(threshold)))
    transformed = exact_congruence_enclosure(shifted, rounded_q)
    attempts = []
    schedule = deterministic_cluster_sizes(
        len(transformed), seed_size=seed_size, expansion_step=expansion_step,
        maximum_size=maximum_cluster_size,
    )
    for size in schedule:
        if maximum_seconds is not None and time.perf_counter() - started >= maximum_seconds:
            break
        partition = deterministic_cluster_partition(
            midpoint_eigenvalues, threshold=float(threshold), cluster_size=size
        )
        remaining = None
        if maximum_seconds is not None:
            remaining = max(0.0, maximum_seconds - (time.perf_counter() - started))
        result = certify_clustered_inertia(
            transformed,
            far_indices=partition["far_indices"],
            cluster_indices=partition["cluster_indices"],
            precision_bits=int(precision_bits),
            maximum_seconds=remaining,
        )
        attempt = {"partition": partition, **result}
        attempts.append(attempt)
        if result["status"] == "CERTIFIED_CLUSTERED_INERTIA":
            return {
                "status": "CERTIFIED_FIXED_BASIS_INERTIA",
                "certified_support_count": int(result["n_positive"]),
                "basis": basis,
                "cluster_schedule": schedule,
                "accepted_cluster_size": size,
                "attempts": attempts,
                "runtime_seconds": time.perf_counter() - started,
                "failure_reason": None,
            }
    return {
        "status": "UNCERTIFIED_FIXED_BASIS_INERTIA",
        "certified_support_count": None,
        "basis": basis,
        "cluster_schedule": schedule,
        "accepted_cluster_size": None,
        "attempts": attempts,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": (
            "MAXIMUM_SECONDS" if maximum_seconds is not None
            and time.perf_counter() - started >= maximum_seconds
            else "CLUSTER_CAP_EXHAUSTED"
        ),
    }
