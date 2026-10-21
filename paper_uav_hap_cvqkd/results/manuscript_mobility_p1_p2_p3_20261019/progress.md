# Execution ledger - approved manuscript mobility P1/P2/P3 plan

Authority: direct user PLEASE IMPLEMENT THIS PLAN, 2026-10-19; original attached
planning request saved beside this file. The approved conversation plan locks
233 sources, geometry/mission/clouds, exact numerical conventions and lambda rule.

## Tasks

- [x] Inspect authority, Git, frozen hash and protect 4850 pre-existing files.
- [x] Adapter/catalog/geometry/Greedy tests and implementation: 10 tests; independent review approved.
- [x] Runner audit and reference gate: 233 sources, 100 positions/60 geometries; both 30-degree references passed.
- [x] P1 60 unique geometries and 100-position expansion:13980 unique evaluations/23300 rows; 388.563s.
- [x] Cloud archive reuse, P2/Greedy/DP and 10-penalty comparison:1000DP+1000Greedy,20.033s.
- [x] Distance comparison: reuse6758/add465 exact source-channel rows;7223 rows total.
- [x] Plot exports/report,24 current tests and independent source/coverage reviews.
- [x] Scoped task/final review approved; all11 actual PNGs visually checked.

Terminal completion is recorded by validation/final_verification.json and the
subsequent EVID-0197/DEC-0180 documentation handoff. This execution ledger is
frozen before that receipt so its hash can be included in the result manifest.

## Pre-flight interface review

| Producer/consumer | Contract | Finding |
|---|---|---|
| Adapter/runner | Flat candidate rows, MP channel/model, deterministic source hash | Lock API in backend brief |
| Runner/plots | positions/P1/cloud NPZ/mobility summary+series/figure1 CSV | Lock export schema before plotting |
| P1/cloud/strategies | raw maximum first, then positive part; S=(~C)*Kstar | Consistent |
| Existing DP/new Greedy | Same speed, lambda and free start | Existing DP uses F/Nt; independent literal check needed |
| New files/old receipts | Preserve old source/cache bytes | Do not add Greedy to hash-protected uav_mobility.py |
| Per-position reuse | Exact geometry identity, source-independent moments only | xi_f remains candidate-dependent |
| Scientific/lifecycle scope | Synthetic manuscript numerical comparison | No security or publication promotion |

Ruling: work in the existing dirty feature checkout with new files and a full
prior-file manifest. Required verified reference inputs are currently untracked;
relocating to a clean worktree would omit them. No commits or branch mutation.

Ruling: use subagents only for the skill-directed, scoped implementation/review
tasks; root owns orchestration, execution and provenance. No agent may edit old
scientific files, caches, frozen specs, ledgers or external manuscripts.

Execution: backend10 + runner3 + existing binary-cloud6 tests passed before P1.
Full P1 ran with per-geometry hash-bound checkpoints; runner review and
plot-fixture validation proceeded independently without changing scientific inputs.

P1 completed PASS: GH maximum difference 5.828670879282072e-16 bit;
all100 MB selected raw rates positive, all100 Uniform family maxima nonpositive.
Old-file preservation still4845 unchanged,5 permitted ledger files changed.
Cloud scenario0 passed archive identities and seed replay0,1,99. Lambda rule
locked before any trajectory solution: hi=.003156008892416172, representative
9.468026677248516e-6. Plot worker and independent plot reviewer approved3 tests.

Runner review fix: reject missing/duplicate output keys; independently verify
full candidate/trajectory/time-series/statistical coverage. Producer snapshot
now binds bytes at import, rather than at stage completion. Regression tests:
RED2 errors before fix, GREEN5/5 after fix. P1 executed the unchanged a29a1c75
producer; later orchestration has its own immutable snapshot.

Comparison PASS:3000 metric rows,90000 slot rows,210 ordinary and60 paired
statistics rows. Bellman residual maximum1.0842021724855044e-19. Prechosen
mission0 has DP/P2 stationary at index80; Greedy index90→80 (100m). No reselection.
100mission representative-lambda means: K P2=.00015024281866088824,
Greedy=.00015238791176394823, DP=.00015649535266182735; D=0,430.6101833,
172.4329898m respectively. These are finite-grid/catalog synthetic diagnostics.
Figure1 GH ranking stable at all31 angles for Union/MB/Uniform from saved rows.

Ruling: retain this ledger and agent briefs with the requested provenance
artifacts instead of deleting the skill workspace at closure. They document
execution decisions and are included in the immutable final artifact manifest.
