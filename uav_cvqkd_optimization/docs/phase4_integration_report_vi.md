# Báo cáo triển khai Phase 4

## 1. Kết quả và phạm vi đã thực hiện

Đã triển khai code và config riêng, không chỉ lập kế hoạch:

- Source-A HAP–UAV reference đúng các giá trị Section IV/PDF p3 của bản thảo.
- Hình học tổng quát theo tọa độ, tách reference30° độc lập; dùng lại pure
  `LinkGeometry` và `atmospheric_transmittance_from_tau_zen` hiện có.
- Adapter physical-context → existing Eq18–20 moment-provider → effective
  scalar channel → existing MB evaluator. Các callback backend phải được bind
  rõ, không tự chọn một model historical khác để lấp chỗ trống.
- Cloud coupling tách binary erasure và optical attenuation, có approval và
  provenance, không CLWC→extinction guessing, không tính trùng cùng cơ chế.
- Finite-size reference của IEEE2025, valid-signal helper và accumulated
  `finite_size_aware_key_yield_proxy`, dùng lại evaluator đã có.
- Audit CLI, compatibility JSON, matrix tham số và integration tests.

Chưa có HAP horizontal coordinates, scenario và các input cần thiết để tạo
paper trajectory. **Không chạy paper-mode, không tạo hình mới, không chuyển
BLOCKED→READY**. Các numerical reference được ghi trong JSON, không gọi là
mission outputs.

## 2. Quyết định tác giả về Z và w được giữ nguyên

**Tác giả xác nhận code hiện tại đúng.** Phase4 không xem xét lại tính đúng đắn
toán học, không viết lại công thức, không đổi source QAM/MB, annihilation/
creation operators, covariance hoặc cách tính matrix/Holevo. Không dùng nghi
vấn Z/w làm lý do dừng triển khai.

`bind_existing_mb_backend` chỉ kiểm scalar contract: source VA, Vmod mapping,
beta, eta_f, xi_f và output scalar tương ứng; nó gọi nguyên signature
`evaluate(source,context,protocol)` của backend được caller bind. Payload
source gồm C,w, operators/matrices là **opaque và không bị adapter sửa**.
Các native guards sẵn có của backend không bị xóa hay bypass.

Test I/O dùng recording callback hoặc replay một response receiver30 đã lưu
trong chính context của nó. Không tính lại Z/w để so với một implementation
mới, không chạy source job, không tạo bảng SKR hay key outcomes giả.
`reference_audit_verified/reference_audit.json` ghi core evaluations=0, closed-form
channel evaluations=0 cho audit CLI; helper geometry/atmospheric-loss được gọi
thật để tính reference hình học.

## 3. Source A: channel và geometry

Config mới:
[configs/channel/hap_uav_mb_reference.yaml](../configs/channel/hap_uav_mb_reference.yaml).
Đây là reference, không phải mission config. Source là bản thảo tác giả, không
được tự gọi là published/peer-reviewed paper. Không lấy receiver30 hardware
overrides làm các giá trị Section IV.

Các trường đã đưa vào SI gồm: HAP20000m, UAV1000m, reference zenith30°,
full divergence233µrad, wavelength1550nm, F0=infinity, transmitter jitter15.61µrad,
aperture diameter.08m, boresight(0,0)m, position SD1m, angular SD1.5mrad,
FOV half-angle6.25mrad, atmospheric altitude20000m, tau_zen.92, ground
Cn²=1e-14m^(-2/3), RMS wind21m/s và beta=.95.

`hap_horizontal_m`/q0 và noise values chưa được Section IV cung cấp giữ null.
Không tự đặt tọa độ ngang từ reference30° hoặc từ hình chiếu lookup cũ.

`waypoint_geometry` nhận HAPxyz và UAVxy/altitude rõ ràng, tính zenith từ tọa
độ rồi dùng helper cũ để lấy slant distance và atmospheric transmission.
Kết quả giữ altitude/tau và horizontal positions để tránh mix geometry/config.
`ExistingMomentProvider` từ chối khác altitude/tau/HAP position đã khai báo,
forward đúng coordinate-derived angle và không đưa reference30° vào request
waypoint như một giá trị thay thế. Nó gọi physical/moment functions đã bind,
không sao chép closed-form engine.

