# Experiment plan for the frozen adaptive DM-CV-QKD model

Status: **preregistered design; no experiments have been run by this task**.
The original first-run peak wording below is historical and is superseded by
the author-approved common 30-photon domain in
`AMPLITUDE_DOMAIN_DECISION.md`, `NUMERICAL_PARAMETER_FREEZE.md`, and
`configs/default.yaml`. This plan evaluates the model in
`FINAL_MODEL_SPEC.md`; the experiment code must implement that specification
before any publication-scale training begins.

## 1. Claims and decision questions

The study is organized around four questions. Each answer must use held-out channel states, paired evaluation randomness, uncertainty across independent training seeds, and the common energy/security rules below.

### Q1. Does channel-adaptive PS outperform fixed or tuned shaping?

Primary contrasts at fixed channel-independent \(V_A\) and square geometry:

- Adaptive PS versus Uniform;
- Adaptive PS versus Binomial;
- Adaptive PS versus fixed MB;
- Adaptive PS versus globally optimized MB.

The optimized MB comparison is essential: its one global \(\nu\) and fixed \(V_A\) are selected on validation data, not the test set. A positive paired held-out raw-SKR difference over the best fixed comparator is evidence for adaptive PS.

### Q2. Does adaptive variance add SKR beyond the matched nonadaptive model?

Primary incremental contrasts:

- Adaptive VA-only versus Uniform;
- PS + adaptive VA versus Adaptive PS;
- GS + adaptive VA versus GS-only;
- Full versus PS + GS.

Every pair shares its PMF/geometry class and differs only in whether \(V_A\) is state-conditioned. Fixed-variance members receive validation optimization under the same average photon budget.

### Q3. Does one global GS add gain beyond adaptive PS and variance?

Primary incremental contrasts:

- GS-only versus Uniform;
- PS + GS versus Adaptive PS;
- GS + adaptive VA versus Adaptive VA-only;
- Full versus PS + adaptive VA.

Any gain is attributed to one channel-independent learned relative geometry, not adaptive GS.

### Q4. Does the frozen policy respond logically to \((T,\epsilon)\)?

Report the learned response surface, not just average SKR:

\[
V_A^*(T,\epsilon),
\qquad
H(P(T,\epsilon))=-\sum_i p_i(T,\epsilon)\log_2p_i(T,\epsilon),
\]

plus representative 256-entry PMFs for preregistered bad, medium, and good states. Also report distances and sensitivities between policies. "Adaptive" is supported only if these outputs change reproducibly with channel state; the expected direction is a hypothesis, not a pass condition that may be imposed after seeing results.

## 2. Models and baselines

All modes use the same 256 labels, fourfold rotational orbit construction, scalar physical normalization, MI estimator, Holevo/security settings, channel samples, and energy convention.

| Label | PMF | Geometry | \(V_A\) | Trainable model parameters |
|---|---|---|---|---|
| Uniform | \(1/256\) | square | validation-selected fixed scalar | none |
| Binomial | fixed product-binomial | square | validation-selected fixed scalar | none |
| Fixed MB | preregistered \(\nu\) | square | validation-selected fixed scalar | none |
| Optimized MB | validation-selected global \(\nu\) | square | validation-selected fixed scalar | none; scalar validation search only |
| Adaptive PS | \(p_\theta(s)\) | square | validation-selected fixed scalar | \(\theta\) |
| GS | uniform | global \(x_\psi\) | validation-selected fixed scalar | \(\psi\) |
| Adaptive VA | uniform | square | \(V_{A,\phi}(s)\) | \(\phi\) |
| PS + GS | \(p_\theta(s)\) | global \(x_\psi\) | validation-selected fixed scalar | \(\theta,\psi\) |
| PS + VA | \(p_\theta(s)\) | square | \(V_{A,\phi}(s)\) | \(\theta,\phi\) |
| GS + VA | uniform | global \(x_\psi\) | \(V_{A,\phi}(s)\) | \(\psi,\phi\) |
| Full | \(p_\theta(s)\) | global \(x_\psi\) | \(V_{A,\phi}(s)\) | \(\theta,\psi,\phi\) |

"Fixed" always means channel-independent. Hyperparameter selection is performed once on validation data and is frozen before test evaluation. The fixed-MB \(\nu\) must be declared before the main comparison; optimized MB must use a documented validation grid or scalar optimizer and convergence rule.

## 3. Data and split discipline

1. Define one joint target distribution \(\mathcal D(T,\epsilon)\). It must genuinely vary both \(T\) and \(\epsilon\) before making a two-variable adaptivity claim.
2. Generate disjoint train, validation, and test channel-state realizations with namespaced seeds. Never recycle validation/test states into stochastic training batches.
3. Generate disjoint AWGN/MI random streams for training, validation, and testing. For each held-out comparison, use common random numbers across all methods so paired differences do not include avoidable Monte Carlo noise.
4. Train each learned mode from multiple independent initialization/training seeds. Freeze the selected checkpoint using a validation-only rule declared before test evaluation.
5. Preserve all state weights. The expected-SKR objective and average-energy constraint must use the same target distribution.
6. Save the complete resolved configuration, code revision, seed namespace, checkpoint hash, and train/validation/test state hashes with every result.

