# Numerical parameter freeze

Status: **author and software-preregistered choices are frozen, but MI execution
hit the bounded CPU resource limit and no MI count or Fock cutoff is
`CONVERGENCE_SELECTED`; publication-scale execution is blocked**. Values are
labelled `AUTHOR_APPROVED`, `DERIVED`, or `CONVERGENCE_SELECTED`. A separately
labelled `SOFTWARE_PREREGISTERED` seed/count is allowed only for deterministic
diagnostics and data generation; it is not a scientific parameter. Any
remaining `null / unresolved` value must fail closed and may not inherit a test,
smoke, or library default.

## 2026-08-27 engineering freeze and execution result

| Area | Frozen value/classification | Execution result |
|---|---|---|
| MI convergence | **SOFTWARE_PREREGISTERED:** counts `64..4096` doubling, five CRN seeds, `0.002 bit + 0.001|I_ref|` | **BLOCKED_RESOURCE_LIMIT:** first 4096-sample fixture/replication exceeded 60 s; an observed-workload extrapolation over 60 equal-structure units is `>1 h`; selected count remains null |
| Fock convergence | **SOFTWARE_PREREGISTERED:** cutoffs `48,56,64,72,80,96,112,128`; trace `1e-10`; moment/symplectic/information tolerances frozen separately | **NOT_RUN_DEPENDENCY:** raw-SKR cutoff test requires MI evidence; selected cutoff remains null |
| Optimizer | **SOFTWARE_PREREGISTERED:** Adam, PS/GS/VA `3e-4/1e-4/1e-4`, dual `1e-2`, clip `1.0`, regularizers `0/0/0` | Three-step full-transmitter smoke passed; no training |
| Lifecycle | **SOFTWARE_PREREGISTERED:** batch `16`, cap `2000`, patience `100`, delta `1e-5 bit`, budget margin `0.1 SNU` | Test-blind; publication entry remains fail-closed |
| Data/statistics | **SOFTWARE_PREREGISTERED:** validation `128`, held-out test `4096`, ten seeds `26082701..26082710`, 95% Student-t CI over seed means | Test realization/outcomes not accessed |
| Baselines | Existing VA/nu grids; state batch `8` | Not scored because MI/Fock settings are unresolved |

The exact convergence preregistration is in
`NUMERICAL_CONVERGENCE_PREREGISTRATION.md`. Machine-readable blocked evidence is
in `results/mi_convergence.json`, `results/fock_cutoff_certification.json`, and
`results/validation_baseline_selection.json`. These artifacts may not be cited
as numerical convergence or performance results.

