# Overnight AO numerical SKR run

OVERNIGHT_STOPPED_SAFETY_PROVENANCE_OR_BUDGET

Success=0, timeout=0, safety/failure=1.
Wall including repair/preflight=680.3129999999946s/28800; recorded controller+JobCPU=62.671875s.
CPU excludes independent interactive repair/preflight/test processes outside the controller Job. No budget reset.
Stage timing, not full detailed cProfile. Last open intervals are partial; never claim complete killed-stage coverage.

| Probe | nu | VA | Status | C | w | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|---|
| 1 | 0.165 | 5.49375 | NUMERICAL_FAILURE |  |  | 3.437999999994645 | 3.234375 |

MB catalog=147; new26-distance rows=0; improved distances=[].
Reference={'L_km': 21.9393102292, 'old_nu': '0.165', 'old_V_A': '5.5', 'old_K': '0.07798099387393764', 'new_nu': 0.165, 'new_V_A': 5.5, 'new_K': 0.07798099387393764, 'delta_K': 0.0, 'AO_matches_catalog': True, 'runner_up_K': 0.07798091552916897, 'top_two_gap': 7.834476867252249e-08, 'accuracy': 'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'}
22km={'L_km': 22.0, 'old_nu': '0.165', 'old_V_A': '5.475', 'old_K': '0.07661740491526092', 'new_nu': 0.165, 'new_V_A': 5.475, 'new_K': 0.07661740491526092, 'delta_K': 0.0, 'AO_matches_catalog': True, 'runner_up_K': 0.07661723159351552, 'top_two_gap': 1.733217454003011e-07, 'accuracy': 'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'}
ActualAO matches independent catalog 26/26; closed selected directions=0.
P1/P2 actual progress=[{'coordinate': 'P1', 'old_bracket': [5.4875, 5.5125], 'new_bracket': [5.4875, 5.5125], 'old_best_value': 5.5, 'new_best_value': 5.5, 'old_status': 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING', 'new_status': 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING', 'prior_missing_now_measured': [], 'prior_pair_covered': False, 'current_call_refinement_stages_attempted': 1, 'fully_valid_midpoint_pairs_this_call': 0, 'current_call_status': 'SOURCE_MISSING_REFINEMENT', 'next_missing': [{'value': 5.49375, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.4937500000000004'}, {'value': 5.50625, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16500000000000001, V_A=5.5062499999999996'}]}, {'coordinate': 'P2', 'old_bracket': [0.1625, 0.16562500000000002], 'new_bracket': [0.1625, 0.16562500000000002], 'old_best_value': 0.165, 'new_best_value': 0.165, 'old_status': 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING', 'new_status': 'BRACKETED_EXACT_CATALOG_SOURCE_MISSING', 'prior_missing_now_measured': [], 'prior_pair_covered': False, 'current_call_refinement_stages_attempted': 1, 'fully_valid_midpoint_pairs_this_call': 0, 'current_call_status': 'SOURCE_MISSING_REFINEMENT', 'next_missing': [{'value': 0.16375, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16375000000000001, V_A=5.5'}, {'value': 0.16531250000000003, 'status': 'EXACT_SOURCE_MISSING', 'error': 'No hash-matched exact source row for nu_raw=0.16531250000000003, V_A=5.5'}]}]
Missing pairs=55; inspect actual nu0=.8 histories rather than assuming every start matches.

## Limits and next steps

Finite-catalog maximum and locally narrowed brackets are not continuous/global convergence. Original inner cap4/outer6/epsilon1e-8/parameter1e-6 unchanged.
Strictnu>0 still differs from mathematicalnu>=0; outer-domain and tiny-gap total error control remain unresolved.
Current source dependency file identifies minimum next original requests. Additional AP or cap/configuration experiments require separate authority.
Sleep restored=True; no workers=True; deadline respected=True.
Error=RuntimeError('Serious source/numerical/provenance failure: NUMERICAL_FAILURE'). Earlier artifacts/source moments/provenance preserved.
