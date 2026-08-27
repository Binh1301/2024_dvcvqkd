"""Frozen global C4-tied geometric-shaping parameterization."""

from __future__ import annotations

import torch
from torch import nn

from .qam256 import C4_ORBIT_COUNT, c4_orbit_indices, expand_c4_orbit_values


def canonical_c4_relative_constellation(constellation: torch.Tensor) -> torch.Tensor:
    """Validate a C4 constellation and remove its positive global scale gauge."""

    if constellation.shape != (256,) or not constellation.is_complex():
        raise ValueError("constellation must have complex shape [256].")
    indices = c4_orbit_indices(device=constellation.device)
    prototypes = constellation[indices[:, 0]]
    reconstructed = expand_c4_orbit_values(prototypes)
    if not bool(torch.allclose(reconstructed, constellation, atol=1e-12, rtol=1e-12)):
        raise ValueError("constellation must obey the deterministic C4 orbit mapping.")
    mean_energy = prototypes.abs().square().mean()
    if not bool(torch.isfinite(mean_energy)) or bool(mean_energy <= 1e-15):
        raise ValueError("Global prototype RMS energy must be finite and positive.")
    return expand_c4_orbit_values(prototypes / torch.sqrt(mean_energy))


class GlobalGeometricShaping(nn.Module):
    """One channel-independent set of 64 complex orbit prototypes.

    The forward pass removes the irrelevant positive scale gauge using global
    unit RMS and expands the prototypes by exact 90-degree rotations into the
    existing 256-symbol row-major labeling.
    """

    def __init__(self, initial_constellation: torch.Tensor) -> None:
        super().__init__()
        if initial_constellation.shape != (256,) or not initial_constellation.is_complex():
            raise ValueError("initial_constellation must have complex shape [256].")
        initial = initial_constellation.to(torch.complex128)
        orbit_indices = c4_orbit_indices(device=initial.device)
        prototypes = initial[orbit_indices[:, 0]]
        canonical_c4_relative_constellation(initial)
        coordinates = torch.view_as_real(prototypes).clone()
        self.raw_coordinates = nn.Parameter(coordinates)

    def raw_prototypes(self) -> torch.Tensor:
        return torch.view_as_complex(self.raw_coordinates.contiguous())

    def relative_prototypes(self) -> torch.Tensor:
        prototypes = self.raw_prototypes()
        mean_energy = prototypes.abs().square().mean()
        if not bool(torch.isfinite(mean_energy)) or bool(mean_energy <= 1e-15):
            raise ValueError("Global prototype RMS energy must be finite and positive.")
        return prototypes / torch.sqrt(mean_energy)

    def forward(self) -> torch.Tensor:
        relative = self.relative_prototypes()
        if relative.shape != (C4_ORBIT_COUNT,):
            raise RuntimeError("Global GS must contain exactly 64 complex prototypes.")
        return expand_c4_orbit_values(relative)
