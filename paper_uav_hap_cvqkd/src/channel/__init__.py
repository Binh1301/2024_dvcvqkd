"""Physical HAP-to-UAV free-space optical channel."""

from .fso_channel import ChannelSamples, sample_fso_channel
from .geometry import LinkGeometry
from .phase_noise import (
    PhaseNoiseScenario,
    optical_wavenumber_per_m,
    phase_distortion_variance,
    phase_excess_noise,
    phase_noise_coefficient,
    phase_noise_scenario,
    phase_noise_scenario_from_channel_config,
    phase_noise_scenario_sha256,
    total_excess_noise,
    validate_phase_noise_scenario_binding,
)
from .pointing_error import PointingParameters
from .state_distribution import (
    ChannelStateSamples,
    IndependentUniformBaselineNoise,
    assert_disjoint_state_realizations,
    sample_channel_state_distribution,
)

__all__ = [
    "ChannelSamples",
    "ChannelStateSamples",
    "IndependentUniformBaselineNoise",
    "LinkGeometry",
    "PhaseNoiseScenario",
    "PointingParameters",
    "assert_disjoint_state_realizations",
    "optical_wavenumber_per_m",
    "phase_distortion_variance",
    "phase_excess_noise",
    "phase_noise_coefficient",
    "phase_noise_scenario",
    "phase_noise_scenario_from_channel_config",
    "phase_noise_scenario_sha256",
    "sample_channel_state_distribution",
    "sample_fso_channel",
    "total_excess_noise",
    "validate_phase_noise_scenario_binding",
]
