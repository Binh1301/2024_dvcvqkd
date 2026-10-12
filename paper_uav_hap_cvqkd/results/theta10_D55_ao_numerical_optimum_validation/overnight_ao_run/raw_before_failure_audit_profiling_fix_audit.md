# Profiling lifecycle repair

Original frozen forensic collector is not edited. Overnight launch redirects ONLY instrumentation to overnight_source_observer.py.
Owner-thread cProfile dumps immediately reenable profiling; multi-snapshot dummy confirms late work and cumulative/non-double-counted totals.
Long AP uses lightweight original-operation stage wrappers plus10s timestamped heartbeats rather than detailed cProfile. Dummy overhead in profiling_overhead_benchmark.json is not an AP runtime prediction.
No numerical operations repeated for snapshots; precision/arguments/order/return values unchanged. Completed inclusive/exclusive times and explicitly open stages survive partial timeout.
No full detailed call-profile claim. Full-run stage coverage is assessed from actual final/partial records, never assumed.
