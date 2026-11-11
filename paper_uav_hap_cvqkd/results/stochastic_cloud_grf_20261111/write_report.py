"""Build the human-readable report from saved evidence only."""
from pathlib import Path
import csv,json
import numpy as np

OUT=Path(__file__).resolve().parent


def build():
    r=json.loads((OUT/'validation.json').read_text());c=r['parameters']
    tracks=list(csv.DictReader((OUT/'track_segments.csv').open()))
    main=[v for v in tracks if int(v['seed'])==c['seed']]
    spans=np.array([float(v['observed_span_s']) for v in main])
    censored=np.mean([v['roi_censored']=='True' or v['left_time_censored']=='True' or v['right_time_censored']=='True' for v in main])
    temporal=list(csv.DictReader((OUT/'material_correlation.csv').open()))
    rows='\n'.join(f"| {v['lag']} | {float(v['theory']):.6f} | {float(v['empirical']):.6f} | {float(v['CI95_half']):.6f} |" for v in temporal)
    main_rows='\n'.join(f"| {name} | {value:.9g} |" for name,value in r['main'].items())
    ensemble_rows='\n'.join(f"| {name} | {v['mean']:.9g} | {v['SE']:.9g} | {v['CI95_half']:.9g} |" for name,v in r['ensemble'].items())
    params='\n'.join(f'| {name} | {value} |' for name,value in c.items())
    outside95=sum(abs(v['estimate']-v['target'])>v['CI95_half']+1e-10 for v in r['checks'])
    max_z=max(abs(v['estimate']-v['target'])/v['SE'] if v['SE']>0 else 0 for v in r['checks'])
    failed='Không có kiểm tra vượt giới hạn 4-SE đặt trước.' if not r['failed_checks'] else '\n'.join(f"- {v['name']}: estimate={v['estimate']:.8g}, target={v['target']:.8g}, SE={v['SE']:.8g}." for v in r['failed_checks'])
    text=f'''# Báo cáo trường mây GRF exponential có gió và AR(1)

Ngày 2026-11-11. Tên mô hình: **Spatiotemporal Stochastic Cloud Field Model using
Spatially Correlated GRF, Wind Advection and AR(1) Temporal Evolution**.
Phạm vi `SYNTHETIC_CLOUD_GENERATION_ONLY`; numerical integrity
`{r['numerical_integrity_status']}`; ensemble descriptive checks `{r['status']}`.

Đã chạy {len(r['independent_seeds'])} seed, mỗi seed 1000 slot k=0..999; seed
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

Ở đây rho={r['rho']:.16g}, innovation scale={r['alpha']:.16g}.
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

Min eigenvalue **{r['spectrum']['minimum_eigenvalue']:.12g}**, max eigenvalue
**{r['spectrum']['maximum_eigenvalue']:.12g}**; số eigenvalues âm và clipping đều
**0**. Sai số tái dựng covariance lớn nhất
**{r['spectrum']['covariance_reconstruction_max_error']:.6g}**. Không thêm jitter,
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
**{r['max_space_time_embedding_target_error']:.6g}**. Đây là kiểm tra riêng ngoài
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
{params}

Seed ensemble: {r['independent_seeds']}.
Miền tổng hợp {r['boundary']['synthetic_extent_xy_m']} m; shape nội bộ [y,x]
{r['boundary']['internal_shape_yx']}; guard {c['guard_m']} m.
Output centres 20,60,...,1980 m; arrays [k,y,x], y tăng lên; không area-average.
Thời điểm cuối 999 s; padding bảo thủ đến 1000 s.

Default theta={r['main_theta']:.16g} là quantile ensemble N(0,1), không phải
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

- Displacement = {r['frozen']['displacement_xy_m_per_slot']} m/slot;
  sau 8 slot x={r['frozen']['eight_slot_displacement_x_m']} m.
- Common-interior error sau dịch một output cell:
  {r['frozen']['eight_slot_common_interior_max_error']}.
- Giá trị full-field sau permutation và trước dịch giống bitwise sau khi sort:
  {r['frozen']['sorted_frozen_values_bitwise_identical']}.
- Relative full variance change={r['frozen']['full_variance_relative_change']:.6g};
  max covariance change={r['frozen']['full_covariance_max_abs_change']:.6g}.
- Tagged seam impulse tại 0/400/999 có ROI peak
  {r['frozen']['tagged_seam_marker_ROI_max']}; positive control peak=1.

Frozen ROI mean/coverage vẫn biến thiên khi vùng mây khác đi qua cửa sổ cố định.
Điều đó không phải numerical diffusion. Hình H phân biệt ROI Eulerian này với
material-frame MSE=0 của frozen field và MSE lý thuyết 2(1-rho^k) khi evolving.

## Kết quả ensemble, uncertainty và histogram

| Main-seed statistic | Value |
|---|---:|
{main_rows}

| Statistic across seeds | Mean | SE | Approx. CI95 half-width |
|---|---:|---:|---:|
{ensemble_rows}

Các cloud fractions trong bảng dùng đơn vị tỷ lệ 0..1. CI là Student-t xấp xỉ
qua **seed độc lập**, không coi các ô/slot tương quan là samples độc lập.
ROI population variance kỳ vọng là **{r['expected_ROI_population_variance']:.12g}**,
khác marginal second moment target=1, vì trừ sample ROI mean trong một trường
có tương quan. Không renormalize để làm phẳng curves.

Đã đánh giá **{len(r['checks'])} kiểm tra 4-SE đặt trước**, có
**{len(r['failed_checks'])}** vượt ngưỡng:

{failed}

Các kiểm tra này là descriptive numerical audit, không phải bảo đảm đồng thời
trên miền liên tục hay chứng nhận khí tượng. Có **{outside95}/{len(r['checks'])}**
pointwise CI95 không chứa target; sai lệch chuẩn hóa lớn nhất là **{max_z:.6g} SE**.
PASS theo 4-SE không được diễn giải thành mọi CI95 đều bao trùm lý thuyết.
Histograms tại bảy thời điểm được
lưu trong ensemble NPZ và overlay với N(0,1) ở Figure A. Unit test marginal
Gaussian dùng các draw độc lập tại một điểm, không dùng iid-pixel p-values.

| Material lag (s) | rho^m | Empirical | CI95 half-width |
|---:|---:|---:|---:|
{rows}

Các covariance tại fixed h và temporal lags có CSV riêng
`space_time_covariance.csv`, gồm cả theory unwrapped, theory embedding, estimate,
SE và CI95. Intensity không được gán correlation Gaussian này.

## Morphology và observed lifetime proxy

Đếm components 8-neighbour trên ROI 40 m, không nối qua biên. Diện tích=count
x1600 m². Material-frame RMS và presence IoU kiểm tra biến đổi hình dạng sau
bù gió chính xác. Các đường nằm ở `time_statistics.csv` và ensemble NPZ.

Seed chính có **{len(main)} observed track segments**; span=(last-first)*dt,
mean **{spans.mean():.6g} s**, median **{np.median(spans):.6g} s**, max
**{spans.max():.6g} s**; tỷ lệ ROI/time-censored **{censored:.6%}**.
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
{r['protected_inputs']['count']} tệp cũ bảo vệ bằng hash không đổi. Worktree
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
'''
    (OUT/'report_vi.md').write_bytes(text.encode('utf-8'))
    print('Wrote report_vi.md from saved evidence')


if __name__=='__main__':build()
