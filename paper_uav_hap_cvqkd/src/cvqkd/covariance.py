"""Paper standard-form covariance, Eqs. (111)--(122), with explicit guards."""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch

from src.modulation.joint_ps_gs import Ensemble


SYMMETRY_SCALE_FLOOR = 1e-15


class PhysicalityError(ValueError):
    """Raised when paper covariance assumptions or physicality checks fail."""


@dataclass(frozen=True)
class CorrelationPhysicalityBound:
    """Physical correlation magnitude and any explicit round-off guard data."""

    z_phys: torch.Tensor
    radicand: torch.Tensor
    roundoff_events: tuple[dict[str, float | int | str], ...]


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
    a: torch.Tensor
    b: torch.Tensor
    correlation: torch.Tensor
    lambda1: torch.Tensor
    lambda2: torch.Tensor
    lambda3: torch.Tensor
    symmetry: SymmetryDiagnostics
    numerical_repairs: tuple[str, ...]
    roundoff_events: tuple[dict[str, float | int | str], ...]


def _roundoff_events(
    quantity: str,
    values: torch.Tensor,
) -> tuple[dict[str, float | int | str], ...]:
    """Serialize only explicitly tolerated negative round-off residuals."""

    indices = torch.nonzero(values < 0.0, as_tuple=False).reshape(-1)
    return tuple(
        {
            "quantity": quantity,
            "batch_index": int(index.detach()),
            "value": float(values[index].detach()),
            "treatment": "set_to_exact_zero_after_tolerance_check",
        }
        for index in indices
    )


