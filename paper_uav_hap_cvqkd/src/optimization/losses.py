"""Frozen raw-SKR objective and exact optional geometry regularizers."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from src.modulation.joint_ps_gs import Ensemble
from src.modulation.geometric_shaping import canonical_c4_relative_constellation


@dataclass(frozen=True)
class LossComponents:
    total: torch.Tensor
    negative_skr: torch.Tensor
    separation: torch.Tensor
    peak: torch.Tensor
    drift: torch.Tensor


def paper_loss(
    raw_secret_key_rate: torch.Tensor,
    ensemble: Ensemble,
    initial_raw_constellation: torch.Tensor,
    *,
    lambda_separation: float = 0.0,
    lambda_peak: float = 0.0,
    lambda_drift: float = 0.0,
    separation_scale: float = 0.15,
    peak_energy_limit: float = 5.0,
) -> LossComponents:
    if any(value < 0.0 for value in (lambda_separation, lambda_peak, lambda_drift)):
        raise ValueError("Regularizer coefficients must be nonnegative.")
    if separation_scale <= 0.0 or peak_energy_limit <= 0.0:
        raise ValueError("Regularizer thresholds must be positive.")
    negative_skr = -raw_secret_key_rate.mean()
    relative = ensemble.relative_constellation
    points = torch.view_as_real(relative.to(torch.complex128))
    pairwise = torch.cdist(points, points)
    upper = torch.triu_indices(points.shape[0], points.shape[0], offset=1, device=points.device)
    normalized_gap = 1.0 - pairwise[upper[0], upper[1]] / separation_scale
    separation = torch.relu(normalized_gap).square().mean()
    maximum_energy = ensemble.amplitudes.abs().square().amax(dim=-1)
    peak = torch.relu(maximum_energy / peak_energy_limit - 1.0).square().mean()
    reference = canonical_c4_relative_constellation(
        initial_raw_constellation.to(device=relative.device, dtype=relative.dtype)
    )
    correlation = torch.sum(relative * reference.conj())
    drift = (
        relative.abs().square().mean()
        + reference.abs().square().mean()
        - 2.0 * correlation.abs() / relative.numel()
    )
    total = (
        negative_skr
        + lambda_separation * separation
        + lambda_peak * peak
        + lambda_drift * drift
    )
    return LossComponents(total, negative_skr, separation, peak, drift)
