# 1. Skills / workflow used

Ponytail full was used for the coding workflow: the existing diagnostic
helpers were reused, no dependency was added, and production model/security
code was left untouched. The relevant repository Superpowers plan was read
before execution:
docs/superpowers/plans/2026-09-11-ap-worker-rebind.md.

The evidence-first order was followed:

1. create the bounded machine-readable audit artifact;
2. validate its input and producer provenance;
3. record this report and the evidence/decision/state updates;
4. run only focused verification.

The exact 15-minute watchdog was enforced. No dense 256-by-256
700--900-digit eigensolve was run.

# 2. Frozen candidates

The audit used the existing median-state serialized inputs from
results/ps_va_ap_worker_localization_20260912.json:

| candidate | checkpoint SHA-256 | direct-input hash | constellation hash | T | epsilon_base | V_A |
|---|---|---|---|---:|---:|---:|
| PS+V_A | 1c5d49d1a562c558a18a76994399b09c4bee88ddbebf35370ae9cb690e3ca8d1 | 4589747c3ae1cf3d8ce996d13f591a0e8f2aae7dd64df402a81507255dd43a99 | 3e56859fb805f8f445c6ec8c465fc435b1b5706a025e67f673c649f30498fcab | 0.022181763383054068 | 0.02025322309984713 | 0.9953704226185827 |
| Full | 9e5bf3fb8534cbf2640ca0feb99810518c110c283931d701c44ee52e16622e51 | cd1874d5b49db0c6c45514ef76e92b533414c1c5cbd06143007d4dd3b3d3cb2f | 26ab6f7b0997f3e79866cb79c3c0891d8b2ee8c1dbd689a4d5d5961bdac7185e | 0.022181763383054068 | 0.02025322309984713 | 0.9962581009336706 |

The requested precision ladder was 80, 120, and 200 decimal digits. The
audit stopped after one completed PS row and one PS timeout; Full was not
started.

# 3. Independent global construction

For each attempted row, the audit parsed the stored binary64 hexadecimal
probabilities and physical prototype amplitudes, expanded the 64
representatives by the four exact phase rotations, and formed

$$
W_{ij}=\sqrt{p_i p_j}\,
\exp\left[-\frac{|\alpha_i|^2+|\alpha_j|^2}{2}
+\alpha_i^\ast\alpha_j\right]
$$

directly as an arbitrary-precision 256-by-256 matrix. The matrix was not
formed in complex128 and then converted, and the production C4 sector builder
was not used to construct W.

The production sector builder was called only as a separately labelled
comparison path after W had been constructed. The exact weighted-Gram and
source-spectrum relation is derived in
[DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md](DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md).

# 4. Fourier transform construction

The full matrix uses orbit-major ordering (k,r), with r in Z4. The
independent transform applies the four-point Fourier matrix

$$
F_{r,a}=\frac{i^{ar}}{2}
$$

on the rotation coordinate. The transformed matrix is
Y = U^H W U, with blocks indexed by Fourier sectors a and b. The diagonal
blocks are compared with independently rebuilt production sectors after
using the same orbit order.

The corrected four-point Fourier matrix is unitary. Its maximum residual in
the completed row is 0.0 at the reported precision. A helper-construction
reporting defect initially recorded 1.0 because an mpmath matrix constructor
ignored a callable initializer and created a zero matrix. The W transform
itself used explicit summation loops and was unaffected. The artifact records
this as a posthoc reported-field correction, and the focused Fourier
unitarity test passes.

# 5. Global invariant checks

The completed row is PS at 80 digits. A TIMEOUT means that the child process
did not return a matrix row before the remaining watchdog budget expired.
NOT_RUN means that the precision/candidate was never started.

