# Observer v2 code audit

Active entry: scripts/observer_v2_recovery_entry.py -> overnight_source_observer_v2.run_observed
-> original full_support_c4_worker.main. Recovery CLI exercises original JSON/input/precision-loop/output
entry with dummy row/Gram/eigen/LU leaves, not a SimpleNamespace-only substitute.
No source-moment arithmetic is performed. All fake row values are quarantined in dummy/ and NEVER
enter source/objective caches. Production --approved-ap remains NOT_RUN and requires fresh probeA
authority, exacthex/cachekey/request hash, unexpired deadlines and native Job containment.

Active metadata accesses worker.mp.mp.dps (mpmath module context), not module.dps. Static active
invalid count0. Historical executed observer v1 retains3 invalid accesses; the old overnight
controller still routesv1 and MUST NOT be reused. These immutable forensic paths are preserved,
not described as globally fixed. v2 imports StageObserver fromv1 module but never callsv1.main.

CheckedStageObserver separates metadata/startup/persistence/shutdown exceptions as
INSTRUMENTATION_FAILURE; original numerical operation exceptions are NUMERICAL_FAILURE.
Supervision takes precedence for TIMEOUT/AC_SAFETY_ABORT/WATCHDOG_ABORT. Unknown process failures
are conservatively instrumentation failures, never inferred mathematical impossibility.
Observer disabled path calls same original main once without hooks/profile; dummy results/calls
equal enabled path. No scientific code changed. Future controlled parent MUST consume worker_result
status before the historical generic probe_worker classifier; no string-timeout heuristics.

Ready status: READY_FOR_CONTROLLED_AP_PILOT, limited to this prepared entry and controlled pilot, not old controller/AP proof.
