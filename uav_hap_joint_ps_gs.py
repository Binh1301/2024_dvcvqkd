"""Joint probabilistic and geometric shaping for UAV-HAP 256-QAM CV-QKD.

This standalone experiment reuses the project's channel, configuration, and
constellation APIs without modifying them. The security calculation follows
the equations in ``uav_hap_1.zstar.base``, but is expressed in complex128
PyTorch so probabilities and constellation coordinates retain gradients.

Fourfold symmetry preserves the project's deterministic ``k * 16 + l`` symbol
ordering. Entry ``(k, l)`` uses first-quadrant prototype
``(8 + qx, 8 + qy)``, where ``qx = k - 8`` for ``k >= 8`` and ``7 - k``
otherwise (and likewise for ``qy``). The corresponding x/y signs mirror that
prototype into all four quadrants.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.nn import functional as torch_functional

from uav_hap_1.channel.channel_model import channel
from uav_hap_1.config import (
    QAM_ALPHA0_UNIFORM,
    QAM_BETA,
    QAM_EPS,
    QAM_ETA,
    QAM_NCUT_UNIFORM,
    QAM_NU_TILDE,
    QAM_V_EL,
    ChannelParams,
    GeometryParams,
)
from uav_hap_1.zstar import base as project_zbase
from uav_hap_1.zstar import uniform as project_uniform
from uav_hap_1_sample.iab.discrete import (
    mismatched_mi_discrete_awgn as project_discrete_mi,
)


SYMBOL_COUNT = 256
GRID_SIDE = 16
LOG2 = math.log(2.0)
REAL_DTYPE = torch.float64
COMPLEX_DTYPE = torch.complex128


@dataclass
class ModelOutput:
    probabilities: torch.Tensor
    probabilities_safe: torch.Tensor
    unit_constellation: torch.Tensor
    constellation: torch.Tensor
    logits: torch.Tensor
    features: torch.Tensor
    gumbel_symbols: torch.Tensor | None


@dataclass
class SecurityOutput:
    tau: torch.Tensor
    tau_eigenvalues: torch.Tensor
    tau_trace: torch.Tensor
    tr_c: torch.Tensor
    w: torch.Tensor
    z_raw: torch.Tensor
    z: torch.Tensor
    gamma_ab: torch.Tensor
    lambda1: torch.Tensor
    lambda2: torch.Tensor
    lambda3: torch.Tensor
    chi_be: torch.Tensor


@dataclass
class LossOutput:
    total: torch.Tensor
    skr: torch.Tensor
    separation: torch.Tensor
    peak: torch.Tensor
    drift: torch.Tensor
    entropy: torch.Tensor
    raw_skr: torch.Tensor


@dataclass
class SchemeEvaluation:
    name: str
    transmittance: torch.Tensor
    probabilities: torch.Tensor
    unit_constellation: torch.Tensor
    constellation: torch.Tensor
    entropy: torch.Tensor
    i_ab: torch.Tensor
    security: SecurityOutput
    raw_skr: torch.Tensor
    reported_skr: torch.Tensor


def set_deterministic_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def tensor_generator(seed: int, device: torch.device) -> torch.Generator:
    generator_device = device.type if device.type == "cuda" else "cpu"
    return torch.Generator(device=generator_device).manual_seed(int(seed))


def build_project_qam(device: torch.device) -> torch.Tensor:
    complex_points = np.asarray(
        project_zbase.build_constellation(float(QAM_ALPHA0_UNIFORM)),
        dtype=np.complex128,
    )
    coordinates = np.column_stack((complex_points.real, complex_points.imag))
    return torch.as_tensor(coordinates, dtype=REAL_DTYPE, device=device)


def project_probabilities(kind: str, device: torch.device) -> torch.Tensor:
    if kind == "uniform":
        values = project_zbase.build_probs_uniform()
    elif kind == "mb":
        values = project_zbase.build_probs_mb(float(QAM_NU_TILDE))
    else:
        raise ValueError(f"Unsupported probability initialization: {kind}")
    return torch.as_tensor(values, dtype=REAL_DTYPE, device=device)


def complex_from_xy(points: torch.Tensor) -> torch.Tensor:
    return torch.complex(points[..., 0], points[..., 1])


def normalize_constellation_batch(
    probabilities: torch.Tensor,
    constellation: torch.Tensor,
    target_va: float | torch.Tensor,
    eps: float = 1e-15,
) -> torch.Tensor:
    """Center each ensemble and enforce ``2 E_p[|alpha|^2] = V_A``."""
    if probabilities.ndim != 2:
        raise ValueError("probabilities must have shape [B, 256].")
    if constellation.ndim == 1:
        constellation = constellation.unsqueeze(0).expand(probabilities.shape[0], -1)
    if constellation.shape != probabilities.shape:
        raise ValueError("constellation must have shape [256] or [B, 256].")
    mu = torch.sum(probabilities * constellation, dim=-1, keepdim=True)
    centered = constellation - mu
    current_va = 2.0 * torch.sum(probabilities * centered.abs().square(), dim=-1, keepdim=True)
    target = torch.as_tensor(target_va, dtype=probabilities.dtype, device=probabilities.device)
    scale = torch.sqrt(target.reshape(-1, 1) / (current_va + eps))
    return scale * centered


def normalize_unit_energy_batch(
    probabilities: torch.Tensor,
    constellation: torch.Tensor,
    eps: float = 1e-15,
) -> torch.Tensor:
    """Center an ensemble and enforce ``E_p[|x|^2] = 1`` without detaching."""
    return normalize_constellation_batch(
        probabilities,
        constellation,
        target_va=2.0,
        eps=eps,
    )


class JointPSGS256QAM(nn.Module):
    """State-conditioned 256-QAM probabilistic/geometric shaping model."""

    valid_modes = {"ps", "gs", "joint"}
    valid_symmetries = {"fourfold", "central", "none"}

    def __init__(
        self,
        base_qam: torch.Tensor,
        mode: str = "joint",
        symmetry: str = "fourfold",
        target_va: float = 2.0,
        input_dim: int = 3,
        hidden_dim: int = 128,
        probability_initialization: str = "uniform",
        logit_clip: float | None = 30.0,
    ) -> None:
        super().__init__()
        if mode not in self.valid_modes:
            raise ValueError(f"mode must be one of {sorted(self.valid_modes)}")
        if symmetry not in self.valid_symmetries:
            raise ValueError(f"symmetry must be one of {sorted(self.valid_symmetries)}")
        if base_qam.shape != (SYMBOL_COUNT, 2):
            raise ValueError("base_qam must have shape [256, 2].")

        self.mode = mode
        self.symmetry = symmetry
        self.target_va = float(target_va)
        self.input_dim = int(input_dim)
        self.hidden_dim = int(hidden_dim)
        self.logit_clip = None if logit_clip is None else float(logit_clip)

        self.distribution_net = nn.Sequential(
            nn.Linear(self.input_dim, self.hidden_dim, dtype=REAL_DTYPE),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, SYMBOL_COUNT, dtype=REAL_DTYPE),
        )
        train_probabilities = mode in {"ps", "joint"}
        for parameter in self.distribution_net.parameters():
            parameter.requires_grad_(train_probabilities)

        initial_probabilities = project_probabilities(probability_initialization, base_qam.device)
        final_layer = self.distribution_net[-1]
        if not isinstance(final_layer, nn.Linear):
            raise TypeError("The final distribution layer must be linear.")
        with torch.no_grad():
            final_layer.weight.zero_()
            final_layer.bias.copy_(torch.log(initial_probabilities.clamp_min(1e-12)))

        self.raw_constellation = nn.Parameter(
            base_qam.clone(),
            requires_grad=mode in {"gs", "joint"},
        )
        self.register_buffer("base_qam", base_qam.clone())
        self.register_buffer(
            "uniform_probabilities",
            torch.full((SYMBOL_COUNT,), 1.0 / SYMBOL_COUNT, dtype=REAL_DTYPE, device=base_qam.device),
        )

        source_indices: list[int] = []
        coordinate_signs: list[tuple[float, float]] = []
        central_sources: list[int] = []
        central_signs: list[float] = []
        for k in range(GRID_SIDE):
            for l in range(GRID_SIDE):
                qx = k - 8 if k >= 8 else 7 - k
                qy = l - 8 if l >= 8 else 7 - l
                source_indices.append((8 + qx) * GRID_SIDE + (8 + qy))
                coordinate_signs.append((1.0 if k >= 8 else -1.0, 1.0 if l >= 8 else -1.0))
                index = k * GRID_SIDE + l
                mirror = SYMBOL_COUNT - 1 - index
                central_sources.append(min(index, mirror))
                central_signs.append(1.0 if index <= mirror else -1.0)
        self.register_buffer(
            "fourfold_source_indices",
            torch.tensor(source_indices, dtype=torch.long, device=base_qam.device),
        )
        self.register_buffer(
            "fourfold_signs",
            torch.tensor(coordinate_signs, dtype=REAL_DTYPE, device=base_qam.device),
        )
        self.register_buffer(
            "central_source_indices",
            torch.tensor(central_sources, dtype=torch.long, device=base_qam.device),
        )
        self.register_buffer(
            "central_signs",
            torch.tensor(central_signs, dtype=REAL_DTYPE, device=base_qam.device),
        )

        initial_complex = complex_from_xy(base_qam)
        initial_normalized = normalize_unit_energy_batch(
            self.uniform_probabilities.unsqueeze(0),
            initial_complex,
        )[0]
        self.register_buffer("initial_qam_complex", initial_normalized)

    def channel_features(self, transmittance: torch.Tensor, epsilon: torch.Tensor) -> torch.Tensor:
        t_safe = transmittance.clamp_min(1e-12)
        sigma2 = 1.0 + transmittance * epsilon / 2.0
        snr = transmittance * self.target_va / sigma2
        return torch.stack(
            (
                torch.log10(t_safe),
                epsilon,
                10.0 * torch.log10(snr.clamp_min(1e-12)),
            ),
            dim=-1,
        )

    def effective_raw_constellation(self) -> torch.Tensor:
        raw = self.base_qam if self.mode == "ps" else self.raw_constellation
        if self.symmetry == "none":
            return raw
        if self.symmetry == "central":
            prototypes = raw[self.central_source_indices]
            return prototypes * self.central_signs.unsqueeze(-1)
        prototypes = raw[self.fourfold_source_indices].abs()
        return prototypes * self.fourfold_signs

    def forward(
        self,
        transmittance: torch.Tensor | float,
        epsilon: torch.Tensor | float,
        use_gumbel: bool = False,
        gumbel_temperature: float = 1.0,
    ) -> ModelOutput:
        device = self.base_qam.device
        transmittance_tensor = torch.as_tensor(
            transmittance,
            dtype=REAL_DTYPE,
            device=device,
        ).reshape(-1)
        epsilon_tensor = torch.as_tensor(epsilon, dtype=REAL_DTYPE, device=device)
        if epsilon_tensor.ndim == 0:
            epsilon_tensor = epsilon_tensor.expand_as(transmittance_tensor)
        else:
            epsilon_tensor = epsilon_tensor.reshape(-1)
        if epsilon_tensor.shape != transmittance_tensor.shape:
            raise ValueError("epsilon must be scalar or match transmittance.")

        features = self.channel_features(transmittance_tensor, epsilon_tensor)
        logits = self.distribution_net(features)
        if self.logit_clip is not None:
            logits = torch.clamp(logits, min=-self.logit_clip, max=self.logit_clip)
        if self.mode == "gs":
            probabilities = self.uniform_probabilities.unsqueeze(0).expand(transmittance_tensor.numel(), -1)
        else:
            probabilities = torch.softmax(logits, dim=-1)
        probabilities_safe = probabilities.clamp_min(1e-12)

        raw_complex = complex_from_xy(self.effective_raw_constellation())
        unit_constellation = normalize_unit_energy_batch(
            probabilities,
            raw_complex,
        )
        constellation = unit_constellation * math.sqrt(self.target_va / 2.0)
        gumbel_symbols = None
        if use_gumbel and self.mode in {"ps", "joint"}:
            gumbel_symbols = torch_functional.gumbel_softmax(
                logits,
                tau=float(gumbel_temperature),
                hard=True,
                dim=-1,
            )
        return ModelOutput(
            probabilities=probabilities,
            probabilities_safe=probabilities_safe,
            unit_constellation=unit_constellation,
            constellation=constellation,
            logits=logits,
            features=features,
            gumbel_symbols=gumbel_symbols,
        )


def annealed_gumbel_temperature(epoch: int, epochs: int, start: float, end: float) -> float:
    if epochs <= 1:
        return float(end)
    fraction = min(max((epoch - 1) / (epochs - 1), 0.0), 1.0)
    return float(start * (end / start) ** fraction)


def make_standard_complex_noise(
    batch_size: int,
    symbol_count: int,
    samples_per_symbol: int,
    generator: torch.Generator,
    device: torch.device,
    antithetic: bool = True,
) -> torch.Tensor:
    independent = (samples_per_symbol + 1) // 2 if antithetic else samples_per_symbol
    shape = (batch_size, symbol_count, independent)
    real = torch.randn(shape, dtype=REAL_DTYPE, device=device, generator=generator)
    imag = torch.randn(shape, dtype=REAL_DTYPE, device=device, generator=generator)
    noise = torch.complex(real, imag) / math.sqrt(2.0)
    if antithetic:
        noise = torch.cat((noise, -noise), dim=-1)[..., :samples_per_symbol]
    return noise


def discrete_mi_mismatched_awgn_batch(
    probabilities: torch.Tensor,
    constellation: torch.Tensor,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor | float,
    noise_samples_per_symbol: int,
    standard_noise: torch.Tensor,
    candidate_chunk_size: int = 64,
) -> torch.Tensor:
    """Exact symbol enumeration with AWGN-only Monte Carlo integration."""
    if probabilities.ndim != 2 or probabilities.shape[1] != SYMBOL_COUNT:
        raise ValueError("probabilities must have shape [B, 256].")
    if constellation.shape != probabilities.shape:
        raise ValueError("constellation must have shape [B, 256].")
    batch_size = probabilities.shape[0]
    if standard_noise.shape != (batch_size, SYMBOL_COUNT, noise_samples_per_symbol):
        raise ValueError("standard_noise has an incompatible shape.")
    if candidate_chunk_size <= 0:
        raise ValueError("candidate_chunk_size must be positive.")

    # Bound the candidate-distance working set. A full validation configuration
    # can otherwise materialize multi-gigabyte [B, M, K, candidate] tensors.
    candidates_per_chunk = min(candidate_chunk_size, SYMBOL_COUNT)
    elements_per_fading_state = (
        SYMBOL_COUNT * noise_samples_per_symbol * candidates_per_chunk
    )
    maximum_working_elements = 2_000_000
    maximum_fading_batch = max(1, maximum_working_elements // elements_per_fading_state)
    if batch_size > maximum_fading_batch:
        values: list[torch.Tensor] = []
        for start in range(0, batch_size, maximum_fading_batch):
            stop = min(start + maximum_fading_batch, batch_size)
            epsilon_chunk = epsilon
            if isinstance(epsilon, torch.Tensor) and epsilon.ndim > 0:
                epsilon_chunk = epsilon.reshape(-1)[start:stop]
            values.append(
                discrete_mi_mismatched_awgn_batch(
                    probabilities[start:stop],
                    constellation[start:stop],
                    transmittance[start:stop],
                    epsilon_chunk,
                    noise_samples_per_symbol,
                    standard_noise[start:stop],
                    candidate_chunk_size,
                )
            )
        return torch.cat(values, dim=0)

    transmittance = transmittance.reshape(-1)
    epsilon_tensor = torch.as_tensor(epsilon, dtype=REAL_DTYPE, device=probabilities.device)
    if epsilon_tensor.ndim == 0:
        epsilon_tensor = epsilon_tensor.expand_as(transmittance)
    else:
        epsilon_tensor = epsilon_tensor.reshape(-1)
    sigma2 = 1.0 + transmittance * epsilon_tensor / 2.0
    means = torch.sqrt(transmittance)[:, None] * constellation
    received = means[:, :, None] + standard_noise * torch.sqrt(sigma2)[:, None, None]
    log_probabilities = torch.log(probabilities.clamp_min(1e-12))
    entropy = -torch.sum(probabilities * log_probabilities, dim=-1) / LOG2

    log_denominator: torch.Tensor | None = None
    for start in range(0, SYMBOL_COUNT, candidate_chunk_size):
        stop = min(start + candidate_chunk_size, SYMBOL_COUNT)
        distances = (
            received[:, :, :, None] - means[:, None, None, start:stop]
        ).abs().square()
        logits = (
            log_probabilities[:, None, None, start:stop]
            - distances / sigma2[:, None, None, None]
        )
        chunk_value = torch.logsumexp(logits, dim=-1)
        log_denominator = (
            chunk_value
            if log_denominator is None
            else torch.logaddexp(log_denominator, chunk_value)
        )
    if log_denominator is None:
        raise RuntimeError("No candidate chunks were evaluated.")

    true_distances = (received - means[:, :, None]).abs().square()
    true_logits = log_probabilities[:, :, None] - true_distances / sigma2[:, None, None]
    correct_log_posterior = true_logits - log_denominator
    conditional_term = torch.sum(
        probabilities * torch.mean(correct_log_posterior, dim=-1),
        dim=-1,
    ) / LOG2
    return entropy + conditional_term


def coherent_state_matrix(constellation: torch.Tensor, ncut: int) -> torch.Tensor:
    number = torch.arange(ncut, dtype=REAL_DTYPE, device=constellation.device)
    inverse_sqrt_factorial = torch.exp(-0.5 * torch.lgamma(number + 1.0))
    powers = constellation.unsqueeze(-1) ** number.to(dtype=torch.int64)
    envelope = torch.exp(-0.5 * constellation.abs().square()).unsqueeze(-1)
    return envelope * powers * inverse_sqrt_factorial


def annihilation_operator(ncut: int, device: torch.device) -> torch.Tensor:
    operator = torch.zeros((ncut, ncut), dtype=COMPLEX_DTYPE, device=device)
    indices = torch.arange(1, ncut, device=device)
    operator[indices - 1, indices] = torch.sqrt(indices.to(dtype=REAL_DTYPE)).to(COMPLEX_DTYPE)
    return operator


def bosonic_entropy(x: torch.Tensor) -> torch.Tensor:
    nonnegative = torch.clamp(x, min=0.0)
    safe = nonnegative.clamp_min(1e-15)
    return (
        (nonnegative + 1.0) * torch.log2(nonnegative + 1.0)
        - nonnegative * torch.log2(safe)
    )


def differentiable_security_block(
    probabilities: torch.Tensor,
    constellation: torch.Tensor,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor | float,
    target_va: float,
    ncut: int,
    density_eigenvalue_floor: float = 1e-12,
    include_density_matrix: bool = True,
) -> SecurityOutput:
    """Recompute tau, Tr(C), w, Z, Gamma_AB, and chi_BE for each state."""
    batch_size = probabilities.shape[0]
    # Fock-space eigendecompositions create several [B, ncut, ncut] complex
    # temporaries. Stream independent fading states to cap their peak footprint.
    maximum_security_matrix_elements = 180_000
    maximum_fading_batch = max(1, maximum_security_matrix_elements // (ncut * ncut))
    if batch_size > maximum_fading_batch:
        chunks: list[SecurityOutput] = []
        for start in range(0, batch_size, maximum_fading_batch):
            stop = min(start + maximum_fading_batch, batch_size)
            epsilon_chunk = epsilon
            if isinstance(epsilon, torch.Tensor) and epsilon.ndim > 0:
                epsilon_chunk = epsilon.reshape(-1)[start:stop]
            chunks.append(
                differentiable_security_block(
                    probabilities[start:stop],
                    constellation[start:stop],
                    transmittance[start:stop],
                    epsilon_chunk,
                    target_va,
                    ncut,
                    density_eigenvalue_floor,
                    include_density_matrix,
                )
            )
        return SecurityOutput(
            tau=torch.cat([chunk.tau for chunk in chunks], dim=0),
            tau_eigenvalues=torch.cat(
                [chunk.tau_eigenvalues for chunk in chunks], dim=0
            ),
            tau_trace=torch.cat([chunk.tau_trace for chunk in chunks], dim=0),
            tr_c=torch.cat([chunk.tr_c for chunk in chunks], dim=0),
            w=torch.cat([chunk.w for chunk in chunks], dim=0),
            z_raw=torch.cat([chunk.z_raw for chunk in chunks], dim=0),
            z=torch.cat([chunk.z for chunk in chunks], dim=0),
            gamma_ab=torch.cat([chunk.gamma_ab for chunk in chunks], dim=0),
            lambda1=torch.cat([chunk.lambda1 for chunk in chunks], dim=0),
            lambda2=torch.cat([chunk.lambda2 for chunk in chunks], dim=0),
            lambda3=torch.cat([chunk.lambda3 for chunk in chunks], dim=0),
            chi_be=torch.cat([chunk.chi_be for chunk in chunks], dim=0),
        )

    fock = coherent_state_matrix(constellation, ncut)
    tau = torch.einsum("bmi,bm,bmj->bij", fock.conj(), probabilities, fock)
    tau = 0.5 * (tau + tau.mH)
    eigenvalues, eigenvectors = torch.linalg.eigh(tau)
    significant = eigenvalues > density_eigenvalue_floor
    safe_eigenvalues = eigenvalues.clamp_min(density_eigenvalue_floor)
    sqrt_values = torch.sqrt(safe_eigenvalues) * significant
    inverse_sqrt_values = torch.rsqrt(safe_eigenvalues) * significant
    tau_sqrt = (eigenvectors * sqrt_values.unsqueeze(-2)) @ eigenvectors.mH
    tau_inverse_sqrt = (eigenvectors * inverse_sqrt_values.unsqueeze(-2)) @ eigenvectors.mH

    a_operator = annihilation_operator(ncut, probabilities.device)
    a_batch = a_operator.unsqueeze(0).expand(probabilities.shape[0], -1, -1)
    c_operator = tau_sqrt @ a_batch @ tau_sqrt @ a_batch.mH
    tr_c = torch.diagonal(c_operator, dim1=-2, dim2=-1).sum(-1).real

    a_tau = tau_sqrt @ a_batch @ tau_inverse_sqrt
    first_moment_operator = a_tau.mH @ a_tau
    t1 = torch.einsum("bmi,bij,bmj->bm", fock.conj(), first_moment_operator, fock).real
    inner = torch.einsum("bmi,bij,bmj->bm", fock.conj(), a_tau, fock)
    t2 = inner.abs().square()
    w = torch.sum(probabilities * (t1 - t2), dim=-1)

    transmittance = transmittance.reshape(-1)
    epsilon_tensor = torch.as_tensor(epsilon, dtype=REAL_DTYPE, device=probabilities.device)
    if epsilon_tensor.ndim == 0:
        epsilon_tensor = epsilon_tensor.expand_as(transmittance)
    else:
        epsilon_tensor = epsilon_tensor.reshape(-1)
    z_raw = (
        2.0 * torch.sqrt(transmittance) * tr_c
        - torch.sqrt(torch.clamp(2.0 * transmittance * epsilon_tensor * w, min=0.0))
    )

    a_value = torch.full_like(transmittance, float(target_va) + 1.0)
    b_value = 1.0 + transmittance * float(target_va) + transmittance * epsilon_tensor
    z_max = torch.sqrt(a_value * b_value) * (1.0 - 1e-9)
    z_value = torch.minimum(z_raw, z_max)

    gamma = torch.zeros(
        (transmittance.numel(), 4, 4),
        dtype=REAL_DTYPE,
        device=probabilities.device,
    )
    gamma[:, 0, 0] = a_value
    gamma[:, 1, 1] = a_value
    gamma[:, 2, 2] = b_value
    gamma[:, 3, 3] = b_value
    gamma[:, 0, 2] = z_value
    gamma[:, 2, 0] = z_value
    gamma[:, 1, 3] = -z_value
    gamma[:, 3, 1] = -z_value

    delta = a_value.square() + b_value.square() - 2.0 * z_value.square()
    determinant = (a_value * b_value - z_value.square()).square()
    discriminant = torch.clamp(delta.square() - 4.0 * determinant, min=0.0)
    root_discriminant = torch.sqrt(discriminant)
    lambda1 = torch.sqrt(torch.clamp(0.5 * (delta + root_discriminant), min=0.0))
    lambda2 = torch.sqrt(torch.clamp(0.5 * (delta - root_discriminant), min=0.0))
    lambda3 = torch.clamp(
        a_value - z_value.square() / (2.0 + transmittance * target_va + transmittance * epsilon_tensor),
        min=1e-15,
    )
    chi_be = (
        bosonic_entropy((lambda1 - 1.0) / 2.0)
        + bosonic_entropy((lambda2 - 1.0) / 2.0)
        - bosonic_entropy((lambda3 - 1.0) / 2.0)
    )
    tau_trace = torch.diagonal(tau, dim1=-2, dim2=-1).sum(-1).real
    if not include_density_matrix:
        tau = tau.new_empty((batch_size, 0, 0))
        eigenvalues = eigenvalues.new_empty((batch_size, 0))
    return SecurityOutput(
        tau=tau,
        tau_eigenvalues=eigenvalues,
        tau_trace=tau_trace,
        tr_c=tr_c,
        w=w,
        z_raw=z_raw,
        z=z_value,
        gamma_ab=gamma,
        lambda1=lambda1,
        lambda2=lambda2,
        lambda3=lambda3,
        chi_be=chi_be,
    )


def shaping_loss(
    model: JointPSGS256QAM,
    output: ModelOutput,
    i_ab: torch.Tensor,
    security: SecurityOutput,
    beta: float,
    separation_scale: float,
    max_photon_number: float,
    entropy_floor: float,
    lambda_sep: float,
    lambda_peak: float,
    lambda_drift: float,
    lambda_entropy: float,
) -> LossOutput:
    raw_skr = float(beta) * i_ab - security.chi_be
    loss_skr = -torch.mean(raw_skr)
    points = torch.view_as_real(output.unit_constellation)
    pairwise_distance2 = torch.cdist(points, points).square()
    off_diagonal = ~torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=points.device)
    separation = torch.exp(-pairwise_distance2 / float(separation_scale) ** 2)[:, off_diagonal].mean()
    peak = torch.relu(output.unit_constellation.abs().square() - float(max_photon_number)).square().mean()
    drift = (
        output.unit_constellation - model.initial_qam_complex.unsqueeze(0)
    ).abs().square().mean()
    entropy_bits = -torch.sum(
        output.probabilities * torch.log2(output.probabilities_safe),
        dim=-1,
    )
    entropy = torch.relu(float(entropy_floor) - entropy_bits).square().mean()
    total = (
        loss_skr
        + float(lambda_sep) * separation
        + float(lambda_peak) * peak
        + float(lambda_drift) * drift
        + float(lambda_entropy) * entropy
    )
    return LossOutput(
        total=total,
        skr=loss_skr,
        separation=separation,
        peak=peak,
        drift=drift,
        entropy=entropy,
        raw_skr=raw_skr,
    )


def parameter_gradient_norm(parameters: Iterable[torch.Tensor]) -> float:
    squared = torch.zeros((), dtype=REAL_DTYPE)
    found = False
    for parameter in parameters:
        if parameter.grad is not None:
            found = True
            squared = squared + parameter.grad.detach().cpu().square().sum()
    return float(torch.sqrt(squared)) if found else 0.0


def model_output_for_baseline(
    kind: str,
    transmittance: torch.Tensor,
    base_qam: torch.Tensor,
    target_va: float,
) -> ModelOutput:
    probabilities_1d = project_probabilities(kind, transmittance.device)
    probabilities = probabilities_1d.unsqueeze(0).expand(transmittance.numel(), -1)
    raw_complex = complex_from_xy(base_qam)
    unit_constellation = normalize_unit_energy_batch(probabilities, raw_complex)
    constellation = unit_constellation * math.sqrt(float(target_va) / 2.0)
    logits = torch.log(probabilities.clamp_min(1e-12))
    return ModelOutput(
        probabilities=probabilities,
        probabilities_safe=probabilities.clamp_min(1e-12),
        unit_constellation=unit_constellation,
        constellation=constellation,
        logits=logits,
        features=torch.empty((transmittance.numel(), 0), dtype=REAL_DTYPE, device=transmittance.device),
        gumbel_symbols=None,
    )


def evaluate_output(
    name: str,
    output: ModelOutput,
    transmittance: torch.Tensor,
    epsilon: float,
    beta: float,
    ncut: int,
    noise_samples: int,
    standard_noise: torch.Tensor,
    candidate_chunk_size: int,
    target_va: float,
) -> SchemeEvaluation:
    i_ab = discrete_mi_mismatched_awgn_batch(
        output.probabilities,
        output.constellation,
        transmittance,
        epsilon,
        noise_samples,
        standard_noise,
        candidate_chunk_size,
    )
    security = differentiable_security_block(
        output.probabilities,
        output.constellation,
        transmittance,
        epsilon,
        target_va,
        ncut,
        include_density_matrix=False,
    )
    entropy = -torch.sum(
        output.probabilities * torch.log2(output.probabilities_safe),
        dim=-1,
    )
    raw_skr = float(beta) * i_ab - security.chi_be
    return SchemeEvaluation(
        name=name,
        transmittance=transmittance,
        probabilities=output.probabilities,
        unit_constellation=output.unit_constellation,
        constellation=output.constellation,
        entropy=entropy,
        i_ab=i_ab,
        security=security,
        raw_skr=raw_skr,
        reported_skr=torch.clamp(raw_skr, min=0.0),
    )


def evaluate_schemes(
    models: Mapping[str, JointPSGS256QAM],
    transmittance: torch.Tensor,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
    noise_seed: int,
    noise_samples: int | None = None,
    ncut: int | None = None,
    progress_label: str | None = None,
) -> dict[str, SchemeEvaluation]:
    evaluation_noise_samples = int(noise_samples or args.test_awgn_samples)
    evaluation_ncut = int(ncut or args.final_ncut)
    generator = tensor_generator(noise_seed, transmittance.device)
    standard_noise = make_standard_complex_noise(
        transmittance.numel(),
        SYMBOL_COUNT,
        evaluation_noise_samples,
        generator,
        transmittance.device,
    )
    evaluations: dict[str, SchemeEvaluation] = {}
    with torch.no_grad():
        outputs: dict[str, ModelOutput] = {
            "Uniform fixed QAM": model_output_for_baseline(
                "uniform", transmittance, base_qam, args.va
            ),
            "MB fixed QAM": model_output_for_baseline("mb", transmittance, base_qam, args.va),
        }
        display_names = {
            "ps": "Learned PS fixed QAM",
            "gs": "Learned GS uniform probabilities",
            "joint": "Learned joint PS+GS",
        }
        for stage, model in models.items():
            outputs[display_names[stage]] = model(transmittance, args.epsilon)
        for index, (name, output) in enumerate(outputs.items(), start=1):
            if progress_label is not None:
                print(
                    f"[{progress_label}] scheme {index}/{len(outputs)}: {name}",
                    flush=True,
                )
            evaluations[name] = evaluate_output(
                name,
                output,
                transmittance,
                args.epsilon,
                args.beta,
                evaluation_ncut,
                evaluation_noise_samples,
                standard_noise,
                args.candidate_chunk_size,
                args.va,
            )
    return evaluations


def _legacy_smoke_train_stage(
    stage: str,
    model: JointPSGS256QAM,
    transmittance: torch.Tensor,
    args: argparse.Namespace,
    output_dir: Path,
) -> tuple[JointPSGS256QAM, list[dict[str, Any]]]:
    """Deprecated one-pool trainer retained only for old checkpoint compatibility."""
    probability_parameters = [
        parameter for parameter in model.distribution_net.parameters() if parameter.requires_grad
    ]
    geometry_parameters = [model.raw_constellation] if model.raw_constellation.requires_grad else []
    groups: list[dict[str, Any]] = []
    if probability_parameters:
        groups.append({"params": probability_parameters, "lr": args.probability_lr})
    if geometry_parameters:
        groups.append({"params": geometry_parameters, "lr": args.constellation_lr})
    optimizer = torch.optim.Adam(groups)

    validation_t = transmittance[: min(args.validation_fading_samples, transmittance.numel())]
    validation_noise = make_standard_complex_noise(
        validation_t.numel(),
        SYMBOL_COUNT,
        args.validation_awgn_samples,
        tensor_generator(args.seed + 9000, transmittance.device),
        transmittance.device,
    )
    history: list[dict[str, Any]] = []
    best_score = -math.inf
    best_state = copy.deepcopy(model.state_dict())

    for epoch in range(1, args.epochs + 1):
        model.train()
        batch_generator = tensor_generator(args.seed + 1000 * (1 + len(stage)) + epoch, transmittance.device)
        if transmittance.numel() <= args.fading_batch_size:
            batch_indices = torch.arange(transmittance.numel(), device=transmittance.device)
        else:
            batch_indices = torch.randperm(
                transmittance.numel(),
                generator=batch_generator,
                device=transmittance.device,
            )[: args.fading_batch_size]
        batch_t = transmittance[batch_indices]
        standard_noise = make_standard_complex_noise(
            batch_t.numel(),
            SYMBOL_COUNT,
            args.awgn_samples,
            tensor_generator(args.seed + 100_000 + epoch + 1000 * len(stage), transmittance.device),
            transmittance.device,
        )
        temperature = annealed_gumbel_temperature(
            epoch,
            args.epochs,
            args.gumbel_temperature_start,
            args.gumbel_temperature_end,
        )
        output = model(
            batch_t,
            args.epsilon,
            use_gumbel=args.use_gumbel,
            gumbel_temperature=temperature,
        )
        i_ab = discrete_mi_mismatched_awgn_batch(
            output.probabilities,
            output.constellation,
            batch_t,
            args.epsilon,
            args.awgn_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        security = differentiable_security_block(
            output.probabilities,
            output.constellation,
            batch_t,
            args.epsilon,
            args.va,
            args.ncut,
        )
        losses = shaping_loss(
            model,
            output,
            i_ab,
            security,
            args.beta,
            args.separation_scale,
            args.max_photon_number,
            args.entropy_floor,
            args.lambda_sep,
            args.lambda_peak,
            args.lambda_drift,
            args.lambda_entropy,
        )
        optimizer.zero_grad(set_to_none=True)
        losses.total.backward()
        probability_gradient = parameter_gradient_norm(probability_parameters)
        geometry_gradient = parameter_gradient_norm(geometry_parameters)
        trainable_parameters = probability_parameters + geometry_parameters
        torch.nn.utils.clip_grad_norm_(trainable_parameters, max_norm=args.gradient_clip)
        optimizer.step()

        validate_now = (
            epoch == 1
            or epoch == args.epochs
            or epoch % args.validation_interval == 0
        )
        validation_score = math.nan
        if validate_now:
            model.eval()
            with torch.no_grad():
                validation_output = model(validation_t, args.epsilon)
                validation_iab = discrete_mi_mismatched_awgn_batch(
                    validation_output.probabilities,
                    validation_output.constellation,
                    validation_t,
                    args.epsilon,
                    args.validation_awgn_samples,
                    validation_noise,
                    args.candidate_chunk_size,
                )
                validation_security = differentiable_security_block(
                    validation_output.probabilities,
                    validation_output.constellation,
                    validation_t,
                    args.epsilon,
                    args.va,
                    args.ncut,
                )
                validation_raw_skr = args.beta * validation_iab - validation_security.chi_be
                validation_score = float(validation_raw_skr.mean())
            if validation_score > best_score:
                best_score = validation_score
                best_state = copy.deepcopy(model.state_dict())

        history.append(
            {
                "stage": stage,
                "epoch": epoch,
                "loss_total": float(losses.total.detach()),
                "loss_skr": float(losses.skr.detach()),
                "loss_separation": float(losses.separation.detach()),
                "loss_peak": float(losses.peak.detach()),
                "loss_drift": float(losses.drift.detach()),
                "loss_entropy": float(losses.entropy.detach()),
                "mean_i_ab": float(i_ab.detach().mean()),
                "mean_chi_be": float(security.chi_be.detach().mean()),
                "mean_raw_skr": float(losses.raw_skr.detach().mean()),
                "probability_gradient_norm": probability_gradient,
                "geometry_gradient_norm": geometry_gradient,
                "gumbel_temperature": temperature,
                "validation_raw_skr": validation_score,
            }
        )
        print(
            f"[{stage:5s}] epoch {epoch:4d}/{args.epochs} "
            f"loss={history[-1]['loss_total']:+.6e} "
            f"raw_SKR={history[-1]['mean_raw_skr']:+.6e} "
            f"grad_p={probability_gradient:.3e} grad_g={geometry_gradient:.3e}"
        )

    model.load_state_dict(best_state)
    torch.save(
        {
            "stage": stage,
            "model_state_dict": best_state,
            "best_validation_raw_skr": best_score,
            "architecture": {
                "input_dim": model.input_dim,
                "hidden_dim": model.hidden_dim,
                "symmetry": model.symmetry,
                "target_va": model.target_va,
            },
        },
        output_dir / f"best_{stage}.pt",
    )
    return model, history


def _legacy_create_stage_model(
    stage: str,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
    trained: Mapping[str, JointPSGS256QAM],
) -> JointPSGS256QAM:
    model = JointPSGS256QAM(
        base_qam=base_qam,
        mode=stage,
        symmetry=args.symmetry,
        target_va=args.va,
        hidden_dim=args.hidden_dim,
        probability_initialization=args.probability_initialization,
    ).to(base_qam.device)
    if stage == "joint":
        if "ps" in trained:
            model.distribution_net.load_state_dict(trained["ps"].distribution_net.state_dict())
        if "gs" in trained:
            with torch.no_grad():
                model.raw_constellation.copy_(trained["gs"].raw_constellation)
    return model


def _legacy_stage_sequence(mode: str) -> list[str]:
    if mode == "joint":
        return ["ps", "gs", "joint"]
    return [mode]


@dataclass(frozen=True)
class PhaseSpecification:
    name: str
    epochs: int
    train_probabilities: bool
    train_geometry: bool
    probability_lr: float
    geometry_lr: float
    ncut: int
    train_awgn_samples: int
    train_fading_samples: int
    regularization_start_factor: float
    regularization_end_factor: float


@dataclass
class BestCheckpoint:
    metrics: dict[str, float]
    model_state: dict[str, torch.Tensor]
    epoch: int
    phase: str
    path: Path


def capture_rng_states() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }


def restore_rng_states(states: Mapping[str, Any]) -> None:
    random.setstate(states["python"])
    np.random.set_state(states["numpy"])
    torch.set_rng_state(states["torch_cpu"])
    if torch.cuda.is_available() and states.get("torch_cuda") is not None:
        torch.cuda.set_rng_state_all(states["torch_cuda"])


def geometry_statistics(output: ModelOutput) -> dict[str, float]:
    probabilities = output.probabilities
    unit = output.unit_constellation
    weighted_mean = torch.sum(probabilities * unit, dim=-1)
    weighted_energy = torch.sum(probabilities * unit.abs().square(), dim=-1)
    symbol_energy = unit.abs().square()
    points = torch.view_as_real(unit)
    distances = torch.cdist(points, points)
    diagonal = torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=unit.device).unsqueeze(0)
    minimum_distance = distances.masked_fill(diagonal, math.inf).amin(dim=(-2, -1))
    maximum_distance = distances.amax(dim=(-2, -1))
    entropy = -torch.sum(probabilities * torch.log2(probabilities.clamp_min(1e-12)), dim=-1)
    return {
        "weighted_mean_abs": float(weighted_mean.abs().mean().detach()),
        "weighted_mean_energy": float(weighted_energy.mean().detach()),
        "maximum_symbol_energy": float(symbol_energy.max().detach()),
        "minimum_pairwise_distance": float(minimum_distance.mean().detach()),
        "maximum_pairwise_distance": float(maximum_distance.mean().detach()),
        "probability_entropy": float(entropy.mean().detach()),
        "minimum_probability": float(probabilities.min().detach()),
        "maximum_probability": float(probabilities.max().detach()),
    }


def validation_metrics(
    output: ModelOutput,
    i_ab: torch.Tensor,
    security: SecurityOutput,
    beta: float,
) -> dict[str, float]:
    raw_skr = float(beta) * i_ab - security.chi_be
    statistics = geometry_statistics(output)
    return {
        "raw_skr": float(raw_skr.mean()),
        "i_ab": float(i_ab.mean()),
        "chi_be": float(security.chi_be.mean()),
        "peak_energy": statistics["maximum_symbol_energy"],
        "minimum_pairwise_distance": statistics["minimum_pairwise_distance"],
        **statistics,
    }


def checkpoint_rank(metrics: Mapping[str, float]) -> tuple[float, float, float, float, float]:
    """Primary raw-SKR ranking followed by the required deterministic tie-breakers."""
    return (
        float(metrics["raw_skr"]),
        float(metrics["i_ab"]),
        -float(metrics["chi_be"]),
        -float(metrics["peak_energy"]),
        float(metrics["minimum_pairwise_distance"]),
    )


def checkpoint_is_better(
    candidate: Mapping[str, float],
    incumbent: Mapping[str, float] | None,
    tolerance: float = 1e-12,
) -> bool:
    if incumbent is None:
        return True
    candidate_rank = checkpoint_rank(candidate)
    incumbent_rank = checkpoint_rank(incumbent)
    for candidate_value, incumbent_value in zip(candidate_rank, incumbent_rank):
        if candidate_value > incumbent_value + tolerance:
            return True
        if candidate_value < incumbent_value - tolerance:
            return False
    return False


def configuration_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key, value in vars(args).items():
        snapshot[key] = str(value) if isinstance(value, Path) else value
    return snapshot


def save_training_checkpoint(
    path: Path,
    model: JointPSGS256QAM,
    optimizer: torch.optim.Optimizer | None,
    scheduler: Any,
    epoch: int,
    phase: str,
    args: argparse.Namespace,
    metrics: Mapping[str, float],
    reference_output: ModelOutput,
    elapsed_seconds: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 2,
        "model_mode": model.mode,
        "model_state_dict": copy.deepcopy(model.state_dict()),
        "optimizer_state_dict": None if optimizer is None else optimizer.state_dict(),
        "scheduler_state_dict": None if scheduler is None else scheduler.state_dict(),
        "epoch": int(epoch),
        "phase": phase,
        "configuration": configuration_snapshot(args),
        "rng_states": capture_rng_states(),
        "validation_metrics": dict(metrics),
        "constellation_coordinates": reference_output.constellation.detach().cpu(),
        "unit_constellation_coordinates": reference_output.unit_constellation.detach().cpu(),
        "symbol_probabilities": reference_output.probabilities.detach().cpu(),
        "normalization_statistics": geometry_statistics(reference_output),
        "elapsed_seconds": float(elapsed_seconds),
    }
    torch.save(payload, path)


def load_training_checkpoint(
    path: Path,
    model: JointPSGS256QAM,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any = None,
    restore_rng: bool = True,
) -> dict[str, Any]:
    payload = torch.load(path, map_location=model.base_qam.device, weights_only=False)
    model.load_state_dict(payload["model_state_dict"])
    if optimizer is not None and payload.get("optimizer_state_dict") is not None:
        optimizer.load_state_dict(payload["optimizer_state_dict"])
    if scheduler is not None and payload.get("scheduler_state_dict") is not None:
        scheduler.load_state_dict(payload["scheduler_state_dict"])
    if restore_rng and payload.get("rng_states") is not None:
        restore_rng_states(payload["rng_states"])
    return payload


def build_optimizer(
    model: JointPSGS256QAM,
    probability_lr: float,
    geometry_lr: float,
    optimizer_name: str,
    weight_decay: float,
) -> tuple[torch.optim.Optimizer, list[torch.Tensor], list[torch.Tensor]]:
    probability_parameters = list(model.distribution_net.parameters())
    geometry_parameters = [model.raw_constellation]
    for parameter in probability_parameters:
        parameter.requires_grad_(probability_lr > 0.0)
    model.raw_constellation.requires_grad_(geometry_lr > 0.0)
    groups: list[dict[str, Any]] = []
    if probability_lr > 0.0:
        groups.append({"params": probability_parameters, "lr": probability_lr, "name": "probability"})
    if geometry_lr > 0.0:
        groups.append({"params": geometry_parameters, "lr": geometry_lr, "name": "geometry"})
    if not groups:
        raise ValueError("At least one optimizer parameter group must have a positive learning rate.")
    optimizer_class = torch.optim.AdamW if optimizer_name == "adamw" else torch.optim.Adam
    optimizer = optimizer_class(groups, weight_decay=float(weight_decay))
    return optimizer, probability_parameters, geometry_parameters


def build_scheduler(
    optimizer: torch.optim.Optimizer,
    scheduler_name: str,
    epochs: int,
    patience: int,
) -> Any:
    if scheduler_name == "plateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=0.5,
            patience=max(1, patience // 4),
            min_lr=1e-8,
        )
    if scheduler_name == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=max(1, epochs),
            eta_min=1e-8,
        )
    return None


def evaluate_model_validation(
    model: JointPSGS256QAM,
    transmittance: torch.Tensor,
    standard_noise: torch.Tensor,
    args: argparse.Namespace,
    ncut: int,
    noise_samples: int,
) -> tuple[dict[str, float], ModelOutput]:
    model.eval()
    with torch.no_grad():
        output = model(transmittance, args.epsilon)
        i_ab = discrete_mi_mismatched_awgn_batch(
            output.probabilities,
            output.constellation,
            transmittance,
            args.epsilon,
            noise_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        security = differentiable_security_block(
            output.probabilities,
            output.constellation,
            transmittance,
            args.epsilon,
            args.va,
            ncut,
            include_density_matrix=False,
        )
    return validation_metrics(output, i_ab, security, args.beta), output


def scalar_gradient_norm(
    scalar: torch.Tensor,
    targets: torch.Tensor | Sequence[torch.Tensor],
    retain_graph: bool = True,
) -> float:
    target_list = [targets] if isinstance(targets, torch.Tensor) else list(targets)
    active_targets = [target for target in target_list if target.requires_grad]
    if not active_targets or not scalar.requires_grad:
        return 0.0
    gradients = torch.autograd.grad(
        scalar,
        active_targets,
        retain_graph=retain_graph,
        allow_unused=True,
    )
    norm2 = torch.zeros((), dtype=REAL_DTYPE, device=scalar.device)
    for gradient in gradients:
        if gradient is not None:
            norm2 = norm2 + gradient.abs().square().sum()
    return float(torch.sqrt(norm2).detach())


def gradient_diagnostics(
    model: JointPSGS256QAM,
    output: ModelOutput,
    security: SecurityOutput,
    losses: LossOutput,
) -> dict[str, float]:
    raw_skr = losses.raw_skr.mean()
    probability_parameters = list(model.distribution_net.parameters())
    geometry_parameters = [model.raw_constellation]
    return {
        "raw_skr_logit_gradient_norm": scalar_gradient_norm(raw_skr, output.logits),
        "raw_skr_probability_parameter_gradient_norm": scalar_gradient_norm(
            raw_skr, probability_parameters
        ),
        "raw_skr_geometry_gradient_norm": scalar_gradient_norm(raw_skr, geometry_parameters),
        "chi_be_logit_gradient_norm": scalar_gradient_norm(security.chi_be.mean(), output.logits),
        "chi_be_geometry_gradient_norm": scalar_gradient_norm(
            security.chi_be.mean(), geometry_parameters
        ),
        "separation_geometry_gradient_norm": scalar_gradient_norm(
            losses.separation, geometry_parameters
        ),
        "peak_geometry_gradient_norm": scalar_gradient_norm(losses.peak, geometry_parameters),
        "drift_geometry_gradient_norm": scalar_gradient_norm(losses.drift, geometry_parameters),
    }


def regularization_factor(specification: PhaseSpecification, epoch: int) -> float:
    if specification.epochs <= 1:
        return float(specification.regularization_end_factor)
    fraction = (epoch - 1) / (specification.epochs - 1)
    return float(
        specification.regularization_start_factor
        + fraction
        * (specification.regularization_end_factor - specification.regularization_start_factor)
    )


def phase_seed_offset(phase: str) -> int:
    offsets = {
        "ps": 10_000,
        "gs": 20_000,
        "geometry_warmup": 30_000,
        "joint_finetune": 40_000,
        "refinement": 50_000,
        "resume": 60_000,
    }
    return offsets.get(phase, 70_000)


def current_learning_rate(optimizer: torch.optim.Optimizer, group_name: str) -> float:
    for group in optimizer.param_groups:
        if group.get("name") == group_name:
            return float(group["lr"])
    return 0.0


def train_phase(
    model: JointPSGS256QAM,
    specification: PhaseSpecification,
    geometry: GeometryParams,
    channel_parameters: ChannelParams,
    validation_t: torch.Tensor,
    validation_noise: torch.Tensor,
    args: argparse.Namespace,
    output_dir: Path,
    best: BestCheckpoint | None = None,
    resume_checkpoint: Path | None = None,
) -> tuple[JointPSGS256QAM, list[dict[str, Any]], BestCheckpoint, float]:
    optimizer, probability_parameters, geometry_parameters = build_optimizer(
        model,
        specification.probability_lr if specification.train_probabilities else 0.0,
        specification.geometry_lr if specification.train_geometry else 0.0,
        args.optimizer,
        args.weight_decay,
    )
    scheduler = build_scheduler(
        optimizer,
        args.scheduler,
        specification.epochs,
        args.early_stopping_patience,
    )
    start_epoch = 1
    elapsed_before = 0.0
    if resume_checkpoint is not None:
        payload = load_training_checkpoint(resume_checkpoint, model, optimizer, scheduler)
        start_epoch = int(payload["epoch"]) + 1
        elapsed_before = float(payload.get("elapsed_seconds", 0.0))

    epoch_zero_metrics, epoch_zero_output = evaluate_model_validation(
        model,
        validation_t,
        validation_noise,
        args,
        args.validation_ncut,
        args.validation_awgn_samples,
    )
    checkpoint_directory = output_dir / "checkpoints"
    epoch_zero_path = checkpoint_directory / f"{specification.name}_epoch0.pt"
    save_training_checkpoint(
        epoch_zero_path,
        model,
        optimizer,
        scheduler,
        0,
        specification.name,
        args,
        epoch_zero_metrics,
        epoch_zero_output,
        elapsed_before,
    )
    if specification.name in {"ps", "gs"} and resume_checkpoint is None:
        save_training_checkpoint(
            output_dir / f"initial_untrained_{model.mode}.pt",
            model,
            optimizer,
            scheduler,
            0,
            specification.name,
            args,
            epoch_zero_metrics,
            epoch_zero_output,
            elapsed_before,
        )
    if best is None or checkpoint_is_better(epoch_zero_metrics, best.metrics):
        best = BestCheckpoint(
            metrics=dict(epoch_zero_metrics),
            model_state=copy.deepcopy(model.state_dict()),
            epoch=0,
            phase=specification.name,
            path=epoch_zero_path,
        )
    canonical_best_path = output_dir / (
        "best_joint.pt" if model.mode == "joint" else f"best_{model.mode}.pt"
    )
    if best.epoch == 0 and (
        best.phase == specification.name or not canonical_best_path.exists()
    ):
        save_training_checkpoint(
            canonical_best_path,
            model,
            optimizer,
            scheduler,
            0,
            best.phase,
            args,
            best.metrics,
            epoch_zero_output,
            elapsed_before,
        )
        best.path = canonical_best_path

    history: list[dict[str, Any]] = [
        {
            "stage": specification.name,
            "epoch": 0,
            "loss_total": math.nan,
            "loss_skr": -epoch_zero_metrics["raw_skr"],
            "mean_i_ab": epoch_zero_metrics["i_ab"],
            "mean_chi_be": epoch_zero_metrics["chi_be"],
            "mean_raw_skr": epoch_zero_metrics["raw_skr"],
            "validation_i_ab": epoch_zero_metrics["i_ab"],
            "validation_chi_be": epoch_zero_metrics["chi_be"],
            "validation_raw_skr": epoch_zero_metrics["raw_skr"],
            "validation_performed": True,
            **{f"geometry_{key}": value for key, value in geometry_statistics(epoch_zero_output).items()},
        }
    ]
    validation_checks_without_improvement = 0
    invalid_updates = 0
    last_valid_state = copy.deepcopy(model.state_dict())
    phase_start = time.perf_counter()

    for epoch in range(start_epoch, specification.epochs + 1):
        model.train()
        offset = phase_seed_offset(specification.name)
        training_channel = channel(
            geometry,
            channel_parameters,
            N=specification.train_fading_samples,
            rng=np.random.default_rng(args.seed + offset + epoch),
        )
        training_pool = torch.as_tensor(
            np.asarray(training_channel["T_samples"], dtype=np.float64),
            dtype=REAL_DTYPE,
            device=model.base_qam.device,
        )
        batch_generator = tensor_generator(args.seed + offset + 100_000 + epoch, training_pool.device)
        batch_size = min(args.fading_batch_size, training_pool.numel())
        batch_indices = torch.randperm(
            training_pool.numel(),
            generator=batch_generator,
            device=training_pool.device,
        )[:batch_size]
        batch_t = training_pool[batch_indices]
        standard_noise = make_standard_complex_noise(
            batch_t.numel(),
            SYMBOL_COUNT,
            specification.train_awgn_samples,
            tensor_generator(args.seed + offset + 200_000 + epoch, batch_t.device),
            batch_t.device,
        )
        output = model(batch_t, args.epsilon)
        i_ab = discrete_mi_mismatched_awgn_batch(
            output.probabilities,
            output.constellation,
            batch_t,
            args.epsilon,
            specification.train_awgn_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        security = differentiable_security_block(
            output.probabilities,
            output.constellation,
            batch_t,
            args.epsilon,
            args.va,
            specification.ncut,
        )
        reg_factor = 0.0 if args.disable_geometry_regularization else regularization_factor(
            specification, epoch
        )
        lambda_sep = args.lambda_sep * reg_factor
        lambda_peak = args.lambda_peak * reg_factor
        lambda_drift = args.lambda_drift * reg_factor
        losses = shaping_loss(
            model,
            output,
            i_ab,
            security,
            args.beta,
            args.separation_scale,
            args.max_photon_number,
            args.entropy_floor,
            lambda_sep,
            lambda_peak,
            lambda_drift,
            args.lambda_entropy,
        )
        diagnostics = (
            gradient_diagnostics(model, output, security, losses)
            if epoch == 1 or epoch % args.gradient_diagnostics_interval == 0
            else {}
        )
        optimizer.zero_grad(set_to_none=True)
        losses.total.backward()

        probability_gradient = parameter_gradient_norm(probability_parameters)
        geometry_gradient = parameter_gradient_norm(geometry_parameters)
        if args.update_strategy == "alternating" and model.mode == "joint":
            geometry_turn = epoch % (args.alternating_ps_steps + 1) == 0
            parameters_to_clear = probability_parameters if geometry_turn else geometry_parameters
            for parameter in parameters_to_clear:
                parameter.grad = None
        active_parameters = [
            parameter
            for parameter in probability_parameters + geometry_parameters
            if parameter.requires_grad and parameter.grad is not None
        ]
        security_is_valid = (
            bool(torch.all(torch.isfinite(security.gamma_ab)))
            and bool(torch.all(torch.isfinite(security.chi_be)))
            and bool(torch.all(security.tau_eigenvalues >= -1e-9))
            and bool(torch.all(security.w >= -1e-8))
            and bool(torch.all(security.lambda1 >= 1.0 - 1e-6))
            and bool(torch.all(security.lambda2 >= 1.0 - 1e-6))
            and bool(torch.all(security.lambda3 >= 1.0 - 1e-6))
        )
        finite_before_step = (
            bool(torch.isfinite(losses.total))
            and security_is_valid
            and all(bool(torch.all(torch.isfinite(parameter.grad))) for parameter in active_parameters)
        )
        if finite_before_step:
            torch.nn.utils.clip_grad_norm_(active_parameters, max_norm=args.gradient_clip)
            last_valid_state = copy.deepcopy(model.state_dict())
            optimizer.step()

        with torch.no_grad():
            post_output = model(batch_t, args.epsilon)
            post_statistics = geometry_statistics(post_output)
        valid_after_step = (
            finite_before_step
            and all(math.isfinite(value) for value in post_statistics.values())
            and post_statistics["weighted_mean_energy"] > 0.999999
            and post_statistics["weighted_mean_energy"] < 1.000001
            and post_statistics["minimum_pairwise_distance"] > args.minimum_pairwise_distance
            and post_statistics["probability_entropy"] > args.minimum_probability_entropy
            and post_statistics["maximum_symbol_energy"] < args.maximum_allowed_symbol_energy
        )
        if not valid_after_step:
            invalid_updates += 1
            model.load_state_dict(last_valid_state)
            for group in optimizer.param_groups:
                group["lr"] = max(float(group["lr"]) * 0.5, 1e-8)
            if invalid_updates > args.maximum_invalid_updates:
                raise RuntimeError(
                    f"{specification.name}: too many invalid updates; last valid model restored."
                )

        validate_now = (
            epoch == specification.epochs
            or epoch % args.validation_interval == 0
            or not valid_after_step
        )
        validation_values: dict[str, float] | None = None
        if validate_now:
            validation_values, validation_output = evaluate_model_validation(
                model,
                validation_t,
                validation_noise,
                args,
                args.validation_ncut,
                args.validation_awgn_samples,
            )
            if checkpoint_is_better(validation_values, best.metrics):
                best_path = output_dir / (
                    "best_joint.pt" if model.mode == "joint" else f"best_{model.mode}.pt"
                )
                save_training_checkpoint(
                    best_path,
                    model,
                    optimizer,
                    scheduler,
                    epoch,
                    specification.name,
                    args,
                    validation_values,
                    validation_output,
                    elapsed_before + time.perf_counter() - phase_start,
                )
                best = BestCheckpoint(
                    metrics=dict(validation_values),
                    model_state=copy.deepcopy(model.state_dict()),
                    epoch=epoch,
                    phase=specification.name,
                    path=best_path,
                )
                validation_checks_without_improvement = 0
            else:
                validation_checks_without_improvement += 1
            if scheduler is not None and args.scheduler == "plateau":
                scheduler.step(validation_values["raw_skr"])
        if scheduler is not None and args.scheduler == "cosine":
            scheduler.step()

        statistics = geometry_statistics(output)
        row = {
            "stage": specification.name,
            "epoch": epoch,
            "loss_total": float(losses.total.detach()),
            "loss_skr": float(losses.skr.detach()),
            "loss_separation": float(losses.separation.detach()),
            "loss_peak": float(losses.peak.detach()),
            "loss_drift": float(losses.drift.detach()),
            "loss_entropy": float(losses.entropy.detach()),
            "weighted_separation": lambda_sep * float(losses.separation.detach()),
            "weighted_peak": lambda_peak * float(losses.peak.detach()),
            "weighted_drift": lambda_drift * float(losses.drift.detach()),
            "weighted_entropy": args.lambda_entropy * float(losses.entropy.detach()),
            "lambda_separation": lambda_sep,
            "lambda_peak": lambda_peak,
            "lambda_drift": lambda_drift,
            "lambda_entropy": args.lambda_entropy,
            "mean_i_ab": float(i_ab.detach().mean()),
            "mean_chi_be": float(security.chi_be.detach().mean()),
            "mean_raw_skr": float(losses.raw_skr.detach().mean()),
            "probability_gradient_norm": probability_gradient,
            "geometry_gradient_norm": geometry_gradient,
            "probability_learning_rate": current_learning_rate(optimizer, "probability"),
            "geometry_learning_rate": current_learning_rate(optimizer, "geometry"),
            "validation_i_ab": math.nan if validation_values is None else validation_values["i_ab"],
            "validation_chi_be": math.nan if validation_values is None else validation_values["chi_be"],
            "validation_raw_skr": math.nan if validation_values is None else validation_values["raw_skr"],
            "validation_performed": validation_values is not None,
            "invalid_update": not valid_after_step,
            **diagnostics,
            **{f"geometry_{key}": value for key, value in statistics.items()},
        }
        history.append(row)
        validation_text = (
            f"{validation_values['raw_skr']:+.6e}"
            if validation_values is not None
            else "skipped"
        )
        print(
            f"[{specification.name:18s}] epoch {epoch:4d}/{specification.epochs} "
            f"raw_K={row['mean_raw_skr']:+.6e} "
            f"val_K={validation_text:>13s} "
            f"grad_p={probability_gradient:.3e} grad_g={geometry_gradient:.3e}"
        )

        with torch.no_grad():
            last_valid_output = model(batch_t, args.epsilon)
        save_training_checkpoint(
            checkpoint_directory / f"last_valid_{model.mode}.pt",
            model,
            optimizer,
            scheduler,
            epoch,
            specification.name,
            args,
            validation_values or best.metrics,
            last_valid_output,
            elapsed_before + time.perf_counter() - phase_start,
        )
        if (
            epoch < specification.epochs
            and validate_now
            and validation_checks_without_improvement >= args.early_stopping_patience
        ):
            print(f"[{specification.name}] early stopping after {validation_checks_without_improvement} checks")
            break

    elapsed = elapsed_before + time.perf_counter() - phase_start
    model.load_state_dict(best.model_state)
    final_metrics, final_output = evaluate_model_validation(
        model,
        validation_t,
        validation_noise,
        args,
        args.validation_ncut,
        args.validation_awgn_samples,
    )
    final_path = output_dir / (
        "final_joint.pt" if model.mode == "joint" else f"final_{model.mode}.pt"
    )
    best_payload = torch.load(best.path, map_location=model.base_qam.device, weights_only=False)
    best_payload["checkpoint_role"] = "final_model_selected_by_validation_raw_skr"
    best_payload["pipeline_elapsed_seconds"] = elapsed
    best_payload["validation_metrics_recomputed"] = final_metrics
    torch.save(best_payload, final_path)
    if best.epoch == 0 and not best.path.name.startswith("best_"):
        best_path = output_dir / (
            "best_joint.pt" if model.mode == "joint" else f"best_{model.mode}.pt"
        )
        save_training_checkpoint(
            best_path,
            model,
            optimizer,
            scheduler,
            0,
            best.phase,
            args,
            best.metrics,
            final_output,
            elapsed,
        )
        best.path = best_path
    return model, history, best, elapsed


def create_model(
    mode: str,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
    probability_initialization: str | None = None,
) -> JointPSGS256QAM:
    return JointPSGS256QAM(
        base_qam=base_qam,
        mode=mode,
        symmetry=args.symmetry,
        target_va=args.va,
        hidden_dim=args.hidden_dim,
        probability_initialization=probability_initialization or args.probability_initialization,
        logit_clip=args.logit_clip,
    ).to(base_qam.device)


def initialize_joint_candidate(
    initialization: str,
    ps_model: JointPSGS256QAM,
    gs_model: JointPSGS256QAM,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
) -> JointPSGS256QAM:
    probability_initialization = "uniform" if initialization == "gs" else args.probability_initialization
    model = create_model("joint", base_qam, args, probability_initialization)
    if initialization in {"ps", "combined", "ps_preserving"}:
        model.distribution_net.load_state_dict(ps_model.distribution_net.state_dict())
    if initialization in {"combined", "gs"}:
        with torch.no_grad():
            model.raw_constellation.copy_(gs_model.raw_constellation)
    elif initialization in {"ps", "ps_preserving"}:
        with torch.no_grad():
            model.raw_constellation.copy_(ps_model.raw_constellation)
    return model


def ps_preserving_metrics_match(
    ps_model: JointPSGS256QAM,
    joint_model: JointPSGS256QAM,
    transmittance: torch.Tensor,
    standard_noise: torch.Tensor,
    args: argparse.Namespace,
    atol: float = 1e-11,
) -> bool:
    with torch.no_grad():
        ps_output = ps_model(transmittance, args.epsilon)
        joint_output = joint_model(transmittance, args.epsilon)
        if not torch.allclose(ps_output.probabilities, joint_output.probabilities, atol=atol, rtol=0.0):
            return False
        if not torch.allclose(ps_output.constellation, joint_output.constellation, atol=atol, rtol=0.0):
            return False
        ps_iab = discrete_mi_mismatched_awgn_batch(
            ps_output.probabilities,
            ps_output.constellation,
            transmittance,
            args.epsilon,
            args.validation_awgn_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        joint_iab = discrete_mi_mismatched_awgn_batch(
            joint_output.probabilities,
            joint_output.constellation,
            transmittance,
            args.epsilon,
            args.validation_awgn_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        ps_security = differentiable_security_block(
            ps_output.probabilities,
            ps_output.constellation,
            transmittance,
            args.epsilon,
            args.va,
            args.validation_ncut,
        )
        joint_security = differentiable_security_block(
            joint_output.probabilities,
            joint_output.constellation,
            transmittance,
            args.epsilon,
            args.va,
            args.validation_ncut,
        )
        return bool(
            torch.allclose(ps_iab, joint_iab, atol=atol, rtol=0.0)
            and torch.allclose(ps_security.chi_be, joint_security.chi_be, atol=atol, rtol=0.0)
        )


def evaluate_joint_initializations(
    ps_model: JointPSGS256QAM,
    gs_model: JointPSGS256QAM,
    base_qam: torch.Tensor,
    validation_t: torch.Tensor,
    validation_noise: torch.Tensor,
    args: argparse.Namespace,
    output_dir: Path,
) -> tuple[JointPSGS256QAM, list[dict[str, Any]], BestCheckpoint]:
    candidates = ("ps", "gs", "combined", "ps_preserving")
    rows: list[dict[str, Any]] = []
    candidate_models: dict[str, JointPSGS256QAM] = {}
    best_name: str | None = None
    best_metrics: dict[str, float] | None = None
    for initialization in candidates:
        model = initialize_joint_candidate(initialization, ps_model, gs_model, base_qam, args)
        metrics, output = evaluate_model_validation(
            model,
            validation_t,
            validation_noise,
            args,
            args.validation_ncut,
            args.validation_awgn_samples,
        )
        path = output_dir / "checkpoints" / f"joint_epoch0_{initialization}.pt"
        candidate_optimizer, _, _ = build_optimizer(
            model,
            args.probability_lr,
            args.constellation_lr,
            args.optimizer,
            args.weight_decay,
        )
        candidate_scheduler = build_scheduler(
            candidate_optimizer,
            args.scheduler,
            max(1, args.geometry_warmup_epochs),
            args.early_stopping_patience,
        )
        save_training_checkpoint(
            path,
            model,
            candidate_optimizer,
            candidate_scheduler,
            0,
            f"joint_init_{initialization}",
            args,
            metrics,
            output,
            0.0,
        )
        rows.append({"initialization": initialization, **metrics, "checkpoint": str(path)})
        candidate_models[initialization] = model
        if checkpoint_is_better(metrics, best_metrics):
            best_name = initialization
            best_metrics = metrics
    preserving = candidate_models["ps_preserving"]
    if not ps_preserving_metrics_match(
        ps_model,
        preserving,
        validation_t,
        validation_noise,
        args,
    ):
        raise AssertionError("PS-preserving joint epoch zero does not reproduce PS metrics.")
    selected_name = best_name if args.joint_initialization == "auto" else args.joint_initialization
    if selected_name is None or best_metrics is None:
        raise RuntimeError("No valid joint initialization was found.")
    selected = candidate_models[selected_name]
    selected_row = next(row for row in rows if row["initialization"] == selected_name)
    selected_metrics = {key: float(selected_row[key]) for key in best_metrics}
    selected_path = output_dir / "checkpoints" / f"joint_epoch0_{selected_name}.pt"
    best = BestCheckpoint(
        metrics=selected_metrics,
        model_state=copy.deepcopy(selected.state_dict()),
        epoch=0,
        phase=f"joint_init_{selected_name}",
        path=selected_path,
    )
    for row in rows:
        row["selected"] = row["initialization"] == selected_name
    return selected, rows, best


def summarize_evaluations(
    evaluations: Mapping[str, SchemeEvaluation],
    models: Mapping[str, JointPSGS256QAM] | None = None,
    training_times: Mapping[str, float] | None = None,
    beta: float = QAM_BETA,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model_name_to_key = {
        "Learned PS fixed QAM": "ps",
        "Learned GS uniform probabilities": "gs",
        "Learned joint PS+GS": "joint",
    }
    for name, evaluation in evaluations.items():
        raw = evaluation.raw_skr.detach().cpu().numpy()
        unit = evaluation.unit_constellation
        energy = torch.sum(evaluation.probabilities * unit.abs().square(), dim=-1)
        distances = torch.cdist(torch.view_as_real(unit), torch.view_as_real(unit))
        diagonal = torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=unit.device).unsqueeze(0)
        minimum_distance = distances.masked_fill(diagonal, math.inf).amin(dim=(-2, -1))
        model_key = model_name_to_key.get(name)
        model = None if models is None or model_key is None else models.get(model_key)
        rows.append(
            {
                "Model": name,
                "H_X": float(evaluation.entropy.mean()),
                "I_AB_discrete": float(evaluation.i_ab.mean()),
                "chi_BE": float(evaluation.security.chi_be.mean()),
                "beta_times_I_AB": float(beta * evaluation.i_ab.mean()),
                "raw_SKR": float(evaluation.raw_skr.mean()),
                "clipped_SKR": float(evaluation.reported_skr.mean()),
                "w": float(evaluation.security.w.mean()),
                "Z": float(evaluation.security.z.mean()),
                "Tr_C": float(evaluation.security.tr_c.mean()),
                "mean_transmittance": float(evaluation.transmittance.mean()),
                "SKR_outage_probability": float(np.mean(raw <= 0.0)),
                "average_energy": float(energy.mean()),
                "peak_energy": float(unit.abs().square().max()),
                "minimum_pairwise_distance": float(minimum_distance.mean()),
                "trainable_parameters": 0
                if model is None
                else int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)),
                "training_time_seconds": 0.0
                if training_times is None or model_key is None
                else float(training_times.get(model_key, 0.0)),
            }
        )
    ps_row = next((row for row in rows if row["Model"] == "Learned PS fixed QAM"), None)
    for row in rows:
        row["Delta_I_AB_vs_PS"] = math.nan if ps_row is None else (
            float(row["I_AB_discrete"]) - float(ps_row["I_AB_discrete"])
        )
        row["Delta_chi_BE_vs_PS"] = math.nan if ps_row is None else (
            float(row["chi_BE"]) - float(ps_row["chi_BE"])
        )
        row["Delta_raw_K_vs_PS"] = math.nan if ps_row is None else (
            float(row["raw_SKR"]) - float(ps_row["raw_SKR"])
        )
    return rows


def channel_transmittance_samples(
    geometry: GeometryParams,
    channel_parameters: ChannelParams,
    count: int,
    seed: int,
    device: torch.device,
) -> tuple[torch.Tensor, dict[str, Any]]:
    data = channel(
        geometry,
        channel_parameters,
        N=max(1, int(count)),
        rng=np.random.default_rng(int(seed)),
    )
    samples = torch.as_tensor(
        np.asarray(data["T_samples"], dtype=np.float64),
        dtype=REAL_DTYPE,
        device=device,
    )
    return samples, data


def independent_channel_splits(
    geometry: GeometryParams,
    channel_parameters: ChannelParams,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict[str, Any]]:
    train_t, train_data = channel_transmittance_samples(
        geometry,
        channel_parameters,
        args.train_fading_samples,
        args.seed + 101,
        device,
    )
    validation_t, validation_data = channel_transmittance_samples(
        geometry,
        channel_parameters,
        args.validation_fading_samples,
        args.seed + 202,
        device,
    )
    test_t, test_data = channel_transmittance_samples(
        geometry,
        channel_parameters,
        args.test_fading_samples,
        args.seed + 303,
        device,
    )
    if torch.equal(train_t, validation_t) or torch.equal(validation_t, test_t) or torch.equal(train_t, test_t):
        raise AssertionError("Train, validation, and test channel samples must be independent.")
    return train_t, validation_t, test_t, {
        "train": train_data,
        "validation": validation_data,
        "test": test_data,
    }


def evaluate_uncertainty(
    models: Mapping[str, JointPSGS256QAM],
    base_qam: torch.Tensor,
    geometry: GeometryParams,
    channel_parameters: ChannelParams,
    args: argparse.Namespace,
) -> tuple[dict[str, SchemeEvaluation], list[dict[str, Any]], list[dict[str, Any]]]:
    run_rows: list[dict[str, Any]] = []
    representative: dict[str, SchemeEvaluation] | None = None
    for run in range(args.uncertainty_runs):
        run_start = time.perf_counter()
        progress_label = f"evaluation run {run + 1}/{args.uncertainty_runs}"
        print(f"[{progress_label}] preparing independent channel and AWGN samples", flush=True)
        test_t, _ = channel_transmittance_samples(
            geometry,
            channel_parameters,
            args.test_fading_samples,
            args.seed + 100_000 + 1000 * run,
            base_qam.device,
        )
        evaluations = evaluate_schemes(
            models,
            test_t,
            base_qam,
            args,
            noise_seed=args.seed + 200_000 + 1000 * run,
            noise_samples=args.test_awgn_samples,
            ncut=args.final_ncut,
            progress_label=progress_label,
        )
        if representative is None:
            representative = evaluations
        for name, evaluation in evaluations.items():
            run_rows.append(
                {
                    "run": run,
                    "seed_channel": args.seed + 100_000 + 1000 * run,
                    "seed_awgn": args.seed + 200_000 + 1000 * run,
                    "Model": name,
                    "I_AB": float(evaluation.i_ab.mean()),
                    "chi_BE": float(evaluation.security.chi_be.mean()),
                    "raw_K": float(evaluation.raw_skr.mean()),
                }
            )
        print(
            f"[{progress_label}] completed in {time.perf_counter() - run_start:.1f} s",
            flush=True,
        )
    if representative is None:
        raise RuntimeError("At least one uncertainty run is required.")

    summary_rows: list[dict[str, Any]] = []
    ps_by_run = {
        int(row["run"]): row
        for row in run_rows
        if row["Model"] == "Learned PS fixed QAM"
    }
    for name in representative:
        model_rows = [row for row in run_rows if row["Model"] == name]
        summary: dict[str, Any] = {"Model": name, "runs": len(model_rows)}
        for metric in ("I_AB", "chi_BE", "raw_K"):
            values = np.asarray([row[metric] for row in model_rows], dtype=np.float64)
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if values.size > 1 else 0.0
            half_width = 1.96 * std / math.sqrt(values.size) if values.size > 1 else 0.0
            summary[f"{metric}_mean"] = mean
            summary[f"{metric}_std"] = std
            summary[f"{metric}_ci95_low"] = mean - half_width
            summary[f"{metric}_ci95_high"] = mean + half_width
            if ps_by_run:
                delta_values = np.asarray(
                    [
                        float(row[metric]) - float(ps_by_run[int(row["run"])][metric])
                        for row in model_rows
                    ],
                    dtype=np.float64,
                )
                delta_mean = float(delta_values.mean())
                delta_std = float(delta_values.std(ddof=1)) if delta_values.size > 1 else 0.0
                delta_half_width = (
                    1.96 * delta_std / math.sqrt(delta_values.size)
                    if delta_values.size > 1
                    else 0.0
                )
                summary[f"Delta_{metric}_vs_PS_mean"] = delta_mean
                summary[f"Delta_{metric}_vs_PS_std"] = delta_std
                summary[f"Delta_{metric}_vs_PS_ci95_low"] = delta_mean - delta_half_width
                summary[f"Delta_{metric}_vs_PS_ci95_high"] = delta_mean + delta_half_width
        summary_rows.append(summary)
    return representative, run_rows, summary_rows


def evaluate_ncut_convergence(
    models: Mapping[str, JointPSGS256QAM],
    base_qam: torch.Tensor,
    test_t: torch.Tensor,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    test_t = test_t[: min(args.ncut_check_fading_samples, test_t.numel())]
    cutoffs = sorted(set((int(args.ncut_check), int(args.final_ncut))))
    rows: list[dict[str, Any]] = []
    for cutoff in cutoffs:
        evaluations = evaluate_schemes(
            models,
            test_t,
            base_qam,
            args,
            noise_seed=args.seed + 300_000,
            noise_samples=args.ncut_check_awgn_samples,
            ncut=cutoff,
        )
        for name, evaluation in evaluations.items():
            rows.append(
                {
                    "ncut": cutoff,
                    "Model": name,
                    "I_AB": float(evaluation.i_ab.mean()),
                    "chi_BE": float(evaluation.security.chi_be.mean()),
                    "raw_K": float(evaluation.raw_skr.mean()),
                }
            )
    final_by_name = {
        row["Model"]: row for row in rows if int(row["ncut"]) == int(args.final_ncut)
    }
    for row in rows:
        reference = final_by_name[row["Model"]]
        row["abs_delta_I_AB_vs_final"] = abs(float(row["I_AB"]) - float(reference["I_AB"]))
        row["abs_delta_chi_BE_vs_final"] = abs(float(row["chi_BE"]) - float(reference["chi_BE"]))
        row["abs_delta_raw_K_vs_final"] = abs(float(row["raw_K"]) - float(reference["raw_K"]))
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str] | None = None) -> None:
    if not rows:
        return
    if fields is not None:
        fieldnames = list(fields)
    else:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_learned_tables(
    output_dir: Path,
    evaluations: Mapping[str, SchemeEvaluation],
) -> None:
    probability_rows: list[dict[str, Any]] = []
    constellation_rows: list[dict[str, Any]] = []
    for name, evaluation in evaluations.items():
        if not name.startswith("Learned"):
            continue
        probabilities = evaluation.probabilities.detach().cpu().numpy()
        constellation = evaluation.constellation.detach().cpu().numpy()
        transmittance = evaluation.transmittance.detach().cpu().numpy()
        for sample_index in range(probabilities.shape[0]):
            for symbol_index in range(SYMBOL_COUNT):
                probability_rows.append(
                    {
                        "scheme": name,
                        "sample_index": sample_index,
                        "T": transmittance[sample_index],
                        "symbol_index": symbol_index,
                        "k": symbol_index // GRID_SIDE,
                        "l": symbol_index % GRID_SIDE,
                        "probability": probabilities[sample_index, symbol_index],
                    }
                )
                point = constellation[sample_index, symbol_index]
                constellation_rows.append(
                    {
                        "scheme": name,
                        "sample_index": sample_index,
                        "T": transmittance[sample_index],
                        "symbol_index": symbol_index,
                        "k": symbol_index // GRID_SIDE,
                        "l": symbol_index % GRID_SIDE,
                        "x": point.real,
                        "y": point.imag,
                    }
                )
    write_csv(output_dir / "learned_probabilities.csv", probability_rows)
    write_csv(output_dir / "learned_constellation.csv", constellation_rows)


def style_axis(axis: plt.Axes) -> None:
    axis.grid(alpha=0.25, linewidth=0.7)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)


def plot_training_history(path: Path, history: Sequence[Mapping[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.5))
    colors = {
        "ps": "#d95f02",
        "gs": "#1b9e77",
        "geometry_warmup": "#7570b3",
        "joint_finetune": "#2c4c7c",
        "refinement": "#b23a48",
        "resume": "#6a4c93",
    }
    for stage in colors:
        stage_rows = [row for row in history if row["stage"] == stage]
        if stage_rows:
            axis.plot(
                [row["epoch"] for row in stage_rows],
                [row["loss_total"] for row in stage_rows],
                marker="o",
                color=colors[stage],
                label=stage.replace("_", " ").upper(),
            )
    axis.set_title("Raw-SKR shaping objective")
    axis.set_xlabel("Epoch")
    axis.set_ylabel("Total loss")
    axis.legend()
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_training_metric_curves(
    path: Path,
    history: Sequence[Mapping[str, Any]],
) -> None:
    metrics = (
        ("mean_raw_skr", "validation_raw_skr", "Raw K"),
        ("mean_i_ab", "validation_i_ab", "I_AB"),
        ("mean_chi_be", "validation_chi_be", "chi_BE"),
    )
    figure, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=False)
    colors = {
        "ps": "#d95f02",
        "gs": "#1b9e77",
        "geometry_warmup": "#7570b3",
        "joint_finetune": "#2c4c7c",
        "refinement": "#b23a48",
        "resume": "#6a4c93",
    }
    for axis, (train_key, validation_key, label) in zip(axes, metrics):
        offset = 0
        for stage in colors:
            rows = [row for row in history if row["stage"] == stage]
            if not rows:
                continue
            x = np.arange(offset, offset + len(rows))
            train_values = np.asarray([float(row.get(train_key, math.nan)) for row in rows])
            validation_values = np.asarray(
                [float(row.get(validation_key, math.nan)) for row in rows]
            )
            axis.plot(x, train_values, color=colors[stage], alpha=0.65, label=f"{stage} train")
            valid = np.isfinite(validation_values)
            axis.scatter(
                x[valid],
                validation_values[valid],
                color=colors[stage],
                marker="o",
                s=25,
                label=f"{stage} validation",
            )
            offset += len(rows)
        axis.set_ylabel(label)
        style_axis(axis)
    axes[0].axhline(0.0, color="#8b1e3f", linewidth=1.0)
    axes[-1].set_xlabel("Sequential logged epoch")
    axes[0].legend(fontsize=7, ncol=2)
    figure.suptitle("Training and fixed-validation metrics")
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_regularization_history(path: Path, history: Sequence[Mapping[str, Any]]) -> None:
    rows = [row for row in history if int(row.get("epoch", 0)) > 0]
    figure, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    if rows:
        x = np.arange(len(rows))
        for key, label in (
            ("loss_separation", "L_sep"),
            ("loss_peak", "L_peak"),
            ("loss_drift", "L_drift"),
            ("loss_entropy", "L_entropy"),
        ):
            axes[0].plot(x, [float(row.get(key, math.nan)) for row in rows], label=label)
        for key, label in (
            ("weighted_separation", "lambda_sep L_sep"),
            ("weighted_peak", "lambda_peak L_peak"),
            ("weighted_drift", "lambda_drift L_drift"),
            ("weighted_entropy", "lambda_entropy L_entropy"),
        ):
            axes[1].plot(x, [float(row.get(key, math.nan)) for row in rows], label=label)
    axes[0].set_ylabel("Unweighted value")
    axes[1].set_ylabel("Weighted contribution")
    axes[1].set_xlabel("Sequential training epoch")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    axes[0].set_title("Regularization values and objective contributions")
    for axis in axes:
        style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_uncertainty_summary(
    path: Path,
    summary_rows: Sequence[Mapping[str, Any]],
) -> None:
    names = [str(row["Model"]) for row in summary_rows]
    means = np.asarray([float(row["raw_K_mean"]) for row in summary_rows])
    lower = np.asarray([float(row["raw_K_ci95_low"]) for row in summary_rows])
    upper = np.asarray([float(row["raw_K_ci95_high"]) for row in summary_rows])
    figure, axis = plt.subplots(figsize=(10, 5.5))
    positions = np.arange(len(names))
    axis.errorbar(
        positions,
        means,
        yerr=np.vstack((means - lower, upper - means)),
        fmt="o",
        color="#2c6e91",
        capsize=5,
    )
    axis.axhline(0.0, color="#b23a48", linewidth=1.1)
    axis.set_xticks(positions, names, rotation=18, ha="right")
    axis.set_ylabel("Raw K mean and 95% CI")
    axis.set_title("Independent Monte Carlo runs")
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_metric_sweep(
    path: Path,
    x: np.ndarray,
    values: Mapping[str, np.ndarray],
    ylabel: str,
    title: str,
) -> None:
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for name, series in values.items():
        axis.plot(x, series, marker="o", linewidth=1.5, label=name)
    if "K" in ylabel:
        axis.axhline(0.0, color="#b23a48", linewidth=1.0)
    axis.set_xlabel("SNR (dB)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend(fontsize=8)
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def learned_evaluation_map(
    evaluations: Mapping[str, SchemeEvaluation],
) -> dict[str, SchemeEvaluation]:
    mapping: dict[str, SchemeEvaluation] = {}
    for name, evaluation in evaluations.items():
        if "Learned PS fixed" in name:
            mapping["PS"] = evaluation
        elif "Learned GS" in name:
            mapping["GS"] = evaluation
        elif "Learned joint" in name:
            mapping["PS+GS"] = evaluation
    return mapping


def plot_constellations(path: Path, evaluations: Mapping[str, SchemeEvaluation]) -> None:
    learned = learned_evaluation_map(evaluations)
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.6), squeeze=False)
    for axis, label in zip(axes[0], ("PS", "GS", "PS+GS")):
        evaluation = learned.get(label)
        if evaluation is None:
            axis.text(0.5, 0.5, "Not trained", ha="center", va="center", transform=axis.transAxes)
            axis.set_title(label)
            continue
        index = int(torch.argmin((evaluation.transmittance - evaluation.transmittance.mean()).abs()))
        points = evaluation.constellation[index].detach().cpu().numpy()
        probabilities = evaluation.probabilities[index].detach().cpu().numpy()
        scatter = axis.scatter(
            points.real,
            points.imag,
            s=10.0 + 1300.0 * probabilities,
            c=np.log10(np.maximum(probabilities, 1e-12)),
            cmap="viridis",
            alpha=0.85,
            edgecolors="none",
        )
        axis.set_title(f"{label} at T={float(evaluation.transmittance[index]):.4g}")
        axis.set_aspect("equal")
        axis.set_xlabel("Re(alpha)")
        axis.set_ylabel("Im(alpha)")
        style_axis(axis)
        figure.colorbar(scatter, ax=axis, label="log10 probability", shrink=0.8)
    figure.suptitle("Learned 256-QAM constellations")
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_probability_heatmaps(path: Path, evaluations: Mapping[str, SchemeEvaluation]) -> None:
    learned = learned_evaluation_map(evaluations)
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.2), squeeze=False)
    for axis, label in zip(axes[0], ("PS", "GS", "PS+GS")):
        evaluation = learned.get(label)
        if evaluation is None:
            axis.text(0.5, 0.5, "Not trained", ha="center", va="center", transform=axis.transAxes)
            axis.set_title(label)
            continue
        probabilities = evaluation.probabilities.mean(0).detach().cpu().numpy().reshape(16, 16)
        image = axis.imshow(probabilities.T, origin="lower", cmap="magma", aspect="equal")
        axis.set_title(label)
        axis.set_xlabel("k index")
        axis.set_ylabel("l index")
        figure.colorbar(image, ax=axis, label="Mean probability", shrink=0.8)
    figure.suptitle("State-averaged symbol probabilities")
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_initial_final_geometry(
    path: Path,
    base_qam: torch.Tensor,
    evaluations: Mapping[str, SchemeEvaluation],
) -> None:
    joint = evaluations.get("Learned joint PS+GS")
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    base = complex_from_xy(base_qam).detach().cpu().numpy()
    axes[0].scatter(base.real, base.imag, s=14, color="#6c757d", alpha=0.8)
    axes[0].set_title("Initial normalized square QAM")
    if joint is None:
        axes[1].text(0.5, 0.5, "Joint model not trained", ha="center", va="center")
        axes[1].set_title("Final PS+GS")
    else:
        index = int(torch.argmin((joint.transmittance - joint.transmittance.mean()).abs()))
        points = joint.unit_constellation[index].detach().cpu().numpy()
        probabilities = joint.probabilities[index].detach().cpu().numpy()
        axes[1].scatter(
            points.real,
            points.imag,
            s=10.0 + 1300.0 * probabilities,
            c=probabilities,
            cmap="viridis",
            alpha=0.85,
        )
        axes[1].set_title("Final PS+GS, size/color proportional to p")
    for axis in axes:
        axis.set_aspect("equal")
        axis.set_xlabel("I coordinate")
        axis.set_ylabel("Q coordinate")
        style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_metric_bars(
    path: Path,
    evaluations: Mapping[str, SchemeEvaluation],
    metric: str,
    title: str,
    ylabel: str,
) -> None:
    names = list(evaluations)
    values: list[float] = []
    errors: list[float] = []
    for evaluation in evaluations.values():
        tensor = {
            "iab": evaluation.i_ab,
            "holevo": evaluation.security.chi_be,
            "skr": evaluation.raw_skr,
        }[metric]
        values.append(float(tensor.mean()))
        errors.append(float(tensor.std(unbiased=False)))
    figure, axis = plt.subplots(figsize=(10, 5.5))
    positions = np.arange(len(names))
    axis.bar(positions, values, yerr=errors, color="#2c6e91", alpha=0.86, capsize=4)
    if metric == "skr":
        axis.axhline(0.0, color="#b23a48", linewidth=1.2)
    axis.set_xticks(positions, names, rotation=18, ha="right")
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def plot_skr_sweep(
    path: Path,
    x: np.ndarray,
    sweep: Mapping[str, np.ndarray],
    xlabel: str,
    title: str,
    log_x: bool = False,
) -> None:
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for name, values in sweep.items():
        axis.plot(x, values, marker="o", linewidth=1.6, label=name)
    axis.axhline(0.0, color="#b23a48", linewidth=1.1)
    if log_x:
        axis.set_xscale("log")
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Mean raw SKR (bits/symbol)")
    axis.set_title(title)
    axis.legend(fontsize=8)
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def evaluate_transmittance_sweep(
    models: Mapping[str, JointPSGS256QAM],
    base_qam: torch.Tensor,
    args: argparse.Namespace,
) -> tuple[np.ndarray, dict[str, dict[str, np.ndarray]]]:
    t_values = torch.logspace(-4, 0, args.transmittance_points, dtype=REAL_DTYPE, device=base_qam.device)
    evaluations = evaluate_schemes(
        models,
        t_values,
        base_qam,
        args,
        args.seed + 31_000,
        noise_samples=args.ncut_check_awgn_samples,
        ncut=args.final_ncut,
    )
    snr_db = 10.0 * torch.log10(
        (t_values * args.va / (1.0 + t_values * args.epsilon / 2.0)).clamp_min(1e-12)
    )
    metrics = {
        "raw_K": {
            name: evaluation.raw_skr.detach().cpu().numpy()
            for name, evaluation in evaluations.items()
        },
        "I_AB": {
            name: evaluation.i_ab.detach().cpu().numpy()
            for name, evaluation in evaluations.items()
        },
        "chi_BE": {
            name: evaluation.security.chi_be.detach().cpu().numpy()
            for name, evaluation in evaluations.items()
        },
    }
    return snr_db.detach().cpu().numpy(), metrics


def evaluate_visibility_sweep(
    models: Mapping[str, JointPSGS256QAM],
    base_qam: torch.Tensor,
    args: argparse.Namespace,
    geometry: GeometryParams,
    channel_parameters: ChannelParams,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    visibility_values = np.geomspace(args.visibility_min, args.visibility_max, args.visibility_points)
    t_values: list[float] = []
    for index, visibility in enumerate(visibility_values):
        varied = replace(channel_parameters, visibility_km=float(visibility))
        data = channel(
            geometry,
            varied,
            N=max(2, args.test_fading_samples),
            rng=np.random.default_rng(args.seed + 40_000 + index),
        )
        t_values.append(float(data["T_eff"]))
    transmittance = torch.tensor(t_values, dtype=REAL_DTYPE, device=base_qam.device)
    evaluations = evaluate_schemes(
        models,
        transmittance,
        base_qam,
        args,
        args.seed + 41_000,
        noise_samples=args.ncut_check_awgn_samples,
        ncut=args.final_ncut,
    )
    sweep = {name: evaluation.raw_skr.detach().cpu().numpy() for name, evaluation in evaluations.items()}
    return visibility_values, sweep


def minimum_pair_distance(constellation: torch.Tensor) -> float:
    points = torch.view_as_real(constellation)
    distances = torch.cdist(points, points)
    diagonal = torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=points.device)
    return float(distances.masked_fill(diagonal.unsqueeze(0), math.inf).min())


def finite_difference_gradient_checks(
    base_qam: torch.Tensor,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    """Compare autograd and central differences for a direct small-state objective."""
    transmittance = torch.tensor([0.08], dtype=REAL_DTYPE, device=base_qam.device)
    noise_samples = 2
    standard_noise = make_standard_complex_noise(
        1,
        SYMBOL_COUNT,
        noise_samples,
        tensor_generator(args.seed + 700_000, base_qam.device),
        base_qam.device,
    )
    initial_probabilities = project_probabilities("mb", base_qam.device)
    initial_logits = torch.log(initial_probabilities.clamp_min(1e-12))
    cutoff = min(args.train_ncut, 16)

    def objective(logits: torch.Tensor, coordinates: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        probabilities = torch.softmax(logits, dim=-1).unsqueeze(0)
        raw_complex = complex_from_xy(coordinates)
        unit = normalize_unit_energy_batch(probabilities, raw_complex)
        physical = unit * math.sqrt(args.va / 2.0)
        i_ab = discrete_mi_mismatched_awgn_batch(
            probabilities,
            physical,
            transmittance,
            args.epsilon,
            noise_samples,
            standard_noise,
            args.candidate_chunk_size,
        )
        security = differentiable_security_block(
            probabilities,
            physical,
            transmittance,
            args.epsilon,
            args.va,
            cutoff,
        )
        return (args.beta * i_ab - security.chi_be).mean(), security.chi_be.mean()

    logits = initial_logits.clone().requires_grad_(True)
    coordinates = base_qam.clone().requires_grad_(True)
    raw_skr, chi_be = objective(logits, coordinates)
    analytical_logits, analytical_coordinates = torch.autograd.grad(
        raw_skr,
        (logits, coordinates),
        retain_graph=True,
    )
    chi_logits, chi_coordinates = torch.autograd.grad(chi_be, (logits, coordinates))
    symbol_index = 8 * GRID_SIDE + 8
    step = args.finite_difference_step

    checks: list[tuple[str, float, Any]] = [
        (
            "probability_logit",
            float(analytical_logits[symbol_index]),
            (symbol_index, None),
        ),
        (
            "I_coordinate",
            float(analytical_coordinates[symbol_index, 0]),
            (symbol_index, 0),
        ),
        (
            "Q_coordinate",
            float(analytical_coordinates[symbol_index, 1]),
            (symbol_index, 1),
        ),
    ]
    rows: list[dict[str, Any]] = []
    for name, analytical, (index, coordinate_axis) in checks:
        plus_logits = initial_logits.clone()
        minus_logits = initial_logits.clone()
        plus_coordinates = base_qam.clone()
        minus_coordinates = base_qam.clone()
        if coordinate_axis is None:
            plus_logits[index] += step
            minus_logits[index] -= step
        else:
            plus_coordinates[index, coordinate_axis] += step
            minus_coordinates[index, coordinate_axis] -= step
        plus = float(objective(plus_logits, plus_coordinates)[0])
        minus = float(objective(minus_logits, minus_coordinates)[0])
        numerical = (plus - minus) / (2.0 * step)
        absolute_error = abs(analytical - numerical)
        relative_error = absolute_error / max(abs(analytical), abs(numerical), 1e-10)
        rows.append(
            {
                "component": name,
                "analytical_gradient": analytical,
                "finite_difference_gradient": numerical,
                "absolute_error": absolute_error,
                "relative_error": relative_error,
                "passed": math.isfinite(relative_error)
                and relative_error <= args.finite_difference_tolerance,
            }
        )
    if not bool(torch.all(torch.isfinite(chi_logits))) or not bool(
        torch.all(torch.isfinite(chi_coordinates))
    ):
        raise AssertionError("chi_BE gradients are non-finite.")
    if float(torch.linalg.vector_norm(chi_logits)) <= 1e-12:
        raise AssertionError("chi_BE does not contribute a probability gradient.")
    if float(torch.linalg.vector_norm(chi_coordinates)) <= 1e-12:
        raise AssertionError("chi_BE does not contribute a geometry gradient.")
    if not all(bool(row["passed"]) for row in rows):
        raise AssertionError(f"Finite-difference gradient check failed: {rows}")
    return rows


def validate_experiment(
    models: Mapping[str, JointPSGS256QAM],
    evaluations: Mapping[str, SchemeEvaluation],
    history: Sequence[Mapping[str, Any]],
    transmittance: torch.Tensor,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
) -> list[str]:
    messages: list[str] = []
    tolerance = 5e-8
    for name, evaluation in evaluations.items():
        probability_sum = evaluation.probabilities.sum(-1)
        if not torch.allclose(probability_sum, torch.ones_like(probability_sum), atol=1e-10, rtol=0.0):
            raise AssertionError(f"{name}: probabilities do not sum to one.")
        if bool(torch.any(evaluation.probabilities < 0.0)):
            raise AssertionError(f"{name}: negative probability detected.")
        mean = torch.sum(evaluation.probabilities * evaluation.constellation, dim=-1)
        unit_energy = torch.sum(
            evaluation.probabilities * evaluation.unit_constellation.abs().square(),
            dim=-1,
        )
        va = 2.0 * torch.sum(
            evaluation.probabilities * evaluation.constellation.abs().square(),
            dim=-1,
        )
        if float(mean.abs().max()) > tolerance:
            raise AssertionError(f"{name}: nonzero probabilistic constellation mean.")
        if not torch.allclose(
            unit_energy,
            torch.ones_like(unit_energy),
            atol=tolerance,
            rtol=0.0,
        ):
            raise AssertionError(f"{name}: shaped weighted energy is not one.")
        if not torch.allclose(va, torch.full_like(va, args.va), atol=tolerance, rtol=0.0):
            raise AssertionError(f"{name}: modulation variance normalization failed.")
        if bool(torch.any(evaluation.entropy < -1e-10)) or bool(torch.any(evaluation.entropy > 8.0 + 1e-10)):
            raise AssertionError(f"{name}: entropy is outside [0, 8].")
        if bool(torch.any(evaluation.i_ab < -2e-3)) or bool(
            torch.any(evaluation.i_ab > evaluation.entropy + 1e-10)
        ):
            raise AssertionError(f"{name}: discrete MI is outside its finite-sample bounds.")
        finite_tensors = (
            evaluation.i_ab,
            evaluation.security.chi_be,
            evaluation.raw_skr,
            evaluation.security.w,
            evaluation.security.z,
        )
        if not all(bool(torch.all(torch.isfinite(value))) for value in finite_tensors):
            raise AssertionError(f"{name}: non-finite security metric detected.")
        if minimum_pair_distance(evaluation.constellation) <= 1e-8:
            raise AssertionError(f"{name}: coincident constellation points detected.")

    stage_names = {
        "ps": {"ps"},
        "gs": {"gs"},
        "joint": {"geometry_warmup", "joint_finetune", "refinement", "resume"},
    }
    for stage, model in models.items():
        stage_rows = [
            row
            for row in history
            if row["stage"] in stage_names[stage] and int(row["epoch"]) > 0
        ]
        if stage_rows and stage in {"ps", "joint"}:
            norms = [
                float(row["probability_gradient_norm"])
                for row in stage_rows
                if "probability_gradient_norm" in row
            ]
            if not norms or not all(math.isfinite(value) for value in norms) or max(norms) <= 1e-12:
                raise AssertionError(f"{stage}: probability gradients are not finite and nonzero.")
        if stage_rows and stage in {"gs", "joint"}:
            norms = [
                float(row["geometry_gradient_norm"])
                for row in stage_rows
                if "geometry_gradient_norm" in row
            ]
            if not norms or not all(math.isfinite(value) for value in norms) or max(norms) <= 1e-12:
                raise AssertionError(f"{stage}: geometry gradients are not finite and nonzero.")

    # Determinism is a property of the implementation, not the Monte Carlo sample
    # count. A bounded probe avoids repeating the publication-scale evaluation twice.
    probe_transmittance = transmittance[: min(2, transmittance.numel())]
    probe_noise_samples = min(8, args.validation_awgn_samples)
    probe_ncut = min(24, args.validation_ncut)
    repeat_a = evaluate_schemes(
        models,
        probe_transmittance,
        base_qam,
        args,
        args.seed + 50_000,
        noise_samples=probe_noise_samples,
        ncut=probe_ncut,
    )
    repeat_b = evaluate_schemes(
        models,
        probe_transmittance,
        base_qam,
        args,
        args.seed + 50_000,
        noise_samples=probe_noise_samples,
        ncut=probe_ncut,
    )
    for name in repeat_a:
        deterministic_pairs = (
            (repeat_a[name].i_ab, repeat_b[name].i_ab),
            (repeat_a[name].security.chi_be, repeat_b[name].security.chi_be),
            (repeat_a[name].raw_skr, repeat_b[name].raw_skr),
        )
        if not all(torch.equal(first, second) for first, second in deterministic_pairs):
            raise AssertionError(f"{name}: fixed-seed evaluation is not deterministic.")

    uniform_output = model_output_for_baseline(
        "uniform", transmittance[:1], base_qam, args.va
    )
    torch_security = differentiable_security_block(
        uniform_output.probabilities,
        uniform_output.constellation,
        transmittance[:1],
        args.epsilon,
        args.va,
        args.validation_ncut,
    )
    numpy_state = project_uniform.compute_state(float(QAM_ALPHA0_UNIFORM), args.validation_ncut)
    if abs(float(torch_security.tr_c[0]) - float(numpy_state["tr_c"])) > 2e-5:
        raise AssertionError("PyTorch security Tr(C) does not match the project implementation.")
    if abs(float(torch_security.w[0]) - float(numpy_state["w"])) > 2e-5:
        raise AssertionError("PyTorch security w does not match the project implementation.")

    reference_generator = tensor_generator(args.seed + 60_000, transmittance.device)
    reference_noise = make_standard_complex_noise(
        1,
        SYMBOL_COUNT,
        args.validation_awgn_samples,
        reference_generator,
        transmittance.device,
    )
    ours = discrete_mi_mismatched_awgn_batch(
        uniform_output.probabilities,
        uniform_output.constellation,
        transmittance[:1],
        args.epsilon,
        args.validation_awgn_samples,
        reference_noise,
        args.candidate_chunk_size,
    )
    project_value = project_discrete_mi(
        uniform_output.probabilities[0],
        uniform_output.constellation[0],
        transmittance[:1],
        args.epsilon,
        noise_samples_per_symbol=args.validation_awgn_samples,
        generator=tensor_generator(args.seed + 60_000, transmittance.device),
        antithetic=True,
        candidate_chunk_size=args.candidate_chunk_size,
    )
    if not torch.allclose(ours, project_value, atol=1e-12, rtol=1e-12):
        raise AssertionError("Batched MI does not match the sample implementation.")

    messages.extend(
        (
            "Probability simplex, shaped unit energy, centering, and V_A checks passed.",
            "Discrete MI entropy bounds and all finite security/SKR checks passed.",
            "No coincident constellation points were found.",
            "Bounded fixed-seed MI, Holevo, and SKR probes are bitwise deterministic.",
            "Differentiable Tr(C), w, and discrete MI match project references within tolerance.",
        )
    )
    messages.insert(
        2,
        "Finite, nonzero gradient-flow checks passed for every stage trained in this invocation."
        if history
        else "Training-gradient checks were skipped in evaluation-only mode; checkpoint tests remain available.",
    )
    return messages


def format_comparison(rows: Sequence[Mapping[str, Any]]) -> str:
    header = (
        f"{'Scheme':<38} {'H(X)':>8} {'I_AB':>10} {'chi_BE':>10} "
        f"{'raw SKR':>11} {'positive':>11} {'outage':>9}"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{str(row['Model']):<38} {float(row['H_X']):>8.4f} "
            f"{float(row['I_AB_discrete']):>10.6f} {float(row['chi_BE']):>10.6f} "
            f"{float(row['raw_SKR']):>+11.6f} {float(row['clipped_SKR']):>11.6f} "
            f"{float(row['SKR_outage_probability']):>9.3f}"
        )
    return "\n".join(lines)


def write_report(
    path: Path,
    args: argparse.Namespace,
    channel_splits: Mapping[str, Mapping[str, Any]],
    comparison_rows: Sequence[Mapping[str, Any]],
    validation_messages: Sequence[str],
    initialization_rows: Sequence[Mapping[str, Any]],
    uncertainty_rows: Sequence[Mapping[str, Any]],
    ncut_rows: Sequence[Mapping[str, Any]],
    finite_difference_rows: Sequence[Mapping[str, Any]],
) -> None:
    smoke_note = (
        "This was a reduced smoke run intended to validate execution and gradients, not convergence."
        if args.smoke_test
        else "This was a requested training run; convergence still depends on hyperparameter study."
    )
    report = f"""Joint probabilistic/geometric shaping experiment
