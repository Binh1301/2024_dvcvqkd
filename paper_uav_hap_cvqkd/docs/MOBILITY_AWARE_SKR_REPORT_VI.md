# Tối ưu vị trí UAV và nguồn MB dưới mây chuyển động

Ngày 2026-10-14. CURRENTLY_VERIFIED_PASS cho mô phỏng minh họa; không phải chứng nhận bảo mật hoặc kết quả final-test.

Đã hoàn tất: 100 vị trí, 30 slot × 20 s, 197 nguồn MB (giữ đủ 182 nguồn gốc), 200 trạng thái sạch/có mây, 39.400 phép đánh giá. Không tính C,w mới; không AP/AO hoặc nội suy. 15 tests và smoke 30 phép đánh giá đã đạt trước lượt đầy đủ.

| Phương án | SKR trung bình (bits/use) | Khả dụng (%) | Quãng bay (m) | Tăng so S1 (%) | Tăng so S2 (%) | Mục tiêu riêng (bits/use) |
|---|---:|---:|---:|---:|---:|---:|
| S1 Reference Fixed | 0.0335033917 | 100 | 0 | 0 | -37.3692 | 0.0335033917 |
| S2 Optimized Stationary | 0.05349345892 | 100 | 0 | 59.6658 | 0 | 0.05349345892 |
| S3 Moving SKR Only | 0.06188325371 | 100 | 2323.6068 | 84.7074 | 15.6838 | 0.06188325371 |
| S4 Moving Mobility-Aware | 0.0610419135 | 100 | 600 | 82.1962 | 14.111 | 0.0604419135 |

S2 chọn vị trí cố định (950, 950) m. S4 dùng lambda=0.001 bits/use, D_ref=1000 m. Mục tiêu có phạt và SKR trung bình là hai đại lượng riêng; cột mục tiêu riêng của S1–S3 có lambda=0. CSV còn lưu objective_at_common_positive_lambda để so sánh cùng mục tiêu.

Hình học minh họa: h_H=20 km, h_U=1 km, UAV tham chiếu (450,450) m, HAP (11419.65511459133,450) m. Tọa độ này giữ đúng L_ref=21.9393102292 km; azimuth +x là giả định minh họa vì repo không có tọa độ HAP thực tế. Mây giả lập ở 5 km, bán kính 420 m, suy hao 10 dB, tâm đầu (2093.7168662297537,450) m, vận tốc (3,0) m/s. Các tham số này không phải đo đạc thời tiết.

Tái sử dụng derive_physical_inputs, LiteralChannel.from_physical, PhysicalFadingDistribution.moments, authenticate/evaluate_authenticated, canonical MB và normalization, deterministic_mutual_information, _holevo_from_source_moments và covariance hiện có. Tệp audit.json lưu đường dẫn/hash; code_equation chi tiết có trong báo cáo SKR trước. Ba mômen/PDF Eq. (10)/C,w/ensemble và Eq. (20) giữ nguyên producer.

T_cloud=10^(-A_c b/10) nhân đúng một lần vào eta_atm của luật thô. Sau đó áp dụng conditioning active trên 0<T<=1 và giữ atom AoA. Đây không phải nhân trực tiếp cả ba mômen đã chuẩn hóa; thay đổi tail/normalizer được tính lại. Mômen thứ ba vẫn bằng 2+(xi_ch−1)mean_eta, không nhân phần shot/detector noise với suy hao mây.

Mô hình SKR là effective_channel_no_fading_noise: T_eff=mean_sqrt_eta², xi_eff=0.0186, N_eff=T_eff xi_ch, a=VA+1, b=1+T_eff(VA+xi_ch), Z*=2sqrt(T_eff)C−sqrt(2T_eff xi_ch w). Ideal heterodyne R=1, xi_det=0, chi_het=1, beta=0.95; phase/adaptive optics OFF. MI discrete 256-QAM mới GH8/16/32 và Holevo direct Z_star dùng cùng ensemble/noise. Đây là xấp xỉ Gaussian bỏ phương sai fading, chưa là security lower bound của kênh fading.

P1 vét cạn nguồn MB ở mỗi vị trí/trạng thái; giữ signed K trong all_candidate_evaluations.csv và dùng S=max(0,K) cho bảng tiện ích. P2 tối đa trung bình theo vị trí cố định. P3 dùng DP với d<=15×20=300 m mỗi bước, vị trí đầu tự chọn, không tính chi phí triển khai. Mục tiêu là mean(S)−lambda D_fly/D_ref, không phải mô hình năng lượng và không báo joule/bits/J. Cùng catalog và quy tắc đổi nguồn mỗi slot cho cả bốn phương án. Khả dụng ở bảng là tỷ lệ slot có S>0, không phải xác suất không-outage AoA hoặc bằng chứng cấp khóa vận hành. P1 và DP tách được vì nguồn không có ràng buộc ngân sách liên-slot hoặc chi phí đổi tham số trong mô hình này.

Đã chạy năm vận tốc mây 0.5,1.5,3,4.5,6 m/s và tám lambda 0,0.0005,0.001,0.002,0.005,0.01,0.02,0.05 bits/use. Bảng hai trạng thái tại mỗi vị trí được tái sử dụng chính xác vì mọi thống kê khác độc lập thời gian/vận tốc trong mô hình binary này. Quỹ đạo mây là dữ liệu minh họa biết trước; không triển khai dự báo hoặc học máy.

