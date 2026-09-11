# 1. Skills / workflow used

Used the repository Superpowers plan in `docs/superpowers/` and the Ponytail
minimal-scope workflow. The work was bounded to a training-only surrogate,
16 active representative states, 0.268 explicit outage mass, six analysis
methods, and exact AP/full-Z anchor evaluation. No MPFR/MPC reverse, complete
reverse, production autograd, publication-scale training, or final-test access
was performed.

# 2. Exact security oracle preserved

The production corrected AP worker, corrected C/w definitions, current
full-physical-Z Holevo interval, channel model, outage semantics, and security
domain checks were not modified. The uniform reference remains:

- C = `0.85985110654649868138037962728289179096834048571987`
- w = `0.018327610474963502048823295065766568532781601388489`
- lambda_min approximately `3.9730108272405810054e-618`
- corrected worker SHA-256: `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`

The old w was not used. Phase is disabled for this analysis:
`PHASE_DISABLED_ANALYSIS_SCENARIO`, `c_phi=0`, and
`epsilon_total=epsilon_base`.

# 3. Training surrogate chosen

The isolated `TRAINING_SURROGATE_ONLY` implementation is
`src/cvqkd/training_surrogate.py`. It consumes per-symbol representative C4
probabilities and 64 complex128 prototypes, adds a bounded spectral
regularization shift inside each 64x64 C4 sector, evaluates the square root,
and uses solve-based B/A factors to obtain smooth C and residual-w moments.
It is separate from `src/cvqkd/gram_moments.py` and is never used as the
authoritative security source moment.

The bounded candidate set was `1e-8`, `1e-10`, and `1e-12`; the selected
stability-first value was `1e-10`.

# 4. Surrogate gradient calibration

All four directions passed sign, C/w reference, and directional gates. Values
below are `(dC, dw, dJ)` with `J=1.7 C - 0.8 w`; relative errors are in the
same order.

| direction | exact tangent | surrogate tangent | sign | relative error | result |
|---|---|---|---|---|---|
| PS | `(5.0092422833e-4, -1.1532623535e-3, 1.7741810710e-3)` | `(5.0092496475e-4, -1.1532708297e-3, 1.7741891039e-3)` | `+,-,+` | `(1.47e-6, 7.35e-6, 4.53e-6)` | PASS |
| GS-real | `(-1.2344647697e-4, 3.4799892529e-4, -4.8825815108e-4)` | `(-1.2344647420e-4, 3.4799900781e-4, -4.8825821238e-4)` | `-,+,-` | `(2.24e-8, 2.37e-7, 1.26e-7)` | PASS |
| GS-imag | `(-1.2344647697e-4, 3.4799892529e-4, -4.8825815108e-4)` | `(-1.2344647420e-4, 3.4799900781e-4, -4.8825821238e-4)` | `-,+,-` | `(2.24e-8, 2.37e-7, 1.26e-7)` | PASS |
| V_A | `(5.7025041894e-1, 1.2488915319e-2, 9.5943457994e-1)` | `(5.7025043025e-1, 1.2488912326e-2, 9.5943460156e-1)` | `+,+,+` | `(1.98e-8, 2.40e-7, 2.25e-8)` | PASS |

# 5. Nearby-ensemble calibration

| ensemble | C exact / surrogate | w exact / surrogate | C relative error | w relative error | domain | result |
|---|---|---|---:|---:|---|---|
| mild PS | `0.8598944472411683 / 0.8598944520989342` | `0.01823035857779745 / 0.01823038193968444` | `5.65e-9` | `1.28e-6` | PASS | PASS |
| mild GS-real | `0.8598468025828229 / 0.8598468073707757` | `0.01833975006849606 / 0.01833977419811992` | `5.57e-9` | `1.32e-6` | PASS | PASS |
| mild V_A | `0.9164314510767270 / 0.9164314570066332` | `0.01952808743262952 / 0.01952811132481117` | `6.47e-9` | `1.22e-6` | PASS | PASS |
| combined | `0.9164557656319341 / 0.9164557716025833` | `0.01947747892467246 / 0.01947750229778735` | `6.51e-9` | `1.20e-6` | PASS | PASS |

# 6. Representative channel grid

The deterministic Case-D exploratory sample used 1000 channel realizations,
with 16 active representatives formed from four equal-probability T bins
crossed with four equal-probability independent epsilon bins. The active mass
is `0.732`; explicit AoA outage mass is `0.268`, and outage rows receive
`K=0` without policy evaluation. Channel seed is `20260910`; epsilon seed is
`4542851964011138592`.

- grid hash: `af2f912e81000a4b09d1942f28ac03078ddc6602774e9b772ba020c4557c5ad2`
- realization hash: `12f055fdd8a99dbe672990e4212cf40a41bada654c27f1149a27cf2ab12e34d9`
- grid artifact: `results/analysis_channel_grid_20260911.json`

