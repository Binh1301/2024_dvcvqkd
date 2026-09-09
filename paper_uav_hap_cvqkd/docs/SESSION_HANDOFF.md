# Session Handoff

Date: 2026-09-10

Lifecycle: NOT_READY_FOR_PUBLICATION_SCALE_RUNS

## Verified

- All 45 Markdown files were inventoried and the authoritative documentation
  hierarchy was inspected.
- Source, tests, configs, experiment entry points, available results, and
  manuscript/PDF availability were audited read-only.
- The C4 transmitter, raw-SKR plumbing, average-energy dual, and finite
  realized-state peak guard are present.
- The current code does not implement target scintillation/AoA/raw-T,
  post-action phase noise, or full-interval Holevo maximization.
- No training, long certification, test access, or experiment was run.

## Documentation changed

- FINAL_MODEL_SPEC.md, EQUATIONS.md, ASSUMPTIONS.md
- CHANNEL_STATE_DISTRIBUTION.md, SECURITY_SCOPE_FREEZE.md
- PAPER_CODE_ALIGNMENT.md, PAPER_TO_CODE.md, KNOWN_ISSUES.md
- PROJECT_STATE.md, NEXT_ACTIONS.md, EXPERIMENT_PLAN.md
- RUNNING_NUMERICAL_EXPERIMENTS.md, NUMERICAL_PARAMETER_FREEZE.md
- PUBLICATION_EXPERIMENT_PROTOCOL.md, README.md

## Open blockers

1. Implement/verify the post-action phase chain and freeze its parameters.
2. Resolve the intended scintillation/AoA/raw-T channel path.
3. Implement/verify the full moving Z interval and inner Holevo maximum.
4. Rebind numerical evidence after the target path exists.

## Exact next task

Implement the smallest deterministic diagnostic/plotting entry point for the
READY_NOW 256-QAM/PMF/C4 figures only; keep target phase/channel/security/SKR
figures disabled until the blockers above are resolved.
