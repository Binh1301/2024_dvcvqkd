# Current paper/code alignment audit

Audit date: 2026-09-10. This is the primary current matrix. The intended
mathematical model is in FINAL_MODEL_SPEC.md; PAPER_TO_CODE.md is structural
only.

Statuses: ALIGNED, PARTIAL, MISMATCH, NOT VERIFIED, NOT IMPLEMENTED.

| Item | Paper | Intended model | Code | Status | Evidence |
|---|---|---|---|---|---|
| Physical channel | \(T_{\rm raw}=\eta_{\rm atm}H_{\rm sc}H_{\rm p}B_{\rm AoA}\) | Power \(T\), active \(0<T\le1\), outage \(K=0\) | sample_fso_channel uses atmospheric loss times pointing loss and beam-wander displacement | MISMATCH | src/channel/fso_channel.py, docs/FINAL_MODEL_SPEC.md |
| Scintillation | \(H_{\rm sc}\) | Scenario/state fading factor | No scintillation sampler or H_sc field | NOT IMPLEMENTED | src/channel/ search |
| Pointing | \(H_{\rm p}\) | Gaussian-beam aperture/pointing loss | pointing_power_transmittance exists | ALIGNED | src/channel/pointing_error.py |
| AoA | \(B_{\rm AoA}\) | Zero factor is an outage | No AoA factor or outage branch | NOT IMPLEMENTED | src/channel/ search |
| Physical-domain \(T\) | No silent min(T_raw,1); report \(p_{>1}\) | Restrict/renormalize active states | Code directly constructs \(T>0\); no T_raw or p_gt_1 | MISMATCH | src/channel/fso_channel.py |
| Wavelength SI | Extinction may use nm; propagation uses m | \(\lambda_m=10^{-9}\lambda_{nm}\) | Channel functions accept wavelength_m; extinction converts to nm; no active phase expression | PARTIAL | src/channel/atmospheric_loss.py, pointing_error.py, diagnostics.py |
| Phase variance | External \(C_{n,\phi}^2\), tau_phi2, \(c_\phi\) | Scenario-level, two-stage surrogate | No C_n_phi2, tau_phi2, or c_phi | NOT IMPLEMENTED | src/ and configs/ search |
| Epsilon causal order | \(\epsilon_{\rm total}=\epsilon_{\rm base}+c_\phi V_A\) | MI/security use post-action epsilon | Sampled epsilon is passed unchanged to policy, MI, and Holevo | MISMATCH | state_distribution.py, joint_ps_gs.py, trainer.py |
| 256-QAM / PS | 64 orbit masses, \(p_{k,r}=q_k/4\) | Fourfold-symmetric adaptive PS | 2 -> 128 -> 64, exact C4 expansion | ALIGNED | probabilistic_shaping.py, qam256.py |
| GS | 64 complex prototypes, \(z_{k,r}=i^rz_k\) | One global geometry, no state conditioning | Global unit-RMS C4 prototypes | ALIGNED | geometric_shaping.py |
| \(V_A\) | 2 -> 64 -> 1, bounded physical mapping | State-conditioned scalar \(V_A\) | Log-domain bounded mapping | ALIGNED | joint_ps_gs.py |
| Physical mapping | \(E_z=\sum q_k|z_k|^2\), \(\alpha=\sqrt{V_A/(2E_z)}i^rz_k\) | One statewise scalar, no centering/deformation | Exact scalar normalization and C4 invariants | ALIGNED | normalization.py, tests |
| MI noise | \(\sigma_c^2=1+T\epsilon_{\rm total}/2\) | Same post-action epsilon | Correct formula for direct epsilon argument | PARTIAL | mutual_information.py |
| Full \(Z\) interval | \(I=[\max(Z_-,-Z_{\rm phys}),\min(Z_+,Z_{\rm phys})]\) | Empty interval fails closed | Only \(Z_-\) is computed | NOT IMPLEMENTED | holevo.py |
| Holevo max | \(\chi_{BE}^{ub}=\max_{Z\in I}\chi_{BE}(Z)\) | Endpoint/interior maximum over moving interval | No interval solver or maximum | NOT IMPLEMENTED | holevo.py |
| Empty security interval | \(Z_L>Z_U\Rightarrow\) failure | No clipping or repair | No interval exists in active path | NOT IMPLEMENTED | holevo.py |
| Raw training \(K\) | \(K=\beta I-\chi\), no statewise positive clipping | Statewise before fading average | train_step uses negative raw SKR | ALIGNED | trainer.py, secret_key_rate.py |
| Average photon dual | \(g_B=\operatorname{mean}(V_A/2)-\bar n_{\rm budget}\) | Separate from peak rule | Dual uses mean V_A against stored V_A budget; algebraically equivalent | ALIGNED | trainer.py, configs/default.yaml |
| Peak constraint | \(\max_i|\alpha_i|^2\le n_{\rm peak}\) | Common hard fail-closed rule | Forward guard plus optimizer rollback | ALIGNED | joint_ps_gs.py, trainer.py |
| Moving-domain gradient | Differentiate value function only after interval solver is fixed | No global smoothness claim | No inner interval/max gradient path | NOT IMPLEMENTED | holevo.py, gram_moments.py |
| Numerical certification | Full-support source moments plus target security observables | Threshold/provenance must be approved | C4 Gram production path exists; support threshold remains unapproved | PARTIAL | PROJECT_STATE.md, results/production_gram_certification.json |

## Audit conclusion

The transmitter and raw-SKR plumbing are aligned with the intended C4 design.
The channel/phase causal chain and full-interval security definition are not
implemented. Therefore security, phase-noise, and SKR plots for the target model
are not presentation-safe yet. Deterministic constellation/PMF/orbit plots do
not depend on those blockers.

No manuscript source is present in the repository. The referenced
C:\Users\HP\Downloads\2026__Binh_s_work (8).pdf is unavailable; the only
local PDF is an unrelated 2024 satellite-to-ground reference and its text stream
is corrupted, so manuscript claims are NOT VERIFIED.
