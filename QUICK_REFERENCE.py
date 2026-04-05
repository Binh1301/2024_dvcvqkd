"""
QUICK REFERENCE: Key Equations & Variable Definitions
From: "Satellite-to-Ground CV-QKD" (Sayat et al., IEEE TCOMM 2024)
Source: cvqkd_simulation.py
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PART A: NOISE TERMS & DETECTOR DEFINITIONS (Eq. 3)
# ═══════════════════════════════════════════════════════════════════════════════

# Physical Constants
ETA = 0.6                                   # Detector quantum efficiency @ 1550 nm
EPS_CH = 0.0186                             # Channel excess noise [SNU]
EPS_DET = 0.0135                            # Detector excess noise [SNU]

# Homodyne Detection (used in GM, M-PSK)
CHI_HOM = (1 - ETA + EPS_DET) / ETA          # ≈ 0.6892 [SNU]
# Formula: χ_hom = (1 - η + ε_det) / η
# Meaning: homodyne noise variance in shot-noise units

# Heterodyne Detection (used in M-QAM)
CHI_HET = (1 + (1 - ETA) + 2 * EPS_DET) / ETA  # ≈ 1.3783 [SNU]
# Formula: χ_het = (1 + (1-η) + 2·ε_det) / η
# Meaning: heterodyne noise variance (2× homodyne) in SNU

# ─────────────────────────────────────────────────────────────────────────────

# Channel Loss Noise (Eq. 3, fundamental)
# χ_line(T, ε_ch) = 1/T - 1 + ε_ch  [SNU]
# Meaning: thermal noise from lost modes + excess channel noise

def _chi_l(T, e):
    """Channel loss noise [SNU]"""
    return 1/T - 1 + e

# Total Noise - Homodyne (Eq. 3)
# χ_tot^hom(T, ε_ch) = χ_line(T, ε_ch) + χ_hom / T
def _chi_t_hom(T, e):
    """Total receiver noise - homodyne [SNU]"""
    return _chi_l(T, e) + CHI_HOM / T

# Total Noise - Heterodyne (Eq. 3)
# χ_tot^het(T, ε_ch) = χ_line(T, ε_ch) + χ_het / T
def _chi_t_het(T, e):
    """Total receiver noise - heterodyne [SNU]"""
    return _chi_l(T, e) + CHI_HET / T

# ═══════════════════════════════════════════════════════════════════════════════
# PART B: KEY RATE FORMULAS
# ═══════════════════════════════════════════════════════════════════════════════

# Mutual Information - Homodyne (used in GM, M-PSK)
# I_A|B(homodyne) = 0.5 · log₂((V_A + 1 + χ_tot) / (1 + χ_tot))  [bits/pulse]
def _IAB_hom(VA, chi_t):
    """Alice-Bob mutual information - homodyne [bits/pulse]"""
    return 0.5 * np.log2((VA + 1 + chi_t) / (1 + chi_t))

# Mutual Information - Heterodyne (used in M-QAM)
# I_A|B(heterodyne) = log₂((V_A + 1 + χ_tot) / (1 + χ_tot))  [bits/pulse]
def _IAB_het(VA, chi_t):
    """Alice-Bob mutual information - heterodyne [bits/pulse]"""
    return np.log2((VA + 1 + chi_t) / (1 + chi_t))

# ─────────────────────────────────────────────────────────────────────────────

# Entropy Function (G-function, used in Holevo bounds)
# G(x) = (x+1)·log₂(1+x) - x·log₂(x)  [bits]
def _G(x):
    """Shannon entropy for symplectic eigenvalue x"""
    x = float(x)
    if x < 1e-10:
        return 0.0
    return (x + 1) * np.log2(1 + x) - x * np.log2(x)

# ─────────────────────────────────────────────────────────────────────────────

# ASYMPTOTIC SECRET KEY RATE - GM (Eq. 4)
# K_∞^GM = β · I_A|B^hom - χ_BE^GM  [bits/pulse]
# where χ_BE^GM = Holevo bound from symplectic eigenvalues
def skr_gm(VA, T, eps, beta):
    """Asymptotic SKR - Gaussian Modulation (homodyne) [bits/pulse]"""
    if T <= 1e-6:
        return 0.0
    chi_t = _chi_t_hom(T, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_gm_hom(VA, T, eps)  # See Part C
    return max(beta * I_AB - S_BE, 0.0)

# ASYMPTOTIC SECRET KEY RATE - M-PSK (Eq. 4 variant)
# K_∞^PSK = β · I_A|B^hom - χ_BE^PSK  [bits/pulse]
def skr_psk(VA, T, eps, M, beta):
    """Asymptotic SKR - M-PSK (homodyne) [bits/pulse]"""
    if T <= 1e-6:
        return 0.0
    chi_t = _chi_t_hom(T, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_psk_hom(VA, T, eps, M)  # See Part C
    return max(beta * I_AB - S_BE, 0.0)

# ASYMPTOTIC SECRET KEY RATE - M-QAM (Eq. 16)
# K_∞^QAM = β · I_A|B^het - χ_BE^QAM  [bits/pulse]
def skr_qam(VA, T, eps, M, beta):
    """Asymptotic SKR - M-QAM (heterodyne) [bits/pulse]"""
    if T <= 1e-6:
        return 0.0
    chi_t = _chi_t_het(T, eps)
    I_AB = _IAB_het(VA, chi_t)
    S_BE = _holevo_qam_het(VA, T, eps, M)  # See Part C
    return max(beta * I_AB - S_BE, 0.0)

# ═══════════════════════════════════════════════════════════════════════════════
# PART C: HOLEVO BOUNDS (Eq. 6, 9, 17-19)
# ═══════════════════════════════════════════════════════════════════════════════

# GM HOLEVO BOUND - HOMODYNE (Eq. 6, 9)
# χ_BE = G((λ₁-1)/2) + G((λ₂-1)/2) - G((λ₃-1)/2) - G((λ₄-1)/2)
# where {λᵢ} are symplectic eigenvalues from covariance matrix
def _holevo_gm_hom(VA, T, e):
    """Holevo bound - GM homodyne (Eq. 6, 9) [bits/pulse]"""
    chi_l = _chi_l(T, e)
    chi_h = CHI_HOM
    chi_tot = chi_l + chi_h / T
    
    # First symplectic eigenvalue pair (λ₁, λ₂)
    l1, l2, B, A = _symp12(VA, T, chi_l)
    sqB = np.sqrt(max(B, 0))
    
    # Second symplectic eigenvalue pair (λ₃, λ₄) — Eq. 9
    denom = T * (VA + 1 + chi_tot)
    C = (A * chi_h + (VA + 1) * sqB + T * (VA + 1 + chi_l)) / denom
    D = (sqB * (VA + 1 + sqB * chi_h)) / denom
    
    disc = max(C**2 - 4 * D, 0)
    l3 = np.sqrt(max(0.5 * (C + np.sqrt(disc)), 1.0))
    l4 = np.sqrt(max(0.5 * (C - np.sqrt(disc)), 1.0))
    
    return (_G((l1-1)/2) + _G((l2-1)/2) - _G((l3-1)/2) - _G((l4-1)/2))

# M-QAM HOLEVO BOUND - HETERODYNE (Eq. 17-19)
# χ_BE^het = G((λ₁-1)/2) + G((λ₂-1)/2) - G((λ₃-1)/2)
def _holevo_qam_het(VA, T, eps, M):
    """Holevo bound - M-QAM heterodyne (Eq. 17-19) [bits/pulse]"""
    Zs = _Zstar_qam(T, eps, VA, M)
    
    # Symplectic eigenvalues for heterodyne (2-mode system)
    a11 = VA + 1
    a22 = 1 + T*VA + T*eps
    th = (a11 + a22) / 2
    dt = a11*a22 - Zs**2
    dsc = max(th**2 - dt, 0)
    
    l1 = np.sqrt(th + np.sqrt(dsc))
    l2 = np.sqrt(max(th - np.sqrt(dsc), 1e-30))
    l3 = max(VA + 1 - Zs**2 / (2 + T*VA + T*eps), 1e-15)
    
    return _G((l1-1)/2) + _G((l2-1)/2) - _G((l3-1)/2)

# ═══════════════════════════════════════════════════════════════════════════════
# PART D: RECONCILIATION & FINITE-SIZE (Eq. 23-27)
# ═══════════════════════════════════════════════════════════════════════════════

# RECONCILIATION EFFICIENCY (Eq. 23)
# β(SNR) [dimensionless] = 0.99 - 0.15·γ_lin (for Multilevel Direct)
def reconciliation_efficiency(snr_dB, mode='MD'):
    """Reconciliation efficiency (Eq. 23) [dimensionless]"""
    snr_lin = 10**(snr_dB/10)
    if mode == 'MD':
        return float(np.clip(0.99 - 0.15*snr_lin, 0, 0.99))
    else:
        return float(np.clip(0.92 - 0.05*snr_lin, 0, 0.95))

# SNR DEFINITION (Eq. 27)
# SNR [dB] = 10·log₁₀( T·V_A/2 / (V_A/2 + (1-T)·χ_tot) )
def _SNR_dB(T, VA, chi_t):
    """Signal-to-noise ratio (Eq. 27) [dB]"""
    a2 = VA / 2
    return 10 * np.log10(max(T*a2 / (a2 + (1-T)*chi_t), 1e-30))

# FRAME ERROR RATE (Eq. 26)
# FER(SNR) = 0.5·[1 + M₁·arctan(M₂·SNR + M₃)]
# Parameters: M₁=0.8218, M₂=-19.46, M₃=-298.1
def frame_error_rate(snr_dB):
    """Frame error rate from reconciliation (Eq. 26) [dimensionless]"""
    M1, M2, M3 = 0.8218, -19.46, -298.1
    return float(np.clip(0.5*(1 + M1*np.arctan(M2*snr_dB + M3)), 0, 1))

# PRIVACY AMPLIFICATION (Eq. 25)
# Δn = (d+1)²/√N + 4(d+1)√log₂(2/εₛ)/√N + 2·log₂(2/(εₛₑc²·εₛ))/√N + 4·εₛ·d/(εₛₑc·√N)
def _dn_privacy(N=1e11):
    """Privacy amplification correction (Eq. 25) [bits]"""
    d = 5                  # D_DISC
    es = 2e-10             # EPS_S
    esec = 1e-9            # EPS_SEC
    sN = np.sqrt(N)
    return ((d+1)**2/sN + 4*(d+1)*np.sqrt(np.log2(2/es))/sN
            + 2*np.log2(2/(esec**2*es))/sN + 4*es*d/(esec*sN))

# FINITE-SIZE SECRET KEY RATE (Eq. 24)
# K_fin = f_rep·[(1-FER)·β·I_A|B - χ_BE - Δn]
def finite_size_skr(VA, T, eps, mode='MD', N=1e11, f_rep=50e6):
    """Finite-size SKR - GM homodyne (Eq. 24) [bits/s]"""
    if T <= 1e-6:
        return 0.0
    ct = _chi_t_hom(T, eps)
    snr = _SNR_dB(T, VA, ct)
    bet = reconciliation_efficiency(snr, mode)
    fer = frame_error_rate(snr)
    if bet <= 0:
        return 0.0
    IAB = _IAB_hom(VA, ct)
    SBE = _holevo_gm_hom(VA, T, eps)
    dn = _dn_privacy(N)
    return max(f_rep * ((1-fer) * bet * IAB - SBE - dn), 0.0)

# ═══════════════════════════════════════════════════════════════════════════════
# PART E: CHANNEL MODEL (Eq. 28-33)
# ═══════════════════════════════════════════════════════════════════════════════

# LINK GEOMETRY (Eq. 28)
# L_tot = √[(RE+H_zen)² + (RE+H_ogs)² - 2(RE+H_zen)(RE+H_ogs)·cos(a1)]
# L_atm = atmospheric path via ray-sphere intersection
def link_geometry(theta_deg, H_zen, H_ogs=0, H_atm=20e3):
    """Total link distance and atmospheric thickness (Eq. 28) [m]"""
    th = np.radians(theta_deg)
    sa1 = np.clip(np.cos(th) * (RE + H_ogs) / (RE + H_zen), -1, 1)
    a1 = np.arcsin(sa1) + (np.pi/2 - th)
    L_tot = np.sqrt((RE+H_zen)**2 + (RE+H_ogs)**2 - 2*(RE+H_zen)*(RE+H_ogs)*np.cos(a1))
    # L_atm = _L_atm_eff_ray(theta_deg, H_ogs, H_atm)  [see full implementation]
    return L_tot

# GEOMETRIC LOSS (Eq. 29)
# A_geo [dB] = 10·log₁₀( L_tot²·λ² / (D_T²·D_r²·T_T·(1-L_P)·T_R) )
def geometric_loss_dB(L_tot, Dr, DT=0.3, TT=0.9, TR=0.9, LP=0.1, LAMBDA=1550e-9):
    """Free-space diffraction loss (Eq. 29) [dB]"""
    return 10*np.log10(L_tot**2 * LAMBDA**2 / (DT**2 * Dr**2 * TT * (1-LP) * TR))

# SCATTERING LOSS (Eq. 30)
# α_scat [dB/km] = 10·log₁₀(e) · (3.912/V) · (1550/550)^(-p)
def scattering_loss_dBpkm(V_km):
    """Mie scattering loss - Kruse-Kim model (Eq. 30) [dB/km]"""
    if   V_km >= 50: p = 1.6
    elif V_km >= 6:  p = 1.3
    elif V_km >= 1:  p = 0.16*V_km + 0.34
    elif V_km >= 0.5:p = V_km - 0.5
    else:            p = 0.0
    return 10*np.log10(np.e) * (3.912/V_km) * (1550/550)**(-p)

# SCINTILLATION INDEX (Eq. 32)
# σ²_I = exp(T₁ + T₂) - 1  (aperture-averaged)
def scintillation_index(Cn2, Dr, L_atm, LAMBDA=1550e-9):
    """Aperture-averaged scintillation index (Eq. 32) [dimensionless]"""
    k = 2*np.pi/LAMBDA
    d = Dr * np.sqrt(np.pi/(2*LAMBDA*L_atm))
    s2R = 2.25 * k**(7/6) * Cn2 * L_atm**(11/6) * (6/11)
    t1 = 0.20*s2R / (1 + 0.18*d**2 + 0.20*s2R**(6/5))**(7/6)
    t2 = (0.21*s2R*(1+0.24*s2R**(6/5))**(-5/6)) / (1 + 0.90*d**2 + 0.21*d**2*s2R**(6/5))
    return float(np.exp(t1+t2) - 1.0)

# SCINTILLATION LOSS (Eq. 31)
# A_sci [dB] = 4.343·erfinv(2p_thr-1)·√(2·ln(σ²_I+1)) - 0.5·ln(σ²_I+1)
def scintillation_loss_dB(s2I, p_thr=1e-6):
    """Scintillation loss with aperture averaging (Eq. 31) [dB]"""
    from scipy.special import erfinv
    arg = float(np.clip(2*p_thr-1, -0.9999, 0.9999))
    A_sci = (4.343 * erfinv(arg) * np.sqrt(2 * np.log(s2I + 1)) - 0.5 * np.log(s2I + 1))
    return abs(A_sci)

# TOTAL TRANSMITTANCE (Eq. 33)
# T [linear] = 10^(-(A_geo + A_scat + A_sci)/10)
def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=0):
    """Total channel transmittance (Eq. 33) [linear, 0≤T≤1]"""
    L_tot = link_geometry(theta_deg, H_zen, H_ogs)
    # [obtain L_atm from _L_atm_eff_ray, then:]
    A_geo = geometric_loss_dB(L_tot, Dr)
    # A_scat, A_sci similarly computed...
    # T = 10**(-total_loss_dB / 10)
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETER VALUES (Table I, III from Paper)
# ═══════════════════════════════════════════════════════════════════════════════

LAMBDA = 1550e-9          # Wavelength [m]
RE = 6_371_000.0          # Earth radius [m]

# Hardware
DT = 0.3                  # TX aperture [m]
TT = 0.9                  # TX efficiency
TR = 0.9                  # RX efficiency
LP = 0.1                  # Pointing/APT loss

# Modulation variances [SNU]
VA_GM = 5.0               # Gaussian Modulation
VA_PSK = 0.5              # M-PSK
VA_QAM = 2.0              # M-QAM

# Finite-size
F_REP = 50e6              # Repetition rate [Hz]
N_BLOCK = 1e11            # Block size [symbols]

# ═══════════════════════════════════════════════════════════════════════════════
# END OF QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════════════════════
