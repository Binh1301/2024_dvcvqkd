"""Isolated v43 audit: real homodyne MI, explicit noise planes, unchanged sources."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr, logsumexp, roots_hermitenorm

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('_v43_preserved_homodyne',
    ROOT/'results/untrusted_positive_skr_feasibility_20261022/model.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value, name, nonnegative=False):
    value = float(value)
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError('Invalid '+name)
    return value


def validate_source(c):
    p = np.asarray(c['p'], dtype=float)
    alpha = np.asarray(c['alpha'], dtype=complex)
    if p.shape != (256,) or alpha.shape != (256,) or not np.isfinite(alpha).all():
        raise ValueError('256 finite physical amplitudes required')
    if not np.isfinite(p).all() or np.any(p <= 0) or abs(p.sum()-1) > 1e-13:
        raise ValueError('Invalid source probabilities')
    va = finite(c['VA'], 'source VA', True)
    if abs(2*np.dot(p, abs(alpha)**2)-va) > 2e-12 or abs(np.dot(p, alpha)) > 1e-12:
        raise ValueError('Source normalization/origin mismatch')
    if abs(np.dot(p, alpha**2)) > 1e-12:
        raise ValueError('Scalar covariance requires C4 symmetry')
    payload_path = ROOT/c['source_path']
    payload = read(payload_path)
    if sha(payload_path) != c['source_sha256'] or payload['ensemble_hash'] != c['ensemble_hash']:
        raise ValueError('Source payload identity changed')
    if any(payload[k] != c[k] for k in ['C', 'w']) or payload['V_A_hex'] != va.hex():
        raise ValueError('Exact source moments/VA mismatch')
    if c['C'] < 0 or c['w'] < 0:
        raise ValueError('Invalid exact correlation moments')
    return p, alpha


def marginal(p, alpha, axis='X'):
    if axis not in ['X', 'P']:
        raise ValueError('Only one real homodyne quadrature is allowed')
    x = 2*(alpha.real if axis == 'X' else alpha.imag)
    levels, inverse = np.unique(x, return_inverse=True)
    return levels, np.bincount(inverse, weights=p)


def homodyne_mi(p, alpha, t, variance, *, order=64, axis='X', grouped=True, scale=1.):
    """Defining real discrete-input Gaussian MI; invertible scaling is classical."""
    p, alpha = np.asarray(p, float), np.asarray(alpha, complex)
    t = finite(t, 'MI signal gain squared', True)
    variance = finite(variance, 'conditional variance')
    scale = finite(scale, 'classical scale')
    if variance <= 0 or scale == 0 or np.any(p <= 0) or abs(p.sum()-1) > 1e-13:
        raise ValueError('Invalid real conditional likelihood')
    if grouped:
        levels, p = marginal(p, alpha, axis)
    else:
        if axis not in ['X', 'P']:
            raise ValueError('HOMODYNE ONLY')
        levels = 2*(alpha.real if axis == 'X' else alpha.imag)
    means = scale*math.sqrt(t)*levels
    sigma = abs(scale)*math.sqrt(variance)
    nodes, weights = roots_hermitenorm(order)
    weights /= math.sqrt(2*math.pi)
    result = 0.
    for probability, mean in zip(p, means):
        y = mean+sigma*nodes
        mixture = logsumexp(np.log(p)[None, :]
            -.5*((y[:, None]-means[None, :])/sigma)**2, axis=1)
        result += probability*float(weights@(-.5*nodes**2-mixture))/math.log(2)
    if not math.isfinite(result) or result < -2e-12:
        raise ValueError('Invalid MI; no clipping')
    return result


def independent_mi(p, alpha, t, variance):
    """Adaptive output-density entropy integration, independent of GH expectation."""
    x, px = marginal(np.asarray(p), np.asarray(alpha))
    means = math.sqrt(t)*x
    sigma = math.sqrt(variance)
    normalizer = math.log(sigma*math.sqrt(2*math.pi))
    def integrand(y):
        log_density = float(logsumexp(np.log(px)-.5*((y-means)/sigma)**2)-normalizer)
        return -math.exp(log_density)*log_density/math.log(2)
    points = np.unique(np.r_[means.min()-12*sigma, means, means.max()+12*sigma])
    values = [quad(integrand, a, b, epsabs=2e-12, epsrel=2e-12, limit=200)
              for a, b in zip(points, points[1:])]
    return sum(v for v, _ in values)-.5*math.log2(2*math.pi*math.e*variance), sum(e for _, e in values)


def conditional_pdf(y, mean, variance):
    if np.iscomplexobj(y) or np.iscomplexobj(mean) or variance <= 0:
        raise ValueError('Normalized homodyne density requires a real mean and variance>0')
    return np.exp(-.5*((np.asarray(y)-mean)**2)/variance)/math.sqrt(2*math.pi*variance)


def xi_detector(eta_det, epsilon_det, definition, independent=None):
    eta_det = finite(eta_det, 'eta_det')
    epsilon_det = finite(epsilon_det, 'epsilon_det', True)
    if not 0 < eta_det <= 1:
        raise ValueError('0<eta_det<=1 required')
    if definition == 'A_epsilon_over_eta':
        return epsilon_det/eta_det
    if definition == 'B_chi_hom':
        return (1-eta_det+epsilon_det)/eta_det
    if definition == 'independent_explicit' and independent is not None:
        return finite(independent, 'independent xi_det', True)
    raise ValueError('xi_det definition/value unresolved; no epsilon_det alias')


def effective(moments, va, eta_det, epsilon_det, *, tolerance=1e-10):
    eta_det = finite(eta_det, 'eta_det')
    epsilon_det = finite(epsilon_det, 'epsilon_det', True)
    va = finite(va, 'VA', True)
    m0, m1, mh, p0 = [finite(moments[k], k, True) for k in ['M0', 'm1', 'mh', 'P0']]
    if abs(m0-1) > tolerance:
        raise ValueError('UNNORMALIZED_CHANNEL_PDF: no automatic renormalization')
    if not 0 < eta_det <= 1 or not 0 <= p0 <= 1 or va <= 0:
        raise ValueError('Invalid detector/source/outage parameters')
    tf = mh*mh
    if moments.get('law') == 'deterministic_delta':
        if mh != math.sqrt(m1):
            raise ValueError('Tagged delta-law moments do not match')
        tf = m1  # Exact delta-law identity avoids squaring a rounded square root.
    if not 0 <= tf <= m1 <= 1:
        raise ValueError('Invalid bounded moments; no clipping')
    nf = (m1-tf)*va
    nc = m1*.0186
    noise = eta_det*(nf+nc)+epsilon_det
    return dict(eta_f=tf, T_quantum=eta_det*tf, N_fading_pre=nf, N_channel_pre=nc,
        N_detector_pre=epsilon_det/eta_det, N_post=noise, sigma2_output=1+noise,
        sigma2_rescaled=(1+noise)/eta_det, signal_gain2_rescaled=tf,
        a=1+va, b=1+eta_det*tf*va+noise, eta_det=eta_det, epsilon_det=epsilon_det,
        vacuum_output=1., detector_loss_vacuum_already_in_unit_vacuum=True,
        quantum_covariance_plane='physical_output_after_untrusted_loss_and_noise')


def evaluate_physical(c, moments, eta_det, epsilon_det, *, order=64, grid=33):
    p, alpha = validate_source(c)
    e = effective(moments, c['VA'], eta_det, epsilon_det)
    center = 2*math.sqrt(e['T_quantum'])*c['C']
    radius = math.sqrt(2*e['N_post']*c['w'])
    # Existing strict homodyne/full-Z routine: exact boundary identities, no spectrum clipping.
    h = legacy.full_holevo(e['a'], e['b'], center, radius, grid)
    iab = homodyne_mi(p, alpha, e['T_quantum'], e['sigma2_output'], order=order)
    scaled = homodyne_mi(p, alpha, e['T_quantum'], e['sigma2_output'], order=order,
                         scale=1/math.sqrt(eta_det))
    if abs(iab-scaled) > 2e-12 or min(h[k] for k in ['nu_1', 'nu_2', 'nu_3']) < 1 or h['chi_BE'] < 0:
        raise ValueError('MI scaling or homodyne covariance failure')
    _, px = marginal(p, alpha)
    entropy = -float(px@np.log2(px))
    capacity = .5*math.log2(1+e['T_quantum']*c['VA']/e['sigma2_output'])
    if iab > min(entropy, capacity)+2e-10:
        raise ValueError('MI exceeds quadrature entropy/Gaussian reference bound')
    return dict(**e, **h, I_AB=iab, I_AB_rescaled=scaled, beta_I_AB=.95*iab,
        K_raw=.95*iab-h['chi_BE'], quadrature_entropy=entropy, gaussian_capacity_reference=capacity,
        source_hash=c['ensemble_hash'], C=c['C'], w=c['w'], VA=c['VA'], nu_raw=c['nu_raw'],
        receiver='homodyne_1D', detector_security='untrusted', model='C_physical_output_gaussian_effective',
        channel_law=moments['law'], approximation='moment_matched_Gaussian_not_exact_fading_likelihood',
        security_valid=False, recommended_secure_default=False, GH_order=order)


def literal_noise(moments, va, eta_det, epsilon_det, definition, *, outage='limit', independent=None):
    xd = xi_detector(eta_det, epsilon_det, definition, independent)
    if outage not in ['limit', 'active_only']:
        raise ValueError('Outage contribution must be explicit')
    mass = moments['M0']-(moments['P0'] if outage == 'active_only' else 0.)
    nf = (moments['m1']-moments['mh']**2)*va
    mn = .0186*moments['m1']+xd*mass
    return dict(xi_det=xd, xi_det_definition=definition, M0=moments['M0'],
        third_noise_moment=mn, outage_extension=outage, detector_mass_factor=mass,
        eta_f=moments['mh']**2, N_literal=nf+mn, sigma2_literal=1+nf+mn,
        signal_gain2_literal=moments['mh']**2)


def evaluate_literal(c, moments, eta_det, epsilon_det, definition, *, real_projection=False, outage='limit'):
    p, alpha = validate_source(c)
    e = literal_noise(moments, c['VA'], eta_det, epsilon_det, definition, outage=outage)
    # The printed modulus-square with complex alpha is not a real Gaussian density.
    masses = np.exp(-2*e['eta_f']*alpha.imag**2/e['sigma2_literal'])
    record = dict(**e, model='B_literal_v43_as_printed', I_AB=None, chi_BE=None, K_raw=None,
        minimum_printed_conditional_mass=float(masses.min()), maximum_printed_conditional_mass=float(masses.max()),
        security_valid=False, receiver='homodyne_1D', detector_security='untrusted',
        channel_law=moments['law'], VA=c['VA'], nu_raw=c['nu_raw'], source_hash=c['ensemble_hash'])
    if not real_projection:
        return {**record, 'status':'FAILED_COMPLEX_MEAN_IN_REAL_PDF'}
    if abs(moments['M0']-1)>1e-10:
        return {**record, 'status':'FAILED_CHANNEL_NORMALIZATION', 'model':'B_v43_noise_real_projection_diagnostic'}
    t, noise = e['eta_f'], e['N_literal']
    h = legacy.full_holevo(1+c['VA'], 1+t*c['VA']+noise,
        2*math.sqrt(t)*c['C'], math.sqrt(2*noise*c['w']))
    mi = homodyne_mi(p, alpha, t, 1+noise)
    return {**record, **h, 'I_AB':mi, 'K_raw':.95*mi-h['chi_BE'],
        'status':'DIAGNOSTIC_REAL_PROJECTION_NOT_LITERAL_PRINTED_DENSITY',
        'model':'B_v43_noise_real_projection_diagnostic', 'quantum_T':t, 'sigma2':1+noise,
        'detector_loss_omitted_from_literal_signal':True}


def raw_coefficients(ch, rho=0.):
    with mp.workdps(90):
        B, d, v, sigma, rho = [mp.mpf(str(v)) for v in [ch['B'], ch['d'], ch['v'], ch['sigma_s_m'], rho]]
        weq = mp.mpf(str(ch['w_eq_m']))
        lc = rho*rho/(sigma*sigma)+v*d*(1+d)/2
        c3 = (32*rho*rho*sigma*sigma/weq**4+2*v)**(-mp.mpf('.5'))
        mu = 6*rho*rho/weq**2+v*(1+2*d)/2
        return dict(B=B, d=d, v=v, logC1=lc, C3=c3, mu=mu, P0=mp.mpf(str(ch['P0'])), P1=mp.mpf(str(ch['P1'])), rho=rho, sigma=sigma)


def raw_pdf_moments(ch, rho=0.):
    """Literal Eqs18-20, explicit zero atom; integrate the same Eq10 without repair."""
    with mp.workdps(90):
        c = raw_coefficients(ch, rho)
        B, d, c3, mu, lc = [c[k] for k in ['B', 'd', 'C3', 'mu', 'logC1']]
        x1 = -mp.log(B)+mu
        def Q(a):
            return (mp.exp(a*x1-a*mu)*mp.erfc(c3*x1)+mp.exp(a*a/(4*c3*c3)-a*mu)*mp.erfc(a/(2*c3)-c3*x1))/2
        closed = {q: c['P1']*B**mp.mpf(str(q))*d*mp.exp(lc)/(d+mp.mpf(str(q)))*Q(d+mp.mpf(str(q))) for q in [0., .5, 1.]}
        mass = c['P0']+closed[0.]
        missing = 1-mass
        p1, bf, df, cf, mf, lf = [float(c[k]) for k in ['P1', 'B', 'd', 'C3', 'mu', 'logC1']]
        def log_density(y):
            return math.log(p1*df/2)+lf-df*math.log(bf)+df*y+math.log(2)+float(log_ndtr(-math.sqrt(2)*cf*(y-math.log(bf)+mf)))
        direct = {}
        for q in [0., .5, 1.]:
            value, error = quad(lambda y: math.exp(log_density(y)+q*y), -math.inf, 0., epsabs=2e-12, epsrel=2e-12, limit=400)
            direct[q] = dict(value=value, error=error, closed=float(closed[q]), residual=value-float(closed[q]))
        tail, tail_error = quad(lambda y: math.exp(log_density(y)), 0., math.inf, epsabs=2e-12, epsrel=2e-12, limit=400)
        return dict(M0=float(mass), M0_decimal=mp.nstr(mass, 80), m1=float(closed[1.]), mh=float(closed[.5]),
            P0=float(c['P0']), active_retained_mass=float(closed[0.]), raw_upper_tail_mass=float(missing),
            upper_tail_decimal=mp.nstr(missing, 80), upper_tail_quadrature=tail, upper_tail_error=tail_error,
            direct=direct, probability_residual=float(mass-1), normalized_within_tolerance=abs(mass-1)<=mp.mpf('1e-10'),
            renormalized=False, clipped=False, law='manuscript43_Eq10_retained_0_to_1', rho_m=rho,
            coefficients={k:float(v) for k,v in c.items()})
