# Cấu hình receiver30: truy vết tham số và kiểm chứng hai mô hình

**Model A tái lập K=0.0053925326540356644 bits/use. Model B bị BLOCKED vì PDF không đạt tolerance1e-10.** Đây là kiểm tra đúng một cấu hình cố định, không tối ưu VA,ν hoặc aperture. Tất cả code mới, report và receipts ở thư mục con này; tệp/caches/kết quả cha không bị ghi đè.

## 1. Bảng đầy đủ tham số thực tế

Mỗi giá trị có unit, trạng thái chỉ định/suy ra, file:function-line hoặc JSON/CSV pointer. parameters.csv giữ bảng dạng máy đọc. Tham số geometry35µrad/1.561µrad/.1m/0° là override thực tế; không lấy223/233µrad,15.61µrad,1m hoặc30° từ baseline. Source chính là historical_regressions.json#receiver30.saved và chuỗi caller parameter_adapter.optical → numeric.optical → power_conserving. Cấu hình configs/channel.yaml là production khác và không được dùng thay thế.

### A Geometry

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| h_HAP | 20 | km | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.h_hap_km; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| h_UAV | 1 | km | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.h_uav_km; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| zenith | 0 | degree | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.zenith_deg; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| slant_distance | 19 | km | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.L_km; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | (20-1)/cos(0)=19 |
| vertical_span | 19000 | m | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | h_HAP-h_UAV |

### B Optical

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| Dr | 0.3 | m | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.D_r; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| full_divergence | 35 | urad | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.divergence_urad; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| angular_jitter_per_axis | 1.561 | urad | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.jitter_urad; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| sigma_h_per_axis | 0.1 | m | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.sigma_h_m; results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py:17 | Actual scenario overrides baseline values; not taken from production channel.yaml |
| wavelength | 1.55e-06 | m | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Hard-coded wave; same value corroborated in configs/manuscript_mobility.json.optical |
| receiver_radius | 0.15 | m | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/untrusted_positive_skr_feasibility_20261022/model.py:28 | Dr/2 |
| w0 | 0.0281931613477072 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.w0_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | w0=2*lambda/(pi*full_divergence); wL=w0*sqrt(1+(L*lambda/(pi*w0^2))^2); w_eff=wL*sqrt(1+Gd) |
| wL_vacuum_propagation | 0.333693129007443 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.wL_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | w0=2*lambda/(pi*full_divergence); wL=w0*sqrt(1+(L*lambda/(pi*w0^2))^2); w_eff=wL*sqrt(1+Gd) |
| w_eff | 0.334566870682952 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.w_eff_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | w0=2*lambda/(pi*full_divergence); wL=w0*sqrt(1+(L*lambda/(pi*w0^2))^2); w_eff=wL*sqrt(1+Gd) |
| Gd | 0.00524365353384111 | dimensionless | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.G_d; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Repository HV closure; recomputed at 35urad |
| aperture_nu | 0.561911943682787 | dimensionless | B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:28 | sqrt(pi)*Dr/(2*sqrt(2)*w_eff); not MB nu |
| A0_erf_equivalent | 0.328547607695462 | power fraction | B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:28 | Used only by original product law; A has no constant A0 |
| A0_circular_at_w_eff | 0.331032005879856 | power fraction | A | Derived diagnostic | results/untrusted_positive_skr_feasibility_20261022/model.py:82 | Centered circular collection at w=w_eff; random width has no single fixed A0 |
| w_eq | 0.372506635166343 | m | B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:28 | Equivalent-beam width; NOT used in Model A collector |
| B_atm_A0 | 0.302263799079825 | dimensionless | B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:28 | eta_atm*A0 |
| pointing_chi_squared | 3.18854726792427 | dimensionless | B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:28 | w_eq^2/(4*sigma_s^2) |
| var_position_x | 0.01 | m^2 | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Independent per-axis Gaussian terms |
| var_position_y | 0.01 | m^2 | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Independent per-axis Gaussian terms |
| var_jitter_angle_per_axis | 2.436721e-12 | rad^2 | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Independent per-axis Gaussian terms |
| angular_displacement_per_axis | 0.029659 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.angular_displacement_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | L*theta_jitter |
| sigma_s_per_axis | 0.104305590842486 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.sigma_s_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | sqrt(sigma_h^2+(L*theta_jitter)^2) |
| sigma_s_squared_per_axis | 0.010879656281 | m^2 | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Total displacement variance per Cartesian axis |
| radial_RMS | 0.147510381200782 | m | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82 | Rayleigh displacement with zero boresight |
| boresight_x | 0 | m | A/B | Implicit fixed zero | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | Model A uses central ncx2/Rayleigh without a nonzero-boresight input; B rho default=0 |
| boresight_y | 0 | m | A/B | Implicit fixed zero | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | Model A uses central ncx2/Rayleigh without a nonzero-boresight input; B rho default=0 |
| rho | 0 | m | A/B | Implicit fixed zero | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | Model A uses central ncx2/Rayleigh without a nonzero-boresight input; B rho default=0 |
| launch_radius_of_curvature | infinity (implied) | m | A/B | Implicit model assumption | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | No R input exists in this call chain; waist-plane propagation formula. channel.yaml infinity is corroboration only. |
| receiver_radius_of_curvature | NOT_STORED_NOT_USED | m | A/B | Not an active parameter | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | No value invented; scalar collected-power model does not evaluate wavefront curvature. |
| AO | OFF | state | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | No AO efficiency multiplier |
| phase_noise | OFF_HISTORICAL_ASSUMPTION | state | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | No c_phi*VA term |
| additional_coupling_insertion_loss | NOT_MODELED | power fraction | A/B | Absent | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29; results/untrusted_positive_skr_feasibility_20261022/model.py:82 | No measured coupling/optics loss budget or hardware calibration supplied; not an extra factor silently set from baseline |
| transmitter_diameter_99percent | 0.0855621357842871 | m | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.transmitter_diameter_99percent_m; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 |  |

