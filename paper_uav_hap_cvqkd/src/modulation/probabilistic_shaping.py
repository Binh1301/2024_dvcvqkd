"""Frozen fourfold-symmetric adaptive probabilistic-shaping policy."""

from __future__ import annotations

import torch
from torch import nn

from .qam256 import c4_orbit_masses, expand_c4_orbit_masses


def channel_features(transmittance: torch.Tensor, epsilon: torch.Tensor) -> torch.Tensor:
    transmittance = torch.as_tensor(transmittance, dtype=torch.float64).reshape(-1)
    epsilon = torch.as_tensor(epsilon, dtype=torch.float64, device=transmittance.device).reshape(-1)
    if epsilon.numel() == 1:
        epsilon = epsilon.expand_as(transmittance)
    if epsilon.shape != transmittance.shape:
        raise ValueError("epsilon must be scalar or match transmittance.")
    if not bool(torch.all(torch.isfinite(transmittance))) or bool(torch.any(transmittance <= 0.0)):
        raise ValueError("PS/V_A channel features require finite T>0.")
    if not bool(torch.all(torch.isfinite(epsilon))) or bool(torch.any(epsilon < 0.0)):
        raise ValueError("epsilon must be finite and nonnegative.")
    return torch.stack((torch.log10(transmittance), epsilon), dim=-1)


class ProbabilisticShapingNetwork(nn.Module):
    """``Linear(2,128) -> ReLU -> Linear(128,64) -> softmax`` orbit policy."""

    def __init__(self, initial_pmf: torch.Tensor | None = None) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(2, 128, dtype=torch.float64),
            nn.ReLU(),
            nn.Linear(128, 64, dtype=torch.float64),
        )
        if initial_pmf is not None:
            if initial_pmf.shape != (256,) or bool(torch.any(initial_pmf <= 0.0)):
                raise ValueError("initial_pmf must be a strictly positive 256-symbol PMF.")
            initial_orbit_masses = c4_orbit_masses(initial_pmf.to(dtype=torch.float64))
            final_layer = self.network[-1]
            with torch.no_grad():
                final_layer.weight.zero_()
                final_layer.bias.copy_(torch.log(initial_orbit_masses))

    def orbit_masses(self, transmittance: torch.Tensor, epsilon: torch.Tensor) -> torch.Tensor:
        """Return the 64 strictly positive, normalized orbit masses ``q_k``."""

        logits = self.network(channel_features(transmittance, epsilon))
        return torch.softmax(logits, dim=-1)

    def forward(self, transmittance: torch.Tensor, epsilon: torch.Tensor) -> torch.Tensor:
        """Return the row-major 256-symbol PMF with ``p[k,r] = q[k]/4``."""

        return expand_c4_orbit_masses(self.orbit_masses(transmittance, epsilon))
