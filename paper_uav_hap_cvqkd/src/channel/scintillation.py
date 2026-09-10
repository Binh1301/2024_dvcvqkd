"""Source-supported scintillation primitives and fail-closed resolution."""

from __future__ import annotations

from typing import Iterable
import math

import numpy as np


class UnsupportedApertureAveragingError(ValueError):
    """Raised when ``sigma_R0^2`` cannot be resolved to ``v_sc``."""


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
) -> dict[str, object]:
    """Return the physical/scintillation resolution record."""

    return {
        "profile_model": str(profile_model),
        "sigma_R0_squared": None if sigma_R0_squared is None else float(sigma_R0_squared),
        "v_sc": float(v_sc),
        "aperture_averaging_status": str(resolution_status),
        "lognormal_parameterization": "ln(H_sc) ~ Normal(-v_sc/2, v_sc)",
        "mean_H_sc": 1.0,
    }


__all__ = [
    "UnsupportedApertureAveragingError",
    "normalized_lognormal_samples",
    "resolve_scintillation_variance",
    "rytov_variance_from_profile",
    "scintillation_provenance",
]
