"""Two explicit optical laws; passive-support conditioning preserves AoA outage.

The unit-mean lognormal times aperture collection is an optical surrogate with
nonzero T>1 tail. Conditioning is an explicit model choice, not a calibration.
No old closed-form pointing PDF is used for APERTURE_CORRECTED.
"""
from dataclasses import asdict, dataclass
import math

import numpy as np
from scipy.integrate import quad
from scipy.special import i0e, log_ndtr, ndtr, roots_legendre
from scipy.stats import ncx2


PDF_ORIGINAL = 'PDF_ORIGINAL'
APERTURE_CORRECTED = 'APERTURE_CORRECTED'
SUPPORT_POLICY = 'condition_active_on_T_le_1_preserve_AoA_atom'


@dataclass(frozen=True)
class OpticalConfig:
    name: str
    divergence_full_rad: float
    receiver_diameter_m: float
    h_hap_m: float = 20000.
    h_uav_m: float = 1000.
    zenith_rad: float = math.pi/6
    wavelength_m: float = 1.55e-6
    tau_zen: float = .92
    sigma_h_m: float = 1.
    theta_jt_rad: float = 15.61e-6
    boresight_m: float = 0.
    sigma_o_rad: float = .0015
    fov_half_rad: float = .00625
    wind_m_s: float = 21.
    cn2_ground: float = 1e-14
    support_policy: str = SUPPORT_POLICY

    def __post_init__(self):
        values = asdict(self)
        for key, value in values.items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                raise ValueError(f'Nonfinite optical parameter: {key}')
        if self.h_hap_m != 20000 or not 0 <= self.h_uav_m < self.h_hap_m:
            raise ValueError('Fixed 20 km HAP and lower UAV required')
        if not 0 <= self.zenith_rad < math.pi/2 or not 0 < self.tau_zen <= 1:
            raise ValueError('Invalid geometry or zenith attenuation')
        for key in ('divergence_full_rad','receiver_diameter_m','wavelength_m','sigma_o_rad','fov_half_rad'):
            if values[key] <= 0:
                raise ValueError(f'Positive parameter required: {key}')
        if min(self.sigma_h_m,self.theta_jt_rad,self.boresight_m,self.cn2_ground,self.wind_m_s) < 0:
            raise ValueError('Nonnegative motion/turbulence required')
        if self.sigma_h_m == self.theta_jt_rad == 0:
            raise ValueError('Use an explicit deterministic law for zero displacement')
        if self.support_policy != SUPPORT_POLICY:
            raise ValueError('An explicit supported passive-support policy is required')


def aperture_collection(r, width, radius):
    """Exact for the specified circularly symmetric Gaussian intensity."""
    r = np.asarray(r, dtype=float)
    if width <= 0 or radius <= 0 or not np.isfinite(r).all() or np.any(r < 0):
        raise ValueError('Invalid Gaussian aperture inputs')
    return ncx2.cdf(4*radius**2/width**2, 2, 4*r**2/width**2)


def optical_geometry(config):
    vertical = config.h_hap_m-config.h_uav_m
    sec = 1/math.cos(config.zenith_rad)
    L = vertical*sec
    wavelength = config.wavelength_m
    k = 2*math.pi/wavelength
    w0 = 2*wavelength/(math.pi*config.divergence_full_rad)
    wL = w0*math.sqrt(1+(L*wavelength/(math.pi*w0**2))**2)

    def cn(h):
        return (.00594*(config.wind_m_s/27)**2*(1e-5*h)**10*math.exp(-h/1000)
                +2.7e-16*math.exp(-h/1500)+config.cn2_ground*math.exp(-h/100))

    # Scaling resolves tiny HV integrals without changing their physical units.
    mu2 = quad(lambda h: 1e14*cn(h)*((h-config.h_uav_m)/vertical)**(5/3),
               config.h_uav_m,config.h_hap_m,epsabs=1e-12,epsrel=2e-13)[0]*1e-14
    jr = quad(lambda h: 1e10*cn(h)*(h-config.h_uav_m)**(5/6),
              config.h_uav_m,config.h_hap_m,epsabs=1e-12,epsrel=2e-13)[0]*1e-10
    rytov = 2.25*k**(7/6)*sec**(11/6)*jr
    gd = 4.35*(2*L/(k*wL**2))**(5/6)*k**(7/6)*vertical**(5/6)*sec**(11/6)*mu2
    weff = wL*math.sqrt(1+gd)
    radius = config.receiver_diameter_m/2
    v = math.sqrt(math.pi)*radius/(math.sqrt(2)*weff)
    A0 = math.erf(v)**2
    weq = math.sqrt(weff**2*math.sqrt(math.pi)*math.erf(v)/(2*v*math.exp(-v*v)))
    return dict(L_m=L,w0_m=w0,wL_m=wL,w_eff_m=weff,G_d=gd,sigma_R2=rytov,
                eta_atm=config.tau_zen**sec,sigma_s_m=math.hypot(config.sigma_h_m,L*config.theta_jt_rad),
                radius_m=radius,A0=A0,w_eq_m=weq,
                P0=math.exp(-config.fov_half_rad**2/(2*config.sigma_o_rad**2)),
                broadening_assumption='HV_Gd_effective_Gaussian_width_raw_Rytov_scintillation')


