"""Stage A figure/report continuation using authenticated saved statistics only."""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FixedLocator, ScalarFormatter

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
METHODS = ('Stationary', 'Greedy', 'DP')
FIGURES = (
    ('A1', 'fig_A1_positions_objective_skr', 'J', 'Main'),
    ('A2', 'fig_A2_positions_unavailability', 'J', 'Main'),
    ('B', 'fig_B_speed_sensitivity', 'speed', 'Main'),
    ('C', 'fig_C_cloud_probability_sensitivity', 'probability', 'Main'),
    ('D', 'fig_D_duration_sensitivity', 'horizon', 'Supplementary'),
    ('E', 'fig_E_spatial_correlation_sensitivity', 'spatial', 'Supplementary'),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def save_csv(name, values):
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def build():
    if (OUT / 'validation_receipt.json').exists():
        raise FileExistsError('Completed review is immutable; use verify_review.py')
    startup = json.loads((OUT / 'startup_manifest.json').read_text(encoding='utf-8'))
    assert sha(BASE / 'validation/final_receipt.json') == startup['base_receipt_sha256']
    receipt = json.loads((BASE / 'validation/final_receipt.json').read_text(encoding='utf-8'))
    assert receipt['status'] == 'CURRENTLY_VERIFIED_PASS'
    for name, digest in receipt['artifact_sha256'].items():
        assert sha(BASE / name) == digest, name
    summary = {(r['case_id'], int(r['lambda_index']), r['method']): r for r in rows(BASE / 'existing_data/aggregate_statistics.csv')}
    paired = {(r['case_id'], int(r['lambda_index']), r['baseline'], r['metric']): r for r in rows(BASE / 'existing_data/paired_improvements.csv')}
    members = rows(BASE / 'case_membership.csv')
    def axis(name):
        return sorted([r for r in members if r['axis'] == name], key=lambda r: float(r['value']))
    def stat(case, method, key, li=1):
        return float(summary[case, li, method][key])
    def pair(case, baseline, key, li=1):
        return float(paired[case, li, baseline, 'U'][key])
    def endpoints(name, key):
        mm = axis(name)
        return stat(mm[0]['case_id'], 'DP', key), stat(mm[-1]['case_id'], 'DP', key)
    mission_rows = rows(BASE / 'existing_data/mission_metrics.csv')
    metrics_by_mission = {(r['case_id'], r['lambda_index'], r['realization_id'], r['method']): r for r in mission_rows}
    positive_dp = [r for r in mission_rows if r['method'] == 'DP' and int(r['lambda_index']) == 1]
    lower_k = sum(float(r['K']) < float(metrics_by_mission[r['case_id'], r['lambda_index'], r['realization_id'], 'Greedy']['K']) - 1e-12 for r in positive_dp)
    d0 = stat('base', 'DP', 'D_mean', 0)
    d1 = stat('base', 'DP', 'D_mean')
    k0 = stat('base', 'DP', 'K_mean', 0)
    k1 = stat('base', 'DP', 'K_mean')
    metrics = {
        'baseline_DP_U_gain_over_P2_percent': pair('base', 'Stationary', 'ratio_of_means_percent'),
        'baseline_DP_U_gain_over_Greedy_percent': pair('base', 'Greedy', 'ratio_of_means_percent'),
        'baseline_DP_distance_saving_over_Greedy_percent': 100 * (1 - d1 / stat('base', 'Greedy', 'D_mean')),
        'DP_distance_reduction_lambda0_to_ref_percent': 100 * (1 - d1 / d0),
        'DP_SKR_loss_lambda0_to_ref_percent': 100 * (1 - k1 / k0),
        'DP_SKR_lower_than_Greedy_missions_lambda_ref': lower_k,
        'distinct_case_missions_lambda_ref': len(positive_dp),
        'DP_J10_to_100_U_increase_percent': 100 * (endpoints('J', 'U_mean')[1] / endpoints('J', 'U_mean')[0] - 1),
        'DP_J10_to_100_K_increase_percent': 100 * (endpoints('J', 'K_mean')[1] / endpoints('J', 'K_mean')[0] - 1),
        'DP_J20_U_fraction_of_J100_percent': 100 * stat('J_20', 'DP', 'U_mean') / stat('base', 'DP', 'U_mean'),
        'DP_speed15_to_25_U_increase_percent': 100 * (stat('speed_25', 'DP', 'U_mean') / stat('base', 'DP', 'U_mean') - 1),
        'DP_speed20_to_25_distance_change_m': stat('speed_25', 'DP', 'D_mean') - stat('speed_20', 'DP', 'D_mean'),
        'p08_DP_U_gain_over_P2_percent': pair('probability_0p8', 'Stationary', 'ratio_of_means_percent'),
        'p08_DP_U_gain_over_Greedy_percent': pair('probability_0p8', 'Greedy', 'ratio_of_means_percent'),
        'p08_DP_delta_U_over_P2': pair('probability_0p8', 'Stationary', 'mean'),
        'p08_DP_delta_U_over_P2_ci95_low': pair('probability_0p8', 'Stationary', 'ci95_low'),
        'p08_DP_delta_U_over_P2_ci95_high': pair('probability_0p8', 'Stationary', 'ci95_high'),
    }
    save_json('review_metrics.json', metrics)
    save_csv('review_metrics.csv', [dict(metric=k, value=v) for k, v in metrics.items()])

    points = []
    with plt.rc_context({'font.family': 'serif', 'font.size': 8, 'axes.labelsize': 9, 'axes.linewidth': .7, 'pdf.fonttype': 42}):
        fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.25))
        fig.subplots_adjust(left=.085, right=.985, bottom=.25, top=.77, wspace=.55)
        labels = {'J': 'Candidate positions J', 'speed': 'UAV speed limit\n(m/s)', 'probability': 'Cloud-blockage\nprobability'}
        for panel, (ax, name) in enumerate(zip(axes, ('J', 'speed', 'probability')), 1):
            mm = axis(name)
            x = [float(r['value']) for r in mm]
            bounds = []
            for baseline, color, marker, ls in (('Stationary', 'tab:blue', 'o', '-'), ('Greedy', 'tab:orange', 's', '--')):
                data = [paired[r['case_id'], 1, baseline, 'U'] for r in mm]
                y, lo, hi = ([float(r[k]) for r in data] for k in ('mean', 'ci95_low', 'ci95_high'))
                line = ax.plot(x, y, color=color, marker=marker, linestyle=ls, lw=1.8, ms=4.8, mfc='white', mew=1,
                               label='DP minus ' + ('P2' if baseline == 'Stationary' else 'Greedy'))[0]
                ax.fill_between(x, lo, hi, color=color, alpha=.12, lw=0)
                for i, (xx, yy) in enumerate(zip(line.get_xdata(), line.get_ydata())):
                    points.append(dict(panel=panel, axis=name, case_id=mm[i]['case_id'], baseline=baseline, lambda_index=1,
                                       x=float(xx), y=float(yy), ci95_low=lo[i], ci95_high=hi[i]))
                bounds += lo + hi
            ax.set_xlabel(labels[name])
            ax.set_title(('(a) Candidate set', '(b) Speed constraint', '(c) Cloud blockage')[panel - 1], fontsize=9, pad=8)
            ax.set_ylabel('Mean paired objective gap\n(bits/use)')
            formatter = ScalarFormatter(useMathText=True)
            formatter.set_powerlimits((-5, -5))
            formatter.set_useOffset(False)
            ax.yaxis.set_major_formatter(formatter)
            ax.set_xticks(x)
            if name == 'J':
                plt.setp(ax.get_xticklabels(), rotation=35, ha='right')
            if name == 'speed':
                ax.set_xticks([0, 5, 10, 15, 20, 25])
            span = max(bounds) - min(0, min(bounds))
            ax.set_ylim(min(0, min(bounds)) - .04 * span, max(bounds) + .12 * span)
            ax.set_xlim(min(x) - .05 * (max(x) - min(x)), max(x) + .05 * (max(x) - min(x)))
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
            ticks = ax.get_xticks()
            ax.xaxis.set_minor_locator(FixedLocator([(a + b) / 2 for a, b in zip(ticks, ticks[1:])]))
            ax.grid(color='.84', lw=.5)
            ax.grid(which='minor', color='.94', lw=.35)
            ax.set_axisbelow(True)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=2, frameon=False, bbox_to_anchor=(.53, .99))
        fig.text(.53, .035, '100 paired missions; pointwise bootstrap 95% CI; fixed λref = 9.46803 × 10⁻⁶ bits/use', ha='center', fontsize=7)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for ax in axes:
            for artist in (ax.xaxis.label, ax.yaxis.label, ax.title, ax.yaxis.get_offset_text(), *ax.get_xticklabels()):
                box = artist.get_window_extent(renderer)
                assert box.x0 >= 0 and box.y0 >= 0 and box.x1 <= fig.bbox.x1 and box.y1 <= fig.bbox.y1, artist.get_text()
        save_json('render_metadata.json', dict(points=len(points), dpi=350, panels=[dict(xlim=list(ax.get_xlim()), ylim=list(ax.get_ylim())) for ax in axes],
                                              input_sha256=sha(BASE / 'existing_data/paired_improvements.csv'), no_new_bootstrap=True))
        for suffix in ('pdf', 'png'):
            fig.savefig(OUT / ('fig_S1_paired_objective_gaps.' + suffix), dpi=350, facecolor='white')
        plt.close(fig)
    save_csv('fig_S1_paired_objective_gaps_data.csv', points)
    figdir = '../../existing_data/figures/'
    report = [
        '# Stage A — Rà soát hình và bản thảo báo cáo', '',
        'UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.', '',
        'Phần bổ sung từ dữ liệu đã lưu. Giữ nguyên sáu hình, CSV, nguồn P1 và quỹ đạo gốc. Không chạy solver, evaluator vật lý, sinh mây, bootstrap mới hoặc Stage B.', '',
        '## Kết quả nên dẫn trước', '',
        f'Ở cấu hình mặc định và λref=9.468026677248516×10⁻⁶, DP tăng objective trung bình **{metrics["baseline_DP_U_gain_over_P2_percent"]:.3f}% so với P2** và **{metrics["baseline_DP_U_gain_over_Greedy_percent"]:.3f}% so với Greedy**, đồng thời đi ít hơn Greedy **{metrics["baseline_DP_distance_saving_over_Greedy_percent"]:.2f}%**. Đây là so sánh offline P2/DP với Greedy chỉ đọc trạng thái hiện tại, chưa cô lập hiệu ứng thông tin tương lai.', '',
        '| Phương án | K (×10⁻⁴ bit/use) | U (×10⁻⁴ bit/use) | D (m) | Availability (%) |',
        '|---|---:|---:|---:|---:|',
    ]
    for method in METHODS:
        report.append(f'| {method} | {stat("base",method,"K_mean")*1e4:.6f} | {stat("base",method,"U_mean")*1e4:.6f} | {stat("base",method,"D_mean"):.3f} | {stat("base",method,"availability_mean")*100:.3f} |')
    report += ['', '| So sánh tại λref | ΔU (bit/use) | CI95% ghép cặp | Gain U (%) và CI95% | U lớn hơn / hòa / nhỏ hơn (mission) |',
               '|---|---:|---|---|---|']
    for baseline in METHODS[:2]:
        r = paired['base', 1, baseline, 'U']
        report.append(f'| DP−{baseline} | {float(r["mean"]):.8g} | [{float(r["ci95_low"]):.8g}, {float(r["ci95_high"]):.8g}] | {float(r["ratio_of_means_percent"]):.3f} [{float(r["ratio_ci95_low"]):.3f}, {float(r["ratio_ci95_high"]):.3f}] | {r["strict_positive"]} / {r["ties"]} / {r["negative"]} |')
    report += [
        '', 'CI lấy trực tiếp từ bootstrap 20.000 whole-mission resamples đã lưu, seed 20261020. Đây là CI pointwise trên 100 mission ghép cặp; chưa hiệu chỉnh nhiều so sánh và không phải mức tin cậy bảo mật lượng tử.', '',
        '## Đánh đổi khi dùng mobility penalty', '',
        f'Với DP mặc định, λ0→λref giảm quãng đường **{d0:.3f}→{d1:.3f} m ({metrics["DP_distance_reduction_lambda0_to_ref_percent"]:.2f}%)**, trong khi SKR giảm **{metrics["DP_SKR_loss_lambda0_to_ref_percent"]:.3f}%**. Availability giảm 100→99,9%. Các tỷ lệ này là chênh lệch giữa mean đã lưu; không gán thêm CI cho chênh lệch xuyên λ.', '',
        f'U_DP không thấp hơn hai baseline ở từng mission trong bộ dữ liệu. Riêng K_DP thấp hơn K_Greedy ở **{lower_k}/{len(positive_dp)}** cặp cấu hình–mission tại λref (dùng dung sai 10⁻¹²). Vì vậy chỉ được mô tả DP tối ưu **U**, không nói DP luôn có SKR cao hơn trong mọi mission.', '',
        '## Sáu hình: thông điệp và vị trí trong bản thảo', '',
        '| Hình | Vai trò | Kết quả và kết luận có thể dùng | Giới hạn cần giữ |',
        '|---|---|---|---|',
        f'| [A1]({figdir}fig_A1_positions_objective_skr.pdf) | Chính | J10→100: DP K +{metrics["DP_J10_to_100_K_increase_percent"]:.2f}%, U +{metrics["DP_J10_to_100_U_increase_percent"]:.2f}%; J20 đạt {metrics["DP_J20_U_fraction_of_J100_percent"]:.2f}% U tại J100. Thêm vị trí giúp mở rộng lựa chọn. | J10 có 8 thành phần liên thông/7 điểm cô lập; từ J20 kết nối. Không cô lập mật độ khỏi kết nối. |',
        f'| [A2]({figdir}fig_A2_positions_unavailability.pdf) | Chính | Ở λref, J10→100: unavailability DP 7,4→0,1%; P2 9,47→2,23%; Greedy 29,57→1,27%. DP có mean thấp nhất tại các điểm thử. | Availability là S>0; thuật toán không trực tiếp tối ưu chỉ số này. |',
        f'| [B]({figdir}fig_B_speed_sensitivity.pdf) | Chính | Tốc độ15→25 m/s chỉ tăng U_DP {metrics["DP_speed15_to_25_U_increase_percent"]:.5f}%; lợi ích biên nhỏ ở vùng này. | Tại v=0, DP=P2; gap với Greedy do chọn điểm đầu offline, không phải di chuyển. D20→25 m/s giảm {abs(metrics["DP_speed20_to_25_distance_change_m"]):.3f} m. |',
        f'| [C]({figdir}fig_C_cloud_probability_sensitivity.pdf) | Chính | p0,1→0,8: hiệu năng tuyệt đối giảm nhưng U_DP/P2 gain tăng; tại p0,8 là {metrics["p08_DP_U_gain_over_P2_percent"]:.2f}% so với P2 và {metrics["p08_DP_U_gain_over_Greedy_percent"]:.2f}% so với Greedy. | Chỉ năm mức đã lưu. Không có đỉnh nội miền được chứng minh; không ngoại suy p>0,8. |',
        f'| [D]({figdir}fig_D_duration_sensitivity.pdf) | Bổ sung | Nt5→30: D_DP 12,48→172,43 m; gain U/P2 0,092→3,075% dù K tuyệt đối giảm nhẹ. | U dùng average reward và total distance; Nt thay đổi cả horizon lẫn mức phạt tương đối, không cô lập lookahead. |',
        f'| [E]({figdir}fig_E_spatial_correlation_sensitivity.pdf) | Bổ sung | ell50→1000 m: K/A giảm nhưng gain U/P2 tăng 1,46→5,96%; P2 suy giảm mạnh hơn. | ell là tương quan tiềm ẩn, không phải bán kính mây đo được; không có bảo đảm đơn điệu. |',
        '', 'Giữ bốn hình chính **A1, A2, B, C** đúng ưu tiên đã chọn trước batch. D/E cung cấp kiểm tra cơ chế, không bị loại vì kết quả trái kỳ vọng.', '',
        '## Hình phụ S1: đọc gap thay vì độ chồng đường', '',
        '[PDF vector](fig_S1_paired_objective_gaps.pdf) · [PNG 350 dpi](fig_S1_paired_objective_gaps.png) · [38 điểm và CI gốc](fig_S1_paired_objective_gaps_data.csv)', '',
        '![Objective gaps](fig_S1_paired_objective_gaps.png)', '',
        'S1 giữ ba phép quét J/tốc độ/p và hai đường ΔU=mean(U_DP−U_P2), mean(U_DP−U_Greedy). Không dùng phép trừ hai CI riêng lẻ; band lấy đúng CI của chênh lệch ghép cặp. Không thêm điểm mô phỏng hoặc làm trơn.', '',
        'Đường DP−Greedy cao tại J nhỏ và tốc độ thấp không tự nó chứng minh mobility gain: Greedy khởi tạo theo slot đầu, còn P2/DP chọn điểm đầu bằng toàn horizon. DP−P2 là đối chiếu phù hợp hơn để mô tả lợi ích đổi vị trí trong cùng điều kiện thông tin offline.', '',
        f'Ở p0,8, ΔU_DP−P2={metrics["p08_DP_delta_U_over_P2"]:.8g}, CI95% [{metrics["p08_DP_delta_U_over_P2_ci95_low"]:.8g}, {metrics["p08_DP_delta_U_over_P2_ci95_high"]:.8g}] bit/use. Kết hợp effect size tuyệt đối với tỷ lệ giúp tránh đọc gain lớn chỉ từ mẫu số nhỏ.', '',
        '## Thuộc tính toán học và phát biểu được phép', '',
        '| Biến đổi | Bảo đảm | Không được suy ra |',
        '|---|---|---|',
        '| Thêm vị trí lồng nhau | U_DP và U_P2 không giảm | Greedy/availability/quãng đường phải đơn điệu |',
        '| Nới giới hạn tốc độ | U_DP không giảm; P2 không đổi | K hoặc D_DP phải tăng ở λ>0 |',
        '| Tăng p với mask chặn lồng nhau | U_DP và U_P2 không tăng | Availability hoặc mobility gain phải có một dạng cố định |',
        '| Nt hoặc ell thay đổi | Không áp đặt đơn điệu | Xu hướng quan sát là định luật tổng quát |',
        '| So phương án cùng cấu hình | U_DP≥U_Greedy,U_P2 | DP tối ưu availability, năng lượng hoặc SKR riêng lẻ khi λ>0 |', '',
        '## Tham số ảnh hưởng mạnh nhất', '',
        'Dùng span=max(mean)−min(mean) trên các dải đã duyệt tại λref, không gọi đây là sensitivity index chuẩn hóa. Với K/availability: **P2 chịu ảnh hưởng lớn nhất bởi p; Greedy bởi tốc độ; DP bởi J**. Với gain U_DP−P2, p tạo span lớn nhất. Với gap DP−Greedy, tốc độ tạo span lớn nhất, có đóng góp của lựa chọn điểm đầu offline.', '',
        '## Rà soát trình bày và truy vết', '',
        'Đã xem sáu PNG gốc: chú giải, nhãn, đơn vị, marker/line style, giá trị zero và band CI được giữ. Bố cục không cần sửa; các hình chính có trục bắt đầu quanh zero nên khoảng cách giữa đường có thể nhỏ. S1 bổ sung effect size trực tiếp, không cắt trục các hình gốc.', '',
        'PDF vector nên dùng khi chèn bản thảo. PNG 350 dpi dùng để xem nhanh; khi phần mềm thu nhỏ preview có thể làm mất nét chữ, cần xem bản gốc trước khi kết luận thiếu nhãn.', '',
        '[Bản thảo thảo luận tiếng Anh](discussion_en.md) · [English captions gốc](../../figure_captions_en.md) · [Source map](figure_review.csv) · [Metric dẫn xuất](review_metrics.csv) · [Xác minh phần bổ sung](validation_report.md)', '',
        'Bộ gốc có receipt cố định và verifier đệ quy yêu cầu chính xác danh sách tệp cũ. Phần analysis mới này không sửa receipt/verifier gốc; verify_review.py xác minh trực tiếp toàn bộ thành viên receipt và các hash producer trước khi kiểm tra phần bổ sung. Không dùng lỗi coverage của verifier cũ sau khi thêm thư mục con để suy ra dữ liệu gốc bị thay đổi.', '',
        'Giữ nguyên chênh lệch frozen hash, Objective C USER_STOPPED và mọi giới hạn finite-catalog/grid, synthetic clouds, MI2D/Holevo homodyne chưa xác thực an toàn, chưa hiệu chuẩn năng lượng. Không thay nguồn khoa học, bảo mật, frozen model, baseline/threshold, lifecycle; không training/test/held-out, external manuscript edit, commit/push.', '',
    ]
    (OUT / 'report_review_vi.md').write_text('\n'.join(report), encoding='utf-8', newline='\n')
    english = f'''# Stage A: numerical-results discussion draft

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

These paragraphs describe the saved synthetic finite-catalog/grid experiment. They do not establish operational or composable quantum security. The symbol K denotes the manuscript-model usable-SKR metric.

At the representative penalty of 9.468026677248516e-6 bit/use, the default DP solution achieves mean K={k1:.8g} and U={stat('base','DP','U_mean'):.8g} bit/use with a mean travel distance of {d1:.3f} m. Its mean objective exceeds the stationary and Greedy references by {metrics['baseline_DP_U_gain_over_P2_percent']:.3f}% and {metrics['baseline_DP_U_gain_over_Greedy_percent']:.3f}%, respectively. The paired 95% confidence intervals for these relative gains are [{pair('base','Stationary','ratio_ci95_low'):.3f}, {pair('base','Stationary','ratio_ci95_high'):.3f}]% and [{pair('base','Greedy','ratio_ci95_low'):.3f}, {pair('base','Greedy','ratio_ci95_high'):.3f}]%. DP also travels {metrics['baseline_DP_distance_saving_over_Greedy_percent']:.2f}% less than Greedy. P2 and DP use offline cloud states, whereas Greedy observes only the current slot; their difference therefore includes an information advantage.

Figures A1 and A2 show the benefit of enlarging the nested candidate set. Increasing J from 10 to 100 raises the DP mean usable SKR by {metrics['DP_J10_to_100_K_increase_percent']:.2f}% and its objective by {metrics['DP_J10_to_100_U_increase_percent']:.2f}%. At the representative penalty, DP zero-SKR unavailability decreases from 7.4% to 0.1%, compared with 9.47% to 2.23% for P2 and 29.57% to 1.27% for Greedy. The J=10 transition graph contains eight connected components, while the tested subsets are connected from J=20 onward. Accordingly, the early improvement reflects both expanded spatial choices and connectivity changes. The J=20 objective reaches {metrics['DP_J20_U_fraction_of_J100_percent']:.2f}% of the J=100 value; this does not identify an economically optimal candidate count.

Figure B indicates a small incremental benefit beyond the default speed. Raising the limit from 15 to 25 m/s improves the DP objective by only {metrics['DP_speed15_to_25_U_increase_percent']:.5f}%. Relaxing the speed constraint cannot reduce the optimal objective, but it need not increase travel distance: mean DP distance decreases from {stat('speed_20','DP','D_mean'):.3f} to {stat('speed_25','DP','D_mean'):.3f} m between 20 and 25 m/s. At zero speed, DP coincides with the offline stationary optimum. Its remaining advantage over Greedy is due to initial-position selection, rather than motion.

Figure C separates worsening absolute performance from increasing adaptation benefit. At blockage probability 0.8, DP retains {stat('probability_0p8','DP','availability_mean')*100:.3f}% nonzero-SKR availability, and its objective is {metrics['p08_DP_U_gain_over_P2_percent']:.2f}% above P2 and {metrics['p08_DP_U_gain_over_Greedy_percent']:.2f}% above Greedy. The absolute DP-minus-P2 objective difference is {metrics['p08_DP_delta_U_over_P2']:.8g} bit/use, with a paired 95% interval of [{metrics['p08_DP_delta_U_over_P2_ci95_low']:.8g}, {metrics['p08_DP_delta_U_over_P2_ci95_high']:.8g}]. The largest observed relative benefit occurs at the upper tested boundary; no interior maximum or extrapolation beyond p=0.8 is inferred.

The supplementary horizon and spatial-correlation results qualify these trends. Increasing Nt from 5 to 30 raises relative DP-versus-P2 objective gain from 0.092% to 3.075%, although absolute average performance declines slightly. Because the objective combines average reward with total travel distance, this sweep does not isolate lookahead from normalization. Increasing latent spatial length from 50 to 1000 m lowers absolute performance but raises the relative DP-versus-P2 objective gain from 1.46% to 5.96%. These observations do not imply a universal monotonic law for horizon or spatial correlation.

The penalty comparison further illustrates the mobility trade-off: at the default configuration, changing from zero to representative penalty reduces DP travel by {metrics['DP_distance_reduction_lambda0_to_ref_percent']:.2f}% while reducing mean usable SKR by {metrics['DP_SKR_loss_lambda0_to_ref_percent']:.3f}%. These are changes between saved means, without a newly assigned cross-penalty confidence interval. Objective dominance must not be restated as mission-wise SKR dominance; the latter is reversed in {lower_k} of {len(positive_dp)} case-mission pairs at the positive penalty.

All intervals are pointwise percentile intervals from the existing 20,000 paired whole-mission bootstrap resamples over 100 missions, not independent-slot intervals or quantum-security bounds. Availability means positive usable SKR and is separate from any engineering threshold. No new cloud, quantum/source calculation, optimization run, bootstrap draw, or Stage B experiment was performed for this figure/report continuation.

Supplementary Figure S1 caption: Paired mean objective differences between DP and the stationary or Greedy references versus (a) candidate count, (b) maximum UAV speed, and (c) cloud-blockage probability, at the same fixed representative penalty. Bands reuse the saved pointwise 95% paired whole-mission bootstrap intervals. The objective advantage at zero speed reflects offline initial-position selection; DP and P2 cannot move there. Lines connect evaluated points without smoothing. The six original captions remain in [figure_captions_en.md](../../figure_captions_en.md).
'''
    (OUT / 'discussion_en.md').write_text(english, encoding='utf-8', newline='\n')
    mapping = []
    for label, name, axis_name, role in FIGURES:
        mapping.append(dict(figure=label, role=role, axis=axis_name, pdf=figdir + name + '.pdf', png=figdir + name + '.png',
                            data=figdir + name + '_data.csv', pdf_sha256=sha(BASE / 'existing_data/figures' / (name + '.pdf')),
                            png_sha256=sha(BASE / 'existing_data/figures' / (name + '.png')), disposition='Retained unchanged after visual review'))
    mapping.append(dict(figure='S1', role='Supplementary', axis='J;speed;probability', pdf='fig_S1_paired_objective_gaps.pdf', png='fig_S1_paired_objective_gaps.png',
                        data='fig_S1_paired_objective_gaps_data.csv', pdf_sha256=sha(OUT / 'fig_S1_paired_objective_gaps.pdf'),
                        png_sha256=sha(OUT / 'fig_S1_paired_objective_gaps.png'), disposition='Saved paired gaps and intervals; no new simulation points'))
    save_csv('figure_review.csv', mapping)
    print('RENDERED_S1', len(points), 'authenticated saved-data points; VI/EN reports written')


if __name__ == '__main__':
    build()
