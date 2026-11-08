# Phase 5B Physical Setup and Cloud Candidate Implementation Plan

> Inline implementation with superpowers:test-driven-development, then one independent review. User explicitly requests implementation now; no additional design approval or commits.

**Goal:** Record author-tuned optical/noise inputs separately, establish the actual old lookup noise from sealed scalar records, calculate Gaussian beam sanity values, and prepare an unapproved LOS-cloud candidate and exact regeneration input recipe.

**Architecture:** Reuse the existing Gaussian beam helper, CLWC/LOS and binary-erasure coupling. Add a candidate builder gated by explicit mode/threshold approval; keep original reference/defaults/results immutable. Extend lookup rejection to compare both noise inputs as well as optical fields.

**Spec:** Phase5B author attachment and existing Phase4/5A interfaces.

## Scope and checks

- [x] Snapshot protected files and baseline tests; bind author attachment SHA-256.
- [x] Write failing tests for six tuned values/provenance, waist/footprint SI arithmetic, exact translated observation windows and shared threshold mask, candidate approval/LOS/clear-versus-erased signal accounting, scalar historical-noise trace and lookup refusal.
- [x] Add `configs/channel/optimized_physical_setup.yaml` and `configs/cloud/binary_los_blockage_candidate.yaml`; preserve manuscript reference. Noise .0136 is the author target, not a relabel of old .0186.
- [x] Implement beam sanity helper and static-reference cloud-window sampler. Reject nonrigid per-cluster velocities; evaluate Gaussian field analytically at exact coordinates, not snapped cell indices.
- [x] Build candidate LOS model only after mode/threshold approval and required layer/spacing inputs; map explicitly to existing binary_erasure policy. No attenuation coefficient, fake rates, or new cloud realization.
- [x] Compare lookup optical and noise values, verify producer/receipt hashes, and replay only stored scalar effective-noise identities; do not run MB/Z/w/Holevo.
- [x] Prepare immutable-input regeneration recipe with exact old geometry/catalog and requested noise override; execution authorization stays false, target distinct, no runner invoked.
- [x] Run full suite, independent review, write concise Vietnamese report and new validation artifacts. Verify protected files and catalog remain unchanged except declared code extension; no paper-mode/figures/commit/push.

## Technical choices and limits

Beam sanity reports nominal diffraction-only radius, ideal centered circular capture and a diffraction-only manuscript erf approximation. No unprovided G_d or complete channel coupling is inferred. Nominal geometric capture is not SKR/transmittance including turbulence, jitter, AoA or atmosphere.

Observation window x_ref=x_local-v_x*t: [0,2000], [1500,3500], [5000,7000]m for the declared drift. The operating region stays physically fixed. Binary masks threshold exactly the sampled CLWC values.

Review focus: full/half-angle confusion; .0186 channel plus separate .005 detector mistaken for a single total; cloud candidate enabled before threshold approval; endpoint-only blockage; negative-time/shape or nonrigid advection in the reference-window transform; historical overwrite or old-protocol authorization copied into a new recipe.

## Execution record

Baseline112 passed in6.20s. Initial feature tests11 failed for missing configs/interfaces. Implementation11 passed; explicit realization/velocity guards were then reproduced RED and fixed. Full suite124 passed. Independent review found no major defect; its invalid-noise comparison diagnostic was reproduced in3 failing regression cases and fixed, and inherited approval wording was removed from the new recipe only. Final full suite127 passed in7.25s, exit0; machine-readable artifacts under `docs/phase5b_validation/`.

No new model or mission values were chosen. Implementation is inline; no commits or worktree changes, as explicitly requested. No runner, cloud realization, new lookup, paper run or figure generated.
