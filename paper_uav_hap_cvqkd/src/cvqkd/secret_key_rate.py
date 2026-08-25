"""Asymptotic reverse-reconciliation SKR, paper Eqs. (131)--(136)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch


@dataclass(frozen=True)
class FadingKeyRate:
    instantaneous_raw: torch.Tensor
    fading_average_raw: torch.Tensor
    instantaneous_positive_part: torch.Tensor
    fading_average_positive_part: torch.Tensor


def fading_secret_key_rate(
    mutual_information: torch.Tensor,
    holevo_information: torch.Tensor,
    beta_reconciliation: float,
) -> FadingKeyRate:
    if mutual_information.shape != holevo_information.shape:
        raise ValueError("MI and Holevo arrays must have identical shape.")
    if not math.isfinite(beta_reconciliation) or not 0.0 < beta_reconciliation <= 1.0:
        raise ValueError("beta_reconciliation must lie in (0,1].")
    if not bool(torch.all(torch.isfinite(mutual_information))) or not bool(
        torch.all(torch.isfinite(holevo_information))
    ):
        raise ValueError("MI and Holevo values must be finite.")
    raw = float(beta_reconciliation) * mutual_information - holevo_information
    positive = torch.clamp_min(raw, 0.0)
    return FadingKeyRate(raw, raw.mean(), positive, positive.mean())

