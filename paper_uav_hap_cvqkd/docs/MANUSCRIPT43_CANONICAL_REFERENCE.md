# Manuscript v43 — nguồn tham chiếu đã được tác giả xác nhận

Trạng thái: **ACTIVE_REFERENCE_USER_CONFIRMED** cho mô hình HAP–UAV manuscript43 được yêu cầu ngày 23/10/2026.

Người dùng xác nhận “đúng cái đấy rồi” khi được hỏi liệu bản đang có bên dưới có phải tài liệu được gọi là v43(2) trong yêu cầu. Do đó nguồn chuẩn của audit và các đối chiếu v43 tiếp theo là **chính nội dung theo hash**, dù tên file trên máy không có hậu tố (2).

| Mục | Giá trị |
|---|---|
| Tên trong yêu cầu | 2026__Binh_s_work (43)(2).pdf |
| File thực tế được xác nhận | C:\Users\HP\Downloads\2026__Binh_s_work (43).pdf |
| SHA-256 | f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b |
| Bản sao nguyên byte trong repository | [available_v43.pdf](../results/manuscript43_canonical_model_comparison_20261023/inputs/available_v43.pdf) |
| Audit toán học | [Báo cáo chi tiết](../results/manuscript43_canonical_model_comparison_20261023/report_vi.md) |
| Cập nhật sau xác nhận | [Báo cáo binding](../results/manuscript43_canonical_model_comparison_20261023/reference_binding_user_confirmed/report_vi.md) |
| Biên nhận xác nhận | [binding.json](../results/manuscript43_canonical_model_comparison_20261023/reference_binding_user_confirmed/binding.json) |

Đây là xác nhận của người dùng về danh tính tài liệu, không phải phép so sánh byte giữa hai PDF khác nhau. Không đổi tên PDF, công thức, numerical outputs hoặc cache để tạo sự tương đồng giả.

**Blocker thiếu PDF đã được giải quyết.** Những câu “chưa tìm thấy v43(2)” trong package audit đã seal trước xác nhận là lịch sử của lần kiểm tra đó; binding hiện tại nằm ở registry này và biên nhận bên trên.

## Nguồn chuẩn có lỗi phải được báo lỗi

Các phương trình bản thảo là nguồn toán học được người dùng chỉ định; các mâu thuẫn được audit phải giữ nguyên và fail closed, không tự sửa:

- Eq10 tại cấu hình Uniform30cm/divergence10µrad/jitter0,5µrad/σh0,03m/VA3 giữ mass 0,9013297245653482 trên [0,1]. SKR theo luật này vẫn **BLOCKED_PDF_NORMALIZATION**.
- K=0,10788256029424448 thuộc luật bounded random-width B=C, phân loại **DIFFERENT** so với Eq10; không được chuyển sang kết quả của manuscript.
- Vmod/quadrature, likelihood thực 1D với complex alpha, MB/centering và approximation khi rho khác0 vẫn cần sửa hoặc làm rõ. [Correction proposal v1](../results/manuscript43_canonical_model_comparison_20261023/correction_proposal_v1.md) giữ trạng thái **PROPOSAL_NOT_ADOPTED**.
- Chưa có production evaluator được phê duyệt là triển khai nhất quán toàn bộ manuscript. Cùng source đã xác thực, ba moment, T=mh², N chung, discrete Gaussian-effective homodyne MI và homodyne covariance là pipeline đối chiếu; không fallback sang bounded và không thêm eta_det.

Registry này giải quyết danh tính tham chiếu cho scope manuscript43. Các frozen experiment trước đây vẫn thuộc snapshot/phạm vi lịch sử của chúng; không ghi đè FINAL_MODEL_SPEC.md hoặc tự sửa protocol heterodyne cũ. Sai khác frozen hash đã ghi nhận vẫn được giữ. Không có security, production, optimization hoặc lifecycle approval từ việc xác nhận PDF.

Giữ **UNVALIDATED_SECURITY_MODEL**, **NOT_READY_FOR_PUBLICATION_SCALE_RUNS**, ObjectiveC **USER_STOPPED**. Source C,w, kết quả cũ và scientific production giữ nguyên.
