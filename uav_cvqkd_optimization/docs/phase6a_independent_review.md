# Phase6A independent review before execution

Final artifact status: **Independent QA PASS for 8/8 full-mission selections in the RSS-only retry**. The initial allocation-traced attempt remains preserved with its explicit 6/8 completion and full-DP wall-limit failure. No model, security, or publication evidence is promoted by this verdict.

What this change does: The new runner consumes the sealed Phase5E signed numerical rates, builds the author-approved synthetic cloud mission, and runs three baselines plus the existing Pareto DP. It keeps this execution in a separate `NUMERICAL_DIAGNOSTIC` scope and exports selected P1/P2 prefixes with accounting and provenance.

Review scope: `src/uav_qkd/phase6a_experiment.py`, its diagnostic configuration and approval binding, `tests/test_phase6a_experiment.py`, the saved author request and implementation plan, and the directly connected lookup loader, cloud, blockage, graph, rotor, propulsion, finite-size, evaluation, baseline, DP, and measurement code. The expected workload is one local mission with 121 nodes and 100 slots, with a separately labeled 25-node/20-slot fallback benchmark.

## Verdict

No blocking correctness or authorization issue found for the currently approved configuration. Proceed only after the runner's actual preflight and the main test run succeed. This review does not establish that preflight has already passed, that full DP completes, or that any Phase6A result exists.

The current configuration hash is `3b6cad3b92ab0ec5a019c72391487d7b288ba0294600f036e365449054d07e25`, matching the explicit approval file. Changed configuration content fails approval validation; paper mode and the existing TEST_ONLY interface reject this diagnostic configuration.

## Nonblocking finding

1. **The general normalized-weight conversion is reversed** (`src/uav_qkd/phase6a_experiment.py:145`).
   - What this is: The runner records the score as `w*r/Rmax - (1-w)*E/Emax`, and the existing greedy solver accepts `r - lambda*E` with lambda in bits/J.
   - Problem: The recorded score implies `lambda = (1-w)/w * Rmax/Emax`; the implementation uses `w/(1-w)`. At a hypothetical weight of 0.25 the two coefficients are `3*Rmax/Emax` and `Rmax/(3*Emax)`.
   - Fix: Reverse the ratio, and test the identity at a weight other than 0.5 if this general parameter remains supported.
   - If skipped: The frozen, approved value of 0.5 still produces exactly the correct coefficient and current results are unaffected. A future separately approved unequal weight would contradict its recorded interpretation.

## Findings checked

- The lookup loader validates the pinned package manifest, file coverage and hashes, raw-rate aliases, CSV/NPZ agreement, exact node policy, geometry, noise values and evidence scope. The runner reads rates and does not invoke the native quantum evaluator or lookup regeneration.
- The cloud generator executes the pinned original NumPy recipe with the new explicit seed. It retains clipping and computes one initial-domain empirical 90th percentile before trajectory optimization. Threshold ties and the saturated fraction are recorded; the scenario is not retuned to force 10 percent blockage.
- The full slab segment is found through the existing HAP-to-UAV intersection. Sample count uses the three-dimensional segment length, including the 2000 m vertical span. Both the 20 m and 10 m masks are compared at all 12,100 graph node-times; disagreement rejects the scenario.
- Cardinal and hover edges are explicitly retained after the shared convergence-checked energy builder. Diagonal edges are removed, allowed costs must remain finite, and the maximum edge speed is checked. The energy budget is derived from the actual rotor profile's hover power.
- Every method receives the same Scenario, and selected solutions use destination `q_k` at `t_k=k*dt`. Finite-size arithmetic retains signed clear rates, multiplies cloud availability once, counts only valid allocated signals, and subtracts the block penalty once for each evaluated prefix.
- At the approved weight of 0.5 the greedy coefficient is dimensionally consistent, determined from clear reward and feasible-edge scales before algorithm results, and not tuned afterwards.
- DP calls the existing solver without a label cap. Its isolated worker has declared wall-clock and sampled RSS watchdogs. Limit failures return no full solution, preserve telemetry and last observed progress where available, and do not silently replace the full comparison with reduced results. Operational sampling is not a continuous memory bound.
- Successful trajectory exports re-evaluate selected path accounting; exported rows separate emitted uses, allocated signals, valid signals, raw retained rate and erased rate. The reduced benchmark has a separate directory and explicit scope. Method timing is honestly described as joint P1/P2 computation.
- Output creation rejects existing directories and stays under the Phase6A result namespace. This review did not modify implementation, existing models, profiles, `paper.yaml`, lookup artifacts, or prior results.

