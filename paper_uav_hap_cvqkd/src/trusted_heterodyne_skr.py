"""Channel-only fading moments and explicit trusted heterodyne diagnostic.

Appendix A: https://arxiv.org/pdf/2002.03476.pdf (v1).
The Gaussian-surrogate MI / discrete fading security model is not validated.
"""
from dataclasses import replace
import math
import numpy as np
import torch
from scripts import run_ao_effective_channel_no_fading_noise_reference as sources
from src.manuscript_literal_3moments import entropy
from src.cvqkd.mutual_information import deterministic_mutual_information, _product_qam_factors

MODEL = 'channel_only_fading_trusted_heterodyne_v1'
SECURITY_STATUS = 'UNVALIDATED_SECURITY_MODEL'
TOLERANCE = 1e-10


def finite(value, name, lower=0.):
    value = float(value)
    if not math.isfinite(value) or value < lower:
        raise ValueError('Invalid ' + name)
    return value


def effective_channel(moments, VA):
    """m_xi is channel excess only; total-noise fields are never inputs."""
    VA = finite(VA, 'VA')
    if VA == 0:
        raise ValueError('VA must be positive')
    m1 = finite(moments['mean_eta'], 'mean eta')
    mh = finite(moments['mean_sqrt_eta'], 'mean sqrt eta')
    t = mh * mh
    if moments.get('moment_law') == 'deterministic_delta':
        t = finite(moments['deterministic_transmissivity'], 'delta T')
        if m1 != t or mh != math.sqrt(t):
            raise ValueError('Inconsistent exact delta law')
    if not 0 <= t <= m1 <= 1 or (mh > 0 and t == 0) or (mh == 0 and m1 != 0):
        raise ValueError('Invalid fading moments; no clipping')
    if not math.isclose(moments.get('physical_probability_mass', 1.), 1., abs_tol=TOLERANCE, rel_tol=0.):
        raise ValueError('Fading law must be normalized, preserving the AoA atom')
    xi = moments.get('channel_excess_noise', moments.get('xi_ch'))
    if xi is not None:
        xi = finite(xi, 'channel excess noise')
    if 'mean_eta_xi_channel' in moments:
        mxi = finite(moments['mean_eta_xi_channel'], 'channel-only third moment')
        if xi is not None and not math.isclose(mxi, m1 * xi, rel_tol=1e-12, abs_tol=1e-14):
            raise ValueError('Constant channel excess and channel-only moment disagree')
    elif xi is not None:
        mxi = m1 * xi
    else:
        raise ValueError('Explicit channel-only noise moment required; total noise is ambiguous')
    if t == 0 and mxi != 0:
        raise ValueError('Zero-channel moment must have zero channel excess output')
    fading = (m1 - t) * VA
    noise = fading + mxi
    b = 1 + m1 * VA + mxi
    b_effective = 1 + t * VA + noise
    if not math.isclose(b, b_effective, abs_tol=1e-12, rel_tol=1e-13):
        raise ValueError('Bob pre-detector variance identity failed')
    return dict(mean_eta=m1, mean_sqrt_eta=mh, m_xi=mxi, mean_eta_xi_channel=mxi,
                channel_excess_noise=xi, T_eff=t, variance_sqrt_eta=m1-t,
                fading_variance=m1-t, fading_excess_output=fading, Delta_fad=fading,
                channel_excess_output=mxi, effective_excess_output=noise, N_eff=noise,
                effective_excess_input=noise/t if t else None, xi_eff=noise/t if t else None,
                a=1+VA, b=b, b_pre=b, W_pre=b, W_pre_effective=b_effective,
                scientific_model=MODEL, security_status=SECURITY_STATUS,
                MI_method='effective_gaussian_MI', exact_pooled_fading_likelihood=False)


