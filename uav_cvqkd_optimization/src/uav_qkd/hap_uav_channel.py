"""Source-A geometry and moment/SKR boundary; existing QAM/Z/w stay opaque."""
from dataclasses import dataclass,replace
import hashlib
import importlib.util
import math
from numbers import Real
from pathlib import Path
import sys
from typing import Callable
import numpy as np
from .config import load_config

PARENT = Path(__file__).resolve().parents[3]/'paper_uav_hap_cvqkd'
NORMALIZATION = 'VA=Vmod=2*nbar'


def _finite(value, name, *, minimum=None):
    if value is None or isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f'{name} requires an explicit finite value')
    if minimum is not None and value < minimum:
        raise ValueError(f'{name} must be >= {minimum}')
    return float(value)


def load_channel_reference(path):
    c=load_config(path)
    positive=('hap_altitude_m','uav_altitude_m','beam_full_divergence_rad','wavelength_m',
              'transmitter_jitter_angle_rad','receiver_aperture_diameter_m','uav_position_sd_m',
              'uav_angular_fluctuation_sd_rad','receiver_fov_half_angle_rad',
              'atmospheric_altitude_m','ground_turbulence_cn2_m_minus_2_3','rms_wind_speed_m_s')
    for name in positive:
        if _finite(c.get(name),name,minimum=0)<=0:
            raise ValueError(f'{name} must be positive in the reference configuration')
    if c['hap_altitude_m']<=c['uav_altitude_m']:
        raise ValueError('HAP altitude must exceed UAV altitude')
    angle=_finite(c.get('reference_zenith_angle_deg'),'reference_zenith_angle_deg')
    if not 0<=angle<90:
        raise ValueError('Reference zenith angle must lie in [0,90) degrees')
    for name in ('boresight_x_m','boresight_y_m'):_finite(c.get(name),name)
    for name in ('zenith_atmospheric_transmittance','reconciliation_efficiency'):
        if not 0<_finite(c.get(name),name)<=1:raise ValueError(f'{name} must lie in (0,1]')
    if c['existing_module_normalization']!=NORMALIZATION:
        raise ValueError('Module variance mapping needs an explicit author decision; core formulas are unchanged')
    curvature=c['wavefront_curvature_radius_m']
    if curvature!='infinity' and (isinstance(curvature,bool) or not isinstance(curvature,Real) or not math.isfinite(curvature) or curvature<=0):
        raise ValueError('Wavefront curvature must be explicitly infinity or a positive finite radius in meters')
    for name in ('channel_excess_noise_snu','detector_excess_noise_snu'):
        if c.get(name) is not None:_finite(c[name],name,minimum=0)
    if c.get('detector_efficiency') is not None and not 0<_finite(c['detector_efficiency'],'detector_efficiency')<=1:
        raise ValueError('Detector efficiency, if declared, must lie in (0,1]')
    return c


def _existing_helper(filename, repository_root):
    """Load only existing pure geometry/loss helpers, without importing a solver."""
    path=Path(repository_root)/'src/channel'/filename
    if not path.is_file():raise FileNotFoundError(f'Required existing channel helper missing: {path}')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    name='_uav_qkd_existing_'+path.stem+'_'+digest[:16]
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name], str(path.resolve()), digest


@dataclass(frozen=True)
class LinkGeometryState:
    slant_distance_m: float
    zenith_angle_rad: float
    atmospheric_transmittance: float
    geometry_mode: str
    producer_sha256: dict
    hap_altitude_m: float
    uav_altitude_m: float
    zenith_atmospheric_transmittance: float
    hap_horizontal_m: tuple | None = None
    uav_horizontal_m: tuple | None = None


def _angle_geometry(h_hap, h_uav, angle, tau, mode, repository_root):
    geometry,path,gsha=_existing_helper('geometry.py',repository_root)
    loss,lpath,lsha=_existing_helper('atmospheric_loss.py',repository_root)
    native=geometry.LinkGeometry(h_hap_m=h_hap,h_uav_m=h_uav,zenith_angle_rad=angle)
    length=native.link_length_m
    transmittance=loss.atmospheric_transmittance_from_tau_zen(length,tau,angle)
    return LinkGeometryState(length,angle,transmittance,mode,{path:gsha,lpath:lsha},h_hap,h_uav,float(tau))


def reference_geometry(config, *, repository_root=PARENT):
    """Independent 30-degree reference; no horizontal HAP coordinates inferred."""
    return _angle_geometry(config['hap_altitude_m'],config['uav_altitude_m'],
                           math.radians(config['reference_zenith_angle_deg']),
                           config['zenith_atmospheric_transmittance'],'reference_angle',repository_root)


