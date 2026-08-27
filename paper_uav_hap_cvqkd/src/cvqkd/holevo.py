"""Differentiable paper Holevo chain, Eqs. (103)--(126), with strict diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import torch

from src.modulation.joint_ps_gs import Ensemble
from .covariance import CovarianceResult, PhysicalityError, standard_form_covariance
from .protocol import validate_channel_state


@dataclass(frozen=True)
class HolevoResult:
    chi_be: torch.Tensor
    tau: torch.Tensor
    tau_trace: torch.Tensor
    w: torch.Tensor
    coherent_correlation: torch.Tensor
    z: torch.Tensor
    covariance: CovarianceResult
    diagnostics: dict[str, Any]


def coherent_state_vectors(amplitudes: torch.Tensor, fock_cutoff: int) -> torch.Tensor:
    if not isinstance(fock_cutoff, int) or fock_cutoff <= 1:
        raise ValueError("fock_cutoff must be an integer greater than one.")
    number = torch.arange(fock_cutoff, dtype=torch.float64, device=amplitudes.device)
    inverse_sqrt_factorial = torch.exp(-0.5 * torch.lgamma(number + 1.0))
    return (
        torch.exp(-0.5 * amplitudes.abs().square()).unsqueeze(-1)
        * amplitudes.unsqueeze(-1) ** number.to(torch.int64)
        * inverse_sqrt_factorial
    )


def density_operator(ensemble: Ensemble, fock_cutoff: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Eq. (103), with correct ``tau_nm=sum_i p_i f_i,n f_i,m*`` orientation."""

    ensemble.validate()
    fock = coherent_state_vectors(ensemble.amplitudes, fock_cutoff)
    tau = torch.einsum("bmi,bm,bmj->bij", fock, ensemble.probabilities, fock.conj())
    tau = 0.5 * (tau + tau.mH)
    return tau, fock


def annihilation_operator(fock_cutoff: int, device: torch.device) -> torch.Tensor:
    operator = torch.zeros((fock_cutoff, fock_cutoff), dtype=torch.complex128, device=device)
    indices = torch.arange(1, fock_cutoff, device=device)
    operator[indices - 1, indices] = torch.sqrt(indices.to(torch.float64)).to(torch.complex128)
    return operator


def bosonic_entropy(x: torch.Tensor) -> torch.Tensor:
    if bool(torch.any(x < 0.0)):
        raise PhysicalityError("Bosonic entropy received a negative occupation number.")
    positive = x > 0.0
    safe = torch.where(positive, x, torch.ones_like(x))
    value = (x + 1.0) * torch.log2(x + 1.0) - torch.where(
        positive, x * torch.log2(safe), torch.zeros_like(x)
    )
    return value


