"""Gaussian-beam pointing loss from the manuscript's Eqs. (27)--(39)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.special import erf, i0


@dataclass(frozen=True)
class PointingParameters:
    """Derived optical quantities and compatibility aliases for the sampler."""

    beam_radius_receiver_m: float
    rayleigh_range_m: float
    t0_amplitude: float
    t0_power: float
    gamma: float
    scale_radius_m: float
    omega_0_m: float
    omega_L_e_m: float
    g_d: float
    nu: float
    omega_L_eq_m: float


def gaussian_beam_radius(
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    *,
    theta_div_rad: float | None = None,
    f0_m: float = math.inf,
) -> tuple[float, float]:
    """Return ``(omega_L, z_R)`` using PDF Eqs. (27)--(29)."""

    values = (float(beam_waist_m), float(wavelength_m), float(link_length_m))
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise ValueError("Beam waist, wavelength, and link length must be positive.")
    f0_m = float(f0_m)
    if f0_m == float("-inf") or (not math.isinf(f0_m) and (not math.isfinite(f0_m) or f0_m == 0.0)):
        raise ValueError("f0_m must be a finite nonzero value or positive infinity.")
    # PDF Eq. (29); the legacy beam_waist input remains the fallback alias.
    omega_0_m = (
        2.0 * wavelength_m / (math.pi * float(theta_div_rad))
        if theta_div_rad is not None
        else float(beam_waist_m)
    )
    if not math.isfinite(omega_0_m) or omega_0_m <= 0.0:
        raise ValueError("Computed omega_0 must be finite and positive.")
    # PDF Eq. (28).
    k_wave = 2.0 * math.pi / wavelength_m
    # PDF Eq. (27).
    curvature_term = 1.0 if math.isinf(f0_m) else 1.0 - link_length_m / f0_m
    omega_L_m = omega_0_m * math.sqrt(
        curvature_term**2 + (2.0 * link_length_m / (k_wave * omega_0_m**2)) ** 2
    )
    # The old public helper returns the Rayleigh range as its second value.
    rayleigh_range_m = math.pi * omega_0_m**2 / wavelength_m
    return float(omega_L_m), float(rayleigh_range_m)


def pointing_parameters(
    aperture_radius_m: float,
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    *,
    theta_div_rad: float | None = None,
    f0_m: float = math.inf,
    zenith_angle_rad: float = 0.0,
    beam_spreading_factor: float = 0.0,
) -> PointingParameters:
    """Derive the PDF optical pointing quantities and Eq. (36) transform."""

    aperture_radius_m = float(aperture_radius_m)
    wavelength_m = float(wavelength_m)
    link_length_m = float(link_length_m)
    zenith_angle_rad = float(zenith_angle_rad)
    beam_spreading_factor = float(beam_spreading_factor)
    if not math.isfinite(aperture_radius_m) or aperture_radius_m <= 0.0:
        raise ValueError("aperture_radius_m must be finite and positive.")
    if not math.isfinite(zenith_angle_rad) or abs(zenith_angle_rad) >= math.pi / 2.0:
        raise ValueError("zenith_angle_rad must lie strictly inside +/- pi/2.")
    if not math.isfinite(beam_spreading_factor) or beam_spreading_factor < 0.0:
        raise ValueError("beam_spreading_factor must be finite and nonnegative.")
    omega_L_m, rayleigh_range_m = gaussian_beam_radius(
        beam_waist_m,
        wavelength_m,
        link_length_m,
        theta_div_rad=theta_div_rad,
        f0_m=f0_m,
    )
    # PDF Eq. (29), repeated here for provenance of the returned field.
    omega_0_m = (
        2.0 * wavelength_m / (math.pi * float(theta_div_rad))
        if theta_div_rad is not None
        else float(beam_waist_m)
    )
    # PDF Eqs. (30)--(31); the attached PDF prints the same expression twice.
    omega_L_e_m = omega_L_m * math.sqrt(1.0 + beam_spreading_factor)
    # PDF Eq. (33), with D_r=2*aperture_radius_m.
    nu = math.sqrt(math.pi) * (2.0 * aperture_radius_m) / (2.0 * math.sqrt(2.0) * omega_L_m)
    # PDF Eq. (34).
    a0 = float(erf(nu) ** 2)
    if not 0.0 < a0 <= 1.0:
        raise ValueError("Computed A0 must lie in (0,1].")
    # PDF Eq. (35).
    omega_L_eq_squared_m2 = (
        omega_L_e_m**2
        * math.sqrt(math.pi)
        * float(erf(nu))
        / (2.0 * nu * math.exp(-nu**2))
    )
    omega_L_eq_m = math.sqrt(omega_L_eq_squared_m2)
    return PointingParameters(
        beam_radius_receiver_m=float(omega_L_m),
        rayleigh_range_m=float(rayleigh_range_m),
        t0_amplitude=float(math.sqrt(a0)),
        t0_power=float(a0),
        # Compatibility representation of Eq. (36): A0*exp[-(r/R)^2].
        gamma=2.0,
        scale_radius_m=float(omega_L_eq_m / math.sqrt(2.0)),
        omega_0_m=float(omega_0_m),
        omega_L_e_m=float(omega_L_e_m),
        g_d=float(beam_spreading_factor),
        nu=float(nu),
        omega_L_eq_m=float(omega_L_eq_m),
    )


def pointing_power_transmittance(
    radial_displacement_m: float | np.ndarray,
    parameters: PointingParameters,
) -> np.ndarray:
    """Map displacement to ``H_p`` using PDF Eq. (36)."""

    radial = np.asarray(radial_displacement_m, dtype=np.float64)
    if np.any(~np.isfinite(radial)) or np.any(radial < 0.0):
        raise ValueError("Radial displacement must be finite and nonnegative.")
    return parameters.t0_power * np.exp(
        -2.0 * radial**2 / parameters.omega_L_eq_m**2
    )


def pointing_pdf(
    values: float | np.ndarray,
    parameters: PointingParameters,
    sigma_jt_m: float,
    rho_m: float = 0.0,
) -> np.ndarray:
    """Evaluate the analytical pointing-coefficient PDF from PDF Eq. (37)."""

    values = np.asarray(values, dtype=np.float64)
    sigma_jt_m = float(sigma_jt_m)
    rho_m = float(rho_m)
    if not math.isfinite(sigma_jt_m) or sigma_jt_m <= 0.0:
        raise ValueError("sigma_jt_m must be finite and positive.")
    if not math.isfinite(rho_m) or rho_m < 0.0:
        raise ValueError("rho_m must be finite and nonnegative.")
    result = np.zeros_like(values)
    valid = (values > 0.0) & (values <= parameters.t0_power)
    if not np.any(valid):
        return result
    sigma_squared = sigma_jt_m**2
    chi_squared = (parameters.omega_L_eq_m / (2.0 * sigma_jt_m)) ** 2
    radial_squared = -0.5 * parameters.omega_L_eq_m**2 * np.log(
        values[valid] / parameters.t0_power
    )
    bessel_argument = rho_m * np.sqrt(radial_squared) / sigma_squared
    # PDF Eq. (37); use scipy.special.i0 exactly as in the paper.
    result[valid] = (
        chi_squared
        / parameters.t0_power**chi_squared
        * math.exp(-rho_m**2 / (2.0 * sigma_squared))
        * values[valid] ** (chi_squared - 1.0)
        * i0(bessel_argument)
    )
    return result


def rician_pdf(values: float | np.ndarray, sigma_jt_m: float, rho_m: float = 0.0) -> np.ndarray:
    """Evaluate the radial Rician PDF from PDF Eq. (26)."""

    values = np.asarray(values, dtype=np.float64)
    sigma_jt_m = float(sigma_jt_m)
    rho_m = float(rho_m)
    if not math.isfinite(sigma_jt_m) or sigma_jt_m <= 0.0:
        raise ValueError("sigma_jt_m must be finite and positive.")
    if not math.isfinite(rho_m) or rho_m < 0.0:
        raise ValueError("rho_m must be finite and nonnegative.")
    result = np.zeros_like(values)
    valid = values >= 0.0
    sigma_squared = sigma_jt_m**2
    # PDF Eq. (26); I0 is the modified Bessel function of the first kind.
    result[valid] = (
        values[valid]
        / sigma_squared
        * np.exp(-(values[valid] ** 2 + rho_m**2) / (2.0 * sigma_squared))
        * i0(rho_m * values[valid] / sigma_squared)
    )
    return result


__all__ = [
    "PointingParameters",
    "gaussian_beam_radius",
    "pointing_parameters",
    "pointing_pdf",
    "pointing_power_transmittance",
    "rician_pdf",
]
