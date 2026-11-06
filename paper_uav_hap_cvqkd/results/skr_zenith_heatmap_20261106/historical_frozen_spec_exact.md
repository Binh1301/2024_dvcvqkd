# Final mathematical model specification

Status: **authoritative implemented specification**. This document freezes the scientific model for the manuscript and implementation. Where it differs from older documentation, this document takes precedence.

No finite-size or composable-security claim is made. The security calculation is the author's accepted asymptotic reverse-reconciliation, ideal-heterodyne DM-CV-QKD chain

\[
\tau\longrightarrow(C,w)\longrightarrow Z\longrightarrow\Gamma_{AB}\longrightarrow\chi_{BE}.
\]

The HAP transmitter is given perfect instantaneous oracle CSI \((T,\epsilon)\), where \(T\) is power transmittance and \(\epsilon\) is input-referred excess noise in SNU. CSI estimation, feedback, delay, quantization, and authentication are outside the present model. All neural and geometry parameters are learned offline and frozen at deployment.

## 1. Scientific objective and common ensemble

For channel state

\[
s=[\log_{10}T,\epsilon],
\]

the frozen transmitter produces a 256-symbol PMF and a modulation variance,

\[
s\mapsto \bigl(\mathbf p_\theta(s),V_{A,\phi}(s)\bigr).
\]

One globally learned geometry \(C_\psi\) is shared by every state. The statewise physical ensemble

\[
\mathcal E(s)=\{p_i(s),\alpha_i(s)\}_{i=1}^{256}
\]

is constructed once and passed unchanged to both the discrete-input mutual-information calculation and the accepted Holevo calculation. It is invalid to compute \(I_{AB}\) and \(\chi_{BE}\) from different PMFs, amplitudes, centering conventions, or values of \(V_A\).

The scientific optimization is

\[
\max_{\theta,\phi,\psi}\;\mathbb E_{s\sim\mathcal D_{\rm train}}[K(s)],
\qquad
K(s)=\beta I_{AB}(\mathcal E(s);T,\epsilon)-\chi_{BE}(\mathcal E(s);T,\epsilon),
\]

subject to the energy conditions in Section 8. This is direct expected-SKR optimization, not BER, reconstruction-loss, or MI-only optimization.

## 2. Channel-conditioned neural transmitter

The PS and variance branches are independent. They have no shared trainable trunk, which keeps their gradient ownership and ablations unambiguous. Both receive exactly \(s=[\log_{10}T,\epsilon]\). Any future affine feature standardization must use training-set statistics frozen before validation and testing and must be recorded as part of the model; it is not part of the model frozen here.

### 2.1 PS branch: fourfold-symmetric 256-symbol PMF

An unrestricted 256-way PMF is incompatible with the accepted scalar standard-form covariance in general: scalar energy normalization alone does not ensure zero displacement, equal quadrature variance, or zero quadrature cross-covariance. The frozen model therefore partitions the 256 constellation labels into 64 orbits of four points under \(90^\circ\) rotation.

The independent PS network is

\[
s\xrightarrow{\operatorname{Linear}(2,128)}h
\xrightarrow{\operatorname{ReLU}}
\xrightarrow{\operatorname{Linear}(128,64)}\ell_\theta(s),
\]

\[
q_k(s)=\frac{\exp \ell_k(s)}{\sum_{j=1}^{64}\exp \ell_j(s)},
\qquad
p_{k,r}(s)=\frac{q_k(s)}{4},
\quad k=1,\ldots,64,\quad r=0,1,2,3.
\]

Thus the deployed output is still \([p_1,\ldots,p_{256}]\), but it has 64 independent orbit masses. For finite logits, \(q_k>0\), hence \(p_{k,r}>0\), and

\[
\sum_{k=1}^{64}\sum_{r=0}^{3}p_{k,r}=1.
\]

The claims must therefore say **channel-adaptive fourfold-symmetric probabilistic shaping**, not unrestricted arbitrary 256-way shaping.

