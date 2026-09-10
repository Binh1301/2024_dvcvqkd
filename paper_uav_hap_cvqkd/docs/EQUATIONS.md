# Formula reference

FINAL_MODEL_SPEC.md is the scientific source of truth. This file keeps the
formula-level notation, units, scope, and current implementation symbol in one
place.

## Pre-action state

\[
S=(T,\epsilon_{\mathrm{base}}),\qquad
0\le T\le1,\qquad \epsilon_{\mathrm{base}}\ge0,
\]

\[
h=[\log_{10}(T),\epsilon_{\mathrm{base}}]^{\mathsf T}.
\]

Units: \(T\) is dimensionless power transmittance; epsilon is input-referred
SNU. Scope: exogenous state before the policy action; the policy feature is
defined only on the active subset \(T>0\), while \(T=0\) is an outage state.
Code symbol: transmittance and sampled epsilon_base_snu.

## Physical fading

\[
T_{\mathrm{raw}}=\eta_{\mathrm{atm}}H_{\mathrm{sc}}H_{\mathrm p}B_{\mathrm{AoA}}.
\]

\[
0\le T\le1,\qquad
p_{>1}=P(T_{\mathrm{raw}}>1),\qquad
B_{\mathrm{AoA}}=0\Rightarrow K=0.
\]

Scope: active physical-domain realization. No pointwise min(T_raw,1) is
permitted. Active sampling rejects/resamples \(T_{\mathrm{raw}}>1\) for the
normalized \(B_{\mathrm{AoA}}=1\) law and retains the \(B_{\mathrm{AoA}}=0\)
outage atom. Composite factors and raw/physical diagnostics are implemented;
production profile, aperture, and AoA mappings remain fail-closed.

For an explicit altitude profile,

\[
\sigma_{R0}^2
=2.25\,k^{7/6}\sec(\zeta)^{11/6}
\int C_n^2(h)(h-h_{\rm UAV})^{5/6}\,dh.
\]

The active scintillation law is
\(\ln H_{\rm sc}\sim\mathcal N(-v_{\rm sc}/2,v_{\rm sc})\), so
\(\mathbb E[H_{\rm sc}]=1\). The code never assumes
\(v_{\rm sc}=\sigma_{R0}^2\); an explicit override or frozen mapping is
required.

For pointing,

\[
\sigma_{\rm UAV,trans}^2=(\sigma_x^2+\sigma_y^2)/2,\qquad
\sigma_m^2=\sigma_{\rm UAV,trans}^2+\sigma_{\rm HAP,disp}^2,
\]
\[
r_x\sim\mathcal N(\rho_x,\sigma_m^2),\qquad
r_y\sim\mathcal N(\rho_y,\sigma_m^2),\qquad
r=(r_x^2+r_y^2)^{1/2}.
\]

For AoA,

\[
\sigma_o^2=(\sigma_\theta^2+\sigma_\phi^2)/2+\sigma_{\rm turb,AoA}^2,
\qquad
p_{\rm out}=\exp[-\theta_{\rm FOV}^2/(2\sigma_o^2)].
\]

Yaw is excluded. A nonzero turbulence AoA term requires external validation
and provenance; the explicit disabled status resolves it to zero.

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

Here \(\kappa=2\pi/\lambda_m\).  With \(C_{n,\phi}^2\) in
\(\mathrm{m}^{-2/3}\), \(\kappa\) in \(\mathrm{m}^{-1}\), and
\(L_{\mathrm{link}}\) in \(\mathrm{m}\), the dimensional product is
\(\mathrm{m}^{-2/3}\mathrm{m}^{-7/6}\mathrm{m}^{11/6}=\mathrm{m}^0\).
Thus \(\tau_{\phi2}\) and \(c_\phi\) are dimensionless.  The active
`phase_parameter_provenance` record stores the SI inputs, resolved link length,
both derived values, their units, the scenario-level scope, and the explicit
common-turbulence semantics rather than independence from an altitude-dependent
\(C_n^2(h)\) profile. The validated profile-to-effective-scalar mapping remains
unresolved.

\[
\xi_{\mathrm{phase}}=c_\phi V_A,\qquad
\epsilon_{\mathrm{total}}
=\epsilon_{\mathrm{base}}+c_\phi V_A.
\]

Units: \(C_{n,\phi}^2\) is \(\mathrm{m}^{-2/3}\); tau_phi2 means
\(\tau_\phi^2\); \(c_\phi,\xi_{\mathrm{phase}}\), and epsilon are dimensionless
under the SNU convention. Scope: scenario-level phase coefficient followed by
state/action-dependent post-action noise. Code status: implemented in
src/channel/phase_noise.py and wired through the trainer; `c_phi` is derived,
not independently configured, and the author-approved scenario value remains
unresolved in config.

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
Carlo. Code symbol: discrete_mutual_information. Active callers pass the
derived post-action epsilon_total; the primitive retains its direct epsilon
argument by design.

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
c4_gram_source_moments, _maximize_bounded_scalar,
standard_form_covariance, and bosonic_entropy.
The active implementation keeps a deterministic closed-interval grid, refines
every grid cell with bounded golden-section steps, and selects the largest
evaluated value. It reports boundary/interior diagnostics and fails closed on
an empty interval or a candidate covariance physicality failure. This is
implementation evidence, not an approved numerical-certification result.

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
