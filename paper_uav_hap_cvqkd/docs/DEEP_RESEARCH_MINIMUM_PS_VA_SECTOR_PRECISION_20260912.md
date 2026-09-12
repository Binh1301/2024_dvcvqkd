# Deep research: minimum sector precision for the frozen PS+V_A source moments

Date: 2026-09-12  
Status: **research-only decision; no expensive computation executed**

## Executive decision

The remaining numerical blocker is best handled by the following single
category:

```text
DIRECT_HIGHER_PRECISION_SECTOR_RUN
```

The recommended starting precision for the next fixed sector ladder is
**1050 decimal digits**. The acceptance rows are then 1250 and 1450 digits.
This recommendation does not amend the repository's frozen
`1050,1250,1450` ladder or its acceptance rule. It selects the existing first
ladder rung because the current PS minimum mode is around `10^-597`, 1050
digits leaves a very large nominal guard margin, and the lower 800--1200-digit
diagnostic rows already indicate that no 1600/2000-digit jump is warranted.

The cheapest *point-estimate* experiment could stop earlier, because the
current PS median has already resolved at 800/900 and 1000/1200 digits. That is
not the same as the cheapest defensible **authoritative** result under the
current project protocol. An outcome-driven sector-by-sector precision ladder
would require a protocol change and would be unsafe to introduce implicitly:
the frozen C4 backend protocol forbids outcome-based precision changes.

No dense 256-by-256 high-precision eigensolve, new arbitrary-precision
worker run, full-Z security evaluation, training, final-test access, or code
change was performed for this memo. The proposed next run remains a bounded,
read-only evaluation of one frozen optimized PS+V_A checkpoint followed by
one median full-Z point.

## 1. Scope and questions answered

This memo addresses only the current source-moment blocker:

\[
\tau=\sum_{k=1}^{256}p_k\lvert\alpha_k\rangle\langle\alpha_k\rvert,
\qquad
C=\operatorname{Tr}(\sqrt{\tau}\,a\sqrt{\tau}\,a^\dagger),
\]

and the corresponding full-support non-Gaussian penalty `w` used by the
existing C4 sector worker. It does not redesign the security model, alter the
PS family, add a probability floor, change `V_A`, revisit the settled dense
global-spectrum question, or authorize publication-scale work.

The investigation covers:

1. the precision needed when the smallest weighted-Gram eigenvalue is around
   `10^-597`;
2. probability and modulation-energy effects on that spectrum;
3. analytic support versus numerical support resolution;
4. alternatives to explicit sector eigendecomposition;
5. propagation of `C,w` uncertainty into `Z` and `K_raw`;
6. the six candidate strategies requested by the project brief; and
7. one bounded, reproducible next-run specification.

Statements below are labelled implicitly by their source: repository facts are
marked as evidence, mathematical steps are derivations, and scaling or
runtime statements are engineering estimates rather than theorems.

## 2. Frozen mathematical object and current worker

For a C4 constellation, the weighted coherent-state Gram matrix is

\[
W_{ij}=\sqrt{p_i p_j}\,
\exp\left[-\frac{|\alpha_i|^2+|\alpha_j|^2}{2}
 +\alpha_i^*\alpha_j\right].
\]

The fourfold orbit makes `W` block diagonal under the exact four-point
Fourier transform. The current worker therefore constructs four Hermitian
64-by-64 sectors `G_s`, diagonalizes each as

\[
G_s=U_s\Lambda_sU_s^\dagger,
\]

and evaluates the full-support source moments using square roots,
inverse-square roots, and factorized solves. It does not use an eigenvalue
threshold in the full-support path.

The worker's current residual form for `w` is important. With

\[
M_s=U_s^\dagger D U_{s-1},
\qquad D=\operatorname{diag}(z_k),
\]

the worker forms the sector transition matrices using factorized solves and
computes `w` as a weighted sum of squared residual norms. This is preferable
to subtracting two nearly equal large terms, but it does not remove the need
to resolve the small spectral modes: the solves contain inverse square roots
of the sector eigenvalues.

The security-theory origin of the chain is the arbitrary-modulation
coherent-state analysis of Denys, Brown, and Leverrier. Their construction
uses the square-root similarity transform of the source state, expresses the
source uncertainty through `C` and `w`, and obtains the two-sided source
correlation interval used here. The cited work is asymptotic and collective-
attack scoped; the repository deliberately does not promote the current
fading average to a broader security claim. See [1] and [2].

## 3. Evidence already available

The following are the relevant frozen-input observations; they are not rerun
by this memo.

