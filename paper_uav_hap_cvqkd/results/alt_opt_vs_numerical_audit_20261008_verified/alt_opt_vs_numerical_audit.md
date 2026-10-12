# Independent audit: ALT_OPT versus numerical search

Date: 2026-10-08. Scope: diagnostic only.

The executed ALT_OPT is sequential coordinate ascent: V_A at fixed current nu, then nu at the newly selected V_A. Its agreement with numerical search is supported by recorded candidate comparisons and controlled independent replay. Continuous convergence/global optimality remains INCONCLUSIVE.

## Required verdicts

| Question | Verdict | Evidence and code |
|---|---|---|
| 1. Genuine alternating updates? | PASS | All 279 stored iterations / 558 stages reconstructed; scripts/run_theta10_D55_alt_opt_distance_sweep.py:196. |
| 2. Newly updated VA used for nu? | PASS | Fixed argument is after_va['V_A']; every nu history checked against it; scripts/run_theta10_D55_alt_opt_distance_sweep.py:217 . |
| 3. Independent selection or reuse of prior final decisions? | PASS | max(runs_with_final, SKR), scripts/run_theta10_D55_alt_opt_distance_sweep.py:462. Prior CSV used for distance validation, comparison, copying Uniform/fixed and experiment hash only. Its reads were denied in 8 replay scenarios; 32 starts built their own histories. |
| 4. Different algorithms, same exact source catalog? | PASS | A enumerates all 136 available MB pairs. B takes successive slices of that bank, with adaptive exact probes. Evaluated subsets differ (see coverage table). This is shared data availability, not independent discovery of the catalog. |
| 5. Why all 26 final pairs identical? | PASS | The independently followed slices reach A's catalog maximizer at every distance; A's winning row appears in B's actual evaluation log. B does not evaluate all A pairs. Evidence supports agreement on this catalog; it does not prove generic equivalence. |
| 6. Does identical SKR prove correctness? | PASS (consistency only) | Equality alone proves consistency; separate coordinate/candidate/identity/cache/replay checks support implementation correctness within this diagnostic. |
| 7. Fixed-parameter, stale-cache or wrong-distance bug? | PASS for executed updates; FAIL strict source identity | Fixed-coordinate and distance behavior pass; in-memory objective keys include config+channel+exact pair. Source payload implementation hashes differ by CRLF versus LF. Recomputed CRLF hashes reproduce stored hashes, proving newline equivalence, but candidate_from_payload checks ensemble/support/finite C,w only and bypasses strict current implementation identity. |
| 8. What prevents convergence/global optimality? | INCONCLUSIVE | Missing exact source probes, unresolved boundaries and incomplete slices. Every distance reports INNER_SEARCH_FAILURE. Unchanged iterate is catalog stagnation, not convergence. |
| 9. Minimum manuscript validation work? | INCONCLUSIVE for certification | First explicitly reconcile the proven newline-only source identity mismatch with a hash-bound manifest and strict loader validation; do not regenerate or change C,w merely for newline differences. Report present work as cache-limited coordinate ascent. For convergence, prospectively freeze tolerances/resources and complete missing exact probes. Global claims additionally need tail bounds/global enclosures and applicable numerical/security certification. |

## Algorithm comparison

