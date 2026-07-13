"""
Visualize SKR sweeps for QAM-256 binomial across key parameters.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import (
        ChannelParams,
        EPS,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_V_EL,
    )
    from uav_hap_1_sample.protocol.qam_protocol import build_state_binomial, compute_metrics
else:
    from ..channel.channel_model import channel
    from ..config import (
        ChannelParams,
        EPS,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_V_EL,
    )
    from ..protocol.qam_protocol import build_state_binomial, compute_metrics


N_SAMPLES = 30_000


def _compute_skr(state, T_eff: float, eps: float, beta: float, eta: float, v_el: float) -> float:
    metrics = compute_metrics(state, float(T_eff), float(eps), float(beta), float(eta), float(v_el))
    return float(metrics.skr)


def _t_eff_for_params(
    geom: GeometryParams,
    ch_params: ChannelParams,
    rng: np.random.Generator,
    L_km: float | None = None,
) -> float:
    L_override_m = None if L_km is None else float(L_km) * 1000.0
    fading = channel(
        geometry=geom,
        channel_params=ch_params,
        N=N_SAMPLES,
        rng=rng,
        L_override_m=L_override_m,
    )
    return float(fading["T_eff"])


def _zero_crossing(x: np.ndarray, y: np.ndarray) -> float | None:
    positive = y > 0
    if not np.any(positive):
        return None
    if np.all(positive):
        return float(x[-1])
    for idx in range(1, len(x)):
        if positive[idx - 1] and not positive[idx]:
            x0, x1 = float(x[idx - 1]), float(x[idx])
            y0, y1 = float(y[idx - 1]), float(y[idx])
            if abs(y1 - y0) <= EPS:
                return x0
            return float(x0 + (0.0 - y0) * (x1 - x0) / (y1 - y0))
    return float(x[positive][-1])


def _mark_positive_region(ax, x: np.ndarray, y: np.ndarray) -> None:
    ax.fill_between(x, 0.0, y, where=y > 0, alpha=0.2, interpolate=True)


def main() -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("matplotlib is required for plotting.") from exc

    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "legend.fontsize": 10,
        }
    )

    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    geom = GeometryParams()
    ch_base = ChannelParams()
    rng = np.random.default_rng(42)

    state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)

    summary_lines: list[str] = []

    # 1. SKR vs eps
    eps_values = np.logspace(np.log10(1e-4), np.log10(1e-1), 50)
    T_levels = [0.1, 0.15, 0.2, 0.3]

    fig, ax = plt.subplots(figsize=(7.6, 5.2), constrained_layout=True)
    for T_eff in T_levels:
        skr_vals = np.array([_compute_skr(state, T_eff, eps, QAM_BETA, QAM_ETA, QAM_V_EL) for eps in eps_values])
        ax.plot(eps_values, skr_vals, lw=2.0, label=f"T_eff={T_eff:.2f}")
        eps_max = _zero_crossing(eps_values, skr_vals)
        if eps_max is not None:
            ax.scatter([eps_max], [0.0], s=40, zorder=3)
            summary_lines.append(f"eps_max = {eps_max:.4g} at T_eff={T_eff:.2f}")
    ax.set_xscale("log")
    ax.set_xlabel("Excess noise eps")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("SKR vs eps (QAM-256 binomial)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    fig.savefig(out_dir / "skr_vs_eps.png", dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    # 2. SKR vs L
    L_values = np.linspace(1.0, 100.0, 50)
    vis_levels = [5, 10, 23]

    fig, ax = plt.subplots(figsize=(7.6, 5.2), constrained_layout=True)
    for visibility in vis_levels:
        ch_params = replace(ch_base, visibility_km=float(visibility), xi_per_km=None)
        skr_vals = []
        for L_km in L_values:
            T_eff = _t_eff_for_params(geom, ch_params, rng, L_km=L_km)
            skr_vals.append(_compute_skr(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL))
        skr_vals = np.asarray(skr_vals, dtype=float)
        ax.plot(L_values, skr_vals, lw=2.0, label=f"visibility={visibility} km")
        L_max = _zero_crossing(L_values, skr_vals)
        if L_max is not None:
            ax.scatter([L_max], [0.0], s=40, zorder=3)
            summary_lines.append(f"L_max = {L_max:.2f} km at visibility={visibility} km")
    ax.set_xlabel("Link distance L (km)")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("SKR vs L (QAM-256 binomial)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    fig.savefig(out_dir / "skr_vs_L.png", dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    # 3. SKR vs key channel parameters
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0), constrained_layout=True)

    a_values = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40])
    skr_vals = []
    for a_m in a_values:
        ch_params = replace(ch_base, a_m=float(a_m))
        T_eff = _t_eff_for_params(geom, ch_params, rng)
        skr_vals.append(_compute_skr(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL))
    skr_vals = np.asarray(skr_vals, dtype=float)
    axes[0, 0].plot(a_values, skr_vals, lw=2.0)
    _mark_positive_region(axes[0, 0], a_values, skr_vals)
    axes[0, 0].set_xlabel("Aperture radius a_m (m)")
    axes[0, 0].set_ylabel("SKR (bits/use)")
    axes[0, 0].set_title("SKR vs aperture radius")
    axes[0, 0].grid(alpha=0.3)
    a_thr = _zero_crossing(a_values, skr_vals)
    if a_thr is not None:
        axes[0, 0].scatter([a_thr], [0.0], s=35)
        summary_lines.append(f"a_m threshold ~ {a_thr:.3f} m")

    w0_values = np.array([0.03, 0.05, 0.08, 0.10, 0.15, 0.20])
    skr_vals = []
    for w0_m in w0_values:
        ch_params = replace(ch_base, W0_m=float(w0_m))
        T_eff = _t_eff_for_params(geom, ch_params, rng)
        skr_vals.append(_compute_skr(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL))
    skr_vals = np.asarray(skr_vals, dtype=float)
    axes[0, 1].plot(w0_values, skr_vals, lw=2.0)
    _mark_positive_region(axes[0, 1], w0_values, skr_vals)
    axes[0, 1].set_xlabel("Beam waist W0_m (m)")
    axes[0, 1].set_ylabel("SKR (bits/use)")
    axes[0, 1].set_title("SKR vs beam waist")
    axes[0, 1].grid(alpha=0.3)
    w0_thr = _zero_crossing(w0_values, skr_vals)
    if w0_thr is not None:
        axes[0, 1].scatter([w0_thr], [0.0], s=35)
        summary_lines.append(f"W0_m threshold ~ {w0_thr:.3f} m")

    sigma_values = np.array([0.5e-3, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3])
    base_sigma_total = float(
        np.sqrt(
            ch_base.sigma_theta_rad**2
            + ch_base.sigma_phi_rad**2
            + ch_base.sigma_psi_rad**2
        )
    )
    skr_vals = []
    for sigma_total in sigma_values:
        scale = float(sigma_total) / max(base_sigma_total, EPS)
        ch_params = replace(
            ch_base,
            sigma_theta_rad=float(ch_base.sigma_theta_rad) * scale,
            sigma_phi_rad=float(ch_base.sigma_phi_rad) * scale,
            sigma_psi_rad=float(ch_base.sigma_psi_rad) * scale,
        )
        T_eff = _t_eff_for_params(geom, ch_params, rng)
        skr_vals.append(_compute_skr(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL))
    skr_vals = np.asarray(skr_vals, dtype=float)
    axes[1, 0].plot(sigma_values, skr_vals, lw=2.0)
    _mark_positive_region(axes[1, 0], sigma_values, skr_vals)
    axes[1, 0].set_xlabel("Pointing error sigma_total (rad)")
    axes[1, 0].set_ylabel("SKR (bits/use)")
    axes[1, 0].set_title("SKR vs pointing error")
    axes[1, 0].grid(alpha=0.3)
    axes[1, 0].set_xscale("log")
    sigma_thr = _zero_crossing(sigma_values, skr_vals)
    if sigma_thr is not None:
        axes[1, 0].scatter([sigma_thr], [0.0], s=35)
        summary_lines.append(f"sigma_total threshold ~ {sigma_thr:.2e} rad")

    vis_values = np.array([2, 5, 10, 15, 23, 50], dtype=float)
    skr_vals = []
    for visibility in vis_values:
        ch_params = replace(ch_base, visibility_km=float(visibility), xi_per_km=None)
        T_eff = _t_eff_for_params(geom, ch_params, rng)
        skr_vals.append(_compute_skr(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL))
    skr_vals = np.asarray(skr_vals, dtype=float)
    axes[1, 1].plot(vis_values, skr_vals, lw=2.0)
    _mark_positive_region(axes[1, 1], vis_values, skr_vals)
    axes[1, 1].set_xlabel("Visibility (km)")
    axes[1, 1].set_ylabel("SKR (bits/use)")
    axes[1, 1].set_title("SKR vs visibility")
    axes[1, 1].grid(alpha=0.3)
    vis_thr = _zero_crossing(vis_values, skr_vals)
    if vis_thr is not None:
        axes[1, 1].scatter([vis_thr], [0.0], s=35)
        summary_lines.append(f"visibility threshold ~ {vis_thr:.2f} km")

    fig.savefig(out_dir / "skr_vs_channel_params.png", dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    # 4. Heatmap SKR(T_eff, eps)
    T_grid = np.linspace(0.05, 0.5, 30)
    eps_grid = np.logspace(np.log10(1e-4), np.log10(0.05), 30)
    skr_grid = np.zeros((len(eps_grid), len(T_grid)), dtype=float)
    for i, eps in enumerate(eps_grid):
        for j, T_eff in enumerate(T_grid):
            skr_grid[i, j] = _compute_skr(state, T_eff, eps, QAM_BETA, QAM_ETA, QAM_V_EL)

    fig, ax = plt.subplots(figsize=(7.6, 5.6), constrained_layout=True)
    T_mesh, eps_mesh = np.meshgrid(T_grid, eps_grid)
    skr_clipped = np.maximum(skr_grid, 0.0)
    pcm = ax.pcolormesh(T_mesh, eps_mesh, skr_clipped, cmap="coolwarm", shading="auto")
    ax.contour(T_mesh, eps_mesh, skr_grid, levels=[0.0], colors="k", linewidths=1.0)
    ax.scatter([0.082], [0.001], color="black", s=45, label="(T=0.082, eps=0.001)")
    ax.set_yscale("log")
    ax.set_xlabel("T_eff")
    ax.set_ylabel("eps")
    ax.set_title("SKR heatmap (QAM-256 binomial)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, loc="lower left")
    fig.colorbar(pcm, ax=ax, label="SKR (bits/use)")
    fig.savefig(out_dir / "skr_heatmap_T_eps.png", dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    if summary_lines:
        print("SKR thresholds (approx):")
        for line in summary_lines:
            print(f"- {line}")


if __name__ == "__main__":
    main()
