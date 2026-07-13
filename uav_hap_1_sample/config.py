from dataclasses import dataclass
from typing import Optional

import numpy as np

EPS = 1e-15
LAMBDA = 1550e-9


def qam_alpha0_mb_for_va(va_target: float, nu_tilde: float) -> float:
    ks = np.arange(16, dtype=float)
    weights = np.exp(-float(nu_tilde) * (ks - 7.5) ** 2)
    denom = float(weights.sum())
    if denom <= 0.0:
        raise ValueError("Invalid nu_tilde leading to non-positive normalization.")
    moment = float(np.sum((ks - 7.5) ** 2 * weights) / denom)
    if moment <= 0.0:
        raise ValueError("Invalid moment for MB alpha0 computation.")
    return float(np.sqrt(15.0 * float(va_target) / moment))

# QAM defaults (aligned with uav_hap/qam_count scripts)
# Note: Ncut tuned for convergence in w, VA, TrC
QAM_M = 256
QAM_NCUT_BINOMIAL = 45
QAM_NCUT_UNIFORM = 150
QAM_NCUT_MB = 150
QAM_ALPHA0_BINOMIAL = 2
QAM_ALPHA0_UNIFORM = np.sqrt(12 / 17)
QAM_NU_TILDE = 0.1
QAM_ALPHA0_MB = 1.735
QAM_BETA = 0.95
QAM_EPS = 0.001
QAM_ETA = 0.95
QAM_V_EL = 0.001


def kruse_q_parameter(visibility_km: float) -> float:
    v = float(visibility_km)
    if v > 50.0:
        return 1.6
    if 6.0 < v <= 50.0:
        return 1.3
    return 0.585 * max(v, EPS) ** (1.0 / 3.0)


def kruse_xi_per_km(visibility_km: float, wavelength_m: float) -> float:
    v = max(float(visibility_km), EPS)
    lambda_nm = max(float(wavelength_m), EPS) * 1e9
    q_v = kruse_q_parameter(v)
    return float((3.912 / v) * (lambda_nm / 550.0) ** (-q_v))


def Cn2_HV(h_m: float, w_wind: float = 21.0, Cn2_0: float = 1.7e-14) -> float:
    h = max(float(h_m), 0.0)
    return float(
        0.00594 * (float(w_wind) / 27.0) ** 2 * (1e-5 * h) ** 10 * np.exp(-h / 1000.0)
        + 2.7e-16 * np.exp(-h / 1500.0)
        + float(Cn2_0) * np.exp(-h / 100.0)
    )


@dataclass(frozen=True)
class GeometryParams:
    H_UAV_m: float = 0.0
    H_HAP_m: float = 20_000.0
    tilt_deg: float = 0.0
    d_h_m: float = 0.0
    zeta_rad: Optional[float] = None


@dataclass(frozen=True)
class ChannelParams:
    wavelength_m: float = LAMBDA
    W0_m: float = 0.0626
    a_m: float = 0.20
    visibility_km: float = 10.0
    xi_per_km: Optional[float] = None
    Cn2: float = 1e-15
    use_hv_turbulence: bool = False
    w_wind: float = 21.0
    Cn2_0: float = 1.7e-14

    sigma_x_m: float = 0.0521
    sigma_y_m: float = 0.0502
    sigma_z_m: float = 0.0703
    sigma_theta_rad: float = 2.6e-3
    sigma_phi_rad: float = 2.04e-3
    sigma_psi_rad: float = 4.06e-3

    sigma_turb_m: Optional[float] = None
    sigma_UAV_m: Optional[float] = None
    sigma_r_m: Optional[float] = None
    rice_nu_m: float = 0.0

    eta_SMF: float = 1.0
    T_T: float = 1.0
    T_R: float = 1.0

    # Legacy fields retained for compatibility with channel model.
    alpha_db_per_km: float = 0.4
    D_r_m: Optional[float] = None
    theta_div_rad: float = 120e-6
    R_m: Optional[float] = None
    gamma: Optional[float] = None
