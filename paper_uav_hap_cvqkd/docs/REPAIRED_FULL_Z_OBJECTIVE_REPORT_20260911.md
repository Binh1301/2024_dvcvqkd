# 1. Skills / workflow used

The repair followed the repository evidence order and the installed
Superpowers/Ponytail workflow. Ponytail constrained the implementation to an
isolated analysis runner, one fail-closed invariant assertion, and focused
tests. The prior Deep Research blocker report was treated as the settled
diagnostic input; no new physical model or publication workflow was opened.

The producer is [`scripts/run_repaired_full_z_objective.py`](../scripts/run_repaired_full_z_objective.py).
The machine-readable result is
[`repaired_full_z_objective_analysis_20260911.json`](../results/repaired_full_z_objective_analysis_20260911.json).
The focused regression tests are
[`test_repaired_full_z_objective.py`](../tests/test_repaired_full_z_objective.py).

The run used the existing phase-disabled, 16-active-state diagnostic grid,
the existing weights/noise/beta, surrogate `C,w` only during search, 9-grid/
2-refinement full-`Z` search, 33-grid/12-refinement production recheck, and a
bounded 50-step analysis optimization for PS+`V_A` and Full. No publication-
scale training, final-test access, MPFR/MPC implementation, C/w definition,
channel, beta, phase, epsilon, outage, or production security equation was
changed.

# 2. Old proxy reconstruction

The old branch is the `search_proxy=True` branch in
`scripts/run_analysis_figures.py`. For each active state it computed

```text
a = 1 + V_A
b = 1 + T V_A + T epsilon
Z_phys = sqrt(max(a b - 1 - |a-b|, 0))
width = sqrt(max(2 T epsilon w, 0) + 1e-18)
r = 2 sqrt(T) C + width
Z_proxy = 0.98 Z_phys tanh(r / (0.98 Z_phys + 1e-12))
```

It then evaluated the covariance Holevo expression at that single point:

```text
chi_proxy = chi_BE(Z_proxy)
K_proxy = beta_rec I_AB - chi_proxy
```

There was no `max_{Z in [Z_L,Z_U]}` and no source-moment interval
intersection in this branch. The following table displays the 16 Uniform
candidate rows; the same calculation was performed for all six modes.

| state | `T` | `epsilon` | old `Z_proxy` | `Z_L` | `Z_U` | `Z_proxy-Z_L` |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.012260598 | 0.005399721 | 0.144984801 | 0.188860677 | 0.191976263 | -0.043875877 |
| 1 | 0.012260598 | 0.015506838 | 0.145760504 | 0.187778581 | 0.193058359 | -0.042018077 |
| 2 | 0.012260598 | 0.025566415 | 0.146397400 | 0.187028788 | 0.193808152 | -0.040631388 |
| 3 | 0.012260598 | 0.035043511 | 0.146943619 | 0.186449957 | 0.194386984 | -0.039506339 |
| 4 | 0.019165542 | 0.005399721 | 0.181270531 | 0.236127340 | 0.240022671 | -0.054856809 |
| 5 | 0.019165542 | 0.015506838 | 0.182240372 | 0.234774425 | 0.241375587 | -0.052534053 |
| 6 | 0.019165542 | 0.025566415 | 0.183036665 | 0.233836979 | 0.242313032 | -0.050800314 |
| 7 | 0.019165542 | 0.035043511 | 0.183719587 | 0.233113282 | 0.243036729 | -0.049393695 |
| 8 | 0.027037351 | 0.005399721 | 0.215302328 | 0.280457975 | 0.285084617 | -0.065155646 |
| 9 | 0.027037351 | 0.015506838 | 0.216454247 | 0.278851063 | 0.286691529 | -0.062396816 |
| 10 | 0.027037351 | 0.025566415 | 0.217400037 | 0.277737621 | 0.287804971 | -0.060337584 |
| 11 | 0.027037351 | 0.035043511 | 0.218211171 | 0.276878057 | 0.288664535 | -0.058666885 |
| 12 | 0.040990840 | 0.005399721 | 0.265100208 | 0.345325886 | 0.351022638 | -0.080225679 |
| 13 | 0.040990840 | 0.015506838 | 0.266518557 | 0.343347308 | 0.353001217 | -0.076828750 |
| 14 | 0.040990840 | 0.025566415 | 0.267683101 | 0.341976334 | 0.354372190 | -0.074293233 |
| 15 | 0.040990840 | 0.035043511 | 0.268681845 | 0.340917959 | 0.355430565 | -0.072236114 |

