"""Validated threshold-shifted Hermitian inertia using block LDL* recursion.

The implementation uses only Arb/acb inclusion arithmetic.  Deterministic
pivot selection is a conditioning heuristic; every accepted sign, inverse,
Schur complement, and inertia conclusion is independently enclosed.  No
individual eigenvalue is isolated.
"""

from __future__ import annotations

import math
import time
from typing import Any, Sequence

from flint import acb, arb, ctx


def _text(value: arb, digits: int = 24) -> str:
    return value.str(digits, radius=False)


def _abs2(value: acb) -> arb:
    return value.real * value.real + value.imag * value.imag


def _abs_upper(value: acb) -> arb:
    return value.abs_upper()


def _max_entry_radius(matrix: Sequence[Sequence[acb]]) -> arb:
    maximum = arb(0)
    for row in matrix:
        for value in row:
            radius = value.real.rad() + value.imag.rad()
            if bool(radius > maximum):
                maximum = radius
    return maximum


def canonicalize_hermitian(values: Sequence[Sequence[acb]]) -> list[list[acb]]:
    """Intersect conjugate entries and return an explicitly Hermitian enclosure."""

    size = len(values)
    if size == 0 or any(len(row) != size for row in values):
        raise ValueError("Hermitian input must be a nonempty square matrix.")
    result = [[acb(0) for _ in range(size)] for _ in range(size)]
    for row in range(size):
        diagonal = values[row][row]
        if not diagonal.imag.contains(0):
            raise ValueError(f"Diagonal entry {row} is not Hermitian.")
        result[row][row] = acb(diagonal.real, 0)
        for column in range(row + 1, size):
            upper = values[row][column]
            lower_conjugate = values[column][row].conjugate()
            try:
                real = upper.real.intersection(lower_conjugate.real)
                imag = upper.imag.intersection(lower_conjugate.imag)
            except ValueError as error:
                raise ValueError(f"Entries ({row},{column}) are not Hermitian enclosures.") from error
            result[row][column] = acb(real, imag)
            result[column][row] = result[row][column].conjugate()
    return result


def shift_hermitian(values: Sequence[Sequence[acb]], threshold: arb) -> list[list[acb]]:
    result = canonicalize_hermitian(values)
    for index in range(len(result)):
        result[index][index] -= threshold
    return canonicalize_hermitian(result)


def _permuted(matrix: list[list[acb]], order: list[int]) -> list[list[acb]]:
    return [[matrix[row][column] for column in order] for row in order]


def _scalar_candidate(matrix: list[list[acb]], index: int) -> dict[str, Any] | None:
    diagonal = matrix[index][index].real
    if bool(diagonal.lower() > 0):
        sign = "POSITIVE"
        margin = diagonal.lower()
    elif bool(diagonal.upper() < 0):
        sign = "NEGATIVE"
        margin = -diagonal.upper()
    else:
        return None
    row_scale = max((_abs_upper(value) for value in matrix[index]), default=arb(1))
    if not bool(row_scale > 0):
        return None
    quality = float(margin / row_scale)
    return {
        "size": 1,
        "indices": [index],
        "signs": (1, 0) if sign == "POSITIVE" else (0, 1),
        "margin": margin,
        "quality": quality,
        "diagonal": diagonal,
    }


def _block_candidate(matrix: list[list[acb]], first: int, second: int) -> dict[str, Any] | None:
    a = matrix[first][first].real
    c = matrix[second][second].real
    b = matrix[first][second]
    determinant = a * c - _abs2(b)
    trace = a + c
    if bool(determinant.upper() < 0):
        signs = (1, 1)
        determinant_margin = -determinant.upper()
    elif bool(determinant.lower() > 0) and bool(trace.lower() > 0):
        signs = (2, 0)
        determinant_margin = determinant.lower()
    elif bool(determinant.lower() > 0) and bool(trace.upper() < 0):
        signs = (0, 2)
        determinant_margin = determinant.lower()
    else:
        return None

    block_norm_upper = max(
        (abs(a).upper() + _abs_upper(b)).upper(),
        (abs(c).upper() + _abs_upper(b)).upper(),
    )
    if not bool(block_norm_upper > 0):
        return None
    eigenvalue_margin = (determinant_margin / block_norm_upper).lower()
    scale_squared = block_norm_upper * block_norm_upper
    quality = float(determinant_margin / scale_squared)
    return {
        "size": 2,
        "indices": [first, second],
        "signs": signs,
        "margin": eigenvalue_margin,
        "quality": quality,
        "a": a,
        "b": b,
        "c": c,
        "determinant": determinant,
        "trace": trace,
    }


def _choose_pivot(matrix: list[list[acb]]) -> tuple[dict[str, Any] | None, dict[str, int]]:
    candidates: list[dict[str, Any]] = []
    rejected = {"scalar_uncertified": 0, "block_uncertified": 0}
    size = len(matrix)
    for index in range(size):
        candidate = _scalar_candidate(matrix, index)
        if candidate is None:
            rejected["scalar_uncertified"] += 1
        else:
            candidates.append(candidate)
    for first in range(size):
        for second in range(first + 1, size):
            candidate = _block_candidate(matrix, first, second)
            if candidate is None:
                rejected["block_uncertified"] += 1
            else:
                candidates.append(candidate)
    if not candidates:
        return None, rejected
    candidates.sort(key=lambda row: (row["quality"], row["size"]), reverse=True)
    return candidates[0], rejected


def _scalar_schur(matrix: list[list[acb]]) -> list[list[acb]]:
    size = len(matrix)
    inverse = arb(1) / matrix[0][0].real
    result = [[acb(0) for _ in range(size - 1)] for _ in range(size - 1)]
    for row in range(1, size):
        for column in range(1, size):
            result[row - 1][column - 1] = (
                matrix[row][column]
                - matrix[row][0] * inverse * matrix[0][column]
            )
    return canonicalize_hermitian(result) if result else []


