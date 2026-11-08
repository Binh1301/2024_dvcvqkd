# Phase 5B independent implementation review

Reviewed 2026-11-07 against the author attachment and `phase5b_implementation_plan.md`. Scope: the three new configs, nominal beam helper, cloud candidate/window helpers, historical scalar-noise audit, lookup noise comparison, and their connected existing LOS/cloud/finite-size interfaces. Review was read-only apart from this document.

No critical or important implementation defect was found in the reviewed checkpoint. The separate author setup preserves the original reference; the full-angle convention produces a transmitter waist distinct from the receiver footprint; nominal capture is explicitly limited to diffraction-only centered geometry. Candidate construction requires mode and threshold approval, provenance, a matching rigid realization, and explicit cloud layer/LOS spacing. The translated windows preserve the exact 1500 m offset and threshold the same sampled Gaussian field. Existing LOS sampling and binary erasure are reused without introducing optical extinction or a second signal loss.

The historical audit checks sealed files and producer bindings, then reproduces stored effective-noise scalar identities without invoking the quantum evaluator. It supports historical channel noise 0.0186 SNU plus separately specified detector noise 0.005 SNU; the requested 0.0136 SNU remains a distinct target. The prepared recipe is explicitly unauthorized, preserves a finite source catalog, and separates historical replay geometry from mission-coordinate approval.

## Findings communicated to implementer

- Minor: `compare_lookup_setup` initially reports noise `inf` versus `inf`, or `-1` versus `-1`, as matching. Reproduction: assign the same value to reference `channel_excess_noise_snu` and protocol `xi_ch`, then inspect `noise_comparison[0]['matches']`. Missing values remain unresolved and NaN mismatches; the selected-reference loader refuses every case, so this is inaccurate diagnostic validation rather than unsafe admission. Add explicit finite/nonnegative guards and regression cases. The implementer acknowledged this and is applying the guard/tests; this review does not claim to have verified that later revision.
- Minor: the copied numerical role label `DIAGNOSTIC_ONLY_NOT_A_GATE_FOR_THIS_APPROVED_EXPERIMENT` could imply historical approval transfers to the pending recipe. Replace its wording with inherited diagnostic-only status and explicit absence of execution authorization. The recipe's top-level execution/publication flags already remain false. The implementer acknowledged the clarification.

## Independent checks

- `python -m pytest tests/test_phase5b_physical_cloud.py -q`: **12 passed in 0.83s** at the reviewed checkpoint.
- Recomputed all five declared regeneration input hashes: optimized setup, original protocol, geometry CSV, source catalog, and source payload binding match.
- Recomputed the 1091-file protected snapshot: only the declared existing-code change `src/uav_qkd/skr_lookup.py` differs. Historical inputs/results and protected reference/configuration files remain byte-identical.
- Inspected scalar auditing, LOS interior-path fixture, native stored-rate replay, and single accumulated finite-size penalty coverage. No new research SKR evaluations were performed by this review.

Limitations: discrete LOS sampling can miss a sufficiently narrow opaque crossing; spacing/convergence validation remains necessary before a scientific baseline. The nominal beam report does not establish full manuscript channel coupling. Final report/validation-plan assembly and subsequent implementer edits were outside this checkpoint; rerun the final suite and hashes after those edits. No quantum-formula revalidation, paper run, lookup regeneration, threshold approval, or evidence promotion was performed.
