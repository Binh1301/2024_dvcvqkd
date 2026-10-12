# Batch3 exact MB refinement

Status: BATCH3_FINISHED_WITH_POWER_ABORT_AND_FINITE_CATALOG_SCOPE

Original scientific implementation,1050/1250/1450 policy,GH8/direct-Zminus and ALT_OPT unchanged. No interpolation.
Numerical ranking: ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no total objective error bound or continuous/global claim.

## Probe outcomes

| Probe | nu_raw | VA | C | w | Status | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|---|
| 1 | 0.165 | 5.4625 | NOT_AVAILABLE | NOT_AVAILABLE | PROCESS_FAILURE | 1952.7190000000119 | 1926.453125 |
| 2 | 0.165 | 5.4875 | 3.204982206511816 | 1.0109632916527298e-06 | COMPLETED_EXACT | 2177.702999999994 | 2117.703125 |

Successful=1; timeout=0.
Wall=10391.192873s/10800s; measured Job+controller CPU=4149.515625s.
Wall compliance=True; error=None.
Total includes execution and between-probe processing; preparation/tests before session are excluded.
Sleep prevention active across campaign, restored in finally; no permanent power-plan change.
See individual supervision receipts for real deadlines, power watches and worker cleanup.

## Expanded finite catalog and original ALT_OPT

```json
{
  "MB_count": 146,
  "new_source_objectives": 26,
  "distances_evaluated": 26,
  "improved_distances": [],
  "largest_numeric_gain": 0.0,
  "reference22_K": 0.07661740491526092,
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
  "unique_missing_pairs": 55,
  "continuous_global_optimum_claimed": false,
  "total_objective_error_bound": "NOT_ESTABLISHED",
  "numerical_ranking_status": "ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED",
  "total_outer_iterations": 283,
  "total_multistart_runs": 129,
  "newly_closed_coordinate_invocations": 0,
  "baseline_closed_coordinate_invocations": 0
}
```

| L km | Old nu | Old VA | New nu | New VA | Old K | New K | Delta K |
|---|---|---|---|---|---|---|---|
| 20.0 | 0.15 | 6.5 | 0.15 | 6.5 | 0.1380135312811619 | 0.1380135312811619 | 0.0 |
| 21.0 | 0.16 | 6.0 | 0.16 | 6.0 | 0.1027071638150534 | 0.1027071638150534 | 0.0 |
| 21.9393102292 | 0.165 | 5.5 | 0.165 | 5.5 | 0.07798099387393764 | 0.07798099387393764 | 0.0 |
| 22.0 | 0.165 | 5.475 | 0.165 | 5.475 | 0.07661740491526092 | 0.07661740491526092 | 0.0 |
| 23.0 | 0.165 | 5.3 | 0.165 | 5.3 | 0.05745739941473693 | 0.05745739941473693 | 0.0 |
| 24.0 | 0.15 | 5.0 | 0.15 | 5.0 | 0.04337158782779649 | 0.04337158782779649 | 0.0 |
| 25.0 | 0.15 | 4.5 | 0.15 | 4.5 | 0.033155735581557266 | 0.033155735581557266 | 0.0 |
| 25.5 | 0.15 | 4.5 | 0.15 | 4.5 | 0.029094514576219477 | 0.029094514576219477 | 0.0 |
| 26.0 | 0.15 | 4.5 | 0.15 | 4.5 | 0.02559880329969072 | 0.02559880329969072 | 0.0 |
| 26.5 | 0.15 | 4.5 | 0.15 | 4.5 | 0.02258632178693923 | 0.02258632178693923 | 0.0 |
| 27.0 | 0.15 | 4.5 | 0.15 | 4.5 | 0.019986441582292652 | 0.019986441582292652 | 0.0 |
| 27.5 | 0.15 | 4.5 | 0.15 | 4.5 | 0.01773877780029154 | 0.01773877780029154 | 0.0 |
| 28.0 | 0.15 | 4.5 | 0.15 | 4.5 | 0.015791856791609243 | 0.015791856791609243 | 0.0 |
| 29.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.012633752605448606 | 0.012633752605448606 | 0.0 |
| 30.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.010253503998581354 | 0.010253503998581354 | 0.0 |
| 30.5 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.009278128392001553 | 0.009278128392001553 | 0.0 |
| 31.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.008419975631179313 | 0.008419975631179313 | 0.0 |
| 31.5 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.007663135177788452 | 0.007663135177788452 | 0.0 |
| 32.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.006994021456280031 | 0.006994021456280031 | 0.0 |
| 32.5 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.006401020851147396 | 0.006401020851147396 | 0.0 |
| 33.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.005874192306253717 | 0.005874192306253717 | 0.0 |
| 34.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.004986168363777209 | 0.004986168363777209 | 0.0 |
| 35.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.004275173307058823 | 0.004275173307058823 | 0.0 |
| 36.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.0037005544396879267 | 0.0037005544396879267 | 0.0 |
| 38.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.0028463445249044643 | 0.0028463445249044643 | 0.0 |
| 40.0 | 0.15 | 3.5548673904962893 | 0.15 | 3.5548673904962893 | 0.00225888275226813 | 0.00225888275226813 | 0.0 |

