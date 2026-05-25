from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class SweepSeries:
    label: str
    v_values: np.ndarray
    z_star: np.ndarray
    chi_be: np.ndarray
    i_ab: np.ndarray
    skr: np.ndarray
    status: Optional[np.ndarray] = None


def plot_v_sweep(series_list: list[SweepSeries], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("matplotlib is required for plotting.") from exc

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.4), constrained_layout=True)
    titles = ["Z* vs v", "chi_BE vs v", "I_AB vs v", "SKR vs v"]
    ylabels = ["Z*", "chi_BE (bits)", "I_AB (bits)", "SKR (bits/use)"]

    for series in series_list:
        status = series.status
        if status is None:
            axes[0, 0].plot(series.v_values, series.z_star, lw=2.0, label=series.label)
            axes[0, 1].plot(series.v_values, series.chi_be, lw=2.0, label=series.label)
            axes[1, 0].plot(series.v_values, series.i_ab, lw=2.0, label=series.label)
            axes[1, 1].plot(series.v_values, series.skr, lw=2.0, label=series.label)
        else:
            physical_mask = status == "physical"
            clipped_mask = status == "clipped"
            invalid_mask = status == "invalid"
            axes[0, 0].plot(series.v_values, np.where(physical_mask, series.z_star, np.nan), lw=2.0, label=series.label)
            axes[0, 1].plot(series.v_values, np.where(physical_mask, series.chi_be, np.nan), lw=2.0, label=series.label)
            axes[1, 0].plot(series.v_values, np.where(physical_mask, series.i_ab, np.nan), lw=2.0, label=series.label)
            axes[1, 1].plot(series.v_values, np.where(physical_mask, series.skr, np.nan), lw=2.0, label=series.label)
            if np.any(clipped_mask):
                axes[1, 1].scatter(series.v_values[clipped_mask], series.skr[clipped_mask], marker="x", s=45, color="orange")
            if np.any(invalid_mask):
                axes[1, 1].scatter(series.v_values[invalid_mask], series.skr[invalid_mask], marker="x", s=45, color="red")

    for ax, title, ylabel in zip(axes.flatten(), titles, ylabels, strict=True):
        ax.set_title(title)
        ax.set_xlabel("v")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(frameon=False)

    from matplotlib.lines import Line2D

    legend_extra = [
        Line2D([0], [0], marker="x", color="orange", linestyle="None", label="clipped (non-physical)"),
        Line2D([0], [0], marker="x", color="red", linestyle="None", label="invalid"),
    ]
    handles, labels = axes[1, 1].get_legend_handles_labels()
    axes[1, 1].legend(handles + legend_extra, labels + [h.get_label() for h in legend_extra], frameon=False)

    out_path = out_dir / "qam_v_sweep_compare.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_nu_sweep(series_list: list[SweepSeries], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("matplotlib is required for plotting.") from exc

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.4), constrained_layout=True)
    titles = ["Z* vs nu_tilde", "chi_BE vs nu_tilde", "I_AB vs nu_tilde", "SKR vs nu_tilde"]
    ylabels = ["Z*", "chi_BE (bits)", "I_AB (bits)", "SKR (bits/use)"]

    for series in series_list:
        status = series.status
        if status is None:
            axes[0, 0].plot(series.v_values, series.z_star, lw=2.0, label=series.label)
            axes[0, 1].plot(series.v_values, series.chi_be, lw=2.0, label=series.label)
            axes[1, 0].plot(series.v_values, series.i_ab, lw=2.0, label=series.label)
            axes[1, 1].plot(series.v_values, series.skr, lw=2.0, label=series.label)
        else:
            physical_mask = status == "physical"
            clipped_mask = status == "clipped"
            invalid_mask = status == "invalid"
            axes[0, 0].plot(series.v_values, np.where(physical_mask, series.z_star, np.nan), lw=2.0, label=series.label)
            axes[0, 1].plot(series.v_values, np.where(physical_mask, series.chi_be, np.nan), lw=2.0, label=series.label)
            axes[1, 0].plot(series.v_values, np.where(physical_mask, series.i_ab, np.nan), lw=2.0, label=series.label)
            axes[1, 1].plot(series.v_values, np.where(physical_mask, series.skr, np.nan), lw=2.0, label=series.label)
            if np.any(clipped_mask):
                axes[1, 1].scatter(series.v_values[clipped_mask], series.skr[clipped_mask], marker="x", s=45, color="orange")
            if np.any(invalid_mask):
                axes[1, 1].scatter(series.v_values[invalid_mask], series.skr[invalid_mask], marker="x", s=45, color="red")

    for ax, title, ylabel in zip(axes.flatten(), titles, ylabels, strict=True):
        ax.set_title(title)
        ax.set_xlabel("nu_tilde")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(frameon=False)

    from matplotlib.lines import Line2D

    legend_extra = [
        Line2D([0], [0], marker="x", color="orange", linestyle="None", label="clipped (non-physical)"),
        Line2D([0], [0], marker="x", color="red", linestyle="None", label="invalid"),
    ]
    handles, labels = axes[1, 1].get_legend_handles_labels()
    axes[1, 1].legend(handles + legend_extra, labels + [h.get_label() for h in legend_extra], frameon=False)

    out_path = out_dir / "qam_nu_sweep_compare.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path
