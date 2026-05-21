"""
General numerical study for discrete-modulated coherent-state ensembles.

This script computes, for square QAM constellations with m = 4, 8, 16:
  - the density matrix tau in a truncated Fock basis,
  - tau^(1/2) and tau^(-1/2) by eigendecomposition,
  - C = Tr(tau^(1/2) a tau^(1/2) a^dagger),
  - w = sum_k p_k [ <alpha_k| a_tau^dagger a_tau |alpha_k>
                   - |<alpha_k| a_tau |alpha_k>|^2 ],
    with a_tau = tau^(1/2) a tau^(-1/2),
  - eigenvalue spectra and positivity diagnostics,
  - convergence versus Ncut.

Supported distributions:
  - binomial
  - uniform

The script prints a compact numeric table and saves a CSV summary in
the local outputs/ directory.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from math import comb, sqrt
from scipy.linalg import eigh
from scipy.special import gammaln


DEFAULT_M_VALUES = (4, 8, 16)
DEFAULT_DISTRIBUTIONS = ("binomial", "uniform")
DEFAULT_NCUT = 40
DEFAULT_NCUT_SWEEP = (25, 35, 45, 60)


@dataclass
class EnsembleResult:
    m: int
    distribution: str
    alpha0: float
    ncut: int
    va_theory: float
    va_numeric: float
    tr_tau: float
    c_value: float
    w_value: float
    min_eig: float
    max_eig: float
    rank: int
    neg_eig_mass: float
    tau_hermitian_error: float
    alt_w_left: float
    alt_w_sandwich: float


def build_constellation(alpha0: float, m: int) -> list[complex]:
    """Build the square QAM constellation with m levels per axis."""
    scale = sqrt(2.0 * (m - 1))
    offset = (m - 1) / 2.0
    alpha_list: list[complex] = []
    for k in range(m):
        for l in range(m):
            alpha = alpha0 / scale * ((k - offset) + 1j * (l - offset))
            alpha_list.append(alpha)
    return alpha_list


def build_probs(m: int, distribution: str) -> np.ndarray:
    """Build symbol probabilities for a square QAM ensemble."""
    if distribution == "uniform":
        return np.full(m * m, 1.0 / (m * m), dtype=float)

    if distribution == "binomial":
        n = m - 1
        probs = []
        norm = 2 ** (2 * n)
        for k in range(m):
            for l in range(m):
                probs.append(comb(n, k) * comb(n, l) / norm)
        return np.array(probs, dtype=float)

    raise ValueError(f"Unsupported distribution: {distribution}")


def coherent_state(alpha: complex, ncut: int) -> np.ndarray:
    """Return |alpha> in the Fock basis with log-space stabilization."""
    vec = np.zeros(ncut, dtype=complex)
    abs_alpha = abs(alpha)
    if abs_alpha == 0.0:
        vec[0] = 1.0
        return vec

    log_abs_alpha = math.log(abs_alpha)
    phase = np.angle(alpha)
    for n in range(ncut):
        log_amp = -0.5 * abs_alpha * abs_alpha + n * log_abs_alpha - 0.5 * gammaln(n + 1)
        vec[n] = np.exp(log_amp) * np.exp(1j * n * phase)
    return vec


def build_fock_matrix(alpha_list: Iterable[complex], ncut: int) -> np.ndarray:
    """Build the matrix F[n_idx, n] = <n|alpha_idx>."""
    alpha_list = list(alpha_list)
    F = np.zeros((len(alpha_list), ncut), dtype=complex)
    for idx, alpha in enumerate(alpha_list):
        F[idx] = coherent_state(alpha, ncut)
    return F


def build_tau(F: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Build tau = sum_k p_k |alpha_k><alpha_k| in the Fock basis."""
    tau = (F.conj().T * p[None, :]) @ F
    tau = 0.5 * (tau + tau.conj().T)
    return tau


def compute_tau_sqrt_invsqrt(tau: np.ndarray, tol: float = 1e-12):
    """Compute tau^(1/2) and tau^(-1/2) via spectral decomposition."""
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


def build_a_operator(ncut: int) -> np.ndarray:
    """Annihilation operator in the truncated Fock basis."""
    a_op = np.zeros((ncut, ncut), dtype=complex)
    for j in range(1, ncut):
        a_op[j - 1, j] = sqrt(j)
    return a_op


def compute_c_value(tau_sqrt: np.ndarray, a_op: np.ndarray) -> float:
    adag = a_op.conj().T
    c_mat = tau_sqrt @ a_op @ tau_sqrt @ adag
    return float(np.real(np.trace(c_mat)))


def compute_a_tau(
    tau_sqrt: np.ndarray,
    tau_invsqrt: np.ndarray,
    a_op: np.ndarray,
    mode: str = "similarity",
) -> np.ndarray:
    """Construct a_tau in several forms for comparison."""
    if mode == "similarity":
        return tau_sqrt @ a_op @ tau_invsqrt
    if mode == "left":
        return a_op @ (tau_sqrt @ tau_invsqrt)
    if mode == "sandwich":
        return tau_sqrt @ a_op @ tau_sqrt
    raise ValueError(f"Unsupported a_tau mode: {mode}")


