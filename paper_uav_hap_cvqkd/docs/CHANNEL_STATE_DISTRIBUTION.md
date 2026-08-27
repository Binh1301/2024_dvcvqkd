# Joint channel-state distribution

Status: implemented distribution contract; its numerical physical and excess-noise bounds must be recorded in the numerical-parameter freeze before publication runs.

## Definition

Every adaptive experiment uses a state

\[
s=(T,\epsilon)\sim \mathcal D,
\qquad
\mathcal D(T,\epsilon)=p_{\rm FSO}(T)\,p_\epsilon(\epsilon).
\]

The power transmittance is generated only by the frozen HAP--UAV FSO model:

\[
L=(h_{\rm HAP}-h_{\rm UAV})/\cos\zeta,
\qquad
T=\eta_{\rm atm}(L)\,T_0\exp[-(r/R_s)^\gamma],
\]

where `eta_atm` is the Kruse/Beer--Lambert power transmittance, `T0` is the on-axis aperture power coupling, and

\[
r\sim {\rm Rayleigh}(\sigma_{\rm axis}),\qquad
\sigma_{\rm axis}^2=\sigma_{\rm turbulence}^2+\sigma_{\rm UAV}^2.
\]

Consequently the physical support is

\[
0<T\le \eta_{\rm atm}T_0\le1.
\]

The excess-noise simulation law is

\[
\epsilon\sim {\rm Uniform}(\epsilon_{\min},\epsilon_{\max}),
\qquad 0\le\epsilon_{\min}<\epsilon_{\max},
\]

in input-referred shot-noise units. Its variance is

\[
\operatorname{Var}(\epsilon)=(\epsilon_{\max}-\epsilon_{\min})^2/12>0.
\]

This bounded uniform law is a declared sensitivity-domain distribution, not a claim that measured excess noise is physically uniform.

## Dependence assumption

`T` and `epsilon` are independent by construction. The frozen propagation equations specify atmospheric/pointing fading for `T` but give neither measurements nor a mechanism that maps that fading to input-referred excess noise. Coupling them would therefore invent a physical relationship. The implementation uses separate BLAKE2b-namespaced pseudorandom streams for the two coordinates. A future coupled distribution is admissible only with measured joint data or an explicit noise mechanism and a preregistered model amendment.

The generated states are iid Monte Carlo states. They do not represent a time series and must not be used to claim performance under mobility-induced temporal correlation, delayed CSI, or channel-estimation error.

## Split generation and reproduction

Training, validation, and test use distinct declared base seeds. Each base seed derives separate `joint_state_transmittance` and `joint_state_excess_noise` streams. Training epochs additionally use the existing epoch namespace. Validation and test realizations are fixed; test states are not used for optimization, hyperparameter selection, early stopping, or baseline selection.

Every realization records:

- base, transmittance, and excess-noise seeds;
- SHA-256 hashes for `T`, `epsilon`, and paired states;
- physical channel metadata and support parameters;
- the independence and iid assumptions.

`assert_disjoint_state_realizations` rejects reused base seeds, identical realization hashes, and exact paired-state overlap across named splits.

## Validity and required frozen inputs

The channel law inherits the validity limits of the frozen homogeneous Kruse attenuation, Gaussian-beam aperture, constant-`C_n^2` beam-wander, zero-boresight, and independent Gaussian UAV-displacement model. It does not add scintillation fading, clouds, fog beyond the declared visibility law, or temporal correlation.

The author-approved primary scenario now provides the HAP/UAV geometry, wavelength, 200 km nominal-good-weather visibility, beam waist, aperture radius, constant `C_n^2`, and `epsilon ~ Uniform[0.001,0.04]` SNU. These are prospective author choices recorded before convergence/testing, not values inferred from legacy or held-out results. Their derived physical diagnostics and validity limits are frozen in `FROZEN_CHANNEL_DIAGNOSTICS.md`.

## Sanity checks and downstream interface

For each split, verify support, finite values, positive sample variance in both coordinates, empirical `T` and `epsilon` histograms, the radial Rayleigh law, and deterministic hashes. Plot the joint scatter and report empirical correlation only as a finite-sample diagnostic; independence is defined by the generator, not by forcing sample correlation to zero.

Pass exactly these instantaneous quantities downstream:

- QAM/PS/VA policy: `[log10(T), epsilon]` plus the common experiment weights;
- CV-QKD MI/Holevo: the same `T`, the same input-referred `epsilon`, and the identical physical ensemble;
- channel metadata: physical-support upper bound, split/stream seeds, hashes, and exact-CSI/iid assumptions.

Do not pass received-power SNR in place of power transmittance, and do not replace input-referred `epsilon` with detector output noise.
