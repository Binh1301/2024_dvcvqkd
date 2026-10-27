# Zenith sweep manuscript43

Mở report_vi.md để xem phạm vi nguồn exact, tham số, cực đại và khoảng SKR dương.
skr_vs_zenith.png là PNG350dpi; skr_vs_zenith.pdf là hình vector.
skr_vs_zenith.csv giữ đủ183 dòng, gồm raw SKR âm và lý do loại.

Mô hình của khảo sát này dùng Gaussian-effective homodyne1D, reverse
reconciliation, xi_det=.005 độc lập và không có eta_det. Giữ PDF43 trên[0,1],
atom AoA và mass tolerance1e-10. Không dùng random-width surrogate.

Optimization chỉ là exhaustive raw-SKR argmax trong36 Uniform và197 MB
source points đã xác thực, không là optimum liên tục/toàn cục.
Fixed MB dùng nu_raw=.25,VA=1.6249995399703647 từ receiver30.
Không tính source C,w mới, nội suy hoặc ghi đè cache.

Kiểm tra chỉ đọc từ thư mục project:

    .\.venv\Scripts\python.exe -X utf8 -B results/skr_vs_zenith_manuscript43_20261023/verify.py

Verifier dùng standard library, không import evaluator hoặc chạy optimization.
Các phase đã hoàn tất từ chối ghi đè. Không xóa receipt để chạy lại.
Một lần tái lập mới cần namespace/startup/protocol riêng và cùng input hashes.

Các producer đã thực thi theo thứ tự:

    .\.venv\Scripts\python.exe -X utf8 -B results/skr_vs_zenith_manuscript43_20261023/run_sweep.py
    .\.venv\Scripts\python.exe -X utf8 -B results/skr_vs_zenith_manuscript43_20261023/render_and_report.py

angles/ chứa đầy đủ candidate ranks, optical/PDF moments và selected-point
checks theo góc. Các checkpoint chỉ được tái dùng với đúng producer/protocol
hash; không sử dụng SKR lịch sử khác model. source_catalog.csv ghi identity
và hash của từng source. protocol.json ràng buộc evaluator trước sweep;
figure_receipt.json ràng buộc presentation producer và source CSV.

Hình PDF được kiểm tra bằng render riêng và PNG được xem trực quan.
visual_review.json ghi các hash đã xem. final_receipt.json đóng dấu artifacts
và task ledgers; các ledger receipt cũ vẫn là snapshot lịch sử.

Không sửa production/frozen/history/cache, không training/final-test/heldout/
publication evaluation, baseline/threshold approval hoặc commit/push.
Giữ UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
