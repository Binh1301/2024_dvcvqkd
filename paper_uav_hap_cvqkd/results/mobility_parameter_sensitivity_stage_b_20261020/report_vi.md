# Stage B — Độ nhạy mây bổ sung

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Thiết kế và phạm vi

Người dùng phê duyệt Stage B sau Stage A. Giữ nguồn P1 exact233 nguồn và cấu hình vật lý hiện tại; không tính lại kênh, MI, Holevo hoặc C,w. Có16 cấu hình riêng biệt:8 mức p,5 mức ell và5 mức rho cùng chia sẻ baseline. Chỉ tạo300 mask cho p=0,3/0,5/0,7;13 cấu hình còn lại được replay chính xác từ archive. Không dùng SKR quang học cũ.

Mỗi cấu hình dùng100 realization ID0–99,seed20261015,lưới100 vị trí,30slot×20s,vmax15m/s,Dref1000m. Hai λ tuyệt đối là0 và9.468026677248516×10⁻⁶. Chín trường hợp mobility Stage A được tái sử dụng; bảy trường hợp mới cần1400 cặp DP/Greedy,ngoài200 cặp audit baseline.

S=(1−C)Kstar;U=mean(S_path)−λD/1000. Greedy dùng S_now−Ntλd/1000. Availability=mean(S_path>0),không dùng engineering threshold. P2/DP offline có thông tin toàn nhiệm vụ,Greedy chỉ đọc slot hiện tại; khởi đầu tự chọn.

CI95% pointwise dùng lại20.000 whole-mission bootstrap count vectors của Stage A,seed20261020;không tạo bootstrap draw mới. So sánh cùng ID và cùng trọng số resampling. Tỷ lệ là100×chênh lệch mean/mean baseline dương;NA khi không hợp lệ. CI chưa hiệu chỉnh nhiều so sánh,không phải giới hạn an toàn lượng tử.

## Hình và kết quả

### fig_B1_cloud_probability

[PDF vector](figures/fig_B1_cloud_probability.pdf) · [PNG 350 dpi](figures/fig_B1_cloud_probability.png) · [CSV](figures/fig_B1_cloud_probability_data.csv)

| Tham số | K P2 | K Greedy | K DP | U DP | D DP(m) | A P2(%) | A Greedy(%) | A DP(%) | Gain U/P2(%) | Gain U/Greedy(%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 1.5749468 | 1.5675060 | 1.5766271 | 1.5760590 | 6.000 | 100.000 | 99.933 | 100.000 | 0.0706 | 1.1487 |
| 0.2 | 1.5649826 | 1.5599774 | 1.5744672 | 1.5711473 | 35.064 | 99.900 | 99.933 | 100.000 | 0.3939 | 2.0372 |
| 0.3 | 1.5387505 | 1.5430554 | 1.5702651 | 1.5621402 | 85.814 | 98.967 | 99.400 | 99.967 | 1.5200 | 3.0248 |
| 0.4 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5486275 | 172.433 | 97.767 | 98.733 | 99.900 | 3.0750 | 4.4177 |
| 0.5 | 1.4492745 | 1.5035587 | 1.5536360 | 1.5267559 | 283.904 | 96.000 | 98.033 | 99.600 | 5.3462 | 4.8092 |
| 0.6 | 1.3767707 | 1.4746602 | 1.5371783 | 1.4993672 | 399.356 | 93.000 | 96.667 | 99.467 | 8.9046 | 5.9106 |
| 0.7 | 1.2701386 | 1.3692316 | 1.5029566 | 1.4506553 | 552.399 | 86.900 | 90.567 | 98.100 | 14.2124 | 11.3016 |
| 0.8 | 1.0894075 | 1.2479814 | 1.4347523 | 1.3622131 | 766.150 | 75.400 | 83.467 | 95.933 | 25.0416 | 15.9504 |

K/U trong bảng có đơn vị10⁻⁴ bit/use. Đánh giá phương án tốt hơn bằng U;không suy availability hoặc K từng mission từ ưu thế U.

| Tham số | ΔU DP−P2 | CI95% | ΔU DP−Greedy | CI95% |
|---|---:|---|---:|---|
| 0.1 | 1.112154e-07 | [2.1924495e-08, 2.3312888e-07] | 1.7899274e-06 | [1.2463991e-06, 2.3856383e-06] |
| 0.2 | 6.1646246e-07 | [3.3894432e-07, 9.3438208e-07] | 3.136873e-06 | [2.4481657e-06, 3.8699274e-06] |
| 0.3 | 2.3389665e-06 | [1.6000374e-06, 3.140395e-06] | 4.5864034e-06 | [3.591504e-06, 5.6885235e-06] |
| 0.4 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] |
| 0.5 | 7.7481403e-06 | [6.376716e-06, 9.1703425e-06] | 7.0055355e-06 | [5.472945e-06, 8.7799118e-06] |
| 0.6 | 1.2259654e-05 | [1.0296078e-05, 1.4323479e-05] | 8.3675384e-06 | [6.7635299e-06, 1.0105616e-05] |
| 0.7 | 1.8051671e-05 | [1.5841752e-05, 2.0352992e-05] | 1.4729963e-05 | [1.1510342e-05, 1.8226238e-05] |
| 0.8 | 2.7280557e-05 | [2.4676008e-05, 2.9989589e-05] | 1.8738957e-05 | [1.4490909e-05, 2.328802e-05] |

