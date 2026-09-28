"""Minimal exact MB fixed-V_A=2 versus best joint point figure."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = RESULTS / "joint_mb_va_global" / "skr_mb_fixed_va2_vs_optimized.png"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    fixed_rows = read_csv(RESULTS / "exact_mb_asymptotic" / "extended_landscape.csv")
    fixed = [
        {"nu_raw": float(row["nu_raw"]), "VA": float(row["VA_actual"]), "SKR": float(row["SKR"])}
        for row in fixed_rows
        if row.get("SKR") and abs(float(row["VA_actual"]) - 2.0) <= 1e-10
    ]
    fixed.sort(key=lambda row: row["nu_raw"])
    if not fixed:
        raise RuntimeError("No exact fixed-V_A=2 MB rows found.")

    report = read_json(RESULTS / "joint_mb_va_global" / "run_report.json")
    if report.get("status") != "GLOBAL_OPTIMUM_UNRESOLVED":
        raise RuntimeError("Expected current GLOBAL_OPTIMUM_UNRESOLVED classification.")
    joint_report = report["best_tested_exact"]
    joint = {
        "nu_raw": float(joint_report["nu_raw"]),
        "VA": float(joint_report["VA"]),
        "SKR": float(joint_report["SKR"]),
    }
    best_fixed = max(fixed, key=lambda row: row["SKR"])
    delta = joint["SKR"] - best_fixed["SKR"]

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })
    figure, ax = plt.subplots(figsize=(8.8, 5.4), dpi=160)
    figure.patch.set_facecolor("white")
    ax.plot(
        [row["nu_raw"] for row in fixed],
        [row["SKR"] for row in fixed],
        color="#2563eb",
        linewidth=2.2,
        marker="o",
        markersize=7,
        markerfacecolor="#2563eb",
        markeredgecolor="white",
        markeredgewidth=0.8,
        label=r"MB fixed $V_A=2$",
        zorder=4,
    )
    ax.scatter(
        [best_fixed["nu_raw"]], [best_fixed["SKR"]],
        s=130,
        marker="o",
        facecolor="#f59e0b",
        edgecolor="#111827",
        linewidth=1.0,
        zorder=7,
    )
    ax.scatter(
        [joint["nu_raw"]], [joint["SKR"]],
        s=225,
        marker="*",
        facecolor="#dc2626",
        edgecolor="#111827",
        linewidth=0.9,
        zorder=8,
    )
    ax.axhline(joint["SKR"], color="#dc2626", linewidth=0.8, linestyle=(0, (4, 3)), alpha=0.65, zorder=1)
    values = [row["SKR"] for row in fixed] + [joint["SKR"]]

    ax.annotate(
        f"$\\nu_{{raw}}$={best_fixed['nu_raw']:.2f}, $V_A$=2",
        xy=(best_fixed["nu_raw"], best_fixed["SKR"]),
        xytext=(best_fixed["nu_raw"] - 0.038, best_fixed["SKR"] - 0.35 * (max(values) - min(values))),
        fontsize=9,
        color="#92400e",
        arrowprops={"arrowstyle": "-", "color": "#f59e0b", "linewidth": 0.8},
    )
    ax.annotate(
        f"$\\nu_{{raw}}$={joint['nu_raw']:.2f}, $V_A$={joint['VA']:.2f}",
        xy=(joint["nu_raw"], joint["SKR"]),
        xytext=(joint["nu_raw"] - 0.040, joint["SKR"] + 0.35 * (max(values) - min(values))),
        fontsize=9,
        color="#991b1b",
        arrowprops={"arrowstyle": "-", "color": "#dc2626", "linewidth": 0.8},
    )
    ax.text(
        0.98,
        0.95,
        f"$\\Delta K$ = {delta:.4e} bits/use",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#fef2f2", "edgecolor": "#fca5a5"},
    )

    ax.set_title("MB fixed-$V_A=2$ versus optimized joint point", weight="bold", pad=14)
    ax.set_xlabel(r"MB parameter $\nu_{\rm raw}$")
    ax.set_ylabel("SKR (bits/use)")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.set_xlim(min(row["nu_raw"] for row in fixed) - 0.018, max(row["nu_raw"] for row in fixed) + 0.035)
    low, high = min(values), max(values)
    pad = 0.55 * (high - low)
    ax.set_ylim(low - pad, high + pad)
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.7, alpha=0.75, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        handles=[
            Line2D([0], [0], color="#2563eb", marker="o", linewidth=2.2, label=r"MB fixed $V_A=2$"),
            Line2D([0], [0], color="#f59e0b", marker="o", linestyle="None", markersize=8, label="Best fixed point"),
            Line2D([0], [0], color="#dc2626", marker="*", linestyle="None", markersize=11, label="Best joint exact tested"),
        ],
        loc="lower right",
        fontsize=9,
        frameon=True,
    )
    figure.text(0.5, 0.018, "Best tested points only", ha="center", va="bottom", fontsize=9, color="#64748b")
    figure.subplots_adjust(left=0.12, right=0.96, bottom=0.14, top=0.87)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(figure)

    print("fixed V_A=2 points:")
    for row in fixed:
        print(f"  nu_raw={row['nu_raw']:.6g}, V_A=2, SKR={row['SKR']:.15e}")
    print(f"best fixed SKR = {best_fixed['SKR']:.15e}")
    print(f"optimized joint = nu_raw={joint['nu_raw']:.6g}, V_A={joint['VA']:.6g}, SKR={joint['SKR']:.15e}")
    print(f"absolute difference = {delta:.15e} bits/use")
    print(f"output = {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