### 2.2 Adaptive-variance branch

The independent variance network is

\[
s\xrightarrow{\operatorname{Linear}(2,64)}h_V
\xrightarrow{\operatorname{ReLU}}
\xrightarrow{\operatorname{Linear}(64,1)}z_\phi(s),
\]

followed by

\[
u(s)=\sigma(z_\phi(s)),
\qquad
V_A(s)=V_{\min}\left(\frac{V_{\max}}{V_{\min}}\right)^{u(s)},
\qquad 0<V_{\min}<V_{\max}.
\]

Because \(0<u<1\) for finite \(z\) and the mapping is monotone, finite network outputs satisfy \(V_{\min}<V_A<V_{\max}\). The stated closed bounds \(V_{\min}\le V_A\le V_{\max}\) also include the limiting cases \(z\to-\infty\) and \(z\to+\infty\). The log-domain interpolation prevents negative variance and treats multiplicative changes in \(V_A\) uniformly.

At deployment, \(\theta^*\), \(\phi^*\), and \(\psi^*\) are frozen. Different states cause different forward-pass outputs \(\mathbf p(s)\) and \(V_A(s)\); they do not cause retraining.

## 3. Global geometry and physical amplitudes

### 3.1 Raw, relative, and physical coordinates

Let \(g_k\in\mathbb C\), \(k=1,\ldots,64\), be trainable raw orbit prototypes. They generate a 256-point raw constellation

\[
c^{\rm raw}_{k,r}=\mathrm i^r g_k,
\qquad r=0,1,2,3.
\]

These 64 complex prototypes are the independent parameterization of the author's global 256-point set \(C_\psi\). They are shared across all channel states and are never outputs of a channel-conditioned network.

Raw geometry has an irrelevant positive scale gauge, because the later physical energy normalization cancels it. Remove that flat direction once, globally, using

\[
z_k=\frac{g_k}{\sqrt{\frac1{64}\sum_{j=1}^{64}|g_j|^2}},
\qquad
x_{k,r}=\mathrm i^r z_k.
\]

The \(x_{k,r}\) are the **relative geometry**. Their distance and angle pattern is GS; it is channel-independent. A global phase is physically immaterial and may be removed only when aligning constellations for plots. The initialization/reference geometry is the ordinary square 16-by-16 QAM grid, partitioned into its 64 rotational orbits with the existing deterministic symbol labeling.

Given orbit masses \(q_k(s)\), define

\[
E_x(s)=\sum_{k=1}^{64}q_k(s)|z_k|^2
=\sum_{k,r}p_{k,r}(s)|x_{k,r}|^2.
\]

The **physical coherent-state amplitudes** are

\[
\boxed{
\alpha_{k,r}(s)=
\sqrt{\frac{V_A(s)}{2E_x(s)}}\;x_{k,r}
}
\]

with no state-dependent translation or deformation.

### 3.2 Exact normalization identities

The construction gives

\[
2\sum_{k,r}p_{k,r}(s)|\alpha_{k,r}(s)|^2=V_A(s).
\]

Fourfold rotation also gives, identically for every state,

\[
\sum_{k,r}p_{k,r}\alpha_{k,r}=0,
\qquad
\sum_{k,r}p_{k,r}\alpha_{k,r}^2=0.
\]

The second identity implies equal in-phase and quadrature second moments and zero I/Q cross-covariance. Therefore the only state-dependent coordinate change caused by PS at fixed \(V_A\) is the single global scale needed to maintain energy; relative distances and angles do not change. This is the clean separation required by the accepted scalar-\(V_A\), standard-form security model.

### 3.3 Comparison with the superseded implementation

The superseded pre-freeze implementation used an unrestricted `2 -> 128 -> 256` softmax and PMF-weighted centering and normalization,

\[
\mu_{\mathbf p}=\sum_i p_i c_i,
\qquad
\widetilde x_i=\frac{c_i-\mu_{\mathbf p}}
{\sqrt{\sum_jp_j|c_j-\mu_{\mathbf p}|^2}},
\qquad
\alpha_i=\sqrt{V_A/2}\,\widetilde x_i.
\]

