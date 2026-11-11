# Báo cáo trường mây GRF exponential có gió và AR(1)

Ngày 2026-11-11. Tên mô hình: **Spatiotemporal Stochastic Cloud Field Model using
Spatially Correlated GRF, Wind Advection and AR(1) Temporal Evolution**.
Phạm vi `SYNTHETIC_CLOUD_GENERATION_ONLY`; numerical integrity
`CURRENTLY_VERIFIED_PASS`; ensemble descriptive checks `CURRENTLY_VERIFIED_PASS`.

Đã chạy 11 seed, mỗi seed 1000 slot k=0..999; seed
chính 20261111. Frozen-field được kiểm chứng trước khi chạy evolving ensemble.
Không triển khai optical blockage, attenuation, QKD, SKR, finite-size hay UAV.

## Mô hình và dẫn xuất covariance

```text
Ks(r,r') = exp(-norm(r-r')/ell_c)
G0, eta1, eta2,... độc lập, cùng luật Gaussian N(0,Ks)
rho = exp(-dt/tau_c)
G[k+1](r) = rho*G[k](r-v*dt) + sqrt(1-rho^2)*eta[k+1](r)
I[k](r) = A*max(0,G[k](r)-theta_c)^q
```

Ở đây rho=0.9966722160545233, innovation scale=0.08151376414425716.
Phép dịch A là permutation trên lưới nội bộ nên A C A^T=C. Vì innovation có
đúng covariance ban đầu, Cov(G_next)=rho^2*C+(1-rho^2)*C=C. Điều kiện bảo toàn
C là thiết yếu; chỉ hệ số sqrt(1-rho^2) không đủ nếu nội suy làm đổi C.

Từ code update, tương lai tại r+h chứa rho^m*G[k](r+h-v*m*dt) cộng innovations
độc lập với G[k]. Với h tính từ điểm trước đến điểm sau:

```text
R(h,m) = E[G(r,k)G(r+h,k+m)]
       = rho^m exp(-norm(h-v*m*dt)/ell_c), m>=0.
```

Do v_x=-5, m=8, đỉnh ở h_x=-40 m. Đối chiếu cả h=-40 và +40 trong CSV và
Figure G kiểm tra trực tiếp dấu; không thay bằng công thức có h+v*m*dt.
Material compensation đi theo h=v*m*dt cho target rho^m. Công thức này chỉ
áp dụng Gaussian latent, không gán cho intensity phi tuyến hoặc presence mask.

## Thuật toán sinh dữ liệu và tính đúng của FFT

Pseudo-code:

```text
1. Tạo lưới tổng hợp đủ cho ROI + gió 5000 m + guard và covariance lags.
2. c[dy,dx] = exponential covariance tại minimum-image distance.
3. lambda = FFT(c); kiểm tra phổ thực, mọi eigenvalue >=0; nếu không thì FAIL.
4. drawGRF = IFFT(sqrt(lambda) * FFT(iid N(0,1))). Giữ DC; không sample-normalize.
5. Sinh G0; chọn theta một lần; kiểm chứng frozen A^k G0, rho=1.
6. Mỗi slot: dịch nguyên trên lưới nội bộ, cộng innovation GRF độc lập cùng Ks.
7. Lấy mẫu 50x50 điểm tâm ô ROI; xuất G, relative intensity, presence diagnostic.
8. Tính thống kê/covariance/histogram/morphology; lặp độc lập qua 11 seed.
```

Min eigenvalue **0.0124993489975**, max eigenvalue
**1256.73727707**; số eigenvalues âm và clipping đều
**0**. Sai số tái dựng covariance lớn nhất
**2.22045e-16**. Không thêm jitter,
không clipping eigenvalue âm, không bỏ DC, không chia cho sample standard deviation.
Mean=0, marginal variance=1 là target ensemble, không ép từng crop mean/variance.
GRF đầu ra đã được lọc không gian, không phải white noise độc lập từng ô.

