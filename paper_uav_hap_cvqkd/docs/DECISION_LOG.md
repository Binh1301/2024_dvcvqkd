# Decision Log

## Corrected full fading 2026-10-17: new explicit model, no optimization

Attachment f5f45a58 authorizes actual code correction: Mode B uses circular
aperture integration, Mode A is comparison-only; both explicitly retain current
active-conditioning/passive-support convention and AoA atom. New corrected CLI
uses full fading noise and ideal heterodyne with interval Holevo. Historical
explicit model CLI and no-fading diagnostics remain distinct. Numerical tests
pass but do not resolve optical calibration, security proof, frozen historical
hash or requested (38)(7) absence. STOP after report; no pointing/MB optimization.

## Task2 optical gate 2026-10-17: stop before inconsistent SKR search

User attachment explicitly requires validated pointing before search and no
continuation with inconsistent transmittance. Aperture reference differs by
8.38672x in mean pointing collection. Preserve old source/config/results;
do not silently substitute a new joint fading law. Task2 remains incomplete,
pending Task1 evaluator/provenance and consistent bounded-transmission law.

## DEC-0162 - Add only a separate manuscript reproduction mode; STOP after tests

2026-10-12 explicit attachment aae63626-108b-440d-9b21-ec9a8b92595f plus
user-supplied (37).pdf authorize literal three-moment backend and lightweight
unit/regression tests only. Use eta_f=E[sqrt(eta)], literal total noise and
selected T=eta_f/xi=xi_f mapping; preserve existing discrete-QAM MI and exact
source normalization/caches. Do not change frozen spec, historical evaluator,
AP/AO, previous results or Objective C. Keep model-specific outputs/identifiers.
Accept EVID-0179 implementation checks, NOT normalization/security readiness:
reference PDF mass .9841200272202841 fails normalization and is not repaired.
G_d and discrete-MI source gaps remain disclosed; no physical substitutions.
STOP now; sweep/catalog evaluation/optimization/new AP/publication require
fresh authority. NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains.


## DEC-0161 - User stop supersedes remaining Objective C execution authority

2026-10-11 explicit "dung": STOP entirecontroller/workertree now. AcceptEVID0178,
retaincatalog182 and five initialcacheAO runs; AP1partialsourceinvalid,Stage2NOT_RUN.
Do not reuse remaining36hbudget for any AP/optimizer/restart. Freshuserresume
direction required; never automatically retry interruptedpoint. No sciencechange.


## DEC-0160 - Authorize Objective C sequential adaptive original ALT_OPT

2026-10-11 userattachment86b46cab-e98a-4f86-8fbf-f327238b7c60: Stage1reference
five paired starts,thenStage2all26. Fresh36h/maximum36AP,Stage1up12/Stage2remaining
(24plusunusedStage1),reserve1800s,originalinternal3600s,sequential,no retry.
Exact requests from originalAO,skipfailedmissingkeys/reusevalidsources;eachnewsource
26originalSKRs. AC/Sleep/watchdog/Jobempty/provenance failclosed unchanged.
Preserveoldresults/science;no manuscript/publication/modelchange. Supplementary
userconvergence assessment doesnot changeoriginalstop rule or prove globaloptimum.
Missingmoments/openboundaries/nu0 exclusion/totalerror unavailable stayexplicit.
Accept EVID-0177 readiness.


## DEC-0159 - Execute only explicitly requested grid timeout retry

2026-10-11. User says "chay lai not cai time out" after closed full31batch.
Authorize ONE new attempt for(.25,3.5), not automatic retry of the whole batch.
Retain original internal3600s timeout/precision/scientific defaults; reuse existing
AC/Sleep/watchdog/Job actualtreecleanup. Conservative operational caps7200s total,
3720s sourceouter includingcleanup,1800s finalreserve, no extension beyond previous
absolute deadline. Separate directory; preserve all earlier reports/CSV/cache.
On success validateCw/evaluate26originalSKRs/comparewith181catalog and save expanded
checkpoint; on timeout/safetyfailure STOP, no further retry/otherAP/AO. No continuous
optimum, publication or model-level authorization follows. Accept EVID-0176 readiness.

## DEC-0158 - Approve only fixed31-source sequential batch

Date: 2026-10-10. Accept EVID-0175. Current user attachment7723d6dd-dbdb-413c-ad2d-03cf9990e614
supersedes prior cache-only STOP for this narrow task: B12 then A19,maximum31
distinct attempts,36h wall deadline including final processing,1800s reserve,
original3600s evaluator timeout unchanged. No retry,parallel AP,additional
points,AO refinement,interpolation,scientific changes or publication promotion.
Timeout may continue only after verified actual Job cleanup and safe AC;
mandatory safety/provenance failure stops entire batch. Preserve prior results.


## DEC-0157 - Accept incomplete exact-data grid;propose coverage-only next batch,not AP

Date: 2026-10-10

Status: TWO_LEVEL_GRID_CACHE_ONLY_COMPLETE_STOP

Accept EVID-0174. Fixed51-pair specification remains20evaluated/31missing;
do not substitute nearbyparameters,fill matrices/interpolate,or narrowcatalog
comparison togridonly. Preserve131off-grid sources andseparate8reference near
points. PriorityA/B identifiescoverage roles,notpredictedSKR;Crefinementdeferred.
Proposeonly(.15,3.5),(.165,6.) asminimal complementary nextbatch;freshuser
authority/budget/runtime safety required before execution. Historicalruntime
scenario is uncertain/biased,not uniformtiming or guaranteedcompletion.
NoAP/Cw/SKR/AO/scientificdefault change/lifecyclepromotion;deliverCSV/figures/
all51coverage/missinglist andSTOP. Finitecatalogranking remainsuncertified.

## DEC-0156 - Deliver all151 evaluated points;relative near-optimality is finite-catalog only

Date: 2026-10-10

Status: FULL_CATALOG_CACHE_ONLY_EXPORT_COMPLETE_STOP

Accept EVID-0173. List every validated point,including negativeSKR;classify
relative loss using eachdistance's ownbest. YES means<=1e-5 fraction=0.001%,
not a totalnumerical-errorbound or continuous-optimum guarantee. Preserve
NUMERICALLY_UNCERTIFIED ranking,prior151-source scientific results/brackets/
method/defaults/lifecycle. NoAP/Cw/SKR/AO or furtherrefinement authority.
Deliver complete151terminaltable,all9nearpoints/counts/deviations/3926CSV
andreport;STOP without additional computation.

## DEC-0155 - Accept cache-only landscape analysis; no optimization authority

Date: 2026-10-10

Status: CACHE_ONLY_ANALYSIS_COMPLETE_STOP

Accept EVID-0172. Interpret151-pair numerical ranking and9/5/2/2/1 near-point
counts as literal stored-objective observations only. Closest competitor differs
only inVA; sparse/anisotropic discrete coverage is not a continuous plateau or
global/numerically certified optimum. No totalK errorbound resolves the smallest
gap; preserve NUMERICALLY_UNCERTIFIED and BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY.
All saved science preserved; do not rerunAP/Cw/SKR/AO or change method/defaults.
No refinement progress/coordinate closure or lifecycle promotion in this task.
Deliver actualTop20,26-distance comparison and exactCSV/report;STOP.

## DEC-0154 - Accept valid ONE lower P1 source, report original refinement and STOP

Date: 2026-10-10

Status: SINGLE_APPROVED_LOWER_ATTEMPT_COMPLETE_BUDGET_CLOSED

Accept EVID-0171. Exact source valid/original26 SKR and cache-onlyAO complete,
catalog151/max26of26/no incumbentgain. Lowerprobe computed K is smaller by
3.6726688357191506e-10,not a rigorously discriminated ordering without total-K
errorbound. OriginalP1 bracket25%narrower,zero additional completedpairedlevels/
coordinateclosures. Next FIRST(.165,5.4984375),SECOND(.165,5.503125); record only,
do not execute either or P2/retry or reuse remaining approvedbudget. Conditional
13levels/14visits estimate does not authorize changing cap4/tolerances/algorithm.
Actual Jobs/Sleep/watchdog cleanup verified, oldscience/rootpreflight preserved.
No scientific method/default/model/lifecycle promotion; STOP after this attempt.

## DEC-0153 - Execute freshly approved ONE lower P1 and stop after result/timeout

Date: 2026-10-10

Status: ONE_LOWER_P1_EXPLICITLY_APPROVED_AND_STARTED

User confirms DEC-0152's pending authority ONLY for(.165,5.496875),120total/
90outer/original60internal/30reserve,ONE/no retry/otherP1/P2. Accept EVID-0170
prelaunch readiness; same source/controller/nativeJob safety path reused without
dummy gate or method/default change. On valid source evaluate26 saved channels,
original P1/cache-only multi-start/warm AO and independent catalog comparison.
Record true bracket/requests/conditional estimates, not forced closure/global
optimum. On timeout/safety failure stop safely. No additional AP or budget reuse.

## DEC-0152 - Complete lower P1 preflight; require the requested fresh AP confirmation

Date: 2026-10-10

Status: PREFLIGHT_COMPLETE_ONE_LOWER_AP_PENDING_FRESH_CONFIRMATION

Accept EVID-0169. Attached task scopes ONE lower(.165,5.496875) but explicitly
conditions AP on fresh execution authorization. Confirm this once after scientific
preflight; do not reuse completed upper budget or silently infer confirmation.
Proposed120min total/90min outer/original60min internal/30min reserve, no retry/
secondpair/P2. Original minimal Job/AC/Sleep/watchdog/actualcleanup path retained,
no dummy/observer/profiler diagnostics. No source/SKR/fullAO generated during
preflight. Live original requests and incumbent verified, not assumed optimal.
Conditional13levels estimate does not authorize changing cap4/tolerances or a
convergence/global claim. Preserve existing code/results/ObjectiveA and STOP
before AP until confirmation; after valid approved source use original26-distance
SKR/P1/cache-onlyAO, then STOP after the single attempt.

## DEC-0151 - Accept completed ONE upper P1 result; stop, no further AP/P2

Date: 2026-10-10

Status: APPROVED_SINGLE_ATTEMPT_COMPLETED_BUDGET_CLOSED

Accept EVID-0168. New source valid, original26-distance evaluation and genuine
cache-onlyAO complete within fresh budget. Incumbents unchanged, catalog150/
26of26 matches do not certify continuous/global optimum or totalK discrimination.
P1 exact-neighbor bracket one-third narrower, zero additional completed paired
levels/coordinate searches; next actual request(.165,5.496875),then(.165,5.503125).
Record these only, do not execute them/P2 or reuse remaining120min budget.
Preserve exact cache/checkpoints/raw receipts/oldscience. Actual native Jobempty/
Sleep/watchdog cleanup verified. No numerical method/default/evaluator/AO/model
change, optional Windows diagnostic redesign, forced gain or lifecycle promotion.
Return scientific results and STOP after this single attempt as user required.

## DEC-0150 - Execute ONE freshly approved upper P1; stop after result or timeout

Date: 2026-10-10

Status: ONE_UPPER_P1_ATTEMPT_APPROVED_AND_STARTED

User's fresh approval supersedes DEC-0149 AP-not-authorized state ONLY for
(.165,5.50625). Total120min/outer90min/internal60min unchanged/reserve30min,
no retry/other probes/P2. Use validated current entry without dummy gate;
original AC/Sleep/watchdog/Job containment/actual-tree cleanup required.
Accept EVID-0167 prelaunch evidence. On valid moments evaluate26 original saved
channels/SKR and unchanged cache-only AO, independently compare catalog and
report true bracket/missing requests. On timeout or safety failure stop safely;
no evaluator/default/formula redesign, unknown-moment interpolation or promotion
of finite-catalog agreement to numerical/global convergence. STOP after attempt.

## DEC-0149 - Remove optional dummy gate; retain fail-closed actual worker cleanup

Date: 2026-10-10

Status: APPROVED_SCOPED_INFRASTRUCTURE_REMOVAL_ONLY_AP_NOT_RUN

Current user explicitly authorizes removal of redundant diagnostics, not AP.
Accept EVID-0166: remove embedded prelaunch dummy harness/PID gate from active
upper P1 entry, retain original Job/AC/Sleep/deadline/internal60min safeguards
and verify actual Job empty within existing wall allowance. Do not bypass a
genuine cleanup failure. Preserve byte-identical historical failed producers
and all scientific artifacts; no observer/profiler/heartbeat redesign or model/
precision/evaluator/AO change. No automatic AP/retry/P2 or old-budget reuse.
Next(.165,5.50625) is technically ready conditional on fresh execution approval
and runtime safeguards; paired lower5.496875 also missing. No numerical optimum
or coordinate closure/lifecycle promotion. Return to scientific Objective B.

## DEC-0148 - Stop approved upper run on native failure;no automatic retry

Date: 2026-10-10

Status: STOPPED_NATIVE_PREFLIGHT_FAILED_AP_NOT_RUN

Accept EVID-0165. User's explicit STOP-on-safety-failure controls: do not restart
dummy/controller or invoke AP even though APcount0 and budget remains. Preserve
failed producer bytes/receipts. Eventual no-worker/Sleep cleanup PASS does not
retroactively certify original native gate. A teardown timing race is plausible,
not proved; require focused bounded cleanup verification/further direction before
any retry/new AP, no broad instrumentation development. No scientific change,
source generation, new numerical-optimality/physical/global claim or extra P2.

## DEC-0147 - Fresh approval for ONE original upper P1 source attempt

Date: 2026-10-10

Status: ONE_UPPER_ATTEMPT_APPROVED; NATIVE_PREFLIGHT_MUST_PASS

New explicit user approval supersedes DEC-0146's pending permission ONLY for
raw(.165,5.50625), one new attempt/no retry/otherAP/P2. Total120min fromcontroller
origin including imports/preflight/processing/cleanup, supervisor<=90min shortened
to preserve>=30min reserve. Original fallback timeout60min UNCHANGED; supervisor
never extends it. Keep all source/science/precision/quadrature/AO/defaults; use
minimal original worker+existing stableAC/Sleep/Job deadline/tree supervisor.
Fail closed at native gate. On source success only, original26-distance objective/
cache-only AO and genuine bracket/catalog recheck allowed. Stop after attempt
and validation; no extra candidates from unused time, global/continuous/accuracy
promotion, cap16 or observer development. Old results/ObjectiveA preserved.

## DEC-0146 - Confirm original upper P1 dependency; require fresh AP approval

Date: 2026-10-10

Status: SCIENTIFIC_PREFLIGHT_COMPLETE; ONE_UPPER_SOURCE_PROPOSAL_ONLY

Accept EVID-0163 reconciliation/live original paired requests. User's proposed
upper(.165,5.50625) is the actual second stage1 dependency and may be separately
scheduled without changing AO request order. Do not replace it with the lower
request or execute either without fresh approval. Current attached120/90/30min
budget is explicitly proposed/conditional, not a continuation of closed B2_A.
Request ONE fresh upper attempt; preserve internal3600s timeout/scientific APIs.
An outer90min budget cannot extend that internal cap; any execution-policy
timeout change needs separate explicit authority. No AP now, no retry/other source/
P2/cap16/profiler/observer work, no publication/model/security promotion.
After actual fresh approval, repeat native AC/Sleep/Job containment/deadline/
cleanup checks for the execution entry; then compute only approved source and
original26-distance/AO results if valid. Reconstruct actual next requests after
new data, do not guarantee gain/paired completion. Old artifacts unchanged.

## DEC-0145 - Close B2 after one exact success and cache-only I/O recovery

Date: 2026-10-10

Status: ONE_APPROVED_SOURCE_COMPLETE; FINITE_CATALOG_ONLY; STOP_NO_MORE_AP

Accept EVID-0162: original source(.165,5.49375) succeeds; recovered original
26-distance evaluator/AO on149 pairs matches maximum26/26, no selected gain,
one P1 lower-neighbor advance/0 closures. Preserve original JSON metadata failure
and raw broad abort receipt; not AP timeout or unsafe power abort. Separate
cache-only storage repair keeps +Infinity radius metadata, rejects nonfinite
scientific values, leaves all original producer/science/default hashes unchanged,
and stays within SAME75min deadline. No duplicated AP or model change.

All workers stopped/Sleep restored. Keep old artifacts/ObjectiveA/unchanged plots.
No remaining budget authorizes more AP, retry, cap16, observer development or
publication-scale task. Next actual P1(.165,5.496875) requires separate fresh
approval; upperP1/P2 requests conditional/unapproved. No continuous/numerically
converged/global claim or totalK accuracy certificate. Historical frozen discrepancy
and lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## DEC-0144 - Authorize exactly one original-API B2 attempt under fresh75min budget

Date: 2026-10-10

Status: ONE_ATTEMPT_APPROVED_PREFLIGHT_PASSED_RUNNING

User "chạy" accepts B1's specific proposal. This supersedes DEC-0143's waiting
restriction only for exactly(.165,5.49375), total4500s including imports/preflight/
processing/cleanup, source<=3600s with900s reserve and no retry/additional AP.
Use original unprofiled source API plus existing AC/Sleep/Job supervision; native
preflight passes EVID-0161. No original formula/precision/quadrature/default/cap/
search changes or observer/profiler development. Valid source permits original
26-distance evaluation/multistart/warm AO and independent finite-catalog check;
otherwise stop after timeout/failure/unsafe abort and retain baseline. Exactness
of formulas or new moments does not imply totalK accuracy or global convergence.

## DEC-0143 - Complete Objective B1 only; request one bounded original-method B2 pilot

Date: 2026-10-10

Status: B1_COMPLETE; B2_FRESH_BUDGET_REQUIRED

New user scope supersedes ObjectiveA STOP only for B1 preparation; continue does
not authorize AP. Accept EVID-0160's original cache-only coordinate reconstruction,
one additional reference check using preexisting source and focused14-answer plan.
Maintain original147-source26-distance curve, explicitly distinguish148-source
reference-only inventory/check; no new optimality promotion or sweep before P1/P2
progress. Request ONE(.165,5.49375)75min total/60min source/15min reserve, shortened
by actual remaining time, only after fresh approval and minimal native readiness.
No profiler/observer controller, timeout/AC retry or later3 AP included. All model/
AP policy/AO defaults fixed; proposedJ16 refinement-budget experiment requires
separate scope and is not part of pilot. WholeK accuracy/multi-start/domain/boundary/
inner completion limitations remain; preserve ObjectiveA. Stop at B1 approval request.

## DEC-0142 - Deliver Objective A writing package, not verified full-paper build

Date: 2026-10-10

Status: OBJECTIVE_A_STANDALONE_PACKAGE_COMPLETE; COMPILATION_NOT_VERIFIED

Accept EVID-0159's scientifically qualified joint section/Algorithm1/stopping
evidence/tables/figures/Overleaf ZIP. Preserve the available article template
and prior files. Since the full-paper master is unavailable, do not claim it
has been integrated or its numbering verified; wrapper offset2 is preview only.
Require an actual external build to validate macro/package/layout/reference
behavior. No compiled manuscript PDF exists and no Overleaf remote build was
performed. Describe6/1e-8 as conservative safeguards, not accuracy/continuous
convergence/global-optimum guarantees; document positive-nu AO versus sampled
Uniform endpoint. No scientific/default/domain/code change or lifecycle/security
promotion. STOP after this Objective A package; Objective B and further AP/AO/
observer work remain unauthorized in this task.

## DEC-0141 - Stopping sensitivity supports safeguards, not convergence certification

Date: 2026-10-10

Status: CACHE_ONLY_SENSITIVITY_COMPLETE; NO_NEW_AP_AUTHORITY

Accept EVID-0158's sixteen temporary original-AO replays and manuscript assets.
The new user authorization supersedes the prior no-AO-rerun restriction only
for cache-only Rmax/epsilon sensitivity. Original algorithm/science/baseline
configuration and inner caps remain unchanged. Larger caps and1e-9 do not improve
any selected or individual terminal solution; all starts still request missing
sources and0/9856 calls close. Rmax6 is not an active cap bottleneck and even4
reproduces this incomplete replay. Eps1e-6 saves4 cycles with unchanged solutions;
this does not establish an optimal production threshold or certified SKR error.
Keep baseline6/1e-8 unchanged, describe as computational safeguards with observed
finite-catalog invariance, not guaranteed numerical convergence. Classification:
BASELINE_PARAMETERS_ONLY_COMPUTATIONAL_SAFEGUARDS. No AP/observer repair/retry,
publication-scale lifecycle promotion or new source-run authority follows.

## DEC-0140 - Accept focused best-found AO manuscript deliverables, not convergence certification

Date: 2026-10-10

Status: SCIENTIFIC_DELIVERABLES_COMPLETE_FROM_SAVED_DATA_NO_AP_AUTHORITY

Accept EVID-0157's Algorithm1/manuscript/table/genuinehistories/figures and
independent147-source ranking.26/26selectedmax agreement is finitecatalog
evidence, not universalstartstability:59/129individualmatches,0unanimousdistances,
0closedcoordinatecalls. Flat histories must remain stagnation/openboundary;
theoreticalnu0endpoint/limits/wholeKerror/remotedomain remainunresolved.
Manuscript-ready formatting does not promote publication-scale lifecycle or
securityclaims. Freezeoriginalscience/AO/settings;nonewAP/observerengineering,
no implicit execution from targeted-probe planning. LocalLaTeXcompile unavailable;
Overleafentryprovided without fabricatedcompilePASS. Future exact scientific
probes require separately approved scope/budget andexistingminimal safe
supervision, not recently failingobserverroute. No methodology change authorized.

## DEC-0139 - Stop after heartbeat-loss A; no further AP in consumed scope

Date: 2026-10-10

Status: ONE_ATTEMPT_CONSUMED_STOPPED_NO_RETRY_NOT_READY_FOR_FURTHER_AP

Accept EVID-0156 stopped/fulltree/Sleep cleanup and preserved partial AP evidence.
Longpath overflow fixed for this run, not proof of complete telemetry reliability.
Actual snapshot publication failed after31valid records; persistedtemp32 and
read-held dummy contention support a replacement-race hypothesis only, since
production exception/holder unrecorded. Do not claim source numerical failure,
full profiling, identified fullrunbottleneck, newSKR gain or AO convergence.
Do not retry/continueanotherAP with unused150min budget or alter executed
producers. Future separately authorized preparation should stress real concurrent
readers/atomic publication and durable typederror/heartbeat reporting on the
same shortproduction paths without science/context/precision/AO changes.
Baseline147/3822/saved26matches/P1P2/0closures remain. No lifecycle/global/
continuousoptimum/threshold/training/finaltest or model promotion.

## DEC-0138 - Execute separately approved path-fixed A after actual production gates PASS

Date: 2026-10-10

Status: ACTIVE_BOUNDED_SINGLE_A_ATTEMPT_NO_RETRY

Accept EVID-0155's actual path operations/production wrapper dummy/native safety/
provenance/regression evidence for this new bounded pilot only. User explicitly
authorizes path repair and conditional automatic A; pending gate superseded,
but old failedattempt/budget/controller never resumed. Same persistent150min
origin, prep45/AP75/finalreserve30, one attempt only. Stage path mapping affects
instrumentation only; original cache identities, source/numerical/evaluator/AO
algorithms/settings remain frozen. No global registry/permanent power change.
On AC/observer/watchdog/Job/deadline failure kill fulltree and stop AP; no retry/
other source. On validCw use original26objectives/cache-onlymultistart/warmAO,
independent maxima/P1P2/coverage checks. Stage/profile/finitecatalog evidence
must not be promoted to full-run profiling/continuous convergence/global optimum.
Final reports/provenance/verified archive/cleanup before originaldeadline.

## DEC-0137 - Accept stopped controlled-A attempt; require path-safe evidence before any new attempt

Date: 2026-10-10

Status: ONE_APPROVED_ATTEMPT_CONSUMED_STOPPED_NO_RETRY

