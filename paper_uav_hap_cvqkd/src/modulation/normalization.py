"""Probability-weighted normalization from paper Eqs. (154)--(168)."""

from __future__ import annotations

import torch


def validate_probabilities(probabilities: torch.Tensor, tolerance: float = 1e-10) -> None:
    if probabilities.ndim not in (1, 2):
        raise ValueError("probabilities must have shape [M] or [B,M].")
    if not probabilities.is_floating_point():
        raise TypeError("probabilities must be real floating-point values.")
    if not bool(torch.all(torch.isfinite(probabilities))):
        raise ValueError("probabilities contain NaN or Inf.")
    if bool(torch.any(probabilities < 0.0)):
        raise ValueError("probabilities must be nonnegative.")
    sums = probabilities.sum(dim=-1)
    if not bool(torch.all(torch.abs(sums - 1.0) <= tolerance)):
        raise ValueError("probabilities must sum to one statewise.")


def weighted_center_and_normalize(
    probabilities: torch.Tensor,
    raw_constellation: torch.Tensor,
    *,
    minimum_energy: float = 1e-15,
) -> torch.Tensor:
    """Enforce statewise ``sum p*x=0`` and ``sum p*|x|^2=1``.

    A shared raw geometry is expanded across channel states. Since the weights
    enter both centering and scaling, PS changes normalized/physical coordinates
    even when the raw geometry is fixed.
    """

    validate_probabilities(probabilities)
    probabilities_batch = probabilities.unsqueeze(0) if probabilities.ndim == 1 else probabilities
    if not raw_constellation.is_complex():
        raise TypeError("raw_constellation must be complex.")
    if raw_constellation.ndim == 1:
        raw_batch = raw_constellation.unsqueeze(0).expand(probabilities_batch.shape[0], -1)
    elif raw_constellation.ndim == 2:
        raw_batch = raw_constellation
    else:
        raise ValueError("raw_constellation must have shape [M] or [B,M].")
    if raw_batch.shape != probabilities_batch.shape:
        raise ValueError("probabilities and constellation shapes are incompatible.")
    if not bool(torch.all(torch.isfinite(raw_batch.real))) or not bool(
        torch.all(torch.isfinite(raw_batch.imag))
    ):
        raise ValueError("raw_constellation contains NaN or Inf.")
    centroid = torch.sum(probabilities_batch * raw_batch, dim=-1, keepdim=True)
    centered = raw_batch - centroid
    energy = torch.sum(probabilities_batch * centered.abs().square(), dim=-1, keepdim=True)
    if bool(torch.any(~torch.isfinite(energy))) or bool(torch.any(energy <= minimum_energy)):
        raise ValueError("Weighted constellation energy must be finite and positive.")
    return centered / torch.sqrt(energy)


def physical_amplitudes(unit_constellation: torch.Tensor, modulation_variance: torch.Tensor) -> torch.Tensor:
    if unit_constellation.ndim != 2 or not unit_constellation.is_complex():
        raise ValueError("unit_constellation must have complex shape [B,M].")
    variance = torch.as_tensor(
        modulation_variance,
        dtype=unit_constellation.real.dtype,
        device=unit_constellation.device,
    ).reshape(-1)
    if variance.numel() == 1:
        variance = variance.expand(unit_constellation.shape[0])
    if variance.shape[0] != unit_constellation.shape[0]:
        raise ValueError("modulation_variance must be scalar or have shape [B].")
    if not bool(torch.all(torch.isfinite(variance))) or bool(torch.any(variance <= 0.0)):
        raise ValueError("modulation_variance must be finite and positive.")
    return torch.sqrt(variance / 2.0).unsqueeze(-1) * unit_constellation

