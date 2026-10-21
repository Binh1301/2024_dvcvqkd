# Project State

## Current: corrected full-fading code validated; exact reference version pending

2026-10-17 attachment f5f45a58. IMPLEMENTED_NUMERICALLY_VALIDATED_REFERENCE_VERSION_PENDING.
New full_fading_channel/evaluator modules and corrected manuscript CLI implement
two named optical modes, complete fading noise, ideal heterodyne interval Holevo
and distinct Gaussian/actual-mixture MI. Four fixed-source comparisons saved in
results/corrected_full_fading_20261017/released_run/. released_verification has
32 unit tests and 40 stricter numerical checks CURRENTLY_VERIFIED_PASS.
Mode B mixture K≈-.000752322973 (233urad/Dr08), -.325876200679 (10urad/Dr55).
No positive rate, parameter optimization, new C,w/AP, training/test/publication
access, baseline/threshold promotion, commit/push. Optical active conditioning
is explicit, physical calibration/security certificate unestablished. Requested
Binh (38)(7) unavailable; available (38) is comparison-only. Frozen historical
hash discrepancy, NOT_READY_FOR_PUBLICATION_SCALE_RUNS and Objective C USER_STOPPED
unchanged. Report docs/CORRECTED_FULL_FADING_MODEL_VI.md; await reference/review.

## Current: Task2 optical gate FAILED; SKR search NOT_RUN

2026-10-17. BLOCKED_POINTING_MODEL_INCONSISTENCY: independent circular aperture
mean Hp=.03311350682836657; equivalent Gaussian mean=.2777137319309177.
16 reference numerical checks CURRENTLY_VERIFIED_PASS; this does not validate
the old approximate law. Old conditioned m1≈.2379089 reproduced. Task1 files
referenced in supplied chat unavailable in this checkout; full Task2 incomplete.
Report docs/POINTING_APERTURE_TASK2_VI.md; machine evidence in
results/pointing_aperture_task2_20261017/. No SKR sweep/source optimization,
training/final-test/publication access or model edits. NOT_READY_FOR_PUBLICATION_SCALE_RUNS,
Objective C USER_STOPPED and historical frozen-hash discrepancy unchanged.

## Current: IEEE numerical-results package COMPLETE; STOP

2026-10-14 EVID-0188/DEC-0171. CURRENTLY_VERIFIED_PASS for scoped numerical
and export validation: reused 39400 MB records, added only 6000 missing Uniform
records with own authenticated C,w (plus 30 smoke). All original 15 tests and
10 new tests pass; 3496 protected old hashes remain unchanged. Seven figures
have both column sizes, vector PDF/300-dpi PNG, explicit plotting CSV; two IEEE
tables, captions, numerical-results LaTeX, Vietnamese report and Overleaf ZIP.

S4 mean .061041913501481276 bits/use, flight 600 m: retains 98.64043960103005%
of S3 mean with 74.17807519839421% less flight. Stationary Uniform/MB means
.004525533061950683/.05349345891657229; moving lambda0 Uniform/MB means
.005221740888377324/.061883253712551226. Joint catalog/source-adaptation
comparison only, not isolated shaping at matched energy. Optional 100 DP-only
scenario comparisons are separate from the original five-speed demonstration.

Artifacts: results/mobility_numerical_results_package_20261014/, including
NUMERICAL_RESULTS_REPORT_VI.md, package_receipt.json, final_validation.json,
completion_integrity_receipt.json and overleaf_numerical_results.zip. All
14 PNG layouts reviewed; vector/DPI/paths/math checks pass. LaTeX compilation
is BLOCKED_BY_ENVIRONMENT (no compiler); manuscript page layout unverified.
Scientific status PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE:
full-fading precision/security/source-snapshot scope unresolved, no full-fading
rerun or certified security claim. Physical PDF/three moments/exact C,w,
scientific/MI/Holevo kernels and old results are unchanged. No new C,w/AP/AO/MC,
training/test dataset access, held-out/final-test/publication evaluation,
baseline/threshold approval or commit/push. Frozen-hash mismatch,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and Objective C USER_STOPPED remain.
Deliver package, then STOP; await a new explicit task.

## Current: mobility-aware joint optimization COMPLETE; STOP

2026-10-14 EVID-0187/DEC-0170. CURRENTLY_VERIFIED_PASS for the requested
synthetic diagnostic: 100 positions, 197 authenticated MB sources (all182
original keys retained), two channel states, 39400 evaluations, 30x20s slots.
15 scoped tests and 30 smoke evaluations passed before the full run. Five
cloud velocities and eight lambda cases completed; six PNG/vector PDFs.
Default means S1=.033503391695769096, S2=.05349345891657229 (950,950)m,
S3=.061883253712551226, S4=.061041913501481276 bits/use. Flights0/0/
2323.606797749979/600m; S4 lambda=.001, objective=.06044191350148127.
No numerical failures; GH8/16/32 winners match at all200states. Independent
cache keys, P1 maxima, covariance spectra/entropy and P2/DP checks pass;
3437 protected old hashes unchanged. Geometry embedding is user-confirmed
and preserves the original 21.9393102292km reference. Cloud parameters are
synthetic, and the penalty is flight distance, not propulsion energy.
Report docs/MOBILITY_AWARE_SKR_REPORT_VI.md; results/mobility_aware_skr_20261014/
contains all CSV, figures, full/experiment_receipt.json, final_validation.json,
completion_integrity_receipt.json and provenance. Progress checkpoint remains
an immutable last loop snapshot; full receipt is terminal evidence.
Current no-fading-noise Gaussian source/MI/Holevo kernels and physical PDF/
three moments are reused unchanged. No new C,w/AP/AO/interpolation. No exact
fading-security, continuous/global physical optimum or total-error certificate.
No training/test data access, held-out/final-test/publication evaluation,
baseline/threshold approval or commit/push. Frozen-hash mismatch and
NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain; Objective C USER_STOPPED.
Deliver implementation/report/figures, then STOP; await a new explicit task.

## Current: updated cached distance figure COMPLETE; STOP

2026-10-14 EVID-0186/DEC-0169. CURRENTLY_VERIFIED_PASS: 5902 evaluations of
227 existing validated ensembles (30 Uniform, 197 MB) at 26 distances, 20-40 km;
78 selected rows, zero numerical failures. Fixed MB keeps (0.2,1.3833230302980657).
Physical PDF/moments/T_eff and discrete MI/direct-Z_star Holevo were recalculated
per distance: xi_eff=0.0186, ideal heterodyne R=1, beta=0.95, phase/adaptive optics OFF.
GH8/16/32 winners match at all distances. Reference best (0.17,5.046875)
reproduces K=0.0587348598790054. Uniform is positive through the sampled 24 km
point and negative from sampled 25 km; both MB curves are positive through 40 km.
Signed CSV is preserved; log10 displays only positive runs.
New namespace results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/:
PNG, vector PDF, selected/all-candidate CSV, source roster, moments and receipts.
Report docs/SKR_DISTANCE_NO_FADING_NOISE_CACHE_REPORT_VI.md. Independent checks
verify the finite-bank maxima, physical covariance spectra, source and output
hashes; all 3423 protected old files are unchanged.
Gaussian approximation ignoring fading variance; finite-cache selection only,
no continuous/global optimum or exact fading security claim. No new source
generation, AP/AO, training, held-out/final-test/publication evaluation or
baseline/threshold approval. Frozen-hash mismatch, old scientific data/model,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and Objective C USER_STOPPED remain.
Deliver artifacts, then STOP; no automatic further run, commit or push.

## Current: extended-timeout AO continuation COMPLETE; AO_RESOURCE_LIMITED; STOP

2026-10-14 EVID-0185/DEC-0168. Actually ran43135.438s numericalcontinuation
within43200s budget (reserve60s,shutdown5s),sequential1,source ceiling7200s.
Loaded8oldstarts/211objectives,restarted0. Three oldtimeouts completed exact;
16new C,w records saved,227objective rows. Source17(.17125,5.046875) hit
remaining-global deadline;1050/1250 saved,1450incomplete,no acceptedCw/SKR.
Currentbest exact(.17,5.046875),K=.0587348598790054;delta1.6878114554863544e-6
(+.0028736936829244926%) vsoldbest. One P1->P2 iteration; P2 usedimmediate
newVA. P1 bracket[5.03125,5.0625] stillopen after4refinementstages; P2
bracket[.169375,.1725] missingneighbor.17125 and boundary0 atnewVA.
No coordinate/global convergence. GH8/16/32 top10 winnerstable,physicality
andprovenance checksCURRENTLY_VERIFIED_PASS;3275protectedhashesunchanged.
Six scopedpreflight tests passed;producer/test hashes verifiedunchanged.
No researchPython workers;Job/watchdog/sleeplease cleanup verified.
Report docs/AO_NO_FADING_NOISE_CONTINUATION_REPORT_VI.md;artifacts under
results/ao_effective_channel_no_fading_noise_reference_continuation/, including
continuation_result/final_validation/completion_integrity_receipt.json.
SameTeff.16092029098192165,xi.0186,beta.95,idealR1,phase/adaptiveopticsOFF.
Eq10/20/PDF/three moments/source normalization and allold caches/modes/results
unchanged. Gaussian approximation ignoringfadingvariance; no certifiedfading
security or rigorous source/globalerror enclosure. Frozenhash mismatch and
NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain;ObjectiveC USER_STOPPED.
STOP;no autoretry/newbudget/multistarts/sweeps/trajectory/training/heldout/
final-test/publication evaluation/commit/push.

## Current: no-fading-noise reference AO COMPLETE; AO_RESOURCE_LIMITED; STOP

2026-10-13 EVID-0184/DEC-0167. Actually ran8 multistarts at onlyL21.9393102292
under effective_gaussian_Zstar_diagnostic_SKR (same normalizedPDF/3moments,
Teff=.16092029098192165,xi=.0186,beta=.95,ideal heterodyne,phase/adaptiveopticsOFF).
All8 original starts terminate(.17,5),K=.05873317206754991,matching182-catalog
max. Delta vsinitial .00010302184641219903 (+.17571479183257652%).
Uniform best exact VA1,K=.004586201522212313;shapingdelta=.0541469705453376.
211 exact objectives;3newsource attempts timeout720/480/600s,0newCw;
sourcewall1800.016s. Final AO_RESOURCE_LIMITED: MBVA[4.5,5.5],nu[.165,.175]
and UniformVA[.8,1.075] brackets not numerically closed;20missingdistinctpairs.
GH8/16/32 winner stable;7tests/independent assertionsCURRENTLY_VERIFIED_PASS,
3228protectedhashesunchanged,0controller/source/oldCprocesses.
Report docs/AO_EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md; result/checkpoint/
CSV/3PNG+PDFs in results/ao_effective_channel_no_fading_noise_reference/.
No exact physical-fading security/global/convergence claim. Oldmodels/cache182/
B/C/checkpoints/MI/Holevo/Eq10/20/frozen spec unchanged; oldspec mismatch remains
promotion blocker,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,ObjectiveC USER_STOPPED.
STOP. No retry/newbudget/search/sweep/trajectory/training/test/publication/commit/push.

## Current: effective_channel_no_fading_noise one-point diagnostic COMPLETE; STOP

2026-10-13 EVID-0183/DEC-0166 explicit user decision. New isolated module/config/
entry/tests/report, same Eq10/normalized PDF/three moments/source cache; all
moment preservation residuals zero. Only L21.9393102292/nuRaw.165/VA5.5,
idealR1/xiDet0/chiHet1/beta.95/xiCh.0186/phaseOFF/AOOFF.
Teff=.16092029098192165, xi_eff=.0186, N_eff=.0029931174122637422;
a6.5,b1.8880547178128329,Zstar2.576345544379474; fresh discreteGaussian
I=.527940610384956,chiStar=.4429134296445705,K=+.05863015022113771.
Five tests CURRENTLY_VERIFIED_PASS;3217 prior protected files unchanged.
Effective Gaussian approximation deliberately ignores fading variance and
does not match full physical Bob covariance or establish fading security.
Report docs/EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md; evidence
results/effective_channel_no_fading_noise/reference_20261013/.
Old modes/results/caches/frozen spec unchanged, historical spec-hash mismatch
and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged; ObjectiveC USER_STOPPED.
No AP/AO/182/26/restartC/newMC/training/test/publication/commit/push. STOP.

## Current: negative-SKR causal diagnostic complete; CONFIGURATION_MISMATCH; STOP

2026-10-13 EVID-0182/DEC-0165. One-point existing-source/MI diagnostic complete for
L21.9393102292, nuRaw.165, VA5.5 using the stored historical row and corrected
ideal reference. Base D55 geometry, source key, ensemble hash, C, and w match;
derived PDF coefficients/support/moment conventions differ (historical
untruncated closed-form versus corrected Eq10 active conditioning). Corrected
raw tail above eta=1 is .015879972779715795; full-support raw Teff=.1694819790377013,
retained unnormalized Teff=.1558491966743379; conditioned Teff=.16092029098192165,
historical Teff=.2011265222214531. Aperture/Rytov/tail/conditioning stages separated.
Fading noise=.42343717270144676 (98.9657642% of Neff); lambda2 entropy term
accounts for the largest Holevo increase. Adding fading to b is the main chi
change in physical covariance sensitivities. Eight tests CURRENTLY_VERIFIED_PASS,
3663 protected + 13 prior ideal output hashes unchanged; actual historical
I/betaI/chi/K/Teff reproduced with zero residuals. Report:
docs/NEGATIVE_SKR_DIAGNOSTIC_REPORT_VI.md; receipt:
results/manuscript_corrected_3moments/negative_skr_diagnostic_20261013/.
Corrected MI remains SAMPLING_PRECISION_NOT_MET and security lower bound remains
NOT_ESTABLISHED. No evaluator/source/cache/Eq10/Eq20/AO/AP/sweep/C/training/test/
publication/commit/push change. Stop; like-for-like rerun needs fresh scope.

## Current: ONE ideal corrected reference complete; MI precision NOT_ESTABLISHED; STOP

2026-10-13 EVID-0181/DEC-0164. User selected idealR1/xiDet0,chihet1 foronly
L21.9393102292,nuRaw.165,VA5.5. Separate idealconfig/entry/results; oldcorrected
core/trusted config, historical/literal/cache/182/B/C unchanged. 29 tests
CURRENTLY_VERIFIED_PASS;3663 protected hashes unchanged; originalM/Nregressions pass.
Physicalmass1,mn=1.7665162371050331;Teff=.16092029098192165,Zstar=2.575487382363995.
IdealchiStar=intervalnumericmax=1.2195896239728028; full interval justified but
no rigorouserrorenclosure. ActualmixtureMI=.4652637991973034,SE=.019468676410223464,
4096samples, SE>.002target =>NOT_ESTABLISHED_MI_PRECISION. SigneddiagnosticK=-.7775890147353646.
EffectiveGaussian approximationI=.4484184676941574,K=-.7935920796633533 separately.
No source recomputation/AP/AO/182/26/restartC/training/test/publication/commit/push.
See docs/MANUSCRIPT_CORRECTED_IDEAL_REFERENCE_REPORT_VI.md and ideal_reference results.
STOP after onepoint/report. ObjectiveC USER_STOPPED; frozen historical mismatch
and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.


## Current: corrected three-moment mode implemented; selected detector BLOCKED; STOP

2026-10-13 EVID-0180/DEC-0163. Isolated manuscript_corrected_3moments preserves
raw Eq10, Eq20, old source/evaluators/caches/results. 24 lightweight tests
CURRENTLY_VERIFIED_PASS;3643 protected hashes unchanged; M/N regressions and26
historical contexts pass. Physical retained law normalizes to1 within1e-10,
three moment/noise/cov/Z identities and deterministic/nonbinarylimits pass.
Discrete pooled-fading mixture MI implemented/tested with small256 fixtures;
reference precision/production point NOT_RUN. Trusted R=.7/xi_det=.0135 has no
verified Holevo: chi/K null, BLOCKED_BY_SCIENTIFIC_MODEL; no ideal substitution.
See docs/MANUSCRIPT_CORRECTED_3MOMENTS_REPORT_VI.md and implementation_validation/attempt_2.
Requested PDF(37)(2) notlocated; explicittaskequations/available(37) distinguished.
ObjectiveC USER_STOPPED/PID0, no AP/controller seen. AP/AO/182/26/training/final-test/
publication/commit/push NOT_RUN; frozen historical discrepancy and lifecycle
NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged. Wait for fresh scoped request.


## Current: manuscript_literal_3moments implemented; normalization discrepancy; STOP

2026-10-12 EVID-0179/DEC-0162. Separate backend/config/one-point entry outside
historical hash scans; 5 lightweight tests PASS, 3251 old hashes unchanged,
original reference reproduced, 26 historical contexts still compatible.
New reference PDF mass=.9841200272202841 (normalization FAILED, not repaired),
covariance numerically valid, raw K=-2.454774809836829. This is a literal
reproduction fixture, not a security/operational-rate certification. See
docs/MANUSCRIPT_LITERAL_3MOMENTS_REPORT_VI.md and implementation_validation_4.
AP/AO/182-catalog/full numerical sweep NOT_RUN; new production entry NOT_RUN.
Objective C remains USER_STOPPED, frozen hash mismatch remains a historical
blocker for promotion, lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.
Wait for explicit next request; no automatic numerical optimization.


## Current: Objective C USER_STOPPED; zero workers, catalog182 preserved

