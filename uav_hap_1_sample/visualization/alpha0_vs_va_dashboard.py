"""
Alpha0 vs VA plot styled like the sweep figures.

Output:
  - output/alpha0_vs_va_dashboard.pdf
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.config import QAM_NU_TILDE
else:
    from ..config import QAM_NU_TILDE


BLUE = "#378ADD"
TEAL = "#1D9E75"
CORAL = "#D85A30"
MB_VA_FACTOR = 0.66421


def alpha0_uniform(va: np.ndarray) -> np.ndarray:
    return np.sqrt((6.0 * va) / 17.0)


def alpha0_binomial(va: np.ndarray) -> np.ndarray:
    return np.sqrt(2.0 * va)


def alpha0_mb(va: np.ndarray) -> np.ndarray:
    return np.sqrt(va / MB_VA_FACTOR)


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "alpha0_vs_va_dashboard.pdf"

    va = np.linspace(0.1, 10.0, 500)
    va0 = 2.0
    y_uniform = alpha0_uniform(va)
    y_binomial = alpha0_binomial(va)
    y_mb = alpha0_mb(va)

    u0 = float(alpha0_uniform(np.array([va0]))[0])
    b0 = float(alpha0_binomial(np.array([va0]))[0])
    m0 = float(alpha0_mb(np.array([va0]))[0])

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )

    fig, ax = plt.subplots(figsize=(5.2, 5.0))

    ax.plot(va, y_mb, color=CORAL, linestyle=":", linewidth=2.2, label="MB")
    ax.plot(va, y_binomial, color=TEAL, linestyle="--", linewidth=2.2, label="Binomial")
    ax.plot(va, y_uniform, color=BLUE, linestyle="-", linewidth=2.2, label="Uniform")

    ax.scatter([va0], [m0], color=CORAL, s=18, zorder=4)
    ax.scatter([va0], [b0], color=TEAL, s=18, zorder=4)
    ax.scatter([va0], [u0], color=BLUE, s=18, zorder=4)
    ax.axvline(va0, color="0.75", linestyle=":", linewidth=1.0)

    ax.set_xlim(0.0, 10.5)
    ax.set_ylim(0.0, 5.0)
    ax.set_xlabel(r"$V_A$ (SNU)")
    ax.set_ylabel(r"$\alpha_0$")
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=True, fontsize=9)

    ax.text(
        0.98,
        0.04,
        fr"$\tilde{{\nu}}={QAM_NU_TILDE}$",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="0.35",
    )

    fig.savefig(out_path, dpi=240, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
