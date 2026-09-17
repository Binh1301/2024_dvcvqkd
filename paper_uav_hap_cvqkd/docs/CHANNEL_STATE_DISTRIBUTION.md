# Channel-state distribution

Status: the pre-action contract, composite-channel architecture, physical-domain
admission, and post-action phase-noise transformation are implemented in
source. The attached manuscript Hufnagel–Valley/finite-aperture scenario is
resolved for channel-only (T) diagnostics; common-turbulence phase mapping and
security runs remain blocked.

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
\(H_{\mathrm{sc}}\), exact PDF5 Rician-derived \(H_{\mathrm p}\), and a hard AoA
gate, then admits only physical \(T\). The scalar
cn2_m_minus_two_thirds is not used as active beam-wander input. The canonical
phase API is present, but the production common-turbulence mapping/value is
unresolved and target entry points fail closed. An explicit v_sc_override is
available for non-publication fixtures; no aperture law is inferred. The
policy receives only positive-\(T\) states and never evaluates log10(0).

The pointing description in this historical boundary paragraph is superseded
by the PDF5 exact Gaussian-beam path below; current code uses Eq. (36) and the
Rician-derived Eq. (37) PDF, not the former generalized-Gamma law.

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
## 2026-09-16 channel-model audit addendum


The attached manuscript scenario is now wired into the active default channel
configuration: Hufnagel–Valley profile, finite-aperture (v_{\rm sc}) mapping,
PDF5 Table-I Gaussian-beam pointing, and the explicit zero-turbulence AoA FOV
fixture.
The common-turbulence phase mapping and all security/publication workflows
remain blocked.

## 2026-09-18 PDF5 implementation update

The active default now uses the attached PDF Table-I values: `D_r=0.08 m`,
`sigma_h=1 m`, `theta_jt=15.61e-6 rad`, `sigma_o=1.5e-3 rad`, and
`theta_FOV=6.25e-3 rad`. The pointing path derives `omega_L`, `G_d`,
`omega_L_e`, `nu`, `A0`, and `omega_L_eq` from Eqs. (27)--(35), uses Eq. (36)
for `H_p`, and exposes Eq. (37) for the analytical pointing PDF. Eq. (49)
and Eq. (50) active-link PDFs are available as diagnostic utilities.

The exact 10,000-sample channel-only diagnostic is recorded in
`results/hap_uav_fso_pdf_diagnostic/diagnostic_results.json`. This update does
not alter the policy input, post-action epsilon chain, security equations,
training code, or lifecycle authorization.
