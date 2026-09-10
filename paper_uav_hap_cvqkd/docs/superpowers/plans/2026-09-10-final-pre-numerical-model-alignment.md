# Final PRE-Numerical Model-Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the source-supported HAP--UAV composite-channel alignment pass while preserving fail-closed behavior for unresolved scientific mappings and the existing lifecycle gate.

**Scope:** Implement and test the active architecture
`C_n^2(h) -> {H_sc, phase/tau/epsilon, optional AoA} ->
eta_atm H_sc H_p B_AoA -> T_raw -> physical T -> policy/MI/Holevo/SKR`.
Retain the old constant-`C_n^2` beam-wander functions only as explicitly marked
legacy diagnostics. Do not invent an altitude-profile-to-`C_n,phi^2` mapping,
an aperture-averaging law, or a turbulence-to-AoA law; unresolved production
choices must fail closed.

**Constraints:** Work in the existing dirty worktree and preserve unrelated
user changes. Do not modify `docs/FINAL_MODEL_SPEC.md`, run training,
publication-scale Monte Carlo, final/held-out evaluation, or certification.
Keep the security order `(T, epsilon_base) -> policy/PS/adaptive VA ->
epsilon_total -> MI/Holevo -> SKR`, the common physical ensemble, and the
implemented full `Z` interval unchanged.

## Task 1: Freeze the audit boundary and write RED tests

**Files:**
- Add: `tests/test_composite_channel.py`
- Add: `tests/test_channel_provenance.py`
- Add or modify: `tests/test_holevo_resolution.py`
- Modify only as needed: existing channel, diagnostics, phase, and pipeline tests

- [x] Record the read-only active call graph and classify current channel,
  diagnostics, training, baseline, validation, held-out, smoke, phase, and
  provenance/hash paths before implementation.
- [x] Add failing tests for Beer--Lambert SI units and the target composition
  `eta_atm * H_sc * H_p * B_AoA`.
- [x] Add failing tests for positive unit-mean lognormal scintillation,
  Rician displacement (including the zero-boresight Rayleigh limit), exclusion
  of `sigma_z`, generalized `H_p` support, and AoA Rayleigh outage.
- [x] Add failing tests for `B_AoA=0 -> T=0`, no floor/clipping, raw-versus-
  physical diagnostics, no `T=1` clipping atom, unsupported aperture mapping,
  unsupported nonzero turbulence AoA, and provenance sensitivity.
- [x] Add failing tests proving the active sampler does not call or use the
  legacy beam-wander variance and that phase provenance describes one common
  turbulence source rather than an independent atmosphere.
- [x] Add the full-`Z` resolution fixture for grid sizes 17, 33, 65, and 129,
  covering interior, lower-boundary, upper-boundary, narrow, and near-boundary
  admissible intervals with explicit tolerances. This validates the existing
  solver; it does not redesign it or certify publication results.

Run the new tests before production changes and retain the expected RED
evidence where the requested APIs are absent.

## Task 2: Implement the smallest source-supported channel primitives

**Files:**
- Add: `src/channel/scintillation.py`
- Add: `src/channel/aoa.py`
- Modify: `src/channel/turbulence.py`
- Modify: `src/channel/pointing_error.py`
- Modify: `src/channel/fso_channel.py`

- [x] Add a sampled altitude-profile interface and the specified
  `sigma_R0^2` integral using SI wavelength, link geometry, and `sec(zeta)`;
  do not equate it to `v_sc` unless an explicit mapping/override is supplied.
- [x] Add normalized lognormal `H_sc` sampling with
  `ln(H_sc) ~ Normal(-v_sc/2, v_sc)` and explicit variance validation.
- [x] Add explicit aperture-averaging resolution: a finite
  `v_sc_override` is accepted only as an explicitly named scenario choice;
  missing/unsupported mappings raise a dedicated fail-closed error.
  No Hufnagel--Valley profile is fabricated where the repository has no
  supported profile parameters.
