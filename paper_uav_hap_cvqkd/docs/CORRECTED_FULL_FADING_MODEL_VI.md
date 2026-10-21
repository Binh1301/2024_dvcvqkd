# Mô hình HAP–UAV 256-QAM: full fading, khẩu độ tròn và heterodyne

Ngày 2026-10-17. Yêu cầu f5f45a58-0425-4187-a9cc-4c6a41f34313.
Đã thay đổi implementation và corrected CLI; không tối ưu pointing/MB.
Trạng thái: **IMPLEMENTED_NUMERICALLY_VALIDATED_REFERENCE_VERSION_PENDING**.
Các kết quả dưới đây là asymptotic numerical diagnostics của mô hình đã khai báo.
Không có kết quả dương hoặc chứng nhận composable security.

## Tài liệu và authority

Đúng file `2026__Binh_s_work (38)(7).pdf` chưa tìm thấy trong attachments,
workspace, Downloads/Documents đã kiểm; đã hỏi đường dẫn. Không đánh đồng nó
với bản hiện có `C:/Users/admin/Downloads/2026__Binh_s_work (38).pdf`, SHA256
`0c60153cb6dcd4f8a3a2e8ecfe0cb245b473463f051837fb46028916eb6be0a0`.
Bản hiện có đã extract và render trang 3 để đọc công thức; chỉ dùng đối chiếu.
Việc xác nhận đủ mọi Eq.(1)–(22) của đúng bản (38)(7) vẫn pending.
Implementation theo các công thức user cung cấp rõ trong attachment và hai
primary references dưới đây, không suy đoán nội dung phiên bản còn thiếu.

Các lỗi thấy trực tiếp ở bản (38) hiện có: Eq.(2) dùng gamma ở numerator nhưng
nu ở normalizer; statement sau Eq.(3) đảo hệ số VA; Eq.(12) viết real likelihood
trong khi alpha/y cần convention complex heterodyne; Eq.(13) dùng conditional
homodyne; phần sau Eq.(18) trộn chi_line/chi_hom vào channel excess. Các correction
trong task này xử lý từng điểm bằng một ensemble, một SNU convention và đúng
receiver, không điều chỉnh hardware/noise để ép K dương.

