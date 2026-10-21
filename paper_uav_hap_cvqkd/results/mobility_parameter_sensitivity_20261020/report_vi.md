# Stage A — Phân tích độ nhạy tham số

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

Kết quả dùng P1 hiện tại (233 nguồn exact), 100 mission ghép cặp và mask đã xác thực. Chỉ tính lại P2/Greedy/DP. Không sinh mây, không tính lại kênh/SKR/C,w, không thực hiện Stage B.

Thiết kế thay đổi một tham số và so nhiều đường tham khảo Hình2–3 của [Gong et al., IEEE WCL2020](https://doi.org/10.1109/LWC.2019.2958804); không chuyển số trạm được chọn hoặc số trạm hoạt động sang mô hình một UAV.

λ dùng cố định ở mọi cấu hình: 0 và 9.468026677248516e-06 bits/use; Dref=1000m, Δt=20s. Availability là tỷ lệ S>0, không có engineering threshold. HAP/UAV, quang học, detector và nguồn giữ nguyên protocol cha. P2/DP offline, Greedy chỉ đọc slot hiện tại và biết chiều dài horizon.

| Hình | PDF | PNG | Dữ liệu vẽ |
|---|---|---|---|
| fig_A1_positions_objective_skr | [PDF](existing_data/figures/fig_A1_positions_objective_skr.pdf) | [PNG](existing_data/figures/fig_A1_positions_objective_skr.png) | [CSV](existing_data/figures/fig_A1_positions_objective_skr_data.csv) |
| fig_A2_positions_unavailability | [PDF](existing_data/figures/fig_A2_positions_unavailability.pdf) | [PNG](existing_data/figures/fig_A2_positions_unavailability.png) | [CSV](existing_data/figures/fig_A2_positions_unavailability_data.csv) |
| fig_B_speed_sensitivity | [PDF](existing_data/figures/fig_B_speed_sensitivity.pdf) | [PNG](existing_data/figures/fig_B_speed_sensitivity.png) | [CSV](existing_data/figures/fig_B_speed_sensitivity_data.csv) |
| fig_C_cloud_probability_sensitivity | [PDF](existing_data/figures/fig_C_cloud_probability_sensitivity.pdf) | [PNG](existing_data/figures/fig_C_cloud_probability_sensitivity.png) | [CSV](existing_data/figures/fig_C_cloud_probability_sensitivity_data.csv) |
| fig_D_duration_sensitivity | [PDF](existing_data/figures/fig_D_duration_sensitivity.pdf) | [PNG](existing_data/figures/fig_D_duration_sensitivity.png) | [CSV](existing_data/figures/fig_D_duration_sensitivity_data.csv) |
| fig_E_spatial_correlation_sensitivity | [PDF](existing_data/figures/fig_E_spatial_correlation_sensitivity.pdf) | [PNG](existing_data/figures/fig_E_spatial_correlation_sensitivity.png) | [CSV](existing_data/figures/fig_E_spatial_correlation_sensitivity_data.csv) |

## Thống kê và cách đọc

Mean, SD mẫu, median và CI95% dùng 100 mission, không dùng ô/slot làm mẫu độc lập. Bootstrap20.000 whole-mission resamples, seed20261020, cùng trọng số resampling giữa các cấu hình. CI pointwise chưa hiệu chỉnh nhiều so sánh; không phải CI bảo mật. Phần trăm là100×(meanDP−meanBaseline)/meanBaseline, không phải mean phần trăm từng mission. Mẫu số không hợp lệ ghi NA. Các trục performance gồm0 nên chênh nhỏ có thể khó thấy; bảng paired cho effect size và CI, không suy kết luận từ độ chồng lấn các band riêng lẻ.

## fig_A1_positions_objective_skr

Tập con được chọn chỉ từ tọa độ: bốn góc, cân bằng quadrant, maximin và tie theo global ID. Đồ thị có thể mất kết nối khi J nhỏ; đây là một phần của hiệu ứng tập lựa chọn, không được sửa bằng cạnh giả. DP/P2 U phải không giảm khi tăng J, không áp dụng bảo đảm đó cho Greedy hoặc availability.

Ở λref: DP meanK đi từ 0.00014034268 đến 0.00015649535 bits/use; meanU từ 0.0001390037 đến 0.00015486275. MeanD từ 141.42136 đến 172.43299m; availability từ 92.600000% đến 99.900000%.
DP meanK ≥ Greedy ở 6/6 điểm; mean availability ≥ Greedy ở 6/6 điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.

| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 1.3634830 | 1.0916584 | 1.4034268 | 1.3634830 | 1.0780008 | 1.3900370 | 144.249783 | 141.421356 | 92.600000 |
| 20 | 1.4212560 | 1.4233232 | 1.5311160 | 1.4212560 | 1.3697018 | 1.4976406 | 566.341822 | 353.562260 | 99.033333 |
| 40 | 1.4539255 | 1.4627126 | 1.5541791 | 1.4539255 | 1.4154181 | 1.5247383 | 499.518063 | 310.949230 | 99.700000 |
| 60 | 1.4748214 | 1.4968266 | 1.5591142 | 1.4748214 | 1.4511513 | 1.5361193 | 482.416036 | 242.869116 | 99.766667 |
| 80 | 1.4909835 | 1.5120436 | 1.5641728 | 1.4909835 | 1.4697602 | 1.5448054 | 446.591707 | 204.555407 | 99.833333 |
| 100 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5024282 | 1.4831088 | 1.5486275 | 430.610183 | 172.432990 | 99.900000 |

K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.

| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |
|---|---|---|---|---|---|---|
| 10 | 2.6554001e-06 | [1.5675885e-06, 3.9054579e-06] | 1.9475124 | 3.1203624e-05 | [2.4577997e-05, 3.8018642e-05] | 28.945827 |
| 20 | 7.6384588e-06 | [5.9785197e-06, 9.4289964e-06] | 5.3744426 | 1.2793882e-05 | [9.9694378e-06, 1.5803828e-05] | 9.340633 |
| 40 | 7.0812836e-06 | [5.4989404e-06, 8.8167006e-06] | 4.8704584 | 1.0932026e-05 | [8.3962066e-06, 1.3669276e-05] | 7.7235311 |
| 60 | 6.1297871e-06 | [4.8020507e-06, 7.5601405e-06] | 4.1562911 | 8.4967922e-06 | [6.3328169e-06, 1.0851505e-05] | 5.8552074 |
| 80 | 5.3821921e-06 | [4.1789714e-06, 6.6544345e-06] | 3.6098267 | 7.5045198e-06 | [5.61306e-06, 9.7377753e-06] | 5.1059484 |
| 100 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 3.0749782 | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] | 4.4176593 |

