"""Scenario-level turbulence phase-noise model from the current manuscript.

The effective phase-distortion surrogate is deliberately separate from the
``Cn2`` value used by the pointing/beam-wander channel model.  The former is
an externally prescribed scenario parameter; it is neither sampled per fading
realization nor inferred from an altitude profile.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

import torch


@dataclass(frozen=True)
class PhaseNoiseScenario:
    """Fixed phase-noise quantities for one numerical turbulence scenario."""

    cn_phi2_m_minus_two_thirds: float
    wavelength_m: float
    link_distance_m: float
    tau_phi2: float
    c_phi: float
    zero_turbulence_reference: bool

    def metadata(self) -> dict[str, float | bool | str]:
        return {
            "cn_phi2_m_minus_two_thirds": self.cn_phi2_m_minus_two_thirds,
            "cn_phi2_units": "m^-2/3",
            "wavelength_m": self.wavelength_m,
            "link_distance_m": self.link_distance_m,
            "tau_phi2": self.tau_phi2,
            "c_phi": self.c_phi,
            "zero_turbulence_reference": self.zero_turbulence_reference,
            "model": (
                "tau_phi2=2.46*Cn_phi2*(2*pi/wavelength_m)^(7/6)"
                "*link_distance_m^(11/6); "
                "c_phi=tau_phi2+0.25*tau_phi2^2"
            ),
        }


def _finite_scalar(name: str, value: float, *, positive: bool, allow_zero: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite scalar.") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    if positive and (result < 0.0 if allow_zero else result <= 0.0):
        relation = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {relation}.")
    return result


def optical_wavenumber_per_m(wavelength_m: float) -> float:
    r"""Return :math:`2\pi/\lambda_m` using an SI wavelength."""

    wavelength_m = _finite_scalar("wavelength_m", wavelength_m, positive=True)
    return 2.0 * math.pi / wavelength_m


def phase_distortion_variance(
    cn_phi2_m_minus_two_thirds: float,
    wavelength_m: float,
    link_distance_m: float,
    *,
    allow_zero_turbulence_reference: bool = False,
) -> float:
    r"""Compute manuscript Eq. (93)'s scenario-level ``tau_phi2``.

    ``tau_phi2`` stores :math:`\tau_\phi^2`, not :math:`\tau_\phi`; hence a
    later ``tau_phi2**2`` is :math:`\tau_\phi^4`.
    """

    cn_phi2 = _finite_scalar(
        "cn_phi2_m_minus_two_thirds",
        cn_phi2_m_minus_two_thirds,
        positive=True,
        allow_zero=allow_zero_turbulence_reference,
    )
    kappa = optical_wavenumber_per_m(wavelength_m)
    link_distance_m = _finite_scalar("link_distance_m", link_distance_m, positive=True)
    return float(2.46 * cn_phi2 * kappa ** (7.0 / 6.0) * link_distance_m ** (11.0 / 6.0))


def phase_noise_coefficient(tau_phi2: float) -> float:
    """Return ``c_phi=tau_phi2 + 0.25*tau_phi2**2`` (manuscript Eq. 98)."""

    tau_phi2 = _finite_scalar("tau_phi2", tau_phi2, positive=True, allow_zero=True)
    return float(tau_phi2 + 0.25 * tau_phi2**2)


def phase_noise_scenario(
    cn_phi2_m_minus_two_thirds: float,
    wavelength_m: float,
    link_distance_m: float,
    *,
    allow_zero_turbulence_reference: bool = False,
) -> PhaseNoiseScenario:
    """Resolve all fixed phase quantities once for a scenario."""

    tau_phi2 = phase_distortion_variance(
        cn_phi2_m_minus_two_thirds,
        wavelength_m,
        link_distance_m,
        allow_zero_turbulence_reference=allow_zero_turbulence_reference,
    )
    return PhaseNoiseScenario(
        cn_phi2_m_minus_two_thirds=float(cn_phi2_m_minus_two_thirds),
        wavelength_m=float(wavelength_m),
        link_distance_m=float(link_distance_m),
        tau_phi2=tau_phi2,
        c_phi=phase_noise_coefficient(tau_phi2),
        zero_turbulence_reference=bool(
            allow_zero_turbulence_reference
            and float(cn_phi2_m_minus_two_thirds) == 0.0
        ),
    )


def validate_phase_noise_scenario_binding(
    scenario: PhaseNoiseScenario,
    *,
    wavelength_m: float,
    link_distance_m: float,
) -> None:
    """Fail closed unless a phase scenario belongs to this FSO geometry.

    A :class:`PhaseNoiseScenario` is deliberately fixed across fading states,
    but it is not transferable across wavelengths or link lengths.  Validate
    its serialized inputs and its derived quantities before attaching it to a
    sampled channel, so a stale scenario cannot silently supply ``c_phi`` to
    a different optical path.
    """

    if not isinstance(scenario, PhaseNoiseScenario):
        raise TypeError("scenario must be a PhaseNoiseScenario.")
    wavelength_m = _finite_scalar("wavelength_m", wavelength_m, positive=True)
    link_distance_m = _finite_scalar(
        "link_distance_m", link_distance_m, positive=True
    )
    relative_tolerance = 1.0e-12
    if not math.isclose(
        scenario.wavelength_m,
        wavelength_m,
        rel_tol=relative_tolerance,
        abs_tol=0.0,
    ):
        raise ValueError(
            "PhaseNoiseScenario wavelength_m does not match the sampled FSO "
            "channel wavelength_m."
        )
    if not math.isclose(
        scenario.link_distance_m,
        link_distance_m,
        rel_tol=relative_tolerance,
        abs_tol=0.0,
    ):
        raise ValueError(
            "PhaseNoiseScenario link_distance_m does not match the sampled "
            "FSO geometry link length."
        )
    cn_phi2 = _finite_scalar(
        "scenario.cn_phi2_m_minus_two_thirds",
        scenario.cn_phi2_m_minus_two_thirds,
        positive=True,
        allow_zero=scenario.zero_turbulence_reference,
    )
    if cn_phi2 == 0.0 and not scenario.zero_turbulence_reference:
        raise ValueError(
            "A zero Cn_phi2 scenario requires explicit "
            "zero_turbulence_reference=True."
        )
    if cn_phi2 > 0.0 and scenario.zero_turbulence_reference:
        raise ValueError(
            "zero_turbulence_reference may only label an explicit zero Cn_phi2 "
            "scenario."
        )
    expected_tau_phi2 = phase_distortion_variance(
        cn_phi2,
        wavelength_m,
        link_distance_m,
        allow_zero_turbulence_reference=scenario.zero_turbulence_reference,
    )
    expected_c_phi = phase_noise_coefficient(expected_tau_phi2)
    if not math.isclose(
        scenario.tau_phi2,
        expected_tau_phi2,
        rel_tol=relative_tolerance,
        abs_tol=0.0,
    ) or not math.isclose(
        scenario.c_phi,
        expected_c_phi,
        rel_tol=relative_tolerance,
        abs_tol=0.0,
    ):
        raise ValueError(
            "PhaseNoiseScenario derived tau_phi2/c_phi is inconsistent with "
            "its SI inputs."
        )


def phase_noise_scenario_sha256(scenario: PhaseNoiseScenario) -> str:
    """Hash a validated fixed phase scenario for selection/provenance binding."""

    validate_phase_noise_scenario_binding(
        scenario,
        wavelength_m=scenario.wavelength_m,
        link_distance_m=scenario.link_distance_m,
    )
    encoded = json.dumps(
        scenario.metadata(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def phase_noise_scenario_from_channel_config(
    channel_config: Mapping[str, Any],
    *,
    link_distance_m: float,
) -> PhaseNoiseScenario:
    """Resolve the explicitly unit-labelled phase scenario from either schema.

    The active runtime schema is ``default.yaml``'s flattened ``channel``
    mapping.  The standalone physical inventory in ``channel.yaml`` uses an
    ``optics`` mapping; accepting it here prevents its SI phase input from
    being silently ignored while retaining an unambiguous label in errors.
    """

    if "optics" in channel_config:
        if "phase_noise" in channel_config or "wavelength_m" in channel_config:
            raise ValueError(
                "Ambiguous channel configuration: use either the flattened "
                "channel schema or the standalone optics schema, not both."
            )
        optics_config = channel_config.get("optics")
        if not isinstance(optics_config, Mapping):
            raise ValueError("optics must be a mapping in the standalone channel schema.")
        scenario_container = optics_config
        label = "optics"
    else:
        scenario_container = channel_config
        label = "channel"
    phase_config = scenario_container.get("phase_noise")
    if not isinstance(phase_config, Mapping):
        raise ValueError(f"{label}.phase_noise must be an explicit mapping.")
    if phase_config.get("units") != "m^-2/3":
        raise ValueError(
            f"{label}.phase_noise.units must explicitly equal 'm^-2/3'."
        )
    cn_phi2 = phase_config.get("cn_phi2_m_minus_two_thirds")
    if cn_phi2 is None:
        raise ValueError(
            f"{label}.phase_noise.cn_phi2_m_minus_two_thirds is unresolved; "
            "the manuscript requires an externally prescribed scenario value."
        )
    allow_zero = phase_config.get("allow_zero_turbulence_reference", False)
    if not isinstance(allow_zero, bool):
        raise ValueError("allow_zero_turbulence_reference must be boolean.")
    return phase_noise_scenario(
        cn_phi2,
        scenario_container.get("wavelength_m"),
        link_distance_m,
        allow_zero_turbulence_reference=allow_zero,
    )


def _coefficient_like(
    c_phi: float | torch.Tensor,
    modulation_variance: torch.Tensor,
) -> torch.Tensor:
    coefficient = torch.as_tensor(
        c_phi,
        dtype=modulation_variance.dtype,
        device=modulation_variance.device,
    )
    if not bool(torch.all(torch.isfinite(coefficient))) or bool(torch.any(coefficient < 0.0)):
        raise ValueError("c_phi must be finite and nonnegative.")
    try:
        torch.broadcast_shapes(coefficient.shape, modulation_variance.shape)
    except RuntimeError as error:
        raise ValueError("c_phi must be scalar or broadcastable to V_A.") from error
    return coefficient


def phase_excess_noise(
    modulation_variance: torch.Tensor,
    c_phi: float | torch.Tensor,
) -> torch.Tensor:
    """Return the differentiable action-dependent term ``c_phi * V_A``."""

    modulation_variance = torch.as_tensor(modulation_variance)
    if not modulation_variance.is_floating_point():
        raise ValueError("modulation_variance must be a floating tensor.")
    if not bool(torch.all(torch.isfinite(modulation_variance))) or bool(
        torch.any(modulation_variance < 0.0)
    ):
        raise ValueError("modulation_variance must be finite and nonnegative.")
    return _coefficient_like(c_phi, modulation_variance) * modulation_variance


def total_excess_noise(
    epsilon_base: torch.Tensor,
    modulation_variance: torch.Tensor,
    c_phi: float | torch.Tensor,
) -> torch.Tensor:
    """Return post-action input-referred noise ``epsilon_base + c_phi*V_A``.

    The implementation intentionally keeps the ``V_A`` tensor in the torch
    graph, so that its phase-noise gradient is exactly ``c_phi``.
    """

    modulation_variance = torch.as_tensor(modulation_variance)
    epsilon_base = torch.as_tensor(
        epsilon_base,
        dtype=modulation_variance.dtype,
        device=modulation_variance.device,
    )
    if not bool(torch.all(torch.isfinite(epsilon_base))) or bool(torch.any(epsilon_base < 0.0)):
        raise ValueError("epsilon_base must be finite and nonnegative.")
    phase_component = phase_excess_noise(modulation_variance, c_phi)
    try:
        torch.broadcast_shapes(epsilon_base.shape, phase_component.shape)
    except RuntimeError as error:
        raise ValueError("epsilon_base must be scalar or broadcastable to V_A.") from error
    return epsilon_base + phase_component
