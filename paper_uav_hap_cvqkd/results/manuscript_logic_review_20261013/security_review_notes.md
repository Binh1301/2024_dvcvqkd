# Independent security-model comparison, 2026-10-13

Read-only theoretical review of the three supplied PDFs and the current literal implementation. No AP, MI, SKR, AO, tests, source/cache changes, or lifecycle approvals were performed. This file contains proposed corrections, not an adopted replacement model.

Repository snapshot: branch `channel/update`, HEAD `84bf84dc3862b6cb51fa368f7e481459845ffb98`. The pre-existing literal implementation and lifecycle edits are preserved. `FINAL_MODEL_SPEC.md` currently hashes to `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`, differing from the historical expected hash; the existing state already records this blocker. Publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## 1. Protocol and security assumptions

| Item | What Binh (37) actually states | Requirement for a consistent correction |
|---|---|---|
| Protocol/source | Prepare-and-measure coherent M-QAM with MB probabilities, pp.1-2, Eqs.(1)-(3),(21)-(23) | Treat the 256 coherent states as quantum modulation; use the DBL arbitrary-modulation source bound, not a classical QAM capacity assertion. |
| Detection | Both homodyne and heterodyne formulas appear, p.3 | Declare one protocol. Existing literal code chooses heterodyne. |
| Reconciliation | Eq.(16) has beta I_AB minus Bob-Eve Holevo; beta=.95 on p.4 | Explicit asymptotic reverse reconciliation. Constant beta=.95 is an assumed numerical efficiency, not an implemented reconciliation code. |
| Detector trust | R and xi_det appear in p.3, but ownership/trust is unspecified | Ideal detector, trusted nonideal detector, and untrusted composite receiver are different models. Specify one before calculating Holevo. |
| Security regime | No finite-size derivation, confidence region, block length, or composable error is supplied | Restrict to an asymptotic collective-attack bound under an explicit parameter-estimation and fading protocol. |
| Attack assumptions | DBL source is cited, but operational fading/adaptation conditions are unspecified | DBL does not require the attack channel to be Gaussian. It does use Gaussian extremality to bound Eve's information from covariance constraints. Distinguish this from assuming Gaussian attacks. |

DBL PDF p.4 explicitly separates its asymptotic analysis from a full finite-size/composable proof. Its p.8 uses a fixed trusted Gaussian measurement and Gaussian extremality, and p.10 assumes collective attacks with the same conditional output state for a given sent symbol. Satellite PDF p.8 restricts its finite-size numerical analysis to Gaussian modulation; it does not supply a finite-size proof for this 256-QAM manuscript.

## 2. Definite algebra/convention errors

### A. Modulation variance: factor four

Binh p.2 immediately after Eq.(3) writes V_A=<n>/2. With the standard coherent-state amplitudes used in Eqs.(21)-(22), vacuum quadrature variance one, and the covariance diagonal V_A+1, the necessary identity is

    V_A = 2 <n> = 2 sum_k p_k |alpha_k|^2.

DBL p.8 defines V=1+2 tr(rho a†a), and p.9 writes V=V_A+1. Current `src/modulation/normalization.py:29,61-69` implements alpha=sqrt(V_A/(2 E_x)) x, already consistent with this identity. This manuscript line is not an interchangeable convention unless all amplitudes, commutators, covariance matrices, and noise normalizations are changed together.

### B. Effective power transmission is missing its square

Binh p.3 following Eq.(11) defines eta_f=<sqrt(eta)> while using eta_f as a power multiplier in Bob's covariance and, through the selected implementation mapping, in Eq.(20).

Let m=E[sqrt(eta)] and r=E[eta]. If eta is power transmission, the effective power parameter is T_eff=m^2. One may instead keep an amplitude parameter g_eff=m, but then covariance uses g_eff^2 and correlation uses g_eff directly.

Even without fading, eta=eta_0 gives m=sqrt(eta_0), and the manuscript Bob signal term is sqrt(eta_0) V_A instead of eta_0 V_A. This proves the error independently of any numerical result.

Literal code locations: `src/manuscript_literal_3moments.py:161-174` stores eta_f=m; `:188` multiplies V_A by m; `:179-181` uses sqrt(m) in Z; `:264-276` explicitly chooses T=eta_f for MI. The code reproduces the manuscript convention deliberately; this is a scientific model error, not an accidental implementation typo.

### C. Total input noise is substituted for channel excess noise

Binh p.3 defines xi=chi_line+chi_hom/het/eta, with chi_line=1/eta-1+xi_ch. This quantity includes loss-induced vacuum and detection/heterodyne noise. It is a total equivalent input noise used in certain classical SNR formulas. It is not the DBL excess noise xi in Eq.(14) of DBL or Eq.(20) of Binh.

