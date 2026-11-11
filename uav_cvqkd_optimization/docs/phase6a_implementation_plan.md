# Phase6A Numerical Diagnostic Implementation Plan

**Goal:** Execute the author's approved synthetic-cloud mission with the sealed Phase5E lookup and the four existing algorithms, evaluating P1 and P2.

**Spec:** `docs/approvals/phase6a_author_request.txt` (verbatim supplied task).

**Architecture:** A distinct `phase6a_experiment.py` runner validates an explicit, hash-bound approval and configuration. Reuse the Phase5E sealed loader, Gaussian field, LOS slab intersection, IEEE rotor/energy graph, finite-size evaluator, baselines and Pareto DP. Leave TEST_ONLY and paper-mode guards unchanged. No quantum evaluator, regeneration or plots.

**Scope:** New runner, focused tests, diagnostic config/approval, new result directory and Vietnamese report. Existing mathematical models, profiles, paper.yaml and historical artifacts remain unchanged. Work in the user-named existing feature branch; no commit/push or workspace migration.

## Decisions before computation

- Original cloud recipe uses seed42. Generate the author-requested **new** seed20261108 realization using the exact pinned generation statements of that recipe; never relabel or overwrite its seed42 artifact. Domain16000x2000m,400x50 initial cell centers,400 components, original clipping retained. Freeze the linear90th percentile of this complete initial sampled domain before algorithms. Record saturation/ties honestly.
- Vertically uniform synthetic slab2000..4000m. Reuse `BlockageModel.projected_segment`; sample along the **3D** slab segment at <=20m and <=10m. Batch only Gaussian evaluation, not geometry or cloud-state equivalence. Compare all12100 node-times rather than a subset. Any disagreement blocks the full run without tuning.
- Cardinal+hover adjacency only: explicitly mask otherwise speed-feasible diagonal edges after the existing convergence-checked graph builder.
- Existing greedy score is bits minus lambda[bits/J]*J. Predeclare balanced normalized reward/energy scoring, equivalent to lambda=Rslot_max/Eedge_max (bits/J), where maxima use clear lookup rewards and allowed edge costs, before examining cloud/algorithm results. Dimensionless weight=.5 gives this ratio; save both scales and coefficient.
- Exact DP unchanged, no label caps/heuristic pruning. Execute in an isolated child with predeclared300s wall/4GiB RSS operational limits, sampled progress/labels. Limit breach aborts full DP, never returns an approximate solution. Then attempt a separately labeled reduced benchmark (5x5 subset,20slots) with the same models. These resource limits are computation safeguards, not physical mission inputs.
- Both objectives share each method's existing joint prefix computation; report eight selected solutions, not eight independent timing measurements.
- Frozen parent spec differs from historical AGENTS hash; record current hash and keep publication/model-sensitive work blocked. This task consumes only sealed numerical rates and author-approved synthetic mission inputs; no parent source model changes or security claims.

## Task1: input/preflight (TDD)
- [x] Save source request and pre-existing-file hash inventory (1267files, clean tracked worktree, feature branch).
- [x] Tests RED: missing Phase6A module caused collection failure before implementation.
- [x] Implement config, approval binding and scenario/preflight; tests GREEN. Reuse existing functions, no source model copies. Focused10cases PASS73.04s; full3D20/10m agreement all12100node-times.

## Task2: execution/output (TDD)
- [x] Tests: immutable output isolation, independent prefix arithmetic, shared inputs, resource-limit failure classification; new module began RED before implementation. Instrumentation/lock regressions subsequently verified RED→GREEN.
- [x] Implement bounded child execution and per-objective trajectory exports; tests GREEN, including real child baseline and forced watchdog.
- [x] Save preflight and frozen inputs before actual execution. PASS triggered actual run without another approval. Three baselines completed; exact DP in progress at this ledger update. Full/reduced statuses will be preserved, never substituted.

## Task3: validation/report
- [x] Fresh independent reviewer checks new runner and both attempts' actual artifacts; all8 full retry trajectories passed independent prefix QA.
- [x] Run full existing+new suite:206passed103.31s,0failures/errors/skips. Verify8selected solutions/800prefix rows and1267protected-file hashes unchanged.
- [x] Seal input/output manifests (22files per attempt); Vietnamese report includes full/reduced attempts, actual measurements, decisions, limitations, tests and next sensitivities.

## Review focus
Source recipe seed42 must not be silently called20261108; threshold clipping may produce tied90th percentile. No endpoint approximation, diagonal edges, double cloud erasure or dimensionally invalid lambda. Full-DP timeout is a failed full comparison, not a reduced-DP winner. No paper/security evidence promotion.

## Execution ledger / rulings

- Initial full run retained at `results/phase6a_baseline_20261109/`:6/8selected solutions. Tracemalloc-instrumented DP hit300s (last observedk93), and the separately labeled25node/20slot exact benchmark completed. This is a bounded execution failure, not a proof that the full problem is inherently infeasible.
- Ruling: user requires runtime and peak memory, not Python allocation tracing. Retry the identical approved scientific configuration and all four algorithms with10ms RSS telemetry, without tracemalloc. Preserve the failed attempt/source snapshot and use a distinct results directory. New no-tracing regression test RED→GREEN. No resource limit, model, scenario, lambda, algorithm or optimality policy changed. Cost if wrong: measured runtimes are instrumentation-dependent; both attempts and scopes must be reported separately.
- Initial review: no blocker for fixed approved inputs. Deferred minor: generic unequal-weight lambda algebra is outside this hash-bound weight0.5 run; fix and test before any different balance-weight experiment.
- Task2 complete: RSS retry finished8/8selections, fullDP exact-on-graph172.8151738s; initial failure preserved, no reduced-solution substitution.
- Ruling: Windows progress rename lock interrupted child10ms sampler late in retry; use uninterrupted parent100ms RSS252895232B as primary actual memory. Preserve executed source and stale progress/tmp; do not overwrite scientific data. Fix retry/error isolation with2RED→GREEN regressions; fullsuite206PASS. Cost/limit: sampled RSS is a lower bound on a continuous peak; no Python allocation peak claimed.
- Final review: independent initial/final-artifact QA plus bounded fix review PASS. No scientific/model/security evidence promotion. No commit/push.