==================================================

Imported project components
---------------------------
- uav_hap_1.channel.channel_model.channel: instantaneous Rayleigh beam-displacement fading,
  T_samples, and T_eff.
- uav_hap_1.config: V_A-related QAM scale, beta={args.beta}, epsilon={args.epsilon},
  detector parameters, visibility, beam waist, aperture, and Cn2 defaults.
- uav_hap_1.zstar.base: square-QAM coordinates, Uniform/MB PMFs, and the reference
  density-matrix/security equations.
- uav_hap_1_sample.iab.discrete: reference discrete-MI implementation used for parity testing.

Independent channel data
------------------------
Training mean T: {float(np.mean(channel_splits['train']['T_samples'])):.10g}
Validation mean T: {float(np.mean(channel_splits['validation']['T_samples'])):.10g}
Test mean T: {float(np.mean(channel_splits['test']['T_samples'])):.10g}
Visibility: {args.visibility_km:.6g} km
Beam waist W0: {args.beam_waist_m:.6g} m
Aperture radius: {args.aperture_radius_m:.6g} m
Cn2: {args.cn2:.6g} m^(-2/3)
Rayleigh is used only for beam-displacement/channel fading, never as a symbol PMF.

Source inconsistencies and conventions
--------------------------------------
- The original NumPy/SciPy security functions return Python floats, so they are not
  differentiable. Their equations were translated to complex128 PyTorch here.
