# Batch2 exact expansion

{
  "status": "BATCH2_FINISHED_FINITE_CATALOG_SCOPE",
  "successful_probes": 3,
  "timeout_probes": 0,
  "budget_session_wall_seconds": 6935.905999999988,
  "total_CPU_seconds": 6744.1875,
  "postprocess": {
    "MB_count": 145,
    "new_source_objectives": 78,
    "distances_evaluated": 26,
    "improved_distances": [
      22.0
    ],
    "largest_numeric_gain": 2.626161285101958e-07,
    "reference22_K": 0.07661714229913241,
    "AO_rechecked": true,
    "AO_matches_catalog": 26,
    "AO_distances": 26,
    "coordinate_calls": 618,
    "coordinate_status_counts": {
      "BOUNDARY_NOT_CLOSED": 312,
      "BRACKETED_EXACT_CATALOG_SOURCE_MISSING": 306
    },
    "selected_status_counts": {
      "STAGNATED_IN_EXACT_CATALOG": 4,
      "UNRESOLVED_BOUNDARY": 22
    },
    "newly_closed_selected_searches": [],
    "unique_missing_pairs": 54,
    "continuous_global_optimum_claimed": false,
    "total_objective_error_bound": "NOT_ESTABLISHED"
  },
  "error": null
}
Original science/settings/precision/quadrature/MI/Holevo/ALT_OPT unchanged. No interpolation. Finite catalog ranking only.


## New exact source moments and runtime

| Probe | nu_raw | V_A | C | w | Status | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|---|
| 1 | 0.165 | 5.475 | 3.1986564642787387 | 9.973886145561931e-07 | COMPLETED_EXACT | 2159.1719999999914 | 2101.03125 |
| 2 | 0.165 | 5.425000000000001 | 3.1733504920888835 | 9.46327534412786e-07 | COMPLETED_EXACT | 2444.4060000000027 | 2368.921875 |
| 3 | 0.15 | 6.25 | 3.590350464949084 | 2.285969661118393e-06 | COMPLETED_EXACT | 2163.4679999999935 | 2104.0625 |

## Finite catalog comparison: historical136, previous142, current

| Link km | Historical136 K | Previous142 K | New nu | New V_A | Current K | Delta vs142 |
|---|---|---|---|---|---|---|
| 20.0 | 0.1380135312811619 | 0.1380135312811619 | 0.15 | 6.5 | 0.1380135312811619 | 0.0 |
| 21.0 | 0.1027071638150534 | 0.1027071638150534 | 0.16 | 6.0 | 0.1027071638150534 | 0.0 |
| 21.9393102292 | 0.07798099387393764 | 0.07798099387393764 | 0.165 | 5.5 | 0.07798099387393764 | 0.0 |
| 22.0 | 0.07661685601911128 | 0.07661714229913241 | 0.165 | 5.475 | 0.07661740491526092 | 2.626161285101958e-07 |
| 23.0 | 0.05745739941473693 | 0.05745739941473693 | 0.165 | 5.3 | 0.05745739941473693 | 0.0 |
| 24.0 | 0.04337158782779649 | 0.04337158782779649 | 0.15 | 5.0 | 0.04337158782779649 | 0.0 |
| 25.0 | 0.033155735581557266 | 0.033155735581557266 | 0.15 | 4.5 | 0.033155735581557266 | 0.0 |
| 25.5 | 0.029094514576219477 | 0.029094514576219477 | 0.15 | 4.5 | 0.029094514576219477 | 0.0 |
| 26.0 | 0.02559880329969072 | 0.02559880329969072 | 0.15 | 4.5 | 0.02559880329969072 | 0.0 |
| 26.5 | 0.02258632178693923 | 0.02258632178693923 | 0.15 | 4.5 | 0.02258632178693923 | 0.0 |
| 27.0 | 0.019986441582292652 | 0.019986441582292652 | 0.15 | 4.5 | 0.019986441582292652 | 0.0 |
| 27.5 | 0.01773877780029154 | 0.01773877780029154 | 0.15 | 4.5 | 0.01773877780029154 | 0.0 |
| 28.0 | 0.015791856791609243 | 0.015791856791609243 | 0.15 | 4.5 | 0.015791856791609243 | 0.0 |
| 29.0 | 0.012633752605448606 | 0.012633752605448606 | 0.15 | 3.5548673904962893 | 0.012633752605448606 | 0.0 |
| 30.0 | 0.010253503998581354 | 0.010253503998581354 | 0.15 | 3.5548673904962893 | 0.010253503998581354 | 0.0 |
| 30.5 | 0.009278128392001553 | 0.009278128392001553 | 0.15 | 3.5548673904962893 | 0.009278128392001553 | 0.0 |
| 31.0 | 0.008419975631179313 | 0.008419975631179313 | 0.15 | 3.5548673904962893 | 0.008419975631179313 | 0.0 |
| 31.5 | 0.007663135177788452 | 0.007663135177788452 | 0.15 | 3.5548673904962893 | 0.007663135177788452 | 0.0 |
| 32.0 | 0.006994021456280031 | 0.006994021456280031 | 0.15 | 3.5548673904962893 | 0.006994021456280031 | 0.0 |
| 32.5 | 0.006401020851147396 | 0.006401020851147396 | 0.15 | 3.5548673904962893 | 0.006401020851147396 | 0.0 |
| 33.0 | 0.005874192306253717 | 0.005874192306253717 | 0.15 | 3.5548673904962893 | 0.005874192306253717 | 0.0 |
| 34.0 | 0.004986168363777209 | 0.004986168363777209 | 0.15 | 3.5548673904962893 | 0.004986168363777209 | 0.0 |
| 35.0 | 0.004275173307058823 | 0.004275173307058823 | 0.15 | 3.5548673904962893 | 0.004275173307058823 | 0.0 |
| 36.0 | 0.0037005544396879267 | 0.0037005544396879267 | 0.15 | 3.5548673904962893 | 0.0037005544396879267 | 0.0 |
| 38.0 | 0.0028463445249044643 | 0.0028463445249044643 | 0.15 | 3.5548673904962893 | 0.0028463445249044643 | 0.0 |
| 40.0 | 0.00225888275226813 | 0.00225888275226813 | 0.15 | 3.5548673904962893 | 0.00225888275226813 | 0.0 |

