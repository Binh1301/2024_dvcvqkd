# Plot task - saved-artifact-only manuscript mobility export

Own ONLY scripts/plot_manuscript_mobility.py and tests/test_manuscript_mobility_plots.py.
You are not alone; preserve others' edits. No old file edits, no full real export
yet (root runs it after data ready), no source/channel/MI/SKR calculation, no
commits. Use stdlib unittest, project .venv Python -X utf8 -B. Test-first with
small temporary synthetic plotting fixtures; record test results. No new deps.

API: export_results(output:Path,settings:dict)->None. CLI --output optional if
useful; root imports API. All output under output/figures, no old files.
Every scientific plot must have vectorPDF (pcolormesh, not imshow/rasterized)
and PNG350dpi; readable IEEE-like style, white/light major-minor grids.

Inputs finalized by root runner:
- positions.csv: position_index,j,x_m,y_m,z_m,distance_km,zenith_deg,geometry_id...
- p1/winners.csv100 rows: geometry/position fields plus family,nu_raw,VA,K_raw,
  K_star,I_AB_2D,chi_BE, etc. p1/family_winners.csv200 analogous MB and Uniform.
- clouds/states.npz: blocked bool[100,100,30], usable_skr float same shape.
- mobility/lambda_schedule.json keys lambda_hi,d_min_m,K_max,multipliers,values,
  representative. Representative mission0. lambda may0 degenerate.
- mobility/representative_paths.csv: strategy Stationary/Greedy/DP,slot1..30,
  position_index,x_m,y_m,blocked,usable_skr,leg_distance_m,cumulative_normalized_skr,
  realization_id,lambda_index,lambda_bits_per_use,lambda_multiplier,nu_raw,VA,
  ensemble_hash,clear_raw_skr.
- mobility/representative_metrics.csv3 rows with strategy,average_skr_bits_per_use,
  total_distance_m,objective_bits_per_use,positive_slots, etc.
- mobility/lambda_statistics.csv: lambda_index,lambda_bits_per_use,strategy,
  metric (average_skr_bits_per_use,total_distance_m,objective_bits_per_use,...),
  mean,sd,se,ci95_low,ci95_high,realizations,uncertainty_scope.
- figures/figure1_distance.csv31 rows: distance_km,zenith_deg,Uniform_optimal_VA,
  Uniform_K_raw,Fixed_MB_K_raw,MB_optimal_nu_raw,MB_optimal_VA,Optimized_MB_K_raw.

Required files:
1 fig1_skr_distance.png/pdf, title SKR versus HAP–UAV Link Distance; x Link
  Distance (km), y Secret Key Rate (bits/use). Blue optimized Uniform,
  orange fixed MB, red optimized MB. semilog positive only; NaN gaps, no eps.
  Add fig1_skr_distance_linear.png/pdf preserving negatives and zero.
2 fig2_cloud_trajectories.png/pdf: 1x1km area, pcolormesh cloud-free fraction for
  representative mission0, all candidate points, stationary star, Greedy and DP
  actual ordered feasible paths, start/end markers. Strategy colors consistent
  with Figure3: stationary black, Greedy orange, DP red (or dark blue if clarity
  requires; pick once). Off-grid HAP need not be shown at11km; caption/report
  specifies geometry. Prevent legends hiding paths; long repeats can overlap,
  do not invent displacement for visibility.
3 fig3_mobility_tradeoff.png/pdf: two panels mean average SKR and mean distance
  versus actual lambda bits/use, Stationary/Greedy/DP with95% CI. shared lambda
  axes symlog at min positive lambda, zero shown, note scale in figure caption
  metadata. Degenerate lambda0 only: annotated single data, no invented sweep.
4 p1_skr_heatmap.png/pdf (Kstar), p1_VA_heatmap.png/pdf, p1_nu_heatmap.png/pdf.
5 cloud_slot_01/10/20/30.png/pdf for representative mission0.
6 figures/plot_data/* CSV enough to trace plotted values; copy original inputs
  or derive display-only arrays. figures/render_receipt.json with renderer SHA,
  input file SHAs, no scientific recalculation, exact nonpositive exclusion
  counts, figure paths, symlog threshold. Do not write visual_review.json: root
  inspects actual PNGs and records it later.

Reference relative sizes single plot3.5–7.16in depending readability; two-panel
double-column7.16in. Use installed Matplotlib, no seaborn, no raster images in
PDF. Ensure legend headroom (old zenith export initially hid maxima; fixed).
Test controls must verify raw negatives unchanged, log excludes nonpositive,
all outputs exist/vector/dpi, and input files unmodified. Root verification
rejects '/Subtype /Image' PDF content. Avoid heavy scientific module imports.
