# Physical channel parameter audit

Status: **historical pre-approval audit; channel values were subsequently
author-approved and resolved on 2026-08-27**. The original table below is
retained as provenance for why approval was required; its `null` and
`AUTHOR_VALUE_REQUIRED` cells are superseded by
`AUTHOR_NUMERICAL_DECISIONS.md`, `NUMERICAL_PARAMETER_FREEZE.md`, and the
fail-closed `FROZEN_CHANNEL_DIAGNOSTICS.md` result. Its model-validity and
source caveats remain active. This audit is read against the immutable
`FINAL_MODEL_SPEC.md`, `SECURITY_SCOPE_FREEZE.md`, and
`AMPLITUDE_DOMAIN_DECISION.md`. It does not assign missing values, change the
channel model, or authorize publication-scale training.

The active propagation path is
`src/channel/state_distribution.py -> src/channel/fso_channel.py`, using
`geometry.py`, `atmospheric_loss.py`, `pointing_error.py`, and `turbulence.py`.
Production scripts require the explicitly resolved values in
`configs/default.yaml`. Dataclass defaults, unit tests, README smoke commands,
and root-level HTML visualizations remain non-publication configuration.

## Classification key

- **A ALREADY_DEFINED_AND_SUPPORTED:** an explicit frozen assumption or
  value is represented consistently in manuscript, configuration, and active
  code.
- **B PRESENT_BUT_NEEDS_SOURCE:** a value or equation is active/present, but
  the current bibliography does not adequately support its provenance or
  validity for this link.
- **C AUTHOR_VALUE_REQUIRED:** no publication value is frozen; examples and
  tests must not be promoted silently.
- **D DERIVED_FROM_OTHER_PARAMETERS:** no independent author value is
  appropriate; compute it from the listed inputs and record it in artifacts.

## Single author-review table

