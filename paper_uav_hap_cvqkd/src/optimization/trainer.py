"""Small deterministic training/evaluation kernel; data generation remains external."""

from __future__ import annotations

from dataclasses import dataclass, replace
import copy
import math

import torch

from src.cvqkd.holevo import HolevoResult, holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.secret_key_rate import FadingKeyRate, fading_secret_key_rate
from src.modulation.joint_ps_gs import (
    Ensemble,
    JointTransmitter,
    PeakPhotonConstraintViolation,
)
from .constraints import ensemble_constraint_metrics, ensemble_state_diagnostics


@dataclass(frozen=True)
class Evaluation:
    ensemble: Ensemble
    mutual_information: torch.Tensor
    holevo: HolevoResult
    key_rate: FadingKeyRate
    constraints: dict[str, float]
    state_diagnostics: dict[str, torch.Tensor]
    optimization_loss: torch.Tensor | None = None
    negative_raw_skr: torch.Tensor | None = None
    energy_constraint_violation: torch.Tensor | None = None
    energy_dual_before_update: float | None = None
    energy_dual_after_update: float | None = None
    peak_feasible_step_accepted: bool | None = None


@dataclass
class EnergyBudgetController:
    """Projected primal-dual controller for the frozen average-``V_A`` constraint.

    The numerical budget and ascent learning rate are mandatory.  Omitting the
    controller from :func:`train_step` leaves the raw-SKR objective unchanged.
    """

    va_budget: float
    dual_learning_rate: float
    multiplier: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.va_budget) or self.va_budget <= 0.0:
            raise ValueError("va_budget must be finite and positive.")
        if not math.isfinite(self.dual_learning_rate) or self.dual_learning_rate <= 0.0:
            raise ValueError("dual_learning_rate must be finite and positive.")
        if not math.isfinite(self.multiplier) or self.multiplier < 0.0:
            raise ValueError("The initial energy multiplier must be finite and nonnegative.")

    def constraint_term(self, modulation_variance: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if modulation_variance.ndim != 1 or modulation_variance.numel() == 0:
            raise ValueError("modulation_variance must have nonempty shape [B].")
        if not bool(torch.all(torch.isfinite(modulation_variance))) or bool(
            torch.any(modulation_variance <= 0.0)
        ):
            raise ValueError("modulation_variance must be finite and positive.")
        violation = modulation_variance.mean() - self.va_budget
        return self.multiplier * violation, violation

    def projected_ascent(self, violation: torch.Tensor) -> None:
        if violation.numel() != 1 or not bool(torch.isfinite(violation.detach())):
            raise ValueError("Energy-budget violation must be one finite scalar.")
        updated = self.multiplier + self.dual_learning_rate * float(violation.detach())
        self.multiplier = max(0.0, updated)

    def state_dict(self) -> dict[str, float]:
        return {
            "va_budget": self.va_budget,
            "dual_learning_rate": self.dual_learning_rate,
            "multiplier": self.multiplier,
        }


def evaluate_transmitter(
    transmitter: JointTransmitter,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    beta_reconciliation: float,
    noise_samples_per_symbol: int,
    density_eigenvalue_tolerance: float,
    generator: torch.Generator,
    require_supported_symmetry: bool = True,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-8,
    physicality_tolerance: float = 1e-10,
) -> Evaluation:
    if not require_supported_symmetry:
        raise ValueError(
            "The frozen C4 trainer is fail-closed: standard-form symmetry is mandatory."
        )
    ensemble = transmitter(transmittance, epsilon)
    mutual_information = discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=noise_samples_per_symbol,
        generator=generator,
    )
    holevo = holevo_information(
        ensemble,
        transmittance,
        epsilon,
        backend="c4_gram",
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        density_trace_tolerance=density_trace_tolerance,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
        physicality_tolerance=physicality_tolerance,
    )
    key_rate = fading_secret_key_rate(mutual_information, holevo.chi_be, beta_reconciliation)
    constraints = ensemble_constraint_metrics(ensemble)
    if transmitter.n_peak_photons is not None:
        constraints.update({
            "peak_photon_limit": transmitter.n_peak_photons,
            "minimum_peak_photon_slack": (
                transmitter.n_peak_photons - constraints["maximum_symbol_energy"]
            ),
            "peak_photon_constraint_satisfied": 1.0,
        })
    return Evaluation(
        ensemble,
        mutual_information,
        holevo,
        key_rate,
        constraints,
        ensemble_state_diagnostics(ensemble),
    )