Lưới output 40 m không biểu diễn chính xác mọi fractional exponential lag bằng
một interpolant Fourier hữu hạn. Để tránh thay covariance tại subpixel offset,
implementation dùng **5 m theo x, 40 m theo y nội bộ**, rồi lấy mỗi ô x thứ 8.
Gió -5 m/slot là -1 ô nội bộ; vì thế không dùng repeated linear interpolation,
và vẫn chính xác -0.125 output cell/slot, -1 output cell/8 slots.
Các displacement không commensurate với lưới nội bộ bị từ chối rõ ràng, không
làm tròn gió. Có thể cấu hình refinement khác. Không giả định có dữ liệu khí
tượng đo ở độ phân giải 5 m.

Các spatial/time stencils được kiểm tra đều nằm dưới half-period của embedding;
maximum chênh giữa kernel nhúng và exponential unwrapped ở các stencil là
**0**. Đây là kiểm tra riêng ngoài
PSD. Covariance Monte Carlo được kiểm tra theo khoảng cách ở hai trục và đường
chéo, tại đầu và cuối qua nhiều seed.

Bounds cho toàn bộ cặp điểm/thời điểm output: |h_x-v_x*m*dt| <=6955 m và
|h_y-v_y*m*dt| <=1960 m, nhỏ hơn half-period 8000/3000 m. Vì thế toàn bộ
covariance Gaussian space-time trên các điểm output cũng bằng kernel lý tưởng
đến sai số floating-point, không chỉ các stencil chọn để kiểm tra. Bounds nằm
trong covariance_support_validation.json; không suy rộng đến off-grid points.

## Tham số thực chạy: tất cả đều illustrative/uncalibrated

| Parameter | Value |
|---|---|
| nx | 50 |
| ny | 50 |
| dx_m | 40.0 |
| dy_m | 40.0 |
| dt_s | 1.0 |
| slots | 1000 |
| vx_m_s | -5.0 |
| vy_m_s | 0.0 |
| ell_c_m | 200.0 |
| tau_c_s | 300.0 |
| seed | 20261111 |
| refine_x | 8 |
| refine_y | 1 |
| guard_m | 1000.0 |
| embedding_scale | 1 |
| initial_fraction | 0.3 |
| threshold_mode | ensemble |
| theta_c | None |
| A | 1.0 |
| q | 1.0 |
| tracking_iou | 0.1 |

Seed ensemble: [20261111, 20261112, 20261113, 20261114, 20261115, 20261116, 20261117, 20261118, 20261119, 20261120, 20261121].
Miền tổng hợp [16000.0, 6000.0] m; shape nội bộ [y,x]
[150, 3200]; guard 1000.0 m.
Output centres 20,60,...,1980 m; arrays [k,y,x], y tăng lên; không area-average.
Thời điểm cuối 999 s; padding bảo thủ đến 1000 s.

Default theta=0.5244005127080407 là quantile ensemble N(0,1), không phải
quantile riêng crop ban đầu. Expected initial presence=30%; số ô ban đầu có
thể khác 30%. Theta giữ cố định suốt mission và qua các seed default. Không
ép độ phủ từng frame. Alternative initial-quantile/fixed modes có trong config.
I là relative intensity, có atom tại zero, không phải CLWC mg/m^3 hoặc suy hao.
Presence mask chỉ dùng chẩn đoán; không phải binary optical blockage.

## Biên và frozen-field trước evolving-field

Backward source của ROI x=[1000,3000] m lần lượt là [3000,5000] ở 400 s,
[5995,7995] ở 999 s, [6000,8000] ở guard horizon 1000 s. Đều nằm trong
miền x=[0,16000] m. Các innovation sinh muộn có tuổi nhỏ hơn và cũng thỏa
bounds. Không characteristic nào cần modulo để lấy dữ liệu vào ROI trong run.
Finite synthetic process vẫn tuần hoàn; không khẳng định tính độc lập miền vô hạn.

Frozen-field rho=1, innovation=0 dùng cùng G0 với seed chính:

- Displacement = [-5.0, 0.0] m/slot;
  sau 8 slot x=-40.0 m.
- Common-interior error sau dịch một output cell:
  0.0.
- Giá trị full-field sau permutation và trước dịch giống bitwise sau khi sort:
  True.
- Relative full variance change=0;
  max covariance change=3.33067e-16.
- Tagged seam impulse tại 0/400/999 có ROI peak
  {'0': 0.0, '400': 0.0, '999': 0.0}; positive control peak=1.

