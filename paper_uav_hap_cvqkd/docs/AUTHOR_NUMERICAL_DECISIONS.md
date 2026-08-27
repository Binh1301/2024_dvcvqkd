# Author numerical decisions

Status: **author channel/energy/security values and software-preregistered
engineering choices are recorded; numerical convergence is blocked by the
bounded CPU resource check**. Publication-scale optimization remains
forbidden until every unresolved row and convergence gate is closed. The
classification labels used below are `AUTHOR_APPROVED` for prospective author
choices, `DERIVED` for equations evaluated from those choices, and
`CONVERGENCE_SELECTED` only for values later selected by preregistered
convergence tests. Diagnostic RNG settings are separately marked
`SOFTWARE_PREREGISTERED` and are not scientific parameters.

`AUTHOR_APPROVAL_REQUIRED=YES` means that the current repository must not pick
the value. `NO` means the rule is already fixed by the immutable model or by a
reproducibility contract; it is still reported in every artifact.

## Software-preregistered engineering addendum (2026-08-27)

These values were frozen without test access and before convergence outcomes.
They are not `AUTHOR_APPROVED` physical assumptions and are not
`CONVERGENCE_SELECTED` numerical settings.

| Area | SOFTWARE_PREREGISTERED value | Evidence/status |
|---|---|---|
| MI | grid `64,128,256,512,1024,2048,4096`; five CRN seeds `202607..202611`; tolerance `0.002 bit + 0.001|I_ref|` | First fixture/replication exceeded 60 s; equal-unit observed-workload extrapolation exceeds 1 h but is not a proven runtime lower bound; no selected count |
| Fock | grid `48,56,64,72,80,96,112,128`; trace `1e-10`; metric-specific tolerances in `NUMERICAL_CONVERGENCE_PREREGISTRATION.md` | Dependency-blocked by missing MI evidence; cutoff-128 boundary trace probe is noncertifying |
| Pseudoinverse | grid `1e-14..1e-10`, candidate `1e-12` | Sensitivity not run; candidate remains unapproved/unselected |
| Optimizer | Adam; PS/GS/VA rates `3e-4/1e-4/1e-4`; dual rate `1e-2`; clip `1.0`; zero regularizers | Three-step smoke passed all nine software checks |
| Training lifecycle | batch/fresh states `16`; cap `2000`; patience `100`; delta `1e-5 bit`; validation budget margin `0.1 SNU` | Preregistered only; no publication training |
| State/statistical counts | validation `128`; held-out test `4096`; ten seeds `26082701..26082710`; Student-t 95% CI over seed means | Test outcomes untouched |
| Baseline evaluation batching | `8` states; sum raw statewise SKR then divide once | Search not run because numerical settings are unresolved |

Rows below that still show `null` for these engineering choices are superseded
by this dated addendum and the machine-readable `configs/default.yaml`. MI sample
count, Fock cutoff, validation/test AWGN counts, and baseline selections remain
genuinely unresolved rather than inheriting defaults.