def train_step(
    transmitter: JointTransmitter,
    optimizer: torch.optim.Optimizer,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    beta_reconciliation: float,
    noise_samples_per_symbol: int,
    density_eigenvalue_tolerance: float,
    generator: torch.Generator,
    require_supported_symmetry: bool = True,
    gradient_clip_norm: float | None = None,
    energy_budget_controller: EnergyBudgetController | None = None,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-8,
    physicality_tolerance: float = 1e-10,
) -> Evaluation:
    if not require_supported_symmetry:
        raise ValueError(
            "The frozen C4 trainer is fail-closed: standard-form symmetry is mandatory."
        )
    transmitter.train()
    optimizer.zero_grad(set_to_none=True)
    evaluation = evaluate_transmitter(
        transmitter,
        transmittance,
        epsilon,
        beta_reconciliation=beta_reconciliation,
        noise_samples_per_symbol=noise_samples_per_symbol,
        generator=generator,
        require_supported_symmetry=require_supported_symmetry,
        symmetry_tolerance=symmetry_tolerance,
        density_trace_tolerance=density_trace_tolerance,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
        physicality_tolerance=physicality_tolerance,
    )
    negative_raw_skr = -evaluation.key_rate.fading_average_raw
    energy_term = torch.zeros_like(negative_raw_skr)
    violation: torch.Tensor | None = None
    dual_before: float | None = None
    if energy_budget_controller is not None:
        dual_before = energy_budget_controller.multiplier
        energy_term, violation = energy_budget_controller.constraint_term(
            evaluation.ensemble.declared_va
        )
    loss = negative_raw_skr + energy_term
    loss.backward()
    parameters = [
        parameter
        for parameter in transmitter.parameters()
        if parameter.requires_grad and parameter.grad is not None
    ]
    if not parameters:
        raise RuntimeError("Transmitter has no trainable parameters with gradients.")
    if any(not bool(torch.all(torch.isfinite(parameter.grad))) for parameter in parameters):
        raise FloatingPointError("Non-finite training gradient.")
    if gradient_clip_norm is not None:
        torch.nn.utils.clip_grad_norm_(parameters, gradient_clip_norm)
    # With a hard peak domain, a proposed optimizer update is accepted only if
    # its *physical* post-normalization ensemble remains feasible on the whole
    # current training batch. Both model and optimizer state are rolled back;
    # amplitudes are never clipped or projected after construction.
    model_before_step = (
        copy.deepcopy(transmitter.state_dict())
        if transmitter.n_peak_photons is not None else None
    )
    optimizer_before_step = (
        copy.deepcopy(optimizer.state_dict())
        if transmitter.n_peak_photons is not None else None
    )
    optimizer.step()
    peak_step_accepted: bool | None = None
    if transmitter.n_peak_photons is not None:
        try:
            transmitter(transmittance, epsilon)
            peak_step_accepted = True
        except PeakPhotonConstraintViolation:
            if model_before_step is None or optimizer_before_step is None:
                raise RuntimeError("Peak-domain rollback state was not captured.")
            transmitter.load_state_dict(model_before_step)
            optimizer.load_state_dict(optimizer_before_step)
            peak_step_accepted = False
    dual_after: float | None = None
    if energy_budget_controller is not None:
        if violation is None:
            raise RuntimeError("Energy controller was enabled without a constraint violation.")
        energy_budget_controller.projected_ascent(violation)
        dual_after = energy_budget_controller.multiplier
    return replace(
        evaluation,
        optimization_loss=loss.detach(),
        negative_raw_skr=negative_raw_skr.detach(),
        energy_constraint_violation=None if violation is None else violation.detach(),
        energy_dual_before_update=dual_before,
        energy_dual_after_update=dual_after,
        peak_feasible_step_accepted=peak_step_accepted,
    )
