# Kế hoạch thực thi hình tiếp theo — Phase 2

## 1. Kết quả kiểm toán và quy ước số hình

Đã đọc các file thực tế được yêu cầu, source các model/solver/exporter và hai
rotor profile; kiểm tra dữ liệu lookup, catalog manifests và output IEEE2019.
Không dùng Deep Research, không suy đoán input và không chạy paper-mode.

### Trạng thái đếm đúng phạm vi

| Phạm vi | READY được ghi nhận | BLOCKED | Kết luận |
|---|---:|---:|---|
| Catalog10 hình trong `figures/paper/status.json` | 1 | 9 | C01 chỉ là minh họa rotor arXiv; C02–C10 chưa có dữ liệu paper-ready |
| Hình rotor IEEE ở `figures/ieee_2019/` | 1 | 0 | R02-IEEE đã có PDF/PNG/CSV/caption/JSON và nguồn/profile khớp hash |
| Tổng artifact khác nhau, không gộp theo số02 | 2 | 9 | Hai hình mô hình rotor khác phiên bản, không phải hai mission results |
| Mission paper hợp lệ | 0 | — | `paper_mode: NOT_RUN` giữ nguyên |

Các manifest catalog cũ ghi hash `parameter_provenance.md` trước khi bổ sung
IEEE. Hash của tài liệu live hiện khác, nhưng snapshot byte-for-byte cũ tại
`docs/ieee_2019_rotor_verification/parameter_provenance_before.md` khớp hash
cũ. Đếm READY ở bảng trên là **trạng thái artifact đã ghi**, không phải một
tuyên bố toàn bộ input-path hiện tại vừa qua lại kiểm chứng live. Không thấy
sai số numerics của C01 được thiết lập từ khác biệt tài liệu này. Nếu cần làm
mới provenance, xuất một edition mới sau review; không viết đè manifest cũ.

### Ánh xạ chuẩn kỹ thuật, chưa tự quyết số manuscript

| ID chuẩn dùng trong kế hoạch | Số trong catalog/file hiện tại | Nội dung và file | Quyết định numbering |
|---|---|---|---|
| C01 | Catalog01 | `figures/paper/fig01_rotor_power.*`, bộ arXiv2018 | Giữ nguyên lịch sử; chưa quyết dùng cùng/so sánh với IEEE trong manuscript |
| R02-IEEE | Figure02 trong task rotor mới | `figures/ieee_2019/fig02_propulsion_power_ieee2019.*` | Không phải C02; nguồn IEEE2019 riêng |
| C02 | Catalog02 | `fig02_cloud_maps` | Bị trùng số02 với R02-IEEE; cần tác giả chốt số manuscript trước tích hợp |
| C03 | Catalog03 | `fig03_skr_lookup` | Giữ ID/file hiện có |
| C04 | Catalog04 | `fig04_trajectory_P1` | Giữ ID/file hiện có |
| C05 | Catalog05 | `fig05_trajectory_P2` | Giữ ID/file hiện có |
| C06 | Catalog06 | `fig06_energy` | Giữ ID/file hiện có |
| C07 | Catalog07 | `fig07_finite_size` | Giữ ID/file hiện có |
| C08 | Catalog08 | `fig08_key_comparison` | Giữ ID/file hiện có |
| C09 | Catalog09 | `fig09_runtime_memory` | Giữ ID/file hiện có |
| C10 | Catalog10 | `fig10_sensitivity` | Giữ ID/file hiện có |

`Cxx` là ID của catalog thực tế, không phải một sơ đồ numbering manuscript mới.
Không đủ căn cứ tự chọn số03 mới cho cloud rồi dịch toàn bộ hình/citation. Task
này chỉ lập ánh xạ, không rename hoặc ghi đè file.

### IEEE Figure02 đã được xác nhận thế nào?

