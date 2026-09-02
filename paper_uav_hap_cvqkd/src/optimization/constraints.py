"""Explicit physical-constraint checks."""

from __future__ import annotations

import torch

from src.modulation.joint_ps_gs import Ensemble


def validation_expected_budget_status(
    mean_va_snu: float, va_budget_snu: float, margin_snu: float
) -> dict[str, float | bool]:
    """Test-blind upper estimate used for adaptive-VA checkpoint eligibility."""

    values = torch.as_tensor((mean_va_snu, va_budget_snu, margin_snu), dtype=torch.float64)
    if not bool(torch.all(torch.isfinite(values))):
        raise ValueError("Budget mean, budget, and margin must be finite.")
    if mean_va_snu <= 0.0 or va_budget_snu <= 0.0 or margin_snu < 0.0:
        raise ValueError("Budget mean/budget must be positive and margin nonnegative.")
    upper = float(mean_va_snu + margin_snu)
    slack = float(va_budget_snu - upper)
    return {
        "validation_mean_va_snu": float(mean_va_snu),
        "preregistered_margin_snu": float(margin_snu),
        "expected_budget_upper_snu": upper,
        "expected_budget_slack_snu": slack,
        "expected_budget_feasible": slack >= -1e-12,
    }


def heldout_budget_comparison_status(
    mean_va_snu: float, va_budget_snu: float
) -> dict[str, float | bool | str | None]:
    """Classify held-out budget validity without authorizing reselection."""

    status = validation_expected_budget_status(mean_va_snu, va_budget_snu, 0.0)
    valid = bool(status["expected_budget_feasible"])
    return {
        "heldout_mean_va_snu": float(mean_va_snu),
        "heldout_budget_snu": float(va_budget_snu),
        "heldout_budget_slack_snu": float(va_budget_snu - mean_va_snu),
        "heldout_budget_feasible": valid,
        "comparison_valid": valid,
        "invalid_reason": None if valid else (
            "held-out mean V_A exceeds the preregistered budget; retain the artifact, "
            "but do not publish it as an energy-fair comparison and do not retrain/reselect"
        ),
    }


def ensemble_state_diagnostics(ensemble: Ensemble) -> dict[str, torch.Tensor]:
    """Return required energy/adaptivity diagnostics for every channel state."""

    ensemble.validate()
    va = ensemble.computed_va()
    symbol_energy = ensemble.amplitudes.abs().square()
    maximum_energy = symbol_energy.max(dim=-1).values
    sorted_energy, order = torch.sort(symbol_energy, dim=-1)
    sorted_probability = torch.gather(ensemble.probabilities, -1, order)
    cumulative_probability = torch.cumsum(sorted_probability, dim=-1)
    quantile_index = torch.searchsorted(
        cumulative_probability,
        torch.full(
            (cumulative_probability.shape[0], 1),
            0.99,
            dtype=cumulative_probability.dtype,
            device=cumulative_probability.device,
        ),
    ).clamp_max(symbol_energy.shape[-1] - 1)
    energy_quantile_99 = torch.gather(sorted_energy, -1, quantile_index).squeeze(-1)
    physical_coordinates = torch.view_as_real(ensemble.amplitudes)
    pairwise = torch.cdist(physical_coordinates, physical_coordinates)
    diagonal = torch.eye(
        pairwise.shape[-1], dtype=torch.bool, device=pairwise.device
    ).unsqueeze(0)
    minimum_physical_distance = pairwise.masked_fill(diagonal, torch.inf).amin(dim=(-2, -1))
    relative = ensemble.relative_constellation
    relative_coordinates = torch.view_as_real(relative)
    relative_minimum = torch.pdist(relative_coordinates).min()
    entropy_bits = -torch.sum(
        torch.special.xlogy(ensemble.probabilities, ensemble.probabilities), dim=-1
    ) / torch.log(torch.tensor(2.0, dtype=va.dtype, device=va.device))
    return {
        "modulation_variance": va,
        "mean_photon_number": va / 2.0,
        "maximum_symbol_energy": maximum_energy,
        "symbol_energy_quantile_99": energy_quantile_99,
        "papr": 2.0 * maximum_energy / va,
        "entropy_bits": entropy_bits,
        "minimum_physical_pair_distance": minimum_physical_distance,
        "minimum_relative_pair_distance": relative_minimum.expand_as(va),
    }


def ensemble_constraint_metrics(ensemble: Ensemble) -> dict[str, float]:
    ensemble.validate()
    mean = ensemble.weighted_mean()
    pseudomoment = ensemble.weighted_pseudomoment()
    va_error = torch.abs(ensemble.computed_va() - ensemble.declared_va)
    state = ensemble_state_diagnostics(ensemble)
    return {
        "maximum_probability_sum_error": float(
            torch.abs(ensemble.probabilities.sum(dim=-1) - 1.0).detach().max()
        ),
        "maximum_weighted_mean_magnitude": float(mean.abs().detach().max()),
        "maximum_weighted_pseudomoment_magnitude": float(pseudomoment.abs().detach().max()),
        "maximum_va_error": float(va_error.detach().max()),
        "minimum_probability": float(ensemble.probabilities.detach().min()),
        "minimum_entropy_bits": float(state["entropy_bits"].detach().min()),
        "maximum_entropy_bits": float(state["entropy_bits"].detach().max()),
        "mean_modulation_variance": float(state["modulation_variance"].detach().mean()),
        "mean_photon_number": float(state["mean_photon_number"].detach().mean()),
        "maximum_symbol_energy": float(state["maximum_symbol_energy"].detach().max()),
        "maximum_symbol_energy_quantile_99": float(
            state["symbol_energy_quantile_99"].detach().max()
        ),
        "maximum_papr": float(state["papr"].detach().max()),
        "minimum_physical_pair_distance": float(
            state["minimum_physical_pair_distance"].detach().min()
        ),
        "minimum_relative_pair_distance": float(
            state["minimum_relative_pair_distance"].detach().min()
        ),
    }
