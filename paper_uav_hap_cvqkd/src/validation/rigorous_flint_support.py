"""Certification-only Arb/FLINT whole-segment C4 Gram support enclosure.

This module is intentionally independent of PyTorch and NumPy.  It consumes a
hexadecimal float64 parameter bundle, interprets every endpoint as the exact
IEEE-754 dyadic value, and evaluates the actual straight parameter path in
Arb/acb balls.  The production complex128 backend is not replaced.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import time
from typing import Any, Callable

from flint import acb, acb_mat, arb, ctx


I = acb(0, 1)


def exact_arb_from_float_hex(value: str) -> arb:
    """Return the exact Arb dyadic represented by a Python float hex string."""

    binary = float.fromhex(value)
    if not math.isfinite(binary):
        raise ValueError("Certification inputs must be finite binary64 values.")
    numerator, denominator = binary.as_integer_ratio()
    exponent = -(denominator.bit_length() - 1)
    if denominator != 1 << (-exponent):
        raise ValueError("binary64 denominator is not a power of two.")
    return arb((numerator, exponent))


def exact_arb_from_fraction(value: Fraction) -> arb:
    denominator = value.denominator
    if denominator & (denominator - 1):
        return arb(value.numerator) / arb(denominator)
    return arb((value.numerator, -(denominator.bit_length() - 1)))


def fraction_ball(left: Fraction, right: Fraction) -> arb:
    if left > right:
        raise ValueError("Invalid path interval ordering.")
    midpoint = (left + right) / 2
    radius = (right - left) / 2
    return arb(exact_arb_from_fraction(midpoint), exact_arb_from_fraction(radius))


def _lower_positive(value: arb) -> bool:
    return bool(value.lower() > 0)


def _relu(value: arb) -> arb:
    if bool(value.upper() <= 0):
        return arb(0)
    if bool(value.lower() >= 0):
        return value
    return arb(0).union(value.upper())


def _shape_size(shape: list[int]) -> int:
    result = 1
    for value in shape:
        result *= int(value)
    return result


class BallTransmitterPath:
    """Arb evaluation of one exact float64 full-transmitter parameter path."""

    def __init__(self, start: dict[str, Any], end: dict[str, Any],
                 state: dict[str, Any], v_min_hex: str, v_max_hex: str) -> None:
        if set(start) != set(end):
            raise ValueError("Segment endpoint parameter names differ.")
        self.start = start
        self.end = end
        self.features = [exact_arb_from_float_hex(value) for value in state["channel_features_float64_hex"]]
        self.v_min = exact_arb_from_float_hex(v_min_hex)
        self.v_max = exact_arb_from_float_hex(v_max_hex)
        self._validate_payloads()

    def _validate_payloads(self) -> None:
        required = {
            "ps_network.network.0.weight", "ps_network.network.0.bias",
            "ps_network.network.2.weight", "ps_network.network.2.bias",
            "gs_model.raw_coordinates",
            "va_network.network.0.weight", "va_network.network.0.bias",
            "va_network.network.2.weight", "va_network.network.2.bias",
        }
        if set(self.start) != required:
            raise ValueError("Fixture bundle does not match the frozen Full transmitter parameterization.")
        for name in required:
            left, right = self.start[name], self.end[name]
            if left["shape"] != right["shape"]:
                raise ValueError(f"Endpoint shape mismatch for {name}.")
            if len(left["float64_hex"]) != _shape_size(left["shape"]):
                raise ValueError(f"Malformed flattened parameter payload for {name}.")

    def _parameter(self, name: str, path_value: arb) -> tuple[list[int], list[arb]]:
        left = self.start[name]
        right = self.end[name]
        values = []
        for initial_hex, final_hex in zip(left["float64_hex"], right["float64_hex"]):
            initial = exact_arb_from_float_hex(initial_hex)
            final = exact_arb_from_float_hex(final_hex)
            values.append(initial + path_value * (final - initial))
        return [int(value) for value in left["shape"]], values

    def _linear(self, prefix: str, inputs: list[arb], path_value: arb) -> list[arb]:
        shape, weight = self._parameter(prefix + ".weight", path_value)
        bias_shape, bias = self._parameter(prefix + ".bias", path_value)
        if len(shape) != 2 or shape[1] != len(inputs) or bias_shape != [shape[0]]:
            raise ValueError(f"Invalid affine shape for {prefix}.")
        output = []
        for row in range(shape[0]):
            value = bias[row]
            offset = row * shape[1]
            for column, input_value in enumerate(inputs):
                value += weight[offset + column] * input_value
            output.append(value)
        return output

    def probabilities(self, path_value: arb) -> list[arb]:
        hidden = [_relu(value) for value in self._linear(
            "ps_network.network.0", self.features, path_value
        )]
        logits = self._linear("ps_network.network.2", hidden, path_value)
        exponentials = [value.exp() for value in logits]
        denominator = sum(exponentials, arb(0))
        if not _lower_positive(denominator):
            raise ValueError("Softmax denominator interval reaches zero.")
        return [value / denominator for value in exponentials]

    def variance(self, path_value: arb) -> arb:
        hidden = [_relu(value) for value in self._linear(
            "va_network.network.0", self.features, path_value
        )]
        raw = self._linear("va_network.network.2", hidden, path_value)[0]
        unit = arb(1) / (arb(1) + (-raw).exp())
        ratio = self.v_max / self.v_min
        if not _lower_positive(ratio):
            raise ValueError("VA ratio interval is nonpositive.")
        return self.v_min * (ratio.log() * unit).exp()

    def relative_prototypes(self, path_value: arb) -> list[acb]:
        shape, coordinates = self._parameter("gs_model.raw_coordinates", path_value)
        if shape != [64, 2]:
            raise ValueError("GS payload must contain 64 complex prototypes.")
        raw = [acb(coordinates[2 * index], coordinates[2 * index + 1]) for index in range(64)]
        mean_energy = sum(
            (value.real * value.real + value.imag * value.imag for value in raw), arb(0)
        ) / 64
        if not _lower_positive(mean_energy):
            raise ValueError("GS unit-RMS gauge interval reaches zero.")
        scale = mean_energy.sqrt()
        return [value / scale for value in raw]

    def physical_ensemble(self, path_value: arb) -> tuple[list[arb], list[acb]]:
        q = self.probabilities(path_value)
        z = self.relative_prototypes(path_value)
        variance = self.variance(path_value)
        energy = sum((qk * (zk.real * zk.real + zk.imag * zk.imag) for qk, zk in zip(q, z)), arb(0))
        if not _lower_positive(energy) or not _lower_positive(variance):
            raise ValueError("Physical normalization interval reaches a nonpositive value.")
        scale = (variance / (2 * energy)).sqrt()
        return [value / 4 for value in q], [scale * value for value in z]

    @staticmethod
    def _overlap(left: acb, right: acb) -> acb:
        left_energy = left.real * left.real + left.imag * left.imag
        right_energy = right.real * right.real + right.imag * right.imag
        return (acb(-(left_energy + right_energy) / 2) + left.conjugate() * right).exp()

    def sectors(self, path_value: arb) -> list[list[list[acb]]]:
        probabilities, prototypes = self.physical_ensemble(path_value)
        raw_sectors: list[list[list[acb]]] = []
        rotations = [acb(1), I, acb(-1), -I]
        for sector in range(4):
            matrix = [[acb(0) for _ in range(64)] for _ in range(64)]
            for row in range(64):
                for column in range(64):
                    root_probability = (probabilities[row] * probabilities[column]).sqrt()
                    value = acb(0)
                    for difference in range(4):
                        value += (
                            root_probability
                            * self._overlap(prototypes[row], rotations[difference] * prototypes[column])
                            * (I ** (sector * difference))
                        )
                    matrix[row][column] = value
            raw_sectors.append(matrix)
        sectors = []
        for raw in raw_sectors:
            hermitian = [[
                (raw[row][column] + raw[column][row].conjugate()) / 2
                for column in range(64)
            ] for row in range(64)]
            sectors.append(hermitian)
        return sectors


def _acb_upper_abs(value: acb) -> arb:
    return value.abs_upper()


def _rho_frobenius(interval_matrix: list[list[acb]], midpoint_matrix: list[list[acb]]) -> arb:
    total = arb(0)
    for interval_row, midpoint_row in zip(interval_matrix, midpoint_matrix):
        for interval_value, midpoint_value in zip(interval_row, midpoint_row):
            upper = _acb_upper_abs(interval_value - midpoint_value)
            total += upper * upper
    return total.sqrt().upper()


def _matrix(values: list[list[acb]]) -> acb_mat:
    size = len(values)
    matrix = acb_mat(size, size)
    for row in range(size):
        if len(values[row]) != size:
            raise ValueError("Sector matrix must be square.")
        for column in range(size):
            matrix[row, column] = values[row][column]
    return matrix


def _text(value: arb, digits: int = 18) -> str:
    return value.str(digits, radius=False)


def validated_eigenvalue_balls(matrix: list[list[acb]], *, precision_bits: int,
                                algorithms: list[str]) -> tuple[list[acb], str]:
    ctx.prec = int(precision_bits)
    last_error: Exception | None = None
    for algorithm in algorithms:
        if algorithm == "approx":
            raise ValueError("Approximate eigensolvers are forbidden for certification.")
        try:
            values = _matrix(matrix).eig(multiple=True, algorithm=algorithm)
            if len(values) != len(matrix):
                raise ValueError("Validated eigensolver returned the wrong multiplicity.")
            if any(not value.imag.contains(0) for value in values):
                raise ValueError("Hermitian eigenvalue ball does not contain a real value.")
            return values, algorithm
        except (ValueError, ArithmeticError) as error:
            last_error = error
    raise ValueError(f"Validated eigensolver failed at {precision_bits} bits: {last_error}")


def classify_eigenballs(eigenvalues: list[acb], rho: arb, threshold: arb) -> dict[str, Any]:
    rows = []
    retained = 0
    suppressed = 0
    unresolved = 0
    for index, value in enumerate(eigenvalues):
        lower = value.real.lower()
        upper = value.real.upper()
        retained_margin = (lower - rho - threshold).lower()
        suppressed_margin = (threshold - upper - rho).lower()
        if bool(retained_margin > 0):
            classification = "RETAINED"
            retained += 1
        elif bool(suppressed_margin > 0):
            classification = "SUPPRESSED"
            suppressed += 1
        else:
            classification = "UNRESOLVED"
            unresolved += 1
        rows.append({
            "index": index,
            "real_lower": _text(lower),
            "real_upper": _text(upper),
            "imaginary_contains_zero": bool(value.imag.contains(0)),
            "classification": classification,
            "retained_margin_lower": _text(retained_margin),
            "suppressed_margin_lower": _text(suppressed_margin),
        })
    return {
        "retained_count": retained,
        "suppressed_count": suppressed,
        "unresolved_count": unresolved,
        "eigenvalue_enclosures": rows,
    }


def evaluate_interval(path: BallTransmitterPath, left: Fraction, right: Fraction,
                      *, threshold: arb, precision_bits: list[int],
                      algorithms: list[str]) -> dict[str, Any]:
    midpoint = (left + right) / 2
    attempts = []
    for bits in precision_bits:
        ctx.prec = int(bits)
        try:
            interval_sectors = path.sectors(fraction_ball(left, right))
            midpoint_sectors = path.sectors(exact_arb_from_fraction(midpoint))
            sector_rows = []
            total_retained = 0
            total_unresolved = 0
            for sector_index, (interval_sector, midpoint_sector) in enumerate(
                zip(interval_sectors, midpoint_sectors)
            ):
                rho = _rho_frobenius(interval_sector, midpoint_sector)
                eigenvalues, algorithm = validated_eigenvalue_balls(
                    midpoint_sector, precision_bits=int(bits), algorithms=algorithms
                )
                classification = classify_eigenballs(eigenvalues, rho, threshold)
                total_retained += int(classification["retained_count"])
                total_unresolved += int(classification["unresolved_count"])
                sector_rows.append({
                    "sector": sector_index,
                    "rho_frobenius_upper": _text(rho),
                    "precision_bits": int(bits),
                    "eigensolver_algorithm": algorithm,
                    **classification,
                })
            result = {
                "left": f"{left.numerator}/{left.denominator}",
                "right": f"{right.numerator}/{right.denominator}",
                "midpoint": f"{midpoint.numerator}/{midpoint.denominator}",
                "precision_bits": int(bits),
                "retained_count": total_retained,
                "unresolved_count": total_unresolved,
                "sectors": sector_rows,
                "status": "CLASSIFIED" if total_unresolved == 0 else "UNRESOLVED",
            }
            attempts.append({"precision_bits": int(bits), "status": result["status"]})
            result["precision_attempts"] = attempts
            if total_unresolved == 0:
                return result
        except (ValueError, ArithmeticError, OverflowError) as error:
            attempts.append({"precision_bits": int(bits), "status": "FAILED", "reason": str(error)})
    return {
        "left": f"{left.numerator}/{left.denominator}",
        "right": f"{right.numerator}/{right.denominator}",
        "midpoint": f"{midpoint.numerator}/{midpoint.denominator}",
        "status": "UNRESOLVED",
        "retained_count": None,
        "unresolved_count": 256,
        "sectors": [],
        "precision_attempts": attempts,
    }


def certify_parameter_segment(path: BallTransmitterPath, *, threshold: arb,
                              precision_bits: list[int], algorithms: list[str],
                              maximum_depth: int, minimum_width: Fraction,
                              maximum_nodes: int, maximum_seconds: float,
                              progress: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    start = evaluate_interval(path, Fraction(0), Fraction(0), threshold=threshold,
                              precision_bits=precision_bits, algorithms=algorithms)
    end = evaluate_interval(path, Fraction(1), Fraction(1), threshold=threshold,
                            precision_bits=precision_bits, algorithms=algorithms)
    if start["status"] != "CLASSIFIED" or end["status"] != "CLASSIFIED":
        return {
            "status": "UNCERTIFIED_ENDPOINT_SPECTRUM",
            "start_spectrum": start,
            "end_spectrum": end,
            "nodes": [],
            "runtime_seconds": time.perf_counter() - started,
        }
    start_rank = int(start["retained_count"])
    end_rank = int(end["retained_count"])
    if start_rank != end_rank:
        return {
            "status": "RIGOROUS_ENDPOINT_RANK_CHANGE_CROSSING",
            "start_rank": start_rank,
            "end_rank": end_rank,
            "start_spectrum": start,
            "end_spectrum": end,
            "nodes": [],
            "runtime_seconds": time.perf_counter() - started,
        }

    pending: list[tuple[Fraction, Fraction, int]] = [(Fraction(0), Fraction(1), 0)]
    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    maximum_seen = 0
    while pending:
        if len(nodes) >= maximum_nodes or time.perf_counter() - started >= maximum_seconds:
            for left, right, depth in pending:
                unresolved.append({
                    "left": f"{left.numerator}/{left.denominator}",
                    "right": f"{right.numerator}/{right.denominator}",
                    "depth": depth,
                    "reason": "FROZEN_WORK_OR_TIME_LIMIT",
                })
            pending.clear()
            break
        left, right, depth = pending.pop()
        maximum_seen = max(maximum_seen, depth)
        result = evaluate_interval(path, left, right, threshold=threshold,
                                   precision_bits=precision_bits, algorithms=algorithms)
        result["depth"] = depth
        nodes.append(result)
        if progress is not None:
            progress(result)
        if result["status"] == "CLASSIFIED" and int(result["retained_count"]) == start_rank:
            result["certification_result"] = "WHOLE_SEGMENT_SUPPORT_CERTIFIED"
            accepted.append(result)
            continue
        if result["status"] == "CLASSIFIED" and int(result["retained_count"]) != start_rank:
            result["certification_result"] = "RIGOROUS_RANK_DIFFERENCE"
            unresolved.append(result)
            continue
        width = right - left
        if depth >= maximum_depth or width <= minimum_width:
            result["certification_result"] = "UNCERTIFIED_RESOURCE_LIMIT"
            unresolved.append(result)
            continue
        midpoint = (left + right) / 2
        pending.append((midpoint, right, depth + 1))
        pending.append((left, midpoint, depth + 1))

    certified = not unresolved
    minimum_margin = None
    if certified:
        margins = []
        for node in accepted:
            for sector in node["sectors"]:
                for eigenvalue in sector["eigenvalue_enclosures"]:
                    key = "retained_margin_lower" if eigenvalue["classification"] == "RETAINED" else "suppressed_margin_lower"
                    margins.append(float(eigenvalue[key]))
        minimum_margin = min(margins) if margins else None
    return {
        "status": "WHOLE_SEGMENT_SUPPORT_CERTIFIED" if certified else "UNCERTIFIED_FAIL_CLOSED",
        "start_rank": start_rank,
        "end_rank": end_rank,
        "start_spectrum": start,
        "end_spectrum": end,
        "accepted_leaf_count": len(accepted),
        "unresolved_leaf_count": len(unresolved),
        "maximum_depth_reached": maximum_seen,
        "minimum_certified_spectral_margin": minimum_margin,
        "nodes": nodes,
        "unresolved_leaves": unresolved,
        "runtime_seconds": time.perf_counter() - started,
    }


def certify_affine_scalar_segment(start: str, end: str, threshold_hex: str,
                                  *, maximum_depth: int = 8) -> dict[str, Any]:
    """Analytically checkable 1x1 regression path using the same Weyl rule."""

    initial = exact_arb_from_float_hex(start)
    final = exact_arb_from_float_hex(end)
    threshold = exact_arb_from_float_hex(threshold_hex)
    start_retained = bool(initial > threshold)
    end_retained = bool(final > threshold)
    if start_retained != end_retained:
        return {"status": "RIGOROUS_ENDPOINT_RANK_CHANGE_CROSSING", "nodes": []}
    pending = [(Fraction(0), Fraction(1), 0)]
    nodes = []
    while pending:
        left, right, depth = pending.pop()
        path_ball = initial + fraction_ball(left, right) * (final - initial)
        midpoint = (left + right) / 2
        midpoint_value = initial + exact_arb_from_fraction(midpoint) * (final - initial)
        rho = (path_ball - midpoint_value).abs_upper()
        retained = bool(midpoint_value.lower() - rho > threshold)
        suppressed = bool(midpoint_value.upper() + rho < threshold)
        nodes.append({"left": str(left), "right": str(right), "depth": depth,
                      "retained": retained, "suppressed": suppressed})
        if retained or suppressed:
            continue
        if depth >= maximum_depth:
            return {"status": "UNCERTIFIED_FAIL_CLOSED", "nodes": nodes}
        middle = (left + right) / 2
        pending.append((middle, right, depth + 1))
        pending.append((left, middle, depth + 1))
    return {"status": "WHOLE_SEGMENT_SUPPORT_CERTIFIED", "nodes": nodes}
