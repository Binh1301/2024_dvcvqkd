# Kế hoạch gỡ chặn chín hình khoa học

## 1. Kết luận từ trạng thái và manifest hiện tại

Đã đọc [status.json](../figures/paper/status.json) và **cả 10 manifest riêng**,
đối chiếu từng bản với mục tương ứng trong index. Kết quả: 1 hình `READY`
(`fig01_rotor_power`, chỉ là minh họa mô hình rotor), 9 hình `BLOCKED`, không có
hình `EXPLORATORY` trong thư mục paper. Cả 9 hình bị chặn đều có `outputs: {}`.
Các file đầu vào mà manifest liệt kê hiện tồn tại và khớp SHA256 đã ghi.

`paper_mode` vẫn là `NOT_RUN`; lookup 2.601 điểm vẫn là `INSUFFICIENT_EVIDENCE`.
Không có `results/paper_verified/results.json` hay
`results/paper_verified/sensitivities.csv` trong workspace đã kiểm tra.

**Phân biệt hai loại phụ thuộc:**

- **Phụ thuộc khoa học trực tiếp:** các đại lượng thật sự cần để dựng nội dung
  của từng hình. Ví dụ bản đồ CLWC không cần epsilon, và bản đồ SKR tiệm cận
  không cần ngân sách propulsion.
- **Cổng của bộ nạp hiện tại:** `_readiness_reasons`, `load_figure_inputs`,
  `_validate_seals` và `validate_report` trong
  [paper_figures.py](../src/uav_qkd/paper_figures.py) yêu cầu chung một gói
  thí nghiệm đã kiểm chứng cho các hình 02–10. Gói này phải khớp cấu hình,
  qua kiểm tra nguồn/readiness, hash, metric và dữ liệu đo. Vì vậy lý do trong
  chín manifest giống nhau; không nên diễn giải thành chín tập thiếu vật lý
  độc lập, hoặc cho rằng mọi trường null đều trực tiếp cần cho mọi hình.

Với bộ nạp hiện tại, chuẩn bị riêng một ma trận mây hay một bảng SKR chưa đủ
để đánh dấu hình tương ứng `READY`. Muốn thay đổi phạm vi cổng theo từng hình
cần một quyết định/đầu việc riêng; báo cáo này **không sửa bộ nạp, trạng thái
hoặc hàm vẽ**, và không đề xuất sửa nhãn JSON để vượt kiểm chứng.

## 2. Quy ước phân loại và danh mục file

| Mã | Phân loại | Cách hiểu |
|---|---|---|
| V | Đã xác minh nguồn trong audit hiện có | Có nguồn và phạm vi rõ; không đồng nghĩa mọi mô hình vật lý/bảo mật đã được chứng nhận |
| D | Dẫn xuất hoặc kết quả tính/đo phần mềm | Phải giữ công thức, input và provenance; kết quả số có thể vẫn thiếu bằng chứng nguồn |
| A | Giả định/thiết lập minh họa được ghi rõ | Có thể tồn tại trong demo nhưng chưa được chọn cho paper |
| U | Chưa có đầu vào paper khả dụng | Null hoặc chưa có bằng chứng/quyết định phù hợp trong các file đã kiểm; không khẳng định không tồn tại ở mọi nơi khác |

Các giá trị `D-demo` là kết quả thật của phần mềm trên input tổng hợp, **không
phải số bịa**, nhưng không thể đổi nhãn thành dữ liệu paper. Một tham số thiết
kế đang `U` có thể được tác giả lựa chọn và ghi thành `A` trong nghiên cứu mô
phỏng sau này; báo cáo này không thực hiện lựa chọn đó và không gọi nó là `V`.

Các đường dẫn trong phần nội dung dưới đây tương đối với thư mục project,
trừ nhóm `S`/`C` đã ghi rõ đường dẫn sibling.

