# Báo cáo mode manuscript_corrected_3moments

Ngày 2026-10-13; branch `channel/update`, HEAD `84bf84dc3862b6cb51fa368f7e481459845ffb98`. Thực hiện theo attachment `82ff4829-20ff-4c83-930f-a00de47c48a2/Pasted text.txt`. Mục tiêu là implementation riêng và lightweight validation; không thay lịch sử hoặc frozen specification.

**Eq. (10) và Eq. (20) được giữ nguyên về toán học.** Raw Eq. (10) vẫn ở `src/manuscript_literal_3moments.py`; mode mới bọc một luật physical riêng. Eq. (20) tái dùng chính đại số `literal_z_star` với đầu vào đúng. Không sửa literal module hoặc các producer source moments.

## A. File mới và file trạng thái được cập nhật

| Đường dẫn repository-relative | Mục đích |
|---|---|
| `src/manuscript_corrected_3moments.py` | Physical-law wrapper, ba moment, dual noise/covariance/Z, khoảng DBL và ideal Holevo maximizer |
| `src/manuscript_corrected_mi.py` | Joint complex discrete fading-mixture likelihood, physical sampling, quadrature và precision diagnostics |
| `src/manuscript_corrected_evaluator.py` | Kiểm tra config/source provenance, integration, per-candidate fields và chặn SKR khi unresolved |
| `configs/manuscript_corrected_3moments.json` | Model riêng, active conditioning, rho=0, phase OFF, R=.7, xi_det=.0135, xi_ch=.0186, beta=.95, trusted receiver |
| `scripts/run_manuscript_corrected_3moments.py` | Entry một existing-source point; không có AP, sweep hoặc optimization |
| `scripts/validate_manuscript_corrected_3moments.py` | Lightweight tests, regressions, producer hashes và protected-file receipt |
| `tests/test_manuscript_corrected_3moments.py` | A–K, M–N; independent quadrature, deterministic/physicality/Holevo checks |
| `tests/test_manuscript_corrected_mi.py` | L: receiver/SNU, outage, 256-symbol fixtures, reproducibility và precision gates |
| `tests/test_manuscript_corrected_evaluator.py` | Config API, source tampering, nonideal security blocker và không tự chạy MI |
| `docs/MANUSCRIPT_CORRECTED_3MOMENTS_REPORT_VI.md` | Báo cáo này |
| `docs/EVIDENCE.md`, `docs/DECISION_LOG.md` | EVID-0180/DEC-0163, evidence trước trạng thái |
| `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, `.agent/SESSION_HANDOFF.md` | Current snapshot và STOP sau implementation/tests/report |

Artifacts mới nằm dưới `results/manuscript_corrected_3moments/implementation_validation/`:

- `baseline_manifest.json`: snapshot trước sửa, 3643 protected file hashes, trạng thái Git và bản sao state trước task.
- `startup_diff.patch`: pre-existing diff, giữ nguyên các thay đổi có trước.
- `attempt_1/validation.json`, `attempt_1/test_output.txt`: receipt phiên bản trung gian, không ghi đè.
- `attempt_2/validation.json`, `attempt_2/test_output.txt`: **receipt hiện hành**, 24 tests PASS; producer hashes khớp code cuối.
- `reference_algebra_receipt.json`: interval của reference algebra fixture; MI, Holevo và SKR cấu hình nonideal là null.
- `mandatory_checks.json`: mapping A–O và phạm vi PASS/BLOCKED/NOT RUN.
- `final_integrity_receipt.json`: protected hashes, output hashes, complete diff/whitespace và lifecycle flags.

Tên PDF trong request là `2026__Binh_s_work (37)(2).pdf`; chưa tìm thấy file này trong thư mục được cung cấp. Bản thực sự đã có là `(37).pdf`, SHA256 `9e7e1af3c218aa8136cf9c00e41309e84c083bab5f8be9735bf14b73e3a8ca95`. Config/record phân biệt requested version và available reference; không tuyên bố đã xác minh bytes của bản `(37)(2)`. Các công thức đầy đủ trong user task là authority cho mode riêng này. PDF không bị chỉnh sửa.

## B. So sánh toán học và implementation

| Công thức ban đầu | Vấn đề | Implementation corrected | Validation |
|---|---|---|---|
| Eq. (2), exponent theo k²+ℓ² | Chưa tâm hóa PMF | Giữ nguyên producer đang đúng: raw levels k−7.5, ℓ−7.5; ν_repo=42.5ν_raw | PASSED A; không sửa source |
| Eq. (3), VA=n/2 | Sai SNU/photon convention | VA=2Σp|α|²; cùng ensemble tại interfaces | PASSED A |
| Eq. (10) raw PDF | Đuôi trên 1 bị bỏ ở finite moments | Raw nguyên vẹn; physical active conditional trên (0,1], giữ atom P0 | PASSED B–D |
| Eq. (10), general rho | Chưa validated nonzero boresight | rho!=0 bị từ chối explicit unsupported diagnostic | PASSED failure tests |
| Eq. (14) raw m_n | Chưa dùng luật physical normalized | Giữ literal raw; corrected m_n=1+χ_het+(ξ_ch−1)m1 | PASSED D |
| Eq. (11), power parameter m_h | Lẫn amplitude với power | T_eff=m_h²; Var√η=m1−T_eff | PASSED E/I |
| Quantum noise dùng ξ_total | Vacuum/receiver bị đưa vào excess | N_out=(m1−T_eff)VA+m1ξ_ch; check đường ba moment | PASSED F |
| Bob covariance | Double counting hoặc wrong power | b=1+m1(VA+ξ_ch)=(VA+1)m1+m_n−χ_het | PASSED G/J |
| Eq. (20) | Sai đầu vào noise/transmission | Giữ 2√T C−√(2Tξw), dùng T_eff,ξ_eff | PASSED H/I |
| Direct Z_star Holevo | Endpoint không mặc nhiên worst-case | Khoảng DBL + physical intersection + grid/refinement | PASSED K ideal fixtures; BLOCKED selected nonideal |
| Eq. (17) Gaussian modulation | Không phải finite-QAM/fading MI | Discrete joint complex fading-mixture MI; sampling/quadrature diagnostics | PASSED L software fixtures; reference precision NOT RUN |

Source normalization và MB producer vốn đúng, nên không sửa `src/modulation`, không tính lại C,w. Cache reuse kiểm tra producer/settings/parameter hex/ensemble identity và **SHA256 source payload theo protected startup manifest**. C,w không được xác thực chỉ bằng key metadata của verifier cũ. Scientific context mới bind source payload, C/w hex, ensemble, raw channel, receiver, numerics và producer bytes.

## C. Raw và physical normalization

Các số sau là kết quả **unit fixture/quadrature trong attempt_2**, không phải corrected SKR production run. Reference: L=21.9393102292 km, ν_raw=.165, VA=5.5, rho=0, cùng raw channel của literal fixture.

| Đại lượng | Giá trị |
|---|---:|
| Raw retained mixed mass trên [0,1] | 0.9841200272202841 |
| F_active(1)=C1 Q(d) | 0.9841173294426483 |
| Independent retained active mass | 0.9841173294426482 |
| Active tail P(X>1) | 0.015882670557351587 |
| Discarded mixed raw mass P1 P(X>1) | 0.015879972779715916 |
| Independent discarded mixed mass | 0.015879972779715795 |
| Raw full-support mixed mass | 0.9999999999999999 |
| Physical normalized mixed mass | 0.9999999999999999 |
| P0, giữ nguyên | 0.00016985667656141038 |

Dung sai normalization `1e-10`; independent retained/tail/full quadrature errors lần lượt khoảng `8.46e-12`, `1.79e-13`, `8.69e-12`. Vì vậy thiếu mass là đuôi raw trên 1, không phải giả định integration error. Raw Eq. (10) không được sửa hệ số hoặc âm thầm renormalize.

Luật physical được chọn rõ:

\[
P_{\rm phys}(d\eta)=P_0\delta_0(d\eta)+P_1\frac{f_{\rm active,raw}(\eta)}{F_{\rm active}(1)}\mathbf1_{0<\eta\le1}\,d\eta.
\]

Đây là conditioning model choice, không phải identity hoặc một derivation bảo toàn năng lượng của raw Eq. (10). Không chia toàn mixed law cho mass .984120 vì sẽ đổi AoA atom. Các trường raw/physical/normalization/tail được lưu riêng.

## D. Ba moment của cùng luật physical

\[
m_1=P_1B\frac{dQ(d+1)}{(d+1)Q(d)},\qquad
m_h=P_1\sqrt B\frac{dQ(d+1/2)}{(d+1/2)Q(d)},
\]

\[
m_n=1+\chi_{\rm het}+(\xi_{\rm ch}-1)m_1.
\]

| Moment | Closed form | Independent integration |
|---|---:|---:|
| mean_eta | 0.23790886783673015 | 0.23790886783673013 |
| mean_sqrt_eta | 0.40114871429673266 | 0.4011487142967326 |
| mean_eta_xi_total | 2.662230522819319 | 2.662230522819318 |

Raw literal third moment vẫn là `2.619955004470893`; difference physical−raw là `0.04227551834842602`. Tại eta=0, dùng limit của ηξ_total bằng `1+χ_het=2.895714285714286`; không gọi ξ_total(0) hoặc chia cho 0. Atom contribution được đưa vào independent noise integration riêng.

## E. Noise audit

`ξ_ch=.0186 SNU` cố định, phase OFF. `χ_het=(2−R+2ξ_det)/R=1.8957142857142857` dùng cho third total-noise moment và receiver bookkeeping, không được trực tiếp đưa vào pre-detection b hoặc Eq. (20).

\[
N_{\rm fade}=(m_1-T_{\rm eff})V_A,\qquad
N_{\rm ch}=m_1\xi_{\rm ch},\qquad N_{\rm out}=N_{\rm fade}+N_{\rm ch}.
\]

Đường ba moment độc lập về đại số:

\[
N_{\rm out}=(m_1-T_{\rm eff})V_A+m_n+m_1-1-\chi_{\rm het}.
\]

Reference algebra: `N_fade=.42343717270144676`, `N_ch=.0044251049417631805`, `N_out=.42786227764320994`; hai đường bằng nhau trong dung sai `1e-10`. Detector và pure-loss terms bị loại khỏi **quantum excess** đúng một lần bằng identity; giá trị m_n khoảng 2.66 không được dùng nguyên làm penalty của Z.

## F. Covariance, Eq. (20), interval và detector

\[
T_{\rm eff}=m_h^2,\quad \xi_{\rm eff}=N_{\rm out}/T_{\rm eff},
\quad a=1+V_A,\quad b=1+m_1(V_A+\xi_{\rm ch}),
\]

\[
Z^*=2\sqrt{T_{\rm eff}}C-\sqrt{2T_{\rm eff}\xi_{\rm eff}w}.
\]

| Reference algebra field | Giá trị |
|---|---:|
| T_eff | 0.16092029098192165 |
| Var√η | 0.0769885768548085 |
| ξ_eff | 2.658846035092476 |
| a | 6.5 |
| b | 2.312923878043779 |
| C, giữ cached | 3.2113076519605626 |
| w, giữ cached | 1.0248765983174194e-6 |
| Z_star | 2.575487382363995 |
| DBL upper endpoint | 2.5773603608169613 |
| Physical correlation cap | 3.1379816897694517 |
| Physical intersection | [2.575487382363995, 2.5773603608169613] |
| λ1, λ2 của pre-detection covariance tại Z_star | 5.668978112682573; 1.4819019907263522 |
| Z_worst / χ_BE / selected detector conditional spectrum | **UNAVAILABLE: trusted receiver model unresolved** |

Khoảng lấy từ DBL arXiv:2103.13945v3 trang 12 Eqs. (11)–(13): nbar=VA/2, c1=m_h C, c2=m_h nbar, nB=(m1 VA+m1 ξ_ch)/2. Radius là `sqrt(2w N_out)`. Intersect với `|Z|≤sqrt(ab−1−|a−b|)`; empty intersection bị từ chối.

Ideal-only maximizer xét mọi local grid maximum, bounded refinement, endpoints và denser grid; không giả định monotonicity. Unit fixture còn có interior optimum và độc lập 4097-grid/bounded comparison. Bất kỳ điểm covariance bị từ chối trong kiểm tra numerical interval làm chi_BE null; không clipping negative discriminant hoặc λ<1. Factorized symplectic algebra giảm cancellation nhưng không thay toán học.

Mặc định **detector trusted, R=.7, ξ_det=.0135**. Repository chỉ có verified ideal Holevo (`SECURITY_SCOPE_FREEZE`, covariance.py, holevo.py); literal total-noise substitution không phải trusted receiver implementation. Do đó selected nonideal `chi_BE`, `Z_worst`, `K_raw`, `K_operational` là null, có lý do rõ ràng. Không dùng λ3=a−Z²/(b+1) cho receiver nonideal. Ideal λ3 chỉ có trong API/test explicit ideal mode. Phần numerical search không có rigorous global error enclosure; không gọi nó là continuous certification.

Deterministic tests gồm T0=.07,.2,.3,.7 với/no ξ_ch. Dùng **tagged analytic delta law**, kiểm tra m1=T0 và m_h=sqrt(T0), báo square-rounding residual rồi áp dụng identity toán học T_eff=T0, variance=0. Đây không phải clipping integrated moments. Generic untagged moment-order failure vẫn bị từ chối. T_eff=0 báo ξ_eff undefined; không tạo rate bằng chia 0.

## G. Discrete fading-mixture MI

Implemented likelihood là actual pooled-mixture:

\[
p(y|i)=P_0p(y|i,0)+P_1\int_0^1p(y|i,\eta)f_{\rm active,phys}(\eta)d\eta.
\]

Receiver classical model được ghi rõ:

\[
Y|i,\eta\sim\mathcal{CN}\left(\sqrt{R\eta}\alpha_i,
1+\tfrac12R\eta\xi_{\rm ch}+\xi_{\rm det}\right).
\]

Complex shot-noise variance là 1; ξ_det output-referred, được cộng một lần. `R(1+χ_het)/2=1+ξ_det` kiểm tra bookkeeping. Receiver likelihood này không tự chứng minh detector security. Nó dùng cùng PMF/amplitudes được verified với C,w.

Sampling dùng exact rho0 raw lognormal-minus-exponential, rejection tại eta≤1 và Bernoulli outage; có draw budget. Likelihood dùng positive joint complex Gauss-Legendre quadrature, order 32→64→128→256 tối đa, mass/moment checks `1e-6`, paired likelihood-refinement tolerance `1e-4 bit`. Không dùng product I_R+I_Q sau pooling; không thay bằng Gaussian-input Eq. (17) hoặc effective AWGN.

MI là **sampling estimate với numerical likelihood quadrature**, không gọi numerical exact. Default samples512/seed20261013; hard cap4096, batch≤64. `MI_valid` cần likelihood convergence, sampling SE≤.002 bit và estimate trong [0,H(p)] theo stated roundoff allowance; estimator signed được giữ nguyên khi không đạt. CI 95% chỉ là normal approximation cho sampling, không bao gồm rigorous quadrature bias. Context bind ensemble, channel, detector, seed/numerics và producer hash; không reuse historical MI cache.

8 MI tests có 256-symbol active synthetic fixture và all-outage fixture, mixed outage likelihood, normalization/moments, SNU, reproducibility và failure gates. **Reference 256-QAM MI/SKR chưa chạy**, không tuyên bố precision certification ở reference hoặc cả catalog. Default evaluator dừng trước MI khi Holevo security unresolved.

## H. Test status A–O

Receipt hiện hành `results/manuscript_corrected_3moments/implementation_validation/attempt_2/validation.json`: **24 tests PASSED**, 0 failures/errors; thời gian test runner `2.407s`. `CURRENTLY_VERIFIED_PASS` là software/unit/regression result, không phải security readiness.

| Test | Status và phạm vi |
|---|---|
| A | PASSED: 256 centered MB, PMF/C4/VA, exact cached source identity |
| B | PASSED: literal raw producer unchanged; known mass .984120 reproduced |
| C | PASSED: retained/full/tail independent quadrature và physical mass=1 trong1e-10 |
| D | PASSED: same-law m1/m_h/m_n, independent integration và third identity |
| E | PASSED: T_eff=m_h² và ordering; generic failure không clipping |
| F | PASSED: direct/three-moment excess noise agreement |
| G | PASSED: b identities agreement; receiver noise không vào pre-detection b |
| H | PASSED: protected Eq20 và corrected equivalent paths |
| I | PASSED: deterministic/noiseless/zero limits, gồm nonbinary analytic delta |
| J | PASSED: finite covariance, uncertainty/spectrum, invalid states rejected, no repairs |
| K | PASSED ideal software interval/maximizer tests; **BLOCKED selected trusted nonideal security** |
| L | PASSED mixture implementation/256 fixtures; **NOT RUN reference numerical precision certification** |
| M | PASSED actual historical K=.07798099387393764; 26 objective contexts compatible |
| N | PASSED actual literal mass=.9841200272202841, raw K=−2.454774809836829 |
| O | PASSED: 3643 protected hashes unchanged; full final integrity receipt |

Entry `--help` passed; production entry NOT RUN. Optional single-point SKR không chạy vì prerequisite receiver/security chưa đủ. Không full26, không all182 evaluation, không AP/new C,w, không AO/global search, không restart Objective C, không training/final-test/held-out/publication và không commit/push.

## I. Preservation và trạng thái repository

Protected baseline gồm tracked project science/results, existing source/scripts/configs/tests, literal output và prior review. Old source/cache/catalog182/Objective B/Objective C/historical results vẫn byte-identical. Các file trạng thái được cập nhật riêng theo evidence-first; pre-existing state edits được lưu trong baseline/startup diff, không bị nhầm thành thay đổi scientific source của task này.

Frozen actual SHA256 vẫn `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`, khác historical AGENTS value; không sửa/restore frozen specification. Objective C checkpoint `USER_STOPPED`, PID0; process inspection không thấy original AP/controller đang chạy. Lifecycle vẫn `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. New scientific functional chỉ tồn tại trong namespace riêng; không thay baseline-selection, thresholds hoặc attack_class của historical protocol.

