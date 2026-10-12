# Session Handoff

## Current: Phase2A FINISHED; no active worker or compute authorization

2026-10-09 EVID-0149/DEC-0132 supersede earlier running/preparation/stop notes.
Controller22548/session90612 exited0; original6380/session54545 exited1.
All Python/source/AO/profile workers gone, Windows Jobs closed, Sleep request
restored to original2147483648. No permanent power-plan change.

Original approval max10800s total including setup/stops/idle/processing/cleanup,
max3600s per probe, max3 sequential attempts,480s reserve, no failed-source retry.
Origin11:46:13.577171Z/monotonic126545.75; absolute deadline14:46:13.577171Z/
monotonic137345.75 never reset. Execution/verification/cleanup finished
by14:34:25Z with total10090.781s wall. Later usercontinue/read-only saved
artifact review and documentation occurred after expiry. No scientific
evaluation/tests/AP launched after deadline; do not claim whole late turn
was inside3h. Approval exhausted. Do NOT rerun or launch further computation.

Output results/theta10_D55_ao_numerical_optimum_validation/phase_2A/.
Authoritative phase_2A_report.json, execution_ledger.csv, source_generation_ledger.json,
objective_checkpoint.json, postprocess_report.json and phase_2A_final_conclusions.md.
Completion audit completion_read_only_verification.json binds saved final hashes.
selected_exact_probes.csv is preserved preparation metadata, not final status;
earlier safety_stop_audit and checkpoint_before_AC_resume/ are historical.
Running handoff preserved as running_handoff_before_completion.md.

Probe1(.165,5.49375), key
db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59:
SAFETY_ABORT/rawPROCESS_FAILURE/Job125,1799.031s wall/1733.859375 JobCPU.
15.578s monitoring gap/lastAC0. Actual suspend versus scheduler delay unknown.
NoC,w and never retried.
Probe2(.165,5.5125), key
6d4fda6bc30868ae691f2b091bddfc0fdd1e8b00373c2c7581a1aa964596a92a:
COMPLETED_EXACT, C3.2176328023710283,w1.0391362032418032e-6,
2723.047s wall/2651.296875 JobCPU, source payload/provenance verified.
Probe3(.16531250000000003,5.5), key
166137fde3766af677d0741fa2457da169a9f4ecfc38f53197856835a01a26e0:
TIMEOUT,3595s wall/3516.90625 JobCPU (3600s ceiling/5s cleanup margin),
noC,w, never retried. Excluded(.16375,5.5) Phase2B not run.

Catalog146->147/3822 saved objectives (26 new rows), independent maxima
UNCHANGED at26/26, actual original AO129 starts/283 iterations/618 searches
matches catalog26/26. Reference21.9393102292(.165,5.5),K.07798099387393764;
22km(.165,5.475),K.07661740491526092. New source2 Kreference
.07798086747835642/K22 .07661627881168132, not a new optimum.
No interpolated C,w/SKR, no point copied into an AO history to force agreement.

P1reference fixednu.165 bracket[5.4875,5.525]->[5.4875,5.5125],
width.0375->.025/radius.025->.0125. One upper midpoint measured, zero
completed new paired stages/coordinate closures. Current missing
VA5.49375(prior safety abort)/5.50625(binary64 5.5062499999999996).
P2fixedVA5.5 unchanged[.1625,.16562500000000002], missing lowernu.16375
(prior60min timeout) and uppernu.16531250000000003(this Phase2A timeout).
55 unique missing pairs,312 boundary-open/306 bracket-source-blocked searches.
At22km P1 still missing(.165,5.4625)/(.165,5.481249999999999); P2
singletonnu.165 atVA5.475, outer(.0825,5.475) missing, opposite.33 unchecked.
Hard(.16375,5.5) still needed for current referenceP2 paired step but insufficient
for numerical optimum; other missing moments/error/boundary checks also remain.
Any Phase2B/retry/additional AP needs explicit fresh authorization; a possible
120min hard-probe ceiling is provisional, not a runtime prediction.

nu0=.8 at both priority distances stopsUNRESOLVED_BOUNDARY at(.4,3.0),
3iterations; lastP1missing(.4,1.5),P2missing(.2,3.0). Kref
.06912585821984563/K22 .06797982114890355. Not proof of a separate
continuous attraction basin.4/5 starts reach each finite-catalog winner.

32 final tests PASS beforedeadline; separate resume contract passed before
resume (not in32). Four original evaluator repeats20/ref/22/40 bit-exact.
1243 protected hash matches; regression evidence final_regression_tests.json,
independent_catalog_verification.csv, original_evaluator_reproducibility.csv.
Recorded CPU8088.203125s includes8074.546875 JobCPU+13.65625 controllers;
independent setup/audit/test CPU outside Jobs not fully captured.
Raw finalreport SHA4065cd9dfd894fab78c57238f589a65680d7bdadf8f237a8431f3caaf66f6b80,
new26 CSVf493def3faedd210f39f8475eb222e6b9c6161d385ce64a0c9f2db178604b9a6,
optimized26 CSV479c355013fb3662f5d9cf9ff4440012c8657f973ac83a24bd4329d9e242a189.

Eight300dpiPNG/vectorPDF pairs generated beforedeadline. Resume renderer
numeric CSVfloat decoding fixed categorical axes without changing math/CSV.
skr_vs_distance_positive_only.png/pdf base10log,K>0 display only,Uniform25km,
bothMB40km; all78 signed comparison CSV rows retained. No abs/clipping/zero/
fit/interpolated crossing. Distance and referenceP1 plots visually inspected.
Standalone render_theta10_D55_phase2a_verified_figures.py NOT_RUN/unnecessary.
Do not rerender now under expired budget.

Executed producers immutable:
run_theta10_D55_ao_phase2a.py SHA
51c0ee8bdf9702a47cf3eceebd59bee778597c2db93635dd763c6f26dbfa4863;
continue_theta10_D55_ao_phase2a_after_ac.py SHA
de20c01f84e3d61c00ee888755b24d1526c303a20a6864dd3cb39db66751af51.
Original AP1050/1250/1450,GH8/directZminus,MI/Holevo/AO all unchanged;
AOeps1e-8,param1e-6,outer6,inner4,boundary3. Ponytail guided reuse of existing
routines/supervisor instead of changing scientific algorithms.

Authoritative current science checkpoint is phase_2A/objective_checkpoint.json,
NOT older batch_3's146 checkpoint. Five original source banks:
exact_mb_test2,theta10_D55_alt_opt_closure_continuation,
targeted_expansion/resumed_sleep_safe_run,batch_2,batch_3/exact_source_cache;
phase_2A/exact_source_cache supplies the one valid new source.
Preserve all older outputs, preparation/stop/resume snapshots and failed receipts.

Classification ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no total K enclosure,
continuous numerical convergence/global certificate. Strictnu>0 vs mathematical
nu>=0 gap remains; stored Uniform comparison not continuous boundary closure.
No model/security/source/precision/quadrature/AO/training/test-access/baseline/
threshold approval change. Frozen historical hash mismatch PREEXISTING_UNCHANGED,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. This approved3-attempt phase is finished;
the broader trustworthy numerical-optimum goal remains unresolved.
