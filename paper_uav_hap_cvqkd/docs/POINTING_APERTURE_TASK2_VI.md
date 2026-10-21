# Task 2: kiểm chứng pointing trước khi tìm SKR dương

Ngày 2026-10-17. Trạng thái **BLOCKED_POINTING_MODEL_INCONSISTENCY**.
Chỉ giai đoạn kiểm chứng quang học hoàn tất; toàn bộ Task 2 chưa hoàn tất.
Không chạy tìm kiếm SKR, tối ưu nguồn, AP, training hoặc test/held-out.

## Cấu hình và phương pháp

L=21939.3102292 m, h_HAP=20000 m, h_UAV=1000 m; sec(zeta)=L/19000.
Dr=0.55 m, full-angle divergence=10 urad, wavelength=1.55e-6 m,
sigma_h=1 m, theta_jt=15.61 urad mỗi trục. tau_zen=0.92 giữ theo reference
được cung cấp; default.yaml để null nên không được diễn giải thành default.
HV dùng wind=21 m/s, Cn2(0)=1e-14, F0=infinity. AoA giữ sigma_o=.0015 rad,
FOV half-angle=.00625 rad; P0=.00016985667656141038 không bị bỏ.

Script độc lập tính HV/Gd từ primitives, scale integrands nhỏ trước quad để
tránh absolute tolerance chi phối. Không gọi production geometry/broadening
helpers. Production LiteralChannel chỉ được dùng trong nhánh tái dựng luật cũ
để truy nguồn chênh lệch; đây không phải kiểm chứng độc lập chính luật cũ.

Reference khẩu độ dùng
Hp(r)=CDF_ncx2(4a²/w²; df=2, nc=4r²/w²), a=Dr/2.
Đối chiếu riêng tích phân Bessel ổn định tại r=0,.1,.275,.5,1,2 m và tích phân
Rayleigh của displacement; các số cực nhỏ ở tail chỉ kiểm absolute residual,
không tuyên bố relative accuracy tại tail. Giới hạn centered và công thức
mean đều được kiểm tra, cho hai beam widths. 16 numerical checks PASS;
checkpoint wL và mean diffraction-only cũng thỏa assert của script.

## Kết quả

| Đại lượng | Giá trị |
|---|---:|
| w0 m | 0.0986760647169751 |
| wL diffraction-only m | 0.1475476163187859 |
| Gd | 0.029985462263114982 |
| w_eff broadened m | 0.14974341909718897 |
| raw Rytov variance | 0.05396207779616573 |
| sigma_s m | 1.0570182137187947 |
| eta_atm | 0.9082089654181673 |
| mean Hp diffraction-only | 0.033118239551900235 |
| mean Hp broadened Gaussian reference | 0.03311350682836657 |
| mean Hp equivalent-Gaussian approximation | 0.2777137319309177 |
| ratio approximation/reference | 8.386720662669747 |

Checkpoint người dùng wL≈.14755 m và mean Hp≈.03312 được xác nhận.
Mean identity khớp radial quadrature trong 1.4e-17; CDF/Bessel residual lớn
nhất tại các điểm đã kiểm dưới 4e-16. Đây là numerical accuracy của mô hình
Gaussian đã nêu, không phải physical calibration của turbulence broadening.

Với v=sqrt(pi)a/(sqrt(2)w_eff), luật cũ có A0=erf(v)^2≈.99773397,
w_eq≈1.31292160 m và Hp_approx=A0 exp(-2r²/w_eq²).
Mean của nó là A0/(1+4sigma_s²/w_eq²)≈.27771373. Nó còn cho thu nhận đáng kể
khi beam center cách aperture rất xa, khác rõ tích phân tròn. Sai khác nhỏ
giữa centered A0 cũ và exact centered≈.99882358 không giải thích được chênh
lệch mean: nguyên nhân lớn là hình dạng loss theo displacement ở ngoài tâm.

Tái dựng literal PDF với cùng primitives cho raw m1=.2341302396514297,
active retained mass=.9841173294440377 và conditioned m1=.23790886782137863.
Do đó số .2379 có thể tái lập trong luật cũ nhưng không xác nhận tính đúng vật
lý của xấp xỉ pointing trong regime beam hẹp/aperture lớn. Conditioning chỉ
đổi khoảng 1.6%; không tạo ra toàn bộ discrepancy.

