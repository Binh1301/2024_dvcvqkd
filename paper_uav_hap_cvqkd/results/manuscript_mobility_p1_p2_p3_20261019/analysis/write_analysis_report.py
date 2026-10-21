"""Build discussion from the checked saved-data summary, without a simulator."""
from pathlib import Path

OUT=Path(__file__).resolve().parent


def f(value):return '—' if value is None else f'{value:.10g}'


def table(headers,rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+
                     ['|'+'|'.join(str(value) for value in row)+'|' for row in rows])


def write_reports(s,data):
    p1,p2,methods,dyn=[s[k] for k in ('p1','p2','methods','dynamics')]
    li=dyn['representative_lambda_index'];penalties=data['penalties'];representative=float(penalties[li])
    def paired(base,metric,index=li):return next(r for r in methods['paired'] if r['baseline']==base and r['metric']==metric and r['lambda_index']==index)
    def method(name,index=li):return next(r for r in methods['method_rows'] if r['method']==name and r['lambda_index']==index)
    ps,pg,us,ug=paired('Stationary','K'),paired('Greedy','K'),paired('Stationary','U'),paired('Greedy','U')
    stat=p1['summary'];mb=stat['MB_K_raw'];gap=stat['rank_gap'];uni=stat['Uniform_best_K_raw']
    availability_share=100*p2['mean_gain_component_availability']/p2['gain']['mean']
    top=p2['top_locations'];dp=method('DP');gr=method('Greedy');st=method('Stationary')
    zero=method('DP',0);frontier=dyn['frontier']
    VI=['# Phân tích định lượng P1–P2–P3 và lợi ích mobility','',
        '**UNVALIDATED_SECURITY_MODEL — NOT_READY_FOR_PUBLICATION_SCALE_RUNS**','',
        'Đây là hậu phân tích các kết quả số đã hoàn tất. Không chạy lại P1/P2/P3/Greedy, kênh, SKR, C,w hoặc sinh mây. '
        'Các bảng và hình bổ sung nằm riêng trong `analysis/`; mọi artifact mô phỏng gốc được kiểm tra SHA-256 trước và sau phân tích. '
        'Bản thảo tiếng Anh ở [numerical_results_discussion_en.md](numerical_results_discussion_en.md) là bản nháp để tác giả xem xét, chưa sửa manuscript bên ngoài repo.','',
        '## 1. Phạm vi, phép đo và truy vết','',
        'Nguồn: `../p1/candidate_evaluations.csv`, `../p1/winners.csv`, `../mobility/mission_metrics.csv`, '
        '`../mobility/paths.npz`, `../clouds/states.npz`, `../positions.csv`, `../protocol.json` và các receipt. '
        'Tái dựng trực tiếp SKR, quãng đường và objective của cả 3.000 đường đã lưu, đồng thời đối chiếu các trung bình, SD và CI t với bảng gốc. '
        '23.300 hàng vị trí–nguồn gồm đủ 233 ensemble ở mỗi vị trí; không xếp hạng bằng nguồn hay evaluator mới.','',
        'Hệ thống giữ nguyên: 100 tâm ô trong 1 km × 1 km, HAP cao 20 km, UAV cao 1 km, 30 slot × 20 s, '
        'vmax=15 m/s, mỗi bước ≤300 m, Dref=1.000 m. Điểm đầu tự chọn cho mọi chiến lược; không tính triển khai hoặc quay về. '
        'Cùng giả định khởi tạo không có nghĩa là ép cùng tọa độ đầu: P2/DP dùng toàn bộ nhiệm vụ, Greedy dùng slot đầu rồi các slot hiện tại.','',
        'Nguồn 197 MB + 36 Uniform. Quang học 1550 nm, phân kỳ toàn phần 233 µrad, đường kính thu 0,08 m; '
        'β=0,95 và ξch=0,0186. Giữ chuẩn VA=2⟨n⟩, MI 2D với phương sai mỗi trục 1+N và Holevo homodyne theo protocol của lượt chạy. '
        'Không thay quy ước này bằng functional production khác.','',
        r'Các metric được giữ riêng: $K_j^*=[\max_g K_{j,g}^{raw}]^+$; $S_{j,n}=(1-c_{j,n})K_j^*$; '
        r'$\overline K=\sum_n S_{j_n,n}/30$; $D=\sum_{n=2}^{30}d_{j_{n-1},j_n}$; $U=\overline K-\lambda D/1000$. '
        'Availability là tỷ lệ slot có S>0. Đơn vị rate là bits/use, không phải bits/s hay tổng số bit.','',
        f'Dải λ giữ nguyên 10 hệ số {data["schedule"]["multipliers"]}, λhi={f(data["schedule"]["lambda_hi"])} bits/use. '
        f'Điểm phân tích chính dùng λ={f(representative)} (=0,003 λhi), đã chốt trước khi xem quỹ đạo.','',
        '## 2. P1: tối ưu nguồn hữu hạn','',
        table(['Đại lượng trên 100 vị trí','Min','Max','Mean','SD toàn bộ lưới (ddof=0)'],
            [[label,f(stat[key]['min']),f(stat[key]['max']),f(stat[key]['mean']),f(stat[key]['sd_population'])] for key,label in [
                ('MB_K_raw','MB tối ưu, bits/use'),('Uniform_best_K_raw','Uniform tối ưu raw, bits/use'),
                ('distance_km','Khoảng cách (km)'),('zenith_deg','Góc zenith (độ)'),('rank_gap','MB thứ nhất − thứ hai (bits/use)'),
                ('rank_gap_percent_of_best','Chênh thứ nhất − thứ hai / thứ nhất (%)')]]),'',
        f'Cả 100/100 vị trí chọn (ν,VA)=(0,125;8). Nguồn đứng thứ hai tại tất cả vị trí là (0,15;8). '
        f'Chênh tuyệt đối {f(gap["min"])}–{f(gap["max"])} bits/use, tức '
        f'{f(stat["rank_gap_percent_of_best"]["min"])}–{f(stat["rank_gap_percent_of_best"]["max"])}%. '
        'Hai lựa chọn gần nhau về hiệu năng, nhưng không phải hòa về số học.','',
        f'VA=8 là trần catalog MB (max={f(p1["MB_catalog_max_VA"])}). Không có bằng chứng rằng đạo hàm theo VA đổi dấu hoặc '
        'nguồn tốt hơn không tồn tại ở VA>8. Vì vậy chỉ kết luận **best exact-tested trong catalog hữu hạn**, không tối ưu liên tục/toàn cục. '
        '100 vị trí không phải 100 mẫu kênh độc lập: lưới có 60 danh tính hình học chính xác, các vị trí đối xứng dùng chung moment. '
        'SD không gian là mô tả lưới; không lập CI suy diễn từ 100 ô.','',
        f'Tính ổn định đã quan sát được giới hạn ở L={f(stat["distance_km"]["min"])}–{f(stat["distance_km"]["max"])} km và '
        f'zenith={f(stat["zenith_deg"]["min"])}–{f(stat["zenith_deg"]["max"])} độ. Nguồn thắng không đổi trong miền này. '
        f'Khoảng cách xếp hạng nhỏ nhất lớn hơn khoảng {f(p1["min_gap_over_two_GH_error_bounds"])} lần tổng hai allowance MI (2β×2e−13). '
        'Đây là đối chiếu với allowance quadrature, không phải bound tổng sai số của mô hình hay nguồn. '
        'Không có dữ liệu perturbation riêng của jitter, Cn², ξch hoặc các tham số quang khác; không kết luận robustness theo các tham số đó. '
        'Kế hoạch tối thiểu nếu được yêu cầu thêm là lưu protocol perturbation và chỉ đánh giá hai nguồn đầu trên các trạng thái mới đã duyệt; nhiệm vụ này không thực hiện các phép tính ấy.','',
        f'Uniform có raw SKR âm ở {p1["Uniform_raw_negative_positions"]}/100 vị trí: '
        f'{f(uni["min"])} đến {f(uni["max"])} bits/use. Kiểm tra dựa trên raw candidate và raw family maximum, không dựa trên số 0 sau clipping. '
        f'MB tạo usable lift tuyệt đối {f(mb["min"])}–{f(mb["max"])} bits/use, trung bình {f(mb["mean"])} so với Uniform usable=0. '
        '**Không tính phần trăm tăng so với 0.**','',
        f'So sánh hai family được tối ưu VA riêng chưa cô lập hiệu ứng PMF: MB chọn VA=8 còn Uniform có miền VA khác. '
        f'Bổ sung đối chiếu cùng VA=8 từ candidate đã lưu: Uniform raw mean={f(stat["Uniform_matched_K_raw"]["mean"])}; '
        f'raw MB−Uniform mean={f(stat["matched_raw_gain"]["mean"])} bits/use. Cả hai có cùng năng lượng trung bình VA/2=4 photon theo chuẩn nguồn. '
        'Đối chiếu này hỗ trợ khác biệt modulation ở cùng năng lượng trung bình trong mô hình đang dùng; không đảm bảo cùng peak amplitude, phần cứng hoặc bảo mật thực nghiệm.','',
        'P1 không đổi nguồn theo vị trí trong lượt này. Do đó không thể gán gain P2/P3 cho một policy đổi nguồn động: tất cả phương án mobility dùng cùng nguồn MB đã chọn. '
        'Bảng chi tiết: [p1_position_details.csv](tables/p1_position_details.csv).','',
        '![A](figures/A_p1_spatial_skr.png)','',
        '## 3. P2: giá trị của chọn vị trí đứng yên','',
        'Protocol có `reference_position_index=44`, tọa độ (450,450) m, từ trước lượt mô phỏng. '
        'Lượt chạy gốc chưa có một phương án metric tên FixedReference; điểm này vốn dùng kiểm tra hình học. '
        'Ở đây baseline cố định được **tái dựng hậu phân tích tại đúng điểm tham chiếu đã có**, bằng mean(S[rid,44,:]); '
        'không đề xuất tọa độ mới, không chọn lại vị trí theo kết quả và không chạy kênh. Đây chưa phải baseline vận hành đã preregister riêng.','',
        table(['Phương án','Mean K','SD mẫu K','Median','P05','P95','CI95% mean, t'],[
            ['Fixed tại index44',f(p2['reference']['mean']),f(p2['reference']['sd']),f(p2['reference']['median']),f(p2['reference']['p05']),f(p2['reference']['p95']),f"[{f(p2['reference']['ci95_t_low'])}, {f(p2['reference']['ci95_t_high'])}]"],
            ['P2',f(p2['chosen']['mean']),f(p2['chosen']['sd']),f(p2['chosen']['median']),f(p2['chosen']['p05']),f(p2['chosen']['p95']),f"[{f(p2['chosen']['ci95_t_low'])}, {f(p2['chosen']['ci95_t_high'])}]"],
            ['P2 − Fixed, paired',f(p2['gain']['mean']),f(p2['gain']['sd']),f(p2['gain']['median']),f(p2['gain']['p05']),f(p2['gain']['p95']),f"[{f(p2['gain']['ci95_t_low'])}, {f(p2['gain']['ci95_t_high'])}]"],
        ]),'',
        f'P2 tăng mean K {f(p2["gain_ratio_of_means_percent"])}% theo tỷ số hai trung bình. '
        f'Availability trung bình tăng từ {f(100*p2["mean_reference_clear_fraction"])}% lên {f(100*p2["mean_clear_fraction"])}%. '
        f'P2 chọn {p2["unique_positions"]} vị trí khác nhau; {p2["entirely_clear_missions"]}/100 nhiệm vụ có đủ 30 slot thông thoáng tại điểm được chọn. '
        f'{p2["near_tie_missions"]}/100 nhiệm vụ có hơn một vị trí trong 1e−12 bits/use so với cực đại; tần suất vị trí chịu ảnh hưởng tie-break trong các trường hợp đó.','',
        table(['Index0 / j bản thảo','x (m)','y (m)','Số nhiệm vụ','Tỷ lệ'],[[f"{r['position_index']} / {r['j']}",f(r['x_m']),f(r['y_m']),r['selected_missions'],f(100*r['selected_fraction'])+'%'] for r in top]),'',
        f'Vị trí clear-sky tốt nhất là index{p2["clear_sky_best_position"]}, nhưng P2 chỉ chọn nó trong {p2["clear_sky_best_selected_missions"]}/100 nhiệm vụ. '
        f'{p2["max_availability_selected_missions"]}/100 lần P2 chọn một điểm có cloud-free fraction cao nhất; '
        'các lần còn lại đánh đổi một phần availability để có clear-sky K cao hơn. P2 tối ưu tích A_jK_j, không tối ưu riêng từng yếu tố.','',
        'Để tách hai yếu tố đối với điểm tham chiếu, dùng phân rã đối xứng đại số (không diễn giải nhân quả):',
        r'$\Delta K=\tfrac12(A_*+A_r)(K_*-K_r)+\tfrac12(K_*+K_r)(A_*-A_r)$.','',
        f'Thành phần clear-sky trung bình={f(p2["mean_gain_component_clear_sky"])}; thành phần availability={f(p2["mean_gain_component_availability"])} bits/use '
        f'({f(availability_share)}% tổng gain). Theo phân rã này, tránh mây đóng góp phần lớn; lợi thế clear-sky vẫn đáng kể. '
        'Đây là kết quả theo scenario p=0,4, ell=250 m, rho tiềm ẩn=0,9 đã cho, không phải sensitivity sweep theo tham số mây.','',
        'Bảng đủ 100 nhiệm vụ chứa tọa độ, clear fraction, clear K, mean K, slot chặn/dương và baseline ở '
        '[p2_stationary_missions.csv](tables/p2_stationary_missions.csv). P2 được chọn offline sau khi biết toàn bộ mây; '
        'gain 85,46% không thể chuyển nguyên vẹn thành bảo đảm cho một UAV phải chọn vị trí trước nhiệm vụ.','',
        '![B](figures/B_stationary_frequency.png)','',
        '## 4. P3, Greedy và Stationary trên cùng nhiệm vụ','',
        f'Bảng chính tại λ={f(representative)}. SD là SD mẫu giữa 100 nhiệm vụ độc lập.','',
        table(['Phương án','Mean K','SD K','Mean D (m)','SD D (m)','Mean U','SD U','Availability','Số đổi vị trí'],
            [[r['method'],f(r['K_mean']),f(r['K_sd']),f(r['D_mean']),f(r['D_sd']),f(r['U_mean']),f(r['U_sd']),f(r['availability_mean']),f(r['changes_mean'])]
             for r in methods['method_rows'] if r['lambda_index']==li]),'',
        table(['Phương án / metric','Median','P05','P95'],[[r['method']+' / '+metric,f(r[metric+'_median']),f(r[metric+'_p05']),f(r[metric+'_p95'])]
            for r in methods['method_rows'] if r['lambda_index']==li for metric in ('K','D','U')]),'',
        f'DP tăng mean K so với P2 {f(ps["mean"])} bits/use ({f(ps["ratio_of_means_percent"])}%), '
        f'so với Greedy {f(pg["mean"])} ({f(pg["ratio_of_means_percent"])}%). '
        f'Mean ΔU tương ứng {f(us["mean"])} ({f(us["ratio_of_means_percent"])}%) và {f(ug["mean"])} ({f(ug["ratio_of_means_percent"])}%). '
        f'Quãng đường DP trung bình {f(dp["D_mean"])} m, nhỏ hơn Greedy {f(gr["D_mean"])} m.','',
        f'Đối với U, DP thắng nghiêm ngặt P2 trong {us["strict_improvement_missions"]}/100 nhiệm vụ, hòa {us["equal_missions"]}; '
        f'thắng Greedy trong {ug["strict_improvement_missions"]}, hòa {ug["equal_missions"]}; không có vi phạm dominance vượt 1e−12. '
        f'Đối với K chưa phạt, DP thấp hơn Greedy trong {pg["inferior_missions"]}/100 nhiệm vụ, cao hơn trong {pg["strict_improvement_missions"]}, '
        f'hòa {pg["equal_missions"]}. Đây là đánh đổi đúng mục tiêu, không phải lỗi DP.','',
        'DP và P2 biết cùng horizon 30 slot; Greedy biết trạng thái tất cả 100 vị trí ở slot hiện tại, không được thấy tương lai. '
        'Cả ba dùng cùng masks, cùng P1, cùng miền điểm đầu tự do và cùng giới hạn vận tốc. Đây là so sánh benchmark offline với một heuristic causal; '
        'không phải so sánh hai controller có cùng lượng thông tin hoặc cùng điểm đầu thực tế. Không có ablation cùng điểm đầu/cùng lookahead để gán một tỷ lệ nhân quả riêng cho thông tin tương lai.','',
        '## 5. Toàn bộ dải λ và tính đơn điệu','',
        table(['λ (bits/use)','Method','Mean K','SD K','Mean D (m)','Mean U','Availability'],
            [[f(r['lambda_bits_per_use']),r['method'],f(r['K_mean']),f(r['K_sd']),f(r['D_mean']),f(r['U_mean']),f(r['availability_mean'])] for r in methods['method_rows']]),'',
        'SD D, SD U, số đổi vị trí, min/max, median và P05/P95 của K/D/U đều có cho đủ 30 tổ hợp trong '
        '[method_comparison.csv](tables/method_comparison.csv), không chỉ cho điểm minh họa.','',
        'Quãng đường DP không tăng khi λ tăng trong từng nhiệm vụ. Với hai nghiệm tối ưu a,b và λb>λa, '
        'hai bất đẳng thức tối ưu cho (λb−λa)(Db−Da)≤0. Vì vậy xu thế này là thuộc tính bài toán có cùng S/miền khả thi; '
        'không ép hình thành đơn điệu. K tối ưu chưa phạt cũng không tăng theo λ≥0; giá trị tối ưu U là max của các hàm affine giảm theo λ.','',
        f'DP trở thành đứng yên ở toàn bộ 100 nhiệm vụ từ λ={f(penalties[7])} (=0,1 λhi); '
        f'ở λ={f(penalties[6])} vẫn có {100-frontier[6]["stationary_DP_missions"]} nhiệm vụ dịch chuyển. '
        'Chỉ có bracket giữa hai giá trị đã thử cho ngưỡng hết dịch chuyển của toàn bộ tập, không có ngưỡng chính xác trong miền λ liên tục. '
        f'Greedy đã đứng yên hoàn toàn từ λ={f(penalties[6])}, nhưng dừng tại điểm tốt nhất slot đầu, nên mean K chỉ {f(method("Greedy",9)["K_mean"])}; '
        'không hội tụ về P2 chỉ vì D=0. Sau các mốc này, metric tương ứng không đổi khi tăng λ thêm trong các điểm đã lưu.','',
        f'Greedy có {dyn["greedy_nonmonotonic_transitions"]} lần tăng D giữa hai λ kề nhau, thuộc {dyn["greedy_nonmonotonic_missions"]} nhiệm vụ. '
        f'Ở trung bình tập, D tăng từ {f(method("Greedy",1)["D_mean"])} lên {f(method("Greedy",2)["D_mean"])} m giữa 0,0001 và 0,0003 λhi; '
        f'K cũng tăng từ {f(method("Greedy",1)["K_mean"])} lên {f(method("Greedy",2)["K_mean"])}. '
        'Mỗi cặp dùng đúng cùng 100 masks, nên không phải do lấy mẫu lại mây. Kiểm tra lần phân kỳ đầu cho thấy điểm được chọn chuyển theo giao điểm score hữu hạn trên lưới: '
        'bước đầu có thể ngắn hơn khi λ lớn hơn nhưng dẫn đến các bước sau dài hơn. Không cần giả thuyết tie-break để giải thích các witness có score phân biệt; '
        'không khẳng định mọi trường hợp khác đều không có tie.','',
        '![C](figures/C_mobility_tradeoff.png)','',
        'Bảng tradeoff DP so với λ=0:','',
        table(['λ/λhi','Mean K','Mean D (m)','K giữ lại (%)','D giảm (%)','Số nhiệm vụ đứng yên'],
            [[f(r['lambda_multiplier']),f(r['DP_mean_K']),f(r['DP_mean_D']),f(r['K_retained_vs_lambda0_percent']),f(r['distance_reduction_vs_lambda0_percent']),r['stationary_DP_missions']] for r in frontier]),'',
        'Các điểm 0,0001–0,003 λhi cho phép giảm đáng kể quãng đường trong khi giữ gần toàn bộ mean K của λ=0; '
        'đây là tập lựa chọn để kỹ sư cân nhắc, không phải λ tốt nhất chung. Bảng `pareto_dp_summary.csv` còn ghi số nhiệm vụ có K hòa trong 1e−12 '
        'nhưng D giảm so với λ trước; ở những nhiệm vụ ấy chỉ có thay đổi đường/tie ở độ phân giải số đang xét. Những trường hợp K thay đổi thật là đánh đổi hữu hạn, '
        'không thể gán mọi mức giảm D tại λ nhỏ cho tie-breaking. Không có năng lượng đẩy hiệu chuẩn hoặc ưu tiên kỹ thuật để chọn một điểm phổ quát.','',
        '## 6. Phân tích thống kê theo cặp','',
        'Các realization dùng PCG64/SeedSequence([20261015,id]) riêng cho ID 0–99; mỗi nhiệm vụ có tương quan không gian và thời gian nội bộ. '
        'Mỗi nhiệm vụ là một cụm độc lập trong mô hình sinh đã lưu. CI t-Student cho mean dùng SD mẫu, 99 bậc tự do. '
        f'Phân tích bổ sung dùng paired percentile bootstrap {s["bootstrap"]["resamples"]} lần, seed {s["bootstrap"]["seed"]}: '
        'lấy mẫu lại toàn bộ mission với replacement, dùng cùng multiplicity mission cho mọi method/λ/metric. Không resample ô/slot như các mẫu độc lập. '
        'Đây là CI pointwise của mean chênh lệch, chưa hiệu chỉnh đồng thời 40 so sánh và không phải CI dự đoán nhiệm vụ riêng lẻ.','',
        'P05/P95 và percentile bootstrap dùng nội suy tuyến tính của NumPy. Hình F: hộp Q1–Q3, vạch median, whisker 1,5 IQR và các điểm ngoài whisker; '
        'whisker không đồng nghĩa P05/P95. Hình C giữ nguyên CI t95% của lượt chạy gốc; hình D dùng CI bootstrap theo cặp mới.','',
        'Hòa nếu |Δ|≤1e−12 bits/use; thắng nghiêm ngặt nếu Δ>1e−12. Lưu thêm số đếm Δ>0 theo float để tách sai khác cực nhỏ. '
        'Chỉ tính tỷ lệ khi mẫu số>1e−12; phần trăm trong bảng là chênh mean / mean baseline, khác mean của 100 phần trăm cá thể. '
        'Cả hai kiểu tỷ lệ và số mẫu số hợp lệ được lưu riêng.','',
        table(['λ/λhi','Baseline','Mean ΔU','Bootstrap CI95%','Median ΔU','SD ΔU','Thắng / hòa / thua','Gain mean (%)'],
            [[f(data['schedule']['multipliers'][r['lambda_index']]),r['baseline'],f(r['mean']),f"[{f(r['ci95_bootstrap_low'])}, {f(r['ci95_bootstrap_high'])}]",f(r['median']),f(r['sd']),
              f"{r['strict_improvement_missions']}/{r['equal_missions']}/{r['inferior_missions']}",f(r['ratio_of_means_percent'])] for r in methods['paired'] if r['metric']=='U']),'',
        'Tại λ minh họa, cả ΔK và ΔU:','',
        table(['Baseline','Metric','Mean Δ','Bootstrap CI95%','Mean phần trăm cá thể','Tỷ lệ hai mean (%)'],
            [[r['baseline'],r['metric'],f(r['mean']),f"[{f(r['ci95_bootstrap_low'])}, {f(r['ci95_bootstrap_high'])}]",f(r['mean_per_mission_percent']),f(r['ratio_of_means_percent'])]
             for r in methods['paired'] if r['lambda_index']==li]),'',
        'Bốn CI bootstrap tại λ minh họa đều có cận dưới dương, hỗ trợ gain trung bình trong tập scenario này. '
        'Không có nghĩa là mọi nhiệm vụ đều hưởng lợi: 39 lần DP hòa P2 về U, và 25 lần K của DP thấp hơn Greedy. '
        'CI và số lượng realization không xác thực bảo mật vật lý, không đại diện thời tiết đo, cũng không cung cấp kết quả held-out mới.','',
        '![D](figures/D_objective_improvement.png)','',
        '![F U](figures/F_paired_U_distribution.png)','',
        '![F K](figures/F_paired_K_distribution.png)','',
        '## 7. Các nhiệm vụ tiêu biểu và bằng chứng nhìn trước','',
        'Ba trường hợp dưới đây là chọn **hậu phân tích**, chỉ để giải thích cơ chế. Giữ nguyên λ=0,003 λhi; '
        'chọn ID nhỏ nhất khi hòa: (i) max ΔU(DP,P2); (ii) min |ΔU(DP,Greedy)| trong các nhiệm vụ DP có dịch chuyển và ΔU(DP,P2)>1e−12; '
        '(iii) ID đầu tiên có DP đứng yên và ΔU(DP,P2)≈0. Chúng không thay thế nhiệm vụ minh họa ID0 đã chốt trước trong báo cáo gốc; '
        'mọi kết luận về mean/CI vẫn dùng đủ 100 nhiệm vụ.','',
        table(['Vai trò','ID','Method','Mean K','D (m)','U','Availability','Đổi vị trí','Đầu→cuối'],
            [[r['role'],r['realization_id'],r['method'],f(r['K']),f(r['D']),f(r['U']),f(r['availability']),int(r['changes']),f"{r['initial_position']}→{r['final_position']}"] for r in dyn['representatives']]),'']
    for role,rid in dyn['selected_missions']:VI+= [f'![E mission {rid}](figures/E_mission_{rid:02d}_{role}.png)','',f'![Slot rates {rid}](figures/E_slot_rates_mission_{rid:02d}.png)','']
    VI += [
        'ID84 là trường hợp lợi ích objective DP lớn nhất so với P2 tại λ này. P2 ở index83, bị chặn 4 slot; Greedy và DP đều tránh toàn bộ slot chặn, '
        'nhưng DP đổi vị trí 5 lần thay vì 7 và đi 847,214 m thay vì 1.088,635 m. DP bắt đầu ở index81 thay vì điểm slot-đầu tốt nhất index20 của Greedy; '
        'lợi thế điểm đầu cũng sử dụng biết trước mây.','',
        'Với mỗi lần DP di chuyển từ i sang j ở slot n, đối chiếu utility tức thời với việc ở lại i: '
        'δu_n=(S[j,n]−S[i,n])/30−λd(i,j)/1000. Sau đó đối chiếu phần đường DP đã lưu từ n tới cuối với phương án khả thi đứng yên tại i từ n tới cuối. '
        'Phép đối chiếu chỉ đọc S và đường cũ, không giải một DP hay mô phỏng phản thực mới.','',
        table(['ID','Slot','i→j','δu tức thời','Gain phần còn lại so với đứng yên i','Slot chặn tương lai nếu đứng i'],
            [[r['realization_id'],r['slot'],f"{r['from_position']}→{r['to_position']}",f(r['immediate_objective_delta_vs_stay']),f(r['remaining_objective_gain_vs_freeze']),r['future_blocked_slots_if_frozen']]
             for r in dyn['moves_in_selected'] if r['temporarily_disadvantageous']]),'',
        f'Trong 100 nhiệm vụ tại λ minh họa, {dyn["temporarily_disadvantageous_moves"]}/{dyn["move_count"]} lần dịch chuyển DP có δu tức thời âm, '
        f'thuộc {dyn["temporarily_disadvantageous_missions"]} nhiệm vụ. Đường tiếp tục có gain còn lại không âm so với đứng yên tại điểm trước trong mọi event được kiểm tra. '
        'Tại ID84 slot2, cả hai điểm đều thông thoáng nhưng DP di chuyển trước khi điểm cũ sẽ bị chặn 21 slot trong phần horizon còn lại. '
        'Đây là bằng chứng số trực tiếp cho quyết định nhìn trước; độ lớn gain phụ thuộc counterfactual đứng yên đã nêu, không phải tách nhân quả tuyệt đối của lookahead.','',
        'ID9 là trường hợp Greedy và DP cho cùng K, D=200 m, U và cùng đường 80→60 với một lần chuyển ở slot14, đúng lúc điểm80 bị chặn. '
        'Phản ứng một bước đủ cho cấu trúc mây của trường hợp này. ID0 không cần mobility theo U: P2/DP ở index80 thông thoáng cả 30 slot; '
        'Greedy bắt đầu index90 rồi chuyển100 m sang80, thu thêm một lượng K nhỏ nhưng không bù được phạt. '
        'Không dựng quỹ đạo minh họa đẹp hơn và không kết luận mobility luôn hữu ích.','',
        '## 8. Khi nào mobility có lợi?','',
        'Tạo upper bound từ chính S: Kslot=mean_n max_j S[j,n], không ràng buộc vận tốc. '
        'H=Kslot−K_P2 đo headroom thời gian–không gian còn lại sau chọn một vị trí. Đây là bound bằng dữ liệu đã lưu, không phải một thuật toán trajectory mới. '
        'Nếu H=0, không đường nào có K cao hơn P2; với λ≥0, dịch chuyển không thể tạo gain objective dương.','',
        table(['Điều kiện tại λ minh họa','N','Mean ΔK DP−P2','Mean ΔU DP−P2','Tỷ lệ thắng U','Mean D DP (m)'],
            [[r['group'],r['missions'],f(r['mean_delta_K']),f(r['mean_delta_U']),f(r['strict_U_fraction']),f(r['mean_DP_distance_m'])] for r in dyn['groups']]),'',
        '33 nhiệm vụ P2 còn ít nhất một slot chặn đều có gain U DP dương; mean ΔU của nhóm này lớn hơn nhóm P2 thông thoáng cả30 slot. '
        'Ngay khi P2 đã thông thoáng, một số đường vẫn có lợi nhỏ nhờ khai thác các vị trí clear-sky K cao hơn ở những thời điểm phù hợp. '
        'Bảy nhiệm vụ có H≈0 không có gain từ mobility. Mây đồng nhất theo vị trí hoặc điểm tốt đã thông suốt cả horizon làm giảm headroom; '
        'mây chặn phần lớn vùng cùng lúc không tạo được lợi thế chỉ nhờ dịch chuyển. Các phát biểu sau là cơ chế theo S, không phải kết quả của một sweep mây mới.','',
        table(['Feature','Spearman ρ với ΔK','Spearman ρ với ΔU'],
            [[feature,f(next(r['Spearman_rho'] for r in dyn['correlations'] if r['feature']==feature and r['target']=='delta_K_DP_Stationary')),
              f(next(r['Spearman_rho'] for r in dyn['correlations'] if r['feature']==feature and r['target']=='delta_U_DP_Stationary'))]
             for feature in ('global_blocked_fraction','spatial_clear_fraction_sd','entirely_clear_positions','p2_clear_fraction','oracle_headroom')]),'',
        'Các tương quan chỉ là exploratory trên100 scenario đã dùng. Headroom và ΔK cùng được dựng từ S nên tương quan mạnh một phần mang tính cấu trúc; '
        'không diễn giải là bằng chứng nhân quả độc lập hoặc predictor đã xác thực trên held-out.','',
        '![G](figures/G_cloud_headroom_gain.png)','',
        '## 9. Giới hạn khoa học và gói kiểm chứng','',
        '1. Finite-grid DP là tối ưu điều kiện theo S và horizon đã cho; không tối ưu quỹ đạo liên tục hoặc vị trí giữa ô. '
        'Finite-source P1 có VA=8 ở trần; không continuous/global optimum.','',
        '2. P2/DP dùng toàn bộ cloud-state matrix offline. Greedy vẫn có oracle trạng thái hiện tại ở mọi vị trí; '
        'không mô hình hóa ước lượng/feedback, trễ, dự báo sai hoặc mây chưa quan sát.','',
        '3. Complete blockage, hình học và Gaussian-copula mây là tổng hợp. Không có sensitivity mới theo p, ell, rho hoặc dữ liệu thời tiết thực. '
        'Slot tương quan nội bộ không làm tăng số mẫu độc lập vượt100.','',
        '4. Thời gian bay và reacquisition không trừ khỏi usable slots; không tính outage dọc đoạn di chuyển, gia tốc, năng lượng, hoặc chi phí triển khai/đường về. '
        'Quãng đường chỉ là surrogate, λ không được hiệu chuẩn sang joule. Không suy ra bits/s, tổng bit hay bits/J khi chưa có channel-use rate.','',
        '5. MI 2D ghép Holevo homodyne là functional số theo manuscript, chưa là homodyne protocol security proof. '
        'Không có kết luận composable/finite-size, attack-class mới, parameter-estimation hoặc xác nhận bảo mật từ CI/tests. '
        'Giữ `UNVALIDATED_SECURITY_MODEL` và `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.','',
        '6. Hash frozen hiện tại df83ea63…db78c15 khác giá trị lịch sử 561fecc9…a7b1; giữ nguyên discrepancy, Objective C USER_STOPPED và mọi lifecycle blocker. '
        'Không sửa pipeline, cache, frozen spec, bản thảo ngoài repo, commit hoặc push.','',
        'Nguồn gốc: `startup_manifest.json`, `analysis_summary.json`, `computation_validation.json`, '
        '`analysis_receipt.json` (kiểm tra hậu xuất hình/report và hash toàn gói), cùng hai script producer. '
        'Receipt gốc được xác thực trực tiếp theo danh sách hash của nó; không chạy lại verifier gốc vốn quét đệ quy cả thư mục mới analysis/. '
        '24 test/346 checks của lượt mô phỏng là evidence cũ được kiểm tra provenance, không tuyên bố đã chạy lại chúng trong nhiệm vụ phân tích này.','',
        '## 10. Trả lời định lượng tám câu hỏi cuối','',
        f'1. **Nguồn P1:** MB (ν,VA)=(0,125;8), không đổi ở100/100 vị trí; nguồn thứ hai(0,15;8), gap '
        f'{f(gap["min"])}–{f(gap["max"])} bits/use. Ổn định trong miền hình học đã khảo sát, chưa xác thực perturbation quang học khác; VA=8 là trần.','',
        f'2. **P2 chọn đâu:** index40=(50,450)m và90=(50,950)m cùng8/100 lần; tiếp theo50,10,20 cùng7 lần. '
        f'Tổng {p2["unique_positions"]} vị trí khác nhau. P2 đạt mean K={f(p2["chosen"]["mean"])}, cao hơn tham chiếu44 {f(p2["gain_ratio_of_means_percent"])}%.','',
        f'3. **Gain mean K DP:** tại λ={f(representative)}, so với P2 {f(ps["mean"])} bits/use ({f(ps["ratio_of_means_percent"])}%), '
        f'so Greedy {f(pg["mean"])} ({f(pg["ratio_of_means_percent"])}%). Tại λ=0, tăng {f(paired("Stationary","K",0)["ratio_of_means_percent"])}% '
        f'và {f(paired("Greedy","K",0)["ratio_of_means_percent"])}%; không nội suy ra mọi λ.','',
        f'4. **Gain objective DP:** λ minh họa: ΔU/P2={f(us["mean"])} ({f(us["ratio_of_means_percent"])}%), '
        f'ΔU/Greedy={f(ug["mean"])} ({f(ug["ratio_of_means_percent"])}%). Thắng U lần lượt61 và89/100, còn lại hòa.','',
        f'5. **Tăng λ:** meanD DP giảm {f(zero["D_mean"])}→0 m; meanK giảm {f(zero["K_mean"])}→{f(st["K_mean"])}. '
        f'100/100 DP đứng yên từ λ={f(penalties[7])}. Greedy có31 transition tăngD trên25 nhiệm vụ và dừng sớm hơn nhưng không đạt vị trí P2.','',
        '6. **Điều kiện lợi nhất:** P2 vẫn có slot chặn nhưng các vị trí khả thi khác thông ở các thời điểm bổ sung. '
        '33/33 nhiệm vụ như vậy có ΔU DP>0 tại λ minh họa; meanΔU=9,851524932e−6 bits/use so với2,043180039e−6 ở67 nhiệm vụ P2 thông hết. '
        'Đây là phân nhóm hậu nghiệm, không forecast ngoài dữ liệu.','',
        f'7. **Robust qua nhiệm vụ:** bootstrap CI95% meanΔU/P2=[{f(us["ci95_bootstrap_low"])},{f(us["ci95_bootstrap_high"])}], '
        f'meanΔU/Greedy=[{f(ug["ci95_bootstrap_low"])},{f(ug["ci95_bootstrap_high"])}] tại λ minh họa; '
        'cả hai dương nhưng không thắng mọi nhiệm vụ. Ở λ lớn DP hòa P2; không tuyên bố gain phổ quát.','',
        '8. **Có thể báo cáo:** số liệu finite-catalog/finite-grid, paired synthetic-mission means/distributions, tradeoff và witness quỹ đạo đã lưu. '
        '**Còn phải xác thực:** bảo mật homodyne/finite-size, thời tiết thực/dự báo causal, thời gian chuyển vị trí/tái thu, năng lượng đẩy, '
        'nguồn ngoài trần catalog, robustness các tham số khác và hiệu năng held-out.']
    (OUT/'report_analysis_vi.md').write_text('\n'.join(VI)+'\n',encoding='utf-8')
    write_english(s,data,paired,method,availability_share)


