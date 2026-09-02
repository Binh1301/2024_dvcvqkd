# Physical amplitude-domain decision

Status: **author-approved 30-photon domain; fixed families certified; learned
families remain fail-closed pending their selected roster**.
This decision does not modify `FINAL_MODEL_SPEC.md`, does not broaden the
security scope in `SECURITY_SCOPE_FREEZE.md`, and does not authorize
publication-scale training.  It defines the additional common admissibility
domain needed to certify a finite Fock cutoff.

## 1. Exact source of the unbounded rare amplitude

For orbit mass `q_k`, global relative prototype `z_k`, and its four rotations,

\[
p_{k,r}=q_k/4,\qquad
E_x=\sum_k q_k|z_k|^2,\qquad
\alpha_{k,r}=\sqrt{\frac{V_A}{2E_x}}\,i^r z_k .
\]

The implemented global GS gauge is

\[
\frac1{64}\sum_k|z_k|^2=1,
\]

so `sum_k |z_k|^2=64` and `max_k |z_k|^2<=64`.  This does not
lower-bound `E_x`.  For example, let one prototype have squared magnitude
`64-63 delta^2`, let the other 63 have squared magnitude `delta^2`, assign
orbit mass `eta` to the large prototype, and distribute `1-eta` over the
small prototypes.  Then

\[
E_x=\eta(64-63\delta^2)+(1-\eta)\delta^2\longrightarrow0
\]

as `eta,delta -> 0`, while the rare large-prototype symbol has

\[
|\alpha_{1,r}|^2=
\frac{V_A}{2}\frac{64-63\delta^2}{E_x}\longrightarrow\infty .
\]

Finite softmax logits ensure `q_k>0` for a particular forward pass, but give no
parameter-independent positive lower bound.  The average-energy identity
continues to hold because the diverging symbols become correspondingly rare.
Consequently, `V_A<=V_max`, the unit-RMS GS gauge, and average photon-number
fairness do not by themselves define a finite Fock-amplitude domain.

## 2. Candidate mechanisms

| Mechanism | Interpretability and IEEE explainability | Differentiability | Fairness and shaping expressiveness | Fock-domain consequence | Decision |
|---|---|---|---|---|---|
| Hard physical peak photon energy, `max_i |alpha_i(s)|^2 <= n_peak` | Direct transmitter/dynamic-range quantity in photons per coherent symbol; independent of labels and parameterization | `max` is continuous and differentiable almost everywhere; ties use a valid subgradient. Exact feasibility still needs a hard guard, not only a loss | One identical physical constraint for all fixed/adaptive PS, GS, and PS+GS schemes. It restricts only ensembles that violate the declared hardware/numerical domain | Directly gives `|alpha|<=sqrt(n_peak)` and therefore a finite worst-case input to cutoff validation | **Selected primary mechanism** |
| Hard PAPR, `PAPR<=rho_max` | Familiar communications constraint, but relative rather than an absolute optical amplitude | Same almost-everywhere property as the hard peak | Common and energy-normalized, but can constrain low- and high-`V_A` policies differently in absolute amplitude | Gives `|alpha|^2<=rho_max V_max/2`; finite only jointly with approved `V_max` | Rejected as primary; less direct than photon energy |
| Bounded GS coordinates | Geometric but parameterization-dependent | Smooth maps such as `tanh` are available | Restricts GS even where physical amplitudes are harmless; does not solve PS-induced `E_x->0` unless a lower-radius condition is also imposed | No finite physical bound from an upper coordinate bound alone | Insufficient |
| Orbit-probability floor `q_k>=q_floor` | Easy to state but lacks a direct hardware meaning | Smoothly implementable as `q=q_floor+(1-64q_floor)softmax(l)` | Directly reduces PS expressiveness and entropy range. A common floor large enough to be numerically useful can exclude the fixed Binomial/MB references | With the unit-RMS gauge, `|alpha|^2<=V_max/(2q_floor)` | Rejected as primary |
| Soft peak penalty only | Useful optimization aid | Almost-everywhere differentiable | Does not define an admissible comparison domain and depends on coefficient tuning | Cannot certify any finite worst-case cutoff | Rejected as certification mechanism |