| Component | A: numerical search | B: ALT_OPT |
|---|---|---|
| Search | Full enumeration: 4290 rows, 165 sources/distance | Sequential VA then nu slices; 1357 unique objective rows |
| Candidate generation | Historical evaluated bank labels + Uniform extras + fixed pair | Same historical MB bank labels; exact midpoint/endpoint probes |
| Coordinate updates | None: direct max over MB pair pool (scripts/run_theta10_D55_unconstrained_three_scheme.py:343) | VA argmax, then nu argmax using selected VA (scripts/run_theta10_D55_alt_opt_distance_sweep.py:126) |
| Multi-start | None | .10, .15, .30, .80 plus prior-distance selected pair |
| Exact source reuse | Rebuild common ensemble; match binary64 ensemble hash | Same helper; cached C,w only; misses fail closed unless explicit opt-in |
| Objective cache | In-memory pair+distance memo inside this run; context config held constant | In-memory context(config+channel)+hex(nu)+hex(VA); recreated per distance (scripts/run_theta10_D55_alt_opt.py:123) |
| Boundary exploration | boundary_probe_points returns same pool; classify_closure aggregates across distances (scripts/run_theta10_D55_unconstrained_three_scheme.py:411) | Endpoint halving/doubling (3 attempts), neighbor midpoint refinement (4 stages); open directions recorded |
| Stopping | Finite pool exhausted; no iterative convergence test | max 6 iterations, delta K <= 1e-8 / parameter delta <= 1e-6, with closed-search status required |
| Final selection | Maximum raw SKR among eligible MB pairs | Maximum terminal raw SKR over start trajectories; no prior-final-point fallback |

Important limitation in A: the code does not implement a fresh adaptive expansion in boundary_probe_points. classify_closure compares probe maxima across *all* distances against a maximum selected K across all distances, so its below_selected_best flag is not a per-distance closure certificate. B explicitly retains unresolved statuses. Neither establishes an optimum over all positive nu/VA.

B's previous CSV is read before starts by load_previous_rows for distance completeness and hash provenance; it is read after optimization to copy Uniform/fixed rows and compare the old MB row. Its values do not enter register_exact_catalog, starting_va, coordinate updates or best_run selection. The historical evaluated_points.csv is a permitted, necessary source of candidate parameter labels for both implementations; no K from that bank is read by source_points_from_bank.

## Constraints, catalog and closure

Runtime v_min, v_max, common VA budget and peak constraint are all None. The 1.5 value in defaults is overridden. Search variables must be finite and positive; no preset VA/nu physical upper bound remains. Cache-only availability restricts the actually executable slices. MAX_BOUNDARY_EXPANSIONS=3, MAX_REFINEMENT_STAGES=4, MAX_AO_ITERATIONS=6 are resource caps with unresolved statuses, not physical constraints.

An interior winning catalog point brackets tested neighbors only. Without monotonicity/unimodality assumptions or tail bounds, it does not close the entire unbounded domain. B explores outside a slice only when its current winner is an endpoint; catalog stagnation is not global closure. A VA=6.5 winner only defeats the tested alternatives.

Two unexercised implementation risks remain: adaptive_maximize_1d does not explicitly reject failures from initial catalog probes when later status is bracketed (normal registration excludes missing rows); and the terminal convergence branch tests the current closed slices, while earlier unresolved_inner is only used at the iteration cap. Neither affected this recorded sweep, which correctly terminates INNER_SEARCH_FAILURE. The combined plot CSV's MB status='PASS' means a valid objective evaluation; the optimization status is only in the distance summary/report and must be used for manuscript claims.

## Full 26-distance comparison

