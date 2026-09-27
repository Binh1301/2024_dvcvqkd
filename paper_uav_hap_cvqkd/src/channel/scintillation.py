"""Source-supported scintillation primitives and fail-closed resolution."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable
import math

import numpy as np
from scipy.integrate import quad


class UnsupportedApertureAveragingError(ValueError):
    """Raised when ``sigma_R0^2`` cannot be resolved to ``v_sc``."""


def hufnagel_valley_cn2(
    height_m: float | np.ndarray,
    wind_speed_m_per_s: float,
    cn2_ground_m_minus_two_thirds: float,
) -> float | np.ndarray:
    """Return the manuscript's altitude-dependent Hufnagel--Valley profile."""

    height = np.asarray(height_m, dtype=np.float64)
    wind = float(wind_speed_m_per_s)
    ground = float(cn2_ground_m_minus_two_thirds)
    if not np.all(np.isfinite(height)):
        raise ValueError("height_m must be finite.")
    if not math.isfinite(wind) or wind < 0.0:
        raise ValueError("wind_speed_m_per_s must be finite and nonnegative.")
    if not math.isfinite(ground) or ground < 0.0:
        raise ValueError("cn2_ground_m_minus_two_thirds must be finite and nonnegative.")
    value = (
        0.00594
        * (wind / 27.0) ** 2
        * (1.0e-5 * height) ** 10
        * np.exp(-height / 1000.0)
        + 2.7e-16 * np.exp(-height / 1500.0)
        + ground * np.exp(-height / 100.0)
    )
    return float(value) if value.ndim == 0 else value


@lru_cache(maxsize=32)
def hufnagel_valley_scintillation(
    h_uav_m: float,
    h_hap_m: float,
    wavelength_m: float,
    zenith_angle_rad: float,
    wind_speed_m_per_s: float,
    cn2_ground_m_minus_two_thirds: float,
    receiver_diameter_m: float,
) -> dict[str, float]:
    """Derive the manuscript's aperture-corrected log-intensity variance.

    The cached scalar calculation keeps the production sampler cheap while
    retaining the exact profile and aperture integrals used by Eqs. (3)--(8).
    """

    values = tuple(
        float(value)
        for value in (
            h_uav_m,
            h_hap_m,
            wavelength_m,
            zenith_angle_rad,
            wind_speed_m_per_s,
            cn2_ground_m_minus_two_thirds,
            receiver_diameter_m,
        )
    )
    h_uav, h_hap, wavelength, zenith, wind, ground, diameter = values
    if h_hap <= h_uav:
        raise ValueError("h_hap_m must exceed h_uav_m.")
    if wavelength <= 0.0 or diameter <= 0.0:
        raise ValueError("wavelength_m and receiver_diameter_m must be positive.")
    if abs(zenith) >= math.pi / 2.0:
        raise ValueError("zenith_angle_rad must lie strictly inside +/- pi/2.")
    profile = lambda height: float(
        hufnagel_valley_cn2(height, wind, ground)
    )
    secant = 1.0 / math.cos(zenith)
    wave_number = 2.0 * math.pi / wavelength
    rytov_integral, rytov_error = quad(
        lambda height: profile(height) * (height - h_uav) ** (5.0 / 6.0),
        h_uav,
        h_hap,
        epsabs=1.0e-24,
        epsrel=2.0e-13,
        limit=300,
    )
    aperture_numerator, numerator_error = quad(
        lambda height: profile(height) * height**2,
        h_uav,
        h_hap,
        epsabs=1.0e-18,
        epsrel=2.0e-13,
        limit=300,
    )
    aperture_denominator, denominator_error = quad(
        lambda height: profile(height) * height ** (5.0 / 6.0),
        h_uav,
        h_hap,
        epsabs=1.0e-24,
        epsrel=2.0e-13,
        limit=300,
    )
    sigma_R0_squared = (
        2.25
        * wave_number ** (7.0 / 6.0)
        * secant ** (11.0 / 6.0)
        * rytov_integral
    )
    Phi_m = (aperture_numerator / aperture_denominator) ** (6.0 / 7.0)
    aperture_factor = (
        1.0
        + 1.11
        * (diameter**2 / (wavelength * Phi_m * secant)) ** (7.0 / 6.0)
    ) ** -1.0
    return {
        "sigma_R0_squared": float(sigma_R0_squared),
        "Phi_m": float(Phi_m),
        "A_ap": float(aperture_factor),
        "v_sc": float(aperture_factor * sigma_R0_squared),
        "rytov_integral": float(rytov_integral),
        "rytov_integral_quad_error": float(rytov_error),
        "aperture_numerator": float(aperture_numerator),
        "aperture_numerator_quad_error": float(numerator_error),
        "aperture_denominator": float(aperture_denominator),
        "aperture_denominator_quad_error": float(denominator_error),
        "model": "hufnagel_valley_finite_aperture_weak_turbulence",
        "profile_formula": (
            "0.00594*(v_wind/27)^2*(1e-5*h)^10*exp(-h/1000) + "
            "2.7e-16*exp(-h/1500) + Cn2_ground*exp(-h/100)"
        ),
    }


def _finite_nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative.")
    return value


