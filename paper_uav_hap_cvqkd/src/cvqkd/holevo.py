"""Differentiable paper Holevo chain, Eqs. (103)--(126), with strict diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal

import torch

from src.modulation.joint_ps_gs import Ensemble
from .covariance import (
    CovarianceResult,
    PhysicalityError,
    physical_correlation_bound,
    standard_form_covariance,
)
from .gram_moments import c4_gram_source_moments
from .protocol import validate_channel_state


HolevoBackend = Literal["c4_gram", "fock_diagnostic"]

INTERVAL_GRID_SIZE = 65
INTERVAL_REFINEMENT_ITERATIONS = 32


class SecurityDomainError(PhysicalityError):
    """A manuscript correlation interval has no physical covariance point."""

    def __init__(
        self,
        message: str,
        *,
        batch_indices: tuple[int, ...],
        z_minus: torch.Tensor,
        z_plus: torch.Tensor,
        z_phys: torch.Tensor,
        z_lower: torch.Tensor,
        z_upper: torch.Tensor,
    ) -> None:
        super().__init__(message)
        self.batch_indices = batch_indices
        self.interval_diagnostics = {
            "z_minus": z_minus,
            "z_plus": z_plus,
            "z_phys": z_phys,
            "z_lower": z_lower,
            "z_upper": z_upper,
        }


@dataclass(frozen=True)
class HolevoResult:
    chi_be: torch.Tensor
    tau: torch.Tensor | None
    tau_trace: torch.Tensor
    w: torch.Tensor
    coherent_correlation: torch.Tensor
    # ``z`` remains a compatibility alias for the selected worst-case point.
    z: torch.Tensor
    z_minus: torch.Tensor
    z_plus: torch.Tensor
    z_phys: torch.Tensor
    z_lower: torch.Tensor
    z_upper: torch.Tensor
    z_star: torch.Tensor
    chi_at_z_lower: torch.Tensor
    chi_at_z_upper: torch.Tensor
    maximizer_location: tuple[str, ...]
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
    interval_grid_size: int,
    interval_refinement_iterations: int,
    diagnostics: dict[str, Any],
) -> HolevoResult:
    """Apply the manuscript's full-interval security chain to source moments."""

    if not isinstance(interval_grid_size, int) or interval_grid_size < 3:
        raise ValueError("interval_grid_size must be an integer of at least three.")
    if not isinstance(interval_refinement_iterations, int) or interval_refinement_iterations < 0:
        raise ValueError("interval_refinement_iterations must be a nonnegative integer.")
    if bool(torch.any(w_raw < 0.0)):
        raise PhysicalityError("Non-Gaussian penalty w is negative; no zero-clamp is permitted.")
    w = w_raw
    correlation_radicand = 2.0 * transmittance * epsilon * w
    if bool(torch.any(correlation_radicand < 0.0)):
        raise PhysicalityError("Correlation-interval radicand is negative.")
    correlation_radius = torch.sqrt(correlation_radicand)
    z_minus = 2.0 * torch.sqrt(transmittance) * coherent_correlation - correlation_radius
    z_plus = 2.0 * torch.sqrt(transmittance) * coherent_correlation + correlation_radius

    va = ensemble.computed_va()
    a = 1.0 + va
    b = 1.0 + transmittance * va + transmittance * epsilon
    bound = physical_correlation_bound(
        a,
        b,
        numerical_tolerance=physicality_tolerance,
    )
    z_phys = bound.z_phys
    z_lower = torch.maximum(z_minus, -z_phys)
    z_upper = torch.minimum(z_plus, z_phys)
    invalid_interval = z_lower > z_upper
    if bool(torch.any(invalid_interval)):
        indices = tuple(
            int(index.detach())
            for index in torch.nonzero(invalid_interval, as_tuple=False).reshape(-1)
        )
        raise SecurityDomainError(
            "SECURITY_DOMAIN_FAILURE: [Z_minus,Z_plus] has empty intersection "
            "with [-Z_phys,Z_phys].",
            batch_indices=indices,
            z_minus=z_minus,
            z_plus=z_plus,
            z_phys=z_phys,
            z_lower=z_lower,
            z_upper=z_upper,
        )

    chi_be, z_star, chi_at_z_lower, chi_at_z_upper, maximizer_location, covariance = (
        _maximize_holevo_over_interval(
            ensemble,
            transmittance,
            epsilon,
            z_lower,
            z_upper,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            physicality_tolerance=physicality_tolerance,
            grid_size=interval_grid_size,
            refinement_iterations=interval_refinement_iterations,
        )
    )
    if bool(torch.any(chi_be < 0.0)):
        raise PhysicalityError("Holevo information is negative; no zero-clamp is permitted.")
    if not bool(torch.all(torch.isfinite(chi_be))):
        raise FloatingPointError("Holevo information returned NaN or Inf.")
    return HolevoResult(
        chi_be=chi_be,
        tau=tau,
        tau_trace=tau_trace,
        w=w,
        coherent_correlation=coherent_correlation,
        z=z_star,
        z_minus=z_minus,
        z_plus=z_plus,
        z_phys=z_phys,
        z_lower=z_lower,
        z_upper=z_upper,
        z_star=z_star,
        chi_at_z_lower=chi_at_z_lower,
        chi_at_z_upper=chi_at_z_upper,
        maximizer_location=maximizer_location,
        covariance=covariance,
        diagnostics={
            **diagnostics,
            "numerical_repairs": covariance.numerical_repairs,
            "roundoff_events": {
                "z_phys": bound.roundoff_events,
                "selected_covariance": covariance.roundoff_events,
            },
            "security_interval": {
                "z_minus": z_minus.detach().tolist(),
                "z_plus": z_plus.detach().tolist(),
                "z_phys": z_phys.detach().tolist(),
                "z_lower": z_lower.detach().tolist(),
                "z_upper": z_upper.detach().tolist(),
                "z_star": z_star.detach().tolist(),
                "chi_at_z_lower": chi_at_z_lower.detach().tolist(),
                "chi_at_z_upper": chi_at_z_upper.detach().tolist(),
                "chi_star": chi_be.detach().tolist(),
                "maximizer_location": maximizer_location,
            },
            "interval_maximizer": {
                "algorithm": "coarse_grid_plus_local_golden_refinement_piecewise_autodiff",
                "grid_size": interval_grid_size,
                "refinement_iterations": interval_refinement_iterations,
                "global_optimality_certificate": False,
            },
            "standard_form_supported": covariance.symmetry.standard_form_supported,
            "standard_form_override": not require_supported_symmetry,
            "symmetry_tolerance": symmetry_tolerance,
            "physicality_tolerance": physicality_tolerance,
        },
    )


