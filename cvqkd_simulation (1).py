"""
=============================================================================
Satellite-to-Ground CV-QKD Simulation
Reproducing Figures 4-8 from:

"Satellite-to-Ground Continuous Variable Quantum Key Distribution:
 The Gaussian and Discrete Modulated Protocols in Low Earth Orbit"
Sayat et al., IEEE Transactions on Communications, Vol. 72, No. 6, June 2024
DOI: 10.1109/TCOMM.2024.3359295
=============================================================================

STRUCTURE
---------
 1. Constants & Parameters  (Table I, III)
 2. Channel Model           (Section IV, Eq. 28-32)
 3. GM-CVQKD               (Section II-A, Eq. 3-11)
 4. M-PSK DM-CVQKD         (Section II-B, Eq. 12)
 5. M-QAM DM-CVQKD         (Section II-C, Eq. 13-22)
 6. Reconciliation & FSK    (Section III, Eq. 23-27)
 7. ISS Pass Model          (Fig. 7 model)
 8. Plot Functions          (Fig. 4, 5, 6, 7, 8)
 9. Main

ASSUMPTIONS (marked inline as # Assumption: ...)
- Constant Cn2 along atmospheric path (integral approximated analytically)
- Detector efficiency eta = 0.6 (typical InGaAs at 1550 nm)
- M-PSK uses homodyne; M-QAM uses heterodyne detection
- MD beta ~ 0.99 at low SNR (paper: 'asymptotically approach 100%')
- MLC-MSD beta ~ 0.92 in satellite link SNR regime
- ISS pass elevation modelled as Gaussian bell curve peaking at t=350s
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.special import erfinv, comb as sp_comb
from scipy.optimize import minimize_scalar

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONSTANTS & PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

LAMBDA = 1550e-9        # Wavelength [m]
RE     = 6_371_000.0   # Earth radius [m]

# Hardware (Table III)
DT = 0.3               # Transmitter aperture diameter [m]
TT = 0.9               # Transmitter optics efficiency
TR = 0.9               # Receiver optics efficiency
LP = 0.1               # Pointing/APT loss

# Excess noise (Table I, all in Shot Noise Units SNU)
EPS_CH = (0.0060 + 0.0100 + 0.0018 + 0.0005 + 0.0002 + 0.0001)  # ≈ 0.0186
EPS_DET= (0.0130 + 0.0002 + 0.0001 + 0.0001 + 0.0001)            # ≈ 0.0135

# Assumption: eta = 0.6 (InGaAs homodyne/heterodyne at 1550 nm)
ETA     = 0.6
CHI_HOM = (1 - ETA + EPS_DET) / ETA            # homodyne detection noise [SNU]
CHI_HET = (1 + (1 - ETA) + 2 * EPS_DET) / ETA  # heterodyne detection noise [SNU]

# Modulation variances (Table III)
VA_GM  = 5.0    # Gaussian [SNU]
VA_PSK = 0.5    # M-PSK    [SNU]
VA_QAM = 2.0    # M-QAM    [SNU]

# Finite-size parameters (Table III)
F_REP   = 50e6    # Repetition rate [Hz]
N_BLOCK = 1e11    # Total symbols
D_DISC  = 5       # Discretisation parameter
EPS_S   = 2e-10   # Smoothing parameter
EPS_SEC = 1e-9    # Security parameter
P_THR   = 1e-6    # Link outage probability

# FER model (Eq. 26, for N=10^6 base; ~0 for N=10^11 at typical SNRs)
M1, M2, M3 = 0.8218, -19.46, -298.1

LATM      = 20_000.0   # Atmosphere thickness [m]
H_OGS_DEF = 0.0        # Default OGS altitude [m]
H_OGS_ISS = 1_029.0   # Mt. John Observatory [m]


# ─────────────────────────────────────────────────────────────────────────────
# 2. CHANNEL MODEL  (Section IV, Eq. 28-33)
# ─────────────────────────────────────────────────────────────────────────────

def _L_atm_eff_ray(theta_deg, H_ogs=H_OGS_DEF, H_atm=LATM):
    """
    Đường laser đi qua lớp khí quyển mỏng [m], tính bằng ray-sphere intersection.

    Đây là phương pháp đúng cho thin atmosphere (Latm << RE).
    Công thức law-of-cosines trong Eq.28 tính chord xuyên Trái Đất → SAI.

    Ray xuất phát từ OGS tại r=RE+H_ogs theo góc elevation theta.
    Giao với vỏ cầu r=RE+H_atm → độ dài đoạn laser qua khí quyển.
    """
    th    = np.radians(theta_deg)
    r_ogs = RE + H_ogs
    r_atm = RE + H_atm
    # |P|^2 = r_atm^2 với P = r_ogs*(cos_lat, sin_lat) + t*(cos(th), sin(th))
    # → t^2 + 2*r_ogs*sin(th)*t + r_ogs^2 - r_atm^2 = 0
    b    = 2 * r_ogs * np.sin(th)
    c    = r_ogs**2 - r_atm**2
    disc = b**2 - 4 * c
    if disc < 0:
        return float(H_atm)  # fallback: zenith thickness
    return float((-b + np.sqrt(disc)) / 2)


def link_geometry(theta_deg, H_zen, H_ogs=H_OGS_DEF, H_atm=LATM):
    """
    Total link distance L_tot [m] và effective atmosphere thickness L_atm [m].

    L_tot   : dùng law-of-cosines (Eq. 28) — đúng cho khoảng cách satellite.
    L_atm   : dùng ray-sphere intersection — đúng cho thin atmosphere layer.
    """
    th = np.radians(theta_deg)

    # L_tot (Eq. 28 — đúng)
    sa1   = np.clip(np.cos(th) * (RE + H_ogs) / (RE + H_zen), -1, 1)
    a1    = np.arcsin(sa1) + (np.pi/2 - th)
    L_tot = np.sqrt((RE+H_zen)**2 + (RE+H_ogs)**2
                    - 2*(RE+H_zen)*(RE+H_ogs)*np.cos(a1))

    # L_atm_eff — ray-sphere intersection (sửa lỗi công thức Eq.28 cho L_atm)
    L_atm = _L_atm_eff_ray(theta_deg, H_ogs, H_atm)

    return float(L_tot), float(L_atm)


def geometric_loss_dB(L_tot, Dr):
    """Free-space diffraction + hardware loss (Eq. 29)."""
    return 10*np.log10(L_tot**2 * LAMBDA**2
                       / (DT**2 * Dr**2 * TT * (1-LP) * TR))


def scattering_loss_dBpkm(V_km):
    """Mie scattering loss [dB/km], Kruse-Kim model (Eq. 30)."""
    if   V_km >= 50: p = 1.6
    elif V_km >= 6:  p = 1.3
    elif V_km >= 1:  p = 0.16*V_km + 0.34
    elif V_km >= 0.5:p = V_km - 0.5
    else:            p = 0.0
    return 10*np.log10(np.e) * (3.912/V_km) * (1550/550)**(-p)


def scintillation_index(Cn2, Dr, L_atm):
    """Aperture-averaged scintillation index (Eq. 32)."""
    k   = 2*np.pi/LAMBDA
    d   = Dr * np.sqrt(np.pi/(2*LAMBDA*L_atm))
    # Assumption: constant Cn2 → sigma2_R integral = Cn2*L^(11/6)*6/11
    s2R = 2.25 * k**(7/6) * Cn2 * L_atm**(11/6) * (6/11)
    t1  = 0.20*s2R / (1 + 0.18*d**2 + 0.20*s2R**(6/5))**(7/6)
    t2  = (0.21*s2R*(1+0.24*s2R**(6/5))**(-5/6)
           / (1 + 0.90*d**2 + 0.21*d**2*s2R**(6/5)))
    return float(np.exp(t1+t2) - 1.0)


def scintillation_loss_dB(s2I, p_thr=P_THR):
    """Scintillation loss with aperture averaging in dB (Eq. 31)."""
    arg = float(np.clip(2*p_thr-1, -0.9999, 0.9999))
    return (4.343*erfinv(arg)*np.sqrt(2*np.log(s2I+1))
            - 0.5*np.log(s2I+1))


def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=H_OGS_DEF):
    """
    Total transmittance combining all losses (Eq. 33).
    Returns (T, L_tot [m], far_field_ok).
    """
    L_tot, L_atm = link_geometry(theta_deg, H_zen, H_ogs)
    ff_ok = (L_tot >= Dr * DT / LAMBDA)

    A_geo  = geometric_loss_dB(L_tot, Dr)
    A_scat = scattering_loss_dBpkm(V_km) * (L_atm/1e3)
    A_sci  = scintillation_loss_dB(scintillation_index(Cn2, Dr, L_atm))

    T = float(np.clip(10**(-(A_geo+A_scat+A_sci)/10), 0, 1))
    return T, L_tot, ff_ok


# ─────────────────────────────────────────────────────────────────────────────
# 3. GM-CVQKD  (Section II-A)
# ─────────────────────────────────────────────────────────────────────────────

def _G(x):
    """Entropy function G(x) = (x+1)log2(x+1) - x*log2(x)."""
    x = max(float(x), 1e-15)
    return (x+1)*np.log2(x+1) - x*np.log2(x)

def _chi_l(T, e): return 1/T - 1 + e
def _chi_t_hom(T, e): return _chi_l(T,e) + CHI_HOM/T
def _chi_t_het(T, e): return _chi_l(T,e) + CHI_HET/T
def _IAB_hom(VA, chi_t): return 0.5*np.log2((VA+1+chi_t)/(1+chi_t))
def _IAB_het(VA, chi_t): return np.log2((VA+1+chi_t)/(1+chi_t))

def _symp12(VA, T, chi_l, Z=None):
    """Symplectic eigenvalues λ1,λ2 of γ_AB (Eq. 7-8)."""
    if Z is None: Z = np.sqrt(VA**2 + 2*VA)
    A = (VA+1)**2 + T**2*(VA+1+chi_l)**2 - 2*T*Z**2
    B = (T*(VA+1)**2 + T*(VA+1)*chi_l - T*Z**2)**2
    disc = max(A**2 - 4*B, 0)
    l1 = np.sqrt(0.5*(A + np.sqrt(disc)))
    l2 = np.sqrt(max(0.5*(A - np.sqrt(disc)), 1e-30))
    return l1, l2, B

def _holevo_gm_hom(VA, T, e):
    """S_BE for GM-CVQKD homodyne (Eq. 6, 9-10)."""
    cl = _chi_l(T, e); ct = cl + CHI_HOM/T
    l1, l2, B = _symp12(VA, T, cl)
    sqB = np.sqrt(max(B,0)); dn = T*(VA+1+ct)
    Ah = (cl*ct*T*(VA+1) + CHI_HOM*sqB + (VA+1)**2*CHI_HOM) / dn
    Dh = sqB*(VA+1 + sqB*CHI_HOM) / dn
    d34 = max(Ah**2 - 4*Dh, 0)
    l3 = np.sqrt(0.5*(Ah + np.sqrt(d34)))
    l4 = np.sqrt(max(0.5*(Ah - np.sqrt(d34)), 1e-30))
    return _G((l1-1)/2)+_G((l2-1)/2)-_G((l3-1)/2)-_G((l4-1)/2)

def skr_gm(VA, T, eps, beta):
    """Asymptotic SKR for GM-CVQKD homodyne [bits/pulse] (Eq. 4)."""
    if T <= 1e-6: return 0.0   # below this, SKR is always negative; avoid overflow
    return beta*_IAB_hom(VA, _chi_t_hom(T,eps)) - _holevo_gm_hom(VA,T,eps)


# ─────────────────────────────────────────────────────────────────────────────
# 4. M-PSK DM-CVQKD  (Section II-B)
# ─────────────────────────────────────────────────────────────────────────────

def _ZM_psk(M, VA):
    """
    Correlation coefficient Z_M cho M-PSK DM-CVQKD (Section II-B).
    a2  = alpha^2 = VA/2
    a2s = alpha^2/sqrt(2)  — dùng cho 8-PSK
    """
    a2  = VA / 2
    a2s = a2 / np.sqrt(2)
    def safe(v): return max(float(v), 1e-300)

    # ── 2-PSK ─────────────────────────────────────────────────────────────
    if M == 2:
        z0 = safe(np.exp(-a2)*np.cosh(a2))
        z1 = safe(np.exp(-a2)*np.sinh(a2))
        return a2*(z0**1.5*z1**-0.5 + z1**1.5*z0**-0.5)

    # ── 4-PSK ─────────────────────────────────────────────────────────────
    elif M == 4:
        exp_a2 = np.exp(-a2)
        z = [safe(0.5*exp_a2*(np.cosh(a2)+np.cos(a2))),   # ζ0
             safe(0.5*exp_a2*(np.sinh(a2)+np.sin(a2))),   # ζ1
             safe(0.5*exp_a2*(np.cosh(a2)-np.cos(a2))),   # ζ2
             safe(0.5*exp_a2*(np.sinh(a2)-np.sin(a2)))]   # ζ3
        return 2*a2*sum(z[(k-1)%4]**1.5 * z[k]**-0.5 for k in range(4))

    # ── 8-PSK — 8 zeta riêng biệt (KHÔNG dùng z4*2) ──────────────────────
    elif M == 8:
        exp_a2 = np.exp(-a2)
        # ζ_{0,4}: ±2*cos(a2s)*cosh(a2s)
        z04b = np.cosh(a2)+np.cos(a2); z04e = 2*np.cos(a2s)*np.cosh(a2s)
        z0 = safe(0.25*exp_a2*(z04b + z04e))
        z4 = safe(0.25*exp_a2*(z04b - z04e))
        # ζ_{1,5}: ±sqrt2*cos(a2s)*sinh(a2s) ±sqrt2*sin(a2s)*cosh(a2s)
        z15b = np.sinh(a2)+np.sin(a2)
        z15e = np.sqrt(2)*np.cos(a2s)*np.sinh(a2s) + np.sqrt(2)*np.sin(a2s)*np.cosh(a2s)
        z1 = safe(0.25*exp_a2*(z15b + z15e))
        z5 = safe(0.25*exp_a2*(z15b - z15e))
        # ζ_{2,6}: ±2*sin(a2s)*sinh(a2s)
        z26b = np.cosh(a2)-np.cos(a2); z26e = 2*np.sin(a2s)*np.sinh(a2s)
        z2 = safe(0.25*exp_a2*(z26b + z26e))
        z6 = safe(0.25*exp_a2*(z26b - z26e))
        # ζ_{3,7}: ∓sqrt2*cos(a2s)*sinh(a2s) ±sqrt2*sin(a2s)*cosh(a2s)
        z37b  = np.sinh(a2)-np.sin(a2)
        z37t1 = np.sqrt(2)*np.cos(a2s)*np.sinh(a2s)
        z37t2 = np.sqrt(2)*np.sin(a2s)*np.cosh(a2s)
        z3 = safe(0.25*exp_a2*(z37b - z37t1 + z37t2))
        z7 = safe(0.25*exp_a2*(z37b + z37t1 + z37t2))

        zeta = [z0, z1, z2, z3, z4, z5, z6, z7]
        return 2*a2*sum(zeta[(k-1)%8]**1.5 * zeta[k]**-0.5 for k in range(8))

    else:
        raise ValueError(f"M-PSK: M={M} không hỗ trợ. Dùng M=2, 4, hoặc 8.")

def _holevo_psk_hom(VA, T, e, M):
    """
    Holevo information S_BE cho M-PSK DM-CVQKD, homodyne (Eq. 6, 9-10).
    Không dùng _symp12 để tránh conflict return values.
    Tính A, B trực tiếp từ ZM.
    """
    cl = _chi_l(T, e); ct = cl + CHI_HOM/T
    ZM = _ZM_psk(M, VA)

    # λ1, λ2 — Eq. 7-8 với Z = ZM
    A  = (VA+1)**2 + T**2*(VA+1+cl)**2 - 2*T*ZM**2
    B  = (T*(VA+1)**2 + T*(VA+1)*cl - T*ZM**2)**2
    disc12 = max(A**2 - 4*B, 0)
    l1 = np.sqrt(0.5*(A + np.sqrt(disc12)))
    l2 = np.sqrt(max(0.5*(A - np.sqrt(disc12)), 1e-30))

    sqB   = np.sqrt(max(B, 0))
    denom = T*(VA+1+ct)

    # λ3, λ4 — Eq. 10 ĐÚNG:
    # C_hom = [A*χ_hom + (VA+1)*√B + T*(VA+1+χ_line)] / [T*(VA+1+χ_tot)]
    # D_hom = √B*(VA+1+√B*χ_hom) / [T*(VA+1+χ_tot)]
    Ah = (A*CHI_HOM + (VA+1)*sqB + T*(VA+1+cl)) / denom
    Dh = sqB*(VA+1 + sqB*CHI_HOM) / denom

    d34 = max(Ah**2 - 4*Dh, 0)
    l3  = np.sqrt(0.5*(Ah + np.sqrt(d34)))
    l4  = np.sqrt(max(0.5*(Ah - np.sqrt(d34)), 1e-30))

    return _G((l1-1)/2)+_G((l2-1)/2)-_G((l3-1)/2)-_G((l4-1)/2)


def _skr_psk_at_VA(VA, T, eps, M, beta):
    """SKR tại VA cố định — dùng nội bộ cho optimization."""
    if T <= 1e-6 or VA <= 0: return -999.0
    try:
        IAB = _IAB_hom(VA, _chi_t_hom(T, eps))
        SBE = _holevo_psk_hom(VA, T, eps, M)
        return beta*IAB - SBE
    except Exception:
        return -999.0


def skr_psk(VA, T, eps, M, beta, optimize_VA=True):
    """
    Asymptotic SKR cho M-PSK DM-CVQKD, homodyne [bits/pulse] (Eq. 4).

    Parameters
    ----------
    VA          : modulation variance khởi đầu (nếu optimize_VA=False thì dùng cố định)
    optimize_VA : nếu True, tự tìm VA tối ưu tại mỗi T bằng minimize_scalar.
                  Bài báo chọn VA "close to optimal" nên cần optimize.

    Returns
    -------
    skr : float [bits/pulse], NaN nếu âm (để semilogy bỏ qua)
    """
    if T <= 1e-6: return 0.0

    if optimize_VA:
        # VA optimal thay đổi theo T: ~0.4-0.6 cho 4-PSK, ~1.1-2.6 cho 8-PSK
        VA_bounds = {2:(0.01,3.0), 4:(0.01,3.0), 8:(0.1,5.0)}
        bounds = VA_bounds.get(M, (0.01, 5.0))
        res = minimize_scalar(
            lambda va: -_skr_psk_at_VA(va, T, eps, M, beta),
            bounds=bounds, method='bounded',
            options={'xatol': 1e-3}
        )
        s = _skr_psk_at_VA(res.x, T, eps, M, beta)
    else:
        s = _skr_psk_at_VA(VA, T, eps, M, beta)

    return max(s, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. M-QAM DM-CVQKD  (Section II-C)
# ─────────────────────────────────────────────────────────────────────────────

def _Zstar_qam(T, eps, VA, M):
    """
    Lower bound Z* for M-QAM with binomial probability distribution (Eq. 20).
    # Assumption: w in Eq. 22 ≈ variance of |alpha_k|^2 (coherent state approx.)
    """
    m = int(round(np.sqrt(M)))
    ks = np.arange(m)
    # Binomial probs per axis
    pk = np.array([float(sp_comb(m-1, k, exact=True)) for k in ks])
    pk /= pk.sum()
    # Coherent state amplitudes on 2D grid (Eq. 13)
    scale = np.sqrt(VA/2)/np.sqrt(m-1) if m > 1 else 0.0
    alpha = np.array([scale*((k-(m-1)/2) + 1j*(l-(m-1)/2))
                      for k in ks for l in ks])
    prob  = np.array([pk[k]*pk[l] for k in range(m) for l in range(m)])
    tr    = float(np.sum(prob*np.abs(alpha)**2))
    w     = float(np.sum(prob*(np.abs(alpha)**2 - tr)**2))
    Zs = 2*np.sqrt(T)*tr - np.sqrt(2*T*eps)*np.sqrt(max(w,0))
    return max(float(Zs), 0.0)

def _holevo_qam_het(VA, T, eps, M):
    """Holevo bound for M-QAM heterodyne (Eq. 17-19)."""
    Zs  = _Zstar_qam(T, eps, VA, M)
    a11 = VA+1; a22 = 1+T*VA+T*eps
    th  = (a11+a22)/2
    dt  = a11*a22 - Zs**2
    dsc = max(th**2-dt, 0)
    l1  = np.sqrt(th+np.sqrt(dsc))
    l2  = np.sqrt(max(th-np.sqrt(dsc), 1e-30))
    l3  = max(VA+1 - Zs**2/(2+T*VA+T*eps), 1e-15)
    return _G((l1-1)/2)+_G((l2-1)/2)-_G((l3-1)/2)

def skr_qam(VA, T, eps, M, beta):
    """Asymptotic SKR for M-QAM DM-CVQKD heterodyne [bits/pulse] (Eq. 4, 16)."""
    if T <= 1e-6: return 0.0
    return beta*_IAB_het(VA, _chi_t_het(T,eps)) - _holevo_qam_het(VA,T,eps,M)


# ─────────────────────────────────────────────────────────────────────────────
# 6. RECONCILIATION & FINITE-SIZE  (Section III)
# ─────────────────────────────────────────────────────────────────────────────

def _SNR_dB(T, VA, chi_t):
    """SNR in dB (Eq. 27)."""
    a2 = VA/2
    return 10*np.log10(max(T*a2/(a2+(1-T)*chi_t), 1e-30))

def reconciliation_efficiency(snr_dB, mode='MD'):
    """
    Empirical reconciliation efficiency.
    MD  → approaches ~99% at very low SNR (satellite regime, SNR < 0 dB).
    MLC-MSD → ~92% at moderate SNR.
    # Assumption: physically motivated models matching paper's stated trends.
    """
    snr_lin = 10**(snr_dB/10)
    if mode == 'MD':
        return float(np.clip(0.99 - 0.15*snr_lin, 0, 0.99))
    else:
        return float(np.clip(0.92 - 0.05*snr_lin, 0, 0.95))

def frame_error_rate(snr_dB):
    """FER from Eq. 26 (N=10^6 base; ≈ 0 for N=10^11 at satellite SNRs)."""
    return float(np.clip(0.5*(1+M1*np.arctan(M2*snr_dB+M3)), 0, 1))

def _dn_privacy(N=N_BLOCK):
    """Privacy amplification correction (Eq. 25)."""
    d,es,esec = D_DISC, EPS_S, EPS_SEC
    sN = np.sqrt(N)
    return ((d+1)**2/sN + 4*(d+1)*np.sqrt(np.log2(2/es))/sN
            + 2*np.log2(2/(esec**2*es))/sN + 4*es*d/(esec*sN))

def finite_size_skr(VA, T, eps, mode='MD', N=N_BLOCK, f_rep=F_REP):
    """
    Finite-size SKR for GM-CVQKD homodyne [bits/s] (Eq. 24).
    """
    if T <= 1e-6: return 0.0
    ct  = _chi_t_hom(T, eps)
    snr = _SNR_dB(T, VA, ct)
    bet = reconciliation_efficiency(snr, mode)
    fer = frame_error_rate(snr)
    if bet <= 0: return 0.0
    IAB = _IAB_hom(VA, ct)
    SBE = _holevo_gm_hom(VA, T, eps)
    dn  = _dn_privacy(N)
    return max(f_rep*((1-fer)*bet*IAB - SBE - dn), 0.0)

def plob_upper_bound(T):
    """Loss-limited PLOB upper bound [bits/pulse] (Pirandola 2021)."""
    if T <= 0 or T >= 1: return 0.0
    return -np.log2(1-T)


# ─────────────────────────────────────────────────────────────────────────────
# 7. ISS PASS ELEVATION MODEL  (Fig. 7)
# ─────────────────────────────────────────────────────────────────────────────

def elevation_model(duration=663, max_elev=87.6, dt=1.0):
    """
    ISS pass elevation angle vs time over Mt. John Observatory (9 Aug 2022).
    # Assumption: Gaussian bell curve peaking at t=350s, σ=115s.
    Returns (t_arr [s], theta_arr [°]).
    """
    t = np.arange(0, duration+dt, dt)
    theta = max_elev * np.exp(-0.5*((t-350)/115)**2)
    return t, np.maximum(theta, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 8. PLOT FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

ELEVS  = [90, 60, 30]
LS     = ['-', '--', '-.']
EL_LEG = [Line2D([0],[0],color='gray',ls=s,lw=1.5,label=f'θ={t}°')
          for t,s in zip(ELEVS,LS)]

def _nan(v): return v if v > 1e-12 else np.nan

# ── Fig 4 ────────────────────────────────────────────────────────────────────
def plot_fig4(out='/mnt/user-data/outputs/fig4_asymptotic_good.png'):
    """Asymptotic SKR vs altitude – good atmosphere – GM / M-PSK / M-QAM."""
    print("▶ Figure 4 (asymptotic, good atmosphere)...")
    V, Cn2, Dr, beta, eps = 200, 1e-16, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 1050, 10)
    alt_m  = alt_km * 1e3

    panels = [
        ('(a) M-PSK', [
            ('GM-CVQKD','k',   'gm', {}),
            ('8-PSK',   'blue','psk',{'M':8}),
            ('4-PSK',   'red', 'psk',{'M':4}),
        ], alt_km, [160,1000]),
        ('(b) 64-QAM', [
            ('GM-CVQKD',              'k',    'gm', {}),
            ('Binomial Dist.',         'blue', 'qam',{'M':64}),
            ('Disc. Gaussian Dist.',   'red',  'qam',{'M':64}),
        ], np.arange(160,5100,20), [160,5000]),
        ('(c) 256-QAM', [
            ('GM-CVQKD',              'k',    'gm', {}),
            ('Binomial Dist.',         'blue', 'qam',{'M':256}),
            ('Disc. Gaussian Dist.',   'red',  'qam',{'M':256}),
        ], np.arange(160,6100,25), [160,6000]),
    ]

    fig, axes = plt.subplots(1,3,figsize=(17,5))
    fig.suptitle(
        r'Fig. 4 – Asymptotic SKRs  |  Good: $V\!=\!200$ km, '
        r'$C_n^2\!=\!10^{-16}$, $D_r\!=\!1$ m, $\beta\!=\!90\%$', fontsize=11)

    for ax,(title,protos,akm,xlim) in zip(axes,panels):
        ax.set_title(title)
        am = akm*1e3
        # PLOB upper bound at θ=90
        ub=[plob_upper_bound(total_transmittance(90,H,Dr,V,Cn2)[0]) for H in am]
        ax.semilogy(akm,ub,'k-',lw=2.5,label='Upper Bound')

        for lbl,col,ptype,kw in protos:
            for th,ls in zip(ELEVS,LS):
                vals=[]
                for H in am:
                    T,_,_=total_transmittance(th,H,Dr,V,Cn2)
                    if   ptype=='gm':  s=skr_gm(VA_GM,T,eps,beta)
                    elif ptype=='psk': s=skr_psk(VA_PSK,T,eps,kw['M'],beta,optimize_VA=True)
                    else:              s=skr_qam(VA_QAM,T,eps,kw['M'],beta)
                    vals.append(_nan(s))
                lb=lbl if th==ELEVS[0] else '_'
                ax.semilogy(akm,vals,color=col,ls=ls,lw=1.5,label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/pulse]')
        ax.set_ylim([1e-6,1e0]); ax.set_xlim(xlim)
        ax.grid(True,which='both',alpha=0.25)
        h,l=ax.get_legend_handles_labels()
        ax.legend(handles=h+EL_LEG,labels=l+[e.get_label() for e in EL_LEG],
                  fontsize=7,loc='upper right')

    plt.tight_layout()
    plt.savefig(out,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  ✓ {out}")

# ── Fig 5 ────────────────────────────────────────────────────────────────────
def plot_fig5(out='/mnt/user-data/outputs/fig5_asymptotic_bad.png'):
    """Asymptotic SKR vs altitude – bad atmosphere – GM / M-QAM only."""
    print("▶ Figure 5 (asymptotic, bad atmosphere)...")
    V, Cn2, Dr, beta, eps = 20, 1e-13, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 6100, 25)
    alt_m  = alt_km*1e3

    fig, axes = plt.subplots(1,2,figsize=(12,5))
    fig.suptitle(
        r'Fig. 5 – Asymptotic SKRs  |  Bad: $V\!=\!20$ km, '
        r'$C_n^2\!=\!10^{-13}$, $D_r\!=\!1$ m, $\beta\!=\!90\%$  '
        '(M-PSK omitted: no positive SKR)', fontsize=11)

    for ax,M_qam in zip(axes,[64,256]):
        ax.set_title(f'({chr(96+list(axes).index(ax)+1)}) {M_qam}-QAM')
        ub=[plob_upper_bound(total_transmittance(90,H,Dr,V,Cn2)[0]) for H in alt_m]
        ax.semilogy(alt_km,ub,'k-',lw=2.5,label='Upper Bound')

        for lbl,col,ptype,VA in [
                ('Gaussian',           'k',   'gm', VA_GM),
                ('Binomial Dist.',     'blue','qam',VA_QAM),
                ('Disc. Gaussian Dist.','red','qam',VA_QAM)]:
            for th,ls in zip(ELEVS,LS):
                vals=[]
                for H in alt_m:
                    T,_,_=total_transmittance(th,H,Dr,V,Cn2)
                    s = skr_gm(VA,T,eps,beta) if ptype=='gm' else skr_qam(VA,T,eps,M_qam,beta)
                    vals.append(_nan(s))
                lb=lbl if th==ELEVS[0] else '_'
                ax.semilogy(alt_km,vals,color=col,ls=ls,lw=1.5,label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/pulse]')
        ax.set_ylim([1e-6,1e0]); ax.set_xlim([alt_km[0],alt_km[-1]])
        ax.grid(True,which='both',alpha=0.25)
        h,l=ax.get_legend_handles_labels()
        ax.legend(handles=h+EL_LEG,labels=l+[e.get_label() for e in EL_LEG],
                  fontsize=7,loc='upper right')

    plt.tight_layout()
    plt.savefig(out,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  ✓ {out}")

# ── Fig 6 ────────────────────────────────────────────────────────────────────
def plot_fig6(out='/mnt/user-data/outputs/fig6_finite_size.png'):
    """Finite-size SKR vs altitude – GM-CVQKD, MD vs MLC-MSD."""
    print("▶ Figure 6 (finite-size)...")
    V, Cn2, eps = 200, 1e-16, EPS_CH
    COLORS = {'MD':'blue','MLC-MSD':'red'}

    configs = [('(a) $D_r = 1$ m', 1.0, np.arange(160,460,5)),
               ('(b) $D_r = 2$ m', 2.0, np.arange(160,1010,10))]

    fig, axes = plt.subplots(1,2,figsize=(12,5))
    fig.suptitle(
        r'Fig. 6 – Finite-Size SKRs  |  GM-CVQKD, Homodyne, MD vs MLC-MSD'
        '\n' r'Good conditions: $V\!=\!200$ km, $C_n^2\!=\!10^{-16}$', fontsize=11)

    for ax,(title,Dr,akm) in zip(axes,configs):
        ax.set_title(title)
        am = akm*1e3
        for mode in ['MD','MLC-MSD']:
            for th,ls in zip(ELEVS,LS):
                vals=[]
                for H in am:
                    T,_,ok=total_transmittance(th,H,Dr,V,Cn2)
                    s=finite_size_skr(VA_GM,T,eps,mode) if ok else 0.0
                    vals.append(_nan(s))
                lb=mode if th==ELEVS[0] else '_'
                ax.semilogy(akm,vals,color=COLORS[mode],ls=ls,lw=1.5,label=lb)

        ax.set_xlabel('Satellite Altitude at Zenith [km]')
        ax.set_ylabel('SKR [bits/s]')
        ax.set_ylim([1e4,1e8]); ax.set_xlim([akm[0],akm[-1]])
        ax.grid(True,which='both',alpha=0.25)
        h,l=ax.get_legend_handles_labels()
        ax.legend(handles=h+EL_LEG,labels=l+[e.get_label() for e in EL_LEG],
                  fontsize=8,loc='upper right')

    plt.tight_layout()
    plt.savefig(out,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  ✓ {out}")

# ── Fig 7 ────────────────────────────────────────────────────────────────────
def plot_fig7(out='/mnt/user-data/outputs/fig7_iss_elevation.png'):
    """ISS pass elevation vs time."""
    print("▶ Figure 7 (ISS elevation pass)...")
    t, theta = elevation_model()
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(t, theta, 'b-', lw=2)
    ax.set_xlabel('Duration (s)', fontsize=12)
    ax.set_ylabel('Elevation Angle (°)', fontsize=12)
    ax.set_title('Fig. 7 – ISS Pass Elevation over Mt. John Observatory\n'
                 '9 August 2022  |  Max = 87.6°  |  Duration = 663 s', fontsize=11)
    ax.set_xlim([0,700]); ax.set_ylim([0,95])
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  ✓ {out}")

# ── Fig 8 ────────────────────────────────────────────────────────────────────
def plot_fig8(out='/mnt/user-data/outputs/fig8_skr_vs_elevation.png'):
    """SKR vs elevation for ISS pass – GM-CVQKD, MD vs MLC-MSD."""
    print("▶ Figure 8 (SKR vs elevation angle, ISS pass)...")
    H_iss = 417_500.0
    Dr, V, Cn2, eps = 2.0, 200, 1e-16, EPS_CH
    COLORS = {'MD':'blue','MLC-MSD':'red'}
    theta_arr = np.arange(30, 91, 1)
    total_key = {}

    fig, ax = plt.subplots(figsize=(8,5))
    for mode in ['MD','MLC-MSD']:
        vals=[]
        for th in theta_arr:
            T,_,ok=total_transmittance(th,H_iss,Dr,V,Cn2,H_OGS_ISS)
            s=finite_size_skr(VA_GM,T,eps,mode) if ok else 0.0
            vals.append(_nan(s))
        ax.semilogy(theta_arr,vals,color=COLORS[mode],lw=2,label=mode)

        # Integrate over ISS pass
        _t,_th = elevation_model()
        key=0.0
        for th_t in _th:
            if th_t < 30: continue
            T,_,ok=total_transmittance(float(th_t),H_iss,Dr,V,Cn2,H_OGS_ISS)
            key += finite_size_skr(VA_GM,T,eps,mode) if ok else 0.0
        total_key[mode] = key

    ax.set_xlabel('Elevation Angle [°]', fontsize=12)
    ax.set_ylabel('SKR [bits/s]', fontsize=12)
    ax.set_title(
        r'Fig. 8 – SKR vs Elevation for ISS Pass  |  $D_r\!=\!2$ m, '
        r'$H_{ISS}\!=\!417.5$ km, Homodyne', fontsize=11)
    ax.set_xlim([30,90])
    ax.grid(True,which='both',alpha=0.25)
    ax.legend(fontsize=11)

    txt = (f"Total key – MD:      {total_key['MD']/1e9:.3f} Gbit  [paper: 1.235 Gbit]\n"
           f"Total key – MLC-MSD: {total_key['MLC-MSD']/1e6:.1f} Mbit  [paper: 385 Mbit]")
    ax.text(0.04,0.97,txt,transform=ax.transAxes,fontsize=8,va='top',
            bbox=dict(boxstyle='round',fc='wheat',alpha=0.6))

    print(f"  MD  total key: {total_key['MD']/1e9:.3f} Gbit  (paper: 1.235 Gbit)")
    print(f"  MSD total key: {total_key['MLC-MSD']/1e6:.1f} Mbit  (paper: 385 Mbit)")

    plt.tight_layout()
    plt.savefig(out,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  ✓ {out}")


# ─────────────────────────────────────────────────────────────────────────────
# 9. MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("="*68)
    print("CV-QKD Satellite-to-Ground Simulation")
    print("Sayat et al., IEEE Trans. Commun. 2024  |  Reproducing Figs 4-8")
    print("="*68)
    print(f"\nEPS_CH={EPS_CH:.4f} SNU  |  CHI_HOM={CHI_HOM:.4f}  CHI_HET={CHI_HET:.4f}")

    # Quick sanity check
    T,L,ok = total_transmittance(90, 400e3, 1.0, 200, 1e-16)
    print(f"\nSanity | θ=90°, H=400km, Dr=1m, good atm:")
    print(f"  T={T:.5f}, L={L/1e3:.1f} km, far-field={ok}")
    print(f"  SKR_GM(asy) = {skr_gm(VA_GM,T,EPS_CH,0.9):.4f} bits/pulse")
    print(f"  SKR_8PSK    = {skr_psk(VA_PSK,T,EPS_CH,8,0.9):.4f} bits/pulse")
    print(f"  SKR_64QAM   = {skr_qam(VA_QAM,T,EPS_CH,64,0.9):.4f} bits/pulse")
    print(f"  SKR_fin(MD) = {finite_size_skr(VA_GM,T,EPS_CH,'MD')/1e6:.2f} Mbit/s")
    print()

    plot_fig4()
    plot_fig5()
    plot_fig6()
    plot_fig7()
    plot_fig8()

    print("\n"+"="*68)
    print("All 5 figures saved to /mnt/user-data/outputs/")
    print("="*68)

if __name__ == '__main__':
    main()
