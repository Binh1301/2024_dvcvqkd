# Bảng quyết định tham số dành cho tác giả — Phase 2

## Phạm vi và trạng thái kiểm toán

Đối chiếu trực tiếp cấu hình, catalog/manifest, source code và dữ liệu đã lưu.
Không đổi default, giá trị null, nguồn rotor, trạng thái source evidence hay
paper-mode. Không đưa ra một bộ số đề xuất để tự chạy kịch bản.

- Catalog `figures/paper/status.json`: **1 READY, 9 BLOCKED**; paper-mode `NOT_RUN`.
- Ngoài catalog có thêm rotor IEEE2019 Figure02 `READY`, đã kiểm lại hash nguồn,
  profile và các output. Như vậy có **2 artifact mô hình đã xuất**, không phải
  hai kết quả mission paper. Figure02 rotor không thay Figure02 cloud.
- Các manifest catalog còn gắn hash cũ của `parameter_provenance.md`. Snapshot
  cũ tại `docs/ieee_2019_rotor_verification/parameter_provenance_before.md` khớp
  hash đó. Đây là provenance lịch sử, không phải hash live của tài liệu đã bổ
  sung IEEE. Không ghi đè/đổi nhãn manifest cũ để che khác biệt.
- Chạy lại suite hiện có: **70 passed in 16.12s**, `python -X utf8 -m pytest -q`.
  PASS phần mềm không nâng source/security/publication readiness.

## Cách đọc bảng

Giữ đúng các nhãn yêu cầu:

- `SOURCE_VERIFIED`: đã có căn cứ và vị trí nguồn, hoặc implementation được
  kiểm tra trực tiếp nếu Source ghi rõ là code. Không có nghĩa mọi giả định
  vật lý/bảo mật của hệ thống đã được chứng nhận.
- `DERIVED`: công thức/kết quả dẫn xuất đã xác định. Nếu Current value ghi
  **chưa tính**, chưa có giá trị số paper; không được điền từ demo.
- `AUTHOR_DECISION_REQUIRED`: cần tác giả chốt scenario, protocol hoặc phạm vi
  claim; chưa có một lựa chọn mới nào được áp dụng trong Phase2.
- `MISSING_SOURCE`: thiếu giá trị/bằng chứng dùng cho paper trong các file đã
  kiểm. Không khẳng định không tồn tại trong tài liệu khác chưa cung cấp.
- `NOT_APPLICABLE`: không thuộc mô hình hiện tại hoặc không có hiệu lực trong
  mode đang xét; không dùng nhãn này để bỏ qua một tham số thực sự cần.

`C01..C10` là ID ổn định của catalog hiện tại; `R02-IEEE` là Figure02 rotor ở
thư mục riêng. Số hình manuscript cuối cùng chưa được chọn khi hai mục cùng
mang số02; xem [kế hoạch thực thi](next_figure_execution_plan_vi.md).

Priority: **P0** nguồn/phạm vi và các cổng chung; **P1** quyết định input nhiệm
vụ, có thể thu thập song song P0; **P2** tạo/kiểm gói kết quả sau khi đủ điều
kiện; **P3** sensitivity và benchmark mở rộng sau base-run validation.

### Mã nguồn tham chiếu trong bảng