2026-10-11 EVID-0178/DEC-0161 explicituserstop,21:59:57UTC+7. Verifiedcontroller
and fulltree terminated; repeatedCIMworkerabsence checksPASS. CheckpointPID0,
USER_STOPPED;2395protectedhashesunchanged,catalog182/AP1interrupted/nonewCwSKR.
Stage1cache5start results preserved/unresolved;Stage2NOT_RUN. No restart/retry or
unusedbudgetreuse. FinalSleepfinally/Jobreceipt notrun on forcedexit; native
powercfgverification requiresadministrator,notclaimedPASS. Lifecycleunchanged.


## Current: Objective C multi-start ALT_OPT preflight PASS

Runtime21:49UTC+7: controller16960/session5456,harddeadline13Oct09:49:30UTC+7.
Original5starts epoch0allreachincumbent,iterations1/2/2/2/3,allunresolved;
AP1(.16375,5.5)P2started,originalworker26500live,Cw/SKR/cleanupPENDING.
2395protectedhashesverified unchanged;no convergence claim.


2026-10-11 EVID-0177/DEC-0160. ObjectiveBcomplete182sources/4732SKRs/51grid,
lasttimeoutretryvalid26SKR/no gain,Jobempty/Sleeprestored/no oldworker. Stage1
referencefivepairedstarts thenStage2all26. Originalsource/science/AO unchanged;
neworchestrator run_theta10_D55_objective_c.py --approved-objective-c, output
results/theta10_D55_objective_C_multistart_alt_opt/. Fresh36h/36AP,Stage1up12,
internal3600s/reserve1800s,sequential,no retry.19tests/ACSleep/provenancePASS.
Readobjective_c_checkpoint.json forruntimePID/deadline/stage/requestledger.
Nu0excludedbyoriginalAO,unknown totalerror;two-closed-iteration mesh convergence
conditional only. NOT_READY/frozenhistorical discrepancy unchanged.


## Current: explicitly authorized ONE retry of grid timeout (.25,3.5) RUNNING

ControllerPID12972/session57841, startUTC2026-10-11T13:01:23.378075Z; new total
deadline15:01:12.222459Z (22:01:12UTC+7). Original APworker25592 verified live.
Source moments/26newSKRs/final actualJobempty verification PENDING. Do not duplicate.

2026-10-11 EVID-0176/DEC-0159. Completed full31 batch has30 successful sources,
one TIMEOUT(.25,3.5),181catalog/50of51grid/780newSKRs; all actual Jobs empty,
Sleep restored, no remaining controller. Original batch results remain unchanged.
User now explicitly requests that ONE timed-out point again, superseding no-retry
only for this new attempt. Entry scripts/retry_theta10_D55_grid_timeout.py reuses
unchanged original source/objective children and verified Job supervisor. Separate
output grid_timeout_retry_1/; original internal3600s, sourceouter3720s, totalcap7200s,
reserve1800s, also bounded by original absolute batch deadline. No second retry,
extra points, AO, profiler, dummy gate or scientific changes. Prelaunch17testsPASS,
1953protected hashes unchanged,181compatible keys,3stableACsamples/SleepPASS.
Read the new checkpoint for runtime state; actual worker cleanup PENDING until end.
NOT_READY_FOR_PUBLICATION_SCALE_RUNS; historical frozen hash discrepancy unchanged.

## Historical: full31 missing-source batch launch and preflight

2026-10-10 EVID-0175/DEC-0158. full_51_grid_exact_completion/preflight.json
verifies151sources,20/51grid,31missing,1953protected hashes,AC/Sleep controls.
Original exact source child/Job watchdog retained;18 scoped tests PASS.
AP0 at preparation; now controllerPID7536/session23677,probe3(.16,6.5)RUNNING.
Probes1-2 validated Cw+26SKRs each,Jobempty/closed;catalog153/grid22of51.
Refincumbent unchanged;maxima improved at10 distances23-29km (finite catalog).
OriginUTC2026-10-10T15:07:32.751912+00:00;harddeadline2026-10-12T03:07:32.751912+00:00.
Authority36h total,31 sequential distinct attempts,
internal3600s unchanged,reserve1800s,no retry/no AO refinement. Consult current
batch_checkpoint.json for live status,absolute deadline,PID and source ledger;
never duplicate live controller. Scientific defaults/frozen discrepancy unchanged;
NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains.

## Historical: two-level51-pair grid COMPLETE(cache-only);20cached/31missing;STOP

2026-10-10 EVID-0174/DEC-0157. two_level_2d_skr_grid/ savedall51binary64
specification/coverage,20reference and520distance grid SKRs,131off-gridpairs/
3406records,missingpriorities/exactmatrix and3scatterPNG400dpi/PDFpairs.
A11/30(36.6667%),B12/25(48%),union20/51(39.2157%),invalid0. Refbestgrid
(.165,5.5),K.07798099387393764 matchesfullcatalog,gap0;neargrid1/offgrid8.
All151source/3926originalobjectives unchanged,806missinggridcombinations not
invented.13testsPASS2.379s/1929inputhashesunchanged/19outputhashesverified;
visual/PNG/PDFstructurechecksPASS,fullPDFparserunavailable(pypdf),notclaimed.
Complete51coverage/31prioritylist printedterminal. Cost14successfultimings
mean41.6868min ->31source scenario21.5382h,notbounds/successguarantee.
Suggestonly(.15,3.5),(.165,6.) forcoverage,NOAPauthority. Allcachedata/no
AP/newCw/SKR/AO/fit/interpolation/oldscientific change. Orderinguncertified,
NOT_READY/frozenhash unchanged. Taskcomplete,STOP.

## Historical: ALL151 exact points listed;3926-row cache-only export COMPLETE;STOP

2026-10-10 EVID-0173/DEC-0156. all_exact_skr_points/ contains all151reference
rows/all3926source-distance rows/relative-nearsets/report/provenance. Source
identities uniquecompatible151,missingcombinations0. Refbest(.165,5.5),
K.07798099387393764 unchanged. Relativethreshold0.0001%/0.001%/0.01% counts
4/9/17,includebest;39nearrows across26distances eachcomparedwithownbest.
Acceptedref deltaNuMax.0006250000000000144,deltaVAMax.025000000000000355.
Complete151terminal ranksverified;9testsPASS2.656s/independent3926-row equality
andderivedarithmeticPASS/1921inputhashesunchanged. AP/newCw/newSKR/AO0;
no scientific/config changes. Relativeperformanceonly,NUMERICALLY_UNCERTIFIED,
notcontinuous/globaloptimum or errorbound. PriorP1/P2/catalog/science unchanged.
Requestedlisting COMPLETE;STOP. NOT_READY/frozenhistoricalhash unchanged.

## Historical: cache-only near-optimal SKR analysis COMPLETE;151 sources unchanged;STOP

2026-10-10 EVID-0172/DEC-0155. near_optimal_skr_analysis/ reads3926 stored
objectives,151 compatible binary64 pairs/26 distances;73 tables/53444 compatible
repeated rows agree,1906 protected/input hashes unchanged. Refbest(.165,5.5),
K.07798099387393764;second(.165,5.496875),K.07798099350667076;
gap3.6726688357191506e-10,deltaNu0,deltaVA.0031249999999998224.
Inclusive nearthreshold1e-6/1e-7/1e-8/1e-9/1e-10 counts9/5/2/2/1.
Two closest share nu.165; near evaluated VA values do not prove a continuous
plateau. Allrankings NUMERICALLY_UNCERTIFIED,no certifiedtotalKerrorbound.
Top20/exactneighbors/all20nusamples/missingrequests/bestvssecond26dist saved,
terminalTop20 printed;4testsPASS2.563s/independentCSV checksPASS. AP/newCw/
newSKR/AOruns0;source/model/defaults/science unchanged. SavedAOmax26/26 verified,
not rerun;no newcoordinateclosure/refinement. LowerP1 result/brackets below
remainvalid. Analysiscomplete,STOP; NOT_READY/frozenhistoricalhash unchanged.

## Historical: ONE lower P1 COMPLETE; catalog151 no SKR gain, bracket25% narrower; STOP

2026-10-10 EVID-0171/DEC-0154. b2_P1_lower_refinement/minimal_run/ succeeds
ONE(.165,5.496875),C3.209726318326182,w1.0213661080792113e-6,support256/
provenancePASS,no timeout/retry/otherP1/P2. OriginalsourceAPI2536.594s/internal
3600unchanged,controller2659.453s<7200,Jobs+controllerCPU2566.703125s excluding
audit/tests. ActualJobs0active/closed,Sleep restored/no watchdog/ACgap/worker,
1870 protectedhashes unchanged.3900 oldrows/26 channelidentities unchanged,
26 newSKR,catalog151,original129starts/283cycles/618coords,max26of26/gains0/
closures0. RefnewK.07798099350667076 vsinc(.165,5.5),K.07798099387393764 unchanged,
delta-3.6726688357191506e-10,totalKdiscrimination uncertified. P1[5.496875,5.50625],
width.009375(25%narrower),maxradius.00625unchanged;newpairedlevels0. NextFIRST
(.165,5.4984375),SECOND(.165,5.503125),not authorized;P2 remains missing.
Conditional13balancedlevels/14loopvisits estimate,notguarantee/capchange.
8prelaunch/67postrun testsPASS;one noautoAP test fixture corrected with historical
bytes archived. Originalscience/defaults/numericalproducers/rootpreflight/oldreports
preserved. BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY,not numerical/global certificate.
Final_cleanup records actual reportingclock;budgetclosed,STOP. NOT_READY unchanged.

## Historical: freshly approved ONE lower P1 running; source/result/cleanup pending

2026-10-10 EVID-0170/DEC-0153. Original source/controller/supervisor reused by
scientific binding entry forONE(.165,5.496875),minimal_run/. Runtime origin
09:56:43.362245Z->11:56:43.362245Z/controller20712; source1 starts09:56:49.308926Z,
outer5394.047s/internal3600 unchanged/reserve1800s.8prelaunch tests/1856 protected
hashes/AC/Sleep PASS. Actual original C4worker26280 running; sourceCw/26SKR/
cache-onlyAO/finalactualJobempty/Sleep restoration PENDING. Previous150source/
P1bracket/incumbent unchanged until valid new evidence. No retry/otherP1/P2,
dummy/observer/profiler or numerical/default redesign; NOT_READY unchanged.

## Historical: lower P1 preflight COMPLETE; fresh execution confirmation pending; AP NOT_RUN

2026-10-10 EVID-0169/DEC-0152. b2_P1_lower_refinement/ contains scientific
preflight/reconciliation/live original P1P2/provenance/conditional refinement
estimate and regression evidence.150 MBsources/3900 savedmetrics/26 ranked
maxima/129 savedstarts verified; two live cache-only coordinate histories match.
FIRST(.165,5.496875) confirmed original dependency and absent; SECOND5.503125
not authorized/P2 missing/0closures. P1[5.49375,5.50625],savedbest(.165,5.5),
K.07798099387393764 unchanged.65tests PASS22.326s/1856 protectedhashes unchanged;
AC/Sleep/restorationPASS, no AP worker. AP/newCw/SKR/fullAO0; fresh confirmation
requested as attachment requires, not received. Previous budget closed; proposed
120total/90outer/internal60unchanged/30reserve ONE attempt only. No dummy gate,
observer/profiler infrastructure or science/default/AO/model change. Conditional
13 balancedlevels/14 loopvisits estimate is not convergence or cap-change authority.
STOP beforeAP pending confirmation; historicalfreeze/NOT_READY unchanged.

## Historical: ONE upper P1 COMPLETE; catalog150, no SKR gain; STOP

2026-10-10 EVID-0168/DEC-0151. minimal_run/ succeeds ONE(.165,5.50625),
C3.214470263936996,w1.0319626288646324e-6/provenance256PASS, no timeout/retry/
otherAP/P2. Original sourceAPI3090.110s (<3600),controller3146.937s (<7200),
Job+controllerCPU3049.1875s excluding audit/tests. Actual source/postprocess
Jobs0active/closed/no watcher or ACgap; Sleep restored, no scoped worker.
1825 protected hashes/3874 oldrows/26 channel identities unchanged;26 newSKR.
Catalog150, original129starts/283cycles/618coords, selected max26/26, gains0/
closures0. Refbest(.165,5.5),K.07798099387393764 unchanged; newprobeK
.07798095622951573. P1[5.49375,5.50625] 1/3 narrower but zero completed paired
levels; next FIRST(.165,5.496875),SECOND(.165,5.503125), not authorized. P2
unchanged.10 prelaunch/63 post-run testsPASS; final_cleanup records finalclock.
BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY; no totalK discrimination/outer/local
numeric/global certificate. Source/AO/precision/defaults/oldscience unchanged;
frozen historical discrepancy/NOT_READY lifecycle unchanged. Budget closed;
STOP, no automatic retry/probe/P2 even with time remaining.

## Historical: approved ONE upper P1 running; result and final cleanup pending

2026-10-10 EVID-0167/DEC-0150. Fresh ONE(.165,5.50625) via unchanged validated
entry/no dummy gate, minimal_run/ origin08:25:01.613412Z,totaldeadline10:25:01.613412Z.
10 scoped tests/prelaunch provenance/stableAC/Sleep PASS;1809 protected hashes
unchanged. Source attempt1 starts08:25:10.905624Z, outer5390.703s/internal3600s
unchanged, reserve1800s. SourceCw/26-distanceSKR/cache-onlyAO/finalactualJobempty
and Sleep restoration are PENDING. No retry/additional AP/P2. Old149/refbest/
P1 bracket unchanged until valid evidence. Original science/defaults/frozen
historical discrepancy/NOT_READY lifecycle unchanged. STOP after this attempt.

## Historical: redundant dummy gate removed; actual Job cleanup tested; AP NOT_RUN

2026-10-10 EVID-0166/DEC-0149. Upper P1 entry no longer runs a synthetic
prelaunch tree/PID gate. Actual Job ActiveProcesses=0 is mandatory before close,
with bounded termination/polling within original wall allowance; failure blocks
continuation. Original shared AC/Sleep/Job/watchdog/internal60min timeout intact;
no observer/profiler/scientific/AO redesign.64 scoped tests PASS15.943s, including
native root-exit/descendant and timeout cleanup, restored Sleep/no watchdog.
1809 protected inputs unchanged; failed producer/test archived byte-identical,
other1823 failed-manifest paths unchanged; raw failure stays FAILED.
AP/newCw/SKR/fullAO0, no active scientific worker; minimal_run/ not created.
Upper(.165,5.50625) execution path ready conditional on fresh approval and live
safeguards. No current AP authority. Catalog149/ref(.165,5.5),K.07798099387393764,
P1[5.49375,5.5125]/lower5.496875 also missing/0closures unchanged. Return to
Objective B; no unnecessary diagnostics project, AP/P2 or lifecycle promotion.
Frozen historical discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Historical: upper controller STOPPED at native gate; AP NOT_RUN;no retry

2026-10-10 EVID-0165/DEC-0148. approved_run/final_report status
STOPPED_PREFLIGHT_FAILURE_NO_AP, origin07:31:20.756551Z, controller16.172s wall/
6.3125sCPU. Dummydeadline9s/2.578125sCPU/6 processes, but immediate descendant
handle check asserts Dummy tree escaped. Source never started: AP0/no timeout/
sourcecache/Cw/SKR/AO/progress. User orders stop on safety failure; no relaunch.
Native recordedPIDs/scoped workers subsequently absent, all Sleep/watchdogs clean,
AC/no gaps/deadline receipts valid;1825 protected hashes unchanged/52 moduletests
PASS9.550s/diffPASS, NOT a nativegatePASS. Teardown race plausible but unproved:
new check omits prior0.2s delay, supervisor waits root only. Preserve failed
producer, propose bounded descendant wait/native verification only with further
direction; no runtime edit/retry/AP/P2/observer. Catalog149/refbest(.165,5.5),
K.07798099387393764/P1[5.49375,5.5125]/P2 unchanged/0closures. Upper stillneeded
with lower5.496875; no unknownCw/K interpolation. Old outputs/ObjectiveA/science/
defaults/frozen historical discrepancy/NOT_READY lifecycle unchanged. STOP.

## Current P1 upper preflight COMPLETE; awaiting ONE fresh compute approval

2026-10-10 EVID-0163/DEC-0146. Output b2_P1_upper_refinement/ under
results/theta10_D55_objective_B_numerical_skr_optimization/.149 unique identities
independently reconciled from180 cachefiles,2 identicalMB filecopies counted once,
29Uniform excluded/0 incompatible counted.147+PREEXISTING(.25,2)+NEW_B2_A(.165,5.49375).
All3874 metrics/26 channels/actual savedAO maxima26/26 verified, not freshAO.
Two live cache-only reference calls reproduce histories. P1 stage1 requests
lower5.496875 thenupper5.50625; upper is genuine proposed dependency, absent
source/keydbb7a2a7024f84f97c455b0b3b564e9a307f369b362f80e055dfbf1e5d49497f.
Best(.165,5.5),K.07798099387393764; bracket[5.49375,5.5125],0closures/P2 unchanged.
No new AP/moments/SKR/channel/fullAO/formula/default change.50tests/diffPASS,
1809 protected hashes unchanged, native temporarySleep restored/ACsamplesPASS,
no worker. Actual AP Job readiness must be rechecked AFTER fresh approval.
120min total/90min outer source/30min reserve is PROPOSAL_ONLY; original internal
3600s cap remains and cannot be extended by supervisor alone. No timeout override/
APretry/other source/P2/cap16/observer/old-budget reuse. Frozen discrepancy and
NOT_READY lifecycle unchanged. STOP and request approval once, not AP execution.

