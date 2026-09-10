# Exact AP Source-Moment Custom Backward Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prototype one mathematically exact arbitrary-precision reverse-mode boundary for the existing full-support 256-state C4 source moments C(p, alpha) and w(p, alpha), then validate it against AP central differences without enabling training.

**Architecture:** Keep the current complex128 production gate and evaluation-only AP forward boundary untouched. Add a narrow experimental AP worker that evaluates the existing four 64-by-64 C4 sectors, retains G_s, S_s, and R_s, and applies a hand-derived reverse VJP. The reverse worker returns gradients for the 64 orbit probabilities and 64 representative amplitudes; a test-only torch adapter expands those gradients through PS/GS/V_A without changing the normal trainer.

**Tech Stack:** Python standard library, existing mpmath AP backend, existing PyTorch models/tests. No dependency or security-equation change.

**Spec:** User feasibility request in the pasted task; current definitions in src/cvqkd/gram_moments.py and scripts/full_support_c4_worker.py.

## Global Constraints

- Preserve M=256, fourfold C4 symmetry, and all 256 positive probabilities.
- Preserve the current C, w, full-Z, and raw-SKR definitions exactly.
- Do not use eigenvalue clipping, jitter, tolerance weakening, pseudoinverse rank reduction, or support truncation.
- Do not route the experimental boundary into trainer.py or normal production training.
- Do not call optimizer.step(), run epochs, use final-test data, or run publication-scale evaluation.
- Keep multi-minute AP validation out of normal CI; use stored references and small fixtures for fast tests.

## Exact mathematical formulation

For one C4 orbit representative vector z in C^64, orbit probability p in R_{>0}^64, and r_d=i^d, define the existing code's raw blocks and sectors:

    B_d[i,j] = sqrt(p_i p_j) exp(-(abs(z_i)^2 + abs(z_j)^2)/2
                              + conj(z_i) r_d z_j)
    G_s = 1/2 (sum_d r_(s d) B_d + (sum_d r_(s d) B_d)^dagger).

The AP worker diagonalizes each positive-definite sector and forms

    S_s = G_s^(1/2),       R_s = G_s^(-1/2),
    D = diag(z),            P = diag((2 sqrt(p))^(-1)).

Use the exact algebraic equivalent of the current implementation:

    Q_s = S_s P,
    A_s = G_s D G_(s-1)^(-1),
    T_s = A_s Q_(s-1),
    u_k = sum_s (Q_s^dagger T_s)_(k,k).

The current source moments remain

    C = sum_s Re trace(S_s B_s S_(s-1) B_s^dagger),
    B_s = S_s D R_(s-1),

    w = sum_(s,k) 4 p_k ||T_s[:,k] - Q_s[:,k] u_k||_2^2.

These are only a notation-preserving reverse form; no security surrogate is introduced.

### Square-root and inverse-square-root differential

From S^2=tau,

    S dS + dS S = d tau.

For R=S^(-1),

    dR = -R (dS) R.

For a real scalar loss L, define matrix adjoints by

    dL = Re trace(bar_X^dagger dX).

Given upstream bar_S and bar_R, first pass through the inverse:

    bar_S <- bar_S - R bar_R R.

Then solve the self-adjoint Sylvester adjoint

    S bar_tau + bar_tau S = bar_S.

The AP implementation solves this in the retained eigenbasis. If
G=U diag(lambda) U^dagger,

    bar_tau = U ((U^dagger bar_S U)_(ij) /
                  (sqrt(lambda_i)+sqrt(lambda_j)))_(ij) U^dagger.

This is the exact Frechet adjoint for positive full support and does not use a thresholded inverse.

### Reverse of C

Reverse the product Y_s=S_s B_s S_(s-1) B_s^dagger from upstream g_C
using bar_Y_s=g_C I. Use ordinary product adjoints in the implementation:

    Y3=Y2 B_s^dagger:
        bar_Y2 += bar_Y3 B_s,  bar_B_s += bar_Y3^dagger Y2;
    Y2=Y1 S_(s-1):
        bar_Y1 += bar_Y2 S_(s-1)^dagger,
        bar_S_(s-1) += Y1^dagger bar_Y2;
    Y1=S_s B_s:
        bar_S_s += bar_Y1 B_s^dagger,
        bar_B_s += S_s^dagger bar_Y1.

Then reverse B_s=S_s D R_(s-1):

    bar_S_s += bar_B_s (D R_(s-1))^dagger,
    bar_D += S_s^dagger bar_B_s R_(s-1)^dagger,
    bar_R_(s-1) += (S_s D)^dagger bar_B_s.

### Reverse of w

Let E_s=T_s-Q_s diag(u) and P4=diag(4p). For upstream g_w,

    bar_E_s = 2 g_w E_s P4,
    bar_T_s += bar_E_s,
    bar_Q_s += -bar_E_s diag(u)^dagger,
    bar_u += -diag(Q_s^dagger bar_E_s).

For u_k=sum_s sum_i conj(Q_(s,ik)) T_(s,ik),

    bar_Q_(s,ik) += T_(s,ik) conj(bar_u_k),
    bar_T_(s,ik) += Q_(s,ik) bar_u_k.