If robustness to distribution shift is studied later, define it as a separate secondary test; it must not replace the in-distribution held-out test.

## 4. Common fairness contract

Every method uses:

- the same \(V_{\min}\) and \(V_{\max}\);
- the same average photon budget \(\mathbb E[V_A]/2\le\bar n_{\rm budget}\);
- the same \(\beta\), ideal detector model, excess-noise convention, and accepted asymptotic Holevo chain;
- the same Fock cutoff policy and convergence tolerance;
- the same MI estimator and evaluation sample budget;
- the same train/validation/test channel distributions and evaluation state weights;
- matched optimization budgets for learned modes, with wall-clock and update counts both reported;
- no test-set tuning.

For each fixed-PMF/fixed-geometry comparator, tune its one scalar \(V_A\) on validation data subject to the common budget. For optimized MB, jointly select the global \((\nu,V_A)\) on validation. Adaptive policies must satisfy the same budget on validation and test. Report both achieved average photon number and any residual constraint violation; do not compare an over-budget policy as if it were feasible.

Historical first-run wording: no hard peak-amplitude limit was imposed. The
current author-approved protocol instead applies the common hard
`max_i |alpha_i|^2 <= 30` photon rule to every eligible realized ensemble,
without clipping, while still requiring \(A_{\max}\), PAPR, and amplitude-tail
diagnostics.

## 5. Training protocol

For a minibatch of channel states, each learned mode minimizes

\[
\mathcal L_{\rm SKR}=-\frac1B\sum_n
[\beta I_{AB,n}-\chi_{BE,n}],
\]

using the same statewise physical ensemble in both terms. Do not apply statewise zero clipping in the loss. Enforce the common average-energy inequality with the projected dual procedure specified in `FINAL_MODEL_SPEC.md` for adaptive-variance modes.

The primary run uses \(\lambda_{\rm sep}=\lambda_{\rm peak}=\lambda_{\rm drift}=0\). Monitor minimum relative distance, peak amplitude/PAPR, and geometry drift. A regularized rerun is allowed only when its trigger, coefficient, threshold, and selection data are recorded; it is not silently substituted for the primary model.

Use a common maximum update budget and validation cadence. Report optimizer, learning rates by parameter group, batch size, gradient clipping if any, stopping rule, number of attempted/completed seeds, and failed-run criteria. Do not discard failed seeds without accounting for them.

## 6. Required correctness gates before long training

Run these gates on every mode and representative bad/medium/good states:

1. PMF positivity, unit sum, and orbit equality.
2. Zero weighted mean and pseudo-second moment: \(\sum p_i\alpha_i=0\), \(\sum p_i\alpha_i^2=0\).
3. Exact declared energy: \(2\sum p_i|\alpha_i|^2=V_A\).
4. Equal I/Q variance and zero I/Q covariance.
5. Byte/value-equivalent ensemble inputs at the MI and Holevo boundaries.
6. Physical covariance and symplectic eigenvalues without silent capping or repair.
7. Nonzero finite-difference and autograd paths for every enabled parameter group; absent gradients for every frozen group.
8. MI convergence versus AWGN sample count.
9. Density-matrix trace/eigenvalue and Holevo convergence versus Fock cutoff, including the largest observed amplitude.
10. Limiting cases: uniform logits recover Uniform; \(\nu=0\) recovers Uniform MB; disabling each head recovers its matched ablation; identical channel inputs give identical frozen-policy outputs.

Publication-scale training does not start until these gates pass.

## 7. Evaluation metrics

### 7.1 Primary performance

- held-out raw average SKR \(\overline K_{\rm raw}=\mathbb E[K^{\rm raw}]\);
- paired per-state and per-seed raw-SKR differences for every primary contrast;
- uncertainty intervals across independent training seeds and held-out states, with the resampling unit stated;
- aggregate-clipped rate \([\overline K_{\rm raw}]_+\) as a secondary physical summary;
- state-selective \(\mathbb E[[K^{\rm raw}]_+]\) only as an explicitly labeled oracle diagnostic.

### 7.2 Mechanism decomposition

- \(I_{AB}\) and \(\chi_{BE}\), reported separately as well as through SKR;
- \(V_A(T,\epsilon)\) and \(\bar n(T,\epsilon)=V_A/2\);
- PMF entropy \(H(P(T,\epsilon))\);
- orbit masses \(q_k(T,\epsilon)\), full 256-entry PMFs, and PMF heat maps on square labels;
- global relative-geometry plot, minimum pair distance, and drift from square QAM;
- \(A_{\max}(T,\epsilon)\), PAPR, and upper quantiles of physical symbol energy;
- average-energy budget slack or violation.