| Mã | File và phạm vi |
|---|---|
| P | [configs/paper.yaml](../configs/paper.yaml), cấu hình paper đang thiếu input |
| Q | [execution_physical_protocol.json](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json), context receiver30 |
| QDATA | [skr_map.csv](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/skr_map.csv), [source_pool.csv](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/source_pool.csv), native computed data |
| QPROD | [run.py](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/run.py), [report_vi.md](../../paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/report_vi.md), producer/recorded run; chỉ đọc, không thực thi trong audit này |
| QAUD | [skr_lookup_audit.json](../results/paper_configuration_audit_20261107/skr_lookup_audit.json), source-evidence limitations |
| A5 | [audit_summary.json](../results/paper_configuration_audit_20261107/audit_summary.json), trạng thái paper NOT_RUN và các đầu vào còn thiếu |
| PROV | [parameter_provenance.md](parameter_provenance.md), nguồn và đơn vị; [paper_configuration_audit_vi.md](paper_configuration_audit_vi.md), scope/phiên bản |
| C | [cloud_field_data.npz](../../dynamic_gaussian_cloud_figure/cloud_field_data.npz), [create_figure.py](../../dynamic_gaussian_cloud_figure/create_figure.py), mây minh họa đã tính |
| DEMO | [configs/demo.yaml](../configs/demo.yaml), [results/final_demo_20261107/results.json](../results/final_demo_20261107/results.json), chỉ tổng hợp |
| I19 | [configs/rotor/ieee_2019.yaml](../configs/rotor/ieee_2019.yaml), DOI10.1109/TWC.2019.2902559; [source_identity.json](ieee_2019_rotor_verification/source_identity.json) |
| A18 | [configs/rotor/arxiv_2018_v1.yaml](../configs/rotor/arxiv_2018_v1.yaml), arXiv1804.02238v1; bộ hiện đang dùng trong P |
| CODE | [src/uav_qkd/](../src/uav_qkd), chỉ xác nhận implementation và hợp đồng dữ liệu |

