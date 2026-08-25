"""Small deterministic training/evaluation kernel; data generation remains external."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from src.cvqkd.holevo import HolevoResult, holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.secret_key_rate import FadingKeyRate, fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, JointTransmitter
from .constraints import ensemble_constraint_metrics


@dataclass(frozen=True)
class Evaluation:
    ensemble: Ensemble
    mutual_information: torch.Tensor
    holevo: HolevoResult
    key_rate: FadingKeyRate
    constraints: dict[str, float]


def evaluate_transmitter(
    transmitter: JointTransmitter,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    beta_reconciliation: float,
    noise_samples_per_symbol: int,
    fock_cutoff: int,
    generator: torch.Generator,
    require_supported_symmetry: bool = True,
) -> Evaluation:
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
        fock_cutoff=fock_cutoff,
        require_supported_symmetry=require_supported_symmetry,
    )
    key_rate = fading_secret_key_rate(mutual_information, holevo.chi_be, beta_reconciliation)
    return Evaluation(
        ensemble,
        mutual_information,
        holevo,
        key_rate,
        ensemble_constraint_metrics(ensemble),
    )


def train_step(
    transmitter: JointTransmitter,
    optimizer: torch.optim.Optimizer,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    beta_reconciliation: float,
    noise_samples_per_symbol: int,
    fock_cutoff: int,
    generator: torch.Generator,
    require_supported_symmetry: bool = True,
    gradient_clip_norm: float | None = None,
) -> Evaluation:
    transmitter.train()
    optimizer.zero_grad(set_to_none=True)
    evaluation = evaluate_transmitter(
        transmitter,
        transmittance,
        epsilon,
        beta_reconciliation=beta_reconciliation,
        noise_samples_per_symbol=noise_samples_per_symbol,
        fock_cutoff=fock_cutoff,
        generator=generator,
        require_supported_symmetry=require_supported_symmetry,
    )
    loss = -evaluation.key_rate.fading_average_raw
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
    optimizer.step()
    return evaluation

