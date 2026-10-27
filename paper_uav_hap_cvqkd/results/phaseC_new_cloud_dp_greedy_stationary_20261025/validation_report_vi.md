# So sánh DP, Greedy và Stationary với cloud Gaussian mới

**DIAGNOSTIC_ONLY — đã thực thi, primary đặt HAP trên tâm lưới theo quyết định tác giả.**

## Hình học và physical layer

Primary: HAP (500,500) m, cao 20 km; UAV cao 1 km, 100 tâm ô (50,150,…,950) m trên lưới 10×10 trong vùng 1 km². Secondary giữ nguyên HAP (11419.65511459133,450) m. Cùng covariance/cloud realizations, nguồn, objective và mobility parameters cho hai hình học. Không gán SKR ở 0° cho toàn vùng.

| Hình học | Zenith (deg) | Best raw K theo vị trí (bits/use) | Vị trí clear-sky dương | Context mới | SKR eval mới |
|---|---|---|---:|---:|---:|
| centered | 0.213231827275–1.91837812097 | 0.000786230405848 đến 0.0007959663284 | 100/100 | 14 | 2968 |
| historical | 28.8562796772–30.9208185813 | -0.00335678978588 đến -0.00265376684559 | 0/100 | 60 | 12720 |

212 payload C,w lịch sử được tái dùng (33 Uniform,179 MB), không nội suy/tính mới. Mỗi noninteger zenith được tính trực tiếp bằng evaluator v43 cũ; chỉ gộp các vị trí có geometry/angle binary64 giống hệt. Eq14, homodyne MI, Holevo, VA=2 nbar, ν_repo=42.5 ν_raw, noise và [0,1] moments/atom giữ nguyên. Dr=0.30 m, divergence35 µrad, jitter1.561 µrad, position SD0.10 m, τzen0.92, ξch0.0186, ξdet0.005, β0.95, AO/phase OFF. Best source ở primary là MB VA=1.358333319784304, ν_raw=0.30; mọi winner primary/secondary vẫn INSUFFICIENT_EVIDENCE.

## Cloud model và cấu hình nhiệm vụ

Giữ chính xác Γij=9(0.9)^|i−j|; j=10 row+column+1. Mean Uniform(-1,1) được sinh lại độc lập ở mọi ô và slot; Gaussian innovations độc lập theo slot, không có G[n−1] hoặc AR(1) trong generator mới. Zero threshold G>0 là convention được tác giả chấp nhận; không gán ngưỡng này cho tài liệu. Calibrated p dùng nghiệm tích phân mixture đã chỉ định; không ép pJ ô blocked.

30 slot ×20 s =600 s; vmax15 m/s, bước chuyển Euclid≤300 m. Di chuyển chéo được phép nếu thỏa khoảng cách, có thể ở lại, tự do chọn vị trí đầu, không deployment/terminal-return penalty. Dref=1000 m; λref=9.468026677248516e−6 bits/use. Giữ 10 λ số học lịch sử với cùng normalization, không tính lại λhigh theo map mới. U=mean(S)−λ total_distance/Dref cho cả ba thuật toán. Stationary chọn vị trí tốt nhất trên toàn mission offline; DP cũng biết toàn bộ cloud tương lai. Greedy chỉ dùng S[:,n], với reward S/Nt và penalty λd/Dref. Tie-break xác định bằng argmax đầu tiên.

## Table A — Primary, zero threshold, λref

Mỗi ô: mean ± SD [95% CI]; CI Student-t theo 100 mission độc lập, cùng mission IDs giữa mọi thuật toán. Không dùng ô/slot như các mẫu độc lập.

