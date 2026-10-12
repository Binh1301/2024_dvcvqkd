# Objective B: remove redundant dummy gate; retain actual worker safety

2026-10-10. AP NOT_RUN. No source, channel, SKR, or AO calculation launched.

The removed gate was an additional diagnostic: it spawned a synthetic process
tree before scientific execution and immediately checked its PIDs after Job close.
It did not own or terminate the scientific worker. Its previous failure remains
FAILED; asynchronous teardown is a plausible explanation, not a proven cause.

Removed from the active upper-P1 controller: the embedded dummy child harness,
dummy CLI entry, prelaunch timeout/PID gate, and dummy receipt dependencies.
No separate dedicated dummy test file existed. Existing numerical and safety
regression tests remain. Historical producers and results are not deleted:
the failed controller/test were archived byte-for-byte against their manifest.
The old manifest itself was not rewritten to disguise the two authorized changes.

Safety remains: stable AC verification/watchdog; temporary same-thread Sleep
lease restored on exit; unchanged internal 60-minute evaluator timeout; original
absolute-deadline Windows Job supervisor; whole-Job termination and kill-on-close.
The active controller now checks the actual Job's ActiveProcesses reaches zero
before closing it. Any remaining descendants are terminated and the empty-Job
check is bounded by the existing wall allowance. Query/termination/verification
failure is recorded and blocks continuation; closing the Job remains the fail-safe.
No observer, profiler, heartbeat, scientific evaluator or AO redesign occurred.

64 scoped tests PASS (15.943 seconds). Short integration workers exercised normal
root exit with a remaining descendant and whole-Job timeout. Both Jobs reached
zero active processes, handles closed, Sleep restored, and watchdogs stopped.
These are supervisor tests, not an AP run or a claim that a future scientific
calculation has already succeeded. A negative regression also checks unverified
cleanup blocks progress. Running the controller without explicit execution
approval refuses before creating output or launching workers.

All 1809 protected scientific/config/cache/result hashes are unchanged. The old
failed-run manifest has only the two authorized controller/test path changes;
their archived original bytes match, and its other 1823 entries remain unchanged.
AST comparisons confirm source_child, postprocess_child and probe_limit are
unchanged. The original shared supervisor is untouched. Unrelated dirty worktree
changes are preserved.

Next upper P1 (.165,5.50625) is ready through the tested execution path, conditional
on fresh execution approval and live AC/Sleep/Job checks. Future output is a new
minimal_run/ directory; it has NOT been created. No old budget is reused. The
original 120-minute total/90-minute outer/30-minute reserve ceilings do not extend
the evaluator's 60-minute timeout. No automatic AP/retry/P2.

Objective B remains scientific work, not a new diagnostics project: catalog149,
reference best (.165,5.5), K=.07798099387393764; P1 bracket [5.49375,5.5125].
The paired lower request (.165,5.496875) is also missing. No new C,w/SKR, bracket
refinement, coordinate closure, continuous/global certificate, or lifecycle
promotion is claimed. Machine-readable evidence: verification.json.