CI meanΔU dương nghiêm ngặt so với P2 ở các điểm [10, 20, 40, 60, 80, 100]; so với Greedy ở [10, 20, 40, 60, 80, 100]. Điểm không có CI dương không được mô tả là gain dương chắc chắn.

Trend meanU tại λref: DP có 5 đoạn tăng, 0 đoạn giảm và 0 đoạn hòa; Greedy tương ứng 5, 0, 0. Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.

J=10 có 8 thành phần liên thông và 7 điểm cô lập; từ J=20 đồ thị đã liên thông. Do đó mức tăng ban đầu gồm cả khả năng tiếp cận vị trí và spatial diversity. J=20 đạt 96.707605% meanU tại J=100. Các mức J lớn vẫn cải thiện nhưng không được gọi là optimum J phổ quát; chi phí tăng mật độ vị trí chưa được đưa vào mục tiêu.

## fig_B_speed_sensitivity

Tốc độ0 và2,5m/s đều không cho phép bước sang ô khác;5m/s bắt đầu cho bước100m. DP có điểm đầu tự chọn nên bằng P2 khi không di chuyển. Greedy có thể khác P2 vì chọn theo slot đầu. Chỉ U_DP được bảo đảm không giảm khi nới tốc độ; tại λ>0 không bảo đảm K hoặc D đơn điệu.

