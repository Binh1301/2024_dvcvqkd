# Pointwise Spectral Guard Protocol

Status: `PROPOSED`; protocol design is prospectively frozen and its exact
implementation is authorized as the next task. It does not approve the
`1e-13` threshold, reactivate `1e-12`, authorize training/evaluation, or alter
the physical/security functional.

The machine-readable contract is
`configs/pointwise_guard_protocol_v1.yaml` with schema
`schemas/pointwise_guard_protocol_v1.schema.json`.

## Method boundary

The adopted security calculation evaluates the statewise physical ensemble at
the realized parameter state. Whole-segment support invariance was an added
condition for claiming smooth autograd behavior through a hard threshold; it
was not established as a requirement of the statewise security functional.
The protocol therefore permits local fixed-support gradients only at a
validated point and does not certify any interpolation `theta(t)`,
`0 <= t <= 1`.

The pointwise checker operates on the final weighted C4 coherent-state Gram
representation. It reuses validated shifted-Hermitian block-LDL* inertia and
nearest-eigenvalue bracketing. Complex128 eigenspectra remain diagnostic, not
proof. Any incomplete, non-Hermitian, materially nonphysical, resource-limited,
or provenance-invalid result fails closed.

## Certification unit

`POINTWISE_CERTIFICATION_UNIT = UNIQUE_REALIZED_STATEWISE_PHYSICAL_ENSEMBLE`.

One unit is one row of the final physical `Ensemble={p_i,alpha_i,V_A}` passed
unchanged to MI and Holevo. Exact canonical ensemble hashes deduplicate repeated
rows while preserving an index map. Monte Carlo noise samples, logits before
normalization, and optimizer interpolation points are not security objects and
are not certified individually.

## Threshold and guard

The threshold is an input to the protocol, not a lifecycle decision. It is
bound as both the exact binary64 dyadic and its hexadecimal representation.
The current candidate remains `PROPOSED_UNAPPROVED`; the configured `1e-12`
rule remains `INVALID_UNAPPROVED`.

For the nearest eigenvalue below and above the threshold, the validated point
producer returns brackets `[l_b,u_b]` and `[l_a,u_a]`. Define

```text
certified_margin = min(tau - u_b, l_a - tau)
uncertainty_upper = max((u_b-l_b)/2, (u_a-l_a)/2)
```

The frozen guard is

```text
POINTWISE_ADMISSIBLE iff certified point support passes
                      and certified_margin > 2 * uncertainty_upper.
```

The factor two is the two-sided outward bracket uncertainty, not an empirical
acceptance multiplier. Equality, missing brackets, nonpositive margin, or a
margin that does not strictly exceed the uncertainty is
`POINTWISE_GUARD_BAND_REJECT`. Raw complex128 distance alone is never enough.

## Exact statuses

| Status | Meaning | Update permission |
|---|---|---|
| `POINTWISE_ADMISSIBLE` | Provenance, physicality, support count, nearest-gap brackets, and strict guard pass for the unique realized ensemble. | Local fixed-support gradient may be used. |
| `POINTWISE_GUARD_BAND_REJECT` | Point support is identified, but the certified margin is inside or touches the guard band. | No backward, optimizer update, or dual update. |
| `POINTWISE_CERTIFICATION_FAILED` | Arithmetic, inertia, bracketing, physicality, completeness, or resource gate did not finish. | No backward, optimizer update, or dual update. |
| `PROVENANCE_FAILURE` | Any required hash, threshold representation, environment, roster, producer, schema, trainer, or rollback binding mismatches. | No backward, optimizer update, or dual update. |

## Transaction semantics

The transaction snapshots all mutable state before the point check and before
any stochastic MI draw:

```text
snapshot(theta_n and all state)
pointwise_check(theta_n)
  reject/fail -> restore/no-op
  admissible -> existing raw-SKR loss -> backward once
              -> propose one optimizer update
              -> pointwise_check(theta_{n+1})
                  admissible -> COMMIT
                  reject/fail -> full ROLLBACK
```

No intermediate segment proof is attempted. `ROLLBACK_EQUIVALENCE` requires
exact observable equality to the pre-proposal state, including parameters,
gradients, Adam parameter groups/moments/step counters, energy-dual state,
Python/NumPy/Torch CPU RNG, conditional CUDA RNG, explicit MI generators,
module training flags, and any training counters. Schedulers and GradScaler
are absent in the current repository; if introduced before implementation,
they become mandatory snapshot fields. No persistent sampler object currently
exists.

## Provenance contract

Every result binds the repository commit, canonical frozen-model hash,
pointwise protocol/config hash, exact threshold representation, point producer,
schema, certification environment, confirmation roster, trainer, and rollback
implementation hashes. A mismatch returns `PROVENANCE_FAILURE`; no fallback or
silent continuation is allowed.

## Frozen implementation test matrix

The 20 required cases are frozen in the YAML config. They cover safe,
guard-overlap, unresolved-certification, provenance failure, PS/GS/VA local
gradients, no-backward rejection, commit, complete rollback, all Adam and dual
state restoration, RNG/generator restoration, absent/present scheduler state,
deterministic repeated rejection, and equivalence to an ordinary far-from-
boundary optimizer update.

## Prospective smoke test

The design-only smoke is not run in this task. It uses the three finite
validation representative states from the hash-bound confirmation roster,
initialization seed `202613`, common-random seed `202615`, six steps, frozen
Adam settings from the training configuration, and two identical repetitions.
It records attempted/accepted updates, pre/post rejects, certification and
provenance failures, acceptance rate, guard margins, raw-SKR diagnostics,
runtime, and rollback determinism.

`OPTIMIZATION_USABLE` requires at least one committed update, zero rollback
equivalence failures, zero provenance failures, and byte-identical repeated
traces. `OPTIMIZATION_EFFECTIVELY_FROZEN` means zero commits with every
rejection explained by the frozen guard/certification statuses; no same-cycle
retuning is allowed.

## Claim boundary

Proposed wording:

> Gradient updates are restricted to numerically admissible realized states
> whose numerical support is pointwise separated from the regularization
> boundary by a validated guard criterion. Reported secret-key rates use the
> unchanged validated security functional.

Do not claim global differentiability, continuous-domain support stability,
whole-trajectory certification, mathematical full-rank recovery from
complex128, or operational security against an unspecified adaptive fading
attack class.
