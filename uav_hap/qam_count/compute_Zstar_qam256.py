"""
Tính Z* và SKR chính xác cho QAM-256 Binomial
===============================================
Công thức Z*:
    Z* = 2√T · Tr(τ^½ â τ^½ â†) − √(2Tε) · w

    w = Σ_k p_k [ v_k†(a_τ† a_τ)v_k  −  |v_k† a_τ v_k|² ]

    a_τ = τ^½ · â · τ^(-½)    (similarity transform)

Công thức SKR:
    a = VA+1,  b = 1+T·VA+T·ε,  c = Z*
    Δ = a²+b²−2c²,  B = (ab−c²)²,  disc = Δ²−4B
    λ₁,₂ = √[(Δ ± √disc)/2]
    λ₃   = (VA+1) − c²/(2+T·VA+T·ε)
    g(x) = (x+1)·log₂(x+1) − x·log₂(x)
    χ_BE = g((λ₁−1)/2) + g((λ₂−1)/2) − g((λ₃−1)/2)
    I_AB = log₂(1 + T·VA/(2+T·χ_tot))
    SKR  = β·I_AB − χ_BE

Pipeline:
    1.  Định nghĩa constellation α_{k,l}
    2.  Tính xác suất binomial p_{k,l}
    3.  Xây dựng density matrix τ trong Fock basis
    4.  Tính τ^½ và τ^(-½) qua eigendecomposition
    5.  Tính Tr(τ^½ â τ^½ â†)
    6.  Tính a_τ = τ^½ â τ^(-½), rồi tính w
    7.  Tính Z*
    8.  Tính eigenvalues λ₁, λ₂, λ₃
    9.  Tính χ_BE, I_AB, SKR
"""

import math
import numpy as np
from math import factorial, comb, sqrt
from scipy.linalg import eigh

# ─────────────────────────────────────────────────────────────
# PARAMETERS — thay đổi tại đây
# ─────────────────────────────────────────────────────────────
Ncut    = 25          # Fock space cutoff (25 đủ cho alpha0=2√2)
alpha0  = 2*sqrt(2)   # base amplitude  (VA = 2.0 SNU)
T       = 0.2         # transmittance
eps     = 0.01        # excess noise
beta    = 0.95        # reconciliation efficiency
eta     = 0.6         # detector efficiency
v_el    = 0.01        # electronic noise
# ─────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# STEP 1: CONSTELLATION α_{k,l}
# α_{k,l} = alpha0/√30 · [(k−7.5) + i(l−7.5)]
# k, l ∈ {0,...,15}  →  256 symbols
# ─────────────────────────────────────────────────────────────
def build_constellation(alpha0):
    alpha_list = []
    for k in range(16):
        for l in range(16):
            a = alpha0 / sqrt(30) * ((k - 7.5) + 1j*(l - 7.5))
            alpha_list.append(a)
    return alpha_list                        # length 256

# ─────────────────────────────────────────────────────────────
# STEP 2: BINOMIAL PROBABILITIES p_{k,l}
# p_{k,l} = C(15,k)·C(15,l) / 2^30
# ─────────────────────────────────────────────────────────────
def build_probs_binomial():
    p_list = []
    for k in range(16):
        for l in range(16):
            p_list.append(comb(15,k) * comb(15,l) / 2**30)
    return np.array(p_list)                 # shape (256,)

# ─────────────────────────────────────────────────────────────
# STEP 3: COHERENT STATE IN FOCK BASIS
# F[n_idx, i] = <i|α_n> = exp(-|α|²/2) · α^i / √(i!)
# ─────────────────────────────────────────────────────────────
def build_fock_matrix(alpha_list, Ncut):
    N = len(alpha_list)
    # precompute log(i!) for numerical stability
    log_fac = np.zeros(Ncut)
    for i in range(1, Ncut):
        log_fac[i] = log_fac[i-1] + np.log(i)

    F = np.zeros((N, Ncut), dtype=complex)
    for n_idx, al in enumerate(alpha_list):
        prefactor = np.exp(-0.5 * abs(al)**2)
        for i in range(Ncut):
            F[n_idx, i] = prefactor * (al**i) / np.exp(0.5*log_fac[i])
    return F                                # shape (256, Ncut)