### C Atmosphere AoA

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| tau_zen | 0.92 | power fraction | A/B | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.tau_zen; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 |  |
| eta_atm | 0.92 | power fraction | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.eta_atm; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | tau_zen^sec(zenith); zenith=0 |
| Cn2_ground_coefficient | 1e-14 | m^(-2/3) | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:18 | Ground exponential coefficient A; distinguish full Cn2(0) |
| Cn2_full_profile_at_0 | 1.027e-14 | m^(-2/3) | A/B | Derived | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:18 | At h=0 the high-altitude term vanishes; HV includes background 2.7e-16 |
| wind_speed | 21 | m/s | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:18 |  |
| HV_rytov_integral | 3.59933916310241e-10 | m^(7/6) | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.HV_rytov_integral; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Raw Rytov used as log-irradiance variance under weak-turbulence approximation |
| HV_mu2_integral | 5.03492629577772e-14 | m^(1/3) | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.HV_mu2_integral; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Raw Rytov used as log-irradiance variance under weak-turbulence approximation |
| raw_Rytov_variance | 0.04145352708219 | dimensionless | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.v; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | Raw Rytov used as log-irradiance variance under weak-turbulence approximation |
| turbulence_factor | 1 | dimensionless | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 |  |
| log_irradiance_mean | -0.020726763541095 | dimensionless | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | S~N(-v/2,v); A uses width=w_eff*exp(-S/2), B multiplicative irradiance I=exp(S) |
| log_irradiance_variance | 0.04145352708219 | dimensionless | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | S~N(-v/2,v); A uses width=w_eff*exp(-S/2), B multiplicative irradiance I=exp(S) |
| log_irradiance_SD | 0.203601392633228 | dimensionless | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | S~N(-v/2,v); A uses width=w_eff*exp(-S/2), B multiplicative irradiance I=exp(S) |
| log_amplitude_variance | 0.0103633817705475 | dimensionless | A/B | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:221 | S~N(-v/2,v); A uses width=w_eff*exp(-S/2), B multiplicative irradiance I=exp(S) |
| AoA_FOV_half_angle | 0.00625 | rad | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | 6.25mrad; full FOV=12.5mrad |
| AoA_angular_SD | 0.0015 | rad per axis | A/B | Specified in actual code | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | 1.5mrad; Rayleigh magnitude |
| AoA_additional_turbulent_variance | NO_SEPARATE_TERM | rad^2 | A/B | Absent in actual formula | results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | P0 uses .0015 directly; no Gd/AoA turbulence term added |
| P0 | 0.000169856676561411 | probability | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.P0; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | P0=exp(-FOV_half^2/(2*sigma_AoA^2)); P1=1-P0 |
| P1 | 0.999830143323439 | probability | A/B | Derived | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved.P1; results/positive_skr_without_receiver_enlargement_20261022/numeric.py:29 | P0=exp(-FOV_half^2/(2*sigma_AoA^2)); P1=1-P0 |

