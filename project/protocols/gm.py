import numpy as np

from ..config import CHI_HET, CHI_HOM, EPS_DET
from ..utils.logger import _log_calc


def _G(x):
    x = float(x)

    if x < 1e-10:
        return 0.0

    return (x + 1) * np.log2(x + 1) - x * np.log2(x)


def _eps_total(T, eps_ch, eps_det=EPS_DET):
    """Total noise referred to channel input: eps_ch + eps_det / T."""
    Ts = max(float(T), 1e-300)
    return eps_ch + eps_det / Ts


def _chi_l(T, e):
    Ts = max(float(T), 1e-300)
    return 1 / Ts - 1 + e


def _chi_t_hom(T, e):
    Ts = max(float(T), 1e-300)
    return _chi_l(Ts, e) + CHI_HOM / Ts


def _chi_t_het(T, e):
    Ts = max(float(T), 1e-300)
    return _chi_l(Ts, e) + CHI_HET / Ts


def _IAB_hom(VA, chi_t):
    return 0.5 * np.log2(1 + VA / (1 + chi_t))


def _IAB_het(VA, chi_t):
    return np.log2(1 + VA / (1 + chi_t))


def _symp12(VA, T, chi_l, Z=None):  # # đúng
    Ts = max(float(T), 1e-300)
    if Z is None:
        Z = np.sqrt(VA**2 + 2 * VA)
    eps_ch = chi_l - (1 / Ts - 1)
    t_v = Ts * (VA + 1 + chi_l)  # equals T*(VA+1+chi_l)
    A = (VA + 1) ** 2 + t_v**2 - 2 * Ts * (Z**2)
    B_inner = Ts * ((VA + 1) ** 2 + (VA + 1) * chi_l - Z**2)
    B = B_inner**2
    disc = max(A**2 - 4 * B, 0)
    l1 = np.sqrt(max(0.5 * (A + np.sqrt(disc)), 1e-30))
    l2 = np.sqrt(max(0.5 * (A - np.sqrt(disc)), 1e-30))

    return l1, l2, B, A


def _holevo_gm_hom(VA, T, e):
    """Holevo bound for GM-CVQKD homodyne (Eq. 6-10)."""
    Ts = max(float(T), 1e-300)
    chi_l = _chi_l(T, e)
    chi_h = CHI_HOM
    chi_tot = chi_l + chi_h / Ts

    l1, l2, B, A = _symp12(VA, Ts, chi_l)
    sqB = np.sqrt(max(B, 0))

    denom = Ts * (1.0 + VA + chi_tot)

    C = (A * chi_h + (VA + 1) * sqB + Ts * (VA + 1 + chi_l)) / denom

    D = (sqB * (VA + 1 + sqB * chi_h)) / denom

    disc = max(C**2 - 4 * D, 0)
    sqrt_disc = np.sqrt(disc)
    l3 = np.sqrt(max(0.5 * (C + sqrt_disc), 1e-30))
    l4 = np.sqrt(max(0.5 * (C - sqrt_disc), 1e-30))

    return _G((l1 - 1) / 2) + _G((l2 - 1) / 2) - _G((l3 - 1) / 2) - _G((l4 - 1) / 2)


def skr_gm(VA, T, eps, beta):
    """Asymptotic SKR for GM-CVQKD [bits/pulse] (Eq. 4)."""
    chi_t = _chi_t_hom(T, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_gm_hom(VA, T, eps)
    skr = beta * I_AB - S_BE
    _log_calc(
        "skr_gm",
        protocol="GM",
        VA=VA,
        T=T,
        eps_ch=eps,
        beta=beta,
        chi_t=chi_t,
        I_AB=I_AB,
        S_BE=S_BE,
        SKR=skr,
    )
    return skr
