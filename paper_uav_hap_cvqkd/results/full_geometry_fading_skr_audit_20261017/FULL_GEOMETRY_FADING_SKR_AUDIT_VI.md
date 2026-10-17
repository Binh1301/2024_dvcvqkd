# Full Numerical Audit of HAP–UAV Geometry, Fading Moments and SKR

Ngày2026-10-17. Task b8e5bb91. Audit-only: không sửa production code/config/source, không chạy22.700 điểm hoặc1.600 missions, không commit/push.

Kết luận hardware: **CONFIGURATION_MATCH_CONFIRMED**. Reference âm được tạo với Dr=.55m và divergence full-angle10urad. Không có evidence rằng reference này lấy từ hardware cũ. Có **5 FAIL strict comparisons được giữ nguyên**, truy về độ chính xác tích phân phụ mu2 và sensitivity của input-referred xi_f; chúng không đổi dấu hoặc độ lớn SKR. Không gọi toàn bộ audit là một PASS chung. **UNVALIDATED_SECURITY_MODEL** giữ nguyên.

## A. Actual runtime configuration

Probe scripts/probe_full_geometry_runtime.py rebuild từ configuration files qua clear_state -> channel_state -> derive_physical_inputs -> manuscript_pointing_parameters -> LiteralChannel.from_physical -> PhysicalFadingDistribution.moments, rồi evaluate_candidate của trusted_heterodyne_skr. Sys.setprofile lưu arguments và return objects thực tế trong runtime_probe.json; không kết luận từ một literal trong file.

Runtime primary dùng configs/binary_cloud_skr_demo.json; derive_physical_inputs đọc configs/default.yaml rồi nhận explicit aperture/beam-waist/zenith/tau overrides. Các thông số turbulence/UAV/AoA còn lại lấy từ default.yaml. Source pair lấy đúng reference_pair trong configs/fading_effective_binary_cloud.json. Trusted alternate lấy riêng từ configs/manuscript_corrected_3moments.json; không đổi thành primary.

| Parameter | Default/source configuration | Runtime actual | Unit | Source |
|---|---|---|---|---|
| Dr | 0.080000000000000002 | 0.55000000000000004 | m | default.yaml -> binary_cloud.channel.receiver_radius_m x2 |
| r_ap | 0.040000000000000001 | 0.27500000000000002 | m | same; derive_physical_inputs override |
| theta_div | 0.000223 | 1.0000000000000003e-05 | rad, full angle | default.yaml -> derived from configured beam_waist override |
| lambda | 1.55e-06 | 1.55e-06 | m | default.yaml.channel.wavelength_m |
| w0 | 0.004424935637532516 | 0.098676064716975098 | m | binary_cloud.channel.beam_waist_m |
| h_HAP | 20000 | 20000 | m | default.yaml + explicit geometry equality check |
| h_UAV | 1000 | 1000 | m | same |
| zeta | 0.52359877559829882 | 0.52359877559784263 | rad | grid/HAP coordinates -> link_geometry override |
| sigma_h | 1 | 1 | m per axis | default.yaml.pointing.sigma_h_m |
| theta_jt | 1.5610000000000001e-05 | 1.5610000000000001e-05 | rad per axis | default.yaml.pointing.theta_jt_rad |
| Cn2(0) | 1e-14 | 1e-14 | m^(-2/3) | default.yaml.turbulence_profile |
| wind | 21 | 21 | m/s | same |
| sigma_o | 0.0015 | 0.0015 | rad | default.yaml.aoa.sigma_o_rad |
| theta_FOV | 0.0062500000000000003 | 0.0062500000000000003 | rad half-angle | default.yaml.aoa.theta_fov_rad |
| xi_ch | 0.018599999999999998 | 0.018599999999999998 | SNU input channel excess | binary_cloud.channel.xi_ch |
| eta_B primary | function default1 | 1 | unitless | binary_cloud.channel.R |
| nu_B primary | function default0 | 0 | SNU output per detected arm | binary_cloud.channel.xi_det |
| eta_B diagnostic | historical config.7 | 0.69999999999999996 | unitless | manuscript_corrected_3moments.json.R |
| nu_B diagnostic | historical config.0135 | 0.0135 | SNU | same.xi_det |
| tau_zen | — | 0.92000000000000004 | power | explicit binary config.clear_tau_zen |
| F0 | infinity | infinity | m | default.yaml.radius_of_curvature_m |

Default.yaml hiện là223urad, không phải233urad.233urad là old-manuscript case được user yêu cầu chẩn đoán. Default Dr=.08m/theta223urad không được dùng cho reference vì explicit override Dr=.55/w0=.098676... thắng. Default tau_zen=null còn yêu cầu chọn atmosphere rõ ràng. UavMotion dataclass có legacy defaults khác; channel builder explicitly truyền sigma_h/sigma_o hiện hành, không lấy dataclass defaults.

