# Decision Log

## DEC-0001 — Freeze C4 transmitter representation

Date: 2026-08-26

Status: ACTIVE

### Context

An unrestricted 256-way PMF plus weighted centering does not guarantee the
standard-form covariance required by the accepted security functional and
confounds PS with physical translation.

### Decision

Use 64 orbit probabilities expanded by fourfold rotation, one globally shared
64-prototype GS geometry, no PMF-weighted translation, an independent adaptive
VA branch, and one statewise scalar physical normalization.

### Rationale

C4 symmetry gives zero displacement, zero pseudomoment, equal quadrature
variance, and unambiguous PS/GS/VA gradient ownership.

### Evidence

- `docs/FINAL_MODEL_SPEC.md`
- `src/modulation/`
- EVID-0002

### Consequences

Claims must say channel-adaptive fourfold-symmetric PS, not unrestricted
256-way shaping. Legacy checkpoints are incompatible.

### Alternatives rejected

Unrestricted 256 logits with PMF-weighted centering and normalization.

### Supersedes / Superseded by

Supersedes the pre-freeze transmitter implementation.

## DEC-0002 — Freeze common energy and hard peak domain

Date: 2026-08-27

Status: ACTIVE

### Context

All schemes require an energy-fair comparison and a finite physical amplitude
domain. Unit-RMS GS and positive softmax probabilities alone do not provide a
uniform peak bound.

### Decision

Use `V_A in [0.1,4.0] SNU`, `E[V_A]<=1.5 SNU`, and fail-closed
`max_i|alpha_i|^2<=30` photons over complete preregistered realizations,
without clipping.

### Rationale

The same box, average budget, and hard physical-symbol rule apply to every
baseline and learned mode.

### Evidence

- `configs/default.yaml`
- `docs/AMPLITUDE_DOMAIN_DECISION.md`
- EVID-0009

### Consequences

Continuous-domain or unevaluated-policy peak claims remain unsupported.

### Alternatives rejected

Soft penalty alone, observed-maximum post hoc bounds, and scheme-specific
energy budgets.

### Supersedes / Superseded by

Supersedes the unresolved peak-domain state.

## DEC-0003 — Select MI sample count 2048

Date: 2026-08-27

Status: ACTIVE

### Context

The exact discrete-input MI Monte Carlo estimator required a sample count
selected without test access under the preregistered sequential rule.

### Decision

Use `N_MC=2048` for validation/test numerical evaluation on the certified
finite roster. Training retains its separately preregistered smaller count.

### Rationale

The machine-readable convergence artifact selects 2048 after the declared
global refinement and replication checks.

### Evidence

- `results/mi_convergence.json`
- `docs/MI_CERTIFICATION_ROSTER.md`
- EVID-0003

### Consequences

Future selected checkpoints still require exact-roster replay. This decision
does not certify Holevo support or publication execution.

### Alternatives rejected

Arbitrary default sample counts and test-tuned selection.

### Supersedes / Superseded by

Supersedes unresolved MI sample count.

## DEC-0004 — Reject configured 1e-12 support rule

Date: 2026-08-28

Status: ACTIVE

### Context

The near-coincident fixture has physical rank 256, while the configured
`1e-12` rule retains six modes and violates frozen `w`, `chi_BE`, and raw-`K`
tolerances.

### Decision

Treat `1e-12` as invalid and unapproved. Keep the configuration approval flag
false and all publication entry points fail closed until a replacement
protocol is approved and certified.

### Rationale

The full-support oracle shows `w` error `0.2181586469` and `chi_BE`/raw-`K`
error about `0.0033089478` bit at `1e-12`.

### Evidence

- `results/near_coincident_gram_oracle.json`
- `results/float64_gram_comparison.json`
- `docs/GRAM_ORACLE_DIAGNOSIS.md`
- EVID-0004 and EVID-0005

### Consequences

No threshold, baseline selection, publication training, or held-out evaluation
is authorized.

### Alternatives rejected

Treating cutoff-256 float64 or agreement among ill-conditioned float64
formulations as ground truth.

### Supersedes / Superseded by

Supersedes the prospectively active but conditional `1e-12` candidate.

## DEC-0005 — Propose observable-based 1e-13 protocol

Date: 2026-08-29

Status: PROPOSED

### Context

Candidate `1e-13` has favorable forward and local-gradient diagnostics, while
exact support identity with `1e-14` fails on 12 fixtures.

### Decision

Propose, but do not activate, `1e-13` with forward-observable,
arbitrary-precision stress, local-gradient, boundary, whole-segment, and
realized-domain replay gates. Preserve support masks as diagnostics.

### Rationale

Exact cross-threshold support identity is neither necessary nor sufficient for
full-support observable accuracy.

### Evidence

