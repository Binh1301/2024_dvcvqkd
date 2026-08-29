# Decision log

## 2026-08-29 -- propose observable-based numerical certification

Decision status: **PROPOSED; AWAITING AUTHOR APPROVAL**.

- Do not treat exact `support(1e-14)==support(1e-13)` as necessary or
  sufficient for observable correctness.
- Preserve exact support masks/ranks as mandatory diagnostics.
- Propose `1e-13` as production candidate and `1e-14` as stricter reference.
- Require forward-observable, independent high-precision stress, local
  fixed-support gradient, support-boundary, enhanced segment-update, and
  realized-domain replay gates.
- Reject endpoint-only exact-mask rollback. Require a calibrated spectral
  guard, segment checking, backtracking/step shrink, and optimizer-state
  handling.
- Keep all claims finite-realized-domain only.

Rationale: all 12 cross-threshold support changes are observable-benign, while
exact-mask decisions near a transition are execution-sensitive and plain
rollback can trap. The replacement is not activated by this decision record.

Historical state preserved: `1e-12` is invalid and unapproved. `1e-13` and
the replacement gate remain proposed. `FINAL_MODEL_SPEC.md` is unchanged.

