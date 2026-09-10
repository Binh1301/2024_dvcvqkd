# Session Handoff

Date: 2026-09-10

Lifecycle: NOT_READY_FOR_PUBLICATION_SCALE_RUNS

## Verified

- The active channel path composes `eta_atm * H_sc * H_p * B_AoA`, uses
  generalized Rician pointing, and admits raw states without clipping or a
  positive floor. Active-domain rejection preserves the AoA outage atom.
- Profile-integrated Rytov support, normalized unit-mean lognormal sampling,
  explicit `v_sc` overrides, AoA gating, and raw/physical diagnostics are
  implemented. Unresolved production mappings fail closed.
- The legacy constant-`C_n^2` beam-wander helper remains available only for
  historical diagnostics and is not called by the active sampler; `sigma_z`
  and yaw remain excluded from their active variance terms.
- The policy receives `(log10(T), epsilon_base)` only for positive-T states;
  `epsilon_total = epsilon_base + c_phi V_A` is derived after the action and
  the same tensor reaches MI and Holevo. Outages retain `T=0` outside policy
  evaluation.
- Full-Z resolution fixtures cover 17/33/65/129 candidates, including
  interior, boundary, narrow, and near-boundary intervals. This is diagnostic
  evidence, not certification.
- The scoped composite/channel/provenance/phase/pipeline/full-Z/MI/SKR/
  baseline verification passed 90 tests in 2.744 seconds; targeted
  `py_compile`, `git diff --check`, and the frozen final-spec hash check pass.
  The broader legacy gradient/optimizer selection has seven
  `FULL_SUPPORT_FALLBACK_EVALUATION_ONLY` errors and remains evaluation-only;
  worker-backed pointwise/full-support tests were not completed.
- No training, publication-scale Monte Carlo, certification, held-out or
  final-test evaluation was run. Pre-existing dirty-worktree changes were
  preserved.

## Important files

- Composite channel: `src/channel/fso_channel.py`, `scintillation.py`,
  `aoa.py`, `turbulence.py`, and `state_distribution.py`.
- Causal phase and active entry-point resolution: `src/channel/phase_noise.py`,
  `src/optimization/trainer.py`, `scripts/_train.py`, and baseline/evaluation
  scripts.
- Current audit/evidence: `docs/PHYSICAL_PARAMETER_AUDIT.md`,
  `docs/PROJECT_STATE.md`, `docs/EVIDENCE.md`, and `docs/DECISION_LOG.md`.
- `docs/FINAL_MODEL_SPEC.md` was not modified; its SHA-256 is
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`.

## Open blockers

1. AUTHOR DECISION: freeze one common turbulence scenario and its profile,
   aperture, AoA, and effective-phase choices.
2. MISSING LITERATURE MAPPING: validate profile-to-`v_sc`, turbulence-to-AoA,
   and profile-to-effective-`C_n,phi^2` mappings.
3. NUMERICAL CERTIFICATION: rebind support/tolerance/convergence evidence to
   the composite post-action/full-Z target path.
4. LEGACY TEST DEBT: update or scope gradient/optimizer tests that invoke the
   evaluation-only full-support fallback.

## Exact next task

Freeze one author-approved, source-supported common-turbulence scenario
(profile, aperture mapping, AoA status/mapping, and effective `C_n,phi^2`
mapping/value), then rebind numerical provenance; do not execute it now.
