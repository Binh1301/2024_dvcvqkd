# Ma trận tham số hợp nhất ba nguồn — Phase 4

Mục đích là tách đúng nguồn và vai trò, không tạo một default mission bằng
cách ghép các số của ba bài. Source A là bản thảo nhóm, không tự nhận đã xuất
bản. Source B chỉ dùng finite-size reference, không thay MB bằng GMCS hoặc
đổi effective transmittance. Source C là reference-aircraft rotor, không
chuyển RF geometry/communication power sang HAP–UAV.

Nguồn và bytes đã đối chiếu:
[source_inputs.json](phase4_validation/source_inputs.json). Source B local
5-page IEEE PDF có DOI10.1109/LCOMM.2025.3624071; Table I ở journal3036/PDF4
đã render/đọc, Eq.(19)–(21) ở journal3035/PDF3. Source A gắn bản
`available_v43.pdf` SHA256 f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b.
Source C giữ hai profile đã có và source verification của task rotor trước.

Các nhãn là **SOURCE_REPORTED**, **DERIVED**, **AUTHOR_ASSUMPTION**,
**AUTHOR_DECISION_REQUIRED**, **NOT_AVAILABLE**. SOURCE_REPORTED không có nghĩa
đã chứng minh security của mô hình hợp nhất. Current module conventions được
ghi nguồn là code/protocol/author directive, không giả là trích dẫn bảng paper.

## Source A — Channel reference, cấu hình riêng

File: [hap_uav_mb_reference.yaml](../configs/channel/hap_uav_mb_reference.yaml).
Không đổi `paper.yaml` hoặc nhập hardware receiver30 override.

| Parameter | Value | Unit | Source | Equation/Table/Section | Role | Status | Affected Figures |
|---|---|---|---|---|---|---|---|
| hap_altitude | 20000 | m | A manuscript | Section IV p3 | Channel geometry | SOURCE_REPORTED | C02–C10 |
| uav_altitude | 1000 | m | A | Section IV p3 | Channel/LOS geometry | SOURCE_REPORTED | C02–C10 |
| reference_zenith_angle | 30 | degree | A | Section IV p3 | Independent reference case, not every waypoint | SOURCE_REPORTED | Channel reference only |
| beam_full_divergence | 233 | µrad | A | Section IV p3, definition II-B | Full-angle optics | SOURCE_REPORTED | C03–C10 |
| wavelength | 1550 | nm | A | Section IV p3 | Optics/turbulence | SOURCE_REPORTED | C03–C10 |
| wavefront_curvature_radius | infinity | m | A | Section IV p3 | Explicit infinite curvature | SOURCE_REPORTED | C03–C10 |
| transmitter_jitter_angle | 15.61 | µrad | A | Section IV p3 | Pointing per-axis SD | SOURCE_REPORTED | C03–C10 |
| receiver_aperture_diameter | .08 | m | A | Section IV p3 | Diameter, not radius | SOURCE_REPORTED | C03–C10 |
| boresight_x / boresight_y | 0 /0 | m | A | Section IV p3 | Offsets, not mission q0 | SOURCE_REPORTED | C03–C10 |
| uav_position_sd | 1 | m | A | Section IV p3 | Pointing jitter | SOURCE_REPORTED | C03–C10 |
| uav_angular_fluctuation_sd | 1.5 | mrad | A | Section IV p3 | AoA | SOURCE_REPORTED | C03–C10 |
| receiver_fov_half_angle | 6.25 | mrad | A | Section IV p3 | Half-angle FOV | SOURCE_REPORTED | C03–C10 |
| atmospheric_altitude | 20000 | m | A | Section IV p3 | Turbulence integration context | SOURCE_REPORTED | C03–C10 |
| zenith_atmospheric_transmittance | .92 | dimensionless | A | Section IV p3 | tau_zen | SOURCE_REPORTED | C03–C10 |
| ground_turbulence_cn2 | 1e-14 | m^(-2/3) | A | Section IV p3 | Turbulence | SOURCE_REPORTED | C03–C10 |
| rms_wind_speed | 21 | m/s | A | Section IV p3 | Turbulence parameter, not cloud advection | SOURCE_REPORTED | C03–C10 |
| reconciliation_efficiency | .95 | dimensionless | A | Section IV p3 | beta, not detector efficiency | SOURCE_REPORTED | C03–C10 |
| Native scalar convention | VA=Vmod=2*nbar | convention | Current code/protocol, previous author mapping | source_normalization, AUTHOR_CONFIRMED_VA_EQUALS_VMOD | Preserved I/O contract | SOURCE_REPORTED | C03–C10 |
| Printed variance convention | Vmod=nbar/2 | convention | A | II-A after Eq3 | Recorded separately, not silently applied | SOURCE_REPORTED | Source mapping note |
| Z/w core correctness decision | Author-confirmed; implementation unchanged | author directive | Phase4 task Section1 | Existing Eq14/Eq16 code remains opaque | Protected core, no new mathematics audit | SOURCE_REPORTED | All MB paths |
| Channel/detector excess noise for NEW reference | null /null | SNU | Not specified in the supplied Section-IV table | New config explicit missing fields | No receiver30 noise imported | NOT_AVAILABLE | C03–C10 |
| Separate detector efficiency | null | dimensionless | Not supplied for this integration | New config missing field | Do not infer from beta | NOT_AVAILABLE | If required by selected backend |
| Geometry L(q), zeta(q), eta_atm(q) | General functions implemented; mission values not computed | m; rad; dimensionless | Existing LinkGeometry / atmospheric helper | A II-B; L=delta_h*sec(zeta), tau^sec(zeta) | Callback context per waypoint | DERIVED | C03–C10 |
| eta_f / effective excess output | mh² / (m1-mh²)*Vmod+E_eta_xi | dimensionless; SNU | A | Eq17 | Channel→SKR scalar interface | DERIVED | C03–C10 |
| m1,mh,M0 moments | Existing-provider inputs, not regenerated | dimensionless | Existing Eq18–20 engine | Native m1,mh,M0 contract | No closed-form/model replacement | DERIVED | C03–C10 |