- [x] Add Rician displacement from independent Gaussian Cartesian components;
  use `sigma_UAV_trans^2=(sigma_x^2+sigma_y^2)/2`, resolved HAP angular-jitter
  convention, and boresight offsets. Do not include `sigma_z` or turbulence
  beam-wander variance in the active pointing scale.
- [x] Preserve the existing manuscript-supported `W_L`, `z_R`, `eta_p0`,
  `Gamma`, and `R` implementation and enforce `0 < H_p <= eta_p0`.
- [x] Add AoA orientation variance excluding yaw, explicit disabled or
  externally validated turbulence-AoA status, Rayleigh magnitude sampling,
  hard FOV gating, and the analytic outage/inlier probabilities.
- [x] Keep the old constant-`C_n^2` beam-wander equation callable only as a
  documented legacy helper; no active target call may reach it.

Run focused primitive tests and `py_compile` before wiring entry points.

## Task 3: Make the sampler physical-domain safe and traceable

**Files:**
- Modify: `src/channel/fso_channel.py`
- Modify: `src/channel/state_distribution.py`
- Modify: `src/channel/diagnostics.py`
- Add or modify: `src/channel/provenance.py` if a small shared record helper is needed

- [x] Generate `T_raw=eta_atm*H_sc*H_p*B_AoA` and expose raw factors,
  outage mask, and provenance in channel metadata.
- [x] Implement active physical sampling as the mixed outage plus
  truncated-renormalized active law. Reject/resample `T_raw>1`; never use
  `min(T_raw,1)`, a positive floor, or a synthetic `T=1` atom.
- [x] Ensure outage states are represented as `T=0` and carry `K=0` semantics,
  while the policy feature path receives only `T>0` states.
- [x] Add diagnostics for `p_out`, `p_in`, `p_above_one`, raw mean, physical
  mean, and relative mean discrepancy, plus the raw identity
  `E[T_raw]=p_in*eta_atm*E[H_p]` when `E[H_sc]=1`.
- [x] Bind geometry, wavelength, visibility, atmospheric model, profile and
  scintillation choices, aperture status, beam/aperture, jitter conventions,
  boresight, pointing shape, AoA status/FOV, raw-to-physical rule, and phase
  status to the emitted provenance record and existing configuration hash.

Run channel/state/diagnostic tests only; do not generate the million-sample
configured diagnostic artifact.

## Task 4: Wire all active entry points without broadening authorization

**Files:**
- Modify: `configs/default.yaml`, `configs/channel.yaml`,
  `configs/baseline_smoke.json`
- Modify: `scripts/_train.py`, `_common.py`, `_numerical_validation.py`,
  `run_baselines.py`, `run_baselines_cached_source_moments.py`,
  `evaluate.py`, `evaluate_baseline.py`, `select_validation_baselines.py`,
  `select_learned_fixed_va.py`, `smoke_validate_frozen.py`, and the channel
  diagnostic wrapper as required by their current call graph

- [x] Add explicit nullable/status fields for profile, scintillation mapping,
  HAP jitter convention, boresight, AoA mapping/FOV, phase mapping, and raw-T
  treatment. Leave unresolved production fields unresolved.
- [x] Route active channel creation through the composite sampler and reject
  unresolved aperture/profile/AoA/phase choices before model execution.
- [x] Keep development/legacy command-line compatibility only where it is
  explicitly labeled test/legacy; it must not become a publication target
  default.
- [x] Preserve the policy input `(log10(T), epsilon_base)` and ensure no path
  sends `epsilon_total` to policy or sends an outage through `log10(0)`.
- [x] Preserve one `epsilon_total` tensor for both MI and Holevo and the same
  ensemble object for both calculations.
- [x] Ensure changed physical choices alter the existing canonical config hash
  and stale-artifact validation remains fail closed.