| Item | Existing evidence | Interpretation |
|---|---|---|
| Uniform Case A | `C=0.85985110654649868138...`, `w=0.01832761047496350205...`; `lambda_min` about `3.9730e-618` | High-precision reference for the earlier uniform case |
| PS median, 800/900 digits | `C=0.86108130075524289091...`; `w=0.0067220381757562110711...`; `lambda_min=5.5183273131200776e-598`; rank 256 | Full-support diagnostic convergence |
| PS median, 1000/1200 digits | Same displayed `C,w,lambda_min` values and rank 256 | Independent higher ladder confirms the diagnostic row |
| Full median, 800/900 digits | `C=0.85942389567118688994...`; `w=0.01304478148295807424...`; `lambda_min=1.0195494813436373e-612`; rank 256 | Matched control also passes the high-precision sector worker |
| PS localization at 300 digits | Sector positive counts `[52,53,53,52]`, total rank 210; negative tail around `10^-302`; reconstruction residuals around `10^-300` | The 300-digit row is a precision floor, not a physical rank result |
| Independent global audit | PS at 80 digits resolved 48 bulk modes and matched the C4 sector union; 120 digits timed out; global high precision was not run | Structural block evidence only; not a support certificate |

The PS minimum eigenvalue gives

\[
L=-\log_{10}(\lambda_{\min})\simeq 597.2582.
\]

The Full control has `L` about `611.9916`, so the fact that it passes at the
same tested ladder is not explained by Full having a larger smallest
eigenvalue. The current evidence supports the existing worker and C4
reduction; it does not support a PS-specific worker bug.

The principal local artifacts are:

- [`results/ps_va_worker_instrumented_800_900_20260912.json`](../results/ps_va_worker_instrumented_800_900_20260912.json), SHA-256
  `3d7dc1024f022a5a4b1121fc6ce98c5c618e6abe46c91b7adcf662c4a75e43a6`;
- [`results/ps_va_worker_instrumented_1000_1200_20260912.json`](../results/ps_va_worker_instrumented_1000_1200_20260912.json), SHA-256
  `649ff8f2a1a8022d4eef6afa1f6be2b003e34818291a89b1bde01c28a6c927dd`;
- [`results/full_worker_instrumented_800_900_20260912.json`](../results/full_worker_instrumented_800_900_20260912.json), SHA-256
  `08510463a9a57c1e002129805e6f2f25c5dbf216258614623d7467650bb90bde`;
- [`results/ps_va_ap_worker_localization_20260912.json`](../results/ps_va_ap_worker_localization_20260912.json), SHA-256
  `b068f2fc5a83d9acf269cff532e1f3cf218c640319b3a26bd6c4cea5876e7908`;
- [`docs/FULL_SUPPORT_C4_GRAM_BACKEND_PROTOCOL.md`](FULL_SUPPORT_C4_GRAM_BACKEND_PROTOCOL.md); and
- [`docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`](NUMERICAL_CONVERGENCE_PREREGISTRATION.md).

## 4. Precision theory for a `10^-L` smallest eigenvalue

### 4.1 Eigenvalue sign resolution

Let `p` be decimal working precision and suppose the sector eigensolver has a
backward or reconstruction error scale `eta`. For a normalized Gram matrix
whose largest eigenvalue is of order one, a useful engineering model is

\[
\eta\approx c(n,\text{algorithm})10^{-p},
\]

where `c` includes matrix dimension, arithmetic guard loss, and the
conditioning of the algorithm. To distinguish a positive smallest mode from
zero or a roundoff artifact, the meaningful condition is

\[
\eta\ll\lambda_{\min}=10^{-L},
\]

not merely `sqrt(eta) << lambda_min`. Thus the working precision needs roughly

\[
p\gtrsim L+g,
\]

where `g` is a guard margin in decimal digits. This is a sign/backward-error
condition. It is not a proof of correct rounding, particularly because
high-level multiprecision linear algebra does not generally carry a blanket
correct-rounding guarantee. The mpmath documentation explicitly recommends
extra working precision and independent checks for such calculations; see
[3].

For the current PS value, the nominal guard above the eigenvalue exponent is:

| Working digits | Nominal digits above `L=597.26` | Meaning |
|---:|---:|---|
| 700 | 103 | Theoretical first probe if the error model is benign |
| 800 | 203 | Already observed to resolve the current target |
| 1000 | 403 | Existing diagnostic row |
| 1200 | 603 | Existing diagnostic confirmation row |
| 1250 | 653 | Frozen acceptance-grade reference row |
| 1450 | 853 | Frozen successive confirmation row |
| 1600 | 1003 | No present evidence justifying this cost |
| 2000 | 1403 | No present evidence justifying this cost |

