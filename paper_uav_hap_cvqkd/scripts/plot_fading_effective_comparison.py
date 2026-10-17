"""Layout-only scheme comparison from verified numerical tables."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from src.binary_cloud_skr import read_csv


def plot(output):
    if saved.read_json(output/'final_validation.json')['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Verified saved data required')
    rows=read_csv(output/'scheme_legacy_updated_comparison.csv')
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.spines.right':False,'axes.spines.top':False})
    fig,axes=plt.subplots(1,2,figsize=(7.16,3.7));all_zero=True
    for ax,metric,title in zip(axes,('average_skr_bits_per_use','availability'),('Mean usable SKR (bits/use)','Threshold availability')):
        selected=[r for r in rows if r['scenario_id']=='0' and r['family']=='MB' and r['metric']==metric]
        selected.sort(key=lambda r:r['scheme'])
        if [r['scheme'] for r in selected]!=['S1','S2','S3','S4']:raise ValueError('Incomplete comparison')
        before=np.array([float(r['legacy_mean']) for r in selected]);after=np.array([float(r['updated_mean']) for r in selected])
        if not np.isfinite(before).all() or not np.isfinite(after).all() or (after<0).any():raise ValueError('Invalid usable metrics')
        all_zero &= bool((after==0).all());x=np.arange(4)
        ax.bar(x-.18,before,.34,label='Legacy');ax.bar(x+.18,after,.34,label='Moment-effective')
        if (after==0).all():ax.scatter(x+.18,after,color='#ff7f0e',marker='_',s=70,linewidths=2,zorder=4)
        ax.set(xticks=x,xticklabels=['S1','S2','S3','S4'],title=title);ax.grid(axis='y',alpha=.15)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,1.0))
    if all_zero:fig.text(.5,.84,'Moment-effective: all zero; no mobility SKR gain claimed',ha='center',fontsize=9)
    fig.subplots_adjust(left=.09,right=.99,bottom=.14,top=.72,wspace=.28)
    directory=output/'figures';fig.savefig(directory/'scheme_comparison.pdf');fig.savefig(directory/'scheme_comparison.png',dpi=300);plt.close(fig)
    saved.save(output/'scheme_figure_layout_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',numerical_evaluations=0,
        source_data_sha256=saved.digest(output/'scheme_legacy_updated_comparison.csv'),producer_sha256=saved.digest(Path(__file__)),
        output_sha256={p:saved.digest(directory/p) for p in ('scheme_comparison.pdf','scheme_comparison.png')},all_updated_default_MB_metrics_zero=all_zero))



def supplement_report(output):
    import csv,json,math
    old=ROOT/'results/binary_cloud_skr_20261015'
    prior=next(r for r in read_csv(old/'clear_winners.csv') if r['family']=='MB' and r['position_index']=='44')
    updated=next(r for r in read_csv(output/'clear_winners.csv') if r['family']=='MB' and r['position_index']=='44')
    moments=saved.read_json(output/'clear_channel_states.json')[44]['moments']
    table=[]
    for name,key in [('Mean T',None),('Effective T','T_eff'),('Fading variance',None),('Effective excess noise','xi_eff'),
                     ('I_AB','I_AB'),('chi_BE','chi_BE'),('Signed raw K','SKR'),('Usable K','K_star'),('Optimal nu_raw','nu_raw'),('Optimal V_A','V_A')]:
        if name=='Mean T':a=b=moments['mean_eta']
        elif name=='Fading variance':a=b=moments['mean_eta']-moments['mean_sqrt_eta']**2
        else:a=float(prior[key]);b=float(updated[key])
        if not math.isfinite(a) or not math.isfinite(b):raise ValueError('Invalid reference comparison')
        table.append(dict(quantity=name,legacy=a,updated=b))
    saved.write_csv(output/'reference_optimized_comparison.csv',table)
    base_path=output/'report_generated_before_supplement.md'
    if not base_path.exists():base_path.write_text((output/'FADING_EFFECTIVE_REPORT_VI.md').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    text=base_path.read_text(encoding='utf-8')
    text+='\n## P1 tối ưu tại vị trí tham chiếu44\n\nBảng này cho argmax raw trong catalog; cặp nguồn hai bên khác nhau. Bảng fixed-source trước đó mới cô lập riêng thay đổi evaluator.\n\n| Quantity | Legacy optimum | Updated raw optimum |\n|---|---:|---:|\n'
    for row in table:text+=f"| {row['quantity']} | {row['legacy']:.12g} | {row['updated']:.12g} |\n"
    text+='\nKhi tất cả raw maxima âm, nu/VA mới chỉ là cặp ít âm nhất trong catalog. Không có cấu hình vận hành tạo khóa được xác lập từ các giá trị usable0 này; không suy rộng thành kết luận bất khả thi cho mọi nguồn hoặc mọi protocol.\n\n'
    data=read_csv(output/'scheme_legacy_updated_comparison.csv')
    text+='## So sánh S1–S4 ở cấu hình cloud mặc định\n\nMỗi ô là legacy → updated, mean trên cùng100 mission. Availability dùng K_min=.001 bits/use.\n\n| Source | Scheme | Mean SKR | Availability | Flight m | Penalized objective |\n|---|---|---:|---:|---:|---:|\n'
    for family in ('MB','Uniform'):
        for scheme in ('S1','S2','S3','S4'):
            fields=[]
            for metric in ('average_skr_bits_per_use','availability','total_flight_distance_m','penalized_objective_bits_per_use'):
                row=next(r for r in data if r['scenario_id']=='0' and r['family']==family and r['scheme']==scheme and r['metric']==metric)
                fields.append(format(float(row['legacy_mean']),'.8g')+' → '+format(float(row['updated_mean']),'.8g'))
            text+='| '+family+' | '+scheme+' | '+' | '.join(fields)+' |\n'
    text+='\nVới lambda=0 và mọi usable rate=0, tất cả quỹ đạo feasible có cùng objective0; quỹ đạo đứng yên trả về là tie-breaking của DP. Không diễn giải flight0 thành lợi ích vật lý/propulsion energy hoặc một optimum quỹ đạo duy nhất.\n'
    history=output/'historical_MC_comparison.json'
    if history.exists():
        h=saved.read_json(history);m=h['historical_pooled_fading_MC'];n=h['updated_effective_gaussian'];se=m['standard_error']
        text+='\n## Đối chiếu chính xác Monte Carlo lịch sử\n\n[Artifact kiểm tra](historical_MC_comparison.json) xác nhận cùng nguồn nu=.165/VA=5.5, ensemble hash và cùng luật vật lý với ideal reference20261013. Đây là nguồn khác với fixed reference nu=.17/VA5.046875 ở đầu báo cáo.\n\n'
        text+=f"Pooled-mixture MC lịch sử: I_AB={m['I_AB']:.12g}, SE={se:.12g}, N={m['samples']}, K_raw={m['K_raw']:.12g}. Updated moment-Gaussian tại đúng nguồn đó: I_AB={n['I_AB']:.12g}, chi_BE={n['chi_BE']:.12g}, K_raw={n['SKR']:.12g}. Nó tái lập nhánh Gaussian approximation lịch sử với residual K={h['residuals']['K_raw']:.3g}.\n\n"
        text+='Sai khác MC/Gaussian ở đây là khác likelihood pooled-fading so với AWGN moment approximation, kèm sampling uncertainty. MC cũ không đạt mục tiêu SE=.002 và không được chạy lại trong task này; không nâng nó thành CURRENTLY_VERIFIED_PASS cho mixture/security. Khác biệt này cũng khác E[K(T)] statewise CSI ở diagnostic512 mẫu mới. Không có bound chặt cho approximation error hoặc bảo mật fading đầy đủ.\n'
    text+='\nPostprocessing hình/bảng: scripts/plot_fading_effective_comparison.py; chỉ đọc dữ liệu đã verified, không tính lại source/MI/Holevo hoặc sửa generator/DP. Chạy sau --stage report để nhận layout cuối. Các lỗi ban đầu và lần dừng vì khóa checkpoint được giữ trong attempts/ và logs; journal resume cùng producer/input, không bỏ điểm thất bại hay dùng K legacy thay thế.\n'
    (output/'FADING_EFFECTIVE_REPORT_VI.md').write_text(text,encoding='utf-8',newline='\n')
    import re
    canonical=re.sub(r'\]\((?!https?://|\.\./)([^)]+)\)',r'](../results/fading_effective_binary_cloud_20261016/\1)',text)
    (ROOT/'docs/FADING_EFFECTIVE_SKR_REPORT_VI.md').write_text(canonical,encoding='utf-8',newline='\n')
    receipt=saved.read_json(output/'report_receipt.json')
    receipt['report_sha256']=saved.digest(output/'FADING_EFFECTIVE_REPORT_VI.md')
    receipt['canonical_report_sha256']=saved.digest(ROOT/'docs/FADING_EFFECTIVE_SKR_REPORT_VI.md')
    receipt['postprocess_producer_sha256']=saved.digest(Path(__file__))
    receipt['postprocessing_scope']='layout repair and audited tables from already verified outputs; no numerical recomputation'
    receipt['reference_optimized_comparison_sha256']=saved.digest(output/'reference_optimized_comparison.csv')
    receipt['output_sha256']={p.relative_to(output).as_posix():saved.digest(p) for p in (output/'figures').iterdir() if p.is_file()}
    saved.save(output/'report_receipt.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'results/fading_effective_binary_cloud_20261016');args=parser.parse_args();plot(args.output);supplement_report(args.output)