Đã đọc manifest và kiểm hash PDF/PNG/CSV/caption, profile, PDF nguồn địa phương
và parameter-audit snapshot. Các file thực sự tồn tại, không chỉ có thông báo
trong chat. Profile là `ieee_2019`, v0 policy `derived`, miền0–30 m/s; P0/Pi/
hover lần lượt79.85628/88.62793774108202/168.48421774108203 W; ME10.2116911984,
MR18.2944803511 m/s. Các giá trị đã ghi được đối chiếu với receipt/nguồn hiện
có, không chạy standalone producer để tạo một edition mới trong Phase2.
Suite hiện hữu có tính số/optimizer tham chiếu và render vào thư mục tạm theo
test; chúng không phải một paper experiment hay kết quả nghiên cứu mới được xuất.

Bộ arXiv riêng vẫn giữ v0 bảng7.2, vmax60 và default P hiện tại. Không trộn
IEEE vmax30 với các hệ số arXiv trong một run. Quyết định chọn bộ rotor cho
mission paper nằm trong [decision sheet](author_parameter_decision_sheet_vi.md).

## 2. Bảy nhóm audit và các phát hiện chính

### 2.1 CV-QKD / SKR

Nguồn trực tiếp là sibling package
`paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/`. Đã đọc
`run.py`, `report_vi.md`, `execution_physical_protocol.json`, đếm lại
`source_pool.csv` và `skr_map.csv`:

- 2.601 spatial node samples; 51×51, tọa độ0..2.000 m; đơn vị bits/use.
- Pool212 nguồn:33Uniform và179MB. Mỗi geometry dùng cùng finite catalog;
  `select_family` chọn max raw signed K, không tối ưu liên tục nu/VA.
- Toàn bộ2.601 winner MB mang `INSUFFICIENT_EVIDENCE`. Raw MB min/max là
  .0007470670338268481 và .0007960878080861267 bits/use. Đây là giá trị số
  có thật, không phải dữ liệu thiếu hoặc được suy từ màu hình.
- R_raw=beta*I_AB-chi_BE. Q protocol ghi effective homodyne real1D,
  reverse-asymptotic, direct Eq14 và original Eq10 retained[0,1] law. Giữ
  noise, source moments và convention của lineage này, không đổi bằng giá trị
  từ một plot/cache khác. VA convention khác bản in đã được ghi rõ trong protocol.
- Producer đọc geometry có sẵn, nhóm equal-radius quanh HAP projection
  (1000,1000), đánh giá từng candidate từ source moments đã lưu, lưu context/
  candidate/identity/benchmark rồi ghi các bảng và NPZ. Report cũ ghi325 context,
  68.900 candidate calls và2 benchmark calls; **đây là số của lần chạy đã lưu,
  không phải số đánh giá mới của Phase2**. Scientific producer content, source
  payload và LF/CRLF bindings được mô tả trong report/receipts gốc.
- Khả năng tái lập phải dựa trên producer/config/input/source hashes và các
  kiểm tra số đúng phạm vi, không chỉ giữ seed. Các receipt numerical PASS
  không giải quyết source/security scope. Không thực thi lại `run.py --execute`
  hoặc source jobs trong audit này; completed namespace không được ghi đè.

S1 raw CSV/NPZ chưa đúng schema generic loader (`x_m,y_m,skr_bits_per_use`
hoặc NPZ `points,rates`). Cần adapter lossless riêng sau khi admissibility và
raw/potential policy được quyết định. `SKRLookup` nội suy tuyến tính và từ
chối extrapolation; không được coi interpolation là một lượt tối ưu mới.

Active IDE report `SKR_DISTANCE_NO_FADING_NOISE_CACHE_REPORT_VI.md` mô tả
lineage khác, bỏ phương sai fading và dùng ideal heterodyne/no detector noise.
Không hoán đổi các rate đó vào receiver30 map hoặc gọi chúng tương đương vì
cùng tên CV-QKD. Dữ liệu catalog source không tự chuyển thành source-verified
security hoặc optimum continuous/global.

