"""Render saved parameter-only results; never calls a scientific evaluator."""
import csv
import json
import math
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUT=Path(__file__).resolve().parent


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:result=list(csv.DictReader(f))
    for r in result:
        for k,v in r.items():
            try:r[k]=float(v)
            except (TypeError,ValueError):pass
    return result
def write(name,data):
    fields=list(dict.fromkeys(k for r in data for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
def fmt(v):return f'{v:.12g}' if isinstance(v,(float,int,np.number)) else str(v)
def table(headers,data):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(fmt,r))+' |\n' for r in data)+'\n'


def main():
    if (OUT/'final_receipt.json').exists():raise FileExistsError('Preserve sealed package')
    selection=read('selection.json');selected=selection['recommendations'];best=selection['detector_scenario_best']
    baseline=read('baseline_regression.json')['result'];validation=read('validation.json');opt=read('optimization.json')
    A=rows('stage_A_detector_only.csv');B=rows('stage_B_transmitter.csv');physical=rows('stage_D_staged_physical.csv')
    curves=rows('selected_sensitivity.csv');robust=rows('robustness.csv');comparison=rows('source_comparison.csv')
    names=['A — Giữ thông số detector gốc','B — Tham chiếu cân bằng','C — K lớn nhất đã thử']
    positive=selection['nominal_positive_count'];maxr=max(best,key=lambda r:r['K_raw'])
    fields=['D_r','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','L_km','eta_det','epsilon_det','VA','nu_raw','I_AB','beta_I_AB','chi_BE','K_raw']
    summary=[{'configuration':r['configuration'],**{k:r[k] for k in fields},'remaining_gap':r['chi_BE']-r['beta_I_AB'],
        'ensemble_hash':r['ensemble_hash'],'status':'POSITIVE_DIAGNOSTIC' if r['K_raw']>0 else 'NEGATIVE; NOT_A_WORKING_DESIGN'} for r in selected]
    write('table_1_recommended_parameters.csv',summary)
    engineering=[]
    for name,r in zip(names,selected):
        changed=[]
        if r['divergence_urad']!=233:changed.append('HAP transmitter optics')
        if r['jitter_urad']!=15.61 or r['sigma_h_m']!=1:changed.append('HAP pointing/tracking; residual centering requirement')
        if r['zenith_deg']!=30:changed.append('relative geometry and scheduling')
        det=(r['eta_det'],r['epsilon_det'])!=(.8,.0135)
        rr=[x for x in robust if int(x['detector_index'])==r['detector_index']]
        worst=min(x['K_raw'] for x in rr if x['case']=='joint_plus20')
        engineering.append(dict(configuration=r['configuration'],changes_at_HAP='; '.join(changed) or 'Original optical requirements',
            changes_at_UAV='Detector efficiency/noise requirement improved; no larger receiver' if det else 'Original detector efficiency/noise and 8cm receiver retained',
            additional_hardware_burden='Detector group may change; component count/mass/power unknown' if det else 'No new UAV receiver group assumed; cooperative tracking hardware unquantified',
            receiver_diameter_m=.08,transmitter_ideal_D99_m=r['transmitter_diameter_99percent_m'],
            jitter_improvement_ratio=15.61/r['jitter_urad'],centering_improvement_ratio=1/r['sigma_h_m'],
            divergence_reduction_ratio=233/r['divergence_urad'],noise_variance_reduction_ratio=.0135/r['epsilon_det'],
            relative_offset_to_beam_radius=r['sigma_s_m']/r['w_eff_m'],K_raw=r['K_raw'],joint20_K=worst,
            robustness='Nominal negative; no positive robustness claim' if r['K_raw']<=0 else ('Remains positive at sampled joint20' if worst>0 else 'Loses positivity at sampled joint20'),
            mass_kg='NOT_AVAILABLE',electrical_power_W='NOT_AVAILABLE',flight_time_gain='NOT_ESTABLISHED',hardware_validated=False))
    write('table_2_engineering_comparison.csv',engineering)
    optical=[]
    for r in B:
        optical.append({k:r[k] for k in ['eta_det','epsilon_det','divergence_urad','w0_m','wL_m','w_eff_m','transmitter_diameter_99percent_m','sigma_s_m','eta_f','m1','I_AB','chi_BE','K_raw']}|
            dict(nominal_1e2_footprint_diameter_m=2*r['wL_m'],turbulence_1e2_footprint_diameter_m=2*r['w_eff_m'],
                mean_collection_given_active=r['m1']/(r['Pactive']*r['eta_atm']),
                offset_to_beam_radius=r['sigma_s_m']/r['w_eff_m']))
    write('transmitter_optical_metrics.csv',optical)
    comparisons=[]
    for r in best:
        rr=[x for x in comparison if int(x['detector_index'])==r['detector_index']]
        for x in rr:comparisons.append([r['eta_det'],r['epsilon_det'],x['scheme'],x['VA'],x['nu_raw'],x['I_AB'],x['chi_BE'],x['K_raw']])
    headers=['Dr(m)','Div(µrad)','Jitter(µrad)','Center SD(m)','ζ(°)','L(km)','ηdet','εdet(SNU)','VA','νraw','I_AB','βI_AB','χ_BE','K']
    parameter_table=table(['Cấu hình']+headers,[[names[i]]+[r[k] for k in fields] for i,r in enumerate(selected)])
    scenario_table=table(['ηdet','εdet','ζ','Div','Jitter','Center SD','VA','ν','I_AB','βI_AB','χ_BE','K'],
        [[r[k] for k in ['eta_det','epsilon_det','zenith_deg','divergence_urad','jitter_urad','sigma_h_m','VA','nu_raw','I_AB','beta_I_AB','chi_BE','K_raw']] for r in best])
    detector_table=table(['ηdet','εdet','I_AB','βI_AB','χ_BE','K','Gap χ−βI'],
        [[r[k] for k in ['eta_det','epsilon_det','I_AB','beta_I_AB','chi_BE','K_raw','remaining_gap']] for r in A])
    stages=[]
    for noise in [.0135,.005]:
        for label,data in [('Detector only',A),('Fixed-source physical scan',physical)]:
            r=max((r for r in data if r['epsilon_det']==noise),key=lambda r:r['K_raw'])
            stages.append([noise,label,r['eta_det'],r['zenith_deg'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['K_raw']])
    pat=[]
    for r in best:
        rr={x['case']:x for x in robust if int(x['detector_index'])==r['detector_index']}
        pat.append([r['eta_det'],r['epsilon_det'],r['K_raw']]+[rr[k]['K_raw'] for k in ['jitter_plus10','centering_plus10','joint_plus10','joint_plus20','noise_0.0135','noise_0.005']])
    params='\n\n'.join(rf"""**{name}**

\[
\begin{{gathered}}
D_r=0.08\,\mathrm{{m}},\quad \theta_{{div}}={r['divergence_urad']:g}\,\mu\mathrm{{rad}},\quad \theta_{{jt}}={r['jitter_urad']:g}\,\mu\mathrm{{rad}},\\
\sigma_h={r['sigma_h_m']:g}\,\mathrm{{m}},\quad \zeta={r['zenith_deg']:g}^\circ,\quad L={r['L_km']:.10g}\,\mathrm{{km}},\\
\eta_{{det}}={r['eta_det']:g},\quad \epsilon_{{det}}={r['epsilon_det']:g},\quad V_A={r['VA']:.12g},\quad \nu_{{raw}}={r['nu_raw']:g},\\
I_{{AB}}={r['I_AB']:.12g},\quad \beta I_{{AB}}={r['beta_I_AB']:.12g},\quad \chi_{{BE}}={r['chi_BE']:.12g},\quad K={r['K_raw']:.12g}.
\end{{gathered}}
\]
""" for name,r in zip(names,selected))
    eng_table=table(['Cấu hình','Thay đổi HAP','Thay đổi UAV','Gánh nặng phần cứng','K','Robustness'],
        [[names[i],r['changes_at_HAP'],r['changes_at_UAV'],r['additional_hardware_burden'],r['K_raw'],r['robustness']] for i,r in enumerate(engineering)])
    text=rf'''# Tối ưu tham số với UAV receiver 8 cm — 2026-10-22

**{'Đã tìm thấy điểm dương trong mô hình' if positive else 'Chưa tìm thấy SKR dương trong miền đã thử'}.** Detector luôn UNTRUSTED, Dr luôn 0.08 m. Chỉ dùng noise detector 0.0135 và 0.005 SNU; không đánh giá mức thấp hơn. Không thay PDF, moments, optical collection, MI, covariance, Holevo, correlation bounds, chuẩn hóa nguồn hoặc receiver homodyne. K lớn nhất trong tám scenario đã refinement là **{maxr['K_raw']:.12g} bit/use**; gap χ−βI là **{-maxr['K_raw']:.12g}** nếu K âm. Đây là best exact tested, không phải kết luận tối ưu toàn cục hoặc no-key theorem.

## 1. Baseline và mô hình được giữ nguyên

Baseline bounded hiện tại đã tính lại trước tìm kiếm: I_AB={baseline['I_AB']:.15g}, βI_AB={baseline['beta_I_AB']:.15g}, χ_BE={baseline['chi_BE']:.15g}, K={baseline['K_raw']:.17g}. Sai khác với saved baseline nằm trong 1e-12 tại mọi field đã đối chiếu; xem [baseline_regression.json](baseline_regression.json). K lịch sử corrected trial −0.058724314679977559 thuộc optical law lịch sử khác và được xác thực riêng, không dùng thay baseline hiện tại.

HAP/UAV=20/1 km, ζ=30°, L=21.9393102292 km, λ=1550 nm, β=.95, εch=.0186, full-angle divergence233 µrad, angular SD15.61 µrad mỗi trục, residual centering SD1 m, AoA1.5 mrad, FOV half-angle6.25 mrad, τzen=.92, detector(.8,.0135), fixed MB(VA5.475,νraw.165). `configs/channel.yaml` có223 µrad tại `theta_div_rad`; đây cũng là divergence, không phải jitter. `configs/manuscript_mobility.json` ghi233 µrad cho manuscript; nghiên cứu giữ233.

Importer gọi trực tiếp `../positive_skr_without_receiver_enlargement_20261022/numeric.py` và evaluator trước của nó, byte hashes trong [startup_manifest.json](startup_manifest.json). Đây là mô hình passive random-width/circular-Gaussian hiện đã dùng cho diagnostic trước; không trở lại PDF lịch sử khác. Full-Z maximum là tối ưu số trên interval vật lý, chưa có rigorous global enclosure.

Các biểu thức hiện có được giữ nguyên:

\[
T_f=\langle\sqrt T\rangle^2,\quad N_f=(\langle T\rangle-T_f)V_A,\quad N_c=.0186\langle T\rangle,\quad N_d=\epsilon_{{det}}/\eta_{{det}},
\]
\[
N_{{post}}=\eta_{{det}}(N_f+N_c)+\epsilon_{{det}},\quad a=1+V_A,\quad b=1+\eta_{{det}}T_fV_A+N_{{post}},\quad K=.95I_{{AB}}-\chi_{{BE}}.
\]

MI chính là actual pooled fading likelihood, với conditional mean 2√(ηdet T)Reα và variance1+ηdet εch T+εdet. Không cộng fading noise lần nữa trong likelihood, không conditioning theo CSI, không postselection. Effective-channel MI được lưu riêng ở I_AB_surrogate. Outage atom được giữ; không clip K âm hoặc T.

## 2. Ý nghĩa của εdet=0.005 SNU

0.005 là giá trị giả định được người dùng cho phép của đúng biến detector excess-noise hiện tại. [Villaseñor et al., arXiv:2005.10465](https://arxiv.org/pdf/2005.10465) dùng electronic-noise υel=.005 và công thức ξdet phụ thuộc coherent efficiency γ (Eq.10); các biến này không tự đồng nhất với εdet của repo. Bài tham khảo không chứng minh phần cứng UAV ở đây đạt .005, không cung cấp phép đổi chuẩn hóa và không thay trust convention. Noise ở .005 vẫn UNTRUSTED.

Các điểm dương của nghiên cứu trước dùngnoise .0005, jitter1 µrad vàσh=.05 m không thuộc miền mới. Chúng không được đưa vào bảng kết quả hoặc dùng làm nghiệm cho yêu cầu này; chỉ artifact lịch sử được xác thực, không chạy lại các mức noise bị cấm.

## 3. Stage A — Chỉ nâng detector

Giữ nguồn và toàn bộ optics/geometry gốc. Mỗi dòng đã tính MI, βMI, Holevo và signed K:

{detector_table}
Không có điểm dương nếu mọi dòng K vẫn âm. Tăng efficiency không được giả định luôn tốt hơn trong mô hình untrusted này; bảng giữ đủ bốn mức η cho mỗi noise. Tỷ lệ giảm noise variance từ .0135 xuống .005 là2.7 lần, không phải phép chuyển sang trusted detector.

## 4. Stage B–D — HAP transmitter, PAT và geometry

Quét divergence233/100/75/50/35/25/20/15 µrad; independent jitter15.61/10/7.5/5/3/1.561 µrad và residual centering1/.5/.3/.2/.1 m. Sau đó dùng sáu PAT tiers kết hợp có chủ đích, ởζ0/15/30 và tám detector scenarios. Đây không phải toàn bộ tích Descartes jitter×centering×source×geometry.

{table(['εdet','Stage','ηdet','ζ','Div','Jitter','Center SD','K lớn nhất fixed source'],stages)}
L=19/cosζ km và toàn bộ diffraction, HV integrals/secant factors, Gd, displacement và fading moments được tính lại bởi hàm hiện có. Không tự thay turbulence hay τzen. Không quét độ cao vì chưa có profile extinction theo độ cao; giữ HAP20/UAV1 km, tránh gán khí quyển chưa hiệu chuẩn cho UAV5 km.

[transmitter_optical_metrics.csv](transmitter_optical_metrics.csv) lưu w0, footprint2wL/2weff, ideal transmitter D99, mean active collection, offset/beam radius, Tf và SKR. Công thức cũ w0=2λ/(πθdiv), Dtx99=2w0√(ln100/2). D99 chỉ là đường kính chứa99% công suất Gaussian lý tưởng, chưa phải thiết kế hard pupil có diffraction/coupling loss. Beam nhỏ hơn làm tăng yêu cầu centering; không suy ra tiết kiệm năng lượng từ divergence nhỏ.

σh là residual optical beam-centering SD theo model, không phải độ chính xác GPS hoặc chuyển động thân UAV. Có thể đặt yêu cầu PAT chủ yếu ở HAP, nhưng beacon, acquisition, latency, field of regard và hợp tác UAV chưa được mô hình hóa. Mứcσh=.1 m là yêu cầu hiệu năng quang, chưa có chứng minh đạt được trên platform cụ thể.

## 5. Stage E — Catalog nguồn exact và joint refinement

Catalog233 nguồn đã xác thực payload/hash:197 MB,36 Uniform. Physical screening giữ nguồn cố định; sau đó rank catalog đầy đủ ở context tốt nhất theo fixed-source K và moment quality cho mỗi detector. Hai baseline-optics η=.8 cũng được rank. Một bước phối hợp kiểm tra winning sources trên các physical contexts rồi rank nguồn lại tại context thắng. Tổng {len(opt['contexts'])} context trong optimization.json; các final context bổ sung nếu có nằm ở catalog_final_*.csv. P1 cố địnhν chọnVA, P2 cố địnhVA chọnν, bốn starts và delta1e-8 trong catalog. Không nội suy C,w/SKR, không tạo AP/moments mới, không khẳng định continuous/global optimum.

Tám kết quả gần zero nhất được chọn và refinement:

{scenario_table}
So sánh cùng optics/geometry/detector, nhưng mỗi family có thể chọn VA khác nhau:

{table(['ηdet','εdet','Nguồn','VA','νraw','I_AB','χ_BE','K'],comparisons)}
Gain giữa fixed MB và optimized MB bao gồm thay đổi cảVA vàν; không gọi toàn bộ là shaping-only gain. Uniform có C,w và ensemble hash riêng. Catalog rời rạc không đủ để kết luận toàn miền liên tục không có nghiệm dương.

## 6. Ba tham chiếu kỹ thuật và bảng parameter

{'Các cấu hình dương chỉ là diagnostic candidates.' if positive else 'Không có ba thiết kế dương để khuyến nghị. A/B/C dưới đây là các tham chiếu âm/gần ngưỡng đã thử, không phải thiết kế hoạt động.'} A giữ đúng thông số detector gốc; B giới hạnη≤.9 và dùngnoise .005; C là K lớn nhất đã thử trong tám scenarios. Nếu B và C trùng nhau, đó là cùng một kết quả được nhìn theo hai tiêu chí, không phải hai thiết kế độc lập.

{parameter_table}
{params}

## 7. Gánh nặng UAV, khối lượng và công suất

{eng_table}
Ưu tiên giữ8 cm và chuyển optics/PAT sang HAP là tiêu chí thiết kế, chưa chứng minh nhẹ hơn theo kg/W. Mô hình không có mass/power cho receiver, detector, ADC, beacon, gimbal hoặc controller; không thể định lượng flight-time hay năng lượng tiết kiệm. Các proxy có trong [table_2_engineering_comparison.csv](table_2_engineering_comparison.csv): Dtx99, tỷ lệ cải thiện jitter/centering/noise, offset/beam radius, nhóm detector có thay yêu cầu hay không. Số linh kiện và điện năng còn thiếu được ghi NOT_AVAILABLE. Nhãn “cân bằng” của B chỉ giới hạn efficiencyη≤.9; không xác nhận yêu cầu PAT là mức cải thiện nhỏ hoặc phần cứng khả thi.

Khi mọi tham chiếu còn âm, thứ tự gần-zero không đủ để biện minh nâng cấp phần cứng. Không khuyến nghị mua detector/PAT hoặc thêm AO nặng, telescope lớn, laser onboard công suất cao để theo đuổi các điểm âm này.

## 8. Robustness với nguồn cố định

{table(['ηdet','εdet','Nominal512','Jitter+10%','Center+10%','Cả hai+10%','Cả hai+20%','Noise.0135','Noise.005'],pat)}
Các perturbation giữ nguyên VA,ν,Dr,divergence,geometry và detector efficiency. Hai cột noise đổi đúng một biến. Nominal headline dùng512×48, bảng perturbation dùng256×32; sai khác cùng điểm được lưu ở convergence.json, không phải cải thiện thật. Không gọi điểm nominal âm là robust; không dùng perturbation làm nguồn tái tối ưu để che mất margin. Các positive nếu có phải vượt2×.95×observed MI change; đây chỉ là kiểm tra hội tụ quan sát.

## 9. Xác minh số và giới hạn

{len(validation['checks'])} scoped checks CURRENTLY_VERIFIED_PASS trên {validation['rows']} logged nodes ({validation['new_evaluations']} mới, {validation['reused_evaluations']} reuse đúng source/parameters/orders và hash dòng cũ). Mass/outage, passive support, m1/mh/Tf, noise-once, exact C,w, PSD/symplectic physicality, raw K, full-Z33/129, entropy110 digits, width32/64, direct mixture/Fourier và half output spacing được kiểm tra. Selected MI256×32 so512×48 có max observed difference {max(x['observed_MI_change'] for x in read('convergence.json')):.6g}. Không đổi tolerance sau khi thấy dấuK.

Startup bảo vệ6445 files, ngoại trừ năm task ledgers được phép cập nhật. Mô hình được import giữ nguyên bytes. Frozen SHA hiện khớp re-freeze ghi trong repo nhưng khác historical expected ởAGENTS.md; giữ promotion blocker. Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS, security_valid=false/hardware_validated=false, ObjectiveC USER_STOPPED. Không training/test/heldout/publication, không thay production baseline hoặc threshold approval.

Đây là evaluator chẩn đoán, chưa có đầy đủ fading-protocol proof, finite-key/composable security, phase calibration, reconciliation implementation hay measured aperture/PAT/detector. Việc giữ nguyên mô hình không làm các giới hạn cũ biến mất.

## 10. Kết luận và cách tái kiểm tra

{'Có candidate dương trong miền được phép; phải đọc robustness và giới hạn trước khi diễn giải.' if positive else 'Trong các tổ hợp đã thử, receiver8 cm với εdet≥.005 chưa tạo được K dương. Giảmnoise giúp thu hẹp gap nhưng optics/PAT/geometry/source adaptation vẫn chưa đủ trong catalog và miền đã xét. Không hạnoise dưới sàn hoặc thay security để tạo kết quả dương.'} Điểm K lớn nhất={maxr['K_raw']:.12g}; vẫn phải phân biệt gap số với tuyên bố bảo mật.

Tại điểm C, các thành phần noise trước detector theo đúng convention hiện có là N_fading={maxr['N_fading']:.12g}, N_channel={maxr['N_channel']:.12g}, N_detector={maxr['N_detector']:.12g}; N_post={maxr['N_post']:.12g}. Detector term lớn gấp {maxr['N_detector']/maxr['N_channel']:.6g} lần channel term và {maxr['N_detector']/maxr['N_fading']:.6g} lần fading term. Với T_f={maxr['eta_f']:.12g}, excess noise effective tổng vẫn bằng {maxr['epsilon_f']:.12g} SNU. Đây là chẩn đoán giới hạn chính ở điểm đã chọn, không chứng minh detector là giới hạn duy nhất trên toàn miền.

Không có cơ sở hiện tại để khẳng định UAV nhẹ/công suất thấp tạo secure key dưới các giới hạn này. Giữ A làm đối chứng, B làm cải thiện detector có giới hạn và C làm closest-tested reference cho manuscript; giữ cả số âm và missing hardware evidence. Không promote chúng thành baseline hoạt động.

Đầu ra chính: [table_1_recommended_parameters.csv](table_1_recommended_parameters.csv), [table_2_engineering_comparison.csv](table_2_engineering_comparison.csv), detector_scenario_best.csv, stage_A/B/C/D CSVs, source_comparison.csv, robustness.csv, selected_sensitivity.csv và all_evaluations.csv. Mỗi numerical node có exact source hash, C,w và thông số đầy đủ; JSONL giữ nguồn gốc new/reused. Tám hình vectorPDF/350dpiPNG trong figures/ dùng raw signedK, đườngK=0 và baseline; đoạn nối chỉ nối node đã tính, không nội suy nguồn.

Từ project directory, chạy ` .\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/verify.py ` để kiểm tra saved receipt, không chạy lại khoa học. Producer tái lập được ghi trong README.md; không rerun producer đã hoàn tất hoặc sửa artifact đã seal.
'''
    (OUT/'report_vi.md').write_text(text,encoding='utf-8')
    colors=['#0072B2','#D55E00','#009E73'];markers=['s','D','^'];figdir=OUT/'figures';figdir.mkdir(exist_ok=True);checks=[]
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':10,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.7,'lines.linewidth':1.1})
    def start():
        fig,ax=plt.subplots(figsize=(6.0,4.2));ax.axhline(0,color='black',ls='--',lw=.8,label='$K=0$');return fig,ax
    def save(fig,ax,name,xlabel):
        ax.set_xlabel(xlabel);ax.set_ylabel('Raw SKR diagnostic (bit/use)');ax.grid(True,ls=':',alpha=.4)
        ax.scatter([],[],color='black',marker='*',s=65,label='Original baseline')
        ax.set_yscale('symlog',linthresh=1e-4,base=10);ax.legend(frameon=False,loc='best',fontsize=7)
        fig.text(.5,.012,'8 cm Rx; untrusted; detector noise ≥ 0.005 SNU; numerical diagnostic',ha='center',fontsize=7)
        fig.tight_layout(rect=[0,.045,1,1]);pdf=figdir/(name+'.pdf');png=figdir/(name+'.png')
        fig.savefig(pdf);fig.savefig(png,dpi=350);data=pdf.read_bytes()
        assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1 and b'/Subtype /Image' not in data
        with Image.open(png) as im:
            assert min(im.size)>1000 and min(im.info['dpi'])>=349
            checks.append(dict(name=name,vector_pdf=True,pages=1,pixels=list(im.size),dpi=list(im.info['dpi'])))
        plt.close(fig)
    for number,axis,xkey,xlabel,bx in [(1,'zenith','L_km','HAP–UAV distance (km)',baseline['L_km']),
        (2,'divergence','divergence_urad','Full-angle divergence (µrad)',233),
        (3,'angular_jitter','jitter_urad','Angular pointing jitter (µrad)',15.61),
        (4,'centering','sigma_h_m','Residual optical centering SD (m)',1),
        (5,'efficiency','eta_det','Detector efficiency',.8),
        (6,'detector_noise','epsilon_det','Detector output excess noise (SNU)',.0135)]:
        fig,ax=start()
        for i,r in enumerate(selected):
            data=sorted([x for x in curves if x['configuration']==r['configuration'] and x['axis']==axis],key=lambda x:x[xkey])
            ax.plot([x[xkey] for x in data],[x['K_raw'] for x in data],color=colors[i],marker=markers[i],ms=4,label=r['configuration'].split('_')[0]+': fixed selected source')
            ax.scatter(r[xkey],r['K_raw'],color=colors[i],marker='*',s=70,zorder=6)
        ax.scatter(bx,baseline['K_raw'],color='black',marker='*',s=75,zorder=7)
        save(fig,ax,f'fig_{number}_{axis}',xlabel)
    fig,ax=start();positions=np.arange(3);width=.24
    for j,scheme in enumerate(['Uniform_best_catalog','MB_fixed','MB_best_exact_tested']):
        values=[next(x['K_raw'] for x in comparison if int(x['detector_index'])==r['detector_index'] and x['scheme']==scheme) for r in selected]
        label=['Uniform (best catalog)','MB (fixed)','MB (best exact tested)'][j]
        ax.plot(positions+(j-1)*width,values,linestyle='none',marker=markers[j],ms=6,label=label,color=colors[j])
    ax.scatter(positions,np.full(3,baseline['K_raw']),color='black',marker='*',s=70,zorder=7)
    ax.set_xticks(positions,['A','B','C']);save(fig,ax,'fig_7_source_comparison','Selected physical configuration')
    fig,ax=start();cases=['nominal','jitter_plus10','centering_plus10','joint_plus10','joint_plus20'];positions=np.arange(5)
    for i,r in enumerate(selected):
        rr={x['case']:x for x in robust if int(x['detector_index'])==r['detector_index']}
        ax.plot(positions,[rr[k]['K_raw'] for k in cases],color=colors[i],marker=markers[i],label=r['configuration'].split('_')[0])
    ax.scatter([0],[baseline['K_raw']],color='black',marker='*',s=70,zorder=7)
    ax.set_xticks(positions,['Nominal','Jitter +10%','Center +10%','Joint +10%','Joint +20%'],rotation=15)
    save(fig,ax,'fig_8_robustness','Fixed source, optics and detector')
    (OUT/'figure_validation.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',figures=checks),indent=2)+'\n',encoding='utf-8')
    print('REPORT COMPLETE; 8 vector PDF/350dpi PNG pairs')


if __name__=='__main__':main()
