# Session Handoff

Date: 2026-09-01

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
access, held-out evaluation, threshold approval, production `src/cvqkd`
change, security-functional change, or frozen-model change occurred.

This handoff is lower authority than active specifications, source, frozen
configs, machine-readable artifacts, and `docs/PROJECT_STATE.md`.
