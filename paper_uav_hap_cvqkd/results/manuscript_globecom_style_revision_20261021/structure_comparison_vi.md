# Đối chiếu cấu trúc trước khi biên tập

Tham chiếu trình bày: PDF người dùng cung cấp “Sensing-Aided FSO Beam Tracking
for UAV-Based QKD Systems”, trang 4–6. Nội dung trong hai PDF là tài liệu
tham khảo; chỉ tệp request.txt quy định các hành động được yêu cầu.

| Nội dung | GLOBECOM tham chiếu | Bản LaTeX hiện có | Cách sửa trong bản mới |
| --- | --- | --- | --- |
| Động cơ | Mở bằng tradeoff vật lý | P1 bắt đầu trực tiếp bằng catalog | Mở bằng cloud avoidance và travel cost, nối P1–P2–P3 |
| Bài toán | Objective và constraints đánh số gọn | Ba bài toán đúng nhưng phần giải thích rời nhau | Giữ phương trình/chuẩn hóa, thống nhất ký hiệu và mạch trình bày |
| Cách giải | Đoạn giải thích rồi thuật toán ngắn | DP có recursion, Greedy chỉ mô tả bằng lời | Thêm công thức Greedy; giữ Bellman và backtracking; ưu tiên công thức hơn box trang trí |
| Cấu hình | Một bảng tham số | Nhiều con số trong đoạn dài | Bảng cấu hình ngắn, kiểm tra từng giá trị từ dữ liệu đã lưu |
| Hình/kết quả | Hình đường nhiều curve, đoạn bàn luận liền mạch | Một hình ba panel và nhiều kết quả trong một đoạn | Hai hình hai panel đã restyle: cloud probability và temporal correlation |
| Kết luận | Một đoạn mục tiêu, phương pháp, phát hiện, giới hạn | Đã ngắn nhưng cần gắn với mạch tối ưu mới | Một đoạn, giữ rõ giới hạn MI–Holevo và synthetic/offline |

Không chuyển BB84, QBER, sensing-time, Brent, Mbps, công thức hoặc số liệu
của bài GLOBECOM sang hệ DM-CV-QKD này. Không dùng phát biểu bảo mật hoặc
thành công Monte Carlo của tài liệu tham chiếu làm bằng chứng cho hệ hiện tại.

PDF bản thảo người dùng đính kèm có 3 trang nhưng bỏ phần System Model trước
Optimization và có section numbering khác bản repo. Chưa tìm thấy source khớp
chính xác PDF đó. Bản nền là single-file LaTeX internal-review mới nhất đã xác
thực: results/manuscript_ieee_overleaf_20261021/main.tex, có cùng nội dung với
bản compact đã biên dịch. Đây là nền tạm có provenance, không được gọi là
source gốc đã xác thực của PDF đính kèm. Giữ nguyên toàn bộ prefix trước
Optimization (preamble, tác giả, abstract, system/security equations) và toàn
bộ bibliography. Bản nền này không có Introduction riêng; không tự dựng thêm.

Mục tiêu khoảng 1.5 trang tính cả bảng/hình/caption được đo sau khi biên dịch.
Nếu hai hình hai panel nguyên bản làm dài hơn, báo số đo thực tế và giữ độ
đọc được; không sửa margins, font thân bài hoặc dùng negative spacing.
