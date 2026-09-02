"""Paper standard-form covariance, Eqs. (111)--(122), with explicit guards."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from src.modulation.joint_ps_gs import Ensemble


SYMMETRY_SCALE_FLOOR = 1e-15


class PhysicalityError(ValueError):
    """Raised when paper covariance assumptions or physicality checks fail."""


@dataclass(frozen=True)
class SymmetryDiagnostics:
    variance_i: torch.Tensor
    variance_q: torch.Tensor
    covariance_iq: torch.Tensor
    maximum_relative_anisotropy: float
    maximum_relative_cross_covariance: float
    standard_form_supported: bool


@dataclass(frozen=True)
class CovarianceResult:
    matrix: torch.Tensor
    lambda1: torch.Tensor
    lambda2: torch.Tensor
    lambda3: torch.Tensor
    symmetry: SymmetryDiagnostics
    numerical_repairs: tuple[str, ...]


def quadrature_symmetry_diagnostics(
    ensemble: Ensemble,
    tolerance: float = 1e-8,
) -> SymmetryDiagnostics:
    probabilities = ensemble.probabilities
    i_values = ensemble.amplitudes.real
    q_values = ensemble.amplitudes.imag
    mean_i = torch.sum(probabilities * i_values, dim=-1, keepdim=True)
    mean_q = torch.sum(probabilities * q_values, dim=-1, keepdim=True)
    centered_i = i_values - mean_i
    centered_q = q_values - mean_q
    variance_i = torch.sum(probabilities * centered_i.square(), dim=-1)
    variance_q = torch.sum(probabilities * centered_q.square(), dim=-1)
    covariance_iq = torch.sum(probabilities * centered_i * centered_q, dim=-1)
    scale = torch.maximum(
        (variance_i + variance_q) / 2.0,
        torch.full_like(variance_i, SYMMETRY_SCALE_FLOOR),
    )
    relative_anisotropy = torch.abs(variance_i - variance_q) / scale
    relative_cross = torch.abs(covariance_iq) / scale
    maximum_anisotropy = float(relative_anisotropy.detach().max())
    maximum_cross = float(relative_cross.detach().max())
    supported = maximum_anisotropy <= tolerance and maximum_cross <= tolerance
    return SymmetryDiagnostics(
        variance_i=variance_i,
        variance_q=variance_q,
        covariance_iq=covariance_iq,
        maximum_relative_anisotropy=maximum_anisotropy,
        maximum_relative_cross_covariance=maximum_cross,
        standard_form_supported=supported,
    )


def standard_form_covariance(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    correlation: torch.Tensor,
    *,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    numerical_tolerance: float = 1e-10,
) -> CovarianceResult:
    ensemble.validate()
    symmetry = quadrature_symmetry_diagnostics(ensemble, symmetry_tolerance)
    if require_supported_symmetry and not symmetry.standard_form_supported:
        raise PhysicalityError(
            "The paper standard-form covariance is not justified for this asymmetric ensemble."
        )
    t = transmittance.reshape(-1)
    eps = epsilon.reshape(-1)
    c = correlation.reshape(-1)
    va = ensemble.computed_va()
    if not (t.shape == eps.shape == c.shape == va.shape):
        raise ValueError("Covariance inputs must have one value per ensemble state.")
    a = va + 1.0
    b = 1.0 + t * va + t * eps
    matrix = torch.zeros((t.shape[0], 4, 4), dtype=torch.float64, device=t.device)
    matrix[:, 0, 0] = a
    matrix[:, 1, 1] = a
    matrix[:, 2, 2] = b
    matrix[:, 3, 3] = b
    matrix[:, 0, 2] = matrix[:, 2, 0] = c
    matrix[:, 1, 3] = matrix[:, 3, 1] = -c
    delta = a.square() + b.square() - 2.0 * c.square()
    determinant = (a * b - c.square()).square()
    discriminant_raw = delta.square() - 4.0 * determinant
    if bool(torch.any(discriminant_raw < -numerical_tolerance)):
        raise PhysicalityError("Symplectic discriminant is materially negative.")
    repairs: list[str] = []
    if bool(torch.any(discriminant_raw < 0.0)):
        repairs.append("clamped tiny negative symplectic discriminant to zero")
    discriminant = torch.clamp_min(discriminant_raw, 0.0)
    root = torch.sqrt(discriminant)
    lambda1_squared = 0.5 * (delta + root)
    lambda2_squared = 0.5 * (delta - root)
    if bool(torch.any(lambda1_squared < -numerical_tolerance)) or bool(
        torch.any(lambda2_squared < -numerical_tolerance)
    ):
        raise PhysicalityError("Negative squared symplectic eigenvalue.")
    lambda1 = torch.sqrt(torch.clamp_min(lambda1_squared, 0.0))
    lambda2 = torch.sqrt(torch.clamp_min(lambda2_squared, 0.0))
    lambda3 = a - c.square() / (b + 1.0)
    minimum_lambda = torch.minimum(torch.minimum(lambda1, lambda2), lambda3)
    if bool(torch.any(minimum_lambda < 1.0 - numerical_tolerance)):
        raise PhysicalityError("Covariance violates the uncertainty condition lambda>=1.")
    return CovarianceResult(matrix, lambda1, lambda2, lambda3, symmetry, tuple(repairs))
