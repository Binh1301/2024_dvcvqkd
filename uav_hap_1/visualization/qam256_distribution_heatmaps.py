"""
Heatmap-style 256-QAM constellation plots for Uniform, Binomial, and MB.

Each distribution is saved as its own PDF:
  - output/qam256_uniform_heatmap.pdf
  - output/qam256_binomial_heatmap.pdf
  - output/qam256_mb_heatmap.pdf

The script also shows a 3-panel preview figure.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1.config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_NU_TILDE,
    )
    from uav_hap_1.zstar.base import build_constellation, build_probs_binomial, build_probs_mb, build_probs_uniform
else:
    from ..config import QAM_ALPHA0_BINOMIAL, QAM_ALPHA0_MB, QAM_ALPHA0_UNIFORM, QAM_NU_TILDE
    from ..zstar.base import build_constellation, build_probs_binomial, build_probs_mb, build_probs_uniform


SPEC = [
    ("Uniform", QAM_ALPHA0_BINOMIAL, build_probs_uniform(), "(a)", "qam256_uniform_heatmap.pdf"),
    ("Binomial", QAM_ALPHA0_BINOMIAL, build_probs_binomial(), "(b)", "qam256_binomial_heatmap.pdf"),
    ("MB", QAM_ALPHA0_MB, build_probs_mb(QAM_NU_TILDE), "(c)", "qam256_mb_heatmap.pdf"),
]

GLOBAL_VMAX = max(float(np.max(probs)) for _, _, probs, _, _ in SPEC)


def constellation_xy(alpha0: float) -> tuple[np.ndarray, np.ndarray]:
    alpha = np.asarray(build_constellation(alpha0), dtype=complex)
    return np.real(alpha), np.imag(alpha)


def axis_limit(alpha0: float) -> float:
    return 3.0


def plot_heatmap(
    label: str,
    alpha0: float,
    probs: np.ndarray,
    tag: str,
    out_path: Path,
    show_axes: bool = True,
) -> tuple[plt.Figure, plt.Axes]:
    x, y = constellation_xy(alpha0)
    lim = axis_limit(alpha0)

    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    sc = ax.scatter(
        x,
        y,
        c=probs,
        s=42,
        cmap="Blues",
        vmin=0.0,
        vmax=GLOBAL_VMAX,
        edgecolors="none",
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xticks([-2, 0, 2])
    ax.set_yticks([-2, 0, 2])
    ax.tick_params(labelsize=10)
    if show_axes:
        ax.set_xlabel("Amplitude Quadrature", fontsize=13)
        ax.set_ylabel("Phase Quadrature", fontsize=13)
    ax.text(0.5, -0.16, tag, transform=ax.transAxes, ha="center", va="top", fontsize=13)
    ax.text(0.5, 1.03, label, transform=ax.transAxes, ha="center", va="bottom", fontsize=12)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.92, pad=0.03)
    cbar.set_label("Symbol probability", fontsize=11)
    fig.savefig(out_path, dpi=240, bbox_inches="tight")
    return fig, ax


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    preview_fig, preview_axes = plt.subplots(1, 3, figsize=(13.2, 4.2), constrained_layout=True)
    saved_paths: list[Path] = []

    for ax, (label, alpha0, probs, tag, filename) in zip(preview_axes, SPEC):
        x, y = constellation_xy(alpha0)
        lim = axis_limit(alpha0)
        sc = ax.scatter(
            x,
            y,
            c=probs,
            s=28,
            cmap="Blues",
            vmin=0.0,
            vmax=GLOBAL_VMAX,
            edgecolors="none",
        )
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([-2, 0, 2])
        ax.tick_params(labelsize=9)
        ax.text(0.5, -0.16, tag, transform=ax.transAxes, ha="center", va="top", fontsize=12)
        ax.text(0.5, 1.03, label, transform=ax.transAxes, ha="center", va="bottom", fontsize=11)
        cbar = preview_fig.colorbar(sc, ax=ax, shrink=0.92, pad=0.02)
        cbar.set_label("Symbol probability", fontsize=10)

        single_path = out_dir / filename
        fig, _ = plot_heatmap(label, alpha0, probs, tag, single_path)
        plt.close(fig)
        saved_paths.append(single_path)

    preview_axes[0].set_ylabel("Phase Quadrature", fontsize=13)
    for ax in preview_axes:
        ax.set_xlabel("Amplitude Quadrature", fontsize=13)

    plt.show()
    plt.close(preview_fig)

    for path in saved_paths:
        print(f"Saved: {path}")


if __name__ == "__main__":
    main()
