"""Fixed8cm extension of the accepted passive optical/homodyne diagnostic."""
from functools import lru_cache
import math
from pathlib import Path
import sys
import mpmath as mp
import numpy as np
from scipy.special import roots_hermitenorm
from scipy.stats import ncx2

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
PRIOR=ROOT/'results/untrusted_positive_skr_feasibility_20261022'
sys.path.insert(0,str(PRIOR))
import model as previous
M=previous.M


@lru_cache(64)
def primitives(hap_km,uav_km):
    if not 17<=hap_km<=25 or not 1<=uav_km<=5 or uav_km>=hap_km:
        raise ValueError('Height outside requested diagnostic domain')
    h0,h1=M(uav_km)*1000,M(hap_km)*1000;dh=h1-h0
    def cn2(h):
        return M('.00594')*(M(21)/27)**2*(M('1e-5')*h)**10*mp.exp(-h/1000)+M('2.7e-16')*mp.exp(-h/1500)+M('1e-14')*mp.exp(-h/100)
    knots=sorted(set([h0,h1]+[M(h) for h in [2000,5000,10000] if h0<h<h1]))
    return mp.quad(lambda h:cn2(h)*(h-h0)**(M(5)/6),knots),mp.quad(lambda h:cn2(h)*((h-h0)/dh)**(M(5)/3),knots)


@lru_cache(256)
def optical(hap_km,uav_km,angle,divergence,jitter,sigma,tau_zen=.92):
    if not 0<=angle<=30 or min(divergence,jitter,sigma)<=0 or not 0<tau_zen<=1:
        raise ValueError('Invalid optical geometry or weather')
    jry,jmu=primitives(hap_km,uav_km)
    sec=1/mp.cos(M(angle)*mp.pi/180);dh=(M(hap_km)-M(uav_km))*1000;length=dh*sec
    wave=M('1.55e-6');k=2*mp.pi/wave;w0=2*wave/(mp.pi*M(divergence)*M('1e-6'))
    wL=w0*mp.sqrt(1+(length*wave/(mp.pi*w0*w0))**2)
    gd=M('4.35')*(2*length/(k*wL*wL))**(M(5)/6)*k**(M(7)/6)*dh**(M(5)/6)*sec**(M(11)/6)*jmu
    weff=wL*mp.sqrt(1+gd);v=M('2.25')*k**(M(7)/6)*sec**(M(11)/6)*jry
    atm=M(tau_zen)**sec;ss=mp.sqrt(M(sigma)**2+(length*M(jitter)*M('1e-6'))**2)
    p0=mp.exp(-M('.00625')**2/(2*M('.0015')**2))
    ch=dict(D_r=.08,h_hap_km=hap_km,h_uav_km=uav_km,zenith_deg=angle,L_km=float(length/1000),
        theta_div_urad=divergence,divergence_urad=divergence,jitter_urad=jitter,sigma_h_m=sigma,
        eta_atm=float(atm),tau_zen=tau_zen,w0_m=float(w0),wL_m=float(wL),w_eff_m=float(weff),G_d=float(gd),
        v=v,P0=p0,P1=1-p0,sigma_s_m=float(ss),transmitter_diameter_99percent_m=float(2*w0*mp.sqrt(mp.log(100)/2)),
        angular_displacement_m=float(length*M(jitter)*M('1e-6')),HV_rytov_integral=float(jry),HV_mu2_integral=float(jmu),
        atmosphere_scope='ORIGINAL_HEIGHT_CALIBRATED_SCENARIO' if hap_km==20 and uav_km==1 else 'HEIGHT_CHANGED_FIXED_TAU_SENSITIVITY_VERTICAL_EXTINCTION_MISSING',
        phase_noise='OFF_HISTORICAL_ASSUMPTION',AO='OFF',turbulence_factor=1.)
    return ch,previous.power_conserving(ch)


