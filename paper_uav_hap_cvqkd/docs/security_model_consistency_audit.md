# Security-model consistency audit — 2026-10-20

**Verdict: INCONSISTENT measurement pairing; UNVALIDATED_SECURITY_MODEL.**
The saved numerical results remain conditional manuscript-style outputs. No SKR,
source, channel, cloud, P2, Greedy, or DP calculation was rerun. No production
evaluator or frozen equation was changed. Numerical reproducibility is a different
question from the existence of a physically justified security bound.

## Scope and authoritative implementation

This audit concerns `configs/manuscript_mobility.json` and
`results/manuscript_mobility_p1_p2_p3_20261019/`, Stage A, Stage B, and the final
saved-data package. It does **not** transfer the different generic heterodyne
equations or the 55-cm/10-µrad historical hardware into these results.

The actual call chain is `src/manuscript_mobility.py:evaluate_source` (lines
168–203) → `scripts/optimize_uniform_manuscript_2d.py:uniform_mi_2d` (line 59)
and `scripts/recheck_manuscript_homodyne_noise.py:security` (lines 84–107).
The angle-dependent channel is the saved
`results/skr_vs_zenith_angle_20261019/run_sweep.py:channel_at_angle` (line 74).
These files were read, not imported or executed. Their hashes and authenticated
input artifacts are recorded in the separate manuscript revision receipt.

## Classification table