def compute_w_from_a_tau(F: np.ndarray, p: np.ndarray, a_tau: np.ndarray) -> float:
    """Compute w for a fixed a_tau operator."""
    m_t1 = a_tau.conj().T @ a_tau
    total = 0.0
    for idx in range(len(p)):
        v = F[idx]
        term1 = np.real(v.conj() @ m_t1 @ v)
        inner = v.conj() @ a_tau @ v
        term2 = np.abs(inner) ** 2
        total += p[idx] * (term1 - term2)
    return float(total)


def theoretical_va(m: int, distribution: str, alpha0: float) -> float:
    if distribution == "binomial":
        return alpha0 * alpha0 / 4.0
    if distribution == "uniform":
        return alpha0 * alpha0 * (m + 1) / 12.0
    raise ValueError(f"Unsupported distribution: {distribution}")


def run_case(alpha0: float, m: int, distribution: str, ncut: int) -> EnsembleResult:
    alpha_list = build_constellation(alpha0, m)
    p = build_probs(m, distribution)
    F = build_fock_matrix(alpha_list, ncut)
    tau = build_tau(F, p)
    tau_sqrt, tau_invsqrt, eigvals = compute_tau_sqrt_invsqrt(tau)
    a_op = build_a_operator(ncut)

    va_numeric = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    tr_tau = float(np.real(np.trace(tau)))
    c_value = compute_c_value(tau_sqrt, a_op)

    a_tau = compute_a_tau(tau_sqrt, tau_invsqrt, a_op, mode="similarity")
    alt_a_tau_left = compute_a_tau(tau_sqrt, tau_invsqrt, a_op, mode="left")
    alt_a_tau_sandwich = compute_a_tau(tau_sqrt, tau_invsqrt, a_op, mode="sandwich")

    w_value = compute_w_from_a_tau(F, p, a_tau)
    alt_w_left = compute_w_from_a_tau(F, p, alt_a_tau_left)
    alt_w_sandwich = compute_w_from_a_tau(F, p, alt_a_tau_sandwich)

    hermitian_error = float(np.max(np.abs(tau - tau.conj().T)))
    min_eig = float(np.min(eigvals)) if len(eigvals) else 0.0
    max_eig = float(np.max(eigvals)) if len(eigvals) else 0.0
    rank = int(np.sum(eigvals > 1e-12))
    neg_eig_mass = float(np.sum(np.clip(-eigvals, 0.0, None)))

    return EnsembleResult(
        m=m,
        distribution=distribution,
        alpha0=alpha0,
        ncut=ncut,
        va_theory=theoretical_va(m, distribution, alpha0),
        va_numeric=va_numeric,
        tr_tau=tr_tau,
        c_value=c_value,
        w_value=w_value,
        min_eig=min_eig,
        max_eig=max_eig,
        rank=rank,
        neg_eig_mass=neg_eig_mass,
        tau_hermitian_error=hermitian_error,
        alt_w_left=alt_w_left,
        alt_w_sandwich=alt_w_sandwich,
    )


def ensure_output_dir() -> Path:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def print_case(result: EnsembleResult) -> None:
    label = f"{result.m}x{result.m} {result.distribution}"
    print("-" * 88)
    print(f"Ensemble: {label}")
    print(f"  alpha0 = {result.alpha0:.10f}, Ncut = {result.ncut}")
    print(f"  VA theory  = {result.va_theory:.12f}")
    print(f"  VA numeric  = {result.va_numeric:.12f}")
    print(f"  Tr(tau)    = {result.tr_tau:.15f}")
    print(f"  C          = {result.c_value:.15f}")
    print(f"  w          = {result.w_value:.15f}")
    print(f"  tau min eig = {result.min_eig:.3e}")
    print(f"  tau max eig = {result.max_eig:.3e}")
    print(f"  tau rank    = {result.rank}")
    print(f"  tau Hermitian error = {result.tau_hermitian_error:.3e}")
    print(f"  negative eigenvalue mass = {result.neg_eig_mass:.3e}")
    print(f"  w(left)     = {result.alt_w_left:.15f}")
    print(f"  w(sandwich) = {result.alt_w_sandwich:.15f}")


def print_summary_table(results: list[EnsembleResult]) -> None:
    header = (
        f"{'ensemble':<16} {'VA(th)':>14} {'VA(num)':>14} {'Tr(tau)':>14} "
        f"{'C':>14} {'w':>14} {'min eig':>14} {'rank':>8}"
    )
    print("=" * len(header))
    print(header)
    print("=" * len(header))
    for r in results:
        name = f"{r.m}x{r.m}-{r.distribution}"
        print(
            f"{name:<16} "
            f"{r.va_theory:14.8f} {r.va_numeric:14.8f} {r.tr_tau:14.8f} "
            f"{r.c_value:14.8f} {r.w_value:14.8f} {r.min_eig:14.3e} {r.rank:8d}"
        )
    print("=" * len(header))


