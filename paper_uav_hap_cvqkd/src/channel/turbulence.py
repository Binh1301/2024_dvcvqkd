"""Receiver-plane displacement variances, paper Eqs. (16)--(24)."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class UavMotion:
    sigma_x_m: float = 0.0521
    sigma_y_m: float = 0.0502
    sigma_z_m: float = 0.0703
    sigma_theta_rad: float = 2.60e-3
    sigma_phi_rad: float = 2.04e-3
    sigma_psi_rad: float = 4.06e-3

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative.")


def uav_misalignment_variance_m2(motion: UavMotion, aperture_radius_m: float) -> float:
    motion.validate()
    if not math.isfinite(aperture_radius_m) or aperture_radius_m <= 0.0:
        raise ValueError("aperture_radius_m must be finite and positive.")
    sigma2_pos = motion.sigma_x_m**2 + motion.sigma_y_m**2 + motion.sigma_z_m**2
    sigma2_orient = (
        motion.sigma_theta_rad**2 + motion.sigma_phi_rad**2 + motion.sigma_psi_rad**2
    )
    return float(sigma2_pos + aperture_radius_m**2 * sigma2_orient)


def turbulence_beam_wander_variance_m2(
    cn2_m_minus_two_thirds: float,
    link_length_m: float,
    beam_waist_m: float,
    zenith_angle_rad: float = 0.0,
) -> float:
    """Constant-Cn2 beam-wander variance from paper Eq. (19)."""

    values = (cn2_m_minus_two_thirds, link_length_m, beam_waist_m)
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise ValueError("Cn2, link length, and beam waist must be finite and positive.")
    cosine = math.cos(zenith_angle_rad)
    if not math.isfinite(cosine) or cosine <= 0.0:
        raise ValueError("zenith_angle_rad must give a positive cosine.")
    return float(
        1.919
        * cn2_m_minus_two_thirds
        * link_length_m**3
        * (2.0 * beam_waist_m) ** (-1.0 / 3.0)
        / cosine**4
    )


def per_axis_displacement_variance_m2(
    turbulence_variance_m2: float,
    uav_variance_m2: float,
) -> float:
    """Frozen interpretation of paper Eq. (21): variance of each Cartesian axis."""

    if any(
        not math.isfinite(value) or value < 0.0
        for value in (turbulence_variance_m2, uav_variance_m2)
    ):
        raise ValueError("Displacement variances must be finite and nonnegative.")
    return float(turbulence_variance_m2 + uav_variance_m2)

