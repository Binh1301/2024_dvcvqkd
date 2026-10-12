# Lower P1 scientific preflight

2026-10-10. CURRENTLY_VERIFIED_PASS_SCIENTIFIC_PREFLIGHT_ONLY.
AP NOT_RUN: the task requires fresh execution confirmation after preflight;
that confirmation is pending. The previous upper-probe budget is closed.

Reconciled 181 compatible cache files: 150 unique positive-MB sources,
two consistent duplicate MB copies counted once, 29 Uniform files excluded
from the MB count. Source identities, implementation/settings provenance,
256-symbol ensembles and finite nonnegative C,w were verified. No scientific
data was repaired or interpolated.

Verified 3,900 saved objective rows at the exact 26-distance grid, with
identical saved channel identities. Each saved selected maximum matches both
an actual original-AO terminal and the finite-catalog maximum. The saved
129 multi-start/warm-start runs were checked, not rerun. This is not a fresh
26-distance AO recheck or a numerical/global-optimality certificate.

Two live original cache-only coordinate calls exactly reproduce the latest
selected-final P1/P2 histories and brackets. Guards reject new AP, fresh SKR,
fresh channel generation and a full-distance AO run during preflight.

P1 at L=21.9393102292 km retains saved incumbent `(0.165,5.5)` with
`K=0.07798099387393764`. Its exact bracket is `[5.49375,5.50625]`, and the
original paired requests are FIRST `(0.165,5.496875)`, SECOND `(0.165,5.503125)`.
Both source moments remain unavailable. The second pair and P2 are not
authorized for AP in the requested single-attempt workflow.

The confirmed lower identity is:

- nu_raw hex: `0x1.51eb851eb851fp-3`.
- V_A hex: `0x1.5fccccccccccdp+2`.
- Compatible key: `9b0e009b708f2099ccf64c1bfdcf1d6d121cf2e85f59a93f5ca6cda53c2e7db3`.
- No compatible source already exists, so no valid prior result would be recomputed.

Original AO defaults `(Rmax,epsilon_opt,parameter_tolerance,inner_steps)` remain
`(6,1e-8,1e-6,4)`. All 1,856 protected hashes, including original evaluators,
settings, completed upper results/cache, and current preparation producers,
remain unchanged. The recorded frozen-model historical discrepancy is
pre-existing and unchanged; no specification was edited or lifecycle promoted.

Native stable-AC samples PASS, a temporary same-thread Sleep lease was verified
and restored, and no AP worker was launched. Actual AP Job containment/watchdog/
deadline/empty-Job cleanup must be checked in the execution phase after fresh
approval, not claimed from this preflight. No dummy gate, observer or profiler
was introduced. Proposed fresh budget: 120min total, <=90min supervisor,
UNCHANGED60min internal timeout, >=30min validation/reporting/cleanup reserve,
ONE attempt, no retry/additional pair/P2. No old budget is reused.

65 regression tests PASS22.326s; no native dummy integration gate was rerun.
Machine-readable evidence: catalog_reconciliation.json, confirmed_candidate.json,
live_reference_searches.json, preflight_verification.json,
protected_input_manifest.json and regression_verification.json.