| Distance | Numerical nu / VA | ALT_OPT nu / VA | K numerical | K ALT_OPT | Difference | Updates verified | Status |
|---:|---|---|---:|---:|---:|---|---|
| 20 | 0.15 / 6.5 | 0.15 / 6.5 | 0.1380135312811619 | 0.1380135312811619 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 21 | 0.16 / 6.0 | 0.16 / 6.0 | 0.1027071638150534 | 0.1027071638150534 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 21.9393102292 | 0.165 / 5.5 | 0.165 / 5.5 | 0.07798099387393764 | 0.07798099387393764 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 22 | 0.165 / 5.5 | 0.165 / 5.5 | 0.07661685601911128 | 0.07661685601911128 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 23 | 0.165 / 5.3 | 0.165 / 5.3 | 0.05745739941473693 | 0.05745739941473693 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 24 | 0.15 / 5.0 | 0.15 / 5.0 | 0.04337158782779649 | 0.04337158782779649 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 25 | 0.15 / 4.5 | 0.15 / 4.5 | 0.033155735581557266 | 0.033155735581557266 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 25.5 | 0.15 / 4.5 | 0.15 / 4.5 | 0.029094514576219477 | 0.029094514576219477 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 26 | 0.15 / 4.5 | 0.15 / 4.5 | 0.02559880329969072 | 0.02559880329969072 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 26.5 | 0.15 / 4.5 | 0.15 / 4.5 | 0.02258632178693923 | 0.02258632178693923 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 27 | 0.15 / 4.5 | 0.15 / 4.5 | 0.019986441582292652 | 0.019986441582292652 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 27.5 | 0.15 / 4.5 | 0.15 / 4.5 | 0.01773877780029154 | 0.01773877780029154 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 28 | 0.15 / 4.5 | 0.15 / 4.5 | 0.015791856791609243 | 0.015791856791609243 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 29 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.012633752605448606 | 0.012633752605448606 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 30 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.010253503998581354 | 0.010253503998581354 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 30.5 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.009278128392001553 | 0.009278128392001553 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 31 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.008419975631179313 | 0.008419975631179313 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 31.5 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.007663135177788452 | 0.007663135177788452 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 32 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.006994021456280031 | 0.006994021456280031 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 32.5 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.006401020851147396 | 0.006401020851147396 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 33 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.005874192306253717 | 0.005874192306253717 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 34 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.004986168363777209 | 0.004986168363777209 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 35 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.004275173307058823 | 0.004275173307058823 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 36 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.0037005544396879267 | 0.0037005544396879267 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 38 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.0028463445249044643 | 0.0028463445249044643 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |
| 40 | 0.15 / 3.5548673904962893 | 0.15 / 3.5548673904962893 | 0.00225888275226813 | 0.00225888275226813 | 0.0 | True | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |

## Catalog coverage

| L (km) | A available/evaluated MB pairs | B actually evaluated pairs | B outside A | A winner in B |
|---:|---:|---:|---:|---|
| 20 | 136 | 78 | 0 | True |
| 21 | 136 | 76 | 0 | True |
| 21.9393102292 | 136 | 74 | 0 | True |
| 22 | 136 | 74 | 0 | True |
| 23 | 136 | 63 | 0 | True |
| 24 | 136 | 63 | 0 | True |
| 25 | 136 | 62 | 0 | True |
| 25.5 | 136 | 62 | 0 | True |
| 26 | 136 | 62 | 0 | True |
| 26.5 | 136 | 62 | 0 | True |
| 27 | 136 | 62 | 0 | True |
| 27.5 | 136 | 62 | 0 | True |
| 28 | 136 | 40 | 0 | True |
| 29 | 136 | 40 | 0 | True |
| 30 | 136 | 40 | 0 | True |
| 30.5 | 136 | 40 | 0 | True |
| 31 | 136 | 40 | 0 | True |
| 31.5 | 136 | 40 | 0 | True |
| 32 | 136 | 40 | 0 | True |
| 32.5 | 136 | 40 | 0 | True |
| 33 | 136 | 40 | 0 | True |
| 34 | 136 | 40 | 0 | True |
| 35 | 136 | 40 | 0 | True |
| 36 | 136 | 40 | 0 | True |
| 38 | 136 | 40 | 0 | True |
| 40 | 136 | 37 | 0 | True |

## Detailed representative traces

Each successful candidate in alt_opt_iteration_evidence.csv has independently crosschecked I_AB, beta I_AB, chi_BE and K from ao_objective_evaluations.csv. Every exact candidate and missing probe is retained for all starts at the eight representative distances. Source moments are reused from hash-matched stored payloads. Historical objective-cache hits below are reconstructed from execution order and crosschecked against per-stage counters; the counterfactual JSON records actual live call outcomes.

### L=20 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.02328019482360292 | 8.0 | 0.13517615077306733 | 0.15 | 0.1372966251516714 | RUNNING |
| 1 | (0.15, 8.0) | 0.1372966251516714 | 6.5 | 0.1380135312811619 | 0.15 | 0.1380135312811619 | RUNNING |
| 2 | (0.15, 6.5) | 0.1380135312811619 | 6.5 | 0.1380135312811619 | 0.15 | 0.1380135312811619 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.16057681997527432.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.02328019482360292 |
| 0.1 | -0.01050821905528947 |
| 1.075 | 0.0726512688711485 |
| 2.0 | 0.10323452169261449 |
| 2.05 | 0.10434425555765836 |
| 3.025 | 0.11983019004666684 |
| 4.0 | 0.1280314306483995 |
| 4.5 | 0.13062230634776495 |
| 5.0 | 0.13247492179644282 |
| 6.0 | 0.13461089967225492 |
| 8.0 | 0.13517615077306733 |