| Quantity | Class | Current authoritative status | Active equation/use | Units and dimensional check | Source and direct-reuse assessment | Exact author action |
|---|---|---|---|---|---|---|
| HAP altitude, `h_HAP` | **C — AUTHOR_VALUE_REQUIRED** | `null`; the manuscript only states that the HAP is above sea level. `LinkGeometry.h_hap_m=20000` is a convenience default and README/tests also use 20 km, but none is an approved experiment value. | Enters vertical separation and hence every deterministic and random loss term. Must satisfy finite `h_HAP > h_UAV`. | m; consistent. The datum must be stated (e.g. altitude above mean sea level), not only “20 km link.” | No existing cited paper directly supplies the intended HAP altitude. The Ismail UAV paper studies a ground-to-UAV range of 100--2000 m, not a HAP downlink. | Select the HAP altitude and its datum without using test performance. |
| UAV altitude, `h_UAV` | **C — AUTHOR_VALUE_REQUIRED** | `null`; `LinkGeometry.h_uav_m=0` and test value 0 m are convenience values inconsistent with an airborne receiver unless explicitly interpreted as a limiting ground-receiver case. | Enters vertical separation. Must be finite and lower than `h_HAP`. | m; consistent; use the same altitude datum as `h_HAP`. | The cited Ismail altitude/range is a ground-to-UAV scenario and is not a direct value for this HAP-to-UAV geometry. | Select the UAV hover altitude and common datum. |
| Zenith angle, `zeta` | **A — ALREADY_DEFINED_AND_SUPPORTED** | Frozen primary case `zeta=0` rad (vertical) in manuscript Eq. (20) and configs. Nonzero-angle support is explicitly non-primary. | `cos(zeta)=1` in the publication case. | rad (dimensionless); valid code domain `|zeta|<pi/2`. | This is a declared geometry assumption, not an imported atmospheric constant. | Confirm that the publication experiment remains vertical; otherwise a separate slant-path model audit is required. |
| Slant/link length, `L_link` | **D — DERIVED_FROM_OTHER_PARAMETERS** | Not independently selectable. | Vertical manuscript Eq. (1): `L_link=h_HAP-h_UAV`. Code extension: `L_link=(h_HAP-h_UAV)/cos(zeta)`, which reduces exactly to Eq. (1) at the frozen `zeta=0`. | m. Division by dimensionless cosine preserves m. | No external numerical reuse is needed. | Record the derived value and equation in every run artifact; do not enter a conflicting independent length. |
| Wavelength, `lambda` | **C — AUTHOR_VALUE_REQUIRED** | `null`. Tests/smoke and legacy HTML use 1550 nm only as examples. | Enters Kruse extinction and `z_R=pi W0^2/lambda`. | Code input m; converted exactly to nm for Kruse. Must be finite and positive. | The cited Ismail paper reports 1550 nm, a standard telecom candidate, but its link is ground-to-UAV, GMCS, 100--2000 m, and includes other receiver assumptions. Reuse is plausible only as an explicit author choice, not automatic evidence for the complete HAP scenario. | Approve the wavelength and ensure the visibility/extinction source is valid at that wavelength. |
| Transmitter beam-waist radius, `W0` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests use 0.0626 m; legacy HTML uses 6.26 cm. These are unreferenced examples. | `z_R=pi W0^2/lambda`; `W_L=W0 sqrt(1+(L_link/z_R)^2)`; also enters beam-wander variance. | m; both derived radii are m. Must be positive. `W0` is a radius, not diameter. | Ismail reports `w0=1.57 cm` for a much shorter ground-to-UAV link. Direct reuse at a HAP slant range is not defensible without a transmitter/telescope design rationale. | Approve a transmitter-side 1/e2 intensity radius and document the transmitter optics that support it. |
| UAV receive-aperture radius, `a_UAV` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests use 0.2 m while legacy HTML and Ismail use 0.075 m; the repository therefore contains conflicting non-authoritative examples. | Sets centered aperture collection `T0^2`, pointing shape/scale, and (under the frozen motion equation) the orientation contribution to `sigma_UAV^2`. | m; must be positive. It is a radius, not diameter. | Ismail reports 7.5 cm in a ground-to-UAV model. It may be a hardware candidate but is not directly transferable without an airborne receiver/telescope rationale. | Approve the aperture radius and verify that the same physical aperture is intended in both collection and motion equations. |
| Meteorological visibility, `V` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests use 10 km; legacy HTML uses 10.94 km. Neither is frozen. | Enters the piecewise Kruse exponent and extinction coefficient. | km, exactly as required by the implemented formula; finite and positive. | The legacy 10.94 km is traceable numerically, not bibliographically: with 1550 nm and `q=1.3`, it gives about 0.4038 dB/km, matching Ismail's 0.4 dB/km. Ismail specifies extinction directly and over 100--2000 m; treating the inferred visibility as homogeneous over a HAP path is not scientifically defensible without author justification. | Approve a visibility/clear-sky scenario or replace it only through a separately approved model change; do not use the test or legacy value by default. |
| Kruse/Beer--Lambert handling | **B — PRESENT_BUT_NEEDS_SOURCE** | Fully implemented and stated in manuscript Eqs. (7)--(9), but the manuscript bibliography contains no primary Kruse/visibility-model citation. It assumes one spatially homogeneous extinction coefficient over the full path. | `q(V)={1.6,1.3,0.585 V^(1/3)}` and `xi=(3.912/V_km)(lambda_nm/550 nm)^(-q)` in km^-1; `eta_atm=exp(-xi L_km)`. | The wavelength ratio and exponent are dimensionless; `xi L_km` is dimensionless. Code `xi` is a Napier extinction coefficient, not dB/km. Convert by `alpha_dB/km=(10/log(10))xi ~=4.343 xi`. | The current manuscript says “Kruse” but does not cite the primary/authoritative source or delimit its wavelength/weather validity. The cited Ismail paper uses `exp(-alpha L)` with `alpha=0.4 dB/km`; importing that number without the dB-to-Napier conversion would be wrong. | Add/verify the primary Kruse-model citation and state the homogeneous clear-air validity assumption. Confirm whether visibility or a directly sourced extinction coefficient is the experiment input. |
| Extinction coefficient, `xi` | **D — DERIVED_FROM_OTHER_PARAMETERS** | No independent config field in the active model. | Derived from approved `(V,lambda)` by the equation above. | km^-1 in the natural exponential. | If the author instead approves a measured/source value in dB/km, conversion and a model amendment must be explicit. | Record both km^-1 and dB/km in metadata; do not enter both visibility and an inconsistent coefficient. |
| Refractive-index structure parameter, `C_n^2` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests/legacy HTML use `1e-15 m^-2/3`; Ismail reports `1e-16 m^-2/3`. Neither is approved for this HAP path. | Constant-`C_n^2` beam-wander variance `sigma_turb^2=1.919 C_n^2 L_link^3 (2W0)^(-1/3)/cos^4(zeta)`. | m^-2/3. Product is `m^(-2/3+3-1/3)=m^2`; dimensionally correct. | Ismail's value is for a ground-to-UAV 100--2000 m study. A constant value over a HAP-to-UAV path ignores altitude dependence and cannot be reused directly without declaring a homogeneous-path sensitivity scenario. | Approve a constant sensitivity value/range and cite its applicability, or authorize an altitude-profile model as a genuine model amendment. |
| Translational jitter, `sigma_x` | **B — PRESENT_BUT_NEEDS_SOURCE** | 0.0521 m in manuscript Table I, config, and `UavMotion`. | Contributes as `sigma_x^2` to `sigma_pos^2`. Components are treated as independent, zero-mean Gaussian standard deviations. | m; squared term m2. | The manuscript attributes the receiver-motion model to Ismail, DOI below, but the accessible primary article gives the aggregate equation and does not report this exact six-value table. Direct provenance is therefore unverified. | Provide the exact primary measurement/platform source for 5.21 cm or explicitly adopt it as an author-defined sensitivity value. |
| Translational jitter, `sigma_y` | **B — PRESENT_BUT_NEEDS_SOURCE** | 0.0502 m in manuscript Table I, config, and `UavMotion`. | Contributes as `sigma_y^2`. | m; squared term m2. | Same unresolved provenance as `sigma_x`. | Source or explicitly approve 5.02 cm. |
| Translational jitter, `sigma_z` | **B — PRESENT_BUT_NEEDS_SOURCE** | 0.0703 m in manuscript Table I, config, and `UavMotion`. | Contributes directly as `sigma_z^2` to a receiver-plane displacement variance. | m; squared term m2. The units close, but mapping motion along the nominal propagation axis directly into transverse misalignment is a physical modeling assumption that needs the cited derivation/coordinate definition. | The cited article does not substantiate the exact number or resolve the coordinate interpretation. | Source or explicitly approve 7.03 cm and define the UAV body/world axes relative to the optical axis. |
| Pitch jitter, `sigma_theta` | **B — PRESENT_BUT_NEEDS_SOURCE** | `2.60e-3` rad in manuscript Table I, config, and `UavMotion`. | Enters `a_UAV^2 sigma_theta^2`. | rad is dimensionless; after multiplication by `a_UAV^2`, term is m2. | Exact value and use of aperture radius as the angular-to-linear lever arm are not established by the current citation. | Source or explicitly approve 2.60 mrad and the lever-arm model. |
| Roll jitter, `sigma_phi` | **B — PRESENT_BUT_NEEDS_SOURCE** | `2.04e-3` rad in manuscript Table I, config, and `UavMotion`. | Enters `a_UAV^2 sigma_phi^2`. | Dimensionally m2 after scaling. | Same unresolved provenance/model dependence as pitch. | Source or explicitly approve 2.04 mrad. |
| Yaw jitter, `sigma_psi` | **B — PRESENT_BUT_NEEDS_SOURCE** | `4.06e-3` rad in manuscript Table I, config, and `UavMotion`. | Enters `a_UAV^2 sigma_psi^2`. | Dimensionally m2 after scaling. | Same unresolved provenance/model dependence as pitch. | Source or explicitly approve 4.06 mrad. |
| Aggregate UAV variance, `sigma_UAV^2` | **D — DERIVED_FROM_OTHER_PARAMETERS** | Computed, not independently configured. | `sigma_x^2+sigma_y^2+sigma_z^2+a_UAV^2(sigma_theta^2+sigma_phi^2+sigma_psi^2)`. | m2; radians are dimensionless. | Follows manuscript Eq. (18), subject to the source/interpretation dependencies above. | Record the derived value; do not substitute the legacy scalar `sigma_UAV=10.2 cm`, which uses a different simplified interface. |
| Boresight offset | **A — ALREADY_DEFINED_AND_SUPPORTED** | Exactly zero; manuscript explicitly neglects systematic boresight and active sampler draws a zero-mean Rayleigh radial displacement. | `r_x,r_y iid~N(0,sigma_axis^2)`, hence `r~Rayleigh(sigma_axis)`. Nonzero boresight would require a Rician radial law and code/model change. | Offset would be m; active value is exactly 0 m. | This is an explicit model assumption, not a measured platform claim. | Confirm zero-boresight as the idealized primary scenario. Do not describe the active law as Rician. |
| Fixed transmitter/receiver optical efficiencies | **C — AUTHOR_VALUE_REQUIRED** | No `eta_tx`, telescope throughput, coupling/optical-train efficiency, or fixed receiver efficiency factor exists in the channel sampler. Their omission is mathematically equivalent to a unit fixed optical-throughput factor outside atmospheric/aperture loss. Detector efficiency is separately excluded by the ideal-heterodyne security model and must not be inserted here. | Active `T=eta_atm eta_point` only. A nonunit fixed optical factor would change physical `T` and needs an explicit model/code amendment. | Dimensionless power efficiencies in `(0,1]`; products remain dimensionless. | Ismail reports detection efficiency 0.5, but that belongs to a different trusted-detector/security model and is not reusable as propagation throughput. | Explicitly approve the ideal unit fixed-throughput assumption, or provide sourced optical-train factor(s) and authorize the required implementation amendment. |
| Excess-noise lower bound, `epsilon_min` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests use `5e-4` SNU only as smoke values. | Lower endpoint of the independent bounded-uniform sensitivity domain; must satisfy `0 <= epsilon_min < epsilon_max`. | Input-referred SNU, dimensionless under the frozen SNU convention. | Neither cited channel reference supplies bounds compatible with the active ideal-detector, discrete-modulated asymptotic calculation. Ismail's electronic/phase/attack noises belong to a different GMCS finite-size model and cannot be copied. | Approve a non-test lower bound with physical or declared sensitivity rationale. |
| Excess-noise upper bound, `epsilon_max` | **C — AUTHOR_VALUE_REQUIRED** | `null`. README/tests use `5e-3` SNU only as smoke values. | Upper endpoint; must strictly exceed `epsilon_min`, ensuring nonzero variance. | Input-referred SNU; dimensionless. | Same non-reuse conclusion as `epsilon_min`. | Approve a finite upper bound independently of test performance. |
| Excess-noise law | **A — ALREADY_DEFINED_AND_SUPPORTED** | Frozen as `Uniform[epsilon_min,epsilon_max]`, with both endpoints unresolved. It is explicitly a sensitivity-domain distribution, not an empirical atmospheric law. | Generated by `IndependentUniformExcessNoise` from a dedicated namespaced RNG stream. | Valid normalized density has units `SNU^-1`; sampled `epsilon>=0`. | No claim of measured uniformity is made. The defensible basis is transparent sensitivity coverage when no measured law exists. | Confirm the sensitivity-study interpretation; only the endpoints require values. |
| `T`--`epsilon` dependence | **A — ALREADY_DEFINED_AND_SUPPORTED** | Independent by construction: `D(T,epsilon)=p_FSO(T)p_epsilon(epsilon)`. | Separate seed namespaces; empirical sample correlation is diagnostic only. | Both variables dimensionless; no unit issue. | The manuscript/channel sources provide no measured or mechanistic coupling. Independence avoids inventing one but is not evidence that a real link is independent. | Retain and state independence unless joint measurements or a cited mechanism justify a preregistered amendment. |

