import math
from functools import lru_cache

import numpy as np
from scipy.special import comb as sp_comb

from ..config import N_FOCK, QAM_V_DISC_GAUSS
from ..utils.logger import _log_calc
from .gm import _G, _eps_total


def _qam_constellation_probs(VA, M, prob_model="binomial", v=QAM_V_DISC_GAUSS):
    m = int(round(np.sqrt(M)))
    if m * m != M:
        raise ValueError("M-QAM requires M=m^2.")
    ks = np.arange(m)
    # Eq. (13)/(17) consistency: choose grid scaling so binomial-shaped QAM has
    # modulation variance VA (i.e., E[|alpha|^2] = VA).
    scale = np.sqrt(2 * VA) / np.sqrt(m - 1) if m > 1 else 0.0
    xvals = scale * (ks - (m - 1) / 2)
    yvals = xvals.copy()
    alpha = np.array([x + 1j * y for x in xvals for y in yvals], dtype=np.complex128)
    if prob_model == "binomial":
        pk = np.array([float(sp_comb(m - 1, k, exact=True)) for k in ks], dtype=float)
        pk /= pk.sum()
        prob = np.array([pk[k] * pk[l] for k in range(m) for l in range(m)], dtype=float)
    elif prob_model == "disc_gaussian":
        prob = np.array([np.exp(-v * (x * x + y * y)) for x in xvals for y in yvals], dtype=float)
        prob /= prob.sum()
    else:
        raise ValueError("prob_model must be 'binomial' or 'disc_gaussian'.")
    return alpha, prob


def _optimize_disc_gaussian_v(VA, M):
    alpha, _ = _qam_constellation_probs(VA, M, prob_model="binomial", v=1.0)
    r2 = np.abs(alpha) ** 2
    grid = np.concatenate([
        np.linspace(0.02, 0.8, 80),
        np.linspace(0.81, 3.0, 80),
    ])
    best_v, best_err = 0.5, np.inf
    for vv in grid:
        p = np.exp(-vv * r2)
        p /= p.sum()
        va_est = np.sum(p * r2)
        err = abs(va_est - VA)
        if err < best_err:
            best_err = err
            best_v = float(vv)
    return best_v


def _annihilation(n_cut):
    a = np.zeros((n_cut, n_cut), dtype=np.complex128)
    for n in range(1, n_cut):
        a[n - 1, n] = np.sqrt(n)
    return a


def _coherent_ket(alpha, n_cut):
    n = np.arange(n_cut, dtype=float)
    denom = np.sqrt(np.array([math.factorial(int(k)) for k in n], dtype=float))
    coeff = np.power(alpha, n) / denom
    return np.exp(-0.5 * np.abs(alpha) ** 2) * coeff.astype(np.complex128)


def _cache_round(value, digits=10):
    return round(float(value), int(digits))


@lru_cache(maxsize=128)
def _qam_tau_terms_cached(VA_key, M, prob_model, v_key, n_cut):
    VA = float(VA_key)
    v = float(v_key)
    alpha, prob = _qam_constellation_probs(VA, M, prob_model=prob_model, v=v)
    kets = np.array([_coherent_ket(a, n_cut) for a in alpha])
    tau = np.zeros((n_cut, n_cut), dtype=np.complex128)
    for p, ket in zip(prob, kets):
        tau += p * np.outer(ket, np.conjugate(ket))

    evals, evecs = np.linalg.eigh(tau)
    evals = np.clip(evals, 0.0, None)
    sqrt_tau = (evecs * np.sqrt(evals)) @ np.conjugate(evecs.T)

    a = _annihilation(n_cut)
    adag = np.conjugate(a.T)
    tr_term = np.trace(sqrt_tau @ a @ sqrt_tau @ adag).real

    atau = a @ tau
    op_w = adag @ tau @ atau
    w = 0.0
    for p, ket in zip(prob, kets):
        t1 = np.vdot(ket, op_w @ ket)
        t2 = np.vdot(ket, atau @ ket)
        w += p * (t1.real - np.abs(t2) ** 2)
    return float(max(tr_term, 0.0)), float(max(w, 0.0))


