# Project State

Last updated: `2026-09-02` (threshold/numerical approval gate review)

## Terminal Status

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Authorization: `FROZEN_MANIFOLD_CONSISTENT_CW_VJP_VALIDATION_AMENDMENT_NOT_EXECUTED`.

## Current Pointwise State

- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- MI remains certified at `N_MC=2048`.
- Candidate `1e-13` is `PROPOSED_UNAPPROVED`; historical `1e-12` is
  `INVALID_UNAPPROVED`.
- The real V1 adapter and transactional runtime remain unchanged.
- The completed V1 smoke is provenance-valid and preserved at
  `results/pointwise_guard_smoke_v2.json`, SHA-256
  `4a914944aecb09204187040e461e84cd67e34f4c254647eea8ece2e625854360`.
- V1 outcome: `OPTIMIZATION_EFFECTIVELY_FROZEN`. Both six-step repetitions
  are byte-identical; all 12 steps are pre-update guard rejects; proposed and
  committed updates are zero.
- V2 is implemented and frozen at
  `configs/pointwise_guard_protocol_v2.yaml`, SHA-256
  `6eb21147336e4ca4c305abdf2532fe03eaa8e4bb570a4c8918bdb91638727845`.
- V2 smoke outcome: `OPTIMIZATION_USABLE`.
- V2 smoke artifact SHA-256:
  `321b6dc4fd28168878d84e511478c209379b6c0aa36da5d9e794092317ca36f6`.
- V2 smoke had 12/12 attempted and committed updates, 12/12 admissible
  pre-checks, 12/12 admissible post-checks, 12/12 finite gradients, zero
  rollbacks/equivalence failures/certification failures/provenance failures,
  and byte-identical repetitions.
- `BLOCKED_FOCK_DEPENDENCY` is stale as an active production-backend label:
  the deployed Holevo route is cutoff-independent C4 Gram. The failed dense-
  Fock stress suffix remains preserved diagnostic evidence.
- The threshold-dependent support gate is a genuine blocker. The production
  formal support-identity gate is false and the `1e-14`/`1e-13` comparison is
  outcome-informed. `BLOCKED_NUMERICAL_DEPENDENCY` for baseline selection is
  downstream of this decision.

## V2 Method Decision

Support certification, certified distance from `tau`, and an optional
engineering margin are separate claims. A complete Arb classification or
validated inertia certificate proves support. With global inward-facing
outward endpoints `U_-` and `L_+`,

`certified_margin = min(tau - U_-, L_+ - tau)`

already accounts for interval uncertainty. V2 therefore proposes admission
exactly when support is rigorously certified and `certified_margin > 0`.
`uncertainty_upper` is diagnostic; no positive engineering margin is approved.

Implementation must not treat midpoint ordering as a proof of adjacency or
nearest-round Arb endpoints before the admission decision. The comparison must
be made in Arb or equivalent exact arithmetic and fail closed.

## Exact Next Permitted Action

Implement and freeze a synthetic fast-route VJP validation harness under
EVID-0033. The frozen Full center remains AP-only and cannot enter
complex128-fast gradient certification. No gradient certification, training,
threshold approval, or final-test access is authorized in that task.

Threshold validation executed and failed closed: full-support rank was 256 for
the two learned-like failures while the thresholded production path retained
13/14 modes and exceeded frozen tolerances. The next permitted work is the
frozen support-free backend implementation; no training is authorized.

The evaluation-only full-support backend is now implemented and its
12-fixture validation manifest is frozen. Fallback gradients remain blocked.

The full-support evaluation validation is now authoritative PASS evidence.
The independent gradient/VJP protocol is frozen but unexecuted; only its
analytic fast-path implementation and runner are authorized next.

EVID-0031 freezes the cluster-safe spectral Fréchet amendment for the
fast-path inverse-square-root derivative. It does not authorize gradient
validation execution, fallback differentiation, threshold approval, or training.

EVID-0032 freezes the analytic fast-path VJP and no-override validation runner.
Its frozen Full center cannot pass the fast-route precondition.

EVID-0033 establishes that the frozen Full center is AP-only and cannot support
complex128-fast gradient certification. The next work is a synthetic fast-route
VJP harness freeze, not gradient-certification execution or training.

EVID-0034 freezes the synthetic fast-route harness. It is the only authorized
VJP execution and remains unrelated to Full-center training eligibility.

EVID-0035 preserves the failed v1 harness result and freezes a repaired v2
harness. Only the v2 command is authorized; synthetic validation remains
`NOT_RUN` under the repaired runner.

EVID-0036 supersedes the v2 independent-sector directional fixture only. The
next work is a manifold-consistent synthetic harness freeze; no VJP execution
is authorized under the amendment.

## Lifecycle Restrictions

Do not rerun the V1 smoke, implement a different rule, approve a threshold,
change `tau`, optimizer settings, seeds, states, precision, MI, Holevo, SKR,
trainer semantics, security functional, or frozen model. No publication-scale
training, optimized-MB grid, baseline selection, final-test access, held-out
evaluation, or publication claim is authorized.

## Current Evidence

- EVID-0034: exact certification environment restored.
- EVID-0035: real point-certifier adapter verified.
- EVID-0036: V1 runner and prospective execution manifest frozen.
- EVID-0037: completed V1 smoke and effectively-frozen outcome.
- EVID-0038: V2 methodology review and prospective protocol freeze.
- EVID-0039: V2 implementation and manifest freeze.
- EVID-0040: completed V2 smoke and `OPTIMIZATION_USABLE` outcome.
- DEC-0025: V2 smoke execution authorization.
- DEC-0024: V2 methodology and implementation authorization.
- DEC-0026: V2 usability accepted; publication gate retained.
- EVID-0041: threshold/numerical approval gate review.
- EVID-0043: threshold fixture provenance harness correction; validation not rerun.
- EVID-0044: full-support C4-Gram backend protocol freeze.
- EVID-0045: evaluation backend implementation and validation-manifest freeze.
- EVID-0046: gradient/VJP validation protocol freeze.
- EVID-0047: cluster-safe spectral Fréchet amendment freeze.
- EVID-0048: analytic VJP implementation and execution-manifest freeze.
- EVID-0049: fast-route gradient/VJP feasibility amendment freeze.
- EVID-0050: synthetic fast-route VJP harness and execution-manifest freeze.
- EVID-0051: synthetic fast-route VJP harness repair and v2-manifest freeze.
- EVID-0052: manifold-consistent C/w VJP amendment freeze.
- DEC-0027: minimum prospective threshold validation authorized.
- Methodology artifact SHA-256:
  `dbf1b4dc369195f8ee94bd8870f3a6142a69bba7e3130f2a2d8822e699d5ad77`.
- Threshold gate review artifact SHA-256:
  `3f75ddb9325ee8a15af2b05039232aec0d76088fff2b1e86a3ab3137b1d008de`.

No scientific source, security functional, frozen model, training state, or
test data changed or was accessed in this review.