## Implemented channel equations and validity boundary

For the frozen vertical scenario,

\[
L=h_{\rm HAP}-h_{\rm UAV},\quad
\eta_{\rm atm}=\exp[-\xi(\lambda,V)L_{\rm km}],
\]

\[
z_R=\frac{\pi W_0^2}{\lambda},\qquad
W_L=W_0\sqrt{1+(L/z_R)^2},\qquad
T_0^2=1-\exp(-2a_{\rm UAV}^2/W_L^2),
\]

\[
\sigma_{\rm axis}^2=\sigma_{\rm turb}^2+\sigma_{\rm UAV}^2,
\quad r\sim {\rm Rayleigh}(\sigma_{\rm axis}),
\quad T=\eta_{\rm atm}T_0^2\exp[-(r/R)^\Gamma].
\]

Here `T` is instantaneous **power transmittance**, not optical field amplitude,
received-power SNR, or RF Friis loss. Gaussian diffraction plus finite-aperture
collection already supplies the geometric spreading; adding a separate
`1/L^2` free-space factor would double count it.

The active model is valid only as the declared homogeneous-clear-air,
fundamental Gaussian-beam, circular-aperture, zero-boresight, constant-`C_n^2`
beam-wander sensitivity model. It does **not** model log-normal,
Gamma--Gamma, or Malaga scintillation; Rytov variance is not computed, so the
code cannot claim a verified weak/moderate/strong scintillation regime. It
also omits turbulence-induced beam broadening beyond centroid wander,
altitude-dependent atmospheric profiles, clouds, explicit fog microphysics,
background light, tracking-loop dynamics, fixed optical-train efficiencies,
and temporal correlation. Samples are iid Monte Carlo states, not a UAV
trajectory.