## Source B — Finite-size reference only

File: [ieee_2025_reference.yaml](../configs/finite_size/ieee_2025_reference.yaml).
Không nhập GMCS rate, mean-transmittance proxy E[T], SNR-dependent beta,
noise/attack hoặc AO settings của B vào MB channel A.

| Parameter | Value | Unit | Source | Equation/Table/Section | Role | Status | Affected Figures |
|---|---|---|---|---|---|---|---|
| N_block | 1e8 | exchanged signals | B IEEE2025 | TableI,3036/PDF4 | Standalone block reference, not all mission blocks | SOURCE_REPORTED | Reference validation; C07 context |
| key_fraction | .8 | dimensionless | B | TableI,3036/PDF4 | n_block/N_block, not eta_valid | SOURCE_REPORTED | Reference only |
| epsilon_PE | 1e-8 | probability | B | TableI | Reference failure component | SOURCE_REPORTED | C07 reference |
| epsilon_EC | 1e-8 | probability | B | TableI | Reference failure component | SOURCE_REPORTED | C07 reference |
| epsilon_PA | 1e-8 | probability | B | TableI | Reference failure component | SOURCE_REPORTED | C07 reference |
| epsilon_reference | 3e-8 | probability | B/input components | Eq21 sum | Does not fill paper.epsilon | DERIVED | Reference validation |
| n_block_reference | 8e7 | key-generation signals | B/input fraction | n=N*.8 | Does not fill paper.m0 | DERIVED | Reference validation |
| Delta reference | .003989881969840257 | bits/valid signal | Existing evaluator, B formula | Eq20 with n=8e7,epsilon=3e-8 | Known finite-block penalty | DERIVED | C07 reference |
| finite_size_aware_key_yield_proxy | max(0,S-7*sqrt(n*log2(2/epsilon))) | bits | Existing accumulated model; B penalty reference | Accumulated terminal-block expression | Performance proxy, not composable proof | DERIVED | C04–C10 |
| fs | null | signals/s | Not given by N_block | No inference from block size | Mission rate still missing | NOT_AVAILABLE | C04–C10 |
| eta_valid / m0 mission | null /null | fraction /signals per clear slot | Not fixed by n/N reference | fs*dt*eta_valid only with declared inputs | Protocol/mission decision | AUTHOR_DECISION_REQUIRED | C04–C10 |
| Mission epsilon/block rule | Not assigned from reference | probability/block convention | Author must choose interpretation | Not silently borrowed | Accumulated proxy scope | AUTHOR_DECISION_REQUIRED | C04–C10 |

## Source C — Rotor preserved, not selected as a new mission default

Files: existing [ieee_2019](../configs/rotor/ieee_2019.yaml) and
[arxiv_2018_v1](../configs/rotor/arxiv_2018_v1.yaml). IEEE Source C DOI:
10.1109/TWC.2019.2902559; no profile/output is changed by Phase4.

