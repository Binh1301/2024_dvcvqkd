"""Plot the current exact interior/boundary joint-SKR comparison."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "joint_mb_va_global"
OUTPUT = RESULTS / "skr_comparison_current.png"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def exact_row(rows: list[dict[str, str]], nu: float, va: float) -> dict[str, str]:
    matches = [
        row for row in rows
        if row.get("coverage_status") == "EXACT_AP_COMPLETE"
        and abs(float(row["nu_raw"]) - nu) < 1e-12
        and abs(float(row["VA"]) - va) < 1e-12
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one exact row for nu_raw={nu}, VA={va}; found {len(matches)}")
    return matches[0]


def main() -> int:
    report = json.loads((RESULTS / "run_report.json").read_text(encoding="utf-8"))
    if report.get("status") != "GLOBAL_OPTIMUM_UNRESOLVED":
        raise RuntimeError("This figure is intended for the unresolved exact-tested comparison state.")

    interior = report["best_tested_exact"]
    boundary = report["best_boundary_tested"]
    local_rows = read_csv(RESULTS / "ap_coverage" / "local.csv")
    boundary_rows = read_csv(RESULTS / "ap_coverage_boundary" / "boundary.csv")
    interior = exact_row(local_rows, float(interior["nu_raw"]), float(interior["VA"]))
    boundary = exact_row(boundary_rows, float(boundary["nu_raw"]), float(boundary["VA"]))

    k_interior = float(interior["SKR"])
    k_boundary = float(boundary["SKR"])
    delta = k_interior - k_boundary
    percent = 100.0 * delta / k_boundary
    labels = ["Best exact\ninterior", "Best exact\nboundary"]
    values = np.array([k_interior, k_boundary], dtype=float)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    })
    fig, ax = plt.subplots(figsize=(8.4, 5.5), dpi=160)
    bars = ax.bar(
        labels,
        values,
        width=0.58,
        color=["#2563eb", "#64748b"],
        edgecolor="#1f2937",
        linewidth=0.8,
        zorder=3,
    )
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("Current exact joint $(\\nu, V_A)$ SKR comparison", pad=14, weight="bold")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.7, alpha=0.75, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0.0, float(values.max()) * 1.55)

    for bar, row in zip(bars, (interior, boundary)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + values.max() * 0.035,
            f"SKR = {float(row['SKR']):.8e}\n"
            f"$\\nu_{{raw}}$ = {float(row['nu_raw']):.3f}, "
            f"$V_A$ = {float(row['VA']):.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#111827",
        )

    ax.text(
        0.98,
        0.96,
        "$\\Delta K = K_{interior} - K_{boundary}$\n"
        f"$\\Delta K$ = {delta:.8e} bits/use\n"
        f"Relative to boundary = {percent:.4f}%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#eff6ff", "edgecolor": "#93c5fd"},
    )
    ax.text(
        0.02,
        0.96,
        "Global optimum unresolved\nUniform optimized baseline not yet certified",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#991b1b",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#fef2f2", "edgecolor": "#fca5a5"},
    )
    fig.text(
        0.5,
        0.015,
        "Exact AP coverage incomplete; comparison reflects current best exact tested points only.",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#475569",
    )
    fig.subplots_adjust(bottom=0.18, top=0.87, left=0.12, right=0.96)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"interior SKR = {k_interior:.15e}")
    print(f"boundary SKR = {k_boundary:.15e}")
    print(f"delta absolute = {delta:.15e} bits/use")
    print(f"delta percent vs boundary = {percent:.8f}%")
    print("note = global optimum unresolved; uniform optimized baseline not yet certified")
    print(f"output = {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