Missing probes (no K assigned): [16.0].

nu at updated VA: 3 exact comparisons; 2 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.13517615077306733 |
| 0.15 | 0.1372966251516714 |
| 0.165 | 0.13609224508767137 |

Missing probes (no K assigned): [0.125, 0.1575].

### L=21.9393102292 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.016459743778080998 | 6.0 | 0.07590840558617484 | 0.16 | 0.07785179812729415 | RUNNING |
| 1 | (0.16, 6.0) | 0.07785179812729415 | 5.5 | 0.07797104999097981 | 0.165 | 0.07798099387393764 | RUNNING |
| 2 | (0.165, 5.5) | 0.07798099387393764 | 5.5 | 0.07798099387393764 | 0.165 | 0.07798099387393764 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.09431154190537515.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.016459743778080998 |
| 0.1 | -0.008124716470584182 |
| 1.075 | 0.043898830521489435 |
| 2.0 | 0.06172323530135909 |
| 2.05 | 0.06234331490044004 |
| 3.025 | 0.0706023881904847 |
| 4.0 | 0.07437063311089159 |
| 4.5 | 0.07532113603513324 |
| 5.0 | 0.07582774362215494 |
| 6.0 | 0.07590840558617484 |
| 8.0 | 0.07391961405374159 |

Missing probes (no K assigned): [5.5, 7.0].

nu at updated VA: 14 exact comparisons; 13 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.05 | 0.0636197822218838 |
| 0.075 | 0.07249039958432901 |
| 0.1 | 0.07590840558617484 |
| 0.125 | 0.0772800304751039 |
| 0.14 | 0.07767041846840461 |
| 0.145 | 0.07775410365442492 |
| 0.15 | 0.07781455885833477 |
| 0.155 | 0.07784848637372888 |
| 0.16 | 0.07785179812729415 |
| 0.175 | 0.07767482706104412 |
| 0.2 | 0.07689131938448324 |
| 0.5 | 0.01275944210784341 |
| 0.6 | -0.02640606573436688 |
| 0.8 | -0.13266280208522596 |

Missing probes (no K assigned): [0.1575, 0.16749999999999998].

Iteration 1: delta K=0.00012919574664349565.

VA at fixed nu: 7 exact comparisons; 6 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 2.0 | 0.06307139541997625 |
| 5.3 | 0.07793413542155281 |
| 5.4 | 0.07795893684004807 |
| 5.5 | 0.07797104999097981 |
| 5.6 | 0.07797080670452328 |
| 5.7 | 0.07795850275428318 |
| 6.0 | 0.07785179812729415 |

Missing probes (no K assigned): [5.45, 5.55].

nu at updated VA: 16 exact comparisons; 15 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.125 | 0.07734269952629402 |
| 0.145 | 0.0778159593828448 |
| 0.15 | 0.07788595478575067 |
| 0.16 | 0.07797104999097981 |
| 0.165 | 0.07798099387393764 |
| 0.17 | 0.07796600001405829 |
| 0.175 | 0.07792659631833587 |
| 0.18 | 0.0778652633151109 |
| 0.185 | 0.07778451363492767 |
| 0.19 | 0.07768590618436944 |
| 0.25 | 0.0750110497905323 |
| 0.3 | 0.07016273265342177 |
| 0.4 | 0.05233916194180466 |
| 0.5 | 0.025287297963043076 |
| 0.6 | -0.008302907786974623 |
| 0.8 | -0.09635845576048219 |

Missing probes (no K assigned): [0.1625, 0.1675].

Iteration 2: delta K=0.0.

