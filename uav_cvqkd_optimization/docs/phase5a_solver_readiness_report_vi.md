# Báo cáo readiness solver theo thời gian — Phase 5A

## 1. Kết quả và giới hạn

Solver đã nhận rate tĩnh R[j] và rate động R[slot,j]. Cả bốn method và evaluator
đều dùng `Scenario.rate_at(slot,j)`. Đây là **hạ tầng phần mềm đã triển khai**,
không phải kết quả mission hoặc một CV-QKD security certificate. Không chạy
paper-mode, tạo hình mới hay tính SKR mới từ MB backend trong Phase5A.

`paper.yaml`, hai profile rotor, công thức Z/w, thuật toán MB/Holevo, CSV/NPZ
lookup gốc và hình lịch sử được giữ nguyên. Không Deep Research, commit/push
hoặc tự đổi `paper_admissible`/evidence labels.

## 2. Bốn khác biệt vật lý được đọc trực tiếp

Metadata cũ:
[execution_physical_protocol.json](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json).
Config mới:
[hap_uav_mb_reference.yaml](../configs/channel/hap_uav_mb_reference.yaml),
bản thảo nhóm tác giả Section IV/PDF p3.

| Parameter | Old lookup | New HAP–UAV config | Unit | Source | Consequence |
|---|---:|---:|---|---|---|
| Receiver aperture diameter | .30 | .08 | m | Old `physical.Dr_m`; new `receiver_aperture_diameter_m` | Khác aperture collection và geometric/pointing factors |
| Beam full divergence | 35 | 233 | µrad | Old `physical.divergence_full_urad`; new `beam_full_divergence_rad` | Khác footprint và geometric coupling; full-angle ở cả hai |
| Transmitter jitter angle, per axis | 1.561 | 15.61 | µrad | Old `physical.jitter_urad`; new `transmitter_jitter_angle_rad` | Khác pointing-displacement distribution |
| UAV position standard deviation, per axis | .10 | 1.00 | m | Old `physical.sigma_h_m`; new `uav_position_sd_m` | Khác position/pointing spread |

Đây không phải thay đổi zeta hay beta. Hai bộ cùng altitude HAP/UAV20/1km,
beta.95 và các field khớp khác trong subset được audit. Noise của reference
mới vẫn null; không copy xi_ch=.0186, xi_det=.005 SNU của receiver30 sang nó.
Kết quả đối chiếu máy nằm tại
[lookup_compatibility.json](phase5a_validation/lookup_compatibility.json).

Với **từng** khác biệt trên, chuỗi phụ thuộc là tham số quang/pointing →
distribution/moments của eta → effective channel → existing MI/Holevo → SKR.
Không cần xem xét lại công thức Z/w để nhận ra thay đổi input này.

| Quantity | Aperture difference | Divergence difference | Jitter difference | Position-SD difference |
|---|---|---|---|---|
| Channel transmissivity/distribution | Có thể đổi collection/pointing moments | Có thể đổi footprint/moments | Có thể đổi pointing moments | Có thể đổi displacement moments |
| Effective excess noise | Có thể đổi qua Var(sqrt(eta)) và E[eta*xi] | Cùng chuỗi moment | Cùng chuỗi moment | Cùng chuỗi moment |
| Vmod của một source cố định | Không tự đổi; giữ VA=Vmod convention | Không tự đổi | Không tự đổi | Không tự đổi |
| VA/nu được chọn nếu tìm lại finite-catalog argmax | Có thể khác | Có thể khác | Có thể khác | Có thể khác |
| Mutual information | Cần đánh giá lại với channel mới | Cần đánh giá lại | Cần đánh giá lại | Cần đánh giá lại |
| Holevo information | Cần đánh giá lại input channel, giữ nguyên implementation | Cần đánh giá lại | Cần đánh giá lại | Cần đánh giá lại |
| Asymptotic SKR | Không chuyển nguyên giá trị cũ | Không chuyển nguyên | Không chuyển nguyên | Không chuyển nguyên |

Không suy ra dấu hoặc độ lớn thay đổi, không nhân một scale vào rate cũ.
Eq17 vẫn dùng T_f=E[sqrt(eta)]² và
T_f*xi_f=(E[eta]-E[sqrt(eta)]²)*Vmod+E[eta*xi]. Đó là phụ thuộc đầu vào đã có,
không phải tính lại công thức lõi MB/Holevo trong Phase5A.

