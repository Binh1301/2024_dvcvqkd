"""Plotting modules for UAV-HAP CV-QKD performance analysis."""

from .skr_gaussian_uav_hap import (
    compute_skr,
    debug_reference_case,
    plot_1_skr_vs_distance,
    plot_2_skr_vs_va,
    plot_3_skr_vs_cn2,
    plot_4_loss_decomposition,
    plot_5_skr_vs_sigma_r,
    plot_6_skr_heatmap,
    plot_7_gm_vs_dm_protocols,
    plot_all_skr_figures,
    plot_all_skr_figures_combined,
)

__all__ = [
    "compute_skr",
    "debug_reference_case",
    "plot_1_skr_vs_distance",
    "plot_2_skr_vs_va",
    "plot_3_skr_vs_cn2",
    "plot_4_loss_decomposition",
    "plot_5_skr_vs_sigma_r",
    "plot_6_skr_heatmap",
    "plot_7_gm_vs_dm_protocols",
    "plot_all_skr_figures",
    "plot_all_skr_figures_combined",
]
