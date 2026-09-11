# 1. Skills / workflow used

This is a documentation-only design study scoped from the repository's
Superpowers plan and the current lifecycle state. Ponytail was applied at full
intensity: the design keeps the smallest solve-based reverse that can answer
the question, reuses cached forward state, avoids explicit inverse matrices,
and does not add an implementation that has not been validated.

The study reads the frozen model and security scope, the validated constrained
C4 tangent source, its runners and tests, and the traceable four-direction
800-digit artifacts. It does not execute a reverse VJP, connect autograd,
differentiate the full Z interval, run an optimizer step, train, access final
test data, or run a compiled benchmark.

# 2. Validated forward system used as basis

The basis is the isolated EXPERIMENTAL_DIAGNOSTIC_ONLY exact C4
source-moment system in src/cvqkd/c4_constrained_tangent.py. The 64 orbit
masses p sum to one and the 64 physical representative amplitudes are z.
For s in Z4, let r=s-1 mod 4, D=diag(z), and
P=diag(1/(2 sqrt(p))). The raw sector blocks are

$$
H_d[i,j]=\sqrt{p_i p_j}\exp\left(
-\frac{|z_i|^2+|i^d z_j|^2}{2}+\overline{z_i}i^d z_j\right).
$$

The sector Fourier projection and positive square root are

$$
X_s=\sum_{d=0}^3 i^{sd}H_d,\qquad
G_s=\frac{X_s+X_s^H}{2},\qquad S_s=G_s^{1/2}.
$$

The exact constrained solves are

$$
B_sS_r=S_sD,\qquad A_sG_r=G_sD.
$$

The remaining forward graph is

$$
Q_s=S_sP,\qquad T_s=A_sQ_r,\qquad
u_k=\sum_{s,i}\overline{Q_s[i,k]}T_s[i,k],\qquad U=\operatorname{diag}(u),
$$

$$
E_s=T_s-Q_sU,\qquad
C=\sum_s\operatorname{Re}\operatorname{Tr}(S_sB_sS_rB_s^H),
$$

$$
w=\sum_{s,k}4p_k\|E_s[:,k]\|_2^2.
$$

The target has minimum Gram eigenvalue
3.9730108272405810054e-618, corrected
C=0.85985110654649868138037962728289179096834048571987, and
w=0.018327610474963502048823295065766568532781601388489.
The PS, GS-real, GS-imaginary, and V_A directions all passed the bounded
800-digit central production-map finite-difference comparison with maximum
relative mismatch 4.9301249353e-9, below the 1e-6 target. Their target
tangent runtimes were approximately 1181.13 s, 2001.04 s, 2878.94 s, and
1795.96 s, respectively.

This validates the forward tangent boundary diagnostically. It does not
validate a reverse or make the system suitable for training.

# 3. Exact constrained adjoint derivation

Use the real Frobenius pairing

$$
\langle A,B\rangle=\operatorname{Re}\operatorname{Tr}(A^HB).
$$

For a scalar objective

$$
L=g_C C+g_w w,
$$

the reverse accumulates adjoints from the terminal scalars toward p and z. A
formal residual Lagrangian can introduce

$$
F_{S,s}=S_s^2-G_s,\quad
F_{B,s}=B_sS_r-S_sD,\quad
F_{A,s}=A_sG_r-G_sD
$$

with matrix multipliers. Eliminating those multipliers gives the following
solve-based rules. The equations are exact for the validated constrained
forward graph; they are a design, not an executed VJP.

For a generic right solve

$$
XA=Y,\qquad dX\,A=dY-X\,dA,
$$

the reverse is

$$
\bar Y A^H=\bar X,\qquad
\bar A\mathrel{+}=-X^H\bar Y.
$$

No explicit A^{-1} is required. Equivalently, the adjoint equation is the
left solve A^H barY^H=barX^H.

For B_s S_r=S_sD, set Y_s^B=S_sD, solve
barY_s^B S_r^H=barB_s, and accumulate

$$
\bar S_r\mathrel{+}=-B_s^H\bar Y_s^B,\qquad
\bar S_s\mathrel{+}=\bar Y_s^B D^H,\qquad
\bar D\mathrel{+}=S_s^H\bar Y_s^B.
$$

For A_s G_r=G_sD, set Y_s^A=G_sD, solve
barY_s^A G_r^H=barA_s, and accumulate

$$
\bar G_r\mathrel{+}=-A_s^H\bar Y_s^A,\qquad
\bar G_s\mathrel{+}=\bar Y_s^A D^H,\qquad
\bar D\mathrel{+}=G_s^H\bar Y_s^A.
$$

