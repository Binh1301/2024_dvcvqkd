# Project State

Last updated: `2026-08-31T11:11:35+07:00`

Repository commit: `8daba301cdcb7cc3737323454e6507094848f788`

Branch: `feat/pre-scale-run`

Worktree status at task start: **CLEAN**. Commit `8daba301...` already contains
the previously staged certification foundation. Its message is
`feat: pre scale + history implement`, not the proposed dedicated checkpoint
message, and its scope is broader than foundation-only work.

## Terminal Status

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

## Publication-Scale Authorization

**NOT AUTHORIZED**

No publication training, optimized-MB grid, baseline selection, final-test
access, or threshold approval occurred. Active `1e-12` remains unapproved and
numerically invalid; candidate `1e-13` remains proposed.

## Frozen Model and Security Scope

`FINAL_MODEL_SPEC.md` SHA-256:

`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`

The accepted 256-state C4 discrete-modulated CV-QKD security functional is
unchanged. Production Holevo evaluation uses the cutoff-independent C4 Gram
backend; dense Fock is diagnostic only. MI remains the exact discrete-input
estimator with convergence-selected `N_MC=2048`.

## Current Verification

- Locked environment restored in ignored `.venv`: CPython 3.12.10 and torch
  2.13.0+cpu with the exact publication lock.
- Current production dynamic suite: `CURRENTLY_VERIFIED_PASS`, 135 discovered:
  124 passed and 11 certification-only skips, exit code 0, runtime 8.761
  seconds, command `python -m unittest discover -s tests -v`.
- Isolated Arb suite: `CURRENTLY_VERIFIED_PASS`, 11/11 passed, 0 failures,
  runtime 0.935 seconds.
- Environment artifact SHA-256:
  `78c35983aaf7fe9fbc636c80d39b9271ea7930c588b28c4d02703c2e2bce5ff9`.
- Test artifact SHA-256:
  `6709db5bcaec5345281832201075ca9b34a26611c5bb22cf8ed6954d7bb324fe`.

This resolves the missing-PyTorch blocker, not numerical certification.

## Independent Confirmation Foundation

- Outcome-uninspected roster: 18 fixtures and four predeclared oracle fixtures.
- Certification channel seed 202701; fixture seed 27083001.
- 384 channel samples, disjoint from train, validation, final test, and pilot.
- Roster SHA-256:
  `a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de`.
- Roster payload SHA-256:
  `b5c25689c3634c5bf9f525bc7366b8661174f628077d92f128b3feaa5ae09762`.

`T` and `epsilon` are independent by construction in this certification-only
channel. It is not the final held-out set.

## High-Precision Oracle State

`results/independent_confirmation_gram_oracles.json` reports
`MULTI_FIXTURE_FULL_SUPPORT_ORACLE_PASS`:

- 4/4 fixtures have two mathematical-rank-256 precision rows.
- 4/4 converge more tightly than `1e-10`.
- Uniform/Binomial resolve at 600/800 digits.
- Near-coincident phase steps `5e-8` and `2e-7` resolve at 1250/1450 digits.
- Final smallest positive eigenvalues are about `3.17e-573`, `3.76e-380`,
  `2.02e-1137`, and `1.47e-1061`.
- Largest successive full-support difference is `2.39e-256`.

The analytic Gram/operator chain is independent of Fock cutoff and float64
support selection. It does not approve a production threshold or establish a
verified whole-segment float64 enclosure.

## Whole-Segment Support Enclosure State

The original proof-oriented foundation propagates interval values and
derivative bounds through affine/ReLU, softmax, sigmoid/log-VA, GS unit-RMS
gauge, physical energy normalization, and coherent overlaps. Its historical
result remains 0/12 because validated numerical assembly/eigensystem error was
absent.

The new certification-only backend uses python-flint 0.9.0 / FLINT 3.6.0 and
propagates Arb/acb balls through the actual exact-binary64 parameter path.
Validated C4 Gram enclosures, rigorous Frobenius perturbation radii, strict
Weyl classification, and deterministic dyadic subdivision are implemented.
Results under the frozen 160/256/384-bit schedule:

- 11/11 isolated certification regressions pass.
- Obvious and near-boundary scalar non-crossings certify; a known crossing is
  rigorously identified.
- Realized whole-segment certificates: **0/12**.
- Rigorous realized crossings: **0/12**.
- Unresolved fail-closed: **12/12**.
- Maximum subdivision depth: 0; runtime: 1061.9827932000626 seconds.
- Every realized start/end spectrum failed validated eigenvalue isolation at
  160, 256, and 384 bits despite multiplicity handling.
- No realized interval was entered after endpoint failure, so realized
  perturbation-radius/observed-change ratios and certified spectral margins
  are unavailable rather than inferred.

