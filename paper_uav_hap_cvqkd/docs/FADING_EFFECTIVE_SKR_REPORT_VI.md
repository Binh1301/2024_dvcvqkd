# Cập nhật SKR theo mômen fading và heterodyne

Ngày 2026-10-16. PRELIMINARY_MOMENT_MATCHED_GAUSSIAN_FADING_APPROXIMATION. Không đổi production default.

## Công thức và audit

Tệp thực tế được cung cấp là 2026__Binh_s_work (37).pdf, SHA256 0ea5d889ccd678de92a1a1a70b424af918794eac2e7f98106cbc5f785a43146b. Trang3 chứa III-A/(11)-(21); biến thể (37)(3).pdf trong task không có trên máy. Bản thảo dùng likelihood vô hướng và conditional eigenvalue homodyne; code giữ complex heterodyne/reverse reconciliation, beta=.95, R=1, xi_det=0. Nguồn kiểm tra heterodyne: Denys–Brown–Leverrier, Quantum5,540(2021), p9, https://quantum-journal.org/papers/q-2021-09-13-540/pdf/.

Đặt $m_1=E[T]$, $m_{1/2}=E[\sqrt T]$, $T_{eff}=m_{1/2}^2$, $V_{fad}=m_1-T_{eff}$. Mômen total-noise hiện có là $m_{\xi,total}=1+\chi_{het}+(\epsilon_{ch}-1)m_1$. Vì nó chứa loss vacuum và detector term, chỉ phần $m_{excess}=m_{\xi,total}-(1+\chi_{het}-m_1)=m_1\epsilon_{ch}$ đi vào excess noise.

Legacy cố ý dùng $N_{old}=T_{eff}\epsilon_{ch}$, $b_{old}=1+T_{eff}(V_A+\epsilon_{ch})$. Updated dùng $N=V_{fad}V_A+m_1\epsilon_{ch}$, $\xi_{eff}=N/T_{eff}$ và $b_{pre}=1+T_{eff}V_A+N=1+m_1(V_A+\epsilon_{ch})$. Vacuum Bob=1 chỉ xuất hiện một lần. Heterodyne likelihood là $CN(\sqrt{T_{eff}}\alpha,1+N/2)$ trên cả hai quadrature; covariance có $\lambda_3=a-Z^2/(b+1)$, không dùng homodyne $\sqrt{a(a-Z^2/b)}$. $Z_-=2m_{1/2}C-\sqrt{2Nw}$, với đúng C,w/ensemble đã xác thực.

Bộ receiver mới chỉ hỗ trợ ideal heterodyne hiện tại; R≠1/xi_det≠0 bị từ chối rõ, không giả vờ có trusted-detector security đã kiểm chứng. Chi_het=1 là added heterodyne vacuum ở receiver; không đưa nó thành noise Eve-accessible. Phương sai fading không bị giảm để ép SKR dương.

PDF thô trên[0,1] có retained mass<1. Giữ nguyên luật vật lý đã được author chấp nhận trong repo: active PDF conditioned trên(0,1], giữ atom AoA P0 tại0. Không đổi Eq10, không đổi normalizer hoặc AoA probability. Binary cloud là outage độc lập ở lớp mission, không đưa vào mômen clear-sky; cloud blocked đặt S=0 mà không tính QKD tạiT=0. Tham số vật lý giữ đúng config repo (D_r=.55m, beam_waist=0.0986760647169751m), không thay bằng mặc định D_r=.08m/divergence233urad ở SectionIV của PDF.

## Reference và đối chiếu

| Đại lượng, cùng nguồn nu=.17/VA=5.046875 | Legacy | Updated |
|---|---:|---:|
| mean_eta | 0.237908867837 | 0.237908867837 |
| T_eff | 0.160920290982 | 0.160920290982 |
| N_eff | 0.00299311741226 | 0.392976828756 |
| xi_eff | 0.0186 | 2.44205889983 |
| b | 1.81513771096 | 2.20512142231 |
| I_AB | 0.49104803313 | 0.421572584961 |
| chi_BE | 0.407760771595 | 1.14663448291 |
| SKR | 0.058734859879 | -0.746140527195 |

Fading variance=0.0769885768548; Delta_fad=0.388551723814; m_excess=0.00442510494176. Raw K được lưu có dấu; usable=max(0,raw).

Nguồn được tối ưu lại riêng tại100 vị trí bằng toàn bộ197MB và30Uniform exact sources; không dùng lại K legacy. [Clear comparison](../results/fading_effective_binary_cloud_20261016/clear_legacy_updated.csv) ghi raw/usable K và nu/VA tối ưu của cả hai model theo vị trí.

## Validation và Monte Carlo

