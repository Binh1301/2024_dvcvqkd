"""Diameter parameter adapter for the unchanged saved optical/homodyne model."""
from functools import lru_cache
import math
from pathlib import Path
import sys
from types import FunctionType
import numpy as np
from scipy.special import roots_hermitenorm
from scipy.stats import ncx2

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'results/positive_skr_without_receiver_enlargement_20261022'))
import numeric as saved
previous=saved.previous


@lru_cache(512)
def optical(diameter,divergence,jitter,sigma,angle):
    if not .08<=diameter<=.55:raise ValueError('Diameter outside diagnostic domain')
    # Propagation is aperture independent in the existing model; collection uses Dr.
    ch0,mo0=saved.optical(20.,1.,angle,divergence,jitter,sigma,.92)
    ch={**ch0,'D_r':diameter}
    return ch,mo0 if diameter==.08 else previous.power_conserving(ch)


@lru_cache(96)
def optical_quadrature(diameter,divergence,jitter,sigma,angle,radial,width_order):
    ch,_=optical(diameter,divergence,jitter,sigma,angle)
    u,wu=np.polynomial.legendre.leggauss(radial);u=(u+1)/2;wu=wu/2
    z,wz=roots_hermitenorm(width_order);wz/=math.sqrt(2*math.pi)
    width=ch['w_eff_m']*np.exp(-(-float(ch['v'])/2+math.sqrt(float(ch['v']))*z)/2)
    t=ch['eta_atm']*ncx2.cdf((diameter/width[:,None])**2,2,8*ch['sigma_s_m']**2*(-np.log(u))[None,:]/width[:,None]**2)
    p=(float(ch['P1'])*np.outer(wz,wu)).ravel();t=np.r_[t.ravel(),0.];p=np.r_[p,float(ch['P0'])]
    unique,index=np.unique(t,return_inverse=True);weights=np.bincount(index,weights=p)
    assert abs(weights.sum()-1)<1e-13 and 0<=unique.min()<=unique.max()<=ch['eta_atm']<=1
    return unique,weights


def quadrature(parameters,radial,width_order):
    hH,hU,angle,div,jt,sigma,eta,noise,tau,diameter=parameters
    assert (hH,hU,tau)==(20.,1.,.92)
    return optical_quadrature(diameter,div,jt,sigma,angle,radial,width_order)


# Reuse identical MI bytecode, changing only its aperture-aware quadrature input.
_globals={**saved.fading_mi.__globals__,'quadrature':quadrature}
fading_mi=FunctionType(saved.fading_mi.__code__,_globals,'fading_mi',saved.fading_mi.__defaults__)


def evaluate(candidate,parameters,radial=128,width_order=16):
    hH,hU,angle,div,jt,sigma,eta,noise,tau,diameter=parameters
    assert (hH,hU,tau)==(20.,1.,.92) and eta in [.8,.85,.9,.95] and noise in [.0135,.005]
    ch,mo=optical(diameter,div,jt,sigma,angle)
    security=previous.evaluate(candidate,mo,eta_det=eta,epsilon_det=noise,order=64,grid=33)
    actual=fading_mi(candidate,parameters,radial,width_order)
    return {**{k:float(v) if hasattr(v,'_mpf_') else v for k,v in ch.items()},**mo,**security,
        'I_AB_surrogate':security['I_AB'],'K_surrogate':security['K_raw'],**actual,
        'I_AB':actual['I_AB_actual'],'beta_I_AB':.95*actual['I_AB_actual'],
        'K_raw':.95*actual['I_AB_actual']-security['chi_BE'],
        'hardware_validated':False,'source_status':'BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
        'rate_per':'transmitted_use_including_outage'}
