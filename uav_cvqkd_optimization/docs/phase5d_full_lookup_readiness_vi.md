# Phase5D — full-lookup readiness và benchmark thực tế

**Đã đo50 spatial points, mỗi điểm đủ212 candidates, chạy serial và2 process:
tổng100 point passes/21.200 native evaluations.** Không full regeneration,
paper-mode hoặc thay candidate policy. Các tham số vẫn Dr=.30m, full divergence
35µrad, pointing jitter1.561µrad, position SD.10m, xi_det=.005 và xi_ch=.0136SNU.

Artifacts:
[benchmark summary](../results/phase5d_benchmark_20261108/summary.json),
[input manifest](../results/phase5d_benchmark_20261108/input_manifest.json),
[output seal](../results/phase5d_benchmark_20261108/output_manifest.json),
[validation bổ sung](phase5d_validation/benchmark_validation.json).

## 1. Giải thích hai ETA khác nhau

Phép tính trong yêu cầu là đúng cho **chạy độc lập từng spatial point**:

| Workload | Số calls |
|---|---:|
| 2601 points ×212 candidates | 551.412 |
| 294 exact radial geometries ×212 candidates | 62.328 |
| Thành phần MB của radial mode:294×179 | 52.626 |

Pilot38.0597s/2120calls cho55.703calls/s;551.412calls/tốc độ này xấp xỉ
**165 phút**. ETA Phase5C12.5–18.2 phút dùng **294 geometry groups** và các
timing context/catalog warm/cold theo point, không phải551.412calls. Tỷ lệ
giảm workload là2601/294≈8.847; thêm khác biệt startup/cache/instrumentation
làm throughput không đồng nhất. Báo cáo Phase5C chưa nhấn đủ rõ hai workload;
không được hiểu12.5–18.2 phút là runtime đã đo cho2601 full independent searches.

Radial reuse là lựa chọn riêng: native channel hiện tại phụ thuộc zenith/radius²,
rho_x=rho_y=0 và context đối xứng. Mọi geometry vẫn tìm đủ212 candidates.
Nếu geometry/pointing/azimuth model đổi, không mặc định gộp bằng radius². Không
nhầm325 contexts của map+các góc zenith sweep với294 geometries riêng của map.

## 2. Benchmark và tài nguyên quan sát được

50 geometry được chọn deterministically theo quantile của294 radius² groups,
bao phủ center đến farthest grid point; không nội suy rate, không lấy cached
pilot SKR và không chọn theo winner. Native producer/context/noise convention
giữ nguyên như Phase5C. Cả hai pass dùng cùng ordered catalog179MB/33Uniform.

Physical context được tạo mới bằng original validated protocol; active
effective-noise protocol riêng dùng.0136 trong nguyên native evaluator với
m1,mh,M0 không phụ thuộc noise. Không lấy các field noise lịch sử trong context
làm target noise hoặc monkey-patch validator hard-code.0186 của producer cũ.

| Measurement | Serial | 2 processes |
|---|---:|---:|
| Evaluations | 10.600 | 10.600 |
| Stage wall-clock | 217.2846s | 137.3368s |
| Evaluations/s | 48.78395 | 77.18250 |
| Sampled aggregate RSS peak | 527.35MiB | 1566.02MiB |
| Sampled process-tree CPU time | 176.4375s | 188.8281s |
| CPU%, một logical core=100% | 81.20% | 137.49% |
| CPU%, chia16 logical CPUs | 5.08% | 8.59% |
| Point wall min/median/max | 2.5771/3.9417/9.6189s | 4.2383/4.6719/7.8200s |
| Point wall mean/sample SD | 4.2940/.9688s | 4.9104/.7290s |

Speedup **đo được1.5821×** cho hai stage walls; không giả định2×. Parent
native initialization22.9661s (resource wall22.9912s) được đo riêng trước
serial stage. Hai worker initialization12.0521 và12.1487s nằm trong parallel
stage; interpreter/process bootstrap còn có overhead riêng. Nếu cộng parent
init vào serial thì tỷ số khác1.7495×, không trộn với stage speedup1.5821×.
Tổng benchmark elapsed382.5906s bao gồm preflight/init/cả hai pass/sealing.

Torch native thread setting quan sát là10/producer,16 logical CPUs; các biến
OMP/MKL/OpenBLAS/NumExpr không được task này tự đặt. Không có vectorized
producer rewrite được đo: giữ native NumPy/GH pipeline và đo process-level
parallelism. Không khẳng định thêm tốc độ của một phiên bản vectorized mới.

