# Targeted exact continuation plan

Phase1 complete; Phase2 NOT AUTHORIZED. Do not request a new budget in this task.
Do not reuse expired Batch3 budgets, execute all55 sources, predict K, or restart a rectangular grid.

## Primary and secondary coordinate blockers

|L km|coordinate|fixed|candidate|bracket|radius|issues|
|---|---|---|---|---|---|---|
|21.9393102292|V_A|0.165|5.5|[5.4875, 5.525]|0.025000000000000355|MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED;OBJECTIVE_STAGNATED_ONLY|
|21.9393102292|nu_raw|5.5|0.165|[0.1625, 0.16562500000000002]|0.0025000000000000022|MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED;OBJECTIVE_STAGNATED_ONLY|
|22.0|V_A|0.165|5.475|[5.45, 5.4875]|0.024999999999999467|MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED;OBJECTIVE_STAGNATED_ONLY|
|22.0|nu_raw|5.475|0.165|[null, null]||BOUNDARY_UNRESOLVED;MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED;OBJECTIVE_STAGNATED_ONLY|

## Smallest useful sets (one original paired step, NOT full convergence)

Reference P1: (.165,5.49375) and (.165,5.5125). Both are needed to finish its first paired midpoint attempt.
Reference P2: (.16375,5.5) and (.16531250000000003,5.5). The lower source previously timed out at3600s.
Thus4 source pairs advance BOTH selected reference coordinates by one step; no smaller set finishes both paired attempts.
A one-source pilot (.16531250000000003,5.5) is informative shaping evidence, but cannot close P2 without its lower partner.
At22km P1: (.165,5.4625) and (.165,5.481249999999999); preserve the latter binary64, not5.48125.
The first was AC-aborted; never automatically retry. It needs explicit fresh authority and safe power.
At22km P2 the actual first request is (.0825,5.475), an OUTER half-value, not a local midpoint.
The opposite outer (.33,5.475) is NOT yet requested and NOT in the55 inventory. Whether/when it is requested depends on
measured lower-outer ordering and the unchanged singleton/endpoint logic. Do not invent a bracket or nu midpoint here.
For progress on all four selected calls the initial actual dependency set contains7 pairs (4 reference +3 at22).
No finite minimum number guarantees final parameter closure or numerical accuracy; later requests depend on exact results.

## Refinement-limit implications

If the incumbent stays fixed and both sides halve, reference VA radius=.025 requires15 midpoint levels,
nu radius=.0025 requires12; the entry-check semantics require16/13 allowed loop stages, respectively.
22km VA radius=.025 likewise requires15 levels/16 entry stages. P2 has no measurable radius.
These are conditional geometric calculations only, not simulated outcomes, guaranteed iterations, or error estimates.
Four steps cannot close those current radii within a single call. Exact probes can make the next invocation start
from a narrower catalog bracket; change no settings now. A future larger cap needs separate prospective approval.
Earlier unresolved-search memory also prevents an individual resumed trajectory from being called converged
merely because its latest coordinates later close. Reassess with the original multi-start driver and report actual status.

## Runtime and execution gates

Existing successful sources cost roughly36-53 minutes; cost for unmeasured points is unknown and can exceed60min.
The prior lower reference nu source timed out; AC abort is not a numerical failure or timeout.
A future explicitly authorized campaign must be sequential with fresh total/per-source deadlines, stableAC,
temporary Sleep prevention, validated Windows Job supervision, provenance checkpoints and full tree cleanup.
Every successful source then gets all26 original-evaluator objectives; adaptive planning uses only measured results.
Restoration of the original execution state is mandatory; no unattended/retried worker is authorized here.

## Per-distance continuation dependencies

Other24 distances are deferred until stronger reference/22 local and accuracy evidence exists.
For each distance below, finish the listed actual P1/P2 dependencies, then recheck both searches, all starts,
outerDeltaK, earlier unresolved flags and numerical accuracy. Currentcache alone is insufficient at every distance.
Source availability may satisfy one paired stage or permit a boundary request; no single probe promises stopping.
|L km|nu|VA|K bits/use|P1 missing values|P2 missing values|gate|
|---|---|---|---|---|---|---|
|20.0|0.15|6.5|0.1380135312811619|[6.375, 7.25] (fixed nu=0.15)|[0.1375, 0.16249999999999998] (fixed VA=6.5)|DEFERRED|
|21.0|0.16|6.0|0.1027071638150534|[12.0] (fixed nu=0.16)|[0.1575, 0.16749999999999998] (fixed VA=6.0)|DEFERRED|
|21.9393102292|0.165|5.5|0.07798099387393764|[5.49375, 5.5125] (fixed nu=0.165)|[0.16375, 0.16531250000000003] (fixed VA=5.5)|PRIMARY|
|22.0|0.165|5.475|0.07661740491526092|[5.4625, 5.481249999999999] (fixed nu=0.165)|[0.0825] (fixed VA=5.475)|SECONDARY|
|23.0|0.165|5.3|0.05745739941473693|[3.65, 5.35] (fixed nu=0.165)|[0.1625, 0.16999999999999998] (fixed VA=5.3)|DEFERRED|
|24.0|0.15|5.0|0.04337158782779649|[4.75, 5.25] (fixed nu=0.15)|[0.125, 0.325] (fixed VA=5.0)|DEFERRED|
|25.0|0.15|4.5|0.033155735581557266|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|25.5|0.15|4.5|0.029094514576219477|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|26.0|0.15|4.5|0.02559880329969072|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|26.5|0.15|4.5|0.02258632178693923|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|27.0|0.15|4.5|0.019986441582292652|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|27.5|0.15|4.5|0.01773877780029154|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|28.0|0.15|4.5|0.015791856791609243|[4.027433695248145, 4.75] (fixed nu=0.15)|[0.3] (fixed VA=4.5)|DEFERRED|
|29.0|0.15|3.5548673904962893|0.012633752605448606|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|30.0|0.15|3.5548673904962893|0.010253503998581354|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|30.5|0.15|3.5548673904962893|0.009278128392001553|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|31.0|0.15|3.5548673904962893|0.008419975631179313|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|31.5|0.15|3.5548673904962893|0.007663135177788452|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|32.0|0.15|3.5548673904962893|0.006994021456280031|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|32.5|0.15|3.5548673904962893|0.006401020851147396|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|33.0|0.15|3.5548673904962893|0.005874192306253717|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|34.0|0.15|3.5548673904962893|0.004986168363777209|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|35.0|0.15|3.5548673904962893|0.004275173307058823|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|36.0|0.15|3.5548673904962893|0.0037005544396879267|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|38.0|0.15|3.5548673904962893|0.0028463445249044643|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
|40.0|0.15|3.5548673904962893|0.00225888275226813|[2.7774336952481447, 4.027433695248145] (fixed nu=0.15)|[0.075] (fixed VA=3.5548673904962893)|DEFERRED|