## Independent checks performed

Command: `python -m pytest tests/test_phase6a_experiment.py -k 'approved_seed or approval_fails or output_refuses' -q`.

Result: **3 passed, 7 deselected**. The expensive mission-build fixture was intentionally not repeated because the main agent was already running it.

The main agent subsequently reported the complete new module suite as **10 passed in 73.04 s**, including the shared mission-build preflight, a real spawned baseline/export test, and a deliberately immediate wall-limit abort. This is execution evidence reported by the main agent, not a second independent rerun. The immediate abort does not predict whether the real full DP fits within 300 s or 4 GiB.

Additional in-memory probes passed without writing experiment results:

- A three-slot one-node scenario with retained rates `[0.2, -0.4, 0.3]` and availability `[1, 0, 1]` preserved the negative raw rate in export, erased its contribution once, and produced 1,600,000 valid signals and 400,000 asymptotic bits. The exported accumulated key matched the independently written requested penalty formula. Emitted uses were 3,000,000, pre-cloud allocated signals 2,400,000, and energy 30 J.
- An off-axis LOS from UAV `(0,0,1000)` to HAP `(1000,1000,20000)` intersected the slab at horizontal endpoints approximately `(157.8947,157.8947)` and `(52.6316,52.6316)`. Sampling used 102 points at the 20 m setting. A small analytic Gaussian distinguished this off-axis clear LOS from the blocked zenith LOS.

Not independently checked here: Full-mission preflight completion or the complete suite beyond the focused checks above, the real 300 s/4 GiB failure path, actual trajectories, final artifact hashes or Vietnamese report. These remain execution and post-run validation work. Full-DP feasibility and peak RSS between sampling instants remain unresolved until execution; this review supplies no security or publication admission.

## Initial executed run: independent artifact QA

Run directory: `results/phase6a_baseline_20261109/`. This section supersedes the pre-execution status above for this specific completed attempt.

The saved preflight is `CURRENTLY_VERIFIED_PASS`. **Six of eight full-mission algorithm/objective selections completed**, from Stationary, SKR-Greedy and Energy-Aware Greedy. Full Pareto DP returned `FAILED_COMPUTATIONAL_LIMIT`, reason `WALL_CLOCK_LIMIT`, with empty solutions and `NO_FULL_OPTIMUM_RETURNED`. It stopped after 300.108498 s of process wall time. Parent-sampled RSS peaked at 490,102,784 bytes; this was not an RSS-limit failure. Last observed progress was k=93, 7,599,858 generated labels, 5,665,180 dominated labels, zero heuristic discards, and a maximum completed frontier of 79,438 labels. The observed progress is not a completed full-horizon optimum.

| Method | Completed P1/P2 | K | Key bits | P1 bits/s | Energy J | Clear fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stationary | both | 100 | 25160.230296656 | 25.160230297 | 168484.217741082 | 0.77 |
| SKR-Greedy | both | 100 | 33623.045287247 | 33.623045287 | 169660.838380330 | 0.81 |
| Energy-Aware Greedy | both | 100 | 33276.467693714 | 33.276467694 | 169170.579780643 | 0.81 |
| Full Pareto DP | neither | — | unavailable | unavailable | unavailable | unavailable |

The separate 25-node/20-slot reduced DP finished `exact-on-graph`. Both selected objectives are zero bits, selecting K=1 under the solver's tie rule. It is explicitly marked `REDUCED_BENCHMARK_ONLY` and is absent from the full-mission comparison rows. It does not supply the missing two full-DP results.

Independent read-only checks passed:

- Saved configuration and input hashes matched. All producer hashes matched at the first QA check before the subsequent instrumentation change. The reconstructed scenario digest matched `ea1088ae527fba4251bb10fef75177220b64dae8d3e83bc73fc3d63e704f4f40`.
- All 121 graph coordinates and signed rates matched the existing Phase5E CSV and NPZ, and finite graph costs matched exactly the cardinal-plus-hover adjacency. The saved availability matrix is binary with shape 100 by 121.
- Every saved baseline CSV/JSON prefix was independently recomputed from the saved scenario arrays, without calling the evaluator or any optimizer. Checks covered positions, destination times, cloud state, retained/effective rate, raw contribution, emitted/allocated/valid signals, accumulated raw bits, one block penalty, nonnegative key yield, cumulative energy, feasibility, and P1/P2 units. Selected values were also no smaller than prior values on their own saved selected paths.
- The reduced trajectories were checked against the 600..1400 m subset and the first 20 saved cloud slots using the same independent arithmetic.
- The final manifest covered exactly 22 other files in the initial run directory, and every saved file hash matched. Both comparison CSVs contain three feasible rows and one explicit full-DP failure row with unavailable objective/key values. No full-DP trajectory CSV exists, and the report correctly counts six completed full-mission selections.

Two scenario limits are directly visible in the saved data. The frozen 90th percentile is exactly 15 mg/m3, the clipping ceiling; 15.785 percent of the original grid ties at that value, so percentile selection does not imply 10 percent blockage. Also, `100 * max(allowed edge energy) = 178289.389734819 J < Emax = 185332.639515190 J`: the energy budget cannot exclude any graph-feasible 100-slot path in this mission. Energy scoring can still change a greedy path, but this run does not test an active energy-budget constraint.

## RSS-only retry review

The main agent preserved the initial executed runner as `docs/phase6a_validation/executed_runner_with_tracemalloc.py`. Its hash independently matches the initial run's recorded runner producer hash. That archival copy explains why the later live runner hash differs; the initial sealed results were not rewritten.

The retry changes reviewed are confined to worker instrumentation and its output descriptions: Python allocation tracing is removed, process RSS is still sampled at 10 ms, progress is sampled approximately once per second, and the same parent watchdog remains in place. `python_peak_bytes` is explicitly null with `NOT_MEASURED` provenance. The solver calls, scientific configuration, approval, cloud and scenario construction, objective arithmetic, pruning, bounds, and output handling are unchanged. An AST comparison confirmed that only `_worker` and `run` function bodies changed; the latter changes only timing/memory descriptions.

No blocker found for a separately labeled RSS-only retry with the same scientific inputs. Removing allocation-tracing overhead is not evidence that the earlier failed run completed, and timings from the two instrumentation regimes must remain distinguished. The separately completed retry is checked below.

## RSS-only retry: independent final artifact QA

Run directory: `results/phase6a_baseline_20261109_rss_retry_20261110/`.

**Eight of eight full-mission algorithm/objective selections completed.** The saved preflight passed and all four methods returned feasible P1 and P2 solutions. The full Pareto DP finished with `exact-on-graph` classification, a null label cap, zero heuristic discards, and horizon 100. Its algorithm reported 10,436,173 generated labels, 8,072,853 dominated labels, and a peak retained frontier of 97,060 labels. This is graph optimization using the existing float64 dominance rules and numerical energy costs; it supplies no continuous-path or modulation global-optimality claim.

| Method | Completed P1/P2 | K | Key bits | P1 bits/s | Energy J | Clear fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stationary | both | 100 | 25160.230296656 | 25.160230297 | 168484.217741082 | 0.77 |
| SKR-Greedy | both | 100 | 33623.045287247 | 33.623045287 | 169660.838380330 | 0.81 |
| Energy-Aware Greedy | both | 100 | 33276.467693714 | 33.276467694 | 169170.579780643 | 0.81 |
| Pareto DP | both | 100 | 77040.107779909 | 77.040107780 | 170641.355579704 | 1.00 |

All selected mission durations are 1000 s. Each method computes both objectives jointly; the identical P1/P2 selections here do not represent independent timing repetitions. DP solver runtime was 172.815174 s and child process wall time 173.674637 s, below the unchanged 300 s watchdog. The **100 ms parent sampler's 252,895,232 bytes is the primary reported memory measurement**. The child metric of 235,724,800 bytes has incomplete sampling coverage, as disclosed below, and must not be presented as an uninterrupted 10 ms peak measurement. Neither metric certifies the continuous peak. Python allocation peak was explicitly unmeasured, not zero. The completed solver child exited with code zero.