## Repository candidates that must not be silently promoted

1. The active README/tests use `(h_HAP,h_UAV,lambda,V,W0,a,C_n^2) =
   (20 km,0,1550 nm,10 km,6.26 cm,20 cm,10^-15 m^-2/3)` and
   `(epsilon_min,epsilon_max)=(5e-4,5e-3)` solely for software smoke tests.
2. The root HTML visualization uses `(L,lambda,V,W0,a,C_n^2) =
   (20 km,1550 nm,10.94 km,6.26 cm,7.5 cm,10^-15 m^-2/3)` and a simplified
   scalar `sigma_UAV=10.2 cm`. It is legacy, uncited, and not the active
   six-component motion model.
3. Ismail *et al.* report a ground-to-UAV range 100--2000 m, 1550 nm,
   `C_n^2=10^-16 m^-2/3`, `w0=1.57 cm`, `alpha=0.4 dB/km`, and
   `a=7.5 cm`. These are useful comparison candidates, but direct reuse as a
   20 km-class HAP-to-UAV scenario is not defensible. Its detection efficiency
   and electronic/phase noises are also outside the frozen ideal-detector
   channel convention.
4. Sayat *et al.* concern a LEO satellite-to-ground CV-QKD scenario. That
   reference supports context, not the missing HAP/UAV hardware and weather
   values.

