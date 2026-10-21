"""Single-point Eq. (11)--(21) diagnostic with explicitly audited source units.

Primary MI is a normalized complex-observation integral; Eq. (13) remains
homodyne. This requested hybrid comparison is not a physical security claim.
No optimizer, new source calculation, or production evaluator is invoked.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr, logsumexp, roots_hermitenorm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'results/manuscript_homodyne_noise_recheck_20261019'
SOURCE = ROOT / ('results/theta10_D55_mb_exact_targeted_expansion/batch_2/'
                 'exact_source_cache/4ff64d8ff1b9cb558e7feab44d02d62b15f2c430a0440ccb9af74b0e42e31a5d.json')
CATALOG = ROOT / 'results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv'
VA, NU, XI, BETA = 5.475, .165, .0186, .95
M = lambda x: mp.mpf(str(x))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def channel():
    """PDF geometry plus explicitly identified repository HV/G_d closure."""
    wl, theta, h0, h1 = map(M, ('1.55e-6', '233e-6', '1000', '20000'))
    zeta = mp.pi / 6
    sec = 1 / mp.cos(zeta)
    dh, k = h1 - h0, 2 * mp.pi / wl
    length = dh * sec
    w0 = 2 * wl / (mp.pi * theta)
    wL = w0 * mp.sqrt(1 + (length * wl / (mp.pi * w0**2))**2)

    def cn2(h):
        return (M('.00594') * (M(21)/27)**2 * (M('1e-5')*h)**10 * mp.exp(-h/1000)
                + M('2.7e-16')*mp.exp(-h/1500) + M('1e-14')*mp.exp(-h/100))

    knots = [h0, M(2000), M(5000), M(10000), h1]
    jry = mp.quad(lambda h: cn2(h)*(h-h0)**(M(5)/6), knots)
    jmu = mp.quad(lambda h: cn2(h)*((h-h0)/dh)**(M(5)/3), knots)
    sigma_R2 = M('2.25')*k**(M(7)/6)*sec**(M(11)/6)*jry
    beam_lambda = 2*length/(k*wL**2)
    gd = M('4.35')*beam_lambda**(M(5)/6)*k**(M(7)/6)*dh**(M(5)/6)*sec**(M(11)/6)*jmu
    weff = wL*mp.sqrt(1+gd)
    ap = mp.sqrt(mp.pi)*M('.08')/(2*mp.sqrt(2)*weff)
    A0 = mp.erf(ap)**2
    weq = mp.sqrt(weff**2*mp.sqrt(mp.pi)*mp.erf(ap)/(2*ap*mp.exp(-ap**2)))
    sigma_s = mp.sqrt(1+(length*M('15.61e-6'))**2)
    eta_atm = M('.92')**sec
    P0 = mp.exp(-M('6.25e-3')**2/(2*M('1.5e-3')**2))
    P1, rho = 1-P0, M(0)
    d = (weq/(2*sigma_s))**2
    C1 = mp.exp(rho**2/sigma_s**2+sigma_R2*d*(1+d)/2)
    C3 = (32*rho**2*sigma_s**2/weq**4+2*sigma_R2)**(-M('.5'))
    mu = 6*rho**2/weq**2+sigma_R2*(1+2*d)/2
    B = A0*eta_atm
    x1 = -mp.log(B)+mu
    def Q(a):
        return (mp.exp(a*x1-a*mu)*mp.erfc(C3*x1)
                + mp.exp(a*a/(4*C3*C3)-a*mu)*mp.erfc(a/(2*C3)-C3*x1))/2
    def moment(q):
        return P1*B**q*d*C1/(d+q)*Q(d+q)
    return dict(L_m=length, zeta_rad=zeta, w0_m=w0, wL_m=wL, G_d=gd,
                w_eff_m=weff, w_eq_m=weq, sigma_s_m=sigma_s, sigma_R2=sigma_R2,
                eta_atm=eta_atm, A0=A0, P0=P0, P1=P1, rho=rho, chi=mp.sqrt(d),
                chi2=d, C1=C1, C3=C3, mu=mu, B=B, x1=x1,
                Q_chi2=Q(d), Q_chi2_plus_half=Q(d+M('.5')), Q_chi2_plus_one=Q(d+1),
                mean_eta=moment(1), mean_sqrt_eta=moment(M('.5')),
                pdf_mass=P0+moment(0), mu2_integral=jmu, rytov_integral=jry)


def security(m1, mh, va, C, w):
    """Literal requested homodyne eigenvalue, evaluated at arbitrary precision."""
    t = mh**2
    var = m1-t
    n_ch = M(XI)*m1
    noise = var*va+n_ch
    V, W = va+1, 1+t*va+noise
    Z = 2*mh*C-mp.sqrt(2*noise*w)
    delta, D = V*V+W*W-2*Z*Z, (V*W-Z*Z)**2
    root = mp.sqrt(delta**2-4*D)
    nus = [mp.sqrt((delta+root)/2), mp.sqrt((delta-root)/2), mp.sqrt(V*(V-Z*Z/W))]
    result = dict(mean_eta=m1, mean_sqrt_eta=mh, eta_f=t, variance_sqrt_eta=var,
                  mean_eta_xi_n=n_ch, eta_f_xi_f=noise, xi_f=noise/t,
                  C=C, w=w, V=V, W=W, Z=Z, Delta=delta, D=D,
                  nu_1=nus[0], nu_2=nus[1], nu_3=nus[2], physical=bool(min(nus)>=1))
    if result['physical']:
        def g(x):
            if x < 0:
                raise ValueError('Negative entropy occupation; no clipping')
            return ((x+1)*mp.log1p(x)-x*mp.log(x))/mp.log(2) if x else M(0)
        terms = [g((nu-1)/2) for nu in nus]
        result.update(entropy_1=terms[0], entropy_2=terms[1], entropy_3=terms[2],
                      chi_BE=terms[0]+terms[1]-terms[2])
    return result


def mi_gh(probabilities, amplitudes, t, noise, order, *, dimension):
    """Direct defining mixture integral; N(0,(1+noise) I_dimension).

    For dimension two the likelihood normalization is 1/(2*pi*sigma^2).
    Its identical conditional/mixture constants cancel inside the log ratio.
    """
    x, weights = roots_hermitenorm(order)
    weights /= math.sqrt(2*math.pi)
    nodes = x[:, None]
    if dimension == 2:
        gx, gy = np.meshgrid(x, x, indexing='ij')
        nodes = np.column_stack((gx.ravel(), gy.ravel()))
        weights = np.outer(weights, weights).ravel()
    elif dimension != 1:
        raise ValueError('dimension must be 1 or 2')
    means = 2*math.sqrt(t)*np.column_stack((amplitudes.real, amplitudes.imag))[:, :dimension]
    sigma = math.sqrt(1+noise)
    conditional = -.5*np.sum(nodes**2, axis=1)
    value = 0.
    for p, center in zip(probabilities, means):
        y = center+sigma*nodes
        log_mix = logsumexp(np.log(probabilities)[None, :]
                           -.5*np.sum(((y[:, None, :]-means[None, :, :])/sigma)**2, axis=-1), axis=1)
        value += p*float(np.dot(weights, conditional-log_mix))/math.log(2)
    return value


def write_csv(name, rows):
    with (OUT/name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def converted(value, *, precise=False):
    if isinstance(value, dict):
        return {k: converted(v, precise=precise) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [converted(v, precise=precise) for v in value]
    if isinstance(value, mp.mpf):
        return mp.nstr(value, 65) if precise else float(value)
    return value


def main():
    if (OUT/'result.json').exists():
        raise FileExistsError('Completed results are immutable')
    startup = json.loads((OUT/'startup_manifest.json').read_text(encoding='utf-8'))
    if digest(Path(startup['manuscript_path'])) != startup['manuscript_sha256']:
        raise ValueError('Manuscript changed since read')
    from scripts.run_manuscript_literal_3moments import verified_candidate
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    candidate = verified_candidate(SOURCE, unconstrained_config())
    if candidate is None or candidate['V_A'] != VA or candidate['nu_raw'] != NU:
        raise ValueError('Exact source identity mismatch')
    with CATALOG.open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if float(r['nu_raw']) == NU and float(r['VA']) == VA]
    if len(rows) != 1 or any(float(rows[0][k]) != candidate[k] for k in ('C', 'w')):
        raise ValueError('Source moments disagree with catalog')
    ensemble = candidate['ensemble']
    p, alpha = [x.detach().cpu().numpy()[0] for x in (ensemble.probabilities, ensemble.amplitudes)]
    nbar = float(np.dot(p, abs(alpha)**2))
    levels, inv = np.unique(alpha.real, return_inverse=True)
    marginal = np.bincount(inv, weights=p)
    product_residual = float(np.max(abs(p.reshape(16, 16)-np.outer(marginal, marginal))))
    raw = np.arange(16)-7.5
    raw_p = np.exp(-NU*raw**2)
    raw_p /= raw_p.sum()
    raw_scale = math.sqrt(VA/(4*np.dot(raw_p, raw**2)))
    source_audit = dict(ensemble_hash=candidate['ensemble_hash'], source_cache_key=candidate['source_cache_key'],
                        canonical_source_cache_key=candidate['canonical_source_cache_key'],
                        source_sha256=digest(SOURCE), catalog_sha256=digest(CATALOG),
                        nbar=nbar, VA_cache=VA, VA_literal_PDF_for_this_ensemble=nbar/2,
                        nbar_required_by_literal_PDF_at_VA_5_475=2*VA,
                        repository_VA_required_for_literal_PDF_point=4*VA,
                        modulation_convention='VA_cache=2*nbar; PDF prints VA=nbar/2',
                        raw_MB_convention='p_ij proportional exp(-nu_raw*((i-7.5)^2+(j-7.5)^2))',
                        raw_to_repo_nu=42.5, spacing=raw_scale,
                        PMF_reconstruction_residual=float(np.max(abs(marginal-raw_p))),
                        amplitude_reconstruction_residual=float(np.max(abs(levels-raw_scale*raw))),
                        product_PMF_residual=product_residual,
                        source_route=candidate['source_moment_route'], support_size=candidate['source_support_size'],
                        truncation='Full 256-state coherent Gram support; AP cache ladder 1050/1250/1450; no finite Fock cutoff',
                        literal_PDF_compatibility='FAILED_VARIANCE_CONVENTION; literal-point SKR not asserted')
    if abs(2*nbar-VA)>1e-12 or max(product_residual, source_audit['PMF_reconstruction_residual'],
                                 source_audit['amplitude_reconstruction_residual'])>1e-12:
        raise ValueError('Source ensemble reconstruction failed')
    checks = []
    def check(name, ok, detail=None):
        checks.append(dict(check=name, status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED', detail=detail))
        if not ok:
            raise AssertionError(f'{name}: {detail}')

    mp.mp.dps = 70
    ch = channel()
    C, w = M(candidate['C']), M(candidate['w'])
    model = security(ch['mean_eta'], ch['mean_sqrt_eta'], M(VA), C, w)
    check('covariance_symplectic_physicality', model['physical'])
    check('retained_PDF_probability_mass', abs(ch['pdf_mass']-1)<M('1e-25'), mp.nstr(ch['pdf_mass']-1, 20))
    check('rounded_slant_distance_consistency', abs(ch['L_m']-M('21939.3102292'))<M('1e-7'))
    cfquad = []
    for power, key in [(0, 'pdf_mass'), (.5, 'mean_sqrt_eta'), (1, 'mean_eta')]:
        d, b, c1, c3, mu, p1 = [float(ch[k]) for k in ('chi2', 'B', 'C1', 'C3', 'mu', 'P1')]
        def integrand(y):
            return math.exp(math.log(p1*d*c1/2)-d*math.log(b)+(d+power)*y
                            +math.log(2)+float(log_ndtr(-math.sqrt(2)*c3*(y-math.log(b)+mu))))
        value, error = quad(integrand, -math.inf, 0, epsabs=2e-15, epsrel=2e-13, limit=400)
        if power == 0:
            value += float(ch['P0'])
        residual = value-float(ch[key])
        check('closed_form_vs_quadrature_'+key, abs(residual)<2e-13, residual)
        cfquad.append(dict(quantity=key, closed_form=float(ch[key]), quadrature=value,
                           residual=residual, quadrature_error_estimate=error))

    t, noise = float(model['eta_f']), float(model['eta_f_xi_f'])
    convergence = []
    for order in (16, 32, 64):
        i2 = mi_gh(p, alpha, t, noise, order, dimension=2)
        i1 = mi_gh(marginal, levels.astype(complex), t, noise, order, dimension=1)
        check(f'normalized_2D_integral_product_identity_GH{order}', abs(i2-2*i1)<2e-13, i2-2*i1)
        convergence.append(dict(order=order, I_AB_2D=i2, I_AB_1D=i1,
                                beta_I_AB_2D=BETA*i2, chi_BE=float(model['chi_BE']),
                                K_2D=BETA*i2-float(model['chi_BE']), K_1D=BETA*i1-float(model['chi_BE']),
                                difference_2D_from_previous=None if len(convergence)==0 else i2-convergence[-1]['I_AB_2D']))
        print('GH', order, convergence[-1], flush=True)
    check('MI_GH16_32_64_convergence', max(abs(r['I_AB_2D']-convergence[-1]['I_AB_2D']) for r in convergence)<2e-13)
    for dim in (1, 2):
        check(f'vacuum_MI_zero_dimension_{dim}', abs(mi_gh(np.array([1.]), np.array([0j]), .2, .01, 16, dimension=dim))<1e-14)
    check('discrete_entropy_MI_bound', 0<=i2<=-float(np.dot(p,np.log2(p))))
    gamma = np.array([[float(model['V']), 0, float(model['Z']), 0],
                      [0, float(model['V']), 0, -float(model['Z'])],
                      [float(model['Z']), 0, float(model['W']), 0],
                      [0, -float(model['Z']), 0, float(model['W'])]])
    omega = np.kron(np.eye(2), np.array([[0., 1.], [-1., 0.]]))
    eigen = np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    check('independent_matrix_symplectic_spectrum', np.max(abs(eigen-np.sort([float(model['nu_1']),float(model['nu_2'])])))<1e-12)
    check('uncertainty_matrix_positive', float(np.linalg.eigvalsh(gamma+1j*omega).min())>0)
    mp.mp.dps = 100
    high = channel()
    high_model = security(high['mean_eta'], high['mean_sqrt_eta'], M(VA), C, w)
    precision_residual = abs(high_model['chi_BE']-model['chi_BE'])
    check('70_to_100_digit_Holevo_stability', precision_residual<M('1e-60'), mp.nstr(precision_residual, 8))
    relabeled = security(ch['mean_eta'], ch['mean_sqrt_eta'], M(str(nbar))/2, C, w)
    check('literal_relabeling_fails_physicality_as_expected', not relabeled['physical'])
    model.update(I_AB=M(i2), beta_I_AB=M(BETA)*M(i2), K=M(BETA)*M(i2)-model['chi_BE'],
                 I_AB_1D=M(i1), K_1D=M(BETA)*M(i1)-model['chi_BE'])
    reference = dict(I_AB=.0019224444, chi_BE=.0017299097, K=.0000964)
    comparison = [dict(quantity=k, recalculated=float(model[k]), reference=v,
                       difference=float(model[k])-v, relative_difference=(float(model[k])-v)/v) for k,v in reference.items()]
    fields = ('mean_eta','mean_sqrt_eta','eta_f','variance_sqrt_eta','mean_eta_xi_n','eta_f_xi_f','xi_f',
              'C','w','V','W','Z','nu_1','nu_2','nu_3','I_AB','beta_I_AB','chi_BE','K')
    write_csv('required_table.csv', [dict(parameter=k, value=mp.nstr(model[k], 24)) for k in fields])
    write_csv('MI_convergence.csv', convergence)
    write_csv('channel_closed_vs_quadrature.csv', cfquad)
    write_csv('reference_comparison.csv', comparison)
    np.savez(OUT/'verified_ensemble.npz', probabilities=p, amplitudes=alpha)
    result = dict(status='CURRENTLY_VERIFIED_PASS', scope='SINGLE_POINT_EXPLICIT_CACHE_NORMALIZATION_HYBRID_DIAGNOSTIC',
                  security_status='UNVALIDATED_SECURITY_MODEL', lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
                  primary='normalized 2D MI with per-component variance 1+eta_f*xi_f; homodyne nu_3 unchanged',
                  literal_PDF_point_status='BLOCKED_BY_VARIANCE_AND_MB_NOTATION_INCONSISTENCIES',
                  parameters=dict(nu_raw=NU, VA=VA, beta=BETA, xi_ch=XI, R=1, xi_det=0,
                                  zenith_deg=30, divergence_full_rad=233e-6, receiver_diameter_m=.08),
                  channel=converted(ch), model=converted(model), high_precision_model=converted(model, precise=True),
                  source_audit=source_audit, literal_VA_relabel_audit=converted(relabeled),
                  convergence=convergence, comparisons= comparison, checks=checks,
                  channel_equations_changed=False, source_moments_recomputed=False, SKR_interpolated=False,
                  PDF_renormalized=False, negative_SKR_clipped=False, optimization_run=False,
                  HV_and_Gd_closure='Repository HV and G_d formulas, absent from PDF; explicitly used as diagnostic convention',
                  precision_dps=[70,100], precision_chi_residual=mp.nstr(precision_residual, 12),
                  producer_sha256=digest(Path(__file__)), manuscript_sha256=startup['manuscript_sha256'],
                  inputs_sha256={str(path.relative_to(ROOT)):digest(path) for path in (SOURCE,CATALOG,ROOT/'src/modulation/normalization.py',ROOT/'src/modulation/qam256.py',ROOT/'src/modulation/joint_ps_gs.py',ROOT/'scripts/exact_cache_provenance.py',ROOT/'scripts/run_manuscript_literal_3moments.py',ROOT/'scripts/run_theta10_D55_unconstrained_three_scheme.py',ROOT/'scripts/run_exact_mb_test2.py',ROOT/'src/channel/pointing_error.py',ROOT/'src/channel/scintillation.py')},
                  versions=dict(numpy=np.__version__,mpmath=mp.__version__),
                  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    (OUT/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('CHECKS', len(checks), 'PASS; PRIMARY K', mp.nstr(model['K'], 24), flush=True)


if __name__ == '__main__':
    main()
