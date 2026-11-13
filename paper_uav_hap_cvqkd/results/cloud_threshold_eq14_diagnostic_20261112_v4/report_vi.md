# Ngưỡng suy hao mây: chẩn đoán Eq.(14)

Ngày 2026-11-12. **DIAGNOSTIC_ONLY_UNCERTIFIED_CW**. Người dùng đã chọn nhánh Eq14,
chấp nhận C,w chưa được chứng nhận, HAP=(1000,1000,20000)m và UAV z=1000m,
miền 2km x2km, 50x50 tâm ô (20,60,...,1980)m. Không sửa kênh/QKD cũ.

## Bảng kết quả chính

Fixed là giữ nghiệm MB tốt nhất dưới clear sky **tại từng geometry**, không phải
đường Fixed-MB nu=.25 của hình lịch sử. Catalog 212 là chọn lại tham số trong
đúng tập nguồn lịch sử được dùng ở nhánh gần nhất; không là tối ưu liên tục VA,nu.

| Hình học | Zenith (độ) | L (km) | Kraw clear (bit/use) | Bracket crossing (dB) | Chế độ |
|---|---:|---:|---:|---|---|
| vertical | 0.000000 | 19.000000 | 0.0007960878081 | [0.098633, 0.099609] | Fixed |
| vertical | 0.000000 | 19.000000 | 0.0007960878081 | [0.098633, 0.099609] | Catalog 212 |
| grid_250 | 4.171974 | 19.050480 | 0.0007490244591 | [0.092773, 0.093750] | Fixed |
| grid_250 | 4.171974 | 19.050480 | 0.0007490244591 | [0.092773, 0.093750] | Catalog 212 |
| domain_corner | 4.256807 | 19.052559 | 0.0007470670338 | [0.092773, 0.093750] | Fixed |
| domain_corner | 4.256807 | 19.052559 | 0.0007470670338 | [0.092773, 0.093750] | Catalog 212 |
| extended_19.5km | 13.002824 | 19.500000 | 0.0002917079886 | [0.037109, 0.038086] | Fixed |
| extended_19.5km | 13.002824 | 19.500000 | 0.0002917079886 | [0.037109, 0.038086] | Catalog 212 |
| extended_20km | 18.194872 | 20.000000 | -0.0002887060551 | Không có positive margin | Fixed |
| extended_20km | 18.194872 | 20.000000 | -0.0002887060551 | Không có positive margin | Catalog 212 |
| extended_21km | 25.208765 | 21.000000 | -0.001626052433 | Không có positive margin | Fixed |
| extended_21km | 25.208765 | 21.000000 | -0.001626052433 | Không có positive margin | Catalog 212 |
| extended_22km | 30.272641 | 22.000000 | -0.003126012864 | Không có positive margin | Fixed |
| extended_22km | 30.272641 | 22.000000 | -0.003126012864 | Không có positive margin | Catalog 212 |

Ngưỡng báo cáo bằng midpoint của bracket rộng <=.001dB. Đây là độ phân giải
root của evaluator cố định; không là sai số vật lý hay chứng nhận nguồn C,w.
Các bậc và vùng màu đồng nhất trong hình2/3 phản ánh độ phân giải bracket,
không chứng minh các dải ngưỡng vật lý rời rạc. Không làm mịn bằng nội suy.
Kraw(0)<=0 được ghi không có margin dương; không gọi A=0 là nghiệm nếu Kraw(0)<0.
Góc0 đúng nghĩa thẳng đứng nằm giữa các tâm ô lưới chẵn, vì vậy được tính riêng.
Góc biên miền liên tục và góc ô xa nhất cũng được tính riêng, không nhầm hai giá trị.

## Mô hình và phép áp suy hao

Giữ nguyên Eq10 retained[0,1], AoA atom, turbulence, pointing, tau_zen.92,
D_r=.30m, lambda1550nm, full divergence35urad, jitter1.561urad, sigma_position.10m,
xi_ch=.0186, xi_det=.005, beta=.95, homodyne hiệu dụng1D, AO và phase OFF.
DM256 square16x16; VA=2*nbar, nu_repo=42.5*nu_raw. Catalog VA[.05,10],nu_raw[0,.4].
Không thay bằng GM-CV-QKD hoặc dùng công thức SKR giả định.

