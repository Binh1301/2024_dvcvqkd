from typing import Optional

import numpy as np
from scipy.integrate import quad
from scipy.special import i0, i1

from ..config import Cn2_HV, ChannelParams, EPS, GeometryParams


def link_distance_m(geometry: GeometryParams) -> float:
    """
    FLOW: Compute slant link distance UAV → HAP
    ─────────────────────────────────────────────
    INPUT:  geometry.H_HAP_m  [m]  — HAP altitude
            geometry.H_UAV_m  [m]  — UAV altitude
            geometry.d_h_m    [m]  — horizontal separation
            geometry.tilt_deg [°]  — beam tilt angle
    ─────────────────────────────────────────────
    STEP 1: delta_h = H_HAP - H_UAV          [m]
    STEP 2a (if d_h > 0):
            L = sqrt(d_h^2 + delta_h^2)      [m]
    STEP 2b (if d_h = 0):
            L = delta_h / cos(tilt_deg)      [m]
    ─────────────────────────────────────────────
    OUTPUT: L_link [m]
    """
    # ── STEP 1: Vertical separation ──────────────────────────────
    # Physics: height difference between HAP and UAV.
    # Formula: delta_h = H_HAP - H_UAV
    # Unit:    input [m], output [m]
    # Ref:     Standard slant-range geometry in FSO link modeling.
    delta_h = float(geometry.H_HAP_m) - float(geometry.H_UAV_m)
    # ── STEP 1.1: Physical feasibility check ─────────────────────
    # Physics: HAP must be above UAV for an upward UAV→HAP path.
    # Formula: valid if delta_h > 0
    # Unit:    meters
    # Ref:     Basic geometric constraint for line-of-sight links.
    if delta_h <= 0.0:
        raise ValueError("H_HAP_m must be greater than H_UAV_m.")

    # ── STEP 2: Horizontal separation magnitude ──────────────────
    # Physics: non-negative horizontal projection of the link.
    # Formula: d_h = max(d_h_m, 0)
    # Unit:    meters
    # Ref:     2D Cartesian decomposition of slant path.
    d_h_m = max(float(geometry.d_h_m), 0.0)
    # ── STEP 2a: Slant distance with horizontal offset ───────────
    # Physics: Pythagorean slant path when UAV is not directly below HAP.
    # Formula: L = sqrt(d_h^2 + delta_h^2)
    # Unit:    meters
    # Ref:     Euclidean distance in right-triangle geometry.
    if d_h_m > 0.0:
        return float(np.sqrt(d_h_m**2 + delta_h**2))

    # ── STEP 2b: Slant distance from zenith angle ────────────────
    # Physics: slant range from vertical separation and beam tilt.
    # Formula: tilt_rad = deg2rad(tilt_deg), L = delta_h / cos(tilt_rad)
    # Unit:    input [deg], intermediate [rad], output [m]
    # Ref:     Standard trigonometric slant-path relation.
    tilt_rad = np.deg2rad(float(geometry.tilt_deg))
    # ── STEP 2b.1: Cosine projection factor ──────────────────────
    # Physics: vertical-to-slant projection coefficient.
    # Formula: cos_tilt = cos(tilt_rad)
    # Unit:    dimensionless
    # Ref:     Trigonometric projection law.
    cos_tilt = np.cos(tilt_rad)
    # ── STEP 2b.2: Valid angular domain check ────────────────────
    # Physics: cos(tilt) must be positive to avoid non-physical/infinite range.
    # Formula: valid if cos_tilt > 0
    # Unit:    dimensionless
    # Ref:     Domain constraint for L = delta_h / cos(tilt).
    if cos_tilt <= 0.0:
        raise ValueError("tilt_deg must satisfy cos(tilt_deg) > 0.")
    return float(delta_h / cos_tilt)


def _zenith_angle_rad(geometry: GeometryParams, L_m: float) -> float: ## oke
    if geometry.zeta_rad is not None:
        return float(geometry.zeta_rad)
    delta_h = float(geometry.H_HAP_m) - float(geometry.H_UAV_m)
    ratio = np.clip(delta_h / max(float(L_m), EPS), -1.0, 1.0)
    return 0


def _aperture_radius_m(channel_params: ChannelParams) -> float:
    if channel_params.D_r_m is not None:
        return max(0.5 * float(channel_params.D_r_m), EPS)
    return max(float(channel_params.a_m), EPS)


def _eta_atm_fixed(xi_per_km: float, L_m: float) -> tuple[float, float]:
    xi_per_km = max(float(xi_per_km), 0.0)
    eta_atm = float(np.exp(-xi_per_km * (float(L_m) / 1000.0)))
    return eta_atm, xi_per_km


