# Repository C,w audit

The selected stored sources were produced by the full-support C4 weighted-Gram
path declared in their authenticated cache payloads. They are NOT values from
the legacy Fock-cutoff backend. This audit reads source/metadata; it does not
invoke production source generation or a3600-second fallback.

Method R in the comparison means the unchanged stored C,w for the exact input
hash. Its current evidence class remains INSUFFICIENT_EVIDENCE.

| Function and file:lines | Input arguments | Implemented expression/data flow | Library/precision | Dimensions | Rank rule | Convergence/cache behavior |
|---|---|---|---|---|---|---|
| `scripts/run_exact_mb_test2.py:57-61` `nu_mb_repo` | nu_raw | nu_repo=42.5*nu_raw | Python binary64 | scalar | No rank selection | finite/nonnegative guard |
| `scripts/run_exact_mb_test2.py:82-90` `ensemble_hash` | Ensemble p,alpha,declaredVA | SHA256 of dtype/shape and float.hex arrays | binary64 exact hex | 256 ordered symbols | N/A | identity only; not convergence |
| `scripts/run_exact_mb_test2.py:93-113` `build_mb_ensemble` | config,nu_raw,va | MB PMF on canonical reference grid, scalar amplitude energy normalization | Torch float64/complex128 | 1x256 | N/A | PMF conversion check atol/rtol1e-14 |
| `scripts/run_exact_mb_test2.py:135-374` `ExactMBEvaluator` | config,output,source_evaluator,cache dir | hash-bound source lookup or c4_gram_source_moments call | JSON binary64 stored C,w | 256 | depends on source solver | cache writer discards detailed fallback rows |
| `src/modulation/qam256.py:16-42` `c4_orbit_indices` | device | deterministic64 fourfold orbits; no symbol-label replacement | integer Torch | 64x4 | N/A | bijection256 checked |
| `src/modulation/qam256.py:84-98` `square_qam256` | alpha0,dtype,device | alpha0/sqrt30 times centered16x16 grid | Torch complex128 | 256 | N/A | finite positive scale guard |
| `src/modulation/qam256.py:101-109` `canonical_square_qam256` | dtype,device | global unit-RMS gauge of square grid | Torch complex128 | 256 | N/A | energy normalization |
| `src/modulation/qam256.py:129-140` `maxwell_boltzmann_pmf` | nu_mb,dtype,device | exp(-nu_repo*abs(canonical_grid)^2)/sum | Torch float64 | 256 | N/A | finite positive PMF and tied rotations |
| `src/modulation/normalization.py:22-69` `physical_amplitudes` | p,relative_constellation,VA,minimum_energy | alpha=sqrt(VA/(2*sum p|x|^2))*x; no centering | Torch float64/complex128 | B x256 | N/A | PMF/energy/VA guards |
| `src/modulation/joint_ps_gs.py:69-139` `Ensemble` | p,alpha,declaredVA,geometry,flags | same ordered physical input for MI and Holevo | Torch float64/complex128 | B x256 | N/A | PMF,VA=2nbar,C4,pseudomoment checks |
| `src/modulation/joint_ps_gs.py:294-319` `reference_ensemble` | kind,batch_size,modulation_variance,nu_mb,bounds | frozen canonical geometry+PMF+physical_amplitudes | Torch float64/complex128 | B x256 | N/A | Ensemble.validate |
| `src/cvqkd/holevo.py:44-53` `coherent_state_vectors` | amplitudes,fock_cutoff | exp(-abs(alpha)^2/2)*alpha^n/sqrt(n!) | Torch complex128 | B x M xNF | Fock truncation; no renormalization | cutoff integer>1 |
| `src/cvqkd/holevo.py:56-63` `density_operator` | ensemble,fock_cutoff | tau_nm=sum p F_n conjugate(F_m), Hermitian symmetrization | Torch complex128 | B xNF xNF | Fock rank<=min(M,NF) | ensemble validation; trace checked by caller |
| `src/cvqkd/holevo.py:66-70` `annihilation_operator` | fock_cutoff,device | a[n-1,n]=sqrt(n) | Torch complex128 | NF xNF | N/A | finite Fock basis |
| `src/cvqkd/holevo.py:73-153` `support_restricted_source_moments` | tau,fock,p,eigenvalue_tolerance,optional eigensystem | support A,Q coefficients; C=sum sqrt(lambda_i lambda_j)|Aij|^2; corrected orthogonal-residual w | Torch complex128 | NF density and retained-r support | lambda>declared tolerance; reject lambda<-tolerance | diagnostic residual identity, not full-support certificate |
| `src/cvqkd/holevo.py:590-666` `dense_fock_holevo_information` | ensemble,T,epsilon,cutoff,numerical guards | dense sqrt(tau), MPsqrt, direct C and weighted variance; downstream Holevo | Torch complex128 | NF xNF | lambda>tolerance for BOTH square roots | trace/physicality caller guards; legacy diagnostic |
| `src/cvqkd/holevo.py:669-738` `c4_gram_holevo_information` | ensemble,T,epsilon,numerical guards | calls Gram source moments then existing covariance branch | Torch complex128 + AP fallback | four64x64 sectors | active source path full-support | not called in this task |
| `src/cvqkd/holevo.py:741-792` `holevo_information` | ensemble,T,epsilon,backend and guards | dispatch Gram primary vs explicit legacy Fock backend | Torch | depends on selected backend | depends on source method | not used for independent computations |
| `src/cvqkd/gram_moments.py:28-37` `_sectors` | per-symbol orbit p,prototype z | weighted coherent Gram transformed into four C4 sectors | Torch complex128 | four64x64 | none here | Hermitian construction |
| `src/cvqkd/gram_moments.py:43-124` `_fast_from_sectors` | p,z,sectors | whole matrix roots/solves and stable weighted C4 residual | Torch complex128, custom Frechet functions | four64x64 | all positive; condition<=1e6; backward residual<=1e-12 | otherwise fallback; residual identity abs scaled by max(1,abs(w)) |
| `src/cvqkd/gram_moments.py:126-133` `_fallback` | p,z | subprocess worker on exact binary64 hex | Python/mpmath worker | four64x64 | precision ladder1050/1250/1450 | 3600s production timeout; NOT called here |
| `src/cvqkd/gram_moments.py:135-257` `c4_gram_source_moments` | Ensemble,density_eigenvalue_tolerance,physicality_tolerance | accepted full-support C,w; diagnostic threshold does not truncate support | Torch complex128 or mpmath | 256 through four64x64 | fast positive/condition gate or full-support AP fallback | fallback FULL_SUPPORT_CONVERGED required |
| `src/cvqkd/spectral_frechet.py:67-70` `hermitian_inverse_sqrt` | positive Hermitian matrix | U invsqrt(lambda) Udagger, custom Loewner VJP | Torch complex128 | 64x64 sector | all eigenvalues>0; no threshold cutoff | fail if nonpositive |
| `src/cvqkd/spectral_frechet.py:73-76` `hermitian_sqrt` | positive Hermitian matrix | U sqrt(lambda) Udagger, custom Loewner VJP | Torch complex128 | 64x64 sector | all eigenvalues>0; no threshold cutoff | fail if nonpositive |
| `scripts/full_support_c4_worker.py:64-205` `_row` | p,z,digits | mpmath Gram sectors; eigensupport, source C and residual w | mpmath arbitrary precision | four64x64 | requires256 positive eigenvalues at each reported row | returns rank,minimum eigenvalue,C,w,resolved |
| `scripts/full_support_c4_worker.py:208-277` `main` | worker JSON exact-hex arrays and digit ladder | compare final two rows C,w then emit source moments | mpmath | four64x64 | final two rows resolved and rank256 | abs diff <=1e-7+1e-6*maxabs; not relative tiny-w accuracy |
| `scripts/exact_cache_provenance.py:42-73` `verify_source_payload` | payload,settings | source identity/settings/code/newline-alias digest validation | Python/SHA256 | JSON | N/A | provenance only; not numerical convergence |

