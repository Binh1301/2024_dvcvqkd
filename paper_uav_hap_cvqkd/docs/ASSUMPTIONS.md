# Assumptions

## Physical assumptions

- The HAP is Alice/transmitter and the UAV is Bob/receiver.
- The sampled physical state uses power transmittance \(0\le T\le1\); field
  attenuation is \(\sqrt T\) on active states, while (T=0) is an outage.
- The intended raw fading factor is
  \(T_{\mathrm{raw}}=\eta_{\mathrm{atm}}H_{\mathrm{sc}}H_{\mathrm p}B_{\mathrm{AoA}}\).
  AoA outage gives \(T=0\) and \(K=0\).
- One physical altitude-dependent \(C_n^2(h)\) turbulence scenario is the
  common source for scintillation, the effective phase scalar, and optional AoA
  turbulence. The mapping from that profile to \(C_{n,\phi}^2\) is not yet
  validated; a scalar must not be treated as an independent atmosphere.
- Explicit turbulence-induced beam wandering is neglected in the active target
  model. The old constant-\(C_n^2\) equation remains only as a marked legacy
  diagnostic and is not called by the active sampler.
- \(H_{\mathrm{sc}}\) uses a normalized lognormal law only after an explicit
  \(v_{\mathrm{sc}}\) choice. The repository does not infer aperture averaging
  from \(\sigma_{R0}^2\).
- AoA turbulence is explicitly disabled unless an externally validated value
  and provenance are supplied; yaw is excluded from the orientation variance.
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
- The source implements the two-stage phase equations and records their resolved
  SI inputs/derived values in `phase_parameter_provenance`; production
  configuration remains null until an author-approved scenario value exists.
  Target entry points therefore fail closed rather than infer a value.

## Numerical assumptions

- The C4 transmitter uses 64 orbit masses, fourfold rotations, global GS, and
  one scalar physical normalization.
- The common hard peak rule is \(\max_i|\alpha_i|^2\le n_{\mathrm{peak}}\);
  the average-energy dual does not enforce it.
- Training uses raw statewise \(K\), with no statewise positive-part clipping.
- Finite-size and operational fading-block aggregation are out of scope.
- Numerical tolerances, MI convergence, source-moment support, and the moving
  full-interval \(Z\) maximization must be verified before security/SKR claims.
