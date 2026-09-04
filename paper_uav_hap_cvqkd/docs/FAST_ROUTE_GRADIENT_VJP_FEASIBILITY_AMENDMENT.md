# Fast-route gradient/VJP feasibility amendment

Status: **frozen before implementation and execution**. This amendment
preserves EVID-0029, EVID-0030, EVID-0031, and EVID-0032. It supersedes only
the assumption that the frozen untrained Full center can be used for a
complex128-fast gradient certification.

## Frozen center classification

`untrained_full_initialization` is a mathematical-full-support, AP-only
evaluation fixture. Its bad/medium/good complex128 gate minima are negative at
roundoff scale, while arbitrary precision resolves positive modes near
`10^-675`. It is therefore `INELIGIBLE` for fast-route gradients. This is an
inherent conditioning result, not a support threshold, evaluator defect, or
permission to differentiate the AP fallback.

## Separate synthetic preflight

The synthetic fixture is an algebraic four-sector, 64-dimensional Hermitian
positive-definite preflight. Each sector is `0.00390625 I`, each symbol
probability is `0.00390625`, and every prototype is `0.125 + 0.25i`. It is
not a physical transmitter, training fixture, or security-performance result.
It is constructed only to satisfy the existing unrelaxed fast-route gates and
exercise the cluster-safe matrix-function VJP.

The later synthetic validation must test positive fast routing, repeated and
unitarily rotated clusters, complex directional derivatives, basis invariance,
and the C/residual-w chain. It may test Z, standard-form covariance,
symplectic values, Holevo, and raw K only as bounded algebraic preflights.

## Claim boundary and lifecycle

A synthetic PASS validates only the analytic Fréchet/VJP implementation inside
the fast domain. It does not validate end-to-end PS/GS/VA gradients for the
frozen Full center, authorize AP differentiation, alter the security
functional, approve a threshold, or authorize publication training.

The frozen Full center remains gradient-ineligible until a distinct,
scientifically defensible training-domain solution is separately designed and
frozen. No fast gate, finite-difference setting, physical mapping, or fallback
semantics changes under this amendment.
