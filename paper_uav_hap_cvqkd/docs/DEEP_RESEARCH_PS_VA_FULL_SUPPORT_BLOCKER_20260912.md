# Deep research: the remaining PS+V_A full-support source-moment blocker

## Executive decision

The selected next category is:

**INVESTIGATE_AP_WORKER_BUG**

The current evidence does not justify adding a probability floor, reducing the PS parameterization, changing the source-moment equations, or escalating AP precision alone. The optimized PS+V_A checkpoint has comfortably positive, moderately shaped probabilities, finite logits with a small dynamic range, and unique C4 coherent states. Those facts make true probability-support loss and softmax underflow poor explanations for the failed exact gate.

The high-precision worker failure is nevertheless real: the PS+V_A jobs at 800 and 900 decimal digits returned FAIL_CLOSED, while the matched Full jobs converged at the same ladder. That asymmetry must be decomposed with an independent worker/solver check before changing the scientific model family.

This report is a numerical and mathematical investigation, not a security result. It does not revisit the repaired full-Z objective, attempt reverse gradients, run training, access final data, or authorize publication-scale evaluation. The project remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and NOT_READY_FOR_ADAPTIVE_TRAINING.

## 1. Question and evidence boundary

The narrow question is why the repaired analysis search produced a promising PS+V_A candidate whose exact arbitrary-precision source-moment evaluation does not pass the current full-support gate, whereas the Full PS+GS+V_A candidate does. The relevant object is the source state

\[
  \tau=\sum_{i=1}^{256}p_i\,|\alpha_i\rangle\langle\alpha_i|,
\]

followed by the source moments C,w used to form the admissible correlation interval. This is distinct from the already repaired search functional. The old off-interval tanh proxy is superseded and is not reconsidered here.

The repository evidence is authoritative. The main records are:

| Record | What it establishes | Status |
|---|---|---|
| [repaired_full_z_ps_va_exact_failure_20260911.json](../results/repaired_full_z_ps_va_exact_failure_20260911.json) | PS+V_A failed closed at 800/900 digits on poor/median/good; the 100/150/200-digit diagnostic ranks were below 256 | FAIL_CLOSED, no PS exact K inferred |
| [repaired_full_z_exact_jobs_20260911.json](../results/repaired_full_z_exact_jobs_20260911.json) | Full exact source rows converged at 800/900 digits on all three anchors | exploratory exact-anchor pass |
| [repaired_full_z_objective_analysis_20260911.json](../results/repaired_full_z_objective_analysis_20260911.json) | The repaired bounded search and 50-step PS+V_A/Full analyses | analysis-only |
| [ps_va_full_support_blocker_diagnostic_20260912.json](../results/ps_va_full_support_blocker_diagnostic_20260912.json) | Read-only PMF, geometry, MB-reference, and matched 300-digit diagnostic audit | diagnostic-only |
| [REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md](REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md) | Current objective-repair boundary and lifecycle consequences | active project record |

The PS failure artifact deliberately does not retain the unresolved 800/900 rows. Therefore it is not valid to say that the PS jobs failed because a particular high-precision eigenvalue had a particular sign, or because a specific timeout was reached. The only supported statement is that the corrected worker returned FAIL_CLOSED and no converged C,w was available.

## 2. What the current numerical record actually says

The corrected AP worker was run with a 100/150/200-digit diagnostic ladder and an 800/900-digit high-precision attempt. The required support rank is 256.

| Anchor | PS+V_A ranks at 100/150/200 | PS high ladder | Full ranks at 800/900 | Full minimum eigenvalue |
|---|---:|---|---:|---:|
| poor | 162 / 174 / 188 | FAIL_CLOSED | 256 / 256 | 3.491668191357...e-611 |
| median | 162 / 176 / 188 | FAIL_CLOSED | 256 / 256 | 1.019549481343...e-612 |
| good | 165 / 176 / 187 | FAIL_CLOSED | 256 / 256 | 4.741890194197...e-614 |

The Full rows are stable between 800 and 900 digits and supply converged source moments. For example, the median Full row gives

\[
 C=0.8594238956711868981\ldots,\qquad
 w=0.0130447814829580745\ldots .
\]

The three available Full exact raw-key values exceed the fixed MB values by +0.0003151158, +0.0007920275, and +0.0009190632 on poor, median, and good respectively. This is useful exploratory evidence, but it is not a PS+V_A comparison because the latter has no exact K at those states.

