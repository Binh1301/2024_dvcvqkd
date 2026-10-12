# ALT_OPT closure diagnostic — exact method unchanged

CURRENTLY_VERIFIED_PASS

No new arbitrary-precision source generation; original objective and search algorithm delegated unchanged.
Three prior source successes were validated, evaluated and consumed at all five distances. No stale-cache bug was found.
They improve nu-slice coverage at VA=5.5 but have lower SKR than the selected candidates; other distances use these on transient/competing branches.
At the baseline and 22 km, the nu bracket narrowed [0.16,0.17] -> [0.1625,0.16625]. New required midpoints remain missing.
VA slices at the selected pairs received no new source point; therefore they still fail local refinement.
The four-stage refinement cap, two-sided 1e-6 criterion, missing midpoint pairs and earlier unresolved searches are distinct blockers.
Type A: selected local midpoint coverage missing. Types B/C: competing branches retain open endpoints. Type D: multi-start pairs disagree.
Type E: no verified stale-state/cache-consumption fault. Type F: no analytic continuous-global certificate (separate from local convergence).

## Five selected coordinate slices

| L | Coordinate | Fixed | Best | K | Exact neighbors | Missing values | Bracket radius | Required halving depth if best fixed |
|---:|---|---:|---:|---:|---|---|---:|---:|
| 20.0 | V_A | 0.15 | 6.5 | 0.1380135312811619 | [{"value": 6.0, "status": "EXACT_EVALUATED", "K": 0.13753857118567137, "nu_raw": 0.15, "V_A": 6.0}, {"value": 8.0, "status": "EXACT_EVALUATED", "K": 0.1372966251516714, "nu_raw": 0.15, "V_A": 8.0}] | [6.25, 7.25] | 1.5 | 21 |
| 20.0 | nu_raw | 6.5 | 0.15 | 0.1380135312811619 | [{"value": 0.125, "status": "EXACT_EVALUATED", "K": 0.13725790520863812, "nu_raw": 0.125, "V_A": 6.5}, {"value": 0.175, "status": "EXACT_EVALUATED", "K": 0.13740814778256105, "nu_raw": 0.175, "V_A": 6.5}] | [0.1375, 0.16249999999999998] | 0.024999999999999994 | 15 |
| 21.9393102292 | V_A | 0.165 | 5.5 | 0.07798099387393764 | [{"value": 5.4, "status": "EXACT_EVALUATED", "K": 0.07797458088717046, "nu_raw": 0.165, "V_A": 5.4}, {"value": 5.55, "status": "EXACT_EVALUATED", "K": 0.07797926607881778, "nu_raw": 0.165, "V_A": 5.55}] | [5.45, 5.525] | 0.09999999999999964 | 17 |
| 21.9393102292 | nu_raw | 5.5 | 0.165 | 0.07798099387393764 | [{"value": 0.1625, "status": "EXACT_EVALUATED", "K": 0.07797905612029876, "nu_raw": 0.1625, "V_A": 5.5}, {"value": 0.16625, "status": "EXACT_EVALUATED", "K": 0.07797961263356556, "nu_raw": 0.16625, "V_A": 5.5}] | [0.16375, 0.16562500000000002] | 0.0025000000000000022 | 12 |
| 22.0 | V_A | 0.165 | 5.5 | 0.07661685601911128 | [{"value": 5.4, "status": "EXACT_EVALUATED", "K": 0.07661416223906092, "nu_raw": 0.165, "V_A": 5.4}, {"value": 5.55, "status": "EXACT_EVALUATED", "K": 0.07661334352182514, "nu_raw": 0.165, "V_A": 5.55}] | [5.45, 5.525] | 0.09999999999999964 | 17 |
| 22.0 | nu_raw | 5.5 | 0.165 | 0.07661685601911128 | [{"value": 0.1625, "status": "EXACT_EVALUATED", "K": 0.07661494394735113, "nu_raw": 0.1625, "V_A": 5.5}, {"value": 0.16625, "status": "EXACT_EVALUATED", "K": 0.07661549304666915, "nu_raw": 0.16625, "V_A": 5.5}] | [0.16375, 0.16562500000000002] | 0.0025000000000000022 | 12 |
| 23.0 | V_A | 0.165 | 5.3 | 0.05745739941473693 | [{"value": 2.0, "status": "EXACT_EVALUATED", "K": 0.047582968002172155, "nu_raw": 0.165, "V_A": 2.0}, {"value": 5.4, "status": "EXACT_EVALUATED", "K": 0.05742551505146282, "nu_raw": 0.165, "V_A": 5.4}] | [3.65, 5.35] | 3.3 | 22 |
| 23.0 | nu_raw | 5.3 | 0.165 | 0.05745739941473693 | [{"value": 0.16, "status": "EXACT_EVALUATED", "K": 0.05744105603495675, "nu_raw": 0.16, "V_A": 5.3}, {"value": 0.175, "status": "EXACT_EVALUATED", "K": 0.05743829697448516, "nu_raw": 0.175, "V_A": 5.3}] | [0.1625, 0.16999999999999998] | 0.009999999999999981 | 14 |
| 24.0 | V_A | 0.15 | 5.0 | 0.04337158782779649 | [{"value": 4.5, "status": "EXACT_EVALUATED", "K": 0.04337056269691686, "nu_raw": 0.15, "V_A": 4.5}, {"value": 5.5, "status": "EXACT_EVALUATED", "K": 0.04316096691777804, "nu_raw": 0.15, "V_A": 5.5}] | [4.75, 5.25] | 0.5 | 19 |
| 24.0 | nu_raw | 5.0 | 0.15 | 0.04337158782779649 | [{"value": 0.1, "status": "EXACT_EVALUATED", "K": 0.042186211035776466, "nu_raw": 0.1, "V_A": 5.0}, {"value": 0.5, "status": "EXACT_EVALUATED", "K": 0.016576330048923726, "nu_raw": 0.5, "V_A": 5.0}] | [0.125, 0.325] | 0.35 | 19 |

