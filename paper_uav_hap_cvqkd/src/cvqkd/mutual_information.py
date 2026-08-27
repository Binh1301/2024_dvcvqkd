"""Differentiable Monte Carlo evaluation of paper Eqs. (91)--(101)."""

from __future__ import annotations

import math

import torch

from src.modulation.joint_ps_gs import Ensemble
from .protocol import validate_channel_state


def _product_qam_factors(
    probabilities: torch.Tensor, means: torch.Tensor, *, tolerance: float = 1e-12
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return exact 16x16 Cartesian/product factors or fail closed."""

    if probabilities.shape[-1] != 256 or means.shape != probabilities.shape:
        raise ValueError("Product-QAM MI requires 256 row-major symbols.")
    batch_size = probabilities.shape[0]
    probability_grid = probabilities.reshape(batch_size, 16, 16)
    mean_grid = means.reshape(batch_size, 16, 16)
    real_probabilities = probability_grid.sum(dim=-1)
    imag_probabilities = probability_grid.sum(dim=-2)
    reconstructed = real_probabilities.unsqueeze(-1) * imag_probabilities.unsqueeze(-2)
    real_levels = mean_grid[:, :, 0].real
    imag_levels = mean_grid[:, 0, :].imag
    reconstructed_means = torch.complex(
        real_levels.unsqueeze(-1).expand(-1, -1, 16),
        imag_levels.unsqueeze(-2).expand(-1, 16, -1),
    )
    if not bool(torch.allclose(
        reconstructed.detach(), probability_grid.detach(), atol=tolerance, rtol=tolerance
    )):
        raise ValueError("PMF is not an exact 16x16 product distribution.")
    if not bool(torch.allclose(
        reconstructed_means.detach(), mean_grid.detach(), atol=tolerance, rtol=tolerance
    )):
        raise ValueError("Constellation is not an exact row-major Cartesian product.")
    return real_probabilities, imag_probabilities, real_levels, imag_levels


def is_product_qam_ensemble(ensemble: Ensemble) -> bool:
    """Return whether the ensemble admits the exact Cartesian/product path."""

    try:
        _product_qam_factors(ensemble.probabilities, ensemble.amplitudes)
    except ValueError:
        return False
    return True


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
    noise_sample_chunk_size: int | None = None,
    implementation: str = "optimized",
) -> torch.Tensor:
    """Return one discrete-input continuous-output MI value per fading state."""

    if implementation not in {"optimized", "reference", "product"}:
        raise ValueError("implementation must be 'optimized', 'reference', or 'product'.")
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
    if noise_sample_chunk_size is None:
        noise_sample_chunk_size = noise_samples_per_symbol
    if not isinstance(noise_sample_chunk_size, int) or noise_sample_chunk_size <= 0:
        raise ValueError("noise_sample_chunk_size must be a positive integer or None.")
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
    product_factors = (
        _product_qam_factors(probabilities, means)
        if implementation == "product" else None
    )
    # Chunking the noise axis is an exact batching transformation: the same
    # explicit noise tensor and estimator are used, while peak memory no longer
    # grows with the convergence reference count.
    conditional_sum = torch.zeros(
        batch_size, dtype=torch.float64, device=ensemble.probabilities.device
    )
    for noise_start in range(0, noise_samples_per_symbol, noise_sample_chunk_size):
        noise_stop = min(noise_start + noise_sample_chunk_size, noise_samples_per_symbol)
        received = (
            means.unsqueeze(-1)
            + torch.sqrt(sigma2_complex)[:, None, None]
            * standard_noise_samples[..., noise_start:noise_stop]
        )
        log_denominator: torch.Tensor | None = None
        if product_factors is not None:
            real_p, imag_p, real_levels, imag_levels = product_factors
            log_real_p = torch.where(
                real_p > 0.0, torch.log(real_p), torch.full_like(real_p, -torch.inf)
            )
            log_imag_p = torch.where(
                imag_p > 0.0, torch.log(imag_p), torch.full_like(imag_p, -torch.inf)
            )
            real_logits = (
                log_real_p[:, None, None, :]
                - (received.real[..., None] - real_levels[:, None, None, :]).square()
                / sigma2_complex[:, None, None, None]
            )
            imag_logits = (
                log_imag_p[:, None, None, :]
                - (received.imag[..., None] - imag_levels[:, None, None, :]).square()
                / sigma2_complex[:, None, None, None]
            )
            log_denominator = (
                torch.logsumexp(real_logits, dim=-1)
                + torch.logsumexp(imag_logits, dim=-1)
            )
        for start in range(0, symbol_count, candidate_chunk_size) if product_factors is None else ():
            stop = min(start + candidate_chunk_size, symbol_count)
            candidate_means = means[:, start:stop]
            if implementation == "reference":
                distances = (
                    received[:, :, :, None] - candidate_means[:, None, None, :]
                ).abs().square()
            else:
                # Exact algebraic identity
                # |y-m|^2=|y|^2+|m|^2-2(Re(y)Re(m)+Im(y)Im(m)).
                # Flattening only the source/noise observation axes turns the
                # dominant pairwise operation into two optimized real float64
                # matrix products.  The candidate chunks, CRN tensor, mixture,
                # summation order between chunks, and estimator are unchanged.
                observations = received.reshape(batch_size, -1)
                observation_coordinates = torch.stack(
                    (observations.real, observations.imag), dim=-1
                )
                candidate_coordinates = torch.stack(
                    (candidate_means.real, candidate_means.imag), dim=-1
                )
                dot = observation_coordinates @ candidate_coordinates.transpose(-2, -1)
                distances = (
                    observations.abs().square().unsqueeze(-1)
                    + candidate_means.abs().square().unsqueeze(-2)
                    - 2.0 * dot
                ).reshape(batch_size, symbol_count, noise_stop - noise_start, -1)
                # A negative value can only be roundoff from the algebraic
                # rearrangement (the exact squared distance is nonnegative).
                distances = torch.clamp_min(distances, 0.0)
            logits = (
                log_probabilities[:, None, None, start:stop]
                - distances / sigma2_complex[:, None, None, None]
            )
            chunk = torch.logsumexp(logits, dim=-1)
            log_denominator = (
                chunk if log_denominator is None
                else torch.logaddexp(log_denominator, chunk)
            )
        if log_denominator is None:
            raise RuntimeError("No candidate symbols were evaluated.")
        true_distance = (received - means.unsqueeze(-1)).abs().square()
        true_logits = (
            log_probabilities[:, :, None]
            - true_distance / sigma2_complex[:, None, None]
        )
        posterior_log = torch.where(
            positive_probability[:, :, None],
            true_logits - log_denominator,
            torch.zeros_like(true_logits),
        )
        conditional_sum = conditional_sum + torch.sum(
            probabilities[:, :, None] * posterior_log, dim=(-2, -1)
        )
    conditional = conditional_sum / (noise_samples_per_symbol * math.log(2.0))
    value = entropy + conditional
    if not bool(torch.all(torch.isfinite(value))):
        raise FloatingPointError("Mutual-information estimator returned NaN or Inf.")
    return value
