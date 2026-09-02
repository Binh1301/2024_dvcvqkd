"""Arb/FLINT point certification for one realized physical ensemble.

This module is intentionally Torch-free so it can run in the isolated
certification environment.  NumPy eigenspectra are used only to propose a
dyadic bracket center; every support and bracket decision is made by validated
Arb shifted-Hermitian inertia.
"""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any, Sequence

import numpy as np
from flint import acb, arb, ctx

from .rigorous_shifted_inertia import aggregate_sector_inertias, shift_hermitian, verified_block_ldl_inertia
from .rigorous_flint_support import validated_eigenvalue_balls


I = acb(0, 1)


def exact_arb_from_float_hex(value: str) -> arb:
    binary = float.fromhex(value)
    if not math.isfinite(binary):
        raise ValueError("Certification values must be finite binary64 values.")
    numerator, denominator = binary.as_integer_ratio()
    if denominator & (denominator - 1):
        raise ValueError("Certification values must be exact binary64 dyadics.")
    return arb((numerator, -(denominator.bit_length() - 1)))


def dyadic_arb(numerator: int, denominator_power_two: int) -> arb:
    return arb((int(numerator), -int(denominator_power_two)))


def c4_orbit_indices() -> list[list[int]]:
    rows: list[list[int]] = []
    for real_index in range(8, 16):
        for imag_index in range(8, 16):
            a, b = real_index, imag_index
            rows.append([
                a * 16 + b,
                (15 - b) * 16 + a,
                (15 - a) * 16 + (15 - b),
                b * 16 + (15 - a),
            ])
    if len(rows) != 64 or len({index for row in rows for index in row}) != 256:
        raise ValueError("Failed to construct the frozen 256-state C4 partition.")
    return rows


def sectors_from_final_ensemble(
    probabilities: Sequence[float], amplitudes: Sequence[complex]
) -> list[list[list[acb]]]:
    if len(probabilities) != 256 or len(amplitudes) != 256:
        raise ValueError("A realized physical ensemble must contain 256 states.")
    orbits = c4_orbit_indices()
    p: list[arb] = []
    z: list[acb] = []
    for orbit in orbits:
        orbit_p = [float(probabilities[index]) for index in orbit]
        if any(value != orbit_p[0] for value in orbit_p):
            raise ValueError("Production probabilities are not exactly C4-tied.")
        orbit_z = [complex(amplitudes[index]) for index in orbit]
        for rotation, value in enumerate(orbit_z):
            expected = (1j ** rotation) * orbit_z[0]
            if value != expected:
                raise ValueError("Production amplitudes are not exactly C4-rotated.")
        p.append(exact_arb_from_float_hex(float(orbit_p[0]).hex()))
        z.append(acb(
            exact_arb_from_float_hex(float(orbit_z[0].real).hex()),
            exact_arb_from_float_hex(float(orbit_z[0].imag).hex()),
        ))
    rotations = [acb(1), I, acb(-1), -I]
    sectors: list[list[list[acb]]] = []
    for sector in range(4):
        raw = [[acb(0) for _ in range(64)] for _ in range(64)]
        for row in range(64):
            for column in range(64):
                root_probability = (p[row] * p[column]).sqrt()
                value = acb(0)
                for difference in range(4):
                    left, right = z[row], rotations[difference] * z[column]
                    left_energy = left.real * left.real + left.imag * left.imag
                    right_energy = right.real * right.real + right.imag * right.imag
                    overlap = (acb(-(left_energy + right_energy) / 2) + left.conjugate() * right).exp()
                    value += root_probability * overlap * (I ** (sector * difference))
                raw[row][column] = value
        sectors.append([[
            (raw[row][column] + raw[column][row].conjugate()) / 2
            for column in range(64)
        ] for row in range(64)])
    return sectors


def _midpoint_matrix(sector: Sequence[Sequence[acb]]) -> np.ndarray:
    return np.asarray([
        [complex(float(value.real.mid()), float(value.imag.mid())) for value in row]
        for row in sector
    ], dtype=np.complex128)


def _diagnostic_nearest(sectors: Sequence[Sequence[Sequence[acb]]], threshold: float) -> tuple[int, float, float]:
    values = np.concatenate([
        np.linalg.eigvalsh(0.5 * (matrix + matrix.conj().T))
        for matrix in (_midpoint_matrix(sector) for sector in sectors)
    ])
    below = values[values <= threshold]
    above = values[values > threshold]
    if below.size == 0 or above.size == 0:
        raise ValueError("Diagnostic spectrum has no eigenvalue on one side of tau.")
    return int(np.count_nonzero(values > threshold)), float(np.max(below)), float(np.min(above))


