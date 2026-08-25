"""Paper Eq. (185) loss with explicit, configured regularizers."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from src.modulation.joint_ps_gs import Ensemble


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
    negative_skr = -raw_secret_key_rate.mean()
    points = torch.view_as_real(ensemble.raw_constellation.to(torch.complex128))
    pairwise = torch.cdist(points, points)
    off_diagonal = ~torch.eye(points.shape[0], dtype=torch.bool, device=points.device)
    separation = torch.exp(-pairwise.square() / separation_scale**2)[off_diagonal].mean()
    peak = torch.relu(ensemble.amplitudes.abs().square() - peak_energy_limit).square().mean()
    drift = (ensemble.raw_constellation - initial_raw_constellation).abs().square().mean()
    total = (
        negative_skr
        + lambda_separation * separation
        + lambda_peak * peak
        + lambda_drift * drift
    )
    return LossComponents(total, negative_skr, separation, peak, drift)

