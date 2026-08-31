"""Whole-segment support certification from interval radii and shifted inertia."""

from __future__ import annotations

from fractions import Fraction
import time
from typing import Any, Callable

from flint import acb, arb, ctx

from .rigorous_flint_support import (
    BallTransmitterPath,
    exact_arb_from_fraction,
    fraction_ball,
)
from .rigorous_shifted_inertia import shift_hermitian, verified_block_ldl_inertia


def _text(value: arb, digits: int = 24) -> str:
    return value.str(digits, radius=False)


def frobenius_perturbation_upper(interval_matrix, midpoint_matrix) -> arb:
    total = arb(0)
    for interval_row, midpoint_row in zip(interval_matrix, midpoint_matrix):
        for interval_value, midpoint_value in zip(interval_row, midpoint_row):
            upper = (interval_value - midpoint_value).abs_upper()
            total += upper * upper
    return total.sqrt().upper()


def certify_sector_guard_band(midpoint_sector, rho: arb, threshold: arb, *,
                              precision_bits: int, maximum_seconds: float | None = None) -> dict[str, Any]:
    """Use Weyl plus two verified inertias to certify threshold support."""

    started = time.perf_counter()
    lower_shift = threshold - rho
    upper_shift = threshold + rho
    lower_result = verified_block_ldl_inertia(
        shift_hermitian(midpoint_sector, lower_shift),
        precision_bits=precision_bits,
        maximum_seconds=maximum_seconds,
    )
    remaining = None
    if maximum_seconds is not None:
        remaining = max(0.0, maximum_seconds - (time.perf_counter() - started))
    upper_result = verified_block_ldl_inertia(
        shift_hermitian(midpoint_sector, upper_shift),
        precision_bits=precision_bits,
        maximum_seconds=remaining,
    )
    both_certified = (
        lower_result["status"] == "CERTIFIED_INERTIA"
        and upper_result["status"] == "CERTIFIED_INERTIA"
    )
    same_count = both_certified and lower_result["n_positive"] == upper_result["n_positive"]
    margins = [
        row["minimum_certified_signed_margin"]
        for row in (lower_result, upper_result)
        if row.get("minimum_certified_signed_margin") is not None
    ]
    def compact(result: dict[str, Any]) -> dict[str, Any]:
        pivots = result.get("pivot_rows", [])
        return {
            key: value for key, value in result.items() if key != "pivot_rows"
        } | {
            "pivot_count": len(pivots),
            "scalar_pivot_count": sum(row["block_size"] == 1 for row in pivots),
            "block_2x2_pivot_count": sum(row["block_size"] == 2 for row in pivots),
        }
    return {
        "status": "CERTIFIED_FIXED_INERTIA" if same_count else "UNRESOLVED",
        "rho_frobenius_upper": _text(rho),
        "lower_shift_tau_minus_rho": _text(lower_shift),
        "upper_shift_tau_plus_rho": _text(upper_shift),
        "n_positive_at_lower_shift": lower_result["n_positive"] if lower_result["status"] == "CERTIFIED_INERTIA" else None,
        "n_positive_at_upper_shift": upper_result["n_positive"] if upper_result["status"] == "CERTIFIED_INERTIA" else None,
        "certified_support_count": lower_result["n_positive"] if same_count else None,
        "n_zero_or_unresolved": (
            int(lower_result["n_zero_or_unresolved"])
            + int(upper_result["n_zero_or_unresolved"])
        ),
        "minimum_certified_signed_margin": min(margins, key=float) if margins else None,
        "lower_shift_inertia": compact(lower_result),
        "upper_shift_inertia": compact(upper_result),
        "runtime_seconds": time.perf_counter() - started,
        "zero_included_proves_crossing": False,
    }