- `results/production_gram_certification.json`
- `results/support_threshold_protocol_audit.json`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`
- EVID-0006 through EVID-0008

### Consequences

The candidate remains outcome-informed and cannot be used by production runs.

### Alternatives rejected

Silently activating `1e-13`, retaining exact support equality as the sole
accuracy gate, or using a Gaussian approximation.

### Supersedes / Superseded by

Approval was rejected by DEC-0006; the design remains a proposal.

## DEC-0006 — Reject current certification-protocol approval

Date: 2026-08-30

Status: REJECTED

### Context

The same pilot outcomes influenced the candidate threshold and feasibility
caps. Only one fixture has full-support arbitrary-precision evidence, and no
validated interval whole-segment enclosure exists.

### Decision

Do not approve the proposed protocol or `1e-13`. Preserve pilot artifacts as
diagnostics, quarantine the stale boundary aggregate, and remain
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Rationale

Independent pre-hashed confirmation, mechanically selected high-precision
classes, and rigorous whole-segment numerical bounds are missing.

### Evidence

- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`
- `results/support_boundary_bisection_crn.json` — quarantined
- EVID-0007, EVID-0008, and EVID-0010

### Consequences

No training, threshold recertification, optimized-MB grid, baseline selection,
or test access may proceed.

### Alternatives rejected

Reusing the pilot roster as confirmation, treating float64 `1e-14` as full
support, or treating finite-node sampling as a segment proof.

### Supersedes / Superseded by

Rejects approval of DEC-0005 without deleting its historical proposal.

## DEC-0007 — Restrict numerical claims to finite realized domains

Date: 2026-08-28

Status: ACTIVE

### Context

No uniform conditioning or peak theorem covers the unrestricted continuous
PS/GS parameter space.

### Decision

Limit claims to explicitly enumerated, hash-bound, fail-closed finite
realizations and fixtures. Require later replay of every selected/evaluated
ensemble.

### Rationale

Finite evidence cannot establish uniform continuous-domain conditioning.

### Evidence

- `docs/NUMERICAL_DOMAIN_SCOPE.md`
- `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`
- EVID-0003 through EVID-0010

### Consequences

No claim may extrapolate stress or canonical fixtures to all learned policies.

### Alternatives rejected

Uniform continuous-domain claims without proof.

### Supersedes / Superseded by

Not superseded.

## DEC-0008 — Use validation-only baseline selection

Date: 2026-08-27

Status: ACTIVE

### Context

Uniform, Binomial, fixed-MB, and optimized-MB baselines require common
energy-fair selection without test leakage.

### Decision

Select fixed VA and optimized-MB `(nu,VA)` using the preregistered validation
grids and deterministic tie-break only after numerical certification passes.
The test set cannot influence selection.

### Rationale

This provides fair, reproducible baselines under the same box and average
budget.

### Evidence

- `configs/default.yaml`
- `docs/PUBLICATION_EXPERIMENT_PROTOCOL.md`
- `scripts/select_validation_baselines.py`
- EVID-0011

### Consequences

The policy is active, but no selection has run because its numerical
dependencies are blocked.

### Alternatives rejected

Test-selected baselines, unequal energy budgets, and post hoc grids.

### Supersedes / Superseded by

Not superseded.

## DEC-0009 — Make C4 Gram the production Holevo backend

Date: 2026-08-29

Status: ACTIVE

### Context

The C4 weighted coherent-state Gram representation is cutoff-independent and
algebraically implements the same accepted source-moment functional. Dense
Fock evaluation remains useful diagnostically but is not a stable stress
reference.

### Decision

Route production Holevo evaluation through `c4_gram`; retain
`fock_diagnostic` only as an explicit diagnostic backend. Preserve the same
hard absolute numerical-support rule and security equations.

### Rationale

This removes Fock-tail truncation from production source moments without
changing the accepted security functional.

### Evidence

- `src/cvqkd/gram_moments.py`
- `src/cvqkd/holevo.py`
- `results/production_gram_certification.json`
- EVID-0006

### Consequences

Backend integration is active, but its support threshold remains invalid and
unapproved; publication execution stays blocked.

### Alternatives rejected

Silent Gaussian approximation and dense-Fock production fallback.

### Supersedes / Superseded by

Supersedes dense Fock as the production backend.

## DEC-0010 - Track a minimal portable evidence set

Date: 2026-08-30

Status: ACTIVE, PENDING COMMIT

### Context

The active evidence register cited result payloads ignored by Git, preventing
clean-clone reconstruction.

### Decision

Use a narrow `.gitignore` allowlist and a hash/size manifest for only active,
non-quarantined certification payloads. Keep all unlisted result files ignored.

### Rationale

This preserves reviewable evidence without treating the entire result tree as
authoritative or versioning runtime-only data.

### Evidence

- `docs/CERTIFICATION_ARTIFACT_MANIFEST.json`
- EVID-0014

### Consequences

Nineteen payloads are staged. Portability begins only after commit.

### Alternatives rejected

