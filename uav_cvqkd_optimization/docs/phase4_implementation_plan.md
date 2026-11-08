# Phase 4 implementation plan

Author decision: current QAM/MB Z and w implementations are accepted. Do not
rederive, audit, rewrite or replace either formula, its operators or matrices.
Only boundary contracts and value/identity forwarding are tested here.

1. Add a Source-A channel reference config using exactly the manuscript
   Section IV values. Keep missing noise/mission coordinates explicit, not
   inherited from the incompatible receiver30 dataset.
2. Add the IEEE2025 finite-block reference (N=1e8, n/N=.8, three epsilons1e-8).
   Derive n/epsilon; never infer fs, eta_valid, m0 or trajectory block size.
3. Add generic waypoint geometry using existing parent LinkGeometry and
   atmospheric_transmittance_from_tau_zen helpers via read-only explicit loading.
   Reference zenith30 is separate from coordinate-derived waypoint angles.
4. Add typed moments/effective-channel and opaque existing-MB-backend adapters.
   Reuse precomputed moments or injected existing Eq18–20 provider; do not
   duplicate the closed-form moment engine, MI, Holevo, Z or w. Preserve current
   author-confirmed VA=Vmod=2*nbar convention at module boundaries.
5. Add cloud coupling interfaces: approved binary erasure vs approved optical
   attenuation, mutually exclusive. Binary blockage comes from the existing
   LOS model and reduces kept signals. Attenuation needs a sourced dimensionless
   power factor and explicit post-attenuation moment/noise provider; no CLWC
   conversion and no default noise scaling/erasure are invented.
6. Reuse finite_key for the accumulated finite_size_aware_key_yield_proxy and
   keep old Scenario/algorithms/profiles/configs untouched. Test the complete
   geometry→moments→SKR request→cloud→proxy boundary using exact analytic unit
   cases, recording test doubles, and/or replayed existing data, never new fake
   experiment outcomes. Keep callback/backend computation provenance explicit.
7. Add a read-only-input audit CLI, compatibility JSON and three requested
   Vietnamese documents. Run the original suite and new integration tests,
   independently review the new interfaces, and hash-check all old inputs.

No paper-mode, optimization/source jobs, lookup regeneration, new figures,
default changes, core edits, evidence promotion, historical overwrite or
commit/push. The historical frozen hash discrepancy remains recorded; it is
not used to block the safe implementation or to reopen accepted Z/w mathematics.