The read-only audit found the following binary64 quantities at the same anchors:

| Method/state | q_min | q_max | q_max/q_min | p_min=q_min/4 | logit range | relative energy | scale s | min physical pair distance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PS+V_A / poor | 0.00652427 | 0.02935582 | 4.4995 | 0.00163107 | 1.50396 | 0.79937 | 0.78905 | 0.12103 |
| PS+V_A / median | 0.00789890 | 0.02686411 | 3.40099 | 0.00197472 | 1.22407 | 0.83151 | 0.77365 | 0.11867 |
| PS+V_A / good | 0.00912075 | 0.02426922 | 2.66088 | 0.00228019 | 0.97866 | 0.86208 | 0.75981 | 0.11655 |
| Full / poor | 0.01222640 | 0.01943780 | 1.5898 | 0.00305660 | 0.46362 | 0.92878 | 0.73234 | 0.10619 |
| Full / median | 0.01284053 | 0.01872467 | 1.45825 | 0.00321013 | 0.37724 | 0.94161 | 0.72734 | 0.10547 |
| Full / good | 0.01336257 | 0.01809034 | 1.35381 | 0.00334064 | — | — | 0.72302 | 0.10484 |

The Full geometry has an RMS GS displacement of about 0.0058345 in the recorded comparison. The PS physical states actually have a larger minimum pair separation and a slightly larger modulation scale than the matched Full states. Thus “PS has collapsed because its V_A is much smaller” is not consistent with the observed anchor diagnostics.

As a reference, the canonical repository MB PMF gives:

| MB parameter nu | symbol p_min | orbit q_min | q_max/q_min |
|---:|---:|---:|---:|
| 0.0 | 0.00390625 | 0.0156250 | 1.0000 |
| 0.1 (fixed reference) | 0.00330657695 | 0.0132263078 | 1.3015 |
| 0.3 (optimized domain edge) | 0.00234239297 | 0.00936957189 | 2.2047 |

The failed PS probabilities are not more concentrated than the repository’s declared MB search domain by orders of magnitude. This does not prove that the PS weighted Gram is well-conditioned—the coherent-state geometry can dominate—but it rules out the simplest PMF-collapse narrative.

## 3. Weighted Gram structure and support theory

Let G be the unweighted coherent-state Gram matrix,

\[
 G_{ij}=\langle\alpha_i|\alpha_j\rangle
 =\exp\!\left[-\frac{|\alpha_i|^2+|\alpha_j|^2}{2}
              +\alpha_i^*\alpha_j\right],
\]

and let \(P=\operatorname{diag}(p_1,\ldots,p_{256})\). If

\[
 A e_i=\sqrt{p_i}\,|\alpha_i\rangle,
\]

then

\[
 \tau=AA^\dagger,\qquad
 W=A^\dagger A=P^{1/2}GP^{1/2}.
\]

The nonzero spectra of \(\tau\) and W coincide. The C4 construction in the repository is an exact block reduction of this same weighted Gram, not a Fock cutoff approximation: four 64-by-64 symmetry sectors account for the 256 state-space modes.

For a finite set of distinct single-mode coherent states, the states are linearly independent. This is a standard coherent-state fact, and it also has a short proof here. The coherent-state literature states the same finite-set linear-independence result.[^13] Form the first 256 Fock coefficients

\[
 F_{ni}=e^{-|\alpha_i|^2/2}\frac{\alpha_i^n}{\sqrt{n!}},
 \qquad 0\le n<256.
\]

Their determinant is, up to a unit-modulus sign,

\[
 \det F=
 \frac{e^{-\frac12\sum_i|\alpha_i|^2}}
      {\sqrt{\prod_{n=0}^{255}n!}}
 \prod_{i<j}(\alpha_j-\alpha_i).
\]

It is nonzero when the amplitudes are distinct. Since the full Gram is \(F^\dagger F+\) a positive semidefinite Fock tail, it is positive definite. Consequently:

* if every p_i>0, the mathematical rank is 256;
* if a probability is exactly zero, the zero-probability state should be removed from the support before applying the inverse;
* a positive but tiny probability preserves mathematical rank while making accurate inverse-square-root calculations difficult.

The source-moment theory used by this project follows the latter support interpretation: the inverse of \(\tau\) is a Moore–Penrose inverse on the support, with zero action outside the support. It does not require the nominal alphabet to remain a 256-dimensional support when a probability is exactly zero.[^1] The current implementation’s strict positive 256-state gate is therefore an implementation contract, not a theorem that forbids support-aware evaluation.

