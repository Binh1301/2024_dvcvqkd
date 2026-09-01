# Next Actions

## V3 Superseding Next Action - 2026-09-01

V2.2 resolved the independent exact-tau oracle gate, but V2.3 failed its
four-case whole-segment feasibility gate. Do not run all 12 V2 segments.

Create a new prospectively frozen V3 only after these implementation blockers
are resolved and synthetically tested:

1. Replace immediate-process termination with Windows process-tree/Job-Object
   enforcement. Test a worker that spawns a descendant holding stdout and
   prove parent return remains within deadline plus frozen grace.
2. Atomically journal the complete `PATH_DOMAIN_CERTIFIED` artifact before any
   C4/Taylor node starts, so a later kill cannot erase Phase-3 evidence.
3. Preserve scalar Taylor coefficients and remainder matrices through
   `Q*H(t)Q`; do not collapse the whole Taylor model to independent entrywise
   balls before congruence.
4. Partition far-positive, near, and far-negative modes deterministically and
   eliminate positive/negative far blocks sequentially with validated solves,
   accounting for all coupling.
5. Profile/canonicalize C4 coefficient construction so one node no longer
   costs roughly 90 seconds; cache midpoint and parameter-path quantities that
   are invariant across precision retries.
6. Freeze a new SHA-ranked feasibility subset and numerical gate before any V3
   realized outcome. At least one whole segment, all persistent path-domain
   rows, zero resource/provenance failures, and a strictly tighter comparable
   enclosure metric are still required before all 12.
7. Validate result artifacts against a tightened schema. Before any future
   full-mode pass, bind the canonical feasibility artifact and verify its
   config identity, provenance, gate fields, and schema—not only a caller
   supplied hash plus status string.

Preserve the certified V2.2 exact-tau artifact; it need not be recomputed
unless an input or bound producer changes. Candidate `1e-13` remains proposed
and unapproved. Historical `1e-12` remains invalid and unapproved.

## Current Gate

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Publication-scale execution, optimized-MB/baseline selection, final-test
access, optimizer integration, and threshold approval remain unauthorized.

The remaining sections below preserve the superseded V1 plan for history; the
V3 action above is authoritative.

## Completed This Cycle

- Validated point block-LDL* inertia: 24/24 endpoints certified at 160 bits.
- Four frozen oracle fixtures point-certified; mathematical rank/support
  distinction preserved.
- Clustered/repeated/threshold-adjacent and segment regressions: 32/32 pass.
- Direct interval whole-segment cycle: 0/12 certified, 0 crossings, 12
  unresolved after 12302.94 seconds; preserved fail-closed.
- Adversarial review completed; V1 acceptance defects recorded.

## Exact Next Action

Create a newly versioned, prospectively hash-bound whole-segment certifier
before another realized-path run.

It must:

1. enforce the exact bundle, environment, roster, endpoint, config, schema,
   producer, point-module, segment-module, and frozen-model hashes;
2. enforce actual elapsed runtime at acceptance, not only cooperative checks;
3. certify the path domain and continuity before any endpoint-count crossing
   claim;
4. report guard-count gaps and unattempted sectors explicitly;
5. use a sharper validated fixed-basis congruence/eigencluster,
   affine/Taylor-model, or validated Schur-complement enclosure rather than
   the dependency-inflated full-matrix Frobenius guard;
6. freeze tests, precision, subdivision, and work limits before inspecting a
   new 12-path outcome.

An optional independent diagnostic may compute high-precision eigenvalue
counts above the exact binary64 proposed `tau` for the four oracle fixtures.
It cannot approve the threshold.

## Pass Criteria for the Next Cycle

- Every accepted leaf rigorously excludes zero from the shifted spectrum and
  has the same certified support count.
- Accepted leaves cover all of `[0,1]`; endpoint equality alone is not proof.
- All normalized denominators and gauges are rigorously positive on any path
  used for a crossing claim.
- Arithmetic ambiguity, zero inclusion, missing input identity, unattempted
  sectors, or work-limit overrun fails closed.
- At least one realized path is resolved without changing `tau` or the frozen
  equations; otherwise preserve the quantitative blocker.

## Prohibited

- Approving/activating `1e-13` or reactivating `1e-12`.
- Treating zero inclusion as a proven crossing.
- Editing the completed V1 artifacts or producers in place.
- Publication training, optimized-MB/baseline selection, or final-test access.
- Modifying `FINAL_MODEL_SPEC.md`, `src/cvqkd`, or the physical/security
  functional to obtain convergence.

## Preserved Facts

- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- MI remains `N_MC=2048`.
- Candidate `1e-13` remains proposed/unapproved.
- Historical/configured `1e-12` remains invalid/unapproved.
- Final test remains inaccessible and untouched.