| Parameter | Value | Unit | Source | Equation/Table/Section | Role | Status | Affected Figures |
|---|---|---|---|---|---|---|---|
| IEEE W/rho/R/A | 20/1.225/.4/.503 | N;kg/m³;m;m² | C IEEE2019 | TableI,2342/PDF14 | Reference aircraft | SOURCE_REPORTED | R02-IEEE; future mission if chosen |
| IEEE Omega/Utip | 300/120 | rad/s;m/s | C | TableI | Reference optics-independent rotor | SOURCE_REPORTED | R02-IEEE |
| IEEE k/delta/s/d0 | .1/.012/.05/.6 | dimensionless | C | TableI | Distinct from RF NLoS kappa | SOURCE_REPORTED | R02-IEEE |
| IEEE vmax | 30 | m/s | C | SectionV,2339/PDF11 | Not TableI | SOURCE_REPORTED | R02-IEEE; future mission choice |
| IEEE P0/Pi/hover | 79.85628/88.62793774108202/168.48421774108203 | W | C/raw inputs | Eq64 | Existing derived profile, unchanged | DERIVED | R02-IEEE |
| IEEE used v0 | 4.028542624594636 | m/s | C/raw inputs | TableI definition | Derived-policy value | DERIVED | R02-IEEE |
| IEEE table v0 | 4.03 | m/s | C | TableI | Rounded source value, retained separately | SOURCE_REPORTED | R02-IEEE |
| Current paper rotor coefficients | P0=580.65,Pi=790.6715228132718 | W | Preprint raw inputs, current paper.yaml | Preprint Eq61 | Default arXiv coefficients unchanged | DERIVED | C01,C04–C10 |
| Rotor selected for a new mission | Not changed | profile | Author decision | Keep both reference profiles | No mixed coefficients/default switch | AUTHOR_DECISION_REQUIRED | C04–C10 |

## Inputs not supplied by combining the three papers

| Parameter | Value | Unit | Source | Equation/Table/Section | Role | Status | Affected Figures |
|---|---|---|---|---|---|---|---|
| HAP horizontal coordinates | null | m | Not inferred from reference angle | New reference config | Mission/LOS geometry | AUTHOR_DECISION_REQUIRED | C02–C10 |
| UAV q0 | null | m | Not RF qI nor heatmap maximum | paper.yaml unchanged | Initial state | AUTHOR_DECISION_REQUIRED | C04–C10 |
| E_max | null | J | Not specified for the QKD mission | paper.yaml unchanged | Propulsion budget | AUTHOR_DECISION_REQUIRED | C04–C10 |
| Waypoint graph | null | nodes/edges;m | Independent from cloud display grid | Existing graph module | Feasible trajectory domain | AUTHOR_DECISION_REQUIRED | C04–C10 |
| Prediction horizon | null | slots | Not selected from block size | Existing energy/prediction bound | Variable stopping constraint | AUTHOR_DECISION_REQUIRED | C04–C10 |
| K optimum | Not computed | slots | Existing DP/baseline prefix evaluation | P1/P2 terminal scan | Derived outcome, not fixed author K | DERIVED | C04–C10 |
| Cloud coefficients/realization | Not selected for mission | mg/m³;m;m² | Existing figure/demo data only | Existing Gaussian model | No newly invented field | AUTHOR_DECISION_REQUIRED | C02,C04–C10 |
| Cloud attenuation/erasure interpretation | mode=null,approval=false | policy | New explicit interface | CloudPolicy/CloudEffect | Mutually exclusive per mechanism | AUTHOR_DECISION_REQUIRED | C04–C10 |
| Cloud optical attenuation factor/extinction | Not supplied | dimensionless factor or sourced1/m | No CLWC conversion assumed | Explicit post-loss provider required | No fabricated optical depth | NOT_AVAILABLE | Attenuation extension |
| Cloud altitude/thickness | null | m | No source supplied | Existing slab LOS interface | Geometry consistency | NOT_AVAILABLE | C04–C10 |
| L_th/clip/frame/LOS spacing | Not selected for paper | mg/m³;m | Figure values remain illustrative | Existing source code, not new defaults | Scenario decisions | AUTHOR_DECISION_REQUIRED | C02,C04–C10 |
| Greedy lambda | null | bits/J | No prior chosen | Existing baseline score | Prior or independent calibration | AUTHOR_DECISION_REQUIRED | C04–C10 |
| Security claim scope | Finite-size proxy; full composable claim not established | claim | Author/model review | No inheritance of B theorem | Do not promote security | AUTHOR_DECISION_REQUIRED | C03–C10 |
| Cloud realization seed | Existing demo/figure seeds only, not newly chosen | seed | Existing manifests | No cloud RNG called in integration | Preserve known input provenance | AUTHOR_DECISION_REQUIRED | C02,C04–C10 |

`AUTHOR_ASSUMPTION` không được dùng cho một giá trị mới trong Phase4 vì không
có giả định mới được tác giả giao để kích hoạt. Các giả định demo/figure cũ
không được chuyển vào các reference config hoặc default paper. Giá trị vắng
mặt vẫn vắng mặt; các function tổng quát và interface đã chạy được trên unit
cases rõ ràng, không tạo dataset paper giả để lấp chỗ trống.
