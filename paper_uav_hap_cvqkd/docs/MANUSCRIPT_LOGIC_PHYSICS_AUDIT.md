# Literature-grounded logic and physics audit

**Object audited:** `C:\Users\HP\Downloads\Uav_Hap_Qam256_manuscript.md`

**Audit date:** 2026-09-09

**Scope:** adaptive 256-state discrete-modulation CV-QKD over a HAP-to-UAV FSO link

**Method:** equation-by-equation comparison with peer-reviewed literature and authoritative propagation standards; no manuscript rewriting and no publication-scale evaluation.

Line references below are line numbers in the uploaded Markdown source, not eventual typeset page numbers. “Correct” means correct under the manuscript's stated normalization and model assumptions; it does not by itself establish composable security or physical fidelity of a numerical parameter set.

## Executive conclusion

The arbitrary-modulation covariance chain in lines 2660–3219 is, at the manuscript level, substantially correct: the definitions of \(\tau\), \(\mathcal C\), \(a_\tau\), \(w\), the \([Z_-,Z_+]\) interval, the physical covariance restriction, the symplectic spectrum, the ideal-heterodyne conditional eigenvalue, and the maximization of the Gaussian Holevo quantity over the physical interval agree with Denys–Brown–Leverrier and standard Gaussian-state calculus [1,2]. The manuscript is also correct not to assume that \(Z_-\) is universally worst-case; Denys et al. explicitly say that this is typical, not proven in complete generality [1].

That positive result is outweighed by five blockers:

1. the repository's production Holevo path still evaluates only \(Z_-\), contradicting the manuscript's full-interval maximization;
2. the numerical support/pseudoinverse treatment of \(\tau^{-1/2}\) is not publication-certified and the repository lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`;
3. the quantity \(2.46 C_{n,\phi}^2 k^{7/6}L^{11/6}\) is used as a residual phase variance without a receiver-, aperture-, piston-, or compensation-specific derivation;
4. aperture averaging and the conversion from point-receiver Rytov variance to the log-irradiance variance \(v_{\rm sc}\) are not specified numerically;
5. the statewise fading average is a valid security rate only under stronger public-state, block-stationarity, parameter-estimation, and conditioning assumptions than are currently operationally defined.

**Verdict: NOT SAFE FOR PUBLICATION-SCALE RESULTS.** Prototype calculations used only to develop and validate the missing methods remain reasonable, but must not be presented as publication-scale security results.

## Classification and severity scale

The requested classifications are used literally:

- **DEFINITELY WRONG:** mathematically or physically inconsistent as stated or implemented.
- **CONDITIONALLY VALID:** correct only after specified conditions are imposed.
- **MODELING APPROXIMATION:** a defensible simplification whose range and validation must be stated.
- **MISSING ASSUMPTION:** a necessary condition is absent or not operationally defined.
- **MISSING CITATION:** the claim/equation lacks an appropriate primary or authoritative source.
- **NUMERICALLY INCOMPLETE:** the mathematics is stated but the procedure, tolerances, parameters, or validation needed to compute it are absent.

Severity is **Critical** (can invalidate the security/result claim), **High** (can materially change results or reproducibility), **Medium** (important scope/model qualification), or **Low** (mainly attribution or presentation).

## 1. Arbitrary-modulation CV-QKD security

### S1 — Density operator \(\tau\)

- **Location:** lines 2660–2680, Eqs. `tau_holevo` and `tau_holevo_qam`.
- **Equation/claim:** \(\tau_n=\sum_i p_{i,n}|\alpha_{i,n}\rangle\langle\alpha_{i,n}|\).
- **Literature check:** This is exactly the average coherent-state density operator used by Denys, Brown, and Leverrier [1].
- **Classification:** **MISSING CITATION**.
- **Severity:** Low.
- **Minimal correction:** Cite Ref. [1] at the definition and state that all \(p_i\) and \(\alpha_i\) are the final physical ensemble supplied identically to MI and Holevo calculations.

### S2 — \(\mathcal C\), \(a_\tau\), and \(w\)

- **Location:** lines 2684–2799, Eqs. `coherent_correlation`, `a_tau`, and the displayed definitions of \(w_n\).
- **Equation/claim:** \(\mathcal C=\operatorname{Tr}(\sqrt\tau,a\sqrt\tau,a^\dagger)\), \(a_\tau=\sqrt\tau,a\tau^{-1/2}\) on \(\operatorname{supp}\tau\), and the ensemble variance defining \(w\).
- **Literature check:** These match Eqs. (10)–(13) and the Gaussian-channel specialization of Ref. [1]. The support-restricted inverse is the correct mathematical object.
- **Classification:** **MISSING CITATION**; **NUMERICALLY INCOMPLETE**.
- **Severity:** Critical for computation; Low for the analytic definitions.
- **Minimal correction:** Cite Ref. [1] and preregister a converged support rule or cutoff-independent construction for \(\sqrt\tau\) and \(\tau^{-1/2}\), including precision, eigenvalue threshold, rank-change diagnostics, stress constellations, and failure conditions. A floating-point threshold must not silently redefine the mathematical support.

### S3 — \([Z_-,Z_+]\) arbitrary-modulation interval

- **Location:** lines 2804–2862, Eq. `z_correlation_interval`.
- **Equation/claim:** \(Z_\pm=2\sqrt T\,\mathcal C\pm\sqrt{2T\epsilon w}\).
- **Literature check:** Correct after substituting the phase-insensitive Gaussian-channel moments \(c_1=\sqrt T\mathcal C\), \(c_2=\sqrt T\langle n\rangle\), and \(n_B=T\langle n\rangle+T\epsilon/2\) into Ref. [1]. This substitution presumes the manuscript's coherent-state/SNU normalization and centered, quadrature-isotropic ensemble.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** Cite Ref. [1] and state the three observed moments being specialized, the input-referred-noise convention, and that the substitution is made state by state only for a stationary conditional Gaussian channel.

### S4 — A fixed lower endpoint is not generally justified

- **Location:** lines 2860–2862 and 3217–3219.
- **Equation/claim:** The manuscript retains the full interval and reduces to \(Z_-\) only when \(Z_-\) actually maximizes \(\chi_{BE}\).
- **Literature check:** Correct. Ref. [1] reports that the lower endpoint is worst in most investigated cases but explicitly notes that no general proof is known and instructs maximization over the interval in general.
- **Classification:** **MISSING CITATION**.
- **Severity:** High because this is a security-conservatism condition.
- **Minimal correction:** Cite the discussion and footnotes surrounding the covariance interval in Ref. [1]. Do not state or implement a universal monotonicity rule without a proof covering the complete adaptive domain.

### S5 — Physical covariance domain

- **Location:** lines 2876–2998, Eqs. `z_physical_condition`, `z_physical_bound`, and `physical_z_interval`.
- **Equation/claim:** For \(\Gamma_{AB}=\begin{psmallmatrix}aI&Z\sigma_z\\Z\sigma_z&bI\end{psmallmatrix}\), physicality gives \(|Z|\le\sqrt{ab-1-|a-b|}\), and the security interval is intersected with this domain.
- **Literature check:** Correct in the vacuum-variance-one convention. It is equivalent to requiring the smallest symplectic eigenvalue to be at least one [2].
- **Classification:** **MISSING CITATION**.
- **Severity:** Low analytically; High if an empty interval is numerically repaired rather than rejected.
- **Minimal correction:** Cite Ref. [2]; specify a fail-closed rule for \(Z_L>Z_U\), and permit only preregistered rounding-tolerance repairs with diagnostics.

### S6 — Symplectic eigenvalues and ideal-heterodyne conditional eigenvalue

- **Location:** lines 3000–3143, Eqs. `gamma_ab_star`, `lambda1_n`, `lambda2_n`, and `lambda3_n`.
- **Equation/claim:** \(\Delta=a^2+b^2-2Z^2\), \(\det\Gamma=(ab-Z^2)^2\), \(\lambda_{1,2}^2=(\Delta\pm\sqrt{\Delta^2-4\det\Gamma})/2\), and \(\lambda_3=a-Z^2/(b+1)\).
- **Literature check:** Correct for the stated standard form and ideal heterodyne measurement. The \(+1\) in the conditional Schur complement is the heterodyne vacuum contribution [2].
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** Cite Ref. [2] and repeat locally that detection is ideal and trusted, vacuum noise is one SNU per quadrature, and detector inefficiency/electronics are not being folded into this conditional eigenvalue.

### S7 — Gaussian Holevo function and worst-case maximization

- **Location:** lines 3147–3219, Eqs. defining \(G\), \(\chi_{BE,n}(Z)\), and `holevo_explicit_dependency`.
- **Equation/claim:** \(\chi_{BE}=G[(\lambda_1-1)/2]+G[(\lambda_2-1)/2]-G[(\lambda_3-1)/2]\), maximized over the physical correlation interval.
- **Literature check:** Correct for asymptotic reverse reconciliation with ideal heterodyne and the Gaussian extremality upper bound used in Ref. [1]. This is not by itself a finite-size or composable proof; Ref. [1] explicitly limits the result accordingly.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** High.
- **Minimal correction:** Cite Refs. [1–3] and label every reported key rate “asymptotic, collective-attack, ideal-heterodyne lower bound” unless a separate stronger proof is supplied.

### S8 — Manuscript-to-code contradiction in the worst-case Holevo evaluation

- **Location:** manuscript lines 3192–3219, 3517–3525, 5293–5325, 6462–6495; repository `src/cvqkd/holevo.py`, lines 177–183; `docs/SECURITY_SCOPE_FREEZE.md`, lines 69–70 and 172–174.
- **Equation/claim:** The manuscript specifies \(\max_{Z\in\mathcal I}\chi_{BE}(Z)\). The production implementation instead sets `z = 2*sqrt(T)*C - sqrt(2*T*epsilon*w)` and evaluates only that value.
- **Literature check:** The implementation is not generally justified by Ref. [1], and it contradicts the manuscript's own qualification.
- **Classification:** **DEFINITELY WRONG**; **NUMERICALLY INCOMPLETE**.
- **Severity:** Critical.
- **Minimal correction:** Implement a verified one-dimensional maximization over the physical interval for every state, with endpoint/interior tests, tolerances, global-search validation on the full declared domain, and adversarial regression cases where the maximizing point is not assumed in advance. Alternatively, prove lower-endpoint maximality over the entire frozen adaptive domain before retaining the current code.

### S9 — Parameter estimation is replaced by oracle channel parameters

- **Location:** lines 2048–2072 and 2804–2916.
- **Equation/claim:** The security quantities are computed from exact realization-level \(T_n\), \(\epsilon_n\), \(\mathcal C_n\), and \(w_n\).
- **Literature check:** Ref. [1] formulates the bound in terms of observable moments \(c_1,c_2,n_B\); exact Gaussian-channel substitutions are appropriate for an oracle theoretical channel but not a practical security claim. Fading postselection additionally requires many indistinguishable estimation signals within each stable subchannel [4].
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** High.
- **Minimal correction:** Call the present calculation an oracle asymptotic performance functional, or define state-bin parameter estimation, confidence bounds, sample allocation, and the conservative mapping from estimated \(c_1,c_2,n_B\) to each admissible \(Z\) interval.

## 2. HAP–UAV FSO channel

### C1 — Beer–Lambert attenuation and units

- **Location:** lines 82–99, Eq. immediately following “Atmospheric Attenuation.”
- **Equation/claim:** \(\eta_{\rm atm}=\exp[-\xi L_{\rm link}/10^3]\) with \(\xi\) in km\(^{-1}\) and \(L\) in m.
- **Literature check:** Dimensionally and mathematically correct for a spatially homogeneous, Napierian extinction coefficient. General inhomogeneous propagation uses \(\exp[-\int\xi(s)\,ds]\) [9,12].
- **Classification:** **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** State that \(\xi\) is Napierian power extinction, that weather is homogeneous over the path, and that molecular absorption and altitude variation are either included in \(\xi\) or intentionally omitted.

### C2 — Kruse model, wavelength units, and visibility convention

- **Location:** lines 101–158, Eqs. `wavelength_unit_conversion`, `kruse_coefficient`, and `q_exponent_definition`.
- **Equation/claim:** \(\xi=(3.912/V)(\lambda_{\rm nm}/550)^{-q}\) km\(^{-1}\), with the conventional piecewise \(q\).
- **Literature check:** The wavelength handling is correct and 3.912 is the Napierian coefficient \(-\ln(0.02)\), not dB/km. The formula therefore uses the historical 2% visibility convention. Current WMO meteorological optical range uses 5%, and ITU-R requires conversion; using ordinary airport/MOR visibility directly would be inconsistent [12]. Kruse is also an empirical near-surface visibility law, not a first-principles high-altitude slant-path extinction model.
- **Classification:** **CONDITIONALLY VALID**; **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** High.
- **Minimal correction:** Explicitly define \(V\) as 2%-contrast visibility or convert 5% MOR data; distinguish km\(^{-1}\) from dB/km; and justify applying a single near-surface visibility to the HAP–UAV path or integrate an altitude-dependent extinction profile.

### C3 — Hufnagel–Valley profile

- **Location:** lines 270–302, Eq. `hufnagel_valley`.
- **Equation/claim:** The standard three-term HV 5/7-type profile is used.
- **Literature check:** The functional form is standard [9,10]. Its dimensional result is m\(^{-2/3}\) when \(h\) is in metres, wind speed in m/s, and the nominal ground coefficient has units m\(^{-2/3}\).
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** Give all units, define whether \(h\) is above ground level or mean sea level, identify the reference surface for the “ground” term, and state how the profile is shifted when the UAV is not at ground level.

### C4 — Downlink point-receiver Rytov variance

- **Location:** lines 243–268, Eq. `rytov_variance`.
- **Equation/claim:** \(\sigma_{R,0}^2=2.25 k^{7/6}\sec^{11/6}\!\zeta\int_{h_{\rm UAV}}^{h_{\rm HAP}}C_n^2(h)(h-h_{\rm UAV})^{5/6}dh\).
- **Literature check:** This is the conventional plane-wave downlink expression; it reduces to the familiar 1.23 coefficient for constant \(C_n^2\) [9,11]. It is a weak-fluctuation, flat-layer/slant-geometry approximation. The manuscript does not define a numerical validity gate for weak/moderate turbulence.
- **Classification:** **CONDITIONALLY VALID**; **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** High.
- **Minimal correction:** Use \(k=2\pi/\lambda_{\rm m}\) explicitly, declare plane-wave/downlink geometry, specify allowed \(\sigma_R^2\) range, and reject or replace the lognormal/Rytov model when that range is exceeded.

### C5 — Aperture averaging and \(v_{\rm sc}\) are not defined

- **Location:** lines 160–241 and especially 304–305.
- **Equation/claim:** A finite-aperture mapping \(\sigma_{R,0}^2\mapsto v_{\rm sc}\) “is specified consistently in the numerical setup,” but no equation or setup values are provided.
- **Literature check:** Aperture averaging depends on aperture diameter, wavelength, elevation, and the vertical turbulence weighting; authoritative methods define an explicit aperture-averaging factor [9,11]. For the manuscript's normalized lognormal gain, \(\operatorname{Var}(H_{\rm sc})=e^{v_{\rm sc}}-1\), so an aperture-averaged scintillation index \(\sigma_{I,D}^2\) corresponds to \(v_{\rm sc}=\ln(1+\sigma_{I,D}^2)\), not an unspecified identity outside the weak limit.
- **Classification:** **NUMERICALLY INCOMPLETE**; **MISSING CITATION**.
- **Severity:** Critical.
- **Minimal correction:** Supply the exact aperture-averaging equation, receiver diameter, path geometry, and whether the factor acts on log-irradiance variance or scintillation index; then use the logarithmic conversion consistently and validate against a second model or phase-screen propagation.

### C6 — Diffraction-only Gaussian spot radius

- **Location:** lines 308–366, Eqs. for \(W_L\) and \(z_R\).
- **Equation/claim:** \(W_L=W_0\sqrt{1+(L/z_R)^2}\), \(z_R=\pi W_0^2/\lambda\).
- **Literature check:** Correct for an unaberrated TEM\(_{00}\) Gaussian beam in free space [9,13]. Atmospheric turbulence also causes beam spreading and deformation, which are excluded from this radius while scintillation and wander are multiplied in separately.
- **Classification:** **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** State that \(W_L\) is the diffraction-only radius and give a regime argument showing turbulence spreading/deformation is negligible, or use a turbulence-broadened/elliptic-beam PDT [6–8].

### C7 — Rician displacement and generalized pointing loss

- **Location:** lines 370–670.
- **Equation/claim:** Equal-variance independent Gaussian Cartesian jitter plus a deterministic boresight offset gives a Rician radial displacement, transformed through the generalized Gaussian-beam aperture-coupling law.
- **Literature check:** Correct under circular aperture, circular spot, equal-axis jitter, and deterministic boresight assumptions. The Rician law and nonzero-boresight pointing model are standard [13,14]; the log-negative-Weibull-type aperture coupling is standard in atmospheric quantum-channel modeling [5].
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** Cite Refs. [5,13,14] and state the circular/equal-jitter assumptions. If platform jitter is anisotropic or correlated, use Beckmann/elliptical statistics instead of Rician.

### C8 — AoA/FOV Rayleigh outage gate

- **Location:** lines 672–791.
- **Equation/claim:** Independent zero-mean equal-variance angular components give Rayleigh \(\Theta\) and \(p_{\rm out}=\exp[-\theta_{\rm FOV}^2/(2\sigma_o^2)]\).
- **Literature check:** The probability calculation is correct for the stated Gaussian angular model. A hard FOV gate is an engineering approximation; real coupling/noise varies continuously near the FOV edge, and mean angular bias would make the radius Rician rather than Rayleigh [11,14].
- **Classification:** **CONDITIONALLY VALID**; **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** Medium.
- **Minimal correction:** Define whether angular boresight bias is zero after tracking, justify independence from lateral pointing/scintillation, and report a sensitivity analysis against a smooth FOV response.

### C9 — Independence/product factorization of atmospheric effects

- **Location:** lines 39–80 and 793–958, composite \(T_{\rm raw}\) construction.
- **Equation/claim:** Deterministic loss, normalized scintillation, pointing loss, and AoA acceptance are multiplied as independent factors.
- **Literature check:** This is not generally exact: turbulence couples beam wander, spot broadening/deformation, aperture averaging, and scintillation. Modern PDT models condition one effect on another or propagate the field jointly [6–8].
- **Classification:** **MODELING APPROXIMATION**; **MISSING ASSUMPTION**.
- **Severity:** High.
- **Minimal correction:** Explicitly state independence as a weak-turbulence/engineering approximation, identify which random mechanisms are assumed independent, and compare moments/tails with an elliptic-beam, law-of-total-probability, beta-PDT, or phase-screen benchmark over the declared parameter domain.

### C10 — Treatment of \(T_{\rm raw}>1\)

- **Location:** lines 968–1184, especially Eqs. `physical_active_transmittance_pdf` and `physical_transmittance_measure`.
- **Equation/claim:** The active density is conditioned on \(0<T_{\rm raw}\le1\) and renormalized, while \(p_{\rm in}\) is retained.
- **Literature check:** The resulting probability measure is mathematically normalized and bounded, but conditioning away the unphysical tail is a new channel model, not a physical consequence of passive propagation. Bounded aperture-transmittance/PDT models avoid this problem, and the accuracy of truncated lognormal models is strongly aperture- and regime-dependent [5–8].
- **Classification:** **CONDITIONALLY VALID**; **MODELING APPROXIMATION**; **NUMERICALLY INCOMPLETE**.
- **Severity:** High.
- **Minimal correction:** Preregister a quantitative admissible threshold for \(p_{>1}\), report it for every scenario, and reject scenarios exceeding it. If the tail is material, replace the composite law with a bounded PDT; do not let renormalization hide the misspecification.

## 3. Phase-noise model

### P1 — Dimensional consistency

- **Location:** lines 1473–1508, Eq. `phase_distortion_variance`.
- **Equation/claim:** \(C_{n,\phi}^2 k^{7/6}L^{11/6}\) is used as a variance.
- **Literature check:** Dimensionally correct: m\(^{-2/3}\)m\(^{-7/6}\)m\(^{11/6}=1\). Dimensional consistency does not identify the statistic as residual coherent-detection phase variance.
- **Classification:** **MISSING CITATION**.
- **Severity:** Low by itself.
- **Minimal correction:** Retain the dimensional statement but do not use it as physical validation of the phase model.

### P2 — Rytov-based “phase variance” is not receiver-defined

- **Location:** lines 1469–1510.
- **Equation/claim:** \(\tau_\phi^2\simeq2.46 C_{n,\phi}^2k^{7/6}L^{11/6}\) is a scenario-level turbulence-induced phase-distortion variance.
- **Literature check:** Rytov statistics separate log-amplitude and phase fluctuations, while operational wavefront phase variance depends on spatial separation/aperture, piston removal, outer scale, wave type, and compensation. ITU-R characterizes coherent-aperture phase through quantities such as the Fried coherence length and explicitly warns that corrupted phase affects single-spatial-mode coherent receivers even when aperture averaging reduces amplitude scintillation [10,11]. The coefficient 2.46 is not, without further derivation, a universal residual phase-error variance for the receiver described here. Ref. [15], which uses the later excess-noise polynomial, obtains atmospheric phase statistics from phase screens rather than establishing this closed-form substitution.
- **Classification:** **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**; **NUMERICALLY INCOMPLETE**.
- **Severity:** Critical.
- **Minimal correction:** Define the optical receiver and phase reference, aperture/mode coupling, pilot/LO architecture, compensation bandwidth, piston/tilt removal, and the random variable whose variance is \(\tau_\phi^2\). Derive or calibrate it with a cited phase-structure/phase-screen model and validate the surrogate over the stated domain.

### P3 — Mapping residual phase variance to input-referred excess noise

- **Location:** lines 1514–1580, \(\xi_{\rm phase}=V_A(\tau_\phi^2+\tau_\phi^4/4)\).
- **Equation/claim:** The phase contribution is linear in \(V_A\) with coefficient \(c_\phi=\tau_\phi^2+\tau_\phi^4/4\).
- **Literature check:** This polynomial appears in the air-channel CV-QKD model of Li and Wang [15], building on a self-reference discrete-modulation receiver [16]. It is protocol-specific and approximate, not a universal identity. For a zero-mean Gaussian residual phase, exact phase averaging produces exponential forms whose input/output reference and factors of \(T\) depend on the receiver convention; a recent free-space CV-QKD experiment uses \(2TV_A(1-e^{-V_{\rm phase}/2})\) at the receiver side [17]. The positive quartic term in the manuscript therefore needs a stated derivation and range, not merely dimensional consistency.
- **Classification:** **CONDITIONALLY VALID**; **MODELING APPROXIMATION**; **MISSING ASSUMPTION**; **MISSING CITATION**.
- **Severity:** High.
- **Minimal correction:** Cite Refs. [15,16], define whether noise is receiver- or input-referred, state the residual-phase distribution and small-error range, and compare the polynomial against the exact characteristic-function expression used by the chosen receiver model.

### P4 — State independence and possible double counting

- **Location:** lines 1435–1468 and 1558–1624.
- **Equation/claim:** \(\tau_\phi^2\) is fixed within a scenario, while \(H_{\rm sc}\) fluctuates independently and \(\epsilon_n=\epsilon_{{\rm base},n}+c_\phi V_{A,n}\).
- **Literature check:** The algebra and \(d\epsilon/dV_A=c_\phi\) are correct within the surrogate. Physically, intensity and phase originate from the same turbulent field and can be correlated; residual phase also depends on tracking/estimation SNR and therefore potentially on instantaneous received power [6,9,17].
- **Classification:** **MODELING APPROXIMATION**; **MISSING ASSUMPTION**.
- **Severity:** High.
- **Minimal correction:** State independence explicitly and test it. If phase estimation uses received pilots, model \(V_{\rm phase}(T)\) or jointly sample field amplitude and phase; avoid counting the same turbulence contribution once as untrusted phase noise and again through a channel estimate unless the decomposition is derived.

## 4. Adaptive transmitter and optimization

### A1 — PS/GS/\(V_A\) dependency graph

- **Location:** lines 4151–4608 and 4773–4800.
- **Equation/claim:** PS and \(V_A\) are state-adaptive; GS prototypes are global; physical coordinates depend on PS and \(V_A\) through one normalization.
- **Literature check:** Logically consistent. The manuscript correctly acknowledges that “separate branches” are not physically independent because \(q\) changes the scale denominator.
- **Classification:** **CONDITIONALLY VALID**.
- **Severity:** Low.
- **Minimal correction:** Preserve the existing dependency graph in implementation and ensure no detached/cached ensemble is used by either MI or Holevo.

### A2 — Fourfold normalization, zero mean, and energy convention

- **Location:** lines 4610–4760, especially Eqs. `physical_constellation_mapping`, `fourfold_zero_mean`, and `exact_modulation_variance`.
- **Equation/claim:** \(p_{k,r}=q_k/4\), \(\alpha_{k,r}=\sqrt{V_A/(2\sum_\ell q_\ell|z_\ell|^2)},i^rz_k\), giving \(E[\alpha]=0\) and \(2E|\alpha|^2=V_A\).
- **Literature check:** Algebraically correct. Fourfold symmetry also gives zero pseudomoment and equal quadrature variances, supporting the scalar standard form used later.
- **Classification:** **CONDITIONALLY VALID**.
- **Severity:** Low.
- **Minimal correction:** Add the one-line pseudomoment proof \(\sum_r i^{2r}=0\) and specify a fail-closed lower bound/diagnostic for \(E_z\) to prevent singular scaling when prototypes numerically collapse.

### A3 — Average-energy budget is conditioned on active states

- **Location:** lines 5752–5806.
- **Equation/claim:** The minibatch budget constrains \(E[V_A]/2\) over active realizations.
- **Literature check:** Correct as an active-symbol photon budget. It is not the same as energy per channel opportunity, which is \(p_{\rm in}E[V_A/2\mid\text{active}]\) if no quantum symbol is sent during known outages.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** Medium.
- **Minimal correction:** Define the accounting denominator—active transmitted quantum symbols, clocked opportunities, or time—and state whether outage is known early enough to suppress transmission.

### A4 — Peak-photon constraint has no certified enforcement method

- **Location:** lines 5808–5853, Eqs. `peak_photon_constraint` and `peak_photon_constraint_explicit`.
- **Equation/claim:** Every instantiated ensemble must satisfy \(\max|\alpha|^2\le n_{\rm peak}\), with no clipping or post-hoc repair.
- **Literature check:** The explicit inequality is algebraically correct, but a soft loss, sampled-state check, or observed maximum does not prove it over a continuous policy domain.
- **Classification:** **NUMERICALLY INCOMPLETE**.
- **Severity:** Critical for the declared hardware/security domain.
- **Minimal correction:** Supply a hard parameterization or a validated whole-domain certificate, define tolerances, and fail any run/checkpoint whose complete declared state domain is not certified before selection or evaluation.

### A5 — Differentiating the moving worst-case Holevo problem

- **Location:** lines 6417–6495.
- **Equation/claim:** The manuscript recognizes that \(\max_{Z\in\mathcal I(\theta)}\chi(Z,\theta)\) need not admit an ordinary chain-rule derivative and defers the numerical treatment.
- **Literature check:** Correct diagnosis. Parametric optimization with a parameter-dependent feasible set requires envelope/KKT sensitivity conditions; at switches or degeneracies only directional derivatives/subgradients may exist [18]. An autodiff call through a selected grid index or a detached argmax is not automatically valid.
- **Classification:** **NUMERICALLY INCOMPLETE**; **MISSING CITATION**.
- **Severity:** Critical.
- **Minimal correction:** Specify and test one method: analytic endpoint/interior candidate evaluation plus KKT/envelope derivatives including active-boundary motion; a differentiable globally valid inner solver; or a documented nonsmooth/subgradient optimizer. Validate gradients against high-precision finite differences away from kinks and directional tests at kinks.

### A6 — Concrete nonsmooth and ill-conditioned loci are not enumerated

- **Location:** lines 6467–6495 and the overall training construction.
- **Equation/claim:** Nonsmoothness is mentioned only generically.
- **Literature check:** The actual loci include: max/min interval intersections; endpoint/interior maximizer switches; multiple maximizers; peak maxima and hinge/penalty activations; symplectic discriminant/eigenvalue degeneracies; entropy derivatives near \(\lambda=1\); small eigenvalues and support-rank changes in \(\tau^{-1/2}\); softmax underflow; prototype collisions; and near-zero \(E_z\).
- **Classification:** **NUMERICALLY INCOMPLETE**.
- **Severity:** High.
- **Minimal correction:** Add a numerical contract listing each locus, its detection threshold, chosen derivative/subgradient, fail/repair behavior, diagnostic artifact, and stress test.

### A7 — Ideal instantaneous CSI and feedback causality

- **Location:** lines 2064–2068, 4151–4228, and 4831–4875.
- **Equation/claim:** Alice observes exact \((T_n,\epsilon_{{\rm base},n})\) before selecting \(q_n,V_{A,n}\).
- **Literature check:** This is a legitimate oracle-adaptation model but requires channel coherence longer than estimation, feedback, constellation selection, and a QKD block. Fading security studies require channel estimation faster than fluctuations and estimation signals indistinguishable from signal states [4]. Exact per-realization excess noise is especially demanding.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** High.
- **Minimal correction:** Define block duration/coherence time, estimation and feedback latency, quantization, public disclosure, pilot indistinguishability, and whether the policy uses a delayed estimate. Otherwise call the result an ideal-CSI upper-performance benchmark.

## 5. Fading-state security and averaging

### F1 — When state-conditioned averaging is legitimate

- **Location:** lines 2048–2072 and 3454–3660.
- **Equation/claim:** Each active realization has a rate \(K_n\), outage has zero rate, and \(\bar K=E[K]\).
- **Literature check:** The algebra is correct, and a conditional Devetak–Winter rate can average over a public classical state label [3]. Operational legitimacy requires each label/bin to define an asymptotically stationary memoryless subchannel with enough parameter-estimation and reconciliation data; Ref. [4] emphasizes stability, fast estimation, and indistinguishable test/signal states. It is not legitimate to apply a fresh asymptotic security proof to every single pulse with oracle parameters.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** Critical.
- **Minimal correction:** Define public state bins/labels, within-bin residual fading, minimum block/bin sample size, statewise observable-moment estimation, reconciliation and privacy-amplification construction, and Eve's access to the label and selected modulation policy.

### F2 — Unresolved fading is not equivalent to averaging instantaneous rates

- **Location:** lines 2064–2067 and discussion following the fading average.
- **Equation/claim:** The manuscript says its rule does not establish security for blindly pooled fading data.
- **Literature check:** Correct and important. If fading is unresolved, the pooled covariance involves \(\langle\sqrt T\rangle\) and \(\langle T\rangle\), and \(\operatorname{Var}(\sqrt T)\) appears as modulation-dependent untrusted noise; it is not generally equal to \(E[K(T)]\) [4,17].
- **Classification:** **MISSING CITATION**.
- **Severity:** High.
- **Minimal correction:** Cite Ref. [4] at this caveat and state that unresolved or intra-bin fading must be included in the covariance/noise bound rather than averaged after nonlinear SKR evaluation.

### F3 — Public side information and adaptive actions must be included in Eve's conditioning

- **Location:** lines 2064–2070, 3476–3515, and 4151–4875.
- **Equation/claim:** The block-state label is said to be public, but the conditional cq security object and policy transcript are not defined.
- **Literature check:** The Devetak–Winter expression is a statement about a joint cq state and public communication [3]. When modulation depends on \(S\), Eve knows or can infer both \(S\) and the public policy/action; the relevant quantities are conditional on that side information.
- **Classification:** **MISSING ASSUMPTION**.
- **Severity:** Critical.
- **Minimal correction:** Define the joint state/transcript including \(S\), acceptance/outage, feedback, policy identifier, modulation ensemble, parameter-estimation disclosure, and reconciliation leakage; write the target rate as a conditional quantity before replacing it with an expectation of statewise terms.

### F4 — Outage as a zero-key erasure

- **Location:** lines 1461–1468 and 3584–3655.
- **Equation/claim:** AoA-outage samples have \(T=0\), \(K=0\), and remain in the opportunity-normalized average.
- **Literature check:** Correct if acquisition/outage is a public erasure criterion fixed independently of secret/test outcomes and known before key extraction. If outage selection depends on measured quantum data, it is postselection and must be included in the proof [4].
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** High.
- **Minimal correction:** Define the acceptance test, timing, public announcement, independence from key/test values, and denominator. If the rule is data dependent, include its success probability and conditional state in parameter estimation/security.

### F5 — Raw negative state rates and no statewise clipping

- **Location:** lines 5670–5748.
- **Equation/claim:** Training uses raw \(K_n=\beta I_n-\chi_n\) and does not replace it by \(\max(0,K_n)\).
- **Literature check:** This is not intrinsically wrong. For one globally conditioned cq protocol, negative conditional contributions can enter the overall conditional Devetak–Winter difference; clipping would instead implement public state selection and requires a defined accept/reject rule [3,4]. The manuscript must choose one operational interpretation.
- **Classification:** **CONDITIONALLY VALID**; **MISSING ASSUMPTION**.
- **Severity:** Medium.
- **Minimal correction:** State whether privacy amplification is global across labelled states or separate by state/bin. If aborting negative-rate bins, define the selection rule before data collection and evaluate its success probability and security conditioning.

## Top five must-fix items before numerical results

1. **Align implementation with the manuscript's security functional.** Implement and validate \(\max_{Z\in\mathcal I}\chi_{BE}(Z)\), or prove lower-endpoint maximality over the complete frozen domain. Current production code is inconsistent with the manuscript and Ref. [1].
2. **Close the \(\tau^{-1/2}\) numerical-support problem.** Select and certify a support/pseudoinverse method over the full 256-state amplitude/geometry/probability domain, including near-coincident stress cases. Do not infer publication readiness from pointwise or selected-path checks.
3. **Replace or calibrate the turbulence-to-phase surrogate.** Define the actual coherent receiver and residual phase variable, obtain \(V_{\rm phase}\) from a phase-structure/phase-screen or measured model, and use a convention-consistent exact or validated small-angle excess-noise mapping.
4. **Complete and validate the FSO turbulence law.** Specify aperture averaging, the \(\sigma_R^2\to v_{\rm sc}\) mapping, weak-regime gates, HV altitude reference/units, Kruse visibility convention, dependence assumptions, and a preregistered \(p_{>1}\) rejection threshold.
5. **Turn the oracle fading average into a defined conditional-security protocol.** Define public state bins, block stationarity, CSI/feedback causality, statewise parameter estimation, Eve's conditioning, outage/postselection, reconciliation leakage, and privacy amplification. If these are not supplied, label the output an oracle asymptotic performance functional rather than an operational secret-key rate.

## Equations verified as correct

Subject to the caveats above, the following manuscript equations are correct:

- Beer–Lambert exponent and metre-to-kilometre conversion.
- Kruse wavelength ratio and 3.912 Napierian coefficient under the 2% visibility convention.
- Normalized lognormal \(H_{\rm sc}\) construction and its mean/moment formulas.
- Plane-wave point-receiver downlink Rytov integral.
- Standard Hufnagel–Valley functional form.
- Free-space Gaussian-beam \(z_R\) and \(W_L\).
- Rician radial displacement under equal-axis Gaussian jitter and nonzero boresight.
- Generalized pointing-loss variable transformation and its bounded support.
- Rayleigh AoA outage probability under zero-mean isotropic Gaussian angular jitter.
- Normalization and CDF algebra of the manuscript's deliberately truncated active transmittance law.
- Dimensional form of \(C_n^2k^{7/6}L^{11/6}\) (but not its identification as residual phase variance).
- Heterodyne complex-AWGN/SNU normalization, assuming the stated ideal receiver.
- \(\tau\), \(\mathcal C\), support-restricted \(a_\tau\), and \(w\).
- \(Z_\pm=2\sqrt T\mathcal C\pm\sqrt{2T\epsilon w}\).
- \(a=V_A+1\), \(b=1+TV_A+T\epsilon\).
- \(|Z|\le\sqrt{ab-1-|a-b|}\) and intersection with \([Z_-,Z_+]\).
- Standard-form covariance matrix, symplectic invariants, \(\lambda_{1,2}\), and ideal-heterodyne \(\lambda_3=a-Z^2/(b+1)\).
- Three-entropy Gaussian Holevo expression and the manuscript-level full-interval maximization.
- Outage-inclusive expectation identity \(E[K]=p_{\rm in}E[K\mid\text{active}]\) when outage is a public zero-key erasure.
- Orbit softmax normalization, \(p_{k,r}=q_k/4\), fourfold zero mean/isotropy, exact \(V_A\) normalization, and the explicit peak-photon inequality.
- \(\epsilon=\epsilon_{\rm base}+c_\phi V_A\) and its \(V_A\) derivative within the adopted phase surrogate.

## Assumptions that must be stated explicitly

1. Vacuum variance is one SNU per quadrature; \(V_A=2E|\alpha|^2\); \(\epsilon\) is input-referred.
2. Security is asymptotic, reverse-reconciled, collective-attack, covariance/Gaussian-extremality based, and non-composable.
3. Bob's heterodyne is ideal/trusted; detector loss/electronics are either absent or assigned a clearly stated trust model.
4. The ensemble is centered, fourfold symmetric, quadrature-isotropic, and identical at the MI and Holevo interfaces.
5. State labels, feedback, policy, outage/acceptance, and modulation choices are public to Eve and included in conditioning.
6. Each security state/bin is stationary and memoryless for long enough to estimate its moments and reconcile data; residual intra-bin fading is bounded.
7. CSI is available causally before modulation selection, with declared estimation time, feedback latency, quantization, and error model.
8. Weather/extinction is homogeneous unless an altitude/path integral is used; Kruse visibility follows the declared 2% convention or is converted from 5% MOR.
9. HV height origin and units, wind definition, nominal ground \(C_n^2\), zenith geometry, and flat-Earth approximation are fixed.
10. Rytov/lognormal use is limited to a preregistered weak/moderate regime; aperture averaging is explicitly defined.
11. Scintillation, beam wander, pointing, AoA, and residual phase are independent only as an approximation, with a validation/sensitivity range.
12. Diffraction-only \(W_L\) excludes turbulence broadening/deformation, or those effects are included elsewhere without double counting.
13. Truncation at \(T=1\) is accepted only below a declared \(p_{>1}\) tolerance; otherwise the channel model is rejected.
14. Residual phase refers to a specified receiver/pilot/LO architecture and compensation bandwidth, with a stated distribution and input/output noise reference.
15. Photon budget denominator and outage transmission behavior are defined; the peak bound holds over the whole policy domain.
16. The moving inner maximization and all support/eigenvalue/constraint nonsmooth points have a defined numerical and derivative contract.

## Citations that should be added to the paper

The present manuscript reference list contains only three entries and is inadequate for the security and channel model. At minimum add Refs. [1–18] where indicated below; Ref. [19] is a useful current validation/context source.

## Sources

[1] A. Denys, P. Brown, and A. Leverrier, “Explicit asymptotic secret key rate of continuous-variable quantum key distribution with an arbitrary modulation,” *Quantum* **5**, 540 (2021). [https://doi.org/10.22331/q-2021-09-13-540](https://doi.org/10.22331/q-2021-09-13-540)

[2] C. Weedbrook *et al.*, “Gaussian quantum information,” *Rev. Mod. Phys.* **84**, 621–669 (2012). [https://doi.org/10.1103/RevModPhys.84.621](https://doi.org/10.1103/RevModPhys.84.621)

[3] I. Devetak and A. Winter, “Distillation of secret key and entanglement from quantum states,” *Proc. R. Soc. A* **461**, 207–235 (2005). [https://doi.org/10.1098/rspa.2004.1372](https://doi.org/10.1098/rspa.2004.1372)

[4] V. C. Usenko *et al.*, “Entanglement of Gaussian states and the applicability to quantum key distribution over fading channels,” *New J. Phys.* **14**, 093048 (2012). [https://doi.org/10.1088/1367-2630/14/9/093048](https://doi.org/10.1088/1367-2630/14/9/093048)

[5] D. Y. Vasylyev, A. A. Semenov, and W. Vogel, “Toward global quantum communication: beam wandering preserves nonclassicality,” *Phys. Rev. Lett.* **108**, 220501 (2012). [https://doi.org/10.1103/PhysRevLett.108.220501](https://doi.org/10.1103/PhysRevLett.108.220501)

[6] D. Vasylyev, A. A. Semenov, and W. Vogel, “Atmospheric quantum channels with weak and strong turbulence,” *Phys. Rev. Lett.* **117**, 090501 (2016). [https://doi.org/10.1103/PhysRevLett.117.090501](https://doi.org/10.1103/PhysRevLett.117.090501)

[7] D. Vasylyev, W. Vogel, and A. A. Semenov, “Theory of atmospheric quantum channels based on the law of total probability,” *Phys. Rev. A* **97**, 063852 (2018). [https://doi.org/10.1103/PhysRevA.97.063852](https://doi.org/10.1103/PhysRevA.97.063852)

[8] M. Klen and A. A. Semenov, “Numerical simulations of atmospheric quantum channels,” *Phys. Rev. A* **108**, 033718 (2023). [https://doi.org/10.1103/PhysRevA.108.033718](https://doi.org/10.1103/PhysRevA.108.033718)

[9] L. C. Andrews and R. L. Phillips, *Laser Beam Propagation through Random Media*, 2nd ed. (SPIE, 2005). [https://doi.org/10.1117/3.626196](https://doi.org/10.1117/3.626196)

[10] ITU-R P.1621-1, “Propagation data required for the design of Earth-space systems operating between 20 THz and 375 THz” (2005), especially the HV 5/7 profile, coherence radius, and phase measures. [Official ITU PDF](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1621-1-200503-S%21%21PDF-E.pdf)

[11] ITU-R P.1622-0, “Prediction methods required for the design of Earth-space systems operating between 20 THz and 375 THz” (2003), especially downlink scintillation and aperture averaging. This historical recommendation is superseded but remains an authoritative source for the cited formulas. [Official ITU PDF](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1622-0-200304-S%21%21PDF-E.pdf)

[12] ITU-R P.1814-1, “Prediction methods required for the design of terrestrial free-space optical links” (2025), especially Beer–Lambert attenuation, visibility definitions, and uncertainty. [Official ITU PDF](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1814-1-202509-I%21%21PDF-E.pdf)

[13] A. A. Farid and S. Hranilovic, “Outage capacity optimization for free-space optical links with pointing errors,” *J. Lightwave Technol.* **25**, 1702–1710 (2007). [https://doi.org/10.1109/JLT.2007.899174](https://doi.org/10.1109/JLT.2007.899174)

[14] F. Yang, J. Cheng, and T. A. Tsiftsis, “Free-space optical communication with nonzero boresight pointing errors,” *IEEE Trans. Commun.* **62**, 713–725 (2014). [https://doi.org/10.1109/TCOMM.2014.010914.130249](https://doi.org/10.1109/TCOMM.2014.010914.130249)

[15] M. Li and T. Wang, “Continuous-variable quantum key distribution over air quantum channel with phase shift,” *IEEE Access* **8**, 39672–39677 (2020). [https://doi.org/10.1109/ACCESS.2020.2975155](https://doi.org/10.1109/ACCESS.2020.2975155)

[16] M. Li and M. Cvijetic, “Continuous-variable quantum key distribution with self-reference detection and discrete modulation,” *IEEE J. Quantum Electron.* **54**, 8000408 (2018). [https://doi.org/10.1109/JQE.2018.2867651](https://doi.org/10.1109/JQE.2018.2867651)

[17] “All-day free-space quantum key distribution with thermal source towards quantum secure communications for unmanned vehicles,” *npj Quantum Information* (2025), especially its residual-phase and fading-noise conventions. [https://doi.org/10.1038/s41534-025-01085-y](https://doi.org/10.1038/s41534-025-01085-y)

[18] J. F. Bonnans, R. Cominetti, and A. Shapiro, “Sensitivity analysis of optimization problems under second order regular constraints,” *Math. Oper. Res.* **23**, 806–831 (1998). [https://doi.org/10.1287/moor.23.4.806](https://doi.org/10.1287/moor.23.4.806)

[19] M. Li *et al.*, “Security analysis of free-space discrete modulated continuous-variable quantum key distribution with precise channel characterization and postselection strategies,” *Phys. Rev. Applied* **25**, 024013 (2026). [https://doi.org/10.1103/v7d9-ylyl](https://doi.org/10.1103/v7d9-ylyl)

**Standards-scope note:** ITU-R P.1814-1's scope is terrestrial FSO, while the HAP–UAV link is an airborne slant path; its visibility guidance is used here for units/convention, not as a complete HAP–UAV propagation standard. For the manuscript's high-altitude optical model, Refs. [9–11] and direct numerical field-propagation validation remain necessary.

## Final verdict

**NOT SAFE FOR PUBLICATION-SCALE RESULTS**

The manuscript contains a viable analytic backbone, and many equations are correct. Publication-scale results are nevertheless unsafe until the full-interval Holevo computation, \(\tau\)-support numerics, phase model, aperture/PDT validation, and conditional fading-security protocol are all specified, implemented, and independently validated. This verdict also agrees with the repository's explicit lifecycle state, which currently does not authorize publication-scale training or evaluation.
