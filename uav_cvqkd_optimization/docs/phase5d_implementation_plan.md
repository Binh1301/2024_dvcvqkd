# Phase5D benchmark and finite-size implementation plan

Explicit user scope: actual50–100-point benchmark, full212-candidate policy, finite-size sensitivity, prepared full commands; no full2601 regeneration or paper-mode.

## Architecture and ownership

Main agent owns new `lookup_benchmark.py`, benchmark tests/config/artifacts, full readiness report and final validation. Independent worker owns new `finite_size_feasibility.py`, its tests/outputs and finite-size report. Both reuse native evaluator and accumulated finite_key; no existing scientific module/config is modified. No dependencies, pruning, fixed-winner shortcuts, or source generation.

- [x] Persist original snapshot and current lifecycle/source identities. Use inline TDD and one final independent review, no commits.
- [x] Test representative50-point selector, full-search serial/parallel result comparison, output/checkpoint ownership and explicit full-authorization gate.
- [x] Benchmark50 distinct radius-stratified actual grid points with212 candidates each, serial and2-process full search; measure cold/native initialization, point variability, wall/evaluation throughput, sampled RSS tree peak and process CPU time. No heavy tests during measurement.
- [x] Compare all candidates and selected identities between modes. Bind per-point records, source/pool/config hashes and code snapshot. Exact radial reuse and naive2601-per-point costs are separate projections; no assumed parallel speedup.
- [x] Prepare gated full driver/config/commands, deterministic order, immutable new output, per-point sealed checkpoints/resume, CSV/NPZ metadata, source labels. Do not execute full path.
- [x] Independently compute finite-size ncrit and strict integer nmin from actual pilot raw rates, epsilon sensitivity and reference n; retain fs symbolically via n=fs*eta_valid*c*T and required-rate-product tables. Exploratory axes do not become mission defaults.
- [x] Full suite after benchmark, independent review and regression fixes, verify protected files and pilot unchanged; deliver two Vietnamese reports and verification JSON.

## Review focus

Per-point vs radius-shared workload confusion; process-spawn startup/oversubscription and sampled-memory scope; parallel execution retaining full source roster; strict positivity at ncrit vs float cancellation; valid n versus transmitted signals/cloud double erasure; full-run authorization scope/config hash and cross-stage checkpoint binding.

The existing frozen-hash discrepancy and NOT_READY lifecycle remain; this fresh bounded diagnostic does not authorize a publication run. Old source/security labels remain unchanged. Finite-size remains a performance proxy.

## Execution record

Initial benchmark4 missing-module tests RED→GREEN. Finite worker19 focused cases passed, then nonempty-output regression RED→GREEN20; old development artifacts/source snapshot preserved and final analysis regenerated in a new verified namespace. Actual benchmark50points×212×2=21200freshcalls, serial217.2846s/parallel137.3368s, measuredspeedup1.5821. No other test suite ran during resource measurement.

Independent artifact review checked204 benchmark seals,552 inputs,60 producer entries,100 point seals and21200 records. Four future-executor findings were fixed after regression RED→GREEN (interruption recovery, CSV loader contract, family/evidence guards, detached NPZ provenance). Full controller/export tested only with mocked backend in tmp; no full scientific regeneration. Final167 tests passed in11.87s. All prior scientific files/pilot/configs preserved, no commit/push.
