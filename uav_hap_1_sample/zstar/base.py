import math
from math import comb, sqrt

import numpy as np
from scipy.linalg import eigh


def build_constellation(alpha0: float) -> list[complex]:
    alpha_list: list[complex] = []
    for k in range(16):
        for l in range(16):
            a = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
            alpha_list.append(a)
    return alpha_list


def build_probs_binomial() -> np.ndarray:
    p_list = []
    for k in range(16):
        for l in range(16):
            p_list.append(comb(15, k) * comb(15, l) / 2**30)
    return np.array(p_list, dtype=float)


def build_probs_uniform() -> np.ndarray:
    return np.full(256, 1.0 / 256.0, dtype=float)


def build_probs_mb(nu_tilde: float) -> np.ndarray:
    nu = float(nu_tilde)
    ks = np.arange(16, dtype=float)
    weights = np.exp(-nu * (ks - 7.5) ** 2)
    prob = np.outer(weights, weights).reshape(-1)
    prob_sum = prob.sum()
    if prob_sum <= 0:
        raise ValueError("Invalid nu_tilde leading to non-positive normalization.")
    prob /= prob_sum
    return prob.astype(float)


def build_fock_matrix(alpha_list: list[complex], ncut: int) -> np.ndarray:
    log_fac = np.zeros(ncut)
    for i in range(1, ncut):
        log_fac[i] = log_fac[i - 1] + np.log(i)

    F = np.zeros((len(alpha_list), ncut), dtype=complex)
    for n_idx, al in enumerate(alpha_list):
        log_al = np.log(al) if al != 0 else -np.inf
        for i in range(ncut):
            log_amp = -0.5 * (abs(al) ** 2) + (i * log_al) - 0.5 * log_fac[i]
            F[n_idx, i] = np.exp(log_amp)
    return F


def build_tau(F: np.ndarray, p: np.ndarray) -> np.ndarray:
    return (F.conj().T * p[None, :]) @ F


def compute_tau_sqrt_invsqrt(tau: np.ndarray, tol: float = 1e-12):
    """Compute tau^(1/2) and tau^(-1/2) safely, avoiding divide-by-zero."""
    eigvals, V = eigh(tau)
    eigvals = np.maximum(eigvals, 0.0)
    sqrt_ev = np.sqrt(eigvals)
    # Avoid divide-by-zero: only invert significant eigenvalues
    inv_sqrt_ev = np.zeros_like(sqrt_ev)
    mask = eigvals > tol
    inv_sqrt_ev[mask] = 1.0 / sqrt_ev[mask]
    tau_sqrt = (V * sqrt_ev[None, :]) @ V.conj().T
    tau_invsqrt = (V * inv_sqrt_ev[None, :]) @ V.conj().T
    return tau_sqrt, tau_invsqrt, eigvals


def build_a_operator(ncut: int) -> np.ndarray:
    a_op = np.zeros((ncut, ncut), dtype=complex)
    for j in range(1, ncut):
        a_op[j - 1, j] = sqrt(j)
    return a_op


def compute_tr_c(tau_sqrt: np.ndarray, a_op: np.ndarray) -> float:
    adag = a_op.conj().T
    C = tau_sqrt @ a_op @ tau_sqrt @ adag
    return float(np.real(np.trace(C)))


def compute_w(tau_sqrt: np.ndarray, tau_invsqrt: np.ndarray, a_op: np.ndarray, F: np.ndarray, p: np.ndarray):
    a_tau = tau_sqrt @ a_op @ tau_invsqrt
    M_t1 = a_tau.conj().T @ a_tau

    w = 0.0
    sum_t1 = 0.0
    sum_t2 = 0.0
    for n_idx in range(len(p)):
        v = F[n_idx]
        t1 = np.real(v.conj() @ M_t1 @ v)
        inner = v.conj() @ a_tau @ v
        t2 = np.abs(inner) ** 2
        w += p[n_idx] * (t1 - t2)
        sum_t1 += p[n_idx] * t1
        sum_t2 += p[n_idx] * t2

    return float(w), float(sum_t1), float(sum_t2)


def compute_zstar(tr_c: float, w: float, T: float, eps: float) -> float:
    return 2 * sqrt(T) * tr_c - sqrt(2 * T * eps * w)


def g(x: float) -> float:
    if x < 0:
        return 0.0
    if x < 1e-15:
        return 0.0
    return (x + 1) * math.log2(x + 1) - x * math.log2(x)


def compute_eigenvalues(VA: float, zstar: float, T: float, eps: float):
    a = VA + 1.0
    b = 1.0 + T * VA + T * eps
    c = zstar

    Delta = a**2 + b**2 - 2 * c**2
    B = (a * b - c**2) ** 2
    disc = Delta**2 - 4 * B
    if disc < 0:
        disc = 0.0

    sd = math.sqrt(disc)
    l1 = math.sqrt(max(0.5 * (Delta + sd), 0.0))
    l2 = math.sqrt(max(0.5 * (Delta - sd), 0.0))
    l3 = max(a - c**2 / (2.0 + T * VA + T * eps), 1e-15)
    return l1, l2, l3, Delta, B, disc


def compute_chi_BE(l1: float, l2: float, l3: float) -> float:
    return g((l1 - 1) / 2) + g((l2 - 1) / 2) - g((l3 - 1) / 2)


def compute_chi_tot(T: float, eps: float, eta: float, v_el: float):
    chi_line = (1.0 - T) / T + eps
    chi_det = (1.0 - eta + v_el) / eta
    chi_tot = chi_line + chi_det / T
    return float(chi_tot), float(chi_line), float(chi_det)


def gaussian_iab_reference(T: float, VA: float, epsilon: float) -> float:
    """Gaussian-input MI retained solely as the legacy reference."""
    return math.log2(1.0 + T * VA / (2.0 + T * epsilon))


def compute_IAB(VA: float, T: float, chi_tot: float) -> float:
    """Backward-compatible wrapper for the original Gaussian I_AB function."""
    return gaussian_iab_reference(T, VA, chi_tot)


def compute_SKR(beta: float, IAB: float, chi_BE: float) -> float:
    return beta * IAB - chi_BE
