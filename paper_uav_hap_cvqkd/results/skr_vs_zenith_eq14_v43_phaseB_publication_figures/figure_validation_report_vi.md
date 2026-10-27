# Kiểm chứng hình SKR theo góc zenith

**CURRENTLY_VERIFIED_PASS cho dữ liệu/dựng hình; phạm vi khoa học vẫn DIAGNOSTIC_ONLY.**

Chỉ đọc hai CSV và report của namespace 61 góc đã seal; không import evaluator. Hàm `select` gốc được trích bằng AST và chỉ xếp hạng raw K đã lưu. 12.932 candidate được kiểm tra; 183 lựa chọn khớp chính xác source identity, VA/nu/C/w và raw SKR binary64 với `best_scheme_by_angle.csv`. Mỗi scheme đủ 61 góc 0–60°, bước 1°; cùng pool 212 nguồn ở mọi góc.

| Scheme | Max raw SKR (bits/use) | Góc | Điểm dương đã lấy mẫu | Khoảng đổi dấu |
|---|---:|---:|---|---|
| Uniform | -0.030747146463279806 | 60° | Không có | Không quan sát |
| Fixed MB | 6.5223770664923908e-05 | 0° | 0–5° | [5, 6]° |
| Optimized MB | 0.00079608780808612667 | 0° | 0–15° | [15, 16]° |

Các expected values trong task chỉ dùng làm consistency check (tolerance 5e−12 do bảng làm tròn); tọa độ hình lấy nguyên giá trị CSV. Đường nối trực tiếp các mẫu, không smooth, không tạo điểm số học, không nội suy giá trị thiếu và không clip raw K về 0. Hình đầy đủ giữ cả 183 mẫu; zoom chỉ lấy 19 mẫu 0–18° của mỗi MB scheme, được ghi rõ “MB schemes only” và caption. Các khoảng tô màu chỉ kẹp dấu trên lưới.

Typography: Times New Roman; axis 9.5 pt, ticks 8.5 pt, legend 8 pt, line 1.65 pt; PNG 600 dpi và PDF vector. Hình đơn rộng 3.5 inch, hình hai panel rộng 7.16 inch trước tight cropping. Không có decorative title hoặc watermark lớn; DIAGNOSTIC_ONLY nằm trong caption/metadata.

Cấu hình số học/vật lý được giữ nguyên qua hash physical protocol. Không tính channel, MI, Holevo, C,w hay SKR mới. Không sửa production, manuscript, frozen spec hoặc source cache; không chạy historical verifier có phép tính số học.

Mọi raw K dương vẫn phụ thuộc INSUFFICIENT_EVIDENCE. Uniform thiếu nguồn nu_raw=0, VA=1.6249995399703647; không suy ra nghiệm tối ưu toàn miền. Strict Phase B vẫn BLOCKED do 73 nguồn pilot thiếu evidence hội tụ và một Uniform thiếu payload/receipt. UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.

Frozen-spec current/historical hash discrepancy đã có trong hồ sơ readiness, không được sửa hoặc bypass; dựng hình từ CSV không giải quyết blocker mô hình.

9621 file lịch sử được bảo vệ đã giữ nguyên SHA256. Chi tiết dữ liệu: `figure_data_validation.json`; QA bản xuất PDF/PNG và kiểm tra cuối: `export_validation.json`. Script tái dựng tất cả hình chỉ từ CSV đã lưu; `figure_captions.tex` chứa ba caption tiếng Anh và snippets LaTeX.

Ki?m tra b?n xu?t ho?n t?t: c? ba PDF m?/render b?ng pypdfium2 (Poppler kh?ng c?), font Times New Roman/STIX ???c nh?ng d??i d?ng Type0, kh?ng c? image XObject raster, ???ng vector v? native text hi?n di?n. T?t c? character bounding boxes n?m trong trang; ?? xem ba PDF ? k?ch th??c IEEE, kh?ng c? overlap/clipping. PNG 2103?1623 px (hai h?nh ??n) v? 4299?1773 px (hai panel), nominal 600 dpi; metadata 599.9988 dpi l? l?m tr?n pixels-per-metre th?ng th??ng. Kh?ng c? discrepancy v?i CSV.

L?n ki?m tra QA ??u d?ng th? t? text c?a pdfplumber cho nh?n tr?c Y xoay, n?n kh?ng nh?n ra nguy?n c?m t?. ?? d?ng pypdf cho n?i dung text v? pdfplumber cho t?a ?? k? t?; d? li?u/h?nh kh?ng thay ??i v? v?n ?? extraction n?y. Kh?ng bi?n d?ch manuscript/LaTeX ho?c ch?ng nh?n source convergence; caption LaTeX ???c cung c?p ?? ch?n v?o b?i.
