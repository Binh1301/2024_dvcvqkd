# Báo cáo mô hình mây Gaussian đa tỷ lệ dừng và chuyển động theo gió

Ngày 2026-11-11. Tên mô hình: **Ibrahim-style Multiscale Gaussian Cloud Model
with Stationary Temporal Evolution and Wind Advection**.
Phạm vi: `CLOUD_GENERATION_ONLY`. Validation số: `CURRENTLY_VERIFIED_PASS`.
Không triển khai optical blockage, suy hao, QKD, SKR, finite-size hoặc UAV optimization.

## Kết quả chính và giới hạn kết luận

Đã chạy đủ **1000 slot k=0..999 cho 11 seed**, gồm seed chính 20261111 và 10
seed bổ sung 20261112..20261121. 11 unit tests và 67 kiểm tra ensemble theo
tiêu chí đặt trước đều PASS. Cấu hình/tiêu chí được lưu trong
`design_receipt.json` trước khi sinh ensemble, không điều chỉnh sau khi xem kết quả.

Gaussian latent X có luật dừng theo thiết kế vì phép dịch Fourier bảo toàn
covariance và innovation có đúng covariance khởi tạo. Ensemble hữu hạn hỗ trợ
implementation này: phương sai crop trung bình ban đầu **1.01403 ± 0.09832**,
cuối **0.99985 ± 0.08678**, với khoảng tin cậy Student-t 95% xấp xỉ qua 11 seed.
Không coi các ô hoặc các slot tương quan là mẫu độc lập.

Độ phủ diagnostic cuối ensemble là **29.7236% ± 3.9562 điểm phần trăm**;
trung bình thời gian rồi trung bình qua seed là **28.5135% ± 2.6332 điểm phần trăm**.
Riêng seed chính kết thúc ở **19.08%**, trung bình mission **24.072%**. Những
con số này được giữ nguyên: tính dừng của X không đảm bảo độ phủ một mission
luôn bằng 30%, và ngưỡng hiệu chuẩn từ X0 có phụ thuộc thống kê với X0.

Đây là bằng chứng cho luật Gaussian tổng hợp hữu hạn được triển khai, không
phải kiểm định tính đúng đắn khí tượng hay kết luận mô hình mới tốt hơn toàn diện.

## Công thức, chuẩn hóa và phân biệt với bài báo

Đã đọc lại Algorithm 1, trang PDF 10/printed page 1378, và Table 2 của Ibrahim
et al. (2024), *Anticipating Optical Availability in Hybrid RF/FSO Links Using
RF Beacons and Deep Learning*. PDF và hash được ghi trong `design_receipt.json`.

Ý tưởng lấy từ bài: hai thang Gaussian độc lập, coarse được nội suy, advection,
innovation hình dạng và threshold. Các phần **do chúng ta đề xuất**: chuẩn hóa
covariance, AR(1) dừng, nội suy/dịch Fourier, miền đệm, intensity tương đối và
ensemble validation. Không gọi công thức mới là nguyên bản Algorithm 1.

```text
Gf = (Wf-mean(Wf))/sqrt(1-1/N)
Gc = FourierInterp((Wc-mean(Wc))/sqrt(1-1/Nc))
X0 = (wf*Gf+wc*Gc)/sqrt(wf^2+wc^2)
X[k+1] = rho*A_v[X[k]] + sqrt(1-rho^2)*Z[k+1]
rho = exp(-dt/tau_c)
A_v[X](r) = X(r-v*dt)
```

Z dùng đúng phép sinh Gaussian đa tỷ lệ của X0, độc lập giữa các slot.
Chuẩn hóa là phép tuyến tính cố định, đảm bảo ensemble marginal mean=0 và
variance=1. Không chia cho sample standard deviation, không chuẩn hóa lại từng
slot và không ép mean/variance của mỗi crop về 0/1. Crop ban đầu seed chính có
mean **0.1372783**, variance **1.0451940**; đây là dao động hữu hạn được báo cáo,
không bị che bằng một phép renormalization phi Gaussian.

