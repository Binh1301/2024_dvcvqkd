# Actual AO stopping criteria and correction

SKR epsilon_opt=1e-08 bits/use, defined at scripts/run_theta10_D55_alt_opt.py:57; runtime source: imported module constant (no CLI epsilon override).
Parameter / inner-bracket tolerance=1e-06; outer max=6; scripts/run_theta10_D55_alt_opt.py:59. --max-ao-iterations overrides the six-iteration default in original drivers; this validation uses six.
Endpoint expansion cap=3; refinement-stage cap=4. There is no independent fixed maximum objective-call count for a slice: initial exact slice size plus up to three endpoint probes and eight midpoint attempts (some successful calls reused locally).
Previous criterion: abs(delta K)<=1e-8 OR both parameter displacements<=1e-6, conditional on reported bracket statuses. A bracketed catalog could be treated as complete even with untested regions; initial missing probes were not universally considered. Earlier unresolved searches were not checked on every convergence branch.
Corrected policy retains epsilon=1e-8. Both coordinate searches must reach NUMERICALLY_CLOSED_LOCAL_BRACKET (two-sided bracket radius<=1e-6, no missing probes or numerical failures), no unresolved earlier search may invalidate stopping, and -1e-8<=delta K<=1e-8 is allowed only with no stage decrease exceeding numeric tolerance. The parameter-displacement alternative no longer certifies convergence.
This is a local numerical bracket condition, not a certificate for an unbounded global maximum. Missing probes have no K value. Zero improvement with incomplete coverage is STAGNATED_IN_EXACT_CATALOG; open endpoint is UNRESOLVED_BOUNDARY; no valid inner candidate is INNER_SEARCH_FAILURE; actual evaluator failures/decreases are NUMERICAL_FAILURE; exhausting six outer iterations is MAX_ITERATIONS_REACHED. No parameter, peak or modulation upper bound was added.

## Known baseline trajectory from immutable execution records

| iteration | VA after | nu after | K before | K after VA | K after nu | delta K | epsilon comparison | current interpretation |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 6.0 | 0.16 | -0.016459743778080998 | 0.07590840558617484 | 0.07785179812729415 | 0.09431154190537515 | abs(delta)<=epsilon: False | CONTINUE; both inner searches missing exact probes |
| 1 | 5.5 | 0.165 | 0.07785179812729415 | 0.07797104999097981 | 0.07798099387393764 | 0.00012919574664349565 | abs(delta)<=epsilon: False | CONTINUE; both inner searches missing exact probes |
| 2 | 5.5 | 0.165 | 0.07798099387393764 | 0.07798099387393764 | 0.07798099387393764 | 0.0 | abs(delta)<=epsilon: True | STAGNATED_IN_EXACT_CATALOG; both inner searches missing exact probes |

The final zero delta meets the scalar epsilon comparison but does not establish convergence. Detailed candidate comparisons were verified in the independent audit and are rechecked during representative replay.
