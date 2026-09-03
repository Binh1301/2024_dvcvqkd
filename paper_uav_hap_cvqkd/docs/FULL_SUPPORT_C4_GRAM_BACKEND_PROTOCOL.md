# Full-support C4-Gram backend protocol

Status: **frozen before implementation**. This is a numerical realization of
the existing security functional, not a change to the frozen physical model,
MI, Holevo, SKR, or security scope.

## Source moments

For each C4 sector, let `G_r = U_r Lambda_r U_r^H`, let `D=diag(z_k)`, and
let `M_r=U_r^H D U_(r-1)`. All 256 mathematical modes are retained. There is
no `lambda > tau` support selection. The exact full-support target is the
limit of the current C4 expression:

`B_r = sqrt(Lambda_r) M_r invsqrt(Lambda_(r-1))`

`C = sum_r tr(sqrt(Lambda_r) B_r sqrt(Lambda_(r-1)) B_r^H)`.

Implementations must obtain `B_r` by factorized Hermitian solves/matrix
functions, not elementwise eigenvalue ratios. This changes evaluation order,
not the formula. Exact binary64 inputs are reconstructed into four 64-by-64
Hermitian sectors.

Define `A_r=sqrt(Lambda_r) B_r invsqrt(Lambda_(r-1))`,
`Q_r=sqrt(Lambda_r) U_r^H /(2 sqrt(p))`, `T_r=A_r Q_(r-1)`, and
`d_k=sum_r <Q_r[:,k],T_r[:,k]>`. The source penalty is evaluated as the
nonnegative residual identity

`w = sum_k 4 p_k sum_r ||T_r[:,k] - Q_r[:,k] d_k||^2`.

Before activation, tests must prove this is algebraically equal to the current
full-support `first_term - sum_k 4 p_k |d_k|^2` expression at arbitrary
precision. No negative clamp other than the existing frozen physicality check
is introduced.

## Routing

The fast path is CPU `float64/complex128`. It may return a source result only
when every sector has positive computed spectrum, condition number at most
`1e6`, Hermitian eigendecomposition reconstruction residual at most `1e-12`,
and the two `w` identities agree to relative error at most `1e-12`.

Otherwise it serializes the exact binary64 PMF and amplitudes with `float.hex`
to the arbitrary-precision worker. The worker uses the fixed 1050, 1250, 1450
decimal-digit ladder. It accepts only rank 256 at 1250 and 1450 and successive
agreement of `C,w,Z,lambda1,lambda2,lambda3,chi_BE,raw_K` under the existing
frozen tolerances. Any failure is fail-closed.

`tau` remains unchanged but is absent from full-support source-moment routing.
It is historical/diagnostic only. Eigenvalue floors, `epsilon I`, threshold
support, straight-through gradients, and outcome-based precision changes are
forbidden.

## Gradients and lifecycle

Fallback is evaluation-only initially. Training may use a fast-path gradient
only after that path has passed its routing gate. A fallback state returns an
explicit no-gradient status; it is not excluded from evaluation. Training
through fallback requires a later frozen analytic VJP using Hermitian
matrix-function Frechet derivatives, validated by independent directional
checks for PS, GS, and VA. Finite differences or a straight-through surrogate
are not a replacement.

Pointwise Guard must later guard evaluator provenance, route determinism,
finite outputs, and approved gradient status—not distance from `tau`.

## Required implementation validation

Use all 12 hash-bound fixtures in `threshold_validation_v1.yaml`, including
the two failed full-model fixtures. Require exact input round-trip, full-support
convergence, fast/fallback route determinism, repeated byte-identical traces,
and frozen-tolerance agreement for every listed observable. Before any
training use, add independent directional-gradient checks for PS, GS, and VA.
No training, baseline search, optimized-MB search, or final-test access is
authorized by this protocol.

## Required implementation artifacts

Implementation must add only the backend source, its worker/request-result
schemas, focused source-moment/Holevo/routing tests, and a hash-bound
implementation manifest. The manifest must bind this protocol, the 12-fixture
roster, the arbitrary-precision worker, production source files, schemas, and
the frozen model. A separate execution manifest is required before any new
validation run.

## Implementation plan

1. Replace only the C4 source-moment internals with the full-support,
   factorized-`C` and residual-`w` formulation; prove arbitrary-precision
   equality to the frozen full-support target.
2. Add deterministic fast/fallback routing and exact-binary64 worker protocol;
   expose evaluation-only fallback status and leave training fallback blocked.
3. Add the focused tests and hash-bound implementation manifest. Do not run the
   new prospective validation in implementation work.
