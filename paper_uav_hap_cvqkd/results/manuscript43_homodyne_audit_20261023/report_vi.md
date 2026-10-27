# Audit HAP–UAV DM-CV-QKD theo manuscript43 — 2026-10-23

**Đã hoàn tất audit và patch cô lập; chưa có mô hình secure-SKR được phê chuẩn làm default.** Có 18 unit tests đạt, 10 regression lịch sử khớp và 233 nguồn exact được kiểm tra. Ba trong chín context của PDF gốc không đạt mass tolerance đã đặt trước. Không sửa PDF, nguồn exact, cache, production evaluator hoặc đặc tả frozen.

Phạm vi dùng **homodyne một quadrature thực, reverse reconciliation, detector untrusted**. Các kết quả mới không có finite-key/composable-security claim. audit_model.py, protocol.json, variants.json và isolated_code_patch.diff là patch riêng trong thư mục này; branch cũ được giữ nguyên. Code mới từ chối nguồn/cache không đúng identity, PDF mất chuẩn hóa, covariance không vật lý và variance sai miền.

Ứng viên 28,1 cm trước đây có K=2.1077487381976345e-05 từ **actual pooled fading MI**. Khi giữ đúng channel moments, nguồn và Holevo đó nhưng dùng **Gaussian effective MI** theo yêu cầu hiện tại, K=-3.04873940221162e-06, tức âm. 30 cm vẫn có K=0.005392532654035664 trong **random-width surrogate lịch sử**; không được chuyển con số này sang PDF log-normal của bản43. Không thực hiện tối ưu mới để khôi phục dấu dương.

## 1. Tệp, phương trình và phạm vi sửa

Nguồn PDF: inputs/manuscript_v43.pdf, SHA256 f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b, bốn trang. Trang2 chứa Eqs.(1)–(8); trang3 chứa Eqs.(9)–(21); trang4 là tài liệu tham khảo. Các PNG trang2–4 đã được kiểm tra trực quan. PDF gốc ở Downloads và bản sao đầu vào không bị chỉnh sửa.

Bảng tham số dùng để tái đánh giá các điểm cố định nằm dưới đây và trong scenario_parameters.csv. Cùng λ=1550nm, β=.95, ξch=.0186, τzen=.92. Baseline giữ full divergence233µrad và jitter15.61µrad. Grid detector riêng cho hai geometry8cm là ηdet={.8,.85,.9,.95}, εdet={.0135,.005}; bảng này ghi detector của từng điểm lịch sử, không thay thế grid đó.

| Scenario | Dr(m) | HAP/UAV(km) | ζ(°) | L(km) | Full div(µrad) | Jitter(µrad) | Center SD(m) | ηdet | εdet | VA | νraw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline8 | 0.08 | 20.0/1.0 | 30 | 21.9393102292 | 233 | 15.61 | 1 | 0.8 | 0.0135 | 5.475 | 0.165 |
| recent8 | 0.08 | 20.0/1.0 | 0 | 19 | 50 | 1.561 | 0.1 | 0.95 | 0.005 | 1.62499953997 | 0.25 |
| historical40cm | 0.401 | 20.0/1.0 | 30 | 21.9393102292 | 25.0785813719 | 1.561 | 0.1 | 0.8 | 0.0135 | 1.77777775971 | 0.3 |
| historical55cm | 0.55 | 20.0/1.0 | 30 | 21.9393102292 | 35 | 3 | 0.1 | 0.8 | 0.0135 | 2.15 | 0.22 |
| receiver28p1 | 0.281 | 20.0/1.0 | 0 | 19 | 35 | 1.561 | 0.1 | 0.95 | 0.005 | 1.3833230303 | 0.2 |
| receiver30 | 0.3 | 20.0/1.0 | 0 | 19 | 35 | 1.561 | 0.1 | 0.95 | 0.005 | 1.62499953997 | 0.25 |
| receiver15 | 0.15 | 20.0/1.0 | 0.0 | 19.0 | 50.0 | 1.561 | 0.1 | 0.95 | 0.005 | 1.6249995399703647 | 0.25 |
| receiver20 | 0.2 | 20.0/1.0 | 0.0 | 19.0 | 50.0 | 1.561 | 0.1 | 0.95 | 0.005 | 1.8 | 0.21 |
| receiver25 | 0.25 | 20.0/1.0 | 0.0 | 19.0 | 35.0 | 1.561 | 0.1 | 0.95 | 0.005 | 1.3833230302980657 | 0.2 |



