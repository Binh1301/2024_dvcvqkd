# Bộ kết quả cuối — HAP–UAV CV-QKD

**UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.**

Chỉ tổng hợp dữ liệu đã hoàn tất. Không chạy lại P1/P2/P3/Greedy, kênh, SKR, MI/Holevo, C,w hoặc sinh mây; không thêm điểm tham số. Giữ nguyên Stage A/B và mọi receipt cũ. Bốn hình trong bộ này dùng đánh số riêng, không sửa PDF bản thảo hoặc điền các placeholder tác giả.

## 1. Bốn hình chính

| Hình | Câu hỏi | PDF vector | PNG 350 dpi | Dữ liệu vẽ |
|---|---|---|---|---|
| 1 | Thêm vị trí UAV cải thiện objective thế nào? | [PDF](figures/fig1_candidate_positions.pdf) | [PNG](figures/fig1_candidate_positions.png) | [CSV](figures/fig1_candidate_positions_data.csv) |
| 2 | Mây làm giảm SKR và tăng unavailability thế nào? | [PDF](figures/fig2_cloud_blockage.pdf) | [PNG](figures/fig2_cloud_blockage.png) | [CSV](figures/fig2_cloud_blockage_data.csv) |
| 3 | Persistence thay đổi objective và nhu cầu di chuyển ra sao? | [PDF](figures/fig3_temporal_correlation.pdf) | [PNG](figures/fig3_temporal_correlation.png) | [CSV](figures/fig3_temporal_correlation_data.csv) |
| 4 | Các λ đã thử đánh đổi SKR lấy quãng đường thế nào? | [PDF](figures/fig4_skr_mobility_tradeoff.pdf) | [PNG](figures/fig4_skr_mobility_tradeoff.png) | [CSV](figures/fig4_skr_mobility_tradeoff_data.csv) |

Chọn đúng bốn chủ đề theo yêu cầu cuối: J/objective; p/SKR–unavailability; rho/objective–distance; tradeoff K–D. Đây là lựa chọn biên tập sau khi Stage A/B hoàn tất, không phải chọn lại seed, mission hoặc tham số để tạo kết quả thuận lợi. Các cấu hình và 100 realization ID được giữ nguyên.

Tất cả hình rộng 7,2 inch, nền trắng, font serif, lưới nhẹ; P2 xanh dương/liền/tròn, Greedy cam/đứt/hình thoi, DP đỏ/liền/tam giác. Marker và nét giúp phân biệt khi in xám. Không làm trơn hoặc nội suy. Dùng trục tuyến tính để giữ đúng các giá trị unavailability bằng 0. Hình 4 nối theo thứ tự λ gốc, không sắp xếp lại theo khoảng cách.

## 2. Cấu hình và các đại lượng

HAP cao 20 km, UAV cao 1 km; HAP ngang (11419,6551;450) m. Vùng 1 km×1 km gồm 100 tâm ô, mỗi trục 50,150,…,950 m; X tăng trước. Đây là hình học tổng hợp. Nhiệm vụ 30 slot×20 s, vmax=15 m/s; bước đi không quá 300 m, được đứng yên. Khởi đầu tự chọn, không có chi phí triển khai/quay về. J sweep dùng đúng tập con lồng nhau đã lưu.

Giữ quang học và evaluator hiện tại: 1550 nm; phân kỳ toàn phần 233 μrad; đường kính thu 0,08 m; tau_zen=0,92; beta=0,95; xi_ch=0,0186 SNU; detector lý tưởng. Các tham số còn lại được truy vết trong [protocol](protocol.json), không lấy từ cấu hình quang học lịch sử khác.

Mây chặn hoàn toàn: S_jn=(1−C_jn)Kstar_j. Mặc định p=0,4, ell=250 m, latent rho=0,9; seed=20261015, ID=0–99. Cùng ID và common innovations ghép cặp giữa các cấu hình. Các tham số Gaussian tiềm ẩn không đồng nhất với tương quan Bernoulli sau threshold.

- K: SKR khả dụng trung bình dọc đường, bit/use.
- D: tổng quãng đường giữa các slot, m.
- U=K−λD/1000: objective có phạt mobility, bit/use; không gọi U là SKR.
- Availability=mean(S_path>0); unavailability=100×mean(S_path=0). Không dùng engineering threshold.
- λref=9,468026677248516×10⁻⁶ bit/use; hình 1–3 dùng đúng giá trị này. Hình 4 dùng đủ 10 λ đã lưu.

Không có channel-use rate nên không đổi K hoặc tổng K theo slot thành số bit khóa hay throughput bit/s.