The all-mode audit confirms `96/96` mode-state rows satisfy
`Z_proxy < Z_L`. Thus `chi_proxy` and `K_proxy` were evaluated at a point
outside the frozen source-moment domain.

# 3. Root cause of interval violation

The cause is a missing source-moment intersection in the old smooth map. The
production interval is built from

```text
Z_minus = 2 sqrt(T) C - sqrt(2 T epsilon w)
Z_plus  = 2 sqrt(T) C + sqrt(2 T epsilon w)
Z_L = max(Z_minus, -Z_phys)
Z_U = min(Z_plus,  Z_phys)
```

The old branch used only a `0.98 Z_phys * tanh(...)` physicality-shaped map.
For these positive representatives, the `tanh` contraction puts the point
well inside `[-Z_phys,Z_phys]` but below `Z_minus`, and the code never applies
`max(Z_minus,-Z_phys)`. This is an objective-definition error, not a C/w
calibration, aggregation, AP-worker, channel, or full-`Z` implementation
error.

# 4. Repaired full-Z search objective

The repaired search reuses the current production path:

```text
surrogate C,w
  -> Z_minus, Z_plus, Z_phys
  -> Z_L=max(Z_minus,-Z_phys), Z_U=min(Z_plus,Z_phys)
  -> max_{Z in [Z_L,Z_U]} chi_BE(Z)
  -> K_repaired = beta_rec I_AB - chi_BE^ub
```

The call path is `_evaluate_transmitter` -> `_surrogate_batch` -> existing
`_holevo_from_source_moments` -> existing `_maximize_bounded_scalar` -> raw
`K`. Search uses the existing deterministic bounded maximizer at grid size 9
and two refinements; the production recheck uses grid size 33 and 12
refinements. Every grid point is generated as an in-interval affine fraction,
and every golden-section refinement remains between its two in-interval
endpoints.

An explicit diagnostic assertion was added in
[`src/cvqkd/holevo.py`](../src/cvqkd/holevo.py): every candidate point passed
to the bounded scalar evaluator must be finite and satisfy the interval up to
`1e-12` scaled tolerance. This is a fail-closed invariant check; it does not
silently clamp the old proxy and does not change the security formula.

# 5. Interval invariant audit

The table shows the Uniform representative rows, including the production
and repaired selected points. All 96 repaired mode-state rows passed; the
machine artifact stores every mode-state row.

| state | `Z_L` | `Z_U` | old `Z_proxy` | production `Z*` | repaired `Z*` | valid? |
|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 0.188860677 | 0.191976263 | 0.144984801 | 0.188860677 | 0.188860677 | yes |
| 1 | 0.187778581 | 0.193058359 | 0.145760504 | 0.187778582 | 0.187778581 | yes |
| 2 | 0.187028788 | 0.193808152 | 0.146397400 | 0.187028789 | 0.187028788 | yes |
| 3 | 0.186449957 | 0.194386984 | 0.146943619 | 0.186449957 | 0.186449957 | yes |
| 4 | 0.236127340 | 0.240022671 | 0.181270531 | 0.236127340 | 0.236127340 | yes |
| 5 | 0.234774425 | 0.241375587 | 0.182240372 | 0.234774426 | 0.234774425 | yes |
| 6 | 0.233836979 | 0.242313032 | 0.183036665 | 0.233836980 | 0.233836979 | yes |
| 7 | 0.233113282 | 0.243036729 | 0.183719587 | 0.233113284 | 0.233113282 | yes |
| 8 | 0.280457975 | 0.285084617 | 0.215302328 | 0.280457975 | 0.280457975 | yes |
| 9 | 0.278851063 | 0.286691529 | 0.216454247 | 0.278851064 | 0.278851063 | yes |
| 10 | 0.277737621 | 0.287804971 | 0.217400037 | 0.277737623 | 0.277737621 | yes |
| 11 | 0.276878057 | 0.288664535 | 0.218211171 | 0.276878059 | 0.276878057 | yes |
| 12 | 0.345325886 | 0.351022638 | 0.265100208 | 0.345325886 | 0.345325886 | yes |
| 13 | 0.343347308 | 0.353001217 | 0.266518557 | 0.343347308 | 0.343347307 | yes |
| 14 | 0.341976334 | 0.354372190 | 0.267683101 | 0.341976336 | 0.341976334 | yes |
| 15 | 0.340917959 | 0.355430565 | 0.268681845 | 0.340917962 | 0.340917959 | yes |

Audit totals: old proxy violations `96/96`; repaired interval violations
`0/96`. The maximum repaired-versus-production `chi_BE` difference in this
audit was `2.71e-9`.

# 6. Case-A reproduction

