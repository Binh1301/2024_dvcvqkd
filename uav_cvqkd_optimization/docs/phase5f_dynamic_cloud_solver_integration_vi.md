# Phase5F — tích hợp lookup Phase5E, dynamic cloud và trajectory solver

**Đã tích hợp và chạy thành công pipeline kỹ thuật TEST_ONLY**, dùng nguyên
lookup Phase5E đã niêm phong. Không tái sinh SKR, không chạy native MB/QAM
evaluator, không chốt mission/cloud inputs và không chạy paper-mode.

## 1. Source và cấu hình

[phase5f_integration.py](../src/uav_qkd/phase5f_integration.py) đọc trực tiếp CSV,
NPZ, target protocol và validation summary trong
`results/phase5d_full_target_radial_2proc_PHASE5E_20261108/`.
Adapter pin package SHA-256
`7b3f3b4fe7a4cd9c9f046aa456f3a1a4e4b8cf83c327f09e0fba23c28831bfa7`,
kiểm đủ624 files/no unsealed extras trước khi dùng rate, rồi kiểm grid/order,
noise .0136/.005 SNU, beta .95, coordinate units m, rate units bits/use,
raw-rate alias và CSV/NPZ.

Giữ2601 lookup nodes trên51×51 grid0..2000m,step40m. HAP projection(1000,1000)m,
altitude HAP/UAV20000/1000m được đọc từ metadata **của dataset**. Mission không
được tự kế thừa HAPxy: builder từ chối geometry khác hoặc thiếu. Truy vấn hiện
chỉ nhận **exact lookup nodes**, không nội suy/off-grid/extrapolation ngầm.
Không fallback sang historical lookup .0186, không clip signed raw rate và
không nâng evidence/admission qua numeric API.

Hai config riêng:

- [phase5f_candidate.yaml](../configs/integration/phase5f_candidate.yaml): pending
  author decisions, inputs chưa có để null; candidate approval=false.
- [phase5f_test_only.yaml](../configs/integration/phase5f_test_only.yaml): explicit
  software fixture. Tất cả số graph/rotor/energy/dt/cloud/m0/epsilon/lambda chỉ
  dùng để exercise pipeline, không phải source-verified mission recommendations.

Runner Phase5F chỉ nhận mode/label `TEST_ONLY`, giới hạn6slots/8explicit graph
points và từ chối paper-mode. Không đổi `paper.yaml`, original reference,
rotor profiles hoặc official cloud candidate. Việc instantiate LOS model trong
test fixture không phải author approval của binary_los_blockage baseline.

## 2. Dynamic cloud/rate và finite-size accounting

Tái dùng `CloudField`, `GaussianCluster`, `BlockageModel`, raw rotor profile
loader, `EnergyModel`, `WaypointGraph`, `Scenario`, `sample_rate_provider` và
`run_methods`. Không sao chép công thức model/solver.

`BinaryLOSRateProvider` kiểm HAP→UAV3D segment giao cloud altitude slab rồi
sample CLWC trên phần giao; không test riêng ô/cell tại endpoint. Gaussian
centers advect liên tục với(-5,0)m/s, không snap40m mỗi slot. Per-cluster
velocities khác drift khai báo bị từ chối. Nguồn/realization được snapshot
một lần trước khi bốn phương pháp chạy.

Với scheduled use:

\[
R_{\rm eff}(q,t)=z_{\rm LOS}(q,t)R_{\rm clear}(q).
\]

Để valid-signal accounting rõ nghĩa, `Scenario.rates` lưu **R_clear per retained
use**, không mask lại; `Scenario.z` lưu z_LOS theo slot. Do đó:

\[
m_k=m_0z_k,\quad S_K=m_0\sum_kz_kR_{\rm clear}(q_k),\quad
n_K=m_0\sum_kz_k,\quad
\widehat L_K=\max(0,S_K-7\sqrt{n_K\log_2(2/\epsilon)}).
\]

