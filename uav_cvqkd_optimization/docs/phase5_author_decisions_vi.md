# Quyết định cần tác giả chốt cho base experiment — Phase 5

Tài liệu này chỉ ghi phương án và hệ quả; **không phê duyệt hoặc áp dụng lựa
chọn nào**. `paper.yaml`, hai profile rotor và các evidence labels giữ nguyên.
Các số reference không tự trở thành mission defaults. Không cần quyết định
lại tính đúng đắn của Z/w: xác nhận hiện tại của tác giả được giữ nguyên.

## 1. Chọn cấu hình kênh và xử lý lookup

Nguồn cũ: [execution_physical_protocol.json](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json),
`physical.*`. Nguồn mới:
[hap_uav_mb_reference.yaml](../configs/channel/hap_uav_mb_reference.yaml),
bản thảo nhóm tác giả Section IV/PDF p3. Bản thảo chưa được gọi là published/
peer-reviewed. Chi tiết hệ quả nằm trong báo cáo readiness.

| Parameter | Old lookup | New HAP–UAV config | Unit | Source | Consequence |
|---|---:|---:|---|---|---|
| Receiver aperture diameter | 0.30 | 0.08 | m | Old `physical.Dr_m`; new `receiver_aperture_diameter_m` | Đổi aperture collection/pointing moments; không chuyển rate cũ sang profile mới |
| Beam full divergence | 35 | 233 | µrad | Old `physical.divergence_full_urad`; new `beam_full_divergence_rad=233e-6` | Đổi footprint/geometric coupling; giữ full-angle convention |
| Transmitter jitter angle, per axis | 1.561 | 15.61 | µrad | Old `physical.jitter_urad`; new `transmitter_jitter_angle_rad=15.61e-6` | Đổi pointing spread/moments; không chỉ đổi nhãn trục |
| UAV position standard deviation, per axis | 0.10 | 1.00 | m | Old `physical.sigma_h_m`; new `uav_position_sd_m` | Đổi displacement distribution và fading moments |

Phương án cần chọn: (A) nghiên cứu đúng receiver30 với đầy đủ geometry/noise/
protocol lineage cũ và giữ giới hạn evidence; (B) dùng đúng Section IV mới và
cho phép một task tạo dữ liệu kênh/SKR mới sau khi đủ input; hoặc (C) cung cấp
một lineage khác có nguồn và binding rõ. Không trộn hardware của B với rate
của A. Không có lựa chọn nào tự nâng `INSUFFICIENT_EVIDENCE` hay
`paper_admissible`. Không cần chạy lại 2.601 điểm chỉ để chốt lựa chọn này.

## 2. Các quyết định còn lại

| Quyết định | Phương án tác giả có thể chốt | Ảnh hưởng | Nguồn/trạng thái hiện tại |
|---|---|---|---|
| Noise model và convention | Giữ đúng receiver30 trong phương án A; hoặc khai báo đầy đủ xi_ch, xi_det và detector/noise treatment cho B/C | Noise-weighted moments, effective xi, MI/Holevo và rate; không được đồng nhất detector efficiency với beta | Receiver30 ghi .0186/.005 SNU; Source-A reference mới để null; [matrix Phase4](integrated_three_paper_parameter_matrix_vi.md) |
| HAP horizontal coordinates | Kế thừa projection (1000,1000)m của lookup chỉ khi chọn toàn bộ scenario A; hoặc chọn tọa độ mission khác và dữ liệu kênh phù hợp | Zenith, slant distance, LOS/cloud và miền rate | Altitude 20000m đã có; tọa độ ngang mission chưa chọn; producer `geometry_groups` xác định tâm lookup cũ |
| UAV initial position q0 | Chọn điểm xuất phát có rationale, thuộc/được thêm vào graph | Feasible paths, hover baseline và mọi objective | `initial_m=null`; không dùng tâm map hay điểm demo mặc định |
| Rotor baseline | Chọn nguyên profile arXiv2018v1 hoặc IEEE2019 cho run mới | Power/hover, v_max, edge costs và horizon năng lượng | [arxiv_2018_v1.yaml](../configs/rotor/arxiv_2018_v1.yaml), [ieee_2019.yaml](../configs/rotor/ieee_2019.yaml); default hiện tại vẫn arXiv |
| Usable propulsion Emax | Cung cấp ngân sách J trực tiếp có provenance; hoặc chọn T_ref và công khai Emax=P_hover*T_ref như scenario allocation | Feasible K/paths và stopping; không phải toàn bộ battery capacity nếu có phân bổ khác | `energy_budget_j=null`; không chọn duration hay budget thay tác giả |
| Waypoint graph | Explicit points hoặc lattice/restricted lattice với spacing/bounds và q0 | Action set, connectivity, edge energy, độ phân giải và chi phí DP | `graph=null`; cloud 50×50 không tự là movement graph |
| Mission/prediction horizon | Chọn số slot có dự báo khả dụng; giữ dt nhất quán | Trần lookahead; K tối ưu vẫn là biến, còn bị chặn bởi energy | `max_horizon=null`, dt=1s trong paper config; reference zenith30° không áp cho mọi waypoint |
| Cloud mechanism | Binary opaque-cloud erasure; hoặc optical attenuation với sourced post-loss moment/noise provider | Binary: m=0 khi blocked; analog: rate thay đổi, giữ m0; không cộng hai lần cùng cloud loss | Mode chưa được tác giả chọn; Phase4 policy approval vẫn false |
| Cloud realization và hình học | Chọn realization/seed/coefficients có provenance; với erasure chọn layer, thickness, L_th, LOS spacing; với analog cung cấp attenuation law/factor, đơn vị và noise convention | b(q,t) hoặc post-loss channel; convergence của sampled LOS cần kiểm tra riêng | Drift manuscript [-5,0]m/s có nguồn; layer/threshold/spacing và hệ số quang paper chưa có; không chuyển demo thành paper |
| fs, eta_valid hoặc m0 | Cung cấp m0 có provenance, hoặc fs và eta_valid theo định nghĩa protocol để dẫn xuất m0=fs*dt*eta_valid | n_K và finite-size penalty; baseline m0 phải loại phần cloud đã tính riêng | Các giá trị mission null; key_fraction=.8 không tự là eta_valid; không suy fs từ N_block |
| Mission finite-size/block interpretation | Chọn epsilon và ý nghĩa accumulated block; có thể chọn reference B nếu tác giả công khai quyết định áp dụng | Một penalty trên prefix n_K; không ép N=1e8 cho mọi đường bay | IEEE2025: epsilon_PE/EC/PA mỗi1e-8, epsilon_ref=3e-8 và n_ref=8e7; đây chỉ là reference |
| Greedy lambda | Prior bits/J có provenance hoặc calibration độc lập được cho phép | Tradeoff reward/energy và đường greedy; không tune theo test realization | `greedy.lambda_bits_per_j` và provenance null |
| Security claim scope và quyền chạy base | Chốt research performance approximation, protocol aggregation và quyền cho đúng workload; bổ sung evidence nếu muốn claim mạnh hơn | Quyết định diễn giải, labeling và cổng xuất bản; software PASS không chứng minh security | `finite_size_aware_key_yield_proxy`; paper-mode NOT_RUN, research authorization false; evidence không được đổi bằng lựa chọn văn phong |

Để bắt đầu Phase5B, cần ghi các quyết định trên vào một cấu hình/base-run
protocol riêng được cho phép, bind đúng nguồn/rate/backend/realization và
kiểm lại lifecycle. Phase5A không tự sửa `paper.yaml`, mở cổng hay chạy base.
