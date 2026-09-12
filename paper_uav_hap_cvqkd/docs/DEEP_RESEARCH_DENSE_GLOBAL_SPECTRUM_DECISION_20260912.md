# Deep research decision memo: whether a dense global AP eigensolve is needed

Date: 2026-09-12

## Executive decision

This is a research-only numerical-analysis memo. The expensive target
calculation—a dense 256-by-256 arbitrary-precision eigendecomposition at the
precision needed to resolve the smallest support modes—was **not executed**.
The existing machine-readable localization artifact reports
global_spectrum_status = NOT_RUN, and no new dense-global spectrum artifact is
claimed here.

The dense-check classification is:

**LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT**

The immediate AP-blocker classification is:

**INSUFFICIENT_AP_PRECISION**

The second label describes the earlier fail-closed attempt, not a change to
the model. The current worker, with the current source and the same frozen
binary64 input convention, now resolves all 256 modes for PS and Full at
successive high-precision rows. That evidence removes the need to diagnose a
production worker or fail-gate bug by spending hours on a redundant dense
global eigensolve. The prior failure artifact is retained as historical
evidence because it did not record the high-precision rows needed to identify
its exact failure mechanism.

The exact next numerical task is:

**RUN_INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT**

Use the frozen median PS+V_A and Full inputs, rebuild the full weighted Gram
matrix independently at 80, 120, and 200 decimal digits, apply the explicit
C4 Fourier transform, calculate the bounded global spectrum at those
precisions, and compare it with the independently rebuilt sectors and the
current worker sectors. This task is a bounded implementation audit, not a
support certificate and not a security result. It should not be escalated to
the 700–900-digit dense target unless a stated mismatch survives the audit.

No probability floor, bounded-logit parameterization, reduced alphabet,
retraining, altered V_A, GS change, channel change, C/w change, or new
security proof is recommended by this memo.

## 1. Question and evidence boundary

The narrow question is whether a dense global weighted-Gram spectrum is
scientifically necessary to distinguish:

1. a PS-specific AP-worker bug;
2. a numerical conditioning or precision failure;
3. an AP fail-gate bug; or
4. an unresolved failure.

The source operator is

$$
\tau=\sum_{i=1}^{256}p_i\,|\alpha_i\rangle\langle\alpha_i|,
$$

and the source moments C and w are computed from its resolved support. The
security equations, physical Z interval, objective repair, corrected C/w
definition, and lifecycle gates are outside the scope of this memo and remain
unchanged.

The evidence boundary is deliberately narrow:

- the active frozen model specification is unchanged;
- the current AP worker is unchanged;
- direct binary64 hexadecimal serialization is retained;
- the high-control PS and Full sector runs are read-only diagnostics;
- the independent full-matrix check uses the serialized physical inputs and
  does not call the production sector constructor;
- no final-test access, publication-scale run, adaptive training, reverse
  VJP, full-Z backward, or security claim is authorized;
- a lower-precision dense global eigensolve was not completed in the present
  memo, so its status is NOT_RUN rather than PASS.

The current frozen model-spec SHA-256 is
8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843.
The current worker SHA-256 is
2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1.
The analysis-runner SHA-256 is
9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f.

## 2. What the current numerical record establishes

### 2.1 Independent direct full-matrix audit already completed

The artifact
[ps_va_ap_worker_localization_20260912.json](../results/ps_va_ap_worker_localization_20260912.json)
contains one median PS+V_A case and one matched Full positive control. It
builds a 256-by-256 weighted Gram matrix directly from the exact binary64
hexadecimal ratios and amplitudes at 100 decimal digits. It then applies an
independent four-point Fourier transform.

The relevant results are:

| case | trace residual | Hermiticity residual | maximum Fourier off-block residual | sector match residuals | global spectrum |
|---|---:|---:|---:|---|---|
| PS+V_A median | 3.2959746043559335e-17 | 0 | 0 | 0, 0, 0, 0 | NOT_RUN |
| Full median | 5.2041704279304213e-17 | 0 | 0 | 0, 0, 0, 0 | NOT_RUN |

