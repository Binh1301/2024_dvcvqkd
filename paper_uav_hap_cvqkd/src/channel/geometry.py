"""Link geometry from paper Eq. (1)."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LinkGeometry:
    """HAP transmitter and UAV receiver geometry, in SI units.

    The paper default is vertical. A nonzero zenith angle is retained only so
    the explicit ``cos(zeta)^-4`` factor in Eq. (19) can be tested.
    """

    h_hap_m: float = 20_000.0
    h_uav_m: float = 0.0
    zenith_angle_rad: float = 0.0

    def validate(self) -> None:
        if not math.isfinite(self.h_hap_m) or not math.isfinite(self.h_uav_m):
            raise ValueError("Altitudes must be finite.")
        if self.h_hap_m <= self.h_uav_m:
            raise ValueError("HAP altitude must exceed UAV altitude.")
        if not math.isfinite(self.zenith_angle_rad):
            raise ValueError("Zenith angle must be finite.")
        if abs(self.zenith_angle_rad) >= math.pi / 2:
            raise ValueError("Zenith angle must lie strictly between -pi/2 and pi/2.")

    @property
    def vertical_separation_m(self) -> float:
        self.validate()
        return float(self.h_hap_m - self.h_uav_m)

    @property
    def link_length_m(self) -> float:
        """Vertical Eq. (1), extended geometrically for an explicit zenith angle."""

        return float(self.vertical_separation_m / math.cos(self.zenith_angle_rad))

    @property
    def is_vertical(self) -> bool:
        return abs(self.zenith_angle_rad) <= 1e-15

