# Parameter provenance

Source labels distinguish direct quotations of numerical settings, mathematical derivation, repository overrides, illustrative settings and unresolved inputs. Runtime YAML does not infer missing values from metadata.

| Parameter | Value | Unit | Source | Exact locator | Classification | Current suitability |
|---|---|---|---|---|---|---|
| W | 100 | N | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| rho | 1.225 | kg/m^3 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| R | 0.5 | m | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| A | 0.79 | m^2 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| Omega | 400 | rad/s | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| U_tip | 200 | m/s | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| blade_count | 4 | 1 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| blade_chord | 0.0196 | m | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| s | 0.05 | 1 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| flat_plate_area | 0.0118 | m^2 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| d0 | 0.3 | 1 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| induced_power_correction_k | 0.1 | 1 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| profile_drag_delta | 0.012 | 1 | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| v0_table | 7.2 | m/s | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Table I | direct | Adopt requested preprint parameter set; do not attribute to IEEE 2019 table |
| P0 | 580.6500000000001 | W | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Eq.(61); v0 definition in Table I | derived | P0/Pi adopted; use table v0=7.2, not unannounced recomputation |
| Pi | 790.6715228132718 | W | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Eq.(61); v0 definition in Table I | derived | P0/Pi adopted; use table v0=7.2, not unannounced recomputation |
| P_hover | 1371.3215228132717 | W | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Eq.(61); v0 definition in Table I | derived | P0/Pi adopted; use table v0=7.2, not unannounced recomputation |
| v0_derived | 7.187922934666108 | m/s | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.27, Eq.(61); v0 definition in Table I | derived | P0/Pi adopted; use table v0=7.2, not unannounced recomputation |
| v_max | 60 | m/s | A-preprint: https://arxiv.org/pdf/1804.02238v1 | PDF p.22, Section V | direct | Adopt preprint setting, not IEEE 2019 vmax=30 |
| HAP_altitude | 20000 | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| UAV_altitude | 1000 | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| optical_wavelength | 1.55e-06 | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| tau_zen | 0.92 | 1 | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| reconciliation_beta | 0.95 | 1 | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| F0 | "infinity" | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| ground_Cn2 | 1e-14 | m^(-2/3) | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| rms_wind | 21 | m/s | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| FOV_half_angle | 0.00625 | rad | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| AoA_sigma | 0.0015 | rad | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV | direct | Geometry altitude adopted; optical values are lookup context only |
| receiver_aperture_diameter_printed | 0.08 | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV; full-angle definition p.2 Section II-B | direct | Historical value; not mixed into receiver30 lookup |
| receiver_aperture_diameter_receiver30 | 0.3 | m | execution_physical_protocol.json | results/skr_zenith_heatmap_20261106, physical block | repository_setting | Verified producer override; not a quotation from B |
| beam_divergence_full_angle_printed | 0.000233 | rad | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV; full-angle definition p.2 Section II-B | direct | Historical value; not mixed into receiver30 lookup |
| beam_divergence_full_angle_receiver30 | 3.5e-05 | rad | execution_physical_protocol.json | results/skr_zenith_heatmap_20261106, physical block | repository_setting | Verified producer override; not a quotation from B |
| pointing_jitter_per_axis_printed | 1.561e-05 | rad | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV; full-angle definition p.2 Section II-B | direct | Historical value; not mixed into receiver30 lookup |
| pointing_jitter_per_axis_receiver30 | 1.561e-06 | rad | execution_physical_protocol.json | results/skr_zenith_heatmap_20261106, physical block | repository_setting | Verified producer override; not a quotation from B |
| UAV_position_jitter_per_axis_printed | 1.0 | m | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.3, Section IV; full-angle definition p.2 Section II-B | direct | Historical value; not mixed into receiver30 lookup |
| UAV_position_jitter_per_axis_receiver30 | 0.1 | m | execution_physical_protocol.json | results/skr_zenith_heatmap_20261106, physical block | repository_setting | Verified producer override; not a quotation from B |
| channel_excess_noise | 0.0186 | SNU | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| detector_excess_noise | 0.005 | SNU | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| measurement | "homodyne_1D_Gaussian_effective" | model | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| VA_catalog_domain | [0.05, 10.0] | SNU | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| nu_raw_catalog_domain | [0.0, 0.4] | 1 | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| VA_source_normalization | "VA=Vmod=2*nbar" | convention | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| nu_mapping | "nu_repo=42.5*nu_raw" | convention | execution_physical_protocol.json | physical/protocol/source_domain fields | repository_setting | Lookup context; finite catalog, not global optimization or security certification |
| Vmod_printed | "nbar/2" | convention | B-bound: paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf | PDF p.2, after Eq.(3) | direct | Conflicts with producer normalization; retain explicit author convention, no silent correction |
| area | [2000, 2000] | m | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | p.1 Section I-A | direct | Adopt |
| dt | 1 | s | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | p.1 Section I-A | direct | Adopt |
| cloud_velocity | [-5, 0] | m/s | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | p.1 Section I-A and p.2 Fig.3 | direct | Adopt |
| cloud_display_grid | [50, 50] | cells | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | p.1 Section I-D, p.2 Fig.3 | direct | Adopt |
| cloud_cell_size | [40, 40] | m | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | 2000/50; p.2 Fig.3 | derived | Cloud discretization only, not a UAV step constraint |
| finite_key | "max(0,S-7*sqrt(n*log2(2/epsilon)))" | bits | Current trajectory manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf | p.2 Eq.(8), p.3 Eq.(28)-(30) | direct | Accumulated performance approximation; not composable security |
| pulse_rate_fs | UNRESOLVED | Hz | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| eta_valid | UNRESOLVED | 1 | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| m0 | UNRESOLVED | signals/clear slot | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| security_epsilon | UNRESOLVED | 1 | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| E_max | UNRESOLVED | J | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| initial_UAV_position | UNRESOLVED | m | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| HAP_horizontal_position | UNRESOLVED | m | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| cloud_layer_altitude | UNRESOLVED | m | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| cloud_layer_thickness | UNRESOLVED | m | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| paper_CLWC_threshold | UNRESOLVED | mg/m^3 | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| detector_efficiency | UNRESOLVED | 1 | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| electronic_noise | UNRESOLVED | SNU | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| waypoint_graph | UNRESOLVED | m | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| prediction_horizon | UNRESOLVED | slots | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| prior_lambda | UNRESOLVED | bits/J | Not specified by the selected sources | Current manuscript and source audit | unresolved | Required before real experiment; no demo fallback |
| figure_cloud_components | 400 | kernels | dynamic_gaussian_cloud_figure/create_figure.py + cloud_field_data.npz | generation constants and saved component arrays | illustrative_setting | Known source-code scenario; not calibrated atmospheric data or opacity threshold |
| figure_seed | 42 | 1 | dynamic_gaussian_cloud_figure/create_figure.py + cloud_field_data.npz | generation constants and saved component arrays | illustrative_setting | Known source-code scenario; not calibrated atmospheric data or opacity threshold |
| figure_threshold | 8.0 | mg/m^3 | dynamic_gaussian_cloud_figure/create_figure.py + cloud_field_data.npz | generation constants and saved component arrays | illustrative_setting | Known source-code scenario; not calibrated atmospheric data or opacity threshold |
| figure_CLWC_clip | 15.0 | mg/m^3 | dynamic_gaussian_cloud_figure/create_figure.py + cloud_field_data.npz | generation constants and saved component arrays | illustrative_setting | Known source-code scenario; not calibrated atmospheric data or opacity threshold |
| figure_global_shape | [50, 400] | cells | dynamic_gaussian_cloud_figure/create_figure.py + cloud_field_data.npz | generation constants and saved component arrays | illustrative_setting | Known source-code scenario; not calibrated atmospheric data or opacity threshold |

