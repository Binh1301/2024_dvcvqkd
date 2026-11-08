"""Snapshot exogenous rate(q,t,scenario) once; shared destination/end-slot inputs.

Callbacks must bind one physical context and cloud realization before sampling.
No SKR backend, cloud law, or scientific scenario is selected here.
"""
from dataclasses import replace
import numpy as np
from .evaluation import Scenario
from .cloud_channel import CloudPolicy, CloudEffect, LinkSlotResult
from .hap_uav_channel import _finite


def sample_rate_provider(s: Scenario, rate_provider) -> Scenario:
    """Preserve existing binary availability; callback must exclude its erasure.

    Dynamic analog cloud results must use sample_link_provider instead, where
    retention and rates are validated together. No position-only cache is used.
    """
    rates = [[_finite(rate_provider(q.copy(), (slot+1)*s.graph.dt, s), 'SKR bits/use')
              for q in s.graph.positions] for slot in range(s.horizon)]
    return replace(s, rates=rates, z=s.z[:s.horizon])


def sample_link_provider(s: Scenario, link_provider, policy: CloudPolicy) -> Scenario:
    """Snapshot Phase4 link results with one approved, exclusive cloud policy.

    The template must have all-one z; this function owns cloud retention. Only
    m0 or zero signals are supported by DP's integer clear-slot count state.
    """
    # Reuse the policy boundary rather than silently treating a string as approval.
    CloudEffect(policy, blocked=False) if policy.mode == 'binary_erasure' else CloudEffect(policy, attenuation_factor=1.)
    if not np.all(s.z == 1):
        raise ValueError('Cloud adapter requires all-one template availability to avoid double erasure')
    rates = np.empty((s.horizon, len(s.graph.positions)))
    z = np.empty(rates.shape, dtype=np.int8)
    for slot in range(s.horizon):
        for j, q in enumerate(s.graph.positions):
            result = link_provider(q.copy(), (slot+1)*s.graph.dt, s)
            if not isinstance(result, LinkSlotResult) or result.cloud_mode != policy.mode or result.cloud_provenance != policy.provenance:
                raise ValueError('Link result must match the approved cloud policy and provenance')
            if type(result.retained_slot) is not bool:
                raise ValueError('Cloud retention must be a boolean, not a fractional valid-signal assumption')
            retained = result.retained_slot
            n = _finite(result.valid_signals, 'valid signals')
            r = _finite(result.skr_bits_per_use, 'SKR bits/use')
            transmission = _finite(result.power_transmittance, 'power transmittance')
            if not 0 <= transmission <= 1:
                raise ValueError('Power transmittance must be in [0,1]')
            if n != (s.m0 if retained else 0.):
                raise ValueError('Valid signals must be m0 or zero; fractional counts require a different DP state')
            if policy.mode == 'optical_attenuation' and not retained:
                raise ValueError('Optical attenuation cannot also apply cloud erasure')
            if not retained and (r != 0. or transmission != 0.):
                raise ValueError('Binary erased slot must have zero contribution and transmission')
            rates[slot, j], z[slot, j] = r, int(retained)
    return replace(s, rates=rates, z=z)