CLI historical runner chỉ có --stage và --output, không có geometry/physics flags. Hàm load_yaml đọc YAML trực tiếp, không environment substitution; static search trên dependency path không phát hiện os.environ/getenv cho physics. Runtime arguments/return objects còn xác nhận effective values. Historical argv/env chưa lưu nguyên gốc; đây là reconstructed trace với input/producer hash matching, không giả vờ truy xuất process cũ.

Không có eta_B=.8 trong active receiver configs. Giá trị.8 trong probability sweep là cloud probability, không phải detector efficiency. Primary(1,0) và trusted diagnostic(.7,.0135) được tách riêng ở mọi bảng.

10urad=1e-5rad; Dr=.55m -> r_ap=.275m. Với full-angle theta dùng w0=2lambda/(pi theta). Nếu dùng half-angle theta_half=theta_full/2, công thức tương đương là lambda/(pi theta_half), không dùng lẫn hệ số2.

Fresh reconstructed A bằng toàn bộ cached clear physical state ở reference44; producer/receipt hashes của evaluator trước đều khớp. Hai SKRs freshA có residual0 so reference artifact cũ. Geometry fingerprint mới lưu đầy đủ Dr/theta/w0, primitives, raw channel và source producers. Không dùng cached objective thiếu fingerprint để tính8 kết quả mới; source cache C,w độc lập geometry được xác thực riêng.

## B. Geometric and atmospheric calculations

Mọi phép tính độc lập ở scripts/audit_full_geometry_fading_skr.py bắt đầu từ primitive config/coordinates, không từ production intermediate. Mpmath70dps tự tích phân profile; không import geometry/channel/moment helpers production. Trong các bảng, cột MP là independent high-precision chain; sai khác với runtime được giữ, không thay số MP thành số cũ.

\[
\zeta=\arctan(r_\perp/\Delta h)
=\arctan(10969.655114591331/19000)
=0.52359877559784263.
\]

zeta=29.999999999973856 degree. Geometry embedding không ép chính xác30degree; khác nhỏ do tọa độ HAP được lưu hữu hạn.
\[
L=(h_{HAP}-h_{UAV})\sec\zeta
=(20000-1000)\times 1.1547005383789473
=21939.3102292.
\]

\[
\eta_{atm}=\tau_{zen}^{\sec\zeta}
=0.92^{1.1547005383789473}
=0.9082089654181672.
\]

\[
w_0=2\lambda/(\pi\theta_{div})
=2(1.55\times10^{-6})/(\pi\,10^{-5})
=0.098676064716975112.
\]

\[
z_R=\pi w_0^2/\lambda
=\pi(0.098676064716975112)^2/(1.55\times10^{-6})
=19735.212943395021.
\]

F0=infinity nên focusing factor1-L/F0=1, L dùng mét. Beam propagation:
\[
w_L=w_0\sqrt{(1-L/F_0)^2+(L\lambda/(\pi w_0^2))^2}.
\]

\[
w_L
=0.098676064716975112\sqrt{1+(21939.3102292\,1.55\times10^{-6}/(\pi\,0.098676064716975112^2))^2}
=0.14754761631878588.
\]

### Hufnagel–Valley/Rytov và broadening

Profile được tính độc lập:
\[
C_n^2(h)=0.00594(v/27)^2(10^{-5}h)^{10}e^{-h/1000}+2.7\times10^{-16}e^{-h/1500}+C_n^2(0)e^{-h/100}.
\]
v=21m/s, Cn2(0)=1e-14m^(-2/3), h trong mét. Các tích phân và công thức dùng đúng code hiện hành:
\[
J_R=\int_{1000}^{20000} C_n^2(h)(h-1000)^{5/6}dh,
\quad \sigma_R^2=2.25k^{7/6}\sec^{11/6}\zeta\ J_R,\quad k=2\pi/\lambda.
\]
\[
\mu_2=\int_{1000}^{20000}C_n^2(h)((h-1000)/19000)^{5/3}dh,
\quad \Lambda_L=2L/(kw_L^2),
\]
\[
G_d=4.35\Lambda_L^{5/6}k^{7/6}(19000)^{5/6}\sec^{11/6}\zeta\ \mu_2,
\quad w_{L,eff}=w_L\sqrt{1+G_d}.
\]

| Auxiliary | Independent value |
|---|---|
| wave_number_per_m | 4053667.9401158621 |
| rytov_integral | 3.5993391631024063e-10 |
| sigma_R2 | 0.053962077796165596 |
| mu2_integral | 5.0349262957777168e-14 |
| beam_lambda | 0.49721062350410394 |
| G_d | 0.029985462263114906 |
| w_eff_m | 0.14974341909718894 |

\[
G_d
=4.35(0.49721062350410394)^{5/6}(4053667.9401158621)^{7/6}19000^{5/6}(1.1547005383789473)^{11/6}(5.0349262957777168e-14)
=0.029985462263114906.
\]

