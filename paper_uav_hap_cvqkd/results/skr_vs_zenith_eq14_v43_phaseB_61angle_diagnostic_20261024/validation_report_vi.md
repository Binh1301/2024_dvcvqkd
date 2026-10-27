# Kiểm chứng sweep SKR theo 61 góc zenith

**DIAGNOSTIC_ONLY — hoàn tất khảo sát catalog lịch sử; strict Phase B vẫn BLOCKED.**

Lưới lấy nguyên `/angles_deg` của `results/skr_vs_zenith_eq14_v43_20261023/protocol.json`: 0–60°, bước 1°. Chín góc 0, 5, 10, 15, 20, 30, 40, 50, 60° đều thuộc lưới. Không thêm điểm hoặc fit nghiệm ngoài lưới.

Tổng **12,932** cặp nguồn–góc, gồm **1,908 tái dùng nguyên giá trị** và **11,024 evaluation SKR mới**; 9 context kênh tái dùng, 52 context mới. **C,w mới: 0; source job: 0.** Thời gian phần sweep: 315.20 s (không gồm preparation/validation/figures).

Pool cố định ở mọi góc: 212 identity, gồm 33 Uniform và 179 MB trong VA∈[0.05,10], ν_raw∈[0,0.40]. Optimized MB chứa cả Uniform ở ν=0 và Fixed MB. Uniform và MB là best-tested trong catalog hiện có, chưa phải tối ưu liên tục/toàn cục.

| Scheme | Raw SKR lớn nhất (bits/use) | Góc | Điểm dương đã lấy mẫu | Điểm dương cuối | Điểm không dương đầu | Khoảng đổi dấu quan sát |
|---|---:|---:|---|---:|---:|---|
| Uniform | -0.0307471464632798 | 60° | Không có | — | 0° | Không quan sát |
| Fixed MB | 6.52237706649239e-05 | 0° | 0–5° (6 điểm) | 5° | 6° | [5, 6]° |
| Optimized MB | 0.000796087808086127 | 0° | 0–15° (16 điểm) | 15° | 16° | [15, 16]° |

Ở 0°, Optimized MB cao hơn Fixed MB khoảng 0.000730864037421203 bits/use. Trên lưới này, số điểm dương tăng từ 6 (Fixed MB) lên 16 (Optimized MB); mọi điểm MB dương được chọn dùng cùng VA=1.358333319784304, ν_raw=0.30. Các lần đổi nguồn MB ở 48°, 56°, 60° đều thuộc miền raw SKR âm.

Các khoảng trên chỉ kẹp sự thay đổi dấu giữa hai góc đã tính; không chứng nhận giới hạn hoạt động liên tục. Raw SKR âm được giữ nguyên. `K_operational=max(0,K_raw)` là cột báo cáo riêng, không dùng để xếp hạng hoặc sửa kết quả.

Trạng thái số: {'CURRENTLY_VERIFIED_PASS': 12932}. Candidate dương: 47; âm: 12885; bằng 0: 0. Không loại bỏ âm hoặc evaluation thất bại; giá trị chưa tính được để trống.

## Tham số MB được chọn

Fixed MB giữ VA=1.6249995399703647 (`0x1.9ffff84830112p+0`), ν_raw=0.25, ν_repo=10.625, C=1.2135302410613147, w=2.856493276891121e-10. Chỉ nguồn cố định; Z, MI và Holevo tính theo góc.

| Góc bắt đầu dùng nguồn | VA | ν_raw | Ensemble hash | Evidence |
|---:|---:|---:|---|---|
| 0° | 1.3583333197843039 | 0.3 | `b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214` | INSUFFICIENT_EVIDENCE |
| 48° | 1.1166663599802431 | 0.25 | `7ed99ce34e3841f9d11dade06615f72b69cbee55a8d0dd4bb04422d7dc440263` | INSUFFICIENT_EVIDENCE |
| 56° | 0.93888887985620251 | 0.3 | `9cc66c29b7bfadcc4dfa74e69b84c68a23ed3db1f1a8e631b0441378414428df` | INSUFFICIENT_EVIDENCE |
| 60° | 0.74166151514903278 | 0.2 | `b0fad3e3ddfcdbefed5b3689a86548868e0a6f3147326686a3026299504cabed` | INSUFFICIENT_EVIDENCE |

Mỗi hàng áp dụng đến trước hàng kế tiếp trên lưới đã lấy mẫu; bảng đủ 61 góc nằm trong `best_scheme_by_angle.csv`. Chuyển nguồn rời rạc có thể làm tham số nhảy. Không suy ra shaping gain ở cùng VA từ hai catalog có độ phủ năng lượng khác nhau.

| Góc | Fixed MB raw K | Optimized MB raw K | Chênh lệch | VA tối ưu MB | ν_raw tối ưu MB |
|---:|---:|---:|---:|---:|---:|
| 0° | 6.52237706649e-05 | 0.000796087808086 | 0.000730864037421 | 1.3583333197843 | 0.3 |
| 5° | 1.25954966036e-05 | 0.000728137251483 | 0.00071554175488 | 1.3583333197843 | 0.3 |
| 10° | -0.000161496046951 | 0.00051043965407 | 0.000671935701021 | 1.3583333197843 | 0.3 |
| 15° | -0.000505180635808 | 0.000101924804602 | 0.00060710544041 | 1.3583333197843 | 0.3 |
| 20° | -0.00109659623706 | -0.00056392013471 | 0.000532676102354 | 1.3583333197843 | 0.3 |
| 30° | -0.00345288797511 | -0.00303172844311 | 0.000421159531998 | 1.3583333197843 | 0.3 |
| 40° | -0.00814864387275 | -0.00766078076894 | 0.000487863103808 | 1.3583333197843 | 0.3 |
| 50° | -0.0156625713507 | -0.0146568743963 | 0.00100569695438 | 1.11666635998024 | 0.25 |
| 60° | -0.0250475554036 | -0.0223120602927 | 0.00273549511091 | 0.741661515149033 | 0.2 |