# 7. Smoke optimization

The 20-step smoke gate passed for PS, V_A, PS+V_A, and Full. All losses and
gradients were finite; PMFs remained strictly positive and normalized; every
ensemble retained 256 unique states; V_A remained inside `[0.1,4.0]`; the
hard peak value remained below the analysis limit; and each smoke objective
window improved. Uniform and MB were fixed, non-optimized baselines.

# 8. Analysis optimization

The learned methods ran 50 bounded surrogate steps. Weighted search-proxy
objective changes were:

| method | initial | final | change | status |
|---|---:|---:|---:|---|
| PS | -0.0274858903 | -0.0262030233 | +0.0012828670 | ANALYSIS_OPTIMIZED |
| V_A | -0.0274858903 | -0.0273882351 | +0.0000976552 | ANALYSIS_OPTIMIZED |
| PS+V_A | -0.0274858903 | -0.0259604276 | +0.0015254627 | ANALYSIS_OPTIMIZED |
| Full | -0.0274858903 | -0.0268068077 | +0.0006790827 | ANALYSIS_OPTIMIZED |

The search objective is explicitly a smooth bounded training proxy, not a
security certificate. The learned V_A values were nearly state-independent:
V_A-only `0.9956813`, PS+V_A `0.9871317`, and Full `0.9956876`; all stayed
below the average budget of `1.5` SNU. Full GS remained non-collapsed but was
close to QAM: relative prototype RMS displacement was approximately `0.00578`.

# 9. Exact AP security anchors

The table shows the seven active anchors. C and w are compact renderings of
the exact AP strings stored in `results/analysis_exact_ap_security_anchors_20260911.json`.
I_AB, chi_BE, and raw K use the existing full-Z security chain; raw K is not
clipped.

| method | T | C | w | I_AB | chi_BE | raw K |
|---|---:|---:|---:|---:|---:|---:|
| Uniform 256-QAM | 0.0073339133 | 0.8598511065 | 0.0183276105 | 0.0051016133 | 0.0059981948 | -0.0011516622 |
| Uniform 256-QAM | 0.0139002975 | 0.8598511065 | 0.0183276105 | 0.0099801034 | 0.0109324531 | -0.0014513549 |
| Uniform 256-QAM | 0.0182687660 | 0.8598511065 | 0.0183276105 | 0.0123288386 | 0.0141175404 | -0.0024051438 |
| Uniform 256-QAM | 0.0221817634 | 0.8598511065 | 0.0183276105 | 0.0152560571 | 0.0169215990 | -0.0024283447 |
| Uniform 256-QAM | 0.0283149802 | 0.8598511065 | 0.0183276105 | 0.0204938888 | 0.0212404686 | -0.0017712742 |
| Uniform 256-QAM | 0.0366739269 | 0.8598511065 | 0.0183276105 | 0.0263584167 | 0.0270028212 | -0.0019623254 |
| Uniform 256-QAM | 0.0661599338 | 0.8598511065 | 0.0183276105 | 0.0465292321 | 0.0464771842 | -0.0022744137 |
| MB baseline (nu=0.1) | 0.0073339133 | 0.8604145894 | 0.0166204376 | 0.0050723608 | 0.0058847456 | -0.0010660028 |
| MB baseline (nu=0.1) | 0.0139002975 | 0.8604145894 | 0.0166204376 | 0.0100016971 | 0.0107346028 | -0.0012329906 |
| MB baseline (nu=0.1) | 0.0182687660 | 0.8604145894 | 0.0166204376 | 0.0123961914 | 0.0138670549 | -0.0020906731 |
| MB baseline (nu=0.1) | 0.0221817634 | 0.8604145894 | 0.0166204376 | 0.0152629688 | 0.0166256285 | -0.0021258081 |
| MB baseline (nu=0.1) | 0.0283149802 | 0.8604145894 | 0.0166204376 | 0.0204351815 | 0.0208756603 | -0.0014622378 |
| MB baseline (nu=0.1) | 0.0366739269 | 0.8604145894 | 0.0166204376 | 0.0263358518 | 0.0265479331 | -0.0015288739 |
| MB baseline (nu=0.1) | 0.0661599338 | 0.8604145894 | 0.0166204376 | 0.0465480905 | 0.0457269176 | -0.0015062316 |
| Full PS+GS+V_A | 0.0073339133 | 0.8569681709 | 0.0195728042 | 0.0052708665 | 0.0060569807 | -0.0010496576 |
| Full PS+GS+V_A | 0.0139002975 | 0.8570177504 | 0.0194207731 | 0.0099857211 | 0.0110156296 | -0.0015291945 |
| Full PS+GS+V_A | 0.0182687660 | 0.8570389360 | 0.0193559736 | 0.0122800652 | 0.0142122761 | -0.0025462142 |
| Full PS+GS+V_A | 0.0221817634 | 0.8570539635 | 0.0193100318 | 0.0152059496 | 0.0170246365 | -0.0025789844 |
| Full PS+GS+V_A | 0.0283149802 | 0.8570729815 | 0.0192518790 | 0.0204215089 | 0.0213535461 | -0.0019531126 |
| Full PS+GS+V_A | 0.0366739269 | 0.8570933310 | 0.0191895955 | 0.0259821014 | 0.0271252090 | -0.0024422127 |
| Full PS+GS+V_A | 0.0661599338 | 0.8571397813 | 0.0190471773 | 0.0465427788 | 0.0466090866 | -0.0023934467 |