def _global_inward_eigenball_bounds(
    below_balls: Sequence[acb], above_balls: Sequence[acb]
) -> tuple[acb, acb, arb, arb]:
    """Return the balls attaining the global inward-facing rigorous endpoints."""

    if not below_balls or not above_balls:
        raise ValueError("A point certificate requires eigenvalues on both sides of tau.")
    below = below_balls[0]
    for candidate in below_balls[1:]:
        if bool(candidate.real.upper() > below.real.upper()):
            below = candidate
    above = above_balls[0]
    for candidate in above_balls[1:]:
        if bool(candidate.real.lower() < above.real.lower()):
            above = candidate
    return below, above, below.real.upper(), above.real.lower()


def _strict_separation_certificate(tau: arb, upper_below: arb, lower_above: arb) -> dict[str, Any]:
    """Decide strict separation using only rigorous Arb endpoints."""

    below_gap = (tau - upper_below).lower()
    above_gap = (lower_above - tau).lower()
    margin = below_gap if bool(below_gap <= above_gap) else above_gap
    if not bool(margin > 0):
        raise ValueError("Rigorous spectral distance from tau is not strictly positive.")
    return {
        "support_is_rigorously_certified": True,
        "strict_separation_certified": True,
        "certified_margin_lower_bound": margin.str(40, radius=False),
        "certified_margin_lower_bound_float": float(margin),
        "below_endpoint_upper": upper_below.str(40, radius=False),
        "above_endpoint_lower": lower_above.str(40, radius=False),
        "binary64_endpoint_role": "DIAGNOSTIC_ONLY_NOT_PROOF",
    }


def _certified_point_result(
    *, support_count: int, negative_count: int, precision_bits: int,
    lower_below: arb, upper_below: arb, lower_above: arb, upper_above: arb,
    tau: arb, diagnostic_support_count: int, bracket_source: str,
    protocol_version: str,
) -> dict[str, Any]:
    certificate = _strict_separation_certificate(tau, upper_below, lower_above)
    return {
        "schema_version": "pointwise-certifier-result-v2",
        "protocol_version": protocol_version,
        "status": "CERTIFIED_POINT",
        "support_count": int(support_count),
        "negative_count": int(negative_count),
        "precision_bits": int(precision_bits),
        "lower_nearest_below": float(lower_below),
        "upper_nearest_below": float(upper_below),
        "lower_nearest_above": float(lower_above),
        "upper_nearest_above": float(upper_above),
        "diagnostic_support_count": diagnostic_support_count,
        "diagnostic_role": "DIAGNOSTIC_ONLY_NOT_PROOF",
        "bracket_source": bracket_source,
        **certificate,
    }


def _certify_at(sectors: Sequence[Sequence[Sequence[acb]]], threshold: arb, bits: int, timeout: float) -> dict[str, Any]:
    ctx.prec = int(bits)
    rows = []
    for index, sector in enumerate(sectors):
        result = verified_block_ldl_inertia(
            shift_hermitian(sector, threshold), precision_bits=int(bits), maximum_seconds=timeout
        )
        rows.append({"sector": index, **result})
        if result["status"] != "CERTIFIED_INERTIA":
            break
    if len(rows) != 4:
        return {"status": "UNCERTIFIED", "n_positive": sum(row["n_positive"] for row in rows),
                "n_negative": sum(row["n_negative"] for row in rows),
                "n_zero_or_unresolved": sum(row["n_zero_or_unresolved"] for row in rows), "sector_rows": rows}
    aggregate = aggregate_sector_inertias(rows)
    return {"status": aggregate["status"], "n_positive": aggregate["n_positive"],
            "n_negative": aggregate["n_negative"], "n_zero_or_unresolved": aggregate["n_zero_or_unresolved"],
            "sector_rows": rows}


def _decimal_arb(value: float) -> arb:
    if not math.isfinite(value):
        raise ValueError("Bracket endpoint must be finite.")
    return arb(format(value, ".18e"))


def _validated_float_bracket(
    sectors: Sequence[Sequence[Sequence[acb]]], approximate: float, expected_negative: int,
    *, side: str, tau: arb, bits: int, timeout: float,
) -> dict[str, Any]:
    """Use fixed diagnostic-centered decimal candidates, then prove counts by Arb inertia."""

    for width in (1e-12, 1e-13, 1e-14, 1e-15, 1e-16):
        left_value, right_value = approximate - width, approximate + width
        left_candidate, right_candidate = _decimal_arb(left_value), _decimal_arb(right_value)
        if side == "BELOW":
            if not bool(right_candidate < tau):
                continue
            expected_left, expected_right = expected_negative - 1, expected_negative
        else:
            if not bool(left_candidate > tau):
                continue
            expected_left, expected_right = expected_negative, expected_negative + 1
        left = _certify_at(sectors, left_candidate, bits, timeout)
        right = _certify_at(sectors, right_candidate, bits, timeout)
        if (left["status"] == "CERTIFIED_INERTIA" and right["status"] == "CERTIFIED_INERTIA"
                and left["n_negative"] == expected_left and right["n_negative"] == expected_right):
            return {
                "status": "CERTIFIED_SINGLE_EIGENVALUE_BRACKET",
                "lower": left_value, "upper": right_value,
                "lower_text": format(left_value, ".18e"),
                "upper_text": format(right_value, ".18e"),
                "width": width,
                "_lower_arb": left_candidate,
                "_upper_arb": right_candidate,
            }
    return {"status": "UNCERTIFIED_EIGENVALUE_BRACKET"}


