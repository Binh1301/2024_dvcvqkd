"""
Compare Tr(C) and w for Uniform, Binomial, and Maxwell-Boltzmann 256-QAM.

Outputs:
  - output/compare_trc_three_distributions.pdf
  - output/compare_w_three_distributions.pdf
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
    )
    from uav_hap_1_sample.protocol.qam_protocol import build_state_binomial, build_state_mb, build_state_uniform
else:
    from ..config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
    )
    from ..protocol.qam_protocol import build_state_binomial, build_state_mb, build_state_uniform


def fmt(v: float) -> str:
    return f"{v:.10f}"


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    states = [
        ("Uniform", build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)),
        ("Binomial", build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)),
        ("MB", build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)),
    ]

    labels = [name for name, _ in states]
    tr_c = np.array([state.tr_c for _, state in states], dtype=float)
    w = np.array([state.w for _, state in states], dtype=float)
    alpha0 = [state.alpha0 for _, state in states]

    colors = ["#378ADD", "#1D9E75", "#D85A30"]
    x = np.arange(len(labels))

    fig1, ax1 = plt.subplots(figsize=(7.2, 4.8))
    bars = ax1.bar(x, tr_c, color=colors, edgecolor="black", linewidth=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("Tr(C)")
    ax1.grid(axis="y", alpha=0.25)
    ax1.set_axisbelow(True)
    fig1.tight_layout()
    path1 = out_dir / "compare_trc_three_distributions.pdf"
    fig1.savefig(path1, dpi=220, bbox_inches="tight")
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(7.2, 4.8))
    bars = ax2.bar(x, w, color=colors, edgecolor="black", linewidth=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("w")
    ax2.set_yscale("log")
    ax2.grid(axis="y", which="both", alpha=0.25)
    ax2.set_axisbelow(True)
    fig2.tight_layout()
    path2 = out_dir / "compare_w_three_distributions.pdf"
    fig2.savefig(path2, dpi=220, bbox_inches="tight")
    plt.close(fig2)

    print(f"Saved: {path1}")
    print(f"Saved: {path2}")
    for name, state in states:
        print(f"{name:8s} Tr(C)={state.tr_c:.10f}, w={state.w:.10f}")


if __name__ == "__main__":
    main()