| Mã file | File hiện có / ý nghĩa |
|---|---|
| P | [configs/paper.yaml](../configs/paper.yaml): cấu hình paper chưa đầy đủ |
| A1 | [parameter_provenance.md](parameter_provenance.md): nguồn, đơn vị, phép dẫn xuất và giả định |
| A2 | [paper_configuration_audit_vi.md](paper_configuration_audit_vi.md): kiểm toán và khác biệt phiên bản nguồn |
| A3 | [configuration_validation.json](../results/paper_configuration_audit_20261107/configuration_validation.json): rotor và từ chối cấu hình thiếu input |
| A4 | [skr_lookup_audit.json](../results/paper_configuration_audit_20261107/skr_lookup_audit.json): schema, hash, lớp bằng chứng của lookup |
| A5 | [audit_summary.json](../results/paper_configuration_audit_20261107/audit_summary.json): `NOT_RUN` và các đầu vào còn thiếu |
| S1 | [skr_map.csv](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/skr_map.csv) và [skr_map.npz](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/skr_map.npz): dữ liệu SKR diagnostic |
| S2 | [execution_physical_protocol.json](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json): geometry, receiver/noise và quy ước producer |
| S3 | [run.py](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/run.py) và [report_vi.md](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/report_vi.md): producer và giải thích lookup, chỉ tham khảo/đọc trong việc này |
| C1 | [create_figure.py](../../dynamic_gaussian_cloud_figure/create_figure.py): bộ sinh mây Gaussian minh họa |
| C2 | [cloud_field_data.npz](../../dynamic_gaussian_cloud_figure/cloud_field_data.npz): ma trận mây và đủ 400 bộ amplitude/center/sigma đã lưu |
| D0 | [configs/demo.yaml](../configs/demo.yaml): các giả định tổng hợp, bộ rotor khác paper |
| D1 | [results/final_demo_20261107/results.json](../results/final_demo_20261107/results.json): bốn phương pháp, P1/P2, series, runtime/memory của demo |
| D2 | [results/final_demo_20261107/scenario.npz](../results/final_demo_20261107/scenario.npz): waypoint, edge cost, rate, availability của demo |
| D3 | [results/final_demo_20261107/sensitivities.csv](../results/final_demo_20261107/sensitivities.csv): các sweep tổng hợp |
| D4 | [results/approximate_smoke_20261107/results.json](../results/approximate_smoke_20261107/results.json) và [approximation_gaps.csv](../results/final_demo_20261107/approximation_gaps.csv): bằng chứng phần mềm approximate/exact trên trường hợp nhỏ |
| L | [data/README.md](../data/README.md), [config.py](../src/uav_qkd/config.py), [verify.py](../src/uav_qkd/verify.py): hợp đồng input và kiểm chứng |

## 3. Bảy nhóm blocker

### Nhóm 1 — CV-QKD/SKR lookup

| Đầu vào/quyết định | Hiện trạng và phân loại | File có thể cung cấp | Hành động tối thiểu |
|---|---|---|---|
| Rate và tọa độ gốc | D: S1 có đủ 2.601 node, 51×51, x/y 0–2.000 m, bits/use; không phải dữ liệu bị mất | S1, A4 | Giữ nguyên raw signed rate, đơn vị và tọa độ; xác minh producer/input bindings trước khi dùng |
| Mức chấp nhận nguồn | U cho paper: cả 2.601 điểm MB còn `INSUFFICIENT_EVIDENCE`; `paper_admissible=false`, strict Phase B false, security unvalidated | A4, S2, S3; các bằng chứng nguồn được repo quang liên kết | Giải quyết các khoảng trống C,w/numerical/security được ghi trong audit và review phạm vi được phép; không chỉ đổi chuỗi trạng thái |
| Phạm vi tối ưu | D: tốt nhất trong catalog nu/VA hữu hạn, không phải chứng nhận tối ưu liên tục | S2, S3 | Chốt claim đúng finite-catalog nếu phù hợp; claim liên tục cần một công việc riêng được cho phép. Đổi caption không tự giải quyết source/security gaps |
| Measurement, noise, normalization | V ở mức cấu hình producer: receiver30/homodyne effective; nguồn in `Vmod=nbar/2` khác quy ước producer `VA=Vmod=2*nbar` | S2, A1, A2 | Xác nhận dùng đúng mô hình/quy ước và lưu sự khác biệt; không trộn bảng/receiver khác. Không suy detector efficiency từ beta hoặc electronic noise từ xi_det |
| Input generic loader | U: `lookup.file`, `sha256`, `provenance` đều null; S1 không đúng trực tiếp schema loader | P, S1, L | Sau khi dữ liệu được chấp nhận, tạo bản chuyển đổi lossless riêng: CSV `x_m,y_m,skr_bits_per_use` hoặc NPZ `points,rates`, bind hash và ghi cách xử lý raw/potential. Không sửa S1 |

S1 giữ `K_raw_bits_per_use` và `K_potential_bits_per_use` tách biệt. Không tự
clip, đổi scale hoặc suy rate từ màu hình. Nội suy ở vị trí UAV phải theo
loader hiện có, không ngoại suy ra ngoài miền dữ liệu. Geometry của nhiệm vụ
phải khớp producer; nếu đổi physical model/geometry thì cần dữ liệu phù hợp,
không âm thầm dùng lại lookup cũ. Nhóm này ảnh hưởng trực tiếp fig03–05,
fig07–08, fig10, và gián tiếp các quỹ đạo/benchmark. Cổng chung hiện khiến nó
ảnh hưởng cả chín hình.

### Nhóm 2 — Tham số finite-size

