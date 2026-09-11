# Exact C4 Tangent and Stability Investigation Plan

> **For agentic workers:** Execute this plan task-by-task. Keep lifecycle
> gates closed and use checkbox syntax to record progress.

**Goal:** Determine whether the full-support 256-state C4 source moments
\(C(p,z)\) and \(w(p,z)\) admit a numerically stable exact tangent/reverse
boundary without changing the security model.

**Architecture:** Keep the current production complex128 gate and the isolated
AP custom backward untouched. First implement an independent arbitrary-
precision forward tangent using constrained solve equations for \(B_s\) and
\(A_s\). Compare it with corrected AP central differences and only then audit
or replace the reverse VJP. If the mathematics passes, benchmark a compiled
multiprecision backend with precision escalation.

**Research artifact:** docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md

**Deep research refinement:** docs/DEEP_RESEARCH_SOURCE_MOMENT_REVERSE_GRADIENT.md

**Global constraints:**

- Preserve \(M=256\), fourfold C4 symmetry, positive full support, corrected
  C and corrected w.
- Preserve the current physical full-Z interval, Holevo maximization, and raw
  signed SKR semantics.
- Do not clip eigenvalues, add jitter, add epsilon identity, truncate
  support, or use a thresholded pseudoinverse.
- Do not run production optimizer steps, production training,
  publication-scale evaluation, baseline selection, or final-test evaluation.
  The separately isolated analysis runner may use bounded surrogate optimizer
  steps only when every artifact is marked `TRAINING_SURROGATE_ONLY` or
  `ANALYSIS_ESTIMATE`.
- Do not use the superseded wrong-w artifact as an oracle.
- Keep slow AP work out of ordinary CI.

---

### Task 1: Freeze evidence and equations

**Files:**
- Read: docs/EVIDENCE.md, docs/DECISION_LOG.md, docs/NEXT_ACTIONS.md,
  docs/PROJECT_STATE.md
- Read: src/cvqkd/gram_moments.py, src/cvqkd/ap_custom_backward.py,
  scripts/full_support_c4_worker.py
- Create: docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md

- [x] Bind the report to the corrected C/w, exact ensemble hash, worker hash,
  custom-backward hash, and current lifecycle state.
- [x] Record the bounded PS failure and measured reverse runtime.
- [x] Confirm the corrected worker uses aa = x2.T and the current target uses
  \(A_s=G_sDG_{s-1}^{-1}\).
- [x] Preserve the existing fail-closed classification.

### Task 2: Derive the forward tangent oracle

**Files:**
- Create later: an isolated tangent module or test-only runner
- Reference: docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md

- [x] Derive \(dH_d,dG_s,dS_s,dR_s,dJ_s,dA_s,dB_s,dQ_s,dT_s\).
- [x] Derive \(du,dE,dC,dw\) under real physical parameter paths.
- [x] Verify the Sylvester tangent and complex-alpha convention.
- [x] Specify the three-way finite-difference/tangent/reverse interpretation.

### Task 3: Audit reverse adjoints and representation choices

- [x] Derive product, inverse, Hermitian-projection, ordinary-transpose,
  Hermitian-transpose, and Sylvester adjoints.
- [x] Derive raw C4 sector and real/imaginary amplitude gradients.
- [x] Identify the target-scale Frechet and inverse-spectrum magnitudes.
- [x] Rank numerical conditioning versus algebraic-bug hypotheses.
- [x] Derive exact right-side solve constraints for B and A.

### Task 4: Literature and backend survey

- [x] Audit the analytical DM-CV-QKD source-moment literature.
- [x] Audit large-QAM and free-space numerical implementations.
- [x] Audit matrix-function, Frechet, Arb/FLINT, and MPFR/MPLAPACK
  references.
- [x] Record what the literature does not establish about a \(10^{-618}\)
  full-support differentiable implementation.

### Task 5: Record one primary recommendation

- [x] Rank current AP, corrected tangent/reverse, C4 reformulation,
  nonorthogonal basis, implicit differentiation, compiled MP,
  AP-calibrated approximation, rigorous truncation, and gradient-free paths.
- [x] Keep exact C/w and security semantics as the primary path.
- [x] Set falsification criteria, precision-ladder checks, and a proposed
  runtime gate.
- [x] Record exactly one remaining blocker and one next task.
- [x] Do not execute the recommended implementation in this research task.
- [x] Expand the literature/backend decision boundary and specify
  conservative \(C,w\)-to-\(Z\)-to-SKR value-error propagation.
- [x] Select C++17 MPFR/MPC as the primary point prototype and Arb/acb_mat as
  the independent reference/enclosure mode.

### Task 6: Bounded forward-tangent implementation

**Files:**
- Create: isolated arbitrary-precision C4 tangent runner/module
- Test: small fixtures first; target directions only after cheap checks

- [x] Implement \(B_sS_{s-1}=S_sD\) and
  \(A_sG_{s-1}=G_sD\) as solve constraints.
- [x] Implement differentiated solve constraints and Sylvester tangents.
- [x] Compare direct and constrained products on well-conditioned fixtures.
- [x] Run the corrected PS tangent diagnostic at the bounded 200/400/600/800
  precision ladder; 800 digits resolved full support and matched the prior
  corrected AP finite-difference reference within \(10^{-8}\).