def write_english(s,data,paired,method,availability_share):
    p1,p2,dyn=s['p1'],s['p2'],s['dynamics'];li=dyn['representative_lambda_index'];lam=float(data['penalties'][li])
    mb=p1['summary']['MB_K_raw'];gap=p1['summary']['rank_gap'];ps,pg,us,ug=paired('Stationary','K'),paired('Greedy','K'),paired('Stationary','U'),paired('Greedy','U')
    dp,gr=method('DP'),method('Greedy')
    text=f'''# Draft: Numerical Results and Discussion

**Numerical-model scope: UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.**
This is a manuscript discussion draft from saved simulation artifacts. It does not assign an operational security claim or authorize publication evaluation.

## Evaluation setting and information assumptions

We analyze 100 synthetic cloud missions over 100 candidate locations in a 1 km × 1 km region. Each mission comprises 30 slots of 20 s, with a maximum inter-slot displacement of 300 m. The source catalog contains 197 Maxwell–Boltzmann (MB) and 36 Uniform 256-QAM ensembles with authenticated exact source moments. All policies use identical per-location source assignments, cloud masks, speed limits, and a freely selectable initial location. Deployment and return costs are omitted. Stationary positioning and dynamic programming (DP) are offline benchmarks with the complete cloud horizon, whereas Greedy observes all locations at the current slot only. Thus, equal feasibility and initialization assumptions do not imply equal information or identical realized starting locations.

We distinguish the average usable rate K, total distance D, and the objective U=K−λD/1000. The ten penalties were fixed from λhi={f(data['schedule']['lambda_hi'])} bits/use after source selection and before trajectory evaluation. Unless otherwise stated, the illustrative operating point is λ={f(lam)}=0.003λhi. Rates are in bits per channel use; a channel-use rate and propulsion-energy calibration are unavailable.

## Finite-catalog source optimization

All 100 locations select (ν,VA)=(0.125,8), with clear-sky rates ranging from {f(mb['min'])} to {f(mb['max'])} bits/use (spatial mean {f(mb['mean'])}; population spatial SD {f(mb['sd_population'])}). Link distances span {f(p1['summary']['distance_km']['min'])}–{f(p1['summary']['distance_km']['max'])} km and zenith angles {f(p1['summary']['zenith_deg']['min'])}–{f(p1['summary']['zenith_deg']['max'])} degrees. The runner-up is (0.15,8) throughout the region; its rate deficit is {f(gap['min'])}–{f(gap['max'])} bits/use, approximately 0.275–0.387% of the selected rate. This establishes ranking stability over the observed channel states, while also showing a relatively flat local catalog competition. It does not establish robustness to unswept optical/noise parameters. Moreover, VA=8 is the MB catalog ceiling; no continuous or global source optimum is claimed.

The best Uniform raw rate remains negative at every location, so its usable rate is zero throughout this region. The MB-minus-Uniform usable difference therefore equals the positive MB rate; a percentage gain over zero is undefined. Family-wise optimization also changes modulation variance, so this difference cannot be attributed solely to shaping at fixed energy. An additional comparison using the saved Uniform VA=8 ensemble gives a mean Uniform raw rate of {f(p1['summary']['Uniform_matched_K_raw']['mean'])} and a mean raw MB-minus-Uniform difference of {f(p1['summary']['matched_raw_gain']['mean'])} bits/use at equal mean energy. Equal peak amplitude or hardware requirements are not implied. Since the same MB ensemble is selected everywhere, the subsequent mobility gain does not require source switching along a trajectory.

## Stationary selection under blockage

The protocol already specifies the geometric reference index44 at (450,450) m. Although a separate fixed-reference strategy was not exported in the original run, its rate can be reconstructed directly from the saved rate matrix. This is a post-analysis baseline at an existing reference point, not a newly selected or preregistered operational baseline. Its mean rate is {f(p2['reference']['mean'])}, compared with {f(p2['chosen']['mean'])} bits/use for optimal stationary selection, a ratio-of-means increase of {f(p2['gain_ratio_of_means_percent'])}%. The paired absolute increase is {f(p2['gain']['mean'])}, with a Student-t 95% interval [{f(p2['gain']['ci95_t_low'])}, {f(p2['gain']['ci95_t_high'])}].

The selected stationary point varies across {p2['unique_positions']} locations. Indices40 and90 are most frequent, each selected in eight missions. Mean cloud-free availability rises from {f(100*p2['mean_reference_clear_fraction'])}% at the reference to {f(100*p2['mean_clear_fraction'])}%; 67 missions permit 30 clear slots at the chosen point. The highest clear-sky-rate location is selected in only eight missions, while 72 selections attain maximal mission cloud-free fraction. A symmetric algebraic decomposition attributes {f(availability_share)}% of the mean reference-to-stationary gain to the availability term. This decomposition is descriptive, not causal, but indicates that cloud avoidance dominates the additional clear-sky-rate improvement in this scenario. The gain assumes offline stationary selection with the complete mission realization.

## Mobility gain and statistical variability

At the illustrative penalty, DP attains mean rate {f(dp['K_mean'])} and mean distance {f(dp['D_mean'])} m, compared with {f(gr['K_mean'])} and {f(gr['D_mean'])} m for Greedy. DP increases mean rate by {f(ps['ratio_of_means_percent'])}% over Stationary and {f(pg['ratio_of_means_percent'])}% over Greedy. Mean objective improvements are {f(us['mean'])} ({f(us['ratio_of_means_percent'])}%) and {f(ug['mean'])} ({f(ug['ratio_of_means_percent'])}%), respectively. The reported percentages use differences of sample means divided by the positive baseline mean, rather than means of per-mission ratios.

We resample whole paired missions, preserving all within-mission spatial and temporal dependence and the common scenarios across methods and penalties. A 20,000-resample paired percentile bootstrap with seed20261019 yields 95% intervals [{f(us['ci95_bootstrap_low'])}, {f(us['ci95_bootstrap_high'])}] for DP-minus-Stationary objective and [{f(ug['ci95_bootstrap_low'])}, {f(ug['ci95_bootstrap_high'])}] for DP-minus-Greedy. Both are positive at the illustrative operating point. Nevertheless, DP strictly improves objective in only 61 and89 missions, respectively, with the remainder tied within 1e−12 bits/use. Unpenalized DP rate is lower than Greedy in25 missions, consistent with optimizing the penalized objective. These are pointwise intervals for mean numerical performance, without simultaneous multiplicity correction; they do not establish physical security or held-out generalization.

## Penalty-dependent movement and the role of lookahead

At λ=0, DP yields mean rate {f(method('DP',0)['K_mean'])} with mean travel {f(method('DP',0)['D_mean'])} m. Increasing λ reduces DP travel in every evaluated mission, and all DP solutions become stationary at the tested penalty {f(data['penalties'][7])}=0.1λhi. This monotonicity follows from the common feasible trajectory set and the linear distance penalty. The sampled penalties bracket the transition; they do not identify its exact continuous value. In contrast, Greedy has31 adjacent-penalty transitions with increased distance across25 missions. The initial divergence can favor a shorter local move at the larger penalty while changing subsequent routing. Because the same missions are reused, this is a deterministic finite-grid policy effect, not independent cloud resampling. At high penalties Greedy stops at its first-slot choice and can remain inferior to the horizon-optimal stationary solution despite zero travel.

Mission84, selected post hoc as the largest DP-minus-Stationary objective gain at the fixed illustrative penalty, shows why future information can help. DP avoids all blocked slots with five relocations and847.214m travel, compared with seven and1088.635m for Greedy. At slot2, DP moves from81 to80 while both locations are currently clear: its immediate objective increment relative to staying is negative, but remaining at81 would encounter21 blocked slots in the residual horizon. Across100 missions, 52 of112 DP moves have a negative immediate increment, in38 missions; their saved continuations have nonnegative residual gain over the feasible counterfactual of remaining at the previous location. These checks use stored trajectories and rate arrays only. They demonstrate anticipatory decisions but do not isolate the causal contribution of lookahead from oracle initialization and other decision differences.

Mission9 gives identical Greedy and DP paths, rates, objectives, and200m travel; a single reactive relocation suffices. Mission0 retains the original preselected illustration: DP and Stationary coincide at index80 with no travel, while Greedy travels100m for a small rate increment that does not offset the penalty. The three post hoc examples are explanatory and do not replace the100-mission statistics.

## Conditions for useful mobility and model limitations

Mobility is most valuable when no single high-rate location remains clear throughout the horizon but reachable alternatives offer complementary clear slots. At the illustrative penalty, all33 missions whose optimal stationary location experiences blockage obtain a positive DP objective gain; their mean increase is9.851524932e−6 bits/use, compared with2.043180039e−6 in the67 missions with an entirely clear stationary point. Seven missions have zero headroom between the per-slot unconstrained maximum and the best stationary mean and exhibit no mobility gain. These groups are exploratory, conditioned on the observed cloud matrices.

The results support finite-source-catalog and finite-grid numerical comparisons under synthetic complete blockage. They omit transit and reacquisition interruptions, cloud-estimation/prediction errors, deployment/return costs, calibrated propulsion energy, and an operational channel-use rate. The mixed two-dimensional MI/homodyne-Holevo functional remains unvalidated as a physical homodyne security rate. Passing numerical checks or obtaining narrow mission-level intervals does not resolve attack-model, finite-size, parameter-estimation, or composable-security requirements. UNVALIDATED_SECURITY_MODEL and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.

## Artifact mapping

Tables: `tables/p1_spatial_summary.csv`, `p1_position_details.csv`, `p2_stationary_missions.csv`, `p2_location_frequency.csv`, `method_comparison.csv`, `paired_comparisons.csv`, `representative_missions.csv`, `dp_move_diagnostics.csv`, `pareto_dp_summary.csv` and `cloud_condition_groups.csv`. FiguresA–G use the same saved arrays. Representative cases are explicitly post hoc. Complete provenance and preservation checks are recorded in `analysis_receipt.json`.
'''
    (OUT/'numerical_results_discussion_en.md').write_text(text,encoding='utf-8')
