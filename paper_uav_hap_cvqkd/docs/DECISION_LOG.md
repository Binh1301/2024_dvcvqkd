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
## DEC-0040 - Documentation-only current model/code alignment

Date: 2026-09-10

Status: ACTIVE DOCUMENTATION DECISION; SCIENTIFIC IMPLEMENTATION BLOCKED

### Decision

Update the existing authoritative Markdown documents to distinguish the current
intended model from the current source implementation. Record the pre-action
state, post-action phase-noise chain, target physical fading factors, full
correlation interval, and the exact current code mismatches. Do not resolve
those mismatches by changing source, tests, parameters, or numerical evidence.

### Evidence

- EVID-0054
- docs/PAPER_CODE_ALIGNMENT.md
- docs/KNOWN_ISSUES.md
- docs/PROJECT_STATE.md

### Consequences

The lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Deterministic
constellation/PMF/orbit diagnostics remain permissible as non-publication
preliminary work. Target phase/channel/security/SKR figures remain blocked until
the listed implementation and numerical gates are separately authorized and
verified.

## DEC-0041 - Implement full physically admissible Z-interval Holevo maximum

Date: 2026-09-10

Status: ACTIVE IMPLEMENTATION DECISION; NUMERICAL CERTIFICATION BLOCKED

### Decision

Implement the frozen `Z_minus`, `Z_plus`, `Z_phys`, `Z_L`, and `Z_U` equations
in the active Holevo path. For every valid interval, evaluate the existing
covariance/entropy functional over a deterministic closed-interval candidate
grid and bounded refinement of every grid cell, including both boundaries;
select the maximum without assuming monotonicity. For an empty interval or
candidate physicality failure, fail closed with structured diagnostics.

### Evidence

- EVID-0056
- `src/cvqkd/holevo.py`
- `tests/test_holevo_interval.py`
- `docs/EQUATIONS.md`
- `docs/PAPER_CODE_ALIGNMENT.md`

### Consequences

`HolevoResult.z` now denotes the selected `Z_star`, and its diagnostics expose
the interval endpoints, physical bound, width, selected value, maximizing
location, and security-domain validity. The selected covariance uses Z directly.
The phase/post-action epsilon chain, policy features, source-moment backend,
and raw-SKR ordering are unchanged. The value function is only piecewise
differentiable because candidate/interval argmax changes are nonsmooth.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; existing numerical
artifacts do not certify the new target functional.

## DEC-0043 - Align the active composite channel before numerical work

Date: 2026-09-10

Status: ACTIVE IMPLEMENTATION DECISION; SCIENTIFIC MAPPINGS BLOCKED

### Decision

Use one common altitude-dependent C_n^2(h) turbulence provenance for
scintillation, effective phase, and optional AoA. Remove the legacy
constant-C_n^2 beam-wander term from the active target sampler while retaining
the equation only as a marked legacy helper. Implement the source-supported
Rician pointing, normalized lognormal scintillation, hard AoA gate, raw-T
diagnostics, and truncated physical-domain admission. Do not invent the
profile-to-phase, aperture-averaging, or turbulence-to-AoA mappings; unresolved
production choices remain explicit and fail closed.

### Evidence

- EVID-0058
- src/channel/fso_channel.py
- src/channel/scintillation.py
- src/channel/aoa.py
- tests/test_composite_channel.py
- tests/test_channel_provenance.py
- tests/test_holevo_resolution.py

### Consequences

The policy remains on (T, epsilon_base), and one post-action epsilon_total
continues to feed both MI and Holevo. Production configuration remains
blocked by unresolved profile/aperture/AoA/phase choices. Full-Z numerical
resolution is tested at 17/33/65/129 candidates but is not certified.
Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0047 - Reuse stable AP source moments for exploratory B-D subsets

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Reuse the 900-digit-stable \(C,w\) only because the exact ensemble hash is
identical across Cases A-D. Evaluate B-D on 16 active states each through the
existing full-Z path. Keep the reuse evaluation-only; do not route it into
training, certification, or publication workflows.

### Evidence

- EVID-0062
- EVID-0063
- results/exploratory_cases_BD_full_security_20260910.json

### Consequences

Cases B-D obtain bounded exploratory MI/Holevo/raw-K values. Case D retains
outage rows at K=0 and satisfies the active-fraction identity. No lifecycle
gate, physical parameter, Gram gate, or security equation was changed.

## DEC-0042 - Retain unresolved Cn_phi2 and bind canonical provenance

Date: 2026-09-10

Status: ACTIVE CONFIGURATION DECISION; AUTHOR FREEZE BLOCKED

### Decision

