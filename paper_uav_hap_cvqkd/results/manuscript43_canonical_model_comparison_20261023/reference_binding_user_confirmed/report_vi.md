# Đã xác nhận nguồn chuẩn v43 — bổ sung sau audit

Người dùng trả lời **“đúng cái đấy rồi”**, xác nhận file C:\Users\HP\Downloads\2026__Binh_s_work (43).pdf là tài liệu được gọi v43(2) trong yêu cầu. SHA-256 kiểm tra lại:

    f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b

Nội dung này trùng hash với PDF đã đọc và tính toán trong audit. Vì vậy **đã giải quyết blocker danh tính tài liệu**, không cần chạy lại evaluator hoặc tìm một PDF khác chỉ để có hậu tố (2).

Nguồn chuẩn hiện tại được ghi tại [MANUSCRIPT43_CANONICAL_REFERENCE.md](../../../docs/MANUSCRIPT43_CANONICAL_REFERENCE.md), với [binding.json](binding.json) lưu xác nhận, file/hash và ranh giới phạm vi. Đây là xác nhận chủ động của người dùng về nguồn, không phải bằng chứng tồn tại một file thứ hai.

[Báo cáo toán học đầy đủ](../report_vi.md), [54 parameter](parameter_provenance_bound.csv), [22 hàng phương trình](equation_comparison_bound.csv) và [35 component](component_classification_bound.csv) tiếp tục áp dụng cho **nguồn đã xác nhận này**. Các cảnh báo thiếu PDF trong package đã seal mô tả trạng thái trước xác nhận; không còn là blocker hiện tại.

[three_model_comparison_bound.csv](three_model_comparison_bound.csv) là view cập nhật metadata: requested_PDF_identity_verified=true; A là EXACT_MATCH về **biểu thức luật kênh**, B/C vẫn DIFFERENT. Tất cả giá trị số và validation_status giữ nguyên byte-value so với CSV trước. EXACT_MATCH của density không phê duyệt normalization, likelihood, source convention hoặc security.

Kết luận không đổi:

| Mục | Trạng thái hiện tại |
|---|---|
| Nguồn bản thảo | USER_CONFIRMED, binding hoàn tất |
| Eq10 ở cấu hình Uniform dương gần đây | Mass 0,9013297245653482; SKR BLOCKED |
| B và C | Cùng hàm random-width; K=0,10788256029424448 thuộc luật khác |
| Sửa notation/công thức | Proposal v1 chưa áp dụng |
| Evaluator production nhất quán toàn bộ manuscript | Chưa được thông qua |
| Security / publication readiness | UNVALIDATED / NOT_READY |

Không tính lại MI, Holevo, SKR hoặc C,w. Chỉ kiểm tra hash/provenance và cập nhật metadata tham chiếu. Audit cũ, receipts và seals giữ nguyên; verifier mới kiểm tra cả artifact cũ và binding hiện tại:

    .venv\Scripts\python.exe -X utf8 -B results/manuscript43_canonical_model_comparison_20261023/reference_binding_user_confirmed/verify.py

Verifier cũ ràng buộc hash ledger tại thời điểm trước xác nhận; dùng verifier mới cho current binding thay vì ghi đè seal lịch sử.