This distinction is central. “The source has full mathematical support” and “the current AP eigensolver has resolved every inverse-sensitive mode” are different propositions. The repository has evidence for the former from its finite positive PMFs and unique C4 states, but not an exact PS AP pass for the latter.

## 4. How much can q_min explain?

For any positive-definite G, the Rayleigh quotient gives

\[
 \lambda_{\min}(P^{1/2}GP^{1/2})
 \ge p_{\min}\lambda_{\min}(G),
\]

and similarly

\[
 \lambda_{\max}(P^{1/2}GP^{1/2})
 \le p_{\max}\lambda_{\max}(G),
 \qquad
 \kappa(W)\le\frac{p_{\max}}{p_{\min}}\kappa(G).
\]

These are eigenvalue bounds for the same geometry. They must not be read as a Loewner statement \(W\succeq p_{\min}G\), which is not generally valid for a noncommuting diagonal scaling.

Under C4, \(p_{\min}=q_{\min}/4\). Relative to a uniform orbit distribution, whose per-symbol probability is \(1/256\), the lower-bound multiplier is

\[
 \frac{q_{\min}/4}{1/256}=64q_{\min}.
\]

For the current PS anchors that multiplier is approximately 0.418, 0.506, and 0.584 from poor to good. It is a loss of less than one decimal digit in this particular lower-bound comparison, not a 100- or 300-digit effect. The current PS q_max/q_min ratios are also only 2.66–4.50.

For scale, the following table shows what would be required if geometry were held fixed and only the rarest orbit mass changed:

| q_min | multiplier versus uniform 64 q_min | decimal penalty in this bound |
|---:|---:|---:|
| 1e-6 | 6.4e-5 | 4.19 digits |
| 1e-8 | 6.4e-7 | 6.19 digits |
| 1e-10 | 6.4e-9 | 8.19 digits |
| 1e-12 | 6.4e-11 | 10.19 digits |

Even if a same-geometry uniform eigenvalue were around 1e-618, driving this particular bound below 1e-1000 would require an orbit mass on the order of 1e-384 or smaller. The actual eigenvalue can be smaller than the lower bound because of geometry, so this is not a proof of conditioning; it is a strong scale check against blaming the observed 10^-3 probabilities.

The conclusion is conditional but useful: a probability floor could help a future candidate whose q_min is genuinely microscopic, but adding a floor now would be changing the model before the present candidate has been shown to fail for that reason.

## 5. Softmax, entropy, and probability parameterization

The frozen PS network is

    Linear(2,128) -> ReLU -> Linear(128,64) -> torch.softmax

and the 64 orbit masses are expanded to 256 symbol probabilities by p=q/4. PyTorch documents softmax as normalized exponentiation and recommends log_softmax when the log-domain result is what is needed for better numerical properties.[^2]

For finite logits, the mathematical softmax is strictly positive. In finite binary64 arithmetic it can become exactly zero only when a relative logit gap is so large that exponentiation underflows. The observed anchor ranges are below 1.51, so this mechanism is not active: all relative exponentials are ordinary, well-resolved numbers. The repository’s global step-50 PS diagnostic also reports a minimum symbol probability of approximately 0.00178737, not zero.

A parameter-independent pointwise guarantee can be obtained by bounding the centered logits. If there are 64 orbit logits and each centered logit lies in [-L,L], then

\[
 q_{\min}\ge\frac{e^{-L}}{e^{-L}+63e^L}
 =\frac{1}{1+63e^{2L}}.
\]

| L | guaranteed q_min |
|---:|---:|
| 1 | 2.14e-3 |
| 2 | 2.91e-4 |
| 3 | 3.93e-5 |
| 4 | 5.32e-6 |
| 5 | 7.21e-7 |
| 6 | 9.75e-8 |
| 7 | 1.32e-8 |
| 8 | 1.79e-9 |

This is a defensible future guard if an author wants a declared compact PS family. It must bound logit differences or use a centered parameterization; bounding raw logits without fixing the common additive gauge is needlessly restrictive. A mixture floor

\[
 q=(1-\delta)\operatorname{softmax}(\ell)+\delta/64
\]

also guarantees \(q_{\min}\ge\delta/64\), but it changes every PMF, therefore changes E_q, the physical scale, MI, and source moments. It is a model amendment, not a transparent numerical patch.

