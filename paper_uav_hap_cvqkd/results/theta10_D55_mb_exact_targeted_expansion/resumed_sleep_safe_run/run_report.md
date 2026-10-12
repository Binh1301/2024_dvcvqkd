# Sleep-safe three-probe exact expansion

THREE_PROBE_CAMPAIGN_FINISHED_WITH_FINITE_CATALOG_SCOPE
Successful=3; timeout=0; attempts=3.
Wall=7732.75s/10800s; aggregate CPU=7515.03125s; wall compliance=True.
Sleep lease={"active_verified": true, "released_verified": true, "power_before": {"ac": 1, "battery_flag": 1, "battery_percent": 100, "system_status": 0, "life_seconds": 4294967295, "full_life_seconds": 4294967295}, "requested_flags": 2147483649, "previous_state": 2147483648, "owner_thread": 21160, "restored_state": 2147483648}; error=None.
Exact catalog/AO outcome={"MB_count": 142, "distances_evaluated": 26, "new_source_objective_rows": 78, "improved_distances": [22.0], "largest_numeric_gain": 2.8628002113340045e-07, "AO_rechecked": true, "AO_matches_catalog": 26, "AO_distances": 26, "newly_closed_selected_searches": [], "numerically_converged_distances": [], "global_optimum_claimed": false, "total_objective_error_bound": "NOT_ESTABLISHED"}.
Original scientific formulas/source method/precision/quadrature/MI/Holevo/AO unchanged; no interpolation.
Final AO uses original four starts and preceding-distance warm continuation (129 starts).
360s reserved for final cache-only recheck/cleanup; final source limit may be shorter than3600s.
Temporary request prevents idle sleep, not manual suspend/shutdown/critical power. No power plan modified.
Finite exact catalog ranking only. Missing moments/open boundaries preclude continuous/global convergence.
Historical/preflight protected hashes unchanged=725.


## Verified source moments and runtime

| Probe | nu_raw | V_A | C | w | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|
| 1 | 0.16562500000000002 | 5.5 | 3.211307653120286 | 1.0282071401398513e-06 | 3203.7649999999994 | 3093.28125 |
| 2 | 0.165 | 5.45 | 3.186004082405213 | 9.712251500409402e-07 | 2199.9370000000054 | 2143.671875 |
| 3 | 0.165 | 5.525 | 3.2239576594753885 | 1.0537499123188515e-06 | 2148.9060000000027 | 2095.65625 |

## Maximum of the expanded exact MB catalog at all26 distances

All values copied directly from old_vs_new_mb_skr.csv. This is not a continuous/global optimum.

| Link km | nu_raw | V_A | K bits/use | deltaK vs139 |
|---|---|---|---|---|
| 20.0 | 0.15 | 6.5 | 0.1380135312811619 | 0.0 |
| 21.0 | 0.16 | 6.0 | 0.1027071638150534 | 0.0 |
| 21.9393102292 | 0.165 | 5.5 | 0.07798099387393764 | 0.0 |
| 22.0 | 0.165 | 5.45 | 0.07661714229913241 | 2.8628002113340045e-07 |
| 23.0 | 0.165 | 5.3 | 0.05745739941473693 | 0.0 |
| 24.0 | 0.15 | 5.0 | 0.04337158782779649 | 0.0 |
| 25.0 | 0.15 | 4.5 | 0.033155735581557266 | 0.0 |
| 25.5 | 0.15 | 4.5 | 0.029094514576219477 | 0.0 |
| 26.0 | 0.15 | 4.5 | 0.02559880329969072 | 0.0 |
| 26.5 | 0.15 | 4.5 | 0.02258632178693923 | 0.0 |
| 27.0 | 0.15 | 4.5 | 0.019986441582292652 | 0.0 |
| 27.5 | 0.15 | 4.5 | 0.01773877780029154 | 0.0 |
| 28.0 | 0.15 | 4.5 | 0.015791856791609243 | 0.0 |
| 29.0 | 0.15 | 3.5548673904962893 | 0.012633752605448606 | 0.0 |
| 30.0 | 0.15 | 3.5548673904962893 | 0.010253503998581354 | 0.0 |
| 30.5 | 0.15 | 3.5548673904962893 | 0.009278128392001553 | 0.0 |
| 31.0 | 0.15 | 3.5548673904962893 | 0.008419975631179313 | 0.0 |
| 31.5 | 0.15 | 3.5548673904962893 | 0.007663135177788452 | 0.0 |
| 32.0 | 0.15 | 3.5548673904962893 | 0.006994021456280031 | 0.0 |
| 32.5 | 0.15 | 3.5548673904962893 | 0.006401020851147396 | 0.0 |
| 33.0 | 0.15 | 3.5548673904962893 | 0.005874192306253717 | 0.0 |
| 34.0 | 0.15 | 3.5548673904962893 | 0.004986168363777209 | 0.0 |
| 35.0 | 0.15 | 3.5548673904962893 | 0.004275173307058823 | 0.0 |
| 36.0 | 0.15 | 3.5548673904962893 | 0.0037005544396879267 | 0.0 |
| 38.0 | 0.15 | 3.5548673904962893 | 0.0028463445249044643 | 0.0 |
| 40.0 | 0.15 | 3.5548673904962893 | 0.00225888275226813 | 0.0 |

## Validation and remaining scope

Independent verifier: {"status": "CURRENTLY_VERIFIED_PASS", "protected_files_unchanged": 725, "MB_count": 142, "successful_sources": 3, "timeout_sources": 0, "SKR_distances": 26, "AO_distances": 26, "AO_starts": 129, "AO_matches_catalog": 26, "sleep_active_verified": true, "sleep_restoration_verified": true, "wall_budget_respected": true, "all_job_limits_respected": true, "workers_remaining": 0, "regression_tests_pass": true, "git_diff_check_pass": true, "scientific_implementation_unchanged": true, "no_interpolation": true, "continuous_global_optimum_claimed": false, "frozen_spec_sha256": "df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15"}.
Original129 starts and52 final coordinate checks yield 618 total coordinate calls: {'BOUNDARY_NOT_CLOSED': 310, 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING': 308}.
Selected statuses: {'STAGNATED_IN_EXACT_CATALOG': 4, 'UNRESOLVED_BOUNDARY': 22}; unique missing exact pairs=52. Newly fully closed coordinate searches=0.
The three requested exact point values are now available in searches, but refinement still requests unavailable neighbors.
At22km (.165,5.45) improves finite numerical K by2.8628002113340045e-07; no total objective error bound establishes meaningful physical gain.
Aggregate Windows Job source/SKR/AO CPU plus coordinator CPU; excludes preparation and independent regression checks.
Old frozen-spec hash discrepancy remains recorded; no model change or publication/training/test/threshold authorization.
Full inputs, receipts, cache-only search histories and remaining_missing_exact_pairs.csv preserve reproducibility.