| Area | Parameter or rule | Frozen value/status | Evidence or required gate |
|---|---|---|---|
| Security | Protocol | Asymptotic reverse reconciliation, ideal heterodyne, exact instantaneous `(T,epsilon)` oracle CSI | `FINAL_MODEL_SPEC.md` |
| Security | `beta_rec` | **AUTHOR_APPROVED:** `0.95` | Identical for every scheme |
| Energy | `V_min` | **AUTHOR_APPROVED:** `0.1 SNU` | Common statewise lower bound |
| Energy | `V_max` | **AUTHOR_APPROVED:** `4.0 SNU` | Common statewise upper bound |
| Energy | `V_A_budget` | **AUTHOR_APPROVED:** `1.5 SNU`; **DERIVED:** mean photon budget `0.75` | Common fading-average constraint |
| Energy | `n_peak` | **AUTHOR_APPROVED:** `30 photons` | One hard final-physical-symbol rule, identical for all eleven schemes; no clipping |
| Energy | Peak-domain approval/scope | `n_peak_author_approved: true`; **AUTHOR_APPROVED:** `complete_preregistered_realizations` | Continuous support/bins remain unavailable without future external certification |
| Energy | Fixed-policy feasibility | `V_min <= V_A <= min(V_max,V_A_budget)` | Exact common box and average budget |
| Energy | Adaptive enforcement | Projected dual ascent on minibatch mean `V_A-V_A_budget`, multiplier projected to nonnegative values | Frozen model Section 8 |
| Energy | Dual learning rate | **SOFTWARE_PREREGISTERED:** `1e-2` | Three-step full-transmitter smoke passed; not performance-tuned |
| Geometry | GS scale gauge | `(1/64) sum_k |z_k|^2 = 1`, applied globally before C4 expansion | Implemented and invariance/gradient tested |
| Geometry | Peak-amplitude domain | Hard fail-closed `max_i|alpha_i|^2<=30` photons | Checked after scalar normalization without clipping; rollback rejects infeasible optimizer steps |
| Regularization | `lambda_sep,lambda_peak,lambda_drift` | `0,0,0` in the primary experiment | Frozen model Section 7 |
| Optimization | Optimizer | Adam, no scheduler currently implemented | Existing training implementation |
| Optimization | PS/GS/VA learning rates | **SOFTWARE_PREREGISTERED:** `3e-4 / 1e-4 / 1e-4` | Explicit Adam parameter groups; tiny smoke only |
| Optimization | Batch size | **SOFTWARE_PREREGISTERED:** `16` | Equals `train_fading_samples` under the current iid protocol |
| Optimization | Maximum epochs | **SOFTWARE_PREREGISTERED:** `2000` | Hard cap; no publication training performed |
| Optimization | Stopping rule | **SOFTWARE_PREREGISTERED:** patience `100`, minimum delta `1e-5 bit` | Complete-validation raw-SKR rule remains test-blind |
| Optimization | Expected-budget margin | **SOFTWARE_PREREGISTERED:** `0.1 SNU` | Require validation mean `V_A + margin <= 1.5 SNU` |
| Optimization | Checkpoint selection | Highest validation raw average SKR among complete-validation-budget-feasible checkpoints | Implemented; test set inaccessible to selection |
| Optimization | Gradient clipping | Global norm `1.0` | Existing frozen implementation; logged as a numerical safeguard |
| Optimization | Independent initialization seeds | **SOFTWARE_PREREGISTERED:** `26082701`--`26082710` | Ten independent runs; CLI rejects unregistered seeds |
| Channel | `h_HAP,h_UAV,zeta` | **AUTHOR_APPROVED:** `20000 m,1000 m,0 rad` | Vertical primary scenario on a common altitude datum |
| Channel | `L_link` | **DERIVED:** `19000 m` | `h_HAP-h_UAV` for `zeta=0`; not an independently tunable input |
| Channel | `lambda,W0,a_UAV,C_n^2` | **AUTHOR_APPROVED:** `1.55e-6 m,0.0157 m,0.075 m,1e-16 m^-2/3` | SI units; waist/aperture are radii |
| Channel | Visibility/scenario | **AUTHOR_APPROVED:** `200 km`, nominal good-weather homogeneous Kruse sensitivity scenario | Must not be described as universal weather or a vertically resolved atmosphere |
| Channel | UAV motion SDs | **AUTHOR_APPROVED adoption of manuscript Table I:** position `(0.0521,0.0502,0.0703) m`; attitude `(0.00260,0.00204,0.00406) rad` | Independent zero-mean Gaussian component/zero-boresight model; source limitation remains disclosed |
| Channel | Derived propagation law | **DERIVED:** `eta_atm=0.931627122110895`, `W_L=0.597290843698307 m`, `T0^2=0.0310421114350335`, `sigma_turb=0.0645921311864522 m`, `sigma_UAV=0.100879602270479 m`, `sigma_r=0.119786633500812 m`, `Gamma=2.00000261222670`, `R=0.425698737510564 m` | Complete equations, units, support, quantiles, limitations, and hashes in `FROZEN_CHANNEL_DIAGNOSTICS.md` and JSON artifact |
| Channel | Physical `T` support/mean | **DERIVED:** `0<T<=0.0289196729404660`; analytic mean `0.0249660838763683` | Transmittance is power, not field amplitude; lower endpoint open |
| Channel | Excess-noise law | **AUTHOR_APPROVED:** independent `Uniform[0.001,0.04]` input-referred SNU | Assumed operating-domain distribution, not a measured HAP-UAV joint distribution; no invented `T-epsilon` coupling |
| Channel | Diagnostic realization | **SOFTWARE_PREREGISTERED:** base seed `202612`, count `1,000,000`, quantiles `(1,10,50,90,99)%` | Reproduction/sanity check only; no `CONVERGENCE_SELECTED` channel value is claimed |
| Channel | Split channel seeds | train `202601`, validation `202603`, test `202605` with BLAKE2b namespaces | Software seeds, frozen independently of outcomes |
| MI | Split AWGN seeds | train `202602`, validation `202604`, test `202606` with BLAKE2b namespaces | Software seeds; paired common randomness for comparisons |
| Data | Train/validation/test state counts | **SOFTWARE_PREREGISTERED:** `16 fresh states/epoch / 128 / 4096` | Split seeds remain distinct; test not accessed |
| MI | Training/evaluation samples per symbol | training **SOFTWARE_PREREGISTERED:** `8`; validation/test **PENDING_CONVERGENCE_SELECTION:** null | `validate_mi_convergence.py` must select the earliest stable suffix against the largest reference count |
| MI | Convergence replications | Five preregistered seeds `202607`--`202611`, reused across configurations | Nested CRN within each replication; reference agreement required across replications |
| MI | Convergence tolerance/grid | **SOFTWARE_PREREGISTERED:** grid `64,128,256,512,1024,2048,4096`; `0.002 bit + 0.001|I_ref|` | Execution resource-blocked; sample count remains **PENDING_CONVERGENCE_SELECTION** |
| Holevo | Fock cutoff | **PENDING_CONVERGENCE_SELECTION:** null | Preregistered grid `48,56,64,72,80,96,112,128`; full rule includes the C4 `|alpha|=sqrt(30)` fixture and raw `K` |
| Holevo | `C,w,Z`, symplectic, `chi_BE`, raw-`K` tolerances | **SOFTWARE_PREREGISTERED:** moments/symplectic `1e-7+1e-6|ref|`; information `1e-6+1e-5|ref|` bit | Not convergence-selected values; criteria fixed before execution |
| Holevo | Density trace tolerance | **SOFTWARE_PREREGISTERED active safeguard:** `1e-10` | Matches `configs/default.yaml`, `configs/cvqkd.yaml`, and the Fock preregistration |
| Holevo | Symmetry/eigen-pseudoinverse/physicality tolerances | symmetry `1e-8`; pseudoinverse candidate `1e-12`; physicality `1e-10` | Pseudoinverse is **PENDING_CONVERGENCE_SELECTION**, approval false until sensitivity passes |
| Numerics | Precision | CPU `torch.float64` and `torch.complex128` | Active implementation |
| Numerics | Environment | CPython 3.12.10; exact packages in `requirements-publication.lock` | Manifest must hash the lock and record device |
| Baselines | Fixed MB reference `nu_MB` | **AUTHOR_APPROVED:** `0.1` | Fixed reference; never validation/test optimized |
| Baselines | Fixed-VA grid | **SOFTWARE_PREREGISTERED:** `0.1:0.1:1.5 SNU` | Uniform discretization of `[V_min,min(V_max,V_A_budget)]`, selected before outcomes; validation only |
| Baselines | Optimized-MB `nu` grid | **AUTHOR_APPROVED domain:** `[0,0.3]`; **SOFTWARE_PREREGISTERED:** step `0.01` | 31 validation-only candidates; deterministic tie-break: lower `V_A`, then lower `nu` |
| Ablations | Fixed `V_A` for PS, GS, and PS+GS learned modes | **null / unresolved** | Requires the same validation-only feasible `V_A` grid and matched training budget; test cannot select it |
| Evaluation | Final held-out state/AWGN counts | states **SOFTWARE_PREREGISTERED:** `4096`; AWGN **PENDING_CONVERGENCE_SELECTION:** null | Test is evaluated once after all selections freeze |
| Statistics | Aggregation | Report every seed; primary estimate is the mean of independent training-seed test means | Seed is the independent optimization unit |
| Statistics | Confidence interval | Two-sided 95% Student-t interval over independent training-seed test means; paired intervals for contrasts | No pooling states as independent training replicates |
| Provenance | Required record | Resolved config/hash, Git revision/dirty diff, environment lock, device, seeds, state hashes, checkpoint hash, raw per-state data | Required by publication protocol |

