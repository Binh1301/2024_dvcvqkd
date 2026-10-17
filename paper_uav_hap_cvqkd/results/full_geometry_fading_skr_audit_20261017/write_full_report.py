"""Render the full audit including preserved strict numerical failures."""
import csv,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
runtime=read(OUT/'runtime_probe.json');audit=read(OUT/'independent_geometry_audit.json');precision=read(OUT/'quadrature_precision_diagnosis.json')
A=audit['cases'][0];g=A['geometry'];f=A['fading'];ind=A['quantum'];state=runtime['cases'][0]['state'];physical=state['physical'];mom=state['moments'];live=runtime['cases'][0]['production_results'];source=runtime['source'];defaults=runtime['defaults']['channel']
fmt=lambda x: '['+', '.join(fmt(z) for z in x)+']' if isinstance(x,list) else '—' if x is None else f'{x:.17g}' if isinstance(x,(float,int)) else str(x)
lines=[]
def add(x=''):lines.append(x)
def table(headers,rows):
    add('| '+' | '.join(headers)+' |');add('|'+'|'.join(['---']*len(headers))+'|')
    for row in rows:add('| '+' | '.join(fmt(x) for x in row)+' |')
    add()
def formula(eq,sub,value):add('\\[\n'+eq+'\n='+sub+'\n='+fmt(value)+'.\n\\]\n')