An entropy floor is not an adequate support certificate. A distribution can put an arbitrarily small mass on one orbit while keeping the remaining 63 orbits sufficiently spread to retain high entropy. Entropy can be used as a regularizer or a diagnostic, but a publication gate requiring positive support needs a direct pointwise bound or a support-aware source calculation.

## 6. V_A, scale, and geometric conditioning

The physical amplitudes are formed as

\[
 \alpha_i=s z_i,\qquad
 s=\sqrt{\frac{V_A}{2E_q}},\qquad
 E_q=\sum_k q_k|z_k|^2.
\]

At fixed normalized geometry, lowering V_A brings the coherent states closer to the origin. The Vandermonde expression above makes the mechanism explicit: if every amplitude is scaled by c, the squared determinant of the first 256 Fock rows changes by

\[
 |c|^{256\cdot255}.
\]

Because c is proportional to \(\sqrt{V_A}\) when E_q is fixed, the corresponding Gram-determinant factor is

\[
 V_A^{256\cdot255/2}.
\]

This is a determinant factor, not an exact formula for \(\lambda_{\min}\). It demonstrates why a tiny scale change can matter when the constellation is already close to singular. It also shows why the probability-dependent denominator E_q and geometry must be analyzed together with V_A.

The present anchors do not support V_A as the primary cause. PS+V_A has V_A near 0.995 in the repaired step-50 summary, while Full is near 0.996; the anchor scales are slightly larger for PS. The Full construction has a small GS displacement and more uniform PMF. Those changes can alter a near-null mode through the Gram geometry, and a small perturbation can lift a tiny eigenvalue by many orders. Weyl’s inequality only gives the absolute bound

\[
 |\lambda_j(G+\Delta G)-\lambda_j(G)|\le\|\Delta G\|_2,
\]

so an RMS displacement alone cannot quantify a relative change when the baseline eigenvalue is around 10^-600.[^3] The causal effect is plausible, but it must be measured with matched swaps.

The minimal geometry/PMF ablation after the worker check should hold the channel state and binary64 inputs fixed and compare:

1. PS q, PS V_A, square geometry;
2. Full q, Full V_A, square geometry;
3. Full q, Full V_A, Full GS geometry;
4. PS q, Full V_A, square geometry.

If needed, the fifth row is PS q, Full V_A, Full GS geometry. The purpose is not to optimize; it is to identify whether the success is driven by PMF, scale, or GS geometry. No row should be converted into a security result unless it passes the same exact convergence gate.

## 7. Serialization audit: A/B/C alternatives

The current transfer path is already unusually favorable for reproducibility. run_analysis_figures.py extracts the per-symbol representative probability and physical prototype, and the AP worker receives their binary64 components as float.hex() strings. Python documents float.hex()/float.fromhex() as an exact hexadecimal representation and round trip for a binary floating-point value.[^4] The mpmath documentation likewise states that conversion from a Python float is lossless; the resulting value is the exact binary64 number, not a newly rounded decimal approximation.[^5]

Three possible policies are worth distinguishing:

| Policy | What is sent | Scientific meaning | Assessment |
|---|---|---|---|
| A. Direct physical inputs | binary64 q/p and physical z/alpha as hex | AP evaluates the exact frozen binary64 ensemble produced by PyTorch | preferred authoritative path |
| B. Logits and reconstruction | binary64 logits as hex; AP recomputes softmax | AP evaluates the real-logit softmax at arbitrary precision, which may differ from the checkpoint’s binary64 PMF | useful audit only unless explicitly frozen as the model |
| C. Decimal text | decimal PMF/amplitudes with stated digits | values are parsed and rounded at the selected AP precision | less exact and more fragile than A |

Policy A is the correct current security-anchor semantics: source moments are computed for the actual checkpoint ensemble, not for an AP-recomputed variant. Policy B can be informative because it isolates softmax-rounding effects, but it must report the maximum difference between the reconstructed and direct PMFs. It must not silently replace the learned distribution. Policy C should only be used with an explicit decimal or interval model and a sufficient rounding-error budget.

The one-checkpoint replay should assert all of the following before any eigensolve:

* direct q sums to one and every entry is positive;
* expanded p equals q/4 exactly in the binary64 representation used by the worker;
* C4 probability ties and amplitude rotations hold;
* all 256 amplitudes are unique;
* hex serialization followed by AP parsing reproduces every direct input;
* if logits are also sent, the AP-recomputed softmax is reported as a separate object and is not substituted into the direct-input job.

