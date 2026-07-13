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
import math
import random
from dataclasses import asdict, dataclass, replace
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
        initial_normalized = normalize_constellation_batch(
            self.uniform_probabilities.unsqueeze(0),
            initial_complex,
            self.target_va,
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
        if self.mode == "gs":
            probabilities = self.uniform_probabilities.unsqueeze(0).expand(transmittance_tensor.numel(), -1)
        else:
            probabilities = torch.softmax(logits, dim=-1)
        probabilities_safe = probabilities.clamp_min(1e-12)

        raw_complex = complex_from_xy(self.effective_raw_constellation())
        constellation = normalize_constellation_batch(
            probabilities,
            raw_complex,
            self.target_va,
        )
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
) -> SecurityOutput:
    """Recompute tau, Tr(C), w, Z, Gamma_AB, and chi_BE for each state."""
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
    return SecurityOutput(
        tau=tau,
        tau_eigenvalues=eigenvalues,
        tau_trace=torch.diagonal(tau, dim1=-2, dim2=-1).sum(-1).real,
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
    points = torch.view_as_real(output.constellation)
    pairwise_distance2 = torch.cdist(points, points).square()
    off_diagonal = ~torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=points.device)
    separation = torch.exp(-pairwise_distance2 / float(separation_scale) ** 2)[:, off_diagonal].mean()
    peak = torch.relu(output.constellation.abs().square() - float(max_photon_number)).square().mean()
    drift = (output.constellation - model.initial_qam_complex.unsqueeze(0)).abs().square().mean()
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
    constellation = normalize_constellation_batch(probabilities, raw_complex, target_va)
    logits = torch.log(probabilities.clamp_min(1e-12))
    return ModelOutput(
        probabilities=probabilities,
        probabilities_safe=probabilities.clamp_min(1e-12),
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
) -> dict[str, SchemeEvaluation]:
    generator = tensor_generator(noise_seed, transmittance.device)
    standard_noise = make_standard_complex_noise(
        transmittance.numel(),
        SYMBOL_COUNT,
        args.eval_awgn_samples,
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
        for name, output in outputs.items():
            evaluations[name] = evaluate_output(
                name,
                output,
                transmittance,
                args.epsilon,
                args.beta,
                args.ncut,
                args.eval_awgn_samples,
                standard_noise,
                args.candidate_chunk_size,
                args.va,
            )
    return evaluations


def train_stage(
    stage: str,
    model: JointPSGS256QAM,
    transmittance: torch.Tensor,
    args: argparse.Namespace,
    output_dir: Path,
) -> tuple[JointPSGS256QAM, list[dict[str, Any]]]:
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


def create_stage_model(
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


def stage_sequence(mode: str) -> list[str]:
    if mode == "joint":
        return ["ps", "gs", "joint"]
    return [mode]


def summarize_evaluations(evaluations: Mapping[str, SchemeEvaluation]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, evaluation in evaluations.items():
        raw = evaluation.raw_skr.detach().cpu().numpy()
        rows.append(
            {
                "scheme": name,
                "H_X": float(evaluation.entropy.mean()),
                "I_AB_discrete": float(evaluation.i_ab.mean()),
                "chi_BE": float(evaluation.security.chi_be.mean()),
                "raw_SKR": float(evaluation.raw_skr.mean()),
                "reported_positive_SKR": float(evaluation.reported_skr.mean()),
                "w": float(evaluation.security.w.mean()),
                "Z": float(evaluation.security.z.mean()),
                "Tr_C": float(evaluation.security.tr_c.mean()),
                "mean_transmittance": float(evaluation.transmittance.mean()),
                "SKR_outage_probability": float(np.mean(raw <= 0.0)),
            }
        )
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str] | None = None) -> None:
    if not rows:
        return
    fieldnames = list(fields or rows[0].keys())
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
    colors = {"ps": "#d95f02", "gs": "#1b9e77", "joint": "#2c4c7c"}
    for stage in ("ps", "gs", "joint"):
        stage_rows = [row for row in history if row["stage"] == stage]
        if stage_rows:
            axis.plot(
                [row["epoch"] for row in stage_rows],
                [row["loss_total"] for row in stage_rows],
                marker="o",
                color=colors[stage],
                label=stage.upper(),
            )
    axis.set_title("Raw-SKR shaping objective")
    axis.set_xlabel("Epoch")
    axis.set_ylabel("Total loss")
    axis.legend()
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
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    t_values = torch.logspace(-4, 0, args.transmittance_points, dtype=REAL_DTYPE, device=base_qam.device)
    evaluations = evaluate_schemes(models, t_values, base_qam, args, args.seed + 31_000)
    return (
        t_values.detach().cpu().numpy(),
        {name: evaluation.raw_skr.detach().cpu().numpy() for name, evaluation in evaluations.items()},
    )


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
            N=max(2, args.fading_samples),
            rng=np.random.default_rng(args.seed + 40_000 + index),
        )
        t_values.append(float(data["T_eff"]))
    transmittance = torch.tensor(t_values, dtype=REAL_DTYPE, device=base_qam.device)
    evaluations = evaluate_schemes(models, transmittance, base_qam, args, args.seed + 41_000)
    sweep = {name: evaluation.raw_skr.detach().cpu().numpy() for name, evaluation in evaluations.items()}
    return visibility_values, sweep


