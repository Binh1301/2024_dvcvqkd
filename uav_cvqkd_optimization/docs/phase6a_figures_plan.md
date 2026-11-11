# Saved Phase6A Figures 4–7 — implementation plan

Spec: user task archived at `docs/phase6a_figures_validation/author_request.txt`.

Goal: IEEE-quality PDF/SVG/600dpi PNG graphics from sealed numerical diagnostic results, without changing scientific readiness or running optimization/sensitivity.

Design: new `src/uav_qkd/phase6a_figures.py` consumes saved results/config/scenario/trajectories/cloud coefficients and validates hashes and quantities. Reuse finite_key, STYLES, CloudField, BlockageModel slab intersection and Phase6A3D LOS sampling. Existing paper-readiness exporter/guards/catalog remain unchanged. New focused tests, per-figure provenance, plotted-data exports, report/captions/LaTeX and fresh independent review.

Decisions:
- Actual dt10s,K100,T1000s override pasted context dt1/K1000. Snapshots0/300/1000s; no invented999s or interpolated positions.
- Figures4/5/7 use P2 saved trajectories, explicitly identify objective. Check P1 paths identical in this dataset rather than merging objectives silently.
- Fig4 uses fixed UAV-coordinate LOS availability,50x50 visualization cell centers, same slab/threshold/20m3D sampler, no endpoint approximation. Validate snapshot mask at actual graph nodes against saved z for300/1000s; t0 is a deterministic reconstruction, not a saved simulation slot.
- Fig5 uses saved accumulated finite-size prefixes, validated with existing finite_key. Label as proxy, no linear synthetic ramp.
- Fig7 four unconnected points, actual energy/kJ and key/bits, no Pareto-frontier claim.
- Fig6 pending: only different synthetic-demo sweeps found. Provide renderer accepting JSON list of sealed result bundles from future matched-budget experiments; at least2 distinct budgets, full method/objective coverage, identical non-budget scientific inputs required. Export selectedK andduration per budget. No placeholder graph.
- Figures4/6 double-column7.16in;5/7 single-column3.5in. Reuse gray/blue/orange/green styles, additional distinct markers, white backgrounds, no embedded oversized titles. Diagnostic/paper-admissibility status stays in provenance/report/captions.

Tasks:
- [x] TDD: missing module RED;9focused cases now PASS. Prefix coordinate corruption and Fig4 text collision reproducedRED→GREEN.
- [x] Implement saved-data loader, four dedicated plotting functions, exports/manifests and CLI. No new dependencies/model copies.
- [x] Generate Fig4/5/7 inPDF/SVG/600dpiPNG;6BLOCKED with noimage. Inspect PNGs and fix collisions, objective labeling and tickdensity; cached masks reused for cosmetic rerenders.
- [x] Independent final review PASS; fullsuite215PASS72.14s,0failed/errors/skipped.1327original-file hashes unchanged; report/LaTeX/captions and verification receipt completed. No commit/push.

Review focus: no new optimization; data-derived time/energy units; snapshots are LOS availability for UAV coordinates; observational path segments do not certify continuous inter-slot clearance; forecast oracle vs myopic comparisons; energy budget nonbinding and finite-size proxy not security proof.
