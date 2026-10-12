# Plan B: complete the difficult P2 paired step (PROPOSED, NOT_RUN)

Only if the selected/reference P2 remains fixedVA5.5 after Plan A. The current
pair is lowernu.16375 and uppernu.16531250000000003. Both are required for the
next complete paired inner stage; original list evaluates lower then upper,
but independent source precomputation can acquire either first without changing
AO when both are subsequently supplied. Neither missing K can be predicted;
either could move bestnu and change future P1/P2 targets.

Recommended first dedicated source: upper(.16531250000000003,5.5), because its
Phase2A AC1/zero-gap/fulltree/sleep receipt is stronger than the older lower
probe's unrecorded power history. This is an observability-risk choice, NOT
evidence it is cheaper or more beneficial. Lower(.16375,5.5) comes next only if
still the required partner, with its own explicit authorization. Lower60min
attempt used3469.96875JobCPU/3595.75wall; upper3516.90625/3595wall. Both need
more than their observed unsuccessful windows OR a resolution of unknown late
stage behavior. No final AP precision progress survived; completion cannot be
predicted and active CPU does not exclude an expensive numerical loop.

Conditional recommendation: dedicated120min ceiling for ONE previously timed-out
source +>=10min processing envelope (130min total), only after approved valid
full-duration observations and stable safety gates. Evidence of near-full CPU
and nearby successful sources makes a bounded longer investigation reasonable,
not a guarantee. If both sources are separately approved together, suggest
250min total=2x120min+10min, never reuse old3h budget. No launch in this task.
The existing instrumented probe_worker passes per-probe-timeout-8 to inner AP;
if choosing an uninstrumented source path, its inner3600s cap would still abort.
Any observer correction remains a separately approved operational change.

If it times out again: save true full-duration stage/progress/resources/CPU/
power, kill wholeJob, restoreSleep, retain failed receipt, no automatic retry,
no invented C/w. Decide whether more time is justified by measured completion
milestones. If stalled/unsafe/provenance failure, stop and diagnose, not extend.

No alternate source pair can substitute a REQUIRED original midpoint merely
because it is faster. Original AO may legitimately request another slice if a
measured optimum moves; follow that logic, not a surrogate. Completed-source
cache avoids duplicate AP; no equivalent partial-resume path currently exists.
If bestnu stays.165 and both partners have no better K, next P2 bracket becomes
[.16375,.16531250000000003] and next partners are(.164375,5.5) and
(.16515625000000003,5.5). These are conditional arithmetic, uncomputed and
NOT preapproved. Safe source completion still does not certify final optimum.