The current evidence makes serialization a low-probability primary cause, but this A/B check is cheap compared with another multi-hour AP attempt.

## 8. Precision, eigensolver, and solve formulation

The lower ladder is consistent with a precision floor rather than a support theorem: the 100/150/200-digit PS rows resolve only 162–188 modes, while an uncached 300-digit probe on the PS median and the matched Full median each resolved 206 modes and returned a residual negative eigenvalue at roughly 10^-302. The Full median then resolved at 800/900 digits with a minimum mode around 10^-612. This is the pattern expected when finite-precision Hermitian eigensolvers report unresolved near-zero modes until the working precision exceeds the spectrum’s scale. The 300-digit diagnostic is retained as diagnostic evidence, not as an exact rank oracle.[^6]

The PS-specific 800/900 failure remains unexplained. It could mean:

* the PS weighted Gram is materially more ill-conditioned than the Full Gram;
* the worker’s C4 phase, transpose, square-root, or solve path has a nonuniform-PMF bug;
* the eigensolver takes a different convergence path for the PS spectrum;
* the job reached a practical runtime/convergence limit; or
* a combination of these effects.

The stored artifact cannot distinguish these cases. Increasing AP precision alone is therefore not the first decision. A dense arbitrary-precision eigensolve has at least cubic matrix-operation scaling in dimension, and its constant and bit-complexity costs rise with precision. The local observations are more informative than a theoretical runtime extrapolation: a 300-digit one-worker diagnostic took about 33 seconds, a Full 800/900 anchor job took about 855 seconds in its recorded batch, and each failed PS high-ladder anchor occupied about 3205 seconds. These times are not directly comparable and do not define a digit-to-time law.

A reasonable diagnostic precision budget, once the worker is independently checked, is:

| Expected minimum mode | Starting decimal-digit window | Use |
|---:|---:|---|
| 10^-900 | 1000–1100 | one-state feasibility probe |
| 10^-1100 | 1200–1300 | two-point convergence check |
| 10^-1500 | 1600–1700 | stress-only probe, likely expensive |
| 10^-1900 | 2000+ | stress-only feasibility, not a routine roster |

These windows include roughly 100 guard digits and assume that the eigensolver and subsequent inverse-sensitive solves do not consume the entire margin. They are not a reason to relax the current convergence protocol or to claim that a PS row is secure.

Replacing eigenvectors with a Cholesky, LDL, or solve-based source-moment formulation may reduce cancellation and improve runtime. It cannot make an inverse of a genuinely tiny mode insensitive to condition number. A solve-based implementation is therefore a valuable independent cross-check, not a proof that the existing PS spectrum has no small mode.

For rigorous enclosures, Arb provides arbitrary-precision real/complex ball arithmetic with propagated error bounds and matrix support.[^7] It can certify a positive pivot or a residual enclosure, but it does not make a 10^-900 mode cheap: the enclosure radius must still be smaller than the mode, or a structural certificate must replace direct spectral resolution. mpmath’s interval context is useful for experiments but is documented as experimental; it should not be treated as the first production repair.[^8]

## 9. What current literature does—and does not—resolve

The source-moment functional is grounded in the arbitrary-modulation DM-CV-QKD literature. Denys, Brown, and Leverrier formulate the source as a finite mixture of coherent states and derive an explicit asymptotic key-rate lower bound. Their treatment highlights the numerical difficulty of larger QAM and argues that relatively small constellations can already approach Gaussian modulation performance.[^1] The support-restricted inverse used in that theory is compatible with dropping exactly zero-probability states, but it does not provide a shortcut for accurately inverting an almost-singular full-support weighted Gram.

PAS work is relevant but uses a different level of numerical and security generality. Notarnicola et al. use Maxwell–Boltzmann-style shaping for finite QAM and analyze a wiretap/pure-loss setting with homodyne detection; that is useful evidence for the physical motivation of shaping, not a validation of an arbitrary learned 256-point PMF in the present source-moment worker.[^9] A 2026 PAS-QAM study likewise evaluates MB-shaped finite constellations under a linear channel and asymptotic collective-attack assumptions, while noting that large-constellation SDP methods are numerically intensive.[^10]

There are experimental demonstrations of probabilistically shaped 256-QAM CV-QKD, but experimental high-order QAM feasibility does not establish an arbitrary-precision support certificate for a learned nonuniform density operator.[^11] Conversely, recent finite-size security work has made important progress for discrete modulation, including four-state heterodyne protocols, but it does not solve this repository’s exact 256-state adaptive source-moment worker problem.[^12]

