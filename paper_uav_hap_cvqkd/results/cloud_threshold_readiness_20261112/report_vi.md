# Kiểm tra điều kiện xác định ngưỡng suy hao mây

Ngày 2026-11-12. **Chưa hoàn thành phép tính ngưỡng được yêu cầu.**
Trạng thái: BLOCKED_BY_SCIENTIFIC_PREREQUISITES. Acrit_fixed và Acrit_reoptimized
đều chưa xác định (null), không phải 0 dB. Không có sweep SKR hoặc hình ngưỡng mới.

## Nguồn chân lý và các nhánh không được trộn

`src/cvqkd/secret_key_rate.py::fading_secret_key_rate` giữ cả raw=beta*MI-Holevo
và positive-part riêng. Root phải dùng instantaneous_raw/fading_average_raw theo
đúng nhánh đã chọn, không dùng instantaneous_positive_part.
`src/channel/fso_channel.py` ghép khí quyển, scintillation, pointing và AoA;
không thay các yếu tố này bằng một mean T đơn lẻ trong mô hình oracle-iid.
`src/optimization/baseline_search.py` là tìm kiếm trên validation có constraints,
không phải giấy phép đổi sang một miền VA/nu khác.

Đặc tả FINAL_MODEL_SPEC có nhánh direct-Z-minus, ideal heterodyne, D_r=0.55m,
xi_total=.0186, nu_raw>=0, VA>0 không có cận vật lý trên cố định.
Trong khi đó gói hình Eq14 gần nhất dùng homodyne hiệu dụng, D_r=0.30m,
xi_ch=.0186, xi_det=.005, beta=.95, VA=[.05,10],nu_raw=[0,.4], AO/phase OFF.
Code đánh giá lịch sử:
`results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/diagnostic_model.py::evaluate`.
Nó gọi MI GH64/128 và components Eq14/Holevo ở 80/110 chữ số,
với nguồn DM 256 điểm, không được thay bằng công thức Gaussian-modulation.
Nguồn MB có nu_repo=42.5*nu_raw, VA=2*nbar.
Các nhánh trên cho các bài toán khác nhau; không tự chọn khẩu độ hoặc Holevo
theo ý nghĩa mơ hồ của từ current.

## Bằng chứng chặn hiện tại