- The original protocol reports Gaussian-input I_AB and includes chi_tot; this experiment
  uses the requested discrete-input channel variance sigma_c^2 = 1 + T*epsilon/2.
- QAM_ALPHA0_MB is rounded, so its project V_A is slightly below 2. Every learned
  ensemble is centered and normalized to E_p[|x|^2]=1, then physically scaled to
  V_A={args.va} for MI and Holevo calculations.
- The density matrices are numerically low rank. Eigenvalues at or below 1e-12 are
  suppressed only in matrix square roots/pseudoinverses, matching the project convention.
- Physical covariance stabilization limits Z below sqrt(a*b), as in compute_metrics.

Architecture
------------
Mode: {args.mode}
Probability network: Linear(3, {args.hidden_dim}) -> ReLU -> Linear({args.hidden_dim}, 256)
Features: [log10(T), epsilon, SNR_dB]
Symmetry: {args.symmetry}; raw_constellation is a 256x2 Parameter. Fourfold mode reads
only first-quadrant prototypes and mirrors them in deterministic k*16+l order.
Probability initialization: {args.probability_initialization}
Target modulation variance: {args.va}
Training/validation/final Fock cutoffs: {args.train_ncut}/{args.validation_ncut}/{args.final_ncut}
Precision: float64 / complex128
The optional hard straight-through Gumbel output is {'enabled' if args.use_gumbel else 'disabled'};
the direct SKR loss always uses exact 256-symbol enumeration.

