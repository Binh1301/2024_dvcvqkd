"""FSO fading channel model for UAV-to-HAP links."""

from .channel_model import (
    channel,
    link_distance_m,
    sample_total_transmittance,
    total_transmittance,
)

__all__ = [
    "link_distance_m",
    "channel",
    "sample_total_transmittance",
    "total_transmittance",
]
