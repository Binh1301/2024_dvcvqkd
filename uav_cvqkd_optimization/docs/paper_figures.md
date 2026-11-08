# Provenance-aware IEEE paper figures

Implementation: `src/uav_qkd/paper_figures.py`. Each catalog entry has a dedicated
plotting function. Existing physics, finite-key evaluation, lookup interpolation
and saved-result verification are reused; no optimizer or experiment runner is
called by the exporter. The historical renderer and its output files are unchanged.

## Current generation status

| Figure | Content | Status | Available exports |
|---|---|---|---|
| fig01_rotor_power | Source-verified rotor power and numerical convex envelope | READY, model illustration only | PDF, 600 dpi PNG, JSON, English caption |
| fig02_cloud_maps | Gaussian CLWC and exact threshold masks | BLOCKED | JSON and planned caption only |
| fig03_skr_lookup | Native spatial asymptotic SKR samples | BLOCKED | JSON and planned caption only |
| fig04_trajectory_P1 | Selected P1 trajectories | BLOCKED | JSON and planned caption only |
| fig05_trajectory_P2 | Selected P2 trajectories | BLOCKED | JSON and planned caption only |
| fig06_energy | Cumulative energy for both objectives | BLOCKED | JSON and planned caption only |
| fig07_finite_size | P2 signals, asymptotic contribution, penalty and estimated key | BLOCKED | JSON and planned caption only |
| fig08_key_comparison | P1 average rate and P2 total key | BLOCKED | JSON and planned caption only |
| fig09_runtime_memory | Recorded runtime, allocation peak and sampled RSS | BLOCKED | JSON and planned caption only |
| fig10_sensitivity | Recorded energy, threshold, graph-spacing and pruning sensitivity | BLOCKED | JSON and planned caption only |

Canonical outputs: `figures/paper/`. `status.json` collects the per-figure
manifests. READY for Figure 1 refers only to a formula-based rotor illustration
using the audited 2018 preprint parameter set. It does not make paper-mode ready
or certify a mission, continuous optimum, lower-envelope error bound or security.
The exact source version/URL accompanies the caption and JSON.

Figures 2–10 remain blocked because paper-mode is NOT_RUN, required configuration
fields are null, and the 2,601-point lookup remains INSUFFICIENT_EVIDENCE. No
placeholder PDFs/PNGs are created for blocked figures, and no demo data are
substituted. The manifests list reasons and the available/missing inputs.

## Commands

From the package directory, set `$env:PYTHONPATH='src'` when not installed.

```powershell
python -m uav_qkd.paper_figures --config configs/paper.yaml --output figures/paper --column double
```

This command returns a nonzero status when any figure is BLOCKED (the Python
entry point returns 2). The delivered directory already exists; the exporter
refuses to overwrite any nonempty directory. Use a new path for another export:

```powershell
python -m uav_qkd.paper_figures --config configs/paper.yaml --output figures/paper_single --column single
```

Single-column width is 3.5 inches, double-column width 7.16 inches. PNGs are
600 dpi; PDFs keep vector text, axes and line/bar plots. Sampled heatmaps are
raster layers in the vector PDF. Labels and captions are English. Algorithms
use gray/blue/orange/green respectively, distinct line styles and bar hatches.

## Saved-data and exploratory behavior

Use `--results <directory>` only for an actual saved experiment with the same
configuration. A full required-output seal, core producer/config bindings,
existing `verify_results` replay, finite-key arithmetic and recorded measurement
checks precede plotting. A numerical verification receipt does not override
source/readiness restrictions. The current authoritative audit must also admit
paper use before Figures 2–10 can be READY.

For deliberate software/demo inspection, both a matching demo configuration and
an explicit flag are required:

```powershell
python -m uav_qkd.paper_figures --config configs/demo.yaml --results results/final_demo_20261107 --exploratory --output figures/exploratory_demo
```

Those exports are EXPLORATORY in every image, caption and JSON; they are never
paper-ready. This task exercised that path only in temporary QA directories
using the existing saved demo, without generating new algorithm outputs or
timings. The QA contact sheets in `docs/paper_figures_validation/` are labeled
exploratory, not scientific paper deliverables.

Trajectories use equal meter scales and an explicitly captioned view of their
actual extent, so short paths remain visible. Coordinates are not shifted or
interpolated. Energy and key curves stop at the selected prefix; no method is
padded to another method's duration. SKR sample values are displayed natively;
there is no reoptimization, zero clipping, smoothing or inferred SKR from colors.
Runtime/memory charts read the recorded measurements and distinguish Python
allocation peak from sampled whole-process RSS. Missing measurements are errors,
not zeros. Infeasible methods are labeled without invented objective values.

Figure 10 defaults to the saved P2 sensitivity; `--sensitivity-objective P1`
selects P1. Its axes retain actual recorded parameter values and SI units;
an uncapped DP point is explicitly labeled `exact` within finite-graph scope.

## Verification

The original 42 tests pass together with 17 focused figure tests (59 total).
Checks include model values, native SKR scale, exact cloud masks, trajectory and
finite-key quantities, recorded runtime/memory, sensitivity arithmetic, empty
or incomplete hash manifests, missing audit files, 600 dpi/physical widths,
source captions, configuration mismatches and overwrite protection. Independent
review findings and regression-test resolution are recorded separately.

`paper.yaml` and historical result files are hash-checked against the protection
snapshot. The initial renderer export from this development turn is retained
under `paper_figures_validation/initial_export/` as superseded review evidence;
only `figures/paper/` is the current deliverable.
