# Pointwise Guard V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen V2 rule `support_is_rigorously_certified AND certified_margin > 0` with the sign decision made inside the existing Arb certifier, then freeze a no-override V2 smoke runner without executing it.

**Architecture:** Reuse the existing realized-point certifier, subprocess adapter, pointwise guard, transactional trainer, and smoke runner. The Arb process emits an explicit strict-separation certificate and exact textual margin; the production guard consumes that certificate in V2 mode and never re-decides its sign from binary64 diagnostics.

**Tech Stack:** Python 3.13/PyTorch production runtime; pinned CPython 3.12.10, python-flint 0.9.0/FLINT 3.6.0 certification runtime; `unittest`; JSON/YAML provenance manifests.

**Spec:** `docs/POINTWISE_GUARD_PROTOCOL_V2.md`

## Global Constraints

- Keep exact `tau = 3961408125713217/2^95 = 0x1.c25c268497682p-44` and `1e-13 = PROPOSED_UNAPPROVED`.
- Preserve V1 artifacts and do not run either smoke.
- Preserve states `bad/medium/good`, seeds `202613/202615`, six steps, two repetitions, precision `[160,256,384,512]`, Adam settings, MI, Holevo, SKR, security scope, and frozen model.
- Modify no `src/cvqkd`, modulation, trainer, default scientific config, or frozen specification file.

---

### Task 1: Arb Strict-Separation Result

**Files:**
- Modify: `tests/test_rigorous_flint_support.py`
- Modify: `src/validation/realized_point_certifier.py`
- Modify: `scripts/pointwise_certifier_worker.py`
- Create: `schemas/pointwise_certifier_result_v2.schema.json`

**Interfaces:**
- Consumes: exact dyadic `tau`, validated Arb eigenvalue balls, and validated inertia brackets.
- Produces: `support_is_rigorously_certified`, `strict_separation_certified`, `certified_margin_lower_bound`, and diagnostic binary64 fields.

- [x] Add a synthetic Arb test where midpoint order differs from the maximum-below upper endpoint, plus strict-positive/equality certificate tests.
- [x] Run the new tests and confirm they fail because the V2 certificate helpers do not exist.
- [x] Implement global inward endpoints and strict margin comparison in Arb; make decimal inertia candidates compare to `tau` in Arb.
- [x] Pass the protocol version through the existing worker and emit the V2 result schema fields.
- [x] Run the isolated real-backend support/inertia tests.

### Task 2: V2 Guard Consumption

**Files:**
- Modify: `tests/test_pointwise_guard.py`
- Modify: `src/optimization/pointwise_guard.py`
- Modify: `src/optimization/real_point_certifier_adapter.py`

**Interfaces:**
- Consumes: the certifier's Arb-decided strict-separation fields.
- Produces: `POINTWISE_ADMISSIBLE` for V2 only when both rigorous support and strict separation are certified; V1 behavior remains available for historical tests.

- [x] Add V2 tests proving a positive exact certificate is accepted even when the old `2 * uncertainty` rule would reject, and missing/false certificates fail closed.
- [x] Run the tests and confirm the V2 config/result contract fails before implementation.
- [x] Add the minimal protocol-version switch; keep all V1 guard logic unchanged.
- [x] Run pointwise guard tests, including a real V2 adapter fixture.

### Task 3: Freeze V2 Runner and Manifest

**Files:**
- Modify: `tests/test_pointwise_smoke_runner_freeze.py`
- Modify: `scripts/run_pointwise_guard_smoke.py`
- Create: `configs/pointwise_guard_execution_manifest_v2.json`
- Create: `schemas/pointwise_guard_execution_manifest_v2.schema.json`
- Create: `schemas/pointwise_guard_smoke_v3.schema.json`

**Interfaces:**
- Consumes: frozen V2 config and tested implementation hashes.
- Produces: a no-override runner bound to V2 and an execution manifest authorizing only the later frozen V2 smoke.

- [x] Add runner-freeze tests for V2 bindings, unchanged smoke parameters, output isolation from V1 artifacts, and no scientific CLI overrides.
- [x] Confirm the tests fail against the V1-bound runner.
- [x] Switch only runner constants/config keys/result path to V2 and add V2 result schema.
- [x] After all implementation tests pass, compute and write every manifest hash binding.
- [x] Run manifest hash verification without invoking the runner.

### Task 4: Evidence and Lifecycle Handoff

**Files:**
- Create: `results/pointwise_guard_implementation_v2.json`
- Modify: `docs/EVIDENCE.md`
- Modify: `docs/DECISION_LOG.md`
- Modify: `docs/PROJECT_STATE.md`
- Modify: `docs/NEXT_ACTIONS.md`
- Modify: `.agent/SESSION_HANDOFF.md`
- Modify: `.gitignore`
- Modify: `../.gitattributes`

**Interfaces:**
- Consumes: fresh test outputs and final hashes.
- Produces: `FROZEN_POINTWISE_GUARD_V2_SMOKE_EXECUTION_AUTHORIZED` as the sole next action.

- [x] Record the machine-readable implementation result before prose evidence.
- [x] Update evidence, decision, state, next action, and handoff in authority order.
- [x] Run all scoped production and real-backend tests, JSON/YAML parsing, hash verification, frozen-model verification, and `git diff --check`.
- [x] Inspect the complete diff and confirm V1 artifacts/scientific files are unchanged and no smoke was run.