| Đầu vào | Phân loại hiện tại | File có thể chứa / giới hạn | Hành động tối thiểu |
|---|---|---|---|
| `dt=1 s` | V | P, A1, current manuscript được A2 nhận diện | Giữ đúng đơn vị |
| `fs`, `eta_valid` | U cho paper | P.`verified_context`, A1/A2; D0 chỉ chứa `m0` giả định | Cung cấp nguồn/định nghĩa tín hiệu hợp lệ hoặc quyết định thiết kế ghi rõ giả định; không mặc định eta_valid=1 |
| `m0` | U; có thể D sau khi có hai trường trên | P; D0 có 10^6 chỉ cho demo | Tính `fs*dt*eta_valid` khi đủ căn cứ, hoặc nhận trực tiếp số tín hiệu hợp lệ/slot có provenance |
| `epsilon` | U; `1e-6` trong D0 là A | P, A1/A2, D0 | Tác giả xác định giá trị và ý nghĩa; không lấy xi_ch=.0186 SNU làm epsilon |
| `n,S,penalty,key` | U-paper, D-demo đã có | D1; `finite_size.py`, `evaluation.py` | Tính/lưu từ cùng block tích lũy của quỹ đạo paper; penalty áp dụng một lần trên prefix, không cộng penalty từng slot |

Thiếu epsilon và m0 chặn việc chọn tối ưu P1/P2, không chỉ chặn vẽ fig07.
Không bắt buộc P1 và P2 có cùng K. Công thức đang là performance approximation
khi gộp các trạng thái kênh; xác định epsilon không tạo ra chứng minh composable.

### Nhóm 3 — Hình học HAP/UAV

| Đầu vào | Phân loại | Nguồn/file hiện có | Hành động tối thiểu |
|---|---|---|---|
| Altitude HAP20 km, UAV1 km; vùng2×2 km | V theo A1/A2 | P và S2 | Giữ đúng nguồn/quy ước |
| `hap_m=(x_H,y_H,z_H)` | U cho tuple nhiệm vụ; chỉ altitude đã biết | P null; S2/S3 có thể chỉ ra geometry đã dùng cho lookup; D0 có horizontal(1000,1000) là thiết lập demo | Xác định tọa độ ngang và khớp hệ quy chiếu với lookup/cloud. Không suy từ đỉnh heatmap hay tự chuyển giá trị demo vào paper |
| `initial_m=q0` | U; D0 có (1000,1000) là A | P, D0; chưa thấy giá trị paper được chọn | Tác giả chọn/ghi nguồn và đưa q0 vào graph |
| Vị trí UAV thực, waypoint index và hệ tọa độ | U-paper; D-demo | D1/D2 | Lưu tọa độ và mapping index rõ ràng, mét, nằm trong vùng; UAV không bị ép vào cell center mây |
| Điểm cuối | Không phải input bắt buộc còn thiếu: hiện mặc định không ràng buộc | `evaluation.py`, `config.py`; P không đặt `terminal_m` | Chỉ đặt terminal khi có yêu cầu khoa học; không thêm điều kiện quay về như một giả định ngầm |

Geometry ngang là đầu vào cho lookup và giao LOS, nhưng không được giải quyết
chỉ bằng altitude. Không dùng altitude100 m hay endpoint RF từ bài rotor cho
nhiệm vụ QKD. Giao optical path phải kiểm ở tầng mây đã khai báo, không ở riêng
ô chứa UAV.

### Nhóm 4 — Mô hình mây động

| Đầu vào | Phân loại | File hiện có | Hành động tối thiểu |
|---|---|---|---|
| Velocity(-5,0) m/s, cloud grid50×50, cell40 m, các thời điểm0/300/1000 s | V/D theo manuscript và 2000/50 | P.`verified_context`, A1/A2 | Giữ chuyển động liên tục 5 m/s, không dịch một cell40 m mỗi giây |
| Gaussian realization: amplitudes, centers, sigma, covariance tùy chọn | U cho realization paper đã chọn; A+D cho bộ minh họa đã tính | C1/C2 có400 components, seed42; D0 có3 components khác | Chọn realization có provenance, xác định rõ đây là mô hình/kịch bản giả định nếu không phải dữ liệu đo; lưu nguyên coefficients, seed, đơn vị và origin |
| Clip/range và `L_th` | U-paper; clip15 và threshold8 mg/m³ trong C1/C2 là A | C1/C2, D0, A1 | Tác giả xác định quy tắc cho paper và claim opacity lý tưởng hóa; không gọi 8 là ngưỡng phổ quát đã đo |
| Altitude/thickness và `mode` blockage | U-paper; layer5–7 km trong D0 là A | P.`blockage=null`, D0; `blockage.py` | Cung cấp slab bottom/top hoặc mô hình lớp mỏng được nêu rõ, nằm nhất quán với HAP/UAV; projected-path2D chỉ dùng khi công khai là approximation |
| LOS sampling spacing | U-paper; 2 m của demo là A | D0, `blockage.py`, test refinement trong suite | Chọn resolution có kiểm tra độ nhạy trên realization dùng thật; agreement hai bước không chứng nhận không bỏ sót mọi vùng hẹp |

