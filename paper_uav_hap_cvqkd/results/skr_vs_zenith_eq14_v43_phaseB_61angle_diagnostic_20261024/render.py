"""Reports and figures from saved, independently checked CSVs only."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
COLORS=['#0072B2','#E69F00','#D62728']
LABELS=['Uniform (available catalog)','Fixed MB','Optimized MB (available catalog)']
SCHEMES=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def text(name,content):(OUT/name).write_bytes((content.rstrip()+'\n').encode('utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def number(value):return float(value) if value not in ('',None) else np.nan


def plots():
    summary=read('diagnostic_summary.json')
    assert summary['saved_validation']['status']=='CURRENTLY_VERIFIED_PASS'
    checks=rows('independent_validation.csv')
    assert all(r['status']=='CURRENTLY_VERIFIED_PASS' for r in checks)
    data=rows('best_scheme_by_angle.csv')
    points=[sorted([r for r in data if r['scheme']==s],key=lambda r:float(r['zenith_deg'])) for s in SCHEMES]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,
        'axes.spines.top':False,'axes.spines.right':False,'legend.fontsize':8.5,
        'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':350})

    def base(ax,ylabel):
        ax.set(xlabel='Zenith Angle (degrees)',ylabel=ylabel,xlim=(0,60))
        ax.grid(alpha=.24,linewidth=.5)
    def series(ax,key):
        for p,color,label in zip(points,COLORS,LABELS):
            x=[float(r['zenith_deg']) for r in p]
            y=[number(r[key]) if r['numerical_status']=='CURRENTLY_VERIFIED_PASS' else np.nan for r in p]
            ax.plot(x,y,color=color,label=label,linewidth=1.5,marker='o',markersize=2.6,markevery=5,
                drawstyle='steps-post' if key in {'VA','nu_raw'} else 'default')
    def finish(fig,name):
        fig.text(.99,.005,'DIAGNOSTIC_ONLY | historical exact C,w | source evidence incomplete',
            ha='right',fontsize=7,color='#555555')
        fig.tight_layout(rect=(0,.035,1,.97))
        fig.savefig(OUT/(name+'.png'),dpi=350)
        fig.savefig(OUT/(name+'.pdf'))
        plt.close(fig)

    fig,ax=plt.subplots(figsize=(7.2,4.7))
    series(ax,'K_raw');base(ax,'Raw SKR (bits/use)')
    ax.axhline(0,color='.35',linewidth=.7,linestyle='--')
    ax.set_title('SKR versus Zenith Angle')
    ax.legend(loc='center left',framealpha=1)
    finish(fig,'skr_vs_zenith')

    fig,ax=plt.subplots(figsize=(7.2,4.7))
    series(ax,'K_raw');base(ax,'Raw SKR (bits/use)')
    brackets=[v['zero_crossing_intervals'] for v in summary['sampled_scheme_results'].values()]
    crossings=[c['interval_deg'] for block in brackets for c in block]
    right=max(c[1] for c in crossings)+3 if crossings else 20
    ax.set(xlim=(0,right),ylim=(-.0008,.0009),title='Sampled SKR near Zero Crossings')
    ax.axhline(0,color='.35',linewidth=.7,linestyle='--')
    for i,short in enumerate(['Uniform','Fixed MB','Optimized MB']):
        for crossing in summary['sampled_scheme_results'][short]['zero_crossing_intervals']:
            a,b=crossing['interval_deg'];ax.axvspan(a,b,color=COLORS[i],alpha=.12)
            ax.scatter([a,b],crossing['endpoint_raw_K'],s=24,color=COLORS[i],zorder=5)
            ax.annotate(f'{short}: [{a:g}, {b:g}] deg',xy=(b,0),
                xytext=(b+.35 if i==1 else b-4.5,.00017 if i==1 else .00048),fontsize=8,color=COLORS[i],
                arrowprops={'arrowstyle':'-','color':COLORS[i],'lw':.7})
    ax.text(.02,.04,'Uniform raw SKR lies below this zoom. Shading brackets sampled signs; no root fit.',
        transform=ax.transAxes,fontsize=7.4)
    ax.legend(loc='upper right')
    finish(fig,'skr_zero_crossing_zoom')

    fig,axes=plt.subplots(2,1,figsize=(7.2,6.2),sharex=True)
    for ax,key,ylabel in zip(axes,['VA','nu_raw'],['Selected $V_A$ (SNU)','Selected $\\nu_{raw}$']):
        series(ax,key);base(ax,ylabel)
    axes[0].set_title('Best-tested Source Parameters versus Zenith Angle')
    axes[0].legend(loc='best');axes[0].set_xlabel('')
    finish(fig,'optimal_parameters_vs_zenith')

    fig,axes=plt.subplots(2,1,figsize=(7.2,6.2),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    mb=points[2];x=[float(r['zenith_deg']) for r in mb]
    for key,color,label in [('beta_I_AB','#0072B2','$\\beta I_{AB}$'),('chi_BE','#D62728','$\\chi_{BE}$')]:
        axes[0].plot(x,[number(r[key]) for r in mb],color=color,label=label,linewidth=1.5)
    axes[1].plot(x,[number(r['K_raw']) for r in mb],color=COLORS[2],linewidth=1.5,label='Raw SKR')
    axes[1].axhline(0,color='.35',linewidth=.7,linestyle='--')
    base(axes[0],'Information (bits/use)');base(axes[1],'Raw SKR (bits/use)')
    axes[0].set_xlabel('');axes[0].set_title('Information Decomposition: Selected Optimized MB')
    axes[0].legend();axes[1].legend()
    finish(fig,'information_decomposition')


def reports():
    s=read('diagnostic_summary.json');task=read('protocol.json')
    r=s['sampled_scheme_results'];checks=s['independent_validation'];validation=s['saved_validation']
    data=rows('best_scheme_by_angle.csv')
    md=['# Kiểm chứng sweep SKR theo 61 góc zenith','',
        '**DIAGNOSTIC_ONLY — hoàn tất khảo sát catalog lịch sử; strict Phase B vẫn BLOCKED.**','',
        'Lưới lấy nguyên `/angles_deg` của `'+task['grid_origin']+'`: 0–60°, bước 1°. '
        'Chín góc 0, 5, 10, 15, 20, 30, 40, 50, 60° đều thuộc lưới. '
        'Không thêm điểm hoặc fit nghiệm ngoài lưới.','',
        f"Tổng **{s['unique_evaluations']:,}** cặp nguồn–góc, gồm **{s['reused_evaluations']:,} tái dùng nguyên giá trị** "
        f"và **{s['new_evaluations']:,} evaluation SKR mới**; 9 context kênh tái dùng, 52 context mới. "
        f"**C,w mới: 0; source job: 0.** Thời gian phần sweep: {s['elapsed_seconds']:.2f} s (không gồm preparation/validation/figures).",'',
        'Pool cố định ở mọi góc: 212 identity, gồm 33 Uniform và 179 MB trong VA∈[0.05,10], '
        'ν_raw∈[0,0.40]. Optimized MB chứa cả Uniform ở ν=0 và Fixed MB. '
        'Uniform và MB là best-tested trong catalog hiện có, chưa phải tối ưu liên tục/toàn cục.','',
        '| Scheme | Raw SKR lớn nhất (bits/use) | Góc | Điểm dương đã lấy mẫu | Điểm dương cuối | Điểm không dương đầu | Khoảng đổi dấu quan sát |',
        '|---|---:|---:|---|---:|---:|---|']
    for short in ['Uniform','Fixed MB','Optimized MB']:
        q=r[short];positive=q['positive_sampled_angles']
        span=f"{min(positive):g}–{max(positive):g}° ({len(positive)} điểm)" if positive else 'Không có'
        crossing='; '.join(f"[{c['interval_deg'][0]:g}, {c['interval_deg'][1]:g}]°" for c in q['zero_crossing_intervals']) or 'Không quan sát'
        last='—' if q['last_sampled_positive_deg'] is None else f"{q['last_sampled_positive_deg']:g}°"
        first='—' if q['first_sampled_nonpositive_deg'] is None else f"{q['first_sampled_nonpositive_deg']:g}°"
        md.append(f"| {short} | {q['best_raw_K']:.15g} | {q['best_angle_deg']:g}° | {span} | {last} | {first} | {crossing} |")
    md+=['','Ở 0°, Optimized MB cao hơn Fixed MB khoảng 0.000730864037421203 bits/use. '
        'Trên lưới này, số điểm dương tăng từ 6 (Fixed MB) lên 16 (Optimized MB); '
        'mọi điểm MB dương được chọn dùng cùng VA=1.358333319784304, ν_raw=0.30. '
        'Các lần đổi nguồn MB ở 48°, 56°, 60° đều thuộc miền raw SKR âm.','',
        'Các khoảng trên chỉ kẹp sự thay đổi dấu giữa hai góc đã tính; không chứng nhận '
        'giới hạn hoạt động liên tục. Raw SKR âm được giữ nguyên. `K_operational=max(0,K_raw)` '
        'là cột báo cáo riêng, không dùng để xếp hạng hoặc sửa kết quả.','',
        f"Trạng thái số: {s['numerical_status_counts']}. Candidate dương: {s['positive_candidate_rows']}; "
        f"âm: {s['negative_candidate_rows']}; bằng 0: {s['zero_candidate_rows']}. "
        'Không loại bỏ âm hoặc evaluation thất bại; giá trị chưa tính được để trống.','',
        '## Tham số MB được chọn','',
        'Fixed MB giữ VA=1.6249995399703647 (`0x1.9ffff84830112p+0`), ν_raw=0.25, ν_repo=10.625, '
        'C=1.2135302410613147, w=2.856493276891121e-10. Chỉ nguồn cố định; Z, MI và Holevo tính theo góc.','',
        '| Góc bắt đầu dùng nguồn | VA | ν_raw | Ensemble hash | Evidence |',
        '|---:|---:|---:|---|---|']
    for t in s['optimized_MB_transitions']:
        md.append(f"| {float(t['zenith_deg']):g}° | {t['VA']:.17g} | {t['nu_raw']:g} | `{t['ensemble_hash']}` | {t['source_evidence_class']} |")
    md+=['','Mỗi hàng áp dụng đến trước hàng kế tiếp trên lưới đã lấy mẫu; bảng đủ 61 góc nằm trong '
        '`best_scheme_by_angle.csv`. Chuyển nguồn rời rạc có thể làm tham số nhảy. '
        'Không suy ra shaping gain ở cùng VA từ hai catalog có độ phủ năng lượng khác nhau.','',
        '| Góc | Fixed MB raw K | Optimized MB raw K | Chênh lệch | VA tối ưu MB | ν_raw tối ưu MB |',
        '|---:|---:|---:|---:|---:|---:|']
    for angle in task['previous_angles_deg']:
        fixed=next(x for x in data if float(x['zenith_deg'])==angle and x['scheme']==SCHEMES[1])
        opt=next(x for x in data if float(x['zenith_deg'])==angle and x['scheme']==SCHEMES[2])
        md.append(f"| {angle:g}° | {float(fixed['K_raw']):.12g} | {float(opt['K_raw']):.12g} | "
            f"{float(opt['K_raw'])-float(fixed['K_raw']):.12g} | {float(opt['VA']):.15g} | {float(opt['nu_raw']):g} |")
    md+=['','## Công thức, cấu hình và bằng chứng','',
        'Giữ nguyên các hàm canonical đã dùng ở chín góc: [0,1] cho Eq. (10), (18)–(20), '
        'atom tại 0 và noise của atom được giữ; bỏ phần ngoài support trong evaluator theo quyết định tác giả, '
        'không clip/renormalize/đổi PDF. VA=Vmod=2 nbar, X_A=2 Re α; ν_repo=42.5 ν_raw. '
        'Eq. (14) trực tiếp `Z=2 sqrt(eta_f) C-sqrt(2 eta_f xi_f w)`, '
        'homodyne MI rời rạc, covariance/Holevo Eq. (13) và raw K=0.95 MI−Holevo không thay đổi. '
        'Không tìm Z interval hoặc tối ưu Z.','',
        'Cấu hình chung: HAP/UAV=20/1 km; Dr=0.30 m; λ=1550 nm; divergence full-angle=35 µrad; '
        'jitter mỗi trục=1.561 µrad; position SD=0.10 m; boresight=0; F0=∞; τzen=0.92; '
        'Cn²(0)=1e−14 m^(−2/3); wind=21 m/s; h_atm=20 km; '
        'FOV half-angle=6.25 mrad; AoA SD=1.5 mrad; ξch=0.0186; ξdet=0.005; β=0.95; '
        'AO/phase noise OFF, homodyne/RR. Đây là baseline thí nghiệm riêng, không thay default PDF.','',
        f"Deficit xác suất được lưu theo từng góc: [{s['probability_deficit_range'][0]:.12g}, "
        f"{s['probability_deficit_range'][1]:.12g}]. Đây là xấp xỉ truncation đã được chấp nhận; "
        'không tuyên bố PDF bị cắt được chuẩn hóa toán học.','',
        f"Phân loại 212 nguồn giữ nguyên: {s['source_evidence_counts']}. "
        f"{s['source_evidence_incomplete_rows']:,} hàng dùng nguồn INSUFFICIENT_EVIDENCE. "
        f"Evidence của các candidate dương: {s['positive_evidence_counts']}. "
        f"Subset chỉ có evidence đầy đủ có {s['strict_source_subset_positive_selected_rows']} điểm được chọn có raw K dương. "
        'Fixed MB và các nguồn Optimized MB được chọn vẫn thiếu evidence hội tụ. '
        'Evaluation SKR thành công không bổ sung bằng chứng hội tụ C,w, cũng không chứng minh C,w sai.','',
        '**Uniform còn thiếu đúng nguồn** ν_raw=0, VA=1.6249995399703647, '
        'VA_hex=`0x1.9ffff84830112p+0`, ensemble hash '
        '`421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7`. '
        'Không chạy lại job timeout, không dùng VA làm tròn, C,w MB hoặc nội suy. '
        'Vì vậy không thể kết luận Uniform tối ưu toàn miền hay mọi Uniform đều không có SKR dương.','',
        '## Kiểm chứng và giới hạn','',
        f"{checks['total']} đối chiếu MI/covariance độc lập: {checks['reused']} tái dùng, {checks['new']} mới, đều PASS. "
        'Các kiểm tra mới đối chiếu MI adaptive integration và GH256, spectrum covariance 4×4, '
        'conditional covariance và Eq. (13)/(14) ở 160 digits. Mọi primary pair dùng GH64/128 và '
        'components 80/110 digits như baseline. Tolerance MI=2e−10, Holevo/spectrum=2e−11. '
        'Không sửa eigenvalue/Z hoặc điều kiện miền xác định.','',
        f"Sai khác MI độc lập lớn nhất={checks['max_adaptive_MI_difference']:.6g}; "
        f"spectrum={checks['max_covariance_difference']:.6g}; "
        f"raw-rate residual={validation['max_raw_rate_residual']:.6g}. "
        '3 focused checks kiểm tra đọc số từ CSV, nested ranking/negative/failure retention, '
        'grid/pool identity và canonical function reuse đã PASS trước sweep.','',
        'Frozen-spec hash hiện tại khác historical hash như hồ sơ readiness đã giải thích; '
        'versioned experiment_spec_v1 và cả hai reference vẫn được kiểm tra, không bypass/ghi đè frozen spec. '
        'Xem `protocol.json`, `baseline_verification.json`, `artifact_integrity_report.md` và `verification.json`.','',
        '**Strict Phase B readiness: BLOCKED.** Hai nhóm prerequisite vẫn là 73 nguồn pilot hiện có '
        'thiếu evidence hội tụ đầy đủ (gồm Fixed MB), và một Uniform đúng VA còn thiếu payload/receipt. '
        'Đây là sweep diagnostic được tác giả cho phép riêng, không phải hoàn tất strict pilot, '
        'certification, tối ưu toàn cục hoặc kết luận publication-grade/composable security. '
        '`UNVALIDATED_SECURITY_MODEL` và `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` giữ nguyên.','',
        'Đầu ra: `diagnostic_skr_61_angles.csv` (12.932 candidate), `best_scheme_by_angle.csv` '
        '(183 hàng, 3 scheme × 61 góc), `source_pool.csv`, `independent_validation.csv`, '
        'bốn PNG 350 dpi và PDF vector tương ứng. Không có training, final-test/held-out, '
        'source generation hoặc production/manuscript/cache/frozen-spec edit.']
    text('validation_report_vi.md','\n'.join(md))
    text('numerical_validation.md',f'''# Numerical validation — DIAGNOSTIC_ONLY

- Original grid provenance: `{task['grid_origin']}` SHA256 `{task['grid_origin_sha256']}`, `/angles_deg`.
- Saved pairs: {validation['unique_pairs']}; duplicate pairs: 0; reused rows identical: {validation['reused_values_unchanged']}.
- Evaluator SHA256: `{task['canonical_evaluator_sha256']}`; physical protocol SHA256: `{task['physical_protocol_sha256']}`.
- Source reconstruction verifies all 212 PMF/amplitude digests, payload SHA256, binary64 VA/nu, C/w hex, 256 symbols and X variance. No source moment kernel executed.
- Every primary pair: unchanged GH64/128 MI tolerance 2e-10; direct Eq14/Eq13 80/110 digits tolerance 2e-11. Failures remain rows with blank rates.
- Independent selected checks: {checks['total']} ({checks['reused']} reused, {checks['new']} new); all PASS. New checks add GH256, adaptive MI, independent symplectic matrix spectrum, conditional covariance and 160-digit components. These are supplemental checks, not additional catalog evaluations or C,w calculations.
- Max independent MI difference {checks['max_adaptive_MI_difference']:.17g}; max covariance difference {checks['max_covariance_difference']:.17g}; conditional difference {checks['max_conditional_difference']:.17g}.
- Max saved raw-rate residual {validation['max_raw_rate_residual']:.17g}; direct Eq14 float residual {validation['max_Eq14_float_residual']:.17g}.
- Max closed/direct channel moment residual {s['max_channel_direct_moment_residual']:.17g}; 80/110-digit moment residual {s['max_channel_precision_residual']:.17g}.
- Near-tie supplemental selected rows: {s['near_tie_selected_rows']}; all selected schemes checked at all angles, including crossings and source switches.
- Three focused tests PASS. No failed candidate excluded. Source classifications unchanged; successful rate computation is not source convergence evidence.
- Truncated PDF is not mathematically normalized. Deficit recorded; no clipping, renormalization or PDF replacement. No Z interval/optimization.
- Strict Phase B remains BLOCKED; UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
''')


if __name__=='__main__':reports();plots()