## 3. Lookup cũ được phân loại thế nào

Các nhãn dưới đây là các trục khác nhau, không ép thành một nhãn duy nhất:

- **Compatible only with its original scenario** về phạm vi sử dụng số:
  receiver30, geometry lookup có projection HAP(1000,1000)m, physical/noise/
  protocol và finite-catalog roster đã lưu. Không tự chốt đây là mission mới.
- **Requires regeneration** nếu tác giả chọn profile Section IV mới: cần dữ
  liệu đúng profile/noise/geometry đó, hoặc một phương án evaluation được
  phê duyệt riêng. Phase5A không chạy lại2.601 điểm.
- **Insufficient evidence** vẫn là evidence label hiện hữu của cả2.601 MB
  winner. Không sửa nhãn, không tự suy paper readiness từ numeric PASS.
- **Compatible with the selected scenario** chưa được xác lập cho mission
  paper hiện đang thiếu input. Không tự cấp nhãn này.

`SKRLookup.load(..., reference=..., protocol=...)` từ chối bốn mismatch trước
khi đọc bảng. Nếu subset khớp, guard vẫn từ chối full compatibility chưa được
xác lập; beta/normalization hoặc metadata subset không đủ cho admission.
Config có thể truyền rõ `lookup.reference_config` và `lookup.protocol_file`
theo đường dẫn tương đối với config; thiếu một trong hai bị từ chối.

Đây là rejection guard cho context đang được audit, **chưa phải positive
admission validator cho mọi lookup tương lai**. Raw legacy loading không có
selected reference vẫn giữ numeric API để replay/diagnostic; nó không xác nhận
nguồn hay admissibility. Direct Scenario arrays/callbacks cũng là numerical
boundary, caller phải bind đúng nguồn. Không có auto fallback sang bảng cũ.

## 4. Rate/time interface đã triển khai

| Interface | Contract |
|---|---|
| `Scenario(..., rates, z, ...)` | rates là J-vector hoặc matrix đúng shape của binary z[slots,J], hữu hạn, bits/use; giữ signed raw rate |
| `s.rate_at(slot,j)` | slot zero-based; lấy rate tại destination q_k, k=slot+1, t_k=k*dt; reject index ngoài horizon |
| `sample_rate_provider(s, provider)` | Gọi `provider(q,t,s)` tại mỗi (slot,j) một lần; snapshot matrix và giữ binary z đã có; provider không erase cloud thêm |
| `sample_link_provider(s, provider, policy)` | Nhận Phase4 LinkSlotResult từ `provider(q,t,s)`, kiểm mode/provenance/signals và dựng rates cùng z từ một policy |
| `run_methods(s,c,weight,measure=False)` | Cùng Scenario cho Stationary, SKR-Greedy, Energy-Aware Greedy, Pareto DP |

Quy ước kế thừa `BlockageModel.sequence`: rate và blockage đánh giá **cuối
slot tại q_k**, không lấy q_(k-1) tại t_(k-1). Edge energy trả cho chuyển động
q_(k-1)→q_k trong dt; observation cuối slot là approximation rời rạc hiện có,
không tích phân channel dọc cạnh. K=1 lấy row0, t=dt, không lấy t=0.

Rate/z arrays được copy và đặt read-only; callback không bị gọi lại trong
solver hoặc cache chỉ theo vị trí. Snapshot (H,J) dùng chung tránh mỗi method
sinh một realization khác. Chi phí/memory sampling O(HJ), ngoài decision
timing của `run_methods`; không có runtime superiority measurement mới.

Provider phải là hàm **exogenous theo q,t và context cố định**. Không hỗ trợ
rate tùy lịch sử đường bay, learning state hay partial retained-signal counts
ngầm. Seed/coefficients/backend và provenance phải được caller giữ cùng
realization; adapter không tự sinh cloud hay chọn physical parameters.

Ví dụ sử dụng ở mức API, không phải run paper:

```python
from uav_qkd.rate_provider import sample_rate_provider, sample_link_provider
from uav_qkd.experiments import run_methods

# base_scenario, approved_provider và method_config phải được caller bind đầy đủ.
# Chọn MỘT adapter theo model, không chạy cả hai cho cùng cloud loss.
dynamic = sample_rate_provider(base_scenario, approved_provider)
runs = run_methods(dynamic, method_config, prior_lambda, measure=False)
# Hoặc: dynamic = sample_link_provider(all_clear_template, approved_link_provider, approved_policy)
```