Gain U_DP/P2 lớn nhất quan sát được tại probability=0.8: **25.0416%**. Đây là cực đại trên các điểm thử,không chứng minh optimum liên tục hoặc xu hướng ngoài dải.

Mask theo p lồng nhau,nên U tối ưu DP/P2 không tăng khi p tăng;không ép gain hoặc availability đơn điệu. Ba điểm bổ sung đã định trước,không chọn theo kết quả.

### fig_B2_spatial_correlation

[PDF vector](figures/fig_B2_spatial_correlation.pdf) · [PNG 350 dpi](figures/fig_B2_spatial_correlation.png) · [CSV](figures/fig_B2_spatial_correlation_data.csv)

| Tham số | K P2 | K Greedy | K DP | U DP | D DP(m) | A P2(%) | A Greedy(%) | A DP(%) | Gain U/P2(%) | Gain U/Greedy(%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 1.5442705 | 1.5614971 | 1.5736845 | 1.5667992 | 72.721 | 99.300 | 100.000 | 100.000 | 1.4589 | 2.0593 |
| 100 | 1.5382060 | 1.5536069 | 1.5723297 | 1.5648696 | 78.792 | 99.200 | 99.933 | 100.000 | 1.7334 | 2.6839 |
| 250 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5486275 | 172.433 | 97.767 | 98.733 | 99.900 | 3.0750 | 4.4177 |
| 500 | 1.4522257 | 1.4522261 | 1.5398210 | 1.5139062 | 273.709 | 95.533 | 94.767 | 99.100 | 4.2473 | 7.5059 |
| 1000 | 1.3606864 | 1.3639389 | 1.4780582 | 1.4417695 | 383.276 | 90.867 | 89.433 | 96.000 | 5.9590 | 9.3719 |

K/U trong bảng có đơn vị10⁻⁴ bit/use. Đánh giá phương án tốt hơn bằng U;không suy availability hoặc K từng mission từ ưu thế U.

| Tham số | ΔU DP−P2 | CI95% | ΔU DP−Greedy | CI95% |
|---|---:|---|---:|---|
| 50 | 2.2528751e-06 | [1.689561e-06, 2.8517719e-06] | 3.1613661e-06 | [2.6322787e-06, 3.717164e-06] |
| 100 | 2.6663639e-06 | [1.9404511e-06, 3.4434368e-06] | 4.090165e-06 | [3.4147452e-06, 4.8026474e-06] |
| 250 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] |
| 500 | 6.168053e-06 | [4.6855618e-06, 7.7515813e-06] | 1.056984e-05 | [8.0870593e-06, 1.32583e-05] |
| 1000 | 8.1083111e-06 | [6.42814e-06, 9.8543078e-06] | 1.2354285e-05 | [9.8293528e-06, 1.5066259e-05] |

Gain U_DP/P2 lớn nhất quan sát được tại spatial=1000: **5.9590%**. Đây là cực đại trên các điểm thử,không chứng minh optimum liên tục hoặc xu hướng ngoài dải.

