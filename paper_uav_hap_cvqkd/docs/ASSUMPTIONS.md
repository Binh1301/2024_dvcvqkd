# Assumptions

## Physical assumptions

- The HAP is Alice/transmitter and the UAV is Bob/receiver.
- The active physical state uses power transmittance \(0<T\le1\); field
  attenuation is \(\sqrt T\).
- The intended raw fading factor is
  \(T_{\mathrm{raw}}=\eta_{\mathrm{atm}}H_{\mathrm{sc}}H_{\mathrm p}B_{\mathrm{AoA}}\).
  AoA outage gives \(T=0\) and \(K=0\).
- \(C_{n,\phi}^2\) is independently prescribed per turbulence scenario,
  fixed within that scenario, and is not derived from \(C_n^2(h)\).
- Turbulence beam wandering is neglected in the intended current model; the
  repository's existing sampler still contains a constant-\(C_n^2\) beam-wander
  term and therefore remains a code mismatch.
- The phase model is a two-stage surrogate: Rytov-based phase distortion followed
  by a CV-QKD phase-noise mapping. It is not an exact unified derivation.
- Propagation uses \(\lambda_m=10^{-9}\lambda_{nm}\). Empirical extinction may
  use \(\lambda_{nm}\); propagation may not use an ambiguous wavelength unit.

## Statistical independence assumptions

- The exogenous state is \(S=(T,\epsilon_{\mathrm{base}})\).
- \(T\) and \(\epsilon_{\mathrm{base}}\) are iid Monte Carlo coordinates and are
  independent unless a measured or mechanistic coupling is separately approved.
- epsilon_total is derived after the policy action; it is not an independently
  sampled state coordinate.
- The current input-referred base-noise sensitivity law is bounded uniform. Its
  bounds are operating-domain assumptions, not measured atmospheric coupling.

## Security assumptions

- Bob uses ideal heterodyne detection.
- Reconciliation is asymptotic reverse reconciliation with declared
  \(0<\beta_{\mathrm{rec}}\le1\).
- The same physical ensemble and the same post-action
  \(\epsilon_{\mathrm{total}}\) feed MI and Holevo.
- The intended Holevo definition maximizes over the full physically admissible
  \(Z\) interval and fails closed on an empty interval.
- Finite-key, composable-security, detector-imperfection, and general-attack
  claims are out of scope.

## CSI assumptions

- The transmitter receives exact instantaneous oracle
  \(h=[\log_{10}T,\epsilon_{\mathrm{base}}]^{\mathsf T}\).
- No estimator, feedback delay, quantization, authentication cost, or CSI error
  is modeled.
- GS is global and channel-independent; PS and \(V_A\) may depend on the state.

## Phase-noise modeling assumptions

- \(\tau_{\phi2}=2.46C_{n,\phi}^2\kappa^{7/6}L_{\mathrm{link}}^{11/6}\).
- \(c_\phi=\tau_{\phi2}+\tau_{\phi2}^2/4\).
- \(\xi_{\mathrm{phase}}=c_\phi V_A\) and
  \(\epsilon_{\mathrm{total}}=\epsilon_{\mathrm{base}}+\xi_{\mathrm{phase}}\).
- The current source/configuration does not yet implement these quantities;
  this is an explicit alignment blocker, not an inferred value.

## Numerical assumptions

- The C4 transmitter uses 64 orbit masses, fourfold rotations, global GS, and
  one scalar physical normalization.
- The common hard peak rule is \(\max_i|\alpha_i|^2\le n_{\mathrm{peak}}\);
  the average-energy dual does not enforce it.
- Training uses raw statewise \(K\), with no statewise positive-part clipping.
- Finite-size and operational fading-block aggregation are out of scope.
- Numerical tolerances, MI convergence, source-moment support, and the moving
  full-interval \(Z\) maximization must be verified before security/SKR claims.