C2 chứa `field(50,400)`, `masks(5,50,400)`, `local_fields(3,50,50)`,
`component_x/y`, `sigma_x/y`, `amplitude`, `times`, `starts`, `cell_m` và `seed`.
Nó có thể cung cấp đủ hệ số để tái lập mây minh họa, không chứng minh một tầng
mây khí tượng hay dữ liệu paper. Phải phân biệt background16×2 km với operating
area2×2 km và khai báo phép liên hệ world/local coordinates; không tạo riêng
mây mới trong từng cửa sổ. Bản đồ coverage và ma trận link availability z[k,j]
là hai sản phẩm khác nhau: z cần geometry và giao LOS.

Theo schema thực thi hiện tại, mỗi cluster cần `amplitude`, `center`, `sigma`;
`covariance` và velocity riêng là tùy chọn. Slab LOS cần
`blockage.mode`, `sample_spacing_m`, `layer_bottom_m`, `layer_top_m` khi dùng
mode `layer`. `cloud.provenance` cũng phải có trong paper-mode. Không thể chỉ
điền tên một độ cao mà bỏ qua các trường mà loader thực sự cần.

### Nhóm 5 — Năng lượng và cấu hình nhiệm vụ

| Đầu vào | Phân loại | File hiện có | Hành động tối thiểu |
|---|---|---|---|
| Bộ rotor preprint2018, vmax60 m/s | V/D; đã đủ cho fig01 | P, A1, A3 | Giữ cùng phiên bản: P0=580.65 W, Pi=790.6715228132718 W, v0 bảng7.2 m/s |
| `energy_budget_j=Emax` | U-paper; 1500 J trong D0 là A với rotor khác | P, D0 | Xác định usable propulsion allocation; nếu dùng `P_hover*T_ref`, T_ref phải là giả định được lựa chọn rõ, không coi là giá trị literature |
| `graph`: points/lattice, spacing, restricted bounds nếu có | U-paper; graph9 waypoint của demo là A | P; D0, D2; `waypoint_graph.py` | Chọn graph độc lập grid mây, bao gồm q0, có successor di chuyển trong vmax*dt; ghi phạm vi exact-on-graph |
| `max_horizon`/prediction horizon | U-paper; 12 của demo là A | P, D0 | Xác định prediction cap. Sau khi biết Emax/graph, dẫn xuất energy bound bằng minimum feasible edge cost, bao gồm hover; không cố định K bằng cap |
| `greedy.lambda_bits_per_j`, `lambda_provenance` | U-paper; demo có sweep/calibration riêng là A+D-demo | P; D0, D1, `lambda_calibration.csv` trong D1 directory | Chọn prior/tuning rule và provenance độc lập realization đánh giá; không tối ưu lambda trên dữ liệu test rồi gọi là online |
| Sweep grids của `sensitivities` | U-paper; chưa có block trong P | D0, D3 | Tác giả chọn phạm vi/độ phân giải energy, threshold, spacing, caps; không sao chép các số demo mặc nhiên |

Các nhánh graph cụ thể cần `graph.kind`: `points` dùng `points_m`, `lattice`
dùng `spacing_m`, còn `restricted_lattice` dùng thêm `bounds_m`. Đây là các
input đang thiếu, không phải giá trị phải được suy từ cloud grid.

P không thiếu một công thức rotor mới. Không cần viết lại mô hình power,
minimum energy hoặc DP; chưa thể dẫn xuất horizon/quỹ đạo khi Emax và graph
chưa được quyết định. Không giả hovering power là minimum power, hoặc cộng
communication energy ngoài mô hình.

### Nhóm 6 — Gói kết quả paper-mode

**B0** dưới đây là dependency dùng chung trong bộ nạp hiện tại cho fig02–10:

1. Cấu hình paper hoàn chỉnh, cùng values với cấu hình được lưu trong kết quả:
   các null `initial_m`, `hap_m`, `energy_budget_j`, `m0`, `epsilon`, `graph`,
   `cloud`, `blockage`, `max_horizon`; các trường lookup và prior lambda cũng
   phải có dữ liệu/provenance theo parser. `research_use_authorized=false`
   hiện không được tự đảo thành true.
2. Các vấn đề nguồn/readiness ở nhóm1 được xử lý bằng bằng chứng đúng phạm vi;
   A5 không còn là một ghi nhận `NOT_RUN` đang áp cho việc dùng kết quả, A4 phải
   có quyết định chấp nhận phù hợp. Chỉ chỉnh hai cờ JSON không giải quyết được
   vấn đề khoa học. Phải tôn trọng cả lifecycle của dự án quang.
