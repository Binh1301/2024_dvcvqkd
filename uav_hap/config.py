from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

EPS = 1e-15
LAMBDA = 1550e-9
MATPLOTLIB_BACKEND = "TkAgg"
EPS_CH = 0.0186
EPS_DET = 0.0135
ETA = 0.6
CHI_HOM = (1.0 - ETA + EPS_DET) / ETA
CHI_HET = (1.0 + (1.0 - ETA) + 2.0 * EPS_DET) / ETA
N_FOCK = 32
QAM_V_DISC_GAUSS = 0.5


def db_per_km_to_neper_per_m(alpha_db_per_km: float) -> float:
    return float(alpha_db_per_km) * np.log(10.0) / (10.0 * 1000.0)


@dataclass(frozen=True)
class GeometryParams:
    H_UAV_m: float = 1_000.0
    H_HAP_m: float = 20_000.0
    tilt_deg: float = 0.0


@dataclass(frozen=True)
class ChannelParams:
    alpha_db_per_km: float = 0.2
    D_r_m: float = 0.35
    theta_div_rad: float = 120e-6
    R_m: float = 0.04
    gamma: float = 2.0
    sigma_turb_m: float = 0.01
    sigma_UAV_m: float = 0.03
    sigma_r_m: Optional[float] = None
    eta_SMF: float = 0.5
    T_T: float = 0.9
    T_R: float = 0.9


@dataclass(frozen=True)
class NoiseParams:
    xi_ch: float = 0.0186
    xi_det: float = 0.0135
    xi_phase: float = 0.01
    detection: Literal["hom", "het"] = "hom"
    eta_d: float = 0.6
    v_el: float = 0.10
    chi_hom: Optional[float] = None
    chi_het: Optional[float] = None


@dataclass(frozen=True)
class SecurityParams:
    VA: float = 3.0
    beta: float = 0.90


@dataclass(frozen=True)
class MonteCarloParams:
    N: int = 200_000
    seed: Optional[int] = 42


@dataclass(frozen=True)
class FiniteSizeParams:
    n: int = 100_000_000
    delta_c: float = 5.0
