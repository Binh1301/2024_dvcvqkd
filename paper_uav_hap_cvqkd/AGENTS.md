# Project Agent Instructions

## Purpose

This repository implements a HAP-to-UAV 256-state discrete-modulated CV-QKD
research framework with channel-adaptive probabilistic shaping, globally
shared geometric shaping, adaptive modulation variance, direct secret-key-rate
optimization, discrete-modulation security evaluation, and numerical/security
certification.

> The repository is authoritative. Previous Codex/chat/sidebar history is
> optional context and must never be required to continue the project.

## Authority and precedence

Distinguish authority from recency. A newer timestamp does not by itself make
a source authoritative.

Scientific/protocol authority:

`ACTIVE / FROZEN > PREREGISTERED > PROPOSED > HISTORICAL / SUPERSEDED / DEPRECATED`

Repository-state evidence hierarchy:

1. Active/frozen specifications and approved preregistered protocols.
2. Current `src/`, `tests/`, active configs, result artifacts, provenance
   hashes, and reproducible diagnostics.
3. `docs/PROJECT_STATE.md`.
4. `docs/EVIDENCE.md`.
5. `docs/DECISION_LOG.md`.
6. `docs/NEXT_ACTIONS.md`.
7. `.agent/SESSION_HANDOFF.md`.
8. Conversation/sidebar history.

A proposal or handoff never overrides frozen specifications, approved
preregistration, current source, valid artifacts, or the canonical current
snapshot. If sources conflict, fail closed, record the conflict, and do not
guess.

## Mandatory startup procedure

Before material changes:

1. Inspect `git status`, `git branch --show-current`, `git rev-parse HEAD`, and
   `git diff`. Record the branch, commit, dirty state, and pre-existing edits.
   Never overwrite unrelated user changes.
2. Read, in order:
   - `docs/FINAL_MODEL_SPEC.md`
   - `docs/SECURITY_SCOPE_FREEZE.md`
   - `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`
   - `docs/PROJECT_STATE.md`
   - `docs/EVIDENCE.md`
   - `docs/DECISION_LOG.md`
   - `docs/NEXT_ACTIONS.md`
   - `.agent/SESSION_HANDOFF.md`
3. Read every active or proposed protocol referenced by `PROJECT_STATE.md`,
   including `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md` when relevant.
   A proposed protocol is informative only until formally approved.
4. Cross-check dynamic claims against source, configs, machine-readable
   artifacts, provenance hashes, tests, and Git state. Correct a stale
   `PROJECT_STATE.md` before proceeding.
5. Reconstruct the lifecycle status, authorization, frozen model identity,
   active versus proposed rules, certified components, historical/quarantined
   evidence, blockers, prohibited actions, and exact next permitted action.

Do not rely on chat history for any of these facts.

## Frozen-model protection

Recompute the SHA-256 of `docs/FINAL_MODEL_SPEC.md` before model-sensitive
work. The historical expected value is:

`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`

If it differs, do not overwrite or silently restore the file. Report the
discrepancy and record it as a blocker. Never modify this specification unless
the user explicitly authorizes a genuine model-level correction.

## Lifecycle safety gate

Never perform publication-scale training, final-test access, final-test
evaluation, or held-out publication evaluation unless both conditions hold:

1. `docs/PROJECT_STATE.md` validly records
   `READY_FOR_PUBLICATION_SCALE_RUNS`; and
2. current repository evidence proves every prerequisite for that state.

A stale status string is not authorization. If authorization cannot be
proved, use `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

Baseline selection, optimized-MB search, threshold certification, and other
dependency-gated actions must also be explicitly authorized by the current
state and evidence before execution.

## Scientific and evidence rules

- Do not fabricate citations, measurements, parameters, results, security
  proofs, test counts, or lifecycle status.
- Keep training, validation, and test realizations separate. Never infer test
  performance from validation or canonical fixtures.
- Treat classical QAM and DM-CV-QKD as distinct unless the frozen protocol
  explicitly couples them.
- Do not substitute Gaussian-modulation security formulas for the implemented
  discrete modulation.
- Never infer mathematical rank from threshold-retained complex128 support.
- Never treat a stricter float64 threshold as a full-support arbitrary-
  precision oracle.
- Never treat a finite-node or local-gradient diagnostic as proof of
  continuous-segment stability.
- Never call a diagnostic run a certification or a stress fixture a proof over
  the continuous PS/GS domain.
- Invalid, stale, or quarantined provenance cannot support approval.

No material scientific/numerical completion claim may exist only in prose.
Identify supporting artifacts, tests, configs, producer/input hashes, and
scope limitations. Do not write “convergence passed” without traceable
evidence.

## Verification vocabulary

Use these labels exactly where applicable:

- `CURRENTLY_VERIFIED_PASS`
- `LAST_KNOWN_PASS`
- `BLOCKED_BY_ENVIRONMENT`
- `NOT_RUN`
- `FAILED`

Never copy a test count from chat or present an old result as a current
worktree pass. If dependencies are missing, record the dependency and use
`BLOCKED_BY_ENVIRONMENT`.

## Evidence-first update protocol

After material work, update state in this direction:

`Artifact -> Evidence -> Decision -> Project State -> Next Action -> Session Handoff`

1. Produce or update machine-readable/test evidence first.
2. Verify producer, config, input/roster, repository, and schema provenance.
3. Record policy changes in `docs/DECISION_LOG.md`.
4. Refresh the compact current snapshot in `docs/PROJECT_STATE.md`.
5. Refresh the execution queue in `docs/NEXT_ACTIONS.md`.
6. Overwrite `.agent/SESSION_HANDOFF.md` with only the latest handoff.

Update `docs/EVIDENCE.md`, `docs/DECISION_LOG.md`, `docs/PROJECT_STATE.md`,
`docs/NEXT_ACTIONS.md`, and `.agent/SESSION_HANDOFF.md` only as relevant; do
not touch all files mechanically. Never let state prose claim PASS before its
evidence exists.

## End-of-task checks

For material work, verify referenced paths and hashes, inspect the complete
diff, run available scoped checks, run `git diff --check`, and record any
environment blocker. Confirm explicitly whether scientific source, security
functional, frozen model, training, test access, baseline selection, or
threshold approval changed.