DBL p.13 assumes a coherent output quantum quadrature variance 1+T xi. Its source-correlation penalty is sqrt(2 T xi w). The covariance already contains the quantum vacuum term +1. The ideal heterodyne conditional covariance already contains another measurement vacuum term in its denominator b+1. Neither should be added again through xi.

Analytic counterexample: eta=1, no fading, xi_ch=0, R=1, xi_det=0. Manuscript chi_het=1 and xi=1, so Eq.(11) gives b=V_A+2 rather than V_A+1. Eq.(20) also spuriously subtracts sqrt(2w). Thus the ideal noiseless channel is represented as noisy.

Literal code locations: `:31-44` calculates detector/total noise; `:148-152` propagates it to E[eta xi]; `:171-173,181,188` then uses it as quantum excess noise. At eta=0 the original xi is singular; algebraically continuing eta xi for the outage atom does not turn this total-noise convention into a valid quantum excess-noise moment.

### D. Source PMF does not match the centered constellation

Binh p.2 Eq.(1) centers amplitudes at k-(m_const-1)/2 and l-(m_const-1)/2, but Eq.(2) uses exp[-nu(k^2+l^2)] for indices 0,...,m_const-1. For nu>0, that weights one corner, gives a nonzero displacement, and breaks the rotation symmetry required by the current scalar source covariance.

For the existing centered MB source/catalog, use q_k=k-(m_const-1)/2 and p_kl proportional to exp[-nu_raw(q_k^2+q_l^2)]. If instead the corner-biased law is intended, it is a different ensemble and its source moments, centering, and covariance assumptions must be recomputed; existing centered C,w must not be reused.

## 3. Consistent fixed-ensemble fading derivation

This is a proposed derivation for a fixed, centered, symmetric source, phase-insensitive fading, ideal heterodyne, and true input-referred channel excess noise xi_ch(eta). The fading distribution must first be a normalized probability law with its outage atom preserved.

Define

    n_bar = sum_k p_k |alpha_k|^2 = V_A/2,
    m = E[sqrt(eta)],  r = E[eta],  u = E[eta xi_ch(eta)],
    T_eff = m^2,
    N_out = (r-m^2) V_A + u,
    xi_eff = N_out / T_eff, when T_eff>0.

The actual PM moments for the pooled channel are

    beta_k = m alpha_k,
    c_1 = m C,  c_2 = m n_bar,
    n_B = r n_bar + u/2.

Use DBL's general bound, p.12 Eqs.(11)-(13), not an unsupported Gaussian-mixture identity:

    Z_± = 2c_1 ± 2 sqrt[w (n_B-c_2^2/n_bar)]
        = 2m C ± sqrt(2 w N_out).

The covariance has

    a = 1+V_A,
    b = 1+r V_A+u = 1+T_eff V_A+N_out,
    Gamma(Z) = [[a I, Z sigma_z], [Z sigma_z, b I]].

This moment/correlation mapping is valid for the pooled mixture under the stated fixed-ensemble assumptions. The mixture quantum channel need not itself be Gaussian: DBL constrains arbitrary compatible channels through measured c_1,c_2,n_B. It does not follow that the mixture's classical MI equals Gaussian AWGN MI with T_eff and xi_eff.

If T_eff=0, use the original observed/general moment formulation and a defined outage protocol. Do not divide by zero to manufacture xi_eff.

## 4. What is correct in Eqs.(18)-(20), and the remaining bound condition

The symplectic expressions themselves are correct for a physically valid two-mode standard covariance:

    Delta = a^2+b^2-2Z^2,
    D = (ab-Z^2)^2,
    lambda_1,2 = sqrt[(Delta ± sqrt(Delta^2-4D))/2].

For ideal heterodyne on Bob, lambda_3=a-Z^2/(b+1), and

    chi_G(Z) = g((lambda_1-1)/2)+g((lambda_2-1)/2)
               -g((lambda_3-1)/2).

Binh p.3 Eq.(19) and its following conditional-eigenvalue line copy the valid DBL form; `src/manuscript_literal_3moments.py:193-202` and `src/cvqkd/covariance.py:103-121` implement it correctly. The erroneous upstream b/Z inputs are the issue. Also, Binh does not explicitly identify the T,xi of Eqs.(19)-(20) with the eta_f,xi_f of Eq.(11); literal code `:264` documents an additional selected mapping.

Z_- is a correlation lower bound. It is not automatically the argmax of Holevo for all parameters. DBL p.12 footnotes 11 and 12 explicitly require maximization of Holevo over the allowed Z interval in general. The conservative covariance interval is the intersection of [Z_-,Z_+] with physicality:

    |Z| <= sqrt(ab-1-|a-b|),  a,b>=1.

An empty intersection is a failure. Otherwise use chi_bound=max_Z chi_G(Z) over the intersection, unless endpoint optimality has been established for every reported point. The existing direct-Z result is an adopted diagnostic choice, not a general proof of this maximization.

