"""
Compute Z* and SKR for QAM-256 with uniform probabilities.

Change from original file:
    p_{k,l} = 1/256, for all k,l in {0,...,15}
"""

import math
import numpy as np
from math import sqrt

import compute_Zstar_qam256 as base


# ------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------
Ncut = 150
alpha0 = sqrt(24/17)
T = 0.2
eps = 0.01
beta = 0.95
eta = 0.6
v_el = 0.01
# ------------------------------------------------------------


def build_probs_uniform():
    # 16 x 16 constellation points -> 256 equiprobable symbols
    return np.full(256, 1.0 / 256.0, dtype=float)


if __name__ == "__main__":
    print("=" * 60)
    print("Computing Z* for QAM-256 Uniform")
    print(f"alpha0 = 2*sqrt(2) = {alpha0:.8f}, Ncut = {Ncut}")
    print(f"T = {T}, eps = {eps}")
    print("=" * 60)

    # Step 1-2
    alpha_list = base.build_constellation(alpha0)
    p = build_probs_uniform()
    print(f"\nStep 1-2: {len(alpha_list)} symbols, Sum p = {p.sum():.15f}")

    # Step 3
    print("Step 3: Building Fock matrix F (256 x Ncut)...")
    F = base.build_fock_matrix(alpha_list, Ncut)
    norms = np.sum(np.abs(F) ** 2, axis=1)
    print(f"         Fock norms: min={norms.min():.8f}, max={norms.max():.8f}")

    # Step 4
    print("Step 4: Building density matrix tau (Ncut x Ncut)...")
    tau = base.build_tau(F, p)
    tr_tau = np.real(np.trace(tau))
    print(f"         Tr(tau) = {tr_tau:.15f} (should be ~1)")

    # Step 5
    print("Step 5: Computing tau^(1/2) and tau^(-1/2)...")
    tau_sqrt, tau_invsqrt, eigvals = base.compute_tau_sqrt_invsqrt(tau)
    err_sq = np.max(np.abs(tau_sqrt @ tau_sqrt - tau))
    print(f"         Verify tau^(1/2)@tau^(1/2)=tau: max error = {err_sq:.2e}")
    rank = np.sum(eigvals > 1e-12)
    print(f"         Rank(tau) = {rank}/{Ncut}")

    # Step 6
    a_op = base.build_a_operator(Ncut)
    VA = np.real(np.trace(tau @ a_op.conj().T @ a_op))
    print(f"\nStep 6: V_A = Tr(tau a^dagger a) = {VA:.15f}")

    # Step 7
    print("\nStep 7: Computing Tr(tau^(1/2) a tau^(1/2) a^dagger)...")
    Tr_C = base.compute_Tr_C(tau_sqrt, a_op)
    print(f"         Tr_C = {Tr_C:.15f}")

    # Quadrature-based Tr(C) and Z*
    Tr_Cx = base.compute_Tr_C_quadrature(tau_sqrt, a_op)
    print(f"         Tr_C (quadrature X) = {Tr_Cx:.15f}")

    # Step 8
    print("\nStep 8: Computing w...")
    w, sum_t1, sum_t2 = base.compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)
    print(f"         Sum p*term1 = {sum_t1:.15f}")
    print(f"         Sum p*term2 = {sum_t2:.15f}")
    print(f"         w           = {w:.15f}")

    # Step 9
    print("\nStep 9: Computing Z*...")
    Zstar = base.compute_Zstar(Tr_C, w, T, eps)
    print(f"         2*sqrt(T)*Tr_C = {2 * sqrt(T) * Tr_C:.15f}")
    print(f"         sqrt(2*T*eps)*w = {sqrt(2 * T * eps) * w:.15f}")
    print(f"         Z* = {Zstar:.15f}")

    # compute quadrature Z*
    Zstar_x = base.compute_Zstar_quadrature(Tr_Cx, w, T, eps)
    print(f"         Z* (quadrature) = {Zstar_x:.15f}")

    # Physical check
    a_cv = VA + 1
    b_cv = 1 + T * VA + T * eps
    Zmax = sqrt(a_cv * b_cv)
    print(f"\n         Z*_max = sqrt[(VA+1)(1+T*VA+T*eps)] = {Zmax:.10f}")
    print(f"         Z* < Z*_max? {Zstar:.6f} < {Zmax:.6f} -> {Zstar < Zmax}")
    # Quadrature stats for diagnostics
    mean_X, var_X, mean_P, var_P = base.compute_quadrature_stats(tau, tau_sqrt, a_op)
    print(f"\n         <X> = {mean_X:.10f}, Var(X) = {var_X:.10f}")
    print(f"         <P> = {mean_P:.10f}, Var(P) = {var_P:.10f}")

    # If Z* is unphysical, apply safe clip fallback before eigen computation
    Zstar_used = Zstar
    if Zstar >= Zmax or (a_cv * b_cv - Zstar**2) <= 0:
        Zstar_used = min(Zstar, Zmax * (1.0 - 1e-9))
        print(f"\n         ⚠ Z* is unphysical (Z* > Z*_max). Applying safe clip: Z*_used = {Zstar_used:.12f}")

    # SKR part
    print("\n" + "=" * 60)
    print("SKR COMPUTATION")
    print("=" * 60)

    chi_tot, chi_line, chi_det = base.compute_chi_tot(T, eps, eta, v_el)
    print(f"\nStep 10: chi_line = {chi_line:.10f}")
    print(f"         chi_det  = {chi_det:.10f}")
    print(f"         chi_tot  = {chi_tot:.10f}")

    print("\nStep 11: Symplectic eigenvalues")
    # use clipped Z* if necessary
    l1, l2, l3, Delta, B, disc = base.compute_eigenvalues(VA, Zstar_used, T, eps)
    print(f"         lambda1 = {l1:.15f}")
    print(f"         lambda2 = {l2:.15f}")
    print(f"         lambda3 = {l3:.15f}")

    print("\nStep 12: Holevo bound chi_BE")
    chi_BE_val = base.compute_chi_BE(l1, l2, l3)
    print(f"         chi_BE = {chi_BE_val:.15f}")

    print("\nStep 13: Mutual information I_AB")
    IAB_val = base.compute_IAB(VA, T, eps)
    print(f"         I_AB = {IAB_val:.15f}")

    print("\nStep 14: Secret Key Rate")
    SKR_raw = base.compute_SKR(beta, IAB_val, chi_BE_val)
    SKR_val = max(SKR_raw, 0.0)
    print(f"         SKR_raw = {SKR_raw:.15f}")
    print(f"         SKR     = {SKR_val:.15f}")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print("  Protocol: QAM-256 Uniform")
    print(f"  alpha0  = {alpha0:.6f}")
    print(f"  T       = {T}, eps = {eps}, beta = {beta}")
    print(f"  eta     = {eta}, v_el = {v_el}")
    print(f"  V_A     = {VA:.10f}")
    print(f"  Z*      = {Zstar:.10f}")
    print(f"  chi_tot = {chi_tot:.10f}")
    print(f"  chi_BE  = {chi_BE_val:.10f}")
    print(f"  I_AB    = {IAB_val:.10f}")
    print(f"  SKR_raw = {SKR_raw:.10f}")
    print(f"  SKR     = {SKR_val:.10f}")
