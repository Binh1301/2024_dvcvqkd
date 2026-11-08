# Phase5F independent technical review

What this change does: It connects the sealed Phase5E lookup to the existing
Gaussian cloud, LOS blockage, finite-size proxy and four trajectory methods.
Execution is limited to explicitly labeled TEST_ONLY fixtures; paper-mode and
author approval remain blocked.

Review scope: `phase5f_integration.py`, its two configs and 13 tests, plus the
connected cloud, blockage, rate-provider, graph, finite-size, evaluator, baseline,
experiment runner and README contracts. Expected load is one bounded local
technical fixture, not a mission or publication run.

## Must fix

1. **Supplied lookup can bypass the seal validation**
   (`src/uav_qkd/phase5f_integration.py:122-124`).
   - What this is: The optional `source` argument avoids loading and validating
     the declared package again.
   - Problem: Only its directory and claimed package hash are checked. Starting
     with a valid source, `dataclasses.replace(source, _nodes=...)` with every
     rate set to `1.0` is accepted and produces Scenario rates of `1.0`, while
     the official first fixture node is `0.004955288516825029` bits/use. The
     object can therefore describe different numbers under the official source
     identity. This affects the public builder boundary; the CLI currently calls
     the safe loading branch.
   - Fix: Remove optional source injection and always load the sealed package,
     or compare all supplied numeric content against a freshly validated source.
     Removing the injection is the smaller complete fix.
   - If we skip it: A reused or constructed source object can silently invalidate
     the common-source claim for direct builder callers.
   - Regression: Change the node values of a copied official source while
     retaining its directory/hash; reject it, or make source injection unavailable.

2. **Per-cluster velocity can defeat the declared cloud drift**
   (`src/uav_qkd/phase5f_integration.py:134-136`).
   - What this is: Integration requires the cloud velocity to be `[-5, 0]` m/s.
   - Problem: GaussianCluster accepts its own `velocity`, and CloudField uses it
     instead of the global velocity. Adding `velocity: [0, 0]` to the supplied
     fixture cluster is accepted and yields a stationary cloud even though the
     global drift check passed. The original fixture switches the center LOS
     from blocked at 2 s to clear at 4 s; the stationary override is clear for
     all four fixture slots.
   - Fix: Reject cluster velocities that differ from the required global drift
     (or reject this optional field entirely in this bounded integration).
   - If we skip it: A valid-looking integration config can exercise a different
     cloud-motion convention from the required reference-window convention.
   - Regression: A cluster velocity of `[0, 0]` must be rejected; an absent
     override must retain the existing continuous-motion test.

## Verification

- Independent command: `python -m pytest tests/test_phase5f_integration.py -q -p no:cacheprovider`.
- Result: **13 passed in 1.00 s** before review fixes.
- Both findings were reproduced using read-only Python calls against the actual
  sealed package. No historical artifacts, configs, implementation or tests were
  edited by this reviewer.
- Accounting inspection confirms Scenario stores the clear rate and applies
  availability once through `m0*z`; the finite-size penalty is computed once
  for each accumulated prefix. Existing end-of-slot destination timing and
  information-access differences are stated correctly in the technical runner.

Verdict: fix 1 and 2 first.

Not checked: The complete suite and final CLI artifact package were not rerun by
this reviewer. No quantum/security proof, lookup regeneration, paper-mode,
mission evaluation, commit or push was performed. Remaining scientific inputs
and the finite LOS sampling limitation still prevent a real-experiment claim.

## Bounded follow-up after fixes and actual CLI dry run

This follow-up supersedes the earlier fix-first verdict. Inspection of the
changed boundary confirms that the builder freshly loads the sealed canonical
source, compares any supplied source with its full immutable contents, and then
uses the freshly verified source. It also rejects per-cluster velocities that
differ from the declared global drift. Both original findings are resolved.
The implementer reports 16 passing focused tests; this reviewer did not repeat
the tests during this read-only artifact follow-up.

The actual CLI output inspected was
`test_artifacts/phase5f_dry_run_20261108/`. Independent read-only checks passed:

- All four output seals match, and the output manifest covers all four payload
  files with no extras. All seven input hashes and all 31 producer hashes match
  the current files.
- The official Phase5E package manifest has its pinned hash
  `7b3f3b4fe7a4cd9c9f046aa456f3a1a4e4b8cf83c327f09e0fba23c28831bfa7`;
  all 624 package file hashes and exact file coverage match.
- The NPZ snapshot is four slots by three graph points. All 12 CSV slot rows
  agree with its positions, availability and rates; the rates match the actual
  Phase5E CSV node values. Times equal `k*dt` at the destination node.
- Each slot has effective rate `z*Rclear`, retained rate `Rclear`, valid count
  `m0*z`, and contribution `m0*z*Rclear`. Blocked transmission is zero.
- The shared scenario digest reconstructs exactly as
  `4ea44b862ca5a0ea5791dea53d5820d0ee8819d777f411475c9660654cc8185a`.
  The report states DP access to the predicted cloud horizon, greedy access to
  the current slot, and retrospective best-prefix selection for all methods.
- All four methods are FEASIBLE. Independently adding the recorded edge costs,
  valid counts and clear-rate contributions, then applying the existing prefix
  penalty once, reproduces all eight selected P1/P2 metrics. Every selected
  edge is feasible and each energy total stays below 1600 J.
- All 2,004 files in the before-snapshot retain their hashes. The current
  `results/` file set equals the 1,023 snapshot result files: no old result was
  changed or removed, and no new official research output appeared there.
- Report status is TEST_ONLY; paper-mode is NOT_RUN, author approval is false,
  paper admissibility is false and source evidence promotion is false.

The following numbers are software fixture receipts only:

| Method | Selected K (P1/P2) | Energy (J) | Valid signals | P2 key proxy (bits) | P1 key proxy (bits/s) |
| --- | --- | --- | --- | --- | --- |
| Stationary | 4 / 4 | 1347.873742 | 300000000 | 868491.480073 | 108561.435009 |
| SKR-Greedy | 4 / 4 | 1387.094430 | 400000000 | 1268398.404115 | 158549.800514 |
| Energy-Aware Greedy | 4 / 4 | 1387.094430 | 400000000 | 1268388.549498 | 158548.568687 |
| Pareto DP | 4 / 4 | 1387.094430 | 400000000 | 1268398.404115 | 158549.800514 |

Current verdict: Ship the TEST_ONLY technical integration. No artifact
inconsistency was found in these bounded checks. This does not authorize Phase6
or a real experiment.

Not checked in the follow-up: a second full code review, full-suite rerun,
independent rerun of the trajectory algorithms, or a continuous LOS certificate.
No native SKR evaluator, lookup regeneration, paper-mode, commit or push was run.
Scientific approvals and mission inputs remain pending.