For the C branch, use the product chain

$$
Y_1=S_sB_s,\qquad Y_2=Y_1S_r,\qquad Y_3=Y_2B_s^H.
$$

Starting with barY3=g_C I, reverse it as

$$
\bar Y_2\mathrel{+}=\bar Y_3B_s,\qquad
\bar B_s\mathrel{+}=\bar Y_3^HY_2,
$$

$$
\bar Y_1\mathrel{+}=\bar Y_2S_r^H,\qquad
\bar S_r\mathrel{+}=Y_1^H\bar Y_2,
$$

$$
\bar S_s\mathrel{+}=\bar Y_1B_s^H,\qquad
\bar B_s\mathrel{+}=S_s^H\bar Y_1.
$$

For w, define W=diag(4p). The direct contributions are

$$
\bar E_s=2g_wE_sW,\qquad
\bar p_k\mathrel{+}=4g_w\sum_s\|E_s[:,k]\|_2^2.
$$

Reverse E_s=T_s-Q_sU and
u_k=sum_{s,i} conj(Q_s[i,k]) T_s[i,k] as

$$
\bar T_s\mathrel{+}=\bar E_s,\qquad
\bar Q_s\mathrel{+}=-\bar E_sU^H,\qquad
\bar u\mathrel{+}=-\operatorname{diag}(Q_s^H\bar E_s),
$$

then

$$
\bar Q_s[:,k]\mathrel{+}=T_s[:,k]\overline{\bar u_k},\qquad
\bar T_s[:,k]\mathrel{+}=Q_s[:,k]\bar u_k.
$$

Equivalently, after summing the s contribution,

$$
\bar T_s=\bar E_s+Q_s\operatorname{diag}(\bar u),\qquad
\bar Q_s=-\bar E_sU^H+T_s\operatorname{diag}(\overline{\bar u}).
$$

For T_s=A_sQ_r and Q_s=S_sP,

$$
\bar A_s\mathrel{+}=\bar T_sQ_r^H,\qquad
\bar Q_r\mathrel{+}=A_s^H\bar T_s,
$$

$$
\bar S_s\mathrel{+}=\bar Q_sP^H,\qquad
\bar P\mathrel{+}=S_s^H\bar Q_s.
$$

The square-root tangent is

$$
S_s\,dS_s+dS_s\,S_s=dG_s.
$$

Because this Sylvester operator is self-adjoint under the real Frobenius
pairing for Hermitian positive S_s, the reverse solves

$$
S_s\bar G_s^{\rm root}+\bar G_s^{\rm root}S_s
=\mathcal H(\bar S_s),
$$

where H(X)=(X+X^H)/2. There is no extra factor of two: the scalar
check dG=2S dS gives barG=barS/(2S).

Add all G_s contributions from the A branch and square-root branch before
the raw Fourier projection. Then

$$
\bar X_s=\mathcal H(\bar G_s),\qquad
\bar H_d=\sum_s\overline{i^{sd}}\bar X_s.
$$

For an entry of H_d, define

$$
q=\overline{\bar H_d[i,j]}H_d[i,j],\quad
a=-\frac{\overline{z_i}}2,\quad
b=-\frac{z_i}{2}+i^dz_j,
$$

$$
c=-\frac{\overline{z_j}}2+\overline{z_i}i^d,\qquad
d=-\frac{z_j}{2}.
$$

The raw-entry pullback is

$$
\bar p_i\mathrel{+}=\frac{\operatorname{Re}(q)}{2p_i},\qquad
\bar p_j\mathrel{+}=\frac{\operatorname{Re}(q)}{2p_j},
$$

$$
\bar z_i\mathrel{+}=(qa)^*+qb,\qquad
\bar z_j\mathrel{+}=(qc)^*+qd.
$$

The diagonal maps add

$$
\bar p_k\mathrel{+}=-\frac{\operatorname{Re}(\bar P_{kk})}{4p_k^{3/2}},
\qquad
\bar z_k\mathrel{+}=\bar D_{kk}.
$$

The final probability adjoint is real after accumulation. The final amplitude
adjoint is complex and uses the real-pairing convention consistently.

# 4. Complex adjoint convention

The reverse must use the real Frobenius pairing and distinguish ordinary
transpose, conjugation, and Hermitian transpose. The primitive rules are:

| Forward operation | Reverse contribution |
|---|---|
| Y=AXB | barX += A^H barY B^H |
| Y=X.T | barX += barY.T |
| Y=conj(X) | barX += conj(barY) |
| Y=X.H | barX += barY.H |
| Y=cX | barX += conj(c) barY |
| Y=H(X) | barX += H(barY) |
| Y=diag(x) | barx += diag(barY) |
| Y=X^{-1} | barX += -X^{-H}barY X^{-H}; diagnostic only, never form the inverse |

The corrected worker contains the ordinary transpose path x2.T; replacing
that with a Hermitian transpose would change the complex derivative. On the
real physical parameter path, the amplitude pullback obeys
d conj(z)=conj(dz), which is why the raw-entry formula has both conjugate
and non-conjugate terms.

For the C4 expansion from one representative amplitude alpha_k to physical
amplitudes alpha_{kq}=i^q alpha_k and replicated mass p_{kq}=p_k/4,

$$
\bar\alpha_k=\sum_{q=0}^3\overline{i^q}\,\bar\alpha_{kq},\qquad
\bar p_k=\frac14\sum_{q=0}^3\bar p_{kq}.
$$

If the exact physical normalization is part of the reverse, let raw
g_k map to relative x_k=g_k/r, where

$$
r^2=\frac1{64}\sum_k|g_k|^2.
$$

Then, with barx already accumulated,

$$
\bar g_k=\frac{\bar x_k}{r}
-\frac{\operatorname{Re}\sum_j\overline{\bar x_j}g_j}{64r^3}g_k.
$$

For alpha=s x, E=sum_k q_k|x_k|^2, and
eta=s Re(sum_k conj(baralpha_k)x_k), use

$$
\bar x\mathrel{+}=s\bar\alpha-\eta\frac{q}{E}x,\qquad
\bar q\mathrel{+}=-\eta\frac{|x|^2}{2E},\qquad
\bar V_A\mathrel{+}=\frac{\eta}{2V_A}.
$$

For a probability softmax q=softmax(ell),

$$
\bar\ell_k=q_k\left(\bar q_k-\sum_jq_j\bar q_j\right).
$$

# 5. Reverse dependency graph

The reverse must accumulate shared inputs across every sector before applying
the upstream transforms:

~~~text
g_C, g_w
   |
   +--> C products ----------------------------+
   |                                          |
   +--> w --> E --> (T,Q,U) --> (A,Q) -------+--> S,G
                                               |
                         (A constraint) -------+
                         (B constraint) -------+
                                               |
                         sqrt adjoint --------+
                                               |
                    G --> X --> H_d ----------+
                                               |
                       D,P,p,z  <---------------+
                                               |
                     C4 expansion / normalization / softmax
~~~

There are four sectors. r=s-1 mod 4 makes S_r, G_r, and Q_r shared
consumers, so adjoints must be added rather than overwritten. The raw blocks
share p and z across all d, while P, D, and the explicit 4p_k weight share the
same probability and amplitude inputs. A reverse implementation that solves
sector-by-sector and discards accumulated adjoints would be mathematically
wrong.

| Node | Shape | Sector count | Reverse action |
|---|---:|---:|---|
| H_d,G_s,S_s,B_s,A_s,Q_s,T_s,E_s | 64x64 | 4 each | retain or recompute from a bounded tape |
| D,P,U | 64x64 diagonal | 1 | retain diagonal entries |
| C,w | scalar | 1 | seed terminal adjoints |
| p,z | 64 | 1 | collect all sector and map contributions |

# 6. Expensive-operation count

The following count assumes the forward tangent already retained the
Hermitian eigensystems or factorizations used to construct S_s and to solve
the triangular right systems. Reusing those factorizations is essential.

| Operation | Forward value | Reverse design | Notes |
|---|---:|---:|---|
| G_s Hermitian eigendecomposition/factorization | 4 | 0 new | reuse cached eigenvalues/eigenvectors or factor data |
| S_s=G_s^(1/2) construction | 4 | 0 new | cached S_s and spectral data |
| B_s S_r=S_sD right solve | 4 | 4 adjoint solves | each reverse solve uses S_r^H |
| A_s G_r=G_sD right solve | 4 | 4 adjoint solves | each reverse solve uses G_r^H |
| Equivalent left-solve forms | 0 | 8 | same eight adjoint solves, not an extra class |
| Square-root Sylvester | 0 | 4 | self-adjoint solve per sector |
| C4 Fourier/projection and Hermitian projection | 4 | 4 | transforms, not dense solves |
| Dense GEMM-scale products | about 36 | about 64 | equivalent 64x64 products; diagonal and elementwise work omitted |

