"""Validate boundary candidates and produce five standalone scientific figures/report."""
from pathlib import Path
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import model as m
import run as r
from extend_bright import read_csv
from validate import precise_entropy

OUT=Path(__file__).resolve().parent


def table(headers,records):
    def fmt(v):
        return f'{v:.15g}' if isinstance(v,(int,float,np.number)) else str(v)
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join(
        '| '+' | '.join(fmt(x) for x in row)+' |\n' for row in records)+'\n'


def main():
    if (OUT/'report_vi.md').exists():raise FileExistsError('Preserve completed report')
    r.SOURCES=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    selection=r.read(OUT/'selection.json');boundary=r.read(OUT/'boundary_selection.json')
    best=selection['recommended'];reference=selection['recommended_reference_geometry'];practical=boundary['practical_candidate']
    extra=[]
    for label,row in [('practical',practical),('small_aperture',boundary['smallest_tested_aperture_candidate']),
                      ('wide_divergence',boundary['widest_tested_divergence_candidate'])]:
        c=r.candidate(row);ch=r.configure(row);mom=m.power_conserving(ch,64)
        a=m.evaluate(c,mom,order=64,grid=65);b=m.evaluate(c,mom,order=128,grid=129)
        assert abs(a['I_AB']-b['I_AB'])<2e-13
        assert abs(a['chi_BE']-b['chi_BE'])<2e-8
        assert abs(float(precise_entropy(b['a'],b['b'],b['Z_worst'],110)['chi'])-b['chi_BE'])<2e-12
        extra.append(dict(label=label,GH64_128=a['I_AB']-b['I_AB'],full_Z65_129=a['chi_BE']-b['chi_BE'],K_refined=b['K_raw']))
    probes=[]
    for radial,width in [(128,16),(256,32),(512,48)]:
        p=m.pooled_mi(r.candidate(practical),r.configure(practical),radial_order=radial,width_order=width)
        p.update(label='practical',K_pooled=.95*p['I_AB_pooled']-practical['chi_BE'])
        probes.append(p);print('PRACTICAL ACTUAL MI',radial,p['I_AB_pooled'],p['K_pooled'],flush=True)
    assert abs(probes[-1]['I_AB_pooled']-probes[-2]['I_AB_pooled'])<2e-5
    r.save('boundary_validation.json',dict(checks=extra,actual_MI_probes=probes,status='CURRENTLY_VERIFIED_PASS_NUMERICAL_ONLY'))
    regression=r.read(OUT/'regression.json');saved=regression['saved']
    A=[dict(component=k,value=float(saved[k]),interpretation=meaning) for k,meaning in [
        ('eta_f','Saved historical channel effective transmission before detector'),
        ('fading_excess_output_pre_detector','Fading output excess before detector'),
        ('channel_excess_output_pre_detector','Channel output excess before detector'),
        ('detector_excess_output_pre_detector','Untrusted output detector excess referred before eta_det'),
        ('eta_f_epsilon_f','Total pre-detector excess'),('I_AB','Consistent homodyne 1D MI'),
        ('chi_BE','Historical diagnostic Holevo'),('K_raw','Signed numerical regression only')]]
    A.extend(dict(component=k,value=float(regression[k]),interpretation='Before-detector noise ratio') for k in ['detector_over_channel','fading_over_channel'])
    r.write('table_A_noise_security_diagnosis.csv',A)
    optical=read_csv('table_B_optical_feasibility.csv')
    B=optical+read_csv('improved_pointing_optical_grid.csv')+read_csv('boundary_catalog_winners.csv')+read_csv('bright_source_comparison.csv')
    for row in B:
        row['channel_validity']='PASSIVE_BOUNDED_RANDOM_WIDTH_UNCALIBRATED_SURROGATE' if row['treatment']=='power_conserving_random_width' else 'NORMALIZED_OLD_EQUIVALENT_BEAM_COMPARISON_UNVERIFIED_PHYSICAL_APPROXIMATION'
        row['security_status']='DIAGNOSTIC_ONLY_NOT_VALIDATED'
    B.sort(key=lambda x:x['K_raw'],reverse=True);r.write('table_B_optical_feasibility_final.csv',B)
    # Every plotted point is a newly evaluated exact-source node or an authenticated saved node.
    plot_rows=[];source=r.candidate(reference)
    for factor in (1.,.1):
        for diameter in r.DIAMETERS:
            ch=m.optical(diameter,10,30,factor,factor)
            plot_rows.append({**r.evaluate(source,ch,m.power_conserving(ch),'figure_aperture'),'figure':'aperture'})
        for divergence in r.DIVERGENCES:
            ch=m.optical(.75,divergence,30,factor,factor)
            plot_rows.append({**r.evaluate(source,ch,m.power_conserving(ch),'figure_divergence'),'figure':'divergence'})
    r.write('figure_optical_data.csv',plot_rows)
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],
        'font.size':8,'axes.labelsize':8,'legend.fontsize':6.5,'xtick.labelsize':7,'ytick.labelsize':7,
        'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.7,'lines.linewidth':1.1})
    figures=OUT/'figures';figures.mkdir(exist_ok=True);figure_checks=[]
    def figure(name,xlabel,curves):
        fig,ax=plt.subplots(figsize=(3.5,2.8));ax.axhline(0,color='black',lw=.7,ls='--')
        for x,y,label,style in curves:
            ax.plot(x,y,style,label=label,markersize=3)
            assert all(math.isfinite(v) for v in x+y)
        ax.set_xlabel(xlabel);ax.set_ylabel('Raw rate diagnostic (bit/use)')
        ax.grid(True,ls=':',lw=.45,alpha=.6);ax.legend(frameon=False)
        fig.text(.5,.012,'Untrusted homodyne; security not validated',ha='center',fontsize=6)
        fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(figures/(name+'.pdf'));fig.savefig(figures/(name+'.png'),dpi=350)
        with Image.open(figures/(name+'.png')) as im:
            assert min(im.size)>=900
            figure_checks.append(dict(name=name,pixels=list(im.size),dpi=im.info.get('dpi'),raw_signed=True))
        plt.close(fig)
    for key,xkey,xlabel in [('aperture','D_r','Receiver aperture diameter (m)'),('divergence','theta_div_urad','Full beam divergence (µrad)')]:
        curves=[]
        for factor,label,style in [(1.,'Original jitter','o-'),(.1,'Both jitter terms ×0.1','s-')]:
            values=sorted([x for x in plot_rows if x['figure']==key and x['position_factor']==factor],key=lambda x:x[xkey])
            curves.append(([x[xkey] for x in values],[x['K_raw'] for x in values],label,style))
        figure('fig_'+key,xlabel,curves)
    C=read_csv('table_C_detector_sensitivity_final.csv')
    for key,xkey,xlabel in [('detector_noise','epsilon_det','Detector output excess noise (SNU)'),('detector_efficiency','eta_det','Detector efficiency')]:
        curves=[]
        for label,text,style in [('original','Original optical link','o-'),('recommended_bright','Improved optical/pointing link','s-')]:
            values=[x for x in C if x['configuration_id']==label and (x['eta_det']==.8 if key=='detector_noise' else x['epsilon_det']==.0135)]
            values.sort(key=lambda x:x[xkey]);curves.append(([x[xkey] for x in values],[x['K_raw'] for x in values],text,style))
        figure('fig_'+key,xlabel,curves)
    old_dist=read_csv('distance_scan.csv');bright_dist=read_csv('bright_distance_scan.csv')
    curves=[]
    for values,label,style in [([x for x in old_dist if x['configuration_id']=='original'],'Original link, catalog MB','o-'),
                               ([x for x in bright_dist if x['configuration_id']=='recommended_0deg'],'0.75 m / 10 µrad, improved jitter','s-')]:
        values.sort(key=lambda x:x['L_km']);curves.append(([x['L_km'] for x in values],[x['K_raw'] for x in values],label,style))
    figure('fig_distance','Slant link distance (km)',curves)
    r.save('figure_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',figures=figure_checks,
           source_interpolation=False,smoothed=False,one_axis_per_figure=True))
    winners=read_csv('bright_source_comparison.csv');original=read_csv('source_comparison.csv')
    thresholds=r.read(OUT/'bright_thresholds.json');bounds=boundary['roots']
    actual=read_csv('actual_pooled_fading_MI.csv')
    text='''# Khảo sát SKR với detector untrusted — 2026-10-22

Đã thực thi regression, 140 cấu hình quang học ở nguồn cố định với ba mô hình kênh, catalog exact 233 nguồn, các khảo sát detector/pointing, tìm nghiệm có bracket và năm hình raw có dấu. **Có giá trị dương trong mô hình kênh thụ động mới; chưa có kết quả nào được xác nhận là sinh khóa an toàn trên hệ thống HAP–UAV thực.** Không đổi detector thành trusted, không clip K, không tạo hay nội suy C,w.

## Q1. Vì sao kết quả gốc âm?

Regression dùng nguyên hàm của trial trước tái lập I_AB=0.0007587634870959417, chi_BE=0.0594451399927187034, K=-0.0587243146799775588. Bảng A dưới đây là kết quả trên đúng kênh gốc, không trộn với mô hình mới. Detector excess trước loss là0.016875, lớn gấp3436.14 lần phần channel và chiếm phần lớn N_pre. Fading/channel=22.84. Với eta_f≈2.435e-4, nhiễu detector output0.0135 là quá lớn so với tín hiệu thu.

Hiệu chỉnh loss/noise là nhất quán ở cấp covariance: t=eta_det*mhalf², N_post=eta_det[(m1-mhalf²)VA+epsilon_ch*m1]+epsilon_det, b=1+tVA+N_post. Vacuum1 xuất hiện một lần; không thêm1-eta hay1-eta_det vào excess; epsilon_det là output quadrature SNU, không tự đồng nhất với v_el. Không thấy double count detector trong trial này.

Trong mô hình Gaussian hiệu dụng, N_post>=2t là điều kiện entanglement-breaking; tại liên kết gốc detector0.0135 đã vượt2t nhiều lần ngay trước khi thêm fading. Đây chỉ là chẩn đoán của surrogate Gaussian, không là chứng minh no-key của mọi kênh fading ngoài miền khảo sát.

## Q2. Có dương với detector gốc không?

**Có trong mô hình Gaussian random-width thụ động đã khai báo**, khi tăng thu quang và giảm pointing jitter. Ở phần cứng/quang học gốc, tối ưu catalog chỉ cho K=-0.0584489853; detector sweep kể cả epsilon_det=0 vẫn không có giá trị dương trong catalog đã thử. Không suy ra bất khả thi ngoài catalog/model.

Chỉ quét aperture/divergence/geometry với jitter gốc ở fixed MB cũng không cho giá trị dương trong mô hình thụ động. Tăng aperture không bù được việc beam hẹp thường lệch ra ngoài khẩu độ. Phải xét pointing cùng collection, không chọn một điểm âm gần zero rồi gọi đó là cải thiện liên kết.

## Q3. Ứng viên tốt nhất tìm được

Ứng viên lớn nhất trong các cấu hình đã thử dùng D_r=0.75m, divergence full10µrad, sigma_position=0.1m, angular jitter1.561µrad, VA=8, nu_raw=0.125. Giữ eta_det=.8, epsilon_det=.0135, epsilon_ch=.0186, beta=.95, homodyne1D, AO OFF, phase OFF như giả thiết gốc. Tại zenith0deg/L19km K_surrogate≈0.424068; giữ zenith30deg/L21.9393102292km K_surrogate≈0.402568. Toàn bộ thông số và phân rã ở bảng dưới.

Đây là BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY. VA=8 là biên catalog MB; không có chứng nhận tối ưu liên tục/toàn cục. Không tạo AP mới vì catalog đủ để trả lời câu hỏi positivity trong diagnostic; mở rộng năng lượng không giúp xác thực mô hình vật lý/security.

## Q4. Ngưỡng cải thiện nào?

Tại zenith30deg, cùng giảm hai jitter xuống0.1, aperture nhỏ nhất trong grid có ứng viên dương là0.55m;0.40m ở10µrad vẫn âm sau scan catalog. Divergence lớn nhất trong grid có dương tạiD=.75m là50µrad;100µrad vẫn âm sau scan catalog. Các root refinement bên dưới giữ một nguồn exact cố định, không phải ngưỡng tối ưu toàn miền. Ngưỡng detector của link sáng có thể nằm ngoài danh sách0.8..1 hoặc0..0.0135; không được áp các ngưỡng đó cho link gốc. Khoảng cách38km vẫn dương ở nguồn/pointing đã chọn; đây là L lớn nhất đã thử (zenith<=60deg), không là maximum-range certificate.

## Q5. MB giúp bao nhiêu?

Ở link cải thiện30deg, fixed MB(.165,5.475) cho0.378577; catalog-best MB(.125,8) cho0.402568, tăng khoảng0.023991 bit/use,6.34%. Cải thiện optical/pointing đã làm fixed MB dương; source optimization bổ sung sau đó. Catalog-best Uniform cho0.0440529 tạiVA2.05. So sánh Uniform/MB này dùng cùng link/detector/receiver, nhưng mỗi family chọn năng lượng tốt nhất trong catalog: không quy toàn bộ chênh lệch thành shaping gain ở cùng năng lượng.

Alternating P1/P2 đã chạy trên các tọa độ exact có sẵn với bốn starts và deltaK1e-8, dừng ở catalog fixed point. Đây không phải continuous convergence hay global optimum; toàn bộ catalog scan, nguồn thắng và coordinate log được lưu.

## Q6. Khuyến nghị sửa ít hơn

Ứng viên ít đòi hỏi transmitter aperture hơn là D_r=.55m, divergence25µrad, cùng jitter0.1m/1.561µrad, zenith30deg, detector gốc. Catalog chọn VA3.5,nu_raw=.2, cho K_surrogate≈0.101322. Gaussian transmitter chứa99% công suất cần đường kính khoảng0.1198m, so với0.2995m cho10µrad. Đây là yêu cầu hình học lý tưởng, không là xác nhận phần cứng, độ phân kỳ thực hoặc năng lực ổn định UAV/HAP.

Ưu tiên đo/hiệu chuẩn pointing và coupling rồi xác minh antenna/aperture/beam budget. Không đề xuất mua phần cứng chỉ dựa trên surrogate này. Không gán gain AO tùy ý: không có AO/coupling model được kiểm chứng cho trial này; chỉ có sensitivity giảm toàn profile Cn² theo các hệ số khai báo. Phase noise vẫn OFF theo phạm vi lịch sử, không được tuyên bố đã mô hình hóa phần cứng phase tracking thực.

## Q7. Kết quả nào security-valid?

**Chưa có kết quả nào được chứng nhận security-valid/operational.** Detector composition, homodyne conditioning, positivity/normalization, source identity và uncertainty/spectrum được kiểm tra. Công thức DBL dùng c1=sqrt(eta_det)mhalf C, c2=sqrt(eta_det)mhalf VA/2, nB=(b-1)/2; radius=2sqrt[w(nB-c2²/nbar)]=sqrt(2N_post*w). Tính numerical maximum trên toàn giao khoảng correlation với physical uncertainty cap, không giả định endpoint worst-case. 33/65/129 grids và entropy80/110 được đối chiếu, nhưng chưa có rigorous global enclosure.

Tài liệu lý thuyết gốc: [Denys–Brown–Leverrier 2021, Sections3–5](https://arxiv.org/html/2103.13945). Conditional eigenvalue homodyne sqrt[a(a-z²/b)] được dùng cùng MI1D, không ghép heterodyne. Đây là lý do giữ bound discrete-modulation, không thay bằng công thức Gaussian modulation.

MI Gaussian hiệu dụng của pooled fading không tự là lower bound cho MI discrete-input thực. Vì vậy đã tính thêm actual pooled homodyne likelihood cho các ứng viên chọn, không conditioning theo CSI và không postselection. Các kết quả này vẫn dùng bound moment/frozen-source trong một kênh iid mô phỏng; không thay thế parameter estimation, finite-key, authentication, hardware calibration hay proof cho fading tương quan. Mọi output có security_valid=false và rate-per-transmitted-use, gồm cả outage.

## Mô hình bounded mới và lý do không chỉ normalize PDF cũ

PDF lognormal lịch sử có tail>1. Reference55cm/10µrad trước dùng aperture-averaged v khác với raw-Rytov manuscript; không trộn hai closure. Trong closure reference đã lưu, missing mass≈3.6536e-5. Trong optical manuscript có trường hợp tail lớn hơn nhiều.

Hai mô hình so sánh được tính riêng: conditional-active trên(0,1] giữ P0, và đưa toàn tail invalid về erasure/vacuum. Cả hai tính lại mọi moment, không ghép raw moments với support bị cắt. Conditional-active là lựa chọn distribution mới, không phải cứ lọc sample rồi miễn phí postselect key rate.

Hơn nữa equivalent-beam pointing có thể sai rất lớn khi aperture lớn hơn beam: tạiD=.75m/10µrad/30deg/jitter gốc, conditioning của approximation có thể cho K dương, trong khi tích phân thu Gaussian tròn dự đoán công suất thu rất nhỏ. Các hàng đó chỉ là comparison, không được dùng để kết luận khả thi.

Mô hình primary mới: mỗi realization là Gaussian beam **tổng công suất bằng1**, bán kính w=w_eff exp(-S/2), S~N(-v/2,v), v lấy raw Rytov manuscript. On-axis intensity fluctuation là lognormal, còn aperture collection tính đúng CDF noncentral-chi-square H=F_chi2(df2,nc=4r²/w²)(4a²/w²). Jitter r Rayleigh với sigma_s²=sigma_position²+(L theta_jitter)². T=eta_atm H nằm trong[0,eta_atm], không cần clip hoặc normalize; AoA atom riêng. Mean H theo Rayleigh có tích phân độc lập1-exp[-2a²/(w²+4sigma_s²)]. Đây là passive Gaussian random-width **surrogate mới**, không phải atmospheric closure được đo hay re-freeze của production. G_d/HV được tái tính theo từng angle; distribution mới không giữ nguyên moment lịch sử.

Outage detector full-mixture vẫn phát sinh epsilon_det ở vacuum input; active-only tắt noise khi outage là một receiver hypothesis khác. Cả hai được so sánh, không chia K cho Pactive. Không coi postselection tự động an toàn.

## Validation và provenance

Regression exact so với saved prior trial đã PASS. validate.py kiểm tra19370 saved rows cùng source C,w và homodyne/untrusted assumptions;51 named checks gồm aperture convolution độc lập, MI-GH64/128, width-GH32/64, full-Z33/129, entropy80/110, detector-zero actual covariance và DBL moment identity. Boundary candidates được kiểm tra bổ sung. Actual-fading MI refinement radial128/256/512, width16/32/48 có tolerance diagnostic2e-5 bit/use; surrogate MI tolerance2e-13; không gọi đó là rigorous security enclosure. Dấu dương của các ứng viên lớn không phụ thuộc sai số refinement này.

Lịch sử thực thi được giữ: lần đầu guard phát hiện rounding q0 d/d ở45deg, sửa bằng đồng nhất thức q0 normalization và tăng160digits, không clip probability; partial files ởattempt_1_precision_failure. Lần scan kế tiếp hoàn thành các numerical stage nhưng summary gặp numpy-int64 JSON serialization; đã sửa serializer và tiếp tục từ CSV, không rerun scientific stages. Việc chọn điểm âm gần zero ưu tiên link tối; bright-link extension và boundary refinement được ghi riêng, không xóa các kết quả âm ban đầu.

Không tạo C,w, không interpolation/large source grid, không trusted-detector substitution, không sửa production/cache/frozen/manuscript. Nguồn có support256; VA=2nbar. SHA/input manifests và final receipt bảo vệ cả thay đổi chưa commit của trial trước. Giữ NOT_READY_FOR_PUBLICATION_SCALE_RUNS, UNVALIDATED_SECURITY_MODEL, frozen-hash historical conflict và ObjectiveC USER_STOPPED; không training/test/held-out/publication, commit/push.

Scripts tự chứa trong thư mục này: model.py, run.py, extend_bright.py, refine_boundary.py, validate.py, finish.py. Producer không ghi đè kết quả đã hoàn tất. Không chạy lại trial đã sealed. Bảng C hoàn chỉnh ởtable_C_detector_sensitivity_final.csv; bảng B sorted ởtable_B_optical_feasibility_final.csv. Năm hìnhvectorPDF/350dpiPNG ởfigures/; không smoothing hay nội suy C,w/SKR.

## Bảng A — Chẩn đoán đúng trial lịch sử

'''
    text+=table(['Component','Value','Interpretation'],[[a['component'],a['value'],a['interpretation']] for a in A])
    text+='\n## Các ứng viên chọn — cùng detector untrusted gốc\n\n'
    text+=table(['Candidate','D_r (m)','Full divergence (µrad)','L (km)','VA','nu_raw','eta_f','epsilon_f','I_AB','beta I_AB','chi_BE','K_raw'],
        [[label]+[row[k] for k in ['D_r','theta_div_urad','L_km','VA','nu_raw','eta_f','epsilon_f','I_AB','beta_I_AB','chi_BE','K_raw']]
         for label,row in [('largest_tested',best),('same_geometry_30deg',reference),('smaller_transmitter',practical)]])
    text+='\n## Phân rã nhiễu trước detector\n\n'
    text+=table(['Candidate','N_fading','N_channel','N_detector','N_pre','N_post'],[[label]+[row[k] for k in ['N_fading','N_channel','N_detector','N_pre','N_post']]
        for label,row in [('largest_tested',best),('same_geometry_30deg',reference),('smaller_transmitter',practical)]])
    text+='\n## Ngưỡng fixed exact source, model-dependent\n\n'
    text+=table(['Quantity','Root','Bracket','Configuration/source scope'],[[x['variable'],x['root'],str((x['lower'],x['upper'])),'D=.75m/10µrad/0deg or stated pointing root; fixed source'] for x in thresholds if 'root' in x]
        +[[x['variable'],x['root'],str((x['lower'],x['upper'])),'30deg, both jitter factors=.1; fixed exact source'] for x in bounds])
    text+='\n## Source comparison, cùng optical/detector/receiver\n\n'
    text+=table(['Configuration','Source group','VA','nu_raw','I_AB','chi_BE','K_raw'],[[x[k] for k in ['configuration_id','source_group','VA','nu_raw','I_AB','chi_BE','K_raw']] for x in winners])
    text+='\n## Actual pooled fading MI — highest quadrature order\n\n'
    last=[x for x in actual if x['radial_order']==512]+[probes[-1]]
    text+=table(['Candidate','Actual I_AB','chi_BE','Raw functional with actual MI'],[[x['label'],x['I_AB_pooled'],x.get('chi_BE',practical['chi_BE']),x['K_pooled']] for x in last])
    text+='\n## Figures\n\n'+''.join(f'- [{x["name"]} PDF](figures/{x["name"]}.pdf), [PNG](figures/{x["name"]}.png).\n' for x in figure_checks)
    (OUT/'report_vi.md').write_text(text,encoding='utf-8')
    r.save('completion.json',dict(status='COMPLETE_NUMERICAL_DIAGNOSTIC_ONLY',security_valid=False,
        additional_boundary_checks=extra,figures=len(figure_checks),actual_MI_practical=probes[-1],
        scientific_production_changed=False,new_source_moments=0))
    print('REPORT AND FIVE FIGURES COMPLETE',flush=True)


if __name__=='__main__':main()
