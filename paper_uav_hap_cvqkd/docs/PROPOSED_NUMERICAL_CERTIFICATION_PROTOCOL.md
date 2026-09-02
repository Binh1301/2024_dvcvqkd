# Proposed numerical certification protocol

Status: **PROPOSED DESIGN; ADVERSARIAL REVIEW FAILED; NOT FROZEN; NOT
ACTIVE**.

This proposal replaces neither `FINAL_MODEL_SPEC.md` nor the active numerical
configuration. The historical `1e-12` pseudoinverse rule remains invalid and
unapproved. The `1e-13` threshold is the best current candidate, but it remains
proposed until this protocol is explicitly approved, frozen, implemented, and
rerun. No publication training, final-test access, held-out evaluation, or
optimized-MB selection is authorized.

## Review disposition

The current proposal is not ready for author approval. The pilot data were
used to choose `1e-13` and several feasibility caps, so those data cannot also
serve as independent confirmation. In addition, the repository does not yet
contain the validated interval arithmetic or analytic enclosure required to
prove that a continuous update segment avoids a hard-support boundary.

The `1e-14` calculation is also not a full-support oracle: it retains only
8--30 of the 256 mathematically positive modes. Its agreement with `1e-13` is
useful pilot evidence, not general error control relative to the physical
full-support functional. Full-support arbitrary-precision evidence currently
exists only for the near-coincident stress fixture.

## Why the historical exact-support gate should be revised

For an exact weighted coherent-state Gram operator, mathematical rank is a
property of the physical ensemble. Positive weights and distinct coherent
amplitudes give a linearly independent finite family; the high-precision stress
oracle resolves all 256 positive eigenvalues, including
`lambda_min ~= 1.722e-1099`.

By contrast, `S_delta = {lambda_j(G) > delta}` is the support retained by a
finite-precision regularization. The stress ensemble retains only eight modes
at both `1e-14` and `1e-13`. Equality of two retained supports is therefore:

- a conservative sufficient condition for keeping the same hard projector;
- not necessary when omitted modes change all declared observables by less
  than their frozen error allowances; and
- not sufficient, because two thresholds can omit the same physical modes and
  agree with each other while both disagree with the full-support functional.

The original threshold preregistration gated observable sensitivity. Exact
support identity was added only after rank changes were already known, and the
current preregistration explicitly labels that addition outcome-informed and
unfrozen. This proposal does not silently rewrite that history.

## Candidate threshold

`delta_prod = 1e-13` and `delta_ref = 1e-14` remain pilot candidates.

| Threshold | Retained-rank range | Minimum retained eigenvalue | Maximum retained condition number | Result |
|---|---:|---:|---:|---|
| `1e-14` | 8--30 | `1.0191e-14` | `7.4117e13` | Truncated pilot reference; not a full-support oracle |
| `1e-13` | 8--29 | `1.0820e-13` | `7.5868e12` | All 16 forward fixtures and the high-precision stress oracle pass |
| `1e-12` | 6--27 | `1.3906e-12` | `5.1943e11` | Invalid; stress `w` error is `0.2181586469`, about `6.14e5` allowances |

At `1e-13`, the stress `w` error is `2.79635e-7`, or 78.652% of its
`3.55534e-7` allowance. This limited margin is recorded; it is not hidden by
the otherwise favorable roster results.

## Proposed gates

### 1. Provenance and scope

Before formal recertification, hash-bind the candidate/reference thresholds,
complex128 CPU backend, PyTorch/MKL/thread environment, fixture generator,
seeds, state realization, declared metrics, formulas, and tolerances. Test data
must remain inaccessible. Any hash mismatch fails closed.

### 2. Forward observable gate

For every state and fixture, never roster averages alone, require finite and
physical `C`, `w`, `Z`, `lambda1`, `lambda2`, `lambda3`, `chi_BE`, and
unclipped raw `K`. Require

`|x_prod-x_ref| <= 1e-7 + 1e-6 |x_ref|`

for `C,w,Z,lambda1,lambda2,lambda3`, and

`|x_prod-x_ref| <= 1e-6 + 1e-5 |x_ref|`

for `chi_BE` and raw `K`. Retained sector masks, nearest retained/suppressed
eigenvalues, condition numbers, and exact-support disagreements are recorded
diagnostically, not used as a standalone pass/fail rule.

### 3. High-precision stress gate

Every prospectively declared ill-conditioned stress fixture must agree with an
independent, successively precision-converged, full-support Gram oracle under
the same per-metric limits. The ill-conditioned classes and oracle membership
must be selected mechanically from input construction before any float64
outcome is inspected. Agreement between two float64 thresholds is not an
oracle and cannot satisfy this gate. No eigenvalue-only omitted-mode bound is
currently accepted for `w` because `tau^(-1/2)` and operator matrix elements
also enter the functional.

### 4. Local gradient gate

On fixed-support states, require common-random-number, multi-step central finite
differences to agree with autograd for PS, GS, and VA. Cover MI, `C,w,Z`, all
three symplectic eigenvalues, `chi_BE`, and raw `K`; include gauge-null and
nonzero physical directions. Require at least three consecutive stable step
pairs under the existing `1e-7 + 5e-3 scale` rule and identical plus/minus
support masks. Record the distance from the threshold and internal eigengaps.
Derivative equality is not required at a hard-support transition.

### 5. Support-boundary gate