That convention makes PS induce a PMF-dependent translation and symbol-dependent physical displacement relative to the raw origin. It fixes the weighted mean and total energy, but an unrestricted PMF/geometry can still violate quadrature symmetry. It therefore confounds PS with physical-coordinate changes and triggers the strict standard-form guard.

The frozen replacement changes the independent PS output from 256 logits to 64 orbit logits, ties probabilities within each rotational orbit, ties global GS points by the same rotations, removes PMF-weighted translation, and uses only the boxed scalar normalization above. The active transmitter/normalization path implements this replacement; legacy checkpoints are intentionally incompatible.

## 4. Fixed PMFs

For square-QAM indices \(a,b\in\{0,\ldots,15\}\), let \(x_{ab}^{\rm sq}\) denote the canonical square-grid point.

- Uniform: \(p_{ab}=1/256\).
- Binomial: \(p_{ab}=b_a b_b\), where \(b_a={15\choose a}/2^{15}\).
- Maxwell--Boltzmann: \(p_{ab}(\nu)=\exp[-\nu|x_{ab}^{\rm sq}|^2]/Z(\nu)\), \(\nu\ge0\).

All three are fourfold symmetric and are compatible with the normalization above. A **fixed MB** baseline uses a preregistered \(\nu\). A **globally optimized MB** baseline selects one channel-independent \(\nu\), and its one fixed \(V_A\), using validation data only and then freezes both for testing.

## 5. Ablations and gradient ownership

"Fixed \(V_A\)" means one channel-independent scalar chosen by the common validation protocol and then frozen. It is not a network output. Fixed PMF/geometry/variance hyperparameters do not receive minibatch training gradients.

| Mode | PMF | Relative geometry | Variance | Parameters receiving training gradients |
|---|---|---|---|---|
| Uniform | \(p_i=1/256\) | fixed square QAM | fixed \(V_A\) | none |
| Binomial | fixed binomial | fixed square QAM | fixed \(V_A\) | none |
| Fixed MB | fixed MB with declared \(\nu\) | fixed square QAM | fixed \(V_A\) | none |
| Globally optimized MB | one validation-selected MB \(\nu^*\) | fixed square QAM | validation-selected fixed \(V_A^*\) | none in model training; \(\nu,V_A\) are validation-only scalar search variables |
| Adaptive PS | \(p_\theta(s)\) | fixed square QAM | fixed \(V_A\) | \(\theta\) only |
| GS-only | uniform | global \(x_\psi\) | fixed \(V_A\) | \(\psi\) only |
| Adaptive VA-only | uniform | fixed square QAM | \(V_{A,\phi}(s)\) | \(\phi\) only |
| PS + GS | \(p_\theta(s)\) | global \(x_\psi\) | fixed \(V_A\) | \(\theta,\psi\) |
| PS + adaptive VA | \(p_\theta(s)\) | fixed square QAM | \(V_{A,\phi}(s)\) | \(\theta,\phi\) |
| GS + adaptive VA | uniform | global \(x_\psi\) | \(V_{A,\phi}(s)\) | \(\psi,\phi\) |
| Full | \(p_\theta(s)\) | global \(x_\psi\) | \(V_{A,\phi}(s)\) | \(\theta,\psi,\phi\) |

The GS-only and GS-combination modes learn one geometry over the training channel distribution. They do not condition geometry on \(T\) or \(\epsilon\).

## 6. Raw SKR objective and rate reporting

For a minibatch \(\{s_n\}_{n=1}^{B}\), construct one ensemble \(\mathcal E_n\) per state and define

\[
K_n^{\rm raw}=\beta I_{AB,n}-\chi_{BE,n},
\qquad
\boxed{
\mathcal L_{\rm SKR}=-\frac1B\sum_{n=1}^{B}K_n^{\rm raw}
}.
\]