| Component | Current Formula | Source | Status | Issue | Proposed Action |
|---|---|---|---|---|---|
| Rate arithmetic | `K_raw = 0.95 I_2D − chi_hom` | adapter `evaluate_source`; recheck `security` | CONSISTENT | Subtraction matches saved fields; this status concerns arithmetic only. | Preserve historical values, qualify their security interpretation. |
| Normalized 2D likelihood | `y ~ N_2(2 sqrt(eta_f)(Re alpha, Im alpha), (1+N) I_2)` | `mi_gh`, lines 110–134; `uniform_mi_2d` | CONSISTENT | Density `1/[2 pi(1+N)]` is correctly normalized as a classical distribution; product factorization is valid for these product QAM PMFs. | Retain as the documented numerical kernel. |
| Bob measurement | Both components above are integrated per transmitted state, with homodyne noise in each. | same kernels; DBL §3, Eq. (3) | INCONSISTENT | A single homodyne measurement yields one quadrature; simultaneous I/Q measurement needs added measurement vacuum. | Choose one physical measurement and derive **both** MI and Holevo for it before any new evaluation. |
| Conditional symplectic eigenvalue | `nu3 = sqrt[V(V−Z²/W)]` | recheck line 94; DBL Eq. (3) | CONSISTENT | Correct ideal homodyne Gaussian conditional expression for the stated standard-form covariance, considered on its own. | Keep its homodyne label; do not pair with a joint I/Q key variable. |
| MI–Holevo pairing | `I_2D` with `chi_hom` | adapter lines 181–198 | INCONSISTENT | Two different Bob measurement variables enter one rate. No theorem justifying this hybrid was identified. | No secure-rate or availability guarantee from its positive values. |
| Source energy | `VA=2 sum p_k |alpha_k|²=2 nbar`, `V=1+VA` | `_validate_ensemble`, lines 68–87; DBL §2 | CONSISTENT | Same coherent amplitudes and source moments used in both numerical branches. Latest three-page PDF omits this convention rather than specifying a conflicting one. | State convention explicitly; never relabel `VA` or reuse moments from another energy. |
| MB parameter identity | product marginal `exp(−nu_raw u²)`, `u=−7.5,...,7.5` | source loader; `exact_cache_provenance.py` | CONSISTENT | Cache additionally stores `nu_repo=42.5 nu_raw`; the two numbers are not interchangeable. | Use `nu_raw` in the manuscript and preserve hex identities. |
| Ideal detector | efficiency `R=1`, electronics `xi_det=0` | current config and protocol | CONSISTENT | Active kernel has no nonideal trusted receiver subsystem. Trust is vacuous at this ideal point. | Describe ideal detection only. |
| Nonideal trusted detector | no active implementation in this manuscript branch | same config; Usenko–Filip 2016 | NOT VERIFIED | No inference about `R<1` or nonzero trusted electronics follows from ideal runs. | Separate receiver transformation and Eve purification assumptions if authorized later. |
| Channel noise convention | `xi_n=xi_ch=0.0186`, output noise `xi_ch <eta>` | recheck lines 87–90 | CONSISTENT | `xi_ch` is input-referred; `N=eta_f xi_f` is output-referred. | Do not insert an additional 1/2 or detector term into these historical fields. |
| Vacuum accounting | `W=1+eta_f VA+N` | recheck line 90 | CONSISTENT | For pure loss, `eta(VA+1)+(1−eta)=1+eta VA`; vacuum is already present. | Do not add `(1−eta)` again to `N`. |
| Fading covariance moments | `eta_f=<sqrt eta>²`; `N=(<eta>−eta_f)VA+xi_ch <eta>` | recheck lines 85–90; Usenko et al. Eq. (5) | CONSISTENT | Correct ensemble second-moment bookkeeping under independent phase-insensitive fading and the stated energy convention. | Explain covariance-level meaning, without claiming a full Gaussian channel identity. |
| Fading MI likelihood | constant Gaussian noise `1+N` for every symbol | `uniform_mi_2d`; actual fading is a mixture | NEEDS CLARIFICATION | Actual conditional noise variance depends on the transmitted amplitude; matching ensemble covariance does not establish equality or a lower bound for discrete-input MI. | Derive or bound the measurement-specific fading MI separately. |
| Source correlation endpoint | `Z_-=2 <sqrt eta>C − sqrt(2Nw)` | recheck line 91; DBL Eqs. (11)–(14) | NEEDS CLARIFICATION | Mapping to the arbitrary-modulation moment constraints requires an operational protocol and correctly estimated moments. | Establish constraints for the adopted measurement and fading process. |
| Worst-case correlation | evaluates only `chi(Z_-)` | recheck lines 91–105; DBL §4 footnotes 11–12 | NOT VERIFIED | A lower bound on correlation need not maximize Holevo over the allowed physical interval. No such maximization is in this saved evaluator. | Verify endpoint sufficiency or maximize over the admissible interval after author approval; no calculation done here. |
| AoA outage | `P0 delta_0 + f_active(eta)`, active support `[0,1]`; moments include `P1=1−P0` | `channel_at_angle`; saved mass checks | CONSISTENT | An atom at zero contributes zero to positive-order moments; active density is not conditioned to mass one. | Preserve atom and absolute mass; disclose flag/conditioning security assumptions. |
| Outage/cloud operational security | effective AoA averaging plus external cloud mask `S=(1−c)Kstar` | saved protocol | NOT VERIFIED | Public erasure flags, abort rules, Eve's side information, accepted sample normalization, and key aggregation are not specified as a proven protocol. | Author must define these before a secure throughput claim. |
| Clipping and availability | maximize raw first; `Kstar=max(0,Kmax_raw)`; available iff `S>0` | source selector and `compare_paths` | CONSISTENT | Correct numerical definitions; positive diagnostic rate is not demonstrated physical QKD availability. | Label as model-defined zero-SKR availability, not an engineering threshold or security certificate. |
| Finite-size/composable/adaptive-fading security | none | current lifecycle/security scope | NOT VERIFIED | Mission bootstrap CIs and physical covariance eigenvalues are not finite-key security bounds. | Retain all existing security/lifecycle restrictions. |

## Measurement derivation (audit reasoning, not an evaluator change)

The defining saved integral is
\[
I_{AB}^{2D}=\sum_k p_k\int_{\mathbb R^2}p_{\rm num}(\mathbf y|k)
\log_2\frac{p_{\rm num}(\mathbf y|k)}{\sum_l p_l p_{\rm num}(\mathbf y|l)}\,d^2\mathbf y.
\]
The complex plane is identified with two real integration coordinates; it does
not itself specify a quantum measurement or its shot-noise normalization.

