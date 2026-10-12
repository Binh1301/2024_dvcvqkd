# Approved upper P1 run stopped at native safety preflight:AP NOT_RUN

Terminal status STOPPED_PREFLIGHT_FAILURE_NO_AP. User approved exactly(.165,5.50625), one attempt/120min total/90min supervisor/30min reserve/original60min evaluator unchanged/no retry/P2. The controller was launched ONCE, origin2026-10-10T07:31:20.756551Z, then stopped after16.172s before source invocation. No source_attempt_started.json, source_result.json or new cache payload exists. AP attempts0, successful new sources0, AP timeouts0. This is NOT a numerical-source failure or evaluator timeout.

## Native failure and cleanup

Fresh AC/Sleep verification succeeds. Same-entry root+child dummy Job reaches its test deadline: returncode124,9.000s wall inside12s ceiling,2.578125s aggregate CPU,6 accounted processes, no watcher gap/AC error, no watchdog thread remaining. However the immediate post-supervision native process-handle assertion reports `Dummy tree escaped`. As required, the controller stops; no automatic preflight/controller/AP retry occurred and no remaining budget is reused.

Recorded dummy root22384, child24616, controller23760 are absent at subsequent native checks; all scoped scientific/controller processes are absent. Outer and nested Sleep leases have verified restoration, no power-plan change.1825 protected hashes are unchanged. Original failed producer/receipts/ledger/authorization remain intact.

The assertion text alone does NOT establish persistent Job escape. The new entry checks root/child handles immediately after the supervisor returns. The earlier successful B2_A entry sleeps0.2s before its analogous assertion. The original bounded_process waits for its directly spawned process/launcher and closes a KILL_ON_JOB_CLOSE Job, but does not explicitly wait for every descendant handle to become signaled. An asynchronous descendant teardown race is a plausible cause; there is no per-PID event timeline proving it. Do not relabel this nativeFAIL as nativePASS based only on later absence.

A focused future repair would use a bounded, deadline-aware wait for recorded descendant termination within the existing cleanup allowance, then fail closed if any remains. This is not an observer/profiler project. No runtime source/supervisor/failed producer was edited or rerun after the failure; repair/relaunch requires further direction because the user explicitly ordered STOP on a safety failure.

## Scientific answers

1.149-source catalog remains reconciled:147baseline+PREEXISTING(.25,2)+previous newB2_A(.165,5.49375), not a new150-source catalog.
2.Upper(.165,5.50625) remains an original stage1 dependency (second call); lower(.165,5.496875) is the first missing call.
3.No exact source computed in this run:AP0, safety gate stopped before invocation.
4.C,w for upper NOT_AVAILABLE; do not reuse lower neighbor moments or fabricate values.
5.No new upper SKR, no measured improvement; reference stored best remains(.165,5.5),K.07798099387393764.22km(.165,5.475),K.07661740491526092 unchanged.
6.Current bestVA5.5, not a newly verified continuous optimum.
7.P1 bracket unchanged[5.49375,5.5125], width.01875 (serialized.018749999999999822), radiusabout.0125.
8.No additional exact neighbor or completed paired refinement level; scientific progress0 in this stopped run.
9.P1 not complete; source-missing/refinement and outer directions remain unresolved.
10.No fresh AO recheck executed. Existing149-source selected maximum26/26 is revalidated by regression tests, not a new run or convergence claim.
11.No new evaluation at any distance; no other-distance gain can be claimed.
12.Upper(.165,5.50625) is still scientifically necessary under the approved scheduling plan, alongside lower(.165,5.496875). Source/keydbb7a2a7024f84f97c455b0b3b564e9a307f369b362f80e055dfbf1e5d49497f remains absent. P2(.16375,5.5)/(.16531250000000003,5.5) remain missing and were NOT_RUN. Resolve/validate native cleanup gate before any new AP execution; no automatic scheduling/retry/P2.
13.Reliable numerical optimum still needs genuine P1/P2 refinement/termination, source+MI+Holevo/K discrimination and boundary/multistart evidence. Finite-catalog scope only; no global/continuous/numerical-convergence promotion. Scientific formulas/defaults/AP method/precision/quadrature/model unchanged; frozen historical discrepancy/NOT_READY lifecycle unchanged.

## Runtime and evidence

Controller16.172s wall/6.3125s CPU; dummyJob9s wall/2.578125s CPU; sourceAP runtime NOT_RUN. Their measured combinedCPU8.890625s excludes setup/tests/reporting/tooling. Full scoped52-test regression PASS9.550s (module/artifact checks), native gate FAIL, post-abort cleanup PASS; these are distinct statuses. All old artifacts/ObjectiveA/source cache preserved. See final_report.json, dummy_supervision.json, execution_ledger.csv and abort_verification.json.

STOP. No AP retry, controller retry, other source, timeout override or P2 execution.
