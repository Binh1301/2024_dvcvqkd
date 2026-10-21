# Stage A validation

CURRENTLY_VERIFIED_PASS: 7445 independent named assertions; 18 current deterministic tests. Historical tests are not rerun or counted.

- 26 unique approved configurations, 100 paired mission IDs, two fixed absolute penalties; complete 15,600 metrics and 423,000 selected-slot values reconstructed from original coordinates, current P1 and authenticated archived masks.
- 5,200 independent cumulative Bellman optima match saved DP objectives. All 10,400 mission-wise DP comparisons dominate P2/Greedy within absolute/relative1e−12. Every Greedy step independently reconstructs its current-slot Nt-lambda score and deterministic tie-break.
- 5000 mathematically guaranteed monotonic inequalities checked for nested J, relaxed speed and nested blockage probability. No unsupported monotonic constraint imposed on Greedy, availability, distance versus speed, horizon or spatial length. No-movement DP equals P2; P2 is speed/lambda invariant; lambda0 Greedy prefixes are causal.
- Mean, sample SD, median and every percentile CI independently recomputed. Bootstrap20,000 whole-mission draws, seed20261020, paired weight identity replayed; no cell/slot independence assumption. Ratios use positive baseline mission means; undefined ratios are empty, never fabricated zeros. Intervals are pointwise, not simultaneous or quantum-security bounds.
- 344 actual primary artist points and their unmodified confidence bounds trace to saved CSVs; six reviewed white-background350dpi PNGs and six vector PDFs. Zero is visible; spatial x-axis is explicitly logarithmic; no smoothing or interpolated simulation points.
- All3,000 original baseline metric records and3,000 paths reproduced at all10 old penalties before the batch; maximum residual 0.0. Baseline audit used1,000 DP/Greedy pairs plus4 deterministic archived controls; Stage A batch used5,000 new pairs. No physical/channel/source/cloud evaluator calls.
- 240 old receipt members authenticated; exact-source payloads and producer hashes bound. All5118 startup files protected except the five authorized ledger paths; new code/output namespace restricted, Git branch/HEAD unchanged and diff whitespace passes.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Stage B NOT_RUN; new cloud scenarios=0, new physical SKR=0, new C,w=0. Frozen historical-hash discrepancy and Objective C USER_STOPPED remain. No production quantum model/cache change, final-test/held-out access, publication/lifecycle/baseline/threshold promotion, external edit, commit or push. These are synthetic finite-catalog/grid, offline P2/DP numerical comparisons, not validated quantum-security or propulsion-energy claims.

Recheck using project Python: `scripts/run_mobility_parameter_sensitivity.py --stage verify`. Completed receipts are checked, never silently replaced.