The corrected reference state was `T=0.028919672940466015`,
`epsilon=0.001`, `V_A=1`, with

```text
C = 0.85985110654649868138037962728289179096834048571987
w = 0.018327610474963502048823295065766568532781601388489
```

| quantity | exact reference source | repaired surrogate source |
|---|---:|---:|
| `I_AB` | 0.02099665844391474 | 0.02099665844391474 |
| `chi_BE` | 0.01518919002933572 | 0.015189189020190952 |
| raw `K` | 0.004757635492383283 | 0.004757636501528051 |
| `Z_L` | 0.2914192733053753 | 0.2914192742561164 |
| `Z_U` | 0.2934784546975139 | 0.2934784570036217 |
| `Z*` | 0.2914192733053753 | 0.2914192742561164 |

The exact reference errors are zero at the stored precision. The repaired
surrogate errors are `|Delta K|=1.0091e-9` and
`|Delta chi_BE|=1.0091e-9`, below the repair gate of `2e-6` for raw K.

# 7. Repaired-vs-exact anchor comparison

Existing exact AP/full-`Z` anchors were reused; no existing source ensemble
was recomputed for this comparison. Across the 21 Uniform/MB/Full anchor
rows, the maximum repaired-surrogate versus exact errors were:

| mode | max absolute raw-`K` error | max relative raw-`K` error |
|---|---:|---:|
| Uniform | 2.5721e-9 | 1.1309e-6 |
| MB | 1.8259e-9 | 1.2123e-6 |
| Full | 5.2219e-9 | 2.1818e-6 |

All seven existing per-anchor orderings were consistent. No PS+`V_A`
existing exact anchor was available. The objective-equivalence gate passed:
zero interval violations, anchor agreement, rank consistency, unchanged
security equation, and only surrogate `C,w` during search.

# 8. Frozen-candidate ranking

Scores below are unconditional weighted raw K over the same 16 active
representatives. “Exact where available” is the mean of the seven existing
exact AP/full-`Z` anchors for the saved frozen candidate, not a replacement
for the 16-state repaired search score.

| method | old proxy | repaired objective | repaired rank | exact where available |
|---|---:|---:|---:|---:|
| Uniform | -0.0273018358 | -0.0011904570 | 3 | -0.0019206456 |
| MB | -0.0273036361 | -0.0009584156 | 1 | -0.0015732597 |
| PS | -0.0271853995 | -0.0013843874 | 6 | unavailable |
| `V_A` | -0.0272046117 | -0.0011862713 | 2 | unavailable |
| PS+`V_A` | -0.0268954244 | -0.0013604518 | 5 | unavailable |
| Full | -0.0271286791 | -0.0012414747 | 4 | -0.0020704032 |

The old order was PS+`V_A`, Full, PS, `V_A`, Uniform, MB. The repaired order
was MB, `V_A`, Uniform, Full, PS+`V_A`, PS. This is the expected distortion
from optimizing an off-interval Holevo value; it is not evidence that the
adaptive methods are disproven.

# 9. Gradient smoke

The one-state repaired hard-max objective produced finite, nonzero gradients
for all requested parameter families:

| mode | gradient norm | selected branch | interval valid |
|---|---:|---|:---:|
| PS | 0.0193904980 | lower boundary | yes |
| GS | 0.0042517889 | lower boundary | yes |
| `V_A` | 0.0011612954 | lower boundary | yes |

All values were finite and backward followed the selected valid branch.
No expensive tangent validation was rerun.

# 10. Bounded PS+VA optimization

PS+`V_A` used the repaired 9-grid/2-refinement objective for 50 analysis
steps. Its 20-step smoke passed finite values, positive probabilities, 256
unique states, and non-decreasing short-window objective behavior.

| step | repaired `K` | `beta I_AB` | `chi_BE` | mean `V_A` | PS entropy | energy residual |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -0.0013745115 | 0.0121601601 | 0.0135346716 | 1.0000000000 | 8.0000000000 | -0.5000000000 |
| 10 | -0.0008602606 | 0.0122785127 | 0.0131387733 | 0.9974529324 | 7.9920040247 | -0.5025470676 |
| 20 | -0.0003405454 | 0.0124035378 | 0.0127440832 | 0.9952324552 | 7.9677635691 | -0.5047675448 |
| 30 | 0.0001782839 | 0.0125461171 | 0.0123678333 | 0.9938228857 | 7.9273736005 | -0.5061771143 |
| 40 | 0.0006872038 | 0.0127111339 | 0.0120239301 | 0.9937951428 | 7.8718199110 | -0.5062048572 |
| 50 | 0.0011779455 | 0.0129003347 | 0.0117223892 | 0.9953704226 | 7.8031613194 | -0.5046295774 |

