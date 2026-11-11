# Phase 6A figure independent review

Scope: new `src/uav_qkd/phase6a_figures.py`, `tests/test_phase6a_figures.py`, the archived author request/plan, the sealed Phase6A source bundle, and generated `results/paper_figures/phase6a/` artifacts. Read-only code/artifact review; this review document is the only file written by the reviewer. No optimization, cloud generation, sensitivity, native quantum evaluation, training, or publication evaluation was run.

## Strengths and verified evidence

- The loader verifies exact source seal coverage/hashes, historical inputs, and executed producer hashes; the executed RSS-retry runner resolves to its exact archived source rather than the subsequently fixed telemetry code.
- All eight selected P1/P2 solutions and 800 saved prefixes validate against saved graph positions, edge energies, LOS values, clear-sky rates, and the existing single accumulated-block finite-size proxy. P1/P2 paths are identical in this particular source dataset.
- Source time is 10 s/slot, 100 selected slots, 1000 s duration. Unsupported 999 s snapshots are rejected. The actual 0/300/1000 s boundaries are used. Final average rates equal saved total key divided by actual 1000 s duration.
- LOS reconstruction reuses the exact existing slab intersection and full-3D <=20 m sampler with saved Gaussian coefficients, threshold, drift, clipping, and geometry. The focused test verifies the 300/1000 s reconstructed masks at all 121 saved graph nodes against the corresponding source arrays. This is not an endpoint-cell blockage approximation.
- Figure 5 uses saved accumulated prefix keys, including the zero-key interval and nonlinearity, rather than a terminal-rate ramp. Figure 7 is four unconnected points, converts J to kJ, and reports 77/81/81/100 percent clear fractions.
- Figure 6 remains blocked. Existing demonstration sensitivity CSVs are identified and excluded; no image exists. Future input requires distinct budgets, matched non-budget configuration/scientific arrays, sealed complete four-method P1/P2 bundles, and exports selected K and duration.
- Per-figure manifests retain diagnostic/non-admissible status and material limitations. Captions do not claim composable security, causal online superiority, a continuous global optimum, or a Pareto frontier.
- Focused verification command: `PYTHONPATH=src python -X utf8 -m pytest -q tests/test_phase6a_figures.py`: **8 passed in 1.45 s**.
- Independent artifact check: all 23 output-manifest entries match their hashes and exact directory coverage. PDF/SVG signatures are valid. PNGs have dimensions 4296x1950 (Figure 4) and 2100x1650 (Figures 5/7), and recorded DPI 599.9988. Figures 4/5/7 PNGs were visually inspected.

## Issues found in the first exports

Critical: none found.

Important: Figure 4's explanatory sentence at `phase6a_figures.py:174` intersects the x-axis tick labels in the exported image. This fails the requested publication-layout quality. Remove the redundant in-image sentence or place it below the axis labels with adequate space.

Minor: Figure 5's lower-right P2 annotation (`phase6a_figures.py:187`) crosses the rising greedy curves. Move it into unused space. Figure 7's 170.5/171.0 kJ tick labels are too close at single-column size; use fewer explicit x ticks. Figure 4's terminal marker on x=0 is partially clipped; `clip_on=False` for endpoint markers can improve readability without changing coordinates.

These findings were communicated to the implementer before final delivery. Final cosmetic exports require a follow-up visual check; scientific quantities need no rerun.

## Declined to judge

- Statistical robustness, uncertain forecasts, physical cloud realism, full security, and continuous-path clearance: no new experiment or scientific-readiness promotion is authorized by this plotting task.
- Full suite results and preservation inventory for every pre-existing repository file: the coordinating agent owns these final verification receipts; this reviewer ran focused tests and independently checked the sealed source/output bundles.
- Figure 6 scientific results or outcomes: no matched energy-budget sweep exists; future software fixtures are not admitted experimental evidence.

## Assessment

**Initial verdict: with layout fixes.** Scientific/provenance handling is consistent with the saved diagnostic evidence. The important Figure 4 label collision must be resolved and final exports visually checked before calling the plotting task complete. Figure quality does not change the project's scientific lifecycle or paper-readiness status.

## Final resolution and follow-up verification

The coordinator re-exported graphics from the saved LOS map cache; no cloud realization or optimization was repeated. A fresh visual inspection of all three final PNGs confirms that the Figure 4 explanatory sentence is removed, the Figure 5 objective annotation is a legend title clear of the curves, and Figure 7 uses three separated x ticks. Endpoint markers use `clip_on=False`. The first-export issues above are resolved.

The final Figure 4 caption explicitly distinguishes the instantaneous blocked mask from historical path segments: a historical segment crossing a region shaded at the later snapshot does not imply that it was blocked at traversal time. It also preserves the continuous inter-slot clearance limitation.

The final 23-entry output manifest again passes exact coverage and hash checks; generated per-figure producer hashes match the current plotting source, and all exported image hashes match. The coordinator added physical figure sizes, software versions, and rendering dependency hashes to provenance. The focused suite now reports **9 passed in 1.67 s**, including the renderer bounding-box regression for the label collision.

**Final verdict: PASS for the authorized saved-data plotting task, subject to the coordinator's full-suite/preservation receipt. No unresolved Critical or Important finding.** Figure 6 correctly remains pending matched experimental data; publication/security readiness remains unchanged. No scientific model, algorithm, configuration, or sealed result modification is requested by this review.