### 2.2 Finite-size-aware key yield

`finite_size.py` thực hiện ổn định số cùng công thức tích lũy:

\[
m_0=f_s\Delta t\eta_{\mathrm{valid}},\quad
n_K=m_0\sum_k z_k,\quad S_K=m_0\sum_k z_kr_j,
\]

\[
\widehat\ell_K=\max\{0,S_K-7\sqrt{n_K\log_2(2/\epsilon)}\}.
\]

Khi n=0 thì key=0. Logarithm dùng biểu thức tương đương1-log2(epsilon) để
tránh overflow ở epsilon nhỏ. Không cộng các slotwise finite penalties.
`dt=1`, beta=.95 đã có căn cứ; fs/valid fraction/m0/epsilon chưa có giá trị
paper. Beta nằm trong asymptotic input rate, không phải eta_valid hay detector
efficiency. K là output quyết định/prefix, không được tác giả gán một giá trị
cố định thay bài toán. Proxy qua các channel states chưa là composable proof.

### 2.3 Hình học

HAP20 km, UAV1 km, vùng2×2 km và dt1 s đã được ghi. Producer lookup đặt
projection(1000,1000)m, nhưng `paper.yaml.hap_m` và `initial_m` vẫn null.
Chọn kế thừa geometry đó cho mission là một quyết định rõ, không suy từ màu
heatmap hoặc copy điểm xuất phát demo. Không dùng RF altitude100m hay qI/qF
của bài IEEE rotor. Vmax hiện60 m/s của default arXiv;30 m/s là profile IEEE
riêng, chưa tự áp dụng cho mission.

### 2.4 Mây và LOS

`CloudField` tính Gaussian tại tọa độ tùy ý với center(0)+v*t, không dịch mảng
theo bước40m/giây. `BlockageModel` cắt segment HAP→UAV với slab altitude rồi
lấy mẫu trên horizontal segment. Điều kiện blocked là CLWC>=Lth tại samples,
không phải UAV endpoint rơi vào ô đen. Sampling có thể bỏ sót vùng hẹp.

Vận tốc[-5,0], cloud grid50×50 và cell40×40m được xác định. Field coefficients,
Lth, cloud layer và LOS spacing paper vẫn chưa chọn. Bộ400-kernel saved field
ở `dynamic_gaussian_cloud_figure/` là minh họa; bộ3-kernel của demo là fixture
khác. Cloud grid không quyết định waypoint graph; UAV coordinates vẫn liên tục.

### 2.5 Năng lượng và mission

Giữ evaluator và numerical lower convex envelope hiện có. Graph edges thỏa
distance<=vmax*dt, costs=E_min(distance,dt); self-loop có hover energy.
Emax, graph/spacing và prediction cap paper chưa có. K upper bound được dẫn
xuất từ min positive feasible edge cost, gồm cả hover, rồi giao với horizon
dự báo. Hover không nhất thiết là minimum-power operation. Không thêm các
communication/turning/transient costs chưa thuộc model.

### 2.6 Bốn thuật toán

`experiments.run_methods` truyền cùng Scenario cho Stationary, SKR-Greedy,
Energy-Aware Greedy và Pareto DP: graph, edge costs, rates, z, budget, m0,
epsilon và terminal evaluator dùng chung. Stationary vẫn tốn hover energy.
Greedy maximizes immediate m0*z*r, energy-aware thêm -lambda*c; tie-break có
định nghĩa. Mỗi baseline xét mọi prefix feasible. DP cập nhật nhiều labels,
dominance chỉ trong cùng(k,j,u), giữ parent pointers để backtrack; cap làm
mode approximate. P1=L/(K*dt), P2=L được chọn riêng trên mọi terminal feasible.

DP dùng predicted future clouds; greedy dùng current-slot decision information.
Cả bốn chọn stopping prefix hồi cứu. Vì vậy so sánh không chỉ là algorithmic
superiority và không là guarantee về online stopping. Lambda cần prior hoặc
calibration provenance riêng, không tune trên realization đánh giá.

