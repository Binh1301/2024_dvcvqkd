# Project State

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

Last updated: 2026-09-25 (EVID-0083 / DEC-0067; latest manuscript channel correction)

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
