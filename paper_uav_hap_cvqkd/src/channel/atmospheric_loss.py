"""Kruse extinction and Beer--Lambert transmittance, paper Eqs. (7)--(9)."""

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
    if not math.isfinite(link_length_m) or link_length_m <= 0.0:
        raise ValueError("link_length_m must be finite and positive.")
    if not math.isfinite(wavelength_m) or wavelength_m <= 0.0:
        raise ValueError("wavelength_m must be finite and positive.")
    xi_per_km = extinction_coefficient_per_km(visibility_km, wavelength_m * 1e9)
    return float(math.exp(-xi_per_km * link_length_m / 1000.0))

