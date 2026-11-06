# Kiểm tra điều kiện tạo bản đồ SKR 2D

Ngày 2026-11-05. Trạng thái **GEOMETRY_ONLY_SKR_NOT_RUN**. Chưa có bản đồ SKR
đã được tính hoặc xác thực, chưa thể dùng lookup này để tối ưu quỹ đạo.

## Phạm vi đã chuẩn bị

`prepare_geometry.py` tạo 51×51 điểm, bước 40 m, vùng [0,2000]² m, HAP chiếu
tại (1000,1000) m, HAP 20 km và UAV 1 km. `geometry_only.csv` và
`geometry_only.npz` là **dữ liệu hình học**, không phải lookup SKR: 2.601 dòng
có `numerical_status=NOT_RUN`, mọi cột channel/rate/source để trống trong CSV
và NaN trong NPZ. Hàm `lookup_skr(x,y)` từ chối trả số hoặc nội suy khi chưa có
bản đồ; tọa độ ngoài vùng cũng bị từ chối.

| Kiểm tra hình học/quang hình học | Giá trị |
|---|---:|
| L tại tâm | 19.000 km |
| Zenith tại tâm | 0° |
| L tại góc vùng | 19.0525589 km |
| Zenith lớn nhất | 4.25680667589° |
| w0, full-angle 35 µrad | 0.02819316135 m |
| wL tại L=19 km | 0.3336931290 m |

Tại 30° phải có r_perp=19000 tan(30°)≈10969.655 m, vượt xa bán kính
1414.214 m của vùng. Không đặt điểm benchmark 30° vào map.

## Cấu hình và pipeline xác định được

`results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/protocol.json`
khóa Dr=.30 m, lambda=1550 nm, full-angle 35 µrad, jitter=1.561 µrad/trục,
sigma_h=.10 m/trục, tau_zen=.92, xi_ch=.0186 SNU, xi_det=.005, beta=.95,
homodyne/RR, AO và phase OFF. Không có tham số detector efficiency riêng trong
protocol này; không thêm eta_det=.95 của model cũ. `nu_repo=42.5 nu_raw`,
VA=2 nbar; source đã đánh giá theo miền VA=[.05,10], nu_raw=[0,.40].

Producer có thể truy cập: `results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/diagnostic_model.py`
gọi `canonical.channel_context` và các hàm MI/Holevo Eq14/Eq13; source inventory
và lịch sử 212 nguồn nằm cùng namespace đó. `results/phaseC_new_cloud_dp_greedy_stationary_20261025/physical_map.py`
là một consumer trước đây, không phải sự cho phép mới để thực thi sweep này.
Exact finite catalog chỉ cho best-tested trong catalog; không tự chứng minh
nghiệm joint/global liên tục. Ngoài catalog, C,w đúng ensemble phải có evidence;
không nội suy C,w.

## Đối chiếu benchmark đã lưu — không chạy lại

Hai hàng đã lưu trong `diagnostic_selected_schemes.csv`, cùng source
nu_raw=.30 và VA=1.358333319784304; cả hai là **INSUFFICIENT_EVIDENCE**.

| Zenith | beta I_AB | chi_BE | K_raw bits/use |
|---|---:|---:|---:|
| 0° | 0.17879398133692795 | 0.17799789352884182 | +0.0007960878080861267 |
| 30° | 0.14966583132819633 | 0.15269755977130728 | -0.003031728443110948 |

So với các số làm tròn trong yêu cầu: residual archived beta I tại 0° là
+3.692795e-11; archived chi là +2.884182e-11; archived K là +8.086127e-12;
archived K tại 30° là +1.556889e-9 bits/use. Đây chỉ là kiểm tra chênh lệch
do làm tròn của dữ liệu lưu, **không phải independent benchmark reevaluation**.
Hệ thống chưa chạy lại MI, Holevo, channel hoặc SKR trong task này.

## Các blocker đã kiểm tra

1. `readiness.json` ghi `phase_B_ready=false`. Protocol strict và state hiện
   hành không cho phép coi bản đồ tối ưu MB hoặc baseline là đã được xác thực.
2. `phaseE2_winning_source_spectral_validation_20261026/source_convergence_status.json`
   vẫn INCONCLUSIVE. 231/256 mode Fock và 186/256 mode Gram đã phân giải trong
   hai kiểm tra được nêu; tính dương 256 mode không chứng minh độ chính xác C,w.
   Không có cận sai số C,w/Z/SKR đủ để xác nhận dấu của winner.
3. Raw Eq10 tại 0° có deficit≈1.0569955e-10, lớn hơn tolerance1e-10.
   Kết quả saved ở trên thuộc diagnostic đã cho phép riêng, không chứng minh
   raw PDF đạt gate. Không normalize/clip để làm nó đạt.
4. Exact 212-source finite catalog không chứng nhận tối ưu liên tục trên (nu,VA).
   Không thể đưa `nu_opt`, `VA_opt` hoặc K* như global maximum khi thiếu chứng cứ.
5. Frozen spec SHA256 thực tế df83ea63...78c15 khác expected lịch sử trong
   AGENTS.md. Preserve frozen file, lifecycle NOT_READY và security-model
   UNVALIDATED. Áp dụng các điều kiện này trước bất kỳ optimized-MB search nào.

## Để tiếp tục

Cần giải quyết/bind lại scientific protocol và support-normalization gate,
thiết lập evidence source C,w cho các candidate dùng trong map, và xác lập
quyền chạy optimized-MB theo project lifecycle. Sau đó mới rerun hai benchmark,
đánh giá từng hình học theo evaluator hiện hành, lưu signed raw K và chỉ clip
potential sau optimization. Nếu chỉ đánh giá finite catalog thì phải đổi nhãn
thành **best-tested catalog**, không gọi maximum toàn miền. Những node lỗi
phải giữ trạng thái và không được nội suy qua như số đã xác minh.

Không tính bản đồ channel/SKR, không chạy tối ưu/source AP, cloud, finite-size,
training, test/held-out hoặc publication; không thay source/config/spec/cache.
Không vẽ heatmap SKR giả hoặc đưa các giá trị NaN thành zero. Evidence geometry
và hashes nằm ở `geometry_receipt.json`; `verification.json` và `test_geometry.py`
ghi kiểm tra thực hiện trong task này.

2026-11-06: hai unit tests và mười kiểm tra geometry/archive **CURRENTLY_VERIFIED_PASS**.
Lượt ghi verification đầu lỗi serialize `numpy.bool_`; output dở được giữ tại
`verification_failed_serialization.json`, sau đó đổi bool thành Python bool và
chạy lại thành công. Không đổi số liệu và không chạy benchmark vật lý.