Thus the exact reverse needs eight primal constrained right solves already
present in the forward state, eight adjoint constrained solves, and four
square-root Sylvester adjoints. It does not need explicit inverse matrices or
new eigendecompositions when the forward spectral state is cached. Recomputing
the spectral state adds four factor/eigensystem constructions and increases
both runtime and memory pressure.

# 7. Cached state / memory estimate

The smallest useful tape retains the four-sector matrix state needed by both
the value and reverse paths: H, G, U, S, B, A, Q, T, and E, counted
conservatively as 36 matrix-equivalents after including replicated diagonal
and sector work. X and temporary product intermediates can be recomputed
from these values. Explicit R and J inverse matrices are not part of the
tape.

At 800 decimal digits, a 64x64 complex matrix has 4096 entries, two real
components per entry, and approximately 42 multiprecision limbs per real
component. A conservative payload estimate for one matrix is 2,752,512
bytes, about 2.62 MiB. The resulting order-of-magnitude estimates are:

| Allocation | Compact payload | Python/multiprecision budget |
|---|---:|---:|
| 36-matrix forward tape | about 95 MiB (0.10 GB) | about 170--220 MiB (0.18--0.23 GB) |
| Tape plus 24--32 adjoint/work matrices | about 160--180 MiB | about 0.35--0.60 GB |
| Peak with retry/workspace allowance | about 0.25--0.40 GB | budget 0.5--1.0 GB |

Memory is therefore manageable on a machine with a few GB available. The
dominant blockers are conditioning, multiprecision arithmetic throughput,
factorization reuse, and retry behavior rather than the raw 64x64 tape size.

# 8. Precision estimate

At the target support boundary,

$$
\lambda_{\min}\simeq3.9730\times10^{-618},\quad
\sqrt{\lambda_{\min}}\simeq1.9932\times10^{-309},
$$

$$
\lambda_{\min}^{-1/2}\simeq5.017\times10^{308},\qquad
\lambda_{\min}^{-1}\simeq2.517\times10^{617}.
$$

The square-root Sylvester denominator contains 2 sqrt(lambda_min). An
explicit inverse-square-root derivative can reach approximately 6.31e925,
while an inverse derivative can reach approximately 6.34e1234. Recovering a
physical derivative of order 1e-3 after cancellation at the latter scale
would require roughly 1238 significant decimal digits before any guard
digits.

The constrained formulation avoids explicitly forming those inverse
matrices, but it does not remove the underlying condition number. A
provisional validation ladder is therefore 1250, 1450, and 1650 decimal
digits, with 1450 digits providing roughly 150--200 decimal guard digits over
the worst estimated scale, or about 4820 bits. This ladder is a planning
estimate only. No precision is approved until two successive levels produce
stable objective adjoints, residuals, and inner-product identities.

# 9. Python/mpmath runtime model

The existing target measurements put a cached forward evaluation roughly in
the 300--420 second range and a constrained tangent central evaluation in the
1082--1407 second range, before counting all finite-difference endpoints.
The old 25653.3898618-second custom-backward attempt is a warning about
uncontrolled numerical work, not a reliable reverse runtime estimate.

For one exact constrained VJP, including the eight adjoint right solves, four
Sylvester solves, dense products, and higher precision, a deliberately broad
unmeasured estimate is:

| Case | One VJP per state |
|---|---:|
| Optimistic | about 1200 s (20 min) |
| Realistic | about 3600 s (60 min) |
| Pessimistic | about 10800 s (3 h) |

These figures are estimates, not evidence. They assume cached forward
factors, no failed precision retry, and a single process. Recomputing
factorizations, Python object allocation, or a failed 1250-digit pass can
push the result toward the pessimistic end.

# 10. Training-scale runtime estimates

Using the realistic 3600-second per-state estimate, serial state counts would
cost approximately:

| States per step | 1 state | 10 states | 100 states | 1000 states |
|---:|---:|---:|---:|---:|
| Batch 1 | 1 h | 10 h | 4.2 d | 41.7 d |
| Batch 8 | 8 h | 80 h | 33.3 d | 333 d |
| Batch 32 | 32 h | 320 h | 133 d | 3.65 y |

Even the optimistic 1200-second estimate makes a batch of eight about 2 h
40 min and a batch of 32 about 10 h 40 min per step before optimizer and
data costs. This misses the current research gates of 60 seconds per state
for a one-step smoke and approximately 2 seconds per state for a batch-32
candidate. An exact mpmath reverse is consequently not a plausible training
backend.