## Version decision

The requested 100 N / 580.65 W set is independently verified in the authors' 2018 arXiv v1, Table I p.27, Eq.(6) p.6, Eq.(61) p.27 and Section V p.22. It is NOT the numerical parameter set in the local 2019 IEEE journal PDF: that file has W=20 N, R=.4 m, A=.503 m^2, U_tip=120 m/s, v0=4.03 m/s, d0=.6 (Table I, PDF p.14 / journal p.2342), and vmax=30 m/s (PDF p.11 / journal p.2339). The physical formula is equivalent, but the numerical sets and equation numbers differ. The configuration follows the explicitly requested preprint set and labels it as such.

Paper B for the optical lookup is the hash-bound available_v43.pdf, SHA256 f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b. Current Copy (17) is the separate four-page trajectory formulation, created 2026-11-06 17:40:53 UTC. Later timestamps alone do not replace the producer-bound source. Manuscript (3).pdf is the MADRL/optical-IRS paper and is not a CV-QKD parameter source.

The 2018 preprint was read through the web tool. Direct shell PDF download was BLOCKED_BY_ENVIRONMENT (WinError 10013); no local preprint byte hash is claimed. The arXiv version, primary URL, exact page/equation locators and transcribed values are retained. Local source PDFs and repository inputs are SHA256-bound in the audit evidence.

No fs, eta_valid or numerical epsilon is supplied by the selected QKD sources. m0 cannot be computed; eta_valid=1 has NOT been adopted. No E_max, hover-reference duration, cloud altitude/thickness or prior lambda is invented. The figure threshold 8 is illustrative, not a universal physical threshold.

