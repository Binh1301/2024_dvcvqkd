"""
UAV-to-HAP FSO channel model for GM-CVQKD.

This script keeps the Gaussian-modulated CV-QKD core and updates the channel to:
1) Atmospheric attenuation: eta_atm = exp(-alpha * L)
2) Pointing/beam fading: T(r) = T0 * exp(-(r/R)^Gamma), with Rice r
3) Geometric capture + SMF coupling + tracking/AO efficiencies

It also includes:
- chi_line, chi_D, chi_tot noise model
- phase-noise term from tau^2 ~= 2.46 * Cn2 * k^(7/6) * L^(11/6)
- fading Monte Carlo with <T>, T_eff, and log-domain statistic
- transmittance grouping (T ~ const per bin) and aggregated SKR/key
- SKR vs distance and SKR vs pointing jitter visualization
"""

from dataclasses import dataclass, replace
from typing import Optional
import math
import numpy as np
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


RE = 6_371_000.0
EPS = 1e-15


@dataclass(frozen=True)
class PlatformParams:
    # UAV-HAP geometry
    h_uav_m: float = 1_000.0       # 100-2000 m
    h_hap_m: float = 20_000.0      # 18-38 km
    theta_z_deg: float = 20.0      # zenith angle

    # UAV jitter model
    sigma_pos_m: float = 0.03      # position jitter std
    sigma_orient_rad: float = 5e-6 # orientation jitter std
    theta_pe_rad: float = 1e-6     # nominal pointing error


@dataclass(frozen=True)
class FSOParams:
    # Channel and atmosphere
    lambda_m: float = 1550e-9
    alpha_db_per_km: float = 0.4

    # Optical parameters
    w0_uav_m: float = 0.0157
    w0_hap_m: float = 0.10
    d_rx_hap_m: float = 0.35       # 30-40 cm diameter
    eta_smf: float = 0.80
    eta_tr: float = 0.85
    eta_ao: float = 0.80
    ao_delay_s: float = 2e-3
    ao_integration_s: float = 5e-4

    # Pointing-fading law
    T0: float = 0.98
    R_m: float = 0.04
    gamma: float = 2.0
    weibull_shape: float = 2.0

    # Hufnagel-Valley model parameters
    hv_A: float = 1.7e-14
    hv_wind_ms: float = 21.0

    # Excess-noise components
    xi_base: float = 0.0
    xi_turb_coeff: float = 1.0
    xi_uav_coeff: float = 1.0

    # Monte Carlo
    n_fading_samples: int = 20_000


@dataclass(frozen=True)
class GMParams:
    # Requested range is 2-4 SNU, keep default at midpoint.
    VA: float = 3.0
    beta: float = 0.9
    eta_d: float = 0.60
    v_el: float = 0.10

    # Finite-size
    N_block: float = 1e8
    f_rep: float = 50e6
    FER: float = 0.0
    d_disc: int = 5
    eps_s: float = 2e-10
    eps_sec: float = 1e-9
    n_groups: int = 10


def G(x: float) -> float:
    x = float(x)
    if x < 1e-12:
        return 0.0
    return (x + 1.0) * math.log2(x + 1.0) - x * math.log2(x)


def slant_range_uav_hap_km(platform: PlatformParams) -> float:
    """Earth-curvature slant range z from UAV to HAP for zenith angle theta_z."""
    h1 = float(platform.h_uav_m)
    h2 = float(platform.h_hap_m)
    if h2 <= h1:
        raise ValueError("h_hap_m must be larger than h_uav_m.")

    theta = math.radians(float(platform.theta_z_deg))
    r1 = RE + h1
    r2 = RE + h2
    radicand = max(r2 * r2 - (r1 * math.sin(theta)) ** 2, 0.0)
    z_m = -r1 * math.cos(theta) + math.sqrt(radicand)
    if z_m <= 0:
        raise ValueError("Computed slant range is non-positive. Check theta_z_deg.")
    return z_m / 1e3