Với covariance C bất biến theo dịch và A Fourier unitary, `A C A*=C`, do đó
`Cov(X_next)=rho^2*C+(1-rho^2)*C=C`. X0 và Z đều Gaussian với cùng C nên luật
Markov Gaussian là dừng. Ở hệ bù chuyển động, correlation lý thuyết là
`rho^lag`; tại tọa độ cố định còn có thừa số spatial correlation.
README có công thức covariance, PSD, suy ra variance crop và chứng minh chi tiết.

Baseline cũ dùng `(1-p)*A_linear X+P*(fine+coarse_interp)`, với p=.002, P=.05.
Không có quan hệ được công bố giữa p/P và cặp rho/innovation mới. Chỉ trong
trường hợp covariance bảo toàn, innovation đã có C, mới có thể đồng nhất
`1-p=rho`, `P=sqrt(1-rho^2)`. Bilinear interpolation của baseline còn làm đổi
covariance; không áp một công thức scalar variance dừng thiếu điều kiện cho nó.

## Tham số thực chạy

Tất cả số trong bảng là **illustrative assumptions/kịch bản người dùng**,
không gán thành thông số công bố của Ibrahim.

| Tham số | Giá trị |
|---|---|
| Cửa sổ quan sát | 2000 x 2000 m; 50 x 50 ô; dx=dy=40 m |
| Thời gian | dt=1 s; K=1000; t cuối=999 s; padding đến 1000 s |
| Gió | vx=-5 m/s, vy=0; -0.125 pixel/slot |
| tau_c / rho / innovation scale | 300 s / 0.9966722160545233 / 0.08151376414425716 |
| Seed | Chính 20261111; ensemble 20261111..20261121 |
| Coarse factor / trọng số | u=5; wf=0.35, wc=1.0 |
| Miền tổng hợp | Nx=225, Ny=105; 9000 x 4200 m |
| Coarse grid tổng hợp | 45 x 21; Fourier interpolation |
| Guard | Tối thiểu 1000 m; crop bắt đầu tại [row,col]=[25,25] |
| Intensity | softplus(X), scale=1, offset=0; không có đơn vị vật lý |
| Gamma seed chính | 0.6946257315928469, quantile 0.70 của crop X0 |
| Gamma các seed | Hiệu chuẩn riêng một lần tại t=0 rồi giữ cố định |
| Snapshots | k=0,100,200,400,600,800,999 |
| Statistical check | Sai số <=4 SE+1e-10 ở các moment/lag định trước |
| Spectral error / tagged-packet limit | 1e-10 / 1e-10, đặt trước run |

Fine/coarse đều được sinh độc lập và được giữ dưới dạng thành phần ban đầu
trong NPZ. Covariance target và covariance thực nghiệm đầu/cuối 11 seed nằm
trong `ensemble_validation.npz`. Do trừ trung bình crop, kỳ vọng population
variance của crop là **0.9923320616403023**, trong khi marginal second moment
vẫn có target 1. Validation kiểm tra cả hai đại lượng riêng biệt.

## Chuyển động, khuếch tán số và không tái nhập

- Một slot: **-5 m**, tức **-0.125 pixel**; 8 slot: **-40 m**, đúng chiều trái.
- Sai số giữa 8 dịch liên tiếp và một dịch 8-slot: **1.7764e-15**.
- Sau 1000 lần dịch Fourier, thay đổi tương đối variance **9.9920e-15**;
  sai số covariance lớn nhất chia variance **2.6239e-14**.
- Phép thử cùng field, cùng domain, chỉ dịch và tắt AR/noise: nội suy bilinear
  mất **85.5872% variance** sau 1000 bước. Đây là so sánh toán tử số, không
  phải chạy lại baseline và không quy toàn bộ drift baseline cho diffusion.

Backtrace của cửa sổ x=[1000,3000] m:

| Thời điểm | Miền nguồn |
|---:|---|
| 0 s | [1000,3000] m |
| 400 s | [3000,5000] m |
| 999 s | [5995,7995] m |
| 1000 s, guard horizon | [6000,8000] m |

