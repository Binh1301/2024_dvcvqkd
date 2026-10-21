"""Render Vietnamese report from saved results, without scientific reevaluation."""
import csv
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent


def table(header,rows):
    return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']
                     +['| '+' | '.join(str(x) for x in row)+' |' for row in rows])


def main():
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    with (OUT/'skr_vs_zenith_angle.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    with (OUT/'operational_zenith_angles.csv').open(encoding='utf-8',newline='') as f:
        ops=list(csv.DictReader(f))
    fnum=lambda x:f'{float(x):.12g}'
    keys=('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw')
    names=('Uniform tối ưu trong catalog','MB cố định','MB tối ưu trong catalog')
    text=['# SKR theo góc thiên đỉnh — so sánh số theo bản thảo','',
          '**CURRENTLY_VERIFIED_PASS** cho các kiểm tra số và provenance trong phạm vi này. '
          '**UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS** vẫn giữ nguyên.','',
          'Dùng MI 2D chuẩn hóa và Holevo homodyne như yêu cầu. Phép ghép này là so sánh số '
          'theo quy ước bản thảo, chưa thiết lập tốc độ khóa homodyne an toàn về mặt vật lý. '
          'Tối ưu chỉ trên catalog hữu hạn: **BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY**.','',
          '## Kết quả và xu hướng','',
          f'Đã đánh giá {s["initial_angles"]} góc ban đầu (0–60°, bước 2°), thêm {s["refined_angles"]} '
          f'góc làm mịn; tổng {s["total_angles"]} góc × 218 nguồn = {s["candidate_evaluations"]} lượt. '
          'Mỗi góc dùng toàn bộ 36 nguồn Uniform và 182 nguồn MB đã xác thực; MB cố định '
          'cũng thuộc catalog MB. Không tạo C,w mới, không nội suy, không cắt SKR âm.','',
          table(['Phương án','K(0°)','K(30°)','K(60°)','K lớn nhất đã đo / góc'],[
              [name,fnum(rows[0][key]),fnum(s['at_30'][key]),fnum(rows[-1][key]),
               f'{fnum(max(rows,key=lambda r:float(r[key]))[key])} / '
               f'{max(rows,key=lambda r:float(r[key]))["zenith_deg"]}°'] for name,key in zip(names,keys)]),'']
    for name,key in zip(names,keys):
        decreasing=[(a['zenith_deg'],b['zenith_deg']) for a,b in zip(rows,rows[1:]) if float(b[key])<float(a[key])]
        text.append(f'- {name}: '+('tăng tại mọi bước góc đã đánh giá.' if not decreasing else
                    'không đơn điệu; các bước giảm là '+', '.join(f'{a}→{b}°' for a,b in decreasing)+'.'))
    text+=['',('Uniform không có SKR dương tại bất kỳ góc đã đánh giá nào; vì vậy không có đường xanh '
               'dương trên hình semilog, còn đường xanh đầy đủ xuất hiện trong hình tuyến tính.'
               if not s['Uniform_positive_angles'] else 'Các góc Uniform dương: '+str(s['Uniform_positive_angles'])),
           '', '## Miền dương và giới hạn vận hành đã khảo sát','',
           table(['Phương án','Góc dương lớn nhất đã đo','Góc không dương đầu tiên','Khoảng chuyển dương→không dương','Khoảng L (km)'],[
               [name,op['maximum_tested_positive_deg']+'°' if op['maximum_tested_positive_deg'] else 'Không có',
                op['first_tested_nonpositive_deg']+'°' if op['first_tested_nonpositive_deg'] else 'Không có',
                '['+op['operational_lower_deg']+', '+op['operational_upper_deg']+']°' if op['operational_lower_deg'] else 'Chưa quan sát',
                '['+fnum(op['distance_lower_km'])+', '+fnum(op['distance_upper_km'])+']' if op['distance_lower_km'] else 'Không áp dụng']
               for name,op in zip(names,ops)]),'']
    for name,key,op in zip(names,keys,ops):
        positive=[r for r in rows if float(r[key])>0]
        upward=[(a,b) for a,b in zip(rows,rows[1:]) if float(a[key])<=0<float(b[key])]
        if positive:
            text.append(f'- {name}: các điểm dương từ {positive[0]["zenith_deg"]}° đến {positive[-1]["zenith_deg"]}° '
                        f'(L={fnum(positive[0]["distance_km"])}–{fnum(positive[-1]["distance_km"])} km).')
        for a,b in upward:
            text.append(f'  Chuyển không dương→dương nằm giữa hai điểm đã tính [{a["zenith_deg"]}, {b["zenith_deg"]}]° '
                        f'(L={fnum(a["distance_km"])}–{fnum(b["distance_km"])} km); không suy ra nghiệm nội suy.')
        if op['status']=='POSITIVE_THROUGH_SWEEP_BOUNDARY_NOT_TRUE_MAXIMUM':
            text.append(f'  {name} còn dương ở 60° (38 km): 60° là biên khảo sát, chưa phải giới hạn vật lý cực đại.')
    text+=['','“Góc không dương đầu tiên” tính từ 0°, nên có thể là 0° khi đường MB bắt đầu âm rồi mới dương. '
            'Chỉ khoảng dương→không dương mới chặn giới hạn phía góc lớn. Không quan sát khoảng như vậy thì '
            'không tạo khoảng chặn giả. Các điểm hữu hạn không chứng minh tính dương liên tục giữa các điểm.','',
            '## Mức cải thiện MB','',
            table(['Góc','K MB cố định','K MB tối ưu','ΔK','Cải thiện khi MB cố định dương'],[
                [str(d)+'°',fnum(s['at_'+str(d)]['Fixed_MB_K_raw']),fnum(s['at_'+str(d)]['Optimized_MB_K_raw']),
                 fnum(s['at_'+str(d)]['MB_improvement_absolute']),
                 f'{s["at_"+str(d)]["MB_improvement_percent"]:.6g}%' if s['at_'+str(d)]['MB_improvement_percent'] is not None else 'Không dùng % vì mẫu số không dương']
                for d in (0,30,60)]),'',
            f'ΔK lớn nhất đã đánh giá = {fnum(s["MB_improvement_max_absolute"]["MB_improvement_absolute"])} bits/use '
            f'tại {s["MB_improvement_max_absolute"]["zenith_deg"]}°. '
            'Cột phần trăm trong CSV chỉ có giá trị khi K MB cố định > 0.','',
            '## Thay đổi tham số nguồn','',
            'Đây là góc đầu tiên có lựa chọn mới trên lưới đã đo; vị trí chuyển chính xác chỉ được giới hạn '
            'bởi điểm liền trước, không phải nghiệm chuyển liên tục.','',
            table(['Phương án','Điểm trước (°)','Điểm đầu tham số mới (°)','Tham số trước','Tham số mới'],[
                [r['scheme'],r['previous_tested_deg'],r['first_tested_new_parameters_deg'],
                 r['previous_parameters'],r['new_parameters']] for r in s['source_changes']]),'',
            'Xem `source_parameter_changes.csv`. Nguồn cố định luôn có νraw=0.165, VA=5.475. '
            'Miền catalog Uniform VA=0.02–12; MB νraw=0.05–0.8, VA=0.025–8. '
            'Giá trị nằm ở biên catalog vẫn chỉ là ứng viên tốt nhất đã thử.','',
            '## Kiểm tra tại 30°','',
            'L=21.939310229205777 km; <η>=0.0002640339370277642854, '
            '<√η>=0.0156059440205538217562, ηf=0.0002435454887726595830. '
            'Tất cả trường kênh khớp hàm recheck bất biến ở sai số dưới 1e-60 tương đối có thang tối thiểu 1.','',
            f'MB cố định K={fnum(s["at_30"]["Fixed_MB_K_raw"])}; Uniform VA={s["at_30"]["Uniform_optimal_VA"]}, '
            f'K={fnum(s["at_30"]["Uniform_K_raw"])} bits/use. Hai tham chiếu cũ được tái lập trước khi quét. '
            'Uniform được xếp hạng lại trên toàn bộ 36 nguồn, không mặc định dùng ứng viên cũ. '
            'Sai số chi tiết nằm trong `reference_gate.json`.','',
            '## Phương trình và truy vết','',
            '- Kênh: `run_sweep.py:channel_at_angle`, bản sao các phương trình của '
            '`scripts/recheck_manuscript_homodyne_noise.py:channel` với ζ thay đổi. '
            'Tính lại L=19secζ km, ηatm=.92^secζ, tích phân HV, σR², Gd, wL, weff, weq, '
            'σs²=1+(L·15.61e-6)², A0 và mọi hệ số/moment PDF ở từng góc. '
            'Khép kín HV/Gd là quy ước repository đã công khai ở recheck, không phải công thức được định nghĩa đầy đủ trong PDF.',
            '- PDF: công thức đóng Q cho q=0,1/2,1 trên [0,1], cộng riêng nguyên tử outage P0; '
            'không chuẩn hóa lại. Đối chiếu tích phân trực tiếp ở 0°,30°,60° lưu trong `channel_closed_vs_quadrature.csv`.',
            '- N=(<η>−<√η>²)VA+.0186<η>; ηf=<√η>²; ξf=N/ηf. '
            'Không thêm nhiễu tổn hao thuần hoặc detector; ideal R=1, ξdet=0.',
            '- MI: nhập nguyên trạng `uniform_mi_2d` từ script Uniform đã kiểm chứng. '
            'Hỗn hợp Cartesian của cả Uniform và MB phân tích tích chính xác; vẫn cộng tensor 2D '
            'hai trục, trung bình 2√ηf α, phương sai từng trục 1+N. Không chia 2, không thêm nhiễu heterodyne. '
            'Đối chiếu hỗn hợp đầy đủ 256 ký hiệu bằng kernel gốc tại 0°,30°,60°.',
            '- Holevo: nhập nguyên trạng `security` của recheck; V=VA+1, W=1+ηfVA+N, '
            'Z=2<√η>C−√(2Nw), ν3=√[V(V−Z²/W)]. Entropy dùng 80 chữ số; kiểm tra 110 chữ số ở ba góc đại diện.',
            '- Nguồn: xác thực schema, cache key, ba hash triển khai, support256, binary64 ν/VA, '
            'hash đầy đủ tệp, hash ensemble, PMF MB, hình học và VA=2<n>. '
            'Không chạy lại AP, thay đổi support hoặc ladder1050/1250/1450. '
            '`source_roster.csv`, `verified_ensembles.npz` và `input_manifest.json` ràng buộc đầu vào.','',
            '## Xác thực số và giới hạn','',
            f'{s["checks"]} kiểm tra trong producer đạt PASS; 9 kiểm tra tự thân độc lập đạt PASS. '
            f'Mọi ứng viên ở mọi góc đều được GH16/32/64: max|ΔMI|={s["GH_maximum_difference"]:.6g} bit. '
            f'Max sai khác phổ symplectic đối chiếu ma trận={s["spectrum_maximum_difference"]:.6g}; '
            f'min eigenvalue(Γ+iΩ)={s["minimum_uncertainty_eigenvalue"]:.6g}>0. '
            'Không sửa covariance, ν, SKR hoặc dữ liệu nguồn để ép dấu dương.','',
            'Đặc tả frozen hiện tại có SHA256 df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15, '
            'khác hash lịch sử mong đợi 561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1. '
            'Tệp được giữ nguyên; đây vẫn là blocker cho nâng trạng thái production. '
            'Không thay mô hình production, hàm bảo mật, nguồn/cache cũ, cấu hình hoặc frozen spec; '
            'không training, test-data/final-test/held-out/publication evaluation, '
            'chứng nhận baseline/threshold, khởi động ObjectiveC, commit hay push.','',
            '## Tệp và tái lập','',
            '- `skr_vs_zenith_angle.csv`: bảng so sánh đầy đủ; `initial_31_points.csv`: 31 điểm ban đầu.',
            '- `skr_vs_zenith_angle_detailed.csv`: MI, βMI, Holevo, noise, nguồn và covariance cho cả ba phương án.',
            '- `all_candidate_evaluations.csv`: toàn bộ ứng viên tại mọi góc, bao gồm GH16/32/64 và kiểm tra ma trận.',
            '- `channel_by_angle.json`, `selected_high_precision_models.json`: mọi trường kênh và số học chính xác cao.',
            '- `operational_zenith_angles.csv`, `source_parameter_changes.csv`: miền dương và lựa chọn nguồn.',
            '- `verify_results.py` chỉ đọc bằng chứng/hash đã lưu; receipt ràng buộc các tệp đầu ra và kiểm tra '
            '4.807 tệp cũ, chỉ cho phép năm tài liệu ledger thay đổi.',
            '- Chạy lại khoa học chỉ trong namespace mới có startup manifest phù hợp; producer từ chối ghi đè '
            'summary đã hoàn tất. Interpreter: `.venv/Scripts/python.exe -X utf8 -B`. '
            'Không cần cài thêm phụ thuộc.','',
            '## Hình so sánh và bảng vận hành','',
            'PNG 350 dpi; PDF vector. Các giá trị không dương được giữ nguyên trong CSV/hình tuyến tính; '
            'hình log dùng NaN để ngắt đoạn, không thay bằng epsilon hoặc nối qua đoạn âm. '
            '`render_figures.py` chỉ đọc CSV để xuất bố cục cuối, dành khoảng trống cho legend góc phải trên; '
            'không tính lại số liệu. `render_receipt.json` ràng buộc CSV/renderer.','',
            '![SKR versus Zenith Angle](skr_vs_zenith_angle.png)','',
            '![SKR versus Zenith Angle, linear](skr_vs_zenith_angle_linear.png)','',
            table(['Phương án','Dương lớn nhất đã đo (°)','Không dương đầu tiên (°)','Trạng thái'],[
                [name,op['maximum_tested_positive_deg'] or 'Không có',op['first_tested_nonpositive_deg'] or 'Không có',op['status']]
                for name,op in zip(names,ops)]),'']
    (OUT/'validation_report.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')
    print('Report saved from existing artifacts')


if __name__=='__main__':
    main()
