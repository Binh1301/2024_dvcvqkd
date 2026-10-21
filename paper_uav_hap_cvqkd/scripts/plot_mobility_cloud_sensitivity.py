"""Stage B figures and reports from saved, authenticated mobility statistics only."""
from pathlib import Path
import csv
import json
import hashlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FixedLocator, ScalarFormatter
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mobility_parameter_sensitivity_stage_b_20261020'
STYLE={'Stationary':dict(color='tab:blue',marker='o',linestyle='-'),
       'Greedy':dict(color='tab:orange',marker='s',linestyle='--'),
       'DP':dict(color='tab:red',marker='^',linestyle='-')}
LABEL={'Stationary':'Stationary (P2)','Greedy':'Greedy','DP':'Dynamic Programming (P3)'}
AXES=('probability','spatial','temporal')
NAMES=('fig_B1_cloud_probability','fig_B2_spatial_correlation','fig_B3_temporal_correlation','fig_B4_distance_penalty')
XLABEL={'probability':'Cloud-blockage\nprobability','spatial':'Spatial correlation length\n(m; log scale)','temporal':'Latent temporal\ncorrelation ρ'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def csv_save(p,data):
    with p.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
def json_save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    if (OUT/'validation/final_receipt.json').exists():raise FileExistsError('Completed Stage B is immutable')
    receipt=js(OUT/'validation/aggregate.json')
    assert receipt['status']=='CURRENTLY_VERIFIED_PASS'
    for name,h in receipt['artifact_sha256'].items():assert sha(OUT/name)==h,name
    protocol=js(OUT/'protocol.json');c=protocol['settings']
    summary={(r['case_id'],int(r['lambda_index']),r['method']):r for r in rows(OUT/'mobility/aggregate_statistics.csv')}
    paired={(r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(OUT/'mobility/paired_improvements.csv')}
    def members(axis):return sorted([r for r in protocol['memberships'] if r['axis']==axis],key=lambda r:r['value'])
    points=[];metadata={}
    def draw(fig_name,panel,ax,axis,method,metric,li=1,baseline=None):
        mm=members(axis);xx=[r['value'] for r in mm];yy=[];lo=[];hi=[]
        for member in mm:
            if baseline:
                r=paired[member['case_id'],li,baseline,'U'];yy.append(float(r['mean']));lo.append(float(r['ci95_low']));hi.append(float(r['ci95_high']))
            else:
                r=summary[member['case_id'],li,method];scale=100 if metric=='availability' else 1
                yy.append(float(r[metric+'_mean'])*scale);lo.append(float(r[metric+'_ci95_low'])*scale);hi.append(float(r[metric+'_ci95_high'])*scale)
        style=dict(STYLE[baseline or method]);label=LABEL[method] if baseline is None else 'DP minus '+('P2' if baseline=='Stationary' else 'Greedy')
        if fig_name==NAMES[3] and method!='Stationary':
            label=('DP' if method=='DP' else 'Greedy')+(', λ=0' if li==0 else ', λref')
            if li==0:style.update(marker='D' if method=='DP' else 'v',linestyle='-.' if method=='DP' else ':')
        line=ax.plot(xx,yy,label=label,lw=1.8,ms=4.6,mfc='white',mew=1,**style)[0]
        ax.fill_between(xx,lo,hi,color=style['color'],alpha=.09,lw=0)
        for i,(x,y) in enumerate(zip(line.get_xdata(),line.get_ydata())):
            points.append(dict(figure=fig_name,panel=panel,axis=axis,case_id=mm[i]['case_id'],method=method,baseline=baseline or '',metric=metric,
                               lambda_index=li,lambda_bits_per_use=c['lambda_values'][li],x=float(x),y=float(y),ci95_low=lo[i],ci95_high=hi[i],
                               color=style['color'],marker=style['marker'],linestyle=style['linestyle']))
    def setup():
        fig,axs=plt.subplots(1,3,figsize=(7.2,3.4));fig.subplots_adjust(left=.105,right=.985,bottom=.28,top=.77,wspace=.72)
        for ax in axs:
            ax.set_axisbelow(True);ax.grid(color='.83',lw=.5);ax.grid(which='minor',color='.94',lw=.35)
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        return fig,axs
    def axis_setup(ax,axis,ylabel,title,scientific=False):
        vals=[r['value'] for r in members(axis)];ax.set_xlabel(XLABEL[axis]);ax.set_ylabel(ylabel,labelpad=3);ax.set_title(title,fontsize=9,pad=8)
        ax.set_xticks(vals)
        if axis=='spatial':
            ax.set_xscale('log');ax.set_xticks(vals);ax.set_xticklabels([str(v) for v in vals]);ax.set_xlim(min(vals)/1.17,max(vals)*1.17)
            ax.xaxis.set_minor_locator(FixedLocator([np.sqrt(a*b) for a,b in zip(vals,vals[1:])]))
        else:
            span=max(vals)-min(vals);ax.set_xlim(min(vals)-.05*span,max(vals)+.05*span)
            ax.xaxis.set_minor_locator(FixedLocator([(a+b)/2 for a,b in zip(vals,vals[1:])]))
        ax.tick_params(axis='x',labelsize=7 if axis!='temporal' else 6.8)
        if axis=='temporal':plt.setp(ax.get_xticklabels(),rotation=90,ha='center')
        if scientific:
            sf=ScalarFormatter(useMathText=True);sf.set_powerlimits((0,0));sf.set_useOffset(False);ax.yaxis.set_major_formatter(sf)
    def finish(fig,axs,name,gaps=False):
        for i,ax in enumerate(axs,1):
            data=[r for r in points if r['figure']==name and r['panel']==i];values=[r[key] for r in data for key in ('y','ci95_low','ci95_high')]
            low=min(0,min(values));high=max(values);span=max(high-low,1e-12);ax.set_ylim(low-.04*span,high+.14*span)
        handles,labels=axs[0].get_legend_handles_labels()
        if gaps:
            fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.35,.99),ncol=3,frameon=False,fontsize=7.3)
            h,l=axs[2].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.84,.99),ncol=1,frameon=False,fontsize=7.2)
        else:fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.53,.99),ncol=3,frameon=False,fontsize=7.5)
        fig.text(.53,.035,'100 paired missions; pointwise bootstrap 95% CI; λref = 9.46803 × 10⁻⁶ bits/use',ha='center',fontsize=7)
        fig.canvas.draw();renderer=fig.canvas.get_renderer();issues=[]
        for ax in axs:
            for artist in (ax.xaxis.label,ax.yaxis.label,ax.title,ax.yaxis.get_offset_text(),*ax.get_xticklabels()):
                b=artist.get_window_extent(renderer)
                if b.x0<0 or b.y0<0 or b.x1>fig.bbox.x1 or b.y1>fig.bbox.y1:issues.append(artist.get_text())
        assert not issues,issues
        metadata[name]=dict(panels=[dict(xlim=list(ax.get_xlim()),ylim=list(ax.get_ylim()),xscale=ax.get_xscale()) for ax in axs],layout_issues=issues)
        for ext in ('pdf','png'):fig.savefig(OUT/'figures'/(name+'.'+ext),dpi=350,facecolor='white')
        plt.close(fig)
    with plt.rc_context({'font.family':'serif','font.size':8,'axes.labelsize':8.5,'axes.linewidth':.7,'pdf.fonttype':42}):
        for axis,name in zip(AXES,NAMES[:3]):
            fig,axs=setup()
            for i,metric in enumerate(('K','availability'),1):
                axis_setup(axs[i-1],axis,'Mean usable SKR\n(bits/use)' if metric=='K' else 'Nonzero-SKR availability\n(%)','(a) Usable SKR' if metric=='K' else '(b) Availability',metric=='K')
                for method in STYLE:draw(name,i,axs[i-1],axis,method,metric)
            axis_setup(axs[2],axis,'Mean DP objective gap\n(bits/use)','(c) Paired DP gain',True)
            for baseline in ('Stationary','Greedy'):draw(name,3,axs[2],axis,'DP','gain_absolute',baseline=baseline)
            finish(fig,axs,name,True)
        fig,axs=setup()
        for i,axis in enumerate(AXES,1):
            axis_setup(axs[i-1],axis,'Mean travel distance\n(m)','('+chr(96+i)+') '+{'probability':'Cloud blockage','spatial':'Spatial correlation','temporal':'Temporal correlation'}[axis])
            draw(NAMES[3],i,axs[i-1],axis,'Stationary','D')
            for li in (0,1):
                for method in ('Greedy','DP'):draw(NAMES[3],i,axs[i-1],axis,method,'D',li)
        finish(fig,axs,NAMES[3])
    csv_save(OUT/'figures/plotted_points.csv',points)
    for name in NAMES:csv_save(OUT/'figures'/(name+'_data.csv'),[r for r in points if r['figure']==name])
    json_save(OUT/'figures/render_metadata.json',dict(status='CURRENTLY_VERIFIED_PASS',figures=metadata,points=len(points),dpi=350,
        input_sha256=receipt['artifact_sha256'],producer_sha256=sha(Path(__file__)),no_smoothing=True,no_added_simulation_points=True))

    captions=[
        'Mean usable SKR, nonzero-SKR availability, and paired DP objective differences versus cloud-blockage probability at the fixed representative penalty. Eight probabilities extend the five archived Stage A settings with newly generated masks at 0.3, 0.5, and 0.7; all settings share innovations and the same current P1 rates.',
        'Mean usable SKR, nonzero-SKR availability, and paired DP objective differences versus latent spatial correlation length at the representative penalty. All five mask configurations are authenticated archive data; the logarithmic horizontal axis retains each evaluated length. Blockage probability and latent temporal correlation are fixed at 0.4 and 0.9.',
        'Mean usable SKR, nonzero-SKR availability, and paired DP objective differences versus latent AR(1) temporal correlation at the representative penalty. Blockage probability and spatial correlation length are fixed at 0.4 and 250 m. The five archived temporal profiles use identical mission IDs and common innovations; rho is a latent Gaussian correlation, distinct from binary blockage correlation.',
        'Mean travel distance versus blockage probability, spatial length, and temporal correlation for the same stationary, Greedy, and DP methods. Greedy and DP use both zero and representative penalties, held fixed across configurations. Stationary travel distance is zero. Distance measures movement and is not a calibrated propulsion-energy estimate.',
    ]
    text=['# Stage B English captions','']
    for name,caption in zip(NAMES,captions):
        text += [f'**{name}.** {caption} Means and pointwise 95% intervals use the same 100 paired missions and the existing 20,000 whole-mission bootstrap resamples. P2/DP are offline benchmarks; Greedy observes the current slot. The exact representative penalty is 9.468026677248516e-6 bit/use.','']
    text+=['UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.']
    (OUT/'figure_captions_en.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    report=['# Stage B — Độ nhạy mây bổ sung','', 'UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.','',
            '## Thiết kế và phạm vi','',
            'Người dùng phê duyệt Stage B sau Stage A. Giữ nguồn P1 exact233 nguồn và cấu hình vật lý hiện tại; không tính lại kênh, MI, Holevo hoặc C,w. Có16 cấu hình riêng biệt:8 mức p,5 mức ell và5 mức rho cùng chia sẻ baseline. Chỉ tạo300 mask cho p=0,3/0,5/0,7;13 cấu hình còn lại được replay chính xác từ archive. Không dùng SKR quang học cũ.','',
            'Mỗi cấu hình dùng100 realization ID0–99,seed20261015,lưới100 vị trí,30slot×20s,vmax15m/s,Dref1000m. Hai λ tuyệt đối là0 và9.468026677248516×10⁻⁶. Chín trường hợp mobility Stage A được tái sử dụng; bảy trường hợp mới cần1400 cặp DP/Greedy,ngoài200 cặp audit baseline.','',
            'S=(1−C)Kstar;U=mean(S_path)−λD/1000. Greedy dùng S_now−Ntλd/1000. Availability=mean(S_path>0),không dùng engineering threshold. P2/DP offline có thông tin toàn nhiệm vụ,Greedy chỉ đọc slot hiện tại; khởi đầu tự chọn.','',
            'CI95% pointwise dùng lại20.000 whole-mission bootstrap count vectors của Stage A,seed20261020;không tạo bootstrap draw mới. So sánh cùng ID và cùng trọng số resampling. Tỷ lệ là100×chênh lệch mean/mean baseline dương;NA khi không hợp lệ. CI chưa hiệu chỉnh nhiều so sánh,không phải giới hạn an toàn lượng tử.','',
            '## Hình và kết quả','']
    findings={}
    for axis,name in zip(AXES,NAMES[:3]):
        mm=members(axis);data=[]
        report += [f'### {name}','',f'[PDF vector](figures/{name}.pdf) · [PNG 350 dpi](figures/{name}.png) · [CSV](figures/{name}_data.csv)','',
                   '| Tham số | K P2 | K Greedy | K DP | U DP | D DP(m) | A P2(%) | A Greedy(%) | A DP(%) | Gain U/P2(%) | Gain U/Greedy(%) |',
                   '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in mm:
            cid=m['case_id'];ss=[summary[cid,1,method] for method in STYLE];dp=ss[2]
            gains=[paired[cid,1,b,'U'] for b in ('Stationary','Greedy')]
            vals=[float(s['K_mean'])*1e4 for s in ss]
            report.append('| '+str(m['value'])+' | '+' | '.join(f'{v:.7f}' for v in vals)+f' | {float(dp["U_mean"])*1e4:.7f} | {float(dp["D_mean"]):.3f} | '+' | '.join(f'{float(s["availability_mean"])*100:.3f}' for s in ss)+' | '+' | '.join('NA' if not g['ratio_of_means_percent'] else f'{float(g["ratio_of_means_percent"]):.4f}' for g in gains)+' |')
            data.append(dict(value=m['value'],case_id=cid,K=float(dp['K_mean']),U=float(dp['U_mean']),D=float(dp['D_mean']),availability=float(dp['availability_mean']),
                             gain_over_P2_percent=float(gains[0]['ratio_of_means_percent']),gain_over_Greedy_percent=float(gains[1]['ratio_of_means_percent'])))
        report += ['', 'K/U trong bảng có đơn vị10⁻⁴ bit/use. Đánh giá phương án tốt hơn bằng U;không suy availability hoặc K từng mission từ ưu thế U.','',
                   '| Tham số | ΔU DP−P2 | CI95% | ΔU DP−Greedy | CI95% |','|---|---:|---|---:|---|']
        for m in mm:
            gs=[paired[m['case_id'],1,b,'U'] for b in ('Stationary','Greedy')]
            report.append('| '+str(m['value'])+' | '+' | '.join(f'{float(g["mean"]):.8g} | [{float(g["ci95_low"]):.8g}, {float(g["ci95_high"]):.8g}]' for g in gs)+' |')
        ys=[d['gain_over_P2_percent'] for d in data];best=data[int(np.argmax(ys))]
        report += ['',f'Gain U_DP/P2 lớn nhất quan sát được tại {axis}={best["value"]}: **{best["gain_over_P2_percent"]:.4f}%**. Đây là cực đại trên các điểm thử,không chứng minh optimum liên tục hoặc xu hướng ngoài dải.','']
        if axis=='probability':report += ['Mask theo p lồng nhau,nên U tối ưu DP/P2 không tăng khi p tăng;không ép gain hoặc availability đơn điệu. Ba điểm bổ sung đã định trước,không chọn theo kết quả.','']
        if axis=='spatial':report += ['Tất cả dữ liệu mask ở dải ell này đã có từ trước;Stage B giữ lại để so với p và rho. Không có bảo đảm đơn điệu theo ell;đây là tương quan tiềm ẩn,không phải kích thước mây đo được.','']
        if axis=='temporal':report += [f'Ở rho0→0,98,K_DP tăng {data[0]["K"]:.8g}→{data[-1]["K"]:.8g} bit/use,U_DP tăng {data[0]["U"]:.8g}→{data[-1]["U"]:.8g},nhưng D_DP giảm {data[0]["D"]:.3f}→{data[-1]["D"]:.3f}m. Gain U_DP/P2 giảm {data[0]["gain_over_P2_percent"]:.4f}→{data[-1]["gain_over_P2_percent"]:.4f}%. Trong mẫu này,persistence làm một vị trí thông thoáng có thể phục vụ nhiều slot hơn và làm P2 cạnh tranh hơn;đây là cách diễn giải phù hợp dữ liệu,không phải chứng minh nhân quả riêng biệt.','',
                                      'Tương quan thời gian cao tạo trạng thái tồn tại lâu hơn,có thể thay đổi cả lựa chọn điểm đứng yên và nhu cầu di chuyển. Không áp đặt hướng biến thiên K,U hoặc mobility gain. Cùng seed không làm mask theo rho thành tập lồng nhau.','']
        findings[axis]=data
    report += ['## Persistence: latent rho và binary correlation','',
               '| rho tiềm ẩn | τ=−20/log(rho)(s) | τ/600s | Corr Bernoulli lag1 lý thuyết | p thực nghiệm và CI95% theo mission |','|---|---:|---:|---:|---|']
    diagnostics=rows(OUT/'clouds/correlation_diagnostics.csv')
    for m in members('temporal'):
        rho=m['value'];tau=0 if rho==0 else -20/np.log(rho)
        binary=next(float(r['target']) for r in diagnostics if r['case_id']==m['case_id'] and r['metric']=='binary_temporal')
        observed=next(r for r in diagnostics if r['case_id']==m['case_id'] and r['metric']=='blockage_probability')
        report.append(f'| {rho} | {tau:.3f} | {tau/600:.4f} | {binary:.6f} | {float(observed["mean"]):.5f} [{float(observed["ci95_low"]):.5f}, {float(observed["ci95_high"]):.5f}] |')
    effects=[]
    for axis in AXES:
        mm=members(axis)
        for method in STYLE:
            for metric in ('K','U','D','availability'):
                values=np.array([float(summary[m['case_id'],1,method][metric+'_mean']) for m in mm])
                effects.append(dict(axis=axis,method=method,metric=metric,span=float(np.ptp(values)),minimum=float(values.min()),maximum=float(values.max()),argmin=mm[int(values.argmin())]['value'],argmax=mm[int(values.argmax())]['value']))
        for baseline in ('Stationary','Greedy'):
            values=np.array([float(paired[m['case_id'],1,baseline,'U']['mean']) for m in mm])
            effects.append(dict(axis=axis,method='DP-minus-'+baseline,metric='U',span=float(np.ptp(values)),minimum=float(values.min()),maximum=float(values.max()),argmin=mm[int(values.argmin())]['value'],argmax=mm[int(values.argmax())]['value']))
    csv_save(OUT/'mobility/parameter_effects.csv',effects)
    report += ['', 'Khởi tạo Z0 theo phân phối dừng,không dùng burn-in. τ biểu diễn AR Gaussian,không đồng nhất với thời gian tương quan Bernoulli hoặc thời gian mây đo được. Với rho0,98,τ lớn hơn nhiệm vụ600s;nên ảnh hưởng lựa chọn điểm đầu offline phải được giữ trong diễn giải. p danh định giữ0,4 nhưng tỷ lệ chặn hữu hạn có dao động như bảng;không ép các mẫu có cùng số slot chặn. CI ở bảng này dùng Student-t theo mission của cloud diagnostics,các hình hiệu năng dùng percentile bootstrap ghép cặp.','',
               '## Yếu tố mây có ảnh hưởng quan sát lớn nhất','',
               '| Phương án/đại lượng | Trục có span lớn nhất | Span trên dải đã thử |','|---|---|---:|']
    for method,metric in [('Stationary','K'),('Greedy','K'),('DP','K'),('DP','availability'),('DP-minus-Stationary','U'),('DP-minus-Greedy','U')]:
        best=max([r for r in effects if r['method']==method and r['metric']==metric],key=lambda r:r['span'])
        unit='percentage points' if metric=='availability' else 'bit/use';scale=100 if metric=='availability' else 1
        report.append(f'| {method}/{metric} | {best["axis"]} | {best["span"]*scale:.8g} {unit} |')
    report += ['', 'Span làmax(mean)−min(mean) trên đúng dải p/ell/rho của Stage B tại λref,không phải Sobol index,elasticity hoặc so sánh được chuẩn hóa theo độ rộng tham số. Không trộn xếp hạng cloud-only này với xếp hạng năm tham số Stage A. [Bảng đầy đủ](mobility/parameter_effects.csv).','',
               '## Quãng đường và penalty','',f'[PDF vector](figures/{NAMES[3]}.pdf) · [PNG350dpi](figures/{NAMES[3]}.png) · [CSV](figures/{NAMES[3]}_data.csv)','',
               'Figure B4 so quãng đường tại hai λ cố định. Với cùng reward và tập khả thi,quãng đường nghiệm DP không tăng khi λ tăng. Không áp đặt điều này cho Greedy;quãng đường không phải năng lượng đẩy đã hiệu chuẩn.','',
               '## Bảo đảm,provenance và giới hạn','',
               'Baseline hiện tại được tái lập đủ600 metric/path tại100 mission×2λ×3 phương án. Bộ cuối được kiểm tra độc lập về seed/common innovations,threshold mây,calibration theo mission-cluster SE,feasible path,Greedy current-slot,Bellman,objective,CI và điểm vẽ. Không nới dung sai sau kết quả.','',
               'Các kiểm tra calibration dùng chính100 mission đã chọn:mean blockage,latent/binary near/far spatial correlation và lag1 temporal product. Dung sai định trước là5SE theo mission+10⁻¹⁰;không lấy300.000 ô/slot làm mẫu độc lập. Tỷ lệ chặn thực nghiệm hữu hạn không bị ép bằng p danh định.','',
               'Nguồn chỉ tối ưu trên catalog hữu hạn,lưới hữu hạn,mây tổng hợp,DP/P2 offline;MI2D/Holevo homodyne chưa xác thực an toàn. Không có hiệu chuẩn năng lượng hoặc transit/reacquisition. Giữ frozen hash conflict và Objective C USER_STOPPED;không thay mô hình khoa học,bảo mật,cache,frozen,lifecycle,baseline/threshold;không final-test/held-out,external manuscript edit,commit/push.','',
               '[Metric từng mission](mobility/mission_metrics.csv) · [Mean/SD/median/CI](mobility/aggregate_statistics.csv) · [Paired gains](mobility/paired_improvements.csv) · [Cloud calibration](clouds/correlation_diagnostics.csv) · [Protocol](protocol.json) · [English captions](figure_captions_en.md) · [Validation](validation_report.md) · [Final receipt](validation/final_receipt.json)','']
    (OUT/'report_vi.md').write_text('\n'.join(report),encoding='utf-8',newline='\n')
    json_save(OUT/'findings.json',findings)
    print('RENDERED',len(NAMES),'figures;',len(points),'actual artist points; VI report and EN captions',flush=True)


if __name__=='__main__':main()
