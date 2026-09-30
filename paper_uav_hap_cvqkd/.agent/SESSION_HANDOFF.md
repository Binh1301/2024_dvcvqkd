# Session Handoff

## Latest completed task

Date: 2026-09-30

EVID-0108 / DEC-0092 created the clean positive-SKR figure from the existing
extended table/report only.

- New assets: `skr_vs_distance_clean.{png,pdf}` and
  `skr_vs_distance_clean_report.json`.
- The figure contains only the two protocol curves, positive exact-tested
  markers, a standard log y-axis, a white background, clean labels, and a
  compact legend. It has no crossing annotations, arrows, footer, inset,
  zero-line, negative branch, or configuration text.
- 8 Uniform and 63 MB positive rows were plotted. No evaluation, source
  moment, candidate, new distance, or interpolation occurred.

This remains presentation-only and the lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Prior positive-only redraw

Date: 2026-09-30

EVID-0107 / DEC-0091 created the positive-SKR-only logarithmic redraw from
the existing extended exact table/report.

- New assets: `skr_vs_distance_positive_only.{png,pdf}` and
  `skr_vs_distance_positive_only_report.json`.
- Only `SKR > 0` rows are plotted: 8 Uniform and 63 MB; no negative row or
  zero line is shown.
- The first-negative distances 26 km and 810 km remain short annotations;
  no crossing is interpolated. No channel/security rerun, source moment, or
  candidate was created.

This remains diagnostic-only and the lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Prior symlog redraw

Date: 2026-09-30

EVID-0106 / DEC-0090 created the clean symlog redraw from the existing
extended exact table/report only.

- New assets: `skr_vs_distance_redraw_symlog.{png,pdf}` and
  `skr_vs_distance_redraw_symlog_report.json`.
- The figure uses the exact requested title/subtitle, `symlog` with
  `linthresh=1e-11`, exact-tested markers/line connections, a zero line, short
  25/26-km and 800/810-km annotations, and a 790--820-km `MB sign bracket`
  inset.
- The renderer validated 83 distances / 166 rows from the existing table and
  report. No channel/security rerun, source moment, candidate, or
  interpolation occurred; the original extended assets were preserved.

This remains diagnostic-only and the lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Extended exact-grid diagnostic

Date: 2026-09-30

EVID-0105 / DEC-0089 extended the common-feasible exact diagnostic and
redrew the figure through 1000 km.

- The same 5 feasible Uniform and 5 feasible MB exact/hash rows were used;
  baseline, budget, peak guard, AO, phase noise, beta, and security path were
  unchanged.
- 83 distances / 166 envelope rows were evaluated with channel recomputation
  at every distance; no source moments or candidate generation occurred.
- Uniform: last exact-positive 25 km, first exact-negative 26 km.
- MB: last exact-positive 800 km, first exact-negative 810 km; the values are
  O(1e-11) bits/use and are low-rate diagnostic observations.
- New assets: `skr_vs_distance_redraw_extended.{png,pdf}`,
  `skr_distance_table_extended.csv`, and the redraw report under
  `results/revised_hap_uav_optical_baseline_figure/`.
- The redraw uses exact-point line connections plus an inset for the
  750--1000-km MB sign bracket; no interpolation is claimed.

This remains diagnostic-only and the lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Prior exact-point redraw

EVID-0104 / DEC-0088 created the requested exact-point line redraw from the
existing common-feasible diagnostic artifacts.

- New outputs: `results/revised_hap_uav_optical_baseline_figure/`
  `skr_vs_distance_redraw.png`, `skr_vs_distance_redraw.pdf`, and
  `skr_vs_distance_redraw_report.json`.
- Only the existing 26 Uniform/MB rows were used; no Binomial data, new
  points, source moments, C,w interpolation, or channel/security rerun.
- Lines connect existing exact-tested points in distance order; circular
  markers and the `SKR = 0` line are shown.
- Endpoint annotations mark Uniform 25 km positive / 26 km negative and MB
  positive through 30 km.
- Renderer validation cross-checked `skr_distance_table.csv` against the
  diagnostic envelope and `protocol_summary.csv`.