# 11. Compiled multiprecision feasibility

Relative to the realistic 3600-second Python estimate, a compiled backend
would need approximately the following end-to-end speedups:

| Target | Required speedup | Broad engineering range |
|---|---:|---:|
| under 60 s per state | 60x | 20--180x |
| under 10 s per state | 360x | 120--1080x |
| under 1 s per state | 3600x | 1200--10800x |

A narrow C++17 implementation using FLINT/Arb or MPFR/MPC with contiguous
storage, reused factorizations, and parallel dense kernels is credible for a
20--60x first measurement. Reaching 360x may require batching, parallel
sectors, and a tuned multiprecision matrix kernel. A 3600x direct port is not
credible without changing the algorithm or hardware assumptions. Julia alone
does not guarantee the required improvement.

The correct next experiment is therefore a small compiled primitive bundle,
not a full reverse implementation: one 64x64 sector, one right solve and its
adjoint, one square-root Sylvester solve and its adjoint, at the planned
precision ladder.

# 12. Ball-arithmetic assessment

Ball arithmetic would make the numerical boundary more useful for
publication-grade evidence. It can certify positive-definiteness/support
conditions, constrain square-root and solve residuals, produce enclosures for
C, w, and a VJP directional derivative, and fail closed when the interval is
too wide. It also supports precision escalation with an auditable reason.

It does not make the problem cheap or automatically provide a useful point
gradient. Dependency overestimation can make intervals wide, especially
through shared p, z, and sector operands; matrix interval solves can be much
slower; and a full-Z maximum still needs a branch-safe nonsmooth treatment.
Ball widths also need to be reported rather than hidden behind a midpoint.

The practical role is certification and validation of a compiled
multiprecision prototype, not ball arithmetic inside every adaptive-training
step. A fail-closed interval result should block the run rather than silently
fall back to an unbounded point estimate.

# 13. Future reverse validation plan

Any implementation must be validated in this order. A failure at any stage
stops the next stage and leaves the reverse path closed.

1. Validate a cheap generic right-solve adjoint identity at 80 decimal digits;
   require the directional inner-product mismatch below 1e-40.
2. Validate the B constraint adjoint identity on a small well-conditioned
   sector.
3. Validate the A constraint adjoint identity on the same class of fixture.
4. Validate the self-adjoint square-root Sylvester identity, including the
   Hermitian projection and the absence of an extra factor of two.
5. Validate product, transpose, conjugation, Hermitian projection, diagonal,
   and C4 Fourier transforms with complex directional probes.
6. Assemble a small complete C4 reverse and compare its scalar directional
   derivative with finite differences.
7. Run one target sector at 800, 1250, and 1450 decimal digits; require
   stable adjoints, residuals, and inner-product identities before proceeding.
8. Validate the PS target against the corrected AP production finite
   difference, requiring dC, dw, and dJ relative error at most 1e-6 and no
   uncontrolled 1e100-scale final adjoint.
9. Repeat the full target comparison for GS-real.
10. Repeat it for GS-imaginary.
11. Repeat it for V_A.

Only after all eleven stages pass may full-Z differentiation, branch-gap
handling, or any training-facing integration be considered. None of those
later stages is authorized by this study.

# 14. Primitive adjoint identity tests

The implementation should first expose only small numerical identities. Each
test uses an independent random or deterministic complex probe and compares
the reverse pairing with a finite directional pairing.

| Primitive | Identity to check | Initial pass criterion |
|---|---|---:|
| Right solve | Re <barX,dX> = Re <barY,dY> + Re <barA,dA> | at most 1e-40 |
| Left/adjoint solve | same identity with A^H | at most 1e-40 |
| Sylvester | Re <barS,dS> = Re <barG,dG> | at most 1e-40 |
| Matrix product | barX=A^H barY B^H | at most 1e-40 |
| Ordinary transpose | barX=barY.T | at most 1e-40 |
| Conjugation | barX=conj(barY) | at most 1e-40 |
| Hermitian projection | barX=H(barY) | at most 1e-40 |
| C4 transform | forward/reverse DFT pair | at most 1e-40 |

The same identities must remain stable at two successive precision levels.
A fixture can pass a scalar finite difference while still having a wrong
complex transpose convention, so the primitive pairing tests are mandatory.

# 15. Practicality gates

There are three independent gates.