Reference độc lập đã tính:

| Đại lượng | Kết quả | Scope |
|---|---:|---|
| L_reference | 21939.310229205777m | delta_h=19000m, zeta30° |
| zeta_reference | .5235987755982988rad | Reference angle, không phải trajectory |
| eta_atm_reference | .9082089654181442 | .92^sec(30°) |
| HAP/UAV horizontal | null /null | Không suy tọa độ từ L/zeta |

Effective boundary giữ eta_f=mh² và output excess noise=(m1-mh²)*Vmod+E[eta*xi].
Phân biệt power eta_f với amplitude gain mh, và giữ module convention
`VA=Vmod=2*nbar` đã được ghi trước đó. Printed nbar/2 được lưu riêng; không
sửa source amplitudes/nbar/VA để ép hai dòng giống nhau. Scalar domain checks
là kiểm I/O, không phải review core Z/w. Chỉ xử lý âm variance ở mức machine
roundoff với cờ riêng; eta_f luôn vẫn là mh², không thay bằng m1.

## 4. Source B: finite-size reference đã kiểm nguồn

Đã tìm/đọc PDF local:
`C:/Users/admin/Downloads/2025.Finite-Size_and_Modulation_Opt_in_CV-QKD_Over_UAV-FSO_AO.pdf`.
DOI10.1109/LCOMM.2025.3624071; 5 trang. Table I journal3036/PDF4 đã render và
kiểm trực quan; Eqs19–21 ở journal3035/PDF3. Các bản local có cùng nội dung
được nhận diện qua hash, không chọn ngẫu nhiên một revision khác.

Config:
[configs/finite_size/ieee_2025_reference.yaml](../configs/finite_size/ieee_2025_reference.yaml).

| Đại lượng | Giá trị | Phân loại |
|---|---:|---|
| N_block | 1e8 | Source-reported standalone block |
| n_block/N_block | .8 | Source-reported key-generation fraction |
| epsilon_PE,EC,PA | 1e-8 mỗi thành phần | Source-reported |
| epsilon_reference | 3e-8 | Derived sum; binary64 lưu3.0000000000000004e-8 |
| n_block_reference | 8e7 | Derived N*key_fraction |
| Delta reference | .003989881969840257 bits/valid signal | Derived using existing penalty evaluator |

Không dùng key_fraction làm eta_valid, không suy fs hoặc mission m0 từ N,
không áp N=1e8 mặc định cho mọi trajectory. Delta helper dùng lại `finite_key`
như phép tính **một block toán học**, không gán m0 trong `paper.yaml`.

Không nhập effective transmittance E[T], GMCS MI/Holevo formulas, SNR-dependent
beta, AO, RF/ground-UAV parameters hay attenuation law của B vào Source A.
Mục tiêu mới được ghi tên `finite_size_aware_key_yield_proxy`; nó không được
quảng bá là composable-security proof cho MB/HAP–UAV fading.

## 5. Cloud hiện tại và hai mode mới

Mô hình cũ `CloudField` là tổng Gaussian dịch liên tục; `BlockageModel` là
threshold deterministic trên các sample của optical-path/slab intersection.
b(q,t) là **binary link-blockage indicator** trong realization đã cho, không
phải xác suất, không phải hệ số Beer-Lambert hoặc tỷ lệ retention tự nhiên.
Legacy graph dùng z=1-b và m=m0*z: đó là **complete-blockage erasure**.

| Mode interface | Channel/SKR | Valid signals | Điều kiện |
|---|---|---|---|
| binary_erasure, blocked | Không gọi channel/SKR backend; metadata T=0, contribution0 | 0 | Existing LOS threshold effect + explicit approved policy |
| binary_erasure, clear | Existing clear-sky moment/SKR provider | m0 | Không thêm analog attenuation cho cùng cloud |
| optical_attenuation | Explicit post-attenuation moment/noise provider rồi SKR backend tương ứng | m0 không bị erase thêm | Sourced dimensionless factor trong(0,1], provenance và author approval |

