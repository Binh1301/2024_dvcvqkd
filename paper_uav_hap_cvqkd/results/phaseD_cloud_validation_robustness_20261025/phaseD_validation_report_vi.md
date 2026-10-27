# PHASE D RESULT: COMPLETE

**DIAGNOSTIC_ONLY; PHASE_B_STRICT_READY = FALSE.** Hoàn tất các kiểm tra và
phân tích được yêu cầu, không đồng nghĩa có chứng chỉ hội tụ nguồn hoặc bảo mật.
Thực thi ngày 26/10/2026; giữ tên namespace 20261025 đúng yêu cầu.

## Baseline được bảo toàn

Tái dựng đủ 912 dòng summary từ 11.400 bản ghi theo mission của Phase C:
sai khác lớn nhất của mean/SD/SE/CI và các bảng B, primary–secondary đều bằng 0.
Không chạy lại các mission hoặc bản đồ physical layer của thí nghiệm gốc.
Primary: HAP (500,500) m, zenith 0.213–1.918°, 100/100 vị trí clear-sky dương.
Secondary: HAP (11419.65511459133,450) m, zenith 28.856–30.921°, 0/100 dương.
Giữ 100 mission, 30 slot × 20 s, 15 m/s, bước Euclidean tối đa 300 m,
Dref=1000 m và lambda_ref=9.468026677248516e-6 bits/use.
Nguồn, bản đồ SKR và normalization giữ nguyên.

## A. Cloud model validation

Covariance có điều kiện bằng Gamma, vô điều kiện bằng Gamma+I/3;
đường chéo tương ứng bằng 9 và 28/3. Ma trận đối xứng, xác định dương;
Cholesky reconstruction PASS. Max standardized entry errors lần lượt
3.4073 và 3.5825 SE theo cụm mission trên 100 mission đã lưu, dưới ngưỡng
chẩn đoán 6 SE. Đây không phải chứng nhận đồng thời mọi phần tử covariance.

Đã đo temporal lag 1, 2, 5, 10 cho G, epsilon, mu và binary. Không có AR
hoặc mean chung cố định trong generator. G lag 1=-0.0112914 có CI 95% riêng
[-0.0223837,-0.0001990], hơi tách khỏi 0. Khoảng Bonferroni 95% cho nhóm
16 kiểm tra chứa 0; điều này đúng với cả 16 kiểm tra. Giữ nguyên quan sát
hữu hạn mẫu, không ép correlation thực nghiệm bằng 0.

Threshold được xác minh độc lập bằng nguyên hàm ở 80 chữ số; sai khác
calibration nhỏ hơn 1e-12. Zero threshold có xác suất biên lý thuyết 0.5.
Binary spatial correlation được kiểm tra bằng tích phân Plackett cho mixture:
ở p=0.5, lag 1 có residual-Gaussian rho=0.9, mixture-G rho=0.867857,
binary rho≈0.668078; lag 10 tương ứng là 0.348678, 0.336226, 0.218207.
Cặp index 9→10 khi sang hàng vẫn có lag 1 dù cách nhau khoảng 905.5 m.
Xem cloud_mathematical_validation.md và CSV để có CI/sai số đầy đủ.

## B. Algorithm robustness

Baseline zero threshold (p=0.5), mean [CI 95% theo mission]:

| Metric | Stationary | Greedy | DP |
|---|---|---|---|
| average_usable_skr | 0.000558056065 [0.000550729469,0.00056538266] | 0.000787469677 [0.000784861855,0.000790077499] | 0.000794311904 [0.000794115995,0.000794507814] |
| objective_U | 0.000558056065 [0.000550729469,0.00056538266] | 0.000770347188 [0.00076762779,0.000773066586] | 0.000783980287 [0.000783494425,0.00078446615] |
| zero_rate_unavailability | 0.296333333 [0.287031993,0.305634674] | 0.00933333333 [0.00606595994,0.0126007067] | 0 [0,0] |
| total_distance_m | 0 [0,0] | 1808.45387 [1734.43152,1882.47621] | 1091.21124 [1042.37036,1140.05211] |

Phân tích paired dùng 100 mission; không coi 30 slot/mission là 30 mẫu độc lập.
CI Student-t paired là kiểm tra chính; 10.000 bootstrap paired dùng để đối chiếu.
Đây là CI riêng cho từng đại lượng, chưa điều chỉnh đồng thời mọi metric.
Tỷ số các mean dùng đúng chiều tăng U/K hoặc giảm distance/unavailability;
baseline bằng 0 thì báo delta tuyệt đối. Bootstrap tỷ số loại các replicate
có mẫu số bằng 0 và báo số replicate hợp lệ, không tạo tỷ số vô hạn.

