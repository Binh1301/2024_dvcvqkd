"""Explicit physical-constraint checks."""

from __future__ import annotations

import torch

from src.modulation.joint_ps_gs import Ensemble


def ensemble_constraint_metrics(ensemble: Ensemble) -> dict[str, float]:
    ensemble.validate()
    mean = torch.sum(ensemble.probabilities * ensemble.amplitudes, dim=-1)
    va_error = torch.abs(ensemble.computed_va() - ensemble.declared_va)
    return {
        "maximum_probability_sum_error": float(
            torch.abs(ensemble.probabilities.sum(dim=-1) - 1.0).detach().max()
        ),
        "maximum_weighted_mean_magnitude": float(mean.abs().detach().max()),
        "maximum_va_error": float(va_error.detach().max()),
        "minimum_probability": float(ensemble.probabilities.detach().min()),
        "maximum_symbol_energy": float(ensemble.amplitudes.abs().square().detach().max()),
    }