3. Một thư mục thí nghiệm thật có `results.json`, `scenario.npz`, `skr_input.csv`,
   `input_manifest.json`, `output_manifest.json`. Các file bắt buộc phải được
   seal đầy đủ; producer/config bindings và replay phải khớp. `sensitivities.csv`
   phải được seal nếu có. CSV generic không được thay bằng raw S1 sai schema.
4. `results.json` có đúng bốn method, cả P1/P2 hoặc trạng thái INFEASIBLE rõ;
   quỹ đạo, prefix, cumulative series, classifications và các measurement cần
   cho `validate_report`. Không nhập số0 để thay dữ liệu thiếu.
5. Chỉ sau đó truyền đúng `--results` và cấu hình tương ứng cho exporter trong
   một thư mục output mới; không ghi đè thư mục paper cũ.

B0 chưa tồn tại cho paper. D1/D2 có schema tương tự và kết quả đã tính, nhưng
được ghi `SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS`, không thể là B0. Các
thư mục `paper_missing_inputs*` là dấu vết từ chối cấu hình, không phải mission
thành công. Ngay cả numerical PASS cũng không tự chứng minh source/security
readiness.

### Nhóm 7 — Benchmark tính toán DP

| Đầu vào benchmark | Phân loại và nơi tìm | Hành động tối thiểu / giới hạn |
|---|---|---|
| `runtime_s` | D-demo có trong D1/D4; U-paper | Đo từ chính lần chạy paper được phép; không đổi thời gian demo hay suy từ số nhãn |
| `python_peak_bytes` | D-demo, U-paper | Giữ phép đo allocation và đơn vị bytes; không gọi là toàn bộ native/process memory |
| `sampled_peak_rss_bytes` | D-demo, U-paper | Giữ sampled process RSS riêng; phép đo hiện lấy mẫu10 ms, không phải peak liên tục chính xác |
| J, horizon, graph degree, cap, generated/dominated/discarded labels, exact/approximate | D-demo từ `graph`, `runs[*].diagnostics`, `classification` trong D1/D4 | Gắn workload và policy pruning của paper; không gọi cap/beam result là exact/global |
| Exact-vs-approximate gap | D-demo từ D4 và test vét cạn; U cho graph paper | Giữ kiểm chứng nhỏ hiện có; nếu cần gap cho workload nghiên cứu, chạy trường hợp exact khả thi có cùng input khi được phép. Không ép uncapped solve cho graph lớn |
| Môi trường và phạm vi đo | D: `input_manifest.json` của D1 ghi Python/dependencies; `memory_scope`/`information_scope` ghi trong D1; `experiments.py:measured` là producer | Ghi môi trường máy/threads và phạm vi timing của lần paper. So sánh measurement trên cùng workload và cùng cách đo |

Tối thiểu để dựng fig09 là bộ measurement thật, đầy đủ của bốn method trong
B0. Lặp phép đo, tóm tắt median/độ phân tán và kiểm soát tải máy là khuyến nghị
để đưa ra claim hiệu năng tính toán vững chắc, không phải số đã có hay một
điều kiện ngầm mới mà renderer hiện tự kiểm. Runtime một lần DP giải đồng thời
P1/P2 không được báo như hai phép đo độc lập. Timing hiện bao gồm instrumentation
và terminal evaluation, không gồm precomputation chung.

## 4. Phân tích riêng từng hình BLOCKED

### Fig02 — Gaussian CLWC và binary coverage

Manifest: [fig02_cloud_maps.json](../figures/paper/fig02_cloud_maps.json).

- **Thiếu trực tiếp:** realization được chọn cho paper; `cloud.clusters` hoặc
  `cloud.file`, amplitude/center/sigma và covariance tùy chọn, `velocity_m_s`, clip
  policy nếu dùng, `threshold_mg_m3`, provenance và world/local coordinate frame.
  Velocity, diện tích, grid và plot times đã có căn cứ V/D; realization và ngưỡng
  paper đang U. Layer/LOS không cần để vẽ riêng coverage nhưng cần cho B0/z.
- **File có thể chứa:** C1/C2 có dữ liệu A+D minh họa đầy đủ; D0 có bộ khác;
  A1/A2 xác nhận giới hạn. P vẫn `cloud=null`.
- **Hành động tối thiểu:** tác giả chọn/ghi rõ nguồn hoặc giả định cho bộ mây và
  ngưỡng; tái dùng hệ số đã lưu nếu đúng scenario được chấp thuận. Với renderer
  hiện tại, còn phải cung cấp B0 và các cổng chung, không chỉ một NPZ minh họa.
- **Phụ thuộc:** khoa học trực tiếp thuộc nhóm4; không phụ thuộc hình SKR hoặc
  finite-size về mặt toán. Phụ thuộc phần mềm hiện tại là B0, gồm cả geometry,
  link blockage, source readiness và bốn method.

