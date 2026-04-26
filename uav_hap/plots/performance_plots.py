from dataclasses import replace
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

from ..channel.channel_model import channel
from ..config import ChannelParams, FiniteSizeParams, GeometryParams, MonteCarloParams, NoiseParams, SecurityParams
from ..main import simulate_uav_hap_cvqkd
from ..protocols.gm import noise, skr

LINE_STYLES = ["-", "--", "-."]
MARKERS = ["o", "s", "^", "d", "v", "P", "X"]


def _default_distance_grid_m() -> np.ndarray:
    return np.linspace(5_000.0, 60_000.0, 20)


def _default_jitter_grid_m() -> np.ndarray:
    return np.linspace(0.005, 0.05, 18)


def _default_turbulence_grid_m() -> np.ndarray:
    return np.linspace(0.002, 0.04, 18)


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


def example_usage(show: bool = True) -> dict:
    figures = {
        "skr_vs_distance": plot_skr_vs_distance(),
        "skr_vs_jitter": plot_skr_vs_jitter(),
        "skr_vs_turbulence": plot_skr_vs_turbulence(),
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
