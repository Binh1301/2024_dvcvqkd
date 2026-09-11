"""Differentiable paper Holevo chain, Eqs. (103)--(126), with strict diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Callable
from typing import Any, Literal

import torch

from src.modulation.joint_ps_gs import Ensemble
from .covariance import CovarianceResult, PhysicalityError, standard_form_covariance
from .gram_moments import c4_gram_source_moments
from .protocol import validate_channel_state


HolevoBackend = Literal["c4_gram", "fock_diagnostic"]

DEFAULT_Z_GRID_SIZE = 33
DEFAULT_Z_REFINEMENT_STEPS = 12


class SecurityDomainError(PhysicalityError):
    """Fail-closed security-domain error with inspectable diagnostics."""

    def __init__(self, message: str, *, diagnostics: dict[str, Any]) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


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


def _maximize_bounded_scalar(
    lower: torch.Tensor,
    upper: torch.Tensor,
    evaluator: Callable[[torch.Tensor], torch.Tensor],
    *,
    grid_size: int = DEFAULT_Z_GRID_SIZE,
    refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Deterministically maximize a batched scalar objective on closed intervals.

    A complete fixed grid is retained, and every grid cell receives a fixed
    number of golden-section refinement steps.  This does not assume endpoint
    monotonicity; ``torch.max`` over all retained candidates supplies the
    selected value and its local autograd/subgradient semantics.
    """

    if not isinstance(grid_size, int) or grid_size < 2:
        raise ValueError("grid_size must be an integer greater than or equal to two.")
    if not isinstance(refinement_steps, int) or refinement_steps < 0:
        raise ValueError("refinement_steps must be a nonnegative integer.")
    lower = lower.reshape(-1)
    upper = upper.reshape(-1)
    if lower.shape != upper.shape or lower.numel() == 0:
        raise ValueError("lower and upper must be nonempty, equally sized batches.")
    if not bool(torch.all(torch.isfinite(lower))) or not bool(torch.all(torch.isfinite(upper))):
        raise ValueError("Bounded maximization endpoints must be finite.")
    if bool(torch.any(lower > upper)):
        raise ValueError("Bounded maximization requires lower <= upper.")

    fractions = torch.linspace(
        0.0,
        1.0,
        grid_size,
        dtype=lower.dtype,
        device=lower.device,
    )
    width = upper - lower
    grid = lower.unsqueeze(-1) + width.unsqueeze(-1) * fractions

    def evaluate(points: torch.Tensor) -> torch.Tensor:
        scale = torch.maximum(
            torch.ones_like(lower),
            torch.maximum(torch.abs(lower), torch.abs(upper)),
        ).unsqueeze(-1)
        tolerance = 1.0e-12 * scale
        if not bool(torch.all(torch.isfinite(points))):
            raise FloatingPointError("Bounded scalar candidates must be finite.")
        if bool(torch.any(points < lower.unsqueeze(-1) - tolerance)) or bool(
            torch.any(points > upper.unsqueeze(-1) + tolerance)
        ):
            raise FloatingPointError(
                "Bounded scalar candidate escaped its declared closed interval."
            )
        values = evaluator(points)
        if values.shape != points.shape:
            raise ValueError(
                "The bounded scalar evaluator must preserve the candidate shape."
            )
        if not bool(torch.all(torch.isfinite(values))):
            raise FloatingPointError("Bounded scalar objective returned NaN or Inf.")
        return values

    candidate_points = [grid]
    candidate_values = [evaluate(grid)]
    golden_ratio = (math.sqrt(5.0) - 1.0) / 2.0
    left = grid[:, :-1]
    right = grid[:, 1:]
    x1 = right - golden_ratio * (right - left)
    x2 = left + golden_ratio * (right - left)
    f1 = evaluate(x1)
    f2 = evaluate(x2)
    candidate_points.extend((x1, x2))
    candidate_values.extend((f1, f2))
    for _ in range(refinement_steps):
        choose_left = f1 >= f2
        new_left = torch.where(choose_left, left, x1)
        new_right = torch.where(choose_left, x2, right)
        new_width = new_right - new_left
        calculated_x1 = new_right - golden_ratio * new_width
        calculated_x2 = new_left + golden_ratio * new_width
        new_candidate = torch.where(
            choose_left,
            calculated_x1,
            calculated_x2,
        )
        new_value = evaluate(new_candidate)
        new_x1 = torch.where(choose_left, calculated_x1, x2)
        new_x2 = torch.where(choose_left, x1, calculated_x2)
        new_f1 = torch.where(choose_left, new_value, f2)
        new_f2 = torch.where(choose_left, f1, new_value)
        candidate_points.append(new_candidate)
        candidate_values.append(new_value)
        left, right = new_left, new_right
        x1, x2 = new_x1, new_x2
        f1, f2 = new_f1, new_f2
    midpoint = 0.5 * (left + right)
    candidate_points.append(midpoint)
    candidate_values.append(evaluate(midpoint))

    points = torch.cat(candidate_points, dim=-1)
    values = torch.cat(candidate_values, dim=-1)
    maximum, index = torch.max(values, dim=-1)
    selected = torch.gather(points, dim=-1, index=index.unsqueeze(-1)).squeeze(-1)
    return maximum, selected