\[
w_{L,eff}
=0.14754761631878588\sqrt{1+0.029985462263114906}
=0.14974341909718894.
\]

Aperture averaging cũng được tính nhưng không đi vào sigma_R² của active Literal PDF:
\[
J_2=\int C_n^2(h)h^2dh,\quad J_{5/6}=\int C_n^2(h)h^{5/6}dh,\quad
\Phi_m=(J_2/J_{5/6})^{6/7},
\]
\[
A_{ap}=[1+1.11(D_r^2/(\lambda\Phi_m\sec\zeta))^{7/6}]^{-1},\quad v_{sc}=A_{ap}\sigma_R^2.
\]

| Quantity | Independent value |
|---|---|
| aperture_numerator | 1.8307834031742625e-05 |
| aperture_denominator | 4.3469721253605587e-10 |
| Phi_m | 9200.5625281323919 |
| A_ap | 0.029306517552841332 |
| v_sc_unused_in_active_PDF | 0.0015814405801211167 |

Active LiteralChannel.from_physical dùng raw sigma_R0_squared≈.053962..., không dùng aperture-averaged v_sc≈.00158144. Đây là mode-specific choice có sẵn. Không trộn hai PDF/scintillation branches. G_d được audit theo công thức implementation; citation/physical calibration của broadening vẫn là giới hạn đã ghi trong code, không được numerical matching tự chứng nhận.
### Aperture collection, pointing và AoA
\[
v=\sqrt\pi D_r/(2\sqrt2\,w_{L,eff}),\quad A_0=\operatorname{erf}^2(v),\quad
w_{L,eq}=\sqrt{w_{L,eff}^2\sqrt\pi\operatorname{erf}(v)/(2v e^{-v^2})}.
\]

\[
v
=\sqrt\pi(0.55)/(2\sqrt2\,0.14974341909718894)
=2.301679698779048.
\]

\[
A_0
=(0.99886634240679539)^2
=0.99773396999312947.
\]

\[
w_{L,eq}
=\sqrt{(0.14974341909718894)^2\sqrt\pi(0.99886634240679539)/(2(2.301679698779048)(e^{-(2.301679698779048)^2}))}
=1.3129215957938436.
\]

\[
\sigma_{jt}=L\theta_{jt}
=21939.3102292(15.61\times10^{-6})
=0.34247263267781197.
\]

\[
\sigma_s=\sqrt{\sigma_h^2+\sigma_{jt}^2}
=\sqrt{1^2+(0.34247263267781197)^2}
=1.0570182137187947.
\]

\[
\chi_p=w_{L,eq}/(2\sigma_s)
=1.3129215957938436/(2(1.0570182137187947))
=0.62104965588754202.
\]

Pointing chi_p²=0.3857026750780343; đây không phải Holevo chi_BE.
\[
P_0
=\exp[-(0.00625)^2/(2(0.0015)^2)]
=0.00016985667656141065.
\]

\[
P_1
=1-0.00016985667656141065
=0.99983014332343856.
\]

Atom P0 delta(eta) được giữ riêng. Các positive-power moments không nhận đóng góp từ atom0. Không bỏ P0, không biến nó thành continuous density.

### Hai aperture intermediates khác nhau trong runtime

manuscript_pointing_parameters:148–156 tính nu theo w_L chưa broadened, trả A0/weq metadata. LiteralChannel.from_physical:86–95 tính lại nu theo w_eff và dùng kết quả đó làm active raw PDF. Không được lấy nhầm metadata intermediate thay active PDF value.

| Quantity | First pointing metadata runtime | Active LiteralChannel runtime | Independent active |
|---|---|---|---|
| nu | 2.3359332828332513 | 2.3016796988061117 | 2.301679698779048 |
| A0 | 0.99809125040703939 | 0.99773396999343456 | 0.99773396999312947 |
| w_eq | 1.4111227269002553 | 1.312921595852572 | 1.3129215957938436 |

## C. Fading PDF and moments

Runtime rho=0 được kiểm tra rõ. Đặt d=chi_p², B=A0 eta_atm:
\[
C_1=e^{\sigma_R^2d(1+d)/2},\quad C_3=(2\sigma_R^2)^{-1/2},\quad
\mu=\sigma_R^2(1+2d)/2,\quad x_1=-\ln B+\mu.
\]

| Coefficient | Independent value |
|---|---|
| B | 0.90615093665002078 |
| C1 | 1.0145250125664589 |
| C3 | 3.0439721195155762 |
| mu | 0.047794356656832869 |
| x1 | 0.14634374672773473 |
| d | 0.3857026750780343 |

Raw PDF gồm atom và continuous term:
\[
f_{raw}(\eta)=P_0\delta(\eta)+\frac{P_1dC_1}{2B^d}\eta^{d-1}
\operatorname{erfc}[C_3(\ln(\eta/B)+\mu)].
\]

