# Project State

Last updated: `2026-09-01T00:00:00+07:00` (provenance/method review)

## Terminal Status

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

The prospectively frozen V3 feasibility cycle failed closed. The current
incremental hard-support whole-segment method is stopped. Do not rerun or
retune V3, execute the full 12-segment cycle, or automatically create V4.

## Current Authoritative Numerical State

- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- MI remains certified at `N_MC=2048`.
- Candidate threshold `1e-13` remains proposed and unapproved. Historical
  `1e-12` remains invalid and unapproved.
- Exact-tau V2.2 result SHA-256:
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`.
  It certifies support counts `17,29,7,8` and nearest gaps for the four frozen
  point fixtures; it does not approve a threshold or certify whole paths.
- V3 config SHA-256:
  `878a17f51734e2c1565276b5ee13d8a0cf2b7bfedfab5f6a7749409b0ee57a20`.
- V3 preselection-manifest SHA-256:
  `660ea716bc05b933d5b4b342c0fd8b1a5aa9584f3bdc41a93c77577664c210b5`.
- V3 deterministic-selection SHA-256:
  `1ea89229c267c395842757bdee2793d4acfd44946266d9b1b41162c347bdf8ba`.
- V3 execution-manifest SHA-256:
  `5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`.
- V3 feasibility-result SHA-256:
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`.

The V3 chronology is prospective: source/rules were frozen at
`b0ff03b963a50219bcee3439fd9175a9891e39a3`; the preselection manifest was
committed before resolving fixture IDs; the outcome-blind resolver selected
`bad/ps`, `bad/gs`, `bad/va`, and `bad/mixed`; the selection and 20-case
preflight were committed before the final execution manifest; the feasibility
run then used only those four rows.

## V3 Result

- complete fixed-inertia certificates: `0/4`;
- proven crossings: `0/4`;
- resource-limit rows: `4/4`;
- durable path-domain certificates: `4/4`;
- journal-reconstructed attempted/completed nodes: `7/3`;
- durable successful Schur events: `52`;
- runtime: `2438.1743897000006 s` against the frozen `1800 s` total limit;
- realized watchdog outcomes: two bounded returns and two
  `WATCHDOG_CONTRACT_BREACH` rows, with maximum return-bound overshoot
  `637.7792758 s`.

The three completed root nodes reached 512 bits, retained a true-near cluster
of eight, and ended `RESIDUAL_INERTIA_UNCERTIFIED`. Coefficient-level
congruence reduced the paired enclosure-radius ratio to
`0.0265262`, `0.0264878`, and `0.0231441`, and sequential Schur elimination
executed. Terminal unresolved far counts were `53,52,53` (median 53), with
reduced dimensions `61,60,61` (median 61). The mixed row completed no
spectral node before its resource limit.

All four early path-domain artifacts passed their frozen checks. Thus the V2
path-persistence defect was repaired, but path admissibility did not resolve
the spectral proof or watchdog blockers.

## Method Decision

DEC-0017 records the exact proposed engineering conclusion:

`HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`

The separate numerical/security-method review is complete and recorded in
DEC-0018. It concludes that whole-segment
support invariance is an additional differentiability/admissibility condition,
not a prerequisite for the adopted statewise security functional at a
validated realized point. The pointwise-guard protocol design is now frozen by
DEC-0019. Its implementation is complete for the scoped matrix under
DEC-0020; threshold approval, smoke execution, and realized evaluation remain
blocked until their separate gates are met.

Authorization: `POINTWISE_GUARD_ADAPTER_IMPLEMENTATION_AUTHORIZED`.

## Exact Next Permitted Action

Implement the repository-backed validated point-certifier adapter against the
frozen pointwise contract. Do not run the smoke test, approve a threshold,
perform publication training, baseline selection, final-test access, or change
the physical/security functional. Silent regularization is prohibited.

## Lifecycle Restrictions

No publication-scale training, optimized-MB grid, baseline selection,
final-test access, held-out evaluation, threshold approval, or publication
claim is authorized. No full 12-segment V3 run occurred. Claims remain limited
to validated point evidence and the finite hash-bound realized domain; no
uniform continuous-domain conditioning result exists.

Production `src/cvqkd`, the physical/security functional,
`docs/FINAL_MODEL_SPEC.md`, training state, and final-test data were unchanged
by V3.

## Verification

- V3 synthetic preflight: `20/20` passed; artifact SHA-256
  `81fe173259071b3124d13da13cd7618564e566e32c7cba7a4a9ea300acb87b50`.
- Historical locked-environment suite: `259 passed` before V3
  (`LAST_KNOWN_PASS`); current local suite is `BLOCKED_BY_ENVIRONMENT` because
  the locked CPython 3.12.10/torch 2.13.0 environment and pytest are absent.
- Provenance reconciliation: `CURRENTLY_VERIFIED_PASS`; artifact
  `results/provenance_reconciliation_v1.json`.
- Pointwise implementation matrix: `CURRENTLY_VERIFIED_PASS`; artifact
  `results/pointwise_guard_implementation_v1.json`.
- Pointwise smoke: `BLOCKED_BY_ENVIRONMENT`; artifact
  `results/pointwise_guard_smoke_v1.json`.
- Certification environment restore: `BLOCKED_BY_ENVIRONMENT`; artifact
  `results/certification_environment_restore_v1.json`.
- Certification environment restore: `CURRENTLY_VERIFIED_PASS`; artifact
  `results/certification_environment_restore_v2.json`.
- Final V3 manifest hash enforcement and live-environment verification passed.
- V3 journals are fsync-backed and hash-chained; replay reconstructs the
  recorded node and Schur counts.
- Independent roster SHA-256:
  `a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de`.
- Final test remained inaccessible and untouched.

## Evidence Index

- EVID-0026: independent exact-dyadic point support and nearest-gap oracle.
- EVID-0027: historical V2.3 feasibility failure.
- EVID-0028: current decisive V3 feasibility failure.
- EVID-0029: provenance reconciliation and method-review result.
- EVID-0030: pointwise guard protocol design freeze.
- EVID-0031: pointwise guard implementation scoped pass.
- DEC-0017: active fail-closed V3 method stop.
- DEC-0018: pointwise-guard protocol design authorization.
- DEC-0019: pointwise guard protocol freeze and implementation authorization.
- DEC-0020: pointwise implementation pass and smoke authorization.
- DEC-0021: smoke blocked by missing validated backend.
- EVID-0033: certification environment restore blocked.
- EVID-0034: hash-pinned certification environment restored.
- DEC-0022: restored environment accepted; adapter implementation next.