Use physical coherent amplitudes with `x=a+a†`, `p=−i(a−a†)`, vacuum variance
one. An ideal homodyne x outcome in the adopted *effective Gaussian surrogate*
would have mean `2 sqrt(t) Re(alpha_k)` and variance `1+N`, where `t=eta_f`.
Its likelihood has one real dimension and normalization
`1/sqrt[2 pi(1+N)]`. With a publicly disclosed random choice of x or p, MI
per transmitted pulse is `I(k;Y_Q | Q)`, the average of the two one-dimensional
MIs, not their sum. Sifting/key-use factors must be stated separately.

For the product and symmetric MB/uniform QAM used here, the **current numerical
surrogate** factorizes, giving `I_2D=I_x+I_p=2 I_x`. This algebra explains the
factor-of-two distinction; it does not justify two noiseless quadrature outcomes
from one pulse, or authorize halving the saved rate. Two independent pulses
would change channel-use accounting and the corresponding Eve information.

For ideal heterodyne, represent Bob's complex outcome as
`B=sqrt(t) alpha_k+Zc`, with `E|Zc|²=1+N/2`. Each real component then has
variance `(2+N)/4`. In quadrature-scaled coordinates `2B`, the mean is the
current `2 sqrt(t) alpha_k`, but each component has variance **`2+N`**, not
`1+N`. Scaling both means and noise leaves MI invariant; changing only the
noise or renaming coordinates does not. Its Gaussian conditional covariance
uses `nu3_het=V−Z²/(W+1)`, not the square root used for homodyne. Thus both
the measured variable and the Eve-conditioning expression conflict in the
current pairing. No global correction factor for `K` follows.

For standard form `Gamma=[[V I,Z sigma_z],[Z sigma_z,W I]]`, homodyne x
conditioning gives `Gamma_A|x=diag(V−Z²/W,V)`, whose determinant gives the
saved square root. Ideal heterodyne conditioning gives
`Gamma_A|B=(V−Z²/(W+1)) I`. These conditional-covariance derivations establish
the measurement distinction directly; Gaussian upper-bound applicability to
the actual discrete protocol is an additional requirement.

## Source and noise traceability

The 233-row source roster binds each family, binary64-hex `nu,VA`, full
payload SHA-256, ensemble hash, and its own `C,w`. The payload uses full
support 256 and records the source implementation/settings. Reading these
records verifies identities; this audit does not regenerate a state, a PMF,
source moment, Gram eigensystem, or security functional. Saved provenance
already binds PMF/amplitude reconstruction and the energy identity. Exact
here means the authenticated full-support numerical route, not a symbolic
or interval-certified real number.

All 100 P1 winners are the MB ensemble `(nu_raw,VA)=(0.125,8)`:
`C=4.4721292430667585`, `w=1.1568418954834532e-5`, ensemble SHA-256
`0c762bca0e798dcbca78e2926b643bb1223fa15b606dcd53f8f194db3d85f20c`.
The same authenticated source and source normalization feed MI and covariance.
The source agreement does not resolve their incompatible Bob measurements.
The MB variance lies at the catalog boundary, preventing a continuous-global
source optimality claim. No matched-energy shaping ablation is inferred.

The loss/noise bookkeeping itself is coherent: `N` is output-referred excess
noise, and `xi_f=N/t` is input-referred to the effective transmission (defined
only for `t>0`). Pure-loss vacuum does not belong in `xi_ch`. A future trusted
receiver with efficiency `R` would, in quadrature units, transform a field
variance through `R W+(1−R)` before electronics and measurement noise. Its
security purification must also distinguish trusted receiver modes from Eve.
This illustrative identity is not an approved nonideal detector model; adding
electronics to `xi_ch` is not an equivalent trusted-detector implementation.

## Fading, exact moments, and the remaining security gap

For a fixed source and fading independent of its symbol, physical homodyne
statistics have `E[Y_x|k]=2 <sqrt eta> Re(alpha_k)` and
`Var(Y_x|k)=1+xi_ch <eta>+4 Var(sqrt eta) (Re alpha_k)²`.
Averaging the last term over the symmetric source gives
`Var(sqrt eta) VA`, explaining `N`. The full conditional law is a mixture
over eta, however. Replacing it by the same Gaussian for every symbol changes
more than the covariance; for discrete inputs no MI identity or bound is
established by moment matching alone. True fading also correlates the two
quadrature amplitudes through the common fading value.