Thay số MP: 0.00016985667656141065 delta(eta) + 0.20319803544991463 eta^(-0.61429732492196565) erfc[3.0439721195155762(ln(eta/0.90615093665002078)+0.047794356656832869)]. C1 channel PDF khác C của exact source Denys.

\[
Q(a)=\tfrac12[e^{ax_1-a\mu}\operatorname{erfc}(C_3x_1)+
e^{a^2/(4C_3^2)-a\mu}\operatorname{erfc}(a/(2C_3)-C_3x_1)].
\]

| Q value | Independent result |
|---|---|
| Q_chi2 | 0.97002766541408547 |
| Q_chi2_plus_half | 0.9388545878232667 |
| Q_chi2_plus_one | 0.91513546373513399 |

Eq19–20 RAW [0,1] moments:
\[
m_{1,raw}=P_1B\frac{dC_1}{d+1}Q(d+1),\quad
m_{1/2,raw}=P_1\sqrt B\frac{dC_1}{d+1/2}Q(d+1/2).
\]

\[
m_{1,raw}
=(0.99983014332343856)(0.90615093665002078)\frac{(0.3857026750780343)(1.0145250125664589)}{1.3857026750780344}(0.91513546373513399)
=0.23413023965143001.
\]

\[
m_{1/2,raw}
=(0.99983014332343856)\sqrt{0.90615093665002078}\frac{(0.3857026750780343)(1.0145250125664589)}{0.88570267507803435}(0.9388545878232667)
=0.39477740140367801.
\]

Active retained mass F_active=C1 Q(d). Raw total [0,1] mass=P0+P1 F_active. Existing PhysicalFadingDistribution giữ P0 và condition riêng active component: physical f_cont=f_raw,cont/F_active trên(0,1]. Đây là lựa chọn đã có và được config/receipt nêu rõ, không phải renormalization mới để cứu kết quả. Raw lognormal extension trên eta>0 có total mass1; phần thiếu trên[0,1] là mass eta>1 của surrogate. Nếu dùng raw Eq19 đơn lẻ, không thu được runtime conditioned m1≈.2379089.

| Quantity/law | Independent closed | Independent quadrature | Relative error |
|---|---|---|---|
| raw_mass | 0.9841200272216735 | 0.9841200272216732 | 2.256275645074497e-16 |
| raw_m1 | 0.23413023965143 | 0.23413023965142996 | 2.3709517964831065e-16 |
| raw_mhalf | 0.394777401403678 | 0.394777401403678 | 0.0 |
| physical_m1 | 0.2379088678213789 | 0.23790886782137888 | 1.1666473750977494e-16 |
| physical_mhalf | 0.40114871427647913 | 0.40114871427647913 | 0.0 |
| physical_mxi | 0.004425104941477648 | 0.004425104941477647 | 1.9600930361185308e-16 |

\[
F_{active}=C_1Q(d)
=(1.0145250125664589)(0.97002766541408547)
=0.98411732944403785.
\]

\[
m_{1,physical}=m_{1,raw}/F_{active}
=0.23413023965143001/0.98411732944403785
=0.23790886782137891.
\]

\[
m_{1/2,physical}=m_{1/2,raw}/F_{active}
=0.39477740140367801/0.98411732944403785
=0.40114871427647913.
\]

\[
m_\xi=\xi_{ch}m_1
=0.0186(0.23790886782137891)
=0.0044251049414776476.
\]

Independent raw mass=0.98412002722167347, deficit=0.015879972778326548; active tail≈0.01588267055596209; full raw positive-support mass including atom=0.99999999999999978. Physical conditioned total=1. Both methods giữ atom0 explicit. Tolerance CF/quadrature: relative1e-10 hoặc absolute2e-13, với adaptive error estimates được lưu; không nới sau kết quả.
Runtime original quad cho G_d hơi khác MP: raw m1=0.23413023966620677, active norm=0.98411732944264829; raw m1/norm=0.2379088678367301. Độc lập thay đúng original mu2 quadrature vào cùng công thức tái dựng được m1=0.23790886783673018. Vì vậy .2379089 truy được về primitives và integration, không phải chỉ từ cache PASS. Phần khác nhau1.535e-11 được điều tra ởI.
## D. Effective channel

Các dòng sau dùng independent high-precision chain, kèm runtime ở bảng so sánh. Channel excess không chứa chi_line, chi_tot hoặc detector noise.

\[
\eta_f=m_{1/2}^2
=(0.40114871427647913)^2
=0.16092029096567229.
\]

\[
\operatorname{Var}(\sqrt\eta)=m_1-\eta_f
=0.23790886782137891-0.16092029096567229
=0.07698857685570662.
\]

\[
E_{fading}=(m_1-\eta_f)V_A
=(0.07698857685570662)5.046875
=0.38855172381864433.
\]

\[
E_{channel}=m_\xi
=0.0186(0.23790886782137891)
=0.0044251049414776476.
\]