No \(\max(0,K_n)\) is placed inside the training loss; doing so would remove the SKR gradient in negative-rate states.

Report all of the following distinctly:

1. the primary raw fading average \(\overline K_{\rm raw}=\mathbb E_s[K^{\rm raw}(s)]\);
2. the nonnegative aggregate rate \(K_{\rm aggregate}=[\overline K_{\rm raw}]_+\), if a physical nonnegative number is required;
3. \(\mathbb E_s[[K^{\rm raw}(s)]_+]\) only as a clearly labeled **state-selective oracle diagnostic**. It is not the primary rate unless a valid transmit/abstain protocol is added.

The accepted \(\tau\to(C,w)\to Z\to\Gamma_{AB}\to\chi_{BE}\) equations, \(\beta\), detector assumptions, noise units, and Fock truncation convention must be identical for every mode.

## 7. Geometry regularizers

Let \(M=256\), let \(x_i\) be the canonical relative points, let \(x_i^{\rm sq}\) be the label-matched canonical square-QAM reference, and let \([a]_+=\max(0,a)\).

### 7.1 Separation hinge

\[
\mathcal L_{\rm sep}=
\frac{2}{M(M-1)}
\sum_{i<j}
\left[1-\frac{|x_i-x_j|}{d_{\rm sep}}\right]_+^2.
\]

This prevents point collisions and near-duplicate states. It acts on relative coordinates. Pairwise distances are translation invariant. The formula is not intrinsically scale invariant, but canonical unit-RMS normalization makes it invariant to a positive rescaling of all raw prototypes; it is also invariant to global rotation. The fourfold construction fixes the physical origin, so translation is not an admissible geometry parameter. The threshold \(d_{\rm sep}\) is dimensionless. The term is compatible with physical energy normalization. It is not initially necessary: set its coefficient to zero and monitor minimum pair distance; activate it only in a preregistered rerun if collapse occurs.

### 7.2 Physical peak hinge

For state \(s_n\), let \(A_{\max,n}=\max_i|\alpha_i(s_n)|^2\). Given a justified physical or numerical threshold \(A_{\rm soft}>0\),

\[
\mathcal L_{\rm peak}=
\frac1B\sum_{n=1}^{B}
\left[\frac{A_{\max,n}}{A_{\rm soft}}-1\right]_+^2.
\]

This discourages rare amplitudes that exceed hardware range or make Fock truncation unreliable. It acts on physical coordinates and is intentionally neither translation nor scale invariant; the physical origin is already fixed to zero. It does not conflict with average-energy normalization, but it can change the optimal shape. No arbitrary \(A_{\rm soft}\) is frozen here, so its coefficient is initially zero. First monitor the diagnostics in Section 8.

### 7.3 Reference-geometry drift

\[
\mathcal L_{\rm drift}=
\min_{\varphi\in[0,2\pi)}
\frac1M\sum_{i=1}^{M}
|x_i-e^{\mathrm i\varphi}x_i^{\rm sq}|^2.
\]

This is label-preserving Procrustes drift from square QAM and prevents large geometry departures. It acts on relative coordinates. Phase minimization makes it rotation invariant, and canonical unit-RMS normalization makes it invariant to positive raw scale. The written expression is not translation invariant, but both constellations have the same fixed zero origin and translation is not an admissible fourfold-symmetric parameter. It is compatible with normalization but directly biases against discovering a better GS solution. It is therefore omitted from the primary model (coefficient zero); it may be used only as a declared warm-start stabilization or sensitivity ablation.

If any terms are activated, the declared primal loss is

\[
\mathcal L=\mathcal L_{\rm SKR}
+\lambda_{\rm sep}\mathcal L_{\rm sep}
+\lambda_{\rm peak}\mathcal L_{\rm peak}
+\lambda_{\rm drift}\mathcal L_{\rm drift},
\]

with every coefficient and threshold selected without test data. The primary frozen configuration has all three coefficients equal to zero.

