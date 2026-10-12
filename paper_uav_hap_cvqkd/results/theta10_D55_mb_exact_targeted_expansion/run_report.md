# Targeted exact MB expansion — candidate plan only

PLAN_PREPARED_AWAITING_NEW_COMPUTE_BUDGET

Currently verified MB catalog: 139 unique pairs. No newer compatible source in the scoped validated cache directories. No AP/SKR/AO rerun.
No new total/per-probe budget was approved. Previous 14400s/3600s session is STOPPED_AT_HARD_BUDGET; configuration watchdogs do not constitute new authorization.

| Priority | nu_raw | VA | Current affected searches | Selection reason |
|---:|---:|---:|---:|---|
| 1 | 0.16562500000000002 | 5.5 | 18 | Closest missing upper-nu midpoint; prior failure had only 33.781s remaining budget, not a 60-minute feasibility test |
| 2 | 0.165 | 5.45 | 8 | Original lower/upper VA midpoint; together with its paired neighbor covers both sides of selected VA=5.5, but further refinement remains |
| 3 | 0.165 | 5.525 | 8 | Original lower/upper VA midpoint; together with its paired neighbor covers both sides of selected VA=5.5, but further refinement remains |

All three are actual midpoint requests at baseline/22 km, with exact hex/cache/ensemble identities verified. No arbitrary candidate was invented.
(.16375,5.5) is deferred because its unchanged evaluator already timed out at 3600s. It is not declared invalid/inferior and will still block the other side of the nu search.
C/D form the two missing VA midpoint sides; their completion can enable another refinement attempt, not guarantee a completed search. Further exact midpoint levels and other branches remain unresolved.
After authorization: start serially with ONE probe, validate original source checks/provenance, checkpoint and measure CPU/wall time, then evaluate its newly enabled SKR at all 26 distances using compatible old objectives. Review actual benefit/cost before another probe.
Retain epsilon=1e-8, parameter tolerance=1e-6, outer cap6, inner cap4, original starts/continuation and source ladder1050/1250/1450. No peak/budget constraints or interpolation added.
Very small positive numerical deltas are not automatically meaningful; no demonstrated uncertainty bound is invented from epsilon_opt. Comparisons without adequate reliability evidence remain INCONCLUSIVE.

| Metric | Before | After this planning turn |
|---|---:|---|
| Compatible MB exact pairs | 139 | 139 (measured cache) |
| New exact MB pairs | 0 | 0 |
| Distances matching catalog maximum | 26/26 last known | Expansion NOT_RUN |
| Distances with improved SKR | 0 last known | Expansion NOT_RUN |
| Numerically converged distances | 0 last known | ALT_OPT NOT_RUN |
| Unresolved coordinate directions | 558 full26 /130 five+postchecks last known | NOT_RUN |
| Unresolved boundary directions | 280 full26 /35 five+postchecks last known | NOT_RUN |

Files named expanded/after contain explicit unexpanded baseline snapshots or NOT_RUN fields, not fabricated after results. New-source CSV is header-only; per-probe new wall/CPU values are blank.
No figure generated: no new best curve. Uniform/fixed-MB were neither recalculated nor modified.
Protected files unchanged=680; regressions PASS=True; git diff --check PASS=True.
Scientific computation, frozen specification, training/test access, baseline selection and threshold approval unchanged. Frozen-spec discrepancy remains open; publication lifecycle unchanged.
STOP for user approval of total hard runtime and maximum per-probe runtime. No expensive computation started.
