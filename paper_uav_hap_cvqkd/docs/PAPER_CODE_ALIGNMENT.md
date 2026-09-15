# Current paper/code alignment audit

Audit date: 2026-09-16. This is the primary current matrix. The intended
mathematical model is in FINAL_MODEL_SPEC.md; PAPER_TO_CODE.md is structural
only.

Statuses: ALIGNED, PARTIAL, MISMATCH, NOT VERIFIED, NOT IMPLEMENTED.

| Item | Paper | Intended model | Code | Status | Evidence |
|---|---|---|---|---|---|
| Physical channel | \(T_{\rm raw}=\eta_{\rm atm}H_{\rm sc}H_{\rm p}B_{\rm AoA}\) | Power \(T\), active \(0<T\le1\), outage \(K=0\) | Composite factors, raw diagnostics, physical admission, and outage metadata are implemented; the attached manuscript scenario is bound in the active config | ALIGNED | src/channel/fso_channel.py, state_distribution.py, configs/default.yaml |
| Scintillation | \(H_{\rm sc}\) | \(\ln H_{\rm sc}\sim N(-v_{\rm sc}/2,v_{\rm sc})\), mean one | Cached Hufnagel–Valley profile, Rytov integral, finite-aperture factor, and normalized lognormal sampler derive \(v_{\rm sc}\) without an override | ALIGNED | src/channel/scintillation.py, configs/default.yaml |
| Pointing | \(H_{\rm p}\) | Generalized Gaussian-beam loss with Rician displacement | Existing \(W_L,z_R,\eta_{p0},\Gamma,R\) law is active with generalized Rician jitter and explicit HAP convention | ALIGNED | src/channel/pointing_error.py, fso_channel.py |
| AoA | \(B_{\rm AoA}\) | Zero factor is an outage; Rayleigh FOV gate | Orientation/outage primitives and hard gate exist; the attached scenario uses the explicit zero-turbulence AoA fixture and FOV | ALIGNED | src/channel/aoa.py, fso_channel.py, configs/default.yaml |
| Physical-domain \(T\) | No silent min(T_raw,1); report \(p_{>1}\) | Restrict/renormalize active states | Rejection/resampling admits the truncated active law; no floor or clipping | ALIGNED | src/channel/fso_channel.py, diagnostics.py |
| Wavelength SI | Extinction may use nm; propagation uses m | \(\lambda_m=10^{-9}\lambda_{nm}\) | Channel functions and phase module use wavelength_m; extinction converts to nm | ALIGNED | src/channel/atmospheric_loss.py, pointing_error.py, phase_noise.py |
| Phase variance | Effective \(C_{n,\phi}^2\), tau_phi2, \(c_\phi\) | Same physical turbulence source; validated profile-to-scalar mapping required | Canonical phase module records common-turbulence semantics and derives tau/c; production mapping/value remains unresolved and fails closed | PARTIAL | src/channel/phase_noise.py, scripts/_train.py |
| Epsilon causal order | \(\epsilon_{\rm total}=\epsilon_{\rm base}+c_\phi V_A\) | MI/security use post-action epsilon | Policy receives epsilon_base; trainer and active baseline paths derive one epsilon_total for MI/Holevo | ALIGNED | state_distribution.py, joint_ps_gs.py, trainer.py |
| 256-QAM / PS | 64 orbit masses, \(p_{k,r}=q_k/4\) | Fourfold-symmetric adaptive PS | 2 -> 128 -> 64, exact C4 expansion | ALIGNED | probabilistic_shaping.py, qam256.py |
| GS | 64 complex prototypes, \(z_{k,r}=i^rz_k\) | One global geometry, no state conditioning | Global unit-RMS C4 prototypes | ALIGNED | geometric_shaping.py |
| \(V_A\) | 2 -> 64 -> 1, bounded physical mapping | State-conditioned scalar \(V_A\) | Log-domain bounded mapping | ALIGNED | joint_ps_gs.py |
| Physical mapping | \(E_z=\sum q_k|z_k|^2\), \(\alpha=\sqrt{V_A/(2E_z)}i^rz_k\) | One statewise scalar, no centering/deformation | Exact scalar normalization and C4 invariants | ALIGNED | normalization.py, tests |
| MI noise | \(\sigma_c^2=1+T\epsilon_{\rm total}/2\) | Same post-action epsilon | MI receives trainer-derived epsilon_total; direct function remains an epsilon-consuming primitive | ALIGNED | mutual_information.py, trainer.py |
| Full \(Z\) interval | \(I=[\max(Z_-,-Z_{\rm phys}),\min(Z_+,Z_{\rm phys})]\) | Empty interval fails closed | Computes both bounds and the physical intersection | ALIGNED | holevo.py, tests/test_holevo_interval.py |
| Holevo max | \(\chi_{BE}^{ub}=\max_{Z\in I}\chi_{BE}(Z)\) | Endpoint/interior maximum over moving interval | Deterministic grid plus bounded refinement over every cell; selected branch remains tensor-connected | PARTIAL | holevo.py, tests/test_holevo_interval.py |
| Empty security interval | \(Z_L>Z_U\Rightarrow\) failure | No clipping or repair | Raises structured SecurityDomainError with interval diagnostics | ALIGNED | holevo.py, tests/test_holevo_interval.py |
| Raw training \(K\) | \(K=\beta I-\chi\), no statewise positive clipping | Statewise before fading average | train_step uses negative raw SKR | ALIGNED | trainer.py, secret_key_rate.py |
| Average photon dual | \(g_B=\operatorname{mean}(V_A/2)-\bar n_{\rm budget}\) | Separate from peak rule | Dual uses mean V_A against stored V_A budget; algebraically equivalent | ALIGNED | trainer.py, configs/default.yaml |
| Peak constraint | \(\max_i|\alpha_i|^2\le n_{\rm peak}\) | Common hard fail-closed rule | Forward guard plus optimizer rollback | ALIGNED | joint_ps_gs.py, trainer.py |
| Moving-domain gradient | Differentiate value function only after interval solver is fixed | No global smoothness claim | Fixed-candidate regions retain autograd; argmax/boundary changes are explicit nonsmooth points | PARTIAL | holevo.py, gram_moments.py, tests/test_holevo_interval.py |
| Numerical certification | Full-support source moments plus target security observables | Threshold/provenance must be approved | C4 Gram production path exists; support threshold remains unapproved | PARTIAL | PROJECT_STATE.md, results/production_gram_certification.json |

## Audit conclusion

The transmitter and raw-SKR plumbing are aligned with the intended C4 design,
and the causal phase/post-action epsilon chain and full-interval Holevo
implementation are present. The attached manuscript's Hufnagel–Valley,
finite-aperture scintillation, pointing, AoA, and mixed physical-(T) law are
implemented and verified as a channel-only diagnostic. The common-turbulence
phase mapping remains unresolved; target security/SKR plots and publication
claims remain blocked.

The manuscript source is external. The attached local PDF
`C:\Users\admin\Downloads\2026__Binh_s_work__Copy_ (1).pdf` was read for this
channel audit; it is used as the source for the Hufnagel–Valley and
transmittance-distribution equations only. It does not authorize security or
publication claims.
