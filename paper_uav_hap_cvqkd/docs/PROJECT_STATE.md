# Project State

Last updated: `2026-08-31T21:30:00+07:00`

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
that mathematical rank and numerical support are distinct. The high-precision
artifact does not store independent counts above exact candidate `tau`, so it
does not independently confirm those four threshold counts.

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
3. Independent high-precision counts above exact candidate `tau` are absent.
4. Transactional integration covering model, Adam, dual, scheduler, RNG, and
   sampler state is absent and remains downstream.
5. Candidate `1e-13` is unapproved and configured `1e-12` remains invalid.
6. Downstream work remains intentionally unexecuted: zero optimized-MB grid
   evaluations, baseline selections, publication training runs, and final-test
   accesses.

## Exact Next Permitted Action

Create a new prospectively hash-bound segment producer that enforces every
frozen input and actual runtime acceptance, proves path domain/continuity
before any crossing claim, and uses a sharper validated fixed-basis
congruence/cluster, affine/Taylor, or Schur-complement enclosure instead of
the dependency-inflated full-matrix Frobenius guard. Freeze and test that
producer before another realized 12-path run. Do not change thresholds,
physical/security equations, or downstream lifecycle state.

## Evidence Index

- Frozen implementation and numerical foundation: EVID-0001--EVID-0019.
- Repository checkpoint and prior Arb cycle: EVID-0020--EVID-0022.
- Shifted point inertia/endpoints: EVID-0023.
- Shifted whole-segment fail-closed attempt: EVID-0024.
- Oracle-fixture point cross-check: EVID-0025.