Retain `channel.cn_phi2_m_minus_two_thirds: null` in production
configuration. Treat `Cn_phi2` as an explicitly prescribed, scenario-level
effective representation of the same physical turbulence in `m^(-2/3)`,
separate from the legacy `cn2_m_minus_two_thirds` compatibility field and
without an evidenced mapping from an altitude-dependent `C_n^2(h)` profile.
Derive `tau_phi2` and `c_phi` from `Cn_phi2`, SI wavelength, and the resolved
link distance; do not expose an independent `c_phi` configuration value.
Persist the canonical phase provenance record in active run/checkpoint
metadata and retain existing resolved-config hash binding.

### Evidence

- EVID-0057
- `src/channel/phase_noise.py`
- `scripts/_train.py`
- `configs/default.yaml`
- `docs/PHYSICAL_PARAMETER_AUDIT.md`

### Consequences

The explicit zero and nonzero values in focused tests remain test-only, and
the separate configured/current `cn2` value is not a phase substitute. Target
entry points continue to fail closed while the author value is null. The
policy input remains `(T, epsilon_base)`, the same post-action
`epsilon_total` remains the MI/Holevo input, and the full-Z Holevo interval is
unchanged. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; no
training, target evaluation, certification, or numerical approval is granted.
## DEC-0044 - Run only non-publication exploratory composite cases

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Permit Cases A--D with explicit development-only scintillation, pointing, and
AoA values, \(N=1000\) channel samples per case, and explicit zero phase. Keep
all unresolved mappings labeled exploratory. Do not invoke training, baseline
selection, final-test, certification, or the arbitrary-precision Holevo
fallback.

Accept the outage-aware active-only SKR plumbing and relative transmittance
diagnostic fix as the minimum code change required for the case harness.

### Evidence

- EVID-0059
- EVID-0060
- results/exploratory_cases_20260910.json

### Consequences

Channel and MI preflight behavior may be reported as exploratory only. Holevo,
active-K, and outage-weighted-K remain unreported because the complex128 fast
gate fails and the fallback is evaluation-only. Lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0046 - Accept one bounded AP-backed Case A security result

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the one-state Case A AP-backed source-moment/full-Z result as
EXPLORATORY_EVALUATION_ONLY. Preserve the complex128 fast gate, keep AP
evaluation-only, and do not generalize the result to Cases B-D, learned
training, certification, or publication.

### Evidence

- EVID-0062
- results/exploratory_case_A_full_security_20260910.json
- src/cvqkd/gram_moments.py
- scripts/full_support_c4_worker.py

### Consequences

Case A has a finite exploratory \(C,w,Z_\star,\chi_{BE}^{ub},K\) result.
The numerical artifact remains bounded to one exact ensemble and a single
evaluation-only AP route. Lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0045 - Preserve the Gram fast gate after numerical root-cause audit

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify the exploratory uniform-ensemble failure as
FLOATING_POINT_ROUNDOFF plus NUMERICAL_ILL_CONDITIONING, not probability
support loss, constellation collapse, or an implementation-indexing bug.
Preserve the complex128 gate, do not add clipping/jitter/support truncation, and
do not enable the arbitrary-precision fallback for training. Keep the fallback
evaluation-only and require a separate bounded one-state security run before
claiming exploratory Holevo/K completion.

### Evidence

- EVID-0061
- results/exploratory_cases_20260910.json
- src/cvqkd/gram_moments.py
- scripts/full_support_c4_worker.py

### Consequences

No numerical tolerance or security formula changed. The current exploratory
cases have finite MI/channel metrics but incomplete Holevo/K metrics. Lifecycle
remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## DEC-0048 - Classify complex128 differentiable path as blocked

Date: 2026-09-10

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify the current differentiable complex128 full-support source-moment path
as EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128 for the investigated exact
256-state ensemble. Preserve the gate and AP evaluation-only boundary. Do not
implement clipping, jitter, support reduction, tolerance weakening, or an
unproven reformulation.

### Evidence

- EVID-0064
- src/cvqkd/gram_moments.py
- src/cvqkd/spectral_frechet.py
- tests/test_holevo_interval.py
- tests/test_gradients.py

### Consequences

The AP-backed forward evaluator is exploratory only. Adaptive training remains
unauthorized and the next work is a separately scoped differentiable numerical
design investigation.

## DEC-0049 - Stop AP custom-backward validation at the fallback definition mismatch

Date: 2026-09-10

Status: SUPERSEDED BY DEC-0050; HISTORICAL FAIL-CLOSED NUMERICAL DECISION

### Decision

Classify this feasibility run as `AP_CUSTOM_BACKWARD_NOT_VALIDATED`. Preserve
the isolated AP implicit-adjoint prototype and the complex128 production gate,
but do not integrate the prototype into `gram_moments.py`, `holevo.py`, or
`trainer.py`. Do not repair or regenerate the existing AP/security artifacts in
this task.

