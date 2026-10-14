# Channel-layer logic review, 2026-10-13

Scope: analytic review of the supplied Binh `(37)` PDF and the two reference
PDFs, current literal backend, saved validation receipt, and historical channel
implementation. No channel integrations, Monte Carlo, AP, SKR, AO, or tests were
run. Existing science, configs, caches, result artifacts, lifecycle records, and
unrelated worktree edits were preserved. This is a proposed correction review,
not a model change or security claim.

Sources below use **physical PDF pages**. Binh is
`2026__Binh_s_work (37).pdf`; Satellite is Sayat et al. 2024, the supplied
satellite-to-ground PDF; DBL is `2103.13945v3 (1).pdf`.

## 1. The saved missing probability has an exact analytic cause

Let `a=chi^2=w_eq^2/(4 sigma_s^2)`, `v=sigma_R^2`, and
`B=A0 eta_atm`. At the actual reference fixture `rho=0`. Then Eqs. (5)--(8)
give independent factors

\[
\ln I_a\sim\mathcal N(-v/2,v),\quad
U=r^2/(2\sigma_s^2)\sim\operatorname{Exp}(1),\quad
X=B\exp[-v/2+\sqrt v\,N-U/a].
\]

The raw active law of `X` is supported on `(0,infinity)`, because lognormal
`I_a` is unbounded. Eq. (10), with `rho=0`, is the exact convolution for this
model; its coefficients are not erroneous at zero boresight:

\[
C_1=e^{v a(1+a)/2},\quad C_3=(2v)^{-1/2},\quad
\mu=v(1+2a)/2.
\]

For the continuous Eq. (10) density `f_X`, the **full-support** mass is

\[
\int_0^\infty f_X(x)\,dx
=C_1\exp\{a^2/(4C_3^2)-a\mu\}=1.
\]

The cancellation is algebraic; there is no integration error hypothesis here.
With Eq. (12)--(14)'s upper limit 1, instead set

\[
F_1=\Pr(X\le1)=C_1Q(a),\quad
M_0=P_0+P_1F_1=1-P_1\Pr(X>1).
\]

The saved receipt at
`results/manuscript_literal_3moments/implementation_validation_4/validation.json`
lines 70--100 records:

| Item | Stored value |
|---|---:|
| `rho` | 0 |
| `sigma_R2` | 0.0539620777961657 |
| `B` | 0.906150936650298 |
| `a` | 0.38570267511254014 |
| `P0` | 0.00016985667656141038 |
| `P1` | 0.9998301433234386 |
| `M0` | 0.9841200272202841 |
| `1-M0` | 0.015879972779715867 |

Thus the saved missing 1.588% is the unconditional probability
`P1 Pr(X>1)` removed by the upper bound, while the original outage atom is kept.
This cause follows exactly from the law and saved values. It is not caused by
AP source moments, QAM, GH8 MI, or a missing normalization factor in the
zero-boresight raw Eq. (10). The current literal code faithfully reproduces the
paper's inconsistent combination of an unbounded raw law and bounded moment
integrals (`src/manuscript_literal_3moments.py:99-156`).

**Do not divide the entire mixed law by M0:** that changes the probability of
AoA outage from `P0` to `P0/M0`. A physical-support decision is required first.

The alternatives are different models, not interchangeable algebraic repairs:

1. **Condition only the active law on `X<=1`, preserve AoA probability.**
   `dP=P0 delta_0 + P1 f_X(t) 1_(0,1](t) dt/F1`.
   With `J_q=E[X^q 1_(X<=1)]`, positive-power mixed moments are `P1 J_q/F1`.
   Explicitly state this conditional phenomenological model. It is already
   implemented by the historical diagnostic `analyze_product`,
   `scripts/calculate_channel_pdf_and_moments.py:571-635`, but it is not the
   literal backend or the historical D55 raw-moment evaluator.
2. **Saturate the raw draw, `T=min(X,1)`.**
   Add a separate atom `P1(1-F1) delta_1`; positive-power moments are
   `P1[J_q+(1-F1)]`. This is a declared approximation, not a derivation of
   physical aperture energy conservation.
3. **Treat over-unity draws as a new rejection/outage mechanism.**
   Replace `P0` by `P0+P1(1-F1)`, retain `P1 f_X(t)` below 1, and retain
   positive-power moments `P1 J_q`. This changes the outage probability and
   protocol; it cannot be hidden in the original AoA definition.
4. **Use an energy-conserving random-field/aperture model.**
   Define collected power by an aperture integral divided by launched total
   power, so transmittance is bounded intrinsically. This is the more physical
   replacement, requiring further modeling, parameters, and validation.