## 3. Kết quả tham chiếu và phân biệt SKR/objective

Ở cấu hình mặc định tại λref:

| Phương án | Mean K (×10⁻⁴ bit/use) | Mean U (×10⁻⁴ bit/use) | Mean D (m) | Availability (%) |
|---|---:|---:|---:|---:|
| P2 | 1,502428 | 1,502428 | 0 | 97,767 |
| Greedy | 1,523879 | 1,483109 | 430,610 | 98,733 |
| DP | 1,564954 | 1,548628 | 172,433 | 99,900 |

Các tỷ lệ được đối chiếu với dữ liệu thô, không áp đặt từ yêu cầu: **gain K DP/P2=4,16162%; DP/Greedy=2,69538%; gain U DP/P2=3,07498%; DP/Greedy=4,41766%**. Vì có penalty, Greedy có mean K cao hơn P2 nhưng mean U thấp hơn P2.

Delta U_DP−P2=4,6199339×10⁻⁶ bit/use, CI95% [3,5650268;5,7313908]×10⁻⁶. Delta U_DP−Greedy=6,5518695×10⁻⁶, CI95% [4,9897767;8,4622842]×10⁻⁶. Đây là CI của chênh lệch ghép cặp; không trừ hai CI riêng lẻ.

DP tối ưu U của bài toán lưới offline đã lưu. Không suy ra DP tối ưu K hoặc availability ở mọi mission: tại λref mặc định, K_DP thấp hơn K_Greedy trong 25/100 mission. Toàn bộ thống kê mean/SD mẫu/median/CI/N và các delta tuyệt đối nằm trong [bảng thống kê](tables/statistical_comparison.csv) và [bảng ghép cặp](tables/paired_improvements.csv).

## 4. Hình 1 — Số vị trí UAV

J tăng 10→100: U_DP tăng 1,3900370×10⁻⁴→1,5486275×10⁻⁴ bit/use, **+11,41%**. U_P2 tăng 1,3634830×10⁻⁴→1,5024282×10⁻⁴; U_Greedy tăng 1,0780008×10⁻⁴→1,4831088×10⁻⁴. DP có mean U cao nhất tại các điểm đã thử.

J=20 đạt 96,71% U_DP của J=100. Có lợi ích biên nhỏ dần sau mở rộng ban đầu, nhưng không gọi J=20 là lựa chọn tối ưu về chi phí vì chưa định giá số vị trí. J=10 có tám thành phần liên thông và bảy điểm cô lập; từ J=20 đồ thị đã liên thông. Vì vậy không thể gán toàn bộ cải thiện ban đầu chỉ cho mật độ vị trí.

Tập lựa chọn lồng nhau bảo đảm U tối ưu của DP/P2 không giảm; Greedy không có bảo đảm này. Không chuyển bảo đảm objective thành bảo đảm availability hoặc quãng đường.

## 5. Hình 2 — Đủ tám mức xác suất chặn

| p | Mean K_DP (×10⁻⁴ bit/use) | Unavailability P2 (%) | Greedy (%) | DP (%) | Gain U_DP/P2 (%) |
|---|---:|---:|---:|---:|---:|
| 0,1 | 1,5766271 | 0 | 0,0667 | 0 | 0,0706 |
| 0,2 | 1,5744672 | 0,1000 | 0,0667 | 0 | 0,3939 |
| 0,3 | 1,5702651 | 1,0333 | 0,6000 | 0,0333 | 1,5200 |
| 0,4 | 1,5649535 | 2,2333 | 1,2667 | 0,1000 | 3,0750 |
| 0,5 | 1,5536360 | 4,0000 | 1,9667 | 0,4000 | 5,3462 |
| 0,6 | 1,5371783 | 7,0000 | 3,3333 | 0,5333 | 8,9046 |
| 0,7 | 1,5029566 | 13,1000 | 9,4333 | 1,9000 | 14,2124 |
| 0,8 | 1,4347523 | 24,6000 | 16,5333 | 4,0667 | 25,0416 |

**Quan sát:** K trung bình của cả ba phương án giảm khi p tăng. Với DP, delta U tuyệt đối so với P2 tăng 1,1121540×10⁻⁷→2,7280557×10⁻⁵ bit/use; gain tương đối tăng 0,0706→25,0416%. CI95% delta tuyệt đối tại p=0,8 là [2,4676008;2,9989589]×10⁻⁵. Vì chênh lệch tuyệt đối cũng tăng, kết quả không chỉ là hiệu ứng mẫu số P2 nhỏ đi.