def _beam_radius_at_receiver(W0_m: float, wavelength_m: float, L_m: float) -> tuple[float, float]:
    """
    FLOW: Gaussian beam propagation — radius at distance L
    ────────────────────────────────────────────────────────
    INPUT:  W0_m         [m]  — beam waist at transmitter
            wavelength_m [m]  — optical wavelength
            L_m          [m]  — propagation distance
    ────────────────────────────────────────────────────────
    STEP 1: z_R = pi * W0^2 / lambda        Rayleigh range [m]
    STEP 2: W_L = W0 * sqrt(1 + (L/z_R)^2) beam radius at HAP [m]
    ────────────────────────────────────────────────────────
    NOTE:   At L >> z_R (far field, L~20km >> z_R~500m):
            W_L ≈ lambda * L / (pi * W0) ≈ 0.63 m
            → geometric loss is DOMINANT
    OUTPUT: (W_L [m], z_R [m])
    """
    # ── STEP 1: Rayleigh range ───────────────────────────────────
    # Physics: distance at which Gaussian-beam area doubles from diffraction.
    # Formula: z_R = pi * W0^2 / lambda
    # Unit:    input [m], output [m]
    # Ref:     Siegman, Lasers; Gaussian beam optics.
    z_r = np.pi * float(W0_m) ** 2 / max(float(wavelength_m), EPS)
    # ── STEP 2: Beam radius at receiver plane ────────────────────
    # Physics: Gaussian-beam spreading after propagation distance L.
    # Formula: W_L = W0 * sqrt(1 + (L/z_R)^2)
    # Unit:    input [m], output [m]
    # Ref:     Standard Gaussian beam propagation law.
    w_l = float(W0_m) * np.sqrt(1.0 + (float(L_m) / max(z_r, EPS)) ** 2)
    return float(w_l), float(z_r)


def _shape_parameters(a_m: float, W_L_m: float) -> dict:
    a = max(float(a_m), EPS)
    w_l = max(float(W_L_m), EPS)
    x = (2.0 * a / w_l) ** 2

    t0_amp = float(np.sqrt(max(1.0 - np.exp(-2.0 * a**2 / w_l**2), EPS)))
    i0_x = float(i0(x))
    i1_x = float(i1(x))
    exp_x = float(np.exp(-x))

    denom = max(1.0 - exp_x * i0_x, EPS)
    log_arg = max((2.0 * t0_amp**2) / denom, 1.0 + 1e-12)
    log_term = float(np.log(log_arg))

    gamma_num = 8.0 * (x / 4.0) * exp_x * i1_x
    gamma_den = max(denom * log_term, EPS)
    gamma = max(float(gamma_num / gamma_den), EPS)
    r_m = float(a * np.power(log_term, -1.0 / gamma))

    return {
        "x": float(x),
        "T0_amp": t0_amp,
        "T0_power": float(t0_amp**2),
        "I0": i0_x,
        "I1": i1_x,
        "Gamma": gamma,
        "R_m": max(r_m, EPS),
        "log_arg": log_arg,
    }


def _sigma2_uav(channel_params: ChannelParams, a_m: float, L_m: float) -> tuple[float, float, float]:
    if channel_params.sigma_UAV_m is not None:
        sigma2 = max(float(channel_params.sigma_UAV_m), 0.0) ** 2
        return sigma2, np.nan, np.nan

    sigma2_pos = (
        float(channel_params.sigma_x_m) ** 2
        + float(channel_params.sigma_y_m) ** 2
        + float(channel_params.sigma_z_m) ** 2
    )
    sigma2_orient = (
        float(channel_params.sigma_theta_rad) ** 2
        + float(channel_params.sigma_phi_rad) ** 2
        + float(channel_params.sigma_psi_rad) ** 2
    )
    sigma2_uav = sigma2_pos + float(a_m) ** 2 * sigma2_orient
    return float(sigma2_uav), float(sigma2_pos), float(sigma2_orient)


