# Session handoff

Current terminal lifecycle: `READY_FOR_CERTIFICATION_PROTOCOL_APPROVAL`.

The status authorizes review only. It does not freeze the proposed protocol,
approve `1e-13`, authorize training, open the final test set, or authorize the
optimized-MB grid.

Read first:

- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`
- `docs/EVIDENCE.md`
- `docs/DECISION_LOG.md`
- `docs/PROJECT_STATE.md`
- `docs/NEXT_ACTIONS.md`

Key facts:

- exact cross-threshold support identity is neither necessary nor sufficient;
- all 12 observed support disagreements pass existing observable tolerances;
- `1e-13` is the best current candidate but stress `w` uses 78.652% of its
  allowance;
- support-boundary location varies by `7.54732e-7` across executions when the
  eigenvalue is within order `1e-18` of the threshold;
- plain exact-mask rollback can trap and is rejected;
- enhanced spectral guard/segment checking/backtracking is proposed but not
  implemented or frozen;
- active `1e-12` remains invalid and unapproved;
- `FINAL_MODEL_SPEC.md` hash remains
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.

No publication training, held-out evaluation, final-test access, optimized-MB
grid, or baseline selection occurred in this review.