## Validation and limitations

{"status": "CURRENTLY_VERIFIED_PASS", "protected_files_unchanged": 796, "MB_count": 145, "successful_probes": 3, "timeout_probes": 0, "new_exact_objectives": 78, "distances": 26, "original_AO_starts": 129, "AO_matches_catalog": 26, "newly_closed_selected_searches": 0, "workers_remaining": 0, "wall_budget_respected": true, "sleep_request_restored": true, "regression_tests_pass": true, "regression_test_count": 32, "git_diff_check_pass": true, "no_interpolation": true, "science_unchanged": true, "reference_MB_count": 142, "baseline22_K": 0.07661714229913241, "CPU_scope": "Measured Job+controller; excludes preparation and independent tests"}
Source (C,w), source precision1050/1250/1450, quadrature, MI, direct-Zminus Holevo and original ALT_OPT unchanged.
All comparisons use142 as current baseline; historical136 is reported separately. No dense restart, interpolation or predicted missing K.
Catalog matching does not establish numerical convergence or continuous-domain global optimality. See actual coordinate logs and remaining_missing_exact_pairs.csv.
Tiny numerical gain has no demonstrated total objective error bound; physical significance is not certified.
Temporary sleep request was verified during run and restored at end. It does not prevent manual shutdown/suspend/critical power.
Frozen-spec discrepancy/lifecycle remain unchanged; no publication/training/test/baseline/threshold approval.
Another batch is justifiable only as targeted numerical coverage, after assessing recorded unresolved directions and runtime; not automatically authorized.

Actual replay has618 unresolved calls:312 BOUNDARY_NOT_CLOSED and306 BRACKETED_EXACT_CATALOG_SOURCE_MISSING,54 unique missing pairs; selected4 stagnated/22 unresolved. Prior142 replay had310/308 and52 pairs. New catalog changes visited slices and requests finer points, so these are separate actually executed scopes, not evidence of convergence or a simple failure-count regression.
Recorded unresolved ridge requests(.165,5.4625),(.165,5.4875) support targeted coverage in a future authorized batch, with exact binary64 identity checks. Gain/closure not guaranteed; no further AP started under completed max3 approval.
At20km source3 becomes runner-up K=.13782413021318984, narrowing gap from.0004177534149630846 to.00018940106797205036 without changing the maximum. At21.939km the maximum is unchanged and top-two gap narrows from4.5690643701856715e-07 to3.620594889452988e-07. See full exact top_two_candidates.csv for all26.
