# Objective B: completed ONE exact upper P1 probe; STOP

2026-10-10. One attempt, one success, zero timeouts/retries/additional probes/P2.
Original evaluator, arbitrary precision, quadrature, MI, direct-Z-minus Holevo,
SKR and original AO settings unchanged. No interpolation, dummy prelaunch gate,
observer/profiler redesign, publication-scale or held-out evaluation.

## Source moments and provenance

At `(nu_raw, V_A) = (0.165, 5.50625)`:

- `C = 3.214470263936996`
- `w = 1.0319626288646324e-06`
- Route: `ARBITRARY_PRECISION_FALLBACK`; support 256; provenance VERIFIED.
- Original precision ladder `[1050,1250,1450]`, source settings and implementation
  hashes preserved. Internal timeout remains 3600 seconds.
- Cache key: `dbb7a2a7024f84f97c455b0b3b564e9a307f369b362f80e055dfbf1e5d49497f`.
- Source SHA256: `eaf4eef65a1556bc60658d442620c012b2e6ebdc3ffb03cc30a83a122f2b4709`.

The source is in the sibling `exact_source_cache/` directory. The exact source
row and provenance are also saved in `new_exact_source_moments.csv`,
`source_result.json` and `source_checkpoint.json`.

## SKR and incumbent

| Link distance (km) | New probe K (bits/use) | Retained catalog-best pair | Catalog-best K (bits/use) |
|---|---|---|---|
| 21.9393102292 | 0.07798095622951573 | (0.165, 5.5) | 0.07798099387393764 |
| 22 | 0.07661659258097087 | (0.165, 5.475) | 0.07661740491526092 |

Reference probe delta is `-3.7644421913007875e-08 bits/use`. No incumbent pair
or selected maximum changes at any of the 26 distances. This is the literal
computed catalog ranking; discrimination of such small differences against a
certified total-K numerical error bound is NOT_ESTABLISHED.

The catalog grows from 149 to 150 compatible unique positive-MB sources. An
independent global scan finds 181 cache files: 152 MB files representing 150
unique pairs, plus 29 Uniform files. Duplicate MB files are counted once.
All 26 new SKR rows use the original saved channel for their distance and the
new hash-matched source, with no channel substitution. All 3,874 old objective
rows and their 26 channel identities are unchanged.

Full exact results:

- `new_exact_skr_26_distances.csv`: new probe, I_AB, beta_I_AB, chi_BE, K and provenance.
- `optimized_skr_26_distances.csv`: selected original-AO terminal at each distance.
- `old_vs_new_skr.csv`: old/new incumbents and new probe K at all distances.
- `objective_checkpoint.json`: 150 exact rows at each of 26 distances.

The original row label `selection_origin=resolved_145_point_bank` is a retained
producer literal, not the current catalog count. Counts above are independently
verified from identities and checkpoint rows; no historical CSV is rewritten.

## Original AO and true refinement progress

Original cache-only AO: 129 starts, 283 iterations, 618 aligned coordinate
searches. Selected actual AO terminals match the independently ranked expanded
catalog maximum at 26/26 distances; catalog ranking did not replace AO.
Individual terminal statuses: 20 `STAGNATED_IN_EXACT_CATALOG`, 109
`UNRESOLVED_BOUNDARY`. Completed coordinate searches: zero.

P1 at the reference distance retains best VA=5.5. Its exact-neighbor bracket
shrinks from `[5.49375,5.5125]` to `[5.49375,5.50625]`: width drops from 0.01875
to 0.0125, a one-third reduction. One missing exact upper dependency is resolved,
but zero additional paired midpoint levels are completed. The original search
still terminates `SOURCE_MISSING_REFINEMENT`, not numerical convergence.

The next requests, in original AO order, are:

1. `(0.165, 5.496875)`, VA hex `0x1.5fccccccccccdp+2`, key
   `9b0e009b708f2099ccf64c1bfdcf1d6d121cf2e85f59a93f5ca6cda53c2e7db3`.
2. `(0.165, 5.503125)`, VA hex `0x1.6033333333333p+2`, key
   `eae6eb908875f29ea033b33fd19c0b59824c60ad28fd3fccc87d0b2dc304e001`.

Neither is run or authorized by this attempt. P2 remains unchanged with missing
`(0.16375,5.5)` and `(0.16531250000000003,5.5)`. Outer directions, missing source
moments, parameter closure and total-K discrimination remain unresolved. This
is BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY, not a continuous/global optimum.

## Runtime, tests and cleanup

Controller origin `2026-10-10T08:25:01.613412Z`; total deadline
`10:25:01.613412Z`. Actual source API wall 3090.110s (51m30.110s), within the
unchanged 3600s internal timeout. Source Job wall 3097.672s/CPU2998.953125s;
postprocess Job wall36.797s/CPU35.5s. Controller including preflight and both
phases finishes3146.937s (52m26.937s). Measured Jobs plus controller CPU is
3049.1875s; independent tests/audit/tooling CPU is excluded.

Both native Job receipts verify zero active processes, closed handles, no
remaining watchdog threads, no power/suspend abort, and restored nested Sleep
leases. Outer Sleep restores original ES_CONTINUOUS-only state. Native process
inspection finds no remaining scoped scientific worker. 10 prelaunch tests
PASS3.028s; 63 post-run scoped regression tests PASS10.959s. No redundant native
dummy test gate was rerun. All 1,825 protected runtime hashes remain unchanged.
Old scientific artifacts are preserved; producer and numerical defaults are
unchanged. Frozen historical hash discrepancy remains recorded and unchanged;
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` remains in force.

Machine-readable checks: `final_report.json`, `postprocess_report.json`,
`final_verification.json`, `test_verification.json`; final reporting/cleanup time
is recorded separately in `final_cleanup.json`. STOP: no retry, other AP or P2.