| Metric | Stationary | Greedy | DP |
|---|---|---|---|
| Average usable SKR (bits/use) | 0.0005580561 ± 3.69e-05 [0.0005507295, 0.0005653827] | 0.0007874697 ± 1.31e-05 [0.0007848619, 0.0007900775] | 0.0007943119 ± 9.87e-07 [0.000794116, 0.0007945078] |
| U (bits/use) | 0.0005580561 ± 3.69e-05 [0.0005507295, 0.0005653827] | 0.0007703472 ± 1.37e-05 [0.0007676278, 0.0007730666] | 0.0007839803 ± 2.45e-06 [0.0007834944, 0.0007844661] |
| Travel (m) | 0 ± 0 [0, 0] | 1808.454 ± 373 [1734.432, 1882.476] | 1091.211 ± 246 [1042.37, 1140.052] |
| Unavailability (%) | 29.63333 ± 4.69 [28.7032, 30.56347] | 0.9333333 ± 1.65 [0.606596, 1.260071] | 0 ± 0 [0, 0] |
| Availability (%) | 70.36667 ± 4.69 [69.43653, 71.2968] | 99.06667 ± 1.65 [98.73993, 99.3934] | 100 ± 0 [100, 100] |
| Position changes | 0 ± 0 [0, 0] | 14.36 ± 2.62 [13.84111, 14.87889] | 8.37 ± 1.88 [7.996219, 8.743781] |
| Algorithm runtime (ms) | 0.028889 ± 0.0176 [0.0254063, 0.03237171] | 0.229851 ± 0.0686 [0.2162485, 0.2434535] | 1.752016 ± 0.518 [1.649284, 1.854748] |

## Table A2 — Primary, calibrated p=0.4, λref

| Metric | Stationary | Greedy | DP |
|---|---|---|---|
| Average usable SKR (bits/use) | 0.0006294008 ± 3.62e-05 [0.0006222084, 0.0006365933] | 0.0007942149 ± 5.28e-06 [0.0007931667, 0.0007952631] | 0.0007946114 ± 9.75e-07 [0.0007944178, 0.0007948049] |
| U (bits/use) | 0.0006294008 ± 3.62e-05 [0.0006222084, 0.0006365933] | 0.0007814065 ± 6.44e-06 [0.0007801288, 0.0007826841] | 0.0007881015 ± 1.68e-06 [0.0007877672, 0.0007884357] |
| Travel (m) | 0 ± 0 [0, 0] | 1352.812 ± 362 [1281.05, 1424.573] | 687.5648 ± 147 [658.4362, 716.6933] |
| Unavailability (%) | 20.63333 ± 4.59 [19.72337, 21.5433] | 0.1333333 ± 0.656 [0.003071881, 0.2635948] | 0 ± 0 [0, 0] |
| Availability (%) | 79.36667 ± 4.59 [78.4567, 80.27663] | 99.86667 ± 0.656 [99.73641, 99.99693] | 100 ± 0 [100, 100] |
| Position changes | 0 ± 0 [0, 0] | 11.37 ± 2.78 [10.81832, 11.92168] | 5.51 ± 1.33 [5.246198, 5.773802] |
| Algorithm runtime (ms) | 0.027636 ± 0.0117 [0.02530659, 0.0299654] | 0.226484 ± 0.048 [0.216964, 0.236004] | 1.766022 ± 0.379 [1.690839, 1.841205] |

## Table B — Primary, calibrated p sweep, λref

Mean [95% CI] cho từng đại lượng; SD và đủ các metric nằm trong summary_comparison.csv.