## Current Objective B2 COMPLETE: one exact source; original catalog149 AO; STOP

2026-10-10 EVID-0162/DEC-0145. Output objective_B_numerical_skr_optimization/b2_A/.
Original(.165,5.49375) AP succeeds C3.2081449662247756,w1.017877140191374e-06,
one attempt/no timeout/retry/other AP. Job3039.063s wall/2938.09375s CPU.
Original JSON radius_of_curvature_m=Infinity I/O failure preserved; separate
postprocess_recovery/ fixes storage only and reuses original evaluator/AO with
AP forbidden under SAME05:44:15.276385Z->06:59:15.276385Z totalclock.
Catalog149=147baseline+1preexisting+1new,3874 metrics/26 distances; actual129
starts/283cycles/618coordinates,26/26 ranked maxima,59/129 individualmatches,
zero terminal changes/SKR gains/closures. Reference(.165,5.5),K.07798099387393764;
22km(.165,5.475),K.07661740491526092. P1 lower-neighbor advance/bracket
[5.49375,5.5125]25% narrower, not a completed paired-refinement level; next
actual(.165,5.496875) unapproved. P2 unchanged/missing. Recovery ends3310.265s;
finalverification3762.837s (<4500s), measured jobs/controllersCPU2999.9375s
(not all tests/toolingCPU).48 tests/diffPASS/1767 protected hashes unchanged.
No matching worker/lease/watchdog remains; AC/Job receipts PASS. Originalscience/
precision/quadrature/AO/caps/ObjectiveA/old artifacts unchanged; no new figure for
unchanged curves. Level1 finite-catalog only; totalK discrimination/continuous/
global/outer closure unresolved. Frozen historical discrepancy/NOT_READY unchanged.
STOP; no additional AP authority.
Final cleanup06:52:19.4821017Z, overall4084.206s (68m04s)<4500s; all protected/
output/producer hashes rechecked unchanged, no worker. See final_cleanup.json.

## Historical Objective B1 preparation; superseded by completed B2 above

2026-10-10 EVID-0160/DEC-0143:7 focused outputs plus verification/regression JSONs
in results/theta10_D55_objective_B_numerical_skr_optimization/. Original live P1/P2
reference reconstruction matches saved147-source histories/brackets, four midpoints
missing and0closures.179 payloads globally scanned/148 positive compatible sources;
extra PREEXISTING(.25,2) gets one fresh reference SKR check using existing Cw,
K.06321019816401585<incumbent. Reference remains(.165,5.5),K.07798099387393764;
other25 distances explicitly preserve147-source baseline. No AP/new Cw/AO sweep/
physics/defaults/precision/profiling/observer change. Strongest Level1 finite-catalog
claim; gap discrimination/wholeK/continuous/global unresolved.44 tests/diffPASS/
1757 protected hashes+2 receipts unchanged; ObjectiveA retained. Proposal only:
one P1(.165,5.49375),75min total/60min source/15min reserve and minimal original
AC/Sleep/Job preflight; no AP-ready/current stable-AC claim, no later probes/retry.
Frozen historical discrepancy and lifecycle NOT_READY unchanged. STOP before B2.

## Current Objective A manuscript package COMPLETE; compile/full-paper unverified

2026-10-10 EVID-0159/DEC-0142: all8 requested files plus19-file Overleaf ZIP saved
results/theta10_D55_ao_manuscript_finalization/. New jointsection/Algorithm1/
stopping sensitivity/compacttable/article master/two appendices integrate existing
147-source results and verified16-setting evidence. Raw-nu convention, indexing,
defaults, persistent unresolved search statuses, Uniform endpoint coverage and
finite-catalog-only claims explicit. Prior .tex/data/science untouched; no AP/
channel/MI/Holevo/SKR/AO/observer execution.35 tests/diffPASS/1733 hashes unchanged.
Five PDFs and two CSVs copied byte-identically; standalone ZIP graph validated
after extraction. No full original paper master found; standalone offset previews
equations5/6/7 only. No LaTeX engine on PATH, local/remote compileNOT_VERIFIED and
no compiled manuscript PDF. External instructions provided. No publication-scale/
security/numerical/global promotion; frozen historical discrepancy unchanged.
Objective B NOT_RUN, STOP scope enforced.

## Current AO stopping sensitivity COMPLETE; baseline defaults unchanged

2026-10-10 EVID-0158/DEC-0141: all14 requested outputs plus genuine per-setting
records saved results/theta10_D55_ao_stopping_parameter_sensitivity/. Original
AO baseline exactly reproduced129 starts/283 iterations/26 maxima before16
temporary Rmax/epsilon settings.147 sources/3822 stored metrics unchanged.
All settings preserve selected and individual terminal pairs/K; maximum26/26,
0/9856 coordinate completions. Eps1e-6 uses279 cycles vs283 for1e-7/8/9;
all caps stop by4, zero cap terminations;129 missing-blocked starts/configuration,
same55 distinct missing sources.20 stagnation/109 unresolved states per setting.
Conclusion BASELINE_PARAMETERS_ONLY_COMPUTATIONAL_SAFEGUARDS. No AP/channel/
security rerun/fresh objective evaluation; original science/AO source/defaults
untouched, inner cap4/parameter1e-6 fixed.30 tests/diffPASS/1591 hashes unchanged;
PNG400dpi/vector PDFs/log10epsilon checked; LaTeX141/296 words/staticPASS,
compile no engine. AO322.892s wall/308.156s CPU excluding unrecorded setup;
report-only reader repair/finalization11.834s, no AO retry. Frozen discrepancy,
continuous/wholeK/global/lifecycle gates unchanged; no new AP authority.

## Current focused AO scientific results COMPLETE; no new AP or engineering

2026-10-10 EVID-0157/DEC-0140: all13mainresults plusOverleafentry/localcoordinate
plots saved results/theta10_D55_ao_final_scientific_results/. Verified147MB/
3822metrics/129genuinestarts/283outerupdates/618searchcalls;selectedmaximum26/26,
59/129individualmatches/0unanimousdistances/0closures. Ref(.165,5.5)
K.07798099387393764;22km(.165,5.475)K.07661740491526092. Alltablemetrics/
candidatekeys/channelidentities/currentcodeprovenance independently checked.
Algorithm1/Englishsection accuratelydescribecaps/domain/stopping/latch and
finitecatalogclaims;actualtrajectory figures+positive-onlylog10distancecurve
vectorPDF/400dpiPNG,Uniformends25/bothMB40.27tests/diffPASS/1561hashesunchanged;
LaTeXstaticchecksPASS,compileblocked(noengine);Overleafmainprovided. No newAP/
source/channel/security/objective/AO orobserverinvocation/modification. Proposed
minimalP1/P2 requestsconditional/no executionauthority. Scientific/frozen/
wholeKerror/numericalconvergence/global/lifecycle gatesunchanged.

## Current path-fixed A STOPPED on heartbeat loss; no worker or retry

2026-10-10 EVID-0156/DEC-0139 supersede active snapshot below. Longpathfix/
134actualpath tests/max247chars/8nativev2cases PASS;53finalregressions/diffPASS,
1561hashes unchanged. ActualA ran339.265s/JobCPU329.828125s then watchdog
detected staleobserver>30s and killedwhole5processJob. AC1/no schedulergap/
no deadlineexceeded.31publishedsnapshots/1050digits/305.375wall,297.203125CPU;
uncommitted32temp saved, no1250/1450/fullprofile/Cw. Reader-held dummyrepro
atomicreplace PermissionError; exact productionexception/holder notrecorded.
Not end-to-end instrumentationREADY; no AP retry/newsource allowed under
remainingbudget. Controllerfinish705.179007s/finalaudit995.36s from persistent
01:14:24.465780Z, within9000s. All29stagefiles archivedhashverified then
per-filetemporarycopiesremoved; Sleep restored/watchdoggone/no worker.
All15outputs+final_answers.md/final_saved_verification.json saved in
observer_v2_recovery/path_fixed_probe_A/. Catalog147/3822/no gains/0newsteps/
closures; freshAO NOT_RUN,26savedmatches baseline only. P1/P2/error/boundary/
stopping gaps unchanged; no numerical/global/lifecycle/scientific promotion.

## Current path-fixed single-A pilot RUNNING under fresh150min budget

2026-10-10 EVID-0155/DEC-0138 supersede stopped/no-new-authority snapshot below
for exactly the new user-authorized path repair/oneA scope. Generated production
paths actual atomic/file/hash/transfer operations PASS,53 regressions/diffPASS,
8 mapped-v2 native dummy cases PASS,147 source provenance intact/candidateA absent.
Staging C:/aoobs/p3c613a8ebe/obs/a writes first real APsnapshot; original scientific
cache remains repository/fullkey. Originalv2/source/science/precision/quadrature/
AO unchanged, no registry/permanentpower change. Output observer_v2_recovery/
path_fixed_probe_A/. Persistent origin01:14:24.465780Z, totaldeadline03:44:24.465780Z;
sourceA deadline02:35:27.896676Z,4500s ceiling,>=1800s reserve. One attempt active,
no retry/B/P2; on unsafe monitoring/AC/deadline stop wholeJob. Live budget/auth/
executionstatus/snapshots authoritative. No newCw/K/AO/closure/profile validity
yet; no numerical/global/lifecycle promotion. Frozen historicalhash discrepancy
PREEXISTING_UNCHANGED; NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current controlled observer-v2 A pilot STOPPED; no retry authorized

2026-10-10 EVID-0154/DEC-0137 supersede pending readiness/approval below.
Fresh90min/A75min/reserve15min pilot consumed one A(.165,5.49375) attempt.
Guarded v2 only, original scientific/AP/AO methods unchanged. Native AC/Sleep/
Job preflight PASS, but actual production snapshot/result path265/264chars
fails with Windows LongPathsEnabled0. Confirmed persistence-only dummy controls;
no original AP main/stage observations/C,w/new SKR/newAO. SourceJob4.234s,
controller19.687s; recorded controller+sourceJobCPU8.375s is scoped, not total
test/audit CPU.49 final regressions/diffPASS/1523hashes unchanged; saved audit
179.285406s since origin, inside original90min deadline. Worker/watchdog gone,
Sleep restored, no retry/B/P2. Catalog147/3822 and saved26/26 unchanged;
P1 bracket/missing pair/P2/0closures/error/boundary gaps unchanged. Current
production persistence readiness is FAILED for this path, not AP-ready evidence.
Results observer_v2_recovery/controlled_probe_A_20261010/final_conclusions.md
and final_validation.json. Further AP requires new explicit scope and path-safe
validation; no scientific/frozen/training/test/baseline/threshold/lifecycle change.

## Current observer v2 recovery READY for separately approved controlled pilot

2026-10-10 EVID-0153/DEC-0136: all12observer_v2_recovery artifacts complete.
Active metadata/workerJSON/dummy integration/context/repeatedprofiling/typedstatus/
nativeJob/deadline/AC+gapinjection/Sleepcleanup PASS;46 regressions/diffPASS,
1442 protected hashes unchanged,147 source provenance/3822savedobjective rows
independently verified. Dummy overheadwall2.545%,realAP overhead/coverage NOT_RUN.
No AP/source/SKR/newAO invocation; oldovernight budget NOTreused. Readiness
only new preparedentry, oldv1producer/redirect remain forensic/NOTFORREUSE.
Proposed fresh90min total/A<=75min/15minreserve/1attempt requires explicitapproval.
Baseline147/3822/26catalogmatches/P1P2incomplete/55missing/0closures unchanged.
Scientific/precision/quadrature/AO settings/wholeKerror/frozenhistoricalhash/
NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged. No worker or Sleeplease remains.

## Current overnight stopped: instrumentation failed; cache-only handoff complete

2026-10-09 EVID-0152/DEC-0135 supersede preflight/running snapshot below.
Observerv1 module.dps getter AttributeError before original AP Gram; A3.438s/
JobCPU3.234375s,1 instrumentation failure,0 success/timeout/ACabort,3 NOT_RUN.
No retry or subsequentAP; allworkers/Sleep gone. Versionedv2 module.mp.dps
fix verified on dummy operations at original3 precisions, realAP NOT_RUN.
41 final tests/diffPASS/1361 protected hashes unchanged. Actual original AO
129starts/283iterations/catalog147/3822 match26/26;0 newmoments/metrics/gains/
closures,55 missingpairs. P1/P2 unchanged, no convergence/error bound/global
certificate. All17overnight artifacts/four baseline genuine plot pairs saved.
Originaldeadline23:44:48.165007Z retained; finalaudit1041.657s inside28800.
No new production authority in failedobserver batch. Model/settings and frozen
historical-hash/NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current overnight batch approved/preflight PASS (2026-10-09)

EVID-0151/DEC-0134 supersede pending diagnostic gate for exactly overnight scope.
Origin15:44:48.165007Z/deadline23:44:48.165007Z,28800s including repair,
900s reserve. A75min/Bconditional60/C120/Dconditional120, once each, max4;
no extraAP/automaticretry/resume after safetyabort. Native39tests/Jobwall/tree/
simulatedAC-loss/Sleep cleanup/provenance PASS,AC1/battery96/no worker.
Instrumentation isolated/new stage timing; frozen math/precision/quadrature/AO
unchanged. Baseline147/3822/ref/22km verified,0newC,w/K yet. Liveovernight
ledger/probe/stage snapshot governs next execution; no convergence assumed.
WholeK error/unbounded/nuzero/frozen historicalhash and publication gates unchanged.

## Current exact-source diagnostic complete; no AP authorized (2026-10-09)

EVID-0150/DEC-0133: all13 requested source_bottleneck_diagnostic artifacts
produced,36 current tests/diffPASS,1340 scientific/prior artifact hashes intact.
0 AP/source/SKR/channel/AO executions and0 operational/scientific fixes.
Verified collector dump_stats disables profiling at first~10s, reproduced on
dummy work; full computation BOTTLENECK_NOT_LOCALIZED. P2 JobCPU ratios high
but later precision/resource progress unknown; A remains safety-abort/ACgap.
P1/P2 unchanged-best halving counts14/12 versus4-stage cap, no closure implied.
Existing partial AP numerical resume unsupported. Plan A lowerVA5.49375 then
conditional5.50625 (60min ceilings), Plan B dedicated upper/lowernu larger
budget conditional; both require separate explicit scope/budget/observer approval.
Baseline147/3822/26 finite maxima unchanged; all previous Phase1/2A files kept.
No currently active worker. Ordering error-unbounded/nu0 domain boundary/global
and frozen historical-hash blockers, NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current Phase2A finished; authority exhausted (2026-10-09)

EVID-0149/DEC-0132 supersede the running/stopped/preparation snapshots below.
1 success(.165,5.5125),1 timeout(.16531250000000003,5.5),1 safety-abort
(.165,5.49375); no retries/Phase2B.147 exact MB sources/3822 saved objectives,
26 new rows; maxima unchanged26/26 and original AO independently matches26/26.
Reference(.165,5.5),K=.07798099387393764;22km(.165,5.475),K=.07661740491526092.
P1 bracket narrows[5.4875,5.525]->[5.4875,5.5125], one-sided coverage only;
P2 unchanged. Zero new closed directions/paired stages,55 missing pairs.
ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no continuous/global optimum.
Authoritative phase_2A/objective_checkpoint.json and phase_2A_final_conclusions.md,
execution_ledger.csv, completion_read_only_verification.json. Preparation CSV and
earlier stop audit are historical, not current outcomes. No workers remain;
controller22548/session90612 exited0, Sleep state restored. Production/32 tests/
cleanup finished before original14:46:13.577171Z deadline:10090.781s wall,
recorded Job+controllerCPU8088.203125s;1243 protected hashes unchanged.
Later handoff documentation/read-only checks after expiry, no fresh science.
No additional AP authorized; Phase2B/retries require explicit fresh authority.
Scientific/settings/frozen-spec blocker and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Historical Phase2A execution snapshots (superseded by EVID-0149)

## Current Phase2A resuming unattempted probes after AC restoration (2026-10-09)

EVID-0148/DEC-0131: usercontinue/liveAC1/pin96,no workers, oldcontrollerdead.
12:42:48Z7405.391s originalremainingbudget; origin/deadline unchanged14:46:13Z.
Onlyprobe2(.165,5.5125) then3(.16531250000000003,5.5), no abortedprobe1retry.
Newcontinuationhelper delegates unchangedmath/Job/Sleep/AO, freshnative safety
preflight;480s reserve. Archive stopfiles/receiptprovenance first.0newCw/K yet;
146catalog and finite/errorunbounded classification until actualnewvalidation.
No extraAP/Phase2B/newbudget/settings/lifecycle change. Frozen-spec blocker remains.
Nowcontroller22548/session90612/probe2(.165,5.5125) started12:46:11Z,3600s
limit; nativeJob/Sleep/ACpreflightPASS/leaseactive.0newC,w/objectives yet.
Currentstopped audit/report are archived/historical; liveledger/probe2 governs.

## Current Phase2A safely stopped; AC disconnected (2026-10-09)

