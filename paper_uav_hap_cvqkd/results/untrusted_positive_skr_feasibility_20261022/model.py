"""Isolated pooled-iid homodyne feasibility DIAGNOSTIC; no security certification."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys

import mpmath as mp
import numpy as np
from scipy.integrate import quad, quad_vec, simpson
from scipy.special import log_ndtr, logsumexp, roots_hermitenorm
from scipy.optimize import minimize_scalar
from scipy.stats import ncx2

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.manuscript_mobility import channel_at_angle, load_catalog
from scripts.recheck_manuscript_homodyne_noise import M, mi_gh

_spec=importlib.util.spec_from_file_location('_saved_product_moment',
    ROOT/'results/zenith_angle_root_cause_diagnostic_20261021/investigate.py')
_moments=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_moments)
mp.mp.dps=80
_GEOMETRIES={}


def optical(diameter,divergence,angle,position_factor=1.,angular_factor=1.,turbulence_factor=1.):
    """Reuse saved manuscript HV primitives, recompute every optical/pointing term."""
    if min(diameter,divergence,position_factor,angular_factor,turbulence_factor)<=0 or not 0<=angle<=60:
        raise ValueError('Invalid optical diagnostic parameters')
    if angle not in _GEOMETRIES:
        _GEOMETRIES[angle]=channel_at_angle(angle)
    base=_GEOMETRIES[angle]
    length,wave=base['L_m'],M('1.55e-6')
    w0=2*wave/(mp.pi*M(divergence)*M('1e-6'))
    wL=w0*mp.sqrt(1+(length*wave/(mp.pi*w0*w0))**2)
    sec=length/M(19000);k=2*mp.pi/wave
    gd=M('4.35')*(2*length/(k*wL*wL))**(M(5)/6)*k**(M(7)/6)*M(19000)**(M(5)/6)*sec**(M(11)/6)*base['mu2_integral']*M(turbulence_factor)
    weff=wL*mp.sqrt(1+gd)
    ap=mp.sqrt(mp.pi)*M(diameter)/(2*mp.sqrt(2)*weff)
    a0=mp.erf(ap)**2
    weq=mp.sqrt(weff*weff*mp.sqrt(mp.pi)*mp.erf(ap)/(2*ap*mp.exp(-ap*ap)))
    sigma=mp.sqrt(M(position_factor)**2+(length*M('15.61e-6')*M(angular_factor))**2)
    return dict(D_r=diameter,theta_div_urad=divergence,zenith_deg=angle,
                position_factor=position_factor,angular_factor=angular_factor,turbulence_factor=turbulence_factor,
                L_km=float(length/1000),w0_m=float(w0),wL_m=float(wL),w_eff_m=float(weff),w_eq_m=float(weq),G_d=float(gd),
                transmitter_diameter_99percent_m=float(2*w0*mp.sqrt(-mp.log(M('.01'))/2)),
                hardware_feasibility='TRANSMITTER_APERTURE_AND_JITTER_CAPABILITY_NOT_VERIFIED',
                B=a0*base['eta_atm'],eta_atm=float(base['eta_atm']),d=weq*weq/(4*sigma*sigma),v=base['sigma_R2']*M(turbulence_factor),
                P0=base['P0'],P1=base['P1'],sigma_s_m=float(sigma),sigma_position_m=position_factor,
                angular_jitter_rad=15.61e-6*angular_factor,phase_noise='OFF_HISTORICAL_ASSUMPTION',AO='OFF')


def bounded(ch,treatment='conditional_active'):
    b,d,v,p1=[ch[k] for k in ('B','d','v','P1')]
    # Tail probabilities below the working precision need more digits, not clipping to one.
    with mp.workdps(160):
        raw={q:_moments.product_moment(b,d,v,p1,M(q))[0] for q in (0,.5,1)}
        _,tail0=_moments.product_moment(b,d,v,p1,M(0))
        retained=1-tail0  # q=0 full moment is exactly one; cancel d/d before rounding.
        raw[0]=p1*retained
    if not 0<retained<=1 or not 0<=raw[.5]**2<=raw[1]<=1:
        raise ValueError('Raw truncated-moment domain failure')
    if treatment=='conditional_active':
        m1,mh=raw[1]/retained,raw[.5]/retained
        p0,pactive=ch['P0'],p1
    elif treatment=='invalid_tail_to_erasure':
        m1,mh=raw[1],raw[.5]
        p0,pactive=1-raw[0],raw[0]
    else:
        raise ValueError('Unknown bounded law')
    if not 0<=mh*mh<=m1<=1 or abs(p0+pactive-1)>M('1e-60'):
        raise ValueError('Physical moment/normalization failure')
    return dict(treatment=treatment,m1=float(m1),mh=float(mh),eta_f=float(mh*mh),
                variance_sqrt_eta=float(m1-mh*mh),P0=float(p0),Pactive=float(pactive),
                retained_raw_mass=float(ch['P0']+raw[0]),raw_upper_tail_mass=float(p1-raw[0]),
                active_normalization=float(retained),physical_mass=float(p0+pactive),
                m1_decimal=mp.nstr(m1,65),mh_decimal=mp.nstr(mh,65))


def power_conserving(ch,order=32):
    """New bounded Gaussian random-width surrogate; every beam has unit power.

    S~N(-v/2,v), w=w_eff exp(-S/2) makes on-axis intensity lognormal. Exact
    circular-aperture collection replaces the small-offset equivalent-beam law.
    This is a declared diagnostic model, not a measured turbulence closure.
    """
    z,weights=roots_hermitenorm(order);weights/=math.sqrt(2*math.pi)
    s=-float(ch['v'])/2+math.sqrt(float(ch['v']))*z
    width=ch['w_eff_m']*np.exp(-s/2)
    sigma=ch['sigma_s_m'];a=ch['D_r']/2
    threshold=(2*a/width)**2
    def values(x):
        power=ncx2.cdf(threshold,df=2,nc=8*sigma*sigma*x/(width*width))
        if not np.isfinite(power).all() or np.any((power<0)|(power>1)):
            raise ValueError('Exact circular collection outside [0,1]')
        return np.sqrt(power)*math.exp(-x)
    # Integrate the actual Rayleigh displacement distribution, including the sharp edge.
    half,error=quad_vec(values,0,math.inf,epsabs=2e-13,epsrel=2e-12,
                        points=[a*a/(2*sigma*sigma)],limit=400)
    if error>2e-11:
        raise ValueError('Rayleigh/circular-aperture integration failed')
    p1=float(ch['P1']);atm=ch['eta_atm']
    m1=p1*atm*float(np.dot(weights,-np.expm1(-2*a*a/(width*width+4*sigma*sigma))))
    mh=p1*math.sqrt(atm)*float(np.dot(weights,half))
    if not 0<=mh*mh<=m1<=atm<=1:
        raise ValueError('Power-conserving channel moment constraints failed')
    return dict(treatment='power_conserving_random_width',m1=m1,mh=mh,eta_f=mh*mh,
                variance_sqrt_eta=m1-mh*mh,P0=float(ch['P0']),Pactive=p1,
                retained_raw_mass=1.,raw_upper_tail_mass=0.,active_normalization=1.,physical_mass=1.,
                width_GH_order=order,radial_quadrature_error=float(error),m1_decimal=repr(m1),mh_decimal=repr(mh))


def source_factors(candidate):
    x,index=np.unique(candidate['alpha'].real,return_inverse=True)
    px=np.bincount(index,weights=candidate['p'])
    return x,px


def _entropy(nu):
    x=(np.asarray(nu)-1)/2
    if np.any(x<0):
        raise ValueError('Entropy evaluated on sub-vacuum symplectic eigenvalue')
    result=np.log1p(x)/math.log(2)
    positive=x>0
    result[positive]+=x[positive]*(np.log1p(x[positive])-np.log(x[positive]))/math.log(2)
    return result


def spectrum(a,b,z):
    z=np.atleast_1d(z)
    root=np.sqrt((a+b)**2-4*z*z)
    nu1=(root+abs(a-b))/2;nu2=(root-abs(a-b))/2
    cap=math.sqrt(min((a-1)*(b+1),(a+1)*(b-1)))
    on_cap=abs(z)==cap
    # Exact uncertainty-boundary identity, not eigenvalue clipping.
    nu1[on_cap]=1+abs(a-b);nu2[on_cap]=1.
    nu3=np.sqrt(a*(a-z*z/b))
    if min(nu1.min(),nu2.min(),nu3.min())<1:
        raise ValueError('Nonphysical homodyne covariance')
    return nu1,nu2,nu3


def full_holevo(a,b,center,radius,grid=33):
    cap=math.sqrt(min((a-1)*(b+1),(a+1)*(b-1)))
    lower,upper=max(center-radius,-cap),min(center+radius,cap)
    if lower>upper:
        raise ValueError('Empty discrete-modulation correlation interval')
    def chi(z):
        n1,n2,n3=spectrum(a,b,z)
        return _entropy(n1)+_entropy(n2)-_entropy(n3)
    points=np.linspace(lower,upper,grid)
    if lower<=0<=upper:
        points=np.unique(np.r_[points,0.])
    values=chi(points)
    candidates=[(float(value),float(z)) for value,z in zip(values,points)]
    for i in range(1,len(points)-1):
        if values[i]>max(values[i-1],values[i+1]):
            result=minimize_scalar(lambda z:-float(chi(z)[0]),bounds=(points[i-1],points[i+1]),
                                   method='bounded',options={'xatol':1e-13})
            if not result.success:
                raise ValueError('Homodyne full-Z numerical refinement failed')
            candidates.append((-float(result.fun),float(result.x)))
    best,z=max(candidates)
    nus=[float(n[0]) for n in spectrum(a,b,z)]
    return dict(chi_BE=best,Z_worst=z,Z_lower=lower,Z_upper=upper,Z_physical_cap=cap,
                chi_at_lower=float(chi(lower)[0]),nu_1=nus[0],nu_2=nus[1],nu_3=nus[2],
                full_Z_grid=grid,rigorous_global_enclosure=False)


def evaluate(candidate,moments,eta_det=.8,epsilon_det=.0135,active_only=False,order=64,grid=33):
    if not 0<eta_det<=1 or epsilon_det<0:
        raise ValueError('Untrusted detector parameters outside physical domain')
    va= candidate['VA'];m1,mh=moments['m1'],moments['mh'];t=eta_det*moments['eta_f']
    fading=moments['variance_sqrt_eta']*va
    channel=.0186*m1
    detector=epsilon_det/eta_det*(moments['Pactive'] if active_only else 1.)
    noise=eta_det*(fading+channel+detector)
    a,b=1+va,1+t*va+noise
    center=2*math.sqrt(eta_det)*mh*candidate['C']
    radius=math.sqrt(2*noise*candidate['w'])
    holevo=full_holevo(a,b,center,radius,grid)
    x,px=source_factors(candidate)
    iab=mi_gh(px,x.astype(complex),t,noise,order,dimension=1)
    if not 0<=iab<=-float(np.dot(px,np.log2(px)))+2e-13 or holevo['chi_BE']<0:
        raise ValueError('Invalid MI/Holevo information domain')
    gamma=np.array([[a,0,holevo['Z_worst'],0],[0,a,0,-holevo['Z_worst']],
                    [holevo['Z_worst'],0,b,0],[0,-holevo['Z_worst'],0,b]])
    omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
    minimum=float(np.linalg.eigvalsh(gamma+1j*omega).min())
    if minimum< -1e-11:
        raise ValueError('Uncertainty constraint failure')
    matrix_nus=np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    if np.max(abs(matrix_nus-np.sort([holevo['nu_1'],holevo['nu_2']])))>1e-10:
        raise ValueError('Independent symplectic spectrum disagrees')
    return dict(family=candidate['family'],VA=va,nu_raw=candidate['nu_raw'],
                ensemble_hash=candidate['ensemble_hash'],C=candidate['C'],w=candidate['w'],
                eta_det=eta_det,epsilon_det=epsilon_det,active_only=active_only,
                eta_f=moments['eta_f'],t_after_detector=t,N_fading=fading,N_channel=channel,N_detector=detector,
                N_pre=fading+channel+detector,N_post=noise,epsilon_f=(fading+channel+detector)/moments['eta_f'],
                a=a,b=b,I_AB=iab,beta_I_AB=.95*iab,K_raw=.95*iab-holevo['chi_BE'],
                uncertainty_min_eigenvalue=minimum,GH_order=order,receiver='homodyne_1D',detector_security='untrusted',
                validity='NORMALIZED_BOUNDED_CHANNEL_PHYSICAL_COVARIANCE_DIAGNOSTIC_ONLY',security_valid=False,**holevo)


def direct_moments(ch,treatment):
    """Independent log-eta integration of the stated bounded law."""
    b,d,v,p1=[float(ch[k]) for k in ('B','d','v','P1')]
    mu=v*(1+2*d)/2;c3=1/math.sqrt(2*v)
    logc=math.log(p1*d/2)+v*d*(1+d)/2-d*math.log(b)
    def integrand(y,q):
        return math.exp(logc+(d+q)*y+math.log(2)+float(log_ndtr(-math.sqrt(2)*c3*(y-math.log(b)+mu))))
    vals=[quad(lambda y:integrand(y,q),-math.inf,0,epsabs=2e-13,epsrel=2e-12,limit=400)[0] for q in (0,.5,1)]
    scale=p1/vals[0] if treatment=='conditional_active' else 1.
    return dict(active_mass=vals[0]*scale,mh=vals[1]*scale,m1=vals[2]*scale)


def pooled_mi(candidate,ch,eta_det=.8,epsilon_det=.0135,radial_order=128,width_order=16):
    """Actual pooled homodyne mixture for the NEW passive random-width model.

    Positive Gauss-Legendre weights integrate the Rayleigh CDF, GH integrates
    log-width, and Simpson integrates the continuous receiver output. No CSI
    conditioning, postselection or source-moment interpolation is performed.
    """
    u,wu=np.polynomial.legendre.leggauss(radial_order);u=(u+1)/2;wu=wu/2
    x=-np.log(u)
    z,wz=roots_hermitenorm(width_order);wz/=math.sqrt(2*math.pi)
    s=-float(ch['v'])/2+math.sqrt(float(ch['v']))*z
    width=ch['w_eff_m']*np.exp(-s/2)
    t=ch['eta_atm']*ncx2.cdf((ch['D_r']/width[:,None])**2,df=2,
                            nc=8*ch['sigma_s_m']**2*x[None,:]/width[:,None]**2)
    probability=(float(ch['P1'])*np.outer(wz,wu)).ravel()
    probability=np.r_[probability,float(ch['P0'])];t=np.r_[t.ravel(),0.]
    if abs(probability.sum()-1)>1e-13 or np.any((t<0)|(t>1)):
        raise ValueError('Pooled-fading quadrature domain/mass failure')
    levels,px=source_factors(candidate)
    means=2*math.sqrt(eta_det)*levels[:,None]*np.sqrt(t)[None,:]
    variance=1+eta_det*.0186*t+epsilon_det
    extent=float(np.max(abs(means))+12*math.sqrt(variance.max()))
    count=2*math.ceil(extent/.025)+1
    y=np.linspace(-extent,extent,count)
    densities=np.empty((len(y),len(px)))
    scale=probability/np.sqrt(2*math.pi*variance)
    for start in range(0,len(y),16):
        delta=y[start:start+16,None,None]-means[None,:,:]
        densities[start:start+16]=np.sum(np.exp(-delta*delta/(2*variance[None,None,:]))*scale[None,None,:],axis=-1)
    mixture=densities@px
    terms=np.zeros_like(densities)
    positive=densities>0
    terms[positive]=densities[positive]*(np.log(densities[positive])-np.broadcast_to(np.log(mixture)[:,None],densities.shape)[positive])
    info=float(simpson(terms@px,x=y)/math.log(2))
    masses=simpson(densities,x=y,axis=0)
    if not 0<=info<=-np.dot(px,np.log2(px)) or np.max(abs(masses-1))>2e-10:
        raise ValueError('Pooled conditional likelihood/MI integration failed')
    return dict(I_AB_pooled=info,radial_order=radial_order,width_order=width_order,
                quadrature_m1=float(probability@t),quadrature_mh=float(probability@np.sqrt(t)),
                conditional_density_mass_max_error=float(np.max(abs(masses-1))),output_grid_count=len(y))