Loss
----
loss = -mean(beta*I_AB_discrete - chi_BE)
       + {args.lambda_sep}*L_sep
       + {args.lambda_peak}*L_peak
       + {args.lambda_drift}*L_drift
       + {args.lambda_entropy}*L_entropy
K_raw is never clamped in training. Only reported/plotting values use max(K_raw, 0).

Run settings
------------
Seed: {args.seed}
PS/GS/geometry-warmup/joint/refinement epochs:
{args.ps_epochs}/{args.gs_epochs}/{args.geometry_warmup_epochs}/{args.joint_epochs}/{args.refinement_epochs}
Training fading samples per newly sampled epoch: {args.train_fading_samples}
Fading batch size: {args.fading_batch_size}
Training/validation/test AWGN samples per symbol:
{args.train_awgn_samples}/{args.validation_awgn_samples}/{args.test_awgn_samples}
Validation/test fading samples: {args.validation_fading_samples}/{args.test_fading_samples}
Independent uncertainty runs: {args.uncertainty_runs}
Probability learning rate: {args.probability_lr}
Constellation learning rate: {args.constellation_lr}
Gradient clip norm: {args.gradient_clip}
Optimizer/scheduler: {args.optimizer}/{args.scheduler}
Update strategy: {args.update_strategy}
{smoke_note}