Run only focused script-resolution, provenance, and pipeline tests.

## Task 5: Correct common-turbulence phase semantics

**Files:**
- Modify: `src/channel/phase_noise.py`, `scripts/_train.py`
- Modify: phase/config/provenance tests and the minimum relevant current-state docs

- [x] Describe `Cn_phi2` as an effective scalar representation of the same
  physical turbulence scenario, with a validated mapping from `C_n^2(h)` still
  unresolved; never use `C_n^2(0)`, an altitude average, or a second atmosphere.
- [x] Keep `tau_phi2`, derived `c_phi`, post-action epsilon, and causal order
  unchanged.
- [x] Require an explicit validated/author-frozen mapping and value for
  production nonzero phase; keep the current production field null and fail
  closed. Test fixtures may use explicit values only as non-production fixtures.
- [x] Record the common turbulence provenance in all active phase records.

Run the focused phase, pipeline, gradient, and baseline-guard tests.

## Task 6: Verify full-Z resolution and unchanged security behavior

**Files:**
- Modify: `tests/test_holevo_resolution.py` and only numerical documentation
  needed to describe the new audit evidence

- [x] Run the 17/33/65/129 grid tests on controlled admissible intervals and
  verify convergence/branch location under explicit tolerances.
- [ ] Re-run the existing interval, PS/GS/VA gradient, full-support, and
  pipeline identity tests. Do not change the full-Z solver or security scope
  unless a focused test demonstrates a real defect.
- [x] Confirm no pointwise clipping, empty-interval repair, policy
  `epsilon_total`, changed PS/GS/VA gradients, or weakened physical support.

## Task 7: Documentation, evidence, and handoff

**Files:**
- Modify the minimum current docs: `PAPER_CODE_ALIGNMENT.md`, `PAPER_TO_CODE.md`,
  `EQUATIONS.md`, `ASSUMPTIONS.md`, `PHYSICAL_PARAMETER_AUDIT.md`,
  `CHANNEL_STATE_DISTRIBUTION.md`, `KNOWN_ISSUES.md`, `EVIDENCE.md`,
  `DECISION_LOG.md`, `PROJECT_STATE.md`, `NEXT_ACTIONS.md`,
  `SESSION_HANDOFF.md`, and `README.md` only where traceability requires it

- [x] Record the pre/post active dataflow and classify beam wander, homogeneous
  scalar `C_n^2`, legacy diagnostics, unsupported mappings, and new composite
  paths as ACTIVE/LEGACY/TEST_ONLY/PLACEHOLDER/UNIMPLEMENTED.
- [x] State aperture averaging and turbulence-AoA mapping blockers separately;
  do not upgrade them to aligned or verified.
- [x] Add exact focused verification results using repository evidence status
  vocabulary and preserve `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
- [x] Overwrite the handoff with the current SHA, dirty-worktree caution,
  changed files, test commands/results, blockers, and exactly one recommended
  next task. Do not execute that next task.

## Verification checklist

- [x] Scoped `python -m unittest` for targeted new/updated tests and existing
  phase, channel, state, diagnostics, pipeline, gradient, Holevo interval,
  and baseline-guard tests.
- [x] `py_compile` for every changed Python file.
- [x] `git diff --check` and complete diff review.
- [x] Recompute/compare the frozen final-spec hash; confirm
  `docs/FINAL_MODEL_SPEC.md` is unchanged.
- [x] Confirm no training, final-test, held-out, publication-scale, or
  certification workflow was run.

## Plan self-review

- The plan keeps unresolved physical mappings explicit and fail closed.
- It removes only active beam-wander use; the legacy equation remains available
  for historical diagnostics and is labeled accordingly.
- It preserves the existing security causal chain, common ensemble, full-Z
  interval, and lifecycle restrictions.
- It adds no arbitrary clipping, floors, turbulence factors, or publication
  claims, and it keeps the implementation limited to source-supported pieces.