VA at fixed nu: 9 exact comparisons; 8 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.016426587350059852 |
| 2.0 | 0.06309753809460306 |
| 5.3 | 0.07795473107720619 |
| 5.4 | 0.07797458088717046 |
| 5.5 | 0.07798099387393764 |
| 5.55 | 0.07797926607881778 |
| 5.6 | 0.07797430195807054 |
| 5.7 | 0.07795481827188011 |
| 8.0 | 0.07451015168057418 |

Missing probes (no K assigned): [5.45, 5.525].

nu at updated VA: 16 exact comparisons; 0 new objectives; 16 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.125 | 0.07734269952629402 |
| 0.145 | 0.0778159593828448 |
| 0.15 | 0.07788595478575067 |
| 0.16 | 0.07797104999097981 |
| 0.165 | 0.07798099387393764 |
| 0.17 | 0.07796600001405829 |
| 0.175 | 0.07792659631833587 |
| 0.18 | 0.0778652633151109 |
| 0.185 | 0.07778451363492767 |
| 0.19 | 0.07768590618436944 |
| 0.25 | 0.0750110497905323 |
| 0.3 | 0.07016273265342177 |
| 0.4 | 0.05233916194180466 |
| 0.5 | 0.025287297963043076 |
| 0.6 | -0.008302907786974623 |
| 0.8 | -0.09635845576048219 |

Missing probes (no K assigned): [0.1625, 0.1675].

### L=22 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.01627354915177078 | 6.0 | 0.0745539780092942 | 0.16 | 0.07647156367409536 | RUNNING |
| 1 | (0.16, 6.0) | 0.07647156367409536 | 5.5 | 0.07660704382863659 | 0.165 | 0.07661685601911128 | RUNNING |
| 2 | (0.165, 5.5) | 0.07661685601911128 | 5.5 | 0.07661685601911128 | 0.165 | 0.07661685601911128 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.09274511282586614.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.01627354915177078 |
| 0.1 | -0.008053026156356636 |
| 1.075 | 0.04320071346464438 |
| 2.0 | 0.06072786170187516 |
| 2.05 | 0.06133684518846133 |
| 3.025 | 0.06943615268430381 |
| 4.0 | 0.07311175707422457 |
| 4.5 | 0.07402964479352325 |
| 5.0 | 0.07451044626476688 |
| 6.0 | 0.0745539780092942 |
| 8.0 | 0.07252526162186912 |

Missing probes (no K assigned): [5.5, 7.0].

nu at updated VA: 14 exact comparisons; 13 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.05 | 0.06242925753693507 |
| 0.075 | 0.07118145173353341 |
| 0.1 | 0.0745539780092942 |
| 0.125 | 0.07590738789678964 |
| 0.14 | 0.07629259274862044 |
| 0.145 | 0.07637516673850875 |
| 0.15 | 0.07643481913411077 |
| 0.155 | 0.0764682960400026 |
| 0.16 | 0.07647156367409536 |
| 0.175 | 0.07629694121765851 |
| 0.2 | 0.07552382189856177 |
| 0.5 | 0.012198459550632701 |
| 0.6 | -0.02650811896826155 |
| 0.8 | -0.13162740983691246 |

Missing probes (no K assigned): [0.1575, 0.16749999999999998].

### L=25 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.009139222583847242 | 4.5 | 0.032219596774399006 | 0.15 | 0.033155735581557266 | RUNNING |
| 1 | (0.15, 4.5) | 0.033155735581557266 | 4.5 | 0.033155735581557266 | 0.15 | 0.033155735581557266 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.04229495816540451.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.009139222583847242 |
| 0.1 | -0.005019659031773172 |
| 1.075 | 0.019704785977284173 |
| 2.0 | 0.027570491864248037 |
| 2.05 | 0.027830013157674555 |
| 3.025 | 0.03105539321543674 |
| 4.0 | 0.03213498423460537 |
| 4.5 | 0.032219596774399006 |
| 5.0 | 0.03209188618941888 |
| 6.0 | 0.031389683592010886 |
| 8.0 | 0.0289538734543745 |