### D Detector noise

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| detector_model | untrusted loss plus output electronic noise | model | A | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 |  |
| eta_det | 0.95 | dimensionless | A | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 |  |
| epsilon_det | 0.005 | SNU output | A | Specified historical override | results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 |  |
| xi_ch | 0.0186 | input-referred SNU | A/B | Specified in evaluator | results/manuscript43_homodyne_audit_20261023/audit_model.py:133; results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 |  |
| vacuum_variance | 1 | SNU | A/B | Specified quadrature convention | results/manuscript43_homodyne_audit_20261023/audit_model.py:69; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 |  |
| xi_det | 0.005 | SNU literal coefficient | B | Specified current request | task.txt#Section3; protocol.json#model_B | Independent coefficient in xi(eta)=xi_ch+xi_det/eta; no efficiency parameter, no hardware epsilon conversion |
| eta_det | NO_PARAMETER | dimensionless | B | Explicitly absent | task.txt#Section3; results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Neither .95 nor an implicit replacement eta_det=1 is passed to the B function |
| electronics_at_outage | included | per transmitted use | A/B | Specified convention | results/manuscript43_homodyne_audit_20261023/audit_model.py:133; results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | A epsilon_det every use; B zero-limit extension adds xi_det*P0 |

### E Modulation protocol

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| M | 256 | symbols | A/B | Specified | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#support_size; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| VA | 1.62499953997036 | SNU | A/B | Specified exact source | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#V_A_hex; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| nbar | 0.812499769985182 | photons/use | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| nu_raw | 0.25 | dimensionless | A/B | Specified exact source | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#nu_mb_raw_hex; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| nu_repo | 10.625 | dimensionless | A/B | Exact source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#nu_mb_repo_hex; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| C | 1.21353024106131 | source moment | A/B | Exact cached | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#C; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| w | 2.85649327689112e-10 | source moment | A/B | Exact cached | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#w; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| source_hash | 01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754 | SHA256 ensemble | A/B | Exact identity | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#ensemble_hash; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| PMF_sum | 1 | probability | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| mean_alpha_real | 1.08299972136961e-17 | amplitude | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| mean_alpha_imag | 0 | amplitude | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| mean_X | 1.21360443947927e-17 | quadrature | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| Var_X | 1.62499953997036 | SNU | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| peak_photons | 22.8515626010808 | photons | A/B | Derived | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:65; src/manuscript_mobility.py:90; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| support_size | 256 | symbols | A/B | Verified | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#support_size; results/manuscript43_homodyne_audit_20261023/audit_model.py:38 | Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar |
| MB_mapping | nu_repo=42.5*nu_raw | equation | A/B | Exact source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#mb_convention |  |
| beta | 0.95 | dimensionless | A/B | Specified in evaluator | results/manuscript43_homodyne_audit_20261023/audit_model.py:160; results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 |  |
| measurement | homodyne one real quadrature | type | A/B | Specified current request | results/manuscript43_homodyne_audit_20261023/audit_model.py:69 |  |
| reconciliation | reverse, asymptotic | type | A/B | Specified protocol | protocol.json; results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved |  |
| source_moment_route | ARBITRARY_PRECISION_FALLBACK | method | A/B | Exact source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#source_moment_route | Reuses existing arbitrary-precision source payload; no new source moment computation |