The distinction between 800 and 1050 is therefore procedural and evidentiary,
not a claim that the current PS eigenvalue mathematically requires 1050
digits. At 800 digits the existing pair already leaves about 203 nominal
digits after the `10^-597` scale. The reason to retain 1250/1450 as the
selected pair is that the repository's frozen full-support protocol selected
those rows after an earlier near-coincident stress analysis, and current
diagnostic rows have not yet been rebound as the authoritative selected row.
The 1050 row is a fixed non-acceptance probe, not an outcome-driven decision
point.

### 4.2 Square roots and inverse square roots

For a scalar positive eigenvalue `lambda`, the relative condition numbers of
`sqrt(lambda)` and `lambda^(-1/2)` with respect to a relative perturbation in
`lambda` are both one half. Consequently, once `lambda` itself is known to a
given number of relative digits, the scalar square root does not consume half
of the available decimal precision.

The dangerous issue is not representing `sqrt(lambda)` (which is about
`10^-298.63` here); it is finding `lambda` and using its inverse in a solve.
An absolute perturbation `delta lambda` creates a relative inverse-square-root
error of approximately

\[
\frac{|\delta(\lambda^{-1/2})|}{\lambda^{-1/2}}
\simeq \frac{|\delta\lambda|}{2\lambda}.
\]

If the input perturbation is at the ordinary `10^-p` scale, the ratio
`delta lambda/lambda` costs approximately `L` digits. This is why the required
precision is governed by `L`, not `L/2`.

The current worker uses two triangular/multi-right-hand-side solves involving
the diagonal inverse square-root factors. A stable factorization reduces
avoidable error, but it cannot make an unresolved physical mode irrelevant.
The final acceptance test must therefore be on `C,w` and downstream observables,
not only on the printed eigenvalue.

### 4.3 Guard-digit recommendation

For this target, 100 decimal guard digits above an estimated spectral exponent
is a reasonable minimum engineering margin. Two adjacent rows and explicit
residual/invariant checks are required because mpmath is not an interval
certificate. The existing 800/900 and 1000/1200 pairs supply stronger
diagnostic evidence than the 100-digit rule alone. A 200-digit guard is a
reasonable stress fallback, not a reason to jump automatically to 1600 or
2000 digits.

## 5. Weighted-Gram lower bound and probability effects

Let `G` be the unweighted normalized coherent-state Gram matrix and
`P=diag(p_1,...,p_M)`. The weighted Gram is

\[
W=P^{1/2}GP^{1/2}.
\]

For every unit vector `x`,

\[
\begin{aligned}
x^\dagger W x
  &=(P^{1/2}x)^\dagger G(P^{1/2}x)\\
  &\geq \lambda_{\min}(G)\|P^{1/2}x\|^2\\
  &\geq \lambda_{\min}(G)p_{\min}\|x\|^2.
\end{aligned}
\]

Taking the minimum over unit `x` proves

\[
\boxed{\lambda_{\min}(W)\geq p_{\min}\lambda_{\min}(G)}.
\]

For the same geometry and uniform probability `p_u=1/256`, the corresponding
comparison is

\[
\lambda_{\min}(W_p)\geq
\frac{p_{\min}}{p_u}\lambda_{\min}(W_u).
\]

The current PS median has

\[
\frac{p_{\min}}{p_u}\simeq0.505529587,
\qquad
-\log_{10}(0.505529587)\simeq0.2961,
\]

and the Full median has

\[
\frac{p_{\min}}{p_u}\simeq0.821794020,
\qquad
-\log_{10}(0.821794020)\simeq0.0852.
\]

Thus PS probability weighting can cost at most about 0.30 decimal orders in
this lower-bound comparison relative to uniform, assuming the geometry is
held fixed. It cannot explain a several-hundred-order support difficulty. The
bound is only a lower bound: the actual smallest eigenvalue also depends on
the full geometry and on how the probability diagonal interacts with its
near-null directions. It should not be used to predict the actual PS/Full
ordering.

## 6. What `V_A` can and cannot do to the spectrum

For fixed normalized constellation shape, write `alpha_k=t u_k`, where the
amplitude scale `t` is proportional to `sqrt(V_A)`. The Gram entries are
analytic functions of `t`. For `M` distinct one-mode coherent states, the
first `M` Fock coefficients contain a Vandermonde matrix in the amplitudes:

\[
\left[u_k^n\right]_{n=0}^{M-1},
\]

whose determinant is nonzero when the `u_k` are distinct. In the small-scale
limit, the generic singular-value hierarchy of the synthesis matrix behaves
like `t^0,t^1,...,t^(M-1)`. The corresponding Gram eigenvalues therefore
behave heuristically like