Việc đặt T=0 làm metadata outage ở mode binary không phải một lần tính SKR
với kênh đã suy hao rồi lại loại tín hiệu: backend đã được skip. Với analog,
không tự scale noise hoặc rate vì detector/input-noise convention có thể khác;
caller phải cung cấp post-loss moments và bind backend vào context post-loss
tương ứng. Không giữ native clear-sky context rồi giả nó là attenuated context.
Opacity hoàn toàn factor0 không được âm thầm diễn giải thành analog mode giữ
signals; phải dùng policy erasure đã được định nghĩa/phê duyệt cho trường hợp đó.

`CloudPolicy` cần boolean True thật và provenance; string hoặc giá trị thiếu
không kích hoạt mode. Config reference mới để mode=null, author_approved=false,
vì Phase4 không nhận một lựa chọn cloud scenario mới. Không đổi model/seed/
realization demo hoặc figure, không đặt extinction/optical-depth/CLWC conversion.
Moment provider ở binary mode phải là clear-sky baseline; eta_valid/m0 cũng
phải được định nghĩa không chứa lại cùng cloud loss trước khi nhân z.

**Giới hạn interface thật:** solver graph hiện có rate tĩnh r[j] và binary
z[k,j]. Nó hỗ trợ cơ chế binary hiện tại; attenuation thay đổi theo thời gian
có thể cần r[k,j] và một task integration/author decision riêng. Interface mới
trả link-slot state nhưng không âm thầm đổi class Scenario hay code DP để
masquerade analog attenuation bằng erasure. Đây không phải vấn đề Z/w.

## 6. Rotor, năng lượng và thuật toán vẫn được bảo toàn

Hai file `configs/rotor/ieee_2019.yaml`, `arxiv_2018_v1.yaml` và các output
rotor giữ nguyên. Không đổi default arXiv trong `paper.yaml`, không trộn
vmax30 IEEE vào coefficients arXiv/vmax60, không chọn Emax/q0/graph/horizon/
lambda mới. Mô hình power, lower convex envelope, edge feasibility, hover
cost, energy accumulation và variable stopping của các solver cũ không đổi.

Bốn method vẫn dùng cùng Scenario và evaluator: Stationary, SKR-Greedy,
Energy-Aware Greedy, Pareto DP. P1 key/(K*dt), P2 total key chọn stopping
time riêng. DP full predicted cloud horizon khác greedy current-slot actions;
mọi method chọn prefix hồi cứu. Không tự gọi kết quả đó là online guarantee.

## 7. Lookup2.601 điểm

Đã có [báo cáo tương thích](skr_lookup_integration_compatibility_vi.md), không
tái sinh bảng. Cấu hình mới khác4 field vật lý của receiver30: aperture,
divergence, transmitter jitter, position SD. Beta và convention metadata khớp
không xóa được các khác biệt này. New reference noises vẫn null; không nhập
.0186/.005 vào nó như thể Section IV đã cho đủ.

Giữ nguyên CSV/NPZ, labels `INSUFFICIENT_EVIDENCE`, paper_admissible=false,
finite-catalog scope và raw/potential columns. Chỉ kiểm scalar/data forwarding
ở test replay, không tái kiểm Z/w của bảng để chặn integration.

## 8. File mới và cách chạy phần đã đủ input

| File | Mục đích |
|---|---|
| `configs/channel/hap_uav_mb_reference.yaml` | Source-A SI parameters và explicit missing values |
| `configs/finite_size/ieee_2025_reference.yaml` | Source-B finite reference, không default mission |
| `src/uav_qkd/hap_uav_channel.py` | Generic geometry, typed moments/effective state, existing-provider/backend adapters |
| `src/uav_qkd/finite_size_reference.py` | Reference derivation, Delta, signal-rate helper, accumulated proxy |
| `src/uav_qkd/cloud_channel.py` | Approved exclusive cloud policies và link-slot coupling |
| `src/uav_qkd/phase4_audit.py` | Config/interface/compatibility audit CLI, không paper runner |
| `tests/test_phase4_integration.py` | 20 integration/domain/regression cases |
| `docs/integrated_three_paper_parameter_matrix_vi.md` | Matrix nguồn, đơn vị, role/status và missing decisions |
| `docs/skr_lookup_integration_compatibility_vi.md` | Compatibility scope, physics differences, actual interface limitation |
| `docs/phase4_interface_independent_review.md` | Independent review checkpoint; không review Z/w toán học |
| `docs/phase4_validation/` | Source hashes/rendered evidence, test XML, audit JSON, final verification |
| `docs/phase4_implementation_plan.md` và báo cáo này | Phạm vi/ghi nhận triển khai |