Tất cả dữ liệu mask ở dải ell này đã có từ trước;Stage B giữ lại để so với p và rho. Không có bảo đảm đơn điệu theo ell;đây là tương quan tiềm ẩn,không phải kích thước mây đo được.

### fig_B3_temporal_correlation

[PDF vector](figures/fig_B3_temporal_correlation.pdf) · [PNG 350 dpi](figures/fig_B3_temporal_correlation.png) · [CSV](figures/fig_B3_temporal_correlation_data.csv)

| Tham số | K P2 | K Greedy | K DP | U DP | D DP(m) | A P2(%) | A Greedy(%) | A DP(%) | Gain U/P2(%) | Gain U/Greedy(%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.1685116 | 1.4989092 | 1.5438945 | 1.4455927 | 1038.250 | 77.033 | 97.667 | 99.567 | 23.7123 | 6.5126 |
| 0.3 | 1.2121106 | 1.5009334 | 1.5496489 | 1.4680485 | 861.852 | 79.700 | 98.067 | 99.600 | 21.1151 | 6.3280 |
| 0.6 | 1.3022973 | 1.4942338 | 1.5536384 | 1.4985397 | 581.945 | 86.600 | 98.000 | 99.733 | 15.0689 | 6.5330 |
| 0.9 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5486275 | 172.433 | 97.767 | 98.733 | 99.900 | 3.0750 | 4.4177 |
| 0.98 | 1.5656339 | 1.5603351 | 1.5710778 | 1.5680628 | 31.844 | 99.967 | 99.833 | 100.000 | 0.1551 | 1.3329 |

K/U trong bảng có đơn vị10⁻⁴ bit/use. Đánh giá phương án tốt hơn bằng U;không suy availability hoặc K từng mission từ ưu thế U.

| Tham số | ΔU DP−P2 | CI95% | ΔU DP−Greedy | CI95% |
|---|---:|---|---:|---|
| 0 | 2.7708111e-05 | [2.6594486e-05, 2.8814818e-05] | 8.8388944e-06 | [7.9940438e-06, 9.6776133e-06] |
| 0.3 | 2.5593783e-05 | [2.4333955e-05, 2.6828406e-05] | 8.736932e-06 | [7.6208303e-06, 9.9194387e-06] |
| 0.6 | 1.9624245e-05 | [1.8053119e-05, 2.1186549e-05] | 9.1896154e-06 | [7.7516961e-06, 1.0713413e-05] |
| 0.9 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] |
| 0.98 | 2.4288717e-07 | [7.6081443e-08, 4.6148518e-07] | 2.0625807e-06 | [1.44806e-06, 2.7369581e-06] |

Gain U_DP/P2 lớn nhất quan sát được tại temporal=0: **23.7123%**. Đây là cực đại trên các điểm thử,không chứng minh optimum liên tục hoặc xu hướng ngoài dải.

Ở rho0→0,98,K_DP tăng 0.00015438945→0.00015710778 bit/use,U_DP tăng 0.00014455927→0.00015680628,nhưng D_DP giảm 1038.250→31.844m. Gain U_DP/P2 giảm 23.7123→0.1551%. Trong mẫu này,persistence làm một vị trí thông thoáng có thể phục vụ nhiều slot hơn và làm P2 cạnh tranh hơn;đây là cách diễn giải phù hợp dữ liệu,không phải chứng minh nhân quả riêng biệt.

Tương quan thời gian cao tạo trạng thái tồn tại lâu hơn,có thể thay đổi cả lựa chọn điểm đứng yên và nhu cầu di chuyển. Không áp đặt hướng biến thiên K,U hoặc mobility gain. Cùng seed không làm mask theo rho thành tập lồng nhau.

## Persistence: latent rho và binary correlation

| rho tiềm ẩn | τ=−20/log(rho)(s) | τ/600s | Corr Bernoulli lag1 lý thuyết | p thực nghiệm và CI95% theo mission |
|---|---:|---:|---:|---|
| 0 | 0.000 | 0.0000 | 0.000000 | 0.40187 [0.39581, 0.40793] |
| 0.3 | 16.612 | 0.0277 | 0.191039 | 0.40203 [0.39397, 0.41008] |
| 0.6 | 39.152 | 0.0653 | 0.405984 | 0.40332 [0.39158, 0.41506] |
| 0.9 | 189.824 | 0.3164 | 0.710511 | 0.41186 [0.38877, 0.43495] |
| 0.98 | 989.966 | 1.6499 | 0.871359 | 0.41871 [0.38745, 0.44998] |

