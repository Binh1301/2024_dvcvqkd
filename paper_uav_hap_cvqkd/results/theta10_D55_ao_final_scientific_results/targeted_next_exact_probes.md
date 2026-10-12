# Minimal targeted exact-source requests (planning only)

No AP computations are authorized or performed by this export. Priorities follow the actual paired-coordinate request order, not catalog growth. Reassess the incumbent/bracket and active missing requests after each valid source; do not automatically execute all four.

| Order | Raw nu | VA | Search | Current bracket |
|---|---|---|---|---|
| 1 | 0.165 | 5.49375 | P1 | [5.4875, 5.5125] |
| 2 | 0.165 | 5.50625 | P1 | [5.4875, 5.5125] |
| 3 | 0.16375 | 5.5 | P2 | [0.1625, 0.16562500000000002] |
| 4 | 0.16531250000000003 | 5.5 | P2 | [0.1625, 0.16562500000000002] |

P1 lower midpoint is the first requested point, directly testing the narrower variance neighborhood of the reference incumbent. Its upper partner is needed to complete that paired stage only if it remains an active request after reevaluation. P2 lower/upper midpoint order follows the implemented routine; both assess shaping at the current VA only while that slice remains relevant. No SKR gain is promised.

For a separately approved single P1 computation: propose total90min, source ceiling75min, reserve15min for original26distance objective/cache-onlyAO and cleanup, one attempt. The original source evaluator plus previously validated minimal AC/Sleep/Windows Job deadline supervision is required; do not invoke the recently failing observer path. Runtime-to-valid-source is unknown; older stopped attempts do not demonstrate numerical impossibility or predict completion. P2 has timeout history and needs a separately chosen adequate ceiling, not an unapproved extension or automatic retry.

Expected scientific output: original validated C,w with unchanged binary64 key/provenance, exact SKR on26distances, actual incumbent/bracket/nextrequests, original cache-onlyAO and independent finite-catalog comparison. No interpolation or promised convergence.

Four requested points alone do not certify the whole domain. Other distances and nu0=.8 have additional dependencies; original4-stage cap/6outer/stagnation latch, nu=0 endpoint, remote directions and objective-error bounds must remain explicit.

With the incumbent fixed, the present P1/P2 radii would require 14/12 geometric halving levels to reach1e-6, compared with4 stages per inner call. These are conditional planning counts, not a forecast. New source moments alone do not remove the cap/stagnation limitation; no setting or continuation rule is changed in this task.

Exact parameter identities:
{'priority': 1, 'nu_raw': 0.165, 'V_A': 5.49375, 'nu_raw_hex': '0x1.51eb851eb851fp-3', 'V_A_hex': '0x1.5f9999999999ap+2', 'coordinate': 'P1', 'bracket': [5.4875, 5.5125], 'condition': 'Only if still requested by unchanged AO after preceding valid result'}
{'priority': 2, 'nu_raw': 0.165, 'V_A': 5.50625, 'nu_raw_hex': '0x1.51eb851eb851fp-3', 'V_A_hex': '0x1.6066666666666p+2', 'coordinate': 'P1', 'bracket': [5.4875, 5.5125], 'condition': 'Only if still requested by unchanged AO after preceding valid result'}
{'priority': 3, 'nu_raw': 0.16375, 'V_A': 5.5, 'nu_raw_hex': '0x1.4f5c28f5c28f6p-3', 'V_A_hex': '0x1.6000000000000p+2', 'coordinate': 'P2', 'bracket': [0.1625, 0.16562500000000002], 'condition': 'Only if still requested by unchanged AO after preceding valid result'}
{'priority': 4, 'nu_raw': 0.16531250000000003, 'V_A': 5.5, 'nu_raw_hex': '0x1.528f5c28f5c2ap-3', 'V_A_hex': '0x1.6000000000000p+2', 'coordinate': 'P2', 'bracket': [0.1625, 0.16562500000000002], 'condition': 'Only if still requested by unchanged AO after preceding valid result'}