EVID-0147/DEC-0130: onlyprobe1(.165,5.49375) attempted; sourceJob125 at
1799.031s/1733.859375sCPU on15.578s pollgap andlastAC0. ActualSleep versus
scheduler delay uncertain; safetyabort NOTtimeout/numericalfailure.0success/
0timeout/1safetyabort/2notrun. NoC,w/newSKR/AO/reffinement; catalog146 unchanged.
Controller6380/session54545 exited1, allworkersgone, finalSleep state restored.
Audit12:27:13Z currentAC0/pin100,8339.938s originalbudgetleft. Origin11:46:13Z/
deadline14:46:13.577171Z unchanged, notpaused/reset. Executionwall2266.781s,
measuredJob/controllerCPU1741.8125s (scopeexcluded audit/test/setupCPU).
Output phase_2A/phase_2A_report andsafety_stop_audit containactual9answers/raw
receipt snapshots.32 currenttests/diffPASS,1202 protectedhashes unchanged.
Stop onbattery; stableAC/freshnativepreflight before onlyunattemptedprobes2/3
within originaldeadline. No automaticretryprobe1/extraAP/Phase2B/budgetreset.
Storedreference(.165,5.5),K=.07798099387393764 and22km(.165,5.475),
K=.07661740491526092 remainfinitebaseline only. Model/evaluator/settings and
frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current explicitly approved Phase2A running (2026-10-09)

EVID-0146/DEC-0129 supersede pending-budget gate. New10800s total/3600s probe/
max3 serial/480s reserve approved for(.165,5.49375),(.165,5.5125),
(.16531250000000003,5.5). Origin11:46:13.577171Z, absolute14:46:13.577171Z
deadline, setup/preflight/verification/cleanup included; no resets. AC1/pin100/
no source worker currentlychecked. New run_theta10_D55_ao_phase2a wrapper reuses
originalAP/Job/Sleep/evaluator/AO and old146 checkpoint. Current liveledger/
probe JSON authoritative; preparation snapshots/old results protected. No new
C,w/SKR/convergence yet. No autoretry/Phase2B/extraAP, unchanged math/settings/
frozen-spec blocker/NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Controller6380/session54545; probe1AP24332 started11:53:58Z,3600s limit.
NativeJob/Sleep/AC preflightPASS, no newsource/objective yet. Do not launch
duplicate or modify executed producer51c0ee8b...; live probe/ledger authoritative.

## Current Phase2A prepared; fresh execution authorization pending (2026-10-09)

EVID-0145/DEC-0128: attachment explicitly separates Stage1 from fresh AP approval.
Stage1 complete:146 sources/3796 saved objectives/26 maxima verified,178 compatible
cachefiles scanned, exactly3 missing original dependency keys prepared:
(.165,5.49375),(.165,5.5125),(.16531250000000003,5.5). Hard(.16375,5.5)
excluded Phase2B. Output ao_numerical_optimum_validation/phase_2A/ all14 paths;
no newC,w/K/AO, pending/baseline fields explicitly labeled. AC1/pin99 before/
after; native Sleep/Job wall/livechild cleanup/exception tests PASS/restored,
0worker.31 currenttests/diffPASS,1173 protected hashes unchanged. Proposed
10800s total/3600s source/max3 serial with480s processing reserve awaiting explicit
user approval; older Batch3 expired, no automatic retry/Phase2B. Recheck/reacquire
safety gates before any authorized AP. Original physics/evaluator/precision/
quadrature/AO unchanged; finite-catalog-only/wholeK error-unbounded classification,
frozen-spec discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current Phase1 AO numerical-optimum audit complete (2026-10-09)

EVID-0144/DEC-0127: saved146 sources/3796 objectives/maxima26/26 verified;
129 starts/283 real iterations/618 search indexing/event alignments PASS.
0 monotonicity violations under existing tolerance,0 closed final directions,
55 missing pairs. Reference/22km4/5 starts agree; nu0=.8 lower(.4,3.0).
Reference best(.165,5.5),K=.07798099387393764;22km(.165,5.475),
K=.07661740491526092, finite-catalog ONLY. Both primary coordinates missing
midpoints; secondary nu slice singleton/open. Strictnu>0 implementation does
not cover mathematicalnu=0 target. No continuous/global/wholeK error certificate.
Output theta10_D55_ao_numerical_optimum_validation/:12 requested artifacts,
8 PNG/PDF pairs, full history/diagnostics/source priorities/Algorithm1/26table.
38 scoped tests/diff PASS,1126 protected hashes unchanged; no AP/channel/objective/
optimizer rerun, no Python worker. TeX compilation NOT_RUN. Ponytail reused
existing provenance/cache/renderer helpers without changing scientific code.
STOP before Phase2; no new budget request or reuse of expired Batch3 authority.
Further targeted evidence needs separate explicit scope/budget/safety gates.
Frozen-spec discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

## Current completed Batch3:146 MB sources, maxima unchanged (2026-10-09)

EVID-0143/DEC-0126:1 source success(.165,5.4875),C3.204982206511816,
w1.0109632916527298e-6,wall2177.703s/CPU2117.703125s. Source1 AC-aborted
not retried; source3 not run because remaining time inside480s reserve;0timeouts.
145->146,26 new objectives,3796 verified rows. All26 maxima unchanged;22km
(.165,5.475),K=.07661740491526092; reference(.165,5.5),K=.07798099387393764.
New runner-up gaps1.733217454003011e-7/7.834476867252249e-8 respectively.
Original129-start/283-iteration AO matches expanded maximum26/26.618 calls
remain312 boundary/306 bracket-missing,55 missing pairs,0 closed directions.
Nu atVA5.475 still singleton; no continuous/global certificate. Six new-source
metric repeats bit-exact, ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no error bound.
Output targeted_expansion/batch_3/ all13 requested paths and independent audit.
36 tests/diff PASS;929 protected hashes unchanged;0 workers, Sleep restored.
Controller/independent numeric checks completed10:49:22Z/10:51:15Z within original
10:56:11Z deadline. Final narrative handoff afterdeadline disclosed. Controller
authorization elapsed10391.192873s including idle/stop, measuredCPU4149.515625s
(scope exclusions inreport), resume2267.656s. No budget reset/extraAP authorized.
All scientific/precision/quadrature/AO unchanged; frozen-spec/publication gates
persist. Older running statements below historical; session50362 exited0.

## Current Batch3 resume running, original deadline retained (2026-10-09)

EVID-0142/DEC-0125:AC restored1,charging. Usercontinue resumes only unattempted
2/3; source1 powerabort never retried. Controller26208/session50362, probe2
(.165,5.4875) AP23844 started10:11:40Z, limit2190.664953s. Originaldeadline
10:56:11Z unchanged,480s final AO/cleanup reserve; source3 conditional on time.
No new C,w/source completion/SKR/AO result yet; baseline145 unchanged.
Native unchanged supervisor wall/idle-descendant cleanup/Sleep/AC tests PASS;
earlier two-busy dummy hit JobCPU guard, failed resume preserved. Scientific/
precision/quadrature/provenance/AO unchanged. Live source_generation_ledger.json
and probe_results/e0b4f67a...json authoritative for current execution; root
run_report.json's stopped checkpoint is historical until final rewrite.
Frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.

## Current approved Batch3 halted on AC loss (2026-10-09)

EVID-0141/DEC-0124 supersede earlier pending-approval states. New10800s/3600s/
max3 serial approval received; only probe1(.165,5.4625) attempted. Source Job
aborted1952.719s/CPU1926.453125s onAC0,returncode125, not timeout or numerical
failure.0 success/0 timeout/1 powerabort; no C,w, no newSKR/fullAO. Catalog145
and old22km best(.165,5.475),K=.07661740491526092 remain unchanged.
Controller16568/session17086 exited1; no Python worker. Original Sleep state
restored and885 protected hashes unchanged. Native Job/Sleep preflight PASS;
early no-AP preflight failures archived, original session deadline retained.
Active-stop wall2162.932809s, measured current-controller/JobCPU1937.28125s
(earlier failed-preflight JobCPU not fully captured). Absolute origin07:56:11Z,
deadline10:56:11Z; no pause/reset. Audit09:59:11Z:AC0,battery48,3419.817s left.
Output targeted_expansion/batch_3/safety_stop_audit.md/json and raw execution
ledger/report preserve evidence. Probe2/3 NOT_RUN; original 'continue' cannot
bypass AC requirement. Reconnect stable AC before further AP; never restart
old main/automatically repeat aborted source. Preserve deadline/attempts in any
explicit continuation; expired budget requires fresh approval. No scientific,
precision/quadrature/MI/Holevo/AO/lifecycle changes; frozen-spec blocker persists.

## Current Batch3 execution selection ready; approval pending (2026-10-09)

EVID-0140/DEC-0123: current execution attachment requires separate fresh
runtime approval. Stage1 complete; all3 missing original points retained:
(.165,5.4625),(.165,5.4875),(.16531250000000003,5.5). No nu midpoint generated
atVA5.475 singleton slice; original lowerouter.0825 missing, opposite.33
unchecked. Third follows otherwise branch, not aVA5.475 closure claim.
145 compatible sources/3770 objectives and stored AO26/26 currently verified.
Output targeted_expansion/batch_3/batch_3_final_selected_probes.csv and pending
run_report.md/json.0 AP/newC,w/newSKR/full AO.876 protected hashes unchanged;
33 current scoped tests/diff PASS. AC/Sleep lease transient preflight PASS and
released; recheck/reacquire/native Job deadline cleanup preflight before AP.
No worker. Fresh proposed10800s/3600s/max3 sequential requires explicit user
confirmation; old budgets not reused. Earlier no-budget-request instructions
apply to completed cache-only task, not this new attachment's approval stage.
Science/model/settings/lifecycle unchanged; frozen-spec discrepancy persists.

## Current cache-only Batch3 preparation complete (2026-10-09)

EVID-0139/DEC-0122:145 compatible MB pairs,3770 objectives independently
verified; stored original AO maximum matches26/26.24 unchanged GH8/direct-Z
reevaluations reproduce metrics bit-exactly; no missing K needed and no AP.
Accuracy ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED: no total objective bound.
22km sampled VA maximum(.165,5.475),K=.07661740491526092, neighbors5.45/5.5;
reference best remains5.5. Original channel replay/ordering confirms the
distance-dependent distinction. AtVA5.475 onlynu=.165 exists; not bracketed.
All54 missing pairs verified/ranked from618 existing calls. Proposed NOT_RUN
Batch3: (.165,5.4625),(.165,5.4875),(.16531250000000003,5.5), original binary64
midpoints. Alternative20/23/24 coverage assessed; known timeouts deferred.
Output targeted_expansion/batch_3_preparation/ includes10 requested artifacts,
full matrix/provenance/repeats/local logs/final verifier.856 protected hashes,
35 scoped tests and diff PASS; no worker. Stop: current task forbids new AP.
No continuous convergence/global optimum/physical significance claim. Science,
precision/quadrature/ALT_OPT settings and145 sources unchanged. Frozen-spec
discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.

## Current completed batch2:145 MB exact candidates (2026-10-09)

EVID-0138/DEC-0121:3/3 successful sources,0 timeout,142->145 exact MB pairs;
78 new original-evaluator objectives atall26 distances. Only22km max changes
(.165,5.45)->(.165,5.475),K=.07661740491526092,delta2.626161285101958e-07
vs142. Other25 maxima unchanged;20km new runner-up(.15,6.25). Tiny numeric gain
not certified meaningful without total objective error bound.
Original129-start cache-only AO matches145-catalog max26/26, but618 calls
remain unresolved:312 open-boundary/306 bracket-source-missing,54 distinct
missing pairs,4 selected stagnated/22 unresolved. No new full coordinate
closure, numerical convergence or global optimality.
Output targeted_expansion/batch_2/run_report.md has moments/runtime and full
historical136/previous142/current comparison tables, with exact CSVs/histories.
Wall6935.906s/10800s, measured Job+controller CPU6744.1875s; all probes<3600s.
Verified AC/sleep prevention, original state restored,0 worker/controller.
796 protected hashes unchanged;32 tests and diff PASS. Earlier artifacts and
preparation snapshots intact. Science/source formulas/precision/quadrature/MI/
Holevo/ALT_OPT/provenance unchanged; no interpolation. Completed3-point approval
does not authorize extra AP from unused time. Future targeted coverage requires
new explicit scope/runtime approval; no promised gain/closure. Frozen-spec
discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged. Older running
statements below are historical; session37875/controller12356 exited0.

## Current approved batch2 execution (2026-10-09)

EVID-0137/DEC-0120: user approves fresh10800s/3600s/max3 sequential batch2,
timeout continuation and post-success reassessment, no automatic retry.
Controller12356, session37875, started05:06:20Z. Probe1(.165,5.475) AP20204
running. active_power_preflight.json confirms AC1/pin100/lease active. Output
targeted_expansion/batch_2/, preparation files preserved in preparation_snapshot/.
Baseline142 sources/current22km reference.07661714229913241; only new successful
objectives evaluated atall26, then original129-start cache-only AO. Original
methods/settings/provenance/precision/physics frozen. No new source completion,
improvement or convergence inferred yet. Keep360s final AO/cleanup reserve.
Old pending-budget statements below are historical/superseded for this batch.
Checkpoint1: valid C=3.1986564642787387,w=9.973886145561931e-07;
wall2159.172s/CPU2101.03125s; MB143/all26 new objectives.22km new finite
max(.165,5.475),K=.07661740491526092,delta2.626161285101958e-07 vs142,
other25 unchanged. Numeric ordering only, error bound absent. Remaining
midpoints reassessed/retained using measured neighbors. Probe2 started05:42:49Z,
AP18092; probe1 tree gone. Final AO pending; no convergence claim.
Frozen-spec discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS unchanged.

Checkpoint2: valid source(.165,5.425000000000001),C=3.1733504920888835,
w=9.46327534412786e-07,wall2444.406s/CPU2368.921875s. MB144/52 new
objectives; no additional maximum change. Source3(.15,6.25) retained after
measured reassessment, started06:24:16Z/AP8420; earlier trees gone. Final AO
pending. No timeouts so far; no numeric/global convergence claim.

## Current batch2 preparation; fresh compute approval pending (2026-10-09)

EVID-0136/DEC-0119: verified142 compatible MB pairs and3692 saved objectives
without scientific rerun. Current22km reference.07661714229913241. All52 actual
missing pairs inspected; provisional probes(.165,5.475),(.165,5.425000000000001),
(.15,6.25). Second is actual original midpoint1ULP above proposed5.425; cache
keys/ensembles checked. Priorities2/3 adapt to measured results if later approved.
No AP/new moments/new SKR/AO started. Output targeted_expansion/batch_2/ holds
selected identities, exact neighbor gaps, baseline snapshots and pending report.
780 protected hashes unchanged;30 scoped tests/diff PASS. AC1/pin100 and temporary
sleep request verified/released in short preflight; recheck/reacquire before AP.
Attachment's proposed fresh3h total/60min per source/max3 batch requires explicit
confirmation; old unused time not carried over. No running worker. Frozen-spec
discrepancy/publication restrictions unchanged. Previous completed142 batch below
remains numerical baseline; its618 unresolved searches were NOT rerun here.

## Current completed sleep-safe three-point campaign (2026-10-09)

EVID-0135/DEC-0118:3/3 valid exact source probes,0 timeout, MB139->142.
78 new original-evaluator objectives atall26distances. Only22km finite max
changes to(nu,VA)=(.165,5.45),K=.07661714229913241,delta2.8628002113340045e-07;
other25 unchanged. Original129-start cache-only AO matches142-catalog max26/26.
Not converged:618 coordinate calls unresolved (310 open boundary/308 missing
source),52 distinct missing pairs; selected4 stagnated/22 unresolved. Zero new
fully closed searches or continuous/global optimum claims.

Output: results/theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run/.
run_report.md contains verified C,w/runtime and full26distance parameter/SKR
tables; CSVs and full histories preserved. Wall7732.75s/10800s; measured Job+
controller CPU7515.03125s; all probes<3600s. AC/sleep prevention verified through
run, original request restored,0 workers.725 protected hashes,30 scoped tests
and diff check PASS. Original scientific files/model/precision/quadrature/MI/
Holevo/AO unchanged. Prior artifacts intact, preflight snapshots retained.
Total objective error bound absent: small22km gain is finite numeric ordering
only. Completed authorization covers exactly3 specified points; no automatic
extra AP under unused budget. Frozen-spec discrepancy and publication lifecycle
NOT_READY_FOR_PUBLICATION_SCALE_RUNS persist. Older running states below are
historical; no controller is currently active.

## Current authorized three-probe sleep-safe execution (2026-10-09)

EVID-0134/DEC-0117: fresh explicit approval all3 ordered probes,10800s total,
3600s each, serial, automatic continuation even after timeout, no retries.
Controller2080 started2026-10-09T02:16:30Z; probe1 running in unified session39160.
Live active_power_preflight.json verifies AC1,battery100, sleep lease active.
Output: targeted_expansion/resumed_sleep_safe_run/. Preflight files preserved
in preflight_snapshot/, prior failed run untouched. All science unchanged.
Reserve360s for final26distance cache-only original AO/cleanup; third probe
may receive a shorter deadline. Check live source_generation_ledger.json,
probe_results/, and final run_report.json. No new C,w/SKR/convergence yet.
Checkpoint: probe1 valid C=3.211307653120286,w=1.0282071401398513e-06;
wall3203.765s/CPU3093.28125s, all26 exact objectives saved, MB140 and all
catalog maxima unchanged. Probe2(.165,5.45) started03:10:38Z; only its worker
tree remains. Final cache-only AO still pending; no convergence established.
Checkpoint2: probe2 valid C=3.186004082405213,w=9.712251500409402e-07;
wall2199.937s/CPU2143.671875s. MB141,52 new objective rows.22km catalog
max(.165,5.45),K=.07661714229913241,delta2.8628002113340045e-07;
other25 maxima unchanged. Total objective error bound not established; no
meaningful/global gain claim. Probe3(.165,5.525) started03:47:59Z; only its
tree active (AP17496). Final cache-only AO pending. No source timeout yet.
Original4+24 scoped tests pass independently at start. Frozen-spec discrepancy
and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain. Older awaiting-approval/stop
conditions below are historical and superseded for this new campaign only.

