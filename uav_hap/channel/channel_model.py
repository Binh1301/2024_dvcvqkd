import numpy as np
from scipy.integrate import quad
from scipy.special import i0, i1

from ..config import Cn2_HV, ChannelParams, EPS, GeometryParams, kruse_xi_per_km

N_SAMPLES_MONTE_CARLO = 30_000


def link_distance_m(geometry: GeometryParams) -> float:
    delta_h = float(geometry.H_HAP_m) - float(geometry.H_UAV_m)
    d_h_m = max(float(geometry.d_h_m), 0.0)
    if d_h_m > 0.0:
        return float(np.sqrt(d_h_m**2 + delta_h**2))
    tilt_rad = np.deg2rad(float(geometry.tilt_deg))
    return float(delta_h / np.cos(tilt_rad))


def _zenith_angle_rad(geometry: GeometryParams, L_m: float) -> float:
    if geometry.zeta_rad is not None:
        return float(geometry.zeta_rad)
    delta_h = float(geometry.H_HAP_m) - float(geometry.H_UAV_m)
    return float(np.arccos(np.clip(delta_h / max(float(L_m), EPS), -1.0, 1.0)))


def _aperture_radius_m(channel_params: ChannelParams) -> float:
    if channel_params.D_r_m is not None:
        return max(0.5 * float(channel_params.D_r_m), EPS)
    return max(float(channel_params.a_m), EPS)


def _eta_atm_fixed(channel_params: ChannelParams, L_m: float) -> tuple[float, float]:
    xi_per_km = kruse_xi_per_km(
        visibility_km=float(channel_params.visibility_km),
        wavelength_m=float(channel_params.wavelength_m),
    )
    eta_atm = float(np.exp(-xi_per_km * (float(L_m) / 1000.0)))
    return eta_atm, float(xi_per_km)


def _beam_radius_at_receiver(W0_m: float, wavelength_m: float, L_m: float) -> tuple[float, float]:
    z_r = np.pi * float(W0_m) ** 2 / max(float(wavelength_m), EPS)
    w_l = float(W0_m) * np.sqrt(1.0 + (float(L_m) / max(z_r, EPS)) ** 2)
    return float(w_l), float(z_r)


def _shape_parameters(a_m: float, W_L_m: float) -> dict:
    a = max(float(a_m), EPS)
    w_l = max(float(W_L_m), EPS)
    x = (2.0 * a / w_l) ** 2
    t0_amp = float(np.sqrt(max(1.0 - np.exp(-2.0 * a**2 / w_l**2), EPS)))
    exp_x = float(np.exp(-x))
    denom = max(1.0 - exp_x * float(i0(x)), EPS)
    log_arg = (2.0 * t0_amp**2) / denom
    log_term = float(np.log(log_arg))
    gamma_num = 2.0 * x * exp_x * float(i1(x))
    gamma = max(float(gamma_num / (denom * log_term)), EPS)
    r_m = float(a * np.power(log_term, -1.0 / gamma))
    return {
        "x": float(x),
        "T0_amp": t0_amp,
        "T0_power": float(t0_amp**2),
        "Gamma": gamma,
        "R_m": max(r_m, EPS),
    }


def _sigma2_uav(channel_params: ChannelParams, L_m: float) -> float:
    if channel_params.sigma_UAV_m is not None:
        return max(float(channel_params.sigma_UAV_m), 0.0) ** 2
    sigma2_pos = (float(channel_params.sigma_x_m) ** 2 +
                  float(channel_params.sigma_y_m) ** 2)
    sigma2_orient = (float(channel_params.sigma_theta_rad) ** 2 +
                     float(channel_params.sigma_phi_rad) ** 2 +
                     float(channel_params.sigma_psi_rad) ** 2)
    return float(sigma2_pos + float(L_m) ** 2 * sigma2_orient)


def _sigma2_turb(channel_params: ChannelParams, geometry: GeometryParams, L_m: float, zeta_rad: float) -> float:
    if channel_params.sigma_turb_m is not None:
        return max(float(channel_params.sigma_turb_m), 0.0) ** 2
    W0 = max(float(channel_params.W0_m), EPS)
    if not channel_params.use_hv_turbulence:
        return float(1.919 * float(channel_params.Cn2) * float(L_m) ** 3 * (2.0 * W0) ** (-1.0 / 3.0))
    cos_zeta = max(float(np.cos(float(zeta_rad))), np.sqrt(EPS))
    def integrand(h_m: float) -> float:
        return Cn2_HV(h_m, w_wind=channel_params.w_wind, Cn2_0=channel_params.Cn2_0) * (h_m - float(geometry.H_UAV_m)) ** 3
    integral, _ = quad(integrand, float(geometry.H_UAV_m), float(geometry.H_HAP_m), limit=200)
    return float(max(1.919 * (2.0 * W0) ** (-1.0 / 3.0) * integral / (cos_zeta ** 4), 0.0))


