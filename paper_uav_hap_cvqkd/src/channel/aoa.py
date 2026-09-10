"""Angle-of-arrival jitter and hard field-of-view outage primitives."""

from __future__ import annotations

import math

import numpy as np

from .turbulence import UavMotion


class UnsupportedTurbulenceAoAError(ValueError):
    """Raised when a nonzero turbulence-induced AoA variance is unvalidated."""


def aoa_orientation_variance_rad2(motion: UavMotion) -> float:
    """Return the two-axis orientation variance; yaw is deliberately excluded."""

    motion.validate()
    return float((motion.sigma_theta_rad**2 + motion.sigma_phi_rad**2) / 2.0)


def _resolve_turbulence_aoa_variance(
    sigma_turb_AoA2: float | None,
    *,
    model: str,
    provenance: str | None,
) -> float:
    value = 0.0 if sigma_turb_AoA2 is None else float(sigma_turb_AoA2)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("sigma_turb_AoA2 must be finite and nonnegative.")
    if model == "disabled":
        if value != 0.0:
            raise UnsupportedTurbulenceAoAError(
                "A nonzero turbulence-induced AoA variance cannot use model='disabled'."
            )
        return 0.0
    if model == "external_validated" and value >= 0.0 and provenance:
        return value
    raise UnsupportedTurbulenceAoAError(
        "Turbulence-induced AoA mapping is unsupported; use explicit disabled "
        "zero variance or provide a validated external value and provenance."
    )


def aoa_variance_rad2(
    motion: UavMotion,
    *,
    sigma_turb_AoA2: float | None = None,
    model: str = "disabled",
    provenance: str | None = None,
) -> float:
    """Return ``sigma_o^2=sigma_UAV_orient^2+sigma_turb_AoA^2``."""

    turbulence = _resolve_turbulence_aoa_variance(
        sigma_turb_AoA2, model=model, provenance=provenance
    )
    return float(aoa_orientation_variance_rad2(motion) + turbulence)


def aoa_outage_probability(theta_fov_rad: float, sigma_o2: float) -> float:
    theta_fov_rad = float(theta_fov_rad)
    sigma_o2 = float(sigma_o2)
    if not math.isfinite(theta_fov_rad) or theta_fov_rad < 0.0:
        raise ValueError("theta_fov_rad must be finite and nonnegative.")
    if not math.isfinite(sigma_o2) or sigma_o2 < 0.0:
        raise ValueError("sigma_o2 must be finite and nonnegative.")
    if sigma_o2 == 0.0:
        return 0.0
    return float(math.exp(-theta_fov_rad**2 / (2.0 * sigma_o2)))


def aoa_inlier_probability(theta_fov_rad: float, sigma_o2: float) -> float:
    return float(1.0 - aoa_outage_probability(theta_fov_rad, sigma_o2))


def sample_aoa_gate(
    *,
    sample_count: int,
    rng: np.random.Generator,
    sigma_o2: float,
    theta_fov_rad: float,
) -> np.ndarray:
    """Sample the hard gate ``1[theta_a <= theta_FOV]``."""

    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator.")
    if not isinstance(sample_count, int) or sample_count <= 0:
        raise ValueError("sample_count must be a positive integer.")
    sigma_o2 = float(sigma_o2)
    theta_fov_rad = float(theta_fov_rad)
    if not math.isfinite(sigma_o2) or sigma_o2 < 0.0:
        raise ValueError("sigma_o2 must be finite and nonnegative.")
    if not math.isfinite(theta_fov_rad) or theta_fov_rad < 0.0:
        raise ValueError("theta_fov_rad must be finite and nonnegative.")
    components = rng.normal(0.0, math.sqrt(sigma_o2), size=(sample_count, 2))
    magnitude = np.hypot(components[:, 0], components[:, 1])
    return (magnitude <= theta_fov_rad).astype(np.int8, copy=False)


__all__ = [
    "UnsupportedTurbulenceAoAError",
    "aoa_inlier_probability",
    "aoa_orientation_variance_rad2",
    "aoa_outage_probability",
    "aoa_variance_rad2",
    "sample_aoa_gate",
]