Ở λref: DP meanK đi từ 0.00015024282 đến 0.00015658451 bits/use; meanU từ 0.00015024282 đến 0.00015491192. MeanD từ 0 đến 176.65644m; availability từ 97.766667% đến 99.933333%.
DP meanK ≥ Greedy ở 8/8 điểm; mean availability ≥ Greedy ở 8/8 điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.

| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.5024282 | 0.9944699 | 1.5024282 | 1.5024282 | 0.9944699 | 1.5024282 | 0.000000 | 0.000000 | 97.766667 |
| 2.5 | 1.5024282 | 0.9944699 | 1.5024282 | 1.5024282 | 0.9944699 | 1.5024282 | 0.000000 | 0.000000 | 97.766667 |
| 5 | 1.5024282 | 1.3545720 | 1.5567906 | 1.5024282 | 1.3328902 | 1.5423046 | 229.000000 | 153.000000 | 99.700000 |
| 7.5 | 1.5024282 | 1.4248224 | 1.5610726 | 1.5024282 | 1.3989926 | 1.5460431 | 272.811183 | 158.740115 | 99.733333 |
| 10 | 1.5024282 | 1.4819779 | 1.5624546 | 1.5024282 | 1.4495434 | 1.5470598 | 342.568542 | 162.597980 | 99.766667 |
| 15 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5024282 | 1.4831088 | 1.5486275 | 430.610183 | 172.432990 | 99.900000 |
| 20 | 1.5024282 | 1.5321420 | 1.5658021 | 1.5024282 | 1.4904712 | 1.5490119 | 440.121206 | 177.335786 | 99.933333 |
| 25 | 1.5024282 | 1.5397239 | 1.5658451 | 1.5024282 | 1.4966233 | 1.5491192 | 455.222182 | 176.656444 | 99.933333 |

K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.

| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |
|---|---|---|---|---|---|---|
| 0 | 0 | [0, 0] | 0 | 5.0795826e-05 | [4.3258911e-05, 5.8524465e-05] | 51.078293 |
| 2.5 | 0 | [0, 0] | 0 | 5.0795826e-05 | [4.3258911e-05, 5.8524465e-05] | 51.078293 |
| 5 | 3.9876372e-06 | [3.0380451e-06, 4.9713734e-06] | 2.6541283 | 2.0941435e-05 | [1.6102115e-05, 2.6023098e-05] | 15.711297 |
| 7.5 | 4.3614877e-06 | [3.3361221e-06, 5.4445822e-06] | 2.9029592 | 1.4705047e-05 | [1.1186661e-05, 1.8535335e-05] | 10.511169 |
| 10 | 4.4631602e-06 | [3.4316955e-06, 5.5478177e-06] | 2.9706313 | 9.7516385e-06 | [7.2659984e-06, 1.244949e-05] | 6.7273864 |
| 15 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 3.0749782 | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] | 4.4176593 |
| 20 | 4.6583734e-06 | [3.595182e-06, 5.7770202e-06] | 3.1005631 | 5.854072e-06 | [4.7071975e-06, 7.1078276e-06] | 3.9276653 |
| 25 | 4.6691052e-06 | [3.601187e-06, 5.7893356e-06] | 3.1077061 | 5.2495923e-06 | [4.3684387e-06, 6.1893005e-06] | 3.5076243 |

CI meanΔU dương nghiêm ngặt so với P2 ở các điểm [5, 7.5, 10, 15, 20, 25]; so với Greedy ở [0, 2.5, 5, 7.5, 10, 15, 20, 25]. Điểm không có CI dương không được mô tả là gain dương chắc chắn.

Trend meanU tại λref: DP có 6 đoạn tăng, 0 đoạn giảm và 1 đoạn hòa; Greedy tương ứng 6, 0, 1. Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.

Từ15 lên25m/s, meanU DP chỉ tăng 0.031752%. MeanD DP từ20 lên25m/s đổi 177.33579→176.65644m: tốc độ tối đa cao hơn không bắt buộc đi dài hơn. Ở v=0, gainU DP−Greedy là 51.078293%, trong khi DP=P2 và cả hai đứng yên; đây là lợi thế chọn điểm đầu offline, không phải lợi ích di chuyển. Gain mobility được đọc bằng DP−P2.