Allowing `X>1` without qualification gives a normalized local intensity-gain
law, but it is not a pure-loss power-transmittance law for CV-QKD. A 1.588%
probability deficit cannot be dismissed as floating-point error.

## 2. Eq. (8) to Eq. (10) is exact at rho=0, not for general Rician pointing

Binh physical PDF p. 2 Eqs. (6)--(8) correctly give a Rician radius when
`(X,Y)` are independent equal-variance Gaussian coordinates with nonzero mean.
Their transformation to Eq. (8) yields the exact raw pointing moment

\[
E[\eta_p^q]
=A_0^q\frac{a}{a+q}
\exp\left[-\frac{q\rho^2}{2\sigma_s^2(a+q)}\right],\quad q\ge0.
\]

Assuming independent lognormal scintillation, the exact raw active moment is

\[
E[X^q]
=B^q\frac{a}{a+q}e^{v(q^2-q)/2}
\exp\left[-\frac{q\rho^2}{2\sigma_s^2(a+q)}\right].
\]

In contrast, full-support integration of Binh physical PDF p. 3 Eq. (10), using
the printed `C1,C3,mu`, implies

\[
E_{(10)}[X^q]
=B^q\frac{a}{a+q}e^{v(q^2-q)/2}
\exp\left[-\frac{2q\rho^2}{w_{eq}^2}
+\frac{8q^2\rho^2\sigma_s^2}{w_{eq}^4}\right].
\]

These expressions are equal at `rho=0`. For `rho>0`, the latter exponent is
only the first two terms of the former's expansion in `q/a`, not its exact
value. In particular, at `v=0` the exact pointing loss has support
`(0,A0]`, whereas Eq. (10)'s nonzero-rho Gaussian component creates a positive
tail above `A0`. Eq. (10) can even predict an increased mean pointing power
with increased boresight for some `a`, contradicting Eq. (6).

The source of this discrepancy can be exhibited directly. Write
`r^2=(X_0+rho_x)^2+(Y_0+rho_y)^2`. The logarithm of pointing loss contains a
central quadratic term `-2(X_0^2+Y_0^2)/w_eq^2` and a Gaussian linear term
`-4(rho_x X_0+rho_y Y_0)/w_eq^2`. Eq. (10) is precisely the
lognormal-minus-exponential law obtained by treating these two terms as
independent. They depend on the same Gaussian coordinates, and are not
independent. This is an inferred derivation of the printed approximation;
the manuscript gives no approximation or independence qualification.

Recommended minimal paper correction: since its numerical defaults use
`rho_x=rho_y=0`, explicitly restrict the closed Eq. (10) and Lemma 1 to zero
boresight. If nonzero boresight is claimed, keep Eq. (8) and use the exact
convolution

\[
f_X(x)=\int_0^{A_0}\frac1{\eta_{atm}u}
f_{I_a}\left(\frac{x}{\eta_{atm}u}\right)f_{\eta_p}(u)\,du.
\]

The saved `rho=.2` independent integration test merely verifies the integral
of Eq. (10) against its own closed moments. It does not verify Eq. (8) to
Eq. (10) for Rician pointing. No new test was run here.

Historical `closed_form_channel_moments` has still different nonzero-rho
corrections at `scripts/calculate_channel_pdf_and_moments.py:461-470`:
`exp[rho^2(1-a)/(2 sigma_s^2 a^2)]` for `q=1` and
`exp[rho^2(1-2a)/(8 sigma_s^2 a^2)]` for `q=1/2`.
They do not match the exact Rician moments above. This issue is inactive in
the stored D55 data because `rho=0`; do not rewrite historical values.

## 3. Amplitude versus power in the channel handoff

Binh PDF p. 3 Eq. (11) defines `eta_f=E[sqrt(eta)]`, but inserts it as power
in Bob's modulation term. DBL physical PDF p. 13, immediately above Eq. (14),
explicitly uses an output displacement `sqrt(T) alpha` and output variance
`1+T xi`. Power transmittance is `T`, not its square root.

For a normalized physical fading law, the channel-layer identity is

\[
m_1=E[T],\quad m_h=E[\sqrt T],\quad
T_{eff}=m_h^2,\quad v_h=m_1-m_h^2\ge0,
\]

\[
N_{fade}=v_hV_A+E[T\epsilon_{ch}],\qquad
1+T_{eff}V_A+N_{fade}=1+m_1V_A+E[T\epsilon_{ch}].
\]

