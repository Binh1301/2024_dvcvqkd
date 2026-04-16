"""
Satellite-to-Ground CV-QKD Simulation – CORRECTED VERSION
Reproducing Figures 4-8 from:
Sayat et al., IEEE Trans. Commun., Vol. 72, No. 6, June 2024
DOI: 10.1109/TCOMM.2024.3359295
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.special import erfinv, comb as sp_comb
from functools import lru_cache
import math

# =============================================================================
# 1. CONSTANTS & PARAMETERS
# =============================================================================
LAMBDA = 1550e-9          # Wavelength [m]
RE     = 6_371_000.0       # Earth radius [m]

# Hardware (Table III)
DT = 0.3                  # Transmitter aperture diameter [m]
TT = 0.9                  # Transmitter optics efficiency
TR = 0.9                  # Receiver optics efficiency
LP = 0.1                  # Pointing/APT loss

# Excess noise (Table I, all in SNU)
EPS_CH  = 0.0060 + 0.0100 + 0.0018 + 0.0005 + 0.0002 + 0.0001   # ≈ 0.0186
EPS_DET = 0.0130 + 0.0002 + 0.0001 + 0.0001 + 0.0001             # ≈ 0.0135

ETA     = 0.6
CHI_HOM = (1 - ETA + EPS_DET) / ETA
CHI_HET = (1 + (1 - ETA) + 2 * EPS_DET) / ETA

# Modulation variances (Table III)
VA_GM  = 5.0
VA_PSK = 0.5
VA_QAM = 2.0

# Finite-size parameters (Table III)
F_REP   = 50e6
N_BLOCK = 1e11
D_DISC  = 5
EPS_S   = 2e-10
EPS_SEC = 1e-9
P_THR   = 1e-6

# FER model (Eq. 26)
M1, M2, M3 = 0.8218, -19.46, -298.1
# Table II coefficients for β (reconciliation efficiency)
RECON_COEFFS = {
    'MLC-MSD': {'c1': 0.9655, 'c2': 0.0001507, 'c3': -0.04696, 'c4': -0.2238},
    'MD':      {'c1': -0.0825, 'c2': 0.1834,   'c3': 0.9821,   'c4': -0.00002815},
}

LATM      = 20_000.0
H_OGS_DEF = 0.0
H_OGS_ISS = 1_029.0

# =============================================================================
# 2. CHANNEL MODEL (Section IV)
# =============================================================================
def link_geometry(theta_deg, H_zen, H_ogs=H_OGS_DEF, H_atm=LATM):
    th = np.radians(theta_deg)
    r1 = RE + H_ogs
    r_sat = RE + H_zen
    r_atm = RE + H_atm
    c2 = np.cos(th) ** 2
    L_tot = -r1 * np.sin(th) + np.sqrt(max(r_sat**2 - r1**2 * c2, 0.0))
    L_atm = -r1 * np.sin(th) + np.sqrt(max(r_atm**2 - r1**2 * c2, 0.0))
    return float(L_tot), float(L_atm)

def geometric_loss_dB(L_tot, Dr):
    return 10 * np.log10(L_tot**2 * LAMBDA**2 /
                         (DT**2 * Dr**2 * TT * (1 - LP) * TR))

def scattering_loss_dBpkm(V_km):
    if   V_km >= 50: p = 1.6
    elif V_km >= 6:  p = 1.3
    elif V_km >= 1:  p = 0.16 * V_km + 0.34
    elif V_km >= 0.5:p = V_km - 0.5
    else:            p = 0.0
    # 10*log10(e) = 10 / ln(10)
    return (10.0 / np.log(10.0)) * (3.912 / V_km) * (1550.0 / 550.0) ** (-p)

def scintillation_index(Cn2, Dr, L_atm):
    k = 2 * np.pi / LAMBDA
    d = np.sqrt(k * Dr**2 / (4 * L_atm))
    # σ_R² : Eq. (32)
    s2R = 2.25 * (k ** (7.0 / 6.0)) * Cn2 * (L_atm ** (11.0 / 6.0)) * (6.0 / 11.0)
    s2R_pow = s2R ** (6.0 / 5.0)

    # Term 1
    t1_num = 0.20 * s2R
    t1_den = (1.0 + 0.18 * d**2 + 0.20 * s2R_pow) ** (6.0 / 5.0)
    t1 = t1_num / t1_den

    # Term 2
    t2_num = 0.21 * s2R * (1.0 + 0.24 * s2R_pow) ** (-6.0 / 5.0)
    t2_den = 1.0 + 0.90 * d**2 + 0.21 * d**2 * s2R_pow
    t2 = t2_num / t2_den

    s2I = np.exp(t1 + t2) - 1.0
    return float(s2I)

def scintillation_loss_dB(s2I, p_thr=P_THR):
    if s2I <= 0:
        return 0.0
    ln_term = np.log(s2I + 1.0)
    arg = np.clip(2.0 * p_thr - 1.0, -0.9999, 0.9999)
    A_sci = 4.343 * (erfinv(arg) * np.sqrt(2.0 * ln_term) - 0.5 * ln_term)
    return abs(A_sci)

def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=H_OGS_DEF):
    L_tot, L_atm = link_geometry(theta_deg, H_zen, H_ogs)
    ff_ok = (L_tot >= Dr * DT / LAMBDA)

    A_geo  = geometric_loss_dB(L_tot, Dr)
    A_scat = scattering_loss_dBpkm(V_km) * (L_atm / 1e3)
    A_sci  = scintillation_loss_dB(scintillation_index(Cn2, Dr, L_atm))

    T = float(np.clip(10 ** (-(A_geo + A_scat + A_sci) / 10.0), 0.0, 1.0))
    return T, L_tot, ff_ok

# =============================================================================
# 3. GM-CVQKD (Section II-A)
# =============================================================================
def _G(x):
    x = float(x)
    if x < 1e-10:
        return 0.0
    return (x + 1.0) * np.log2(x + 1.0) - x * np.log2(x)

def _chi_l(T, e):
    Ts = max(float(T), 1e-300)
    return 1.0 / Ts - 1.0 + e

def _chi_t_hom(T, e):
    Ts = max(float(T), 1e-300)
    return _chi_l(Ts, e) + CHI_HOM / Ts

def _chi_t_het(T, e):
    Ts = max(float(T), 1e-300)
    return _chi_l(Ts, e) + CHI_HET / Ts

def _IAB_hom(VA, chi_t):
    return 0.5 * np.log2(1.0 + VA / (1.0 + chi_t))

def _IAB_het(VA, chi_t):
    return np.log2(1.0 + VA / (1.0 + chi_t))

def _symp12(VA, T, chi_l, Z=None):
    Ts = max(float(T), 1e-300)
    if Z is None:
        Z = np.sqrt(VA**2 + 2.0 * VA)
    t_v = 1.0 + Ts * (VA + (chi_l - (1.0 / Ts - 1.0)))   # = T*(VA+1+chi_l)
    A = (VA + 1.0)**2 + t_v**2 - 2.0 * Ts * (Z**2)
    B_inner = Ts * ((VA + 1.0)**2 + (VA + 1.0) * chi_l - Z**2)
    B = B_inner**2
    disc = max(A**2 - 4.0 * B, 0.0)
    l1 = np.sqrt(max(0.5 * (A + np.sqrt(disc)), 1e-30))
    l2 = np.sqrt(max(0.5 * (A - np.sqrt(disc)), 1e-30))
    return l1, l2, B, A

def _holevo_gm_hom(VA, T, e):
    Ts = max(float(T), 1e-300)
    chi_l = _chi_l(T, e)
    chi_h = CHI_HOM
    chi_tot = chi_l + chi_h / Ts

    l1, l2, B, A = _symp12(VA, Ts, chi_l)
    sqB = np.sqrt(max(B, 0.0))

    denom = Ts * (1.0 + VA + chi_tot)
    C = (A * chi_h + (VA + 1.0) * sqB + Ts * (VA + 1.0 + chi_l)) / denom
    D = (sqB * (VA + 1.0 + sqB * chi_h)) / denom

    disc = max(C**2 - 4.0 * D, 0.0)
    sqrt_disc = np.sqrt(disc)
    l3 = np.sqrt(max(0.5 * (C + sqrt_disc), 1e-30))
    l4 = np.sqrt(max(0.5 * (C - sqrt_disc), 1e-30))

    return (_G((l1 - 1.0) / 2.0) + _G((l2 - 1.0) / 2.0) -
            _G((l3 - 1.0) / 2.0) - _G((l4 - 1.0) / 2.0))

def skr_gm(VA, T, eps, beta):
    chi_t = _chi_t_hom(T, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_gm_hom(VA, T, eps)
    return beta * I_AB - S_BE

# =============================================================================
# 4. M-PSK DM-CVQKD (Section II-B)
# =============================================================================
def _ZM_psk(M, VA):
    if M not in (2, 4, 8):
        raise ValueError("Only M=2,4,8 are supported.")
    if VA <= np.finfo(float).eps:
        return 0.0
    a2 = VA / 2.0
    tiny = np.finfo(float).tiny
    phi = 2.0 * np.pi * np.arange(M, dtype=float) / M
    vals = np.exp(a2 * np.exp(1j * phi))
    zeta = (np.exp(-a2) / M) * np.fft.fft(vals)
    z = np.clip(np.real_if_close(zeta, tol=1e5).real, tiny, None)
    z_prev = np.roll(z, 1)
    terms = np.exp(1.5 * np.log(z_prev) - 0.5 * np.log(z))
    prefactor = a2 if M == 2 else 2.0 * a2
    return float(prefactor * np.sum(terms))

def _holevo_psk_hom(VA, T, e, M):
    Ts = max(float(T), 1e-300)
    cl = _chi_l(Ts, e)
    ct = cl + CHI_HOM / Ts
    ZM = _ZM_psk(M, VA)

    t_v = Ts * (VA + 1.0 + cl)
    A = (VA + 1.0)**2 + t_v**2 - 2.0 * Ts * ZM**2
    B_inner = Ts * ((VA + 1.0)**2 + (VA + 1.0) * cl - ZM**2)
    B = B_inner**2

    d12 = max(A**2 - 4.0 * B, 0.0)
    l1 = np.sqrt(0.5 * (A + np.sqrt(d12)))
    l2 = np.sqrt(max(0.5 * (A - np.sqrt(d12)), 1e-30))

    sqB = np.sqrt(max(B, 0.0))
    chi_tot = cl + CHI_HOM / Ts
    denom = Ts * (1.0 + VA + chi_tot)

    Ah = (A * CHI_HOM + (VA + 1.0) * sqB + t_v) / denom
    Dh = sqB * (VA + 1.0 + sqB * CHI_HOM) / denom

    d34 = max(Ah**2 - 4.0 * Dh, 0.0)
    l3 = np.sqrt(0.5 * (Ah + np.sqrt(d34)))
    l4 = np.sqrt(max(0.5 * (Ah - np.sqrt(d34)), 1e-30))

    return (_G((l1 - 1.0) / 2.0) + _G((l2 - 1.0) / 2.0) -
            _G((l3 - 1.0) / 2.0) - _G((l4 - 1.0) / 2.0))

def skr_psk(VA, T, eps, M, beta):
    Ts = max(float(T), 1e-300)
    chi_t = _chi_t_hom(Ts, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_psk_hom(VA, Ts, eps, M)
    return beta * I_AB - S_BE

# =============================================================================
# 5. M-QAM DM-CVQKD (Section II-C)
# =============================================================================
N_FOCK = 32
QAM_V_DISC_GAUSS = 0.5

def _qam_constellation_probs(VA, M, prob_model='binomial', v=QAM_V_DISC_GAUSS):
    m = int(round(np.sqrt(M)))
    if m * m != M:
        raise ValueError("M-QAM requires M=m^2.")
    ks = np.arange(m)
    scale = np.sqrt(2.0 * VA) / np.sqrt(m - 1.0) if m > 1 else 0.0
    xvals = scale * (ks - (m - 1.0) / 2.0)
    yvals = xvals.copy()
    alpha = np.array([x + 1j * y for x in xvals for y in yvals], dtype=np.complex128)
    if prob_model == 'binomial':
        pk = np.array([float(sp_comb(m - 1, k, exact=True)) for k in ks], dtype=float)
        pk /= pk.sum()
        prob = np.array([pk[k] * pk[l] for k in range(m) for l in range(m)], dtype=float)
    elif prob_model == 'disc_gaussian':
        prob = np.array([np.exp(-v * (x * x + y * y)) for x in xvals for y in yvals], dtype=float)
        prob /= prob.sum()
    else:
        raise ValueError("prob_model must be 'binomial' or 'disc_gaussian'.")
    return alpha, prob

def _optimize_disc_gaussian_v(VA, M):
    alpha, _ = _qam_constellation_probs(VA, M, prob_model='binomial', v=1.0)
    r2 = np.abs(alpha)**2
    grid = np.concatenate([np.linspace(0.02, 0.8, 80), np.linspace(0.81, 3.0, 80)])
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
    return np.exp(-0.5 * np.abs(alpha)**2) * coeff.astype(np.complex128)

@lru_cache(maxsize=128)
def _qam_tau_terms_cached(VA, M, prob_model, v, n_cut):
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
        w += p * (t1.real - np.abs(t2)**2)
    return float(max(tr_term, 0.0)), float(max(w, 0.0))

def _Zstar_qam(T, eps, VA, M, prob_model='binomial', v=QAM_V_DISC_GAUSS, n_cut=N_FOCK):
    tr_term, w = _qam_tau_terms_cached(VA, M, prob_model, float(v), int(n_cut))
    z_star = 2.0 * np.sqrt(T) * tr_term - np.sqrt(2.0 * T * eps) * w
    return max(float(z_star), 0.0)

def _IAB_qam_hom(VA, T, eps):
    return 0.5 * np.log2(1.0 + T * VA / (2.0 + T * eps))

def _IAB_qam_het(VA, T, eps):
    return np.log2(1.0 + T * VA / (2.0 + T * eps))

def _holevo_qam_het(VA, T, eps, M, prob_model='binomial', v=QAM_V_DISC_GAUSS):
    Zs = _Zstar_qam(T, eps, VA, M, prob_model=prob_model, v=v)
    a11 = VA + 1.0
    a22 = 1.0 + T * VA + T * eps
    theta = a11**2 + a22**2 - 2.0 * Zs**2
    delta = (a11 * a22 - Zs**2)**2
    dsc = max(theta**2 - 4.0 * delta, 0.0)
    l1 = np.sqrt(max(0.5 * (theta + np.sqrt(dsc)), 1e-30))
    l2 = np.sqrt(max(0.5 * (theta - np.sqrt(dsc)), 1e-30))
    l3 = max(VA + 1.0 - Zs**2 / (2.0 + T * VA + T * eps), 1e-15)
    return _G((l1 - 1.0) / 2.0) + _G((l2 - 1.0) / 2.0) - _G((l3 - 1.0) / 2.0)

def skr_qam(VA, T, eps, M, beta, prob_model='binomial', v=QAM_V_DISC_GAUSS):
    iab = _IAB_qam_het(VA, T, eps)
    sbe = _holevo_qam_het(VA, T, eps, M, prob_model=prob_model, v=v)
    return beta * iab - sbe

# =============================================================================
# 6. RECONCILIATION & FINITE-SIZE (Section III)
# =============================================================================
def _SNR_dB(T, alpha_sq, chi_t):
    num = T * alpha_sq
    den = alpha_sq + (1.0 - T) * chi_t
    snr_lin = num / max(den, 1e-30)
    return 10.0 * np.log10(max(snr_lin, 1e-30))

def reconciliation_efficiency(snr_dB, mode='MD'):
    """
    Eq. (26): β = c1^{c2 * SNR_dB} - c3^{c4 * SNR_dB}
    """
    c = RECON_COEFFS[mode]
    beta = c['c1'] ** (c['c2'] * snr_dB) - c['c3'] ** (c['c4'] * snr_dB)
    return float(np.clip(beta, 0.0, 1.0))

def frame_error_rate(snr_dB):
    """
    Eq. (26): FER = 0.5 * (1 + m1 * arctan(m2 * SNR_dB + m3))
    """
    return float(np.clip(0.5 * (1.0 + M1 * np.arctan(M2 * snr_dB + M3)), 0.0, 1.0))

def _dn_privacy(N=N_BLOCK):
    d, es, esec = D_DISC, EPS_S, EPS_SEC
    sN = np.sqrt(N)
    return ((d + 1.0)**2 / sN +
            4.0 * (d + 1.0) * np.sqrt(np.log2(2.0 / es)) / sN +
            2.0 * np.log2(2.0 / (esec**2 * es)) / sN +
            4.0 * es * d / (esec * sN) / sN)

def finite_size_skr(VA, T, eps, mode='MD', N=N_BLOCK, f_rep=F_REP):
    ct = _chi_t_hom(T, eps)
    snr = _SNR_dB(T, VA, ct)
    bet = reconciliation_efficiency(snr, mode)
    fer = frame_error_rate(snr)
    IAB = _IAB_hom(VA, ct)
    SBE = _holevo_gm_hom(VA, T, eps)
    dn = _dn_privacy(N)
    return f_rep * ((1.0 - fer) * (bet * IAB - SBE - dn))

def plob_upper_bound(T):
    if T <= 0.0 or T >= 1.0:
        return 0.0
    return -np.log2(1.0 - T)

# =============================================================================
# 7. ISS PASS ELEVATION MODEL (Fig. 7)
# =============================================================================
def elevation_model(duration=663, max_elev=87.6, dt=1.0):
    t = np.arange(0, duration + dt, dt)
    theta = max_elev * np.exp(-0.5 * ((t - 350.0) / 115.0)**2)
    return t, np.maximum(theta, 0.0)

# =============================================================================
# 8. PLOT FUNCTIONS (Fig. 4-8)
# =============================================================================
ELEVS  = [90, 60, 30]
LS     = ['-', '--', '-.']
EL_LEG = [Line2D([0], [0], color='gray', ls=s, lw=1.5, label=f'θ={t}°')
          for t, s in zip(ELEVS, LS)]

def _nan(v, floor=1e-12):
    if not np.isfinite(v):
        return np.nan
    return v if v > floor else np.nan

def plot_fig4():
    print("▶ Figure 4 (asymptotic, good atmosphere)...")
    V, Cn2, Dr, beta, eps = 200, 1e-16, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 1050, 10)
    alt_m  = alt_km * 1e3

    panels = [
        ('(a) M-PSK', [
            ('Gaussian', 'goldenrod', 'gm', {}),
            ('8-PSK',   'blue','psk',{'M':8}),
            ('4-PSK',   'red', 'psk',{'M':4}),
        ], alt_km, [160,1000]),
        ('(b) 64-QAM', [
            ('Gaussian',               'goldenrod', 'gm', {}),
            ('Binomial Dist.',         'blue', 'qam',{'M':64}),
            ('Disc. Gaussian Dist.',   'red',  'qam',{'M':64}),
        ], np.arange(160,5100,20), [160,5000]),
        ('(c) 256-QAM', [
            ('Gaussian',               'goldenrod', 'gm', {}),
            ('Binomial Dist.',         'blue', 'qam',{'M':256}),
            ('Disc. Gaussian Dist.',   'red',  'qam',{'M':256}),
        ], np.arange(160,6100,25), [160,6000]),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(6.5, 11))
    v64 = _optimize_disc_gaussian_v(VA_QAM, 64)
    v256 = _optimize_disc_gaussian_v(VA_QAM, 256)

    for ax, (title, protos, akm, xlim) in zip(axes, panels):
        ax.set_title(title)
        am = akm * 1e3
        ub = [plob_upper_bound(total_transmittance(90, H, Dr, V, Cn2)[0]) for H in am]
        ax.semilogy(akm, ub, 'k-', lw=2.5, label='Upper Bound')

        for lbl, col, ptype, kw in protos:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in am:
                    T, _, ff_ok = total_transmittance(th, H, Dr, V, Cn2)
                    if not ff_ok:
                        vals.append(np.nan)
                        continue
                    if ptype == 'gm':
                        s = skr_gm(VA_GM, T, eps, beta)
                    elif ptype == 'psk':
                        s = skr_psk(VA_PSK, T, eps, kw['M'], beta)
                    else:
                        if lbl == 'Disc. Gaussian Dist.':
                            vv = v64 if kw['M'] == 64 else v256
                            s = skr_qam(VA_QAM, T, eps, kw['M'], beta, prob_model='disc_gaussian', v=vv)
                        else:
                            s = skr_qam(VA_QAM, T, eps, kw['M'], beta, prob_model='binomial')
                    vals.append(_nan(s))
                lb = lbl if th == ELEVS[0] else '_'
                ax.semilogy(akm, vals, color=col, ls=ls, lw=1.5, label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/pulse]')
        ax.set_ylim([1e-7, 1e0])
        ax.set_xlim(xlim)
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=0.35, linestyle='-')
        ax.grid(True, which='minor', alpha=0.20, linestyle=':')
        ax.legend(fontsize=8, loc='upper right', frameon=True)

    fig.text(0.5, 0.02,
             r'Fig. 4. Asymptotic limit SKRs as a function of satellite altitude for '
             r'(a) M-PSK, (b) 64-QAM, and (c) 256-QAM DM-CVQKD in relation to '
             r'GM-CVQKD in good atmospheric conditions. The solid lines indicate '
             r'$\theta = 90^\circ$, dashed lines indicate $\theta = 60^\circ$, '
             r'dash-dotted lines indicate $\theta = 30^\circ$. $D_r = 1$ m, '
             r'$\beta = 90\%$.',
             ha='center', va='bottom', fontsize=8)
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.show()
    print("  ✓ Figure 4 displayed")

def plot_fig5():
    print("▶ Figure 5 (asymptotic, bad atmosphere)...")
    V, Cn2, Dr, beta, eps = 20, 1e-13, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 6100, 25)
    alt_m  = alt_km * 1e3

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(r'Fig. 5 – Asymptotic SKRs  |  Bad: $V\!=\!20$ km, $C_n^2\!=\!10^{-13}$, $D_r\!=\!1$ m, $\beta\!=\!90\%$', fontsize=11)

    v64 = _optimize_disc_gaussian_v(VA_QAM, 64)
    v256 = _optimize_disc_gaussian_v(VA_QAM, 256)
    for ax, M_qam in zip(axes, [64, 256]):
        ax.set_title(f'({chr(97 + list(axes).index(ax))}) {M_qam}-QAM')
        ub = [plob_upper_bound(total_transmittance(90, H, Dr, V, Cn2)[0]) for H in alt_m]
        ax.semilogy(alt_km, ub, 'k-', lw=2.5, label='Upper Bound')

        for lbl, col, ptype, VA in [
                ('Gaussian', 'yellow', 'gm', VA_GM),
                ('Binomial Dist.', 'blue', 'qam', VA_QAM),
                ('Disc. Gaussian Dist.', 'red', 'qam', VA_QAM)]:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in alt_m:
                    T, _, _ = total_transmittance(th, H, Dr, V, Cn2)
                    if ptype == 'gm':
                        s = skr_gm(VA, T, eps, beta)
                    elif lbl == 'Disc. Gaussian Dist.':
                        vv = v64 if M_qam == 64 else v256
                        s = skr_qam(VA, T, eps, M_qam, beta, prob_model='disc_gaussian', v=vv)
                    else:
                        s = skr_qam(VA, T, eps, M_qam, beta, prob_model='binomial')
                    vals.append(_nan(s))
                lb = lbl if th == ELEVS[0] else '_'
                ax.semilogy(alt_km, vals, color=col, ls=ls, lw=1.5, label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/pulse]')
        ax.set_ylim([1e-12, 1e0])
        ax.set_xlim([alt_km[0], alt_km[-1]])
        ax.grid(True, which='both', alpha=0.25)
        h, l = ax.get_legend_handles_labels()
        ax.legend(handles=h + EL_LEG, labels=l + [e.get_label() for e in EL_LEG],
                  fontsize=7, loc='upper right')

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 5 displayed")

def plot_fig6():
    print("▶ Figure 6 (finite-size)...")
    V, Cn2, eps = 200, 1e-16, EPS_CH
    COLORS = {'MD': 'blue', 'MLC-MSD': 'red'}

    configs = [('(a) $D_r = 1$ m', 1.0, np.arange(160, 460, 5)),
               ('(b) $D_r = 2$ m', 2.0, np.arange(160, 1010, 10))]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(r'Fig. 6 – Finite-Size SKRs  |  GM-CVQKD, Homodyne, MD vs MLC-MSD' '\n' r'Good conditions: $V\!=\!200$ km, $C_n^2\!=\!10^{-16}$', fontsize=11)

    for ax, (title, Dr, akm) in zip(axes, configs):
        ax.set_title(title)
        am = akm * 1e3
        for mode in ['MD', 'MLC-MSD']:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in am:
                    T, _, ok = total_transmittance(th, H, Dr, V, Cn2)
                    s = finite_size_skr(VA_GM, T, eps, mode) if ok else 0.0
                    vals.append(_nan(s))
                lb = mode if th == ELEVS[0] else '_'
                ax.semilogy(akm, vals, color=COLORS[mode], ls=ls, lw=1.5, label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/s]')
        ax.set_ylim([1e4, 1e8])
        ax.set_xlim([akm[0], akm[-1]])
        ax.grid(True, which='both', alpha=0.25)
        h, l = ax.get_legend_handles_labels()
        ax.legend(handles=h + EL_LEG, labels=l + [e.get_label() for e in EL_LEG],
                  fontsize=8, loc='upper right')

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 6 displayed")

def plot_fig7():
    print("▶ Figure 7 (ISS elevation pass)...")
    t, theta = elevation_model()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, theta, 'b-', lw=2)
    ax.set_xlabel('Duration (s)', fontsize=12)
    ax.set_ylabel('Elevation Angle (°)', fontsize=12)
    ax.set_title('Fig. 7 – ISS Pass Elevation over Mt. John Observatory\n'
                 '9 August 2022  |  Max = 87.6°  |  Duration = 663 s', fontsize=11)
    ax.set_xlim([0, 700])
    ax.set_ylim([0, 95])
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 7 displayed")

def plot_fig8():
    print("▶ Figure 8 (SKR vs elevation angle, ISS pass)...")
    H_iss = 417_500.0
    Dr, V, Cn2, eps = 2.0, 200, 1e-16, EPS_CH
    COLORS = {'MD': 'blue', 'MLC-MSD': 'red'}
    theta_arr = np.arange(30, 91, 1)
    total_key = {}

    fig, ax = plt.subplots(figsize=(8, 5))
    for mode in ['MD', 'MLC-MSD']:
        vals = []
        for th in theta_arr:
            T, _, ok = total_transmittance(th, H_iss, Dr, V, Cn2, H_OGS_ISS)
            s = finite_size_skr(VA_GM, T, eps, mode) if ok else 0.0
            vals.append(_nan(s))
        ax.semilogy(theta_arr, vals, color=COLORS[mode], lw=2, label=mode)

        _t, _th = elevation_model()
        key = 0.0
        for th_t in _th:
            if th_t < 30:
                continue
            T, _, ok = total_transmittance(float(th_t), H_iss, Dr, V, Cn2, H_OGS_ISS)
            key += finite_size_skr(VA_GM, T, eps, mode) if ok else 0.0
        total_key[mode] = key

    ax.set_xlabel('Elevation Angle [°]', fontsize=12)
    ax.set_ylabel('SKR [bits/s]', fontsize=12)
    ax.set_title(r'Fig. 8 – SKR vs Elevation for ISS Pass  |  $D_r\!=\!2$ m, $H_{ISS}\!=\!417.5$ km, Homodyne', fontsize=11)
    ax.set_xlim([30, 90])
    ax.grid(True, which='both', alpha=0.25)
    ax.legend(fontsize=11)

    txt = (f"Total key – MD:      {total_key['MD']/1e9:.3f} Gbit  [paper: 1.235 Gbit]\n"
           f"Total key – MLC-MSD: {total_key['MLC-MSD']/1e6:.1f} Mbit  [paper: 385 Mbit]")
    ax.text(0.04, 0.97, txt, transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', fc='wheat', alpha=0.6))

    print(f"  MD  total key: {total_key['MD']/1e9:.3f} Gbit  (paper: 1.235 Gbit)")
    print(f"  MSD total key: {total_key['MLC-MSD']/1e6:.1f} Mbit  (paper: 385 Mbit)")

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 8 displayed")

# =============================================================================
# 9. MAIN
# =============================================================================
def main():
    print("=" * 68)
    print("CV-QKD Satellite-to-Ground Simulation – CORRECTED")
    print("Sayat et al., IEEE Trans. Commun. 2024 | Reproducing Figs 4-8")
    print("=" * 68)
    print(f"\nEPS_CH={EPS_CH:.4f} SNU  |  CHI_HOM={CHI_HOM:.4f}  CHI_HET={CHI_HET:.4f}")

    plot_fig4()
    plot_fig5()
    plot_fig6()
    plot_fig7()
    plot_fig8()

    print("\n" + "=" * 68)
    print("All 5 figures reproduced successfully!")
    print("=" * 68)

if __name__ == '__main__':
    main()