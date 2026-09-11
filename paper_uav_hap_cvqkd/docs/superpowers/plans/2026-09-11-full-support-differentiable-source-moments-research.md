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

**Global constraints:**

- Preserve \(M=256\), fourfold C4 symmetry, positive full support, corrected
  C and corrected w.
- Preserve the current physical full-Z interval, Holevo maximization, and raw
  signed SKR semantics.
- Do not clip eigenvalues, add jitter, add epsilon identity, truncate
  support, or use a thresholded pseudoinverse.
- Do not run optimizer.step(), training, publication-scale evaluation,
  baseline selection, or final-test evaluation.
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
- [ ] Extend to GS-real, GS-imaginary, and \(V_A\) only if PS passes.
- [ ] Audit local primitive adjoint identities before complete reverse VJP.
- [ ] Move to compiled multiprecision only after the Python/AP tangent is
  algebraically supported.
- [ ] Run full-Z backward once only if all four source directions pass and
  the proposed runtime gate is met.
- [x] Update evidence in Artifact -> Evidence -> Decision -> Project State ->
  Next Action -> Session Handoff order.

**Stop conditions:**

1. Any perturbed point loses positivity, uniqueness, or 256/256 support.
2. Tangent and corrected AP finite difference disagree after precision
   escalation and a valid h plateau.
3. Local adjoint identities fail.
4. AP/ball precision cannot certify the derivative.
5. A mathematically passing implementation remains impractical for the
   planned adaptive workload.

No approximation is substituted at a stop condition.