| Vấn đề | Bản43 | Repo thực tế | Kết luận / patch |
| --- | --- | --- | --- |
| Modulation | Sau(3): Vmod=n̄/2 | Normalization VA=2n̄ | Bản thảo lệch hệ số4 so với X=2Reα; giữ nguồn/caches |
| MB | γ ở tử, ν ở Z; norm của chỉ sốk | PMF centered; νrepo=42,5νraw | Thiếu định nghĩa/notation; giữ PMF hiện có |
| MI | Gaussian1D dùng αphức trong modulus | Production frozen heterodyne; diagnostic có cả2D/1D | Dùng Reα trong patch; không ghép MI2D với Holevo homodyne |
| Detector | ξ=ξch+ξdet/η | Nhiều biến ξdet/εdet/R ở các namespace | Giữ ηdet/εdet riêng; explicit A/B/independent |
| Noise | σ²=1+ηfξf | Recent untrusted helper đã có Npost đúng | C giữ đúng signal/loss/noise; B giữ literal để audit |
| Holevo | ν3 homodyne; T=ηf | Production heterodyne; recent helper homodyne/full-Z | C dùng Ttotal=ηdetηf cùng Npost trong Z,Γ,χ |
| PDF | Eq.(10), moments trên[0,1] | Raw literal, conditional-active và random-width riêng | Không thay law cho nhau; fail closed trên mass lỗi |

repository_map.csv ghi đường dẫn, hàm:dòng và hash của 37 tệp. production_call_sites.csv bổ sung chín caller/channel/source file vào inventory gốc28 tệp. Đây không phải tuyên bố đã chạy toàn bộ pipeline cũ.

## 2. Nguồn, Vmod và MB

Đặt \(X_k=2\operatorname{Re}\alpha_k\), \(P_k=2\operatorname{Im}\alpha_k\), vacuum variance1. Với ensemble centered/C4:

\[
\operatorname{Var}X=\operatorname{Var}P=2\sum_kp_k|\alpha_k|^2=2\bar n=V_A.
\]

Vì vậy sửa Vmod=n̄/2 thành Vmod=2n̄ nếu giữ quadrature này. Không sửa VA, amplitude hoặc C,w của cache để khớp phương trình sai. source_normalization.csv kiểm tra đủ233 nguồn:

| Nguồn | VA cache | n̄ | E[X] | E[X²] | Var(X) | n̄/2 theo PDF |
| --- | --- | --- | --- | --- | --- | --- |
| MB ν=0.165 | 5.475 | 2.7375000000000007 | 5.529421079228559e-17 | 5.475 | 5.475 | 1.3687500000000004 |
| MB ν=0.25 | 1.6249995399703647 | 0.8124997699851825 | 1.2136044394792741e-17 | 1.624999539970365 | 1.624999539970365 | 0.40624988499259124 |
| Uniform ν=0.0 | 1.0 | 0.49999999999999994 | 2.7755575615628914e-17 | 0.9999999999999999 | 0.9999999999999999 | 0.24999999999999997 |



Raw centered indices là \(u_i=i-7.5\). Nguồn hiện có dùng \(p_{ij}\propto\exp[-\nu_{raw}(u_i^2+u_j^2)]\); canonical constellation có mean energy42,5 nên \(\nu_{repo}=42.5\nu_{raw}\). Với physical energy \(|\alpha|^2=\Delta^2(u_i^2+u_j^2)\), \(\nu_{phys}=\nu_{raw}/\Delta^2\). Đây là đổi biến của cùng PMF.

Nếu γ vàν khác nhau, tử/mẫu(2) không bảo đảm tổng1. Fixture γ=.165/ν=.25 cho tổng 1.39265375221; đây là counterexample, không phải giá trị được suy đoán cho manuscript. Khi γ=ν, weighting bằng i²+j² chưa centered vẫn cho meanα≠0; MB_notation_checks.csv ghi cụ thể. Cache cũ không dùng được dưới PMF thay đổi đó.

## 3. Detector và bốn mặt phẳng tham chiếu

Đặt \(m_1=\langle\eta\rangle\), \(m_h=\langle\sqrt\eta\rangle\), \(T_f=m_h^2\), \(N_f=(m_1-T_f)V_A\), \(N_c=m_1\xi_{ch}\).

| Mặt phẳng | Mean homodyne | Variance noise Gaussian hiệu dụng | Vai trò |
| --- | --- | --- | --- |
| Alice | Xk=2Reαk | Vacuum1 | Classical displacement variance VA=2n̄ |
| Channel output trước detector | √Tf Xk | 1+Nf+Nc | Detectorloss chưa tác động |
| Physical detector output YB | √(ηdet Tf) Xk | 1+ηdet(Nf+Nc)+εdet | Plane quantumΓ trongC |
| Classical Y′=YB/√ηdet | √Tf Xk | 1/ηdet+Nf+Nc+εdet/ηdet | MI invariant; Γ lượng tử giữ nguyên |

