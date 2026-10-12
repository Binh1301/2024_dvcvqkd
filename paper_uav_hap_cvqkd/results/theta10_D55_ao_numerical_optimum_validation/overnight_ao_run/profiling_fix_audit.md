# Profiling lifecycle repair

Original frozen forensic collector is not edited. Overnight launch redirects ONLY instrumentation to overnight_source_observer.py.
Owner-thread cProfile dumps immediately reenable profiling; multi-snapshot dummy confirms late work and cumulative/non-double-counted totals.
Long AP uses lightweight original-operation stage wrappers plus10s timestamped heartbeats rather than detailed cProfile. Dummy overhead in profiling_overhead_benchmark.json is not an AP runtime prediction.
No numerical operations repeated for snapshots; precision/arguments/order/return values unchanged. Completed inclusive/exclusive times and explicitly open stages survive partial timeout.
No full detailed call-profile claim. Full-run stage coverage is assessed from actual final/partial records, never assumed.

## Production failure and versioned correction

First-stage wrapper used worker.mp.dps on a module, raising AttributeError before AP Gram construction. Initial39 dummy tests missed this integration. Executed observer v1 is preserved, not silently repaired/retried. v2 uses worker.mp.mp.dps and passes real-module dummy operations at all3 original precisions. Full AP coverage and v2 real-source equivalence remain NOT_RUN; no real AP launched after failure. Final41 tests include2 integration checks; no source-moment computation in those tests.
