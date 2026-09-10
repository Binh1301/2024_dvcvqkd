# Next Actions

## Current gate

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

The documentation and source alignment audit is complete. No training, threshold approval,
baseline selection, final-test access, or publication-scale evaluation is
authorized.

Cases A--D have now completed as EXPLORATORY_ONLY channel/MI preflights at
N=1000 per case. Full-Z Holevo/K was intentionally not completed after the
complex128 fast gate failed; the arbitrary-precision fallback remains
evaluation-only.

The Gram root-cause audit found floating-point roundoff plus severe numerical
ill-conditioning, not duplicate states or probability support loss. The old AP
worker w definition was corrected and the bounded Case A result was rebound;
it remains evaluation-only and must not be used for training or certification.

The corrected Case A AP/source-moment/full-Z result is recorded in EVID-0066.
EVID-0062, EVID-0063, and all old worker-backed w-dependent artifacts are
marked SUPERSEDED_WRONG_AP_W.

The old B-D subset is not current evidence. B-D must be recomputed only after
the corrected Case A source moments are accepted in a separate bounded task.

The short differentiable investigation classified the current exact complex128
path as EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128. The isolated AP
implicit-adjoint prototype remains PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION.
Do not train.

## Exact next numerical action

Recompute the bounded B-D exploratory subsets using the corrected Case A C,w
and full-Z path. Do not execute that task in the current lifecycle state
without separate authorization.

## Priority order

### P0 — resolve target-model blockers

1. Freeze one author-approved, source-supported common-turbulence scenario,
   including the altitude profile, aperture-averaging rule, AoA status/mapping,
   and effective C_n,phi^2 phase mapping/value.
2. Rebind numerical/provenance evidence after that complete physical scenario
   is frozen and the full \(Z\)-interval target path is hash-bound.

### P1 — deterministic Friday diagnostics

Use only existing deterministic transmitter modules for regular 256-QAM,
Uniform/Binomial/MB PMFs, C4 orbit expansion, and global-geometry figures.
These do not require training or security evaluation.

### P2 — resolved composite-channel diagnostic, if explicitly labeled

A small runner may visualize the composite sampler only after all supplied
profile, scintillation, pointing, AoA, and raw-domain choices are explicit. It
must be labeled as a diagnostic, not as target numerical evidence.

### P3 — target channel/phase diagnostics

Run only after P0 resolves the required modules and parameters:
\(H_{\mathrm{sc}}\), \(H_{\mathrm p}\), \(B_{\mathrm{AoA}}\), raw/physical \(T\),
\(p_{>1}\), \(\xi_{\mathrm{phase}}(V_A)\), and
\(\epsilon_{\mathrm{total}}(V_A)\).

### P4 — security/SKR and learned output

Run only after P0 plus numerical approval: \(\chi_{BE}(Z)\) over the physical
interval, fixed-baseline K plots, and then learned PS/GS/\(V_A\) diagnostics.

## Stop conditions

- Do not convert historical lower-endpoint Holevo values into target claims
  without the new numerical rebinding.
- Do not use epsilon_total as a policy input or sample it independently.
- Do not call current channel artifacts scintillation/AoA evidence.
- Do not run publication training, baseline selection, optimized-MB search,
  final-test access, or long certification.
