# AO stopping-parameter sensitivity

BASELINE_PARAMETERS_ONLY_COMPUTATIONAL_SAFEGUARDS

## Scope and provenance

CURRENTLY_VERIFIED_PASS: actual original AO reruns, temporary Rmax/epsilon only. No AP generation, interpolation, channel replay or science changes. Restored compatible 3822 objective rows with original provenance checks. Each setting uses its own ordered warm chain; 20/21 km prefix is required before detailed reference/22 km analysis. Source catalog remains 147. Shared immutable validated rows are reused, counters reset between configurations; no configuration borrows trajectories or warm starts from another. Baseline first, one-factor axes next, remaining grid last.

## Twelve required answers

1. Yes: R6/1e-8 exactly reproduces 129 starts, 283 iterations and 26 selected catalog maxima.
2. R8/R10 do not improve selected SKR at any distance.
3. Neither larger cap changes any selected binary64 pair.
4. Tightening 1e-8 to 1e-9 produces no SKR gain.
5. Tightening 1e-8 to 1e-9 leaves all 129 individual histories/counts unchanged (283 cycles). Epsilon1e-6 reduces 283 to279 cycles: four starts at22km terminate one cycle earlier, after a positive increment5.488961496435962e-7. Their terminal pairs/K are nevertheless unchanged. Epsilon1e-7 also retains283 cycles.
6. Actual code reasons and overlapping diagnostic flags are preserved in sensitivity_by_start.csv.
7. All129 starts/configuration request missing sources. Zero-increment incomplete termination occurs129/129 times for eps<=1e-7 and125/129 for eps1e-6. All starts meet their objective threshold; none completes its coordinates. Each configuration requests the same55 distinct missing binary64 source pairs.
8. Selected finite-catalog values are invariant at 26/26 distances for all sixteen settings.
9. Six is not the active outer bottleneck: all runs stop by iteration4 and zero runs terminate because of the cap. At Rmax4, three runs reach the last permitted cycle for eps<=1e-7 (two for eps1e-6), but the epsilon decision wins. Six is only a computational safeguard, not a convergence guarantee; four is sufficient to reproduce this incomplete catalog replay too.
10. Retain1e-8 provisionally as an objective-change safeguard, not an empirically optimal threshold. Even1e-6 produces identical terminal results while using four fewer cycles; this single-cache timing/trajectory observation does not justify a production accuracy claim or permanent setting change.
11. Missing moments, unclosed boundaries, incomplete inner refinement and an unbounded total SKR error prevent convergence certification.
12. The manuscript may report exact finite-catalog invariance and baseline reproduction, not continuous/global optimality.

## Actual configuration statistics

|Rmax|epsilon|iterations|histogram|stop reasons|zero-increment incomplete runs|calls/hits (AO body)|distinct missing|
|---|---|---|---|---|---|---|---|
|6|1e-08|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|4|1e-08|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|8|1e-08|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|10|1e-08|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|6|1e-06|279|{3: 37, 2: 70, 4: 2, 1: 20}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|125/129|4371/3541|55|
|6|1e-07|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|6|1e-09|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|4|1e-06|279|{3: 37, 2: 70, 4: 2, 1: 20}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|125/129|4371/3541|55|
|4|1e-07|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|4|1e-09|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|8|1e-06|279|{3: 37, 2: 70, 4: 2, 1: 20}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|125/129|4371/3541|55|
|8|1e-07|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|8|1e-09|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|10|1e-06|279|{3: 37, 2: 70, 4: 2, 1: 20}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|125/129|4371/3541|55|
|10|1e-07|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|
|10|1e-09|283|{3: 38, 2: 69, 4: 3, 1: 19}|{'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}|129/129|4447/3605|55|

## Reference starts, including nu_initial=0.8

|configuration|L|start|terminal (nu,VA,K)|outer iterations|actual reason|
|---|---|---|---|---|---|
|R6_eps1e-08|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-08|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-08|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-08|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-08|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-08|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-08|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-08|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-06|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-06|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-07|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-07|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-09|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R6_eps1e-09|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-06|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-06|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-07|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-07|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-09|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R4_eps1e-09|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-06|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-06|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-07|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-07|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-09|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R8_eps1e-09|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-06|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-06|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-07|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-07|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-09|21.9393102292|nu_0.8|(0.4,3.0,0.06912585821984563)|3|UNRESOLVED_BOUNDARY|
|R10_eps1e-09|22.0|nu_0.8|(0.4,3.0,0.06797982114890355)|3|UNRESOLVED_BOUNDARY|

## Inner-search audit and costs

The original adaptive_maximize_1d creates a fresh evaluated map and bracket for every call; only compatible exact rows/catalog persist. It does not carry an active midpoint bracket between outer cycles. Missing midpoint/outer values are requested again and remain missing. The four-stage cap is unchanged; missing moments can stop refinement before that cap. The unresolved-inner latch persists within each AO run, so objective tolerance alone never yields a completed-search claim. Increasing Rmax cannot force additional cycles after the original stopping decision. At the reference selected pair, the P1 bracket is [5.4875,5.5125] and P2 is [0.1625,0.16562500000000002]. Conditional fixed-best halvings to radius1e-6 are 14 and 12; these are geometric estimates, not executed steps or a guarantee the best stays fixed.

All genuine iterations/candidate events are in ao_iteration_history.csv and configuration JSONs. Coordinate audit distinguishes iteration calls from52 selected-final postchecks per configuration. Across16 settings there are2064 starts,4512 outer updates and9856 coordinate calls, with zero closures. Computational CSV separates AO-body/postcheck calls, hits, missing lookups and existing-source SKR evaluations. Distinct missing binary64 pairs reflect expensive source demand, not AP timings. Each eps<=1e-7 setting uses4447 AO-body calls/3605 hits/842 missing events; eps1e-6 uses4371/3541/830. Postchecks add406calls/324hits/82missing events per setting. Existing-source fresh SKR evaluations and new AP sources are both zero. No longer run generates a new missing source beyond the same55 pairs.

Measured16-configuration execution totals322.89248490010505s wall and308.15625s CPU, including postchecks and original runtime guards. Report-only finalization takes11.833741599984933s wall/11.03125s CPU. A missing-event reader KeyError occurred after all16 AO checkpoints were saved; the report reader was fixed and no AO rerun was performed. Initial setup/full-process clocks were not saved because of this reporting exception; these quantities are NOT_RECORDED, and the measured configuration totals must not be presented as complete end-to-end runtime. Timing is a single sequential cache-only measurement, not a causal production-speed claim or an estimate of arbitrary-precision source-generation cost.

## Safety and verification

No worker, observer, Job Object or sleep override is needed or invoked for this cache-only diagnostic. AP methods fail closed via guards. All temporary AO aliases restored. All1591 protected input hashes and older artifacts remain unchanged. Historical frozen-spec discrepancy remains PREEXISTING_UNCHANGED and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains unchanged. Scoped regression: CURRENTLY_VERIFIED_PASS,30 tests; genuine histories, all16 independent warm chains, compatible metrics and protected hashes checked. Both PDFs are one-page vector figures with zero raster images; both PNGs are400dpi and visually reviewed. Epsilon x-axis is base10log. LaTeX compilation is NOT_RUN_NO_LOCAL_ENGINE; static table/text checks and word-count constraints PASS (VersionA141, VersionB296 whitespace-delimited words). Detailed checks and output hashes are recorded in sensitivity_validation.json.
