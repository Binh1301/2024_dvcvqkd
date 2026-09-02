"""Small shared numerical assertions."""

from __future__ import annotations

import numpy as np
import torch


def require_finite(name: str, values) -> None:
    finite = torch.isfinite(values) if isinstance(values, torch.Tensor) else np.isfinite(values)
    if not bool(finite.all()):
        raise FloatingPointError(f"{name} contains NaN or Inf.")

