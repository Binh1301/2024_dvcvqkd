# Gradient/VJP validation protocol

Status: **frozen before implementation and execution**. This protocol does
not alter the full-support evaluator, the scientific/security model, MI,
Holevo, SKR, `tau`, the optimizer, or the frozen transmitter.

## Scope and precondition

The arbitrary-precision C4 fallback is evaluation-only. It is never an
autograd path, a straight-through estimator, or a training substitute. Every
center, plus, and minus evaluation used by this protocol must report
`COMPLEX128_FAST`; a fallback route, non-finite value, provenance mismatch, or
route change is `GRADIENT_VJP_VALIDATION_FAIL_CLOSED`.

The protocol validates a future analytic VJP of the full-support fast path. It
does not authorize training merely because the evaluation backend passed.

## Frozen probes

Use the deterministic untrained Full transmitter at fixture seed `202613` and
the existing bad/medium/good representative validation states. Reuse one
`N_MC=2048` complex-noise tensor generated with seed `202615` for center,
autograd/VJP, and every `+/-` perturbation. No validation or final-test state
is selected from any observed outcome.

For each PS, GS, and VA coordinate listed in
`configs/gradient_vjp_validation_protocol_v1.yaml`, evaluate central
differences at
`1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6` for `MI,C,w,Z,lambda1,lambda2,lambda3,
chi_BE,raw_K`. A future VJP must supply the matching directional derivative.

For each metric, three adjacent step pairs must be stable and agree with the
VJP under

`1e-7 + 5e-3 * max(abs(d_h), abs(d_next), abs(d_vjp))`.

The metric/family/coordinate passes only if all required statewise rows pass.
No best-window selection, coordinate replacement, or tolerance/step change is
allowed after outcomes are known.

## Required future implementation and evidence

The implementation must provide an analytic Hermitian matrix-function
Frechet/VJP path for the complex128 fast route, a no-gradient fallback status,
canonical route/provenance records, and a no-override runner. The runner must
bind this protocol, EVID-0029, the evaluation-backend manifest, source files,
the frozen model, and the three-state fixture reconstruction before execution.

Its artifact must record center/plus/minus routes, CRN identity, all listed
directional derivatives, adjacent-pair comparisons, exact input hashes, and
every fail-closed reason. It must keep threshold approval, publication
training, final-test access, optimized-MB selection, baseline selection, and
security-functional change false.

## Prohibitions and lifecycle

Do not differentiate the arbitrary-precision fallback. Do not introduce a
floor, `epsilon I`, support threshold, clipping, deletion, normalization,
or straight-through estimator. A successful future protocol execution is a
gradient-validity prerequisite only; it does not approve a hard threshold or
publication-scale training.
