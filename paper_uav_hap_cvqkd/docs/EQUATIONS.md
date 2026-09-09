# Formula reference

FINAL_MODEL_SPEC.md is the scientific source of truth. This file keeps the
formula-level notation, units, scope, and current implementation symbol in one
place.

## Pre-action state

\[
S=(T,\epsilon_{\mathrm{base}}),\qquad
0<T\le1,\qquad \epsilon_{\mathrm{base}}\ge0,
\]

\[
h=[\log_{10}(T),\epsilon_{\mathrm{base}}]^{\mathsf T}.
\]

Units: \(T\) is dimensionless power transmittance; epsilon is input-referred
SNU. Scope: exogenous state before the policy action. Code symbol: current
transmittance and sampled excess_noise_snu.

## Physical fading

\[
T_{\mathrm{raw}}=\eta_{\mathrm{atm}}H_{\mathrm{sc}}H_{\mathrm p}B_{\mathrm{AoA}}.
\]

\[
0<T\le1,\qquad
p_{>1}=P(T_{\mathrm{raw}}>1),\qquad
B_{\mathrm{AoA}}=0\Rightarrow K=0.
\]

Scope: active physical-domain realization. No pointwise min(T_raw,1) is
permitted. Code status: the current sampler implements
eta_atm * pointing_power_transmittance; scintillation, AoA outage, and raw-T
diagnostics are not implemented.

## Wavelength

\[
\lambda_m=10^{-9}\lambda_{nm},\qquad
k=\kappa=\frac{2\pi}{\lambda_m},\qquad
z_R=\frac{\pi W_0^2}{\lambda_m}.
\]

Units: \(\lambda_m,W_0,L_{\mathrm{link}},z_R\) are metres; \(\lambda_{nm}\) is
nanometres and is used only by the empirical extinction law. Code symbols:
wavelength_m and wavelength_m * 1e9 in atmospheric_loss.py. No active
propagation formula may use an ambiguous wavelength unit.

## Phase distortion

\[
\tau_{\phi2}
=2.46\,C_{n,\phi}^2\kappa^{7/6}L_{\mathrm{link}}^{11/6},
\qquad
c_\phi=\tau_{\phi2}+\frac14\tau_{\phi2}^{\,2}.
\]

\[
\xi_{\mathrm{phase}}=c_\phi V_A,\qquad
\epsilon_{\mathrm{total}}
=\epsilon_{\mathrm{base}}+c_\phi V_A.
\]

Units: \(C_{n,\phi}^2\) is \(\mathrm{m}^{-2/3}\); tau_phi2 means
\(\tau_\phi^2\); \(c_\phi,\xi_{\mathrm{phase}}\), and epsilon are dimensionless
under the SNU convention. Scope: scenario-level phase coefficient followed by
state/action-dependent post-action noise. Code status: not implemented.

## C4 transmitter

\[
q_k=\operatorname{softmax}(\ell_k),\qquad
p_{k,r}=\frac{q_k}{4},\qquad
z_{k,r}=i^r z_k,\qquad k=1,\ldots,64,\ r=0,\ldots,3.
\]

\[
\frac1{64}\sum_k|z_k|^2=1,\qquad
E_z=\sum_kq_k|z_k|^2,
\qquad
\alpha_{k,r}
=\sqrt{\frac{V_A}{2E_z}}\,i^r z_k.
\]

Units: relative prototypes are unit-RMS and dimensionless; alpha is a
coherent-state amplitude. Scope: one global GS geometry, state-conditioned PS,
and one scalar physical normalization. Code symbols:
ProbabilisticShapingNetwork, GlobalGeometricShaping, and physical_amplitudes.

## Modulation variance

\[
u=\sigma(z_\phi),\qquad
V_A=V_{\min}\left(\frac{V_{\max}}{V_{\min}}\right)^u,
\qquad 0<V_{\min}<V_{\max}.
\]

Code symbol: AdaptiveVarianceNetwork; architecture 2 -> 64 -> 1.

## Mutual information

\[
Y=\sqrt{T}\,\alpha_i+N,\qquad
N\sim\mathcal{CN}(0,\sigma_c^2),\qquad
\sigma_c^2=1+\frac{T\epsilon_{\mathrm{total}}}{2}.
\]

Scope: exact 256-symbol discrete-input enumeration with complex-AWGN Monte
Carlo. Code symbol: discrete_mutual_information. Current code uses its direct
epsilon argument, so it is aligned only after that argument is the derived
post-action value.

## Holevo source moments and full correlation interval

\[
\tau=\sum_i p_i|\alpha_i\rangle\langle\alpha_i|,
\qquad
Z_-=2\sqrt{T}C-\sqrt{2T\epsilon_{\mathrm{total}}w},
\]

\[
Z_+=2\sqrt{T}C+\sqrt{2T\epsilon_{\mathrm{total}}w},
\quad
a=1+V_A,\quad
b=1+TV_A+T\epsilon_{\mathrm{total}},
\]

\[
Z_{\mathrm{phys}}=\sqrt{ab-1-|a-b|},
\quad
I=[\max(Z_-,-Z_{\mathrm{phys}}),\min(Z_+,Z_{\mathrm{phys}})].
\]

If the interval is empty, the state fails closed. The intended value is

\[
\chi_{BE}^{\mathrm{ub}}=\max_{Z\in I}\chi_{BE}(Z).
\]

Scope: full interval, not the lower endpoint by assumption. Code symbols:
c4_gram_source_moments, standard_form_covariance, and bosonic_entropy.
Current production code evaluates only \(Z_-\); full-interval evaluation is
NOT_IMPLEMENTED.

## Secret-key rate and training

\[
K^{\mathrm{raw}}_n=\beta_{\mathrm{rec}}I_{AB,n}
-\chi_{BE,n}^{\mathrm{ub}},
\qquad
\mathcal L_{\mathrm{SKR}}=-\frac1B\sum_nK^{\mathrm{raw}}_n.
\]

No statewise \(\max(0,K_n)\) appears in the training loss. The active hard
physical constraint is

\[
\max_i|\alpha_i(S)|^2\le n_{\mathrm{peak}},
\]

separate from the average photon constraint

\[
\mathbb E[V_A/2]\le\bar n_{\mathrm{budget}},
\qquad
g_B=\operatorname{mean}(V_A/2)-\bar n_{\mathrm{budget}}.
\]

Code symbols: fading_secret_key_rate, train_step,
EnergyBudgetController, and enforce_peak_photon_constraint.
