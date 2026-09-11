# Corrected AP Custom Backward Validation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the isolated AP custom reverse VJP against the corrected AP
directional finite-difference oracle for cheap C4 fixtures and four bounded
full-support Case A directions, without opening adaptive training.

**Architecture:** Keep `src/cvqkd/ap_custom_backward.py` isolated. Add one
validation runner that calls the corrected `scripts/full_support_c4_worker.py`
for independent forward values and `source_moments_vjp` for reverse values.
Build PS, GS-real, GS-imag, and V_A directions through the existing C4 and
physical-amplitude mappings, and record support, precision, h-sweep, complex
convention, combined-objective, and runtime provenance in a new ignored JSON
artifact.

**Tech Stack:** Existing Python, PyTorch, mpmath, unittest, JSON, SHA-256. No
new dependency, channel change, security-equation change, training, or
optimizer step.

---

### Task 1: Freeze the corrected algebra and validation inputs

**Files:**
- Read: `src/cvqkd/ap_custom_backward.py`, `scripts/full_support_c4_worker.py`, `src/cvqkd/gram_moments.py`, `src/modulation/joint_ps_gs.py`, `src/modulation/geometric_shaping.py`, `src/modulation/normalization.py`
- Create: `docs/superpowers/plans/2026-09-11-corrected-ap-custom-backward-validation.md`

- [x] Confirm the corrected worker contains `aa = x2.T` and no `aa = sr * x2.T`.
- [x] Confirm the custom forward uses `A_s = sectors[s] @ diag(z) @ inverse[s-1]` and its reverse path differentiates that same expression.
- [x] Bind the run to corrected `C,w`, the exact ensemble hash, the corrected worker hash, the current custom-backward hash, and the current model hash.
- [x] Preserve the normal checkout and all pre-existing uncommitted B-D evidence changes.

### Task 2: Build the isolated validation runner

**Files:**
- Create: `scripts/validate_corrected_ap_custom_backward.py`
- Create (ignored artifact): `results/ap_custom_backward_corrected_directional_validation_20260911.json`

- [x] Add an independent corrected AP forward adapter using `full_support_c4_worker._row`, with explicit decimal precision and no production fallback path.
- [x] Add four cheap four-state fixtures: uniform, mildly nonuniform positive PMF, perturbed real geometry, and perturbed imaginary geometry; use an independent generic AP adapter because the repository worker is fixed at 64 prototypes.
- [x] Add target Case A direction constructors using existing softmax, `GlobalGeometricShaping`, `physical_amplitudes`, and C4 orbit extraction; do not manually renormalize probabilities or amplitudes.
- [x] Add the bounded h sweep `1e-3`, `3e-4`, `1e-4`, `3e-5`, and `1e-5` on cheap fixtures; use the declared 800-digit full-support precision for the bounded target endpoint and fail closed on unresolved support.
- [x] Compare AP central differences against custom VJP for C and w on cheap fixtures, record absolute/relative errors, support/rank, precision, and h stability.
- [x] Record the combined `J=1.7*C-0.8*w` comparison and separate real/imaginary complex-gradient convention checks.
- [x] Keep one-state full-Z backward conditional on all four source-moment direction families passing; never call `optimizer.step()` or train.

### Task 3: Run cheap fixtures and focused regression checks

**Files:**
- Modify if needed: `src/cvqkd/ap_custom_backward.py`
- Test if needed: `tests/test_ap_custom_backward_corrected.py`

- [x] Run the cheap fixture forward/VJP checks first.
- [x] If a fixture fails, trace the mismatch to the first divergent forward or reverse algebra component before changing code.
- [x] Run the existing fast source-moment, spectral-VJP, normalization, and protocol tests; keep target AP jobs outside ordinary CI.

### Task 4: Run bounded corrected Case A directional validation

**Files:**
- Modify: `scripts/validate_corrected_ap_custom_backward.py`
- Create/update ignored artifact: `results/ap_custom_backward_corrected_directional_validation_20260911.json`

- [ ] Validate PS-logit, GS-real, GS-imag, and V_A directions with explicit positive probabilities, 256 unique states, and 256/256 resolved support at the selected precision.
- [x] Stop before full-Z backward if any source-moment direction fails materially or if the AP backend cannot complete the declared full-support reference within the bounded runtime budget.
- [ ] If all four source-moment families pass, run one corrected Case A full-Z state backward once and record K, Z*, branch location, gradients, finiteness, and nonzero status; do not call an optimizer.
- [x] Measure AP forward, custom VJP, combined runtime, and serial batch-1/8/32 estimates; classify practicality separately from correctness.

### Task 5: Verify and update traceable evidence

**Files:**
- Modify: `docs/EVIDENCE.md`, `docs/DECISION_LOG.md`, `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, `.agent/SESSION_HANDOFF.md`

- [x] Run `py_compile`, focused fast tests, artifact/hash integrity, and `git diff --check`.
- [x] Mark the old custom-backward target artifact as `SUPERSEDED_WRONG_AP_W_REFERENCE`; never use old w as an oracle.
- [x] Set exactly one final classification from the requested four values, keep `NOT_READY_FOR_ADAPTIVE_TRAINING` unless all required validation passes and runtime is acceptable, and record one remaining blocker.
- [x] Perform final Ponytail review and complete the evidence update in artifact -> evidence -> decision -> project state -> next action -> session handoff order.