def minimum_pair_distance(constellation: torch.Tensor) -> float:
    points = torch.view_as_real(constellation)
    distances = torch.cdist(points, points)
    diagonal = torch.eye(SYMBOL_COUNT, dtype=torch.bool, device=points.device)
    return float(distances.masked_fill(diagonal.unsqueeze(0), math.inf).min())


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
        va = 2.0 * torch.sum(
            evaluation.probabilities * evaluation.constellation.abs().square(),
            dim=-1,
        )
        if float(mean.abs().max()) > tolerance:
            raise AssertionError(f"{name}: nonzero probabilistic constellation mean.")
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

    for stage, model in models.items():
        stage_rows = [row for row in history if row["stage"] == stage]
        if stage in {"ps", "joint"}:
            norms = [float(row["probability_gradient_norm"]) for row in stage_rows]
            if not norms or not all(math.isfinite(value) for value in norms) or max(norms) <= 1e-12:
                raise AssertionError(f"{stage}: probability gradients are not finite and nonzero.")
        if stage in {"gs", "joint"}:
            norms = [float(row["geometry_gradient_norm"]) for row in stage_rows]
            if not norms or not all(math.isfinite(value) for value in norms) or max(norms) <= 1e-12:
                raise AssertionError(f"{stage}: geometry gradients are not finite and nonzero.")

    repeat_a = evaluate_schemes(models, transmittance, base_qam, args, args.seed + 50_000)
    repeat_b = evaluate_schemes(models, transmittance, base_qam, args, args.seed + 50_000)
    for name in repeat_a:
        if not torch.equal(repeat_a[name].i_ab, repeat_b[name].i_ab):
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
        args.ncut,
    )
    numpy_state = project_uniform.compute_state(float(QAM_ALPHA0_UNIFORM), args.ncut)
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
            "Probability simplex, non-negativity, centering, and V_A checks passed.",
            "Discrete MI entropy bounds and all finite security/SKR checks passed.",
            "PS, GS, and joint gradient-flow checks passed for every trained stage.",
            "No coincident constellation points were found.",
            "Fixed-seed evaluation is bitwise deterministic.",
            "Differentiable Tr(C), w, and discrete MI match project references within tolerance.",
        )
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
            f"{str(row['scheme']):<38} {float(row['H_X']):>8.4f} "
            f"{float(row['I_AB_discrete']):>10.6f} {float(row['chi_BE']):>10.6f} "
            f"{float(row['raw_SKR']):>+11.6f} {float(row['reported_positive_SKR']):>11.6f} "
            f"{float(row['SKR_outage_probability']):>9.3f}"
        )
    return "\n".join(lines)