### 2.7 Paper-mode, outputs và runtime

Chưa có paper result bundle. `run.py`/`build_scenario` từ chối input thiếu;
`research_use_authorized=false`. Điền đủ null cũng không tự làm model an toàn:
producer paper hiện vẫn xuất `UNVALIDATED_SECURITY_MODEL — RESEARCH PERFORMANCE
APPROXIMATION`. Exporter còn kiểm audit/source-admissibility, config equality,
required file seals, core producer bindings và metric replay. Không sửa literal
status chỉ để qua gate; review phạm vi và bằng chứng phải đi trước thay đổi policy.

Timing và memory phải đo từ cùng run được phép: runtime có instrumentation,
Python allocation peak khác sampled process RSS10ms; precomputation chung không
nằm trong method runtime. DEMO có measurement thật của dữ liệu tổng hợp, không
phải measurement paper. Các graphs/caps/label counts/seed và môi trường đo phải
được lưu nếu muốn so sánh DP về chi phí tính toán.

## 3. Cổng thực thi chung và thứ tự ưu tiên

1. **G0 — tác giả/nguồn:** chốt claim/lineage và giải quyết source evidence,
   convention và lifecycle phù hợp. Tôn trọng source/frozen restrictions của
   dự án quang; không có authorization mới từ việc viết kế hoạch này.
2. **G1 — quyết định input:** dùng decision sheet để chốt protocol tín hiệu,
   geometry/rotor/scenario, cloud, energy/graph/horizon và lambda có provenance.
   Không có giá trị đề xuất được tự điền trong Phase2.
3. **G2 — base bundle:** chạy bốn method/cả P1/P2 chỉ sau G0/G1, giữ cùng
   physical inputs; tạo đầy đủ config/input/producer/output seals và replay.
4. **G3 — readiness review:** đối chiếu output evidence và scope thật với
   producer/current audits. Một bundle tính đúng nhưng unvalidated không được
   tự gắn READY. Chỉ sau review tương ứng mới render dưới nhãn phù hợp.
5. **G4 — sensitivity/benchmark:** sau base correctness, chạy các grid được
   chốt và workload đo thật; không ép exact DP vào graph lớn để có thêm số.

**Ưu tiên cao nhất:** giải quyết G0 và thu thập G1 song song; một base bundle
đủ điều kiện có thể cấp dữ liệu cho C02–C09 theo bộ nạp hiện tại. C10 cần sweep
bổ sung. Không có chín mô hình/solver riêng cần viết lại.

C02/cloud và C03/asymptotic map có ít phụ thuộc khoa học trực tiếp hơn các
trajectory figures. Nhưng loader hiện dùng một shared bundle gate cho C02–C10;
không thể hứa chỉ đưa một NPZ cloud vào là đủ READY. Nếu muốn minh họa hoặc
diagnostic trước mission, phải có review scope/cổng riêng trong task sau,
không bỏ gate trong Phase2 và không đổi EXPLORATORY thành paper-ready.

## 4. Lệnh dự kiến — chưa thực thi trong Phase2

Các lệnh dưới đây chạy từ `uav_cvqkd_optimization/`, chỉ khi các điều kiện nêu
trước đã được đáp ứng. Đây là đường dẫn **mới dự kiến**, không phải file đã có
hay mô phỏng thành công; nếu thư mục đã tồn tại phải chọn namespace mới.

```powershell
$env:PYTHONPATH='src'
```

**E0 — kiểm thử phần mềm, đã thực thi trong Phase2:**

```powershell
python -X utf8 -m pytest -q
```

**E1 — tạo base/sensitivity bundle, chỉ sau G0/G1 và quyền thực thi đúng phạm vi:**