Missing probes (no K assigned): [4.25, 4.75].

nu at updated VA: 2 exact comparisons; 1 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.032219596774399006 |
| 0.15 | 0.033155735581557266 |

Missing probes (no K assigned): [0.3].

### L=29 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.004390421862070473 | 4.0 | 0.01226514488525611 | 0.1 | 0.01226514488525611 | RUNNING |
| 1 | (0.1, 4.0) | 0.01226514488525611 | 4.0 | 0.01226514488525611 | 0.1 | 0.01226514488525611 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.016655566747326583.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.004390421862070473 |
| 0.1 | -0.0026403591324388187 |
| 1.075 | 0.007634982877951169 |
| 2.0 | 0.010755151094055448 |
| 2.05 | 0.010854150091055101 |
| 3.025 | 0.012012832361435688 |
| 4.0 | 0.01226514488525611 |
| 4.5 | 0.012194256826007166 |
| 5.0 | 0.012031539873570002 |
| 6.0 | 0.011509896630802291 |
| 8.0 | 0.009998634528581407 |

Missing probes (no K assigned): [3.5125, 4.25].

nu at updated VA: 1 exact comparisons; 0 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.01226514488525611 |

Missing probes (no K assigned): [0.05].

### L=30 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.003716300054756794 | 4.0 | 0.009930708177237374 | 0.1 | 0.009930708177237374 | RUNNING |
| 1 | (0.1, 4.0) | 0.009930708177237374 | 4.0 | 0.009930708177237374 | 0.1 | 0.009930708177237374 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.013647008231994167.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.003716300054756794 |
| 0.1 | -0.002272216629084911 |
| 1.075 | 0.006182173429829539 |
| 2.0 | 0.008732857474101241 |
| 2.05 | 0.008813318108849617 |
| 3.025 | 0.00974600234568579 |
| 4.0 | 0.009930708177237374 |
| 4.5 | 0.009859772996158603 |
| 5.0 | 0.009712681928039396 |
| 6.0 | 0.009255250553869387 |
| 8.0 | 0.007948237114960482 |

Missing probes (no K assigned): [3.5125, 4.25].

nu at updated VA: 1 exact comparisons; 0 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.009930708177237374 |

Missing probes (no K assigned): [0.05].

### L=35 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.001820024943267848 | 4.0 | 0.004103492820787369 | 0.1 | 0.004103492820787369 | RUNNING |
| 1 | (0.1, 4.0) | 0.004103492820787369 | 4.0 | 0.004103492820787369 | 0.1 | 0.004103492820787369 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.005923517764055216.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.001820024943267848 |
| 0.1 | -0.0011808489117411947 |
| 1.075 | 0.0025319119496570053 |
| 2.0 | 0.0036319512028778235 |
| 2.05 | 0.0036660761125661516 |
| 3.025 | 0.004050472738951559 |
| 4.0 | 0.004103492820787369 |
| 4.5 | 0.004056768960736784 |
| 5.0 | 0.003975780384633504 |
| 6.0 | 0.0037395924198153213 |
| 8.0 | 0.0030848234541532987 |

Missing probes (no K assigned): [3.5125, 4.25].

nu at updated VA: 1 exact comparisons; 0 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.004103492820787369 |

Missing probes (no K assigned): [0.05].

### L=40 km, nu0=.10

| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | (0.1, 0.025) | -0.0010692584650278225 | 4.0 | 0.002155229885572662 | 0.1 | 0.002155229885572662 | RUNNING |
| 1 | (0.1, 4.0) | 0.002155229885572662 | 4.0 | 0.002155229885572662 | 0.1 | 0.002155229885572662 | INNER_SEARCH_FAILURE |

Iteration 0: delta K=0.0032244883506004846.

VA at fixed nu: 11 exact comparisons; 10 new objectives; 1 objective-cache hits. Search=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; boundary=INTERIOR.

