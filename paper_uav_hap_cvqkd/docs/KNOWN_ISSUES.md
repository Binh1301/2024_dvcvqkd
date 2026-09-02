# Known issues and publication blockers

Current-state reconciliation (2026-09-01): items 12, 15, 18, and 20 below
contain historical pre-approval wording. Their current replacements are
`NUMERICAL_PARAMETER_FREEZE.md`, `configs/default.yaml`,
`AMPLITUDE_DOMAIN_DECISION.md`, EVID-0009, and EVID-0029. They are retained
for provenance and must not be read as unresolved current values.

1. **No numerical paper results.** Sections V--VI are empty; no figure definitions, experimental table, result values, or final claims can be reproduced.
2. **Numerical freeze remains incomplete.** Link/optical, epsilon, `beta`, energy, optimization, and `N_MC=2048` are frozen/certified as recorded in the current freeze documents. Fock cutoff and pseudoinverse support remain uncertified.
3. **Variance notation conflict.** The draft changes from `sigma_r` to undefined `sigma_s` in its PDT equations. The frozen implementation follows Eqs. (21)--(24): Rayleigh scale equals per-axis standard deviation. Legacy code used `sqrt(total_variance/2)`.
4. **Standard-form security scope.** The frozen transmitter enforces C4 symmetry, zero displacement, and zero pseudomoment by construction. The lower-level covariance code still rejects unsupported asymmetric ensembles; no full-covariance proof is invented.
5. **Exact CSI oracle.** Pilot estimation and authenticated feedback are described narratively but not modeled quantitatively.
6. **Asymptotic only.** Parameter-estimation confidence regions, finite-size corrections, authentication, reconciliation leakage, and privacy-amplification costs are absent.
7. **Ideal detector only.** Detector efficiency and electronic noise are not in the implemented paper path.
8. **No reconciliation feasibility.** A fixed `beta` does not establish a realizable code for learned low-entropy PMFs.
9. **PS/GS attribution is constrained.** The active path has no weighted centering: PS changes orbit probabilities and one statewise scalar, while GS changes one global C4 relative geometry. Claims must still say fourfold-symmetric PS rather than unrestricted 256-way shaping.
10. **Fock/support numerics are not certified.** The cutoff studies show the blocker is support/pseudoinverse conditioning rather than Fock-tail trace loss. Candidate `1e-13` remains outcome-informed, `1e-14` retains only 8--30 of 256 mathematical modes on the pilot roster, and only the near-coincident fixture has a full-support oracle. See `PROJECT_STATE.md`.
11. **Eigendecomposition gradients.** Gradients may be ill-conditioned near repeated or thresholded density eigenvalues.
12. **Historical: no environment lock.** Superseded by the hash-pinned
    `requirements-publication.lock` and the locked-environment evidence in
    EVID-0016. The current local machine still lacks that environment.
13. **Legacy results are incompatible.** July checkpoints use a three-input PS network and fixed `V_A`; they cannot initialize or verify the paper architecture.
14. **Security boundary remains narrow.** Strict C4 learned training now preserves the accepted scalar-`Z` standard form and the paper scripts fail closed. This does not extend the accepted asymptotic covariance-based bound to arbitrary asymmetric modulation or a composable proof.
15. **Historical: adaptive-variance numerical fairness unresolved.** The
    budget, dual learning rate, common box, and validation procedure are now
    frozen in `NUMERICAL_PARAMETER_FREEZE.md` and `configs/default.yaml`;
    numerical support certification remains the separate blocker.
16. **Excess-noise operating domain is author-frozen, not empirically measured.** Production states use independent input-referred `epsilon ~ Uniform[0.001,0.04]` SNU, separate namespaced streams, split hashes, and leakage checks. This is a controlled sensitivity-domain law and must not be presented as measured HAP-UAV coupling.
17. **Optional geometry regularizers are not active.** Exact canonical separation, physical-peak, and phase-aligned drift terms are implemented, but their primary coefficients remain zero. Nonzero coefficients/thresholds require author approval without test-set tuning.
18. **Historical: optimized MB search not numerically frozen.** The
    validation-only grids and reference `nu` are now preregistered in
    `configs/default.yaml`; the search remains `NOT_RUN` because upstream
    numerical gates are blocked.
19. **Channel-model scope is narrow.** Homogeneous Kruse attenuation and beam wander omit scintillation, altitude profiles, clouds, background light, optical efficiencies, and tracking-loop dynamics.
20. **Historical: common energy values unresolved.** `V_A_budget=1.5`,
    `n_peak=30`, and `complete_preregistered_realizations` are author-approved
    and recorded in `AMPLITUDE_DOMAIN_DECISION.md` and the numerical freeze.
    Learned selected-roster certification is still pending.
21. **Seed derivation was hardened after review.** Training epochs now use namespaced BLAKE2b-derived seeds rather than arithmetic increments; a regression test checks 1,000 epochs against validation/test namespaces.