def _sigma2_turb(channel_params: ChannelParams, geometry: GeometryParams, L_m: float, zeta_rad: float) -> float:
    if channel_params.sigma_turb_m is not None:
        return max(float(channel_params.sigma_turb_m), 0.0) ** 2

    W0 = max(float(channel_params.W0_m), EPS)
    
    return float(1.919 * float(channel_params.Cn2) * float(L_m) ** 3 * (2.0 * W0) ** (-1.0 / 3.0))



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

    zeta_rad = _zenith_angle_rad(geometry, L_m)

    eta_atm, xi_per_km = _eta_atm_fixed(xi_per_km=channel_params.xi_per_km, L_m=L_m)
    a_m = _aperture_radius_m(channel_params)
    W_L_m, z_R_m = _beam_radius_at_receiver(
        W0_m=channel_params.W0_m,
        wavelength_m=channel_params.wavelength_m,
        L_m=L_m,
    )
    shape = _shape_parameters(a_m=a_m, W_L_m=W_L_m)

    sigma2_uav, sigma2_pos, sigma2_orient = _sigma2_uav(channel_params, a_m=a_m, L_m=L_m)
    sigma2_turb = _sigma2_turb(channel_params, geometry=geometry, L_m=L_m, zeta_rad=zeta_rad)
    sigma2_model = float(max(sigma2_uav + sigma2_turb, 0.0))

    sigma2_r = (
        max(float(channel_params.sigma_r_m), 0.0) ** 2
        if channel_params.sigma_r_m is not None
        else sigma2_model
    )
    sigma_r = float(np.sqrt(max(sigma2_r, 0.0)))
    sigma_s = float(np.sqrt(max(sigma2_r, 0.0) / 2.0))

    if sigma_s <= EPS:
        r_samples = np.zeros(int(N), dtype=float)
    else:
        # Rice sampling (non-zero LOS component) with K = nu^2 / (2*sigma_s^2).
        k_rice = max(float(channel_params.rice_K), 0.0)
        nu = np.sqrt(2.0 * k_rice) * sigma_s
        x_los = generator.normal(loc=nu, scale=sigma_s, size=int(N))
        y_nlos = generator.normal(loc=0.0, scale=sigma_s, size=int(N))
        r_samples = np.sqrt(x_los**2 + y_nlos**2)

    exponent = np.power(np.maximum(r_samples, 0.0) / max(shape["R_m"], EPS), shape["Gamma"])
    T_field_samples = shape["T0_amp"] * np.sqrt(np.exp(-exponent))
    eta_point = np.clip(T_field_samples**2, 0.0, 1.0)

    eta_smf = float(channel_params.eta_SMF)
    eta_sys = float(channel_params.T_T) * float(channel_params.T_R)
    eta_fixed = float(np.clip(eta_atm * eta_smf * eta_sys, 0.0, 1.0))

    T_samples = np.clip(eta_fixed * eta_point, EPS, 1.0)
    assert np.all(T_samples <= 1.0 + 1e-9), \
        f"T_samples exceeds 1: max={T_samples.max()}"
    assert np.all(T_samples >= 0.0), \
        "T_samples contains negative values"
    T_eff = float(np.mean(T_samples))
    return {
        "L_m": L_m,
        "L_km": L_m / 1000.0,
        "zeta_rad": zeta_rad,
        "r_samples": r_samples,
        "T_field_samples": T_field_samples,
        "eta_point_samples": eta_point,
        "T_samples": T_samples,
        "T_eff": T_eff,
        "sigma2_pos_m2": sigma2_pos,
        "sigma2_orient_rad2": sigma2_orient,
        "sigma2_UAV_m2": sigma2_uav,
        "sigma2_turb_m2": sigma2_turb,
        "sigma2_r_m2": sigma2_r,
        "sigma_r_m": sigma_r,
        "eta_atm": eta_atm,
        "xi_per_km": xi_per_km,
        "eta_geo": shape["T0_power"],
        "eta_SMF": eta_smf,
        "eta_sys": eta_sys,
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
        "log_arg": shape["log_arg"],
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
        "T_eff": out["T_eff"],
        "eta_atm": out["eta_atm"],
        "eta_geo": out["eta_geo"],
        "eta_smf": out["eta_SMF"],
        "eta_sys": out["eta_sys"],
        "eta_fixed": out["eta_fixed"],
        "T0": out["T0"],
        "T0_amp": out["T0_amp"],
        "T0_power": out["T0_power"],
        "Gamma": out["Gamma"],
        "R_m": out["R_m"],
        "W_L_m": out["W_L_m"],
        "sigma_r_m": out["sigma_r_m"],
        "sigma2_r_m2": out["sigma2_r_m2"],
    }


def total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2, H_ogs=0.0):
    zeta = np.deg2rad(max(90.0 - float(theta_deg), 0.0))
    delta_h = float(H_zen) - float(H_ogs)
    d_h = max(delta_h * np.tan(zeta), 0.0)
    base_geometry = GeometryParams(
        H_UAV_m=float(H_ogs),
        H_HAP_m=float(H_zen),
        d_h_m=float(d_h),
        zeta_rad=float(zeta),
    )
    base_channel = ChannelParams(
        D_r_m=float(Dr),
        visibility_km=float(V_km),
        Cn2=float(Cn2),
    )
    out = channel(geometry=base_geometry, channel_params=base_channel, N=1)
    return float(out["T_eff"]), float(out["L_m"]), True
