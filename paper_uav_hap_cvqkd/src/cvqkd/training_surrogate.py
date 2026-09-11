"""TRAINING_SURROGATE_ONLY smooth C4 source moments.

This module is deliberately separate from :mod:`gram_moments`.  It is a
search aid for short transmitter optimization experiments; its regularized
complex128 values are never an authoritative security result.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch


@dataclass(frozen=True)
class TrainingSurrogateResult:
    """Regularized source moments and diagnostics for optimization only."""

    coherent_correlation: torch.Tensor
    w: torch.Tensor
    diagnostics: dict[str, float | str]


def _c4_sectors(p: torch.Tensor, z: torch.Tensor) -> list[torch.Tensor]:
    rotations = torch.tensor((1.0, 1.0j, -1.0, -1.0j), dtype=torch.complex128, device=z.device)
    weight = torch.sqrt(p[:, None] * p[None, :])
    blocks: list[torch.Tensor] = []
    for rotation in rotations:
        right = rotation * z
        blocks.append(
            weight
            * torch.exp(
                -0.5 * (z.abs().square()[:, None] + right.abs().square()[None, :])
                + z.conj()[:, None] * right[None, :]
            )
        )
    sectors: list[torch.Tensor] = []
    for sector in range(4):
        matrix = sum(
            blocks[d] * rotations[(sector * d) % 4] for d in range(4)
        )
        sectors.append(0.5 * (matrix + matrix.mH))
    return sectors


def _right_solve(matrix: torch.Tensor, rhs: torch.Tensor) -> torch.Tensor:
    """Return X in X @ matrix = rhs without materializing an inverse."""

    return torch.linalg.solve(matrix.transpose(-2, -1), rhs.transpose(-2, -1)).transpose(-2, -1)


def c4_training_surrogate(
    probabilities: torch.Tensor,
    prototypes: torch.Tensor,
    *,
    regularization: float = 1.0e-10,
) -> TrainingSurrogateResult:
    """Evaluate smooth regularized C4 source moments for training search.

    ``probabilities`` and ``prototypes`` are the 64 representative entries
    from the expanded 256-state arrays (each probability is the per-symbol
    mass, so the four entries in an orbit sum to its orbit mass).  The shift
    is applied to every C4 sector before the spectral square-root and right
    solves.  This is an analysis surrogate, not a support truncation, exact
    oracle, or security replacement.
    """

    if probabilities.ndim != 1 or probabilities.shape != (64,):
        raise ValueError("training surrogate requires 64 orbit probabilities")
    if prototypes.ndim != 1 or prototypes.shape != (64,) or not prototypes.is_complex():
        raise ValueError("training surrogate requires 64 complex orbit prototypes")
    if probabilities.dtype != torch.float64 or prototypes.dtype != torch.complex128:
        raise TypeError("training surrogate requires float64/complex128 inputs")
    if not math.isfinite(regularization) or regularization <= 0.0:
        raise ValueError("regularization must be finite and positive")
    if bool(torch.any(probabilities <= 0.0)) or not bool(torch.isfinite(probabilities).all()):
        raise ValueError("training surrogate requires strictly positive finite probabilities")
    if not bool(torch.isfinite(prototypes.real).all()) or not bool(torch.isfinite(prototypes.imag).all()):
        raise ValueError("training surrogate prototypes must be finite")

    sectors = _c4_sectors(probabilities, prototypes)
    identity = torch.eye(64, dtype=torch.complex128, device=prototypes.device)
    shifted = [matrix + regularization * identity for matrix in sectors]
    eigensystems = [torch.linalg.eigh(matrix) for matrix in shifted]
    eigenvalues = [values for values, _ in eigensystems]
    minimum = min(values.min() for values in eigenvalues)
    if bool(torch.any(minimum <= 0.0)):
        raise FloatingPointError("training surrogate regularization did not make sectors positive")

    square = [
        vectors @ torch.diag(torch.sqrt(values)).to(torch.complex128) @ vectors.mH
        for values, vectors in eigensystems
    ]
    diagonal_z = torch.diag(prototypes)
    diagonal_weight = torch.diag(1.0 / (2.0 * torch.sqrt(probabilities))).to(torch.complex128)
    correlation = torch.zeros((), dtype=torch.float64, device=prototypes.device)
    coefficients: list[torch.Tensor] = []
    a_matrices: list[torch.Tensor] = []

    for sector in range(4):
        previous = (sector - 1) % 4
        b = _right_solve(square[previous], square[sector] @ diagonal_z)
        correlation = correlation + torch.trace(
            square[sector] @ b @ square[previous] @ b.mH
        ).real
        a = _right_solve(shifted[previous], shifted[sector] @ diagonal_z)
        a_matrices.append(a)
        coefficients.append(square[sector] @ diagonal_weight)

    transformed = [
        a_matrices[sector] @ coefficients[(sector - 1) % 4]
        for sector in range(4)
    ]

    inner = sum(
        torch.sum(coefficients[sector].conj() * transformed[sector], dim=0)
        for sector in range(4)
    )
    residual = sum(
        torch.sum(
            4.0
            * probabilities
            * torch.sum(
                (transformed[sector] - coefficients[sector] * inner[None, :]).abs().square(),
                dim=0,
            )
        ).real
        for sector in range(4)
    )
    if not bool(torch.isfinite(correlation)) or not bool(torch.isfinite(residual)):
        raise FloatingPointError("training surrogate returned NaN or Inf")
    return TrainingSurrogateResult(
        coherent_correlation=correlation,
        w=residual,
        diagnostics={
            "marker": "TRAINING_SURROGATE_ONLY",
            "regularization": float(regularization),
            "minimum_shifted_eigenvalue": float(minimum.detach()),
            "maximum_shifted_eigenvalue": float(max(values.max() for values in eigenvalues).detach()),
        },
    )


__all__ = ["TrainingSurrogateResult", "c4_training_surrogate"]