def _expand_ensemble_for_correlations(
    ensemble: Ensemble,
    candidate_count: int,
) -> Ensemble:
    probabilities = ensemble.probabilities
    amplitudes = ensemble.amplitudes
    declared_va = ensemble.declared_va.reshape(-1)
    batch_size, symbol_count = probabilities.shape
    return Ensemble(
        probabilities=probabilities.unsqueeze(1).expand(-1, candidate_count, -1).reshape(
            batch_size * candidate_count, symbol_count
        ),
        amplitudes=amplitudes.unsqueeze(1).expand(-1, candidate_count, -1).reshape(
            batch_size * candidate_count, symbol_count
        ),
        declared_va=declared_va.unsqueeze(1).expand(-1, candidate_count).reshape(-1),
        raw_constellation=ensemble.raw_constellation,
        exact_csi_oracle=ensemble.exact_csi_oracle,
        c4_symmetric=ensemble.c4_symmetric,
    )


def _evaluate_holevo_for_correlations(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    correlations: torch.Tensor,
    *,
    require_supported_symmetry: bool,
    symmetry_tolerance: float,
    physicality_tolerance: float,
    return_covariance: bool,
) -> tuple[torch.Tensor, CovarianceResult | None, tuple[str, ...]]:
    """Evaluate covariance entropy for one or many candidate correlations."""

    if correlations.ndim not in (1, 2):
        raise ValueError("correlations must have shape [B] or [B,K].")
    transmittance = transmittance.reshape(-1)
    epsilon = epsilon.reshape(-1)
    batch_size = transmittance.shape[0]
    if epsilon.shape != transmittance.shape or correlations.shape[0] != batch_size:
        raise ValueError("Correlation and channel batches must have equal length.")
    candidate_count = 1 if correlations.ndim == 1 else correlations.shape[1]
    if candidate_count <= 0:
        raise ValueError("correlations must contain at least one candidate per state.")
    flat_correlations = correlations.reshape(-1)
    expanded = _expand_ensemble_for_correlations(ensemble, candidate_count)
    expanded_transmittance = transmittance.unsqueeze(1).expand(-1, candidate_count).reshape(-1)
    expanded_epsilon = epsilon.unsqueeze(1).expand(-1, candidate_count).reshape(-1)
    covariance = standard_form_covariance(
        expanded,
        expanded_transmittance,
        expanded_epsilon,
        flat_correlations,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        numerical_tolerance=physicality_tolerance,
    )
    lambdas = (covariance.lambda1, covariance.lambda2, covariance.lambda3)
    minimum_lambda = torch.minimum(torch.minimum(lambdas[0], lambdas[1]), lambdas[2])
    if bool(torch.any(minimum_lambda < 1.0 - physicality_tolerance)):
        raise PhysicalityError(
            "A candidate correlation violates the uncertainty condition lambda>=1."
        )
    repairs = list(covariance.numerical_repairs)
    if any(bool(torch.any(value < 1.0)) for value in lambdas):
        repairs.append(
            "clamped symplectic eigenvalues within physicality tolerance to one for entropy"
        )
    entropy_lambdas = tuple(torch.clamp_min(value, 1.0) for value in lambdas)
    l1, l2, l3 = entropy_lambdas
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
    if correlations.ndim == 2:
        chi_be = chi_be.reshape(correlations.shape)
        selected_covariance = None
    else:
        selected_covariance = covariance
    return chi_be, selected_covariance if return_covariance else None, tuple(repairs)


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
    z_grid_size: int = DEFAULT_Z_GRID_SIZE,
    z_refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
) -> HolevoResult:
    """Apply the frozen security chain to backend-independent source moments."""

    if bool(torch.any(w_raw < -physicality_tolerance)):
        raise PhysicalityError("Non-Gaussian penalty w is materially negative.")
    repairs: list[str] = []
    if bool(torch.any(w_raw < 0.0)):
        repairs.append("clamped tiny negative w to zero")
    w = torch.clamp_min(w_raw, 0.0)
    transmittance = transmittance.reshape(-1)
    epsilon = epsilon.reshape(-1)
    coherent_correlation = coherent_correlation.reshape(-1)
    w = w.reshape(-1)
    if not (
        transmittance.shape
        == epsilon.shape
        == coherent_correlation.shape
        == w.shape
        == ensemble.declared_va.reshape(-1).shape
    ):
        raise ValueError("Holevo source moments and channel batches must have equal length.")
    va = ensemble.computed_va()
    a = va + 1.0
    b = 1.0 + transmittance * va + transmittance * epsilon
    physical_radicand = a * b - 1.0 - torch.abs(a - b)
    if bool(torch.any(physical_radicand < -physicality_tolerance)):
        raise SecurityDomainError(
            "Analytic physicality bound has a materially negative radicand.",
            diagnostics={
                **diagnostics,
                "failure_reason": "NEGATIVE_Z_PHYS_RADICAND",
                "security_domain_valid": torch.zeros_like(physical_radicand, dtype=torch.bool),
                "physicality_radicand": physical_radicand,
            },
        )
    if bool(torch.any(physical_radicand < 0.0)):
        repairs.append("clamped tiny negative Z_phys radicand to zero")
    z_phys = torch.sqrt(torch.clamp_min(physical_radicand, 0.0))
    radicand = 2.0 * transmittance * epsilon * w
    z_minus = 2.0 * torch.sqrt(transmittance) * coherent_correlation - torch.sqrt(radicand)
    z_plus = 2.0 * torch.sqrt(transmittance) * coherent_correlation + torch.sqrt(radicand)
    z_lower = torch.maximum(z_minus, -z_phys)
    z_upper = torch.minimum(z_plus, z_phys)
    security_domain_valid = z_lower <= z_upper
    interval_diagnostics = {
        **diagnostics,
        "Z_minus": z_minus,
        "Z_plus": z_plus,
        "Z_phys": z_phys,
        "Z_L": z_lower,
        "Z_U": z_upper,
        "z_minus": z_minus,
        "z_plus": z_plus,
        "z_phys": z_phys,
        "z_lower": z_lower,
        "z_upper": z_upper,
        "interval_width": z_upper - z_lower,
        "security_domain_valid": security_domain_valid,
    }
    if bool(torch.any(~security_domain_valid)):
        raise SecurityDomainError(
            "The physically admissible Z interval is empty.",
            diagnostics={
                **interval_diagnostics,
                "failure_reason": "EMPTY_Z_INTERVAL",
                "Z_star": None,
                "z_star": None,
                "chi_BE_ub": None,
            },
        )

    candidate_repairs: set[str] = set()

    def evaluate_candidates(candidate_z: torch.Tensor) -> torch.Tensor:
        try:
            values, _, candidate_numerical_repairs = _evaluate_holevo_for_correlations(
                ensemble,
                transmittance,
                epsilon,
                candidate_z,
                require_supported_symmetry=require_supported_symmetry,
                symmetry_tolerance=symmetry_tolerance,
                physicality_tolerance=physicality_tolerance,
                return_covariance=False,
            )
        except PhysicalityError as error:
            raise SecurityDomainError(
                "A candidate in the analytic Z interval failed covariance physicality.",
                diagnostics={
                    **interval_diagnostics,
                    "failure_reason": "CANDIDATE_PHYSICALITY_FAILURE",
                    "candidate_Z": candidate_z.detach(),
                },
            ) from error
        candidate_repairs.update(candidate_numerical_repairs)
        return values

    chi_be, z_star = _maximize_bounded_scalar(
        z_lower,
        z_upper,
        evaluate_candidates,
        grid_size=z_grid_size,
        refinement_steps=z_refinement_steps,
    )
    try:
        selected_chi, covariance, selected_repairs = _evaluate_holevo_for_correlations(
            ensemble,
            transmittance,
            epsilon,
            z_star,
            require_supported_symmetry=require_supported_symmetry,
            symmetry_tolerance=symmetry_tolerance,
            physicality_tolerance=physicality_tolerance,
            return_covariance=True,
        )
    except PhysicalityError as error:
        raise SecurityDomainError(
            "The selected worst-case correlation failed covariance physicality.",
            diagnostics={
                **interval_diagnostics,
                "failure_reason": "SELECTED_CANDIDATE_PHYSICALITY_FAILURE",
                "candidate_Z": z_star.detach(),
            },
        ) from error
    if covariance is None:
        raise RuntimeError("Selected Holevo covariance was not returned.")
    if not bool(torch.allclose(selected_chi, chi_be, atol=1e-12, rtol=1e-10)):
        raise FloatingPointError("Selected Holevo candidate was not reproduced consistently.")
    scale = torch.maximum(
        torch.ones_like(z_star),
        torch.maximum(torch.abs(z_lower), torch.abs(z_upper)),
    )
    location_tolerance = torch.maximum(
        torch.full_like(scale, physicality_tolerance), 1e-12 * scale
    )
    maximizing_location: list[str] = []
    for index in range(z_star.shape[0]):
        tolerance = float(location_tolerance[index].detach())
        if abs(float((z_star[index] - z_lower[index]).detach())) <= tolerance:
            maximizing_location.append("lower_boundary")
        elif abs(float((z_star[index] - z_upper[index]).detach())) <= tolerance:
            maximizing_location.append("upper_boundary")
        else:
            maximizing_location.append("interior")
    return HolevoResult(
        chi_be=chi_be,
        tau=tau,
        tau_trace=tau_trace,
        w=w,
        coherent_correlation=coherent_correlation,
        z=z_star,
        covariance=covariance,
        diagnostics={
            **interval_diagnostics,
            "Z_star": z_star,
            "chi_BE_ub": chi_be,
            "z_star": z_star,
            "maximizing_location": tuple(maximizing_location),
            "numerical_repairs": tuple(repairs)
            + tuple(sorted(candidate_repairs))
            + tuple(selected_repairs),
            "standard_form_supported": covariance.symmetry.standard_form_supported,
            "standard_form_override": not require_supported_symmetry,
            "symmetry_tolerance": symmetry_tolerance,
            "physicality_tolerance": physicality_tolerance,
            "z_grid_size": z_grid_size,
            "z_refinement_steps": z_refinement_steps,
            "maximization_method": "fixed_grid_all_cells_golden_section",
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
    z_grid_size: int = DEFAULT_Z_GRID_SIZE,
    z_refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
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
        z_grid_size=z_grid_size,
        z_refinement_steps=z_refinement_steps,
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
    z_grid_size: int = DEFAULT_Z_GRID_SIZE,
    z_refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
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
        z_grid_size=z_grid_size,
        z_refinement_steps=z_refinement_steps,
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
    z_grid_size: int = DEFAULT_Z_GRID_SIZE,
    z_refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
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
            z_grid_size=z_grid_size,
            z_refinement_steps=z_refinement_steps,
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
            z_grid_size=z_grid_size,
            z_refinement_steps=z_refinement_steps,
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
    z_grid_size: int = DEFAULT_Z_GRID_SIZE,
    z_refinement_steps: int = DEFAULT_Z_REFINEMENT_STEPS,
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
        z_grid_size=z_grid_size,
        z_refinement_steps=z_refinement_steps,
    ).chi_be