The current literature therefore supports the following narrow conclusion: the blocker is a numerical-certification and implementation gap at the intersection of high-order coherent-state geometry, nonuniform PMFs, and inverse-sensitive source moments. It is not evidence of a known theorem that PS must lose support, nor evidence that a probability floor is standard in DM-CV-QKD.

## 10. Hypothesis ranking

The ranking below is a decision ranking, not a posterior probability. “Primary cause” means the explanation most worth testing next given the repository measurements.

| Rank | Hypothesis | Assessment | Reason |
|---:|---|---|---|
| 1 | H5: AP worker/solver bug or PS-specific path failure | unresolved, highest priority | Full passes in the same worker family; PS has mild logits and positive PMF; the stored failure does not expose the high-ladder rows needed to distinguish bug from conditioning |
| 2 | H4: insufficient AP precision or eigensolver conditioning | likely contributor | both PS and Full fail at 300 digits; Full only resolves near 10^-612 at 800/900 |
| 3 | H6: Full GS changes conditioning | plausible, unquantified | Full’s small GS displacement can lift near-null modes, but no matched causal ablation exists |
| 4 | H2: V_A/normalization scale | low-to-medium | current PS and Full V_A values are nearly equal; PS scale and pair distances are not smaller in the anchor audit |
| 5 | H3: serialization | low | float.hex/fromhex is exact for the transferred binary64 values; still worth an A/B replay because it is inexpensive |
| 6 | H1: probability concentration / q_min | low for this checkpoint | PS q_min is 0.0065–0.0091, and the weighted-Gram bound predicts less than one decimal digit of PMF penalty versus uniform |
| 7 | H7: true mathematical support loss | very low analytically, but exact PS certification missing | finite softmax PMF plus unique coherent amplitudes imply rank 256; this remains an unverified implementation result until an independent AP path confirms it |

H5 and H4 are intentionally adjacent. The evidence says “precision and solver behavior matter,” but it does not say “the worker is correct for this nonuniform input.” The responsible next step is to test both on one fixed checkpoint rather than select a model intervention from the failure status alone.

## 11. One immediate experiment: A, narrowed to a worker decomposition

Run one read-only diagnostic on the median PS+V_A checkpoint, with the Full median checkpoint as a positive control. This is the single immediate experiment; it is not a new training run.

### Inputs

Use the checkpoint and direct physical PMF/prototype values already bound in the exact-anchor workflow. Preserve binary64 values using Policy A above. Keep the current C4 ordering, no phase, the same state, and the same worker constants.

### Measurements

1. Record q_min, q_max, p_min, logit range, E_q, scale, minimum pair distance, exact C4/uniqueness checks, and the direct-input SHA-256.
2. Replay the direct hex serialization and assert bitwise equality before the AP calculation.
3. Run the current AP worker at 300, 400, 600, 800, 1000, and 1200 decimal digits, retaining every sector rank, minimum eigenvalue, Hermitian residual, eigensolver status, C,w (when available), and wall time. The two final rows must be retained even on failure.
4. Build the four C4 sectors independently from the same direct inputs using an alternate implementation or factorization path. At minimum compare the sector matrices, traces, Hermitian residuals, and spectra against the current worker. An Arb/acb matrix path or an independently written dense weighted-Gram path is suitable; copying the worker line-for-line is not.
5. Run the same cross-check on Full median. Full is the positive control for the worker, input convention, and expected resolution scale.

### Interpretation gates

* If the independent path agrees with Full and resolves PS at a precision where the current worker fails, classify the issue as an AP worker/solver bug and fix only that implementation path before any model change.
* If both paths agree on the PS spectrum and it remains unresolved through the declared ladder, classify the issue as genuine PS conditioning; then run the matched PMF/scale/GS ablation before selecting a guard or reparameterization.
* If direct and logit-reconstructed PMFs differ materially, keep direct PMF as the checkpoint result and treat the difference as a serialization/model contract issue, not as evidence for a support floor.
* Do not calculate or report a PS exact K unless two successive precision rows resolve rank 256 and the prescribed C,w agreement test passes.

This experiment has the highest information gain because it separates a scientific conditioning problem from a worker implementation problem without altering the trained candidate or the frozen security equations.

## 12. Decision among the six allowed categories

The selected category is exactly:

**INVESTIGATE_AP_WORKER_BUG**

