# IEEE 2019 reference rotor and Figure 02 plan

1. Inspect the actual local journal PDF (17 pages), DOI, Eq.(12), Section V,
   raster Table I and Eq.(64). Keep rendered/extracted source evidence.
2. Add separate raw-parameter profiles under configs/rotor/: ieee_2019 and
   arxiv_2018_v1. Do not modify paper.yaml, demo.yaml or historical producers.
   Derive P0/Pi/hover and geometric v0 from the raw values. IEEE profile uses
   derived v0 explicitly, recording the rounded table value4.03 alongside it;
   the legacy arXiv profile keeps its original table-v0 policy7.2.
3. Reuse propulsion_power for total power. Provide stable component diagnostics
   separately, without altering the old energy/DP/security call graph.
4. Find ME and MR speeds by bounded local refinements of all grid-detected
   minima, including appropriate endpoints; verify objectives against an
   independent dense-grid sweep. Record numerical evidence, not guessed speeds.
5. Render a single-column IEEE figure with four distinguishable curves, hover,
   ME/MR markers; save vector PDF,600dpi PNG, computed CSV, English caption and
   provenance JSON under figures/ieee_2019/. This is the newly requested rotor
   Figure02, not a replacement for the blocked fig02_cloud_maps catalog entry.
6. Add tests before implementation; run all existing tests, visually inspect
   exports, update provenance and write a Vietnamese implementation report.

Scope excludes paper-mode mission, CV-QKD/cloud/finite-size values, Emax,
source/security readiness promotion, historical-result edits, commits or pushes.
