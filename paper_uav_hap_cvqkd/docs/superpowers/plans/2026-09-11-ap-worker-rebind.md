# AP Worker Definition Rebind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the AP fallback worker reproduce the current frozen C4 source-moment definition of w, then rebind only the bounded Case A exploratory evidence.

**Architecture:** Keep production C4, Holevo, full-Z, PS, GS, V_A, and trainer code unchanged. Replace only the AP worker's extra left sr factor after deriving that x2.T is already the production A_s=G_s D G_(s-1)^(-1). Use explicit slow fixture checks outside normal CI, then run corrected Case A at 800 and 900 digits.

**Tech Stack:** Existing Python, mpmath, PyTorch, unittest. No new dependency.

**Spec:** Current production equations in src/cvqkd/gram_moments.py, worker in scripts/full_support_c4_worker.py, and the pasted AP-worker rebind request.

## Global Constraints

- Preserve M=256, full positive support, C4 sector construction, and exact C/w equations.
- Modify only scripts/full_support_c4_worker.py for numerical behavior.
- Do not train, call optimizer.step(), run B-D, change full-Z semantics, or access final-test data.
- Do not clip, jitter, weaken gates, truncate support, or use pseudoinverses.
- Keep old worker-backed artifacts as historical records; mark them SUPERSEDED_WRONG_AP_W, never silently overwrite them.
- Keep custom backward isolated with status PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION.

## Algebra frozen before patch

For sector s, previous sector is s-1 modulo 4. Let

    m  = U_s^H D U_(s-1)
    sr = diag(sqrt(lambda_s))
    sp = diag(sqrt(lambda_(s-1)))

The worker computes

    x  = sp^(-1) m.T
    b  = sr x.T = sr m sp^(-1)

Thus b is the eigenbasis representation of a_tau=S_s D R_(s-1).

The second solve computes

    x2 = sp^(-1) (sr b).T
    x2.T = sr b sp^(-1)
          = sr^2 m sp^(-2)
          = U_s^H [G_s D G_(s-1)^(-1)] U_(s-1).

Therefore x2.T is already the production A_s. The old

    aa = sr * x2.T

computes S_s A_s, not A_s, and changes every downstream t = aa @ q and w residual. The minimal correction is exactly:

    aa = x2.T

No other equation changes.

## Tasks

### Task 1: Add red regression tests before the patch

**Files:**
- Create: tests/test_ap_worker_equivalence.py

- [x] Add a source-level test that requires aa = x2.T and rejects aa = sr * x2.T; run it and observe the expected failure.
- [x] Add an environment-gated slow test for three 64-orbit fixtures: uniform, mildly nonuniform positive PMF, and perturbed real geometry. Compare production _fast C/w with AP _row C/w.
- [x] Add fast lifecycle assertions requiring affected old artifacts to carry SUPERSEDED_WRONG_AP_W after Task 4. Do not run 800/900 digits in normal CI.

### Task 2: Patch the AP worker only

**Files:**
- Modify: scripts/full_support_c4_worker.py:142

- [x] Replace only aa = sr * x2.T with aa = x2.T.
- [x] Keep worker precision ladder, support checks, C computation, and JSON schema unchanged.
- [x] Run the source-level test and focused C4 checks.

### Task 3: Run explicit small-fixture equivalence

**Files:**
- Create: ignored diagnostic output only if needed.

- [x] Run the slow fixture test with RUN_SLOW_AP_WORKER_EQUIVALENCE=1.
- [x] Record production/AP C and w equivalence through the passing test for all three fixtures.
- [x] Confirm no production source or security equation changed.

### Task 4: Recompute corrected Case A AP source moments

**Files:**
- Create: results/ap_worker_corrected_case_A_20260911.json (ignored exploratory artifact).

- [x] Reconstruct the exact Case A ensemble and verify hash c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3.
- [x] Run corrected 800-digit AP forward and record 256/256 rank, lambda_min, C, w, runtime.
- [x] Run corrected 900-digit AP forward and record the same.
- [x] Record absolute and relative C/w differences.

### Task 5: Mark stale artifacts and recompute Case A full-Z

**Files:**
- Modify only affected result JSONs and relevant state docs.

- [x] Mark every identified artifact depending on the old AP w as SUPERSEDED_WRONG_AP_W; retain old values under explicit historical fields.
- [x] Record old w, corrected w, root cause, and affected downstream values.
- [x] Recompute only Case A with existing T, epsilon_total, V_A, beta, MI, and full-Z maximization.
- [x] Do not assume the old lower-boundary optimum; do not clamp K.
- [x] Do not recompute Cases B-D.

### Task 6: Final verification

- [ ] Run focused worker-equivalence tests, C4 tests, lifecycle/provenance tests, corrected Case A smoke, py_compile, and git diff --check.
- [ ] Update EVIDENCE -> DECISION_LOG -> PROJECT_STATE -> NEXT_ACTIONS -> .agent/SESSION_HANDOFF.md.
- [ ] Mark custom backward PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION.
- [ ] Use exactly one final status: CORRECTED_AP_FORWARD_VALIDATED only if all corrected Case A checks pass; otherwise AP_W_MISMATCH_UNRESOLVED.
