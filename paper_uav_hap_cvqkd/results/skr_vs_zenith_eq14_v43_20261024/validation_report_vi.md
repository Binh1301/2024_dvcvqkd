# Phase A — các quy ước được tác giả phê duyệt ngày 24/10/2026

**Hai vướng mắc về truncation và VA–Vmod đã được giải quyết cho thí nghiệm số này. Kiểm tra tập trung đạt; Phase B chưa sẵn sàng do các dependency còn lại.**

Trạng thái máy đọc: `gate.json`, `phase_A_model_conventions_ready=true`, `phase_B_ready=false`.
Bản cập nhật nằm trong namespace mới; package Phase A ngày 23/10 giữ nguyên như một snapshot lịch sử.
Không diễn giải trạng thái BLOCKED của snapshot cũ thành gate hiện hành cho hai quy ước vừa được duyệt.

## Quy ước đang dùng

| Nội dung | Implementation hiện tại |
|---|---|
| Luật fading | Eq. (10) nguyên bản; atom tại zero giữ riêng |
| Moment | Eqs. (18)–(20) trên [0,1]; bỏ phần ngoài khoảng trong evaluator |
| Thiếu hụt xác suất | Diagnostic; không còn là điều kiện chặn vì chuẩn hóa chính xác |
| Chuẩn hóa PDF | Không clip, chia cho retained mass, đổi luật hoặc chuyển tail vào atom |
| Biến nguồn | `VA = Vmod = 2 sum(p*abs(alpha)**2)` |
| Homodyne | `X_A = 2 Re(alpha)`; phương sai likelihood `1 + eta_f*xi_f` |
| Correlation | `Z = 2*sqrt(eta_f)*C - sqrt(2*eta_f*xi_f*w)` |
| Tối ưu Z | Không có; không interval, endpoint, cap, projection hoặc thay công thức |
| MI / covariance / Holevo | Giữ nguyên helper homodyne 1D và code Eq. (13) của Phase A trước |

`model.py` tái sử dụng trực tiếp cùng function object `correlation_eq14` và `components`
từ package trước. Chỉ thay điều kiện chấp nhận truncation và khóa mapping VA–Vmod.
`printed_normalization` trong protocol chỉ ghi lại ký hiệu `Vmod=nbar/2` của PDF;
evaluator không sử dụng nó. Bản thảo không được sửa.

Cụ thể, với `mh=<sqrt(eta)>`, `m1=<eta>` và retained mass `M0`:

```text
eta_f = mh**2
N = (m1 - eta_f)*VA + xi_ch*m1 + xi_det*M0
xi_f = N/eta_f
V = 1 + VA
W = 1 + eta_f*VA + N
K_raw = beta*I_AB - chi_BE
```

Giữ `xi(eta)=xi_ch+xi_det/eta` và đóng góp atom `xi_det*P0` trong Eq. (20).
Không thay `xi_det*M0` bằng `xi_det`; không chia trực tiếp cho eta tại zero.
Trạng thái `law_mathematically_valid=false` vẫn được giữ: luật bị cắt không được tuyên bố chuẩn hóa.
Chấp nhận này giới hạn ở baseline đã khóa, không tự áp dụng cho cấu hình khác.

## Tham số

| Tham số | Giá trị |
|---|---|
| HAP / UAV; khoảng cách | 20 / 1 km; `L=19 sec(zeta)` km |
| Đường kính thu / bước sóng | 0.30 m / 1550 nm |
| Divergence full-angle / F0 | 35 µrad / vô cực |
| Jitter mỗi trục / position SD mỗi trục | 1.561 µrad / 0.10 m |
| Boresight | 0 |
| Tau zenith / Cn² ground / wind | 0.92 / 1e-14 m^(-2/3) / 21 m/s |
| FOV half-angle / AoA SD | 6.25 / 1.5 mrad |
| xi_ch / xi_det / beta | 0.0186 / 0.005 / 0.95 |
| Receiver / reconciliation | Homodyne / reverse, asymptotic |
| AO / additional phase noise | OFF / OFF |
| Miền nguồn | VA ∈ [0.05,10], nu_raw ∈ [0,0.40]; không thêm giới hạn photon đỉnh 30 |

PDF có default aperture 8 cm, divergence 233 µrad, jitter 15.61 µrad,
position SD 1 m, zenith 30°. Những khác biệt trên là lựa chọn thí nghiệm đã duyệt,
không phải sửa default PDF. HV và Gd vẫn dùng closure của repository đã công bố
trong audit trước; không coi phần tham chiếu còn thiếu trong PDF là đã đầy đủ.

