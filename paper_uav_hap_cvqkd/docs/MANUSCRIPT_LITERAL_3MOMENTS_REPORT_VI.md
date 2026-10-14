# Báo cáo triển khai manuscript_literal_3moments

## Kết quả và phạm vi

Đã thêm backend riêng cho các Eq. (9)--(20), không sửa evaluator lịch sử.
Nguồn được người dùng cung cấp trực tiếp: `2026__Binh_s_work (37).pdf`,
SHA-256 `9e7e1af3c218aa8136cf9c00e41309e84c083bab5f8be9735bf14b73e3a8ca95`.
Đây là bản `(37)` được đính kèm ở lượt xác nhận, không giả định rằng một bản
`(37)(2)` chưa được cung cấp có nội dung giống hệt. Công thức trên trang 3 đã
được kiểm tra cả bằng text extraction và ảnh render PDF. Nội dung `TBD`,
placeholder và hướng dẫn nằm trong PDF không được thực thi.

Status kiểm thử implementation: **CURRENTLY_VERIFIED_PASS**, 5/5 unittest.
Đây **không** phải PASS của normalization hoặc chứng nhận bảo mật.
Normalization tại fixture tham chiếu **FAILED**: khối lượng chỉ bằng
`0.9841200272202841`, thiếu `0.015879972779715867`, khoảng **1.588%**.
Mật độ và moment được giữ nguyên, không renormalize.

Chỉ chạy kiểm thử tổng hợp, tích phân độc lập và hai phép đánh giá một điểm
tham chiếu (mode cũ/new) bằng C,w đã lưu. AP, AO, 182-pair evaluation,
26-distance numerical sweep và publication/final-test access: **NOT_RUN**.

## A. Tệp mới và tệp metadata được cập nhật