def holevo_information(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    fock_cutoff: int,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-8,
    density_eigenvalue_tolerance: float = 1e-12,
    physicality_tolerance: float = 1e-10,
) -> HolevoResult:
    for name, value in (
        ("symmetry_tolerance", symmetry_tolerance),
        ("density_trace_tolerance", density_trace_tolerance),
        ("density_eigenvalue_tolerance", density_eigenvalue_tolerance),
        ("physicality_tolerance", physicality_tolerance),
    ):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive.")
    ensemble.validate()
    transmittance, epsilon = validate_channel_state(transmittance, epsilon)
    transmittance = transmittance.to(ensemble.probabilities.device)
    epsilon = epsilon.to(ensemble.probabilities.device)
    tau, fock = density_operator(ensemble, fock_cutoff)
    tau_trace = torch.diagonal(tau, dim1=-2, dim2=-1).sum(dim=-1).real
    trace_error = torch.abs(tau_trace - 1.0)
    if bool(torch.any(trace_error > density_trace_tolerance)):
        raise PhysicalityError(
            "Fock truncation gives a density trace outside tolerance; increase fock_cutoff."
        )
    eigenvalues, eigenvectors = torch.linalg.eigh(tau)
    if bool(torch.any(eigenvalues < -density_eigenvalue_tolerance)):
        raise PhysicalityError("Density operator has a materially negative eigenvalue.")
    significant = eigenvalues > density_eigenvalue_tolerance
    safe = torch.where(significant, eigenvalues, torch.ones_like(eigenvalues))
    sqrt_values = torch.where(significant, torch.sqrt(safe), torch.zeros_like(safe))
    inverse_sqrt_values = torch.where(significant, torch.rsqrt(safe), torch.zeros_like(safe))
    tau_sqrt = (eigenvectors * sqrt_values.unsqueeze(-2)) @ eigenvectors.mH
    tau_inverse_sqrt = (eigenvectors * inverse_sqrt_values.unsqueeze(-2)) @ eigenvectors.mH
    a_operator = annihilation_operator(fock_cutoff, ensemble.probabilities.device)
    a_batch = a_operator.unsqueeze(0).expand(ensemble.probabilities.shape[0], -1, -1)
    c_operator = tau_sqrt @ a_batch @ tau_sqrt @ a_batch.mH
    coherent_correlation = torch.diagonal(c_operator, dim1=-2, dim2=-1).sum(dim=-1).real
    a_tau = tau_sqrt @ a_batch @ tau_inverse_sqrt
    first_moment = a_tau.mH @ a_tau
    t1 = torch.einsum("bmi,bij,bmj->bm", fock.conj(), first_moment, fock).real
    inner = torch.einsum("bmi,bij,bmj->bm", fock.conj(), a_tau, fock)
    w_raw = torch.sum(ensemble.probabilities * (t1 - inner.abs().square()), dim=-1)
    if bool(torch.any(w_raw < -physicality_tolerance)):
        raise PhysicalityError("Non-Gaussian penalty w is materially negative.")
    repairs: list[str] = []
    if bool(torch.any(w_raw < 0.0)):
        repairs.append("clamped tiny negative w to zero")
    w = torch.clamp_min(w_raw, 0.0)
    radicand = 2.0 * transmittance * epsilon * w
    z = 2.0 * torch.sqrt(transmittance) * coherent_correlation - torch.sqrt(radicand)
    covariance = standard_form_covariance(
        ensemble,
        transmittance,
        epsilon,
        z,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        numerical_tolerance=physicality_tolerance,
    )
    lambdas = (covariance.lambda1, covariance.lambda2, covariance.lambda3)
    adjusted_lambdas: list[torch.Tensor] = []
    for value in lambdas:
        if bool(torch.any(value < 1.0)):
            repairs.append("clamped symplectic eigenvalue within tolerance to one for entropy")
        adjusted_lambdas.append(torch.clamp_min(value, 1.0))
    l1, l2, l3 = adjusted_lambdas
    chi_be = (
        bosonic_entropy((l1 - 1.0) / 2.0)
        + bosonic_entropy((l2 - 1.0) / 2.0)
        - bosonic_entropy((l3 - 1.0) / 2.0)
    )
    if bool(torch.any(chi_be < -physicality_tolerance)):
        raise PhysicalityError("Holevo information is materially negative.")
    if not bool(torch.all(torch.isfinite(chi_be))):
        raise FloatingPointError("Holevo information returned NaN or Inf.")
    if bool(torch.any(chi_be < 0.0)):
        repairs.append("clamped tiny negative Holevo information to zero")
        chi_be = torch.clamp_min(chi_be, 0.0)
    return HolevoResult(
        chi_be=chi_be,
        tau=tau,
        tau_trace=tau_trace,
        w=w,
        coherent_correlation=coherent_correlation,
        z=z,
        covariance=covariance,
        diagnostics={
            "fock_cutoff": fock_cutoff,
            "maximum_density_trace_error": float(trace_error.detach().max()),
            "minimum_density_eigenvalue": float(eigenvalues.detach().min()),
            "suppressed_density_eigenvalues": int((~significant).sum().detach()),
            "numerical_repairs": tuple(repairs) + covariance.numerical_repairs,
            "standard_form_supported": covariance.symmetry.standard_form_supported,
            "standard_form_override": not require_supported_symmetry,
            "symmetry_tolerance": symmetry_tolerance,
            "density_trace_tolerance": density_trace_tolerance,
            "density_eigenvalue_pseudoinverse_tolerance": density_eigenvalue_tolerance,
            "physicality_tolerance": physicality_tolerance,
        },
    )