\[
N_{eff}=\eta_f\xi_f
=0.38855172381864433+0.0044251049414776476
=0.39297682876012202.
\]

\[
\xi_f=N_{eff}/\eta_f
=0.39297682876012202/0.16092029096567229
=2.4420589001044766.
\]

\[
r_{fading}=100E_{fading}/N_{eff}
=100(0.38855172381864433)/(0.39297682876012202)
=98.873952707227232.
\]

Runtime nguyên bản: tử số=0.38855172381411168, mẫu số=0.39297682875587486, ratio=98.873952707142394%. Tuyên bố98.87% đúng khi làm tròn; không phải từ total noise hoặc detector.
## E. Covariance

Exact source nu_raw=0.17000000000000001, VA=5.046875; C=2.9818069279923307, w=6.1909456504525073e-07; ensemble hash b2dde0f1bdf8c14fefedc304926b6524b79e0628d577af2b387a55e975f9205b; payload hash e6e1b9ef8be95c72e3328966edde7b7c9e3d9bb885d3171e4927cbcb13d70317. Không build/source worker mới, không nội suy C,w.
\[
V=V_A+1
=5.046875+1
=6.046875.
\]

\[
W_{pre}=1+\eta_fV_A+N_{eff}
=1+(0.16092029096567229)5.046875+0.39297682876012202
=2.2051214222274993.
\]

\[
W_{pre}=1+m_1(V_A+\xi_{ch})
=1+(0.23790886782137891)(5.046875+0.0186)
=2.2051214222274993.
\]

\[
Z_{base}=2\sqrt{\eta_f}C
=2\sqrt{0.16092029096567229}(2.9818069279923307)
=2.3922960307696428.
\]

\[
Z_{correction}=\sqrt{2N_{eff}w}
=\sqrt{2(0.39297682876012202)(6.1909456504525073e-07)}
=0.00069755260572104477.
\]

\[
Z=Z_{base}-Z_{correction}
=2.3922960307696428-0.00069755260572104477
=2.3915984781639219.
\]

Gamma_AB=[[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]]. Full matrix và spectra ở high_precision_SKR.json. Kiểm tra riêng positive covariance, Gamma+iOmega, closed symplectic spectrum so direct iOmegaGamma; không clip Z/covariance để làm hợp lệ.
| Metric | Independent A value |
|---|---|
| min eigenvalue Gamma+iOmega | 0.35091351052616659 |
| closed vs matrix symplectic residual | 2.897817305224548e-70 |

## F. Mutual information and Holevo

Nguồn256 labels: p_k proportional exp(-nu_raw*|raw_grid|²), raw_grid=(i-7.5)+j(l-7.5). nu_repo=42.5nu_raw. Physical alpha_k=raw_grid*sqrt(VA/(2 sum p|raw_grid|²)), nên VA=2sum p|alpha|². Arrays256 xác suất/amplitudes nguyên precision nằm trong runtime_probe.json; exact ensemble/source hash được xác thực, không Gaussian-modulated substitution.

Independent audit tái sử dụng numerical functions của scripts/audit_negative_skr_independent.py đã được tách khỏi production: direct full256 complex likelihood GH16/32/48 và independent adaptive quadrature trên real marginals sau factorization check. File này không import production MI/Holevo helpers. Geometry/PDF ở task này được viết mới từ primitives. Không dùng old SKR result làm input.

\[
p(y|\alpha_k)=\frac{1}{\pi\sigma_c^2}e^{-|y-\sqrt{\eta_B\eta_f}\alpha_k|^2/\sigma_c^2},
\quad\sigma_c^2=1+\nu_B+\eta_BN_{eff}/2.
\]
\[
I=\sum_kp_k\int_{\mathbb C}p(y|\alpha_k)\log_2\frac{p(y|\alpha_k)}{\sum_jp_jp(y|\alpha_j)}d^2y.
\]

Complex variance sigma_c² nghĩa mỗi real quadrature có variance sigma_c²/2. Gain channel sqrt(eta_f), detector sqrt(eta_B). Heterodyne vacuum contribution1 và electronic noise nu_B được cộng đúng một lần. Ln được chia ln2. Đây là effective Gaussian likelihood, không true pooled-fading mixture MI.

| Detector | Channel amplitude gain | Detector amplitude gain | Complex variance | Per-real variance | I_AB | beta I_AB | GH32/48 difference |
|---|---|---|---|---|---|---|---|
| ideal_primary | 0.40114871427647913 | 1 | 1.1964884143800609 | 0.59824420719003046 | 0.42157258492356747 | 0.4004939556773891 | 0 |
| trusted_diagnostic | 0.40114871427647913 | 0.83666002653407556 | 1.1510418900660426 | 0.57552094503302131 | 0.31840443438760091 | 0.30248421266822084 | 1.1102230246251565e-16 |

