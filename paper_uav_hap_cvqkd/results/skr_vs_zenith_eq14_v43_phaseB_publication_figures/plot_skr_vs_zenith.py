"""IEEE figure formatting from saved raw-rate CSVs only; no scientific imports."""
import ast
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fonts
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator, ScalarFormatter
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SOURCE = ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024'
SELECTION = ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/run.py'
PASS = 'CURRENTLY_VERIFIED_PASS'
SCHEMES = ['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']
LABELS = ['Uniform','Fixed MB','Optimized MB']
STYLES = [dict(color='#666666',linestyle='--'),
    dict(color='#0072B2',linestyle='-',marker='s'),
    dict(color='#007F73',linestyle='-',marker='o')]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write_json(name,value):
    (OUT/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def write_text(name,value): (OUT/name).write_bytes((value.rstrip()+'\n').encode('utf-8'))
def read_csv(path,required):
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        assert required <= set(reader.fieldnames or []), 'Missing columns: '+str(path)
        result=list(reader)
    return result


def protected_unchanged():
    for name,digest in read(OUT/'startup_manifest.json')['protected'].items():
        assert sha(ROOT.parent/name)==digest, 'Historical file changed: '+name


def load_and_validate():
    protected_unchanged()
    task=read(SOURCE/'protocol.json')
    assert sha(ROOT/task['physical_protocol_path'])==task['physical_protocol_sha256']
    physical=read(ROOT/task['physical_protocol_path'])
    assert task['correlation_policy']=='manuscript_eq14_direct'
    assert physical['physical']['Dr_m']==.30
    assert (physical['xi_ch'],physical['xi_det'],physical['beta'])==(.0186,.005,.95)
    for name,digest in read(SOURCE/'artifact_manifest.json')['files'].items():
        assert sha(SOURCE/name)==digest, 'Input experiment artifact changed: '+name
    angles=task['angles_deg']
    assert angles==list(range(61))
    required={'zenith_deg','ensemble_hash','family','K_raw','numerical_status',
        'source_evidence_class','result_scope','source_id','source_sha256','VA_hex','nu_raw_hex'}
    candidates=read_csv(SOURCE/'diagnostic_skr_61_angles.csv',required)
    selected=read_csv(SOURCE/'best_scheme_by_angle.csv',required|{'scheme'})
    assert len(candidates)==12932 and len(selected)==183
    pairs=set();groups={a:[] for a in angles}
    for row in candidates:
        a=float(row['zenith_deg']);assert a.is_integer() and int(a) in groups
        a=int(a);key=(a,row['source_id']);assert key not in pairs;pairs.add(key)
        assert row['numerical_status']==PASS, 'Saved candidate failure: '+str(key)
        assert row['result_scope']=='DIAGNOSTIC_ONLY'
        assert row['K_raw'] and math.isfinite(float(row['K_raw']))
        groups[a].append(dict(row,K_raw=float(row['K_raw'])))
    for a in angles:
        assert len(groups[a])==212
        assert {r['source_id'] for r in groups[a]}=={r['source_id'] for r in groups[0]}

    # Extract only the pure ranking function; importing its runner loads evaluators.
    tree=ast.parse(SELECTION.read_text(encoding='utf-8'))
    selection_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select')
    namespace=dict(SCHEMES=SCHEMES,STRICT={'VERIFIED_EXACT','VERIFIED_BY_ALTERNATIVE_EVIDENCE'},LABEL='DIAGNOSTIC_ONLY')
    exec(compile(ast.Module(body=[selection_node],type_ignores=[]),str(SELECTION),'exec'),namespace)
    select=namespace['select']
    lookup={(r['scheme'],int(float(r['zenith_deg']))):r for r in selected}
    assert len(lookup)==183 and {r['scheme'] for r in selected}==set(SCHEMES)
    matched=[]
    for a in angles:
        for best in select(groups[a],physical):
            stored=lookup[(best['scheme'],a)]
            assert stored['numerical_status']==PASS and stored['result_scope']=='DIAGNOSTIC_ONLY'
            for k in ['ensemble_hash','source_id','source_sha256','VA_hex','nu_raw_hex','C_hex','w_hex','source_evidence_class']:
                assert stored[k]==best[k], ('Selection identity mismatch',a,best['scheme'],k)
            for k in ['K_raw','C','w','VA','nu_raw']:
                assert float(stored[k]).hex()==float(best[k]).hex(), ('Saved value mismatch',a,k)
            matched.append(stored)
    series={s:[lookup[(s,a)] for a in angles] for s in SCHEMES}
    statistics={}
    expected=[(-.03074714646,60,[]),(.00006522377,0,list(range(6))),
        (.0007960878080861267,0,list(range(16)))]
    for s,label,(expected_max,expected_angle,expected_positive) in zip(SCHEMES,LABELS,expected):
        records=series[s];values=np.array([float(r['K_raw']) for r in records])
        index=int(np.argmax(values));positive=[a for a,k in zip(angles,values) if k>0]
        crossings=[[a,b] for a,b in zip(angles,angles[1:]) if (values[a]>0)!=(values[b]>0)]
        assert abs(float(values[index])-expected_max)<=5e-12
        assert angles[index]==expected_angle and positive==expected_positive
        statistics[label]=dict(maximum_raw_SKR=float(values[index]),maximum_angle_deg=angles[index],
            positive_sampled_angles_deg=positive,zero_crossing_brackets_deg=crossings,
            negative_samples=int(np.count_nonzero(values<0)),
            selected_source_evidence_counts=dict(Counter(r['source_evidence_class'] for r in records)))
    assert statistics['Fixed MB']['zero_crossing_brackets_deg']==[[5,6]]
    assert statistics['Optimized MB']['zero_crossing_brackets_deg']==[[15,16]]
    best=series[SCHEMES[2]][0]
    for k,v in dict(nu_raw=.30,VA=1.358333319784304,C=1.067911050328646,w=5.700303183579203e-10).items():
        assert float(best[k]).hex()==float(v).hex(),k
    validation=dict(status=PASS,result_scope='DIAGNOSTIC_ONLY',candidate_rows_read=len(candidates),
        selected_rows_matched=len(matched),angles_per_scheme=61,statistics=statistics,
        ranking_function_path=SELECTION.relative_to(ROOT).as_posix(),ranking_file_sha256=sha(SELECTION),
        ranking_function_sha256=hashlib.sha256(ast.get_source_segment(SELECTION.read_text(encoding='utf-8'),selection_node).encode()).hexdigest(),
        physical_protocol_sha256=task['physical_protocol_sha256'],
        expected_values_used_only_as_checks=True,negative_values_preserved=True,
        interpolation=False,smoothing=False,new_numerical_points=0,
        new_channel_evaluations=0,new_MI_evaluations=0,new_Holevo_evaluations=0,
        new_SKR_evaluations=0,new_Cw_computations=0,strict_Phase_B_ready=False)
    return series,validation


def configure_fonts():
    try: path=fonts.findfont('Times New Roman',fallback_to_default=False);family='Times New Roman'
    except ValueError: path=fonts.findfont('STIXGeneral',fallback_to_default=False);family='STIXGeneral'
    plt.rcParams.update({'font.family':'serif','font.serif':[family],'mathtext.fontset':'stix',
        'font.size':9,'axes.labelsize':9.5,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
        'legend.fontsize':8,'axes.linewidth':.7,'lines.linewidth':1.65,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
        'pdf.compression':9,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
    return dict(family=family,path=path,sha256=sha(Path(path)))


def draw(ax,series,zoom=False):
    for i,s in enumerate(SCHEMES):
        if zoom and i==0:continue
        records=[r for r in series[s] if not zoom or float(r['zenith_deg'])<=18]
        x=np.array([float(r['zenith_deg']) for r in records])
        y=np.array([float(r['K_raw']) for r in records])
        line,=ax.plot(x,y,label=LABELS[i],**STYLES[i],markersize=3.3,
            markerfacecolor='white',markeredgewidth=.8,markevery=1 if zoom else 5,zorder=3,clip_on=False)
        assert np.array_equal(line.get_xdata(),x) and np.array_equal(line.get_ydata(),y)
    ax.axhline(0,color='#444444',linestyle='--',linewidth=.8,zorder=2)
    ax.set(xlim=(0,18 if zoom else 60),xlabel='Zenith angle (deg)',ylabel='Secret key rate (bits/use)')
    ax.xaxis.set_major_locator(MultipleLocator(3 if zoom else 10))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.grid(color='#D7D7D7',linewidth=.45,alpha=.7)
    ax.tick_params(direction='out',length=3,width=.65)
    if not zoom:
        ax.legend(loc='center left',frameon=True,facecolor='white',edgecolor='#CCCCCC',framealpha=1)
        return
    low=min(float(r['K_raw']) for s in SCHEMES[1:] for r in series[s] if float(r['zenith_deg'])<=18)
    peak=float(series[SCHEMES[2]][0]['K_raw']);pad=.12*(peak-low)
    ax.set_ylim(low-pad,peak+pad)
    formatter=ScalarFormatter(useMathText=True);formatter.set_powerlimits((-4,-4));ax.yaxis.set_major_formatter(formatter)
    for a,b,i in [(5,6,1),(15,16,2)]:
        ax.axvspan(a,b,color=STYLES[i]['color'],alpha=.10,zorder=1)
        ax.annotate(f'sampled [{a}, {b}]',xy=((a+b)/2,0),
            xytext=(3 if i==1 else 11,.00022 if i==1 else .00012),ha='center',fontsize=7.7,
            color=STYLES[i]['color'],arrowprops=dict(arrowstyle='-',color=STYLES[i]['color'],lw=.65))
    ax.annotate(r'$K_{\max}='+f'{peak/1e-4:.5f}'+r'\times10^{-4}$',xy=(0,peak),
        xytext=(3.7,peak+pad*.35),fontsize=8.1,ha='left',
        arrowprops=dict(arrowstyle='-',color=STYLES[2]['color'],lw=.65))
    ax.legend(loc='lower left',frameon=True,facecolor='white',edgecolor='#CCCCCC',framealpha=1,
        title='MB schemes only',title_fontsize=7.8)


def export(fig,name,metadata):
    fig.canvas.draw()
    # Tight bounding boxes retain labels without shrinking the specified font sizes.
    fig.savefig(OUT/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.045,
        metadata={'Description':'DIAGNOSTIC_ONLY; saved raw SKR; source convergence evidence incomplete'})
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.045,metadata={
        'Title':'Secret key rate versus zenith angle','Subject':'DIAGNOSTIC_ONLY; saved raw SKR; source convergence evidence incomplete',
        'Keywords':'DIAGNOSTIC_ONLY, sampled angles, no new SKR computation','Creator':'Matplotlib saved-CSV renderer'})
    renderer=fig.canvas.get_renderer();bounds=[]
    for ax in fig.axes:
        bounds.append(list(ax.get_tightbbox(renderer).bounds))
    metadata[name]=dict(figsize_inches=list(fig.get_size_inches()),dpi=600,
        axes_tight_bounds_display_pixels=bounds,axes_titles=[ax.get_title() for ax in fig.axes])
    plt.close(fig)


def captions():
    limitation=('Available-catalog results are diagnostic, with incomplete source-convergence evidence '
        'for all positive rates.')
    common=(r'Positive samples span $0^\circ$--$5^\circ$ (Fixed MB) and '
        r'$0^\circ$--$15^\circ$ (Optimized MB); Uniform remains negative. ')
    bracket=(r'Shaded $[5^\circ,6^\circ]$ and $[15^\circ,16^\circ]$ intervals bracket sampled '
        'sign changes, not established continuous-angle thresholds. ')
    texts=[('skr_vs_zenith_publication',r'Saved raw SKR for Uniform, Fixed Maxwell--Boltzmann (MB), '
        r'and Optimized MB 256-QAM over $0^\circ$--$60^\circ$, sampled every $1^\circ$. '+common+limitation),
        ('skr_vs_zenith_zoom',r'Saved raw-SKR zoom for Fixed MB and Optimized MB over $0^\circ$--$18^\circ$ '
        r'on the $1^\circ$ grid; Uniform is omitted. '+common+bracket+limitation),
        ('skr_vs_zenith_two_panel',r'Saved raw SKR on the $1^\circ$ grid: (a) Uniform, Fixed MB, and '
        r'Optimized MB over $0^\circ$--$60^\circ$; (b) MB-only zoom over $0^\circ$--$18^\circ$. '
        +common+bracket+limitation)]
    blocks=['% DIAGNOSTIC_ONLY. Publication-quality formatting does not certify source convergence.',
        '% Each figure is a vector PDF with a corresponding 600-dpi PNG.']
    for name,caption in texts:
        kind='figure*' if name.endswith('two_panel') else 'figure'
        width=r'\textwidth' if kind=='figure*' else r'\columnwidth'
        blocks.append('\n'+f'\\begin{{{kind}}}[t]\n  \\centering\n  \\includegraphics[width={width}]{{{name}.pdf}}\n'
            f'  \\caption{{{caption}}}\n  \\label{{fig:{name}}}\n\\end{{{kind}}}')
    write_text('figure_captions.tex','\n'.join(blocks))


def main():
    series,validation=load_and_validate()
    validation['font']=configure_fonts()
    rendering={}
    for name,zoom in [('skr_vs_zenith_publication',False),('skr_vs_zenith_zoom',True)]:
        fig,ax=plt.subplots(figsize=(3.5,2.7),layout='constrained')
        draw(ax,series,zoom);export(fig,name,rendering)
    fig,axes=plt.subplots(1,2,figsize=(7.16,2.95),layout='constrained')
    for ax,zoom,label in zip(axes,[False,True],['(a)','(b)']):
        draw(ax,series,zoom)
        ax.text(.98,1.025,label,transform=ax.transAxes,ha='right',va='bottom',fontsize=9)
    export(fig,'skr_vs_zenith_two_panel',rendering)
    captions()
    protected_unchanged()
    validation['rendering']=rendering
    validation['script_sha256']=sha(Path(__file__))
    validation['historical_files_unchanged']=len(read(OUT/'startup_manifest.json')['protected'])
    write_json('figure_data_validation.json',validation)
    lines=['# Kiểm chứng hình SKR theo góc zenith','',
        '**CURRENTLY_VERIFIED_PASS cho dữ liệu/dựng hình; phạm vi khoa học vẫn DIAGNOSTIC_ONLY.**','',
        'Chỉ đọc hai CSV và report của namespace 61 góc đã seal; không import evaluator. '
        'Hàm `select` gốc được trích bằng AST và chỉ xếp hạng raw K đã lưu. '
        '12.932 candidate được kiểm tra; 183 lựa chọn khớp chính xác source identity, '
        'VA/nu/C/w và raw SKR binary64 với `best_scheme_by_angle.csv`. '
        'Mỗi scheme đủ 61 góc 0–60°, bước 1°; cùng pool 212 nguồn ở mọi góc.','',
        '| Scheme | Max raw SKR (bits/use) | Góc | Điểm dương đã lấy mẫu | Khoảng đổi dấu |',
        '|---|---:|---:|---|---|']
    for label,s in validation['statistics'].items():
        positive=s['positive_sampled_angles_deg'];span=f'{positive[0]}–{positive[-1]}°' if positive else 'Không có'
        intervals='; '.join(f'[{a}, {b}]°' for a,b in s['zero_crossing_brackets_deg']) or 'Không quan sát'
        lines.append(f"| {label} | {s['maximum_raw_SKR']:.17g} | {s['maximum_angle_deg']}° | {span} | {intervals} |")
    lines+=['','Các expected values trong task chỉ dùng làm consistency check (tolerance 5e−12 do bảng làm tròn); '
        'tọa độ hình lấy nguyên giá trị CSV. Đường nối trực tiếp các mẫu, không smooth, '
        'không tạo điểm số học, không nội suy giá trị thiếu và không clip raw K về 0. '
        'Hình đầy đủ giữ cả 183 mẫu; zoom chỉ lấy 19 mẫu 0–18° của mỗi MB scheme, '
        'được ghi rõ “MB schemes only” và caption. Các khoảng tô màu chỉ kẹp dấu trên lưới.','',
        f"Typography: {validation['font']['family']}; axis 9.5 pt, ticks 8.5 pt, legend 8 pt, "
        'line 1.65 pt; PNG 600 dpi và PDF vector. Hình đơn rộng 3.5 inch, '
        'hình hai panel rộng 7.16 inch trước tight cropping. Không có decorative title '
        'hoặc watermark lớn; DIAGNOSTIC_ONLY nằm trong caption/metadata.','',
        'Cấu hình số học/vật lý được giữ nguyên qua hash physical protocol. Không tính '
        'channel, MI, Holevo, C,w hay SKR mới. Không sửa production, manuscript, frozen '
        'spec hoặc source cache; không chạy historical verifier có phép tính số học.','',
        'Mọi raw K dương vẫn phụ thuộc INSUFFICIENT_EVIDENCE. Uniform thiếu nguồn '
        'nu_raw=0, VA=1.6249995399703647; không suy ra nghiệm tối ưu toàn miền. '
        'Strict Phase B vẫn BLOCKED do 73 nguồn pilot thiếu evidence hội tụ và một '
        'Uniform thiếu payload/receipt. UNVALIDATED_SECURITY_MODEL và '
        'NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.','',
        'Frozen-spec current/historical hash discrepancy đã có trong hồ sơ readiness, '
        'không được sửa hoặc bypass; dựng hình từ CSV không giải quyết blocker mô hình.','',
        f"{validation['historical_files_unchanged']} file lịch sử được bảo vệ đã giữ nguyên SHA256. "
        'Chi tiết dữ liệu: `figure_data_validation.json`; QA bản xuất PDF/PNG và '
        'kiểm tra cuối: `export_validation.json`. Script tái dựng tất cả hình chỉ từ '
        'CSV đã lưu; `figure_captions.tex` chứa ba caption tiếng Anh và snippets LaTeX.']
    write_text('figure_validation_report_vi.md','\n'.join(lines))
    print(json.dumps({k:validation[k] for k in ['status','result_scope','selected_rows_matched',
        'angles_per_scheme','new_SKR_evaluations','new_Cw_computations','historical_files_unchanged']},indent=2))


if __name__=='__main__':main()
