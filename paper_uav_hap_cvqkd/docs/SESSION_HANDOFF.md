# Session Handoff

Date: 2026-09-01

Lifecycle: `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

## Completed V3 Cycle

- Prospectively froze source/rules, then preselection, deterministic fixture
  selection, synthetic preflight, and the final execution manifest.
- Passed the 20-case synthetic preflight and the combined 259-test suite.
- Ran only the selected `bad/ps`, `bad/gs`, `bad/va`, and `bad/mixed`
  feasibility rows.
- Persisted all four path-domain certificates before spectral work.
- Recorded fsync-backed hash-chained node/Schur journals and Job-Object
  watchdog artifacts.
- Stopped after the frozen feasibility gate failed; the full 12-row cycle was
  not run.

## Authoritative Result

V3 result SHA-256:
`5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`.

The result is `0/4` complete certificates, `0/4` crossings, `4/4`
resource limits, `7/3` attempted/completed nodes, 52 durable Schur events,
and `2438.1743897000006 s` runtime against a frozen `1800 s` total. Two
segment returns breached the watchdog grace, by `331.5281874 s` and
`637.7792758 s`. Completed roots retained `53,52,53` unresolved far modes.

V3 config SHA-256:
`878a17f51734e2c1565276b5ee13d8a0cf2b7bfedfab5f6a7749409b0ee57a20`.
Final manifest SHA-256:
`5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`.

## Decision and Next Action

DEC-0017 stops incremental hard-support whole-segment certification under the
current method and records this conclusion:

`HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`

The separate numerical/security-method review and protocol design are complete.
The only next action is `POINTWISE_GUARD_IMPLEMENTATION_AUTHORIZED`: implement
the frozen pointwise guard and complete transactional rollback protocol. This
does not authorize threshold approval, training, or evaluation.

Do not rerun/retune V3, run all 12, create V4 automatically, approve a
threshold, train, run optimized MB/baselines, access final test, or alter the
frozen physical/security equations. `FINAL_MODEL_SPEC.md` and production
`src/cvqkd` remain unchanged.
