"""Plot the exact median-state secret-key-rate comparison.

This figure is intentionally limited to the one frozen median channel state
stored in ``PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json``.  It does not
construct a channel sweep or infer poor/good-state values.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "results" / "PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "figures_preliminary"

# Reuse the repository plotting guard when the project root is not already on
# sys.path (as is typical when this file is invoked by its path).
sys.path.insert(0, str(PROJECT_ROOT))
from src.utils.plotting import require_raw_data_path  # noqa: E402


EXPECTED_MEDIAN = {
    "T": 0.022181763383054068,
    "epsilon": 0.02025322309984713,
    "ps_va": 0.0003801578161163992,
    "full": 0.0003328325002894157,
    "mb": -0.00045919497163375914,
}

METHODS = (
    {
        "key": "ps_va",
        "label": r"PS + $V_A$",
        "value_label": r"$+3.80\times10^{-4}$",
        "color": "#0072B2",
        "position": 0.95,
        "line_width": 2.8,
        "marker_size": 9.0,
    },
    {
        "key": "full",
        "label": r"Full ($\mathrm{PS}+\mathrm{GS}+V_A$)",
        "value_label": r"$+3.33\times10^{-4}$",
        "color": "#D55E00",
        "position": 2.05,
        "line_width": 2.3,
        "marker_size": 8.0,
    },
    {
        "key": "mb",
        "label": "MB",
        "value_label": r"$-4.59\times10^{-4}$",
        "color": "#333333",
        "position": 3.15,
        "line_width": 2.0,
        "marker_size": 8.0,
    },
)


def _require_expected(name: str, actual: float, expected: float) -> None:
    """Fail closed if the canonical artifact is not the supplied result."""

    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-18):
        raise ValueError(
            f"Unexpected {name}: artifact has {actual!r}, expected {expected!r}"
        )


def load_median_data(raw_data_path: Path = RAW_DATA_PATH) -> dict[str, float]:
    """Load and validate only the frozen median-state values used by the plot."""

    require_raw_data_path(raw_data_path)
    with raw_data_path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)

    if artifact.get("artifact_class") != "PS_VA_SOURCE_MOMENTS_CONVERGED":
        raise ValueError("The figure requires the converged PS+V_A source-moment artifact.")
    if artifact.get("status") != "PS_VA_SOURCE_MOMENTS_CONVERGED":
        raise ValueError("The source artifact is not in the converged state.")

    median = artifact["median_full_Z_exact"]
    ranking = artifact["median_ranking"]["scores_raw_K"]
    values = {
        "T": float(median["T"]),
        "epsilon": float(median["epsilon_total"]),
        "ps_va": float(ranking["ps_va"]),
        "full": float(ranking["full"]),
        "mb": float(ranking["mb"]),
    }
    for name, expected in EXPECTED_MEDIAN.items():
        _require_expected(name, values[name], expected)

    if artifact["median_ranking"]["order_best_to_worst"] != ["ps_va", "full", "mb"]:
        raise ValueError("The artifact does not contain the expected median-state ranking.")
    if not (values["ps_va"] > values["full"] > values["mb"]):
        raise ValueError("The stored raw secret-key rates do not have the expected ordering.")
    if not (values["mb"] < 0.0 < values["full"] < values["ps_va"]):
        raise ValueError("The stored raw secret-key rates do not straddle the zero threshold as expected.")

    return values


def _scaled_axis(value: float, _position: int) -> str:
    """Format values already expressed in units of 1e-4."""

    if abs(value) < 1e-12:
        value = 0.0
    return f"{value:g}".replace("-", "−")


def make_figure(data: dict[str, float], *, slide: bool = False) -> plt.Figure:
    """Create either the report figure or the cleaner slide variant."""

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "axes.labelsize": 11 if not slide else 14,
            "axes.titlesize": 14 if not slide else 21,
            "xtick.labelsize": 9 if not slide else 11,
            "ytick.labelsize": 9 if not slide else 12,
        }
    )

    figure = plt.figure(figsize=(6.5, 4.2) if not slide else (7.2, 4.6), facecolor="white")
    axes = figure.add_axes((0.14, 0.20, 0.82, 0.60) if not slide else (0.13, 0.18, 0.83, 0.66))
    axes.set_facecolor("white")

    y_values = {method["key"]: data[method["key"]] * 1e4 for method in METHODS}
    x_limits = (0.35, 3.72)
    axes.set_xlim(*x_limits)
    axes.set_ylim(-5.5, 4.8)
    axes.xaxis.set_visible(False)
    axes.yaxis.set_major_locator(FixedLocator([-5.0, -2.5, 0.0, 2.5, 4.5]))
    axes.yaxis.set_major_formatter(FuncFormatter(_scaled_axis))
    axes.set_ylabel(r"Secret key rate $K$ ($\times 10^{-4}$)", labelpad=8)
    axes.grid(axis="y", color="#d9d9d9", linewidth=0.55, alpha=0.7, zorder=0)

    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["bottom"].set_visible(False)
    axes.spines["left"].set_color("#555555")
    axes.spines["left"].set_linewidth(0.8)
    axes.tick_params(axis="y", colors="#333333", width=0.7, length=3.5)

    axes.axhline(
        0.0,
        color="#555555",
        linewidth=1.0,
        linestyle=(0, (4, 3)),
        zorder=1,
    )
    axes.text(
        x_limits[1] - 0.02,
        0.18,
        "zero-key threshold",
        ha="right",
        va="bottom",
        fontsize=8.5 if not slide else 10.5,
        color="#555555",
    )

    for method in METHODS:
        key = method["key"]
        x_center = method["position"]
        y_value = y_values[key]
        line_start, line_end = x_center - 0.30, x_center + 0.30

        axes.plot(
            [line_start, line_end],
            [y_value, y_value],
            color=method["color"],
            linewidth=method["line_width"] + (0.5 if slide else 0.0),
            solid_capstyle="round",
            zorder=3,
        )
        axes.plot(
            x_center,
            y_value,
            marker="o",
            markersize=method["marker_size"] + (1.5 if slide else 0.0),
            markerfacecolor=method["color"],
            markeredgecolor="white",
            markeredgewidth=1.2,
            linestyle="None",
            zorder=4,
        )

        axes.text(
            x_center + 0.38,
            y_value,
            method["label"],
            ha="left",
            va="center",
            fontsize=10.2 if not slide else 13.2,
            fontweight="bold" if key == "ps_va" else "normal",
            color="#222222",
        )
        value_offset = 0.40 if key != "mb" else -0.40
        axes.text(
            x_center,
            y_value + value_offset,
            method["value_label"],
            ha="center",
            va="bottom" if key != "mb" else "top",
            fontsize=9.1 if not slide else 12.0,
            color=method["color"],
        )

    if not slide:
        axes.annotate(
            "Best exact median result",
            xy=(METHODS[0]["position"], y_values["ps_va"]),
            xytext=(1.48, 4.68),
            ha="left",
            va="top",
            fontsize=8.5,
            color=METHODS[0]["color"],
            arrowprops={
                "arrowstyle": "-",
                "color": METHODS[0]["color"],
                "linewidth": 0.75,
                "shrinkA": 2,
                "shrinkB": 2,
            },
        )

    title = "Preliminary Exact Security Result" if slide else "Exact SKR Comparison at Median Channel State"
    figure.suptitle(title, x=0.5, y=0.965 if slide else 0.955, fontsize=21 if slide else 14, fontweight="bold")

    if slide:
        figure.text(
            0.5,
            0.895,
            r"Median channel state · exact values only",
            ha="center",
            va="center",
            fontsize=12.5,
            color="#555555",
        )
        figure.text(
            0.5,
            0.055,
            r"Median-state ranking: PS + $V_A$ > Full > MB",
            ha="center",
            va="center",
            fontsize=12.0,
            color="#333333",
        )
    else:
        figure.text(
            0.5,
            0.895,
            "Repaired full-Z security objective",
            ha="center",
            va="center",
            fontsize=9.5,
            color="#555555",
        )
        figure.text(
            0.5,
            0.095,
            r"Exact evaluation at median channel state: $T = 0.02218$, $\epsilon = 0.02025$",
            ha="center",
            va="center",
            fontsize=9.3,
            color="#333333",
        )
        figure.text(
            0.5,
            0.050,
            r"Poor/good PS+$V_A$ exact results pending",
            ha="center",
            va="center",
            fontsize=8.6,
            color="#666666",
            style="italic",
        )

    return figure


def main() -> None:
    data = load_median_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report_figure = make_figure(data)
    report_png = OUTPUT_DIR / "exact_median_skr.png"
    report_pdf = OUTPUT_DIR / "exact_median_skr.pdf"
    report_figure.savefig(report_png, dpi=300, bbox_inches="tight", facecolor="white")
    report_figure.savefig(report_pdf, bbox_inches="tight", facecolor="white")
    plt.close(report_figure)

    slide_figure = make_figure(data, slide=True)
    slide_png = OUTPUT_DIR / "exact_median_skr_slide.png"
    slide_figure.savefig(slide_png, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(slide_figure)

    print(f"Source: {RAW_DATA_PATH}")
    print(f"Report PNG: {report_png}")
    print(f"Report PDF: {report_pdf}")
    print(f"Slide PNG: {slide_png}")
    print("Plotted raw K values:", {key: data[key] for key in ("ps_va", "full", "mb")})


if __name__ == "__main__":
    main()
