# Paper/code alignment for the frozen numerical protocol

## Pre-publication numerical freeze status (2026-08-27)

The manuscript must add `beta_rec=0.95`, the approved physical-channel table,
the independent assumed `epsilon ~ Uniform[0.001,0.04] SNU` operating domain,
`V_A in [0.1,4.0] SNU`, `E[V_A]<=1.5 SNU`, the common hard
`max_i|alpha_i|^2<=30` rule without clipping, the global GS unit-RMS gauge, and
the validation-only fixed-baseline procedure. It must not yet state numerical
values for MI samples or Fock cutoff: neither is `CONVERGENCE_SELECTED`.

The frozen MI run exceeded the bounded CPU resource window at the first
`uniform_low_va_0.1`, 4096-sample fixture/replication; the full preregistered
workload has an observed-unit extrapolation above one hour on the recorded host;
this is a feasibility estimate, not a proven wall-clock lower bound.
Consequently Fock raw-SKR convergence, pseudoinverse sensitivity, and baseline
selection remain dependency-blocked. The cutoff-128, 30-photon-boundary trace
probe is explicitly noncertifying and must not appear as a paper result.

This audit is scoped to the transmitter, constraints, baseline selection, and
security language. `FINAL_MODEL_SPEC.md` was not modified.

## ALIGNED

| Topic | Implemented/paper contract |
|---|---|
| Physical mapping | `p_(k,r)=q_k/4`, `E_x=sum_k q_k|z_k|^2`, and `alpha_(k,r)=sqrt(V_A/(2E_x)) i^r z_k`; no PMF-weighted translation or per-symbol clipping. |
| C4 notation | 64 deterministic row-major orbits, four exact rotations, tied probabilities, zero displacement, and zero pseudomoment. |
| Global GS | One channel-independent 64-prototype geometry is shared over all states. |
| Adaptive PS | The 64 orbit masses depend on exact oracle features `[log10(T),epsilon]`. |
| Adaptive VA | Only the scalar `V_A(T,epsilon)` adapts, within the author-frozen box. |
| Energy budget | Fixed policies satisfy `V_A<=V_A_budget`; adaptive policies use projected dual ascent and complete-validation feasibility. |
| GS gauge | `z_k=g_k/sqrt((1/64)sum_l|g_l|^2)`, so `(1/64)sum_k|z_k|^2=1` without changing physical alpha. |
| MI/Holevo identity | The same final `Ensemble={p_i,alpha_i}` object is passed unchanged to both branches. |
| Baseline selection | Uniform, Binomial, fixed MB, and optimized MB are selected only on validation; PS/GS/PS+GS fixed VA uses the same outer VA grid. |

## PAPER_UPDATE_REQUIRED

1. Add the common physical-domain equation after the scalar normalization:

   \[
   A_{\max}(T,\epsilon)=\max_{k,r}|\alpha_{k,r}(T,\epsilon)|^2
   \le n_{\rm peak}.
   \]

   State that the single preregistered `n_peak` applies to all eleven schemes,
   is checked on final physical amplitudes, and is neither post-hoc clipping nor
   a soft-penalty definition. Insert the exact paragraph from
   `AMPLITUDE_DOMAIN_DECISION.md` after author approval.

2. Add the GS scale gauge explicitly:

   \[
   z_k=\frac{g_k}{\sqrt{64^{-1}\sum_l|g_l|^2}},\qquad
   64^{-1}\sum_k|z_k|^2=1.
   \]

   Explain that `g -> c g`, `c>0`, leaves every physical amplitude unchanged.

3. Replace any statement that peak energy is guaranteed by `V_A<=V_max` or by
   the GS gauge alone. The rare-amplitude counterexample in
   `AMPLITUDE_DOMAIN_DECISION.md` shows that neither bounds the joint PS+GS
   parameterization.

4. Describe baseline selection exactly: one common validation-only VA grid;
   fixed MB uses preregistered `nu_MB`; optimized MB uses the Cartesian
   validation grid; peak-infeasible candidates are ineligible; no test metric
   participates; ties prefer lower VA then lower nu.

5. State adaptive-budget enforcement and checkpoint selection exactly:
   projected dual ascent on mean `V_A-V_A_budget`, rollback of any peak-invalid
   physical optimizer step, and highest complete-validation mean raw SKR among
   checkpoints satisfying `mean_validation(V_A)+margin<=V_A_budget` and the
   peak constraint. A held-out negative budget slack invalidates that comparison
   artifact and may not trigger retraining or reselection.

6. Describe convergence scope exactly. Finite bad/medium/good/boundary fixtures
   are prechecks, not learned-domain certificates. Publication evidence must
   enumerate and hash-bind every selected baseline ensemble/checkpoint, and must
   include a density-pseudoinverse-threshold sensitivity audit for `C,w,Z,chi_BE`.
   State that the exact producer and combiner independently reconstruct the
   selected roster on the complete frozen validation realization and bind every
   trace to its source and deterministic physical-ensemble hashes.

7. Replace security language with the approved paragraph in
   `SECURITY_SCOPE_FREEZE.md`. Until its two author decisions are signed, use
   the fallback wording: asymptotic covariance-based DM-CV-QKD rate functional,
   ideal heterodyne, reverse reconciliation, exact oracle CSI, no assigned
   attack class, and no finite/composable/general-attack claim.

8. Correct any claim that Bob-estimated/feedback-impaired CSI is simulated.
   The code consumes exact instantaneous oracle `(T,epsilon)` and models no
   estimator, delay, quantization, feedback overhead, or authentication cost.

## CODE_UPDATE_REQUIRED

No unresolved code/model mismatch was found in the scoped implementation.
Publication execution is nevertheless blocked by unresolved author values and
subsequent convergence evidence. A future nonzero boresight, nonideal detector,
finite-size security treatment, coupled `T`--epsilon law, or optical-throughput
factor would be a genuine model/code amendment and must not be inserted through
configuration prose alone.