def hv_cn2(h_m: np.ndarray, fso: FSOParams) -> np.ndarray:
    """Hufnagel-Valley Cn2(h) profile."""
    h = np.maximum(np.asarray(h_m, dtype=float), 0.0)
    v = float(fso.hv_wind_ms)
    A = float(fso.hv_A)
    term1 = 0.00594 * (v / 27.0) ** 2 * (1e-5 * h) ** 10 * np.exp(-h / 1000.0)
    term2 = 2.7e-16 * np.exp(-h / 1500.0)
    term3 = A * np.exp(-h / 100.0)
    return term1 + term2 + term3


def effective_cn2_hv(platform: PlatformParams, fso: FSOParams, n_points: int = 512) -> float:
    """Path-averaged Cn2 between UAV and HAP altitudes."""
    h1 = float(platform.h_uav_m)
    h2 = float(platform.h_hap_m)
    if h2 <= h1:
        return float(hv_cn2(np.array([h1]), fso)[0])
    h = np.linspace(h1, h2, int(n_points))
    c = hv_cn2(h, fso)
    return float(np.trapz(c, h) / max(h2 - h1, EPS))


def atmospheric_eta(alpha_db_per_km: float, L_km: float) -> float:
    alpha_neper_per_km = float(alpha_db_per_km) * math.log(10.0) / 10.0
    return float(math.exp(-alpha_neper_per_km * float(L_km)))


def diffraction_divergence_rad(wavelength_m: float, w0_m: float) -> float:
    return float(wavelength_m) / (math.pi * max(float(w0_m), EPS))


def geometric_capture_eta(L_km: float, fso: FSOParams) -> float:
    L_m = float(L_km) * 1e3
    theta_div = diffraction_divergence_rad(fso.lambda_m, fso.w0_uav_m)
    wL = math.sqrt(float(fso.w0_uav_m) ** 2 + (theta_div * L_m) ** 2)
    a = float(fso.d_rx_hap_m) / 2.0
    eta = 1.0 - math.exp(-2.0 * (a / max(wL, EPS)) ** 2)
    return float(np.clip(eta, 0.0, 1.0))


def effective_uav_jitter_sigma_m(platform: PlatformParams, L_km: float) -> float:
    L_m = float(L_km) * 1e3
    return math.sqrt(float(platform.sigma_pos_m) ** 2 + (L_m * float(platform.sigma_orient_rad)) ** 2)


def turbulence_wander_sigma_m(cn2_eff: float, L_km: float, fso: FSOParams) -> float:
    # Compact empirical scaling for beam wander in this simulator.
    base = max(float(fso.w0_uav_m), 1e-4)
    return base * 0.35 * math.sqrt(max(float(cn2_eff), 1e-18) / 1e-14) * math.sqrt(max(float(L_km), 0.1) / 20.0)


def sample_pointing_error_r(
    rng: np.random.Generator,
    n_samples: int,
    sigma_turb_m: float,
    sigma_uav_m: float,
    d_m: float,
    weibull_shape: float,
) -> np.ndarray:
    sigma_point = math.sqrt(float(sigma_turb_m) ** 2 + float(sigma_uav_m) ** 2)
    d = float(d_m)

    if sigma_point <= EPS:
        return np.full(int(n_samples), abs(d), dtype=float)

    if abs(d) <= EPS:
        return sigma_point * rng.weibull(float(weibull_shape), size=int(n_samples))

    # Rice distribution from 2D Gaussian components.
    x = rng.normal(loc=d, scale=sigma_point, size=int(n_samples))
    y = rng.normal(loc=0.0, scale=sigma_point, size=int(n_samples))
    return np.sqrt(x * x + y * y)


def pointing_transmittance(r_m: np.ndarray, fso: FSOParams) -> np.ndarray:
    R = max(float(fso.R_m), EPS)
    g = max(float(fso.gamma), EPS)
    t = float(fso.T0) * np.exp(-np.power(np.maximum(r_m, 0.0) / R, g))
    return np.clip(t, 0.0, 1.0)


def phase_noise_tau2(cn2_eff: float, L_km: float, wavelength_m: float) -> float:
    k = 2.0 * math.pi / float(wavelength_m)
    L_m = float(L_km) * 1e3
    return 2.46 * float(cn2_eff) * (k ** (7.0 / 6.0)) * (L_m ** (11.0 / 6.0))


