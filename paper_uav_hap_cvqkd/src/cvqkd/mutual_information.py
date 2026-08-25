"""Differentiable Monte Carlo evaluation of paper Eqs. (91)--(101)."""

from __future__ import annotations

import math

import torch

from src.modulation.joint_ps_gs import Ensemble
from .protocol import validate_channel_state


def standard_complex_noise(
    shape: tuple[int, ...],
    *,
    generator: torch.Generator,
    device: torch.device,
    antithetic: bool = False,
) -> torch.Tensor:
    """Draw CN(0,1); independent samples are the paper default."""

    if any(size <= 0 for size in shape):
        raise ValueError("Noise dimensions must be positive.")
    if antithetic:
        independent = (shape[-1] + 1) // 2
        draw_shape = (*shape[:-1], independent)
    else:
        draw_shape = shape
    real = torch.randn(draw_shape, dtype=torch.float64, device=device, generator=generator)
    imag = torch.randn(draw_shape, dtype=torch.float64, device=device, generator=generator)
    noise = torch.complex(real, imag) / math.sqrt(2.0)
    if antithetic:
        noise = torch.cat((noise, -noise), dim=-1)[..., : shape[-1]]
    return noise


def discrete_mutual_information(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    noise_samples_per_symbol: int,
    generator: torch.Generator | None = None,
    standard_noise_samples: torch.Tensor | None = None,
    candidate_chunk_size: int = 64,
) -> torch.Tensor:
    """Return one discrete-input continuous-output MI value per fading state."""

    ensemble.validate()
    transmittance, epsilon = validate_channel_state(transmittance, epsilon)
    transmittance = transmittance.to(device=ensemble.probabilities.device)
    epsilon = epsilon.to(device=ensemble.probabilities.device)
    batch_size, symbol_count = ensemble.probabilities.shape
    if transmittance.shape[0] != batch_size:
        raise ValueError("Channel-state count must match ensemble batch size.")
    if not isinstance(noise_samples_per_symbol, int) or noise_samples_per_symbol <= 0:
        raise ValueError("noise_samples_per_symbol must be a positive integer.")
    if not isinstance(candidate_chunk_size, int) or candidate_chunk_size <= 0:
        raise ValueError("candidate_chunk_size must be a positive integer.")
    expected_shape = (batch_size, symbol_count, noise_samples_per_symbol)
    if standard_noise_samples is None:
        if generator is None:
            raise ValueError("An explicit generator or standard_noise_samples is required.")
        standard_noise_samples = standard_complex_noise(
            expected_shape,
            generator=generator,
            device=ensemble.probabilities.device,
            antithetic=False,
        )
    if standard_noise_samples.shape != expected_shape or not standard_noise_samples.is_complex():
        raise ValueError("standard_noise_samples has the wrong shape or dtype.")
    sigma2_complex = 1.0 + transmittance * epsilon / 2.0
    means = torch.sqrt(transmittance).unsqueeze(-1) * ensemble.amplitudes
    received = means.unsqueeze(-1) + torch.sqrt(sigma2_complex)[:, None, None] * standard_noise_samples
    probabilities = ensemble.probabilities
    if probabilities.requires_grad and bool(torch.any(probabilities <= 0.0)):
        raise ValueError(
            "Differentiable MI requires strictly positive probabilities; an exact-zero "
            "boundary has singular entropy gradients."
        )
    positive_probability = probabilities > 0.0
    log_probabilities = torch.where(
        positive_probability,
        torch.log(probabilities),
        torch.full_like(probabilities, -torch.inf),
    )
    entropy = -torch.sum(torch.special.xlogy(probabilities, probabilities), dim=-1) / math.log(2.0)
    log_denominator: torch.Tensor | None = None
    for start in range(0, symbol_count, candidate_chunk_size):
        stop = min(start + candidate_chunk_size, symbol_count)
        distances = (
            received[:, :, :, None] - means[:, None, None, start:stop]
        ).abs().square()
        logits = (
            log_probabilities[:, None, None, start:stop]
            - distances / sigma2_complex[:, None, None, None]
        )
        chunk = torch.logsumexp(logits, dim=-1)
        log_denominator = chunk if log_denominator is None else torch.logaddexp(log_denominator, chunk)
    if log_denominator is None:
        raise RuntimeError("No candidate symbols were evaluated.")
    true_distance = (received - means.unsqueeze(-1)).abs().square()
    true_logits = log_probabilities[:, :, None] - true_distance / sigma2_complex[:, None, None]
    posterior_log = torch.where(
        positive_probability[:, :, None],
        true_logits - log_denominator,
        torch.zeros_like(true_logits),
    )
    conditional = torch.sum(
        probabilities * torch.mean(posterior_log, dim=-1), dim=-1
    ) / math.log(2.0)
    value = entropy + conditional
    if not bool(torch.all(torch.isfinite(value))):
        raise FloatingPointError("Mutual-information estimator returned NaN or Inf.")
    return value
