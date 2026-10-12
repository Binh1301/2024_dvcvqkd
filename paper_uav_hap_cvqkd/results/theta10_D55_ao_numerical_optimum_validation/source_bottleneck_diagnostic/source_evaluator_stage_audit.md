# Original source evaluator stage audit

Status: BOTTLENECK_NOT_LOCALIZED. Code inspection and saved profiles only.

## Actual call graph and stages

`probe_worker -> build_mb_ensemble/reference_ensemble -> ExactMBEvaluator.source_moments
-> c4_gram_source_moments -> _fast gate -> _fallback subprocess
-> profile_worker -> original full_support_c4_worker.main -> _row`.

1. qam256.py constructs16x16 points, canonical normalization and normalized MB PMF.
   run_exact_mb_test2.py mapsnu_repo=42.5nu_raw and uses reference_ensemble at VA.
   No peak/VA box in this experiment; original ensemble validation preserved.
2. gram_moments.py extracts64 C4 prototypes/probabilities and four64x64 complex128
   Gram sectors. Detached eigh gate checks positivity/condition<=1e6/residual<=1e-12.
   B/C and completed5.5125 reject the gate (tiny negative binary64 eigenvalues),
   so the AP fallback is justified by actual route records. GateInfinity is not a
   measured AP condition number, nor proof of physical singularity.
3. Exact float.hex input goes to worker; original mp.workdps1050/1250/1450.
   Each row rebuilds four rotational overlap blocks (64x64), projects four
   Hermitian C4 sectors, then calls mp.eighe on each. 12 eighe calls if all rows finish.
4. Rank/minimum eigenvalue are checked. Rank!=256 returns unresolved row; resolved
   row performs original eigenbasis operator transforms, diagonal roots, two
   64-right-hand-side _lu_solve_matrix operations per sector and matrix products.
   Up to512 scalar-RHS lu_solve calls per resolved precision row (1536 if all3
   resolved). This is static work count, not actual retained run progress.
   Installed mpmath lu_solve copies A/b and adds10 bits inside each solve;
   LU_decomp caches on its copy. No evidence that sibling RHS solves share a
   factorization. Potential repeated work INSIDE the scientific evaluator is
   not authorized for replacement, including diagonal division/factor reuse.
5. C is computed by the original trace sums; w is the nonnegative weighted
   residual norm after original a/q/t/d transforms. No alternative formula.
6. Last two precision rows must have rank256/resolved and C/w agree under
   original1e-7+1e-6*max(abs(values)). JSON is emitted only after all rows.
   Parent converts C/w to float64, checks finite/physical values, ensemble hash
   consistency/support and atomically commits source cache. Cache retains final
   C/w, support and precision identity, NOT full intermediate convergence rows.

## Timing evidence and the collector defect

All target profiles, including SUCCESSFUL(.165,5.5125), have only about10s
captured self-time and one _row/_sectors frame, zero retained eighe calls.
They are fresh/long-lived files, but a recent mtime does not mean a full profile.
profile_worker snapshots every10s using profiler.dump_stats from a thread.
Installed stdlib dump_stats calls create_stats; create_stats calls disable().
Dummy-only reproduction confirms before-dump work recorded and after-dump work
absent. No reenabling is present in the original collector. This is a verified
OBSERVABILITY defect, not a proven numerical evaluator stall: completed source2
works despite the same truncated profile. Do not assign first10s hotspots to the
whole60min computation. Stage timings, precision completion/rank histories and
AP eigenspectra are NOT_RECORDED after that interval.

High precision is required by the preserved policy/float64 gate failure, but
these records do not prove exactly how many digits each failed source needs.
Neighboring successes and failures demonstrate heterogeneous elapsed outcomes;
without full-stage measurements, cannot distinguish intrinsic parameter cost,
precision-row resolution pattern, profiler effect or machine contention.

## Minimum proposed observations (NOT IMPLEMENTED)

Approve a separate execution-only observer change: profiler owned/reset/enabled
on its computation thread or independent stack sampling; dummy-validate full
capture first. Add stderr-only stage/precision start/end milestones without
changing call order/values, rank summaries already computed by original worker,
and external PID/Job CPU, monotonic+UTC, working set/commit and power samples.
Keep stdout result protocol and exact identity untouched. Any instrumented run
must prove same source inputs/operations/precision/validation/provenance; logging
overhead is measured, not assumed harmless or a speedup. No real AP launched.

Evidence: original worker/gram_moments.py/probe_worker/profile_worker,
execution_history_and_profiles.json and source_runtime_comparison.csv.
