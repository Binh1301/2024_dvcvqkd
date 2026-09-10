"""Scenario-level phase distortion and post-action excess-noise equations."""

from __future__ import annotations

import math
from typing import Any

import torch


def _finite_float(value: Any, name: str, *, nonnegative: bool = False) -> float:
    try:
        resolved = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be finite.") from error
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite.")
    if nonnegative and resolved < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return resolved


def phase_distortion_variance(
    Cn_phi2: float,
    wavelength_m: float,
    link_distance_m: float,
) -> float:
    """Return the scenario-level tau_phi2 value, meaning tau_phi**2."""

    cn_phi2 = _finite_float(Cn_phi2, "Cn_phi2", nonnegative=True)
    wavelength = _finite_float(wavelength_m, "wavelength_m")
    link_distance = _finite_float(link_distance_m, "link_distance_m")
    if wavelength <= 0.0:
        raise ValueError("wavelength_m must be positive.")
    if link_distance <= 0.0:
        raise ValueError("link_distance_m must be positive.")
    kappa = 2.0 * math.pi / wavelength
    return 2.46 * cn_phi2 * kappa ** (7.0 / 6.0) * link_distance ** (11.0 / 6.0)


def phase_noise_coefficient(tau_phi2: float) -> float:
    """Return c_phi = tau_phi2 + 0.25*tau_phi2**2."""

    value = _finite_float(tau_phi2, "tau_phi2", nonnegative=True)
    return value + 0.25 * value**2


def phase_parameter_provenance(
    Cn_phi2: float,
    wavelength_m: float,
    link_distance_m: float,
    *,
    mapping_status: str = "unresolved",
    author_approved: bool = False,
) -> dict[str, Any]:
    """Return phase inputs as an effective scalar of the common atmosphere."""

    cn_phi2 = _finite_float(Cn_phi2, "Cn_phi2", nonnegative=True)
    wavelength = _finite_float(wavelength_m, "wavelength_m")
    link_distance = _finite_float(link_distance_m, "link_distance_m")
    tau_phi2 = phase_distortion_variance(cn_phi2, wavelength, link_distance)
    c_phi = phase_noise_coefficient(tau_phi2)
    return {
        "parameterization": "scenario_level_effective_Cn_phi2",
        "cn_phi2_m_minus_two_thirds": cn_phi2,
        "wavelength_m": wavelength,
        "link_distance_m": link_distance,
        "tau_phi2": tau_phi2,
        "c_phi": c_phi,
        "units": {
            "cn_phi2_m_minus_two_thirds": "m^(-2/3)",
            "wavelength_m": "m",
            "link_distance_m": "m",
            "tau_phi2": "dimensionless",
            "c_phi": "dimensionless",
        },
        "cn_phi2_scope": "fixed_within_scenario",
        "cn_phi2_mapping_status": str(mapping_status),
        "cn_phi2_author_approved": bool(author_approved),
        "common_turbulence_source": "same altitude-dependent C_n^2(h) scenario as scintillation/AoA",
        "cn_phi2_relation_to_cn2_profile": (
            "effective scalar representation of the same physical turbulence; "
            "validated C_n^2(h)->C_n,phi^2 mapping remains unresolved"
        ),
        "c_phi_is_derived": True,
    }


def _float64_tensor(value: torch.Tensor | float, *, device: torch.device | None = None) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.to(dtype=torch.float64, device=device)
    return torch.as_tensor(value, dtype=torch.float64, device=device)


def _validate_noise_tensor(value: torch.Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(value))):
        raise ValueError(f"{name} must be finite.")
    if bool(torch.any(value < 0.0)):
        raise ValueError(f"{name} must be nonnegative.")


def phase_excess_noise(
    modulation_variance: torch.Tensor | float,
    c_phi: torch.Tensor | float,
) -> torch.Tensor:
    """Return the post-action phase contribution c_phi * V_A."""

    va = _float64_tensor(modulation_variance)
    coefficient = _float64_tensor(c_phi, device=va.device)
    _validate_noise_tensor(va, "modulation_variance")
    _validate_noise_tensor(coefficient, "c_phi")
    return coefficient * va


def total_excess_noise(
    epsilon_base: torch.Tensor | float,
    modulation_variance: torch.Tensor | float,
    c_phi: torch.Tensor | float,
) -> torch.Tensor:
    """Return epsilon_base + c_phi * V_A without breaking autograd."""

    va = _float64_tensor(modulation_variance)
    base = _float64_tensor(epsilon_base, device=va.device)
    _validate_noise_tensor(base, "epsilon_base")
    return base + phase_excess_noise(va, c_phi)


def phase_coefficient_from_parameters(
    Cn_phi2: float,
    wavelength_m: float,
    link_distance_m: float,
) -> float:
    """Compute c_phi from the declared scenario-level parameters."""

    return phase_parameter_provenance(Cn_phi2, wavelength_m, link_distance_m)["c_phi"]


__all__ = [
    "phase_coefficient_from_parameters",
    "phase_distortion_variance",
    "phase_excess_noise",
    "phase_parameter_provenance",
    "phase_noise_coefficient",
    "total_excess_noise",
]
