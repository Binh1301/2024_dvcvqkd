"""Differentiable paper Holevo chain, Eqs. (103)--(126), with strict diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal

import torch

from src.modulation.joint_ps_gs import Ensemble
from .covariance import CovarianceResult, PhysicalityError, standard_form_covariance
from .gram_moments import c4_gram_source_moments
from .protocol import validate_channel_state


HolevoBackend = Literal["c4_gram", "fock_diagnostic"]


@dataclass(frozen=True)
class HolevoResult:
    chi_be: torch.Tensor
    tau: torch.Tensor | None
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


def support_restricted_source_moments(
    tau: torch.Tensor,
    fock: torch.Tensor,
    probabilities: torch.Tensor,
    *,
    density_eigenvalue_tolerance: float,
    eigenvalues: torch.Tensor | None = None,
    eigenvectors: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor, tuple[dict[str, float | int], ...]]:
    """Evaluate ``C`` and ``w`` in the retained Hermitian spectral support.

    This is algebraically identical to constructing ``sqrt(tau)`` and its
    thresholded Moore--Penrose inverse in the full Fock basis.  It avoids that
    full-matrix reconstruction and evaluates ``t1-|inner|^2`` through an exact
    residual identity, reducing cancellation when those terms are close.
    """

    if tau.ndim != 3 or tau.shape[-1] != tau.shape[-2]:
        raise ValueError("tau must be a batch of square matrices.")
    if fock.ndim != 3 or fock.shape[0] != tau.shape[0] or fock.shape[-1] != tau.shape[-1]:
        raise ValueError("fock must match tau batch and cutoff dimensions.")
    if probabilities.shape != fock.shape[:-1]:
        raise ValueError("probabilities must match the Fock symbol batch.")
    if not math.isfinite(density_eigenvalue_tolerance) or density_eigenvalue_tolerance <= 0.0:
        raise ValueError("density_eigenvalue_tolerance must be finite and positive.")
    if (eigenvalues is None) != (eigenvectors is None):
        raise ValueError("eigenvalues and eigenvectors must be supplied together.")
    if eigenvalues is None:
        eigenvalues, eigenvectors = torch.linalg.eigh(tau)
    elif eigenvalues.shape != tau.shape[:-1] or eigenvectors.shape != tau.shape:
        raise ValueError("Supplied eigendecomposition does not match tau.")
    if bool(torch.any(eigenvalues < -density_eigenvalue_tolerance)):
        raise PhysicalityError("Density operator has a materially negative eigenvalue.")
    significant = eigenvalues > density_eigenvalue_tolerance
    a = annihilation_operator(tau.shape[-1], tau.device)
    correlations: list[torch.Tensor] = []
    penalties: list[torch.Tensor] = []
    diagnostics: list[dict[str, float | int]] = []
    for batch_index in range(tau.shape[0]):
        retained = significant[batch_index]
        if not bool(torch.any(retained)):
            raise PhysicalityError("Density spectral support is empty.")
        values = eigenvalues[batch_index, retained]
        vectors = eigenvectors[batch_index, :, retained]
        support_a = vectors.mH @ a @ vectors
        square_root = torch.sqrt(values)
        inverse_square_root = torch.rsqrt(values)
        correlations.append(torch.sum(
            square_root[:, None]
            * square_root[None, :]
            * support_a.abs().square()
        ).real)
        a_tau_support = (
            square_root[:, None] * support_a * inverse_square_root[None, :]
        )
        coefficients = fock[batch_index] @ vectors.conj()
        transformed_fock = (coefficients @ a_tau_support.T) @ vectors.T
        inner = torch.sum(fock[batch_index].conj() * transformed_fock, dim=-1)
        norm = torch.sum(fock[batch_index].abs().square(), dim=-1).real
        if bool(torch.any(norm <= 0.0)):
            raise PhysicalityError("A truncated coherent vector has nonpositive norm.")
        residual = transformed_fock - fock[batch_index] * (inner / norm).unsqueeze(-1)
        difference = (
            torch.sum(residual.abs().square(), dim=-1).real
            + inner.abs().square() * (torch.reciprocal(norm) - 1.0)
        )
        penalties.append(torch.sum(probabilities[batch_index] * difference).real)
        minimum = values.min()
        maximum = values.max()
        diagnostics.append({
            "minimum_density_eigenvalue": float(eigenvalues[batch_index].detach().min()),
            "maximum_density_eigenvalue": float(eigenvalues[batch_index].detach().max()),
            "support_size": int(retained.detach().sum()),
            "effective_numerical_rank": int(retained.detach().sum()),
            "pseudoinverse_support_size": int(retained.detach().sum()),
            "suppressed_density_eigenvalues": int((~retained).detach().sum()),
            "minimum_retained_density_eigenvalue": float(minimum.detach()),
            "maximum_retained_density_eigenvalue": float(maximum.detach()),
            "retained_density_condition_number": float((maximum / minimum).detach()),
        })
    return torch.stack(correlations), torch.stack(penalties), tuple(diagnostics)


def bosonic_entropy(x: torch.Tensor) -> torch.Tensor:
    if bool(torch.any(x < 0.0)):
        raise PhysicalityError("Bosonic entropy received a negative occupation number.")
    positive = x > 0.0
    safe = torch.where(positive, x, torch.ones_like(x))
    value = (x + 1.0) * torch.log2(x + 1.0) - torch.where(
        positive, x * torch.log2(safe), torch.zeros_like(x)
    )
    return value


def _holevo_from_source_moments(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    coherent_correlation: torch.Tensor,
    w_raw: torch.Tensor,
    tau: torch.Tensor | None,
    tau_trace: torch.Tensor,
    require_supported_symmetry: bool,
    symmetry_tolerance: float,
    physicality_tolerance: float,
    diagnostics: dict[str, Any],
) -> HolevoResult:
    """Apply the frozen security chain to backend-independent source moments."""

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
    adjusted_lambdas: list[torch.Tensor] = []
    for value in (covariance.lambda1, covariance.lambda2, covariance.lambda3):
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
            **diagnostics,
            "numerical_repairs": tuple(repairs) + covariance.numerical_repairs,
            "standard_form_supported": covariance.symmetry.standard_form_supported,
            "standard_form_override": not require_supported_symmetry,
            "symmetry_tolerance": symmetry_tolerance,
            "physicality_tolerance": physicality_tolerance,
        },
    )


def dense_fock_holevo_information(
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
    """Historical dense-Fock backend retained only for explicit diagnostics."""
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
    return _holevo_from_source_moments(
        ensemble,
        transmittance,
        epsilon,
        coherent_correlation=coherent_correlation,
        w_raw=w_raw,
        tau=tau,
        tau_trace=tau_trace,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        physicality_tolerance=physicality_tolerance,
        diagnostics={
            "backend": "fock_diagnostic",
            "fock_cutoff": fock_cutoff,
            "maximum_density_trace_error": float(trace_error.detach().max()),
            "minimum_density_eigenvalue": float(eigenvalues.detach().min()),
            "suppressed_density_eigenvalues": int((~significant).sum().detach()),
            "density_trace_tolerance": density_trace_tolerance,
            "density_eigenvalue_pseudoinverse_tolerance": density_eigenvalue_tolerance,
        },
    )


def c4_gram_holevo_information(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    density_eigenvalue_tolerance: float,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-10,
    physicality_tolerance: float = 1e-10,
) -> HolevoResult:
    """Cutoff-independent production Holevo evaluation for C4 ensembles."""

    for name, value in (
        ("symmetry_tolerance", symmetry_tolerance),
        ("density_trace_tolerance", density_trace_tolerance),
        ("density_eigenvalue_tolerance", density_eigenvalue_tolerance),
        ("physicality_tolerance", physicality_tolerance),
    ):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive.")
    if not require_supported_symmetry:
        raise ValueError("The C4 Gram production backend requires supported symmetry.")
    ensemble.validate()
    transmittance, epsilon = validate_channel_state(transmittance, epsilon)
    transmittance = transmittance.to(ensemble.probabilities.device)
    epsilon = epsilon.to(ensemble.probabilities.device)
    moments = c4_gram_source_moments(
        ensemble,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
        physicality_tolerance=physicality_tolerance,
    )
    support_sizes = [row["support_size"] for row in moments.diagnostics]
    suppressed = sum(256 - int(value) for value in support_sizes)
    analytic_trace = ensemble.probabilities.sum(dim=-1)
    trace_error = torch.abs(analytic_trace - 1.0)
    if bool(torch.any(trace_error > density_trace_tolerance)):
        raise PhysicalityError("Weighted Gram trace is outside the declared tolerance.")
    return _holevo_from_source_moments(
        ensemble,
        transmittance,
        epsilon,
        coherent_correlation=moments.coherent_correlation,
        w_raw=moments.w,
        tau=None,
        tau_trace=analytic_trace,
        require_supported_symmetry=True,
        symmetry_tolerance=symmetry_tolerance,
        physicality_tolerance=physicality_tolerance,
        diagnostics={
            "backend": "c4_gram",
            "fock_cutoff": None,
            "source_operator_representation": "weighted_coherent_state_gram",
            "density_trace_source": "analytic_probability_normalization",
            "maximum_density_trace_error": float(trace_error.detach().max()),
            "minimum_density_eigenvalue": min(
                float(row["minimum_eigenvalue"]) for row in moments.diagnostics
            ),
            "suppressed_density_eigenvalues": suppressed,
            "density_eigenvalue_pseudoinverse_tolerance": density_eigenvalue_tolerance,
            "density_trace_tolerance": density_trace_tolerance,
            "source_moment_diagnostics": moments.diagnostics,
        },
    )


def holevo_information(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    backend: HolevoBackend,
    density_eigenvalue_tolerance: float,
    fock_cutoff: int | None = None,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-8,
    physicality_tolerance: float = 1e-10,
) -> HolevoResult:
    """Public Holevo interface with cutoff-independent C4 Gram production default."""

    if backend == "c4_gram":
        if fock_cutoff is not None:
            raise ValueError("The c4_gram backend rejects fock_cutoff; it is cutoff-independent.")
        return c4_gram_holevo_information(
            ensemble,
            transmittance,
            epsilon,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            density_trace_tolerance=density_trace_tolerance,
            density_eigenvalue_tolerance=density_eigenvalue_tolerance,
            physicality_tolerance=physicality_tolerance,
        )
    if backend == "fock_diagnostic":
        if fock_cutoff is None:
            raise ValueError("The fock_diagnostic backend requires an explicit fock_cutoff.")
        return dense_fock_holevo_information(
            ensemble,
            transmittance,
            epsilon,
            fock_cutoff=fock_cutoff,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            density_trace_tolerance=density_trace_tolerance,
            density_eigenvalue_tolerance=density_eigenvalue_tolerance,
            physicality_tolerance=physicality_tolerance,
        )
    raise ValueError(f"Unsupported Holevo backend: {backend!r}.")


def shared_fixed_ensemble_holevo_chi(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    backend: HolevoBackend,
    density_eigenvalue_tolerance: float,
    fock_cutoff: int | None = None,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-8,
    physicality_tolerance: float = 1e-10,
) -> torch.Tensor:
    """Compute fixed-baseline chi with tau/C/w evaluated exactly once.

    This path is valid only when every batch row is the same source ensemble.
    Channel-dependent Z, covariance matrices, symplectic eigenvalues, and chi
    remain evaluated for every state. No security formula is changed.
    """

    ensemble.validate()
    if not all(torch.equal(value, value[:1].expand_as(value)) for value in (
        ensemble.probabilities, ensemble.amplitudes, ensemble.declared_va,
    )):
        raise ValueError("Shared-source Holevo requires one identical fixed ensemble per state.")
    transmittance, epsilon = validate_channel_state(transmittance, epsilon)
    if transmittance.shape[0] != ensemble.probabilities.shape[0]:
        raise ValueError("Channel-state count must match ensemble batch size.")
    # The production Gram path is evaluated on the complete batch. A previous
    # one-row source cache introduced small eigensolver-path differences, so it
    # remains disabled until an exact equivalence proof is available.
    return holevo_information(
        ensemble,
        transmittance,
        epsilon,
        backend=backend,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
        fock_cutoff=fock_cutoff,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        density_trace_tolerance=density_trace_tolerance,
        physicality_tolerance=physicality_tolerance,
    ).chi_be