### 7.3 Adaptivity measures

For state pairs \(s_a,s_b\), report

\[
D_{\rm TV}(P_a,P_b)=\frac12\sum_i|p_i(s_a)-p_i(s_b)|,
\]

and a numerically safe symmetric divergence such as Jensen--Shannon divergence. Report finite-difference response magnitudes of \(V_A\) and PMF entropy along both \(\log_{10}T\) and \(\epsilon\). Jacobian norms of the 64 orbit masses may be reported as a compact sensitivity map. Avoid using KL divergence alone when probabilities approach numerical precision.

## 8. Bad, medium, and good state evidence

Select representative states before inspecting learned outputs. Use fixed quantiles of a preregistered channel-quality score on the validation distribution, then map those quantile definitions unchanged to the test set. The score and tie-breaking rule must be recorded. A suitable score is the Uniform-baseline raw SKR or, if avoiding outcome-based selection, the joint empirical quantiles of high/median/low \(T\) and \(\epsilon\).

For each bad, medium, and good state, publish:

- the exact \((T,\epsilon)\);
- \(V_A^*(T,\epsilon)\);
- \(H(P(T,\epsilon))\);
- the 16-by-16 label heat map and numerical 256-entry PMF artifact;
- the physical constellation with probability encoded visually;
- \(I_{AB}\), \(\chi_{BE}\), raw SKR, \(A_{\max}\), and PAPR.

In addition, show two controlled sweeps: vary \(T\) at fixed \(\epsilon\), and vary \(\epsilon\) at fixed \(T\). This distinguishes genuine two-input response from correlation in the sampled channel distribution. Do not describe a visually plausible direction as optimal without the SKR contrast that supports it.

## 9. Analysis of the four questions

Use paired held-out differences. For every contrast report the mean/median effect, uncertainty interval, seed-level distribution, and energy-budget equality. Do not declare success from a single best seed.

- **Q1 succeeds** only if Adaptive PS exceeds the best validation-tuned fixed shaping baseline on held-out raw average SKR and the gain is robust across seeds.
- **Q2 succeeds** only if adaptive-VA members improve their directly matched fixed-VA counterparts under the same achieved average photon budget.
- **Q3 succeeds** only if adding global GS improves each declared matched comparison without obtaining the gain from extra energy or invalid covariance states.
- **Q4 succeeds** only if \(V_A\) and/or PMF outputs show reproducible, nontrivial state dependence on controlled \(T\) and \(\epsilon\) sweeps. If outputs collapse to constants, report that honestly even if Full performs well.

Correct multiplicity for the set of headline contrasts or state clearly that intervals are simultaneous/exploratory. Include effect sizes; a small statistically resolved gain may still be practically negligible because of computational or implementation cost.

## 10. Planned tables and figures

1. **Model/fairness table:** parameters, adaptive components, achieved photon budget, peak diagnostics, training cost.
2. **Primary SKR table:** raw average SKR, \(I_{AB}\), \(\chi_{BE}\), uncertainty, and paired deltas for all 11 baselines/ablations.
3. **SKR versus channel figure:** per-state rates and binned summaries versus \(T\) and \(\epsilon\).
4. **Variance surface:** \(V_A^*(T,\epsilon)\) with budget summary.
5. **Entropy surface:** \(H(P(T,\epsilon))\).
6. **Representative policies:** PMFs and physical constellations for preregistered bad/medium/good states.
7. **Global GS figure:** learned relative geometry versus square QAM, clearly labeled channel-independent.
8. **Numerical-convergence appendix:** MI samples, Fock cutoff/trace error, covariance checks, and gradient/finite-difference checks.

## 11. Reproducibility artifacts

Release or archive, for every reported run:

- resolved configuration and all still-unfrozen numerical choices;
- source revision and environment lock;
- train/validation/test channel-state hashes and seed derivation;
- optimizer state, selected checkpoint, and selection criterion;
- raw per-state \(T,\epsilon,V_A,I_{AB},\chi_{BE},K^{\rm raw}\);
- 256-entry PMFs or sufficient frozen checkpoints/code to reproduce them;
- geometry coordinates, amplitude diagnostics, constraint diagnostics, and convergence traces;
- failed-run logs and the complete seed inventory.

## 12. Decisions required before execution

Before running the plan, freeze the numerical values/rules for \(V_{\min}\), \(V_{\max}\), \(V_{A,\rm budget}\), \(\beta\), the joint \((T,\epsilon)\) distributions and split sizes, optical/channel parameters, Fock cutoffs/tolerances, MI sample budgets, optimizer schedules, number of training seeds, stopping/checkpoint rule, uncertainty procedure, fixed-MB \(\nu\), and optimized-MB search bounds. If a geometry or peak regularizer becomes necessary, preregister its trigger and selection procedure in a plan amendment before examining test performance.