This is a moment-matching channel interface, not a security proof or a claim
that a Gaussian likelihood has the same MI as the fading mixture. The
literal backend follows the paper's unsquared value at
`src/manuscript_literal_3moments.py:161-188,264-275`. Keeping the same `v_h`
while using `m_h` in place of `m_h^2` adds an artificial
`(m_h-m_h^2) V_A` term to Bob's second moment. Define either an amplitude
`g_f=m_h` or power `T_f=m_h^2`, and use the distinction consistently.

The noise product `E[T epsilon_ch]` must be distinguished from
input-referred **total** line/detector noise and the heterodyne measurement
vacuum. The code's Eq. (14) reproduction uses the latter; its saved
`mean_eta_xi=2.619955...` is not equivalent to the historical
`mean_T_epsilon=.005195940...`. Detector bookkeeping needs the security
review; the propagation layer should pass separate declared quantities.

## 4. Turbulence and aperture averaging: differences and unresolved sources

Binh PDF p. 2 Eq. (5) explicitly places raw `sigma_R^2` in the lognormal
density. In weak point-receiver scintillation this approximates log-intensity
variance. In general, for a mean-one lognormal with log variance `v`,
`SI=E[I^2]/E[I]^2-1=exp(v)-1`; thus `v=ln(1+SI)`.

Satellite PDF pp. 6--7 Eqs. (31)--(32) explicitly account for aperture
averaging and distinguish `sigma_I^2(Dr)` from raw Rytov variance. Its Eq.
(31) is a threshold/outage-quantile loss budget, not a full channel PDF and
not another deterministic factor to multiply into a stochastic fading model.

The literal backend knowingly uses raw `sigma_R0_squared` at
`src/manuscript_literal_3moments.py:82-97`; historical channel code uses
`v_sc=A_ap sigma_R0_squared` at `src/channel/scintillation.py:79-135` as a
weak-turbulence finite-aperture approximation. The historical receipt stores
`sigma_X2=.00039536014503027954`, meaning `v_sc=4 sigma_X2`, while the literal
fixture stores `sigma_R2=.0539620777961657`. This is a substantive model
difference, not numerical tolerance. The literal fixture also uses the D55
experiment geometry, not the manuscript's `Dr=.08m` default on p. 4.

Choose and justify a **single** finite-aperture log-intensity model with an
explicit source and regime. Do not silently replace raw Rytov by aperture
variance in a literal reproduction. For a corrected physical model, use
consistent chosen `v` in density, PDF coefficients, moments, and Monte Carlo.
The current aperture-integral weighting also needs source checking: its
Rytov integral uses `h-h_UAV`, while aperture `Phi` uses absolute `h`
(`scintillation.py:80-124`). For an elevated receiver this cannot be certified
merely by calling both formulas Hufnagel--Valley.

## 5. Aperture beam width, G_d, and double counting

Binh PDF p. 2 Eq. (6) uses `w_L,eff` in both `nu`, `A0`, and `w_eq`. The
literal adapter follows this at `manuscript_literal_3moments.py:90-94`.
Historical `manuscript_pointing_parameters` uses unbroadened `w_L` in `nu/A0`
but broadened `w_L sqrt(1+G_d)` in `w_eq`
(`src/channel/pointing_error.py:148-168`). These are different aperture models.

The PDF says `G_d can be found in []`, with an unresolved citation. Neither
of the two supplied reference papers derives the G_d formula used by the
code. The current helper implements

\[
G_d=4.35\Lambda_b^{5/6}k^{7/6}\Delta h^{5/6}
\sec^{11/6}\zeta\int_{h_U}^{h_H}C_n^2(h)
\left(\frac{h-h_U}{\Delta h}\right)^{5/3}dh,
\quad \Lambda_b=\frac{2L}{k w_L^2}.
\]

It is dimensionless (`C_n^2` has units `m^(-2/3)`, the integral has
`m^(1/3)`, the remaining dimensional prefactor has `m^(-1/3)`), but dimensional
consistency does not verify its wave-type/direction/regime attribution.
Resolve the primary source, exact path coordinate, downlink applicability,
and whether `w_L,eff` is a long-term or short-term radius. If G_d already
contains beam-wander broadening, adding an independent wander displacement
again can double count turbulence. A primary definition is missing, so this
is a source gap, not a proved wrong constant.

## 6. Validity, generation recipe, checks, and handoff

