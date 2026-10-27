# C,w numerical stability — INCONCLUSIVE full support

The final comparison uses the largest completed Fock cutoff/highest scheduled
precision, and the highest completed Gram precision. Selection never uses
closeness to the cached value. Differences in Cw_comparison.csv are computed
at100digits against the EXACT binary64 cached values; converting both methods
to float64 first would hide sub-ulp differences. Relative and absolute
differences are separate, and the repository cache is a reference, not an
independently certified truth.

Six small-case labels (4/16/64-QAM, Uniform/MB) pass full-rank independent
algebra checks. MB4 equals Uniform4 because all four points have the same
energy; these are six test labels, not six distinct physical constellations.
For the selected256-QAM sources, the completed C,w observables agree across
methods and tested precision/cutoffs, but some positive source modes remain
unresolved. No formal convergence certificate or evidence promotion follows.

## Conditioning, cutoff and cancellation

Winner complex128 Fock atNF64: changing the declared eigenvalue threshold
from1e-10 to1e-12,1e-14,1e-16 retains25,30,35,40 modes, respectively.
Residual w changes from about9.59060e-9 to6.70527e-10,5.70921e-10,
5.70037e-10. Raising NF alone with an unchanged spectral threshold does not
restore discarded positive modes. Gram float64 at1e-16 retains43 modes and
gives about5.70094e-10, showing a different near-roundoff numerical support.
These are explicitly regularized approximations, not replacements for the
canonical256-mode MP inverse.

At the same float64 cutoff/operator, direct-minus-residual w can be around
4e-16 absolute, already around1e-6 relative at w~5.7e-10. Stable residuals
reduce cancellation but cannot repair missing spectral support or conditioning.
No negative result is clipped. Exact direct/residual differences, any negative
w and eigenvalues, and backward residuals are retained in the CSV/job JSONs.

FockNF24 gives w around2.23e-8 for the winner: too short despite its inexpensive
density construction. Poisson tails are checked independently; no state or PMF
is renormalized. Trace near1 is necessary but not sufficient for inverse-root
accuracy. Input binary64 probabilities have tiny exact-sum deviations from1,
recorded in input_validation.json and used identically by both methods.

Arbitrary precision uses the declared10^(-digits+20) spectral floor. The winning
FockNF256/260digit job retains231/256 modes, while Gram180digits retains186/256.
Fixed MB best completed Fock hasNF128/rank128, and Gram180digits rank186/256.
Backward residuals at high precision do not bound unresolved tiny eigenvalues;
only RETAINED condition numbers are reported, not a fabricated full condition.
Both Gram260digit jobs hit180s; Fixed FockNF256 had only the remaining global
budget. Logs retain per-sector progress; no missing final C,w is filled in.

The original repository worker uses1050/1250/1450 digits and requires256positive
modes, but its final C,w allowance is1e-7+1e-6*maxabs. The absolute part is
larger than the stored w. Its cached settings/label do not substitute for the
missing original per-precision receipt or prove tiny-w relative accuracy.

## Bounded outcomes

| Job | Outcome | Runtime s | Assigned time cap s |
|---|---|---|---|
| 49_Winner_MB_B_NNone_d260 | INCONCLUSIVE_TIMEOUT | 180.125 | 180.000 |
| 63_Fixed_MB_B_NNone_d260 | INCONCLUSIVE_TIMEOUT | 180.094 | 180.000 |
| 65_Fixed_MB_A_N256_d260 | INCONCLUSIVE_TIMEOUT | 9.281 | 9.175 |

Runtime limits were enforced sequentially. A Windows venv launcher initially
hid the actual numerical-worker RSS;45 completed low/medium-cost jobs have
launcher-only memory samples and are explicitly flagged. The batch was stopped,
those results/logs preserved, and workers were relaunched via the actual base
interpreter with the existing venv dependencies. Subsequent RSS samples measure
the correct PID. No installed package, production code or historical cache was
changed. One interrupted Fock diagnostic was resumed once; this is not a retry
of either timed-out Gram260 run or the missing Uniform job.

## Safest next step

Keep current cache/evidence labels. Before another high-cost attempt, add
per-sector/per-precision numerical checkpoints and profile the selected-source
worker. A separately budgeted run above260digits must resolve all256 source
modes at two successive precisions and compare C,w, residuals and rank; it
must not rely on the repository's broad absolute tolerance alone. If numerical
or analytic bounds for omitted-mode effects are unavailable, keep full-support
accuracy INCONCLUSIVE. Do not restart the entire source catalog or Uniform job.