## fig_C_cloud_probability_sensitivity

Chỉ dùng năm mức đã lưu; không có0,3/0,5/0,7. Giữ ell250m và latent rho0,9 với common innovations. Binary correlation sau threshold có thể thay đổi theo p. Mask lồng nhau cho phép kiểm tra U_DP/P2 không tăng theo p; không ép Greedy hoặc availability có cùng tính chất. Gain phần trăm lớn cần đọc cùng gain tuyệt đối và baseline.

Ở λref: DP meanK đi từ 0.00015766271 đến 0.00014347523 bits/use; meanU từ 0.0001576059 đến 0.00013622131. MeanD từ 6 đến 766.14962m; availability từ 100.000000% đến 95.933333%.
DP meanK ≥ Greedy ở 5/5 điểm; mean availability ≥ Greedy ở 5/5 điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.

| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |
|---|---|---|---|---|---|---|---|---|---|
| 0.1 | 1.5749468 | 1.5675060 | 1.5766271 | 1.5749468 | 1.5581597 | 1.5760590 | 98.714777 | 6.000000 | 100.000000 |
| 0.2 | 1.5649826 | 1.5599774 | 1.5744672 | 1.5649826 | 1.5397785 | 1.5711473 | 213.337815 | 35.064495 | 100.000000 |
| 0.4 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5024282 | 1.4831088 | 1.5486275 | 430.610183 | 172.432990 | 99.900000 |
| 0.6 | 1.3767707 | 1.4746602 | 1.5371783 | 1.3767707 | 1.4156919 | 1.4993672 | 622.815872 | 399.355650 | 99.466667 |
| 0.8 | 1.0894075 | 1.2479814 | 1.4347523 | 1.0894075 | 1.1748235 | 1.3622131 | 772.684036 | 766.149619 | 95.933333 |

K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.

| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |
|---|---|---|---|---|---|---|
| 0.1 | 1.112154e-07 | [2.1924495e-08, 2.3312888e-07] | 0.070615339 | 1.7899274e-06 | [1.2463991e-06, 2.3856383e-06] | 1.1487445 |
| 0.2 | 6.1646246e-07 | [3.3894432e-07, 9.3438208e-07] | 0.39391009 | 3.136873e-06 | [2.4481657e-06, 3.8699274e-06] | 2.0372235 |
| 0.4 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 3.0749782 | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] | 4.4176593 |
| 0.6 | 1.2259654e-05 | [1.0296078e-05, 1.4323479e-05] | 8.9046451 | 8.3675384e-06 | [6.7635299e-06, 1.0105616e-05] | 5.9105648 |
| 0.8 | 2.7280557e-05 | [2.4676008e-05, 2.9989589e-05] | 25.041645 | 1.8738957e-05 | [1.4490909e-05, 2.328802e-05] | 15.950444 |

CI meanΔU dương nghiêm ngặt so với P2 ở các điểm [0.1, 0.2, 0.4, 0.6, 0.8]; so với Greedy ở [0.1, 0.2, 0.4, 0.6, 0.8]. Điểm không có CI dương không được mô tả là gain dương chắc chắn.

Trend meanU tại λref: DP có 0 đoạn tăng, 4 đoạn giảm và 0 đoạn hòa; Greedy tương ứng 0, 4, 0. Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.

Ở p=0,8, meanU DP cao hơn P2 25.041645% và Greedy 15.950444%. Trong năm mức đã thử, gain lớn nhất nằm ở biên p=0,8; chưa quan sát một đỉnh nội miền hoặc ngưỡng mây làm mobility mất tác dụng. Không ngoại suy sang p>0,8 và không tạo các điểm0,3/0,5/0,7.

## fig_D_duration_sensitivity

Mỗi điểm dùng prefix mây thật và được tối ưu lại, không cắt đường30slot. Giữ U=meanS−λD/1000 và Greedy dùng Ntλ. Khi Nt đổi, hiệu ứng bao gồm horizon và mức phạt tương đối với average reward, không cô lập riêng lợi ích lookahead; không áp đặt đơn điệu theo Nt hoặc bảo đảm online.