### Fig03 — Bản đồ spatial SKR

Manifest: [fig03_skr_lookup.json](../figures/paper/fig03_skr_lookup.json).

- **Thiếu trực tiếp:** bảng được chấp nhận cho phạm vi paper; bindings của
  geometry/noise/measurement/normalization; lựa chọn raw/potential; schema input
  tương thích với `SKRLookup`; `lookup.file/sha256/provenance`. Không thiếu giá
  trị số S1, nhưng chúng là D với source evidence chưa đủ, không phải V cho claim.
- **File có thể chứa:** S1 cung cấp ma trận, S2/S3 cung cấp bối cảnh và producer;
  A4 ghi chính xác lý do inadmissible. Không dùng `skr_input.csv` tổng hợp của D1.
- **Hành động tối thiểu:** xử lý nhóm1, chốt finite-catalog claim phù hợp và làm
  adapter lossless/provenance khi được phép. Không cần tái chạy trajectory để
  tính riêng spatial SKR, nhưng loader hiện vẫn đòi B0 trước khi xuất READY.
- **Phụ thuộc:** nhóm1 và geometry producer thuộc nhóm3. Finite-size, cloud,
  Emax không phải đầu vào trực tiếp của bản đồ tiệm cận; chúng chỉ đang xuất
  hiện do dependency B0. Fig04/05/07/08/10 dùng rates cùng nguồn này.

### Fig04 — Quỹ đạo tối ưu/chọn theo P1

Manifest: [fig04_trajectory_P1.json](../figures/paper/fig04_trajectory_P1.json).

- **Thiếu trực tiếp:** `initial_m`, `hap_m`, candidate graph/edge energies,
  Emax, prediction horizon, m0/epsilon, rate array r[j], availability z[k,j],
  prior lambda; cuối cùng là `runs[*].solutions.P1.trajectory_m`, `path_indices`,
  K, mission time và classification cho bốn method. Các scalar nguồn đã có theo
  nhóm1–5 được giữ; các quyết định mission còn U; quỹ đạo hiện chỉ có D-demo.
- **File có thể chứa:** P/A1–A5, S1/S2, C1/C2 cho inputs; D0/D1/D2 cho ví dụ
  schema và thuật toán, không phải quỹ đạo paper có thể sao chép.
- **Hành động tối thiểu:** hoàn tất nhóm1–5 và authorization đúng phạm vi;
  chạy một base experiment công bằng để tạo B0, chọn prefix P1 bằng accumulated
  key/(K*dt), kiểm feasibility và backtracking. Không tự vẽ đường nối giả.
- **Phụ thuộc:** dữ liệu khoa học của fig03, field/LOS ở nhóm4 và mô hình rotor
  đã đủ; không cần đợi render fig01/02/03. Chia sẻ base run với fig05–09.

### Fig05 — Quỹ đạo tối ưu/chọn theo P2

Manifest: [fig05_trajectory_P2.json](../figures/paper/fig05_trajectory_P2.json).

- **Thiếu trực tiếp:** cùng bộ physical/mission input của fig04, nhưng phải có
  `runs[*].solutions.P2.trajectory_m/path_indices/K` được chọn bằng total
  accumulated key, cùng classification và feasibility. Không thay P2 bằng path
  P1; cả hai đang U-paper, D-demo trong D1.
- **File có thể chứa:** P, A1–A5, S1/S2, C1/C2, D1/D2. D1 có P1/P2 đúng schema
  nhưng thuộc cấu hình tổng hợp/rotor khác.
- **Hành động tối thiểu:** dùng cùng B0/base run đã nêu cho fig04 và backtrack
  terminal tốt nhất P2 riêng. Không cần thêm một mô hình vật lý hay ép K giống P1.
- **Phụ thuộc:** nhóm1–6; cùng inputs với fig04, không phụ thuộc hình fig04 đã
  xuất hay chưa. Series P2 cung cấp trực tiếp dữ liệu cho fig07.

### Fig06 — Cumulative propulsion energy

Manifest: [fig06_energy.json](../figures/paper/fig06_energy.json).

- **Thiếu trực tiếp:** path/prefix P1 và P2 đã chọn, graph costs c[i,j],
  `series[*].time_s/energy_j`, Emax và mission duration thực. Rotor/slot đã có
  V/D, nhưng năng lượng quỹ đạo cụ thể là U-paper và D-demo trong D1/D2.
- **File có thể chứa:** P/A3 cho rotor; `propulsion.py`, `waypoint_graph.py`,
  `evaluation.py` cho phép tính; D1/D2 cho cấu trúc series/costs hiện có.
