"""Common physical ensemble and paper training configurations, Eqs. (169), (191)--(195)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn

from .geometric_shaping import GlobalGeometricShaping
from .normalization import physical_amplitudes, validate_probabilities, weighted_center_and_normalize
from .probabilistic_shaping import ProbabilisticShapingNetwork, channel_features
from .qam256 import reference_pmf, square_qam256


@dataclass(frozen=True)
class Ensemble:
    """Statewise coherent-state ensemble consumed unchanged by MI and Holevo."""

    probabilities: torch.Tensor
    amplitudes: torch.Tensor
    declared_va: torch.Tensor
    raw_constellation: torch.Tensor
    exact_csi_oracle: bool = True

    def computed_va(self) -> torch.Tensor:
        return 2.0 * torch.sum(self.probabilities * self.amplitudes.abs().square(), dim=-1)

    def validate(self, tolerance: float = 1e-9) -> None:
        validate_probabilities(self.probabilities, tolerance=tolerance)
        if self.probabilities.ndim != 2:
            raise ValueError("Ensemble probabilities must have shape [B,M].")
        if self.amplitudes.shape != self.probabilities.shape or not self.amplitudes.is_complex():
            raise ValueError("Ensemble amplitudes must be complex and match probabilities.")
        if not bool(torch.all(torch.isfinite(self.amplitudes.real))) or not bool(
            torch.all(torch.isfinite(self.amplitudes.imag))
        ):
            raise ValueError("Ensemble amplitudes contain NaN or Inf.")
        declared = self.declared_va.reshape(-1)
        if declared.shape[0] != self.probabilities.shape[0]:
            raise ValueError("declared_va must have one value per state.")
        computed = self.computed_va()
        error = torch.abs(computed - declared)
        scale = torch.maximum(torch.ones_like(declared), torch.abs(declared))
        if not bool(torch.all(error <= tolerance * scale)):
            raise ValueError("Declared V_A does not equal 2 sum_i p_i |alpha_i|^2.")


class AdaptiveVarianceNetwork(nn.Module):
    """Exact paper Eqs. (162)--(166); bounds are mandatory inputs."""

    def __init__(self, v_min: float, v_max: float) -> None:
        super().__init__()
        if not math.isfinite(v_min) or not math.isfinite(v_max):
            raise ValueError("v_min and v_max must be explicitly finite.")
        if v_min <= 0.0 or v_max <= v_min:
            raise ValueError("Require 0 < v_min < v_max.")
        self.v_min = float(v_min)
        self.v_max = float(v_max)
        self.network = nn.Sequential(
            nn.Linear(2, 64, dtype=torch.float64),
            nn.ReLU(),
            nn.Linear(64, 1, dtype=torch.float64),
        )

    def forward(self, transmittance: torch.Tensor, epsilon: torch.Tensor) -> torch.Tensor:
        unit = torch.sigmoid(self.network(channel_features(transmittance, epsilon)).squeeze(-1))
        ratio = self.v_max / self.v_min
        return self.v_min * torch.pow(torch.as_tensor(ratio, dtype=unit.dtype, device=unit.device), unit)


class JointTransmitter(nn.Module):
    """Paper transmitter modes without a learned receiver/demapper."""

    MODES = {"uniform", "binomial", "mb", "ps", "gs", "ps_gs", "ps_va", "gs_va", "full"}

    def __init__(
        self,
        mode: str,
        *,
        fixed_va: float | None = None,
        v_min: float | None = None,
        v_max: float | None = None,
        reference_distribution: str = "uniform",
        nu_mb: float | None = None,
    ) -> None:
        super().__init__()
        if mode not in self.MODES:
            raise ValueError(f"Unsupported mode {mode!r}.")
        self.mode = mode
        self.reference_distribution = mode if mode in {"uniform", "binomial", "mb"} else reference_distribution
        base = square_qam256()
        self.register_buffer("base_constellation", base)
        fixed_pmf = reference_pmf(
            self.reference_distribution,
            nu_mb=nu_mb,
            dtype=torch.float64,
            device=base.device,
        )
        self.register_buffer("fixed_probabilities", fixed_pmf)
        self.ps_network = (
            ProbabilisticShapingNetwork(fixed_pmf)
            if mode in {"ps", "ps_gs", "ps_va", "full"}
            else None
        )
        self.gs_model = GlobalGeometricShaping(base) if mode in {"gs", "ps_gs", "gs_va", "full"} else None
        self.va_network = (
            AdaptiveVarianceNetwork(
                v_min if v_min is not None else float("nan"),
                v_max if v_max is not None else float("nan"),
            )
            if mode in {"ps_va", "gs_va", "full"}
            else None
        )
        if self.va_network is None:
            if fixed_va is None or not math.isfinite(fixed_va) or fixed_va <= 0.0:
                raise ValueError("A finite positive fixed_va is required for this mode.")
            self.fixed_va = float(fixed_va)
        else:
            self.fixed_va = None

    def forward(self, transmittance: torch.Tensor, epsilon: torch.Tensor) -> Ensemble:
        transmittance = torch.as_tensor(
            transmittance, dtype=torch.float64, device=self.base_constellation.device
        ).reshape(-1)
        epsilon = torch.as_tensor(
            epsilon, dtype=torch.float64, device=self.base_constellation.device
        ).reshape(-1)
        if epsilon.numel() == 1:
            epsilon = epsilon.expand_as(transmittance)
        # Validation and exact paper features are shared by PS and V_A branches.
        channel_features(transmittance, epsilon)
        probabilities = (
            self.ps_network(transmittance, epsilon)
            if self.ps_network is not None
            else self.fixed_probabilities.unsqueeze(0).expand(transmittance.shape[0], -1)
        )
        raw = self.gs_model() if self.gs_model is not None else self.base_constellation
        unit = weighted_center_and_normalize(probabilities, raw)
        variance = (
            self.va_network(transmittance, epsilon)
            if self.va_network is not None
            else torch.full_like(transmittance, self.fixed_va)
        )
        amplitudes = physical_amplitudes(unit, variance)
        ensemble = Ensemble(probabilities, amplitudes, variance, raw, exact_csi_oracle=True)
        ensemble.validate()
        return ensemble


def reference_ensemble(
    kind: str,
    *,
    batch_size: int,
    modulation_variance: float,
    nu_mb: float | None = None,
    device: torch.device | str | None = None,
) -> Ensemble:
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")
    transmitter = JointTransmitter(
        kind,
        fixed_va=modulation_variance,
        nu_mb=nu_mb,
    )
    if device is not None:
        transmitter = transmitter.to(device=device)
    t = torch.ones(batch_size, dtype=torch.float64, device=device)
    epsilon = torch.zeros(batch_size, dtype=torch.float64, device=device)
    return transmitter(t, epsilon)
