from dataclasses import replace
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

from ..channel.channel_model import channel
from ..config import ChannelParams, FiniteSizeParams, GeometryParams, MonteCarloParams, NoiseParams, SecurityParams
from ..main import simulate_uav_hap_cvqkd
from ..protocols.gm import noise, optimize_modulation_variance, skr, skr_components

LINE_STYLES = ["-", "--", "-."]
MARKERS = ["o", "s", "^", "d", "v", "P", "X"]


def _default_distance_grid_m() -> np.ndarray:
    return np.linspace(5_000.0, 60_000.0, 20)


def _default_jitter_grid_m() -> np.ndarray:
    return np.linspace(0.005, 0.05, 18)


def _default_turbulence_grid_m() -> np.ndarray:
    return np.linspace(0.002, 0.04, 18)


def _default_cn2_grid() -> np.ndarray:
    return np.logspace(-15, -17, 15)


def _new_figure(figsize=(7.2, 4.8)):
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    ax.grid(True, which="major", alpha=0.35)
    ax.grid(True, which="minor", alpha=0.2, linestyle=":")
    ax.minorticks_on()
    return fig, ax


def _sim(
    L_m: float,
    geometry: GeometryParams,
    channel_params: ChannelParams,
    noise_params: NoiseParams,
    security_params: SecurityParams,
    monte_carlo: MonteCarloParams,
    finite_size: FiniteSizeParams,
    N: int,
    n: int,
    seed: int,
    sigma_r_m: Optional[float] = None,
    xi_phase: Optional[float] = None,
) -> dict:
    mc = replace(monte_carlo, seed=int(seed))
    return simulate_uav_hap_cvqkd(
        geometry=geometry,
        channel_params=channel_params,
        noise_params=noise_params,
        security_params=security_params,
        monte_carlo=mc,
        finite_size=finite_size,
        L_m=float(L_m),
        sigma_r_m=sigma_r_m,
        xi_phase=xi_phase,
        N=int(N),
        n=int(n),
        histogram_bins=None,
    )


def _optimized_skr_from_teff(T_eff: float, noise_params: NoiseParams, beta: float) -> tuple[float, float]:
    opt = optimize_modulation_variance(
        T_eff=max(float(T_eff), 1e-15),
        noise_params=noise_params,
        beta=float(beta),
        VA_min=0.1,
        VA_max=10.0,
        VA_points=200,
    )
    return float(opt["SKR_opt"]), float(opt["VA_opt"])


