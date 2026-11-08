# Phase 5A independent implementation review

Review date: 2026-11-07.

What this change does: The graph solvers accept either a static waypoint rate vector or a slot-by-waypoint rate matrix. Explicit adapters sample destination rates at slot-end times once, and selected-reference lookup loading refuses incompatible or incompletely established contexts.

**Verdict: Ship within the declared Phase 5A software-interface scope. No confirmed must-fix defect found.** This verdict does not authorize a physical experiment, lookup regeneration, paper-mode execution, or a security claim.

## Evidence inspected

- User Phase 5A attachment and `docs/phase5a_implementation_plan.md`.
- `evaluation.py`, `rate_provider.py`, `baselines.py`, `dp_solver.py`, `config.py`, `skr_lookup.py`, and `experiments.py`; connected finite-size, graph, cloud and reference-comparison implementations.
- New time-dependent-rate tests, existing planning tests, and the changed paper-figure fixture. A source search checked all rate-array consumers.
- `docs/phase5a_validation/protected_before.json`: recomputed hashes for all 1,067 listed existing files. None were missing. Exactly the seven declared existing files differed: the six changed implementation modules and `tests/test_paper_figures.py`. New files are outside that before-manifest comparison.

## Correctness observations

- Scenario construction copies rate and availability arrays, rejects nonfinite or mismatched rates, and makes both arrays read-only. Static vectors and repeated matrices share the same numerical path through `rate_at`.
- All solvers evaluate destination waypoint `q_k` using zero-based row `k-1`; adapters call providers at `k * dt`. Static and dynamic algorithms share availability, graph, energy and finite-size settings.
- The accumulated state remains `a=sum(z*r)` and `u=sum(z)`. The finite-size penalty is evaluated on the accumulated block. DP pruning compares labels only at the same slot, destination and retained-slot count; lower energy and greater accumulated contribution are sufficient for dominance for this fixed exogenous-rate model.
- Optical attenuation requires retained signals and an all-one template. The link adapter rejects fractional signal counts, erased slots with nonzero contributions, unapproved policies, and mode/provenance mismatches. Source callbacks remain responsible for the physical correctness of their rates and cloud realization.
- Selected-reference lookup loading cannot pass on the checked physical subset alone. Missing reference/protocol pairs and incompatible contexts fail before lookup file loading. No-context legacy loading is explicitly only numerical loading; it does not certify scientific compatibility.
- Existing plot tests now obtain fresh measured synthetic artifacts with current producer hashes. Historical metric replay is tested separately from producer-provenance acceptance.

## Reviewer verification

`python -m pytest -q tests/test_time_dependent_rates.py tests/test_planning.py`

Result: **27 passed in 0.74 s**, no failures.

An additional independent, in-memory enumeration check used 100 cases from RNG seed 503. It varied dynamic rates (including negative values), binary availability, energy budgets and terminal restrictions on the existing three-waypoint numerical fixture. Both DP objectives matched exhaustive feasible-path arithmetic with `rtol=1e-13`, `atol=1e-8`. This was software validation only; no research rates or results were generated.

## Scope and limits

- Dynamic sampling is a programmatic interface; the existing YAML/CLI runner remains static. No missing dynamic CLI feature is inferred from this scoped implementation.
- Full-horizon snapshots require `O(HJ)` storage and provider evaluations. Greedy decisions use current-slot entries; DP uses the predicted horizon. Snapshot preparation and retrospective best-prefix selection do not make their information access equivalent.
- Read-only rate/availability arrays prevent accidental element writes. The API still relies on callers treating the Scenario, graph and callbacks as fixed during sampling and solving; it is not an isolation boundary against arbitrary provider mutation.
- The lookup guard deliberately has no successful admission path until complete geometry/noise/protocol/lineage binding exists. This documented restriction is not an inferred compatibility approval.
- Exactness is scoped to the fixed finite graph, supplied exogenous arrays, horizon and float64 model. No continuous-trajectory, physical-channel or security certification follows from these checks.

Not checked: the full suite was not independently rerun by this reviewer; the implementing agent owns its full-suite count. Z/w, MB-QAM/Holevo derivations, physical backend validity and publication-scale behavior were not reviewed or executed.