Holevo independent dùng Delta=V²+W²-2Z², D=(VW-Z²)²; nu1,2=sqrt((Delta +/- sqrt(Delta²-4D))/2). Ideal conditional nu3=V-Z²/(W+1). Delta/D được tính lại dưới đây, không đọc từ production covariance helper. S(AB)=sum g((nu1,2-1)/2); S_cond được trừ, không cộng.

| Quantity | Independent ideal A |
|---|---|
| Delta | 29.987771190879648 |
| D | 57.978330784657338 |
| nu1 | 5.283036505104068 |
| nu2 | 1.4412829273315673 |
| nu3 het | [4.2623113197944393] |

Trusted detector dùng upsilon=1+2nu_B/(1-eta_B), V_B2=eta_BW+(1-eta_B)upsilon. Tạo independent AFG/C blocks từ beam splitter/EPR AppendixA, condition Gamma_AFG-C(Gamma_B2+I)^(-1)C^T và lấy3 symplectic eigenvalues, không dùng ideal nu3. Ancillas được giả định trusted/độc lập Eve; đây không phải calibration chứng minh từ phép đo.

| Quantity | Independent ideal A | Independent trusted A |
|---|---|---|
| lambda_1 | 5.283036505104068 | 5.283036505104068 |
| lambda_2 | 1.4412829273315673 | 1.4412829273315673 |
| conditional_eigenvalues | [4.2623113197944393] | [1, 1.1101285398242504, 4.4990030153218932] |
| S_AB_terms | [2.8353531906054847, 0.8321525541689706] | [2.8353531906054847, 0.8321525541689706] |
| S_AB | 3.6675057447744552 | 3.6675057447744552 |
| conditional_entropy_terms | [2.5208712618927565] | [0, 0.31190856095705655, 2.6002407451612966] |
| conditional_entropy | 2.5208712618927565 | 2.9121493061183532 |
| chi_BE | 1.146634482881699 | 0.75535643865610214 |
| chi_upper | 3.0614259788216649 | 3.0614259788216649 |

Cả8 covariance/detector cases đều đạt physicality và chi<=2g((Wpre-1)/2), không clip Holevo. Bound là necessary consistency check, không phải tightness hoặc security-proof certificate. So printed chi≈1.146634/.755356 khớp; sai khác ~1e-11 của independent chain so runtime được giải thích bằngmu2, không nhầm receiver hoặc log base.
## G. SKR

ideal_primary:
\[
K_{ind}=0.95I_{ind}-\chi_{ind}
=0.95(0.42157258492356747)-1.146634482881699
=-0.74614052720430979.
\]

\[
K_{runtime}=0.95I_{runtime}-\chi_{runtime}
=0.95(0.4215725849611287)-1.1466344829084623
=-0.74614052719539004.
\]

Independent minus runtime K=-8.9197538244434327e-12 bits/use. beta*MI=0.4004939556773891<chi=1.146634482881699; rate âm trong cả hai phép tính. Không chỉnh hardware/noise/source để ép dương.
trusted_diagnostic:
\[
K_{ind}=0.95I_{ind}-\chi_{ind}
=0.95(0.31840443438760091)-0.75535643865610214
=-0.45287222598788129.
\]

\[
K_{runtime}=0.95I_{runtime}-\chi_{runtime}
=0.95(0.31840443441681998)-0.75535643867863644
=-0.45287222598265747.
\]

Independent minus runtime K=-5.2238213754662866e-12 bits/use. beta*MI=0.30248421266822084<chi=0.75535643865610214; rate âm trong cả hai phép tính. Không chỉnh hardware/noise/source để ép dương.
## H. Configuration sensitivity

Chỉ4 cases x2 receiver với cùng exact source/primitive atmospheric/motion inputs. Mỗi case tính fresh, không dùng objective cache. A là config đang chạy; B/C/D là diagnostics theo user, không ghi vào production configuration.

| Case | Dr m | Full-angle urad | w0 | wL | w_eq | A0 | sigma_s | pointing chi² |
|---|---|---|---|---|---|---|---|---|
| A | 0.55000000000000004 | 10 | 0.098676064716975112 | 0.14754761631878588 | 1.3129215957938436 | 0.99773396999312947 | 1.0570182137187947 | 0.3857026750780343 |
| B | 0.080000000000000002 | 233 | 0.0042350242367800474 | 2.555933150291724 | 2.5565913072600046 | 0.00048958417445276099 | 1.0570182137187947 | 1.4625060891170982 |
| C | 0.55000000000000004 | 233 | 0.0042350242367800474 | 2.555933150291724 | 2.5718196925986696 | 0.022868278006622972 | 1.0570182137187947 | 1.4799808703600605 |
| D | 0.080000000000000002 | 10 | 0.098676064716975112 | 0.14754761631878588 | 0.15548695760579603 | 0.13258191195557179 | 1.0570182137187947 | 0.0054095731618025071 |

