# Project State

Last updated: 2026-09-11 (corrected AP worker and Case A rebind)

## Terminal status

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

No publication-scale training, baseline selection, optimized-MB search,
final-test access, held-out evaluation, or publication claim is authorized.

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
  bounded Holevo maximization are now implemented and focused-tested; target
  numerical evidence remains bound to the prior lower-endpoint path.
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
  is not current evidence. It must be recomputed with corrected (C,w) in a
  separate task; no B-D recomputation occurred here.
- The isolated AP custom-backward prototype remains
  `PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION`; no 256-state directional
  gradient claim or adaptive-training authorization exists.

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

Cases A--D completed as EXPLORATORY_ONLY with \(N=1000\) channel samples each.
The old worker-backed Case A/B-D security artifacts are superseded. Corrected
Case A alone has a current bounded full-Z exploratory result; B-D remain
pending corrected rebind. See EVID-0060, EVID-0066, and the superseded
artifacts.

## Exact next permitted action

Recompute the bounded B-D exploratory subsets using the corrected Case A
source moments; do not execute that task in this lifecycle state.

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
- Existing historical numerical evidence remains in EVIDENCE.md and
  DECISION_LOG.md under its original provenance.