- **Hành động tối thiểu:** sau B0, lưu/replay tổng edge energy của từng prefix,
  đối chiếu budget/speed; dùng đúng endpoint thời gian, không kéo dài hay padding
  curve. Không cần đổi rotor hoặc chạy thêm solver chỉ để tính lại energy đã lưu.
- **Phụ thuộc:** paths cùng dữ liệu với fig04 và fig05; code rotor/energy, không
  phải PDF fig01. SKR/finite-size ảnh hưởng việc chọn path, không tham gia trực
  tiếp vào công thức energy sau khi path đã biết. Loader vẫn yêu cầu B0.

### Fig07 — Tích lũy và ảnh hưởng finite-size

Manifest: [fig07_finite_size.json](../figures/paper/fig07_finite_size.json).

- **Thiếu trực tiếp:** m0, epsilon, dt, sequence z/r trên selected P2 prefixes;
  `series[*].valid_signals`, `asymptotic_bits`, `penalty_bits`, `key_bits`,
  time và terminal values nhất quán. M0/epsilon đang U, không được dùng hai số
  A từ D0 để giả làm paper. Các series D1 là D-demo.
- **File có thể chứa:** A1/A2 ghi công thức và khoảng trống nguồn; D1 cho
  saved series; `finite_size.py`/`evaluation.py` cho evaluator đã có.
- **Hành động tối thiểu:** xác định nhóm2, tạo B0; kiểm n=m0*u, S=m0*a,
  penalty=7*sqrt(n*log2(2/epsilon)), key=max(0,S-penalty), kể cả n=0.
  Không cần viết evaluator mới hay cộng penalty của từng slot.
- **Phụ thuộc:** nhóm1/2 và selected paths P2 ở fig05; availability từ nhóm3/4.
  Hình này và fig08 đọc chung output, không cần render theo thứ tự.

### Fig08 — So sánh key/rate cuối nhiệm vụ

Manifest: [fig08_key_comparison.json](../figures/paper/fig08_key_comparison.json).

- **Thiếu trực tiếp:** cho từng method, `solutions.P1.average_skr_bits_s` và
  `solutions.P2.key_bits`, K/duration tương ứng, classification, trạng thái
  feasible/infeasible và metadata fairness. Các đại lượng là U-paper; D1 có
  phép đo/tính D-demo, không phải baseline paper.
- **File có thể chứa:** D1, `summary.csv` cùng thư mục, `evaluation.py`; P/A1–A5
  cho căn cứ physical/finite-size. Đơn vị bits/s khác bits/use của lookup.
- **Hành động tối thiểu:** lấy scalar từ cùng B0 đã tạo fig04/05/07; đối chiếu
  L/(K*dt) cho P1, L cho P2 và chung điều kiện đánh giá. Không chạy mỗi method
  trên cloud realization khác nhau hoặc lựa lambda trên realization đánh giá.
- **Phụ thuộc:** nhóm1–6. Phải nêu DP có predicted future clouds, greedy chỉ
  current-slot actions và mọi method chọn prefix hồi cứu. Không cần fig09 được
  vẽ xong, dù measurement vẫn là trường bắt buộc của loader chung.

### Fig09 — Runtime và memory

Manifest: [fig09_runtime_memory.json](../figures/paper/fig09_runtime_memory.json).

- **Thiếu trực tiếp:** `runs[*].runtime_s`, `python_peak_bytes`,
  `sampled_peak_rss_bytes` và classification trên cùng workload paper; môi
  trường, graph/horizon/pruning và phạm vi đo cần được nhận diện. Số demo đã
  được đo thật (D-demo), nhưng measurement paper là U.
- **File có thể chứa:** D1/D4, `summary.csv`, `input_manifest.json` cùng thư
  mục; `experiments.py:measured`, `run_methods`; `dp_solver.py` cho diagnostics.
- **Hành động tối thiểu:** dùng wrapper đo hiện có trong một base run B0 được
  phép và lưu measurements nguyên bản; kiểm bốn method đủ trường. Không lấy
  wall time export hình hoặc thời gian pytest thay runtime thuật toán; không
  dùng memory allocation như peak RSS. Khuyến nghị repeated benchmark tách khỏi
  điều kiện tối thiểu đã trình bày ở nhóm7.
- **Phụ thuộc:** cùng base workload tạo fig04/05/08 và nhóm7; không phụ thuộc
  việc đã render các hình kia. Exact/approximate mode phải có nhãn đúng; không
  tự chạy uncapped exact trên graph lớn để lấy một điểm so sánh.

### Fig10 — Sensitivity

Manifest: [fig10_sensitivity.json](../figures/paper/fig10_sensitivity.json).