Từ `uav_cvqkd_optimization/`:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -m pytest -q
python -X utf8 -m uav_qkd.phase4_audit --output docs/phase4_validation/reference_audit_reproduction
```

Lệnh thực tế đã chạy dùng output
`docs/phase4_validation/reference_audit_verified`. Export/audit chọn một thư mục
mới, không ghi đè. JSON:
[reference_audit.json](phase4_validation/reference_audit_verified/reference_audit.json).

Hai thư mục `reference_audit` và `reference_audit_final` giữ các checkpoint trước
đó; không dùng hash producer của chúng để đại diện code sau cùng.

Provider APIs nhận callable existing backend rõ ràng. Chúng không tự import
và kích hoạt một evaluator historical có noise law khác. Chưa bind một
physical/SKR instance paper khi geometry/noise/approval còn thiếu; không có
rate hoặc outcome giả thay thế. Các exact analytic unit cases, recording test
doubles và stored-response replay chỉ kiểm contracts, không phải experiments.

## 9. Kiểm thử thực tế và review

Baseline trước thay đổi: **70 passed in 5.38s**. Sau code/regressions:
**90 passed in 6.53s**, gồm70 cũ +20 mới, exit0:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase4_validation/tests.xml
```

Các case gồm SI/degree/radian, coordinate/reference geometry, missing HAP,
finite reference, không suy fs/m0, moment square vs mean, scalar/noise domains,
native source/consumer forwarding, blocked LOS không endpoint, skipped backend,
approved attenuation không double erasure, actual saved-response replay,
geometry/config mismatch, retained-mass domains, incomplete compatibility
classification, arithmetic overflow, exact normalization clause và overwrite protection.

Review độc lập phát hiện3 boundary issues: geometry trộn altitude/config,
scalar moments không hợp lệ lọt guard, và physical subset bị gọi full
compatibility. Các issue đã được tái hiện bằng test thất bại rồi sửa trong
**module interface mới**, không sửa core. Bổ sung giữ tọa độ thực trong request
để không forward null thay một HAP position caller đã cung cấp. Không có
finding quan trọng còn mở. Tất cả test toán học Z/w/matrix vẫn ngoài scope;
không thêm bất kỳ test toán học mới nào cho chúng.

Bản ghi [verification.json](phase4_validation/verification.json) đối chiếu hash
input/producer của audit cuối, nguồn PDF, `paper.yaml`, các input/output rotor
và artifacts có hash lịch sử được tham chiếu. Phạm vi kiểm tra bảo toàn được
ghi rõ trong JSON; không coi file không có snapshot/hash đối chứng là đã được
kiểm chứng byte-for-byte. Parent research source không có Git diff. Các file
Phase4 được liệt kê cùng SHA-256 trong bản ghi này.

## 10. Việc còn chờ và figures

Vẫn cần tác giả cung cấp/chọn: HAP horizontal coordinates, q0, Emax, graph,
prediction horizon, fs/eta_valid hoặc m0, mission epsilon/block interpretation,
Source-A noise inputs/backend convention đủ, cloud attenuation/erasure mode
và source/approval, layer/thickness/Lth/LOS resolution hoặc sourced attenuation
model, lambda và security-claim scope.

Không tự dùng epsilon3e-8 và key_fraction.8 làm mission defaults. Reference
geometry và finite penalty đã tính được ngay, không cần invent các input khác;
nhưng không đủ để xuất trajectory, C07 accumulated mission keys hay các hình
so sánh paper. Catalog vẫn1 READY/9 BLOCKED, IEEE rotor riêng vẫn READY;
không auto-promote hình nào. Có thể chuẩn bị một task figure reference riêng
nếu tác giả muốn, không dùng nó thay cho paper-result figures đang thiếu.

Lịch sử frozen-spec hash discrepancy và lifecycle hiện hữu được giữ nguyên,
không sửa/khôi phục file và không dùng chúng như lý do dừng các safe interfaces
đã triển khai. Không công bố paper readiness mới từ một lượt test phần mềm.
Không thay đổi dữ liệu lịch sử, không commit/push, không Deep Research.