Blanket-unignore of `results/` and Markdown-only summaries.

### Supersedes / Superseded by

Not superseded.

## DEC-0011 - Freeze the independent confirmation roster before outcomes

Date: 2026-08-30

Status: ACTIVE

### Context

The previous candidate-support diagnostics were outcome-informed and lacked a
disjoint prospective confirmation set.

### Decision

Freeze a new certification-only channel, 18 fixtures, and a four-fixture
high-precision subset with outcome inspection explicitly marked absent.

### Rationale

Membership and precision-class design must precede candidate outcomes to avoid
post hoc selection.

### Evidence

- `configs/independent_confirmation_roster.yaml`
- EVID-0015

### Consequences

The roster foundation exists, but no threshold is approved and final test
remains inaccessible.

### Alternatives rejected

Reusing pilot fixtures as independent confirmation or selecting fixtures after
candidate-threshold inspection.

### Supersedes / Superseded by

Not superseded.

## DEC-0012 - Keep the segment enclosure experimental and fail closed

Date: 2026-08-30

Status: ACTIVE FAIL-CLOSED POLICY; NUMERICAL CONTEXT SUPERSEDED

### Context

Analytic interval/derivative propagation is implemented, but the initial Gram
assembly and Hermitian eigensystem lack a validated numerical enclosure.

### Decision

Classify the current implementation as proof-oriented diagnostic foundation
only. It must return no realized support certificate while `eta_num` is absent.

### Rationale

Endpoint enclosure and finite-node ranks cannot establish whole-segment
separation from a hard eigenvalue threshold.

### Evidence

- `src/validation/whole_segment_support.py`
- EVID-0017

### Consequences

Zero of twelve realized paths certifies. Threshold approval and optimizer
integration remain blocked.

### Alternatives rejected

Empirical safety factors, endpoint-only acceptance, and calling
`numpy.nextafter` a validated Hermitian eigensolver.

### Supersedes / Superseded by

Refined by DEC-0014, which supplies validated Gram arithmetic but retains the
fail-closed policy because endpoint support remains unresolved.

## DEC-0013 - Extend oracle precision only to resolve declared full support

Date: 2026-08-30

Status: ACTIVE DIAGNOSTIC POLICY

### Context

The predeclared 50/80/120/160 digit sequence did not resolve full rank for the
regular Uniform and Binomial fixtures.

### Decision

Freeze a rank-resolution-only extension to 600/800 digits without inspecting
candidate-threshold observables. Preserve the stress schedule at
1050/1250/1450 digits.

### Rationale

The oracle requirement was two successive full-support precisions; unresolved
mathematical rank is not a candidate performance outcome.

### Evidence

- `configs/independent_confirmation_oracle.yaml`
- EVID-0019

### Consequences

All four declared fixtures now have two converged full-rank rows. This remains
an oracle result, not support-threshold approval.

### Alternatives rejected

Treating 160-digit truncated rank as truth or changing the threshold policy.

### Supersedes / Superseded by

Not superseded.

## DEC-0014 - Keep the Arb direct-enclosure backend experimental and require threshold-relative inertia

Date: 2026-08-31

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0015; HISTORICAL FAIL-CLOSED EVIDENCE

### Context

Validated Arb/acb propagation now covers the actual PS/VA/GS parameter path,
but full endpoint eigenvalue isolation fails for all 12 realized segments at
160, 256, and 384 bits. Increasing subdivision cannot repair an unresolved
endpoint spectrum.

### Decision

Retain the direct interval Gram plus Weyl/subdivision method as an
experimental mathematically stronger replacement proposal. Continue to fail
closed. The next implementation cycle must use a validated threshold-relative
Hermitian inertia or equivalent eigencluster enclosure that can prove the
number of eigenvalues above `tau` without isolating every clustered
eigenvalue. Do not increase precision or alter thresholds post hoc in the
completed cycle.

### Evidence

- EVID-0021
- EVID-0022

### Consequences

No threshold is approved, no optimizer rollback is activated, and lifecycle
status remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Alternatives rejected

Treating finite nodes as proof, accepting approximate eigenvalues, silently
raising the maximum precision after inspecting outcomes, or regularizing the
security functional.

### Supersedes / Superseded by

Refines DEC-0012 by supplying validated Gram arithmetic while preserving its
fail-closed outcome. Superseded by DEC-0015 after shifted inertia resolved the
endpoint blocker but direct interval certification still failed 0/12.

## DEC-0015 - Accept point inertia evidence; reject direct interval V1 as a certification path

Date: 2026-08-31

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION, NOT THRESHOLD APPROVAL

### Context

Validated block-LDL* resolves every realized endpoint at 160 bits, but the
direct interval Frobenius guard-band cycle resolves no realized segment after
299 nodes and 12302.94 seconds. Adversarial review also found missing automatic
bundle/environment hash enforcement and an overbroad dormant crossing branch
in the frozen V1 segment producer.