Fresh user90min/A75min/reserve15min authority superseded the pending gate for
one guarded observer-v2 A attempt only. EVID-0154 records production startup
path persistence failure, safe shutdown, unchanged science/catalog and no valid
new source. Do not retry using remaining90min budget, run B/P2, reset output,
or route to overnight-v1. No numerical/source-bottleneck conclusion from this
operational error. DummyREADY/49 unit regressions do not certify production
path persistence or full AP coverage. Saved26/26 is unchanged baseline evidence,
not fresh AO convergence. Zero new refinement/closed searches.

Before any future separately approved AP attempt: validate actual Windows
path lengths for initial/periodic/final snapshot, heartbeat, typed sidecar,
profiler and exact cache, including failure reporting when sidecar itself
cannot persist. Prefer scoped path handling/staging over machine-wide changes;
do not alter registry, evaluator, precision, quadrature, MI/security or AO.
No repair/new AP authority is inferred here. Preserve executed producers and
all prior results; no continuous/global optimality or lifecycle promotion.

## DEC-0136 - Accept observer recovery readiness; stop before controlled AP pilot

Date: 2026-10-10

Status: READY_FOR_CONTROLLED_AP_PILOT_NOT_EXECUTION_APPROVAL

Accept EVID-0153's activev2 integration/context/profile/typedfailure/native safety/
provenance evidence. DummyREADY is not proof of actual longAP behavior, scientific
convergence or publication readiness. Original scientific/evaluator/AO settings
remain unchanged; preserve failedv1/oldcontroller/old artifacts rather than silently
repairing their historical hashes. New prepared entry only; NEVER oldv1redirect.
No AP/sourceA retry/B/P2 authorized; oldovernight budget not reused. Propose fresh
90min total with sourceA<=75min and15min reserve,1 attempt, after explicit user
approval. Parent controller must use guarded v2 entry and typed result sidecar,
original Job/AC/Sleep, absolute deadlines/provenance/noorphan; shorten AP for
remainingreserve. Stop safely on any failure, no automatic retries or numerical
method/cap changes. Report finitecatalog/errorunbounded/domain limitations.

## DEC-0135 - Stop overnight AP on observability failure; preserve and report actual defect

Date: 2026-10-09

Status: STOPPED_PRODUCTION_OBSERVER_FAILED; NO_AUTOMATIC_RETRY_OR_CONTINUATION

Accept EVID-0152's actual instrumentation AttributeError, not a mathematical
source failure/timeout/AC safety-abort. User expressly requires cache-only failure
report if profiler validation/repair fails; therefore no retryA or launchB/C/D
after discovering this defect. Preserve executedv1/failed receipt/raw reports,
dummy-test versioned observer correction only. v2's dummy PASS is not actual
AP equivalence/full-run coverage. Do not infer a completed75min attempt, new
moments, betterK, numerical/global convergence or source bottleneck location.
Scope now cache-only handoff complete, no activeworker/Sleep request. Future
production must explicitly adopt corrected integration and authorize exact scope/
retry; do not reset28800s deadline or reuse failed controller/old ledger silently.
Scientific/AO/precision/settings and lifecycle/frozen-hash limitations unchanged.

## DEC-0134 - Execute bounded overnight scope after verified observer/safety preflight

Date: 2026-10-09

Status: EXPLICITLY_APPROVED_OVERNIGHT_TARGETED_EXECUTION

EVID-0151 and the user's new attachment supersede DEC-0133's pending gate only
for this run. Authorize A(.165,5.49375)75min; B(.165,5.50625)60min only after
A success and actual activeP1 request; C(.16531250000000003,5.5)120min;
D(.16375,5.5)120min only if still required with remaining reserve. Maximum4
attempts once each, no substitute pairs/automatic retries. Absolute deadline
23:44:48.165007Z with900s reserve, including repair; no reset/resume on unsafe
AC/gap/containment/provenance. Safe Job/Sleep/provenance before every AP.
Instrumentation wrappers/timeouts only repaired, original scientific functions/
precision/AO settings/provenance exact. Use stage coverage honestly, not first10s
as whole-run profiling. Each valid source original26-distance objectives and
genuine original cache-only AO/independent ranking; implicit AP forbidden.
Do not assume gain/closure/error bounds or promote numerical/global/lifecycle
claims. Stop safely without asking intermediate approval if authority insufficient.

## DEC-0133 - Accept cache-only bottleneck diagnosis; stop before fixes or AP

Date: 2026-10-09

Status: DIAGNOSTIC_COMPLETE; CONTINUATION_PLANS_PROPOSED_NOT_AUTHORIZED

Accept EVID-0150's profiler-observability defect and explicit full-stage unknown.
Do not attribute timeouts to eighe/condition/resource failure from a10s startup
profile, or relabel A as numerical timeout. Keep original scientific evaluator/
precision/provenance/MI/Holevo/AO untouched. No fix to collector/supervisor/
checkpoint or settings implemented without separate user approval.
Recommend Plan A as the first cost-controlled coordinate step after approval
for minimal observation and fresh probe budget; Plan B remains conditional.
Original paired source requests, numerical accuracy/boundaries/multistart
evidence govern progress, not catalog size. Fourteen/twelve halving arithmetic
is conditional, not a guarantee; cap/latch limits do not authorize algorithm
changes. Resume incomplete sources only by explicitly approved original-input
restart, never unproven partial numerical state. All AP/plans NOT_RUN this task.
No numerical/global/lifecycle promotion, old Phase2A budget remains expired.

## DEC-0132 - Close Phase2A execution authority; retain finite-catalog-only results

Date: 2026-10-09

Status: COMPLETED_APPROVED_ATTEMPT_SCOPE; BUDGET_EXPIRED; NUMERICAL_OPTIMUM_UNRESOLVED

Accept EVID-0149's actual1 success/1 timeout/1 safety-abort,147-candidate
catalog, unchanged maxima and genuine AO agreement26/26. One-sided P1 bracket
progress is not completed paired refinement or convergence. P2 and boundary/
accuracy dependencies remain open; no global or continuous-optimum claim.
Hard(.16375,5.5) is still needed for the current reference P2 lower side, but
not sufficient to resolve all optimum blockers. Phase2B or any retry/additional
AP needs separate explicit scope and fresh runtime authorization. Do not infer
authority from later continue or reuse/reset the expired Phase2A budget.
Preserve failed receipts, preparation/stop snapshots and original science.
All numerical processing/cleanup finished within the original deadline;
later documentation/read-only verification does not imply a new compute budget.
No frozen model, evaluator, precision, quadrature, MI/Holevo, AO settings,
training/test/baseline/threshold or lifecycle promotion. Existing frozen-hash
blocker and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain.

## DEC-0131 - Resume original Phase2A authority only after verified AC1

Date: 2026-10-09

Status: RESUMING_UNATTEMPTED_PROBES_WITH_ORIGINAL_DEADLINE

EVID-0148 verifiesACrestoration/usercontinue and retainedunexpired budget.
Resume onlyprobe2(.165,5.5125), then3(.16531250000000003,5.5) underoriginal
14:46:13Z deadline/480s reserve, no probe1/hardPhase2B/timeout/AC retry orreset.
Keep stoppedreceipts/producers/snapshots and allscientificsettings intact;
freshAC/Sleep/nativeJob provenance/cleanup gatesmandatory. CSVnumericcast is
renderer-only, not a new calculation. Report actualCw/SKR/AO/closures/gaps,
not assumedsuccess/convergence. No numerical/global/lifecycle authority change.

## DEC-0130 - Stop Phase2A on native unsafe gap/AC0; no aborted-source retry

Date: 2026-10-09

Status: STOPPED_BLOCKED_BY_ENVIRONMENT_AC_REQUIRED

Accept EVID-0147: nativeJob125 kills allprobe1 workers on15.578s monitoringgap
andAC0. No validC,w;0newobjective/source/AO/coordinate completion. Rawgeneric
PROCESS_FAILURE is interpreted as safetyabort, nottimeout or numericalfailure.
Keep actualreceipt and allpreparation/stop snapshots, original10800s deadline
and attemptedsource inventory. RestoreSleep and verify no workers, then stop
all computation on battery. Never retryabortedprobe1 automatically. StableAC
is needed before considering only unattemptedprobe2/3 within originalbudget;
no reset/extraAP/Phase2B. Further work after expiry needs freshauthority.
Report finitebaseline/errorunbounded scope, no fakeoptimization improvement.
No scientificalgorithm/settings or lifecycle authorization changed.

## DEC-0129 - Execute only newly approved Phase2A under single absolute budget

Date: 2026-10-09

Status: EXPLICITLY_APPROVED_PHASE2A_EXECUTION

User approval supersedes DEC-0128's pending gate for exactly3 ordered original
probes. EVID-0146/auth JSON bind10800s total/3600s source/max3 sequential with
480s processing reserve from new unreset origin. Native AC/Sleep/Job safety and
strict provenance must pass; terminate fulltree on failure. Timeout may advance
to next independent source if safe/time permit; no retry/Phase2B/extraAP.
Use unchanged scientific evaluator/settings/methods and genuine originalAO,
not a catalog-winner copy. Save all26 new objectives per valid source, original
histories/coordinates and independent maximum comparison. Preserve pending
snapshots/old artifacts. Catalog growth alone is not convergence; no lifecycle,
global, threshold, training or test-access promotion.

## DEC-0128 - Prepare three Phase2A dependencies; require new budget approval

Date: 2026-10-09

Status: STAGE1_COMPLETE_AWAITING_EXPLICIT_NEW_PHASE2A_AUTHORIZATION

Current Phase2 attachment supersedes Phase1's no-budget-request end-of-task rule
only by opening preparation/preflight and a new proposed budget confirmation.
EVID-0145 verifies original146 baseline and three specific missing midpoint
dependencies, native AC/Sleep/Job readiness/cleanup and protected artifacts.
Do not compute AP before fresh explicit approval. Proposed10800s/3600s/max3
serial includes processing/cleanup;480s reserve can shorten later deadlines.
After approval no intermediate approval pause is required; timeout continuation
only with remaining budget and safe power/provenance. No automatic retries,
model/settings/method changes, old budget reuse or Phase2B. Preserve lowernu
timeout dependency as excluded and reconsider necessity from actual Stage2
results before any separately approved hard probe. Pending tables/figures cannot
be presented as newly computed results. No numerical/global/lifecycle promotion.

## DEC-0127 - Accept Phase1 AO audit; stop before new AP

Date: 2026-10-09

Status: PHASE1_COMPLETE_STOP_BEFORE_NEW_AP; NO NUMERICAL/GLOBAL APPROVAL

Accept EVID-0144's independently verified146-catalog/26-distance data and real
AO histories. Algorithm P1/P2 indexing is consistent; inner returns are only
exact-tested approximate maximizers. Strictpositive nu differs from nu>=0 target;
do not silently change it.0 closed selected directions;4/5 start agreement at
priority distances is partial evidence, not continuous/global convergence.
Prepare manuscript Algorithm1 and diagnostic figures with incomplete status.
Prioritize actual reference dependencies, then22km, then gate other24; do not
run all55 missing sources for catalog growth. Four primary pairs complete at
most one paired step per selected coordinate, not full convergence. Prior timeout
and AC abort require separate decisions, never automatic retry. Keep original
epsilon/parameter/outer/inner caps; diagnose their limits without modifying them.
Total objective accuracy remains error-unbounded despite repeated ordering.
Preserve all old science/artifacts, baseline curves and binary64 keys. This task
authorizes cache-only Phase1 and ends here; no AP budget ask, reuse, or execution.
Any Phase2 needs separate explicit scope/fresh budget and original safety gates.
No lifecycle/model/security/threshold/training/test/baseline authority changed.

## DEC-0126 - Close Batch3 with146 finite candidates; retain incomplete directions

Date: 2026-10-09

Status: COMPLETE_WITH_POWER_ABORT_AND_BUDGET_SKIP; NO NUMERICAL/GLOBAL APPROVAL

Accept EVID-0143's1 valid new source/26 objectives,146 catalog and independently
verified26/26 original ALT_OPT matches.0 maximum gains atall26; source2 is new
runner-up at22/reference.0 closed directions,55 missing dependencies. Nu slice
atVA5.475 remains singleton. Tiny runner-up gaps and bit-exact repeats do not
establish total numerical accuracy/continuous convergence/global optimality.
Source1 stopped on AC loss, never retried; source3 skipped to preserve480s
processing/cleanup reserve under original deadline, not marked timeout.
Production computation and independent audit completed before deadline; final
narrative handoff after deadline is disclosed. Preserve all old snapshots,
raw moments/ledgers/histories; no worker/Sleep lease remains. Approval is closed,
not authority for extra AP; further coverage requires new explicit scope/budget.
Scientific formulas/precision/quadrature/MI/Holevo/ALT_OPT and lifecycle unchanged.

## DEC-0125 - Resume only unattempted Batch3 sources after live AC restoration

Date: 2026-10-09

Status: RESUMED_WITH_ORIGINAL_AUTHORIZATION_DEADLINE

EVID-0142 records liveAC1 and user's continue request. Resume approved source2,
then3 only if time/safety permits; never retry aborted source1 or timed-out
source. Origin07:56:11Z/deadline10:56:11Z unchanged. Max3600s probe,480s reserve
and no extra source during original cache-only129-start AO. Preserve prior
attempts and all stopped/resume snapshots; old protected producers unchanged.
Native preflight isolates wall deadline with live idle child to avoid treating
the earlier two-busy-process JobCPU guard as a wall-time assertion failure.
Original supervisor/CPU/safety guards and all scientific methods unchanged.
Report actual outcomes and any catalog/AO mismatch, not presumed completion/gain.

## DEC-0124 - Accept approved Batch3 scope; stop on verified AC loss

Date: 2026-10-09

Status: EXECUTION_STOPPED_BLOCKED_BY_ENVIRONMENT_AC_REQUIRED

Current explicit approval superseded DEC-0123's pending budget. Execute atmost3
specified sequential points, new10800s total/3600s source, no timeout retry.
EVID-0141 verifies actual native preflight and first source attempt, but AC0
caused Job125 termination after1952.719s. Enforce the user's safety-stop rule:
no probe2/3 on battery. Do not relabel power abort as timeout or numerical failure.
No source/objective completed; catalog145 and old maxima unchanged. All885
protected hashes/worker cleanup/Sleep restoration verified. Previous preflight
failures preserved and budget NOT reset (origin07:56:11Z, deadline10:56:11Z).
Current 'continue' triggers safe inspection, not permission to bypass AC.
Require stable AC before any further AP. Do not automatically rerun aborted
probe1 or erase prior attempts. Any authorized continuation must preserve the
original deadline and skip earlier attempts; once expired a new runtime scope
needs explicit approval. No scientific/lifecycle change or convergence claim.

## DEC-0123 - Finalize Batch3 points; require explicit new runtime approval

Date: 2026-10-09

Status: SELECTION_COMPLETE_AWAITING_EXPLICIT_BATCH3_BUDGET_APPROVAL

Current attachment opens Stage1 and proposes a new10800s/3600s/max3 sequential
execution, but explicitly requires separate user budget approval before AP.
EVID-0140 verifies the145 baseline and retains all3 original points. There is
no generated nu midpoint atVA5.475: only an outer half-value. Do not invent a
rounded local point or silently substitute the farouter(.0825,5.475).
Keep third(.16531250000000003,5.5) under the attachment's otherwise branch,
with explicit note it does not bracket the current22kmVA5.475 nu slice.
Stop before AP; request explicit budget confirmation. After confirmation run
sequentially using original evaluator and live AC/Sleep/Job preflight, preserve
prepared files, checkpoint each outcome, no timeout retry or budget overrun.
No source/scientific/provenance/optimization policy or lifecycle change.

## DEC-0122 - Accept cache-only145-catalog diagnostic; stop before Batch3 AP

Date: 2026-10-09

Status: DIAGNOSTIC/PLANNING COMPLETE; NEW AP NOT AUTHORIZED

Accept EVID-0139's145 compatible sources,3770 objectives,26/26 existing AO
matches and24 bit-exact unchanged-evaluator repeats. Accuracy classification is
ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; neither deterministic repetition nor
the final subtraction ULP scale certifies total numerical error or physical gain.
5.475 is the sampled22km VA maximum, not a continuous/global certificate;
itsnu slice is singleton and both outer directions are not closed.
Select exactly(.165,5.4625),(.165,5.4875),(.16531250000000003,5.5) for future
coverage, with exact original midpoint keys. These give complementary VA/nu
information, not guaranteed gain/convergence; all54 missing dependencies ranked.
Stop now. No new AP budget is requested or inferred, and old unused time is
not authorization. An expensive future expansion is conditional on a scientific
coverage objective and new explicit runtime/power approval. No formulas, source
method, precision, quadrature, ALT_OPT settings/multistarts or lifecycle changed.

## DEC-0121 - Close successful batch2; retain finite-catalog scope and open directions

Date: 2026-10-09

Status: COMPLETED DIAGNOSTIC COMPUTE; NO CONVERGENCE/GLOBAL OPTIMALITY APPROVAL

Accept EVID-0138's3/3 sources,0 timeouts,145 MB pairs,78 exact new objectives and
26/26 original cache-only AO/catalog matches. Only22km improves relative142,
at(.165,5.475),delta2.626161285101958e-07; do not compare only to obsolete139
or call tiny numeric gain scientifically significant without error bound.
Runner-up/neighbor coverage strengthens but no search closes:54 missing pairs,
312 open-boundary and306 bracket/missing calls among618 actually rerun.
No numeric/global convergence; selected4 stagnated/22 unresolved.
Actual wall6935.906s/CPU6744.1875s, deadline/power/lease cleanup PASS,0 workers,
796 protected hashes and32 scoped tests/diff PASS. Preserve all outputs/source
moment caches and old artifacts; do not consume leftover time for extra probes.
Further targeted ridge expansion could provide coverage only after new explicit
scope/runtime authorization; no guaranteed physical gain or global closure.
Scientific/numerical formulas/settings/AO and frozen model unchanged; no new
publication/training/test/baseline/threshold approval.

## DEC-0120 - Execute approved batch2 with exact identities and fresh wall limits

Date: 2026-10-09

Status: ACTIVE DIAGNOSTIC COMPUTE AUTHORIZATION

Current user approval supersedes DEC-0119's pending confirmation. Execute max3
unique points in stated order(.165,5.475),(.165,5.425000000000001),(.15,6.25),
new10800s total/max3600s each, serial. Reassess remaining need from measured
data after every valid source; retain original order absent demonstrated
redundancy. Continue after timeout if safe/in budget, never retry timeout.
Use EVID-0137's actual active AC/sleep guard and original Windows Job worker.
Reserve360s for final original cache-only AO and cleanup, never extend deadline.
Compare against142 exact baseline, not139; max145 unique MB sources. Preserve
preparation and prior batch bytes. No science/formula/precision/quadrature/MI/
Holevo/AO/provenance or lifecycle change; no forced matching or global convergence.

## DEC-0119 - Prepare adaptive batch2; confirm proposed fresh limits before AP

Date: 2026-10-09

Status: PREPARATION ONLY; NEW COMPUTE AUTHORIZATION PENDING

Accept EVID-0136's142 baseline, binary64 identities, cached local gaps and full
52-missing-pair inspection. First proposed source(.165,5.475) serves measured
ridge switch at21.939/22km. Correct proposed5.425 to actual original search
midpoint5.425000000000001 (1ULP), not a scientific or algorithm modification.
Keep(.15,6.25) provisional for20/21km coverage; reassess priorities2/3 after
valid exact results, rather than predict unknown K. Avoid known long timeouts.
Baseline22 reference remains.07661714229913241 from142, not the old139 curve.

The attachment explicitly describes a proposed fresh10800s/3600s/max3 serial
batch and execution once authorized. Ask for confirmation before expensive AP;
prior completed approval/leftover time is not reused. After approval recheck
AC/reacquire verified sleep prevention, use original Job/source evaluator,
checkpoint each outcome, evaluate only newly available26distance objectives
and run original cache-only AO. Continue independent probes after timeout only
within approved limits/safety; never retry automatically or force convergence.
No scientific/model/publication/training/test/baseline/threshold approval changed.

## DEC-0118 - Close the completed three-point campaign, retain unresolved scope

Date: 2026-10-09

Status: COMPLETED DIAGNOSTIC EXECUTION; NO CONTINUOUS/GLOBAL CONVERGENCE APPROVAL

Accept EVID-0135: three valid sources, zero timeout,142 finite MB candidates,
78 exact26distance objectives and original129-start cache-only AO. AO matches
catalog maximum26/26; only22km has a small numerical increase at(.165,5.45).
Do not elevate finite numeric ordering to meaningful physical gain without a
total objective error bound. No coordinate search completed:52 missing pairs
and open boundaries remain; selected4 stagnated/22 unresolved, no convergence.
Actual wall7732.75s within10800s, all per-probe deadlines pass; temporary sleep
request restored and no workers remain. Preserve all old results and the new
source/checkpoint/catalog artifacts. Authorization is complete after these
three specified probes; unused time does not authorize other points or retries.
Any later exact-source expansion needs a new explicit scope/runtime decision.
Scientific methods/settings, model, publication/training/test/baseline/threshold
approvals unchanged; frozen-spec discrepancy remains recorded.

## DEC-0117 - Fresh approval executes all three probes, including after timeout

Date: 2026-10-09

Status: ACTIVE DIAGNOSTIC COMPUTE AUTHORIZATION

The user's current explicit approval supersedes DEC-0116's pending-budget and
stop-after-timeout conditions for this NEW execution only. Run ordered pairs
(.16562500000000002,5.5),(.165,5.45),(.165,5.525) sequentially with10800s total
and3600s maximum per probe. Continue automatically after timeout; never retry
a timed-out point within this run. Stop for unsafe power/provenance/numerical
failure or exhausted total budget. Keep original science and preserve history.
Accept EVID-0134's live AC/active temporary lease before original worker start.
Reserve360s for final26distance original cache-only AO and cleanup; no extension
of total budget. Expanded catalog remains a finite exact-tested ranking, not
continuous convergence. No publication/training/test/threshold approval changes.

## DEC-0116 - Temporary sleep/AC guard accepted; new AP budget still pending

Date: 2026-10-09

Status: OPERATIONAL PREFLIGHT ONLY; NO AP BUDGET CONFIRMATION

User requests transient thread-scoped automatic-sleep prevention and native
power checks without changing power plans or scientific calculations. Accept
EVID-0133's temporary request/release, Job timeout/cleanup and simulated-power
abort evidence. Operational wrapper does not amend source methods, precision,
quadrature, AO or lifecycle. Recheck AC and verify/reacquire the request before
any future AP; unexpected suspend still cannot be treated as wall-time PASS.
The proposed NEW10800s total/3600s per probe requires explicit confirmation;
do not reuse prior expired approvals. Stop after preflight. Candidate order
remains(.16562500000000002,5.5),(.165,5.45),(.165,5.525); exclude(.16375,5.5).
After fresh approval, use original evaluator sequentially and stop/report on
timeout or unsafe power rather than automatically launching another probe.

## DEC-0115 - Stop after sleep-related deadline failure; no further AP

Date: 2026-10-09

Status: WALL-BUDGET COMPLIANCE FAILED; CONTINUATION NOT AUTHORIZED

Accept EVID-0132's raw timeout/CPU/wall evidence and confirmed Windows battery
sleep/hibernate/resume events. Do not classify the10800s/3600s real-time budget
as PASS merely because CPU use was1771s. The polling supervisor terminated
after recovery rather than at the real-time deadline. Preserve original ledgers,
profiling artifacts and separate compliance audit. No C,w completed; SKR/AO and
probes2/3 remain NOT_RUN. All workers stopped; MB count unchanged139.
Treat this wall-time session as exhausted and stop. A new attempt needs fresh
explicit runtime authorization plus separately agreed stable-power/no-suspend
conditions. Do not alter source formulas, precision/quadrature or AO, invent
moments, silently reuse CPU-based remaining budget or infer ensemble invalidity.
No power settings, scientific or lifecycle approvals were changed here.

## DEC-0114 - New three-hour budget; probe1 result before continuation

Date: 2026-10-08

