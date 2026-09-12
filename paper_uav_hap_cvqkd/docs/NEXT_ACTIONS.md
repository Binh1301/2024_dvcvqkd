# Next Actions

## Current gate

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

The documentation and source alignment audit is complete. No training, threshold approval,
baseline selection, final-test access, or publication-scale evaluation is
authorized.

## Latest completed task: EVID-0081 / DEC-0065

The frozen PS+V_A sector ladder was completed for the existing repaired-
objective median checkpoint. The 1050 diagnostic and 1250/1450 acceptance
rows resolved total support 256 and the acceptance pair passed the frozen C/w
criterion. The authoritative values are
`C_PSVA=0.8610813007552428909072445071897962976560950806268` and
`w_PSVA=0.0067220381757562110710871873472856506670610666856165`.

The one exact median full-Z evaluation passed its interval check and returned
raw `K=+0.0003801578161163992`; the exact median classification is
`PS_VA_MEDIAN_BEST` with order PS+V_A > Full > MB. This is a median-only
result and does not authorize any poor/good evaluation, training, baseline
selection, final-test access, or publication-scale run.

Artifact:
`results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`, SHA-256
`9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`.

Recommended next task, requiring separate authorization: exact poor + good
ranking only. Do not execute it from this handoff.

## Historical bounded analysis outcome before EVID-0081

The analysis-only surrogate and exact AP/full-Z anchor workflow is complete
and recorded in EVID-0074. It produced six analysis-grade SVG figures, but all
active exact raw-K anchors are negative and Full does not meaningfully improve
the fixed MB baseline. Treat the result as `MIXED_PRELIMINARY_SUPPORT`, keep
`ANALYSIS_FIGURES_READY`, and retain `NOT_PUBLICATION_CERTIFIED`.

Do not launch a publication-scale run or spend this task on MPFR/MPC reverse
engineering. EVID-0075/DEC-0059 identify the decisive blocker: the smooth
search proxy evaluates `Z` below the frozen source-moment interval in all 16
active states. The selected next task is a bounded interval-preserving
objective repair and fixed-baseline/ranking recheck; that authorization has
now been consumed by EVID-0076. It authorized only the isolated diagnostic
recheck, not production training or final evaluation.

That repair is now complete under EVID-0076/DEC-0060. The existing full-Z
path was reused with surrogate `C,w` during search; all `96/96` old proxy rows
were reproduced as below-`Z_L`, while the repaired search had `0/96` interval
violations. Case-A, existing exact-anchor equivalence, rank consistency, and
PS/GS/V_A gradient smoke passed. The bounded PS+V_A and Full 50-step checks
passed their 20-step smoke. Full exceeded MB at all three available exact
states, but optimized PS+V_A failed closed at the full-support AP gate, so
the exact adaptive ranking remains incomplete. Classification is
`FULL_Z_SEARCH_OBJECTIVE_REPAIRED`; novelty remains
`CURRENT_NOVELTY_NOT_SUPPORTED`.

Historical EVID-0077/DEC-0061 record the earlier read-only root-cause audit of
that gate; DEC-0062 below supersedes its next-action interpretation.
The failed PS checkpoint has p_min approximately 0.00163--0.00228, q_max/q_min
approximately 2.66--4.50, and logit range below 1.51. The weighted-Gram scale
bound does not support probability concentration as the primary cause; direct
binary64 hex transfer is also the current exact-input path. A 300-digit probe
resolves only 206 modes for both PS median and Full median, while Full resolves
at 800/900 digits and PS remains FAIL_CLOSED there. Precision/conditioning is
therefore relevant, but a PS-specific worker/solver failure remains unresolved.
The selected next category is exactly `INVESTIGATE_AP_WORKER_BUG`.

Cases A--D now have corrected bounded exploratory evidence at N=1000 channel
samples per case. Case A and the new B-D source-moment/full-Z result remain
evaluation-only; no publication or certification claim follows.

The Gram root-cause audit found floating-point roundoff plus severe numerical
ill-conditioning, not duplicate states or probability support loss. The old AP
worker w definition was corrected and the bounded Case A result was rebound;
it remains evaluation-only and must not be used for training or certification.

The corrected Case A AP/source-moment/full-Z result is recorded in EVID-0066.
EVID-0062, EVID-0063, and all old worker-backed w-dependent artifacts are
marked SUPERSEDED_WRONG_AP_W.