## 1. CV-QKD / SKR lookup

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| Lookup numeric data | 2.601 node; 51×51; x/y0..2000 | m; bits/use | QDATA, QAUD | CSV native fields, NPZ meshes | DERIVED | Có dữ liệu số, không tái tạo từ hình; chỉ dùng khi admissibility được xử lý | C03–C10; toàn bộ qua gate chung | P0 |
| MB lookup evidence | INSUFFICIENT_EVIDENCE ở cả2.601 điểm | status | QDATA, QAUD | MB_source_evidence_class; paper_admissible=false | MISSING_SOURCE | Bổ sung bằng chứng nguồn phù hợp và review; không đổi nhãn bằng tay | C02–C10 qua gate | P0 |
| Continuous/global modulation optimum | Chưa được chứng nhận | claim | Q, QPROD | source_domain, select_family, source pool | MISSING_SOURCE | Giữ claim finite-catalog; claim liên tục cần scope/công việc được cho phép riêng | C03–C10 | P0 |
| Catalog roster | 212: 33Uniform,179MB | candidates | QDATA | source_pool.csv.family | DERIVED | Giữ roster và source hashes; không hiểu outer bounds là phủ liên tục | C03–C10 | P0 |
| VA catalog domain | [0.05,10] | SNU, theo convention producer | Q | source_domain.VA | SOURCE_VERIFIED | Đây là domain thí nghiệm, không tự trở thành giới hạn vật lý phổ quát | C03–C10 | P0 |
| nu_raw catalog domain / mapping | [0,0.4]; nu_repo=42.5*nu_raw | dimensionless | Q | source_domain, nu_mapping | SOURCE_VERIFIED | Không trộn hai convention hoặc thay domain giữa các method | C03–C10 | P0 |
| beta | 0.95 | dimensionless | Q, PROV | beta; bản quang Section IV | SOURCE_VERIFIED | Giữ vai trò reconciliation efficiency; không dùng như detector efficiency | C03–C10 | P0 |
| h_HAP / h_UAV trong lookup | 20000 /1000 | m | Q | physical.h_hap_km / h_uav_km | SOURCE_VERIFIED | Mission dùng lookup này phải khớp geometry/model | C03–C10 | P0 |
| Aperture diameter | 0.30 | m | Q | physical.Dr_m | SOURCE_VERIFIED | Repo override receiver30; không gọi đây là mặc định .08 m của bản quang cũ | C03–C10 | P0 |
| Beam divergence | 35e-6, full-angle | rad | Q | physical.divergence_full_urad | SOURCE_VERIFIED | Giữ full-angle; không đổi sang half-angle mà giữ số | C03–C10 | P0 |
| Pointing jitter | 1.561e-6 mỗi trục | rad | Q | physical.jitter_urad | SOURCE_VERIFIED | Giữ convention/producer tương ứng | C03–C10 | P0 |
| Position jitter sigma_h | 0.10 mỗi trục | m | Q | physical.sigma_h_m | SOURCE_VERIFIED | Không trộn sigma của bản quang cũ hoặc mô hình khác | C03–C10 | P0 |
| xi_ch / xi_det | .0186 /.005 | SNU | Q | xi_ch, xi_det | SOURCE_VERIFIED | Bind đúng noise convention; xi_det không tự là electronic noise | C03–C10 | P0 |
| Measurement / reconciliation | homodyne_1D_Gaussian_effective / reverse_asymptotic | model | Q | measurement, reconciliation | SOURCE_VERIFIED | Giữ lineage và các giới hạn Gaussian-effective/DM source, không gán security proof mới | C03–C10 | P0 |
| Optical loss / correlation | original Eq10 retained[0,1]; direct Eq14 | model | Q | channel_law, correlation_policy | SOURCE_VERIFIED | Bảo toàn convention và kiểm chứng source/numerical liên quan; không âm thầm normalize/thay law | C03–C10 | P0 |
| VA normalization | VA=Vmod=2*nbar trong producer; bản in có nbar/2 | convention | Q, PROV | source_normalization, printed_normalization, author mapping | SOURCE_VERIFIED | Giữ binding của convention đã ghi; thay đổi cần review mô hình được cho phép | C03–C10 | P0 |
| Detector efficiency / separate electronic noise | null; chưa xác định riêng | dimensionless / SNU | P, PROV | verified_context.optical_repository_context | MISSING_SOURCE | Làm rõ có được mô hình hóa riêng hay không; không điền .95 hoặc .005 theo suy đoán | C03–C10 nếu thuộc model được chọn | P0 |
| Raw vs potential rate | Có cả hai cột; MB raw hiện dương | bits/use | QDATA | K_raw_bits_per_use, K_potential_bits_per_use | AUTHOR_DECISION_REQUIRED | Chốt quantity đầu vào và lưu raw gốc; không clip/đổi scale ngầm | C03–C10 | P0 |
| lookup.file / sha256 / provenance | null /null /null | path/hash/record | P, CODE | lookup block; skr_lookup.py | MISSING_SOURCE | Khi dữ liệu được chấp nhận, tạo adapter lossless riêng theo schema; không sửa CSV/NPZ gốc | C03–C10 | P0 |
| Chọn lineage của bảng dùng cho paper | Receiver30 đang được audit; cache distance bỏ fading variance là lineage khác | model scope | QPROD, active distance report | receiver30 report; SKR_DISTANCE_NO_FADING_NOISE_CACHE_REPORT_VI.md | AUTHOR_DECISION_REQUIRED | Xác nhận lineage đúng manuscript; không thay bảng để lấy rate cao hơn, không trộn noise/receiver/geometry | C03–C10 | P0 |

QDATA không phải một dataset giả hay bị mất: đây là các đánh giá số đã lưu. Nhưng
numeric PASS, nguồn payload đủ để tái tạo binary64, và security/source evidence
đủ cho claim paper là các việc khác nhau. Chưa có bước nào nâng trạng thái đó.