Current direct/interval code: `src/cvqkd/holevo.py:402-436` evaluates Z_- directly when maximize_full_interval=False; `:438-458` constructs the physical intersection for the other branch. Literal code has no interval maximization.

## 5. MI, detection, and averaging order

For deterministic ideal-heterodyne AWGN with the standard source amplitudes,

    Y|k ~ CN(sqrt(T) alpha_k, 1+T xi_ch/2),
    I_AB = sum_k p_k integral f(y|k) log2[f(y|k)/sum_j p_j f(y|j)] d^2y.

`src/cvqkd/mutual_information.py:396-397` has this consistent normalization. For a finite 256-state alphabet, 0<=I_AB<=H(p)<=8 bits/use. Binh Eq.(17) is explicitly a Gaussian-modulation formula; it cannot become exact DM MI by assigning Gaussian-looking probabilities to 256 points. Satellite p.4 Eq.(16) uses the Gaussian-style expression for M-QAM. DBL p.29 explicitly recognizes that finite-QAM MI has no such closed form and discusses when its Gaussian approximation is small. Retain the discrete integral in the repository for an actual DM calculation.

For pooled unknown fading, the likelihood is instead

    f(y|k) = E_eta[ CN(y; sqrt(eta) alpha_k, 1+eta xi_ch(eta)/2) ].

Replacing this mixture by AWGN with T_eff,xi_eff only matches first/second moments; it does not prove equality or a lower bound for I_AB. Common random eta also couples real and imaginary observations, so the deterministic AWGN product identity I_R+I_Q does not automatically apply to the mixture. The literal implementation's `:274-276` is therefore an effective-Gaussian-channel MI approximation, not a verified fading likelihood.

For CSI known to both parties and public to Eve, conditional bin/block rates may be aggregated only after specifying binning, a fixed ensemble per bin, conditional parameter estimation, reconciliation, and key aggregation. For a fixed source with eta independent of X, I(X;Y|eta)>=I(X;Y) in general. Thus replacing pooled MI by an instantaneous average can improve the value merely by adding side information; these are different protocols.

Detector choices:

- Ideal: R=1, xi_det=0; omit detector noise from the quantum xi term. Ideal heterodyne vacuum is already in the measurement likelihood and b+1.
- Trusted nonideal: keep the untrusted channel covariance separately and model the receiver ancillas/loss/noise as trusted. The resulting conditional entropy generally involves the receiver's enlarged covariance, not the unchanged ideal single-lambda_3 formula. Satellite p.3 Eqs.(6)-(11) has a distinct detector treatment with two conditional symplectic eigenvalues; do not transplant its chi_tot into the simplified DBL DM covariance.
- Untrusted receiver: explicitly compose receiver loss/noise with the quantum channel before a remaining ideal heterodyne measurement. With the usual satellite electronic-noise convention, eta'=R eta and quantum output excess is R eta xi_ch+2xi_det. Heterodyne splitting vacuum is still measurement noise, not extra quantum excess. This is a deliberately more conservative, separately declared protocol; do not assume trust implicitly.

## 6. Parameter-estimation and physical checks needed before claims

DBL p.10-12 requires the measured constraints c_1,c_2,n_B. In the current ideal complex heterodyne normalization, n_B=E[|Y|^2]-1. c_1=Re sum_k p_k conjugate(d_k) beta_k, c_2=Re sum_k p_k conjugate(alpha_k) beta_k, with d_k=<alpha_k|a_tau|alpha_k>. Merely supplying a fitted T and total noise does not establish these constraints under arbitrary attacks, especially for adaptive/non-Gaussian/fading channels.

For asymptotic simulations, state the observed moments being modeled and the iid/conditional-iid assumptions. For a finite-size claim, jointly bound c_1,c_2,n_B, source preparation and SNU calibration, use the worst case over their confidence region, and account for reconciliation leakage, verification, smoothing/privacy-amplification, and bin-dependent sample counts. Neither manuscript nor literal code supplies that finite-size proof.

Recommended symbolic/numerical sanity tests (NOT RUN here): normalized channel mass including outage; E[eta] in [0,1]; E[sqrt eta]^2<=E[eta]; deterministic-channel limit; ideal noiseless eta=1 limit; vacuum V_A->0 limit; identical p,alpha,V_A in MI and C,w branches; nonnegative w; Gamma+iOmega>=0; lambda_j>=1; full allowed correlation/Holevo interval; MI alphabet entropy bound; actual fading mixture MI vs effective-AWGN approximation; detector trusted/untrusted limits. Parameter adaptation must condition the source and PE together; mixing C,w from one ensemble with MI from another is invalid.

The current exact source-moment catalog can support C,w for its hash-matched centered ensembles. It does not independently validate PDF normalization, detector trust, fading MI, endpoint Holevo optimality, or finite-size/composable security. Correcting channel equations with the source unchanged can preserve source caches, while all old channel/objective/SKR identities must remain distinct from corrected results.