### G Numerical

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| cached_source_density_eigenvalue_tolerance | 1e-12 | absolute tolerance | A/B | Historical source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#source_settings.density_eigenvalue_tolerance | Settings of reused source calculation; no fresh AP certification |
| cached_source_physicality_tolerance | 1e-10 | absolute tolerance | A/B | Historical source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#source_settings.physicality_tolerance | Settings of reused source calculation; no fresh AP certification |
| cached_source_precision_ladder | [1050, 1250, 1450] | digits | A/B | Historical source metadata | results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json#source_settings.precision_ladder | Settings of reused source calculation; no fresh AP certification |
| moment_width_GH | 32 | nodes | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Historical moment computation unchanged |
| MI_GH_primary | 128 | nodes | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Comparison to GH64; same source/moments |
| full_Z_grid_primary | 129 | nodes | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Comparison to33; numerical resolution, not global certification |
| source_model_decimal_precision | 80 | digits | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Preserved imported historical mpmath setting |
| raw_PDF_decimal_precision | 90 | digits | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Original audit closed form |
| entropy_check_precision | 80 and 110 | digits | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Independent entropy formula |
| mass_tolerance | 1e-10 | absolute | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Inherited unchanged before evaluation |
| MI_absolute_tolerance | 2e-10 | bits/use | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Independent adaptive integration and GH agreement |
| Holevo_absolute_tolerance | 2e-08 | bits/use | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Grid33/129 |
| rate_denominator | all transmitted uses including AoA outage | uses | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | No postselection or factor2 |
| repetition_rate | UNKNOWN_NOT_MODELED | Hz | A/B | Specified numerical rule | protocol.json; results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | No bits/s claim |

### F Effective channel

| Parameter | Giá trị | Đơn vị | Model | Chỉ định / suy ra | Nguồn chính xác | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| M0 | 1 | probability | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| E_eta | 0.228930928770195 | power fraction | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| E_sqrt_eta | 0.472859898131668 | amplitude fraction | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| eta_f | 0.223596483261091 | power fraction | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| E_eta_xi_pre_detector | 0.00952127316986247 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| E_eta_xi_after_detector | 0.00904520951136934 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| N_fading_pre | 0.00866847149829003 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| N_channel_pre | 0.00425811527512562 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| N_electronic_pre | 0.00526315789473684 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| N_post | 0.0172802574347449 | SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| xi_f_input_quantum | 0.0813507636741876 | input-referred SNU | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| sigma2_MI | 1.01728025743474 | SNU output | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| T_Holevo | 0.212416659098037 | power fraction | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| Bob_unconditional_variance | 1.3624572307511 | SNU output | A | Derived | results/untrusted_positive_skr_feasibility_20261022/model.py:82; results/manuscript43_homodyne_audit_20261023/audit_model.py:133 | Physical detector output; pre and post reference planes distinguished |
| M0 | 0.9999999998943 | probability | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Unnormalized retained-law moment; not a validated probability model |
| tail_outside_0_1 | 1.05699551364938e-10 | probability | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Unnormalized retained-law moment; not a validated probability model |
| E_eta | 0.230060363122391 | dimensionless | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Unnormalized retained-law moment; not a validated probability model |
| E_sqrt_eta | 0.472722659854402 | dimensionless | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/audit_model.py:233 | Unnormalized retained-law moment; not a validated probability model |
| eta_f | 0.22346671313982 | dimensionless | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| mean_eta_xi | 0.00927912275354797 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| N_fading | 0.0107146781884023 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| N_effective | 0.0199938009419503 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| xi_f | 0.0894710476608675 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| sigma2_MI | 1.01999380094195 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| T_Holevo | 0.22346671313982 | dimensionless | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| zero_atom_noise_contribution | 8.49283382807053e-07 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |
| active_only_mean_eta_xi | 0.00927827347016516 | SNU | B | Derived diagnostic | results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py:40 | Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation |



## 2. Hai mô hình và mặt phẳng noise

**Model A** giữ nguyên power_conserving_random_width. Đặt \(S\sim N(-v/2,v)\), \(w(S)=w_{eff}\exp(-S/2)\). Gaussian beam chuẩn hóa công suất được thu bằng circular-aperture ncx2 CDF tại từng width/offset; AoA thêm atom0. Vì vậy \(0\leq\eta\leq\eta_{atm}=.92\), tổng mass1 và không có upper-tail ngoài1. Width dispersion này là surrogate đã khai báo; không đồng nhất với PDF tích lognormal×pointing củaB.

