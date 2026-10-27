"""Render only saved final diagnostics; no numerical/source optimization."""
import csv
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT=Path(__file__).resolve().parent
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def fmt(x):return 'BLOCKED' if x is None else f'{x:.12g}'
def table(rows,fields):
    return '| '+' | '.join(fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'+''.join(
        '| '+' | '.join('BLOCKED' if r.get(k) is None else
            (fmt(r.get(k)) if isinstance(r.get(k),(float,int)) else str(r.get(k,''))) for k in fields)+' |\n' for r in rows)


def figures():
    plt.rcParams.update({'font.family':'serif','font.size':9,'axes.labelsize':10,'legend.fontsize':8,
        'axes.titlesize':10,'pdf.fonttype':42,'ps.fonttype':42,'lines.linewidth':1.4})
    target=OUT/'figures';target.mkdir(exist_ok=True)
    records=[]
    def canvas(title,xlabel):
        fig,ax=plt.subplots(figsize=(5.6,3.7),layout='constrained')
        ax.set(title=title,xlabel=xlabel,ylabel='Raw SKR (bit/use)',yscale='log')
        ax.grid(True,which='both',alpha=.24,linestyle=':')
        return fig,ax
    def curve(ax,rows,x,label,color,marker):
        rows=sorted(rows,key=lambda r:r[x])
        xx=np.array([r[x] for r in rows])
        yy=np.array([r['raw_SKR'] if r['raw_SKR'] is not None and r['raw_SKR']>0
            and r['validation_status']=='CURRENTLY_VERIFIED_PASS_SECURITY_PROVISIONAL' else np.nan for r in rows])
        assert not np.any(yy[np.isfinite(yy)]<=0)
        ax.plot(xx,yy,color=color,marker=marker,markersize=3.3,label=label)
        records.append(dict(label=label,positive=int(np.isfinite(yy).sum()),excluded=int(np.isnan(yy).sum()),
            channel_laws=sorted({r['channel_law'] for r in rows}),x_field=x))
        assert len(records[-1]['channel_laws'])==1
    def save(fig,stem):
        fig.savefig(target/(stem+'.png'),dpi=350)
        fig.savefig(target/(stem+'.pdf'))
        plt.close(fig)
    A=read('stage_A_final.json');secondary=read('secondary_zenith.json')
    fig,ax=canvas('Uniform 256-QAM: primary and secondary channels','Zenith angle (deg)')
    curve(ax,A,'zenith_deg','Primary Eq. (10), baseline: no positive points','0.45','s')
    curve(ax,secondary,'zenith_deg','Independent bounded law, improved optics','#0072B2','o')
    ax.set_xlim(0,30);ax.legend(loc='best')
    fig.get_layout_engine().set(rect=(0,0.1,1,0.9))
    fig.text(.5,.025,'Primary: 35 / 1.561 urad / 0.10 m; secondary: 10 / 0.5 urad / 0.03 m\n'
        'Divergence / jitter / position SD; receiver 30 cm. Security provisional.',
        ha='center',fontsize=7)
    save(fig,'fig1_uniform_vs_zenith')
    D=read('diameter_comparison.json')
    fig,ax=canvas('Uniform 256-QAM: matched geometry across apertures','Receiver diameter (m)')
    for law,label,color,marker in [
        ('manuscript43_Eq10_retained_0_to_1','Primary Eq. (10): PDF mass blocked','0.45','s'),
        ('power_conserving_random_width','Independent bounded law (secondary)','#0072B2','o')]:
        curve(ax,[r for r in D if r['channel_law']==law],'Dr_m',label,color,marker)
    ax.set_xticks([.3,.35,.4,.45,.5,.55,.6]);ax.legend(loc='best')
    fig.get_layout_engine().set(rect=(0,0.08,1,0.92))
    fig.text(.5,.025,'Zenith 0 deg; divergence 10 urad; jitter 0.5 urad; position SD 0.03 m.\n'
        'No rate assigned to failed PDFs. Security provisional.',ha='center',fontsize=7)
    save(fig,'fig2_uniform_vs_receiver_diameter')
    T=read('three_scheme_zenith.json')
    fig,ax=canvas('Independent bounded channel: three modulation schemes','Zenith angle (deg)')
    schemes=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']
    for scheme,color,marker in zip(schemes,['#0072B2','#D55E00','#009E73'],['o','s','^']):
        curve(ax,[r for r in T if r['scheme']==scheme],'zenith_deg',scheme,color,marker)
    ax.set_xlim(0,30);ax.legend(loc='best')
    fig.get_layout_engine().set(rect=(0,0.08,1,0.92))
    fig.text(.5,.025,'Same 30 cm receiver / 10 urad divergence / 0.5 urad jitter / 0.03 m position SD.\n'
        'Exact catalog selection; same v43 noise, homodyne. Security provisional.',ha='center',fontsize=7)
    save(fig,'fig3_three_scheme_bounded')
    (OUT/'plot_manifest.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
        positive_only=True,no_connection_across_invalid=True,one_law_per_curve=True,
        curves=records),indent=2)+'\n',encoding='utf-8')