## Kiểm tra tập trung

`focused_tests.json`: **9/9 tests đạt**. Có một assertion ban đầu so sánh bằng tuyệt đối
hai phép xuất binary64 của atom noise, khác nhau một ULP (~1.06e-22).
Đã sửa riêng assertion xuất số đó và chạy lại đúng test bị ảnh hưởng; tám test còn lại
được xác nhận AST không đổi. Không sửa công thức, giá trị hay tolerance scientific.
Lần đầu được giữ trong `attempt_01/`; lần chạy lại trong `focused_test_retry.json`.

- Tái dựng và xác minh ensemble/payload/settings/implementation cho **212 nguồn: 33 Uniform, 179 MB**.
  Cả hai họ đều thỏa `2*nbar = VA = Vmod` và moment quadrature `E[X_A²]=VA` trong tolerance 2e-12;
  PMF, tâm, đối xứng và ensemble hash vẫn khớp. Không tính lại C,w.
- Tính lại context tại **0° và 60°**, closed form, tích phân độc lập và precision 80/110 digits.
  Đây là hai điểm kiểm tra, không phải pilot chín góc hay sweep 61 góc.
- Hai fixture đầu cuối tại 0°: Uniform `(VA=0.0525, nu_raw=0)` và MB `(VA=4.75, nu_raw=0.17)`.
  Chọn các nguồn có receipt đã xác minh để kiểm tra pipeline; không lựa chọn theo SKR.
  MI GH64/128, tích phân độc lập, 256 symbol/16 mức quadrature và X/P phù hợp;
  Eq. (14), entropy 80/110 digits và symplectic spectrum độc lập phù hợp.
  Cả hai K_raw âm được giữ nguyên trong `focused_evaluator_checks.json`; không kết luận tối ưu hay khả thi.
- Gate vẫn từ chối context lỗi số, context sai protocol, nguồn bị sửa, covariance ngoài miền,
  công thức Z khác và việc dùng nguồn thiếu receipt như đã hội tụ.

| Zenith | M0 | Thiếu hụt xác suất / tail ngoài [0,1] | `<eta xi(eta)>` |
|---|---|---|---|
| 0° | 0.9999999998943004 | 1.056995513649377e-10 | 0.009279122753547968 |
| 60° | 0.9999999999974114 | 2.5885985333934575e-12 | 0.006347507011268344 |

Thiếu hụt ở 0° lớn hơn ngưỡng diagnostic cũ 1e-10 nhưng **không chặn** evaluator mới.
Các moment 0° bằng giá trị đã lưu trước đây; không có phép renormalization ẩn.
Hai điểm này không chứng minh mọi nguồn/góc đều physical: pilot vẫn phải ghi lỗi
covariance tại Z Eq. (14) nếu có, không sửa Z để vượt gate.

## Điều tra receipt C,w riêng

Xem `receipt_investigation.json`, `receipt_root_cause.json`, `source_catalog_coverage.csv`
và danh sách chính xác `pilot_evidence_gaps.csv`.

| Phạm vi | Có receipt hội tụ được xác minh | Chưa tìm được receipt đầy đủ |
|---|---:|---:|
| Catalog 212 nguồn hiện có | 21 | 191 |
| Pool pilot 80 nguồn hiện có | 6 | 74 |

Tìm thêm **16 receipt** trong `source_result_*.json`. Lần tìm trước chỉ nhận
`source_receipts/*.json`, nên báo 5/212. Lần này đọc 93 file bằng chứng trong 15 root
tạo nguồn và kiểm tra thêm bốn artifact legacy được payload dẫn tới.
Không có receipt đã bound nhưng mâu thuẫn C,w hoặc precision ladder trong tập được tìm thấy.

Hai schema receipt đều được kiểm tra hash payload, ladder 1050/1250/1450,
support 256, resolved, eigenvalue dương và C,w ở từng mức khớp payload.
Không nới tiêu chí hội tụ để tăng số nguồn PASS.

