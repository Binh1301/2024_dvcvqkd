# Unchanged four-step refinement: code and execution audit

Runtime: epsilon_opt=1e-8, parameter_tolerance=1e-6, outer=6, inner stages=4. No setting changed.

## Actual implementation

Limit: scripts/run_theta10_D55_alt_opt.py:61; counter resets per coordinate-search invocation at scripts/run_theta10_D55_alt_opt.py:363.
Loop: scripts/run_theta10_D55_alt_opt.py:365; each stage attempts both (lower+best)/2 and (best+upper)/2 at scripts/run_theta10_D55_alt_opt.py:381.
Counter increment: scripts/run_theta10_D55_alt_opt.py:385, AFTER both attempts, BEFORE the missing-result check.
A missing-source attempt therefore consumes one stage then breaks immediately. Cache hits and fresh successful objective calls are not individual stage units: one paired midpoint attempt counts as one stage regardless of caching.
Initial exact-catalog evaluations and boundary expansions do not increment refinement_stages. Successful midpoint pairs allow the next stage.
Missing point: scripts/run_theta10_D55_alt_opt.py:387; cap exhaustion: scripts/run_theta10_D55_alt_opt.py:392.
Cap exhaustion yields INNER_SEARCH_FAILURE, not numerical convergence. Raising the cap would not change outer epsilon or the six-iteration cap, but could change inner search completion and indirectly the outer decision if source coverage were sufficient.

## What actually happened

Strict rerun 558 coordinate invocations: 280 no-refinement/open-boundary; 278 stop at the FIRST paired attempt on missing source. Zero hit cap 4.
Latest representative replay 130 coordinate/postchecks: 35 open-boundary, 95 first-attempt source-missing. Zero hit cap 4.
Thus cap=4 is a prospective independent ceiling, not the active termination cause in these recorded searches.

## Final baseline slices

| coordinate | fixed | exact bracket | missing values | radius | conditional halvings |
|---|---:|---|---|---:|---:|
| V_A | 0.165 | [5.4, 5.55] | [5.45, 5.525] | 0.09999999999999964 | 17 |
| nu_raw | 5.5 | [0.1625, 0.16625] | [0.16375, 0.16562500000000002] | 0.0025000000000000022 | 12 |

The 17/12 counts are ceil(log2(radius/1e-6)), a conditional parameter-radius reduction with fixed best and both midpoint evaluations available. They are NOT objective-tolerance counts or global-optimality evidence.
In the unchanged implementation the radius check occurs at the BEGINNING of the next loop stage. Reaching radius tolerance on the last allowed midpoint stage still produces REFINEMENT_LIMIT_REACHED: in this fixed-best idealization the verdict needs at least 18/13 allowed stages, not merely 17/12 midpoint levels.
At the final pair neither coordinate completes even its first paired refinement: VA needs 5.45/5.525 at nu=.165; nu needs .16375/.16562500000000002 at VA=5.5.
New prior source points became initial catalog neighbors on subsequent searches; individual successful AP probes are not successfully completed paired refinement stages.
For every offline cap 4/8/12/16/20, existing data meet the same UNKNOWN_SOURCE before that cap. No hypothetical objective or source was invented.
Outer delta K=0 already meets objective epsilon; incomplete inner searches/earlier unresolved conditions remain. This is catalog stagnation, not numerical convergence.
