"""
Visualize SKR sensitivity for QAM-256 Binomial.

This script reuses the same physical model as compute_Zstar_qam256.py and
plots how SKR changes with:
1) transmittance T
2) base amplitude alpha0
3) excess noise eps

Fixed defaults:
- Ncut = 25
- alpha0 = 2*sqrt(2)
- T = 0.2
- eps = 0.01
- beta = 0.95
- eta = 0.6
- v_el = 0.01

Run:
    python skr_sweep_visualize.py
"""

import math
from math import comb, sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigh


# ------------------------------------------------------------
# Fixed baseline parameters
# ------------------------------------------------------------
Ncut = 25
ALPHA0_BASE = 2 * sqrt(2)
T_BASE = 0.2
EPS_BASE = 0.01
BETA = 0.95
ETA = 0.6
V_EL = 0.01


# ------------------------------------------------------------
# Core model (aligned with compute_Zstar_qam256.py)
# ------------------------------------------------------------
def build_constellation(alpha0):
    alpha_list = []
    for k in range(16):
        for l in range(16):
            a = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
            alpha_list.append(a)
    return alpha_list


def build_probs_binomial():
    p_list = []
    for k in range(16):
        for l in range(16):
            p_list.append(comb(15, k) * comb(15, l) / 2**30)
    return np.array(p_list, dtype=float)


def build_fock_matrix(alpha_list, ncut):
    log_fac = np.zeros(ncut)
    for i in range(1, ncut):
        log_fac[i] = log_fac[i - 1] + np.log(i)

    F = np.zeros((len(alpha_list), ncut), dtype=complex)
    for n_idx, al in enumerate(alpha_list):
        prefactor = np.exp(-0.5 * abs(al) ** 2)
        for i in range(ncut):
            F[n_idx, i] = prefactor * (al**i) / np.exp(0.5 * log_fac[i])
    return F


def build_tau(F, p):
    return (F.conj().T * p[None, :]) @ F


def compute_tau_sqrt_invsqrt(tau, tol=1e-12):
    eigvals, V = eigh(tau)
    eigvals = np.maximum(eigvals, 0.0)

    sqrt_ev = np.sqrt(eigvals)
    inv_sqrt_ev = np.where(eigvals > tol, 1.0 / sqrt_ev, 0.0)

    tau_sqrt = (V * sqrt_ev[None, :]) @ V.conj().T
    tau_invsqrt = (V * inv_sqrt_ev[None, :]) @ V.conj().T
    return tau_sqrt, tau_invsqrt


def build_a_operator(ncut):
    a_op = np.zeros((ncut, ncut), dtype=complex)
    for j in range(1, ncut):
        a_op[j - 1, j] = sqrt(j)
    return a_op


def compute_tr_c(tau_sqrt, a_op):
    adag = a_op.conj().T
    C = tau_sqrt @ a_op @ tau_sqrt @ adag
    return np.real(np.trace(C))


def compute_w(tau_sqrt, tau_invsqrt, a_op, F, p):
    a_tau = tau_sqrt @ a_op @ tau_invsqrt
    M_t1 = a_tau.conj().T @ a_tau

    w = 0.0
    for n_idx in range(len(p)):
        v = F[n_idx]
        t1 = np.real(v.conj() @ M_t1 @ v)
        inner = v.conj() @ a_tau @ v
        t2 = np.abs(inner) ** 2
        w += p[n_idx] * (t1 - t2)

    return float(w)


def compute_zstar(tr_c, w, T, eps):
    # Follows formula documented in compute_Zstar_qam256.py
    return 2 * sqrt(T) * tr_c - sqrt(2 * T * eps) * w


def g(x):
    if x < 1e-15:
        return 0.0
    return (x + 1) * math.log2(x + 1) - x * math.log2(x)


def compute_eigenvalues(VA, zstar, T, eps):
    a = VA + 1.0
    b = 1.0 + T * VA + T * eps
    c = zstar

    Delta = a**2 + b**2 - 2 * c**2
    B = (a * b - c**2) ** 2
    disc = max(Delta**2 - 4 * B, 0.0)

    sd = math.sqrt(disc)
    l1 = math.sqrt(max(0.5 * (Delta + sd), 0.0))
    l2 = math.sqrt(max(0.5 * (Delta - sd), 0.0))
    l3 = max(a - c**2 / (2.0 + T * VA + T * eps), 1e-15)
    return l1, l2, l3