## Three next probes — planning only

Ranking uses current selected terminal relevance, shared current searches, then recorded feasibility. Historical repetition alone never ranks a source first.

| Rank | nu | VA | Selected distances | Current affected searches | Impact | Risk |
|---:|---:|---:|---|---:|---|---|
| 1 | 0.16562500000000002 | 5.5 | [21.9393102292,22.0] | 18 | ENABLE_NEXT_EXACT_REFINEMENT_ATTEMPT_NOT_GUARANTEED_CLOSURE | ONLY_SHORT_REMAINING_BUDGET_TIMEOUT_NOT_60_MIN_TESTED |
| 2 | 0.16375 | 5.5 | [21.9393102292,22.0] | 18 | ENABLE_NEXT_EXACT_REFINEMENT_ATTEMPT_NOT_GUARANTEED_CLOSURE | PREVIOUS_60_MIN_TIMEOUT |
| 3 | 0.165 | 5.45 | [21.9393102292,22.0] | 8 | ENABLE_NEXT_EXACT_REFINEMENT_ATTEMPT_NOT_GUARANTEED_CLOSURE | ORIGINAL_AP_RUNTIME_UNKNOWN |

No selected parameter or SKR changed in cache-only replay; no search closed and no convergence was established.
An available exact value a few ULPs away is not a cache alias under the exact identity policy; do not round nu or VA to reuse it.
No online tolerance changes were made; offline 1e-7/1e-8/1e-9 sensitivity is detailed in stopping_criteria_analysis.md.
Saved source audit covers existing, newly generated and requested missing ensembles. Objective availability is limited to verified five-distance cache contexts.
Coordinate_slice_analysis.csv retains every evaluated/missing candidate, exact metrics and hex identities, not an interpolated curve.
Historical source requests 836 -> 786; original missing sources 50 -> 48; two new adaptive missing sources leave 50 known missing.
Protected files unchanged: 633; source identities verified: 168; regression tests PASS=True; git diff --check PASS=True.
Scientific source/security/frozen model/training/test access/baseline selection/threshold approval unchanged. Frozen-spec discrepancy remains open.
Stop here. The three ranked probes require explicit approval and a separate hard runtime budget.