```powershell
python -X utf8 -m uav_qkd.run --config configs/paper.yaml --output results/paper_phase2_run01
python -X utf8 -m uav_qkd.verify --output results/paper_phase2_run01
```

Ghi chú: run hiện bao gồm sensitivity nếu được cấu hình, có thể dùng
`--skip-sensitivities` cho base-run stage. Không gọi lệnh này lúc P hiện vẫn
null/authorization false. Verify là numerical/integrity replay, không thay G3.

**E2 — render catalog khi đã có dữ liệu và readiness phù hợp:**

```powershell
python -X utf8 -m uav_qkd.paper_figures --config configs/paper.yaml --results results/paper_phase2_run01 --output figures/paper_phase2_edition01 --column double
```

Exporter hiện là batch command, **không có `--figure`**. Các hình bên dưới
tham chiếu E2 cùng dependency/data cụ thể, không phát minh cờ CLI chọn từng
hình. `--column single` dùng một output namespace mới nếu cần.

**E3 — chọn sensitivity P1 thay vì P2 mặc định:**

```powershell
python -X utf8 -m uav_qkd.paper_figures --config configs/paper.yaml --results results/paper_phase2_run01 --output figures/paper_phase2_P1_edition01 --column double --sensitivity-objective P1
```

Nếu tác giả chọn IEEE làm mission default mới, cần một task tích hợp và audit
trước E1; hiện chưa có thay đổi như vậy. Gate source của C01 trong renderer
đang gắn với arXiv profile cũ, còn R02-IEEE có entry point riêng. Không coi
việc đổi rotor YAML là đủ để toàn bộ catalog/claims tự khớp.

## 5. Kế hoạch từng hình chưa hoàn thành

Trong mọi mục, điều kiện READY bao gồm G0–G3 của loader hiện tại; chỉ liệt kê
đủ data số không thay thế source/evidence/readiness. File nguồn và phân loại
chi tiết xem [decision sheet](author_parameter_decision_sheet_vi.md).

### C02 — Catalog02: Gaussian CLWC và binary blockage maps

- **Code:** `paper_figures.plot_fig02_cloud_maps`, `cloud_model.py`,
  `blockage.py` và bộ nạp shared inputs.
- **Bắt buộc trực tiếp:** coefficients Gaussian, velocity, coordinate frame,
  clip policy nếu dùng, threshold, display times/domain/grid. Layer/LOS cần
  cho link-availability/base bundle, không phải riêng horizontal coverage plot.
- **Đã có:** source settings của vùng2×2 km, grid50×50, drift5m/s, times0/300/1000;
  saved coefficients ở sibling `dynamic_gaussian_cloud_figure/`, chỉ minh họa.
- **Còn thiếu:** paper realization được chọn, Lth/clip/frame/provenance; layer,
  thickness, LOS resolution và các input của G1/B0 nếu dùng renderer hiện tại.
- **Nguồn cần kiểm:** realization có phải measured hay simulated scenario;
  label assumption, units/covariance, layer geometry và opacity interpretation.
- **READY khi:** có shared verified bundle và field/masks tái lập từ đúng
  cùng coefficients, source/readiness được review; không nâng mây minh họa ngầm.
- **Lệnh dự kiến:** E2 sau E1/G3; không có CLI riêng chọn C02.
- **Tạo ngay?** Không. Tác giả phải chọn/ghi nguồn scenario; không phải chỉ lỗi
  plotting. Không cần C03 để tính Gaussian về toán, nhưng shared gate vẫn áp dụng.

### C03 — Catalog03: Spatial asymptotic SKR lookup

- **Code:** `paper_figures.plot_fig03_skr_lookup`, `skr_lookup.py`,
  producer receiver30 S3 chỉ làm nguồn tham chiếu, không thực thi tại đây.
- **Bắt buộc trực tiếp:** spatial coordinates/rates/units, geometry/physical
  protocol và admissibility, native/generic schema với raw/potential policy.
