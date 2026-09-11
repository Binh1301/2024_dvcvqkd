# Deep research investigation: why the smooth proxy improves while exact Full-Z does not

Date: 2026-09-11
Status: `CURRENTLY_VERIFIED_PASS` for the diagnostic audit; `ANALYSIS_ESTIMATE`, not a security certification
Scope: current phase-disabled Case-D exploratory analysis and the frozen full-
`Z` DM-CV-QKD target

## Executive decision

The primary blocker is now identified. The bounded search objective used by the
analysis runner does not preserve the frozen source-moment interval. In every
one of the 16 active grid states, for every saved method candidate, the search
proxy evaluates the Holevo function at a `Z` below the admissible lower endpoint
`Z_L`. The observed ratio `Z_proxy / Z_L` is approximately `0.767--0.790`.

This is not an MPFR/MPC, arbitrary-precision, or source-moment-differentiation
problem. It is an objective-definition problem. The proxy is smooth and
finite, but it is neither the prescribed `max_{Z in [Z_L,Z_U]}` functional nor
a demonstrated upper or lower bound for it. It can therefore improve during
optimization while sending the policy in a direction that does not improve
the exact full-`Z` rate.

The weight arithmetic and the raw-rate aggregation are internally consistent
for the current diagnostic fixture. The negative-key regime is real and
important, but it cannot explain the proxy/exact rank reversal: the exact MB
baseline has positive cells at the declared `beta=0.95`, while the proxy has no
positive cells for either fixed baseline. GS degradation and joint PS/GS/`V_A`
interference remain plausible secondary effects, but they are confounded until
the objective is repaired.

The one immediate numerical task is:

> **Repair and boundedly re-run the objective with an interval-preserving `Z`
> parameterization (or the exact full-`Z` functional), then compare the proxy
> and exact rankings on the fixed diagnostic grid. Do not start AP
> publication-scale training.**

The current paper direction is:

> **`CURRENT_NOVELTY_NOT_SUPPORTED`: do not present Full PS+GS+`V_A` as a
> positive joint-adaptation result on the current evidence.**

That decision is revisitable only after the repair and the gates in Section 12;
it is not permission to select baselines, access final-test data, or begin a
publication run.

## 1. Question, scope, and authority

The question is why the short-run surrogate objective improves for PS,
`V_A`, PS+`V_A`, and Full, while the exact full-`Z` evaluation does not produce
a meaningful Full advantage over the simpler MB baseline.

This investigation uses the repository as the authority:

- The frozen target is the full physical interval
  `I=[Z_L,Z_U]`, followed by `chi_BE^ub=max_{Z in I} chi_BE(Z)`.
- The raw objective is `K_raw=beta I_AB-chi_BE`; it is deliberately not
  clipped by `max(0,K_raw)` inside training.
- Statewise rates are evaluated before the declared fading-distribution
  average.
- The same statewise physical ensemble must feed mutual information and the
  Holevo branch.
- The current adaptive fading calculation remains an oracle-CSI asymptotic
  functional. It is not a certified operational security proof for the
  continuously varying fading average.

Primary local records are the [frozen model specification](FINAL_MODEL_SPEC.md),
[security-scope freeze](SECURITY_SCOPE_FREEZE.md),
[analysis-figure report](ANALYSIS_FIGURES_REPORT_20260911.md), and the
[objective audit artifact](../results/analysis_objective_audit_20260911.json).

Explicitly out of scope here: MPFR/MPC implementation, arbitrary-precision
backend selection, reverse VJPs, source-moment differentiation, publication-
scale training, final-test access, and a new security claim.

## 2. What the repository actually evaluated

The isolated analysis workflow used a `TRAINING_SURROGATE_ONLY` complex128
source-moment path. It ran 50 bounded steps on six methods over a deterministic
representative grid. The source surrogate passed its local directional and
nearby-ensemble calibration gates, but that only establishes usefulness as a
local numerical aid; it does not validate the search objective.

