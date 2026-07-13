"""
IEEE-style SKR vs channel parameters (V, w0, a, Cn^2) for Binomial, Uniform, MB.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace

import numpy as np
import matplotlib.pyplot as plt

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import ChannelParams, GeometryParams
    from uav_hap_1_sample.protocol.qam_protocol import (
        build_state_binomial,
        build_state_uniform,
        build_state_mb,
        compute_metrics,
    )
else:
    from ..channel.channel_model import channel
    from ..config import ChannelParams, GeometryParams
    from ..protocol.qam_protocol import (
        build_state_binomial,
        build_state_uniform,
        build_state_mb,
        compute_metrics,
    )


BASELINE = {
    "eta": 0.95,
    "eps": 0.001,
    "beta": 0.95,
    "v_el": 0.001,
}

DIST_CONFIGS = {
    "Binomial": {"alpha0": 2.0, "ncut": 45},
    "Uniform": {"alpha0": float(np.sqrt(12.0 / 17.0)), "ncut": 150},
    "MB": {"alpha0": 1.735, "ncut": 150, "nu_tilde": 0.1},
}

COLORS = {
    "Binomial": "tab:blue",
    "Uniform": "tab:orange",
    "MB": "tab:green",
}
LINESTYLES = {
    "Binomial": "-",
    "Uniform": "--",
    "MB": "-.",
}

DEFAULTS = {
    "V_km": 10.0,
    "w0_m": 0.0626,
    "a_m": 0.20,
    "Cn2": 1e-15,
}

N_SAMPLES = 15_000
MIN_SKR = 1e-10


@dataclass(frozen=True)
class DistSpec:
    name: str
    state: object
    color: str
    linestyle: str


def _ensure_output_dir() -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def _build_specs() -> list[DistSpec]:
    return [
        DistSpec(
            name="Binomial",
            state=build_state_binomial(DIST_CONFIGS["Binomial"]["alpha0"], DIST_CONFIGS["Binomial"]["ncut"]),
            color=COLORS["Binomial"],
            linestyle=LINESTYLES["Binomial"],
        ),
        DistSpec(
            name="Uniform",
            state=build_state_uniform(DIST_CONFIGS["Uniform"]["alpha0"], DIST_CONFIGS["Uniform"]["ncut"]),
            color=COLORS["Uniform"],
            linestyle=LINESTYLES["Uniform"],
        ),
        DistSpec(
            name="MB",
            state=build_state_mb(
                DIST_CONFIGS["MB"]["alpha0"], DIST_CONFIGS["MB"]["ncut"], DIST_CONFIGS["MB"]["nu_tilde"]
            ),
            color=COLORS["MB"],
            linestyle=LINESTYLES["MB"],
        ),
    ]


def _compute_skr(state, t_eff: float) -> float:
    metrics = compute_metrics(
        state,
        float(t_eff),
        float(BASELINE["eps"]),
        float(BASELINE["beta"]),
        float(BASELINE["eta"]),
        float(BASELINE["v_el"]),
    )
    return float(metrics.skr_raw)


def _channel_t_eff(channel_params: ChannelParams, geometry: GeometryParams, rng) -> float:
    fading = channel(geometry=geometry, channel_params=channel_params, N=N_SAMPLES, rng=rng)
    return float(fading["T_eff"])


def _progress(label: str, idx: int, total: int, step: int = 5) -> None:
    if total <= 0:
        return
    if idx % step == 0 or idx == total - 1:
        pct = int(100 * (idx + 1) / total)
        print(f"{label}: {pct:3d}%")


def _plot_panel(ax, x_vals, t_eff_vals, specs: list[DistSpec], xlabel: str, title: str, logx: bool = False):
    for spec in specs:
        skr_vals = np.array([_compute_skr(spec.state, t) for t in t_eff_vals], dtype=float)
        skr_plot = np.clip(skr_vals, MIN_SKR, None)
        ax.plot(
            x_vals,
            skr_plot,
            color=spec.color,
            linestyle=spec.linestyle,
            linewidth=1.8,
            label=spec.name,
        )
    if logx:
        ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(r"SKR (bits/use, log scale)")
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)


def _annotate_separation(ax, x_vals, t_eff_vals, specs: list[DistSpec], idx: int) -> None:
    if idx < 0 or idx >= len(x_vals):
        return
    y_vals = [max(_compute_skr(spec.state, t_eff_vals[idx]), MIN_SKR) for spec in specs]
    y_min = min(y_vals)
    y_max = max(y_vals)
    x = x_vals[idx]
    ax.annotate(
        "",
        xy=(x, y_min),
        xytext=(x, y_max),
        arrowprops=dict(arrowstyle="<->", color="0.25", lw=1.0),
    )
    ax.text(x, y_max, r"$\Delta$", fontsize=10, color="0.25", ha="left", va="bottom")


def _mark_baseline(ax, x_vals, t_eff_vals, specs: list[DistSpec], x_key: float, logx: bool = False):
    if logx:
        idx = int(np.argmin(np.abs(np.log10(x_vals) - np.log10(x_key))))
    else:
        idx = int(np.argmin(np.abs(x_vals - x_key)))
    x = float(x_vals[idx])
    for spec in specs:
        y = max(_compute_skr(spec.state, t_eff_vals[idx]), MIN_SKR)
        ax.scatter([x], [y], color=spec.color, s=22, zorder=4)


def main() -> None:
    _configure_style()
    specs = _build_specs()

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle("SKR vs Channel Parameters (IEEE-style)", fontsize=12)

    geometry = GeometryParams(H_HAP_m=20_000.0, H_UAV_m=0.0)
    rng = np.random.default_rng(202406)

    # Panel 1: SKR vs Visibility V
    v_vals = np.linspace(2.0, 50.0, 40)
    t_eff_v = []
    for i, v in enumerate(v_vals):
        _progress("Visibility sweep", i, len(v_vals))
        params = replace(ChannelParams(), visibility_km=float(v), xi_per_km=None)
        t_eff_v.append(_channel_t_eff(params, geometry, rng))
    t_eff_v = np.array(t_eff_v, dtype=float)
    ax = axes[0, 0]
    _plot_panel(ax, v_vals, t_eff_v, specs, r"$V$ (km)", "SKR vs Visibility $V$")
    _mark_baseline(ax, v_vals, t_eff_v, specs, DEFAULTS["V_km"])
    _annotate_separation(ax, v_vals, t_eff_v, specs, idx=len(v_vals) // 2)
    ax.text(0.03, 0.95, r"$V \uparrow \Rightarrow$ SKR $\uparrow$", transform=ax.transAxes, fontsize=9, va="top")

    # Panel 2: SKR vs beam waist w0
    w_vals = np.linspace(0.03, 0.20, 40)
    t_eff_w = []
    for i, w0 in enumerate(w_vals):
        _progress("Beam waist sweep", i, len(w_vals))
        params = replace(ChannelParams(), W0_m=float(w0))
        t_eff_w.append(_channel_t_eff(params, geometry, rng))
    t_eff_w = np.array(t_eff_w, dtype=float)
    ax = axes[0, 1]
    _plot_panel(ax, w_vals, t_eff_w, specs, r"$w_0$ (m)", "SKR vs Beam Waist $w_0$")
    _mark_baseline(ax, w_vals, t_eff_w, specs, DEFAULTS["w0_m"])
    _annotate_separation(ax, w_vals, t_eff_w, specs, idx=len(w_vals) // 2)
    ax.text(0.03, 0.95, r"$w_0 \uparrow \Rightarrow$ SKR $\uparrow$", transform=ax.transAxes, fontsize=9, va="top")

    # Panel 3: SKR vs aperture radius a
    a_vals = np.linspace(0.05, 0.40, 40)
    t_eff_a = []
    for i, a in enumerate(a_vals):
        _progress("Aperture sweep", i, len(a_vals))
        params = replace(ChannelParams(), a_m=float(a), D_r_m=None)
        t_eff_a.append(_channel_t_eff(params, geometry, rng))
    t_eff_a = np.array(t_eff_a, dtype=float)
    ax = axes[1, 0]
    _plot_panel(ax, a_vals, t_eff_a, specs, r"$a$ (m)", "SKR vs Aperture Radius $a$")
    _mark_baseline(ax, a_vals, t_eff_a, specs, DEFAULTS["a_m"])
    _annotate_separation(ax, a_vals, t_eff_a, specs, idx=len(a_vals) // 2)
    ax.text(0.03, 0.95, r"$a \uparrow \Rightarrow$ SKR $\uparrow$", transform=ax.transAxes, fontsize=9, va="top")

    # Panel 4: SKR vs turbulence strength Cn2
    cn_vals = np.logspace(-17, -13, 40)
    t_eff_cn = []
    for i, cn2 in enumerate(cn_vals):
        _progress("Turbulence sweep", i, len(cn_vals))
        params = replace(ChannelParams(), Cn2=float(cn2), use_hv_turbulence=False)
        t_eff_cn.append(_channel_t_eff(params, geometry, rng))
    t_eff_cn = np.array(t_eff_cn, dtype=float)
    ax = axes[1, 1]
    _plot_panel(
        ax,
        cn_vals,
        t_eff_cn,
        specs,
        r"$C_n^2$ (m$^{-2/3}$)",
        r"SKR vs Turbulence $C_n^2$",
        logx=True,
    )
    _mark_baseline(ax, cn_vals, t_eff_cn, specs, DEFAULTS["Cn2"], logx=True)
    _annotate_separation(ax, cn_vals, t_eff_cn, specs, idx=len(cn_vals) // 2)
    ax.text(0.03, 0.95, r"$C_n^2 \uparrow \Rightarrow$ SKR $\downarrow$", transform=ax.transAxes, fontsize=9, va="top")

    axes[0, 0].legend(loc="best", fontsize=9, frameon=True)

    fig.tight_layout()
    out_path = os.path.join(_ensure_output_dir(), "skr_ieee_channel_params.png")
    fig.savefig(out_path, dpi=300, facecolor="white")
    plt.show()


if __name__ == "__main__":
    main()
