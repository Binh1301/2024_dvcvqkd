"""Fixed-altitude HAP-to-UAV link geometry."""

from __future__ import annotations

from dataclasses import dataclass
import math


HAP_ALTITUDE_M = 20_000.0


def derive_link_length_m(
    h_hap_m: float,
    h_uav_m: float,
    zenith_angle_rad: float,
) -> float:
    """Return ``L=(20000-h_UAV)/cos(zeta)`` in metres."""

    h_hap_m = float(h_hap_m)
    h_uav_m = float(h_uav_m)
    zenith_angle_rad = float(zenith_angle_rad)
    if not math.isfinite(h_hap_m) or not math.isfinite(h_uav_m):
        raise ValueError("Altitudes must be finite.")
    if h_hap_m != HAP_ALTITUDE_M:
        raise ValueError(f"h_hap_m is fixed at {HAP_ALTITUDE_M:g} m.")
    if h_hap_m <= h_uav_m:
        raise ValueError("HAP altitude must exceed UAV altitude.")
    if not math.isfinite(zenith_angle_rad):
        raise ValueError("Zenith angle must be finite.")
    if abs(zenith_angle_rad) >= math.pi / 2:
        raise ValueError("Zenith angle must lie strictly between -pi/2 and pi/2.")
    return float((HAP_ALTITUDE_M - h_uav_m) / math.cos(zenith_angle_rad))


def zenith_angle_rad_for_link_length_m(link_length_m: float, h_uav_m: float) -> float:
    """Return the radians angle producing a requested valid slant length."""

    link_length_m = float(link_length_m)
    h_uav_m = float(h_uav_m)
    vertical_m = HAP_ALTITUDE_M - h_uav_m
    if not math.isfinite(link_length_m) or link_length_m <= 0.0:
        raise ValueError("link_length_m must be finite and positive.")
    if not math.isfinite(h_uav_m) or h_uav_m >= HAP_ALTITUDE_M:
        raise ValueError("h_uav_m must be finite and below the fixed HAP altitude.")
    cosine = vertical_m / link_length_m
    if not 0.0 < cosine <= 1.0:
        raise ValueError("link_length_m must be at least the vertical separation.")
    return float(math.acos(cosine))


@dataclass(frozen=True)
class LinkGeometry:
    """HAP transmitter and UAV receiver geometry, in SI units.

    ``zenith_angle_rad`` is stored in radians. Degree-valued scenarios must be
    converted with ``math.radians`` before construction.
    """

    h_hap_m: float = 20_000.0
    h_uav_m: float = 0.0
    zenith_angle_rad: float = 0.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        derive_link_length_m(self.h_hap_m, self.h_uav_m, self.zenith_angle_rad)

    @property
    def vertical_separation_m(self) -> float:
        self.validate()
        return float(HAP_ALTITUDE_M - self.h_uav_m)

    @property
    def link_length_m(self) -> float:
        return derive_link_length_m(self.h_hap_m, self.h_uav_m, self.zenith_angle_rad)

    @property
    def is_vertical(self) -> bool:
        return abs(self.zenith_angle_rad) <= 1e-15

