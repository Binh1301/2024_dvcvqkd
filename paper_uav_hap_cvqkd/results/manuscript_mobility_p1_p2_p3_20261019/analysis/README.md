# Phân tích dữ liệu đã lưu

Đọc [report_analysis_vi.md](report_analysis_vi.md) và
[numerical_results_discussion_en.md](numerical_results_discussion_en.md).

Không có lượt chạy P1/P2/P3/Greedy, evaluator, C,w hoặc cloud generator mới.
`analyze_saved_results.py` chỉ đọc CSV/NPZ và tạo thống kê, bootstrap và hình;
`write_analysis_report.py` kết xuất nội dung từ đúng summary ấy.

Sau khi receipt tồn tại, generator từ chối ghi đè gói đã hoàn tất. Kiểm tra lại
bằng lệnh sau, đứng tại gốc `2024_dvcvqkd`:

```powershell
paper_uav_hap_cvqkd/.venv/Scripts/python.exe -X utf8 -B paper_uav_hap_cvqkd/results/manuscript_mobility_p1_p2_p3_20261019/analysis/verify_analysis.py
```

Verifier độc lập kiểm lại arithmetic/statistics từ CSV gốc, bootstrap theo cặp,
hash, coverage, hình và liên kết. Nó không import mô-đun vật lý hay optimizer.
Không gọi verifier mô phỏng cũ: verifier đó quét đệ quy và không biết thư mục
analysis mới; thay vào đó xác thực nguyên vẹn 145 hash đã ghi trong receipt gốc.
Các receipt là hồ sơ integrity bằng SHA-256, không phải chữ ký mật mã.

Mọi bảng trong `tables/` giữ đơn vị gốc bits/use và mét. P05/P95 dùng quantile
nội suy tuyến tính. SD không gian P1 dùng ddof0, SD giữa mission dùng ddof1.
Bootstrap lấy lại toàn mission100 lần với replacement cho mỗi trong20000
replicates, seed20261019, cùng trọng số cho mọi method và lambda; đây không phải
sinh cloud realization mới. Tỷ lệ vô nghĩa do denominator≤1e-12 được để trống.

Ánh xạ dữ liệu hình:

| Hình | Dữ liệu |
|---|---|
| A | p1_position_details.csv |
| B | p2_location_frequency.csv; reference44 từ protocol gốc |
| C | Sao chép nguyên PDF/PNG fig3 gốc; method_comparison.csv tái dựng cùng số liệu |
| D | paired_comparisons.csv, mean ΔU và percentile-bootstrap CI95% |
| E, slot-rates | representative_missions/slot_details/cloud_maps.csv |
| F | mission_paired_gains.csv; hộp Q1–Q3, median, whisker1.5IQR, outliers |
| G | cloud_conditions.csv; trục hiển thị theo10^-6 bits/use, CSV giữ đơn vị gốc |

Các ví dụ ID84/9/0 được chọn hậu phân tích bằng tiêu chí ghi trong báo cáo, tại
lambda minh họa cố định từ trước. Chúng không thay nhiệm vụ minh họa gốc hoặc
được dùng để suy ra độ tin cậy thống kê. Cả100 nhiệm vụ vẫn góp vào mọi mean/CI.

Giữ UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS, frozen
hash discrepancy và Objective C USER_STOPPED. Không đồng nhất CI số với bảo mật,
quãng đường với joule, hoặc best-tested catalog/grid với nghiệm toàn cục liên tục.