| Đường dẫn tương đối trong project | Mục đích |
|---|---|
| `src/manuscript_literal_3moments.py` | Eq. (9)--(14), total noise, effective channel, covariance, Z, spectrum, entropy và discrete-MI adapter |
| `configs/manuscript_literal_3moments.json` | Mode, phiên bản/hash PDF, R=.7, xi_det=.0135, xi_ch=.0186, beta=.95, GH8, không normalize |
| `scripts/run_manuscript_literal_3moments.py` | Entry một điểm, bắt buộc chọn scientific-model và nguồn exact có sẵn, namespace/identifier mới, không overwrite |
| `tests/test_manuscript_literal_3moments.py` | A--F: công thức, tích phân độc lập, legacy regression và fail-closed |
| `scripts/validate_manuscript_literal_3moments.py` | Chạy unittest nhẹ, kiểm tra hash và xuất receipt mới |
| `docs/MANUSCRIPT_LITERAL_3MOMENTS_REPORT_VI.md` | Báo cáo này |
| `docs/EVIDENCE.md`, `docs/DECISION_LOG.md`, `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, `.agent/SESSION_HANDOFF.md` | Ghi nhận authorization, bằng chứng và STOP; không sửa specification frozen |

Backend được đặt **ngoài** `src/channel` và `src/cvqkd`: `objective_identity`
lịch sử quét hai thư mục đó. Thêm backend vào đó sẽ khiến các context cache
cũ bị mất tương thích dù evaluator cũ không đổi. Không cần sửa helper
provenance/cache hay source evaluator để tích hợp backend riêng này.

## B. Audit công thức được triển khai

Đặt \(B=A_0\eta_{atm}\), \(d=\chi^2=(w_{Leq}/2\sigma_s)^2\).
Giữ \(P_0\delta_0\) riêng, \(P_1=1-P_0\), với
\(P_0=\exp[-\theta_{FoV}^2/(2\sigma_o^2)]\).

\[
C_1=\exp\left[\rho^2/\sigma_s^2+\tfrac12\sigma_R^2d(1+d)\right],\qquad
C_3=\left(32\rho^2\sigma_s^2/w_{Leq}^4+2\sigma_R^2\right)^{-1/2},
\]
\[
\mu=6\rho^2/w_{Leq}^2+\tfrac12\sigma_R^2(1+2d),\qquad
x_1=\ln(1/B)+\mu,
\]
\[
Q(a)=\tfrac12\left[e^{ax_1-a\mu}\operatorname{erfc}(C_3x_1)
+e^{a^2/(4C_3^2)-a\mu}\operatorname{erfc}\left(a/(2C_3)-C_3x_1\right)\right].
\]

`log_ndtr` và `logsumexp` chỉ là cách tính ổn định của đúng biểu thức erfc
và tổng hai số hạng; không đổi mô hình hoặc hệ số. Exponential overflow được
báo lỗi, không sửa tham số. PDF trên \([0,1]\) là

\[
f_\eta(\eta)=P_0\delta_0(\eta)+P_1\frac{dC_1}{2B^d}\eta^{d-1}
\operatorname{erfc}\left[C_3(\ln(\eta/B)+\mu)\right].
\]

Ba moment Eq. (12)--(14):

\[
m_1=P_1B\frac{dC_1}{d+1}Q(d+1),\qquad
m_h=P_1\sqrt B\frac{dC_1}{d+1/2}Q(d+1/2),
\]
\[
M_0=P_0+P_1C_1Q(d),\qquad
m_n=m_1(\xi_{ch}-1)+(1+\chi_{het})M_0.
\]

Không gán \(M_0=1\), không chia moment cho \(M_0\), không dùng integral
untruncated lịch sử. Không đánh giá \(\xi(0)\).

\[
\chi_{het}=\frac{1+(1-R)+2\xi_{det}}R=1.8957142857142857,
\quad \xi_{line}=1/\eta-1+\xi_{ch},\quad
\xi=\xi_{line}+\chi_{het}/\eta\quad(\eta>0).
\]

Eq. (11) và mapping được chọn cho Eq. (20):

\[
\eta_f=m_h,\quad v_h=m_1-m_h^2,\quad
n_f=\eta_f\xi_f=v_hV_A+m_n,\quad\xi_f=n_f/\eta_f\ (\eta_f>0),
\]
\[
a=V_A+1,\qquad b=1+m_hV_A+(m_1-m_h^2)V_A+m_n,
\]
\[
Z_*=2\sqrt{m_h}\,C-\sqrt{2wn_f},\qquad
\Gamma_{AB}=\begin{pmatrix}aI_2&Z_*\sigma_z\\Z_*\sigma_z&bI_2\end{pmatrix}.
\]

Không dùng \(m_h^2\) thay \(m_h\) trong \(\eta_f\), modulation term hay
term đầu của \(Z_*\). Không loại detector hoặc pure-loss noise khỏi \(m_n\).

\[
\Delta=a^2+b^2-2Z_*^2,\qquad D=(ab-Z_*^2)^2,
\]
\[
\lambda_{1,2}=\sqrt{(\Delta\pm\sqrt{\Delta^2-4D})/2},\qquad
\lambda_3=a-Z_*^2/(b+1),
\]
\[
g(x)=(x+1)\log_2(x+1)-x\log_2x,\quad g(0)=0,
\]
\[
\chi_{BE}=g((\lambda_1-1)/2)+g((\lambda_2-1)/2)-g((\lambda_3-1)/2),
\qquad K=0.95I_{AB}-\chi_{BE}.
\]

Entropy dùng biểu thức tương đương ổn định
\([\ln(1+x)+x(\ln(1+x)-\ln x)]/\ln2\) khi \(x>0\).
Negative discriminant, covariance không dương xác định, variance âm,
negative w hoặc eigenvalue dưới 1 đều fail-closed, **không clipping**.
Nếu eigenvalue dưới 1 trong tolerance, vẫn báo numerical failure vì entropy
không được định nghĩa ở occupation âm. Zero eta_f cho xi_f/SKR null và trạng
thái `ZERO_EFFECTIVE_TRANSMISSION`, không chia 0 hoặc tạo K=0 giả định.

## C. Khác biệt với mode cũ và phần giữ nguyên

Mode cũ dùng moment raw/untruncated, \(T_{eff}=m_h^2\), epsilon=.0186,
\(b=1+T_{eff}V_A+T_{eff}\epsilon\) và
\(Z_-=2\sqrt{T_{eff}}C-\sqrt{2T_{eff}\epsilon w}\).
Mode mới dùng literal finite moments, \(\eta_f=m_h\), total noise \(n_f\),
và các biểu thức b/Z ở trên. Không thay source normalization để ép theo
Eq. (1)--(3) của PDF: PMF MB, nu_raw convention, amplitudes và VA normalization
repository được giữ nguyên đúng yêu cầu. Đây là reproduction của
**channel-moment/covariance/Holevo**, không phải toàn bộ phương trình PDF.

Đối với physical mapping của Eq. (5)--(6), new mode dùng raw Rytov
`sigma_R0_squared`, không dùng aperture-averaged `v_sc`; nu_ap, A0 và w_eq
được tính bằng effective beam width như PDF, không lấy A0 lịch sử dùng w_L.
Các primitive geometry, HV profile và G_d được tái sử dụng không chỉnh sửa.
PDF không cung cấp công thức/citation đầy đủ cho G_d (`[]`), nên sự tái sử
dụng này được ghi rõ là source gap, không phải derivation hoàn chỉnh từ PDF.

Discrete-constellation MI vẫn là helper `deterministic_mutual_information`,
product GH8, cùng ensemble ở cả MI/security, beta=.95. Adapter mới chọn rõ
T=eta_f, epsilon=xi_f để vào likelihood cũ
\(Y=\sqrt{\eta_f}\alpha+CN(0,1+n_f/2)\).
Không thay bằng Gaussian Eq. (17), không thêm correction trusted-detector,
không trừ đi thành phần noise để chuyển về convention Denys.
Việc dùng total noise làm epsilon của likelihood cũ cũng là integration
convention được công bố, không phải DM-MI derivation được PDF chứng minh.

## D. Kiểm thử và kết quả

Bằng chứng chính: `results/manuscript_literal_3moments/implementation_validation_4/validation.json`
và `test_output.txt`. 5 unittest chứa các nhóm A--F, chạy 3.823 s theo
unittest (receipt tổng có thêm thời gian kiểm tra bảo toàn).

| Nhóm | Kết quả |
|---|---|
| A: eta_f, n_f, b | PASSED |
| B: Z_star và không bình phương m_h | PASSED |
| C: fixture .4/.5/.25, VA2, C1, w.01 | PASSED: eta_f=.5, variance=.15, n_f=.55, b=2.55 |
| D: closed forms so với tích phân độc lập [0,1] | PASSED, cả rho=0 và rho=.2; Eq14 có outage limit contribution |
| D: PDF normalization tại reference | **FAILED**, M0=.9841200272202841; báo discrepancy, không sửa mật độ |
| E: original reference regression | PASSED: K=.07798099387393764 và MI khớp; cả 26 cache context vẫn compatible |
| F: numerical/physicality/zero/tampered source/overflow | PASSED: domain lỗi bị từ chối, không clipping; covariance reference hợp lệ |
| AP, AO, full catalog/sweep, publication/final-test | NOT RUN |

Một lần kiểm thử ban đầu có lỗi Python ghép trường status; đã sửa.
Receipt lỗi ở `implementation_validation/` được giữ nguyên, không ghi đè.
Receipt iteration 2 và 3 cũng được giữ; iteration 4 tương ứng các producer hiện tại.

Tại fixture reference L=21.9393102292 km, nu_raw=.165, VA=5.5:

| Đại lượng new mode | Giá trị |
|---|---:|
| mean_eta | 0.23413023966620677 |
| mean_sqrt_eta = eta_f | 0.39477740142305245 |
| mean_eta_xi | 2.619955004470893 |
| pdf_mass | 0.9841200272202841 |
| eta_f_xi_f | 3.0505007409261733 (rounded display) |
| I_AB | 0.5159273267867874 (rounded display) |
| chi_BE | 2.9449057702842776 (rounded display) |
| raw SKR | **-2.454774809836829** |

Raw negative K được giữ, không biến thành operational rate. Các giá trị đầy đủ
trong machine-readable receipt là nguồn số có thẩm quyền. Không yêu cầu K mới
khớp K lịch sử. Lỗi normalization ngăn diễn giải fixture này như một PDF
xác suất hợp lệ hoặc chứng nhận tốc độ khóa, dù covariance numerical hợp lệ.

## E. Bảo toàn

Receipt kiểm tra **3251** tệp cũ/protected theo hash, gồm source caches,
Objective B, toàn bộ Objective C đã commit, scientific src/scripts/config,
specification frozen và kết quả/plots cũ. Không sửa byte nào trong các tệp đó.
Không sửa `src/channel`, `src/cvqkd`, original SKR caller, AP worker hay AO.
Source cache được đọc và verify bằng helper cũ; C,w phải khớp đúng binary64
nu_raw/VA, ensemble hash và source payload. Thử sửa C bị từ chối trong test.

Historical frozen-model expected hash trong AGENTS vẫn khác actual
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`.
Đây là discrepancy có trước task, không được âm thầm reconcile hoặc sửa spec.
Nó vẫn là blocker cho promotion/publication; task này chỉ thực hiện mode
reproduction riêng theo yêu cầu người dùng. Lifecycle vẫn
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; Objective C vẫn `USER_STOPPED`.