The bounded objective change was `+0.0025524570`. This is an
`ANALYSIS_ESTIMATE`, not a security result.

# 11. Bounded Full optimization

Full used the same channel states, weights, noise seed, energy budget, and
initial PS/`V_A` branches as PS+`V_A`; it additionally exposed GS. Its 20-step
smoke also passed.

| step | repaired `K` | `beta I_AB` | `chi_BE` | mean `V_A` | PS entropy | energy residual | GS displacement |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | -0.0013745115 | 0.0121601601 | 0.0135346716 | 1.0000000000 | 8.0000000000 | -0.5000000000 | 0.0000000000 |
| 10 | -0.0011837348 | 0.0122000660 | 0.0133838008 | 0.9991396973 | 7.9991198378 | -0.5008603027 | 0.0011759369 |
| 20 | -0.0009916533 | 0.0122396285 | 0.0132312818 | 0.9983076179 | 7.9964415907 | -0.5016923821 | 0.0023433729 |
| 30 | -0.0007982421 | 0.0122795536 | 0.0130777957 | 0.9975316726 | 7.9919214173 | -0.5024683274 | 0.0035109214 |
| 40 | -0.0006036369 | 0.0123208535 | 0.0129244904 | 0.9968394543 | 7.9855260915 | -0.5031605457 | 0.0046761200 |
| 50 | -0.0004081160 | 0.0123645923 | 0.0127727083 | 0.9962581009 | 7.9772266499 | -0.5037418991 | 0.0058345010 |

The bounded objective change was `+0.0009663955`. This is also an
`ANALYSIS_ESTIMATE`, not a publication or security result.

# 12. Exact poor/median/good ranking

The same three existing anchor states were used for MB, PS+`V_A`, and Full.
MB used its existing exact AP source moments. Full used new converged
800/900-digit AP source moments, persisted in
[`repaired_full_z_exact_jobs_20260911.json`](../results/repaired_full_z_exact_jobs_20260911.json).

PS+`V_A` was sent through the same corrected AP worker at all three states,
but all three jobs returned `FAIL_CLOSED`; therefore no PS+`V_A` exact K is
inferred. A diagnostic 100/150/200-digit ladder found unresolved ranks of
`162,174,188` (poor), `162,176,188` (median), and `165,176,187` (good), against
the required rank 256. These rows are recorded in
[`repaired_full_z_ps_va_exact_failure_20260911.json`](../results/repaired_full_z_ps_va_exact_failure_20260911.json)
and are not security results.

| state | MB exact raw K | PS+`V_A` exact raw K | Full exact raw K | Full - MB |
|---|---:|---:|---:|---:|
| poor | -0.0011643123 | FAIL_CLOSED | -0.0008491965 | +0.0003151158 |
| median | -0.0004591950 | FAIL_CLOSED | +0.0003328325 | +0.0007920275 |
| good | -0.0007335867 | FAIL_CLOSED | +0.0001854765 | +0.0009190632 |

Equal-weight three-state means were MB `-0.0007856980` and Full
`-0.0001102958`, a Full-minus-MB difference of `+0.0006754022`. Full beat MB
at all three available exact states. The requested Full-versus-PS+`V_A`
decision remains unavailable because PS+`V_A` did not pass the full-support
AP gate.

# 13. Scientific interpretation

The central blocker was successfully repaired: the search now evaluates the
same physical full-`Z` functional as the frozen security semantics, with only
surrogate `C,w` approximated during search. The old proxy ranking must be
discarded because it optimized an off-domain Holevo value.

The bounded exact subset is encouraging for Full relative to MB, but it does
not establish the paper novelty claim. The relevant PS+`V_A` exact ranking is
missing, the channel grid is phase-disabled and exploratory, the optimization
is only 50 steps, and the exact check covers three states. No conclusion that
Full is the final winner, that GS helps, or that adaptive modulation has a
publication-ready gain is justified.

# 14. Final classification

`FULL_Z_SEARCH_OBJECTIVE_REPAIRED`

# 15. Novelty status

`CURRENT_NOVELTY_NOT_SUPPORTED`

# 16. Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

# 17. Remaining blocker

The optimized PS+`V_A` checkpoint does not produce converged full-support
`C,w` source moments in the required high-precision AP worker, so its exact
poor/median/good ranking is unavailable.

# 18. Recommended next task

Add a full-support-preserving PS+`V_A` parameterization or conditioning guard,
then repeat only the three-state exact AP/full-`Z` ranking check and persist
the complete comparison; do not execute that task in this report.