| Candidate value | Exact K |
|---:|---:|
| 0.025 | -0.0010692584650278225 |
| 0.1 | -0.0007185831565131751 |
| 1.075 | 0.0013120310591576475 |
| 2.0 | 0.0019092244897641157 |
| 2.05 | 0.0019276220943046807 |
| 3.025 | 0.0021323446319254195 |
| 4.0 | 0.002155229885572662 |
| 4.5 | 0.002126288829799882 |
| 5.0 | 0.0020784245619626107 |
| 6.0 | 0.001941531938383624 |
| 8.0 | 0.0015655752785688412 |

Missing probes (no K assigned): [3.5125, 4.25].

nu at updated VA: 1 exact comparisons; 0 new objectives; 1 objective-cache hits. Search=BOUNDARY_NOT_CLOSED; boundary=BOUNDARY_NOT_CLOSED.

| Candidate value | Exact K |
|---:|---:|
| 0.1 | 0.002155229885572662 |

Missing probes (no K assigned): [0.05].

## Counterfactual independence test

Prior numerical final-selection CSVs/report were guarded against reads; load_previous_rows and source_moments were patched to raise if called. The guard itself was tested once. The real run_single_distance_ao, adaptive_maximize_1d and deterministic evaluator were reused unchanged. Existing source files and evaluation artifacts were preserved. Each distance was replayed with four starts in forward/reverse order, from a cold in-memory objective cache and a compatible cache preloaded only from B's full objective log. Cache preload was validated against current channel/ensemble identities and cold runs provide independently recalculated SKR. No final-result selections were injected.

| L | Cache | Order | Selected pair | K | Fresh evaluator calls | Status |
|---:|---|---|---|---:|---:|---|
| 21.9393102292 | cold_objective | forward | (0.165, 5.5) | 0.07798099387393764 | 74 | INNER_SEARCH_FAILURE |
| 21.9393102292 | cold_objective | reverse | (0.165, 5.5) | 0.07798099387393764 | 74 | INNER_SEARCH_FAILURE |
| 21.9393102292 | compatible_existing_objective_cache | forward | (0.165, 5.5) | 0.07798099387393764 | 0 | INNER_SEARCH_FAILURE |
| 21.9393102292 | compatible_existing_objective_cache | reverse | (0.165, 5.5) | 0.07798099387393764 | 0 | INNER_SEARCH_FAILURE |
| 25 | cold_objective | forward | (0.15, 4.5) | 0.033155735581557266 | 62 | INNER_SEARCH_FAILURE |
| 25 | cold_objective | reverse | (0.15, 4.5) | 0.033155735581557266 | 62 | INNER_SEARCH_FAILURE |
| 25 | compatible_existing_objective_cache | forward | (0.15, 4.5) | 0.033155735581557266 | 0 | INNER_SEARCH_FAILURE |
| 25 | compatible_existing_objective_cache | reverse | (0.15, 4.5) | 0.033155735581557266 | 0 | INNER_SEARCH_FAILURE |

Start-order stability here is empirical for the two requested distances. Starts can terminate at different pairs even while the best across starts is unchanged. Warm-start/cache sharing is not proof of global uniqueness.

## Accounting and stopping audit

| Counter | Reconstructed | Interpretation |
|---|---:|---|
| objective_calls | 4147 | Initial evaluations plus all stage objective calls |
| unique_exact | 1357 | Unique successful distance+binary64 pair evaluations |
| cache_hits | 1954 | Successful calls reusing same context and pair |
| missing_probes | 836 | Missing-source attempts (including repeats) |
| unresolved_inner | 558 | Unresolved coordinate-search invocations, not distinct global directions |
| unresolved_boundary | 280 | Coordinate invocations reporting BOUNDARY_NOT_CLOSED |
| monotonicity_violations | 0 | Observed stage decreases beyond 1e-8 |

The accounting identity is 4147 = 1357 + 1954 + 836. No numerical failures were recorded. Every audited distance has stagnation among tested candidates together with missing source evaluations; continuous coordinate maximization is incomplete and global boundary closure is unproved. Boundary flags can be INTERIOR on a selected run while other starts at that same distance report open boundaries. No recorded result is numerically converged.

## Provenance and limitations

