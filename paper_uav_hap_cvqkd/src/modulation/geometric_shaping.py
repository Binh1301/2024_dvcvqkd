"""Global, channel-independent GS coordinates from paper Eqs. (151)--(153)."""

from __future__ import annotations

import torch
from torch import nn


class GlobalGeometricShaping(nn.Module):
    def __init__(self, initial_constellation: torch.Tensor) -> None:
        super().__init__()
        if initial_constellation.shape != (256,) or not initial_constellation.is_complex():
            raise ValueError("initial_constellation must have complex shape [256].")
        coordinates = torch.view_as_real(initial_constellation.to(torch.complex128)).clone()
        self.raw_coordinates = nn.Parameter(coordinates)

    def forward(self) -> torch.Tensor:
        return torch.view_as_complex(self.raw_coordinates.contiguous())

