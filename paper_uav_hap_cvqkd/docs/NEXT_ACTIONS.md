# Next Actions

## Latest AP coverage result: EVID-0093 / DEC-0077

The priority AP batch is restartable but blocked by the existing one-hour
arbitrary-precision subprocess timeout. Exact coverage is `19/143` global,
`26/59` local, `9/18` boundary, and `8/43` uniform. Failure ledgers record
the unresolved points; no C,w interpolation or numerical weakening is allowed.

Do not run Brent/golden-section, choose a uniform baseline, or claim a global
optimum. The next permitted step is an explicit runtime decision for resuming
the same cache (or a separately authorized environment with the same precision
ladder). Preserve all successful JSON source files and failed-point ledgers.

## Latest global joint MB/V_A coverage result: EVID-0092 / DEC-0076

The cache-bound global diagnostic is complete but fail-closed. It produced all
required artifacts, with exact coverage `15/143` for the interior grid,
`5/18` for the boundary grid, and `5/43` for the uniform scan. The best
tested exact point remains `(nu_raw,V_A)=(.24,1.95)`, not a global optimum.

Do not select a baseline or run Brent/golden-section yet. The next numerical
step, if authorized and computationally budgeted, is a fresh exact AP source
batch covering the missing boundary, uniform coarse/refinement, and global
grid points. Preserve cache identity and report the fresh-point budget. Do not
run Adam or use interpolation.

## Latest joint MB/V_A result: EVID-0091 / DEC-0075

The exact joint landscape and local stencil are complete. Best tested local
point: `(nu_raw,V_A)=(.24,1.95)`, `SKR=2.1544608008872113e-05`. It is not a
global optimum certificate.

Do not run Adam. A separately authorized next task may perform a deterministic
global/boundary search using exact cache-bound evaluations, but it must certify
the full domain and uniform optimized baseline before claiming a joint optimum.

## Latest authorized MB boundary result: EVID-0090 / DEC-0074

The authorized exact-MB stage reached the hard peak-photon boundary at
`nu_raw=0.30`; `.20,.22,.25` are exact and increasing, but no valid interior
turnover is bracketed. The reduced-support QPSK-like limit is diagnostic only
and does not define production `K_infinity`.

Do not run Brent/golden-section without an interior bracket. Do not weaken the
peak constraint or production positive-PMF invariant. The next numerical task,
if needed, is a separately scoped boundary analysis or author decision about
the physical peak domain—not Adam.

## Latest reconciliation result: EVID-0089 / DEC-0073

Old coarse MI is now classified `STOCHASTIC_COARSE_ONLY`. Deterministic GH MI
is nearly invariant across the low-SNR MB range, while the deterministic coarse
SKR maximum on the tested grid is `nu_raw=0.20`.

The exact full-SKR point evaluator is ready, and Holevo derivatives are not
needed for a bounded scalar method. Do not launch that method from this state:
optimized-MB search/baseline selection remains lifecycle-gated. A separately
authorized search must use deterministic GH MI and exact hash-matched C,w.

## Latest deterministic MI result: EVID-0088 / DEC-0072

Deterministic GH MI and `dI_AB/dnu_raw` are verified. The exact 16-PAM product
acceleration is valid, and the five-point MC cross-check passes with 65536
samples/symbol. This does not make the full SKR differentiable because AP C,w
and Holevo remain evaluation-only.

Do not start full-SKR scalar search or Adam from this state: optimized-MB search
and baseline selection remain lifecycle-gated. The next task must explicitly
address the full-K derivative/Holevo cost while retaining exact source-cache
identity.

## Latest exact TEST2 readiness result: EVID-0087 / DEC-0071

The exact common-ensemble evaluator and safe exact-hash source cache pass. The
bounded seven-point coarse landscape has its numerical maximum at
`nu_raw=0.16`, but both FD rows are unresolved against paired CRN uncertainty.
TEST2 Adam and TEST3 remain `NOT RUN`.

Do not tighten h, weaken the readiness threshold, reuse the invalid historical
cached sweep, or call 0.16 a continuous optimum. The next defensible optimizer
task requires a prospectively fixed MI-noise reduction plan using the existing
exact source cache and the same common-ensemble evaluator; do not start it from
this state without separate authorization.

## Latest completed optimizer diagnostic: EVID-0086 / DEC-0070

Synthetic Adam/FD TEST 1 passed. Its old source-availability blocker is
superseded by EVID-0087; the active blocker is unresolved physical FD relative
to MI Monte Carlo uncertainty.

## Latest completed MB phase rebound: EVID-0085 / DEC-0069

The supplied MB C,w sweep was rerun with the diagnostic phase strength
`C_n,phase^2=9.4e-18 m^-2/3`. All ten rows passed and became positive; the
least/maximum grid value is at `nu_MB=0.20`,
`K=0.00004194428949251256` bits/symbol.

This remains a conditional diagnostic using historical supplied C,w rows.
Do not promote the grid maximum to production baseline selection.

## Latest completed MB diagnostic: EVID-0084 / DEC-0068

The supplied ten MB `C,w` rows were applied to the conditional new channel
with `tau_zen=0.92`, `zeta=30 deg`, `V_A=2`, and legacy diagnostic
`eta_AO=0.95`. All rows passed; all raw SKRs were negative. The least-negative
grid point was `nu_MB=0.20`, `K=-0.00018194195597724065`.

This is not baseline selection. Do not promote the grid maximum to a
production MB choice; the C,w source rows retain historical provenance.

## Latest completed channel consistency task: EVID-0083 / DEC-0067

The active channel and conditional PDF path now use direct `tau_zen` atmospheric
attenuation, the latest HV ground value `1e-14`, the corrected slant
finite-aperture factor, explicit `F0`, and manuscript beam-spread/equivalent
pointing. Production `tau_zen` remains `null` by design; no `0.92`, `0.89`, or
`0.75` scenario was silently selected. Explicit conditional diagnostics used
`tau_zen=0.92` only for formula/PDF validation.

The next required author decision is to select and approve one atmospheric
`tau_zen` scenario. Until then, do not run configuration-driven channel
generation, security/SKR evaluation, baseline selection, training, final-test
access, or publication-scale work.

## Latest completed channel task: EVID-0082 / DEC-0066

The attached manuscript HAP-UAV channel audit is complete for the optical
transmittance law only. The active configuration derives Hufnagel–Valley
finite-aperture `v_sc`, retains the AoA atom at (T=0), and excludes phase
noise from (p_T). Results are in `results/channel_pdf_and_moments.json` and
the preliminary channel figure files. This is diagnostic evidence only.

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
