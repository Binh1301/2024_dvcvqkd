# Supervisor and Windows power audit

Verified original bounded_process uses absolute monotonic polling, Windows Job
KILL_ON_JOB_CLOSE plus aggregate Job user-CPU ceiling, process wait and final
handle/worker cleanup. Windows Job CPU accounting is aggregate, not exclusive
AP timing. Starts process before Job assignment: a small containment setup race
is a code-level concern, not evidence of escaped workers in these runs. A
suspended-start/assign/resume operational design would require separate approval.

Sleep-safe layer requests ES_CONTINUOUS|ES_SYSTEM_REQUIRED on the owning thread,
verifies/restores prior state and checks AC/noncritical battery before run.
Watchdog polls0.2s, aborts on ACunsafe/readfailure or gap>5s, records gap/lastpower;
5s operational deadline margin and full Job termination remain. This prevents
automatic idle Sleep, not manual suspend, critical hibernation/shutdown or power
loss. A watchdog cannot run during OS suspension; no universal strict wall-time
guarantee during suspension. Overrun must fail even if cleanup later succeeds.

A: initialAC1, laterAC0,15.578s gap, Job125 safety stop at1799.031s; actual
suspension versus scheduler delay UNKNOWN. Do not relabel numerical timeout.
B: old Job return0 after internal AP timeout; no AC/Sleep monitoring receipt
retained for this attempt, so do not infer AC1 or absence of sleep from missing
fields. C: AC1 before/last, no recorded gap, Sleep acquired/restored; AP timeout
and Job124. No stored periodic CPU/RSS/heartbeat history localizes a stall.
Outer45s heartbeat messages, if surfaced in a transient session, report only
elapsed supervision, not numerical progress; retained probe logs only final JSON
or are empty. Missing start/stop timestamps/PIDs explicitly labeled in CSV.

Operational proposals ONLY: stable wiredAC/user no manual Sleep, durable
start/end UTC+monotonic/PID and periodic JobCPU/power/resource/event logs,
atomic append/update ledgers, explicit stop-reason precedence and time reserve.
Use rising CPU and stack changes as diagnostics, not proof of numerical
convergence; no automatic kill/retry of a slow active evaluator based solely on
CPU. Separate source/objective/AO/report workers already exist and should keep
one absolute deadline, final reserve and fulltree cleanup. No power plan changed,
no real AP run or supervisor fix here. Existing scoped dummy regression tests
are run; native continuous heartbeat telemetry remains a proposed enhancement.

Timeout interaction: gram_moments default subprocess timeout3600s, BUT approved
probe_worker intercepts that exact worker launch and sets per_probe_timeout-8s.
Thus a separately approved120min outer limit can actually extend inner AP in
that instrumented path, without changing numerical worker. Increasing ONLY an
unintercepted outer supervisor would leave inner3600s ceiling in place. Inspect
the actual chosen command path before any future dedicated budget approval.
