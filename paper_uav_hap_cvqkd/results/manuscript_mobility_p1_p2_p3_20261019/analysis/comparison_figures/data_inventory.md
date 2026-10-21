# Data inventory

Project-relative paths. Complete observed schemas; no inferred missing columns.

## results/manuscript_mobility_p1_p2_p3_20261019/mobility/mission_metrics.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 3000

`realization_id, lambda_index, lambda_bits_per_use, lambda_multiplier, strategy, average_skr_bits_per_use, total_distance_m, objective_bits_per_use, clear_slots, blocked_slots, positive_slots, availability, repositionings, initial_position_index, final_position_index, max_transition_m, improvement_vs_stationary_absolute, improvement_vs_stationary_percent, objective_improvement_vs_stationary_absolute, objective_improvement_vs_stationary_percent`

## results/manuscript_mobility_p1_p2_p3_20261019/mobility/time_series.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 90000

`realization_id, lambda_index, lambda_bits_per_use, lambda_multiplier, strategy, slot, position_index, x_m, y_m, blocked, usable_skr, leg_distance_m, cumulative_normalized_skr, nu_raw, VA, ensemble_hash, clear_raw_skr`

## results/manuscript_mobility_p1_p2_p3_20261019/mobility/p2_positions.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 100

`realization_id, lambda_index, lambda_bits_per_use, lambda_multiplier, strategy, average_skr_bits_per_use, total_distance_m, objective_bits_per_use, clear_slots, blocked_slots, positive_slots, availability, repositionings, initial_position_index, final_position_index, max_transition_m, improvement_vs_stationary_absolute, improvement_vs_stationary_percent, objective_improvement_vs_stationary_absolute, objective_improvement_vs_stationary_percent, j, x_m, y_m, family, nu_raw, VA, ensemble_hash, clear_raw_skr, clear_usable_skr`

## results/manuscript_mobility_p1_p2_p3_20261019/positions.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 100

`position_index, j, x_m, y_m, z_m, distance_km, zenith_deg, zenith_hex, horizontal_squared_hex, geometry_id`

## results/manuscript_mobility_p1_p2_p3_20261019/p1/winners.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 100

`position_index, j, x_m, y_m, z_m, distance_km, zenith_deg, zenith_hex, horizontal_squared_hex, geometry_id, source_group, family, nu_raw, VA, C, w, I_AB_2D, beta_I_AB, chi_BE, K_raw, eta_f, xi_f, N, V, W, Z, nu_1, nu_2, nu_3, MI_GH16, MI_GH32, MI_GH64, GH_max_difference, uncertainty_min_eigenvalue, matrix_spectrum_max_difference, ensemble_hash, source_sha256, K_star`

## results/manuscript_mobility_p1_p2_p3_20261019/p1/family_winners.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 200

`position_index, j, x_m, y_m, z_m, distance_km, zenith_deg, zenith_hex, horizontal_squared_hex, geometry_id, source_group, family, nu_raw, VA, C, w, I_AB_2D, beta_I_AB, chi_BE, K_raw, eta_f, xi_f, N, V, W, Z, nu_1, nu_2, nu_3, MI_GH16, MI_GH32, MI_GH64, GH_max_difference, uncertainty_min_eigenvalue, matrix_spectrum_max_difference, ensemble_hash, source_sha256, K_star`

## results/manuscript_mobility_p1_p2_p3_20261019/p1/candidate_evaluations.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 23300

`position_index, j, x_m, y_m, z_m, distance_km, zenith_deg, zenith_hex, horizontal_squared_hex, geometry_id, family, nu_raw, VA, C, w, I_AB_2D, beta_I_AB, chi_BE, K_raw, eta_f, xi_f, N, V, W, Z, nu_1, nu_2, nu_3, MI_GH16, MI_GH32, MI_GH64, GH_max_difference, uncertainty_min_eigenvalue, matrix_spectrum_max_difference, ensemble_hash, source_sha256, evaluation_origin`

## results/manuscript_mobility_p1_p2_p3_20261019/source_roster.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 233

`family, nu_raw, VA, C, w, ensemble_hash, source_path, source_sha256, cache_key, canonical_cache_key, source_moment_route, support_size, nu_raw_hex, VA_hex`

## results/manuscript_mobility_p1_p2_p3_20261019/analysis/tables/method_comparison.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 30

`lambda_index, lambda_bits_per_use, lambda_multiplier, method, K_n, K_mean, K_sd, K_min, K_p05, K_median, K_p95, K_max, K_ci95_t_low, K_ci95_t_high, D_n, D_mean, D_sd, D_min, D_p05, D_median, D_p95, D_max, D_ci95_t_low, D_ci95_t_high, U_n, U_mean, U_sd, U_min, U_p05, U_median, U_p95, U_max, U_ci95_t_low, U_ci95_t_high, availability_n, availability_mean, availability_sd, availability_min, availability_p05, availability_median, availability_p95, availability_max, availability_ci95_t_low, availability_ci95_t_high, changes_n, changes_mean, changes_sd, changes_min, changes_p05, changes_median, changes_p95, changes_max, changes_ci95_t_low, changes_ci95_t_high, blocked_n, blocked_mean, blocked_sd, blocked_min, blocked_p05, blocked_median, blocked_p95, blocked_max, blocked_ci95_t_low, blocked_ci95_t_high`

## results/manuscript_mobility_p1_p2_p3_20261019/analysis/tables/paired_comparisons.csv

K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless

Rows: 40

`lambda_index, lambda_bits_per_use, baseline, metric, n, mean, sd, min, p05, median, p95, max, ci95_t_low, ci95_t_high, ci95_bootstrap_low, ci95_bootstrap_high, strict_improvement_missions, equal_missions, inferior_missions, strict_fraction, equal_fraction, literal_positive_missions, ratio_of_means_percent, relative_valid_missions, mean_per_mission_percent, median_per_mission_percent`

## results/manuscript_mobility_p1_p2_p3_20261019/mobility/paths.npz

paths: zero-based position indices; lambda_values: bits/use; blocked: bool True=blocked; usable_skr: bits/use

`{"paths": {"shape": [100, 10, 3, 30], "dtype": "int16"}, "lambda_values": {"shape": [10], "dtype": "float64"}}`

## results/manuscript_mobility_p1_p2_p3_20261019/clouds/states.npz

paths: zero-based position indices; lambda_values: bits/use; blocked: bool True=blocked; usable_skr: bits/use

`{"blocked": {"shape": [100, 100, 30], "dtype": "bool"}, "usable_skr": {"shape": [100, 100, 30], "dtype": "float64"}}`