Dynamic path hiện là programmatic Scenario/adapters → `run_methods`, không
thêm YAML/CLI dynamic paper runner hoặc exporter tái dựng callback. `run_experiment`
vẫn build static lookup từ config. Không gán dynamic rates cho static figure03
hoặc dùng saved bundle schema để giả làm dynamic experiment đã chạy.

## 5. Cloud coupling và finite-size

Binary erasure: Phase4 provider trả valid_signals=0, rate=0,T=0 khi LOS/slab
blocked và không gọi MB backend; slot clear giữ m0. Dynamic binary snapshot
được kiểm trùng `BlockageModel.sequence` cùng realization/times.

Optical attenuation: provider đã tính post-loss channel/rate theo model được
chọn, retained_slot=true và valid_signals=m0. Không nhân z để erase cùng cloud
lần nữa. Link adapter yêu cầu template z toàn1, policy literal True có
provenance, mode và provenance mỗi result phải khớp. Không nhận m0/2 hoặc
fractional erasure mà vẫn gọi đó là state u integer. Policy chưa chọn trong
reference config vẫn chưa được kích hoạt.

Không đặt extinction coefficient, L_th, cloud altitude/thickness, LOS sampling
hay eta_valid cho paper. Số cloud/rate trong unit tests chỉ là **arithmetic
software fixtures**, không được xuất làm research results.

Với path dài K:

\[
m_k=m_0z_{k-1,j_k},\quad u_K=\sum_{k=1}^Kz_{k-1,j_k},\quad
a_K=\sum_{k=1}^Kz_{k-1,j_k}R_{k-1,j_k},\quad
n_K=m_0u_K,\ S_K=m_0a_K.
\]

\[
\widehat L_K=\max\{0,S_K-7\sqrt{n_K\log_2(2/\epsilon)}\},\quad
P1=\max_K\widehat L_K/(K\Delta t),\quad P2=\max_K\widehat L_K.
\]

Mỗi candidate prefix chịu **một** penalty trên accumulated n_K; không cộng
penalty từng slot. P1 và P2 chọn terminal/prefix riêng, K>=1; energy và speed
constraints cùng hover self-loop giữ nguyên. m0 và epsilon mission chưa chốt;
N=1e8/key_fraction=.8 của IEEE2025 không tự thành mission input.

## 6. Dominance và thông tin truy cập

DP vẫn nhóm nhãn cùng (k,j,u), không prune giữa u khác nhau. Với hai label
cùng nhóm, e_A<=e_B và a_A>=a_B: mọi suffix feasible từ B cũng feasible từ A
vì cùng q_k/thời gian/graph và ngân sách còn lại lớn hơn. Exogenous R[slot,j]
và z[slot,j] cho cùng suffix có cùng increment của u,a; cùng u cho cùng n
và penalty. Key là hàm không giảm theo a khi n cố định, nên cùng terminal
duration không mất objective khi bỏ B. Đây là điều kiện cho **finite graph,
fixed horizon/rates, integer clear-slot accounting, additive positive edge
energy và float64 arithmetic** đang xét.

Không áp lý luận này cho arbitrary fractional m_k, history-dependent channel,
continuously optimized trajectory hoặc một security proof. Label cap vẫn
`approximate`; không cấp cap ngầm cho exact mode. Tests exhaustive kiểm
objective P1/P2, không chứng nhận tối ưu liên tục hoặc mọi tie-selected path.

DP dùng full predicted future rows. Greedy action score chỉ dùng current row;
template được sample cả horizon để chia sẻ deterministic inputs, không có nghĩa
greedy decision được dùng future. Cả bốn dùng retrospective best feasible
prefix, nên stopping không phải online guarantee. Đây **không phải benchmark
ngang quyền dự báo**; information advantage phải được công bố cùng performance.

## 7. Kiểm thử, file và bảo toàn