| Area | Symbol/config name | Meaning and experimental role | Frozen constraints | Literature/config bound or candidate | AUTHOR_APPROVAL_REQUIRED |
|---|---|---|---|---|---|
| Physical | `h_HAP`, `channel.h_hap_m` | HAP altitude used to derive link length | `h_HAP>h_UAV`; vertical primary scenario | **AUTHOR_APPROVED:** `20000 m` | **NO** |
| Physical | `h_UAV`, `channel.h_uav_m` | UAV altitude | `0<=h_UAV<h_HAP` | **AUTHOR_APPROVED:** `1000 m` on the same altitude datum | **NO** |
| Physical | `L_link` | Vertical optical path length; never an independent propagation input | `h_HAP-h_UAV` at `zeta=0` | **DERIVED:** `19000 m` | **NO** |
| Physical | `lambda`, `channel.wavelength_m` | Optical wavelength | finite, positive; compatible with extinction model | **AUTHOR_APPROVED:** `1.55e-6 m` (`1550 nm`) | **NO** |
| Physical | `W0`, `channel.beam_waist_m` | Transmit 1/e2 intensity radius | finite, positive | **AUTHOR_APPROVED:** `0.0157 m` (`1.57 cm`) | **NO** |
| Physical | `a_UAV`, `channel.aperture_radius_m` | Receive-aperture radius | finite, positive; radius, not diameter | **AUTHOR_APPROVED:** `0.075 m` (`7.5 cm`) | **NO** |
| Physical | `V`, `channel.visibility_km` | Homogeneous visibility in Kruse attenuation | finite, positive; nominal scenario only | **AUTHOR_APPROVED:** `200 km`, explicitly nominal good weather, not universal conditions | **NO** |
| Physical | `C_n^2`, `channel.cn2_m_minus_two_thirds` | Constant beam-wander strength | finite, positive, units m^-2/3 | **AUTHOR_APPROVED:** `1e-16 m^-2/3`; homogeneous-path sensitivity assumption | **NO** |
| Physical | `sigma_x,sigma_y,sigma_z` | Position-jitter standard deviations | nonnegative metres; independent zero-mean Gaussian components | **AUTHOR_APPROVED adoption of manuscript values:** `0.0521,0.0502,0.0703 m`; source limitation remains reportable | **NO** |
| Physical | `sigma_theta,sigma_phi,sigma_psi` | Attitude-jitter standard deviations | nonnegative radians; frozen lever-arm equation | **AUTHOR_APPROVED adoption of manuscript values:** `0.00260,0.00204,0.00406 rad`; source/coordinate limitation remains reportable | **NO** |
| Physical | boresight | Deterministic pointing offset | exactly zero; otherwise Rayleigh law is invalid | frozen idealization | **NO** |
| Physical | fixed optical throughput | Loss outside atmosphere/aperture | active model is unit throughput; detector efficiency is not inserted here | omission must be accepted or a genuine model amendment authorized | **YES** |
| Physical | `epsilon_min`, `minimum_snu` | Lower input-referred excess-noise endpoint | `0<=epsilon_min<epsilon_max` | **AUTHOR_APPROVED:** `0.001 SNU` | **NO** |
| Physical | `epsilon_max`, `maximum_snu` | Upper input-referred excess-noise endpoint | finite and strictly above lower endpoint | **AUTHOR_APPROVED:** `0.04 SNU` | **NO** |
| Physical | epsilon law | Sensitivity distribution | independent bounded uniform; nonzero variance | **AUTHOR_APPROVED:** `Uniform[0.001,0.04]` input-referred SNU, an assumed operating domain rather than a measured joint law | **NO** |
| Physical | `T`--epsilon relationship | Joint channel-state law | statistically independent, iid, separate namespaced RNGs | no empirical/mechanistic coupling is available | **NO** unless new evidence authorizes a model amendment |
| Physical | Channel diagnostic realization | Reproduces/checks the approved channel generator without training | base seed `202612`, count `1,000,000`, quantiles `1,10,50,90,99%`; independent of all data splits | **SOFTWARE_PREREGISTERED**, not an author physical value or a convergence selection; exact hashes in `frozen_channel_diagnostics.json` | **NO** |
| Physical | `eta_atm,W_L,T0^2,sigma_turb,sigma_UAV,sigma_r,Gamma,R,p(T)` | Propagation quantities evaluated from the approved scenario | equations and units in `FROZEN_CHANNEL_DIAGNOSTICS.md`; must remain inside physical support | **DERIVED:** diagnostic status PASS; no value is `CONVERGENCE_SELECTED` | **NO** |
| Security | `beta_rec`, `cvqkd.beta_reconciliation` | Reverse-reconciliation efficiency in `K=beta I-chi` | finite `0<beta<=1`; identical for all schemes | **AUTHOR_APPROVED:** `0.95` | **NO** |
| Security | `ATTACK_CLASS_APPROVAL` | Statewise collective-attack interpretation | all six conditions in `SECURITY_SCOPE_FREEZE.md` | compatible with DBL-2021 only after citation/theory approval | **YES** |
| Security | `FADING_PROTOCOL_SCOPE_APPROVAL` | Oracle simulation versus operational block/bin claim | default code is exact oracle CSI and statewise asymptotic evaluation | operational binning/estimation/aggregation is not implemented | **YES** |
| Energy | `V_min`, `cvqkd.v_min_snu` | Minimum statewise modulation variance | finite `0<V_min<V_max` | **AUTHOR_APPROVED:** `0.1 SNU` | **NO** |
| Energy | `V_max`, `cvqkd.v_max_snu` | Maximum statewise modulation variance | finite and above `V_min` | **AUTHOR_APPROVED:** `4.0 SNU` | **NO** |
| Energy | `V_A_budget`, `cvqkd.v_a_budget_snu` | Fading-average variance budget; mean photon budget is half | `V_A_budget>=V_min`; common to all schemes | **AUTHOR_APPROVED:** `1.5 SNU`; **DERIVED** mean photon budget `0.75` | **NO** |
| Energy | `n_peak`, `cvqkd.n_peak_photons` | Common maximum coherent-state photon number per symbol | finite, positive; `max_i|alpha_i|^2<=n_peak`; one value for all 11 schemes | **AUTHOR_APPROVED:** `30 photons` on every final physical ensemble, with no clipping | **NO** |
| Energy | `n_peak_author_approved` | Machine-readable approval gate | literal `true` after approval | **AUTHOR_APPROVED:** `true` | **NO** |
| Energy | `peak_domain_scope` | Scope over which peak feasibility is asserted | verifier accepts only `complete_preregistered_realizations`; continuous support/bins remain blocked without a future external hash-bound certificate | **AUTHOR_APPROVED:** `complete_preregistered_realizations` | **NO** |
| Energy | GS gauge | Removes positive global-scale non-identifiability | `(1/64) sum_k |z_k|^2=1`; does not alter physical alpha | implemented and tested | **NO** |
| Energy | average-budget enforcement | Adaptive-VA feasibility mechanism | projected dual ascent; complete-validation feasibility required | frozen model | **NO** |
| Optimization | optimizer | Parameter update family | implementation supports Adam | `adam` in config, but not author-ratified for publication | **YES** |
| Optimization | `learning_rates.ps` | PS-network Adam learning rate | finite, positive; recorded parameter group | `null` | **YES** |
| Optimization | `learning_rates.gs` | global-GS Adam learning rate | finite, positive | `null` | **YES** |
| Optimization | `learning_rates.va` | adaptive-VA Adam learning rate | finite, positive | `null` | **YES** |
| Optimization | `energy_dual_learning_rate` | Projected dual-ascent step | finite, positive for adaptive-VA modes | `null` | **YES** |
| Optimization | batch size | Number of iid train states per update | current protocol requires equality to `train_fading_samples` | `null` | **YES** |
| Optimization | maximum epochs | Hard training cap | positive integer | `null` | **YES** |
| Optimization | validation patience | Early-stopping patience | positive integer | `null` | **YES** |
| Optimization | validation minimum delta | Material raw-SKR improvement | finite, nonnegative bits | `null` | **YES** |
| Optimization | `validation_energy_budget_margin_snu` | Test-blind margin added to validation mean VA for adaptive checkpoint eligibility | nonnegative; require `mean_validation(V_A)+margin<=V_A_budget`; fixed before training | `null`; must be justified from a preregistered validation/statistical rule | **YES** |
| Optimization | checkpoint criterion | Select highest complete-validation mean raw SKR among budget- and peak-feasible checkpoints | validation only; deterministic; test inaccessible | implemented | **NO** |
| Optimization | gradient clipping | Global-gradient norm safeguard | positive when enabled; active interface uses 1.0 | 1.0 is present but lacks author ratification | **YES** |
| Optimization | regularizers | Separation, soft peak, drift coefficients | primary experiment fixes all to zero; hard peak rule is separate | `(0,0,0)` frozen by model | **NO** |
| Numerics | MI tolerance | Stable-suffix absolute/relative error tolerance | finite, nonnegative and fixed before convergence | both `null` | **YES** |
| Numerics | MI candidate sample grid | Nested Monte Carlo counts | strictly increasing positive integers; largest is reference | `null`; replication seeds 202607--202611 are frozen software seeds | **YES** |
| Numerics | Fock tolerance | Stable-suffix tolerance for moments, symplectic eigenvalues, `chi_BE`, and raw `K` | fixed before execution; trace tolerance separately enforced | **SOFTWARE_PREREGISTERED:** moments/symplectic `1e-7+1e-6|ref|`, information `1e-6+1e-5|ref|` bit | **NO** |
| Numerics | Fock cutoff grid | Candidate Hilbert-space dimensions | strictly increasing integers >=2; includes convergence at `sqrt(n_peak)` boundary | `null`; no cutoff may be certified yet | **YES** |
| Numerics | Holevo symmetry tolerance | Relative anisotropy/cross-covariance gate | active `1e-8`; fail-closed standard-form guard | fixed implementation safety contract | **NO** |
| Numerics | Symmetry diagnostic scale floor | Prevents division by zero only when normalizing quadrature residuals | active `1e-15`; does not repair the covariance | fixed implementation safety contract | **NO** |
| Numerics | Density trace tolerance | Maximum Fock density trace error | active **SOFTWARE_PREREGISTERED** `1e-10`; matches convergence configuration | fixed before execution; not a selected cutoff | **NO** |
| Numerics | Density eigenvalue/pseudoinverse threshold | Suppresses eigenmodes in `sqrt(tau)` and `tau^(-1/2)`; affects `w,Z,chi_BE` | active candidate `1e-12`; must lie on a preregistered sensitivity grid and pass all selected ensembles | configuration contains `1e-12` with approval gate `false`; publication retention requires sensitivity evidence | **YES** |
| Numerics | Holevo physicality tolerance | Material-negative `w`, covariance discriminant/eigenvalue, and negative-chi fail gate | active `1e-10`; only within-tolerance repairs are logged | fixed implementation safety contract | **NO** |
| Numerics | Pseudoinverse sensitivity grid/tolerance | Validation-only comparison of `C,w,Z,chi_BE` against the smallest threshold | strictly increasing positive grid; absolute/relative acceptance values fixed pre-test | all `null`; dedicated tooling implemented | **YES** |
| Numerics | Exact selected-roster convergence reconstruction | Post-selection rebuild of all four baselines and every selected checkpoint on the complete frozen validation realization | binds canonical roster/config/state, source artifact hashes, deterministic ensemble hashes, and exact MI/Fock/threshold settings; missing/extra/duplicate traces fail | implemented by `validate_selected_roster_convergence.py`; no value is selected by this mechanism | **NO** |
| Numerics | MI counts for train/validation/test | Samples per symbol in optimization and final evaluation | positive; validation/test not below convergence-selected count | `null` | **YES** |
| Numerics | numerical precision | Density/covariance/optimization dtype and device scope | CPU float64/complex128 in convergence contract | implemented and environment-locked | **NO** |
| Numerics | state counts | Train/validation/test fading realization sizes | positive integers; fixed split seeds; no overlap | `null` | **YES** |
| Statistics | independent training seeds/count | Optimization replication unit | distinct nonempty list; every attempted run retained | `null` | **YES** |
| Statistics | split seeds | Dataset/AWGN reproducibility | train 202601/202602, validation 202603/202604, test 202605/202606; namespaced and distinct | frozen software choices, independent of outcomes | **NO** |
| Statistics | interval method | Primary uncertainty statement | two-sided 95% Student-t over independent training-seed test means; paired contrasts | preregistered protocol | **NO** |
| Baselines | `nu_MB`, `cvqkd.mb_nu` | Fixed-MB reference exponent | finite, nonnegative; not validation optimized | **AUTHOR_APPROVED:** `0.1` | **NO** |
| Baselines | optimized-MB nu grid | Validation-only shaping search | strictly increasing finite nonnegative values; test forbidden | **AUTHOR_APPROVED domain:** `[0,0.3]`; **SOFTWARE_PREREGISTERED discretization:** step `0.01` (31 candidates), fixed before outcomes | **NO** |
| Baselines | fixed-VA grid | Common outer grid for four fixed baselines and PS/GS/PS+GS | inside `[V_min,min(V_max,V_A_budget)]`; peak-infeasible candidates ineligible | **SOFTWARE_PREREGISTERED:** `0.1:0.1:1.5 SNU` (15 candidates), a uniform discretization of the author-approved budget-feasible interval | **NO** |
| Baselines | `baseline_search.state_batch_size` | Validation evaluation batching only; sum statewise raw SKR then divide once | positive integer; may not change averaging or candidate CRN | `null` | **YES** |
| Baselines | tie breaking | Resolve equal validation scores | highest raw SKR, then lower VA, then lower nu | implemented | **NO** |

## Approval protocol

1. The author supplies values/sources for every **YES** row without consulting
   held-out test outcomes.
2. A resolved configuration sets `n_peak_author_approved: true` only after the
   numerical value and scope are signed off.
3. Run `scripts/preconvergence_domain_check.py`. If any benchmark is excluded
   at `V_min`, revise the proposed common domain prospectively; do not delete or
   weaken that benchmark.
4. Only after the precheck passes may validation-only finite-fixture MI/Fock
   convergence and pseudoinverse sensitivity be executed to select numerical
   settings. Publication training remains blocked until those preliminary
   diagnostics pass under the approved configuration.
5. After training and validation-only selection, run
   `scripts/validate_selected_roster_convergence.py --selection-roster ...`
   using the roster-only schema. It reconstructs every
   selected baseline and checkpoint on the complete frozen validation
   realization and emits exact MI/Fock/pseudoinverse evidence. Then run
   `scripts/combine_convergence_evidence.py --selection-roster ...`; it
   independently reconstructs the roster and rejects missing, extra, duplicate,
   or hash/settings-mismatched traces. Final held-out evaluation remains blocked
   until this post-selection evidence and the pre-test manifest validate.
