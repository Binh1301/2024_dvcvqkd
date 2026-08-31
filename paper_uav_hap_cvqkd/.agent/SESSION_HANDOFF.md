# Session Handoff

Generated: `2026-08-31T11:11:35+07:00`

Commit/branch: `8daba301cdcb7cc3737323454e6507094848f788` on
`feat/pre-scale-run`.

Worktree: **DIRTY with only this task's certification/state additions relative
to the clean task-start commit**. Review the full diff before staging or
committing.

## Objective and outcome

Implemented a standalone, certification-only Arb/acb direct interval Gram
backend and evaluated the 12 frozen PS/GS/VA/mixed realized paths. The backend
and all requested regressions work, but every realized endpoint spectrum
remains unresolved because validated full eigenvalue isolation fails at all
scheduled precisions. Lifecycle remains:

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

No threshold approval, production training, optimized-MB, baseline selection,
final-test access, security-functional change, `src/cvqkd` change, or frozen
model change occurred.

## Repository checkpoint reconstruction

- Task start was clean at `8daba301...`; index and unstaged diff were empty.
- The reported staged 44-path foundation did not exist.
- HEAD already tracked the prior 19-payload certification foundation, but the
  commit message is `feat: pre scale + history implement` and its scope is
  broader than certification-only.
- No duplicate or misleading checkpoint commit was created.
- Git history still cannot independently prove prospective roster ordering,
  because roster and completed oracle first appear together.

## New certification backend

- Isolated ignored environment: `.venv-cert`.
- Hash-pinned lock: `requirements-certification-flint.lock`.
- python-flint 0.9.0, FLINT 3.6.0, CPython 3.12.10, one FLINT thread.
- Precision schedule: 160, 256, 384 bits.
- Exact binary64 endpoint dyadics are propagated through actual affine/ReLU,
  softmax PS, sigmoid/log-domain VA, GS interpolation/unit-RMS gauge, energy
  normalization, analytic coherent overlaps, and four Hermitian C4 sectors.
- Interval-minus-midpoint Frobenius upper bounds provide rigorous sector
  perturbation radii; strict Weyl classification and dyadic subdivision fail
  closed. Approximate eigensolvers are forbidden.
- Future transaction inventory records model, Adam moments/steps, schedulers,
  dual variable, CPU/CUDA RNG, data/sampler generators, counters, and gradient
  scaler, but integration is defined only and inactive.

## Verification

- Isolated certification regressions: `CURRENTLY_VERIFIED_PASS`, 11/11,
  runtime 0.935 seconds.
- Production suite: `CURRENTLY_VERIFIED_PASS`, 135 discovered: 124 passed and
  11 isolated-backend skips, runtime 8.761 seconds.
- `git diff --check`: pass.
- `FINAL_MODEL_SPEC.md` SHA-256 remains
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.

## Realized 12-path result

- Artifact: `results/rigorous_whole_segment_certification.json`.
- SHA-256:
  `0b09b2d11c1c645fce882cb5d7403161d98973043bb6dce6a9257c3aa0360cd6`.
- Runtime: 1061.9827932000626 seconds.
- Certified: 0/12.
- Rigorously identified crossings: 0/12.
- Unresolved/fail-closed: 12/12.
- Maximum subdivision depth: 0.
- For every realized start/end spectrum, python-flint/FLINT failed validated
  eigenvalue isolation at 160, 256, and 384 bits despite `multiple=True`.
- This is an endpoint eigensystem blocker, not a finite-node pass or a proved
  crossing.

## Portable artifacts

- `results/certification_flint_environment.json`:
  `47f6c51f9c76be1ec7cd7411bb3c638dd6d117c4d592ec25de1c988b60db745b`.
- `results/rigorous_segment_fixture_bundle.json`:
  `1a29b45266c4fa3f0dd8a3773c31665dd49679c64466835a9a92a8b767dd2149`.
- `results/rigorous_whole_segment_certification.json`:
  `0b09b2d11c1c645fce882cb5d7403161d98973043bb6dce6a9257c3aa0360cd6`.
- The worktree portability manifest declares 22 payloads totaling 18,396,880
  bytes. The prior 19-payload foundation is in HEAD; the three new payloads
  and their implementation are uncommitted worktree additions.

## Exact next action

Before another realized-path run, prospectively specify and implement a
validated threshold-shifted Hermitian inertia, verified LDL*, or equivalent
eigencluster enclosure. It must count eigenvalues above candidate `tau`
without isolating every extremely small/clustered eigenvalue, fail on
ambiguous interval pivots, and compose with the existing Arb radii and
subdivision. Do not raise the completed cycle's precision limit or alter a
threshold post hoc.

After implementation, add clustered/repeated/threshold-adjacent and
resource-failure tests, then run a new explicitly versioned prospective cycle.

## Preserved prohibitions and facts

- Configured `1e-12`: invalid and unapproved.
- Candidate `1e-13`: proposed and unapproved.
- MI: `N_MC=2048`.
- Final test remains inaccessible.
- No claims beyond the finite, hash-bound realized admissible PS/GS domain.
- No optimizer rollback integration until standalone certification succeeds.