Mỗi mode được đo một lần trên50 điểm; SD trong bảng là biến thiên theo
spatial point, không phải variance của các lần benchmark lặp. Parallel làm
hai point đồng thời nên tổng stage nhanh hơn dù mean wall của một point tăng.
Không suy statistical runtime superiority hoặc tốc độ trên host khác từ lần đo này.

RSS là tổng sampled parent+children, parent vẫn giữ serial engine khi chạy
parallel, shared pages có thể bị đếm nhiều lần. Sampler nghỉ50ms giữa lần lấy
mẫu cộng chi phí collection; đây **không phải peak liên tục chính xác** hoặc
RAM vật lý không trùng lặp. CPU là delta/lifetime maxima sampled theo process,
có thể bỏ sót phần cleanup rất ngắn. Stage timing gồm monitoring và checkpoint
I/O. Không quy toàn bộ chênh lệch với pilot cho một nguyên nhân chưa được cô lập.

## 3. ETA cập nhật, giữ full search và nhu cầu tăng tốc

Ngoại suy tuyến tính từ throughput của từng stage vừa đo:

| Workload | Serial | 2 processes |
|---|---:|---:|
| 551.412 calls, per-point | **188.39 phút** | **119.07 phút** |
| 62.328 calls, radial_exact | **21.29 phút** | **13.46 phút** |

Serial table chưa cộng one-off parent init≈23s. Parallel stage đã chứa worker
startup; một lệnh mới còn parent preparation/init. Vì vậy đây là planning
estimates theo mode và host này, không phải full-run measurement, confidence
interval hoặc cam kết runtime. Full-run cache/I/O/tải host/phân bố geometry
có thể khác. Dùng số mới thay ETA pilot khi xin phép chạy.

Có thể **giữ full212-candidate search**. Hai-process execution có speedup đã
đo nhưng tốn RSS cao hơn; không cần giảm candidate pool để dùng kết quả đo này.
Ưu tiên lựa chọn workload minh bạch trước khi cân nhắc rewrite producer.
Radial_exact và2process chỉ là config thay thế được phê duyệt riêng, không
âm thầm thay baseline per-point/serial.

Ở50 điểm benchmark, MB winner vẫn VA=1.358333319784304,nu_raw=.3, nhưng điều
này **không cho phép cố định winner** cho244 geometry chưa đo. Mọi record
đều có đủ212 candidates. Không có accelerated/pruned search hoặc quality
claim dựa trên việc bỏ bớt candidates. Serial/parallel scientific rows và
winner identities khớp binary64; chỉ runtime telemetry khác. Native GH64/128
và80/110-digit guards giữ nguyên, không có numerical exception trong benchmark.

## 4. Full executor đã chuẩn bị, chưa được chạy

Hai config mới có hash riêng:

- [Per-point/serial reference](../configs/lookup/phase5d_full_target_per_point.json):
  `8498840e9f102231e8efce54cf61fe0431ee68fe04a97972024402def87fb1e9`.
- [Radial_exact/2-process alternative](../configs/lookup/phase5d_full_target_radial_2proc.json):
  `0671e70ef5a5a78afed6f750859161439153f2030fe6e6b733a216f1f6616111`.

Config bind target noise, ordered pool hash, original protocol/geometry/optimized
setup hashes, workers/mode và tolerances. Không có approval file được tạo bởi
task này. `full` yêu cầu file xác nhận riêng: scope=`PHASE5D_FULL_LOOKUP`,
author_approved là booleanTrue, đúng config_sha256 và candidate_pool_sha256.
File đó phải xuất phát từ quyết định tác giả mới; test fixtures không phải quyền.

**Lệnh chuẩn bị dưới đây chưa chạy**; approval path là input còn thiếu:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -B -m uav_qkd.lookup_benchmark full `
  --config configs/lookup/phase5d_full_target_per_point.json `
  --output results/phase5d_full_target_per_point_APPROVED_NEW `
  --approval-file docs/approvals/phase5d_full_lookup_author_approval.json
```

Resume dùng cùng config/approval/output và thêm `--resume`. Nếu chọn alternative,
phải dùng config/hash/approval/output khác tương ứng; không tái dùng approval của
per-point config. Namespace phải mới, thuộc results/phase5d_ của package;
completed sealed output bất biến, không ghi đè lịch sử.