The trace residual is not evidence of lost support. It is the exact-AP sum of
the serialized binary64 per-symbol probabilities minus one. The PyTorch
binary64 sum is one at its working precision, but the exact rational values
represented by those binary64 numbers sum to one plus a small rounding
residual. The residual is about 10^-17, while the support modes of interest
are about 10^-598 to 10^-612. It must be recorded and propagated, not hidden,
but it is many orders below any structural or support gate used here.

The 100-digit independent sector eigenvalues include tiny negative values of
order 10^-102. That is the expected finite-precision eigensolver floor at
this diagnostic precision, not a conclusion that the mathematical Gram
matrix is indefinite. The independent matrix construction nevertheless
reproduces the Fourier block structure and the sector matrices to the
reported precision.

### 2.2 Current worker high-control rows now converge

The current worker was instrumented without changing its source: the harness
observed sector matrices, eigensolver rows, and solve residuals while invoking
the worker normally. The high-control artifacts are:

- [ps_va_worker_instrumented_800_900_20260912.json](../results/ps_va_worker_instrumented_800_900_20260912.json)
- [ps_va_worker_instrumented_1000_1200_20260912.json](../results/ps_va_worker_instrumented_1000_1200_20260912.json)
- [full_worker_instrumented_800_900_20260912.json](../results/full_worker_instrumented_800_900_20260912.json)

| case and rows | rank at each row | minimum resolved eigenvalue | C | w | worker status |
|---|---:|---:|---:|---:|---|
| PS, 800/900 digits | 256/256 | 5.5183273131200776e-598 | 0.8610813007552428909072... | 0.0067220381757562110711... | FULL_SUPPORT_CONVERGED |
| PS, 1000/1200 digits | 256/256 | 5.5183273131200776e-598 | 0.8610813007552428909072... | 0.0067220381757562110711... | FULL_SUPPORT_CONVERGED |
| Full, 800/900 digits | 256/256 | 1.0195494813436373e-612 | 0.8594238956711868899434... | 0.0130447814829580742424... | FULL_SUPPORT_CONVERGED |

All four sectors have 64 positive modes at every reported high row. The
instrumented triangular solves report relative residual 0.0 in their
arbitrary-precision output. The maximum observed Hermiticity residual of the
sector matrices is also 0.0 because the worker explicitly applies the
Hermitian symmetrization required by its numerical contract.

The paired runtimes are approximately 633.8 seconds for the PS 800/900
artifact, 1056.8 seconds for the PS 1000/1200 artifact, and 1071.8 seconds
for the Full 800/900 artifact. These are not dense-global timings; they are
the measured cost of the instrumented four-sector worker and its
inverse-sensitive solves.

### 2.3 Historical failure versus current evidence

The older
[repaired_full_z_ps_va_exact_failure_20260911.json](../results/repaired_full_z_ps_va_exact_failure_20260911.json)
records a fail-closed PS high-ladder attempt and lower-precision ranks. It
does not retain the high-ladder eigenvalue rows, source hashes, or stage-level
diagnostics needed to decide whether the failure was a negative numerical
floor, a timeout, or a solver-stage issue. It is therefore a valid historical
record of a failed attempt but not a sufficient root-cause artifact.

The current unchanged worker's 800/900 and 1000/1200 rows are stronger,
directly relevant evidence. They show that the same mathematical PS input
does have a reproducible, fully resolved sector path. Thus:

- a true PS-only algebraic support loss is not supported;
- a persistent PS-specific worker bug is not supported;
- an AP fail-gate bug is not supported, because the worker accepts the
  correctly resolved high rows;
- the earlier blocker is best classified as insufficient precision or
  insufficient run-control evidence, with the historical artifact retained
  as a caution about reproducibility.

This does not turn the rows into a publication security result. It only
answers the numerical root-cause question at the level needed to decide
whether a dense global eigensolve is worth its cost.

## 3. Weighted Gram/source-spectrum derivation

Let the normalized coherent vectors be v_i = |alpha_i>, and define the
weighted synthesis operator

$$
A:\mathbb C^{256}\longrightarrow\mathcal H,\qquad
A e_i=\sqrt{p_i}\,v_i.
$$

Then

$$
\tau=AA^\ast,
\qquad
W=A^\ast A=P^{1/2}GP^{1/2},
\qquad
P=\operatorname{diag}(p_1,\ldots,p_{256}),
$$