def waypoint_geometry(hap_position_m,uav_horizontal_m,uav_altitude_m,tau_zen,*,repository_root=PARENT):
    if hap_position_m is None:raise ValueError('HAP position is required; no horizontal coordinates are assumed')
    hap=np.asarray(hap_position_m,float);q=np.asarray(uav_horizontal_m,float)
    if hap.shape!=(3,) or q.shape!=(2,) or not np.isfinite(hap).all() or not np.isfinite(q).all():
        raise ValueError('HAP requires finite xyz and UAV requires finite horizontal xy in meters')
    altitude=_finite(uav_altitude_m,'UAV altitude')
    if hap[2]<=altitude:raise ValueError('HAP altitude must exceed UAV altitude')
    angle=math.atan2(float(np.linalg.norm(q-hap[:2])),float(hap[2]-altitude))
    state=_angle_geometry(float(hap[2]),altitude,angle,tau_zen,'coordinate_derived',repository_root)
    return replace(state,hap_horizontal_m=tuple(float(x) for x in hap[:2]),uav_horizontal_m=tuple(float(x) for x in q))


@dataclass(frozen=True)
class FadingMoments:
    mean_eta: float
    mean_sqrt_eta: float
    mean_eta_xi: float
    provenance: str
    probability_mass: float | None = None

    def __post_init__(self):
        m1=_finite(self.mean_eta,'E[eta]',minimum=0)
        mh=_finite(self.mean_sqrt_eta,'E[sqrt(eta)]',minimum=0)
        _finite(self.mean_eta_xi,'E[eta*xi]',minimum=0)
        tol=32*np.finfo(float).eps
        if m1>1 or mh>1 or m1>mh+tol or mh*mh>m1+tol:
            raise ValueError('Moment domain requires mh^2 <= m1 <= mh <=1 for power eta in [0,1]')
        if not self.provenance:raise ValueError('Moment provenance is required')
        if self.probability_mass is not None:
            mass=_finite(self.probability_mass,'retained probability mass',minimum=0)
            if mass>1+tol or mh>mass+tol or mh*mh>mass*m1+tol:
                raise ValueError('Moment/retained mass domain is inconsistent; no normalization is applied')

    @classmethod
    def from_existing_v43(cls,moments,*,xi_ch,xi_det,provenance):
        """Consume existing Eq18–20 outputs; no source moments are recalculated."""
        ch=_finite(xi_ch,'xi_ch',minimum=0);det=_finite(xi_det,'xi_det',minimum=0)
        mass=_finite(moments['M0'],'M0 retained mass',minimum=0)
        return cls(float(moments['m1']),float(moments['mh']),
                   ch*float(moments['m1'])+det*mass,provenance,mass)


class ExistingMomentProvider:
    """Connect existing physical and Eq18–20 callbacks without replacing them.

    The caller binds the exact existing backend/conventions. No default optical
    engine, detector model, noise value, PDF normalization or source solver is
    selected by this interface.
    """
    def __init__(self,config,physical_provider:Callable,moment_provider:Callable,provenance:str):
        if not callable(physical_provider) or not callable(moment_provider) or not provenance:
            raise ValueError('Existing physical/moment providers and provenance must be explicit')
        self.config,self.physical_provider,self.moment_provider,self.provenance=config,physical_provider,moment_provider,provenance

    def __call__(self,geometry:LinkGeometryState):
        for field in ('hap_altitude_m','uav_altitude_m','zenith_atmospheric_transmittance'):
            if not np.isclose(getattr(geometry,field),self.config[field],rtol=1e-12,atol=1e-14):
                raise ValueError(f'Channel geometry/config altitude or tau mismatch: {field}')
        if geometry.geometry_mode=='coordinate_derived' and (geometry.hap_horizontal_m is None or geometry.uav_horizontal_m is None):
            raise ValueError('Coordinate-derived geometry must retain its explicit horizontal positions')
        configured_hap=self.config.get('hap_horizontal_m')
        if configured_hap is not None and geometry.hap_horizontal_m is not None and not np.allclose(configured_hap,geometry.hap_horizontal_m,rtol=0,atol=1e-10):
            raise ValueError('Configured HAP horizontal position differs from the geometry')
        ch=_finite(self.config.get('channel_excess_noise_snu'),'xi_ch noise',minimum=0)
        det=_finite(self.config.get('detector_excess_noise_snu'),'xi_det noise',minimum=0)
        request={k:v for k,v in self.config.items() if k not in ('_config_path','reference_zenith_angle_deg')}
        request.update(slant_distance_m=geometry.slant_distance_m,zenith_angle_rad=geometry.zenith_angle_rad,
                       zenith_angle_deg=math.degrees(geometry.zenith_angle_rad),
                       atmospheric_transmittance=geometry.atmospheric_transmittance,
                       geometry_mode=geometry.geometry_mode,
                       hap_horizontal_m=list(geometry.hap_horizontal_m) if geometry.hap_horizontal_m is not None else None,
                       uav_horizontal_m=list(geometry.uav_horizontal_m) if geometry.uav_horizontal_m is not None else None)
        native=self.physical_provider(request)
        moments=self.moment_provider(native)
        return FadingMoments.from_existing_v43(moments,xi_ch=ch,xi_det=det,provenance=self.provenance)


