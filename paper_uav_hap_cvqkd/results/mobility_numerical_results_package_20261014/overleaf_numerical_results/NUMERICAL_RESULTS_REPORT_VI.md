# Gói Numerical Results cho mô hình UAV–HAP dưới mây chuyển động

Ngày 2026-10-14. Gói hình/bảng theo định dạng IEEE; số liệu khoa học vẫn là PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE. Không chứng nhận security cho kênh fading hoặc nâng lifecycle publication.

Đã xác minh và tái sử dụng đủ 39.400 kết quả MB, 200 trạng thái, 100 vị trí, 30 slot. Không chạy lại bảng MB. Tính mới đúng 6.000 đối chứng Uniform (30 nguồn × 200 trạng thái), sau 30 phép smoke; không tính C,w mới, không AP/AO, nội suy hay Monte Carlo. 25 tests đã đạt, gồm nguyên 15 tests cũ và 10 kiểm tra dữ liệu/hình mới.

| Scheme | Mean SKR (bits/use) | Flight (m) | lambda (bits/use) | Own objective |
|---|---:|---:|---:|---:|
| S1 Reference Fixed | 0.0335033917 | 0 | 0 | 0.0335033917 |
| S2 Optimized Stationary | 0.05349345892 | 0 | 0 | 0.05349345892 |
| S3 Moving SKR Only | 0.06188325371 | 2323.6068 | 0 | 0.06188325371 |
| S4 Moving Mobility-Aware | 0.0610419135 | 600 | 0.001 | 0.0604419135 |

S4 giữ 98.640440% SKR của S3, giảm quãng bay 74.178075%, tăng 82.196221% so S1 và 14.110986% so S2. Không gọi quãng bay là năng lượng. Table II tách mục tiêu riêng và mục tiêu chung lambda=0.001 để tránh so sánh khác đại lượng.

Cumulative mới là C(n)=sum(S_1..S_n)/30, đơn vị bits/use; endpoint bằng đúng mean SKR. Không có f_use được xác thực nên không xuất tổng bit khóa và không gọi kết quả là finite-size-secure key yield. K thô có dấu được giữ nguyên; tiện ích S=max(0,K) có định nghĩa riêng.

Boundary audit: có mây, S2 chọn (950,950) m với 5 slot bị mây. Counterfactual dùng các giá trị sạch trong cache chọn (950,450) m. Tọa độ HAP lệch +x làm giảm L về biên phải; mây và hệ số giao mặt phẳng làm (950,950) ít bị che hơn. Đây là optimum của lưới hữu hạn, không suy ra optimum liên tục hoặc lỗi biên.

Uniform đối chứng dùng PMF/amplitude/cache C,w riêng và tối ưu VA trên 30 nguồn đã xác thực. MB dùng 197 cặp nu_raw/VA. Từng family tự tối ưu stationary/DP; cùng vùng, mây, slot, R/xi/beta/mobility, và source adaptation mỗi slot. Không ép Uniform đi theo quỹ đạo MB hoặc dùng nguồn MB cho Uniform. Catalog và VA chọn có thể khác, nên gain thể hiện joint source adaptation trong ngân hàng sẵn có, không phải cô lập PS ở cùng năng lượng trung bình.

| Comparison | Uniform (bits/use) | MB (bits/use) | Absolute MB gain | Percent gain if Uniform>0 |
|---|---:|---:|---:|---:|
| stationary | 0.004525533062 | 0.05349345892 | 0.04896792585 | 1082.036639% |
| moving_lambda0 | 0.005221740888 | 0.06188325371 | 0.05666151282 | 1085.107707% |

Main velocity figure dùng đúng năm vận tốc cũ, chỉ đổi độ lớn v theo +x. Ngoài ra, khảo sát riêng 5 kịch bản cố định (gốc, lệch tâm y±150 m, đổi hướng±15°) ở 5 vận tốc, tổng 100 so sánh từ bảng trạng thái MB có sẵn; không tính SKR mới. Mean/SD chỉ mô tả năm kịch bản xác định, không phải confidence interval hay mẫu khí tượng ngẫu nhiên.