def _qam_tau_terms(VA, M, prob_model="binomial", v=QAM_V_DISC_GAUSS, n_cut=N_FOCK):
    return _qam_tau_terms_cached(
        _cache_round(VA),
        int(M),
        prob_model,
        _cache_round(v),
        int(n_cut),
    )


def _Zstar_qam(T, eps_total, VA, M, prob_model="binomial", v=QAM_V_DISC_GAUSS, n_cut=N_FOCK):
    """Lower-bound correlation Z* in Eq. (20), using total excess noise ε."""
    tr_term, w = _qam_tau_terms(VA, M, prob_model=prob_model, v=v, n_cut=n_cut)
    Ts = max(float(T), 1e-300)
    eps_total = max(float(eps_total), 0.0)
    z_star = 2 * np.sqrt(Ts) * tr_term - np.sqrt(2 * Ts * eps_total) * w
    z_star = max(float(z_star), 0.0)
    _log_calc(
        "Zstar_qam",
        protocol="QAM",
        M=M,
        VA=VA,
        T=Ts,
        eps_total=eps_total,
        prob_model=prob_model,
        v=v,
        n_cut=n_cut,
        tr_term=tr_term,
        w=w,
        Z_star=z_star,
    )
    return z_star


def _IAB_qam_hom(VA, T, eps_total):
    return 0.5 * np.log2(1 + T * VA / (2 + T * eps_total))


def _IAB_qam_het(VA, T, eps_total):
    return np.log2(1 + T * VA / (2 + T * eps_total))


def _holevo_qam_het(VA, T, eps_ch, M, prob_model="binomial", v=QAM_V_DISC_GAUSS, eps_total=None):
    """Holevo bound for M-QAM heterodyne (Eq. 17-19)."""
    Ts = max(float(T), 1e-300)
    if eps_total is None:
        eps_total = _eps_total(Ts, eps_ch)
    Zs = _Zstar_qam(Ts, eps_total, VA, M, prob_model=prob_model, v=v)
    a11 = VA + 1
    a22 = 1 + Ts * VA + Ts * eps_total
    # FIX (Eq. 17-19): use symplectic invariants form for ν1,2.
    theta = a11**2 + a22**2 - 2 * Zs**2
    delta = (a11 * a22 - Zs**2) ** 2
    dsc = max(theta**2 - 4 * delta, 0)
    l1 = np.sqrt(max(0.5 * (theta + np.sqrt(dsc)), 1e-30))
    l2 = np.sqrt(max(0.5 * (theta - np.sqrt(dsc)), 1e-30))
    l3 = max(VA + 1 - Zs**2 / (2 + Ts * VA + Ts * eps_total), 1e-15)
    S_BE = _G((l1 - 1) / 2) + _G((l2 - 1) / 2) - _G((l3 - 1) / 2)
    _log_calc(
        "holevo_qam_het",
        protocol="QAM",
        M=M,
        VA=VA,
        T=Ts,
        eps_ch=eps_ch,
        eps_total=eps_total,
        prob_model=prob_model,
        v=v,
        Zs=Zs,
        a11=a11,
        a22=a22,
        theta=theta,
        delta=delta,
        l1=l1,
        l2=l2,
        l3=l3,
        S_BE=S_BE,
    )
    return S_BE


def skr_qam(VA, T, eps, M, beta, prob_model="binomial", v=QAM_V_DISC_GAUSS):
    """
    Asymptotic SKR for M-QAM DM-CVQKD heterodyne [bits/pulse] (Eq. 4, 16).
    Input `eps` is channel excess noise ε_ch; ε_total is formed internally.
    """
    Ts = max(float(T), 1e-300)
    eps_total = _eps_total(Ts, eps)
    iab = _IAB_qam_het(VA, Ts, eps_total)
    sbe = _holevo_qam_het(VA, Ts, eps, M, prob_model=prob_model, v=v, eps_total=eps_total)
    skr = beta * iab - sbe
    _log_calc(
        "skr_qam",
        protocol="QAM",
        M=M,
        VA=VA,
        T=Ts,
        eps_ch=eps,
        eps_total=eps_total,
        beta=beta,
        prob_model=prob_model,
        v=v,
        I_AB=iab,
        S_BE=sbe,
        SKR=skr,
    )
    return skr