def evaluate_path_interval(path: BallTransmitterPath, left: Fraction, right: Fraction, *,
                           threshold: arb, precision_schedule: list[int],
                           maximum_seconds: float) -> dict[str, Any]:
    started = time.perf_counter()
    midpoint = (left + right) / 2
    attempts = []
    for bits in precision_schedule:
        if time.perf_counter() - started >= maximum_seconds:
            break
        ctx.prec = int(bits)
        interval_sectors = path.sectors(fraction_ball(left, right))
        midpoint_sectors = path.sectors(exact_arb_from_fraction(midpoint))
        sector_rows = []
        for sector_index, (interval_sector, midpoint_sector) in enumerate(
            zip(interval_sectors, midpoint_sectors)
        ):
            rho = frobenius_perturbation_upper(interval_sector, midpoint_sector)
            remaining = max(0.0, maximum_seconds - (time.perf_counter() - started))
            result = certify_sector_guard_band(
                midpoint_sector, rho, threshold,
                precision_bits=int(bits), maximum_seconds=remaining,
            )
            sector_rows.append({"sector": sector_index, **result})
            if result["status"] != "CERTIFIED_FIXED_INERTIA":
                break
        support = sum(int(row["certified_support_count"]) for row in sector_rows
                      if row["certified_support_count"] is not None)
        fixed = len(sector_rows) == 4 and all(
            row["status"] == "CERTIFIED_FIXED_INERTIA" for row in sector_rows
        )
        attempt = {
            "precision_bits": int(bits),
            "status": "CERTIFIED_FIXED_INERTIA" if fixed else "UNRESOLVED",
            "certified_support_count": support if fixed else None,
            "unresolved_block_size": sum(int(row["n_zero_or_unresolved"]) for row in sector_rows),
            "sector_rows": sector_rows,
        }
        attempts.append(attempt)
        if fixed:
            return {
                "left": f"{left.numerator}/{left.denominator}",
                "right": f"{right.numerator}/{right.denominator}",
                "midpoint": f"{midpoint.numerator}/{midpoint.denominator}",
                **attempt,
                "attempts": attempts,
                "runtime_seconds": time.perf_counter() - started,
            }
    last = attempts[-1] if attempts else None
    return {
        "left": f"{left.numerator}/{left.denominator}",
        "right": f"{right.numerator}/{right.denominator}",
        "midpoint": f"{midpoint.numerator}/{midpoint.denominator}",
        "precision_bits": last["precision_bits"] if last else None,
        "status": "UNRESOLVED",
        "certified_support_count": None,
        "unresolved_block_size": last["unresolved_block_size"] if last else 256,
        "sector_rows": last["sector_rows"] if last else [],
        "attempts": attempts,
        "runtime_seconds": time.perf_counter() - started,
    }


def certify_interval_tree(
    evaluator: Callable[[Fraction, Fraction], dict[str, Any]], *,
    start_rank: int, end_rank: int, maximum_depth: int, minimum_width: Fraction,
    maximum_nodes: int, maximum_seconds: float,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    if start_rank != end_rank:
        return {
            "status": "RIGOROUS_ENDPOINT_INERTIA_CROSSING",
            "start_rank": start_rank,
            "end_rank": end_rank,
            "nodes": [],
            "runtime_seconds": time.perf_counter() - started,
        }
    pending = [(Fraction(0), Fraction(1), 0)]
    accepted = []
    unresolved = []
    nodes = []
    maximum_depth_reached = 0
    while pending:
        if len(nodes) >= maximum_nodes or time.perf_counter() - started >= maximum_seconds:
            unresolved.extend({
                "left": str(left), "right": str(right), "depth": depth,
                "leaf_state": "UNCERTIFIED_RESOURCE_LIMIT",
            } for left, right, depth in pending)
            break
        left, right, depth = pending.pop()
        maximum_depth_reached = max(maximum_depth_reached, depth)
        result = evaluator(left, right)
        result["depth"] = depth
        nodes.append(result)
        if progress is not None:
            progress(result)
        if result["status"] == "CERTIFIED_FIXED_INERTIA":
            if int(result["certified_support_count"]) != start_rank:
                result["leaf_state"] = "UNCERTIFIED_INCONSISTENT_FIXED_INERTIA"
                unresolved.append(result)
            else:
                result["leaf_state"] = "CERTIFIED_FIXED_INERTIA"
                accepted.append(result)
            continue
        width = right - left
        if depth >= maximum_depth or width <= minimum_width:
            result["leaf_state"] = "UNCERTIFIED_RESOURCE_LIMIT"
            unresolved.append(result)
            continue
        middle = (left + right) / 2
        pending.append((middle, right, depth + 1))
        pending.append((left, middle, depth + 1))
    if unresolved:
        status = "UNCERTIFIED_FAIL_CLOSED"
    else:
        status = "WHOLE_SEGMENT_FIXED_INERTIA_CERTIFIED"
    margins = [
        sector["minimum_certified_signed_margin"]
        for node in accepted for sector in node.get("sector_rows", [])
        if sector.get("minimum_certified_signed_margin") is not None
    ]
    return {
        "status": status,
        "start_rank": start_rank,
        "end_rank": end_rank,
        "accepted_leaf_count": len(accepted),
        "unresolved_leaf_count": len(unresolved),
        "maximum_depth_reached": maximum_depth_reached,
        "minimum_certified_signed_margin": min(margins, key=float) if margins else None,
        "nodes": nodes,
        "unresolved_leaves": unresolved,
        "runtime_seconds": time.perf_counter() - started,
    }