### Selected rule

Every ensemble evaluated or accepted for training selection, validation,
baseline selection, convergence certification, or held-out testing shall obey

\[
\boxed{A_{\max}(s)=\max_i|\alpha_i(s)|^2\le n_{\rm peak}}
\]

for the author-approved value `n_peak=30` photons, common to all eleven
schemes, under the `complete_preregistered_realizations` scope. It was fixed
before validation or test performance and was not inferred from trained
amplitudes.

This hard rule, rather than a peak regularizer, is the certification mechanism.
An optional differentiable constraint term may help optimization, but no
checkpoint is eligible unless an exact guard verifies the boxed inequality.
Fock convergence must include the boundary amplitude `sqrt(n_peak)`, not only
the maximum observed in a selected checkpoint.

The current verifier accepts only the complete preregistered realization set,
with every realized state checked. Continuous-support or state-bin claims remain
blocked until a real external certificate is implemented and hash-bound;
checking minibatches or finite fixtures does not establish either claim.

## 3. Exact regular-QAM baseline references

The canonical square constellation implemented by `canonical_square_qam256`
is

\[
z_{ab}=\frac{(a-7.5)+i(b-7.5)}{\sqrt{42.5}},\qquad a,b=0,\ldots,15,
\]

and hence

\[
e_{ab}=|z_{ab}|^2,\qquad e_{\max}=\frac{45}{17}.
\]

For any fixed square-QAM PMF define

\[
E_p=\sum_{ab}p_{ab}e_{ab},\quad
R_p=\frac{e_{\max}}{E_p},\quad
\operatorname{PAPR}=R_p,\quad
A_{\max}=\frac{V_A}{2}R_p.
\]

The exact reference coefficients are:

| Baseline | `E_p` | PAPR `R_p` | Peak photon energy `A_max` | Peak-feasible fixed-`V_A` ceiling |
|---|---:|---:|---:|---:|
| Uniform 256-QAM | `1` | `45/17 = 2.6470588235294118` | `(45/34) V_A = (45/17) n_bar` | `V_A <= (34/45)n_peak` |
| Product-Binomial 256-QAM | `3/17` | `15` | `(15/2) V_A = 15 n_bar` | `V_A <= (2/15)n_peak` |

For the Binomial PMF, the smallest corner-symbol probability is `2^-30` and
the corresponding four-point orbit mass is `2^-28`.  Its large PAPR is thus a
real consequence of applying the common physical-energy normalization to a
distribution concentrated near the origin; it is not a numerical error.

For Maxwell--Boltzmann shaping,

\[
p_{ab}(\nu)=\frac{e^{-\nu e_{ab}}}{Z(\nu)},\qquad
E_{\rm MB}(\nu)=\frac{\sum_{ab}e_{ab}e^{-\nu e_{ab}}}
{\sum_{ab}e^{-\nu e_{ab}}},
\]

\[
R_{\rm MB}(\nu)=\frac{45/17}{E_{\rm MB}(\nu)},\qquad
A_{\max}^{\rm MB}=\frac{V_A}{2}R_{\rm MB}(\nu),\qquad
V_A\le\frac{2n_{\rm peak}}{R_{\rm MB}(\nu)}.
\]

The fixed reference is **AUTHOR_APPROVED** at `nu_MB=0.1`. The optimized-MB
domain is **AUTHOR_APPROVED** as `[0,0.3]`; its validation-only
**SOFTWARE_PREREGISTERED** discretization is `0.00:0.01:0.30`. At `nu=0` the
formula reduces exactly to the Uniform result.

### Approved-domain certification

With `V_min=0.1`, `V_max=4.0`, average `V_A` budget `1.5`, and
`n_peak=30`, the fixed-policy validation grid is the preregistered uniform
discretization `0.1:0.1:1.5 SNU`. Every candidate is peak feasible. The
full `[0.1,4.0]` physical box is also certified for each fixed reference:

| Family | PAPR | Peak at `V_A=4` photons | Result |
|---|---:|---:|---|
| Uniform | `45/17` | `90/17 = 5.294117647058823` | PASS |
| Binomial | `15` | `30` exactly | PASS at the boundary |
| Fixed MB, `nu=0.1` | `2.754443493980498` | `5.508886987960996` | PASS |
| Optimized MB, every `nu=0.00:0.01:0.30` | `2.647058823529411` through `2.985998568298204` | at most `5.971997136596409` | PASS |

The Binomial calculation at `V_A=4` is a physical-domain boundary diagnostic,
not a fixed-policy search candidate: constant policies remain restricted by
the average budget to `V_A<=1.5`. Exact analytic and independently constructed
numerical values are recorded in `results/amplitude_domain_certification.json`.
PS- and/or GS-shaped learned modes are not falsely assigned a global analytic
certificate; they retain the same runtime guard and require recertification of
the complete selected roster.

## 4. Audit of all eleven comparison schemes

| Scheme | Peak-rule application | Benchmark-exclusion risk |
|---|---|---|
| Uniform | Apply exact coefficient `45/17` at its validation-selected fixed `V_A` | Excluded if `V_min>(34/45)n_peak` |
| Binomial | Apply exact coefficient `15` at its validation-selected fixed `V_A` | Excluded if `V_min>(2/15)n_peak`; this is the most immediate fixed-baseline risk |
| Fixed MB | Use certified `R_MB(0.1)` and select fixed `V_A` on `0.1:0.1:1.5` by validation only | No candidate is peak-excluded under `n_peak=30` |
| Optimized MB | Every preregistered `(nu,V_A)` pair is checked before validation scoring | All `31 x 15` preregistered candidates are peak feasible; test selection remains forbidden |
| Adaptive PS | Square geometry; check `e_max/E_q(s)` for every relevant state | Highly concentrated orbit masses can be inadmissible |
| GS-only | Uniform orbit masses imply `E_x=1`; check global `max_k|z_k|^2` and fixed `V_A` | Extreme global prototypes can be inadmissible |
| Adaptive VA-only | PAPR is `45/17`; apply the rule statewise to `V_A(s)` | Upper `V_A` outputs can be inadmissible |
| PS+GS | Check the joint ratio `max_k|z_k|^2/E_x(s)` at fixed `V_A` | Retains the original rare-amplitude failure without the hard rule |
| PS+adaptive VA | Check the square-geometry ratio times statewise `V_A(s)/2` | Concentrated PS and high adaptive `V_A` can jointly violate |
| GS+adaptive VA | Check global GS ratio times statewise `V_A(s)/2` | Extreme GS and high adaptive `V_A` can jointly violate |
| Full | Check the complete statewise physical ensemble | Highest risk; all three factors can combine |

No benchmark may be silently removed after observing validation or test
performance.  Before any test access, the approved `n_peak`, `V_min`, and MB
domains must leave at least one feasible candidate for every mandatory scheme.
If they do not, the publication comparison remains blocked: revise the common
physical domain or the common `V_A` domain prospectively, regenerate all
development artifacts, and document the change.  A separate threshold per
scheme is prohibited.

## 5. GS scale gauge verification

For raw prototypes `g_k` with

\[
r(g)=\sqrt{\frac1{64}\sum_k|g_k|^2},\qquad z_k(g)=g_k/r(g),
\]

any positive scalar `c` gives `z_k(cg)=z_k(g)`.  Therefore `E_x`, every
physical `alpha_(k,r)`, the PMF, `V_A`, MI, and the Holevo input ensemble are
exactly invariant to positive raw scaling.  A global complex phase rotates the
constellation and is relevant only to plot alignment; it is not the positive
scale gauge removed by the implementation.

For any differentiable objective `F` depending on `g` only through `z(g)`,
`F(cg)=F(g)`.  Euler's homogeneous-function identity gives the radial-gradient
condition

\[
\left\langle g,\nabla_gF\right\rangle_{\mathbb R^{128}}=0.
\]

The active `GlobalGeometricShaping.relative_prototypes()` implementation
performs this unit-RMS normalization.  Existing tests verify positive-scale
physical invariance and a nonzero gradient orthogonal to the raw radial
direction.

### Repeated-update stability verification