def receiver(mapping, eta_B=1., nu_B=0.):
    eta_B = finite(eta_B, 'detector efficiency')
    nu_B = finite(nu_B, 'electronic noise')
    if not 0 < eta_B <= 1:
        raise ValueError('Detector efficiency must be in (0,1]')
    t, noise = mapping['T_eff'], mapping['effective_excess_output']
    chi_het = (2-eta_B+2*nu_B)/eta_B
    line = (1+noise)/t-1 if t else None
    total = line+chi_het/t if t else None
    return dict(eta_B=eta_B, nu_B=nu_B, chi_het=chi_het, chi_line=line, chi_tot=total,
                detector_gain_squared=eta_B*t, sigma2_complex=1+nu_B+eta_B*noise/2,
                V_B2=eta_B*mapping['W_pre']+1-eta_B+2*nu_B,
                electronic_noise_convention='output-referred variance per detected arm, Appendix A nu_B = repository xi_det',
                detector_security_convention='trusted',
                likelihood='CN(sqrt(eta_B*T_eff)*alpha,1+nu_B+eta_B*N_eff/2)')


def heterodyne_likelihood(y, alpha, mapping, eta_B=1., nu_B=0.):
    r = receiver(mapping, eta_B, nu_B)
    variance = r['sigma2_complex']
    return np.exp(-np.abs(np.asarray(y)-math.sqrt(r['detector_gain_squared'])*alpha)**2/variance)/(math.pi*variance)


def symplectic_spectrum(matrix):
    matrix = np.asarray(matrix, dtype=float)
    n = len(matrix)//2
    omega = np.kron(np.eye(n), [[0., 1.], [-1., 0.]])
    if matrix.shape != (2*n, 2*n) or not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, rtol=0, atol=1e-12):
        raise ValueError('Invalid covariance matrix')
    if np.linalg.eigvalsh(matrix).min() <= 0 or np.linalg.eigvalsh(matrix+1j*omega).min() < -TOLERANCE:
        raise ValueError('Nonphysical covariance; no correlation clipping')
    values = np.linalg.eigvals(1j*omega@matrix)
    if np.max(np.abs(values.imag)) > TOLERANCE:
        raise ValueError('Nonreal symplectic spectrum')
    values = np.sort(np.abs(values.real)).reshape(n, 2)
    if np.max(np.abs(values[:, 0]-values[:, 1])) > TOLERANCE or values.min() < 1-TOLERANCE:
        raise ValueError('Invalid symplectic doublets')
    return values.mean(axis=1)


def spectral_entropy(values):
    # Only entropy's continuous vacuum limit is used within the declared roundoff allowance.
    values = np.asarray(values)
    if values.min() < 1-TOLERANCE:
        raise ValueError('Entropy outside physical domain')
    return sum(entropy(max(0., (float(v)-1)/2)) for v in values)


