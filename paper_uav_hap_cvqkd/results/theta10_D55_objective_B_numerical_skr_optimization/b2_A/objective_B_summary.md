# Objective B2: one exact source completed, original AO validated

Probe A `(nu_raw,V_A)=(0.165,5.49375)` SUCCEEDED on the original arbitrary-precision route, one attempt, zero AP timeouts/retries/additional probes. Full support256 and compatible binary64/code/settings provenance verified. New `C=3.2081449662247756`, `w=1.017877140191374e-06`; these are the evaluator's serialized numerical values, not a new error certificate.

Original postprocessing failed ONLY while serializing the unchanged `radius_of_curvature_m=+Infinity` configuration metadata. It was not an AC/watchdog/source-numerical failure. The original controller's `ABORTED_UNSAFE_OR_NUMERICAL_FAILURE` status is retained as raw evidence, not silently corrected. Its source payload, partial20-km CSVs, traceback and receipts are preserved. A separate cache-only recovery reused the original postprocess function, guarded against AP, under the SAME original75-minute deadline. Only output destination/JSON encoding changed: +Infinity is accepted for that metadata field alone; nonfinite moments/objective values still fail.

## Scientific outcome

All26 saved channel identities unchanged. Original MI/direct-Z-minus evaluator computed both the new source and the preexisting extra(.25,2) at all26 distances. Catalog149 = baseline147 + ONE preexisting compatible source + ONE new AP source; not149 newly generated sources. `postprocess_recovery/objective_checkpoint.json` contains3874 metrics. Recovery performed52 new objective evaluations; the earlier failed postprocess evaluated the same two20-km points once, so54 fresh objective calls occurred in B2, with no duplicated AP computation.

Original multistart/warm-chain AO:129 starts,283 outer iterations,618 coordinate calls, independent catalog maximum matched26/26. Best pairs/K and all129 individual terminals remain unchanged.59/129 individual starts attain their distance's maximum; reference4/5, not universal convergence. Zero coordinate searches closed. No new figure is rendered because validated selected SKR data did not change. Objective A, old plots/CSVs/caches and scientific producer files are preserved.

Reference21.9393102292km: selected(.165,5.5), `K=0.07798099387393764`; probe `K=0.07798098033334322`, lower by `1.3540594423488983e-08` bits/use in the implemented numerical evaluator.22km remains(.165,5.475), `K=0.07661740491526092`; probe `K=0.07661706904906529`. No distance improves. A total SKR-error bound sufficient to resolve the reference gap is NOT_ESTABLISHED.

P1 lower exact neighbor advances once: bracket `[5.4875,5.5125]` -> `[5.49375,5.5125]`, width `.025` -> `.01875` (25% narrower). Best VA5.5 unchanged. This is ONE added exact side/neighbor, not a completed paired midpoint refinement level; the new call still attempts stage1 and stops at missing moments. Radius remains about.0125; no parameter-tolerance completion. Next original requests(.165,5.496875) and(.165,5.50625).

P2 makes zero progress: bracket[.1625,.16562500000000002], missing(.16375,5.5) and(.16531250000000003,5.5). Neither was executed. All outer directions/global coverage remain unresolved. Strongest supported result: Level1 finite-catalog maximum with partial local-neighbor evidence, NOT a completed numerical coordinate/multistart or global optimum.

## Runtime and safety

Original source API3033.344s wall; whole source Job including process startup/cleanup3039.063s wall,2938.09375s aggregate CPU. Original controller3064.437s wall including preflight/failed postprocess; failed postprocess6.531s wall/5.8125s JobCPU. Cache-only recovery37.484s Job wall/36.65625s JobCPU, controller39.656s wall. Recovery ended3310.265s (55m10s) after ORIGINAL origin05:44:15.276385Z; deadline06:59:15.276385Z, no clock reset. Final regression/verification/documentation also occur before that deadline; see final_verification.json for later completion time.

AC stable samples PASS, no AC abort or watchdog gap in either real receipt. All Job deadlines respected, watchdog threads gone, nested and outer Sleep leases restored, no matching scientific/controller worker remains at native cleanup check. No power-plan change, profiler or observer.48 scoped tests PASS in8.347s, including independent checks of all3874 metrics, original channel/provenance identities, actual AO iterations/catalog ranking and serializer rejection of nonfinite scientific values. An initial new test used the wrong trajectory field schema; fixed to inspect original `nu/V_A` trajectory points and genuine iteration K fields, without changing outputs/science.1767 protected files hash-identical. Frozen historical hash discrepancy PREEXISTING_UNCHANGED; lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains.

## Fourteen objective answers

1. Highest implemented reference SKR remains0.07798099387393764 (about0.077981 for orientation; accurate decimal digits not certified).
2. Corresponding rawnu=.165,VA5.5; repo-nu conversion is not silently substituted.
3. No available149-source candidate improves it. Missing candidates' values are unknown.
4. P1 needs new actual midpoint source moments; bracket/radius/tolerance and outer closure are unresolved.
5. P2 still needs the two exact sources listed above and numerical/domain closure.
6. Next original P1 request(.165,5.496875), exact hex/key in targeted_exact_probe_plan.csv.
7. A valid result fills the next live P1 request; it does not alone complete a paired stage. Reconstruct actual bracket before choosing further AP.
8. Inner cap4/call restarts. New exact neighbors can tighten future calls; repeating unchanged cache cannot. Fixed-incumbent radius estimate still14 P1/12 P2 successful halvings plus a subsequent loop-entry check, not a guaranteed algorithm convergence bound. Alternative cap16 remains PROPOSED/NOT_RUN.
9. New runner-up gap1.3540594423488983e-08 is near epsilon1e-8, but epsilon is a stopping safeguard, NOT an objective-error bound or proof of a tie.
10. Terminals unchanged:59/129 maximum matches, reference4/5. Startnu0=.8 still(.4,3),K.06912585821984563 with unresolved moments/boundary, not an established separate converged basin.
11. Original full-support precision/settings/implementation validation and exact K decomposition PASS. No pointwise total source+MI+Holevo/K-error certificate; quadrature/source-discrimination limits from B1 remain.
12. Prioritize actual new P1 request(s), then P2; independently assess original-method objective uncertainty, starts/open boundaries and stopping adequacy. No bulk55-point campaign or extra AP here.
13. Existing best-found26-distance curve, real histories, finite-catalog comparison and this bracket update are useful qualified manuscript evidence. Do not claim continuous convergence/global/unique optimum or rewrite Objective A automatically.
14. A future smallest bounded pilot could be ONE(.165,5.496875), fresh75min total/<=60min source/>=15min reserve; current adjacent source took about51min, but next runtime/success is unknown. This is a proposal requiring separate approval, not an execution request or reuse of remaining budget.

## Authoritative result paths

- `source_result.json`, `source_checkpoint.json`, `exact_source_cache/db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59.json`: source/moments/provenance.
- `postprocess_recovery/optimized_skr_26_distances.csv`, `old_vs_new_skr.csv`: all26 selected parameters/MI/Holevo/K and comparison.
- `postprocess_recovery/cache_only_runs.json`, `cache_only_searches.json`, `reference_ao_coordinate_search.csv`: genuine original AO and unresolved searches.
- `postprocess_recovery/recovery_execution.json`, `postprocess_report.json`, `final_verification.json`: recovery/runtime/safety/final verification.

STOP. No additional AP, retry, cap change, model change, manuscript rewrite or publication-scale authorization.