Tất cả nằm trong [0,9000] m, còn ít nhất 1000 m guard trong toàn horizon.
Innovation sinh muộn hơn có tuổi nhỏ hơn, nên cũng thỏa giới hạn đó. Không có
đường đặc trưng nào phải modulo để lấy dữ liệu vào crop.

Gói Gaussian trơn đặt ở seam x tổng hợp, tâm y trong cửa sổ quan sát, có biên độ
tối đa trong crop tại 0/400/999 s lần lượt **8.37e-16 / 2.85e-15 / 1.27e-14**,
nhỏ hơn ngưỡng 1e-10. Positive control đưa gói vào crop cho biên độ **1.0**;
unit test còn phát hiện gói tái nhập nếu xét đến 1500 s, ngoài horizon bảo vệ.
Đây là kiểm chứng **không tái nhập hình học vào cửa sổ quan sát**. Fourier có
support toàn cục và C vẫn là covariance trên torus hữu hạn; không suy rộng
thành độc lập nhân quả support hữu hạn hoặc một mô hình khí tượng miền vô hạn.

## Tương quan theo thời gian và cấu trúc mây

Các ước lượng sau đã bù chuyển động trên một cửa sổ vật chất nằm hoàn toàn
trong miền đệm. Mỗi seed dùng `sum(Y0*Ylag)/sum(Y0^2)`, rồi tính mean/SE qua
11 seed. Không phải Pearson trên chuỗi slot được giả định độc lập.

| Lag (s) | rho^lag | Empirical mean | CI95 nửa khoảng |
|---:|---:|---:|---:|
| 1 | 0.996672 | 0.999293 | 0.002853 |
| 8 | 0.973686 | 0.980872 | 0.008403 |
| 40 | 0.875173 | 0.856171 | 0.019114 |
| 80 | 0.765928 | 0.738123 | 0.033105 |
| 100 | 0.716531 | 0.703254 | 0.043795 |
| 200 | 0.513417 | 0.509647 | 0.049804 |
| 400 | 0.263597 | 0.249981 | 0.096568 |
| 999 | 0.035793 | 0.040756 | 0.037600 |

Tất cả 11 lag, kể cả 0/20/800 s, nằm trong giới hạn 4-SE đã đặt trước. Các CI95
là xấp xỉ từng điểm, không phải một bảo đảm đồng thời trên toàn không-thời gian.
67 kiểm tra còn gồm spatial covariance ở hai trục, mean, variance, second/
third/fourth moments tại bảy thời điểm và chênh lệch đầu-cuối qua seed.

Presence mask được đo connected components **8-neighbour**, không nối tuần
hoàn qua crop, không lọc bỏ cụm nhỏ. Seed chính: 25 cụm ban đầu, diện tích
trung bình 48000 m^2, lớn nhất 459200 m^2; cuối 39 cụm, diện tích trung bình
19569.23 m^2, lớn nhất 121600 m^2. `connected_components_main.csv` chứa cả
1000 slot; ensemble NPZ/CSV chứa number/mean/max area và sai số qua seed.
Các cụm bị cắt ở mép crop, nên đây là thống kê trong vùng quan sát.

## Đối chiếu baseline đã lưu, không chạy lại

| Đại lượng | Baseline p=.002/P=.05 | Phiên bản mới, seed chính |
|---|---:|---:|
| Số khung / t cuối | 1001 / 1000 s | 1000 / 999 s |
| Gamma cố định | 0.6308975316793873 | 0.6946257315928469 |
| Độ phủ ban đầu | 30% | 30% |
| Trung bình mission | 10.8843% | 24.0720% |
| Độ phủ cuối | 7.60% | 19.08% |
| Variance ban đầu | 1.37981255 | 1.04519405 |
| Variance cuối | 0.17533645 | 0.87527675 |
| Biên quan sát | Torus 2 km; vòng hình học 400 s | Crop miền 9 km; không tái nhập trong horizon |
| Dịch subpixel | Bilinear, có diffusion | Fourier unitary, sai số probe ~1e-14 |

