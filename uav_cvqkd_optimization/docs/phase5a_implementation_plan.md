# Phase 5A Time-Dependent Rate Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution; one independent review after implementation.

**Goal:** Support exogenous R(q,t) in the existing four graph algorithms without changing physical models or publication gates.

**Architecture:** Keep static vectors valid, accept finite slot-by-waypoint matrices in Scenario, and route every algorithm through one rate_at(slot,j) method. Explicit provider adapters snapshot rate(q,t,scenario) once at destination q_k, t_k=k*dt. Cloud link-slot sampling derives both rates and binary retention from one approved policy.

**Tech Stack:** Existing Python, NumPy, pytest; no new dependencies.

**Spec:** User's Phase5A attachment; Phase4 reports and actual solver modules.

## Constraints and scope

- No paper-mode, lookup regeneration, Z/w/MB/Holevo edits, rotor/config/default changes, historical result or figure edits, commits or pushes.
- S_K=m0*sum(z_k*r_k), n_K=m0*sum(z_k); one terminal-block penalty; variable K and graph/energy feasibility unchanged.
- Frozen rate snapshots are deterministic exogenous inputs; no trajectory/history-dependent callback rewards or arbitrary fractional signal counts.
- Exact graph DP claim is limited to this fixed model, finite graph/horizon and float64 arithmetic. No continuous/global/security certificate.
- Direct vector/matrix Scenario construction is a numerical interface, not a source-admissibility decision. Selected reference lookup loading must reject incompatible or unestablished context.
- Existing CLI/YAML runner remains static; dynamic inputs are explicit programmatic adapters and run_methods. No new physical backend or mission values are selected.

## Approaches

Extend the shared Scenario rather than copy solvers. A lazy position-only cache is invalid for moving clouds; recomputing backend calls inside each algorithm risks inconsistent realizations and waste. Sampling (slot,waypoint) once retains reproducibility and shares inputs, with O(HJ) storage and full-horizon preparation disclosed separately from greedy decision access.

## Review focus

Invalid matrix shapes/nonfinite values; off-by-one endpoint times; analog double erasure or fractional counts; metadata subset mistaken for compatibility; dominance incorrectly merging different n_K. Tests below own each case.

## Tasks

- [x] Persist pre-edit hashes and run baseline suite.
- [x] Write failing tests for static/matrix equivalence, dynamic timing and independent exhaustive P1/P2 enumeration, signal/energy/velocity/stationary constraints, cloud repeatability, invalid inputs and lookup rejection.
- [x] Extend evaluation.py, dp_solver.py and baselines.py to use rate_at; fix experiments.py waypoint counting; add rate_provider.py sampling and cloud adapter.
- [x] Add strict selected-reference lookup guard in skr_lookup.py and optional explicit context binding in config.py; preserve no-context legacy loading without claiming compatibility.
- [x] Run focused/full tests, independent review, fix confirmed findings with regression tests.
- [x] Write author decisions and readiness report; compare four metadata differences and quantity dependencies; record tests/hashes and unchanged catalog.
- [x] Verify every protected artifact except explicitly listed code changes; inspect diffs and whitespace. Do not commit/push.

## Execution record

- Baseline:90 passed in5.89s. Initial feature tests:14 failed/4 passed for missing dynamic interfaces.
- Dynamic implementation passed its18 initial cases. Whole suite exposed100 passed/8 setup errors from historical producer hashes in figure test fixtures. Preserved strict verifier and switched only that test fixture to fresh measured synthetic tmp data; no historical writes.
- Full suite after four extra boundary/replay tests:112 passed. Independent review found no must-fix defect;27 focused/planning tests and100 extra exhaustive comparisons passed.
- Final suite:112 passed in6.29s, exit0. Machine-readable evidence and preservation scope: `docs/phase5a_validation/verification.json`.
- Implementation choices: inline execution, existing workspace, no commits/worktree churn per user's explicit request; no new dependencies or paper runner. Selected-reference lookup gate is intentionally reject-only until full binding evidence exists; legacy loading does not assert compatibility.
