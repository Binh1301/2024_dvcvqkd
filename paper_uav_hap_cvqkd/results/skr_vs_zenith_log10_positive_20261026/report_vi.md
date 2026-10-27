# Hình SKR theo zenith — log cơ số 10, chỉ hiện phần dương

Đã tạo `skr_vs_zenith_log10_positive.pdf` (vector) và PNG 600 dpi,
giữ màu, marker, font và trục X 0–60° của bản gốc. Trục Y là log thật cơ số 10,
nhãn 10^-5, 10^-4, 10^-3; không phải lấy log rồi đổi đơn vị của dữ liệu.

Theo yêu cầu mới, chỉ hiển thị K_raw>0: Fixed MB có 6 mẫu tại 0–5°,
Optimized MB có 16 mẫu tại 0–15°. Uniform không có mẫu dương nên không có
đường dữ liệu; legend ghi rõ “no positive samples”. Không vẽ đường K=0 trên
trục log. Các đoạn kết thúc tại mẫu dương cuối, không nội suy tới điểm đổi dấu.

Ẩn 161 mẫu âm chỉ ở lớp hiển thị bằng NaN; toàn bộ 183 hàng gốc và CSV
candidate vẫn giữ nguyên. Không đổi SKR, không clip âm về 0, không thêm điểm,
không làm mượt và không tính mới C,w/channel/MI/Holevo/SKR. Bản PDF tuyến tính
cũ và toàn bộ gói hình cũ được giữ nguyên trong namespace lịch sử.

Dữ liệu lấy từ `results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/`
với cùng cấu hình 30 cm/35 µrad/1.561 µrad, homodyne và Eq. (14) trực tiếp.
Tái sử dụng hàm kiểm tra dữ liệu và style của renderer đã seal, không chạy
runner mô phỏng. `plot_validation.json` lưu hash, số điểm và kiểm tra từng đường.

PDF đã render bằng PDFium và xem trực tiếp: nhãn 10^n đúng, không chồng lấn
hoặc cắt chữ/marker. Font được nhúng, không có image XObject raster trong PDF;
PNG 2103×1623 px, nominal 600 dpi. `export_validation.json` lưu bằng chứng QA.
10.274 tệp lịch sử được bảo vệ không đổi hash, gồm toàn bộ Phase E/E2.

Phạm vi vẫn **DIAGNOSTIC_ONLY**; không nâng phân loại nguồn, strict Phase B,
security hoặc lifecycle. Không chạy job precision400/500 đã chuẩn bị ở E2.
