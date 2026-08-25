# Implemented equations and conventions

## Channel

- Eq. (1): `L_link = h_HAP - h_UAV` for the vertical default. A nonzero zenith angle uses the geometric slant length and is explicitly identified.
- Eqs. (7)--(9): Kruse extinction and Beer--Lambert power transmittance.
- Eqs. (11)--(15): Gaussian beam radius, Rayleigh range, and centered aperture coupling `T0^2`.
- Eqs. (16)--(18): UAV translational/orientation displacement variance.
- Eq. (19): constant-`C_n^2` turbulence variance including `cos(zeta)^-4`.
- Eqs. (21)--(24): `sigma_axis^2 = sigma_turb^2 + sigma_UAV^2`, `r_x,r_y ~ N(0,sigma_axis^2)`, and `r ~ Rayleigh(sigma_axis)`.
- Eqs. (27)--(34): `eta_p = T0^2 exp[-(r/R)^Gamma]` and Bessel-derived `Gamma,R`.
- Eqs. (42)--(55): `T = eta_atm eta_p`; rates are evaluated per state before averaging.

No analytic PDT function is needed for the accepted direct-sampling computation. Generated values are checked against `0 < T <= eta_atm T0^2`; a floating-point underflow to exactly zero raises until the authors define an outage/floor convention compatible with `log10(T)` adaptation.

## Modulation

- Eqs. (65)--(69): deterministic 16x16 constellation in `k*16+l` order.
- Eqs. (70), (81), (86): `V_A = 2 sum_i p_i |alpha_i|^2`.
- Eqs. (72)--(80): Uniform, Binomial, and MB (`nu_MB` explicit) PMFs.
- Eqs. (141), (145)--(150): `PSNet([log10 T,epsilon])`, architecture `2-128-256`, softmax PMF.
- Eqs. (151)--(153): globally shared raw GS coordinates.
- Eqs. (154)--(160): probability-weighted centering and unit energy.
- Eqs. (161)--(168): explicit-bounds `V_A` network and `alpha=sqrt(V_A/2)x`.

Weighted normalization means PS changes normalized and physical coordinates even if raw coordinates are fixed. Only weighted energy is held fixed.

## Mutual information

`src/cvqkd/mutual_information.py` implements Eqs. (91)--(101): exact source-symbol enumeration and independent complex-AWGN Monte Carlo integration, with log-sum-exp accumulation. The noise convention is `CN(0, 1+T epsilon/2)`.

## Holevo and SKR

- Eq. (103): `tau_nm = sum_i p_i f_i,n f_i,m*`. This is the ket--bra orientation.
- Eqs. (105)--(110): `C`, `a_tau`, `w`, and `Z`.
- Eqs. (111)--(122): paper standard-form covariance and symplectic eigenvalues.
- Eqs. (123)--(126): bosonic entropy and `chi_BE`.
- Eqs. (131)--(136): `K_n=beta I_AB,n-chi_BE,n`, followed by fading averaging.

The covariance is not capped or silently made physical. Tiny within-tolerance roundoff corrections are listed in returned diagnostics; material violations raise `PhysicalityError`.