def trusted_holevo(a, b, z, eta_B=1., nu_B=0.):
    """Appendix A AFG conditioning, cross-checked by an independent AB purification.

    The two-mode purification avoids the singular thermal ancilla at eta_B=1.
    It also provides the finite additive-electronic-noise limit at unit efficiency.
    """
    r = receiver(dict(T_eff=0., effective_excess_output=0., W_pre=b), eta_B, nu_B)
    I, Z = np.eye(2), np.diag([1., -1.])
    gamma = np.block([[a*I, z*Z], [z*Z, b*I]])
    ab = symplectic_spectrum(gamma)
    radicand = (a+b)**2-4*z*z
    if radicand <= 0:
        raise ValueError('Invalid standard-form covariance')
    s = math.sqrt(radicand)
    va, vb = (s+a-b)/2, (s-a+b)/2
    ch = math.sqrt((a+b+s)/(2*s)); sh = z/(s*ch)
    transform = np.block([[ch*I, sh*Z], [sh*Z, ch*I]])
    diag = np.diag([va, va, vb, vb])
    if not np.allclose(transform@diag@transform.T, gamma, atol=1e-12, rtol=1e-12):
        raise ValueError('AB purification reconstruction failed')
    if min(va, vb) < 1-TOLERANCE:
        raise ValueError('Unphysical purification spectrum')
    cross = transform@np.block([[math.sqrt(max(0., (va-1)*(va+1)))*Z, np.zeros((2,2))],
                                [np.zeros((2,2)), math.sqrt(max(0., (vb-1)*(vb+1)))*Z]])
    cross_b = math.sqrt(eta_B)*cross[2:4, :]
    eve_conditional = diag-cross_b.T@cross_b/(r['V_B2']+1)
    eve_spectrum = symplectic_spectrum(eve_conditional)
    conditional = np.r_[1., eve_spectrum]
    appendix = None
    residual = 0.
    appendix_status = 'IDEAL_OR_ADDITIVE_NOISE_LIMIT_USING_PURIFICATION'
    upsilon = 1+2*nu_B/(1-eta_B) if eta_B < 1 else None
    if upsilon is not None and np.finfo(float).eps*upsilon**2 <= TOLERANCE:
        appendix_status = 'CURRENTLY_VERIFIED_PASS'
        epr = math.sqrt((upsilon-1)*(upsilon+1))
        initial = np.zeros((8,8));initial[:4,:4]=gamma
        initial[4:,4:] = np.block([[upsilon*I,epr*Z],[epr*Z,upsilon*I]])
        beam = np.eye(8); u,v=math.sqrt(eta_B),math.sqrt(1-eta_B)
        beam[2:6,2:6]=np.block([[u*I,v*I],[-v*I,u*I]])
        after = beam@initial@beam.T  # A,B2,F,G; signs are a local phase convention.
        keep=[0,1,4,5,6,7]; measured=[2,3]
        afg = after[np.ix_(keep,keep)]
        correlation = after[np.ix_(keep,measured)]
        appendix = afg-correlation@np.linalg.solve(after[np.ix_(measured,measured)]+I,correlation.T)
        conditional = symplectic_spectrum(appendix)
        residual = float(np.max(np.abs(np.sort(conditional)-np.sort(np.r_[1.,eve_spectrum]))))
        if residual > TOLERANCE:
            raise ValueError('Appendix A and independent purification disagree')
    elif eta_B < 1:
        appendix_status = 'ILL_CONDITIONED_THERMAL_REPRESENTATION_USING_EQUIVALENT_PURIFICATION'
    if (eta_B, nu_B) == (1., 0.):
        conditional = np.array([a-z*z/(b+1)])
    chi = spectral_entropy(ab)-spectral_entropy(eve_spectrum)
    if not math.isfinite(chi) or chi < -TOLERANCE:
        raise ValueError('Invalid Holevo information')
    return dict(chi_BE=chi,lambda_1=float(ab[-1]),lambda_2=float(ab[0]),
                conditional_symplectic_eigenvalues=conditional.tolist(),
                conditional_eve_symplectic_eigenvalues=eve_spectrum.tolist(),
                conditional_covariance_AFG=None if appendix is None else appendix.tolist(),
                conditional_covariance_E=eve_conditional.tolist(),Gamma_AB=gamma.tolist(),
                appendix_purification_spectrum_residual=residual,
                entropy_roundoff_modes=[float(v) for v in np.r_[ab,conditional,eve_spectrum] if v<1],
                appendix_covariance_status=appendix_status,
                conditional_measurement='trusted_heterodyne_Appendix_A',
                ideal_conditional_eigenvalue=a-z*z/(b+1) if (eta_B,nu_B)==(1.,0.) else None)



def low_snr_discrete_mi(ensemble, gain_squared, variance, order):
    """Same product-QAM GH integral, regrouped with expm1/log1p and +/- nodes.

    Avoids subtracting entropy from almost equal conditional entropy at low SNR.
    The exact normalization identity sum(p)=1 is used without changing the source.
    """
    factors = _product_qam_factors(ensemble.probabilities,
                                 math.sqrt(gain_squared)*ensemble.amplitudes)
    nodes, weights = np.polynomial.hermite.hermgauss(order)
    total = 0.
    for probabilities, levels in ((factors[0], factors[2]), (factors[1], factors[3])):
        p = probabilities.detach().cpu().numpy()[0].astype(np.longdouble)
        x = levels.detach().cpu().numpy()[0].astype(np.longdouble)/math.sqrt(variance)
        delta = x[:, None]-x[None, :]
        integral = np.zeros(len(p), dtype=np.longdouble)
        for node, weight in zip(nodes, weights/math.sqrt(math.pi)):
            plus = np.expm1(-delta*delta+2*node*delta)@p
            minus = np.expm1(-delta*delta-2*node*delta)@p
            integral -= weight*(np.log1p(plus)+np.log1p(minus))/2
        total += float(p@integral/math.log(2))
    if not math.isfinite(total) or total < 0:
        raise FloatingPointError('Stable discrete low-SNR integral unresolved')
    return total


