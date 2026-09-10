# Channel-state distribution

Status: the pre-action contract, composite-channel architecture, physical-domain
admission, and post-action phase-noise transformation are implemented in
source. Target runs remain parameter-blocked until the unresolved profile,
aperture, AoA, and common-turbulence phase mappings are frozen.

## Pre-action state

For every sampled realization,

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

The active domain keeps \(0\le T\le1\), with \(T=0\) reserved for the AoA
outage atom. It records \(p_{>1}=P(T_{\mathrm{raw}}>1)\), raw and physical
means, and the relative mean discrepancy. Active states use the
truncated-renormalized law on \(0<T\le1\); no pointwise saturation or floor is
used. An AoA outage has \(B_{\mathrm{AoA}}=0\), \(T=0\), and zero key rate.

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

For non-outage states, the policy receives only

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

The active implementation composes eta_atm, normalized lognormal
\(H_{\mathrm{sc}}\), generalized Rician \(H_{\mathrm p}\), and a hard AoA
gate, then admits only physical \(T\). The scalar
cn2_m_minus_two_thirds is not used as active beam-wander input. The canonical
phase API is present, but the production common-turbulence mapping/value is
unresolved and target entry points fail closed. An explicit v_sc_override is
available for non-publication fixtures; no aperture law is inferred. The
policy receives only positive-\(T\) states and never evaluates log10(0).

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
  The active record binds geometry, wavelength, visibility, profile/scintillation
  status, jitter conventions, boresight, AoA status/FOV, and raw-\(T\) treatment.

Do not pass received-power SNR, detector-output noise, or epsilon_total as a
policy input.