The exact authority for the reported anchors was the corrected AP source-moment
worker plus the existing full-physical-`Z` Holevo chain. Uniform, MB, and seven
Full anchor rows were evaluated. The saved learned candidate recheck in the
objective audit uses saved surrogate `C,w` values and is consequently labelled
`ANALYSIS_ESTIMATE`, not AP evidence.

The relevant weighted search-proxy changes over 50 steps were:

| method | initial proxy raw `K` | final proxy raw `K` | change |
|---|---:|---:|---:|
| PS | `-0.0274858903` | `-0.0262030233` | `+0.0012828670` |
| `V_A` | `-0.0274858903` | `-0.0273882351` | `+0.0000976552` |
| PS+`V_A` | `-0.0274858903` | `-0.0259604276` | `+0.0015254627` |
| Full | `-0.0274858903` | `-0.0268068077` | `+0.0006790827` |

The proxy ranked PS+`V_A` most favorably and Full second among the learned
methods. A full-`Z` re-evaluation of the saved candidate ensembles, still
using their saved surrogate `C,w`, instead gave:

| method | full-`Z` weighted raw `K` | status of `C,w` |
|---|---:|---|
| MB | `-0.0009584156` | saved surrogate source moments |
| `V_A` | `-0.0011862713` | saved surrogate source moments |
| Uniform | `-0.0011904570` | saved surrogate source moments |
| Full | `-0.0012414747` | saved surrogate source moments |
| PS+`V_A` | `-0.0013604518` | saved surrogate source moments |
| PS | `-0.0013843874` | saved surrogate source moments |

This rank reversal is the central numerical observation. It is not a final
learned-model result because the learned `C,w` values were not regenerated by
the corrected AP worker. It is nevertheless sufficient to invalidate the
current proxy as an optimization objective for scientific interpretation.

## 3. Objective audit: the primary blocker

### 3.1 Frozen full-`Z` definition

For each active state, let `C,w` be the source moments and let
`ε=ε_total` be the post-action noise. The target uses

```text
z_minus = 2 sqrt(T) C - sqrt(2 T epsilon w)
z_plus  = 2 sqrt(T) C + sqrt(2 T epsilon w)

a = 1 + V_A
b = 1 + T V_A + T epsilon
z_phys = sqrt(a b - 1 - |a-b|)

Z_L = max(z_minus, -z_phys)
Z_U = min(z_plus,  z_phys)
chi_BE^ub = max_{Z in [Z_L,Z_U]} chi_BE(Z)
```

The interval is a source-moment constraint intersected with the physical
covariance domain. A point can be inside `[-z_phys,z_phys]` and still be
outside the admissible source-moment interval.

### 3.2 What the search proxy did

The analysis runner instead formed

```text
representative = 2 sqrt(T) C + sqrt(2 T epsilon w)
Z_proxy = 0.98 z_phys
           * tanh(representative / (0.98 z_phys + 1e-12))
```

The `tanh` map was introduced as a smooth physical-domain bound. It is not an
interval-preserving map. For the present positive representatives it maps a
value of order `z_phys` to roughly `tanh(1) z_phys`, which is about 24% lower
than `z_phys` and below the source-moment lower endpoint.

### 3.3 Direct numerical evidence

The objective audit reports the following for all six method modes:

- `16/16` active states have `Z_proxy < Z_L`.
- No tested proxy state was above `Z_U`.
- For Uniform, `Z_proxy/Z_L` ranges from `0.76768125` to
  `0.78811291`, with mean `0.77869588`.
- For MB, the corresponding range is `0.76698166--0.78664575`, with mean
  `0.77757531`.
- The learned modes also have all 16 states below `Z_L`.

At the first Uniform grid state (`T=0.0122605976`,
`ε_base=0.0053997214`, `V_A=1`), the audit gives approximately:

```text
valid interval: [0.1888606775, 0.1919762611]
z_phys:          0.1923028971
z_proxy:         0.1449848007

exact full-Z chi_BE: 0.0076528122
proxy chi_BE:       0.0293999753
exact raw K:        +0.0006380156
proxy raw K:        -0.0211091475
```

