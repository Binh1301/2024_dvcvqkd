"""
Publication-quality plots for SKR = 0 boundary analysis.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from typing import Callable

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import ChannelParams, GeometryParams
    from uav_hap_1_sample.protocol.qam_protocol import build_state_binomial, compute_metrics
else:
    from ..channel.channel_model import channel
    from ..config import ChannelParams, GeometryParams
    from ..protocol.qam_protocol import build_state_binomial, compute_metrics


BASELINE = {
    "eta": 0.95,
    "eps": 0.001,
    "v_el": 0.001,
    "alpha0": 2.0,
    "beta": 0.95,
    "ncut": 45,
}
T_EFF_BASELINE = 0.132129
XI_BASELINE = 0.068559
T_EFF_CURRENT = 0.082
H_HAP_DEFAULT = 20_000.0

SKR_TOL = 1e-8
N_SAMPLES = 30_000


def _compute_skr(state, t_eff: float, eps: float, beta: float, eta: float, v_el: float) -> float:
    metrics = compute_metrics(state, float(t_eff), float(eps), float(beta), float(eta), float(v_el))
    return float(metrics.skr_raw)


def _bisect_t_eff(
    state,
    eps: float,
    beta: float,
    eta: float,
    v_el: float,
    t_min: float = 0.01,
    t_max: float = 0.5,
) -> float:
    s_min = _compute_skr(state, t_min, eps, beta, eta, v_el)
    s_max = _compute_skr(state, t_max, eps, beta, eta, v_el)
    if s_min > 0 and s_max > 0:
        return float("nan")
    if s_min < 0 and s_max < 0:
        return float("nan")
    for _ in range(120):
        t_mid = 0.5 * (t_min + t_max)
        skr = _compute_skr(state, t_mid, eps, beta, eta, v_el)
        if abs(skr) < SKR_TOL:
            return float(t_mid)
        if skr > 0:
            t_max = t_mid
        else:
            t_min = t_mid
    return float(0.5 * (t_min + t_max))


def _progress(label: str, idx: int, total: int, step: int = 5) -> None:
    if total <= 0:
        return
    if idx % step == 0 or idx == total - 1:
        pct = int(100 * (idx + 1) / total)
        print(f"{label}: {pct:3d}%")


def _ensure_output_dir() -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _build_state_alpha(alpha0: float) -> tuple:
    ncut = max(45, int(3.0 * float(alpha0) ** 2) + 10)
    return build_state_binomial(float(alpha0), int(ncut))


def _sensitivity_1d_plots() -> tuple[dict[str, float], np.ndarray]:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    fig.suptitle("SKR=0 Boundary Sensitivity (1D)", fontsize=12)

    baseline_state = build_state_binomial(BASELINE["alpha0"], BASELINE["ncut"])

    eps_values = np.logspace(np.log10(1e-4), np.log10(0.1), 30)
    eta_values = np.linspace(0.5, 0.99, 30)
    v_el_values = np.linspace(0.0, 0.05, 30)
    alpha_values = np.linspace(1.5, 4.0, 20)
    beta_values = np.linspace(0.8, 1.0, 20)

    t_eps = np.array(
        [
            _bisect_t_eff(baseline_state, e, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
            for e in eps_values
        ],
        dtype=float,
    )

    t_eta = np.array(
        [
            _bisect_t_eff(baseline_state, BASELINE["eps"], BASELINE["beta"], e, BASELINE["v_el"])
            for e in eta_values
        ],
        dtype=float,
    )

    t_vel = np.array(
        [
            _bisect_t_eff(baseline_state, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], v)
            for v in v_el_values
        ],
        dtype=float,
    )

    t_alpha_full = []
    for a in alpha_values:
        state = _build_state_alpha(a)
        t_min = _bisect_t_eff(state, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
        if np.isnan(t_min):
            break
        t_alpha_full.append(t_min)
    t_alpha = np.asarray(t_alpha_full, dtype=float)
    alpha_values = alpha_values[: len(t_alpha)]

    t_beta = np.array(
        [
            _bisect_t_eff(baseline_state, BASELINE["eps"], b, BASELINE["eta"], BASELINE["v_el"])
            for b in beta_values
        ],
        dtype=float,
    )

    ax = axes[0, 0]
    ax.plot(eps_values, t_eps, color="tab:blue")
    ax.set_xscale("log")
    ax.set_title("T_min vs eps")
    ax.set_xlabel("eps")
    ax.set_ylabel("T_eff_min")
    ax.axhspan(0, T_EFF_CURRENT, color="0.9", label="Current T_eff")
    ax.scatter([BASELINE["eps"]], [T_EFF_BASELINE], color="red", zorder=3)
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    ax = axes[0, 1]
    ax.plot(eta_values, t_eta, color="tab:blue")
    ax.set_title("T_min vs eta")
    ax.set_xlabel("eta")
    ax.set_ylabel("T_eff_min")
    ax.axhspan(0, T_EFF_CURRENT, color="0.9")
    ax.scatter([BASELINE["eta"]], [T_EFF_BASELINE], color="red", zorder=3)
    ax.grid(alpha=0.3)

    ax = axes[0, 2]
    ax.plot(v_el_values, t_vel, color="tab:blue")
    ax.set_title("T_min vs v_el")
    ax.set_xlabel("v_el")
    ax.set_ylabel("T_eff_min")
    ax.scatter([BASELINE["v_el"]], [T_EFF_BASELINE], color="red", zorder=3)
    ax.grid(alpha=0.3)

    ax = axes[1, 0]
    ax.plot(alpha_values, t_alpha, color="tab:blue")
    ax.set_title("T_min vs alpha0")
    ax.set_xlabel("alpha0")
    ax.set_ylabel("T_eff_min")
    ax.scatter([BASELINE["alpha0"]], [T_EFF_BASELINE], color="red", zorder=3)
    ax.grid(alpha=0.3)

    def alpha_to_va(x):
        return 0.5 * np.asarray(x) ** 2

    def va_to_alpha(x):
        return np.sqrt(2.0 * np.asarray(x))

    sec = ax.secondary_xaxis("top", functions=(alpha_to_va, va_to_alpha))
    sec.set_xlabel("VA = alpha0^2 / 2")

    ax = axes[1, 1]
    ax.plot(beta_values, t_beta, color="tab:blue")
    ax.set_title("T_min vs beta")
    ax.set_xlabel("beta")
    ax.set_ylabel("T_eff_min")
    ax.scatter([BASELINE["beta"]], [T_EFF_BASELINE], color="red", zorder=3)
    ax.grid(alpha=0.3)

    def _safe_range(arr: np.ndarray) -> float:
        arr = arr[~np.isnan(arr)]
        if arr.size == 0:
            return 0.0
        return float(np.max(arr) - np.min(arr))

    deltas = {
        "eps": _safe_range(t_eps),
        "eta": _safe_range(t_eta),
        "v_el": _safe_range(t_vel),
        "alpha0": _safe_range(t_alpha),
        "beta": _safe_range(t_beta),
    }
    labels = sorted(deltas, key=deltas.get, reverse=True)
    values = np.array([deltas[k] for k in labels], dtype=float)
    norm = (values - values.min()) / max(values.max() - values.min(), 1e-9)
    colors = [plt.cm.RdYlBu(1.0 - n) for n in norm]

    ax = axes[1, 2]
    ax.barh(labels, values, color=colors)
    ax.set_title("Sensitivity (ΔT_min)")
    ax.set_xlabel("ΔT_eff_min")
    ax.grid(alpha=0.3, axis="x")
    ax.invert_yaxis()

    fig.tight_layout()
    out_dir = _ensure_output_dir()
    fig.savefig(os.path.join(out_dir, "skr_sensitivity_1d.png"), dpi=300)
    return deltas, baseline_state


def _compute_heatmap(
    x_vals: np.ndarray,
    y_vals: np.ndarray,
    func: Callable[[float, float], float],
    label: str,
) -> np.ndarray:
    z = np.zeros((len(y_vals), len(x_vals)), dtype=float)
    for i, y in enumerate(y_vals):
        _progress(label, i, len(y_vals), step=6)
        for j, x in enumerate(x_vals):
            z[i, j] = func(x, y)
    return z


def _heatmaps_2d(state) -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle("SKR_raw Heatmaps", fontsize=12)

    t_vals = np.linspace(0.05, 0.4, 40)
    eps_vals = np.logspace(np.log10(1e-4), np.log10(0.05), 40)
    eta_vals = np.linspace(0.5, 0.99, 40)

    z_teps = _compute_heatmap(
        t_vals,
        eps_vals,
        lambda t, eps: _compute_skr(state, t, eps, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"]),
        "Heatmap T_eff vs eps",
    )
    z_teta = _compute_heatmap(
        t_vals,
        eta_vals,
        lambda t, eta: _compute_skr(state, t, BASELINE["eps"], BASELINE["beta"], eta, BASELINE["v_el"]),
        "Heatmap T_eff vs eta",
    )
    z_eps_eta = _compute_heatmap(
        eps_vals,
        eta_vals,
        lambda eps, eta: _compute_skr(state, T_EFF_BASELINE, eps, BASELINE["beta"], eta, BASELINE["v_el"]),
        "Heatmap eps vs eta",
    )

    def draw(ax, x, y, z, xscale="linear", yscale="linear", title="", xlabel="", ylabel=""):
        z_min = float(np.min(z))
        z_max = float(np.max(z))
        if z_min < 0.0 < z_max:
            norm = TwoSlopeNorm(vmin=z_min, vcenter=0.0, vmax=z_max)
        else:
            norm = None
        mesh = ax.pcolormesh(x, y, z, shading="auto", cmap="RdYlGn", norm=norm)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        ax.grid(alpha=0.3)
        fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04)
        ax.contour(x, y, z, levels=[0.0], colors="black", linewidths=1.6)

    draw(
        axes[0],
        t_vals,
        eps_vals,
        z_teps,
        xscale="linear",
        yscale="log",
        title="SKR(T_eff, eps)",
        xlabel="T_eff",
        ylabel="eps",
    )
    axes[0].scatter([T_EFF_CURRENT], [BASELINE["eps"]], marker="*", s=90, color="black", zorder=4)
    axes[0].scatter([T_EFF_BASELINE], [BASELINE["eps"]], marker="o", s=60, color="black", zorder=4)

    draw(
        axes[1],
        t_vals,
        eta_vals,
        z_teta,
        title="SKR(T_eff, eta)",
        xlabel="T_eff",
        ylabel="eta",
    )
    axes[1].scatter([T_EFF_CURRENT], [BASELINE["eta"]], marker="*", s=90, color="black", zorder=4)
    axes[1].scatter([T_EFF_BASELINE], [BASELINE["eta"]], marker="o", s=60, color="black", zorder=4)

    draw(
        axes[2],
        eps_vals,
        eta_vals,
        z_eps_eta,
        xscale="log",
        title="SKR(eps, eta) @ T_eff=0.132",
        xlabel="eps",
        ylabel="eta",
    )
    axes[2].scatter([BASELINE["eps"]], [BASELINE["eta"]], marker="*", s=90, color="black", zorder=4)
    axes[2].scatter([BASELINE["eps"]], [BASELINE["eta"]], marker="o", s=60, color="black", zorder=4)

    fig.tight_layout()
    out_dir = _ensure_output_dir()
    fig.savefig(os.path.join(out_dir, "skr_heatmap_2d.png"), dpi=300)


def _channel_mapping_plots(state) -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Channel Mapping", fontsize=12)

    geometry = GeometryParams(H_HAP_m=H_HAP_DEFAULT, H_UAV_m=0.0)
    base_channel = ChannelParams()
    etas = [0.6, 0.8, 0.95]
    colors = ["tab:orange", "tab:green", "tab:blue"]

    # SKR vs L
    L_km = np.linspace(1.0, 30.0, 50)
    t_eff_L = np.array(
        [
            channel(geometry=geometry, channel_params=base_channel, N=N_SAMPLES, L_override_m=l * 1000.0)[
                "T_eff"
            ]
            for l in L_km
        ],
        dtype=float,
    )
    ax = axes[0]
    for eta, color in zip(etas, colors):
        skr_vals = np.array(
            [
                _compute_skr(state, t_eff, BASELINE["eps"], BASELINE["beta"], eta, BASELINE["v_el"])
                for t_eff in t_eff_L
            ],
            dtype=float,
        )
        ax.plot(L_km, skr_vals, color=color, label=f"eta={eta:.2f}")
        if np.any(skr_vals > 0) and np.any(skr_vals < 0):
            idx = np.where(skr_vals > 0)[0][-1]
            if idx + 1 < len(L_km):
                l0, l1 = L_km[idx], L_km[idx + 1]
                s0, s1 = skr_vals[idx], skr_vals[idx + 1]
                l_max = l0 + (0 - s0) * (l1 - l0) / (s1 - s0)
                ax.scatter([l_max], [0], color=color, zorder=4)
    ax.axhspan(np.min(ax.get_ylim()), 0.0, color="0.9", zorder=0)
    ax.set_xlabel("L (km)")
    ax.set_ylabel("SKR_raw")
    ax.set_title("SKR vs L")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    ax2 = ax.twinx()
    ax2.plot(L_km, t_eff_L, color="0.4", linestyle="--", label="T_eff")
    ax2.set_ylabel("T_eff")
    ax2.tick_params(axis="y", labelsize=9)

    # SKR vs visibility
    ax = axes[1]
    vis_vals = np.linspace(5.0, 50.0, 50)
    for eta, color in zip(etas, colors):
        t_eff_vis = np.array(
            [
                channel(
                    geometry=geometry,
                    channel_params=replace(base_channel, visibility_km=float(v), xi_per_km=None),
                    N=N_SAMPLES,
                )["T_eff"]
                for v in vis_vals
            ],
            dtype=float,
        )
        skr_vals = np.array(
            [
                _compute_skr(state, t_eff, BASELINE["eps"], BASELINE["beta"], eta, BASELINE["v_el"])
                for t_eff in t_eff_vis
            ],
            dtype=float,
        )
        ax.plot(vis_vals, skr_vals, color=color, label=f"eta={eta:.2f}")
        if np.any(skr_vals > 0) and np.any(skr_vals < 0):
            idx = np.where(skr_vals > 0)[0][0]
            if idx > 0:
                v0, v1 = vis_vals[idx - 1], vis_vals[idx]
                s0, s1 = skr_vals[idx - 1], skr_vals[idx]
                v_min = v0 + (0 - s0) * (v1 - v0) / (s1 - s0)
                ax.scatter([v_min], [0], color=color, zorder=4)
    ax.axhspan(np.min(ax.get_ylim()), 0.0, color="0.9", zorder=0)
    ax.set_xlabel("Visibility (km)")
    ax.set_ylabel("SKR_raw")
    ax.set_title("SKR vs Visibility (H_HAP=20 km)")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    fig.tight_layout()
    out_dir = _ensure_output_dir()
    fig.savefig(os.path.join(out_dir, "skr_channel_mapping.png"), dpi=300)


def main() -> None:
    deltas, baseline_state = _sensitivity_1d_plots()
    _heatmaps_2d(baseline_state)
    _channel_mapping_plots(baseline_state)
    plt.show()


if __name__ == "__main__":
    main()