- **Thiếu trực tiếp:** block `sensitivities` với các grid
  `energy_budget_j`, `thresholds_mg_m3`, `waypoint_spacings_m`, `label_caps` được
  chọn cho paper; file `sensitivities.csv` có đủ bốn nhóm, method và objective,
  `parameter`, `objective_value`, key/signal/penalty fields, status và
  classification. Manifest hiện chọn objective P2. Tất cả grid paper là U;
  grid D0 là A, bảng D3 là D-demo.
- **File có thể chứa:** D0/D3, `experiments.py:sensitivity_runs`; D4 và gap CSV
  cho kiểm tra approximate nhỏ. Không có file sensitivity paper tại đường dẫn
  dự kiến.
- **Hành động tối thiểu:** sau base B0, tác giả chốt grid và chạy các biến thể
  có kiểm soát, giữ những input không khảo sát cùng lambda prior; lưu CSV được
  seal và đối chiếu cumulative objective. Ghi rõ khi spacing làm mất movement
  edges, hoặc label cap tạo approximation; không nội suy ra sweep chưa chạy.
- **Phụ thuộc:** base run và toàn bộ nhóm1–7. Không cần một simulation engine
  mới; chỉ cần output thực của các sweep đã có. Đây là hình cuối nên chạy sau
  khi single-run correctness/readiness đã ổn định, tránh nhân chi phí của một
  cấu hình sai lên nhiều lần.

## 5. Thứ tự ưu tiên có hiệu quả gỡ chặn cao nhất

| Ưu tiên | Hành động / sản phẩm cần đạt | Tác động |
|---|---|---|
| P0 | Chốt admissibility/scope của lookup và quy ước optical/geometry bằng bằng chứng nhóm1; giữ lifecycle/frozen/source restrictions | Blocker chung của cả9 qua loader và upstream của hầu hết objective; ngăn chạy nhiều experiment trên nguồn chưa phù hợp |
| P1, làm song song với P0 | Tác giả cung cấp một bản quyết định có provenance cho fs/eta_valid hoặc m0, epsilon, q0/qH, Emax, cloud scenario/layer/Lth/LOS spacing, graph, prediction horizon, prior lambda | Giải quyết nhóm2–5 một lần cho cả9, thay vì xử lý từng caption riêng; không cần viết thêm hàm vẽ |
| P2 | Sau khi đủ điều kiện, tạo một B0 đúng bốn method/cả P1/P2, đầy đủ measurement, seals và replay | Có thể cung cấp dữ liệu cho **8 hình02–09** cùng lúc; không phải tám lần mô phỏng độc lập |
| P3 | Chốt grid rồi chạy sensitivity có kiểm soát, giữ shared inputs, lưu bảng và classifications | Gỡ phần còn lại của fig10; tránh sweep sớm trước base-run validation |
| P4, khuyến nghị tăng độ vững của claim | Benchmark lặp có kiểm soát tải máy và so sánh exact/approx trên cỡ khả thi, báo gap/variance đúng phạm vi | Củng cố fig09/10, không được biến demo hoặc exact-on-small-graph thành bảo đảm cho graph/continuum lớn |

Không có hành động đơn lẻ như sao chép `demo.yaml`, sửa `NOT_RUN` thành PASS,
đặt eta_valid=1 hay truyền `--exploratory` có thể gỡ chặn paper một cách hợp lệ.
Các hình02/03 có ít input khoa học trực tiếp hơn B0; nếu mục tiêu thay đổi sang
chỉ công bố minh họa mô hình hoặc diagnostic có giới hạn thì cần review phạm vi
và cổng riêng ở một task sau. Hình đó phải giữ nhãn thích hợp, không tự thành
paper-ready hay thay thế thí nghiệm đang thiếu.

## 6. Kiểm thử và giới hạn của công việc này

Đã thực thi trong lượt lập báo cáo, từ thư mục `uav_cvqkd_optimization/`:

```powershell
python -X utf8 -m pytest -q
```

Kết quả thực tế: **59 passed in 5.60s**, exit code0;
`CURRENTLY_VERIFIED_PASS` cho suite phần mềm hiện có. Không thêm/xóa/sửa test.
Các fixture/ảnh tạm do test có sẵn sử dụng không phải thí nghiệm paper và không
ghi hình mới vào `figures/paper/`. Kết quả test không nâng `INSUFFICIENT_EVIDENCE`
hoặc chứng minh composable security, tính tối ưu liên tục hay performance paper.

Chỉ tạo báo cáo này. Không thêm hàm vẽ; không sửa `paper.yaml`, manifest, audit
gốc hay kết quả cũ; không chọn giá trị khoa học mới; không chạy paper experiment,
source job, optimizer/sweep nghiên cứu hoặc tạo placeholder plot; không commit/push.
Mọi hành động ở phần ưu tiên là **kế hoạch**, chưa phải authorization hoặc bằng
chứng chúng đã được thực thi. Chín hình vẫn `BLOCKED` sau khi lập báo cáo.