`tests/test_physical_peak_domain.py` performs 100 consecutive float64 optimizer
updates on a GS-enabled differentiable objective. After every update it asserts:

1. finite, nondegenerate raw prototype RMS;
2. `mean_k |z_k|^2=1` to `1e-12` absolute tolerance;
3. exact C4 expansion, energy normalization, zero mean, and zero pseudomoment;
4. before each update, a nonzero GS gradient and relative radial component
   `|<g,grad>|/(||g|| ||grad||) <= 1e-10`;
5. multiplying the current raw coordinates by each preregistered positive
   scale in a small test set leaves the forward physical ensemble unchanged to
   `1e-11` relative/absolute tolerance; and
6. `A_max<=n_peak` whenever the test uses an amplitude-admissible fixture.

The test must not require the raw norm itself to remain constant: Euclidean or
Adam updates can move the redundant raw radius even though every forward pass
removes it.  The pass criterion is stability of the canonical and physical
outputs, not raw-coordinate equality.

## 6. Implemented mechanism contract

The numerical implementation now:

1. provides one author-controlled field, `cvqkd.n_peak_photons`, shared by
   every baseline, learned mode, convergence script, and evaluator;
2. compute `A_max=max_i |alpha_i|^2` from the final physical `Ensemble`, after
   the frozen scalar normalization, without clipping or rescaling symbols;
3. applies an exact fail-closed admissibility check at all ensemble interfaces used
   for baseline search, learned checkpoint selection, convergence, and final
   evaluation;
4. rejects inadmissible initial forward passes and uses a rollback feasible-step
   mechanism that restores both model and Adam state after an invalid proposal;
5. marks any infeasible validation candidate as ineligible before its SKR is
   compared, using the same rule and tolerance for all schemes;
6. require every selected checkpoint to pass the peak rule on the complete
   preregistered selection domain and record its maximum, slack, offending
   state if any, and configuration hash;
7. includes a synthetic C4 boundary fixture at `|alpha|=sqrt(n_peak)` in the Fock
   convergence configurations and set
   but records finite-fixture coverage only; publication evidence must enumerate
   and hash-bind every selected baseline ensemble and learned checkpoint;
8. preserve the same ensemble object at the MI and Holevo interfaces and all
   C4, energy, and security guards;
9. includes the repeated-update gauge test above and scheme-wide peak/fairness tests;
   and
10. rejects unresolved/unapproved `n_peak`, `V_min`, `V_max`, fixed-MB `nu_ref`, or an empty
    feasible baseline grid before publication execution.

No individual-amplitude clipping, post-hoc probability deletion, test-selected
threshold, or scheme-specific peak allowance is permitted: each would change
the ensemble, break comparison fairness, or invalidate the frozen MI/Holevo
identity.

## 7. Approval closure and remaining convergence handoff

The peak value (`30` photons), realized-state scope, fixed-MB reference
(`nu=0.1`), optimized-MB domain (`[0,0.3]`), and common `V_A` box/budget are
author approved. Fixed-family feasibility is certified by the reproducible
artifact. Before publication execution, numerical convergence must still be
established at the boundary `|alpha|=sqrt(30)` and every learned selected
ensemble must pass the same rule on the complete preregistered roster.

## 8. Exact manuscript wording

Subject to successful Fock convergence and selected-roster certification, use:

> All fixed and learned 256-state ensembles were restricted to the same hard
> physical peak coherent-state energy, `max_i |alpha_i(T,epsilon)|^2 <=
> 30`, in addition to the common modulation-variance box and fading-average
> photon-number budget.  The threshold was preregistered before optimization
> and held fixed across Uniform, Binomial, Maxwell--Boltzmann, PS, GS, adaptive
> variance, and joint ablations.  It was enforced on the final physical
> amplitudes after the common scalar energy normalization; no symbol clipping
> or scheme-specific threshold was used.  Fock-space convergence was certified
> through the boundary amplitude `sqrt(30)`.  This constraint defines the
> finite physical simulation domain and does not extend the stated asymptotic
> oracle-CSI security assumptions.

Until convergence is actually selected, do not claim that a Fock cutoff has
been certified; the present artifact certifies the physical amplitude domain
only.