Hash FINAL_MODEL_SPEC thực tế `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15` khác hash lịch sử AGENTS
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`. Giữ nguyên tệp, không tự phục hồi hoặc phê duyệt hash mới.
readiness Phase B: phase_B_ready=false, số nguồn theo lớp {'VERIFIED_EXACT': 6, 'VERIFIED_BY_ALTERNATIVE_EVIDENCE': 1, 'INSUFFICIENT_EVIDENCE': 74, 'INVALID': 0}.
E2: INCONCLUSIVE; source tốt nhất còn INSUFFICIENT_EVIDENCE,
full_support_certified=false; chưa có rigorous_Cw_error_bound.
Hash nguồn tốt nhất và liên kết protocol đã kiểm tra trực tiếp, không chỉ chép
nhãn PROJECT_STATE. Đây là thiếu bằng chứng, không khẳng định C,w chắc chắn sai.
Một nghiệm root chính xác đến .005 dB không thay thế hội tụ C,w/MI/Holevo.
Không chạy tối ưu liên tục rồi nội suy C,w ở các VA,nu chưa có nguồn chính xác.
Max trên 212 nguồn lịch sử cũng không được gọi là tối ưu liên tục toàn miền.

## Đặt suy hao đúng một lần

Với mỗi realization T_clear, dùng T_eff=s*T_clear, s=10^(-A/10), giữ AoA atom0.
Đối với nhánh moments cố định: m1'=s*m1, mh'=sqrt(s)*mh, M0'=M0, P0'=P0.
Không tái chuẩn hóa PDF và không tái tích phân một PDF clear trên miền [0,1]
để vô tình lấy thêm phần đuôi đã loại khỏi baseline.
Đặc biệt nhánh Eq14 có noise N=(m1-mh^2)*VA+xi_ch*m1+xi_det*M0.
Sau suy hao, N'=s*((m1-mh^2)*VA+xi_ch*m1)+xi_det*M0;
detector noise không bị suy hao cùng tín hiệu. Không đơn giản nhân toàn N với s.
Sau đó phải gọi lại chính MI/Holevo của nhánh đã chọn, không scale SKR đã lưu.
Nếu trạng thái oracle tức thời được chọn, phải tính từng realization trước average;
không thay average(K(T)) bằng K(average(T)).

## Hình học đã kiểm tra

Miền UAV cấu hình manuscript hiện có là 1000m, 10x10 tâm ô,
HAP xy=[11419.65511459133, 450], không phải miền 2km x2km của trường mây.
`existing_geometry.csv` ghi toàn bộ 100 vị trí cũ, không gán threshold.
Với **giả thiết bổ sung** HAP ở tâm miền 2km liên tục, khoảng đứng 19km:
zenith lớn nhất 4.256806676 độ,
Lmax 19.052558883km.
Đây chỉ là biên hình học có điều kiện, chưa là layout QKD được chọn.
L=22km tương ứng góc 30.272641319 độ và bán kính
ngang 11.090536506km: là extended-range,
không phải do miền bay 2km tự sinh ra. Không đồng nhất xy_UAV với xy trên lớp mây.

## Công cụ đã chuẩn bị và giới hạn

`src/cloud_threshold_search.py` cung cấp pushforward realization/moments và
coarse raw sweep0..100dB/bước.5, bisection bracket rộng<=.005dB qua callback.
Chưa nối một evaluator khoa học vì nhánh chưa được quyết định. Test callback
giải tích chỉ là fixture kiểm thử root, không là công thức SKR thay thế.
Hàm xử lý K(0)<=0 như không có positive margin, không giả vờ root=0;
không có crossing thì right-censored, không ngoại suy. Có nhiều crossing hoặc
upward steps thì không trả một threshold duy nhất. Sweep chỉ chứng minh
monotonicity tại các điểm đã đánh giá, không bảo đảm liên tục hay toàn miền.
Nhánh tối ưu còn cần tolerance/budget, convergence và sai số từng evaluation;
bracket theo dấu không đáng tin nếu sai số số học làm dấu K không chắc chắn.

Định nghĩa outage bằng dấu Kraw<=0 vẫn đúng theo evaluator được chọn.
Chưa xác minh quy tắc A>=Acrit hay một ngưỡng toàn cục. Nếu chọn average-SKR
thì threshold của average khác outage tức thời; AoA đã gây K=0 dù A=0.
Không cài quy tắc outage mới vào mô hình mây/QKD hiện có.

## Việc cần quyết định trước bước tính số

Chọn rõ nhánh Eq14 diagnostic hoặc frozen ideal-heterodyne; cố định khẩu độ,
receiver/noise/security convention và miền VA/nu theo nhánh đó. Gắn HAP xy và
lưới UAV thực với miền 2km. Xác nhận chỉ chạy chẩn đoán dùng nguồn chưa được
chứng nhận, hoặc hoàn tất điều kiện hội tụ trước ngưỡng có thể dùng chính thức.
Không có một boolean override nào trong công cụ để bỏ qua thiếu bằng chứng.
Reoptimization phải dùng procedure và nguồn hợp lệ, không đổi thành catalog
envelope hoặc surrogate. Không tự chạy AP cao, training, final-test, held-out,
publication hoặc ObjectiveC đã USER_STOPPED.

Các tệp số có sẵn ở A=0 được trích riêng `saved_clear_sky_reference.csv` và
đánh dấu nguồn lịch sử; không phải sweep suy hao hoặc Experiment A/B mới.
Figure1,Figure2,Figure3,threshold-map và so sánh fixed/reoptimized: **NOT_RUN**.