def rytov_variance_from_profile(
    heights_m: Iterable[float],
    cn2_profile_m_minus_two_thirds: Iterable[float],
    *,
    wavelength_m: float,
    link_length_m: float,
    h_uav_m: float,
    zenith_angle_rad: float = 0.0,
) -> float:
    """Return the specified profile-integrated plane-wave Rytov variance.

    The profile is supplied explicitly.  This function intentionally does not
    construct a Hufnagel--Valley profile or infer one from a scalar ``C_n^2``.
    """

    heights = np.asarray(tuple(heights_m), dtype=np.float64)
    profile = np.asarray(tuple(cn2_profile_m_minus_two_thirds), dtype=np.float64)
    if heights.ndim != 1 or profile.ndim != 1 or heights.size < 2:
        raise ValueError("A turbulence profile requires at least two 1-D samples.")
    if heights.shape != profile.shape:
        raise ValueError("Profile heights and C_n^2 values must have equal shape.")
    if not np.all(np.isfinite(heights)) or not np.all(np.isfinite(profile)):
        raise ValueError("Turbulence profile values must be finite.")
    if np.any(np.diff(heights) <= 0.0):
        raise ValueError("Turbulence profile heights must be strictly increasing.")
    if np.any(profile < 0.0):
        raise ValueError("Turbulence profile C_n^2 values must be nonnegative.")
    wavelength_m = float(wavelength_m)
    link_length_m = float(link_length_m)
    h_uav_m = float(h_uav_m)
    zenith_angle_rad = float(zenith_angle_rad)
    if not math.isfinite(wavelength_m) or wavelength_m <= 0.0:
        raise ValueError("wavelength_m must be finite and positive.")
    if not math.isfinite(link_length_m) or link_length_m <= 0.0:
        raise ValueError("link_length_m must be finite and positive.")
    if not math.isfinite(h_uav_m):
        raise ValueError("h_uav_m must be finite.")
    if not math.isfinite(zenith_angle_rad) or abs(zenith_angle_rad) >= math.pi / 2.0:
        raise ValueError("zenith_angle_rad must be finite and strictly below pi/2 in magnitude.")
    if heights[0] < h_uav_m or heights[-1] > h_uav_m + link_length_m:
        raise ValueError("Turbulence profile must lie within the propagation path.")
    path_weight = np.power(heights - h_uav_m, 5.0 / 6.0)
    integral = float(np.trapezoid(profile * path_weight, heights))
    k = 2.0 * math.pi / wavelength_m
    secant = 1.0 / math.cos(zenith_angle_rad)
    return float(2.25 * k ** (7.0 / 6.0) * secant ** (11.0 / 6.0) * integral)


def normalized_lognormal_samples(
    v_sc: float,
    rng: np.random.Generator,
    sample_count: int,
) -> np.ndarray:
    """Draw positive ``H_sc`` samples with analytic mean one."""

    v_sc = _finite_nonnegative(v_sc, "v_sc")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator.")
    if not isinstance(sample_count, int) or sample_count <= 0:
        raise ValueError("sample_count must be a positive integer.")
    if v_sc == 0.0:
        return np.ones(sample_count, dtype=np.float64)
    return np.exp(
        rng.normal(-0.5 * v_sc, math.sqrt(v_sc), size=sample_count)
    ).astype(np.float64, copy=False)


def resolve_scintillation_variance(
    *,
    sigma_R0_squared: float,
    aperture_averaging_model: str | None,
    v_sc_override: float | None,
) -> tuple[float, str]:
    """Resolve the aperture log variance without assuming ``v_sc=sigma_R0^2``."""

    sigma_R0_squared = _finite_nonnegative(sigma_R0_squared, "sigma_R0_squared")
    if v_sc_override is not None:
        return _finite_nonnegative(v_sc_override, "v_sc_override"), "explicit_v_sc_override"
    if aperture_averaging_model == "identity_sigma_R0_explicit":
        return sigma_R0_squared, "explicit_identity_sigma_R0"
    if aperture_averaging_model == "disabled" and sigma_R0_squared == 0.0:
        return 0.0, "disabled_explicit"
    raise UnsupportedApertureAveragingError(
        "No validated aperture-averaging mapping resolves sigma_R0^2 to v_sc; "
        "provide an explicit v_sc_override or an author-frozen mapping."
    )


def scintillation_provenance(
    *,
    sigma_R0_squared: float | None,
    v_sc: float,
    resolution_status: str,
    profile_model: str,
    derivation: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the physical/scintillation resolution record."""

    record = {
        "profile_model": str(profile_model),
        "sigma_R0_squared": None if sigma_R0_squared is None else float(sigma_R0_squared),
        "v_sc": float(v_sc),
        "aperture_averaging_status": str(resolution_status),
        "lognormal_parameterization": "ln(H_sc) ~ Normal(-v_sc/2, v_sc)",
        "mean_H_sc": 1.0,
    }
    if derivation is not None:
        record["derivation"] = dict(derivation)
    return record


__all__ = [
    "UnsupportedApertureAveragingError",
    "hufnagel_valley_cn2",
    "hufnagel_valley_scintillation",
    "normalized_lognormal_samples",
    "resolve_scintillation_variance",
    "rytov_variance_from_profile",
    "scintillation_provenance",
]