def _block_schur(matrix: list[list[acb]]) -> list[list[acb]]:
    size = len(matrix)
    a = matrix[0][0].real
    b = matrix[0][1]
    c = matrix[1][1].real
    determinant = a * c - _abs2(b)
    inverse = [
        [acb(c / determinant), -b / determinant],
        [-b.conjugate() / determinant, acb(a / determinant)],
    ]
    result = [[acb(0) for _ in range(size - 2)] for _ in range(size - 2)]
    for row in range(2, size):
        for column in range(2, size):
            correction = acb(0)
            for left in range(2):
                for right in range(2):
                    correction += matrix[row][left] * inverse[left][right] * matrix[right][column]
            result[row - 2][column - 2] = matrix[row][column] - correction
    return canonicalize_hermitian(result) if result else []


def verified_block_ldl_inertia(
    values: Sequence[Sequence[acb]],
    *,
    precision_bits: int,
    maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Return a fail-closed verified inertia certificate for a Hermitian family."""

    ctx.prec = int(precision_bits)
    started = time.perf_counter()
    matrix = canonicalize_hermitian(values)
    labels = list(range(len(matrix)))
    positive = 0
    negative = 0
    pivot_rows = []
    minimum_margin: arb | None = None

    while matrix:
        if maximum_seconds is not None and time.perf_counter() - started >= maximum_seconds:
            return {
                "status": "UNCERTIFIED_RESOURCE_LIMIT",
                "n_positive": positive,
                "n_negative": negative,
                "n_zero_or_unresolved": len(matrix),
                "precision_bits": int(precision_bits),
                "minimum_certified_signed_margin": _text(minimum_margin) if minimum_margin is not None else None,
                "unresolved_block_size": len(matrix),
                "pivot_rows": pivot_rows,
                "runtime_seconds": time.perf_counter() - started,
                "failure_reason": "MAXIMUM_SECONDS",
            }
        radius_before = _max_entry_radius(matrix)
        pivot, rejected = _choose_pivot(matrix)
        if pivot is None:
            return {
                "status": "UNCERTIFIED_PIVOT",
                "n_positive": positive,
                "n_negative": negative,
                "n_zero_or_unresolved": len(matrix),
                "precision_bits": int(precision_bits),
                "minimum_certified_signed_margin": _text(minimum_margin) if minimum_margin is not None else None,
                "unresolved_block_size": len(matrix),
                "pivot_rows": pivot_rows,
                "runtime_seconds": time.perf_counter() - started,
                "failure_reason": "NO_SIGN_CERTIFIABLE_1X1_OR_2X2_PRINCIPAL_PIVOT",
                "rejected_candidates": rejected,
            }

        selected = pivot["indices"]
        order = selected + [index for index in range(len(matrix)) if index not in selected]
        matrix = _permuted(matrix, order)
        labels = [labels[index] for index in order]
        positive += int(pivot["signs"][0])
        negative += int(pivot["signs"][1])
        if minimum_margin is None or bool(pivot["margin"] < minimum_margin):
            minimum_margin = pivot["margin"]
        diagnostic: dict[str, Any] = {
            "step": len(pivot_rows),
            "block_size": int(pivot["size"]),
            "original_indices": labels[:pivot["size"]],
            "positive_contribution": int(pivot["signs"][0]),
            "negative_contribution": int(pivot["signs"][1]),
            "certified_eigenvalue_margin_lower": _text(pivot["margin"]),
            "selection_quality": pivot["quality"],
            "maximum_entry_radius_before": _text(radius_before),
            "rejected_candidates": rejected,
        }
        if pivot["size"] == 1:
            diagnostic["diagonal_lower"] = _text(pivot["diagonal"].lower())
            diagnostic["diagonal_upper"] = _text(pivot["diagonal"].upper())
            matrix = _scalar_schur(matrix)
        else:
            diagnostic.update({
                "determinant_lower": _text(pivot["determinant"].lower()),
                "determinant_upper": _text(pivot["determinant"].upper()),
                "trace_lower": _text(pivot["trace"].lower()),
                "trace_upper": _text(pivot["trace"].upper()),
            })
            matrix = _block_schur(matrix)
        labels = labels[pivot["size"]:]
        diagnostic["maximum_entry_radius_after"] = _text(_max_entry_radius(matrix)) if matrix else "0"
        pivot_rows.append(diagnostic)

    return {
        "status": "CERTIFIED_INERTIA",
        "n_positive": positive,
        "n_negative": negative,
        "n_zero_or_unresolved": 0,
        "precision_bits": int(precision_bits),
        "minimum_certified_signed_margin": _text(minimum_margin) if minimum_margin is not None else None,
        "unresolved_block_size": 0,
        "pivot_rows": pivot_rows,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": None,
    }


def aggregate_sector_inertias(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    certified = all(row["status"] == "CERTIFIED_INERTIA" for row in rows)
    margins = [row["minimum_certified_signed_margin"] for row in rows
               if row.get("minimum_certified_signed_margin") is not None]
    return {
        "status": "CERTIFIED_INERTIA" if certified else "UNCERTIFIED",
        "n_positive": sum(int(row["n_positive"]) for row in rows),
        "n_negative": sum(int(row["n_negative"]) for row in rows),
        "n_zero_or_unresolved": sum(int(row["n_zero_or_unresolved"]) for row in rows),
        "minimum_certified_signed_margin": min(margins, key=float) if margins else None,
        "sector_rows": list(rows),
    }