- [x] Extend to GS-real, GS-imaginary, and \(V_A\) only after the cheap
  directional preflight passed; validate target endpoints and constrained
  tangents in that order at 800 AP digits.
- [ ] Audit local primitive adjoint identities before complete reverse VJP.
- [ ] Move to compiled multiprecision only after the Python/AP tangent is
  algebraically supported.
- [ ] Run full-Z backward once only if all four source directions pass and
  the proposed runtime gate is met.
- [x] Update evidence in Artifact -> Evidence -> Decision -> Project State ->
  Next Action -> Session Handoff order.
- [x] Record the four-direction target artifact, support/normalization checks,
  residuals, magnitude logs, runtimes, and the practical reverse/adjoint
  blocker.

**Stop conditions:**

1. Any perturbed point loses positivity, uniqueness, or 256/256 support.
2. Tangent and corrected AP finite difference disagree after precision
   escalation and a valid h plateau.
3. Local adjoint identities fail.
4. AP/ball precision cannot certify the derivative.
5. A mathematically passing implementation remains impractical for the
   planned adaptive workload.

No approximation is substituted at a stop condition.

### Task 7: Bounded analysis-surrogate figures

**Files:**
- Create: isolated `src/cvqkd/training_surrogate.py` and
  `scripts/run_analysis_figures.py`
- Create: analysis artifacts under `results/` and SVG figures under
  `figures/analysis/`
- Record: `docs/ANALYSIS_FIGURES_REPORT_20260911.md`

- [x] Calibrate a bounded smooth surrogate against the four validated tangent
  directions without rerunning the 800-digit tangent.
- [x] Validate four nearby full-support ensembles against corrected AP C/w.
- [x] Build a deterministic 16-active-state grid with explicit outage mass and
  phase-disabled labeling.
- [x] Run the six-method 20-step smoke and 50-step analysis optimization.
- [x] Evaluate MB and seven Full exact AP/full-Z security anchors.
- [x] Produce Figures 1--6 and an exact-vs-surrogate comparison artifact.
- [x] Stop the publication path because Full has no meaningful exact-bin gain
  over the simple MB baseline.

The analysis result is `ANALYSIS_FIGURES_READY` and
`MIXED_PRELIMINARY_SUPPORT`, not publication certification. The next
recommended investigation is the Full-vs-MB surrogate/objective mismatch;
do not execute a publication-scale run from this plan.

### Task 8: Full-Z objective and aggregation audit

**Files:**
- Create: isolated `scripts/audit_analysis_objective.py`
- Create: `results/analysis_objective_audit_20260911.json`
- Record: `docs/DEEP_RESEARCH_FADING_FULL_Z_BLOCKER_20260911.md`

- [x] Audit active/outage weights and conditional normalization.
- [x] Compare the smooth search proxy with exact full-Z baseline rows.
- [x] Check whether proxy `Z` lies in the frozen source-moment interval.
- [x] Re-evaluate saved candidates with full-Z using explicitly labelled
  surrogate `C,w` values.
- [x] Rank H1--H6, define GO/NO-GO gates, and choose one next bounded task.

The audit found `Z_proxy < Z_L` in all 16 active states and invalidated the
proxy as a target-security optimization objective. The weight arithmetic
passed. The current positive joint-adaptation novelty is
`CURRENT_NOVELTY_NOT_SUPPORTED`; the next and only immediate numerical task
is an interval-preserving objective repair and bounded ranking recheck. Keep
reverse repair, full-Z backward, adaptive training, final-test access, and
publication-scale evaluation closed.

### Task 9: Bounded interval-preserving full-Z objective repair

**Files:**
- Create: isolated `scripts/run_repaired_full_z_objective.py`
- Update: `src/cvqkd/holevo.py` with a fail-closed diagnostic interval assertion
- Create: `tests/test_repaired_full_z_objective.py`
- Create: `docs/REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md`
- Create: repaired objective and exact-check artifacts under `results/`

- [x] Reproduce the old off-interval proxy before changing the objective;
  `96/96` mode-state rows have `Z_proxy < Z_L`.
- [x] Reuse the existing physical interval and full-Z maximizer with only
  surrogate `C,w` approximated during search.
- [x] Assert every bounded scalar candidate is finite and inside
  `[Z_L,Z_U]`; record zero repaired interval violations.
- [x] Reproduce corrected Case A and pass existing exact anchor-equivalence
  and rank-consistency gates.
- [x] Pass finite PS/GS/V_A gradient smoke and the 20-step optimization smoke.
- [x] Run only the bounded 50-step PS+V_A and Full analysis checks with the
  same initial PS/V_A branches, grid, weights, noise, energy budget, and beta.
- [x] Run the bounded poor/median/good exact AP/full-Z check. Full converged;
  PS+V_A failed closed at the full-support AP gate and is not assigned an
  exact K.
- [x] Preserve `FULL_Z_SEARCH_OBJECTIVE_REPAIRED`,
  `CURRENT_NOVELTY_NOT_SUPPORTED`, and
  `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
- [x] Update evidence in Artifact -> Evidence -> Decision -> Project State ->
  Next Action -> Session Handoff order.

The repair is analysis-only. It does not authorize publication-scale training,
final-test access, adaptive training, reverse VJP work, full-Z backward,
baseline selection, or a new security claim. The one remaining blocker is the
missing converged exact PS+V_A source-moment/ranking result.
