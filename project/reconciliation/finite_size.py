import numpy as np

from ..config import D_DISC, EPS_S, EPS_SEC, F_REP, M1, M2, M3, N_BLOCK, RECON_COEFFS
from ..protocols.gm import _IAB_hom, _chi_t_hom, _holevo_gm_hom
from ..utils.logger import _log_calc


def _SNR_dB(T, alpha_sq, chi_t):
    """SNR in dB (Eq. 27)."""
    num = T * alpha_sq
    den = alpha_sq + (1 - T) * chi_t
    snr_lin = num / max(den, 1e-30)
    return 10 * np.log10(max(snr_lin, 1e-30))


def reconciliation_efficiency(snr_dB, mode="MD"):
    """Reconciliation efficiency β from Eq. (26) and Table II."""
    if mode not in RECON_COEFFS:
        raise ValueError(f"Unsupported reconciliation mode: {mode}")
    snr_lin = 10 ** (snr_dB / 10)
    c = RECON_COEFFS[mode]
    beta = c["c1"] * (snr_lin ** c["c2"]) + c["c3"] * (snr_lin ** c["c4"])
    return float(np.clip(beta, 0.0, 1.0))


def frame_error_rate(snr_dB):
    """FER from Eq. 26 (N=10^6 base; ≈ 0 for N=10^11 at satellite SNRs)."""
    return float(np.clip(0.5 * (1 + M1 * np.arctan(M2 * snr_dB + M3)), 0, 1))


def _dn_privacy(N=N_BLOCK):
    """Privacy amplification correction (Eq. 25)."""
    d, es, esec = D_DISC, EPS_S, EPS_SEC
    sN = np.sqrt(N)
    # Eq. (25): all four terms scale with 1/sqrt(N).
    return (
        (d + 1) ** 2 / sN
        + 4 * (d + 1) * np.sqrt(np.log2(2 / es)) / sN
        + 2 * np.log2(2 / (esec**2 * es)) / sN
        + 4 * es * d / (esec * sN)
    )


def finite_size_skr(VA, T, eps, mode="MD", N=N_BLOCK, f_rep=F_REP):
    """
    Finite-size SKR for GM-CVQKD homodyne [bits/s] (Eq. 24).
    """
    ct = _chi_t_hom(T, eps)
    snr = _SNR_dB(T, VA / 2.0, ct)
    bet = reconciliation_efficiency(snr, mode)
    fer = frame_error_rate(snr)
    IAB = _IAB_hom(VA, ct)
    SBE = _holevo_gm_hom(VA, T, eps)
    dn = _dn_privacy(N)
    skr = f_rep * ((1 - fer) * bet * IAB - SBE - dn)
    _log_calc(
        "finite_size_skr",
        protocol="GM",
        mode=mode,
        VA=VA,
        T=T,
        eps_ch=eps,
        chi_t=ct,
        snr_dB=snr,
        beta=bet,
        FER=fer,
        I_AB=IAB,
        S_BE=SBE,
        delta_n=dn,
        f_rep=f_rep,
        SKR_bps=skr,
    )
    return skr


def plob_upper_bound(T):
    """Loss-limited PLOB upper bound [bits/pulse] (Pirandola 2021)."""
    if T <= 0 or T >= 1:
        return 0.0
    return -np.log2(1 - T)