Frozen ROI mean/coverage vẫn biến thiên khi vùng mây khác đi qua cửa sổ cố định.
Điều đó không phải numerical diffusion. Hình H phân biệt ROI Eulerian này với
material-frame MSE=0 của frozen field và MSE lý thuyết 2(1-rho^k) khi evolving.

## Kết quả ensemble, uncertainty và histogram

| Main-seed statistic | Value |
|---|---:|
| initial_fraction | 0.3332 |
| final_fraction | 0.2756 |
| time_mean_fraction | 0.2888036 |
| initial_variance | 1.06161347 |
| final_variance | 1.00497662 |

| Statistic across seeds | Mean | SE | Approx. CI95 half-width |
|---|---:|---:|---:|
| final_fraction | 0.300072727 | 0.018201364 | 0.0405551664 |
| initial_fraction | 0.294181818 | 0.0211049232 | 0.0470246994 |
| time_mean_fraction | 0.300181709 | 0.00922296424 | 0.0205500449 |
| initial_variance | 0.969583965 | 0.0388428252 | 0.0865472079 |
| final_variance | 0.920047008 | 0.0315722304 | 0.0703473133 |

Các cloud fractions trong bảng dùng đơn vị tỷ lệ 0..1. CI là Student-t xấp xỉ
qua **seed độc lập**, không coi các ô/slot tương quan là samples độc lập.
ROI population variance kỳ vọng là **0.951924560732**,
khác marginal second moment target=1, vì trừ sample ROI mean trong một trường
có tương quan. Không renormalize để làm phẳng curves.

Đã đánh giá **152 kiểm tra 4-SE đặt trước**, có
**0** vượt ngưỡng:

Không có kiểm tra vượt giới hạn 4-SE đặt trước.

Các kiểm tra này là descriptive numerical audit, không phải bảo đảm đồng thời
trên miền liên tục hay chứng nhận khí tượng. Có **5/152**
pointwise CI95 không chứa target; sai lệch chuẩn hóa lớn nhất là **3.10073 SE**.
PASS theo 4-SE không được diễn giải thành mọi CI95 đều bao trùm lý thuyết.
Histograms tại bảy thời điểm được
lưu trong ensemble NPZ và overlay với N(0,1) ở Figure A. Unit test marginal
Gaussian dùng các draw độc lập tại một điểm, không dùng iid-pixel p-values.

| Material lag (s) | rho^m | Empirical | CI95 half-width |
|---:|---:|---:|---:|
| 0 | 1.000000 | 1.000000 | 0.000000 |
| 1 | 0.996672 | 0.988665 | 0.007113 |
| 8 | 0.973686 | 0.968485 | 0.012886 |
| 20 | 0.935507 | 0.945182 | 0.023206 |
| 40 | 0.875173 | 0.889731 | 0.029710 |
| 80 | 0.765928 | 0.760546 | 0.050450 |
| 100 | 0.716531 | 0.703574 | 0.056739 |
| 200 | 0.513417 | 0.547763 | 0.054924 |
| 400 | 0.263597 | 0.342322 | 0.056570 |
| 800 | 0.069483 | 0.112523 | 0.090477 |
| 999 | 0.035793 | -0.000878 | 0.077464 |

Các covariance tại fixed h và temporal lags có CSV riêng
`space_time_covariance.csv`, gồm cả theory unwrapped, theory embedding, estimate,
SE và CI95. Intensity không được gán correlation Gaussian này.

## Morphology và observed lifetime proxy

Đếm components 8-neighbour trên ROI 40 m, không nối qua biên. Diện tích=count
x1600 m². Material-frame RMS và presence IoU kiểm tra biến đổi hình dạng sau
bù gió chính xác. Các đường nằm ở `time_statistics.csv` và ensemble NPZ.

Seed chính có **13760 observed track segments**; span=(last-first)*dt,
mean **1.53096 s**, median **0 s**, max
**127 s**; tỷ lệ ROI/time-censored **26.984012%**.
Mỗi seed có summary riêng và toàn bộ segments nằm ở `track_segments.csv`.
Split/merge/ambiguous association kết thúc identity; phát sinh segment mới
không được khẳng định là cloud birth vật lý. Bilinear indicator weights chỉ
dùng trong association, không dịch Gaussian field. Do excursion thresholds,
40 m sampling và quy tắc identity, nhiều đoạn ngắn là có thể; không suy ra
physical cloud lifetime hoặc survival distribution đã hiệu chuẩn.

