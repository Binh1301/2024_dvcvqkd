"""Independent Task-2 optical gate. No SKR search if pointing laws disagree."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import i0e
from scipy.stats import ncx2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def aperture(r, w, a):
    return ncx2.cdf(4*a*a/(w*w), 2, 4*np.asarray(r)**2/(w*w))


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import yaml
    from src.manuscript_literal_3moments import LiteralChannel

    out = ROOT/'results'/(sys.argv[1] if len(sys.argv)>1 else 'pointing_aperture_task2_20261017')
    if out.resolve().parent != (ROOT/'results').resolve():
        raise ValueError('Output must be one new directory under project results')
    out.mkdir(exist_ok=False)
    cfg = yaml.safe_load((ROOT/'configs/default.yaml').read_text())['channel']
    L, a, theta = 21939.3102292, .275, 10e-6
    h0, h1 = cfg['h_uav_m'], cfg['h_hap_m']
    sec = L/(h1-h0)
    wavelength = cfg['wavelength_m']
    k = 2*math.pi/wavelength
    profile = cfg['turbulence_profile']
    wind, cn0 = profile['wind_speed_m_per_s'], profile['cn2_ground_m_minus_two_thirds']

    def cn(h):
        return .00594*(wind/27)**2*(1e-5*h)**10*math.exp(-h/1000)+2.7e-16*math.exp(-h/1500)+cn0*math.exp(-h/100)

    # Scale tiny integrands so absolute quadrature tolerance cannot dominate.
    mu2 = quad(lambda h: 1e14*cn(h)*((h-h0)/(h1-h0))**(5/3), h0, h1, epsabs=1e-12, epsrel=2e-13)[0]*1e-14
    jr = quad(lambda h: 1e10*cn(h)*(h-h0)**(5/6), h0, h1, epsabs=1e-12, epsrel=2e-13)[0]*1e-10
    rytov = 2.25*k**(7/6)*sec**(11/6)*jr
    w0 = 2*wavelength/(math.pi*theta)
    wL = w0*math.sqrt(1+(L*wavelength/(math.pi*w0*w0))**2)
    beam_lambda = 2*L/(k*wL*wL)
    gd = 4.35*beam_lambda**(5/6)*k**(7/6)*(h1-h0)**(5/6)*sec**(11/6)*mu2
    weff = wL*math.sqrt(1+gd)
    sigma = math.hypot(1., L*15.61e-6)
    v = math.sqrt(math.pi)*a/(math.sqrt(2)*weff)
    A0 = math.erf(v)**2
    weq = math.sqrt(weff**2*math.sqrt(math.pi)*math.erf(v)/(2*v*math.exp(-v*v)))
    tau = .92**sec
    p0 = math.exp(-cfg['aoa']['theta_fov_rad']**2/(2*cfg['aoa']['sigma_o_rad']**2))
    checks, rows = [], []
    for label, w in [('diffraction_only', wL), ('HV_broadened_Gaussian', weff)]:
        centered = -math.expm1(-2*a*a/(w*w))
        mean = -math.expm1(-2*a*a/(w*w+4*sigma*sigma))
        radial, err = quad(lambda r: float(aperture(r,w,a))*r/sigma**2*math.exp(-r*r/(2*sigma*sigma)), 0, 12*sigma, epsabs=1e-13, epsrel=2e-12, points=[a])
        checks.append(dict(name=label+'_centered', residual=float(aperture(0,w,a))-centered, passed=abs(float(aperture(0,w,a))-centered)<1e-13))
        checks.append(dict(name=label+'_mean_identity', residual=radial-mean, error_estimate=err, passed=abs(radial-mean)<1e-11))
        for r in [0., .1, .275, .5, 1., 2.]:
            # Independent Bessel integral: exp[-2(s-r)^2/w^2] I0e(4sr/w^2).
            direct = quad(lambda s: 4*s/w**2*math.exp(-2*(s-r)**2/w**2)*i0e(4*s*r/w**2), 0,a, epsabs=1e-13, epsrel=2e-12)[0]
            value = float(aperture(r,w,a))
            checks.append(dict(name=f'{label}_Bessel_r{r}', residual=value-direct, passed=abs(value-direct)<1e-11))
        rows.append(dict(model=label,w_m=w,mean_Hp_closed=mean,mean_Hp_quadrature=radial,centered=centered))
    approx_mean = A0/(1+4*sigma*sigma/weq**2)
    literal = LiteralChannel(tau,A0,weq,sigma,rytov,0.,p0,1-p0)
    active_mass = literal.active_moment(0)
    raw_m1 = (1-p0)*literal.active_moment(1)
    conditioned_m1 = raw_m1/active_mass
    reference_mean = rows[1]['mean_Hp_closed']
    result = dict(status='BLOCKED_POINTING_MODEL_INCONSISTENCY', search_status='NOT_RUN',
        inputs=dict(L_m=L,Dr_m=2*a,h_HAP_m=h1,h_UAV_m=h0,sigma_h_m=1.,theta_jt_rad=15.61e-6,theta_div_full_rad=theta,tau_zen=.92),
        geometry=dict(w0_m=w0,wL_m=wL,G_d=gd,w_eff_m=weff,sigma_s_m=sigma,sigma_R2=rytov,eta_atm=tau,P0=p0,A0_approx=A0,w_eq_m=weq),
        comparison=dict(mean_Hp_approx=approx_mean,mean_Hp_reference=reference_mean,approx_over_reference=approx_mean/reference_mean,raw_m1=raw_m1,active_retained_mass=active_mass,conditioned_m1=conditioned_m1,
            independent_product_unit_mean_scintillation_m1=(1-p0)*tau*reference_mean),
        checks=checks,all_numerical_checks_pass=all(c['passed'] for c in checks),
        scientific_scope='Aperture reference is exact only for the specified Gaussian intensity; HV broadening is retained as a Gaussian-width approximation. No joint scintillation/pointing model or security proof is validated.',
        missing_task1_files=[str(p) for p in ['docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md','src/trusted_heterodyne_skr.py','results/full_geometry_fading_skr_audit_20261017'] if not (ROOT/p).exists()],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['configs/default.yaml','docs/FINAL_MODEL_SPEC.md','src/manuscript_literal_3moments.py']})
    assert result['all_numerical_checks_pass']
    assert abs(wL-.14755)<1e-5 and abs(rows[0]['mean_Hp_closed']-.03312)<1e-5
    assert result['comparison']['approx_over_reference']>5
    with (out/'optical_checks.json').open('w') as f:
        json.dump(result,f,indent=2)
    with (out/'mean_pointing_comparison.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    r=np.linspace(0,2,1001)
    exact=aperture(r,weff,a); approx=A0*np.exp(-2*r*r/weq**2)
    np.savetxt(out/'radial_collection.csv',np.column_stack([r,exact,approx]),delimiter=',',header='r_m,aperture_reference,equivalent_gaussian_approx',comments='')
    fig,ax=plt.subplots(); ax.plot(r,exact,label='Circular aperture reference'); ax.plot(r,approx,label='Equivalent Gaussian approximation'); ax.set(xlabel='Displacement r (m)',ylabel='Collected power fraction',ylim=(0,1.05)); ax.legend(); fig.tight_layout(); fig.savefig(out/'pointing_comparison.png',dpi=200); fig.savefig(out/'pointing_comparison.pdf'); plt.close(fig)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
