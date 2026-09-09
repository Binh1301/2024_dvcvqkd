# Project State

Last updated: `2026-09-10T00:00:00+07:00`

## Active Lifecycle Status

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

The current-manuscript amendment is active.  It replaces the exogenous
`(T,epsilon)` plus fixed-`Z_lower` functional with `(T,epsilon_base)`, a fixed
external phase scenario, `epsilon_total=epsilon_base+c_phi*V_A`, and a
full-physical-interval numerical Holevo maximization.  See
`docs/MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md`.

No training, baseline selection, final-test access, held-out evaluation,
threshold approval, or publication-scale claim is authorized for the amended
functional.  The default configuration deliberately leaves `Cn_phi2` null and
must fail before any numerical run.

## Active Authoritative Model

- Amended `FINAL_MODEL_SPEC.md` SHA-256:
  `f3c118768fc3e4fe5e308d3e660507f815526b86e442100945ab47e6924ca974`.
- Amendment record SHA-256:
  `fae9c754474183f4214db5848c834739278961f6853622b12c7a18eef0bd2776`.
- Required unresolved scientific input: a provenance-backed scenario value
  for `Cn_phi2` in `m^-2/3`, distinct from `Cn2(h)`.
- Required before targeted numerical validation: a prospectively frozen
  full-interval maximizer convergence protocol and independent theory review.

Prior numerical artifacts remain historical evidence only.  They do not
certify the amended functional, because their state/noise and/or Holevo
endpoint definitions differ.

## Historical V3 Status (superseded functional)

### Historical Authoritative Numerical State

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

This is pending a separate numerical/security-method review. It is not a
security theorem, threshold decision, protocol approval, or authorization to
change the frozen functional.

## Exact Next Permitted Action

Before any targeted numerical validation is proposed, obtain a documented
author decision on `Cn_phi2` for each scenario and freeze a new,
full-interval-specific numerical certification protocol.  That protocol must
cover grid/refinement convergence, physical-boundary behavior, maximizer
switching/nonsmoothness, and the `epsilon_base -> epsilon_total` action path.
It also requires an independent security/theory review of the current
full-interval maximization.

The historical V3 method review remains relevant only to old support-threshold
artifacts.  Do not rerun or retune V3, execute its full 12-segment cycle, or
automatically create V4.  Any resulting numerical/domain/security/protocol
change must be proposed explicitly and frozen before a realized evaluation.
Silent regularization is prohibited.

## Lifecycle Restrictions

No publication-scale training, optimized-MB grid, baseline selection,
final-test access, held-out evaluation, threshold approval, or publication
claim is authorized. No full 12-segment V3 run occurred. Claims remain limited
to validated point evidence and the finite hash-bound realized domain; no
uniform continuous-domain conditioning result exists.

The V3 record accurately says that its own run did not change production code;
the later 2026-09-09 current-manuscript amendment did change the active
functional. Final-test data remain inaccessible and untouched.

## Verification

- V3 synthetic preflight: `20/20` passed; artifact SHA-256
  `81fe173259071b3124d13da13cd7618564e566e32c7cba7a4a9ea300acb87b50`.
- Historical combined repository suite: `259 passed` before the amendment.
  Post-amendment targeted test evidence is recorded in EVID-0029.
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
- EVID-0029: current-manuscript model amendment and targeted implementation
  verification.
- DEC-0017: active fail-closed method stop and review requirement.
