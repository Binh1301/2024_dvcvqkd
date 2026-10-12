# Confirmed P1 upper candidate: raw(.165,5.50625)

At L21.9393102292km, original adaptive_maximize_1d was called live using149 restored exact objective rows, new-source disabled and AP/fresh-SKR/channel/full-AO calls explicitly guarded. Its history/bracket reproduces the recorded selected-final P1 search exactly; no surrogate/interpolation or invented trajectory.

Current bracket[5.49375,5.5125], incumbentVA5.5,K.07798099387393764. Exact neighbors:

| VA | Stored K (bits/use) |
|---|---|
|5.49375|.07798098033334322|
|5.5|.07798099387393764|
|5.5125|.07798086747835642|

Original stage1 evaluates the following Python binary64 expressions in order:

1. (5.49375+5.5)/2 =5.496875, hex0x1.5fccccccccccdp+2, source missing.
2. (5.5+5.5125)/2 =5.50625, hex0x1.6066666666666p+2, source missing.

The list evaluates BOTH calls before checking their results. Therefore5.50625 is an actual required upper-side dependency, although not the first chronological request or midpoint of the full bracket. Its separately scheduled AP calculation does not change the AO update order. Current stage attempts1, complete paired levels0, statusBRACKETED_EXACT_CATALOG_SOURCE_MISSING/refinementSOURCE_MISSING_REFINEMENT. Inner cap4 has not been exhausted; stopping tolerance1e-6 not reached. No coordinate closure/global-domain certificate.

Proposed upper pair uses nuhex0x1.51eb851eb851fp-3, repo-nuhex0x1.c0ccccccccccdp+2, VAhex0x1.6066666666666p+2. Original complete identity and ensemble hash are in confirmed_candidate.json; cachekeydbb7a2a7024f84f97c455b0b3b564e9a307f369b362f80e055dfbf1e5d49497f. Global compatible cache scan proves no source for this pair. C,w and K are unknown, not predicted.

Fresh proposal ONLY: total7200s/120min, outer AP ceiling5400s/90min, at least1800s/30min reserve, ONE new attempt, no retry/other AP/P2. Original src/cvqkd/gram_moments.py fallback uses subprocess.run(timeout=3600); it is unchanged. Thus actual AP calculation remains capped at60min even with a90min outer ceiling. Extending the internal timeout is NOT authorized here and would need a separate explicit execution-policy decision; increasing only the supervisor cannot provide90min of AP. No old budget is reused and no deadline is started until fresh approval/controller launch.

Current native AC samples and temporary same-thread Sleep acquire/release PASS. Original B2 Job/worker route has verified successful-run receipts, but a fresh native containment/deadline/cleanup preflight must be repeated for the actual approved entry before AP; readiness is not presumed from old receipts. No new controller/profiler/observer/AP process was launched by preparation.

After a future valid upper source: validate/cache exact original Cw, evaluate original SKR at26 saved channels, rerun original multistart/warm AO with unchanged R6/epsilon1e-8/parameter1e-6/inner4, independently rank catalog, record actual new P1/P2 requests and stop. Do not promise gain or a completed paired level: lower midpoint is still missing and the winner/bracket may change. If incumbent stays5.5, an evaluated upper neighbor can change the next right midpoint; recompute the actual original search rather than reuse a stale plan. No additional AP is implied.