def write_report(
    path: Path,
    args: argparse.Namespace,
    channel_data: Mapping[str, Any],
    comparison_rows: Sequence[Mapping[str, Any]],
    validation_messages: Sequence[str],
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

Channel data
------------
Mean instantaneous T: {float(np.mean(channel_data['T_samples'])):.10g}
T_eff: {float(channel_data['T_eff']):.10g}
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
- QAM_ALPHA0_MB is rounded, so its project V_A is slightly below 2. The comparison
  normalizes every ensemble to the common target V_A={args.va}.
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
Fock cutoff: {args.ncut}
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
Epochs per stage: {args.epochs}
Training fading samples: {args.fading_samples}
Fading batch size: {args.fading_batch_size}
Training AWGN samples/symbol: {args.awgn_samples}
Evaluation AWGN samples/symbol: {args.eval_awgn_samples}
Probability learning rate: {args.probability_lr}
Constellation learning rate: {args.constellation_lr}
Gradient clip norm: {args.gradient_clip}
{smoke_note}

Validation
----------
{chr(10).join('- ' + message for message in validation_messages)}

Baseline comparison
-------------------
{format_comparison(comparison_rows)}

Remaining limitations
---------------------
- The Holevo block inherits the project's asymptotic covariance-matrix lower-bound model;
  this is not a composable finite-size security proof.
- MI is an AWGN Monte Carlo estimate. Exact symbol enumeration removes symbol-sampling
  noise, but finite AWGN samples remain.
- Fock-space truncation must be increased and convergence-audited for final publication.
- Hermitian eigendecomposition gradients can become ill-conditioned near repeated or
  thresholded density-matrix eigenvalues.
- State-conditioned shaping assumes transmitter/receiver access to the channel state and
  a deployable mechanism for synchronizing the selected PMF/geometry.
- Smoke-test checkpoints demonstrate functionality and gradient flow only; they are not
  evidence that PS/GS has converged or improved the SKR.
"""
    path.write_text(report, encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ps", "gs", "joint"), default="joint")
    parser.add_argument("--symmetry", choices=("fourfold", "central", "none"), default="fourfold")
    parser.add_argument("--epochs", type=int, default=1000, help="Epochs per trained stage.")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--output-dir", default="ps_gs_results")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--probability-initialization", choices=("uniform", "mb"), default="mb")
    parser.add_argument("--probability-lr", type=float, default=1e-3)
    parser.add_argument("--constellation-lr", type=float, default=1e-4)
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--fading-samples", type=int, default=32)
    parser.add_argument("--fading-batch-size", type=int, default=4)
    parser.add_argument("--validation-fading-samples", type=int, default=4)
    parser.add_argument("--awgn-samples", type=int, default=8)
    parser.add_argument("--validation-awgn-samples", type=int, default=16)
    parser.add_argument("--eval-awgn-samples", type=int, default=32)
    parser.add_argument("--candidate-chunk-size", type=int, default=64)
    parser.add_argument("--ncut", type=int, default=QAM_NCUT_UNIFORM)
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
    parser.add_argument("--validation-interval", type=int, default=10)
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
    args = parser.parse_args(argv)
    if args.epochs <= 0 or args.ncut <= 1:
        parser.error("epochs must be positive and ncut must exceed one.")
    if args.smoke_test:
        args.epochs = min(args.epochs, 1)
        args.ncut = min(args.ncut, 24)
        args.fading_samples = min(args.fading_samples, 3)
        args.fading_batch_size = min(args.fading_batch_size, 2)
        args.validation_fading_samples = min(args.validation_fading_samples, 2)
        args.awgn_samples = min(args.awgn_samples, 4)
        args.validation_awgn_samples = min(args.validation_awgn_samples, 8)
        args.eval_awgn_samples = min(args.eval_awgn_samples, 8)
        args.visibility_points = min(args.visibility_points, 3)
        args.transmittance_points = min(args.transmittance_points, 5)
        args.validation_interval = 1
    return args


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
    channel_data = channel(
        geometry,
        channel_parameters,
        N=args.fading_samples,
        rng=np.random.default_rng(args.seed),
    )
    transmittance = torch.as_tensor(
        np.asarray(channel_data["T_samples"], dtype=np.float64),
        dtype=REAL_DTYPE,
        device=device,
    )
    base_qam = build_project_qam(device)

    trained: dict[str, JointPSGS256QAM] = {}
    history: list[dict[str, Any]] = []
    for stage in stage_sequence(args.mode):
        print(f"Training stage: {stage}")
        model = create_stage_model(stage, base_qam, args, trained)
        trained_model, stage_history = train_stage(
            stage,
            model,
            transmittance,
            args,
            output_dir,
        )
        trained[stage] = trained_model
        history.extend(stage_history)

    evaluations = evaluate_schemes(
        trained,
        transmittance,
        base_qam,
        args,
        args.seed + 20_000,
    )
    validation_messages = validate_experiment(
        trained,
        evaluations,
        history,
        transmittance,
        base_qam,
        args,
    )
    comparison_rows = summarize_evaluations(evaluations)

    write_csv(output_dir / "comparison.csv", comparison_rows)
    write_csv(output_dir / "training_history.csv", history)
    save_learned_tables(output_dir, evaluations)
    plot_training_history(output_dir / "training_loss.png", history)
    plot_constellations(output_dir / "learned_constellations.png", evaluations)
    plot_probability_heatmaps(output_dir / "probability_heatmaps.png", evaluations)
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
    t_axis, t_sweep = evaluate_transmittance_sweep(trained, base_qam, args)
    plot_skr_sweep(
        output_dir / "skr_vs_transmittance.png",
        t_axis,
        t_sweep,
        "Transmittance T",
        "Raw SKR versus transmittance",
        log_x=True,
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
        channel_data,
        comparison_rows,
        validation_messages,
    )

    print("\n" + format_comparison(comparison_rows))
    print("\nValidation:")
    for message in validation_messages:
        print(f"  PASS: {message}")
    print(f"\nOutputs: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