**Geometry/loss:** planar `L=(h_H-h_U) sec(zeta)` is valid at moderate zenith
angles on short HAP paths; use `0<=zeta<pi/2`, `h_H>h_U`, consistent radians,
and `L>=h_H-h_U`. It has no Earth curvature or trajectory. The zenith
transmittance `tau_zen` must refer to the same altitude interval; a
ground-to-20km atmospheric value cannot automatically represent UAV1km-to-
HAP20km. Do not import Satellite Eq. (29) far-field telescope loss alongside
the Gaussian-aperture `eta_p`; both include aperture/geometric coupling.

**Turbulence:** weak lognormal approximations require declared weak Rytov
regime, commonly `sigma_R^2` well below 1, and a validated finite-aperture
mapping. At stronger regimes change the physical model with an explicit
source, rather than extending Eq. (5) silently. The saved reference raw
Rytov value is about .054, but this alone does not validate all larger-zenith
distances.

**Pointing/AoA:** Rician/Rayleigh requires independent isotropic Gaussian
transverse components. Unequal x/y variances do not become exactly Rician by
averaging them, as current `derive_physical_inputs:140-143` does. The stated
variance `sigma_s^2=sigma_h^2+L^2 theta_jt^2` is per coordinate. Rayleigh AoA
outage uses per-coordinate angular `sigma_o`, and `theta_FOV` is the
**half-angle**. Independent `AoA`, pointing, scintillation, and jitter
factorization is an assumption: common UAV orientation or a common
turbulent field can couple these variables. Then use joint moments
`E[B_AoA X^q]`, not `P1 E[X^q]`.

**Proposed MC recipe, not executed:** for each declared stationary geometry
state draw independent `N_I,X,Y,N_theta_x,N_theta_y` only if that independence
model is adopted. Set `I=exp(-v/2+sqrt(v) N_I)`,
`r=hypot(rho_x+sigma_s X,rho_y+sigma_s Y)`,
`Hp=A0 exp(-2r^2/w_eq^2)`, and
`B_AoA=1[hypot(sigma_o N_theta_x,sigma_o N_theta_y)<=theta_FOV]`.
Form `X_raw=eta_atm I Hp`, apply the explicitly chosen physical-support law,
and set `T=B_AoA X_physical`. For active conditioning, rejection-sample the
**joint** `(I,r)` until `X_raw<=1`; sampling conditioned I and pointing
independently is not equivalent. I.i.d. draws are a marginal Monte Carlo
model, not a time-correlated UAV trajectory. Temporal claims require
velocity, stabilization bandwidth, turbulence coherence time, and a specified
correlation process, which are not supplied.

**Checks that should later be run under separate authorization:**

- Total continuous mass plus all atoms equals 1; show outage as a separate
  atom/bar, active histogram or CDF, and raw `Pr(X_raw>1)`.
- `0<=T<=1`, `0<=m_h^2<=m_1<=1`, and normalized mass before computing a
  variance. Subprobability integrals should not be called expectations.
- Plot lognormal `ln(I)` versus Normal and Rician `r` CDF/quantiles; compare
  q=1/2,1,2 raw moments against the exact formula above. This distinguishes
  correctness of Eq. (8) from self-consistency of Eq. (10).
- `rho=0` gives Rayleigh; `v=0` gives no scintillation; `sigma_s->0` gives
  deterministic boresight loss; `theta_FOV->infinity` gives zero AoA outage.
- `C_n^2->0` gives `v->0,G_d->0` and removes broadening; larger aperture
  should improve collection under the chosen model. Avoid `C3` singularity
  by using the degenerate analytic distribution in the zero-v, zero-rho
  limit, not an arbitrary epsilon.
- Plot instantaneous components and, if temporal modeling is adopted, their
  autocorrelation and cross-correlations rather than claiming physical
  independence from marginal agreement.

**Exactly what to pass downstream:** geometry `(L,zeta)`, atmospheric power
factor, beam/aperture parameters and provenance, chosen log variance, pointing
and AoA parameters, the explicitly normalized mixed law and atoms, raw
over-unity tail, instantaneous **power** T and excess-only epsilon_ch for
statewise evaluation, and for an unconditional moment model
`m1=E[T]`, `mh=E[sqrt(T)]`, `m_epsilon=E[T epsilon_ch]`,
`T_eff=mh^2`, `Var_sqrtT=m1-mh^2`. Keep detector efficiency/electronic noise,
total input-referred line noise, and ideal heterodyne measurement noise
separate. Also pass whether the ensemble depends on instantaneous channel
state; simple unconditional moment factorization requires a fixed ensemble
or a separately justified conditioning scheme. Do not pass `mh` into a
power-transmittance API or substitute raw moments for retained-law moments.

Channel conclusions do not optimize QAM, change stored C,w, certify the
DM-CV-QKD theorem mapping, or assign an operational security claim.