Reverse T_s=A_s Q_(s-1), Q_s=S_s P, and
A_s=G_s D G_(s-1)^(-1) with standard product and inverse adjoints. The
explicit P4 contribution is

    dL/dp_k += 4 g_w sum_(s,i) abs(E_(s,ik))^2,

and

    d/dp_k [1/(2 sqrt(p_k))] = -1/(4 p_k^(3/2)).

Finally combine all bar_S_s, bar_R_s, and bar_G_s contributions and apply
the Sylvester adjoint once per sector.

### Reverse of the C4 sector construction

The sector symmetrization is self-adjoint for Hermitian upstream matrices.
For q_(d,ij)=conj(bar_B_(d,ij)) B_(d,ij), the real probability and complex
prototype gradients are

    dp_i += Re[ (1/(2 p_i)) sum_j (q_(d,ij)+q_(d,ji)) ],

    dz_i += sum_j [
        conj(q_(d,ij) (-1/2 conj(z_i)))
        + q_(d,ij) (-1/2 z_i + r_d z_j)
    ] + sum_j [
        conj(q_(d,ji) (-1/2 conj(z_i) + conj(z_j) r_d))
        + q_(d,ji) (-1/2 z_i)
    ].

The implementation will compare these gradients against AP central differences,
then expand representative gradients through the existing C4 orbit map for
the torch chain.

## Prototype boundary

The experimental boundary is one narrow entry point:

    torch orbit p,z (float64/complex128)
            -> exact-binary64 AP sectors and C,w
            -> AP retained eigensystems and implicit adjoint VJP
            -> torch gradients for p,z

It is evaluation/test-only and is not imported by gram_moments.py or trainer.py
by default. The normal complex128 fast gate and AP evaluation-only fallback
remain unchanged.

## Tasks

### Task 1: Add failing low-dimensional reverse tests

**Files:**
- Create: tests/test_ap_custom_backward.py
- Test only: a small positive C4 fixture and a well-conditioned analytic source-moment graph.

- [x] Write one test asserting the experimental reverse API returns finite C, w, and gradients for a 4-orbit fixture.
- [x] Write one test comparing the combined aC+bw VJP against central differences on that fixture.
- [x] Run python -m unittest tests.test_ap_custom_backward -v; the first run failed on the missing experimental module/API.

### Task 2: Implement the minimal AP reverse worker

**Files:**
- Create: src/cvqkd/ap_custom_backward.py

- [x] Reuse the existing sector construction and AP eigensystem convention from full_support_c4_worker.py.
- [x] Implement matrix-product adjoints, inverse adjoints, square-root Sylvester adjoints, and the sector-to-p,z reverse formulas above.
- [x] Keep all AP values at the requested decimal precision and reject unresolved/non-positive full support.
- [x] Run the low-dimensional tests and confirm the expected red-to-green transition.

### Task 3: Validate the exact 256-state forward and VJP manually

**Files:**
- Create: results/ap_custom_backward_case_A_20260910.json (ignored exploratory artifact if the repository result policy excludes it).

- [x] Reconstruct the exact uniform 256-state Case A ensemble and verify the ensemble hash against the stored AP reference.
- [ ] Compare forward C,w with the verified 800/900-digit values; C agrees, but w exposes an AP-worker definition mismatch.
- [ ] Run one real-p direction, one real-z direction, one imaginary-z direction, one V_A-scaling direction, and one combined aC+bw VJP against AP central differences.
- [x] Measure one AP reverse VJP at 800 digits; estimate batch 1/8/32 costs without running those batches.
- [x] Do not execute optimizer steps or normal training.

### Task 4: Validate the torch PS/GS/V_A chain if and only if Task 3 passes

**Files:**
- Modify: tests/test_ap_custom_backward.py only for fast chain checks.

- [ ] Use torch only for logits-to-softmax and existing GS/V_A normalization.
- [ ] Call the custom boundary once and check finite/nonzero PS, GS-real, GS-imag, and V_A gradients.
- [ ] Run one full-Z state backward only after source-moment VJP validation; do not call optimizer.step().

### Task 5: Final verification and evidence update

**Files:**
- Modify only relevant state files: docs/EVIDENCE.md, docs/DECISION_LOG.md, docs/PROJECT_STATE.md, docs/NEXT_ACTIONS.md, .agent/SESSION_HANDOFF.md.

- [ ] Run focused tests, py_compile, and git diff --check.
- [ ] Run a Ponytail review of the diff and remove unrelated changes.
- [ ] Record exactly one required classification and exactly one remaining blocker.
- [ ] Keep lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive status NOT_READY_FOR_ADAPTIVE_TRAINING unless all requested source-moment validations pass.

## Stop criteria

Stop without integrating a custom boundary if any of the following is true:

1. AP cannot resolve all 256 positive modes at the precision needed by the
   retained formulas.
2. The implicit-adjoint VJP disagrees with AP central differences beyond the
   preregistered 1e-6 relative target for non-near-zero directions.
3. A single AP VJP is so slow that the exact method is not a practical adaptive
   training path; classify it as correct-but-impractical only after derivative
   agreement is demonstrated.

No approximation is substituted at a stop criterion.

This run also stopped because the existing AP worker's aa=sr*x2.T does not
match the current C4 a_blocks=G_s D G_(s-1)^(-1) formula. The worker's stored
w reference is therefore not a valid forward target for this VJP until that
separate fallback bug is corrected and its downstream artifacts are rebound.
