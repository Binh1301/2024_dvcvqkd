# Phase A — v43, Eq. (14) trực tiếp

**Đã triển khai và kiểm tra thành phần Phase A; Phase B–F bị chặn.** Đây không phải sweep SKR đã hoàn tất.

## Tham số

| Tham số | Giá trị |
|---|---|
| h_hap_km | 20.0 |
| h_uav_km | 1.0 |
| h_atm_km | 20.0 |
| Dr_m | 0.3 |
| wavelength_m | 1.55e-06 |
| divergence_full_urad | 35.0 |
| jitter_urad | 1.561 |
| sigma_h_m | 0.1 |
| rho_x_m | 0.0 |
| rho_y_m | 0.0 |
| F0 | Infinity |
| tau_zen | 0.92 |
| Cn2_ground | 1e-14 |
| wind_m_s | 21.0 |
| FOV_half_rad | 0.00625 |
| sigma_AoA_rad | 0.0015 |
| AO | OFF |
| phase_noise | OFF |
| xi_ch / xi_det | 0.0186 / 0.005 SNU |
| beta / receiver | 0.95 / homodyne 1D, reverse reconciliation |
| VA / nu_raw | [0.05,10] / [0,0.40] |
| Photon đỉnh | Ghi giá trị; không áp giới hạn 30 theo lựa chọn của người dùng |

Xem `parameters.csv` để phân biệt default PDF và lựa chọn thí nghiệm.
PDF chuẩn có SHA-256 `f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b`; không sửa bản thảo.

## Công thức và phạm vi triển khai

`model.correlation_eq14` chỉ tính

$$Z=2\sqrt{\eta_f}C-\sqrt{2\eta_f\xi_f w}.$$

Không có tìm kiếm Z, endpoint tùy chọn, projection, full-Z grid hoặc nhánh on_cap.
`model.components` tính Eq. (13) với Vmod được truyền rõ ràng cho **fixture kiểm tra thành phần**.
`model.evaluate` chặn tính MI/Holevo/SKR khi luật xác suất, mapping VA hoặc receipt C,w chưa qua gate.
MI dùng helper Gaussian homodyne thực 1D đã có; không dùng MI Shannon hay heterodyne.
Eq. (20) giữ đóng góp atom `xi_det*P0`; không chia cho eta tại zero.

## Phát hiện toán học tại 0 độ

- M0 = `0.9999999998943004486350622973260195331642338644709904774527541969395012226516929532342519165138727146`.
- Tail ổn định trên eta>1 = `0.0000000001056995513649377026739804668357661355290095225472458030604987773483070467317742037127459965639523891`.
- P0 = `0.0001698566765614106550345032258511254724309412750681197687833250899033423561129748491854822030112403506`; active retained mass = `0.9998301432177390379800277941001684076918029231959223576839708718495978802955799783850664343108614743`.
- Sai khác closed/direct moment lớn nhất = `1.11022e-16`.
- Kiểm tra số: **CURRENTLY_VERIFIED_PASS**; tính hợp lệ luật xác suất: **BLOCKED_PDF_SUPPORT_NORMALIZATION**.

Với rho=0, B,d,v,P1 dương, Eq. (10) có mật độ dương trên eta>1. Giới hạn tích phân tới 1
giữ thiếu mass. Tail dương là đặc tính luật, không biến mất nhờ tăng precision hay nới tolerance.
Kiểm tra dừng tại góc 0; 60 góc còn lại không được chạy. File 183 hàng chỉ ghi trạng thái BLOCKED.
`channel_preflight.json` lưu closed form, tích phân độc lập, precision80/110 và định nghĩa atom.
Survival-form được dùng để **kiểm tra tích phân của cùng Eq. (10)**, không thay PDF hoặc moment bản thảo.

Catalog dùng VA=2*nbar, còn PDF in Vmod=nbar/2: trên cùng ensemble, printed Vmod=VA/4.
Không đổi source hay tự đồng nhất hai biến. Mapping vẫn `UNRESOLVED_AUTHOR_REVIEW_REQUIRED`.
Diễn giải X=2Re(alpha) được giữ như convention người dùng yêu cầu, không sửa likelihood in trong PDF.
MB giữ cùng PMF centered và nu_repo=42.5*nu_raw; khác biệt ký hiệu gamma/nu trong PDF được báo riêng.
HV và Gd dùng closure hiện có của repository; bản thảo chưa điền đầy đủ tham chiếu cho hai thành phần này.

## Nguồn và provenance

- Có 33 Uniform và 179 MB trong miền yêu cầu.
- Tái dựng p,alpha, xác minh ensemble hash/payload/source code/settings: 212 PASS; 0 FAILED.
- Receipt hội tụ gắn được với đúng payload: 5.
- Chưa tìm thấy receipt đạt yêu cầu trong các thư mục nguồn đã khảo sát: 207.
- Pool pilot hiện có 80; sau một Uniform còn thiếu sẽ là 81.
- Toàn catalog sau nguồn bổ sung sẽ là 213; chưa tạo nguồn đó.

Hash đúng không tự chứng minh precision hội tụ. `source_identity_audit.json` ghi phạm vi tìm receipt;
không kết luận receipt không tồn tại ở mọi nơi và không tái chạy AP để thay thế bằng chứng thiếu.
Fixed MB giữ VA hex `0x1.9ffff84830112p+0` và hash `01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754`.
`source_catalog_coverage.csv` ghi cả photon đỉnh, nbar, printed Vmod và trạng thái từng nguồn.

## Kiểm chứng và điều kiện tiếp tục

13 tests thành phần/gate: CURRENTLY_VERIFIED_PASS. Xem `unit_tests.json` và `unit_tests.log`.
Các fixture tổng hợp không phải kết quả HAP–UAV, không dùng chọn baseline hoặc báo SKR dương.
`gate.json` ghi `phase_B_ready=false`; source generation, optimization, SKR sweep và figure đều NOT_RUN.
Phases B–F được CLI từ chối trước mọi tính toán; chưa triển khai source_job/renderer vì dependency này.

Trước khi tiếp tục cần: (1) tác giả giải quyết support/normalization của Eq. (10),
(2) khóa mapping VA–Vmod, (3) cung cấp/xác thực receipt hội tụ nguồn còn thiếu và kiểm tra lại lifecycle.
Mọi sửa công thức chỉ là đề xuất riêng và cần phê duyệt rõ ràng; package này không áp dụng correction nào.

`UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` và sai khác frozen hash được giữ.
Không có kết luận finite-key/composable security hoặc khả thi phần cứng từ các tests này.

Chạy kiểm chứng chỉ đọc từ project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_20261023/run.py --verify-only
```

Không chạy lại producer Phase A đã seal; verifier không nhập evaluator, không tính lại nguồn hoặc kênh.