\[
\lambda_j(W)\sim t^{2j},
\qquad
\lambda_{\min}(W)\sim t^{2(M-1)}=t^{510}
\sim V_A^{255}.
\]

This is a small-amplitude asymptotic estimate, not a global law at the current
operating point. It gives a useful scale check. A multiplicative change
`V_A -> gamma V_A` changes the asymptotic decimal exponent by approximately
`255 log10(gamma)`:

| Change in `V_A` | Approximate change in `log10(lambda_min)` |
|---:|---:|
| `gamma=0.9` | `-11.7` orders |
| `gamma=0.8` | `-24.7` orders |
| `gamma=0.5` | `-76.8` orders |
| `gamma` about `0.164` | `-200` orders |
| `gamma` about `0.0666` | `-300` orders |

Therefore a modest change in `V_A` does not normally move the current
smallest mode by hundreds of orders. Such a change is possible near a
geometric collision or a special cancellation, where a two-state eigenvalue
can scale as the squared displacement. The current minimum pair distances
are useful diagnostics but do not determine the smallest 256-state eigenvalue.
`V_A` also changes `C`, `w`, and the post-action excess noise, so a security
comparison must not attribute a `K` change to support conditioning alone.

## 7. Why Full can pass while PS fails

There is no contradiction in a Full control passing a worker row while PS
fails at a lower row, even if the Full global minimum is eventually smaller.
The following effects are sufficient:

- each C4 sector distributes its near-null modes differently;
- the eigensolver's absolute residual and sign decisions are sector dependent;
- solve conditioning depends on the particular eigenvectors and transition
  matrices, not only on the global minimum;
- `C` and `w` are sums of terms with cancellations and residuals, so a scalar
  result can be stable before every displayed eigenvalue is visually stable;
- the PS and Full geometries have different mode gaps and different overlaps,
  even when their probability ranges are similar.

The existing data show that the Full row is a useful positive control, not a
conditioning theorem. The correct conclusion is that the unchanged worker
has a reproducible high-precision path for both cases. It is not valid to
infer that Full is intrinsically easier or that PS has a distinct numerical
bug from a single lower-precision pass/fail boundary.

## 8. Analytic coherent-state support versus numerical support

The analytic support result is stronger than a numerical rank count. Suppose
the 256 amplitudes are distinct and all probabilities are positive. If

\[
\sum_{k=1}^{M}c_k\lvert\alpha_k\rangle=0,
\]

then the Fock coefficient at photon number `n` gives

\[
\sum_{k=1}^{M}
c_k e^{-|\alpha_k|^2/2}\alpha_k^n=0.
\]

Taking `n=0,...,M-1` produces a Vandermonde system. Distinct amplitudes make
its determinant nonzero, so every coefficient is zero. Hence every finite set
of distinct canonical coherent states is linearly independent, and the
positive-probability mixture has mathematical rank `M=256`. This theorem is
also stated in the arbitrary-modulation source analysis; see [1] and [4].

This proves support, not numerical safety. The operator `tau^(-1/2)` is very
large on a `10^-597` mode. A numerical algorithm can therefore fail to
represent a mathematically positive state even though the state has no exact
zero eigenvalue. The theorem does not bound the condition number, the error in
`C,w`, or the security functional.

The current numerical full-support gate must remain fail-closed. A future
protocol could combine the analytic rank theorem with exact distinctness,
positive probabilities, matrix residuals, and a source-moment convergence
gate, but simply replacing `rank==256` with an analytic assertion would hide
the inverse-square-root error that the gate is meant to expose.

## 9. Must all 256 eigenvalues be numerically resolved?

There are three different meanings of “resolve all modes.”

1. **Mathematical support:** no numerical eigenvalue list is needed. The
   Vandermonde argument establishes rank 256 from the frozen input.
2. **Current spectral implementation:** yes, every sector eigenvalue and
   eigenvector is used by the current formula. A thresholded or suppressed
   mode changes the full-support functional.
3. **A different matrix-function implementation:** not necessarily. A
   certified action of `G_s^(1/2)` and `G_s^(-1/2)` on the required transition
   vectors could avoid printing or explicitly storing all eigenpairs. It must
   still bound the action error on the tiny-eigenvalue subspace.

Thus the publication artifact need not print 256 eigenvalues to fifty digits.
It must record the support argument, frozen inputs, matrix/function residuals,
and convergence of `C,w,Z,chi_BE,K_raw`. A numerical support threshold is not
an acceptable substitute for the full-support target.

## 10. Conditioning of the source moments

