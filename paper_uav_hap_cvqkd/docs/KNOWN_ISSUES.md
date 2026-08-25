# Known issues and publication blockers

1. **No numerical paper results.** Sections V--VI are empty; no figure definitions, experimental table, result values, or final claims can be reproduced.
2. **Missing numerical parameters.** Link/optical parameters, `beta`, `V_min/V_max`, Fock cutoff, sample budgets, optimizer settings, and seed policy are not fully specified by the paper.
3. **Variance notation conflict.** The draft changes from `sigma_r` to undefined `sigma_s` in its PDT equations. The frozen implementation follows Eqs. (21)--(24): Rayleigh scale equals per-axis standard deviation. Legacy code used `sqrt(total_variance/2)`.
4. **Standard-form security blocker.** The paper covariance assumes quadrature-symmetric standard form, but arbitrary learned PMFs/geometries need not satisfy it. Strict code rejects such ensembles. No full-covariance proof is invented.
5. **Exact CSI oracle.** Pilot estimation and authenticated feedback are described narratively but not modeled quantitatively.
6. **Asymptotic only.** Parameter-estimation confidence regions, finite-size corrections, authentication, reconciliation leakage, and privacy-amplification costs are absent.
7. **Ideal detector only.** Detector efficiency and electronic noise are not in the implemented paper path.
8. **No reconciliation feasibility.** A fixed `beta` does not establish a realizable code for learned low-entropy PMFs.
9. **PS/GS attribution.** Weighted centering/scaling causes PMF changes to alter normalized/physical coordinates. Raw-geometry freezing is not physical-coordinate freezing.
10. **Fock truncation.** Every run must report trace error and cutoff convergence over its complete `V_A` range.
11. **Eigendecomposition gradients.** Gradients may be ill-conditioned near repeated or thresholded density eigenvalues.
12. **No environment lock.** `requirements.txt` declares interfaces, not an author-validated publication lockfile.
13. **Legacy results are incompatible.** July checkpoints use a three-input PS network and fixed `V_A`; they cannot initialize or verify the paper architecture.
14. **Strict learned training is scientifically blocked.** The paper uses a scalar-`Z` standard-form covariance, while unconstrained PS/GS updates generally break quadrature symmetry. The strict path correctly stops; the exploratory override is not security evidence.
15. **Adaptive-variance fairness is unresolved.** Pointwise `V_min/V_max` bounds do not impose a common fading-averaged energy budget. Adaptive-`V_A` gains require matched average/peak energy and validation-optimized fixed-`V_A` baselines.
16. **Excess-noise adaptivity is not demonstrated.** The current sampler varies `T` but supplies one configured `epsilon` value to all states. A distribution or block estimator is required before claiming learned `epsilon` adaptation.
17. **Optional geometry regularizers are not active.** The executed loss is Eq. (184); Eq. (185) coefficients are effectively zero. Nonzero separation/peak/drift terms require author-approved coefficients and a resolved raw-geometry scale gauge.
18. **No optimized MB comparison.** The smoke baseline evaluates an explicit `nu`; publication claims require validation-only optimization and untouched test evaluation.
19. **Channel-model scope is narrow.** Homogeneous Kruse attenuation and beam wander omit scintillation, altitude profiles, clouds, background light, optical efficiencies, and tracking-loop dynamics.
20. **No common photon budget.** Before comparing fixed and adaptive modulation variance, define and enforce a shared average photon-number budget and peak constraint.
21. **Seed derivation was hardened after review.** Training epochs now use namespaced BLAKE2b-derived seeds rather than arithmetic increments; a regression test checks 1,000 epochs against validation/test namespaces.
