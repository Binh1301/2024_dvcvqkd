# Security-scope freeze

Status: **security wording frozen, subject to the two author approvals identified
in Section E**. This document narrows the claims that may be made from the
implemented calculation. It does not alter `FINAL_MODEL_SPEC.md` or extend the
security proof.

## A. Exact security assumptions

| Item | Frozen assumption | Implementation/theory consequence |
|---|---|---|
| Protocol and modulation | Prepare-and-measure, single-mode coherent-state, 256-state discrete-modulated CV-QKD. The learned PMF and geometry are C4 symmetric; this is not Gaussian modulation and not a classical coexistence-QAM rate calculation. | The density operator is the actual mixture `tau=sum_i p_i |alpha_i><alpha_i|`; Gaussian-modulation formulas are not substituted for the discrete ensemble. |
| Measurement | Bob performs ideal heterodyne (double-homodyne) detection. | Detector efficiency is effectively one and electronic noise is zero in the active equations. No separate trusted-detector loss/noise model is present. |
| Reconciliation | Asymptotic reverse reconciliation with declared efficiency `beta_rec`. Bob's heterodyne data define the raw key variable. | The rate functional is `K_raw=beta_rec I_AB-chi_BE`. A numerical `beta_rec` does not establish that a practical reconciliation code exists. |
| Security regime | Asymptotic only. | There is no finite-block penalty, composable security parameter, smoothing term, privacy-amplification cost, authentication cost, or finite-sample confidence interval. |
| Attack class | **AUTHOR_REVIEW_REQUIRED.** The implemented chain is compatible with the Denys--Brown--Leverrier analytical bound against collective attacks, state by state, only under all conditions listed below. The code correctly leaves `ProtocolAssumptions.attack_class=None` until this interpretation is approved and cited. | It is not a proof against arbitrary coherent/general attacks. Gaussian optimality alone does not promote the result to such a proof. |
| CSI | Exact instantaneous `(T,epsilon)` is supplied as an oracle to Alice, Bob's model, and the evaluator. The trained policy is frozen offline. | CSI estimation, confidence bounds, feedback delay/error/quantization, feedback authentication cost, and pilot overhead are absent. The manuscript's current narrative that Bob estimates and feeds back the state is not implemented. |
| Channel parameters | `T` is instantaneous power transmittance. `epsilon>=0` is excess noise in shot-noise units referred to the channel input. | The ideal-channel covariance uses `b=1+T V_A+T epsilon`; no output-referred or detector-referred noise may be substituted. |
| SNU and modulation | `[x,p]=2i`, vacuum quadrature variance is one, `V_A=2 sum_i p_i |alpha_i|^2=2 n_bar`, and the source-mode covariance diagonal is `V_A+1`. | Bob's complex heterodyne channel uses `CN(0,1+T epsilon/2)`, consistent with per-quadrature variance `1/2+T epsilon/4`. |
| Ensemble consistency | The identical statewise `Ensemble={p_i,alpha_i}` is passed unchanged to the MI and Holevo branches. | PS, GS, and adaptive `V_A` affect both branches through the same physical amplitudes and probabilities. |
| Symmetry/standard form | Zero displacement, equal quadrature variances, zero I/Q covariance, and zero pseudomoment are enforced by C4 construction. Unsupported asymmetric ensembles fail closed. | The scalar standard-form covariance used by the Holevo calculation is not claimed for arbitrary asymmetric 256-state modulation. |
| Fading average | `I_AB`, the Holevo bound, and `K_raw` are evaluated conditionally for each oracle state before averaging. | The current average is an oracle fading-distribution performance functional. An operational fading-channel secret-key rate requires the block/conditioning assumptions below. |

### Conditional collective-attack interpretation

The statewise calculation may be described as an asymptotic collective-attack
lower bound only if the author explicitly adopts all of the following:

1. Each evaluated `(T,epsilon)` represents a stationary, memoryless channel
   block containing asymptotically many signals, so the same conditional state
   is repeated within that block.
2. The channel-state label and the resulting modulation policy are treated as
   public side information available to Eve; adaptation is not a secret
   randomization.
3. Alice uses one declared ensemble within the block and Bob uses ideal
   heterodyne detection with the normalization in the table above.
4. The first- and second-moment constraints required by the arbitrary-
   modulation bound are established asymptotically for every security-relevant
   block or preregistered state bin. Supplying simulated true `T` and `epsilon`
   is not a replacement for experimental parameter estimation.
5. Fading-state binning, acceptance/abort behavior, and aggregation of keys
   across blocks are fixed independently of secret/test outcomes. No
   post-selection advantage is claimed by silently discarding negative-rate
   states.
6. Either independent privacy amplification is applied to each certified
   block/bin or a cited theorem justifies the chosen cross-block aggregation.

