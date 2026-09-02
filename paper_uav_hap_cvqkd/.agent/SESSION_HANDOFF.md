# Session Handoff

Date: 2026-09-02

## Authoritative Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Authorization: `FROZEN_THRESHOLD_VALIDATION_EXECUTION_AUTHORIZED`.

## Current Evidence

The provenance-valid V1 smoke is complete and preserved at
`results/pointwise_guard_smoke_v2.json`, SHA-256
`4a914944aecb09204187040e461e84cd67e34f4c254647eea8ece2e625854360`.
Its two six-step traces are byte-identical; every step is a pre-update
`POINTWISE_GUARD_BAND_REJECT`; no proposal or commit occurred. The frozen V1
outcome is `OPTIMIZATION_EFFECTIVELY_FROZEN`. Do not rerun or retune it.

The V2 methodology and implementation are frozen and its smoke is complete:

- config SHA-256:
  `6eb21147336e4ca4c305abdf2532fe03eaa8e4bb570a4c8918bdb91638727845`;
- execution manifest SHA-256:
  `d27d7fd6be10121b4217e8cc72af88481e994acb89d30787cfa7c8c9b5e4f568`;
- smoke artifact SHA-256:
  `321b6dc4fd28168878d84e511478c209379b6c0aa36da5d9e794092317ca36f6`;
- methodology artifact SHA-256:
  `dbf1b4dc369195f8ee94bd8870f3a6142a69bba7e3130f2a2d8822e699d5ad77`;
- rule: rigorously certified support and `certified_margin > 0`;
- `uncertainty_upper`: diagnostic only;
- positive engineering margin: none justified, fixed at zero.
- Threshold gate review artifact SHA-256:
  `3f75ddb9325ee8a15af2b05039232aec0d76088fff2b1e86a3ab3137b1d008de`.

V2 outcome is `OPTIMIZATION_USABLE`: 12/12 updates committed, all pre/post
checks admissible, all gradients finite, zero rollbacks/equivalence failures,
zero certification/provenance failures, and byte-identical repetitions.

The dense-Fock cutoff blocker is stale for the active cutoff-independent C4-Gram
production path, although its failed stress diagnostic is preserved. The
active threshold/support blocker is genuine: formal support identity is false,
and the candidate comparison is outcome-informed. Baseline selection remains
downstream of that blocker.

Implementation must use global inward-facing Arb endpoints or certified
adjacent inertia brackets, make the strict comparison before non-directed
float serialization, and fail closed. The current direct-eigenball midpoint
selection is not by itself a proof of adjacency.

Candidate `1e-13` remains `PROPOSED_UNAPPROVED`; historical `1e-12` remains
`INVALID_UNAPPROVED`. The frozen model SHA-256 remains
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.

## Exact Next Permitted Action

Run `python scripts\\run_threshold_validation_v1.py
--execute-frozen-validation` exactly once from the project root. The manifest
binds 12 fixtures, their hashes, 600/800-digit full-support oracle convergence,
the candidate production path, existing tolerances, and all required
observables. Do not rerun either smoke; a pass still needs explicit author
threshold approval.

The only attempt failed before threshold calculation because the harness used
the production fixture seed/state binding but checked the independent-roster
hash. EVID-0043 records the corrected wiring; the production fixture is
unchanged.

No scientific source, security functional, frozen model, training, baseline
selection, optimized-MB search, final-test access, or held-out evaluation
changed or occurred.