Khởi tạo Z0 theo phân phối dừng,không dùng burn-in. τ biểu diễn AR Gaussian,không đồng nhất với thời gian tương quan Bernoulli hoặc thời gian mây đo được. Với rho0,98,τ lớn hơn nhiệm vụ600s;nên ảnh hưởng lựa chọn điểm đầu offline phải được giữ trong diễn giải. p danh định giữ0,4 nhưng tỷ lệ chặn hữu hạn có dao động như bảng;không ép các mẫu có cùng số slot chặn. CI ở bảng này dùng Student-t theo mission của cloud diagnostics,các hình hiệu năng dùng percentile bootstrap ghép cặp.

## Yếu tố mây có ảnh hưởng quan sát lớn nhất

| Phương án/đại lượng | Trục có span lớn nhất | Span trên dải đã thử |
|---|---|---:|
| Stationary/K | probability | 4.855393e-05 bit/use |
| Greedy/K | probability | 3.1952459e-05 bit/use |
| DP/K | probability | 1.4187471e-05 bit/use |
| DP/availability | probability | 4.0666667 percentage points |
| DP-minus-Stationary/U | temporal | 2.7465223e-05 bit/use |
| DP-minus-Greedy/U | probability | 1.694903e-05 bit/use |

Span làmax(mean)−min(mean) trên đúng dải p/ell/rho của Stage B tại λref,không phải Sobol index,elasticity hoặc so sánh được chuẩn hóa theo độ rộng tham số. Không trộn xếp hạng cloud-only này với xếp hạng năm tham số Stage A. [Bảng đầy đủ](mobility/parameter_effects.csv).

## Quãng đường và penalty

[PDF vector](figures/fig_B4_distance_penalty.pdf) · [PNG350dpi](figures/fig_B4_distance_penalty.png) · [CSV](figures/fig_B4_distance_penalty_data.csv)

Figure B4 so quãng đường tại hai λ cố định. Với cùng reward và tập khả thi,quãng đường nghiệm DP không tăng khi λ tăng. Không áp đặt điều này cho Greedy;quãng đường không phải năng lượng đẩy đã hiệu chuẩn.

## Bảo đảm,provenance và giới hạn

Baseline hiện tại được tái lập đủ600 metric/path tại100 mission×2λ×3 phương án. Bộ cuối được kiểm tra độc lập về seed/common innovations,threshold mây,calibration theo mission-cluster SE,feasible path,Greedy current-slot,Bellman,objective,CI và điểm vẽ. Không nới dung sai sau kết quả.

Các kiểm tra calibration dùng chính100 mission đã chọn:mean blockage,latent/binary near/far spatial correlation và lag1 temporal product. Dung sai định trước là5SE theo mission+10⁻¹⁰;không lấy300.000 ô/slot làm mẫu độc lập. Tỷ lệ chặn thực nghiệm hữu hạn không bị ép bằng p danh định.

Nguồn chỉ tối ưu trên catalog hữu hạn,lưới hữu hạn,mây tổng hợp,DP/P2 offline;MI2D/Holevo homodyne chưa xác thực an toàn. Không có hiệu chuẩn năng lượng hoặc transit/reacquisition. Giữ frozen hash conflict và Objective C USER_STOPPED;không thay mô hình khoa học,bảo mật,cache,frozen,lifecycle,baseline/threshold;không final-test/held-out,external manuscript edit,commit/push.

[Metric từng mission](mobility/mission_metrics.csv) · [Mean/SD/median/CI](mobility/aggregate_statistics.csv) · [Paired gains](mobility/paired_improvements.csv) · [Cloud calibration](clouds/correlation_diagnostics.csv) · [Protocol](protocol.json) · [English captions](figure_captions_en.md) · [Validation](validation_report.md) · [Final receipt](validation/final_receipt.json)
