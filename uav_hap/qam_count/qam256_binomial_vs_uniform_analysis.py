"""
Scientific comparison of QAM-256 Binomial vs Uniform ensembles in CV-QKD.

This script reuses physics helpers from:
  - compute_Zstar_qam256.py
  - compute_Zstar_qam256_uniform.py

Outputs:
  - Figure: outputs/qam256_binomial_vs_uniform_analysis.png
  - Console summary table: VA, Tr_C, w, Z*, chi_BE, I_AB, SKR
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import compute_Zstar_qam256 as base
import compute_Zstar_qam256_uniform as uniform_mod


# -----------------------------------------------------------------------------
# Fixed study parameters
# -----------------------------------------------------------------------------
NCUT = 25
ALPHA0_BINOMIAL = 2.0 * np.sqrt(2.0)
ALPHA0_UNIFORM = np.sqrt(24.0 / 17.0)  # chosen to match VA ~ 2

T_BASE = 0.3
EPS_BASE = 0.01
BETA_BASE = 0.95
ETA = 0.6
V_EL = 0.01

EPS_SWEEP = np.linspace(0.0, 0.1, 120)
T_SWEEP = np.linspace(0.02, 0.95, 120)


@dataclass
class EnsembleState:
    name: str
    alpha0: float
    probs: np.ndarray
    alpha_list: list[complex]
    VA: float
    Tr_C: float
    w: float
    tr_tau: float


@dataclass
class PointMetrics:
    Zstar: float
    chi_tot: float
    chi_BE: float
    I_AB: float
    SKR: float
    penalty: float


def build_state(name: str, alpha0: float, probs: np.ndarray) -> EnsembleState:
    """Compute VA, Tr_C, and w from the ensemble state in Fock basis."""
    alpha_list = base.build_constellation(alpha0)
    F = base.build_fock_matrix(alpha_list, NCUT)
    tau = base.build_tau(F, probs)
    tau_sqrt, tau_invsqrt, _ = base.compute_tau_sqrt_invsqrt(tau)
    a_op = base.build_a_operator(NCUT)

    VA = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    Tr_C = float(base.compute_Tr_C(tau_sqrt, a_op))
    w, _, _ = base.compute_w(tau_sqrt, tau_invsqrt, a_op, F, probs)
    tr_tau = float(np.real(np.trace(tau)))

    return EnsembleState(
        name=name,
        alpha0=alpha0,
        probs=probs,
        alpha_list=alpha_list,
        VA=VA,
        Tr_C=Tr_C,
        w=float(w),
        tr_tau=tr_tau,
    )


def compute_point_metrics(state: EnsembleState, T: float, eps: float, beta: float) -> PointMetrics:
    """Compute derived SKR metrics at one operating point."""
    Zstar = float(base.compute_Zstar(state.Tr_C, state.w, T, eps))
    chi_tot, _, _ = base.compute_chi_tot(T, eps, ETA, V_EL)
    l1, l2, l3, _, _, _ = base.compute_eigenvalues(state.VA, Zstar, T, eps)
    chi_BE = float(base.compute_chi_BE(l1, l2, l3))
    I_AB = float(base.compute_IAB(state.VA, T, chi_tot))
    SKR = float(base.compute_SKR(beta, I_AB, chi_BE))
    penalty = float(np.sqrt(2.0 * T * eps * state.w))

    return PointMetrics(
        Zstar=Zstar,
        chi_tot=float(chi_tot),
        chi_BE=chi_BE,
        I_AB=I_AB,
        SKR=SKR,
        penalty=penalty,
    )


def print_summary(bin_state: EnsembleState, uni_state: EnsembleState) -> None:
    """Print scientific summary table at baseline operating point."""
    bin_metrics = compute_point_metrics(bin_state, T_BASE, EPS_BASE, BETA_BASE)
    uni_metrics = compute_point_metrics(uni_state, T_BASE, EPS_BASE, BETA_BASE)

    print("=" * 114)
    print("QAM-256 baseline summary (T=0.3, eps=0.01, beta=0.95)")
    print("=" * 114)
    print(
        f"{'Ensemble':<12} {'VA':>12} {'Tr(tau)':>12} {'Tr_C':>12} {'w':>12} "
        f"{'Z*':>12} {'chi_BE':>12} {'I_AB':>12} {'SKR':>12}"
    )
    print("-" * 114)
    print(
        f"{'Binomial':<12} {bin_state.VA:12.8f} {bin_state.tr_tau:12.8f} {bin_state.Tr_C:12.8f} "
        f"{bin_state.w:12.8f} {bin_metrics.Zstar:12.8f} {bin_metrics.chi_BE:12.8f} "
        f"{bin_metrics.I_AB:12.8f} {bin_metrics.SKR:12.8f}"
    )
    print(
        f"{'Uniform':<12} {uni_state.VA:12.8f} {uni_state.tr_tau:12.8f} {uni_state.Tr_C:12.8f} "
        f"{uni_state.w:12.8f} {uni_metrics.Zstar:12.8f} {uni_metrics.chi_BE:12.8f} "
        f"{uni_metrics.I_AB:12.8f} {uni_metrics.SKR:12.8f}"
    )
    print("=" * 114)

    delta_tr_c = bin_state.Tr_C - uni_state.Tr_C
    rel_delta = delta_tr_c / max(abs(uni_state.Tr_C), 1e-15)
    print("Tr(C) comparison:")
    print(f"  Tr_C(binomial) = {bin_state.Tr_C:.10f}")
    print(f"  Tr_C(uniform)  = {uni_state.Tr_C:.10f}")
    print(f"  Delta Tr_C     = {delta_tr_c:.10f} ({rel_delta:.4%} vs uniform)")
    print("=" * 114)


def make_figure(bin_state: EnsembleState, uni_state: EnsembleState, out_path: Path) -> None:
    """Create a report-quality multi-panel scientific figure."""
    fig, axes = plt.subplots(3, 2, figsize=(18, 14), constrained_layout=True)
    fig.suptitle("QAM-256 Binomial vs Uniform in CV-QKD", fontsize=18, fontweight="bold")

    # -------------------------------------------------------------------------
    # 1) Probability heatmaps (shared color scale)
    # -------------------------------------------------------------------------
    p_bin_grid = bin_state.probs.reshape(16, 16)
    p_uni_grid = uni_state.probs.reshape(16, 16)
    vmin = min(float(np.min(p_bin_grid)), float(np.min(p_uni_grid)))
    vmax = max(float(np.max(p_bin_grid)), float(np.max(p_uni_grid)))

    im0 = axes[0, 0].imshow(
        p_bin_grid,
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
    )
    axes[0, 0].set_title("(a) Binomial prior probability map")
    axes[0, 0].set_xlabel(r"$k$")
    axes[0, 0].set_ylabel(r"$l$")

    im1 = axes[0, 1].imshow(
        p_uni_grid,
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
    )
    axes[0, 1].set_title("(b) Uniform prior probability map")
    axes[0, 1].set_xlabel(r"$k$")
    axes[0, 1].set_ylabel(r"$l$")

    cbar = fig.colorbar(im1, ax=axes[0, :], shrink=0.9)
    cbar.set_label("Probability")

    # -------------------------------------------------------------------------
    # 2) Energy distribution histogram: |alpha|^2 with probability weights
    # -------------------------------------------------------------------------
    e_bin = np.abs(np.array(bin_state.alpha_list)) ** 2
    e_uni = np.abs(np.array(uni_state.alpha_list)) ** 2
    bins = np.linspace(0.0, max(float(e_bin.max()), float(e_uni.max())) * 1.03, 25)

    axes[1, 0].hist(
        e_bin,
        bins=bins,
        weights=bin_state.probs,
        alpha=0.60,
        color="#1f77b4",
        edgecolor="black",
        linewidth=0.5,
        label="Binomial",
    )
    axes[1, 0].hist(
        e_uni,
        bins=bins,
        weights=uni_state.probs,
        alpha=0.60,
        color="#ff7f0e",
        edgecolor="black",
        linewidth=0.5,
        label="Uniform",
    )
    axes[1, 0].set_title(r"(c) Weighted energy distribution of $|\alpha|^2$")
    axes[1, 0].set_xlabel(r"$|\alpha|^2$")
    axes[1, 0].set_ylabel("Probability mass")
    axes[1, 0].grid(alpha=0.3)
    axes[1, 0].legend(frameon=False)

    # -------------------------------------------------------------------------
    # 3) Noise penalty comparison: sqrt(2*T*eps*w) vs eps
    # -------------------------------------------------------------------------
    penalty_bin = np.sqrt(2.0 * T_BASE * EPS_SWEEP * bin_state.w)
    penalty_uni = np.sqrt(2.0 * T_BASE * EPS_SWEEP * uni_state.w)

    axes[1, 1].plot(EPS_SWEEP, penalty_bin, color="#1f77b4", lw=2.2, label="Binomial")
    axes[1, 1].plot(EPS_SWEEP, penalty_uni, color="#ff7f0e", lw=2.2, label="Uniform")
    axes[1, 1].set_title(r"(d) Noise penalty $\sqrt{2T\epsilon w}$ at $T=0.3$")
    axes[1, 1].set_xlabel(r"Excess noise $\epsilon$")
    axes[1, 1].set_ylabel(r"Penalty term $\sqrt{2T\epsilon w}$")
    axes[1, 1].grid(alpha=0.3)
    axes[1, 1].legend(frameon=False)

    # -------------------------------------------------------------------------
    # 4) Delta SKR: SKR_binomial - SKR_uniform vs eps
    # -------------------------------------------------------------------------
    skr_bin = []
    skr_uni = []
    for eps_val in EPS_SWEEP:
        skr_bin.append(compute_point_metrics(bin_state, T_BASE, float(eps_val), BETA_BASE).SKR)
        skr_uni.append(compute_point_metrics(uni_state, T_BASE, float(eps_val), BETA_BASE).SKR)
    skr_bin = np.array(skr_bin, dtype=float)
    skr_uni = np.array(skr_uni, dtype=float)
    delta_skr = skr_bin - skr_uni

    axes[2, 0].plot(EPS_SWEEP, delta_skr, color="#2ca02c", lw=2.2)
    axes[2, 0].axhline(0.0, color="black", lw=1.0, ls="--")
    axes[2, 0].set_title(r"(e) $\Delta$SKR at $T=0.3$, $\beta=0.95$")
    axes[2, 0].set_xlabel(r"Excess noise $\epsilon$")
    axes[2, 0].set_ylabel(r"$\Delta\mathrm{SKR}=\mathrm{SKR}_{\mathrm{bin}}-\mathrm{SKR}_{\mathrm{uni}}$")
    axes[2, 0].grid(alpha=0.3)

    # -------------------------------------------------------------------------
    # 5) Z* comparison vs transmittance
    # -------------------------------------------------------------------------
    z_bin = np.array([base.compute_Zstar(bin_state.Tr_C, bin_state.w, float(tv), EPS_BASE) for tv in T_SWEEP])
    z_uni = np.array([base.compute_Zstar(uni_state.Tr_C, uni_state.w, float(tv), EPS_BASE) for tv in T_SWEEP])

    axes[2, 1].plot(T_SWEEP, z_bin, color="#1f77b4", lw=2.2, label="Binomial")
    axes[2, 1].plot(T_SWEEP, z_uni, color="#ff7f0e", lw=2.2, label="Uniform")
    axes[2, 1].set_title(r"(f) Correlation bound $Z^*$ vs transmittance")
    axes[2, 1].set_xlabel(r"Transmittance $T$")
    axes[2, 1].set_ylabel(r"$Z^*$")
    axes[2, 1].grid(alpha=0.3)
    axes[2, 1].legend(frameon=False)

    # Inset: direct Tr(C) comparison for the two ensembles.
    inset = inset_axes(axes[2, 1], width="40%", height="45%", loc="lower right", borderpad=1.2)
    tr_vals = [bin_state.Tr_C, uni_state.Tr_C]
    inset.bar([0, 1], tr_vals, color=["#1f77b4", "#ff7f0e"], alpha=0.85, width=0.65)
    inset.set_xticks([0, 1])
    inset.set_xticklabels(["Bin", "Uni"], fontsize=8)
    inset.set_ylabel(r"$\mathrm{Tr}(C)$", fontsize=8)
    inset.tick_params(axis="y", labelsize=8)
    inset.set_title(r"$\mathrm{Tr}(C)$", fontsize=9)
    inset.grid(alpha=0.2, axis="y")

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # Step 1: build both ensembles with matched modulation variance near VA ~ 2.
    p_bin = base.build_probs_binomial()
    p_uni = uniform_mod.build_probs_uniform()

    bin_state = build_state("Binomial", ALPHA0_BINOMIAL, p_bin)
    uni_state = build_state("Uniform", ALPHA0_UNIFORM, p_uni)

    print_summary(bin_state, uni_state)

    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "qam256_binomial_vs_uniform_analysis.png"
    make_figure(bin_state, uni_state, out_path)

    print("Saved figure:")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()