## F. Caveats và điểm dừng

1. Literal eta_f là E[sqrt(eta)], **không phải bình phương**.
2. T=eta_f, xi=xi_f giữa Eq11/Eq20 là convention người dùng chọn; PDF không
   chỉ rõ mapping này. Adapter MI chọn cùng inputs và cũng công bố convention.
3. Total-input-referred noise của PDF khác channel-excess-noise convention
   của evaluator Denys lịch sử; không loại pure-loss/detector contributions.
4. Eq17 là Gaussian-modulation MI, không cung cấp độc lập discrete-QAM MI.
   Giữ nguyên PMF/VA normalization theo repository như yêu cầu cũng không đồng
   nghĩa implement literal toàn bộ Eq1--3 của PDF.
5. Mode này là **manuscript reproduction**, không phải security-proof,
   numerical certification hay publication approval. Normalization discrepancy
   và source gap G_d đều được giữ công khai, không sửa vật lý để ép PASS.

Entry chỉ cho một candidate có source exact sẵn và một distance, bắt buộc
`--scientific-model manuscript_literal_3moments`, `--source-payload`,
`--manuscript`, `--distance-km`. Hash PDF sai, candidate không tương thích hoặc
output identifier đã có đều bị từ chối. Namespace mới là
`results/manuscript_literal_3moments/`; identifier chứa model/PDF/config/physics/
producer hashes và source identity/C,w hex, không restore objective cũ làm
result mới. Entry `--help` đã smoke-check; không chạy production entry.

**STOP** sau implementation, validation và reporting. Muốn chạy sweep,
optimization hoặc giải quyết normalization/model gap cần yêu cầu rõ ràng mới.
