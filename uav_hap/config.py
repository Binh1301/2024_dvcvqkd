from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

EPS = 1e-15
LAMBDA = 1550e-9
MATPLOTLIB_BACKEND = "TkAgg"

# CV-QKD default noise model (phase-noise term removed from channel excess noise).
EPS_BG = 0.0002
EPS_RIN = 0.0001
EPS_MOD = 0.0005
EPS_CH = EPS_BG + EPS_RIN + EPS_MOD  # 0.0008
EPS_DET = 0.013
V_ELE = 0.10
ETA = 0.5
CHI_HOM = (1.0 - ETA + EPS_DET) / ETA
CHI_HET = (1.0 + (1.0 - ETA) + 2.0 * EPS_DET) / ETA

# Default modulation variances used by legacy plotting modules.
VA_GM = 2.6
VA_PSK = 2.6
VA_QAM = 2.6

# Legacy constants still imported by utilities/plots.
CALC_LOG_XLSX = "cvqkd_calculation_log.xlsx"
H_OGS_ISS = 1_029.0
ELEVS = [90, 60, 30]
LS = ["-", "--", "-."]

N_FOCK = 32
QAM_V_DISC_GAUSS = 0.5


def db_per_km_to_neper_per_m(alpha_db_per_km: float) -> float:
    return float(alpha_db_per_km) * np.log(10.0) / (10.0 * 1000.0)


def kruse_q_parameter(visibility_km: float) -> float:
    v = float(visibility_km)
    if v > 50.0:
        return 1.6
    if v > 6.0:
        return 1.3
    return 0.585 * np.cbrt(max(v, EPS))


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
    H_UAV_m: float = 1_000.0
    H_HAP_m: float = 20_000.0
    tilt_deg: float = 0.0
    d_h_m: float = 0.0
    zeta_rad: Optional[float] = None


@dataclass(frozen=True)
class ChannelParams:
    wavelength_m: float = LAMBDA
    W0_m: float = 0.0157
    a_m: float = 0.075
    visibility_km: float = 10.0
    # User-requested fixed attenuation coefficient (km^-1).
    xi_per_km: float = 0.391260
    Cn2: float = 1e-16
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

    eta_SMF: float = 1.0
    T_T: float = 1.0
    T_R: float = 1.0

    # Legacy fields retained for backward compatibility.
    alpha_db_per_km: float = 0.4
    D_r_m: Optional[float] = None
    theta_div_rad: float = 120e-6
    R_m: Optional[float] = None
    gamma: Optional[float] = None


@dataclass(frozen=True)
class NoiseParams:
    epsilon_bg: float = EPS_BG
    epsilon_RIN: float = EPS_RIN
    epsilon_mod: float = EPS_MOD
    epsilon_toa: float = 0.0
    include_epsilon_toa_as_intensity: bool = False
    epsilon_det: float = EPS_DET
    detection: Literal["hom", "het"] = "hom"
    eta_d: float = ETA
    v_el: float = V_ELE
    chi_hom: Optional[float] = None
    chi_het: Optional[float] = None

    # Legacy parameters retained to keep existing callers compatible.
    xi_ch: Optional[float] = None
    xi_det: Optional[float] = None
    xi_phase: float = 0.0


@dataclass(frozen=True)
class SecurityParams:
    VA: float = VA_GM
    beta: float = 0.95
    optimize_VA: bool = False
    VA_min: float = 0.1
    VA_max: float = 10.0
    VA_points: int = 200


@dataclass(frozen=True)
class MonteCarloParams:
    N: int = 200_000
    seed: Optional[int] = 42


@dataclass(frozen=True)
class FiniteSizeParams:
    N_block: int = 100_000_000
    n_ratio: float = 0.8
    epsilon_PE: float = 1e-8
    epsilon_EC: float = 1e-8
    epsilon_PA: float = 1e-8
    # Legacy finite-size placeholders for compatibility with older code paths.
    n: Optional[int] = None
    delta_c: float = 5.0
