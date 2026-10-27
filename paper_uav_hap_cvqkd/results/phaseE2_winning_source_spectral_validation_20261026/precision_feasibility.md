# Precision and performance feasibility

All target-source timings below are historical Phase E measurements, not new runs:

| Job | Observed controller wall | Outcome |
|---|---:|---|
| Winner Gram80 | 106.969s | complete, 105 retained modes |
| Winner Gram180 | 154.610s | complete, 186 retained modes |
| Winner Gram260 | 180.125s | timeout after all four rank messages; no numerical checkpoint |
| Winner Fock NF256/260 | 140.500s | complete, 231 retained modes |

Historical logs do not contain stage-resolved CPU times. They cannot establish
how much of the Gram260 timeout belonged to construction, eigensolves or final
moments. Code inspection shows expensive redundant full-matrix Fourier sums and
diagonal matrix products. That is an optimization opportunity, not measured
proof of the dominant stage. Generic stress-source 1050/1250/1450 settings are
not a precision estimate for this particular winning source.

The isolated wrapper builds H_s directly from four coherent overlaps per pair:

\[
(H_s)_{ij}=\sqrt{p_i p_j}\sum_{t=0}^3 i^{st}
e^{-(|z_i|^2+|z_j|^2)/2+z_i^*i^t z_j}.
\]

The exact identity D_alpha F_(s-1)=F_s diag(z) gives L_s=H_s diag(z).
This removes the full 256x256 matrix and the separate 16-term Fourier sums for
both H_s and L_s. Diagonal products become row/column scaling, with no generic
LU solve. The unchanged Phase E method remains the small-case cross-check.
There is no new source-moment definition.

Each precision uses four sequential 64x64 eigensystems; matrices and eigenvectors
are checkpointed. Compatible completed sectors skip construction/eigensolving on
resume. Completed moments are also reused. Different precisions rebuild independently.
The old 180/260-digit spectrum-only files cannot avoid a new eigensolve because
their eigenvectors were never serialized. Overlaps are still evaluated separately
per sector; target-size performance of this simpler implementation is unmeasured.
No claimed speedup is extrapolated from M<=16 tests.

The finite-NF256 log-spectrum fit suggests missing eigenvalues of order
1e-274..1e-284, but is not a rigorous full-Gram estimate. The independent directed
scalar bound guarantees all full-Gram eigenvalues >=1e-312. These motivate two
separate **400 and 500 decimal digit** trials, with floors 1e-380 and 1e-480.
Residuals, input rounding, eigenvector/cluster conditioning and inverse-square-root
amplification must still be assessed. Rank256 or matching printed digits alone
does not establish accurate C,w.

Proposed cap: 3600s total active controller wall, 600s per stage, sequential
workers, 1024MiB sampled working-set limit, one numerical thread. A single
validated eigensystem remains available even if a later stage times out.
Polling/kill/serialization overshoot is recorded; the sampled memory cap is not
an OS allocation guarantee. The actual base Python interpreter is launched
with the existing venv site-packages, so its numerical PID is monitored.
No package installation or Application Control workaround is proposed.

Runtime at 400/500 digits is **NOT_BENCHMARKED**. The cap is a stop budget,
not an expected completion time. If either precision cannot resolve every mode,
checks fail, or the functional error assessment remains inconclusive, stop and
retain INCONCLUSIVE. No automatic higher precision, retries or source upgrades.
See controlled_run_authorization_plan.md for the exact unexecuted command.
