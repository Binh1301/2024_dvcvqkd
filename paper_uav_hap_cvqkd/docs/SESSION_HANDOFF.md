# Session Handoff

## Latest completed task: EVID-0081 / DEC-0065 (2026-09-12)

The authorized frozen PS+V_A median source-moment task is complete. The
existing repaired-objective checkpoint and direct binary64 candidate inputs
were reverified. The 1050 diagnostic and 1250/1450 acceptance pair resolved
all 256 support modes; the acceptance pair passed the frozen convergence
criterion.

Authoritative source moments:

```text
C_PSVA = 0.8610813007552428909072445071897962976560950806268
w_PSVA = 0.0067220381757562110710871873472856506670610666856165
```

The one exact median full-Z point passed `Z_L <= Z_star <= Z_U` and returned
raw `K=+0.0003801578161163992`. Exact median ranking is
`PS_VA_MEDIAN_BEST`, ordered PS+V_A > Full > MB. This is median-only
evidence; it does not establish the poor/good ranking or a publication claim.

Artifact:
`results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`, SHA-256
`9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`.
Report:
`docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md`.

Recommended next task, requiring separate authorization: exact poor + good
ranking only. Do not execute it from this handoff. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive training remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`.

## Historical research-only decision: 2026-09-12

EVID-0080 and DEC-0064 select exactly
`DIRECT_HIGHER_PRECISION_SECTOR_RUN` for the remaining frozen PS+V_A
source-moment blocker. The next source-moment ladder starts at 1050 decimal
digits, with acceptance at 1250 and confirmation at 1450 digits, using the
existing four 64-by-64 C4 sectors and exact serialized binary64 inputs. The
frozen `1050,1250,1450` protocol remains unchanged. Existing 800/900 and
1000/1200 rows are diagnostic evidence, not the selected protocol row.

After source-moment convergence, evaluate only the median full-Z point. Do
not run a dense high-precision global eigensolve, 1600/2000-digit escalation,
outcome-driven mixed precision, Arb migration, source-moment reformulation,
training, final-test work, or publication-scale evaluation. The research memo
did not execute a numerical run or change code, equations, model, security
scope, or lifecycle state.

Report:

- `docs/DEEP_RESEARCH_MINIMUM_PS_VA_SECTOR_PRECISION_20260912.md`
- `docs/DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md`
- `docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md`

Research memo SHA-256:
`5d9a58d8d437fe0f14756316c14a2128ce429c4d2b162204d4f7cfe3d1cc65d4`

## Current numerical decision: 2026-09-12

EVID-0078 and DEC-0062 supersede the earlier worker-bug interpretation for
the current median numerical question. The unchanged worker now has
successive high-precision full-support rows for PS and Full, and the
independent direct 100-digit global construction reproduces the C4 structure.
The dense-check decision is
LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT. The immediate
AP-blocker classification is INSUFFICIENT_AP_PRECISION.

EVID-0079 and DEC-0063 record the bounded follow-up. The watchdog completed
the frozen median PS+V_A global row at 80 digits, timed out PS at 120 digits,
and did not start PS at 200 digits or any Full row. It finished in
899.0290027 of the 900-second budget with status
`DENSE_LOW_PRECISION_COST_BOUNDED_SKIP`.

The completed PS row passed the independent global invariants, Fourier
off-block check, production-sector comparison, and resolved
global-spectrum/sector-union check. This is structural diagnostic evidence,
not a support certificate or a complete six-row global audit.

The exact next numerical task recorded in this historical section was
`DETERMINE_MINIMUM_SECTOR_AP_PRECISION_FOR_FROZEN_PS_VA`; it is complete under
EVID-0081/DEC-0065. Do not rerun the dense 700--900-digit global target. This
handoff remains research-only; all lifecycle gates stay closed.

## Historical update: 2026-09-12 PS+V_A full-support blocker root-cause audit

EVID-0076 and DEC-0060 record the completed bounded repair. The old search
proxy was reproduced as `Z_proxy < Z_L` in `96/96` mode-state rows. The
repaired search calls the existing physical `[Z_L,Z_U]` interval and full-Z
maximizer, has zero repaired interval violations, matches the corrected
Case-A reference and existing exact anchor orderings, and passes finite
PS/GS/V_A gradient smoke.

The repaired PS+V_A and Full searches ran 50 analysis steps after passing their
20-step smoke with the same grid, weights, noise, beta, energy budget, and
initial PS/V_A branches. Full exceeded MB at all three available exact
poor/median/good states. The optimized PS+V_A AP jobs failed closed at the
full-support gate, so the complete adaptive ranking is not established.

Classification: `FULL_Z_SEARCH_OBJECTIVE_REPAIRED`.
Novelty: `CURRENT_NOVELTY_NOT_SUPPORTED`.
Lifecycle: `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
Adaptive training: `NOT_READY_FOR_ADAPTIVE_TRAINING`.

EVID-0077 and DEC-0061 record a read-only root-cause audit of the remaining
PS+V_A exact gate. The checkpoint has p_min approximately 0.00163--0.00228,
q_max/q_min approximately 2.66--4.50, and logit range below 1.51. The
weighted-Gram scale check does not support probability concentration as the
primary cause, and the worker receives direct binary64 hex inputs. A 300-digit
probe resolves 206 modes for both PS median and Full median; Full resolves at
800/900 digits, while PS remains FAIL_CLOSED there. Precision/conditioning is
relevant, but a PS-specific worker/solver failure remains unresolved.

Selected next category: `INVESTIGATE_AP_WORKER_BUG`.

## Report and artifacts

- Report: `docs/REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md`
- Result: `results/repaired_full_z_objective_analysis_20260911.json`
- Exact Full cache: `results/repaired_full_z_exact_jobs_20260911.json`
- PS+V_A exact failure: `results/repaired_full_z_ps_va_exact_failure_20260911.json`
- Blocker report: `docs/DEEP_RESEARCH_PS_VA_FULL_SUPPORT_BLOCKER_20260912.md`
- Blocker diagnostic: `results/ps_va_full_support_blocker_diagnostic_20260912.json`
- Global audit report: `docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md`
- Global audit artifact: `results/independent_global_block_audit_20260912.json`
- Producer: `scripts/run_repaired_full_z_objective.py`
- Focused tests: `tests/test_repaired_full_z_objective.py`

The result is analysis-only. No publication-scale training, final-test access,
reverse VJP, full-Z backward, baseline selection, or security certification
occurred.

## Historical blocker statement

The optimized PS+V_A checkpoint does not yet provide the complete three-state
exact C,w source-moment ranking. The later sector rows establish high-control
convergence at selected ladders and support AP precision/conditioning as the
current diagnosis rather than a demonstrated worker-specific defect; the
minimum reproducible sector precision is still not selected.

## Bounded task result

The bounded read-only
RUN_INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT was completed as EVID-0079.
The PS 80-digit row resolved 48 modes above 1e-60 and matched the sector
union; the PS 120-digit child timed out, and PS 200/Full were not started.
The result preserved the dense decision
`LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT` and the AP
diagnosis `INSUFFICIENT_AP_PRECISION`. Do not rerun this bounded audit or
escalate to a dense high-precision global eigensolve.

## Closed work

Keep the corrected AP worker, C/w definitions, channel physics, beta, phase,
epsilon, outage rule, and raw-K convention unchanged. Keep complete reverse
execution, full-Z backward, adaptive or production training, threshold
approval, final-test access, publication-scale evaluation, and new security
claims closed.