## 2. Finite-size-aware key yield

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| f_s | null | signals/s | P, PROV | verified_context.pulse_rate_hz | MISSING_SOURCE | Cung cấp nguồn/định nghĩa rate; không lấy RF bandwidth1MHz làm symbol rate | C04–C10; gate chung | P1 |
| eta_valid | null | dimensionless | P, PROV | verified_context.eta_valid | AUTHOR_DECISION_REQUIRED | Xác định phần tín hiệu key generation và hao hụt protocol; không mặc định1 | C04–C10 | P1 |
| m0 numeric | null | valid signals/clear slot | P, CODE | m0; finite_size.py | MISSING_SOURCE | Cung cấp trực tiếp giá trị có provenance hoặc đủ fs/eta_valid để dẫn xuất | C04–C10 | P1 |
| m0 relation | fs*dt*eta_valid; chưa có số paper | signals/clear slot | task/model, PROV | accumulated signal definition | DERIVED | Chỉ tính khi inputs đã xác định; không dùng m0 demo | C04–C10 | P1 |
| epsilon | null | dimensionless | P, PROV | epsilon; finite_size.py validates0<epsilon<1 | AUTHOR_DECISION_REQUIRED | Chốt giá trị và ý nghĩa trong proxy; không lấy channel excess noise làm epsilon | C04–C10 | P1 |
| delta_t | 1 | s | P, PROV | dt; current manuscript Section I-A | SOURCE_VERIFIED | Giữ cùng slot cho cloud, edge, signal và rate | C02,C04–C10 | P1 |
| K / K* | K>=1 là decision variable; chưa có nghiệm paper | slots | CODE | Scenario.horizon, terminal scan trong dp_solver/evaluation | DERIVED | Không điền fixed K; optimizer/prefix evaluator chọn riêng P1/P2 | C04–C10 | P2 |
| n_K / S_K | sum(m_k) / sum(m_k*r_j); chưa tính paper | signals / bits | CODE, PROV | evaluation.py, finite_size.py | DERIVED | Lưu cùng path/blockage/rates, không tạo series độc lập | C07–C08,C10 | P2 |
| Finite-size proxy | max(0,S-7*sqrt(n*log2(2/epsilon))) | bits | CODE, PROV | finite_size.py; current manuscript Eq8,28–30 | SOURCE_VERIFIED | Một correction trên accumulated prefix; không cộng penalty slotwise | C04–C10 | P0 |
| Composable proof cho proxy across channel states | Chưa có | security claim | PROV, Q | limitations; UNVALIDATED_SECURITY_MODEL | MISSING_SOURCE | Không gọi proxy là composable-security bound; review claim/aggregation trước READY | C03–C10 | P0 |

## 3. Hình học HAP–UAV

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| HAP altitude | 20000 trong metadata; hap_m chưa điền | m | P, Q, PROV | verified_context.hap_altitude_m | SOURCE_VERIFIED | Không coi biết altitude là đã có tuple HAP đầy đủ | C02–C10 | P1 |
| UAV altitude | 1000 | m | P, Q | uav_altitude_m | SOURCE_VERIFIED | Giữ đúng HAP–UAV, không chuyển thành100m từ bài RF | C02–C10 | P1 |
| HAP projection của lookup đã có | (1000,1000) | m | QPROD | geometry_groups: radius2 quanh1000; report geometry section | SOURCE_VERIFIED | Đây là geometry của bảng cũ, không tự trở thành lựa chọn mission mới | C03–C10 | P0 |
| HAP tuple nhiệm vụ | hap_m=null | m | P | hap_m | AUTHOR_DECISION_REQUIRED | Chốt có kế thừa geometry lookup hay không; nếu khác phải có rate data phù hợp | C02–C10 | P1 |
| q0 | initial_m=null | m | P | initial_m | AUTHOR_DECISION_REQUIRED | Chọn và ghi rationale; không dùng tâm heatmap hoặc RF qI mặc định | C04–C10; gate chung | P1 |
| Operating area | [2000,2000], local coordinates | m | P, PROV | area_m; manuscript Section I-A | SOURCE_VERIFIED | Xác định transform nếu cloud ở world map khác | C02–C10 | P1 |
| Terminal position constraint | Không đặt; mặc định unrestricted | model | CODE | terminal_index=None; optional terminal_m | NOT_APPLICABLE | Chỉ thêm ràng buộc cuối nếu tác giả yêu cầu, không coi là thiếu bắt buộc | C04–C10 | P1 |

