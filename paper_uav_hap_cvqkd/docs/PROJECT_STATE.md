# Project State

Last updated: `2026-09-01T00:00:00+07:00`

## Current V2.3 Superseding Update

This section supersedes the older V1 next-action language retained below for
history.

- V1 checkpoint commit: `c9e532092a52c79edc7188409989f9e603ac130a`.
- Repository-state reconciliation commit: `d08438dacd8be3f8c36e1c80abb5dc1acb5ae272`.
- V2 source/config freeze commit: `565db027f422c67a2e59403aed96f5604916be51`.
- Current certified exact-tau artifact: V2.2, SHA-256
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`.
- Exact-tau support counts: `17, 29, 7, 8`; four fixtures certified,
  zero unresolved, nearest gaps certified, exact-threshold inertia at 160 bits.
- Current segment freeze manifest: V2.3, SHA-256
  `57e3f7692fcd86c8f31ce70daf7b82a2a8dfa757064a3c44a3be6e6eb426fb1b`.
- V2.3 feasibility artifact: SHA-256
  `b7430af4831d96a7b94d88383aab3a64190aecf4ad50099bc3e6a8901921fd1d`.
- Feasibility result: 0/4 certified, 0 crossings, 4/4 resource-limit rows,
  zero provenance failures, 1800.0383 seconds; full 12-path run prohibited.
- Last durable nodes reached depth 3/3/2, cluster cap 24, and Taylor radii
  `4.188e-5`, `1.607e-6`, and `2.091e-5`; combined far-block inertia remained
  uncertified.
- Hard-watchdog acceptance failed: medium/PS recorded 1004.227 seconds
  against its nominal 450-second limit. The implementation lacks bounded
  process-tree/pipe cleanup, but the realized overrun's exact cause was not
  independently traced.
- The complete combined suite passes 203 tests after the exact-tau gate tests;
  the V2.2 oracle-specific suite passes 8 tests. Production `src/cvqkd`, the
  physical/security functional, and `FINAL_MODEL_SPEC.md` are unchanged.

The exact next action is a prospectively frozen V3 feasibility protocol. It
must first prove process-tree timeout enforcement and durable path-domain
journaling synthetically. It must then retain Taylor coefficient dependence
through fixed congruence and improve far-block reduction before another small
SHA-selected subset is evaluated. No all-12 run is permitted until that new
gate passes quantitatively.

Current V2 task-start commit:
`c9e532092a52c79edc7188409989f9e603ac130a` on `feat/v1-cyclepoint`.
The worktree and index were clean at reconstruction. This commit contains the
complete V1 shifted-inertia implementation, tests, configs, schemas,
documentation, and immutable result artifacts; no duplicate Phase-0 commit is
required.

## Terminal Status

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Publication training, optimized-MB/baseline selection, final-test access, and
threshold approval are not authorized and did not occur. Configured `1e-12`
remains invalid/unapproved; candidate `1e-13` remains proposed/unapproved.

## Frozen Model and Security Scope

`FINAL_MODEL_SPEC.md` SHA-256 remains
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
The physical/security functional and production `src/cvqkd` are unchanged.
MI remains the certified exact discrete-input estimator at `N_MC=2048`.

Claims remain limited to the finite, hash-bound realized admissible PS/GS
domain. No uniform continuous-domain conditioning theorem, finite-size or
composable proof, imperfect-CSI result, or publication performance claim is
established.

## Verification

- Production suite: 156 discovered, 124 passed, 32 certification-only skips,
  zero failures; runtime 6.971 seconds.
- Isolated Arb/inertia suite: 32/32 passed, zero failures; runtime 1.011
  seconds.
- python-flint 0.9.0 / FLINT 3.6.0; precision schedule 160/256/384/512 bits.
- Independent confirmation roster SHA-256:
  `a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de`.
- The certification-only `T, epsilon` realization is disjoint from train,
  validation, pilot, and final test. Final test was not accessed.

## Shifted Point Inertia

For Hermitian `G`, support above proposed `tau` is the positive inertia of
`G - tau I`. Validated Arb/acb 1x1/2x2 block-LDL* with Schur complements and
Sylvester additivity certified:

- 24/24 endpoint rows, 15 unique points, support 13 throughout endpoints;
- zero unresolved endpoint dimensions; all at 160 bits;
- minimum signed pivot/block margin `8.628156120464208e-14`;
- endpoint runtime `63.32869829982519` seconds;
- endpoint artifact SHA-256
  `45b509a94ac94ae92f7c9c03d67465d068d426dcb4da10777e613ab3f0152b5d`.

The four frozen oracle fixtures certify point supports 17, 29, 7, and 8 at
160 bits. Their independent high-precision mathematical rank is 256, proving
that mathematical rank and numerical support are distinct. EVID-0026 now also
independently certifies those four exact-tau counts and nearest gaps with
exact-dyadic Arb inertia brackets.

## Whole-Segment Result

Direct Arb interval propagation plus midpoint Frobenius guard bands and
dyadic subdivision did not solve the continuous-path blocker:

- whole-segment certificates: **0/12**;
- rigorous crossings: **0/12**;
- unresolved fail-closed: **12/12**;
- 299 attempted nodes, 260 resource-limit leaves, zero accepted leaves;
- median/max depth 13/20; median/max precision 512/512 bits;
- final available guard-count gaps 61--63 modes (median 62);
- interval Frobenius radii approximately `1.668e-10` to `1.352e-2`;
- runtime `12302.942093300167` seconds (`3.4175` hours), `11.5849x` the
  previous 1061.9827932-second 0/12 cycle.

The V1 result artifact SHA-256 is
`07d61fe810691f7276fc61005224d405a5ab794f380353e0d9386cc8912a6635`.
It records matching observed hashes for the frozen model, roster, bundle,
endpoint result, environment artifact, configs, and producers.

## Adversarial Restrictions on V1

V1 is valid fail-closed evidence for its observed exact inputs, but no
hypothetical V1 pass may be accepted:

1. The runner records but does not enforce frozen bundle/environment hashes.
2. Its dormant endpoint-rank-difference crossing branch lacks an independent
   whole-path domain/continuity proof.
3. Work limits are cooperative; good/VA recorded 7425.479 seconds against the
   nominal 600-second segment limit, and total runtime exceeded 7200 seconds.
4. `n_zero_or_unresolved=0` can coexist with unequal certified guard counts;
   blocker size must use count gaps and unattempted sectors.
5. Prospective files were hash-bound before results but uncommitted, so Git
   history alone does not establish preregistration chronology.

None of these issues produced a false pass in the 0/12 result.

## Evidence Portability

Commit `34c5eaa...` contains the immutable prior 22-payload failed Arb cycle,
including `results/rigorous_whole_segment_certification.json` at 0/12. Commit
`c9e5320...` checkpoints V1 and the 26-payload, 28,028,606-byte manifest,
including the shifted-inertia environment, endpoint, interval, and oracle
cross-check artifacts. The V1 checkpoint message is `feat: update cycle
point`; it is broader than the suggested certification-only wording but its
tree content is the authoritative checkpoint.

## Quantitative Blockers

1. Direct interval dependency inflation leaves 61--63 near-threshold modes
   ambiguous after depth 20; complete certification remains 0/12.
2. The V1 segment provenance/domain/runtime defects require a new producer
   version before any future pass can be accepted.
3. V2.3 timed out on 4/4 feasibility rows; one nominal 450-second worker
   returned after 1004.227 seconds, so hard process-tree enforcement failed.
4. V2.3 did not persist standalone path-domain artifacts and its durable nodes
   exhausted cluster cap 24 with combined far-block inertia unresolved.
5. Transactional integration covering model, Adam, dual, scheduler, RNG, and
   sampler state is absent and remains downstream.
6. Candidate `1e-13` is unapproved and configured `1e-12` remains invalid.
7. Downstream work remains intentionally unexecuted: zero optimized-MB grid
   evaluations, baseline selections, publication training runs, and final-test
   accesses.

## Exact Next Permitted Action

Create a new prospectively hash-bound V3 feasibility producer with tested
Windows process-tree enforcement, early durable path-domain journaling,
coefficient-level Taylor congruence, and sequential positive/negative
far-block reduction. Freeze and test it before another small realized subset;
do not run 12 paths until that gate passes. Do not change thresholds,
physical/security equations, or downstream lifecycle state.

## Evidence Index

- Frozen implementation and numerical foundation: EVID-0001--EVID-0019.
- Repository checkpoint and prior Arb cycle: EVID-0020--EVID-0022.
- Shifted point inertia/endpoints: EVID-0023.
- Shifted whole-segment fail-closed attempt: EVID-0024.
- Oracle-fixture point cross-check: EVID-0025.
- Exact-dyadic support/gap oracle: EVID-0026.
- Taylor/eigencluster feasibility failure: EVID-0027.
