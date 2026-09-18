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

`ACTIVE > PREREGISTERED > PROPOSED > HISTORICAL / SUPERSEDED / DEPRECATED`

Frozen labels describe the historical or current scientific contract; they do
not prevent an intentional active-model revision. Historical hashes and
lifecycle labels are provenance, not edit authorization.

Repository-state evidence hierarchy:

1. Active specifications and approved preregistered protocols.
2. Current `src/`, `tests/`, active configs, result artifacts, provenance
   hashes, and reproducible diagnostics.
3. `docs/PROJECT_STATE.md`.
4. `docs/EVIDENCE.md`.
5. `docs/DECISION_LOG.md`.
6. `docs/NEXT_ACTIONS.md`.
7. `.agent/SESSION_HANDOFF.md`.
8. Conversation/sidebar history.

A proposal or handoff is context; current active source/specifications,
approved numerical protocols, valid artifacts, and the current snapshot are
authoritative for the task. Historical text does not block an intentional
revision. If active sources conflict, record the conflict and do not guess.

## Mandatory startup procedure

Before material changes, inspect `git status`, `git branch --show-current`,
`git rev-parse HEAD`, and `git diff`; record the branch, commit, dirty state,
and pre-existing edits. Never overwrite unrelated user changes.

Read the specification, security, numerical, state, evidence, and handoff
documents relevant to the task. Cross-check dynamic scientific claims against
current source, configs, machine-readable artifacts, provenance hashes, tests,
and Git state. Historical freeze text and lifecycle status do not block an
intentional model/specification revision.

Do not rely on chat history for these facts.

## Execution scope

Keep publication-scale training, final-test access, held-out evaluation, and
long numerical campaigns separate from ordinary edits. Run them only when the
current task explicitly includes that work and its scientific prerequisites
are checked; no historical model hash or lifecycle state is required for
ordinary development.

## Scientific and evidence rules

- Do not fabricate citations, measurements, parameters, results, security
  proofs, test counts, or lifecycle status.
- Keep training, validation, and test realizations separate. Never infer test
  performance from validation or canonical fixtures.
- Treat classical QAM and DM-CV-QKD as distinct unless the active protocol
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

After material scientific/numerical work, produce or update machine-readable
evidence first, verify its producer/config/input/schema provenance, and update
the relevant evidence or handoff documents only when needed. Do not touch
state or history files mechanically, and never let prose claim PASS before its
evidence exists.

## End-of-task checks

For material work, verify referenced paths and hashes, inspect the complete
diff, run available scoped checks, run `git diff --check`, and record any
environment blocker. Confirm explicitly whether scientific source, security
functional, training, test access, baseline selection, or threshold validation
changed.