## 8. Energy fairness and amplitude diagnostics

With the coherent-state convention used here,

\[
V_A(s)=2\sum_i p_i(s)|\alpha_i(s)|^2,
\qquad
\mathbb E[|\alpha|^2\mid s]=\frac{V_A(s)}2,
\qquad
\bar n(s)=\frac{V_A(s)}2.
\]

All fixed and adaptive comparisons use the same pointwise box \([V_{\min},V_{\max}]\) and the same fading-averaged photon budget

\[
\mathbb E_{s\sim\mathcal D}[\bar n(s)]\le \bar n_{\rm budget},
\quad\text{equivalently}\quad
\mathbb E_{s\sim\mathcal D}[V_A(s)]\le V_{A,\rm budget}=2\bar n_{\rm budget}.
\]

The same state distribution and weights must be used for this constraint and for expected SKR. During training the constraint may be enforced by a nonnegative dual variable,

\[
\mathcal L_{\rm constrained}
=\mathcal L+\lambda_E
\left(\frac1B\sum_nV_A(s_n)-V_{A,\rm budget}\right),
\qquad \lambda_E\ge0,
\]

with descent in model parameters and projected ascent in \(\lambda_E\). This enforces a constraint rather than redefining the scientific objective. Final validation and test policies must satisfy the budget on their complete state sets. Fixed-\(V_A\) baselines select one scalar on validation subject to the identical budget and box.

Do not impose an unmotivated hard peak constraint initially. Record, per state and in fading-distribution summaries,

\[
A_{\max}(s)=\max_i|\alpha_i(s)|^2,
\qquad
\operatorname{PAPR}(s)=
\frac{A_{\max}(s)}{\mathbb E_p[|\alpha|^2\mid s]}
=\frac{2A_{\max}(s)}{V_A(s)}.
\]

Also record high quantiles of \(|\alpha_i|^2\) under the joint state-symbol distribution. The Fock cutoff must converge at the largest amplitudes actually produced, not only at the average energy.

## 9. Required invariants before training

Every implementation mode must test, statewise and at strict numerical tolerance:

- \(p_i>0\), \(\sum_i p_i=1\), and equality of the four probabilities within every orbit;
- \(\sum_i p_i\alpha_i=0\) and \(\sum_i p_i\alpha_i^2=0\);
- \(2\sum_i p_i|\alpha_i|^2=V_A\);
- equal I/Q variance and zero I/Q covariance;
- identical ensemble object/values at the MI and Holevo interfaces;
- finite, physical covariance/symplectic spectra with no silent repair;
- nonzero finite-difference and autograd sensitivity along every enabled parameter path;
- MI Monte Carlo convergence and density-matrix/Fock-cutoff trace convergence across the entire \(V_A\) and amplitude range.

## 10. Contribution and scope

The precise contribution to test is:

> A channel-conditioned fourfold-symmetric probabilistic-shaping and modulation-variance policy, combined with one globally optimized 256-state geometry, trained offline end-to-end by direct expected asymptotic SKR maximization over an ideal-CSI HAP--UAV FSO fading distribution.

The work does not claim that PS, GS, 256-QAM, CV-QKD, or adaptive \(V_A\) is individually novel. Its evidence must isolate the incremental value of channel-conditioned PS, channel-conditioned variance, and global geometry under one energy-fair security calculation.

## 11. Remaining numerical decisions

The mathematical architecture is frozen. Before publication-scale training, the experiment configuration must still declare: \(V_{\min}\), \(V_{\max}\), \(V_{A,\rm budget}\), \(\beta\), the joint train/validation/test distributions of \((T,\epsilon)\), Fock cutoff and convergence tolerance, MI sample budgets, optimizer/schedule/seed counts, and any activated regularizer thresholds. Reconciliation feasibility, imperfect CSI, finite-size security, detector imperfections, and a transmit/abstain protocol remain explicit limitations or future work, not blockers to implementing this asymptotic oracle study.