Điều bỏ qua trong mô hình: N_fade=(mean_eta−T_eff)VA; noise kênh đúng theo second moment là mean_eta xi_ch nhưng mô hình hiện dùng T_eff xi_ch. Tổng chênh output variance=(mean_eta−T_eff)(VA+xi_ch). Nó ảnh hưởng b, penalty trong Z và Gaussian MI. CSV fading_omission_audit ghi số cụ thể ở mọi source thắng; chỉ là audit đại số, không phải kết quả security mới. PDF Eq. (10), support/normalizer/atom và ba mômen vẫn giữ nguyên.

Có code full-fading MI/Holevo, nhưng chưa đủ điều kiện tái chạy thành bảng validated đầy đủ: MI mixture đã lưu không đạt sampling precision, Holevo interval chưa có rigorous global enclosure/security protocol; 15 nguồn MB bổ sung nằm ngoài snapshot nguồn được evaluator corrected cũ cho phép. Không nới tolerance, bypass provenance hoặc ghép MI/Holevo khác noise để gọi là validated. Các hình chính giữ nguyên nhãn Gaussian sơ bộ như yêu cầu. Không kết luận rằng toàn bộ mô hình fading có SKR âm từ một điểm diagnostic.

Tất cả hình có bản single (3.5 inch) và double (7.16 inch), PDF vector và PNG 300 dpi, cùng màu/line/marker. Fig1 biểu diễn tập che khuất chiếu qua tia vào mặt phẳng UAV: center=(c−a qH)/(1−a), radius=Rc/(1−a), a=(hc−hU)/(hH−hU). Đây không phải đặt mây ở cao độ UAV; tâm mây thật vẫn ở 5 km và lưu CSV. Fig2 giữ nhảy slot và shade thời gian reference bị che. Fig4 không vẽ đường Pareto nội suy; đủ tám lambda kể cả điểm trùng. Fig6 là S2/S4 và giữ nguyên mọi bước tham số.

Giới hạn: cloud đĩa/suy hao nhị phân, forecast/CSI biết trước, slot endpoints bỏ diễn biến trong transit, reacquisition/source-overhead, không propulsion model, không security protocol/finite-size/source total-error enclosure. Khả dụng=phần trăm slot S>0, không phải xác suất không-outage AoA. Tọa độ HAP là embedding minh họa được user xác nhận, không measured location.

Artifacts và caption:

- Figure 1: [single PDF](figures/figure_1_cloud_trajectories_single.pdf), [double PDF](figures/figure_1_cloud_trajectories_double.pdf), [PNG](figures/figure_1_cloud_trajectories_double.png).
  Cloud-induced occlusion and trajectories: (a) S3, (b) S4. Gray circles are occlusion footprints mapped through the altitude-plane ray intersection into UAV coordinates, not clouds located at UAV altitude. For a=(h_c-h_U)/(h_H-h_U), their centers are (c-a q_H)/(1-a) and radii R_c/(1-a). Actual cloud centers at h_c=5 km and UAVs at h_U=1 km are stored in the plotting CSV. Arrows indicate movement; open circles and crosses show start/end, which may coincide.
- Figure 2: [single PDF](figures/figure_2_skr_time_single.pdf), [double PDF](figures/figure_2_skr_time_double.pdf), [PNG](figures/figure_2_skr_time_double.png).
  Original per-slot usable SKR for S1--S4, with post-step rendering and no smoothing. Gray intervals indicate cloud blockage of the reference optical path. All results use the same preliminary effective-Gaussian channel, source adaptation, beta=0.95 and ideal heterodyne receiver.
- Figure 3: [single PDF](figures/figure_3_cumulative_normalized_single.pdf), [double PDF](figures/figure_3_cumulative_normalized_double.pdf), [PNG](figures/figure_3_cumulative_normalized_double.png).
  Cumulative normalized SKR C(n)=sum_{k=1}^n S(k)/N_t, with C(0)=0 and C(N_t) equal to the mean usable SKR. No channel-use rate is specified, so these values are in bits/use, not total secret bits or finite-size-secure key yield.
