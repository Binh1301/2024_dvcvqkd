# Project State

Last updated: `2026-08-31T00:30:00+07:00`

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`

Branch: `new/qam-256-autoencoder-fix`

Worktree status: **DIRTY**. This work preserves pre-existing edits and adds
staged/untracked files. Inspect both index and worktree before committing.

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
- Current dynamic suite: `CURRENTLY_VERIFIED_PASS`, 124 tests, exit code 0,
  command `python -m unittest discover -s tests -v`.
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

The proof-oriented foundation propagates interval values and derivative bounds
through affine/ReLU, softmax, sigmoid/log-VA, GS unit-RMS gauge, physical energy
normalization, and coherent overlaps. Results:

- Synthetic obvious no-crossing case certifies.
- Synthetic known crossing rejects with 768 unresolved subintervals.
- All 12 realized endpoint changes lie below derivative bounds.
- Bound/observed ratios range from 7.97955 to 52.60276.
- Finite-node gaps to `1e-13` range from `8.0414e-14` to `8.2549e-14`;
  sampled retained rank is 13.
- Whole-segment realized certificates: **0/12**.

There is no validated initial Gram-assembly/Hermitian-eigensystem numerical
enclosure `eta_num`. `numpy.nextafter` expansion and sampled ranks are not a
verified directed-rounding eigensolver. The logic is also not integrated into
transactional Adam acceptance with model, optimizer, dual, and RNG rollback.

## Corrected Boundary Diagnostic

- Regenerated artifact SHA-256:
  `a1d780dc76e251662cadbe99e6f8277e7b59a75d13590b85527beda83fc0af67`.
- Bad-state center `0.002889168901951052`, width
  `6.984920454533583e-13`, ranks 14/15.
- Rollback acceptances: 0/50, 5/50, and 50/50.

The old artifact remains quarantined. Neither artifact is a continuous-segment
proof or threshold approval.

## Evidence Portability

`docs/CERTIFICATION_ARTIFACT_MANIFEST.json` declares 19 non-quarantined
payloads totaling 16,984,424 bytes. Exact `.gitignore` exceptions and payloads
are staged. They are not clean-clone portable from current HEAD until committed.
Unlisted/quarantined/benchmark/smoke files remain ignored and non-authoritative.

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

1. Validated `eta_num` for complex Gram assembly and Hermitian
   eigenvalue/inertia evaluation is absent; realized path certificates are
   0/12.
2. Derivative bounds are 7.98-52.60 times observed endpoint changes while
   finite-node threshold gaps are only `8.04e-14`-`8.25e-14`; ordinary
   float64 expansion cannot close the proof obligation.
3. Transactional optimizer enforcement is absent: no certified integration of
   the segment guard with Adam/model/dual/RNG rollback exists.
4. Candidate `1e-13` remains outcome-informed and author-unapproved; active
   `1e-12` remains invalid. No independent threshold approval has occurred.
5. The portable evidence set is staged but uncommitted, so current HEAD alone
   cannot reconstruct it in a clean clone.
6. Downstream work remains intentionally unexecuted: 0 optimized-MB grid
   evaluations, 0 baseline selections, 0 publication training runs, and 0
   final-test accesses.

## Scientific Claim Boundary

Claims remain limited to the finite, hash-bound realized admissible PS/GS
domain. No uniform continuous-domain conditioning theorem, attack-class
assignment for adaptive fading average, finite-size/composable proof,
imperfect-CSI result, or publication performance claim is established.

## Next Permitted Action

Implement a validated complex Gram assembly plus Hermitian eigenvalue/inertia
enclosure that supplies `eta_num`, compose it with the fail-closed adaptive
segment bisection, and test proof obligations. Do not inspect new candidate
outcomes or run training, baseline selection, optimized-MB, or final test.

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