Đặt \(T_f=m_h^2\), \(N_f=(m_1-T_f)V_A\), \(N_c=.0186m_1\). Detector untrusted có \(\eta_d=.95\), output electronics \(\epsilon_d=.005\):

\[
T_q=.95T_f,\quad N_{post}=.95(N_f+N_c)+.005,\quad \sigma_N^2=1+N_{post}.
\]

Pre-detector noise budget có \(\langle\eta\xi_A\rangle=.0186m_1+.005/.95\). Sau detector, phần channel/electronic là \(.95(.0186m_1)+.005\). \(\xi_{f,A}=N_{post}/T_q\), tương đương \(N_{pre}/T_f\). Vacuum tại physical output là1, không cộng thêm loss vacuum lần nữa. Cùng \(T_q,N_{post}\) trong DBL full-Z,covariance và homodyne \(\nu_3=\sqrt{a(a-Z^2/b)}\).

**Model B** dùng chính PDF43 trên[0,1], cùng geometry và source, nhưng \(\xi_{det}=.005\) là tham số độc lập theo yêu cầu hiện tại:

\[
\xi_B(\eta)=.0186+\frac{.005}{\eta},\quad
m_n=.0186m_1+.005M_0,\quad
N_B=(m_1-m_h^2)V_A+m_n,\quad
\sigma_{N,B}^2=1+N_B,\quad T_B=m_h^2.
\]

**Không có ηdet trong Model B**, không chuyển .005 thành .005/.95 và không nhân transmittance/noise thêm. Mean homodyne là \(2\sqrt{T_B}\operatorname{Re}\alpha_k\); sửa mean phức của phương trình in để tạo real1D density theo yêu cầu Gaussian homodyne hiện tại. Nếu mass hợp lệ, các tham số \(T_B,N_B\) phải đi nguyên vào bound/covariance/Holevo; ở đây gate mass đã chặn trước phép tính MI/Holevo.

| Đại lượng | Model A — random-width lịch sử | Model B — PDF43, ξdet=.005 |
| --- | --- | --- |
| Trạng thái | CURRENTLY_VERIFIED_PASS_COMPONENT_ONLY | BLOCKED_BY_SCIENTIFIC_MODEL |
| E[eta] | 0.228930928770195 | 0.230060363122391 |
| E[sqrt(eta)] | 0.472859898131668 | 0.472722659854402 |
| eta_f | 0.223596483261091 | 0.22346671313982 |
| E[eta*xi] trước detector / literal | 0.00952127316986247 | 0.00927912275354797 |
| N tại output MI | 0.0172802574347449 | 0.0199938009419503 |
| xi_f input quantum | 0.0813507636741876 | 0.0894710476608675 |
| sigma_N^2 | 1.01728025743474 | 1.01999380094195 |
| T quantum Holevo | 0.212416659098037 | 0.22346671313982 |
| I_AB | 0.21074687539664 | BLOCKED |
| beta*I_AB | 0.200209531626808 | BLOCKED |
| chi_BE | 0.194816998972772 | BLOCKED |
| K raw (bits/use) | 0.00539253265403566 | BLOCKED |



Các sigma² và xi_f củaB là **diagnostic coefficients từ unnormalized moments**, không phải xác nhận channel vật lý. Không ghép MI củaA với Holevo củaB, không nhân homodyne MI lên2. Conditional noise khác Bob unconditional variance \(b=1+TV_A+N\).

## 3. Chuẩn hóa PDF43 và ba moment

M0 (decimal90-derived) = 0.99999999989430044863506229732601953316423386447099047745275419693950122265169295.

Mass ngoài[0,1] = **0.00000000010569955136493770267398046683576613552900952254724580306049877734830704676574808**. Nó lớn hơn ngưỡng1e-10, nên giữ **FAILED** dù chỉ vượt khoảng5,7%. Atom AoA \(P_0=0.00016985667656141065\) được cộng riêng vào zeroth moment.

| Moment / mass | Closed form | Tích phân độc lập | Sai khác |
| --- | --- | --- | --- |
| 0 | 0.999830143217739 | 0.999830143217739 | -1.11022302462516e-16 |
| 0.5 | 0.472722659854402 | 0.472722659854402 | -5.55111512312578e-17 |
| 1 | 0.230060363122391 | 0.230060363122391 | -5.55111512312578e-17 |



