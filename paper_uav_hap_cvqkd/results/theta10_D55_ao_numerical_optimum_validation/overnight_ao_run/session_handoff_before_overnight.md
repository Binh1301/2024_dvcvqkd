# Session Handoff

## Current: exact source bottleneck diagnostic COMPLETE; STOP before AP or fixes

2026-10-09 EVID-0150/DEC-0133. User explicitly authorized cache-only inspection,
logs, code audit, dummy regression checks and plans, NOT real AP/source/SKR/AO
or execution-layer improvements. Output:
results/theta10_D55_ao_numerical_optimum_validation/source_bottleneck_diagnostic/.
All13 requested files present plus execution_history_and_profiles.json,
protected_input_manifest/input_manifest_after and regression_tests.json.
Prior Phase1/Phase2A artifacts unchanged; pre-diagnostic handoff archived here.

Key finding: existing profile_worker checkpoints call cProfile.dump_stats every10s.
Installed dump_stats->create_stats->disable disables the profiler on first dump,
never reenables. Dummy-thread before/after test reproduced it. Every target .prof
including SUCCESS(.165,5.5125) records only~10s initial _row/_sectors with0
retained eighe calls. Full computation BOTTLENECK_NOT_LOCALIZED. Exp/sqrt
startup hotspots cannot identify60min eighe/LU/matrix costs. No collector fix
implemented; observability changes require separate approval, math stays frozen.

Failed sources:
A(.165,5.49375)1799.031wall/1733.859375aggregateJobCPU, SAFETY_ABORT raw
PROCESS_FAILURE/Job125,15.578s gap/lastAC0, not numerical timeout. AP childPID/
separate exit unknown; historical outer probe-wrapperPID24332 only.
B(.16375,5.5)3595.75wall/3469.96875CPU, internal3592s AP timeout,
wrapperexit0; AC/Sleep history/start-stop/childPID not retained.
C(.16531250000000003,5.5)3595wall/3516.90625CPU, internalAP timeout/
Job124,AC1/no recordedgap/Sleeprestored; exact start-stop/childPID unknown.
CPU/wallB~.965/C~.978 consistent with active expensive work, NOT numerical
progress proof. No RSS/commit time series/AP precision rows or full profile.
No finalC,w for failures. Do not infer OOM/suspension/physical singularity.

Baseline unchanged147 sources/3822 saved objectives/AO catalogmaximum26/26.
Reference21.9393102292(.165,5.5),K.07798099387393764;
22km(.165,5.475),K.07661740491526092. No newsource/K/AO call this diagnostic.
Current reference pairs: P1(.165,5.49375)/(.165,5.50625 binary64
5.5062499999999996); P2(.16375,5.5)/(.16531250000000003,5.5).
Missing_source_priority.csv ranks9 actual requests/hex/crossdistance usefulness.
Original fixed-best radii.0125/.0025 require14/12 paired halvings to1e-6,
conditional only. Inner4 cap insufficient current one-call brackets; checks
tolerance on next entry, not afterfourth stage. Six outer steps do not guarantee
24 refinements due stagnation/earlier-unresolved latch. Prepopulating original
requested exact points then fresh originalAO replay could avoid that cap per
invocation, but not authorized now; do NOT change settings/caps/stopping logic.

Proposed Plan A (recommended first): after separate observer/safety approval and
fresh compute authorization, (.165,5.49375) then only if still original request
(.165,5.50625),60min ceilings, suggested130min total incl10minreserve. Prior
lowerVA failure safety-related, not demonstrated numerical timeout; actual
runtime/K unknown. Reassess selectedpair/dependencies after every successful
original26-distance evaluation and originalAO only when newly authorized.
Plan B: only ifVA5.5 still selected, uppernu.16531250000000003 first for stronger
retained power telemetry, then conditional lowernu.16375. Bothprior60mintimeout,
bounded120min per source recommendation is conditional investigation not
completion promise; one source130min total or two250min incl10minreserve.
No currentAP budget or automaticretry. Existing probe_worker intercepts inner
worker timeout to per_probe_timeout-8s; uninstrumented gram_moments still has
3600s inner limit, so changing only outertimeout on wrongpath won'textend AP.
Any actual operational observer change needs approval and dummy validation.

Partial AP resume unsupported/unproven: .prof is timing only, worker emits
allrows onlyatend, finalsource writes atomicallyaftervalidation. Existing caches
resume BETWEENsources, never insideeighe/LU/mpmath state. Approved failedsource
must restartoriginalbinary64inputs. No speculative checkpoint machinery added.

Current36 scoped regression tests PASS (3newdummy/key/cap tests +33existing),
gitdiffcheckPASS,1340 protected scientific/priorartifact hashes unchanged.
Producer wall20.609s diagnostic only; all tests dummy/saved/provenance, no AP.
NoPython workers remain. Originalscientific source/settings/preregistered
precision1050/1250/1450/GH8/MI/directZminus/Holevo/AO all unchanged.
Diagnostic producer scripts/diagnose_theta10_D55_source_bottlenecks.py SHA
da3c88aa20bf8241a6d0a526fa4099fd8d3b7d42931e4d0cd8262b05a7a3eb1e;
diagnostic_report.json SHA
7e686428be9f321565ada31a542a2198ed02f8373b1edf4869d30cfb531e3580.
Fail-on-existing-output prevents overwriting this diagnostic by rerun.
Ponytail: stdlib pstats/cProfile plus original provenance helper, no scientific
driver imported/no dependency installed/no operational fix withoutapproval.

Accuracy still ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; source convergence
tolerances and bit-exact repeats do not bound fullK error for1e-8/tinyrankgaps.
nu=0/domain/unboundedouter/multistart dependencies stillopen, no coordinate/
continuous/global certificate. Frozen historicalhashdiscrepancy unchanged,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. No training/finaltest/baseline/threshold/
lifecycle promotion. Phase2A originalbudgetEXPIRED and its3attemptscopefinished.
Next turn should read diagnostic report/plans and wait for explicit new scope/
budget, NEVER interpret continue alone as approval forAP/fixes/retries.