## 4. Gaussian cloud và optical blockage

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| Cloud drift velocity | [-5,0] trong metadata | m/s | P, PROV | verified_context.cloud_velocity_m_s; manuscript Fig3 | SOURCE_VERIFIED | Dịch liên tục, không dịch40m mỗi slot; không nhầm với wind21m/s của turbulence context | C02,C04–C10 | P1 |
| Cloud grid | 50 rows ×50 columns cho operating area | cells | P, PROV | verified_context.cloud_visualization_grid | SOURCE_VERIFIED | Không dùng làm movement graph tự động | C02,C04–C10 | P1 |
| Cloud cell size | [40,40] | m | area/grid | 2000/50 | DERIVED | Không ép UAV ở cell centers; không coi toàn16km background là50×50 | C02,C04–C10 | P1 |
| amplitudes, centers, sigma/covariance | cloud=null; C có400 components minh họa, DEMO có3 | mg/m³; m; m² | C, DEMO, P | Gaussian coefficients và saved arrays | AUTHOR_DECISION_REQUIRED | Chọn realization/nguồn hoặc chấp nhận scenario giả định được ghi rõ; không tự gán cho paper | C02,C04–C10 | P1 |
| clip_max | Chưa chọn paper; C dùng15 | mg/m³ | C, P | clip/generation settings | AUTHOR_DECISION_REQUIRED | Chốt có clip hay không, bảo toàn cùng field qua các hình | C02,C04–C10 | P1 |
| L_th | Chưa chọn paper; C/DEMO dùng8 minh họa | mg/m³ | C, DEMO, P | threshold_mg_m3 | AUTHOR_DECISION_REQUIRED | Chọn idealized model threshold có rationale; không gọi8 là universal opacity threshold | C02,C04–C10 | P1 |
| Cloud altitude / thickness | Chưa có nguồn nhiệm vụ | m | PROV, P | blockage=null | MISSING_SOURCE | Cung cấp căn cứ/lựa chọn mô hình lớp mây; không nhập demo layer5–7km ngầm | C04–C10; gate của C02 | P1 |
| blockage.mode / layer_bottom_m / layer_top_m | null | mode / m | P, CODE | BlockageModel constructor | AUTHOR_DECISION_REQUIRED | Chốt slab hoặc approximation được công khai, nhất quán h_HAP/h_UAV | C04–C10; gate của C02 | P1 |
| sample_spacing_m | Chưa chọn paper; DEMO dùng2 | m | DEMO, CODE | LOS sampling along slab intersection | AUTHOR_DECISION_REQUIRED | Chọn resolution và kiểm tra độ nhạy; không gọi sampling agreement là continuous intersection certificate | C04–C10 | P1 |
| b[k,j] / z[k,j] | Chưa có paper; demo có trong scenario.npz | binary | CODE, DEMO | blockage.sequence; z=1-b | DERIVED | Tính từ optical path chứ không test riêng endpoint UAV | C04–C10 | P2 |

Các hệ số cloud đã lưu trong C là dữ liệu tổng hợp tái lập được, không phải
quan trắc khí tượng. `cloud_model.py` dùng center(t)=center(0)+velocity*t và
Gaussian quadratic form; `blockage.py` cắt segment HAP→UAV với slab rồi lấy
mẫu horizontal segment. Map CLWC không tự là map UAV có SKR=0. Paper cloud
chưa có, không có lý do kỹ thuật đơn thuần để nâng C02 thành READY.