def _floor_dyadic(value: float, power: int) -> int:
    numerator, denominator = float(value).as_integer_ratio()
    return (numerator << power) // denominator


def _bracket(
    sectors: Sequence[Sequence[Sequence[acb]]], approximate: float, expected_negative: int,
    *, side: str, tau_numerator: int, tau_power: int, bits: int, timeout: float,
    maximum_expansions: int,
) -> dict[str, Any]:
    center = _floor_dyadic(approximate, tau_power)
    tau = dyadic_arb(tau_numerator, tau_power)
    for expansion_index in range(maximum_expansions + 1):
        expansion = (1 << expansion_index) - 1
        left_num = center - expansion
        right_num = center + 1 + expansion
        left = _certify_at(sectors, dyadic_arb(left_num, tau_power), bits, timeout)
        right = _certify_at(sectors, dyadic_arb(right_num, tau_power), bits, timeout)
        if left["status"] != "CERTIFIED_INERTIA" or right["status"] != "CERTIFIED_INERTIA":
            continue
        if side == "BELOW":
            accepted = left["n_negative"] == expected_negative - 1 and right["n_negative"] == expected_negative
        else:
            accepted = left["n_negative"] == expected_negative and right["n_negative"] == expected_negative + 1
        if not accepted:
            continue
        lower = dyadic_arb(left_num, tau_power)
        upper = dyadic_arb(right_num, tau_power)
        if side == "BELOW" and not bool(upper < tau):
            continue
        if side == "ABOVE" and not bool(lower > tau):
            continue
        return {
            "status": "CERTIFIED_SINGLE_EIGENVALUE_BRACKET",
            "lower": float(left_num / (1 << tau_power)),
            "upper": float(right_num / (1 << tau_power)),
            "lower_text": lower.str(30, radius=False),
            "upper_text": upper.str(30, radius=False),
            "expansion_index": expansion_index,
            "_lower_arb": lower,
            "_upper_arb": upper,
        }
    return {"status": "UNCERTIFIED_EIGENVALUE_BRACKET"}