Validated Gram assembly is no longer absent, but the current full-spectrum
eigensolver cannot certify threshold-relative endpoint rank for these highly
clustered spectra. Since endpoints are unresolved, no interval enters
Weyl/subdivision. The logic is not integrated into transactional Adam
acceptance; a complete future state inventory is recorded but inactive.

## Corrected Boundary Diagnostic

- Regenerated artifact SHA-256:
  `a1d780dc76e251662cadbe99e6f8277e7b59a75d13590b85527beda83fc0af67`.
- Bad-state center `0.002889168901951052`, width
  `6.984920454533583e-13`, ranks 14/15.
- Rollback acceptances: 0/50, 5/50, and 50/50.

The old artifact remains quarantined. Neither artifact is a continuous-segment
proof or threshold approval.

## Evidence Portability

At task start, commit `8daba301...` cleanly tracked the prior 19-payload,
16,984,424-byte foundation. No reported 44-path staged set existed, so no
duplicate checkpoint was created. The worktree manifest now declares 22
payloads totaling 18,396,880 bytes, adding the isolated environment, exact
fixture bundle, and realized fail-closed result. Those new worktree additions
are not claimed to be part of the pre-task commit.

Git history does not independently establish prospective roster ordering:
the roster and completed oracle outcomes first appear together in the same
commit. Their embedded producer/config/roster hashes remain verifiable, but
this ordering limitation must not be hidden.

## Frozen Numerical Parameters

| Parameter | Value | Classification |
|---|---:|---|
| `beta_rec` | `0.95` | AUTHOR_APPROVED |
| `V_min`, `V_max` | `0.1`, `4.0 SNU` | AUTHOR_APPROVED |
| `V_A_budget` | `1.5 SNU` | AUTHOR_APPROVED |
| mean photon budget | `0.75` | DERIVED |
| hard peak | `30 photons` | AUTHOR_APPROVED finite-realization scope |
| validation/test MI samples | `2048` | CONVERGENCE_SELECTED |
| precision | float64/complex128 CPU | ACTIVE IMPLEMENTATION |
| active support threshold | `1e-12` | CONFIGURED, INVALID, UNAPPROVED |
| candidate threshold | `1e-13` | PROPOSED ONLY |

No Fock cutoff or support threshold is certified.

## Quantitative Blockers

1. Validated Arb Gram assembly exists, but endpoint Hermitian eigenvalue
   isolation fails at every scheduled precision (160/256/384 bits) for all
   12 realized paths; certificates remain 0/12 and unresolved remain 12/12.
2. A validated threshold-relative inertia/eigencluster enclosure is absent.
   Subdivision cannot start while endpoint rank is unresolved.
3. Transactional optimizer enforcement is absent: no certified integration of
   the segment guard with Adam/model/dual/RNG rollback exists.
4. Candidate `1e-13` remains outcome-informed and author-unapproved; active
   `1e-12` remains invalid. No independent threshold approval has occurred.
5. The roster and completed independent-oracle outcomes enter Git history in
   the same commit, so Git history alone cannot prove pre-outcome ordering.
6. Downstream work remains intentionally unexecuted: 0 optimized-MB grid
   evaluations, 0 baseline selections, 0 publication training runs, and 0
   final-test accesses.

## Scientific Claim Boundary

Claims remain limited to the finite, hash-bound realized admissible PS/GS
domain. No uniform continuous-domain conditioning theorem, attack-class
assignment for adaptive fading average, finite-size/composable proof,
imperfect-CSI result, or publication performance claim is established.

## Next Permitted Action

Prospectively specify and implement a validated threshold-shifted Hermitian
inertia (or equivalent clustered-eigenvalue) enclosure for each C4 sector.
It must count eigenvalues above candidate `tau` without requiring isolation of
every tiny eigenvalue, compose with the existing Arb interval radii and
fail-closed subdivision, and be tested before another 12-path cycle. Do not
raise precision or alter thresholds post hoc, inspect new candidate outcomes,
or run training, baseline selection, optimized-MB, or final test.

## Evidence Index

- Frozen model/transmitter/MI/security backend: EVID-0001 through EVID-0006.
- Candidate diagnostics/domain limitations: EVID-0007 through EVID-0011.
- Superseded environment/portability observations: EVID-0012, EVID-0013.
- Portable artifact set: EVID-0014.
- Independent roster: EVID-0015.
- Locked environment/current tests: EVID-0016.
- Experimental whole-segment enclosure: EVID-0017.
- Corrected boundary diagnostic: EVID-0018.
- Four-fixture full-support oracle: EVID-0019.
- Repository checkpoint reconstruction: EVID-0020.
- Isolated Arb backend and fixtures: EVID-0021.
- Realized Arb fail-closed attempt: EVID-0022.