## 5. Năng lượng, rotor và mission graph

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| Active default rotor | arXiv2018v1; chưa đổi | version | P, A18 | propulsion/rotor metadata | AUTHOR_DECISION_REQUIRED | Nếu mission mới dùng IEEE phải có lựa chọn và audit rõ, không thay từng hệ số lẻ | C01,C04–C10; R02 độc lập | P1 |
| Default P0 / Pi | 580.65 /790.6715228132718 | W | A18, P | preprint Eq61/TableI; derived values | DERIVED | Giữ bộ đồng nhất, không trộn với IEEE | C01,C04–C10 | P1 |
| Default v0 / vmax | 7.2 table value /60 | m/s | A18 | TableI p27 /SectionV p22 | SOURCE_VERIFIED | Đây là default hiện tại, không phải IEEE2019 | C01,C04–C10 | P1 |
| IEEE W / rho / R / A | 20 /1.225 /.4 /.503 | N; kg/m³; m; m² | I19 | TableI, journal2342/PDF14 | SOURCE_VERIFIED | Reference aircraft, không tự áp dụng cho mọi UAV | R02; mission chỉ sau quyết định | P1 |
| IEEE Omega / Utip | 300 /120 | rad/s; m/s | I19 | TableI; Utip=Omega*R | SOURCE_VERIFIED | Giữ nguyên rounded source profile | R02; mission tùy quyết định | P1 |
| IEEE blades / chord / solidity | 4 /.0157 /.05 | count; m; dimensionless | I19 | TableI, journal2342/PDF14 | SOURCE_VERIFIED | Không thay bằng tham số arXiv | R02; mission tùy quyết định | P1 |
| IEEE flat-plate area / d0 | .0151 /.6 | m²; dimensionless | I19 | TableI, journal2342/PDF14 | SOURCE_VERIFIED | Giữ thông số bảng và rounding convention | R02; mission tùy quyết định | P1 |
| IEEE correction k / profile delta | .1 /.012 | dimensionless | I19 | TableI, journal2342/PDF14 | SOURCE_VERIFIED | Không nhầm k với RF NLoS kappa | R02; mission tùy quyết định | P1 |
| IEEE table v0 / vmax | 4.03 /30 | m/s | I19 | TableI /SectionV journal2339 | SOURCE_VERIFIED | vmax không lấy từ TableI; figure mới công khai v0-derived policy | R02; mission tùy quyết định | P1 |
| IEEE derived P0 / Pi / hover | 79.85628 /88.62793774108202 /168.48421774108203 | W | I19 derivation | Eq64; raw A=.503 | DERIVED | Không hard-code ba hằng số làm ba input độc lập | R02; mission tùy quyết định | P1 |
| IEEE used v0 | 4.028542624594636 | m/s | I19 derivation | sqrt(W/(2*rho*A)); profile policy derived | DERIVED | Giữ riêng table4.03 và derived4.02854; không đổi policy ngầm | R02; mission tùy quyết định | P1 |
| E_max | energy_budget_j=null | J | P, PROV | energy_budget_j | AUTHOR_DECISION_REQUIRED | Cung cấp usable propulsion allocation; không dùng1500J của demo | C04–C10 | P1 |
| T_hover_reference nếu dẫn xuất budget | Chưa chọn; không phải input bắt buộc nếu Emax đã có | s | PROV | optional Emax=P_hover*T_ref | AUTHOR_DECISION_REQUIRED | Không tự chọn duration hay gọi lựa chọn này là literature value | C04–C10 | P1 |
| E_min(D,dt) | dt*lower-convex-envelope(P)(D/dt) | J | CODE | propulsion.py, WaypointGraph.build | SOURCE_VERIFIED | Giữ speed mixing/numerical convergence; không thay constant-speed power | C06; mọi feasible trajectory | P1 |
| Acceleration/turn/transient cost | Không mô hình hóa | model | CODE, PROV | power/energy assumptions | NOT_APPLICABLE | Nêu limitation; không tự thêm cost vào model/số đã lưu | C01,C04–C10 | P1 |
| graph.kind / points_m / spacing_m / bounds_m | graph=null | type; m | P, CODE | config.py graph branches | AUTHOR_DECISION_REQUIRED | Chọn graph, có q0, connectivity và feasible successors; cloud grid không quyết định graph | C04–C10 | P1 |
| c[i,j] | Chưa tính paper | J/edge | CODE | E_min(distance,dt), hover self-loop | DERIVED | Precompute sau khi graph/rotor/dt được chốt, kiểm độ hội tụ | C04–C10 | P2 |
| max_horizon / prediction cap | null | slots | P | max_horizon | AUTHOR_DECISION_REQUIRED | Chọn prediction availability horizon, không ép nó bằng optimal K | C04–C10 | P1 |
| K_energy_bound | Chưa tính; floor(Emax/min feasible edge cost) | slots | CODE | Scenario.horizon | DERIVED | Bao gồm hover, không giả hover là minimum-power speed | C04–C10 | P2 |
| RF altitude100m / RF communication power / NLoS model | Không thuộc rotor-only/QKD mission hiện tại | model | I19 RF section | SectionV, khác phần rotor | NOT_APPLICABLE | Không sao chép sang HAP–UAV | Không phải đầu vào mở khóa | P0 |

