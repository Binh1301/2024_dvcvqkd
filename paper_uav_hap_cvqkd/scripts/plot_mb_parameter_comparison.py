"""Plot current exact MB fixed-V_A and joint-MB SKR points."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
GLOBAL = RESULTS / "joint_mb_va_global"
OUTPUT = GLOBAL / "skr_mb_parameter_comparison.png"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def exact_global(row: dict[str, str]) -> bool:
    return row.get("evaluation_status") == "EXACT_CACHE_EVALUATION" and row.get("exact_evaluation") == "YES"


def exact_ap(row: dict[str, str]) -> bool:
    return row.get("coverage_status") == "EXACT_AP_COMPLETE"


def load_fixed_va2() -> list[dict[str, float]]:
    rows = read_csv(RESULTS / "exact_mb_asymptotic" / "extended_landscape.csv")
    points = []
    for row in rows:
        if not row.get("SKR") or abs(float(row["VA_actual"]) - 2.0) > 1e-10:
            continue
        points.append({
            "nu_raw": float(row["nu_raw"]),
            "VA": float(row["VA_actual"]),
            "SKR": float(row["SKR"]),
        })
    if not points:
        raise RuntimeError("No exact fixed-V_A=2 MB points found.")
    return sorted(points, key=lambda row: row["nu_raw"])


def load_joint_exact() -> list[dict[str, float]]:
    sources = (
        (GLOBAL / "global_landscape.csv", exact_global),
        (GLOBAL / "boundary_search.csv", exact_global),
        (GLOBAL / "ap_coverage" / "local.csv", exact_ap),
        (GLOBAL / "ap_coverage_boundary" / "boundary.csv", exact_ap),
    )
    points: dict[tuple[float, float], dict[str, float]] = {}
    for path, predicate in sources:
        for row in read_csv(path):
            if not predicate(row) or not row.get("SKR"):
                continue
            nu = float(row["nu_raw"])
            va = float(row["VA"])
            if nu < 0.1:
                continue
            points.setdefault(
                (round(nu, 14), round(va, 14)),
                {"nu_raw": nu, "VA": va, "SKR": float(row["SKR"])},
            )
    if not points:
        raise RuntimeError("No exact joint MB points found.")
    return sorted(points.values(), key=lambda row: (row["nu_raw"], row["VA"]))


def main() -> int:
    report = read_json(GLOBAL / "run_report.json")
    if report.get("status") != "GLOBAL_OPTIMUM_UNRESOLVED":
        raise RuntimeError("Expected GLOBAL_OPTIMUM_UNRESOLVED current classification.")
    fixed = load_fixed_va2()
    joint = load_joint_exact()
    best_fixed = max(fixed, key=lambda row: row["SKR"])
    best_joint_report = report["best_tested_exact"]
    best_joint = {
        "nu_raw": float(best_joint_report["nu_raw"]),
        "VA": float(best_joint_report["VA"]),
        "SKR": float(best_joint_report["SKR"]),
    }

    envelope = []
    grouped: dict[float, list[dict[str, float]]] = defaultdict(list)
    for row in joint:
        grouped[round(row["nu_raw"], 12)].append(row)
    for nu, rows in sorted(grouped.items()):
        best = max(rows, key=lambda row: row["SKR"])
        envelope.append(best)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "axes.titlesize": 15,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })
    figure, ax = plt.subplots(figsize=(10.8, 6.7), dpi=160)
    figure.patch.set_facecolor("white")
    y_values = [row["SKR"] for row in fixed + joint]
    y_min = min(y_values + [-1.0e-5])
    y_max = max(y_values + [2.5e-5])
    pad = 0.1 * (y_max - y_min)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.set_xlim(min(row["nu_raw"] for row in joint + fixed) - 0.012, max(row["nu_raw"] for row in joint + fixed) + 0.022)
    ax.set_xlabel(r"MB parameter $\nu_{\rm raw}$")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("MB parameter comparison: exact SKR points", weight="bold", pad=17)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.7, alpha=0.75, zorder=0)
    ax.grid(axis="x", color="#e2e8f0", linewidth=0.5, alpha=0.45, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(0.0, color="#475569", linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)

    ax.plot(
        [row["nu_raw"] for row in fixed],
        [row["SKR"] for row in fixed],
        color="#d97706",
        marker="o",
        markersize=7,
        linewidth=2.0,
        label=r"MB fixed $V_A=2$ (exact)",
        zorder=4,
    )
    scatter = ax.scatter(
        [row["nu_raw"] for row in joint],
        [row["SKR"] for row in joint],
        c=[row["VA"] for row in joint],
        cmap="viridis",
        s=45,
        alpha=0.82,
        edgecolors="white",
        linewidths=0.55,
        label="Joint MB exact tested",
        zorder=5,
    )
    colorbar = figure.colorbar(scatter, ax=ax, pad=0.018, fraction=0.046)
    colorbar.set_label(r"$V_A$ (SNU)", rotation=90)

    ax.plot(
        [row["nu_raw"] for row in envelope],
        [row["SKR"] for row in envelope],
        color="#334155",
        linestyle="--",
        linewidth=1.35,
        marker="s",
        markersize=4.2,
        alpha=0.85,
        label="Best exact tested SKR per $\\nu$ (joint)",
        zorder=4,
    )
    ax.scatter(
        [best_fixed["nu_raw"]], [best_fixed["SKR"]],
        marker="*", s=205, color="#f59e0b", edgecolors="black", linewidths=0.75,
        zorder=8,
    )
    ax.scatter(
        [best_joint["nu_raw"]], [best_joint["SKR"]],
        marker="*", s=235, color="#dc2626", edgecolors="black", linewidths=0.8,
        zorder=9,
    )
    ax.annotate(
        f"Best fixed-$V_A=2$ MB\n"
        f"$\\nu_{{raw}}$={best_fixed['nu_raw']:.3f}, $V_A$=2\n"
        f"SKR={best_fixed['SKR']:.8e}",
        xy=(best_fixed["nu_raw"], best_fixed["SKR"]),
        xytext=(best_fixed["nu_raw"] + 0.012, best_fixed["SKR"] - 4.5e-6),
        fontsize=9,
        arrowprops={"arrowstyle": "-", "color": "#d97706", "linewidth": 0.85},
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#fffbeb", "edgecolor": "#fbbf24"},
    )
    ax.annotate(
        f"Best joint exact tested MB\n"
        f"$\\nu_{{raw}}$={best_joint['nu_raw']:.3f}, $V_A$={best_joint['VA']:.3f}\n"
        f"SKR={best_joint['SKR']:.8e}",
        xy=(best_joint["nu_raw"], best_joint["SKR"]),
        xytext=(best_joint["nu_raw"] + 0.014, best_joint["SKR"] + 3.6e-6),
        fontsize=9,
        arrowprops={"arrowstyle": "-", "color": "#dc2626", "linewidth": 0.85},
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#fef2f2", "edgecolor": "#fca5a5"},
    )

    ax.legend(loc="lower right", fontsize=9, frameon=True)
    figure.text(
        0.5,
        0.935,
        "Only exact available results are plotted  ·  No interpolation, surrogate, or Monte Carlo production value",
        ha="center",
        va="center",
        fontsize=9.5,
        color="#475569",
    )
    figure.text(
        0.5,
        0.018,
        "MB parameter comparison  ·  GLOBAL_OPTIMUM_UNRESOLVED  ·  Exact AP coverage incomplete",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#991b1b",
    )
    figure.subplots_adjust(left=0.10, right=0.92, bottom=0.13, top=0.87)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)

    print("series,nu_raw,V_A,SKR,status")
    for row in fixed:
        print(f"MB_fixed_VA2,{row['nu_raw']:.12g},{row['VA']:.12g},{row['SKR']:.15e},EXACT")
    for row in joint:
        print(f"MB_joint_exact_tested,{row['nu_raw']:.12g},{row['VA']:.12g},{row['SKR']:.15e},EXACT_TESTED")
    print(f"best_fixed_VA2,{best_fixed['nu_raw']:.12g},2,{best_fixed['SKR']:.15e},BEST_FIXED_EXACT")
    print(f"best_joint_exact_tested,{best_joint['nu_raw']:.12g},{best_joint['VA']:.12g},{best_joint['SKR']:.15e},BEST_JOINT_GLOBAL_UNRESOLVED")
    print(f"output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
