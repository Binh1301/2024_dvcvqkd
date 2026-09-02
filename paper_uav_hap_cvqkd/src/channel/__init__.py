"""Physical HAP-to-UAV free-space optical channel."""

from .fso_channel import ChannelSamples, sample_fso_channel
from .geometry import LinkGeometry
from .pointing_error import PointingParameters
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
    "assert_disjoint_state_realizations",
    "sample_channel_state_distribution",
    "sample_fso_channel",
]
