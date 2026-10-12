# AO numerical optimum validation — Phase1

Audit complete.146 compatible MB sources,3796 saved objective rows,26/26 selected
AO finite-catalog maxima. No new AP, source moments, channel, MI/Holevo or optimizer
evaluation. Old artifacts and scientific files are hash-protected. Numeric validity
and incomplete optimization are separate outcomes; no lifecycle promotion.

## Required conclusions

1. P1/P2 indexing is consistent: P1 fixes previousnu, P2 fixes the NEW VA. Domain
   difference: implementation excludesnu=0, unlike the mathematical target.
2. Each iteration runs the two original exact-tested slice searches, propagates
   their candidates and computes genuine DeltaK; no reconstructed final copies.
3. All283 iterations/129 starts genuinely alternate;618 recorded calls include52
   selected-final postchecks. Per-coordinate fresh/cache counters are available;
   requested-call counts are only recorded at run/distance level.
4. Both coordinates are blocked by missing source moments.312 calls have open
   boundaries,306 have bracketed missing sources.0 selected directions complete.
   None reaches the four-stage cap now, but that cap would be insufficient for
   one-call refinement of the present priority brackets. Total numerical accuracy
   also remains unresolved, independently of source coverage.
5. Reference (.165,5.5),K=.07798099387393764 is a verified finite-catalog maximum
   and best observed multi-start result. It is not a validated continuous local
   numerical optimum, a completed approximate coordinate optimum or global optimum.
6. Reference: both lower/upper VA midpoints and both nu midpoints are required.
   At22km(.165,5.475),K=.07661740491526092, P1 is bracketed but P2 is singleton:
   original lowerouternu=.0825 is missing and opposite side untested.
7.4 actual pairs are the minimum set to finish one paired step in BOTH reference
   calls;7 initial dependencies advance the two reference and two22km calls.
   This is not a promise of final convergence. See targeted plan and55-entry priority CSV.
8. Multi-start stability is partial, not universal:4/5 starts match the catalog
   winner at each priority distance;nu0=.8 returns(.4,3.0) with lowerK. Full table below.
9. Sources/provenance and deterministic original-evaluator repeatability support
   reported numbers. Retained source convergence/quadrature/entropy evidence does
   NOT bound whole-K error; tiny rank gaps remain error-unbounded.
10. A defensible Algorithm1 can already describe the ACTUAL incomplete procedure.
    A convergence discussion must say catalog stagnation, not convergence. TeX
    supplied with dependencies; compilation is NOT_RUN in this environment.
11. Before reliable optimizedSKRall26: validate both priority coordinate searches,
    candidate-specific numerical accuracy and multistart/boundary coverage; then
    repeat original procedure for the other24 with explicit status. Addressnu=0
    scope prospectively, never silently; finite tests alone cannot certify global.

## Actual priority multistart terminals

|L km|start|iterations|nu|VA|K bits/use|status|
|---|---|---|---|---|---|---|
|21.9393102292|nu_0.1|3|0.165|5.5|0.07798099387393764|STAGNATED_IN_EXACT_CATALOG|
|21.9393102292|nu_0.15|2|0.165|5.5|0.07798099387393764|STAGNATED_IN_EXACT_CATALOG|
|21.9393102292|nu_0.3|2|0.165|5.5|0.07798099387393764|STAGNATED_IN_EXACT_CATALOG|
|21.9393102292|nu_0.8|3|0.4|3.0|0.06912585821984563|UNRESOLVED_BOUNDARY|
|21.9393102292|warm_previous_distance|2|0.165|5.5|0.07798099387393764|STAGNATED_IN_EXACT_CATALOG|
|22.0|nu_0.1|4|0.165|5.475|0.07661740491526092|UNRESOLVED_BOUNDARY|
|22.0|nu_0.15|3|0.165|5.475|0.07661740491526092|UNRESOLVED_BOUNDARY|
|22.0|nu_0.3|3|0.165|5.475|0.07661740491526092|UNRESOLVED_BOUNDARY|
|22.0|nu_0.8|3|0.4|3.0|0.06797982114890355|UNRESOLVED_BOUNDARY|
|22.0|warm_previous_distance|2|0.165|5.475|0.07661740491526092|UNRESOLVED_BOUNDARY|

## Manuscript and comparison caveats

Eight figure pairs (PNG300dpi/vectorPDF) use recorded histories and exact scatter
slices. FigureA uses initial/P2 values with P1 crosses; lines indicate update
sequence, not a fit. Both parameter plots use actual initialization and updates.
The22km nu slice contains only one measured point. Missing values never plotted.
Local slice CSVs include the full exact slice while viewports focus on the incumbent.

three_scheme_comparison.csv retains all78 signed SKRs. The distance figure follows
the established positive-only renderer: Uniform ends25km, both MB reach40km;
standard base10log, no abs/zero substitution/interpolated zero crossing/K=0line.
AO curve label says finite-catalog best, not certified global. Stored Uniform
selection is not newly optimized or certified in this task. Fixed MB uses actual
VA=1.3833230302980657 (not exactly requested1.3833230303);
that historical discrepancy is preserved and disclosed, not silently repaired.

Historical records are exported by artifact/execution identity. Counts are in
historical_execution_inventory.json; old catalogs/status policies are not promoted
to current scientific evidence or combined into one fictitious trajectory.
The closure aggregate already includes its coordinate-batch snapshots, so they
are not counted twice. Historical certification all_multistart_iterations.csv is
a129-start SUMMARY, not an iteration trace; actual CSV/JSON histories are used.

Fresh phase2 scope/budget is required. This task stops beforeAP and does not ask
for a budget. Science/model/settings/thresholds/train/test access remain unchanged.
Frozen-spec historical-hash discrepancy is pre-existing; lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Machine report records current verification,
protected hashes, test outputs and actual cache-only runtime.