## Current sleep-safe preflight ready (2026-10-09)

EVID-0133/DEC-0116: AC connected, battery100%; transient automatic-sleep request
verified and restored during short native tests. Busy worker/descendant deadlines
and cleanup pass; simulated AC-loss termination125 passes. Four operational
tests plus24 provenance/stopping regressions and git diff --check pass. 709
protected hashes unchanged. New helper adds only power/sleep supervision around
the existing Job supervisor; no scientific calculation/settings changed.

resumed_sleep_safe_run/ has requested preflight/report/current-catalog and
NOT_RUN result paths. MB139 unchanged, three missing pairs preserved. No AP,
new SKR or AO started. NEW3h total/60min probe budget proposed but requires
explicit confirmation; old failed authorization not reused. Request currently
released; recheck AC/reacquire before actual computation. No permanent power
change. Manual shutdown/sleep/critical-power cannot be prevented by this API;
actual overruns remain FAILED. Frozen-spec/lifecycle gates remain unchanged.

## Current probe1 outcome and wall-budget failure (2026-10-09)

EVID-0132/DEC-0115: first pair(.16562500000000002,5.5) TIMEOUT; no C,w/source
completed, MB count139 unchanged. No SKR26distance/AO revalidation or probe2/3.
No Python worker remains. Raw probe/session wall30405.938/30410.828s exceeded
approved3600/10800s; wall compliance FAILED despite Job CPU1771.3125s.
Windows events confirm battery sleep22:52:50 Oct08 and wake06:47:41 Oct09
(Bangkok). Supervisor killed the Job after resume, not at the real deadline.
Do not label awake self-check/regression PASS as real-time-budget PASS.

Raw results and separate deadline_compliance_audit.json/probe_1_outcome.md
under targeted_expansion/probe_1_authorized_3h/ preserve actual timings.
694 protected hashes/executed producer preserved;24 scoped tests and diff
check pass, distinct from FAILED wall compliance. Original scientific/source/
precision/quadrature/AO/frozen files untouched. Stop; no further AP under the
exhausted wall session. Any new attempt needs fresh runtime approval and agreed
stable-power/no-suspend conditions. No power settings changed. Frozen-spec
discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS persist.

## Current authorized probe1 (2026-10-08)

EVID-0131/DEC-0114: user newly authorizes10800s total/3600s per source probe.
Probe1(.16562500000000002,5.5) running under original worker/Job supervisor;
started2026-10-08T15:20:54Z, controller17208. Separate execution output at
results/theta10_D55_mb_exact_targeted_expansion/probe_1_authorized_3h/.
No completion/source/SKR/convergence is established yet; inspect live ledger.
Original plan/cache/results preserved. Only probe1 is scheduled, then result
report/user review before probe2. Timeout does not authorize automatic retry
or another probe. Runtime/precision/quadrature/formulas/AO/lifecycle unchanged;
supervisor self-check passes. Frozen-spec discrepancy remains open.

## Current targeted MB expansion plan (2026-10-08)

EVID-0130/DEC-0113: STAGE_1 plan prepared and verified; current139 positive-nu
MB pairs unchanged. Pilot candidates: (.16562500000000002,5.5), (.165,5.45),
(.165,5.525), derived from original missing midpoint requests. Deferred
(.16375,5.5) previously timed out at3600s. No new AP/SKR/AO execution or new
source pair. No new hard runtime budget is approved; old14400s ledger exhausted.

Artifacts: results/theta10_D55_mb_exact_targeted_expansion/; all11 paths saved
with explicit plan/current-catalog/LAST_KNOWN/NOT_RUN scopes. No after expansion
or convergence claims. 680 protected hashes unchanged;24 regressions and git
diff --check pass. Require fresh total/per-probe runtime approval, then start
one serial probe and reassess benefit before further work. Original equations,
methods, precision, quadrature, epsilon/tolerances, inner/outer caps and starts
unchanged. Frozen-spec discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS
persist; no training/test/baseline/threshold approval changes.

## Current finite-catalog maximum assessment (2026-10-08)

EVID-0129/DEC-0112: all 26 ALT_OPT pairs attain the numerical maximum over
C_reference (136 historical MB pairs, full 3536-row coverage), C_available_MB
(139 positive-nu MB), and C_available_all (168 sources including 29 Uniform).
Finite-set labels are justified; continuous convergence/global optimality
remain NOT_PROVEN. No new AP: only 63 missing exact objectives from existing
sources, 3551 MB objective cache hits. All 661 protected hashes unchanged.

Raw strict logs verify 129 starts/279 total iterations/57 selected iterations.
No starts skipped or capped at 6. All recorded coordinate searches stop at
0/1 refinement stages; none hits cap 4. Offline caps 4/8/12/16/20 hit the
same UNKNOWN_SOURCE; increasing cap alone closes zero directions. The 17/12
conditional midpoint levels are parameter-radius counts; loop-entry checking
would require 18/13 allowed stages for the completion verdict in that idealization.

Artifacts: results/theta10_D55_alt_opt_catalog_certification/; 12 required
outputs, independent verifier and 24 scoped regression tests pass. Stop AP
planning here; finite-catalog manuscript wording only. Further continuous
closure needs an explicitly authorized prospective plan/budget. No numerical,
security or publication promotion. Frozen-spec discrepancy remains open;
NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains unchanged.

## Current cache-only closure diagnosis (2026-10-08)

EVID-0128/DEC-0111: diagnostic audit CURRENTLY_VERIFIED_PASS. All 3 new sources
were consumed at all 5 representative distances; no verified caching/status
bug. Cache-only replay restored 367 rows, performed 25 starts/60 iterations,
and added zero objective evaluations, zero AP sources and zero closures.
All 5 selected parameters/K/statuses remain unchanged; other 21 LAST_KNOWN.
218 identities (168 available/50 missing), 26 stored selected landscapes and
1314 candidate-history consistency checks are recorded under
results/theta10_D55_alt_opt_closure_diagnostic/.

Main local blockers: missing two-sided midpoint coverage, broad brackets versus
1e-6 and four refinement stages, plus earlier/multistart unresolved searches.
At fixed baseline best, VA/nu require 17/12 halvings, not achievable by four
stages from the current brackets; this is conditional, not an algorithm change.
Offline epsilon 1e-7/1e-8/1e-9 changes no recorded scalar stopping decisions.
Top 3 probes: (.16562500000000002,5.5), (.16375,5.5), (.165,5.45), planning only.
They cannot guarantee closure. All 633 protected hashes and 24 scoped tests
pass. No source AP is authorized; old budget exhausted. Frozen-spec discrepancy
and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.

## Current budget-complete closure assessment (2026-10-08)

EVID-0127/DEC-0110: the 4-hour continuation is stopped safely, no worker active.
Session wall=14397.36s (<14400s); source wall=14342.312000000002s and aggregate
Job CPU=13651.15625s. Six probes: 3 exact completions, 3 timeouts. 2/50
original missing ensembles completed, plus one new midpoint; 48 original
ensembles remain. Historical unavailable dependency requests: 836 -> 786.
Original 165 sources and all 567 protected files are unchanged; overlay 3
rows are validated (combined source count=168).

Five stagnated distances actually continued after each successful batch,
75 multi-start trajectories / 180 iterations / 390 coordinate/postcheck calls.
Their exact selected parameters/security metrics are unchanged, with final
delta K=0 and STAGNATED_IN_EXACT_CATALOG. Same-slice coordinate/boundary
closures added: 0/0; newly converged distances: 0. The other 21 are explicitly
LAST_KNOWN, not reoptimized, because representative closure failed.

Artifacts: results/theta10_D55_alt_opt_closure_continuation/. All requested
tables/reports and checkpointed caches are present. All-26 fresh after-counts
are NOT_RUN; do not compare cumulative subgroup 390/105 invocations to old
558/280. Epsilon=1e-8, parameter tolerance=1e-6, outer cap=6, source methods,
physical/security model, precision and quadrature remain unchanged. 24 scoped
regressions, source provenance, artifact audit and git diff --check pass.

The reusable runner now rejects an active owner or exhausted budget; its
executed pre-guard snapshot is hash-bound separately. Further AP needs a new
explicit budget, not blind retry of failed probes. No unbounded-global
certificate is supplied. Frozen-spec hash discrepancy remains open and
lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Historical active closure snapshot (2026-10-08; superseded by EVID-0127)

## Current closure continuation (2026-10-08)

EVID-0126/DEC-0109: Stage-1 inventory verified: 836 missing requests map to
50 exact source ensembles, 558 coordinate invocations and 280 open boundaries.
Current provenance accepts 165 unchanged source rows; 567 protected files
retain hashes. User authorizes a new 4-hour total / 60-minute per-probe hard
budget, batch size 1. Original equations, methods, precision, GH8, epsilon
and max outer iterations remain frozen.

Runner scripts/run_theta10_D55_alt_opt_closure_continuation.py is executing
batch 2 (.1625,5.5) using the original probe worker and Job deadline supervisor.
Batch 1 (.15,4.75) timed out at wall=3600.0s / aggregate CPU=3340.125s, with
zero new rows and no deadline overrun. CPU accounting self-check passes. Refer to live
source_generation_ledger.json and probe_results/ under
results/theta10_D55_alt_opt_closure_continuation/ for subsequent status.
No new source completion or numerical convergence is yet recorded in this
snapshot. The latest saved-batch report distinguishes LAST_KNOWN rows and
NOT_RUN all-26 after metrics; an active later batch may not yet appear there.
Do not launch a duplicate controller or call a RUNNING probe completed.

The 5 stagnated/21 open-boundary/0 converged classification remains the last
verified optimization state. The other 21 are gated on representative
validation. Frozen-spec hash discrepancy remains open; lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Current strict 26-distance reproducibility snapshot (2026-10-08)

EVID-0125/DEC-0108: EXACT_TESTED_ALT_OPT_REPRODUCIBILITY_PASS. All 26 distances
actually reran the existing corrected driver, with 129 starts, 279 iterations
and 1357 fresh exact objective evaluations. All six per-distance metrics match
the old ALT_OPT table exactly; max |delta K|=0. Actual counters equal the prior
4147/1357/1954/836/558/280 reference. The 541 protected files and 165 exact
source rows are unchanged; no new source generation or interpolation occurred.

Epsilon_opt=1e-8, parameter tolerance=1e-6, outer cap=6 are frozen. Selected
statuses: 5 STAGNATED_IN_EXACT_CATALOG (20, 21.9393102292, 22, 23, 24 km) and
21 UNRESOLVED_BOUNDARY. All terminal delta K=0, but none is numerically
converged. The remaining 50 missing source ensembles still block closure.

Current artifacts: results/theta10_D55_alt_opt_26distance_strict_rerun/.
Figure is positive-only standard log10; Uniform ends at 25 km, both MB curves
at 40 km. Exact fixed MB VA=1.3833230302980657 is preserved. 24 current scoped
regression tests pass. The orchestration-only wrapper changed no scientific
or optimization implementation. Frozen-spec hash discrepancy remains open;
lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Historical provenance/stopping repair and bounded validation (2026-10-08)

EVID-0124/DEC-0107 records PROVENANCE_VERIFICATION_PASS for all 165 original
source rows under the explicit newline-equivalence policy and separate
objective-identity validation. Historical bytes/hashes remain intact. The
corrected stopping logic retains epsilon_opt=1e-8, parameter tolerance=1e-6
and max outer iterations=6; 24 current regression tests pass.

The 836 missing requests represent 50 unique exact source ensembles. One
prioritized pilot timed out and added zero moments. Its measured 860.313-second
elapsed time exceeded the configured 90/270-second probe/total budgets; this
is recorded, and the supervisor has been repaired and tested. No further
source generation ran after budget exhaustion.

Five representative distances were replayed from compatible exact caches.
Their parameters/SKR are unchanged, but all remain unresolved. The 26-row
table explicitly retains LAST_KNOWN values at the other 21 distances, whose
optimization was NOT_RUN because representative closure failed. No numerical
convergence or global optimum is established. Scientific models/source
mathematics and old artifacts are unchanged. Publication lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Historical independent ALT_OPT audit (2026-10-08)

EVID-0123 verifies real sequential coordinate updates and independent terminal
selection from all stored histories. Controlled replay at 21.9393102292 and
25 km blocked previous final-result inputs and source generation; forward/
reverse start orders and cold/compatible objective caches selected the same
best exact-tested pairs. All 26 original rows legitimately match numerical
search on the shared available catalog. Continuous convergence remains
INCONCLUSIVE because exact source coverage and boundaries are unresolved.

At the EVID-0123 snapshot source provenance needed qualification: implementation
hashes differ from current bytes for 136/136 registered MB sources, but their
stored hashes are exactly reproduced by CRLF versions of current LF files.
Thus newline-equivalent source content is verified while strict current-byte
identity was FAILED. That snapshot's loader checked ensemble identity but not
implementation/settings; EVID-0124 subsequently corrected the loader and
EVID-0125 reverified it. No C,w, model, evaluator or previous result was changed.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest full-distance ALT_OPT continuation (2026-10-07)

EVID-0122/DEC-0106 records the cache-only ALT_OPT continuation over all 26
distances from 20 to 40 km. The same validated theta10/D55 physical/security
model and exact direct-`Z_minus` evaluator were used. Four base starts plus a
previous-distance warm start were attempted at each distance; Uniform and
fixed-MB rows were copied from the existing exact CSV, and only optimized-MB
rows were replaced in a new output table.

The baseline row at `21.9393102292 km` passes exact six-field validation. The
selected MB pair and `K` match the prior optimized-MB curve at all 26 points,
with zero maximum absolute `K` difference. The source CSV hash and 165-row
source cache are unchanged. The run is still
`FULL_DISTANCE_ALT_OPT_COMPLETE_WITH_UNRESOLVED_SEARCH`: missing exact source
moments leave inner and boundary closure unresolved, so the rows are
best-exact-tested candidates rather than a continuous/global optimum.

The selected `nu_raw` ridge is non-monotone and `V_A` is non-increasing with
catalog jumps. The new renderer uses base-10 logarithmic scale and displays
only positive exact rows: Uniform ends at 25 km; both MB curves extend to 40
km. Previous artifacts were not overwritten. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest ALT_OPT optimization-layer diagnostic (2026-10-07)

EVID-0121/DEC-0105 records the new `ALT_OPT` driver at the theta10/D55
diagnostic distance `21.9393102292 km`. The physical/security evaluator,
source-moment implementation, and channel assumptions were unchanged. The
best exact-tested pair is `(.165,5.5)` with `K=.07798099387393764`; the first
three starts reach it and the `.8` start ends at `(.4,3.0)`. This is not a
converged or global optimum claim: 34 exact source probes were missing, 20
inner directions remained unresolved, and 6 boundary directions were open.
The source cache was unchanged at 165 rows; no numerical or monotonicity
failure occurred. The open-source fallback was stopped after one probe became
CPU-bound for about 23 minutes.

The run is diagnostic-only and `BLOCKED_BY_ENVIRONMENT` for continuous AO
closure. Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest theta10/D55 unconstrained three-scheme diagnostic (2026-10-07)

EVID-0120/DEC-0104 completed the user-authorized diagnostic with peak and
common-VA constraints disabled in a separate runtime experiment. It evaluated
4,290 exact candidate rows and selected 78 exact rows over the 26-distance
grid. Uniform is positive through 25 km and non-positive at 25.5 km; fixed and
optimized MB are positive through 40 km. Optimized MB uses higher VA at short
distance, peaking at `VA=6.5`, then declines toward `VA=3.5548673904962893`.

The requested binary64 source at `VA=1.3833230303` timed out in the AP
fallback. The fixed curve uses the existing exact row
`VA=1.3833230302980657`, equal at ten displayed decimals; no interpolation was
used. Strict binary64 fixed-reference provenance remains unresolved. The new
figure is symlog (`base=10`, `linthresh=1e-4`) and retains negative Uniform
rows. Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest theta10/D55 three-scheme diagnostic (2026-10-02)

EVID-0119/DEC-0103 completed the exact D55 comparison with optimized Uniform,
fixed MB, and exact-bank optimized MB. Uniform selects VA from 1.5 at 20 km
down to .5 at 35--40 km, is positive at 25 km, and is non-positive at 25.5
km. Both MB curves remain positive through 40 km. No publication baseline or
maximum-distance claim follows; lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest transition theta/D_r frontier (2026-10-02)

EVID-0118/DEC-0102 continued only the 15--50 urad transition region. Positive
Uniform requires very-large receiver apertures: theta15 has exact thresholds
`.553045 m` at 20 km and `.642847 m` at 25 km; theta20 has `.654944 m` and
`.766989 m`; theta25 has no positive 25-km point below `.80 m`. Theta30--50
have no positive 20-km point below `.80 m`.

All refined candidates fail by 30 km, while exact bisection boundaries retain
`T_eff≈.089827455`. No 30--40-km candidate exists, so MB was not run and no
optical baseline was selected. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest joint theta/D_r optical search (2026-10-02)

