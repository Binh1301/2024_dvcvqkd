"""
So sánh SKR theo T, excess noise (ε), và reconciliation efficiency (β)
cho QAM-256 Binomial vs Uniform.

Yêu cầu: compute_Zstar_qam256.py phải nằm cùng thư mục.
Output:  outputs/skr_compare_T_eps_beta.png
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from math import comb, sqrt
from scipy.linalg import eigh

import compute_Zstar_qam256 as base

# ─────────────────────────────────────────────────────────────
# PARAMETERS
# ─────────────────────────────────────────────────────────────
Ncut = 25
ETA  = 0.6
V_EL = 0.01

ALPHA0_BINOMIAL = 2 * sqrt(2)
ALPHA0_UNIFORM  = sqrt(24 / 17)

# Baseline values (dùng khi không sweep tham số đó)
T_BASE    = 0.30
EPS_BASE  = 0.01
BETA_BASE = 0.95

# Sweep grids
T_GRID    = np.linspace(0.02, 0.95, 80)
EPS_GRID  = np.linspace(0.00, 0.08, 80)
BETA_GRID = np.linspace(0.50, 1.00, 80)

# ─────────────────────────────────────────────────────────────
# BUILD MODEL STATE  (VA, Tr_C, w)
# ─────────────────────────────────────────────────────────────

def build_probs_uniform() -> np.ndarray:
    return np.full(256, 1.0 / 256.0, dtype=float)


def build_state(alpha0: float, p: np.ndarray) -> dict:
    """Trả về dict gồm VA, Tr_C, w cho một model."""
    alpha_list = base.build_constellation(alpha0)
    F          = base.build_fock_matrix(alpha_list, Ncut)
    tau        = base.build_tau(F, p)

    # τ^½ và τ^(-½)
    eigvals, V   = eigh(tau)
    eigvals      = np.maximum(eigvals, 0.0)
    sqrt_ev      = np.sqrt(eigvals)
    inv_sqrt_ev  = np.where(eigvals > 1e-12, 1.0 / sqrt_ev, 0.0)
    tau_sqrt     = (V * sqrt_ev[None, :])     @ V.conj().T
    tau_invsqrt  = (V * inv_sqrt_ev[None, :]) @ V.conj().T
    # symmetrize
    tau_sqrt    = 0.5 * (tau_sqrt    + tau_sqrt.conj().T)
    tau_invsqrt = 0.5 * (tau_invsqrt + tau_invsqrt.conj().T)

    a_op = base.build_a_operator(Ncut)

    VA    = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    Tr_C  = base.compute_Tr_C(tau_sqrt, a_op)
    w, _, _ = base.compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)

    return {"VA": VA, "Tr_C": Tr_C, "w": w}


# ─────────────────────────────────────────────────────────────
# SKR tại một điểm (T, eps, beta)
# ─────────────────────────────────────────────────────────────

def skr_point(state: dict, T: float, eps: float, beta: float) -> float:
    VA, Tr_C, w = state["VA"], state["Tr_C"], state["w"]
    chi_tot, _, _ = base.compute_chi_tot(T, eps, ETA, V_EL)
    Zstar         = base.compute_Zstar(Tr_C, w, T, eps)
    l1, l2, l3, *_ = base.compute_eigenvalues(VA, Zstar, T, eps)
    chi_be        = base.compute_chi_BE(l1, l2, l3)
    iab           = base.compute_IAB(VA, T, chi_tot)
    return max(beta * iab - chi_be, 0.0)


# ─────────────────────────────────────────────────────────────
# SWEEP curves
# ─────────────────────────────────────────────────────────────

def sweep_T(state, eps=EPS_BASE, beta=BETA_BASE):
    return T_GRID, np.array([skr_point(state, float(t), eps, beta) for t in T_GRID])

def sweep_eps(state, T=T_BASE, beta=BETA_BASE):
    return EPS_GRID, np.array([skr_point(state, T, float(e), beta) for e in EPS_GRID])

def sweep_beta(state, T=T_BASE, eps=EPS_BASE):
    return BETA_GRID, np.array([skr_point(state, T, eps, float(b)) for b in BETA_GRID])


# ─────────────────────────────────────────────────────────────
# PLOT
# ─────────────────────────────────────────────────────────────

COLORS = {"Binomial": "#1f77b4", "Uniform": "#d62728"}
LWIDTH = 2.2


def style_ax(ax, xlabel: str, vline: float):
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("SKR (bits/use)", fontsize=12)
    ax.axvline(vline, color="gray", ls="--", lw=1.0, alpha=0.7, label="_baseline")
    ax.axhline(0,     color="black", ls="-",  lw=0.6, alpha=0.3)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.tick_params(which="both", direction="in", top=True, right=True)
    ax.legend(frameon=True, framealpha=0.9, fontsize=10)


def main():
    print("=" * 70)
    print("  SKR comparison: QAM-256 Binomial vs Uniform")
    print("=" * 70)

    # ── Build states ──────────────────────────────────────────
    print("\n[1/2] Computing model states...")
    p_binom   = base.build_probs_binomial()
    p_uniform = build_probs_uniform()

    state_binom   = build_state(ALPHA0_BINOMIAL, p_binom)
    state_uniform = build_state(ALPHA0_UNIFORM,  p_uniform)

    for name, st in [("Binomial", state_binom), ("Uniform", state_uniform)]:
        print(f"  {name:9s}  VA={st['VA']:.6f}  Tr_C={st['Tr_C']:.6f}  w={st['w']:.6f}")

    # Baseline SKR
    skr_b = skr_point(state_binom,   T_BASE, EPS_BASE, BETA_BASE)
    skr_u = skr_point(state_uniform, T_BASE, EPS_BASE, BETA_BASE)
    print(f"\n  Baseline (T={T_BASE}, ε={EPS_BASE}, β={BETA_BASE}):")
    print(f"    Binomial SKR = {skr_b:.8f} bits/use")
    print(f"    Uniform  SKR = {skr_u:.8f} bits/use")

    # ── Sweep ─────────────────────────────────────────────────
    print("\n[2/2] Sweeping parameters and plotting...")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    fig.suptitle(
        f"SKR sensitivity: QAM-256 Binomial vs Uniform\n"
        f"η={ETA}, v_el={V_EL}",
        fontsize=13, fontweight="bold"
    )

    # --- Panel 1: sweep T ---
    ax = axes[0]
    for name, state in [("Binomial", state_binom), ("Uniform", state_uniform)]:
        xs, ys = sweep_T(state)
        ax.plot(xs, ys, lw=LWIDTH, color=COLORS[name], label=name)
    ax.set_title(f"SKR vs T  (ε={EPS_BASE}, β={BETA_BASE})", fontsize=11)
    style_ax(ax, "Transmittance T", T_BASE)

    # --- Panel 2: sweep ε ---
    ax = axes[1]
    for name, state in [("Binomial", state_binom), ("Uniform", state_uniform)]:
        xs, ys = sweep_eps(state)
        ax.plot(xs, ys, lw=LWIDTH, color=COLORS[name], label=name)
    ax.set_title(f"SKR vs ε  (T={T_BASE}, β={BETA_BASE})", fontsize=11)
    style_ax(ax, "Excess noise ε (SNU)", EPS_BASE)

    # --- Panel 3: sweep β ---
    ax = axes[2]
    for name, state in [("Binomial", state_binom), ("Uniform", state_uniform)]:
        xs, ys = sweep_beta(state)
        ax.plot(xs, ys, lw=LWIDTH, color=COLORS[name], label=name)
    ax.set_title(f"SKR vs β  (T={T_BASE}, ε={EPS_BASE})", fontsize=11)
    style_ax(ax, "Reconciliation efficiency β", BETA_BASE)

    # ── Save ──────────────────────────────────────────────────
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_path = out_dir / "skr_compare_T_eps_beta.png"
    fig.savefig(fig_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"\n  Saved → {fig_path}")
    print("Done.")


if __name__ == "__main__":
    main()