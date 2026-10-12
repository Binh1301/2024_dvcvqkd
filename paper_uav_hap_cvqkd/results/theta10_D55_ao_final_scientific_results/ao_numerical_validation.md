# AO numerical validation

Current saved-data verification: 1561 protected hashes unchanged, 147 compatible MB pairs/3822 metrics/26 identities. No physical/security/source/objective/AO rerun. Original epsilon1e-8/parameter1e-6/outer6/inner4/boundary3 unchanged.
Independent 147-row maxima agree with genuine AO terminal selection at 26/26 distances. Selected-direction closures=0; no numerical/global certification.
Reference top evaluated candidates:

| nu_raw | VA | K | Gap from best |
|---|---|---|---|
| 0.165 | 5.5 | 0.07798099387393764 | 0.0 |
| 0.165 | 5.4875 | 0.07798091552916897 | 7.834476867252249e-08 |
| 0.165 | 5.5125 | 0.07798086747835642 | 1.2639558122362615e-07 |
| 0.165 | 5.475 | 0.0779806318144487 | 3.620594889452988e-07 |
| 0.165 | 5.525 | 0.07798053696750062 | 4.5690643701856715e-07 |

Reference multi-start terminal results:

Across all distances, 59/129 individual terminal results match the catalog maximum, and 0/26 distances have unanimous agreement across all starts. Terminal states: 20 STAGNATED_IN_EXACT_CATALOG, 109 UNRESOLVED_BOUNDARY. The independently verified 26/26 agreement is for the best selected start, not for every initialization.

| Start | nu | VA | K | State |
|---|---|---|---|---|
| nu_0.1 | 0.165 | 5.5 | 0.07798099387393764 | STAGNATED_IN_EXACT_CATALOG |
| nu_0.15 | 0.165 | 5.5 | 0.07798099387393764 | STAGNATED_IN_EXACT_CATALOG |
| nu_0.3 | 0.165 | 5.5 | 0.07798099387393764 | STAGNATED_IN_EXACT_CATALOG |
| nu_0.8 | 0.4 | 3.0 | 0.06912585821984563 | UNRESOLVED_BOUNDARY |
| warm_previous_distance | 0.165 | 5.5 | 0.07798099387393764 | STAGNATED_IN_EXACT_CATALOG |

P1: bracket=[5.4875, 5.5125], width=0.025000000000000355; status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; missing=[{'value': 5.49375, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.4937500000000004'}, {'value': 5.50625, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.5062499999999996'}].

P2: bracket=[0.1625, 0.16562500000000002], width=0.0031250000000000167; status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; missing=[{'value': 0.16375, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16375000000000001, V_A=5.5'}, {'value': 0.16531250000000003, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16531250000000003, V_A=5.5'}].