## 6. Bốn thuật toán và mục tiêu

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| Method roster | Stationary, SKR-Greedy, Energy-Aware Greedy, Pareto DP | methods | CODE | experiments.run_methods | SOURCE_VERIFIED | Giữ cùng Scenario/graph/rates/z/budget/evaluator cho bốn method | C04–C10 | P2 |
| Stationary hover cost | dt*P(0) mỗi slot, q=q0 | J/slot | CODE | baselines.py + self-loop cost | SOURCE_VERIFIED | Không gán zero energy; có thể INFEASIBLE nếu không đủ hover budget | C04–C10 | P2 |
| Greedy score | m0*z*r; energy-aware thêm -lambda*c | bits/slot | CODE | baselines.solve_baseline | SOURCE_VERIFIED | Giữ tie-break reward, edge cost, index như code | C04–C10 | P2 |
| lambda / lambda_provenance | null /null | bits/J; source record | P | greedy block | AUTHOR_DECISION_REQUIRED | Prior hoặc calibration độc lập; không chọn theo test realization | C04–C10 | P1 |
| P1 | max L_hat/(K*dt), chưa có optimum paper | bits/s | CODE, PROV | evaluation / dp terminal scan | SOURCE_VERIFIED | Đánh giá mọi prefix feasible, không nhầm bits/use | C04,C06,C08,C10 | P2 |
| P2 | max L_hat, chưa có optimum paper | bits | CODE, PROV | evaluation / dp terminal scan | SOURCE_VERIFIED | Chọn terminal riêng, không ép giống P1 | C05–C10 | P2 |
| DP mode | exact trong P, graph paper chưa có | algorithm | P, CODE | dp.mode; dp_solver | AUTHOR_DECISION_REQUIRED | Chốt workload khả thi; nếu dùng approximation phải ghi rõ | C04–C10 | P1 |
| label_cap | null và không active trong exact | labels/state | P, CODE | solve_dp(label_cap=None) | NOT_APPLICABLE | Chỉ chọn cap nếu dùng approximate; không âm thầm cap exact | C04–C10 | P1 |
| Dominance | Cùng(k,j,u), e thấp hơn/a cao hơn, float64 strict | rule | CODE | pareto_prune / state grouping | SOURCE_VERIFIED | Không prune giữa u khác nhau; không claim optimum continuous | C04–C10 | P2 |
| Cloud information | DP full predicted horizon; greedy current-slot decisions | information model | CODE, PROV | run_methods / baselines / stored information_scope | SOURCE_VERIFIED | Công khai khác biệt; không quy toàn bộ gain thành superior algorithm | C04–C10 | P0 |
| Stopping information | Best feasible prefix hồi cứu cho mọi method | policy | CODE | selected_solutions | SOURCE_VERIFIED | Không gọi greedy + retrospective stopping là online guarantee | C04–C10 | P0 |

## 7. Paper-mode, result bundle và runtime