### Decision

Retain the point-inertia implementation and endpoint artifact as valid
experimental evidence. Preserve the V1 whole-segment artifact as a fail-closed
0/12 result, but do not allow V1 to produce an acceptable pass. Candidate
`1e-13` remains proposed/unapproved and configured `1e-12` remains
invalid/unapproved.

The next cycle must use a new, prospectively hash-bound producer that enforces
all frozen inputs and runtime acceptance, proves path domain/continuity before
any intermediate-value crossing claim, and replaces the dependency-inflated
full-matrix Frobenius guard with a sharper validated fixed-basis
congruence/cluster, affine/Taylor, or Schur-complement enclosure.

### Consequences

No threshold, optimizer integration, optimized-MB selection, baseline
selection, publication training, or final-test access is authorized. Claims
remain limited to validated point support on the finite frozen fixtures.

### Alternatives rejected

Approving from equal endpoint inertia, treating interval zero inclusion as a
crossing, increasing precision after outcome inspection, accepting V1 despite
provenance gaps, or changing the physical/security functional.

### Supersedes / Superseded by

Supersedes DEC-0014 as the active numerical next-action policy. Not
superseded.

## DEC-0016 - Accept the exact-tau oracle; reject V2 whole-segment feasibility

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION, NOT THRESHOLD APPROVAL

### Context

The V2.2 exact-dyadic oracle independently certified the four expected support
counts and nearest gaps. The prospectively selected V2.3 Taylor/eigencluster
feasibility subset then certified 0/4 segments, produced four resource-limit
rows, and exceeded one nominal hard deadline. The implementation lacks bounded
Windows process-tree/pipe cleanup, but the realized overrun's exact cause was
not independently traced. Durable nodes also exhausted the cluster cap and
failed far-block inertia.

### Decision

Accept EVID-0026 as validated point support/gap evidence. Preserve EVID-0027
as unsuccessful whole-segment evidence and stop before the all-12 cycle. Do
not approve candidate `1e-13`, reactivate historical `1e-12`, or authorize any
downstream baseline/training/test action.

Any next segment attempt must be a newly frozen V3. It must use a tested
Windows process-tree/Job-Object timeout, durably checkpoint path-domain results
before spectral work, retain scalar Taylor coefficient dependence through the
fixed congruence instead of collapsing immediately to entrywise balls, and
test sequential positive/negative far-block elimination or an independently
proved tighter equivalent as a tightening strategy.

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. V2 is not permitted
to run all 12 paths because its prospectively frozen feasibility gate failed.
The exact-tau oracle resolves the former independent-support-count blocker but
does not establish whole-path fixed inertia or optimizer admissibility.

### Alternatives rejected

Increasing the V2 wall-clock limit after observing timeouts, raising its
cluster cap, loosening the threshold, treating checkpoint control flow as a
persistent path-domain certificate, accepting a late worker result, or using
zero-containing intervals as crossings.

### Supersedes / Superseded by

Supersedes DEC-0015 as the active numerical next-action policy. Not
superseded.

## DEC-0017 - Stop incremental hard-support whole-segment certification

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED ENGINEERING DECISION; METHOD IMPRACTICALITY PROPOSED

### Context

V3 prospectively implemented every declared architectural tightening:
Windows Job Objects, early path-domain persistence, complete hash-chained node
and Schur journals, exact C4 sectors, coefficient-level Taylor congruence, and
deterministic sequential sign-homogeneous Schur elimination. The paired
dependency radius improved by about 38--43x, and realized Schur reductions
executed, but the frozen four-row gate still produced 0/4 complete segments,
four resource limits, 52--53 unresolved far modes on completed roots, and two
large watchdog return-bound breaches.

### Decision

Preserve EVID-0028 as the decisive failed V3 cycle. Do not rerun or retune V3,
do not execute all 12, and do not automatically create V4. Record
`HARD_SUPPORT_WHOLE_SEGMENT_CERTIFICATION_NOT_PRACTICAL_UNDER_CURRENT_METHOD`
as a proposed engineering conclusion pending independent numerical/security-
method review.

The review must decide whether to change numerical regularization
architecture, derive a mathematically equivalent smoother formulation,
change optimization admissibility strategy, or narrow the paper claim. It may
not silently regularize the security functional or approve a threshold.

### Evidence

- EVID-0028
- V3 result SHA-256
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`
- V3 manifest SHA-256
  `5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. Candidate `1e-13`
remains proposed/unapproved, `1e-12` remains invalid/unapproved, and no
baseline selection, optimized-MB grid, training, final-test access, or
publication claim is authorized.

### Alternatives rejected

Post-outcome increases to precision, runtime, Taylor order, cluster size,
block schedule, or subdivision; rerunning a favorable subset; treating Schur
activity or a smaller radius as a complete path proof; and proceeding to all
12 despite the failed gate.

### Supersedes / Superseded by