Để định hướng, nếu giả định thêm scintillation độc lập, unit-mean và không
condition product, mean product là P1 eta_atm mean Hp≈.0300688755110.
Đây **chỉ là phép so sánh có điều kiện**, không phải replacement fading model:
lognormal có tail khiến product có thể >1, và dependence/conditioning phải
được khai báo trước. Không dùng số này để tính SKR hay tìm nguồn tốt nhất.
Không thể giữ nguyên analytic literal PDF rồi chỉ thay A0/w_eq bằng reference:
đổi Hp(r) làm đổi cả phân bố transmission.

## Trả lời năm câu hỏi

1. sigma_h chiếm khoảng 89.5% displacement variance tại reference; jitter góc
   chiếm khoảng 10.5%. Điều này chỉ xếp contribution vào sigma_s², chưa chứng
   minh tham số nào chi phối SKR. Xấp xỉ pointing sai regime là blocker hiện tại.
2. Chưa xác lập giảm sigma_h riêng có phục hồi SKR dương hay không: Experiment A
   NOT_RUN sau optical gate thất bại.
3. Chưa có first-positive, best-positive, Pareto frontier hay least-demanding
   configuration đã kiểm chứng. Experiments A/B/C và refinement NOT_RUN.
4. MB gain sau stabilization chưa xác lập; source reoptimization và Uniform
   comparator NOT_RUN. Không nội suy C,w hoặc tái dùng no-fading-noise SKR.
5. Chưa có final positive result. Reference aperture integral chính xác trong
   ideal Gaussian intensity; broadened Gaussian vẫn là approximation. Full
   fading moments trong covariance, nếu có, cũng không tự thiết lập fading
   mixture MI hoặc composable security.

## Điều kiện tiếp tục

Yêu cầu người dùng chỉ rõ không tiếp tục với inconsistent transmittance
evaluator. Vì vậy không phát sinh năm SKR plots hoặc bảng candidate SKR giả.
Những deliverables đó pending, không được đánh dấu complete.

Checkout cloud/implement tại HEAD fc80c8cd9f70e2c3adb75e79379a058f5fecf1ec
không có docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md và thư mục kết quả Task 1
đã nêu trong chat. Evaluator trusted_heterodyne_skr cũng chưa tìm thấy trong
inventory trước đó. Không giả sử evaluator hiện có là corrected Task-1 chain.
Để tiếp tục cần đưa đúng Task-1 implementation/tests/provenance vào checkout,
xác lập joint law aperture-integrated pointing + scintillation + AoA (bao gồm
independence và xử lý support T<=1), rồi validate moments, covariance và MI.
Không tự chọn min(T,1), truncated renormalization hoặc receiver mới để ép dương.

Frozen hash thực tế df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15
vẫn khác historical expected AGENTS; giữ nguyên blocker promotion.
NOT_READY_FOR_PUBLICATION_SCALE_RUNS và Objective C USER_STOPPED giữ nguyên.
Không thay production src/config/frozen specs hoặc kết quả cũ; không commit/push.

## Tái lập và artifacts

Từ project root:

```powershell
.\.venv-binary-cloud\Scripts\python.exe scripts/validate_pointing_aperture_task2.py
```

Script fail nếu output directory đã tồn tại để bảo vệ evidence cũ. Khi tái chạy
truyền tên thư mục mới làm positional argument, ví dụ task2_verification;
không xóa evidence cũ.
Môi trường .venv-cert thiếu scipy, lần chạy đó BLOCKED_BY_ENVIRONMENT;
.venv-binary-cloud chạy thành công. Numerical checks CURRENTLY_VERIFIED_PASS.

Artifacts tại results/pointing_aperture_task2_20261017/: optical_checks.json
(inputs, hashes, checks), mean_pointing_comparison.csv, radial_collection.csv,
pointing_comparison.png và vector PDF. Figure đã được xem kiểm tra trực quan.
Một process verification riêng đã chạy vào
results/pointing_aperture_task2_verification_20261017/; optical_checks.json
hai lần chạy có cùng SHA256. Đây là repeatability check của optical gate,
không phải SKR validation hoặc independent physical calibration.