The proxy point remains within the broad covariance physicality interval
`[-z_phys,z_phys]`, but it violates the source-moment interval. The large
Holevo and rate discrepancy is therefore expected from evaluating the wrong
domain; it is not evidence that the AP source moments are inaccurate.

For the fixed baselines, the weighted comparison is:

| method | exact full-`Z` weighted raw `K` | search-proxy weighted raw `K` | exact positive cells | proxy positive cells |
|---|---:|---:|---:|---:|
| Uniform | `-0.0011904563` | `-0.0273018358` | `5/16` | `0/16` |
| MB | `-0.0009584152` | `-0.0273036361` | `7/16` | `0/16` |

The proxy is thus not merely a noisy approximation with a small calibration
error. It changes the security functional being optimized and can reverse
method rankings.

### 3.4 Why this explains the observed behavior

This is a mathematical and numerical inference from the code and audit:

1. The optimizer improves `K` computed from `chi_BE(Z_proxy)`.
2. `Z_proxy` is outside the interval on which the frozen Holevo bound is
   defined.
3. The derivative of that off-domain composition need not agree with the
   derivative of the bounded maximum over `[Z_L,Z_U]`.
4. A method can therefore reduce the proxy's off-domain penalty while changing
   `C,w,V_A`, or the ensemble in a way that worsens the valid full-`Z` maximum.
5. The apparent proxy improvement is real as an optimization trace but has no
   valid interpretation as improvement of the target security functional.

The first repair should either parameterize
`Z=Z_L+s(Z_U-Z_L)` with `s in [0,1]` (using a stable sigmoid or bounded
quadrature nodes) or evaluate the exact bounded full-`Z` functional. Any
smooth approximation must be checked for interval inclusion and ranking
consistency before it is used to train a policy.

## 4. Weight and aggregation audit

The current analysis fixture contains 1000 realizations: 732 active and 268
AoA-outage rows. The 16 active representative rows have equal unconditional
weight `0.04575`; the explicit outage mass is `0.268` and receives raw `K=0`.

| quantity | value |
|---|---:|
| active state count | `16` |
| active mass | `0.732` |
| outage mass | `0.268` |
| active weight range | `0.04575--0.04575` |
| all weights including outage | `0.9999999999999999` |
| conditional-active normalization factor | `1/0.732 = 1.3661202186` |

The aggregation arithmetic is therefore a `CURRENTLY_VERIFIED_PASS` for this
diagnostic artifact. Conditioning on active states would multiply every active
method by the same positive factor and cannot explain a method rank reversal.
The outage mass makes the unconditional average smaller, but it contributes
zero to every method and cannot make Full lose to MB when the active comparison
already has that ordering.

The frozen raw objective intentionally keeps negative statewise rates. Replacing
it with `max(0,K_raw)` would answer a different transmit/abstain or
post-selection question and is not authorized by the security-scope freeze.
Thus negative values are not, by themselves, an aggregation bug.

There is one separate distribution limitation: the representative grid was
constructed from four `T` bins crossed with four independently binned
`ε_base` values. In the underlying active sample, the reported correlations
were `corr(T,ε)=-0.0152023` and
`corr(log10(T),ε)=0.00288396`, consistent with no detected linear dependence in
this fixture. This does not establish the production joint distribution,
because the physical turbulence, AoA, phase, CSI, and conditioning protocol
remain unresolved.

## 5. The negative-key regime and the `K(T,ε)` map

The exact MB map below uses the 4-by-4 representative grid, full-`Z` Holevo,
the corrected source moments, and `beta=0.95`. Entries are raw bits/use; they
are not clipped.

