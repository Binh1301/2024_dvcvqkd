"""Explicit approved cloud policies; no CLWC-to-extinction conversion invented."""
from dataclasses import dataclass
from typing import Callable
from .blockage import BlockageModel
from .hap_uav_channel import FadingMoments,effective_channel,make_skr_request,_finite


@dataclass(frozen=True)
class CloudPolicy:
    mode: str
    author_approved: bool
    provenance: str


@dataclass(frozen=True)
class CloudEffect:
    policy: CloudPolicy
    blocked: bool | None = None
    attenuation_factor: float | None = None

    def __post_init__(self):
        if self.policy.author_approved is not True or not self.policy.provenance:
            raise ValueError('Cloud policy must be explicitly author-approved with provenance')
        if self.policy.mode=='binary_erasure':
            if type(self.blocked) is not bool or self.attenuation_factor is not None:
                raise ValueError('Binary erasure requires deterministic blockage only; modes are exclusive')
        elif self.policy.mode=='optical_attenuation':
            if self.blocked is not None:raise ValueError('Attenuation and erasure fields are mutually exclusive')
            factor=_finite(self.attenuation_factor,'sourced power attenuation factor')
            if not 0<factor<=1:raise ValueError('Partial attenuation factor must lie in (0,1]; define opaque outage via an approved erasure policy')
        else:
            raise ValueError('Cloud mode must be binary_erasure or optical_attenuation')


def cloud_blockage_effect(model:BlockageModel,position,time,policy:CloudPolicy):
    if policy.mode!='binary_erasure':raise ValueError('Existing CLWC/LOS blockage supplies binary erasure, not an extinction coefficient')
    return CloudEffect(policy,blocked=model.blocked(position,time))


@dataclass(frozen=True)
class LinkSlotResult:
    valid_signals: float
    skr_bits_per_use: float
    power_transmittance: float
    retained_slot: bool
    cloud_mode: str
    cloud_provenance: str
    backend_metadata: dict


def evaluate_link_slot(geometry,Vmod,m0,beta,moment_provider:Callable,skr_backend:Callable,
                       cloud_effect:CloudEffect,*,attenuated_moment_provider:Callable | None=None):
    """Connect existing providers. No backend/model is chosen or enabled silently.

    Binary opaque-cloud blockage means erasure: no channel/SKR call and no kept
    signals. Analog attenuation leaves m0 unchanged and requires a provider for
    POST-loss moments/noise, since detector/input-noise scaling is not specified.
    """
    signals=_finite(m0,'m0 valid signals per clear slot')
    if signals<=0:raise ValueError('m0 must be positive')
    mode=cloud_effect.policy.mode
    if mode=='binary_erasure' and cloud_effect.blocked:
        return LinkSlotResult(0.,0.,0.,False,mode,cloud_effect.policy.provenance,
                              {'evaluation':'not called: deterministic cloud erasure'})
    if mode=='optical_attenuation':
        if attenuated_moment_provider is None:
            raise ValueError('Attenuation requires an explicit post-loss moment/noise provider; no noise scaling is assumed')
        moments=attenuated_moment_provider(geometry,cloud_effect.attenuation_factor)
    else:
        moments=moment_provider(geometry)
    if not isinstance(moments,FadingMoments):raise ValueError('Existing moment provider must return the declared FadingMoments interface')
    channel=effective_channel(moments,Vmod)
    if channel.power_transmittance==0:
        return LinkSlotResult(signals,0.,0.,True,mode,cloud_effect.policy.provenance,
                              {'evaluation':'zero base transmission; cloud eligible-slot count unchanged'})
    result=skr_backend(make_skr_request(channel,beta))
    rate=_finite(result.get('K_raw'),'backend K_raw bits/use')
    return LinkSlotResult(signals,rate,channel.power_transmittance,True,mode,
                          cloud_effect.policy.provenance,result)