The stop condition is a newly verified forward-definition mismatch: the AP
worker's `aa=sr*x2.T` does not implement the current C4 reference
(G_sD G_{s-1}^{-1}=x2.T), so its stored (w) cannot be used as the forward
target for custom-backward validation. The small-fixture adjoint test is not
enough to authorize a 256-state gradient claim.

### Evidence

- EVID-0065
- `results/ap_custom_backward_case_A_20260910.json`, SHA-256
  `dc11c998f755d328906558b949444e4bf45a088657938f7b4b1c1a13daaf58d4`
- `src/cvqkd/ap_custom_backward.py`
- `tests/test_ap_custom_backward.py`
- `src/cvqkd/gram_moments.py`, `tests/test_full_support_c4_gram_backend.py`
- `scripts/full_support_c4_worker.py`

### Consequences

The prototype remains experimental and evaluation-only. No Case A AP
directional finite-difference suite, torch PS/GS/V_A chain, full-Z backward,
optimizer step, training, certification, final-test access, or publication-scale
evaluation is authorized. Existing worker-backed C/w/security artifacts remain
historical pending one separately scoped AP fallback correction and artifact
rebind. Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive
training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

## DEC-0050 - Accept corrected AP worker and bounded Case A rebind

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the one-line AP worker correction `aa=x2.T` as matching the frozen
production C4 (A_s=G_sDG_{s-1}^{-1}) definition. Accept the corrected 800/900
digit Case A source moments and the bounded corrected full-Z result as current
exploratory evidence only. Mark all old worker-backed (w)-dependent artifacts
`SUPERSEDED_WRONG_AP_W`; retain their old numbers for provenance.

Do not recompute Cases B-D in this task. Keep the custom backward isolated with
status `PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION`.

### Evidence

- EVID-0066
- `results/ap_worker_corrected_case_A_20260911.json`, SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`
- `results/exploratory_case_A_full_security_corrected_20260911.json`, SHA-256
  `a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa`
- `tests/test_ap_worker_equivalence.py`

### Consequences

Corrected Case A has (w=0.018327610474963502...),
([Z_L,Z_U]=[0.2914192733053753,0.2934784546975139]),
(chi_{BE}^{ub}=0.01518919002933572), and raw
(K=0.004757635492383283). These remain bounded exploratory values; no
publication, certification, training, final-test, or B-D authorization follows.
Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## DEC-0051 - Accept corrected bounded B-D security rebind as exploratory evidence

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED EXPLORATORY DECISION

### Decision

Accept the newly generated B-D artifact as a corrected, bounded,
evaluation-only source-moment/full-Z exploratory rebind. It uses the accepted
corrected AP `(C,w)`, the exact uniform 256-state ensemble hash, direct seeded
physical channel samples, active-only statewise MI/Holevo evaluation, and raw
signed SKR with no clipping. Case D outage rows remain outside MI/Holevo and
have exact `K=0`.

Because the historical ignored B-D artifact and its exact index roster were
unavailable in this checkout, the new artifact uses and records the declared
`evenly_spaced_active_rows_v1` reconstruction rule. Its values must not be
described as a publication-scale or exact historical-subset result.

### Evidence

- EVID-0067
- `results/exploratory_cases_BD_full_security_corrected_20260911.json`,
  SHA-256 `c7c88940e5219a191277f358318eb756dcdeea61d6a6e546d0286af42a3c2ba0`
- `scripts/recompute_corrected_bd_security.py`
- Corrected worker SHA-256
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`

### Consequences

The corrected A-D exploratory table is now complete for the bounded
development subset. B, C, and D have negative mean raw K under corrected w;
those signed values are retained and are not clamped. The lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, adaptive training remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`, and the remaining blocker is corrected AP
custom-backward directional validation. Do not run that validation as part of
this rebind.

## DEC-0052 - Stop corrected AP custom-backward validation after bounded PS failure

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept the cheap independent four-state checks and the four physical-mapping
structure checks as exploratory diagnostics only. Do not accept a 256-state
custom-backward gradient claim. Stop the target suite after one bounded PS
direction: the corrected AP reference resolved all 256 modes, but the custom
combined VJP differed materially (`3.3995565604790261e+102` versus
`0.0017741810692945003680`). Do not launch GS-real, GS-imag, V_A, or full-Z
backward jobs.

Classify the validation as `AP_CUSTOM_BACKWARD_NOT_VALIDATED` and retain the
custom path isolated from production. The measured custom reverse runtime was
`25653.3898618 s`, so ordinary adaptive training remains closed independently
of the correctness failure.

### Evidence

- EVID-0068
- `results/ap_custom_backward_corrected_directional_validation_20260911.json`,
  SHA-256 `60d6da12dc23bb8d4d086fef6ab3a349201c33745d0a930ba37be8b76203bc14`
- `results/ap_custom_backward_ps_target_attempt_20260911.json`,
  SHA-256 `3c8b87793b76abc82e0ecc89a5e33fb9c513dec749cdbbd2e4e2f5b4f3856d2a`
- `scripts/validate_corrected_ap_custom_backward.py`,
  SHA-256 `6fa71c0d1d055627a4fa93af79e12617d166712bd0ed14534319d394190e8db9`
- Target-attempt runner SHA-256
  `3f24854ccf9906a42bde8132f8e6d175ca7a49c928c2caf32027c5914a767244`
- Corrected worker SHA-256
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Corrected AP source-moment artifact SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`

