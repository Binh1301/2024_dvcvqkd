import numpy as np

from ..utils.logger import _log_calc
from .gm import _G, _IAB_hom, _chi_l, _chi_t_hom, _symp12
from ..config import CHI_HOM


def compute_ZM_PSK(VA, M):
    """Correlation coefficient Z_M for M-PSK (supports M=2,4,8)."""
    if M not in (2, 4, 8):
        raise ValueError(f"M-PSK supports only M=2,4,8. M={M}")
    if VA < 0:
        raise ValueError("VA must be non-negative.")
    if VA <= np.finfo(float).eps:
        return 0.0

    alpha2 = float(VA) / 2.0
    tiny = np.finfo(float).tiny

    if M == 2:
        z0 = np.exp(-alpha2) * np.cosh(alpha2)
        z1 = np.exp(-alpha2) * np.sinh(alpha2)
        z0 = max(float(z0), tiny)
        z1 = max(float(z1), tiny)
        zm = alpha2 * (z0 ** 1.5 * z1 ** (-0.5) + z1 ** 1.5 * z0 ** (-0.5))
    elif M == 4:
        ea = np.exp(-alpha2)
        z = np.array(
            [
                0.5 * ea * (np.cosh(alpha2) + np.cos(alpha2)),
                0.5 * ea * (np.sinh(alpha2) + np.sin(alpha2)),
                0.5 * ea * (np.cosh(alpha2) - np.cos(alpha2)),
                0.5 * ea * (np.sinh(alpha2) - np.sin(alpha2)),
            ],
            dtype=float,
        )
        z = np.maximum(z, tiny)
        zm = 2.0 * alpha2 * float(np.sum(np.roll(z, 1) ** 1.5 * z ** (-0.5)))
    else:
        a2 = alpha2
        a2s = alpha2 / np.sqrt(2.0)
        ea = np.exp(-a2)
        z = np.empty(8, dtype=float)
        z[0] = 0.25 * ea * (np.cosh(a2) + np.cos(a2) + 2.0 * np.cos(a2s) * np.cosh(a2s))
        z[4] = 0.25 * ea * (np.cosh(a2) + np.cos(a2) - 2.0 * np.cos(a2s) * np.cosh(a2s))
        z[1] = 0.25 * ea * (
            np.sinh(a2)
            + np.sin(a2)
            + np.sqrt(2.0) * np.cos(a2s) * np.sinh(a2s)
            + np.sqrt(2.0) * np.sin(a2s) * np.cosh(a2s)
        )
        z[5] = 0.25 * ea * (
            np.sinh(a2)
            + np.sin(a2)
            - np.sqrt(2.0) * np.cos(a2s) * np.sinh(a2s)
            - np.sqrt(2.0) * np.sin(a2s) * np.cosh(a2s)
        )
        z[2] = 0.25 * ea * (np.cosh(a2) - np.cos(a2) + 2.0 * np.sin(a2s) * np.sinh(a2s))
        z[6] = 0.25 * ea * (np.cosh(a2) - np.cos(a2) - 2.0 * np.sin(a2s) * np.sinh(a2s))
        z[3] = 0.25 * ea * (
            np.sinh(a2)
            - np.sin(a2)
            - np.sqrt(2.0) * np.cos(a2s) * np.sinh(a2s)
            + np.sqrt(2.0) * np.sin(a2s) * np.cosh(a2s)
        )
        z[7] = 0.25 * ea * (
            np.sinh(a2)
            - np.sin(a2)
            + np.sqrt(2.0) * np.cos(a2s) * np.sinh(a2s)
            - np.sqrt(2.0) * np.sin(a2s) * np.cosh(a2s)
        )
        z = np.maximum(z, 1e-300)
        zm = 2.0 * alpha2 * float(np.sum(np.roll(z, 1) ** 1.5 * z ** (-0.5)))

    _log_calc("ZM_psk", protocol="PSK", M=M, VA=VA, alpha2=alpha2, ZM=zm)
    return float(zm)


def _psk_zeta_components(M, a2):
    idx = np.arange(M, dtype=float)
    phi = 2.0 * np.pi * idx / M
    vals = np.exp(a2 * np.exp(1j * phi))
    phase = np.exp(-1j * np.outer(idx, phi))
    zeta = (np.exp(-a2) / M) * (phase @ vals)
    imag_max = float(np.max(np.abs(np.imag(zeta))))
    z = np.real_if_close(zeta, tol=1e6).real
    tiny = np.finfo(float).tiny
    return np.clip(z, tiny, None), imag_max


def _ZM_psk(M, VA):
    return compute_ZM_PSK(VA=VA, M=M)


