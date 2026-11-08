# Phase 4 independent interface review

What this change does: Adds separate Source-A and finite-size reference configs,
coordinate-derived geometry, opaque moment/SKR adapters, and explicitly approved
cloud coupling. Existing QAM/MB Z and w mathematics are author-confirmed and were
not reviewed, rederived, or changed.

Review scope: new four Python modules, two configs, integration tests, implementation
plan, supplied Phase 4 task, and connected configuration/finite-key/blockage helpers.
Expected use is local scientific interface integration; no mission was executed.

## Must fix

1. **Geometry can disagree with forwarded physical altitudes**
   (`src/uav_qkd/hap_uav_channel.py:137-145`).
   - What this is: The physical callback receives both config altitudes and
     coordinate-derived distance/angle.
   - Problem: With the reference config and
     `waypoint_geometry([0,0,20000],[0,0],2000,.92)`, the callback receives
     `slant_distance_m=18000` but altitudes `20000/1000`, whose vertical separation
     is 19000. A different `tau_zen` likewise disagrees with the config value.
     These are accepted inputs to the new public interface.
   - Fix: Carry HAP/UAV altitude and zenith-transmittance identity in the geometry
     state, then reject config disagreement or forward one authoritative consistent
     set. Add a mismatched-altitude/tau regression test.
   - If skipped: Different physical callbacks can use different geometries for
     the same request, silently combining inconsistent channel inputs.

2. **Moment boundary accepts impossible scalar inputs**
   (`src/uav_qkd/hap_uav_channel.py:107-122`).
   - What this is: The wrapper validates external channel moments before building
     the scalar SKR request.
   - Problem: `FadingMoments(.5,0.,0.,'unit fixture',probability_mass=2.)` is accepted
     and maps to zero transmission. For the declared power domain [0,1], the
     first moment cannot exceed the square-root moment. Retained probability mass
     above one is also accepted and is used in detector-noise forwarding.
   - Fix: Validate the complete declared scalar bounds, including `m1 <= mh`
     and probability mass in [0,1], with explicit roundoff tolerance where needed.
     Validate retained-mass consistency for the native retained-moment contract.
   - If skipped: Malformed provider outputs can silently become incorrect channel
     requests or bypass the backend as a zero-transmission case. This finding
     concerns scalar I/O validation only, not any QAM/Z/w formula.

3. **Partial parameter match is labeled full configuration compatibility**
   (`src/uav_qkd/phase4_audit.py:18-37`).
   - What this is: The lookup audit returns a machine-readable compatibility flag.
   - Problem: After matching the twelve enumerated physical fields, the function
     returns `configuration_compatible=True` even if `beta=.5`, modulation
     normalization differs, and reference noises are unresolved. Boresight,
     atmospheric altitude, and curvature also are not compared.
   - Fix: Rename the flag to explicitly identify the physical subset match and
     keep full compatibility unresolved/false, or compare all required physical
     and scalar protocol fields and fail closed on missing values. Add a test
     whose listed physical fields match but normalization/beta differ.
   - If skipped: A future caller can mistake a partial match for permission to
     reuse an incompatible lookup. The current bundled receiver30 mismatch is
     correctly rejected, so this does not overturn that current audit conclusion.

Verdict: Fix 1-3 before treating the interfaces as validated for reuse.

## Verification and limits

`CURRENTLY_VERIFIED_PASS`: `python -m pytest -q -p no:cacheprovider
tests/test_phase4_integration.py` — 12 passed in 0.60 s. Three standalone scalar
boundary reproductions confirmed the findings above. These were analytic inputs
and callbacks; no quantum/backend computation, simulation, optimizer, or new
experiment data was generated.

Cloud approval checks require literal `True`; erasure skips the backend and
valid-signal count, while attenuation requires an explicit post-loss provider.
The new configs preserve the requested reference values and missing inputs.

Not checked: Z/w mathematics, publication security, paper runs, full original-suite
rerun, or independently recomputed historical source hashes. Static graph rates
`r[j]` remain an acknowledged integration limit for analog time-varying `r[k,j]`.