def certify_final_ensemble_point(
    probabilities: Sequence[float], amplitudes: Sequence[complex],
    *, tau_float64_hex: str, precision_bits: Sequence[int] = (160, 256, 384, 512),
    # Binary64 diagnostic centers are only used to seed this grid.  The
    # validated inertia calls, not the center, decide the accepted bracket.
    bracket_denominator_power_two: int = 48, maximum_bracket_expansions: int = 8,
    maximum_seconds_per_inertia: float = 120.0,
    protocol_version: str = "pointwise-guard-v1",
) -> dict[str, Any]:
    """Return validated support and nearest-side brackets for one final ensemble."""

    tau_float = float.fromhex(tau_float64_hex)
    tau_num, tau_den = tau_float.as_integer_ratio()
    tau_power = tau_den.bit_length() - 1
    bracket_power = max(int(bracket_denominator_power_two), int(tau_power))
    bracket_tau_num = tau_num << (bracket_power - tau_power)
    ctx.prec = max(int(bits) for bits in precision_bits)
    sectors = sectors_from_final_ensemble(probabilities, amplitudes)
    diagnostic_support, approximate_below, approximate_above = _diagnostic_nearest(sectors, tau_float)
    last_debug: dict[str, Any] = {}
    for bits in precision_bits:
        ctx.prec = int(bits)
        sectors = sectors_from_final_ensemble(probabilities, amplitudes)
        try:
            tau_arb = dyadic_arb(tau_num, tau_power)
            balls = [
                value
                for sector in sectors
                for value in validated_eigenvalue_balls(
                    sector, precision_bits=int(bits), algorithms=["vdhoeven_mourrain", "rump"]
                )[0]
            ]
            below_balls = [value for value in balls if bool(value.real.upper() < tau_arb)]
            above_balls = [value for value in balls if bool(value.real.lower() > tau_arb)]
            if len(below_balls) + len(above_balls) == len(balls) and below_balls and above_balls:
                below, above, upper_below, lower_above = _global_inward_eigenball_bounds(
                    below_balls, above_balls
                )
                return _certified_point_result(
                    support_count=len(above_balls), negative_count=len(below_balls),
                    precision_bits=int(bits), lower_below=below.real.lower(),
                    upper_below=upper_below, lower_above=lower_above,
                    upper_above=above.real.upper(), tau=tau_arb,
                    diagnostic_support_count=diagnostic_support,
                    bracket_source="validated_Arb_eigenvalue_balls",
                    protocol_version=protocol_version,
                )
        except (ValueError, ArithmeticError, TypeError):
            pass
        at_tau = _certify_at(sectors, dyadic_arb(tau_num, tau_power), int(bits), maximum_seconds_per_inertia)
        last_debug = {"at_tau": at_tau, "bits": int(bits)}
        if at_tau["status"] != "CERTIFIED_INERTIA" or at_tau["n_zero_or_unresolved"] != 0:
            continue
        try:
            balls = [
                value
                for sector in sectors
                for value in validated_eigenvalue_balls(
                    sector, precision_bits=int(bits), algorithms=["vdhoeven_mourrain", "rump"]
                )[0]
            ]
            below_balls = [value for value in balls if bool(value.real.upper() < dyadic_arb(tau_num, tau_power))]
            above_balls = [value for value in balls if bool(value.real.lower() > dyadic_arb(tau_num, tau_power))]
            if len(below_balls) + len(above_balls) != len(balls) or not below_balls or not above_balls:
                raise ValueError("validated eigenvalue balls do not separate from tau")
            below, above, upper_below, lower_above = _global_inward_eigenball_bounds(
                below_balls, above_balls
            )
            return _certified_point_result(
                support_count=int(at_tau["n_positive"]),
                negative_count=int(at_tau["n_negative"]), precision_bits=int(bits),
                lower_below=below.real.lower(), upper_below=upper_below,
                lower_above=lower_above, upper_above=above.real.upper(),
                tau=dyadic_arb(tau_num, tau_power),
                diagnostic_support_count=diagnostic_support,
                bracket_source="validated_Arb_eigenvalue_balls",
                protocol_version=protocol_version,
            )
        except (ValueError, ArithmeticError, TypeError):
            pass
        below = _validated_float_bracket(
            sectors, approximate_below, at_tau["n_negative"], side="BELOW",
            tau=dyadic_arb(tau_num, tau_power), bits=int(bits), timeout=maximum_seconds_per_inertia,
        )
        above = _validated_float_bracket(
            sectors, approximate_above, at_tau["n_negative"], side="ABOVE",
            tau=dyadic_arb(tau_num, tau_power), bits=int(bits), timeout=maximum_seconds_per_inertia,
        )
        last_debug.update({"below": below, "above": above})
        if below["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET" and above["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET":
            return _certified_point_result(
                support_count=int(at_tau["n_positive"]),
                negative_count=int(at_tau["n_negative"]), precision_bits=int(bits),
                lower_below=below["_lower_arb"], upper_below=below["_upper_arb"],
                lower_above=above["_lower_arb"], upper_above=above["_upper_arb"],
                tau=dyadic_arb(tau_num, tau_power),
                diagnostic_support_count=diagnostic_support,
                bracket_source="validated_Arb_inertia_at_fixed_decimal_candidates",
                protocol_version=protocol_version,
            )
        below = _bracket(
            sectors, approximate_below, at_tau["n_negative"], side="BELOW",
            tau_numerator=bracket_tau_num, tau_power=bracket_power,
            bits=int(bits), timeout=maximum_seconds_per_inertia,
            maximum_expansions=maximum_bracket_expansions,
        )
        above = _bracket(
            sectors, approximate_above, at_tau["n_negative"], side="ABOVE",
            tau_numerator=bracket_tau_num, tau_power=bracket_power,
            bits=int(bits), timeout=maximum_seconds_per_inertia,
            maximum_expansions=maximum_bracket_expansions,
        )
        if below["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET" and above["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET":
            return _certified_point_result(
                support_count=int(at_tau["n_positive"]),
                negative_count=int(at_tau["n_negative"]), precision_bits=int(bits),
                lower_below=below["_lower_arb"], upper_below=below["_upper_arb"],
                lower_above=above["_lower_arb"], upper_above=above["_upper_arb"],
                tau=dyadic_arb(tau_num, tau_power),
                diagnostic_support_count=diagnostic_support,
                bracket_source="validated_Arb_inertia_at_dyadic_candidates",
                protocol_version=protocol_version,
            )
    return {"status": "UNCERTIFIED_POINT", "reason": "validated tau inertia or nearest-side bracket failed", "diagnostic_support_count": diagnostic_support, "diagnostic_nearest_below": approximate_below, "diagnostic_nearest_above": approximate_above, "debug": last_debug}