This remains a visualization-only diagnostic asset. The
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` lifecycle state and prior conclusions
are unchanged.

## Prior named figure export

EVID-0103 / DEC-0087 exported the requested named diagnostic-only figures
and table from the verified EVID-0102 common-feasible exact envelope.

- Main outputs: `results/revised_hap_uav_optical_baseline_figure/`
  `skr_vs_distance.png`, `skr_vs_distance.pdf`, and
  `skr_distance_table.csv`.
- Optional outputs: `betaIAB_vs_distance.{png,pdf}` and
  `chiBE_vs_distance.{png,pdf}`.
- The renderer rechecked exact/hash status, `V_A <= 1.5`, peak feasibility,
  required distances, and the no-new-moments/no-interpolation provenance.
- No channel/security evaluation was rerun; the source run had already
  recomputed the channel at every exact-tested distance.
- Binomial remains omitted with the explicit no-safe-exact-dataset note.

This is an asset export only. The common-feasible exact-grid conclusions and
the `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` lifecycle state are unchanged.

## Prior completed diagnostic

EVID-0102 / DEC-0086 completed the requested fair common-feasible diagnostic.

- Fixture: `w0=0.10 m`, `D_r=0.55 m`, `tau_zen=0.92`,
  `epsilon_ch=0.0186 SNU`, `beta=0.95`, AO OFF, heterodyne, reverse
  reconciliation.
- Common budget: `0 < V_A <= 1.5 SNU` for both protocols.
- Exact rows retained: 5 Uniform and 5 MB; peak constraint
  `n_peak_photons=30.0` passed for every retained row.
- The prior MB row `V_A=3.5548673905` and every other over-budget row were
  excluded; no source moments or C,w interpolation was used.
- Distances: `19,20,21,21.9393102292,22,23,24,25,26,27,28,29,30 km`.
- Channel quantities were recomputed at every distance; plots use markers only.
- MB exceeds Uniform at every exact-tested distance.
- Uniform: last exact positive at 25 km (`SKR=5.9111913793e-4`), first exact
  negative at 26 km (`SKR=-2.9334046616e-4`).
- MB: positive through the largest exact-tested distance, 30 km
  (`SKR=7.8782598116e-3`), with `nu=0.2`, `V_A=1.3833230303`.
- SKR gains: `0.0442303289` bits/use at 22 km and `0.0238529688` bits/use at
  25 km.
- Primary driver: larger `beta I_AB`; lower `chi_BE` helps at 22 km but MB
  has higher `chi_BE` at 25 km.

## Exact-cache boundary

The result is the best exact-tested feasible candidate envelope only. It is
not a continuous or global optimization, not a common exact-VA grid, and not
a publication comparison. Binomial remains excluded because no safe current-
compatible exact C,w dataset exists.

## Artifacts

All artifacts are under `results/revised_uniform_mb_common_feasible_diagnostic/`:

- `revised_uniform_mb_common_feasible_report.json`
- `diagnostic_candidate_details.csv`
- `diagnostic_distance_envelope.csv`
- `protocol_summary.csv`
- `security_term_attribution.csv`
- `availability.csv`
- `excluded_candidates.csv`
- `channel_by_distance.csv`
- `diagnostic_skr_vs_distance.{png,pdf}`
- `diagnostic_beta_iab_vs_distance.{png,pdf}`
- `diagnostic_chi_be_vs_distance.{png,pdf}`

## Verification and blockers

- Runner exit code 0; `py_compile`, JSON/CSV inspection, and visual inspection
  of all three marker-only plots passed.
- `FINAL_MODEL_SPEC.md` remains unmodified and hash-mismatched against the
  historical expected value.
- Remaining blockers include unresolved `tau_zen` and `cn_phi2` authorization,
  sparse exact C,w coverage, unauthorized optimized-MB search, missing
  Binomial exact C,w, and no common exact-VA grid.

## Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Next action

Resolve the frozen-spec and authorization blockers before any broader or
publication-scale comparison. Preserve the existing exact cache and all
unrelated worktree edits.