Matrix square-root sensitivity is governed by the Fréchet derivative of the
matrix function. In general, the derivative of the inverse square root grows
as the spectrum approaches zero. Higham's matrix-function treatment describes
this conditioning framework and the distinct stability questions for square
root algorithms; see [5] and [6].

For the present worker, a conservative interpretation is:

- the sector eigensolver must provide a small reconstruction/backward residual;
- the smallest mode must be separated from that residual by a large margin;
- square-root and inverse-square-root factors must be formed at the same
  working precision as the eigenvalues;
- the solve residuals must be recorded, not inferred from the final scalar;
- the final scalar `C,w` must agree at adjacent accepted precisions; and
- the downstream full-Z calculation must pass its own convergence gate.

The residual-form `w` calculation is numerically preferable because it
preserves nonnegativity as a sum of squared residual norms. It is not a proof
that an insufficiently resolved support produces the correct residual vectors.

## 11. Alternatives to explicit eigendecomposition

### 11.1 Cholesky

For a positive definite sector, Cholesky gives `G_s=L_sL_s^\dagger` and is a
good positivity and solve diagnostic. It is not the principal matrix square
root in general. Replacing `sqrt(G_s)` and `G_s^(-1/2)` by `L_s` would change
the formula unless a separate algebraic derivation establishes equivalence.
Cholesky also becomes difficult to certify when the computed pivot is near
the precision floor. It can accelerate a reformulated solve, but it is not a
precision escape hatch.

### 11.2 QR, polar, and coherent-state synthesis factors

Let `V` have columns `sqrt(p_k)|alpha_k>`, so `W=V^\dagger V`. A QR or polar
factorization can expose the same support and may be useful for an independent
implementation. However, the triangular factor inherits the near dependence
of the coherent states. Computing the source operator in that basis still
requires a solve or inverse associated with the small singular values. QR can
change error constants and memory traffic, but not remove the underlying
condition number.

### 11.3 Matrix-function actions and Krylov methods

Rational approximations, contour methods, Newton-type iterations, or Krylov
actions can avoid materializing a full square-root matrix. For a required
vector action, this may be attractive once a reliable error estimator is
available. For an inverse square root with `lambda_min` around `10^-597`, an
unresolved component in the corresponding eigenspace is still amplified by
about `10^298.6` in norm. The iteration count or storage can improve without
removing the need for accurate spectral information.

These methods are not the cheapest next step because the current C4 worker is
already algebraically validated and has passed adjacent high-precision rows.
They should be considered only if the frozen sector run fails its scalar or
residual gate.

## 12. mpmath and Arb/FLINT options

mpmath uses a global working precision rather than attaching independent
precision metadata to each number. Basic arithmetic is designed to round at
the working precision, but high-level matrix algorithms require user-supplied
guard precision and post hoc validation. Its Hermitian eigensolvers and
Cholesky routines are useful for the current 64-by-64 sectors; they are not a
rigorous interval certificate. See [3].

Arb/acb provides ball arithmetic and can enclose scalar and matrix operations.
Its matrix documentation includes rigorous eigenvalue-enclosure machinery,
but also warns that overlapping eigenvalue clusters and dependency
overestimation can make enclosures wide or expensive. Approximate QR routines
are not equivalent to a rigorous global enclosure. See [7] and [8].

Arb is therefore a strong independent reference or interval backend if the
point calculation cannot be made reproducible. It is not the cheapest first
move for one already-converged PS median, and introducing it now would add a
new backend without evidence that the current fixed sector worker fails.

## 13. Runtime scaling and what not to run

The dominant work is four 64-by-64 eigensystems plus the subsequent dense
sector solves. At fixed dimension, multiprecision cost grows with digit count;
the exponent depends on multiplication algorithms, eigensolver iterations,
conditioning, and Python object overhead. It should not be extrapolated as
linear in decimal digits.

For the PS worker, the existing pair runtimes are approximately:

| Pair | Total seconds | Mean seconds/row |
|---|---:|---:|
| 800/900 | `633.775` | `316.9` |
| 1000/1200 | `1056.824` | `528.4` |

A deliberately crude fit to these two points gives a digit exponent near
`1.98`. It predicts roughly 11.3 minutes for one 1250-digit PS row and 15.2
minutes for one 1450-digit row. These are planning estimates, not guarantees;
the Full control's 800/900 pair took about 17.9 minutes and demonstrates that
conditioning and implementation details matter. No 1600- or 2000-digit run
is justified by the current evidence.

The frozen near-coincident protocol is the relevant higher-precision prior:
its 1250/1450 pair was selected after a stress spectrum around `10^-1099`.
The present PS median is less extreme (`10^-597`), and its 800/900 and
1000/1200 results already pass diagnostically. The fixed 1050/1250/1450
ladder recommendation is therefore a protocol-compliance and provenance
decision, not a claim that the current candidate needs 1450 digits for
floating-point sign resolution.

