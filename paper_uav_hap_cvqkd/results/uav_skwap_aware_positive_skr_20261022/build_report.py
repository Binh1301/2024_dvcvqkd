"""Vietnamese SWaP report and figures from saved numerical evidence only."""
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
def fmt(v):return 'UNKNOWN' if v is None else (f'{v:.12g}' if isinstance(v,(int,float,np.number)) else str(v))
def table(headers,data):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(fmt,r))+' |\n' for r in data)+'\n'


def main():
    if (OUT/'final_receipt.json').exists():raise FileExistsError('Preserve sealed output')
    sel=read('selection.json');selected=sel['recommendations'];validation=read('validation.json')
    minimum=read('source_refined_minimum.json');opt=read('optimization.json');A=rows('table_A_receiver_detector.csv');positive=rows('table_B_positive_candidates.csv')
    roots=rows('critical_receiver_roots.csv');curves=rows('fixed_source_aperture_curves.csv');robust=rows('robustness.csv')
    comparisons=rows('source_comparison.csv');sensitivity=rows('detector_sensitivity.csv');hardware=read('hardware_evidence.json')
    names=['A — Ưu tiên receiver nhỏ','B — Tham chiếu cho mục tiêu cân bằng chưa đạt','C — Tham chiếu hiệu năng']
    # Use the most refined saved node for an identical ensemble and physical point.
    fields=['D_r','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','eta_det','epsilon_det']
    nodes={}
    for line in (OUT/'evaluations.jsonl').read_text().splitlines():
        r=json.loads(line)
        k=(r['ensemble_hash'],*[r[x] for x in fields])
        if k not in nodes or (r['radial_order'],r['width_order'])>(nodes[k]['radial_order'],nodes[k]['width_order']):nodes[k]=r
    per=[]
    for diameter in [x['D_r'] for x in opt['history']]:
        for eta,noise in [(.8,.0135),(.95,.0135),(.8,.005),(.95,.005)]:
            valid=[r for r in nodes.values() if r['family']=='MB' and r['D_r']==diameter and r['eta_det']==eta and r['epsilon_det']==noise
                and r['divergence_urad'] in [15.,20.,25.,35.,50.] and r['jitter_urad'] in [15.61,10.,5.,3.,1.561]
                and r['sigma_h_m'] in [1.,.5,.3,.2,.1] and r['zenith_deg'] in [0.,15.,30.]]
            for branch,predicate in [('jitter_at_least3',lambda r:r['jitter_urad']>=3),('including_1p561',lambda r:True)]:
                r=max((r for r in valid if predicate(r)),key=lambda r:r['K_raw']);per.append({**r,'branch':branch})
    write('aperture_best_exact_tested.csv',per)
    impacts=[]
    for context in ['original_optics','improved_fixed_optics','improved_nadir']:
        local=[r for r in A if r['optical_context']==context]
        base=next(r for r in local if r['D_r']==.08 and r['eta_det']==.8 and r['epsilon_det']==.0135)
        for label,diam,eta,noise in [('aperture8to20cm',.20,.8,.0135),('efficiency80to95',.08,.95,.0135),('noise0135to005',.08,.8,.005),('combined',.20,.95,.005)]:
            r=next(r for r in local if r['D_r']==diam and r['eta_det']==eta and r['epsilon_det']==noise)
            impacts.append(dict(optical_context=context,change=label,baseline_K=base['K_raw'],modified_K=r['K_raw'],delta_K=r['K_raw']-base['K_raw'],source_hash=r['ensemble_hash']))
    write('isolated_parameter_impacts.csv',impacts)
    engineering=[];energy=[]
    for r in selected:
        engineering.append(dict(design=r['design'],balanced_objective_met=sel['balanced_objective_met'] if r['design'].startswith('B') else 'NOT_BALANCED_ROLE',receiver_m=r['D_r'],detector_efficiency=r['eta_det'],detector_excess_noise=r['epsilon_det'],
            detector_upgrade='noise/efficiency requirement changed' if (r['eta_det'],r['epsilon_det'])!=(.8,.0135) else 'reference detector parameters',
            PAT_requirement=f"{r['jitter_urad']}urad angularSD; {r['sigma_h_m']}m optical centeringSD",HAP_transmitter_D99_m=r['transmitter_diameter_99percent_m'],
            receiver_clear_area_ratio_to8cm=(r['D_r']/.08)**2,payload_mass_kg='UNKNOWN',QKD_electrical_power_W='UNKNOWN',
            payload_burden='Custom1550nm optics plus PAT/LO/DAQ/control integration required; no authenticated UAV BOM',
            power_evidence='Grounded component examples only; not an assembled power budget',nominal_engineering_margin_met=r['K_raw']>=1e-4,K_raw=r['K_raw'],joint10_K=r['joint10_K'],joint20_K=r['joint20_K'],
            robustness=r['robustness_class'],hardware_validated=False))
        energy.append(dict(design=r['design'],K_raw=r['K_raw'],R_key_over_f_rep=max(0,r['K_raw']),f_rep_Hz='UNKNOWN',
            receiver_bandwidth_for_selected_SNU='NOT_AUTHENTICATED',R_key_bit_s='NOT_COMPUTED',external_p_avail='UNKNOWN',R_useful_bit_s='NOT_COMPUTED',
            P_UAV_QKD_W='UNKNOWN',E_bit_J='NOT_COMPUTED',total_key_bits_per_sortie='NOT_COMPUTED',reason='Missing coherent BOM/power, compatible repetition rate, external availability and flight energy/duty'))
    write('table_C_UAV_engineering.csv',engineering);write('throughput_energy.csv',energy)
    evidence=[{**r,'mass_kg':r['mass_kg'] if 'mass_kg' in r and r['mass_kg'] is not None else 'UNKNOWN',
        'electrical_operating_W':r['electrical_operating_W'] if r.get('electrical_operating_W') is not None else 'UNKNOWN'} for r in hardware['rows']]
    write('UAV_mass_power_evidence.csv',evidence)
    D=[];savings=[]
    for r in roots:
        D.append({**r,'pointing_scenario':'moderate3' if r['jitter_urad']==3 else 'demanding1p561',
            'minimum_rounded_tested_positive_D_m':r['rounded_D_m'],'raw_K_at_rounded_D':r['rounded_K'],
            'remaining_limitations':'fixed common source, beam35urad, zenith0, centering.1m; local bracket, hardware/security unvalidated'})
    write('table_D_critical_receiver_thresholds.csv',D)
    for jitter in [3.,1.561]:
        local=[r for r in roots if r['jitter_urad']==jitter and r['target_K']==0]
        ref=next((r for r in local if r['eta_det']==.8 and r['epsilon_det']==.0135),None)
        if ref:
            for r in local:
                savings.append(dict(jitter_urad=jitter,reference_eta=.8,reference_noise=.0135,eta_det=r['eta_det'],epsilon_det=r['epsilon_det'],
                    reference_D_crit_m=ref['D_crit_m'],D_crit_m=r['D_crit_m'],diameter_reduction_m=ref['D_crit_m']-r['D_crit_m'],
                    ideal_clear_area_reduction_fraction=1-(r['D_crit_m']/ref['D_crit_m'])**2,
                    scope='GEOMETRIC_APERTURE_ONLY; NOT_MASS_POWER_OR_FLIGHT_TIME_SAVING'))
    write('detector_aperture_savings.csv',savings)
    aperture_saving_note='; '.join(f"jitter {r['jitter_urad']:g} µrad: Dcrit {r['reference_D_crit_m']*100:.6g} → {r['D_crit_m']*100:.6g} cm, giảm {r['diameter_reduction_m']*100:.6g} cm" for r in savings if r['eta_det']==.95 and r['epsilon_det']==.005)
    param_fields=['D_r','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','L_km','eta_det','epsilon_det','VA','nu_raw','m1','eta_f','epsilon_f','I_AB','beta_I_AB','chi_BE','K_raw']
    units=['m','µrad, full angle','µrad, SD','m, SD','degree','km','dimensionless','SNU','SNU','raw','dimensionless','dimensionless','SNU','bit/use','bit/use','bit/use','bit/use']
    param_table=table(['Tham số','Đơn vị','A','B','C'],
        [[key,unit]+[r[key] for r in selected] for key,unit in zip(param_fields,units)])
    summary_table=table(['Vai trò','Receiver (cm)','Jitter (µrad)','ηdet','εdet (SNU)','K (bit/use)','Độ bền'],
        [[names[i],r['D_r']*100,r['jitter_urad'],r['eta_det'],r['epsilon_det'],r['K_raw'],r['robustness_class']] for i,r in enumerate(selected)])
    balance_note=('B đáp ứng ưu tiên jitter ≥ 3 µrad và còn K ≥ 10⁻⁴ khi residual tăng đồng thời 10%.' if sel['balanced_objective_met'] else
        'Chưa tìm được thiết kế B đáp ứng đồng thời PAT ưu tiên (jitter ≥ 3 µrad) và độ bền 10% trong các điểm đã thử. B dưới đây chỉ là tham chiếu dương có SKR joint+10% tốt nhất trong shortlist, nhưng vẫn âm khi perturb đồng thời; không phải thiết kế cân bằng đạt yêu cầu.')
    engineering_note='; '.join(f"{r['design'][0]}: {'đạt' if r['K_raw']>=1e-4 else 'chưa đạt'} K ≥ 10⁻⁴ ở nominal" for r in selected)
    distinct_note=f"Ba vai trò tương ứng {sel['distinct_recommended_physical_points']} cấu hình vật lý khác nhau. B/C trùng thông số là cùng một cấu hình, không phải hai thiết kế độc lập."
    effect_note=' '.join(f"Ở {context}, thay đổi đơn lẻ có deltaK lớn nhất là {max((r for r in impacts if r['optical_context']==context and r['change']!='combined'),key=lambda r:r['delta_K'])['change']}." for context in ['original_optics','improved_fixed_optics','improved_nadir'])
    noise_note='; '.join(f"{r['design'][0]}: deltaK={next(x['K_raw'] for x in sensitivity if x['design']==r['design'] and x['eta_det']==r['eta_det'] and x['epsilon_det']==.005)-next(x['K_raw'] for x in sensitivity if x['design']==r['design'] and x['eta_det']==r['eta_det'] and x['epsilon_det']==.0135):.12g} bit/use" for r in selected)
    per_table=table(['Dr(cm)','ηdet','εdet','Nhánh','Div','Jitter','CenterSD','ζ','VA','ν','K'],
        [[100*r['D_r'],r['eta_det'],r['epsilon_det'],r['branch'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['zenith_deg'],r['VA'],r['nu_raw'],r['K_raw']] for r in per])
    threshold_table=table(['ηdet','εdet','Jitter','TargetK','Dcrit(cm)','RoundedD(cm)','K tại roundedD'],
        [[r['eta_det'],r['epsilon_det'],r['jitter_urad'],r['target_K'],100*r['D_crit_m'],100*r['rounded_D_m'],r['rounded_K']] for r in roots])
    robust_table=table(['Thiết kế','K nominal','Jitter+10%','Center+10%','Joint+10%','Joint+20%','Noise.0135','Noise.005'],
        [[names[i],r['K_raw']]+[next(x['K_raw'] for x in robust if x['candidate']==r['candidate'] and x['case']==case)
            for case in ['jitter_plus10','centering_plus10','joint_plus10','joint_plus20','noise_0.0135','noise_0.005']] for i,r in enumerate(selected)])
    small=[r for r in per if .15<=r['D_r']<=.20];middle=[r for r in positive if .25<=r['D_r']<=.30 and r['jitter_urad']>=3]
    smallbest=max(small,key=lambda r:r['K_raw']);regular20=[r for r in middle if r['joint20_K']>=1e-4]
    hardware_table=table(['Nhóm','Ví dụ / nguồn','Khối lượng(kg)','Công suất điện(W)','Giới hạn'],
        [[r['group'],f"[{r['item']}]({r['url']})",r.get('mass_kg'),r.get('electrical_operating_W'),r['note']] for r in hardware['rows']])
    eng_table=table(['Thiết kế','Receiver','Detector','PAT','Gánh nặng payload','Power evidence','K','Robustness'],
        [[names[i],r['receiver_m'],f"eta{r['detector_efficiency']}; noise{r['detector_excess_noise']}",r['PAT_requirement'],r['payload_burden'],r['power_evidence'],r['K_raw'],r['robustness']] for i,r in enumerate(engineering)])
    baseline=read('regression.json')['records'][0]['result']
    body=rf'''# Receiver UAV nhỏ và detector cải thiện

Thư mục thí nghiệm đề ngày 2026-10-22; tiếp tục và đóng gói ngày 2026-10-23 (Asia/Bangkok).

Đã hoàn tất nghiên cứu tham số với detector **UNTRUSTED**, homodyne 1D và các công thức cũ giữ nguyên. Ứng viên dương đã qua kiểm tra số nhỏ nhất được tìm thấy có Dr={sel['minimum_evaluated_positive_m']*100:.6g} cm; receiver nhỏ nhất trong menu chính có ứng viên dương là {fmt(sel['primary_minimum_sampled_positive_m'])} m. Đây là kết quả nhỏ nhất đã thử/cục bộ, chưa chứng nhận receiver nhỏ nhất toàn miền. Chưa xác thực phần cứng hoặc chứng minh bảo mật cho các SKR này.

{summary_table}
{balance_note}

{distinct_note}

{engineering_note}. Tiêu chí này chỉ là margin kỹ thuật.

## Bảng tham số A/B/C

{param_table}
C,w và ensemble hash chính xác nằm trong selected_designs.csv và selection.json. Bảng trên ghi trực tiếp I_AB, βI_AB, χ_BE và excess noise hiệu dụng.

## Mô hình, regression và phạm vi

Giữ M256, beta.95, epsilon_ch.0186SNU, HAP20/UAV1km, tau_zen.92, AO/phaseOFF, đúng PMF/normalization và exact C,w. Không thêm AO/PAT distribution, không đổi loss/noise convention, MI hoặc full-Z Holevo. T_f=E[sqrtT]^2; N_fading=(E[T]-T_f)VA; N_channel=.0186E[T]; N_detector=epsilon_det/eta_det; N_post=eta_det(N_fading+N_channel)+epsilon_det. Vacuum1 xuất hiện một lần. Actual pooled fading MI là chính; MI hiệu dụng được lưu riêng. Không clip K âm; outage atom được giữ.

Parameter adapter gọi propagation và power-conserving collector cũ. Dr chỉ thay vào cùng circular-aperture CDF; code bytecode của hàm MI giống hệt hàm đã lưu, chỉ dependency quadrature nhận khẩu độ thay đổi. Các bytes mô hình lịch sử được hash-bind và giữ nguyên. Bốn fresh regression8cm baseline,8cm gần đây,40.1cm và55cm đã khớp trước search; xem regression.json. Baseline hiện tại K={baseline['K_raw']:.17g}; historical corrected-trial K=-.05872431468 thuộc optical law khác nên không đánh tráo hai baseline.

Full divergence233µrad ở manuscript khác223µrad tại theta_div_rad của config; cả hai là divergence, không phải jitter15.61µrad. Không sửa production tau_zen=null hoặc phase mapping chưa giải quyết. Quét geometry0/15/30 bằng đúng phương trình; không đổi độ cao hoặc dựng profile khí quyển mới.

Chỉ dùng detector noise.0135/.005SNU, eta.8/.85/.9/.95. .005 là giả định của biến epsilon_det hiện tại, không bằng chứng thực nghiệm hoặc phép đồng nhất với electronic v_el của Villaseñor. Không dùng các kết quả cũ ởnoise.0005 hoặc sigma_h.05m làm nghiệm cho nhiệm vụ này.

## Stage A — Receiver và detector, nguồn cố định

table_A_receiver_detector.csv giữ đủ I_AB,betaI,Holevo,K cho sáu Dr và tám detector scenarios ở optics gốc, optics35urad/jitter3urad/centering.1m tại30deg và nadir. Các delta sau giữ đúng nguồn/optics/geometry trong từng nhóm:

{table(['Optical context','Thay đổi','K gốc','K mới','DeltaK'],[[r['optical_context'],r['change'],r['baseline_K'],r['modified_K'],r['delta_K']] for r in impacts])}
{effect_note}

Không quy gain sau tối ưu nguồn thành hiệu ứng detector/aperture riêng. Tăng efficiency không mặc định cải thiện K đơn điệu trong mọi kênh untrusted. TableA có đủ thông số để kiểm chứng điều này.

## Stage B–D — Optics, PAT, nguồn và ngưỡng

Screen có sáu PAT tiers, năm beam và ba góc cho bốn detector corners, không full Cartesian jitter×centering×source. Eta.85/.9 có trong StageA và detector sensitivity của thiết kế cuối. Ưu tiên nhánhjitter>=3urad;1.561urad là demanding reference. Residual beam-centering SD là sai số quang tại beam/receiver, không đồng nhất với độ chính xác GPS hoặc vị trí thân UAV.

Tối ưu nguồn dùng 233 payload exact (197 MB / 36 Uniform), bốn starts P1/P2 trong catalog; không nội suy C,w/SKR hoặc AP mới. Tất cả coordinate probes thực đều được lưu. Điểm đã cache ở Stage A được đưa lại đúng vào đủ 90 physical contexts mỗi nhánh; source_coverage.json xác minh metadata stage không làm thiếu nhánh đã tính. optimization_phase1.json giữ snapshot trước bổ sung coverage. Đây vẫn là best exact tested, không global/continuous optimum.

{per_table}

Các ngưỡng dưới đây dùng **cùng một nguồn exact**, divergence 35 µrad, zenith 0° và centering 0,1 m. Chỉ Dr và detector/pointing scenario ghi ở bảng thay đổi. Root có bracket đầu tiên trên menu tăng Dr, target 0 hoặc 1e-4. Số chữ số của root là độ chính xác số, không phải tolerance chế tạo. Không gọi đây là global minimum hoặc certified threshold:

{threshold_table}
critical_receiver_status.csv giữ NO_SIGN_CHANGE nếu không bracket; không ngoại suy ngoài 45 cm. detector_aperture_savings.csv so sánh deltaDr và clear-area hình học cùng nguồn/optics/PAT. Area giảm không phải mass/power/flight-time saving. Các điểm roundedD được tính trực tiếp, không lấy SKR nội suy. PAT_relaxation.csv và least_demanding_PAT.csv kiểm tra riêng jitter × centering cho các nguồn/optics đã shortlist; đây là tập không bị trội trong menu tại nguồn cố định, không phải ngưỡng PAT tối thiểu toàn cục. Threshold curves ở trên 30 cm chỉ là so sánh fixed-source; fallback optimization used={opt['fallback_used']}, các fallback diameter đã tối ưu={opt['fallback_diameters']}. 55 cm giữ làm benchmark regression, không default thiết kế UAV mới.

## Stage E — Bằng chứng khối lượng và công suất

{hardware_table}

Các reference là linh kiện/prototype rời, không phải BOM đã ghép cho A/B/C. Telescope thiên văn có obstruction/coatings và chưa được xác thực cho clear-aperture1550nm trong mô hình; khối lượng của chúng không phải lower bound cho thiết kế custom. Prototype DV-QKD drone ở656nm không chứng minh detector homodyne1550nm hoặc PAT3urad tại19–22km. Resolution3.33urad không phải closed-loop SD107urad; hai số có chức năng khác nhau.

[Hao et al.](https://arxiv.org/pdf/2101.07482) báo cáo detector efficiency95% trong một receiver phòng thí nghiệm ở1530nm, gồm photodiodeQE99% và visibility98%. Điều này hỗ trợ tính khả dĩ của high-efficiency detection nói chung, nhưng không xác thực bộη=.95/εdet=.005SNU/1550nm/bandwidth/LO/power của UAV ở đây. Không nhập protocol hoặc công thức phase-conjugate receiver của bài đó vào model. Các ví dụ calibration99.5% ở1064nm không được dùng làm bằng chứng1550nm.

FEMTO typical rail power=15(.120+.090)=3.15W, không gồm converter/optics. AD9648 two-channel chip figure=2(.106)=.212W, không gồm DAQ board, clock, FPGA hoặc transfer. RIO10–20mW là optical output, không phải điện tiêu thụ. Jetson7–25W là configurable budget; RaspberryPi15W là supply capacity, không phải operating draw. Không cộng các ví dụ khác nhau thành một hệ thống tưởng tượng. HAWK13kg/110W là whole classical terminal; không cộng thêm thành phần của nó lần nữa.

{eng_table}

P_UAV,QKD=P_optics+P_PAT+P_detector+P_LO+P_ADC+P_processing+P_control chỉ được tính khi có BOM đồng bộ và power tại cùng operating point. Hiện cả ba thiết kế cònUNKNOWN tổngmass/power; bộ xử lý/control dùng chung phải chỉ tính một lần. Receiver nhỏ hơn hoặc eta_det cao hơn không tự suy ra ít W hay nhiều W hơn. HAP optics/PAT có thể nhận thêm gánh nặng, nhưng beacon/receiver stabilization/coupling/phase/ADC/DSP trên UAV chưa được chứng minh loại bỏ được.

R_key=f_rep max(0,K), R_useful=p_avail R_key và E_bit=P_UAV,QKD/R_useful được giữ dạng công thức. Không tính số bit/s,J/bit hoặc bits/sortie vì thiếu f_rep, bandwidth/noise calibration, external availability, battery/duty/flight duration của đúng platform. ADC125MSPS không phải f_rep đã xác thực. K đã gồm AoA outage; một p_avail tương lai phải là availability ngoài mô hình, không nhân lại cùng outage. Không mượn thời gian bay từ prototype khác.

## Stage F — Robustness

{robust_table}
Giữ nguồn và mọi biến không được perturb. Các mức10/20% thay residual SD, không đổi distribution. K>=1e-4 là engineering margin, không security proof. “POSITIVE_AT_JOINT20” chỉ có nghĩa số mẫu joint20 vượt1e-4 cùng nguồn; không chứng minh mọi thời tiết/phase/pointing spectrum. Barely-positive không được gọi robust. B có thể giữ nguồn chịu perturbation tốt hơn thay vì nguồn max nominal K; source_selection ghi rõ lựa chọn.

## Q1. Receiver15–20cm có dương với detector cải thiện không?

{'Có điểm dương đã thử' if smallbest['K_raw']>0 else 'Chưa tìm thấy điểm dương trong miền/các nguồn đã thử'}. Best tested trong hai lớp15/20cm có K={smallbest['K_raw']:.12g}, Dr={smallbest['D_r']*100:g}cm, eta={smallbest['eta_det']:g}, noise={smallbest['epsilon_det']:g},div={smallbest['divergence_urad']:g}urad,jitter={smallbest['jitter_urad']:g}urad,centering={smallbest['sigma_h_m']:g}m. Không là no-key theorem ngoài catalog/domain.

## Q2. Receiver25–30cm có robust positive với PAT không quá cực đoan không?

Có {len(middle)} shortlisted positive rows dùngjitter>=3urad trong lớp25–30cm; trong đó {len(regular20)} rows cònK>=1e-4 khi cả hai residual tăng20%. Xem tableB/robustness. “Không quá cực đoan” là ưu tiên tương đối trong menu; chưa có chứng minh hardware3urad/.1m cho HAP–UAV.

## Q3. Giảmnoise.0135→.005 giúp bao nhiêu?

Giảm variance 2,7 lần. Giữ nguyên nguồn và phần cứng khác tại A/B/C: {noise_note}. isolated_parameter_impacts.csv cho deltaK cùng nguồn/optics; detector_sensitivity.csv thay đúng noise tại từng thiết kế cuối. Không thay loss vacuum, trust hoặc SNU. Tại A/B/C, noise-switch K và gap được ghi trong bảng robustness, không suy từ kết quả lịch sử khác.

## Q4. Tăngeta.8→.95 có hiệu quả hơn tăngaperture không?

Kết hợp η=.95 và εdet=.005, so với η=.8/εdet=.0135 tại cùng nguồn/optics: {aperture_saving_note}. Đây là tiết kiệm khẩu độ hình học tại hai scenario cố định, không phải mass/power saving. Đối chiếu hiệu ứng efficiency riêng với tăng aperture bằng deltaK ở Stage A và deltaDcrit cùng nguồn trong detector_aperture_savings.csv. Efficiency và receiver diameter tác động khác nhau; không áp một thứ hạng chung cho mọi điểm. Không suy chi phí điện hoặc mass từ eta_det; thiếu device-specific evidence cho cả hai.

## Q5. Receiver nhỏ nhất đã tìm được là bao nhiêu?

Sau shortlist đầu, refine_minimum.py kiểm tra thêm tối đa ba bước source/aperture cục bộ: Dr ban đầu {minimum['initial_D_m']*100:g} cm → {minimum['final_D_m']*100:g} cm. Nguồn được giữ exact trong từng root; bảng ngưỡng detector ở trên vẫn dùng nguồn chung riêng. selection_phase1/ giữ nguyên các bảng trước bước này; source_refined_minimum.json ghi bracket, nguồn và residual.

Ứng viên đã qua refinement nhỏ nhất có Dr={sel['minimum_evaluated_positive_m']*100:.6g} cm; menu chính nhỏ nhất có ứng viên dương={fmt(sel['primary_minimum_sampled_positive_m'])} m. Phân biệt với root K=0 cục bộ và điểm làm tròn để tính trực tiếp. A ở bảng đầu có nguồn và K trực tiếp; không dùng machine-epsilon-positive root probe làm thiết kế thực. A chưa đạt K≥1e-4 ở nominal.

## Q6. PAT có thể hỗ trợ trên UAV hay phải chuyển sang HAP?

Đặt thêm transmitter aperture/steering/tracking tạiHAP phù hợp hướng kiến trúc, nhưng hiệu năng còn là requirement chưa được chứng minh. Current prototype/reference data cho thấy sensor resolution, closed-loop jitter, residual centering và full19–22km link khác nhau. Chưa thể loại bỏ UAV stabilization, beacon, optical-mode/LO alignment hoặc control power mà vẫn khẳng định đạt model parameters.

## Q7. Thiết kế cân bằng tốt nhất là gì?

{balance_note} {distinct_note} Chưa có cơ sở chọn một thiết kế tối ưu năng lượng vì thiếu BOM và công suất hệ thống. A ưu tiên nhỏ hơn nhưng có margin hẹp; C là tham chiếu hiệu năng cao hơn trong menu đã thử, với receiver/PAT/detector demands ghi rõ. B/C vẫn âm khi centering tăng 10% hoặc cả hai residual tăng 10%, nên không gọi là robust.

## Q8. Nếu dưới30cm không có nghiệm, điểm đầu tiên trên30cm là gì?

Fallback optimization used={opt['fallback_used']}; diameters={opt['fallback_diameters']}. Nếuprimary đã có dương, không gọi một điểm lớn hơn là “minimum cần thiết”. Bảng threshold vẫn so sánh bốn detector scenarios fixed-source, còn40.1/55cm là matching regression/benchmark. Mọi positive chỉ là candidate model-based SKR, không certified secure-key generation hoặc hardware deployment recommendation.

## Validation, artifact và kết luận

{len(validation['checks'])} CURRENTLY_VERIFIED_PASS scoped checks, {validation['rows']} logged nodes ({validation['new_evaluations']} mới/{validation['reused_evaluations']} authenticated reuse). Baseline/regression, exact C,w/ensemble/source hash, mixed law/outage normalization, passive T support, covariance/symplectic physicality, noise once, same homodyne measurement, full-Z33/129, entropy110digits, width32/64, direct mixture/Fourier MI, half output spacing và observed convergence có receipt. Source/threshold/global/hardware/security limitations giữ nguyên.

Không sửa frozen/model/security implementation, source cache, config hoặc kết quả lịch sử. Startup bảo vệ {len(read('startup_manifest.json')['protected'])} files, ngoại trừ relevant task ledgers. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy và ObjectiveC USER_STOPPED. Không AP/training/test/heldout/publication hoặc production baseline/threshold approval.

TableA: table_A_receiver_detector.csv; TableB: table_B_positive_candidates.csv; TableC: table_C_UAV_engineering.csv; TableD: table_D_critical_receiver_thresholds.csv. Các bảng supplement ghi source comparisons, PAT Pareto, detector savings, hardware evidence và throughput/energy UNKNOWN. Tất cả figures là plot độc lập với vectorPDF và PNG350dpi; nối node chỉ giúp đọc dữ liệu, không nội suy source hay tạo optimum curve.

Các ứng viên cho biết miền dương đã thử và phần mục tiêu nhẹ/cân bằng còn chưa đạt. Xác nhận battery-powered UAV thực vẫn thiếu BOM/operating power, measured optics/PAT/detector/SNU/phase/bandwidth và security protocol evidence; không chuyển raw positive thành chứng nhận triển khai.
'''
    (OUT/'report_vi.md').write_text(body,encoding='utf-8')
    render(selected,baseline,curves,roots,sensitivity,comparisons,robust)
    print('REPORT COMPLETE',flush=True)


def render(selected,baseline,curves,roots,sensitivity,comparisons,robust):
    colors=['#0072B2','#D55E00','#009E73'];markers=['s','D','^'];checks=[]
    figdir=OUT/'figures';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':10,'legend.fontsize':7.5,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.7,'lines.linewidth':1.1})
    def start():
        fig,ax=plt.subplots(figsize=(6,4.3));ax.axhline(0,color='black',ls='--',lw=.8,label='$K=0$');return fig,ax
    def save(fig,ax,name,xlabel,rate=True):
        ax.set_xlabel(xlabel);ax.set_ylabel('Raw SKR diagnostic (bit/use)' if rate else 'Local critical receiver diameter (cm)')
        if rate:ax.set_yscale('symlog',linthresh=1e-4,base=10)
        if name in ['fig_8_robustness','fig_9_source']:ax.set_ylim(bottom=min(ax.get_ylim()[0],1.5*baseline['K_raw']))
        ax.grid(True,ls=':',alpha=.4);ax.legend(frameon=False,loc='best',fontsize=7)
        fig.text(.5,.012,'Untrusted homodyne; existing model; hardware and security unvalidated',ha='center',fontsize=7)
        fig.tight_layout(rect=[0,.045,1,1]);pdf=figdir/(name+'.pdf');png=figdir/(name+'.png')
        fig.savefig(pdf);fig.savefig(png,dpi=350);data=pdf.read_bytes()
        assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1 and b'/Subtype /Image' not in data
        with Image.open(png) as im:
            assert min(im.size)>1000 and min(im.info['dpi'])>=349
            checks.append(dict(name=name,vector_pdf=True,pages=1,pixels=list(im.size),dpi=list(im.info['dpi'])))
        plt.close(fig)
    for i,(eta,noise) in enumerate([(.8,.0135),(.95,.0135),(.8,.005),(.95,.005)],1):
        fig,ax=start()
        for j,jitter in enumerate([3.,1.561]):
            data=sorted([r for r in curves if r['eta_det']==eta and r['epsilon_det']==noise and r['jitter_urad']==jitter],key=lambda r:r['D_r'])
            ax.plot([r['D_r']*100 for r in data],[r['K_raw'] for r in data],color=colors[j],marker=markers[j],ms=4,label=f'Jitter {jitter:g} µrad; center SD 0.1 m')
        ax.axvspan(15,25,color='gray',alpha=.08);ax.axvline(30,color='gray',ls=':',lw=.8,label='Primary range ≤ 30 cm')
        ax.scatter([8],[baseline['K_raw']],color='black',marker='*',s=70,label='Original baseline (own optics/source)',zorder=7)
        ax.set_title(f'ηdet={eta:g}; εdet={noise:g} SNU; fixed common source',fontsize=10)
        save(fig,ax,f'fig_{i}_aperture','Receiver diameter (cm)')
    fig,ax=start()
    for i,r in enumerate(selected):
        data=sorted([x for x in sensitivity if x['design']==r['design'] and x['epsilon_det']==r['epsilon_det']],key=lambda x:x['eta_det'])
        ax.plot([x['eta_det'] for x in data],[x['K_raw'] for x in data],color=colors[i],marker=markers[i],ms=4,label=r['design'][0])
    ax.scatter([.8],[baseline['K_raw']],color='black',marker='*',s=70,label='Original baseline (own optics/source)')
    save(fig,ax,'fig_5_efficiency','Detector efficiency; other selected parameters fixed')
    fig,ax=start()
    for i,r in enumerate(selected):
        data=sorted([x for x in sensitivity if x['design']==r['design'] and x['eta_det']==r['eta_det']],key=lambda x:x['epsilon_det'])
        ax.plot([x['epsilon_det'] for x in data],[x['K_raw'] for x in data],color=colors[i],marker=markers[i],ms=4,label=r['design'][0])
    ax.scatter([.0135],[baseline['K_raw']],color='black',marker='*',s=70,label='Original baseline (own optics/source)')
    save(fig,ax,'fig_6_noise','Detector output excess noise (SNU)')
    fig,ax=plt.subplots(figsize=(6,4.3));corners=[(.8,.0135),(.95,.0135),(.8,.005),(.95,.005)]
    for i,jitter in enumerate([3.,1.561]):
        for target,offset,marker in [(0.,-.05,'o'),(1e-4,.05,'+')]:
            x=[];y=[]
            for j,(eta,noise) in enumerate(corners):
                r=next((r for r in roots if r['eta_det']==eta and r['epsilon_det']==noise and r['jitter_urad']==jitter and r['target_K']==target),None)
                if r:x.append(j+offset);y.append(r['D_crit_m']*100)
            ax.plot(x,y,linestyle='none',color=colors[i],marker=marker,ms=6,label=f'Jitter {jitter:g} µrad; target K={target:g}')
    ax.axhspan(15,25,color='gray',alpha=.08);ax.axhline(30,color='gray',ls=':',lw=.8,label='30 cm primary ceiling')
    ax.set_xticks(range(4),['η .8\nε .0135','η .95\nε .0135','η .8\nε .005','η .95\nε .005'])
    save(fig,ax,'fig_7_boundary','Detector scenario; common exact source / beam / geometry',rate=False)
    fig,ax=start();cases=['nominal','jitter_plus10','centering_plus10','joint_plus10','joint_plus20']
    for i,r in enumerate(selected):
        data={x['case']:x for x in robust if x['candidate']==r['candidate']}
        ax.plot(range(5),[data[x]['K_raw'] for x in cases],color=colors[i],marker=markers[i],ms=4,label=r['design'][0])
    ax.scatter([0],[baseline['K_raw']],color='black',marker='*',s=70,label='Original baseline (own optics/source)')
    ax.set_xticks(range(5),['Nominal','Jitter+10%','Center+10%','Joint+10%','Joint+20%'],rotation=15)
    save(fig,ax,'fig_8_robustness','Fixed source / optics / detector')
    fig,ax=start()
    for j,scheme in enumerate(['Uniform','Fixed_MB','Optimized_MB']):
        values=[next(x['K_raw'] for x in comparisons if x['design']==r['design'] and x['scheme']==scheme) for r in selected]
        ax.plot(np.arange(3)+(j-1)*.17,values,linestyle='none',color=colors[j],marker=markers[j],ms=6,label=scheme.replace('_',' '))
    ax.scatter(range(3),[r['K_raw'] for r in selected],color='black',marker='*',s=70,label='Selected source',zorder=7)
    ax.axhline(baseline['K_raw'],color='gray',ls=':',lw=.8,label='Original baseline (own optics/source)')
    ax.set_xticks(range(3),['A','B','C']);save(fig,ax,'fig_9_source','Same physical configuration for all three source comparisons')
    (OUT/'figure_validation.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',figures=checks),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