@dataclass(frozen=True)
class EffectiveChannelState:
    power_transmittance: float
    amplitude_gain: float
    output_excess_noise: float
    input_excess_noise: float | None
    modulation_variance: float
    variance_sqrt_eta: float
    variance_roundoff_adjustment: bool
    moment_provenance: str
    normalization: str = NORMALIZATION


def effective_channel(moments:FadingMoments,Vmod:float):
    """Eq17 boundary arithmetic only. No MI/Holevo/Z/w implementation here."""
    variance=_finite(Vmod,'Vmod',minimum=0)
    if variance<=0:raise ValueError('Vmod must be positive')
    transmission=moments.mean_sqrt_eta**2
    raw_variance=moments.mean_eta-transmission
    # Only a recorded machine-roundoff residual can be set to zero; T remains mh².
    fading_variance=max(0.,raw_variance)
    noise=_finite(fading_variance*variance+moments.mean_eta_xi,'effective output excess noise',minimum=0)
    input_noise=_finite(noise/transmission,'effective input excess noise',minimum=0) if transmission>0 else None
    return EffectiveChannelState(transmission,moments.mean_sqrt_eta,noise,
                                  input_noise,variance,
                                  fading_variance,raw_variance<0,moments.provenance)


@dataclass(frozen=True)
class SKRRequest:
    power_transmittance: float
    input_excess_noise: float
    modulation_variance: float
    beta: float
    normalization: str


def make_skr_request(effective:EffectiveChannelState,beta:float):
    efficiency=_finite(beta,'beta')
    if not 0<efficiency<=1:raise ValueError('beta must lie in (0,1]')
    if effective.power_transmittance<=0:raise ValueError('Zero-transmission channel has no positive-transmission SKR request')
    return SKRRequest(effective.power_transmittance,effective.input_excess_noise,
                      effective.modulation_variance,efficiency,effective.normalization)


def bind_existing_mb_backend(evaluator:Callable,source:dict,context:dict,protocol:dict):
    """Adapt the existing evaluate(source,context,protocol) signature unchanged.

    Source is opaque, including accepted C/w, operators and matrices. This only
    validates scalar I/O mapping; native backend guards and metadata are retained.
    """
    if not callable(evaluator):raise ValueError('An existing MB evaluator callable is required')
    if str(protocol.get('source_normalization','')).split(';',1)[0].strip()!=NORMALIZATION:
        raise ValueError('The documented existing modulation normalization must be explicit')
    def evaluate(request:SKRRequest):
        if request.normalization!=NORMALIZATION or request.modulation_variance!=source['VA']:
            raise ValueError('Source/consumer VA/Vmod interface mapping mismatch')
        if request.beta!=protocol['beta']:raise ValueError('Backend/request beta mismatch')
        moments=FadingMoments.from_existing_v43(context['moments'],xi_ch=protocol['xi_ch'],
                     xi_det=protocol['xi_det'],provenance='existing native context, unchanged')
        expected=effective_channel(moments,source['VA'])
        if not np.allclose([request.power_transmittance,request.input_excess_noise],
                           [expected.power_transmittance,expected.input_excess_noise],rtol=1e-12,atol=1e-14):
            raise ValueError('Channel/SKR scalar input interface mismatch')
        result=evaluator(source,context,protocol)
        _finite(result.get('K_raw'),'existing backend K_raw')
        for key,value in [('eta_f',request.power_transmittance),('xi_f',request.input_excess_noise)]:
            if key in result and not np.isclose(result[key],value,rtol=1e-12,atol=1e-14):
                raise ValueError(f'Existing backend {key} output differs from its scalar request')
        return result
    return evaluate
