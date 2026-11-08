# Kiểm toán cấu hình paper theo nguồn

Ngày 2026-11-07. Phạm vi hoàn tất: xác định nguồn, điền phần tham số có bằng
chứng, kiểm thử và kiểm tra từ chối cấu hình thiếu đầu vào. Thí nghiệm paper:
**NOT_RUN**. Không có giả định kịch bản mới được điền để vượt validation.

## Các tài liệu thực sự được nhận diện

1. PDF địa phương `C:/Users/admin/Downloads/Energy_Minimization_for_Wireless_Communication_With_Rotary-Wing_UAV.pdf`:
   IEEE TWC 2019, 17 trang, DOI 10.1109/TWC.2019.2902559. Table I nằm ở PDF
   trang 14 / trang tạp chí 2342. Công suất ở Eq.(12), hằng số ở Eq.(64), không
   phải Eq.(6)/(61). Table I dùng W=20 N, R=.4 m, A=.503 m², Utip=120 m/s,
   v0=4.03 m/s, d0=.6; Section V (PDF p.11 / p.2339) dùng vmax=30 m/s.
2. Bản tác giả **arXiv:1804.02238v1, 6 April 2018**, 31 trang:
   <https://arxiv.org/pdf/1804.02238v1>. Bản này có đúng bộ được yêu cầu:
   W=100 N, A=.79 m², Utip=200 m/s, d0=.3, v0=7.2 m/s. Nguồn: Table I PDF
   p.27; Eq.(6) p.6; Eq.(61) p.27; vmax=60 m/s tại Section V p.22.
   `paper.yaml` dùng bộ này và ghi rõ phiên bản, không gắn sai cho Table I IEEE.
3. Paper B cho **nguồn mô hình quang của lookup** được xác định từ liên kết
   provenance của producer, thay vì đoán theo tên file/timestamp:
   `paper_uav_hap_cvqkd/results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf`.
   Tên bài: *Performance Analysis of Probabilistically Shaped CV-QKD in
   Free-space HAP-to-UAV Systems*. SHA256:
   `f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b`.
   Đây là bản 4 trang, metadata 2026-10-23 02:06:09 UTC, phần abstract và
   optimization còn placeholder. Không coi đó là một công bố hoàn chỉnh.
4. Bản **current trajectory manuscript** là `2026__Binh_s_work__Copy_ (17).pdf`,
   4 trang, metadata 2026-11-06 17:40:53 UTC; chứa P1/P2, accumulated finite-size
   approximation và DP. Không gộp nội dung bản này với Paper B quang thành một
   nguồn duy nhất. Bản Copy (16) chỉ 3 trang. Bản Binh (40) có cùng tên họ tài
   liệu quang nhưng không được tự thay thế file mà producer gắn hash.
5. `Manuscript (3).pdf` thực tế là *Heterogeneous MADRL for Joint UAV Deployment
   and Optical IRS Allocation in Air-Ground Integrated Networks*. Nó chỉ là
   nguồn tham khảo hình mây; không phải Paper B CV-QKD.

Inventory lưu 84 PDF ứng viên cùng hash/metadata/trích trang đầu; so sánh nội
dung trong `source_inventory.json`, `cvqkd_candidate_comparison.json`. Bản A
IEEE có Table I dạng ảnh nên đã render và đọc trực quan. Bản preprint được
đọc qua web; tải PDF bằng shell bị BLOCKED_BY_ENVIRONMENT (WinError 10013),
do đó không bịa local byte hash cho bản preprint chưa tải về.

## Tham số đã điền và phép tính

| Đại lượng | Giá trị | Nguồn/phân loại |
|---|---:|---|
| P0 | 580.65 W | Dẫn xuất Eq.(61), A=.79 m² |
| Pi | 790.6715228132718 W | Dẫn xuất Eq.(61), W=100 N, k=.1 |
| P_hover | 1371.321522813272 W | P0+Pi |
| v0 dùng mô phỏng | 7.2 m/s | Table I preprint |
| v0 tính từ W,rho,A | 7.187922934666108 m/s | Dẫn xuất; không âm thầm thay giá trị bảng |
| vmax | 60 m/s | Section V preprint |
| UAV altitude | 1,000 m | Paper B p.3 Section IV |
| HAP altitude | 20,000 m | Paper B p.3 Section IV; metadata vì thiếu qH,x/y |
| Vùng / slot | 2,000×2,000 m / 1 s | Current manuscript p.1 Section I-A |
| Mây / cloud display | (-5,0) m/s / 50×50 cells | Current p.1 I-D, p.2 Fig.3 |

Không trộn bộ 580.65/790.67 W với bộ demo 79.86/88.63 W. Các tham số rho, s,
A, Utip, v0, d0 và vmax được điền đồng bộ trong `propulsion`. Không nhập UAV
altitude 100 m, RF bandwidth hoặc communication power từ bài rotor. Các điểm
làm tròn (A so với pi R², v0) và khác biệt ký hiệu k với kappa được ghi rõ.

Các giá trị 0.30 m aperture, 35 µrad **full-angle**, 1.561 µrad jitter mỗi trục,
.10 m UAV jitter mỗi trục, xi_ch=.0186, xi_det=.005, beta=.95 được xác nhận
trong `execution_physical_protocol.json` của receiver30. Chúng là **repository
overrides**, không phải trích dẫn bảng mặc định của B. Bản B in aperture .08 m,
full-angle233 µrad, jitter15.61 µrad, sigma_h1 m tại p.3. Detector excess noise
không đồng nghĩa electronic noise; beta không phải detector efficiency.

