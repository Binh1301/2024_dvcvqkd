"""Joint composite-channel/pre-action-noise state distribution.

The channel sampler supplies physical ``T`` from the composite optical model.
The baseline may use a fixed author-approved channel excess noise, while the
legacy independent bounded-uniform model remains available for alternatives.
Separate namespaced random streams keep stochastic alternatives reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from src.utils.random import array_sha256, derive_seed

from .fso_channel import ChannelSamples, sample_fso_channel
from .geometry import LinkGeometry
from .turbulence import UavMotion


@dataclass(frozen=True)
class IndependentUniformExcessNoise:
    """Bounded input-referred pre-action excess noise in shot-noise units.

    This is a declared simulation distribution, not a measured atmospheric
    law.  Bounds are therefore mandatory experiment parameters and must be
    frozen without consulting test-set performance.
    """

    minimum_snu: float
    maximum_snu: float

    def validate(self) -> None:
        values = np.asarray((self.minimum_snu, self.maximum_snu), dtype=np.float64)
        if np.any(~np.isfinite(values)):
            raise ValueError("Excess-noise bounds must be finite.")
        if self.minimum_snu < 0.0:
            raise ValueError("minimum_snu must be nonnegative.")
        if self.maximum_snu <= self.minimum_snu:
            raise ValueError(
                "maximum_snu must exceed minimum_snu so epsilon genuinely varies."
            )

    @property
    def theoretical_variance_snu2(self) -> float:
        self.validate()
        return float((self.maximum_snu - self.minimum_snu) ** 2 / 12.0)


@dataclass(frozen=True)
class FixedExcessNoise:
    """Deterministic input-referred baseline channel excess noise."""

    value_snu: float

    def validate(self) -> None:
        if not np.isfinite(self.value_snu) or self.value_snu < 0.0:
            raise ValueError("value_snu must be finite and nonnegative.")

    @property
    def minimum_snu(self) -> float:
        self.validate()
        return float(self.value_snu)

    @property
    def maximum_snu(self) -> float:
        self.validate()
        return float(self.value_snu)

    @property
    def theoretical_variance_snu2(self) -> float:
        self.validate()
        return 0.0


@dataclass(frozen=True)
class ChannelStateSamples:
    """One independently generated realization of the joint state law."""

    transmittance: np.ndarray
    epsilon_base_snu: np.ndarray
    fso: ChannelSamples
    base_seed: int
    transmittance_seed: int
    epsilon_base_seed: int
    metadata: dict[str, Any]

    @property
    def sample_count(self) -> int:
        return int(self.transmittance.size)

    @property
    def active_mask(self) -> np.ndarray:
        """States eligible for the policy feature ``log10(T)``."""

        return self.transmittance > 0.0

    @property
    def outage_mask(self) -> np.ndarray:
        """Hard AoA outage states, which carry zero key rate."""

        return ~self.active_mask

    @property
    def excess_noise_snu(self) -> np.ndarray:
        """Legacy alias for the pre-action epsilon field."""

        return self.epsilon_base_snu

    @property
    def excess_noise_seed(self) -> int:
        """Legacy alias for the pre-action noise stream seed."""

        return self.epsilon_base_seed

    @property
    def realization_sha256(self) -> str:
        pairs = np.column_stack((self.transmittance, self.epsilon_base_snu))
        return array_sha256(pairs)


def sample_channel_state_distribution(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    visibility_km: float | None = None,
    tau_zen: float | None = None,
    beam_waist_m: float,
    aperture_radius_m: float,
    cn2_m_minus_two_thirds: float,
    excess_noise: IndependentUniformExcessNoise | FixedExcessNoise,
    sample_count: int,
    seed: int,
    uav_motion: UavMotion | None = None,
    radius_of_curvature_m: float = np.inf,
    theta_div_rad: float | None = None,
    pointing_model: str = "generalized_gaussian",
    scintillation_log_variance: float | None = None,
    v_sc_override: float | None = None,
    aperture_averaging_model: str | None = "disabled",
    turbulence_profile_heights_m: np.ndarray | None = None,
    turbulence_profile_cn2_m_minus_two_thirds: np.ndarray | None = None,
    sigma_R0_squared: float | None = None,
    turbulence_profile_model: str | None = None,
    wind_speed_m_per_s: float | None = None,
    ground_cn2_m_minus_two_thirds: float | None = None,
    boresight_x_m: float = 0.0,
    boresight_y_m: float = 0.0,
    sigma_hap_ang_rad: float = 0.0,
    hap_angular_jitter_convention: str = "per_axis",
    aoa_model: str = "disabled",
    sigma_turb_AoA2: float | None = None,
    turbulence_aoa_provenance: str | None = None,
    theta_fov_rad: float | None = None,
) -> ChannelStateSamples:
    """Draw iid states from ``p_composite(T) p_epsilon_base(epsilon_base)``.

    ``T`` follows the physical HAP--UAV composite sampler.  The baseline uses
    a deterministic ``FixedExcessNoise`` value; the legacy alternative samples
    independently from ``Uniform[minimum_snu, maximum_snu]``.
    """

    if not isinstance(sample_count, int) or sample_count < 2:
        raise ValueError("Joint channel realizations require sample_count >= 2.")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
    excess_noise.validate()
    transmittance_seed = derive_seed(seed, "joint_state_transmittance")
    excess_noise_seed = derive_seed(seed, "joint_state_excess_noise")
    fso = sample_fso_channel(
        geometry=geometry,
        wavelength_m=wavelength_m,
        visibility_km=visibility_km,
        tau_zen=tau_zen,
        beam_waist_m=beam_waist_m,
        radius_of_curvature_m=radius_of_curvature_m,
        theta_div_rad=theta_div_rad,
        pointing_model=pointing_model,
        aperture_radius_m=aperture_radius_m,
        cn2_m_minus_two_thirds=cn2_m_minus_two_thirds,
        sample_count=sample_count,
        rng=np.random.default_rng(transmittance_seed),
        uav_motion=uav_motion,
        scintillation_log_variance=scintillation_log_variance,
        v_sc_override=v_sc_override,
        aperture_averaging_model=aperture_averaging_model,
        turbulence_profile_heights_m=turbulence_profile_heights_m,
        turbulence_profile_cn2_m_minus_two_thirds=(
            turbulence_profile_cn2_m_minus_two_thirds
        ),
        sigma_R0_squared=sigma_R0_squared,
        turbulence_profile_model=turbulence_profile_model,
        wind_speed_m_per_s=wind_speed_m_per_s,
        ground_cn2_m_minus_two_thirds=ground_cn2_m_minus_two_thirds,
        boresight_x_m=boresight_x_m,
        boresight_y_m=boresight_y_m,
        sigma_hap_ang_rad=sigma_hap_ang_rad,
        hap_angular_jitter_convention=hap_angular_jitter_convention,
        aoa_model=aoa_model,
        sigma_turb_AoA2=sigma_turb_AoA2,
        turbulence_aoa_provenance=turbulence_aoa_provenance,
        theta_fov_rad=theta_fov_rad,
    )
    if isinstance(excess_noise, FixedExcessNoise):
        epsilon_base = np.full(
            sample_count, excess_noise.value_snu, dtype=np.float64
        )
        joint_distribution = "p_FSO(T) * delta(epsilon_base-epsilon_ch)"
        statistical_dependence = "epsilon_base fixed by baseline input"
        dependence_justification = "Author-approved deterministic baseline channel excess noise."
        epsilon_model = "fixed"
    else:
        epsilon_base = np.random.default_rng(excess_noise_seed).uniform(
            excess_noise.minimum_snu,
            excess_noise.maximum_snu,
            size=sample_count,
        ).astype(np.float64, copy=False)
        joint_distribution = "p_FSO(T) * Uniform(epsilon_base_min, epsilon_base_max)"
        statistical_dependence = "T and epsilon_base independent by construction"
        dependence_justification = (
            "The frozen propagation model and available manuscript provide no "
            "measured or mechanistic T-epsilon_base coupling."
        )
        epsilon_model = "independent_uniform"
    transmittance = np.asarray(fso.transmittance, dtype=np.float64)
    if (
        isinstance(excess_noise, IndependentUniformExcessNoise)
        and not float(np.ptp(epsilon_base)) > 0.0
    ):
        raise FloatingPointError("This epsilon_base realization has zero variance.")
    pairs = np.column_stack((transmittance, epsilon_base))
    physical_upper = float(fso.metadata.get("physical_support_upper", 1.0))
    metadata = dict(fso.metadata)
    metadata.update(
        {
            "joint_distribution": joint_distribution,
            "statistical_dependence": statistical_dependence,
            "dependence_justification": dependence_justification,
            "epsilon_model": epsilon_model,
            "temporal_model": "iid Monte Carlo states; no time correlation",
            "epsilon_base_units": "input-referred SNU",
            "epsilon_base_minimum_snu": float(excess_noise.minimum_snu),
            "epsilon_base_maximum_snu": float(excess_noise.maximum_snu),
            "epsilon_base_theoretical_variance_snu2": excess_noise.theoretical_variance_snu2,
            "epsilon_units": "input-referred SNU",
            "epsilon_minimum_snu": float(excess_noise.minimum_snu),
            "epsilon_maximum_snu": float(excess_noise.maximum_snu),
            "epsilon_theoretical_variance_snu2": excess_noise.theoretical_variance_snu2,
            "transmittance_physical_upper_bound": physical_upper,
            "raw_transmittance_sha256": (
                None
                if fso.raw_transmittance is None
                else array_sha256(fso.raw_transmittance)
            ),
            "scintillation_factor_sha256": (
                None
                if fso.scintillation_factor is None
                else array_sha256(fso.scintillation_factor)
            ),
            "aoa_gate_sha256": (
                None if fso.aoa_gate is None else array_sha256(fso.aoa_gate)
            ),
            "p_out": fso.metadata.get("p_out"),
            "p_in": fso.metadata.get("p_in"),
            "p_out_analytic": fso.metadata.get("p_out_analytic"),
            "p_above_one": fso.metadata.get("p_above_one"),
            "raw_mean_T": fso.metadata.get("raw_mean_T"),
            "physical_mean_T": fso.metadata.get("physical_mean_T"),
            "delta_T": fso.metadata.get("delta_T"),
            "raw_identity_mean_T": fso.metadata.get("raw_identity_mean_T"),
            "channel_provenance": fso.metadata.get("provenance"),
            "empirical_transmittance_variance": float(np.var(transmittance)),
            "empirical_epsilon_base_variance_snu2": float(np.var(epsilon_base)),
            "empirical_epsilon_variance_snu2": float(np.var(epsilon_base)),
            "empirical_t_epsilon_correlation": (
                None
                if isinstance(excess_noise, FixedExcessNoise)
                else float(np.corrcoef(transmittance, epsilon_base)[0, 1])
            ),
            "base_seed": seed,
            "transmittance_seed": transmittance_seed,
            "epsilon_base_seed": excess_noise_seed,
            "excess_noise_seed": excess_noise_seed,
            "transmittance_sha256": array_sha256(transmittance),
            "epsilon_base_sha256": array_sha256(epsilon_base),
            "excess_noise_sha256": array_sha256(epsilon_base),
            "realization_sha256": array_sha256(pairs),
        }
    )
    return ChannelStateSamples(
        transmittance=transmittance,
        epsilon_base_snu=epsilon_base,
        fso=fso,
        base_seed=seed,
        transmittance_seed=transmittance_seed,
        epsilon_base_seed=excess_noise_seed,
        metadata=metadata,
    )


def assert_disjoint_state_realizations(
    named_samples: Iterable[tuple[str, ChannelStateSamples]],
) -> None:
    """Fail if named splits reuse a seed, full realization, or exact state pair."""

    samples = list(named_samples)
    names = [name for name, _ in samples]
    if len(names) != len(set(names)):
        raise ValueError("Split names must be unique.")
    seeds = [sample.base_seed for _, sample in samples]
    if len(seeds) != len(set(seeds)):
        raise ValueError("Channel-state split seeds must be distinct.")
    fingerprints = [sample.realization_sha256 for _, sample in samples]
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("Channel-state splits reuse a complete realization.")
    pair_sets: list[set[bytes]] = []
    for _, sample in samples:
        pairs = np.ascontiguousarray(
            np.column_stack((sample.transmittance, sample.epsilon_base_snu)),
            dtype=np.float64,
        )
        pair_sets.append({row.tobytes() for row in pairs})
    for left in range(len(samples)):
        for right in range(left + 1, len(samples)):
            overlap = pair_sets[left].intersection(pair_sets[right])
            if overlap:
                raise ValueError(
                    f"Channel-state realization leakage between {names[left]} and "
                    f"{names[right]}."
                )