| p | Algorithm | Usable K [CI] | U [CI] | Unavailability % [CI] | Distance m [CI] |
|---:|---|---|---|---|---|
| 0.1 | Stationary | 0.0007912637 [0.0007896065,0.0007929209] | 0.0007912637 [0.0007896065,0.0007929209] | 0.3666667 [0.1586771,0.5746563] | 0 [0,0] |
| 0.1 | Greedy | 0.000795892 [0.00079586,0.000795924] | 0.0007928971 [0.0007925502,0.000793244] | 0 [0,0] | 316.3137 [280.6787,351.9487] |
| 0.1 | DP | 0.0007955396 [0.0007954489,0.0007956303] | 0.0007948856 [0.0007947557,0.0007950156] | 0 [0,0] | 69.07107 [55.50281,82.63932] |
| 0.2 | Stationary | 0.0007484862 [0.000744317,0.0007526555] | 0.0007484862 [0.000744317,0.0007526555] | 5.6 [5.060947,6.139053] | 0 [0,0] |
| 0.2 | Greedy | 0.0007957116 [0.0007956421,0.0007957812] | 0.000789996 [0.0007895357,0.0007904563] | 0 [0,0] | 603.6778 [557.6795,649.6761] |
| 0.2 | DP | 0.000795215 [0.0007950552,0.0007953748] | 0.0007930188 [0.0007928168,0.0007932208] | 0 [0,0] | 231.9565 [214.0414,249.8715] |
| 0.3 | Stationary | 0.0006939925 [0.0006877676,0.0007002173] | 0.0006939925 [0.0006877676,0.0007002173] | 12.5 [11.71137,13.28863] | 0 [0,0] |
| 0.3 | Greedy | 0.0007952848 [0.0007947534,0.0007958161] | 0.0007858654 [0.0007850499,0.0007866809] | 0.03333333 [-0.03280723,0.0994739] | 994.8563 [936.7537,1052.959] |
| 0.3 | DP | 0.0007949202 [0.0007947472,0.0007950932] | 0.0007907379 [0.0007904867,0.0007909892] | 0 [0,0] | 441.7229 [414.4877,468.9581] |
| 0.4 | Stationary | 0.0006294008 [0.0006222084,0.0006365933] | 0.0006294008 [0.0006222084,0.0006365933] | 20.63333 [19.72337,21.5433] | 0 [0,0] |
| 0.4 | Greedy | 0.0007942149 [0.0007931667,0.0007952631] | 0.0007814065 [0.0007801288,0.0007826841] | 0.1333333 [0.003071881,0.2635948] | 1352.812 [1281.05,1424.573] |
| 0.4 | DP | 0.0007946114 [0.0007944178,0.0007948049] | 0.0007881015 [0.0007877672,0.0007884357] | 0 [0,0] | 687.5648 [658.4362,716.6933] |
| 0.5 | Stationary | 0.0005580561 [0.0005507295,0.0005653827] | 0.0005580561 [0.0005507295,0.0005653827] | 29.63333 [28.7032,30.56347] | 0 [0,0] |
| 0.5 | Greedy | 0.0007874697 [0.0007848619,0.0007900775] | 0.0007703472 [0.0007676278,0.0007730666] | 0.9333333 [0.606596,1.260071] | 1808.454 [1734.432,1882.476] |
| 0.5 | DP | 0.0007943119 [0.000794116,0.0007945078] | 0.0007839803 [0.0007834944,0.0007844661] | 0 [0,0] | 1091.211 [1042.37,1140.052] |
| 0.6 | Stationary | 0.0004766997 [0.0004685321,0.0004848673] | 0.0004766997 [0.0004685321,0.0004848673] | 39.86667 [38.82865,40.90468] | 0 [0,0] |
| 0.6 | Greedy | 0.0007748293 [0.000770321,0.0007793377] | 0.0007532175 [0.0007486745,0.0007577605] | 2.466667 [1.905603,3.02773] | 2282.609 [2199.545,2365.673] |
| 0.6 | DP | 0.0007937864 [0.0007931937,0.000794379] | 0.0007784961 [0.0007776968,0.0007792953] | 0.03333333 [-0.03280723,0.0994739] | 1614.942 [1549.415,1680.469] |
| 0.7 | Stationary | 0.0003926287 [0.0003842703,0.0004009872] | 0.0003926287 [0.0003842703,0.0004009872] | 50.46667 [49.40717,51.52617] | 0 [0,0] |
| 0.7 | Greedy | 0.0007388921 [0.0007316696,0.0007461145] | 0.0007128542 [0.0007058249,0.0007198836] | 6.933333 [6.028313,7.838354] | 2750.078 [2656.289,2843.867] |
| 0.7 | DP | 0.0007882031 [0.0007854546,0.0007909516] | 0.0007651729 [0.0007623264,0.0007680194] | 0.7 [0.3572247,1.042775] | 2432.42 [2337.476,2527.364] |
| 0.8 | Stationary | 0.0002955509 [0.0002882703,0.0003028314] | 0.0002955509 [0.0002882703,0.0003028314] | 62.73333 [61.81522,63.65144] | 0 [0,0] |
| 0.8 | Greedy | 0.0006641313 [0.0006521668,0.0006760958] | 0.0006363915 [0.0006248538,0.0006479291] | 16.33333 [14.83067,17.83599] | 2929.847 [2825.412,3034.281] |
| 0.8 | DP | 0.0007534568 [0.0007478938,0.0007590199] | 0.0007223878 [0.000716712,0.0007280637] | 5.066667 [4.366448,5.766885] | 3281.467 [3166.405,3396.529] |