The old custom-backward artifact remains `SUPERSEDED_WRONG_AP_W` and is not
an oracle.

### Consequences

Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`; the single
remaining blocker is a root-cause fix and fresh full-support validation of the
AP reverse path at the `~10^-618` eigenvalue scale. No training, optimizer
step, channel change, security-equation change, final-test access, or
publication-scale evaluation was performed.

## DEC-0053 - Prefer an exact C4 tangent audit before reverse repair

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Treat the full-support differentiable source-moment problem as unresolved at
the target spectrum. Do not patch the custom reverse by changing transpose
conventions based only on the \(10^{102}\) output. The corrected worker's
ordinary transpose is part of its solve orientation; the correct next
diagnostic is an independent arbitrary-precision forward tangent.

The approved research direction is to preserve the exact C4 C/w functional
while evaluating
\(B_sS_{s-1}=S_sD\) and
\(A_sG_{s-1}=G_sD\) by constrained solves, and differentiating those
constraints together with the square-root Sylvester equation. A compiled
multiprecision backend is conditional on passing the tangent and local
adjoint tests.

### Evidence

- EVID-0069
- docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md
- Corrected target result and custom failure in EVID-0068

### Consequences

Keep the AP custom backward isolated and classified
AP_CUSTOM_BACKWARD_NOT_VALIDATED. Do not start GS, \(V_A\), full-Z backward,
adaptive training, or publication-scale evaluation until the source-moment
three-way validation passes and runtime is separately acceptable. The
security equations, full support, corrected C/w, and complex128 gate remain
unchanged.

## DEC-0054 - Accept one bounded C4 forward tangent diagnostic; keep training closed

Date: 2026-09-11

Status: ACTIVE FAIL-CLOSED NUMERICAL DECISION

### Decision

Accept the isolated C4 constrained-solve forward tangent as
`CONSTRAINED_TANGENT_VALIDATED` for the single recovered Case-A PS direction.
The exact full-support C/w functional is unchanged. The tangent may be used
as a diagnostic boundary, but not as a production gradient or adaptive-
training authorization. Keep the old AP custom reverse classified
`AP_CUSTOM_BACKWARD_NOT_VALIDATED` and do not begin reverse repair, GS-real,
GS-imaginary, V_A, full-Z backward, optimizer steps, or training in this task.

The 800-digit target row resolved 256/256 modes and matched the prior corrected
AP reference within 1e-8 for dC, dw, and combined dJ. The 200/400/600 rows
failed closed before full support was resolved. The target constrained-only
row took 1181.1304 seconds, so the exact tangent is not computationally
practical for the proposed adaptive workload. The target explicit R/J
comparison was not completed within the bounded runtime window; cheap-fixture
explicit/constrained identities and residuals passed.

### Evidence

- EVID-0070
- `results/c4_constrained_forward_tangent_20260911.json`, SHA-256
  `023fb41db59a079314f639ff47513890445c7a7b885c17273a5f3df52b71ddcb`
- `src/cvqkd/c4_constrained_tangent.py`, SHA-256
  `a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258`
- `scripts/validate_c4_constrained_tangent.py`, SHA-256
  `de7f5e9c6ec9060c5135092aba89864b46bcd019884f10c34514af86405b6c70`
- `tests/test_c4_constrained_tangent.py`, SHA-256
  `6763a7c82c74929a4e4ba3b06df4376fbf027abc417d3dc69a2a4fe711f59c09`
- Prior corrected PS direction hash:
  `e274073c5038308b521bd1a348c932a4a249cd5fc59a006b7611911e2be6dd87`

### Consequences

Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`, and the project
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. The remaining
numerical blocker is a complete, validated, and computationally practical
full-support source-moment gradient boundary, including the reverse path.
The next permitted task is validation of the remaining source directions or a
separately scoped practical exact-backend investigation; neither authorizes
training or final-test access.
