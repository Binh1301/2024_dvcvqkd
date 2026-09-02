"""Gaussian-beam aperture coupling and pointing loss, Eqs. (11)--(15), (27)--(34)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from scipy.special import i0e, i1e


@dataclass(frozen=True)
class PointingParameters:
    beam_radius_receiver_m: float
    rayleigh_range_m: float
    t0_amplitude: float
    t0_power: float
    gamma: float
    scale_radius_m: float


def gaussian_beam_radius(
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
) -> tuple[float, float]:
    if any(
        not math.isfinite(value) or value <= 0.0
        for value in (beam_waist_m, wavelength_m, link_length_m)
    ):
        raise ValueError("Beam waist, wavelength, and link length must be positive.")
    rayleigh_range_m = math.pi * beam_waist_m**2 / wavelength_m
    beam_radius_m = beam_waist_m * math.sqrt(1.0 + (link_length_m / rayleigh_range_m) ** 2)
    return float(beam_radius_m), float(rayleigh_range_m)


def pointing_parameters(
    aperture_radius_m: float,
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
) -> PointingParameters:
    if not math.isfinite(aperture_radius_m) or aperture_radius_m <= 0.0:
        raise ValueError("aperture_radius_m must be finite and positive.")
    beam_radius_m, rayleigh_range_m = gaussian_beam_radius(
        beam_waist_m, wavelength_m, link_length_m
    )
    t0_power = 1.0 - math.exp(-2.0 * aperture_radius_m**2 / beam_radius_m**2)
    if not 0.0 < t0_power < 1.0:
        raise ValueError("Computed aperture coupling is outside (0, 1).")
    t0_amplitude = math.sqrt(t0_power)
    x = (2.0 * aperture_radius_m / beam_radius_m) ** 2
    # exp(-x) I_n(x) is evaluated directly by the scaled Bessel functions.
    exp_i0 = float(i0e(x))
    exp_i1 = float(i1e(x))
    term = 1.0 - exp_i0
    ratio = 2.0 * t0_power / term
    if term <= 0.0 or ratio <= 1.0:
        raise ValueError("Invalid pointing-shape intermediate values.")
    log_ratio = math.log(ratio)
    gamma = 2.0 * x * exp_i1 / (term * log_ratio)
    if not math.isfinite(gamma) or gamma <= 0.0:
        raise ValueError("Computed pointing shape parameter is invalid.")
    scale_radius_m = aperture_radius_m * log_ratio ** (-1.0 / gamma)
    return PointingParameters(
        beam_radius_receiver_m=float(beam_radius_m),
        rayleigh_range_m=float(rayleigh_range_m),
        t0_amplitude=float(t0_amplitude),
        t0_power=float(t0_power),
        gamma=float(gamma),
        scale_radius_m=float(scale_radius_m),
    )


def pointing_power_transmittance(radial_displacement_m, parameters: PointingParameters):
    """Paper Eq. (27), accepting scalar or NumPy array input."""

    import numpy as np

    radial = np.asarray(radial_displacement_m, dtype=np.float64)
    if np.any(~np.isfinite(radial)) or np.any(radial < 0.0):
        raise ValueError("Radial displacement must be finite and nonnegative.")
    return parameters.t0_power * np.exp(
        -np.power(radial / parameters.scale_radius_m, parameters.gamma)
    )

