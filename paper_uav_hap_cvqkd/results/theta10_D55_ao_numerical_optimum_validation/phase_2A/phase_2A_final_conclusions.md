# Phase2A final conclusions — saved results only

Execution and original numerical validation ended by14:34:25UTC, before the
unchanged14:46:13.577171UTC deadline. Current user's later `continue` caused
only saved-artifact/hashes/figure inspection and documentation, not new AP,
objective, AO, quadrature, or regression runs. Do not claim the entire later
interactive turn was within the expired compute budget. No further AP authorized.

## Actual outcomes

|Probe|nu_raw|VA|Outcome|C|w|wall seconds|Job CPU seconds|
|---|---|---|---|---|---|---|---|
|1|0.165|5.49375|Safety-abort, no automatic retry|unavailable|unavailable|1799.031|1733.859375|
|2|0.165|5.5125|COMPLETED_EXACT|3.2176328023710283|1.0391362032418032e-6|2723.047|2651.296875|
|3|0.16531250000000003|5.5|TIMEOUT, no automatic retry|unavailable|unavailable|3595.000|3516.90625|

Probe1's Job125 followed a15.578s watchdog gap and AC0; actual suspend versus
scheduler delay is not distinguished. Probe3 stayed within its3600s approved
ceiling with the original5s operational termination margin. No fourth source
or excluded(.16375,5.5) source was computed. Original binary64/cache identities,
precision1050/1250/1450 and scientific methods unchanged.

## Required answers

1. **Success/timeout/stop:**1/1/1; all3 approved sources attempted once.
2. **New moments:**onlyprobe2 validC,w above; no inferred failed-source values.
3. **Best observed results:** reference21.9393102292km(.165,5.5),
   K=.07798099387393764;22km(.165,5.475),K=.07661740491526092.
   Both are finite-catalog maxima, not continuous/global optima.
4. **Improvement:**none at all26 distances; every stored deltaK exactly0.
5. **P1/P2 refinement:**one upperVA midpoint now measured. ReferenceP1 bracket
   changes[5.4875,5.525] to[5.4875,5.5125], width.0375 to.025 and radius.025
   to.0125. This is one-sided coverage/bracket progress, NOT a completed paired
   refinement step. The unchanged new invocation still records1 attempted stage
   and stops on missing points. P2 has no new validnu measurement, unchanged
   bracket[.1625,.16562500000000002]. Both have0 completed new midpoint pairs.
6. **Coordinate completion:**0 newly closed selected directions; parameter
   tolerance1e-6 not reached. Current618 searches remain312 open-boundary/306
   bracket-source-blocked.55 missing pairs: measured5.5125 replaced by a finer
   missing5.50625, not evidence of catalog/global convergence.
7. **AO versus catalog:**actual original129 starts/283 iterations and independent
   saved147-candidate matrices agree at26/26. No final-catalog point copied into
   an AO trajectory.147 MB pairs/3822 objective rows,26 fresh objective rows.
8. **Phase2B:**(.16375,5.5) still genuinely blocks the referenceP2 lower side,
   since selectedVA remains5.5. It is necessary for that current paired step
   but insufficient for trustworthy optimality: the timed-out uppernu partner
   and P1 missing moments/accuracy/boundary checks also remain. Phase2B needs
   separate explicit scope/runtime authorization; no automatic retry or bigger
   budget inferred. Previous60min timeout does not predict completion time.
9. **Runtime/safety/tests:**10090.781s wall from original origin, including
   setup/stops/idle/processing/cleanup; below10800s. Recorded Job+controllerCPU
   8088.203125s, excludes some independent setup/audit/test-processCPU.32 final
   regression tests/diffPASS beforedeadline; separate resume contract also passed
   beforeexecution.1243 protected input hashes unchanged. Allworkers exited and
   originalSleep state restored. No permanent power-plan change.

## Exact remaining priority dependencies

- P1 atnu=.165: VA5.49375 (prior safety-abort) and VA5.50625 (new missing
  binary64 arithmetic midpoint). Neither may be filled by interpolation.
- P2 atVA5.5: nu=.16375 (old60min timeout) and
  nu=.16531250000000003 (new60min timeout).
- At22km P1 still missing(.165,5.4625)/(.165,5.481249999999999); P2 atVA5.475
  remains singleton, lowerouter(.0825,5.475) missing/opposite side unchecked.

The nu0=.8 start at both priority distances remains(.4,3.0), with K=
.06912585821984563(reference)/.06797982114890355(22km). Its last searches
explicitly lack(.4,1.5) and(.2,3.0), and stopUNRESOLVED_BOUNDARY after stagnation.
This supports missing-source/boundary blockage, not proof of a separate
continuous attraction region.4/5 starts still reach each finite-catalog winner.

## Accuracy and publication limits

Four retained original GH8/directZ-minus metric repeats from newC,w are bit-exact
at20/reference/22/40km. Repeatability/provenance do not enclose total objective
error. Classification remainsORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED.
No source/precision/quadrature/MI/Holevo/AO changes, fit or interpolation.
Strictpositive implementednu still does not include the mathematicalnu=0 boundary;
compatible storedUniform comparisons are not a continuous boundary certificate.
No continuous numerical convergence, global optimum or publication-scale claim.

## Data and figures

- `new_exact_skr_26_distances.csv`: newsource2 metrics at all26 distances.
- `optimized_skr_26_distances.csv`: actualAO-selected parameters/decomposition/status.
- `old_vs_new_skr_optimum.csv`: old146 versus new147 independent maxima andAOmatch.
- `cache_only_runs.json`, `ao_iteration_history.csv`: genuine multi-start histories.
- `coordinate_completion_status.csv`, `coordinate_refinement_progress.csv`,
  `reference_targeted_coordinate_searches.json`: actual brackets/next dependencies.
- `independent_catalog_verification.csv`, `original_evaluator_reproducibility.csv`:
  original in-budget verification records.
- Eight300dpiPNG/vectorPDF pairs generated beforedeadline, including
  `skr_vs_distance_positive_only.png/pdf`. Numeric CSV decoding in the resume
  renderer prevents categorical axes; no data values changed. All78 signed
  comparison rows retained; figure alone displaysK>0, Uniformthrough25km and
  bothMBthrough40km, standardbase10log. No abs(K), zero substitution, fitted
  optimum or interpolatedzero crossing. Distance andreferenceP1 plots inspected.

All previous scientific artifacts and stopped/preparation snapshots preserved.
Frozen-spec historical-hash discrepancy remains PREEXISTING_UNCHANGED;
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Approval is now exhausted/expired, not
authority for more AP or retries.