## Công thức, cấu hình và bằng chứng

Giữ nguyên các hàm canonical đã dùng ở chín góc: [0,1] cho Eq. (10), (18)–(20), atom tại 0 và noise của atom được giữ; bỏ phần ngoài support trong evaluator theo quyết định tác giả, không clip/renormalize/đổi PDF. VA=Vmod=2 nbar, X_A=2 Re α; ν_repo=42.5 ν_raw. Eq. (14) trực tiếp `Z=2 sqrt(eta_f) C-sqrt(2 eta_f xi_f w)`, homodyne MI rời rạc, covariance/Holevo Eq. (13) và raw K=0.95 MI−Holevo không thay đổi. Không tìm Z interval hoặc tối ưu Z.

Cấu hình chung: HAP/UAV=20/1 km; Dr=0.30 m; λ=1550 nm; divergence full-angle=35 µrad; jitter mỗi trục=1.561 µrad; position SD=0.10 m; boresight=0; F0=∞; τzen=0.92; Cn²(0)=1e−14 m^(−2/3); wind=21 m/s; h_atm=20 km; FOV half-angle=6.25 mrad; AoA SD=1.5 mrad; ξch=0.0186; ξdet=0.005; β=0.95; AO/phase noise OFF, homodyne/RR. Đây là baseline thí nghiệm riêng, không thay default PDF.

Deficit xác suất được lưu theo từng góc: [1.63919820461e-12, 1.05699551365e-10]. Đây là xấp xỉ truncation đã được chấp nhận; không tuyên bố PDF bị cắt được chuẩn hóa toán học.

Phân loại 212 nguồn giữ nguyên: {'INSUFFICIENT_EVIDENCE': 190, 'VERIFIED_EXACT': 21, 'VERIFIED_BY_ALTERNATIVE_EVIDENCE': 1}. 11,590 hàng dùng nguồn INSUFFICIENT_EVIDENCE. Evidence của các candidate dương: {'INSUFFICIENT_EVIDENCE': 47}. Subset chỉ có evidence đầy đủ có 0 điểm được chọn có raw K dương. Fixed MB và các nguồn Optimized MB được chọn vẫn thiếu evidence hội tụ. Evaluation SKR thành công không bổ sung bằng chứng hội tụ C,w, cũng không chứng minh C,w sai.

**Uniform còn thiếu đúng nguồn** ν_raw=0, VA=1.6249995399703647, VA_hex=`0x1.9ffff84830112p+0`, ensemble hash `421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7`. Không chạy lại job timeout, không dùng VA làm tròn, C,w MB hoặc nội suy. Vì vậy không thể kết luận Uniform tối ưu toàn miền hay mọi Uniform đều không có SKR dương.

## Kiểm chứng và giới hạn

235 đối chiếu MI/covariance độc lập: 35 tái dùng, 200 mới, đều PASS. Các kiểm tra mới đối chiếu MI adaptive integration và GH256, spectrum covariance 4×4, conditional covariance và Eq. (13)/(14) ở 160 digits. Mọi primary pair dùng GH64/128 và components 80/110 digits như baseline. Tolerance MI=2e−10, Holevo/spectrum=2e−11. Không sửa eigenvalue/Z hoặc điều kiện miền xác định.

Sai khác MI độc lập lớn nhất=1.36696e-15; spectrum=6.21725e-15; raw-rate residual=0. 3 focused checks kiểm tra đọc số từ CSV, nested ranking/negative/failure retention, grid/pool identity và canonical function reuse đã PASS trước sweep.

Frozen-spec hash hiện tại khác historical hash như hồ sơ readiness đã giải thích; versioned experiment_spec_v1 và cả hai reference vẫn được kiểm tra, không bypass/ghi đè frozen spec. Xem `protocol.json`, `baseline_verification.json`, `artifact_integrity_report.md` và `verification.json`.

**Strict Phase B readiness: BLOCKED.** Hai nhóm prerequisite vẫn là 73 nguồn pilot hiện có thiếu evidence hội tụ đầy đủ (gồm Fixed MB), và một Uniform đúng VA còn thiếu payload/receipt. Đây là sweep diagnostic được tác giả cho phép riêng, không phải hoàn tất strict pilot, certification, tối ưu toàn cục hoặc kết luận publication-grade/composable security. `UNVALIDATED_SECURITY_MODEL` và `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` giữ nguyên.

Đầu ra: `diagnostic_skr_61_angles.csv` (12.932 candidate), `best_scheme_by_angle.csv` (183 hàng, 3 scheme × 61 góc), `source_pool.csv`, `independent_validation.csv`, bốn PNG 350 dpi và PDF vector tương ứng. Không có training, final-test/held-out, source generation hoặc production/manuscript/cache/frozen-spec edit.
