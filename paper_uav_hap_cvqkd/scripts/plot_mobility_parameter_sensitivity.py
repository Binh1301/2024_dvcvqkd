"""Six Stage A figures and quantitative reports from saved CSVs; no solvers."""
from pathlib import Path
import argparse
import csv
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FixedLocator, ScalarFormatter
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
METHODS=('Stationary','Greedy','DP')
LABELS={'Stationary':'Stationary (P2)','Greedy':'Greedy','DP':'Dynamic Programming (P3)'}
STYLE={'Stationary':dict(color='tab:blue',linestyle='-',marker='o'),
       'Greedy':dict(color='tab:orange',linestyle='--',marker='s'),
       'DP':dict(color='tab:red',linestyle='-',marker='^')}
NAMES=('fig_A1_positions_objective_skr','fig_A2_positions_unavailability','fig_B_speed_sensitivity',
       'fig_C_cloud_probability_sensitivity','fig_D_duration_sensitivity','fig_E_spatial_correlation_sensitivity')
LAM=9.468026677248516e-6
AXIS_LABELS={'J':'Candidate positions J','speed':'UAV speed limit\n(m/s)','horizon':'Number of time slots',
             'probability':'Cloud-blockage\nprobability','spatial':'Correlation length\n(m; log scale)'}
AXIS_VI={'J':'số vị trí J','speed':'tốc độ tối đa','horizon':'số slot','probability':'xác suất chặn','spatial':'chiều dài tương quan không gian'}