Không có channel-use rate giả định: cumulative_skr_contributions=sum(S_n), hiển thị bits/use-slot. Không gọi số này là tổng bit khóa thực tế. Nếu cấu hình channel_use_rate_per_s, xuất thêm cumulative_secret_bits=rate×Delta_t×sum(S_n), vẫn chỉ là ước lượng theo functional đang dùng.

Kiểm tra độc lập toàn bộ dữ liệu: 200 cực đại P1; cache keys/hash và cùng C,w; PDF normalization/moment ordering; a,b,Z,K; uncertainty matrix và spectrum. Max residual spectrum=2.66454e-14, entropy=1.77636e-15. DP khớp vét cạn 3 vị trí/4 slot trong test; nghiệm toàn bộ khớp tái dựng DP. S2≥S1, S3≥S2; objective S4≥stationary cùng lambda. 3437 file cũ không đổi hash.

Giới hạn: cực đại chỉ trong 100 điểm và 197 nguồn được tính số, không phải tối ưu liên tục/toàn cục của hệ vật lý. C,w và GH có kiểm tra số nhưng chưa có enclosure tổng sai số chặt. Cloud là đĩa phẳng suy hao nhị phân, CSI/lịch mây biết trước, thống kê turbulence/pointing cố định tại từng vị trí; không fluid dynamics. Đánh giá rate tại vị trí slot, bỏ diễn biến link giữa các cell, trễ reacquisition, overhead đổi nguồn và chi phí triển khai. Không đánh giá năng lượng đẩy thực tế.

Khác đoạn Overleaf tham khảo: triển khai phạt quãng đường theo yêu cầu đính kèm, không P_hov/e_mov/E_ref. Không sửa tệp TeX/PDF bên ngoài. PDF được hash-bound nhưng chưa trích xuất full text vì thiếu PDF parser; các công thức triển khai lấy từ task đính kèm và đoạn TeX người dùng cung cấp.

15 tests bao phủ A_c=0, hình học/biên/altitude mây, source/catalog/ref SKR, P2, DP-vét cạn, tốc độ, dominance, signed-negative handling, journal reuse/corruption và cache context. Lượt đầu bắt lỗi serialize UavMotion và assertion thừa rằng toàn lưới sạch ở slot đầu; sửa serializer và kiểm tra đúng reference ray đi vào/ra, không đổi physics để ép kết quả. Lưu log lỗi ban đầu và receipt lượt đạt.

Chạy từ paper_uav_hap_cvqkd bằng PowerShell:

```powershell
& .venv/Scripts/python.exe -m unittest tests.test_mobility_skr -v
& .venv/Scripts/python.exe scripts/run_mobility_skr_experiment.py --smoke --output results/mobility_demo_rerun
& .venv/Scripts/python.exe scripts/run_mobility_skr_experiment.py --output results/mobility_demo_rerun
```

Runner dùng cache journal cùng identity nếu cần tiếp tục lượt chưa xong; từ chối ghi đè lượt đã có experiment_receipt.json. Chỉnh tham số trong configs/mobility_aware_skr_demo.json và dùng output mới để giữ provenance.

Tệp mới: src/uav_mobility.py, src/mobility_skr.py, scripts/run_mobility_skr_experiment.py, scripts/plot_mobility_skr_results.py, scripts/finalize_mobility_skr_experiment.py, tests/test_mobility_skr.py, configs/mobility_aware_skr_demo.json. Scientific kernels/security functional/frozen specification và mọi cache/result cũ không đổi.

Artifacts: [summary.csv](../results/mobility_aware_skr_20261014/full/summary.csv), [time series](../results/mobility_aware_skr_20261014/full/scheme_time_series.csv), [bảng SKR](../results/mobility_aware_skr_20261014/full/skr_table.csv), [final validation](../results/mobility_aware_skr_20261014/final_validation.json).

- [figure_1_cloud_and_uav_trajectory.png](../results/mobility_aware_skr_20261014/full/figure_1_cloud_and_uav_trajectory.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_1_cloud_and_uav_trajectory.pdf)
- [figure_2_skr_vs_time.png](../results/mobility_aware_skr_20261014/full/figure_2_skr_vs_time.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_2_skr_vs_time.pdf)
- [figure_3_cumulative_skr.png](../results/mobility_aware_skr_20261014/full/figure_3_cumulative_skr.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_3_cumulative_skr.pdf)
- [figure_4_average_skr_vs_cloud_velocity.png](../results/mobility_aware_skr_20261014/full/figure_4_average_skr_vs_cloud_velocity.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_4_average_skr_vs_cloud_velocity.pdf)
- [figure_5_skr_and_flight_vs_penalty.png](../results/mobility_aware_skr_20261014/full/figure_5_skr_and_flight_vs_penalty.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_5_skr_and_flight_vs_penalty.pdf)
- [figure_6_optimized_source_parameters.png](../results/mobility_aware_skr_20261014/full/figure_6_optimized_source_parameters.png) / [PDF](../results/mobility_aware_skr_20261014/full/figure_6_optimized_source_parameters.pdf)

Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS và frozen-hash mismatch cũ vẫn giữ. Không training, held-out/final-test/publication evaluation, AP/AO, source generation, commit hoặc push. STOP sau báo cáo minh họa này.