| Case | m1 | eta_f | xi_f | W_pre | Z | I ideal | chi ideal | K ideal | K trusted |
|---|---|---|---|---|---|---|---|---|---|
| A | 0.23790886782137891 | 0.16092029096567229 | 2.4420589001044766 | 2.2051214222274993 | 2.3915984781639219 | 0.42157258492356747 | 1.146634482881699 | -0.74614052720430979 | -0.45287222598788129 |
| B | 0.00026403393702785954 | 0.00024354548877273714 | 0.44473691162212892 | 1.0013374573071663 | 0.093056243288312676 | 0.00088631939018465151 | 0.0015943167103623082 | -0.00075231328968688928 | -0.0004912016334547287 |
| C | 0.012392337848559115 | 0.011444664261479859 | 0.43804584426713222 | 1.0627730775634301 | 0.63790705854323149 | 0.040973323594095556 | 0.059865914928012021 | -0.020941257513621241 | -0.013191646139340154 |
| D | 0.00064776319891116758 | 1.3605130943901468e-05 | 236.12892136198687 | 1.0032812282900045 | 0.021933799983696503 | 4.9449890560688542e-05 | 0.017272210615157907 | -0.017225233219125252 | -0.011062322975862621 |

ChỉA cho m1≈.2379089. B cho m1≈.000264034, đúng bậc1e-4 của hardware cũ nhưng không được coi trùng exact một con số minh họa từ configuration khác. Default223urad khác caseB233urad; không đổi tên chúng cho khớp kết quả mong muốn.
| Case | Reconstructed geometry fingerprint |
|---|---|
| A | 61476619a452852eb311bfc1099041a571da53e851bb585911d5650a3f7148b4 |
| B | afe45c172cb7e463fe67572365d151eeb2242f87f4bb3da64f8c59cae2e07e8b |
| C | da38ad5f44207a4bb948313caac757762d20d3dcb67b841867f26ab372d978af |
| D | d31437fa8b6b06c0561b936e2a5c3dd10802b48dd7fc85e4d8968c04f8007d59 |

## I. Final verdict, strict FAILs và tác động định lượng

**CONFIGURATION_MATCH_CONFIRMED:** trace hiệu lực Dr=.55/full-angle10urad, fresh physical-state equality và zero residual fresh/historical reference SKR cùng xác nhận hardware. Không có CONFIGURATION_MISMATCH ở reference.

**MOMENT_MISMATCH, scope strict high-precision comparison:** không che5 FAIL trong independent_geometry_audit.json. Các phép CF/quadrature độc lập cùng luật đều khớp; discrepancy so runtime đến từ accuracy quadrature phụ mu2, không phải dùng sai hardware hoặc moment convention.

| Original strict check | Outcome | Detail |
|---|---|---|
| A_geometry_runtime_agreement | FAIL | {"L_m": 0.0, "zeta_rad": 0.0, "eta_atm": -1.1102230246251565e-16, "w0_m": 1.3877787807814457e-17, "wL_m": -2.7755575615628914e-17, "G_d": 2.4221669808754953e-11, "A0": -3.05089287166993e-13, "w_eq_m": -5.87283555120166e-11, "sigma_s_m": 0.0, "sigma_R2": -1.0408340855860843e-16, "P0": 2.710505431213761e-19, "A_ap": 2.7755575615628914e-17, "v_sc_unused_in_active_PDF": -1.5178830414797062e-18} |
| A_closed_runtime_moments | FAIL | null |
| D_geometry_runtime_agreement | FAIL | {"L_m": 0.0, "zeta_rad": 0.0, "eta_atm": -1.1102230246251565e-16, "w0_m": 1.3877787807814457e-17, "wL_m": -2.7755575615628914e-17, "G_d": 2.4221669808754953e-11, "A0": -2.8917701566655296e-12, "w_eq_m": 1.6896206656014101e-12, "sigma_s_m": 0.0, "sigma_R2": -1.0408340855860843e-16, "P0": 2.710505431213761e-19, "A_ap": 1.1102230246251565e-16, "v_sc_unused_in_active_PDF": -6.938893903907228e-17} |
| D_ideal_primary_independent_SKR_agreement | FAIL | {"W_pre": -6.661338147750939e-16, "Z": 2.330774462322438e-13, "eta_f": 2.8829105172979014e-16, "xi_f": -5.15734654982225e-09, "I_AB": 1.9159614216349152e-15, "chi_BE": -7.577272143066693e-15, "K_raw": 9.398731792842341e-15} |
| D_trusted_diagnostic_independent_SKR_agreement | FAIL | {"W_pre": -6.661338147750939e-16, "Z": 2.330774462322438e-13, "eta_f": 2.8829105172979014e-16, "xi_f": -5.15734654982225e-09, "I_AB": 2.5017694079559893e-15, "chi_BE": -5.755812493291046e-15, "K_raw": 8.132383655379272e-15} |