# ─────────────────────────────────────────────────────────────
# STEP 4: DENSITY MATRIX τ IN FOCK BASIS
# τ_fock[i,j] = Σ_n p_n · F[n,i]* · F[n,j]
#             = (F† · diag(p) · F)[i,j]
# ─────────────────────────────────────────────────────────────
def build_tau(F, p):
    # F: (256, Ncut),  p: (256,)
    return (F.conj().T * p[None,:]) @ F     # shape (Ncut, Ncut)

# ─────────────────────────────────────────────────────────────
# STEP 5: τ^½ AND τ^(-½) VIA EIGENDECOMPOSITION
# τ = V D V†  →  τ^½ = V √D V†,  τ^(-½) = V (1/√D) V†
# τ^(-½) only inverts eigenvalues above threshold tol
# ─────────────────────────────────────────────────────────────
def compute_tau_sqrt_invsqrt(tau, tol=1e-12):
    eigvals, V = eigh(tau)                  # eigvals sorted ascending, real
    eigvals    = np.maximum(eigvals, 0.0)   # clip tiny negatives

    sqrt_ev    = np.sqrt(eigvals)
    inv_sqrt_ev = np.where(eigvals > tol, 1.0/sqrt_ev, 0.0)

    tau_sqrt    = (V * sqrt_ev[None,:])    @ V.conj().T
    tau_invsqrt = (V * inv_sqrt_ev[None,:]) @ V.conj().T
    return tau_sqrt, tau_invsqrt, eigvals

# ─────────────────────────────────────────────────────────────
# STEP 6: ANNIHILATION OPERATOR â IN FOCK BASIS
# â|n⟩ = √n |n-1⟩  →  a_op[n-1, n] = √n
# ─────────────────────────────────────────────────────────────
def build_a_operator(Ncut):
    a_op = np.zeros((Ncut, Ncut), dtype=complex)
    for j in range(1, Ncut):
        a_op[j-1, j] = sqrt(j)
    return a_op

# ─────────────────────────────────────────────────────────────
# STEP 7: Tr(τ^½ â τ^½ â†)
# ─────────────────────────────────────────────────────────────
def compute_Tr_C(tau_sqrt, a_op):
    adag = a_op.conj().T
    C    = tau_sqrt @ a_op @ tau_sqrt @ adag
    return np.real(np.trace(C))

# ─────────────────────────────────────────────────────────────
# STEP 8: a_τ = τ^½ · â · τ^(-½)
# Then compute w:
#   M_t1 = a_τ† · a_τ
#   term1_k = v_k† M_t1 v_k
#   term2_k = |v_k† a_τ v_k|²
#   w = Σ_k p_k (term1_k - term2_k)
# ─────────────────────────────────────────────────────────────
def compute_w(tau_sqrt, tau_invsqrt, a_op, F, p):
    a_tau = tau_sqrt @ a_op @ tau_invsqrt   # τ^½ â τ^(-½)
    M_t1  = a_tau.conj().T @ a_tau          # a_τ† a_τ, precompute

    w      = 0.0
    sum_t1 = 0.0
    sum_t2 = 0.0

    for n_idx in range(len(p)):
        v     = F[n_idx]                            # <i|α_n>, shape (Ncut,)

        t1    = np.real(v.conj() @ M_t1 @ v)       # v† (a_τ† a_τ) v
        inner = v.conj() @ a_tau @ v                # v† a_τ v  (complex)
        t2    = np.abs(inner)**2                    # |v† a_τ v|²

        w      += p[n_idx] * (t1 - t2)
        sum_t1 += p[n_idx] * t1
        sum_t2 += p[n_idx] * t2

    return w, sum_t1, sum_t2

# ─────────────────────────────────────────────────────────────
# STEP 9: Z*
# Z* = 2√T · Tr(τ^½ â τ^½ â†) − √(2Tε) · w
# ─────────────────────────────────────────────────────────────
def compute_Zstar(Tr_C, w, T, eps):
    return 2*sqrt(T)*Tr_C - sqrt(2*T*eps*w)