- **Đã có:** S1/QDATA đủ2.601 điểm và212-candidate numerical provenance;
  projection(1000,1000), HAP/UAV20/1km và receiver context đã ghi.
- **Còn thiếu:** evidence đủ cho phạm vi paper, lookup.file/sha256/provenance
  và adapter lossless; hiện không có bản paper-admitted generic input.
- **Nguồn cần kiểm:** C,w/evidence, Eq10 support convention, homodyne effective
  model, normalization mapping, finite-catalog scope và permission/lifecycle.
- **READY khi:** review chấp nhận đúng scope bằng bằng chứng, bindings và
  units hợp lệ, shared loader không nhận synthetic/unvalidated như certified.
- **Lệnh dự kiến:** E2 sau data admission/G3; không chạy lại source/MB search
  từ một lệnh exporter. Nếu cần tái sinh source, phải có task riêng được phép.
- **Tạo ngay?** Không. Bảng có số nhưng thiếu evidence, không phải file bị mất
  hoặc chỉ sai header. Đổi tên cột hay caption không đủ mở khóa.

### C04 — Catalog04: Selected P1 trajectories

- **Code:** `plot_fig04_trajectory_p1`, `baselines.py`, `dp_solver.py`,
  `evaluation.py`, graph/energy/blockage/lookup modules.
- **Bắt buộc:** q0, HAP geometry, r[j], z[k,j], graph/costs, Emax, m0, epsilon,
  dt, prediction horizon, lambda prior; selected P1 paths/indices/K/classification.
- **Đã có:** bốn thuật toán và verified software contracts, rotor profiles,
  source geometry context, synthetic demo paths và tests; chưa có paper paths.
- **Còn thiếu:** G1 và B0 đúng scope; mọi path paper vẫn chưa tính.
- **Nguồn cần kiểm:** lookup và cloud evidence, protocol tín hiệu, scenario
  decisions, chế độ exact/approx và thông tin dự báo giữa method.
- **READY khi:** cùng scenario, prefix optimization L/(K*dt), path feasibility/
  backtracking replay và seals qua G2/G3, không dùng lại demo trajectory.
- **Lệnh dự kiến:** E1 base stage, verify, rồi E2.
- **Tạo ngay?** Không; chờ quyết định và bằng chứng. Không cần renderer C02/C03
  đã chạy trước, chỉ cần input khoa học tương ứng.

### C05 — Catalog05: Selected P2 trajectories

- **Code:** `plot_fig05_trajectory_p2` và cùng solver/evaluation stack của C04.
- **Bắt buộc:** cùng physical/mission inputs với C04, nhưng terminal/path tốt
  nhất theo total L, không thay bằng selected P1 path.
- **Đã có:** hỗ trợ hai objective từ một DP run và prefix selection của
  baselines; demo schema. Đây không phải một paper P2 experiment.
- **Còn thiếu:** input G1 và `solutions.P2` của bốn method trong B0.
- **Nguồn cần kiểm:** tương tự C04; không ép duration/trajectory trùng P1.
- **READY khi:** selected P2 terminals/paths có replay, feasibility, source và
  scope đúng; đủ G0–G3.
- **Lệnh dự kiến:** cùng E1 và E2 với C04, không phải bốn run vật lý mới.
- **Tạo ngay?** Không. Dùng chung base experiment sau quyết định tác giả.

### C06 — Catalog06: Cumulative propulsion energy

- **Code:** `plot_fig06_energy`, `propulsion.py`, `waypoint_graph.py`,
  `evaluation.py`.
- **Bắt buộc:** selected P1/P2 prefixes, đúng rotor/dt, edge costs, cumulative
  energy/time và budget; không padding sang duration method khác.
- **Đã có:** cả hai rotor profile riêng, model/lower-convex-envelope implementation
  và tests; computed demo series có nhưng thuộc input khác.
- **Còn thiếu:** paper paths, graph, Emax, mission configuration và B0.
- **Nguồn cần kiểm:** profile được chọn cho run, convergence của numerical
  edge costs, energy accounting và bỏ acceleration/turning assumptions.
