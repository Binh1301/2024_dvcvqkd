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
| Nested sequential sample-count grid per symbol | `256,512,1024,2048,4096,8192` |
| Independent replication base seeds | `202607..202611` |
| CRN rule | Nested within replication and common across configurations |
| Absolute tolerance | `0.002 bit` |
| Relative tolerance | `0.001` times `|I_ref|` |
| Selection | First count after two consecutive global refinement passes |
| Replication stability | Required at every passing stage using the same absolute-plus-relative bound |

The absolute term controls low-MI states; the relative term prevents an
unnecessarily absolute-only criterion at large MI. Samples are processed in
chunks of 64 without changing the estimator or RNG stream. The exact
prospective stopping rule and roster are hash-bound in
`MI_CERTIFICATION_ROSTER.md`.

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

## Prospectively approved near-coincident extension (2026-08-28)

Before inspecting any Fock outcome above 128, the numerical engineer and
orchestrator froze the stress-only extension sequence
`144,160,192,224,256`, with 256 as a nonselectable reference. The combined
ordered grid is therefore
`48,56,64,72,80,96,112,128,144,160,192,224,256`. The original stable-suffix
rule and every tolerance above remain unchanged. The extension is first run on
`near_coincident_pseudoinverse_stress` using both the active full-matrix path
and an algebraically equivalent support-restricted/residual diagnostic path.
It may change neither the active pseudoinverse threshold nor the frozen
allowance. A full-roster rerun is permitted only if the stress-only result has
a selectable suffix. No held-out state or performance ranking is involved.

## Prospectively approved Gram-oracle precision extension (2026-08-28)

The independent Gram oracle first froze and executed `50,80,120,160` decimal
digits. Before any calculation above 160 digits, those runs showed only
`16,24,33,44` of the analytically expected 256 positive modes above their
precision floors. A log-spectrum extrapolation estimated `974--986` digits by
C4 sector. A measured runtime fit (`time ~ digits^0.267`) projected about 90 s
for four eigensystems at 1050 digits, so `1050` digits is prospectively appended
as the first adaptive full-support probe. That probe resolved only 244/256
modes and prospectively updated the sector estimates to `1111--1118` digits.
Before inspecting any later outcome, `1250` digits is therefore frozen as the
first expected full-resolution point and `1450` as its successive full-support
confirmation. The adaptive sequence is `1050,1250,1450`. It is diagnostic
only; it does not change the `1e-12` production threshold, Fock tolerances, or
security model.

## Failure rule

No grid or tolerance may be relaxed after seeing an outcome.  Failure at the
largest reference, absence of a stable selectable suffix, or failure of the
active pseudoinverse threshold leaves the project
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; the approved peak domain must then be
reconsidered or a new prospectively approved numerical protocol must be issued.