# ─────────────────────────────────────────────────────────────
# STEP 10: g(x) — von Neumann entropy function
# g(x) = (x+1)·log₂(x+1) − x·log₂(x)
# QUAN TRỌNG: truyền vào x = (λ−1)/2, KHÔNG phải λ trực tiếp
# ─────────────────────────────────────────────────────────────
def g(x):
    if x < 0:
        return 0.0
    if x < 1e-15:
        return 0.0
    return (x + 1) * math.log2(x + 1) - x * math.log2(x)


# ─────────────────────────────────────────────────────────────
# STEP 11: SYMPLECTIC EIGENVALUES λ₁, λ₂, λ₃
# Covariance matrix Γ*_AB = [[a, c], [c, b]]
#   a = VA+1
#   b = 1+T·VA+T·ε
#   c = Z*
# Δ = a²+b²−2c²
# B = (ab−c²)²
# disc = Δ²−4B
# λ₁,₂ = √[(Δ ± √disc)/2]
# λ₃   = (VA+1) − c²/(2+T·VA+T·ε)   [heterodyne]
# ─────────────────────────────────────────────────────────────
def compute_eigenvalues(VA, Zstar, T, eps):
    a    = VA + 1.0
    b    = 1.0 + T*VA + T*eps
    c    = Zstar

    Delta = a**2 + b**2 - 2*c**2
    B     = (a*b - c**2)**2
    disc  = Delta**2 - 4*B

    if disc < 0:
        # numerical issue: set disc=0
        disc = 0.0

    sd   = math.sqrt(disc)
    l1   = math.sqrt(max(0.5*(Delta + sd), 0.0))
    l2   = math.sqrt(max(0.5*(Delta - sd), 0.0))
    l3   = max(a - c**2 / (2.0 + T*VA + T*eps), 1e-15)

    return l1, l2, l3, Delta, B, disc


# ─────────────────────────────────────────────────────────────
# STEP 12: χ_BE (Holevo bound on Eve's information)
# χ_BE = g((λ₁−1)/2) + g((λ₂−1)/2) − g((λ₃−1)/2)
# ─────────────────────────────────────────────────────────────
def compute_chi_BE(l1, l2, l3):
    return g((l1-1)/2) + g((l2-1)/2) - g((l3-1)/2)


# ─────────────────────────────────────────────────────────────
# STEP 13: I_AB (mutual information, heterodyne)
# I_AB = log₂(1 + T·VA / (2 + T·χ_tot))
# χ_tot = χ_line + χ_det/T
#   χ_line = (1−T)/T + ε
#   χ_det  = (1−η + v_el)/η
# ─────────────────────────────────────────────────────────────
def compute_chi_tot(T, eps, eta, v_el):
    chi_line = (1.0 - T) / T + eps
    chi_det  = (1.0 - eta + v_el) / eta
    chi_tot  = chi_line + chi_det / T
    return chi_tot, chi_line, chi_det


def compute_IAB(VA, T, chi_tot):
    return math.log2(1.0 + T*VA / (2.0 + T*chi_tot))