s=10^(-A/10); m1'=s*m1,mh'=sqrt(s)*mh,M0'=M0,P0'=P0.
t'=mh'^2; N'=(m1'-mh'^2)*VA+xi_ch*m1'+xi_det*M0.
Detector noise không bị nhân s. Giữ thiếu khối lượng của baseline, không
renormalize, không nhập lại phần đuôi clear đã loại bỏ. Không scale SKR cũ.
Tại mỗi A, tính lại MI discrete GH64/128, Eq13/14 và Holevo80/110 chữ số.
Kraw=beta*I_AB-chi_BE, giữ cả số âm. Mô hình pooled moment-matched này khác
với average K(T) của một mô hình oracle iid; không trộn hai nhánh.

## Tái sử dụng hàm cũ và giới hạn tối ưu

Import CLI cũ bị Windows Application Control chặn torch_python.dll (WinError4551).
Adapter mới thực thi nguyên các định nghĩa hàm số học đã lưu, với namespace NumPy/
SciPy/mpmath rõ ràng, không nạp DLL bị chặn, giả lập Torch, hoặc thay chính sách OS.
`adapter_validation.json` ghi hash module và tên hàm nguyên bản được dùng.
Mảng PMF/alpha được nạp từ archive đã có và khớp hash từng source; không tạo nguồn.
195 nguồn có mảng trong archive. Khôi phục thêm14bộ biên độ chỉ khi byte PMF và
biên độ khớp đúng digest nguồn cũ; không đổi tham số, không nội suy hoặc tính C,w.
Hiện có 209 bộ mảng khớp hash và 3
nguồn chưa có mảng. Các nguồn thiếu chỉ được loại khi upper bound không thể thắng.
Nếu không loại được nhưng upper bound vẫn âm, chỉ biết interval raw-SKR ở vùng
âm; không dùng lower endpoint như một maximum chính xác. Nếu bound còn có thể
dương, runner dừng, không đưa ra root đầy đủ. CSV ghi catalog_maximum_resolved
và catalog_K_upper để kiểm tra riêng từng điểm.

Upper bound cổ điển I_discrete<=0.5log2(1+t*VA/(1+N)) chỉ dùng screening;
giá trị SKR báo cáo luôn dùng MI discrete nguyên bản. Eq14/Holevo vectorized để
tính bound được so với110digits cho cả212nguồn tại9checkpoints.
Nghiệm chọn được so với exhaustive209nguồn tại9điểm,
cộng replay209nguồnA0 cũ.
Sai số replayA0 tối đa 0bit/use.
Chọn catalog có tolerance1e-10bit/use và đệm bound1e-11 từ kiểm tra số học;
không gọi đây là enclosure số học interval có chứng minh hay tối ưu toàn miền.

**Experiment B liên tục VA,nu chưa hoàn tất**: không có source coverage liên tục
và Torch constructor/optimizer bị chặn. Không nội suy C,w, không tự tạo AP nguồn,
không thay kết quả finite catalog thành global optimum. Hình/CSV nhãn catalog
để so sánh kết quả phần chọn lại nguồn có thể tái lập của implementation hiện có.

## Hình học và tính toán

Tính 251 nhóm bán kính chính xác đại diện2500tâmô;
do kênhđẳnghướng, các ô cùng r^2 có geometry giống nhau, không phải interpolation.
Tính thêm vertical, góc miền liên tục và L=19.5,20,21,22km tách riêng.
Tổng 257 geometry. 79nhóm
có raw sweep đủ201mứcA0..100dB/bước.5, bao gồm mọi hình học đại diện và các
checkpoint full đã hoàn tất được giữ nguyên. 178nhóm
còn lại tính raw0..0.5dB và bisection quanh root; sau đó kiểm tra upper bound của
toàn bộ212nguồn ở200nútA=.5..100dB. Chỉ khi mọi upper bound < -1e-10 mới bỏ
phép tính MI tại những nút đã chắc chắn không cho SKR dương; nếu không, quay về
raw sweep đầy đủ. Đây là kiểm tra dấu bằng bound, không phải201giá trị raw đã tính.
CSV/summary của từng nhóm ghi scan_scope và full_range_bound_checks riêng.
Không điền giá trị raw giả tại các nút chỉ có bound. Tất cả root bracket được
đánh giá bằng MI/Holevo nguyên bản. Hình1 dùng raw sweep đầy đủ của hình học đại diện.
Số selected evaluation rows chính: 37042,
thời gian lượt hoàn tất v4 90.140s (không gồm adapter validation,
render hoặc chi phí trước đó của 72full-sweep
checkpoints được tái sử dụng từ v3). Không diễn giải đây là chi phí chạy từ đầu.
Mỗi nhóm lưu toàn bộ evaluations và summary có moments nguồn, source identity.
Số rows không gồm các evaluation bị loại trong screening/validation, probe và
lần chạy lỗi trước đó. Hai lần chạy trước giữ riêng: lần1 không loại được nguồn
thiếu, lần2 lỗi serialize NumPy boolean ở export; không đổi vật lý hoặc tolerance.
Input/provenance và design receipt khóa lựa chọn người dùng và thông số trước run.