## Đối chiếu nguồn và mô hình Ibrahim-style

[Peleg et al. (2017), DOI10.1002/2016MS000854](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016MS000854)
là weather generator kết hợp stochastic/physical modules và dữ liệu hiệu chuẩn.
[Carpentieri et al., author preprint](https://arxiv.org/pdf/2305.07293), Sections
2.2-2.4/Eq2, dùng advection và AR(p) phụ thuộc scale với spatially structured noise.
Published reference được yêu cầu là DOI10.1016/j.apenergy.2023.121775; PDF cuối
tại ETH endpoint trả403 nên không mô tả preprint như final version. Peleg HTML
đọc được phần chính nêu trong references.json; requests chi tiết sau đó timeout.

Single-scale exponential covariance, một rho cố định, uniform prescribed wind
và positive-part intensity là **mô hình giản lược đề xuất**, không phải nguyên
văn hoặc tái lập đầy đủ hai bài. Không fit dữ liệu vệ tinh/khí tượng.

Ibrahim-style stationary baseline hiện có dùng weighted fine/coarse spectrum,
Fourier interpolation/shift và DC projection; covariance không phải radial
exponential. Cả hai dùng stationary Gaussian evolution khi A bảo toàn C.
Mô hình mới giữ DC và dùng exponential embedding với lưới gió commensurate,
tốn nhiều điểm nội bộ hơn; intensity mới có zero atom, trong khi softplus cũ
dương ở mọi điểm. Không thay hoặc chạy lại baseline, không kết luận ưu thế
khí tượng hay hiệu suất tổng thể từ khác biệt thiết kế đó.

Đối với UAV-HAP, trường không gian 2 km, tọa độ mét và clock 1 s có thể hỗ trợ
nghiên cứu cloud motion/availability trong tương lai. Hiện chưa có cloud height,
ray intersection, đo LWC, extinction, link outage hoặc liên kết QKD nào. Gaussian
đẳng hướng, ell/tau cố định, bất biến thống kê và phép biến đổi intensity không
mô tả microphysics, mass conservation, convection hoặc weather regimes.

## Tệp, tests và phạm vi thay đổi

Code/config/README mới ở src/stochastic_cloud_grf.py,
configs/stochastic_cloud_grf.json, scripts/run_stochastic_cloud_grf.py,
scripts/plot_stochastic_cloud_grf.py, tests/test_stochastic_cloud_grf.py,
docs/STOCHASTIC_CLOUD_GRF_README.md. Không sửa code hoặc dữ liệu Ibrahim.
Output độc lập này gồm toàn bộ NPZ, CSV, metadata/provenance, source notes,
A-H PNG400dpi/PDF và GIF1000frames; README chứa các đường dẫn cụ thể.

12 tests mới +21 tests hồi quy hai mô hình Ibrahim = **33 scoped tests PASS**,
log tại regression_tests.log. Chưa chạy full repository suite. Artifact verifier,
PDF/GIF QA và git diff --check được ghi trong artifact_verification.json.
941 tệp cũ bảo vệ bằng hash không đổi. Worktree
ban đầu đã có thay đổi EVID0234/DEC0217 và code/artifact Ibrahim chưa track;
preexisting_git_diff.patch cùng protected_inputs.json lưu trạng thái đó.

Chỉ thêm cloud generator độc lập và cập nhật sổ trạng thái/bàn giao liên quan.
Các tệp sửa để ghi nhận nhiệm vụ: docs/EVIDENCE.md, docs/DECISION_LOG.md,
docs/PROJECT_STATE.md, docs/NEXT_ACTIONS.md và .agent/SESSION_HANDOFF.md.
Mọi mục trạng thái có trước được giữ; handoff trước có bản lưu trong output.
Existing scientific source/security functional/frozen model, baseline selection,
QKD threshold approval, publication/security settings không đổi. Không training,
final-test/heldout/publication evaluation. NOT_READY_FOR_PUBLICATION_SCALE_RUNS,
UNVALIDATED_SECURITY_MODEL, E2 INCONCLUSIVE và ObjectiveC USER_STOPPED giữ nguyên.
Frozen historical-hash discrepancy cũ được giữ và không sửa spec.
