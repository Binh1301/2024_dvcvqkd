# Manuscript43 homodyne audit

Mở report_vi.md để xem kết luận, công thức, bảng detector và old-versus-new.
manuscript_corrections_vi.md liệt kê các đề xuất sửa PDF theo loại phát hiện.
protocol.json giữ tiêu chí đặt trước; variants.json phân biệt A/B/C.
Bảng tham số ở đầu report_vi.md và scenario_parameters.csv.
noise_moment_checks.csv đối chiếu288 moment nhiễu từ tích phân PDF đã lưu.

**Đây là audit đã hoàn tất, có các blocker khoa học. Không có secure default.**
C là thành phần Gaussian homodyne/untrusted đã qua kiểm tra số học khi input
guards đạt. PDF gốc không đạt mass tolerance ở 30/40/55 cm. K của 28,1 cm đổi
dấu từ dương sang âm khi đổi actual pooled MI sang Gaussian effective MI,
với cùng channel moments và source. Không suy rộng kết quả giữa hai channel laws.

Từ thư mục paper_uav_hap_cvqkd, chỉ đọc bằng:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/verify.py

Verifier dùng standard library, không import evaluator, không chạy MI/Holevo
hoặc tái tạo dữ liệu. Nó kiểm tra hash, receipts, CSV và các bất biến đã lưu.
final_receipt.json đóng dấu cả producer, artifacts và năm ledger.

Chuỗi lệnh đã thực thi cho nghiên cứu này, theo thứ tự:

    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/run_audit.py regress
    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/run_audit.py validate
    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/compare.py
    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/audit_inventory.py
    .\.venv\Scripts\python.exe -X utf8 -B results/manuscript43_homodyne_audit_20261023/build_report.py

**Không chạy lại chuỗi trên trong namespace đã đóng dấu.** Các producer số học
từ chối ghi đè các phase đã hoàn tất; đây không phải lỗi cần xóa receipt để vượt qua.
Tái lập mới cần namespace riêng, startup manifest và protocol/hash mới, cùng đúng
historical files và exact-source payloads. Không dùng kết quả cũ nếu input hash đổi.
Không phát sinh AP hoặc nội suy C,w. Packages số học dùng sẵn trong project venv;
execution_history.json ghi phiên bản môi trường.

inputs/ giữ bản sao byte-identical của yêu cầu và PDF bốn trang, text và PNG từng
trang. capture_pdf.py chỉ đọc PDF, dùng PyMuPDF 1.26.5 ở công cụ tạm ngoài project;
không thêm dependency vào project venv. Bản sao PDF và hash đã đủ cho audit chỉ đọc.
Các PNG trang 2–4 đã được xem để kiểm tra phương trình và tài liệu tham khảo.

attempt_1/ bảo toàn code/test receipt và lỗi tích hợp KeyError B trước khi sửa
caller sang đúng lognormal/Rician factory. Không sửa tiêu chí/tolerance để đạt PASS.
protocol.initial_implementation_sha256 trỏ đến các producer ban đầu này;
execution_history.json và final_receipt.json ghi producer cuối cùng.

repository_map.csv ghi hàm:dòng của 37 file đã kiểm tra. affected_results.csv
liệt kê 252 result entries (thư mục và tệp ở root) với phạm vi tái đánh giá; cache_impact.csv ghi
287 entries, bao gồm 233 source payloads đã xác thực. Các mục chưa tính lại
không được coi là đã được thẩm định. isolated_code_patch.diff là patch của các
script/config mới; scoped_ledger_changes.diff là thay đổi năm ledger so với startup.

Không sửa src/, frozen specifications, production configs, source caches hoặc
historical outputs. Không optimization/training/final-test/heldout/publication,
baseline selection, threshold approval hoặc commit/push. Giữ trạng thái
UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
