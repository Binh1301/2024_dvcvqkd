# Next Actions

## Current Gate

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

The active model was amended on 2026-09-09 to use exogenous
`(T,epsilon_base)`, external fixed `Cn_phi2`,
`epsilon_total=epsilon_base+c_phi*V_A`, and a full-physical-interval Holevo
maximizer. The amendment record is
`docs/MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md`. The default configuration has no
approved `Cn_phi2` value and fails closed.

## Exact Next Permitted Action

Obtain and freeze a provenance-backed SI `Cn_phi2` for each scenario, then
write and independently review a new numerical certification protocol for the
amended functional. At minimum it must establish full-interval maximizer
grid/refinement convergence, boundary/domain failures, nonsmooth switching
behavior, and the causal `epsilon_base -> V_A -> epsilon_total` path. It must
also obtain a primary-theory justification for the full-interval security
interpretation.

## Historical V3 Review

Perform a separate numerical/security-method review. The review must decide
whether the research should use:

1. a different numerical regularization architecture whose security meaning
   is documented;
2. a mathematically equivalent smoother formulation of the frozen functional;
3. an explicit, prospectively frozen conditioning/admissibility strategy; or
4. a narrower paper claim that avoids unsupported continuous-path
   conditioning.

The review must distinguish numerical stability, mathematical support, and
security-model assumptions. It must quantify any excluded transmitter/domain
states and may only propose—not silently apply—changes to the threshold,
functional, admissible domain, or paper claim.

## Stop Conditions

- Do not rerun or retune V3 after observing its result.
- Do not execute the full 12-segment V3 cycle.
- Do not automatically create V4 or expand precision, runtime, Taylor order,
  cluster size, block schedule, or subdivision limits.
- Do not approve candidate `1e-13` or reactivate historical `1e-12`.
- Do not silently regularize or replace the discrete-modulation security
  functional.
- Do not perform publication training, the optimized-MB grid, baseline
  selection, final-test access, or held-out evaluation.
- Do not assign `Cn_phi2` by copying/reusing the Hufnagel--Valley/beam-wander
  `Cn2(h)` value.
- Do not use an old fixed-`Z_lower` artifact as full-interval Holevo evidence.

## Preserved Facts

- Active amended model SHA-256:
  `f3c118768fc3e4fe5e308d3e660507f815526b86e442100945ab47e6924ca974`.
- Historical pre-amendment model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- MI remains `N_MC=2048`.
- Exact-tau V2.2 point result remains valid and need not be recomputed unless
  an input or oracle producer changes.
- V3 result SHA-256:
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`.
- Proposed engineering conclusion pending review:
  `HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`.
- Final test remains inaccessible and untouched.
