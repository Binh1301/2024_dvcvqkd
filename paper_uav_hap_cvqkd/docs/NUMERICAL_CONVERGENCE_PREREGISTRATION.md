# Numerical convergence preregistration

Status: **SOFTWARE_PREREGISTERED before convergence outcomes were inspected**.
This document freezes engineering error criteria and candidate grids; it is
not convergence evidence and does not authorize training or test access.

## Scope

The bounded pretraining fixture roster is generated only from the frozen
validation realization.  It contains the outcome-independent bad, medium, and
good channel states; the low/high fixed-VA extremes for Uniform, Binomial, and
fixed MB; optimized-MB `nu` extrema and the analytically worst PAPR grid member;
the untrained full-model initialization; and a synthetic C4 ensemble with an
exact `|alpha|^2=30` symbol.  This certifies the frozen physical boundary and
listed reference families, not future learned checkpoints.  Every selected
learned checkpoint must be replayed by the exact-roster convergence gate before
held-out evaluation.

## Mutual-information Monte Carlo rule

| Item | Preregistered value |
|---|---|
| Nested sample-count grid per symbol | `64,128,256,512,1024,2048,4096` |
| Independent replication base seeds | `202607..202611` |
| CRN rule | Nested within replication and common across configurations |
| Absolute tolerance | `0.002 bit` |
| Relative tolerance | `0.001` times `|I_ref|` |
| Reference | `4096`; never selectable |
| Selection | First candidate whose complete suffix passes every state, fixture, and replication |
| Replication stability | Every reference replication must lie within the same absolute-plus-relative bound of the replication mean |

The absolute term controls low-MI states; the relative term prevents an
unnecessarily absolute-only criterion at large MI.  Samples are processed in
chunks of 64 without changing the estimator or RNG stream.

## Fock-cutoff and SKR rule

| Item | Preregistered value |
|---|---|
| Cutoff grid | `48,56,64,72,80,96,112,128` |
| Reference cutoff | `128`; never selectable |
| Density-trace tolerance | `1e-10` |
| `C,w,Z` tolerance | `1e-7 + 1e-6 |reference|` |
| Each symplectic eigenvalue tolerance | `1e-7 + 1e-6 |reference|` |
| `chi_BE` and instantaneous raw `K` tolerance | `1e-6 bit + 1e-5 |reference|` |
| Selection | First cutoff whose complete suffix passes all metrics, states, and fixtures |

The grid ceiling is fixed prospectively from the coherent-state Poisson tail at
the approved photon boundary, not from a computed Holevo/SKR outcome.  A
candidate also fails on any physicality exception or density-trace violation.
The raw key rate is `K=0.95 I_AB-chi_BE`; no zero clipping is permitted.

## Density pseudoinverse sensitivity

The threshold grid is `1e-14,1e-13,1e-12,1e-11,1e-10`, with `1e-14` as the
reference and `1e-12` as the prospectively active candidate.  Every listed
fixture must keep `C,w,Z,chi_BE` within `1e-7 + 1e-6 |reference|`.  Retention of
`1e-12` is conditional on this test.

## Failure rule

No grid or tolerance may be relaxed after seeing an outcome.  Failure at the
largest reference, absence of a stable selectable suffix, or failure of the
active pseudoinverse threshold leaves the project
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; the approved peak domain must then be
reconsidered or a new prospectively approved numerical protocol must be issued.
