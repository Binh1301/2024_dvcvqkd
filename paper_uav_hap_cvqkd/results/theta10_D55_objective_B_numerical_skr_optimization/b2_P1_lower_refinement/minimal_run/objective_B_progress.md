# Objective B — completed ONE lower P1 probe; STOP

2026-10-10. One AP attempt, one success, zero timeout/retry/additional P1/P2.
Original source API/controller/Job safeguards reused; evaluator, precision,
quadrature, MI, direct-Z-minus Holevo, SKR and original AO defaults unchanged.
No interpolation, approximation, fitting, observer/profiler or dummy cleanup gate.
New execution outputs are here in minimal_run/; the root preflight artifacts,
completed upper results and Objective A remain untouched.

## 1–5. Source result, exact SKR and incumbent

At `(nu_raw,VA)=(0.165,5.496875)`:

- `C = 3.209726318326182`
- `w = 1.0213661080792113e-06`
- nu_raw binary64: `0x1.51eb851eb851fp-3`.
- VA binary64: `0x1.5fccccccccccdp+2`.
- Source key: `9b0e009b708f2099ccf64c1bfdcf1d6d121cf2e85f59a93f5ca6cda53c2e7db3`.
- Source SHA256: `a54901e4f186319693b8ae6d761ba46724cc4bcfa2800a03e996fc906a5166bf`.
- `ARBITRARY_PRECISION_FALLBACK`, support256, provenance VERIFIED, original
  precision ladder1050/1250/1450 and internal timeout3600s unchanged.

At L=21.9393102292km, fixed nu_raw=0.165, the requested exact comparisons are:

| VA | I_AB | beta I_AB | chi_BE | K (bits/use) |
|---|---|---|---|---|
| 5.49375 | 0.6336060059179758 | 0.6019257056220769 | 0.5239447252887337 | 0.07798098033334322 |
| 5.496875 | 0.633897663992304 | 0.6022027807926887 | 0.524221787286018 | 0.07798099350667076 |
| 5.5 | 0.6341892631163653 | 0.602479799960547 | 0.5244988060866094 | 0.07798099387393764 |
| 5.50625 | 0.634772284608971 | 0.6030336703785224 | 0.5250527141490067 | 0.07798095622951573 |

The new computed K is smaller than the incumbent by
`3.6726688357191506e-10 bits/use`. The incumbent does NOT change. This is the
literal computed finite-catalog ranking, not a rigorously resolved physical
ordering: a certified total-SKR error bound is unavailable. Successive exact
source precision checks alone do not certify total MI/Holevo/SKR discrimination.

## 6–9. Original P1 bracket and next requests

Feeding the new exact point into the original cache-only P1 yields bestVA5.5 and
bracket `[5.496875,5.50625]`. The old bracket was `[5.49375,5.50625]`.
Nominal width falls0.0125->0.009375, decrease0.003125 (25%). Binary64 width
is `0.009374999999999467`. No manual shrink or assumed winner was used.

P1 still ends `SOURCE_MISSING_REFINEMENT`; coordinate completion is false.
One exact lower dependency is resolved, but zero additional paired-midpoint
levels or complete coordinate searches are verified. The original loop's next
requests, in order, are:

1. `(0.165,5.4984375)`, VAhex `0x1.5fe6666666666p+2`, key
   `b926dee57f352e1ff94570f4f187b83bcb0b9d24c5ae30f65fc2a414e66a5b04`.
2. `(0.165,5.503125)`, VAhex `0x1.6033333333333p+2`, key
   `eae6eb908875f29ea033b33fd19c0b59824c60ad28fd3fccc87d0b2dc304e001`.

Neither was run or authorized by this attempt. P2 remains unchanged, with
missing `(0.16375,5.5)` and `(0.16531250000000003,5.5)`.

## 10–13. AO, gains and remaining numerical refinement

Catalog150->151 unique compatible MB sources. An independent scan finds182
cachefiles:153 MB files representing151 pairs (two consistent duplicates),
29 Uniform files. All3,900 old objective rows and26 old channel identities are
unchanged;26 new rows were computed by the original evaluator with the validated
new source. Selected parameters and maximum SKR are unchanged at all26 distances.

Original AO recheck:129 starts/283 iterations/618 aligned coordinate searches.
Actual AO-selected terminals match independent catalog maxima26/26; maxima were
not substituted for AO. Individual terminal statuses:20
`STAGNATED_IN_EXACT_CATALOG`,109 `UNRESOLVED_BOUNDARY`. Completed coordinates0.

The new bracket width is approximately9,375 times tolerance1e-6. The original
criterion is NOT full width: it checks the largest distance from bestVA to a
neighbor. This radius remains `0.006249999999999645`, approximately6,250
tolerances, because the upper neighbor has not moved. Under an IDEALIZED
fixed-best, both-sides midpoint-halving assumption,13 additional paired levels
would reduce that radius below1e-6; a14th loop visit recognizes closure because
the original code checks the criterion before evaluating the next pair.
Halving the entire width to <=1e-6 would instead require14 levels.

These are conditional estimates, not guarantees. After four idealized paired
levels the largest radius would still be about0.000390625,390.625 tolerances.
Unchanged inner cap4 cannot close this starting bracket in one such call;
missing exact moments currently block its first stage. None of these diagnostics
authorizes a cap change. Missing P1/P2 sources, unresolved outer directions and
lack of certified total-K discrimination prevent a continuous numerical/global
optimum claim. BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY remains the scope.

## 14. Runtime, tests, provenance and real-worker cleanup

Controller origin `2026-10-10T09:56:43.362245Z`; total deadline
`11:56:43.362245Z`. Source API wall2536.594s (42m16.594s), below original3600s.
Source Job wall2542.312s/CPU2450.875s; postprocess Job wall104.531s/CPU101.171875s.
Controller including both phases finishes2659.453s (44m19.453s). Measured Jobs
plus controller CPU2566.703125s excludes independent audit/tests/tooling CPU.
Final reporting/cleanup elapsed time is recorded in final_cleanup.json and
must remain within the same7200s clock, not a restarted budget.

Both actual native Job receipts verify zero active processes, closed handles,
no watchdog thread, no AC/suspend abort, and restored nested Sleep requests.
Outer Sleep restores its original ES_CONTINUOUS-only state. Native inspection
finds no remaining scoped scientific worker. All1,870 protected runtime hashes
are unchanged.8 prelaunch tests PASS1.543s;67 post-run regressions PASS26.549s.
The no-auto-AP test was corrected to verify no mkdir rather than assume an
output directory remains absent after a successful run. Its original prelaunch
bytes are archived in test_producers/ and match the recorded hash; no numerical
producer was edited. No native dummy test gate was rerun.

Full data: new_exact_source_moments.csv, new_exact_skr_26_distances.csv,
reference_P1_comparison.csv, optimized_skr_26_distances.csv, old_vs_new_skr.csv,
ao_multistart_recheck.csv, reference_P1_refinement.csv and objective_checkpoint.json.
Machine evidence: source_result.json, final_report.json, postprocess_report.json,
final_verification.json, test_verification.json and final_cleanup.json.
The old `selection_origin=resolved_145_point_bank` is a retained producer label,
not the catalog size. Current counts are independently checked from exact keys.
Frozen historical discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

STOP after this single successful probe; no retry, second P1 or P2, no remaining
budget reuse or numerical/global/lifecycle promotion.
