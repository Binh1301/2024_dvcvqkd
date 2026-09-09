# Channel-state distribution

Status: the pre-action sampling contract is implemented; the post-action
phase-noise transformation is the current model/code blocker.

## Pre-action state

For every active realization,

\[
S=(T,\epsilon_{\mathrm{base}})\sim\mathcal D,
\qquad
\mathcal D(T,\epsilon_{\mathrm{base}})
=p_T(T)\,p_{\epsilon_{\mathrm{base}}}(\epsilon_{\mathrm{base}}).
\]

The intended raw physical fading is

\[
T_{\mathrm{raw}}
=\eta_{\mathrm{atm}}H_{\mathrm{sc}}H_{\mathrm p}B_{\mathrm{AoA}}.
\]

The active domain keeps \(0<T\le1\). It records
\(p_{>1}=P(T_{\mathrm{raw}}>1)\) and does not silently saturate
\(T_{\mathrm{raw}}\). An AoA outage has \(B_{\mathrm{AoA}}=0\), \(T=0\), and
zero key rate.

The current base-noise sensitivity law is

\[
\epsilon_{\mathrm{base}}
\sim\operatorname{Uniform}(\epsilon_{\min},\epsilon_{\max}),
\qquad
0\le\epsilon_{\min}<\epsilon_{\max}.
\]

It is input-referred SNU and is a declared operating-domain distribution, not a
measured atmospheric law. \(T\) and \(\epsilon_{\mathrm{base}}\) are independent
by construction because no measured or mechanistic coupling is available.

## Policy input and post-action state

The policy receives only

\[
h=[\log_{10}(T),\epsilon_{\mathrm{base}}]^{\mathsf T}.
\]

After the policy produces \(V_A(S)\), derive

\[
\xi_{\mathrm{phase}}(S)=c_\phi V_A(S),
\qquad
H=(T,\epsilon_{\mathrm{total}}),
\qquad
\epsilon_{\mathrm{total}}
=\epsilon_{\mathrm{base}}+c_\phi V_A(S).
\]

Thus \(H\) is a derived post-action state. epsilon_total must not be sampled as
an independent coordinate and must be used consistently in MI and security.

## Current code boundary

The current implementation samples transmittance and excess_noise_snu
independently, then passes the latter unchanged to the PS,
adaptive-\(V_A\), MI, and Holevo paths. It has no phase coefficient, no
post-action epsilon construction, no scintillation factor, no AoA outage, and no
raw-transmittance diagnostic. Existing channel artifacts therefore describe the
current sampler, not the complete target distribution above.

## Split generation and reproduction

The implemented sampler uses distinct train/validation/test base seeds and
separate namespaced streams for transmittance and base excess noise. Every
realization records seeds, SHA-256 hashes, physical metadata, independence, and
iid assumptions. assert_disjoint_state_realizations rejects reused seeds,
identical realization hashes, and exact paired-state overlap.

## Downstream interface

- Policy: \(h=[\log_{10}(T),\epsilon_{\mathrm{base}}]\).
- MI and Holevo: the same \(T\), the derived
  \(\epsilon_{\mathrm{total}}\), and the identical physical ensemble.
- Provenance: raw \(T_{\mathrm{raw}}\), admitted \(T\), all fading components,
  base noise, derived phase noise, seeds, hashes, and outage/overflow counts.

Do not pass received-power SNR, detector-output noise, or epsilon_total as a
policy input.
