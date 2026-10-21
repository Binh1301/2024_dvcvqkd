# Figure validation

CURRENTLY_VERIFIED_PASS — 737 independent, named assertions.

- Complete saved input: 100 paired missions, ten exact λ values, three methods; 3,000 metric records and 90,000 selected-slot records. No omission, imputation or new optimization.
- All K, D, U and availability reconstructed directly from saved paths and S; U=mean(S)−λD/1000. Every leg ≤300m. DP objective dominates both baselines in all 2,000 comparisons within 1e−12; DP distance is non-increasing at the tested λ for each mission. P2 distance is zero and its SKR is λ-invariant.
- Means, sample SDs, medians and Student-t95% mean intervals independently checked. Forty paired comparisons use the same 100 mission IDs; bootstrap intervals are reused byte-equivalent numbers from the authenticated existing 20,000 whole-mission bootstrap analysis. Pointwise intervals are not simultaneous or security bounds.
- All 514 Matplotlib primary-curve points match independently reconstructed saved-data values; Fig.5 order is increasing λ. Actual line styles follow the requested blue-circle, orange-square and red-triangle assignments. λ=0 is retained; symlog threshold is np.float64(3.156008892416172e-07) bits/use.
- Fig.6/7 use disclosed post-hoc mission 84, exact stored λ=np.float64(9.468026677248516e-06). Requested rounded 9.46803e−6 is absent exactly; no new λ was created. Slot blockage is authenticated, cumulative values are exact prefix sums and are not physical secret-bit counts.
- Fig.8 retains all 100 negative Uniform raw rates and both families' exact raw values. No percentage gain relative to negative/zero Uniform.
- Eight vector PDFs (no embedded raster images), eight white-background 350dpi PNGs, eight source-map rows and linked English/Vietnamese documents checked. Final PNGs were visually inspected for clipping, readable labels, legends and preserved negative/zero values; image hashes are in visual_review.json.
- All 202 hash-bound members of the two prior receipts match. All 5076 pre-existing project files are protected; only the five authorized ledger paths may change. New files are restricted to this figure directory. Git branch and HEAD match startup.
- Original 24 tests/346 checks and prior 883 analysis checks remain historical evidence; they were not rerun or counted as this verification.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Frozen-specification hash discrepancy and Objective C USER_STOPPED remain. No physical SKR/source/cloud/P1/P2/P3/Greedy rerun; no final-test/held-out access, lifecycle promotion, external manuscript edit, commit or push. P2/DP are offline benchmarks; the synthetic finite-grid MI2D/homodyne-Holevo model is not a validated quantum-security rate.

Run `python -X utf8 -B verify_figures.py` using the project environment. A completed receipt is checked, not silently replaced.
