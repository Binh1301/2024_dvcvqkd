# Session Handoff

Date: 2026-09-10

## Current-Manuscript Amendment (active)

The active functional changed on 2026-09-09 under the user-directed current
manuscript source of truth. Read these before any task action:

1. `docs/MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md`;
2. `docs/FINAL_MODEL_SPEC.md` (SHA-256
   `f3c118768fc3e4fe5e308d3e660507f815526b86e442100945ab47e6924ca974`);
3. `docs/MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md` (SHA-256
   `fae9c754474183f4214db5848c834739278961f6853622b12c7a18eef0bd2776`);
4. `docs/PROJECT_STATE.md`.

The exogenous state is now `(T, epsilon_base)`. `Cn_phi2` is a separate,
fixed SI phase-scenario input; it must not be derived from beam-wander/HV
`Cn2(h)`. The action path is
`epsilon_total=epsilon_base+c_phi*V_A`, with the identical total tensor sent
to MI and the full-physical-interval Holevo maximizer. The default config has
`Cn_phi2: null`, so numerical entry points must fail closed.

No prior numerical artifact certifies this amended functional. Before any
targeted numerical validation, freeze an author-provided `Cn_phi2`, an
interval-maximizer certification/convergence protocol, and obtain independent
security review. No training, baseline selection, final-test access, held-out
evaluation, or publication-scale result is authorized.

## Authoritative Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

V3 is complete and failed its frozen four-row feasibility gate. Do not rerun,
retune, expand to all 12, or automatically create V4. Candidate `1e-13`
remains proposed/unapproved; historical `1e-12` remains invalid/unapproved.

## Current Evidence

- Frozen model:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- V3 config:
  `878a17f51734e2c1565276b5ee13d8a0cf2b7bfedfab5f6a7749409b0ee57a20`.
- V3 final manifest:
  `5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`.
- V3 result:
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`.
- Exact-tau V2.2 result:
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`.
- MI remains certified at `N_MC=2048`.

V3 produced `0/4` complete certificates, `0/4` crossings, `4/4` resource
limits, `4/4` early path-domain certificates, `7/3` attempted/completed
nodes, and 52 durable Schur events. Runtime was `2438.1743897000006 s`
against the frozen `1800 s` limit. Two rows met the two-second
watchdog-return grace; two were `WATCHDOG_CONTRACT_BREACH`, with maximum
overshoot `637.7792758 s`. Completed roots left `53,52,53` unresolved far
modes despite 38--43x tighter paired dependency radii.

The current proposed engineering conclusion is:

`HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`

It is pending independent numerical/security-method review and is not a
threshold or security approval.

## Exact Next Permitted Action

Conduct that separate review to choose among a documented regularization
architecture, a mathematically equivalent smoother formulation, a
prospectively frozen admissibility strategy, or a narrowed paper claim. Do not
silently change the physical/security functional or domain.

No publication training, optimized-MB search, baseline selection, final-test
access, held-out evaluation, or threshold approval occurred. The historical V3
run did not change production code; the later active 2026-09-09 amendment did
change production `src/cvqkd` and the frozen model as documented above.

This handoff is lower authority than active specifications, source, frozen
configs, machine-readable artifacts, and `docs/PROJECT_STATE.md`.