The old B-D subset is not current evidence. The corrected B-D rebind is
recorded in EVID-0067; its exact historical indices were unavailable, so the
artifact records a deterministic reconstructed active roster.

The short differentiable investigation classified the current exact complex128
path as EXACT_FULL_SUPPORT_NOT_PRACTICAL_IN_COMPLEX128. The isolated AP
implicit-adjoint prototype passes cheap fixtures but failed one bounded
  corrected 800-digit PS target VJP by many orders of magnitude; EVID-0068
  classifies it AP_CUSTOM_BACKWARD_NOT_VALIDATED. The isolated forward
  tangent now covers GS-real, GS-imaginary, and V_A; reverse/full-Z work
  remains closed. Do not train.
- The full-support differentiable source-moment research audit is recorded in
  FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md and EVID-0069. It
  recommends an exact C4 constrained-solve forward tangent before reverse
  repair; this recommendation does not authorize training.
- EVID-0070 records the isolated exact C4 constrained-solve tangent for PS.
  EVID-0071 records the bounded GS-real, GS-imaginary, and V_A extensions;
  all four directions pass at 800 digits, but the remaining direction totals
  are 2001.04 s, 2878.94 s, and 1795.96 s. The exact tangent remains
  diagnostic-only and is not practical for adaptive training.
- EVID-0072 records the constrained reverse practicality study. The
  solve-based reverse is mathematically sound as a design, but primitive
  adjoint identities, target reverse validation, and compiled timing remain
  unrun. The selected path is
  SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE.
- EVID-0073 records the deep research refinement. The primary prototype
  backend is C++17 MPFR/MPC point arithmetic; Arb/acb_mat is reserved for
  independent reference/enclosure checks. The report supplies the exact
  right-solve/Sylvester adjoints and conservative \(C,w\)-to-\(Z\) value
  error propagation, but it does not validate a reverse VJP or authorize
  training.

## Current numerical decision (2026-09-12)

EVID-0078 and DEC-0062 supersede the earlier worker-bug interpretation for
the current median-checkpoint numerical question. The unchanged worker now
has successive high-precision full-support rows for PS and Full, and the
independent direct 100-digit global construction reproduces the C4 structure.
The dense-check decision is
LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT. The immediate
AP-blocker classification is INSUFFICIENT_AP_PRECISION.

EVID-0079 and DEC-0063 record the bounded follow-up. The independent global
audit completed PS at 80 digits, timed out PS at 120 digits, and did not start
PS at 200 digits or any Full row. The 900-second watchdog ended in
`DENSE_LOW_PRECISION_COST_BOUNDED_SKIP`; the completed PS row passed the
global/C4 structure and resolved-spectrum-union checks. This partial result
does not provide a support certificate or a complete PS-versus-Full global
comparison.

## Historical research-only precision decision before EVID-0081 (2026-09-12)

EVID-0080/DEC-0064 select exactly
`DIRECT_HIGHER_PRECISION_SECTOR_RUN`. The next source-moment ladder starts at
1050 decimal digits, with acceptance at 1250 and confirmation at 1450 digits,
using the existing four 64-by-64 C4 sectors and exact binary64-hex inputs. The
frozen `1050,1250,1450` protocol remains unchanged. Existing 800/900 and
1000/1200 rows are diagnostic evidence and are not silently promoted to the
selected protocol row.

After the source-moment pair passes, evaluate only the median full-Z point.
Do not run a dense high-precision global eigensolve, 1600/2000-digit
escalation, outcome-driven mixed-precision aggregation, an Arb migration, a
source-moment reformulation, training, baseline selection, or final-test
evaluation. A timeout or failed residual/convergence gate remains fail-closed.

## Exact next numerical action

The minimum sector-precision task is complete under EVID-0081/DEC-0065. The
remaining analysis blocker is the incomplete three-state exact PS+V_A
adaptive ranking. If separately authorized, execute exact poor + good
ranking only. Do not execute it from this handoff. Do not run the dense
700--900-digit global target, complete reverse, full-Z backward, adaptive
training, baseline selection, final-test access, or publication-scale
evaluation.

DEC-0057's C++17 MPFR/MPC one-sector primitive benchmark remains a separately
scoped, unexecuted recommendation and is not needed to interpret the current
objective blocker.

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