| `T` \\ `epsilon_base` | `0.00539972` | `0.01550684` | `0.02556642` | `0.03504351` |
|---|---:|---:|---:|---:|
| `0.0122606` | `+0.0007975` | `+0.0002000` | `-0.0000318` | `-0.0015866` |
| `0.0191655` | `+0.0010890` | `+0.0001994` | `-0.0022317` | `-0.0042017` |
| `0.0270374` | `+0.0041421` | `-0.0004287` | `-0.0054137` | `-0.0071097` |
| `0.0409908` | `+0.0020283` | `+0.0034904` | `-0.0039657` | `-0.0079260` |

Seven of the 16 active MB cells are positive at `beta=0.95`, corresponding
to active mass `0.32025` on the equal-weight representative grid. Uniform has
five positive cells. The exact Full anchors at the median epsilon
`ε_base=0.0202532231` are all negative, so the current scenario is a
low-rate/noisy regime for the selected slice, but not an everywhere-negative
regime.

The beta required to make a cell nonnegative is `beta_threshold=chi_BE/I_AB`.
Across the exact MB grid it ranges from approximately `0.7541` to `1.3710`.
Cells requiring beta above one cannot be rescued by a physical reconciliation
efficiency. A beta of `0.95` is therefore a meaningful scenario assumption,
not a guarantee of a positive average.

The research brief also contains a positive reference at
`T=0.02891967294`, `epsilon_base=0.001`, `V_A=1`, with raw
`K=+0.0047576355`. That point lies outside the present noisy grid and shows
that the negative result is scenario-sensitive. It does not validate Full or
the current fading average.

At the seven median-epsilon AP anchors, Full beats MB only at the lowest `T`
by about `1.63e-5` bits/use; it is worse at the other six points:

| `T` | MB raw `K` | Full raw `K` | Full minus MB |
|---:|---:|---:|---:|
| `0.00733391` | `-0.00106600` | `-0.00104966` | `+0.00001635` |
| `0.01390030` | `-0.00123299` | `-0.00152919` | `-0.00029620` |
| `0.01826877` | `-0.00209067` | `-0.00254621` | `-0.00045554` |
| `0.02218176` | `-0.00212581` | `-0.00257898` | `-0.00045318` |
| `0.02831498` | `-0.00146224` | `-0.00195311` | `-0.00049087` |
| `0.03667393` | `-0.00152887` | `-0.00244221` | `-0.00091334` |
| `0.06615993` | `-0.00150623` | `-0.00239345` | `-0.00088722` |

The exact-bin estimate is `-0.0015155352` for Full versus `-0.0011516261`
for MB. These AP anchor results are current analysis evidence, not a final
publication evaluation.

## 6. Secondary mechanisms

### GS degradation

There is strong secondary evidence that the current Full update moves in a
harmful local direction:

- The corrected exact local tangent gives `dJ=-0.0004882582` for both the
  real and imaginary GS directions, for the diagnostic `J=1.7C-0.8w`.
- Full anchor `C` is approximately `0.856968--0.857140` and `w` is
  `0.019573--0.019047`, whereas MB has `C=0.8604145894` and
  `w=0.0166204376` in the same AP comparison.
- The learned Full geometry is close to the QAM reference, with relative
  prototype RMS displacement about `0.00578`; it has not found a large useful
  geometric deformation.

This is a numerical inference, not a global proof that GS is harmful. The
invalid proxy must be repaired before a Full-minus-GS causal control is
interpretable.

### Joint PS/GS/`V_A` interference

The saved learned source moments are also consistent with destructive
interaction, but are not AP-authoritative:

| method | saved `C` | saved `w` | note |
|---|---:|---:|---|
| PS | `0.8590473` | `0.02082795` | PS-only surrogate candidate |
| `V_A` | `0.8573875` | `0.01827361` | `V_A`-only surrogate candidate |
| PS+`V_A` | `0.8517344` | `0.02057043` | largest saved `C` reduction |
| Full | `0.8570555` | `0.01930524` | near-QAM GS candidate |

