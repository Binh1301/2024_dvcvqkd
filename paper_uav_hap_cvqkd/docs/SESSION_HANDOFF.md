# Session Handoff

Date: 2026-09-10

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

## Numerical result boundary

MI preflight values were finite. Full-Z Holevo/K was not completed because the
fixed 256-QAM fixture failed the complex128 fast gate at approximately
\(-1.57\times10^{-16}\); the arbitrary-precision fallback is evaluation-only
and was not run. The broader gradient/optimizer focused selection remains
FAILED with four pre-existing FULL_SUPPORT_FALLBACK_EVALUATION_ONLY errors.

## Changed files

- src/optimization/trainer.py
- src/channel/diagnostics.py
- tests/test_pipeline_consistency.py
- tests/test_composite_channel.py
- results/exploratory_cases_20260910.json
- current-state evidence/decision/project/next-action documents

## Open blockers

1. Freeze one author-approved common-turbulence scenario and its profile,
   aperture-averaging, AoA, and effective phase mappings.
2. Rebind numerical/security evidence to the composite post-action/full-Z path.
3. Keep learned training and publication lifecycle closed.
4. Do not weaken the complex128 gate or enable AP fallback for training.

## Exact next task

Cases B--D now completed bounded 16-active-state full-Z subsets using the
verified stable AP source moments. The next task is to design one mathematically
exact hybrid/custom-backward strategy for C/w with an explicit error bound or
controlled AP directional reference; do not execute it in this handoff.