EVID-0117/DEC-0101 searched 90 primary full-angle divergence/receiver pairs at
20/25/30/35/40 km with exact channel recomputation. Every pair is
`NONPOSITIVE_AT_20`; no category B/C/D or 30--40-km Uniform crossing exists.
The best cache-bound K(20) is `-3.3000236312e-5` at
`theta=50 urad,D_r=.10 m`; the best K(30)/K(40) is at
`theta=250 urad,D_r=.10 m`, still negative.

Exact `.14,.18,.20` Uniform source moments were generated; the current exact
bank has 17 VA rows, with remaining missing rows explicitly fail-closed. MB
and local refinement were not run because no Uniform crossing candidate exists.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest theta10 receiver-aperture diagnostic (2026-10-02)

EVID-0116/DEC-0100 ran the controlled `D_r=.10--.55 m` sweep with the current
theta10-derived waist and direct `Z_minus` evaluator. Exact channel bisection
over the available Uniform VA cache gives positive thresholds near `.491811 m`
at 20 km, `.512472 m` at 22 km, and `.544644 m` at 25 km; `V_A*=.8` at each
bracket. The first tested positive diameters are `.50 m` at 20 km and `.55 m`
at 22/25 km.

This is cache-bound: 10 requested VA source moments within the common budget
remain missing, so no continuous-VA threshold is claimed. The current result
supports receiver aperture as the dominant physical cause of the old positive
curve, with no security/divergence/noise change. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest positive-Uniform provenance audit (2026-10-02)

EVID-0115/DEC-0099 identified the exact source of the historical positive
Uniform figure: the 83-distance common-feasible exact envelope under
`w0=.10 m`, `D_r=.55 m`, `tau_zen=.92`, fixed epsilon `.0186`, beta `.95`,
AO/phase OFF, direct `Z_minus`, and sparse per-distance Uniform VA selection.
The current exact evaluator reproduced ten original short-distance rows with
maximum absolute SKR difference `0.0`. Uniform is positive through exact 25 km
and negative at 26 km; MB is positive at 800 km and negative at 810 km.

The old source recomputed distance-dependent channel quantities and did not
reuse fixed `T_eff` or interpolate. The current theta10urad/D10cm result is
negative because it uses a materially smaller `D_r=.10 m` aperture (and a
slightly different derived full divergence), not because the old figure used a
superseded security evaluator. Old-physical VA `.08--.15` sensitivity is
negative at 20/22/25/30 km; the old positive curve used larger VA values at
short distances.

Classification: `POSITIVE_UNIFORM_FROM_OLD_PHYSICAL_BASELINE`.
No replacement figure or new parameter search was run. Publication lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest Uniform VA diagnostic (2026-10-02)

EVID-0114/DEC-0098 verified the Uniform 256-QAM modulation-variance choice
for `theta_div=10e-6 rad`, `D_r=0.10 m` without changing the frozen model.
The implementation-derived peak-only domain is
`0 < V_A <= 22.666666666666668`. Exact coverage is 322 rows (14 VA values ×
23 distances); 13 requested VA source moments remain missing and are recorded
explicitly, so no continuous optimum is claimed.

The best exact-tested envelope uses `V_A=0.12` through 31 km and `V_A=0.13`
from 31.5--40 km. All selected SKRs are negative; there is no exact positive
point or sign crossing. `V_A=1.075` is a fixed reference-bank row, while
`V_A=0.1` is strictly below the exact-tested envelope by at most
`1.220287529912716e-8` bits/use, below the frozen `1e-6` SKR tolerance.
Classification: `VA=0.1 NEAR-OPTIMAL WITHIN NUMERICAL TOLERANCE`.

Artifacts are under `results/uniform_va_optimization_theta10_D10cm/`.
No MB rerun or final figure redraw occurred. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest divergence sensitivity search (2026-10-02)

EVID-0113/DEC-0097 tested `theta_div=5--300 urad` for the D10cm receiver
diagnostic. No candidate produced Uniform positive at 30 km and non-positive
by 40 km; all candidates are classified `TOO_NARROW_RANGE`. No theta was
selected and no final sensitivity figure was generated. Publication lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest theta10urad distance diagnostic (2026-10-02)

EVID-0112/DEC-0096 reran the 23-point 20--40 km distance experiment at
`theta_div=10e-6 rad`, `D_r=0.10 m`, with derived `w0=0.0986760647169751 m`.
It plots fixed Uniform, fixed MB, and exact-bank MB optimized curves. The
Uniform curve is non-positive at all tested distances; both MB curves remain
positive through 40 km. This is diagnostic-only; the resolved numerical MB
search status remains separate and publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Redesigned global MB/V_A numerical result resolved (2026-10-01)

EVID-0111/DEC-0095 resolve the frozen redesigned numerical search. Exact
coverage is 145 points. The best exact candidate is
`(nu_raw,V_A)=(0.165,5.5)` with `K=0.07904194520968355`; top-ten ranking is
stable under GH-order checks, and exact high-nu slice maxima decrease through
`nu_raw=0.8`.

Numerical experiment status: `GLOBAL_OPTIMUM_RESOLVED`.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; no
training, final-test access, baseline selection, or publication claim follows.

## Latest targeted ridge continuation (2026-10-01)

EVID-0110/DEC-0094 continued the redesigned exact search without a rectangular
restart. Total coverage is now 119 exact rows, including 42 continuation
rows. The best exact candidate is `(nu_raw,V_A)=(0.165,5.5)` with
`SKR=0.07904194520968355`; the ridge moved toward higher `nu_raw` and lower
`V_A` from the prior `(0.15,6)` row.

The lower-VA boundary at `0.025` and upper-VA boundary at `8` are numerically
closed by sparse exact rows. High-`nu` exact rows at `.25/.30/.40` decrease,
but no exact point exists at the expanded `nu_max=0.8` boundary. Status remains
`GLOBAL_OPTIMUM_UNRESOLVED`; publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Redesigned-baseline global MB/V_A experiment (2026-10-01)

EVID-0109/DEC-0093 record the author-authorized experiment-specific re-freeze:
`tau_zen=0.92`, `w0=0.10 m`, `D_r=0.55 m`, AO/phase noise/peak/budget OFF,
constant `epsilon_total=0.0186 SNU`, `beta=0.95`, no fixed upper bounds, and
direct `Z_minus` Holevo. The new final-model hash is
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`;
the composite experiment hash is
`a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58`.

Channel/model audit passed and the new-channel evaluator processed 77 exact
points. The best exact-tested rows are Uniform `V_A=1.075`,
`K=0.008551627907451953`, and MB `(nu_raw,V_A)=(0.15,3.5548673904962893)`,
`K=0.07565435753581196`. Neither is a global optimum or selected baseline.
The upper-nu, upper-VA, and global lower-VA boundaries are unresolved; status
is `GLOBAL_OPTIMUM_UNRESOLVED`.

The optimized-MB search is authorized only within this frozen experiment, but
publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. No
training, final-test access, held-out evaluation, or publication-scale claim is
authorized.

## Latest clean positive-SKR visualization (2026-09-30)

EVID-0108/DEC-0092 added
`results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_clean.{png,pdf}`.
It uses only the existing positive exact-tested rows, a standard log y-axis,
white background, simple line/marker styling, and the two requested legend
entries. No annotations, negative values, Binomial, or explanatory figure
text are included.

No data, source moments, candidates, channel/security evaluation, or
interpolation was added. This remains presentation-only and the lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest positive-SKR-only visualization redraw (2026-09-30)

EVID-0107/DEC-0091 added
`results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_positive_only.{png,pdf}`.
It reads only the existing extended table/report, plots 8 positive Uniform
rows and 63 positive MB rows on a standard logarithmic y-axis, and plots no
negative SKR values. The 25/26-km and 800/810-km sign information is retained
as short annotations only.

No new data, source moments, candidates, channel/security evaluation, or
interpolation was added. This remains diagnostic-only and the lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest symlog visualization redraw (2026-09-30)

EVID-0106/DEC-0090 added
`results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw_symlog.{png,pdf}`.
The renderer reads only the existing extended exact table and its redraw
report. It uses a symlog SKR axis with `linthresh=1e-11`, exact-tested line
connections and markers, the zero line, short endpoint annotations, and a
minimal 790--820-km MB sign-bracket inset.

No data, source moments, candidates, channel/security evaluation, or
interpolation was added. The 800/810-km MB bracket remains a low-rate
diagnostic observation, and the lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest extended common-feasible distance diagnostic (2026-09-30)

EVID-0105/DEC-0089 extended the unchanged common-feasible exact diagnostic to
83 distances through 1000 km. Uniform remains positive at 25 km and negative
at 26 km. MB is positive at 800 km and negative at 810 km, giving an
exact-tested bracket only. The final MB bracket values are O(1e-11) bits/use
and must be treated as low-rate diagnostic observations, not convergence or
operational evidence.

The extended redraw and table are complete. No source moments, candidate
generation, C,w interpolation, security-formula change, or publication-scale
workflow occurred. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest exact-point SKR visualization redraw (2026-09-30)

EVID-0104/DEC-0088 added
`results/revised_hap_uav_optical_baseline_figure/skr_vs_distance_redraw.{png,pdf}`.
The redraw reads only the existing 26-row common-feasible exact table and
cross-checks it against the diagnostic envelope and protocol summary. It
uses straight visual connections between exact-tested points, circular
markers, and a zero line; it does not add or estimate values.

The annotations show Uniform's last exact-positive point at 25 km and first
exact-negative point at 26 km, while MB remains positive at the largest
exact-tested point, 30 km. Binomial is omitted with the no-safe-exact-dataset
note. This is visualization-only; the EVID-0102 conclusions, blockers, and
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` lifecycle are unchanged.

## Latest named common-feasible figure export (2026-09-30)

EVID-0103/DEC-0087 exported the requested `skr_vs_distance` PNG/PDF,
`skr_distance_table.csv`, and optional `betaIAB`/`chiBE` figures from the
EVID-0102 exact envelope. The export retained 13 exact-tested distances for
Uniform and MB, including the 21.9393102292-km fixture, and did not add
source moments or interpolation. All rows remained inside `0 < V_A <= 1.5`
with the `n_peak_photons=30.0` guard. Binomial is explicitly omitted for
lack of a safe current-compatible exact C,w dataset.

This is a named diagnostic asset export, not a new evaluation or a
publication-quality result. The exact-grid conclusions and lifecycle state
from EVID-0102 remain unchanged: MB is above Uniform at all tested points,
Uniform changes sign between 25 and 26 km, and MB remains positive through
30 km. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest common-feasible Uniform/MB diagnostic (2026-09-30)

EVID-0102/DEC-0086 enforced the same `0 < V_A <= 1.5 SNU` budget for both
protocols under the revised `w0=0.10 m`, `D_r=0.55 m` baseline. It evaluated
5 of 8 safe exact Uniform candidates and 5 of 30 safe exact MB candidates;
the remaining rows were excluded by the common budget. Peak feasibility was
checked identically with `n_peak_photons=30.0`. No source moments or C,w
interpolation were used.

MB is above Uniform at all 13 exact-tested distances. Uniform's last exact
positive is 25 km and first exact negative is 26 km. MB remains positive
through the largest exact-tested distance, 30 km. The gains are
`0.0442303289` bits/use at 22 km and `0.0238529688` bits/use at 25 km.
The best feasible exact MB parameters at both distances are
`nu=0.2`, `V_A=1.3833230303`.

The observed advantage is primarily larger `beta I_AB`: at 22 km lower
`chi_BE` also helps, while at 25 km MB `chi_BE` is higher than Uniform and
partly offsets the larger classical term. This remains a diagnostic-only
cache-envelope result, not a continuous optimum, common exact-VA grid,
baseline selection, or publication result. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest revised Uniform/MB distance diagnostic (2026-09-30)

EVID-0101/DEC-0085 compared the revised `w0=0.10 m`, `D_r=0.55 m` optical
fixture with `tau_zen=0.92`, `epsilon_ch=0.0186`, `beta=0.95`, AO OFF, and
phase noise OFF. It recomputed the channel at 12 exact-tested distances from
19 to 30 km. The run evaluated all 8 current-compatible exact Uniform rows
and all 30 current-compatible exact MB rows at every distance; no source
moments or interpolation were used, and Binomial was excluded for lack of a
safe exact C,w dataset.

The MB best-exact-tested envelope is above Uniform at every tested distance.
Uniform's last exact positive is 25 km (`SKR=5.9111913793e-4`, `V_A=0.8`)
and its first exact negative is 26 km (`SKR=-2.9334046616e-4`, `V_A=0.8`).
MB remains positive at 30 km (`SKR=1.0681535110e-2`, `nu=0.15`,
`V_A=3.5548673905`). At 22 km the SKRs are `0.0082792999` (Uniform) and
`0.0744226542` (MB); at 25 km they are `0.0005911191` and `0.0336534193`.

This is a diagnostic-only exact-cache comparison, not a continuous optimum,
common feasible grid, operation-distance estimate, baseline selection, or
publication result. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest revised Uniform optical baseline diagnostic (2026-09-30)

EVID-0100/DEC-0084 tested the requested `w0=0.10 m`, `D_r=0.55 m` geometry
with `tau_zen=0.92`, `epsilon_ch=0.0186`, `beta=0.95`, AO OFF, and phase
noise OFF. Recomputed primary-channel values are
`omega_L,eq=1.4180699494 m`, `A0=0.9981187282`, `T_eff=0.2032273703`, and
`6.9201780236 dB` total loss. On the 8 available exact Uniform C,w rows, the
best tested row is `V_A=1.075`, `SKR=0.00855162790745` bits/use; the exact
requested positive rows available in the cache are `V_A=0.6,0.7,0.8,1.075`.

The old receiver with the new `w0` remains negative, so the recovery is
primarily due to the larger receiver aperture in this diagnostic. Sparse exact
candidate bisection gives `D_r≈0.5113500300 m` and a revised-baseline
distance crossing near `25.6127085762 km`; neither is a continuous optimum or
selected design. `w0=0.10 m` is physically consistent with `D_t=0.25--0.30 m`
at truncation ratios `2.5--3.0`.

The requested V_A sweep is incomplete: 11 of 15 requested values lack exact
C,w, so no interpolation, source-moment generation, adaptive V_A refinement,
baseline selection, or publication-scale distance claim is allowed. The
current `FINAL_MODEL_SPEC.md` hash also differs from the historical expected
hash and remains an explicit blocker. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Latest Uniform beam-waist/receiver diagnostic (2026-09-30)

EVID-0099/DEC-0083 completed a cache-only optical sweep with AO and phase
noise OFF, `epsilon_ch=0.0186`, and `tau_zen=0.92`. At fixed `D_r=0.08 m`,
no tested `w0` from `4.4--150 mm` produced positive SKR on the 8 available
exact Uniform C,w candidates. The best tested row over the sweep was still
negative (`K≈-3.069622e-6` at `w0≈105.397 mm`, `V_A=0.1`).

The 2D coarse control found positive rows only at `D_r=1 m`; the first coarse
positive pair was `w0=30 mm,D_r=1 m`, with `K≈1.69054475e-3` at 21.94 km.
Sparse exact receiver thresholds range from about `0.511 m` to `0.953 m` for
the tested positive-waist rows. That pair's cache-only operation-distance
estimate is `23.6922059451 km`.

This does not determine a continuous `w0_crit` or a Uniform optimum: most
requested V_A points lack exact C,w and the requested `[0.01,5]` domain is
outside the current frozen `[0.1,4.0]` domain. No source moments were created,
no interpolation was used, and no transmitter/receiver baseline was selected.

## Latest HAP-UAV/Sayat forensic diagnostic (2026-09-30)

EVID-0098/DEC-0082 identify `35.9369 dB` current effective loss, dominated by
`32.7197 dB` finite-aperture/beam coupling and `2.7548 dB` pointing jitter.
All 8 available exact Uniform points are negative with phase/AO off; the best
tested value is `K=-4.3454249141616776e-5` at `V_A=0.1`. The exact continuous
Uniform optimum is unresolved because most V_A points lack exact C,w.

Sparse-exact diagnostics place the tested-candidate thresholds at
`T_eff≈0.0898275`, `epsilon≈0.00540667`, and receiver diameter `≈1.52931 m`.
No new source moment, model change, baseline selection, or publication-scale
run occurred.

## Latest phase-noise sensitivity diagnostic (2026-09-29)

EVID-0097/DEC-0081 restored the original `D_r=0.08 m` aperture and swept only
`C_n,phi^2` at 19 km. MB-with-AO and MB-without-AO become positive at
`1e-18`, but Uniform remains negative (`K=-4.975513931165798e-05`). No
all-positive phase threshold was found; the full distance sweep was not run
and no new C,w was computed.

## Latest aperture sensitivity diagnostic (2026-09-29)

EVID-0096/DEC-0080 tested receiver diameters `0.08--0.16 m` at `L=19 km`
using 8 historical exact Uniform and 30 historical exact MB candidates.
Uniform and MB-without-AO remained negative at every tested diameter, so no
diameter satisfied the all-positive gate. The requested full distance sweep
was not run; no aperture was selected and no new C,w was computed.

## Latest historical exact distance diagnostic (2026-09-29)

EVID-0095/DEC-0079 produced the three-curve Uniform/MB-AO/MB-noAO envelope
using only audit-approved historical C,w. The MB-AO sign bracket is 31--33 km
with historical-exact linear estimate 31.409924920888173 km; Uniform and
MB-noAO remain negative over 19--100 km. This is not a final publication
figure and does not resolve sparse Uniform optimization or Binomial absence.