Nguyên nhân có thể truy vết: `scripts/run_exact_mb_test2.py:256–270` lấy diagnostic
nhưng chỉ ghi C,w, route và support vào cache, không lưu `fallback_rows`.
`src/cvqkd/gram_moments.py:184–188` yêu cầu worker trả `FULL_SUPPORT_CONVERGED`
trước khi chấp nhận fallback. Điều này hỗ trợ provenance của quá trình tạo nguồn,
nhưng không tái tạo được các hàng precision đã bị bỏ khỏi file.
187/191 nguồn thiếu receipt ghi `FRESH_EXACT_EVALUATION`; bốn nguồn còn lại là legacy import.
Bốn artifact legacy vẫn khớp C,w và hash đã ghi khi dùng đúng biểu diễn CRLF;
hash bytes hiện tại khác do line endings, và chúng cũng không chứa full ladder.
Không sửa các file đó hoặc giả lập receipt mới từ giá trị cuối.

**Thiếu receipt không phải bằng chứng C,w sai.** Tất cả 212 payload/ensemble hiện có
vẫn được xác minh danh tính. Với 191 nguồn còn thiếu bằng chứng hội tụ lưu trên đĩa,
giữ `CONVERGENCE_EVIDENCE_NOT_LOCATED` và `NOT_CLASSIFIED_INCORRECT`.
Đây là kết quả trong phạm vi đã tìm, không khẳng định receipt không tồn tại ở nơi khác.

Fixed MB vẫn đúng ensemble `01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754`,
VA `1.6249995399703647` (`0x1.9ffff84830112p+0`), nu_raw `0.25`,
C `1.2135302410613147`, w `2.856493276891121e-10`.
Danh tính này đạt; receipt đầy đủ của chính nguồn đó chưa tìm được.

## Điều kiện tối thiểu trước Phase B

| Dependency còn lại | Nguyên nhân chính xác | Việc tối thiểu cần làm |
|---|---|---|
| Receipt của pilot | 27 Uniform + 47 MB trong 80 nguồn hiện có chưa có ladder bound đầy đủ, gồm Fixed MB | Khôi phục/xác thực receipt cho 74 nguồn trong `pilot_evidence_gaps.csv`. Nếu không còn receipt, tác giả cần quyết định riêng tiêu chuẩn bằng chứng cho diagnostic hoặc duyệt kiểm tra hội tụ bổ sung có ngân sách; chưa áp dụng ngoại lệ nào. Không cần xử lý cả 191 nguồn của catalog để bắt đầu pilot. |
| Uniform còn thiếu | Không có nguồn tại VA binary64 chính xác của Fixed MB, nu_raw=0 | Tạo đúng một nguồn đó với receipt trong cache mới khi các gate cho phép. Không thay bằng VA=1.625 hoặc C,w của MB. |
| Frozen-spec provenance | `docs/FINAL_MODEL_SPEC.md` hiện hash `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`, khác hash lịch sử trong AGENTS.md `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1` | Chốt provenance/hash tham chiếu hoặc ngoại lệ được tác giả cho phép cho pilot cô lập. Không tự sửa hoặc khôi phục frozen spec. Hai quyết định mới không tự giải quyết sai khác hash này. |
| Orchestration Phase B | Package hiện chỉ có Phase A và guard B–F | Sau khi dependency dữ liệu/provenance được giải quyết, triển khai job nguồn còn thiếu và runner chín góc với 81 nguồn, checkpoint và timing. |

Ngân sách 20 source-job attempts trong kế hoạch không mặc nhiên đủ để tính lại 74 nguồn
thiếu receipt. Không tự tăng ngân sách, giảm pool, bỏ Fixed MB hoặc nới gate bằng chứng.
Không có blocker mới về Eq. (10) normalization hay mapping VA–Vmod trong thí nghiệm này.

## Bảo toàn và kiểm chứng

`verification.json`/`artifact_manifest.json` kiểm tra các file bản cập nhật và 9,263 file lịch sử
được bảo vệ, gồm toàn bộ package Phase A cũ. Producer mới không ghi vào production,
frozen spec, PDF hoặc cache nguồn cũ. Chỉ cập nhật namespace mới và các ledger trạng thái.
Không tạo CSV sweep mới để lẫn với 183 hàng BLOCKED của snapshot trước.

Từ project root, kiểm tra chỉ đọc:

```powershell
.venv/Scripts/python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_20261024/run.py --verify-only
```

Không chạy lại producer đã seal. B–F bị CLI từ chối, không có source job, tối ưu,
pilot, sweep 61 góc, hình mới hoặc đánh giá held-out/publication.
Giữ `UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`
và `ObjectiveC USER_STOPPED`. Numerical PASS ở đây không phải chứng minh security.