| candidate | precision | Hermiticity residual | trace error | Frobenius invariant error | trace(W^2) error |
|---|---:|---:|---:|---:|---:|
| PS+V_A | 80 | 0.0 | 3.2959746043559335e-17 | 0.0 | 1.0785415561280616e-81 |
| PS+V_A | 120 | TIMEOUT | TIMEOUT | TIMEOUT | TIMEOUT |
| PS+V_A | 200 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 80 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 120 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 200 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

For PS at 80 digits:

- trace(W) = 0.99999999999999996704025395644066520617;
- trace of the extracted sectors is the same;
- ||W||_F^2 = 0.48872469879958830890232903101424590857;
- the sector Frobenius invariant matches at the reported precision;
- trace(W^2) = 0.48872469879958830890232903101424590857.

The approximately 3.30e-17 trace error is the expected exact-binary64
normalization residual, not a support failure.

# 6. Off-block residual

The off-block value is the maximum norm of the a != b Fourier blocks divided
by ||W||_F. The requested ladder produced:

| candidate | 80 digits | 120 digits | 200 digits |
|---|---:|---:|---:|
| PS+V_A | 0.0 | TIMEOUT | NOT_RUN |
| Full | NOT_RUN | NOT_RUN | NOT_RUN |

The completed PS row therefore supports the expected C4 block structure. The
earlier independent 100-digit localization artifact also reports 0.0 for the
maximum Fourier off-block residual for both PS and Full, but it did not run a
dense global eigensolve.

# 7. Global-vs-production block comparison

For PS at 80 digits, the relative Frobenius residuals between the diagonal
Fourier blocks extracted from the direct global W and the production sectors
are:

$$
[8.0192566557\mathrm e{-82},\
4.6556070035\mathrm e{-81},\
1.1335494419\mathrm e{-81},\
9.3820611337\mathrm e{-82}],
$$

with maximum 4.6556070035129793e-81. The direct global blocks versus the
independently rebuilt direct-sector formula have residuals
[0.0, 0.0, 0.0, 0.0].

This is a PS positive result for the completed row: the direct full-matrix
path and production C4 blocks agree. The Full block comparison was not
started within the budget. Its prior independent 100-digit structural audit
also reported zero Fourier-sector residuals, but that prior artifact did not
record the new production-sector comparison field.

# 8. Dense global spectrum

Only the PS 80-digit global eigensolve completed. The resolution threshold
was 10^-(digits-20) = 1e-60. It is a precision-dependent diagnostic
threshold, not a full-support gate.

| candidate | digits | runtime | resolved modes | lambda_min resolved | eig residual |
|---|---:|---:|---:|---:|---:|
| PS+V_A | 80 | 451.2841081 s total; 347.0384548 s eigensolver | 48 | 6.6964607367675085e-60 | 1.8872605588228927e-80 |
| PS+V_A | 120 | 447.7414750 s, TIMEOUT | NOT_RUN | NOT_RUN | NOT_RUN |
| PS+V_A | 200 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 80 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 120 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Full | 200 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

The completed PS row also reports maximum eigenvalue
0.65161924940335072627794844348808834144, global-eigenvalue trace error
1.1596417737553576e-80, and no non-finite result.

# 9. Sector-union spectrum comparison

For PS at 80 digits, the sorted 256 global eigenvalues agree with the
concatenated four-sector eigenvalues:

- resolved global count: 48;
- resolved sector-union count: 48;
- maximum absolute difference: 4.2168791772922093e-81;
- maximum log10 difference among resolved paired modes:
  1.9517689816295757e-25;
- global eigendecomposition residual: 1.8872605588228927e-80.

Near-zero modes below 1e-60 were not interpreted by relative error. The
120-digit timeout and all Full rows are NOT_RUN, so no all-ladder or
PS-versus-Full global-spectrum claim is made.

# 10. PS-vs-Full conditioning comparison

The completed global row is PS only, so this audit does not provide a
completed side-by-side global spectrum at every requested precision.
Existing high-precision sector evidence remains:

| candidate | high rows | minimum resolved mode | status |
|---|---|---:|---|
| PS+V_A | 800/900 and 1000/1200 digits | 5.5183273131200776e-598 | FULL_SUPPORT_CONVERGED |
| Full | 800/900 digits | 1.0195494813436373e-612 | FULL_SUPPORT_CONVERGED |

The 80-digit PS global row resolves only 48 modes above its declared
diagnostic threshold, as expected from the approximately 10^-598 smallest
sector mode. The timeout is a cost result, not evidence of a PS-specific
construction bug. Full was not globally eigensolved under this audit.

# 11. Time-budget compliance

The hard budget was 900 seconds. The watchdog completed in 899.0290027
seconds, with budget_compliance = true and status
DENSE_LOW_PRECISION_COST_BOUNDED_SKIP.

Recorded rows:

- PS at 80 digits: completed;
- PS at 120 digits: timed out;
- PS at 200 digits: not started;
- Full at 80/120/200 digits: not started.

No 400-, 800-, 1000-, or 1200-digit dense global calculation was attempted.
No high-precision dense target was launched.

# 12. Final AP diagnosis

**INSUFFICIENT_AP_PRECISION**

The completed independent PS global row agrees with the direct C4 blocks,
the production sectors, the global invariants, and the resolved sector-union
spectrum. The current unchanged worker separately converges for PS at
800/900 and 1000/1200 digits and for Full at 800/900 digits. The 120-digit
timeout is attributable to the hard cost budget and does not satisfy the
evidence required for AP_WORKER_PS_SPECIFIC_BUG or AP_FAIL_GATE_BUG.

The classification is supported by the earlier fail-closed lower-precision
rows and the current high-control sector convergence. Because the bounded
global audit did not finish the Full side, this report does not claim a
complete six-row global comparison.

# 13. Dense-global conclusion

**LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT**

The exact C4 unitary equivalence makes the sector union the same mathematical
spectrum as the global matrix. The completed independent 80-digit PS row
provides the requested end-to-end global check for one candidate before the
budget stopped the ladder. The high-precision sector rows resolve the
inverse-sensitive tail that the global 80-digit row cannot resolve. A
700--900-digit dense global run would duplicate the sector spectrum and is
not scientifically required by the current evidence.

# 14. Code changes

Changed only diagnostic/test support:

- extended scripts/diagnose_ps_va_ap_worker.py to record global invariants,
  production block matches, global eigenvalues, and sector-union metrics;
- added scripts/run_independent_global_block_audit.py with a subprocess
  watchdog and incremental artifact saves;
- added three cheap direct-global/C4 tests to
  tests/test_ap_worker_equivalence.py.

No production source, worker equations, C/w definitions, security model,
model checkpoint, probabilities, geometry, channel, or lifecycle gate was
changed. No new dependency was added.

# 15. Tests / verification

The following checks passed:

- GlobalWeightedGramAuditTests: 3/3;
- py_compile for both audit scripts and the focused test file;
- JSON validation for independent_global_block_audit_20260912.json;
- git diff --check.

The broader tests.test_ap_worker_equivalence module remains blocked by three
missing ignored historical/corrected artifacts in this checkout. Those files
were not recreated. This is an environment/provenance blocker, not a failure
of the new cheap global tests.

# 16. Lifecycle

**NOT_READY_FOR_PUBLICATION_SCALE_RUNS**

Adaptive training, final-test access, publication-scale evaluation, baseline
selection, threshold approval, full-Z backward, reverse VJP, and new security
or novelty claims remain closed.

# 17. Remaining blocker

The three-state exact PS+V_A adaptive ranking remains incomplete because the
minimum sector-level AP precision for the frozen PS+V_A source-moment row has
not yet been reduced to the smallest reproducible ladder and rebound into
the median full-Z security point.

# 18. Recommended next task

Determine the minimum sector-level AP precision required for the frozen
PS+V_A median candidate, compute its exact C,w, and then evaluate only the
median full-Z security point. Do not execute this task in this report.