Runner-up/top-two gaps: top_two_candidates.csv and old_vs_new_optimum.csv.
Full histories: cache_only_runs.json/cache_only_searches.json. Coordinate final-pair changes compare same slices only.
Local exact VA/nu slices at22km and all new successful source objectives at26 distances are saved; missing K is never inferred.
Further expansion is conditional coverage/sensitivity work, not a promised gain or convergence certificate.

Protected files unchanged=929.
Earlier selection snapshots and all previous numerical artifacts preserved.
Frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain; no training/test/baseline/threshold approval.

## Final execution status and independent verification

Probe1: POWER ABORT on AC loss, not timeout or numerical failure; no new moments.
Probe2: COMPLETED_EXACT, C=3.204982206511816, w=1.0109632916527298e-06.
Probe3: NOT_RUN_INSUFFICIENT_UNRESERVED_BUDGET. After successful source2 and its26-distance evaluation, remaining time was within the480s reserve for final AO/cleanup. No3h budget was reset and no source was retried.

Completed_independent_verification.json verifies146 compatible MB sources and3796 objective rows. Six original-evaluator repeats from the new source are bit-exact;36 final scoped tests and git diff --check PASS. Original science/source/precision/quadrature/MI/Holevo/ALT_OPT unchanged. No Python worker remains and original Sleep state restored;929 protected hashes unchanged.

22km best remains(nu_raw,VA)=(.165,5.475),K=.07661740491526092. New(.165,5.4875) is runner-up,K=.07661723159351552,gap1.733217454003011e-7. Nearest evaluated VA neighbors of5.475 are5.45 and5.4875, both lower. Lower midpoint5.4625 remains missing.

Reference21.9393102292km best remains(.165,5.5),K=.07798099387393764; new source is runner-up,K=.07798091552916897,gap7.834476867252249e-8. No maximum improves at any of26 distances (deltaK=0 throughout).

Zero new completed coordinate searches;618 calls remain312 open-boundary/306 bracket-source-missing. Missing inventory54->55 reflects one measured old point removed and new actual finer midpoints requested: (.165,5.481249999999999) at22km and(.165,5.49375) atreference. It is not evidence of worse optimization or convergence. Nu slice at selectedVA5.475 still contains onlynu=.165; no nu bracket was closed because probe3 did not run.

Measured campaign CPU4149.515625s covers recorded Jobs/controllers, including recovered failed-resume dummy measurements; earliest failed-preflight JobCPU and independent-validation/test subprocess CPU are not fully included. Authorization elapsed to controller completion10391.192873s includes stopped/idle time and all carried-over execution. Controller and independent numerical verification completed before the original deadline10:56:11Z. Final narrative/status handoff was written after that deadline; do not describe the entire interactive turn as finished within3h. No AP or source/optimization calculation is scheduled after the deadline.

Further expensive expansion is justified only for explicitly chosen coverage/numerical-sensitivity questions, not promised SKR improvement. No total objective error bound or continuous/global certificate exists; ordering remains ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED.

Windows JobCPU guard is aggregate user CPU, as documented by [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information). Only the dummy wall-preflight workload used an idle live child to distinguish that guard from wall-time expiry; the production supervisor and all AP guards remain unchanged. Earlier failure/safety-stop/selection reports remain preserved in snapshots.