Epoch-zero joint initialization comparison
------------------------------------------
{chr(10).join(str(dict(row)) for row in initialization_rows) if initialization_rows else 'Not run for this mode.'}

Validation
----------
{chr(10).join('- ' + message for message in validation_messages)}

Baseline comparison
-------------------
{format_comparison(comparison_rows)}

Uncertainty summary
-------------------
{chr(10).join(str(dict(row)) for row in uncertainty_rows)}

ncut convergence
----------------
{chr(10).join(str(dict(row)) for row in ncut_rows) if ncut_rows else 'Skipped by configuration.'}

Finite-difference gradients
---------------------------
{chr(10).join(str(dict(row)) for row in finite_difference_rows) if finite_difference_rows else 'Skipped by configuration.'}

Reproducible commands
---------------------
PS-only:
  python uav_hap_joint_ps_gs.py --config ps_gs_fast_config.json --mode ps
GS-only:
  python uav_hap_joint_ps_gs.py --config ps_gs_fast_config.json --mode gs
Full staged PS+GS:
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --mode joint
Resume:
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --resume ps_gs_results/checkpoints/last_valid_joint.pt --resume-additional-epochs 100
Evaluation only:
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --evaluation-only
Ablation examples:
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --disable-geometry-regularization
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --update-strategy alternating
  python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --joint-initialization combined