Primary publication links used to verify the existing references:

- T. Ismail, A. H. Sabeeh, M. Yasser, and N. Alshaer, “Finite-Size and
  Modulation Optimization in CV-QKD Over UAV-Based FSO Link With Adaptive
  Optics,” *IEEE Communications Letters*, 29(12), 3033--3037 (2025),
  [DOI 10.1109/LCOMM.2025.3624071](https://doi.org/10.1109/LCOMM.2025.3624071).
  The current manuscript's “Jan. 2025” reference should be updated to the
  final bibliographic record. The article supports the aggregate UAV variance
  equation but not the six exact motion values in the manuscript table.
- M. T. Sayat *et al.*, “Satellite-to-Ground Continuous Variable Quantum Key
  Distribution: The Gaussian and Discrete Modulated Protocols in Low Earth
  Orbit,” *IEEE Transactions on Communications*, 72(6), 3244--3255 (2024),
  [DOI 10.1109/TCOMM.2024.3359295](https://doi.org/10.1109/TCOMM.2024.3359295).

## Dimensional and limiting-case audit

- All active exponents are dimensionless; the turbulence expression returns
  m2, the pointing scale `R` returns m, and `T` is a dimensionless power ratio.
- `r=0` must give `T=eta_atm T0^2`; increasing `r` must decrease `T`.
- `a_UAV -> infinity` gives `T0^2 -> 1`; `V -> infinity` gives
  `eta_atm -> 1` within the empirical Kruse formula; `C_n^2 -> 0` removes only
  the turbulence beam-wander contribution.
- Setting all motion standard deviations and `C_n^2` to zero makes
  `sigma_axis=0`. NumPy's Rayleigh sampler then produces deterministic zero,
  whereas the current public sampler rejects `C_n^2=0`; this limiting case is
  therefore an analytical check, not an accepted production input.
- A nonzero boresight must produce a Rician radial law; it cannot be represented
  by changing the Rayleigh scale.
- The conversion check for a direct attenuation input is
  `xi_Np/km=alpha_dB/km/4.342944819`. Mixing dB/km directly into
  `exp(-xi L)` is a failure mode.
- `T` must satisfy `0<T<=eta_atm T0^2<=1`. Exact underflow to zero currently
  fails closed because the adaptive network consumes `log10(T)`; no outage or
  floor convention is frozen.

## Monte Carlo generation and validation recipe

After author values are approved, generate each split with its distinct frozen
base seed. Derive independent namespaced RNG streams for transmittance and
excess noise; compute deterministic channel quantities once; draw
`r~Rayleigh(sigma_axis)` and map it monotonically to `T`; draw epsilon from its
independent uniform law; and archive arrays, seeds, hashes, support upper
bound, and all derived physical quantities. Do not time-correlate or reorder
the iid samples and then describe them as a flight trajectory.

Required validation plots/statistics are: histogram and empirical CDF of `r`
against the Rayleigh law; histogram/CDF and log-scale histogram of `T`; joint
`(T,epsilon)` scatter plus reported sample correlation; split-wise histograms;
and transmittance sensitivity plots versus visibility, aperture, beam waist,
and `C_n^2`. Check deterministic reproduction, nonzero coordinate variance,
disjoint split hashes/state pairs, support, monotonic mapping, and the Rayleigh
moments `E[r]=sigma_axis sqrt(pi/2)` and `E[r^2]=2 sigma_axis^2`.

## Manuscript/code mismatches and source dependencies

1. The manuscript says the six motion values follow the Ismail reference, but
   that article does not report those exact values. A primary platform or
   measurement source is missing.
2. The manuscript invokes the empirical Kruse law but its two-entry
   bibliography contains no Kruse/visibility-model source or wavelength/domain
   qualification.
3. The manuscript narrative says the beam is affected by atmospheric
   turbulence generally; the code includes turbulence-induced centroid wander
   only. It does not implement scintillation or verify a Rytov regime.
4. The channel geometry/optical fields are now author-approved and resolved;
   their diagnostic derivation passes. The homogeneous-path and source-scope
   limitations recorded in this audit remain manuscript disclosures.
5. Fixed optical train losses are absent, and the ideal heterodyne detector
   model must not be confused with propagation efficiency.
6. The manuscript's pilot estimation/feedback narrative is not a channel
   generator feature: downstream receives exact instantaneous oracle
   `(T,epsilon)` from iid samples, without estimation error, delay, or temporal
   correlation.
7. Nonvertical operation is not publication-audited. The code replaces the
   vertical Eq. (1) length by a slant length and also retains Eq. (19)'s
   `cos(zeta)^-4` factor. No cited derivation establishes that combined
   extension, so only the frozen `zeta=0` case is supported.

## Numerical-engineer handoff and exact downstream outputs

The numerical engineer must leave publication execution blocked until all
category-C values and all category-B source/approval dependencies are resolved.
Once resolved, it should serialize the raw approved inputs plus derived
`L_link`, `xi`, `eta_atm`, `z_R`, `W_L`, `T0^2`, `Gamma`, `R`,
`sigma_UAV^2`, `sigma_turb^2`, `sigma_axis^2`, and the physical `T` upper
bound. It must not import the smoke/legacy constants.

Pass exactly:

- to the QAM/PS/VA agent: instantaneous `[log10(T),epsilon]`, where `T` is
  power transmittance and epsilon is input-referred SNU, plus split weights and
  oracle/iid metadata; do not pass `T_eff` or SNR as a substitute;
- to the CV-QKD agent: the identical instantaneous `T` and epsilon arrays,
  together with the identical physical modulation ensemble supplied by the
  transmitter; do not fold detector efficiency, electronic noise, or an RF
  path-loss convention into either channel coordinate;
- for provenance: raw `T`, epsilon, radial displacement, physical support,
  every approved/derived channel parameter, stream seeds, realization hashes,
  and the explicit assumptions `T independent of epsilon`, `iid`,
  `zero-boresight`, and `exact CSI oracle`.
