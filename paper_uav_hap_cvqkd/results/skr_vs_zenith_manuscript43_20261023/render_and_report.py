"""Figure and Vietnamese report from saved, checked sweep rows; no evaluator."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator,NullFormatter
import numpy as np

OUT=Path(__file__).resolve().parent
LABELS=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def fmt(value):return 'Không có' if value is None else f'{value:.12g}'
def ranges(intervals):return '; '.join(str(a)+'°' if a==b else str(a)+'–'+str(b)+'°' for a,b in intervals) or 'Không có'


def main():
    if (OUT/'final_receipt.json').exists() or (OUT/'figure_receipt.json').exists():
        raise FileExistsError('Preserve completed figure')
    summary=read('summary.json');protocol=read('protocol.json')
    with (OUT/'skr_vs_zenith.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    line_data=[];all_positive=[]
    with plt.rc_context({'font.family':'DejaVu Serif','font.size':11,'axes.labelsize':12,
        'axes.titlesize':14,'legend.fontsize':9,'pdf.fonttype':42,'ps.fonttype':42,
        'axes.linewidth':.8,'xtick.direction':'in','ytick.direction':'in'}):
        fig,ax=plt.subplots(figsize=(6.8,4.5),layout='constrained')
        for label,color,marker in zip(LABELS,['#1f77b4','#ff7f0e','#2ca02c'],['o','s','^']):
            data=sorted([x for x in rows if x['scheme']==label],key=lambda x:int(x['zenith_deg']))
            xx=np.array([int(x['zenith_deg']) for x in data])
            yy=np.array([float(x['SKR']) if x['valid_point']=='True' and x['SKR'] and float(x['SKR'])>0 else np.nan for x in data])
            assert len(xx)==61 and np.array_equal(xx,np.arange(61))
            valid_indices=np.flatnonzero(np.isfinite(yy))
            marker_indices=np.unique(np.r_[valid_indices[::3],valid_indices[-1:]]).astype(int).tolist()
            ax.plot(xx,yy,color=color,marker=marker,markersize=3.6,markevery=marker_indices or None,
                linewidth=1.7,label=label)
            all_positive.extend(yy[np.isfinite(yy)].tolist())
            line_data.append(dict(scheme=label,positive_points=int(np.isfinite(yy).sum()),
                excluded_angles=xx[~np.isfinite(yy)].tolist(),excluded_points_rendered_as='NaN gaps',
                legend_label=label))
        ax.set(title='SKR versus Zenith Angle',xlabel='Zenith Angle (deg)',ylabel='Secret Key Rate (bits/use)')
        ax.set_yscale('log');ax.set_xlim(0,60);ax.set_xticks(np.arange(0,61,10))
        if all_positive:
            ax.set_ylim(min(all_positive)*.72,max(all_positive)*1.65)
        else:
            ax.set_ylim(1e-6,1e-1)
            ax.text(.5,.48,'No positive valid SKR points',transform=ax.transAxes,ha='center',va='center')
        if line_data[0]['positive_points']==0 and all_positive:
            ax.text(.025,.035,'Uniform: no positive valid points',transform=ax.transAxes,fontsize=8.5,color='.35')
        ax.yaxis.set_major_locator(LogLocator(base=10))
        ax.yaxis.set_minor_locator(LogLocator(base=10,subs=np.arange(2,10)*.1))
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.grid(True,which='major',linestyle='--',linewidth=.6,color='.80')
        ax.grid(True,which='minor',linestyle=':',linewidth=.4,color='.88')
        ax.tick_params(which='both',top=True,right=True)
        ax.legend(loc='upper right',framealpha=.95,edgecolor='.8')
        fig.savefig(OUT/'skr_vs_zenith.png',dpi=350)
        fig.savefig(OUT/'skr_vs_zenith.pdf',metadata={'Title':'SKR versus Zenith Angle',
            'Subject':'Finite exact-source catalog; homodyne Gaussian-effective manuscript43 diagnostic; no secure-default claim'})
        plt.close(fig)
    table='| Scheme | Số điểm dương | Max raw SKR (bits/use) | Góc max | Khoảng dương trên grid1° |\n| --- | --- | --- | --- | --- |\n'
    for label in LABELS:
        x=summary['schemes'][label]
        table+='| '+label+' | '+str(len(x['positive_angles']))+' | '+fmt(x['maximum_raw_SKR'])+' | '+fmt(x['maximum_angle_deg'])+'° | '+ranges(x['positive_intervals_deg'])+' |\n'
    raw_winner=max((s for s in LABELS if summary['schemes'][s]['maximum_raw_SKR'] is not None),
        key=lambda s:summary['schemes'][s]['maximum_raw_SKR'],default=None)
    peaks='| Scheme | VA tại peak | nu_raw tại peak | Source hash |\n| --- | --- | --- | --- |\n'
    for label in LABELS:
        peak=summary['schemes'][label]['maximum_source']
        peaks+='| '+label+' | '+('Không có | Không có | Không có' if peak is None else
            fmt(peak['V_mod_or_VA'])+' | '+fmt(peak['nu_raw'])+' | '+peak['source_hash'])+' |\n'
    mb_positive=[x for x in rows if x['scheme']==LABELS[2] and x['valid_point']=='True']
    decreasing=all(float(b['SKR'])<float(a['SKR']) for a,b in zip(mb_positive,mb_positive[1:]))
    trend='SKR của Optimized MB giảm theo góc trên khoảng dương.' if decreasing and len(mb_positive)>1 else 'Xem từng giá trị raw trong CSV để theo dõi thay đổi theo góc.'
    body=f'''# SKR theo góc zenith — manuscript43, receiver30

Đã quét đủ **61 góc0°–60°,bước1°**, lưu183 dòng cho ba scheme. Hình PNG350dpi và vectorPDF dùng đúng title/labels/legend yêu cầu,trục log và line+marker. Không có file ảnh tham chiếu trong đính kèm hiện tại; styling theo mô tả đã cung cấp.

## Kết quả

{table}

Scheme có peak raw cao nhất trong khảo sát: **{raw_winner or 'Không có scheme đánh giá được'}**. Đây là so sánh trong catalog exact đã có,không là chứng minh optimum liên tục hoặc toàn cục. Góc maximum chỉ xác định trên grid1°. Khoảng dương chỉ gồm các góc đạt kiểm tra số học và K>0,không ngoại suy qua khoảng loại.

{trend} Optimized MB tốt nhất tại cả56 góc có PDF đạt gate. Fixed MB chỉ có một điểm dương nên hình biểu diễn bằng marker riêng; Uniform giữ legend theo yêu cầu nhưng không vẽ các giá trị âm. Cực đại tại5° chỉ là maximum trong các điểm đủ điều kiện đánh giá; chưa thể so sánh rate với0°–4° bị BLOCKED.

{peaks}

Tổng {summary['positive_plotted_points']} điểm được vẽ. Các góc bị loại do PDF normalization: **{summary['PDF_failed_angles']}**. Candidate-source failures: {summary['candidate_failures']}; selected numerical-check failures: {summary['selected_numerical_failures']}. Raw SKR âm vẫn giữ nguyên trongCSV; không zero clipping. valid_point và plot_point nghĩa là đủ điều kiện xuất hiện trên trục log. numerically_valid riêng cho biết điểm âm có tính hợp lệ số học hay không. NaN dùng để ngắt đường tại điểm bị loại,không nối xuyên các khoảng đó.

## Tham số và evaluator

| Đại lượng | Giá trị | Nguồn |
| --- | --- | --- |
| HAP/UAV | 20/1km | receiver30_configuration_verification_20261023/protocol.json |
| Dr / wavelength | .30m /1550nm | receiver30 và actual optical factory |
| Full divergence / jitter | 35µrad /1.561µrad | receiver30 overrides |
| Position SD / boresight | .1m per axis /0m | receiver30; Rayleigh pointing |
| tau_zen / atmosphere | .92 /tau_zen^sec(zenith) | preserved actual channel code |
| HV wind / ground coefficient | 21m/s /1e-14m^(-2/3) | preserved HV primitives |
| AoA half-FOV / angular SD | 6.25mrad /1.5mrad | preserved P0 formula |
| beta /xi_ch /xi_det | .95 /.0186 /.005SNU | task.txt và protocol.json |
| Detection / reconciliation | real1D homodyne /reverse | Gaussian effective MI |
| Fixed MB | nu_raw=.25,VA=1.6249995399703647 | current receiver30 exact source |
| Optimized Uniform | best trong36 authenticated Uniform VA points | source_catalog.csv |
| Optimized MB | best trong197 authenticated MB(nu_raw,VA) points | source_catalog.csv |
| Source units | VA=2nbar,X=2Re(alpha) | giữ nguyên source/cache convention |
| AO /phase | OFF /OFF | receiver30 historical assumptions |

Không dùng eta_det trong bất kỳ curve nào. Không dùng random-width surrogate hay historical pooled MI. channel_at_angle và optical factory tái tính L,wL,w_eff,Gd,rawRytov,sigma_s,A0,w_eq,atmospheric transmittance cho từng góc; hai HV integrals được gọi lại theo cùng geometry. AtomP0 được bảo toàn.

Với m1=E[eta],mh=E[sqrt(eta)],Tf=mh²:

    E[eta*xi] = .0186*m1 + .005*M0
    N = (m1-Tf)*VA + E[eta*xi]
    xi_f = N/Tf
    sigma_N² = 1+N
    T_Holevo = Tf
    a = 1+VA; b = 1+Tf*VA+N
    Z± = 2*sqrt(Tf)*C ± sqrt(2*N*w)
    nu3_homodyne = sqrt(a*(a-Z²/b))

Cùng T,N và exact source ở MI/bound/covariance/Holevo. Source catalog được xác thực hash và payload trước sweep. Không nội suy C,w hoặc SKR; không newAP và không ghi cache mới. Optimization là exhaustive argmax rawK trong tập exact đã khai báo. Scheme legend giữ nguyên yêu cầu; từ “Optimized” ở đây nghĩa best exact-tested trong catalog. Giá trị nằm trên biên catalog không phải chứng minh optimum theo VA/nu liên tục.

## Loại điểm và kiểm tra

Mass tolerance1e-10 được giữ từ audit trước,không điều chỉnh theo dấu SKR. Góc0 tái lập deficit1.056995513649377e-10; PDF lognormal-product bị thiếu mass do retained support[0,1]. Không renormalize,clipping,chuyển tail sang atom hoặc thay law. Tại góc failed mass,không chạy source optimization/MI/Holevo; rate để trống/BLOCKED,không phải0. Optimized VA/nu để trống khi chưa thể chọn nguồn; Fixed MB vẫn giữ pair đã chỉ định.

Từng angle checkpoint trong angles/ lưu optical coefficients,M0,m1,mh,closed/direct quadrature,upper tail,candidate ranks/failures và selected checks. Mọi candidate được kiểm tra covariance/symplectic/entropy/capacity; selected sources có GH64/128,adaptive MI,256/16,X/P,scaling,16conditional density integrals,full-Z33/129,entropy80/110 và independent quantum matrix checks.

PNG/PDF được render từ đúng CSV đã lưu. No negative/invalid point trên log-axis. source_catalog.csv,protocol.json,startup_manifest.json,execution_history.json,sweep_receipt.json,figure_receipt.json và final_receipt.json giữ producer/input/output hashes. verify.py chỉ đọc saved artifacts; không import evaluator hoặc chạy lại optimization.

Không khẳng định secure default,finite-key/composable security,hardware validation hoặc global optimum. Numeric full-Z max không là rigorous interval enclosure. Gaussian effective MI là moment-matched approximation,không phải exact conditional likelihood của fading. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy và ObjectiveC USER_STOPPED. Hình “publication-friendly” nói về trình bày,không phải lifecycle approval.

Không sửa production code,frozen model,old results hoặc exact caches; không training/test/heldout/publication evaluation,production baseline/threshold approval hay commit/push. Old ledger hashes là snapshot lịch sử; numerical artifacts trước vẫn được bảo vệ bằng hash.
'''
    (OUT/'report_vi.md').write_text(body,encoding='utf-8')
    save('figure_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',renderer_sha256=sha(Path(__file__)),
        CSV_sha256=sha(OUT/'skr_vs_zenith.csv'),PNG_sha256=sha(OUT/'skr_vs_zenith.png'),
        PDF_sha256=sha(OUT/'skr_vs_zenith.pdf'),plot_type='one axes,line+markers,log_y',curves=line_data,
        positive_values_rendered=len(all_positive),negative_or_invalid_values_rendered=0,PNG_dpi=350,
        PDF_vector=True,legend_location='upper right',labels=LABELS))
    print('FIGURE/REPORT COMPLETE',len(all_positive),'positive points',flush=True)


if __name__=='__main__':main()