**Giải thích được hỗ trợ:** mask theo p lồng nhau làm mất thêm reward, trong khi khả năng đổi vị trí giúp DP khai thác các vị trí còn thông thoáng. **Giới hạn:** mức giảm unavailability là kết quả quan sát, không phải một định lý tối ưu availability. Cực đại gain nằm tại biên p=0,8 của dải thử; không chứng minh có optimum hoặc threshold liên tục và không ngoại suy p>0,8.

Greedy không có cùng xu hướng gain đơn điệu: mean U_Greedy thấp hơn P2 ở p=0,1–0,4. Tại p=0,5 mean delta là +7,42605×10⁻⁷ nhưng CI95% [−1,12058×10⁻⁶;2,55326×10⁻⁶] chứa 0. Tại p=0,7, mean delta +3,32171×10⁻⁶ cũng có CI [−3,10424×10⁻⁷;6,79191×10⁻⁶] chứa 0. Không mô tả hai điểm này là cải thiện dương chắc chắn. Tại p=0,8, Greedy gain U/P2=7,84059%, thấp hơn DP=25,04165%.

[Bảng thảo luận p đầy đủ, gồm cả Greedy−P2 và CI](tables/cloud_probability_discussion.csv).

## 6. Hình 3 — Kiểm tra cơ chế persistence

Giữ p=0,4,ell=250 m và λref. Không đồng nhất latent rho với hệ số tương quan mây nhị phân.

| rho | Cloud-free tại P2 (%) | Số vị trí thông suốt cả 30 slot, mean | Tỷ lệ cell-slot đổi trạng thái (%) | Số lần DP đổi vị trí, mean | D_DP (m) | Gain U_DP/P2 (%) |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 77,033 | 0 | 48,213 | 7,36 | 1038,250 | 23,7123 |
| 0,3 | 79,700 | 0 | 39,019 | 5,99 | 861,852 | 21,1151 |
| 0,6 | 86,600 | 0,02 | 28,657 | 3,83 | 581,945 | 15,0689 |
| 0,9 | 97,767 | 6,36 | 14,094 | 1,12 | 172,433 | 3,0750 |
| 0,98 | 99,967 | 29,56 | 6,346 | 0,19 | 31,844 | 0,1551 |

Số mission DP có di chuyển giảm từ 100/100 xuống 10/100. U_DP tăng 1,4455927×10⁻⁴→1,5680628×10⁻⁴ bit/use, trong khi U_P2 tiến gần U_DP. Đó là lý do chọn objective thay vì chỉ SKR ở hình 3: chi phí quãng đường thay đổi nhiều, còn mean K_DP chỉ tăng từ 1,5438945×10⁻⁴ lên 1,5710778×10⁻⁴.

**Bằng chứng:** bảng được tính trực tiếp từ mask và path đã lưu; không suy các đại lượng này bằng mắt từ hình. **Giải thích phù hợp dữ liệu:** persistence làm xuất hiện nhiều vị trí thuận lợi suốt nhiệm vụ và P2 offline có thể chọn chúng, nên lợi ích tăng thêm của di chuyển giảm. **Chưa chứng minh:** đây không phải cô lập nguyên nhân hay quy luật đơn điệu theo rho. Không có matched-information ablation, common-initial-position ablation hoặc kiểm chứng dự báo online.

Tau Gaussian=−20/log(rho) khoảng 989,97 s tại rho=0,98, dài hơn nhiệm vụ 600 s. Tương quan Bernoulli lag1 lý thuyết khi đó khoảng 0,87136. Xác suất chặn thực nghiệm của các mission dao động dù p danh định bằng 0,4; không ép bằng nhau để tạo xu hướng. Độ dài clear-run ở bảng dữ liệu chỉ mô tả cửa sổ 30 slot, có censoring ở biên, không phải phân phối thời gian tồn tại mây ngoài nhiệm vụ.

[Dữ liệu từng mission](tables/temporal_evidence_missions.csv) · [Mean/SD/median/CI của bằng chứng persistence](tables/temporal_evidence_summary.csv).

## 7. Hình 4 — Tradeoff SKR–mobility

Đường nối theo đủ 10 λ đã lưu, không nối theo thứ tự khoảng cách và không gọi là Pareto frontier tối ưu toàn cục. Tại λ=0, DP có K=1,5730512×10⁻⁴ bit/use và D=1482,688 m. Tại λref, K=1,5649535×10⁻⁴ và D=172,433 m: **giảm D 88,37%, giảm K 0,515%**. So với Greedy tại cùng λref, DP đi ít hơn 59,96% và vẫn có mean K/U cao hơn.

