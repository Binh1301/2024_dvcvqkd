"""Exact C4 coherent-state Gram evaluation of the paper source moments."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import torch

from src.modulation.joint_ps_gs import Ensemble
from src.modulation.qam256 import c4_orbit_indices


@dataclass(frozen=True)
class GramMomentResult:
    coherent_correlation: torch.Tensor
    w: torch.Tensor
    diagnostics: tuple[dict[str, Any], ...]


def c4_gram_source_moments(
    ensemble: Ensemble,
    *,
    density_eigenvalue_tolerance: float,
    physicality_tolerance: float = 1e-10,
) -> GramMomentResult:
    """Compute thresholded ``C,w`` without a Fock cutoff.

    The transformation is an exact unitary C4 block diagonalization of the
    weighted coherent-state Gram matrix. It retains the paper's absolute
    density-eigenvalue support rule unchanged.
    """

    ensemble.validate()
    if not ensemble.c4_symmetric:
        raise ValueError("C4 Gram moments require a declared C4 ensemble.")
    if ensemble.probabilities.dtype != torch.float64 or ensemble.declared_va.dtype != torch.float64:
        raise TypeError("C4 Gram production requires float64 probabilities and declared VA.")
    if ensemble.amplitudes.dtype != torch.complex128:
        raise TypeError("C4 Gram production requires complex128 amplitudes.")
    if any(value.device.type != "cpu" for value in (
        ensemble.probabilities, ensemble.amplitudes, ensemble.declared_va
    )):
        raise ValueError("C4 Gram certification currently requires CPU tensors.")
    for name, value in (
        ("density_eigenvalue_tolerance", density_eigenvalue_tolerance),
        ("physicality_tolerance", physicality_tolerance),
    ):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive.")
    indices = c4_orbit_indices(device=ensemble.probabilities.device)
    rotations = torch.tensor(
        [1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j],
        dtype=torch.complex128, device=ensemble.probabilities.device,
    )
    correlations = []
    penalties = []
    diagnostics = []
    for batch in range(ensemble.probabilities.shape[0]):
        grouped_probabilities = ensemble.probabilities[batch, indices]
        if not torch.allclose(
            grouped_probabilities, grouped_probabilities[:, :1].expand_as(grouped_probabilities),
            rtol=1e-12, atol=1e-14,
        ):
            raise ValueError("C4 Gram moments require tied orbit probabilities.")
        prototypes = ensemble.amplitudes[batch, indices[:, 0]]
        symbol_probabilities = grouped_probabilities[:, 0]
        square_root_weights = torch.sqrt(
            symbol_probabilities[:, None] * symbol_probabilities[None, :]
        )
        blocks = []
        for difference in range(4):
            rotated = rotations[difference] * prototypes
            overlap = torch.exp(
                -0.5 * (
                    prototypes.abs().square()[:, None]
                    + rotated.abs().square()[None, :]
                )
                + prototypes.conj()[:, None] * rotated[None, :]
            )
            blocks.append(square_root_weights * overlap)
        sectors = []
        eigenvalues = []
        eigenvectors = []
        for sector in range(4):
            matrix = sum(
                blocks[difference] * rotations[(sector * difference) % 4]
                for difference in range(4)
            )
            matrix = 0.5 * (matrix + matrix.mH)
            values, vectors = torch.linalg.eigh(matrix)
            if bool(torch.any(values < -density_eigenvalue_tolerance)):
                raise ValueError("A C4 Gram sector has a materially negative eigenvalue.")
            sectors.append(matrix)
            eigenvalues.append(values)
            eigenvectors.append(vectors)
        supports = [values > density_eigenvalue_tolerance for values in eigenvalues]
        if any(not bool(torch.any(support)) for support in supports):
            raise ValueError("A C4 Gram sector has empty retained support.")
        a_tau_blocks = []
        correlation = torch.zeros((), dtype=torch.float64, device=prototypes.device)
        for sector in range(4):
            previous = (sector - 1) % 4
            row_values = eigenvalues[sector][supports[sector]]
            column_values = eigenvalues[previous][supports[previous]]
            row_vectors = eigenvectors[sector][:, supports[sector]]
            column_vectors = eigenvectors[previous][:, supports[previous]]
            matrix_element = row_vectors.mH @ (prototypes[:, None] * column_vectors)
            a_support = (
                torch.sqrt(row_values)[:, None] * matrix_element
                / torch.sqrt(column_values)[None, :]
            )
            correlation = correlation + torch.sum(
                torch.sqrt(row_values)[:, None]
                * torch.sqrt(column_values)[None, :]
                * a_support.abs().square()
            ).real
            a_tau_blocks.append(
                torch.sqrt(row_values)[:, None] * a_support
                / torch.sqrt(column_values)[None, :]
            )
        coefficients = []
        for sector in range(4):
            values = eigenvalues[sector][supports[sector]]
            vectors = eigenvectors[sector][:, supports[sector]]
            coefficients.append(
                torch.sqrt(values)[:, None] * vectors.mH
                / (2.0 * torch.sqrt(symbol_probabilities))[None, :]
            )
        transformed = [
            a_tau_blocks[sector] @ coefficients[(sector - 1) % 4]
            for sector in range(4)
        ]
        inner = sum(
            torch.sum(coefficients[sector].conj() * transformed[sector], dim=0)
            for sector in range(4)
        )
        first_term = sum(
            torch.sum(
                eigenvalues[(sector - 1) % 4][supports[(sector - 1) % 4]][None, :]
                * a_tau_blocks[sector].abs().square()
            )
            for sector in range(4)
        ).real
        penalty = first_term - torch.sum(
            4.0 * symbol_probabilities * inner.abs().square()
        ).real
        if not bool(torch.isfinite(correlation)) or not bool(torch.isfinite(penalty)):
            raise FloatingPointError("C4 Gram source moments returned NaN or Inf.")
        if bool(penalty < -physicality_tolerance):
            raise ValueError("C4 Gram non-Gaussian penalty is materially negative.")
        correlations.append(correlation)
        penalties.append(penalty)
        retained = torch.cat([values[support] for values, support in zip(eigenvalues, supports)])
        all_values = torch.cat(eigenvalues)
        diagnostics.append({
            "expected_coherent_state_rank_from_unique_float_amplitudes": len(set(
                complex(value) for value in ensemble.amplitudes[batch].detach().tolist()
            )),
            "numerical_retained_rank": int(sum(int(support.sum()) for support in supports)),
            "support_size": int(sum(int(support.sum()) for support in supports)),
            "sector_support_sizes": [int(support.sum()) for support in supports],
            "sector_support_masks": [
                [bool(value) for value in support.detach().tolist()]
                for support in supports
            ],
            "sector_minimum_retained_eigenvalues": [
                float(values[support].detach().min())
                for values, support in zip(eigenvalues, supports)
            ],
            "sector_maximum_suppressed_eigenvalues": [
                (
                    float(values[~support].detach().max())
                    if bool(torch.any(~support)) else None
                )
                for values, support in zip(eigenvalues, supports)
            ],
            "minimum_eigenvalue": float(all_values.detach().min()),
            "maximum_eigenvalue": float(all_values.detach().max()),
            "nearest_suppressed_eigenvalue_below_threshold": float(
                max(
                    values[~support].detach().max() if bool(torch.any(~support))
                    else torch.tensor(float("-inf"), dtype=torch.float64)
                    for values, support in zip(eigenvalues, supports)
                )
            ),
            "minimum_retained_eigenvalue": float(retained.detach().min()),
            "retained_condition_number": float(
                (retained.detach().max() / retained.detach().min())
            ),
        })
    return GramMomentResult(torch.stack(correlations), torch.stack(penalties), tuple(diagnostics))