Why the other choices are premature:

* **INCREASE_AP_PRECISION_ONLY**: 800/900 failure is not recorded as a clean precision exhaustion, and the runtime is already large. More digits may be necessary, but the first experiment must show whether the worker is forming and solving the intended PS sectors.
* **FIX_SERIALIZATION_ONLY**: the current hex path is exact for its binary64 inputs; serialization should be replay-verified, not assumed to be the root cause.
* **ADD_FULL_SUPPORT_PS_DOMAIN_GUARD**: the observed checkpoint already has p_min around 10^-3; a new floor would change the model without explaining the failure.
* **REFORMULATE_FORWARD_SOURCE_MOMENTS**: a solve-based formulation is a good cross-check and possible performance improvement, but it cannot remove true inverse sensitivity and should not replace the production equations before validation.
* **REDUCE_PS_PARAMETERIZATION**: reducing the 64-dimensional PMF family could improve conditioning, but it changes the scientific question and is not supported by a demonstrated PS probability-collapse mechanism.

## 13. Training guard and lifecycle consequence

The experiment must not be used to reopen adaptive training. Until it passes, the following guards remain active:

* no publication-scale or adaptive training;
* no baseline selection or optimized-MB selection;
* no final-test access, held-out evaluation, or publication ranking;
* no PS+V_A exact raw K inferred from a failed worker row;
* no support threshold relaxed from the current fail-closed rule;
* no alteration to C,w, the physical Z interval, the channel, beta, phase, epsilon, outage, or raw-K convention.

If the worker issue is confirmed and repaired, rerun only the three-state exact PS+V_A/Full/MB comparison first. If genuine conditioning is confirmed, the next proposal must separately specify whether a bounded-logit family, support-aware evaluation, or a model-level parameterization amendment is intended. None is authorized by this report.

## 14. Publication implication

The current evidence supports only these statements:

1. The repaired search objective is interval-preserving and analysis-grade.
2. Full exact anchors converge at the current 800/900 ladder on three selected states and exceed MB there.
3. The optimized PS+V_A exact anchor comparison is unavailable because its source-moment worker gate failed closed.
4. No complete PS+V_A-versus-Full ranking, adaptive gain, or joint-adaptation novelty claim is supported.

It would be incorrect to write that PS lost mathematical support, that Full is scientifically superior, or that a probability floor is required. The publication claim remains CURRENT_NOVELTY_NOT_SUPPORTED.

## 15. Provenance and final status

The new diagnostic artifact is [ps_va_full_support_blocker_diagnostic_20260912.json](../results/ps_va_full_support_blocker_diagnostic_20260912.json), SHA-256:

8a44ca9330cca61d8a15d2457b6c1d8445b560b5776935e184de15e550f5255d

Its relevant input and source hashes are recorded in the JSON. The principal source hashes at this audit are:

| File | SHA-256 |
|---|---|
| scripts/full_support_c4_worker.py | 2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1 |
| scripts/run_analysis_figures.py | 9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f |
| src/modulation/probabilistic_shaping.py | 89e60be5b7ce3de863918f03a6f036287aafc0688a8e24718869784c5b0832b7 |
| src/modulation/joint_ps_gs.py | 3760b7c2677c9c88361eb444778f5955beff4529a69472df927647cfac384d8f |
| src/modulation/normalization.py | 88dd777f6ce2f64117dc64cbcebc1335337aaa73f5b597410618d0581fd47ce2 |
| src/modulation/qam256.py | 34238f2958943016fac82766e464c3dbacb797a60a2df55566d41afee4a145fa |
| src/cvqkd/gram_moments.py | bbad4c303a71ae69be99a4fffba90d968de35f34242977bad03dc1b3e6c5c551 |
| docs/FINAL_MODEL_SPEC.md | 8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843 |

The abbreviated hashes in this table are only for readability; the complete hashes are in the machine-readable artifact and the repository state records. No focused project test was changed or claimed as a result of this report.

Final classification:

**INVESTIGATE_AP_WORKER_BUG**

Final lifecycle:

**NOT_READY_FOR_PUBLICATION_SCALE_RUNS**

Final adaptive-training status:

**NOT_READY_FOR_ADAPTIVE_TRAINING**

## Footnotes

[^1]: S. Denys, P. Brown, and A. Leverrier, “Explicit asymptotic secret key rate of continuous-variable quantum key distribution with an arbitrary modulation,” Quantum 5, 540 (2021). The paper defines the finite coherent-state source, discusses the QAM numerical problem, and specifies the support-restricted inverse used in the source-moment construction. See Sources [1] and [2].