def compute_chi_BE(l1, l2, l3):
    return g((l1 - 1) / 2) + g((l2 - 1) / 2) - g((l3 - 1) / 2)


def compute_chi_tot(T, eps, eta, v_el):
    chi_line = (1.0 - T) / T + eps
    chi_det = (1.0 - eta + v_el) / eta
    chi_tot = chi_line + chi_det / T
    return chi_tot


def compute_IAB(VA, T, chi_tot):
    return math.log2(1.0 + T * VA / (2.0 + T * chi_tot))


def build_state(alpha0, ncut, p, a_op):
    alpha_list = build_constellation(alpha0)
    F = build_fock_matrix(alpha_list, ncut)
    tau = build_tau(F, p)

    tau_sqrt, tau_invsqrt = compute_tau_sqrt_invsqrt(tau)
    VA = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    tr_c = compute_tr_c(tau_sqrt, a_op)
    w = compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)
    return VA, tr_c, w


def compute_skr_from_state(VA, tr_c, w, T, eps, beta, eta, v_el):
    zstar = compute_zstar(tr_c, w, T, eps)
    l1, l2, l3 = compute_eigenvalues(VA, zstar, T, eps)
    chi_be = compute_chi_BE(l1, l2, l3)
    chi_tot = compute_chi_tot(T, eps, eta, v_el)
    iab = compute_IAB(VA, T, chi_tot)
    skr_raw = beta * iab - chi_be
    skr = max(skr_raw, 0.0)
    return skr, skr_raw