def chi_device(v_el: float, eta_d: float) -> float:
    eta = max(float(eta_d), EPS)
    return (float(v_el) + (1.0 - eta)) / eta


def gm_covariance_matrix(VA: float, T: float, chi_line: float, Z: Optional[float] = None) -> np.ndarray:
    if Z is None:
        Z = math.sqrt(float(VA) ** 2 + 2.0 * float(VA))
    I = np.eye(2, dtype=float)
    sigma_z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=float)
    corr = math.sqrt(max(float(T), EPS)) * float(Z) * sigma_z
    B = float(T) * (float(VA) + 1.0 + float(chi_line)) * I
    top = np.hstack(((float(VA) + 1.0) * I, corr))
    bottom = np.hstack((corr, B))
    return np.vstack((top, bottom))


def _symp12(VA: float, T: float, chi_line: float, Z: Optional[float] = None) -> tuple:
    Ts = max(float(T), EPS)
    if Z is None:
        Z = math.sqrt(float(VA) ** 2 + 2.0 * float(VA))
    t_v = Ts * (float(VA) + 1.0 + float(chi_line))
    A = (float(VA) + 1.0) ** 2 + t_v**2 - 2.0 * Ts * (float(Z) ** 2)
    B_inner = Ts * ((float(VA) + 1.0) ** 2 + (float(VA) + 1.0) * float(chi_line) - float(Z) ** 2)
    B = B_inner**2
    disc = max(A * A - 4.0 * B, 0.0)
    l1 = math.sqrt(max(0.5 * (A + math.sqrt(disc)), 1e-30))
    l2 = math.sqrt(max(0.5 * (A - math.sqrt(disc)), 1e-30))
    return l1, l2, B, A


def holevo_gm_hom(VA: float, T: float, chi_line: float, chi_D: float) -> float:
    Ts = max(float(T), EPS)
    chi_tot = float(chi_line) + float(chi_D) / Ts
    l1, l2, B, A = _symp12(VA, Ts, chi_line)
    sqB = math.sqrt(max(B, 0.0))
    denom = Ts * (1.0 + float(VA) + chi_tot)

    C = (A * float(chi_D) + (float(VA) + 1.0) * sqB + Ts * (float(VA) + 1.0 + float(chi_line))) / denom
    D = (sqB * (float(VA) + 1.0 + sqB * float(chi_D))) / denom

    disc = max(C * C - 4.0 * D, 0.0)
    l3 = math.sqrt(max(0.5 * (C + math.sqrt(disc)), 1e-30))
    l4 = math.sqrt(max(0.5 * (C - math.sqrt(disc)), 1e-30))

    return G((l1 - 1.0) / 2.0) + G((l2 - 1.0) / 2.0) - G((l3 - 1.0) / 2.0) - G((l4 - 1.0) / 2.0)


def iab_hom(VA: float, chi_tot: float) -> float:
    return 0.5 * math.log2(1.0 + float(VA) / (1.0 + float(chi_tot)))


def delta_n_privacy(gm: GMParams, N_block: Optional[float] = None) -> float:
    n_eff = float(gm.N_block) if N_block is None else float(N_block)
    sN = math.sqrt(max(n_eff, 1.0))
    d = float(gm.d_disc)
    es = float(gm.eps_s)
    esec = float(gm.eps_sec)
    return (
        (d + 1.0) ** 2 / sN
        + 4.0 * (d + 1.0) * math.sqrt(math.log2(2.0 / es)) / sN
        + 2.0 * math.log2(2.0 / (esec**2 * es)) / sN
        + 4.0 * es * d / (esec * sN)
    )


def group_transmittance_samples(T_samples: np.ndarray, n_groups: int, t_upper: Optional[float] = None) -> dict:
    g = max(int(n_groups), 1)
    t = np.clip(np.asarray(T_samples, dtype=float), EPS, 1.0)
    if t_upper is None:
        t_hi = float(np.max(t))
    else:
        t_hi = max(float(t_upper), EPS)
    edges = np.linspace(0.0, t_hi, g + 1)
    total = int(t.size)

    groups = []
    for idx in range(g):
        lo = edges[idx]
        hi = edges[idx + 1]
        if idx < g - 1:
            mask = (t >= lo) & (t < hi)
        else:
            mask = (t >= lo) & (t <= hi)
        n = int(np.count_nonzero(mask))
        p = float(n / max(total, 1))
        t_mean = float(np.mean(t[mask])) if n > 0 else 0.0
        groups.append(
            {
                "group": idx + 1,
                "t_low": float(lo),
                "t_high": float(hi),
                "n": n,
                "p": p,
                "T_group": t_mean,
            }
        )
    return {"edges": edges, "groups": groups}