Status: ACTIVE USER AUTHORIZATION; NO NUMERICAL/MODEL/LIFECYCLE CHANGE

User grants maximum10800s total and3600s per exact-source probe for the new
targeted pilot. This is separate from the exhausted old14400s session.
Execute only (.16562500000000002,5.5) first with unchanged original exact
method and corrected supervisor. Validate/checkpoint/time and, if successful,
evaluate26 exact objectives and affected cache-only AO searches. Report the
result before deciding probe2. Do not automatically continue on timeout or
invalidity; no probe2/3 is launched by the current one-probe driver.
Preserve all old artifacts. No cap/tolerance/precision/quadrature/formula
change, manufactured convergence, publication or test access is authorized.

## DEC-0113 - Prepare targeted three-candidate pilot; require fresh budget

Date: 2026-10-08

Status: PLANNING ONLY; NO NEW AP EXECUTION BUDGET APPROVED

User requests targeted near-ridge expansion subject to a separately approved
computational budget. EVID-0130 accepts the three actual midpoint candidates
(.16562500000000002,5.5), (.165,5.45), (.165,5.525) as a pilot plan, not fixed
optima or required successes. Defer the prior3600s timeout (.16375,5.5) rather
than automatically repeating it; retain its unresolved dependency.
The old four-hour authorization remains exhausted. Do not start AP/SKR/AO
expansion until fresh total/per-probe hard runtime is explicitly supplied.
After authorization, start one serial probe and review validated result, actual
timing and newly enabled objective evidence before another. Mathematical and
numerical methods, all AO settings and lifecycle remain frozen. No assurance
of three completions, improved SKR, continuous convergence or global optimality.

## DEC-0112 - Accept explicit finite-set maxima; defer further AP

Date: 2026-10-08

Status: FINITE-CATALOG DIAGNOSTIC DISPOSITION; NO CONTINUOUS/LIFECYCLE PROMOTION

Accept EVID-0129's exhaustive 136-reference-pair and 139-current-MB-pair
comparisons at 26 distances, with 168-all-source set explicitly distinguished.
ALT_OPT attains these finite-set numerical maxima; it is not continuously
converged or globally certified. The 4-step cap is a prospective ceiling, not
the observed blocker: missing sources/open boundaries stop earlier. Do not
raise it, relax epsilon/tolerance or compute further AP from this decision.

Do not spend another AP batch merely to reproduce the catalog maximum. If
continuous-coordinate closure is scientifically necessary, first authorize a
prospective coverage/closure plan and separate hard compute budget, retaining
all original methods unless a separately approved change is explicitly made.
Use scope-limited finite-catalog manuscript wording only; publication/numerical
security certification and frozen-spec provenance gates remain open. Prior
top-three source proposals remain unexecuted planning, not compute permission.

## DEC-0111 - Preserve cache-only diagnosis; three probes remain planning only

Date: 2026-10-08

Status: DIAGNOSTIC COMPLETE; NO AP AUTHORIZATION OR LIFECYCLE PROMOTION

Accept EVID-0128's verified cache consumption, unchanged five-distance replay,
source dependency ranking and conditional refinement-depth assessment. No
scientific or optimizer fault is established, so do not modify the frozen
algorithm, caps, epsilon, source identity, mathematics or numerical method.
Do not interpret 3 source completions or zero delta K as coordinate closure.
Prioritize (.16562500000000002,5.5), (.16375,5.5), (.165,5.45) only after
explicit approval and separately supplied total/per-probe hard runtime limits.
The old 4-hour budget remains exhausted. Three successful probes would not
guarantee convergence; unchanged four-stage searches and earlier/multistart
coverage need independent resolution. Keep the other 21 distances LAST_KNOWN.
Do not conflate local numerical blockers with the missing analytic certificate
for the unbounded global domain. Publication status remains unchanged.

## DEC-0110 - Preserve partial closure evidence after hard-budget completion

Date: 2026-10-08

Status: ACTIVE DIAGNOSTIC DISPOSITION; NO CONVERGENCE OR LIFECYCLE PROMOTION

Accept EVID-0127's 3 exact sources (2 original missing keys plus one adaptive
midpoint), measured timings and unchanged five-distance candidate results.
Do not turn source availability, a smaller local bracket, zero delta K or
unchanged parameters into numerical convergence. Zero identical-slice
coordinate/boundary invocations closed; all 26 global claims remain unproved.

Stop after the authorized 4-hour budget; all source workers are stopped.
Preserve original 165-row cache, overlay 3 rows, objective checkpoints,
timeouts and executed producer snapshot. The other 21 values are LAST_KNOWN,
not a fresh full-grid optimization. Require separate explicit authorization
and adequate runtime for further AP work. Do not silently retry failed keys,
resume an exhausted budget, accelerate, change precision, raise iteration
caps or invent a tail bound. Operational duplicate-owner/budget guards are
accepted without mathematical changes. Publication state remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0109 - Budget-bound exact-source closure continuation

Date: 2026-10-08

Status: ACTIVE DIAGNOSTIC EXECUTION AUTHORIZATION; NO MATHEMATICAL CHANGE

The user authorizes continuation using the unchanged original evaluator,
with total hard budget 14400s, maximum 3600s per probe and batch size 1.
This is a new budget, not reuse/extension of the earlier exhausted pilot.
Deduplicate exact ensembles, prioritize the five stagnated distances and
shared competitive dependencies, save each batch before continuing, and
reuse only provenance-compatible source/objective checkpoints.

Keep epsilon_opt=1e-8, parameter tolerance=1e-6, outer cap=6 and the original
coordinate-update/search, quadrature and precision policies. Operational
resume, atomic ledgers and native Job CPU accounting are permitted; no
source-method acceleration, approximation, new bounds or forced convergence
label is permitted. Verify source rows and representatives before updating
the remaining 21 distances. A timeout is not an invalid ensemble/low SKR.

Evidence: EVID-0126, missing_source_dependency_map.csv,
unresolved_search_inventory.csv and source_generation_ledger.json in
results/theta10_D55_alt_opt_closure_continuation/. No publication or frozen
spec promotion, baseline selection, threshold approval or final-test access.

## DEC-0108 - Accept strict exact-tested reproducibility without closure promotion

Date: 2026-10-08

Status: ACTIVE DIAGNOSTIC DECISION; NO SCIENTIFIC/POLICY CHANGE

The explicit user request authorizes a cache-only reproducibility rerun at
all 26 distances even though the separately gated source-completion workflow
has not closed representative directions. This authorization does not permit
AP generation, acceleration, evaluator changes, continuous convergence or
publication promotion. Existing corrected provenance/stopping and numerical
methods were frozen unchanged.

Accept EVID-0125 as successful reproduction of the exact-tested ALT_OPT sweep:
26/26 six-field exact matches and all six diagnostic totals unchanged.
Retain 5 STAGNATED_IN_EXACT_CATALOG and 21 UNRESOLVED_BOUNDARY statuses, not
CONVERGED_NUMERICALLY. Keep original aggregate statuses and historical reports
separately. Future source completion still requires its own explicit budget
and authorization; the 165-row source cache must remain protected.

Evidence: results/theta10_D55_alt_opt_26distance_strict_rerun/run_report.json,
previous_vs_rerun_comparison.csv, input_manifest_before.json/after.json and
post_run_checks.txt. No model, training/test access, baseline selection,
threshold approval or publication lifecycle changed.

## DEC-0107 - Explicit canonical provenance and conservative ALT_OPT stopping

Date: 2026-10-08

Status: ACTIVE DIAGNOSTIC DECISION; NO LIFECYCLE PROMOTION

Accept EVID-0124's newline-only canonical verification policy. Preserve all
historical raw hashes and source files; only proven current-byte/LF/CRLF
equivalence is compatible. Scientific code, settings or unknown identity
changes invalidate reuse. Objective compatibility is distinct from source
compatibility and includes scientific code/configuration/channel identity.

Retain epsilon_opt=1e-8 and the six-iteration default. Neither an unchanged
pair nor a bracket over a sparse catalog is sufficient for numerical
convergence. Both final-coordinate searches and stopping prerequisites must
pass; local numerical closure does not certify an unbounded global optimum.

Preserve the bounded pilot's timeout and measured budget overrun honestly.
The repaired process supervisor does not retroactively make the initial
timeout meet its budget. No source moment was added, so representative closure
remains unresolved and the remaining 21-distance optimization is NOT_RUN.
The publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

Evidence: EVID-0124 and
`results/theta10_D55_alt_opt_convergence_validation/validation_report.json`.

## DEC-0106 - Retain full-distance ALT_OPT as unresolved diagnostic

Date: 2026-10-07

Status: ACTIVE DIAGNOSTIC DECISION; BLOCKED_BY_ENVIRONMENT; NO LIFECYCLE PROMOTION

Accept EVID-0122 as the full-distance continuation of the validated theta10/D55
ALT_OPT diagnostic. It preserves the physical/security model and exact direct-
`Z_minus` evaluator, uses cache-only exact source moments, and writes a new
distance table and figure. Uniform and fixed-MB rows were not reevaluated; the
existing source CSV and source cache were hash-checked unchanged. The selected
optimized-MB row reproduces the prior pair and SKR at all 26 distances.

Do not call these rows converged or global optima. Missing exact source moments
leave inner and outer boundary directions unresolved at every distance, and
multi-start terminal pairs remain initialization-dependent. If closure is
authorized later, run the existing source worker in an environment that can
complete the missing exact probes, explicitly supplying `--allow-new-source`,
while preserving this cache-only diagnostic and its hashes.

The separate renderer is accepted as a positive-only display: standard base-10
log scale, Uniform through 25 km only, and both MB curves through 40 km. No
zero line or interpolation is used. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0122
- `results/theta10_D55_alt_opt_distance_sweep/run_report.json`
- `results/theta10_D55_alt_opt_distance_sweep/mb_alt_opt_distance_summary.csv`
- `results/theta10_D55_alt_opt_distance_sweep/skr_vs_distance_three_scheme_log10_report.json`

## DEC-0105 - Retain ALT_OPT as blocked diagnostic; no optimum promotion

Date: 2026-10-07

Status: ACTIVE DIAGNOSTIC DECISION; `BLOCKED_BY_ENVIRONMENT`; NO LIFECYCLE PROMOTION

Accept the new optimization-layer implementation as a separate diagnostic
driver only. It reuses the existing exact direct-`Z_minus` evaluator and
source moments, adds adaptive `V_A|nu` and `nu|V_A` searches, context-bound
exact caching, multi-start logs, monotonicity checks, and convergence/
trajectory artifacts. It does not alter the physical model or the previous
joint-search artifacts.

The cache-only validation found the best exact-tested pair `.165,5.5` at the
theta10/D55 baseline distance, but exact source coverage did not close all
adaptive midpoint/outer probes. The open-source fallback was stopped after a
single probe remained CPU-bound for about 23 minutes; no source cache row was
added. Therefore the result must remain `BEST_AO_EXACT_TESTED_CANDIDATE_ONLY`
and must not be called a converged AO solution, stationary/global optimum, or
publication baseline.

### Evidence

- EVID-0121
- `results/theta10_D55_alt_opt/ao_report.json`
- `results/theta10_D55_alt_opt/ao_summary.csv`
- `results/theta10_D55_alt_opt/ao_iterations.csv`

## DEC-0104 - Accept theta10/D55 unconstrained exact diagnostic with fixed-pair caveat

Date: 2026-10-07

Status: ACTIVE DIAGNOSTIC DECISION; NO LIFECYCLE PROMOTION; STRICT FIXED-BINARY64 SOURCE UNRESOLVED

Accept EVID-0120 as a separate exact-tested adaptive diagnostic. It removes
the peak-photon and common-VA constraints only in the new runtime experiment,
keeps the physical/security parameters and direct-`Z_minus` evaluator fixed,
and does not overwrite the constrained D55 artifacts.

The result retains the exact Uniform sign bracket `25 km` positive to `25.5
km` non-positive. Both MB curves are positive through 40 km. The optimized MB
ridge moves toward higher VA at short distance and then declines with distance;
the exact VA=8 upper probes, nu=.05 lower probes, and nu=.8 upper probes are
below the selected envelope. This is an exact-tested adaptive envelope, not a
continuous optimum proof over all positive VA and nu.

The requested fixed decimal `V_A=1.3833230303` source calculation timed out
in the existing AP fallback. The accepted diagnostic fixed curve uses the
existing exact hash-matched binary64 row `1.3833230302980657`, equal at the
reported ten-decimal precision, with no moment interpolation. A strict rerun
at the requested binary64 value requires a source-worker environment that
completes the fallback.

Do not promote this run to a publication baseline, continuous global optimum,
or final-test/publication evidence. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0120
- `results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/run_report.json`
- `results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/skr_vs_distance_three_scheme.csv`

## DEC-0103 - Accept theta10/D55 three-scheme diagnostic

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO LIFECYCLE PROMOTION

Accept EVID-0119. The D55 exact comparison confirms optimized Uniform is
positive through 25 km and becomes non-positive at 25.5 km, while both fixed
and optimized MB remain positive through 40 km. The optimized MB advantage is
quantified in the exact table and is generally beta-I_AB driven; fixed MB at
20 km is the exception where lower chi_BE dominates.

Retain the linear three-curve figure as diagnostic-only. No obsolete evaluator,
VA<=1.5 artificial budget, C,w interpolation, or channel reuse was used. Do not
select D55 as a baseline or call 40 km a maximum operating distance.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0119
- `results/skr_vs_distance_theta10urad_D55cm_three_scheme/skr_vs_distance_three_scheme_report.json`
- `results/skr_vs_distance_theta10urad_D55cm_three_scheme/skr_vs_distance_three_scheme.png`

## DEC-0102 - Accept transition frontier; stop before MB

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO OPTICAL CANDIDATE SELECTED

Accept EVID-0118. The transition search establishes a physical tradeoff:
increasing divergence from 15 to 20 urad raises the required receiver diameter
for Uniform positivity from approximately `.553 m`/`.643 m` (20/25 km) to
`.655 m`/`.767 m`. At 25 urad the 25-km threshold is above `.75 m` and no
positive point appears below `.80 m`; 30--50 urad have no positive 20-km point
below `.80 m`.

The common exact boundary `T_eff≈.089827455` persists. The four refined
candidates are positive only through 20 or 25 km and all fail at 30 km. Do not
run MB, extend the optical domain, or force a 30--40-km crossing from this
result. Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0118
- `results/transition_theta_dr_frontier/transition_pareto_frontier.csv`
- `results/transition_theta_dr_frontier/transition_refined_summary.csv`

## DEC-0101 - Retain no-solution result in primary theta/D_r domain

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO OPTICAL CANDIDATE SELECTED

Accept EVID-0117. All 90 primary ((theta_{
m div},D_r)) pairs are already
non-positive at 20 km. Therefore no candidate satisfies the requested
30--40-km Uniform crossing target, and no category-C/D design exists in the
declared physically reasonable domain.

Retain the Pareto-like negative alternatives in the coarse summary, but do not
extend the domain, run MB, refine locally, or manufacture a crossing. The
result supports the conclusion that the useful old positive curve requires a
design outside this primary divergence range and/or the previously identified
large-aperture/narrow-divergence regime. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0117
- `results/joint_theta_dr_optical_search/uniform_coarse_summary.csv`
- `results/joint_theta_dr_optical_search/joint_theta_dr_uniform_report.json`

## DEC-0100 - Accept cache-bound receiver-aperture diagnostic

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; CONTINUOUS VA THRESHOLD UNRESOLVED

Accept EVID-0116. With the current theta10 physical/security model unchanged,
the exact-cache Uniform threshold brackets are approximately `0.491811 m` at
20 km, `0.512472 m` at 22 km, and `0.544644 m` at 25 km. The first tested
positive sweep diameter is `.50 m` at 20 km and `.55 m` at 22/25 km. The
`D_r=.55 m` sanity rows agree in sign with the recovered old positive-Uniform
artifact.

Interpret these as exact-channel bisection brackets over the 11 available
Uniform VA source rows only. Do not call them continuous-VA thresholds while
the missing requested source moments remain unresolved. The result supports
receiver aperture, rather than divergence or security-evaluator changes, as
the dominant explanation for the old positive curve, subject to this cache
scope.

No model/security change, parameter search, baseline selection, publication
figure, training, or final-test access is authorized. Publication lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0116
- `results/theta10_receiver_aperture_uniform_diagnostic/theta10_receiver_aperture_uniform_report.json`
- `results/theta10_receiver_aperture_uniform_diagnostic/threshold_bisection_exact.csv`

## DEC-0099 - Accept positive-Uniform provenance classification

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO BASELINE PROMOTION

Accept EVID-0115. The positive-Uniform figure is reproduced from the old
physical baseline with the current exact direct-`Z_minus` evaluator. The old
baseline recomputes distance-dependent geometry and uses `w0=0.10 m`,
`D_r=0.55 m`, `tau_zen=.92`, `epsilon=.0186`, beta `.95`, AO/phase OFF, and a
common `V_A<=1.5` sparse exact envelope. Uniform positivity ends at the exact
25/26-km bracket; MB's 800/810-km bracket is a low-rate diagnostic.

The 10-point short-distance reproduction has maximum absolute SKR difference
`0.0`. VA `.08,.10,.12,.13,.15` on the old physical channel is negative at
20/22/25/30 km, so `V_A=.1` is not the source of the old positive curve. The
dominant change to the current negative result is the old optical baseline,
especially the much larger receiver aperture; no superseded security evaluator
was identified.

Do not select the old baseline, change the current model, search new
parameters, or redraw the figure until a separate physical-baseline decision
is authorized. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0115
- `results/positive_uniform_provenance_audit/positive_uniform_provenance_audit.json`
- `results/positive_uniform_provenance_audit/direct_reproduction_comparison.csv`

## DEC-0098 - Accept Uniform VA diagnostic; retain continuous optimum unresolved

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO BASELINE OR LIFECYCLE PROMOTION

Accept EVID-0114 as the exact Uniform variance diagnostic for the frozen
theta10urad/D10cm channel. The old `V_A=1.075` curve is confirmed as a fixed
reference-bank row; direct exact comparison shows `V_A=0.1` is less negative
at all six requested distances. The expanded exact bank finds `V_A=0.12`
best through 31 km and `V_A=0.13` best from 31.5--40 km, with all 23
selected SKRs still negative.

Classify the requested historical value as
`VA=0.1 NEAR-OPTIMAL WITHIN NUMERICAL TOLERANCE`: it is not the strict
best exact-tested row, but the maximum exact envelope improvement is only
`1.220287529912716e-8` bits/use versus the frozen `1e-6` absolute SKR
tolerance. Keep the continuous optimum unresolved because 13 requested VA
source moments remain missing; do not interpolate or promote the envelope to
a continuous optimum.

Do not change the physical/security model, rerun MB, select a baseline, or
redraw the final publication figure. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0114
- `results/uniform_va_optimization_theta10_D10cm/uniform_va_verification_summary.json`
- `results/uniform_va_optimization_theta10_D10cm/uniform_va_selected_by_distance.csv`

## DEC-0097 - Do not select divergence without a valid Uniform crossing

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO THETA SELECTED

Accept EVID-0113. The tested divergence interval and expanded probes contain
no physically evaluated candidate with Uniform positive at 30 km and
non-positive by 40 km. Do not force the requested visual behavior by changing
another parameter, selecting a bad Uniform VA, or discarding valid rows.

No final sensitivity-selected baseline is authorized by this result. Preserve
the theta10 distance rerun separately; publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0113
- `results/skr_vs_distance_theta_sensitivity_D10cm/theta_sensitivity_report.json`

## DEC-0096 - Accept theta10urad distance diagnostic

Date: 2026-10-02

Status: ACTIVE DIAGNOSTIC DECISION; NO LIFECYCLE PROMOTION

Accept EVID-0112 as the recomputed narrow-divergence distance diagnostic. It
uses the frozen model/direct-Z-minus path and exact bank, with three displayed
curves: Uniform, fixed MB, and MB optimized. It does not alter the physical
model, select a baseline, authorize training, or authorize final-test access.

Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0112
- `results/skr_vs_distance_theta10urad_D10cm/skr_vs_distance_report.json`
- `results/skr_vs_distance_theta10urad_D10cm/validation.json`

## DEC-0095 - Resolve redesigned numerical lifecycle status

Date: 2026-10-01

Status: ACTIVE RESOLVED NUMERICAL EXPERIMENT; PUBLICATION LIFECYCLE UNCHANGED

Accept EVID-0111. The final exact local refinement is bracketed around
`(nu_raw,V_A)=(0.165,5.5)`, top-ten ranking is stable under GH-order checks,
and exact VA slices close the high-nu branch through `nu_raw=0.8`.

Set the redesigned numerical experiment status to
`GLOBAL_OPTIMUM_RESOLVED`. This resolves only the frozen finite numerical
search protocol; it does not authorize publication-scale training,
final-test access, baseline selection, or broader security claims.

Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0111
- `results/redesigned_baseline_global_mb_va/continuation_final_summary.json`
- `results/redesigned_baseline_global_mb_va/continuation_final_report.md`

## DEC-0094 - Accept targeted ridge continuation; keep nu_max unresolved

Date: 2026-10-01

Status: ACTIVE CONTINUATION DECISION; GLOBAL OPTIMUM UNRESOLVED

Accept EVID-0110 as the targeted continuation of the redesigned-baseline
search. The exact ridge moved toward higher `nu_raw` and lower `V_A`, with
best exact candidate `(0.165,5.5)`, `K=0.07904194520968355`.

Accept the sparse `V_A` boundary evidence and the decreasing high-`nu`
branch through `nu_raw=0.40` as diagnostics. Do not call the candidate a
continuous/global optimum because the expanded `nu_max=0.8` boundary has not
been exact-evaluated. Retain `GLOBAL_OPTIMUM_UNRESOLVED` and resume only with
compatible exact AP points if further closure is desired.

Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0110
- `results/redesigned_baseline_global_mb_va/continuation_final_summary.json`
- `results/redesigned_baseline_global_mb_va/continuation_final_report.md`

## DEC-0093 - Activate redesigned experiment; keep global optimum unresolved

Date: 2026-10-01

Status: ACTIVE AUTHOR-AUTHORIZED EXPERIMENT DECISION; GLOBAL OPTIMUM UNRESOLVED

Accept EVID-0109 as the controlled experiment-specific re-freeze and exact
cache-bound search. The previous final-model hash
`8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`
is superseded only for this experiment by final-model hash
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
and composite model/config hash
`a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58`.

Authorize the dedicated runner to use adaptive finite numerical domains,
constant noise, no peak/budget guard, and direct Z-minus exactly as frozen.
Do not promote `(0.15,3.5548673904962893)` or the Uniform `V_A=1.075` row to a
selected or global baseline. Upper-nu, upper-VA, and global lower-VA boundaries
remain unresolved. Additional AP coverage may resume the same exact source
cache, but every new point must retain full-support/provenance gates.

The publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
This decision changes the experiment's physical baseline, energy-domain rules,
phase model, and Holevo target; it does not authorize training, final-test
access, held-out evaluation, or a publication claim.

### Evidence

- EVID-0109
- `results/redesigned_baseline_global_mb_va/final_summary.json`
- `results/redesigned_baseline_global_mb_va/evaluated_points.csv`
- `results/redesigned_baseline_global_mb_va/adaptive_domain_history.csv`

## DEC-0092 - Accept clean positive-SKR redraw; no scope expansion

Date: 2026-09-30

Status: ACTIVE VISUALIZATION-ONLY DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0108 as a clean display of the existing positive exact-tested
rows. The figure intentionally contains only the two requested protocols and
essential plot elements. Removing crossing annotations and explanatory text
does not remove or replace any data; the negative rows remain unplotted.

