"""Visualize the project's fixed Uniform, MB, and Binomial 256-QAM baselines."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

import uav_hap_joint_ps_gs as core


SCHEMES = (
    ("Uniform QAM", "uniform"),
    ("Maxwell-Boltzmann QAM", "mb"),
    ("Binomial QAM", "binomial"),
)


def fixed_outputs(va: float = 2.0) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    device = torch.device("cpu")
    base_qam = core.build_project_qam(device)
    transmittance = torch.tensor([0.1], dtype=core.REAL_DTYPE, device=device)
    outputs: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for display_name, kind in SCHEMES:
        output = core.model_output_for_baseline(kind, transmittance, base_qam, va)
        points = output.constellation[0].detach().cpu().numpy()
        probabilities = output.probabilities[0].detach().cpu().numpy()
        outputs[display_name] = (points, probabilities)
    return outputs


def plot_constellations(
    outputs: dict[str, tuple[np.ndarray, np.ndarray]],
    output_dir: Path,
) -> tuple[Path, Path]:
    figure, axes = plt.subplots(1, 3, figsize=(19.2, 6.5))
    for axis, (name, _) in zip(axes, SCHEMES, strict=True):
        points, probabilities = outputs[name]
        log_probabilities = np.log10(np.clip(probabilities, 1e-15, None))
        probability_ratio = probabilities / probabilities.max()
        marker_sizes = 18.0 + 115.0 * np.power(probability_ratio, 0.62)
        color_min = float(log_probabilities.min())
        color_max = float(log_probabilities.max())
        if math.isclose(color_min, color_max):
            color_min -= 0.05
            color_max += 0.05
        scatter = axis.scatter(
            points.real,
            points.imag,
            c=log_probabilities,
            s=marker_sizes,
            cmap="viridis",
            vmin=color_min,
            vmax=color_max,
            edgecolors="none",
        )
        limit = 1.10 * float(np.max(np.abs(np.concatenate((points.real, points.imag)))))
        axis.set_xlim(-limit, limit)
        axis.set_ylim(-limit, limit)
        axis.set_aspect("equal", adjustable="box")
        axis.set_title(name)
        axis.set_xlabel(r"$\mathrm{Re}(\alpha)$")
        axis.set_ylabel(r"$\mathrm{Im}(\alpha)$")
        axis.grid(alpha=0.28)
        colorbar = figure.colorbar(scatter, ax=axis, fraction=0.048, pad=0.035)
        colorbar.set_label(r"$\log_{10}$ probability")
    figure.suptitle("Fixed 256-QAM baseline constellations", fontsize=18)
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    png_path = output_dir / "fixed_qam_baseline_constellations.png"
    pdf_path = output_dir / "fixed_qam_baseline_constellations.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png_path, pdf_path


def plot_probability_heatmaps(
    outputs: dict[str, tuple[np.ndarray, np.ndarray]],
    output_dir: Path,
) -> tuple[Path, Path]:
    figure, axes = plt.subplots(1, 3, figsize=(18.7, 5.9))
    for axis, (name, _) in zip(axes, SCHEMES, strict=True):
        _, probabilities = outputs[name]
        heatmap = probabilities.reshape(core.GRID_SIDE, core.GRID_SIDE)
        image = axis.imshow(
            heatmap,
            origin="lower",
            interpolation="nearest",
            cmap="magma",
            aspect="equal",
        )
        axis.set_title(name)
        axis.set_xlabel("k index")
        axis.set_ylabel("l index")
        axis.set_xticks((0, 5, 10, 15))
        axis.set_yticks((0, 5, 10, 15))
        colorbar = figure.colorbar(image, ax=axis, fraction=0.048, pad=0.035)
        colorbar.set_label("Symbol probability")
    figure.suptitle("Fixed 256-QAM symbol probabilities", fontsize=18)
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))
    png_path = output_dir / "fixed_qam_baseline_probability_heatmaps.png"
    pdf_path = output_dir / "fixed_qam_baseline_probability_heatmaps.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png_path, pdf_path


def main() -> int:
    output_dir = Path("experiments/joint_seed2026/research_figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = fixed_outputs()
    paths = (
        *plot_constellations(outputs, output_dir),
        *plot_probability_heatmaps(outputs, output_dir),
    )
    for path in paths:
        print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