def js(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,data):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
def save_json(path,data):Path(path).write_bytes((json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
def numeric(row):
    return {k:(v if k in ('case_id','method','baseline','metric','ratio_status') else (None if v=='' else float(v))) for k,v in row.items()}
def fmt(v):return 'NA' if v is None else f'{float(v):.8g}'


def load(out):
    require=js(out/'validation/aggregate.json')
    if require['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Aggregate gate failed')
    for name,digest in require['artifact_sha256'].items():
        if sha(out/name)!=digest:raise ValueError('Aggregate artifact changed: '+name)
    p=js(out/'protocol.json');summary=[numeric(r) for r in rows(out/'existing_data/aggregate_statistics.csv')]
    paired=[numeric(r) for r in rows(out/'existing_data/paired_improvements.csv')]
    return p,{(r['case_id'],int(r['lambda_index']),r['method']):r for r in summary},\
           {(r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in paired}


def render(out,protocol,summary,paired):
    folder=out/'existing_data/figures';points=[];metadata={};layout_issues=[]
    def members(axis):return sorted([r for r in protocol['memberships'] if r['axis']==axis],key=lambda r:r['value'])
    def setup(count):
        fig,axs=plt.subplots(1,count,figsize=(7.2,3.25),squeeze=False)
        fig.subplots_adjust(left=.105,right=.985,bottom=.25,top=.77,wspace=.72 if count==3 else .38)
        for ax in axs[0]:
            ax.set_axisbelow(True);ax.minorticks_on();ax.grid(which='major',color='.83',lw=.5);ax.grid(which='minor',color='.94',lw=.35)
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        return fig,list(axs[0])
    def configure(ax,axis,metric,title):
        ax.set_xlabel(AXIS_LABELS[axis]);ax.set_title(title,fontsize=9,pad=7)
        label={'K':'Mean usable SKR\n(bits/use)','U':'Mean objective U\n(bits/use)','D':'Mean travel distance\n(m)',
               'availability':'Nonzero-SKR availability\n(%)','unavailability_percent':'Zero-SKR unavailability\n(%)',
               'gain_percent':'DP gain in mean U\n(%)','gain_absolute':'Mean DP objective gain\n(bits/use)'}[metric]
        ax.set_ylabel(label,labelpad=3)
        if metric in ('K','U','gain_absolute'):
            sf=ScalarFormatter(useMathText=True);sf.set_powerlimits((0,0));sf.set_useOffset(False);ax.yaxis.set_major_formatter(sf)
        vals=[m['value'] for m in members(axis)]
        ticks=[0,5,10,15,20,25] if axis=='speed' else vals
        if axis=='spatial':
            ax.set_xscale('log');ax.set_xticks(vals);ax.set_xticklabels([str(v) for v in vals])
            ax.xaxis.set_minor_locator(FixedLocator([np.sqrt(a*b) for a,b in zip(vals,vals[1:])]))
            ax.set_xlim(min(vals)/1.15,max(vals)*1.15)
        else:
            ax.set_xticks(ticks);ax.xaxis.set_minor_locator(FixedLocator([(a+b)/2 for a,b in zip(ticks,ticks[1:])]))
            span=max(vals)-min(vals);ax.set_xlim(min(vals)-.045*span,max(vals)+.045*span)
        if axis=='J':
            ax.tick_params(axis='x',labelrotation=35,labelsize=7.5)
            plt.setp(ax.get_xticklabels(),ha='right')
    def draw(name,panel,ax,axis,key,method,li=1,base=None,zero_style=False):
        mm=members(axis);x=np.array([r['value'] for r in mm],float);y=[];low=[];high=[]
        for member in mm:
            if base is None:
                row=summary[member['case_id'],li,method];scale=100 if key=='availability' else 1
                y.append(row[key+'_mean']*scale);low.append(row[key+'_ci95_low']*scale);high.append(row[key+'_ci95_high']*scale)
            else:
                row=paired[member['case_id'],li,base,'U']
                if key=='gain_percent':y.append(row['ratio_of_means_percent']);low.append(row['ratio_ci95_low']);high.append(row['ratio_ci95_high'])
                else:y.append(row['mean']);low.append(row['ci95_low']);high.append(row['ci95_high'])
        label=LABELS[method] if base is None else 'DP minus '+('P2' if base=='Stationary' else 'Greedy')
        style=dict(STYLE[method] if base is None else STYLE[base])
        if zero_style:
            style.update(linestyle=':' if method=='Greedy' else '-.',marker='v' if method=='Greedy' else 'D')
        if name==NAMES[2] and method!='Stationary':label=('Greedy' if method=='Greedy' else 'DP')+(', λ=0' if li==0 else ', λref')
        yy=np.array([np.nan if v is None else v for v in y]);lo=np.array([np.nan if v is None else v for v in low]);hi=np.array([np.nan if v is None else v for v in high])
        line=ax.plot(x,yy,**style,lw=2.1,ms=5.5,mfc='white',mew=1.1,label=label)[0]
        ax.fill_between(x,lo,hi,color=style['color'],alpha=.08,lw=0)
        for i,(vx,vy) in enumerate(zip(line.get_xdata(),line.get_ydata())):
            points.append(dict(figure=name,panel=panel,axis=axis,case_id=mm[i]['case_id'],lambda_index=li,lambda_bits_per_use=(0 if li==0 else LAM),
                method=method,baseline=base or '',metric=key,curve=label,point_index=i,x=float(vx),y=None if not np.isfinite(vy) else float(vy),
                ci95_low=None if not np.isfinite(lo[i]) else float(lo[i]),ci95_high=None if not np.isfinite(hi[i]) else float(hi[i]),
                source='paired_improvements.csv' if base else 'aggregate_statistics.csv',color=style['color'],linestyle=style['linestyle'],marker=style['marker']))
        return line
    def finish(fig,axs,name,gain=False):
        for ax in axs:
            finite=[]
            for line in ax.lines:finite.extend(np.asarray(line.get_ydata())[np.isfinite(line.get_ydata())].tolist())
            # Keep zero and every unmodified confidence bound; no truncated performance zoom.
            relevant=[r for r in points if r['figure']==name and r['panel']==axs.index(ax)+1]
            bounds=[float(v) for r in relevant for v in (r['y'],r['ci95_low'],r['ci95_high']) if v is not None]
            lower=min(0.,min(bounds));upper=max(bounds);span=max(upper-lower,1e-12)
            ax.set_ylim(lower-.045*span,upper+.14*span)
        handles,labels=axs[0].get_legend_handles_labels()
        if gain:
            fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.35,.99),ncol=3,frameon=False,fontsize=7.4)
            hh,ll=axs[-1].get_legend_handles_labels();fig.legend(hh,ll,loc='upper center',bbox_to_anchor=(.84,.99),ncol=1,frameon=False,fontsize=7.1)
        else:fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.53,.99),ncol=3,frameon=False,fontsize=7.8)
        fig.text(.53,.035,'100 paired missions; pointwise bootstrap 95% CI; λref = 9.46803 × 10⁻⁶ bits/use',ha='center',fontsize=7)
        fig.canvas.draw();renderer=fig.canvas.get_renderer();box=fig.bbox
        inspect=list(fig.legends)+list(fig.texts)
        for ax in axs:
            inspect += [ax.xaxis.label,ax.yaxis.label,ax.title,ax.yaxis.get_offset_text()]
            inspect += [t for t,x in zip(ax.get_xticklabels(),ax.get_xticks()) if ax.get_xlim()[0]<=x<=ax.get_xlim()[1]]
            inspect += [t for t,y in zip(ax.get_yticklabels(),ax.get_yticks()) if ax.get_ylim()[0]<=y<=ax.get_ylim()[1]]
        for artist in inspect:
            bb=artist.get_window_extent(renderer)
            if bb.x0<-.5 or bb.y0<-.5 or bb.x1>box.x1+.5 or bb.y1>box.y1+.5:
                layout_issues.append(dict(figure=name,text=artist.get_text() if hasattr(artist,'get_text') else 'legend',bbox=list(bb.bounds)))
        metadata[name]=dict(dimensions_inches=list(fig.get_size_inches()),panels=[dict(xlim=list(ax.get_xlim()),ylim=list(ax.get_ylim()),xscale=ax.get_xscale(),xlabel=ax.get_xlabel(),ylabel=ax.get_ylabel()) for ax in axs])
        for ext in ('pdf','png'):fig.savefig(folder/(name+'.'+ext),dpi=350,facecolor='white')
        plt.close(fig)
    with plt.rc_context({'font.family':'serif','font.size':8,'axes.labelsize':8.7,'xtick.labelsize':8,'ytick.labelsize':8,
                         'axes.linewidth':.7,'pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'}):
        fig,axs=setup(3)
        for panel,(key,li,title) in enumerate((('U',0,'(a) λ = 0: U = K̄'),('U',1,'(b) λ = λref'),('K',1,'(c) λ = λref')),1):
            configure(axs[panel-1],'J',key,title)
            for method in METHODS:draw(NAMES[0],panel,axs[panel-1],'J',key,method,li)
        finish(fig,axs,NAMES[0])
        fig,axs=setup(2)
        for panel,li in enumerate((0,1),1):
            configure(axs[panel-1],'J','unavailability_percent','(a) λ = 0' if li==0 else '(b) λ = λref')
            for method in METHODS:draw(NAMES[1],panel,axs[panel-1],'J','unavailability_percent',method,li)
        finish(fig,axs,NAMES[1])
        fig,axs=setup(3)
        for panel,key in enumerate(('K','U','D'),1):
            configure(axs[panel-1],'speed',key,'('+chr(96+panel)+') '+{'K':'Usable SKR','U':'Objective','D':'Travel distance'}[key])
            draw(NAMES[2],panel,axs[panel-1],'speed',key,'Stationary',1)
            for li in (0,1):
                for method in ('Greedy','DP'):draw(NAMES[2],panel,axs[panel-1],'speed',key,method,li,zero_style=li==0)
        finish(fig,axs,NAMES[2])
        for name,axis,metric_gain in ((NAMES[3],'probability','gain_percent'),(NAMES[5],'spatial','gain_absolute')):
            fig,axs=setup(3)
            for panel,key in enumerate(('K','availability'),1):
                configure(axs[panel-1],axis,key,'(a) Usable SKR' if panel==1 else '(b) Availability')
                for method in METHODS:draw(name,panel,axs[panel-1],axis,key,method,1)
            configure(axs[2],axis,metric_gain,'(c) Paired DP gain')
            for base in METHODS[:2]:draw(name,3,axs[2],axis,metric_gain,'DP',1,base=base)
            finish(fig,axs,name,gain=True)
        fig,axs=setup(3)
        for panel,key in enumerate(('K','U','D'),1):
            configure(axs[panel-1],'horizon',key,'('+chr(96+panel)+') λ = λref')
            for method in METHODS:draw(NAMES[4],panel,axs[panel-1],'horizon',key,method,1)
        finish(fig,axs,NAMES[4])
    write_csv(folder/'plotted_points.csv',points)
    for name in NAMES:write_csv(folder/(name+'_data.csv'),[r for r in points if r['figure']==name])
    save_json(folder/'render_metadata.json',dict(status='CURRENTLY_VERIFIED_PASS' if not layout_issues else 'FAILED',
        producer_sha256=sha(Path(__file__)),png_dpi=350,vector_pdf=True,point_count=len(points),layout_issues=layout_issues,
        confidence_intervals='20,000 paired whole-mission percentile bootstrap; seed20261020; unmodified',
        performance_axes_include_zero=True,no_smoothing=True,no_simulation_interpolation=True,figures=metadata,
        input_sha256={name:sha(out/'existing_data'/name) for name in ('aggregate_statistics.csv','paired_improvements.csv')}))
    print('FIGURES_RENDERED',6,'points',len(points),'layout issues',len(layout_issues),flush=True)