Executor chuẩn bị có deterministic input order, đầy đủ record/candidates/argmax
cho mỗi evaluated point/group, atomic checkpoint rồi seal. Khi resume: kiểm
config/input/stage/noise/geometry, ordered roster, scalar identities, đủ hai
families và evidence/security flags; archive partial riêng, validate complete
JSON trước khi phục hồi missing seal. CSV/NPZ export có thể tiếp tục sau
interruption, chỉ reuse byte/array-identical files và không overwrite mismatch.

CSV giữ signed raw MB trong `skr_bits_per_use` tương thích `SKRLookup.load`,
và riêng `K_raw_bits_per_use`, `K_potential_bits_per_use`. NPZ giữ points/rates,
units/noise, config/input/pool/producer hashes và independent family evidence
arrays, không pickle. Full-grid map về đúng2601 coordinates; no extrapolation,
no candidate pruning. Loader numeric PASS không tự cấp full scientific admission.

## 5. Finite-size, cloud và paper decisions

Chi tiết:
[phase5d_finite_size_feasibility_vi.md](phase5d_finite_size_feasibility_vi.md).
Với epsilon3e-8, constant pilot r và số **valid** signals n:

`n>49*log2(2/epsilon)/r^2`.

Target cần khoảng **51.864–53.186 triệu** valid signals; historical cần
**2.010–2.282 tỷ**, tại đúng5 rates đã phân tích. Ở reference n=8e7, target
proxy≈72.277–77.236bits, historical=0. Đây là block reference/sensitivity,
không phải mission n hoặc key_fraction được phê duyệt.

Không chọn f_s. Giữ `n=f_s*eta_valid*c*K*delta_t`, c là clear fraction;
không nhân cloud lần nữa khi n đã valid. Clear LOS giữ clear-channel rate/m0,
blocked LOS choT=0,raw contribution=0,m=0 qua LOS/slab model hiện có. Không
test riêng endpoint UAV thay cho path, không CLWC→extinction tự đặt.
`binary_los_blockage` vẫn candidate; không có cloud/finite-size trong SKR benchmark.

Còn thiếu cho base mission/paper: cloud mode/L_th/layer/thickness/realization/
seed/LOS resolution approval; HAPxy/q0; nguyên rotor profile/Emax/graph/horizon;
f_s/eta_valid/m0; epsilon/block interpretation/prior lambda; exact lookup
geometry/protocol admission, claim scope và quyền/lifecycle phù hợp. Target
noise.0136 đã xác nhận. `INSUFFICIENT_EVIDENCE`, `paper_admissible=false` và
finite-size proxy limitations giữ nguyên; positive proxy không phải composable
security proof. Frozen-spec discrepancy/NOT_READY không bị đổi thành publication
authorization qua một benchmark hoặc full-run approval file.

## 6. Review, tests và bảo toàn

[Review độc lập](phase5d_independent_review.md) kiểm204 output hashes,552 inputs,
60 producers,100 checkpoint seals và21.200 records thực. Bốn finding liên quan
future executor đã được pin RED→GREEN: interruption/resume, CSV loader schema,
checkpoint family/evidence flags và NPZ provenance. Tests chỉ mô phỏng controller/
export dưới tmp với backend bị mock, không có scientific full regeneration.
Finite-size generator cũng được sửa guard refuse nonempty output trước ghi.

Suite cuối: **167 passed in11.87s,0 failed,0 errors,0 skipped**, gồm135 case
có sẵn và32 case mới. Lệnh từ package:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5d_validation/tests.xml
```

Benchmark giữ nguyên bytes và archived executed producer; current source có
guard/schema fixes sau phép đo. Validation ghi tách hai hashes, không thay
manifest cũ để giả rằng revision sau đã được benchmark. Finite-size development
checkpoint cũng được giữ với archived producer, artifact cuối nằm ở namespace
`phase5d_finite_size_20261108_verified`.

File mới: `lookup_benchmark.py`, `finite_size_feasibility.py`, hai test files,
hai full config, hai báo cáo, plan/review/validation và benchmark/sensitivity
artifacts. Không sửa existing scientific sources, Z/w, MB/Holevo, rotor,
`paper.yaml`, lookup hay pilot. Catalog vẫn1 READY/9 BLOCKED; IEEE rotor riêng
vẫn READY. Kết quả suite cuối và preservation trong
[verification.json](phase5d_validation/verification.json).

Readiness: đã có benchmark/sensitivity và software guards để tác giả cân nhắc
phê duyệt một full numerical regeneration theo **config/mode cụ thể**. Full
regeneration và paper-mode vẫn NOT_RUN. Không commit/push.
