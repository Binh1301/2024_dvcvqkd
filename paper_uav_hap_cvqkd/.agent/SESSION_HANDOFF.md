# Session Handoff

## Latest completed task

Date: 2026-09-28

EVID-0093 / DEC-0077 completed the authorized AP coverage attempt. It is
restartable but blocked by the existing one-hour AP subprocess timeout.

- Global exact coverage: 19/143.
- Local high-priority mesh: 26/59.
- Boundary: 9/18.
- Uniform baseline roster: 8/43.
- Best exact interior remains `(nu_raw,V_A)=(.24,1.95)` with
  `SKR=2.1544608008872113e-05`.
- Best tested boundary is `nu_raw=.275`, `V_A=1.939393833980765`, with
  `SKR=2.1507318654867557e-05`.
- Timeout failures and incomplete points are recorded in the three
  `*_failed_or_incomplete.csv` ledgers.
- No interpolation, surrogate, Adam, boundary refinement, baseline selection,
  training, or publication-scale run occurred.
- Classification remains `GLOBAL_OPTIMUM_UNRESOLVED`.

The earlier global diagnostic remains recorded below.

EVID-0092 / DEC-0076 completed the authorized cache-bound global joint MB/V_A
coverage diagnostic. It is fail-closed; global certification is unresolved.

- Requested global grid: 143 rows, 15 exact cache evaluations.
- Requested boundary grid: 18 rows, 5 exact cache evaluations.
- Requested uniform scan: 43 rows, 5 exact cache evaluations.
- No fresh AP source point, interpolation, surrogate, Brent/golden search, or
  Adam ran.
- Best exact point currently tested remains `(nu_raw,V_A)=(.24,1.95)`.
- Classification: `GLOBAL_OPTIMUM_UNRESOLVED`.

The earlier exact joint MB/V_A diagnostic remains recorded below.

EVID-0091 / DEC-0075 completed the authorized exact joint MB/V_A diagnostic.

- Feasible curved region mapped with hard peak and V_A config bounds.
- 25-point exact feasible landscape completed.
- Local exact refinement completed.
- Best tested local point: `(nu_raw,V_A)=(.24,1.95)`.
- SKR: `2.1544608008872113e-05`.
- Local stencil supports a local interior candidate, not global optimality.
- No global optimizer, baseline selection, or Adam ran.
- Common ensemble/hash, positive-PMF, peak, phase-noise, and exact C,w rules
  remained unchanged.

Artifacts:

- `results/joint_mb_va/feasible_boundary.csv`
- `results/joint_mb_va/joint_landscape.csv`
- `results/joint_mb_va/local_refinement.csv`
- `results/joint_mb_va/local_refinement.json`
- `results/joint_mb_va/run_report.json`

Global diagnostic artifacts:

- `results/joint_mb_va_global/run_report.json`
- `results/joint_mb_va_global/global_landscape.csv`
- `results/joint_mb_va_global/feasible_boundary.csv`
- `results/joint_mb_va_global/boundary_search.csv`
- `results/joint_mb_va_global/interior_search_log.csv`
- `results/joint_mb_va_global/uniform_optimized_baseline.csv`
- `results/joint_mb_va_global/local_refinement.csv`
- `results/joint_mb_va_global/optimum_certification.csv`
- `results/joint_mb_va_global/objective_decomposition.csv`
- `results/joint_mb_va_global/gh_convergence.csv`
- `results/joint_mb_va_global/ap_coverage/local_report.json`
- `results/joint_mb_va_global/ap_coverage/local_failed_or_incomplete.csv`
- `results/joint_mb_va_global/ap_coverage/ap_batch_timeout_summary.json`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary_report.json`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary_failed_or_incomplete.csv`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform_report.json`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform_failed_or_incomplete.csv`

## Verification

The current focused run passed 15 tests (9 exact-MB/reconciliation and 6
global-joint tests); joint/AP scripts were compiled and exact source/cache
jobs were run. AP timeout failures are recorded. No physical/security
equations changed.

## Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Next action

Only a separately budgeted exact-source continuation with an explicit timeout
decision remains; certify the full domain and uniform optimized baseline before
claiming a joint optimum. Do not run Adam automatically.

## Worktree caution

The worktree contains prior user/channel/MB changes and untracked scripts.
Preserve unrelated files.