Ở λref: DP meanK đi từ 0.0001572523 đến 0.00015649535 bits/use; meanU từ 0.00015713415 đến 0.00015486275. MeanD từ 12.478709 đến 172.43299m; availability từ 100.000000% đến 99.900000%.
DP meanK ≥ Greedy ở 6/6 điểm; mean availability ≥ Greedy ở 6/6 điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.

| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1.5699041 | 1.5524113 | 1.5725230 | 1.5699041 | 1.5453922 | 1.5713415 | 74.135563 | 12.478709 | 100.000000 |
| 10 | 1.5609322 | 1.5405727 | 1.5711743 | 1.5609322 | 1.5260804 | 1.5674748 | 153.065737 | 39.073262 | 100.000000 |
| 15 | 1.5466963 | 1.5339426 | 1.5686290 | 1.5466963 | 1.5123579 | 1.5622426 | 227.973999 | 67.451466 | 99.933333 |
| 20 | 1.5304755 | 1.5292349 | 1.5674402 | 1.5304755 | 1.5016281 | 1.5575716 | 291.579504 | 104.230737 | 99.900000 |
| 25 | 1.5186578 | 1.5256286 | 1.5664596 | 1.5186578 | 1.4915382 | 1.5529072 | 360.058212 | 143.138999 | 99.920000 |
| 30 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5024282 | 1.4831088 | 1.5486275 | 430.610183 | 172.432990 | 99.900000 |

K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.

| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |
|---|---|---|---|---|---|---|
| 5 | 1.4373417e-07 | [3.9994492e-08, 2.6860255e-07] | 0.091556016 | 2.5949322e-06 | [9.0164779e-07, 4.9286523e-06] | 1.6791415 |
| 10 | 6.5426879e-07 | [3.4520426e-07, 1.0078563e-06] | 0.41915262 | 4.1394421e-06 | [2.1498456e-06, 6.792772e-06] | 2.7124665 |
| 15 | 1.5546319e-06 | [9.6298245e-07, 2.2127501e-06] | 1.0051306 | 4.9884706e-06 | [3.1344004e-06, 7.5151726e-06] | 3.2984722 |
| 20 | 2.7096078e-06 | [1.8924849e-06, 3.5975814e-06] | 1.7704353 | 5.5943487e-06 | [3.9118592e-06, 7.8813032e-06] | 3.7255222 |
| 25 | 3.4249362e-06 | [2.4479884e-06, 4.4853382e-06] | 2.2552389 | 6.1369016e-06 | [4.450305e-06, 8.2637324e-06] | 4.1144784 |
| 30 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 3.0749782 | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] | 4.4176593 |

CI meanΔU dương nghiêm ngặt so với P2 ở các điểm [5, 10, 15, 20, 25, 30]; so với Greedy ở [5, 10, 15, 20, 25, 30]. Điểm không có CI dương không được mô tả là gain dương chắc chắn.

Trend meanU tại λref: DP có 0 đoạn tăng, 5 đoạn giảm và 0 đoạn hòa; Greedy tương ứng 0, 5, 0. Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.

GainU DP/P2 tăng từ 0.091556016% ở5slot lên 3.0749782% ở30slot, dù meanK/U tuyệt đối của DP giảm. P2 phải tìm một điểm phù hợp cho nhiều slot hơn, trong khi DP được đổi vị trí; cách diễn giải này phù hợp với kết quả nhưng không cô lập hiệu ứng thông tin tương lai khỏi chuẩn hóa Nt và các prefix khác nhau.

## fig_E_spatial_correlation_sensitivity

Các ell50–1000m đã có sẵn, tương ứng0,5–10 lần khoảng cách ô100m. Trục x logarithmic giữ đủ5 điểm đã tính, tránh chồng nhãn50/100m; không thêm điểm mô phỏng. Giữ p0,4 và latent rho0,9. Không có bảo đảm đơn điệu theo ell; common innovations không làm các mask theo ell trở thành tập lồng nhau. Đây là chiều dài tương quan tiềm ẩn, không phải bán kính mây đo được.

