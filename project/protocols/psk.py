import numpy as np

from ..utils.logger import _log_calc
from .gm import _G, _IAB_hom, _chi_l, _chi_t_hom, _symp12
from ..config import CHI_HOM


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
    if M not in (2, 4, 8):
        raise ValueError("Only M=2,4,8 are supported.")
    if VA < 0:
        raise ValueError("VA must be non-negative.")
    if VA <= np.finfo(float).eps:
        return 0.0

    a2 = VA / 2.0
    z, imag_max = _psk_zeta_components(M, a2)
    if imag_max > 1e-10:
        raise ValueError(f"Unexpected complex zeta components for M={M}: imag_max={imag_max:.3e}")

    z_prev = np.roll(z, 1)
    terms = np.exp(1.5 * np.log(z_prev) - 0.5 * np.log(z))
    prefactor = a2 if M == 2 else 2.0 * a2
    zm = float(prefactor * np.sum(terms))
    _log_calc(
        "ZM_psk",
        protocol="PSK",
        M=M,
        VA=VA,
        a2=a2,
        prefactor=prefactor,
        zeta_min=np.min(z),
        zeta_max=np.max(z),
        zeta_imag_max=imag_max,
        terms_sum=np.sum(terms),
        ZM=zm,
    )
    return zm


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
