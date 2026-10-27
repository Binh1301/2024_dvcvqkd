"""Render saved fixed8cm results: eight figures, four tables and Vietnamese report."""
import csv
import math
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
from matplotlib.patches import Rectangle
from PIL import Image
import search as s


def rows(name):
    result=[]
    with (s.OUT/name).open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            for k,v in r.items():
                try:r[k]=float(v)
                except (TypeError,ValueError):pass
            result.append(r)
    return result


def table(headers,data):
    def fmt(v):return f'{v:.12g}' if isinstance(v,(int,float,np.number)) else str(v)
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(fmt(v) for v in r)+' |\n' for r in data)+'\n'


def main():
    sel=s.read(s.OUT/'selection.json');base=sel['baseline'];selected=sel['recommendations'];A,B,C=selected
    sensitivity=rows('table_1_individual_sensitivity.csv');curves=rows('figure_data.csv');robust=rows('robustness.csv')
    worst=rows('robustness_worst_fine.csv');weather=rows('weather_sensitivity.csv');comp=rows('source_comparisons.csv')
    roots=rows('thresholds.csv');root_status=rows('threshold_status.csv');matched=rows('same_energy_shaping.csv');phase1=s.read(s.OUT/'phase1.json')
    extra=s.read(s.OUT/'necessity.json')['additional_positive_original_geometry']
    labels={A['configuration']:'A: original detector',B['configuration']:'B: detector assisted',C['configuration']:'C: best nonideal tested'}
    vn={A['configuration']:'A — Detector gốc',B['configuration']:'B — Có hỗ trợ detector',C['configuration']:'C — Nonideal tốt nhất đã thử','C_original_geometry_tiny_margin':'C0 — Geometry gốc, sát ngưỡng'}
    colors=['#0072B2','#D55E00','#009E73'];markers=['s','D','^'];checks=[];figdir=s.OUT/'figures';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':9,'axes.labelsize':9,
        'legend.fontsize':6.8,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.7,'lines.linewidth':1.0})
    def save(fig,name,description):
        fig.text(.5,.012,'Fixed 8 cm Rx; untrusted detector; numerical diagnostic only',ha='center',fontsize=6.5)
        fig.tight_layout(rect=[0,.045,1,1]);pdf=figdir/(name+'.pdf');png=figdir/(name+'.png')
        fig.savefig(pdf);fig.savefig(png,dpi=350)
        data=pdf.read_bytes();assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1 and b'/Subtype /Image' not in data
        with Image.open(png) as im:
            assert min(im.size)>1000 and min(im.info['dpi'])>=349
            checks.append(dict(name=name,description=description,pixels=list(im.size),dpi=list(im.info['dpi']),vector_pdf=True,pages=1))
        plt.close(fig)
    scans=[(1,'zenith','L_km','HAP–UAV distance (km)','zenith'),(2,'zenith','zenith_deg','Zenith angle (deg)','zenith'),
        (3,'efficiency','eta_det','Detector efficiency','detector_efficiency'),(4,'noise','epsilon_det','Detector output excess noise (SNU)','detector_noise'),
        (5,'divergence','divergence_urad','Full-angle beam divergence (µrad)','divergence'),(6,'pointing','jitter_urad','Angular pointing jitter (µrad)','angular_jitter')]
    for number,kind,xkey,xlabel,stage in scans:
        fig,ax=plt.subplots(figsize=(4.8,3.6));ax.axhline(0,color='black',ls='--',lw=.8,label='$K=0$')
        original=sorted([r for r in sensitivity if r['changed_parameter']==stage],key=lambda r:r[xkey])
        ax.plot([r[xkey] for r in original],[r['K_raw'] for r in original],'ko--',ms=2.5,label='Original optics / fixed MB')
        for r,color,marker in zip(selected,colors,markers):
            data=sorted([x for x in curves if x['configuration']==r['configuration'] and x['figure']==kind],key=lambda x:x[xkey])
            ax.plot([x[xkey] for x in data],[x['K_raw'] for x in data],color=color,marker=marker,ms=3,label=labels[r['configuration']])
            ax.scatter(r[xkey],r['K_raw'],color=color,s=65,marker='*',zorder=8)
        ax.scatter(base[xkey],base['K_raw'],marker='*',s=80,color='black',label='Original baseline',zorder=9)
        ax.set_xlabel(xlabel);ax.set_ylabel('Raw SKR diagnostic (bit/use)');ax.set_yscale('symlog',linthresh=1e-4,base=10)
        if kind=='noise':ax.set_xscale('symlog',linthresh=1e-4,base=10)
        ax.grid(True,ls=':',alpha=.45)
        if number in [1,2]:ax.legend(frameon=False,fontsize=6.2,loc='center left',bbox_to_anchor=(.02,.29))
        else:ax.legend(frameon=False,fontsize=6.2,loc='best')
        if number in [1,2]:ax.set_title('20/1 km heights; all geometry terms recomputed',fontsize=9)
        save(fig,f'fig_{number}_{kind if number!=1 else "distance"}','Exact evaluated source nodes; all unplotted coordinates fixed for each curve. No interpolated optimization.')
    grid=rows('geometry_detector_grid.csv');angles=sorted({r['zenith_deg'] for r in grid});noise=sorted({r['epsilon_det'] for r in grid})
    matrix=np.full((len(noise),len(angles)),np.nan)
    for r in grid:matrix[noise.index(r['epsilon_det']),angles.index(r['zenith_deg'])]=r['K_raw']
    def edges(x):return np.r_[max(0,x[0]-(x[1]-x[0])/2),(np.array(x[:-1])+np.array(x[1:]))/2,x[-1]+(x[-1]-x[-2])/2]
    xx,yy=edges(angles),edges(noise);fig,ax=plt.subplots(figsize=(5.2,4.0))
    norm=SymLogNorm(linthresh=1e-4,vmin=float(np.nanmin(matrix)),vmax=float(np.nanmax(matrix)),base=10)
    mesh=ax.pcolormesh(xx,yy,matrix,cmap='coolwarm',norm=norm,edgecolors='white',linewidth=.3)
    for i in range(len(noise)):
        for j in range(len(angles)):
            if matrix[i,j]>0:ax.add_patch(Rectangle((xx[j],yy[i]),xx[j+1]-xx[j],yy[i+1]-yy[i],fill=False,edgecolor='black',lw=.8))
    boundary=rows('geometry_detector_roots.csv')
    if boundary:ax.scatter([r['zenith_deg'] for r in boundary],[r['epsilon_det_crit'] for r in boundary],color='black',marker='x',s=23,label='Exact $K=0$ roots',clip_on=False)
    ax.scatter(B['zenith_deg'],B['epsilon_det'],marker='*',s=80,color='yellow',edgecolor='black',label='B nominal')
    ax.set_yscale('symlog',linthresh=1e-4,base=10);ax.set_xlabel('Zenith angle (deg); distance 19–21.94 km');ax.set_ylabel('Detector output excess noise (SNU)')
    ax.set_title('B optics and exact source fixed; original heights',fontsize=9)
    ax.text(.02,.98,'Original optics lie outside this panel.\nOutline: sampled K>0; zero noise is diagnostic.',transform=ax.transAxes,fontsize=6.5,va='top',bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
    ax.legend(frameon=False,fontsize=6.5,loc='lower left');cb=fig.colorbar(mesh,ax=ax,label='Raw SKR (bit/use)');cb.solids.set_rasterized(False)
    save(fig,'fig_7_geometry_detector_boundary','49 exact geometry/noise nodes; black crosses are bracketed exact-evaluation roots, not contour interpolation')
    fig,ax=plt.subplots(figsize=(4.9,3.6));data=[base]+selected
    ax.bar(range(4),[r['K_raw'] for r in data],color=['gray']+colors,width=.6)
    ax.axhline(0,color='black',ls='--',lw=.8);ax.set_xticks(range(4),['Original','A\noptics/PAT','B\ndetector','C\nnonideal'])
    ax.set_ylabel('Raw SKR diagnostic (bit/use)');ax.grid(axis='y',ls=':',alpha=.4)
    for i,r in enumerate(data):ax.annotate(f"{r['K_raw']:.4g}",(i,r['K_raw']),xytext=(0,5 if r['K_raw']>=0 else -13),textcoords='offset points',ha='center',fontsize=8)
    ax.margins(y=.2);save(fig,'fig_8_configuration_comparison','Signed raw rates, same receiver8cm; Table4 separates actual MI, betaMI, Holevo and surrogate MI')
    s.save('figure_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',figures=checks,interpolated_source_moments=False,smoothed_optimization=False,one_plot_per_figure=True))
    modifications=[]
    for r in selected+extra:
        changed=[(k,old,new) for k,old,new in zip(s.FIELDS,s.BASE,s.parameters(r)) if abs(new-old)>1e-12]
        modifications.append(dict(configuration=r['configuration'],physical_parameters_changed=len(changed),parameters_changed='; '.join(k for k,_,_ in changed),
            original_values='; '.join(f'{k}={old:g}' for k,old,_ in changed),new_values='; '.join(f'{k}={new:.12g}' for k,_,new in changed),
            source_parameters_changed=int(r['VA']!=base['VA'])+int(r['nu_raw']!=base['nu_raw']),K_raw=r['K_raw'],
            divergence_reduction_factor=233/r['divergence_urad'],angular_SD_reduction_factor=15.61/r['jitter_urad'],horizontal_SD_reduction_factor=1/r['sigma_h_m'],
            detector_noise_variance_reduction_factor=.0135/r['epsilon_det'],detector_efficiency_relative_change=r['eta_det']/.8-1,
            Tx99_cm=100*r['transmitter_diameter_99percent_m'],horizontal_separation_km=(r['h_hap_km']-r['h_uav_km'])*math.tan(math.radians(r['zenith_deg'])),
            engineering_implications='Residual tracking/PAT and detector specifications uncalibrated; optimistic reference, not certified hardware'))
    s.write('table_3_minimum_modifications.csv',modifications)
    s.write('table_4_SKR_decomposition.csv',[{**base,'configuration':'Original_bounded_baseline'}]+selected+extra)
    s.write('table_2_positive_8cm.csv',[r for r in selected+extra if r['K_raw']>0])
    # Both deltas are visible; only the same-model delta is a controlled effect.
    for r in sensitivity:
        r['delta_K_vs_historical_regression']=r['K_raw']-(-.0587243146799775588)
        r['historical_delta_scope']='INCLUDES_OPTICAL_MODEL_DIFFERENCE_NOT_CAUSAL'
    s.write('table_1_individual_sensitivity.csv',sensitivity)
    tx=[]
    for div in s.DIV:
        ch,_=s.n.optical(20.,1.,30.,div,15.61,1.,.92)
        tx.append(dict(divergence_full_urad=div,w0_m=ch['w0_m'],D_tx_99_cm=100*ch['transmitter_diameter_99percent_m'],D_tx_9999_cm=100*math.sqrt(2)*ch['transmitter_diameter_99percent_m']))
    s.write('transmitter_apertures.csv',tx)
    influence=[]
    for kind in dict.fromkeys(r['changed_parameter'] for r in sensitivity):
        r=max((x for x in sensitivity if x['changed_parameter']==kind),key=lambda x:x['K_raw'])
        influence.append([kind,r['modified_value'],r['K_raw'],r['delta_K']])
    recommend=B if B['K_raw']>0 else C
    boxed=(r'\['+'\n'+r'\boxed{\begin{gathered}'+'\n'
        +rf"D_r={recommend['D_r']:.3g}\,\mathrm{{m}},\quad \theta_{{\rm div}}={recommend['divergence_urad']:.6g}\,\mu\mathrm{{rad}},\quad \theta_{{\rm jt}}={recommend['jitter_urad']:.6g}\,\mu\mathrm{{rad}},"+r'\\'+'\n'
        +rf"\sigma_h={recommend['sigma_h_m']:.6g}\,\mathrm{{m}},\quad \zeta={recommend['zenith_deg']:.6g}^\circ,\quad L={recommend['L_km']:.12g}\,\mathrm{{km}},"+r'\\'+'\n'
        +rf"\eta_{{\rm det}}={recommend['eta_det']:.6g},\quad \epsilon_{{\rm det}}={recommend['epsilon_det']:.8g}\,\mathrm{{SNU}},\quad V_A={recommend['VA']:.12g},\quad \nu_{{\rm raw}}={recommend['nu_raw']:.6g},"+r'\\'+'\n'
        +rf"K={recommend['K_raw']:.12g}\,\mathrm{{bit/use}}"+'\n'+r'\end{gathered}}'+'\n'+r'\]')
    summary=table(['Cấu hình','HAP/UAV(km)','ζ(độ)','L(km)','Div(µrad)','Jitter(µrad)','σh(m)','ηdet','εdet','VA','νraw','K'],
        [[vn[r['configuration']],f"{r['h_hap_km']:g}/{r['h_uav_km']:g}",r['zenith_deg'],r['L_km'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['eta_det'],r['epsilon_det'],r['VA'],r['nu_raw'],r['K_raw']] for r in selected])
    source_gain=[]
    geometry_gain=[]
    for r in selected:
        zrows=[x for x in curves if x['configuration']==r['configuration'] and x['figure']=='zenith']
        k30=next(x['K_raw'] for x in zrows if x['zenith_deg']==30.)
        k15=next(x['K_raw'] for x in zrows if x['zenith_deg']==15.)
        geometry_gain.append([vn[r['configuration']],k30,k15,k15-k30])
        group=[x for x in comp if x['configuration']==r['configuration']]
        fixed=next(x for x in group if x['comparison']=='historical_fixed_MB');mb=next(x for x in group if x['comparison']=='MB_best_tested');uni=next(x for x in group if x['comparison']=='Uniform_best_tested')
        source_gain.append([vn[r['configuration']],fixed['K_raw'],uni['K_raw'],mb['K_raw'],mb['K_raw']-fixed['K_raw']])
    duplicate=s.parameters(B)==s.parameters(C) and B['ensemble_hash']==C['ensemble_hash']
    text=f'''# Giữ receiver8cm: geometry, detector và PAT — 2026-10-22

Đã thực hiện yêu cầu mới, giữ **Dr=.08m tại mọi node** và detector **UNTRUSTED**. Không quét lại khẩu độ thu. Regression lịch sử khớp K=-.058724314679977559 trước khi tìm kiếm. Kết quả chính dùng mô hình bounded circular-Gaussian đã chốt và actual pooled fading MI, không dùng effective-Gaussian MI thay thế.

**Detector gốc:** {'có điểm dương trong shortlist' if A['K_raw']>0 else 'chưa có điểm dương trong miền đã thử'}. Điểm A gần zero nhất được chọn ở độ cao20/1km có K={A['K_raw']:.12g}. **Detector hỗ trợ:** K_B={B['K_raw']:.12g}; **nonideal tốt nhất trong shortlist:** K_C={C['K_raw']:.12g}. Đây là numerical diagnostic; chưa có thiết kế nào được xác nhận hardware/security thực. {'B và C trùng nhau trong shortlist; không phải hai thiết kế độc lập.' if duplicate else 'B và C là hai bộ tham số được đánh giá riêng.'}

{summary}
Mọi tốc độ theo mỗi lần truyền, gồm outage; giữ K âm nguyên dấu. “Best” là best exact tested trong catalog233 nguồn, không global optimum. Các ngưỡng giữ nguồn cố định và chỉ có phạm vi nhánh đã có bracket.

## Baseline, provenance và khí quyển

K lịch sử=-.0587243146799775588 được tái tính bằng đúng hàm trial và saved moments. baseline bounded mới có m1={base['m1']:.15g}, Tf={base['eta_f']:.15g}, I={base['I_AB']:.15g}, chi={base['chi_BE']:.15g}, K={base['K_raw']:.15g}. Sự khác biệt hai baseline là đổi optical law ở nghiên cứu trước; không ép hai mô hình trả cùng số. regression.json và geometry_regression.json xác minh riêng trước StageA. DeltaK chính của Table1 lấy baseline bounded cùng mô hình; delta so historical được lưu thêm và ghi rõ không là causal sensitivity.

Baseline: HAP20km,UAV1km,ζ30°,L21.9393102292km,lambda1550nm,Dr8cm,full-angle divergence233µrad,theta_jt15.61µrad mỗi trục,sigma_h1m,AoA SD1.5mrad,FOVhalf6.25mrad,tau_zen.92,epsilon_ch.0186,eta_det.8,epsilon_det.0135 outputquadratureSNU,beta.95,homodyne1D,AO/phaseOFF như giả thiết trước. configs/channel.yaml/default.yaml có223µrad ởtheta_div_rad; không phải angularjitter. Điểm223 được lưu riêng, không thay baseline233.

Bạn cung cấp các cặp(Vkm,tau_zen)=(23,.92),(15,.89),(5,.75), lưu weather_input.json. Dùng eta_atm=tau_zen^secζ trực tiếp, visibility chỉ là nhãn; không nhân thêmKruse. Bảng này **chưa phải vertical extinction profile**. HAP/UAV thay đổi độ cao vẫn được tính lạiHV/diffraction/pointing/fading nhưng giữ zenith optical depth để làm sensitivity. Các điểm này mang HEIGHT_CHANGED_FIXED_TAU_SENSITIVITY_VERTICAL_EXTINCTION_MISSING, không đủ để xác nhận khí quyển hay khả năng bay. Chỉ chọn khuyến nghị ởHAP20/UAV1, nơi attenuation có cùng định nghĩa scenario gốc; không root L bằng cách tự thay độ cao.

## Mô hình và workflow

w0=2lambda/(pi theta_div), wL=w0 sqrt[1+(Llambda/(pi w0²))²], w_eff=wL sqrt(1+Gd), Dtx99=2w0 sqrt(ln100/2). Mọitheta_div làfullangle. HV dùng đúng profile wind21m/s,Cn²ground1e-14; hai tích phân theo độ cao được tính lại trên[h_UAV,h_HAP], cùng secζ factors cũ. L=(h_HAP-h_UAV)/cosζ và sigma_s²=sigma_h²+(Ltheta_jt)². Không chỉ scaleL mà giữ stale turbulence/beam terms.

Kênh thụ động cũ được tái sử dụng: S~N(-v/2,v), randomwidth w=w_eff exp(-S/2), Rayleigh offsetr; circularcollection H=F_noncentralChiSquare2(D_r²/w²;4r²/w²), activeT=eta_atm H. Giữ atomP0=exp[-FOV²/(2sigma_AoA²)] tạiT0 riêng; mỗi beam có tổng công suất1, không cógain hay clippingT. m1=E[T],mh=E[sqrtT],Tf=mh².

N_fading=(m1-Tf)VA,N_channel=.0186m1,N_detector=epsilon_det/eta_det;
N_post=eta_det(N_fading+N_channel)+epsilon_det;
a=1+VA,b=1+eta_det Tf VA+N_post.
Vacuum1 xuất hiện một lần; không thêm1-eta_det lần nữa vào excess. Untrusted assignment giữ cảdetectorloss/noise choEve. C,w lấy đúng payload/hash của cùng256state ensemble. Full-Z numerical maximization trên giao intervalcorrelation với physicalcovariance; nu3_hom=sqrt[a(a-z²/b)], không trộn heterodyneMI.

MI chính dùng p(y|x)=E_T Normal(y;2sqrt(eta_det T)x,1+eta_det*.0186T+epsilon_det). Không cộng N_fading lần nữa bên trong conditionalvariance, khôngCSIconditioning/postselection. K=.95I_actual-chi. I_AB_surrogate/K_surrogate được lưu riêng. Fourier inversion chỉ tăng tốc cùng Gaussianmixture; direct-likelihood và halfspacing checks có receipt.

StageA giữMB(.165,VA5.475). StageB stagedtiers và geometry hữu hạn, giữdetectorgốc; StageC nhắm các beam/pointing/noise regions, không Cartesian toàn bộ9tham số. StageD dùng233 sourceexact(197MB,36Uniform), targetedalternating4starts, dừngdeltaK1e-8/catalogfixedpoint. Không AP hoặc nội suyC,w/SKR. Các matching8cm nodes từ nghiên cứu trước được reuse theo sourcehash/parameters/quadrature và hash từng dòng; không reuse số khácreceiver/measurement/detector/weather. Các screened MI128x16 được refinement256x32/512x48/1024x64, observedchange<2e-6 và positive vượt2lần ảnh hưởng quan sát lênK. Đây không phải rigorous errorbound/security certification.

## Q1. Giữ8cm và detector gốc có SKR dương không?

{'Có trong các node được chọn; vẫn chỉ là diagnostic.' if A['K_raw']>0 else 'Chưa tìm được, kể cả sau catalog ở các context chọn và wider-beam checks.'} A dùng đúngeta=.8,epsilon=.0135; K={A['K_raw']:.12g}, gap chi-betaI={-A['K_raw']:.12g} bit/use khiKâm. Không suy ra no-key theorem ngoài miền/tập nguồn đã thử. Sáu geometry/PAT branches trong phase1.json, kể cả các height sensitivity, đều được giữ để kiểm chứng phạm vi.

## Q2. Rút ngắn liên kết giúp bao nhiêu?

GiữHAP20/UAV1, nadir rútL từ21.9393 xuống19km; từng nguồn/optics/detector được tính lại tạiζ0,5,...30. Figure1/2 và Table1 có số thực, không giả địnhK tăng đơn điệu. Ở nguồn cố định và pointing1m, khoảng cách ngắn hơn có thể tăng relativeoffset/fading và không làmK dương. Sau optics/PAT/detector upgrade, ảnh hưởng phụ thuộc beam và source; các đườngselected cho biết gain thực. HAP17..25/UAV1..5 sensitivity cóL12..27.7km nhưng attenuationtheoheight chưa hiệu chuẩn; không dùng để tuyên bố range hay độ cao vận hành tối ưu.

Đối chiếu riêng việc chuyển30°→15° ở cùng nguồn, optics và detector cho từng dòng (cả hai node cùng quadrature256x32):

{table(['Cấu hình','K tại30°/21.9393km','K tại15°/19.6702km','DeltaK do geometry'],geometry_gain)}

{table(['HAP/UAV(km)','ζ','L(km)','Div','VA','ν','K detector gốc — height sensitivity'],[[f"{r['h_hap_km']:g}/{r['h_uav_km']:g}",r['zenith_deg'],r['L_km'],r['divergence_urad'],r['VA'],r['nu_raw'],r['K_raw']] for r in phase1['B_catalog_best']])}

Kết hợp detector noise.001 với hai geometry thay đổi độ cao (chỉ sensitivity, chưa có vertical extinction calibration):

{table(['HAP/UAV(km)','L(km)','Div(µrad)','ηdet','εdet','VA','ν','K'],[[f"{r['h_hap_km']:g}/{r['h_uav_km']:g}",r['L_km'],r['divergence_urad'],r['eta_det'],r['epsilon_det'],r['VA'],r['nu_raw'],r['K_raw']] for r in rows('height_changed_detector_comparisons.csv')])}

## Q3. Tham số nào tác động lớn nhất?

{table(['Tham số','Giá trị cho K lớn nhất trong OFAT','K','DeltaK cùng model'],influence)}
Detector excessnoise có tác động lớn nhất ở baseline nguồn cố định. Các điểmeta=1/noise=0 chỉ là diagnosticreferences. Cải thiệnefficiency riêng không giải quyết geometry/PAT/fading; giảmdivergence không làgain miễn phí. “Ít âm hơn” trên kênh yếu không đồng nghĩa collection tốt hơn, nên shortlist dựa cảmomentquality vàK, không chỉ chọn điểm tối nhất cóHolevonhỏ.

## Q4. Chỉ nâng detector có đủ không?

OFAT không có điểm dương ở nguồn cố định. Catalogdetector-only có sẵn ởepsilon.0005 và0; đây là counterfactualtách riêng ởStageD, không đổi quang học gốc hoặc nguồn trongTable1. Xemcatalog_detector_only_*.csv. Không gọizero-noise là detector đạt được và không đổi thànhtrusted để có dương.

{table(['ηdet','εdet','VA','νraw','K best exact tested — optics gốc'],[[r['eta_det'],r['epsilon_det'],r['VA'],r['nu_raw'],r['K_raw']] for r in rows('catalog_shortlist.csv') if r['divergence_urad']==233 and r['jitter_urad']==15.61 and r['sigma_h_m']==1])}

## Q5. Những tổ hợp thay đổi nào tạo dương?

Table2 chỉ chứa các configurationcóactualK>0 sau refinement. Chúng cần đồng thờibeam/PAT/relativecentering vàdetector; giữDr8cm không đồng nghĩa giữ nguyên transmitter hoặc receiver electronics. Các thành phầnthayđổi mức20lần sigma_h, nhiều lần angularjitter/divergence/noise là yêu cầu mạnh, không tự gọi “moderate”. Rawpositive trong StageC source seed và source catalog được lưu riêng để xác định thay đổi nào đủ.

{summary}

Giữ cả geometry gốc30°/21.9393km cũng có một điểm dương nhỏ khi tăng efficiency lên.95. Đây là phép tính trực tiếp đã refinement, không phải khuyến nghị có margin:

{table(['Cấu hình','ζ','L(km)','ηdet','εdet','K','Observed MI change'],[[vn[r['configuration']],r['zenith_deg'],r['L_km'],r['eta_det'],r['epsilon_det'],r['K_raw'],r['observed_MI_change']] for r in extra])}

## Q6. Tập thay đổi tối thiểu và các ngưỡng là gì?

{table(['Cấu hình','Sốthayđổi vật lý','Tham số','Giá trị gốc','Giá trị mới','K'],[[vn[r['configuration']],r['physical_parameters_changed'],r['parameters_changed'],r['original_values'],r['new_values'],r['K_raw']] for r in modifications])}
Các count táchsourcechangesVA/nu khỏihardware/geometry. Đây là tối thiểu trongshortlist/coordinate relaxation đã thử, không chứng minh ít nhất toànmiền. Thresholds giữsourcefixed, target0 và1e-4; mốc1e-4 chỉ engineering comparison, không là định nghĩasecurity. Lcrit chỉ xuất khi bracketζ0..30 ởheights20/1 có signchange; không extrapolate dưới19km hoặc ngoàiheightweather hợp lệ.

B/C đều đòi hỏi divergence giảm 9.32 lần, angular SD giảm 15.61 lần, horizontal SD giảm 20 lần và detector noise variance giảm 27 lần. C nâng efficiency thêm 18.75% tương đối so với0.8. Đây là yêu cầu mạnh; không gọi là cải thiện nhỏ chỉ vì receiver vẫn8cm. B chuyển từ góc30° sang15°, tương ứng khoảng cách ngang tương đối từ10.97km xuống5.09km; chi phí di chuyển/điều khiển platform chưa được mô hình hóa.

necessary_changes.csv kiểm tra bằng cách hoàn nguyên từng biến của B/C về baseline, giữ các biến khác và nguồn cố định. Năm thay đổi vật lý của B đều cần cho dấu dương trên nhánh đó. Với C, hoàn nguyên geometry về30° vẫn còn K dương nhỏ; hoàn nguyên efficiency về.8 cho lại B dương. Do đó rút ngắn link và nâng efficiency là hai cách đánh đổi để tăng margin, không phải cả hai cùng bắt buộc cho mọi điểm dương. Kết luận này chỉ có phạm vi nhánh đã xét, không chứng minh tối thiểu toàn cục.

{table(['Cấu hình','Biến','TargetK','Root','Lcrit(km)','Residual'],[[r['configuration'],r['variable'],r['target_K'],r['root'],r['L_crit_km'],r['residual']] for r in roots])}
threshold_status.csv ghi cảNO_SIGN_CHANGE, cùng giá trị hai đầu; không tự gán ηcrit/Lcrit nếu không cóbracket. geometry_detector_roots.csv giữboundaryexactnoise/zenith cùngsource, Figure7 không nội suy tạo vùng tối ưu.

{table(['Cấu hình','Divergencecrit(µrad)','TargetK','Residual'],[[r['configuration'],r['root'],r['target_K'],r['residual']] for r in rows('divergence_thresholds.csv')])}

## Q7. MB có mở thêm vùngdương không?

{table(['Cấu hình','K fixedMB','K bestUniform (VA khác)','K bestMB (VA khác)','Gain chọn cảVA,ν'],source_gain)}
Để tách shaping khỏi việc chọn năng lượng, dùng cùng optics/detector và VA chung gần nhất có đủ hai nguồn exact:

{table(['Cấu hình','VA chung','K Uniform','K MB','DeltaK cùngVA','νMB'],[[r['configuration'],r['VA'],r['Uniform_K'],r['MB_K'],r['delta_K_same_VA'],r['nu_raw']] for r in matched])}
Hash riêng của hai nguồn nằm trong same_energy_shaping.csv; không dùng C,w của MB cho Uniform. So sánh hai family đã chọn VA khác nhau không được gọi toàn bộ là shaping gain. Dấu K của fixed MB so với best MB cho biết source adaptation có chuyển kết quả âm thành dương tại cùng kênh hay không. Nguồn thiếu không được nội suy. Đây là best exact tested, không phải tối ưu toàn cục.

## Q8. Dương có sống sót khi pointing xấu đi10–20% không?

{table(['Cấu hình','K nominal','K nhỏ nhất trong25 perturbations','Worst fine512x48'],[[vn[r['configuration']],r['K_raw'],min(x['K_raw'] for x in robust if x['configuration']==r['configuration']),next(x['K_raw'] for x in worst if x['configuration']==r['configuration'])] for r in selected])}
{table(['Cấu hình','Chỉ angular+20%','Chỉ horizontal+20%','Cảhai+10%','Cảhai+20%'],[[vn[r['configuration']]]+[next(x['K_raw'] for x in robust if x['configuration']==r['configuration'] and x['angular_factor']==fa and x['horizontal_factor']==fh) for fa,fh in [(1.2,1.),(1.,1.2),(1.1,1.1),(1.2,1.2)]] for r in selected])}
Mỗi trường hợp giữ nguồn, detector và optics của điểm nominal; nhân hai residual độc lập và đồng thời với các hệ số0.8,0.9,1,1.1,1.2. Không tái tối ưu nguồn để che việc mất margin. B mất dấu dương khi cả hai lỗi tăng10%. C còn dương khi cả hai tăng10%, nhưng K chỉ khoảng5.53e-5, thấp hơn mốc so sánh kỹ thuật1e-4. Cả B và C đều âm khi hai lỗi cùng tăng20%; chưa có ứng viên được chọn nào bền trước mức suy giảm này.

## Q9. Optics, PAT, độcao và detector có hợp lý không?

{table(['Cấu hình','Dtx99(cm)','wL(m)','w_eff(m)','sigma_s(m)','eta_atm','Pout'],[[vn[r['configuration']],100*r['transmitter_diameter_99percent_m'],r['wL_m'],r['w_eff_m'],r['sigma_s_m'],r['eta_atm'],r['P0']] for r in selected])}
Dtx99 chỉ là đường kính chứa99% công suất của Gaussian lý tưởng; chứa99.99% cần đường kính lớn hơn sqrt2 lần. Chưa có số đo về hard-pupil diffraction, M², coupling throughput, mount hoặc vibration; không xem receiver8cm là toàn bộ tải quang. HAP phải mang transmitter lớn hơn và hệ PAT chính xác hơn. [Walsh et al., coherent drone optical link](https://www.nature.com/articles/s41598-022-22027-0) dùng optical tracking và tip/tilt lồng nhau để giữ coupling. Đây là thí nghiệm truyền tin cổ điển, không chứng minh SKR hoặc các residual1µrad/0.05m tại khoảng cách và độ cao ở đây. GPS phục vụ acquisition/coarse; độ chính xác GPS không đồng nhất với độ lệch tâm beam còn dư.

theta_jt là residual transmitter pointing; sigma_h là sai lệch vị trí/tâm beam tương đối còn lại. Phép cộng variance giả định hai thành phần độc lập; không đếm cùng chuyển động hai lần. Receiver attitude/AoA được giữ riêng trong P0/FOV, không dùng việc giảm theta_jt để xóa outage. UAV ở5km hoặc HAP17–25km cần platform và operating envelope riêng, chưa mặc nhiên khả thi. Các khuyến nghị chính giữ độ cao20/1km để tránh phụ thuộc profile extinction còn thiếu.

epsilon_det là output quadrature excess noise trong SNU của mô hình; không tự đồng nhất với v_el của một bài khác. Nâng efficiency hoặc giảm noise cần hiệu chuẩn tại đúng LO power, bandwidth, shot noise, mode visibility và receiver coupling. Chưa có component specification hoặc số đo mass/power nên chưa cam kết đạt được. [Nghiên cứu kiểm soát excess noise](https://www.nature.com/articles/srep19201) là dẫn chứng về kỹ thuật kiểm soát noise, không xác nhận các mức noise/η của UAV hoặc security untrusted ở đây. Efficiency1 và noise0 chỉ là tham chiếu lý tưởng, không phải khuyến nghị phần cứng.

Với các cặp visibility/transmittance bạn cung cấp, giữ cùng nguồn và PAT:

{table(['Cấu hình','V(km)','tau_zen','eta_atm','K'],[[vn[r['configuration']],r['visibility_km'],r['tau_zen'],r['eta_atm'],r['K_raw']] for r in weather])}
Không cộng thêm Kruse, không giảm channel noise hoặc turbulence để tạo K dương. Các kiểm tra weather vẫn dùng HV gốc; không giả định visibility xác định Cn². Còn dương tại một weather case không đồng nghĩa chịu được weather xấu đồng thời với suy giảm pointing.

## Q10. Bộtham số nào đưa vào manuscript?

Trong manuscript, trình bày B như **ứng viên gần ngưỡng với ít thay đổi hơn**, giữ A âm làm đối chứng và dùng C để minh họa margin bổ sung khi tăng efficiency. Chưa có ứng viên đủ căn cứ để khuyến nghị triển khai thực tế hoặc gọi là bền trước suy giảm pointing20%. Không thay baseline production. Bộ tham số cụ thể của B đã được tính:

{boxed}

{table(['Cấu hình','m1','Tf','epsilon_f','I_actual','I_surrogate','betaI_actual','chi_BE','K'],[[vn[r['configuration']],r['m1'],r['eta_f'],r['epsilon_f'],r['I_AB'],r['I_AB_surrogate'],r['beta_I_AB'],r['chi_BE'],r['K_raw']] for r in selected])}

## Artifacts, kiểmtra và giới hạn

Table1: table_1_individual_sensitivity.csv; Table2: table_2_positive_8cm.csv; Table3: table_3_minimum_modifications.csv; Table4: table_4_SKR_decomposition.csv. all_evaluations.csv/evaluations.jsonl giữ noise decomposition, source identity, physicality và nguồn gốc direct/reused. Catalog và alternating logs ghi từng nguồn và bước P1/P2; không tạo số cho nguồn thiếu cache. height_changed_detector_comparisons.csv chỉ là sensitivity chưa có vertical calibration, không là bằng chứng phần cứng. selection_phase2.json giữ lựa chọn trước khi cập nhật A theo nguồn thắng của catalog cuối; selection.json là lựa chọn cuối.

Tám hình trong figures/ là các plot độc lập, có vector PDF và PNG350dpi; giữ K âm và đường K=0. Dữ liệu đều được đánh giá trực tiếp, đường nối chỉ giúp đọc node; không smooth fit hay nội suy source. validation.json và convergence.json chứa kiểm tra full-Z33/129, entropy110digits, width32/64, direct mixture/Fourier, half spacing, mass/support/PSD/spectrum, noise được tính một lần và HV tích phân độc lập. Quan sát hội tụ không phải rigorous security enclosure. Receipt và verify.py xác minh hash từ dữ liệu đã lưu, không chạy lại tìm kiếm.

Không thay scientific source, security code, cache, config, frozen model hoặc kết quả lịch sử. Không chạy receiver-aperture sweep, AP mới, training, final-test hoặc held-out publication evaluation. Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS và UNVALIDATED_SECURITY_MODEL; discrepancy frozen hash lịch sử và ObjectiveC USER_STOPPED giữ nguyên. Chưa xác minh finite-key, authentication, calibration, phase hardware hoặc proof cho fading tương quan; một functional dương chưa tự trở thành secure key rate thực.
'''
    # Presentation spacing only; all numeric strings remain unchanged.
    replacements={
        'receiver8cm':'receiver 8 cm','Dr8cm':'Dr 8 cm','Dr=.08m':'Dr = 0.08 m','StageA':'Stage A','StageB':'Stage B','StageC':'Stage C','StageD':'Stage D',
        'detectorhardware':'detector hardware','detectorgốc':'detector gốc','detectorloss':'detector loss','detectornoise':'detector noise','Detector excessnoise':'Detector excess noise',
        'sourcefixed':'source fixed','sourcechanges':'source changes','sourceexact':'source exact','sourcehash':'source hash','sourcecatalog':'source catalog','sourceinterpolation':'source interpolation',
        'Full-Z numerical':'Full-Z numerical','fullZ':'full Z','outputquadratureSNU':'output quadrature SNU','outputquadratureexcessSNU':'output quadrature excess SNU',
        'mỗi lần truyền':'mỗi lần truyền','Mọitheta_div':'Mọi theta_div','fullangle':'full angle','randomwidth':'random width','circularcollection':'circular collection',
        'conditionalvariance':'conditional variance','same256state':'same 256-state','physicalcovariance':'physical covariance','intervalcorrelation':'interval correlation',
        'chưafinitedkey':'Chưa finite-key','finitedkey':'finite-key','chưađược':'chưa được','chưa cóvertical':'chưa có vertical',
        'geometrygốc':'geometry gốc','opticsnominal':'optics nominal','nguồn/detector/opticsnominal':'nguồn/detector/optics nominal',
        'thayđổi':'thay đổi','tham số/nguồn':'tham số/nguồn','sốthayđổi':'số thay đổi','Sốthayđổi':'Số thay đổi','khuyếnnghị':'khuyến nghị','Bộtham số':'Bộ tham số',
        'dương bền20%':'dương bền 20%','cóứngviên':'có ứng viên','giữnguồn':'giữ nguồn','vùngdương':'vùng dương','chọnlàm':'chọn làm',
        'trong25':'trong 25','trongshortlist':'trong shortlist','tậpnguồn':'tập nguồn','toànmiền':'toàn miền','cùngVA':'cùng VA','cùngoptics':'cùng optics',
        'từng nguồn/optics':'từng nguồn/optics','phụthuộc':'phụ thuộc','khỏihardware':'khỏi hardware','khỏienergyadaptation':'khỏi energy adaptation',
        'mô hìnhbounded':'mô hình bounded','cùngmodel':'cùng model','các configurationcóactualK':'các configuration có actual K',
        'theoheight':'theo height','extinctionprofile':'extinction profile','verticalcalibration':'vertical calibration','Height_changed_detector_comparisons.csv':'height_changed_detector_comparisons.csv',
        'scientificsource/security/cache/config/frozenmodel':'scientific source/security/cache/config/frozen model','historicalresults':'historical results',
        'hardware/security thực':'hardware/security thực','ANTOAN':'an toàn','securekeyrate':'secure key rate','numericalpositivefunctional':'numerical positive functional',
        'Cảhai':'Cả hai','chỉ engineering':'chỉ engineering','định nghĩasecurity':'định nghĩa security','tái tối ưu source':'tái tối ưu source',
        'Dtx99 chỉ là Gaussianencircledpower':'Dtx99 chỉ là Gaussian encircled power','Gaussianencircledpower':'Gaussian encircled power',
        'támhình':'tám hình','Támhình':'Tám hình','Table1':'Table 1','Table2':'Table 2','Table3':'Table 3','Table4':'Table 4',
        'Figure1/2':'Figure 1/2','Figure7':'Figure 7','Figuredata':'Figure data','Allweatherchecks':'All weather checks',
        'vàdirect':'và direct','ngưỡnggiữ':'ngưỡng giữ','giữriêngtrong':'giữ riêng trong','độcao':'độ cao','độcaovận hành':'độ cao vận hành',
        'khảthi':'khả thi','phầncứng':'phần cứng','đượcxácnhận':'được xác nhận','đủnguồnexact':'đủ nguồn exact','một numerical':'một numerical',
        'Kâm':'K âm','Knominal':'K nominal','Kdương':'K dương','K0':'K = 0','giữnegativeK':'giữ negative K'
    }
    replacements.update({'catalog233':'catalog 233','ĐiểmA':'Điểm A','táchsourcechanges':'tách source changes','giữsourcefixed':'giữ source fixed',
        'detector-only':'detector-only','Catalogdetector':'Catalog detector','ởepsilon':'ở epsilon','và0':'và 0','counterfactualtách':'counterfactual tách',
        'Không gọizero':'Không gọi zero','thànhtrusted':'thành trusted','Xemcatalog':'Xem catalog','táchsource':'tách source','sourceadaptation':'source adaptation',
        'HAP20':'HAP 20','UAV1':'UAV 1','theta_jt15.61':'theta_jt 15.61','sigma_h1':'sigma_h 1','divergence233':'divergence 233',
        'khôngsmooth':'không smooth','cóbracket':'có bracket','giữboundaryexactnoise':'giữ boundary exact noise','cùngsource':'cùng source',
        'đượctính':'được tính','vàdetector':'và detector','cùngsource':'cùng source','bestMB':'best MB','fixedMB':'fixed MB'})
    for old,new in replacements.items():text=text.replace(old,new)
    text=re.sub(r',(?=[A-Za-z\u00c0-\u1ef9])',', ',text)
    text=re.sub(r'(?<![\w.])(\d+(?:\.\d+)?)(km|cm|m|µrad|SNU|mrad|nm|digits)\b',r'\1 \2',text)
    (s.OUT/'report_vi.md').write_text(text,encoding='utf-8')
    (s.OUT/'executive_conclusion_vi.md').write_text('Giữ receiver8cm và detector UNTRUSTED.\n\n'+summary+'\nĐây là numerical diagnostic, chưa xác nhận hardware/security; các yêu cầu PAT/noise có thể rất khắt khe.\n',encoding='utf-8')
    s.save('protocol.json',dict(receiver_fixed_m=.08,baseline=list(s.BASE),parameter_fields=s.FIELDS,source_catalog=233,primary_MI='ACTUAL_POOLED_FADING_LIKELIHOOD',
        source_fixed_stageA=dict(VA=5.475,nu_raw=.165),user_weather=s.read(s.OUT/'weather_input.json'),screen_quadrature=[128,16],selected_MI_change_tolerance=2e-6,
        source_coordinate_stop_deltaK=1e-8,engineering_K_target=1e-4,threshold_scope='FIXED_SOURCE_LOCAL; distance roots via original-height zenith only',
        height_extinction='MISSING_VERTICAL_PROFILE; changed heights sensitivity only',security_valid=False,hardware_validated=False))
    print('REPORT AND EIGHT FIGURES COMPLETE',flush=True)


if __name__=='__main__':main()
