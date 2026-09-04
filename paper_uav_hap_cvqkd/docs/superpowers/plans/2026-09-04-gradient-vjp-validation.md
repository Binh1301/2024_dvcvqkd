# Gradient/VJP Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and freeze, but do not execute, the independent fast-path analytic-VJP validation runner.

**Architecture:** Reuse the full-support source diagnostics and existing CRN finite-difference conventions. The runner rejects any arbitrary-precision fallback route and compares a future analytic VJP against the frozen directional probes.

**Tech Stack:** PyTorch float64/complex128, existing C4 evaluator, JSON/YAML manifests, `unittest`.

**Spec:** `docs/GRADIENT_VJP_VALIDATION_PROTOCOL.md`

## Global Constraints

- No fallback differentiation, training, final-test access, threshold approval, clipping, flooring, or `epsilon I`.
- Preserve the frozen model, MI, Holevo, SKR, security functional, all 12 evaluation fixtures, and existing derivative tolerances.

### Task 1: Analytic fast-path VJP interface

**Files:** Modify `src/cvqkd/gram_moments.py`; test `tests/test_full_support_c4_gram_backend.py`.

- [ ] Write failing tests for finite analytic VJP output on an eligible fast path and `FullSupportGradientUnavailable` on fallback.
- [ ] Implement only the Hermitian matrix-function Frechet/VJP interface defined by the protocol.
- [ ] Run the focused source-moment tests; do not invoke the 12-fixture runner.

### Task 2: Frozen directional validation runner

**Files:** Create `scripts/run_gradient_vjp_validation.py`, result schema, execution manifest, and focused runner tests.

- [ ] Write failing tests for exact CRN reuse, all frozen coordinates, route rejection, and fail-closed provenance.
- [ ] Implement the no-override runner using the protocol's six central-difference steps and derivative rule.
- [ ] Run scoped tests and manifest-hash verification only.

### Task 3: Freeze execution lifecycle

**Files:** Create implementation artifact; update current certification manifest, evidence, decision log, project state, next actions, and handoff as required.

- [ ] Record machine-readable implementation evidence before lifecycle prose.
- [ ] Bind every source/config/schema/fixture hash in a new execution manifest.
- [ ] Authorize exactly one later gradient/VJP validation execution; do not run it.