| Gate | Required evidence | Current posture |
|---|---|---|
| G1 mathematical soundness | Complete derivation and primitive identities with no transpose ambiguity | Design pass; identities not run |
| G2 numerical reliability | Small, single-sector, and all four target directions pass support, normalization, residual, precision, and finite-difference checks; no uncontrolled 1e100 final adjoints | Forward tangent pass; reverse not validated |
| G3 runtime | Research prototype at most 1800 s/state; one-step smoke at most 60 s/state; batch candidate about 2 s/state at batch 32, or at most about 64 s/source-gradient batch | Fails for mpmath estimate |

The current forward tangent supplies useful G2 evidence for the forward
boundary, but it does not supply G1 reverse identities or G2 reverse
evidence. The mpmath reverse also fails G3 on the conservative runtime model.
Therefore the only plausible next route is a compiled multiprecision
prototype after the primitive identities are implemented and measured.

# 16. Publication evidence requirements

Any future reverse result must separate mathematical security equations from
the numerical realization. The artifact must identify the backend, compiler
and flags, library versions, source hashes, precision ladder, guard digits,
factorization reuse, retry policy, and hardware.

It must include convergence and support checks, solve and Sylvester residuals,
primitive adjoint identities, scalar finite-difference comparisons for all
four physical directions, memory and wall-clock measurements, and the
exact C4/full-Z scope. It must state whether a branch gap is present, how
shared sector adjoints are accumulated, and which operations are exact
solves versus approximations.

If ball arithmetic is used, publish enclosure endpoints and widths for
support, C, w, and directional VJP quantities, together with the
fail-closed and precision-escalation rules. Do not report only midpoint
gradients. Do not claim training readiness from a single target state or
from a forward tangent.

# 17. Code/document changes

This study creates only this documentation artifact and the corresponding
traceability updates. It does not modify the frozen specification,
scientific equations, constrained tangent source, runners, tests, or
training code. The existing plan item to audit local primitive adjoint
identities remains unchecked because the identities were designed here but
not executed.

The lifecycle state remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS, and adaptive readiness remains
NOT_READY_FOR_ADAPTIVE_TRAINING. The existing four-direction forward
tangent artifact remains diagnostic-only.

# 18. Verification

The required source, plan, test, runner, artifact, frozen-specification, and
state documents were read and cross-checked before this report was written.
No reverse VJP, full-Z backward, optimizer step, training run, final-test
access, publication-scale evaluation, or compiled benchmark was performed.

The focused non-reverse verification after the documentation update is:

- the constrained tangent and corrected AP custom-backward focused tests:
  7/7 passed;
- Python syntax compilation for the touched tangent runner and focused test:
  passed;
- repository whitespace verification with git diff --check: passed.

These checks verify repository integrity and the existing forward boundary.
They are not reverse validation evidence.

# 19. Final practicality decision

SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE

# 20. Reason for decision

The constrained reverse is mathematically sound as a solve-based adjoint:
eight cached primal right solves have eight corresponding adjoint solves, and
the four square-root derivatives use four self-adjoint Sylvester solves.
The derivation needs no explicit inverse matrices and the estimated tape fits
within a sub-GB Python budget.

It is not yet target-validated. The target Gram eigenvalue is approximately
1e-618, the forward tangent already takes minutes per direction, and the
conditioning estimate points to a 1250--1650 decimal-digit ladder. The
unmeasured Python/multiprecision VJP estimate is 1200--10800 seconds per
state, far above the 60-second smoke and approximately 2-second batch
candidate gates. The old uncontrolled custom-backward result is additional
evidence that a direct Python reverse is a poor engineering target, but it is
not used as a quantitative benchmark.

A compiled, narrowly scoped multiprecision prototype is the smallest
experiment that can distinguish arithmetic throughput from mathematical
failure while preserving the exact constrained formulation.

# 21. Adaptive-training readiness

NOT_READY_FOR_ADAPTIVE_TRAINING

# 22. Recommended next task

Implement and benchmark one C++17 FLINT/Arb or MPFR/MPC 64x64 one-sector
primitive bundle: the primal and adjoint right solve plus the
square-root Sylvester solve and its adjoint, with cached factorization data.
Run it at 1250, 1450, and 1650 decimal digits, require solve residuals and
inner-product identities at every level, and measure factor-reuse behavior.
Use a target of at most 10 seconds for the one-sector bundle at 1450 digits.

Do not implement the full reverse, connect autograd, differentiate full Z,
run training, or access final-test data as part of that task.
