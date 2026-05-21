"""
Visualize the generalized QAM ensemble metrics.

This script reads the CSV summary produced by qam_metrics_general.py and
generates two figures:
  - a comparison chart for V_A, C, w, and truncation diagnostics,
  - a convergence plot for w versus Ncut across all supported ensembles.

Output files are saved in the local outputs/ directory.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from qam_metrics_general import DEFAULT_DISTRIBUTIONS, DEFAULT_M_VALUES, run_case


SUMMARY_CSV = Path(__file__).resolve().parent / "outputs" / "qam_metrics_general_summary.csv"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
DEFAULT_ALPHA0 = 2 * np.sqrt(2)
DEFAULT_NCUTS = [25, 35, 45, 60]


@dataclass
class Row:
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


def load_summary(csv_path: Path) -> list[Row]:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing summary file: {csv_path}. Run qam_metrics_general.py first."
        )

    rows: list[Row] = []
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for item in reader:
            rows.append(
                Row(
                    m=int(item["m"]),
                    distribution=item["distribution"],
                    alpha0=float(item["alpha0"]),
                    ncut=int(item["ncut"]),
                    va_theory=float(item["va_theory"]),
                    va_numeric=float(item["va_numeric"]),
                    tr_tau=float(item["tr_tau"]),
                    c_value=float(item["c_value"]),
                    w_value=float(item["w_value"]),
                    min_eig=float(item["min_eig"]),
                    max_eig=float(item["max_eig"]),
                    rank=int(item["rank"]),
                    neg_eig_mass=float(item["neg_eig_mass"]),
                    tau_hermitian_error=float(item["tau_hermitian_error"]),
                    alt_w_left=float(item["alt_w_left"]),
                    alt_w_sandwich=float(item["alt_w_sandwich"]),
                )
            )
    return rows


def get_row(rows: list[Row], m: int, distribution: str) -> Row:
    for row in rows:
        if row.m == m and row.distribution == distribution:
            return row
    raise KeyError(f"Missing row for m={m}, distribution={distribution}")


def ensure_out_dir() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR


def plot_summary(rows: list[Row], out_dir: Path) -> Path:
    labels = [f"{row.m}x{row.m}\n{row.distribution}" for row in rows]
    x = np.arange(len(rows))
    width = 0.34

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    fig.suptitle("QAM coherent-state ensemble diagnostics", fontsize=16, fontweight="bold")

    va_err = [abs(row.va_numeric - row.va_theory) for row in rows]
    tr_deficit = [abs(1.0 - row.tr_tau) for row in rows]
    eig_floor = [max(row.min_eig, 1e-18) for row in rows]

    ax = axes[0, 0]
    ax.bar(x, [row.va_theory for row in rows], width=width, label="V_A theory", color="#264653")
    ax.bar(x + width, [row.va_numeric for row in rows], width=width, label="V_A numeric", color="#2a9d8f")
    ax.set_title("Modulation variance")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(labels, rotation=0)
    ax.grid(alpha=0.25, axis="y")
    ax.legend(frameon=False)

    ax = axes[0, 1]
    ax.bar(x, [row.c_value for row in rows], width=width, label="C", color="#e76f51")
    ax.bar(x + width, [row.w_value for row in rows], width=width, label="w", color="#f4a261")
    ax.set_title("Correlation C and fluctuation w")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_yscale("log")
    ax.grid(alpha=0.25, axis="y", which="both")
    ax.legend(frameon=False)

    ax = axes[1, 0]
    ax.bar(x, va_err, width=0.5, color="#457b9d")
    ax.bar(x + 0.5, tr_deficit, width=0.5, color="#8d99ae")
    ax.set_title("Truncation diagnostics")
    ax.set_xticks(x + 0.25)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_yscale("log")
    ax.grid(alpha=0.25, axis="y", which="both")
    ax.legend(["|V_A(num) - V_A(th)|", "|1 - Tr(tau)|"], frameon=False)

    ax = axes[1, 1]
    ax.bar(x, eig_floor, width=0.5, color="#6d597a")
    ax.set_title("Smallest eigenvalue of tau")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_yscale("log")
    ax.grid(alpha=0.25, axis="y", which="both")

    summary_path = out_dir / "qam_metrics_summary.png"
    fig.savefig(summary_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary_path


def plot_convergence(out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), constrained_layout=True)
    fig.suptitle("Convergence of w versus Ncut", fontsize=16, fontweight="bold")

    for ax, distribution in zip(axes, DEFAULT_DISTRIBUTIONS, strict=True):
        for m in DEFAULT_M_VALUES:
            series = [run_case(DEFAULT_ALPHA0, m, distribution, ncut) for ncut in DEFAULT_NCUTS]
            ax.plot(
                [item.ncut for item in series],
                [item.w_value for item in series],
                marker="o",
                lw=2,
                label=f"{m}x{m}",
            )
        ax.set_title(f"{distribution.capitalize()} prior")
        ax.set_xlabel("Ncut")
        ax.set_ylabel("w")
        ax.set_yscale("log")
        ax.grid(alpha=0.25, which="both")
        ax.legend(frameon=False)

    conv_path = out_dir / "qam_w_convergence.png"
    fig.savefig(conv_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return conv_path


def main() -> None:
    out_dir = ensure_out_dir()
    rows = load_summary(SUMMARY_CSV)
    summary_path = plot_summary(rows, out_dir)
    conv_path = plot_convergence(out_dir)

    print("Saved figures:")
    print(f"  {summary_path}")
    print(f"  {conv_path}")


if __name__ == "__main__":
    main()