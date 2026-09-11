# Corrected B-D Exploratory Security Rebind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recompute only the bounded exploratory Cases B, C, and D with the accepted corrected AP source moments and existing statewise full-Z Holevo evaluator.

**Architecture:** Reconstruct the 20260910 physical channel cases with the existing seeded FSO sampler, use a deterministic evenly-spaced 16-active-state roster when the ignored historical artifact is unavailable, and pass the fixed corrected (C,w) directly through `_holevo_from_source_moments`. Outages remain outside MI/Holevo and receive exact zero raw key rate.

**Tech Stack:** Existing Python, NumPy, PyTorch, unittest, JSON, SHA-256. No AP worker, eigendecomposition, training, optimizer, or new dependency.

---

### Task 1: Freeze the bounded reconstruction inputs

**Files:**
- Create: `scripts/recompute_corrected_bd_security.py`
- Read-only inputs: `src/channel/fso_channel.py`, `src/cvqkd/mutual_information.py`, `src/cvqkd/holevo.py`, `src/cvqkd/secret_key_rate.py`, `src/modulation/joint_ps_gs.py`

- [x] Encode only the supplied development cases: `N_channel=1000`, channel seed `20260910`, `V_A=1`, `beta=0.95`, phase coefficient `0`, explicit `v_sc=0.25` for B--D, `sigma_hap_ang_rad=5e-6` for C--D, and the supplied D FOV value.
- [x] Use direct `sample_fso_channel` with explicit case motion settings that reproduce the recorded physical statistics; never clip `T_raw`.
- [x] Generate `epsilon_base` from a separate deterministic derived seed and record both channel and noise hashes.
- [x] Verify the uniform reference ensemble row hash is `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`; assert the same fixed ensemble tensors are used for B, C, and D.
- [x] Select 16 evenly spaced active rows per case, record indices and a SHA-256 roster hash, and record that the historical ignored B--D artifact was unavailable rather than inventing its indices.

### Task 2: Run the corrected statewise pipeline

**Files:**
- Modify: `scripts/recompute_corrected_bd_security.py`
- Create (ignored local artifact): `results/exploratory_cases_BD_full_security_corrected_20260911.json`

- [x] Compute MI only for active selected rows with the existing estimator and explicit AWGN seed.
- [x] Call `_holevo_from_source_moments` with the corrected constants `C=0.85985110654649868138037962728289179096834048571987` and `w=0.018327610474963502048823295065766568532781601388489`; do not call the AP worker or `c4_gram_source_moments`.
- [x] Preserve all full-Z interval diagnostics, raw signed `K=0.95*I_AB-chi_BE`, interval widths, boundary/interior counts, domain failures, and physicality minima.
- [x] Assign Case D outage rows exact `K=0` without policy, MI, or Holevo evaluation, then verify `mean_K_all = active_fraction * mean_K_active` to recorded floating-point discrepancy.
- [x] Store corrected-vs-supplied-old wrong-w comparisons, provenance hashes, solver settings, phase-disabled status, runtime, and the corrected A reference without rerunning A.

### Task 3: Focused verification and evidence update

**Files:**
- Modify: `docs/EVIDENCE.md`, `docs/DECISION_LOG.md`, `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, `.agent/SESSION_HANDOFF.md`

- [x] Run the corrected source/stale-artifact, ensemble, full-Z, outage/pipeline, and B--D smoke checks; record missing ignored-artifact tests as `BLOCKED_BY_ENVIRONMENT` if they cannot run.
- [x] Run targeted `py_compile` and `git diff --check`; verify the frozen model hash remains `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843` and no production source/security equation changed.
- [x] Update evidence in artifact → decision → project state → next action → session handoff order, retain `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, `PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION`, and `NOT_READY_FOR_ADAPTIVE_TRAINING`.
- [x] Inspect the complete diff with Ponytail review and report the exact required final status and remaining blocker; do not execute gradient validation.
