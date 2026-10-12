# Exact source bottleneck diagnostic

CURRENTLY_VERIFIED_PASS_FOR_CACHE_ONLY_DIAGNOSTIC

Cache/log/code inspection only. No AP, new source, channel, MI/Holevo, SKR or AO execution; no operational fix applied.

| Probe | Wall seconds | Job CPU seconds | Termination | Last verified progress | Evidence |
|---|---:|---:|---|---|---|
| A (0.165,5.49375) | 1799.0310000000027 | 1733.859375 | SAFETY_ABORT | Initial sector construction ~10s; later UNKNOWN | results/theta10_D55_ao_numerical_optimum_validation/phase_2A/source_generation_ledger.json |
| B (0.16375,5.5) | 3595.75 | 3469.96875 | TIMEOUT | Initial sector construction ~10s; later UNKNOWN | results/theta10_D55_alt_opt_closure_continuation/source_generation_ledger.json |
| C (0.16531250000000003,5.5) | 3595.0 | 3516.90625 | TIMEOUT | Initial sector construction ~10s; later UNKNOWN | results/theta10_D55_ao_numerical_optimum_validation/phase_2A/source_generation_ledger.json |

## Twelve required conclusions

1. Why did the two P2 sources time out?
   VERIFIED: B and C exhausted the instrumented AP limit (~3592s); B wrapper exited0 after reporting TIMEOUT, C Job returned124. Both lack final valid C,w.
   INFERENCE: Job CPU/wall ~0.965 and ~0.978 is consistent with expensive active computation, not a mostly idle worker.
   UNKNOWN: Exact late-stage cause, completed precision rows and remaining work; timeout is not mathematical impossibility.
   PROPOSED: Obtain valid full-duration observations before attributing delay or predicting runtime.
   EVIDENCE: failed_probe_timeline.csv; original probe JSON/error; execution_history_and_profiles.json

2. Were the failed probes making numerical progress?
   VERIFIED: Their first ~10s profiles record original _row/_sectors and exp/sqrt arithmetic; Job CPU accumulated for most of the run.
   INFERENCE: They entered genuine AP computation; aggregate CPU is not proof of later precision/eigenvalue convergence.
   UNKNOWN: Progress after the first profile dump; no rank/C/w milestones survive.
   PROPOSED: Original-operation stage/precision milestones and independent CPU/working-set samples, approval required.
   EVIDENCE: profiles and dummy reproduction; full_support_c4_worker.py main/_row

3. Which stage is the primary bottleneck?
   VERIFIED: All retained target profiles stop at initial sector construction; dump_stats calls create_stats which disables the profiler, reproduced on dummy work.
   INFERENCE: exp/sqrt dominate only the captured startup interval; spectral/LU/matrix stages are static cost candidates, not measured bottlenecks.
   UNKNOWN: BOTTLENECK_NOT_LOCALIZED for the full computation.
   PROPOSED: Approve minimal observer correction; never substitute formulas/precision or claim eighe is the measured bottleneck.
   EVIDENCE: source_evaluator_stage_audit.md; stdlib cProfile source; execution_history_and_profiles.json

4. Resource exhaustion, suspension or numerical difficulty?
   VERIFIED: A has15.578s watchdog gap/AC0 and safety Job125; B/C recorded float64 gate rejection with tiny negative eigenvalues. C AC1/no recorded gap; B has no power watch.
   INFERENCE: Gate rejection explains why original AP fallback is required; it does not quantify physical AP conditioning or prove singularity.
   UNKNOWN: No RSS/commit/page-fault time series, AP eigenspectrum or OS suspend event record; no supported OOM/stall diagnosis.
   PROPOSED: Retain safety stop classification and add approved nonnumerical resource telemetry.
   EVIDENCE: supervisor receipts; fast_path_gate; supervisor_and_power_audit.md

5. Can operational improvements reduce runtime?
   VERIFIED: Collector loses profiling after its first dump; redundant preflight gate and unused MI-noise allocation exist outside source evaluation. No timing establishes their material overhead.
   INFERENCE: Stable AC and valid observability can prevent wasted interruptions; speedup of the mathematical worker is unmeasured.
   UNKNOWN: Magnitude of profiling overhead or setup savings; no promised runtime reduction.
   PROPOSED: Approve observer/ledger improvements separately; do not replace LU, precision, quadrature, backend or scientific operations.
   EVIDENCE: probe_worker; ExactMBEvaluator.__init__; profile_worker; local mpmath linalg.py

6. Is safe partial AP checkpoint/resume feasible?
   VERIFIED: Existing .prof is timing data, not matrices/arbitrary-precision state. Full source JSON commits atomically only after successful evaluator validation.
   INFERENCE: Completed-source reuse/campaign continuation is safe under exact identity; within-source resume is not supported.
   UNKNOWN: No demonstrated bit-consistent AP continuation checkpoint schema or round-trip equivalence.
   PROPOSED: Restart an approved failed source from original inputs; do not resume partial numeric state.
   EVIDENCE: checkpoint_resume_feasibility.md; worker.main; source_moments atomic source write