- Figure 4: [single PDF](figures/figure_4_skr_flight_tradeoff_single.pdf), [double PDF](figures/figure_4_skr_flight_tradeoff_double.pdf), [PNG](figures/figure_4_skr_flight_tradeoff_double.png).
  Average SKR versus total flight distance for all eight evaluated movement penalties. Only evaluated points are drawn; overlapping lambda values remain separately listed in CSV. S2, S3(lambda=0) and S4(lambda=0.001 bits/use) are marked. Flight distance is not propulsion energy; average SKR and penalized objective are reported separately.
- Figure 5: [single PDF](figures/figure_5_cloud_velocity_single.pdf), [double PDF](figures/figure_5_cloud_velocity_double.pdf), [PNG](figures/figure_5_cloud_velocity_double.png).
  The five original cloud-speed cases with fixed +x direction and unchanged initial center, radius, attenuation, physical channel and mission. Curves connect only evaluated speed points for visual guidance, without interpolation or extrapolated results. No monotonicity is asserted.
- Figure 6: [single PDF](figures/figure_6_source_parameters_single.pdf), [double PDF](figures/figure_6_source_parameters_double.pdf), [PNG](figures/figure_6_source_parameters_double.png).
  Exact selected source pairs for S2 and S4: (a) nu_MB,raw and (b) V_A. Values are held over each slot, without interpolation. The repository convention is nu_repo=42.5 nu_raw. Both schemes use identical source-adaptation rules and the same finite MB catalog.
- Figure 7: [single PDF](figures/figure_7_uniform_mb_single.pdf), [double PDF](figures/figure_7_uniform_mb_double.pdf), [PNG](figures/figure_7_uniform_mb_double.png).
  Controlled optimized Uniform and MB comparison for stationary and moving(lambda=0) UAVs. Uniform optimizes VA over 30 authenticated Uniform sources; MB optimizes nu_raw and VA over 197 authenticated MB sources. Geometry, clouds, slots, receiver, noise and mobility constraints are common. Available catalog sizes and selected energy may differ; this is a joint source-adaptation comparison, not an isolated energy-matched shaping gain.

[Table I CSV](table_I_system_parameters.csv) / [LaTeX](table_I_system_parameters.tex); [Table II CSV](table_II_performance.csv) / [LaTeX](table_II_performance.tex). [Numerical Results LaTeX](numerical_results_section.tex), [standalone IEEEtran](ieee_numerical_results_standalone.tex).

LaTeX đã sinh theo IEEEtran với graphicx/amsmath; trình biên dịch pdflatex/latexmk/tectonic không có trong môi trường: BLOCKED_BY_ENVIRONMENT cho compile. Không tuyên bố đã compile PDF manuscript. Các PDF hình được Matplotlib xuất và kiểm tra riêng.

Các lệnh đã dùng, từ paper_uav_hap_cvqkd (ghi nhận quy trình; không chạy lại vào namespace đã hoàn tất):

```powershell
& .venv/Scripts/python.exe scripts/build_mobility_numerical_package.py prepare
& .venv/Scripts/python.exe -m unittest tests.test_mobility_skr tests.test_mobility_results_package -v
& .venv/Scripts/python.exe scripts/build_mobility_numerical_package.py uniform-smoke
& .venv/Scripts/python.exe scripts/build_mobility_numerical_package.py uniform
& .venv/Scripts/python.exe scripts/build_mobility_numerical_package.py finish
```

Uniform và finish từ chối chạy lại khi receipt hoàn tất đã có. prepare chỉ dùng để khởi tạo; không chạy lại phase này hoặc helper xuất hình vào namespace đã hoàn tất. Nhà nghiên cứu có thể dùng các helper plotting/CSV với thư mục mới khi cần variant; không chỉnh source-data cũ. Không sửa tệp Overleaf ngoài Downloads. Không commit/push. Frozen-hash blocker và NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.

Bằng chứng máy đọc: [package receipt](package_receipt.json), [kiểm tra độc lập](final_validation.json), [25 tests](test_receipt.json), [đối chứng Uniform](uniform/receipt.json), [audit security](scientific_validation_audit.json). CURRENTLY_VERIFIED_PASS áp dụng cho kiểm tra số liệu/xuất hình; trạng thái khoa học vẫn sơ bộ, compile TeX là BLOCKED_BY_ENVIRONMENT.
