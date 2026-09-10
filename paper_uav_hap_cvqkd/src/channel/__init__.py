"""Physical HAP-to-UAV free-space optical channel."""

from .aoa import (
    UnsupportedTurbulenceAoAError,
    aoa_inlier_probability,
    aoa_orientation_variance_rad2,
    aoa_outage_probability,
    aoa_variance_rad2,
    sample_aoa_gate,
)
from .fso_channel import (
    ChannelSamples,
    TransmittanceDomainError,
    compose_raw_transmittance,
    physicalize_raw_transmittance,
    sample_fso_channel,
)
from .diagnostics import composite_transmittance_diagnostics
from .geometry import LinkGeometry
from .phase_noise import (
    phase_coefficient_from_parameters,
    phase_distortion_variance,
    phase_excess_noise,
    phase_parameter_provenance,
    phase_noise_coefficient,
    total_excess_noise,
)
from .pointing_error import PointingParameters
from .scintillation import (
    UnsupportedApertureAveragingError,
    normalized_lognormal_samples,
    resolve_scintillation_variance,
    rytov_variance_from_profile,
)
from .state_distribution import (
    ChannelStateSamples,
    IndependentUniformExcessNoise,
    assert_disjoint_state_realizations,
    sample_channel_state_distribution,
)

__all__ = [
    "ChannelSamples",
    "ChannelStateSamples",
    "IndependentUniformExcessNoise",
    "LinkGeometry",
    "PointingParameters",
    "TransmittanceDomainError",
    "UnsupportedApertureAveragingError",
    "UnsupportedTurbulenceAoAError",
    "aoa_inlier_probability",
    "aoa_orientation_variance_rad2",
    "aoa_outage_probability",
    "aoa_variance_rad2",
    "assert_disjoint_state_realizations",
    "compose_raw_transmittance",
    "composite_transmittance_diagnostics",
    "normalized_lognormal_samples",
    "phase_coefficient_from_parameters",
    "phase_distortion_variance",
    "phase_excess_noise",
    "phase_parameter_provenance",
    "phase_noise_coefficient",
    "physicalize_raw_transmittance",
    "resolve_scintillation_variance",
    "rytov_variance_from_profile",
    "sample_aoa_gate",
    "sample_channel_state_distribution",
    "sample_fso_channel",
    "total_excess_noise",
]