All eight AP jobs (MB plus seven Full anchors) converged at the 800/900-digit
ladder. Uniform uses the already validated exact reference row.

# 10. Exact-vs-surrogate security comparison

For the 21 Uniform/MB/Full anchor rows, the surrogate was passed through the
existing full-Z chain only for comparison. The maximum relative errors were
C `6.16e-9`, w `2.16e-6`, and K `2.18e-6`; maximum absolute K error was
`5.22e-9`. All 21 per-anchor method orderings were rank-consistent. These are
validation results for search usefulness, not permission to report surrogate
security.

# 11. Main figure 1

K versus T, with exact AP/full-Z anchor markers, outage K=0 behavior, and
guide-to-eye connections:

`figures/analysis/figure_1_statewise_k_vs_t.svg`

# 12. Main figure 2

Learned V_A versus representative T for V_A-only, PS+V_A, and Full, with
V_min/V_max guides. The nearly flat curves reflect the short-run policy
outputs, not a certified power-allocation claim:

`figures/analysis/figure_2_learned_va_vs_t.svg`

# 13. Main figure 3

PS adaptation is shown as learned PMF entropy H(p) versus T:

`figures/analysis/figure_3_ps_entropy_vs_t.svg`

# 14. Main figure 4

Poor, median, and good active-state Full constellation snapshots use marker
area for probability:

`figures/analysis/figure_4_full_constellation_snapshots.svg`

# 15. Summary method comparison

The six-method weighted values below are `OPTIMIZATION/ANALYSIS ESTIMATE`
values from the representative grid and smooth search proxy. The separate
exact-bin estimate uses seven exact active anchors and outage mass:

| method | weighted search-proxy raw K | exact-bin raw K |
|---|---:|---:|
| Uniform | -0.0273018358 | -0.0014059125 |
| MB baseline (nu=0.1) | -0.0273036361 | -0.0011516261 |
| PS | -0.0271853995 | not evaluated as exact-bin |
| V_A | -0.0272046117 | not evaluated as exact-bin |
| PS+V_A | -0.0268954244 | not evaluated as exact-bin |
| Full PS+GS+V_A | -0.0271286791 | -0.0015155352 |

`figures/analysis/figure_5_weighted_method_summary.svg` visualizes only the
search-proxy column. The exact-bin values are separate evidence.

# 16. Scientific interpretation

1. Full beats Uniform at only the lowest exact active anchor by a small amount;
   it is worse at the other six anchors.
2. Full beats MB only at the lowest anchor, by approximately `1.63e-5`
   bits/use; it is worse at the remaining anchors and in the exact-bin
   estimate.
3. The only positive region is the poorest active T anchor; there is no broad
   T-region gain.
4. Adaptive V_A changes the learned value by less than about 1.3% and does
   not produce an exact-security improvement.
5. PS does change with T: PS entropy rises from about 7.746 to 7.840 bits
   across the four T groups, but the effect is modest.
6. GS learns a nontrivial but very small deformation: approximately 0.58%
   relative prototype RMS displacement from QAM.
7. The short-run search-proxy gains are driven mainly by PS and PS+V_A
   interaction; the Full combination does not transfer that advantage to
   exact full-Z anchors.
8. Yes. Every reported active exact statewise raw K is negative.
9. AoA outage is substantial at 26.8%, but it is not the main cause of the
   negative conclusion because outage contributes exactly zero; active-state
   K is already negative.
10. No. The observed Full result is not large or consistent enough to justify
    continuing directly to publication-scale certification.

# 17. Is the novelty numerically supported?

MIXED_PRELIMINARY_SUPPORT

# 18. Figure status

ANALYSIS_FIGURES_READY

# 19. Publication status

NOT_PUBLICATION_CERTIFIED

# 20. Main remaining blocker to true final publication run

Full PS+GS+V_A shows no meaningful exact full-Z raw-K improvement over the
simple MB baseline in this phase-disabled analysis scenario.

# 21. Recommended next task

Investigate the Full-vs-MB optimization mismatch: validate the smooth search
proxy and policy parameterization against exact anchor behavior, with special
attention to why PS+V_A improves the proxy while Full does not transfer that
gain to exact full-Z security. Do not execute a publication-scale run until
that issue is resolved.