Ở các λ đã thử từ 0,1λhi trở lên, DP đứng yên trong cả 100 mission và hòa P2; lambda_hi=0,003156008892416172 bit/use. Chỉ kết luận trên các điểm thử, không định vị threshold liên tục. Greedy dừng di chuyển không đồng nghĩa trở thành P2, vì điểm đầu được chọn theo slot đầu, còn P2 dùng toàn horizon.

Error bar ngang và dọc là CI pointwise cho hai mean, không phải một confidence region chung trong mặt phẳng K–D. Các điểm trùng nhau ở penalty lớn vẫn được giữ đầy đủ trong CSV; P2 được vẽ một điểm tham chiếu để tránh lặp mười lần cùng một giá trị.

## 8. Tương quan không gian: giữ ở phụ lục nhưng thảo luận đủ

Ell 50→1000 m: mean K_DP giảm 1,5736845×10⁻⁴→1,4780582×10⁻⁴; availability giảm 100→96%. Nhưng delta U_DP−P2 tăng 2,2528751×10⁻⁶→8,1083111×10⁻⁶ bit/use, gain tương đối tăng 1,45886→5,95899%.

Dữ liệu mask cho thấy tỷ lệ slot mà **mọi vị trí đều bị chặn** tăng 0→2,70%, tạo outage không thể tránh bằng chọn vị trí tức thời. Cloud-free tại vị trí P2 giảm 99,30→90,87%; mean số lần DP đổi vị trí tăng 0,65→2,25. Vì vậy không diễn giải gain tương đối tăng là bằng chứng spatial diversity tăng. Hiệu năng tuyệt đối giảm, còn P2 giảm mạnh hơn DP trong dải đã xét.

Không có định lý đơn điệu theo ell; mask theo ell không lồng nhau. [Bằng chứng từ mask/path](tables/spatial_evidence_missions.csv) và [thống kê](tables/spatial_evidence_summary.csv) giữ riêng quan sát và giải thích.

## 9. P1, chọn vị trí và mobility là ba vai trò khác nhau

P1 đã tính Kstar_j=[max_G K_j(nu,VA)]+ trên 233 nguồn exact. Cả 100 vị trí chọn cùng (nu,VA)=(0,125;8), cùng ensemble hash. Map clear-sky Kstar vẫn thay đổi theo vị trí, trong khoảng 1,1629628×10⁻⁴–1,5780044×10⁻⁴ bit/use, do các kênh theo vị trí đã lưu; không phải do thay source shaping giữa các vị trí.

- **Nguồn:** P1 cung cấp nền nguồn tối ưu trên catalog hữu hạn; chưa có matched-energy ablation trong bốn hình này nên không định lượng riêng shaping gain.
- **Vị trí đứng yên:** P2 chọn một điểm cho cả horizon; ba đường chính không có deployment cố định không tối ưu nên không dùng chúng để tuyên bố một tỷ lệ gain riêng của stationary selection.
- **Di chuyển:** DP−P2 đo giá trị tăng thêm khi cho phép đổi vị trí trong cùng benchmark offline. DP−Greedy còn bao gồm lợi thế biết tương lai và chọn điểm đầu.

VA=8 ở biên catalog MB. Không gọi nghiệm nguồn là tối ưu trên miền liên tục và không gán gain tránh mây cho một quá trình thay đổi nu/VA không xảy ra.

## 10. Hình phụ nên giữ

| Nội dung | Vai trò đề xuất | Lý do |
|---|---|---|
| SKR/objective theo vmax | Phụ lục, giữ hình Stage A hiện có | Làm rõ ràng buộc tốc độ; 15→25 m/s chỉ tăng U_DP 0,03175%; không lặp thành hai hình mới |
| Availability theo J | Phụ lục | Bổ sung objective ở hình 1; không phải mục tiêu tối ưu trực tiếp |
| Mission duration | Phụ lục | Thay đổi cả horizon và mức phạt tương đối giữa average reward/total distance |
| Spatial correlation | Phụ lục | Quan trọng để giới hạn diễn giải diversity, nhưng ít trực tiếp hơn bốn câu hỏi chính |
| Objective improvement theo λ | Phụ lục | Paired CI giúp đọc gap nhỏ và vùng DP hòa P2; không lặp các đường mean U mới |
| Trajectory P2/Greedy/DP | Phụ lục minh họa | Ưu tiên mission ID0 đã chọn trước; nếu dùng ví dụ ID84 phải ghi rõ chọn hậu nghiệm, không xem là điển hình thống kê |
| Stage A p chỉ năm điểm | Thay bằng hình 2 cuối | Stage B đã bổ sung đủ tám điểm; không giữ hai hình gần trùng nhau trong bài chính |
| S1 paired gaps | Tùy giới hạn phụ lục | Hữu ích về effect size, nhưng thông tin đã có trong bảng paired cuối |