## J. Scientific limitations và điều kiện tiếp theo

Active conditioning giữ raw Eq10 và AoA atom nhưng là model choice. Mode chỉ validated rho0, fixed centered C4 source, independent positive-amplitude fading với phase tracked, pooled all uses kể cả outage. Public CSI, discard outage hoặc source adaptation sẽ cần protocol/moment conditioning khác; không lấy instantaneous average thay pooled MI.

Mean amplitude m_h khác power m_h². Effective ξ_eff chứa fading-induced term dù physical ξ_ch cố định. Eq20 giữ nguyên với đúng excess inputs; correlation lower endpoint khác Holevo maximizing correlation. General DBL moments xác lập interval theo giả thiết, chưa tạo finite-size/composable proof hoặc thực nghiệm parameter estimation.

Trusted nonideal receiver Holevo là blocker chính. MI routine có sampling/likelihood diagnostics, chưa có rigorous total-error enclosure hoặc reference-point precision receipt. Requested PDF `(37)(2)` chưa được xác minh; G_d/physical optics source gap của literal mapping vẫn được ghi nhận, không âm thầm thay channel equations. Frozen-hash discrepancy vẫn là blocker cho promotion.

Chỉ sau khi receiver security model được xác lập và provenance/MI/Holevo precision đủ mới xét single-point SKR. Dừng sau implementation, lightweight tests và report; các sweep/AO/AP cần yêu cầu mới.

BLOCKED_BY_SCIENTIFIC_MODEL