## Monotonicity và outage

Upward step raw lớn nhất trong tất cả các điểm đã đánh giá: 8.14779639e-06 bit/use;
số đường có positive re-entry quan sát được: 0.
`monotonicity_diagnostics.csv` ghi cả kiểm tra strict từ scanner và kiểm tra
allowance1e-10bit/use. Nếu raw tăng ở vùng âm, không được gọi raw là monotonic.
Một crossing không tự chứng minh không có crossing giữa các nút chưa đánh giá.
Quy tắc chính xác theo evaluator vẫn là b=1[Kraw<=0]. Bản đồ crossing này chỉ
là margin chẩn đoán theo geometry, không được tích hợp thành outage chính thức.
Ngưỡng thay theo vị trí; không chọn một số toàn cục tùy ý. Nếu cần conservative
margin cho miền, lấy minimum có điều kiện từ bản đồ và nêu giả định tương ứng,
không coi đó là hằng số khí tượng hoặc ngưỡng bảo mật phổ quát.

## Tệp và xác minh

critical_thresholds.csv; critical_threshold_map.csv (5000 mode-position rows);
threshold_maps.npz; geometry_jobs.json; mỗi geometry_evaluations.csv và_summary.json;
adapter_validation.json; execution_summary.json; design_receipt/protected_inputs;
unit_tests.log, verification.json, artifact_hashes.json và3PNG400dpi/PDF.
Lệnh từ project root (run mới từ đầu không cần checkpoint trước):

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/run_eq14_cloud_threshold.py --output results/cloud_threshold_eq14_new --workers 6
.\.venv\Scripts\python.exe -X utf8 -B scripts/report_eq14_cloud_threshold.py results/cloud_threshold_eq14_new
```

Runner cần namespace mới, giữ checkpoint theo geometry; không ghi kết quả cũ.
Không chạy full repo tests, sourceCw generation, finite-size, security/publication
evaluation, final-test/heldout, training hoặc ObjectiveC. Frozen model, các cache
và gói mây cũ giữ nguyên. Cw vẫn INSUFFICIENT_EVIDENCE, E2INCONCLUSIVE,
strictPhaseBfalse, UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Đây là bản đồ ngưỡng theo tọa độ UAV. Khi tích hợp tương lai phải lấy A_cloud
tại giao điểm qc của tia với lớp mây; không tự lấy A_cloud tại xy của UAV.

## Xác minh cuối cùng

11 unit tests PASS trong unit_tests.log. 12 endpoint checks độc lập qua adaptive
MI integration, matrix symplectic spectrum và conditional covariance PASS trong
selected_root_validation.json. Kiểm tra chỉ đọc cuối ở verification.json và
verify.py: 257 nhóm, 2500 vị trí, 37042 selected evaluation rows. Không có điểm
catalog-negative nào còn unresolved trong dữ liệu đã xuất. 1263 tệp cũ bảo vệ
giữ nguyên. Ba PDF/PNG400dpi đã render và kiểm tra trực quan; font nhúng,
Figure1/2 vector, Figure3 raster data với trục/chữ vector. git diff --check PASS
được kiểm tra riêng tại cuối phiên; toàn bộ repository tests NOT_RUN.

Read-only verification từ project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/cloud_threshold_eq14_diagnostic_20261112_v4/verify.py
```

Danh mục đầy đủ các tệp xuất và hash trong artifact_hashes.json. Report phần
xác minh này được bổ sung ở bước finalize.py, không chạy lại mô hình.