[Denys–Brown–Leverrier v3](https://arxiv.org/pdf/2103.13945v3): kiểm Eq.(3),
Eq.(11)–(14), footnotes 11/12 và convention VA=2<n>. Footnotes yêu cầu xét
maximum Holevo trên interval thay vì luôn mặc định endpoint.
[Hosseinidehaj–Walk–Ralph v1](https://arxiv.org/html/2002.03476v1): kiểm
Eq.(6)–(9). Đúng v1, covariance ensemble-average là Eq.(7), moment integrals
là Eq.(8), và effective eta/noise nằm trong Eq.(9), không phải Eq.(7).
Tên file có suffix (4)(1)/(5) chưa có; không giả định đã xác nhận byte identity
của bản local đó với các arXiv primary editions đã đọc.

Frozen spec SHA256 vẫn là
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`, khác
historical expected trong AGENTS. Không sửa/restore frozen document; promotion
blocker giữ nguyên. Task này cấp phép correction cho namespace mới, không thay
scope của historical direct-Z experiment, training hoặc publication.

## Mapping công thức sang code

Bảng đánh số Binh dưới đây theo bản **(38) hiện có**, chưa chứng nhận (38)(7).

| Binh / nguồn đối chiếu | Hàm và quyết định implementation |
|---|---|
| (1), constellation | `qam256.square_qam256`, `make_ensemble` hiện có; 256 trạng thái, amplitude chuẩn hóa bởi `physical_amplitudes` |
| (2), MB | `qam256.maxwell_boltzmann_pmf`; một tham số nhất quán, numerator/normalizer cùng PMF |
| (3), energy | `Ensemble.computed_va`, `authenticate_source`: VA=2 sum p abs(alpha)^2 theo Denys; sửa statement VA=<n>/2 trong draft |
| (4), atmosphere | `full_fading_channel.optical_geometry`: eta_atm=tau_zen^sec(zeta), L từ fixed-altitude geometry |
| (5), turbulence | cùng hàm: HV/raw Rytov, Ia=exp(-s/2+sqrt(s)z), unit mean trước conditioning |
| (6), pointing | `FullFadingLaw.hp`: Mode A equivalent Gaussian; Mode B `aperture_collection` dùng noncentral-chi-square CDF |
| (7), Rician motion | `radial_density`: per-axis sigma_s²=sigma_h²+(L theta_jt)²; stable scaled Bessel I0e |
| (8), pointing PDF | Mode A rho=0 được tái dựng từ product law và kiểm so với literal PDF; Mode B không dùng công thức này |
| (9), AoA | `optical_geometry`, `quadrature`, `cdf`: giữ P0 delta_0 tách riêng |
| (10), full PDF | Mode A kiểm tương đương `LiteralChannel`; Mode B tích phân conditional lognormal trên Rician r, có `density`, `cdf` riêng |
| (11), raw SKR | `full_fading_evaluator.evaluate_candidate`: 0.95 I-chi, giữ dấu |
| (12), MI | `mixture_mi` tích phân complex joint likelihood; Gaussian diagnostic dùng `deterministic_mutual_information` |
| (13), Holevo | `corrected_covariance`, `holevo_interval_maximizer` tái sử dụng; lambda3=a-Z²/(b+1) theo heterodyne Denys Eq.(3) |
| (14), correlation | `admissible_correlation_interval`, `evaluate_ideal_security`: full Denys interval Eq.(11), general pooled moments, không giả định endpoint |
| (15), tau | existing exact C,w cache; authenticate ensemble/source SHA256 và current source producers |
| (16), Fock expansion | không mở source worker mới hoặc thêm Fock truncation; giữ full-support exact-cache route |
| (17), w | existing `c4_gram_source_moments`/AP cache theo Denys Eq.(12), không nội suy |
| (18), effective fading | `effective_channel`: squared amplitude moment và full channel excess theo Hosseinidehaj Eq.(7)–(9) |
| (19),(20), closed moments | chỉ comparison Mode A; Mode B `_integral` dùng truncated-lognormal moments và Rician integration |
| (21), noise moment | không đưa chi_line/detector vào channel excess; dùng <eta xi_eta>=.0186 m1 |
| (22), raw integral | comparison Mode A; Mode B có integral riêng, không gọi analytic Eq.(10)/(19)/(20) |

Nguồn MB cố định: nu_raw=.17, VA=5.046875. Raw grid là (i-7.5)+j(l-7.5),
nu_repo=42.5 nu_raw do scaling canonical grid hiện có. PMF và physical amplitudes
đều lấy từ cùng ensemble đã kiểm, không tái chuẩn hóa C,w theo hình học quang.
C=2.9818069279923307, w=6.190945650452507e-7; 256-state ensemble hash
`b2dde0f1bdf8c14fefedc304926b6524b79e0628d577af2b387a55e975f9205b`.
Payload SHA256 `e6e1b9ef8be95c72e3328966edde7b7c9e3d9bb885d3171e4927cbcb13d70317`.
AP producer unchanged, không build/rank truncate mới; authenticated-cache reuse
không tự cấp một total-error certificate mới cho C,w.

## Hai luật quang học và support

Hai baseline tách riêng trong `configs/corrected_full_fading.json`:

- `BINH_PDF_233urad_D08`: divergence full-angle 233 urad, Dr=.08 m, zeta=30°.
- `NARROW_10urad_D55`: full-angle 10 urad, Dr=.55 m; geometry giữ
  L=21.9393102292 km bằng zeta=0.5235987755978426 rad.

HAP=20 km, UAV=1 km, lambda=1550 nm, tau_zen=.92, sigma_h=1 m,
theta_jt=15.61 urad per axis, wind=21 m/s, Cn2(0)=1e-14, F0=infinity.
AoA sigma_o=.0015 rad, FOV half-angle=.00625 rad, P0≈.00016985667656.
Broadening giữ HV/Gd effective Gaussian width; scintillation dùng raw Rytov
như literal mode hiện có. Gd bibliography/calibration chưa được giải quyết chỉ
bằng numerical matching. Không tự chuyển sang aperture-averaged scintillation.

Mode A `PDF_ORIGINAL`: Hp=A0 exp(-2r²/w_eq²). Analytic Eq.(10) chỉ kiểm được
rho=0 trong scope này; nonzero boresight bị từ chối cho mode A.
Mode B `APERTURE_CORRECTED`, mặc định của class và primary optical mode:

\[
H_p(r)=F_{\chi'^2_2(4r^2/w^2)}(4a^2/w^2),\quad a=D_r/2,\ w=w_{L,eff}.
\]

Centered limit và Bessel aperture integral được kiểm độc lập. Với Gaussian
intensity và zero boresight, E Hp=1-exp[-2a²/(w²+4sigma_s²)]. Checkpoint
diffraction-only wL=.1475476163 m, E Hp=.03311823955; broadened E Hp=.03311350683.
Mean approximation cũ≈.27771373193 ở narrow beam. Thay Hp làm đổi toàn PDF.

Trước giới hạn support: X=eta_atm Ia Hp(r). Scintillation, displacement và AoA
giả định độc lập; normal E Ia=1. Lognormal khiến P(X>1)>0, nên raw product
không phải passive-transmissivity law trên [0,1]. Chính sách hiện hành được
ghi rõ: **condition active law on X<=1, preserve the AoA atom**. Không dùng
min(X,1), không bỏ outage và không gọi conditioning là experimental validation.
Sau conditioning, scintillation và displacement không còn độc lập trong joint
law được giữ lại; code tích phân joint law rồi normalize một lần toàn active
component, không condition scintillation riêng ở mỗi displacement.

Với B(r)=eta_atm Hp(r), s=sigma_R², raw truncated moment là

\[
M_q=\int_0^\infty f_R(r)B(r)^q e^{s q(q-1)/2}
\Phi\left(\frac{-\ln B(r)+(1/2-q)s}{\sqrt{s}}\right)dr.
\]

Factive=M0, m_q=P1 Mq/M0 cho q>0. Continuous physical density cũng được
tính từ product integral; CDF có jump P0 tại 0. Direct log-scaled survival
integral kiểm tail, tránh phép 1-Factive làm mất tail rất nhỏ của baseline cũ.
Narrow Mode A loại active tail≈.01588267056; Mode B≈.003871300968. Đây là
lựa chọn surrogate cần hiệu chuẩn hoặc thay bằng energy-conserving propagation
model trong một task sau, không phải security-certified physical correction.

## Full noise, covariance và correlation

\[
\eta_f=m_{1/2}^2,\quad v_f=m_1-\eta_f,\quad
N_{eff}=v_f V_A+.0186m_1,\quad \xi_f=N_{eff}/\eta_f.
\]

\[
a=1+V_A,\quad b=1+\eta_fV_A+N_{eff}=1+m_1(V_A+.0186).
\]

Channel excess không chứa vacuum/loss term hoặc detector noise.
Primary receiver là ideal heterodyne (R=1, xi_det=0), phase/AO OFF.
Không dùng trusted (.7,.0135) trong bất kỳ kết quả primary nào.

\[
c_1=m_{1/2}C,\quad c_2=m_{1/2}V_A/2,\quad n_B=m_1(V_A+.0186)/2,
\]
\[
n_B-c_2^2/(V_A/2)=N_{eff}/2,\quad
Z_\pm=2m_{1/2}C\pm\sqrt{2N_{eff}w}.
\]

Intersect với |Z|<=sqrt(min[(a-1)(b+1),(a+1)(b-1)]), rồi maximize Holevo
trên toàn khoảng. Các baseline này cho Z_worst=Z_minus **sau khi kiểm tra**,
không dùng kết luận đó làm giả định chung. Grid/refinement và dense replay là
numerical verification, chưa phải rigorous continuous supremum enclosure.

Gamma có blocks aI, bI và Z sigma_z. Spectrum dùng Delta=a²+b²-2Z²,
D=(ab-Z²)²; existing stable factorization tránh cancellation. Conditional
lambda3=a-Z²/(b+1), không dùng biểu thức homodyne trong bản (38) hiện có.
Holevo là sum hai Gaussian entropies trừ conditional entropy. Không clip
covariance, correlation hoặc entropy để làm chúng hợp lệ.

## Hai MI, hai con số SKR

Gaussian-effective diagnostic dùng same exact ensemble với gain sqrt(eta_f),
complex noise variance 1+N_eff/2 và GH16/32/48 product quadrature.

Actual pooled fading-mixture dùng CN(sqrt(eta) alpha_k,1+.0186 eta/2),
average likelihood trên physical law bao gồm P0. Tích phân I_AB trên complex
output plane bằng 2D Hermite importance rule; không factor I/Q do chúng có
chung fading. Product quadrature (Rician r, truncated normal z) được kiểm
mass/m1/mhalf bằng independent adaptive truncated-moment integrals trước khi
normalize numerical weights. Lanczos chỉ giảm **likelihood quadrature nodes**
theo sqrt(eta), tuyệt đối không giảm 256-state source support. Numerical zero
nodes do underflow được ghi riêng, không gọi thành AoA outages vật lý mới.

Mixture orders 24/40/56; verification 72 fading nodes, output GH80 và reference
variance 1.5, thay physical quadrature 48 thành 64 và siết tolerance.
Đây là hội tụ số của stated physical-surrogate mixture, không phải exact
arithmetic hoặc MI của một turbulence field đã đo/calibrate.

| Baseline | Optical mode | I Gaussian | I mixture | chi_BE | K Gaussian | K mixture |
|---|---|---:|---:|---:|---:|---:|
| 233 urad, Dr=.08 | A | .000886319390 | .000886325171 | .001594316710 | -.000752313290 | -.000752307798 |
| 233 urad, Dr=.08 | B | .000886324405 | .000886330187 | .001594336651 | -.000752328465 | -.000752322973 |
| 10 urad, Dr=.55 | A | .421572584924 | .452443647216 | 1.146634482882 | -.746140527204 | -.716813018027 |
| 10 urad, Dr=.55 | B | .005797331991 | .016332539084 | .341392112809 | -.335884647418 | -.325876200679 |

Tất cả rates là signed bits/use. Với narrow Mode B:

\[
m_1=.0257215527662,\quad m_{1/2}=.0411432838286,\quad
\eta_f=.00169276980420,\quad v_f=.0240287829620,
\]
\[
N_{eff}=.121748684893,\quad \xi_f=71.9227650391,\quad
Z_-=.244974394854,\quad Z_+=.245750920187,
\]
\[
a=6.046875,\quad b=1.130291882498,\quad
(\lambda_1,\lambda_2,\lambda_3)\approx(6.038503655914,1.121920538412,6.018703999290).
\]
\[
K_{mixture}=.95(.0163325390841)-.341392112809
=.0155159121299-.341392112809=-.325876200679.
\]

Full precision của **mọi baseline/mode/MI method**, gồm beta I, C,w,Z endpoints,
a,b,three lambdas và noise moments nằm trong `released_run/decomposition.csv`
và per-case JSON. K âm không được thay bằng zero hoặc abs(K).

## Kiểm thử và giới hạn

Test suite có 14 new tests và 18 existing corrected ideal/moment tests.
Validation artifact ghi từng check riêng, không dựa số test từ chat cũ.

| Mandatory requirement | Kiểm tra | Status |
|---|---|---|
| 1. PMF và VA | 256-state normalization, computed energy, exact payload/ensemble hashes | PASS |
| 2. Normalization/support/outage | CDF endpoints, positive quadrature support, explicit P0 | PASS |
| 3. Hai mode moments | independent product quadrature vs truncated-lognormal/radial integrals | PASS |
| 4. Nonnegative amplitude variance | checked before effective channel | PASS |
| 5. Bob variance identity | both formulas agree | PASS |
| 6. Denys interval | general c1,c2,nB and N_eff/2 identity | PASS |
| 7. Physical covariance/spectrum | direct iOmegaGamma and Gamma+iOmega eigenvalues | PASS |
| 8. Heterodyne conditional eigenvalue | lambda3=a-Z²/(b+1) | PASS |
| 9. No-fading | deterministic delta tag gives xi_f=xi_ch | PASS |
| 10. Pure loss/vacuum | eta=0 limit b=1, N_eff=0 | PASS |
| 11. MI/Holevo refinement | GH, physical quadrature, likelihood compression, denser full interval | PASS |
| 12. Old-model checkpoint | Mode A reproduces m1≈.2379089 and K_G≈-.746140527 | PASS |
| 13. Aperture moments | noncentral CDF vs scaled-Bessel integral and analytic pointing mean | PASS |
| 14. No mixing | source/VA/nu/C/w/hash tampering and receiver/protocol mismatches rejected | PASS |

Xem `released_verification/validation.json` cho PASS/FAIL cuối cùng và
`unit_tests.txt` cho tên từng test. Lần RED đầu do evaluator mới chưa tồn tại
được giữ là expected TDD setup failure, không phải regression cuối cùng.
Terminal run: 32 tests PASS, 0 failures/errors; 40 separate stricter replay/
matrix/entropy checks PASS. Mỗi PASS chỉ thuộc stated numerical scope.
Scoped tests không bao gồm mọi historical evaluator: old protected baseline
manifest của `validate_cached_candidate` đã mismatch trước khi thay code task
này. New evaluator dùng pinned source-payload SHA256 + current source-producer
verification; không sửa historical manifest để làm nó PASS.

Về security, giả định fixed centered C4 source độc lập fading, phase compensation,
stationary iid composite channel và pooled outcomes bao gồm outage. Có thể cho
Eve giữ/purify fading label; không xem fading noise là trusted detector noise.
Không tự kéo composable proof của Gaussian modulation sang DM. Temporal
correlations, finite samples, PE confidence, reconciliation leakage/code và
calibration chưa được triển khai thành operational certificate. Missing exact
manuscript version và frozen-hash conflict cũng còn nguyên.

## Code và lệnh tái lập

Mới: `src/full_fading_channel.py`, `src/full_fading_evaluator.py`,
`configs/corrected_full_fading.json`, `scripts/run_full_fading_model.py`,
`scripts/verify_full_fading_model.py`, `tests/test_full_fading_pipeline.py`.
Đổi caller `scripts/run_manuscript_corrected_3moments.py`: default route dùng
full-fading implementation mới; explicit scientific-model historical giữ CLI
cũ. Không redirect historical mobility/optimization/training experiments.
`effective_channel_no_fading_noise.py` giữ nguyên và chỉ là diagnostic.

Từ project root, output namespace mới, không ghi đè:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv-binary-cloud\Scripts\python.exe scripts/run_manuscript_corrected_3moments.py --output results/my_corrected_replay
.\.venv-binary-cloud\Scripts\python.exe scripts/verify_full_fading_model.py --input results/my_corrected_replay --output results/my_corrected_verification
```

Artifact root: `results/corrected_full_fading_20261017/`. `released_run` và
`released_verification` là terminal numerical evidence; earlier baseline/final
names là immutable development snapshots. Producer/config/source hashes được
lưu trong receipts. Không sửa exact-source producers, frozen specifications,
physical defaults hoặc historical results. Không AP/source build mới,
pointing/MB optimization, training/test/held-out/publication, commit hay push.

## Trả lời cuối

1. Covariance đã nhất quán với channel-excess convention và pooled moments;
   Denys cung cấp DM correlation, không thay C bằng Gaussian-modulation value.
2. Ideal heterodyne Holevo đúng công thức, kiểm full feasible Z interval;
   numerical convergence không đồng nghĩa rigorous maximization certificate.
3. Fading-induced noise được giữ đầy đủ trong cả MI diagnostic và covariance;
   actual-mixture MI lấy trực tiếp từ physical distribution.
4. Baseline 233 urad/8 cm với fixed MB source đã khai báo có Mode B mixture
   K≈-.000752322973; narrow Mode B mixture K≈-.325876200679 bits/use.
   Đây không phải optimized rates hoặc chứng nhận đúng file (38)(7).
5. Reference version, optical surrogate/conditioning/calibration và operational
   security scope còn pending. Chưa tuyên bố toàn bộ yêu cầu reference audit
   hoàn tất. Dừng sau deliverables; không tự chạy tối ưu tiếp.