There is a useful *conditional* link to arbitrary-modulation moment bounds:
with `c1=<sqrt eta>C`, `c2=<sqrt eta> nbar`, and
`nB=<eta> nbar+xi_ch <eta>/2`, the expression
`2c1−2 sqrt[w(nB−c2²/nbar)]` reduces algebraically to the saved `Z_-`.
This is an audit derivation, not a new numerical evaluation. It shows that
non-Gaussian fading need not, by itself, invalidate a moment-based bound if
its required constraints are legitimately established. It does **not** prove
the current surrogate MI is the observed MI, that the selected endpoint is
worst case, or that adaptive/correlated mission data satisfy an iid-block
security theorem. A physical covariance is necessary but not sufficient.

The separate AoA atom is retained in both moments without active-link
renormalization. If it is publicly flagged and discarded, conditional moments
and rate-per-attempt factors would change and must be derived together.
Cloud blockage is an additional modeled erasure, not a second application of
the AoA probability. A Gaussian surrogate for this mixed law is not literally
the flagged-erasure measurement distribution. Cloud/source/position labels
and any estimation/selection rules must be public side information in a
future security statement. None is supplied by a mobility optimizer.

## Proposed corrections — NOT APPLIED

1. **Homodyne option:** declare Bob's quadrature choice and sifting protocol;
   use the matching one-dimensional discrete-input likelihood and homodyne
   Holevo conditioning. Derive/estimate the fading likelihood or a proven MI
   lower bound. Do not infer corrected results by scaling old outputs.
2. **Heterodyne option:** declare the two-quadrature measurement; derive its
   signal/noise normalization including added vacuum and use the matching
   heterodyne conditional covariance. Re-establish parameter estimation and
   source constraints under that measurement.
3. For either option, establish a physically admissible correlation domain and
   worst-case Holevo treatment. DBL's endpoint caveat is not resolved by
   successful eigenvalue or entropy arithmetic.
4. Specify stationarity/block/bin assumptions, publicly known state/source
   labels, parameter-estimation confidence bounds, AoA/cloud erasure/abort
   rules, and cross-block key aggregation. Add finite-size/composable claims
   only with the corresponding proof and approved implementation.
5. Only after explicit author approval, implement an isolated corrected model
   and separately authorized new results. Retain the existing experiment
   unchanged for comparison. This task makes **no such implementation or run**.

## Primary references checked

- [Denys, Brown, Leverrier, Quantum 5, 540 (2021)](https://doi.org/10.22331/Q-2021-09-13-540),
  [author paper](https://arxiv.org/pdf/2103.13945): §2 (SNU and energy), §3
  Eq. (3) (measurement-dependent conditional eigenvalue), §4 Eqs. (11)–(14)
  and footnotes 11–12 (correlation interval caveat). This source supplies the
  arbitrary-modulation framework; it does not validate this hybrid evaluator.
- [Usenko et al., New J. Phys. 14, 093048 (2012)](https://doi.org/10.1088/1367-2630/14/9/093048),
  [author paper](https://arxiv.org/pdf/1208.4307): Eq. (5) explains fading
  covariance noise for Gaussian-state protocols. Transfer to discrete-input
  likelihoods is not established by that covariance identity.
- [Usenko and Filip, Entropy 18(1), 20 (2016)](https://doi.org/10.3390/e18010020),
  [author paper](https://arxiv.org/pdf/1601.03105): trusted preparation and
  detection noise must be assigned to the correct subsystems; this is not
  proof of a nonideal discrete-modulation receiver in the present branch.

Downloaded primary-paper PDFs and hashes are preserved in
`results/manuscript_ieee_revision_20261020/references/` and its input manifest.
The source-supported statements above are distinguished from the explicit
audit derivations and from unresolved security assumptions.

## Repository and publication boundary

Frozen spec actual SHA-256:
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`;
historical expected:
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
The discrepancy is preserved, not repaired. The generic frozen ideal-heterodyne
model and the separately authorized literal manuscript evaluator have different
measurement conventions; this audit does not promote the latter to frozen
conformance. Keep `UNVALIDATED_SECURITY_MODEL`,
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, and Objective C `USER_STOPPED`.
No training, final-test/held-out access, baseline/threshold approval, commit,
push, or external manuscript overwrite occurred.