The current iid continuous-state simulator does not implement these operational
steps. It evaluates the conditional asymptotic formula at sampled states. Thus
the phrase **statewise asymptotic collective-attack calculation** is supportable
after the author approves the conditions above; the stronger phrase
**security proof for the adaptive fading protocol** is not.

## B. Allowed paper claims

The following claims are allowed without broadening the model:

- The study evaluates a 256-state coherent-state DM-CV-QKD prepare-and-measure
  protocol with ideal heterodyne detection and asymptotic reverse
  reconciliation.
- For each oracle channel state, it computes exact discrete-input mutual
  information and a covariance-based upper bound on Eve's Holevo information
  from the same physical discrete ensemble.
- The implemented Holevo path is
  `tau -> (C,w) -> Z_lower -> Gamma_AB -> symplectic eigenvalues -> chi_BE_upper`.
  Consequently, `beta_rec I_AB-chi_BE_upper` is a lower-bound rate functional
  within the accepted asymptotic model, up to separately certified numerical
  truncation/Monte Carlo error.
- The C4 restriction supports the scalar standard form used in the calculation;
  the result covers the implemented C4 PMFs/geometries, not unrestricted
  asymmetric 256-way shaping.
- PS and `V_A` adapt to exact `(T,epsilon)` oracle CSI while GS remains global,
  and all learned parameters are frozen before deployment/evaluation.
- Rates are evaluated statewise before taking the declared fading-distribution
  average. This average may be called an **oracle-CSI asymptotic rate
  calculation** or **simulation lower-bound functional**.
- After the Section-E approvals, the single-state/block calculation may be
  described as compatible with asymptotic collective attacks under the six
  conditions above.

## C. Prohibited or unsupported claims

The present implementation and manuscript may not claim:

- finite-size, finite-key, composable, universally composable, unconditional,
  device-independent, or measurement-device-independent security;
- security against arbitrary coherent/general attacks;
- that Gaussian optimality by itself proves security of the implemented
  256-state adaptive fading protocol;
- a security proof for arbitrary asymmetric 256-QAM, or importation of a
  Gaussian-modulation covariance formula without the discrete-modulation
  correlation bound;
- security with imperfect, delayed, estimated, unauthenticated, or quantized
  CSI, or any practical pilot/feedback overhead;
- security with nonunit detector efficiency, electronic noise, trusted
  receiver noise, saturation, local-oscillator attacks, or other implementation
  imperfections;
- a realized reconciliation efficiency, coded throughput, frame-error rate,
  distribution matcher, or privacy-amplification implementation;
- valid finite-sample parameter estimation for continuously varying states;
- a secure transmit/abstain or post-selection gain from
  `E[max(0,K_raw)]`; this remains an oracle diagnostic unless a protocol and
  proof are added;
- security of the fading-average rate merely by averaging independently
  secure-looking instantaneous formulas; the block/bin and aggregation
  conditions in Section A are required;
- publication-ready Holevo values until the finite physical-amplitude domain
  and exact enumerated selected-ensemble/checkpoint Fock convergence are certified.

## D. Exact manuscript-ready paragraph

The paragraph below is the recommended replacement security-scope statement.
It is approved for use **only after** both Section-E author approvals are
resolved and the primary citation is inserted at `[DBL-2021]`.

> We evaluate a prepare-and-measure 256-state coherent-state discrete-modulated
> CV-QKD protocol with ideal heterodyne detection and asymptotic reverse
> reconciliation. For each exact oracle channel state `(T,epsilon)`, the same
> physical ensemble `{p_i,alpha_i}` is used to compute the discrete-input mutual
> information and the Denys--Brown--Leverrier arbitrary-modulation
> covariance-based upper bound on Eve's Holevo information [DBL-2021], through
> `tau -> (C,w) -> Z -> Gamma_AB -> chi_BE`. Under the explicit modeling
> assumption that each known fading state represents an asymptotically long
> stationary memoryless block, that the state and adaptive modulation choice
> are public to Eve, and that the required first- and second-moment parameters
> are known asymptotically for each analyzed block or preregistered state bin,
> the resulting `K_raw=beta_rec I_AB-chi_BE` is interpreted as a statewise lower
> bound against collective attacks. The reported fading average is an
> oracle-CSI asymptotic simulation functional obtained only after statewise
> evaluation. We do not claim finite-size or composable security, security
> against arbitrary coherent attacks, a proof for imperfect CSI or detector
> imperfections, or an operational security proof for continuously varying
> fading without an explicit state-binning, parameter-estimation, and
> cross-block key-aggregation protocol.

If the author does not approve the conditional collective-attack assumptions,
replace the sentence beginning "Under the explicit modeling assumption" with:

> The calculation is reported only as the author's accepted asymptotic
> covariance-based DM-CV-QKD rate functional; no attack class or operational
> fading-protocol security claim is assigned.

## E. Citation/theory dependencies and required author decisions

