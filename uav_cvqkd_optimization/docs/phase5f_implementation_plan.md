# Phase5F technical lookup/cloud/solver integration

User authorizes technical integration and labeled TEST_ONLY dry runs, not new
lookup evaluations, mission assumptions, candidate approval or paper-mode.

- [x] Snapshot old artifacts; read Phase5E CSV/NPZ/package/metadata directly.
- [x] Add pinned Phase5E package loader: verify hashes, units/noise/HAP/grid,
  raw rates/T/evidence agreement; exact-node graph queries only, no historical
  fallback or implicit interpolation/admission.
- [x] Add separate pending config with missing mission/cloud inputs and a
  TEST_ONLY fixture config with explicit software-only values. Do not modify
  paper.yaml or official cloud candidate approvals.
- [x] Reuse Gaussian CLWC/3D slab LOS/rotor energy/graph/shared Scenario and
  run_methods. Effective scheduled rate=z*R_clear; store R_clear as retained
  rate and m=m0*z so loss is accounted once. Snapshot at destination q_k,t=k*dt.
- [x] Test clear/blocked/moving clouds, off-endpoint LOS, static/dynamic
  equivalence, same realization and source for all four algorithms, timing,
  finite-size accumulation, speed/energy and deterministic replay, mismatch
  and missing paper-input rejection.
- [x] Run TEST_ONLY CLI outside results/, create provenance/sealed technical
  artifacts; full suite/review/preservation verification and Vietnamese report
  with remaining author decisions and Phase6 status.

Smallest implementation: new adapter/technical runner and two configs; existing
scientific modules remain unchanged. Fixture numbers are not scientific
recommendations or mission defaults. Native CV-QKD backend is never invoked.

Execution: initialmissing-entrypoint RED→GREEN; integration13cases PASS, then
review reproduced source-object numeric injection and per-cluster drift override.
Both pinned RED→GREEN; nullfinite-block rejection added. Final16focused/193full
tests PASS (full12.21s). ActualCLI TEST_ONLY artifacts generated in test_artifacts,
independently verified with no research-result additions or protected-file changes.
No native SKR evaluation, code/model rewrite, paper run, commit or push.