## 14. Why an adaptive sector ladder is not selected now

Sector-specific precision is mathematically plausible, but the current
authoritative path has two obstacles:

1. the frozen protocol explicitly forbids outcome-based precision changes; and
2. `w` is assembled from cross-sector transition matrices and residual
   vectors, so a mixed-precision point estimate needs an explicit error budget
   before sector contributions can be combined defensibly.

It would be safe to use sector-specific scouting in a future protocol if each
sector produced a validated contribution enclosure and the final aggregation
was performed at a common precision or with a proved global error budget. It
is not safe to silently promote only sectors that look difficult and call the
mixed result authoritative under the current manifest.

This is why `ADAPTIVE_SECTOR_PRECISION` is ranked second below, even though it
could be cheaper in a new protocol. The selected category is the fixed,
already-frozen higher-precision sector run.

## 15. Propagation from `C,w` to `Z`

For fixed positive `T` and `epsilon_total`, the source endpoints are

\[
Z_\pm=2\sqrt{T}\,C\pm\sqrt{2T\epsilon_{\mathrm{total}}w}.
\]

The first-order absolute perturbation bound is

\[
|\delta Z_\pm|
\lesssim 2\sqrt{T}|\delta C|
 +\sqrt{\frac{T\epsilon_{\mathrm{total}}}{2w}}|\delta w|.
\]

For the frozen PS median values, the two coefficients are approximately

\[
2\sqrt{T}=0.2978708672,
\qquad
\sqrt{\frac{T\epsilon_{\mathrm{total}}}{2w}}=0.1828014441.
\]

This makes `w` important but not catastrophically amplified at this point.
The current preregistered source-moment tolerance
`1e-7 + 1e-6*|reference|` would correspond, at this point, to an endpoint
movement of order `10^-7` before the Holevo maximization. The downstream
`chi_BE`/instantaneous-`K` tolerance is the tighter practical gate:
`1e-6 bit + 1e-5*|reference|`.

For an interval enclosure `C in [C_-,C_+]` and `w in [w_-,w_+]`, with
`w_->=0`, a simple conservative enclosure for the whole source interval is

\[
\left[
2\sqrt{T}C_- - \sqrt{2T\epsilon w_+},
\quad
2\sqrt{T}C_+ + \sqrt{2T\epsilon w_+}
\right].
\]

The tighter endpoint-specific bounds use `w_+` for the lower endpoint and
`w_-` for its upper counterpart. The resulting interval must then be
intersected with the frozen physical covariance domain. This is a conservative
numerical enclosure, not an excuse to evaluate an unphysical `Z` value.

## 16. Propagation from `Z` to `K_raw`

The implemented ordering is

\[
\tau\longrightarrow(C,w)\longrightarrow[Z_-,Z_+]
\longrightarrow\max_Z\chi_{BE}(Z)\longrightarrow
K_{\mathrm{raw}}=\beta I_{AB}-\chi_{BE}.
\]

For a point estimate, adjacent precision rows should be compared at `C,w,Z`,
all symplectic eigenvalues, `chi_BE`, and `K_raw`. A derivative estimate of
the Holevo functional can explain a discrepancy, but it is not a safe upper
bound at a moving interval maximizer.

For a conservative security calculation, use an upper bound on the Holevo
maximization over the enlarged admissible `Z` interval and a lower bound on
the mutual information:

\[
K_{\mathrm{low}}
 =\beta I_{AB,\mathrm{low}}-\chi_{BE,\mathrm{upper}}.
\]

This is the correct direction for numerical uncertainty. If the source
interval is not rigorously enclosed, the result is only a sensitivity
diagnostic. A pointwise `C,w` convergence row should not be described as an
interval security certificate.

The current median comparison scale is favorable for a bounded ranking
diagnostic: the existing Full median is approximately `+0.0003328` and the
MB median approximately `-0.0004592`, a separation of about `7.92e-4 bit`.
The preregistered `1e-6`-bit instantaneous tolerance is much smaller than
that gap, but only after the full-Z interval and all model-alignment gates are
passed. It does not authorize a learned ranking or publication claim.

## 17. Exact versus conservative goals

There are two valid but different deliverables:

### Exact-source-moment numerical deliverable

Use the frozen full-support sector worker, the exact serialized binary64
inputs, the 1050/1250/1450 rows, adjacent scalar convergence, matrix/solve
residuals, and downstream observable agreement. Call the result a selected
high-precision numerical value under the frozen protocol. Do not call it a
formal interval enclosure merely because it has many decimal digits.