def ensure_output_dir():
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main():
    print("=" * 70)
    print("SKR sensitivity sweep: T, alpha0, eps")
    print("=" * 70)
    print(
        f"Fixed params: Ncut={Ncut}, alpha0={ALPHA0_BASE:.6f}, T={T_BASE}, eps={EPS_BASE}, "
        f"beta={BETA}, eta={ETA}, v_el={V_EL}"
    )

    p = build_probs_binomial()
    a_op = build_a_operator(Ncut)

    # Baseline state at alpha0 fixed
    VA_base, tr_c_base, w_base = build_state(ALPHA0_BASE, Ncut, p, a_op)
    print(f"Baseline state: VA={VA_base:.8f}, TrC={tr_c_base:.8f}, w={w_base:.8f}")

    # 1D sweeps
    T_vals = np.linspace(0.02, 0.95, 50)
    alpha_vals = np.linspace(0.8, 4.2, 34)
    eps_vals = np.linspace(0.0, 0.08, 41)

    skr_vs_T = np.array(
        [compute_skr_from_state(VA_base, tr_c_base, w_base, Tv, EPS_BASE, BETA, ETA, V_EL)[0] for Tv in T_vals]
    )

    skr_vs_eps = np.array(
        [compute_skr_from_state(VA_base, tr_c_base, w_base, T_BASE, ev, BETA, ETA, V_EL)[0] for ev in eps_vals]
    )

    skr_vs_alpha = []
    cached_states = {}
    for av in alpha_vals:
        VA_a, tr_c_a, w_a = build_state(float(av), Ncut, p, a_op)
        cached_states[float(av)] = (VA_a, tr_c_a, w_a)
        skr_vs_alpha.append(
            compute_skr_from_state(VA_a, tr_c_a, w_a, T_BASE, EPS_BASE, BETA, ETA, V_EL)[0]
        )
    skr_vs_alpha = np.array(skr_vs_alpha)

    # 2D heatmaps
    T_grid = np.linspace(0.02, 0.95, 32)
    alpha_grid = np.linspace(0.8, 4.2, 28)
    eps_grid = np.linspace(0.0, 0.08, 28)

    SKR_T_alpha = np.zeros((len(alpha_grid), len(T_grid)))
    for i, av in enumerate(alpha_grid):
        VA_a, tr_c_a, w_a = build_state(float(av), Ncut, p, a_op)
        for j, Tv in enumerate(T_grid):
            SKR_T_alpha[i, j] = compute_skr_from_state(VA_a, tr_c_a, w_a, float(Tv), EPS_BASE, BETA, ETA, V_EL)[0]

    SKR_T_eps = np.zeros((len(eps_grid), len(T_grid)))
    for i, ev in enumerate(eps_grid):
        for j, Tv in enumerate(T_grid):
            SKR_T_eps[i, j] = compute_skr_from_state(VA_base, tr_c_base, w_base, float(Tv), float(ev), BETA, ETA, V_EL)[0]

    out_dir = ensure_output_dir()

    # Figure 1: 1D curves
    fig1, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    axes[0].plot(T_vals, skr_vs_T, color="#006d77", lw=2.2)
    axes[0].axvline(T_BASE, color="gray", ls="--", lw=1)
    axes[0].set_title("SKR vs T (alpha0, eps fixed)")
    axes[0].set_xlabel("T")
    axes[0].set_ylabel("SKR (bits/use)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(alpha_vals, skr_vs_alpha, color="#bc6c25", lw=2.2)
    axes[1].axvline(ALPHA0_BASE, color="gray", ls="--", lw=1)
    axes[1].set_title("SKR vs alpha0 (T, eps fixed)")
    axes[1].set_xlabel("alpha0")
    axes[1].set_ylabel("SKR (bits/use)")
    axes[1].grid(alpha=0.3)

    axes[2].plot(eps_vals, skr_vs_eps, color="#9b2226", lw=2.2)
    axes[2].axvline(EPS_BASE, color="gray", ls="--", lw=1)
    axes[2].set_title("SKR vs eps (T, alpha0 fixed)")
    axes[2].set_xlabel("eps")
    axes[2].set_ylabel("SKR (bits/use)")
    axes[2].grid(alpha=0.3)

    fig1.suptitle("QAM-256 Binomial: SKR sensitivity (Ncut=25, beta=0.95, eta=0.6, v_el=0.01)")
    fig1.tight_layout()
    fig1_path = out_dir / "skr_sensitivity_1d.png"
    fig1.savefig(fig1_path, dpi=180)

    # Figure 2: heatmaps
    fig2, axes2 = plt.subplots(1, 2, figsize=(13.5, 5.2))

    im1 = axes2[0].imshow(
        SKR_T_alpha,
        origin="lower",
        aspect="auto",
        extent=[T_grid.min(), T_grid.max(), alpha_grid.min(), alpha_grid.max()],
        cmap="viridis",
    )
    axes2[0].set_title("SKR(T, alpha0) at eps=0.01")
    axes2[0].set_xlabel("T")
    axes2[0].set_ylabel("alpha0")
    cbar1 = fig2.colorbar(im1, ax=axes2[0])
    cbar1.set_label("SKR (bits/use)")

    im2 = axes2[1].imshow(
        SKR_T_eps,
        origin="lower",
        aspect="auto",
        extent=[T_grid.min(), T_grid.max(), eps_grid.min(), eps_grid.max()],
        cmap="magma",
    )
    axes2[1].set_title("SKR(T, eps) at alpha0=2*sqrt(2)")
    axes2[1].set_xlabel("T")
    axes2[1].set_ylabel("eps")
    cbar2 = fig2.colorbar(im2, ax=axes2[1])
    cbar2.set_label("SKR (bits/use)")

    fig2.suptitle("QAM-256 Binomial: 2D SKR maps")
    fig2.tight_layout()
    fig2_path = out_dir / "skr_sensitivity_2d.png"
    fig2.savefig(fig2_path, dpi=180)

    # Print compact summary values around baseline
    skr_base, skr_base_raw = compute_skr_from_state(
        VA_base, tr_c_base, w_base, T_BASE, EPS_BASE, BETA, ETA, V_EL
    )

    print("\nBaseline SKR at requested fixed point")
    print(f"  alpha0={ALPHA0_BASE:.6f}, T={T_BASE:.3f}, eps={EPS_BASE:.4f}")
    print(f"  SKR_raw={skr_base_raw:.10f}, SKR_clamped={skr_base:.10f}")

    print("\nGenerated files:")
    print(f"  - {fig1_path}")
    print(f"  - {fig2_path}")


if __name__ == "__main__":
    main()
