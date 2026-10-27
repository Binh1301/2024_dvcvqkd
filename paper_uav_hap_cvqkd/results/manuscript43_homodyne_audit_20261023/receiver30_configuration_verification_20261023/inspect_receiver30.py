"""One fixed receiver30 reproduction; separate literal B without detector efficiency."""
import csv
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
PARENT=OUT.parent
ROOT=PARENT.parents[1]
sys.path.insert(0,str(PARENT))
import audit_model as a
import run_audit as r
from compare import independent_entropy
import mpmath as mp
import numpy as np
from scipy.integrate import quad


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name,data):
    (OUT/name).write_text(json.dumps(r.clean(data),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def write(name,data):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)


def origin(fn):
    fn=inspect.unwrap(fn)
    return Path(inspect.getsourcefile(fn)).relative_to(ROOT).as_posix()+':'+str(inspect.getsourcelines(fn)[1])


def literal_model_B(c,moments,xi_det,tolerance):
    """xi_det is explicitly independent; no eta_det or hardware electronic-noise argument."""
    tf=moments['mh']**2
    mn=.0186*moments['m1']+xi_det*moments['M0']
    nf=(moments['m1']-tf)*c['VA'];noise=nf+mn
    result=dict(model='B_literal_v43_real_homodyne',channel_law=moments['law'],
        xi_det=xi_det,xi_det_definition='EXPLICIT_INDEPENDENT_PARAMETER_AUTHORIZED_IN_CURRENT_REQUEST',
        xi_ch=.0186,M0=moments['M0'],m1=moments['m1'],mh=moments['mh'],eta_f=tf,
        mean_eta_xi=mn,N_fading=nf,N_effective=noise,xi_f=noise/tf,
        sigma2_MI=1+noise,T_Holevo=tf,beta=.95,
        I_AB=None,beta_I_AB=None,chi_BE=None,K_raw=None,security_valid=False,
        noise_reference_plane='literal effective output; xi_det adds constant output noise; no separate efficiency',
        zero_atom_noise_contribution=xi_det*moments['P0'],
        active_only_mean_eta_xi=.0186*moments['m1']+xi_det*(moments['M0']-moments['P0']))
    if abs(moments['M0']-1)>tolerance:
        return {**result,'status':'BLOCKED_BY_SCIENTIFIC_MODEL',
            'failure':'FAILED_PDF_NORMALIZATION_PREDECLARED_1e-10','MI_Holevo_evaluation':'NOT_RUN'}
    p,alpha=a.validate_source(c)
    h=a.legacy.full_holevo(1+c['VA'],1+tf*c['VA']+noise,
        2*math.sqrt(tf)*c['C'],math.sqrt(2*noise*c['w']),129)
    mi=a.homodyne_mi(p,alpha,tf,1+noise,order=128)
    return {**result,**h,'I_AB':mi,'beta_I_AB':.95*mi,'K_raw':.95*mi-h['chi_BE'],
        'status':'GAUSSIAN_COMPONENT_ONLY_NO_SECURITY_APPROVAL','MI_Holevo_evaluation':'EVALUATED'}


def parameter_rows(ch,raw_ch,mo,c,A,B,raw,old):
    data=[]
    old_path='results/manuscript43_homodyne_audit_20261023/historical_regressions.json#records[label=receiver30].saved'
    opt=origin(r.adapter().saved.optical);prim=origin(r.adapter().saved.primitives)
    passive=origin(a.legacy.power_conserving);rawopt=origin(a.legacy.optical)
    phys=origin(a.effective);lit=origin(literal_model_B)
    payload=c['source_path'];source=payload+'#'
    def add(group,name,value,unit,model,kind,source,note=''):
        data.append(dict(group=group,parameter=name,value=value,unit=unit,model=model,
            specified_or_derived=kind,configuration_source=source,note=note))
    def stored(group,name,key,unit,note=''):
        add(group,name,float(ch[key]),unit,'A/B','Derived',old_path+'.'+key+'; '+opt,note)
    for name,key,unit in [('h_HAP','h_hap_km','km'),('h_UAV','h_uav_km','km'),
        ('zenith','zenith_deg','degree'),('Dr','D_r','m'),('full_divergence','divergence_urad','urad'),
        ('angular_jitter_per_axis','jitter_urad','urad'),('sigma_h_per_axis','sigma_h_m','m')]:
        add('A Geometry' if name in ['h_HAP','h_UAV','zenith'] else 'B Optical',name,float(ch[key]),unit,'A/B',
            'Specified historical override',old_path+'.'+key+'; '+origin(r.adapter().optical),
            'Actual scenario overrides baseline values; not taken from production channel.yaml')
    stored('A Geometry','slant_distance','L_km','km','(20-1)/cos(0)=19')
    add('A Geometry','vertical_span',19000.,'m','A/B','Derived',opt,'h_HAP-h_UAV')
    add('B Optical','wavelength',1.55e-6,'m','A/B','Specified in actual code',opt,'Hard-coded wave; same value corroborated in configs/manuscript_mobility.json.optical')
    add('B Optical','receiver_radius',ch['D_r']/2,'m','A/B','Derived',passive+'; '+rawopt,'Dr/2')
    for name,key in [('w0','w0_m'),('wL_vacuum_propagation','wL_m'),('w_eff','w_eff_m')]:
        stored('B Optical',name,key,'m','w0=2*lambda/(pi*full_divergence); wL=w0*sqrt(1+(L*lambda/(pi*w0^2))^2); w_eff=wL*sqrt(1+Gd)')
    stored('B Optical','Gd','G_d','dimensionless','Repository HV closure; recomputed at 35urad')
    ap=math.sqrt(math.pi)*ch['D_r']/(2*math.sqrt(2)*ch['w_eff_m'])
    a0=math.erf(ap)**2
    add('B Optical','aperture_nu',ap,'dimensionless','B','Derived',rawopt,'sqrt(pi)*Dr/(2*sqrt(2)*w_eff); not MB nu')
    add('B Optical','A0_erf_equivalent',a0,'power fraction','B','Derived',rawopt,'Used only by original product law; A has no constant A0')
    add('B Optical','A0_circular_at_w_eff',-math.expm1(-2*(ch['D_r']/2)**2/ch['w_eff_m']**2),
        'power fraction','A','Derived diagnostic',passive,'Centered circular collection at w=w_eff; random width has no single fixed A0')
    add('B Optical','w_eq',raw_ch['w_eq_m'],'m','B','Derived',rawopt,'Equivalent-beam width; NOT used in Model A collector')
    add('B Optical','B_atm_A0',float(raw_ch['B']),'dimensionless','B','Derived',rawopt,'eta_atm*A0')
    add('B Optical','pointing_chi_squared',float(raw_ch['d']),'dimensionless','B','Derived',rawopt,'w_eq^2/(4*sigma_s^2)')
    for name,value in [('var_position_x',ch['sigma_h_m']**2),('var_position_y',ch['sigma_h_m']**2),
        ('var_jitter_angle_per_axis',(ch['jitter_urad']*1e-6)**2)]:
        add('B Optical',name,value,'rad^2' if 'angle' in name else 'm^2','A/B','Derived',opt,'Independent per-axis Gaussian terms')
    stored('B Optical','angular_displacement_per_axis','angular_displacement_m','m','L*theta_jitter')
    stored('B Optical','sigma_s_per_axis','sigma_s_m','m','sqrt(sigma_h^2+(L*theta_jitter)^2)')
    add('B Optical','sigma_s_squared_per_axis',ch['sigma_s_m']**2,'m^2','A/B','Derived',opt,'Total displacement variance per Cartesian axis')
    add('B Optical','radial_RMS',math.sqrt(2)*ch['sigma_s_m'],'m','A/B','Derived',passive,'Rayleigh displacement with zero boresight')
    for name in ['boresight_x','boresight_y','rho']:
        add('B Optical',name,0.,'m','A/B','Implicit fixed zero',passive+'; '+origin(a.raw_coefficients),
            'Model A uses central ncx2/Rayleigh without a nonzero-boresight input; B rho default=0')
    add('B Optical','launch_radius_of_curvature','infinity (implied)','m','A/B','Implicit model assumption',opt,
        'No R input exists in this call chain; waist-plane propagation formula. channel.yaml infinity is corroboration only.')
    add('B Optical','receiver_radius_of_curvature','NOT_STORED_NOT_USED','m','A/B','Not an active parameter',opt,
        'No value invented; scalar collected-power model does not evaluate wavefront curvature.')
    add('B Optical','AO','OFF','state','A/B','Specified in actual code',opt,'No AO efficiency multiplier')
    add('B Optical','phase_noise','OFF_HISTORICAL_ASSUMPTION','state','A/B','Specified in actual code',opt,'No c_phi*VA term')
    add('B Optical','additional_coupling_insertion_loss','NOT_MODELED','power fraction','A/B','Absent',opt+'; '+passive,
        'No measured coupling/optics loss budget or hardware calibration supplied; not an extra factor silently set from baseline')
    stored('B Optical','transmitter_diameter_99percent','transmitter_diameter_99percent_m','m')
    add('C Atmosphere AoA','tau_zen',.92,'power fraction','A/B','Specified historical override',old_path+'.tau_zen; '+opt)
    stored('C Atmosphere AoA','eta_atm','eta_atm','power fraction','tau_zen^sec(zenith); zenith=0')
    add('C Atmosphere AoA','Cn2_ground_coefficient',1e-14,'m^(-2/3)','A/B','Specified in actual code',prim,
        'Ground exponential coefficient A; distinguish full Cn2(0)')
    add('C Atmosphere AoA','Cn2_full_profile_at_0',1e-14+2.7e-16,'m^(-2/3)','A/B','Derived',prim,
        'At h=0 the high-altitude term vanishes; HV includes background 2.7e-16')
    add('C Atmosphere AoA','wind_speed',21.,'m/s','A/B','Specified in actual code',prim)
    for name,key,unit in [('HV_rytov_integral','HV_rytov_integral','m^(7/6)'),
        ('HV_mu2_integral','HV_mu2_integral','m^(1/3)'),('raw_Rytov_variance','v','dimensionless')]:
        stored('C Atmosphere AoA',name,key,unit,'Raw Rytov used as log-irradiance variance under weak-turbulence approximation')
    add('C Atmosphere AoA','turbulence_factor',1.,'dimensionless','A/B','Specified in actual code',opt)
    for name,value in [('log_irradiance_mean',-float(ch['v'])/2),('log_irradiance_variance',float(ch['v'])),
        ('log_irradiance_SD',math.sqrt(float(ch['v']))),('log_amplitude_variance',float(ch['v'])/4)]:
        add('C Atmosphere AoA',name,value,'dimensionless','A/B','Derived',passive+'; '+origin(a.raw_coefficients),
            'S~N(-v/2,v); A uses width=w_eff*exp(-S/2), B multiplicative irradiance I=exp(S)')
    add('C Atmosphere AoA','AoA_FOV_half_angle',.00625,'rad','A/B','Specified in actual code',opt,'6.25mrad; full FOV=12.5mrad')
    add('C Atmosphere AoA','AoA_angular_SD',.0015,'rad per axis','A/B','Specified in actual code',opt,'1.5mrad; Rayleigh magnitude')
    add('C Atmosphere AoA','AoA_additional_turbulent_variance','NO_SEPARATE_TERM','rad^2','A/B','Absent in actual formula',opt,
        'P0 uses .0015 directly; no Gd/AoA turbulence term added')
    for name,key in [('P0','P0'),('P1','P1')]:
        stored('C Atmosphere AoA',name,key,'probability','P0=exp(-FOV_half^2/(2*sigma_AoA^2)); P1=1-P0')
    for name,value in [('detector_model','untrusted loss plus output electronic noise'),('eta_det',.95),('epsilon_det',.005)]:
        add('D Detector noise',name,value,'dimensionless' if name=='eta_det' else 'SNU output' if name=='epsilon_det' else 'model',
            'A','Specified historical override',old_path+'; '+phys)
    add('D Detector noise','xi_ch',.0186,'input-referred SNU','A/B','Specified in evaluator',phys+'; '+lit)
    add('D Detector noise','vacuum_variance',1.,'SNU','A/B','Specified quadrature convention',origin(a.homodyne_mi)+'; '+phys)
    add('D Detector noise','xi_det',.005,'SNU literal coefficient','B','Specified current request','task.txt#Section3; protocol.json#model_B',
        'Independent coefficient in xi(eta)=xi_ch+xi_det/eta; no efficiency parameter, no hardware epsilon conversion')
    add('D Detector noise','eta_det','NO_PARAMETER','dimensionless','B','Explicitly absent','task.txt#Section3; '+lit,
        'Neither .95 nor an implicit replacement eta_det=1 is passed to the B function')
    add('D Detector noise','electronics_at_outage','included','per transmitted use','A/B','Specified convention',phys+'; '+lit,
        'A epsilon_det every use; B zero-limit extension adds xi_det*P0')
    p,alpha=a.validate_source(c);x=2*alpha.real
    for name,value,unit,kind in [('M',256,'symbols','Specified'),('VA',c['VA'],'SNU','Specified exact source'),
        ('nbar',float(p@abs(alpha)**2),'photons/use','Derived'),('nu_raw',c['nu_raw'],'dimensionless','Specified exact source'),
        ('nu_repo',float.fromhex(read(ROOT/payload)['nu_mb_repo_hex']),'dimensionless','Exact source metadata'),
        ('C',c['C'],'source moment','Exact cached'),('w',c['w'],'source moment','Exact cached'),
        ('source_hash',c['ensemble_hash'],'SHA256 ensemble','Exact identity'),('PMF_sum',float(p.sum()),'probability','Derived'),
        ('mean_alpha_real',float((p@alpha).real),'amplitude','Derived'),('mean_alpha_imag',float((p@alpha).imag),'amplitude','Derived'),
        ('mean_X',float(p@x),'quadrature','Derived'),('Var_X',float(p@x**2-(p@x)**2),'SNU','Derived'),
        ('peak_photons',float(max(abs(alpha)**2)),'photons','Derived'),('support_size',len(p),'symbols','Verified')]:
        field={'M':'support_size','VA':'V_A_hex','nu_raw':'nu_mb_raw_hex','nu_repo':'nu_mb_repo_hex',
            'C':'C','w':'w','source_hash':'ensemble_hash','support_size':'support_size'}.get(name)
        provenance=source+field if field else origin(parameter_rows)+'; '+origin(a.legacy.load_catalog)
        add('E Modulation protocol',name,value,unit,'A/B',kind,provenance+'; '+origin(a.validate_source),
            'Same authenticated ensemble in both models; X=2Re(alpha), VA=2*nbar')
    add('E Modulation protocol','MB_mapping','nu_repo=42.5*nu_raw','equation','A/B','Exact source metadata',source+'mb_convention')
    add('E Modulation protocol','beta',.95,'dimensionless','A/B','Specified in evaluator',origin(a.evaluate_physical)+'; '+lit)
    add('E Modulation protocol','measurement','homodyne one real quadrature','type','A/B','Specified current request',origin(a.homodyne_mi))
    add('E Modulation protocol','reconciliation','reverse, asymptotic','type','A/B','Specified protocol','protocol.json; '+old_path)
    add('E Modulation protocol','source_moment_route',c['source_moment_route'],'method','A/B','Exact source metadata',source+'source_moment_route',
        'Reuses existing arbitrary-precision source payload; no new source moment computation')
    for key,value in read(ROOT/payload)['source_settings'].items():
        add('G Numerical','cached_source_'+key,json.dumps(value),'digits' if key=='precision_ladder' else 'absolute tolerance',
            'A/B','Historical source metadata',source+'source_settings.'+key,'Settings of reused source calculation; no fresh AP certification')
    for name,value,unit in [('M0',1.,'probability'),('E_eta',mo['m1'],'power fraction'),
        ('E_sqrt_eta',mo['mh'],'amplitude fraction'),('eta_f',A['eta_f'],'power fraction'),
        ('E_eta_xi_pre_detector',A['mean_eta_xi_pre_detector'],'SNU'),('E_eta_xi_after_detector',A['mean_eta_xi_after_detector'],'SNU'),
        ('N_fading_pre',A['N_fading_pre'],'SNU'),('N_channel_pre',A['N_channel_pre'],'SNU'),
        ('N_electronic_pre',A['N_detector_pre'],'SNU'),('N_post',A['N_post'],'SNU'),
        ('xi_f_input_quantum',A['xi_f'],'input-referred SNU'),('sigma2_MI',A['sigma2_MI'],'SNU output'),
        ('T_Holevo',A['T_quantum'],'power fraction'),('Bob_unconditional_variance',A['b'],'SNU output')]:
        add('F Effective channel',name,value,unit,'A','Derived',passive+'; '+phys,
            'Physical detector output; pre and post reference planes distinguished')
    for name,key in [('M0','M0'),('tail_outside_0_1','raw_upper_tail_mass'),('E_eta','m1'),('E_sqrt_eta','mh')]:
        add('F Effective channel',name,raw[key],'probability' if name in ['M0','tail_outside_0_1'] else 'dimensionless','B','Derived diagnostic',
            origin(a.raw_pdf_moments),'Unnormalized retained-law moment; not a validated probability model')
    for key in ['eta_f','mean_eta_xi','N_fading','N_effective','xi_f','sigma2_MI','T_Holevo','zero_atom_noise_contribution','active_only_mean_eta_xi']:
        add('F Effective channel',key,B[key],'dimensionless' if key in ['eta_f','T_Holevo'] else 'SNU','B','Derived diagnostic',lit,
            'Diagnostic coefficients only; failed PDF mass prevents MI/Holevo/SKR evaluation')
    for name,value,unit,note in [('moment_width_GH',32,'nodes','Historical moment computation unchanged'),
        ('MI_GH_primary',128,'nodes','Comparison to GH64; same source/moments'),
        ('full_Z_grid_primary',129,'nodes','Comparison to33; numerical resolution, not global certification'),
        ('source_model_decimal_precision',80,'digits','Preserved imported historical mpmath setting'),
        ('raw_PDF_decimal_precision',90,'digits','Original audit closed form'),
        ('entropy_check_precision','80 and 110','digits','Independent entropy formula'),
        ('mass_tolerance',1e-10,'absolute','Inherited unchanged before evaluation'),
        ('MI_absolute_tolerance',2e-10,'bits/use','Independent adaptive integration and GH agreement'),
        ('Holevo_absolute_tolerance',2e-8,'bits/use','Grid33/129'),
        ('rate_denominator','all transmitted uses including AoA outage','uses','No postselection or factor2'),
        ('repetition_rate','UNKNOWN_NOT_MODELED','Hz','No bits/s claim')]:
        add('G Numerical',name,value,unit,'A/B','Specified numerical rule','protocol.json; '+passive+'; '+origin(a.raw_pdf_moments),note)
    return data


def report(parameters,A,B,raw,checks,c,saved):
    def f(value):
        if value is None:return 'BLOCKED'
        return str(value) if isinstance(value,str) else format(value,'.15g') if isinstance(value,(int,float)) else str(value)
    def table(headers,values):
        return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join(
            '| '+' | '.join(f(x).replace('|','/') for x in row)+' |\n' for row in values)+'\n'
    groups=[]
    for group in dict.fromkeys(x['group'] for x in parameters):
        groups.append('### '+group+'\n\n'+table(['Parameter','Giá trị','Đơn vị','Model','Chỉ định / suy ra','Nguồn chính xác','Ghi chú'],
            [[x[k] for k in ['parameter','value','unit','model','specified_or_derived','configuration_source','note']] for x in parameters if x['group']==group]))
    comparison=table(['Đại lượng','Model A — random-width lịch sử','Model B — PDF43, ξdet=.005'],
        [[name,A.get(ka),B.get(kb)] for name,ka,kb in [
            ('Trạng thái','status','status'),('E[eta]','m1','m1'),('E[sqrt(eta)]','mh','mh'),
            ('eta_f','eta_f','eta_f'),('E[eta*xi] trước detector / literal','mean_eta_xi_pre_detector','mean_eta_xi'),
            ('N tại output MI','N_post','N_effective'),('xi_f input quantum','xi_f','xi_f'),
            ('sigma_N^2','sigma2_MI','sigma2_MI'),('T quantum Holevo','T_quantum','T_Holevo'),
            ('I_AB','I_AB','I_AB'),('beta*I_AB','beta_I_AB','beta_I_AB'),('chi_BE','chi_BE','chi_BE'),
            ('K raw (bits/use)','K_raw','K_raw')]])
    moments=table(['Moment / mass','Closed form','Tích phân độc lập','Sai khác'],
        [[q,x['closed'],x['value'],x['residual']] for q,x in raw['direct'].items()])
    body=rf'''# Cấu hình receiver30: truy vết tham số và kiểm chứng hai mô hình

**Model A tái lập K={A['K_raw']:.17g} bits/use. Model B bị BLOCKED vì PDF không đạt tolerance1e-10.** Đây là kiểm tra đúng một cấu hình cố định, không tối ưu VA,ν hoặc aperture. Tất cả code mới, report và receipts ở thư mục con này; tệp/caches/kết quả cha không bị ghi đè.

## 1. Bảng đầy đủ tham số thực tế

Mỗi giá trị có unit, trạng thái chỉ định/suy ra, file:function-line hoặc JSON/CSV pointer. parameters.csv giữ bảng dạng máy đọc. Tham số geometry35µrad/1.561µrad/.1m/0° là override thực tế; không lấy223/233µrad,15.61µrad,1m hoặc30° từ baseline. Source chính là historical_regressions.json#receiver30.saved và chuỗi caller parameter_adapter.optical → numeric.optical → power_conserving. Cấu hình configs/channel.yaml là production khác và không được dùng thay thế.

{''.join(groups)}

## 2. Hai mô hình và mặt phẳng noise

**Model A** giữ nguyên power_conserving_random_width. Đặt \(S\sim N(-v/2,v)\), \(w(S)=w_{{eff}}\exp(-S/2)\). Gaussian beam chuẩn hóa công suất được thu bằng circular-aperture ncx2 CDF tại từng width/offset; AoA thêm atom0. Vì vậy \(0\leq\eta\leq\eta_{{atm}}=.92\), tổng mass1 và không có upper-tail ngoài1. Width dispersion này là surrogate đã khai báo; không đồng nhất với PDF tích lognormal×pointing củaB.

Đặt \(T_f=m_h^2\), \(N_f=(m_1-T_f)V_A\), \(N_c=.0186m_1\). Detector untrusted có \(\eta_d=.95\), output electronics \(\epsilon_d=.005\):

\[
T_q=.95T_f,\quad N_{{post}}=.95(N_f+N_c)+.005,\quad \sigma_N^2=1+N_{{post}}.
\]

Pre-detector noise budget có \(\langle\eta\xi_A\rangle=.0186m_1+.005/.95\). Sau detector, phần channel/electronic là \(.95(.0186m_1)+.005\). \(\xi_{{f,A}}=N_{{post}}/T_q\), tương đương \(N_{{pre}}/T_f\). Vacuum tại physical output là1, không cộng thêm loss vacuum lần nữa. Cùng \(T_q,N_{{post}}\) trong DBL full-Z,covariance và homodyne \(\nu_3=\sqrt{{a(a-Z^2/b)}}\).

**Model B** dùng chính PDF43 trên[0,1], cùng geometry và source, nhưng \(\xi_{{det}}=.005\) là tham số độc lập theo yêu cầu hiện tại:

\[
\xi_B(\eta)=.0186+\frac{{.005}}{{\eta}},\quad
m_n=.0186m_1+.005M_0,\quad
N_B=(m_1-m_h^2)V_A+m_n,\quad
\sigma_{{N,B}}^2=1+N_B,\quad T_B=m_h^2.
\]

**Không có ηdet trong Model B**, không chuyển .005 thành .005/.95 và không nhân transmittance/noise thêm. Mean homodyne là \(2\sqrt{{T_B}}\operatorname{{Re}}\alpha_k\); sửa mean phức của phương trình in để tạo real1D density theo yêu cầu Gaussian homodyne hiện tại. Nếu mass hợp lệ, các tham số \(T_B,N_B\) phải đi nguyên vào bound/covariance/Holevo; ở đây gate mass đã chặn trước phép tính MI/Holevo.

{comparison}

Các sigma² và xi_f củaB là **diagnostic coefficients từ unnormalized moments**, không phải xác nhận channel vật lý. Không ghép MI củaA với Holevo củaB, không nhân homodyne MI lên2. Conditional noise khác Bob unconditional variance \(b=1+TV_A+N\).

## 3. Chuẩn hóa PDF43 và ba moment

M0 (decimal90-derived) = {raw['M0_decimal']}.

Mass ngoài[0,1] = **{raw['upper_tail_decimal']}**. Nó lớn hơn ngưỡng1e-10, nên giữ **FAILED** dù chỉ vượt khoảng5,7%. Atom AoA \(P_0={raw['P0']:.17g}\) được cộng riêng vào zeroth moment.

{moments}

moments.csv có cả mass tổng/mass tail/three noise moments checks. \(\langle\eta\xi_B\rangle\) đối chiếu linear combination của hai quadrature độc lập0/1 cộng atom: \(.0186\int_0^1\eta f(\eta)d\eta+.005[P_0+\int_0^1 f(\eta)d\eta]\).
Zero-limit extension \(\lim_{{\eta\to0}}\eta\xi_B(\eta)=.005\) cho phần atom bằng {B['zero_atom_noise_contribution']:.17g}. Active-only bỏ phần đó; giá trị so sánh được lưu riêng, không áp dụng postselection.

Nguyên nhân: irradiance lognormal unbounded, aperture-equivalent pointing tối đa hữu hạn, nên tích raw vẫn có xác suấtη>1. Tích phân giữ tới1 bỏ tail nhưng không chuẩn hóa lại. Không clipping/renormalization/chuyển tail sang outage/thay PDF bằng random-width. Model B ghi MI,βMI,Holevo,K là unavailable/BLOCKED, không phải0.

## 4. Tái lập, provenance và giới hạn

Model A so sánh trực tiếp với corrected_same_channel.csv#receiver30 và old_vs_new.csv#receiver30; numerical_checks.json ghi từng residual và independent check. MI GH64/128,256-symbol/16-level/X/P/scaling,adaptive integration,full-Z33/129,entropy80/110 và uncertainty/symplectic matrix được kiểm tra riêng. Source hash là {c['ensemble_hash']}; C={c['C']:.17g},w={c['w']:.17g},payloadSHA={c['source_sha256']}. Source units VA=2nbar; không đổi thành nbar/2.

Giá trị pooled fading MI cũ ở selection.json là {saved['I_AB']:.17g}, K={saved['K_raw']:.17g}. **Không dùng nó thay Gaussian MI** đang kiểm tra; con số dương mục tiêu0.005392532654035664 thuộc Gaussian effective random-width modelA với detector. Cả hai số cũ được giữ đúng context.

Parameter A0 và curvature cần đọc đúng vai trò: A dùng exact circular collection với width ngẫu nhiên nên không có A0 cố định; A0_erf/w_eq thuộcB. Launch curvature không được truyền như tham số: wL dùng waist-plane formula, tương đương launchR=∞; curvature tại receiver không được lưu/dùng. Không lấy một radius chưa có từ manuscript. AO/phaseOFF; thêm coupling/insertion loss, saturation,LO,bandwidth,rate và hardware calibration không được mô hình hóa.

{sum(x['status']=='CURRENTLY_VERIFIED_PASS' for x in checks)} scoped checks đạt; PDF normalization củaB là phát hiện FAILED được giữ, không bị đổi thành PASS. Đây không là toàn bộ test suite hoặc security certification. Fixed-source moments được lấy nguyên từ cache arbitrary-precision cũ; không chạy lại AP. Full-Z finite numerical maximization không là rigorous global enclosure. Moment-matched Gaussian MI không là exact conditional density của fading. Chưa có operational fading/parameter-estimation/finite-key/composable proof hoặc xác nhận hardware.

Lần đầu dựng bảng provenance gặp TypeError vì inspect nhận lru_cache wrapper. attempt_1/ giữ code/protocol/lỗi; helper đã unwrap đúng function trước khi lấy file/dòng. Các phép tính được kiểm tra lại sau sửa helper; không đổi phương trình hoặc tolerance.

Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,ObjectiveC USER_STOPPED. Frozen SHA hiện tại khác historical expected trong AGENTS nhưng không thay đổi; không promotion. Parent seal đã PASS trước khi task này cập nhật ledger. Các artifact hash cũ giữ nguyên; ledger hashes cũ là snapshot lịch sử, nên verifier cha không phải verifier cho ledger của task mới. verify.py của thư mục con kiểm tra snapshot/protected files và artifacts task này.

Lệnh đã chạy từ project root:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/inspect_receiver30.py

Không chạy lại producer đã hoàn tất. Kiểm tra chỉ đọc:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/receiver30_configuration_verification_20261023/verify.py

Không production/security-source/frozen/cache edits,optimization,training/final-test/heldout/publication,baseline/threshold approval hoặc commit/push.
'''
    (OUT/'report_vi.md').write_text(body,encoding='utf-8')


def main():
    if (OUT/'results.json').exists():raise FileExistsError('Preserve completed fixed-point reproduction')
    protocol=read(OUT/'protocol.json')
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(check=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED',detail=detail))
        if not ok:
            save('failed_checks.json',checks);raise AssertionError((name,detail))
    ref=next(x for x in read(PARENT/'historical_regressions.json')['records'] if x['label']=='receiver30')
    saved=ref['saved'];p=r.parameters(saved);c=r.source(saved)
    check('Exact requested source identity',c['ensemble_hash']==protocol['source_hash'])
    probabilities,alpha=a.validate_source(c)
    check('Fixed geometry and source parameters',p==(20.,1.,0.,35.,1.561,.1,.95,.005,.92,.3)
        and c['VA']==protocol['source']['VA'] and c['nu_raw']==.25)
    ch,mo=r.adapter().optical(.3,35.,1.561,.1,0.)
    for key in ['m1','mh','eta_f','P0']:
        check('Fresh historical channel '+key,abs(mo[key]-saved[key])<5e-12)
    for key in ['w0_m','wL_m','w_eff_m','G_d','sigma_s_m']:
        check('Fresh optical '+key,abs(float(ch[key])-saved[key])<5e-12)
    moments=dict(M0=mo['physical_mass'],m1=mo['m1'],mh=mo['mh'],P0=mo['P0'],law=mo['treatment'])
    A=a.evaluate_physical(c,moments,.95,.005,order=128,grid=129)
    A.update(status='CURRENTLY_VERIFIED_PASS_COMPONENT_ONLY',m1=mo['m1'],mh=mo['mh'],
        mean_eta_xi_pre_detector=.0186*mo['m1']+.005/.95,
        mean_eta_xi_after_detector=.95*.0186*mo['m1']+.005,
        xi_f=A['N_post']/A['T_quantum'],sigma2_MI=A['sigma2_output'])
    old=next(x for x in r.csvrows(PARENT/'corrected_same_channel.csv') if x['scenario']=='receiver30')
    for key in ['I_AB','chi_BE','K_raw']:
        check('Model A Gaussian reproduction '+key,abs(A[key]-float(old[key]))<5e-12,
            dict(saved=float(old[key]),fresh=A[key],delta=A[key]-float(old[key])))
    coarse=a.evaluate_physical(c,moments,.95,.005,order=64,grid=33)
    check('GH64/128',abs(coarse['I_AB']-A['I_AB'])<2e-10)
    check('Full Z33/129',abs(coarse['chi_BE']-A['chi_BE'])<2e-8)
    independent,error=a.independent_mi(probabilities,alpha,A['T_quantum'],A['sigma2_MI'])
    check('Independent adaptive MI',abs(independent-A['I_AB'])<2e-10 and error<2e-10,
        dict(adaptive=independent,reported_error=error))
    for digits in [80,110]:
        value=independent_entropy(A,digits)
        check('Independent entropy '+str(digits),abs(value-A['chi_BE'])<2e-11,dict(value=value))
    full=a.homodyne_mi(probabilities,alpha,A['T_quantum'],A['sigma2_MI'],order=128,grouped=False)
    y=a.homodyne_mi(probabilities,alpha,A['T_quantum'],A['sigma2_MI'],order=128,axis='P')
    check('256 symbols equal16 levels',abs(full-A['I_AB'])<2e-12)
    check('X and P symmetry',abs(y-A['I_AB'])<2e-12)
    check('Invertible measurement scaling',abs(A['I_AB']-A['I_AB_rescaled'])<2e-12)
    masses=[]
    for level in np.unique(2*alpha.real):
        mean=math.sqrt(A['T_quantum'])*level
        mass,err=quad(lambda y:a.conditional_pdf(y,mean,A['sigma2_MI']),-math.inf,math.inf,epsabs=1e-12,epsrel=1e-12)
        masses.append(dict(level=level,mass=mass,error=err))
    check('All16 conditional densities normalized',all(abs(x['mass']-1)<2e-10 for x in masses))
    gamma=np.array([[A['a'],0,A['Z_worst'],0],[0,A['a'],0,-A['Z_worst']],
        [A['Z_worst'],0,A['b'],0],[0,-A['Z_worst'],0,A['b']]])
    omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
    uncertainty=float(np.linalg.eigvalsh(gamma+1j*omega).min())
    eigen=np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    check('Independent uncertainty matrix',uncertainty>=-1e-11,uncertainty)
    check('Independent symplectic spectrum',max(abs(eigen-np.sort([A['nu_1'],A['nu_2']])))<1e-10,eigen.tolist())
    raw_ch=r.raw_channel(p);raw=a.raw_pdf_moments(raw_ch)
    previous=next(x for x in read(PARENT/'channel_pdf_audit.json')['contexts'] if x['context']=='receiver30')
    check('Reproduce raw PDF mass deficit',abs(raw['raw_upper_tail_mass']-previous['raw_upper_tail_mass'])<1e-20,
        dict(saved=previous['raw_upper_tail_mass'],fresh=raw['raw_upper_tail_mass']))
    for q,x in raw['direct'].items():
        check('Raw PDF independent moment '+str(q),abs(x['residual'])<2e-10)
    check('Tail direct quadrature',abs(raw['upper_tail_quadrature']-raw['raw_upper_tail_mass'])<2e-12)
    check('Unchanged outcome-independent mass threshold',protocol['mass_tolerance']==1e-10)
    check('Raw PDF failure explicitly retained',not raw['normalized_within_tolerance'] and raw['raw_upper_tail_mass']>1e-10)
    B=literal_model_B(c,raw,.005,protocol['mass_tolerance'])
    check('Model B has no efficiency argument','eta_det' not in inspect.signature(literal_model_B).parameters
        and 'eta_det' not in B and B['xi_det']==.005)
    check('Model B blocked without numerical information rates',B['status']=='BLOCKED_BY_SCIENTIFIC_MODEL'
        and all(B[k] is None for k in ['I_AB','beta_I_AB','chi_BE','K_raw']))
    direct_noise=.0186*raw['direct'][1.]['value']+.005*(raw['P0']+raw['direct'][0.]['value'])
    check('Third noise moment independent quadrature',abs(direct_noise-B['mean_eta_xi'])<2e-10,
        dict(closed=B['mean_eta_xi'],direct=direct_noise,residual=direct_noise-B['mean_eta_xi']))
    check('Zero atom versus active-only noise',abs(B['mean_eta_xi']-B['active_only_mean_eta_xi']-.005*raw['P0'])<1e-15)
    check('Unnormalized B fixture fails closed',literal_model_B(c,{**raw,'M0':.98},.005,1e-10)['K_raw'] is None)
    check('Positive A is diagnostic not security-approved',A['K_raw']>0 and not A['security_valid'])
    params=parameter_rows(ch,raw_ch,mo,c,A,B,raw,saved)
    check('Every parameter has unit source and derivation class',all(x['unit'] and x['configuration_source'] and x['specified_or_derived'] for x in params))
    save('results.json',dict(model_A=A,model_B=B,model_A_channel=ch,model_A_moments=mo,
        model_B_channel=raw_ch,model_B_PDF=raw,source_identity={k:c[k] for k in c if k not in ['p','alpha']},
        source_payload_metadata=read(ROOT/c['source_path']),no_optimization=True,
        no_new_source_moments=True,security_valid=False))
    save('numerical_checks.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,
        expected_scientific_failure='Model B PDF mass is outside1e-10; rates BLOCKED',new_scientific_default=False))
    write('parameters.csv',params);write('conditional_normalization.csv',masses)
    moment_rows=[dict(moment=str(q),closed=x['closed'],direct=x['value'],residual=x['residual']) for q,x in raw['direct'].items()]
    moment_rows.extend([
        dict(moment='M0_total_including_atom',closed=raw['M0'],direct=raw['P0']+raw['direct'][0.]['value'],residual=raw['P0']+raw['direct'][0.]['value']-raw['M0']),
        dict(moment='tail_above1',closed=raw['raw_upper_tail_mass'],direct=raw['upper_tail_quadrature'],residual=raw['upper_tail_quadrature']-raw['raw_upper_tail_mass']),
        dict(moment='mean_eta_xi_B_zero_limit',closed=B['mean_eta_xi'],direct=direct_noise,residual=direct_noise-B['mean_eta_xi'])])
    write('moments.csv',moment_rows)
    report(params,A,B,raw,checks,c,saved)
    save('execution_history.json',dict(producer_sha256=a.sha(Path(__file__)),protocol_sha256=a.sha(OUT/'protocol.json'),
        computations='One fixed geometry/source; ModelA Gaussian replay and independent checks; ModelB moments/noise then blocked before MI/Holevo',
        optimization=False,source_AP=False,source_interpolation=False,publication_test=False,
        scientific_model_changes='New isolated ModelB explicit xi_det=.005,no efficiency; historical code unchanged',
        tests=len(checks),parameter_rows=len(params)))
    print('COMPLETE',len(params),'parameters;',len(checks),'scoped checks; A K=',A['K_raw'],'; B BLOCKED',flush=True)


if __name__=='__main__':
    main()
