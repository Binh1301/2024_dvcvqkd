# Project State

Last updated: 2026-09-11 (interval-preserving full-Z objective repair and bounded exact check; prior corrected AP/tangent/reverse evidence retained)

## Terminal status

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

No publication-scale training, baseline selection, optimized-MB search,
final-test access, held-out evaluation, or publication claim is authorized.

## Latest bounded analysis result

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

- The active sampler now composes eta_atm, normalized lognormal H_sc,
  generalized Rician H_p, and optional hard AoA B_AoA, with raw/physical
  diagnostics and no clipping or floor.
- The legacy constant-C_n^2 beam-wander equation is not used by the active
  sampler. sigma_z is excluded from pointing variance and yaw from AoA
  orientation variance.
- Explicit profile Rytov support, v_sc overrides, AoA gating, and channel
  provenance are implemented for resolved inputs. No production profile,
  aperture-averaging, turbulence-AoA, or profile-to-effective-phase mapping
  is frozen; unresolved choices fail closed.
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
| Current composite-channel T diagnostics | ALIGNED_API_ONLY | Resolved inputs are supported; production profile/aperture/AoA choices remain blocked |
| Target phase parameterized run, scintillation, AoA, raw-T, p_gt_1 | BLOCKED | Composite architecture exists, but profile/aperture/AoA/common-phase mappings remain unresolved |
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
| H_sc Monte Carlo | ALIGNED_API_ONLY | Positive unit-mean lognormal sampler exists; production v_sc mapping is unresolved |
| H_p Monte Carlo | SAFE AFTER SMALL FIX | Pointing sampler exists; a raw-data/plot wrapper is missing |
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

## Exact next permitted action

The repaired objective is accepted for bounded analysis only. The one
remaining numerical blocker is the missing converged exact PS+`V_A` source-
moment/ranking result. The next task is a full-support-preserving PS+`V_A`
parameterization or conditioning guard followed by the same three-state exact
AP/full-Z comparison. Keep complete reverse execution, full-Z backward,
adaptive training, baseline selection, final-test access, and publication-
scale evaluation closed.

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
- Existing historical numerical evidence remains in EVIDENCE.md and
  DECISION_LOG.md under its original provenance.