17 focused tests PASS; deterministic delta, vacuum/detector accounting, likelihood2D, ensemble identity, batch/scalar/full-product equivalence, physicality, smallT và legacy preservation đều có kiểm tra. Log lỗi đầu tiên được giữ: legacy strict Jensen guard không nhận một số delta do sqrt rounding; dùng các delta binary-exact để đối chiếu và test riêng exact-delta tag ở.16/.5. Không sửa legacy để ép PASS.

MC chỉ dùng validation, không thay analytic moments chính. Mỗi vị trí0/9/44/90/99 lấy262144 mẫu từ exact physical sampler,16 replication, cùng AoA atom và active conditioning. So m1/mhalf/mxi_total với SE mẫu; so K(MC moments) và K(analytic moments) bằng cùng evaluator, tolerance cố định5SE+1e-6bit. [Mômen](../results/fading_effective_binary_cloud_20261016/analytical_vs_MC_moments.csv), [SKR](../results/fading_effective_binary_cloud_20261016/analytical_vs_MC_SKR.csv), [replications](../results/fading_effective_binary_cloud_20261016/MC_replications.csv).

Tại cùng nguồn reference, moment-effective K=-0.746140527195; MC trung bình K(T_i)=0.165663209065 ± SE0.01126, còn mean positive-part=0.165663209065. Không đồng nhất các đại lượng: K(E covariance) là functional khác E[K(T)], và E[max(K,0)] đòi CSI/postselection/transmit-abstain. Không được coi chúng là bằng chứng bảo mật vận hành.

## Binary P1–P3

Tái sử dụng đúng ma trận cloud cũ và hash generator, cùng16 cấu hình×100 mission,30×20s, constraints, lambda, threshold và DP. Không đổi optimizer hoặc cloud model. [Scheme comparison](../results/fading_effective_binary_cloud_20261016/scheme_legacy_updated_comparison.csv), [paired differences](../results/fading_effective_binary_cloud_20261016/paired_updated_minus_legacy.csv), [updated summary](../results/fading_effective_binary_cloud_20261016/summary_statistics.csv).

Max raw MB=-0.027942008491; max raw Uniform=-0.0275937177584. All MB usable zero=True; all Uniform usable zero=True. Nếu mọi usable rate bằng0 thì không có mobility SKR gain; relative improvement so reference0 để trống, không báo phần trăm giả.

## Trả lời các câu hỏi bắt buộc

- Vì sao trước đây thiếu fading variance? Đó là nhánh diagnostic có chủ ý effective_channel_no_fading_noise (EVID0183/DEC0166), dùng để cô lập ảnh hưởng variance, không phải đầy đủ fading security.
- Hiện variance được đưa vào thế nào? Qua V_fad*VA trong N, cùng mean_T*xi_ch; cùng N đi vào MI, Z-minus và covariance.
- Noise có tính đúng một lần? Có trong phạm vi ideal heterodyne: tách mxi_total khỏi vacuum/detector trước khi lập b_pre; measurement added vacuum chỉ ở likelihood và b+1.
- Receiver còn heterodyne? Có; complex two-quadrature likelihood và heterodyne Schur complement giữ nguyên. Không chuyển sang homodyne của manuscript.
- Vì sao khác kết quả Monte Carlo? Moment matching và average instantaneous rates là hai functional khác nhau; còn postselection và sampling uncertainty phải báo riêng. Xem diagnostic matched-source mới, không ghép số lịch sử khác nguồn/cấu hình.
- Có positive SKR với cấu hình gốc? Xem max signed rates và toàn bộ catalog ở trên; không chỉnh vật lý hoặc noise để ép dương.
- Đủ publication chưa? Chưa. Đây là xấp xỉ Gaussian moment-matched; conditional likelihood thật của fading không Gaussian/homoscedastic, security/CSI/block-bin estimation và finite-size proof chưa được thiết lập. Direct Z-minus giữ đúng scope được yêu cầu, không tuyên bố chứng nhận full interval hay global continuous optimum.

## Files và interfaces

Mới: src/fading_effective_skr.py (effective_channel, heterodyne_likelihood, evaluate_candidate/evaluate_batch), scripts/run_fading_effective_binary_cloud.py (reference, monte_carlo, full, verify, report), configs/fading_effective_binary_cloud.json và tests/test_fading_effective_skr.py. Cập nhật docs/FADING_EFFECTIVE_SKR_REPORT_VI.md cùng Evidence/Decision/ProjectState/NextActions/Handoff theo receipt. Các source/kernel/config legacy, shared caches, binary generator/DP và mọi kết quả trước task đều giữ nguyên. Không đổi production default, training/test dataset access, publication evaluation, commit hoặc push.

Run stages bằng .venv-binary-cloud/Scripts/python.exe -X utf8 -B scripts/run_fading_effective_binary_cloud.py --stage reference|mc|full|verify|report. Mỗi stage tính số từ chối ghi đè khi đã hoàn tất; journal mới resume chỉ cùng producer/input identity. Tất cả kết quả trong namespace riêng fading_effective_binary_cloud_20261016; không sửa Downloads manuscript.