def documents(out,protocol,summary,paired):
    def members(axis):return sorted([r for r in protocol['memberships'] if r['axis']==axis],key=lambda r:r['value'])
    def group(axis,method,key):return np.array([summary[m['case_id'],1,method][key+'_mean'] for m in members(axis)])
    captions=[
        'Mean objective versus the number of candidate UAV positions for Stationary (P2), Greedy, and DP (P3), using nested spatially balanced subsets. Panels show the objective at zero and representative mobility penalties, and the usable SKR at the representative penalty. All means use the same 100 cloud missions; candidate additions preserve the original physical positions and source rates.',
        'Zero-usable-SKR unavailability versus the number of candidate positions at zero and representative mobility penalties. Unavailability is the percentage of slots with S=0 along the selected trajectory. Linear axes retain zeros. The algorithms optimize the SKR objective, not availability itself.',
        'Mean usable SKR, mobility-penalized objective, and total travel distance versus maximum UAV speed. Greedy and DP use zero and representative penalties; Stationary is a speed-independent reference. Means use the same 100 archived cloud missions. Higher speed enlarges the feasible transition set but does not require longer travel.',
        'Mean usable SKR, nonzero-SKR availability, and relative paired DP objective gains versus nominal cloud-blockage probability, at the representative penalty. The evaluated probabilities are 0.1,0.2,0.4,0.6,0.8. Configurations share Gaussian innovations, physical locations, and current clear-sky source rates. Relative gains use the mean of the same baseline missions as denominator and are undefined for invalid baselines.',
        'Mean usable SKR, objective, and total travel distance versus mission length at the representative penalty. Each method is reoptimized on nested prefixes of the same archived cloud missions, with a fixed 20-s slot duration. The objective retains average SKR and total-distance normalization; Greedy uses the corresponding Nt times lambda coefficient.',
        'Mean usable SKR, nonzero-SKR availability, and paired DP objective improvements versus latent spatial correlation length at the representative penalty. The horizontal axis is logarithmic and retains all five evaluated lengths. Blockage probability and latent temporal correlation remain fixed at 0.4 and 0.9. Only authenticated archived masks are used; the spatial length is not a measured cloud radius.'
    ]
    common=f' Bands are pointwise 95% percentile-bootstrap intervals over 20,000 whole-mission resamples (seed 20261020). The exact representative penalty is {LAM!r} bits/use.'
    cap='# IEEE-style captions\n\n'+'\n\n'.join('**'+name+'.** '+text+common for name,text in zip(NAMES,captions))
    cap+='\n\nUNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Synthetic finite-catalog/grid numerical comparison; P2/DP use offline future cloud states.\n'
    (out/'figure_captions_en.md').write_bytes(cap.encode('utf-8'))
    mapping=[]
    for name,axis in zip(NAMES,('J','J','speed','probability','horizon','spatial')):
        mapping.append(dict(figure=name,axis=axis,pdf='existing_data/figures/'+name+'.pdf',png='existing_data/figures/'+name+'.png',
            plot_data='existing_data/figures/'+name+'_data.csv',statistics='existing_data/aggregate_statistics.csv',
            paired='existing_data/paired_improvements.csv',original_source='current P1 winners + authenticated archived cloud masks',caption='figure_captions_en.md'))
    write_csv(out/'figure_source_mapping.csv',mapping)
    observations={};trends=[]
    for axis in AXIS_LABELS:
        mm=members(axis);obs=dict(values=[m['value'] for m in mm],methods={})
        for method in METHODS:
            obs['methods'][method]={}
            for key in ('K','U','D','availability'):
                y=group(axis,method,key);tol=1e-9 if key=='D' else 1e-12
                record=dict(first=float(y[0]),last=float(y[-1]),minimum=float(y.min()),maximum=float(y.max()),
                    argmin=mm[int(y.argmin())]['value'],argmax=mm[int(y.argmax())]['value'],
                    increasing_segments=int(np.sum(np.diff(y)>tol)),decreasing_segments=int(np.sum(np.diff(y)<-tol)),
                    tied_segments=int(np.sum(abs(np.diff(y))<=tol)))
                obs['methods'][method][key]=record;trends.append(dict(axis=axis,method=method,metric=key,**record))
        obs['DP_mean_K_ge_Greedy_points']=int(np.sum(group(axis,'DP','K')>=group(axis,'Greedy','K')-1e-12))
        obs['DP_mean_availability_ge_Greedy_points']=int(np.sum(group(axis,'DP','availability')>=group(axis,'Greedy','availability')-1e-12))
        for base in METHODS[:2]:
            pp=[paired[m['case_id'],1,base,'U'] for m in mm]
            obs['positive_paired_U_CI_vs_'+base]=[mm[i]['value'] for i,r in enumerate(pp) if r['ci95_low']>1e-12]
            obs['max_relative_U_gain_vs_'+base]=max((r['ratio_of_means_percent'] for r in pp if r['ratio_of_means_percent'] is not None),default=None)
        observations[axis]=obs
    write_csv(out/'existing_data/observed_trends.csv',trends)
    effects_raw=rows(out/'existing_data/parameter_effects.csv')
    strongest={}
    for title,method,key in [('SKR','DP','K'),('availability','DP','availability'),('mobility_gain_vs_P2','DP-minus-Stationary','U'),('gain_vs_Greedy','DP-minus-Greedy','U')]:
        candidates=[r for r in effects_raw if r['method']==method and r['metric']==key]
        best=max(candidates,key=lambda r:float(r['span']))
        strongest[title]={k:(best[k] if k in ('axis','method','metric') else (None if best[k]=='' else float(best[k]))) for k in best}
    method_specific={}
    for method in METHODS:
        method_specific[method]={}
        for key in ('K','availability'):
            best=max((r for r in effects_raw if r['method']==method and r['metric']==key),key=lambda r:float(r['span']))
            method_specific[method][key]=dict(axis=best['axis'],span=float(best['span']),minimum=float(best['minimum']),maximum=float(best['maximum']))
    findings=dict(representative_lambda=LAM,observations=observations,strongest_observed_spans=strongest,
        method_specific_strongest_spans=method_specific,
        interpretation='Descriptive spans over different approved domains, not universal normalized or causal parameter sensitivities',
        recommended_figures=[NAMES[i] for i in (0,1,2,3)],security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    save_json(out/'findings.json',findings)
    lines=['# Stage A — Phân tích độ nhạy tham số','',
        'UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.','',
        'Kết quả dùng P1 hiện tại (233 nguồn exact), 100 mission ghép cặp và mask đã xác thực. Chỉ tính lại P2/Greedy/DP. '
        'Không sinh mây, không tính lại kênh/SKR/C,w, không thực hiện Stage B.','',
        'Thiết kế thay đổi một tham số và so nhiều đường tham khảo Hình2–3 của '
        '[Gong et al., IEEE WCL2020](https://doi.org/10.1109/LWC.2019.2958804); không chuyển số trạm được chọn hoặc số trạm hoạt động sang mô hình một UAV.','',
        f'λ dùng cố định ở mọi cấu hình: 0 và {LAM!r} bits/use; Dref=1000m, Δt=20s. Availability là tỷ lệ S>0, không có engineering threshold. '
        'HAP/UAV, quang học, detector và nguồn giữ nguyên protocol cha. P2/DP offline, Greedy chỉ đọc slot hiện tại và biết chiều dài horizon.','',
        '| Hình | PDF | PNG | Dữ liệu vẽ |','|---|---|---|---|']
    lines += [f'| {name} | [PDF](existing_data/figures/{name}.pdf) | [PNG](existing_data/figures/{name}.png) | [CSV](existing_data/figures/{name}_data.csv) |' for name in NAMES]
    lines += ['', '## Thống kê và cách đọc','',
        'Mean, SD mẫu, median và CI95% dùng 100 mission, không dùng ô/slot làm mẫu độc lập. Bootstrap20.000 whole-mission resamples, '
        'seed20261020, cùng trọng số resampling giữa các cấu hình. CI pointwise chưa hiệu chỉnh nhiều so sánh; không phải CI bảo mật. '
        'Phần trăm là100×(meanDP−meanBaseline)/meanBaseline, không phải mean phần trăm từng mission. Mẫu số không hợp lệ ghi NA. '
        'Các trục performance gồm0 nên chênh nhỏ có thể khó thấy; bảng paired cho effect size và CI, không suy kết luận từ độ chồng lấn các band riêng lẻ.','']
    explanations={
        'J':'Tập con được chọn chỉ từ tọa độ: bốn góc, cân bằng quadrant, maximin và tie theo global ID. Đồ thị có thể mất kết nối khi J nhỏ; đây là một phần của hiệu ứng tập lựa chọn, không được sửa bằng cạnh giả. DP/P2 U phải không giảm khi tăng J, không áp dụng bảo đảm đó cho Greedy hoặc availability.',
        'speed':'Tốc độ0 và2,5m/s đều không cho phép bước sang ô khác;5m/s bắt đầu cho bước100m. DP có điểm đầu tự chọn nên bằng P2 khi không di chuyển. Greedy có thể khác P2 vì chọn theo slot đầu. Chỉ U_DP được bảo đảm không giảm khi nới tốc độ; tại λ>0 không bảo đảm K hoặc D đơn điệu.',
        'horizon':'Mỗi điểm dùng prefix mây thật và được tối ưu lại, không cắt đường30slot. Giữ U=meanS−λD/1000 và Greedy dùng Ntλ. Khi Nt đổi, hiệu ứng bao gồm horizon và mức phạt tương đối với average reward, không cô lập riêng lợi ích lookahead; không áp đặt đơn điệu theo Nt hoặc bảo đảm online.',
        'probability':'Chỉ dùng năm mức đã lưu; không có0,3/0,5/0,7. Giữ ell250m và latent rho0,9 với common innovations. Binary correlation sau threshold có thể thay đổi theo p. Mask lồng nhau cho phép kiểm tra U_DP/P2 không tăng theo p; không ép Greedy hoặc availability có cùng tính chất. Gain phần trăm lớn cần đọc cùng gain tuyệt đối và baseline.',
        'spatial':'Các ell50–1000m đã có sẵn, tương ứng0,5–10 lần khoảng cách ô100m. Trục x logarithmic giữ đủ5 điểm đã tính, tránh chồng nhãn50/100m; không thêm điểm mô phỏng. Giữ p0,4 và latent rho0,9. Không có bảo đảm đơn điệu theo ell; common innovations không làm các mask theo ell trở thành tập lồng nhau. Đây là chiều dài tương quan tiềm ẩn, không phải bán kính mây đo được.'}
    for name,axis in zip((NAMES[0],NAMES[2],NAMES[3],NAMES[4],NAMES[5]),('J','speed','probability','horizon','spatial')):
        mm=members(axis);obs=observations[axis];dp=obs['methods']['DP']
        lines += ['## '+name,'',explanations[axis],'',
            f'Ở λref: DP meanK đi từ {fmt(dp["K"]["first"])} đến {fmt(dp["K"]["last"])} bits/use; '
            f'meanU từ {fmt(dp["U"]["first"])} đến {fmt(dp["U"]["last"])}. MeanD từ {fmt(dp["D"]["first"])} đến {fmt(dp["D"]["last"])}m; '
            f'availability từ {100*dp["availability"]["first"]:.6f}% đến {100*dp["availability"]["last"]:.6f}%.',
            f'DP meanK ≥ Greedy ở {obs["DP_mean_K_ge_Greedy_points"]}/{len(mm)} điểm; mean availability ≥ Greedy ở '
            f'{obs["DP_mean_availability_ge_Greedy_points"]}/{len(mm)} điểm. Đây là thống kê theo các mean, không phải bảo đảm cho từng mission. '
            'Đánh giá phương án tốt hơn theo objective U; quãng đường thấp nhất riêng lẻ không phải mục tiêu của DP.','',
            '| Giá trị | K P2 | K Greedy | K DP | U P2 | U Greedy | U DP | D Greedy (m) | D DP (m) | A DP (%) |',
            '|---|---|---|---|---|---|---|---|---|---|']
        for member in mm:
            rr=[summary[member['case_id'],1,m] for m in METHODS]
            vals=[r[k+'_mean']*1e4 for k in ('K','U') for r in rr]
            lines.append('| '+str(member['value'])+' | '+' | '.join(f'{v:.7f}' for v in vals)+f' | {rr[1]["D_mean"]:.6f} | {rr[2]["D_mean"]:.6f} | {100*rr[2]["availability_mean"]:.6f} |')
        lines += ['', 'K/U trong bảng có đơn vị10⁻⁴ bits/use; A là nonzero-SKR availability.','',
            '| Giá trị | ΔU DP−P2 | CI95% | Gain U/P2 (%) | ΔU DP−Greedy | CI95% | Gain U/Greedy (%) |',
            '|---|---|---|---|---|---|---|']
        for member in mm:
            pp=[paired[member['case_id'],1,b,'U'] for b in METHODS[:2]]
            cells=[]
            for r in pp:cells += [fmt(r['mean']),'['+fmt(r['ci95_low'])+', '+fmt(r['ci95_high'])+']',fmt(r['ratio_of_means_percent'])]
            lines.append('| '+str(member['value'])+' | '+' | '.join(cells)+' |')
        lines += ['',f'CI meanΔU dương nghiêm ngặt so với P2 ở các điểm {obs["positive_paired_U_CI_vs_Stationary"]}; '
            f'so với Greedy ở {obs["positive_paired_U_CI_vs_Greedy"]}. Điểm không có CI dương không được mô tả là gain dương chắc chắn.','']
        g=obs['methods']['Greedy']['U']
        lines += [f'Trend meanU tại λref: DP có {dp["U"]["increasing_segments"]} đoạn tăng, {dp["U"]["decreasing_segments"]} đoạn giảm và '
            f'{dp["U"]["tied_segments"]} đoạn hòa; Greedy tương ứng {g["increasing_segments"]}, {g["decreasing_segments"]}, {g["tied_segments"]}. '
            'Đây là quan sát ở mean; kiểm tra tính chất bảo đảm được thực hiện riêng cho từng mission.','']
        if axis=='J':
            d=rows(out/'subset_diagnostics.csv')[0];u20=summary['J_20',1,'DP']['U_mean'];u100=summary['base',1,'DP']['U_mean']
            lines += [f'J=10 có {d["components"]} thành phần liên thông và {d["isolated_positions"]} điểm cô lập; từ J=20 đồ thị đã liên thông. '
                'Do đó mức tăng ban đầu gồm cả khả năng tiếp cận vị trí và spatial diversity. '
                f'J=20 đạt {100*u20/u100:.6f}% meanU tại J=100. Các mức J lớn vẫn cải thiện nhưng không được gọi là optimum J phổ quát; '
                'chi phí tăng mật độ vị trí chưa được đưa vào mục tiêu.','']
        elif axis=='speed':
            u15=summary['base',1,'DP']['U_mean'];u25=summary['speed_25',1,'DP']['U_mean']
            d20=summary['speed_20',1,'DP']['D_mean'];d25=summary['speed_25',1,'DP']['D_mean']
            gap0=paired['speed_0',1,'Greedy','U']['ratio_of_means_percent']
            lines += [f'Từ15 lên25m/s, meanU DP chỉ tăng {100*(u25-u15)/u15:.6f}%. MeanD DP từ20 lên25m/s đổi '
                f'{fmt(d20)}→{fmt(d25)}m: tốc độ tối đa cao hơn không bắt buộc đi dài hơn. '
                f'Ở v=0, gainU DP−Greedy là {fmt(gap0)}%, trong khi DP=P2 và cả hai đứng yên; đây là lợi thế chọn điểm đầu offline, không phải lợi ích di chuyển. '
                'Gain mobility được đọc bằng DP−P2.','']
        elif axis=='probability':
            p8=paired['probability_0p8',1,'Stationary','U'];g8=paired['probability_0p8',1,'Greedy','U']
            lines += [f'Ở p=0,8, meanU DP cao hơn P2 {fmt(p8["ratio_of_means_percent"])}% và Greedy {fmt(g8["ratio_of_means_percent"])}%. '
                'Trong năm mức đã thử, gain lớn nhất nằm ở biên p=0,8; chưa quan sát một đỉnh nội miền hoặc ngưỡng mây làm mobility mất tác dụng. '
                'Không ngoại suy sang p>0,8 và không tạo các điểm0,3/0,5/0,7.','']
        elif axis=='horizon':
            first=paired['horizon_5',1,'Stationary','U']['ratio_of_means_percent'];last=paired['base',1,'Stationary','U']['ratio_of_means_percent']
            lines += [f'GainU DP/P2 tăng từ {fmt(first)}% ở5slot lên {fmt(last)}% ở30slot, dù meanK/U tuyệt đối của DP giảm. '
                'P2 phải tìm một điểm phù hợp cho nhiều slot hơn, trong khi DP được đổi vị trí; cách diễn giải này phù hợp với kết quả nhưng không cô lập hiệu ứng thông tin tương lai '
                'khỏi chuẩn hóa Nt và các prefix khác nhau.','']
        else:
            first=paired['spatial_50',1,'Stationary','U'];last=paired['spatial_1000',1,'Stationary','U']
            lines += [f'Trong dữ liệu này, meanU DP giảm khi ell tăng nhưng gain tuyệt đối DP−P2 tăng {fmt(first["mean"])}→{fmt(last["mean"])} bits/use '
                f'và gain tương đối tăng {fmt(first["ratio_of_means_percent"])}→{fmt(last["ratio_of_means_percent"])}%. '
                'Kết quả không hỗ trợ kết luận rằng tương quan lớn hơn luôn làm gain mobility nhỏ hơn: baseline P2 giảm mạnh hơn DP trong dải này. '
                'Đây là kết quả có điều kiện, không phải một định luật đơn điệu theo ell.','']
    lines += ['## '+NAMES[1],'',
        'HìnhA2 dùng cùng tập J nhưng đo zero-SKR unavailability. Đây không phải mục tiêu tối ưu, vì vậy không suy thứ tự availability từ thứ tự objective. '
        'Các giá trị0 được giữ đúng, không đổi thành epsilon để vẽ log.','',
        '| J | P2 λ0 (%) | Greedy λ0 (%) | DP λ0 (%) | P2 λref (%) | Greedy λref (%) | DP λref (%) |',
        '|---|---|---|---|---|---|---|']
    for member in members('J'):
        vals=[summary[member['case_id'],li,m]['unavailability_percent_mean'] for li in (0,1) for m in METHODS]
        lines.append('| '+str(member['value'])+' | '+' | '.join(f'{v:.7f}' for v in vals)+' |')
    lines += ['', '## Tham số có ảnh hưởng quan sát lớn nhất','',
        'So sánh span=max(mean)−min(mean) trên đúng dải đã duyệt, tại λref. Các dải và đơn vị tham số khác nhau nên đây là '
        'xếp hạng mô tả có điều kiện, không phải elasticity, Sobol index hoặc chứng minh nguyên nhân phổ quát.','',
        '| Đại lượng | Tham số có span lớn nhất | Span | Điểm min → max |','|---|---|---|---|']
    for label,r in strongest.items():
        span=100*r['span'] if label=='availability' else r['span'];unit='percentage points' if label=='availability' else 'bits/use'
        lines.append(f'| {label} | {AXIS_VI[r["axis"]]} | {fmt(span)} {unit} | {fmt(r["argmin"])} → {fmt(r["argmax"])} |')
    lines += ['', 'Xếp hạng phụ thuộc phương án; không gộp kết quả DP thành kết luận chung cho mọi thuật toán.','',
        '| Phương án | Tham số ảnh hưởng meanK mạnh nhất | Span K (bits/use) | Tham số ảnh hưởng availability mạnh nhất | Span (pp) |',
        '|---|---|---|---|---|']
    for method,r in method_specific.items():
        lines.append(f'| {method} | {AXIS_VI[r["K"]["axis"]]} | {fmt(r["K"]["span"])} | {AXIS_VI[r["availability"]["axis"]]} | {100*r["availability"]["span"]:.6f} |')
    lines += ['', 'Toàn bộ span của các phương án/metric: [parameter_effects.csv](existing_data/parameter_effects.csv). '
        'Gain biên theo J và CI: [J_incremental_gains.csv](existing_data/J_incremental_gains.csv). '
        'Không gọi một vùng là bão hòa chỉ vì CI của incremental gain chứa0.','',
        '## Bốn hình ưu tiên và giới hạn','',
        '**A1, A2, B, C** theo ưu tiên đã chốt trước batch: số lựa chọn và objective; outage dọc đường; ràng buộc tốc độ; '
        'mức độ mây. D/E bổ sung cơ chế horizon và spatial diversity. Không chọn lại seed, dải tham số hoặc λ sau khi thấy kết quả.','',
        'Đây là finite-catalog/grid synthetic manuscript comparison. Giữ P1 tại233 nguồn, không phải optimum nguồn liên tục; '
        'MI2D ghép Holevo homodyne chưa được xác thực an toàn lượng tử. P2/DP có thông tin toàn horizon, Greedy là current-slot oracle; '
        'không có common-information ablation. Khoảng cách chưa là năng lượng; chưa có transit/reacquisition hay số bit vật lý. '
        'Frozen hash discrepancy và Objective C USER_STOPPED giữ nguyên. Không Stage B, final-test/held-out, nâng lifecycle, external edit, commit/push.','',
        '## Dữ liệu và xác minh','',
        '[Protocol](protocol.json) · [Nguồn đầu vào](input_manifest.json) · [Metric từng mission](existing_data/mission_metrics.csv) · '
        '[Mean/SD/median/CI](existing_data/aggregate_statistics.csv) · [Paired gains](existing_data/paired_improvements.csv) · '
        '[Baseline10λ](validation/baseline_reproduction.csv) · [Captions](figure_captions_en.md) · '
        '[Source map](figure_source_mapping.csv) · [Validation](validation_report.md) · [Receipt](validation/final_receipt.json)']
    (out/'report_vi.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'results/mobility_parameter_sensitivity_20261020')
    args=parser.parse_args();out=args.output.resolve()
    if (out/'validation/final_receipt.json').exists():raise FileExistsError('Completed figure package is immutable')
    protocol,summary,paired=load(out);render(out,protocol,summary,paired);documents(out,protocol,summary,paired)


if __name__=='__main__':main()