This decision does not authorize source moments, candidate generation,
channel/security evaluation, interpolation, optimization, baseline selection,
or publication-scale evaluation. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0108
- `scripts/render_skr_vs_distance_clean.py`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_clean.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_clean.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_clean_report.json`

## DEC-0091 - Accept positive-SKR-only redraw; no scope expansion

Date: 2026-09-30

Status: ACTIVE VISUALIZATION-ONLY DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0107 as a display-only view of the existing exact-tested rows.
Filtering to `SKR > 0` and using a logarithmic y-axis improves readability of
the useful positive-rate region. The 26-km and 810-km first-negative labels
are annotations only; they do not add or plot negative values and do not
estimate either crossing.

This decision does not authorize source moments, candidate generation,
channel/security evaluation, interpolation, optimization, baseline selection,
or publication-scale evaluation. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0107
- `scripts/render_skr_vs_distance_positive_only.py`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_positive_only.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_positive_only.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_positive_only_report.json`

## DEC-0090 - Accept clean symlog redraw; no scope expansion

Date: 2026-09-30

Status: ACTIVE VISUALIZATION-ONLY DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0106 as a display-only redraw of the existing extended exact
table. The symlog transform makes the mixed-sign low-rate region readable;
it does not create values, change signs, or estimate a crossing. Lines remain
visual connections between exact-tested points only, and the endpoint labels
remain exact-positive/exact-negative observations rather than a continuous
`L_max`.

This decision does not authorize source moments, candidate generation,
channel/security evaluation, interpolation, optimized-MB search, baseline
selection, or publication-scale evaluation. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0106
- `scripts/render_skr_vs_distance_redraw_symlog.py`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_symlog.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_symlog.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_symlog_report.json`

## DEC-0089 - Accept extended exact-grid MB sign bracket; diagnostic-only

Date: 2026-09-30

Status: ACTIVE CACHE-ONLY EXTENSION DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0105 as an extension of the common-feasible diagnostic using the
same exact/hash-matched candidate sets and unchanged baseline. Record the MB
last-positive/first-negative pair as the exact-tested bracket `800 km` to
`810 km` only. The difference from Uniform is an exact-grid endpoint
comparison (`800 - 25 = 775 km`), not a continuous maximum-distance claim.

The new line plot is a visualization of exact rows. Its connecting segments
are not interpolated data, and the near-zero MB endpoint values are not
numerical-convergence evidence. This decision does not authorize source
moments, new C,w candidates, optimized-MB search, security-formula changes,
baseline selection, or publication-scale evaluation. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0105
- `scripts/run_revised_uniform_mb_common_feasible_extension.py`
- `scripts/render_skr_vs_distance_redraw_extended.py`
- `results/revised_uniform_mb_common_feasible_extended_diagnostic/revised_uniform_mb_common_feasible_report.json`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_extended.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_extended.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_distance_table_extended.csv`

## DEC-0088 - Accept exact-point SKR visualization redraw; no scope expansion

Date: 2026-09-30

Status: ACTIVE VISUALIZATION-ONLY DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0104 as a redraw of the existing EVID-0102/EVID-0103 exact
common-feasible artifacts. Straight line segments are permitted only as a
visual connection between existing exact-tested points in distance order;
they must not be interpreted as interpolated SKR values or a precise
zero-crossing estimate. The redraw adds no data, source moments, C,w values,
channel/security evaluation, optimization, or protocol claim. Lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0104
- `scripts/render_skr_vs_distance_redraw.py`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_report.json`

## DEC-0087 - Accept named diagnostic figure export; no scope expansion

Date: 2026-09-30

Status: ACTIVE DIAGNOSTIC EXPORT DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0103 as the named-asset export of EVID-0102. The renderer may
reuse the already verified common-feasible exact envelope for the requested
main SKR figure, security-term figures, and per-distance table, provided it
keeps exact markers only and preserves the fail-closed feasibility checks.
This export does not constitute a new channel/security evaluation and does
not authorize source-moment generation, C,w interpolation, optimized-MB
search, publication-scale evaluation, baseline selection, or a precise
zero-crossing estimate. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0103
- `scripts/render_revised_hap_uav_optical_baseline_figure.py`
- `results/revised_hap_uav_optical_baseline_figure/figure_report.json`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance.png`
- `results/revised_hap_uav_optical_baseline_figure/skr_vs_distance.pdf`
- `results/revised_hap_uav_optical_baseline_figure/skr_distance_table.csv`

## DEC-0086 - Accept common-budget Uniform/MB diagnostic; no publication claim

Date: 2026-09-30

Status: ACTIVE CACHE-ONLY DIAGNOSTIC DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0102 as a fair common-budget comparison using only exact,
current-hash-matched C,w rows with the same `0 < V_A <= 1.5 SNU` budget for
Uniform and MB. Existing peak-energy feasibility checks with
`n_peak_photons=30.0` passed for all included rows. The channel was recomputed
at every tested distance and the figures contain exact markers only.

Under this bounded cache envelope MB is above Uniform at all 13 tested
distances. Uniform's last exact positive is 25 km and first exact negative is
26 km. MB remains positive through the largest exact-tested distance, 30 km.
The best feasible exact MB row at 22 and 25 km is `nu=0.2`,
`V_A=1.3833230303`. The SKR gain is `0.0442303289` bits/use at 22 km and
`0.0238529688` bits/use at 25 km.

The decomposition shows the primary observed advantage is larger `beta I_AB`.
Lower `chi_BE` helps at 22 km, but at 25 km MB has higher `chi_BE` and the
larger classical term still dominates. This result does not authorize source
moment generation, C,w interpolation, optimized-MB search, common exact-VA
grid claims, baseline selection, or publication-scale evaluation. Lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0102
- `results/revised_uniform_mb_common_feasible_diagnostic/revised_uniform_mb_common_feasible_report.json`
- `results/revised_uniform_mb_common_feasible_diagnostic/diagnostic_distance_envelope.csv`
- `results/revised_uniform_mb_common_feasible_diagnostic/security_term_attribution.csv`
- `results/revised_uniform_mb_common_feasible_diagnostic/excluded_candidates.csv`
- `results/revised_uniform_mb_common_feasible_diagnostic/diagnostic_skr_vs_distance.png`

## DEC-0085 - Accept revised Uniform/MB distance comparison as diagnostic-only

Date: 2026-09-30

Status: ACTIVE CACHE-ONLY DIAGNOSTIC DECISION; NO BASELINE OR LIFECYCLE CHANGE

Accept EVID-0101 as a bounded comparison of the existing exact-cache Uniform
and MB rows under `w0=0.10 m`, `D_r=0.55 m`, `tau_zen=0.92`,
`epsilon_ch=0.0186 SNU`, `beta=0.95`, AO OFF, and phase noise OFF. The channel
was recomputed at every tested distance from 19 to 30 km, including the
existing 21.9393102292-km geometry fixture.

The best exact-tested MB envelope is above the best exact-tested Uniform
envelope at all 12 tested distances. Uniform has the last exact positive at
25 km and the first exact negative at 26 km. MB remains positive at the last
tested point, 30 km. These are exact-grid sign observations only; no zero
crossing was interpolated.

This decision does not authorize optimized-MB search, new source moments,
interpolation, Binomial evaluation, common-grid claims, baseline selection,
publication figures, or publication-scale evaluation. The available rows are
8 Uniform and 30 MB current hash-matched historical C,w candidates; Binomial
has no safe current-compatible exact C,w dataset. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0101
- `results/revised_uniform_mb_distance_diagnostic/revised_uniform_mb_distance_report.json`
- `results/revised_uniform_mb_distance_diagnostic/diagnostic_candidate_details.csv`
- `results/revised_uniform_mb_distance_diagnostic/diagnostic_distance_envelope.csv`
- `results/revised_uniform_mb_distance_diagnostic/protocol_summary.csv`
- `results/revised_uniform_mb_distance_diagnostic/availability.csv`
- `results/revised_uniform_mb_distance_diagnostic/diagnostic_skr_vs_distance.png`
- `results/revised_uniform_mb_distance_diagnostic/diagnostic_beta_iab_vs_distance.png`
- `results/revised_uniform_mb_distance_diagnostic/diagnostic_chi_be_vs_distance.png`

## DEC-0084 - Accept revised optical baseline as cache-only diagnostic; do not select baseline

Date: 2026-09-30

Status: ACTIVE CACHE-ONLY DIAGNOSTIC DECISION; FULL UNIFORM V_A SWEEP UNRESOLVED

Accept EVID-0100 as a bounded test of the requested `w0=0.10 m`,
`D_r=0.55 m` optical geometry with the existing channel, security evaluator,
`epsilon_ch=0.0186 SNU`, `beta=0.95`, AO OFF, and phase noise OFF. On the
8 current hash-matched exact Uniform candidates, this geometry is positive at
the best-tested row `V_A=1.075` with `SKR=0.00855162790745` bits/use. The
controlled cases show that the receiver aperture is the dominant recovery
mechanism in this fixture: new `w0` alone remains negative at the old
`D_r=0.08 m`, while the combined new geometry is positive.

The exact requested V_A list is not fully covered: only `0.6,0.7,0.8,1.075`
are both requested and available in the current Uniform C,w cache. Missing
values remain missing; no C,w, Z, or Holevo result was interpolated or
generated. Therefore no continuous optimum, final positive interval, selected
hardware baseline, or publication-quality `L_max` is approved. The reported
`D_r≈0.5113500300 m` and `L≈25.6127085762 km` are sparse exact-candidate
bisection diagnostics only.

The `FINAL_MODEL_SPEC.md` SHA-256 currently differs from the historical hash
required by `AGENTS.md`; this is recorded as a blocker and the specification
was not changed. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0100
- `results/revised_uniform_baseline_diagnostic/revised_uniform_baseline_report.json`
- `results/revised_uniform_baseline_diagnostic/table1_revised_channel.csv`
- `results/revised_uniform_baseline_diagnostic/table2_uniform_va_sweep_exact_available.csv`
- `results/revised_uniform_baseline_diagnostic/table2_requested_va_status.csv`
- `results/revised_uniform_baseline_diagnostic/table3_nearby_receiver_aperture.csv`
- `results/revised_uniform_baseline_diagnostic/table4_nearby_beam_waist.csv`
- `results/revised_uniform_baseline_diagnostic/distance_sweep.csv`
- `results/revised_uniform_baseline_diagnostic/receiver_crossing.csv`
- `results/revised_uniform_baseline_diagnostic/distance_crossing.csv`

## DEC-0083 - Accept beam-waist diagnostic; do not select transmitter or receiver

Date: 2026-09-30

Status: ACTIVE CACHE-ONLY DIAGNOSTIC DECISION; CONTINUOUS UNIFORM OPTIMUM UNRESOLVED

Accept EVID-0099 as a bounded optical beam-waist/receiver-aperture diagnostic.
At the current `D_r=0.08 m`, changing `w0` from `4.4 mm` through `150 mm`
did not produce a positive SKR on the available exact Uniform candidates.
The result is non-monotone because reduced diffraction coupling competes with
the narrower far-field beam and the existing pointing jitter.

The 2D control shows that the receiver aperture, not beam waist alone, is the
decisive missing scale: the first positive coarse row is `(w0=30 mm,D_r=1 m)`
and its sparse exact receiver threshold is about `0.953 m`. This is a
diagnostic combination only. The continuous Uniform `V_A` domain remains
unresolved because only eight exact C,w rows exist, so no `w0_crit`, selected
hardware design, or Uniform optimum may be claimed.

Do not interpolate C,w, extend the frozen `[0.1,4.0]` V_A domain to the
requested `[0.01,5]`, alter `epsilon_ch`, add AO/phase-noise suppression,
change beta, alter the security formula, or select a baseline. Any exact
continuation requires an explicit source-moment budget and domain decision.
No model/security equation, source moment, training state, final-test state, or
lifecycle gate changed. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0099
- `results/beam_waist_diagnostic/beam_waist_report.json`
- `results/beam_waist_diagnostic/beam_waist_sweep.csv`
- `results/beam_waist_diagnostic/beam_waist_receiver_heatmap.csv`
- `results/beam_waist_diagnostic/beam_waist_receiver_thresholds.csv`
- `results/beam_waist_diagnostic/beam_waist_distance_crossing.csv`

## DEC-0001 — Freeze C4 transmitter representation

Date: 2026-08-26

Status: ACTIVE

### Context

An unrestricted 256-way PMF plus weighted centering does not guarantee the
standard-form covariance required by the accepted security functional and
confounds PS with physical translation.

### Decision

Use 64 orbit probabilities expanded by fourfold rotation, one globally shared
64-prototype GS geometry, no PMF-weighted translation, an independent adaptive
VA branch, and one statewise scalar physical normalization.

### Rationale

C4 symmetry gives zero displacement, zero pseudomoment, equal quadrature
variance, and unambiguous PS/GS/VA gradient ownership.

### Evidence

- `docs/FINAL_MODEL_SPEC.md`
- `src/modulation/`
- EVID-0002

### Consequences

Claims must say channel-adaptive fourfold-symmetric PS, not unrestricted
256-way shaping. Legacy checkpoints are incompatible.

### Alternatives rejected

Unrestricted 256 logits with PMF-weighted centering and normalization.

### Supersedes / Superseded by

Supersedes the pre-freeze transmitter implementation.

## DEC-0002 — Freeze common energy and hard peak domain

Date: 2026-08-27

Status: ACTIVE

### Context

All schemes require an energy-fair comparison and a finite physical amplitude
domain. Unit-RMS GS and positive softmax probabilities alone do not provide a
uniform peak bound.

### Decision

Use `V_A in [0.1,4.0] SNU`, `E[V_A]<=1.5 SNU`, and fail-closed
`max_i|alpha_i|^2<=30` photons over complete preregistered realizations,
without clipping.

### Rationale

The same box, average budget, and hard physical-symbol rule apply to every
baseline and learned mode.

### Evidence

- `configs/default.yaml`
- `docs/AMPLITUDE_DOMAIN_DECISION.md`
- EVID-0009

### Consequences

Continuous-domain or unevaluated-policy peak claims remain unsupported.

### Alternatives rejected

Soft penalty alone, observed-maximum post hoc bounds, and scheme-specific
energy budgets.

### Supersedes / Superseded by

Supersedes the unresolved peak-domain state.

## DEC-0003 — Select MI sample count 2048

Date: 2026-08-27

Status: ACTIVE

### Context

The exact discrete-input MI Monte Carlo estimator required a sample count
selected without test access under the preregistered sequential rule.

### Decision

Use `N_MC=2048` for validation/test numerical evaluation on the certified
finite roster. Training retains its separately preregistered smaller count.

### Rationale

The machine-readable convergence artifact selects 2048 after the declared
global refinement and replication checks.

### Evidence

- `results/mi_convergence.json`
- `docs/MI_CERTIFICATION_ROSTER.md`
- EVID-0003

### Consequences

Future selected checkpoints still require exact-roster replay. This decision
does not certify Holevo support or publication execution.

### Alternatives rejected

Arbitrary default sample counts and test-tuned selection.

### Supersedes / Superseded by

Supersedes unresolved MI sample count.

## DEC-0004 — Reject configured 1e-12 support rule

Date: 2026-08-28

Status: ACTIVE

### Context

The near-coincident fixture has physical rank 256, while the configured
`1e-12` rule retains six modes and violates frozen `w`, `chi_BE`, and raw-`K`
tolerances.

### Decision

Treat `1e-12` as invalid and unapproved. Keep the configuration approval flag
false and all publication entry points fail closed until a replacement
protocol is approved and certified.

### Rationale

The full-support oracle shows `w` error `0.2181586469` and `chi_BE`/raw-`K`
error about `0.0033089478` bit at `1e-12`.

### Evidence

- `results/near_coincident_gram_oracle.json`
- `results/float64_gram_comparison.json`
- `docs/GRAM_ORACLE_DIAGNOSIS.md`
- EVID-0004 and EVID-0005

### Consequences

No threshold, baseline selection, publication training, or held-out evaluation
is authorized.

### Alternatives rejected

Treating cutoff-256 float64 or agreement among ill-conditioned float64
formulations as ground truth.

### Supersedes / Superseded by

Supersedes the prospectively active but conditional `1e-12` candidate.

## DEC-0005 — Propose observable-based 1e-13 protocol

Date: 2026-08-29

Status: PROPOSED

### Context

Candidate `1e-13` has favorable forward and local-gradient diagnostics, while
exact support identity with `1e-14` fails on 12 fixtures.

### Decision

Propose, but do not activate, `1e-13` with forward-observable,
arbitrary-precision stress, local-gradient, boundary, whole-segment, and
realized-domain replay gates. Preserve support masks as diagnostics.

### Rationale

Exact cross-threshold support identity is neither necessary nor sufficient for
full-support observable accuracy.

### Evidence

- `results/production_gram_certification.json`
- `results/support_threshold_protocol_audit.json`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`
- EVID-0006 through EVID-0008

### Consequences

The candidate remains outcome-informed and cannot be used by production runs.

### Alternatives rejected

Silently activating `1e-13`, retaining exact support equality as the sole
accuracy gate, or using a Gaussian approximation.

### Supersedes / Superseded by

Approval was rejected by DEC-0006; the design remains a proposal.

## DEC-0006 — Reject current certification-protocol approval

Date: 2026-08-30

Status: REJECTED

### Context

The same pilot outcomes influenced the candidate threshold and feasibility
caps. Only one fixture has full-support arbitrary-precision evidence, and no
validated interval whole-segment enclosure exists.

### Decision

Do not approve the proposed protocol or `1e-13`. Preserve pilot artifacts as
diagnostics, quarantine the stale boundary aggregate, and remain
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Rationale

Independent pre-hashed confirmation, mechanically selected high-precision
classes, and rigorous whole-segment numerical bounds are missing.

### Evidence

- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`
- `results/support_boundary_bisection_crn.json` — quarantined
- EVID-0007, EVID-0008, and EVID-0010

### Consequences

No training, threshold recertification, optimized-MB grid, baseline selection,
or test access may proceed.

### Alternatives rejected

Reusing the pilot roster as confirmation, treating float64 `1e-14` as full
support, or treating finite-node sampling as a segment proof.

### Supersedes / Superseded by

Rejects approval of DEC-0005 without deleting its historical proposal.

## DEC-0007 — Restrict numerical claims to finite realized domains

Date: 2026-08-28

Status: ACTIVE

### Context

No uniform conditioning or peak theorem covers the unrestricted continuous
PS/GS parameter space.

### Decision

Limit claims to explicitly enumerated, hash-bound, fail-closed finite
realizations and fixtures. Require later replay of every selected/evaluated
ensemble.

### Rationale

Finite evidence cannot establish uniform continuous-domain conditioning.

### Evidence

- `docs/NUMERICAL_DOMAIN_SCOPE.md`
- `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`
- EVID-0003 through EVID-0010

### Consequences

No claim may extrapolate stress or canonical fixtures to all learned policies.

### Alternatives rejected

Uniform continuous-domain claims without proof.

### Supersedes / Superseded by

Not superseded.

## DEC-0008 — Use validation-only baseline selection

Date: 2026-08-27

Status: ACTIVE

### Context

Uniform, Binomial, fixed-MB, and optimized-MB baselines require common
energy-fair selection without test leakage.

### Decision

Select fixed VA and optimized-MB `(nu,VA)` using the preregistered validation
grids and deterministic tie-break only after numerical certification passes.
The test set cannot influence selection.

### Rationale

This provides fair, reproducible baselines under the same box and average
budget.

### Evidence

- `configs/default.yaml`
- `docs/PUBLICATION_EXPERIMENT_PROTOCOL.md`
- `scripts/select_validation_baselines.py`
- EVID-0011

### Consequences

The policy is active, but no selection has run because its numerical
dependencies are blocked.

### Alternatives rejected

Test-selected baselines, unequal energy budgets, and post hoc grids.

### Supersedes / Superseded by

Not superseded.

## DEC-0009 — Make C4 Gram the production Holevo backend

Date: 2026-08-29

Status: ACTIVE

### Context

The C4 weighted coherent-state Gram representation is cutoff-independent and
algebraically implements the same accepted source-moment functional. Dense
Fock evaluation remains useful diagnostically but is not a stable stress
reference.

### Decision

Route production Holevo evaluation through `c4_gram`; retain
`fock_diagnostic` only as an explicit diagnostic backend. Preserve the same
hard absolute numerical-support rule and security equations.

### Rationale

This removes Fock-tail truncation from production source moments without
changing the accepted security functional.

### Evidence

- `src/cvqkd/gram_moments.py`
- `src/cvqkd/holevo.py`
- `results/production_gram_certification.json`
- EVID-0006

### Consequences

Backend integration is active, but its support threshold remains invalid and
unapproved; publication execution stays blocked.

### Alternatives rejected

Silent Gaussian approximation and dense-Fock production fallback.

### Supersedes / Superseded by

Supersedes dense Fock as the production backend.

## DEC-0010 - Track a minimal portable evidence set

Date: 2026-08-30

Status: ACTIVE, PENDING COMMIT

### Context

The active evidence register cited result payloads ignored by Git, preventing
clean-clone reconstruction.

### Decision

Use a narrow `.gitignore` allowlist and a hash/size manifest for only active,
non-quarantined certification payloads. Keep all unlisted result files ignored.

### Rationale

This preserves reviewable evidence without treating the entire result tree as
authoritative or versioning runtime-only data.

### Evidence

- `docs/CERTIFICATION_ARTIFACT_MANIFEST.json`
- EVID-0014

### Consequences

Nineteen payloads are staged. Portability begins only after commit.

### Alternatives rejected

Blanket-unignore of `results/` and Markdown-only summaries.

### Supersedes / Superseded by

Not superseded.

## DEC-0011 - Freeze the independent confirmation roster before outcomes

Date: 2026-08-30

Status: ACTIVE

### Context

The previous candidate-support diagnostics were outcome-informed and lacked a
disjoint prospective confirmation set.

### Decision

Freeze a new certification-only channel, 18 fixtures, and a four-fixture
high-precision subset with outcome inspection explicitly marked absent.

### Rationale

Membership and precision-class design must precede candidate outcomes to avoid
post hoc selection.

### Evidence

- `configs/independent_confirmation_roster.yaml`
- EVID-0015

### Consequences

The roster foundation exists, but no threshold is approved and final test
remains inaccessible.

### Alternatives rejected

Reusing pilot fixtures as independent confirmation or selecting fixtures after
candidate-threshold inspection.

### Supersedes / Superseded by

Not superseded.

## DEC-0012 - Keep the segment enclosure experimental and fail closed

Date: 2026-08-30

Status: ACTIVE FAIL-CLOSED POLICY; NUMERICAL CONTEXT SUPERSEDED

### Context

Analytic interval/derivative propagation is implemented, but the initial Gram
assembly and Hermitian eigensystem lack a validated numerical enclosure.

### Decision

Classify the current implementation as proof-oriented diagnostic foundation
only. It must return no realized support certificate while `eta_num` is absent.

### Rationale

Endpoint enclosure and finite-node ranks cannot establish whole-segment
separation from a hard eigenvalue threshold.

### Evidence

- `src/validation/whole_segment_support.py`
- EVID-0017

### Consequences

Zero of twelve realized paths certifies. Threshold approval and optimizer
integration remain blocked.

### Alternatives rejected

Empirical safety factors, endpoint-only acceptance, and calling
`numpy.nextafter` a validated Hermitian eigensolver.

### Supersedes / Superseded by

Refined by DEC-0014, which supplies validated Gram arithmetic but retains the
fail-closed policy because endpoint support remains unresolved.

## DEC-0013 - Extend oracle precision only to resolve declared full support

Date: 2026-08-30

Status: ACTIVE DIAGNOSTIC POLICY

### Context

The predeclared 50/80/120/160 digit sequence did not resolve full rank for the
regular Uniform and Binomial fixtures.

### Decision

Freeze a rank-resolution-only extension to 600/800 digits without inspecting
candidate-threshold observables. Preserve the stress schedule at
1050/1250/1450 digits.

### Rationale

The oracle requirement was two successive full-support precisions; unresolved
mathematical rank is not a candidate performance outcome.

### Evidence

- `configs/independent_confirmation_oracle.yaml`
- EVID-0019

### Consequences