[^2]: PyTorch documentation for torch.nn.functional.softmax, including the normalized-exponential definition and the recommendation to use log_softmax for better numerical properties. See Source [3].

[^3]: N. J. Higham, “Eigenvalue Inequalities for Hermitian Matrices,” including Rayleigh-quotient and Weyl perturbation bounds. See Source [4].

[^4]: Python documentation for float.hex and float.fromhex, which gives an exact hexadecimal representation and round trip of binary floating-point values. See Source [5].

[^5]: mpmath documentation on conversion from Python floats and finite-precision arithmetic. See Sources [6] and [7].

[^6]: The mpmath matrix documentation specifies eighe for Hermitian eigensystems. The interpretation of unresolved near-zero modes here is a numerical-analysis inference from the repository ladder, not a claim that mpmath supplies a rigorous eigenvalue enclosure. See Source [8].

[^7]: Arb documentation describes arbitrary-precision real/complex ball arithmetic with propagated error bounds and matrix support. See Source [9].

[^8]: mpmath’s interval context documentation labels its interval arithmetic experimental. See Source [10].

[^9]: M. N. Notarnicola et al., “Probabilistic amplitude shaping for continuous-variable quantum key distribution with discrete modulation over a wiretap channel,” arXiv:2211.05688 (2022). See Source [11].

[^10]: E. Parente et al., “Discrete-Modulation Continuous-Variable Quantum Key Distribution with Probabilistic Amplitude Shaping over a Linear Quantum Channel,” Applied Sciences 16, 6694 (2026). See Source [12].

[^11]: F. Roumestan et al., “High-Rate Continuous Variable Quantum Key Distribution Based on Probabilistically Shaped 64 and 256-QAM,” arXiv:2111.12356 (2021). See Source [13].

[^12]: S. Bäuml et al., “Security of discrete-modulated continuous-variable quantum key distribution,” Quantum 8, 1418 (2024). See Source [14].

[^13]: “Introduction to coherent quantization,” including the finite-set
  linear-independence statement for distinct coherent states. See Source [15].

## Sources

1. Denys, Brown, and Leverrier, “Explicit asymptotic secret key rate of continuous-variable quantum key distribution with an arbitrary modulation,” Quantum 5, 540 (2021):
   https://quantum-journal.org/papers/q-2021-09-13-540/
2. Denys, Brown, and Leverrier, full preprint:
   https://arxiv.org/pdf/2103.13945
3. PyTorch, torch.nn.functional.softmax documentation:
   https://docs.pytorch.org/docs/main/generated/torch.nn.functional.softmax.html
4. N. J. Higham, “Eigenvalue Inequalities for Hermitian Matrices”:
   https://nhigham.com/2021/03/09/eigenvalue-inequalities-for-hermitian-matrices/
5. Python standard-library documentation for float.hex:
   https://docs.python.org/3/library/stdtypes.html#float.hex
6. mpmath general documentation, conversion and precision:
   https://mpmath.org/doc/current/general.html
7. mpmath technical documentation:
   https://www.mpmath.org/doc/current/technical.html
8. mpmath matrix and Hermitian eigensystem documentation:
   https://mpmath.org/doc/current/matrices.html
9. Arb official documentation:
   https://www.arblib.org/
10. mpmath interval-context documentation:
    https://mpmath.org/doc/current/contexts.html
11. Notarnicola et al., “Probabilistic amplitude shaping for continuous-variable quantum key distribution with discrete modulation over a wiretap channel”:
    https://arxiv.org/abs/2211.05688
12. Parente et al., “Discrete-Modulation Continuous-Variable Quantum Key Distribution with Probabilistic Amplitude Shaping over a Linear Quantum Channel”:
    https://www.mdpi.com/2076-3417/16/13/6694
13. Roumestan et al., “High-Rate Continuous Variable Quantum Key Distribution Based on Probabilistically Shaped 64 and 256-QAM”:
    https://arxiv.org/abs/2111.12356
14. Bäuml et al., “Security of discrete-modulated continuous-variable quantum key distribution”:
    https://quantum-journal.org/papers/q-2024-07-18-1418/
15. “Introduction to coherent quantization,” including the finite-set
    linear-independence statement for distinct coherent states:
    https://link.springer.com/article/10.1007/s13324-022-00689-3
