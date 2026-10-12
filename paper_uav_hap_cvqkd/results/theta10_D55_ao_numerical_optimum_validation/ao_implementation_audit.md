# Actual AO implementation audit

Scope: Phase1 saved-record audit only; no AP, channel, MI/Holevo or optimizer rerun.
Authoritative implementation: scripts/run_theta10_D55_alt_opt.py (ExactObjective,
adaptive_maximize_1d, coordinate_search_complete, stopping_status) and
run_theta10_D55_alt_opt_distance_sweep.py (starting_va, run_single_distance_ao).
Batch3 evaluate() supplies genuine records and selected-final postchecks.

P1 fixes nu^(r-1) and searches VA; P2 fixes the NEW VA^(r) and searches nu.
The following P1 fixes the NEW nu^(r). All618 search records were aligned with
all283 real iterations and52 final postchecks, validating fixed binary64 values,
returned K, status and entire candidate-event histories. No final-copy trajectory.

The mathematical argmax over a continuous domain is a TARGET, not the returned
result: each inner call returns the maximum of its valid exact-tested candidates.
Implementation domain is nu_raw>0,VA>0; the requested nu>=0 includes Uniform at
nu=0, which register_catalog and ExactObjective explicitly exclude. No silent
domain change. A stored Uniform comparison is not an AO nu=0 boundary closure.

Starts are nu=.1,.15,.3,.8, plus previous-distance selected (nu,VA) after the
first distance. Initial VA is the smallest available exact VA on that nu slice,
unless the warm VA exists with exactly the same binary64 key.129 starts total.
The original four-start reference experiment is retained separately; later
records have five reference starts, not four. See historical_execution_inventory.

Inner search evaluates every existing exact slice point, not a preset dense box.
An endpoint maximum requests half the smallest value or twice the largest,
up to3 expansions; missing source leaves BOUNDARY_NOT_CLOSED. A singleton does
not become closed after one lower outer point: the other side is untested.
An interior best uses nearest measured lower/upper neighbors. If radius>1e-6,
both binary64 arithmetic midpoints are requested. Paired attempts consume one
refinement stage, even if missing, then stop immediately on missing data.
Four stages maximum; radius is checked at the next stage ENTRY. At the cap,
successful midpoint attempts without an entry tolerance check return failure.
None of the618 current calls reached the refinement cap: missing data/open
boundary are the active blockers. No monotonicity in either parameter assumed.

Objective caching binds current scientific code, config, exact channel context,
GH8, beta=.95, epsilon=.0186, ensemble/source keys and float.hex() coordinates.
Sources retain historical raw keys; only proven LF/CRLF aliases are accepted.
allow_new_source=False fails closed; no interpolation, abs(K), clipping or fitting.
Audit guards forbid source_moments, underlying AP fallback, fresh objective,
channel generation and optimizer calls. Current checkpoint rows only are restored.

Outer stopping uses |Delta K|<=1e-8, BOTH coordinate searches numerically closed,
no earlier unresolved search, and no current numerical/monotonic warning.
Small Delta K with incomplete inner search is STAGNATED_IN_EXACT_CATALOG or
UNRESOLVED_BOUNDARY, never CONVERGED_NUMERICALLY. Outer cap6 remains unchanged.
Sampled interior bracketing is LOCAL evidence, not closure of all remote extrema
of an unbounded non-monotone objective. Even local closure would not prove global.

Actual per-coordinate fresh evaluation/cache-hit counts are recorded in each
iteration and exported unchanged. Requested objective-call counters are only
stored per RUN/distance, not per coordinate: these fields are NOT_RECORDED.
Recorded event counts are reported separately, not relabeled as objective calls.
Historical source keys are attributed via verified current pair lookup and
explicitly are not asserted to be original historical raw keys. Current146 rows
are independently validated against the original source and objective identities.

All settings/scientific files remain unchanged. Frozen-spec hash differs from
AGENTS historical expected hash (existing author re-freeze); it is neither repaired
nor certification authority. Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
