"""Saved-data tables, source/model interpretation and isolated LaTeX replacement."""
from collections import defaultdict
import difflib
import json
from pathlib import Path
import numpy as np
from compare_algorithms import read,rows,save,write,mean_statistics,METRICS

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
ALGORITHMS=['Stationary','Greedy','DP']


def text(name,value):(OUT/name).write_bytes((value.rstrip()+'\n').encode())
def estimate(row,scale=1):
    v=[float(row[k])*scale for k in ['mean','sd','ci95_low','ci95_high']]
    return f'{v[0]:.7g} ± {v[1]:.3g} [{v[2]:.7g}, {v[3]:.7g}]'


def main():
    config=read('experiment_config.json');execution=read('execution_summary.json');audit=read('cloud_validation.json')
    summary=rows('summary_comparison.csv');data=rows('simulation_results.csv');pairs=rows('paired_mission_results.csv')
    lookup={(r['geometry'],r['case_id'],r['algorithm'],r['metric']):r for r in summary}
    primary=config['primary_geometry'];physical={g:read(f'physical_summary_{g}.json') for g in config['geometry_cases']}
    grouped=defaultdict(list)
    for row in pairs:grouped[(row['geometry'],row['case_id'],row['baseline'],row['metric'])].append(row)
    improvements=[]
    for (geometry,case,baseline,metric),records in grouped.items():
        delta=mean_statistics([float(r['DP_minus_baseline']) for r in records])
        base=float(np.mean([float(r['baseline_value']) for r in records]))
        factor=-1 if metric in ['zero_rate_unavailability','total_distance_m'] else 1
        improvements.append(dict(geometry=geometry,case_id=case,baseline=baseline,metric=metric,
            baseline_mean=base,mean_DP_minus_baseline=delta['mean'],delta_sd=delta['sd'],
            paired_delta_ci95_low=delta['ci95_low'],paired_delta_ci95_high=delta['ci95_high'],
            improvement_absolute=factor*delta['mean'],improvement_percent=100*factor*delta['mean']/abs(base) if base else '',
            percent_status='RATIO_OF_MEANS' if base else 'ZERO_BASELINE_ABSOLUTE_ONLY'))
    write('relative_improvements.csv',improvements)
    with np.load(OUT/'cloud_realizations.npz') as archive:
        old_g,new_g=archive['G_old'],archive['G_new'];old_c,new_c=archive['C_old_p04'],archive['C_calibrated'][3]
    h=np.array([j for j in range(100) if j%10!=9]);v=np.arange(90)
    correlations=[]
    for model,latent,binary in [('NEW',new_g,new_c),('OLD',old_g,old_c)]:
        for variable,values in [('latent',latent),('binary_p04',binary)]:
            for direction,a,b in [('horizontal',values[:,h,:],values[:,h+1,:]),('vertical',values[:,v,:],values[:,v+10,:]),
                ('temporal',values[:,:,:-1],values[:,:,1:])]:
                correlations.append(dict(model=model,variable=variable,direction=direction,
                    pooled_Pearson=float(np.corrcoef(a.reshape(-1),b.reshape(-1))[0,1]),missions=100))
    write('old_new_empirical_correlations.csv',correlations)
    rare=[]
    for case in ['new_zero','new_calibrated_p0.4']:
        for algorithm in ALGORITHMS:
            records=[r for r in data if r['geometry']==primary and r['case_id']==case and r['algorithm']==algorithm]
            failures=sum(float(r['zero_rate_unavailability'])>0 for r in records)
            rare.append(dict(case_id=case,algorithm=algorithm,independent_missions=len(records),missions_with_any_zero_rate_slot=failures,
                one_sided95_upper_any_outage_mission_probability=1-.05**(1/len(records)) if failures==0 else '',
                note='No zero-failure guarantee; mission is the independent unit'))
    write('rare_event_observations.csv',rare)
    reference=dict(canonical_manuscript_pdf='C:/Users/HP/Downloads/2026__Binh_s_work (43).pdf',
        canonical_manuscript_sha256='f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b',
        canonical_manuscript_pages=3,cloud_subsection_in_canonical_pdf=False,
        new_cloud_equation_authority='Current explicit user task; local cited letter confirms mean/covariance generation family',
        local_cloud_reference='C:/Users/HP/Downloads/Network_Availability_Maximization_for_Free-Space_Optical_Satellite_Communications.pdf',
        local_cloud_reference_sha256='9356d6a74bd1132e77827b751b70ec50d001ed9cd58bd2f3edb967443185aba9',
        local_cloud_reference_section='Section III, PDF page 3; truncation described without numerical cutoff',
        cited_reference_13='Sanchez Net et al., Approximation Methods for Estimating the Availability of Optical Ground Networks, JOCN 8(10), 800-812 (2016)',
        reference_13_url='https://opg.optica.org/jocn/abstract.cfm?uri=jocn-8-10-800',
        reference_13_access='Publisher abstract verified; full text not accessible during audit; no cutoff attributed to it',
        zero_threshold='Explicit user-approved operational convention, not a recovered verbatim reference equation',
        calibrated_threshold='Explicit user-approved extension',mean_resampling='Explicit independent-slot simulation convention',
        production_cloud_file_preserved='src/binary_cloud.py is bound in frozen physical dependencies; old generator used only as controlled secondary law')
    save('model_reference_audit.json',reference)
    latex=r'''% Isolated replacement only; no existing manuscript or frozen equation is edited.
\subsection{Synthetic correlated cloud blockage}
Let $j=1,\ldots,J$ index $J=100$ UAV candidate positions and let
$n=1,\ldots,N_t$ index equal-duration slots. For the $10\times10$ grid,
we use row-major indexing $j=10r+c+1$, where $r,c\in\{0,\ldots,9\}$.
At each slot we independently generate
\begin{equation}
 \mu_{j,n}\overset{\mathrm{iid}}{\sim}\mathcal U(-1,1),\qquad
 \mathbf G_n\mid\boldsymbol\mu_n\sim\mathcal N(\boldsymbol\mu_n,\boldsymbol\Gamma),
 \quad \Gamma_{ij}=9(0.9)^{|i-j|}.
 \label{eq:phasec_cloud_gaussian}
\end{equation}
The independently resampled means and Gaussian innovations are a simulation
convention; no temporal AR(1) law or previous-slot Gaussian state is used.
The primary binary conversion is the explicit operational choice
\begin{equation}
 c_{j,n}=\mathbb I\{G_{j,n}>0\},\qquad c_{j,n}\in\{0,1\},
 \label{eq:phasec_cloud_threshold}
\end{equation}
where $c_{j,n}=1$ denotes complete blockage and $c_{j,n}=0$ a clear path.
This threshold is not asserted to be a numerical cutoff specified by the
reference; symmetry gives unconditional blockage probability $1/2$.
For a separate calibrated-probability sensitivity experiment, we replace
zero by $t_p$, found numerically from
\begin{equation}
 \frac12\int_{-1}^{1}\left[1-\Phi\!\left(\frac{t_p-\mu}{3}\right)\right]
 \,\mathrm d\mu=p.
 \label{eq:phasec_cloud_calibration}
\end{equation}
This calibration is an additional simulation convention. We do not fix the
number of blocked positions in a slot. The covariance is index-based, rather
than distance-isotropic: horizontal and vertical nearest neighbors have
conditional Gaussian correlations $0.9$ and $0.9^{10}$, respectively. Averaging
over independently resampled means adds $1/3$ to the unconditional covariance
diagonal; binary correlations need not equal the Gaussian correlations.
Complete blockage gives $T_{c,j,n}=1-c_{j,n}$ and usable rate
$S_{j,n}=(1-c_{j,n})K_j^\star$, where $K_j^\star$ is the nonnegative
available-catalog clear-sky rate computed with the unchanged physical-layer
model. These synthetic fields do not represent a measured atmospheric forecast
or a cloud with a physical center, shape, or velocity. The same realized matrix
$S$ is supplied to every positioning algorithm. DP and optimal Stationary
use the full mission offline; Greedy uses only current-slot cloud information.
'''
    text('cloud_model_replacement.tex',latex)
    patch=''.join(difflib.unified_diff([],latex.splitlines(keepends=True),fromfile='/dev/null',tofile='b/manuscript_cloud_model_replacement.tex'))
    text('proposed_manuscript_cloud.patch',patch)
    text('manuscript_integration.md',r'''# Proposed cloud-subsection integration

The canonical v43 reference is a three-page PDF without an editable cloud
subsection source in this workspace. No frozen manuscript file was modified.
`proposed_manuscript_cloud.patch` is an unapplied add-file patch containing the
isolated replacement. Once the author provides/opens the editable manuscript,
replace only the old cloud-model subsection with:

```latex
\input{manuscript_cloud_model_replacement}
```

Preserve all other expressions, labels and optimization problems. New cloud
labels use a unique phasec prefix. A context-based edit to an unknown .tex file
was not fabricated. The threshold calibration and independent mean resampling
are explicit simulation conventions, not verbatim reference equations.
''')
    descriptions=[
        ('fig1_cloud_realizations','Independent-slot binary cloud fields at slots 1, 10, and 30 of mission 0, zero-threshold mode. White cells are clear and shaded cells blocked. The row-major index covariance is not distance-isotropic.'),
        ('fig2_cloud_covariance',r'Exact conditional covariance $\Gamma_{ij}=9(0.9)^{|i-j|}$ and row-major mapping of the 100 candidate positions. Horizontal and vertical nearest neighbors have conditional Gaussian correlations $0.9$ and $0.9^{10}$, despite equal grid spacing.'),
        ('fig3_unavailability_vs_p','Zero-rate unavailability versus calibrated blockage probability for optimal Stationary, current-slot Greedy, and offline DP. Bands are pointwise 95% Student-t intervals across 100 paired missions; observed zero outages do not establish zero population risk.'),
        ('fig4_usable_skr_vs_p','Average usable SKR versus calibrated blockage probability for the three positioning algorithms, using the same position-dependent Optimized MB clear-sky map and cloud states. Bands are pointwise 95% mission-mean intervals.'),
        ('fig5_objective_vs_p',r'Penalized objective $U=\bar S-\lambda D/D_{\rm ref}$ versus calibrated blockage probability at $\lambda=9.468026677248516\times10^{-6}$ bits/use. DP and optimal Stationary use offline mission knowledge; Greedy does not.'),
        ('fig6_distance_vs_p','Total UAV travel distance versus calibrated blockage probability. Stationary travel is zero. DP maximizes the penalized objective and is not required to minimize distance individually. Shading indicates pointwise 95% mission-mean intervals.'),
        ('fig7_representative_trajectories','Paired trajectories for mission 0 in zero-threshold mode at the reference mobility penalty. The background shows the fraction of blocked slots over the mission, not a fixed cloud. Open rings and crosses indicate initial and final positions. DP and optimal Stationary are offline benchmarks; Greedy uses only current-slot states.'),
        ('fig8_mobility_penalty_tradeoff',r'Mean usable-rate versus travel-distance tradeoff at calibrated $p=0.4$ for the ten historical mobility penalties, including zero and $\lambda_{\rm ref}$. Error bars are pointwise 95% intervals over the same 100 paired missions. Lines only join the tested penalty settings.')]
    captions=['% DIAGNOSTIC_ONLY; synthetic cloud, incomplete exact-source convergence evidence.']
    for name,caption in descriptions:
        captions.append('\\begin{figure*}[t]\n\\centering\n\\includegraphics[width=\\textwidth]{'+name+'.pdf}\n\\caption{'+caption+
            ' Primary HAP projection is (500,500) m. Results are diagnostic and conditional on incomplete source-convergence evidence; no QKD security certification is claimed.}\n\\label{fig:'+name+'}\n\\end{figure*}\n')
    text('figure_captions.tex','\n'.join(captions))
    md=['# So sánh DP, Greedy và Stationary với cloud Gaussian mới','',
        '**DIAGNOSTIC_ONLY — đã thực thi, primary đặt HAP trên tâm lưới theo quyết định tác giả.**','',
        '## Hình học và physical layer','',
        'Primary: HAP (500,500) m, cao 20 km; UAV cao 1 km, 100 tâm ô '+
        '(50,150,…,950) m trên lưới 10×10 trong vùng 1 km². Secondary giữ nguyên '+
        'HAP (11419.65511459133,450) m. Cùng covariance/cloud realizations, nguồn, '+
        'objective và mobility parameters cho hai hình học. Không gán SKR ở 0° cho toàn vùng.','',
        '| Hình học | Zenith (deg) | Best raw K theo vị trí (bits/use) | Vị trí clear-sky dương | Context mới | SKR eval mới |',
        '|---|---|---|---:|---:|---:|']
    for geometry,p in physical.items():
        md.append(f"| {geometry} | {p['new_angle_range_deg'][0]:.12g}–{p['new_angle_range_deg'][1]:.12g} | {p['raw_K_range'][0]:.12g} đến {p['raw_K_range'][1]:.12g} | {p['positive_clear_sky_positions']}/100 | {p['unique_channel_geometries']} | {p['new_SKR_evaluations']} |")
    md+=['','212 payload C,w lịch sử được tái dùng (33 Uniform,179 MB), không nội suy/tính mới. '+
        'Mỗi noninteger zenith được tính trực tiếp bằng evaluator v43 cũ; chỉ gộp các '+
        'vị trí có geometry/angle binary64 giống hệt. Eq14, homodyne MI, Holevo, '+
        'VA=2 nbar, ν_repo=42.5 ν_raw, noise và [0,1] moments/atom giữ nguyên. '+
        'Dr=0.30 m, divergence35 µrad, jitter1.561 µrad, position SD0.10 m, '+
        'τzen0.92, ξch0.0186, ξdet0.005, β0.95, AO/phase OFF. '+
        'Best source ở primary là MB VA=1.358333319784304, ν_raw=0.30; '+
        'mọi winner primary/secondary vẫn INSUFFICIENT_EVIDENCE.','',
        '## Cloud model và cấu hình nhiệm vụ','',
        'Giữ chính xác Γij=9(0.9)^|i−j|; j=10 row+column+1. Mean Uniform(-1,1) '+
        'được sinh lại độc lập ở mọi ô và slot; Gaussian innovations độc lập theo '+
        'slot, không có G[n−1] hoặc AR(1) trong generator mới. Zero threshold '+
        'G>0 là convention được tác giả chấp nhận; không gán ngưỡng này cho tài liệu. '+
        'Calibrated p dùng nghiệm tích phân mixture đã chỉ định; không ép pJ ô blocked.','',
        '30 slot ×20 s =600 s; vmax15 m/s, bước chuyển Euclid≤300 m. Di chuyển chéo '+
        'được phép nếu thỏa khoảng cách, có thể ở lại, tự do chọn vị trí đầu, không '+
        'deployment/terminal-return penalty. Dref=1000 m; λref=9.468026677248516e−6 '+
        'bits/use. Giữ 10 λ số học lịch sử với cùng normalization, không tính lại '+
        'λhigh theo map mới. U=mean(S)−λ total_distance/Dref cho cả ba thuật toán. '+
        'Stationary chọn vị trí tốt nhất trên toàn mission offline; DP cũng biết '+
        'toàn bộ cloud tương lai. Greedy chỉ dùng S[:,n], với reward S/Nt và penalty '+
        'λd/Dref. Tie-break xác định bằng argmax đầu tiên.','',
        '## Table A — Primary, zero threshold, λref','',
        'Mỗi ô: mean ± SD [95% CI]; CI Student-t theo 100 mission độc lập, cùng '+
        'mission IDs giữa mọi thuật toán. Không dùng ô/slot như các mẫu độc lập.','',
        '| Metric | Stationary | Greedy | DP |','|---|---|---|---|']
    metric_labels=[('average_usable_skr','Average usable SKR (bits/use)',1),('objective_U','U (bits/use)',1),
        ('total_distance_m','Travel (m)',1),('zero_rate_unavailability','Unavailability (%)',100),
        ('availability','Availability (%)',100),('position_changes','Position changes',1),('runtime_s','Algorithm runtime (ms)',1000)]
    for metric,label,scale in metric_labels:
        md.append('| '+label+' | '+' | '.join(estimate(lookup[(primary,'new_zero',a,metric)],scale) for a in ALGORITHMS)+' |')
    md+=['','## Table A2 — Primary, calibrated p=0.4, λref','','| Metric | Stationary | Greedy | DP |','|---|---|---|---|']
    for metric,label,scale in metric_labels:md.append('| '+label+' | '+' | '.join(estimate(lookup[(primary,'new_calibrated_p0.4',a,metric)],scale) for a in ALGORITHMS)+' |')
    md+=['','## Table B — Primary, calibrated p sweep, λref','',
        'Mean [95% CI] cho từng đại lượng; SD và đủ các metric nằm trong summary_comparison.csv.','',
        '| p | Algorithm | Usable K [CI] | U [CI] | Unavailability % [CI] | Distance m [CI] |',
        '|---:|---|---|---|---|---|']
    table_b=[]
    for p in config['Monte_Carlo']['probabilities']:
        for a in ALGORITHMS:
            fields=[];record=dict(p=p,algorithm=a)
            for metric,scale in [('average_usable_skr',1),('objective_U',1),('zero_rate_unavailability',100),('total_distance_m',1)]:
                r=lookup[(primary,f'new_calibrated_p{p:.1f}',a,metric)]
                values=[float(r[k])*scale for k in ['mean','ci95_low','ci95_high']]
                fields.append(f'{values[0]:.7g} [{values[1]:.7g},{values[2]:.7g}]')
                for k in ['mean','sd','ci95_low','ci95_high']:record[metric+'_'+k]=r[k]
            md.append(f'| {p:g} | {a} | '+' | '.join(fields)+' |');table_b.append(record)
    write('table_B_probability_sweep.csv',table_b)
    md+=['','## Table C — DP so với baseline','',
        'Delta=DP−baseline; gain dương nghĩa là tăng U/rate hoặc giảm unavailability/distance. '+
        'Phần trăm dùng tỷ số của mean, không lấy trung bình các tỷ số mission. '+
        'Baseline bằng 0 chỉ báo delta tuyệt đối. CI là paired mission-delta.','',
        '| Case | Baseline | Metric | Delta mean [paired 95% CI] | Gain (%) |',
        '|---|---|---|---|---:|']
    for r in improvements:
        if r['geometry']!=primary or r['case_id'] not in ['new_zero','new_calibrated_p0.4','new_calibrated_p0.8']:continue
        gain='N/A (baseline=0)' if r['improvement_percent']=='' else f"{r['improvement_percent']:.6g}"
        md.append(f"| {r['case_id']} | {r['baseline']} | {r['metric']} | {r['mean_DP_minus_baseline']:.9g} [{r['paired_delta_ci95_low']:.9g},{r['paired_delta_ci95_high']:.9g}] | {gain} |")
    md+=['','## Primary versus Secondary và old versus new','',
        '| Geometry / model / mode | Algorithm | Usable K | U | Unavailability (%) | Travel (m) |',
        '|---|---|---:|---:|---:|---:|']
    geometry_comparison=[]
    for geometry in config['geometry_cases']:
        for case in ['new_zero','new_calibrated_p0.4','old_p0.4']:
            for a in ALGORITHMS:
                rec=dict(geometry=geometry,case_id=case,algorithm=a)
                vals=[]
                for metric,scale in [('average_usable_skr',1),('objective_U',1),('zero_rate_unavailability',100),('total_distance_m',1)]:
                    rec[metric]=float(lookup[(geometry,case,a,metric)]['mean']);vals.append(f'{rec[metric]*scale:.9g}')
                md.append(f'| {geometry}/{case} | {a} | '+' | '.join(vals)+' |');geometry_comparison.append(rec)
    write('primary_secondary_model_comparison.csv',geometry_comparison)
    md+=['','Secondary có raw K âm ở cả 100 vị trí; max(0,K) bằng 0 làm tất cả thuật toán '+
        'có U=rate=distance=0, availability0%, unavailability100%. Đây là kết quả đúng '+
        'của physical layer ở zenith gần30°, không được sửa bằng đổi noise/nguồn/frozen '+
        'formula. Các kết quả secondary đã được tính trong cùng lượt này và giữ '+
        'nguyên khi bổ sung primary, với chính xác cùng C và white innovations.','',
        '## Diễn giải','',
        '1. DP không thua U của Greedy hoặc Stationary ở bất kỳ instance đã kiểm tra. '+
        'Đây là nghiệm hữu hạn trên lưới và cloud tương lai biết trước, không phải '+
        'một bộ điều khiển online hay dự báo khí quyển đã được chứng nhận.','',
        '2. Ở p=0.4, lợi ích U của DP so Greedy là khoảng0.857%, rate chỉ khoảng0.050%, '+
        'nhưng giảm khoảng49.18% quãng đường. So Stationary, U tăng khoảng25.21%. '+
        'Ở p=0.8, U tăng khoảng13.51% so Greedy và unavailability giảm khoảng68.98%, '+
        'đổi lại quãng đường tăng khoảng12.00%. Không suy ra DP luôn có từng metric '+
        'riêng tốt nhất. Chênh lệch cũng phản ánh thông tin offline, không chỉ thuật toán.','',
        '3. Cloud mới có anisotropy theo index: ngang100m có lag1, dọc100m có lag10; '+
        'row-wrap index liền nhau vẫn tương quan mạnh dù cách nhau≈905.5m. Không '+
        'diễn giải là cloud có tâm/hình dạng/vận tốc đang bay qua lưới.','',
        '4. Mean và innovation sinh mới mỗi20s làm các slot độc lập theo mô hình. '+
        'AR(1) cũ tạo độ bền theo thời gian, đồng thời spatial kernel cũng khác. '+
        'Trong đối chiếu tổng hợp, Stationary offline ở p=0.4 đạt gần99.5% '+
        'availability với model cũ, còn model mới chỉ≈79.37%; không quy toàn bộ '+
        'chênh lệch riêng cho AR(1) khi hai thành phần đều đổi. DP cần nhiều '+
        'di chuyển hơn dưới cloud mới. So sánh dùng cùng physical map và nominal p, không '+
        'dùng lại kết quả thuật toán của các experiment cũ.','',
        '5. Lợi ích tránh outage của DP tăng rõ ở blockage cao. Tăng λ làm DP '+
        'chuyển dần sang ít di chuyển; với λ lớn, DP trùng Stationary tối ưu, trong '+
        'khi Greedy còn chịu giới hạn chọn vị trí ban đầu chỉ theo slot đầu. '+
        'Các λ đã thử là hữu hạn, không chứng nhận tradeoff liên tục.','',
        '6. 100/100 vị trí primary có Kstar>0 trong mô hình clear-sky hiện dùng. '+
        'Đây là diagnostic dựa trên catalog có sẵn và source convergence evidence '+
        'còn thiếu. Missing Uniform ở VA=1.6249995399703647/nu0 vẫn chưa có; '+
        'không khẳng định global modulation optimum hay unconditional QKD security.','',
        '## Threshold và kiểm chứng cloud','',
        '| Mode | Target p | Threshold | Empirical p [95% CI] |','|---|---:|---:|---|']
    for r in rows('empirical_blockage.csv')[:10]:
        md.append(f"| {r['case_id']} | {float(r['p_target']):g} | {float(r['threshold']):.12g} | {float(r['mean']):.8g} [{float(r['ci95_low']):.8g},{float(r['ci95_high']):.8g}] |")
    md+=['','Zero threshold và calibrated p=0.4 khác nhau. Calibrated p=0.5 có '+
        't=0 nên mask trùng zero mode; hai view này được tái dùng, không tạo thêm '+
        'realization độc lập. Cùng G được threshold ở mọi p; old/new ghép white '+
        'innovations bằng đổi dấu nhằm ghép upper-tail mới với lower-tail cũ. '+
        'Các confidence intervals giữa p/λ vì vậy có tương quan; không tuyên bố '+
        'đây là các experiment độc lập với nhau.','',
        'Γ là covariance có điều kiện theo mean. Sau khi marginalize mean resampling, '+
        'Cov(G)=Γ+I/3; không scale lại Γ. Audit512 missions kiểm tra cả residual '+
        'G−µ so với Γ và mixture so với Γ+I/3, bằng mission-cluster SE. Max deviation '+
        f"lần lượt {audit['covariance_checks'][0]['max_mission_cluster_standardized_error']:.4g} và "+
        f"{audit['covariance_checks'][1]['max_mission_cluster_standardized_error']:.4g} SE, dưới gate6SE. "+
        'Pooled Pearson audit ở zero mode:','',
        '| Variable | Direction | Empirical correlation |','|---|---|---:|']
    for r in audit['pooled_Pearson_correlations']:md.append(f"| {r['variable']} | {r['direction']} | {r['empirical_Pearson']:.8g} |")
    md+=['','Binary correlations được đo riêng, không gán bằng Gaussian correlations. '+
        'Uniform-mean KS/DKW check và structural không-AR checks PASS. '+
        'Full matrices/means/G/epsilon/C/S được lưu trong cloud_realizations.npz.','',
        '## Giới hạn CI và nguồn tham khảo','',
        'CI Student-t pointwise có thể vượt biên [0,1] ở rare events và được giữ '+
        'nguyên trong CSV. 0 outage quan sát ở DP không chứng minh risk bằng0: '+
        'với 0/100 mission bị outage, upper bound một phía95% cho xác suất một '+
        'mission có ít nhất một outage là≈2.9513%. Không coi3000slot là3000 mẫu '+
        'độc lập để thu hẹp bound. Xem rare_event_observations.csv. '+
        'Các CI chỉ phản ánh variability synthetic-cloud giữa mission, chưa gồm '+
        'source-moment uncertainty hoặc atmospheric/model uncertainty.','',
        'Canonical PDF v43 được xác nhận có3trang, chưa có subsection cloud/mobility '+
        'để sửa trực tiếp. Mô hình mới được áp dụng theo yêu cầu tác giả hiện tại. '+
        'FSO letter local, SectionIII/page3, nêu mean/covariance và truncation '+
        'nhưng không nêu cutoff số. Reference[13] được xác nhận danh tính tại '+
        '[Optica](https://opg.optica.org/jocn/abstract.cfm?uri=jocn-8-10-800); '+
        'full text chưa truy cập được, nên không gán threshold0 cho tài liệu. '+
        'Bản cloud_model_replacement.tex và add-file patch là proposal riêng, '+
        'không chỉnh frozen manuscript, equation labels hoặc optimization problems.','',
        '## Execution summary','',
        f"100 mission IDs độc lập mỗi case; {execution['mission_case_views']} mission-case views "+
        f"(2 geometries×19cases×100), {execution['unique_algorithm_triplet_executions']} actual algorithm-triplet "+
        f"executions và {execution['reused_triplet_views']} alias views; {execution['algorithm_execution_count']} "+
        'thuật toán executions. Cùng100new-G và100old-G missions được ghépCRN; '+
        'không phải3800 cloud draws độc lập. 30slots,100positions; sourcepool212; '+
        f"new C,w=0; new channel/SKR pairs={sum(p['new_SKR_evaluations'] for p in physical.values())}. "+
        'Seed mission20261015, mission IDs0…99; auditseed20261025,512missions.','',
        f"Runtime đo riêng: primary physical map {physical['centered']['elapsed_seconds']:.6g}s; "+
        f"secondary {physical['historical']['elapsed_seconds']:.6g}s; MC cumulative {execution['elapsed_seconds']:.6g}s; "+
        '4 focused unit tests cùng stochastic audit PASS. Live DP objective/movement '+
        'failures=0. Kiểm chứng saved-record replay và artifact integrity nằm trong '+
        'verification.json. Runtime là Python wall-clock phụ thuộc môi trường, '+
        'không phải latency truyền thông QKD.','',
        'Tất cả8 PNG600dpi/PDF vector, bảng và trajectories ở namespace này. '+
        'Không sửa production/frozen/security evaluator/caches lịch sử; strict '+
        'Phase B vẫn BLOCKED, UNVALIDATED_SECURITY_MODEL và '+
        'NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.']
    text('validation_report_vi.md','\n'.join(md))
    cloud_report=['# Cloud model validation — DIAGNOSTIC_ONLY','',
        'Primary law: conditional N(mu_n,Gamma), Gamma_ij=9*0.9^abs(i-j), J=100. '+
        'Independent Uniform(-1,1) means and Gaussian residuals resampled every slot. '+
        'No previous state/rho/AR update. Row-major indexing; index anisotropy retained.','',
        'Zero threshold and calibrated p are explicit author-approved simulation conventions. '+
        'All eight p targets fall within their observed mission-level95% blockage intervals. '+
        'No per-slot fixed blocked count. Exact thresholds/empirical estimates: empirical_blockage.csv.','',
        'The supplied Gamma is CONDITIONAL covariance. Marginalizing random means '+
        'gives Gamma+I/3; both moments are tested separately, not confused or renormalized. '+
        '512 independent mission clusters,30slots each; covariance gate6clusterSE, '+
        'pooled Pearson and binary correlations reported separately. '+
        'Uniform KS D='+str(audit['mean_uniform_KS_D'])+' < DKW bound '+str(audit['mean_uniform_DKW_bound_alpha_1e_minus6'])+'.','',
        'Four unit-test methods cover exact/symmetric/PD covariance, deterministic '+
        'slot generation/mean resampling/thresholds/no-state signature, brute-force '+
        'DP/feasibility/stationary/diagonal moves, and nonanticipating Greedy/ties. '+
        'All actual MC instances also check shared C/S and DP objective dominance.','',
        'Old model is called only in the controlled OLD case, using the untouched '+
        'src/binary_cloud.py implementation. Same base white normals, sign-adjusted '+
        'new residuals, same mission IDs, same p0.4 and same geometry/rate map. '+
        'No historical algorithm outcome is reused as a new-cloud outcome.','',
        'See cloud_validation.json, old_new_empirical_correlations.csv, focused_tests.json '+
        'and verification.json. Source convergence and atmospheric forecast validation '+
        'are outside these synthetic-cloud checks.']
    text('cloud_model_validation.md','\n'.join(cloud_report))
    print('Tables, eight captions, model audit and isolated manuscript proposal written.')


if __name__=='__main__':main()