def channel(geometry: GeometryParams, channel_params: ChannelParams, N: int,
            rng=None, L_override_m=None) -> dict:
    generator = np.random.default_rng() if rng is None else rng
    L_m = float(L_override_m) if L_override_m is not None else link_distance_m(geometry)
    zeta_rad = _zenith_angle_rad(geometry, L_m)
    eta_atm, xi_per_km = _eta_atm_fixed(channel_params, L_m)
    a_m = _aperture_radius_m(channel_params)
    W_L_m, z_R_m = _beam_radius_at_receiver(channel_params.W0_m, channel_params.wavelength_m, L_m)
    shape = _shape_parameters(a_m, W_L_m)
    sigma2_uav = _sigma2_uav(channel_params, L_m)
    sigma2_turb = _sigma2_turb(channel_params, geometry, L_m, zeta_rad)
    sigma2_r = float(max(sigma2_turb + sigma2_uav, 0.0))
    sigma_r = float(np.sqrt(max(sigma2_r, 0.0)))
    sigma_s = float(np.sqrt(max(sigma2_r / 2.0, 0.0)))
    r_samples = generator.rayleigh(scale=sigma_s, size=int(N)) if sigma_s > EPS else np.zeros(int(N))
    exponent = np.power(np.maximum(r_samples, 0.0) / shape["R_m"], shape["Gamma"])
    T_field_samples = shape["T0_amp"] * np.sqrt(np.exp(-exponent))
    eta_point = np.clip(T_field_samples, 0.0, 1.0)
    eta_fixed = float(np.clip(eta_atm * channel_params.eta_SMF * channel_params.T_T * channel_params.T_R, 0.0, 1.0))
    T_samples = np.clip(eta_fixed * eta_point, 0.0, 1.0)
    return {
        "L_m": L_m,
        "L_km": L_m / 1000.0,
        "zeta_rad": zeta_rad,
        "r_samples": r_samples,
        "T_field_samples": T_field_samples,
        "eta_point_samples": eta_point,
        "T_samples": T_samples,
        "T_eff": float(np.mean(T_samples)),
        "sigma2_UAV_m2": sigma2_uav,
        "sigma2_turb_m2": sigma2_turb,
        "sigma2_r_m2": sigma2_r,
        "sigma_r_m": sigma_r,
        "eta_atm": eta_atm,
        "xi_per_km": xi_per_km,
        "eta_geo": shape["T0_power"],
        "eta_SMF": float(channel_params.eta_SMF),
        "eta_sys": float(channel_params.T_T * channel_params.T_R),
        "eta_fixed": eta_fixed,
        "aperture_radius_m": a_m,
        "W_L_m": W_L_m,
        "z_R_m": z_R_m,
        "x": shape["x"],
        "T0": shape["T0_power"],
        "T0_amp": shape["T0_amp"],
        "T0_power": shape["T0_power"],
        "Gamma": shape["Gamma"],
        "R_m": shape["R_m"],
    }


def sample_total_transmittance(params: ChannelParams, n_samples: int, rng=None) -> dict:
    out = channel(GeometryParams(), params, int(n_samples), rng)
    return {
        "T_samples": out["T_samples"],
        "r_samples": out["r_samples"],
        "T_eff": out["T_eff"],
        "eta_atm": out["eta_atm"],
        "eta_geo": out["eta_geo"],
        "eta_smf": out["eta_SMF"],
        "eta_sys": out["eta_sys"],
        "Gamma": out["Gamma"],
        "R_m": out["R_m"],
        "W_L_m": out["W_L_m"],
    }


def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=0.0):
    zeta = np.deg2rad(max(90.0 - float(theta_deg), 0.0))
    delta_h = float(H_zen) - float(H_ogs)
    d_h = max(delta_h * np.tan(zeta), 0.0)
    geom = GeometryParams(H_UAV_m=float(H_ogs), H_HAP_m=float(H_zen), d_h_m=d_h, zeta_rad=zeta)
    ch = ChannelParams(D_r_m=float(Dr), visibility_km=float(V_km), Cn2=float(Cn2), sigma_r_m=0.0)
    out = channel(geom, ch, N_SAMPLES_MONTE_CARLO)
    return float(out["T_eff"]), float(out["L_m"]), True