## Table C — DP so với baseline

Delta=DP−baseline; gain dương nghĩa là tăng U/rate hoặc giảm unavailability/distance. Phần trăm dùng tỷ số của mean, không lấy trung bình các tỷ số mission. Baseline bằng 0 chỉ báo delta tuyệt đối. CI là paired mission-delta.

| Case | Baseline | Metric | Delta mean [paired 95% CI] | Gain (%) |
|---|---|---|---|---:|
| new_zero | Greedy | objective_U | 1.36330997e-05 [1.10746341e-05,1.61915653e-05] | 1.76973 |
| new_zero | Greedy | average_usable_skr | 6.84222733e-06 [4.26614368e-06,9.41831099e-06] | 0.868888 |
| new_zero | Greedy | zero_rate_unavailability | -0.00933333333 [-0.0126007067,-0.00606595994] | 100 |
| new_zero | Greedy | total_distance_m | -717.24263 [-783.824324,-650.660937] | 39.6605 |
| new_zero | Stationary | objective_U | 0.000225924222 [0.000218817969,0.000233030476] | 40.4841 |
| new_zero | Stationary | average_usable_skr | 0.00023625584 [0.000228921736,0.000243589943] | 42.3355 |
| new_zero | Stationary | zero_rate_unavailability | -0.296333333 [-0.305634674,-0.287031993] | 100 |
| new_zero | Stationary | total_distance_m | 1091.21124 [1042.37036,1140.05211] | N/A (baseline=0) |
| new_calibrated_p0.4 | Greedy | objective_U | 6.69501172e-06 [5.50954035e-06,7.88048309e-06] | 0.85679 |
| new_calibrated_p0.4 | Greedy | average_usable_skr | 3.96435294e-07 [-6.51911656e-07,1.44478224e-06] | 0.0499154 |
| new_calibrated_p0.4 | Greedy | zero_rate_unavailability | -0.00133333333 [-0.00263594786,-3.07188107e-05] | 100 |
| new_calibrated_p0.4 | Greedy | total_distance_m | -665.247009 [-730.900277,-599.593741] | 49.1751 |
| new_calibrated_p0.4 | Stationary | objective_U | 0.000158700635 [0.000151615289,0.000165785981] | 25.2146 |
| new_calibrated_p0.4 | Stationary | average_usable_skr | 0.000165210516 [0.000158018684,0.000172402349] | 26.2489 |
| new_calibrated_p0.4 | Stationary | zero_rate_unavailability | -0.206333333 [-0.215432959,-0.197233708] | 100 |
| new_calibrated_p0.4 | Stationary | total_distance_m | 687.564754 [658.436199,716.693309] | N/A (baseline=0) |
| new_calibrated_p0.8 | Greedy | objective_U | 8.59963486e-05 [7.64634876e-05,9.55292096e-05] | 13.5131 |
| new_calibrated_p0.8 | Greedy | average_usable_skr | 8.93254953e-05 [7.89522612e-05,9.96987295e-05] | 13.45 |
| new_calibrated_p0.8 | Greedy | zero_rate_unavailability | -0.112666667 [-0.125719244,-0.0996140889] | 68.9796 |
| new_calibrated_p0.8 | Greedy | total_distance_m | 351.619912 [205.515559,497.724266] | -12.0013 |
| new_calibrated_p0.8 | Stationary | objective_U | 0.000426836938 [0.000419664663,0.000434009212] | 144.421 |
| new_calibrated_p0.8 | Stationary | average_usable_skr | 0.000457905951 [0.000450511758,0.000465300145] | 154.933 |
| new_calibrated_p0.8 | Stationary | zero_rate_unavailability | -0.576666667 [-0.585996705,-0.567336629] | 91.9235 |
| new_calibrated_p0.8 | Stationary | total_distance_m | 3281.46663 [3166.4045,3396.52876] | N/A (baseline=0) |