def report():
    end=read('completion_receipt.json');raw=end['primary_best'];sec=end['secondary_best']
    if end['primary_positive_found']:raise ValueError('Primary conclusion changed; update report and figure labels before authoring')
    sec_all=end['secondary_best_all_tested']
    comparison=read('three_scheme_comparison.json')
    law_comparison=read('law_comparison.json')
    ablation=read('ablation.json');diameters=read('diameter_comparison.json')
    A=read('stage_A_final.json');B=read('stage_B_final.json');C=read('stage_C_final.json')
    sources=read('source_catalog.json');by_hash={c['ensemble_hash']:c for c in sources}
    sc=by_hash[sec['source_hash']]
    stage_rows=[]
    for name,rows in [('A',A),('B',B),('C',C)]:
        valid=[r for r in rows if r['raw_SKR'] is not None]
        if valid:stage_rows.append(dict(stage=name,**{k:max(valid,key=lambda r:r['raw_SKR'])[k]
            for k in ['Dr_m','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','VA','raw_SKR']}))
    c_initial=read('stage_C_initial.json')+read('stage_C_extension.json')+C
    per_d=[]
    for d in [.3,.35,.4,.45,.5,.55,.6]:
        rows=(read('stage_B_initial.json')+B) if d==.3 else [r for r in c_initial if r['Dr_m']==d]
        rows=list({r['context_id']:r for r in rows}.values());valid=[r for r in rows if r['raw_SKR'] is not None]
        best=max(valid,key=lambda r:r['raw_SKR']) if valid else {}
        per_d.append(dict(Dr_m=d,valid_contexts=len(valid),blocked_contexts=len(rows)-len(valid),
            best_raw_SKR=best.get('raw_SKR'),VA=best.get('VA'),zenith_deg=best.get('zenith_deg'),
            divergence_urad=best.get('divergence_urad')))
    bounded_ab=[r for r in ablation if r['channel_law']=='power_conserving_random_width']
    base=next(r for r in bounded_ab if r['ablation']=='all_improved')['raw_SKR']
    for row in bounded_ab:row['K_loss_on_reversion']=base-row['raw_SKR']
    ranked=sorted([r for r in bounded_ab if r['ablation'].startswith('revert_')],key=lambda r:-r['K_loss_on_reversion'])
    selected=list((OUT/'selected_validation').glob('*.json'))
    check_count=sum(len(json.loads(p.read_text(encoding='utf-8'))['validation']['checks']) for p in selected)
    source_note=('Các điểm mới yêu cầu đã có nguồn chính xác.' if not end['source_gaps'] else
        'Còn thiếu nguồn chính xác tại VA='+','.join(map(str,end['source_gaps']))+
        '; không được xem đây là tối ưu hoàn tất trên toàn đoạn [0.05,10].')
    text=f"""# Uniform 256-QAM — khảo sát SKR dương, manuscript-v43

## Kết quả chính và bảng parameter

**PDF Eq. (10) gốc: chưa tìm được Uniform SKR dương trong các điểm hợp lệ đã thử.**
Ứng viên mạnh nhất: K={fmt(raw['raw_SKR'])} bit/use tại Dr={raw['Dr_m']} m,
divergence={raw['divergence_urad']} µrad, jitter={raw['jitter_urad']} µrad,
σh={raw['sigma_h_m']} m, zenith={raw['zenith_deg']}°, VA={raw['VA']}.
Đây là kết quả âm, không thay bằng 0. Những PDF không đạt mass gate không có MI/Holevo/SKR.

**Mô hình bị chặn độc lập (secondary), tại receiver 30 cm: tìm được Uniform raw SKR dương
K={fmt(sec['raw_SKR'])} bit/use với receiver 30 cm.**
Kết quả này không chứng minh Uniform dương dưới Eq. (10) gốc.
Nó giữ đúng noise-v43, homodyne Gaussian effective/RR nhưng dùng một luật thu công suất khác,
được khai báo và suy ra riêng bên dưới. Không thay production model, không đổi tolerance.

| Parameter | Giá trị |
|---|---|
| HAP / UAV altitude | 20 km / 1 km, giữ cố định |
| Wavelength | 1550 nm |
| Atmospheric zenith transmittance | 0.92; không thay độ cao/profile |
| Wind / Cn² ground | 21 m/s / 1e-14 m^(-2/3), từ receiver30 |
| AoA half FOV / SD | 0.00625 rad / 0.0015 rad |
| Explicit outage atom P0 | 0.00016985667656141065 |
| Channel / detector excess noise | 0.0186 / 0.005 SNU |
| Separate detector efficiency | Không có eta_det trong phép tính v43 này |
| Reconciliation / β | Reverse reconciliation / 0.95 |
| AO / phase / boresight | OFF / OFF / 0 |
| Baseline Dr / full divergence / jitter / σh | 0.30 m / 35 µrad / 1.561 µrad / 0.10 m |
| Secondary best Dr / full divergence / jitter / σh | {sec['Dr_m']} m / {sec['divergence_urad']} µrad / {sec['jitter_urad']} µrad / {sec['sigma_h_m']} m |
| Secondary best zenith / slant length / VA | {sec['zenith_deg']}° / {sec['distance_km']} km / {sec['VA']} |
| Source energy / probabilities | VA=2 nbar; p=1/256 exactly |
| Uniform source coverage | {end['uniform_source_count']} authenticated exact points in requested VA domain |
| MB source coverage | 197 authenticated exact points, separate ensembles |
| Mass / MI / Holevo numerical tolerance | 1e-10 / 2e-10 / 2e-8 |

## Mô hình và công thức đang thực sự dùng

Với m1=E[η], mh=E[√η], M0 là tổng mass kể cả atom AoA:

\\[
T_f=m_h^2,\\quad
\\langle\\eta\\xi\\rangle=0.0186m_1+0.005M_0,\\quad
N=T_f\\xi_f=(m_1-T_f)V_A+0.0186m_1+0.005M_0.
\\]

Giữ quy ước giới hạn của ηξ tại outage như evaluator manuscript-v43 đã kiểm tra;
không thay bằng một detector plane mới. Phương sai homodyne là 1+N,
trung bình có điều kiện là 2√Tf Re(αk). Tính MI rời rạc thực 1D
bằng tích phân mixture Gaussian; không thay MI bằng Shannon capacity.
Các điểm được chọn được kiểm tra lại GH128, tích phân entropy đầu ra thích nghi,
256 ký hiệu so với 16 mức biên X, X/P và bất biến scaling cổ điển.

Covariance dùng a=1+VA, b=1+Tf VA+N và cùng Tf,N trong khoảng DBL:

\\[
Z\\in[2\\sqrt{{T_f}}C-\\sqrt{{2Nw}},2\\sqrt{{T_f}}C+\\sqrt{{2Nw}}]
\\cap[-Z_{{phys}},Z_{{phys}}],
\\quad Z_{{phys}}^2=\\min((a-1)(b+1),(a+1)(b-1)).
\\]

\\[
\\nu_{{1,2}}=\\frac{{\\sqrt{{(a+b)^2-4Z^2}}\\pm|a-b|}}{{2}},
\\quad \\nu_3=\\sqrt{{a(a-Z^2/b)}},
\\quad \\chi_{{BE}}=g((\\nu_1-1)/2)+g((\\nu_2-1)/2)-g((\\nu_3-1)/2).
\\]

g(x)=(x+1)log2(x+1)-x log2(x). Lấy max χ trên khoảng Z vật lý bằng solver số
và kiểm tra lưới 33/129, entropy độc lập 80/110 chữ số. Đây không phải bao
chứng nhận toàn cục bằng interval arithmetic. K=0.95 IAB−χBE, giữ mọi K âm.
Không clip eigenvalue hoặc sửa covariance. C,w thuộc đúng ensemble gắn source hash.

## Luật kênh: primary và secondary khác nhau ở đâu

Primary giữ nguyên Eq. (10), tích phân trên 0<η≤1 và atom P0 tại 0.
M0=P0+P1 C1 Q(χ²) được tính closed form và độc lập trong log η.
Mass η>1 được lưu riêng; nếu 1−M0>1e-10, rate bị chặn trước khi tối ưu VA.
Không renormalize, không clip η, không chuyển phần đuôi thành erasure.
Stage A giữ nguyên lỗi mass tại 0°–4°. Đổi Dr/divergence luôn tính lại w0,wL,
turbulence broadening, equivalent beam, pointing và atmospheric/slant geometry.

Secondary là luật Gaussian beam random-width bảo toàn công suất, đã có evaluator chẩn đoán
trong repository. Đặt B~Bernoulli(P1), S~Normal(−v/2,v),
W=w_eff exp(−S/2), R~Rayleigh(σs), các biến độc lập:

\\[
F(a,R,W)=F_{{\\chi'^2_2((2R/W)^2)}}((2a/W)^2),\\quad
\\eta=B\\eta_{{atm}}F(a,R,W),\\quad a=D_r/2.
\\]

Mỗi beam có tổng công suất 1, nên 0≤η≤ηatm≤1 và tổng probability đúng 1,
atom vẫn là P0. Đây là thu công suất tròn chính xác trong một luật random-width
được định nghĩa mới; không phải truncate/condition/renormalize Eq. (10).

\\[
m_1=P_1\\eta_{{atm}}\\,E_S[1-\\exp(-2a^2/(W^2+4\\sigma_s^2))],
\\]
\\[
m_h=P_1\\sqrt{{\\eta_{{atm}}}}\\,E_S\\int_0^\\infty
e^{{-x}}\\sqrt{{F_{{\\chi'^2_2(8\\sigma_s^2x/W^2)}}((2a/W)^2)}}\\,dx.
\\]

Tích phân GH32/64 khớp ở ứng viên dương; kiểm tra độc lập GH96×Legendre512
trên x∈[0,40], phần mass bỏ qua ≤exp(−40), sai khác moment dưới 1e-12.
Luật random-width chưa được hiệu chuẩn bằng phép đo turbulence/beam-wander;
đúng support và normalization không chứng minh đây là mô hình khí quyển thực chính xác.

Đối chiếu hai luật tại từng geometry cố định (không đổi noise hoặc nguồn trong một đánh giá):

{table(law_comparison,['physical_setting','channel_law','pdf_mass','mass_deficit','E_eta','E_sqrt_eta','VA','raw_SKR'])}

Nếu Eq. (10) thất bại ở geometry secondary tốt, không gán cho nó rate của secondary.

## Stage A/B/C — primary Eq. (10)

{table(stage_rows,['stage','Dr_m','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','VA','raw_SKR'])}

Stage A dùng 31 góc 0:1:30; coarse VA rồi lấy toàn bộ nguồn chính xác trong
các bracket cực đại cục bộ. Stage B screen 675 geometry ở 0/10/20°, tối đa
5 VA coarse cho kênh hợp lệ, full bank top16 và góc 0:1:20 tại 4 settings tốt nhất.
Đây là sàng lọc có chủ đích; không tối ưu liên tục toàn miền ở mọi geometry.
Stage C dùng 3 divergence lân cận settings B tốt, rồi mở rộng 60 µrad khi
aperture lớn làm mass gate khó đạt; góc fallback 40/50/60° không phải thay độ cao.
Không dùng điểm bị loại để kết luận một thiết kế có positive SKR.

{table(per_d,['Dr_m','valid_contexts','blocked_contexts','best_raw_SKR','VA','zenith_deg','divergence_urad'])}

Với Dr=0.60 m, chưa có geometry primary hợp lệ trong miền C đã thử;
không kết luận mọi divergence/góc khác đều bất khả thi. Aperture lớn hơn
không khắc phục được tự động giới hạn support của xấp xỉ PDF.
Mọi lựa chọn VA/nu là best exact-tested; không có global bound hoặc chứng nhận minimum liên tục.
Ở ứng viên primary mạnh nhất, βI={fmt(raw['beta_I_AB'])} còn χ={fmt(raw['chi_BE'])};
muốn K>0 phải cải thiện chênh lệch hơn {fmt(-raw['raw_SKR'])} bit/use.
Nếu giữ χ cố định thì MI phải vượt {fmt(raw['chi_BE']/.95)} bit/use; đây chỉ là
điều kiện đại số, không chứng minh có thể điều khiển MI độc lập với χ bằng VA/geometry.
Cần hoàn tất các nguồn còn thiếu và mở rộng có kiểm soát miền geometry/PDF hợp lệ
trước khi kết luận rộng hơn. Không giảm ξch/ξdet, đổi β hay đổi homodyne để tạo positive.

## Uniform dương và đối chiếu MB trên cùng kênh

{table(comparison,['channel_law','scheme','Dr_m','VA','nu_raw','I_AB','beta_I_AB','chi_BE','raw_SKR'])}

Secondary best Uniform tại Dr=30 cm: source hash {sec['source_hash']};
C={fmt(sc['C'])}, w={fmt(sc['w'])}; source payload {sc['source_path']}.
Primary best dùng source riêng ghi trong CSV và source_catalog.json.
Fixed MB cố định (nu_raw,VA)=(0.25,1.6249995399703647), ensemble hash
01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754.
Optimized MB chọn từ 197 nguồn xác thực; không lấy C,w của MB cho Uniform.

Gshaping(primary)={fmt(end['shaping_gain']['manuscript43_Eq10_retained_0_to_1'])} bit/use;
Gshaping(secondary)={fmt(end['shaping_gain']['power_conserving_random_width'])} bit/use.
Chỉ trừ các rate có cùng law/geometry/noise, không so chéo primary với secondary.

## Cải thiện nào có tác động lớn trong phép đối chiếu cục bộ?

Giữ geometry ứng viên secondary dương rồi trả từng parameter về baseline;
mỗi hàng đều chọn lại VA từ cùng nguồn chính xác:

{table(bounded_ab,['ablation','divergence_urad','jitter_urad','sigma_h_m','VA','raw_SKR','K_loss_on_reversion'])}

Trong phép đối chiếu này, mất mát lớn nhất khi {ranked[0]['ablation']},
ΔK={fmt(ranked[0]['K_loss_on_reversion'])} bit/use.
Đây là xếp hạng cục bộ giữa các bước thay đổi khác độ lớn và có tương tác,
không phải độ nhạy toàn cục hay chứng minh một parameter luôn quan trọng nhất.
Đường Dr trong diameter_comparison.csv giữ cố định mọi geometry còn lại.
Trong toàn bộ các điểm secondary đã thử, K lớn nhất là {fmt(sec_all['raw_SKR'])}
bit/use tại Dr={sec_all['Dr_m']} m, VA={sec_all['VA']}, zenith={sec_all['zenith_deg']}°,
full divergence={sec_all['divergence_urad']} µrad, jitter={sec_all['jitter_urad']} µrad,
σh={sec_all['sigma_h_m']} m. Điểm này khác với mục tiêu giữ receiver nhỏ 30 cm;
không mặc định khả thi về tải trọng. Nếu VA tốt nhất chạm nguồn VA lớn nhất đang có,
đỉnh theo VA vẫn chưa được bracket đầy đủ.

## Trả lời Q1–Q6

1. **Uniform có K dương?** Chưa tìm thấy với primary Eq. (10) gốc;
   có với secondary bounded, cùng quy ước noise-v43 và Gaussian-effective homodyne.
2. **Cấu hình nhỏ nhất đã thử cho kết quả dương?** Dr={sec['Dr_m']} m,
   full divergence={sec['divergence_urad']} µrad, jitter={sec['jitter_urad']} µrad,
   σh={sec['sigma_h_m']} m, zenith={sec['zenith_deg']}°, VA={sec['VA']},
   K={fmt(sec['raw_SKR'])}. Chỉ là nhỏ nhất trong aperture được thử, thuộc secondary.
3. **Giữ Dr=30 cm được không?** Được trong secondary; chưa có positive primary.
4. **Cải thiện nào lớn nhất?** Bảng ablation định lượng tác động cục bộ; phải cải thiện
   tracking/stabilization để dùng jitter 0.5 µrad và vị trí 3 cm.
   Không suy từ positive secondary sang primary hoặc từ aperture sang khả năng mang tải.
5. **MB còn lợi thế bao nhiêu?** Gshaping secondary={fmt(end['shaping_gain']['power_conserving_random_width'])}
   bit/use; primary={fmt(end['shaping_gain']['manuscript43_Eq10_retained_0_to_1'])} bit/use
   tại đúng geometry tương ứng, với cùng luật kênh cho mỗi phép trừ.
6. **Kết quả nào qua kiểm tra?** Có {len(selected)} context/source được kiểm tra chọn lại,
   {check_count} kiểm tra MI/Holevo/covariance đã lưu; mass gate áp dụng cho tất cả context.
   Positive secondary qua các kiểm tra số và support/normalization của chính luật đó,
   nhưng toàn bộ kết quả vẫn UNVALIDATED_SECURITY_MODEL.

## Giới hạn nguồn tính toán, kỹ thuật và bảo mật

{source_note}
Hai lần khởi động backend gmpy2 bị Windows Application Control chặn trước
khi tính C,w. Không vô hiệu hóa hoặc đi vòng policy. Fallback dùng backend Python chuẩn,
giữ nguyên full-support C4 và ladder 1050/1250/1450 chữ số, timeout 3600 s;
trạng thái và thời gian từng tác vụ nằm trong completion_receipt/source_attempts.
Không nội suy, không điền C,w/SKR cho điểm thiếu, không đổi precision để lấy positive.
Exact-source ở đây là nhánh full-support đã xác thực, không phải nghiệm giải tích
vô hạn chữ số. Worker gốc yêu cầu hai mức cuối resolve đủ rank 256 và
|Δx|≤1e-7+1e-6 max(|x1250|,|x1450|), x=C,w; receipt giữ nguyên các hàng precision.
Tolerance xác thực ensemble/VA và tiêu chí hội tụ C,w là hai kiểm tra khác nhau.

Div=10 µrad tương ứng w0≈0.098676 m, đường kính phát chứa 99% công suất
khoảng 0.2995 m ở HAP, tính theo cùng Gaussian optics.
Ở L=19 km, jitter 0.5 µrad cho dịch điểm 1σ=0.0095 m và
σs=√(σh²+(L θjt)²)=0.0314682379551 m khi σh=0.03 m.
Các SD và giả thiết độc lập của motion/jitter/AoA được giữ theo mô hình;
chưa có phép đo để xác nhận tương quan giữa chúng.
Receiver 30 cm và jitter/position cải thiện là giả thiết thiết kế, chưa có bằng chứng
khối lượng, công suất, bandwidth PAT hay tải trọng UAV. Đường Dr lớn không phải chứng nhận
thiết kế bay khả thi; không có dữ liệu phần cứng để bảo đảm yêu cầu này.

Các khoảng full-Z có kiểm tra số, chưa phải enclosure toàn cục. Gaussian effective
fading closure, quy ước noise tại outage, attack class/CSI, parameter estimation,
finite size, reconciliation thực và composable security còn chưa được chứng minh.
Giữ NOT_READY_FOR_PUBLICATION_SCALE_RUNS, ObjectiveC USER_STOPPED và blocker
frozen-hash: actual df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15,
khác historical expected 561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1.
Không đổi scientific source/production code/security functional/frozen spec/config hay cache cũ;
không training, test/held-out/publication evaluation, baseline/threshold approval, commit/push.

## Artifact và đọc hình

- candidate_comparison.csv: {end['candidate_rows']} hàng, gồm mọi source evaluation và
  context bị chặn; K âm giữ nguyên, rate thiếu để trống. source_catalog.json liên kết ensemble/payload hash.
  Có {end['candidate_failure_count']} source evaluation lỗi covariance/information, lưu riêng
  trong candidate_failures.json và có exclusion_reason trong CSV; không dùng làm positive.
- stage_A_final.csv: VA tốt nhất đã thử theo từng góc và lý do loại.
- diameter_comparison.csv: cùng zenith/divergence/jitter/position cho tất cả aperture;
  primary và secondary có cột channel_law tách biệt.
- three_scheme_comparison.csv, three_scheme_zenith.csv: cùng kênh/noise, fixedMB rõ nguồn.
- Figures 1–3: PNG350dpi/PDF vector, log-y chỉ K>0 đã kiểm tra;
  NaN tạo ngắt tại các khoảng âm/invalid. Figure 1 ghi riêng primary baseline không có positive
  và secondary cải thiện optics; không diễn giải đây là một đường dùng lẫn hai laws.
  Figure 2 có primary mass-blocked và secondary theo cùng geometry.
  Figure 3 chỉ secondary, 3 schemes cùng physical channel.
- selected_validation/, bounded_moment_validation.json, independent_bounded_validation.json,
  guard_checks.json và verification.json chứa kiểm tra; verify.py chỉ đọc artifact, không rerun số.

Các artifact lịch sử được kiểm hash từ startup_manifest trước và sau công việc.
Các hash ledger trong receipt cũ là snapshot lịch sử; không sửa receipt cũ khi cập nhật ledger
cho nhiệm vụ mới. Tái lập các phase vào namespace mới, không ghi đè các receipt đã hoàn tất.
"""
    (OUT/'report_vi.md').write_text(text,encoding='utf-8')
    # Add explicit source family to the all-candidate CSV, including MB comparisons.
    path=OUT/'candidate_comparison.csv'
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    for row in rows:
        c=by_hash.get(row['source_hash'])
        row['family']='Uniform' if c is None else c['family']
        row['nu_raw']='' if c is None else c['nu_raw']
    fields=list(rows[0])
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    (OUT/'README.md').write_text("""# Reproduction and read-only verification

Run from paper_uav_hap_cvqkd with .venv/Scripts/python.exe -X utf8 -B.
Read-only check: results/uniform_positive_skr_manuscript43_20261023/verify.py

Producer sequence (use a new isolated output namespace for reproduction):
source_job.py VA: historical GMP launcher, recorded OS policy failure.
source_python_job.py VA: unchanged full-support kernel/precision, standard MP Python backend.
search.py screen: prospective protocol Stage A/B/C and separate secondary screen.
complete_search.py extend: extra divergence60/raw normalization and selected checks.
complete_search.py finish: fresh available sources, comparisons and matched curves.
check_guards.py / independent_bounded.py: isolated boundary/independent moment checks.
write_outputs.py: saved data only; writes CSV source labels, report and three PNG/PDF pairs.

Do not rerun completed numerical phases or overwrite old caches/receipts.
No new package or production change. New exact sources are versioned under new_exact_source.
All maxima are best exact-tested; security remains provisional.
""",encoding='utf-8')


if __name__=='__main__':
    report();figures()