Audit trước tự tích phân PDF từ raw channel parameters đã lưu và kiểm MI/Holevo trên các moment đó; chưa tái dựng Gd từ primitive turbulence inputs. Audit hiện tại đi thêm bước này. Vì vậy residual SKR khoảng9e-12 ở đây không mâu thuẫn với residual khoảng9e-15 của audit trước và không có bằng chứng cache/evaluator version bị trộn.

Root của sai khác Gd: src/channel/pointing_error.py:124–136, manuscript_pointing_parameters, quad(...epsabs=1e-18,epsrel=2e-13). Mu2 chỉ cỡ5e-14; absolute tolerance cho phép dừng trước khi đạt relative target. Giữ nguyên code này, probe chẩn đoán capture original value/error rồi tính lại integrand riêng với epsabs1e-28. Không thay kết quả runtime hoặc production tolerance.

| mu2 calculation | Value | Reported absolute error |
|---|---|---|
| Original production quadrature | 5.0349262917105936e-14 | 2.3818994966625489e-19 |
| Independent70dps | 0.00000000000005034926295777716499811767830693570915664790917938113232172369531 | arithmetic precision; not physical accuracy |
| Diagnostic tighter SciPy quadrature | 5.0349262957777212e-14 | 3.0292258760486853e-28 |

Original minus MP mu2=-4.0671228998117678e-23, nằm trong original error estimate. Gd independent-runtime=2.4221669808754953e-11; A m1 difference=-1.5351248050521349e-11. D xi_f difference≈-5.157e-9 chỉ là relative≈-2.184e-11 vì eta_f nhỏ; SKR D difference≈9e-15. Năm initial FAIL không bị đổi tolerance hoặc rewrite thành PASS.
Causal test thay chỉ mu2 original vào independent geometry dựng lại runtime Gd/m1/mhalf cho cả4 cases với residual<1e-13. Các check riêng theo đúng đại lượng xác nhận cả8 signed SKRs chênh<1e-9. Đây là giải thích uncertainty/cause, không hủy strict FAIL. quadrature_precision_diagnosis.json lưu toàn bộ hai bộ kiểm tra.
**NUMERICALLY_CONSISTENT, scope:** closed-form vs independent quadrature của raw/conditioned PDF, moment identities, covariance/noise accounting, independent MI/Holevo và signed SKR đến sai số đã định lượng. Không có evidence NOISE_ACCOUNTING_ERROR, HOLEVO_ERROR hoặc MI_ERROR gây dấu âm. Không tuyên bố toàn bộ94 strict checks đều PASS:89 PASS,5 FAIL được báo đủ;18 causal/metric/AoA follow-up checks PASS.

**UNVALIDATED_SECURITY_MODEL:** numerical/configuration confirmation không thiết lập security proof cho discrete modulation fading. Hosseinidehaj hỗ trợ Gaussian-modulation fading covariance/receiver; exact Denys C,w/correlation constraints giữ nguyên. Gaussian-surrogate MI không được tự đồng nhất true pooled-fading MI hoặc lower bound đã chứng minh; directZ không được tự chứng nhận full-interval worst case. Trusted-DM composition, calibration, operational/finite-size/composable scope vẫn chưa xác lập.

Khuyến nghị tối thiểu nếu cần matching ở precision cao hơn: một task sau có thể scale integrand mu2 hoặc giảm epsabs tương xứng khoảng1e-28 và prospectively kiểm regression. Đây là numerical refinement, không phải thay physical model để cứu SKR; tác động reference K hiện chỉ khoảng9e-12. **Chưa sửa production; chờ xác nhận riêng trước bất kỳ thay đổi nào.**

Sources: [Hosseinidehaj v1 Eq4–7/AppendixA](https://arxiv.org/pdf/2002.03476.pdf), [Denys2021](https://quantum-journal.org/papers/q-2021-09-13-540/pdf/); bản thảo thực tế dùng để đối chiếu là2026__Binh_s_work (38).pdf (SHA0c60153c...be0a0), requested(38)(3) không có. Công thức Gd tái lập từ repo, bibliography/calibration ngoài code chưa được xác nhận. Frozen actual hashdf83ea63...78c15 vẫn khác historical AGENTS; không sửa. NOT_READY_FOR_PUBLICATION_SCALE_RUNS và ObjectiveC USER_STOPPED giữ nguyên.

Artifacts: runtime_probe.json (arguments/return objects, original defaults/CLI/env), independent_geometry_audit.json (4 independent chains và94 checks), high_precision_common_geometry.json/high_precision_SKR.json, moments_closed_vs_quadrature.csv, runtime_parameters.csv, configuration_sensitivity.csv, SKR_entropy_decomposition.csv và quadrature_precision_diagnosis.json. Các file nằm trong results/full_geometry_fading_skr_audit_20261017/. Runtime probe script và independent audit script là2 file mới riêng; không sửa source/Cw/config/frozen specifications hoặc output cũ. Không full-catalog/mission/optimizer, training/test access, publication/baseline/threshold promotion, external edits hoặc commit/push. Audit complete; STOP.