Tại cùng t=999 s, baseline lưu có coverage **8.40%**, variance
`0.42409665030782945^2`, tránh nhầm bảng 1000-s với horizon mới.
Baseline snapshot Pearson sau bù dịch nguyên pixel ở lag40/80 s lần lượt
**0.629986 / 0.497934**. Baseline chỉ lưu ba map và có một seed; estimator,
spatial covariance, trọng số và chuẩn hóa khác phiên bản mới. Không coi các
con số đó là một so sánh ensemble công bằng hoặc bằng chứng ưu thế khí tượng.
Trùng số seed không tạo một cặp cloud realization giống nhau khi kích thước
miền, phép sinh và số lượng random draws đã thay đổi.
Ngưỡng ban đầu, covariance và độ nhám cũng khác, không dùng coverage cao hơn
để khẳng định mô hình mới tốt hơn.

## Tệp mới, tệp sửa và kiểm thử

Tệp code/config/documentation mới:

- `../../src/ibrahim_stationary_cloud.py`
- `../../configs/ibrahim_stationary_cloud.json`
- `../../scripts/run_ibrahim_stationary_cloud.py`
- `../../scripts/plot_ibrahim_stationary_cloud.py`
- `../../tests/test_ibrahim_stationary_cloud.py`
- `../../docs/IBRAHIM_STATIONARY_CLOUD_README.md`

Trong thư mục này: `cloud_fields.npz` gồm X/intensity/diagnostic mask
`[1000,50,50]`, coordinates/times/metadata và thành phần ban đầu;
`ensemble_validation.npz`, ba CSV thống kê, metadata/provenance/boundary/
numerical/validation JSON, `unit_tests.log`, `verify.py`, README, báo cáo này;
6 bộ Figure A-F PNG400dpi/PDF; GIF đủ 1000 slot. PDF E/F là đường/text vector;
map PDF nhúng grid raster cùng trục/text vector. Các khung hình cùng hệ tọa độ
và cùng thang màu theo thời gian; GIF phát nhanh 50 ms/slot, không thay dt dữ liệu.

Đã chạy: **11 unit tests PASS**, **67 ensemble checks PASS**, read-only baseline
verifier PASS, exported-artifact verifier và `git diff --check`. Kết quả exporter
và hash cuối được ghi trong `artifact_verification.json`. Chưa chạy: full
repository suite, fit khí tượng/CLWC, optical/channel/QKD/SKR/finite-size/UAV,
training/final-test/held-out/publication evaluation.

236 tệp production/config/frozen/baseline được bảo vệ bằng hash không đổi.
Kiểm tra cuối sửa chiều y của GIF cho đồng nhất với trục y hướng lên; đặt đúng
tâm y của tagged-packet probe và thêm positive control để tránh một probe vốn
nằm ngoài dải y. Đã chạy lại probe và 11 tests; không đổi Gaussian generator,
mảng X/intensity/mask, ensemble, tham số hay tiêu chí 67 checks. Source trước/sau
và kết quả probe ban đầu được giữ trong `producer_snapshots/`,
`numerical_validation_initial.json`, `finalization_receipt.json`; receipt đặt
trước ensemble không bị sửa. Hình được render lại chỉ từ dữ liệu đã lưu.
Chỉ cập nhật các sổ EVIDENCE/DECISION/PROJECT_STATE/NEXT_ACTIONS và session handoff
để ghi nhận cloud-only diagnostic mới; không sửa paper manuscript hoặc baseline.
Branch đầu phiên `feat/cloud-11-11`, HEAD
`0c039f394511ce43c0038e76694c4f15e446b1eb`, worktree ban đầu sạch.

Scientific source **mới** chỉ là cloud generator độc lập. Existing scientific
source, security functional, frozen model, baseline selection và QKD threshold
approval không đổi. Frozen SHA-256 vẫn `df83ea63...b78c15`, khác historical
`561fecc9...a2a7b1`; blocker cũ giữ nguyên. Không đổi publication/security settings:
`UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, E2
`INCONCLUSIVE` và Objective C `USER_STOPPED` được giữ nguyên.