### Conservative security deliverable

Use ball or interval enclosures for `C,w` (or a separately proved error bound),
propagate them to a physical `Z` interval, maximize `chi_BE` over that enlarged
interval, and subtract it from a lower-bounded MI. This can support a
conservative lower bound if every enclosure and physicality check is valid,
but it does not provide the requested exact `C,w` point unless the intervals
are subsequently narrow and selected under a stated rule.

The current task asks first for the exact source moments and then one median
full-Z point. The direct fixed 1050/1250/1450 sector route therefore has the
best fit.

## 18. Strategy ranking

| Rank | Category | Validity for current model | Expected cost | Implementation effort | Decision |
|---:|---|---|---|---|---|
| 1 | `DIRECT_HIGHER_PRECISION_SECTOR_RUN` | High; uses the existing validated C4 worker and frozen protocol | Medium-high, about 35 minutes for estimated 1050/1250/1450 PS rows | Low | **Selected** |
| 2 | `ADAPTIVE_SECTOR_PRECISION` | Potentially high in a new protocol; not currently admissible without a manifest change | Potentially lower | Medium; needs per-sector error budgets and mixed-precision validation | Defer |
| 3 | `CONSERVATIVE_INTERVAL_SECURITY_EVALUATION` | High for a proved conservative bound, not an exact point value | Medium to high; interval overestimation is possible | Medium-high | Use only if point convergence fails or a bound is required |
| 4 | `ANALYTIC_SUPPORT_PLUS_NUMERICAL_CONVERGENCE_GATE` | Establishes rank but not inverse-square-root accuracy by itself | Low | Low | Supporting gate, not a complete source-moment result |
| 5 | `ARB_SECTOR_PROTOTYPE` | Potentially strongest numerical evidence, but current matrix routines have clustering/overestimation caveats | High and uncertain | High | Independent fallback, not first move |
| 6 | `REFORMULATE_FORWARD_SOURCE_MOMENTS` | Could be valid only after a new derivation and equivalence proof | Unknown | Very high | Do not pursue for this blocker |

The selected direct run is not a claim that higher precision is the only
possible algorithm. It is the shortest path compatible with the current
frozen formula, worker, provenance, and lifecycle gates.

## 19. Exact next-run specification

This is a specification for a future authorized read-only run, not an
execution record.

### Inputs and scope

1. Use only the frozen optimized PS+V_A median checkpoint and its serialized
   binary64 hexadecimal probabilities and prototypes.
2. Bind the checkpoint hash, direct-input hash, worker hash, model-spec hash,
   and protocol hash in the result manifest.
3. Run the four C4 64-by-64 sectors only. Do not form a dense high-precision
   256-by-256 global eigensystem.
4. Do not run Full again, search new PS/GS/V_A values, train, access held-out
   data, or execute reverse/full-Z backward work.

### Precision and acceptance

1. Start the fixed sector ladder at **1050 decimal digits**. This is the one
   recommended starting precision for the next run.
2. Recompute the same four sectors at 1250 and 1450 digits. The 1250 and 1450
   rows are the frozen acceptance/reference and successive confirmation pair;
   the 1050 row is a non-acceptance probe and its outcome cannot justify
   skipping either acceptance row.
3. Require computed rank 256 at both 1250 and 1450. Do not use an eigenvalue
   floor, support threshold, diagonal repair, or negative-eigenvalue clamp.
4. Record for every sector: Hermiticity residual, trace, minimum and maximum
   eigenvalue, positive count, eigendecomposition reconstruction residual,
   orthogonality residual, solve residuals, and the sector contributions to
   `C` and `w`.
5. Require the aggregate `C,w` values and all downstream observables to agree
   between 1250 and 1450 under the already frozen tolerances:
   `C,w,Z,symplectic eigenvalues` within
   `1e-7 + 1e-6*|reference|`, and `chi_BE`/instantaneous `K_raw` within
   `1e-6 bit + 1e-5*|reference|`.
6. Require trace normalization, Hermiticity, residual identities, finite
   values, nonnegative `w`, physical covariance, and valid symplectic
   eigenvalues. Any failed gate is `FAIL_CLOSED`.

### One median full-Z point

After the source-moment pair passes, evaluate only the frozen median
full-Z physical interval. Use the same post-action
`epsilon_total=epsilon_base+c_phi V_A` in MI and security. Record:

- `C,w` and their precision rows;
- the source `Z` interval and physical intersection;
- the maximizing `Z` and whether it is boundary or interior;
- the three symplectic eigenvalues;
- `chi_BE`, MI provenance, and `K_raw`;
- numerical tolerances and every accepted/rejected physicality check; and
- all hashes and wall-clock timings.

