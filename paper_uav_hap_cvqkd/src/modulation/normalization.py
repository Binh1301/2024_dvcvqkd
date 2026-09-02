"""Frozen scalar physical-energy normalization without weighted centering."""

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


def physical_amplitudes(
    probabilities: torch.Tensor,
    relative_constellation: torch.Tensor,
    modulation_variance: torch.Tensor,
    *,
    minimum_energy: float = 1e-15,
) -> torch.Tensor:
    """Apply exactly ``alpha = sqrt(V_A/(2 E_x)) x`` statewise.

    ``relative_constellation`` is shared across channel states in the frozen
    transmitter.  This function performs no centering, orbitwise normalization,
    or state-dependent deformation; only one real scalar is applied per state.
    """

    validate_probabilities(probabilities)
    probabilities_batch = probabilities.unsqueeze(0) if probabilities.ndim == 1 else probabilities
    if not relative_constellation.is_complex() or relative_constellation.ndim not in (1, 2):
        raise ValueError("relative_constellation must be complex with shape [M] or [B,M].")
    if relative_constellation.ndim == 1:
        relative_batch = relative_constellation.unsqueeze(0).expand(probabilities_batch.shape[0], -1)
    else:
        relative_batch = relative_constellation
    if relative_batch.shape != probabilities_batch.shape:
        raise ValueError("probabilities and relative_constellation shapes are incompatible.")
    if not bool(torch.all(torch.isfinite(relative_batch.real))) or not bool(
        torch.all(torch.isfinite(relative_batch.imag))
    ):
        raise ValueError("relative_constellation contains NaN or Inf.")
    variance = torch.as_tensor(
        modulation_variance,
        dtype=relative_batch.real.dtype,
        device=relative_batch.device,
    ).reshape(-1)
    if variance.numel() == 1:
        variance = variance.expand(relative_batch.shape[0])
    if variance.shape[0] != relative_batch.shape[0]:
        raise ValueError("modulation_variance must be scalar or have shape [B].")
    if not bool(torch.all(torch.isfinite(variance))) or bool(torch.any(variance <= 0.0)):
        raise ValueError("modulation_variance must be finite and positive.")
    relative_energy = torch.sum(
        probabilities_batch * relative_batch.abs().square(), dim=-1
    )
    if bool(torch.any(~torch.isfinite(relative_energy))) or bool(
        torch.any(relative_energy <= minimum_energy)
    ):
        raise ValueError("Relative constellation energy must be finite and positive.")
    scale = torch.sqrt(variance / (2.0 * relative_energy))
    return scale.unsqueeze(-1) * relative_batch