Tại p=0.4, delta mean K của DP−Greedy bằng 3.96435e-7; CI paired t 95%
[-6.51912e-7,1.44478e-6],bootstrap[-4.95137e-7,1.52006e-6]:
**lợi ích 0.0499% chưa phân biệt với 0**, không gọi là mức tăng rate đáng kể.
Delta U=6.69501e-6, CI [5.50954e-6,7.88048e-6]; mức giảm quãng đường
665.247 m, CI [599.594,730.900] m: hai lợi ích này rõ trong mẫu đã thử.

Tại p=0.8, U tăng 13.5131%, K tăng 13.4500%, unavailability giảm 68.9796%,
distance tăng 12.0013%. Cả CI paired t và bootstrap cho delta U, delta K,
unavailability và distance đều tách khỏi 0. Đây là đánh đổi tăng di chuyển
để né outage. DP biết mây tương lai offline, Greedy chỉ biết slot hiện tại:
không tách được lợi ích thông tin oracle khỏi phần còn lại của khác biệt.

DP zero mode quan sát 0 slot zero-rate/3000 và 0/100 mission có outage.
Cận trên một phía 95% cho xác suất một mission có ít nhất một outage là
2.9513%. Không dùng giả định 3000 slot độc lập để tạo cận hẹp giả.
Không quan sát outage không có nghĩa xác suất thực bằng 0.

| p | Baseline | Metric | Delta mean [paired t95%CI] | Paired bootstrap95%CI | Gain % |
|---|---|---|---|---|---|
| 0.4 | Greedy | average_usable_skr | 3.96435294e-07 [-6.51911656e-07,1.44478224e-06] | [-4.95136828e-07,1.52005867e-06] | 0.0499153675 |
| 0.4 | Greedy | objective_U | 6.69501172e-06 [5.50954035e-06,7.88048309e-06] | [5.64524815e-06,7.96514756e-06] | 0.856789914 |
| 0.4 | Greedy | zero_rate_unavailability | -0.00133333333 [-0.00263594786,-3.07188107e-05] | [-0.00266666667,-0.000333333333] | 100 |
| 0.4 | Greedy | total_distance_m | -665.247009 [-730.900277,-599.593741] | [-731.690772,-602.306551] | 49.1751349 |
| 0.4 | Greedy | position_changes | -5.86 [-6.38004244,-5.33995756] | [-6.38,-5.36] | 51.5391381 |
| 0.4 | Stationary | average_usable_skr | 0.000165210516 [0.000158018684,0.000172402349] | [0.00015795893,0.000172094194] | 26.2488556 |
| 0.4 | Stationary | objective_U | 0.000158700635 [0.000151615289,0.000165785981] | [0.00015153941,0.000165479286] | 25.2145574 |
| 0.4 | Stationary | zero_rate_unavailability | -0.206333333 [-0.215432959,-0.197233708] | [-0.215,-0.197] | 100 |
| 0.4 | Stationary | total_distance_m | 687.564754 [658.436199,716.693309] | [658.580584,715.925599] | N/A baseline=0 |
| 0.4 | Stationary | position_changes | 5.51 [5.24619795,5.77380205] | [5.25,5.77] | N/A baseline=0 |
| 0.5 | Greedy | average_usable_skr | 6.84222733e-06 [4.26614368e-06,9.41831099e-06] | [4.40175748e-06,9.45911914e-06] | 0.868887721 |
| 0.5 | Greedy | objective_U | 1.36330997e-05 [1.10746341e-05,1.61915653e-05] | [1.12028905e-05,1.62566651e-05] | 1.76973447 |
| 0.5 | Greedy | zero_rate_unavailability | -0.00933333333 [-0.0126007067,-0.00606595994] | [-0.0126666667,-0.00633333333] | 100 |
| 0.5 | Greedy | total_distance_m | -717.24263 [-783.824324,-650.660937] | [-781.81042,-652.863444] | 39.6605434 |
| 0.5 | Greedy | position_changes | -5.99 [-6.53211427,-5.44788573] | [-6.52,-5.45] | 41.7130919 |
| 0.5 | Stationary | average_usable_skr | 0.00023625584 [0.000228921736,0.000243589943] | [0.000229053735,0.000243520357] | 42.3355026 |
| 0.5 | Stationary | objective_U | 0.000225924222 [0.000218817969,0.000233030476] | [0.000218978348,0.000232997593] | 40.4841443 |
| 0.5 | Stationary | zero_rate_unavailability | -0.296333333 [-0.305634674,-0.287031993] | [-0.305666667,-0.287333333] | 100 |
| 0.5 | Stationary | total_distance_m | 1091.21124 [1042.37036,1140.05211] | [1043.25623,1137.96554] | N/A baseline=0 |
| 0.5 | Stationary | position_changes | 8.37 [7.99621935,8.74378065] | [8,8.73] | N/A baseline=0 |
| 0.8 | Greedy | average_usable_skr | 8.93254953e-05 [7.89522612e-05,9.96987295e-05] | [7.91329179e-05,9.95584517e-05] | 13.4499745 |
| 0.8 | Greedy | objective_U | 8.59963486e-05 [7.64634876e-05,9.55292096e-05] | [7.65612663e-05,9.54777975e-05] | 13.5131209 |
| 0.8 | Greedy | zero_rate_unavailability | -0.112666667 [-0.125719244,-0.0996140889] | [-0.125666667,-0.0996666667] | 68.9795918 |
| 0.8 | Greedy | total_distance_m | 351.619912 [205.515559,497.724266] | [210.503037,494.960123] | -12.0013074 |
| 0.8 | Greedy | position_changes | 0.45 [-0.208618869,1.10861887] | [-0.2,1.09] | -2.45901639 |
| 0.8 | Stationary | average_usable_skr | 0.000457905951 [0.000450511758,0.000465300145] | [0.000450563972,0.00046519416] | 154.933037 |
| 0.8 | Stationary | objective_U | 0.000426836938 [0.000419664663,0.000434009212] | [0.000419810051,0.000433869536] | 144.420798 |
| 0.8 | Stationary | zero_rate_unavailability | -0.576666667 [-0.585996705,-0.567336629] | [-0.586,-0.567333333] | 91.9234857 |
| 0.8 | Stationary | total_distance_m | 3281.46663 [3166.4045,3396.52876] | [3170.60067,3399.56822] | N/A baseline=0 |
| 0.8 | Stationary | position_changes | 18.75 [18.305532,19.194468] | [18.32,19.19] | N/A baseline=0 |