This one point is a bounded numerical diagnostic. It does not authorize a
three-state ranking, adaptive training, baseline selection, final-test
evaluation, or a publication-scale security claim.

### Runtime stop rule

Use a hard 60-minute wall-clock budget for the complete PS precision artifact,
including the fixed 1050 row. Stop
and write a fail-closed partial artifact if any one row exceeds 20 minutes,
if the 1450 row cannot complete inside the budget, or if the worker's
predicted next precision would exceed 1450. Do not escalate to 1600 or 2000
digits under this task. A timeout is evidence about cost, not evidence of
mathematical rank deficiency.

## 20. Caching and reproducibility checklist

The following cache boundaries reduce repeated work without changing the
formula:

- cache the exact input conversion, normalized probabilities, prototypes, and
  all hashes;
- cache the four sector matrices keyed by input hash and sector index;
- cache each eigendecomposition keyed by input hash, sector, worker version,
  and decimal precision;
- cache square-root/inverse-square-root diagonal factors and solve
  factorizations only at their own precision;
- cache cross-sector transition matrices `M_s` and sector `C` contributions;
- cache the residual vectors used for the nonnegative `w` identity;
- aggregate cached values only after checking that precision and provenance
  keys match; and
- never treat a lower-precision factorization as an authoritative
  higher-precision factorization.

The final result must be reproducible from the frozen binary64 hexadecimal
inputs, not from a decimal reserialization or an optimizer checkpoint whose
floating-point conversion is ambiguous.

## 21. Publication and lifecycle implication

The paper need not print a 600-digit eigenvalue. It should eventually report
the analytic finite-constellation support condition, the exact C4 reduction,
the selected precision pair, residual and invariant checks, source-moment
convergence, full-Z physicality, and the uncertainty of the reported
functional. It must preserve the repository's current scope boundary:
asymptotic oracle-CSI calculation, no finite-size or composable claim, and no
unapproved attack-class or operational fading-protocol claim.

Until the specified PS source-moment pair and the one median full-Z point are
actually executed and independently checked, the project remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and
`NOT_READY_FOR_ADAPTIVE_TRAINING`. This memo changes neither state.

## 22. Final answer to the blocker

The current PS+V_A minimum mode is approximately `5.52e-598`, so 800 decimal
digits already provide a large conditional guard margin and have produced
stable diagnostic `C,w` rows. The authoritative route is nevertheless the
existing fixed C4 protocol: start the fixed ladder at **1050 decimal digits**,
retain 1250/1450 as the acceptance pair, compute one median full-Z point, and
stop there. Do not run a dense global eigensolve, 1600/2000-digit escalation,
adaptive mixed-precision aggregation, a new backend, or any training.

The exact selected category is:

```text
DIRECT_HIGHER_PRECISION_SECTOR_RUN
```

## Sources

[1] S. Denys, C. Brown, and A. Leverrier, “Explicit asymptotic secret key
rate of continuous-variable quantum key distribution with an arbitrary
modulation,” *Quantum* 5, 540 (2021), especially the source-state,
square-root similarity, `C,w`, and `Z`-interval construction.  
<https://quantum-journal.org/papers/q-2021-09-13-540/>

[2] Open-access version of the same primary paper.  
<https://arxiv.org/abs/2103.13945>

[3] mpmath documentation: basic usage, technical precision behavior, and
matrix/eigensolver routines.  
<https://www.mpmath.org/doc/current/basics.html>  
<https://www.mpmath.org/doc/current/technical.html>  
<https://mpmath.org/doc/current/matrices.html>

[4] A. Neumaier and A. Ghaani Farashahi, “Introduction to coherent
quantization,” Proposition 5.1, finite linear independence of distinct
coherent states.  
<https://link.springer.com/article/10.1007/s13324-022-00689-3>

[5] N. J. Higham, *Functions of Matrices*, Chapter 3, conditioning and
Fréchet derivatives.  
<https://epubs.siam.org/doi/10.1137/1.9780898717778.ch3>

[6] N. J. Higham, *Functions of Matrices*, Chapter 6, matrix square roots and
algorithmic stability.  
<https://epubs.siam.org/doi/10.1137/1.9780898717778.ch6>

[7] F. Johansson, Arb documentation on ball arithmetic and dependency
overestimation.  
<https://arblib.org/using.html>

[8] Arb `acb_mat` documentation on approximate and rigorous matrix
eigenvalue routines and eigenvalue clusters.  
<https://arblib.org/acb_mat.html>