Baseline trước sửa: **90 passed in5.89s**. Lần chạy cuối sau review:
**112 passed in6.29s,0 failed,0 errors,0 skipped**, gồm90 test cũ và22 case
mới. Lệnh thực tế từ thư mục package:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5a_validation/tests.xml
```

Bằng chứng: [verification.json](phase5a_validation/verification.json) và
[tests.xml](phase5a_validation/tests.xml). `git diff --check` kiểm whitespace;
các file mới/untracked còn được kiểm trailing whitespace riêng vì toàn package
chưa tracked trong root Git.

[Review độc lập](phase5a_independent_review.md) không phát hiện must-fix defect;
reviewer chạy27 focused/planning tests và100 kiểm tra DP-vét cạn độc lập trong
bộ nhớ. Đây là software fixtures, không phải experimental replications hoặc
security certification. Scenario/graph/provider context phải giữ cố định trong
sampling/solving; read-only arrays không phải isolation chống callback cố ý
thay đổi context.

Tests mới gồm static vector/repeated-matrix equality cho cả bốn method,
static metric replay từ demo lịch sử, changing-slot greedy, six seeded small
graphs với exhaustive enumeration độc lập và dominance bật/tắt, accumulated
penalty/P1/P2/K, hovering/speed/energy, non-unit dt/indexes, shared snapshot,
seeded cloud drift/LOS endpoint sampling, analog no-double-erasure/fractional
counts, invalid matrix and lookup/config rejection.

Một lần full-suite sau thay solver phát hiện100 passed/8 setup errors vì test
figure dùng bundle lịch sử với hash producer cũ. Đã đổi **test fixture** sang
bundle synthetic đo thật trong tmp, không sửa bundle/manifests lịch sử và
không nới verifier. Một regression test xác nhận old metrics vẫn replay đúng
nhưng old producer bundle bị từ chối với code hiện tại. Các test xuất ảnh sẵn
có chỉ ghi tmp; không có hình mới trong `figures/`.

| File | Thay đổi |
|---|---|
| `src/uav_qkd/evaluation.py` | Validate static/dynamic rates, copy/read-only, rate_at và evaluator |
| `src/uav_qkd/dp_solver.py` | DP gọi cùng rate_at theo slot |
| `src/uav_qkd/baselines.py` | Ba baseline gọi cùng rate_at |
| `src/uav_qkd/experiments.py` | Waypoint count lấy graph thay vì len(rates) |
| `src/uav_qkd/rate_provider.py` | Mới: rate/link snapshot adapters |
| `src/uav_qkd/skr_lookup.py` | Rejection guard và selected-reference loading |
| `src/uav_qkd/config.py` | Explicit optional reference/protocol binding |
| `tests/test_time_dependent_rates.py` | Mới: focused arithmetic/compatibility regression tests |
| `tests/test_paper_figures.py` | Current-producer temporary synthetic fixture |
| `docs/phase5a_implementation_plan.md` | Phạm vi, thiết kế và thực thi |
| `docs/phase5_author_decisions_vi.md` | Những quyết định cần thiết cho base run |
| `docs/phase5a_independent_review.md` | Independent review checkpoint |
| `docs/phase5a_validation/` | Pre-edit hashes, lookup comparison, tests và verification |
| Báo cáo này | Readiness và giới hạn hiện tại |

Source hashes trong bundle cũ/Phase4 vẫn là lịch sử, không sửa để khớp code
Phase5A mới. Parent frozen-spec hash discrepancy/lifecycle hiện hữu không
được sửa hoặc dùng để mở một cổng publication mới. Không yêu cầu tác giả xác
nhận lại Z/w để sử dụng hạ tầng software này.

## 8. Catalog và điều kiện bắt đầu Phase 5B

Catalog hiện tại vẫn **1 READY,9 BLOCKED,0 EXPLORATORY**; IEEE2019 rotor
reference riêng vẫn READY. Không có figure hoặc evidence status nào được
nâng. Chỉ hạ tầng rate động được mở khóa trong Phase5A.

Phase5B cần tác giả chốt các mục trong
[phase5_author_decisions_vi.md](phase5_author_decisions_vi.md): lineage/hardware
và xử lý lookup, noise/convention, HAPxy/q0, nguyên profile rotor, Emax, graph,
prediction horizon, cloud mechanism/realization/parameters, fs/eta_valid hoặc
m0, epsilon/block interpretation, prior lambda, security claim và quyền cho
workload cụ thể. Sau đó bind provider đúng q,t và cùng context, seal inputs,
kiểm readiness/lifecycle hiện hành trước base-run validation. Chọn scenario
mới không tự cho phép regenerate2.601 điểm hay chạy publication-scale.
