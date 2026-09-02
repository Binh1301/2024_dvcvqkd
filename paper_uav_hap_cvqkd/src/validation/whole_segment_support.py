"""Conservative whole-segment bounds for C4 transmitter Gram matrices.

The derivative enclosure is proof-oriented: it propagates value intervals and
absolute derivative bounds through affine layers, ReLU, softmax, sigmoid,
log-domain variance, GS gauge normalization, physical energy normalization,
and coherent-state overlaps. It never substitutes finite-node sampling for
the bound. Support certification additionally requires externally validated
initial eigenvalue intervals; absent those intervals it fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import numpy as np
import torch

from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.probabilistic_shaping import channel_features
from src.modulation.qam256 import c4_orbit_indices


def _down(value: np.ndarray | float) -> np.ndarray:
    return np.nextafter(np.asarray(value, dtype=np.float64), -np.inf)


def _up(value: np.ndarray | float) -> np.ndarray:
    return np.nextafter(np.asarray(value, dtype=np.float64), np.inf)


@dataclass(frozen=True)
class DualInterval:
    lower: np.ndarray
    upper: np.ndarray
    derivative_abs: np.ndarray

    def validate(self) -> None:
        if self.lower.shape != self.upper.shape or self.lower.shape != self.derivative_abs.shape:
            raise ValueError("Interval value and derivative shapes differ.")
        if np.any(~np.isfinite(self.lower)) or np.any(~np.isfinite(self.upper)):
            raise ValueError("Interval contains a nonfinite endpoint.")
        if np.any(self.lower > self.upper) or np.any(self.derivative_abs < 0.0):
            raise ValueError("Invalid interval ordering or derivative bound.")

    @property
    def absolute_upper(self) -> np.ndarray:
        return _up(np.maximum(np.abs(self.lower), np.abs(self.upper)))


@dataclass(frozen=True)
class TransmitterSegmentBounds:
    probability_lower: np.ndarray
    probability_upper: np.ndarray
    probability_derivative_abs: np.ndarray
    amplitude_abs_upper: np.ndarray
    amplitude_derivative_abs: np.ndarray
    va_lower: float
    va_upper: float
    va_derivative_abs: float
    energy_lower: float
    derivative_chain: tuple[str, ...]


@dataclass(frozen=True)
class SupportCertificate:
    certified: bool
    retained_rank: int
    threshold: float
    variation_radius: float
    numerical_radius: float | None
    minimum_retained_lower: float | None
    maximum_suppressed_upper: float | None
    retained_margin: float | None
    suppressed_margin: float | None
    reason: str


@dataclass(frozen=True)
class PartitionCertificate:
    certified: bool
    accepted_intervals: tuple[tuple[float, float], ...]
    unresolved_intervals: tuple[tuple[float, float], ...]
    maximum_depth_reached: int
    reason: str


def _product_interval(
    left_lower: np.ndarray, left_upper: np.ndarray,
    right_lower: np.ndarray, right_upper: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    candidates = np.stack((
        left_lower * right_lower,
        left_lower * right_upper,
        left_upper * right_lower,
        left_upper * right_upper,
    ))
    return _down(np.min(candidates, axis=0)), _up(np.max(candidates, axis=0))


def _linear_dual(
    weight0: np.ndarray, weight1: np.ndarray,
    bias0: np.ndarray, bias1: np.ndarray,
    inputs: DualInterval,
) -> DualInterval:
    inputs.validate()
    weight_lower = np.minimum(weight0, weight1)
    weight_upper = np.maximum(weight0, weight1)
    left_lower = weight_lower[:, :, None]
    left_upper = weight_upper[:, :, None]
    right_lower = inputs.lower[None, :, ...]
    right_upper = inputs.upper[None, :, ...]
    term_lower, term_upper = _product_interval(
        left_lower, left_upper, right_lower, right_upper
    )
    lower = _down(np.sum(term_lower, axis=1) + np.minimum(bias0, bias1)[:, None])
    upper = _up(np.sum(term_upper, axis=1) + np.maximum(bias0, bias1)[:, None])
    input_abs = inputs.absolute_upper
    weight_abs = _up(np.maximum(np.abs(weight_lower), np.abs(weight_upper)))
    derivative = _up(
        np.abs(weight1 - weight0) @ input_abs
        + weight_abs @ inputs.derivative_abs
        + np.abs(bias1 - bias0)[:, None]
    )
    return DualInterval(lower, upper, derivative)


def _relu_dual(values: DualInterval) -> DualInterval:
    values.validate()
    lower = _down(np.maximum(values.lower, 0.0))
    upper = _up(np.maximum(values.upper, 0.0))
    derivative = np.where(values.upper <= 0.0, 0.0, values.derivative_abs)
    return DualInterval(lower, upper, _up(derivative))


def _network_logits_bounds(network0: torch.nn.Sequential, network1: torch.nn.Sequential,
                            features: np.ndarray) -> DualInterval:
    point = np.asarray(features, dtype=np.float64).reshape(-1, 1)
    inputs = DualInterval(point, point, np.zeros_like(point))
    first0, first1 = network0[0], network1[0]
    hidden = _linear_dual(
        first0.weight.detach().numpy(), first1.weight.detach().numpy(),
        first0.bias.detach().numpy(), first1.bias.detach().numpy(), inputs,
    )
    hidden = _relu_dual(hidden)
    final0, final1 = network0[2], network1[2]
    return _linear_dual(
        final0.weight.detach().numpy(), final1.weight.detach().numpy(),
        final0.bias.detach().numpy(), final1.bias.detach().numpy(), hidden,
    )


def _softmax_dual(logits: DualInterval) -> DualInterval:
    logits.validate()
    count, batch = logits.lower.shape
    lower = np.empty_like(logits.lower)
    upper = np.empty_like(logits.upper)
    for state in range(batch):
        for index in range(count):
            other = np.arange(count) != index
            lower_denominator = 1.0 + np.sum(np.exp(_up(
                logits.upper[other, state] - logits.lower[index, state]
            )))
            upper_denominator = 1.0 + np.sum(np.exp(_down(
                logits.lower[other, state] - logits.upper[index, state]
            )))
            lower[index, state] = _down(1.0 / _up(lower_denominator))
            upper[index, state] = _up(1.0 / _down(upper_denominator))
    maximum_logit_derivative = np.max(logits.derivative_abs, axis=0, keepdims=True)
    derivative = _up(upper * (logits.derivative_abs + maximum_logit_derivative))
    result = DualInterval(_down(lower), _up(upper), derivative)
    result.validate()
    return result


def _sigmoid_scalar_bounds(values: DualInterval) -> DualInterval:
    values.validate()
    lower = _down(1.0 / (1.0 + np.exp(_up(-values.lower))))
    upper = _up(1.0 / (1.0 + np.exp(_down(-values.upper))))
    derivative = _up(0.25 * values.derivative_abs)
    return DualInterval(lower, upper, derivative)


def _complex_box_magnitude(
    real_lower: np.ndarray, real_upper: np.ndarray,
    imag_lower: np.ndarray, imag_upper: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    def component_minimum(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
        return np.where((lower <= 0.0) & (upper >= 0.0), 0.0, np.minimum(np.abs(lower), np.abs(upper)))
    real_min = component_minimum(real_lower, real_upper)
    imag_min = component_minimum(imag_lower, imag_upper)
    real_max = np.maximum(np.abs(real_lower), np.abs(real_upper))
    imag_max = np.maximum(np.abs(imag_lower), np.abs(imag_upper))
    return (
        _down(np.sqrt(_down(real_min * real_min + imag_min * imag_min))),
        _up(np.sqrt(_up(real_max * real_max + imag_max * imag_max))),
    )


def transmitter_segment_bounds(
    transmitter0: JointTransmitter,
    transmitter1: JointTransmitter,
    transmittance: float,
    epsilon_snu: float,
) -> TransmitterSegmentBounds:
    if transmitter0.mode != transmitter1.mode:
        raise ValueError("Segment endpoints must use the same transmitter mode.")
    features = channel_features(
        torch.tensor([transmittance], dtype=torch.float64),
        torch.tensor([epsilon_snu], dtype=torch.float64),
    ).detach().numpy()[0]

    if transmitter0.ps_network is None:
        probabilities = transmitter0.fixed_probabilities.detach().numpy()
        p_lower = _down(probabilities)
        p_upper = _up(probabilities)
        p_derivative = np.zeros_like(probabilities)
        orbit_indices = c4_orbit_indices().detach().numpy()
        q_lower = 4.0 * p_lower[orbit_indices[:, 0]]
        q_upper = 4.0 * p_upper[orbit_indices[:, 0]]
        q_derivative = np.zeros(64, dtype=np.float64)
    else:
        if transmitter1.ps_network is None:
            raise ValueError("PS availability differs between endpoints.")
        logits = _network_logits_bounds(
            transmitter0.ps_network.network, transmitter1.ps_network.network, features
        )
        q = _softmax_dual(logits)
        q_lower, q_upper, q_derivative = q.lower[:, 0], q.upper[:, 0], q.derivative_abs[:, 0]
        p_lower = np.repeat(q_lower / 4.0, 4)
        p_upper = np.repeat(q_upper / 4.0, 4)
        p_derivative = np.repeat(q_derivative / 4.0, 4)

    if transmitter0.va_network is None:
        if transmitter1.va_network is not None or transmitter0.fixed_va != transmitter1.fixed_va:
            raise ValueError("Fixed-VA segment endpoints differ.")
        va_lower = va_upper = float(transmitter0.fixed_va)
        va_derivative = 0.0
    else:
        if transmitter1.va_network is None:
            raise ValueError("VA availability differs between endpoints.")
        raw = _network_logits_bounds(
            transmitter0.va_network.network, transmitter1.va_network.network, features
        )
        unit = _sigmoid_scalar_bounds(raw)
        v_min = transmitter0.va_network.v_min
        v_max = transmitter0.va_network.v_max
        if (v_min, v_max) != (transmitter1.va_network.v_min, transmitter1.va_network.v_max):
            raise ValueError("VA bounds differ between endpoints.")
        log_ratio = math.log(v_max / v_min)
        va_lower = float(_down(v_min * np.exp(_down(log_ratio * unit.lower[0, 0]))))
        va_upper = float(_up(v_min * np.exp(_up(log_ratio * unit.upper[0, 0]))))
        va_derivative = float(_up(va_upper * log_ratio * unit.derivative_abs[0, 0]))

    orbit_indices = c4_orbit_indices().detach().numpy()
    if transmitter0.gs_model is None:
        if transmitter1.gs_model is not None:
            raise ValueError("GS availability differs between endpoints.")
        prototypes = transmitter0.base_relative_constellation.detach().numpy()[orbit_indices[:, 0]]
        z_lower = _down(np.abs(prototypes))
        z_upper = _up(np.abs(prototypes))
        z_derivative = np.zeros(64, dtype=np.float64)
    else:
        if transmitter1.gs_model is None:
            raise ValueError("GS availability differs between endpoints.")
        raw0 = transmitter0.gs_model.raw_coordinates.detach().numpy()
        raw1 = transmitter1.gs_model.raw_coordinates.detach().numpy()
        real_lower, real_upper = np.minimum(raw0[:, 0], raw1[:, 0]), np.maximum(raw0[:, 0], raw1[:, 0])
        imag_lower, imag_upper = np.minimum(raw0[:, 1], raw1[:, 1]), np.maximum(raw0[:, 1], raw1[:, 1])
        g_lower, g_upper = _complex_box_magnitude(real_lower, real_upper, imag_lower, imag_upper)
        g_derivative = _up(np.sqrt(np.sum((raw1 - raw0) ** 2, axis=1)))
        mean_lower = float(_down(np.mean(_down(g_lower * g_lower))))
        mean_upper = float(_up(np.mean(_up(g_upper * g_upper))))
        if mean_lower <= 0.0:
            raise ValueError("GS gauge interval includes zero RMS and cannot be certified.")
        mean_derivative = float(_up(2.0 * np.mean(_up(g_upper * g_derivative))))
        z_lower = _down(g_lower / math.sqrt(mean_upper))
        z_upper = _up(g_upper / math.sqrt(mean_lower))
        z_derivative = _up(
            g_derivative / math.sqrt(mean_lower)
            + 0.5 * g_upper * mean_derivative / (mean_lower ** 1.5)
        )

    energy_lower = float(_down(np.sum(_down(q_lower * _down(z_lower * z_lower)))))
    energy_upper = float(_up(np.sum(_up(q_upper * _up(z_upper * z_upper)))))
    if energy_lower <= 0.0:
        raise ValueError("Physical-normalization energy interval reaches zero.")
    energy_derivative = float(_up(np.sum(
        _up(q_derivative * _up(z_upper * z_upper))
        + _up(q_upper * _up(2.0 * z_upper * z_derivative))
    )))
    scale_upper = math.sqrt(float(_up(va_upper / _down(2.0 * energy_lower))))
    scale_derivative = float(_up(
        0.5 * scale_upper * (va_derivative / va_lower + energy_derivative / energy_lower)
    ))
    alpha_upper_orbit = _up(scale_upper * z_upper)
    alpha_derivative_orbit = _up(scale_derivative * z_upper + scale_upper * z_derivative)
    flat_indices = orbit_indices.reshape(-1)
    def expand_orbit(values: np.ndarray) -> np.ndarray:
        expanded = np.empty(256, dtype=np.float64)
        expanded[flat_indices] = np.repeat(values, 4)
        return expanded
    return TransmitterSegmentBounds(
        probability_lower=expand_orbit(q_lower / 4.0),
        probability_upper=expand_orbit(q_upper / 4.0),
        probability_derivative_abs=expand_orbit(q_derivative / 4.0),
        amplitude_abs_upper=expand_orbit(alpha_upper_orbit),
        amplitude_derivative_abs=expand_orbit(alpha_derivative_orbit),
        va_lower=va_lower,
        va_upper=va_upper,
        va_derivative_abs=va_derivative,
        energy_lower=energy_lower,
        derivative_chain=(
            "affine", "relu_activation_changes_enclosed", "softmax",
            "sigmoid", "log_domain_va", "gs_unit_rms_gauge",
            "pmf_weighted_physical_scale", "coherent_overlap",
        ),
    )


def gram_derivative_frobenius_bound(bounds: TransmitterSegmentBounds) -> float:
    p_lower = bounds.probability_lower
    p_upper = bounds.probability_upper
    p_derivative = bounds.probability_derivative_abs
    if np.any(p_lower <= 0.0):
        raise ValueError("A positive probability lower bound is required.")
    a = bounds.amplitude_abs_upper
    da = bounds.amplitude_derivative_abs
    probability_term = 0.5 * (
        p_derivative[:, None] / p_lower[:, None]
        + p_derivative[None, :] / p_lower[None, :]
    )
    amplitude_term = (a[:, None] + a[None, :]) * (da[:, None] + da[None, :])
    overlap_modulus_upper = np.sqrt(_up(p_upper[:, None] * p_upper[None, :]))
    entry_derivative = _up(overlap_modulus_upper * _up(probability_term + amplitude_term))
    return float(_up(np.sqrt(_up(np.sum(_up(entry_derivative * entry_derivative))))))


def certify_support_from_validated_intervals(
    eigenvalue_lower: Iterable[float],
    eigenvalue_upper: Iterable[float],
    *,
    retained_rank: int,
    threshold: float,
    variation_radius: float,
    numerical_radius: float | None,
) -> SupportCertificate:
    lower = np.sort(np.asarray(tuple(eigenvalue_lower), dtype=np.float64))
    upper = np.sort(np.asarray(tuple(eigenvalue_upper), dtype=np.float64))
    if lower.shape != upper.shape or lower.ndim != 1 or lower.size == 0:
        raise ValueError("Validated eigenvalue intervals must be nonempty and aligned.")
    if np.any(lower > upper):
        raise ValueError("An eigenvalue lower endpoint exceeds its upper endpoint.")
    if not 1 <= retained_rank <= lower.size:
        raise ValueError("retained_rank is outside the eigenspectrum.")
    if numerical_radius is None:
        return SupportCertificate(
            False, retained_rank, threshold, variation_radius, None, None, None,
            None, None,
            "No validated Gram assembly/eigensystem numerical enclosure is available.",
        )
    radius = float(_up(variation_radius + numerical_radius))
    retained_lower = float(lower[-retained_rank])
    suppressed_upper = float(upper[-retained_rank - 1]) if retained_rank < lower.size else -math.inf
    retained_margin = float(_down(retained_lower - radius - threshold))
    suppressed_margin = math.inf if retained_rank == lower.size else float(
        _down(threshold - (suppressed_upper + radius))
    )
    certified = retained_margin > 0.0 and suppressed_margin > 0.0
    return SupportCertificate(
        certified, retained_rank, threshold, variation_radius, numerical_radius,
        retained_lower, suppressed_upper, retained_margin, suppressed_margin,
        "Both Weyl guard inequalities are strict." if certified else
        "At least one validated Weyl guard inequality is nonpositive; fail closed.",
    )


def certify_segment_by_bisection(
    eigenvalue_interval_provider: Callable[[float], tuple[Iterable[float], Iterable[float]]],
    derivative_bound_provider: Callable[[float, float], float],
    *,
    retained_rank: int,
    threshold: float,
    numerical_radius: float | None,
    maximum_depth: int,
    minimum_interval_width: float,
) -> PartitionCertificate:
    """Certify a complete segment or fail closed at frozen resource limits.

    The providers must themselves return validated enclosures. Diagnostic node
    samples are not accepted as providers. Each accepted interval uses its
    midpoint eigenspectrum and ``rho <= h sup_I ||dG/dt||_2``.
    """

    if maximum_depth < 0 or not 0.0 < minimum_interval_width <= 1.0:
        raise ValueError("Invalid bisection resource limits.")
    pending: list[tuple[float, float, int]] = [(0.0, 1.0, 0)]
    accepted: list[tuple[float, float]] = []
    unresolved: list[tuple[float, float]] = []
    maximum_seen = 0
    while pending:
        left, right, depth = pending.pop()
        maximum_seen = max(maximum_seen, depth)
        midpoint = 0.5 * (left + right)
        lower, upper = eigenvalue_interval_provider(midpoint)
        derivative = float(derivative_bound_provider(left, right))
        if not math.isfinite(derivative) or derivative < 0.0:
            unresolved.append((left, right))
            continue
        certificate = certify_support_from_validated_intervals(
            lower, upper,
            retained_rank=retained_rank,
            threshold=threshold,
            variation_radius=float(_up(0.5 * (right - left) * derivative)),
            numerical_radius=numerical_radius,
        )
        if certificate.certified:
            accepted.append((left, right))
            continue
        if depth >= maximum_depth or right - left <= minimum_interval_width:
            unresolved.append((left, right))
            continue
        pending.append((midpoint, right, depth + 1))
        pending.append((left, midpoint, depth + 1))
    certified = not unresolved
    return PartitionCertificate(
        certified=certified,
        accepted_intervals=tuple(sorted(accepted)),
        unresolved_intervals=tuple(sorted(unresolved)),
        maximum_depth_reached=maximum_seen,
        reason=(
            "Every subinterval has a strict validated Weyl support guard."
            if certified else
            "At least one subinterval is unresolved at the frozen resource limit; reject the step."
        ),
    )