def simulate_fading(
    platform: PlatformParams,
    fso: FSOParams,
    L_km: float,
    cn2_eff: float,
    seed: int,
) -> dict:
    rng = np.random.default_rng(int(seed))

    sigma_uav = effective_uav_jitter_sigma_m(platform, L_km)
    sigma_turb = turbulence_wander_sigma_m(cn2_eff, L_km, fso)
    d_m = float(platform.theta_pe_rad) * float(L_km) * 1e3

    r = sample_pointing_error_r(
        rng=rng,
        n_samples=int(fso.n_fading_samples),
        sigma_turb_m=sigma_turb,
        sigma_uav_m=sigma_uav,
        d_m=d_m,
        weibull_shape=fso.weibull_shape,
    )
    t_point = pointing_transmittance(r, fso)

    eta_atm = atmospheric_eta(fso.alpha_db_per_km, L_km)
    eta_geo = geometric_capture_eta(L_km, fso)
    eta_fixed = eta_atm * eta_geo * float(fso.eta_smf) * float(fso.eta_tr) * float(fso.eta_ao)
    t_samples = np.clip(eta_fixed * t_point, EPS, 1.0)

    return {
        "sigma_uav_m": sigma_uav,
        "sigma_turb_m": sigma_turb,
        "eta_atm": eta_atm,
        "eta_geo": eta_geo,
        "eta_fixed": eta_fixed,
        "T_samples": t_samples,
        "T_mean": float(np.mean(t_samples)),
        "T_eff": float(np.mean(np.sqrt(t_samples)) ** 2),
        "T_logneg": float(np.exp(np.mean(np.log(t_samples)))),
    }


def noise_model(T_eff: float, L_km: float, cn2_eff: float, sigma_turb_m: float, sigma_uav_m: float, gm: GMParams, fso: FSOParams) -> dict:
    tau2 = phase_noise_tau2(cn2_eff, L_km, fso.lambda_m)
    ao_delay_ratio = float(fso.ao_delay_s) / max(float(fso.ao_integration_s), EPS)
    ao_residual = max(0.0, 1.0 - float(fso.eta_ao)) + 0.05 * max(ao_delay_ratio - 1.0, 0.0)

    V_phase = 2.0 * tau2 * max(ao_residual, 0.0)
    xi_turb = float(fso.xi_turb_coeff) * (sigma_turb_m / max(float(fso.R_m), EPS)) ** 2
    xi_uav = float(fso.xi_uav_coeff) * (sigma_uav_m / max(float(fso.R_m), EPS)) ** 2
    xi_tot = float(fso.xi_base) + V_phase + xi_turb + xi_uav

    T = max(float(T_eff), EPS)
    chi_line = (1.0 / T - 1.0) + xi_tot
    chi_D = chi_device(gm.v_el, gm.eta_d)
    chi_tot = chi_line + chi_D / T

    return {
        "tau2": tau2,
        "V_phase": V_phase,
        "xi_turb": xi_turb,
        "xi_uav": xi_uav,
        "xi_tot": xi_tot,
        "chi_line": chi_line,
        "chi_D": chi_D,
        "chi_tot": chi_tot,
    }


