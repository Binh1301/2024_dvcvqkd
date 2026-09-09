# Project State

Last updated: 2026-09-10 (documentation/model/code alignment audit)

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
- The current code is not aligned with the target phase chain, scintillation/AoA
  fading, raw-T diagnostic, or full-interval Holevo maximization.

## Numerical and security gate

- Existing MI/Gram artifacts remain scoped to the prior code path.
- The C4 Gram production backend is cutoff-independent and the arbitrary-
  precision fallback is evaluation-only.
- Support/tolerance approval remains unresolved; no security/SKR figure may be
  presented as target-model evidence.
- Existing test artifact results/current_test_suite.json is a
  LAST_KNOWN_PASS for its recorded repository/model provenance, not a current
  pass for the edited target specification. No test was run by this audit.

## Friday preliminary diagnostic posture

| Class | Status | Scope |
|---|---|---|
| Regular 256-QAM, fixed PMFs, C4 orbit geometry | READY_NOW | Deterministic, data-free transmitter diagnostics |
| Current atmospheric/pointing T diagnostics | SAFE_AFTER_SMALL_FIX | Label as current sampler only |
| Target phase, scintillation, AoA, raw-T, p_gt_1 | BLOCKED | Required source/code path is absent |
| Target epsilon_total and full-interval chi_BE/SKR | BLOCKED | Phase chain and security solver are absent |
| Learned PS/GS/V_A outputs | BLOCKED | Training is closed and target security is not aligned |

## Preliminary figure readiness audit

| Figure | Status | Exact reason |
|---|---|---|
| Regular 256-QAM | READY NOW | Deterministic construction exists in qam256.py |
| Uniform / Binomial / MB PMF | READY NOW | Deterministic PMF constructors exist |
| Fourfold orbit visualization | READY NOW | Exact C4 index and expansion functions exist |
| Phase-noise curve xi_phase(V_A) | BLOCKED | c_phi and phase module/config are absent |
| epsilon_total(V_A) | BLOCKED | Post-action phase-noise chain is absent |
| H_sc Monte Carlo | BLOCKED | No scintillation sampler or frozen mapping |
| H_p Monte Carlo | SAFE AFTER SMALL FIX | Pointing sampler exists; a raw-data/plot wrapper is missing |
| AoA outage Monte Carlo | BLOCKED | No B_AoA factor or outage branch |
| T_raw histogram | BLOCKED | No raw product/admission path |
| Physical T histogram | SAFE AFTER SMALL FIX | Current sampler can produce T, but only as the present atmospheric/pointing path |
| p_gt_1 diagnostic | BLOCKED | No T_raw diagnostic |
| chi_BE(Z) interval diagnostic | BLOCKED | Only Z_minus is evaluated |
| Baseline K versus T | BLOCKED | Full-interval security and numerical gate are unresolved |
| Baseline K versus V_A | BLOCKED | Full-interval security and numerical gate are unresolved |
| Learned PS/GS/V_A output | BLOCKED | Training is closed and target security is not aligned |

## Exact next permitted action

Prepare a tiny deterministic diagnostic/plotting entry point for the
READY_NOW transmitter figures and, separately, resolve the single highest
scientific blocker before any target channel/security Monte Carlo:
the post-action phase chain plus full-interval security definition.

## Lifecycle restrictions

Do not modify scientific source or tests in this documentation task. Do not
run training, publication-scale Monte Carlo, long Gram/Holevo certification,
threshold approval, or final-test evaluation. Do not silently replace the
target equations with the current implementation.

## Current evidence

- EVID-0054: 2026-09-10 documentation/source/config/manuscript availability
  audit.
- DEC-0040: documentation-only alignment; unresolved model/code mismatches are
  retained as blockers.
- Existing historical numerical evidence remains in EVIDENCE.md and
  DECISION_LOG.md under its original provenance.