where

$$
G_{ij}=\langle\alpha_i|\alpha_j\rangle
=\exp\left(
-\frac{|\alpha_i|^2+|\alpha_j|^2}{2}
+\alpha_i^\ast\alpha_j
\right).
$$

If W x = lambda x with lambda > 0, then A x is nonzero and

$$
\tau(Ax)=AA^\ast A x=A(Wx)=\lambda(Ax).
$$

The converse follows by applying A^\ast to an eigenvector of tau with
positive eigenvalue. Hence AA^\ast and A^\ast A have exactly the same
nonzero eigenvalues with multiplicity. This is also the singular-value
decomposition statement: both operators have eigenvalues equal to the
squares of the nonzero singular values of A.

The Fock-space operator tau is infinite-dimensional and has infinitely many
zero eigenvalues outside the finite span of the source vectors. W is the
finite 256-by-256 representation of all possible nonzero source modes. A
dense global eigensolve of W and the union of the four exact sector
eigensystems are therefore two coordinate representations of the same
finite spectrum.

For distinct single-mode coherent amplitudes, finite coherent-state sets are
linearly independent. This result is stated as Proposition 5.1 in
[Introduction to coherent quantization](https://link.springer.com/article/10.1007/s13324-022-00689-3).
It can also be seen directly from the first 256 Fock coefficients:

$$
F_{ni}=e^{-|\alpha_i|^2/2}\frac{\alpha_i^n}{\sqrt{n!}},
\qquad 0\le n<256.
$$

Their determinant is, up to a nonzero scalar,

$$
\det F\ \propto\ \prod_{i<j}(\alpha_j-\alpha_i).
$$

It is nonzero when the amplitudes are distinct. Therefore a positive
probability on every distinct state gives a mathematically positive-definite
W, even when its smallest eigenvalue is so small that ordinary arithmetic
cannot resolve it. This is the central distinction in the current blocker:
mathematical full support is not the same proposition as numerical
full-support resolution.

## 4. Exact C4 Fourier block diagonalization

Index the 256 states by an orbit representative k in {0,...,63} and a
rotation r in Z_4:

$$
\alpha_{k,r}=i^r z_k,
\qquad
p_{k,r}=\frac{q_k}{4}.
$$

Define the 64-by-64 weighted overlap matrices

$$
B_d[k,\ell]
=\sqrt{\frac{q_k}{4}\frac{q_\ell}{4}}\,
\langle z_k|i^d z_\ell\rangle,
\qquad d\in\mathbb Z_4.
$$

The phase covariance of coherent overlaps gives

$$
\langle i^r z_k|i^s z_\ell\rangle
=\langle z_k|i^{s-r}z_\ell\rangle.
$$

Consequently the full weighted Gram matrix has the block-circulant form

$$
W_{(k,r),(\ell,s)}=B_{s-r}[k,\ell].
$$

Let the four-point Fourier matrix be

$$
F_{r,a}=\frac{1}{2}i^{ar},
\qquad a,r\in\mathbb Z_4.
$$

Using F on the orbit coordinate and the identity on the representative
coordinate gives

$$
(\mathsf U^\ast W\mathsf U)_{a,b}
=\frac14\sum_{r,u=0}^{3}
i^{-ar}\,B_{u-r}\,i^{bu}.
$$

Set d=u-r. The sum over r is zero unless a=b. Therefore

$$
\mathsf U^\ast W\mathsf U
=\operatorname{diag}(X_0,X_1,X_2,X_3),
\qquad
X_a=\sum_{d=0}^{3}B_d\,i^{ad}.
$$

Because B_{-d}=B_d^\ast, each X_a is Hermitian in exact arithmetic. The
worker's

$$
G_a=\frac{X_a+X_a^\ast}{2}
$$

is the rounding-safe representation of that same exact sector. Thus

$$
\operatorname{spec}(W)
=\bigcup_{a=0}^{3}\operatorname{spec}(G_a),
$$

including multiplicity. This is an exact unitary equivalence, not an
approximation from a Fock cutoff.

### Nonuniform orbit-symmetric PS

The q_k need not be equal across the 64 representatives. The only required
condition is that the probability is constant along each C4 orbit:

$$
p_{k,0}=p_{k,1}=p_{k,2}=p_{k,3}=q_k/4.
$$

That condition leaves the factor sqrt(q_k q_l)/4 in B_d independent of the
rotation labels. The block-circulant relation and Fourier cancellation are
therefore unchanged for an arbitrary nonuniform q. The shaping changes the
64-by-64 block entries and their eigenvalues, but not the decomposition.

If probabilities differ within an orbit, if a representative-to-index map is
wrong, or if the amplitudes are not related by the stated phase action, the
off-block residual will expose the violation. This is why an independent
full-matrix transform is a stronger implementation audit than merely
re-running the worker's own sector constructor.

## 5. Required global invariants

For a direct full matrix W and its Fourier sectors W_a, record at least:

1. **Trace**

   $$
   \operatorname{tr}W=\sum_i p_i,
   \qquad
   \operatorname{tr}W=\sum_a\operatorname{tr}W_a.
   $$

2. **Hermiticity**

   $$
   r_H=\frac{\|W-W^\ast\|_F}{\max(1,\|W\|_F)}.
   $$

3. **Frobenius norm**

   $$
   \|W\|_F^2=\operatorname{tr}(W^2)
   =\sum_a\|W_a\|_F^2.
   $$

4. **Power traces**

   $$
   \operatorname{tr}(W^m)=\sum_a\operatorname{tr}(W_a^m),
   \qquad m=2
   $$

   at minimum, with m=3 optional when inexpensive. Power traces are
   invariant under the Fourier basis and do not require matching eigenvector
   columns.

5. **Block traces and positive-mode counts**, with the threshold explicitly
   recorded. A count at a precision-dependent threshold is a diagnostic, not
   a mathematical rank proof.

6. **Determinant or log-determinant**, when the matrix is already known to be
   positive and the calculation is cheap:

   $$
   \det W=\prod_a\det W_a,
   \qquad
   \log\det W=\sum_a\log\det W_a.
   $$

   This is a useful invariant but not a support certificate for a matrix
   whose determinant may be on the order of 10^-15000 or smaller.

The acceptance test should compare invariants against the input-normalization
residual. It must not demand an exact unit trace from the exact binary64
numbers if those numbers do not have an exact unit sum.

## 6. Off-block and block-match residuals

Let D be the block diagonal matrix made from four independently rebuilt
sectors, and let Y = U^\ast W U. Define the normalized off-block residual

$$
r_{\mathrm{off}}
=\frac{
\left\|Y-\operatorname{blockdiag}(Y_{00},Y_{11},Y_{22},Y_{33})\right\|_F
}{\max(\|W\|_F,\text{scale})}.
$$

The maximum off-diagonal block norm is also useful:

$$
r_{\mathrm{off},\max}
=\max_{a\ne b}
\frac{\|Y_{ab}\|_F}{\max(\|W\|_F,\text{scale})}.
$$

For each Fourier sector compare the transformed full matrix block with the
independently reconstructed production-form block:

$$
r_{\mathrm{blk},a}
=\frac{\|Y_{aa}-G_a^{\mathrm{ind}}\|_F}
{\max(\|Y_{aa}\|_F,\text{scale})}.
$$

Record the maximum relative Frobenius residual and a maximum-entry residual.
Use the same orbit order. If the two Fourier conventions use opposite signs,
align sector a with sector -a mod 4 before comparing. If representatives have
been permuted, compare after the explicit permutation P:

$$
Y_{aa}\ \longleftrightarrow\ P^\ast G_a^{\mathrm{ind}}P.
$$

Do not use arbitrary eigenvector matching. The matrix-level comparison is
well-defined even when eigenvalues cluster.

At d decimal digits, a reasonable structural target is residual stability
consistent with a working error scale near 10^{-(d-20)} for this 256-state
calculation, subject to the input roundoff and the actual multiprecision
implementation. The target is stability across two precision rows, not a
magic universal constant. The current 100-digit direct audit gives exactly
zero at the printed precision for the off-block and four sector residuals.

## 7. Spectrum comparison

For each low-precision row:

1. diagonalize the direct full W;
2. diagonalize the four independently rebuilt sectors;
3. sort the full eigenvalues and the concatenated sector eigenvalues;
4. compare absolute sorted differences;
5. compare logarithms only when both values lie above a declared resolution
   floor;
6. compare cumulative counts above thresholds;
7. compare power traces and Frobenius norms.

Near zero, relative error is meaningless. For a mode near 10^-600, a
small absolute perturbation can reverse its sign or change its apparent
relative value by many orders. The appropriate language is:

- resolved positive and stable at two successive rows;
- unresolved at the current precision;
- numerical floor or sign noise;
- mismatch with the independent block reconstruction.

For the bulk, use sorted L-infinity or Wasserstein-like matching after
sorting. For the extreme tail, compare threshold counts and logarithmic
clusters rather than individual eigenvalue labels. If eigenvalues cluster,
compare the invariant subspace or the cluster as a whole. Individual
eigenvectors are not a useful diagnostic for this question.

## 8. Precision requirements by purpose

| purpose | suggested decimal digits | what it can establish | what it cannot establish |
|---|---:|---|---|
| serialization/provenance | binary64 hex inputs, any AP working precision | exact replay of the frozen binary64 ensemble | physical uncertainty beyond the checkpoint |
| Hermiticity, trace, Fourier structure | 80–120 | block invariance, indexing, normalization residual, matrix-level agreement | positivity of modes near 10^-600 |
| independent global bulk check | 80, 120, 200 | global-versus-sector spectral union for resolved bulk and medium tail | full 256-mode support |
| diagnostic floor | about 300 | identifies the onset of unresolved near-zero modes and solver behavior | an exact positive minimum |
| all PS support modes | approximately 800–900 | current two-row PS full-support convergence | publication security by itself |
| all Full support modes | approximately 800–900 | current two-row Full full-support convergence | a reason to run a dense global eigensolve |
| 1000–1200 confirmation | current PS diagnostic ladder | stability margin for the resolved C,w row | a replacement for the frozen security protocol |

The smallest observed current PS mode is approximately 5.5e-598 and the Full
mode is approximately 1.0e-612. A rough first requirement is more than 600
decimal digits merely to represent the scale of the smallest mode. Inverse
operations and eigensolver error require guard digits; the observed 800/900
rows provide that margin. Precision should be chosen from the quantity being
certified, not from a blanket instruction to use 800 digits everywhere.

The inputs are serialized binary64. High-precision arithmetic therefore
resolves the deterministic frozen binary64 ensemble more accurately; it does
not create physical accuracy beyond the source checkpoint. That distinction
is desirable for a reproducible numerical gate, but it should be stated in
any publication or audit.

## 9. Dense versus sector cost

For cubic dense eigensolvers:

$$
\frac{256^3}{4\cdot64^3}=16.
$$

Thus one dense 256-by-256 all-eigenpair solve has about 16 times the leading
arithmetic work of four independent 64-by-64 all-eigenpair solves. Dense
Hermitian eigensolvers do not all have identical constants, so this is a
scaling ratio, not a wall-time prediction. The
[LAPACK working note on symmetric eigensolvers and Cholesky](https://www.netlib.org/lapack/lawnspdf/lawn135.pdf)
also records cubic complexity for both classes of dense operation.

For dense storage, a 256-by-256 matrix has 16 times the entries of one
64-by-64 sector, but four sectors together have 4 times fewer entries than
the full matrix. Therefore the full matrix uses approximately 4 times the
matrix/eigenvector storage of all four sectors, or 16 times the storage of
one sector. Arbitrary-precision object overhead can change the constants.

The measured sector-worker runtimes show why the asymptotic ratio matters:
the completed 800/900 sector pairs take roughly 10.6 minutes for PS and
17.9 minutes for Full under the current instrumented environment. A dense
high-precision run could therefore plausibly exceed an hour even before
additional allocation and multiprecision overhead. It must be benchmarked at
low precision before any high-precision launch; it must not be started
blindly from the 7-hour worst-case concern.

## 10. Backend and eigensolver assessment

### mpmath

The current worker uses mpmath and its complex-Hermitian eigensolver. The
official [mpmath documentation](https://mpmath.org/doc/current/mpmath.pdf)
documents eighe/eigh for complex Hermitian eigenproblems. It is convenient,
reproducible in the current repository, and already supports the sector
workflow. It is also relatively slow for a 256-by-256 matrix at hundreds of
decimal digits and does not provide rigorous interval enclosures. It remains
the appropriate current sector backend, not the preferred dense target
backend.

### Arb/FLINT

Arb represents real values by balls and complex values by rectangular complex
balls. The [FLINT acb_mat documentation](https://arblib.org/acb_mat.html)
distinguishes approximate QR eigenvalues, which carry no error guarantee,
from enclosure routines that provide rigorous bounds. Its global enclosure
can prove that all eigenvalues lie in a region, but the documentation warns
that one ball need not correspond to one eigenvalue; overlapping modes and
experimental eigensolver paths can prevent isolation. The routines are
therefore scientifically stronger for an independently certified
positive-half-plane or cluster statement, but they are not a reason to
execute the current dense target without a new hypothesis.

If a future reviewer requires a second high-precision implementation, Arb
or FLINT with acb_mat balls is the best independent scientific option. It
should be used to enclose the Hermitian spectrum or certify clusters, not
presented as a magical individual-eigenvalue oracle. The current virtual
environment does not have the Python flint binding installed.

### MPFR/MPC

MPFR provides arbitrary-precision binary floating point with specified
rounding semantics; see the [official MPFR documentation](https://www.mpfr.org/mpfr-current/).
An MPFR/MPC C++ backend would likely be faster and more controllable than
pure-Python mpmath, but point arithmetic alone supplies no eigenvalue
enclosures. It is a new backend project and is unnecessary for the present
decision.

### Mathematica

Wolfram's [Eigensystem documentation](https://reference.wolfram.com/language/ref/Eigensystem.html)
supports arbitrary-precision matrices and an Arnoldi method. The
[WorkingPrecision documentation](https://reference.wolfram.com/language/ref/WorkingPrecision.html)
warns that low-precision inputs limit the useful precision of the result and
that runtime can increase substantially with working precision. Mathematica
is a convenient one-off independent check if licensed, but it does not
remove the need to bind exact inputs, record precision, and save residuals.

### Julia/BigFloat

Julia's [BigFloat documentation](https://docs.julialang.org/en/v1/base/numbers/)
uses MPFR-backed arbitrary-precision numbers, and
[LinearAlgebra](https://docs.julialang.org/en/v1/stdlib/LinearAlgebra/)
provides eigen, determinant, trace, and positive-definiteness operations.
Julia is a good engineering environment for a fresh point-arithmetic
replication, but it introduces a new environment and does not by itself
provide Arb-style rigorous eigenvalue balls. It is not needed for the
smallest sufficient audit.

## 11. Cholesky, logdet, and extremal alternatives

### Cholesky

For an exact positive-definite W, an exact Cholesky factor exists. An AP
Cholesky factorization with all positive pivots is a useful, relatively cheap
support sanity check. It is not equivalent to computing the eigenvalues:
the pivots depend on row/column ordering and can differ greatly from the
smallest eigenvalue. A finite-precision pivot failure can be numerical, and
successful pivots do not certify the accuracy of the smallest eigenvalue.
Use Cholesky as an auxiliary cross-check, never as the sole replacement for
the sector convergence rows.

### Determinant and logdet

The determinant factorization across sectors is an exact invariant. A
high-precision logdet computed from Cholesky diagonals can detect gross
block or input mismatches without multiplying numbers as small as
10^-15000. It remains sensitive to every small mode and cannot prove that
the smallest mode is positive. It is a consistency check, not a full-support
certificate.

### Extremal or iterative eigensolvers

Lanczos, Arnoldi, or shift-invert methods can target a small spectral region.
They are most attractive for large sparse matrices; Wolfram's documentation
describes Arnoldi as especially useful for large sparse problems. The current
matrix is dense and only 256 by 256, while the modes of interest are
extremely clustered near zero. Loss of orthogonality, cluster resolution, and
the high-precision solves required by shift-invert reduce the expected
benefit. The [Netlib spectrum-slicing discussion](https://www.netlib.org/utk/people/JackDongarra/PAPERS/eigen-improve-ijhpca-2024.pdf)
supports selective eigenspectrum methods when only a thin slice is needed,
but this project needs a support decision across all 256 modes. The existing
four 64-by-64 full sector solves are simpler and better aligned with the
symmetry proof.

## 12. Smallest PS-versus-Full numerical plan

Do not optimize or change either model family. Use only the frozen median
inputs already captured by the localization artifact:

- PS+V_A checkpoint:
  repaired_full_z_checkpoint_ps_va_20260911_step_50.pt,
  SHA-256 1c5d49d1a562c558a18a76994399b09c4bee88ddbebf35370ae9cb690e3ca8d1.
- Full checkpoint:
  repaired_full_z_checkpoint_full_20260911_step_50.pt,
  SHA-256 9e5bf3fb8534cbf2640ca0feb99810518c110c283931d701c44ee52e16622e51.

For each case and each of 80, 120, and 200 decimal digits:

1. rebuild all 256 amplitudes and per-symbol probabilities from the stored
   binary64 hexadecimal values;
2. form the direct 256-by-256 W without calling the worker's sector builder;
3. compute trace, Hermiticity, Frobenius norm, tr(W^2), and the serialized
   normalization residual;
4. transform W with the explicit 4-point Fourier matrix;
5. record normalized off-block and block-match residuals;
6. diagonalize W and the four independent blocks at this low precision;
7. compare the sorted global spectrum with the union of sector spectra above
   the declared precision floor;
8. compare against the current worker's sector rows where the precision
   overlaps;
9. save all inputs, hashes, timings, thresholds, unresolved-mode flags, and
   no-security-result scope.

The 100-digit structural row already exists. The proposed 80/120/200 ladder
is the smallest reproducibility extension that tests stability rather than
relying on one arbitrary precision.

## 13. GO/STOP criteria

### Low-precision audit GO

The bounded low-precision audit is justified now because it tests an
independent end-to-end implementation path at a fraction of the high
support cost. It has a total wall-time budget of 15 minutes. If the full
PS-plus-Full matrix audit exceeds that budget, stop and retain the partial
artifact; do not increase precision to recover a low-priority bulk check.

### High dense-global GO

A future dense high-precision global run may be considered only if all of the
following become true:

1. the independent low-precision direct matrix, Fourier transform,
   off-block residual, block match, and bulk spectrum union show a
   reproducible mismatch that the sectors cannot explain; or a specific
   external audit/reviewer requirement demands the global artifact;
2. the mismatch identifies a new hypothesis that the dense run can test;
3. a low-precision timing pilot projects no more than one hour for the
   required high-precision row;
4. exact input hashes, source hash, backend version, precision, and
   termination criteria are fixed before launch;
5. the run is separately authorized as a read-only diagnostic.

If such a run is ever authorized, use a two-hour hard wall-time stop for one
256-by-256 matrix. Save a partial diagnostic on timeout; never convert a
timeout or a nonconverged row into a support result. Arb/FLINT ball
arithmetic is preferable for an independent certification attempt; mpmath
remains adequate for an approximation-only replication.

### Current STOP

The current evidence satisfies the scientific need without the dense high
run: the exact algebra forces the global/sector spectrum identity, the
independent direct matrix reproduces the C4 structure at 100 digits, and
the current sector worker has successive high-precision full-support rows
for both PS and Full. A dense 800–900-digit global eigensolve would repeat
information already determined by the sector calculations. Do not execute it
under this memo.

## 14. Interpretation of the four AP outcomes

### INSUFFICIENT_AP_PRECISION

Choose this when the independent direct matrix and current worker agree
after a higher precision ladder, while the earlier lower ladder reports
unresolved or negative numerical-floor modes. This is the current
classification. It says the earlier attempt did not supply enough
resolution or reproducible run evidence; it does not authorize changing the
model.

### AP_WORKER_PS_SPECIFIC_BUG

Choose this only if independently rebuilt PS matrices or sectors disagree
with the worker at the same serialized inputs and adequate precision, while
the matched Full positive control agrees. A nonzero block-match residual or
PS-only C/w mismatch would be required.

### AP_FAIL_GATE_BUG

Choose this only if the independent high-precision spectrum and inverse
quantities pass the declared support criteria, but the worker rejects the
same rows because of an incorrect rank, positivity, or tolerance decision.
The current worker's accepted 800/900 rows do not support this label.

### UNRESOLVED_AP_FAILURE

Retain this only if the independent path and the current worker continue to
disagree, or neither precision ladder reaches a stable row within the
declared budget. The current high-control rows move the project out of this
category for the median diagnostic, although they do not settle the
three-state adaptive ranking.

## 15. Why the three dense-check classifications differ

The three decision labels answer a different question from the four AP
blocker labels:

- **DENSE_GLOBAL_HIGH_PRECISION_REQUIRED** would mean that the sector proof
  or independent block audit leaves a scientifically material ambiguity that
  only the dense high spectrum can resolve. Current evidence does not meet
  that condition.
- **LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT** means that
  the low global calculation is useful as an independent integration check,
  while the extreme support modes are certified numerically by converged
  high-precision sectors. This is the current decision.
- **DENSE_GLOBAL_CHECK_NOT_USEFUL** would mean that even a bounded low global
  calculation adds no meaningful audit value. That is too strong: a
  lower-precision direct global spectrum is still a useful independent
  check of ordering, indexing, and the spectrum union.

## 16. Anti-overengineering boundary

Stop the investigation after the following four conditions pass:

1. the exact C4 unitary equivalence is documented;
2. the direct full W has stable trace/Hermiticity/power invariants and a
   negligible stable off-block residual;
3. the low global spectrum agrees with the union of independently rebuilt
   sectors over its resolved range;
4. each candidate requiring inverse-sensitive source moments has two
   successive high-precision sector rows with full support, stable C,w, and
   recorded provenance.

At that point a dense high-precision global eigensolve is linear-algebra
duplication, not additional evidence about the security source spectrum. It
should be reopened only for a surviving matrix/block mismatch, a
provenance/indexing discrepancy, or an explicit external audit requirement.
Do not build a new backend, add a model guard, or create an iterative
eigensolver merely to make the numerical workflow look more elaborate.

## 17. Final classification and exact next action

Final dense-check classification, exactly one:

**LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT**

Immediate AP-blocker classification, exactly one:

**INSUFFICIENT_AP_PRECISION**

Exact next numerical task, not executed in this research-only memo:

**RUN_INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT** — direct 256-state
weighted-Gram construction for frozen median PS+V_A and Full at 80/120/200
decimal digits; compute Fourier off-block residuals, block matches, trace,
Frobenius norm, tr(W^2), and resolved bulk spectrum-union comparisons; stop
at 15 minutes total; save diagnostics only; do not run the dense
700–900-digit target.

Lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and
NOT_READY_FOR_ADAPTIVE_TRAINING. No security, novelty, publication, or
adaptive-ranking claim follows from this memo.

## Sources

1. Coherent-state finite linear independence:
   [Introduction to coherent quantization, Proposition 5.1](https://link.springer.com/article/10.1007/s13324-022-00689-3).
2. Arbitrary-precision Hermitian eigensolvers:
   [mpmath documentation, eighe/eigh](https://mpmath.org/doc/current/mpmath.pdf).
3. Rigorous and approximate complex matrix eigenvalue routines:
   [Arb/FLINT acb_mat documentation](https://arblib.org/acb_mat.html).
4. Correctly rounded arbitrary-precision binary floating point:
   [GNU MPFR documentation](https://www.mpfr.org/mpfr-current/).
5. Arbitrary-precision and Arnoldi matrix eigensystems:
   [Wolfram Eigensystem](https://reference.wolfram.com/language/ref/Eigensystem.html).
6. Working precision and input-precision limitations:
   [Wolfram WorkingPrecision](https://reference.wolfram.com/language/ref/WorkingPrecision.html).
7. MPFR-backed arbitrary precision in Julia:
   [Julia numbers and BigFloat](https://docs.julialang.org/en/v1/base/numbers/).
8. Julia dense linear algebra:
   [Julia LinearAlgebra](https://docs.julialang.org/en/v1/stdlib/LinearAlgebra/).
9. Dense Cholesky/eigensolver cubic complexity:
   [LAPACK Working Note 135](https://www.netlib.org/lapack/lawnspdf/lawn135.pdf).
10. Selective eigenvalue computation and cubic dense scaling:
    [Numerical eigen-spectrum slicing](https://www.netlib.org/utk/people/JackDongarra/PAPERS/eigen-improve-ijhpca-2024.pdf).
