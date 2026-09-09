# Known issues and publication blockers

Audit date: 2026-09-10. The table below is the checked current ledger; older
numerical decisions remain in DECISION_LOG.md and EVIDENCE.md.

| ID | Severity | Area | Issue | Current evidence | Required resolution | Blocks preliminary MC? | Blocks publication? |
|---|---|---|---|---|---|---|---|
| KI-001 | CRITICAL | Security | Production Holevo uses only \(Z_-\), not the full admissible interval. | src/cvqkd/holevo.py | Implement/verify \(Z_-,Z_+,Z_{\rm phys}\), empty-interval failure, and \(\max_{Z\in I}\chi_{BE}(Z)\). | YES for security/SKR plots | YES |
| KI-002 | CRITICAL | Phase noise | No post-action \(\epsilon_{\rm total}=\epsilon_{\rm base}+c_\phi V_A\). | No C_n_phi2/tau_phi2/c_phi symbols in src or configs | Freeze parameters and implement causal phase chain; use total epsilon in MI/security. | YES for phase/epsilon/SKR plots | YES |
| KI-003 | CRITICAL | Channel | No scintillation \(H_{\rm sc}\), AoA \(B_{\rm AoA}\), raw \(T\), or \(p_{>1}\) path. | src/channel/fso_channel.py | Resolve intended fading implementation or explicitly re-scope the model before channel figures. | YES for target fading plots | YES |
| KI-004 | MAJOR | Wavelength | Manuscript/code SI-unit consistency cannot be completed; any ambiguous propagation use of lambda must be ruled out. | Source accepts wavelength_m and converts only empirical extinction to nm; no current manuscript source/PDF | Provide the current manuscript and audit every propagation lambda expression in metres. | NO for deterministic plots | YES for manuscript alignment |
| KI-005 | CRITICAL | Numerical security | Support/tolerance policy is not approved for the active C4 source path. | PROJECT_STATE.md; production Gram artifacts | Complete an approved, provenance-bound numerical gate; do not treat current diagnostics as certification. | YES for security/SKR plots | YES |
| KI-006 | MAJOR | Optimization | Moving-domain inner-max gradient is undefined because the full interval solver is absent. | holevo.py and gram_moments.py | Validate endpoint/interior value and gradient behavior after KI-001. | YES for learned/SKR plots | YES |
| KI-007 | MAJOR | Security domain | Empty security intervals are not represented in the active code. | No Z_L/Z_U guard in holevo.py | Fail closed before covariance/entropy evaluation. | YES for security/SKR plots | YES |
| KI-008 | MAJOR | Numerical tolerances | Existing MI/Gram tolerances are bound to the prior scalar-epsilon/lower-endpoint path. | NUMERICAL_CONVERGENCE_PREREGISTRATION.md and results | Rebind or explicitly scope convergence evidence after the target path is implemented. | YES for target SKR | YES |
| KI-009 | MAJOR | Geometry | GS minimum-distance and degeneracy monitoring exists as diagnostics, but no current learned roster is certified. | optimization/constraints.py; amplitude-domain docs | Monitor d_min and certify every selected realized ensemble before publication. | NO for deterministic QAM/PMF | YES |
| KI-010 | MAJOR | Peak domain | Hard peak guard is implemented, but its current evidence scope is finite realized rosters, not continuous policy support. | joint_ps_gs.py; AMPLITUDE_DOMAIN_DECISION.md | Keep claims finite and hash-bound or produce a separately approved domain certificate. | NO for deterministic plots | YES |
| KI-011 | MAJOR | Parameters | Target phase/scintillation/AoA parameters and mapping rules are not frozen in config. | configs/default.yaml, channel.yaml | Author-approve values/rules without test access before any target MC. | YES for target channel/phase plots | YES |
| KI-012 | MINOR | Documentation | Existing historical protocol docs contain scalar/lower-endpoint terminology. | Specialized docs and archived artifacts | Leave historical records intact; add explicit target/current boundary when directly referenced. | NO | NO, if not used as current claim |
| KI-013 | MAJOR | Turbulence | No frozen Rytov/aperture-averaging to scintillation parameter mapping exists. | No v_sc or H_sc implementation/config field | Author-approve the mapping or state that the target scintillation factor is not yet numerically defined. | YES for scintillation plots | YES |

## Claim boundary

The deterministic 256-QAM, PMF, orbit, and current transmitter-geometry
diagnostics do not require training or security certification. Current physical
channel diagnostics can describe only the implemented atmospheric/pointing path;
they must not be labeled as the target scintillation/AoA model.