## C. Indexing sensitivity

Năm mapping: Row, Column, Serpentine, Random_A (seed 20261026), Random_B
(seed 20261027). Mỗi mapping dùng 100 mission và p=0.4,0.5,0.8, giữ nguyên
vị trí, Kstar, lambda, tốc độ và objective. Trường latent theo label của
Phase C được permutation chính xác sang ô vật lý; Gamma vẫn bằng
9*.9**abs(label_i-label_j). Đây là coupling của cùng 100 base draw,
không phải các dataset độc lập mới.

Row/Column là hai biểu diễn đối xứng qua transpose; K và distance bất biến
chính xác. DP và Stationary có objective bằng nhau bit-exact ở 300 instance
ghép. Greedy phá hòa bằng physical index đầu tiên nên không equivariant.
300 kiểm tra riêng với thứ tự phá hòa được transpose cho sai khác U bằng 0.
Không diễn giải chênh lệch Greedy này thành khác biệt vật lý của cloud law.

| Indexing | p | DP vs Greedy delta U [paired95%CI] | Relative U gain % |
|---|---|---|---|
| Row | 0.4 | 6.69501172e-06 [5.50954035e-06,7.88048309e-06] | 0.856789914 |
| Row | 0.5 | 1.36330997e-05 [1.10746341e-05,1.61915653e-05] | 1.76973447 |
| Row | 0.8 | 8.59963486e-05 [7.64634876e-05,9.55292096e-05] | 13.5131209 |
| Column | 0.4 | 7.59215696e-06 [6.08823231e-06,9.0960816e-06] | 0.972718305 |
| Column | 0.5 | 1.45261281e-05 [1.17818089e-05,1.72704474e-05] | 1.88784841 |
| Column | 0.8 | 8.58737823e-05 [7.63958995e-05,9.53516651e-05] | 13.491263 |
| Serpentine | 0.4 | 8.04675638e-06 [6.25979404e-06,9.83371872e-06] | 1.0315772 |
| Serpentine | 0.5 | 1.26872938e-05 [1.00232068e-05,1.53513808e-05] | 1.64512855 |
| Serpentine | 0.8 | 8.62119729e-05 [7.72649795e-05,9.51589663e-05] | 13.5967645 |
| Random_A | 0.4 | 5.29218871e-06 [4.85296994e-06,5.73140749e-06] | 0.67452535 |
| Random_A | 0.5 | 6.44367683e-06 [5.49663567e-06,7.390718e-06] | 0.8253538 |
| Random_A | 0.8 | 3.9762864e-05 [3.46391953e-05,4.48865326e-05] | 5.59083421 |
| Random_B | 0.4 | 4.86668083e-06 [4.41920797e-06,5.31415368e-06] | 0.62006973 |
| Random_B | 0.5 | 6.26056334e-06 [5.7598459e-06,6.76128077e-06] | 0.801831297 |
| Random_B | 0.8 | 4.9091256e-05 [4.24377433e-05,5.57447686e-05] | 7.00402007 |

