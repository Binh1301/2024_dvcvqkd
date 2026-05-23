"""
Compare SKR sensitivity for QAM-256 binomial vs uniform ensembles.

This script visualizes how the secret key rate changes with:
  - transmittance T,
  - excess noise eps,
  - reconciliation efficiency beta,

for the two existing QAM-256 codes:
  - compute_Zstar_qam256.py (binomial prior)
  - compute_Zstar_qam256_uniform.py (uniform prior)

The script saves a comparison figure in outputs/.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from math import comb, sqrt
from scipy.linalg import eigh

import compute_Zstar_qam256 as base


Ncut = 25
ETA = 0.6
V_EL = 0.01

ALPHA0_BINOMIAL = 2 * sqrt(2)
ALPHA0_UNIFORM = sqrt(24 / 17)

T_BASE = 0.3
EPS_BASE = 0.01
BETA_BASE = 0.95

T_GRID = np.linspace(0.02, 0.95, 60)
EPS_GRID = np.linspace(0.0, 0.08, 60)
BETA_GRID = np.linspace(0.5, 1.0, 60)


@dataclass
class ModelResult:
    name: str
    alpha0: float
    va: float
    tr_tau: float
    c_value: float
    w_value: float
    chi_tot: float
    chi_be: float
    iab: float
    skr_raw: float
    skr: float


def build_probs_uniform() -> np.ndarray:
    return np.full(256, 1.0 / 256.0, dtype=float)


def compute_tau_sqrt_invsqrt(tau: np.ndarray, tol: float = 1e-12):
    eigvals, V = eigh(tau)
    eigvals = np.maximum(eigvals, 0.0)
    sqrt_eigvals = np.sqrt(eigvals)
    inv_sqrt_eigvals = np.zeros_like(sqrt_eigvals)
    positive = eigvals > tol
    inv_sqrt_eigvals[positive] = 1.0 / sqrt_eigvals[positive]
    tau_sqrt = (V * sqrt_eigvals[None, :]) @ V.conj().T
    tau_invsqrt = (V * inv_sqrt_eigvals[None, :]) @ V.conj().T
    tau_sqrt = 0.5 * (tau_sqrt + tau_sqrt.conj().T)
    tau_invsqrt = 0.5 * (tau_invsqrt + tau_invsqrt.conj().T)
    return tau_sqrt, tau_invsqrt, eigvals


def compute_w(tau_sqrt, tau_invsqrt, a_op, F, p):
    a_tau = tau_sqrt @ a_op @ tau_invsqrt
    m_t1 = a_tau.conj().T @ a_tau

    w = 0.0
    for idx in range(len(p)):
        v = F[idx]
        term1 = np.real(v.conj() @ m_t1 @ v)
        inner = v.conj() @ a_tau @ v
        term2 = np.abs(inner) ** 2
        w += p[idx] * (term1 - term2)

    return float(w)


def build_state(alpha0: float, p: np.ndarray):
    alpha_list = base.build_constellation(alpha0)
    F = base.build_fock_matrix(alpha_list, Ncut)
    tau = base.build_tau(F, p)
    tau_sqrt, tau_invsqrt, eigvals = compute_tau_sqrt_invsqrt(tau)
    a_op = base.build_a_operator(Ncut)

    va = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    tr_tau = float(np.real(np.trace(tau)))
    c_value = base.compute_Tr_C(tau_sqrt, a_op)
    w_value = compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)

    return {
        "va": va,
        "tr_tau": tr_tau,
        "c_value": c_value,
        "w_value": w_value,
        "eigvals": eigvals,
    }


def compute_skr_curve(va: float, c_value: float, w_value: float, t: float, eps: float, beta: float):
    chi_tot, _, _ = base.compute_chi_tot(t, eps, ETA, V_EL)
    zstar = base.compute_Zstar(c_value, w_value, t, eps)
    l1, l2, l3, _, _, _ = base.compute_eigenvalues(va, zstar, t, eps)
    chi_be = base.compute_chi_BE(l1, l2, l3)
    iab = base.compute_IAB(va, t, chi_tot)
    skr_raw = base.compute_SKR(beta, iab, chi_be)
    skr = max(skr_raw, 0.0)
    return skr, skr_raw, chi_be, iab, chi_tot


def evaluate_model(name: str, alpha0: float, p: np.ndarray) -> ModelResult:
    state = build_state(alpha0, p)
    skr, skr_raw, chi_be, iab, chi_tot = compute_skr_curve(
        state["va"], state["c_value"], state["w_value"], T_BASE, EPS_BASE, BETA_BASE
    )
    return ModelResult(
        name=name,
        alpha0=alpha0,
        va=state["va"],
        tr_tau=state["tr_tau"],
        c_value=state["c_value"],
        w_value=state["w_value"],
        chi_tot=chi_tot,
        chi_be=chi_be,
        iab=iab,
        skr_raw=skr_raw,
        skr=skr,
    )


def sweep_curve(model_state: dict, sweep_name: str):
    va = model_state["va"]
    c_value = model_state["c_value"]
    w_value = model_state["w_value"]

    values = []
    if sweep_name == "T":
        xs = T_GRID
        for t in xs:
            skr, _, _, _, _ = compute_skr_curve(va, c_value, w_value, float(t), EPS_BASE, BETA_BASE)
            values.append(skr)
    elif sweep_name == "eps":
        xs = EPS_GRID
        for eps in xs:
            skr, _, _, _, _ = compute_skr_curve(va, c_value, w_value, T_BASE, float(eps), BETA_BASE)
            values.append(skr)
    elif sweep_name == "beta":
        xs = BETA_GRID
        for beta in xs:
            skr, _, _, _, _ = compute_skr_curve(va, c_value, w_value, T_BASE, EPS_BASE, float(beta))
            values.append(skr)
    else:
        raise ValueError(f"Unsupported sweep: {sweep_name}")

    return xs, np.array(values, dtype=float)


def ensure_output_dir() -> Path:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> None:
    print("=" * 80)
    print("SKR comparison: binomial vs uniform QAM-256")
    print("=" * 80)

    p_binomial = base.build_probs_binomial()
    p_uniform = build_probs_uniform()

    bin_state = build_state(ALPHA0_BINOMIAL, p_binomial)
    uni_state = build_state(ALPHA0_UNIFORM, p_uniform)

    bin_result = evaluate_model("binomial", ALPHA0_BINOMIAL, p_binomial)
    uni_result = evaluate_model("uniform", ALPHA0_UNIFORM, p_uniform)

    print(f"Binomial: VA={bin_result.va:.8f}, Tr(tau)={bin_result.tr_tau:.8f}, C={bin_result.c_value:.8f}, w={bin_result.w_value:.8f}")
    print(f"Uniform  : VA={uni_result.va:.8f}, Tr(tau)={uni_result.tr_tau:.8f}, C={uni_result.c_value:.8f}, w={uni_result.w_value:.8f}")

    sweeps = ["T", "eps", "beta"]
    labels = ["T", "Excess noise ε", "Reconciliation efficiency β"]
    xlabels = ["T", "ε", "β"]
    baselines = [f"ε={EPS_BASE}, β={BETA_BASE}", f"T={T_BASE}, β={BETA_BASE}", f"T={T_BASE}, ε={EPS_BASE}"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)
    fig.suptitle("SKR sensitivity for QAM-256: binomial vs uniform", fontsize=16, fontweight="bold")

    model_states = [bin_state, uni_state]
    model_labels = ["Binomial", "Uniform"]
    model_colors = ["#006d77", "#bc6c25"]

    for ax, sweep_name, title, xlabel, baseline in zip(axes, sweeps, labels, xlabels, baselines, strict=True):
        for state, label, color in zip(model_states, model_labels, model_colors, strict=True):
            xs, ys = sweep_curve(state, sweep_name)
            ax.plot(xs, ys, lw=2.2, color=color, label=label)

        if sweep_name == "T":
            ax.axvline(T_BASE, color="gray", ls="--", lw=1)
        elif sweep_name == "eps":
            ax.axvline(EPS_BASE, color="gray", ls="--", lw=1)
        else:
            ax.axvline(BETA_BASE, color="gray", ls="--", lw=1)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("SKR (bits/use)")
        ax.grid(alpha=0.3)
        ax.legend(frameon=False)
        ax.text(0.03, 0.95, baseline, transform=ax.transAxes, va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.8", alpha=0.9))

    out_dir = ensure_output_dir()
    fig_path = out_dir / "skr_compare_T_eps_beta.png"
    fig.savefig(fig_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print("\nSaved figure:")
    print(f"  {fig_path}")
    print("\nBaseline summary:")
    print(f"  Binomial SKR = {bin_result.skr:.10f} (raw={bin_result.skr_raw:.10f})")
    print(f"  Uniform   SKR = {uni_result.skr:.10f} (raw={uni_result.skr_raw:.10f})")


if __name__ == "__main__":
    main()