## Latest historical C,w audit (2026-09-29)

EVID-0094/DEC-0078 completed a read-only repository-wide C,w inventory. It
found 6,876 indexed records, 77 hash-identifiable ensembles, 75 duplicate
groups, and 148 superseded/wrong-AP-w records. Only 7 of the 162 planned
distance-experiment combinations have safe current hash-bound exact matches;
no Binomial combination is safe. No historical C,w was migrated and no new
source moment was computed.

The next distance experiment must use only the seven safe matches or remain
pending for the other candidates. Historical records marked validation-needed,
unknown, or superseded cannot silently enter the active cache.

## Latest exact AP coverage batch (2026-09-28)

EVID-0093/DEC-0077 record the restartable exact AP batch. Successful coverage
is `19/143` global, `26/59` local high-priority mesh, `9/18` boundary, and
`8/43` uniform. Remaining points are explicitly incomplete or failed closed
after the existing one-hour AP subprocess timeout; no interpolation or
surrogate was used. The best exact interior remains `(0.24,1.95)` with
`SKR=2.1544608008872113e-05`; the best tested boundary is `.275` with
`SKR=2.1507318654867557e-05`.

Classification remains `GLOBAL_OPTIMUM_UNRESOLVED`. Do not run boundary scalar
refinement, select the uniform baseline, claim gain decomposition, training,
or publication-scale evaluation. Resume only with the same exact cache and an
explicit runtime decision for the AP timeout.

## Latest global joint MB/V_A coverage diagnostic (2026-09-27)

EVID-0092 records the authorized cache-bound global follow-up. The requested
143-point feasible grid, 18-point boundary grid, and 43-point uniform scan
were emitted with exact-cache status per row, but only 15, 5, and 5 rows had
hash-matched exact source moments available. The result is therefore
`GLOBAL_OPTIMUM_UNRESOLVED`: no Brent/golden search, continuous derivative-free
search, global optimum claim, or optimized uniform baseline selection.

The best exact point currently tested remains `(nu_raw,V_A)=(.24,1.95)` with
`SKR=2.1544608008872113e-05`; the best tested boundary row is `.25` at
`V_A=2.133332719960486` with `SKR=2.1311057548123425e-05`. All model,
security, phase-noise, peak, PMF, and lifecycle rules remain unchanged.

## Latest joint MB/V_A exact landscape (2026-09-27)

EVID-0091/DEC-0075 complete the authorized joint diagnostic over the curved
peak-feasible region. The sparse exact grid and local stencil identify
`(nu_raw,V_A)=(.24,1.95)` with `SKR=2.1544608008872113e-05` as the best tested
local point. This is not a global optimum certificate: no global scalar/2D
optimizer ran, and the wider domain remains only sparsely sampled.

The fixed-V_A=2 MB result is therefore only a diagnostic slice; modulation
variance materially changes MI and phase noise. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, with no baseline selected.

## Latest authorized exact-MB boundary stage (2026-09-27)

EVID-0090/DEC-0074 recognize the narrow author authorization for exact-MB
optimization/asymptotic certification while preserving the global publication
lifecycle. Exact finite-positive-PMF points `.20,.22,.25` pass and SKR rises to
`2.152060894113902e-05` at `.25`. At `.30` and above, the unchanged hard peak
constraint rejects the normalized ensemble; no finite turnover or valid scalar
search bracket exists before that physical boundary.

A separate four-symbol QPSK-like reduced-support diagnostic is recorded but is
not production finite-`nu` evidence. The MB limit classification remains
`UNRESOLVED`; no bounded optimizer or baseline selection ran.

## Latest MI reconciliation (2026-09-27)

EVID-0089/DEC-0073 reconciles the old stochastic coarse MI against the new
deterministic GH evaluator using identical ensemble/channel inputs. The old MI
trend is `STOCHASTIC_COARSE_ONLY` (maximum reconstructed z `2.742`); the
65536-sample MC/GH cross-check has maximum z `0.3857`.

The deterministic low-SNR coarse SKR grid has its largest tested value at
`nu_raw=0.20`, `K=2.145553668606579e-05`, after replacing old MC MI. This is
not a continuous optimum. Exact arbitrary SKR point evaluation is ready by
the existing common evaluator, but bounded optimized-MB search remains blocked
by lifecycle authorization.

## Latest deterministic MI certification (2026-09-27)

EVID-0088/DEC-0072 certify deterministic float64 Gauss-Hermite MI for the
existing common MB ensemble. The exact raw-to-repo factor `42.5`, PMF-dependent
`V_A` normalization, PMF/geometry factorization, quadrature convergence, and
autodiff-vs-central-difference derivatives passed. The selected GH order is 8;
the existing MC evaluator agrees within the 65536-sample validation error.

This removes the MI-only noise blocker, not the full-SKR derivative blocker:
AP C,w/Holevo remains evaluation-only. Full-SKR bounded search and Adam remain
`NOT RUN` under lifecycle gating; no continuous optimum or baseline was selected.

## Latest exact common-ensemble TEST2 diagnostic (2026-09-27)

EVID-0087/DEC-0071 implement the exact MB evaluator with the mandatory
`nu_repo=42.5*nu_raw` conversion, exact ensemble hashes shared across MI,
source moments, and Holevo, and implementation/config-bound source caching.
The seven-point `V_A=2` coarse landscape peaks numerically at `nu_raw=0.16`,
`K=8.106128035987757e-05`; this is not a continuous optimum.

FD readiness around 0.16 failed: gradients at `h=0.01` and `0.005` are
unresolved relative to paired CRN stderr and do not meet stability tolerance.
Physical TEST2 Adam therefore remains `NOT RUN`; TEST3 remains `NOT RUN`.
EVID-0084/EVID-0085 cached-sweep SKRs are
`SUPERSEDED_INVALID_COMMON_ENSEMBLE` because MI and C,w used different MB
parameter conventions.

## Latest optimizer diagnostic (2026-09-26)

EVID-0086/DEC-0070 verify that Adam plus central finite differences works on
the known synthetic objective: final `(nu,V_A)=(0.170206,2.201044)` versus the
known `(0.17,2.2)` maximum, with stable FD derivatives. Its source-availability
blocker is superseded by EVID-0087. Physical nu-only and joint optimization
remain `NOT RUN` because the exact common-ensemble FD readiness gate failed.
No interpolation or physical-optimum claim was made.

## Latest MB phase-strength rebound (2026-09-25)

EVID-0085/DEC-0069 rebound the supplied MB C,w diagnostic with
`C_n,phase^2=9.4e-18 m^-2/3` instead of `1e-16`. The same conditional channel
and AO=0.95 settings were used. All ten rows are positive; the numerical grid
maximum is `nu_MB=0.20`, `K=0.00004194428949251256`. This remains diagnostic
only and does not select a production baseline.

## Latest MB channel diagnostic (2026-09-25)

EVID-0084/DEC-0068 applied the supplied historical MB `C,w` rows to the
conditional new-channel effective evaluation at `tau_zen=0.92`,
`zeta=30 deg`, `V_A=2`, and `eta_AO=0.95`. All ten rows passed finite/physical
checks; all raw SKRs were negative, with the least-negative grid value at
`nu_MB=0.20`, `K=-0.00018194195597724065`. This is diagnostic-only and does
not select a baseline or change lifecycle authorization.

## Latest channel consistency correction (2026-09-25)

EVID-0083/DEC-0067 apply the latest manuscript channel formulas to the active
interface and conditional PDF diagnostic. Direct `tau_zen` attenuation,
`C_n^2(0)=1e-14`, the slant finite-aperture denominator, explicit `F0`, and
the manuscript beam-spread/equivalent-pointing path are implemented. Kruse and
older homogeneous/generalized paths remain explicitly legacy. Production
`tau_zen` is intentionally `null`; configuration-driven generation fails
closed until the author selects one of the manuscript MODTRAN scenarios.
This is channel-only work and does not alter security or lifecycle gates.

Last updated: 2026-09-30 (EVID-0106 / DEC-0090; latest visualization-only redraw)

## Previous channel-model audit (2026-09-16)

EVID-0082/DEC-0066 bind the attached manuscript channel scenario for
channel-only diagnostics. The active sampler now derives the Hufnagel–Valley
finite-aperture scintillation variance (`v_sc=0.01434494998119213`), uses the
manuscript pointing/AoA values, preserves the exact outage atom, and keeps
phase noise outside (p_T). The PDF/moment artifact and focused 63-test suite
pass. This does not change the frozen security scope or authorize training,
baseline selection, final-test access, or publication-scale work.

## Latest completed numerical result (2026-09-12)

EVID-0081 and DEC-0065 record completion of the authorized frozen
PS+V_A median task. The existing repaired-objective checkpoint and exact
binary64 candidate inputs were reverified. The 1050 diagnostic row and the
1250/1450 acceptance pair each resolved all four 64x64 sectors with total
support 256, and the acceptance pair passed the frozen C/w convergence rule.

The authoritative median source moments are
`C_PSVA=0.8610813007552428909072445071897962976560950806268` and
`w_PSVA=0.0067220381757562110710871873472856506670610666856165`.

The one exact median full-Z point returned
`Z_L=0.25403343722167576`, `Z_U=0.258948630366243`,
`Z_star=0.25403343722167576`, `I_AB=0.01569902141495305`,
`chi_BE=0.014533912528089`, and raw `K=+0.0003801578161163992`; its
interval check passed. Exact median ranking is `PS_VA_MEDIAN_BEST`, with
PS+V_A > Full > MB. This is median-only evidence and does not establish the
unrun poor/good ranking or a publication claim.

The immutable machine-readable result is
`results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json` (SHA-256
`9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`), with
the durable report at
`docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md`.

The next recommended task is separately authorized exact poor+good ranking
only. Do not execute it from this state. Lifecycle and adaptive-training
gates remain closed.

## Terminal status

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

No publication-scale training, baseline selection, optimized-MB search,
final-test access, held-out evaluation, or publication claim is authorized.

## Historical numerical decision boundary before EVID-0081 (2026-09-12)

EVID-0078 and DEC-0062 supersede the earlier worker-bug hypothesis for the
current median-checkpoint interpretation. The unchanged worker resolves the
median PS case at 800/900 and 1000/1200 digits and the matched Full case at
800/900 digits, with stable C,w and 256/256 support in every sector. An
independent direct 256-state weighted Gram at 100 digits reproduces the
Fourier off-block and sector-match structure for both cases; its global
spectrum was deliberately NOT_RUN.

The current dense-check decision is exactly
LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT. The immediate
AP-blocker classification is exactly INSUFFICIENT_AP_PRECISION. The remaining
analysis blocker is the incomplete three-state exact PS+V_A adaptive
ranking, not a demonstrated worker or fail-gate defect.

The bounded follow-up task specified by DEC-0062 was subsequently executed as
EVID-0079; its partial result is recorded below. The 700--900-digit dense
global target is STOPPED unless a surviving mismatch or explicit external
audit requirement creates a new testable hypothesis. Lifecycle and
adaptive-training gates remain closed.

## Historical bounded audit result before EVID-0081 (2026-09-12)

EVID-0079 and DEC-0063 record the authorized follow-up. The independent
watchdog completed the frozen median PS+V_A global row at 80 digits, timed
out the PS 120-digit row, and did not start PS 200 or any Full row. It
finished in 899.0290027 of the 900-second budget with status
`DENSE_LOW_PRECISION_COST_BOUNDED_SKIP`.

The PS 80-digit row passed the direct global weighted-Gram invariants,
Fourier off-block check, production-sector comparison, and resolved
global-spectrum/sector-union comparison. It resolved 48 modes above the
diagnostic 1e-60 threshold. This is structural diagnostic evidence only;
the Full side was not globally completed and no support certificate follows.

The dense decision remains exactly
`LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT`, and the
immediate AP diagnosis remains exactly `INSUFFICIENT_AP_PRECISION`. The low-
precision global audit is now a bounded partial result, not the current next
task. The next permitted numerical task is
`DETERMINE_MINIMUM_SECTOR_AP_PRECISION_FOR_FROZEN_PS_VA`: determine the
minimum reproducible sector AP precision, compute exact C,w, and then evaluate
only the median full-Z security point. Do not execute that task from this
state entry.

No production code, model/security definition, or lifecycle gate changed.
Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive-training
readiness remains NOT_READY_FOR_ADAPTIVE_TRAINING.

## Historical research-only precision decision before EVID-0081 (2026-09-12)

EVID-0080 and DEC-0064 record the research-only numerical-analysis
investigation of the remaining frozen PS+V_A source-moment blocker. The
selected category is exactly
`DIRECT_HIGHER_PRECISION_SECTOR_RUN`.

The next source-moment computation should start the fixed ladder at 1050
decimal digits and confirm the acceptance rows at 1250 and 1450 digits using
the existing four 64-by-64 C4 sectors. The existing frozen
`1050,1250,1450` ladder remains unchanged; 1250 is the first
acceptance-grade row after the existing 800/900 and 1000/1200 diagnostic rows.
After the source-moment ladder passes, evaluate only the median full-Z point.
Do not run a dense high-precision
global eigensolve, 1600/2000-digit escalation, outcome-driven mixed
precision, a new Arb backend, a source-moment reformulation, training, or
final-test work.

The memo estimates the current PS minimum mode at approximately `5.52e-598`,
proves the weighted-Gram `p_min` lower bound, and shows that the current
probability minimum can account for only about 0.30 decimal orders relative
to uniform at fixed geometry. Existing high-precision rows remain diagnostic
until rebound under the frozen acceptance protocol. No numerical run or
security result was executed by EVID-0080.

