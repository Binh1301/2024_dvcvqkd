# Session Handoff

## Latest completed task

Date: 2026-09-30

EVID-0098 / DEC-0082 completed the phase-off, no-AO HAP-UAV/Sayat forensic
diagnostic using only existing exact historical C,w.

- Current `T_eff=2.548668306761574e-4` (`35.9369 dB` loss).
- Dominant loss: `A0` (`32.7197 dB`), then pointing jitter (`2.7548 dB`).
- Best tested Uniform: `V_A=0.1`, `K=-4.3454249141616776e-5`.
- Best unconstrained diagnostic MB: `(nu_raw,V_A)=(0.15,3.5548673904962893)`,
  `K=5.389031300306879e-5`; it exceeds the current `V_A<=1.5` budget.
- Best tested budget-feasible MB: `(0.20,1.3833230302980657)`,
  `K=3.6522672467498285e-5`.
- Sparse-exact thresholds: `T_eff≈0.0898275`, `epsilon≈0.00540667`,
  receiver diameter `≈1.52931 m`.
- Exact continuous Uniform optimum remains unresolved; no new C,w or baseline
  selection was authorized.
- Artifacts: `results/hap_uav_sayat_forensics/`.

## Previous completed task

Date: 2026-09-29

EVID-0097 / DEC-0081 completed the phase-noise-only sensitivity diagnostic at
the original `D_r=0.08 m` aperture. The sweep `9.4e-18` through `1e-18` did
not make all three schemes positive at 19 km: Uniform remains negative at
`K=-4.975513931165798e-05` at `1e-18`.

- 8 historical exact Uniform candidates and 30 historical exact MB candidates.
- No new C,w/AP/Fock/Gram moments; no aperture, epsilon, beta, AO, or security formula changed.
- Full distance sweep intentionally not run.
- Artifacts: `results/skr_vs_link_distance/phase_noise_sensitivity/`.

## Previous completed task

Date: 2026-09-29

EVID-0096 / DEC-0080 completed the bounded historical-exact aperture
sensitivity diagnostic. Diameters `0.08--0.16 m` were tested at `L=19 km`;
Uniform and MB-without-AO stayed negative, so no all-positive aperture was
found and the full distance sweep was intentionally not run.

- 8 historical exact Uniform candidates and 30 historical exact MB candidates.
- `tau_zen=0.92`, `C_n,phi^2=9.4e-18`, `eta_AO=0.95`,
  `T_eff=<sqrt(T_raw)>^2`, direct-Z, and `maximize_full_interval=False`.
- No new C,w/AP/Fock/Gram source moments; no physics/security parameter changed.
- Artifacts: `results/skr_vs_link_distance/aperture_all_positive_diagnostic/`.

## Previous completed task

Date: 2026-09-29

EVID-0095 / DEC-0079 completed the historical exact distance envelope using
only audit-approved C,w; no new C,w was computed.

- Curves: Uniform, MB with AO, MB without AO.
- MB-AO bracket: [31,33] km; historical-exact estimate 31.409924920888173 km.
- Uniform and MB-noAO: no sign change over 19--100 km.
- Figure/artifacts: `results/skr_vs_link_distance/historical_exact_*`.
- This is diagnostic only; no final publication operation-distance claim.

The earlier EVID-0094 / DEC-0078 read-only repository-wide C,w audit remains
recorded below. No new C,w was computed and no active cache was modified.

- Indexed 6,876 C,w records and 77 hash-identifiable ensembles.
- Found 75 duplicate hash groups; duplicate C,w deltas were zero.
- Found 148 superseded/wrong-AP-w records.
- Matched 7 of 162 planned distance candidates safely: 3 Uniform and 4 MB;
  no Binomial match.
- Remaining feasible candidates: 139 without safe historical reuse.
- Artifacts are under `results/skr_vs_link_distance/`.
- MB pair-level report: `historical_mb_exact_pairs.csv` (71 records, 69 unique
  pairs, 4 safe current-distance matches).
- Classification: `AUDIT_COMPLETE_NO_NEW_SOURCE_MOMENTS`.

The earlier AP coverage attempt EVID-0093 / DEC-0077 is recorded below. It is
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