Với \(Y_B=\sqrt{\eta_{det}}Y_{ch}+\sqrt{1-\eta_{det}}V_0+E_{el}\), vacuum cộng thành \(\eta_{det}+(1-\eta_{det})=1\). Không thêm loss vacuum lần nữa vào output excess. C dùng

\[
T_{total}=\eta_{det}T_f,\quad
N_{post}=\eta_{det}[(m_1-T_f)V_A+m_1\xi_{ch}]+\epsilon_{det},\quad
\sigma^2_{N,B}=1+N_{post}.
\]

ConventionA là \(\xi_{det}=\epsilon_{det}/\eta_{det}\): v42 vàv43 trùng đại số ởη>0 nếu chuyển tham số đúng. ConventionB là \(\chi_{hom}=(1-\eta_{det}+\epsilon_{det})/\eta_{det}\), có cả loss vacuum trong noise budget quy về trước detector; không phải electronic excess đơn thuần.

**Nếu M0=1, literal σ² với conventionB đúng bằng variance của classically rescaled measurement, nên MI có thể trùngC.** Nhưng dùng Wrescaled như quantum variance với vacuum/CCR cũ và áp lạiZ không phải phép đổi biến cổ điển hợp lệ cho Holevo. Baselineη=.8/ε=.0135: MI lệch 3.73e-17, nhưng Holevo lệch 0.533976187339. classical_quantum_plane_checks.csv kiểm tra đủ16 detector/context pairs. Manuscript chưa chọn A/B/independent; independent chưa có giá trị nên BLOCKED.