Remaining limitations
---------------------
- The Holevo block inherits the project's asymptotic covariance-matrix lower-bound model;
  this is not a composable finite-size security proof.
- MI is an AWGN Monte Carlo estimate. Exact symbol enumeration removes symbol-sampling
  noise, but finite AWGN samples remain.
- ncut convergence is reported here, but publication thresholds still require a
  domain-specific tolerance and larger repeated runs.
- Hermitian eigendecomposition gradients can become ill-conditioned near repeated or
  thresholded density-matrix eigenvalues.
- State-conditioned shaping assumes transmitter/receiver access to the channel state and
  a deployable mechanism for synchronizing the selected PMF/geometry.
- Fast/smoke checkpoints demonstrate functionality and gradient flow only. PS+GS is
  claimed better only if repeated full runs give a positive confidence-supported gain.
"""
    path.write_text(report, encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config")
    known, _ = config_parser.parse_known_args(argv)
    config_defaults: dict[str, Any] = {}
    if known.config:
        config_path = Path(known.config)
        config_defaults = json.loads(config_path.read_text(encoding="utf-8"))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--mode", choices=("ps", "gs", "joint"), default="joint")
    parser.add_argument("--symmetry", choices=("fourfold", "central", "none"), default="fourfold")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--output-dir", default="ps_gs_results")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--probability-initialization", choices=("uniform", "mb"), default="mb")
    parser.add_argument(
        "--joint-initialization",
        choices=("auto", "ps", "gs", "combined", "ps_preserving"),
        default="auto",
    )
    parser.add_argument("--ps-epochs", type=int, default=200)
    parser.add_argument("--gs-epochs", type=int, default=100)
    parser.add_argument("--geometry-warmup-epochs", type=int, default=100)
    parser.add_argument("--joint-epochs", type=int, default=300)
    parser.add_argument("--refinement-epochs", type=int, default=100)
    parser.add_argument("--probability-lr", type=float, default=1e-3)
    parser.add_argument("--geometry-warmup-probability-lr", type=float, default=0.0)
    parser.add_argument("--constellation-lr", type=float, default=1e-4)
    parser.add_argument("--refinement-probability-lr", type=float, default=1e-4)
    parser.add_argument("--refinement-constellation-lr", type=float, default=1e-5)
    parser.add_argument("--optimizer", choices=("adam", "adamw"), default="adam")
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--scheduler", choices=("none", "plateau", "cosine"), default="plateau")
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--early-stopping-patience", type=int, default=40)
    parser.add_argument("--validation-interval", type=int, default=5)
    parser.add_argument("--update-strategy", choices=("simultaneous", "alternating"), default="simultaneous")
    parser.add_argument("--alternating-ps-steps", type=int, default=3)
    parser.add_argument("--train-fading-samples", type=int, default=64)
    parser.add_argument("--fading-batch-size", type=int, default=8)
    parser.add_argument("--validation-fading-samples", type=int, default=128)
    parser.add_argument("--test-fading-samples", type=int, default=256)
    parser.add_argument("--train-awgn-samples", type=int, default=8)
    parser.add_argument("--refinement-awgn-samples", type=int, default=16)
    parser.add_argument("--validation-awgn-samples", type=int, default=64)
    parser.add_argument("--test-awgn-samples", type=int, default=128)
    parser.add_argument("--uncertainty-runs", type=int, default=5)
    parser.add_argument("--candidate-chunk-size", type=int, default=64)
    parser.add_argument("--train-ncut", type=int, default=64)
    parser.add_argument("--validation-ncut", type=int, default=QAM_NCUT_UNIFORM)
    parser.add_argument("--final-ncut", type=int, default=QAM_NCUT_UNIFORM)
    parser.add_argument("--ncut-check", type=int, default=100)
    parser.add_argument("--ncut-check-awgn-samples", type=int, default=16)
    parser.add_argument("--ncut-check-fading-samples", type=int, default=8)
    parser.add_argument("--va", type=float, default=2.0)
    parser.add_argument("--beta", type=float, default=QAM_BETA)
    parser.add_argument("--epsilon", type=float, default=QAM_EPS)
    parser.add_argument("--separation-scale", type=float, default=0.15)
    parser.add_argument("--max-photon-number", type=float, default=5.0)
    parser.add_argument("--entropy-floor", type=float, default=5.0)
    parser.add_argument("--lambda-sep", type=float, default=1e-3)
    parser.add_argument("--lambda-peak", type=float, default=1e-3)
    parser.add_argument("--lambda-drift", type=float, default=1e-3)
    parser.add_argument("--lambda-entropy", type=float, default=0.0)
    parser.add_argument("--geometry-regularization-start-factor", type=float, default=0.0)
    parser.add_argument("--disable-geometry-regularization", action="store_true")
    parser.add_argument("--gradient-diagnostics-interval", type=int, default=10)
    parser.add_argument("--minimum-pairwise-distance", type=float, default=1e-6)
    parser.add_argument("--minimum-probability-entropy", type=float, default=0.25)
    parser.add_argument("--maximum-allowed-symbol-energy", type=float, default=100.0)
    parser.add_argument("--maximum-invalid-updates", type=int, default=5)
    parser.add_argument("--logit-clip", type=float, default=30.0)
    parser.add_argument("--use-gumbel", action="store_true")
    parser.add_argument("--gumbel-temperature-start", type=float, default=1.0)
    parser.add_argument("--gumbel-temperature-end", type=float, default=0.1)
    parser.add_argument("--visibility-km", type=float, default=10.0)
    parser.add_argument("--beam-waist-m", type=float, default=0.0626)
    parser.add_argument("--aperture-radius-m", type=float, default=0.20)
    parser.add_argument("--cn2", type=float, default=1e-15)
    parser.add_argument("--visibility-min", type=float, default=5.0)
    parser.add_argument("--visibility-max", type=float, default=40.0)
    parser.add_argument("--visibility-points", type=int, default=7)
    parser.add_argument("--transmittance-points", type=int, default=12)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--resume-additional-epochs", type=int, default=50)
    parser.add_argument("--evaluation-only", action="store_true")
    parser.add_argument("--skip-ncut-convergence", action="store_true")
    parser.add_argument("--skip-finite-difference", action="store_true")
    parser.add_argument("--finite-difference-step", type=float, default=1e-5)
    parser.add_argument("--finite-difference-tolerance", type=float, default=5e-2)
    parser.set_defaults(**config_defaults)
    args = parser.parse_args(argv)
    epoch_values = (
        args.ps_epochs,
        args.gs_epochs,
        args.geometry_warmup_epochs,
        args.joint_epochs,
        args.refinement_epochs,
    )
    if any(value < 0 for value in epoch_values):
        parser.error("Stage epoch counts must be non-negative.")
    if min(args.train_ncut, args.validation_ncut, args.final_ncut, args.ncut_check) <= 1:
        parser.error("All ncut values must exceed one.")
    if args.uncertainty_runs <= 0:
        parser.error("uncertainty-runs must be positive.")
    if args.smoke_test:
        args.ps_epochs = min(args.ps_epochs, 1)
        args.gs_epochs = min(args.gs_epochs, 1)
        args.geometry_warmup_epochs = min(args.geometry_warmup_epochs, 1)
        args.joint_epochs = min(args.joint_epochs, 1)
        args.refinement_epochs = min(args.refinement_epochs, 1)
        args.train_ncut = min(args.train_ncut, 20)
        args.validation_ncut = min(args.validation_ncut, 24)
        args.final_ncut = min(args.final_ncut, 24)
        args.ncut_check = min(args.ncut_check, 20)
        args.train_fading_samples = min(args.train_fading_samples, 3)
        args.fading_batch_size = min(args.fading_batch_size, 2)
        args.validation_fading_samples = min(args.validation_fading_samples, 2)
        args.test_fading_samples = min(args.test_fading_samples, 2)
        args.train_awgn_samples = min(args.train_awgn_samples, 4)
        args.refinement_awgn_samples = min(args.refinement_awgn_samples, 4)
        args.validation_awgn_samples = min(args.validation_awgn_samples, 8)
        args.test_awgn_samples = min(args.test_awgn_samples, 8)
        args.ncut_check_awgn_samples = min(args.ncut_check_awgn_samples, 4)
        args.ncut_check_fading_samples = min(args.ncut_check_fading_samples, 1)
        args.uncertainty_runs = min(args.uncertainty_runs, 2)
        args.visibility_points = min(args.visibility_points, 3)
        args.transmittance_points = min(args.transmittance_points, 5)
        args.validation_interval = 1
        args.gradient_diagnostics_interval = 1
        args.early_stopping_patience = max(args.early_stopping_patience, 2)
    return args


def phase_specifications(args: argparse.Namespace) -> dict[str, PhaseSpecification]:
    return {
        "ps": PhaseSpecification(
            "ps",
            args.ps_epochs,
            True,
            False,
            args.probability_lr,
            0.0,
            args.train_ncut,
            args.train_awgn_samples,
            args.train_fading_samples,
            0.0,
            0.0,
        ),
        "gs": PhaseSpecification(
            "gs",
            args.gs_epochs,
            False,
            True,
            0.0,
            args.constellation_lr,
            args.train_ncut,
            args.train_awgn_samples,
            args.train_fading_samples,
            args.geometry_regularization_start_factor,
            1.0,
        ),
        "geometry_warmup": PhaseSpecification(
            "geometry_warmup",
            args.geometry_warmup_epochs,
            args.geometry_warmup_probability_lr > 0.0,
            True,
            args.geometry_warmup_probability_lr,
            args.constellation_lr,
            args.train_ncut,
            args.train_awgn_samples,
            args.train_fading_samples,
            0.0,
            0.25,
        ),
        "joint_finetune": PhaseSpecification(
            "joint_finetune",
            args.joint_epochs,
            True,
            True,
            args.probability_lr,
            args.constellation_lr,
            args.train_ncut,
            args.train_awgn_samples,
            args.train_fading_samples,
            args.geometry_regularization_start_factor,
            1.0,
        ),
        "refinement": PhaseSpecification(
            "refinement",
            args.refinement_epochs,
            True,
            True,
            args.refinement_probability_lr,
            args.refinement_constellation_lr,
            args.final_ncut,
            args.refinement_awgn_samples,
            max(args.train_fading_samples, args.validation_fading_samples),
            1.0,
            1.0,
        ),
    }


def load_available_trained_models(
    output_dir: Path,
    base_qam: torch.Tensor,
    args: argparse.Namespace,
) -> dict[str, JointPSGS256QAM]:
    models: dict[str, JointPSGS256QAM] = {}
    for mode in ("ps", "gs", "joint"):
        path = output_dir / f"best_{mode}.pt"
        if not path.exists():
            continue
        model = create_model(mode, base_qam, args)
        load_training_checkpoint(path, model, restore_rng=False)
        models[mode] = model
    return models


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    set_deterministic_seed(args.seed)
    device = torch.device(args.device)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    geometry = GeometryParams()
    channel_parameters = ChannelParams(
        visibility_km=args.visibility_km,
        W0_m=args.beam_waist_m,
        a_m=args.aperture_radius_m,
        Cn2=args.cn2,
    )
    train_t, validation_t, test_t, channel_splits = independent_channel_splits(
        geometry,
        channel_parameters,
        args,
        device,
    )
    base_qam = build_project_qam(device)
    validation_noise = make_standard_complex_noise(
        validation_t.numel(),
        SYMBOL_COUNT,
        args.validation_awgn_samples,
        tensor_generator(args.seed + 404, device),
        device,
    )

    trained: dict[str, JointPSGS256QAM] = {}
    history: list[dict[str, Any]] = []
    initialization_rows: list[dict[str, Any]] = []
    training_times: dict[str, float] = {}
    specifications = phase_specifications(args)

    if args.evaluation_only:
        trained = load_available_trained_models(output_dir, base_qam, args)
        if not trained:
            raise FileNotFoundError(
                f"No best_ps.pt, best_gs.pt, or best_joint.pt checkpoints found in {output_dir}."
            )
    elif args.resume is not None:
        payload = torch.load(args.resume, map_location=device, weights_only=False)
        model_mode = str(payload["model_mode"])
        resumed_model = create_model(model_mode, base_qam, args)
        canonical_best_path = output_dir / f"best_{model_mode}.pt"
        best_payload = (
            torch.load(canonical_best_path, map_location=device, weights_only=False)
            if canonical_best_path.exists()
            else payload
        )
        previous_metrics = {
            key: float(value) for key, value in best_payload["validation_metrics"].items()
        }
        previous_best = BestCheckpoint(
            metrics=previous_metrics,
            model_state=copy.deepcopy(best_payload["model_state_dict"]),
            epoch=int(best_payload["epoch"]),
            phase=str(best_payload["phase"]),
            path=canonical_best_path if canonical_best_path.exists() else args.resume,
        )
        train_probabilities = model_mode in {"ps", "joint"}
        train_geometry = model_mode in {"gs", "joint"}
        resume_phase = PhaseSpecification(
            name=str(payload["phase"]),
            epochs=int(payload["epoch"]) + args.resume_additional_epochs,
            train_probabilities=train_probabilities,
            train_geometry=train_geometry,
            probability_lr=args.probability_lr if train_probabilities else 0.0,
            geometry_lr=args.constellation_lr if train_geometry else 0.0,
            ncut=args.final_ncut if str(payload["phase"]) == "refinement" else args.train_ncut,
            train_awgn_samples=args.refinement_awgn_samples
            if str(payload["phase"]) == "refinement"
            else args.train_awgn_samples,
            train_fading_samples=args.train_fading_samples,
            regularization_start_factor=1.0,
            regularization_end_factor=1.0,
        )
        resumed_model, resumed_history, resumed_best, elapsed = train_phase(
            resumed_model,
            resume_phase,
            geometry,
            channel_parameters,
            validation_t,
            validation_noise,
            args,
            output_dir,
            best=previous_best,
            resume_checkpoint=args.resume,
        )
        trained = load_available_trained_models(output_dir, base_qam, args)
        trained[model_mode] = resumed_model
        history.extend(resumed_history)
        training_times[model_mode] = elapsed
        print(f"Resumed {model_mode} from {args.resume}; best validation K={resumed_best.metrics['raw_skr']:+.6e}")
    else:
        if args.mode in {"ps", "joint"}:
            print("Training stage 1: PS-only convergence")
            ps_model = create_model("ps", base_qam, args)
            ps_model, ps_history, ps_best, ps_elapsed = train_phase(
                ps_model,
                specifications["ps"],
                geometry,
                channel_parameters,
                validation_t,
                validation_noise,
                args,
                output_dir,
            )
            trained["ps"] = ps_model
            history.extend(ps_history)
            training_times["ps"] = ps_elapsed
            print(f"PS best validation K={ps_best.metrics['raw_skr']:+.6e} at epoch {ps_best.epoch}")

        if args.mode in {"gs", "joint"}:
            print("Training matched GS-only model")
            gs_model = create_model("gs", base_qam, args, probability_initialization="uniform")
            gs_model, gs_history, gs_best, gs_elapsed = train_phase(
                gs_model,
                specifications["gs"],
                geometry,
                channel_parameters,
                validation_t,
                validation_noise,
                args,
                output_dir,
            )
            trained["gs"] = gs_model
            history.extend(gs_history)
            training_times["gs"] = gs_elapsed
            print(f"GS best validation K={gs_best.metrics['raw_skr']:+.6e} at epoch {gs_best.epoch}")

        if args.mode == "joint":
            print("Evaluating all PS+GS epoch-zero initialization candidates")
            joint_model, initialization_rows, joint_best = evaluate_joint_initializations(
                trained["ps"],
                trained["gs"],
                base_qam,
                validation_t,
                validation_noise,
                args,
                output_dir,
            )
            write_csv(output_dir / "joint_initializations.csv", initialization_rows)
            joint_elapsed = 0.0
            for phase_name in ("geometry_warmup", "joint_finetune", "refinement"):
                print(f"Training joint stage: {phase_name}")
                joint_model, phase_history, joint_best, elapsed = train_phase(
                    joint_model,
                    specifications[phase_name],
                    geometry,
                    channel_parameters,
                    validation_t,
                    validation_noise,
                    args,
                    output_dir,
                    best=joint_best,
                )
                history.extend(phase_history)
                joint_elapsed += elapsed
            trained["joint"] = joint_model
            training_times["joint"] = joint_elapsed
            print(
                f"Joint best validation K={joint_best.metrics['raw_skr']:+.6e} "
                f"from {joint_best.phase} epoch {joint_best.epoch}"
            )

    evaluations, uncertainty_run_rows, uncertainty_summary_rows = evaluate_uncertainty(
        trained,
        base_qam,
        geometry,
        channel_parameters,
        args,
    )
    validation_messages = validate_experiment(
        trained,
        evaluations,
        history,
        test_t,
        base_qam,
        args,
    )
    finite_difference_rows = (
        [] if args.skip_finite_difference else finite_difference_gradient_checks(base_qam, args)
    )
    if finite_difference_rows:
        validation_messages.append("Probability-logit and I/Q finite-difference checks passed.")
    ncut_rows = (
        []
        if args.skip_ncut_convergence
        else evaluate_ncut_convergence(trained, base_qam, test_t, args)
    )
    if ncut_rows:
        validation_messages.append(
            f"Full-ncut evaluation completed at ncut={args.final_ncut} and was compared with ncut={args.ncut_check}."
        )
    comparison_rows = summarize_evaluations(
        evaluations,
        trained,
        training_times,
        beta=args.beta,
    )

    write_csv(output_dir / "comparison.csv", comparison_rows)
    write_csv(output_dir / "uncertainty_runs.csv", uncertainty_run_rows)
    write_csv(output_dir / "uncertainty_summary.csv", uncertainty_summary_rows)
    write_csv(output_dir / "ncut_convergence.csv", ncut_rows)
    write_csv(output_dir / "finite_difference_gradients.csv", finite_difference_rows)
    write_csv(output_dir / "training_history.csv", history)
    save_learned_tables(output_dir, evaluations)
    if history:
        plot_training_history(output_dir / "training_loss.png", history)
        plot_training_metric_curves(output_dir / "training_validation_metrics.png", history)
        plot_regularization_history(output_dir / "regularization_history.png", history)
    plot_constellations(output_dir / "learned_constellations.png", evaluations)
    plot_initial_final_geometry(output_dir / "initial_final_geometry.png", base_qam, evaluations)
    plot_probability_heatmaps(output_dir / "probability_heatmaps.png", evaluations)
    plot_uncertainty_summary(output_dir / "random_seed_confidence_intervals.png", uncertainty_summary_rows)
    plot_metric_bars(
        output_dir / "iab_comparison.png",
        evaluations,
        "iab",
        "Discrete-input mutual information",
        "I_AB (bits/symbol)",
    )
    plot_metric_bars(
        output_dir / "holevo_comparison.png",
        evaluations,
        "holevo",
        "Holevo information recomputed per shaped ensemble",
        "chi_BE (bits/symbol)",
    )
    plot_metric_bars(
        output_dir / "skr_comparison.png",
        evaluations,
        "skr",
        "Raw secret-key rate over instantaneous fading",
        "Raw SKR (bits/symbol)",
    )
    snr_axis, snr_metrics = evaluate_transmittance_sweep(trained, base_qam, args)
    plot_metric_sweep(
        output_dir / "skr_vs_snr.png",
        snr_axis,
        snr_metrics["raw_K"],
        "Raw K (bits/symbol)",
        "Raw K versus SNR",
    )
    plot_metric_sweep(
        output_dir / "iab_vs_snr.png",
        snr_axis,
        snr_metrics["I_AB"],
        "I_AB (bits/symbol)",
        "Discrete mutual information versus SNR",
    )
    plot_metric_sweep(
        output_dir / "chi_be_vs_snr.png",
        snr_axis,
        snr_metrics["chi_BE"],
        "chi_BE (bits/symbol)",
        "Holevo information versus SNR",
    )
    visibility_axis, visibility_sweep = evaluate_visibility_sweep(
        trained,
        base_qam,
        args,
        geometry,
        channel_parameters,
    )
    plot_skr_sweep(
        output_dir / "skr_vs_visibility.png",
        visibility_axis,
        visibility_sweep,
        "Visibility (km)",
        "Raw SKR versus visibility using channel T_eff",
        log_x=True,
    )
    write_report(
        output_dir / "experiment_report.txt",
        args,
        channel_splits,
        comparison_rows,
        validation_messages,
        initialization_rows,
        uncertainty_summary_rows,
        ncut_rows,
        finite_difference_rows,
    )

    print("\n" + format_comparison(comparison_rows))
    print("\nValidation:")
    for message in validation_messages:
        print(f"  PASS: {message}")
    print(f"\nOutputs: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