def physical_correlation_bound(
    a: torch.Tensor,
    b: torch.Tensor,
    *,
    numerical_tolerance: float,
) -> CorrelationPhysicalityBound:
    """Compute ``sqrt(a*b - 1 - abs(a-b))`` with an auditable guard.

    A material negative radicand is a scientific physicality failure.  A
    residual in ``[-numerical_tolerance, 0)`` can arise from binary64
    cancellation at the exact boundary; it is set to its known analytic value
    zero and returned as structured diagnostic data rather than silently
    repaired.
    """

    if a.shape != b.shape:
        raise ValueError("a and b must have identical shapes.")
    if not math.isfinite(numerical_tolerance) or numerical_tolerance <= 0.0:
        raise ValueError("numerical_tolerance must be finite and positive.")
    radicand = a * b - 1.0 - torch.abs(a - b)
    if bool(torch.any(radicand < -numerical_tolerance)):
        raise PhysicalityError("Physical correlation-bound radicand is materially negative.")
    events = _roundoff_events("z_phys_radicand", radicand)
    guarded = torch.where(radicand < 0.0, torch.zeros_like(radicand), radicand)
    return CorrelationPhysicalityBound(
        z_phys=torch.sqrt(guarded),
        radicand=radicand,
        roundoff_events=events,
    )


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
    # Algebraically this is ``delta**2 - 4*determinant``.  The factored form
    # avoids avoidable cancellation near an admissible correlation boundary.
    discriminant_raw = (a - b).square() * ((a + b).square() - 4.0 * c.square())
    if bool(torch.any(discriminant_raw < -numerical_tolerance)):
        raise PhysicalityError("Symplectic discriminant is materially negative.")
    repairs: list[str] = []
    roundoff_events = list(_roundoff_events("symplectic_discriminant", discriminant_raw))
    if roundoff_events:
        repairs.append("explicitly guarded tiny negative symplectic discriminant")
    discriminant = torch.where(
        discriminant_raw < 0.0,
        torch.zeros_like(discriminant_raw),
        discriminant_raw,
    )
    root = torch.sqrt(discriminant)
    lambda1_squared = 0.5 * (delta + root)
    if bool(torch.any(lambda1_squared < -numerical_tolerance)):
        raise PhysicalityError("Negative squared symplectic eigenvalue.")
    # The subtraction form ``0.5 * (delta - root)`` loses the smaller root
    # at physical-boundary endpoints.  Use the exact product of quadratic
    # roots, lambda1_squared*lambda2_squared=determinant, instead.  This is a
    # change of evaluation algebra, not a clip of a subunit eigenvalue.
    denominator = delta + root
    if bool(torch.any(denominator <= 0.0)):
        raise PhysicalityError(
            "Symplectic smaller-root denominator is nonpositive."
        )
    lambda2_squared = 2.0 * determinant / denominator
    if bool(torch.any(lambda2_squared < -numerical_tolerance)):
        raise PhysicalityError("Negative squared symplectic eigenvalue.")
    lambda1_events = _roundoff_events("lambda1_squared", lambda1_squared)
    lambda2_events = _roundoff_events("lambda2_squared", lambda2_squared)
    if lambda1_events or lambda2_events:
        repairs.append("explicitly guarded tiny negative squared symplectic eigenvalue")
    roundoff_events.extend(lambda1_events)
    roundoff_events.extend(lambda2_events)
    # At the analytic physical boundary one symplectic eigenvalue is exactly
    # one.  Reconstructing ``z_phys`` and squaring it can leave an O(eps)
    # residual, so recognize only a machine-precision boundary residual and
    # evaluate the exact boundary identity.  This is recorded explicitly; it
    # is not a generic subunit-eigenvalue clamp.
    physical_bound_radicand = a * b - 1.0 - torch.abs(a - b)
    boundary_residual = c.square() - physical_bound_radicand
    boundary_scale = torch.maximum(
        torch.ones_like(physical_bound_radicand), physical_bound_radicand.abs()
    )
    boundary_tolerance = 4.0 * torch.finfo(delta.dtype).eps * boundary_scale
    at_physical_boundary = torch.abs(boundary_residual) <= boundary_tolerance
    boundary_indices = torch.nonzero(at_physical_boundary, as_tuple=False).reshape(-1)
    if boundary_indices.numel():
        roundoff_events.extend(
            {
                "quantity": "physical_boundary_symplectic_identity",
                "batch_index": int(index.detach()),
                "value": float(boundary_residual[index].detach()),
                "treatment": (
                    "evaluate_exact_lambda2_squared_boundary_identity_as_one; "
                    "machine_precision_residual_only"
                ),
            }
            for index in boundary_indices
        )
        repairs.append("explicitly evaluated machine-precision physical-boundary identity")
        lambda2_squared = torch.where(
            at_physical_boundary, torch.ones_like(lambda2_squared), lambda2_squared
        )
    lambda1 = torch.sqrt(torch.where(
        lambda1_squared < 0.0, torch.zeros_like(lambda1_squared), lambda1_squared
    ))
    lambda2 = torch.sqrt(torch.where(
        lambda2_squared < 0.0, torch.zeros_like(lambda2_squared), lambda2_squared
    ))
    # This numerator form avoids the boundary cancellation in
    # ``a - c**2/(b+1)`` when the exact conditional eigenvalue is one.
    lambda3 = (a * (b + 1.0) - c.square()) / (b + 1.0)
    # If b>a at the same analytic boundary, the conditional eigenvalue is
    # exactly one as well.  Use that identity only on the same recorded
    # machine-precision boundary event; elsewhere retain the stable numerator
    # expression above.
    conditional_boundary = at_physical_boundary & (b > a)
    conditional_indices = torch.nonzero(conditional_boundary, as_tuple=False).reshape(-1)
    if conditional_indices.numel():
        roundoff_events.extend(
            {
                "quantity": "physical_boundary_conditional_identity",
                "batch_index": int(index.detach()),
                "value": float(boundary_residual[index].detach()),
                "treatment": (
                    "evaluate_exact_lambda3_boundary_identity_as_one; "
                    "machine_precision_residual_only"
                ),
            }
            for index in conditional_indices
        )
        repairs.append("explicitly evaluated machine-precision conditional-boundary identity")
        lambda3 = torch.where(conditional_boundary, torch.ones_like(lambda3), lambda3)
    minimum_lambda = torch.minimum(torch.minimum(lambda1, lambda2), lambda3)
    if bool(torch.any(minimum_lambda < 1.0)):
        raise PhysicalityError(
            "Covariance violates lambda>=1; no subunit symplectic eigenvalue is clipped."
        )
    return CovarianceResult(
        matrix,
        a,
        b,
        c,
        lambda1,
        lambda2,
        lambda3,
        symmetry,
        tuple(repairs),
        tuple(roundoff_events),
    )
