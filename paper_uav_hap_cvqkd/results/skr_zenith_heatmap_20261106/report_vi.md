# SKR theo zenith và bản đồ 2D receiver30

Ngày 2026-11-06. Đã tính bằng pipeline receiver30 có sẵn. Trạng thái kiểm chứng
số: **CURRENTLY_VERIFIED_PASS**. Phạm vi: numerical asymptotic objective với finite source
catalog, không phải chứng nhận optimum liên tục hoặc composable security.

## Cấu hình

HAP/UAV=20/1 km, vertical span19 km; Dr=.30 m, lambda1550 nm,
divergence full-angle35 µrad, jitter1.561 µrad mỗi trục, sigma_h=.10 m mỗi
trục, tau_zen=.92, xi_ch=.0186, xi_det=.005, beta=.95, homodyne real1D,
reverse reconciliation, AO/phaseOFF. Không thêm detector efficiency .95.
Giữ original Eq10 retained [0,1] PDF/atom và approved truncation convention;
không normalize, clip, thay turbulence/pointing hoặc sửa Eq14/Eq13.
Đầy đủ tham số và snapshot mới trong execution_physical_protocol.json.

Catalog33Uniform/179MB, cùng nguồn trên mọi geometry, VA=[.05,10],
nu_raw=[0,.40], nu_repo=42.5nu_raw, VA=2*nbar. C,w dùng nguyên payload cùng
ensemble, không nội suy hoặc tính nguồn mới. Mỗi geometry đánh giá toàn bộ
212 nguồn và chọn raw signed K lớn nhất riêng cho Uniform và MB. Vì là
finite catalog nên mọi nhãn tối ưu chỉ có nghĩa best-tested catalog.

## Thực thi

32 góc: 0..30° bước1°, cộng endpoint
30.2726413189°, L=22km chính xác theo fixed vertical span.
Map dùng nguyên 2601 tọa độ trong geometry_only.csv, HAP projection(1000,1000)m.
294 bán kính bình phương khác nhau cho294 geometry; symmetric coordinates
dùng chung đúng kết quả tính của cùng geometry, không nội suy hay heuristic.
Tổng325context, 68900candidate evaluations,
cộng2fresh benchmark calls. Không C,w/source build, finite-size/cloud/energy/
trajectory/training/test/held-out/publication evaluation.

## Benchmark tính lại

| Zenith | I_AB | beta I_AB | chi_BE | K_raw bits/use |
|---:|---:|---:|---:|---:|
| 0 | 0.1882041908809768 | 0.1787939813369279 | 0.1779978935288418 | 0.0007960878080861267 |
| 30 | 0.1575429803454698 | 0.1496658313281963 | 0.1526975597713073 | -0.003031728443110948 |

VA=1.358333319784304, nu_raw=.30. Cả hai benchmark có absolute/relative
deviation bằng0 so binary64 records cũ; không điều chỉnh physical parameters.

## Bản đồ MB, bits/use

- Min: **0.0007470670338268481**.
- Max: **0.0007960878080861267**.
- Center(1000,1000)m: **0.0007960878080861267**.
- Numerical failures trên map: 0.

Heatmap thể hiện raw MB objective, axes km, aspect1:1, color range chứa0;
không tăng contrast giả để phóng đại spatial variation. Grey dùng cho lỗi/
missing nếu có. CSV/NPZ giữ cả Uniform raw objective và potential=max(0,raw)
sau ranking. Uniform curve âm vẫn được vẽ nguyên giá trị. Source evidence
class/ensemble identity được giữ tại từng điểm và mỗi candidate.

## Kiểm chứng

Mỗi evaluation dùng GH64/128 và Holevo/Eq14 80/110digits với tolerance gốc.
verify.py kiểm mọi catalog argmax, producer/source hashes, toàn bộ geometry,
CSV/NPZ, symmetry, endpoint và benchmark. Adaptive output-density MI độc lập
tại center, corner và sweep endpoint cho cả hai scheme:6checks.
4focused tests; 19dataset/provenance checks.
Chi tiết PASS/FAIL trong verification.json; mọi numerical error trong
evaluation_errors.json. Các figures PNG300dpi được kiểm tra trực quan.

## Binding và giới hạn

Lần chạy đầu gặp lỗi raw dependency hashes vì checkout dùng CRLF. Ba attempt
failure JSON được giữ nguyên. Binding mới cho phép chính xác LF/CRLF equivalence,
và bind current bytes của hai validation entry points không được import/thực
thi. Scientific producer content không đổi. Counts: {'VERIFIED_NEWLINE_EQUIVALENT': 312, 'IDENTICAL': 88, 'UNUSED_VALIDATION_ENTRY_CURRENT_BYTES_BOUND': 2}.
146source payload chỉ đổi newline,66payload byte-identical; input p/alpha
digests, C/w hex và source producer settings đều kiểm lại. Bản historical
frozen spec được tái dựng đúng SHA256 trong output mới, không sửa file gốc.
Không monkey-patch hàm toán hoặc bỏ domain/numerical checks. New task snapshot
đi qua existing protocol validator; original snapshot files giữ nguyên.

Original source evidence classifications và security limitations được giữ,
không tự nâng Phase B hay source convergence. PDF tail/truncation và frozen
history không được biến thành chứng nhận physical/security bằng việc hoàn
thành numerical map. Không có finite-key/composable guarantee, experimental
calibration hoặc continuous optimization certificate trong task này.

## Tái lập

Từ project root:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv-binary-cloud\Scripts\python.exe -X utf8 -B results/skr_zenith_heatmap_20261106/verify.py
```

run.py --execute bảo vệ completed outputs. Để chạy mới, sao chép source
run.py/test_run.py/verify.py/build_report.py sang namespace results mới trước
khi execute; không ghi đè benchmark/caches hoặc kết quả đã hoàn tất.

Deliverables: skr_vs_zenith.png/csv, skr_heatmap.png, skr_map.csv/npz.
Context/candidate tables, source pool, protocol/binding, benchmarks và
verification giữ full numerical trace. Không commit/push.