The existing 51x51 SKR lookup is a numerically evaluated finite-catalog table with source/security limitations; it is not promoted to source-certified R_asy_star over a continuous modulation domain. See skr_lookup_audit.json in the audit result directory.

## Numerical and display settings

| Parameter | Value | Unit | Provenance |
|---|---|---|---|
| seed | 42 | 1 | existing paper.yaml template; numerical_setting |
| velocity_samples | 2001 | speed nodes | existing paper.yaml; refinement validation script; numerical_setting |
| energy_tolerance_j | 0.001 | J | existing paper.yaml; sampled edge/refinement tolerance; numerical_setting |
| DP_mode | exact | algorithm | current manuscript p.4; uncapped exact graph mode; algorithm_setting |
| DP_label_cap | None | labels/state | exact mode; no cap active; algorithm_setting |
| plot_times | [0, 300, 1000] | s | current manuscript p.2 Fig.3; direct |

The preprint calls the induced-power increment k=0.1; its kappa denotes a different thrust/weight ratio. The YAML metadata names the increment explicitly to avoid conflating those symbols. A=0.79 is a rounded table value, not exactly pi*(0.5)^2. No communication power or RF altitude/bandwidth is imported.

## IEEE 2019 reference aircraft supplement

This supplement adds a separate `ieee_2019` rotor profile and does not replace the arXiv-v1 values or the partial default `paper.yaml`. The local 17-page journal PDF was directly inspected (including its raster Table I). DOI: [10.1109/TWC.2019.2902559](https://doi.org/10.1109/TWC.2019.2902559). The existing source/profile evidence is in `ieee_2019_rotor_verification/source_identity.json`; the raw profile bytes and PDF bytes are bound before a figure can be labeled READY.

| Parameter | Value | Unit | Exact source | Classification | Version / verification |
|---|---|---|---|---|---|
| weight_N | 20.0 | N | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| air_density_kg_m3 | 1.225 | kg/m^3 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| rotor_radius_m | 0.4 | m | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| rotor_disc_area_m2 | 0.503 | m^2 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| rotor_angular_speed_rad_s | 300.0 | rad/s | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| rotor_tip_speed_m_s | 120.0 | m/s | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| blade_count | 4 | 1 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| blade_chord_m | 0.0157 | m | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| rotor_solidity | 0.05 | 1 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| fuselage_equivalent_flat_plate_area_m2 | 0.0151 | m^2 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| fuselage_drag_ratio | 0.6 | 1 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| induced_power_correction_factor | 0.1 | 1 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| blade_profile_drag_coefficient | 0.012 | 1 | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| mean_induced_velocity_hover_m_s | 4.03 | m/s | journal p.2342 / PDF p.14 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| maximum_speed_m_s | 30.0 | m/s | Section V, journal p.2339 / PDF p.11 | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| P0_W | 79.85628000000001 | W | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| Pi_W | 88.62793774108202 | W | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| hover_power_W | 168.48421774108203 | W | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| v0_derived_m_s | 4.028542624594636 | m/s | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| v0_used_m_s | 4.028542624594636 | m/s | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| v0_table_m_s | 4.03 | m/s | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | directly reported | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| disc_area_pi_R2_m2 | 0.5026548245743669 | m^2 | Eq.(64), journal p.2342 / PDF p.14; Table I definitions | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| V_ME | 10.211691198388639 | m/s | Numerical derivation from Eq.(12); bounded refinement and dense-grid check | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |
| V_MR | 18.294480351062063 | m/s | Numerical derivation from Eq.(12); bounded refinement and dense-grid check | derived | ieee_2019 / CURRENTLY_VERIFIED_PASS |

P0/Pi are computed from raw Table I values, not independent fitted constants. The exact rounded disc area .503 m^2 is retained rather than substituted with pi*.4^2. The figure uses derived v0=4.028542624594636 m/s, and separately records the table value4.03 m/s. The legacy `arxiv_2018_v1` profile retains its original table-value policy7.2 m/s and agrees with every `PropulsionParams` field in `paper.yaml` within1e-10.
These are parameters of one reference aircraft, not experimental proof that every HAP-UAV CV-QKD UAV has these characteristics. The induced-power increment k=.1 is distinct from the RF NLoS loss kappa=.2; RF altitude, bandwidth, communication power and RF endpoints are not imported.
The newly requested rotor Figure02 is exported under `figures/ieee_2019/fig02_propulsion_power_ieee2019.*`; it does not replace the older blocked `fig02_cloud_maps` catalog item. `paper-mode: NOT_RUN`, missing fs/valid fraction/m0/epsilon/Emax/q0/HAP horizontal coordinates/cloud-layer inputs, source-evidence limitations and all old results remain unchanged. Earlier provenance-manifest hashes describe the earlier document snapshot; its original bytes are preserved in `ieee_2019_rotor_verification/parameter_provenance_before.md`, rather than rewriting those manifests after this append.