Ở λref: DP meanK đi từ 0.00015736845 đến 0.00014780582 bits/use; meanU từ 0.00015667992 đến 0.00014417695. MeanD từ 72.721349 đến 383.27581m; availability từ 100.000000% đến 96.000000%.
DP meanK ≥ Greedy ở 5/5 điểm; mean availability ≥ Greedy ở 5/5 điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.

| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 1.5442705 | 1.5614971 | 1.5736845 | 1.5442705 | 1.5351856 | 1.5667992 | 277.898543 | 72.721349 | 100.000000 |
| 100 | 1.5382060 | 1.5536069 | 1.5723297 | 1.5382060 | 1.5239679 | 1.5648696 | 313.042873 | 78.792417 | 100.000000 |
| 250 | 1.5024282 | 1.5238791 | 1.5649535 | 1.5024282 | 1.4831088 | 1.5486275 | 430.610183 | 172.432990 | 99.900000 |
| 500 | 1.4522257 | 1.4522261 | 1.5398210 | 1.4522257 | 1.4082079 | 1.5139062 | 464.915135 | 273.708504 | 99.100000 |
| 1000 | 1.3606864 | 1.3639389 | 1.4780582 | 1.3606864 | 1.3182267 | 1.4417695 | 482.805863 | 383.275815 | 96.000000 |

K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.

| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |
|---|---|---|---|---|---|---|
| 50 | 2.2528751e-06 | [1.689561e-06, 2.8517719e-06] | 1.4588604 | 3.1613661e-06 | [2.6322787e-06, 3.717164e-06] | 2.0592729 |
| 100 | 2.6663639e-06 | [1.9404511e-06, 3.4434368e-06] | 1.7334245 | 4.090165e-06 | [3.4147452e-06, 4.8026474e-06] | 2.6838918 |
| 250 | 4.6199339e-06 | [3.5650268e-06, 5.7313908e-06] | 3.0749782 | 6.5518695e-06 | [4.9897767e-06, 8.4622842e-06] | 4.4176593 |
| 500 | 6.168053e-06 | [4.6855618e-06, 7.7515813e-06] | 4.2473101 | 1.056984e-05 | [8.0870593e-06, 1.32583e-05] | 7.5058803 |
| 1000 | 8.1083111e-06 | [6.42814e-06, 9.8543078e-06] | 5.9589859 | 1.2354285e-05 | [9.8293528e-06, 1.5066259e-05] | 9.3718976 |

CI meanΔU dương nghiêm ngặt so với P2 ở các điểm [50, 100, 250, 500, 1000]; so với Greedy ở [50, 100, 250, 500, 1000]. Điểm không có CI dương không được mô tả là gain dương chắc chắn.

Trend meanU tại λref: DP có 0 đoạn tăng, 4 đoạn giảm và 0 đoạn hòa; Greedy tương ứng 0, 4, 0. Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.

Trong dữ liệu này, meanU DP giảm khi ell tăng nhưng gain tuyệt đối DP−P2 tăng 2.2528751e-06→8.1083111e-06 bits/use và gain tương đối tăng 1.4588604→5.9589859%. Kết quả không hỗ trợ kết luận rằng tương quan lớn hơn luôn làm gain mobility nhỏ hơn: baseline P2 giảm mạnh hơn DP trong dải này. Đây là kết quả có điều kiện, không phải một định luật đơn điệu theo ell.

## fig_A2_positions_unavailability

HìnhA2 dùng cùng tập J nhưng đo zero-SKR unavailability. Đây không phải mục tiêu tối ưu, vì vậy không suy thứ tự availability từ thứ tự objective. Các giá trị0 được giữ đúng, không đổi thành epsilon để vẽ log.