All four declared fixtures now have two converged full-rank rows. This remains
an oracle result, not support-threshold approval.

### Alternatives rejected

Treating 160-digit truncated rank as truth or changing the threshold policy.

### Supersedes / Superseded by

Not superseded.

## DEC-0014 - Keep the Arb direct-enclosure backend experimental and require threshold-relative inertia

Date: 2026-08-31

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0015; HISTORICAL FAIL-CLOSED EVIDENCE

### Context

Validated Arb/acb propagation now covers the actual PS/VA/GS parameter path,
but full endpoint eigenvalue isolation fails for all 12 realized segments at
160, 256, and 384 bits. Increasing subdivision cannot repair an unresolved
endpoint spectrum.

### Decision

Retain the direct interval Gram plus Weyl/subdivision method as an
experimental mathematically stronger replacement proposal. Continue to fail
closed. The next implementation cycle must use a validated threshold-relative
Hermitian inertia or equivalent eigencluster enclosure that can prove the
number of eigenvalues above `tau` without isolating every clustered
eigenvalue. Do not increase precision or alter thresholds post hoc in the
completed cycle.

### Evidence

- EVID-0021
- EVID-0022

### Consequences

No threshold is approved, no optimizer rollback is activated, and lifecycle
status remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Alternatives rejected

Treating finite nodes as proof, accepting approximate eigenvalues, silently
raising the maximum precision after inspecting outcomes, or regularizing the
security functional.

### Supersedes / Superseded by

Refines DEC-0012 by supplying validated Gram arithmetic while preserving its
fail-closed outcome. Superseded by DEC-0015 after shifted inertia resolved the
endpoint blocker but direct interval certification still failed 0/12.

## DEC-0015 - Accept point inertia evidence; reject direct interval V1 as a certification path

Date: 2026-08-31

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION, NOT THRESHOLD APPROVAL

### Context

Validated block-LDL* resolves every realized endpoint at 160 bits, but the
direct interval Frobenius guard-band cycle resolves no realized segment after
299 nodes and 12302.94 seconds. Adversarial review also found missing automatic
bundle/environment hash enforcement and an overbroad dormant crossing branch
in the frozen V1 segment producer.

### Decision

Retain the point-inertia implementation and endpoint artifact as valid
experimental evidence. Preserve the V1 whole-segment artifact as a fail-closed
0/12 result, but do not allow V1 to produce an acceptable pass. Candidate
`1e-13` remains proposed/unapproved and configured `1e-12` remains
invalid/unapproved.

The next cycle must use a new, prospectively hash-bound producer that enforces
all frozen inputs and runtime acceptance, proves path domain/continuity before
any intermediate-value crossing claim, and replaces the dependency-inflated
full-matrix Frobenius guard with a sharper validated fixed-basis
congruence/cluster, affine/Taylor, or Schur-complement enclosure.

### Consequences

No threshold, optimizer integration, optimized-MB selection, baseline
selection, publication training, or final-test access is authorized. Claims
remain limited to validated point support on the finite frozen fixtures.

### Alternatives rejected

Approving from equal endpoint inertia, treating interval zero inclusion as a
crossing, increasing precision after outcome inspection, accepting V1 despite
provenance gaps, or changing the physical/security functional.

### Supersedes / Superseded by

Supersedes DEC-0014 as the active numerical next-action policy. Not
superseded.

## DEC-0016 - Accept the exact-tau oracle; reject V2 whole-segment feasibility

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION, NOT THRESHOLD APPROVAL

### Context

The V2.2 exact-dyadic oracle independently certified the four expected support
counts and nearest gaps. The prospectively selected V2.3 Taylor/eigencluster
feasibility subset then certified 0/4 segments, produced four resource-limit
rows, and exceeded one nominal hard deadline. The implementation lacks bounded
Windows process-tree/pipe cleanup, but the realized overrun's exact cause was
not independently traced. Durable nodes also exhausted the cluster cap and
failed far-block inertia.

### Decision

Accept EVID-0026 as validated point support/gap evidence. Preserve EVID-0027
as unsuccessful whole-segment evidence and stop before the all-12 cycle. Do
not approve candidate `1e-13`, reactivate historical `1e-12`, or authorize any
downstream baseline/training/test action.

Any next segment attempt must be a newly frozen V3. It must use a tested
Windows process-tree/Job-Object timeout, durably checkpoint path-domain results
before spectral work, retain scalar Taylor coefficient dependence through the
fixed congruence instead of collapsing immediately to entrywise balls, and
test sequential positive/negative far-block elimination or an independently
proved tighter equivalent as a tightening strategy.

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. V2 is not permitted
to run all 12 paths because its prospectively frozen feasibility gate failed.
The exact-tau oracle resolves the former independent-support-count blocker but
does not establish whole-path fixed inertia or optimizer admissibility.

### Alternatives rejected

Increasing the V2 wall-clock limit after observing timeouts, raising its
cluster cap, loosening the threshold, treating checkpoint control flow as a
persistent path-domain certificate, accepting a late worker result, or using
zero-containing intervals as crossings.

### Supersedes / Superseded by

Supersedes DEC-0015 as the active numerical next-action policy. Not
superseded.

## DEC-0017 - Stop incremental hard-support whole-segment certification

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED ENGINEERING DECISION; METHOD IMPRACTICALITY PROPOSED

### Context

V3 prospectively implemented every declared architectural tightening:
Windows Job Objects, early path-domain persistence, complete hash-chained node
and Schur journals, exact C4 sectors, coefficient-level Taylor congruence, and
deterministic sequential sign-homogeneous Schur elimination. The paired
dependency radius improved by about 38--43x, and realized Schur reductions
executed, but the frozen four-row gate still produced 0/4 complete segments,
four resource limits, 52--53 unresolved far modes on completed roots, and two
large watchdog return-bound breaches.

### Decision

Preserve EVID-0028 as the decisive failed V3 cycle. Do not rerun or retune V3,
do not execute all 12, and do not automatically create V4. Record
`HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`
as a proposed engineering conclusion pending independent numerical/security-
method review.

The review must decide whether to change numerical regularization
architecture, derive a mathematically equivalent smoother formulation,
change optimization admissibility strategy, or narrow the paper claim. It may
not silently regularize the security functional or approve a threshold.

### Evidence

- EVID-0028
- V3 result SHA-256
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`
- V3 manifest SHA-256
  `5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. Candidate `1e-13`
remains proposed/unapproved, `1e-12` remains invalid/unapproved, and no
baseline selection, optimized-MB grid, training, final-test access, or
publication claim is authorized.

### Alternatives rejected

Post-outcome increases to precision, runtime, Taylor order, cluster size,
block schedule, or subdivision; rerunning a favorable subset; treating Schur
activity or a smaller radius as a complete path proof; and proceeding to all
12 despite the failed gate.

### Supersedes / Superseded by

Supersedes DEC-0016 as the active numerical next-action policy. Not
superseded.

## DEC-0018 - Authorize pointwise-guard protocol design only

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0019; ACTIVE METHOD REVIEW
EVIDENCE

### Context

The V3 hard-support whole-segment feasibility cycle failed closed, while exact
point-inertia/gap evidence and fixed-support local-gradient diagnostics remain
available on finite rosters. The provenance audit found only CRLF/LF byte
normalization mismatches; no scientific payload changed.

### Decision

Authorize the next task to design a prospective pointwise admissibility guard
and transactional rollback protocol. Do not implement it in this cycle, do
not approve any support threshold, and do not perform realized optimization or
evaluation. The guard must validate the current point, use locally valid
fixed-support gradients, validate the proposed endpoint, and commit or restore
the complete mutable training state. It must not certify intermediate points
or alter the security functional.

### Method review conclusion

Whole-segment support invariance is not required for validity of the adopted
statewise security calculation at a validated realized point; it was an
additional numerical condition for claiming smooth optimization through a hard
support operation. A transition at an unobserved interpolation point affects
optimization smoothness and admissibility, not the already computed pointwise
value, provided the pointwise evaluator and numerical rule are themselves
validated. Current evidence supports this only on the finite exact-tau,
endpoint, stress-oracle, and local-gradient rosters.

The pointwise rule changes only the numerical optimization domain. Physical
modulation, MI, Holevo, and reported SKR equations remain unchanged. Claims of
global differentiability, continuous-domain support stability, and
whole-trajectory certification remain prohibited. `attack_class=None` limits
manuscript security wording but does not by itself block numerical design;
the separate threshold/support blocker still prevents execution.

### Evidence

- EVID-0029
- EVID-0026, EVID-0027, EVID-0028
- `docs/SECURITY_SCOPE_FREEZE.md`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`

### Consequences

`NEXT_ACTIONS.md` now names pointwise-guard protocol design as the sole next
permitted action. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; candidate `1e-13` remains proposed
and `1e-12` remains invalid.

### Alternatives ranked

1. `POINTWISE_GUARD` - best supported by finite point-inertia and local-gradient
   evidence, and it preserves the frozen security functional.
2. `NARROW_PAPER_CLAIM` - scientifically safe fallback but does not address
   optimization usability.
3. `NUMERICAL_REGULARIZATION_REDESIGN` - potentially useful, but its security
   semantics are not yet documented.
4. `SMOOTHER_EQUIVALENT_FORMULATION_REVIEW` - no mathematically equivalent
   implementation or proof is currently available.

## DEC-0019 - Freeze pointwise guard protocol design

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0020; ACTIVE DESIGN CONTRACT

### Decision

Freeze `pointwise-guard-protocol-v1` as a proposed, threshold-parametric design
for the next implementation task. The smallest certification unit is one
unique realized statewise physical ensemble, not an individual Monte Carlo
noise sample. The design reuses validated shifted-Hermitian block-LDL*
inertia and nearest-eigenvalue brackets. It accepts only if

`certified_margin > 2 * uncertainty_upper`,

where the margin is the minimum certified distance from `tau` to the nearest
bracketed eigenvalue on either side and `uncertainty_upper` is the maximum
validated bracket half-width. The factor two is a fixed two-sided enclosure
allowance, not an outcome-tuned constant.

Only `POINTWISE_ADMISSIBLE` permits a local fixed-support gradient. Guard-band,
certification, and provenance failures are no-ops. The transaction snapshots
all mutable model, optimizer, dual-controller, module-mode, RNG, explicit
generator, and counter state. Schedulers and GradScaler are absent in the
current repository and become mandatory fields if introduced before
implementation. No interpolation segment is certified.

### Evidence

- EVID-0030
- `configs/pointwise_guard_protocol_v1.yaml`
- `docs/POINTWISE_GUARD_PROTOCOL.md`
- `tests/test_pointwise_guard_protocol_design.py`

### Consequences

The next permitted task is implementation of this exact protocol. The protocol
remains `PROPOSED`; the candidate threshold remains `PROPOSED_UNAPPROVED`;
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0020 - Accept pointwise implementation and authorize smoke test

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED IMPLEMENTATION DECISION; SMOKE ONLY

### Decision

Accept the pointwise guard implementation against the frozen protocol for the
scoped implementation matrix. The runtime now performs pre-update point
checks, rejects before backward, validates the post-update endpoint, defers
the energy-dual update until commit, and restores complete transaction state
on rejection. The validated point-certifier and provenance bindings remain
injected; no raw complex128 fallback exists.

Authorize the separately frozen six-step certification-only smoke test as the
next task. Do not run it in the implementation task, approve `1e-13`, reactivate
`1e-12`, or perform publication training, baseline selection, or test access.

### Evidence

- EVID-0031
- `results/pointwise_guard_implementation_v1.json`
- `tests/test_pointwise_guard.py`

### Consequences

`NEXT_ACTIONS.md` now names `POINTWISE_GUARD_SMOKE_TEST_AUTHORIZED` as the sole
next action. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0021 - Stop pointwise smoke on missing validated backend

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; ENVIRONMENT BLOCKED

### Decision

Do not execute the frozen pointwise smoke when the required validated
Arb/python-flint backend is unavailable and no repository-backed point
certifier exists. The injected certifier used by unit tests and raw
complex128 eigenspectra are not acceptable substitutes. Record the blocked
attempt with zero updates and preserve the smoke protocol unchanged.

### Evidence

- EVID-0032
- `results/pointwise_guard_smoke_v1.json`
- `configs/pointwise_guard_protocol_v1.yaml`

### Consequences

The usability decision is `SMOKE_TEST_BLOCKED_BY_ENVIRONMENT`, not
`OPTIMIZATION_USABLE` or `OPTIMIZATION_EFFECTIVELY_FROZEN`. The exact next
action is to restore the hash-pinned certification environment and provide a
validated repository-backed point-certifier adapter, then rerun the same
frozen six-step smoke test without retuning.

## DEC-0022 - Accept restored certification environment

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0023; ACTIVE ENVIRONMENT EVIDENCE

### Decision

Accept EVID-0034 as a current verified pass for the exact certification
environment. CPython 3.12.10, python-flint 0.9.0, FLINT 3.6.0, PyYAML 6.0.3,
NumPy 2.5.2, Windows x86-64, and the lock hash match the frozen requirements.
The real Arb/acb and shifted-inertia preflight suite passes 32/32.

At the time of this decision, the next task was adapter implementation; that
adapter and the smoke runner are now frozen by DEC-0023.
Do not run the smoke test in this environment-only task, approve a threshold,
or change any scientific/security functional.

### Evidence

- EVID-0034
- `results/certification_environment_restore_v2.json`

### Consequences

`NEXT_ACTIONS.md` now names adapter implementation as the sole next action.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0023 - Freeze real adapter and authorize smoke execution

Date: 2026-09-02

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0024; ACTIVE V1 PROVENANCE

### Decision

Accept EVID-0035 and EVID-0036. The real adapter uses the restored pinned
Arb/FLINT environment through canonical JSON and preserves the final physical
ensemble exactly. The no-override runner and prospective execution manifest
are frozen before smoke outcomes. Authorize the exact six-step, three-state,
two-repetition smoke test as the next task.

Do not change the threshold, guard inequality, seeds, state roster, precision,
optimizer settings, or security functional. Do not run publication training,
baseline selection, optimized-MB search, or final-test evaluation.

### Evidence

- EVID-0035
- EVID-0036
- `configs/pointwise_guard_execution_manifest_v1.json`

### Consequences

`NEXT_ACTIONS.md` now names `FROZEN_POINTWISE_SMOKE_EXECUTION_AUTHORIZED` as
the sole next permitted action. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0027 - Retain threshold blocker and authorize minimum prospective validation

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION; THRESHOLD UNAPPROVED

### Decision

Accept EVID-0041. Record `OPTIMIZATION_USABLE` as a pointwise optimizer result,
but do not approve `1e-13`. The dense-Fock cutoff label is stale for the active
cutoff-independent C4-Gram backend, while the failed Fock stress suffix remains
historical diagnostic evidence. The active threshold/support blocker is genuine:
formal support identity is false and the candidate comparison is
outcome-informed. Baseline selection remains a downstream numerical blocker.

Authorize only the minimum prospective finite threshold validation described by
EVID-0041. It must be frozen before outcomes, use independent full-support
arbitrary-precision Gram oracles for every declared ill-conditioned production
fixture, and compare all frozen observables under existing tolerances. Do not
rerun either smoke, change tau or security claims, or perform any publication
experiment.

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The exact next action
is to freeze and execute the prospective threshold/numerical validation gate;
explicit author threshold approval and completion of the existing numerical
prerequisites are required before publication-scale experiments.

### Evidence

- EVID-0041
- `results/threshold_numerical_gate_review_v1.json`
- `configs/default.yaml`
- `docs/FINAL_MODEL_SPEC.md`, Section 11

## DEC-0028 - Freeze minimum prospective threshold validation execution

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; THRESHOLD UNAPPROVED

### Decision

Freeze the 12 production fixtures whose declared `1e-14`/`1e-13` support masks
differ, with their roster hashes in `configs/threshold_validation_v1.yaml`.
For each, independently resolve full mathematical support with the existing
arbitrary-precision C4-Gram oracle at 600 and 800 decimal digits; accept only
two converged 256-mode rows and production `tau=1e-13` agreement for
support/rank diagnostics, `C,w,Z`, all three symplectic eigenvalues, `chi_BE`,
and raw `K` under the already frozen tolerances. The oracle never applies tau.

Authorize only the manifest-bound runner. A pass is pending explicit author
approval and does not itself change threshold status or publication lifecycle.

## DEC-0029 - Correct threshold-validation fixture provenance wiring

Date: 2026-09-02

Status: ACTIVE HARNESS CORRECTION; VALIDATION NOT RERUN

The attempted validation stopped before threshold evaluation. Its production
fixture reconstruction deterministically matched the frozen
`untrained_full_initialization` hash, but the reusable oracle harness compared
it to the different independent-confirmation roster hash. Bind the harness to
the already frozen production fixture hashes. The Torch-bearing production
Python runtime is required; the Arb-only environment has no Torch. No
scientific fixture, tau, tolerance, or expected production hash changed.

## DEC-0030 - Freeze support-free full-support C4-Gram implementation

Date: 2026-09-03

Status: ACTIVE IMPLEMENTATION DECISION; NO SCIENTIFIC CHANGE

Accept EVID-0044. Authorize implementation of the frozen full-support C4
sector source-moment backend only. It preserves the existing security chain
and all 12 fixtures, replaces threshold support with mathematical full support,
uses a residual-norm `w`, and sends insufficiently conditioned complex128
states to a fixed arbitrary-precision evaluation fallback. No gradient through
the fallback, training, threshold approval, or publication experiment is
authorized.

## DEC-0031 - Authorize frozen full-support evaluation validation

Date: 2026-09-03

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; VALIDATION ONLY

Accept EVID-0045. The evaluation-only full-support backend implementation and
hash-bound 12-fixture validation manifest are complete. Authorize exactly one
manifest-bound evaluation validation. Do not train, select baselines, access
final-test data, or authorize fallback gradients. A validation pass does not
approve a threshold or publication-scale experiments.

## DEC-0032 - Freeze independent gradient/VJP validation protocol

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; PROTOCOL NOT EXECUTED

Accept EVID-0046. Authorize only implementation of the future analytic
fast-path VJP and its no-override validation runner. The arbitrary-precision
fallback remains evaluation-only; any fallback route fails gradient validation
closed. A later execution requires a separate frozen execution manifest. No
training, threshold approval, baseline selection, optimized-MB search, or
final-test access is authorized.

## DEC-0033 - Freeze cluster-safe spectral Fréchet amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; AMENDMENT NOT EXECUTED

Accept EVID-0047. Supersede EVID-0030 only for the spectral-gradient rule:
the fast-path inverse-square-root derivative is the basis-invariant Loewner
Fréchet operator, with its Hermitian real-inner-product VJP. Do not use
individual-eigenvector backward or add an eigengap criterion. Authorize only
implementation of this custom fast-path VJP and a hash-bound runner; do not
execute gradient validation, differentiate fallback, or train.

## DEC-0034 - Freeze analytic VJP implementation and authorize validation

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; CERTIFICATION NOT EXECUTED

Accept EVID-0048. Authorize exactly one later execution of the hash-bound
gradient/VJP validation runner. EVID-0031 defines repeated-eigenvalue behavior;
AP fallback remains evaluation-only. This does not establish gradient
correctness, approve a threshold, authorize training, or permit final-test or
selection access.

## DEC-0035 - Freeze fast-route gradient/VJP feasibility amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; SYNTHETIC VALIDATION NOT EXECUTED

Accept EVID-0049. The frozen Full center cannot enter `COMPLEX128_FAST` because
its full-support modes are below binary64 resolution; it remains AP-only and
gradient-ineligible. This amendment supersedes EVID-0032 only for that center's
fast-route feasibility. Authorize implementation and freeze of a separate
synthetic fast-route harness with no training claim. Do not execute it yet,
relax gates, or differentiate fallback.

## DEC-0036 - Freeze synthetic fast-route VJP harness and authorize execution

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; SYNTHETIC ONLY

Accept EVID-0050. Authorize exactly one execution of the hash-bound synthetic
fast-route VJP preflight. A result applies only to the algebraic fast-domain
fixture; it cannot authorize Full-center training, AP differentiation,
publication training, threshold approval, selection, or final-test access.

## DEC-0037 - Repair synthetic fast-route VJP harness and reauthorize v2

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; V2 NOT EXECUTED

Accept EVID-0051. Preserve the v1 failed execution as a harness failure. The
v2 runner reads the frozen tolerance field names exactly and has distinct
runtime-attempt provenance. Authorize exactly one later v2 synthetic preflight
execution. No Full-center gradient claim, training, fallback differentiation,
threshold approval, selection, or final-test access is authorized.

## DEC-0038 - Freeze manifold-consistent C/w VJP amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; AMENDMENT NOT EXECUTED

Accept EVID-0052. The prior v2 failure arose from an independent-sector path
outside the production C4 manifold, not from a fast-gate defect. Preserve both
failed synthetic artifacts. Authorize only implementation and freeze of a
manifold-consistent synthetic VJP harness using Fixture B. Do not execute it,
relax gates, or claim Full-center training eligibility.

## DEC-0039 - Freeze manifold-consistent synthetic VJP harness

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; HARNESS NOT EXECUTED

Accept EVID-0053. The separate runner preserves the spectral-only and
manifold-consistent paths and binds their inputs before future execution. Do
not execute it until a separate lifecycle review authorizes the command. It
cannot establish Full-center training eligibility or publication readiness.

## DEC-0024 - Preserve V1 outcome and freeze prospective pointwise guard V2

Date: 2026-09-02

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0025; ACTIVE V2 METHOD

### Decision

Accept EVID-0037 as the completed V1 smoke outcome
`OPTIMIZATION_EFFECTIVELY_FROZEN`. Preserve the V1 protocol, blocked artifact,
completed artifact, states, seeds, optimizer, precision, `tau`, and all smoke
settings without rerun or retuning.

Accept EVID-0038 and freeze `pointwise-guard-v2` as a proposed, inactive
replacement. V2 admits a realized point exactly when support is rigorously
certified and the rigorous spectral-distance lower bound is strictly positive.
The reported interval half-width is diagnostic and is not charged again.
No positive engineering margin is adopted because pre-existing independent
evidence supplies none.

Authorize implementation and scoped verification of the repository-backed V2
point-certifier adapter and frozen V2 smoke runner only. The implementation
must not use midpoint order as proof, nearest-round Arb endpoints before the
decision, alter the scientific/security functional, or execute the smoke.

### Evidence

- EVID-0037
- EVID-0038
- `results/pointwise_guard_v2_methodology_review.json`
- `configs/pointwise_guard_protocol_v2.yaml`
- `docs/POINTWISE_GUARD_PROTOCOL_V2.md`

### Consequences

The exact next action is to implement the repository-backed validated V2
point-certifier adapter and frozen V2 smoke runner. Candidate `1e-13` remains
`PROPOSED_UNAPPROVED`; historical `1e-12` remains `INVALID_UNAPPROVED`.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. V2 smoke execution,
publication training, baseline selection, optimized-MB search, and final-test
access remain unauthorized.

## DEC-0025 - Authorize frozen V2 smoke execution

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; V2 SMOKE ONLY

### Decision

Accept EVID-0039. The V2 implementation is complete for its scoped matrix and
the V2 execution manifest is frozen after passing production and real Arb/FLINT
tests. Authorize exactly the manifest-bound V2 smoke runner as the next task.

Do not rerun or modify V1 evidence, change `tau`, threshold status, states,
seeds, optimizer, precision, MI, Holevo, SKR, security scope, or the frozen
model. Do not perform publication training, baseline selection, optimized-MB
search, or final-test access. At this pre-execution decision point, no V2
smoke outcome existed; the later result is recorded by EVID-0040.

### Evidence

- EVID-0039
- `configs/pointwise_guard_execution_manifest_v2.json`
- `results/pointwise_guard_implementation_v2.json`

### Consequences

The exact next permitted action is to run the frozen V2 smoke execution. The
V2 protocol remains proposed with candidate `1e-13` unapproved and historical
`1e-12` invalid/unapproved. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0026 - Accept V2 smoke usability and retain publication gate

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED LIFECYCLE DECISION; OPTIMIZATION USABLE

### Decision

Accept EVID-0040. The frozen V2 smoke satisfies the preregistered
`OPTIMIZATION_USABLE` rule: at least one committed update, zero
rollback-equivalence failures, zero provenance failures, and byte-identical
repeated traces. All pre/post point checks were admissible and all recorded
gradients were finite.

Preserve the completed V1 negative evidence and do not rerun either smoke.
This usability result changes no threshold, physical/security functional,
frozen model, or publication lifecycle authorization.

### Consequences

The project remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The still-required
gate before publication-scale experiments is explicit approval of the
candidate numerical threshold/support policy, followed by completion of the
existing frozen numerical prerequisites currently marked
`BLOCKED_FOCK_DEPENDENCY` and `BLOCKED_NUMERICAL_DEPENDENCY` for pseudoinverse,
Fock-cutoff, and baseline-selection state. No baseline selection, training,
optimized-MB search, or final-test access is authorized by this decision.

The exact next permitted action is to resolve that threshold/numerical approval
gate under a separately authorized lifecycle task.

### Evidence

- EVID-0040
- `configs/default.yaml`
- `docs/FINAL_MODEL_SPEC.md`, Section 11
## DEC-0040 - Documentation-only current model/code alignment

Date: 2026-09-10

Status: ACTIVE DOCUMENTATION DECISION; SCIENTIFIC IMPLEMENTATION BLOCKED

### Decision

Update the existing authoritative Markdown documents to distinguish the current
intended model from the current source implementation. Record the pre-action
state, post-action phase-noise chain, target physical fading factors, full
correlation interval, and the exact current code mismatches. Do not resolve
those mismatches by changing source, tests, parameters, or numerical evidence.

### Evidence

- EVID-0054
- docs/PAPER_CODE_ALIGNMENT.md
- docs/KNOWN_ISSUES.md
- docs/PROJECT_STATE.md

### Consequences

The lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Deterministic
constellation/PMF/orbit diagnostics remain permissible as non-publication
preliminary work. Target phase/channel/security/SKR figures remain blocked until
the listed implementation and numerical gates are separately authorized and
verified.

## DEC-0041 - Implement full physically admissible Z-interval Holevo maximum

Date: 2026-09-10

Status: ACTIVE IMPLEMENTATION DECISION; NUMERICAL CERTIFICATION BLOCKED

### Decision

Implement the frozen `Z_minus`, `Z_plus`, `Z_phys`, `Z_L`, and `Z_U` equations
in the active Holevo path. For every valid interval, evaluate the existing
covariance/entropy functional over a deterministic closed-interval candidate
grid and bounded refinement of every grid cell, including both boundaries;
select the maximum without assuming monotonicity. For an empty interval or
candidate physicality failure, fail closed with structured diagnostics.

### Evidence

- EVID-0056
- `src/cvqkd/holevo.py`
- `tests/test_holevo_interval.py`
- `docs/EQUATIONS.md`
- `docs/PAPER_CODE_ALIGNMENT.md`

### Consequences

`HolevoResult.z` now denotes the selected `Z_star`, and its diagnostics expose
the interval endpoints, physical bound, width, selected value, maximizing
location, and security-domain validity. The selected covariance uses Z directly.
The phase/post-action epsilon chain, policy features, source-moment backend,
and raw-SKR ordering are unchanged. The value function is only piecewise
differentiable because candidate/interval argmax changes are nonsmooth.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; existing numerical
artifacts do not certify the new target functional.

## DEC-0043 - Align the active composite channel before numerical work

Date: 2026-09-10

Status: ACTIVE IMPLEMENTATION DECISION; SCIENTIFIC MAPPINGS BLOCKED

### Decision

Use one common altitude-dependent C_n^2(h) turbulence provenance for
scintillation, effective phase, and optional AoA. Remove the legacy
constant-C_n^2 beam-wander term from the active target sampler while retaining
the equation only as a marked legacy helper. Implement the source-supported
Rician pointing, normalized lognormal scintillation, hard AoA gate, raw-T
diagnostics, and truncated physical-domain admission. Do not invent the
profile-to-phase, aperture-averaging, or turbulence-to-AoA mappings; unresolved
production choices remain explicit and fail closed.

### Evidence

- EVID-0058
- src/channel/fso_channel.py
- src/channel/scintillation.py
- src/channel/aoa.py
- tests/test_composite_channel.py
- tests/test_channel_provenance.py
- tests/test_holevo_resolution.py

### Consequences

The policy remains on (T, epsilon_base), and one post-action epsilon_total
continues to feed both MI and Holevo. Production configuration remains
blocked by unresolved profile/aperture/AoA/phase choices. Full-Z numerical
resolution is tested at 17/33/65/129 candidates but is not certified.
Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0047 - Reuse stable AP source moments for exploratory B-D subsets

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Reuse the 900-digit-stable \(C,w\) only because the exact ensemble hash is
identical across Cases A-D. Evaluate B-D on 16 active states each through the
existing full-Z path. Keep the reuse evaluation-only; do not route it into
training, certification, or publication workflows.

### Evidence

- EVID-0062
- EVID-0063
- results/exploratory_cases_BD_full_security_20260910.json

### Consequences

Cases B-D obtain bounded exploratory MI/Holevo/raw-K values. Case D retains
outage rows at K=0 and satisfies the active-fraction identity. No lifecycle
gate, physical parameter, Gram gate, or security equation was changed.

## DEC-0042 - Retain unresolved Cn_phi2 and bind canonical provenance

Date: 2026-09-10

Status: ACTIVE CONFIGURATION DECISION; AUTHOR FREEZE BLOCKED

### Decision

Retain `channel.cn_phi2_m_minus_two_thirds: null` in production
configuration. Treat `Cn_phi2` as an explicitly prescribed, scenario-level
effective representation of the same physical turbulence in `m^(-2/3)`,
separate from the legacy `cn2_m_minus_two_thirds` compatibility field and
without an evidenced mapping from an altitude-dependent `C_n^2(h)` profile.
Derive `tau_phi2` and `c_phi` from `Cn_phi2`, SI wavelength, and the resolved
link distance; do not expose an independent `c_phi` configuration value.
Persist the canonical phase provenance record in active run/checkpoint
metadata and retain existing resolved-config hash binding.

### Evidence

- EVID-0057
- `src/channel/phase_noise.py`
- `scripts/_train.py`
- `configs/default.yaml`
- `docs/PHYSICAL_PARAMETER_AUDIT.md`

### Consequences

The explicit zero and nonzero values in focused tests remain test-only, and
the separate configured/current `cn2` value is not a phase substitute. Target
entry points continue to fail closed while the author value is null. The
policy input remains `(T, epsilon_base)`, the same post-action
`epsilon_total` remains the MI/Holevo input, and the full-Z Holevo interval is
unchanged. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; no
training, target evaluation, certification, or numerical approval is granted.
## DEC-0044 - Run only non-publication exploratory composite cases

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Permit Cases A--D with explicit development-only scintillation, pointing, and
AoA values, \(N=1000\) channel samples per case, and explicit zero phase. Keep
all unresolved mappings labeled exploratory. Do not invoke training, baseline
selection, final-test, certification, or the arbitrary-precision Holevo
fallback.

Accept the outage-aware active-only SKR plumbing and relative transmittance
diagnostic fix as the minimum code change required for the case harness.

### Evidence

- EVID-0059
- EVID-0060
- results/exploratory_cases_20260910.json

### Consequences

Channel and MI preflight behavior may be reported as exploratory only. Holevo,
active-K, and outage-weighted-K remain unreported because the complex128 fast
gate fails and the fallback is evaluation-only. Lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0046 - Accept one bounded AP-backed Case A security result

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the one-state Case A AP-backed source-moment/full-Z result as
EXPLORATORY_EVALUATION_ONLY. Preserve the complex128 fast gate, keep AP
evaluation-only, and do not generalize the result to Cases B-D, learned
training, certification, or publication.

### Evidence

- EVID-0062
- results/exploratory_case_A_full_security_20260910.json
- src/cvqkd/gram_moments.py
- scripts/full_support_c4_worker.py

### Consequences

Case A has a finite exploratory \(C,w,Z_\star,\chi_{BE}^{ub},K\) result.
The numerical artifact remains bounded to one exact ensemble and a single
evaluation-only AP route. Lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0045 - Preserve the Gram fast gate after numerical root-cause audit

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify the exploratory uniform-ensemble failure as
FLOATING_POINT_ROUNDOFF plus NUMERICAL_ILL_CONDITIONING, not probability
support loss, constellation collapse, or an implementation-indexing bug.
Preserve the complex128 gate, do not add clipping/jitter/support truncation, and
do not enable the arbitrary-precision fallback for training. Keep the fallback
evaluation-only and require a separate bounded one-state security run before
claiming exploratory Holevo/K completion.

### Evidence

- EVID-0061
- results/exploratory_cases_20260910.json
- src/cvqkd/gram_moments.py
- scripts/full_support_c4_worker.py

### Consequences

No numerical tolerance or security formula changed. The current exploratory
cases have finite MI/channel metrics but incomplete Holevo/K metrics. Lifecycle
remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0048 - Classify complex128 differentiable path as blocked

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify the current differentiable complex128 full-support source-moment path
as EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128 for the investigated exact
256-state ensemble. Preserve the gate and AP evaluation-only boundary. Do not
implement clipping, jitter, support reduction, tolerance weakening, or an
unproven reformulation.

### Evidence

- EVID-0064
- src/cvqkd/gram_moments.py
- src/cvqkd/spectral_frechet.py
- tests/test_holevo_interval.py
- tests/test_gradients.py

### Consequences

The AP-backed forward evaluator is exploratory only. Adaptive training remains
unauthorized and the next work is a separately scoped differentiable numerical
design investigation.

## DEC-0049 - Stop AP custom-backward validation at the fallback definition mismatch

Date: 2026-09-10

Status: SUPERSEDED BY DEC-0050; HISTORICAL FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify this feasibility run as `AP_CUSTOM_BACKWARD_NOT_VALIDATED`. Preserve
the isolated AP implicit-adjoint prototype and the complex128 production gate,
but do not integrate the prototype into `gram_moments.py`, `holevo.py`, or
`trainer.py`. Do not repair or regenerate the existing AP/security artifacts in
this task.

The stop condition is a newly verified forward-definition mismatch: the AP
worker's `aa=sr*x2.T` does not implement the current C4 reference
(G_sD G_{s-1}^{-1}=x2.T), so its stored (w) cannot be used as the forward
target for custom-backward validation. The small-fixture adjoint test is not
enough to authorize a 256-state gradient claim.

### Evidence

- EVID-0065
- `results/ap_custom_backward_case_A_20260910.json`, SHA-256
  `dc11c998f755d328906558b949444e4bf45a088657938f7b4b1c1a13daaf58d4`
- `src/cvqkd/ap_custom_backward.py`
- `tests/test_ap_custom_backward.py`
- `src/cvqkd/gram_moments.py`, `tests/test_full_support_c4_gram_backend.py`
- `scripts/full_support_c4_worker.py`

### Consequences

The prototype remains experimental and evaluation-only. No Case A AP
directional finite-difference suite, torch PS/GS/V_A chain, full-Z backward,
optimizer step, training, certification, final-test access, or publication-scale
evaluation is authorized. Existing worker-backed C/w/security artifacts remain
historical pending one separately scoped AP fallback correction and artifact
rebind. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive
training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

## DEC-0050 - Accept corrected AP worker and bounded Case A rebind

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the one-line AP worker correction `aa=x2.T` as matching the frozen
production C4 (A_s=G_sDG_{s-1}^{-1}) definition. Accept the corrected 800/900
digit Case A source moments and the bounded corrected full-Z result as current
exploratory evidence only. Mark all old worker-backed (w)-dependent artifacts
`SUPERSEDED_WRONG_AP_W`; retain their old numbers for provenance.

Do not recompute Cases B-D in this task. Keep the custom backward isolated with
status `PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION`.

### Evidence

- EVID-0066
- `results/ap_worker_corrected_case_A_20260911.json`, SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`
- `results/exploratory_case_A_full_security_corrected_20260911.json`, SHA-256
  `a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa`