Independent read-only checks passed without re-running any solver or cloud build:

- The retry manifest covered exactly 22 other files, and all hashes matched. All recorded input and live producer hashes matched at the time of that check, before the later telemetry-only fix. The executed runner is now preserved by its matching archival copy as described below. The saved approval/configuration hash and scenario digest matched the initial run.
- Every array and scalar in retry `scenario.npz` and `cloud_realization.npz` was exactly equal to its initial-run counterpart. Scientific inputs, availability and cloud realization were therefore unchanged across instrumentation regimes.
- All six baseline solution objects were exactly equal to the initial run's objects, despite timing changes.
- All eight selected trajectories were independently checked row by row against the saved scenario arrays. The checks recomputed signed contributions, erasure once, accumulated valid signals, one prefix penalty, yield, P1/P2 values, cumulative propulsion energy, node coordinates, destination time and feasibility. The selected value was no smaller than any earlier prefix on its own saved path. These accounting checks do not independently rerun the DP optimum search.
- Both final comparison CSVs contain four feasible rows whose objective and key values match the saved solutions. `completed_algorithm_objective_pairs` equals eight, and `reduced_benchmark` is null. The retry has no reduced-benchmark directory.
- The report retains `paper_mode=NOT_RUN`, `paper_admissible=false`, and `source_evidence_promoted=false`, and explicitly labels DP as a perfect-forecast oracle while greedy actions use the current slot. The DP-versus-greedy result is not an equal-information superiority claim.

Verdict: The reviewed configuration and final retry artifacts pass this independent correctness/accounting review. The threshold-clipping ties, globally nonbinding energy budget, forecast information difference, and finite-size proxy limits remain material interpretation constraints. The unequal-weight algebra finding remains irrelevant to the frozen weight of 0.5 and is deferred outside this approved scenario.

Not checked by this reviewer: The final complete repository test-suite execution, independent reproduction of every cloud sample, a separate DP optimization run, protected-history comparison beyond the inputs verified above, or the final Vietnamese report. The main agent owns those remaining report/check items. No implementation or result artifact was changed by this review.

## Telemetry incident and subsequent narrow fix

After artifact QA, the main agent disclosed a `PermissionError` / Windows `WinError 5` in the retry stdout while replacing `progress.tmp` with `progress.json`. It occurred near k=97; the final saved progress sample is at 148.041598 s. The exception stopped the child sampler thread, but the solver continued to completion and the independent 100 ms parent RSS watchdog continued throughout the 173.674637 s child lifetime. This review inspected the saved final progress and telemetry values; the precise stdout exception was reported by the main agent rather than independently reproduced during the actual run.

Consequently, the sealed child's RSS value is an incomplete sampled measure plus its final explicit RSS observation. It does not establish uninterrupted 10 ms sampling. The sealed generic `memory_scope` string alone does not disclose this interruption; the final human report must supply this qualification and use the independent parent value as the primary process-memory measurement. The objective, trajectory, feasibility, complete-label diagnostics, process exit and independent parent watchdog evidence remain valid. A separate optimization rerun is not needed to repair the interpretation of that telemetry.

The exact executed retry runner is archived as `docs/phase6a_validation/executed_runner_rss_retry.py`; its hash independently matches the retry input manifest. All other producer files still match the recorded retry hashes. The subsequent source fix changes only `_atomic` and `_worker`: it retries a transient replace lock up to three times, catches progress I/O errors so RSS sampling continues, and reports a progress-error count. The scientific configuration, optimizer calls and mathematics are unchanged. The sealed run artifacts remain untouched, and the later fix is not represented as having run during the completed retry.

Independent regression command: `python -m pytest tests/test_phase6a_experiment.py -k 'progress_file_lock or atomic_progress' -q`.

Result: **2 passed, 11 deselected in 1.95 s**. A simulated transient Windows replace lock was retried, and a simulated progress write error left the worker feasible with the error counted. No further blocker found in this narrow fix.
