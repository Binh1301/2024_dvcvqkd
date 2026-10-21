# Backend task: exact manuscript mobility adapter and Greedy

Own ONLY src/manuscript_mobility.py and tests/test_manuscript_mobility.py.
You are not alone; preserve others' edits. Do not edit historical files/config,
ledgers/results. No simulations, AP/source generation, commit/push. Root runs
the full experiment. Use .venv/Scripts/python.exe -X utf8 -B from project root.
Write and run meaningful failing tests first, then implement and pass them.

Read AGENTS and configs/manuscript_mobility.json. Preserve existing scientific
helpers. Safely import only channel_at_angle from
results/skr_vs_zenith_angle_20261019/run_sweep.py (importlib spec is acceptable),
security/M/converted from scripts/recheck_manuscript_homodyne_noise.py and
uniform_mi_2d from scripts/optimize_uniform_manuscript_2d.py. Do not call old
orchestration/check/evaluate/load_roster functions that write old results.

Required API (root runner will depend on exactly these names/keys):

- ROOT: project Path. sha(path)->full SHA256; read_csv(path)->list[dict].
- validate_config(settings)->positions ndarray(100,2). Strict approved physical,
  security/numerical/geometry/mission/cloud/optimization settings; reject model
  changes rather than silently ignoring config. Compare optical fields with
  reference protocol; prevent inherited .55m/10urad/heterodyne evaluator use.
- load_catalog(settings)->list[dict], sorted (family,nu_raw,VA,ensemble_hash).
  Combine MB197 rows from old roster (filter family MB) plus Uniform36 recent
  all_candidates; verify configured roster digest/counts, full payload digest,
  exact_cache_provenance.verify_source_payload/settings, nu/VA hex, Cw, full256,
  source reconstruction/PMF/product/energy and ensemble_hash. No duplicates.
  Candidate keys: family,nu_raw,VA,C,w,ensemble_hash,source_path,source_sha256,
  cache_key,canonical_cache_key,source_moment_route,support_size,nu_raw_hex,VA_hex,
  p (numpy probabilities), alpha (numpy complex amplitudes).
- geometry_table(settings)->(position_rows,geometry_rows). position row keys:
  position_index,j,x_m,y_m,z_m,distance_km,zenith_deg,zenith_hex,
  horizontal_squared_hex,geometry_id. Call existing candidate_grid/link_geometry.
  Geometry IDs g000,g001,... in first-occurrence order. Group ONLY exact
  horizontal_squared_hex AND distance/angle values under fixed config.
  geometry_rows are representative position rows (one per ID); expect60.
- channel_at_angle(degrees): reexport pure historical helper unchanged.
- evaluate_source(candidate,ch)->(row,model). MP model via unchanged security,
  GH16/32/64 via unchanged 2D tensor helper; no formula changes/clipping. Row:
  family,nu_raw,VA,C,w,I_AB_2D,beta_I_AB,chi_BE,K_raw,eta_f,xi_f,N,V,W,Z,
  nu_1,nu_2,nu_3,MI_GH16,MI_GH32,MI_GH64,GH_max_difference,
  uncertainty_min_eigenvalue,matrix_spectrum_max_difference,ensemble_hash,
  source_sha256. model is original MP security dict. Fail if any invalid data,
  covariance, spectrum, entropy bound or GH delta>2e-13. MP digits80 set by root.
- select_winner(rows)->row: min key(-K_raw,nu_raw,VA,ensemble_hash), reject empty
  and invalid values; never clip candidates before selection.
- lambda_schedule(Kstar,positions,reference_distance_m)->dict with lambda_hi,
  d_min_m,K_max,multipliers,values,representative. hi=2*Kmax*Dref/dmin; multipliers
  exactly approved list. Degenerate Kmax0 -> values[0],representative0,hi0.
- greedy_step(rates_now,previous_index,distances,feasible,*,slots,
  penalty_bits_per_use,reference_distance_m)->int. previous None: argmax rate.
  Otherwise maximize rate-Nt*lambda*distance/Dref among feasible neighbors.
  Exact ties smallest index. Validate finite nonnegative rates, graph/speed,
  nonnegative penalty and positive scalar dimensions. Only current slot enters.
- greedy_trajectory(S,positions,*,slot_duration_s,max_speed_m_per_s,
  penalty_bits_per_use,reference_distance_m)->dict with same keys as existing
  uav_mobility.optimize_trajectory, calculated directly from the path.
- compare_paths(S,blocked,positions,*,slot_duration_s,max_speed_m_per_s,
  penalty_bits_per_use,reference_distance_m)->(summaries,paths,series).
  Reuse best_stationary and optimize_trajectory (F/Nt normalization unchanged).
  paths dict keys Stationary,Greedy,DP -> index vectors. summaries three rows:
  strategy,average_skr_bits_per_use,total_distance_m,objective_bits_per_use,
  clear_slots,blocked_slots,positive_slots,availability,repositionings,
  initial_position_index,final_position_index,max_transition_m.
  series rows strategy,slot (1-based),position_index,x_m,y_m,blocked,usable_skr,
  leg_distance_m,cumulative_normalized_skr (cumsum(rate)/Nt).
  Require S>=0, boolean C matching S, blocked S exactly0; validate all transitions
  and U_DP>=U_Greedy,U_Stationary with abs/rel1e-12. Availability strictly S>0.

Tests: raw negative/tie P1; wrong config/hash/VA/Cw; exact geometry60 and no
approximate grouping; one frozen reference source evaluation; N dependsVA;
Greedy scaling/casual prefix/non-future access/feasibility; DP vs literal F
recursion and exhaustive 3x4, N1,v0,lambda0/high; no/all cloud; degenerate
rates; same common objective and undefined zero-reference percentage handled
by root. Do not run old full scientific tests or generate new source moments.
Report test commands/results and any assumptions. No new dependencies.