## P1 tối ưu tại vị trí tham chiếu44

Bảng này cho argmax raw trong catalog; cặp nguồn hai bên khác nhau. Bảng fixed-source trước đó mới cô lập riêng thay đổi evaluator.

| Quantity | Legacy optimum | Updated raw optimum |
|---|---:|---:|
| Mean T | 0.237908867837 | 0.237908867837 |
| Effective T | 0.160920290982 | 0.160920290982 |
| Fading variance | 0.0769885768548 | 0.0769885768548 |
| Effective excess noise | 0.0186 | 0.0394594076632 |
| I_AB | 0.49104803313 | 0.0028899055756 |
| chi_BE | 0.407760771595 | 0.0311267696097 |
| Signed raw K | 0.058734859879 | -0.0283813593129 |
| Usable K | 0.058734859879 | 0 |
| Optimal nu_raw | 0.17 | 0.3 |
| Optimal V_A | 5.046875 | 0.025 |

Khi tất cả raw maxima âm, nu/VA mới chỉ là cặp ít âm nhất trong catalog. Không có cấu hình vận hành tạo khóa được xác lập từ các giá trị usable0 này; không suy rộng thành kết luận bất khả thi cho mọi nguồn hoặc mọi protocol.

## So sánh S1–S4 ở cấu hình cloud mặc định

Mỗi ô là legacy → updated, mean trên cùng100 mission. Availability dùng K_min=.001 bits/use.

| Source | Scheme | Mean SKR | Availability | Flight m | Penalized objective |
|---|---|---:|---:|---:|---:|
| MB | S1 | 0.034105375 → 0 | 0.58066667 → 0 | 0 → 0 | 0.034105375 → 0 |
| MB | S2 | 0.061241611 → 0 | 0.992 → 0 | 0 → 0 | 0.061241611 → 0 |
| MB | S3 | 0.063193566 → 0 | 0.99966667 → 0 | 1417.525 → 0 | 0.063193566 → 0 |
| MB | S4 | 0.063103922 → 0 | 0.99966667 → 0 | 216.48215 → 0 | 0.06288744 → 0 |
| Uniform | S1 | 0.0026630544 → 0 | 0.58066667 → 0 | 0 → 0 | 0.0026630544 → 0 |
| Uniform | S2 | 0.0051498017 → 0 | 0.979 → 0 | 0 → 0 | 0.0051498017 → 0 |
| Uniform | S3 | 0.0054320294 → 0 | 0.99966667 → 0 | 1417.525 → 0 | 0.0054320294 → 0 |
| Uniform | S4 | 0.0053514393 → 0 | 0.99533333 → 0 | 90.620844 → 0 | 0.0052608185 → 0 |

Với lambda=0 và mọi usable rate=0, tất cả quỹ đạo feasible có cùng objective0; quỹ đạo đứng yên trả về là tie-breaking của DP. Không diễn giải flight0 thành lợi ích vật lý/propulsion energy hoặc một optimum quỹ đạo duy nhất.

## Đối chiếu chính xác Monte Carlo lịch sử

[Artifact kiểm tra](../results/fading_effective_binary_cloud_20261016/historical_MC_comparison.json) xác nhận cùng nguồn nu=.165/VA=5.5, ensemble hash và cùng luật vật lý với ideal reference20261013. Đây là nguồn khác với fixed reference nu=.17/VA5.046875 ở đầu báo cáo.

Pooled-mixture MC lịch sử: I_AB=0.465263799197, SE=0.0194686764102, N=4096, K_raw=-0.777589014735. Updated moment-Gaussian tại đúng nguồn đó: I_AB=0.448418467694, chi_BE=1.21958962397, K_raw=-0.793592079663. Nó tái lập nhánh Gaussian approximation lịch sử với residual K=8.88e-16.

Sai khác MC/Gaussian ở đây là khác likelihood pooled-fading so với AWGN moment approximation, kèm sampling uncertainty. MC cũ không đạt mục tiêu SE=.002 và không được chạy lại trong task này; không nâng nó thành CURRENTLY_VERIFIED_PASS cho mixture/security. Khác biệt này cũng khác E[K(T)] statewise CSI ở diagnostic512 mẫu mới. Không có bound chặt cho approximation error hoặc bảo mật fading đầy đủ.

Postprocessing hình/bảng: scripts/plot_fading_effective_comparison.py; chỉ đọc dữ liệu đã verified, không tính lại source/MI/Holevo hoặc sửa generator/DP. Chạy sau --stage report để nhận layout cuối. Các lỗi ban đầu và lần dừng vì khóa checkpoint được giữ trong attempts/ và logs; journal resume cùng producer/input, không bỏ điểm thất bại hay dùng K legacy thay thế.
