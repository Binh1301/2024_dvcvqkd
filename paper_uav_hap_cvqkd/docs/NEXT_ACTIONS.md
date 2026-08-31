# Next Actions

## Current Gate

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Publication-scale execution, optimized-MB/baseline selection, final-test
access, and threshold approval remain unauthorized.

## Exact Next Action

Implement and test a validated numerical enclosure `eta_num` for complex C4
Gram assembly and Hermitian eigenvalue/inertia evaluation. Compose it with the
existing analytic derivative enclosure and fail-closed adaptive bisection.

### Required proof obligations

- Outward rounding or a rigorously justified equivalent covers complex
  coherent overlaps, weighted Gram assembly, and all arithmetic error.
- Hermitian eigenvalue separation or inertia is verified, not inferred from an
  ordinary float64 residual.
- Every accepted segment satisfies a proved separation bound using
  `R_I = eta_num + h L_I`; unresolved intervals fail closed.
- ReLU crossings, PS/VA/GS normalization, and physical energy scaling remain
  enclosed.
- Tests include no-crossing, known crossing, ill-conditioned full-rank, and
  resource-exhaustion cases.

### Pass criteria

- `eta_num` is executable, provenance-bound, and mathematically documented.
- Every accepted interval is enclosed away from the hard threshold.
- All rounding/eigensolver/resource failures reject without changing frozen
  equations or tolerance.
- The full dynamic suite remains green in the locked environment.

### Fail criteria

- Endpoint equality, dense sampling, empirical safety factors, or unverified
  complex128 residuals are used as proof.
- A candidate threshold is approved/activated or the functional is regularized.
- Final-test, validation selection, optimized-MB, or training data is touched.

## Following Actions

1. Integrate the verified guard transactionally with full model, Adam, dual,
   and RNG rollback tests.
2. Obtain independent threshold-approval review using only the frozen roster
   and declared oracle subset.
3. Commit the minimal portable evidence set for clean-clone reconstruction.
4. Only after certification passes, run validation-only optimized-MB and
   baseline selection.
5. Publication training and final held-out evaluation remain later stages.

## Preserved Facts

- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- MI remains `N_MC=2048`.
- Independent oracle passes 4/4 declared fixtures.
- Realized whole-segment certificates remain 0/12 because `eta_num` is absent.
- Candidate `1e-13` remains proposed and unapproved.