The Full learned `V_A` is nearly flat at `0.9956876`; `V_A`-only and
PS+`V_A` are similarly flat. This could indicate weak variance leverage,
gradient competition, or simply the proxy's off-domain landscape. It is not
possible to distinguish those causes yet.

### Undertraining

Only 50 bounded surrogate steps were run. No multi-seed convergence or
validation-stability claim was made. Therefore undertraining remains possible,
especially for GS, but it is not the first experiment: extra steps against the
invalid objective would only improve the wrong target.

## 7. Literature-grounded interpretation

The following are literature-supported facts, separated from the local
inferences above.

| literature-supported fact | relevance to this blocker |
|---|---|
| The arbitrary-modulation asymptotic DM-CV-QKD analysis derives the rate from the actual discrete ensemble and moment information, and has been applied to QAM-like modulation. [1] | A smooth surrogate must preserve the source-moment constraints used by the security functional; differentiability alone is insufficient. |
| Tight DM analyses treat modulation/postselection choices as part of the protocol and optimize them in the stated channel model. [2][3] | A gain for one modulation or postselection setting is not a universal gain for a different fading/phase/noise scenario. |
| Free-space fading work emphasizes conditional channel characterization, estimation, and state clustering/binning; subdivision trades lower fading uncertainty against fewer samples per group. [4][5] | A continuous oracle-state average cannot automatically be promoted to an operational fading security claim. The joint distribution and aggregation protocol must be frozen. |
| A recent numerical free-space DM-CV-QKD study reports that amplitude postselection can improve SKR while phase postselection can degrade it, and that transmittance-postselection gains can disappear once finite-size effects are included. [6] | It supports testing PS and phase/geometry branches separately and warns against assuming that every adaptive branch is complementary. The current fixture has phase disabled, so the result is not a direct reproduction. |
| Adaptive signal-processing work reports that the useful modulation choice depends on reconciliation efficiency and that postselection has a success-probability cost; it also finds no universal postselection benefit when the underlying operating point is already good. [7] | `beta`, operating point, and selection semantics must be treated as controlled variables after the objective repair. |
| Recent probability-shaped DM-CV-QKD theory and experiment show that shaping can be useful in a matched static channel, including high-rate 16-QAM demonstrations. [8][12] | These results support the plausibility of PS in principle, but do not validate this Full adaptive fading method or its current proxy. |
| Reconciliation efficiency is SNR- and implementation-dependent. Practical studies report rate-adaptive behavior, FER effects, and efficiencies below an ideal constant; theory warns that assuming optimal efficiency can be optimistic at long distance. [9][10][11] | The current `beta=0.95` is an asymptotic scenario parameter, not a realized code/FER result. It should not be used to explain away the objective mismatch. |

The literature therefore supports the following framing: source-moment domain
fidelity, channel conditioning, and reconciliation assumptions are all
first-order; no cited result licenses replacing an admissible full-`Z`
maximization by an unvalidated `tanh` representative.

## 8. Ranked hypotheses H1--H6

The labels preserve the six hypotheses in the research brief. “Priority” is
causal priority for the next investigation, not confidence that a mechanism is
globally proved.

