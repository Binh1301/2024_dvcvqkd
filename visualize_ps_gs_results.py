#!/usr/bin/env python3
"""Create publication-style figures for the joint PS/GS experiment results.

Example:
    python visualize_ps_gs_results.py --results-dir experiments/joint_seed2026
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm


METHOD_ORDER = (
    "Uniform fixed QAM",
    "MB fixed QAM",
    "Learned PS fixed QAM",
    "Learned GS uniform probabilities",
    "Learned joint PS+GS",
)

METHOD_LABELS = {
    "Uniform fixed QAM": "Uniform QAM",
    "MB fixed QAM": "MB QAM",
    "Learned PS fixed QAM": "Learned PS",
    "Learned GS uniform probabilities": "Learned GS",
    "Learned joint PS+GS": "Joint PS+GS",
}

METHOD_COLORS = {
    "Uniform fixed QAM": "#7A7F85",
    "MB fixed QAM": "#A1A6AA",
    "Learned PS fixed QAM": "#376996",
    "Learned GS uniform probabilities": "#C28B2C",
    "Learned joint PS+GS": "#177E74",
}

CONSTELLATION_METHODS = (
    "Learned PS fixed QAM",
    "Learned GS uniform probabilities",
    "Learned joint PS+GS",
)


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9.0,
            "axes.titlesize": 10.0,
            "axes.labelsize": 9.0,
            "axes.linewidth": 0.8,
            "axes.edgecolor": "#30343B",
            "axes.labelcolor": "#20242A",
            "xtick.color": "#30343B",
            "ytick.color": "#30343B",
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "grid.color": "#D8DBDE",
            "grid.linewidth": 0.6,
            "grid.alpha": 0.8,
            "legend.frameon": False,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required result file not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(row: dict[str, str], field: str) -> float:
    try:
        return float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid or missing numeric field {field!r} in {row}") from error


def rows_by_model(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["Model"]: row for row in rows}


def save_figure(figure: plt.Figure, stem: Path, dpi: int) -> tuple[Path, Path]:
    png_path = stem.with_suffix(".png")
    pdf_path = stem.with_suffix(".pdf")
    figure.savefig(png_path, dpi=dpi, bbox_inches="tight", pad_inches=0.08)
    figure.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08)
    plt.close(figure)
    return png_path, pdf_path


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.14,
        1.08,
        label,
        transform=axis.transAxes,
        fontsize=11,
        fontweight="bold",
        va="top",
        ha="left",
    )


def plot_raw_skr(
    axis: plt.Axes,
    summaries: dict[str, dict[str, str]],
) -> None:
    methods = [method for method in METHOD_ORDER if method in summaries]
    y_positions = np.arange(len(methods), dtype=np.float64)
    for y, method in zip(y_positions, methods):
        row = summaries[method]
        mean = as_float(row, "raw_K_mean")
        low = as_float(row, "raw_K_ci95_low")
        high = as_float(row, "raw_K_ci95_high")
        axis.errorbar(
            mean,
            y,
            xerr=np.asarray([[mean - low], [high - mean]]),
            fmt="none",
            ecolor="#5A6067",
            elinewidth=1.2,
            capsize=3.0,
            zorder=1,
        )
        axis.scatter(
            mean,
            y,
            s=45 if method == "Learned joint PS+GS" else 34,
            color=METHOD_COLORS[method],
            edgecolor="white",
            linewidth=0.6,
            zorder=2,
        )
        axis.text(high + 0.00035, y, f"{mean:.5f}", va="center", fontsize=7.5)

    axis.set_yticks(y_positions, [METHOD_LABELS[method] for method in methods])
    axis.invert_yaxis()
    axis.set_xlabel("Raw secret-key rate (bits/symbol)")
    axis.set_title("Mean performance and 95% CI", loc="left")
    axis.set_xlim(0.008, 0.030)
    axis.grid(axis="x")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    panel_label(axis, "A")


def plot_paired_gain(
    axis: plt.Axes,
    uncertainty_rows: list[dict[str, str]],
    summaries: dict[str, dict[str, str]],
) -> None:
    by_run: dict[int, dict[str, dict[str, str]]] = {}
    for row in uncertainty_rows:
        by_run.setdefault(int(row["run"]), {})[row["Model"]] = row

    run_ids: list[int] = []
    gains: list[float] = []
    for run in sorted(by_run):
        run_rows = by_run[run]
        if "Learned PS fixed QAM" not in run_rows or "Learned joint PS+GS" not in run_rows:
            continue
        ps_value = as_float(run_rows["Learned PS fixed QAM"], "raw_K")
        joint_value = as_float(run_rows["Learned joint PS+GS"], "raw_K")
        run_ids.append(run + 1)
        gains.append(1e6 * (joint_value - ps_value))

    joint_summary = summaries["Learned joint PS+GS"]
    mean = 1e6 * as_float(joint_summary, "Delta_raw_K_vs_PS_mean")
    low = 1e6 * as_float(joint_summary, "Delta_raw_K_vs_PS_ci95_low")
    high = 1e6 * as_float(joint_summary, "Delta_raw_K_vs_PS_ci95_high")

    axis.axhline(0.0, color="#30343B", linewidth=0.8)
    axis.axhspan(low, high, color=METHOD_COLORS["Learned joint PS+GS"], alpha=0.14)
    axis.plot(
        run_ids,
        gains,
        color=METHOD_COLORS["Learned joint PS+GS"],
        linewidth=1.1,
        marker="o",
        markersize=5,
    )
    axis.axhline(mean, color=METHOD_COLORS["Learned joint PS+GS"], linestyle="--", linewidth=1.2)
    axis.text(
        0.98,
        0.08,
        f"paired mean {mean:.2f} [{low:.2f}, {high:.2f}]",
        transform=axis.transAxes,
        color=METHOD_COLORS["Learned joint PS+GS"],
        ha="right",
        va="bottom",
        fontsize=7.5,
    )
    axis.set_xticks(run_ids)
    axis.set_xlim(0.7, max(run_ids) + 0.8)
    axis.set_ylim(0.0, max(42.0, high * 1.12))
    axis.set_xlabel("Independent evaluation seed")
    axis.set_ylabel("Joint gain over PS (microbits/symbol)")
    axis.set_title("Paired gain is positive in all five evaluations", loc="left")
    axis.grid(axis="y")
    axis.spines[["top", "right"]].set_visible(False)
    panel_label(axis, "B")


def plot_gain_decomposition(
    axis: plt.Axes,
    summaries: dict[str, dict[str, str]],
    beta: float,
) -> None:
    ps = summaries["Learned PS fixed QAM"]
    joint = summaries["Learned joint PS+GS"]
    delta_beta_iab = 1e6 * beta * (
        as_float(joint, "I_AB_mean") - as_float(ps, "I_AB_mean")
    )
    holevo_reduction = -1e6 * (
        as_float(joint, "chi_BE_mean") - as_float(ps, "chi_BE_mean")
    )
    net_gain = 1e6 * (
        as_float(joint, "raw_K_mean") - as_float(ps, "raw_K_mean")
    )
    labels = (r"$\Delta(\beta I_{AB})$", r"$-\Delta\chi_{BE}$", r"$\Delta K$")
    values = np.asarray((delta_beta_iab, holevo_reduction, net_gain))
    colors = (METHOD_COLORS["Learned PS fixed QAM"], "#C28B2C", METHOD_COLORS["Learned joint PS+GS"])
    y_positions = np.arange(values.size)

    axis.axvline(0.0, color="#30343B", linewidth=0.8)
    axis.barh(y_positions, values, color=colors, height=0.56, alpha=0.92)
    for y, value, color in zip(y_positions, values, colors):
        if abs(value) < 1.0:
            axis.scatter(value, y, s=28, color=color, edgecolor="white", linewidth=0.5, zorder=3)
            label_position = 1.0
            horizontal_alignment = "left"
        else:
            label_position = value + (0.7 if value >= 0.0 else -0.7)
            horizontal_alignment = "left" if value >= 0.0 else "right"
        axis.text(
            label_position,
            y,
            f"{value:+.3f}",
            ha=horizontal_alignment,
            va="center",
            fontsize=7.5,
        )
    axis.set_yticks(y_positions, labels)
    axis.invert_yaxis()
    axis.set_xlim(-3.0, 40.0)
    axis.set_xlabel("Contribution (microbits/symbol)")
    axis.set_title(r"Gain is driven by lower $\chi_{BE}$", loc="left")
    axis.grid(axis="x")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    panel_label(axis, "C")


def plot_ncut_sensitivity(axis: plt.Axes, ncut_rows: list[dict[str, str]]) -> None:
    cutoffs = sorted({int(row["ncut"]) for row in ncut_rows})
    if len(cutoffs) < 2:
        raise ValueError("ncut_convergence.csv must contain at least two cutoffs.")
    lower_cutoff = cutoffs[0]
    lower_rows = {
        row["Model"]: row for row in ncut_rows if int(row["ncut"]) == lower_cutoff
    }
    methods = [method for method in METHOD_ORDER if method in lower_rows]
    y_positions = np.arange(len(methods), dtype=np.float64)
    values = [
        1e15 * as_float(lower_rows[method], "abs_delta_raw_K_vs_final")
        for method in methods
    ]
    for y, method, value in zip(y_positions, methods, values):
        axis.hlines(y, 0.0, value, color="#D0D4D7", linewidth=1.2)
        axis.scatter(
            value,
            y,
            s=38 if method == "Learned joint PS+GS" else 30,
            color=METHOD_COLORS[method],
            edgecolor="white",
            linewidth=0.5,
            zorder=2,
        )
        axis.text(value + 0.12, y, f"{value:.2f}", va="center", fontsize=7.5)
    axis.set_yticks(y_positions, [METHOD_LABELS[method] for method in methods])
    axis.invert_yaxis()
    axis.set_xlim(0.0, max(values) * 1.35)
    axis.set_xlabel(r"$|K_{150}-K_{120}|$ ($10^{-15}$ bits/symbol)")
    axis.set_title("Fock-cutoff convergence", loc="left")
    axis.grid(axis="x")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    panel_label(axis, "D")


def create_summary_figure(results_dir: Path, output_dir: Path, dpi: int, beta: float) -> tuple[Path, Path]:
    summary_rows = read_csv(results_dir / "uncertainty_summary.csv")
    uncertainty_rows = read_csv(results_dir / "uncertainty_runs.csv")
    ncut_rows = read_csv(results_dir / "ncut_convergence.csv")
    summaries = rows_by_model(summary_rows)

    required = {"Learned PS fixed QAM", "Learned joint PS+GS"}
    missing = sorted(required.difference(summaries))
    if missing:
        raise ValueError(f"Missing required methods in uncertainty summary: {missing}")

    figure, axes = plt.subplots(2, 2, figsize=(10.8, 7.7))
    figure.subplots_adjust(left=0.14, right=0.98, top=0.90, bottom=0.12, wspace=0.37, hspace=0.46)
    figure.suptitle(
        "Joint probabilistic and geometric shaping: evaluation summary",
        fontsize=14,
        fontweight="bold",
        y=0.97,
    )

    plot_raw_skr(axes[0, 0], summaries)
    plot_paired_gain(axes[0, 1], uncertainty_rows, summaries)
    plot_gain_decomposition(axes[1, 0], summaries, beta)
    plot_ncut_sensitivity(axes[1, 1], ncut_rows)

    figure.text(
        0.5,
        0.025,
        "Mean +/- 95% CI across five independent channel/AWGN evaluation seeds; "
        "paired intervals do not represent independent training-seed uncertainty.",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#4E545A",
    )
    return save_figure(figure, output_dir / "research_summary", dpi)


def load_constellation_state(
    coordinate_path: Path,
    probability_path: Path,
    sample_index: int,
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {
        method: {"coordinates": {}, "probabilities": {}, "transmittance": None}
        for method in CONSTELLATION_METHODS
    }

    if not coordinate_path.exists() or not probability_path.exists():
        raise FileNotFoundError(
            "learned_constellation.csv and learned_probabilities.csv are required "
            "for the constellation figure."
        )

    with coordinate_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            method = row["scheme"]
            if method not in selected or int(row["sample_index"]) != sample_index:
                continue
            symbol = int(row["symbol_index"])
            selected[method]["coordinates"][symbol] = (float(row["x"]), float(row["y"]))
            selected[method]["transmittance"] = float(row["T"])

    with probability_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            method = row["scheme"]
            if method not in selected or int(row["sample_index"]) != sample_index:
                continue
            selected[method]["probabilities"][int(row["symbol_index"])] = float(
                row["probability"]
            )

    for method, values in selected.items():
        coordinate_symbols = set(values["coordinates"])
        probability_symbols = set(values["probabilities"])
        if len(coordinate_symbols) != 256 or coordinate_symbols != probability_symbols:
            raise ValueError(
                f"Expected 256 matched symbols for {method!r} at sample {sample_index}; "
                f"found {len(coordinate_symbols)} coordinates and "
                f"{len(probability_symbols)} probabilities."
            )
    return selected


def create_constellation_figure(
    results_dir: Path,
    output_dir: Path,
    sample_index: int,
    dpi: int,
) -> tuple[Path, Path]:
    selected = load_constellation_state(
        results_dir / "learned_constellation.csv",
        results_dir / "learned_probabilities.csv",
        sample_index,
    )
    all_probabilities = np.asarray(
        [
            probability
            for values in selected.values()
            for probability in values["probabilities"].values()
        ],
        dtype=np.float64,
    )
    probability_norm = LogNorm(
        vmin=max(float(all_probabilities.min()), 1e-12),
        vmax=float(all_probabilities.max()),
    )

    all_coordinates = np.asarray(
        [
            coordinate
            for values in selected.values()
            for coordinate in values["coordinates"].values()
        ],
        dtype=np.float64,
    )
    coordinate_limit = 1.08 * float(np.max(np.abs(all_coordinates)))

    figure, axes = plt.subplots(1, 3, figsize=(10.8, 3.8), sharex=True, sharey=True)
    figure.subplots_adjust(left=0.07, right=0.91, top=0.82, bottom=0.20, wspace=0.13)
    figure.suptitle(
        "Learned 256-QAM shaping at a representative fading state",
        fontsize=13,
        fontweight="bold",
        y=0.96,
    )

    scatter = None
    for index, (axis, method) in enumerate(zip(axes, CONSTELLATION_METHODS)):
        values = selected[method]
        symbols = sorted(values["coordinates"])
        coordinates = np.asarray([values["coordinates"][symbol] for symbol in symbols])
        probabilities = np.asarray([values["probabilities"][symbol] for symbol in symbols])
        marker_sizes = 5.0 + 30.0 * np.sqrt(probabilities / probabilities.max())
        scatter = axis.scatter(
            coordinates[:, 0],
            coordinates[:, 1],
            c=probabilities,
            s=marker_sizes,
            cmap="cividis",
            norm=probability_norm,
            edgecolor="#22262B",
            linewidth=0.25,
            alpha=0.95,
        )
        axis.axhline(0.0, color="#B8BDC1", linewidth=0.6, zorder=0)
        axis.axvline(0.0, color="#B8BDC1", linewidth=0.6, zorder=0)
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlim(-coordinate_limit, coordinate_limit)
        axis.set_ylim(-coordinate_limit, coordinate_limit)
        axis.grid(alpha=0.5)
        axis.set_title(METHOD_LABELS[method])
        axis.set_xlabel("In-phase coordinate")
        axis.text(
            0.04,
            0.95,
            f"T = {values['transmittance']:.4f}",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=7.5,
            color="#4E545A",
        )
        panel_label(axis, chr(ord("A") + index))
    axes[0].set_ylabel("Quadrature coordinate")

    if scatter is None:
        raise RuntimeError("No constellation points were plotted.")
    colorbar_axis = figure.add_axes((0.93, 0.22, 0.015, 0.56))
    colorbar = figure.colorbar(scatter, cax=colorbar_axis)
    colorbar.set_label(r"Symbol probability $p_i$ (log scale)", fontsize=8)
    colorbar.ax.tick_params(labelsize=7)
    figure.text(
        0.49,
        0.045,
        "Marker area and color encode symbol probability; all panels use common coordinate and probability scales.",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#4E545A",
    )
    return save_figure(figure, output_dir / "research_constellations", dpi)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("experiments/joint_seed2026"),
        help="Directory containing the completed experiment CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Figure directory (default: RESULTS_DIR/research_figures).",
    )
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--beta", type=float, default=0.95)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_dir = args.results_dir.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else results_dir / "research_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_style()

    generated = [
        *create_summary_figure(results_dir, output_dir, args.dpi, args.beta),
        *create_constellation_figure(
            results_dir,
            output_dir,
            args.sample_index,
            args.dpi,
        ),
    ]
    print("Generated publication figures:")
    for path in generated:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
