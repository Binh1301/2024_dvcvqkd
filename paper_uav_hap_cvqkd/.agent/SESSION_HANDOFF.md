# Session Handoff

Date: 2026-09-12

## Latest completed task: EVID-0081 / DEC-0065

The authorized frozen PS+V_A median source-moment task is complete. The
existing repaired-objective checkpoint and direct binary64 candidate inputs
were reverified. The 1050 diagnostic and 1250/1450 acceptance pair resolved
all 256 support modes and passed the frozen C/w convergence rule.

Authoritative values:

```text
C_PSVA = 0.8610813007552428909072445071897962976560950806268
w_PSVA = 0.0067220381757562110710871873472856506670610666856165
```

The one exact median full-Z point passed `Z_L <= Z_star <= Z_U` and returned
raw `K=+0.0003801578161163992`. Exact median ranking is
`PS_VA_MEDIAN_BEST`, with PS+V_A > Full > MB. This is median-only evidence,
not a three-state or publication claim.

Artifact:
`results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`, SHA-256
`9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`.
Report:
`docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md`.

Recommended next task, requiring separate authorization: exact poor + good
ranking only. Do not execute it from this handoff.

## Historical decision

EVID-0080 and DEC-0064 select exactly
`DIRECT_HIGHER_PRECISION_SECTOR_RUN` for the remaining frozen PS+V_A
source-moment blocker.

The next source-moment ladder starts at 1050 decimal digits, with acceptance
at 1250 and confirmation at 1450 digits using the existing four 64-by-64 C4
sectors and exact serialized binary64 inputs. The repository's frozen
`1050,1250,1450` ladder remains unchanged; existing 800/900 and 1000/1200
rows are diagnostic evidence and are not silently promoted to the selected
protocol row.

After source-moment convergence, evaluate only the median full-Z point. Do
not run a dense high-precision global eigensolve, 1600/2000-digit escalation,
outcome-driven mixed-precision aggregation, an Arb migration, a
source-moment reformulation, training, baseline selection, final-test work,
or publication-scale evaluation.

## Historical exact next task

`DETERMINE_MINIMUM_SECTOR_AP_PRECISION_FOR_FROZEN_PS_VA` is complete under
EVID-0081/DEC-0065. Do not rerun the ladder or execute any dense global
high-precision alternative.

## Reports and evidence

- `docs/DEEP_RESEARCH_MINIMUM_PS_VA_SECTOR_PRECISION_20260912.md`
- `docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md`
- `results/independent_global_block_audit_20260912.json`
- `results/ps_va_worker_instrumented_800_900_20260912.json`
- `results/ps_va_worker_instrumented_1000_1200_20260912.json`
- `results/full_worker_instrumented_800_900_20260912.json`

Research memo SHA-256:
`5d9a58d8d437fe0f14756316c14a2128ce429c4d2b162204d4f7cfe3d1cc65d4`

Frozen model-spec SHA-256:
`8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`

## Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`. Keep reverse
VJP/full-Z backward, adaptive or production training, baseline selection,
threshold approval, final-test access, publication-scale evaluation, and new
security or novelty claims closed. No production security equations or
lifecycle gate was changed.