| priority | hypothesis | current status | evidence for/against | falsifying or resolving check |
|---:|---|---|---|---|
| 1 | **H1: objective/aggregation mismatch** | **Confirmed for the objective; aggregation arithmetic passes.** | `Z_proxy` is below `Z_L` in `16/16` states; baseline proxy/exact values and candidate rankings disagree. Weights sum to one and active renormalization is a common factor. | Replace the proxy by an interval-preserving objective and repeat the fixed-grid baseline/ranking audit. |
| 2 | **H4: GS degradation** | Strong secondary numerical signal; not globally established. | Exact GS tangent has negative `dJ`; Full AP anchors generally lose to MB; Full geometry remains near QAM. | Matched repaired-objective Full-minus-GS control with AP `C,w` and full-`Z` anchors. |
| 3 | **H5: joint PS/GS/`V_A` interference** | Plausible secondary mechanism; confounded. | Saved PS+`V_A` and Full source moments degrade relative to MB, while `V_A` is nearly flat. | Freeze the repaired objective; compare PS+`V_A` against Full-minus-GS at identical states, seeds, budgets, and exact security evaluation. |
| 4 | **H2: negative-key physical regime** | Real, but insufficient as the primary explanation. | Many high-`ε` cells are negative, yet MB has `7/16` positive cells at `beta=.95` and the low-noise reference is positive. | Sweep the declared `ε` regime only after objective repair; retain raw rates and report positive-state mass separately. |
| 5 | **H6: channel/joint-distribution/`beta` mismatch** | Important external-validity blocker; not the current proxy inversion. | The grid is an independent Cartesian diagnostic; phase is disabled; CSI is oracle; no production turbulence/AoA/phase mapping or realized FER is frozen. | Author-approve one common scenario, freeze the joint distribution and block/bin aggregation, and repeat all methods fairly. |
| 6 | **H3: undertraining** | Unresolved and likely contributory only after H1. | 50 steps and one short run do not establish convergence; however, more steps would optimize an invalid functional. | Multi-seed convergence and held-out validation after interval-preserving objective passes. |

## 9. Fair comparison protocol after the repair

The fixed `nu=0.1` MB row is a useful diagnostic baseline, but it was not
selected as a formal optimized MB baseline. A fair later comparison should
include, under one preregistered scenario:

1. Uniform 256-QAM.
2. Fixed MB, with its parameter declared before evaluation.
3. Optimized MB, selected using training/validation only and not final-test
   data.
4. PS only.
5. `V_A` only.
6. PS+`V_A` with GS frozen.
7. Full PS+GS+`V_A`.

Every method must use the same raw objective, the same channel weights and
outage rule, the same post-action epsilon, the same exact ensemble in MI and
Holevo, the same full-`Z` interval/maximizer, the same beta assumption, and
the same convergence/seed/validation protocol. Proxy-only rankings must not be
reported as security rankings.

For beta, the current `.95` can remain a clearly declared asymptotic scenario
value during the repair. It should later be accompanied by a sensitivity sweep
and, for any practical claim, a reconciliation-code/FER model or measurement.
The required beta threshold map is already a useful diagnostic; it must not be
used to silently discard negative states.

## 10. Deferred exact checks, in the correct order

The requested exact PS+`V_A` check and Full-minus-GS control remain necessary,
but they are downstream of H1:

- **Exact PS+`V_A` check:** after the objective repair, evaluate PS+`V_A` on
  the same representative `T`/epsilon grid or a preregistered slice with AP
  `C,w`, the full physical interval, and identical MI/Holevo ensembles.
- **Full-minus-GS control:** hold GS at the QAM reference, optimize/evaluate
  PS+`V_A` under the repaired objective, and compare it with Full at matched
  states, budgets, seeds, and checkpoints.
- **Convergence check:** only after the two method definitions are fixed, use
  multiple seeds and a held-out validation roster. Do not use the current 50
  steps as evidence of global optimization.

These are not alternative immediate tasks. They are acceptance checks within
the one selected objective-repair investigation. Running them first would
leave the causal result confounded by the invalid proxy.

## 11. One immediate numerical task

### Selected task: interval-preserving objective audit and bounded rerun

Implement the smallest isolated analysis change that replaces the `tanh`
representative with an admissible interval construction, preferably:

```text
s = sigmoid(r)
Z_candidate = Z_L + s * (Z_U - Z_L)
```

or a small fixed set of interval nodes with a differentiable aggregation that
is explicitly documented. The exact bounded full-`Z` solver is the reference.

Run only the following bounded checks:

1. Verify `Z_candidate in [Z_L,Z_U]` for every active state and method.
2. Re-evaluate Uniform and MB with both the repaired objective and exact
   full-`Z`; require small absolute/rank discrepancies before any learned
   update is interpreted.
3. Re-run a short, explicitly analysis-only optimization for the saved method
   set, then re-evaluate the resulting candidates with the exact full-`Z`
   path. Keep the same grid, outage mass, beta, seeds, and no-final-test rule.