## Primary versus Secondary và old versus new

| Geometry / model / mode | Algorithm | Usable K | U | Unavailability (%) | Travel (m) |
|---|---|---:|---:|---:|---:|
| centered/new_zero | Stationary | 0.000558056065 | 0.000558056065 | 29.6333333 | 0 |
| centered/new_zero | Greedy | 0.000787469677 | 0.000770347188 | 0.933333333 | 1808.45387 |
| centered/new_zero | DP | 0.000794311904 | 0.000783980287 | 0 | 1091.21124 |
| centered/new_calibrated_p0.4 | Stationary | 0.000629400835 | 0.000629400835 | 20.6333333 | 0 |
| centered/new_calibrated_p0.4 | Greedy | 0.000794214916 | 0.000781406458 | 0.133333333 | 1352.81176 |
| centered/new_calibrated_p0.4 | DP | 0.000794611351 | 0.00078810147 | 0 | 687.564754 |
| centered/old_p0.4 | Stationary | 0.000789704476 | 0.000789704476 | 0.5 | 0 |
| centered/old_p0.4 | Greedy | 0.000793176024 | 0.000789569945 | 0.233333333 | 380.869116 |
| centered/old_p0.4 | DP | 0.000794965896 | 0.000794225961 | 0 | 78.1509026 |
| historical/new_zero | Stationary | 0 | 0 | 100 | 0 |
| historical/new_zero | Greedy | 0 | 0 | 100 | 0 |
| historical/new_zero | DP | 0 | 0 | 100 | 0 |
| historical/new_calibrated_p0.4 | Stationary | 0 | 0 | 100 | 0 |
| historical/new_calibrated_p0.4 | Greedy | 0 | 0 | 100 | 0 |
| historical/new_calibrated_p0.4 | DP | 0 | 0 | 100 | 0 |
| historical/old_p0.4 | Stationary | 0 | 0 | 100 | 0 |
| historical/old_p0.4 | Greedy | 0 | 0 | 100 | 0 |
| historical/old_p0.4 | DP | 0 | 0 | 100 | 0 |

Secondary có raw K âm ở cả 100 vị trí; max(0,K) bằng 0 làm tất cả thuật toán có U=rate=distance=0, availability0%, unavailability100%. Đây là kết quả đúng của physical layer ở zenith gần30°, không được sửa bằng đổi noise/nguồn/frozen formula. Các kết quả secondary đã được tính trong cùng lượt này và giữ nguyên khi bổ sung primary, với chính xác cùng C và white innovations.

## Diễn giải

1. DP không thua U của Greedy hoặc Stationary ở bất kỳ instance đã kiểm tra. Đây là nghiệm hữu hạn trên lưới và cloud tương lai biết trước, không phải một bộ điều khiển online hay dự báo khí quyển đã được chứng nhận.

2. Ở p=0.4, lợi ích U của DP so Greedy là khoảng0.857%, rate chỉ khoảng0.050%, nhưng giảm khoảng49.18% quãng đường. So Stationary, U tăng khoảng25.21%. Ở p=0.8, U tăng khoảng13.51% so Greedy và unavailability giảm khoảng68.98%, đổi lại quãng đường tăng khoảng12.00%. Không suy ra DP luôn có từng metric riêng tốt nhất. Chênh lệch cũng phản ánh thông tin offline, không chỉ thuật toán.