`effective_rate` chỉ là cách trình bày scheduled-rate và kiểm consistency;
không nhân nó thêm lần nữa vào contribution. Blocked LOS cho effective T=0,
effective rate=0,m=0,raw contribution=0; clear LOS giữ clear T/rate và m0.
Không thêm optical attenuation hoặc CLWC→extinction coefficient. P1/P2 và
one accumulated-prefix penalty dùng nguyên evaluator hiện có.

Snapshot zero-based row k-1 tương ứng destination q_k,t_k=k*dt, cùng quy ước
với `BlockageModel.sequence`. Clear retained-rate có thể cache theo node vì
static; **dynamic z/effective-rate không cache chỉ theo vị trí**. Không có
geometry deduplication cho cloud state.

Cloud figure convention được giữ và kiểm:2000×2000m operating region,
50×50 visualization cells,40×40m; static-reference window left edges0/1500/
5000m tại0/300/1000s. Đây là inverse cloud-coordinate shift, không di chuyển
vùng UAV vật lý. Visualization grid không được dùng làm waypoint graph;
fixture graph chỉ có3explicit lookup nodes.

## 3. Four-method fairness và technical dry-run

Bốn method dùng cùng một Scenario: q0,graph,edge costs/rotor,energy budget,
horizon,clear source,cloud realization,z/time convention,m0/epsilon và
terminal-prefix evaluator. Shared-input digest được kiểm trước/sau execution.

DP action planning đọc full predicted cloud horizon; greedy action chỉ đọc
current-slot row. Mọi method chọn best feasible prefix hồi cứu cho P1/P2;
đó không phải causal online stopping guarantee và không phải benchmark ngang
quyền dự báo. Không quy gain của fixture thành performance claim của paper.

CLI **đã chạy**, từ `uav_cvqkd_optimization/`:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -B -m uav_qkd.phase5f_integration `
  --config configs/integration/phase5f_test_only.yaml `
  --output test_artifacts/phase5f_dry_run_20261108
```

Artifacts tại
[test_artifacts/phase5f_dry_run_20261108](../test_artifacts/phase5f_dry_run_20261108):
`dry_run.json`, `scenario_TEST_ONLY.npz`, `slot_quantities_TEST_ONLY.csv`,
input/output manifests. Tất cả output mang `TEST_ONLY — NOT RESEARCH OR PAPER
RESULTS`; không ghi fixture vào `results/` và không xuất hình paper.

Kết quả chỉ là kiểm tra phần mềm: bốn methods đều FEASIBLE; Stationary giữ
nguyên q0; SKR-Greedy/DP và Energy-Aware Greedy có paths được evaluator kiểm
energy/speed. Với fixture3nodes, availability theo4slots là:

```text
[[1,0,1], [1,1,1], [1,1,1], [0,1,1]]
```

Fixture dt=2s,m0=1e8/clear-slot,epsilon3e-8,E1600J,IEEE rotor vàlambda.5 là
**software test values**, không áp dụng sang candidate config. f_s và eta_valid
vẫn null; không suy chúng từ m0 hoặc reference key_fraction. Tests chạy cả
clear/all-blocked/moving-cloud cases, không diễn giải số key fixture như research
outcome hay composable-security proof.

## 4. Tests và validation

Các end-to-end/domain cases kiểm: source package pin/coverage/tampering,
historical rejection, HAP geometry mismatch, clear-sky/static equivalence cả
bốn methods, full LOS blockage, changing-slot cloud, endpoint-clear/path-blocked,
continuous drift và window1500m không snap, end-slot indexing, stationary,
energy/speed infeasibility, one accumulated finite penalty, no double erasure,
deterministic replay, missing-input/paper refusal và output isolation.

[Independent review](phase5f_independent_review.md) phát hiện hai boundary bugs:
supplied source object có thể giữ identity nhưng sửa numeric contents, và
per-cluster velocity có thể override global drift. Đã tái hiện RED và sửa:
builder luôn verify/reload canonical package, không dùng object do caller đưa
làm active data; chỉ chấp nhận nó nếu contents khớp. Per-cluster drift phải
khớp global. Thêm null-finite-block missing-input guard; không điền default.

Suite cuối: **193 passed in12.21s,0 failed,0 errors,0 skipped** (177 có sẵn
và16 case mới), exit0:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5f_validation/tests.xml
```