Bracket detected transitions and report ranks, near-threshold eigenvalues,
one-sided `chi_BE`/`K` limits, and one-sided AD/FD derivatives. A crossing is
forward-benign only when both sides separately pass the reference/oracle gates
and their one-sided `chi_BE` and `K` gap remains within the frozen information
tolerances.

An exact scalar boundary is not currently certifiable. Independent diagnostic
executions of the same reported fixture/path placed the nearest boundary in
`[0.002889168901951052, 0.002889923634]`, width `7.54732e-7`, even though the
transition eigenvalue differed from `1e-13` by only order `1e-18`. Those
cross-runtime values lack raw per-environment hash binding and are pilot
observations only.

### 6. Enhanced support-stable update gate

Plain endpoint mask equality is rejected: a path can cross twice, and exact
mask decisions flicker near the threshold. Plain rollback is also rejected:
the outward-VA diagnostic accepted `0/50` steps when initialized `5e-5` below
the boundary and then repeated the same rejection.

Any formal implementation must instead:

1. inspect the whole proposed segment using a validated interval enclosure;
   endpoint checks and dense finite-node sampling are insufficient;
2. at each interval midpoint, combine an outward-rounded Gram/eigensolver
   enclosure `eta_num` with a guaranteed interval derivative bound
   `L_I >= sup ||dG/dt||_2`; with half-width `h`, require every midpoint
   eigenvalue to remain more than `R_I = eta_num + h*L_I` from the threshold;
3. backtrack or shrink on a crossing/guard violation;
4. restore parameters and optimizer state, and remove or reset the rejected
   normal momentum so an unchanged Adam proposal is not retried indefinitely;
5. log the family, ensemble/state hash, segment, nearest eigenvalue, guard
   margin, backtracking count, and accepted displacement; and
6. bisect unresolved intervals and fail closed at prospectively frozen depth,
   width, or resource limits if a certified enclosure cannot be obtained.

For Adam/AdamW, each trial must snapshot parameters, moments, AMSGrad state,
step counter, schedulers/controllers, dual variables, and all RNG state. The
gradient and provisional moment update are computed once. Backtracking scales
the complete parameter proposal, including AdamW decay, without advancing the
moments repeatedly. Acceptance commits one moment/step update; exhaustion
restores the entire snapshot and records a no-op.

The pilot suggests a parameter-distance diagnostic guard of at least `1e-6`
around the observed transition neighborhood because fixed-side gradients pass
at `rho=1e-6` and become execution-sensitive by `rho=1e-7`. This is not a
frozen universal guard. Formal approval must prospectively define a spectral
guard calibrated from repeated backend/thread runs and then rerun fresh
evidence. It cannot replace `R_I`. A 65-node dyadic sampler or an empirical
float64 residual multiplier is diagnostic only and is not a
continuous-segment certificate.

Proposed feasibility criteria for that future frozen run are:

- at least 90% accepted proposals per family at nominal and 10x learning-rate
  scales, with nonzero physical motion;
- at least 50% accepted steps per family in the declared 100x stress
  trajectories;
- no trapped isotropic trajectory and no more than ten consecutive unchanged
  retries after backtracking/momentum handling; and
- explicit demonstration of feasible tangential motion near each declared
  boundary.

These values are proposed after pilot evidence and must not be called
preregistered. If approved, they must be frozen before a fresh formal run.

### 7. Realized-domain replay

Replay every later hash-bound training-selected and validation-selected
ensemble under all frozen gates. Evaluation ensembles may be replayed only
after all numerical choices are frozen and may never influence selection.
Any provenance, physicality, numerical, guard, or observable failure fails
closed. Claims are restricted to the finite realized admissible domain; no
uniform continuous-domain conditioning claim is allowed.

## Pilot evidence and consequences

- All 16 canonical fixtures pass forward observable tolerances at `1e-13`.
- All 12 support disagreements are forward-benign; worst tolerance use is
  3.573% (`deterministic_gs_only`, `w`).
- The high-precision stress comparison passes, with the `w` margin noted above.
- The maintained local gradient audit passes 12/12 coordinates.
- Direct sweeps find PS `5/1512`, GS `6/1512`, and VA `44/420` admissible
  crossings; none appears at 10x or smaller family learning-rate scale.
- The near-coincident stress fixture remains rank eight across all direct
  probes.
- Random full-model proposals reject `0/960`; 24 objective-free rollback
  trajectories accept `768/768` sequential 100x steps with nonzero motion.
- Near the boundary, ordinary PS/GS tangent probes reject `0/64` each; at 100x
  scale 40/64 PS and 39/64 GS probes remain feasible.
- Plain persistent outward rollback can trap and is therefore not proposed for
  adoption.

The pilot supports continued protocol engineering. It does not yet support
protocol approval, activate `1e-13`, authorize training, or establish a
complete quantum-security proof.

## Required independent confirmation design

Before outcomes are generated, create and hash-bind a certification-only
channel realization with a new seed namespace disjoint from pilot, train,
validation, and test. Freeze physical channel strata, new PS/GS/VA/full
transmitter seeds, a fixed Latin-hypercube VA design, analytic boundary
families, perturbation directions, scales, environments, and all acceptance
criteria. Near-coincident oracle cases must be chosen from their analytic
construction, not observed condition numbers. Report every declared path.

For an iid path claim with target violation rate `q` and one-sided failure
probability `alpha`, prospectively require at least
`ceil(log(alpha)/log(1-q))` independent paths; each stratum needs its own fixed
allocation. This supports only a finite/distributional claim, never a uniform
continuous-domain proof.