## Numerical validation rule

MI validation uses nested common random numbers. The largest evaluated sample
count is the explicit reference; a smaller count passes only if it and every
larger candidate remain within the declared absolute-plus-relative tolerance
for every bad/medium/good state and every listed transmitter configuration.

Fock validation applies the same stable-suffix rule simultaneously to `C`,
`w`, `Z`, and `chi_BE`, while independently enforcing the density-trace
tolerance. Bad/medium/good states are selected on validation without looking at
learned outputs: nearest states to componentwise `(T,epsilon)` quantiles
`(10%,90%)`, `(50%,50%)`, and `(90%,10%)`, scaled by validation interdecile
ranges.

Finite fixture scripts are executable only after all physical/numerical fields
and the explicit `n_peak` approval/scope are supplied. They fail closed before
claiming publication coverage otherwise. They include a C4 boundary-amplitude
fixture at `sqrt(n_peak)`, optimized-MB grid values, and peak-feasible baseline
VA cases, but remain explicitly finite-fixture diagnostics. Publication
convergence evidence must separately enumerate and hash-bind every selected
baseline ensemble and learned checkpoint, identically across MI, Fock, and
pseudoinverse-threshold artifacts. Native finite-fixture scripts emit a null
selected-roster certification and therefore cannot open the combined gate.
After selection, a `selected-convergence-roster-v1` artifact freezes the config,
validation state, selection hashes, and checkpoint entries without creating a
dependency on the later combined-evidence hash. Then
`validate_selected_roster_convergence.py` reconstructs every
actual selected transmitter on the complete frozen validation realization and
binds each trace to its checkpoint/baseline source hash and deterministic
physical-ensemble hash. The combiner independently repeats reconstruction and
requires exact roster, canonical config, state, settings, and tolerance matches.
A soft penalty or observed maximum is never accepted as domain evidence.

## Blocking amplitude proof

The unit-RMS gauge implies `sum_k |z_k|^2=64`, hence each relative prototype is
finite for a fixed parameter vector. Physical scaling, however, contains

`1/sqrt(E_x)`, where `E_x=sum_k q_k |z_k|^2`.

The softmax guarantees `q_k>0` but supplies no uniform positive lower bound;
the learned prototypes likewise have no minimum magnitude. A sequence can put
nearly all PMF mass on near-zero prototypes and vanishing mass on a prototype
whose relative magnitude approaches eight. Then `E_x` approaches zero and the
rare physical amplitude grows without a finite global bound even at fixed
`V_max`. The selected additional rule is the common author-controlled hard
peak-photon domain. Its software mechanism is implemented, but its numerical
threshold and scope remain unresolved; therefore no cutoff is certified by
this freeze.