- **READY khi:** replay tổng costs theo path và budget/speed checks qua;
  selected path provenance/G3 hợp lệ. Không cần sửa power equation.
- **Lệnh dự kiến:** E2 từ cùng E1; không chạy solver chỉ để cộng lại energy đã lưu.
- **Tạo ngay?** Không. C04/C05 cung cấp path data; không phụ thuộc file PDF C01.

### C07 — Catalog07: Accumulated finite-size quantities

- **Code:** `plot_fig07_finite_size`, `finite_size.py`, `evaluation.py`.
- **Bắt buộc:** selected P2 paths, m0/epsilon/dt, z/r và time-series n,S,penalty,L.
- **Đã có:** formula/evaluator và tests n=0, sqrt scaling, stability; demo
  series chỉ dùng kiểm phần mềm.
- **Còn thiếu:** fs/valid fraction hoặc m0 có căn cứ, epsilon, paper inputs và
  selected P2 series thực.
- **Nguồn cần kiểm:** valid-block definition, epsilon/protocol scope, consistency
  của r và z; proxy không thành composable theorem.
- **READY khi:** accumulated correction được áp dụng một lần cho mỗi prefix,
  các metric replay khớp và G0–G3 đủ. Cần inputs của C05, không cần render C05 trước.
- **Lệnh dự kiến:** E1/verify, rồi E2.
- **Tạo ngay?** Không; không chọn epsilon demo để vẽ một hình được gọi paper-ready.

### C08 — Catalog08: Final key and average throughput comparison

- **Code:** `plot_fig08_key_comparison`, `selected_solutions`, shared evaluator.
- **Bắt buộc:** bốn selected P1 rates bits/s và P2 totals bits, durations,
  feasibility/classification và fair shared-scenario metadata.
- **Đã có:** schema/logic chọn riêng P1/P2, deterministic tie handling, demo
  outputs và tests; không có paper method outcomes.
- **Còn thiếu:** B0 và các scalar terminal tương ứng, nguồn/decisions G0/G1.
- **Nguồn cần kiểm:** m0/epsilon, lookup, scenario, lambda provenance và thông
  tin cloud; không chọn phương pháp trên scenario khác nhau để báo gain.
- **READY khi:** scalar khớp series và L/(K*dt), cùng điều kiện physical input,
  mô tả đúng offline prediction/retrospective stopping; G3 scope hợp lệ.
- **Lệnh dự kiến:** E2 từ E1 cùng C04–C07; không cần experiment thứ hai để vẽ bar.
- **Tạo ngay?** Không. Không điền zero cho method chưa đo hoặc chưa chạy.

### C09 — Catalog09: Runtime and memory

- **Code:** `plot_fig09_runtime_memory`, `experiments.measured/run_methods`,
  DP diagnostics; không phải đồng hồ của exporter.
- **Bắt buộc:** runtime_s, python_peak_bytes, sampled_peak_rss_bytes từng
  method trên cùng workload, graph/horizon/cap/environment và scope đo.
- **Đã có:** measurement wrapper, demo timings/memory và label diagnostics.
  Đó là số đo thật của run synthetic, không phải paper benchmark.
- **Còn thiếu:** paper measurements, workload/environment được chọn và B0.
- **Nguồn cần kiểm:** instrumentation/native-memory distinctions, machine/load
  conditions, exact/approx labels và repeated benchmarks nếu claim thống kê.
- **READY khi:** có measurement record thật, sealed và complete theo G2/G3;
  không suy runtime từ complexity, không lấy pytest time hay copy demo timing.
- **Lệnh dự kiến:** measurement được tạo trong E1, hình trong E2. Nếu cần
  statistical benchmark lặp thì chốt protocol/workload trước một task đo riêng.
- **Tạo ngay?** Không. Không tự chạy exact graph lớn để tạo thêm con số.