def compute_SKR_MPSK(T_eff, VA, M, beta, eta_det, eps_ch, vel):
    """SKR for M-PSK DM-CVQKD (homodyne) with UAV-HAP T_eff."""
    Ts = max(float(T_eff), 1e-300)
    chi_hom = (1.0 - float(eta_det)) / max(float(eta_det), 1e-300) + float(vel) / max(float(eta_det), 1e-300)
    chi_line = 1.0 / Ts - 1.0 + float(eps_ch)
    chi_tot = chi_line + chi_hom / Ts
    V = float(VA) + 1.0
    i_ab = 0.5 * np.log2((V + chi_tot) / max(1.0 + chi_tot, 1e-300))

    zm = compute_ZM_PSK(VA=VA, M=M)
    A = V**2 + Ts**2 * (V + chi_line) ** 2 - 2.0 * Ts * zm**2
    B = (Ts * V**2 + Ts * V * chi_line - Ts * zm**2) ** 2

    disc = A**2 - 4.0 * B
    if disc < 0.0:
        return 0.0
    sqrt_disc = np.sqrt(disc)
    l1 = np.sqrt(max(0.5 * (A + sqrt_disc), 0.0))
    l2 = np.sqrt(max(0.5 * (A - sqrt_disc), 0.0))

    sqrt_b = np.sqrt(max(B, 0.0))
    denom = Ts * max(V + chi_tot, 1e-300)
    C_hom = (A * chi_hom + V * sqrt_b + Ts * (V + chi_line)) / denom
    D_hom = sqrt_b * (V + sqrt_b * chi_hom) / denom
    disc3 = C_hom**2 - 4.0 * D_hom
    if disc3 < 0.0:
        return 0.0
    sqrt_disc3 = np.sqrt(disc3)
    l3 = np.sqrt(max(0.5 * (C_hom + sqrt_disc3), 0.0))
    l4 = np.sqrt(max(0.5 * (C_hom - sqrt_disc3), 0.0))

    def g(x):
        if x <= 1.0 + 1e-10:
            return 0.0
        a_ = (x + 1.0) / 2.0
        b_ = (x - 1.0) / 2.0
        return a_ * np.log2(a_) - b_ * np.log2(b_)

    chi_be = g(l1) + g(l2) - g(l3) - g(l4)
    skr = float(beta) * i_ab - chi_be
    _log_calc(
        "skr_mpsk_hom",
        protocol="PSK",
        M=M,
        VA=VA,
        T_eff=Ts,
        beta=beta,
        eta_det=eta_det,
        eps_ch=eps_ch,
        vel=vel,
        ZM=zm,
        I_AB=i_ab,
        chi_BE=chi_be,
        SKR=skr,
    )
    return max(float(skr), 0.0)


def _holevo_psk_hom(VA, T, e, M):
    """
    Holevo Information for PSK-modulated Homodyne Detection
    S_BE = G(λ1-1/2) + G(λ2-1/2) - G(λ3-1/2) - G(λ4-1/2)
    """
    Ts = max(float(T), 1e-300)
    cl = _chi_l(Ts, e)
    ZM = _ZM_psk(M, VA)
    B_inner = Ts * ((VA + 1.0) ** 2 + (VA + 1.0) * cl - ZM**2)
    if B_inner < -1e-12:
        raise ValueError(
            f"Unphysical PSK covariance: B_inner={B_inner:.3e} < 0 for M={M}, VA={VA}, T={Ts}."
        )

    l1, l2, B, A = _symp12(VA, Ts, cl, Z=ZM)
    sqB = np.sqrt(max(B, 0.0))
    chi_tot = cl + CHI_HOM / Ts
    denom = Ts * (1.0 + VA + chi_tot)
    t_v = Ts * (VA + 1.0 + cl)
    Ah = (A * CHI_HOM + (VA + 1.0) * sqB + t_v) / denom
    Dh = sqB * (VA + 1.0 + sqB * CHI_HOM) / denom

    d34 = max(Ah**2 - 4.0 * Dh, 0.0)
    l3 = np.sqrt(0.5 * (Ah + np.sqrt(d34)))
    l4 = np.sqrt(max(0.5 * (Ah - np.sqrt(d34)), 1e-30))

    # Holevo information
    S_BE = _G((l1 - 1.0) / 2.0) + _G((l2 - 1.0) / 2.0) - _G((l3 - 1.0) / 2.0) - _G((l4 - 1.0) / 2.0)
    _log_calc(
        "holevo_psk_hom",
        protocol="PSK",
        M=M,
        VA=VA,
        T=Ts,
        eps_ch=e,
        ZM=ZM,
        A=A,
        B_inner=B_inner,
        B=B,
        sqB=sqB,
        chi_tot=chi_tot,
        Ah=Ah,
        Dh=Dh,
        l1=l1,
        l2=l2,
        l3=l3,
        l4=l4,
        S_BE=S_BE,
    )
    return S_BE


def skr_psk(VA, T, eps, M, beta):
    """
    Secret Key Rate for PSK-modulated Homodyne Detection
    SKR = β·I_AB - S_BE

    Args:
        VA: Modulation variance
        T: Transmission coefficient
        eps: Channel excess noise
        M: PSK modulation order (2, 4, 8, 16, ...)
        beta: Reconciliation efficiency

    Returns:
        SKR in bits/pulse
    """
    Ts = max(float(T), 1e-300)
    chi_t = _chi_t_hom(Ts, eps)
    I_AB = _IAB_hom(VA, chi_t)
    S_BE = _holevo_psk_hom(VA, Ts, eps, M)
    skr = beta * I_AB - S_BE
    _log_calc(
        "skr_psk",
        protocol="PSK",
        M=M,
        VA=VA,
        T=Ts,
        eps_ch=eps,
        beta=beta,
        chi_t=chi_t,
        I_AB=I_AB,
        S_BE=S_BE,
        SKR=skr,
    )
    return skr