At 22 km P1/P2 selected-final diagnostics:
[{'L_km': 22.0, 'coordinate': 'V_A', 'fixed': 0.165, 'current_candidate': 5.475, 'K': 0.07661740491526092, 'source_cache_key': '4ff64d8ff1b9cb558e7feab44d02d62b15f2c430a0440ccb9af74b0e42e31a5d', 'bracket': '[5.45, 5.4875]', 'bracket_width': 0.037499999999999645, 'radius': 0.024999999999999467, 'parameter_tolerance': 1e-06, 'conditional_fixed_best_midpoint_levels': 15, 'conditional_required_loop_stages': 16, 'conditional_radius_after_four_levels': 0.0015624999999999667, 'neighbor_values_and_gaps': '[{"value": 5.4875, "K": 0.07661723159351552, "gap": 1.733217454003011e-07, "source_cache_key": "e0b4f67abe7e7514f95471b59f034e9e8e7eab34a8d29a4fc0824c1ade393c45"}, {"value": 5.45, "K": 0.07661714229913241, "gap": 2.626161285101958e-07, "source_cache_key": "5764a134490ed68f96ff10357aa67c1f4f57b88f2bd1ca6a4a9a8498859f6644"}]', 'missing_exact_points': '[{"value": 5.4625, "status": "EXACT_SOURCE_MISSING", "error": "No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.4625000000000004"}, {"value": 5.481249999999999, "status": "EXACT_SOURCE_MISSING", "error": "No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.4812499999999993"}]', 'range': '[0.025, 8.0]', 'termination_reason': 'SOURCE_MISSING_REFINEMENT', 'original_status': 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING', 'status_categories': 'MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED', 'evaluated_points': 15, 'boundary_expansions': 0, 'refinement_stages': 1, 'coordinate_complete': False, 'global_domain_closed': False}, {'L_km': 22.0, 'coordinate': 'nu_raw', 'fixed': 5.475, 'current_candidate': 0.165, 'K': 0.07661740491526092, 'source_cache_key': '4ff64d8ff1b9cb558e7feab44d02d62b15f2c430a0440ccb9af74b0e42e31a5d', 'bracket': '[null, null]', 'bracket_width': '', 'radius': '', 'parameter_tolerance': 1e-06, 'conditional_fixed_best_midpoint_levels': None, 'conditional_required_loop_stages': '', 'conditional_radius_after_four_levels': '', 'neighbor_values_and_gaps': '[]', 'missing_exact_points': '[{"value": 0.0825, "status": "EXACT_SOURCE_MISSING", "error": "No hash-matched exact source row for nu_raw=0.082500000000000004, V_A=5.4749999999999996"}]', 'range': '[0.165, 0.165]', 'termination_reason': 'NOT_NEEDED', 'original_status': 'BOUNDARY_NOT_CLOSED', 'status_categories': 'BOUNDARY_UNRESOLVED;MISSING_SOURCE_BLOCKED;NUMERICAL_ACCURACY_UNRESOLVED', 'evaluated_points': 1, 'boundary_expansions': 1, 'refinement_stages': 0, 'coordinate_complete': False, 'global_domain_closed': False}]

Code semantics: starts .1/.15/.3/.8 plus warm pair; initial VA is warm value only if available, otherwise smallest slice value. Every available positive coordinate value is compared. Endpoint halving/doubling cap3; paired nearest-neighbor midpoints cap4; radius tolerance checked at loop entry. An attempted missing-pair stage is not a completed refinement. Earlier unresolved-search latch persists. At small objective change, open boundary => UNRESOLVED_BOUNDARY; incomplete/latch => STAGNATED_IN_EXACT_CATALOG; only complete/warning-free searches permit CONVERGED_NUMERICALLY. Caps/failures do not certify closure.

All 618 recorded coordinate-search calls were checked; 0 satisfy the original completion predicate. This includes the 52 selected-final coordinate postchecks, not only a subset of reference-distance searches.

nu0=.8 actual full-cycle pairs: (.8,1.5)->(.5,1.5)->(.4,3)->(.4,3), finalK=.06912585821984563. Final missing (.4,1.5) and(.2,3), not proven distinct basin. Four other starts reach reference best. All-distance multi-start terminals in ao_multistart_terminal_results.csv.

Local support: both reference nearest evaluated VA and nu neighbors have lower recorded K. Missing midpoints and remote directions prevent continuous optimality. Whole-objective error at the top-two gap is unbounded; GH8 deterministic MI and original AP1050/1250/1450 preserved, not promoted to an error certificate.

Historical139-MB numerical/certification catalog was inspected, not mixed into 147-source maximum claims. Historical comparison curve is stored compatible Uniform/fixedMB only; MB curve uses current147 best. Uniform omission is rendering only (last positive25km); no invented crossing/interpolation/abs/zero replacement.

Theory nu>=0 vs implementation nu>0 remains unresolved. Frozen-spec historical expected hash differs from unchanged current re-freeze; recorded PREEXISTING_UNCHANGED. Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS; manuscript-ready formatting does not authorize training/finaltest/security/global claims.

Regression evidence: 27 tests PASS; gitdiffcheck PASS. LaTeX compile=NOT_RUN_NO_LOCAL_LATEX_ENGINE; snippet packages/figures supplied, no unsupported local compile claim.
