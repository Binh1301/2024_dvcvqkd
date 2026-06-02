from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle, FancyArrowPatch
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError("matplotlib is required for plotting.") from exc

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1.channel.channel_model import channel
    from uav_hap_1.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_MB,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_MB,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from uav_hap_1.protocol.qam_protocol import build_state_mb, compute_metrics
else:
    from ..channel.channel_model import channel
    from ..config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_MB,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_MB,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from ..protocol.qam_protocol import build_state_mb, compute_metrics


@dataclass(frozen=True)
class PlotSettings:
    v_min: float = 5.0
    v_max: float = 50.0
    v_points: int = 18
    n_samples: int = 3000
    seed: int = 123
    w0_values: tuple[float, ...] = (0.04, 0.06, 0.08)
    a_values: tuple[float, ...] = (0.05, 0.075)
    cn2_values: tuple[float, ...] = (1e-16, 3e-16, 1e-15, 3e-15)


def _skr_from_t_eff(state, t_eff: float) -> float:
    metrics = compute_metrics(
        state,
        float(t_eff),
        float(QAM_EPS),
        float(QAM_BETA),
        float(QAM_ETA),
        float(QAM_V_EL),
    )
    return float(metrics.skr_raw)


def _compute_curve(
    v_values: np.ndarray,
    w0_m: float,
    a_m: float,
    cn2: float,
    rng_seed: int,
    n_samples: int,
) -> np.ndarray:
    geometry = GeometryParams()
    state = build_state_mb(float(QAM_ALPHA0_MB), int(QAM_NCUT_MB), float(QAM_NU_TILDE))

    skr_values = []
    for v in v_values:
        params = ChannelParams(
            W0_m=float(w0_m),
            a_m=float(a_m),
            Cn2=float(cn2),
            visibility_km=float(v),
            xi_per_km=None,
        )
        rng = np.random.default_rng(rng_seed + int(1000 * v) + int(100 * w0_m) + int(10 * a_m))
        t_eff = channel(geometry, params, n_samples, rng)["T_eff"]
        skr_values.append(_skr_from_t_eff(state, t_eff))
    return np.array(skr_values, dtype=float)


def _add_inset(fig: plt.Figure) -> None:
    ax_in = fig.add_axes([0.70, 0.60, 0.26, 0.30])
    ax_in.set_facecolor("white")

    nx, ny = 300, 140
    x = np.linspace(0.0, 1.0, nx)
    y = np.linspace(-0.22, 0.22, ny)
    X, Y = np.meshgrid(x, y)

    fog = np.linspace(0.08, 0.35, nx)
    ax_in.imshow(np.tile(fog, (ny, 1)), extent=[0, 1, y.min(), y.max()],
                 cmap="Greys", alpha=0.30, origin="lower", aspect="auto")

    w0 = 0.05
    w = w0 * np.sqrt(1 + (x / 0.25) ** 2)
    I = np.exp(-2 * (Y**2) / (w**2))
    I = I / I.max()
    ax_in.imshow(10 * np.log10(np.maximum(I, 1e-4)),
                 extent=[0, 1, y.min(), y.max()], cmap="viridis", origin="lower", aspect="auto", alpha=0.85)

    ax_in.plot(x, w, color="deepskyblue", lw=1.0)
    ax_in.plot(x, -w, color="deepskyblue", lw=1.0)
    ax_in.plot([0, 1], [0, 0], color="cyan", lw=0.8, alpha=0.7)

    ax_in.add_patch(Circle((0.0, 0.0), 0.012, color="black", alpha=0.8))
    ax_in.add_patch(Circle((1.0, 0.0), 0.06, edgecolor="black", facecolor="none", lw=1.2))
    ax_in.add_patch(FancyArrowPatch((0.05, w0), (0.05, -w0),
                                    arrowstyle="<->", mutation_scale=8, color="white"))

    for _ in range(18):
        cx = float(np.random.uniform(0.15, 0.9))
        cy = float(np.random.uniform(-0.16, 0.16))
        r = float(np.random.uniform(0.01, 0.03))
        ax_in.add_patch(Circle((cx, cy), r, edgecolor="white", facecolor="none", lw=0.6, alpha=0.18))

    ax_in.text(0.06, 0.14, "V", color="white", fontsize=8)
    ax_in.text(0.08, 0.0, r"$w_0$", color="white", fontsize=8, va="center")
    ax_in.text(0.95, 0.09, r"$a$", ha="right", fontsize=8)
    ax_in.text(0.58, -0.17, r"$C_n^2$", color="white", fontsize=8)

    ax_in.set_xticks([])
    ax_in.set_yticks([])
    for spine in ax_in.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)


def plot_skr_vs_visibility(out_dir: Path, settings: PlotSettings | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = settings or PlotSettings()

    v_values = np.linspace(cfg.v_min, cfg.v_max, cfg.v_points)

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.2), constrained_layout=True)
    axes = axes.flatten()

    colors = ["tab:blue", "tab:green", "tab:purple", "tab:orange"]
    linestyles = ["-", "--"]

    for idx, cn2 in enumerate(cfg.cn2_values):
        ax = axes[idx]
        for w_idx, w0 in enumerate(cfg.w0_values):
            for a_idx, a in enumerate(cfg.a_values):
                skr = _compute_curve(
                    v_values,
                    w0_m=w0,
                    a_m=a,
                    cn2=cn2,
                    rng_seed=cfg.seed,
                    n_samples=cfg.n_samples,
                )
                label = f"$w_0$={w0:.2f} m, $a$={a:.3f} m"
                ax.plot(
                    v_values,
                    skr,
                    color=colors[w_idx % len(colors)],
                    linestyle=linestyles[a_idx % len(linestyles)],
                    lw=1.9,
                    label=label,
                )
                ax.scatter([v_values[-1]], [skr[-1]], color=colors[w_idx % len(colors)], s=18, zorder=3)

        ax.set_title(rf"$C_n^2 = {cn2:.0e}\ \mathrm{{m}}^{{-2/3}}$")
        ax.set_xlabel(r"Visibility $V$ (km)")
        ax.set_ylabel("SKR (bits/use)")
        ax.grid(alpha=0.3)

    legend_lines = []
    legend_labels = []
    for w_idx, w0 in enumerate(cfg.w0_values):
        legend_lines.append(Line2D([0], [0], color=colors[w_idx % len(colors)], lw=2))
        legend_labels.append(rf"$w_0={w0:.2f}\,\mathrm{{m}}$")
    for a_idx, a in enumerate(cfg.a_values):
        legend_lines.append(Line2D([0], [0], color="black", lw=2, linestyle=linestyles[a_idx]))
        legend_labels.append(rf"$a={a:.3f}\,\mathrm{{m}}$")

    axes[0].legend(
        legend_lines,
        legend_labels,
        loc="upper left",
        fontsize=8,
        frameon=False,
        ncol=2,
    )

    fig.suptitle("SKR vs Visibility with Beam & Aperture Variations", fontsize=13)
    _add_inset(fig)

    out_path = out_dir / "skr_vs_visibility_fso.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path