add(r'''# Full Numerical Audit of HAP–UAV Geometry, Fading Moments and SKR

Ngày2026-10-17. Task b8e5bb91. Audit-only: không sửa production code/config/source, không chạy22.700 điểm hoặc1.600 missions, không commit/push.

Kết luận hardware: **CONFIGURATION_MATCH_CONFIRMED**. Reference âm được tạo với Dr=.55m và divergence full-angle10urad. Không có evidence rằng reference này lấy từ hardware cũ. Có **5 FAIL strict comparisons được giữ nguyên**, truy về độ chính xác tích phân phụ mu2 và sensitivity của input-referred xi_f; chúng không đổi dấu hoặc độ lớn SKR. Không gọi toàn bộ audit là một PASS chung. **UNVALIDATED_SECURITY_MODEL** giữ nguyên.

## A. Actual runtime configuration

Probe scripts/probe_full_geometry_runtime.py rebuild từ configuration files qua clear_state -> channel_state -> derive_physical_inputs -> manuscript_pointing_parameters -> LiteralChannel.from_physical -> PhysicalFadingDistribution.moments, rồi evaluate_candidate của trusted_heterodyne_skr. Sys.setprofile lưu arguments và return objects thực tế trong runtime_probe.json; không kết luận từ một literal trong file.

Runtime primary dùng configs/binary_cloud_skr_demo.json; derive_physical_inputs đọc configs/default.yaml rồi nhận explicit aperture/beam-waist/zenith/tau overrides. Các thông số turbulence/UAV/AoA còn lại lấy từ default.yaml. Source pair lấy đúng reference_pair trong configs/fading_effective_binary_cloud.json. Trusted alternate lấy riêng từ configs/manuscript_corrected_3moments.json; không đổi thành primary.
''')
params=[
('Dr',2*defaults['aperture_radius_m'],physical['receiver_diameter_m'],'m','default.yaml -> binary_cloud.channel.receiver_radius_m x2'),
('r_ap',defaults['aperture_radius_m'],physical['receiver_radius_m'],'m','same; derive_physical_inputs override'),
('theta_div',defaults['theta_div_rad'],physical['theta_div_rad'],'rad, full angle','default.yaml -> derived from configured beam_waist override'),
('lambda',defaults['wavelength_m'],physical['wavelength_m'],'m','default.yaml.channel.wavelength_m'),
('w0',defaults['beam_waist_m'],physical['beam_waist_m'],'m','binary_cloud.channel.beam_waist_m'),
('h_HAP',defaults['h_hap_m'],physical['h_hap_m'],'m','default.yaml + explicit geometry equality check'),
('h_UAV',defaults['h_uav_m'],physical['h_uav_m'],'m','same'),
('zeta',defaults['zenith_angle_rad'],physical['zenith_angle_rad'],'rad','grid/HAP coordinates -> link_geometry override'),
('sigma_h',defaults['pointing']['sigma_h_m'],physical['sigma_h_m'],'m per axis','default.yaml.pointing.sigma_h_m'),
('theta_jt',defaults['pointing']['theta_jt_rad'],physical['theta_jt_rad'],'rad per axis','default.yaml.pointing.theta_jt_rad'),
('Cn2(0)',defaults['turbulence_profile']['cn2_ground_m_minus_two_thirds'],physical['cn2_ground_m_minus_two_thirds'],'m^(-2/3)','default.yaml.turbulence_profile'),
('wind',defaults['turbulence_profile']['wind_speed_m_per_s'],physical['wind_m_per_s'],'m/s','same'),
('sigma_o',defaults['aoa']['sigma_o_rad'],physical['sigma_o_rad'],'rad','default.yaml.aoa.sigma_o_rad'),
('theta_FOV',defaults['aoa']['theta_fov_rad'],physical['theta_fov_rad'],'rad half-angle','default.yaml.aoa.theta_fov_rad'),
('xi_ch',defaults['excess_noise_distribution']['epsilon_ch_snu'],mom['xi_ch'],'SNU input channel excess','binary_cloud.channel.xi_ch'),
('eta_B primary','function default1',runtime['detectors']['ideal_primary']['eta_B'],'unitless','binary_cloud.channel.R'),
('nu_B primary','function default0',runtime['detectors']['ideal_primary']['nu_B'],'SNU output per detected arm','binary_cloud.channel.xi_det'),
('eta_B diagnostic','historical config.7',runtime['detectors']['trusted_diagnostic']['eta_B'],'unitless','manuscript_corrected_3moments.json.R'),
('nu_B diagnostic','historical config.0135',runtime['detectors']['trusted_diagnostic']['nu_B'],'SNU','same.xi_det'),
('tau_zen',defaults['tau_zen'],physical['tau_zen'],'power','explicit binary config.clear_tau_zen'),
('F0','infinity','infinity','m','default.yaml.radius_of_curvature_m')]
table(['Parameter','Default/source configuration','Runtime actual','Unit','Source'],params)
with (OUT/'runtime_parameters.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['parameter','default','runtime','unit','source']);writer.writerows(params)
add(r'''Default.yaml hiện là223urad, không phải233urad.233urad là old-manuscript case được user yêu cầu chẩn đoán. Default Dr=.08m/theta223urad không được dùng cho reference vì explicit override Dr=.55/w0=.098676... thắng. Default tau_zen=null còn yêu cầu chọn atmosphere rõ ràng. UavMotion dataclass có legacy defaults khác; channel builder explicitly truyền sigma_h/sigma_o hiện hành, không lấy dataclass defaults.

CLI historical runner chỉ có --stage và --output, không có geometry/physics flags. Hàm load_yaml đọc YAML trực tiếp, không environment substitution; static search trên dependency path không phát hiện os.environ/getenv cho physics. Runtime arguments/return objects còn xác nhận effective values. Historical argv/env chưa lưu nguyên gốc; đây là reconstructed trace với input/producer hash matching, không giả vờ truy xuất process cũ.

Không có eta_B=.8 trong active receiver configs. Giá trị.8 trong probability sweep là cloud probability, không phải detector efficiency. Primary(1,0) và trusted diagnostic(.7,.0135) được tách riêng ở mọi bảng.

10urad=1e-5rad; Dr=.55m -> r_ap=.275m. Với full-angle theta dùng w0=2lambda/(pi theta). Nếu dùng half-angle theta_half=theta_full/2, công thức tương đương là lambda/(pi theta_half), không dùng lẫn hệ số2.

Fresh reconstructed A bằng toàn bộ cached clear physical state ở reference44; producer/receipt hashes của evaluator trước đều khớp. Hai SKRs freshA có residual0 so reference artifact cũ. Geometry fingerprint mới lưu đầy đủ Dr/theta/w0, primitives, raw channel và source producers. Không dùng cached objective thiếu fingerprint để tính8 kết quả mới; source cache C,w độc lập geometry được xác thực riêng.

## B. Geometric and atmospheric calculations

Mọi phép tính độc lập ở scripts/audit_full_geometry_fading_skr.py bắt đầu từ primitive config/coordinates, không từ production intermediate. Mpmath70dps tự tích phân profile; không import geometry/channel/moment helpers production. Trong các bảng, cột MP là independent high-precision chain; sai khác với runtime được giữ, không thay số MP thành số cũ.
''')
formula(r'\zeta=\arctan(r_\perp/\Delta h)',rf'\arctan({fmt(g["horizontal_distance_m"])}/19000)',g['zeta_rad'])
add(f"zeta={fmt(g['zeta_deg'])} degree. Geometry embedding không ép chính xác30degree; khác nhỏ do tọa độ HAP được lưu hữu hạn.")
formula(r'L=(h_{HAP}-h_{UAV})\sec\zeta',rf'(20000-1000)\times {fmt(g["secant"])}',g['L_m'])
formula(r'\eta_{atm}=\tau_{zen}^{\sec\zeta}',rf'0.92^{{{fmt(g["secant"])}}}',g['eta_atm'])
formula(r'w_0=2\lambda/(\pi\theta_{div})',r'2(1.55\times10^{-6})/(\pi\,10^{-5})',g['w0_m'])
formula(r'z_R=\pi w_0^2/\lambda',rf'\pi({fmt(g["w0_m"])})^2/(1.55\times10^{{-6}})',g['rayleigh_m'])
add(r'''F0=infinity nên focusing factor1-L/F0=1, L dùng mét. Beam propagation:
\[
w_L=w_0\sqrt{(1-L/F_0)^2+(L\lambda/(\pi w_0^2))^2}.
\]
''')
formula('w_L',rf'{fmt(g["w0_m"])}\sqrt{{1+({fmt(g["L_m"])}\,1.55\times10^{{-6}}/(\pi\,{fmt(g["w0_m"])}^2))^2}}',g['wL_m'])
add(r'''### Hufnagel–Valley/Rytov và broadening

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
''')
table(['Auxiliary','Independent value'],[(k,g[k]) for k in ('wave_number_per_m','rytov_integral','sigma_R2','mu2_integral','beam_lambda','G_d','w_eff_m')])
formula('G_d',rf'4.35({fmt(g["beam_lambda"])})^{{5/6}}({fmt(g["wave_number_per_m"])})^{{7/6}}19000^{{5/6}}({fmt(g["secant"])})^{{11/6}}({fmt(g["mu2_integral"])})',g['G_d'])
formula(r'w_{L,eff}',rf'{fmt(g["wL_m"])}\sqrt{{1+{fmt(g["G_d"])}}}',g['w_eff_m'])
add(r'''Aperture averaging cũng được tính nhưng không đi vào sigma_R² của active Literal PDF:
\[
J_2=\int C_n^2(h)h^2dh,\quad J_{5/6}=\int C_n^2(h)h^{5/6}dh,\quad
\Phi_m=(J_2/J_{5/6})^{6/7},
\]
\[
A_{ap}=[1+1.11(D_r^2/(\lambda\Phi_m\sec\zeta))^{7/6}]^{-1},\quad v_{sc}=A_{ap}\sigma_R^2.
\]
''')
table(['Quantity','Independent value'],[(k,g[k]) for k in ('aperture_numerator','aperture_denominator','Phi_m','A_ap','v_sc_unused_in_active_PDF')])
add('Active LiteralChannel.from_physical dùng raw sigma_R0_squared≈.053962..., không dùng aperture-averaged v_sc≈.00158144. Đây là mode-specific choice có sẵn. Không trộn hai PDF/scintillation branches. G_d được audit theo công thức implementation; citation/physical calibration của broadening vẫn là giới hạn đã ghi trong code, không được numerical matching tự chứng nhận.')
add(r'''### Aperture collection, pointing và AoA
\[
v=\sqrt\pi D_r/(2\sqrt2\,w_{L,eff}),\quad A_0=\operatorname{erf}^2(v),\quad
w_{L,eq}=\sqrt{w_{L,eff}^2\sqrt\pi\operatorname{erf}(v)/(2v e^{-v^2})}.
\]
''')
formula('v',rf'\sqrt\pi(0.55)/(2\sqrt2\,{fmt(g["w_eff_m"])})',g['nu_ap'])
formula('A_0',rf'({fmt(g["erf_nu"])})^2',g['A0'])
formula(r'w_{L,eq}',rf'\sqrt{{({fmt(g["w_eff_m"])})^2\sqrt\pi({fmt(g["erf_nu"])})/(2({fmt(g["nu_ap"])})(e^{{-({fmt(g["nu_ap"])})^2}}))}}',g['w_eq_m'])
formula(r'\sigma_{jt}=L\theta_{jt}',rf'{fmt(g["L_m"])}(15.61\times10^{{-6}})',g['sigma_jt_m'])
formula(r'\sigma_s=\sqrt{\sigma_h^2+\sigma_{jt}^2}',rf'\sqrt{{1^2+({fmt(g["sigma_jt_m"])})^2}}',g['sigma_s_m'])
formula(r'\chi_p=w_{L,eq}/(2\sigma_s)',rf'{fmt(g["w_eq_m"])}/(2({fmt(g["sigma_s_m"])}))',g['pointing_chi'])
add(f"Pointing chi_p²={fmt(g['pointing_chi_squared'])}; đây không phải Holevo chi_BE.")
formula('P_0',r'\exp[-(0.00625)^2/(2(0.0015)^2)]',g['P0'])
formula('P_1',rf'1-{fmt(g["P0"])}',g['P1'])
add(r'''Atom P0 delta(eta) được giữ riêng. Các positive-power moments không nhận đóng góp từ atom0. Không bỏ P0, không biến nó thành continuous density.

### Hai aperture intermediates khác nhau trong runtime

manuscript_pointing_parameters:148–156 tính nu theo w_L chưa broadened, trả A0/weq metadata. LiteralChannel.from_physical:86–95 tính lại nu theo w_eff và dùng kết quả đó làm active raw PDF. Không được lấy nhầm metadata intermediate thay active PDF value.
''')
table(['Quantity','First pointing metadata runtime','Active LiteralChannel runtime','Independent active'],[
('nu',physical['pointing']['nu'],math.sqrt(math.pi)*physical['receiver_diameter_m']/(2*math.sqrt(2)*physical['pointing']['omega_L_m']*math.sqrt(1+physical['pointing']['G_d'])),g['nu_ap']),
('A0',physical['pointing']['A0'],state['clear_raw_channel']['A0'],g['A0']),
('w_eq',physical['pointing']['omega_L_eq_m'],state['clear_raw_channel']['w_eq'],g['w_eq_m'])])
add(r'''## C. Fading PDF and moments

Runtime rho=0 được kiểm tra rõ. Đặt d=chi_p², B=A0 eta_atm:
\[
C_1=e^{\sigma_R^2d(1+d)/2},\quad C_3=(2\sigma_R^2)^{-1/2},\quad
\mu=\sigma_R^2(1+2d)/2,\quad x_1=-\ln B+\mu.
\]
''')
table(['Coefficient','Independent value'],[(k,f[k]) for k in ('B','C1','C3','mu','x1')]+[('d',g['pointing_chi_squared'])])
add(r'''Raw PDF gồm atom và continuous term:
\[
f_{raw}(\eta)=P_0\delta(\eta)+\frac{P_1dC_1}{2B^d}\eta^{d-1}
\operatorname{erfc}[C_3(\ln(\eta/B)+\mu)].
\]
''')
add(f"Thay số MP: {fmt(g['P0'])} delta(eta) + {fmt(f['PDF_active_prefactor'])} eta^({fmt(g['pointing_chi_squared']-1)}) erfc[{fmt(f['C3'])}(ln(eta/{fmt(f['B'])})+{fmt(f['mu'])})]. C1 channel PDF khác C của exact source Denys.")
add(r'''
\[
Q(a)=\tfrac12[e^{ax_1-a\mu}\operatorname{erfc}(C_3x_1)+
e^{a^2/(4C_3^2)-a\mu}\operatorname{erfc}(a/(2C_3)-C_3x_1)].
\]
''')
table(['Q value','Independent result'],[(k,f[k]) for k in ('Q_chi2','Q_chi2_plus_half','Q_chi2_plus_one')])
add(r'''Eq19–20 RAW [0,1] moments:
\[
m_{1,raw}=P_1B\frac{dC_1}{d+1}Q(d+1),\quad
m_{1/2,raw}=P_1\sqrt B\frac{dC_1}{d+1/2}Q(d+1/2).
\]
''')
formula(r'm_{1,raw}',rf'({fmt(g["P1"] )})({fmt(f["B"] )})\frac{{({fmt(g["pointing_chi_squared"] )})({fmt(f["C1"] )})}}{{{fmt(g["pointing_chi_squared"]+1)}}}({fmt(f["Q_chi2_plus_one"] )})',f['raw_mean_eta'])
formula(r'm_{1/2,raw}',rf'({fmt(g["P1"] )})\sqrt{{{fmt(f["B"] )}}}\frac{{({fmt(g["pointing_chi_squared"] )})({fmt(f["C1"] )})}}{{{fmt(g["pointing_chi_squared"]+.5)}}}({fmt(f["Q_chi2_plus_half"] )})',f['raw_mean_sqrt_eta'])
add(r'''Active retained mass F_active=C1 Q(d). Raw total [0,1] mass=P0+P1 F_active. Existing PhysicalFadingDistribution giữ P0 và condition riêng active component: physical f_cont=f_raw,cont/F_active trên(0,1]. Đây là lựa chọn đã có và được config/receipt nêu rõ, không phải renormalization mới để cứu kết quả. Raw lognormal extension trên eta>0 có total mass1; phần thiếu trên[0,1] là mass eta>1 của surrogate. Nếu dùng raw Eq19 đơn lẻ, không thu được runtime conditioned m1≈.2379089.
''')
table(['Quantity/law','Independent closed','Independent quadrature','Relative error'],[(row['quantity'],row['closed_form'],row['quadrature'],row['relative_error']) for row in __import__('csv').DictReader((OUT/'moments_closed_vs_quadrature.csv').open()) if row['case']=='A'])
formula(r'F_{active}=C_1Q(d)',rf'({fmt(f["C1"])})({fmt(f["Q_chi2"])})',f['raw_active_mass'])
formula(r'm_{1,physical}=m_{1,raw}/F_{active}',rf'{fmt(f["raw_mean_eta"])}/{fmt(f["raw_active_mass"])}',f['mean_eta'])
formula(r'm_{1/2,physical}=m_{1/2,raw}/F_{active}',rf'{fmt(f["raw_mean_sqrt_eta"])}/{fmt(f["raw_active_mass"])}',f['mean_sqrt_eta'])
formula(r'm_\xi=\xi_{ch}m_1',rf'0.0186({fmt(f["mean_eta"])})',f['m_xi'])
add(f"Independent raw mass={fmt(f['raw_total_mass'])}, deficit={fmt(f['raw_mass_deficit'])}; active tail≈{fmt(f['numerical_tail_probability'])}; full raw positive-support mass including atom={fmt(f['numerical_whole_raw_total'])}. Physical conditioned total={fmt(f['physical_total_mass'])}. Both methods giữ atom0 explicit. Tolerance CF/quadrature: relative1e-10 hoặc absolute2e-13, với adaptive error estimates được lưu; không nới sau kết quả.")
add(f"Runtime original quad cho G_d hơi khác MP: raw m1={fmt(mom['raw_mean_eta'])}, active norm={fmt(mom['active_normalization'])}; raw m1/norm={fmt(mom['raw_mean_eta']/mom['active_normalization'])}. Độc lập thay đúng original mu2 quadrature vào cùng công thức tái dựng được m1={fmt(precision['reconstructed_runtime_cases'][0]['mean_eta_using_original_mu2'])}. Vì vậy .2379089 truy được về primitives và integration, không phải chỉ từ cache PASS. Phần khác nhau1.535e-11 được điều tra ởI.")
add(r'''## D. Effective channel

Các dòng sau dùng independent high-precision chain, kèm runtime ở bảng so sánh. Channel excess không chứa chi_line, chi_tot hoặc detector noise.
''')
q=ind['ideal_primary'];rt=live['ideal_primary']
formula(r'\eta_f=m_{1/2}^2',rf'({fmt(f["mean_sqrt_eta"])})^2',q['eta_f'])
formula(r'\operatorname{Var}(\sqrt\eta)=m_1-\eta_f',rf'{fmt(f["mean_eta"])}-{fmt(q["eta_f"])}',q['fading_variance'])
formula(r'E_{fading}=(m_1-\eta_f)V_A',rf'({fmt(q["fading_variance"])})5.046875',q['fading_excess_output'])
formula(r'E_{channel}=m_\xi',rf'0.0186({fmt(f["mean_eta"])})',q['m_xi'])
formula(r'N_{eff}=\eta_f\xi_f',rf'{fmt(q["fading_excess_output"])}+{fmt(q["m_xi"])}',q['N_eff'])
formula(r'\xi_f=N_{eff}/\eta_f',rf'{fmt(q["N_eff"])}/{fmt(q["eta_f"])}',q['xi_f'])
formula(r'r_{fading}=100E_{fading}/N_{eff}',rf'100({fmt(q["fading_excess_output"])})/({fmt(q["N_eff"])})',q['fading_fraction_percent'])
add(f"Runtime nguyên bản: tử số={fmt(rt['fading_excess_output'])}, mẫu số={fmt(rt['N_eff'])}, ratio={fmt(100*rt['fading_excess_output']/rt['N_eff'])}%. Tuyên bố98.87% đúng khi làm tròn; không phải từ total noise hoặc detector.")
add(r'''## E. Covariance
''')
add(f"Exact source nu_raw={fmt(source['nu_raw'])}, VA={fmt(source['V_A'])}; C={fmt(source['C'])}, w={fmt(source['w'])}; ensemble hash {source['ensemble_hash']}; payload hash {source['source_payload_sha256']}. Không build/source worker mới, không nội suy C,w.")
formula('V=V_A+1','5.046875+1',q['V'])
formula(r'W_{pre}=1+\eta_fV_A+N_{eff}',rf'1+({fmt(q["eta_f"])})5.046875+{fmt(q["N_eff"])}',q['W_pre'])
formula(r'W_{pre}=1+m_1(V_A+\xi_{ch})',rf'1+({fmt(f["mean_eta"])})(5.046875+0.0186)',q['W_pre'])
formula(r'Z_{base}=2\sqrt{\eta_f}C',rf'2\sqrt{{{fmt(q["eta_f"])}}}({fmt(source["C"])})',q['Z_signal'])
formula(r'Z_{correction}=\sqrt{2N_{eff}w}',rf'\sqrt{{2({fmt(q["N_eff"])})({fmt(source["w"])})}}',q['Z_penalty'])
formula(r'Z=Z_{base}-Z_{correction}',rf'{fmt(q["Z_signal"])}-{fmt(q["Z_penalty"])}',q['Z'])
add('Gamma_AB=[[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]]. Full matrix và spectra ở high_precision_SKR.json. Kiểm tra riêng positive covariance, Gamma+iOmega, closed symplectic spectrum so direct iOmegaGamma; không clip Z/covariance để làm hợp lệ.')
table(['Metric','Independent A value'],[('min eigenvalue Gamma+iOmega',q['minimum_uncertainty_eigenvalue']),('closed vs matrix symplectic residual',q['closed_matrix_spectrum_residual'])])
add(r'''## F. Mutual information and Holevo

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
''')
table(['Detector','Channel amplitude gain','Detector amplitude gain','Complex variance','Per-real variance','I_AB','beta I_AB','GH32/48 difference'],[(name,math.sqrt(q['eta_f']),math.sqrt(runtime['detectors'][name]['eta_B']),row['sigma2_complex'],row['variance_per_real_quadrature'],row['I_AB'],row['beta_I_AB'],abs(row['full_2D_GH'][2]['I_AB']-row['full_2D_GH'][1]['I_AB'])) for name,row in ind.items()])
add(r'''Holevo independent dùng Delta=V²+W²-2Z², D=(VW-Z²)²; nu1,2=sqrt((Delta +/- sqrt(Delta²-4D))/2). Ideal conditional nu3=V-Z²/(W+1). Delta/D được tính lại dưới đây, không đọc từ production covariance helper. S(AB)=sum g((nu1,2-1)/2); S_cond được trừ, không cộng.
''')
delta=q['V']**2+q['W_pre']**2-2*q['Z']**2;det=(q['V']*q['W_pre']-q['Z']**2)**2
table(['Quantity','Independent ideal A'],[('Delta',delta),('D',det),('nu1',q['lambda_1']),('nu2',q['lambda_2']),('nu3 het',q['conditional_eigenvalues'])])
add(r'''Trusted detector dùng upsilon=1+2nu_B/(1-eta_B), V_B2=eta_BW+(1-eta_B)upsilon. Tạo independent AFG/C blocks từ beam splitter/EPR AppendixA, condition Gamma_AFG-C(Gamma_B2+I)^(-1)C^T và lấy3 symplectic eigenvalues, không dùng ideal nu3. Ancillas được giả định trusted/độc lập Eve; đây không phải calibration chứng minh từ phép đo.
''')
table(['Quantity','Independent ideal A','Independent trusted A'],[(k,ind['ideal_primary'][k],ind['trusted_diagnostic'][k]) for k in ('lambda_1','lambda_2','conditional_eigenvalues','S_AB_terms','S_AB','conditional_entropy_terms','conditional_entropy','chi_BE','chi_upper')])
add('Cả8 covariance/detector cases đều đạt physicality và chi<=2g((Wpre-1)/2), không clip Holevo. Bound là necessary consistency check, không phải tightness hoặc security-proof certificate. So printed chi≈1.146634/.755356 khớp; sai khác ~1e-11 của independent chain so runtime được giải thích bằngmu2, không nhầm receiver hoặc log base.')
add(r'''## G. SKR
''')
for name,row in ind.items():
    actual=live[name]
    add(name+':')
    formula(r'K_{ind}=0.95I_{ind}-\chi_{ind}',f'0.95({fmt(row["I_AB"] )})-{fmt(row["chi_BE"] )}',row['K_raw'])
    formula(r'K_{runtime}=0.95I_{runtime}-\chi_{runtime}',f'0.95({fmt(actual["I_AB"] )})-{fmt(actual["chi_BE"] )}',actual['K_raw'])
    add(f"Independent minus runtime K={fmt(row['K_raw']-actual['K_raw'])} bits/use. beta*MI={fmt(row['beta_I_AB'])}<chi={fmt(row['chi_BE'])}; rate âm trong cả hai phép tính. Không chỉnh hardware/noise/source để ép dương.")
add(r'''## H. Configuration sensitivity

Chỉ4 cases x2 receiver với cùng exact source/primitive atmospheric/motion inputs. Mỗi case tính fresh, không dùng objective cache. A là config đang chạy; B/C/D là diagnostics theo user, không ghi vào production configuration.
''')
table(['Case','Dr m','Full-angle urad','w0','wL','w_eq','A0','sigma_s','pointing chi²'],[(c['case'],c['geometry']['Dr_m'],c['geometry']['theta_div_rad']*1e6)+tuple(c['geometry'][k] for k in ('w0_m','wL_m','w_eq_m','A0','sigma_s_m','pointing_chi_squared')) for c in audit['cases']])
table(['Case','m1','eta_f','xi_f','W_pre','Z','I ideal','chi ideal','K ideal','K trusted'],[(c['case'],c['fading']['mean_eta'])+tuple(c['quantum']['ideal_primary'][k] for k in ('eta_f','xi_f','W_pre','Z','I_AB','chi_BE','K_raw'))+(c['quantum']['trusted_diagnostic']['K_raw'],) for c in audit['cases']])
sensitivity=[]
for c in audit['cases']:
    for name,row in c['quantum'].items():sensitivity.append(dict(case=c['case'],detector=name,Dr=c['geometry']['Dr_m'],theta_div_rad=c['geometry']['theta_div_rad'],**{k:c['geometry'][k] for k in ('w0_m','wL_m','w_eq_m','A0','sigma_s_m','pointing_chi_squared')},m1=c['fading']['mean_eta'],**{k:row[k] for k in ('eta_f','xi_f','W_pre','Z','I_AB','chi_BE','K_raw')},geometry_fingerprint=c['runtime_geometry_fingerprint']))
with (OUT/'configuration_sensitivity.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(sensitivity[0]));writer.writeheader();writer.writerows(sensitivity)
add('ChỉA cho m1≈.2379089. B cho m1≈.000264034, đúng bậc1e-4 của hardware cũ nhưng không được coi trùng exact một con số minh họa từ configuration khác. Default223urad khác caseB233urad; không đổi tên chúng cho khớp kết quả mong muốn.')
table(['Case','Reconstructed geometry fingerprint'],[(c['case'],c['runtime_geometry_fingerprint']) for c in audit['cases']])
add(r'''## I. Final verdict, strict FAILs và tác động định lượng

**CONFIGURATION_MATCH_CONFIRMED:** trace hiệu lực Dr=.55/full-angle10urad, fresh physical-state equality và zero residual fresh/historical reference SKR cùng xác nhận hardware. Không có CONFIGURATION_MISMATCH ở reference.

**MOMENT_MISMATCH, scope strict high-precision comparison:** không che5 FAIL trong independent_geometry_audit.json. Các phép CF/quadrature độc lập cùng luật đều khớp; discrepancy so runtime đến từ accuracy quadrature phụ mu2, không phải dùng sai hardware hoặc moment convention.
''')
table(['Original strict check','Outcome','Detail'],[(x['check'],x['status'],json.dumps(x['detail'],ensure_ascii=False)) for x in audit['failures']])
add(r'''Audit trước tự tích phân PDF từ raw channel parameters đã lưu và kiểm MI/Holevo trên các moment đó; chưa tái dựng Gd từ primitive turbulence inputs. Audit hiện tại đi thêm bước này. Vì vậy residual SKR khoảng9e-12 ở đây không mâu thuẫn với residual khoảng9e-15 của audit trước và không có bằng chứng cache/evaluator version bị trộn.

Root của sai khác Gd: src/channel/pointing_error.py:124–136, manuscript_pointing_parameters, quad(...epsabs=1e-18,epsrel=2e-13). Mu2 chỉ cỡ5e-14; absolute tolerance cho phép dừng trước khi đạt relative target. Giữ nguyên code này, probe chẩn đoán capture original value/error rồi tính lại integrand riêng với epsabs1e-28. Không thay kết quả runtime hoặc production tolerance.
''')
quad=precision['original_quadrature'][0]
table(['mu2 calculation','Value','Reported absolute error'],[
('Original production quadrature',quad['observed_value'],quad['observed_error_estimate']),
('Independent70dps',precision['MP_mu2'],'arithmetic precision; not physical accuracy'),
('Diagnostic tighter SciPy quadrature',quad['tighter_value'],quad['tighter_error_estimate'])])
add(f"Original minus MP mu2={fmt(precision['mu2_difference_original_minus_MP'])}, nằm trong original error estimate. Gd independent-runtime={fmt(precision['Gd_difference_independent_minus_runtime'])}; A m1 difference={fmt(f['mean_eta']-mom['mean_eta'])}. D xi_f difference≈-5.157e-9 chỉ là relative≈-2.184e-11 vì eta_f nhỏ; SKR D difference≈9e-15. Năm initial FAIL không bị đổi tolerance hoặc rewrite thành PASS.")
add('Causal test thay chỉ mu2 original vào independent geometry dựng lại runtime Gd/m1/mhalf cho cả4 cases với residual<1e-13. Các check riêng theo đúng đại lượng xác nhận cả8 signed SKRs chênh<1e-9. Đây là giải thích uncertainty/cause, không hủy strict FAIL. quadrature_precision_diagnosis.json lưu toàn bộ hai bộ kiểm tra.')
add(r'''**NUMERICALLY_CONSISTENT, scope:** closed-form vs independent quadrature của raw/conditioned PDF, moment identities, covariance/noise accounting, independent MI/Holevo và signed SKR đến sai số đã định lượng. Không có evidence NOISE_ACCOUNTING_ERROR, HOLEVO_ERROR hoặc MI_ERROR gây dấu âm. Không tuyên bố toàn bộ94 strict checks đều PASS:89 PASS,5 FAIL được báo đủ;18 causal/metric/AoA follow-up checks PASS.

**UNVALIDATED_SECURITY_MODEL:** numerical/configuration confirmation không thiết lập security proof cho discrete modulation fading. Hosseinidehaj hỗ trợ Gaussian-modulation fading covariance/receiver; exact Denys C,w/correlation constraints giữ nguyên. Gaussian-surrogate MI không được tự đồng nhất true pooled-fading MI hoặc lower bound đã chứng minh; directZ không được tự chứng nhận full-interval worst case. Trusted-DM composition, calibration, operational/finite-size/composable scope vẫn chưa xác lập.

Khuyến nghị tối thiểu nếu cần matching ở precision cao hơn: một task sau có thể scale integrand mu2 hoặc giảm epsabs tương xứng khoảng1e-28 và prospectively kiểm regression. Đây là numerical refinement, không phải thay physical model để cứu SKR; tác động reference K hiện chỉ khoảng9e-12. **Chưa sửa production; chờ xác nhận riêng trước bất kỳ thay đổi nào.**

Sources: [Hosseinidehaj v1 Eq4–7/AppendixA](https://arxiv.org/pdf/2002.03476.pdf), [Denys2021](https://quantum-journal.org/papers/q-2021-09-13-540/pdf/); bản thảo thực tế dùng để đối chiếu là2026__Binh_s_work (38).pdf (SHA0c60153c...be0a0), requested(38)(3) không có. Công thức Gd tái lập từ repo, bibliography/calibration ngoài code chưa được xác nhận. Frozen actual hashdf83ea63...78c15 vẫn khác historical AGENTS; không sửa. NOT_READY_FOR_PUBLICATION_SCALE_RUNS và ObjectiveC USER_STOPPED giữ nguyên.

Artifacts: runtime_probe.json (arguments/return objects, original defaults/CLI/env), independent_geometry_audit.json (4 independent chains và94 checks), high_precision_common_geometry.json/high_precision_SKR.json, moments_closed_vs_quadrature.csv, runtime_parameters.csv, configuration_sensitivity.csv, SKR_entropy_decomposition.csv và quadrature_precision_diagnosis.json. Các file nằm trong results/full_geometry_fading_skr_audit_20261017/. Runtime probe script và independent audit script là2 file mới riêng; không sửa source/Cw/config/frozen specifications hoặc output cũ. Không full-catalog/mission/optimizer, training/test access, publication/baseline/threshold promotion, external edits hoặc commit/push. Audit complete; STOP.
''')
text='\n'.join(lines)+'\n'
(ROOT/'docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md').write_text(text,encoding='utf-8')
(OUT/'FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md').write_text(text,encoding='utf-8')
summary=dict(audit_completed=True,verification_scope='Audit/provenance complete; strict failures retained',verdicts=['CONFIGURATION_MATCH_CONFIRMED','MOMENT_MISMATCH','NUMERICALLY_CONSISTENT','UNVALIDATED_SECURITY_MODEL'],
             strict_checks=dict(passed=len(audit['checks'])-len(audit['failures']),failed=len(audit['failures']),status='FAILED'),
             downstream_diagnosis=dict(status=precision['status'],checks=len(precision['checks'])),
             current_hardware=dict(Dr_m=physical['receiver_diameter_m'],theta_full_rad=physical['theta_div_rad'],w0_m=physical['beam_waist_m']),
             runtime_m1=mom['mean_eta'],independent_high_precision_m1=f['mean_eta'],m1_difference=f['mean_eta']-mom['mean_eta'],
             signed_SKR={name:dict(runtime=live[name]['K_raw'],independent=row['K_raw'],difference=row['K_raw']-live[name]['K_raw']) for name,row in ind.items()},
             source_moment_builds=0,new_production_SKR_calls=8,full_catalog_or_missions_run=False,production_edited=False,
             recommended_production_change_not_applied='Only optional tighter/scaled mu2 quadrature; no formula/noise/hardware correction to force positive SKR')
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