### C10 — Catalog10: Sensitivity

- **Code:** `plot_fig10_sensitivity`, `experiments.sensitivity_runs`,
  solver/baselines/evaluator hiện có.
- **Bắt buộc:** grid energy/threshold/waypoint spacing/label caps đã chốt,
  cùng inputs không khảo sát, bảng có đủ method/objective/parameter/metric/status
  và classification; file CSV phải được seal.
- **Đã có:** sweep implementation và demo CSV/approximation gap trên trường
  hợp nhỏ, không có paper sensitivity.
- **Còn thiếu:** paper grids (P chưa có sensitivities block), base scenario,
  nguồn/decisions, measured outputs của từng biến thể.
- **Nguồn cần kiểm:** control of confounders, giữ lambda đã chọn từ trước,
  graph connectivity/movement và loss of exactness khi cap active.
- **READY khi:** G0–G4 đủ, các objective/finite-key field được kiểm, records
  tồn tại thật; không nội suy ra sensitivity cases chưa chạy.
- **Lệnh dự kiến:** E1 với sensitivities được cấu hình khi cho phép; E2 cho
  P2 mặc định hoặc E3 cho P1, mỗi edition ở output namespace mới.
- **Tạo ngay?** Không. Ưu tiên sau base-run correctness để không nhân chi phí
  của một cấu hình hoặc nguồn chưa phù hợp.

## 6. Tác vụ an toàn đã thực hiện, việc còn chờ

Đã kiểm tra repository/code/data, đối chiếu source version/figure numbering,
xác nhận file IEEE2019 và integrity bindings, đếm lookup/catalog, chạy suite
hiện hữu và tạo đúng hai tài liệu Phase2. Suite hiện tại:
**70 passed in 16.12s**, `CURRENTLY_VERIFIED_PASS` ở phạm vi phần mềm; không
thêm/xóa/làm yếu test. Kết quả này mới đo trong lượt Phase2, không chép số cũ.

Không phát hiện hình CV-QKD mới nào vừa đủ dữ liệu được xác minh vừa chỉ mắc
một lỗi kỹ thuật. Mismatch hash tài liệu catalog là snapshot-version issue
đã có bản cũ khớp hash, không phải lý do nâng các hình thiếu source thành READY.
Không có sửa code hoặc xuất hình mới nào được thực hiện.

Năm nhóm quan trọng nhất còn chờ:

1. Source-admissible SKR/claim/receiver lineage, không chỉ header của CSV.
2. fs/valid fraction hoặc m0, epsilon và valid-block/proxy interpretation.
3. Mission scenario: rotor selection, q0/HAP coordinates, Emax, graph/horizon
   và prior lambda có provenance.
4. Cloud realization, Lth/clip/frame, altitude/thickness, LOS resolution.
5. Sealed paper outputs và measurement/sensitivity thực sau các điều kiện trên.

Ba hành động tiếp theo theo thứ tự: (1) source/claim readiness review cùng
decision sheet; (2) tác giả chốt một scenario/protocol hoàn chỉnh có provenance,
không copy demo; (3) sau khi đủ quyền và bằng chứng, chạy một base bundle có
measurement/replay rồi mới sensitivity và render edition mới. Không có hình
CV-QKD mới nào được tạo ngay trong scope hiện tại; C02 là ứng viên ít phụ
thuộc vật lý nhất nhưng vẫn cần scenario author decision và policy phù hợp.

Không sửa `paper.yaml`, model/optimizer/plotting code, trạng thái nguồn hay
paper-mode; không đổi số/tên/ghi đè hình hoặc kết quả lịch sử; không tạo dữ liệu
ngẫu nhiên/placeholder cho paper, không commit/push. Các lệnh E1–E3 và hành động có điều
kiện trong tài liệu này là **kế hoạch**, không phải execution receipt hoặc một
quyết định khoa học mới đã được phê duyệt.
