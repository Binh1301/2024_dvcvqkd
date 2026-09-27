"""Gaussian-beam aperture coupling and pointing loss, Eqs. (11)--(15), (27)--(34)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from scipy.integrate import quad
from scipy.special import i0e, i1e


@dataclass(frozen=True)
class PointingParameters:
    beam_radius_receiver_m: float
    rayleigh_range_m: float
    t0_amplitude: float
    t0_power: float
    gamma: float
    scale_radius_m: float
    model: str = "generalized_gaussian"
    omega_l_m: float | None = None
    g_d: float | None = None
    omega_l_eq_m: float | None = None
    nu: float | None = None
    a0: float | None = None


def gaussian_beam_radius(
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    radius_of_curvature_m: float = math.inf,
) -> tuple[float, float]:
    if any(
        not math.isfinite(value) or value <= 0.0
        for value in (beam_waist_m, wavelength_m, link_length_m)
    ):
        raise ValueError("Beam waist, wavelength, and link length must be positive.")
    radius_of_curvature_m = float(radius_of_curvature_m)
    if math.isnan(radius_of_curvature_m) or radius_of_curvature_m == 0.0:
        raise ValueError("radius_of_curvature_m must be nonzero or infinity.")
    if math.isfinite(radius_of_curvature_m) and radius_of_curvature_m < 0.0:
        raise ValueError("radius_of_curvature_m must be positive or infinity.")
    rayleigh_range_m = math.pi * beam_waist_m**2 / wavelength_m
    wave_number = 2.0 * math.pi / wavelength_m
    focusing = (
        1.0
        if math.isinf(radius_of_curvature_m)
        else 1.0 - link_length_m / radius_of_curvature_m
    )
    beam_radius_m = beam_waist_m * math.sqrt(
        focusing**2 + (2.0 * link_length_m / (wave_number * beam_waist_m**2)) ** 2
    )
    return float(beam_radius_m), float(rayleigh_range_m)


def pointing_parameters(
    aperture_radius_m: float,
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    radius_of_curvature_m: float = math.inf,
) -> PointingParameters:
    if not math.isfinite(aperture_radius_m) or aperture_radius_m <= 0.0:
        raise ValueError("aperture_radius_m must be finite and positive.")
    beam_radius_m, rayleigh_range_m = gaussian_beam_radius(
        beam_waist_m, wavelength_m, link_length_m, radius_of_curvature_m
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


def manuscript_pointing_parameters(
    aperture_radius_m: float,
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    radius_of_curvature_m: float,
    h_uav_m: float,
    h_hap_m: float,
    zenith_angle_rad: float,
    wind_speed_m_per_s: float,
    cn2_ground_m_minus_two_thirds: float,
) -> PointingParameters:
    """Return the manuscript ``A0, omega_L, G_d, omega_L,eq`` parameters."""

    if not math.isfinite(h_uav_m) or not math.isfinite(h_hap_m) or h_hap_m <= h_uav_m:
        raise ValueError("The turbulence path altitudes must be finite and increasing.")
    if not math.isfinite(zenith_angle_rad) or abs(zenith_angle_rad) >= math.pi / 2.0:
        raise ValueError("zenith_angle_rad must lie strictly inside +/- pi/2.")
    omega_l, rayleigh_range_m = gaussian_beam_radius(
        beam_waist_m, wavelength_m, link_length_m, radius_of_curvature_m
    )
    secant = 1.0 / math.cos(zenith_angle_rad)
    wave_number = 2.0 * math.pi / wavelength_m
    vertical_span = h_hap_m - h_uav_m

    from .scintillation import hufnagel_valley_cn2

    mu2 = quad(
        lambda height: float(
            hufnagel_valley_cn2(
                height,
                wind_speed_m_per_s,
                cn2_ground_m_minus_two_thirds,
            )
        )
        * ((height - h_uav_m) / vertical_span) ** (5.0 / 3.0),
        h_uav_m,
        h_hap_m,
        epsabs=1.0e-18,
        epsrel=2.0e-13,
        limit=300,
    )[0]
    lambda_beam = 2.0 * link_length_m / (wave_number * omega_l**2)
    g_d = (
        4.35
        * lambda_beam ** (5.0 / 6.0)
        * wave_number ** (7.0 / 6.0)
        * vertical_span ** (5.0 / 6.0)
        * secant ** (11.0 / 6.0)
        * mu2
    )
    omega_l_e = omega_l * math.sqrt(1.0 + g_d)
    diameter = 2.0 * float(aperture_radius_m)
    nu = math.sqrt(math.pi) * diameter / (2.0 * math.sqrt(2.0) * omega_l)
    a0 = math.erf(nu) ** 2
    omega_l_eq = math.sqrt(
        omega_l_e**2 * math.sqrt(math.pi) * math.erf(nu)
        / (2.0 * nu * math.exp(-nu**2))
    )
    return PointingParameters(
        beam_radius_receiver_m=float(omega_l),
        rayleigh_range_m=float(rayleigh_range_m),
        t0_amplitude=float(math.sqrt(a0)),
        t0_power=float(a0),
        gamma=2.0,
        scale_radius_m=float(omega_l_eq / math.sqrt(2.0)),
        model="manuscript_gaussian_equivalent",
        omega_l_m=float(omega_l),
        g_d=float(g_d),
        omega_l_eq_m=float(omega_l_eq),
        nu=float(nu),
        a0=float(a0),
    )


def pointing_power_transmittance(radial_displacement_m, parameters: PointingParameters):
    """Paper Eq. (27), accepting scalar or NumPy array input."""

    import numpy as np

    radial = np.asarray(radial_displacement_m, dtype=np.float64)
    if np.any(~np.isfinite(radial)) or np.any(radial < 0.0):
        raise ValueError("Radial displacement must be finite and nonnegative.")
    if parameters.model == "manuscript_gaussian_equivalent":
        return parameters.t0_power * np.exp(
            -2.0 * radial**2 / parameters.omega_l_eq_m**2
        )
    return parameters.t0_power * np.exp(
        -np.power(radial / parameters.scale_radius_m, parameters.gamma)
    )


__all__ = [
    "PointingParameters",
    "gaussian_beam_radius",
    "manuscript_pointing_parameters",
    "pointing_parameters",
    "pointing_power_transmittance",
]

