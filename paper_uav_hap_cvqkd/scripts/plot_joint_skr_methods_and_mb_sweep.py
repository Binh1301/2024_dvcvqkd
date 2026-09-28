"""Plot current exact Uniform/Binomial/MB/joint-SKR comparison."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
GLOBAL = RESULTS / "joint_mb_va_global"
OUTPUT = GLOBAL / "skr_comparison_methods_and_mb_sweep.png"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def f(row: dict, key: str) -> float:
    return float(row[key])


def exact_global_row(row: dict) -> bool:
    return row.get("evaluation_status") == "EXACT_CACHE_EVALUATION" and row.get("exact_evaluation") == "YES"


def exact_coverage_row(row: dict) -> bool:
    return row.get("coverage_status") == "EXACT_AP_COMPLETE"


def load_fixed_mb_points() -> list[dict]:
    rows = read_csv(RESULTS / "exact_mb_asymptotic" / "extended_landscape.csv")
    points = []
    for row in rows:
        if not row.get("SKR"):
            continue
        points.append({
            "nu_raw": f(row, "nu_raw"),
            "VA": f(row, "VA_actual"),
            "SKR": f(row, "SKR"),
            "context": "fixed_VA_2_exact",
        })
    return sorted(points, key=lambda row: row["nu_raw"])


def load_joint_points() -> list[dict]:
    paths_and_predicates = (
        (GLOBAL / "global_landscape.csv", exact_global_row),
        (GLOBAL / "boundary_search.csv", exact_global_row),
        (GLOBAL / "ap_coverage" / "local.csv", exact_coverage_row),
        (GLOBAL / "ap_coverage_boundary" / "boundary.csv", exact_coverage_row),
    )
    points: dict[tuple[float, float], dict] = {}
    for path, predicate in paths_and_predicates:
        for row in read_csv(path):
            if not predicate(row) or not row.get("SKR"):
                continue
            nu = f(row, "nu_raw")
            va = f(row, "VA")
            if nu < 0.1:
                continue
            points.setdefault(
                (round(nu, 14), round(va, 14)),
                {"nu_raw": nu, "VA": va, "SKR": f(row, "SKR"), "context": "joint_exact_tested"},
            )
    return sorted(points.values(), key=lambda row: (row["nu_raw"], row["VA"]))


def load_current_summary() -> dict:
    report = read_json(GLOBAL / "run_report.json")
    if report.get("status") != "GLOBAL_OPTIMUM_UNRESOLVED":
        raise RuntimeError("Expected current classification GLOBAL_OPTIMUM_UNRESOLVED.")

    uniform = report["best_uniform_tested"]
    if uniform.get("baseline_status") != "SPARSE_CACHE_ONLY_NOT_OPTIMIZED":
        raise RuntimeError("Uniform status changed; inspect baseline authority before plotting.")
    if uniform.get("evaluation_status") != "EXACT_CACHE_EVALUATION":
        raise RuntimeError("Uniform comparison point is not an exact evaluation.")

    joint = report["best_tested_exact"]
    boundary = report["best_boundary_tested"]
    if boundary.get("evaluation_status") != "EXACT_CACHE_EVALUATION":
        raise RuntimeError("Boundary comparison point is not an exact evaluation.")

    baseline_selection = read_json(RESULTS / "validation_baseline_selection.json")
    binomial_pending = baseline_selection.get("status") != "CURRENTLY_VERIFIED_PASS"
    local_report = read_json(GLOBAL / "ap_coverage" / "local_report.json")
    boundary_report = read_json(GLOBAL / "ap_coverage_boundary" / "boundary_report.json")
    uniform_report = read_json(GLOBAL / "ap_coverage_uniform" / "uniform_report.json")
    return {
        "report": report,
        "uniform": {"nu_raw": f(uniform, "nu_raw"), "VA": f(uniform, "VA"), "SKR": f(uniform, "SKR")},
        "joint": {"nu_raw": f(joint, "nu_raw"), "VA": f(joint, "VA"), "SKR": f(joint, "SKR")},
        "boundary": {"nu_raw": f(boundary, "nu_raw"), "VA": f(boundary, "VA"), "SKR": f(boundary, "SKR")},
        "binomial_pending": binomial_pending,
        "coverage": {
            "global": (report["coverage"]["global_grid_exact_rows"], report["coverage"]["global_grid_rows"]),
            "local": (local_report["exact_points"], local_report["requested_points"]),
            "boundary": (boundary_report["exact_points"], boundary_report["requested_points"]),
            "uniform": (uniform_report["exact_points"], uniform_report["requested_points"]),
        },
    }


def annotate_bar(ax, x: float, value: float | None, text: str, *, color: str, hatch: str = "") -> None:
    if value is None:
        ax.bar(x, 0.0, width=0.58, facecolor="white", edgecolor=color, hatch=hatch, linewidth=1.4, zorder=3)
        ax.text(x, 1.2e-6, text, ha="center", va="bottom", fontsize=8.5, color=color, weight="bold")
        return
    bar = ax.bar(x, value, width=0.58, color=color, edgecolor="#1f2937", linewidth=0.8, zorder=3)[0]
    offset = 1.6e-6 if value >= 0 else 1.1e-6
    va = "bottom"
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + offset,
        text,
        ha="center",
        va=va,
        fontsize=8.1,
        color="#111827",
    )


def main() -> int:
    summary = load_current_summary()
    fixed_mb = load_fixed_mb_points()
    joint_points = load_joint_points()
    if not fixed_mb:
        raise RuntimeError("No current exact fixed-V_A MB points found.")
    if not joint_points:
        raise RuntimeError("No current exact joint MB points found.")

    uniform = summary["uniform"]
    joint = summary["joint"]
    boundary = summary["boundary"]
    fixed_best = max(fixed_mb, key=lambda row: row["SKR"])
    binomial_pending = summary["binomial_pending"]

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })
    figure, (methods_ax, mb_ax) = plt.subplots(
        1, 2, figsize=(13.2, 6.8), sharey=True,
        gridspec_kw={"width_ratios": [0.85, 1.65], "wspace": 0.08},
    )
    figure.patch.set_facecolor("white")
    y_values = [uniform["SKR"], joint["SKR"], *(row["SKR"] for row in fixed_mb), *(row["SKR"] for row in joint_points)]
    y_min = min(y_values + [-5.5e-5])
    y_max = max(y_values + [3.4e-5])
    y_pad = 0.08 * (y_max - y_min)
    y_limits = (y_min - y_pad, y_max + y_pad)

    for ax in (methods_ax, mb_ax):
        ax.set_ylim(*y_limits)
        ax.grid(axis="y", color="#cbd5e1", linewidth=0.65, alpha=0.75, zorder=0)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
        ax.axhline(0.0, color="#475569", linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)

    # Left panel: method bars. Binomial is an explicitly non-numeric pending slot.
    methods_ax.set_title("Current method comparison", weight="bold")
    methods_ax.set_ylabel("SKR (bits/use)")
    methods_ax.set_xticks([0, 1, 2], ["Uniform", "Binomial", "Optimized\njoint"])
    annotate_bar(
        methods_ax,
        0,
        uniform["SKR"],
        f"{uniform['SKR']:.4e}\n"
        f"$\\nu_{{raw}}$={uniform['nu_raw']:.3f}, $V_A$={uniform['VA']:.3f}\n"
        "best exact tested\n(baseline unresolved)",
        color="#94a3b8",
    )
    annotate_bar(
        methods_ax,
        1,
        None,
        "PENDING\nno current exact\nBinomial baseline",
        color="#9ca3af",
        hatch="///",
    )
    annotate_bar(
        methods_ax,
        2,
        joint["SKR"],
        f"{joint['SKR']:.4e}\n"
        f"$\\nu_{{raw}}^*$={joint['nu_raw']:.3f}, $V_A^*$={joint['VA']:.3f}\n"
        "best exact tested joint\n(global unresolved)",
        color="#2563eb",
    )
    methods_ax.legend(
        handles=[
            Patch(facecolor="#94a3b8", edgecolor="#1f2937", label="Uniform: best exact tested"),
            Patch(facecolor="white", edgecolor="#9ca3af", hatch="///", label="Binomial: pending"),
            Patch(facecolor="#2563eb", edgecolor="#1f2937", label="Joint: best exact tested"),
        ],
        loc="upper left",
        fontsize=8,
        frameon=True,
    )

    # Right panel: exact MB sweep. Fixed V_A=2 is a line; joint points are not interpolated.
    mb_ax.set_title("Exact MB points and joint tested points", weight="bold")
    mb_ax.set_xlabel(r"MB parameter $\nu_{\rm raw}$")
    mb_ax.plot(
        [row["nu_raw"] for row in fixed_mb],
        [row["SKR"] for row in fixed_mb],
        color="#d97706",
        linewidth=1.8,
        marker="o",
        markersize=6,
        label=r"MB fixed $V_A=2$ (exact)",
        zorder=4,
    )
    joint_scatter = mb_ax.scatter(
        [row["nu_raw"] for row in joint_points],
        [row["SKR"] for row in joint_points],
        c=[row["VA"] for row in joint_points],
        cmap="viridis",
        s=34,
        alpha=0.78,
        edgecolors="white",
        linewidths=0.45,
        label="Joint exact tested rows",
        zorder=5,
    )
    colorbar = figure.colorbar(joint_scatter, ax=mb_ax, pad=0.02, fraction=0.046)
    colorbar.set_label(r"$V_A$ (SNU)", rotation=90)
    mb_ax.scatter(
        [joint["nu_raw"]], [joint["SKR"]],
        marker="*", s=190, color="#dc2626", edgecolors="black", linewidths=0.7,
        zorder=7, label="Best exact tested joint point",
    )
    mb_ax.annotate(
        f"best joint exact tested\n"
        f"($\\nu_{{raw}}$={joint['nu_raw']:.3f}, $V_A$={joint['VA']:.3f})",
        xy=(joint["nu_raw"], joint["SKR"]),
        xytext=(joint["nu_raw"] + 0.012, joint["SKR"] + 4.0e-6),
        fontsize=8.5,
        arrowprops={"arrowstyle": "-", "color": "#dc2626", "linewidth": 0.8},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#fef2f2", "edgecolor": "#fca5a5"},
    )
    mb_ax.annotate(
        f"best fixed-$V_A$ MB\n"
        f"($\\nu_{{raw}}$={fixed_best['nu_raw']:.3f})",
        xy=(fixed_best["nu_raw"], fixed_best["SKR"]),
        xytext=(fixed_best["nu_raw"] + 0.012, fixed_best["SKR"] - 5.0e-6),
        fontsize=8.2,
        arrowprops={"arrowstyle": "-", "color": "#d97706", "linewidth": 0.8},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#fffbeb", "edgecolor": "#fbbf24"},
    )
    mb_ax.legend(loc="lower right", fontsize=8, frameon=True)
    mb_ax.set_xlim(0.08, max(0.31, max(row["nu_raw"] for row in joint_points) + 0.02))

    figure.suptitle("CV-QKD optimization: current exact method comparison and MB sweep", fontsize=15, weight="bold", y=0.98)
    figure.text(
        0.5,
        0.935,
        "Only exact available results are plotted; missing categories are pending, not interpolated.",
        ha="center",
        va="center",
        fontsize=9,
        color="#475569",
    )
    figure.text(
        0.5,
        0.018,
        "Global optimum unresolved  ·  Uniform optimized baseline not yet certified  ·  "
        f"coverage: global {summary['coverage']['global'][0]}/{summary['coverage']['global'][1]}, "
        f"local {summary['coverage']['local'][0]}/{summary['coverage']['local'][1]}, "
        f"boundary {summary['coverage']['boundary'][0]}/{summary['coverage']['boundary'][1]}, "
        f"uniform {summary['coverage']['uniform'][0]}/{summary['coverage']['uniform'][1]}",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#64748b",
    )
    figure.subplots_adjust(left=0.08, right=0.94, bottom=0.14, top=0.88)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)

    print("method,SKR,key_parameters,status")
    print(f"Uniform,{uniform['SKR']:.15e},nu_raw=0; VA={uniform['VA']:.6g},BEST_EXACT_TESTED_BASELINE_UNRESOLVED")
    print("Binomial,,pending,no_current_valid_exact_baseline")
    print(f"Optimized joint,{joint['SKR']:.15e},nu_raw={joint['nu_raw']:.6g}; VA={joint['VA']:.6g},BEST_EXACT_TESTED_GLOBAL_UNRESOLVED")
    print(f"MB fixed VA=2,{len(fixed_mb)} exact points,nu_raw range {fixed_mb[0]['nu_raw']:.6g}-{fixed_mb[-1]['nu_raw']:.6g},EXACT")
    print(f"MB joint tested,{len(joint_points)} exact points,nu_raw range {joint_points[0]['nu_raw']:.6g}-{joint_points[-1]['nu_raw']:.6g},EXACT_TESTED_NOT_GLOBAL")
    print(f"best fixed-VA=2 MB: nu_raw={fixed_best['nu_raw']:.6g}, SKR={fixed_best['SKR']:.15e}")
    print(f"output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