[Danh mục hình gốc và đề xuất chi tiết](figure_inventory.csv). Không tạo thêm các hình phụ trùng nội dung.

## 11. Sáu câu trả lời cuối

1. **Tham số tác động SKR mạnh nhất?** Theo span mean trên đúng các dải đã thử: J đối với DP (1,61527×10⁻⁵ bit/use); vmax đối với Greedy (5,45254×10⁻⁵); p đối với P2 (4,85539×10⁻⁵). Đây là mô tả có điều kiện, không phải chỉ số độ nhạy được chuẩn hóa.
2. **DP có lợi nhất so với P2 khi nào?** Trong các cấu hình mây đã lưu, gain U tương đối lớn nhất tại p=0,8,ell=250m,rho=0,9:25,04165%. Delta U tuyệt đối lớn nhất tại p=0,4,ell=250m,rho=0:2,7708111×10⁻⁵ bit/use; gần giá trị tại p=0,8. Không suy optimum trên tổ hợp p×ell×rho chưa quét.
3. **Rho thay đổi di chuyển bao nhiêu?** Rho0→0,98: D_DP1038,250→31,844m; số lần đổi vị trí7,36→0,19; số mission di chuyển100→10. Bằng chứng persistence hỗ trợ P2 trở nên cạnh tranh hơn trong benchmark offline.
4. **Greedy và DP khác nhau thế nào?** Tại λref mặc định, meanK_DP cao hơn2,69538%, meanU cao hơn4,41766% và D thấp hơn59,95613%. Tuy nhiên K_DP không cao hơn trong mọi mission và thông tin tương lai không công bằng giữa hai thuật toán theo nghĩa online.
5. **Bốn hình bài chính?** J/objective; p/SKR–unavailability; rho/objective–distance; K–D theo λ. Các hình khác chuyển phụ lục có lý do cụ thể.
6. **Kết luận nào chưa phải claim bảo mật?** Toàn bộ so sánh là kết quả số theo evaluator bản thảo, chưa phải chứng minh an toàn vật lý, finite-size/composable hoặc vận hành thực nghiệm.

## 12. Thống kê, truy vết và giới hạn

Bảng cuối có mean, SD mẫu, median, CI95% và N=100 cho mỗi nhóm; SD không phải CI. Hình 1–3 dùng lại CI bootstrap đã xác thực của Stage A/B, seed20261020. CI mean còn thiếu của tradeoff được dựng từ output từng mission và chính count vectors đã lưu, không có bootstrap draw mới. CI paired K/U của tradeoff giữ artifact seed20261019; những CI paired D/availability không được lưu trước được dựng bằng count vectors20261020 và ghi rõ provenance theo từng hàng. Ratio CI để trống nếu artifact cũ không có, không tự nhận là đã lưu.

29 tổ hợp hình–cấu hình bao gồm baseline dùng lại giữa các hình; không coi chúng là 29 thí nghiệm độc lập. [8.700 bản ghi phục vụ hình](tables/selected_missions.csv), [696 hàng thống kê](tables/statistical_comparison.csv), [232 hàng paired](tables/paired_improvements.csv) và [mapping tới nguồn](figure_source_mapping.csv) giữ đúng grain và realization ID. CI pointwise chưa hiệu chỉnh multiple comparisons, không phải confidence bounds lượng tử.

Giữ giới hạn catalog/lưới hữu hạn, hình học/mây tổng hợp, chặn hoàn toàn, oracle current-state cho Greedy và toàn horizon cho P2/DP, bỏ qua reacquisition/transit/flight interruptions, không chi phí triển khai/quay về, chưa hiệu chuẩn năng lượng. MI hai chiều ghép Holevo homodyne là mô hình số chưa xác thực an toàn. Giữ frozen-hash discrepancy, Objective C USER_STOPPED, UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

Không thay scientific source, security functional, frozen specification, cache, baseline hoặc threshold approval; không training/test/final-test/held-out, không sửa bản thảo bên ngoài, commit hoặc push.

[English Numerical Results and Discussion](numerical_results_discussion_en.md) · [English captions](figure_captions_en.md) · [Protocol](protocol.json) · [Input manifest](input_manifest.json) · [Validation](validation_report.md) · [Receipt](validation/final_receipt.json).