- `tests/test_ap_worker_equivalence.py`

### Consequences

Corrected Case A has (w=0.018327610474963502...),
([Z_L,Z_U]=[0.2914192733053753,0.2934784546975139]),
(chi_{BE}^{ub}=0.01518919002933572), and raw
(K=0.004757635492383283). These remain bounded exploratory values; no
publication, certification, training, final-test, or B-D authorization follows.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0051 - Accept corrected bounded B-D security rebind as exploratory evidence

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the newly generated B-D artifact as a corrected, bounded,
evaluation-only source-moment/full-Z exploratory rebind. It uses the accepted
corrected AP `(C,w)`, the exact uniform 256-state ensemble hash, direct seeded
physical channel samples, active-only statewise MI/Holevo evaluation, and raw
signed SKR with no clipping. Case D outage rows remain outside MI/Holevo and
have exact `K=0`.

Because the historical ignored B-D artifact and its exact index roster were
unavailable in this checkout, the new artifact uses and records the declared
`evenly_spaced_active_rows_v1` reconstruction rule. Its values must not be
described as a publication-scale or exact historical-subset result.

### Evidence

- EVID-0067
- `results/exploratory_cases_BD_full_security_corrected_20260911.json`,
  SHA-256 `c7c88940e5219a191277f358318eb756dcdeea61d6a6e546d0286af42a3c2ba0`
- `scripts/recompute_corrected_bd_security.py`
- Corrected worker SHA-256
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`

### Consequences

The corrected A-D exploratory table is now complete for the bounded
development subset. B, C, and D have negative mean raw K under corrected w;
those signed values are retained and are not clamped. The lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, adaptive training remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`, and the remaining blocker is corrected AP
custom-backward directional validation. Do not run that validation as part of
this rebind.

## DEC-0052 - Stop corrected AP custom-backward validation after bounded PS failure

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept the cheap independent four-state checks and the four physical-mapping
structure checks as exploratory diagnostics only. Do not accept a 256-state
custom-backward gradient claim. Stop the target suite after one bounded PS
direction: the corrected AP reference resolved all 256 modes, but the custom
combined VJP differed materially (`3.3995565604790261e+102` versus
`0.0017741810692945003680`). Do not launch GS-real, GS-imag, V_A, or full-Z
backward jobs.

Classify the validation as `AP_CUSTOM_BACKWARD_NOT_VALIDATED` and retain the
custom path isolated from production. The measured custom reverse runtime was
`25653.3898618 s`, so ordinary adaptive training remains closed independently
of the correctness failure.

### Evidence

- EVID-0068
- `results/ap_custom_backward_corrected_directional_validation_20260911.json`,
  SHA-256 `60d6da12dc23bb8d4d086fef6ab3a349201c33745d0a930ba37be8b76203bc14`
- `results/ap_custom_backward_ps_target_attempt_20260911.json`,
  SHA-256 `3c8b87793b76abc82e0ecc89a5e33fb9c513dec749cdbbd2e4e2f5b4f3856d2a`
- `scripts/validate_corrected_ap_custom_backward.py`,
  SHA-256 `6fa71c0d1d055627a4fa93af79e12617d166712bd0ed14534319d394190e8db9`
- Target-attempt runner SHA-256
  `3f24854ccf9906a42bde8132f8e6d175ca7a49c928c2caf32027c5914a767244`
- Corrected worker SHA-256
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Corrected AP source-moment artifact SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`

The old custom-backward artifact remains `SUPERSEDED_WRONG_AP_W` and is not
an oracle.

### Consequences

Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`; the single
remaining blocker is a root-cause fix and fresh full-support validation of the
AP reverse path at the `~10^-618` eigenvalue scale. No training, optimizer
step, channel change, security-equation change, final-test access, or
publication-scale evaluation was performed.

## DEC-0053 - Prefer an exact C4 tangent audit before reverse repair

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Treat the full-support differentiable source-moment problem as unresolved at
the target spectrum. Do not patch the custom reverse by changing transpose
conventions based only on the \(10^{102}\) output. The corrected worker's
ordinary transpose is part of its solve orientation; the correct next
diagnostic is an independent arbitrary-precision forward tangent.

The approved research direction is to preserve the exact C4 C/w functional
while evaluating
\(B_sS_{s-1}=S_sD\) and
\(A_sG_{s-1}=G_sD\) by constrained solves, and differentiating those
constraints together with the square-root Sylvester equation. A compiled
multiprecision backend is conditional on passing the tangent and local
adjoint tests.

### Evidence

- EVID-0069
- docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md
- Corrected target result and custom failure in EVID-0068

### Consequences

Keep the AP custom backward isolated and classified
AP_CUSTOM_BACKWARD_NOT_VALIDATED. Do not start GS, \(V_A\), full-Z backward,
adaptive training, or publication-scale evaluation until the source-moment
three-way validation passes and runtime is separately acceptable. The
security equations, full support, corrected C/w, and complex128 gate remain
unchanged.

## DEC-0054 - Accept one bounded C4 forward tangent diagnostic; keep training closed

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept the isolated C4 constrained-solve forward tangent as
`CONSTRAINED_TANGENT_VALIDATED` for the single recovered Case-A PS direction.
The exact full-support C/w functional is unchanged. The tangent may be used
as a diagnostic boundary, but not as a production gradient or adaptive-
training authorization. Keep the old AP custom reverse classified
`AP_CUSTOM_BACKWARD_NOT_VALIDATED` and do not begin reverse repair, GS-real,
GS-imaginary, V_A, full-Z backward, optimizer steps, or training in this task.

The 800-digit target row resolved 256/256 modes and matched the prior corrected
AP reference within 1e-8 for dC, dw, and combined dJ. The 200/400/600 rows
failed closed before full support was resolved. The target constrained-only
row took 1181.1304 seconds, so the exact tangent is not computationally
practical for the proposed adaptive workload. The target explicit R/J
comparison was not completed within the bounded runtime window; cheap-fixture
explicit/constrained identities and residuals passed.

### Evidence

- EVID-0070
- `results/c4_constrained_forward_tangent_20260911.json`, SHA-256
  `023fb41db59a079314f639ff47513890445c7a7b885c17273a5f3df52b71ddcb`
- `src/cvqkd/c4_constrained_tangent.py`, SHA-256
  `a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258`
- `scripts/validate_c4_constrained_tangent.py`, SHA-256
  `de7f5e9c6ec9060c5135092aba89864b46bcd019884f10c34514af86405b6c70`
- `tests/test_c4_constrained_tangent.py`, SHA-256
  `6763a7c82c74929a4e4ba3b06df4376fbf027abc417d3dc69a2a4fe711f59c09`
- Prior corrected PS direction hash:
  `e274073c5038308b521bd1a348c932a4a249cd5fc59a006b7611911e2be6dd87`

### Consequences

Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`, and the project
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The remaining
numerical blocker is a complete, validated, and computationally practical
full-support source-moment gradient boundary, including the reverse path.
The next permitted task is validation of the remaining source directions or a
separately scoped practical exact-backend investigation; neither authorizes
training or final-test access.

## DEC-0055 - Accept bounded four-direction C4 forward tangent; keep adaptive training closed

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept the bounded GS-real, GS-imaginary, and V_A constrained-solve
forward-tangent rows as passing when combined with the recovered PS row in
EVID-0070. The target study used the existing GS/V_A transmitter mapping,
the corrected AP worker, 800 AP digits, and one h=10^{-4} central
finite-difference endpoint pair per direction. It preserved positive
probabilities, 256 unique states, full 256/256 support, the corrected C/w
functional, and the physical normalization; phase remained disabled.

The aggregate classification is
`FULL_SOURCE_FORWARD_TANGENT_VALIDATED`, but it is diagnostic-only. The exact
tangent is not computationally practical for the proposed adaptive workload:
the three remaining direction totals were 2001.04 s, 2878.94 s, and 1795.96 s
respectively, in addition to the prior 1181.13 s PS tangent. Keep the old AP
custom reverse classified `AP_CUSTOM_BACKWARD_NOT_VALIDATED`. Do not start
reverse repair, full-Z backward, optimizer steps, training, final-test access,
publication-scale evaluation, or security evaluation from this decision.

### Evidence

- EVID-0071
- `results/c4_remaining_forward_tangents_20260911.json`, SHA-256
  `471e04862ef5cfaaa3ee65c01d229285ce43f93cb4c08ca8bfc4a198a4414566`
- `scripts/validate_remaining_c4_forward_tangents.py`, SHA-256
  `a829e608a73d91a08222753f7660a8303186f9d6b618c26d640331b19641534a`
- `src/cvqkd/c4_constrained_tangent.py`, SHA-256
  `a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258`
- `tests/test_c4_constrained_tangent.py`, SHA-256
  `a6b8024aece7257b803c20fdc8ba48cd046d13b012b80f09888ae8c375d08c78`
- Corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Exact ensemble SHA-256:
  `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`

### Consequences

The project lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and
adaptive readiness remains `NOT_READY_FOR_ADAPTIVE_TRAINING`. The single
remaining blocker is a validated and computationally practical reverse/adjoint
of the constrained C4 source-moment system. The next task is a separately
scoped practicality study of that blocker; this decision does not authorize
executing it, full-Z backward, or training.

## DEC-0056 - Skip mpmath reverse; build compiled multiprecision prototype

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Select exactly
SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE.

The solve-based reverse derivation for the validated C4 constrained forward
graph is mathematically sound on paper: it requires eight cached primal right
solves, eight adjoint right solves, and four self-adjoint square-root
Sylvester solves, without explicit inverse matrices. The estimated tape is
manageable, but the target approximately 1e-618 eigenvalue scale and the
minutes-long forward tangent measurements make an mpmath reverse implausible
for the current runtime gates. The reverse has not been implemented or
validated.

Authorize only a separately scoped compiled primitive benchmark. Keep full
reverse execution, full-Z backward, optimizer steps, adaptive training,
baseline selection, final-test access, security evaluation, and
publication-scale evaluation closed.

### Evidence

- EVID-0072
- docs/CONSTRAINED_REVERSE_PRACTICALITY_STUDY.md
- Report SHA-256:
  5a8bfb0444d1658fed55ad6f1a13cf29c7b4c53bf3614e676db1a97a3a3c0f16

### Consequences

The project lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and
adaptive readiness remains NOT_READY_FOR_ADAPTIVE_TRAINING. The next
permitted action is one C++17 64x64 one-sector primitive bundle at 1250,
1450, and 1650 decimal digits with residual, inner-product, and timing
gates. This decision does not authorize implementing the complete reverse.

## DEC-0057 - Refine the compiled reverse prototype backend

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept EVID-0073 and use the deep research report as the current numerical
and mathematical decision boundary for the full-support source-moment
gradient. Refine DEC-0056's compiled multiprecision prototype choice to:

1. use C++17 with MPFR/MPC point arithmetic for the primary constrained
   right-solve and Sylvester-adjoint benchmark; and
2. use Arb/acb_mat through FLINT as an independent enclosure/reference mode
   after the point primitives pass.

Retain the exact C4 constrained equations, the corrected complex \(u\), the
weighted \(w\), and all 256 full-support states. Do not use thresholded
eigenvalues, jitter, a pseudoinverse, or an unproved reformulation.

This decision authorizes only the already scoped one-sector primitive
benchmark. It does not authorize a complete reverse VJP, full-\(Z\)
backward, optimizer step, adaptive training, baseline selection, final-test
access, publication-scale evaluation, or a new security claim.

### Evidence

- EVID-0073
- docs/DEEP_RESEARCH_SOURCE_MOMENT_REVERSE_GRADIENT.md, SHA-256
  f6bc18fe28747ee123514d69171f55f49383975e732f51e8dd5a40785bd97996
- DEC-0056 and docs/CONSTRAINED_REVERSE_PRACTICALITY_STUDY.md

### Consequences

The lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive
readiness remains NOT_READY_FOR_ADAPTIVE_TRAINING. The next task is a
narrow C++17 64x64 one-sector benchmark at 1250, 1450, and 1650 decimal
digits with right-solve, adjoint right-solve, square-root Sylvester,
residual, inner-product, factor-reuse, and timing gates. The report's
sub-10-second full-state discussion remains an unproven engineering target,
not a project result.

## DEC-0058 - Keep bounded analysis figures diagnostic and stop before publication run

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED ANALYSIS DECISION

### Decision

Accept EVID-0074 as a completed, analysis-only figure workflow. The isolated
training surrogate may be used as a search aid because it passed all four
directional calibration gates and the nearby full-support checks. Exact
corrected AP source moments and the existing full-physical-Z Holevo path remain
the only security authority for the reported anchors.

Do not promote the surrogate search values to security results. Do not begin a
publication-scale run from these figures: all active exact raw-K anchors are
negative, and Full has no meaningful exact-bin advantage over the fixed MB
baseline. Preserve the phase-disabled label, corrected w, full-Z maximization,
outage K=0 rule, and unresolved production channel/phase mappings.

### Evidence

- EVID-0074
- `docs/ANALYSIS_FIGURES_REPORT_20260911.md`
- `results/analysis_figures_artifact_20260911.json`

### Consequences

The analysis status is `ANALYSIS_FIGURES_READY`; the scientific conclusion is
`MIXED_PRELIMINARY_SUPPORT`; and the publication status remains
`NOT_PUBLICATION_CERTIFIED`. The next recommended investigation is the
Full-vs-MB surrogate/objective mismatch, not a publication-scale run. This
decision does not authorize reverse repair, full-Z backward, adaptive
training, baseline selection, final-test access, or publication-scale
evaluation. DEC-0057's separately scoped compiled primitive benchmark remains
unexecuted and outside this analysis result.

## DEC-0059 - Repair the full-Z search objective before interpreting learned gains

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED ANALYSIS DECISION

### Decision

Accept EVID-0075 and the accompanying deep-research report as the current
decision boundary for the Full-vs-MB blocker. The primary cause is the
analysis search objective, not arbitrary precision or source-moment
differentiation: its smooth `tanh` representative evaluates `Z` below `Z_L`
in all 16 active grid states and is not the frozen full-Z functional.

Treat the apparent proxy improvement and its PS+`V_A`/Full ranking as invalid
for scientific or security interpretation. Keep the weight audit result as a
pass for the diagnostic fixture: active mass `0.732`, outage mass `0.268`,
equal active weights `0.04575`, and total mass one. Keep raw negative rates;
do not replace the objective with `max(0,K_raw)`.

Select exactly one immediate numerical task: repair the proxy using an
interval-preserving `Z` parameterization (or the exact bounded full-Z
functional), then perform a bounded fixed-grid baseline/ranking audit and
short candidate recheck. The exact PS+`V_A` check and Full-minus-GS control
are downstream checks after this repair, not parallel next tasks.

Classify the current positive joint-adaptation novelty as
`CURRENT_NOVELTY_NOT_SUPPORTED`. Do not present Full PS+GS+`V_A` as a
positive exact full-Z result on the current evidence.

### Evidence

- EVID-0075
- `docs/DEEP_RESEARCH_FADING_FULL_Z_BLOCKER_20260911.md`, SHA-256
  `2cc9f30119903c858304567d8abf962930ce845327db70c35ef9715094d5bc99`
- `results/analysis_objective_audit_20260911.json`, SHA-256
  `bbf6389997941e8447a51261405e45fbfb0b6653a210207f8dda7d070acd6b69`

### Consequences

This decision authorizes only the bounded diagnostic objective repair and
recheck described above. It does not authorize reverse repair, full-Z
backward, adaptive training, baseline selection, final-test access,
publication-scale evaluation, or a new security claim. The lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, adaptive readiness remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`, and the separately scoped C++ primitive
benchmark from DEC-0057 remains unexecuted.