def _chi_at_correlation(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    correlation: torch.Tensor,
    *,
    require_supported_symmetry: bool,
    symmetry_tolerance: float,
    physicality_tolerance: float,
) -> tuple[torch.Tensor, CovarianceResult]:
    """Evaluate the manuscript Holevo expression at one batch of correlations."""

    covariance = standard_form_covariance(
        ensemble,
        transmittance,
        epsilon,
        correlation,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        numerical_tolerance=physicality_tolerance,
    )
    chi = (
        bosonic_entropy((covariance.lambda1 - 1.0) / 2.0)
        + bosonic_entropy((covariance.lambda2 - 1.0) / 2.0)
        - bosonic_entropy((covariance.lambda3 - 1.0) / 2.0)
    )
    if not bool(torch.all(torch.isfinite(chi))):
        raise FloatingPointError("Holevo information returned NaN or Inf.")
    return chi, covariance


def _maximize_holevo_over_interval(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    z_lower: torch.Tensor,
    z_upper: torch.Tensor,
    *,
    require_supported_symmetry: bool,
    symmetry_tolerance: float,
    physicality_tolerance: float,
    grid_size: int,
    refinement_iterations: int,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    tuple[str, ...],
    CovarianceResult,
]:
    """Maximize the actual scalar Holevo function on each physical interval.

    The solver explicitly includes both endpoints, selects the best point on a
    deterministic full interval grid, then performs a bounded golden-section
    refinement in that grid cell.  ``argmax`` and branch choices make the
    resulting value function piecewise differentiable; within a fixed active
    candidate, the selected value retains the ordinary torch gradient.
    """

    if z_lower.shape != z_upper.shape:
        raise ValueError("Correlation interval endpoints must have identical shapes.")
    fractions = torch.linspace(
        0.0,
        1.0,
        grid_size,
        dtype=z_lower.dtype,
        device=z_lower.device,
    )
    grid_z = z_lower.unsqueeze(-1) + (z_upper - z_lower).unsqueeze(-1) * fractions
    grid_chi = torch.stack(
        [
            _chi_at_correlation(
                ensemble,
                transmittance,
                epsilon,
                grid_z[:, column],
                require_supported_symmetry=require_supported_symmetry,
                symmetry_tolerance=symmetry_tolerance,
                physicality_tolerance=physicality_tolerance,
            )[0]
            for column in range(grid_size)
        ],
        dim=-1,
    )
    chi_at_z_lower = grid_chi[:, 0]
    chi_at_z_upper = grid_chi[:, -1]
    coarse_index = torch.argmax(grid_chi, dim=-1)
    coarse_z = torch.gather(grid_z, 1, coarse_index.unsqueeze(-1)).squeeze(-1)
    coarse_chi = torch.gather(grid_chi, 1, coarse_index.unsqueeze(-1)).squeeze(-1)

    left_index = torch.clamp(coarse_index - 1, min=0)
    right_index = torch.clamp(coarse_index + 1, max=grid_size - 1)
    left = torch.gather(grid_z, 1, left_index.unsqueeze(-1)).squeeze(-1)
    right = torch.gather(grid_z, 1, right_index.unsqueeze(-1)).squeeze(-1)
    golden_fraction = (math.sqrt(5.0) - 1.0) / 2.0
    for _ in range(refinement_iterations):
        left_probe = right - golden_fraction * (right - left)
        right_probe = left + golden_fraction * (right - left)
        left_value = _chi_at_correlation(
            ensemble,
            transmittance,
            epsilon,
            left_probe,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            physicality_tolerance=physicality_tolerance,
        )[0]
        right_value = _chi_at_correlation(
            ensemble,
            transmittance,
            epsilon,
            right_probe,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            physicality_tolerance=physicality_tolerance,
        )[0]
        move_left = left_value < right_value
        left = torch.where(move_left, left_probe, left)
        right = torch.where(move_left, right, right_probe)
    refined_z = 0.5 * (left + right)
    refined_chi, _ = _chi_at_correlation(
        ensemble,
        transmittance,
        epsilon,
        refined_z,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        physicality_tolerance=physicality_tolerance,
    )

    candidate_z = torch.stack((z_lower, z_upper, coarse_z, refined_z), dim=-1)
    candidate_chi = torch.stack(
        (chi_at_z_lower, chi_at_z_upper, coarse_chi, refined_chi), dim=-1
    )
    selected_index = torch.argmax(candidate_chi, dim=-1)
    z_star = torch.gather(candidate_z, 1, selected_index.unsqueeze(-1)).squeeze(-1)
    chi_star = torch.gather(candidate_chi, 1, selected_index.unsqueeze(-1)).squeeze(-1)
    selected_chi, selected_covariance = _chi_at_correlation(
        ensemble,
        transmittance,
        epsilon,
        z_star,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        physicality_tolerance=physicality_tolerance,
    )
    if not bool(torch.allclose(chi_star, selected_chi, rtol=1e-12, atol=1e-12)):
        raise FloatingPointError("Interval maximizer candidate and selected evaluation disagree.")
    locations: list[str] = []
    for row in range(z_star.numel()):
        if bool(torch.isclose(z_lower[row], z_upper[row], rtol=0.0, atol=0.0)):
            locations.append("degenerate_interval")
        elif bool(torch.isclose(z_star[row], z_lower[row], rtol=0.0, atol=0.0)):
            locations.append("z_lower")
        elif bool(torch.isclose(z_star[row], z_upper[row], rtol=0.0, atol=0.0)):
            locations.append("z_upper")
        else:
            locations.append("interior")
    return (
        selected_chi,
        z_star,
        chi_at_z_lower,
        chi_at_z_upper,
        tuple(locations),
        selected_covariance,
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
    interval_grid_size: int = INTERVAL_GRID_SIZE,
    interval_refinement_iterations: int = INTERVAL_REFINEMENT_ITERATIONS,
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
        interval_grid_size=interval_grid_size,
        interval_refinement_iterations=interval_refinement_iterations,
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
    interval_grid_size: int = INTERVAL_GRID_SIZE,
    interval_refinement_iterations: int = INTERVAL_REFINEMENT_ITERATIONS,
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
        interval_grid_size=interval_grid_size,
        interval_refinement_iterations=interval_refinement_iterations,
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
    interval_grid_size: int = INTERVAL_GRID_SIZE,
    interval_refinement_iterations: int = INTERVAL_REFINEMENT_ITERATIONS,
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
            interval_grid_size=interval_grid_size,
            interval_refinement_iterations=interval_refinement_iterations,
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
            interval_grid_size=interval_grid_size,
            interval_refinement_iterations=interval_refinement_iterations,
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
    interval_grid_size: int = INTERVAL_GRID_SIZE,
    interval_refinement_iterations: int = INTERVAL_REFINEMENT_ITERATIONS,
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
        interval_grid_size=interval_grid_size,
        interval_refinement_iterations=interval_refinement_iterations,
    ).chi_be
