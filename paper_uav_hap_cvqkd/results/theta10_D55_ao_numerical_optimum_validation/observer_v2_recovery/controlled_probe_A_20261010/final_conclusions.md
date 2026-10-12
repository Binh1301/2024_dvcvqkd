# Controlled Probe A — final conclusions

Status: INSTRUMENTATION_FAILURE; stopped after one attempt, no retry, B or P2.

1. Source Job wall-time 4.234 s; controller 19.687 s; recorded controller+source Job CPU 8.375 s (not all test/audit CPU).
2. Windows LongPathsEnabled=0; sidecar temporary pathname 264 characters. Same unchanged atomic writer succeeds on a short name and extended pathname, fails on the ordinary long name. Observer snapshot startup precedes original AP main; failure result-sidecar writing also failed. No permanent Windows setting changed.
3. No valid (C,w), source cache entry, new SKR or expanded catalog. Baseline remains 147 sources/3822 saved metrics. Source fallback scientific formulas and v2 producer bytes are unchanged.
4. Reference old best: (nu,VA)=(0.165,5.5), K=0.07798099387393764 bits/use. At 22 km: (0.165,5.475), K=0.07661740491526092. No new comparison can be made.
5. P1 stays [5.4875,5.5125]; zero additional refinement steps/bracket shrink/best change. Exact paired midpoints remain (0.165,5.49375) and (0.165,5.50625); upper midpoint binary64 is 0x1.6066666666666p+2. No coordinate direction completed.
6. Fresh cache-only AO is NOT_RUN (requires valid new source). Saved original AO evidence still matches the unchanged catalog 26/26; no new 26/26 certification. Full baseline table is a byte-identical explicitly labeled copy, not newly computed SKR.
7. No real AP snapshots, stage/precision coverage or measured instrumentation overhead. Source numerical bottleneck is not localized; only the operational pathname failure is confirmed.
8. 49 current scoped regressions PASS; three native dummy safety cases PASS; 1523 protected hashes unchanged. Source Job contained five processes, watchdog exited, no workers remain, Sleep restored, AC remains connected; deadline respected.
9. Before any separately approved attempt: validate long-path-safe output for snapshot, heartbeat, result sidecar, profiler and exact cache at actual path lengths, plus error reporting when sidecar persistence itself fails. No observer/source repair or AP retry performed here. Remaining P1 and P2 moments, original stopping-limit/accuracy/boundary gaps are still unresolved; no continuous/global optimum claimed.

Ponytail: reused validated v2 entry, original source/AO and native supervisor; audit uses stdlib persistence controls, no alternate numerical method.
Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS; historical frozen-hash discrepancy remains preexisting and unchanged.

Final saved check after state/handoff updates: 353.6824617 s since the same controller origin at 01:08:27.6287887Z, within 90 minutes; all 1523 protected hashes unchanged, no Python worker, 49 tests and diff check PASS. See final_saved_artifact_verification.json. No retry or additional source execution.