## DEC-0060 - Accept the interval-preserving full-Z objective repair

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED ANALYSIS DECISION

### Decision

Accept EVID-0076 and
`docs/REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md` as the current decision
boundary for the repaired search-objective audit. The repaired runner calls
the existing physical `[Z_L,Z_U]` construction and full-Z maximizer with only
surrogate `C,w` during search. Its candidate audit has `0/96` interval
violations, the corrected Case-A and existing anchor-equivalence gates pass,
and PS/GS/V_A gradient smoke is finite.

Classify the objective as exactly:
`FULL_Z_SEARCH_OBJECTIVE_REPAIRED`.

Do not restore the paper novelty claim: use exactly
`CURRENT_NOVELTY_NOT_SUPPORTED`. The bounded exact subset shows Full above MB
on the three selected states, but optimized PS+V_A failed closed at the
full-support AP source-moment gate, so the required PS+V_A-versus-Full ranking
is incomplete.

### Evidence

- EVID-0076
- `docs/REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md`, SHA-256:
  `b6077b4942390ea90840b463d495a3199a85fa332f21ede11e604868265b3a5c`
- `results/repaired_full_z_objective_analysis_20260911.json`, SHA-256:
  `aa94fc2032ab9d1421c3f4256cf3a7a4be6526c612797f4b162c1c8c85d98f23`
- `results/repaired_full_z_exact_jobs_20260911.json`, SHA-256:
  `52eafe5ee42af34a53b2280ddf10639fe77d50f87702ddc754ababbb06b5ad5c`
- `results/repaired_full_z_ps_va_exact_failure_20260911.json`, SHA-256:
  `27b6474a67b26755f076d3ed7569fe5fe22b3f0758df0242e059ccf4333b997f`

### Consequences

The old off-interval proxy and its learned ranking must not be used as
security or novelty evidence. The bounded repaired optimization remains an
analysis estimate only. Keep exactly
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and
`NOT_READY_FOR_ADAPTIVE_TRAINING`; do not run publication-scale training,
final-test evaluation, reverse VJP/full-Z backward, baseline selection, or a
new security claim.

The one remaining numerical blocker is the missing converged exact PS+V_A
source-moment/ranking result. The next task is to add a full-support-
preserving PS+V_A parameterization or conditioning guard and repeat only the
three-state exact AP/full-Z comparison; do not execute that task under this
decision.

## DEC-0061 - Select a one-checkpoint AP worker decomposition

Date: 2026-09-12

Status: ACTIVE FAIL-CLOSED RESEARCH DECISION

### Decision

Accept EVID-0077 and
docs/DEEP_RESEARCH_PS_VA_FULL_SUPPORT_BLOCKER_20260912.md as the current
root-cause audit for the remaining optimized PS+V_A exact source-moment
blocker. Select exactly:

INVESTIGATE_AP_WORKER_BUG

The next and only permitted numerical action for this blocker is a read-only
median-checkpoint decomposition using the direct binary64 PMF/prototype inputs,
a captured AP precision ladder, and an independently implemented C4-sector or
factorization cross-check. The matched Full median checkpoint is the positive
control. The experiment must retain unresolved rows and must not infer an exact
PS K from a failed row.

### Evidence

- EVID-0077
- docs/DEEP_RESEARCH_PS_VA_FULL_SUPPORT_BLOCKER_20260912.md, SHA-256:
  c4031394281b6529887f86fa93d7516b6d7ab7c07ce3a5f55c402f3c0a866251
- results/ps_va_full_support_blocker_diagnostic_20260912.json, SHA-256:
  8a44ca9330cca61d8a15d2457b6c1d8445b560b5776935e184de15e550f5255d
- results/repaired_full_z_ps_va_exact_failure_20260911.json, SHA-256:
  27b6474a67b26755f076d3ed7569fe5fe22b3f0758df0242e059ccf4333b997f
- results/repaired_full_z_exact_jobs_20260911.json, SHA-256:
  52eafe5ee42af34a53b2280ddf10639fe77d50f87702ddc754ababbb06b5ad5c

### Rationale

The current PS anchor has p_min around 10^-3, modest q_max/q_min, and logit
ranges below 1.51. The weighted-Gram bound does not support probability
concentration as the primary cause. PS and Full have nearly equal V_A, and the
PS anchor has no smaller physical pair spacing in the recorded audit. Direct
float.hex/fromhex transfer is an exact binary64 round trip. Both PS and Full
fail at the 300-digit diagnostic floor, but only Full is currently shown to
resolve at 800/900 digits. Therefore precision and conditioning are relevant,
but a PS-specific worker/solver failure remains unresolved and must be tested
before a guard or model-family amendment.

### Consequences

This decision supersedes DEC-0060’s proposed guard-first ordering only for the
next blocker investigation; it does not reject a guard as a possible later
response to independently confirmed conditioning. Do not add a q floor, reduce
the PS family, reformulate C,w, or increase AP precision as the sole change
under this decision.

Keep the current fail-closed full-support gate. Keep
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and
NOT_READY_FOR_ADAPTIVE_TRAINING. Do not run publication-scale training,
adaptive training, baseline selection, optimized-MB selection, final-test
evaluation, held-out evaluation, reverse VJP/full-Z backward, or any new
security or novelty claim.

## DEC-0062 - Stop dense high-precision global eigensolve; retain bounded audit

Date: 2026-09-12

Status: ACTIVE FAIL-CLOSED RESEARCH DECISION

### Decision

Accept EVID-0078 and
docs/DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md as the current
numerical-analysis decision for the PS+V_A full-support blocker.

Select exactly:

LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT

For the immediate AP-blocker classification, select exactly:

INSUFFICIENT_AP_PRECISION

The unchanged current worker now resolves the median PS case at 800/900 and
1000/1200 digits and the matched Full case at 800/900 digits. The independent
100-digit direct weighted-Gram construction reproduces the exact C4
off-block and block structure. Therefore a dense 256-by-256 eigensolve at
support-resolving precision is redundant for the current question.

The one next numerical task is a bounded read-only
RUN_INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT using direct serialized
binary64 inputs for frozen median PS+V_A and Full at 80/120/200 decimal
digits. It must record global/sector invariants, Fourier off-block residuals,
block-match residuals, resolved bulk spectrum comparisons, hashes, and
timings, with a 15-minute total budget. It is not a support certificate or a
security result and is not executed by this decision.

### Evidence

- EVID-0078
- docs/DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md,
  SHA-256:
  a6fe26730bfdd874155264d6829674c4004e6007707d8ba0258f0f9e95c47e92
- results/ps_va_ap_worker_localization_20260912.json,
  SHA-256:
  b068f2fc5a83d9acf269cff532e1f3cf218c640319b3a26bd6c4cea5876e7908
- results/ps_va_worker_instrumented_800_900_20260912.json,
  SHA-256:
  3d7dc1024f022a5a4b1121fc6ce98c5c618e6abe46c91b7adcf662c4a75e43a6
- results/ps_va_worker_instrumented_1000_1200_20260912.json,
  SHA-256:
  649ff8f2a1a8022d4eef6afa1f6be2b003e34818291a89b1bde01c28a6c927dd
- results/full_worker_instrumented_800_900_20260912.json,
  SHA-256:
  08510463a9a57c1e002129805e6f2f25c5dbf216258614623d7467650bb90bde

### Consequences

This decision supersedes DEC-0061 only for the interpretation of the
median-checkpoint blocker and the next numerical action. It does not alter
the frozen model, C/w definitions, full-support gate, physical Z interval,
security scope, or lifecycle restrictions. Do not add a probability floor,
change the PS family, alter V_A or GS, change the channel, execute reverse
work, train, select a baseline, access final data, or make a new security or
novelty claim.

## DEC-0063 - Accept bounded global audit and move to minimum sector precision

Date: 2026-09-12

Status: ACTIVE FAIL-CLOSED RESEARCH DECISION

### Decision

Accept EVID-0079 and
docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md as the completed
bounded follow-up to DEC-0062.

Retain exactly:

- Dense-global conclusion:
  `LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT`
- Immediate AP diagnosis: `INSUFFICIENT_AP_PRECISION`

The PS 80-digit independent global row passed the structural, invariant,
block, and resolved-spectrum-union checks. The PS 120-digit row timed out;
PS 200 and all Full rows were not started under the 900-second budget. The
partial result is sufficient to preserve the dense decision, but it is not a
complete six-row global comparison or a support certificate.

The bounded audit authorization is consumed. Select the next task:
`DETERMINE_MINIMUM_SECTOR_AP_PRECISION_FOR_FROZEN_PS_VA` — determine the
smallest reproducible sector-level AP precision for frozen PS+V_A, compute
exact C,w, and then evaluate only the median full-Z security point. Do not
execute that task in this decision.

### Consequences

DEC-0063 supersedes DEC-0062 only for the next numerical action. It does not
alter the frozen model, C/w equations, channel, security definition,
probabilities, geometry, or support gate. Do not run a dense high-precision
global eigensolve, add a probability floor, change the PS parameterization,
execute reverse/full-Z backward, train, select a baseline, access final data,
or make a new security or novelty claim.

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive
training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

### Evidence

- EVID-0079
- docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md,
  SHA-256:
  bf2f0d9b8c2f6b98e50ea0ab90620bb05941475c3b2400be8bc54dda28029b7f
- results/independent_global_block_audit_20260912.json,
  SHA-256:
  4adebde66edc194d1097c900f2cffffdb5302278f194c04fd8253fd2fddc292e

## DEC-0064 - Select direct fixed higher-precision sector run

Date: 2026-09-12

Status: ACTIVE FAIL-CLOSED RESEARCH DECISION

### Decision

Accept EVID-0080 and
`docs/DEEP_RESEARCH_MINIMUM_PS_VA_SECTOR_PRECISION_20260912.md` as the
numerical-analysis decision for the remaining frozen PS+V_A source-moment
blocker.

Select exactly:

```text
DIRECT_HIGHER_PRECISION_SECTOR_RUN
```

For the next source-moment computation, start the fixed ladder at 1050
decimal digits, then confirm the acceptance rows at 1250 and 1450 digits using
the existing four 64-by-64 C4 sectors and exact serialized binary64 inputs.
Then evaluate only the median full-Z point. The current frozen
`1050,1250,1450` protocol remains unchanged; 1250 is the first
acceptance-grade row after the existing 800--1200 diagnostic evidence. No
dense high-precision global
eigensolve, 1600/2000-digit escalation, mixed outcome-driven sector ladder,
Arb migration, source-moment reformulation, training, or final-test access is
authorized by this decision.

The analytic coherent-state rank result and weighted-Gram bound are
supporting reasoning only. They do not replace the full-support numerical
gate or certify `C,w` by themselves.

### Consequences

This decision does not alter the frozen model, C4 equations, probabilities,
geometry, `V_A`, channel, full-Z interval, security scope, or lifecycle. It
does not authorize execution from the decision log; the future run must emit
the specified sector residuals, source-moment rows, downstream convergence,
hashes, and fail-closed status. Adaptive sector precision is deferred because
the current protocol forbids outcome-based precision changes and a mixed
precision `w` error budget has not been specified.

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive
training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

### Evidence

- EVID-0080
- `docs/DEEP_RESEARCH_MINIMUM_PS_VA_SECTOR_PRECISION_20260912.md`, SHA-256:
  `5d9a58d8d437fe0f14756316c14a2128ce429c4d2b162204d4f7cfe3d1cc65d4`
- `docs/FULL_SUPPORT_C4_GRAM_BACKEND_PROTOCOL.md`
- `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`

## DEC-0065 - Accept converged PS+V_A median source moments and median result

Date: 2026-09-12

Status: ACTIVE FAIL-CLOSED RESEARCH DECISION

### Decision

Accept EVID-0081 and
`docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md` as the completed
execution of DEC-0064 for the frozen repaired-objective optimized PS+V_A
median candidate.

The 1050 diagnostic row resolved all four 64x64 sectors (256/256 total
support). The frozen 1250/1450 acceptance pair also resolved 256/256 and
passed the preregistered C/w criterion. Freeze the authoritative source
moments as:

```text
C_PSVA = 0.8610813007552428909072445071897962976560950806268
w_PSVA = 0.0067220381757562110710871873472856506670610666856165
```

The one permitted median full-Z evaluation passed its interval check and
returned raw `K = +0.0003801578161163992`. Exact median ranking is
`PS_VA_MEDIAN_BEST`, with the measured order PS+V_A > Full > MB.

### Consequences

This decision consumes the DEC-0064 execution authorization and supersedes
the `INSUFFICIENT_AP_PRECISION` interpretation for this frozen median
candidate only. It does not certify the poor/good states, complete the
three-state adaptive ranking, authorize retraining, baseline selection,
final-test access, publication-scale evaluation, or support a novelty claim
from one median point.

Because PS+V_A beats MB at the median, the next recommended task is a
separately authorized exact poor+good ranking only. Do not execute that task
from this decision.

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive
training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

### Evidence

- EVID-0081
- `results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`, SHA-256:
  `9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`
- `docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md`, SHA-256:
  `d1e39435c27063bae978348bedd733a28bc4eb32da86d79e5f1b6b2c3937714a`
- `results/ps_va_source_moments_1050_20260912.json`, SHA-256:
  `dd4d70a0483c8502ffefe1d81a6efa42a6b0adec64619da1d0c532cbc9720f97`
- `results/ps_va_source_moments_1250_1450_20260912.json`, SHA-256:
  `52f446062110e7a21e8138bcf7bfa8c3d11d94904bb80efde17ad43a4c5db474`
