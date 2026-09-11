# Session Handoff

## Latest update: 2026-09-11 C4 forward tangent

The isolated `EXPERIMENTAL_DIAGNOSTIC_ONLY` C4 constrained-solve forward
tangent is implemented in `src/cvqkd/c4_constrained_tangent.py` and recorded
in `results/c4_constrained_forward_tangent_20260911.json`. Cheap fixtures
passed. The recovered Case-A PS target resolves 256/256 modes at 800 digits
and matches corrected AP dC/dw/dJ within 1e-8; the row takes 1181.1304 s.
Classification: `CONSTRAINED_TANGENT_VALIDATED` for this local diagnostic only.
The lower 200/400/600 precision rows fail closed before full support resolves.
The old reverse remains invalid and the target explicit R/J comparison did not
complete within its bounded runtime window.

Keep `NOT_READY_FOR_ADAPTIVE_TRAINING` and
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. Do not run reverse repair, full-Z
backward, optimizer steps, training, final-test access, or publication-scale
evaluation. The next bounded numerical task is the remaining GS-real,
GS-imaginary, and V_A forward directions.

Date: 2026-09-11

Lifecycle: NOT_READY_FOR_PUBLICATION_SCALE_RUNS

## Completed

- Added outage-aware active-only evaluation/training behavior: \(T=0\) never
  reaches policy features, outage raw \(K=0\), active gradients remain live.
- Added signed mean_difference_T beside relative delta_T diagnostics.
- Audited the prior Case B/C delta_T anomaly: paired retained samples now
  define delta_T; proposal-vs-admitted sampling remains proposal_delta_T.
- Audited the exact Gram failure: no duplicate states or zero probabilities;
  the cause is FLOATING_POINT_ROUNDOFF plus NUMERICAL_ILL_CONDITIONING.
- Short differentiable-path investigation localized failure at the C4
  positive-definite eigengate; sqrt/inverse-sqrt, C, w, and backward are not
  reached in complex128. Classification:
  EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128.
- Focused outage/composite tests: 20 passed.
- Ran four exploratory composite-channel cases at N=1000:
  deterministic A, explicit-v_sc B, Rician-pointing C, and AoA-outage D.
- Saved results/exploratory_cases_20260910.json with EXPLORATORY_ONLY status.
- Added the isolated corrected AP custom-backward validation runner and
  cheap artifact. Four small fixtures, separate C/w components, combined
  VJP, and real/imaginary complex-alpha checks passed at 80 digits.
- The four PS/GS-real/GS-imag/V_A target mappings passed structural preflight.
  One bounded 800-digit PS target attempt resolved 256/256 AP modes but the
  custom combined VJP failed materially (`3.3995e+102` versus AP
  `0.001774...`) after `25653.3898618 s`; the target suite was stopped.

## Numerical result boundary

Corrected Case A and a bounded corrected B-D source-moment/full-Z security
subset are now recorded as evaluation-only evidence. The new B-D artifact uses
16 reconstructed evenly spaced active rows per case because the prior ignored
artifact and exact indices were unavailable. The broader gradient/optimizer
focused selection remains FAILED with four pre-existing
FULL_SUPPORT_FALLBACK_EVALUATION_ONLY errors.

## Changed files

- src/optimization/trainer.py
- src/channel/diagnostics.py
- tests/test_pipeline_consistency.py
- tests/test_composite_channel.py
- results/exploratory_cases_20260910.json
- current-state evidence/decision/project/next-action documents
- scripts/recompute_corrected_bd_security.py
- corrected B-D evidence/decision/project/next-action documents

## Open blockers

1. Freeze one author-approved common-turbulence scenario and its profile,
   aperture-averaging, AoA, and effective phase mappings.
2. Fix and revalidate full-support AP custom-backward reverse stability at the
   approximately `10^-618` Gram-eigenvalue scale.
3. Keep learned training and publication lifecycle closed.
4. Do not weaken the complex128 gate or enable AP fallback for training.

## Exact next task

Investigate the failed full-support AP custom-backward reverse path; do not
start adaptive training or full-Z backward.

## Research refinement

The full-support differentiable source-moment audit is recorded in
FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md. It confirms the
frozen C4 tangent equations, quantifies the approximately 10^-618
conditioning scale, and ranks an exact constrained-solve tangent followed by
compiled multiprecision as the primary path.

The next implementation must start with the isolated forward tangent and a
corrected three-way PS comparison: AP finite difference, AP tangent, and
custom reverse. Keep reverse repair, full-Z backward, and adaptive training
closed until that diagnostic passes.