def plot_skr_vs_distance(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 100,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    k_fade_phase = np.empty_like(L_arr)
    k_det_phase = np.empty_like(L_arr)
    k_fade_no_phase = np.empty_like(L_arr)
    k_det_no_phase = np.empty_like(L_arr)

    for i, L_m in enumerate(L_arr):
        out_fp = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=n, seed=seed + i, xi_phase=nz.xi_phase)
        out_dp = _sim(
            L_m,
            geom,
            ch,
            nz,
            sec,
            mc,
            fs,
            N=1,
            n=n,
            seed=seed + 1000 + i,
            sigma_r_m=0.0,
            xi_phase=nz.xi_phase,
        )
        out_fn = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=n, seed=seed + 2000 + i, xi_phase=0.0)
        out_dn = _sim(
            L_m,
            geom,
            ch,
            nz,
            sec,
            mc,
            fs,
            N=1,
            n=n,
            seed=seed + 3000 + i,
            sigma_r_m=0.0,
            xi_phase=0.0,
        )
        k_fade_phase[i] = out_fp["K_eff"]
        k_det_phase[i] = out_dp["K_eff"]
        k_fade_no_phase[i] = out_fn["K_eff"]
        k_det_no_phase[i] = out_dn["K_eff"]

    fig, ax = _new_figure()
    x_km = L_arr / 1000.0
    ax.plot(x_km, k_fade_phase, linestyle="-", marker="o", markevery=max(len(x_km) // 12, 1), label="Fading MC, phase noise")
    ax.plot(
        x_km,
        k_det_phase,
        linestyle="--",
        marker="s",
        markevery=max(len(x_km) // 12, 1),
        label="No fading, phase noise",
    )
    ax.plot(
        x_km,
        k_fade_no_phase,
        linestyle="-.",
        marker="^",
        markevery=max(len(x_km) // 12, 1),
        label="Fading MC, no phase noise",
    )
    ax.plot(
        x_km,
        k_det_no_phase,
        linestyle="-",
        marker="d",
        markevery=max(len(x_km) // 12, 1),
        label="No fading, no phase noise",
    )
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Secret key rate K_eff [bits/use]")
    ax.set_title("Secret Key Rate vs Distance for UAV–HAP CV-QKD under Fading")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_skr_vs_jitter(
    sigma_uav_values_m: Optional[Sequence[float]] = None,
    sigma_turb_levels_m: Sequence[float] = (0.005, 0.015, 0.03),
    distance_m: Optional[float] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 500,
) -> plt.Figure:
    sigma_uav = np.asarray(_default_jitter_grid_m() if sigma_uav_values_m is None else sigma_uav_values_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size
    L_m = float(geom.H_HAP_m - geom.H_UAV_m) if distance_m is None else float(distance_m)

    fig, ax = _new_figure()
    for j, sigma_turb in enumerate(sigma_turb_levels_m):
        curve = np.empty_like(sigma_uav)
        for i, sigma_uav_i in enumerate(sigma_uav):
            ch_i = replace(ch, sigma_turb_m=float(sigma_turb), sigma_UAV_m=float(sigma_uav_i), sigma_r_m=None)
            out = _sim(L_m, geom, ch_i, nz, sec, mc, fs, N=N, n=n, seed=seed + 500 * j + i)
            curve[i] = out["K_eff"]
        ax.plot(
            sigma_uav,
            curve,
            linestyle=LINE_STYLES[j % len(LINE_STYLES)],
            marker=MARKERS[j % len(MARKERS)],
            markevery=max(len(sigma_uav) // 10, 1),
            label=rf"$\sigma_{{turb}}={float(sigma_turb):.3f}$ m",
        )

    ax.set_xlabel(r"UAV jitter $\sigma_{UAV}$ [m]")
    ax.set_ylabel("Secret key rate K_eff [bits/use]")
    ax.set_title("Secret Key Rate vs UAV Jitter for Different Turbulence Levels")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_skr_vs_turbulence(
    sigma_turb_values_m: Optional[Sequence[float]] = None,
    distance_m: Optional[float] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 900,
) -> plt.Figure:
    sigma_turb = np.asarray(_default_turbulence_grid_m() if sigma_turb_values_m is None else sigma_turb_values_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size
    L_m = float(geom.H_HAP_m - geom.H_UAV_m) if distance_m is None else float(distance_m)

    k_eff = np.empty_like(sigma_turb)
    for i, sigma_turb_i in enumerate(sigma_turb):
        ch_i = replace(ch, sigma_turb_m=float(sigma_turb_i), sigma_r_m=None)
        out = _sim(L_m, geom, ch_i, nz, sec, mc, fs, N=N, n=n, seed=seed + i)
        k_eff[i] = out["K_eff"]

    fig, ax = _new_figure()
    ax.plot(sigma_turb, k_eff, linestyle="-", marker="o", markevery=max(len(sigma_turb) // 10, 1), label="Monte Carlo fading")
    ax.set_xlabel(r"Turbulence parameter $\sigma_{turb}$ [m]")
    ax.set_ylabel("Secret key rate K_eff [bits/use]")
    ax.set_title("Secret Key Rate vs Turbulence for UAV–HAP CV-QKD")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_skr_vs_cn2(
    cn2_values: Optional[Sequence[float]] = None,
    distance_m: Optional[float] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 1100,
) -> plt.Figure:
    cn2_arr = np.asarray(_default_cn2_grid() if cn2_values is None else cn2_values, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size
    L_m = float(geom.H_HAP_m - geom.H_UAV_m) if distance_m is None else float(distance_m)

    k_eff = np.empty_like(cn2_arr)
    for i, cn2 in enumerate(cn2_arr):
        ch_i = replace(ch, Cn2=float(cn2), use_hv_turbulence=False, sigma_turb_m=None, sigma_r_m=None)
        out = _sim(L_m, geom, ch_i, nz, sec, mc, fs, N=N, n=n, seed=seed + i)
        k_eff[i] = out["K_eff"]

    fig, ax = _new_figure()
    ax.semilogx(cn2_arr, k_eff, linestyle="-", marker="o", markevery=max(len(cn2_arr) // 10, 1), label="Fixed-Cn2 model")
    ax.invert_xaxis()
    ax.set_xlabel(r"Refractive-index structure constant $C_n^2$ [m$^{-2/3}$]")
    ax.set_ylabel("Secret key rate K_eff [bits/use]")
    ax.set_title("Secret Key Rate vs $C_n^2$ (from $10^{-15}$ to $10^{-17}$)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_outage(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 1300,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    p_out = np.empty_like(L_arr)
    for i, L_m in enumerate(L_arr):
        out = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=n, seed=seed + i)
        p_out[i] = out["P_out"]

    fig, ax = _new_figure()
    ax.plot(L_arr / 1000.0, p_out, linestyle="--", marker="s", markevery=max(len(L_arr) // 12, 1), label=r"$P_{out}=\Pr(K_i<0)$")
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Outage probability")
    ax.set_title("Outage Probability vs Distance for UAV–HAP CV-QKD")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_finite_vs_asymptotic(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 60_000,
    n: int = 100_000_000,
    seed: int = 1700,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    k_eff = np.empty_like(L_arr)
    k_finite = np.empty_like(L_arr)
    for i, L_m in enumerate(L_arr):
        out = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=n, seed=seed + i)
        k_eff[i] = out["K_eff"]
        k_finite[i] = out["K_finite"]

    fig, ax = _new_figure()
    x_km = L_arr / 1000.0
    ax.plot(x_km, k_eff, linestyle="-", marker="o", markevery=max(len(x_km) // 12, 1), label="Asymptotic K_eff")
    ax.plot(x_km, k_finite, linestyle="-.", marker="^", markevery=max(len(x_km) // 12, 1), label="Finite-size K_finite")
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Secret key rate [bits/use]")
    ax.set_title("Finite-Size and Asymptotic Secret Key Rate vs Distance")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_teff_vs_mc(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    N: int = 60_000,
    seed: int = 2100,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo

    k_wrong = np.empty_like(L_arr)
    k_correct = np.empty_like(L_arr)

    for i, L_m in enumerate(L_arr):
        rng = np.random.default_rng(int(mc.seed if mc.seed is not None else seed) + i + seed)
        fading = channel(geometry=geom, channel_params=ch, N=int(N), rng=rng, L_override_m=float(L_m))
        T_samples = np.asarray(fading["T_samples"], dtype=float)

        noise_terms = noise(T_samples=T_samples, noise_params=nz)
        k_samples = np.asarray(skr(T_samples=T_samples, noise_terms=noise_terms, security_params=sec, detection=nz.detection), dtype=float)
        k_correct[i] = float(np.mean(k_samples))

        T_mean = np.array([float(np.mean(T_samples))], dtype=float)
        noise_mean = noise(T_samples=T_mean, noise_params=nz)
        k_wrong[i] = float(skr(T_samples=T_mean, noise_terms=noise_mean, security_params=sec, detection=nz.detection)[0])

    fig, ax = _new_figure()
    x_km = L_arr / 1000.0
    ax.plot(x_km, k_wrong, linestyle="--", marker="s", markevery=max(len(x_km) // 12, 1), label=r"Wrong: $K(\mathbb{E}[T])$")
    ax.plot(
        x_km,
        k_correct,
        linestyle="-",
        marker="o",
        markevery=max(len(x_km) // 12, 1),
        label=r"Correct: $\mathbb{E}[K(T)]$",
    )
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("Secret key rate [bits/use]")
    ax.set_title("Comparison of Wrong and Correct Fading Averaging Methods")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_transmittance_histogram(
    distance_m: Optional[float] = None,
    bins: int = 80,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    N: int = 120_000,
    seed: int = 2600,
) -> plt.Figure:
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    L_m = float(geom.H_HAP_m - geom.H_UAV_m) if distance_m is None else float(distance_m)
    rng = np.random.default_rng(int(mc.seed if mc.seed is not None else seed) + seed)
    fading = channel(geometry=geom, channel_params=ch, N=int(N), rng=rng, L_override_m=L_m)
    T_samples = np.asarray(fading["T_samples"], dtype=float)

    fig, ax = _new_figure()
    ax.hist(T_samples, bins=int(bins), density=True, alpha=0.75, edgecolor="black", linewidth=0.5, label="PDF approximation")
    ax.set_xlabel("Transmittance T")
    ax.set_ylabel("Probability density")
    ax.set_title("Histogram of Channel Transmittance under UAV–HAP Fading")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_figure1_teff_vs_distance(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3100,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    teff = np.empty_like(L_arr)
    for i, L_m in enumerate(L_arr):
        out = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        teff[i] = out["T_eff"]

    fig, ax = _new_figure()
    ax.semilogy(L_arr / 1000.0, teff, linestyle="-", marker="o", markevery=max(len(L_arr) // 12, 1))
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel(r"Effective transmittance $T_{\mathrm{eff}}$")
    ax.set_title("Figure 1: $T_{eff}$ vs Distance")
    fig.tight_layout()
    return fig


def plot_figure2_skr_vs_distance(
    distances_m: Optional[Sequence[float]] = None,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3200,
) -> plt.Figure:
    L_arr = np.asarray(_default_distance_grid_m() if distances_m is None else distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size
    sec_fixed = SecurityParams(VA=2.6, beta=0.95, optimize_VA=False)
    sec_opt = SecurityParams(VA=2.6, beta=0.95, optimize_VA=True)

    skr_fixed = np.empty_like(L_arr)
    skr_opt = np.empty_like(L_arr)
    va_opt = np.empty_like(L_arr)

    for i, L_m in enumerate(L_arr):
        out_fixed = _sim(L_m, geom, ch, nz, sec_fixed, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        out_opt = _sim(L_m, geom, ch, nz, sec_opt, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        skr_fixed[i] = out_fixed["K_eff"]
        skr_opt[i] = out_opt["VA_optimization"]["SKR_opt"]
        va_opt[i] = out_opt["VA_optimization"]["VA_opt"]

    fig, ax = _new_figure()
    x_km = L_arr / 1000.0
    ax.plot(x_km, skr_fixed, linestyle="--", marker="s", markevery=max(len(x_km) // 12, 1), label="Fixed VA = 2.6")
    ax.plot(x_km, skr_opt, linestyle="-", marker="o", markevery=max(len(x_km) // 12, 1), label="Optimized VA")
    ax.set_xlabel("Distance L [km]")
    ax.set_ylabel("SKR [bits/use]")
    ax.set_title("Figure 2: SKR vs Distance (Fixed VA vs Optimized VA)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_figure3_skr_vs_va(
    distances_m: Sequence[float] = (1_000.0, 2_000.0, 5_000.0),
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3300,
) -> plt.Figure:
    L_arr = np.asarray(distances_m, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    fig, ax = _new_figure()
    for i, L_m in enumerate(L_arr):
        out = _sim(L_m, geom, ch, nz, sec, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        opt = optimize_modulation_variance(
            T_eff=out["T_eff"],
            noise_params=nz,
            beta=sec.beta,
            VA_min=0.1,
            VA_max=10.0,
            VA_points=200,
        )
        va_range = np.asarray(opt["VA_range"], dtype=float)
        skr_range = np.asarray(opt["SKR_list"], dtype=float)
        skr_plot = np.where(skr_range > 0.0, skr_range, np.nan)
        ax.semilogy(
            va_range,
            skr_plot,
            linestyle=LINE_STYLES[i % len(LINE_STYLES)],
            label=f"L={L_m/1000:.1f} km",
        )
        if float(opt["SKR_opt"]) > 0.0:
            ax.scatter([opt["VA_opt"]], [opt["SKR_opt"]], marker="o", s=30)

    ax.axvline(2.6, linestyle=":", color="gray", linewidth=1.2, label="VA=2.6 reference")
    ax.set_xlabel(r"Modulation variance $V_A$ [SNU]")
    ax.set_ylabel("SKR [bits/use]")
    ax.set_title("Figure 3: SKR vs $V_A$ at selected short/medium distances")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_figure4_skr_vs_cn2(
    cn2_values: Optional[Sequence[float]] = None,
    distance_m: float = 2_000.0,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3400,
) -> plt.Figure:
    cn2_arr = np.asarray(np.logspace(-15, -17, 15) if cn2_values is None else cn2_values, dtype=float)
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    k_opt = np.empty_like(cn2_arr, dtype=float)
    va_opt = np.empty_like(cn2_arr, dtype=float)
    for i, cn2 in enumerate(cn2_arr):
        ch_i = replace(ch, Cn2=float(cn2), use_hv_turbulence=False, sigma_turb_m=None, sigma_r_m=None)
        out = _sim(distance_m, geom, ch_i, nz, sec, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        k_opt[i], va_opt[i] = _optimized_skr_from_teff(out["T_eff"], nz, sec.beta)

    fig, ax = _new_figure()
    k_plot = np.where(k_opt > 0.0, k_opt, np.nan)
    ax.semilogx(cn2_arr, k_plot, linestyle="-", marker="o", markevery=max(len(cn2_arr) // 10, 1))
    ax.invert_xaxis()
    ax.set_xlabel(r"Refractive-index structure constant $C_n^2$ [m$^{-2/3}$]")
    ax.set_ylabel("Optimized SKR [bits/use]")
    ax.set_title(r"Figure 4: Optimized SKR vs $C_n^2$ (distance = %.1f km)" % (distance_m / 1000.0))
    fig.tight_layout()
    return fig


def plot_figure5_skr_vs_nblock(
    nblock_values: Optional[Sequence[int]] = None,
    distance_m: float = 1_000.0,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3500,
) -> plt.Figure:
    n_blocks = (
        np.asarray(np.logspace(6, 10, 13), dtype=float).astype(int)
        if nblock_values is None
        else np.asarray(nblock_values, dtype=int)
    )
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs_base = FiniteSizeParams() if finite_size is None else finite_size

    k_finite = np.empty_like(n_blocks, dtype=float)
    k_opt_asym = np.empty_like(n_blocks, dtype=float)
    for i, nblk in enumerate(n_blocks):
        fs_i = replace(fs_base, N_block=int(nblk), n_ratio=0.8, n=None)
        out = _sim(distance_m, geom, ch, nz, sec, mc, fs_i, N=N, n=int(nblk), seed=seed + i)
        k_opt_asym[i], va_opt_i = _optimized_skr_from_teff(out["T_eff"], nz, sec.beta)

        t_arr = np.array([max(float(out["T_eff"]), 1e-15)], dtype=float)
        n_terms = noise(t_arr, nz)
        sec_i = SecurityParams(VA=float(va_opt_i), beta=float(sec.beta), optimize_VA=False)
        comps = skr_components(
            T_samples=t_arr,
            noise_terms=n_terms,
            security_params=sec_i,
            detection=nz.detection,
            eta_d=n_terms["eta_d"],
        )
        n_block = int(round(float(fs_i.n_ratio) * float(fs_i.N_block)))
        epsilon = float(fs_i.epsilon_PE + fs_i.epsilon_EC + fs_i.epsilon_PA)
        delta = 7.0 * np.log2(2.0 / max(epsilon, 1e-30)) / np.sqrt(float(max(n_block, 1)))
        k_fs = (float(n_block) / float(fs_i.N_block)) * (
            float(sec_i.beta) * float(comps["I_AB"][0]) - float(comps["chi_BE"][0]) - float(delta)
        )
        k_finite[i] = max(float(k_fs), 0.0)

    fig, ax = _new_figure()
    k_finite_plot = np.where(k_finite > 0.0, k_finite, np.nan)
    k_asym_plot = np.where(k_opt_asym > 0.0, k_opt_asym, np.nan)
    ax.semilogx(n_blocks, k_finite_plot, linestyle="-", marker="o", label="Finite-size SKR")
    ax.semilogx(n_blocks, k_asym_plot, linestyle="--", marker="s", label="Asymptotic SKR (optimized $V_A$)")
    ax.set_xlabel(r"Block size $N_{block}$")
    ax.set_ylabel("SKR [bits/use]")
    ax.set_title(r"Figure 5: SKR vs $N_{block}$ (distance = %.1f km)" % (distance_m / 1000.0))
    ax.legend()
    fig.tight_layout()
    return fig


def plot_figureA_skr_vs_sigma_pos(
    sigma_pos_values_m: Optional[Sequence[float]] = None,
    distance_m: float = 1_000.0,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3600,
) -> plt.Figure:
    sigma_pos = (
        np.asarray(np.linspace(0.01, 0.16, 16), dtype=float)
        if sigma_pos_values_m is None
        else np.asarray(sigma_pos_values_m, dtype=float)
    )
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    k_eff = np.empty_like(sigma_pos)
    for i, s in enumerate(sigma_pos):
        comp = float(s) / np.sqrt(3.0)
        ch_i = replace(ch, sigma_x_m=comp, sigma_y_m=comp, sigma_z_m=comp, sigma_r_m=None)
        out = _sim(distance_m, geom, ch_i, nz, sec, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        k_eff[i], _ = _optimized_skr_from_teff(out["T_eff"], nz, sec.beta)

    fig, ax = _new_figure()
    ax.plot(sigma_pos, k_eff, linestyle="-", marker="o")
    ax.set_xlabel(r"UAV position jitter RMS $\sigma_{pos}$ [m]")
    ax.set_ylabel("Optimized SKR [bits/use]")
    ax.set_title(r"Figure A: Optimized SKR vs $\sigma_{pos}$")
    fig.tight_layout()
    return fig


def plot_figureB_skr_vs_sigma_orient(
    sigma_orient_values_rad: Optional[Sequence[float]] = None,
    distance_m: float = 1_000.0,
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    N: int = 40_000,
    seed: int = 3700,
) -> plt.Figure:
    sigma_orient = (
        np.asarray(np.linspace(0.5e-3, 8e-3, 16), dtype=float)
        if sigma_orient_values_rad is None
        else np.asarray(sigma_orient_values_rad, dtype=float)
    )
    geom = GeometryParams() if geometry is None else geometry
    ch = ChannelParams() if channel_params is None else channel_params
    nz = NoiseParams() if noise_params is None else noise_params
    sec = SecurityParams() if security_params is None else security_params
    mc = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs = FiniteSizeParams() if finite_size is None else finite_size

    k_eff = np.empty_like(sigma_orient)
    for i, s in enumerate(sigma_orient):
        comp = float(s) / np.sqrt(3.0)
        ch_i = replace(ch, sigma_theta_rad=comp, sigma_phi_rad=comp, sigma_psi_rad=comp, sigma_r_m=None)
        out = _sim(distance_m, geom, ch_i, nz, sec, mc, fs, N=N, n=fs.N_block, seed=seed + i)
        k_eff[i], _ = _optimized_skr_from_teff(out["T_eff"], nz, sec.beta)

    fig, ax = _new_figure()
    ax.plot(sigma_orient * 1e3, k_eff, linestyle="-", marker="o")
    ax.set_xlabel(r"UAV angular jitter RMS $\sigma_{orient}$ [mrad]")
    ax.set_ylabel("Optimized SKR [bits/use]")
    ax.set_title(r"Figure B: Optimized SKR vs $\sigma_{orient}$")
    fig.tight_layout()
    return fig


def generate_paper_figures(show: bool = True, save_dir: Optional[str] = None) -> dict:
    figures = {
        "figure1_teff_vs_L": plot_figure1_teff_vs_distance(),
        "figure2_skr_vs_L": plot_figure2_skr_vs_distance(),
        "figure3_skr_vs_VA": plot_figure3_skr_vs_va(),
        "figure4_skr_vs_Cn2": plot_figure4_skr_vs_cn2(),
        "figure5_skr_vs_Nblock": plot_figure5_skr_vs_nblock(),
        "figureA_skr_vs_sigma_pos": plot_figureA_skr_vs_sigma_pos(),
        "figureB_skr_vs_sigma_orient": plot_figureB_skr_vs_sigma_orient(),
    }
    if save_dir is not None:
        import os

        os.makedirs(save_dir, exist_ok=True)
        for name, fig in figures.items():
            fig.savefig(os.path.join(save_dir, f"{name}.png"), dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    return figures


def example_usage(show: bool = True) -> dict:
    figures = {
        "skr_vs_distance": plot_skr_vs_distance(),
        "skr_vs_jitter": plot_skr_vs_jitter(),
        "skr_vs_turbulence": plot_skr_vs_turbulence(),
        "skr_vs_cn2": plot_skr_vs_cn2(),
        "outage": plot_outage(),
        "finite_vs_asymptotic": plot_finite_vs_asymptotic(),
        "teff_vs_mc": plot_teff_vs_mc(),
        "transmittance_histogram": plot_transmittance_histogram(),
    }
    if show:
        plt.show()
    return figures


if __name__ == "__main__":
    example_usage(show=True)
