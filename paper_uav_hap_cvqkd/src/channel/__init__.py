"""Physical HAP-to-UAV free-space optical channel."""

from .fso_channel import ChannelSamples, sample_fso_channel
from .geometry import LinkGeometry
from .pointing_error import PointingParameters

__all__ = ["ChannelSamples", "LinkGeometry", "PointingParameters", "sample_fso_channel"]

