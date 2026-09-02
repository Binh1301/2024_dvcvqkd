"""Composite instantaneous HAP-to-UAV FSO channel, paper Eqs. (42)--(55)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math

import numpy as np

from .atmospheric_loss import atmospheric_transmittance
from .geometry import LinkGeometry
from .pointing_error import PointingParameters, pointing_parameters, pointing_power_transmittance
from .turbulence import (
    UavMotion,
    per_axis_displacement_variance_m2,
    turbulence_beam_wander_variance_m2,
    uav_misalignment_variance_m2,
)


@dataclass(frozen=True)
class ChannelSamples:
    transmittance: np.ndarray
    radial_displacement_m: np.ndarray
    atmospheric_transmittance: float
    pointing: PointingParameters
    sigma_axis_m: float
    exact_csi_oracle: bool
    metadata: dict[str, Any]

    @property
    def mean_transmittance(self) -> float:
        return float(np.mean(self.transmittance))


def sample_fso_channel(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    visibility_km: float,
    beam_waist_m: float,
    aperture_radius_m: float,
    cn2_m_minus_two_thirds: float,
    sample_count: int,
    rng: np.random.Generator,
    uav_motion: UavMotion | None = None,
) -> ChannelSamples:
    """Draw instantaneous power-transmittance samples by Eqs. (21)--(24), (42).

    ``sigma_axis_m`` is explicitly the scale of the Rayleigh radial law, as
    frozen from Eqs. (21)--(24). No estimator or feedback error is modeled;
    downstream adaptation therefore has exact-CSI oracle metadata.
    """

    geometry.validate()
    if not isinstance(sample_count, int) or sample_count <= 0:
        raise ValueError("sample_count must be a positive integer.")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator.")
    motion = UavMotion() if uav_motion is None else uav_motion
    link_length_m = geometry.link_length_m
    eta_atm = atmospheric_transmittance(link_length_m, visibility_km, wavelength_m)
    pointing = pointing_parameters(
        aperture_radius_m, beam_waist_m, wavelength_m, link_length_m
    )
    sigma2_uav = uav_misalignment_variance_m2(motion, aperture_radius_m)
    sigma2_turbulence = turbulence_beam_wander_variance_m2(
        cn2_m_minus_two_thirds,
        link_length_m,
        beam_waist_m,
        geometry.zenith_angle_rad,
    )
    sigma2_axis = per_axis_displacement_variance_m2(sigma2_turbulence, sigma2_uav)
    sigma_axis_m = math.sqrt(sigma2_axis)
    radial = rng.rayleigh(scale=sigma_axis_m, size=sample_count)
    eta_point = pointing_power_transmittance(radial, pointing)
    transmittance = eta_atm * eta_point
    upper = eta_atm * pointing.t0_power
    if np.any(~np.isfinite(transmittance)) or np.any(transmittance <= 0.0):
        raise FloatingPointError(
            "Generated nonpositive transmittance; a numerical outage convention is required "
            "before log10(T) adaptation can consume this state."
        )
    if np.any(transmittance > upper * (1.0 + 1e-12)):
        raise FloatingPointError("Generated transmittance exceeds the physical support.")
    return ChannelSamples(
        transmittance=np.asarray(transmittance, dtype=np.float64),
        radial_displacement_m=np.asarray(radial, dtype=np.float64),
        atmospheric_transmittance=float(eta_atm),
        pointing=pointing,
        sigma_axis_m=float(sigma_axis_m),
        exact_csi_oracle=True,
        metadata={
            "link_length_m": float(link_length_m),
            "zenith_angle_rad": float(geometry.zenith_angle_rad),
            "sigma2_uav_m2": float(sigma2_uav),
            "sigma2_turbulence_m2": float(sigma2_turbulence),
            "sigma2_axis_m2": float(sigma2_axis),
            "rayleigh_scale_convention": "sigma_axis from paper Eqs. (21)-(24)",
            "csi_assumption": "exact instantaneous T and epsilon oracle; no estimator model",
        },
    )