## Observations

1. The active Gram route is algebraically equivalent to the specified C and w
for these exactly C4-symmetric coherent ensembles, if its full-support/precision
conditions hold. It is an algebraic reformulation, not a different source law.
2. `density_eigenvalue_tolerance=1e-12` in the active source cache is diagnostic
metadata, not the eigenvalue cutoff of its full-support Gram fallback. Applying
that cutoff to the independent Fock/Gram reference would evaluate a different
regularized operator. This experiment reports such cutoff effects explicitly.
3. The historical worker's absolute tolerance1e-7 is about175 times the winner's
stored w. A FULL_SUPPORT_CONVERGED label under that rule alone is not a relative
accuracy certificate at the1e-10 w scale. Exact input hashes and declared digit
settings do not substitute for missing per-precision observations.
4. The cache writer stores the final binary64 C,w,route and support_size, but
omits the complete fallback diagnostic rows. No original per-precision receipt
for these two sources is fabricated or recovered by running a different method.
5. The legacy support-restricted Fock helper already has an explicit correction
for non-unit truncated coherent norms. It does NOT silently normalize the
physical source. Its retained-rank rule and Fock truncation still differ from
an exact infinite-space MP inverse. Dense and support-residual variants are
mathematically equivalent for the same retained operator and normalization.
6. The production Holevo module contains repair/interval branches, but they are
not called by the independent source methods. This experiment never clips w,
alters Eq14/MI/Holevo, or switches Z policy. Limited downstream checks use only
the approved isolated v43 mathematical components, subject to readiness.
7. Mathematical equivalence is separate from numerical equivalence: Hermitian
backward residuals can be tiny while an inverse square root is poorly resolved.
All thresholds, effective ranks, spectral minima and numerical limitations are
retained in convergence_diagnostics.csv and individual job artifacts.

