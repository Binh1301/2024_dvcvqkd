"""Differentiable discrete-input mutual information for the QAM channel."""

from __future__ import annotations

import math
from typing import Optional

import torch


def normalize_constellation(
    probs: torch.Tensor,
    alpha: torch.Tensor,
    modulation_variance: float | torch.Tensor,
) -> torch.Tensor:
    """Center ``alpha`` and enforce ``2 E[|alpha|^2] = modulation_variance``."""
    if probs.ndim != 1 or alpha.ndim != 1 or probs.numel() != alpha.numel():
        raise ValueError("probs and alpha must be one-dimensional tensors of equal length.")

    target_va = torch.as_tensor(modulation_variance, dtype=probs.dtype, device=probs.device)
    if bool(torch.any(target_va <= 0.0)):
        raise ValueError("modulation_variance must be positive.")

    centered = alpha - torch.sum(probs * alpha)
    current_va = 2.0 * torch.sum(probs * centered.abs().square())
    if bool(current_va <= 0.0):
        raise ValueError("The constellation must have positive modulation variance.")
    return centered * torch.sqrt(target_va / current_va)


def mismatched_mi_discrete_awgn(
    probs: torch.Tensor,
    alpha: torch.Tensor,
    transmittance: torch.Tensor | float,
    excess_noise_snu: torch.Tensor | float,
    noise_samples_per_symbol: int = 8,
    generator: Optional[torch.Generator] = None,
    antithetic: bool = True,
    candidate_chunk_size: Optional[int] = None,
) -> torch.Tensor:
    """Estimate one achievable discrete-input MI value per fading sample.

    The transmitted symbols are enumerated exactly and weighted by ``probs``;
    only the complex AWGN is sampled. The channel convention is

        Y = sqrt(T) alpha_X + N,
        N ~ CN(0, 1 + T * excess_noise_snu / 2).

    Args:
        probs: Symbol probabilities with shape ``[M]``.
        alpha: Complex constellation with shape ``[M]``.
        transmittance: Scalar or vector of instantaneous values with shape ``[B]``.
        excess_noise_snu: Scalar or one value per fading sample.
        noise_samples_per_symbol: Number ``K`` of AWGN samples per symbol.
        generator: Optional generator controlling only the AWGN draws.
        antithetic: Pair each sampled noise value with its negative.
        candidate_chunk_size: Candidate-symbol chunk size for bounded memory use.

    Returns:
        A real tensor of shape ``[B]`` in bits per transmitted symbol.
    """
    if probs.ndim != 1 or alpha.ndim != 1 or probs.numel() != alpha.numel():
        raise ValueError("probs and alpha must be one-dimensional tensors of equal length.")
    if not probs.is_floating_point():
        raise TypeError("probs must be a real floating-point tensor.")
    if not alpha.is_complex():
        raise TypeError("alpha must be a complex tensor.")
    if alpha.device != probs.device:
        raise ValueError("probs and alpha must be on the same device.")
    if noise_samples_per_symbol <= 0:
        raise ValueError("noise_samples_per_symbol must be positive.")
    if bool(torch.any(probs < 0.0)) or bool(torch.sum(probs) <= 0.0):
        raise ValueError("probs must be non-negative with positive total mass.")
    probability_tolerance = 1e-10 if probs.dtype == torch.float64 else 1e-6
    if bool(torch.abs(torch.sum(probs) - 1.0) > probability_tolerance):
        raise ValueError("probs must sum to one.")

    real_dtype = probs.dtype
    complex_dtype = torch.complex128 if real_dtype == torch.float64 else torch.complex64
    alpha = alpha.to(dtype=complex_dtype)
    transmittance = torch.as_tensor(transmittance, dtype=real_dtype, device=probs.device).reshape(-1)
    excess_noise = torch.as_tensor(excess_noise_snu, dtype=real_dtype, device=probs.device)
    if excess_noise.ndim == 0:
        excess_noise = excess_noise.expand_as(transmittance)
    else:
        excess_noise = excess_noise.reshape(-1)
        if excess_noise.numel() != transmittance.numel():
            raise ValueError("excess_noise_snu must be scalar or match transmittance.")
    if bool(torch.any(transmittance < 0.0)):
        raise ValueError("transmittance must be non-negative.")
    if bool(torch.any(excess_noise < 0.0)):
        raise ValueError("excess_noise_snu must be non-negative.")

    sigma2 = 1.0 + transmittance * excess_noise / 2.0
    if bool(torch.any(sigma2 <= 0.0)):
        raise ValueError("The complex noise variance must be positive.")

    symbol_count = probs.numel()
    chunk_size = symbol_count if candidate_chunk_size is None else int(candidate_chunk_size)
    if chunk_size <= 0:
        raise ValueError("candidate_chunk_size must be positive when provided.")

    # The 1e-300 floor is only for logarithm protection in float64 operation.
    log_floor = max(1e-300, torch.finfo(real_dtype).tiny)
    log_probs = torch.log(probs.clamp_min(log_floor))
    entropy_bits = -torch.sum(probs * (log_probs / math.log(2.0)))

    sqrt_t = torch.sqrt(transmittance)
    means = sqrt_t[:, None] * alpha[None, :]
    batch_size = transmittance.numel()
    if antithetic:
        independent_count = (noise_samples_per_symbol + 1) // 2
    else:
        independent_count = noise_samples_per_symbol

    noise_shape = (batch_size, symbol_count, independent_count)
    noise_real = torch.randn(noise_shape, dtype=real_dtype, device=probs.device, generator=generator)
    noise_imag = torch.randn(noise_shape, dtype=real_dtype, device=probs.device, generator=generator)
    noise = torch.complex(noise_real, noise_imag) * torch.sqrt(sigma2[:, None, None] / 2.0)
    if antithetic:
        noise = torch.cat((noise, -noise), dim=2)[:, :, :noise_samples_per_symbol]
    received = means[:, :, None] + noise

    log_denominator: Optional[torch.Tensor] = None
    for start in range(0, symbol_count, chunk_size):
        stop = min(start + chunk_size, symbol_count)
        candidate_means = means[:, None, None, start:stop]
        candidate_distances = (received[:, :, :, None] - candidate_means).abs().square()
        candidate_logits = (
            log_probs[None, None, None, start:stop]
            - candidate_distances / sigma2[:, None, None, None]
        )
        chunk_logsumexp = torch.logsumexp(candidate_logits, dim=-1)
        log_denominator = (
            chunk_logsumexp
            if log_denominator is None
            else torch.logaddexp(log_denominator, chunk_logsumexp)
        )

    true_distances = (received - means[:, :, None]).abs().square()
    true_logits = log_probs[None, :, None] - true_distances / sigma2[:, None, None]
    correct_log_posterior = true_logits - log_denominator
    conditional_term = torch.sum(
        probs[None, :] * torch.mean(correct_log_posterior, dim=2) / math.log(2.0),
        dim=1,
    )
    return entropy_bits + conditional_term