7. Which source should be prioritized next?
   VERIFIED: (.165,5.49375) is still the current lower P1 midpoint and was safety-aborted, not numerically timed out.
   INFERENCE: It is a defensible lower demonstrated timeout-risk first attempt, followed conditionally by current upper partner(.165,5.50625).
   UNKNOWN: Its completion time and K; the unmeasured partner can also be costly.
   PROPOSED: Plan A, only after new scope/budget and stable AC/approved observations.
   EVIDENCE: missing_source_priority.csv; reference_P1_blockers.csv

8. Minimum useful source set for P1/P2 advancement?
   VERIFIED: Current paired-step dependencies are four missing sources: (.165,5.49375),(.165,5.50625),(.16375,5.5),(.16531250000000003,5.5). The old VA5.5125 is already measured.
   INFERENCE: One source gives useful evidence; both current partners per coordinate allow one paired stage on that fixed slice. If an incumbent moves, recalculate actual dependencies.
   UNKNOWN: Whether any source changes the incumbent, which may change the next P2 fixed VA.
   PROPOSED: Follow original midpoint requests adaptively, not an automatic stale rectangular batch.
   EVIDENCE: reference_P1_blockers.csv; reference_P2_blockers.csv; original adaptive_maximize_1d

9. What further refinement is needed?
   VERIFIED: Current reference radii .0125/.0025 exceed1e-6. Unchanged-best paired halving needs14/12 total stages, or13/11 after one successful pair.
   INFERENCE: More exact moments are needed; four-step inner cap is insufficient on those current brackets. Tolerance is checked at next loop entry, not after the fourth pair.
   UNKNOWN: Actual refined path and source count when winners move; geometric counts are conditional.
   PROPOSED: Prepopulate only original requested exact points with approval and rerun original AO on progressively narrowed cache; settings changes require separate decision.
   EVIDENCE: ao_optimum_completion_criteria.md; original search loop; diagnostic_report.json refinement_arithmetic

10. What prevents a numerical coordinate optimum claim?
   VERIFIED: Both selected searches have missing partners,0 closed selected directions; nu0=.8 remains boundary-blocked; strictnu>0 excludes mathematicalnu=0.
   INFERENCE: Catalog maximum and DeltaK0 are not coordinate convergence. Local bracketing also does not exclude remote nonmonotone maxima.
   UNKNOWN: Continuous coordinate/global maxima and boundary limits.
   PROPOSED: Complete both searches at the actual selected pair, verify boundaries, stopping/status history and justify competing starts.
   EVIDENCE: saved original AO/P1/P2 histories; ao_optimum_completion_criteria.md

11. Which numerical accuracy evidence is missing?
   VERIFIED: Four prior metric repeats were bit-exact; source identity/support valid; smallest relevant top-two K gaps ~7.83e-8(reference)/1.73e-7(22km).
   INFERENCE: Repeatability is not a totalK error enclosure. Declared C/w comparison tolerances cannot be directly interpreted as a K uncertainty.
   UNKNOWN: Candidate-specific AP/MI-quadrature/entropy/roundoff error propagation sufficient for1e-8 stopping or displayed digits.
   PROPOSED: Plan separate approved accuracy evidence without lowering precision or changing evaluators; withhold unsupported digits/ordering confidence.
   EVIDENCE: Phase1/2A numerical_accuracy_status.md and original_evaluator_reproducibility.csv

12. Which continuation plan supports manuscript optimization?
   VERIFIED: 147-source AO/catalog agreement26/26 is finite evidence, not convergence. Neither plan is authorized to execute here.
   INFERENCE: Plan A plus valid observation is the best first cost-controlled step; Plan B is necessary if actual selected P2 dependencies persist.
   UNKNOWN: Whether any finite planned batch completes the numerical optimum.
   PROPOSED: Request separate approval for minimal operational observation fixes, then Plan A; dedicated120min P2 attempt conditional on real progress/safety and approval, not a completion promise.
   EVIDENCE: conservative_continuation_plan.md; difficult_P2_continuation_plan.md

## Validation

36 current regression tests PASS; 1340 protected hashes unchanged; git diff --check PASS.
Prior Phase1/2A files preserved. Existing frozen-spec historical hash discrepancy unchanged; no lifecycle promotion.
All plans NOT_RUN, require explicit separate scope/budget approval. Current finite maximum is not a continuous/global certificate.
Ponytail: stdlib pstats/cProfile and original provenance checker reused; no scientific driver imported or new dependency installed.