moments.csv có cả mass tổng/mass tail/three noise moments checks. \(\langle\eta\xi_B\rangle\) đối chiếu linear combination của hai quadrature độc lập0/1 cộng atom: \(.0186\int_0^1\eta f(\eta)d\eta+.005[P_0+\int_0^1 f(\eta)d\eta]\).
Zero-limit extension \(\lim_{\eta\to0}\eta\xi_B(\eta)=.005\) cho phần atom bằng 8.4928338280705324e-07. Active-only bỏ phần đó; giá trị so sánh được lưu riêng, không áp dụng postselection.

Nguyên nhân: irradiance lognormal unbounded, aperture-equivalent pointing tối đa hữu hạn, nên tích raw vẫn có xác suấtη>1. Tích phân giữ tới1 bỏ tail nhưng không chuẩn hóa lại. Không clipping/renormalization/chuyển tail sang outage/thay PDF bằng random-width. Model B ghi MI,βMI,Holevo,K là unavailable/BLOCKED, không phải0.

## 4. Tái lập, provenance và giới hạn

Model A so sánh trực tiếp với corrected_same_channel.csv#receiver30 và old_vs_new.csv#receiver30; numerical_checks.json ghi từng residual và independent check. MI GH64/128,256-symbol/16-level/X/P/scaling,adaptive integration,full-Z33/129,entropy80/110 và uncertainty/symplectic matrix được kiểm tra riêng. Source hash là 01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754; C=1.2135302410613147,w=2.8564932768911209e-10,payloadSHA=f50b7253bc19791fa5e652832fdcb903fc198094e3cc871733a5855977a95018. Source units VA=2nbar; không đổi thành nbar/2.

Giá trị pooled fading MI cũ ở selection.json là 0.21078485464976601, K=0.0054286129445057785. **Không dùng nó thay Gaussian MI** đang kiểm tra; con số dương mục tiêu0.005392532654035664 thuộc Gaussian effective random-width modelA với detector. Cả hai số cũ được giữ đúng context.

Parameter A0 và curvature cần đọc đúng vai trò: A dùng exact circular collection với width ngẫu nhiên nên không có A0 cố định; A0_erf/w_eq thuộcB. Launch curvature không được truyền như tham số: wL dùng waist-plane formula, tương đương launchR=∞; curvature tại receiver không được lưu/dùng. Không lấy một radius chưa có từ manuscript. AO/phaseOFF; thêm coupling/insertion loss, saturation,LO,bandwidth,rate và hardware calibration không được mô hình hóa.

39 scoped checks đạt; PDF normalization củaB là phát hiện FAILED được giữ, không bị đổi thành PASS. Đây không là toàn bộ test suite hoặc security certification. Fixed-source moments được lấy nguyên từ cache arbitrary-precision cũ; không chạy lại AP. Full-Z finite numerical maximization không là rigorous global enclosure. Moment-matched Gaussian MI không là exact conditional density của fading. Chưa có operational fading/parameter-estimation/finite-key/composable proof hoặc xác nhận hardware.

Lần đầu dựng bảng provenance gặp TypeError vì inspect nhận lru_cache wrapper. attempt_1/ giữ code/protocol/lỗi; helper đã unwrap đúng function trước khi lấy file/dòng. Các phép tính được kiểm tra lại sau sửa helper; không đổi phương trình hoặc tolerance.

Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,ObjectiveC USER_STOPPED. Frozen SHA hiện tại khác historical expected trong AGENTS nhưng không thay đổi; không promotion. Parent seal đã PASS trước khi task này cập nhật ledger. Các artifact hash cũ giữ nguyên; ledger hashes cũ là snapshot lịch sử, nên verifier cha không phải verifier cho ledger của task mới. verify.py của thư mục con kiểm tra snapshot/protected files và artifacts task này.

Lệnh đã chạy từ project root:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py

Không chạy lại producer đã hoàn tất. Kiểm tra chỉ đọc:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/verify.py

Không production/security-source/frozen/cache edits,optimization,training/final-test/heldout/publication,baseline/threshold approval hoặc commit/push.