Supersedes DEC-0016 as the active numerical next-action policy. Not
superseded.

## DEC-0018 - Authorize pointwise-guard protocol design only

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0019; ACTIVE METHOD REVIEW
EVIDENCE

### Context

The V3 hard-support whole-segment feasibility cycle failed closed, while exact
point-inertia/gap evidence and fixed-support local-gradient diagnostics remain
available on finite rosters. The provenance audit found only CRLF/LF byte
normalization mismatches; no scientific payload changed.

### Decision

Authorize the next task to design a prospective pointwise admissibility guard
and transactional rollback protocol. Do not implement it in this cycle, do
not approve any support threshold, and do not perform realized optimization or
evaluation. The guard must validate the current point, use locally valid
fixed-support gradients, validate the proposed endpoint, and commit or restore
the complete mutable training state. It must not certify intermediate points
or alter the security functional.

### Method review conclusion

Whole-segment support invariance is not required for validity of the adopted
statewise security calculation at a validated realized point; it was an
additional numerical condition for claiming smooth optimization through a hard
support operation. A transition at an unobserved interpolation point affects
optimization smoothness and admissibility, not the already computed pointwise
value, provided the pointwise evaluator and numerical rule are themselves
validated. Current evidence supports this only on the finite exact-tau,
endpoint, stress-oracle, and local-gradient rosters.

The pointwise rule changes only the numerical optimization domain. Physical
modulation, MI, Holevo, and reported SKR equations remain unchanged. Claims of
global differentiability, continuous-domain support stability, and
whole-trajectory certification remain prohibited. `attack_class=None` limits
manuscript security wording but does not by itself block numerical design;
the separate threshold/support blocker still prevents execution.

### Evidence