Exact numerical function signatures, source line ranges and file hashes are
in repository_function_inventory.json. The two input ensembles are serialized
under inputs/ and validated in input_validation.json; the original source
cache values and evidence classifications remain unchanged.

## Cache-method detail

| Exact method | Input arguments | Responsibility and numerical boundary |
|---|---|---|
| scripts/run_exact_mb_test2.py:136-181 ExactMBEvaluator.__init__ | config,channel,output,CRN seeds,MI samples,source_evaluator,allow_legacy_exact_import,source_cache_dir | Initializes source cache/settings; default source evaluator is c4_gram_source_moments. Not instantiated for source generation here. |
| scripts/run_exact_mb_test2.py:183-193 _source_identity | ensemble,nu_raw,va | Exact ensemble/parameter/implementation/settings identity; SHA256. |
| scripts/run_exact_mb_test2.py:199-226 _legacy_exact_source | ensemble,nu_raw,identity | Authenticated exact-ensemble import only; not neighboring-parameter interpolation. |
| scripts/run_exact_mb_test2.py:228-274 source_moments | ensemble,nu_raw,va | Cache lookup or source solve; saves C,w,route,support, not complete precision rows. |
| scripts/run_exact_mb_test2.py:276-291 prepare_sources | points,workers | Optional source batch; NOT called. |
| scripts/run_exact_mb_test2.py:293-374 __call__ | nu_raw,va | Legacy channel-dependent MI/Holevo/rate evaluation; NOT used for independent C,w or the approved v43 check. |

A cheap current numerical gate replay (sectors and detached eigensystems ONLY)
shows minimum float eigenvalues about-6.51e-17 and-1.34e-16 for Winner/Fixed.
Backward reconstruction residuals are8.77e-16 and1.47e-15, but the positivity
and condition gates reject both. The active code would require its AP fallback.
No production moment/fallback call is made; read repository_fast_gate_diagnostic.json.
