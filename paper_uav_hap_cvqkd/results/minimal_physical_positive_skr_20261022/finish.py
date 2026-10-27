"""Seven standalone figures, three tables and Vietnamese evidence report."""
import csv
import json
import math
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm, LogNorm
from matplotlib.patches import Rectangle
from PIL import Image
import search as s


def rows(name):
    result=[]
    with (s.OUT/name).open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for k,v in row.items():
                try:row[k]=float(v)
                except (ValueError,TypeError):pass
            result.append(row)
    return result


def table(headers,data):
    def fmt(v):return f'{v:.12g}' if isinstance(v,(float,int,np.number)) else str(v)
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(fmt(v) for v in row)+' |\n' for row in data)+'\n'


def main():
    selection=s.read(s.OUT/'final_selection.json');final=selection['recommendations'];base=selection['baseline']
    names={'minimal':'1: refined minimum','balanced':'2: balanced','higher_performance':'3: higher rate'}
    vietnamese={'minimal':'1 — Ít thay đổi về khẩu độ thu','balanced':'2 — Cân bằng, có dự trữ pointing','higher_performance':'3 — Hiệu năng cao hơn, đòi hỏi Tx lớn'}
    A=rows('table_A_baseline_sensitivity.csv');allrows=rows('all_evaluations.csv')
    physical=rows('staged_physical_scan.csv');curves=rows('figure_sensitivity_data.csv')
    robust=rows('final_robustness.csv');roots=rows('refined_boundary_roots.csv');comparisons=rows('final_source_comparisons.csv')
    figures=s.OUT/'figures';figures.mkdir(exist_ok=True);figure_checks=[]
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':9,
        'axes.labelsize':9,'legend.fontsize':7,'xtick.labelsize':8,'ytick.labelsize':8,
        'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.7,'lines.linewidth':1.05})
    colors=['#0072B2','#D55E00','#009E73'];markers=['s','D','^']
    def start(xlabel,symlog=False):
        fig,ax=plt.subplots(figsize=(4.7,3.6));ax.axhline(0,color='black',ls='--',lw=.8,label='$K=0$')
        ax.set_xlabel(xlabel);ax.set_ylabel('Raw SKR diagnostic (bit/use)');ax.grid(True,ls=':',alpha=.45)
        if symlog:ax.set_yscale('symlog',base=10,linthresh=1e-3)
        return fig,ax
    def save(fig,name,description):
        fig.text(.5,.012,'Untrusted homodyne; numerical model, hardware unvalidated',ha='center',fontsize=6.6)
        fig.tight_layout(rect=[0,.045,1,1]);pdf=figures/(name+'.pdf');png=figures/(name+'.png')
        fig.savefig(pdf);fig.savefig(png,dpi=350)
        with Image.open(png) as im:
            assert min(im.size)>1000 and min(im.info['dpi'])>=349
            pdf_bytes=pdf.read_bytes();pages=len(re.findall(rb'/Type /Page\b',pdf_bytes))
            assert pdf_bytes.startswith(b'%PDF-') and pdf_bytes.rstrip().endswith(b'%%EOF') and pages==1
            figure_checks.append(dict(name=name,description=description,pixels=list(im.size),dpi=list(im.info['dpi']),pages=pages))
        plt.close(fig)
    def baseline(ax,x):ax.scatter([x],[base['K_raw']],marker='*',s=90,color='black',label='Original baseline',zorder=7)
    fig,ax=start('Full-angle divergence (µrad)')
    for data,label,style in [(sorted([r for r in A if r['changed_parameter']=='divergence'],key=lambda r:r['tested_value']),'Original pointing','o-'),
                              (sorted([r for r in physical if r['D_r']==.08 and r['jitter_urad']==1.561 and r['sigma_h_m']==.1],key=lambda r:r['divergence_urad']),'1.561 µrad / 0.1 m','s-')]:
        ax.plot([r['divergence_urad'] for r in data],[r['K_raw'] for r in data],style,ms=3,label=label)
    baseline(ax,233);ax.set_title('8 cm receiver; fixed historical MB source',fontsize=10)
    ax.text(.04,.84,'Recommended receivers ≥40.1 cm: outside this panel',transform=ax.transAxes,fontsize=7)
    ax.legend(frameon=False,loc='best');save(fig,'fig_1_divergence_8cm','Both curves fixed MB(.165,5.475); no selected larger-Rx point projected onto 8cm')
    fig,ax=start('Receiver diameter (cm)',True)
    original=sorted([r for r in A if r['changed_parameter']=='receiver'],key=lambda r:r['D_r'])
    ax.plot([100*r['D_r'] for r in original],[r['K_raw'] for r in original],'o-',ms=3,label='Original pointing / fixed MB')
    points=[]
    for diameter in s.DR:
        eligible=[r for r in allrows if r['D_r']==diameter and r['stage'] in ('stage_B','stage_C') or r['D_r']==diameter and r['stage'].startswith('source_receiver_')]
        if eligible:points.append(max(eligible,key=lambda r:r['K_raw']))
    ax.scatter([100*r['D_r'] for r in points],[r['K_raw'] for r in points],s=20,marker='x',color='gray',label='Best staged point (source/pointing vary)')
    for r,color,marker in zip(final,colors,markers):ax.scatter(100*r['D_r'],r['K_raw'],s=45,c=color,marker=marker,label=names[r['recommendation']],zorder=8)
    baseline(ax,8);ax.legend(frameon=False,fontsize=6.7);save(fig,'fig_2_receiver_diameter','Raw signed points; no smoothed optimum envelope')
    for name,xkey,xlabel,number in [('angular_jitter','jitter_urad','Angular pointing jitter (µrad)',3),('position','sigma_h_m','Horizontal residual SD (m)',4)]:
        fig,ax=start(xlabel,True)
        stage='angular_jitter' if name=='angular_jitter' else 'position'
        data=sorted([r for r in A if r['changed_parameter']==stage],key=lambda r:r[xkey])
        ax.plot([r[xkey] for r in data],[r['K_raw'] for r in data],'ko--',ms=2.5,label='Original optics / fixed MB')
        for r,color,marker in zip(final,colors,markers):
            data=sorted([x for x in curves if x['figure']==name and x['recommendation']==r['recommendation']],key=lambda r:r[xkey])
            ax.plot([x[xkey] for x in data],[x['K_raw'] for x in data],color=color,marker=marker,ms=3,label=names[r['recommendation']])
            ax.scatter(r[xkey],r['K_raw'],s=80,marker='*',color=color,zorder=8)
        baseline(ax,base[xkey]);ax.legend(frameon=False,fontsize=6.6)
        save(fig,f'fig_{number}_{name}','Other physical variables and each curve source remain fixed; stars are nominal recommendations')
    # Cell colors use evaluated fixed-source nodes only; absent cells are hatched.
    diameters=s.DR;divergences=sorted(s.DIV);matrix=np.full((len(diameters),len(divergences)),np.nan)
    for r in physical:
        if r['jitter_urad']==3 and r['sigma_h_m']==.1:matrix[diameters.index(r['D_r']),divergences.index(r['divergence_urad'])]=r['K_raw']
    fig,ax=plt.subplots(figsize=(5.2,3.9));norm=SymLogNorm(linthresh=1e-3,vmin=float(np.nanmin(matrix)),vmax=float(np.nanmax(matrix)),base=10)
    mesh=ax.pcolormesh(np.arange(len(divergences)+1)-.5,np.arange(len(diameters)+1)-.5,np.ma.masked_invalid(matrix),cmap='coolwarm',norm=norm,edgecolors='white',linewidth=.3)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isnan(matrix[i,j]):ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,hatch='///',edgecolor='gray',lw=0))
            elif matrix[i,j]>0:ax.add_patch(Rectangle((j-.49,i-.49),.98,.98,fill=False,edgecolor='black',lw=1.2))
    for r,label in [(final[1],'2'),(final[2],'3')]:
        ax.scatter(divergences.index(r['divergence_urad']),diameters.index(r['D_r']),marker='*',s=100,color='yellow',edgecolor='black')
        ax.annotate(label,(divergences.index(r['divergence_urad']),diameters.index(r['D_r'])),xytext=(6,5),textcoords='offset points',fontsize=8)
    ax.set_xticks(range(len(divergences)),[f'{v:g}' for v in divergences]);ax.set_yticks(range(len(diameters)),[f'{100*d:g}' for d in diameters])
    ax.set_xlabel('Full-angle divergence (µrad)');ax.set_ylabel('Receiver diameter (cm)')
    ax.set_title('3 µrad / 0.1 m; fixed MB(.165, 5.475)',fontsize=10,pad=24)
    ax.text(.01,1.01,'Outline: K>0; hatch: untested; stars: design locations',transform=ax.transAxes,fontsize=7)
    cb=fig.colorbar(mesh,ax=ax,label='Raw SKR (bit/use)',ticks=[-.1,-.01,-.001,0,.001,.01]);cb.solids.set_rasterized(False)
    save(fig,'fig_5_heatmap','Cell outlines show evaluated positivity, not an interpolated K=0 contour; baseline and design1 have different pointing')
    # Best observed per compact Rx/divergence is a projection of sampled nodes, not a complete search.
    compact=s.DR[:7];matrix=np.full((len(divergences),len(compact)),np.nan)
    for i,d in enumerate(compact):
        for j,v in enumerate(divergences):
            eligible=[r['K_raw'] for r in allrows if r['D_r']==d and r['divergence_urad']==v]
            if eligible:matrix[j,i]=max(eligible)
    assert np.nanmax(matrix)<0
    fig,ax=plt.subplots(figsize=(5.0,3.8))
    mesh=ax.pcolormesh(np.arange(len(compact)+1)-.5,np.arange(len(divergences)+1)-.5,matrix,cmap='Blues_r',norm=SymLogNorm(linthresh=.005,vmin=float(np.nanmin(matrix)),vmax=0,base=10),edgecolors='white',linewidth=.35)
    ax.set_xticks(range(len(compact)),[f'{100*d:g}' for d in compact]);ax.set_yticks(range(len(divergences)),[f'{v:g}' for v in divergences])
    ax.set_xlabel('Receiver diameter (cm)');ax.set_ylabel('Full-angle divergence (µrad)')
    ax.scatter(0,divergences.index(233.),marker='*',s=100,c='black',label='Original baseline location')
    ax.set_title('Compact/intermediate optics: all sampled rates <0',fontsize=10)
    ax.text(.02,.03,'No K=0 contour in sampled 8–30 cm region.\nRecommendations ≥40.1 cm lie outside this panel.',transform=ax.transAxes,fontsize=7,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
    ax.legend(frameon=False,fontsize=6.6,loc='upper right');cb=fig.colorbar(mesh,ax=ax,label='Best sampled raw SKR (bit/use)');cb.solids.set_rasterized(False)
    save(fig,'fig_6_compact_feasibility','Best sampled rates over staged pointing/source nodes; not a no-key theorem or untested-cell fill')
    pareto=rows('final_pareto.csv')
    fig,ax=plt.subplots(figsize=(5.1,3.9))
    mesh=ax.scatter([100*r['D_r'] for r in pareto],[100*r['transmitter_diameter_99percent_m'] for r in pareto],
        c=[r['K_raw'] for r in pareto],s=17,cmap='viridis',norm=LogNorm(vmin=1e-4,vmax=max(r['K_raw'] for r in pareto)),alpha=.65,label='Sampled Pareto nodes (K>0)')
    for r,color,marker in zip(final,colors,markers):
        ax.scatter(100*r['D_r'],100*r['transmitter_diameter_99percent_m'],s=65,marker=marker,color=color,edgecolor='black',lw=.5,label=names[r['recommendation']],zorder=8)
    ax.scatter(8,100*base['transmitter_diameter_99percent_m'],marker='*',s=80,c='black',label='Original (K<0)')
    ax.set_xlabel('UAV receiver diameter (cm)');ax.set_ylabel('Ideal transmitter $D_{tx,99}$ (cm)');ax.grid(True,ls=':',alpha=.4)
    ax.legend(frameon=False,fontsize=6.5,loc='upper left');cb=fig.colorbar(mesh,ax=ax,label='Raw SKR (bit/use)');cb.solids.set_rasterized(False)
    save(fig,'fig_7_pareto','Five Pareto dimensions include angular/position tolerance and rate; 2D projection does not establish hardware feasibility')
    s.save('figure_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',figures=figure_checks,smoothing=False,source_interpolation=False,one_plot_per_figure=True,missing_cells='HATCHED_OR_EXPLICITLY_ABSENT'))
    # Engineering table and physical receipt keep inferred quantities distinct from measured specs.
    C=[];engineering=[]
    for r in final:
        label=r['recommendation'];minimum=min(x['K_raw'] for x in robust if x['recommendation']==label)
        C.append(dict(configuration=vietnamese[label],D_r_cm=100*r['D_r'],divergence_urad=r['divergence_urad'],jitter_urad=r['jitter_urad'],sigma_h_m=r['sigma_h_m'],
            receiver_enlargement=r['D_r']/.08,collimation_improvement=233/r['divergence_urad'],angular_stability_improvement=15.61/r['jitter_urad'],horizontal_stability_improvement=1/r['sigma_h_m'],
            D_tx_99_cm=100*r['transmitter_diameter_99percent_m'],K_raw=r['K_raw'],worst_20percent_K=minimum,
            receiver_class='LARGE_ABOVE_30CM_SWAP_UNVERIFIED',tradeoff='Local onset; not pointing-robust' if label=='minimal' else 'Survives sampled joint20percent degradation' if label=='balanced' else 'Higher collection with larger Tx; pointing-sensitive'))
        engineering.append(dict(recommendation=label,**{k:r[k] for k in ['D_r','divergence_urad','w0_m','wL_m','w_eff_m','G_d','eta_atm','P0','m1','eta_f','sigma_s_m','angular_displacement_m','sigma_h_over_w_eff','angular_displacement_over_w_eff']},
            transmitted_fraction_within_Dtx99=.99,D_tx_99_m=r['transmitter_diameter_99percent_m'],D_tx_9999_m=math.sqrt(2)*r['transmitter_diameter_99percent_m'],
            received_mean_fraction_before_detector=r['m1'],received_mean_fraction_after_detector=.8*r['m1'],
            aperture_pupil_diffraction_and_coupling_calibrated=False,absolute_power_watt='NOT_SPECIFIED'))
    s.write('table_C_minimum_improvement.csv',C);s.write('physical_channel_receipt.csv',engineering)
    s.write('table_B_positive_candidates.csv',[{**r,'D_r_cm':100*r['D_r'],'D_tx_99_cm':100*r['transmitter_diameter_99percent_m'],
        'feasibility':'LARGE_RECEIVER_SWAP_NOT_VERIFIED; NUMERICAL_POSITIVE_ONLY'} for r in final])
    matched=[];adaptation=[]
    for r in final:
        par=s.parameters(r);local=[x for x in allrows if s.parameters(x)==par]
        common={x['VA'] for x in local if x['family']=='Uniform'}&{x['VA'] for x in local if x['family']=='MB'}
        va=min(common,key=lambda value:abs(value-r['VA']))
        uni=max((x for x in local if x['family']=='Uniform' and x['VA']==va),key=lambda x:x['K_raw'])
        mb=max((x for x in local if x['family']=='MB' and x['VA']==va),key=lambda x:x['K_raw'])
        matched.append(dict(recommendation=r['recommendation'],VA=va,Uniform_K=uni['K_raw'],MB_K=mb['K_raw'],
            delta_K_same_energy=mb['K_raw']-uni['K_raw'],nu_raw=mb['nu_raw'],Uniform_hash=uni['ensemble_hash'],MB_hash=mb['ensemble_hash']))
        group=[x for x in comparisons if x['recommendation']==r['recommendation'] and x['comparison']=='family_energy_optimized_or_historical_fixed']
        best=next(x for x in group if x['family']=='MB');fixed=next(x for x in group if x['family']=='Fixed MB')
        adaptation.append([vietnamese[r['recommendation']],fixed['K_raw'],best['K_raw'],best['K_raw']-fixed['K_raw']])
    s.write('same_energy_shaping_comparison.csv',matched)
    tx=[]
    for v in s.DIV:
        c,_=s.n.optical(.08,v,15.61,1.)
        tx.append(dict(divergence_full_urad=v,w0_m=c['w0_m'],D_tx_99_cm=100*c['transmitter_diameter_99percent_m'],D_tx_9999_cm=100*math.sqrt(2)*c['transmitter_diameter_99percent_m'],wL_m=c['wL_m'],w_eff_m=c['w_eff_m'],G_d=c['G_d']))
    s.write('transmitter_apertures.csv',tx)
    sensitivity=[]
    for kind in ['divergence','receiver','angular_jitter','position']:
        r=max((x for x in A if x['changed_parameter']==kind),key=lambda x:x['K_raw'])
        sensitivity.append([kind,r['tested_value'],r['K_raw'],r['delta_K']])
    compact_best=[]
    for d in s.DR[:8]:
        eligible=[r for r in allrows if r['D_r']==d]
        r=max(eligible,key=lambda x:x['K_raw'])
        compact_best.append([100*d,r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['VA'],r['nu_raw'],r['K_raw']])
    root0=next(r for r in roots if r['branch']=='near_40cm' and r['target_K']==0)
    root1=next(r for r in roots if r['branch']=='near_40cm' and r['target_K']==1e-4)
    summary=table(['Cấu hình','Rx (cm)','Divergence (µrad)','Jitter (µrad)','σh (m)','Tx99 (cm)','VA','νraw','K (bit/use)'],
        [[vietnamese[r['recommendation']],100*r['D_r'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],100*r['transmitter_diameter_99percent_m'],r['VA'],r['nu_raw'],r['K_raw']] for r in final])
    text=f'''# Thay đổi vật lý tối thiểu để SKR dương — 2026-10-22

Đã chạy tìm kiếm theo giai đoạn với detector untrusted gốc. **Chưa tìm được SKR dương ở receiver 8–30 cm trong các điểm đã thử.** Receiver 40 cm tiến sát ngưỡng nhưng còn âm; tinh chỉnh nhánh này cho điểm báo cáo **40.1 cm**, K={final[0]['K_raw']:.10g} bit/use. Đây là điểm gần onset, không bền trước suy giảm pointing. Cấu hình cân bằng **55 cm / 35 µrad / 3 µrad / 0.1 m** có dự trữ tốt hơn. Tất cả receiver được chọn đều thuộc lớp lớn trên30cm; khả năng mang trên UAV chưa được xác minh. Không có kết luận rằng đây là thiết kế đã đủ điều kiện sinh khóa an toàn.

{summary}
Các tốc độ là raw K có dấu, theo mỗi lần truyền, gồm outage. Dùng MI của likelihood fading thực, không dùng Gaussian surrogate làm kết quả chính. Nhãn chung: BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY, security_valid=false, hardware_validated=false. Đường kính40.1cm là điểm làm tròn lên theo bước1mm trên nhánh cục bộ đã tìm nghiệm, không là cực tiểu toàn cục hay dung sai chế tạo1mm.

## Cấu hình gốc và nơi lấy giá trị parameter

Nguồn baseline manuscript: configs/manuscript_mobility.json và src/manuscript_mobility.py, đã được dùng bởi hai nghiên cứu trước. D_r=.08m; divergence full233µrad; jitter góc mỗi trục15.61µrad; sigma_h=1m; HAP20km/UAV1km; zenith30°; L={base['L_km']:.15g}km; lambda1550nm. AoA SD1.5mrad, FOV half6.25mrad, tau_zen=.92; eta_atm30°={base['eta_atm']:.15g}; P0={base['P0']:.15g}. Channel excess.0186, detector eta.8/excess output.0135, beta.95, homodyne1D, AO OFF và phase OFF theo giả thiết lịch sử. Nguồn cố định StageA–D là MB(nu_raw=.165,VA=5.475), hash {base['ensemble_hash']}.

configs/channel.yaml và configs/default.yaml hiện chứa **223µrad ở theta_div_rad**, không phải angular jitter; theta_jt_rad vẫn15.61e-6. Hai config active có tau_zen=null và mapping phase chưa giải quyết, nên không tự chạy production evaluator. Diagnostic này kế thừa scenario manuscript có provenance và không thay config active. Điểm223µrad được lưu riêng trong BảngA, không đổi baseline233µrad.

Baseline trên mô hình bounded mới: m1={base['m1']:.15g}, Tf={base['eta_f']:.15g}, I_AB={base['I_AB']:.15g}, betaI={base['beta_I_AB']:.15g}, chi_BE={base['chi_BE']:.15g}, K={base['K_raw']:.15g}. Regression historical trial riêng vẫn K=-.0587243146799775588; sự khác biệt đến từ mô hình quang học đã đổi ở nghiên cứu trước, không phải thay detector.

## Công thức và phương pháp số đã dùng

Với theta_div là **full angle**, w0=2lambda/(pi theta_div), wL=w0 sqrt[1+(Llambda/(pi w0²))²], w_eff=wL sqrt(1+Gd). Dtx99=2w0 sqrt(ln100/2). Tất cả giá trị nằm ở transmitter_apertures.csv; không coi giảm divergence là miễn phí. Beam tròn Gaussian ngẫu nhiên độ rộng w=w_eff exp(-S/2), S~N(-v/2,v), v={base['v']:.15g}. Sai lệch tâm Rayleigh có SD mỗi trục sigma_s=sqrt[sigma_h²+(L theta_jt)²]. Mỗi beam tích phân toàn mặt phẳng bằng1; công suất thu tròn dùng CDF noncentral-chi-square chính xác: H(r,w)=F_chi2prime(df2,noncentrality4r²/w²)(D_r²/w²). Trên active T=eta_atm H, cộng atomP0 tạiT=0. H thuộc[0,1], T thuộc[0,eta_atm]; giữ atom riêng, không clip hay normalize một tail phi vật lý.

m1=E[T], mh=E[sqrt(T)], Tf=mh². Noise trước detector:
N_fading=(m1-Tf)VA; N_channel=.0186m1; N_detector=.0135/.8=.016875.
N_post=.8(N_fading+N_channel)+.0135; a=1+VA, b=1+.8TfVA+N_post.
Interval discrete-modulation dùng center=2sqrt(.8)mh C, radius=sqrt(2N_post w); chi_BE được numerical maximize trên toàn giao interval với miền covariance vật lý. Eigenvalue homodyne điều kiện là nu3=sqrt[a(a-z²/b)]. Các quy ước detector/C,w/fading đã chốt được giữ nguyên; không mở lại nghiên cứu security.

MI chính tính likelihood pooled: p(y|x)=E_T Normal(y;2sqrt(.8T)x,1+.8*.0186T+.0135); I=Σpx ∫p(y|x)log2[p(y|x)/p(y)]dy. Fading nằm trong mixture, không cộng N_fading lần nữa vào phương sai từngT. Không CSI conditioning hoặc postselection. K=.95I-chi_BE. numeric.py chỉ tăng tốc cùng likelihood qua characteristic-function/Fourier inversion; được đối chiếu trực tiếp với pooled_mi cũ tại cùng node, không thay mô hình. K_surrogate và I_AB_surrogate được giữ riêng trong mọi dòng.

Stages: one-parameter scans nguồn cố định;8cm trước rồi10/12/15/20/25/30/40/55cm; các tier(jitterµrad,sigma_m)=(15.61,1),(12,.75),(10,.5),(7.5,.3),(5,.2),(3,.2),(3,.1),(1.561,.1). Mỗi tier xét10 divergence đã yêu cầu; dừng tăng yêu cầu pointing khi nguồn cố định dương ở một receiver. Các điểm diameter lớn ở StageA là sensitivity độc lập, không được dùng để nhảy qua compact search. StageE xét233 nguồn exact(197MB,36Uniform) trên các context đã chọn; C,w/PMF/energy/hash xác thực, không tạo AP hay nội suy. Chọn context theo moment-quality chỉ là heuristic sàng lọc, không là objectiveSKR hoặc chứng nhận phủ toàn miền. Targeted alternating dùng4 starts, P1 tìmVA trên cùngnu, P2 tìmnu trên cùngVA trong catalog, dừng deltaK<1e-8 hoặc catalog fixed point. Thiếu nguồn cùngVA được đánh dấu MISSING_EXACT_SOURCE_NO_INTERPOLATION.

Screen dùng quadrature128x16; các ứng viên chọn dùng256x32/512x48, tăng1024x64 nếu cần. Dừng khi thay đổiMI giữa hai mức<2e-6 và K lớn hơn hai lần ảnh hưởng quan sát lênK. Đây là quan sát hội tụ, không là error bound nghiêm ngặt. Full-Z33/129, entropy110digits, Fourier half-output-spacing và density-mass checks có receipt. FFT chỉ sửa density âm do roundoff trong budget tích phân1e-12, ghi rõ từng dòng; không sửa transmittance. RegressionA/B khớp sai số cỡ1e-15. Chi numerical không có rigorous global enclosure; giữ giới hạn security trước đó.

## Q1. Tham số gốc nào cản trở SKR dương?

Tín hiệu thu quá yếu so với noise detector untrusted cố định. Baseline N_detector/N_channel={base['N_detector']/base['N_channel']:.10g}; sigma_h=1m lớn hơn dịch góc Ltheta_jt={base['angular_displacement_m']:.9g}m. Trong sensitivity nguồn cố định, giảm sigma_h giúp tăngK nhiều nhất; riêng giảm divergence hoặc tăngRx không đủ và có thể làm raw bound xấu hơn do fading trong nguồnVA cao.

{table(['Tham số','Giá trị cho K lớn nhất','K','DeltaK so baseline'],sensitivity)}
Không một thay đổi độc lập trong danh sách làm K dương. Các delta cỡ1e-9 của điểm baseline là khác quadrature128x16 so với baseline512x48, không là hiệu quả vật lý.

## Q2. Receiver có giữ8cm được không?

Chưa có điểm dương trong80 context cố định8cm và context được xét233nguồn. Không được suy ra bất khả thi mọi nguồn/mọi beam/PAT. Figure1 giữ8cm, fixedMB; Figure6 hiển thị best sampled ở8–30cm. Không có đườngK=0 trong vùng compact đã thử; không vẽ contour giả hoặc điền node chưa tính.

{table(['Rx(cm)','Divergence','Jitter','σh','VA','νraw','K lớn nhất đã thử ở đúngRx'],compact_best)}

## Q3. Nếu giữ8cm thì thay đổi tối thiểu là gì?

Chưa tìm thấy tổ hợp đủ, nên không có maximum admissible divergence, required angular/position threshold hoặc robustness của một thiết kế8cm dương để báo cáo. Ngay cả tiers mạnh nhất trong danh sách vẫn chưa tạo dương ở các điểm đã thử. Dtx99 ở10µrad gần30cm không tự giải quyết thiếu thu quang; beam hẹp tăng nhạy lệch tâm. Không gán một ngưỡng từ thiết kế55/75cm cho8cm.

## Q4. Nếu tăngRx, kích thước nhỏ nhất đã tìm được?

Trong danh sách rời rạc,40cm âm và55cm có dương. Tại40cm, source-catalog best ở25µrad choK=-.000216000397480931; tối ưu divergence cục bộ giữ nguồn cho theta={final[0]['divergence_urad']:.12g}µrad vẫn K=-.0002158387266592565. Nghiệm tăngRx trên nhánh này: K=0 tạiD={root0['root']:.12g}m; K=1e-4 tạiD={root1['root']:.12g}m. Chọn điểm làm tròn lênD={final[0]['D_r']:.6g}m, rồi kiểm tra lại toàn catalog và MI mịn. Cấu hình1 là ứng viên giảm khẩu độ thu trên nhánh này; đòi hỏi PAT tốt, không tối thiểu đồng thời mọi chiều kỹ thuật.

Toàn bộ26 root giữ đúng một nguồn exact và các tham số khác cố định, nằm ở refined_boundary_roots.csv; không phải ngưỡng toàn cục sau tối ưu liên tục. Mỗi trong4 biến của3 ứng viên có sign-change về baseline tại cả2 mục tiêu; thêm2 root của nhánh40cm. Không suy ra root ở các context chưa có bracket. Mốc1e-4 chỉ là engineering comparison target, không là định nghĩa security.

## Q5. Kết hợp divergence/pointing nào cân bằng nhất trong shortlist?

Cấu hình2 dùngRx55cm, full35µrad, jitter3µrad, sigma_h.1m. Nguồn được chọn trong catalog với ràng buộc đồng thời jitter3.6µrad/sigma_h.12m vẫn K>=1e-4, rồi kiểm tra đủ25 tổ hợp±10/20%. Đây là guard robustness trong shortlist, không là nghiệm cost/global tối ưu. Cấu hình1 gần onset và cấu hình3 dùng beam hẹp hơn có thể mất dương khi pointing xấu đi; xem bảng dưới.

{table(['Cấu hình','K nominal','K thấp nhất trong25 perturbations','K fine ở worst case'],[[vietnamese[r['recommendation']],r['K_raw'],min(x['K_raw'] for x in robust if x['recommendation']==r['recommendation']),next(x['K_raw'] for x in rows('worst_robustness_fine.csv') if x['recommendation']==r['recommendation'])] for r in final])}
Pareto dùng năm chiều: giảmRx, tăng divergence (giảmTx), tăng tolerated angular jitter, tăng tolerated sigma_h, tăngK. Chỉ các điểm đã tính; projection2D không giữ đầy đủ thứ tự dominance. Danh sách final_pareto.csv và figure7 không chứng nhận optimal frontier liên tục. Điểm regression75cm/10µrad được giữ như upper comparison, không chọn làm thiết kế mặc định.

Nguồn cân bằng có guard robustness có thể hy sinh nominalK so với nguồn đứng trên nominal Pareto frontier ở cùng phần cứng. Robustness là tiêu chí bổ sung; không gọi nguồn robust là nominal optimum.

## Q6. Kích thướcTx/Rx và yêu cầu vật lý có hợp lý không?

{table(['Cấu hình','w0(m)','wL(m)','w_eff(m)','Ltheta_jt(m)','σh/w_eff','Ltheta_jt/w_eff','Dtx99(cm)'],[[vietnamese[r['recommendation']],r['w0_m'],r['wL_m'],r['w_eff_m'],r['angular_displacement_m'],r['sigma_h_over_w_eff'],r['angular_displacement_over_w_eff'],100*r['transmitter_diameter_99percent_m']] for r in final])}
Các kích thướcTx là yêu cầu encircled-power của Gaussian lý tưởng, không là pupil đã thiết kế. Dtx99 chứa99% Gaussian không chặn;99.99% cần đường kínhsqrt2 lầnDtx99. Mô hình primary chưa đưa hard-pupil diffraction, M² thực, throughput, coupling single-mode, mounting, obscuration và wavefront residual vào. Không đồng nhất cắt1% công suất với cùng Gaussian propagation; không xác nhận khẩu độ tối thiểu phần cứng. Điểm gần onset đặc biệt dễ mất margin do loss/coupling chưa mô hình hóa.

Rx40.1/55cm đều thuộc nhómlarge>30cm, cần platformSWaP riêng: khối lượng quang học/gimbal, tải và mômen lên UAV, mount/cách ly rung, băng thông tracking và receiverattitude. Không có sốmass/power/vibration đo được nên không tuyên bố phù hợp UAV thông thường. 8–15cm là compact;15–30cm intermediate chỉ là phân lớp tìm kiếm exploratory, không phải giới hạn chứng nhận. Chưa tìm được khuyến nghị positive đủ căn cứ cho compactUAV.

Cơ chế có cơ sở để hạ residual: coarse gimbal kết hợp beacon sensor và fine steering mirror; GPS dùng acquisition/coarse, không phải measurement trực tiếp của beam-centering residual. [Carrasco-Casado et al., UAV laser terminal](https://arxiv.org/abs/1506.08854) mô tả GPS-aided gimbal, fine mirror và beacon tracking; [NASA CLICK](https://www.nasa.gov/smallspacecraft/what-is-click/) dùng fine steering mirror cho precisionpointing. Đây là dẫn chứng kiến trúc, không chứng minh jitter1.561/3µrad hoặcsigma.1m đạt được ở liên kết này.

theta_jt là residual transmitter pointing mỗi trục; sigma_h phải được hiểu/đo là residual tương đối độc lập sau coarse/beam steering, không cộng lại cùng một chuyển động đã nằm trongtheta_jt. Receiver attitude/AoA1.5mrad được giữ riêng trongP0/FOV, không dùng cải thiệntheta_jt để xóaoutage. Nếu các residual tương quan, quy tắc cộng variance đang dùng cần hiệu chuẩn lại. Giữ turbulence/HV và atmosphere không đổi. Không tối ưu FOV vì chưa có background noise trade-off; không gán gainAO/coupling hoặc giảm noise tùy ý.

## Q7. MB shaping bổ sung bao nhiêu sau cải thiện quang học?

{table(['Cấu hình','So sánh','Family','VA','νraw','K'],[[vietnamese[r['recommendation']],r['comparison'],r['family'],r['VA'],r.get('nu_raw','—'),r.get('K_raw',r.get('status',''))] for r in comparisons])}
Family-energy-optimized so sánh chọnVA khác nhau, nên chênh lệch không được gọi toàn bộ là shaping gain. Dòngsame_VA chỉ dùng nguồn exact có cùngVA; thiếu thì flag. FixedMB(.165,5.475) tách riêng để thấy ích lợi sourceadaptation sau cải thiện kênh. Best nominalMB có thể khác nguồn robust-balanced; không gọi guard robustness là maximizernominal. Catalog gốc sau tối ưu nguồn vẫn K={selection['original_catalog_best']['K_raw']:.12g}; source optimization không tự cứu kênh gốc. Báo cáo chỉ best exact tested, không global/continuous optimum.

{table(['Cấu hình','K fixedMB','K best nominalMB','Gain do chọn cảVA vàν'],adaptation)}

Để tách riêng hiệu ứng shaping ở cùng năng lượng, dùng VA chung gần nhất có đủ hai nguồn exact trong catalog (không thayVA của ba khuyến nghị):

{table(['Cấu hình','VA chung','K Uniform','K MB','DeltaK cùngVA','νMB'],[[vietnamese[r['recommendation']],r['VA'],r['Uniform_K'],r['MB_K'],r['delta_K_same_energy'],r['nu_raw']] for r in matched])}
File same_energy_shaping_comparison.csv giữ hash riêng của hai nguồn. MB ở đây là best exact tested trên cácν có sẵn tại đúngVA đó.

## Q8. Đề xuất đưa gì vào manuscript?

Đưa cấu hình2 làm **kịch bản sensitivity có margin** của mô hình bounded đã khai báo; chỉ gọi là khuyến nghị nghiên cứu, chờ đo/certify optics/PAT/platform và các điều kiện security còn thiếu. Cấu hình1 dùng minh họa onset/giảmRx, không gọi robust. Cấu hình3 minh họa đánh đổi transmitter lớn hơn và nhạy pointing để tăng nominalK. Không thay manuscriptbaseline hoặc tuyên bố UAV phổ thông mang được55cm; giữ baselineâm và kết quảcompactâm trong bài. BenchmarkA75cm/10µrad vàB55cm/25µrad của nghiên cứu trước chỉ là regression/comparison, không tự trở thành thiết kế mặc định.

{table(['Cấu hình','Rx tăng(lần)','Collimation tăng(lần)','Angular stability tăng(lần)','Horizontal stability tăng(lần)','K','Trade-off'],[[r['configuration'],r['receiver_enlargement'],r['collimation_improvement'],r['angular_stability_improvement'],r['horizontal_stability_improvement'],r['K_raw'],r['tradeoff']] for r in C])}

### Phân rã đầy đủ ba cấu hình

{table(['Cấu hình','m1','Tf','I_AB','betaI_AB','chi_BE','K'],[[vietnamese[r['recommendation']],r['m1'],r['eta_f'],r['I_AB'],r['beta_I_AB'],r['chi_BE'],r['K_raw']] for r in final])}
{table(['Cấu hình','N_fading','N_channel','N_detector','N_post','AoA outage'],[[vietnamese[r['recommendation']],r['N_fading'],r['N_channel'],r['N_detector'],r['N_post'],r['P0']] for r in final])}

### Hồ sơ, phạm vi và tái kiểm tra

TableA: table_A_baseline_sensitivity.csv (đủmoment/noise/I/chi/K/delta); TableB: table_B_positive_candidates.csv; TableC: table_C_minimum_improvement.csv. transmitter_apertures.csv và physical_channel_receipt.csv tách yêu cầu hình học/received fractions khỏi hardware chưa đo. final_selection.json, final_source_comparisons.csv, alternating_*.csv, final_robustness.csv, refined_boundary_roots.csv, all_evaluations.csv và evaluations.jsonl giữ đúng các node/evaluator/sourcehash. selection.json giữ shortlist tự động ban đầu; **final_selection.json mới là ba cấu hình cuối sau tinh chỉnh40cm và robustness**.

Bảy hình nằm trong figures/, mỗi hình vectorPDF và350dpiPNG. Dữ liệu figure3/4 nằm ở figure_sensitivity_data.csv; heatmap dùng node cố định, hatch là chưa thử, outline là node dương, không nội suy tạo tối ưu. Các điểm trên đường chỉ nối để đọc xu hướng. SOURCE/physical searches không phủ toànCartesian; thiếu node không chứng minh âm.

checks.json/figure_validation.json/final_convergence.json và final_receipt.json chứa kết quả kiểm tra, hashproducer/input/artifact và preservation manifest. Chạy verify.py để xác minh chỉ từ artifact đã lưu; không chạy lại tìm kiếm. Numeric search nằm ở search.py/refine.py, isolatednumeric.py; không sửa historicalmodel/source/security/config/cache/spec. GitHEAD và dirty work trước task được chụp trongstartup_manifest.json.

Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS, UNVALIDATED_SECURITY_MODEL; discrepancy historicalfrozenhash đã ghi trước và ObjectiveC USER_STOPPED vẫn giữ. Không có training/finaltest/heldout/newAP, productionbaseline selection hoặc thresholdcertification. Không thử finitekey/experimentalhardware; các kết quả dương vẫn là numericaldiagnostic của kênh surrogate chưa đo.
'''
    (s.OUT/'report_vi.md').write_text(text,encoding='utf-8')
    (s.OUT/'executive_conclusion_vi.md').write_text('Không có điểm SKR dương ở Rx8–30cm trong miền đã thử.\n\n'+summary+'\nCấu hình2 là kịch bản có dự trữ pointing tốt nhất trong shortlist; Rx40.1/55cm vẫn cần chứng minh SWaP. Các tốc độ là numerical diagnostic; chưa xác nhận hardware/security.\n',encoding='utf-8')
    coverage=[]
    for diameter in s.DR:
        tested={s.parameters(r) for r in physical if r['D_r']==diameter}
        source_contexts={s.parameters(r) for r in allrows if r['D_r']==diameter and r['stage'].startswith('source_')}
        coverage.append(dict(D_r_m=diameter,staged_fixed_source_contexts=len(tested),full_requested_3D_menu=420,
            untested_fixed_source_menu_contexts=420-len(tested),contexts_with_catalog_rows=len(source_contexts),
            scope='STAGED_NOT_CARTESIAN; zero cells do not certify infeasibility'))
    s.write('search_coverage.csv',coverage)
    s.save('protocol.json',dict(primary_baseline=base,source_catalog=233,source_fixed_through_physical_stages=dict(nu_raw=.165,VA=5.475),divergence_full_urad=s.DIV,receiver_menu_m=s.DR,angular_jitter_urad=s.JT,horizontal_SD_m=s.SIG,
        tiers=s.TIERS,screen_quadrature=[128,16],selected_convergence_MI=2e-6,engineering_K_target=1e-4,source_coordinate_stop_deltaK=1e-8,
        primary_MI='ACTUAL_POOLED_FADING_LIKELIHOOD',physical_model='PREVIOUS_PASSIVE_RANDOM_WIDTH_EXACT_CIRCULAR_COLLECTION',
        regression_only=['prior_A_.75m_10urad','prior_B_.55m_25urad'],missing_cells='NOT_EVALUATED',roots='FIXED_SOURCE_LOCAL_NO_GLOBAL_CERTIFICATE',
        security_valid=False,hardware_validated=False,publication_training_final_test='NOT_RUN'))
    print('REPORT AND SEVEN FIGURES COMPLETE',flush=True)


if __name__=='__main__':main()