def evaluate_batch(candidate, moment_rows, config, authorized_hashes, *, eta_B=1., nu_B=0.):
    ensemble = sources.authenticate(candidate, authorized_hashes, config)
    mappings=[effective_channel(m,candidate['V_A']) for m in moment_rows]
    if not mappings:
        raise ValueError('Empty channel batch')
    outputs=[]; active=[]
    for i,m in enumerate(mappings):
        r=receiver(m,eta_B,nu_B)
        z=2*m['mean_sqrt_eta']*candidate['C']-math.sqrt(2*m['N_eff']*candidate['w'])
        common=dict(m,**r,nu_raw=candidate['nu_raw'],V_A=candidate['V_A'],C=candidate['C'],w=candidate['w'],
                    ensemble_hash=candidate['ensemble_hash'],source_cache_key=candidate['source_cache_key'],
                    source_path=candidate['source_path'],source_payload_sha256=sources.digest(sources.ROOT/candidate['source_path']),
                    Z_star=z,Z_signal=2*m['mean_sqrt_eta']*candidate['C'],Z_penalty=math.sqrt(2*m['N_eff']*candidate['w']),
                    Holevo_target='chi_BE_at_direct_Z_star',numerical_repairs=[])
        if m['T_eff']==0:
            common.update(I_AB=0.,beta_I_AB=0.,chi_BE=0.,SKR=0.,K_raw=0.,K_usable=0.,QKD_expressions_evaluated=False)
        else:
            common.update(trusted_holevo(m['a'],m['b'],z,eta_B,nu_B));active.append(i)
        outputs.append(common)
    if not active:
        return outputs
    batch=replace(ensemble,probabilities=ensemble.probabilities.expand(len(active),-1),
                  amplitudes=ensemble.amplitudes.expand(len(active),-1),declared_va=ensemble.declared_va.expand(len(active)))
    t=torch.tensor([outputs[i]['detector_gain_squared'] for i in active],dtype=torch.float64)
    eps=torch.tensor([2*(outputs[i]['sigma2_complex']-1)/outputs[i]['detector_gain_squared'] for i in active],dtype=torch.float64)
    with torch.no_grad():
        mi=[deterministic_mutual_information(batch,t,eps,quadrature_order=o,implementation='product') for o in (8,16,32)]
    beta=float(config['cvqkd']['beta_reconciliation'])
    if beta!=.95:
        raise ValueError('Reconciliation convention differs from current repository')
    hx=float(-torch.special.xlogy(ensemble.probabilities,ensemble.probabilities).sum()/math.log(2))
    for k,i in enumerate(active):
        row=outputs[i]
        snr=row['detector_gain_squared']*candidate['V_A']/(2*row['sigma2_complex'])
        row['MI_low_snr_regrouping']=snr < math.sqrt(np.finfo(float).eps)
        if row['MI_low_snr_regrouping']:
            for order, values in zip((8,16,32), mi):
                values[k]=low_snr_discrete_mi(ensemble,row['detector_gain_squared'],row['sigma2_complex'],order)
        if abs(float(mi[2][k]-mi[1][k]))>1e-8:
            raise ValueError('GH16/32 discrete MI convergence unresolved')
        value=float(mi[2][k]);row=outputs[i]
        if not 0<=value<=hx:
            raise ValueError('Discrete MI outside source entropy')
        raw=beta*value-row['chi_BE']
        row.update(I_AB=value,beta_rec=beta,beta_I_AB=beta*value,SKR=raw,K_raw=raw,K_usable=max(0.,raw),
                   MI_orders=[dict(order=o,I_AB=float(v[k]),SKR=beta*float(v[k])-row['chi_BE']) for o,v in zip((8,16,32),mi)],
                   QKD_expressions_evaluated=True,MI_detector_gain_squared=float(t[k]),MI_kernel_epsilon=float(eps[k]))
    return outputs


def evaluate_candidate(candidate,moments,config,authorized_hashes,**detector):
    return evaluate_batch(candidate,[moments],config,authorized_hashes,**detector)[0]
