from typing import Optional

import numpy as np

from ..config import ChannelParams, EPS, GeometryParams, db_per_km_to_neper_per_m


def link_distance_m(geometry: GeometryParams) -> float:
    delta_h = float(geometry.H_HAP_m) - float(geometry.H_UAV_m)
    if delta_h <= 0.0:
        raise ValueError("H_HAP_m must be greater than H_UAV_m.")

    tilt_rad = np.deg2rad(float(geometry.tilt_deg))
    cos_tilt = np.cos(tilt_rad)
    if cos_tilt <= 0.0:
        raise ValueError("tilt_deg must satisfy cos(tilt_deg) > 0.")
    return float(delta_h / cos_tilt)


def _sigma_r(channel_params: ChannelParams) -> float:
    if channel_params.sigma_r_m is not None:
        return max(float(channel_params.sigma_r_m), 0.0)
    sigma2 = float(channel_params.sigma_turb_m) ** 2 + float(channel_params.sigma_UAV_m) ** 2
    return float(np.sqrt(max(sigma2, 0.0)))


def _eta_atm(alpha_db_per_km: float, L_m: float) -> float:
    alpha_np_per_m = db_per_km_to_neper_per_m(alpha_db_per_km)
    return float(np.exp(-alpha_np_per_m * float(L_m)))


def _eta_geo(D_r_m: float, theta_div_rad: float, L_m: float) -> float:
    denom = max(float(theta_div_rad) * float(L_m), EPS)
    eta = (float(D_r_m) / denom) ** 2
    return float(np.clip(eta, 0.0, 1.0))


def channel(
    geometry: GeometryParams,
    channel_params: ChannelParams,
    N: int,
    rng: Optional[np.random.Generator] = None,
    L_override_m: Optional[float] = None,
) -> dict:
    if int(N) <= 0:
        raise ValueError("N must be positive.")

    generator = np.random.default_rng() if rng is None else rng
    L_m = float(L_override_m) if L_override_m is not None else link_distance_m(geometry)
    if L_m <= 0.0:
        raise ValueError("L must be positive.")

    sigma_r = _sigma_r(channel_params)
    if sigma_r <= EPS:
        r_samples = np.zeros(int(N), dtype=float)
    else:
        r_samples = generator.rayleigh(scale=sigma_r, size=int(N))

    eta_point = np.exp(-np.power(np.maximum(r_samples, 0.0) / max(float(channel_params.R_m), EPS), float(channel_params.gamma)))
    eta_atm = _eta_atm(channel_params.alpha_db_per_km, L_m)
    eta_geo = _eta_geo(channel_params.D_r_m, channel_params.theta_div_rad, L_m)
    eta_smf = float(channel_params.eta_SMF)
    eta_sys = float(channel_params.T_T) * float(channel_params.T_R)

    T_samples = np.clip(eta_atm * eta_geo * eta_point * eta_smf * eta_sys, EPS, 1.0)
    return {
        "L_m": L_m,
        "r_samples": r_samples,
        "T_samples": T_samples,
        "sigma_r_m": sigma_r,
        "eta_atm": eta_atm,
        "eta_geo": eta_geo,
        "eta_SMF": eta_smf,
        "eta_sys": eta_sys,
    }


def sample_total_transmittance(
    params: ChannelParams,
    n_samples: int,
    rng: Optional[np.random.Generator] = None,
) -> dict:
    geometry = GeometryParams()
    out = channel(geometry=geometry, channel_params=params, N=int(n_samples), rng=rng)
    return {
        "T_samples": out["T_samples"],
        "r_samples": out["r_samples"],
        "eta_atm": out["eta_atm"],
        "eta_geo": out["eta_geo"],
        "eta_smf": out["eta_SMF"],
        "eta_sys": out["eta_sys"],
        "eta_fixed": out["eta_atm"] * out["eta_geo"] * out["eta_SMF"] * out["eta_sys"],
        "sigma_r_m": out["sigma_r_m"],
    }


def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=0.0):
    del theta_deg, V_km, Cn2
    base_geometry = GeometryParams(H_UAV_m=float(H_ogs), H_HAP_m=float(H_zen))
    base_channel = ChannelParams(D_r_m=float(Dr), sigma_r_m=0.0)
    out = channel(geometry=base_geometry, channel_params=base_channel, N=1)
    return float(out["T_samples"][0]), float(out["L_m"]), True