Branch `10-5-2026`, commit `eec4dd114d9f3ab128f82c37be520dafd197caaa`; pre-existing dirty work preserved.

All prior artifacts, source cache, producer scripts, physical/security code, configs and frozen-spec bytes were hashed before/after the audit. Exact hashes and current source-identity validation are in alt_opt_independence_test.json. No physical/security functional, source moments, training/test access, baseline selection or threshold approval changed.

The current frozen-spec hash differs from the historical expected AGENTS hash. This pre-existing provenance discrepancy remains a lifecycle blocker; the model document was not modified. Publication lifecycle stays NOT_READY_FOR_PUBLICATION_SCALE_RUNS. This audit tests algorithm execution, not the validity of the full quantum-security proof or global error certification.

Strict source-implementation byte identity FAILS for 136/136 registered MB rows. Stored gram_moments.py SHA256=f55c47589422a52224db8798e0c910ceb093eb06d6863b0107e9fd62d2466d48; current=bbad4c303a71ae69be99a4fffba90d968de35f34242977bad03dc1b3e6c5c551. Stored full_support_c4_worker.py SHA256=fe4be5e4b9ce8075f4553f296e32e8f59723bbcfe0b244ab9f6b24886c827ff3; current=2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1. Hashing current bytes with CRLF line endings reproduces the stored hashes exactly. Other identity fields and support_size=256 agree. This is a proven newline-only metadata difference, not evidence of different source mathematics, but it prevents an unqualified claim of strict current-byte cache validation. The original loader accepts payloads by ensemble hash without checking implementation/settings identity; audit did not change it.

## Check registry

| Check | Verdict | Code location |
|---|---|---|
| Objective log contains unique distance/exact-pair keys | PASS | scripts/run_theta10_D55_alt_opt.py:123 |
| Current producers match recorded run hashes | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:721 |
| Every B objective row matches independent A candidate evaluation | PASS | scripts/run_theta10_D55_unconstrained_three_scheme.py:280 |
| SKR identity holds for all A/B objective rows | PASS | scripts/run_skr_vs_link_distance_theta10urad.py:153 |
| All 26 distances use matching distance-dependent channel metadata | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:86 |
| Formal variable constraints removed | PASS | scripts/run_theta10_D55_unconstrained_three_scheme.py:98 |
| Eight representative channels recompute identically | PASS | scripts/run_theta10_D55_unconstrained_three_scheme.py:252 |
| All alternating histories, selections, cache counts and continuation verified | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:126 |
| Aggregate counters reconstructed from execution histories | PASS | scripts/run_theta10_D55_alt_opt.py:160 |
| Per-distance accounting matches summary | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:579 |
| All final B rows selected from own terminal histories | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:462 |
| Counterfactual previous-result inputs blocked | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:101 |
| Cold and warm counterfactuals reconstruct real own histories | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:126 |
| Start order and compatible-cache reuse preserve best selected pair | PASS | scripts/run_theta10_D55_alt_opt_distance_sweep.py:462 |
| Strict byte-for-byte source implementation identity | FAIL | scripts/run_theta10_D55_unconstrained_three_scheme.py:136 |
| Continuous inner-search convergence and global optimality | INCONCLUSIVE | scripts/run_theta10_D55_alt_opt.py:58 |
| Historical frozen-spec hash | INCONCLUSIVE | AGENTS.md:Mandatory startup procedure |
| All prior results, source cache, evaluators, configs and model files unchanged | PASS | audit_alt_opt.py:snapshot |
| Source implementation mismatch is exactly newline-equivalent | PASS | scripts/run_theta10_D55_unconstrained_three_scheme.py:136 |

## Conclusion

ALT_OPT genuinely executes alternating coordinate updates on exact tested slices and independently selects its terminal candidates. Agreement with numerical search is legitimate on the shared available source catalog and is supported by actual histories and cold-cache counterfactual replay. Overall unqualified PASS is withheld: strict source-byte identity FAILS (the discrepancy is independently shown to be newline-only), and continuous convergence/global optimality remains INCONCLUSIVE.