3. Cloud mới có anisotropy theo index: ngang100m có lag1, dọc100m có lag10; row-wrap index liền nhau vẫn tương quan mạnh dù cách nhau≈905.5m. Không diễn giải là cloud có tâm/hình dạng/vận tốc đang bay qua lưới.

4. Mean và innovation sinh mới mỗi20s làm các slot độc lập theo mô hình. AR(1) cũ tạo độ bền theo thời gian, đồng thời spatial kernel cũng khác. Trong đối chiếu tổng hợp, Stationary offline ở p=0.4 đạt gần99.5% availability với model cũ, còn model mới chỉ≈79.37%; không quy toàn bộ chênh lệch riêng cho AR(1) khi hai thành phần đều đổi. DP cần nhiều di chuyển hơn dưới cloud mới. So sánh dùng cùng physical map và nominal p, không dùng lại kết quả thuật toán của các experiment cũ.

5. Lợi ích tránh outage của DP tăng rõ ở blockage cao. Tăng λ làm DP chuyển dần sang ít di chuyển; với λ lớn, DP trùng Stationary tối ưu, trong khi Greedy còn chịu giới hạn chọn vị trí ban đầu chỉ theo slot đầu. Các λ đã thử là hữu hạn, không chứng nhận tradeoff liên tục.

6. 100/100 vị trí primary có Kstar>0 trong mô hình clear-sky hiện dùng. Đây là diagnostic dựa trên catalog có sẵn và source convergence evidence còn thiếu. Missing Uniform ở VA=1.6249995399703647/nu0 vẫn chưa có; không khẳng định global modulation optimum hay unconditional QKD security.

## Threshold và kiểm chứng cloud

| Mode | Target p | Threshold | Empirical p [95% CI] |
|---|---:|---:|---|
| new_zero | 0.5 | 0 | 0.50036667 [0.49398595,0.50674738] |
| new_calibrated_p0.1 | 0.1 | 3.91554570006 | 0.0996 [0.096894509,0.10230549] |
| new_calibrated_p0.2 | 0.2 | 2.5715806717 | 0.19909667 [0.19507787,0.20311546] |
| new_calibrated_p0.3 | 0.3 | 1.60235723467 | 0.29898 [0.29371631,0.30424369] |
| new_calibrated_p0.4 | 0.4 | 0.7741380628 | 0.39970667 [0.39382901,0.40558433] |
| new_calibrated_p0.5 | 0.5 | 0 | 0.50036667 [0.49398595,0.50674738] |
| new_calibrated_p0.6 | 0.6 | -0.7741380628 | 0.60120667 [0.59492429,0.60748904] |
| new_calibrated_p0.7 | 0.7 | -1.60235723467 | 0.70109667 [0.69532059,0.70687275] |
| new_calibrated_p0.8 | 0.8 | -2.5715806717 | 0.80083 [0.79603823,0.80562177] |
| old_p0.4 | 0.4 | -0.253347103136 | 0.41186 [0.38876939,0.43495061] |

Zero threshold và calibrated p=0.4 khác nhau. Calibrated p=0.5 có t=0 nên mask trùng zero mode; hai view này được tái dùng, không tạo thêm realization độc lập. Cùng G được threshold ở mọi p; old/new ghép white innovations bằng đổi dấu nhằm ghép upper-tail mới với lower-tail cũ. Các confidence intervals giữa p/λ vì vậy có tương quan; không tuyên bố đây là các experiment độc lập với nhau.

Γ là covariance có điều kiện theo mean. Sau khi marginalize mean resampling, Cov(G)=Γ+I/3; không scale lại Γ. Audit512 missions kiểm tra cả residual G−µ so với Γ và mixture so với Γ+I/3, bằng mission-cluster SE. Max deviation lần lượt 3.69 và 3.949 SE, dưới gate6SE. Pooled Pearson audit ở zero mode:

| Variable | Direction | Empirical correlation |
|---|---|---:|
| G | horizontal | 0.8686108 |
| G | vertical | 0.33858123 |
| G | temporal | -0.0041457297 |
| binary | horizontal | 0.66916467 |
| binary | vertical | 0.21936317 |
| binary | temporal | -0.0043706249 |

Binary correlations được đo riêng, không gán bằng Gaussian correlations. Uniform-mean KS/DKW check và structural không-AR checks PASS. Full matrices/means/G/epsilon/C/S được lưu trong cloud_realizations.npz.

## Giới hạn CI và nguồn tham khảo

CI Student-t pointwise có thể vượt biên [0,1] ở rare events và được giữ nguyên trong CSV. 0 outage quan sát ở DP không chứng minh risk bằng0: với 0/100 mission bị outage, upper bound một phía95% cho xác suất một mission có ít nhất một outage là≈2.9513%. Không coi3000slot là3000 mẫu độc lập để thu hẹp bound. Xem rare_event_observations.csv. Các CI chỉ phản ánh variability synthetic-cloud giữa mission, chưa gồm source-moment uncertainty hoặc atmospheric/model uncertainty.

Canonical PDF v43 được xác nhận có3trang, chưa có subsection cloud/mobility để sửa trực tiếp. Mô hình mới được áp dụng theo yêu cầu tác giả hiện tại. FSO letter local, SectionIII/page3, nêu mean/covariance và truncation nhưng không nêu cutoff số. Reference[13] được xác nhận danh tính tại [Optica](https://opg.optica.org/jocn/abstract.cfm?uri=jocn-8-10-800); full text chưa truy cập được, nên không gán threshold0 cho tài liệu. Bản cloud_model_replacement.tex và add-file patch là proposal riêng, không chỉnh frozen manuscript, equation labels hoặc optimization problems.

## Execution summary

100 mission IDs độc lập mỗi case; 3800 mission-case views (2 geometries×19cases×100), 3600 actual algorithm-triplet executions và 200 alias views; 10800 thuật toán executions. Cùng100new-G và100old-G missions được ghépCRN; không phải3800 cloud draws độc lập. 30slots,100positions; sourcepool212; new C,w=0; new channel/SKR pairs=15688. Seed mission20261015, mission IDs0…99; auditseed20261025,512missions.

Runtime đo riêng: primary physical map 29.2414s; secondary 149.595s; MC cumulative 18.3423s; 4 focused unit tests cùng stochastic audit PASS. Live DP objective/movement failures=0. Kiểm chứng saved-record replay và artifact integrity nằm trong verification.json. Runtime là Python wall-clock phụ thuộc môi trường, không phải latency truyền thông QKD.

Tất cả8 PNG600dpi/PDF vector, bảng và trajectories ở namespace này. Không sửa production/frozen/security evaluator/caches lịch sử; strict Phase B vẫn BLOCKED, UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.

Final saved-record validation: 7.600 DP objective inequalities, 342.000 trajectory rows, all movement limits and 5.700 preserved secondary numeric records PASS. Actual primary mission0 G/mu/epsilon/C and scientific algorithm metrics replayed bit-exactly; runtime excluded from equality. Four post-geometry unit tests rerun PASS. The initial and incremental greedy/compare function ASTs match exactly.

Tổng các phase có stopwatch: 208.458470 s; đây là tổng physical maps, MC, focused tests/audit và final rendering, không phải wall-clock toàn bộ phiên: không gồm đọc/viết code, chờ quyết định, QA PDF và draft rendering đầu. Xem execution_overview.json.

Tám PDF đã mở/render/kiểm tra bằng bundled pypdfium2, pypdf, pdfplumber. Font được nhúng, text/curves/heatmaps đều vector, không image XObject raster, không ký tự vượt trang; PNG nominal600dpi. Đã kiểm tra trực quan đủ8hình và chỉnh contrast cho index labels/colorbar; không thay đổi dữ liệu.
