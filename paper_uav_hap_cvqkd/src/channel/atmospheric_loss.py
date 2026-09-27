"""Atmospheric transmittance models.

The MODTRAN zero-zenith transmittance law is the active manuscript model.
Kruse/Beer--Lambert remains available only for explicitly legacy callers.
"""

from __future__ import annotations

import math


def kruse_q(visibility_km: float) -> float:
    if not math.isfinite(visibility_km) or visibility_km <= 0.0:
        raise ValueError("visibility_km must be finite and positive.")
    if visibility_km > 50.0:
        return 1.6
    if visibility_km > 6.0:
        return 1.3
    return 0.585 * visibility_km ** (1.0 / 3.0)


def extinction_coefficient_per_km(visibility_km: float, wavelength_nm: float) -> float:
    if not math.isfinite(wavelength_nm) or wavelength_nm <= 0.0:
        raise ValueError("wavelength_nm must be finite and positive.")
    return float(
        (3.912 / visibility_km)
        * (wavelength_nm / 550.0) ** (-kruse_q(visibility_km))
    )


def atmospheric_transmittance(
    link_length_m: float,
    visibility_km: float,
    wavelength_m: float,
) -> float:
    """Legacy Kruse/Beer--Lambert transmittance.

    The latest manuscript baseline must use :func:`atmospheric_transmittance_from_tau_zen`.
    """
    if not math.isfinite(link_length_m) or link_length_m <= 0.0:
        raise ValueError("link_length_m must be finite and positive.")
    if not math.isfinite(wavelength_m) or wavelength_m <= 0.0:
        raise ValueError("wavelength_m must be finite and positive.")
    xi_per_km = extinction_coefficient_per_km(visibility_km, wavelength_m * 1e9)
    return float(math.exp(-xi_per_km * link_length_m / 1000.0))


def atmospheric_transmittance_from_tau_zen(
    link_length_m: float,
    tau_zen: float,
    zenith_angle_rad: float,
) -> float:
    """Return ``eta_atm=tau_zen**sec(zeta)`` from a direct MODTRAN input."""

    link_length_m = float(link_length_m)
    tau_zen = float(tau_zen)
    zenith_angle_rad = float(zenith_angle_rad)
    if not math.isfinite(link_length_m) or link_length_m <= 0.0:
        raise ValueError("link_length_m must be finite and positive.")
    if not math.isfinite(tau_zen) or not 0.0 < tau_zen <= 1.0:
        raise ValueError("tau_zen must be finite and lie in (0,1].")
    if not math.isfinite(zenith_angle_rad) or abs(zenith_angle_rad) >= math.pi / 2.0:
        raise ValueError("zenith_angle_rad must be finite and strictly inside +/- pi/2.")
    secant = 1.0 / math.cos(zenith_angle_rad)
    return float(tau_zen**secant)


__all__ = [
    "atmospheric_transmittance",
    "atmospheric_transmittance_from_tau_zen",
    "extinction_coefficient_per_km",
    "kruse_q",
]

