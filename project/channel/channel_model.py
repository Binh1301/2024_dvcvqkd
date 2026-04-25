import numpy as np
from scipy.special import erfinv

from ..config import (
    DB_PER_NEPER,
    DT,
    H_OGS_DEF,
    LAMBDA,
    LATM,
    LP,
    P_THR,
    RE,
    RYTOV_INT_COEFF,
    RYTOV_PREFAC,
    SCINT_T1_COEFF,
    SCINT_T1_D_COEFF,
    SCINT_T2_COEFF,
    SCINT_T2_D_COEFF,
    SCINT_T2_S_COEFF,
    TR,
    TT,
)
from ..utils.logger import _log_calc


def link_geometry(theta_deg, H_zen, H_ogs=H_OGS_DEF, H_atm=LATM):  # # oke
    """Total link distance and effective atmosphere thickness (Eq. 28)."""
    th = np.radians(theta_deg)
    r1 = RE + H_ogs
    r_sat = RE + H_zen
    r_atm = RE + H_atm

    # Ray-sphere intersection for elevation angle th:
    # L = -r1*sin(th) + sqrt(r2^2 - r1^2*cos(th)^2)
    c2 = np.cos(th) ** 2
    # #alpha_1 = np.arcsin(np.cos(th) * r1 / r_sat) + 90 - theta_deg;
    # #alpha_2 = np.arcsin(np.cos(th) * r1 / r_atm) + 90 - theta_deg;
    # #L_tot = r_sat ** 2 + r1 ** 2 - 2 * r1 * r_sat * np.cos(alpha_1) ** 1/2
    # #L_atm = r_atm ** 2 + r1 ** 2 - 2 * r1 * r_atm * np.cos(alpha_2) ** 1/2
    L_tot = -r1 * np.sin(th) + np.sqrt(max(r_sat**2 - r1**2 * c2, 0.0))
    L_atm = -r1 * np.sin(th) + np.sqrt(max(r_atm**2 - r1**2 * c2, 0.0))
    return float(L_tot), float(L_atm)


def geometric_loss_dB(L_tot, Dr):  # # oke
    """Free-space diffraction + hardware loss (Eq. 29)."""
    return 10 * np.log10(L_tot**2 * LAMBDA**2 / (DT**2 * Dr**2 * TT * (1 - LP) * TR))


def scattering_loss_dBpkm(V_km):  # #oke
    """Mie scattering loss [dB/km], Kruse-Kim model (Eq. 30)."""
    if V_km >= 50:
        p = 1.6
    elif V_km >= 6:
        p = 1.3
    elif V_km >= 1:
        p = 0.16 * V_km + 0.34
    elif V_km >= 0.5:
        p = V_km - 0.5
    else:
        p = 0.0
    return DB_PER_NEPER * (3.912 / V_km) * (1550 / 550) ** (-p)


def _cn2_weighted_integral(Cn2, L_atm, integration_points=1024):
    """
    Compute ∫ Cn2(z) * (L_atm - z)^(5/6) dz in Eq. (32).

    Supported Cn2 inputs:
    - scalar (constant Cn2 along path; uses analytic integral),
    - callable f(z_array) returning a same-shape profile.
    """
    if np.isscalar(Cn2):
        cn2 = float(Cn2)
        if cn2 < 0:
            raise ValueError("Cn2 must be non-negative.")
        return cn2 * (L_atm ** (11.0 / 6.0)) * RYTOV_INT_COEFF

    if callable(Cn2):
        z = np.linspace(0.0, L_atm, int(integration_points) + 1)
        cn2_profile = np.asarray(Cn2(z), dtype=float)
        if cn2_profile.shape != z.shape:
            raise ValueError("Cn2(z) must return an array with the same shape as z.")
        if np.any(cn2_profile < 0):
            raise ValueError("Cn2(z) must be non-negative along the path.")
        weight = np.power(np.maximum(L_atm - z, 0.0), 5.0 / 6.0)
        return float(np.trapz(cn2_profile * weight, z))

    raise TypeError("Cn2 must be a non-negative scalar or a callable Cn2(z).")


def scintillation_index(Cn2, Dr, L_atm):
    """
    Aperture-averaged scintillation index (Eq. 32).
    """
    if L_atm <= 0:
        return 0.0
    if Dr <= 0:
        raise ValueError("Dr must be positive.")

    k = 2 * np.pi / LAMBDA
    d = Dr * np.sqrt(np.pi / (2 * LAMBDA * L_atm))

    cn2_int = _cn2_weighted_integral(Cn2, float(L_atm))
    s2R = RYTOV_PREFAC * (k ** (7.0 / 6.0)) * cn2_int
    s2R_pow = s2R ** (6.0 / 5.0)

    t1_num = SCINT_T1_COEFF * s2R
    t1_den = (1 + SCINT_T1_D_COEFF * (d**2) + SCINT_T1_COEFF * s2R_pow) ** (7.0 / 6.0)
    t1 = t1_num / t1_den

    t2_num = SCINT_T2_COEFF * s2R * (1 + SCINT_T2_S_COEFF * s2R_pow) ** (-5.0 / 6.0)
    t2_den = 1 + SCINT_T2_D_COEFF * (d**2) + SCINT_T2_COEFF * (d**2) * s2R_pow
    t2 = t2_num / t2_den

    s2I = np.exp(t1 + t2) - 1.0
    return float(s2I)


def scintillation_loss_dB(s2I, p_thr=P_THR):
    """
    Scintillation loss with aperture averaging in dB (Eq. 31).
    """
    # Tránh giá trị s2I quá nhỏ gây lỗi log(1)
    if s2I <= 0:
        return 0.0

    # Tính toán thành phần ln(s2I + 1)
    ln_term = np.log(s2I + 1)

    # Đối số cho hàm erfinv
    arg = float(np.clip(2 * p_thr - 1, -0.9999, 0.9999))

    # Eq. (31): dB conversion factor is 10*log10(e) (≈4.343)
    A_sci = DB_PER_NEPER * (erfinv(arg) * np.sqrt(2 * ln_term) - 0.5 * ln_term)

    return A_sci if A_sci > 0 else 0


def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=H_OGS_DEF):
    """
    Total transmittance combining all losses (Eq. 33).
    Returns (T, L_tot [m], far_field_ok).
    """
    L_tot, L_atm = link_geometry(theta_deg, H_zen, H_ogs)
    ff_ok = L_tot >= Dr * DT / LAMBDA

    A_geo = geometric_loss_dB(L_tot, Dr)
    A_scat = scattering_loss_dBpkm(V_km) * (L_atm / 1e3)
    A_sci = scintillation_loss_dB(scintillation_index(Cn2, Dr, L_atm))

    T = float(np.clip(10 ** (-(A_geo + A_scat + A_sci) / 10), 0, 1))
    _log_calc(
        "total_transmittance",
        theta_deg=theta_deg,
        H_zen_m=H_zen,
        H_ogs_m=H_ogs,
        Dr_m=Dr,
        V_km=V_km,
        Cn2=Cn2,
        L_tot_m=L_tot,
        L_atm_m=L_atm,
        far_field_ok=ff_ok,
        A_geo_dB=A_geo,
        A_scat_dB=A_scat,
        A_sci_dB=A_sci,
        T=T,
    )
    return T, L_tot, ff_ok