| J | P2 λ0 (%) | Greedy λ0 (%) | DP λ0 (%) | P2 λref (%) | Greedy λref (%) | DP λref (%) |
|---|---|---|---|---|---|---|
| 10 | 9.4666667 | 29.9333333 | 7.1666667 | 9.4666667 | 29.5666667 | 7.4000000 |
| 20 | 5.6666667 | 6.3666667 | 0.4666667 | 5.6666667 | 6.9666667 | 0.9666667 |
| 40 | 4.6000000 | 5.0333333 | 0.1000000 | 4.6000000 | 4.6000000 | 0.3000000 |
| 60 | 3.4666667 | 2.3333333 | 0.0666667 | 3.4666667 | 2.7666667 | 0.2333333 |
| 80 | 2.5333333 | 1.6333333 | 0.0000000 | 2.5333333 | 2.2000000 | 0.1666667 |
| 100 | 2.2333333 | 1.4333333 | 0.0000000 | 2.2333333 | 1.2666667 | 0.1000000 |

## Tham số có ảnh hưởng quan sát lớn nhất

So sánh span=max(mean)−min(mean) trên đúng dải đã duyệt, tại λref. Các dải và đơn vị tham số khác nhau nên đây là xếp hạng mô tả có điều kiện, không phải elasticity, Sobol index hoặc chứng minh nguyên nhân phổ quát.

| Đại lượng | Tham số có span lớn nhất | Span | Điểm min → max |
|---|---|---|---|
| SKR | số vị trí J | 1.6152669e-05 bits/use | 10 → 100 |
| availability | số vị trí J | 7.3 percentage points | 10 → 100 |
| mobility_gain_vs_P2 | xác suất chặn | 2.7169341e-05 bits/use | 0.1 → 0.8 |
| gain_vs_Greedy | tốc độ tối đa | 4.5546234e-05 bits/use | 25 → 0 |

Xếp hạng phụ thuộc phương án; không gộp kết quả DP thành kết luận chung cho mọi thuật toán.

| Phương án | Tham số ảnh hưởng meanK mạnh nhất | Span K (bits/use) | Tham số ảnh hưởng availability mạnh nhất | Span (pp) |
|---|---|---|---|---|
| Stationary | xác suất chặn | 4.855393e-05 | xác suất chặn | 24.600000 |
| Greedy | tốc độ tối đa | 5.4525395e-05 | tốc độ tối đa | 36.700000 |
| DP | số vị trí J | 1.6152669e-05 | số vị trí J | 7.300000 |

Toàn bộ span của các phương án/metric: [parameter_effects.csv](existing_data/parameter_effects.csv). Gain biên theo J và CI: [J_incremental_gains.csv](existing_data/J_incremental_gains.csv). Không gọi một vùng là bão hòa chỉ vì CI của incremental gain chứa0.

## Bốn hình ưu tiên và giới hạn

**A1, A2, B, C** theo ưu tiên đã chốt trước batch: số lựa chọn và objective; outage dọc đường; ràng buộc tốc độ; mức độ mây. D/E bổ sung cơ chế horizon và spatial diversity. Không chọn lại seed, dải tham số hoặc λ sau khi thấy kết quả.

Đây là finite-catalog/grid synthetic manuscript comparison. Giữ P1 tại233 nguồn, không phải optimum nguồn liên tục; MI2D ghép Holevo homodyne chưa được xác thực an toàn lượng tử. P2/DP có thông tin toàn horizon, Greedy là current-slot oracle; không có common-information ablation. Khoảng cách chưa là năng lượng; chưa có transit/reacquisition hay số bit vật lý. Frozen hash discrepancy và Objective C USER_STOPPED giữ nguyên. Không Stage B, final-test/held-out, nâng lifecycle, external edit, commit/push.

## Dữ liệu và xác minh

[Protocol](protocol.json) · [Nguồn đầu vào](input_manifest.json) · [Metric từng mission](existing_data/mission_metrics.csv) · [Mean/SD/median/CI](existing_data/aggregate_statistics.csv) · [Paired gains](existing_data/paired_improvements.csv) · [Baseline10λ](validation/baseline_reproduction.csv) · [Captions](figure_captions_en.md) · [Source map](figure_source_mapping.csv) · [Validation](validation_report.md) · [Receipt](validation/final_receipt.json)