- `scripts/full_support_c4_worker.py`, SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`

## DEC-0066 - Bind the attached manuscript channel scenario for T diagnostics

Date: 2026-09-16

Status: ACTIVE CHANNEL-ONLY IMPLEMENTATION DECISION; SECURITY GATES UNCHANGED

### Decision

Use the attached manuscript's Hufnagel–Valley profile, finite-aperture
scintillation mapping, generalized pointing parameters, and explicit
zero-turbulence AoA FOV scenario in the active channel configuration. Derive
`v_sc` in the production sampler; do not use the exploratory `v_sc=0.25` as a
production value. Preserve the mixed (T=0) outage law and truncated active
domain, with no clipping or phase-noise term in (p_T).

### Consequences

The channel-only PDF/moment diagnostic is reproducible and verified. Explicit
`v_sc_override` paths remain development fixtures. This decision does not
authorize training, security/SKR evaluation, baseline selection, final-test
access, or publication claims; the phase (C_{n,\phi}^2) mapping remains
unresolved.

### Evidence

- EVID-0082
- `configs/default.yaml`
- `src/channel/scintillation.py`
- `src/channel/fso_channel.py`

## DEC-0068 - Apply supplied historical MB C,w rows to conditional new-channel diagnostic

Date: 2026-09-25

Status: ACTIVE DIAGNOSTIC DECISION; NO BASELINE SELECTION

### Decision

Use the user-supplied ten `C,w` pairs at
`nu_MB={0.02,0.05,0.075,0.0875,0.090625,0.09375,0.10,0.125,0.15,0.20}`
for a fixed `V_A=2`, `zeta=30 deg`, `tau_zen=0.92`, and legacy diagnostic
`eta_AO=0.95` sweep. Evaluate with the current discrete-modulation MI,
Holevo, covariance, and raw-SKR pipeline. Report the maximum only as a
numerical grid diagnostic; do not select a production MB baseline.

### Consequences

The sweep completed all 10 points and found the least-negative raw SKR at
`nu_MB=0.20`, `K=-0.00018194195597724065`. No security equation, channel
implementation, training path, baseline-selection gate, or lifecycle status
changed. The supplied historical C,w provenance remains a limitation.

### Evidence

- EVID-0084
- `results/mb_sweep_fixed_zeta30_VA2.csv`
- `figures/skr_vs_mb_fixed_zeta30_VA2.pdf`

## DEC-0069 - Rebind cached MB C,w diagnostic to C_n,phase^2=9.4e-18

Date: 2026-09-25

Status: ACTIVE DIAGNOSTIC DECISION; NO BASELINE SELECTION

### Decision

Replace the AO=0.95 diagnostic phase fixture `C_n,phase^2=1e-16` with the
user-selected `9.4e-18 m^-2/3` and rerun the same supplied-C,w MB sweep. Keep
all channel, PMF, `V_A`, beta, AO, MI, Holevo, and raw-SKR semantics unchanged.

### Consequences

The ten-point grid now has positive raw SKR values. The numerical maximum is
at `nu_MB=0.20`, `K=0.00004194428949251256` bits/symbol. This remains a
conditional diagnostic using historical supplied C,w rows; it does not select
a production MB baseline or authorize publication-scale work.

### Evidence

- EVID-0085
- `results/mb_sweep_fixed_zeta30_VA2.csv`
- `figures/skr_vs_mb_fixed_zeta30_VA2.pdf`

## DEC-0067 - Apply latest manuscript channel formulas and retain atmospheric fail-closed gate

Date: 2026-09-25

Status: ACTIVE CHANNEL-ONLY IMPLEMENTATION DECISION; ATMOSPHERIC SCENARIO UNSELECTED

### Decision

Update the channel interface and conditional PDF path to use direct
`tau_zen**sec(zeta)` atmospheric attenuation, `C_n^2(0)=1e-14`, the
finite-aperture denominator `lambda*Phi*sec(zeta)`, explicit `F0`, and the
manuscript beam-spread/equivalent-pointing quantities. Keep Kruse/visibility
and the old homogeneous/generalized fixtures callable only through explicitly
legacy paths. Leave production `tau_zen` null and require an author-approved
selection before configuration-driven channel generation.

### Consequences

The latest conditional channel/PDF diagnostic is reproducible, but no unique
atmospheric baseline exists yet. No SKR equation, Holevo implementation,
PS/GS/`V_A` optimization, phase-noise semantics, numerical security gate, or
lifecycle authorization changed. The project remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0083
- `configs/default.yaml`
- `configs/channel.yaml`
- `src/channel/atmospheric_loss.py`
- `src/channel/scintillation.py`
- `src/channel/pointing_error.py`
- `src/channel/fso_channel.py`

## DEC-0070 - Accept synthetic Adam diagnostic; keep physical optimizer unverified

Date: 2026-09-26

Status: ACTIVE DIAGNOSTIC DECISION; PHYSICAL TEST NOT RUN

### Decision

Accept TEST 1 as evidence that central finite differences, sigmoid chain rule,
Adam sign/moments, parameter updates, and rollback plumbing function on the
known synthetic objective with `V_A` range `(0.1,4.0)`. Do not run or claim
physical TEST 2 until exact ensemble-matched C,w exist for every FD and dense
grid point. Consequently keep joint TEST 3 `NOT RUN`.

### Consequences

The optimizer implementation is synthetically functional, but physical SKR
optimization is unverified. Do not interpolate C,w, call the tabulated maximum
a continuous optimum, select a baseline, or change lifecycle authorization.

### Evidence

- EVID-0086
- `results/diagnostic_mb_va_adam/diagnostic_report.json`

## DEC-0071 - Accept exact common-ensemble evaluator; stop TEST2 at FD readiness

Date: 2026-09-27

Status: ACTIVE DIAGNOSTIC DECISION; TEST2 ADAM NOT RUN

### Decision

Use `nu_mb_repo=42.5*nu_mb_raw` and require one exact binary64 ensemble hash
across MI, C4-Gram source moments, Holevo, and SKR. Permit source-moment cache
reuse only when the exact ensemble identity, convention, implementation
fingerprints, numerical settings, and precision ladder match. Preserve the
historical cached artifacts but classify their SKRs as
`SUPERSEDED_INVALID_COMMON_ENSEMBLE`.

Accept the bounded seven-point exact landscape as diagnostic evidence only.
Do not run nu-only Adam because both exact FD rows around the coarse best are
unresolved against paired CRN uncertainty and fail stability. Keep TEST3
`NOT RUN`.

### Consequences

The repository no longer needs a sparse C,w table to evaluate an arbitrary MB
ensemble, but the current `N_MC=2048` physical derivative is not ready for
Adam. A further run requires a prospectively fixed MI-noise reduction plan;
tightening h or weakening the readiness gate is not accepted.

### Evidence

- EVID-0087
- `results/exact_mb_test2/run_report.json`
- `results/exact_mb_test2/coarse_landscape.csv`
- `results/exact_mb_test2/finite_difference.json`

## DEC-0072 - Accept deterministic MI certification; keep full-SKR search closed

Date: 2026-09-27

Status: ACTIVE NUMERICAL DIAGNOSTIC DECISION; NO OPTIMIZED-MB SEARCH

### Decision

Accept the deterministic Gauss-Hermite MI path and its raw-`nu` autodiff
certification. Use the exact product acceleration only because the repository
PMF and 256-QAM geometry factorization were independently checked. Retain the
Monte-Carlo evaluator only as an independent validation path.

Do not run the full exact-SKR bounded search or Adam in this task. The current
project lifecycle does not authorize optimized-MB search/baseline selection,
and deterministic MI alone does not differentiate the expensive AP Holevo
source-moment fallback.

### Consequences

The noisy-MI finite-difference blocker is removed for `I_AB`; it is not removed
for the full `K=beta I_AB-chi_BE` objective. The next optimization task must
preserve exact C,w cache identity and separately address the Holevo derivative
cost/readiness.

### Evidence

- EVID-0088
- `results/exact_mb_test2a/run_report.json`
- `results/exact_mb_test2a/autodiff_vs_fd.csv`
- `results/exact_mb_test2a/mc_vs_gh.csv`

## DEC-0073 - Classify old MI trend as stochastic and block unauthorized SKR search

Date: 2026-09-27

Status: ACTIVE NUMERICAL DIAGNOSTIC DECISION; BOUNDED SEARCH NOT RUN

### Decision

Classify the old coarse MI variation as `STOCHASTIC_COARSE_ONLY`: its largest
reconstructed deviation from deterministic GH was `2.742` standard errors,
while the 65536-sample MC/GH cross-check had maximum z-score `0.3857`.

The fixed-V_A low-SNR deterministic MI is effectively invariant over the
tested MB range, so the old apparent MI trend must not be used as a physical
deterministic trend. Replace old MC MI with GH MI for any future deterministic
SKR comparison.

The exact arbitrary point evaluator is ready, and Holevo autodiff is not
required for a derivative-free scalar search. Do not execute that search now:
the current lifecycle does not authorize optimized-MB search or baseline
selection. Keep TEST2 Adam and TEST3 `NOT RUN`.

### Evidence

- EVID-0089
- `results/exact_mb_reconciliation/run_report.json`
- `results/exact_mb_reconciliation/same_point_reconciliation.csv`

## DEC-0074 - Record authorized MB boundary and stop at hard physical domain

Date: 2026-09-27

Status: ACTIVE AUTHORIZED EXACT-MB SUB-STAGE; FINITE OPTIMUM UNRESOLVED

### Decision

Recognize the author authorization for the restricted exact-MB optimization and
asymptotic-certification sub-stage without changing the global publication
lifecycle. Evaluate finite positive-PMF points until the existing hard
peak-photon domain rejects the normalized ensemble.

The exact landscape increases from `nu_raw=0.20` to `.25`; `.30` and above
fail closed on `n_peak_photons=30`. No interior turnover or valid bounded-search
bracket exists before that boundary. Do not run a scalar optimizer or call the
boundary point an optimum.

Keep the four-symbol QPSK-like calculation quarantined as an asymptotic
reduced-support diagnostic; it does not replace finite-positive-PMF production
source moments.

### Evidence

- EVID-0090
- `results/exact_mb_asymptotic/extended_landscape.json`
- `results/exact_mb_asymptotic/asymptotic_four_state_diagnostic.json`

## DEC-0079 - Accept historical exact distance envelope as diagnostic only

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR DIAGNOSTIC; NOT PUBLICATION FIGURE

### Decision

Accept the three-curve historical exact distance envelope under EVID-0095.
The MB-AO curve has only a historical-exact operation-distance estimate at
31.409924920888173 km from the [31,33] km bracket. Uniform and MB-noAO have
no sign change on the evaluated grid. Do not call the estimate a final
publication operation distance, and do not promote the envelope to a global
baseline/PCS result.

No new C,w was computed; no historical C,w was migrated.

### Evidence

- EVID-0095
- `results/skr_vs_link_distance/historical_exact_distance_plot.png`
- `results/skr_vs_link_distance/historical_exact_distance_plot.pdf`
- `results/skr_vs_link_distance/historical_exact_operation_distance_summary.csv`

## DEC-0078 - Accept historical C,w audit; do not migrate records yet

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR READ-ONLY AUDIT; MIGRATION NOT AUTHORIZED

### Decision

Accept EVID-0094 as the repository-wide C,w inventory. Do not compute new
source moments and do not copy historical rows into the active exact cache.
Only seven current distance-roster combinations have a safe current
hash-bound exact match; 139 feasible roster combinations remain unmatched.

The large historical inventory contains downstream copies, unhashable records,
and 148 explicitly superseded/wrong-AP-w records. Their presence is evidence
for provenance reconstruction, not permission to reuse. A later author review
must approve any `NEEDS_ONE_POINT_VALIDATION` or migration action.

### Evidence

- EVID-0094
- `results/skr_vs_link_distance/historical_source_moment_audit.csv`
- `results/skr_vs_link_distance/historical_source_moment_matches_current.csv`
- `results/skr_vs_link_distance/historical_source_moment_duplicates.csv`
- `results/skr_vs_link_distance/historical_mb_exact_pairs.csv`

## DEC-0077 - Record AP timeout blocker and preserve fail-closed coverage

Date: 2026-09-28

Status: BLOCKED_BY_ENVIRONMENT; GLOBAL OPTIMUM UNRESOLVED

### Decision

Accept the completed AP rows as exact evaluation evidence only. The priority
batch improved coverage to `19/143` global, `26/59` local, `9/18` boundary,
and `8/43` uniform, but the remaining arbitrary-precision jobs hit the
existing one-hour subprocess timeout or remain uncomputed. Keep all missing
points explicitly failed/incomplete; do not infer their C,w, do not run
boundary refinement, do not select the uniform baseline, and do not claim a
global optimum.

The timeout is an environment/runtime blocker in the existing AP route, not a
license to weaken precision, support, residual gates, or the source cache
identity. A future continuation may resume the same cache with a separately
authorized runtime decision; the current mathematical protocol is unchanged.

### Evidence

- EVID-0093
- `results/joint_mb_va_global/ap_coverage/local_failed_or_incomplete.csv`
- `results/joint_mb_va_global/ap_coverage/ap_batch_timeout_summary.json`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary_failed_or_incomplete.csv`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform_failed_or_incomplete.csv`

## DEC-0076 - Record fail-closed global joint coverage; keep optimum unresolved

Date: 2026-09-27

Status: ACTIVE AUTHORIZED DIAGNOSTIC; GLOBAL OPTIMUM UNRESOLVED

### Decision

Accept the cache-bound global joint diagnostic as evidence of coverage and
integrity only. The 143-point feasible grid, 18-point boundary grid, and
43-point uniform scan are not fully exact because the shared AP source cache
contains only 15, 5, and 5 corresponding rows. Keep the classification
`GLOBAL_OPTIMUM_UNRESOLVED`; do not call `(0.24,1.95)` a global optimum, do
not select the uniform baseline, and do not convert the sparse comparator
decomposition into a gain claim.

The runner is cache-only by default and reports missing exact source moments
instead of using interpolation or a surrogate. Brent/golden-section and any
continuous derivative-free search remain `NOT RUN` until the exact boundary
coverage is complete. Adam remains prohibited for this stage.

### Evidence

- EVID-0092
- `results/joint_mb_va_global/run_report.json`
- `results/joint_mb_va_global/global_landscape.csv`
- `results/joint_mb_va_global/boundary_search.csv`
- `results/joint_mb_va_global/uniform_optimized_baseline.csv`

## DEC-0075 - Accept joint MB/V_A exact landscape; do not claim global optimum

Date: 2026-09-27

Status: ACTIVE AUTHORIZED JOINT DIAGNOSTIC; GLOBAL OPTIMUM UNRESOLVED

### Decision

Accept the exact feasible-domain and sparse joint MB/V_A landscape under the
author's restricted authorization. Preserve the curved peak-feasible domain,
recompute phase noise for every V_A, and use exact common-ensemble C,w/Holevo.

The local exact stencil identifies `(nu_raw,V_A)=(.24,1.95)` as the best tested
local point with `SKR=2.1544608008872113e-05`, but the global search is not
complete. Do not call this pair the global optimum or select a baseline.

No Adam, interpolation, surrogate, or physical/security equation change was
used.

### Evidence

- EVID-0091
- `results/joint_mb_va/joint_landscape.csv`
- `results/joint_mb_va/local_refinement.csv`
## DEC-0080 - Stop aperture search after tested range remains non-positive

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR DIAGNOSTIC STOP; NO APERTURE SELECTED

Accept EVID-0096 as the bounded receiver-aperture sensitivity diagnostic.
At the minimum physical distance, the tested diameter range `0.08--0.16 m`
did not make all three historical exact envelopes positive: Uniform and MB
without AO remained negative at every tested diameter. Stop as requested.

Do not launch the full distance sweep, change phase/noise/channel/security
parameters, widen the aperture range, migrate historical C,w, or compute new
C,w under this decision. A continuation requires an explicit author-approved
aperture range or a separate parameter decision. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0096
- `results/skr_vs_link_distance/aperture_all_positive_diagnostic/aperture_sensitivity.csv`
- `results/skr_vs_link_distance/aperture_all_positive_diagnostic/selected_aperture_metadata.json`
## DEC-0081 - Stop phase-noise-only search when Uniform remains negative

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR DIAGNOSTIC STOP; ALL-POSITIVE THRESHOLD UNRESOLVED

Accept EVID-0097 as a phase-noise sensitivity diagnostic at the original
`D_r=0.08 m` aperture. Lowering `C_n,phi^2` from `9.4e-18` to `1e-18`
makes MB-with-AO and MB-without-AO positive at 19 km, but Uniform remains
negative. The all-positive threshold is therefore not found in the authorized
sweep.

Do not change `epsilon_ch`, beta, aperture, `eta_AO`, detector parameters, or
security formulas, and do not launch the full distance sweep. Any continuation
requires an explicit author decision about another parameter or a wider phase
range. No new C,w was computed. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0097
- `results/skr_vs_link_distance/phase_noise_sensitivity/phase_sensitivity.csv`
- `results/skr_vs_link_distance/phase_noise_sensitivity/phase_sensitivity_report.json`
## DEC-0082 - Accept forensic diagnosis; do not claim Uniform optimum

Date: 2026-09-30

Status: ACTIVE DIAGNOSTIC DECISION; GLOBAL UNIFORM OPTIMUM UNRESOLVED

Accept EVID-0098 as a read-only diagnosis of the current low SKR. The primary
bottleneck is total optical loss, especially the small receiver/large beam
coupling, followed by excess noise relative to the Uniform security bound.
Physical distance alone is not the relevant comparison with Sayat 2024.

Do not claim that no continuous `V_A` can make Uniform positive: only eight
exact Uniform points exist. Do not interpolate C,w, extend the V_A domain,
select a baseline, or launch a new AP campaign from this decision. Detector
efficiency/noise remains absent from the ideal-heterodyne repository model and
must not be inserted as an ad hoc correction.

No channel/security equation, source moment, training state, final-test state,
or lifecycle gate changed. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence

- EVID-0098
- `results/hap_uav_sayat_forensics/FORENSIC_DIAGNOSIS.md`
- `results/hap_uav_sayat_forensics/forensic_report.json`

## DEC-0163 - corrected three-moment isolated implementation; STOP (2026-10-13)

Authority: userattachment82ff4829 explicitly preserves raw Eq10 and Eq20,
selects active conditioning with AoA atom retained, rho0, phaseOFF, centered
MB/VA=2n, corrected effective excess noise, DBL interval and discrete mixture MI.
EVID-0180 supports isolated namespace only, not a change to frozen/historical
experiment scope. New src modules remain outside src/channel and src/cvqkd.
Use existing hash-matched C,w only; payload bytes also bind protected baseline.
Selected receiver convention is trusted, R=.7/xi_det=.0135. No verified receiver
Holevo exists; do not substitute ideal entropy. Final status
BLOCKED_BY_SCIENTIFIC_MODEL, no corrected production reference SKR launched.
Keep raw/literal outputs and all old caches/results. No optimization/AP/sweeps,
ObjectiveC restart, final-test/publication or automatic commit/push. Resolve
receiver security/provenance/numerical prerequisites under a fresh scoped request.
Requested (37)(2) PDF unavailable; supplied equationtask authoritative, metadata
unverified version recorded. Frozen-hash historical mismatch remains unchanged.

## DEC-0164 - ideal one-point diagnostic complete; STOP (2026-10-13)

Authority userattachment6abbafa6 explicitly selects idealheterodyne R1/xiDet0,
chihet1; overrides previous STOP only for one reference candidate, tests/report.
Accept EVID-0181 as software/algebra/onepoint diagnostic evidence. Keep previous
trusted config, corrected core, raw Eq10/Eq20, historical/literal modes/caches/results.
Actualmixture samplingSE target failed; do not increase budget or relax tolerance
automatically. Signed SKR estimates remain negative and explicitly diagnostic.
EffectiveGaussian discrete MI/SKR is separately labeled approximation; no silent
fallback. Numerical interval max not a rigorous global enclosure/securitycertificate.
No trustednonideal implementation, AP/source recalculation/AO/182/26/restartC or
training/final-test/publication/commit/push. Deliver report and STOP; any precision
expansion or optimization needs a fresh scoped request. Frozen specs untouched.

## DEC-0165 - negative-SKR causal diagnostic records a configuration mismatch (2026-10-13)

Authority: explicit user attachment `f386aec4-dfab-449a-85f6-be325a3dfac3`.

Accept EVID-0182 as a one-reference diagnostic with existing C,w and mixture MI,
read-only channel/provenance checks and unchanged historical point reproduction.
The historical and
corrected modes share the base D55 geometry and exact source identity, but their
derived PDF coefficients, scintillation convention, support, and moment
conditioning differ. Keep the final status `CONFIGURATION_MISMATCH`; do not
describe the cross-mode SKR change as a like-for-like physical-channel effect.

The stored algebra is internally consistent: corrected fading noise is
`0.42343717270144676` versus channel noise `0.0044251049417631805`, historical
and corrected covariance/Holevo/SKR values reproduce their artifacts, and the
`lambda_2` entropy term dominates the Holevo increase. Corrected mixture MI
precision remains unresolved (`SE=0.019468676410223464` versus target `0.002`),
so the negative corrected K remains a signed diagnostic rather than a validated
security lower bound. A future like-for-like one-point comparison or precision
work requires a fresh scoped request; do not optimize or sweep automatically.

Completion clarification: .1558491966743379 is retained, unnormalized mh²;
corrected full-support raw mh² is .1694819790377013. Aperture, Rytov, tail cut
and conditioning sensitivities are explicitly separated. Eight current tests
and 3663 protected/13 prior ideal output hashes pass. Covariance controls show
adding fading variance to b is the main positive change in chi at this point;
those controls are mathematical sensitivities, not valid protocols.

## DEC-0166 - separate Gaussian diagnostic deliberately ignores fading variance (2026-10-13)

Authority: explicit user request REMOVE FADING-INDUCED NOISE FROM EFFECTIVE
GAUSSIAN SKR. Supersede the previous STOP only for the one specified reference,
isolated implementation, fresh Gaussian MI/Holevo, lightweight tests and report.
Keep raw Eq10, normalized physical law, all three moments and existing C,w.
Use T_eff=mh², xi_eff=xi_ch=.0186, N_eff=T_eff*xi_ch in both MI and covariance/
Eq20; b=1+T_eff(VA+xi_ch). Do not mix old b with the new Z noise.

Accept EVID-0183 as diagnostic evidence: K=+.05863015022113771 at
L21.9393102292/.165/VA5.5. Full-moment covariance preservation is deliberately
not claimed. This mode is an effective Gaussian approximation that ignores
fading-induced variance; it does not replace manuscript_corrected_3moments or
change frozen security/attack/lifecycle claims. Keep old corrected mixture
precision failure visible in comparison; no reuse of its MI for the new mode.
STOP after this result/report; no automatic AP/AO/search/sweep/restartC,
publication/test/training or commit/push.

## DEC-0167 - user-authorized isolated diagnostic AO, 2026-10-13

The new explicit RUN MULTISTART ALTERNATING OPTIMIZATION attachment supersedes
DEC-0166 STOP only for this reference-distance diagnostic. Permit catalog182
comparison, 8 multistart P1/P2 trajectories, limited exact source generation in
an overlay cache, higher-order discrete MI checks, Uniform VA search and report.
Keep effective_channel_no_fading_noise equations, normalized physical PDF/moments,
xi=.0186,beta=.95,ideal heterodyne,Eq10/20,direct chi(Zstar),signed K fixed.
No physical upper/peak/energy constraints are introduced. Finite sampled ranges
and source limits are computational only. Zero nu is explicitly checked.
Use new namespace ao_effective_channel_no_fading_noise_reference; protected
historical/catalog/B/C/modes/checkpoints remain byte-identical.
User was asked an optional resource preference; disclosed default is fresh
1800s new-source budget,720s per source,max3 attempts,600s Uniform reserve.
No resource-limit outcome implies coordinate/global convergence or security.
Frozen expected-hash mismatch remains a pre-existing promotion blocker.
No old ObjectiveC restart,26-distance/trajectory/cloud/aperture/divergence sweeps,
training/heldout/final-test/publication evaluation,commit or push. STOP after report.

DEC-0167 completion: accept EVID-0184/final_validation.json only within
the diagnostic scope. Actual AO/Uniform searches ran; all3 source attempts
timeout, source budget exhausted. Final AO_RESOURCE_LIMITED, best exact
(.17,5),K=.05873317206754991; no local/global convergence or fading-security
certification. Original author-selected equations unchanged. No retry or reuse
of oldC/unused historical budgets. Keep checkpoint/report and STOP; further
source/optimization work requires new explicit scope/resource decision.

## DEC-0168 - user explicitly extends exact-source time and resumes one AO, 2026-10-13

Supersede previousSTOP only for same reference-distance no-fading-noise
continuation. User authorizes7200s/source,43200s total,max1concurrent,frequent
checkpointing and existing-cache reuse. Do not restart8multistarts. Recover
exact oldprobes(.17,4.75),(.17,5.25),(0,.9),then continueP1/P2 using immediately
updatedVA and exact new sources within budget. No interpolation.
Accept EVID-0185 preparation only,not source/numeric convergence. New wrapper
may extend transporttimeout and journal completed original precision rows;
mathematical source/kernel/precision/normalization and Eq10/20 stay unchanged.
Old evaluators/results/catalog182/B/C/checkpoints protected. Separate new
namespace; stop gracefully at budget/environment limit,retain priorbest until
verified strict improvement. Timeout is resource status,never negative/invalidK.
No oldC restart/newmultistarts/distance/trajectory/publication/training/heldout/
final-test access,commit/push. Gaussian Zstar approximation remains diagnostic.

DEC-0168 completion 2026-10-14: authorized7200s/source and43200s continuation
finished as AO_RESOURCE_LIMITED;stop numerical search at the remaining-global
deadline,retain16complete new sources and source17precision checkpoints. Keep
bestexact(.17,5.046875),K=.0587348598790054;no convergence/global/security
promotion. P2 usednewP1 VA;8oldstarts neverrestarted. No automatic retry or new
resourcebudget beyond this request. Existing model/lifecycle/frozen/cache/oldC
scope remainsunchanged; no commit/push. EVID-0185/completion receipt supports
this terminal snapshot.

## DEC-0169 - user authorizes cached distance-figure update, 2026-10-14

Supersede priorSTOP only for this finite existing-cache diagnostic figure. Select best among validatedcached Uniform/MB ensembles separately at26distances20-40km;preservefixedMB/source/PDF/no-fading-noise equations and alloldartifacts. Recompute distance-dependent physicalmoments/discreteMI/direct-Zstar Holevo;never copy the reference Teff to otherdistances. No new AP/AO/source generation or continuous/global/security certification. Label optimized=best in validatedcache and effectiveGaussian ignoring fadingvariance. Save standalonePNG/vectorPDF/signedCSV/provenance in new namespace;no commit/push.

DEC-0169 completion, 2026-10-14: EVID-0186 and both figure/integrity receipts
support delivery of the completed cached-distance figure. Interpret Optimized
only as the best validated cached candidate at each sampled distance. Keep
negative Uniform values in CSV and show only positive runs on the requested
log10 figure. Stop after delivery; no additional AP/AO/search, training,
held-out/final-test/publication evaluation, commit or push. Existing lifecycle,
frozen-model blocker and source/security certification limits remain unchanged.

## DEC-0170 - user authorizes synthetic mobility-aware diagnostic, 2026-10-14

Supersede prior STOP only for the attached mobility task: finite authenticated
MB catalog at 100 grid positions, two cloud states; P2 and discrete DP; 30-slot
synthetic demonstration, velocity/penalty sweeps and six standalone figures.
Use the existing effective_channel_no_fading_noise evaluator unchanged. The
attached distance-penalty model overrides the selected TeX energy approximation
for this implementation; no joules/propulsion-energy claim. Explicit HAP
embedding preserves the old reference slant distance; no measured coordinate
claim. Tests and a small smoke must pass before the full diagnostic. Keep raw
K and positive-part usable rates distinct. No AP/AO, new source moments,
training/held-out/final-test/publication evaluation, commit or push. Frozen
hash discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.

DEC-0170 geometry confirmation: user explicitly chose the reference-preserving
demonstration coordinates via the clarification reply. Recorded in
results/mobility_aware_skr_20261014/geometry_user_confirmation.json. This matches
the running configuration exactly; no numerical input or accepted result changed.

DEC-0170 completion: deliver the completed diagnostic implementation, CSV,
six PNG/vector PDFs and Vietnamese report supported by EVID-0187 and hash-bound
full/final-validation/completion receipts. Finite catalog/grid optima are
computed-table results, not continuous-domain or exact fading security
certification. Default lambda=0.001 is a declared demonstration setting,
not a selected physical energy parameter. Stop the authorized experiment;
no automatic source/AO search, training/held-out/final-test/publication work,
commit or push. Preserve all old results and external manuscripts.

## DEC-0171 - targeted numerical package and Uniform benchmark, 2026-10-14

User explicitly authorizes IEEE figures/tables/LaTeX, existing-data validation,
only missing controlled Uniform comparison and affordable separate scenario
sensitivity. Supersede priorSTOP solely for this diagnostic package. Preserve
all old39400results and197MBbank; use existing no-fading-noise mode for controlled
30Uniformsource states. Full fading-aware numerical modules are present but
not validated for complete security/precision and every later source identity;
do not bypass their guards or call this package certified fading security.
Keep main figures preliminary; output omission audit, boundary explanation,
normalized cumulative quantity, exact discrete results and all plotted CSV.
No new Cw/AP/AO, oldfull MB rerun, training/heldout/final-test/publication
evaluation, commit/push. Frozen mismatch andNOT_READY remain.

DEC-0171 completion: accept EVID-0188 only as the requested cached-data and
additional Uniform diagnostic package. Deliver the seven IEEE figures, two
tables, plotting CSV, Overleaf ZIP, LaTeX section and Vietnamese report. Original
39400 MB records, old C,w/scientific kernels and frozen specifications are
preserved; only missing 6000 Uniform plus 30 smoke evaluations were computed.
Optional scenario comparisons use the existing binary-state rate table.

Keep preliminary Gaussian/no-fading-variance classification and finite-bank/
finite-grid scope explicit. Do not promote full fading-security, publication
lifecycle, physical energy, continuous optimality or matched-energy shaping
claims. TeX compilation remains BLOCKED_BY_ENVIRONMENT, despite successful
lexical/path/export checks. No external manuscript edit, commit or push.
This task is COMPLETE; STOP. Further scientific runs require a new explicit
request and independently valid lifecycle/provenance evidence.
