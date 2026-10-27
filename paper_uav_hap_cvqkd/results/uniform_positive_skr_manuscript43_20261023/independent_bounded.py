"""Independent finite-domain radial quadrature for the secondary best channel."""
import math
import numpy as np
from scipy.special import roots_hermitenorm
from scipy.stats import ncx2
import search as s


def main():
    row=s.read(s.OUT/'screen_receipt.json')['secondary_best']
    ctx=s.read(s.OUT/'contexts'/(row['context_id']+'.json'));ch=ctx['channel']
    z,wz=roots_hermitenorm(96);wz/=math.sqrt(2*math.pi)
    width=ch['w_eff_m']*np.exp(-(-float(ch['v'])/2+math.sqrt(float(ch['v']))*z)/2)
    x,wx=np.polynomial.legendre.leggauss(512);x=20*(x+1);wx*=20
    aperture=ch['D_r']/2
    power=ncx2.cdf((2*aperture/width[:,None])**2,df=2,
        nc=8*ch['sigma_s_m']**2*x[None,:]/width[:,None]**2)
    assert np.isfinite(power).all() and np.all((power>=0)&(power<=1))
    radial=wx*np.exp(-x)
    p1=float(ch['P1']);atm=ch['eta_atm']
    first=p1*atm*float(wz@(power@radial))
    half=p1*math.sqrt(atm)*float(wz@(np.sqrt(power)@radial))
    errors=dict(m1=first-ctx['moments']['m1'],mh=half-ctx['moments']['mh'])
    assert max(abs(v) for v in errors.values())<2e-11
    centered=ncx2.cdf((2*aperture/width)**2,df=2,nc=0)
    centered_error=float(np.max(abs(centered+np.expm1(-2*aperture**2/width**2))))
    assert centered_error<2e-15
    s.save(s.OUT/'independent_bounded_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',
        method='GH96 width x Legendre512 radial x in[0,40], direct aperture CDF',
        radial_omitted_mass_upper_bound=math.exp(-40),m1=first,mh=half,
        residuals=errors,centered_CDF_identity_error=centered_error,
        producer_sha256=s.a.sha(__file__),context_id=row['context_id']))
    print('INDEPENDENT BOUNDED',errors)


if __name__=='__main__':main()
