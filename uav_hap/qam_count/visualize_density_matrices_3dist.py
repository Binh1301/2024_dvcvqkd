"""
Visualize the 256-QAM density matrix tau for three distributions.

Panels:
  - Uniform
  - Binomial
  - Maxwell-Boltzmann

The script uses the same constellation mapping as qam_count:
  alpha_{k,l} = alpha0 / sqrt(30) * [(k - 7.5) + i (l - 7.5)]

It plots the real part of tau in a truncated Fock basis.
"""

from __future__ import annotations

import sys
from math import comb, sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from uav_hap_1.config import QAM_ALPHA0_BINOMIAL, QAM_ALPHA0_MB, QAM_ALPHA0_UNIFORM, QAM_NU_TILDE
from uav_hap_1.zstar import base as zbase


Ncut = 25

SPEC = [
    ("Uniform", QAM_ALPHA0_UNIFORM, "uniform"),
    ("Binomial", QAM_ALPHA0_BINOMIAL, "binomial"),
    ("MB", QAM_ALPHA0_MB, "mb"),
]

ALPHA_MAP = {label: alpha0 for label, alpha0, _ in SPEC}


def build_probs(kind: str) -> np.ndarray:
    if kind == "uniform":
        return np.full(256, 1.0 / 256.0, dtype=float)
    if kind == "binomial":
        probs = []
        for k in range(16):
            for l in range(16):
                probs.append(comb(15, k) * comb(15, l) / 2**30)
        return np.array(probs, dtype=float)
    if kind == "mb":
        ks = np.arange(16, dtype=float)
        weights = np.exp(-QAM_NU_TILDE * (ks - 7.5) ** 2)
        prob = np.outer(weights, weights).reshape(-1)
        prob /= prob.sum()
        return prob.astype(float)
    raise ValueError(f"Unsupported kind: {kind}")


def build_density_matrix(alpha0: float, kind: str) -> tuple[np.ndarray, dict[str, float]]:
    alpha_list = zbase.build_constellation(alpha0)
    F = zbase.build_fock_matrix(alpha_list, Ncut)
    p = build_probs(kind)
    tau = zbase.build_tau(F, p)
    tau = 0.5 * (tau + tau.conj().T)
    stats = {
        "trace": float(np.real(np.trace(tau))),
        "va": float(np.real(np.trace(tau @ zbase.build_a_operator(Ncut).conj().T @ zbase.build_a_operator(Ncut)))),
    }
    return tau, stats


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "qam256_density_matrices_3panel.png"

    matrices = []
    stats_list = []
    for label, alpha0, kind in SPEC:
        tau, stats = build_density_matrix(alpha0, kind)
        matrices.append((label, tau))
        stats_list.append((label, stats))

    vmax = max(float(np.max(np.real(tau))) for _, tau in matrices)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), constrained_layout=True)
    fig.suptitle(
        "256-QAM density matrices in truncated Fock basis",
        fontsize=16,
        fontweight="bold",
    )

    im = None
    for ax, (label, tau), (_, stats) in zip(axes, matrices, stats_list):
        rho_real = np.real(tau)
        im = ax.imshow(
            rho_real,
            origin="upper",
            cmap="viridis",
            vmin=0.0,
            vmax=vmax,
            aspect="equal",
            interpolation="nearest",
        )
        ax.set_title(
            f"{label}\n"
            f"$\\alpha_0$={ALPHA_MAP[label]:.6f}  "
            f"$\\mathrm{{Tr}}(\\tau)$={stats['trace']:.6f}",
            fontsize=11,
        )
        ax.set_xlabel("Fock state |n>")
        ax.set_ylabel("Fock state <m|")
        ticks = list(range(0, Ncut, 2))
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.tick_params(labelsize=8)

    cbar = fig.colorbar(im, ax=axes, shrink=0.92, pad=0.02)
    cbar.set_label("Re(τ)")

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")
    for label, stats in stats_list:
        print(f"{label:8s} trace={stats['trace']:.10f}")


if __name__ == "__main__":
    main()