# ─────────────────────────────────────────────────────────────
# STEP 14: SKR
# SKR = β·I_AB − χ_BE
# ─────────────────────────────────────────────────────────────
def compute_SKR(beta, IAB, chi_BE):
    return beta * IAB - chi_BE

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*60)
    print("Computing Z* for QAM-256 Binomial")
    print(f"alpha0 = 2√2 = {alpha0:.8f},  Ncut = {Ncut}")
    print(f"T = {T},  ε = {eps}")
    print("="*60)

    # Step 1–2
    alpha_list = build_constellation(alpha0)
    p          = build_probs_binomial()
    print(f"\nStep 1-2: {len(alpha_list)} symbols,  Σp = {p.sum():.15f}")

    # Step 3
    print("Step 3: Building Fock matrix F (256 × 25)...")
    F = build_fock_matrix(alpha_list, Ncut)
    norms = np.sum(np.abs(F)**2, axis=1)
    print(f"         Fock norms: min={norms.min():.8f}, max={norms.max():.8f}")

    # Step 4
    print("Step 4: Building density matrix τ (25 × 25)...")
    tau    = build_tau(F, p)
    tr_tau = np.real(np.trace(tau))
    print(f"         Tr(τ) = {tr_tau:.15f}  (should be ≈1)")

    # Step 5
    print("Step 5: Computing τ^½ and τ^(-½)...")
    tau_sqrt, tau_invsqrt, eigvals = compute_tau_sqrt_invsqrt(tau)
    err_sq = np.max(np.abs(tau_sqrt @ tau_sqrt - tau))
    print(f"         Verify τ^½ @ τ^½ = τ: max error = {err_sq:.2e}")
    rank = np.sum(eigvals > 1e-12)
    print(f"         Rank(τ) = {rank}/{Ncut}")

    # Step 6
    a_op = build_a_operator(Ncut)
    VA   = np.real(np.trace(tau @ a_op.conj().T @ a_op))
    print(f"\nStep 6: V_A = Tr(τ â†â) = {VA:.15f}")
    print(f"         V_A analytical  = 2.000000000000000")
    print(f"         Diff            = {abs(VA-2.0):.2e}  (Ncut truncation)")

    # Step 7
    print("\nStep 7: Computing Tr(τ^½ â τ^½ â†)...")
    Tr_C = compute_Tr_C(tau_sqrt, a_op)
    print(f"         Tr(τ^½ â τ^½ â†) = {Tr_C:.15f}")

    # Step 8
    print("\nStep 8: Computing w  (a_τ = τ^½ â τ^(-½))...")
    w, sum_t1, sum_t2 = compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)
    print(f"         Σ p_k × term1   = {sum_t1:.15f}")
    print(f"         Σ p_k × term2   = {sum_t2:.15f}")
    print(f"         w               = {w:.15f}")

    # Step 9
    print("\nStep 9: Computing Z*...")
    Zstar = compute_Zstar(Tr_C, w, T, eps)
    print(f"         2√T × Tr_C      = {2*sqrt(T)*Tr_C:.15f}")
    print(f"         √(2Tε) × w      = {sqrt(2*T*eps)*w:.15f}")
    print(f"         Z*              = {Zstar:.15f}")

    # Physical check
    a_cv  = VA + 1
    b_cv  = 1 + T*VA + T*eps
    Zmax  = sqrt(a_cv * b_cv)
    print(f"\n         Z*_max = √[(VA+1)(1+T·VA+T·ε)] = {Zmax:.10f}")
    print(f"         Z* < Z*_max? {Zstar:.6f} < {Zmax:.6f} → {Zstar < Zmax}")
    if not (0 < Zstar < Zmax):
        print("         ⚠ Z* UNPHYSICAL — check Ncut or alpha0")
    else:
        print("         ✓ Z* is physical")

    # Summary Z*
    print("\n" + "="*60)
    print("SUMMARY — Z*")
    print("="*60)
    print(f"  V_A    = {VA:.10f}  SNU")
    print(f"  Tr(C)  = {Tr_C:.10f}")
    print(f"  w      = {w:.10f}")
    print(f"  Z*     = {Zstar:.10f}  SNU")
    print(f"  Z*_max = {Zmax:.10f}  SNU")

    # ─────────────────────────────────────────────────────────
    # SKR COMPUTATION
    # ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SKR COMPUTATION")
    print("="*60)

    # Chi_tot
    chi_tot, chi_line, chi_det = compute_chi_tot(T, eps, eta, v_el)
    print(f"\nStep 10: Noise parameters")
    print(f"  chi_line = (1−T)/T + ε       = {chi_line:.10f}")
    print(f"  chi_det  = (1−η+v_el)/η      = {chi_det:.10f}")
    print(f"  chi_tot  = chi_line+chi_det/T = {chi_tot:.10f}")

    # Eigenvalues
    print(f"\nStep 11: Symplectic eigenvalues")
    l1, l2, l3, Delta, B, disc = compute_eigenvalues(VA, Zstar, T, eps)
    a_cv = VA+1; b_cv = 1+T*VA+T*eps
    print(f"  a = VA+1              = {a_cv:.10f}")
    print(f"  b = 1+T·VA+T·ε       = {b_cv:.10f}")
    print(f"  c = Z*                = {Zstar:.10f}")
    print(f"  Δ = a²+b²−2c²        = {Delta:.10f}")
    print(f"  B = (ab−c²)²         = {B:.10f}")
    print(f"  disc = Δ²−4B         = {disc:.10f}")
    print(f"  λ₁ = {l1:.15f}")
    print(f"  λ₂ = {l2:.15f}")
    print(f"  λ₃ = {l3:.15f}")
    print(f"  (λ₁−1)/2 = {(l1-1)/2:.10f}")
    print(f"  (λ₂−1)/2 = {(l2-1)/2:.10f}")
    print(f"  (λ₃−1)/2 = {(l3-1)/2:.10f}")

    # chi_BE
    print(f"\nStep 12: Holevo bound χ_BE")
    gl1 = g((l1-1)/2); gl2 = g((l2-1)/2); gl3 = g((l3-1)/2)
    chi_BE_val = compute_chi_BE(l1, l2, l3)
    print(f"  g((λ₁−1)/2) = g({(l1-1)/2:.6f}) = {gl1:.15f}")
    print(f"  g((λ₂−1)/2) = g({(l2-1)/2:.6f}) = {gl2:.15f}")
    print(f"  g((λ₃−1)/2) = g({(l3-1)/2:.6f}) = {gl3:.15f}")
    print(f"  χ_BE = {gl1:.8f} + {gl2:.8f} − {gl3:.8f}")
    print(f"       = {chi_BE_val:.15f}")

    # I_AB
    print(f"\nStep 13: Mutual information I_AB (heterodyne)")
    IAB_val = compute_IAB(VA, T, eps)
    print(f"  I_AB = log₂(1 + T·VA/(2+T·χ_tot))")
    print(f"       = log₂(1 + {T}·{VA:.4f}/({2+T*chi_tot:.6f}))")
    print(f"       = {IAB_val:.15f}")


    # SKR
    print(f"\nStep 14: Secret Key Rate")
    SKR_raw = compute_SKR(beta, IAB_val, chi_BE_val)
    SKR_val = max(SKR_raw, 0.0)
    print(f"  SKR_raw = β·I_AB − χ_BE")
    print(f"          = {beta}×{IAB_val:.8f} − {chi_BE_val:.8f}")
    print(f"          = {beta*IAB_val:.10f} − {chi_BE_val:.10f}")
    print(f"          = {SKR_raw:.15f}")
    print(f"  SKR     = max(SKR_raw, 0) = {SKR_val:.15f}")

    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"  Protocol : QAM-256 Binomial")
    print(f"  alpha0   = 2√2 = {alpha0:.6f}")
    print(f"  T        = {T},  ε = {eps},  β = {beta}")
    print(f"  η        = {eta},  v_el = {v_el}")
    print(f"  ─────────────────────────────────")
    print(f"  V_A      = {VA:.10f}  SNU")
    print(f"  Z*       = {Zstar:.10f}  SNU")
    print(f"  χ_tot    = {chi_tot:.10f}  SNU")
    print(f"  ─────────────────────────────────")
    print(f"  λ₁       = {l1:.10f}")
    print(f"  λ₂       = {l2:.10f}")
    print(f"  λ₃       = {l3:.10f}")
    print(f"  ─────────────────────────────────")
    print(f"  χ_BE     = {chi_BE_val:.10f}  bits")
    print(f"  I_AB     = {IAB_val:.10f}  bits")
    print(f"  SKR_raw  = {SKR_raw:.10f}  bits/use")
    print(f"  SKR      = {SKR_val:.10f}  bits/use  {'✓ POSITIVE' if SKR_val > 0 else '✗ ZERO (negative clamped)'}")