At that historical decision boundary, the exact next numerical task was
`DETERMINE_MINIMUM_SECTOR_AP_PRECISION_FOR_FROZEN_PS_VA`, now with the
direct 1050/1250/1450 sector specification in EVID-0080. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive-training readiness remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`.

## Bounded analysis result before EVID-0078

EVID-0074 and DEC-0058 record the completed analysis-figure workflow. The
isolated `TRAINING_SURROGATE_ONLY` source-moment path passed Case-A
directional calibration and four nearby full-support checks. It drove only a
50-step search over six methods on 16 active representative Case-D states,
with explicit outage mass `0.268` and phase disabled (`c_phi=0`,
`epsilon_total=epsilon_base`).

Eight exact AP anchor jobs (MB plus seven Full states) converged at the
800/900-digit ladder. The existing corrected full-Z security chain was used
for the anchor table; all 21 exact-vs-surrogate method orderings were
consistent. However, every active exact raw-K anchor is negative, and the Full
exact-bin estimate `-0.0015155352` is worse than the fixed MB baseline
`-0.0011516261`. Classification: `MIXED_PRELIMINARY_SUPPORT`.

The six SVG outputs are `ANALYSIS_FIGURES_READY` and analysis-grade only. The
surrogate security estimates are not authoritative, and publication status is
`NOT_PUBLICATION_CERTIFIED`. The next recommended investigation is the
Full-vs-MB surrogate/objective mismatch; no publication run is justified by
this result.

EVID-0075 and DEC-0059 now resolve the primary part of that mismatch: the
smooth search `tanh` maps `Z` below `Z_L` in all 16 active states, so it is not
an interval-preserving approximation to the frozen full-Z objective. The
weight audit passes (`0.732` active mass, `0.268` outage mass, total one), and
the raw negative-rate convention remains intentional. The current positive
joint-adaptation novelty is therefore `CURRENT_NOVELTY_NOT_SUPPORTED` until
the objective is repaired and rechecked.

EVID-0076 and DEC-0060 record the completed bounded objective repair. The
repaired runner uses the existing physical `[Z_L,Z_U]` interval and full-Z
maximizer, with `0/96` interval violations, corrected Case-A agreement,
existing exact-anchor rank consistency, and finite PS/GS/V_A gradient smoke.
The bounded PS+V_A and Full searches each passed the 20-step smoke and ran
50 analysis steps. The three-state exact check found Full above MB at all
available states, but the optimized PS+V_A AP source rows failed closed at the
full-support gate, so no complete adaptive ranking or novelty claim follows.
The final classification is `FULL_Z_SEARCH_OBJECTIVE_REPAIRED`; novelty stays
`CURRENT_NOVELTY_NOT_SUPPORTED` and the lifecycle stays

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.


Historical EVID-0077 and DEC-0061 record the earlier root-cause audit for the remaining
optimized PS+V_A exact source-moment blocker. The PS anchor has positive,
moderately shaped probabilities (p_min approximately 0.00163--0.00228 and
logit range below 1.51), and the weighted-Gram q_min scale check does not
support probability concentration as the primary cause. The direct worker
inputs use exact binary64 hex transfer. A 300-digit read-only probe resolves
only 206 modes for both PS median and Full median, while Full resolves at
800/900 digits and PS still fails closed at that ladder. This leaves
precision/conditioning relevant but does not distinguish a PS-specific worker
failure from genuine conditioning.

The historical selected next category was
INVESTIGATE_AP_WORKER_BUG; DEC-0062 supersedes it for the current median
diagnosis. The next and only permitted numerical action for
this blocker is a one-checkpoint median PS worker decomposition with direct
hex replay, captured 300/400/600/800/1000/1200-digit rows, and an independent
C4-sector or factorization cross-check using Full median as a positive control.
No q floor, PS parameterization reduction, C/w reformulation, or precision-only
change is selected. The lifecycle and adaptive-training status remain
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and
NOT_READY_FOR_ADAPTIVE_TRAINING.


## Current model status

- The current intended mathematical target is recorded in
  FINAL_MODEL_SPEC.md, including the pre-action state
  \(S=(T,\epsilon_{\mathrm{base}})\), post-action
  \(\epsilon_{\mathrm{total}}\), phase surrogate, physical fading target, and
  full \(Z\)-interval security definition.
- Current FINAL_MODEL_SPEC SHA-256:
  8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843.
- This replaces the historical implementation-spec hash
  561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1;
  old artifacts bound to that hash are historical evidence for the former
  scalar-epsilon/lower-endpoint path, not certification of the new target.
- The transmitter architecture, C4 invariants, raw-SKR loss, average-energy
  dual, and finite-realization hard peak guard remain present in source.
- The causal phase/post-action epsilon chain and canonical scenario-level phase
  provenance are aligned in source and active evaluation plumbing, but its
  C_n_phi2 value remains null. The composite channel architecture and raw-T
  diagnostics are implemented, while production scintillation/AoA mappings
  remain unresolved. The
  full physical Z interval, structured empty-domain failure, and deterministic
  bounded Holevo maximization are now implemented and focused-tested. The
  repaired objective audit is analysis-only and does not rebind publication
  security evidence.
- Mixed batches now evaluate only active \(T>0\) rows; outage rows remain
  \(T=0\), bypass the policy, receive raw \(K=0\), and do not receive fake
  gradients. The relative transmittance diagnostic and signed mean difference
  are both emitted.
- The Case B/C nonzero transmittance discrepancy was traced to unpaired
  proposal-versus-admitted populations. Manuscript delta_T now uses paired
  retained raw/physical samples; proposal_delta_T preserves the extra diagnostic.

## Current PRE-Numerical channel alignment

- The active sampler now composes direct-tau eta_atm, normalized lognormal
  H_sc, the manuscript Gaussian-equivalent H_p path, and optional hard AoA
  B_AoA, with raw/physical diagnostics and no clipping or floor. Explicit
  legacy calls retain the generalized Rician path.
- The legacy constant-C_n^2 beam-wander equation is not used by the active
  sampler. sigma_z is excluded from pointing variance and yaw from AoA
  orientation variance.
- Explicit HV profile Rytov support, the corrected finite-aperture mapping,
  AoA gating, and channel provenance are implemented for resolved inputs. The
  atmospheric `tau_zen` scenario and profile-to-effective-phase mapping remain
  unresolved; unresolved choices fail closed.
- Full-Z resolution diagnostics now cover 17/33/65/129 candidate grids.
  They are numerical validation evidence only, not certification.

## Numerical and security gate

- Existing MI/Gram artifacts remain scoped to the prior code path.
- The C4 Gram production backend is cutoff-independent and the arbitrary-
  precision fallback is evaluation-only.
- Full-interval covariance/entropy candidates use the existing physicality
  guard and explicit diagnostics.
- Support/tolerance approval remains unresolved; no security/SKR figure may be
  presented as target-model evidence.
- Existing test artifact results/current_test_suite.json is a
  LAST_KNOWN_PASS for its recorded repository/model provenance, not a current
  pass for the edited target specification. The scoped channel/security
  verification for this milestone passed 90 tests; the current focused outage
  regression passed 20 tests; worker-backed
  full-support/pointwise certification tests were not completed. No
  certification or publication-scale test was run.
- The corrected B-D rebind focused suite passed 44/44 tests. The repository
  AP-equivalence test is `BLOCKED_BY_ENVIRONMENT`: one test passed, one slow
  test was skipped, and three tests errored because ignored historical or
  corrected-A JSON fixtures are absent from this checkout.
- The broader focused gradient/optimizer selection remains FAILED with four
  FULL_SUPPORT_FALLBACK_EVALUATION_ONLY errors; this pre-existing numerical
  boundary was not weakened.
- The exact uniform exploratory Gram failure is classified as
  FLOATING_POINT_ROUNDOFF plus NUMERICAL_ILL_CONDITIONING: 256 positive
  probabilities and unique coherent states, Hermitian sectors, singular values
  near \(10^{-20}\), and AP residual negatives shrinking through 600 digits.
- The old worker-backed Case A result is superseded because its AP (w) used
  `aa=sr*x2.T`. The corrected AP worker resolves 256/256 modes at both 800 and
  900 digits with (C=0.8598511065), (w=0.01832761047), and minimum
  eigenvalue (3.973e-618). Corrected full-Z gives
  \(\chi_{BE}^{ub}=0.01518919003\) and raw \(K=0.00475763549\).
  This remains bounded exploratory evidence only.
- The differentiable complex128 source-moment investigation is classified
  EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128. No stable exact C/w gradient
  formulation was found; adaptive training remains blocked.
- The previous B-D bounded full-Z subset is marked `SUPERSEDED_WRONG_AP_W` and
  is not current evidence. EVID-0067 records the new bounded corrected B-D
  rebind using reconstructed evenly-spaced active rosters, because the prior
  ignored artifact and exact indices were unavailable in this checkout. The
  new result remains exploratory and evaluation-only.
- The isolated AP custom-backward prototype passes four cheap independent
  fixtures and complex-alpha convention checks, but its bounded 800-digit PS
  target VJP is materially wrong (`3.3995e+102` versus corrected AP
  `0.001774...`). It is classified `AP_CUSTOM_BACKWARD_NOT_VALIDATED`; no
  256-state production directional gradient claim or adaptive-training
  authorization exists. The old reverse and full-Z backward were not run;
  the isolated forward tangent is recorded separately in EVID-0070/0071.
- The full-support differentiable source-moment research audit is recorded in
  FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md. It confirms the
  forward tangent equations, quantifies the inverse-spectrum scales, and
  recommends an exact C4 constrained-solve tangent before any reverse repair.
  This is research-only evidence and does not change the security model or
  lifecycle state.
- The isolated C4 constrained-solve forward tangent is now validated for the
  recovered Case-A PS direction and the remaining GS-real, GS-imaginary, and
  V_A directions at the bounded 800-digit target. Each target has positive
  probabilities, 256 unique states, 256/256 resolved support, and dC, dw, and
  dJ agreement with corrected AP central differences below 1e-6. The combined
  result is `FULL_SOURCE_FORWARD_TANGENT_VALIDATED`, diagnostic-only. Target
  direction totals were 2001.04 s (GS-real), 2878.94 s (GS-imaginary), and
  1795.96 s (V_A), so no practical production gradient or adaptive-training
  authorization exists.
- The constrained reverse practicality study is recorded in
  CONSTRAINED_REVERSE_PRACTICALITY_STUDY.md and EVID-0072. Its solve-based
  adjoint is mathematically sound as a design, but primitive identities,
  target reverse validation, and compiled timing remain unrun. Select
  SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE; this does
  not authorize a complete reverse, full-Z backward, or training.
- The 37-section deep research refinement is recorded in
  DEEP_RESEARCH_SOURCE_MOMENT_REVERSE_GRADIENT.md and EVID-0073. It derives
  the right-solve and square-root Sylvester adjoints, gives conservative
  value-error propagation from \(C,w\) into the \(Z\) interval, rejects
  unannounced spectral truncation, and selects C++17 MPFR/MPC point
  arithmetic as the primary compiled prototype with Arb/acb_mat as a
  certification/reference mode. It is design evidence only; no reverse VJP
  or security certification occurred.

## Friday preliminary diagnostic posture

| Class | Status | Scope |
|---|---|---|
| Regular 256-QAM, fixed PMFs, C4 orbit geometry | READY_NOW | Deterministic, data-free transmitter diagnostics |
| Current composite-channel T diagnostics | ALIGNED_API_ONLY | Explicit conditional tau/profile inputs are supported; production tau selection and common-phase mapping remain blocked |
| Target phase parameterized run, scintillation, AoA, raw-T, p_gt_1 | BLOCKED | Production tau selection and common-phase mapping remain unresolved |
| Target epsilon_total and full-interval chi_BE/SKR | ALIGNED_API_ONLY | Epsilon chain and interval implementation exist; target C_n_phi2, channel paths, and numerical evidence rebinding remain unresolved |
| Learned PS/GS/V_A outputs | BLOCKED | Training is closed and target security is not aligned |

## Preliminary figure readiness audit

| Figure | Status | Exact reason |
|---|---|---|
| Regular 256-QAM | READY NOW | Deterministic construction exists in qam256.py |
| Uniform / Binomial / MB PMF | READY NOW | Deterministic PMF constructors exist |
| Fourfold orbit visualization | READY NOW | Exact C4 index and expansion functions exist |
| Phase-noise curve xi_phase(V_A) | BLOCKED | c_phi API exists, but no author-approved C_n_phi2 is configured |
| epsilon_total(V_A) | ALIGNED_API_ONLY | Post-action chain is implemented; target plotting remains parameter-blocked |
| H_sc Monte Carlo | ALIGNED_API_ONLY | HV finite-aperture v_sc mapping is implemented; production tau selection remains unresolved |
| H_p Monte Carlo | ALIGNED_API_ONLY | Manuscript Gaussian-equivalent pointing and PDF diagnostics are implemented conditionally |
| AoA outage Monte Carlo | ALIGNED_API_ONLY | Hard B_AoA gate exists; turbulence-AoA mapping/FOV remains unresolved |
| T_raw histogram | ALIGNED_API_ONLY | Raw product/admission path exists; target parameters remain unresolved |
| Physical T histogram | ALIGNED_API_ONLY | Composite physical sampler exists; target parameters remain unresolved |
| p_gt_1 diagnostic | ALIGNED_API_ONLY | p_above_one is recorded by the sampler; target parameterization remains unresolved |
| chi_BE(Z) interval diagnostic | ALIGNED_API_ONLY | Full physical intersection and deterministic max diagnostics exist; target parameter and numerical gates remain blocked |
| Baseline K versus T | BLOCKED | Full-interval security and numerical gate are unresolved |
| Baseline K versus V_A | BLOCKED | Full-interval security and numerical gate are unresolved |
| Learned PS/GS/V_A output | BLOCKED | Training is closed and target security is not aligned |

## Exploratory case outcome

Cases A--D are now bound to corrected exploratory evidence with \(N=1000\)
channel samples per case. Corrected Case A and the bounded corrected B-D
source-moment/full-Z subset remain evaluation-only; the old worker-backed
Case A/B-D security artifacts are superseded. See EVID-0066, EVID-0067, and
EVID-0068, and the superseded artifacts.

## Historical exact next permitted action

The repaired objective is accepted for bounded analysis only. The one
remaining numerical blocker is the missing converged exact PS+`V_A` source-
moment/ranking result. Under DEC-0061, the next task is a read-only
median-checkpoint AP-worker decomposition with direct binary64 hex replay,
captured 300/400/600/800/1000/1200-digit rows, and an independent C4-sector or
factorization cross-check using Full median as a positive control. Do not add a
q floor, change the PS parameterization, reformulate C,w, or increase precision
as the sole change. Keep complete reverse execution, full-Z backward, adaptive
training, baseline selection, final-test access, and publication-scale
evaluation closed.

## Lifecycle restrictions

Do not run training, publication-scale Monte Carlo, long Gram/Holevo
certification, threshold approval, or final-test evaluation. Do not silently
replace the target equations with the current implementation.

## Current evidence

- EVID-0054: 2026-09-10 documentation/source/config/manuscript availability
  audit.
- EVID-0055: 2026-09-10 causal phase/post-action noise implementation and
  focused verification; parameter readiness remains open.
- EVID-0056: 2026-09-10 full physical Z-interval implementation and focused
  interval/gradient verification; target numerical rebinding remains open.
- DEC-0040: documentation-only alignment; unresolved model/code mismatches are
  retained as blockers.
- DEC-0041: full Z-interval implementation; no lifecycle or numerical approval
  was granted.
- EVID-0057: 2026-09-10 Cn_phi2 scientific/configuration freeze audit and
  focused provenance verification.
- DEC-0042: retain unresolved Cn_phi2 as null; derive c_phi and persist its
  canonical provenance without granting lifecycle or numerical approval.
- EVID-0058: 2026-09-10 PRE-Numerical composite-channel alignment and focused
  physical/provenance/resolution verification.
- DEC-0043: align the active composite channel while retaining unresolved
  scientific mappings as fail-closed blockers.
- EVID-0059: outage-aware active-state SKR plumbing and 20-test focused pass.
- EVID-0060: four exploratory composite-channel cases; Holevo/K blocked by
  the fast-support gate.
- EVID-0061: exact-ensemble Gram/full-support root-cause audit.
- DEC-0044: authorize only non-publication exploratory cases.
- DEC-0045: preserve the fast gate and keep AP fallback evaluation-only after
  the root-cause audit.
- EVID-0062: one bounded AP-backed Case A full-Z security result.
- DEC-0046: accept Case A as exploratory only; do not generalize or train.
- EVID-0063: bounded B-D full-Z security subset.
- DEC-0047: reuse stable AP source moments only for exact-ensemble exploratory
  B-D subsets.
- EVID-0064: differentiable complex128 source-moment investigation.
- DEC-0048: preserve the fast gate and classify the differentiable path as
  blocked.
- EVID-0065: AP custom-backward feasibility audit; forward w mismatch stopped
  full-support directional validation.
- DEC-0049: keep the AP custom backward isolated and require fallback correction
  plus artifact rebinding before further differentiation work.
- EVID-0066: corrected AP worker, 800/900 source-moment stability, and corrected
  Case A full-Z rebind.
- DEC-0050: accept corrected AP forward/Case A exploratory evidence; defer B-D
  rebind and keep custom backward pending.
- EVID-0067: corrected bounded B-D source-moment/full-Z exploratory rebind;
  44-test focused suite passed, AP-equivalence fixture test blocked by missing
  ignored artifacts.
- DEC-0051: accept corrected bounded B-D rebind as exploratory evidence; keep
  lifecycle and adaptive-training gates closed.
- EVID-0068: cheap corrected AP custom-backward checks passed; bounded PS
  target VJP failed materially and stopped the target suite.
- DEC-0052: keep the custom backward unvalidated and stop before GS/VA/full-Z
  after the bounded PS failure.
- EVID-0069: full-support differentiable source-moment research audit;
  constrained-solve forward tangent recommended; lifecycle unchanged.
- DEC-0053: prefer the exact C4 tangent audit before reverse repair.
- EVID-0070: exact C4 constrained-solve forward tangent; Case-A PS target
  validated at 800 digits, with a 1181.1304-second diagnostic runtime.
- DEC-0054: accept the bounded PS tangent as diagnostic evidence; retain
  `NOT_READY_FOR_ADAPTIVE_TRAINING` and keep the reverse path closed.
- EVID-0071: bounded GS-real, GS-imaginary, and V_A forward tangents passed at
  800 AP digits; all four source directions are forward-tangent validated.
- DEC-0055: accept the four-direction forward tangent diagnostically while
  retaining the practical reverse/adjoint blocker and lifecycle gates.
- EVID-0072: constrained reverse practicality study; solve-based adjoint
  derivation is design-sound, mpmath reverse is skipped, and compiled
  multiprecision primitives are the only next permitted task.
- DEC-0056: select
  SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE; retain
  NOT_READY_FOR_ADAPTIVE_TRAINING and all lifecycle gates.
- EVID-0073: deep research refinement of the reverse-gradient boundary;
  exact right-solve/Sylvester adjoints, security-rigorous value-error
  propagation, backend comparison, and compiled MPFR/MPC primary
  recommendation; no reverse or training authorization.
- DEC-0057: refine the compiled prototype backend to C++17 MPFR/MPC point
  arithmetic with Arb/acb_mat as an independent reference/enclosure mode;
  retain all lifecycle gates.
- EVID-0075: objective/aggregation audit; the smooth search proxy violates the
  full-Z source-moment interval in all tested active states, while fixture
  weight arithmetic passes.
- DEC-0059: repair the interval-preserving objective before interpreting
  learned gains; classify the current positive joint-adaptation novelty as
  `CURRENT_NOVELTY_NOT_SUPPORTED` and retain all lifecycle gates.
- EVID-0076: interval-preserving full-Z objective repair; zero repaired
  interval violations and passing objective/gradient gates, with exact
  PS+`V_A` comparison fail-closed.
- DEC-0060: accept `FULL_Z_SEARCH_OBJECTIVE_REPAIRED`, retain
  `CURRENT_NOVELTY_NOT_SUPPORTED`, and keep the publication/adaptive lifecycle
  gates closed.
- EVID-0077: PS+`V_A` full-support blocker root-cause audit; PMF concentration
  and serialization are not supported as primary causes, while precision,
  conditioning, and a PS-specific worker issue remain unresolved.
- DEC-0061: select `INVESTIGATE_AP_WORKER_BUG`; authorize only the bounded
  one-checkpoint worker decomposition and retain all lifecycle gates.
- EVID-0078: unchanged-worker PS and Full high-control sector convergence
  plus an independent 100-digit direct global weighted-Gram/C4 structure
  audit; dense global spectrum remains NOT_RUN.
- DEC-0062: select LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT
  and classify the immediate AP blocker as INSUFFICIENT_AP_PRECISION; retain
  only the bounded low-precision global audit as the next numerical task.
- EVID-0079: bounded independent global block audit; PS 80 digits completed,
  PS 120 digits timed out, and the remaining requested rows were not started.
- DEC-0063: accept the bounded partial audit, retain the dense/AP diagnoses,
  and select minimum sector-level AP precision for frozen PS+V_A as the next
  task while keeping lifecycle gates closed.
- Existing historical numerical evidence remains in EVIDENCE.md and
  DECISION_LOG.md under its original provenance.
