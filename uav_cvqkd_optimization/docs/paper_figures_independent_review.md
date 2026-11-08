# Independent figure-export review

Reviewed `src/uav_qkd/paper_figures.py` and `tests/test_paper_figures.py` against
`docs/paper_figures_plan.md`, including their configuration, lookup, finite-key,
saved-result verification, and trajectory-evaluation dependencies. This review
assumes a local researcher exporting existing saved experiments.

What this change does: It provides ten plotting functions and a batch exporter
with per-figure provenance and captions. The default configuration correctly
exports only the rotor illustration and blocks the nine mission-result figures.

## Must fix

1. **Missing seals are accepted as verified recorded measurements**
   (`src/uav_qkd/paper_figures.py:136`, inherited verifier behavior at
   `src/uav_qkd/verify.py:16`).
   - What this is: The loader delegates file integrity checks to `verify_results`.
   - Problem: That verifier checks only entries present in each manifest; it
     does not require any entries. In a temporary directory, a changed
     `results.json` with `runtime_s=123456789.0`, the original input manifest,
     and `output_manifest.json={}` was accepted. The returned verification said
     `CURRENTLY_VERIFIED_PASS` with `output_hash_checks=0`. Thus figure 9 can
     present unsealed, changed timing as recorded experimental evidence.
   - Fix: Before calling the existing verifier, require a nonempty producer/input
     manifest and the saved-output seal entries used by each exported figure,
     at least `results.json` and `input_manifest.json`, plus `sensitivities.csv`
     when present. Add a regression test for an empty/incomplete seal.
   - If skipped: The new evidence-bound exporter accepts incomplete provenance.

2. **Missing audit inputs abort the batch before BLOCKED manifests exist**
   (`src/uav_qkd/paper_figures.py:110`, `:358`, `:377`).
   - What this is: Default generation reads readiness and rotor audit receipts.
   - Problem: These reads occur outside the guarded export/load blocks. Pointing
     `AUDIT` to an absent directory caused `FileNotFoundError` and left zero JSON
     manifests, contrary to the plan's missing-input BLOCKED behavior. An absent
     rotor receipt similarly aborts before figure 1's manifest is written.
   - Fix: Convert missing/malformed audit evidence into readiness reasons and
     write all ten BLOCKED manifests; keep the rotor's independent gate.
   - If skipped: An incomplete checkout cannot produce the promised reviewable
     status report.

## Should fix

3. **The trajectory exports hide the existing demo trajectories**
   (`src/uav_qkd/paper_figures.py:255`).
   - What this is: Both trajectory panels use the full configured 2000 m square.
   - Problem: The saved demo's moving P1 trajectories span only 20 m in x and
     zero in y. At the required 3.5-inch width, all moving lines are covered by
     the initial-position star. Visual inspection shows an apparently stationary
     mission rather than readable trajectories.
   - Fix: Add a clearly labeled inset of the data-derived trajectory bounds, or
     use documented data-derived zoom bounds with adequate padding. Keep
     coincident paths explicitly described as coincident.
   - If skipped: The figures cannot communicate the trajectories they contain.

4. **Standalone captions omit the promised source/version qualification**
   (`src/uav_qkd/paper_figures.py:33`, `:394`).
   - What this is: Captions are exported separately for use beside manuscript
     figures.
   - Problem: Figure 1 says that the source parameter version is retained, but
     never names the verified 2018 arXiv-v1 variant or distinguishes it from the
     IEEE 2019 parameter table. The qualification exists in configuration data,
     not in the caption. This misses the plan's explicit requirement that source
     version and numerical/data qualifications travel with each English caption.
   - Fix: State the actual source version in the rotor caption and append the
     saved data status and applicable method classification to result captions.
   - If skipped: A detached caption loses information needed to interpret the
     parameter set and result scope.

Verdict: Fix 1 and 2 before delivery; address 3 and 4 for the promised scientific
figure quality.

Validation: All 11 figure tests pass. Independently reproduced the empty-seal
and missing-audit cases using temporary directories. Inspected actual single-column
renders of figures 4, 7, and 10; no simulation, optimizer, or research evaluation
was launched. Existing saved data were read without modification.

Not checked: Complete 600 dpi/PDF visual inspection for every figure and width;
future admissible paper datasets are unavailable. Current NOT_RUN and
INSUFFICIENT_EVIDENCE gates remain effective for the default paper export.