Tham khảo receiver/noise framework trong [Laudenbach et al.](https://arxiv.org/pdf/1703.09278). Các plane equations ở đây được suy ra trực tiếp từ loss/vacuum, không dùng Gaussian-modulation SKR thay DM source bound.

## 4. MI homodyne và conditional variance

Patch tính discrete-input MI với real mean \(2\sqrt{T_{total}}\operatorname{Re}\alpha_k\). Tổng256 labels bằng marginal16 levels vì cùng Reα cho cùng density. Không nhân MI lên2; entropy measured quadrature≤4bit/use. \(\frac12\log_2(1+T_{total}V_A/\sigma_N^2)\) chỉ là Gaussian reference bound.

Với complex mean như bản in vày∈R, conditional mass là \(\exp[-2\eta_f(\operatorname{Im}\alpha_k)^2/\sigma_\xi^2]\), khác1. B-as-printed có MI/Holevo/SKR unavailable. B_real_projection_diagnostic sửa mean thành Reα và giữ noise/covariance literal để so sánh; không phải nguyên density in trong PDF.

Fading thực cho \(\operatorname{Var}(Y_B\mid X=x)=1+\eta_{det}m_1\xi_{ch}+\epsilon_{det}+\eta_{det}(m_1-T_f)x^2\), phụ thuộc symbol. C thay x² bằngVA để tạo **moment-matched Gaussian approximation**, không phải exact fading likelihood. Unconditional Bob variance là \(b=\sigma_N^2+T_{total}V_A=1+\eta_{det}m_1(V_A+\xi_{ch})+\epsilon_{det}\), khác conditional noise. Đổi actual pooled MI thành Gaussian MI có thể đổi SKR dù noise/Holevo không đổi.

Unit tests kiểm tra conditional normalization, finite/nonnegative MI trong tolerance, T→0, entropy≤4, X/P symmetry,256/16 equality, adaptive quadrature, invertible scaling, source tampering, noise planes, covariance và low-T stability. Các số nằm trong conditional_pdf_normalization.csv, MI_independent_checks.csv, unit_tests.json và focused_independent_checks.csv. Raw negativeK giữ nguyên.

## 5. PDF, outage và ba moments

Giữ Eq.(10), closed forms(18)–(19). channel_moment_checks.csv đối chiếu closed form với direct integration đổi biếnη=exp(y) trên[0,1]; atomP0 cộng riêng ởpower0. Residuals đạt tolerance đã đặt trước.

| Scenario | M0 | Khối lượng η>1 | Eη | E√η | Chuẩn hóa ≤1e-10 | K theo PDF gốc |
| --- | --- | --- | --- | --- | --- | --- |
| baseline8 | 1 | 3.39738802132e-83 | 0.000264033937028 | 0.0156059440206 | CURRENTLY_VERIFIED_PASS | -0.05872431468 |
| recent8 | 1 | 3.39738795996e-83 | 0.0108269202694 | 0.103113481941 | CURRENTLY_VERIFIED_PASS | -0.0238716505217 |
| historical40cm | 0.99877661032 | 0.00122338968014 | 0.433708410202 | 0.64737921253 | FAILED | — |
| historical55cm | 0.998519527489 | 0.00148047251114 | 0.466619169783 | 0.674719399246 | FAILED | — |
| receiver28p1 | 0.999999999997 | 3.33608009538e-12 | 0.205379138324 | 0.446448247703 | CURRENTLY_VERIFIED_PASS | -0.00535729108401 |
| receiver30 | 0.999999999894 | 1.05699551365e-10 | 0.230060363122 | 0.472722659854 | FAILED | — |
| receiver15 | 1 | 6.42102551207e-55 | 0.0374776527557 | 0.191868941021 | CURRENTLY_VERIFIED_PASS | -0.0202642350634 |
| receiver20 | 1 | 3.91526918253e-38 | 0.0655207995113 | 0.253726952464 | CURRENTLY_VERIFIED_PASS | -0.0161434436965 |
| receiver25 | 1 | 2.80922636504e-15 | 0.166876654249 | 0.402151313426 | CURRENTLY_VERIFIED_PASS | -0.0113726175885 |



M0=P0+P1 C1 Q(χ²). Zero-limit extension \(g(0)=\lim_{\eta\to0}\eta\xi(\eta)=\xi_{det}\) cho Eq.(20) là \(\xi_{ch}m_1+\xi_{det}M_0\). Active-only cho \(\xi_{ch}m_1+\xi_{det}(M_0-P_0)\). Chênh lệch ξdetP0; không phải conditioning lại PMF. C giữ electronics trên mọi transmitted use; gating/postselection là protocol khác.

noise_moment_checks.csv đối chiếu đủ288 tổ hợp context/detector/ξdet/outage. Direct noise integral được lấy bằng linearity từ các quadrature độc lập của moment0 và1 đã lưu; atom0 cộng riêng theo extension. Đây là kiểm tra moment nhiễu, không phê chuẩn các PDF mất mass và không chạy lại MI/Holevo.

40/55cm mất mass do lognormal gain unbounded trong khi tích phân chỉ tới1. 30cm hơi vượt1e-10 nên vẫn bị chặn; không nới tolerance vì gần ngưỡng. 28,1cm mất3,34e-12, được chấp nhận trong tolerance nhưng residual/tail vẫn lưu. Không renormalize, chuyển tail sang outage, clipping hoặc thêm atomη=1. Raw-PDF C cho40/55/30cm có K unavailable, không phải0.

**Rician:** Eq.(10) khớp product lognormal×pointing ởρ=0. Vớiρ≠0, untruncated moments từ Eq.(8) cho counterexample:ρ=.5m/power1 tại fixture baseline có lệch 2.14681%. Rician_product_checks.csv ghi analytic Laplace/directRice checks. Đây là whole-support supplementary check, không thay truncated moments ở trên. Manuscript cần nêu approximation/domain hoặc derivation choρ≠0.

Eq.(5) dùng lnIa∼N(−v/2,v). Code dùng rawRytov làmv dưới weak-turbulence approximation. turbulence_variance_checks.csv xác nhận mass1,E[Ia]=1,E[Ia²]=exp(v). Log-amplitude variance=v/4. Không đổi atmospheric model hoặc lẫn rawRytov/aperture-averaged variance. Gd/Cn² còn chỗ thiếu citation[] trong PDF.

## 6. Holevo và scope bảo mật

C dùng cùng \(T_{total}\), \(N_{post}=T_{total}\xi_{total}\) trong \(Z_\pm=2\sqrt{T_{total}}C\pm\sqrt{2N_{post}w}\), \(a=1+V_A\), \(b=1+T_{total}V_A+N_{post}\). Intersect physical correlation interval rồi numerical-maxχ. Conditional eigenvalue là homodyne \(\nu_3=\sqrt{a(a-Z^2/b)}\).

[Denys–Brown–Leverrier](https://arxiv.org/html/2103.13945v3) nêu công thức homodyne trên và áp dụng bound cho homodyne. Production protocol frozen của repo vẫn là idealheterodyne; đó là khác biệt protocol, không phải giới hạn “DBL chỉ heterodyne”. Exact C,w hiện có được dùng nguyên.

Full-Z33/129, independent symplectic matrix/uncertainty và entropy80/110digits đã kiểm tra. Không clip eigenvalues dưới1. Exact uncertainty-boundary identity của helper không phải numerical repair. Numerical max chưa là rigorous global enclosure. [Hosseinidehaj–Walk–Ralph](https://arxiv.org/abs/2002.03476) là reference effective fading/finite-sizeGaussian; không tự chuyển proof sang256-QAM ở đây. Parameter estimation, operational fading protocol và finite/composable proof vẫn chưa xác lập.

## 7. Detector-convention comparison

Ví dụ geometry gốc,ηdet=.8,εdet=.0135,fixedMB(.165,VA5.475). CSV đầy đủ144 rows cho hai geometry×tám detector pairs×các variant/extension:

| Biến thể | ηdet | εdet | ξdet / định nghĩa | Outage extension | Gain² MI | Variance MI | MI | Holevo | K / trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C_physical_output | 0.8 | 0.0135 | epsilon_det_output_separate_from_efficiency | physical output | 0.0001948363910181277 | 1.0135936682283404 | 0.000758763487095913 | 0.05944513999271761 | -0.05872431467997649 |
| C_physical_classically_rescaled_output | 0.8 | 0.0135 | epsilon_det_output_separate_from_efficiency | physical output | 0.00024354548877265962 | 1.2669920852854255 | 0.000758763487095913 | 0.05944513999271761 | -0.05872431467997649 |
| B_literal_v43_as_printed | 0.8 | 0.0135 | A_epsilon_over_eta = 0.016874999999999998 | limit | 0.00024354548877265962 | 1.0169920852854255 | — | — | FAILED_COMPLEX_MEAN_IN_REAL_PDF |
| B_v43_noise_real_projection_diagnostic | 0.8 | 0.0135 | A_epsilon_over_eta = 0.016874999999999998 | limit | 0.00024354548877265962 | 1.0169920852854255 | 0.0009451628209055842 | 0.07157890934624023 | -0.07068100466637992 |
| B_v43_noise_real_projection_diagnostic | 0.8 | 0.0135 | A_epsilon_over_eta = 0.016874999999999998 | active_only | 0.00024354548877265962 | 1.0169892189540084 | 0.0009451654830535494 | 0.07156903395142189 | -0.07067112674252102 |
| B_literal_v43_as_printed | 0.8 | 0.0135 | B_chi_hom = 0.2668749999999999 | limit | 0.00024354548877265962 | 1.2669920852854255 | — | — | FAILED_COMPLEX_MEAN_IN_REAL_PDF |
| B_v43_noise_real_projection_diagnostic | 0.8 | 0.0135 | B_chi_hom = 0.2668749999999999 | limit | 0.00024354548877265962 | 1.2669920852854255 | 0.0007587634870959502 | 0.5934213273314501 | -0.5927005020187089 |
| B_v43_noise_real_projection_diagnostic | 0.8 | 0.0135 | B_chi_hom = 0.2668749999999999 | active_only | 0.00024354548877265962 | 1.266946754784868 | 0.0007587906208682282 | 0.593351405219241 | -0.5926305541294162 |
| B_independent_xi_det_unresolved | 0.8 | 0.0135 | independent_explicit | physical output | — | — | — | — | BLOCKED_MISSING_DEFINITION_OR_VALUE |



## 8. Old versus new — cùng historical channel law

| Scenario / cùng law lịch sử | MI cũ | MI Gaussian | Holevo cũ | Holevo mới | K cũ | K mới |
| --- | --- | --- | --- | --- | --- | --- |
| baseline8 | 0.000753762353882783 | 0.0007537576311201701 | 0.05941243731599366 | 0.05941243731599366 | -0.05869636307980502 | -0.0586963675664295 |
| recent8 | 0.011648919977141457 | 0.011648872627355254 | 0.03474496486068279 | 0.03474496486068279 | -0.023678490882398408 | -0.023678535864695302 |
| historical40cm | 0.328598187261735 | 0.3284832264348961 | 0.3118846040182446 | 0.31188460401824414 | 0.0002836738804036787 | 0.00017446109490709683 |
| historical55cm | 0.409551549600137 | 0.40949201037312083 | 0.3539241344550901 | 0.3539241344550901 | 0.03514983766504004 | 0.03509327539937468 |
| receiver28p1 | 0.1656282249036697 | 0.16560282887547745 | 0.15732573617110424 | 0.1573257361711058 | 2.1077487381976345e-05 | -3.04873940221162e-06 |
| receiver30 | 0.210784854649766 | 0.21074687539663958 | 0.19481699897277194 | 0.19481699897277194 | 0.0054286129445057785 | 0.005392532654035664 |
| receiver15 | 0.039538088659869734 | 0.03953747953843063 | 0.057112991145256586 | 0.057112991145256586 | -0.019551806918380342 | -0.019552385583747493 |
| receiver20 | 0.07467525387302669 | 0.07467335379777157 | 0.08561666365736476 | 0.08561666365736476 | -0.014675172477989398 | -0.014676977549481773 |
| receiver25 | 0.1372622697041933 | 0.137242420746872 | 0.13756643120196688 | 0.13756643120196688 | -0.007167274982983252 | -0.007186131492438463 |
| original_manuscript_trial8 | 0.0007587634870959417 | 0.000758763487095913 | 0.05944513999271871 | 0.05944513999271761 | -0.05872431467997756 | -0.05872431467997649 |



baseline8/recent8/15–55cm dùng đúng passive random-width moments lịch sử; chỉ thay actual fading likelihood MI bằng Gaussian effective MI. C new MI khớp I_AB_surrogate đã tồn tại; Holevo cùng convention khớp helper cũ. **Không phát hiện double-count εdet trong recent untrusted helper.** Đổi dấu28,1cm là đổi approximation; không chứng minh source cache sai hoặc phủ nhận legacy value trong chính model cũ.

original_manuscript_trial8 giữ đúng rawlognormal law: K mới=-0.058724314679976491, khớp số cũ ở độ chính xác số học. 30/40/55cm còn dương trong passive-surrogate table, nhưng chuyển sang rawPDF bị chặn tại các context mất mass. raw_manuscript43_results.json ghi riêng các giá trị/blocked fields. Không quy chênh lệch hai laws thành hiệu ứng detector riêng.

**Không chuyển tiếp kết luận “minimum28,1cm positive” sang Gaussian model.** Không re-ranking/optimization catalog mới; chỉ re-evaluate source cũ. affected_results.csv liệt kê252 result entries (thư mục và tệp ở root, có entry_kind riêng): chỉ scenario ghi rõ được tính lại; phần khác NOT_REEVALUATED. Old2DMI/homodyneHolevo zenith/mobility outputs giữ nguyên, không dùng làm consistent new homodyne SKR.

cache_impact.csv liệt kê287 cache entries:233 authenticated source payloads còn dùng được với đúng ensemble/VA; cache khác chỉ được bảo toàn, không coi là tái thẩm định. Objective/SKR cache phải có contextID mới khi dùngC. Không đổi namespace hoặc bytes source cache.

## 9. Thay đổi, verification và blocker

Chỉ thêm patch riêng cùng năm task ledgers. Không sửa src/, frozen spec, production configs, exact caches hoặc artifacts cũ. repository_map.csv và isolated_code_patch.diff chỉ rõ code/traceability; verify.py kiểm tra saved artifacts bằng hash, không gọi evaluator.

Lần tích hợp đầu tiên, harness dùng passive-collector geometry để đọc hệ số PDF cũ, gây KeyErrorB sau17 tests đạt. attempt_1/ giữ nguyên producer/failure. Caller đã sửa sang đúng preserved lognormal/Rician factory, thêm guard/test;18 tests sau đó đạt. Không đổi tolerance hoặc scientific source.

Không designate secure default do PDF mass failures,ξdet manuscript chưa định nghĩa,caveatρ≠0,Gaussian-MI approximation và operational/security scope chưa hoàn tất. C chỉ là **numerically validated physical homodyne/untrusted Gaussian component** khi input guards đạt. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy,ObjectiveC USER_STOPPED.

Không newAP, optimization sweep, training, final-test/heldout/publication, production baseline/threshold approval hoặc commit/push. Đề xuất sửa PDF nằm riêng ở manuscript_corrections_vi.md; PDF không bị chỉnh sửa.

## Appendix: bản đồ repo đã kiểm tra

| Tệp / nhóm | Vai trò | Hàm : dòng |
| --- | --- | --- |
| scripts/hap_uav_channel_pdf.py | mixed channel PDF and Rician pointing | Scenario:56;_fallback_log_ndtr:101;log_ndtr:118;i0e:122;ndtri:130;_fallback_finite_quad:134;_fallback_quad:156;brentq:186;_quad:208;_finite_quad:216;_safe_exp:222;_log1mexp:231;_sha256:242;cn2_hufnagel_valley:246;derive_parameters:261;log_hsc_pdf_from_log_h:380;f_hsc:387;f_rmis:395;f_rayleigh:418;f_hp:425;f_theta:447;_log_pdf_log_x:457;_log_survival_log_x:470;_cdf_log_x:483;f_x:487;f_x_direct_quadrature:501;_raw_moment:519;_truncated_moment:525;_log_density_integral:534;_raw_quantile:546;component_and_channel_analysis:564;_normalization_checks:606;_histogram:665;_sample_physical_active:676;monte_carlo:697;_style:740;_save:755;make_figures:762;_print_value:874;print_summary:878;_json_ready_mc:923;parse_args:933;main:941 |
| scripts/calculate_channel_pdf_and_moments.py | geometry/HV/closed moments | hv_cn2:45;_sha256:51;derive_physical_inputs:55;hsc_statistics:210;hsc_pdf:256;pointing_pdf:270;_product_kernel:291;_log_product_pdf_log_coordinate:316;product_pdf:329;product_cdf:338;_tail_probability:345;_untruncated_moment:371;_truncated_moment:389;closed_form_channel_moments:426;_pdf_log_integral:496;_product_quantile:514;_mixed_quantiles:526;_pointing_pdf_normalization:543;analyze_product:571;_stderr:647;primitive_monte_carlo:651;production_sampler_check:706;_comparison:764;_active_config_record:781;_plot_single:810;_plot_comparison:847;main:886 |
| src/manuscript_literal_3moments.py | historical37 literal mode, not v43 | ManuscriptModelError:20;finite:24;detector_noise:31;total_input_noise:39;_log_erfc:47;_exp:51;LiteralChannel:59;effective_channel:161;z_star:177;covariance:184;entropy:213;holevo:220;evaluate_candidate:225 |
| src/manuscript_corrected_3moments.py | explicit historical conditional-active law; not raw v43 PDF | CorrectedModelError:26;_agree:30;PhysicalFadingDistribution:35;corrected_channel_moments:168;deterministic_moments:172;effective_fading_channel:196;corrected_z_star:248;corrected_covariance:262;admissible_correlation_interval:301;_ideal_holevo:336;holevo_interval_maximizer:343 |
| src/manuscript_corrected_evaluator.py | trusted/ideal configuration gate; not new untrusted mode | validate_settings:19;validate_cached_candidate:37;scientific_context:74;evaluate_candidate:95 |
| src/manuscript_corrected_mi.py | historical complex fading measurement | FadingMIError:25;_finite:29;_ensemble:36;receiver_parameters:48;_mixture_log_likelihood:71;_quadrature:84;_physical_fading_samples:121;_information_samples:155;discrete_fading_mutual_information:171 |
| src/cvqkd/mutual_information.py | frozen production complex heterodyne MI | _product_qam_factors:14;is_product_qam_ensemble:44;standard_complex_noise:54;discrete_mutual_information:78;_gauss_hermite_noise:237;_deterministic_real_mi:254;_deterministic_full_mi:296;deterministic_mutual_information:366 |
| scripts/recheck_manuscript_homodyne_noise.py | shared GH dimension1 helper; historical script uses mixed primary pairing | digest:32;channel:36;security:84;mi_gh:110;write_csv:137;converted:144;main:154 |
| src/modulation/qam256.py | C4 square QAM and canonical MB PMF | c4_orbit_indices:16;expand_c4_orbit_values:45;expand_c4_orbit_masses:59;c4_orbit_masses:71;square_qam256:84;canonical_square_qam256:101;uniform_pmf:112;binomial_pmf:118;maxwell_boltzmann_pmf:129;reference_pmf:143 |
| src/modulation/normalization.py | VA=2*nbar physical amplitudes | validate_probabilities:8;physical_amplitudes:22 |
| src/cvqkd/gram_moments.py | exact source correlation implementation | FullSupportGradientUnavailable:17;GramMomentResult:21;_hex:26;_sectors:28;_fast:39;_fast_from_sectors:43;_fallback:126;c4_gram_source_moments:135 |
| scripts/exact_cache_provenance.py | authenticated source/cache identities | json_hash:19;canonical_bytes:23;source_hashes:27;source_settings:34;verify_source_payload:42;objective_identity:76;objective_compatible:91 |
| src/manuscript_mobility.py | 233-source authenticated catalog and historical mixed evaluator | sha:37;read_csv:41;validate_config:46;_validate_ensemble:68;load_catalog:90;geometry_table:145;evaluate_source:168;select_winner:206;lambda_schedule:218;greedy_step:232;_mission:255;_path_result:269;greedy_trajectory:280;compare_paths:292 |
| src/cvqkd/covariance.py | frozen production heterodyne conditional spectrum | PhysicalityError:15;SymmetryDiagnostics:20;CovarianceResult:30;quadrature_symmetry_diagnostics:39;standard_form_covariance:72 |
| src/cvqkd/holevo.py | production correlation interval/Holevo | SecurityDomainError:24;HolevoResult:33;coherent_state_vectors:44;density_operator:56;annihilation_operator:66;support_restricted_source_moments:73;bosonic_entropy:156;_maximize_bounded_scalar:167;_expand_ensemble_for_correlations:273;_evaluate_holevo_for_correlations:295;_holevo_from_source_moments:364;dense_fock_holevo_information:590;c4_gram_holevo_information:669;holevo_information:741;shared_fixed_ensemble_holevo_chi:795 |
| src/cvqkd/protocol.py | frozen ideal heterodyne assumptions | ProtocolAssumptions:11;validate_channel_state:27 |
| src/optimization/trainer.py | production learning caller; NOT_RUN | Evaluation:31;EnergyBudgetController:51;evaluate_transmitter:94;_active_state_tensors:206;train_step:231 |
| scripts/run_theta10_D55_alt_opt.py | historical finite exact-source parameter optimizer; NOT_RUN | ExactSourceUnavailable:64;ExactCandidateFailure:68;sha256:72;write_csv:76;json_hash:84;finite_metrics:90;ExactObjective:97;adaptive_maximize_1d:238;coordinate_search_complete:441;stopping_status:447;run_single_ao:464;save_figure:613;make_figures:624;self_check:652;main:700 |
| scripts/optimize_uniform_manuscript_2d.py | historical 2D MI optimizer; not homodyne reuse | sha:42;save_json:46;write_csv:50;uniform_mi_2d:58;UniformSearch:84;run_search:231;finalize:274;plot_results:315;write_report:350;main:469 |
| results/untrusted_positive_skr_feasibility_20261022/model.py | preserved strict real homodyne/Gaussian component and passive surrogate | optical:28;bounded:55;power_conserving:82;source_factors:115;_entropy:121;spectrum:131;full_holevo:145;evaluate:172;direct_moments:207;pooled_mi:219 |
| results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py | preserved pooled fading likelihood and aperture adapter | optical:18;optical_quadrature:27;quadrature:39;evaluate:50 |
| configs/default.yaml | production protocol/defaults preserved | — |
| configs/channel.yaml | unresolved production channel inputs preserved | — |
| configs/manuscript_corrected_3moments.json | historical alternative convention preserved | — |
| configs/manuscript_mobility.json | authenticated source roster preserved | — |
| tests/test_mutual_information.py | historical production MI tests | MutualInformationTests:11 |
| tests/test_holevo.py | historical production security tests | HolevoTests:15 |
| tests/test_manuscript_corrected_mi.py | historical complex fading test | _PhysicalFixture:14;CorrectedMITests:29 |
| src/channel/fso_channel.py | Production channel/source/rate caller; frozen behavior preserved | TransmittanceDomainError:44;ChannelSamples:49;compose_raw_transmittance:66;physicalize_raw_transmittance:92;_finite_nonnegative:122;_resolve_scintillation:129;sample_fso_channel:213 |
| src/channel/geometry.py | Production channel/source/rate caller; frozen behavior preserved | LinkGeometry:10 |
| src/channel/turbulence.py | Production channel/source/rate caller; frozen behavior preserved | UavMotion:10;uav_misalignment_variance_m2:24;uav_translational_variance_m2:42;uav_orientation_variance_rad2:49;hap_angular_displacement_variance_m2:56;pointing_displacement_variance_m2:78;turbulence_beam_wander_variance_m2:94;per_axis_displacement_variance_m2:117 |
| src/channel/scintillation.py | Production channel/source/rate caller; frozen behavior preserved | UnsupportedApertureAveragingError:13;hufnagel_valley_cn2:17;hufnagel_valley_scintillation:45;_finite_nonnegative:139;rytov_variance_from_profile:146;normalized_lognormal_samples:194;resolve_scintillation_variance:213;scintillation_provenance:234 |
| src/channel/pointing_error.py | Production channel/source/rate caller; frozen behavior preserved | PointingParameters:13;gaussian_beam_radius:28;pointing_parameters:57;manuscript_pointing_parameters:96;pointing_power_transmittance:171 |
| src/channel/aoa.py | Production channel/source/rate caller; frozen behavior preserved | UnsupportedTurbulenceAoAError:12;aoa_orientation_variance_rad2:16;_resolve_turbulence_aoa_variance:23;aoa_variance_rad2:46;aoa_outage_probability:61;aoa_inlier_probability:73;sample_aoa_gate:77 |
| src/channel/atmospheric_loss.py | Production channel/source/rate caller; frozen behavior preserved | kruse_q:12;extinction_coefficient_per_km:22;atmospheric_transmittance:31;atmospheric_transmittance_from_tau_zen:48 |
| src/cvqkd/secret_key_rate.py | Production channel/source/rate caller; frozen behavior preserved | FadingKeyRate:12;fading_secret_key_rate:19 |
| src/modulation/joint_ps_gs.py | Production channel/source/rate caller; frozen behavior preserved | PeakPhotonConstraintViolation:17;validate_peak_photon_limit:21;enforce_peak_photon_constraint:37;Ensemble:69;AdaptiveVarianceNetwork:142;JointTransmitter:171;reference_ensemble:294 |


