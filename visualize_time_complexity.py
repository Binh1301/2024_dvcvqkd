"""Plot measured and asymptotic complexity for the six shaping strategies."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


METHODS = (
    "Uniform",
    "Maxwell-Boltzmann",
    "Binomial",
    "PS",
    "GS",
    "PS+GS",
)
CHECKPOINT_BOUNDARIES = {
    "PS": ("ps_epoch0.pt", "last_valid_ps.pt"),
    "GS": ("gs_epoch0.pt", "last_valid_gs.pt"),
    "PS+GS": ("geometry_warmup_epoch0.pt", "last_valid_joint.pt"),
}
COMPLEXITIES = {
    "Uniform": r"$\Theta(M)$",
    "Maxwell-Boltzmann": r"$\Theta(M)$",
    "Binomial": r"$\Theta(M)$",
    "PS": r"$\Theta(E_{\rm PS}\,\mathcal{C}_{\rm tr})$",
    "GS": r"$\Theta(E_{\rm GS}\,\mathcal{C}_{\rm tr})$",
    "PS+GS": (
        r"$\Theta((E_{\rm W}+E_{\rm J})\mathcal{C}_{\rm tr}"
        r"+E_{\rm R}\mathcal{C}_{\rm fin})$"
    ),
}
COLORS = {
    "Uniform": "#78998A",
    "Maxwell-Boltzmann": "#5F8875",
    "Binomial": "#456F61",
    "PS": "#D98C3F",
    "GS": "#3E7CA6",
    "PS+GS": "#B84D45",
}


def checkpoint_minutes(experiment_dir: Path) -> dict[str, float]:
    """Measure complete optimizer spans using the checkpoint boundaries."""
    minutes = {method: 0.0 for method in METHODS}
    checkpoint_dir = experiment_dir / "checkpoints"
    for method, (start_name, end_name) in CHECKPOINT_BOUNDARIES.items():
        start_path = checkpoint_dir / start_name
        end_path = checkpoint_dir / end_name
        if not start_path.is_file():
            raise FileNotFoundError(f"Missing checkpoint: {start_path}")
        if not end_path.is_file():
            raise FileNotFoundError(f"Missing checkpoint: {end_path}")
        elapsed = end_path.stat().st_mtime - start_path.stat().st_mtime
        if not math.isfinite(elapsed) or elapsed < 0.0:
            raise ValueError(f"Invalid checkpoint time span for {method}")
        minutes[method] = elapsed / 60.0
    return minutes


def plot_time_complexity(
    experiment_dir: Path,
    output_dir: Path,
    dpi: int = 300,
) -> tuple[Path, Path]:
    """Create one research figure in PNG and vector PDF formats."""
    elapsed_minutes = checkpoint_minutes(experiment_dir)
    values = np.asarray([elapsed_minutes[method] for method in METHODS])
    positions = np.arange(len(METHODS))

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 10.5,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    figure, (time_axis, order_axis) = plt.subplots(
        1,
        2,
        figsize=(10.8, 5.2),
        gridspec_kw={"width_ratios": (1.55, 1.0), "wspace": 0.08},
    )
    bars = time_axis.barh(
        positions,
        values,
        height=0.62,
        color=[COLORS[method] for method in METHODS],
        edgecolor="#263238",
        linewidth=0.65,
        zorder=3,
    )
    time_axis.set_yticks(positions, METHODS)
    time_axis.invert_yaxis()
    time_axis.set_xlabel("Measured optimization wall time (min)")
    time_axis.set_title("(a) Observed CPU cost", loc="left", fontweight="bold")
    time_axis.grid(axis="x", color="#D8D8D2", linewidth=0.75, zorder=0)
    time_axis.spines[["top", "right"]].set_visible(False)
    time_axis.set_xlim(0.0, max(10.5, float(values.max()) * 1.18))

    for method, value, bar in zip(METHODS, values, bars, strict=True):
        y_value = bar.get_y() + bar.get_height() / 2.0
        if value == 0.0:
            time_axis.scatter(
                [0.0],
                [y_value],
                marker="D",
                s=25,
                color=COLORS[method],
                edgecolor="#263238",
                linewidth=0.55,
                zorder=4,
                clip_on=False,
            )
            time_axis.text(
                0.16,
                y_value,
                "closed form; no iterative training",
                va="center",
                ha="left",
                fontsize=8.4,
                color="#38433E",
            )
        else:
            time_axis.text(
                value + 0.13,
                y_value,
                f"{value:.2f}",
                va="center",
                ha="left",
                fontsize=9.2,
                fontweight="bold",
                color="#263238",
            )

    order_axis.set_title("(b) Dominant asymptotic order", loc="left", fontweight="bold")
    order_axis.set_xlim(0.0, 1.0)
    order_axis.set_ylim(time_axis.get_ylim())
    order_axis.axis("off")
    for y_value, method in zip(positions, METHODS, strict=True):
        order_axis.plot(
            [0.02, 0.09],
            [y_value, y_value],
            color=COLORS[method],
            linewidth=5.0,
            solid_capstyle="round",
        )
        order_axis.text(0.13, y_value, method, va="center", ha="left", fontsize=9.5)
        order_axis.text(
            0.97,
            y_value,
            COMPLEXITIES[method],
            va="center",
            ha="right",
            fontsize=11,
        )

    order_axis.text(
        0.02,
        0.015,
        r"$\mathcal{C}(K,N)=B\left(M^2K+MN^2+N^3\right)$",
        transform=order_axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.5,
    )
    order_axis.text(
        0.02,
        -0.045,
        r"$M$: symbols, $K$: AWGN samples, $N$: Fock cutoff,"
        "\n"
        r"$B$: fading states; $E_{\rm W},E_{\rm J},E_{\rm R}$: joint stages.",
        transform=order_axis.transAxes,
        ha="left",
        va="top",
        fontsize=8.4,
        color="#4D5552",
    )

    figure.suptitle(
        "Computational cost of probabilistic and geometric shaping",
        fontsize=14.5,
        fontweight="bold",
        y=0.985,
    )
    figure.text(
        0.5,
        0.012,
        "256-QAM, CPU, float64/complex128. Fixed PMFs exclude the common SKR "
        "evaluation; learned-method times span epoch-zero to last-valid checkpoints.",
        ha="center",
        va="bottom",
        fontsize=8.2,
        color="#4D5552",
    )
    figure.subplots_adjust(left=0.16, right=0.98, top=0.88, bottom=0.17)

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "research_time_complexity.png"
    pdf_path = output_dir / "research_time_complexity.pdf"
    figure.savefig(png_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png_path, pdf_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot time complexity for fixed, PS, GS, and joint PS+GS methods."
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=Path("experiments/joint_seed2026"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/joint_seed2026/research_figures"),
    )
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    png_path, pdf_path = plot_time_complexity(
        args.experiment_dir,
        args.output_dir,
        args.dpi,
    )
    print(f"PNG: {png_path.resolve()}")
    print(f"PDF: {pdf_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
