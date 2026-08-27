"""Protocol metadata and channel-state validation."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class ProtocolAssumptions:
    detection: str = "ideal heterodyne"
    reconciliation: str = "asymptotic reverse reconciliation"
    detector_efficiency: float | None = None
    electronic_noise_snu: float | None = None
    finite_size: bool = False
    composable_security: bool = False
    csi: str = "exact instantaneous (T, epsilon) oracle"
    feedback_model: str | None = None
    security_scope: str = "author-accepted asymptotic covariance-based DM-CV-QKD bound"
    attack_class: str | None = None


PAPER_ASSUMPTIONS = ProtocolAssumptions()


def validate_channel_state(
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    allow_zero_transmittance: bool = True,
) -> tuple[torch.Tensor, torch.Tensor]:
    transmittance = torch.as_tensor(transmittance, dtype=torch.float64).reshape(-1)
    epsilon = torch.as_tensor(epsilon, dtype=torch.float64, device=transmittance.device).reshape(-1)
    if epsilon.numel() == 1:
        epsilon = epsilon.expand_as(transmittance)
    if epsilon.shape != transmittance.shape:
        raise ValueError("epsilon must be scalar or match transmittance.")
    lower_invalid = transmittance < 0.0 if allow_zero_transmittance else transmittance <= 0.0
    if not bool(torch.all(torch.isfinite(transmittance))) or bool(torch.any(lower_invalid)):
        relation = "nonnegative" if allow_zero_transmittance else "positive"
        raise ValueError(f"transmittance must be finite and {relation}.")
    if bool(torch.any(transmittance > 1.0)):
        raise ValueError("Power transmittance cannot exceed one.")
    if not bool(torch.all(torch.isfinite(epsilon))) or bool(torch.any(epsilon < 0.0)):
        raise ValueError("epsilon must be finite and nonnegative.")
    return transmittance, epsilon
