# Phase D figures — DIAGNOSTIC_ONLY

| Figure | PNG600dpi | VectorPDF |
|---|---|---|
| figD1_conditional_unconditional_covariance | [PNG](figD1_conditional_unconditional_covariance.png) | [PDF](figD1_conditional_unconditional_covariance.pdf) |
| figD2_binary_latent_correlation | [PNG](figD2_binary_latent_correlation.png) | [PDF](figD2_binary_latent_correlation.pdf) |
| figD3_indexing_cloud_maps | [PNG](figD3_indexing_cloud_maps.png) | [PDF](figD3_indexing_cloud_maps.pdf) |
| figD4_paired_objective_improvement | [PNG](figD4_paired_objective_improvement.png) | [PDF](figD4_paired_objective_improvement.pdf) |
| figD5_rate_distance_tradeoff | [PNG](figD5_rate_distance_tradeoff.png) | [PDF](figD5_rate_distance_tradeoff.pdf) |
| figD6_indexing_robustness | [PNG](figD6_indexing_robustness.png) | [PDF](figD6_indexing_robustness.pdf) |

**Figure 1.** Conditional and unconditional covariance diagnostics from 100 saved missions. Dashed diagonals are 9 and 28/3; off-diagonal targets are identical. Points are raw entry/lag summaries, with no smoothing.

**Figure 2.** Binary versus unconditional latent correlations for six fixed cell pairs. Open markers and mission95%CI are empirical known-marginal estimates; crosses show the independently integrated mixture prediction. The dotted equality line is a reference, not a fitted model.

**Figure 3.** Cloud masks for five index assignments using the exact same latent label field (mission 0, slot 1, p=0.5). Row/column are transpose-related; other mappings change physical correlation patterns.

**Figure 4.** DP objective improvement over Greedy and offline Stationary, with 10000-replicate paired mission bootstrap 95% CI. All results use 100 paired missions and lambda_ref; intervals are pointwise.

**Figure 5.** Paired DP-minus-Greedy rate and distance differences with bootstrap 95% CI. At p=0.4 the rate interval crosses zero; at p=0.8 improved rate requires greater travel. No curve is fitted or interpolated.

**Figure 6.** Indexing robustness: paired objective gains with Student-t 95% CI (horizontal offsets are visual only), and unavailability at p=0.8. Five fixed assignments are tested; they are not an exhaustive permutation study.

Phase C figures are reused by reference, unchanged: [Phase C figure index](../phaseC_new_cloud_dp_greedy_stationary_20261025/figure_index.md).