def evaluate_link(
    platform: PlatformParams,
    gm: GMParams,
    fso: FSOParams,
    seed: int = 7,
    L_override_km: Optional[float] = None,
) -> dict:
    L_km = float(L_override_km) if L_override_km is not None else slant_range_uav_hap_km(platform)
    cn2_eff = effective_cn2_hv(platform, fso)
    fading = simulate_fading(platform, fso, L_km, cn2_eff, seed=seed)
    noise = noise_model(
        T_eff=fading["T_eff"],
        L_km=L_km,
        cn2_eff=cn2_eff,
        sigma_turb_m=fading["sigma_turb_m"],
        sigma_uav_m=fading["sigma_uav_m"],
        gm=gm,
        fso=fso,
    )

    I_AB = iab_hom(gm.VA, noise["chi_tot"])
    S_BE = holevo_gm_hom(gm.VA, fading["T_eff"], noise["chi_line"], noise["chi_D"])
    skr_asy = float(gm.beta) * I_AB - S_BE
    d_priv = delta_n_privacy(gm)
    skr_fin = float(gm.f_rep) * ((1.0 - float(gm.FER)) * float(gm.beta) * I_AB - S_BE - d_priv)

    return {
        "L_km": L_km,
        "cn2_eff": cn2_eff,
        **fading,
        **noise,
        "I_AB": I_AB,
        "S_BE": S_BE,
        "SKR_asy": skr_asy,
        "delta_n_privacy": d_priv,
        "SKR_fin_bps": skr_fin,
        "covariance": gm_covariance_matrix(gm.VA, fading["T_eff"], noise["chi_line"]),
    }


def evaluate_link_grouped(
    platform: PlatformParams,
    gm: GMParams,
    fso: FSOParams,
    n_groups: Optional[int] = None,
    seed: int = 7,
    L_override_km: Optional[float] = None,
) -> dict:
    L_km = float(L_override_km) if L_override_km is not None else slant_range_uav_hap_km(platform)
    cn2_eff = effective_cn2_hv(platform, fso)
    fading = simulate_fading(platform, fso, L_km, cn2_eff, seed=seed)
    grouped = group_transmittance_samples(
        fading["T_samples"],
        n_groups=gm.n_groups if n_groups is None else int(n_groups),
        t_upper=fading["eta_fixed"] * float(fso.T0),
    )

    asy_agg = 0.0
    fin_agg_bps = 0.0
    group_rows = []
    for row in grouped["groups"]:
        if row["n"] <= 0 or row["T_group"] <= EPS:
            group_rows.append({**row, "I_AB": np.nan, "S_BE": np.nan, "SKR_asy": np.nan, "SKR_fin_bps": np.nan})
            continue

        noise_g = noise_model(
            T_eff=row["T_group"],
            L_km=L_km,
            cn2_eff=cn2_eff,
            sigma_turb_m=fading["sigma_turb_m"],
            sigma_uav_m=fading["sigma_uav_m"],
            gm=gm,
            fso=fso,
        )
        iab = iab_hom(gm.VA, noise_g["chi_tot"])
        sbe = holevo_gm_hom(gm.VA, row["T_group"], noise_g["chi_line"], noise_g["chi_D"])
        skr_asy = float(gm.beta) * iab - sbe

        n_block_g = max(float(gm.N_block) * row["p"], 1.0)
        d_priv_g = delta_n_privacy(gm, N_block=n_block_g)
        skr_fin_g = float(gm.f_rep) * row["p"] * (
            (1.0 - float(gm.FER)) * float(gm.beta) * iab - sbe - d_priv_g
        )

        asy_agg += row["p"] * skr_asy
        fin_agg_bps += skr_fin_g
        group_rows.append(
            {
                **row,
                "chi_line": noise_g["chi_line"],
                "chi_tot": noise_g["chi_tot"],
                "I_AB": iab,
                "S_BE": sbe,
                "SKR_asy": skr_asy,
                "delta_n_privacy": d_priv_g,
                "SKR_fin_bps": skr_fin_g,
            }
        )

    return {
        "L_km": L_km,
        "cn2_eff": cn2_eff,
        **fading,
        "group_edges": grouped["edges"],
        "group_rows": group_rows,
        "SKR_asy_grouped": float(asy_agg),
        "SKR_fin_grouped_bps": float(fin_agg_bps),
    }