Metadata `verified_context` giữ các dữ kiện đã kiểm tra nhưng parser không dùng
nó để tự điền đầu vào còn thiếu. Tất cả 77 dòng provenance, đơn vị, vị trí nguồn
và mức phù hợp nằm trong `parameter_provenance.md` và JSON tương ứng.

## SKR có tồn tại nhưng chưa đủ điều kiện paper

`paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/skr_map.csv` và NPZ
chứa 51×51=2,601 **node samples**, phủ x,y từ0 đến2,000 m. Đây không phải grid
50×50 **cell** mây. MB raw range:
0.0007470670338268481–0.0007960878080861267 bits/use; không có rate thiếu hoặc
tọa độ trùng. Tất cả 2,601 điểm có numerical status CURRENTLY_VERIFIED_PASS,
nhưng source evidence **INSUFFICIENT_EVIDENCE**. Đây là finite-catalog maxima,
không chứng nhận tối ưu liên tục theo nu/VA hay security lower bound của fading.

Producer dùng HAP20/UAV1 km, homodyne real1D, xi_ch/xi_det như protocol,
direct Eq.(14), original Eq.(10) retained0..1 law và source catalog đã lưu.
Giữ raw signed rate; potential=max(0,raw) là cột riêng. Nu raw domain0..0.4,
VA .05..10 là domain catalog, không tự biến thành constraint vật lý. Không
đổi chuẩn hóa VA=2*nbar của producer thành Vmod=nbar/2 in trong B: khác biệt
này phải được công khai. Chi tiết/hashes trong `skr_lookup_audit.json`.

CSV gốc không có cột `skr_bits_per_use`; NPZ gốc dùng mesh fields, khác schema
generic loader (`points`,`rates`). Nếu sau này được chấp thuận sử dụng, cần
adapter lossless có provenance và quyết định rõ raw/potential; không sửa dữ liệu
gốc. Hiện `lookup.file/sha256/provenance` vẫn null để không tự nhận dữ liệu này
là paper-approved. Không tái sinh SKR vì có input/gate blockers độc lập.

## Đầu vào thật còn thiếu

- q0 và horizontal HAP coordinates: không suy q0 từ tâm hình hoặc endpoint RF.
- Emax (propulsion allocation) hoặc reference hover duration được tác giả chọn.
  Chỉ có thể dùng Emax=P_hover*T_ref sau khi T_ref được khai báo là giả định.
- fs, eta_valid và epsilon: không có giá trị số trong nguồn được chọn. Không
  đặt eta_valid=1, không coi xi_ch là security epsilon. Vì thế m0 chưa tính được.
- Cloud realization được chấp thuận, altitude, thickness, Lth và LOS sampling
  resolution. Figure generator có400 kernels, seed42, clip15 mg/m³, threshold8,
  nhưng đó là minh họa, không phải mô hình khí tượng calibrated. Layer5–7 km
  trong demo không được chuyển vào paper.
- Waypoint graph/spacing, prediction horizon và prior lambda/calibration rule.
- SKR input được chấp thuận và giải quyết source/security evidence phù hợp.

Giữ nguyên công thức finite-size tích lũy một lần ở terminal. Không thay thành
slotwise penalty hoặc thông lượng cộng đơn giản. Gộp các trạng thái kênh là
performance approximation; chưa chứng minh composable security.

## Kiểm chứng và tình trạng thực thi

- Baseline suite trước chỉnh sửa: **34 passed** thực chạy trong lượt này.
- Sau bổ sung: **42 passed** = 34 cũ + 8 mới, không xóa/yếu hóa test cũ.
  Bao gồm source rotor, P0/Pi/hover, energy feasibility, QKD units, valid-signal
  count, altitude/LOS geometry và partial source-config loading/fail-closed.
  Các test fixture đặt epsilon/m0/layer chỉ là unit tests, không phải paper inputs.
- Exact DP vs brute force của suite cũ vẫn qua.
- `python -X utf8 scripts/verify_paper_configuration.py` kiểm công suất dương,
  hover, displacement infeasibility và numerical lower-envelope refinement trên
  301 mean speeds với 2001/4001/8001 velocity nodes. Kết quả trong
  `configuration_validation.json`; không suy rộng thành chứng nhận continuum.
- Kiểm tra cấu hình dừng đúng trước graph/mission với missing inputs; paper
  mission **NOT_RUN**. Không chạy assumptions-based scenario hoặc baseline
  performance sweep khi thiếu các đầu vào nêu trên.
- 138 file kết quả trước đó được kiểm SHA256 và giữ nguyên. Demo YAML và runtime
  source/parser không đổi. Frozen hash vẫn
  df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15, khác hash
  lịch sử trong AGENTS; không chỉnh/khôi phục frozen file.
- NOT_READY_FOR_PUBLICATION_SCALE_RUNS, strict Phase B false và security status
  không được nâng. Không training/held-out/final-test, source generation, MB
  reoptimization, threshold/baseline certification, commit hoặc push.

Gói bằng chứng: `../results/paper_configuration_audit_20261107/`. Bước tiếp theo
là cung cấp/phê duyệt các giá trị còn thiếu và xử lý source/lifecycle blockers;
không thể gọi paper_verified là thành công chỉ bằng cách điền số giả định.
