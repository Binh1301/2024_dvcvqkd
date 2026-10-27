"""Reuse the accepted passive optical and homodyne/full-Z diagnostic unchanged."""
from functools import lru_cache
import math
from pathlib import Path
import sys
import numpy as np
from scipy.special import roots_hermitenorm
from scipy.stats import ncx2

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
PRIOR=ROOT/'results/untrusted_positive_skr_feasibility_20261022'
sys.path.insert(0,str(PRIOR))
import model as previous


@lru_cache(maxsize=64)
def optical(diameter,divergence,jitter,sigma):
    ch=previous.optical(diameter,divergence,30,sigma,jitter/15.61)
    mo=previous.power_conserving(ch)
    return ch,mo


@lru_cache(maxsize=64)
def quadrature(diameter,divergence,jitter,sigma,radial,width_order):
    ch,_=optical(diameter,divergence,jitter,sigma)
    u,wu=np.polynomial.legendre.leggauss(radial);u=(u+1)/2;wu=wu/2
    z,wz=roots_hermitenorm(width_order);wz/=math.sqrt(2*math.pi)
    width=ch['w_eff_m']*np.exp(-(-float(ch['v'])/2+math.sqrt(float(ch['v']))*z)/2)
    t=ch['eta_atm']*ncx2.cdf((diameter/width[:,None])**2,2,
        8*ch['sigma_s_m']**2*(-np.log(u))[None,:]/width[:,None]**2)
    p=(float(ch['P1'])*np.outer(wz,wu)).ravel()
    t=np.r_[t.ravel(),0.];p=np.r_[p,float(ch['P0'])]
    unique,index=np.unique(t,return_inverse=True);weights=np.bincount(index,weights=p)
    assert abs(weights.sum()-1)<1e-13 and 0<=unique.min()<=unique.max()<=1
    return unique,weights


def fading_mi(candidate,parameters,radial=128,width_order=16,spacing=.025):
    """Same exact Gaussian-mixture likelihood; Fourier inversion accelerates it.

    The Gaussian characteristic function is integrated with the same fading
    quadrature. |k|>10 contributes <1e-22 to the density; periodic copies lie
    beyond12 output standard deviations. Tiny negative FFT roundoff is logged.
    """
    t,p=quadrature(*parameters,radial,width_order)
    x,px=previous.source_factors(candidate)
    assert np.max(abs(x+x[::-1]))<1e-12 and np.max(abs(px-px[::-1]))<1e-13
    variance=1+.8*.0186*t+.0135
    means=2*math.sqrt(.8)*x[8:,None]*np.sqrt(t)[None,:]
    extent=float(means.max()+12*math.sqrt(variance.max()));period=2*extent
    n=2**math.ceil(math.log2(period/spacing));dy=period/n
    indices=np.arange(1,min(n//2,int(10*period/(2*math.pi)))+1)
    cf=np.zeros((8,n),dtype=complex);cf[:,0]=p.sum()
    for start in range(0,len(indices),16):
        ids=indices[start:start+16];k=2*math.pi*ids/period
        values=np.sum(np.exp(-.5*k[None,:,None]**2*variance[None,None,:]
                            -1j*k[None,:,None]*means[:,None,:])*p[None,None,:],axis=-1)
        cf[:,ids]=values;cf[:,-ids]=values.conj()
    pos=np.fft.fftshift(np.fft.ifft(cf,axis=1).real,axes=1).T/dy
    densities=np.column_stack((pos[(-np.arange(n))%n,::-1],pos))
    negative_mass=float(-np.sum(densities[densities<0])*dy)
    if densities.min()<-5e-15 or negative_mass>1e-12:
        raise ValueError('FFT density roundoff exceeds declared mass budget')
    densities=np.maximum(densities,0)  # Explicit numerical repair, never transmission clipping.
    mixture=densities@px;positive=densities>0
    logs=np.log(np.where(mixture>0,mixture,1))[:,None]
    terms=np.zeros_like(densities)
    terms[positive]=densities[positive]*(np.log(densities[positive])-np.broadcast_to(logs,densities.shape)[positive])
    info=float(dy*np.sum(terms@px)/math.log(2))
    mass_error=float(np.max(abs(densities.sum(axis=0)*dy-1)))
    assert 0<=info<=-np.dot(px,np.log2(px)) and mass_error<2e-12
    return dict(I_AB_actual=info,radial_order=radial,width_order=width_order,
        output_grid=n,output_spacing=dy,conditional_mass_error=mass_error,
        FFT_negative_roundoff_mass=negative_mass,quadrature_m1=float(p@t),quadrature_mh=float(p@np.sqrt(t)))


def evaluate(candidate,parameters,radial=128,width_order=16):
    ch,mo=optical(*parameters)
    old=previous.evaluate(candidate,mo,order=64,grid=33)
    actual=fading_mi(candidate,parameters,radial,width_order)
    return {**{k:float(v) if hasattr(v,'_mpf_') else v for k,v in ch.items()},**mo,**old,
        'divergence_urad':parameters[1],'jitter_urad':parameters[2],'sigma_h_m':parameters[3],
        'I_AB_surrogate':old['I_AB'],'K_surrogate':old['K_raw'],**actual,
        'I_AB':actual['I_AB_actual'],'beta_I_AB':.95*actual['I_AB_actual'],
        'K_raw':.95*actual['I_AB_actual']-old['chi_BE'],
        'angular_displacement_m':ch['L_km']*1000*parameters[2]*1e-6,
        'sigma_h_over_w_eff':parameters[3]/ch['w_eff_m'],
        'angular_displacement_over_w_eff':ch['L_km']*1000*parameters[2]*1e-6/ch['w_eff_m'],
        'source_status':'BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY','rate_per':'transmitted_use_including_outage'}