class FullFadingLaw:
    def __init__(self, config, mode=APERTURE_CORRECTED, tolerance=2e-11):
        if mode not in (PDF_ORIGINAL,APERTURE_CORRECTED):
            raise ValueError('Unknown optical mode')
        if mode == PDF_ORIGINAL and config.boresight_m != 0:
            raise ValueError('Original analytic PDF is validated only at zero boresight')
        self.config,self.mode,self.tolerance = config,mode,tolerance
        self.geometry = optical_geometry(config)
        self.P0 = self.geometry['P0']
        self._raw = {q:self._integral(q) for q in (0.,.5,1.)}
        self.tail_mass,self.log_tail_mass = self._tail_integral()
        self.retained = self._raw[0.][0]
        if not 0 < self.retained <= 1+1e-12:
            raise ValueError('Invalid active retained probability')
        if abs(self.retained+self.tail_mass-1)>2e-11:
            raise ValueError('Retained probability plus independently integrated tail failed')
        self.mean_sqrt_eta = (1-self.P0)*self._raw[.5][0]/self.retained
        self.mean_eta = (1-self.P0)*self._raw[1.][0]/self.retained
        if not 0 < self.mean_sqrt_eta**2 <= self.mean_eta <= 1:
            raise ValueError('Physical moment ordering failed; no clipping')

    def hp(self,r):
        g = self.geometry
        if self.mode == PDF_ORIGINAL:
            return g['A0']*np.exp(-2*np.asarray(r)**2/g['w_eq_m']**2)
        return aperture_collection(r,g['w_eff_m'],g['radius_m'])

    def radial_density(self,r):
        sigma,rho = self.geometry['sigma_s_m'],self.config.boresight_m
        r = np.asarray(r)
        return r/sigma**2*np.exp(-.5*((r-rho)/sigma)**2)*i0e(r*rho/sigma**2)

    def _breaks(self):
        g=self.geometry; a,w,s=g['radius_m'],g['w_eff_m'],g['sigma_s_m']
        end=self.config.boresight_m+12*s
        return sorted({0.,end,*[v for v in (a-w,a,a+w,a+2*w,a+4*w,a+8*w,s,3*s,6*s) if 0<v<end]})

    def _integral(self,q, bound=1.):
        g=self.geometry; variance=g['sigma_R2']; sd=math.sqrt(variance)

        def integrand(r):
            B=g['eta_atm']*float(self.hp(r))
            if B == 0:
                # Active underflow contributes at most machine-scale positive moments.
                factor=1. if q == 0 else 0.
            else:
                factor=B**q*math.exp(.5*variance*q*(q-1))*ndtr((math.log(bound/B)+(.5-q)*variance)/sd)
            return float(self.radial_density(r))*factor

        breaks=self._breaks()
        return quad(integrand,0,breaks[-1],points=breaks[1:-1],epsabs=self.tolerance/10,
                    epsrel=self.tolerance/10,limit=500)

    def _tail_integral(self):
        # A direct log-scaled survival integral resolves tails lost in 1-F(1).
        g=self.geometry; variance=g['sigma_R2']; sd=math.sqrt(variance)
        peak_log=float(log_ndtr((math.log(g['eta_atm']*float(self.hp(0)))-variance/2)/sd))
        def integrand(r):
            b=g['eta_atm']*float(self.hp(r))
            if b==0: return 0.
            logsf=float(log_ndtr((math.log(b)-variance/2)/sd))
            return float(self.radial_density(r))*math.exp(logsf-peak_log)
        breaks=self._breaks()
        scaled=quad(integrand,0,breaks[-1],points=breaks[1:-1],epsabs=self.tolerance/10,
                    epsrel=self.tolerance/10,limit=500)[0]
        log_tail=peak_log+math.log(scaled)
        return math.exp(log_tail),log_tail

    def cdf(self,t):
        if not math.isfinite(t) or t<0 or t>1:
            raise ValueError('CDF physical domain is [0,1]')
        if t == 0:
            return self.P0
        return self.P0+(1-self.P0)*self._integral(0.,t)[0]/self.retained

    def density(self,t):
        """Continuous density only; the separate AoA atom is not a density."""
        if not math.isfinite(t) or t<=0 or t>1:
            raise ValueError('Continuous physical density requires 0<T<=1')
        g=self.geometry; variance=g['sigma_R2']; sd=math.sqrt(variance)
        def integrand(r):
            b=g['eta_atm']*float(self.hp(r))
            if b==0: return 0.
            z=(math.log(t/b)+variance/2)/sd
            return float(self.radial_density(r))*math.exp(-z*z/2)/(t*sd*math.sqrt(2*math.pi))
        breaks=self._breaks()
        value=quad(integrand,0,breaks[-1],points=breaks[1:-1],epsabs=self.tolerance/10,
                   epsrel=self.tolerance/10,limit=500)[0]
        return (1-self.P0)*value/self.retained

    def moments(self,xi_ch=.0186):
        if xi_ch != .0186:
            raise ValueError('This primary study fixes xi_ch=.0186 and ideal detection')
        return dict(optical_mode=self.mode,configuration=asdict(self.config),geometry=self.geometry,
                    mean_eta=self.mean_eta,mean_sqrt_eta=self.mean_sqrt_eta,
                    physical_probability_mass=self.cdf(1.),outage_atom=self.P0,
                    active_retained_mass=self.retained,raw_active_tail_mass=self.tail_mass,
                    raw_active_tail_log_probability=self.log_tail_mass,
                    raw_total_mass_on_0_1=self.P0+(1-self.P0)*self.retained,
                    raw_full_positive_support_mass=1.,physical_support=[0.,1.],
                    support_policy=SUPPORT_POLICY,conditioning_is_modeling_choice=True,
                    independence_assumptions=['displacement','lognormal_scintillation','AoA'],
                    moment_quadrature_errors={str(q):err for q,(_,err) in self._raw.items()},
                    mean_eta_xi_total=2+(.0186-1)*self.mean_eta,chi_het=1.,R=1.,xi_det=0.,xi_ch=.0186)

    def quadrature(self,order=32):
        """Positive product integration with bounded normal tails (|z|<=12).

        Normalization occurs only after comparison to the independent adaptive
        retained mass and half/first moments, never to fix an invalid optical law.
        """
        roots,base=roots_legendre(order)
        radii,radial_weights=[],[]
        for left,right in zip(self._breaks()[:-1],self._breaks()[1:]):
            r=left+(roots+1)*(right-left)/2
            radii.extend(r); radial_weights.extend(base*(right-left)/2*self.radial_density(r))
        radii=np.asarray(radii); radial_weights=np.asarray(radial_weights)
        B=self.geometry['eta_atm']*self.hp(radii)
        sd=math.sqrt(self.geometry['sigma_R2'])
        eta_parts,weight_parts=[],[]
        for b,rw in zip(B,radial_weights):
            if b == 0:
                eta_parts.append(np.array([0.])); weight_parts.append(np.array([rw])); continue
            top=min(12.,(-math.log(b)+sd*sd/2)/sd)
            if top<=-12:
                raise ValueError('Truncated-normal integration range unresolved')
            z=-12+(roots+1)*(top+12)/2
            eta_parts.append(b*np.exp(-sd*sd/2+sd*z))
            weight_parts.append(rw*base*(top+12)/2*np.exp(-z*z/2)/math.sqrt(2*math.pi))
        eta=np.concatenate(eta_parts); weights=np.concatenate(weight_parts)
        mass=float(weights.sum())
        errors=dict(mass=abs(mass-self.retained),
                    m1=abs((1-self.P0)*float(weights@eta)/self.retained-self.mean_eta),
                    mhalf=abs((1-self.P0)*float(weights@np.sqrt(eta))/self.retained-self.mean_sqrt_eta))
        if max(errors.values())>2e-9 or np.any(eta<0) or np.any(eta>1):
            raise ValueError(f'Physical quadrature not converged: {errors}')
        weights=weights*(1-self.P0)/mass
        eta=np.r_[0.,eta]; weights=np.r_[self.P0,weights]
        return eta,weights,dict(order=order,errors=errors,normal_tail_bound=4e-33,
                                AoA_atom_weight=self.P0,
                                active_numerical_underflow_weight=float(weights[1:][eta[1:]==0].sum()),
                                numerical_zero_nodes_are_not_additional_physical_outages=True,
                                radial_tail_bound='r>rho+12sigma, negligible under stated Rician law')