def plot_skr_vs_distance(platform: PlatformParams, gm: GMParams, fso: FSOParams) -> None:
    L_km = np.linspace(5.0, 80.0, 70)
    alpha_cases = [0.1, 0.4]

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for alpha_db in alpha_cases:
        fso_case = replace(fso, alpha_db_per_km=float(alpha_db))
        vals = []
        for i, L in enumerate(L_km):
            out = evaluate_link_grouped(
                platform,
                gm,
                fso_case,
                n_groups=gm.n_groups,
                seed=100 + i,
                L_override_km=float(L),
            )
            vals.append(out["SKR_asy_grouped"])
        ax.plot(L_km, vals, lw=2, label=f"alpha={alpha_db:.1f} dB/km")

    ax.axhline(0.0, color="k", lw=1.0, alpha=0.5)
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Grouped SKR [bits/pulse]")
    ax.set_title(f"UAV-to-HAP GM-CVQKD: Grouped SKR vs Distance (G={gm.n_groups})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()


def plot_transmittance_vs_distance(platform: PlatformParams, gm: GMParams, fso: FSOParams) -> None:
    L_km = np.linspace(5.0, 80.0, 70)
    alpha_cases = [0.1, 0.4]

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for alpha_db in alpha_cases:
        fso_case = replace(fso, alpha_db_per_km=float(alpha_db))
        t_eff_vals = []
        for i, L in enumerate(L_km):
            out = evaluate_link(platform, gm, fso_case, seed=300 + i, L_override_km=float(L))
            t_eff_vals.append(out["T_eff"])
        ax.semilogy(L_km, t_eff_vals, lw=2, label=f"alpha={alpha_db:.1f} dB/km")

    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Effective transmittance T_eff")
    ax.set_title("UAV-to-HAP FSO: T change vs Distance")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    plt.tight_layout()


def plot_skr_vs_jitter(platform: PlatformParams, gm: GMParams, fso: FSOParams) -> None:
    pos_jitter_mm = np.linspace(1.0, 120.0, 70)
    L_fix = slant_range_uav_hap_km(platform)

    x_sigma_uav_mm = []
    skr_vals = []
    for i, sig_mm in enumerate(pos_jitter_mm):
        platform_case = replace(platform, sigma_pos_m=float(sig_mm) * 1e-3)
        out = evaluate_link_grouped(
            platform_case,
            gm,
            fso,
            n_groups=gm.n_groups,
            seed=900 + i,
            L_override_km=L_fix,
        )
        x_sigma_uav_mm.append(out["sigma_uav_m"] * 1e3)
        skr_vals.append(out["SKR_asy_grouped"])

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(x_sigma_uav_mm, skr_vals, lw=2, color="tab:red")
    ax.axhline(0.0, color="k", lw=1.0, alpha=0.5)
    ax.set_xlabel("Effective pointing jitter sigma_uav [mm]")
    ax.set_ylabel("Grouped SKR [bits/pulse]")
    ax.set_title(f"UAV-to-HAP GM-CVQKD: Grouped SKR vs Pointing Jitter (L={L_fix:.1f} km, G={gm.n_groups})")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()


def plot_transmittance_vs_jitter(platform: PlatformParams, gm: GMParams, fso: FSOParams) -> None:
    pos_jitter_mm = np.linspace(1.0, 120.0, 70)
    L_fix = slant_range_uav_hap_km(platform)

    x_sigma_uav_mm = []
    t_eff_vals = []
    for i, sig_mm in enumerate(pos_jitter_mm):
        platform_case = replace(platform, sigma_pos_m=float(sig_mm) * 1e-3)
        out = evaluate_link(platform_case, gm, fso, seed=1200 + i, L_override_km=L_fix)
        x_sigma_uav_mm.append(out["sigma_uav_m"] * 1e3)
        t_eff_vals.append(out["T_eff"])

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.semilogy(x_sigma_uav_mm, t_eff_vals, lw=2, color="tab:green")
    ax.set_xlabel("Effective pointing jitter sigma_uav [mm]")
    ax.set_ylabel("Effective transmittance T_eff")
    ax.set_title(f"UAV-to-HAP FSO: T change vs Pointing Jitter (L={L_fix:.1f} km)")
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()


def plot_skr_vs_group_count(platform: PlatformParams, gm: GMParams, fso: FSOParams) -> None:
    group_counts = np.array([1, 2, 5, 10, 20, 50, 100], dtype=int)
    L_fix = slant_range_uav_hap_km(platform)
    asy_vals = []
    fin_vals = []

    for i, g in enumerate(group_counts):
        out = evaluate_link_grouped(platform, gm, fso, n_groups=int(g), seed=1500 + i, L_override_km=L_fix)
        asy_vals.append(out["SKR_asy_grouped"])
        fin_vals.append(out["SKR_fin_grouped_bps"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4))
    ax1.plot(group_counts, asy_vals, marker="o", lw=1.8)
    ax1.set_xlabel("Number of T groups G")
    ax1.set_ylabel("Grouped SKR [bits/pulse]")
    ax1.set_title(f"Grouped asymptotic SKR vs G (L={L_fix:.1f} km)")
    ax1.grid(True, alpha=0.3)

    ax2.plot(group_counts, fin_vals, marker="o", lw=1.8, color="tab:purple")
    ax2.set_xlabel("Number of T groups G")
    ax2.set_ylabel("Grouped finite-size SKR [bits/s]")
    ax2.set_title(f"Grouped finite-size SKR vs G (L={L_fix:.1f} km)")
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()


def main() -> None:
    platform = PlatformParams(
        h_uav_m=1_000.0,
        h_hap_m=20_000.0,
        theta_z_deg=20.0,
        sigma_pos_m=0.03,
        sigma_orient_rad=5e-6,
        theta_pe_rad=1e-6,
    )
    fso = FSOParams(
        lambda_m=1550e-9,
        alpha_db_per_km=0.4,
        w0_uav_m=0.0157,
        w0_hap_m=0.10,
        d_rx_hap_m=0.35,
        eta_smf=0.80,
        eta_tr=0.85,
        eta_ao=0.80,
        ao_delay_s=2e-3,
        ao_integration_s=5e-4,
        T0=0.98,
        R_m=0.04,
        gamma=2.0,
        weibull_shape=2.0,
        hv_A=1.7e-14,
        hv_wind_ms=21.0,
        xi_base=0.0,
        xi_turb_coeff=1.0,
        xi_uav_coeff=1.0,
        n_fading_samples=20_000,
    )
    gm = GMParams(
        VA=3.0,
        beta=0.9,
        eta_d=0.60,
        v_el=0.10,
        N_block=1e8,
        f_rep=50e6,
        FER=0.0,
        d_disc=5,
        eps_s=2e-10,
        eps_sec=1e-9,
        n_groups=10,
    )

    probe = evaluate_link(platform, gm, fso, seed=42)
    probe_grouped = evaluate_link_grouped(platform, gm, fso, n_groups=gm.n_groups, seed=42)
    print("=== UAV-to-HAP GM-CVQKD quick probe ===")
    print(f"L={probe['L_km']:.3f} km, Cn2_eff={probe['cn2_eff']:.3e}")
    print(
        "T_mean={:.6f}, T_eff={:.6f}, T_logneg={:.6f}".format(
            probe["T_mean"], probe["T_eff"], probe["T_logneg"]
        )
    )
    print(
        "chi_line={:.6f}, chi_D={:.6f}, chi_tot={:.6f}".format(
            probe["chi_line"], probe["chi_D"], probe["chi_tot"]
        )
    )
    print(
        "I_AB={:.6f}, S_BE={:.6f}, SKR_asy={:.6f} bits/pulse".format(
            probe["I_AB"], probe["S_BE"], probe["SKR_asy"]
        )
    )
    print(
        "delta_n={:.6e}, SKR_fin={:.3f} bits/s".format(
            probe["delta_n_privacy"], probe["SKR_fin_bps"]
        )
    )
    print(
        "Grouped (G={}) => SKR_asy={:.6f} bits/pulse, SKR_fin={:.3f} bits/s".format(
            gm.n_groups, probe_grouped["SKR_asy_grouped"], probe_grouped["SKR_fin_grouped_bps"]
        )
    )

    plot_transmittance_vs_distance(platform, gm, fso)
    plot_skr_vs_distance(platform, gm, fso)
    plot_transmittance_vs_jitter(platform, gm, fso)
    plot_skr_vs_jitter(platform, gm, fso)
    plot_skr_vs_group_count(platform, gm, fso)
    plt.show()


if __name__ == "__main__":
    main()
