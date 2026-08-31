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
