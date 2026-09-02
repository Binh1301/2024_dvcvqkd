"""Deterministic sign-homogeneous sequential Schur reduction for V3.

Midpoint eigenvalues select only a deterministic work order.  Every accepted
far block is independently proved positive or negative by validated inertia,
and every coupling is retained in an inclusion Schur complement.  Unproved
far labels remain explicit in the final residual diagnostics.
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable, Sequence

from flint import acb, acb_mat, arb, ctx

from .rigorous_shifted_inertia import canonicalize_hermitian, verified_block_ldl_inertia


Matrix = list[list[acb]]


def deterministic_signed_partition(
    midpoint_eigenvalues: Sequence[float],
    *,
    threshold: float,
    near_size: int,
) -> dict[str, Any]:
    """Partition labels into near, far-positive, and far-negative sets.

    The midpoint partition is a scheduling heuristic only.  It never proves a
    sign.  Ties are broken by original index and far queues are farthest first.
    """

    values = [float(value) for value in midpoint_eigenvalues]
    if not values or not math.isfinite(float(threshold)) or not all(map(math.isfinite, values)):
        raise ValueError("Midpoint values and threshold must be finite and nonempty.")
    if near_size <= 0 or near_size > len(values):
        raise ValueError("near_size must lie in [1, dimension].")
    nearest_order = sorted(
        range(len(values)), key=lambda index: (abs(values[index] - threshold), index)
    )
    near = set(nearest_order[:near_size])
    # An exact midpoint tie with the threshold has no diagnostic sign and must
    # stay in the residual even if it exceeds the requested seed size.
    near.update(index for index, value in enumerate(values) if value == threshold)
    positive = [index for index, value in enumerate(values)
                if index not in near and value > threshold]
    negative = [index for index, value in enumerate(values)
                if index not in near and value < threshold]
    positive.sort(key=lambda index: (-(values[index] - threshold), index))
    negative.sort(key=lambda index: (-(threshold - values[index]), index))
    near_order = [index for index in nearest_order if index in near]
    return {
        "rule": "NEAR_ABSOLUTE_DISTANCE_THEN_FAR_SIGN_AND_DESCENDING_CLEARANCE",
        "midpoint_labels_are_diagnostic_only": True,
        "near_indices": near_order,
        "far_positive_indices": positive,
        "far_negative_indices": negative,
        "requested_near_size": int(near_size),
        "actual_near_size": len(near_order),
    }


def _principal(values: Sequence[Sequence[acb]], indices: Sequence[int]) -> Matrix:
    return [[values[row][column] for column in indices] for row in indices]


def _rectangular(
    values: Sequence[Sequence[acb]], rows: Sequence[int], columns: Sequence[int],
) -> Matrix:
    return [[values[row][column] for column in columns] for row in rows]


def _as_mat(values: Sequence[Sequence[acb]]) -> acb_mat:
    return acb_mat([[value for value in row] for row in values])


def _as_lists(values: acb_mat) -> Matrix:
    return [[values[row, column] for column in range(values.ncols())]
            for row in range(values.nrows())]


def _compact_inertia(result: dict[str, Any]) -> dict[str, Any]:
    pivots = result.get("pivot_rows", [])
    return {key: value for key, value in result.items() if key != "pivot_rows"} | {
        "pivot_count": len(pivots),
        "scalar_pivot_count": sum(row["block_size"] == 1 for row in pivots),
        "block_2x2_pivot_count": sum(row["block_size"] == 2 for row in pivots),
    }


def _remaining_seconds(started: float, maximum_seconds: float | None) -> float | None:
    if maximum_seconds is None:
        return None
    return max(0.0, maximum_seconds - (time.perf_counter() - started))


def _solve_diagnostics(a: acb_mat, x: acb_mat, e: acb_mat) -> dict[str, Any]:
    residual = a * x - e
    count = residual.nrows() * residual.ncols()
    contains_zero = 0
    maximum_abs = arb(0)
    maximum_radius = arb(0)
    finite = True
    for row in range(residual.nrows()):
        for column in range(residual.ncols()):
            value = residual[row, column]
            contains_zero += int(value.contains(0))
            finite = finite and bool(value.is_finite())
            maximum_abs = max(maximum_abs, value.abs_upper(), key=float)
            radius = value.real.rad() + value.imag.rad()
            maximum_radius = max(maximum_radius, radius, key=float)
    solution_finite = all(
        bool(x[row, column].is_finite())
        for row in range(x.nrows()) for column in range(x.ncols())
    )
    return {
        "method": "PYTHON_FLINT_ACB_MAT_VALIDATED_SOLVE_PRECOND",
        "entry_count": count,
        "residual_entries_containing_zero": contains_zero,
        "all_residual_entries_contain_zero": contains_zero == count,
        "all_solution_and_residual_entries_finite": finite and solution_finite,
        "maximum_residual_abs_upper": maximum_abs.str(24, radius=False),
        "maximum_residual_component_radius": maximum_radius.str(24, radius=False),
    }


def validated_signed_schur_step(
    values: Sequence[Sequence[acb]],
    *,
    block_indices: Sequence[int],
    expected_sign: str,
    precision_bits: int,
    maximum_seconds: float | None = None,
) -> dict[str, Any]:
    """Prove and eliminate one positive- or negative-definite principal block."""

    started = time.perf_counter()
    ctx.prec = int(precision_bits)
    matrix = canonicalize_hermitian(values)
    dimension = len(matrix)
    block = list(block_indices)
    if expected_sign not in {"POSITIVE", "NEGATIVE"}:
        raise ValueError("expected_sign must be POSITIVE or NEGATIVE.")
    if not block or len(set(block)) != len(block) or any(
        index < 0 or index >= dimension for index in block
    ):
        raise ValueError("block_indices must be distinct valid current positions.")
    remaining = [index for index in range(dimension) if index not in set(block)]
    block_values = canonicalize_hermitian(_principal(matrix, block))
    inertia_full = verified_block_ldl_inertia(
        block_values,
        precision_bits=int(precision_bits),
        maximum_seconds=_remaining_seconds(started, maximum_seconds),
    )
    inertia = _compact_inertia(inertia_full)
    wanted_positive = len(block) if expected_sign == "POSITIVE" else 0
    wanted_negative = len(block) if expected_sign == "NEGATIVE" else 0
    sign_certified = (
        inertia_full["status"] == "CERTIFIED_INERTIA"
        and int(inertia_full["n_positive"]) == wanted_positive
        and int(inertia_full["n_negative"]) == wanted_negative
        and int(inertia_full["n_zero_or_unresolved"]) == 0
    )
    if not sign_certified:
        return {
            "status": "UNCERTIFIED_SIGN_BLOCK",
            "expected_sign": expected_sign,
            "block_indices": block,
            "remaining_indices": remaining,
            "block_inertia": inertia,
            "solve": None,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "BLOCK_NOT_CERTIFIED_SIGN_HOMOGENEOUS",
        }
    if not remaining:
        return {
            "status": "CERTIFIED_SIGNED_SCHUR_STEP",
            "expected_sign": expected_sign,
            "block_indices": block,
            "remaining_indices": [],
            "block_inertia": inertia,
            "solve": {"method": "EMPTY_REMAINDER", "entry_count": 0},
            "schur_complement": [],
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": None,
        }

    a = _as_mat(block_values)
    e_values = _rectangular(matrix, block, remaining)
    e = _as_mat(e_values)
    d = _as_mat(canonicalize_hermitian(_principal(matrix, remaining)))
    try:
        solution = a.solve(e, algorithm="precond")
        solve = _solve_diagnostics(a, solution, e)
    except (ValueError, ZeroDivisionError, RuntimeError) as error:
        return {
            "status": "UNCERTIFIED_SIGNED_SOLVE",
            "expected_sign": expected_sign,
            "block_indices": block,
            "remaining_indices": remaining,
            "block_inertia": inertia,
            "solve": {"method": "PYTHON_FLINT_ACB_MAT_VALIDATED_SOLVE_PRECOND",
                      "exception": str(error)},
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "VALIDATED_SOLVE_FAILED",
        }
    if not (solve["all_residual_entries_contain_zero"]
            and solve["all_solution_and_residual_entries_finite"]):
        return {
            "status": "UNCERTIFIED_SIGNED_SOLVE",
            "expected_sign": expected_sign,
            "block_indices": block,
            "remaining_indices": remaining,
            "block_inertia": inertia,
            "solve": solve,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "SOLVE_ENCLOSURE_DIAGNOSTICS_FAILED",
        }
    e_star = _as_mat([[e_values[row][column].conjugate()
                       for row in range(len(e_values))]
                      for column in range(len(e_values[0]))])
    try:
        schur = canonicalize_hermitian(_as_lists(d - e_star * solution))
    except ValueError:
        return {
            "status": "UNCERTIFIED_SCHUR_HERMITICITY",
            "expected_sign": expected_sign,
            "block_indices": block,
            "remaining_indices": remaining,
            "block_inertia": inertia,
            "solve": solve,
            "schur_complement": None,
            "runtime_seconds": time.perf_counter() - started,
            "failure_reason": "SCHUR_CONJUGATE_ENCLOSURES_DO_NOT_INTERSECT",
        }
    return {
        "status": "CERTIFIED_SIGNED_SCHUR_STEP",
        "expected_sign": expected_sign,
        "block_indices": block,
        "remaining_indices": remaining,
        "block_inertia": inertia,
        "solve": solve,
        "schur_complement": schur,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": None,
    }


def sequential_signed_schur_reduction(
    values: Sequence[Sequence[acb]],
    *,
    midpoint_eigenvalues: Sequence[float],
    threshold: float,
    near_size: int,
    block_sizes: Sequence[int],
    precision_bits: int,
    sign_groups: Sequence[str] = ("POSITIVE", "NEGATIVE"),
    maximum_residual_dimension: int | None = None,
    maximum_rounds: int | None = None,
    maximum_seconds: float | None = None,
    elimination_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run a frozen-schedule-ready adaptive sequence of signed eliminations.

    Failed blocks are retried at smaller frozen sizes.  A failed singleton is
    deferred, not counted.  Before every block attempt, the next sign is the
    queue whose head has greatest absolute shifted midpoint distance, with
    POSITIVE first on an exact cross-sign tie and original index as the final
    tie breaker.  Deferred labels are retried in a later round after other
    successful eliminations have changed the Schur complement.  If a complete
    round makes no progress, every remaining far label stays explicit in the
    final residual.
    """

    started = time.perf_counter()
    matrix = canonicalize_hermitian(values)
    dimension = len(matrix)
    if len(midpoint_eigenvalues) != dimension:
        raise ValueError("Midpoint eigenvalue count must equal matrix dimension.")
    schedule = [int(value) for value in block_sizes]
    if (not schedule or any(value <= 0 for value in schedule)
            or schedule != sorted(set(schedule), reverse=True) or schedule[-1] != 1):
        raise ValueError("block_sizes must be unique descending positive integers ending in 1.")
    signs = tuple(sign_groups)
    if len(signs) != 2 or set(signs) != {"POSITIVE", "NEGATIVE"}:
        raise ValueError("sign_groups must contain POSITIVE and NEGATIVE exactly once.")
    partition = deterministic_signed_partition(
        midpoint_eigenvalues, threshold=float(threshold), near_size=int(near_size)
    )
    pending = {
        "POSITIVE": list(partition["far_positive_indices"]),
        "NEGATIVE": list(partition["far_negative_indices"]),
    }
    labels = list(range(dimension))
    steps: list[dict[str, Any]] = []
    certified_positive = 0
    certified_negative = 0
    rounds = int(maximum_rounds) if maximum_rounds is not None else dimension
    resource_limited = False

    for round_index in range(rounds):
        progress = False
        active = {
            sign: [label for label in pending[sign] if label in labels]
            for sign in signs
        }
        while any(active.values()):
            if maximum_seconds is not None and time.perf_counter() - started >= maximum_seconds:
                resource_limited = True
                break
            available_signs = [sign for sign in signs if active[sign]]

            def candidate_key(sign: str) -> tuple[float, int, int]:
                label = active[sign][0]
                distance = abs(float(midpoint_eigenvalues[label]) - float(threshold))
                sign_priority = 0 if sign == "POSITIVE" else 1
                return (-distance, sign_priority, label)

            sign = min(available_signs, key=candidate_key)
            head_label = active[sign][0]
            head_distance = abs(
                float(midpoint_eigenvalues[head_label]) - float(threshold)
            )
            accepted = None
            attempted_sizes = [size for size in schedule if size <= len(active[sign])]
            for size in attempted_sizes:
                block_labels = active[sign][:size]
                positions = [labels.index(label) for label in block_labels]
                step = validated_signed_schur_step(
                    matrix,
                    block_indices=positions,
                    expected_sign=sign,
                    precision_bits=int(precision_bits),
                    maximum_seconds=_remaining_seconds(started, maximum_seconds),
                )
                public = {key: value for key, value in step.items()
                          if key != "schur_complement"}
                public.update({
                    "round": round_index,
                    "candidate_selection_rule": (
                        "GREATEST_ABSOLUTE_SHIFTED_MIDPOINT_DISTANCE_THEN_"
                        "POSITIVE_THEN_ORIGINAL_INDEX"
                    ),
                    "candidate_head_label": head_label,
                    "candidate_head_distance": head_distance,
                    "attempted_block_size": size,
                    "original_labels": block_labels,
                    "dimension_before": len(labels),
                    "accepted": step["status"] == "CERTIFIED_SIGNED_SCHUR_STEP",
                })
                steps.append(public)
                if step["status"] == "CERTIFIED_SIGNED_SCHUR_STEP":
                    accepted = (step, block_labels)
                    break
            if accepted is None:
                # Do not count the uncertified head.  Other active heads may
                # still be rigorously eliminable in this round.
                active[sign].pop(0)
                continue
            step, block_labels = accepted
            removed = set(block_labels)
            labels = [label for label in labels if label not in removed]
            matrix = step["schur_complement"]
            active[sign] = [label for label in active[sign] if label not in removed]
            pending[sign] = [label for label in pending[sign] if label not in removed]
            if sign == "POSITIVE":
                certified_positive += len(block_labels)
            else:
                certified_negative += len(block_labels)
            steps[-1]["dimension_after"] = len(labels)
            if elimination_callback is not None:
                elimination_callback(dict(steps[-1]))
            progress = True
        if resource_limited or not progress:
            break

    unresolved_positive = [label for label in pending["POSITIVE"] if label in labels]
    unresolved_negative = [label for label in pending["NEGATIVE"] if label in labels]
    residual_inertia = None
    failure_reason = None
    if resource_limited:
        failure_reason = "MAXIMUM_SECONDS"
    elif maximum_residual_dimension is not None and len(labels) > maximum_residual_dimension:
        failure_reason = "RESIDUAL_DIMENSION_LIMIT"
    elif labels:
        residual_full = verified_block_ldl_inertia(
            matrix,
            precision_bits=int(precision_bits),
            maximum_seconds=_remaining_seconds(started, maximum_seconds),
        )
        residual_inertia = _compact_inertia(residual_full)
        if residual_full["status"] == "CERTIFIED_INERTIA":
            certified_positive += int(residual_full["n_positive"])
            certified_negative += int(residual_full["n_negative"])
        else:
            failure_reason = "RESIDUAL_INERTIA_UNCERTIFIED"
    certified = (
        failure_reason is None
        and certified_positive + certified_negative == dimension
    )
    return {
        "status": "CERTIFIED_SEQUENTIAL_INERTIA" if certified else "UNCERTIFIED_SEQUENTIAL_INERTIA",
        "n_positive": certified_positive if certified else None,
        "n_negative": certified_negative if certified else None,
        "n_zero_or_unresolved": 0 if certified else len(labels),
        "partition": partition,
        "block_schedule": schedule,
        "sign_groups": list(signs),
        "cross_sign_candidate_order": (
            "GREATEST_ABSOLUTE_SHIFTED_MIDPOINT_DISTANCE_THEN_"
            "POSITIVE_THEN_ORIGINAL_INDEX"
        ),
        "steps": steps,
        "successful_schur_count": sum(step["accepted"] for step in steps),
        "sequential_certified_positive": sum(
            len(step["original_labels"]) for step in steps
            if step["accepted"] and step["expected_sign"] == "POSITIVE"
        ),
        "sequential_certified_negative": sum(
            len(step["original_labels"]) for step in steps
            if step["accepted"] and step["expected_sign"] == "NEGATIVE"
        ),
        "residual_original_labels": labels,
        "final_reduced_dimension": len(labels),
        "unresolved_far_positive_indices": unresolved_positive,
        "unresolved_far_negative_indices": unresolved_negative,
        "residual_inertia": residual_inertia,
        "all_couplings_accounted_by_schur_updates": True,
        "midpoint_partition_used_for_proof": False,
        "runtime_seconds": time.perf_counter() - started,
        "failure_reason": failure_reason,
    }


__all__ = [
    "deterministic_signed_partition",
    "sequential_signed_schur_reduction",
    "validated_signed_schur_step",
]