def print_convergence(alpha0: float, m: int, distribution: str, ncut_values: list[int]) -> None:
    print("\n" + "=" * 88)
    print(f"Convergence versus Ncut for {m}x{m} {distribution}")
    print("=" * 88)
    rows = [run_case(alpha0, m, distribution, ncut) for ncut in ncut_values]
    ref = rows[-1]
    print(f"{'Ncut':>6} {'VA(num)':>14} {'Tr(tau)':>14} {'C':>14} {'w':>14} {'|Δw| vs ref':>14}")
    for row in rows:
        print(
            f"{row.ncut:6d} {row.va_numeric:14.8f} {row.tr_tau:14.8f} {row.c_value:14.8f} "
            f"{row.w_value:14.8f} {abs(row.w_value - ref.w_value):14.3e}"
        )


def write_csv(results: list[EnsembleResult], csv_path: Path) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "m",
                "distribution",
                "alpha0",
                "ncut",
                "va_theory",
                "va_numeric",
                "tr_tau",
                "c_value",
                "w_value",
                "min_eig",
                "max_eig",
                "rank",
                "neg_eig_mass",
                "tau_hermitian_error",
                "alt_w_left",
                "alt_w_sandwich",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.m,
                    r.distribution,
                    r.alpha0,
                    r.ncut,
                    r.va_theory,
                    r.va_numeric,
                    r.tr_tau,
                    r.c_value,
                    r.w_value,
                    r.min_eig,
                    r.max_eig,
                    r.rank,
                    r.neg_eig_mass,
                    r.tau_hermitian_error,
                    r.alt_w_left,
                    r.alt_w_sandwich,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute C and w for square QAM coherent-state ensembles."
    )
    parser.add_argument(
        "--alpha0",
        type=float,
        default=2 * sqrt(2),
        help="Base modulation amplitude used in the QAM scaling.",
    )
    parser.add_argument(
        "--ncut",
        type=int,
        default=DEFAULT_NCUT,
        help="Main Fock cutoff used for the summary table.",
    )
    parser.add_argument(
        "--ncut-sweep",
        type=str,
        default=",".join(str(v) for v in DEFAULT_NCUT_SWEEP),
        help="Comma-separated list of Ncut values for the convergence check.",
    )
    parser.add_argument(
        "--m-values",
        type=str,
        default=",".join(str(v) for v in DEFAULT_M_VALUES),
        help="Comma-separated list of QAM orders to evaluate, using m = 4, 8, 16.",
    )
    parser.add_argument(
        "--distributions",
        type=str,
        default=",".join(DEFAULT_DISTRIBUTIONS),
        help="Comma-separated list of probability laws: binomial, uniform.",
    )
    return parser.parse_args()


def parse_int_list(text: str) -> list[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def parse_str_list(text: str) -> list[str]:
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def main() -> None:
    args = parse_args()
    m_values = parse_int_list(args.m_values)
    distributions = parse_str_list(args.distributions)
    ncut_sweep = parse_int_list(args.ncut_sweep)

    for m in m_values:
        if m not in DEFAULT_M_VALUES:
            raise ValueError(f"Unsupported m={m}. Expected one of {DEFAULT_M_VALUES}.")

    for distribution in distributions:
        if distribution not in DEFAULT_DISTRIBUTIONS:
            raise ValueError(
                f"Unsupported distribution '{distribution}'. Expected one of {DEFAULT_DISTRIBUTIONS}."
            )

    print("=" * 88)
    print("Discrete-modulated coherent-state ensemble diagnostics")
    print("=" * 88)
    print(f"alpha0 = {args.alpha0:.10f}")
    print(f"main Ncut = {args.ncut}")
    print(f"Ncut sweep = {ncut_sweep}")
    print(f"m values   = {m_values}")
    print(f"laws       = {distributions}")

    results: list[EnsembleResult] = []
    for m in m_values:
        for distribution in distributions:
            result = run_case(args.alpha0, m, distribution, args.ncut)
            results.append(result)
            print_case(result)

    print_summary_table(results)

    for m in m_values:
        for distribution in distributions:
            print_convergence(args.alpha0, m, distribution, ncut_sweep)

    out_dir = ensure_output_dir()
    csv_path = out_dir / "qam_metrics_general_summary.csv"
    write_csv(results, csv_path)
    print("\nSaved CSV summary to:")
    print(f"  {csv_path}")

    print("\nInterpretation notes:")
    print("  - Binomial ensembles keep V_A = alpha0^2 / 4 by construction.")
    print("  - Uniform ensembles scale as V_A = ((m + 1) / 12) * alpha0^2.")
    print("  - C measures the tau-weighted correlation term Tr(tau^(1/2) a tau^(1/2) a^dagger).")
    print("  - w measures the ensemble average of the a_tau fluctuation term.")
    print("  - Large Ncut should stabilize Tr(tau), C, and w; the sweep quantifies that convergence.")


if __name__ == "__main__":
    main()