"""Frozen C4 transmitter, common physical ensemble, and ablation configurations."""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn

from .geometric_shaping import GlobalGeometricShaping, canonical_c4_relative_constellation
from .normalization import physical_amplitudes, validate_probabilities
from .probabilistic_shaping import ProbabilisticShapingNetwork, channel_features
from .qam256 import c4_orbit_indices, c4_orbit_masses, reference_pmf, square_qam256


class PeakPhotonConstraintViolation(ValueError):
    """Raised when a physical ensemble leaves the preregistered peak domain."""


def validate_peak_photon_limit(n_peak_photons: float | None) -> float | None:
    """Validate the optional common hard peak-photon domain.

    ``None`` deliberately disables the mechanism for bounded software tests and
    legacy callers.  Publication entry points require a finite author-approved
    value separately; no numerical value is inferred here.
    """

    if n_peak_photons is None:
        return None
    value = float(n_peak_photons)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("n_peak_photons must be null or finite and positive.")
    return value


def enforce_peak_photon_constraint(
    ensemble: "Ensemble",
    n_peak_photons: float | None,
    *,
    relative_tolerance: float = 1e-12,
) -> None:
    """Fail closed on ``max_i |alpha_i|^2 > n_peak`` without mutation.

    The guard is evaluated on the final physical amplitudes after the frozen
    scalar energy normalization.  It never clips, translates, rescales, or
    detaches the ensemble subsequently supplied to MI and Holevo.
    """

    limit = validate_peak_photon_limit(n_peak_photons)
    if limit is None:
        return
    if not math.isfinite(relative_tolerance) or relative_tolerance < 0.0:
        raise ValueError("relative_tolerance must be finite and nonnegative.")
    state_peaks = ensemble.amplitudes.abs().square().amax(dim=-1)
    allowed = limit * (1.0 + relative_tolerance)
    violating = state_peaks > allowed
    if bool(torch.any(violating)):
        state_index = int(torch.nonzero(violating, as_tuple=False)[0, 0].detach())
        observed = float(state_peaks[state_index].detach())
        raise PeakPhotonConstraintViolation(
            "Hard peak-photon constraint violated: "
            f"state={state_index}, max|alpha|^2={observed:.17g}, "
            f"n_peak={limit:.17g}. The physical ensemble was rejected without clipping."
        )