Bằng chứng trong
[verification.json](phase5f_validation/verification.json) và
[tests.xml](phase5f_validation/tests.xml). Không có native SKR calls trong Phase5F.
Package Phase5E và toàn bộ old model/config/results được kiểm lại hashes.

Independent artifact follow-up đã kiểm4 output hashes,7 input hashes,31 producer
hashes,whole624-file Phase5E source,12slot rows cùng NPZ snapshot và tất cả8
selected P1/P2 metrics bằng arithmetic. Không có inconsistency; review chỉ
phê duyệt scope TEST_ONLY, không thay scientific approvals/lifecycle.

## 5. Quyết định còn thiếu cho base experiment

| Quyết định | Phương án có căn cứ để tác giả chốt; ảnh hưởng |
|---|---|
| Binary LOS blockage approval | Chấp nhận idealized opaque-LOS erasure hoặc yêu cầu model khác; candidate hiện chưa approved |
| CLWC threshold L_th | Cung cấp nguồn/scenario rationale; threshold8 của fixture không phải universal opacity threshold |
| Cloud layer altitude/thickness | Chọn từ dữ liệu mission/meteorology hoặc khai báo assumption; quyết định phần LOS giao mây |
| Cloud realization và seed | Chọn explicit coefficients hoặc generator+seed/version+manifest; giữ cố định cho cả4methods |
| HAP horizontal coordinates | Có thể chọn đúng lookup projection(1000,1000)m để reuse nếu tác giả đồng ý; geometry khác cần source/rate phù hợp |
| UAV initial position q0 | Chọn node cụ thể có rationale, nằm trong graph; không mặc định dùng center của fixture |
| Energy budget | Cung cấp usable propulsion allocation J; không dùng1600J fixture |
| Mission horizon | Chọn forecast-available cap và dt; K optimal vẫn do prefix objectives/energy quyết định |
| Waypoint graph | Chọn explicit nodes/connectivity; exact-node adapter hiện dùng lookup nodes40m, không dùng50×50 visualization cells |
| Symbol rate f_s | Cung cấp source/definition, không lấy RF bandwidth hoặc N_block làm f_s |
| Valid-signal accounting | Chốt eta_valid cho clear slots và m0=fs*dt*eta_valid hoặc m0 trực tiếp có provenance; tránh chứa lại cloud loss |
| Rotor baseline | Chọn nguyên arXiv2018v1 hoặc IEEE2019 profile, không trộn coefficients/vmax; default paper không đổi |
| Greedy lambda | Prior bits/J có provenance hoặc calibration độc lập được cho phép; không tune theo test realization |

Ngoài ra epsilon/block interpretation, security-claim scope và quyền chạy
Phase6/base experiment vẫn cần chốt. Reference epsilon3e-8/n8e7/key_fraction.8
không tự trở thành mission parameters.

Constraint cần lưu ý khi chốt graph/dt: IEEE profile vmax30m/s không đi được
giữa exact lookup nodes cách40m trong dt1s. Tác giả cần chọn dt/graph nhất quán
hoặc author-approve validation off-grid/interpolation trong task khác. Fixture
dt2s chỉ để exercise transitions; không tự thay source slot của mission.

## 6. File changes và Phase6 status

File mới: `src/uav_qkd/phase5f_integration.py`, `tests/test_phase5f_integration.py`,
hai YAML integration configs, plan/review/report và validation artifacts,
TEST_ONLY dry-run directory. Không sửa existing mathematical model, original
QAM/Z/w/Holevo,rotor profiles,paper.yaml hoặc historical/Phase5E lookup/pilot.

**Chưa thể chạy Phase6 — Base Trajectory Experiment như research/paper run.**
Technical pipeline đã PASS, nhưng author decisions ở trên còn thiếu; runner
Phase5F cố ý chỉ chạy TEST_ONLY và không tự mở research/paper lifecycle.
Official binary_los_blockage candidate vẫn unapproved. Catalog1 READY/9 BLOCKED
và IEEE rotor reference READY riêng giữ nguyên; source/security evidence
không được nâng. Không commit/push.