@lru_cache(128)
def quadrature(parameters,radial,width_order):
    hH,hU,angle,div,jt,sigma,eta,noise,tau=parameters
    ch,_=optical(hH,hU,angle,div,jt,sigma,tau)
    u,wu=np.polynomial.legendre.leggauss(radial);u=(u+1)/2;wu=wu/2
    z,wz=roots_hermitenorm(width_order);wz/=math.sqrt(2*math.pi)
    width=ch['w_eff_m']*np.exp(-(-float(ch['v'])/2+math.sqrt(float(ch['v']))*z)/2)
    t=ch['eta_atm']*ncx2.cdf((.08/width[:,None])**2,2,8*ch['sigma_s_m']**2*(-np.log(u))[None,:]/width[:,None]**2)
    p=(float(ch['P1'])*np.outer(wz,wu)).ravel();t=np.r_[t.ravel(),0.];p=np.r_[p,float(ch['P0'])]
    unique,index=np.unique(t,return_inverse=True);weights=np.bincount(index,weights=p)
    assert abs(weights.sum()-1)<1e-13 and 0<=unique.min()<=unique.max()<=ch['eta_atm']<=1
    return unique,weights


def fading_mi(candidate,parameters,radial=128,width_order=16,spacing=.025):
    """Identical checked Fourier inversion, now with explicit detector parameters."""
    eta,noise=parameters[6:8]
    t,p=quadrature(tuple(parameters),radial,width_order);x,px=previous.source_factors(candidate)
    assert np.max(abs(x+x[::-1]))<1e-12 and np.max(abs(px-px[::-1]))<1e-13
    variance=1+eta*.0186*t+noise;means=2*math.sqrt(eta)*x[8:,None]*np.sqrt(t)[None,:]
    extent=float(means.max()+12*math.sqrt(variance.max()));period=2*extent
    count=2**math.ceil(math.log2(period/spacing));dy=period/count
    indices=np.arange(1,min(count//2,int(10*period/(2*math.pi)))+1)
    cf=np.zeros((8,count),dtype=complex);cf[:,0]=p.sum()
    for start in range(0,len(indices),16):
        ids=indices[start:start+16];k=2*math.pi*ids/period
        values=np.sum(np.exp(-.5*k[None,:,None]**2*variance[None,None,:]-1j*k[None,:,None]*means[:,None,:])*p[None,None,:],axis=-1)
        cf[:,ids]=values;cf[:,-ids]=values.conj()
    pos=np.fft.fftshift(np.fft.ifft(cf,axis=1).real,axes=1).T/dy
    densities=np.column_stack((pos[(-np.arange(count))%count,::-1],pos))
    negative_mass=float(-np.sum(densities[densities<0])*dy)
    if densities.min()<-5e-15 or negative_mass>1e-12:raise ValueError('FFT roundoff mass exceeds declared budget')
    densities=np.maximum(densities,0);mixture=densities@px;positive=densities>0
    logmix=np.log(np.where(mixture>0,mixture,1))[:,None];terms=np.zeros_like(densities)
    terms[positive]=densities[positive]*(np.log(densities[positive])-np.broadcast_to(logmix,densities.shape)[positive])
    info=float(dy*np.sum(terms@px)/math.log(2));mass_error=float(np.max(abs(densities.sum(axis=0)*dy-1)))
    assert 0<=info<=-np.dot(px,np.log2(px)) and mass_error<2e-12
    return dict(I_AB_actual=info,radial_order=radial,width_order=width_order,output_grid=count,output_spacing=dy,
        conditional_mass_error=mass_error,FFT_negative_roundoff_mass=negative_mass,quadrature_m1=float(p@t),quadrature_mh=float(p@np.sqrt(t)))


def evaluate(candidate,parameters,radial=128,width_order=16):
    hH,hU,angle,div,jt,sigma,eta,noise,tau=parameters
    ch,mo=optical(hH,hU,angle,div,jt,sigma,tau)
    security=previous.evaluate(candidate,mo,eta_det=eta,epsilon_det=noise,order=64,grid=33)
    actual=fading_mi(candidate,parameters,radial,width_order)
    return {**{k:float(v) if isinstance(v,mp.mpf) else v for k,v in ch.items()},**mo,**security,
        'I_AB_surrogate':security['I_AB'],'K_surrogate':security['K_raw'],**actual,
        'I_AB':actual['I_AB_actual'],'beta_I_AB':.95*actual['I_AB_actual'],'K_raw':.95*actual['I_AB_actual']-security['chi_BE'],
        'rate_per':'transmitted_use_including_outage','hardware_validated':False,'source_status':'BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY'}