- EVID-0029
- EVID-0026, EVID-0027, EVID-0028
- `docs/SECURITY_SCOPE_FREEZE.md`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`

### Consequences

`NEXT_ACTIONS.md` now names pointwise-guard protocol design as the sole next
permitted action. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; candidate `1e-13` remains proposed
and `1e-12` remains invalid.

### Alternatives ranked

1. `POINTWISE_GUARD` - best supported by finite point-inertia and local-gradient
   evidence, and it preserves the frozen security functional.
2. `NARROW_PAPER_CLAIM` - scientifically safe fallback but does not address
   optimization usability.
3. `NUMERICAL_REGULARIZATION_REDESIGN` - potentially useful, but its security
   semantics are not yet documented.
4. `SMOOTHER_EQUIVALENT_FORMULATION_REVIEW` - no mathematically equivalent
   implementation or proof is currently available.

## DEC-0019 - Freeze pointwise guard protocol design

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0020; ACTIVE DESIGN CONTRACT

### Decision

Freeze `pointwise-guard-protocol-v1` as a proposed, threshold-parametric design
for the next implementation task. The smallest certification unit is one
unique realized statewise physical ensemble, not an individual Monte Carlo
noise sample. The design reuses validated shifted-Hermitian block-LDL*
inertia and nearest-eigenvalue brackets. It accepts only if

`certified_margin > 2 * uncertainty_upper`,

where the margin is the minimum certified distance from `tau` to the nearest
bracketed eigenvalue on either side and `uncertainty_upper` is the maximum
validated bracket half-width. The factor two is a fixed two-sided enclosure
allowance, not an outcome-tuned constant.

Only `POINTWISE_ADMISSIBLE` permits a local fixed-support gradient. Guard-band,
certification, and provenance failures are no-ops. The transaction snapshots
all mutable model, optimizer, dual-controller, module-mode, RNG, explicit
generator, and counter state. Schedulers and GradScaler are absent in the
current repository and become mandatory fields if introduced before
implementation. No interpolation segment is certified.

### Evidence

- EVID-0030
- `configs/pointwise_guard_protocol_v1.yaml`
- `docs/POINTWISE_GUARD_PROTOCOL.md`
- `tests/test_pointwise_guard_protocol_design.py`

### Consequences

The next permitted task is implementation of this exact protocol. The protocol
remains `PROPOSED`; the candidate threshold remains `PROPOSED_UNAPPROVED`;
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0020 - Accept pointwise implementation and authorize smoke test

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED IMPLEMENTATION DECISION; SMOKE ONLY

### Decision

Accept the pointwise guard implementation against the frozen protocol for the
scoped implementation matrix. The runtime now performs pre-update point
checks, rejects before backward, validates the post-update endpoint, defers
the energy-dual update until commit, and restores complete transaction state
on rejection. The validated point-certifier and provenance bindings remain
injected; no raw complex128 fallback exists.

Authorize the separately frozen six-step certification-only smoke test as the
next task. Do not run it in the implementation task, approve `1e-13`, reactivate
`1e-12`, or perform publication training, baseline selection, or test access.

### Evidence

- EVID-0031
- `results/pointwise_guard_implementation_v1.json`
- `tests/test_pointwise_guard.py`

### Consequences

`NEXT_ACTIONS.md` now names `POINTWISE_GUARD_SMOKE_TEST_AUTHORIZED` as the sole
next action. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0021 - Stop pointwise smoke on missing validated backend

Date: 2026-09-01

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; ENVIRONMENT BLOCKED

### Decision

Do not execute the frozen pointwise smoke when the required validated
Arb/python-flint backend is unavailable and no repository-backed point
certifier exists. The injected certifier used by unit tests and raw
complex128 eigenspectra are not acceptable substitutes. Record the blocked
attempt with zero updates and preserve the smoke protocol unchanged.

### Evidence

- EVID-0032
- `results/pointwise_guard_smoke_v1.json`
- `configs/pointwise_guard_protocol_v1.yaml`

### Consequences

The usability decision is `SMOKE_TEST_BLOCKED_BY_ENVIRONMENT`, not
`OPTIMIZATION_USABLE` or `OPTIMIZATION_EFFECTIVELY_FROZEN`. The exact next
action is to restore the hash-pinned certification environment and provide a
validated repository-backed point-certifier adapter, then rerun the same
frozen six-step smoke test without retuning.

## DEC-0022 - Accept restored certification environment

Date: 2026-09-01

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0023; ACTIVE ENVIRONMENT EVIDENCE

### Decision

Accept EVID-0034 as a current verified pass for the exact certification
environment. CPython 3.12.10, python-flint 0.9.0, FLINT 3.6.0, PyYAML 6.0.3,
NumPy 2.5.2, Windows x86-64, and the lock hash match the frozen requirements.
The real Arb/acb and shifted-inertia preflight suite passes 32/32.

At the time of this decision, the next task was adapter implementation; that
adapter and the smoke runner are now frozen by DEC-0023.
Do not run the smoke test in this environment-only task, approve a threshold,
or change any scientific/security functional.

### Evidence

- EVID-0034
- `results/certification_environment_restore_v2.json`

### Consequences

`NEXT_ACTIONS.md` now names adapter implementation as the sole next action.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0023 - Freeze real adapter and authorize smoke execution

Date: 2026-09-02

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0024; ACTIVE V1 PROVENANCE

### Decision

Accept EVID-0035 and EVID-0036. The real adapter uses the restored pinned
Arb/FLINT environment through canonical JSON and preserves the final physical
ensemble exactly. The no-override runner and prospective execution manifest
are frozen before smoke outcomes. Authorize the exact six-step, three-state,
two-repetition smoke test as the next task.

Do not change the threshold, guard inequality, seeds, state roster, precision,
optimizer settings, or security functional. Do not run publication training,
baseline selection, optimized-MB search, or final-test evaluation.

### Evidence

- EVID-0035
- EVID-0036
- `configs/pointwise_guard_execution_manifest_v1.json`

### Consequences

`NEXT_ACTIONS.md` now names `FROZEN_POINTWISE_SMOKE_EXECUTION_AUTHORIZED` as
the sole next permitted action. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0027 - Retain threshold blocker and authorize minimum prospective validation

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION; THRESHOLD UNAPPROVED

### Decision

Accept EVID-0041. Record `OPTIMIZATION_USABLE` as a pointwise optimizer result,
but do not approve `1e-13`. The dense-Fock cutoff label is stale for the active
cutoff-independent C4-Gram backend, while the failed Fock stress suffix remains
historical diagnostic evidence. The active threshold/support blocker is genuine:
formal support identity is false and the candidate comparison is
outcome-informed. Baseline selection remains a downstream numerical blocker.

Authorize only the minimum prospective finite threshold validation described by
EVID-0041. It must be frozen before outcomes, use independent full-support
arbitrary-precision Gram oracles for every declared ill-conditioned production
fixture, and compare all frozen observables under existing tolerances. Do not
rerun either smoke, change tau or security claims, or perform any publication
experiment.

### Consequences

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The exact next action
is to freeze and execute the prospective threshold/numerical validation gate;
explicit author threshold approval and completion of the existing numerical
prerequisites are required before publication-scale experiments.

### Evidence

- EVID-0041
- `results/threshold_numerical_gate_review_v1.json`
- `configs/default.yaml`
- `docs/FINAL_MODEL_SPEC.md`, Section 11

## DEC-0028 - Freeze minimum prospective threshold validation execution

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; THRESHOLD UNAPPROVED

### Decision

Freeze the 12 production fixtures whose declared `1e-14`/`1e-13` support masks
differ, with their roster hashes in `configs/threshold_validation_v1.yaml`.
For each, independently resolve full mathematical support with the existing
arbitrary-precision C4-Gram oracle at 600 and 800 decimal digits; accept only
two converged 256-mode rows and production `tau=1e-13` agreement for
support/rank diagnostics, `C,w,Z`, all three symplectic eigenvalues, `chi_BE`,
and raw `K` under the already frozen tolerances. The oracle never applies tau.

Authorize only the manifest-bound runner. A pass is pending explicit author
approval and does not itself change threshold status or publication lifecycle.

## DEC-0029 - Correct threshold-validation fixture provenance wiring

Date: 2026-09-02

Status: ACTIVE HARNESS CORRECTION; VALIDATION NOT RERUN

The attempted validation stopped before threshold evaluation. Its production
fixture reconstruction deterministically matched the frozen
`untrained_full_initialization` hash, but the reusable oracle harness compared
it to the different independent-confirmation roster hash. Bind the harness to
the already frozen production fixture hashes. The Torch-bearing production
Python runtime is required; the Arb-only environment has no Torch. No
scientific fixture, tau, tolerance, or expected production hash changed.

## DEC-0030 - Freeze support-free full-support C4-Gram implementation

Date: 2026-09-03

Status: ACTIVE IMPLEMENTATION DECISION; NO SCIENTIFIC CHANGE

Accept EVID-0044. Authorize implementation of the frozen full-support C4
sector source-moment backend only. It preserves the existing security chain
and all 12 fixtures, replaces threshold support with mathematical full support,
uses a residual-norm `w`, and sends insufficiently conditioned complex128
states to a fixed arbitrary-precision evaluation fallback. No gradient through
the fallback, training, threshold approval, or publication experiment is
authorized.

## DEC-0031 - Authorize frozen full-support evaluation validation

Date: 2026-09-03

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; VALIDATION ONLY

Accept EVID-0045. The evaluation-only full-support backend implementation and
hash-bound 12-fixture validation manifest are complete. Authorize exactly one
manifest-bound evaluation validation. Do not train, select baselines, access
final-test data, or authorize fallback gradients. A validation pass does not
approve a threshold or publication-scale experiments.

## DEC-0032 - Freeze independent gradient/VJP validation protocol

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; PROTOCOL NOT EXECUTED

Accept EVID-0046. Authorize only implementation of the future analytic
fast-path VJP and its no-override validation runner. The arbitrary-precision
fallback remains evaluation-only; any fallback route fails gradient validation
closed. A later execution requires a separate frozen execution manifest. No
training, threshold approval, baseline selection, optimized-MB search, or
final-test access is authorized.

## DEC-0033 - Freeze cluster-safe spectral Fréchet amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; AMENDMENT NOT EXECUTED

Accept EVID-0047. Supersede EVID-0030 only for the spectral-gradient rule:
the fast-path inverse-square-root derivative is the basis-invariant Loewner
Fréchet operator, with its Hermitian real-inner-product VJP. Do not use
individual-eigenvector backward or add an eigengap criterion. Authorize only
implementation of this custom fast-path VJP and a hash-bound runner; do not
execute gradient validation, differentiate fallback, or train.

## DEC-0034 - Freeze analytic VJP implementation and authorize validation

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; CERTIFICATION NOT EXECUTED

Accept EVID-0048. Authorize exactly one later execution of the hash-bound
gradient/VJP validation runner. EVID-0031 defines repeated-eigenvalue behavior;
AP fallback remains evaluation-only. This does not establish gradient
correctness, approve a threshold, authorize training, or permit final-test or
selection access.

## DEC-0035 - Freeze fast-route gradient/VJP feasibility amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; SYNTHETIC VALIDATION NOT EXECUTED

Accept EVID-0049. The frozen Full center cannot enter `COMPLEX128_FAST` because
its full-support modes are below binary64 resolution; it remains AP-only and
gradient-ineligible. This amendment supersedes EVID-0032 only for that center's
fast-route feasibility. Authorize implementation and freeze of a separate
synthetic fast-route harness with no training claim. Do not execute it yet,
relax gates, or differentiate fallback.

## DEC-0036 - Freeze synthetic fast-route VJP harness and authorize execution

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; SYNTHETIC ONLY

Accept EVID-0050. Authorize exactly one execution of the hash-bound synthetic
fast-route VJP preflight. A result applies only to the algebraic fast-domain
fixture; it cannot authorize Full-center training, AP differentiation,
publication training, threshold approval, selection, or final-test access.

## DEC-0037 - Repair synthetic fast-route VJP harness and reauthorize v2

Date: 2026-09-04

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; V2 NOT EXECUTED

Accept EVID-0051. Preserve the v1 failed execution as a harness failure. The
v2 runner reads the frozen tolerance field names exactly and has distinct
runtime-attempt provenance. Authorize exactly one later v2 synthetic preflight
execution. No Full-center gradient claim, training, fallback differentiation,
threshold approval, selection, or final-test access is authorized.

## DEC-0038 - Freeze manifold-consistent C/w VJP amendment

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; AMENDMENT NOT EXECUTED

Accept EVID-0052. The prior v2 failure arose from an independent-sector path
outside the production C4 manifold, not from a fast-gate defect. Preserve both
failed synthetic artifacts. Authorize only implementation and freeze of a
manifold-consistent synthetic VJP harness using Fixture B. Do not execute it,
relax gates, or claim Full-center training eligibility.

## DEC-0039 - Freeze manifold-consistent synthetic VJP harness

Date: 2026-09-04

Status: ACTIVE IMPLEMENTATION DECISION; HARNESS NOT EXECUTED

Accept EVID-0053. The separate runner preserves the spectral-only and
manifold-consistent paths and binds their inputs before future execution. Do
not execute it until a separate lifecycle review authorizes the command. It
cannot establish Full-center training eligibility or publication readiness.

## DEC-0024 - Preserve V1 outcome and freeze prospective pointwise guard V2

Date: 2026-09-02

Status: SUPERSEDED AS NEXT-ACTION POLICY BY DEC-0025; ACTIVE V2 METHOD

### Decision

Accept EVID-0037 as the completed V1 smoke outcome
`OPTIMIZATION_EFFECTIVELY_FROZEN`. Preserve the V1 protocol, blocked artifact,
completed artifact, states, seeds, optimizer, precision, `tau`, and all smoke
settings without rerun or retuning.

Accept EVID-0038 and freeze `pointwise-guard-v2` as a proposed, inactive
replacement. V2 admits a realized point exactly when support is rigorously
certified and the rigorous spectral-distance lower bound is strictly positive.
The reported interval half-width is diagnostic and is not charged again.
No positive engineering margin is adopted because pre-existing independent
evidence supplies none.

Authorize implementation and scoped verification of the repository-backed V2
point-certifier adapter and frozen V2 smoke runner only. The implementation
must not use midpoint order as proof, nearest-round Arb endpoints before the
decision, alter the scientific/security functional, or execute the smoke.

### Evidence

- EVID-0037
- EVID-0038
- `results/pointwise_guard_v2_methodology_review.json`
- `configs/pointwise_guard_protocol_v2.yaml`
- `docs/POINTWISE_GUARD_PROTOCOL_V2.md`

### Consequences

The exact next action is to implement the repository-backed validated V2
point-certifier adapter and frozen V2 smoke runner. Candidate `1e-13` remains
`PROPOSED_UNAPPROVED`; historical `1e-12` remains `INVALID_UNAPPROVED`.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. V2 smoke execution,
publication training, baseline selection, optimized-MB search, and final-test
access remain unauthorized.

## DEC-0025 - Authorize frozen V2 smoke execution

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED EXECUTION DECISION; V2 SMOKE ONLY

### Decision

Accept EVID-0039. The V2 implementation is complete for its scoped matrix and
the V2 execution manifest is frozen after passing production and real Arb/FLINT
tests. Authorize exactly the manifest-bound V2 smoke runner as the next task.

Do not rerun or modify V1 evidence, change `tau`, threshold status, states,
seeds, optimizer, precision, MI, Holevo, SKR, security scope, or the frozen
model. Do not perform publication training, baseline selection, optimized-MB
search, or final-test access. At this pre-execution decision point, no V2
smoke outcome existed; the later result is recorded by EVID-0040.

### Evidence

- EVID-0039
- `configs/pointwise_guard_execution_manifest_v2.json`
- `results/pointwise_guard_implementation_v2.json`

### Consequences

The exact next permitted action is to run the frozen V2 smoke execution. The
V2 protocol remains proposed with candidate `1e-13` unapproved and historical
`1e-12` invalid/unapproved. Lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0026 - Accept V2 smoke usability and retain publication gate

Date: 2026-09-02

Status: ACTIVE FAIL-CLOSED LIFECYCLE DECISION; OPTIMIZATION USABLE

### Decision

Accept EVID-0040. The frozen V2 smoke satisfies the preregistered
`OPTIMIZATION_USABLE` rule: at least one committed update, zero
rollback-equivalence failures, zero provenance failures, and byte-identical
repeated traces. All pre/post point checks were admissible and all recorded
gradients were finite.

Preserve the completed V1 negative evidence and do not rerun either smoke.
This usability result changes no threshold, physical/security functional,
frozen model, or publication lifecycle authorization.

### Consequences

The project remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The still-required
gate before publication-scale experiments is explicit approval of the
candidate numerical threshold/support policy, followed by completion of the
existing frozen numerical prerequisites currently marked
`BLOCKED_FOCK_DEPENDENCY` and `BLOCKED_NUMERICAL_DEPENDENCY` for pseudoinverse,
Fock-cutoff, and baseline-selection state. No baseline selection, training,
optimized-MB search, or final-test access is authorized by this decision.

The exact next permitted action is to resolve that threshold/numerical approval
gate under a separately authorized lifecycle task.

### Evidence

- EVID-0040
- `configs/default.yaml`
- `docs/FINAL_MODEL_SPEC.md`, Section 11
