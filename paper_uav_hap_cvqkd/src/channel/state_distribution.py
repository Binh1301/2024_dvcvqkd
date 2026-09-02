"""Joint physical-transmittance/excess-noise state distribution.

The frozen propagation model supplies ``T``.  The manuscript does not supply
an empirical model linking input-referred excess noise to atmospheric fading,
so production states use an explicitly declared independent bounded-uniform
excess-noise model.  Separate namespaced random streams make that assumption
an implementation property rather than an accidental sample correlation.
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
    """Bounded input-referred excess noise in shot-noise units.

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
class ChannelStateSamples:
    """One independently generated realization of the joint state law."""

    transmittance: np.ndarray
    excess_noise_snu: np.ndarray
    fso: ChannelSamples
    base_seed: int
    transmittance_seed: int
    excess_noise_seed: int
    metadata: dict[str, Any]

    @property
    def sample_count(self) -> int:
        return int(self.transmittance.size)

    @property
    def realization_sha256(self) -> str:
        pairs = np.column_stack((self.transmittance, self.excess_noise_snu))
        return array_sha256(pairs)


def sample_channel_state_distribution(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    visibility_km: float,
    beam_waist_m: float,
    aperture_radius_m: float,
    cn2_m_minus_two_thirds: float,
    excess_noise: IndependentUniformExcessNoise,
    sample_count: int,
    seed: int,
    uav_motion: UavMotion | None = None,
) -> ChannelStateSamples:
    """Draw iid states from ``p_FSO(T) p_epsilon(epsilon)``.

    ``T`` follows the frozen HAP--UAV FSO sampler.  ``epsilon`` is sampled
    independently from ``Uniform[minimum_snu, maximum_snu]`` because neither
    the frozen equations nor the available measurements define a physical
    coupling.  A coupling may only replace this model with documented data or
    a separately justified physical noise mechanism.
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
        beam_waist_m=beam_waist_m,
        aperture_radius_m=aperture_radius_m,
        cn2_m_minus_two_thirds=cn2_m_minus_two_thirds,
        sample_count=sample_count,
        rng=np.random.default_rng(transmittance_seed),
        uav_motion=uav_motion,
    )
    epsilon = np.random.default_rng(excess_noise_seed).uniform(
        excess_noise.minimum_snu,
        excess_noise.maximum_snu,
        size=sample_count,
    ).astype(np.float64, copy=False)
    transmittance = np.asarray(fso.transmittance, dtype=np.float64)
    if not float(np.ptp(transmittance)) > 0.0:
        raise FloatingPointError("This T realization has zero variance.")
    if not float(np.ptp(epsilon)) > 0.0:
        raise FloatingPointError("This epsilon realization has zero variance.")
    pairs = np.column_stack((transmittance, epsilon))
    physical_upper = float(fso.atmospheric_transmittance * fso.pointing.t0_power)
    metadata = dict(fso.metadata)
    metadata.update(
        {
            "joint_distribution": "p_FSO(T) * Uniform(epsilon_min, epsilon_max)",
            "statistical_dependence": "T and epsilon independent by construction",
            "dependence_justification": (
                "The frozen propagation model and available manuscript provide no "
                "measured or mechanistic T-epsilon coupling."
            ),
            "temporal_model": "iid Monte Carlo states; no time correlation",
            "epsilon_units": "input-referred SNU",
            "epsilon_minimum_snu": float(excess_noise.minimum_snu),
            "epsilon_maximum_snu": float(excess_noise.maximum_snu),
            "epsilon_theoretical_variance_snu2": excess_noise.theoretical_variance_snu2,
            "transmittance_physical_upper_bound": physical_upper,
            "empirical_transmittance_variance": float(np.var(transmittance)),
            "empirical_epsilon_variance_snu2": float(np.var(epsilon)),
            "empirical_t_epsilon_correlation": float(
                np.corrcoef(transmittance, epsilon)[0, 1]
            ),
            "base_seed": seed,
            "transmittance_seed": transmittance_seed,
            "excess_noise_seed": excess_noise_seed,
            "transmittance_sha256": array_sha256(transmittance),
            "excess_noise_sha256": array_sha256(epsilon),
            "realization_sha256": array_sha256(pairs),
        }
    )
    return ChannelStateSamples(
        transmittance=transmittance,
        excess_noise_snu=epsilon,
        fso=fso,
        base_seed=seed,
        transmittance_seed=transmittance_seed,
        excess_noise_seed=excess_noise_seed,
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
            np.column_stack((sample.transmittance, sample.excess_noise_snu)),
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
