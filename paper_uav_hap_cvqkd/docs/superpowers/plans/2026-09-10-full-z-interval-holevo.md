# Full Physically Admissible Z-Interval Holevo Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the production lower-endpoint-only Holevo evaluation with a deterministic worst-case maximization over the complete analytically and physically admissible Z interval, without changing the phase-noise causal chain or lifecycle gate.

**Architecture:** Keep `c4_gram_source_moments()` as the one source-moment evaluation. Compute `Z_minus`, `Z_plus`, `Z_phys`, and the physical intersection in `_holevo_from_source_moments()`. Evaluate the existing standard-form covariance and entropy formula for a batched scalar-Z candidate set. Use a fixed interval grid followed by bounded golden-section refinement in every grid cell; include both interval boundaries and select with a tensor maximum. Return the selected covariance while preserving autograd through the selected candidate. Fail closed with structured diagnostics when the interval is empty or a candidate violates covariance physicality.

**Tech Stack:** Python 3.12, PyTorch float64/complex128, existing covariance and C4 Gram backends, `unittest`.

## Task 1: Add failing interval and optimizer tests

**Files:**
- Create or modify: `tests/test_holevo_interval.py`
- Modify only if needed: `tests/test_holevo.py`, `tests/test_pipeline_consistency.py`, `tests/test_gradients.py`

- [x] Add controlled scalar-objective tests for strict interior, lower-boundary, and upper-boundary maxima using the shared bounded-maximizer helper.
- [x] Add production-path tests for the physicality-truncated interval and the exact covariance cross-block (`Z`, with no extra `sqrt(T)`).
- [x] Add an empty-interval test asserting the structured security-domain failure and its `security_domain_valid=False` diagnostics.
- [x] Retain and rerun the existing same-`epsilon_total` MI/Holevo identity test through `evaluate_transmitter`.
- [x] Add phase/V_A, PS, and GS gradient tests through the conservative Holevo result on smooth fixtures.

Run the focused new tests before production implementation and require the expected import/behavior failures.

## Task 2: Implement the bounded scalar maximizer and security interval

**Files:**
- Modify: `src/cvqkd/holevo.py`
- Modify: `src/cvqkd/__init__.py` only if the structured exception is exported

- [x] Add explicit deterministic optimizer constants/arguments: fixed candidate grid size and fixed golden-section refinement count; validate both as positive integers.
- [x] Add a small `_maximize_bounded_scalar()` helper that accepts batched lower/upper tensors and a batched evaluator, samples the full grid, refines every grid cell, includes both boundaries, and returns the selected value and point with tensor `max` semantics.
- [x] Add an explicit `SecurityDomainError` carrying a diagnostics mapping for empty intervals and candidate-domain failures.
- [x] Compute the frozen `Z_minus`, `Z_plus`, `Z_phys`, `Z_L`, and `Z_U` equations from the already-derived effective epsilon and ensemble `V_A`; do not alter `T`, epsilon, or source moments.
- [x] Evaluate every candidate through `standard_form_covariance()` and the existing symplectic/entropy formula. Reject material `lambda_j < 1` and nonfinite values; record any existing within-tolerance numerical repair explicitly rather than silently clipping.
- [x] Re-evaluate the selected `Z_star` once to return its covariance and selected diagnostics. Set `HolevoResult.z` to `Z_star`, preserve existing source-moment fields, and add interval/argmax/security-valid diagnostics.
- [x] Keep the covariance cross block exactly `Z_star * sigma_z`; do not introduce a transmission factor.

Run the new interval tests and the changed Holevo tests after implementation.

## Task 3: Verify integration and gradient ownership

**Files:**
- Modify: `docs/EQUATIONS.md`, `README.md`, and the minimum relevant current-state/evidence documents only after tests produce evidence.

- [x] Verify `evaluate_transmitter()` still constructs the ensemble from `(T, epsilon_base)`, derives one `epsilon_total` after the action, and passes that same object/tensor to MI and Holevo.
- [x] Verify gradients reach adaptive V_A through `epsilon_total`, and PS/GS through the shared ensemble/source moments and selected worst-case branch.
- [x] Run only focused Holevo/Gram/pipeline/gradient tests, targeted `py_compile`, and `git diff --check`; do not run training, certification, final-test, or publication-scale Monte Carlo.
- [x] Record exact verification evidence, update the current security mismatch/state records, and retain `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Task 4: Ponytail final patch review

- [x] Inspect the complete diff for unrelated refactors, phase-chain changes, policy-input changes, numerical constants, and lifecycle broadening.
- [x] Remove any edit not required for full-interval security, focused tests, or traceable current-state documentation.
- [x] Confirm production `Cn_phi2` remains `null` and no certification/provenance claim is upgraded by this implementation.
