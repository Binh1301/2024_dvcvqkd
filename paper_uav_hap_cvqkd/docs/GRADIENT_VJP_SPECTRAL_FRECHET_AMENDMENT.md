# Gradient/VJP spectral Fréchet amendment

Status: **frozen before implementation and execution**. This amendment
supersedes EVID-0030 only for spectral-gradient semantics. EVID-0030 remains
historical, frozen, and unexecuted; its seeds, probes, CRN, `N_MC`, step
ladder, tolerances, physical mapping, and lifecycle restrictions are unchanged.

## Positive-definite matrix function

For a Hermitian positive-definite matrix `T = U diag(lambda_i) U^H`, define
`f(T)=T^(-1/2)`. For Hermitian direction `E`, the required derivative is

`Df_T[E] = U (L Hadamard (U^H E U)) U^H`,

where, for every positive pair including repeated values,

`L_ij = -1/(sqrt(lambda_i)*sqrt(lambda_j)*(sqrt(lambda_i)+sqrt(lambda_j)))`.

For distinct values, with `a=sqrt(lambda_i)` and `b=sqrt(lambda_j)`,

`(a^-1-b^-1)/(a^2-b^2) = ((b-a)/(ab))/((a-b)(a+b)) = -1/(ab(a+b))`.

Thus the same expression has repeated-value limit
`L_ii=-1/(2*lambda_i^(3/2))`. No eigenvalue-gap branch, simple-spectrum
requirement, eigenvalue perturbation, or cluster splitting is permitted.

## Complex reverse-mode convention

For a real scalar loss, this repository's complex128 VJP convention is
`dLoss = Re(tr(G^H dT))`. First hermitianize an upstream matrix as
`G_H=(G+G^H)/2`. The Loewner matrix is real symmetric, so the Fréchet operator
is self-adjoint under this real Frobenius inner product. The spectral VJP is
therefore

`VJP_T(G) = U (L Hadamard (U^H G_H U)) U^H`.

The future custom autograd boundary must return this whole-matrix VJP; PyTorch
may use `torch.linalg.eigh` only in forward decomposition. Its eigenvector
backward is explicitly prohibited.

## C, w, and downstream chain

The amendment does not change `C`, `w`, `Z`, covariance, symplectic values,
Holevo, MI, or raw SKR. For `C`, propagate the Fréchet VJP through the existing
factorized sector products. For `w`, propagate through the validated residual
norm, never its cancellation-prone subtraction counterpart. For every solve
`A X=B`, use `dX=A^-1(dB-dA X)` and the corresponding adjoint solve; do not
materialize a matrix inverse. Product, trace, square-root, covariance,
symplectic, entropy, MI, and raw-K VJPs retain their actual PyTorch real/complex
coordinates. GS remains differentiated in its existing real/imaginary raw
coordinates through its existing gauge map and physical normalization.

## Route and repeated-eigenvalue policy

The custom Fréchet VJP is available only for the existing
`COMPLEX128_FAST` route with a Hermitian positive-definite matrix. A nonpositive
eigenvalue, AP fallback route, unknown route, nonfinite result, or provenance
mismatch is `FAIL_CLOSED` for gradient availability. This is not a support
threshold and does not change mathematical full support. The AP subprocess is
never differentiated.

## Required cheap preflight tests

Use the frozen complex128 synthetic tolerance (`atol=1e-10`, `rtol=1e-9`) to
test: distinct diagonal SPD; identity; repeated positive cluster; unitary
rotation of that cluster; near-repeated SPD; complex Hermitian SPD; finite
differences of `T^(-1/2)`; no NaN at repetition; and basis invariance under a
unitary basis change inside the repeated eigenspace. These are protocol/math
preflights only, not gradient/VJP certification.

## Lifecycle

No gradient validation has passed. Publication training, final-test access,
baseline selection, optimized-MB selection, threshold approval, and fallback
differentiation remain unauthorized. The next task may implement the custom
Fréchet VJP and a hash-bound validation harness, but must not execute it.