Với random mapping, tương quan mạnh có thể nối các ô vật lý xa/gần tùy ý:
performance và độ lớn lợi ích DP thay đổi. Tại p=0.8, U gain của DP so với
Greedy là 13.51% Row, 13.60% Serpentine, 5.59% Random_A, 7.00% Random_B.
DP vẫn trội U trong các instance đã thử, và CI delta U paired dương ở cả
năm mapping, nhưng độ lớn gain không bất biến với cách đánh index.
Hai permutation ngẫu nhiên không đủ để khái quát mọi mapping hoặc xác định
một mô hình mây vật lý; đây là hạn chế của covariance theo index.

## D. Winning exact-source evidence

Nguồn nu_raw=0.30, VA=1.358333319784304, C=1.067911050328646,
w=5.700303183579203e-10, ensemble b083ac84…eb214.
Identity/hash/settings/PMF/normalization PASS; nu_repo=12.75.
Không phục hồi được receipt gắn với nguồn này theo từng precision.
Cache writer lưu summary C,w/route/support và bỏ các precision diagnostics.
Giữ INSUFFICIENT_EVIDENCE; hash hoặc phép tính SKR đúng không chứng minh hội tụ.

Sensitivity riêng: 13 scenario × 14 context đã lưu = 182 component-rate call.
Giữ MI/effective channel đã lưu, tính Eq14/Eq13 bằng helper nguyên bản ở
80/110 chữ số. Primary evaluator vẫn từ chối C,w không khớp payload;
không tắt provenance guard. Các stress C±1e-10/1e-8/1e-6, w±1%/10%/100%
đều giữ rank 1 và SKR dương ở 100/100 vị trí, với giả thiết chỉ perturb
winner và giữ nguyên 211 nguồn khác. Đây là các đầu vào stress nhân tạo,
không phải sai số solver đã được chứng nhận hoặc chứng minh hội tụ nguồn.
Kế hoạch phục hồi một nguồn được chuẩn bị riêng, chưa chạy.

## E. Manuscript readiness

Đã chuẩn bị bốn subsection IEEE-style bằng LaTeX, không sửa frozen manuscript.
Phần cloud/mobility mô tả các convention đã duyệt; phần results chứa CI,
giới hạn indexing, hình học và giả định thông tin oracle. Phần limitations
nêu rõ mây tổng hợp, không cloud motion, distance chưa phải propulsion energy,
bằng chứng hội tụ nguồn và homodyne/security validation còn thiếu.
Không thêm citation hoặc định lý bảo mật chưa được xác minh.

Canonical PDF cùng SHA f970cd6d… có bốn trang theo PdfReader, gồm trang 4
là references. Metadata “ba trang” trong prose Phase C là sai sót đếm trang;
Phase D ghi đính chính, không sửa PDF hoặc artifact lịch sử. Công thức và
physical results không bị ảnh hưởng. LaTeX đã kiểm tra cấu trúc/nhãn, nhưng
chưa compile IEEEtran vì không có TeX engine trong PATH. Draft sẵn sàng
review nội dung; mathematical/security validation và publication readiness
vẫn chưa đạt.

## F. Execution and preservation

New C,w calculations=ZERO; source job=ZERO; channel integration mới=ZERO.
182 component-only SKR call thành công, gồm 14 lần kiểm tra lại giá trị gốc.
Probe trước đó có 14 stored-value primary call thành công và 168 lần guard
từ chối đúng dự kiến; giữ riêng, không gọi chúng là physicality failures.
Tổng cộng 196 downstream rate evaluation thành công, 168 attempt bị guard từ chối.

Monte Carlo mới: 1200 cấu hình mapping/p/mission × ba thuật toán = 3600 call;
tái dùng 900 baseline algorithm record, không sinh independent cloud draw mới.
Thêm 300 Greedy-only transpose/tie check, chín lời gọi thuật toán trong ba
toy graph mới, và các fixture trong bốn unittest method được ghi nhận riêng.
Bootstrap seed 20261026, 10.000 replicate; mapping seed 20261026/27;
base field seed 20261015, mission ID 0…99.

Bốn unittest method, ba restricted-graph brute-force case, 7600 bất đẳng thức
DP đã lưu, 2400 bất đẳng thức DP mới và 300 transpose Greedy check đều PASS.
Không vi phạm vận tốc; không có perturbation thất bại trong component stage.
Đối chiếu hash 9886 file lịch sử, không có thay đổi. Bằng chứng hội tụ nguồn
chưa phục hồi được là dependency khoa học còn thiếu, không phải failed test.
Xem artifact_integrity_report.md và verification.json cho kiểm chứng cuối.

Mã reproduce_phaseD.py mặc định verify chỉ đọc. Analysis guard ngăn tự động
ghi đè run đã hoàn tất. Reports/figures đọc CSV/NPY/NPZ đã tính;
xem figure_index.md. Giữ PHASE_B_STRICT_READY=FALSE,
UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Không training, test/heldout/publication, sửa frozen/production/cache,
source job hoặc tự động nâng lifecycle.