| Parameter | Current value | Unit | Source | Source location | Evidence status | Required decision | Affected figures | Priority |
|---|---|---|---|---|---|---|---|---|
| Paper experiment | NOT_RUN; chưa có results/paper_verified/results.json | run status | P, A5 từ audit trước, filesystem | paper config + audit_summary | MISSING_SOURCE | Chỉ chạy khi input, nguồn và quyền/lifecycle phù hợp đã đủ | C02–C10 | P0 |
| research_use_authorized | false | gate | P | config.py requires boolean True | AUTHOR_DECISION_REQUIRED | Không tự đảo cờ; cờ không thay bằng chứng nguồn/lifecycle | C02–C10 | P0 |
| Result data_status | Producer paper hiện ghi UNVALIDATED_SECURITY_MODEL—RESEARCH PERFORMANCE APPROXIMATION | scope | CODE | experiments.run_experiment | SOURCE_VERIFIED | Không xóa nhãn để qua exporter. Review source/claim và policy bằng bằng chứng nếu muốn READY | C02–C10 | P0 |
| Sealed base bundle | Chưa có paper bundle; demo bundle có nhưng synthetic | files | CODE, DEMO | _validate_seals / verify_results | MISSING_SOURCE | Cần results.json,scenario.npz,skr_input.csv,input_manifest.json,output_manifest.json cùng config/producers | C02–C09; nền cho C10 | P2 |
| Native schema adapter | Chưa có bản paper-admitted generic lookup | schema | QAUD, CODE | CSV x_m,y_m,skr_bits_per_use hoặc NPZ points,rates | AUTHOR_DECISION_REQUIRED | Sau admissibility, tạo bản lossless riêng có raw/potential policy; không sửa bảng gốc | C03–C10 | P0 |
| runtime_s | Có measurement demo, chưa có paper | s | DEMO, CODE | runs[*], experiments.measured | MISSING_SOURCE | Đo từ workload được phép, không suy/nhân thời gian demo hoặc thời gian pytest | C09; loader chung | P2 |
| python_peak_bytes | Có demo, chưa có paper | bytes | DEMO, CODE | tracemalloc scope | MISSING_SOURCE | Phân biệt Python allocation với toàn bộ process/native memory | C09 | P2 |
| sampled_peak_rss_bytes | Có demo, chưa có paper | bytes | DEMO, CODE | psutil RSS sampling10ms | MISSING_SOURCE | Không gọi đây là peak liên tục chính xác | C09 | P2 |
| Workload/environment metadata | Demo có graph/labels,Python/deps,scope; paper chưa có | records | DEMO, CODE | diagnostics,input_manifest,memory_scope | MISSING_SOURCE | Lưu J,H,cap,discards,hardware/threads và scope đo đúng lần paper | C09–C10 | P2 |
| Sensitivity grids / results | P chưa có sensitivities; CSV chỉ có demo | input grid / rows | P, DEMO | experiments.sensitivity_runs | AUTHOR_DECISION_REQUIRED | Chốt energy/threshold/spacing/caps trước; chỉ chạy sau base correctness/readiness | C10 | P3 |
| Statistical runtime superiority | Chưa có benchmark paper lặp | claim | records hiện có | single-call timings | MISSING_SOURCE | Nếu muốn claim thống kê, cần phép đo lặp cùng workload và mô tả variance; không bịa CI | C09–C10 | P3 |
| Final manuscript numbering | Chưa có mapping duy nhất cho số02 | editorial mapping | catalog + R02 manifest | 02 cloud khác02 rotor | AUTHOR_DECISION_REQUIRED | Chốt mapping khi tích hợp manuscript; chưa rename hoặc overwrite | Toàn bộ | P1 |

## Những quyết định cần tác giả trả lời trước tiên

1. **Nguồn/claim lookup:** dùng đúng receiver30 finite-catalog và các convention
   đã ghi hay một lineage khác; bằng chứng còn thiếu được giải quyết thế nào?
   Không có quyết định văn phong nào tự làm `INSUFFICIENT_EVIDENCE` biến mất.
2. **Protocol tín hiệu:** fs, valid fraction hoặc m0 có provenance, epsilon và
   phạm vi interpretation của finite-size proxy. Không có số đề xuất trong bảng.
3. **Scenario nhiệm vụ:** chọn rotor nào cho run mới, q0/HAP geometry, Emax,
   cloud realization/layer/Lth/LOS resolution, graph và prediction horizon,
   prior lambda. Tách rõ cái lấy từ nguồn và cái được chọn như giả định.

Sau khi các quyết định và bằng chứng đủ, mới tạo một base bundle dùng chung
cho C02–C09 theo renderer hiện tại, rồi sensitivity C10. Chi tiết từng hình,
điều kiện và lệnh dự kiến nằm trong tài liệu kế tiếp. Phase2 này không tự trả
lời các quyết định thay tác giả và không triển khai paper run.