4. Stop if the repaired objective is still not rank-consistent with exact
   full-`Z`; record `FAILED` and do not scale the run.

This is a diagnostic numerical task, not publication training, baseline
selection, final-test evaluation, or adaptive-training authorization.

## 12. GO/NO-GO gates

### GO for a later method-comparison study only if all hold

- The search objective is interval-valid and its fixed-baseline values and
  rankings agree with exact full-`Z` within a preregistered tolerance.
- Exact PS+`V_A` and Full-minus-GS controls are evaluated with AP source moments
  on matched states; any gain is not confined to one marginal anchor.
- At least one author-approved, source-supported channel/phase/AoA scenario is
  frozen, including the joint `T,epsilon` distribution and outage/aggregation
  protocol.
- The result is positive in aggregate raw `K` under the declared scenario and
  shows a meaningful, reproducible gain over both fixed and properly selected
  MB baselines.
- Multiple seeds, convergence, and held-out validation are complete; no
  policy is selected on final-test data.
- `beta` is either explicitly asymptotic/ideal in the paper or supported by a
  declared reconciliation and FER model. No practical claim is made from a
  bare constant.
- The relevant security and numerical scope approvals are independently
  present. The current project state does not satisfy these gates.

### NO-GO for the current positive novelty claim if any hold

- The repaired objective still reverses ranking against exact full-`Z`.
- Full wins only at a tiny or isolated state while losing the aggregate or the
  matched Full-minus-GS control.
- A positive claim depends on `max(0,K_raw)`, silent outage removal, an
  unreported beta change, or proxy-only values.
- Channel/phase/CSI/aggregation assumptions remain unresolved but are described
  as an operational fading security result.
- The only available learned source moments are surrogate estimates and not
  independently checked by the corrected AP authority.

Current status is `NO-GO` for publication-scale method claims. The status of
the objective audit itself is `CURRENTLY_VERIFIED_PASS`; the method claim is
not.

## 13. Final answers to the core questions

**Why does the proxy improve while exact Full does not?**  Because the proxy
optimizes a smooth off-domain value of the Holevo function. Its `tanh` map puts
`Z` below the required source-moment lower endpoint in every tested active
state, so the proxy gradient is not the gradient of the frozen full-`Z`
functional. The proxy improvement is therefore an optimization fact about a
different objective, not evidence of exact security improvement.

**Is the problem weight aggregation?**  No evidence supports that conclusion
for this fixture. Active and outage weights sum to one, and conditional active
normalization is a common factor. The raw negative-rate convention is also
intentional.

**Is the physical regime relevant?**  Yes. Excess noise makes many states
negative and beta matters strongly. It is a secondary scenario blocker, not
the explanation for the proxy/exact rank reversal.

**What one experiment has the highest value?**  Repair the interval-preserving
objective and run the bounded baseline/ranking plus short candidate recheck
described in Section 11. Do not spend the next run on more steps, exact PS+`V_A`,
or Full-minus-GS while the objective is invalid.

**Does current evidence support the proposed novelty?**  No. The correct
current classification is `CURRENT_NOVELTY_NOT_SUPPORTED`; the current exact
Full result is worse than fixed MB in the representative exact-bin estimate,
and the only favorable proxy ranking is invalidated by the interval audit.

## 14. Reproducibility and provenance

The additive diagnostic producer is
[`scripts/audit_analysis_objective.py`](../scripts/audit_analysis_objective.py).
Its output is
[`results/analysis_objective_audit_20260911.json`](../results/analysis_objective_audit_20260911.json).

Recorded hashes at the time of this report:

| artifact | SHA-256 |
|---|---|
| `scripts/audit_analysis_objective.py` | `CABC201737AA3292DA528E1CC616A64F3DFF1BEB25EBF9532FD8F24845F6BE80` |
| `results/analysis_objective_audit_20260911.json` | `BBF6389997941E8447A51261405E45FBFB0B6653A210207F8DDA7D070ACD6B69` |
| `results/analysis_figure_data_20260911.json` | `239d3da2a8cd318d92eab77108f28afd36109cfdd068dc56332d5776b679e699` |
| `scripts/run_analysis_figures.py` | `9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f` |
| `docs/FINAL_MODEL_SPEC.md` | `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843` |

The representative grid provenance is:

- 1000 sampled realizations; 16 active representatives; outage mass `0.268`.
- Active grid hash:
  `af2f912e81000a4b09d1942f28ac03078ddc6602774e9b772ba020c4557c5ad2`.
- Realization hash:
  `12f055fdd8a99dbe672990e4212cf40a41bada654c27f1149a27cf2ab12e34d9`.
- Phase-disabled analysis: `c_phi=0` and
  `epsilon_total=epsilon_base`.

No production source, frozen model specification, final-test dataset, or
lifecycle authorization was changed by this investigation.

## Sources

[1] A. Denys, P. Brown, and A. Leverrier, “Explicit asymptotic secret key
rate of continuous-variable quantum key distribution with an arbitrary
modulation,” *Quantum* 5, 540 (2021),
[Quantum journal](https://quantum-journal.org/papers/q-2021-09-13-540/).

[2] J. Lin, T. Upadhyaya, and N. Lütkenhaus, “Asymptotic security analysis of
discrete-modulated continuous-variable quantum key distribution,” *Physical
Review X* 9, 041064 (2019),
[arXiv:1905.10896](https://arxiv.org/abs/1905.10896).

[3] S. Kanitschar and C. Pacher, “Optimizing continuous-variable quantum key
distribution with PSK modulation and postselection,” *Physical Review Applied*
18, 034073 (2022),
[arXiv:2104.09454](https://arxiv.org/abs/2104.09454).

[4] H. Ruppert et al., “Fading channel estimation for free-space continuous-
variable secure quantum communication,”
[arXiv:2011.04386](https://arxiv.org/abs/2011.04386).

[5] “Feasibility of satellite-to-ground continuous-variable quantum key
distribution,” *npj Quantum Information* 6, 95 (2020),
[Nature](https://www.nature.com/articles/s41534-020-00336-4).

[6] Y. Li et al., “Security analysis of free-space discrete-modulation
continuous-variable quantum key distribution with precise channel
characterization and postselection strategies,” *Physical Review Applied* 25,
024013 (2026),
[APS](https://journals.aps.org/prapplied/abstract/10.1103/v7d9-ylyl).

[7] “Enhanced continuous-variable quantum key distribution protocol via
adaptive signal processing,” *Communications Physics* 8, 406 (2025),
[Nature](https://www.nature.com/articles/s42005-025-02317-5).

[8] A. Parente et al., “Discrete-modulated continuous-variable quantum key
distribution with probabilistic amplitude shaping over a linear quantum
channel,” [arXiv:2603.02870](https://arxiv.org/abs/2603.02870).

[9] M. Gümüş et al., “Rate-adaptive reconciliation for continuous-variable
quantum key distribution over a discrete-modulated free-space optical link,”
*Journal of Lightwave Technology* 43, 3564--3573 (2025),
[Optica](https://opg.optica.org/jlt/abstract.cfm?uri=jlt-43-8-3564).

[10] M. Hajomer et al., “Long-distance continuous-variable quantum key
distribution over 100-km fiber with local local oscillator,” *Science
Advances* 10 (2024),
[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10776027/).

[11] A. Leverrier, “Information reconciliation for discrete-modulated
continuous-variable quantum key distribution,”
[arXiv:2310.17548](https://arxiv.org/abs/2310.17548).

[12] Y. Wu et al., “High-rate discrete-modulated continuous-variable quantum
key distribution with composable security,” *Physical Review X* 16, 021039
(2026),
[APS](https://journals.aps.org/prx/abstract/10.1103/882y-w4zy).
