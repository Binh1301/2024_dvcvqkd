"""Plot exact deterministic-GH MB SKR points at V_A=2 for nu in [0.05, 0.20]."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "exact_mb_reconciliation" / "same_point_reconciliation.csv"
OUTPUT = ROOT / "results" / "joint_mb_va_global" / "skr_mb_va2_exact_range_005_020.png"


def main() -> int:
    with CSV.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    points = [
        {"nu": float(row["nu_raw"]), "skr": float(row["new_deterministic_SKR"])}
        for row in rows
        if abs(float(row["VA_actual"]) - 2.0) <= 1e-10
        and 0.05 <= float(row["nu_raw"]) <= 0.20
    ]
    points.sort(key=lambda row: row["nu"])
    if not points:
        raise RuntimeError("No exact V_A=2 points found.")
    best = max(points, key=lambda row: row["skr"])

    plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
    figure, ax = plt.subplots(figsize=(8.8, 5.4), dpi=160)
    values = [row["skr"] for row in points]
    ax.set_xlim(0.05, 0.20)
    ax.set_ylim(min(values) - 0.12 * (max(values) - min(values)), max(values) + 0.22 * (max(values) - min(values)))
    ax.set_xlabel(r"MB parameter $\nu_{\rm raw}$")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title(r"Exact MB SKR at fixed $V_A=2$", weight="bold", pad=14)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.7, alpha=0.75)
    ax.grid(axis="x", color="#e2e8f0", linewidth=0.5, alpha=0.45)
    ax.axhline(0.0, color="#64748b", linewidth=0.8, linestyle=(0, (4, 3)))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Break the line wherever exact points are missing; no interpolation is implied.
    groups: list[list[dict[str, float]]] = []
    for point in points:
        if not groups or point["nu"] - groups[-1][-1]["nu"] > 0.011:
            groups.append([])
        groups[-1].append(point)
    for group in groups:
        ax.plot(
            [row["nu"] for row in group],
            [row["skr"] for row in group],
            color="#2563eb",
            linewidth=2.2,
            marker="o",
            markersize=7,
            markeredgecolor="white",
            markeredgewidth=0.8,
            zorder=4,
        )
    ax.scatter([best["nu"]], [best["skr"]], marker="*", s=220, color="#dc2626", edgecolors="#111827", linewidths=0.8, zorder=7)
    ax.annotate(
        f"best exact: $\\nu_{{raw}}$={best['nu']:.2f}\nSKR={best['skr']:.8e}",
        xy=(best["nu"], best["skr"]),
        xytext=(best["nu"] - 0.045, best["skr"] + 0.25 * (max(values) - min(values))),
        fontsize=9,
        color="#991b1b",
        arrowprops={"arrowstyle": "-", "color": "#dc2626", "linewidth": 0.8},
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#fef2f2", "edgecolor": "#fca5a5"},
    )
    ax.legend(
        handles=[
            Line2D([0], [0], color="#2563eb", marker="o", linewidth=2.2, label="Exact deterministic-GH points"),
            Line2D([0], [0], color="#dc2626", marker="*", linestyle="None", markersize=11, label="Best exact point"),
        ],
        loc="lower right",
        fontsize=9,
        frameon=True,
    )
    figure.text(0.5, 0.018, "Exact available points only; missing $\\nu_{raw}$ values are not interpolated.", ha="center", va="bottom", fontsize=9, color="#64748b")
    figure.subplots_adjust(left=0.12, right=0.96, bottom=0.14, top=0.87)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(figure)

    print(f"points={len(points)}")
    for row in points:
        print(f"nu_raw={row['nu']:.6g}, V_A=2, SKR={row['skr']:.15e}")
    print(f"best=nu_raw={best['nu']:.6g}, SKR={best['skr']:.15e}")
    print(f"output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