### Primary dependency that must be added and verified

`[DBL-2021]` should be the primary source, not an uncited equation transfer:

> A. Denys, P. Brown, and A. Leverrier, "Explicit asymptotic secret key rate of
> continuous-variable quantum key distribution with an arbitrary modulation,"
> *Quantum*, vol. 5, p. 540, 2021, DOI: 10.22331/q-2021-09-13-540,
> arXiv:2103.13945v3.

The source explicitly treats prepare-and-measure coherent-state discrete
modulation with heterodyne detection, reverse reconciliation, and collective
attacks in the asymptotic regime; it also explicitly states that it is not a
full composable proof against general attacks. Its published QAM ancillary code
uses the same structural expressions implemented here:

- `tau=sum_i p_i |alpha_i><alpha_i|`;
- `C=Tr(sqrt(tau) a sqrt(tau) a^dagger)`;
- `a_tau=sqrt(tau) a tau^(-1/2)` and the corresponding non-Gaussian penalty
  `w`;
- `Z_lower=2 sqrt(T) C-sqrt(2 T epsilon w)`;
- `a=V_A+1`, `b=1+T V_A+T epsilon`, `c=Z_lower`, ideal-heterodyne conditional
  eigenvalue `lambda_3=a-c^2/(b+1)`, and the three-entropy Holevo expression.

The active code matches this structural chain. Its different density-matrix
pseudoinverse threshold is a numerical truncation choice that must be covered
by the already required Fock-cutoff convergence study, not presented as a new
security theorem.

### Existing manuscript references

- The manuscript's Sayat *et al.* reference is relevant context for satellite
  QAM DM-CV-QKD and itself points to the Denys--Brown--Leverrier bound. It is not
  a substitute for citing the primary theorem used by Eqs. (103)--(126).
- The Ismail *et al.* UAV reference concerns a finite-size Gaussian-modulated
  scenario. It cannot justify finite-size security, discrete-modulation
  security, or the implemented `C,w,Z` chain.

### Exact author approvals still required

1. **ATTACK_CLASS_APPROVAL:** approve or reject the six-condition statewise
   collective-attack interpretation in Section A. Until approved,
   `attack_class=None` must remain and the fallback paragraph in Section D must
   be used.
2. **FADING_PROTOCOL_SCOPE_APPROVAL:** choose whether the manuscript will
   remain an oracle statewise simulation study or will specify asymptotically
   long fading blocks, preregistered state bins, parameter estimation, and
   per-bin/cross-bin key aggregation. The latter is a protocol/theory extension
   and is not implemented by this task.

### Parameter-estimation requirements for any future operational claim

For each security-relevant block or bin, Alice and Bob must estimate the
first-moment correlations and Bob second moment needed by the arbitrary-
modulation covariance bound (often represented by `c1`, `c2`, and `n_B` in the
primary source), using data not retained for the key. Finite-size use requires
worst-case confidence bounds and associated failure probabilities. The current
simulator instead substitutes the exact Gaussian-channel expectations implied
by oracle `T` and input-referred `epsilon`; this is sufficient only for the
declared asymptotic model calculation.

### Numerical/physical checks that remain mandatory

- certify MI Monte Carlo convergence independently of the security theorem;
- certify density trace, `C`, `w`, `Z`, and `chi_BE` convergence over the final
  finite physical-amplitude domain;
- reject material negative density eigenvalues, `w<0`, nonphysical covariance
  matrices, or symplectic eigenvalues below one rather than repairing them;
- record every within-tolerance numerical repair;
- verify `0<T<=1`, `epsilon>=0`, one ensemble at both interfaces, and the C4
  standard-form invariants for every evaluated state;
- report raw fading averages separately from aggregate clipping and the
  state-selective positive-part diagnostic.

## Code and manuscript evidence audited

- `src/cvqkd/protocol.py`: ideal heterodyne, asymptotic reverse reconciliation,
  no finite/composable claim, oracle CSI, and intentionally unresolved attack
  class.
- `src/cvqkd/holevo.py`: exact `tau -> C,w,Z` path and fail-closed Fock/density
  diagnostics.
- `src/cvqkd/covariance.py`: the standard covariance, symplectic eigenvalues,
  ideal-heterodyne conditional eigenvalue, and uncertainty guard.
- `src/cvqkd/secret_key_rate.py`: `beta_rec I_AB-chi_BE` and statewise-before-
  average ordering.
- `src/optimization/trainer.py` and `tests/test_pipeline_consistency.py`: the
  identical `Ensemble` object reaches MI and Holevo without mutation.
- Source manuscript Eqs. (56)--(64), (82)--(90), and (103)--(137): noise/SNU,
  statewise ensemble, Holevo chain, and fading-order statements. Its Sec. IV-A
  pilot-estimation narrative conflicts with the frozen oracle-CSI limitation
  and must not be used as an implemented security claim.