@dataclass(frozen=True)
class Ensemble:
    """Statewise coherent-state ensemble consumed unchanged by MI and Holevo."""

    probabilities: torch.Tensor
    amplitudes: torch.Tensor
    declared_va: torch.Tensor
    raw_constellation: torch.Tensor
    exact_csi_oracle: bool = True
    c4_symmetric: bool = False

    @property
    def relative_constellation(self) -> torch.Tensor:
        """Canonical global relative points (legacy field name retained for API stability)."""

        return self.raw_constellation

    def computed_va(self) -> torch.Tensor:
        return 2.0 * torch.sum(self.probabilities * self.amplitudes.abs().square(), dim=-1)

    def weighted_mean(self) -> torch.Tensor:
        return torch.sum(self.probabilities * self.amplitudes, dim=-1)

    def weighted_pseudomoment(self) -> torch.Tensor:
        return torch.sum(self.probabilities * self.amplitudes.square(), dim=-1)

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
        if self.c4_symmetric:
            if self.probabilities.shape[-1] != 256:
                raise ValueError("Frozen C4 ensembles must have exactly 256 symbols.")
            if bool(torch.any(self.probabilities <= 0.0)):
                raise ValueError("Frozen softmax/reference PMFs must be strictly positive.")
            # This both checks tied probabilities and gives a direct implementation
            # guard against an incorrect q -> p expansion or missing factor of four.
            c4_orbit_masses(self.probabilities, tolerance=tolerance)
            indices = c4_orbit_indices(device=self.amplitudes.device)
            grouped = self.amplitudes[..., indices]
            rotated = 1j * grouped[..., :-1]
            rotation_error = torch.abs(grouped[..., 1:] - rotated)
            rotation_error = torch.maximum(
                rotation_error.amax(dim=(-2, -1)),
                torch.abs(grouped[..., :1] - 1j * grouped[..., -1:]).amax(dim=(-2, -1)),
            )
            amplitude_scale = torch.maximum(
                torch.ones_like(declared), self.amplitudes.abs().amax(dim=-1)
            )
            if not bool(torch.all(rotation_error <= tolerance * amplitude_scale)):
                raise ValueError("Physical amplitudes do not obey exact C4 rotations.")
            moment_scale = torch.maximum(torch.ones_like(declared), declared)
            if not bool(torch.all(self.weighted_mean().abs() <= tolerance * moment_scale)):
                raise ValueError("Frozen C4 ensemble has nonzero displacement.")
            if not bool(
                torch.all(self.weighted_pseudomoment().abs() <= tolerance * moment_scale)
            ):
                raise ValueError("Frozen C4 ensemble is not quadrature isotropic.")


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

    MODES = {
        "uniform", "binomial", "mb", "optimized_mb", "ps", "gs", "va",
        "ps_gs", "ps_va", "gs_va", "full",
    }

    def __init__(
        self,
        mode: str,
        *,
        fixed_va: float | None = None,
        v_min: float | None = None,
        v_max: float | None = None,
        reference_distribution: str = "uniform",
        nu_mb: float | None = None,
        n_peak_photons: float | None = None,
    ) -> None:
        super().__init__()
        if mode not in self.MODES:
            raise ValueError(f"Unsupported mode {mode!r}.")
        self.mode = mode
        self.n_peak_photons = validate_peak_photon_limit(n_peak_photons)
        self.reference_distribution = (
            "mb" if mode == "optimized_mb"
            else mode if mode in {"uniform", "binomial", "mb"}
            else reference_distribution
        )
        base = square_qam256()
        self.register_buffer("base_constellation", base)
        self.register_buffer(
            "base_relative_constellation", canonical_c4_relative_constellation(base)
        )
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
            if mode in {"va", "ps_va", "gs_va", "full"}
            else None
        )
        if self.va_network is None:
            if fixed_va is None or not math.isfinite(fixed_va) or fixed_va <= 0.0:
                raise ValueError("A finite positive fixed_va is required for this mode.")
            if (v_min is None) != (v_max is None):
                raise ValueError("v_min and v_max must be supplied together for fixed-V_A modes.")
            if v_min is not None and v_max is not None:
                if not math.isfinite(v_min) or not math.isfinite(v_max) or not 0.0 < v_min < v_max:
                    raise ValueError("Require finite common bounds 0 < v_min < v_max.")
                if not v_min <= fixed_va <= v_max:
                    raise ValueError("fixed_va must lie inside the common [v_min,v_max] box.")
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
        relative = (
            self.gs_model() if self.gs_model is not None else self.base_relative_constellation
        )
        variance = (
            self.va_network(transmittance, epsilon)
            if self.va_network is not None
            else torch.full_like(transmittance, self.fixed_va)
        )
        amplitudes = physical_amplitudes(probabilities, relative, variance)
        ensemble = Ensemble(
            probabilities,
            amplitudes,
            variance,
            relative,
            exact_csi_oracle=True,
            c4_symmetric=True,
        )
        ensemble.validate()
        enforce_peak_photon_constraint(ensemble, self.n_peak_photons)
        return ensemble

    def trainable_parameter_families(self) -> tuple[str, ...]:
        """Return the enabled gradient owners in frozen-spec order."""

        families: list[str] = []
        if self.ps_network is not None:
            families.append("ps")
        if self.gs_model is not None:
            families.append("gs")
        if self.va_network is not None:
            families.append("va")
        return tuple(families)


def reference_ensemble(
    kind: str,
    *,
    batch_size: int,
    modulation_variance: float,
    nu_mb: float | None = None,
    v_min: float | None = None,
    v_max: float | None = None,
    n_peak_photons: float | None = None,
    device: torch.device | str | None = None,
) -> Ensemble:
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")
    transmitter = JointTransmitter(
        kind,
        fixed_va=modulation_variance,
        v_min=v_min,
        v_max=v_max,
        nu_mb=nu_mb,
        n_peak_photons=n_peak_photons,
    )
    if device is not None:
        transmitter = transmitter.to(device=device)
    t = torch.ones(batch_size, dtype=torch.float64, device=device)
    epsilon = torch.zeros(batch_size, dtype=torch.float64, device=device)
    return transmitter(t, epsilon)
