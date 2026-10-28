# Báo cáo sửa bản thảo từ III.B đến Conclusions

Ngày: 2026-10-21. Phạm vi cuối cùng theo lựa chọn trực tiếp của người dùng:
**chỉ bàn giao LaTeX và hình, chưa biên dịch**.

## Bản nền và ranh giới chỉnh sửa

Bản nền là `results/manuscript_ieee_overleaf_20261021/main.tex`, bản single-file
đã có receipt hoàn tất, cùng PDF đã biên dịch của nó. Bản GLOBECOM trước đó
`manuscript_globecom_style_revision_20261021/` có nguồn/PDF nhưng chưa có
receipt hoàn tất và còn lỗi ngắt kết luận theo báo cáo cũ; không dùng làm bản
nền đã hoàn tất. Các bản compact và IEEE revision trước đó cũng được đối chiếu.

Nguồn được xác nhận theo lịch sử repository, chưa được xác nhận là nguồn gốc
khớp tuyệt đối một PDF bên ngoài. Không tự dựng Introduction còn thiếu.
Title, tác giả TBD/XXX, abstract, toàn bộ lời văn khoa học, công thức trước
phần tối ưu và bibliography được giữ nguyên. Kiểm tra phục hồi các heading
cho thấy prefix trước tối ưu giống hoàn toàn bản nền sau khi đảo hai thao tác
heading đã ghi trong `validation/heading_edits.json`.

Bản nền có một Section I và hai subsection. Để đạt đúng III.B/IV/V bằng bộ
đếm section tự động, chỉ đổi heading mô hình vật lý thành Section II, thêm
Section III tại điểm bắt đầu mô tả MI và đặt phần bảo mật sẵn có vào III.A.
Không sửa, di chuyển hoặc viết lại đoạn khoa học hay công thức tại đây.
III.B bắt đầu ở `\subsection{SKR Performance Optimization}` trong `main.tex`.

Hai hình mới giữ số 2 và 3 theo yêu cầu bằng một offset của bộ đếm figure.
Bản nền không có hình hệ thống phía trước để làm Fig. 1; không tạo hình giả
hoặc tự bổ sung nội dung ngoài phạm vi. Đây là một giới hạn của nguồn nền,
cần đồng bộ khi ghép với bản thảo đầy đủ của tác giả.

## Đối chiếu GLOBECOM và thay đổi đã thực hiện

PDF tham chiếu tại Downloads có SHA-256
`04fbdd7d6bce2642888e730f75ddc04523874458d847057c93a5476457bd52b2`, khớp manifest
cũ. Đã đọc và xem trang 4, 5, 6; lưu bản sao và ảnh kiểm tra trong `references/`.

- III.B mở bằng tradeoff cloud avoidance--distance, sau đó trình bày P1/P2/P3,
  giải thích biến và ràng buộc, Bellman, baseline Greedy và thuật toán DP.
- Giữ raw-rate maximization trước clipping, finite-catalog optimality, free
  initial position, feasible staying, giới hạn tốc độ và hệ số Bellman
  `Nt*lambda/D_ref`. Không thay bằng tối ưu liên tục hoặc thuật toán của bài mẫu.
- Algorithm 1 dùng float một cột, input/output, vòng lặp qua thời gian/vị trí,
  predecessor argmax, lưu backpointer, chọn terminal và backtracking. Caption
  dài có thể chiếm hai dòng; chưa kiểm tra bố cục sau biên dịch.
- Section IV mở ngắn, có Table I với hai cặp Parameter/Value mỗi hàng, Fig. 2
  một cột, Fig. 3 hai panel rộng, các đoạn bàn luận liền mạch theo thứ tự hình.
- Section V là một đoạn kết luận ngắn với future work khiêm tốn.
- Bỏ bảng runtime tùy chọn vì không cần thêm cho phạm vi trình bày này; không
  bịa runtime hoặc so sánh tốc độ thực thi.

Các label công thức được giữ: `eq:raw`, `eq:p1`, `eq:p2`, `eq:p3`, `eq:dp_init`,
`eq:dp`, `eq:greedy`. Các label section/bibliography và bốn mục tài liệu tham
khảo cũng được bảo toàn. Label `sec:method` trỏ đến III.B vì phần giải pháp
được tích hợp trong subsection này.

## Hình và dữ liệu

| Hình | Nội dung | Nguồn CSV đã lưu |
| --- | --- | --- |
| Fig. 2 | Zero-rate unavailability theo p; Stationary/Greedy/DP | `fig2_cloud_blockage_data.csv`, metric `unavailability_percent` |
| Fig. 3(a) | Mean penalized objective theo J | `fig1_candidate_positions_data.csv`, metric `U` |
| Fig. 3(b) | Mean travel distance theo latent rho | `fig3_temporal_correlation_data.csv`, metric `D` |

CSV nguồn thuộc bộ final 20261020, được đối chiếu với receipt và bản restyle
IEEE classic 20261021. Chỉ dựng lại các panel từ đúng mean/CI đã lưu:
24 + 18 + 15 = 57 điểm, không nội suy hoặc resampling. Trục đều tuyến tính
vì đúng metric/dải tương ứng; số 0 được giữ nguyên. Fig. 3(b) bao gồm đường
Stationary bằng 0. PDF là vector; PNG 350 dpi. Font Times New Roman, nét mảnh,
marker circle/triangle/diamond, grid chấm nhẹ và legend trong khung.
Đã xem cả hai PNG ở kích thước xuất; chưa kiểm tra kích thước hiển thị trong
PDF bản thảo vì chưa biên dịch.

`figure_manifest.csv` ghi đường dẫn/hash nguồn và đích. Trong bảy receipt có
743 thành viên: 638 khớp SHA-256 nhị phân; 105 tệp văn bản chỉ khác CRLF/LF.
105 tệp này khớp nội dung sau đổi CRLF thành LF, không được mô tả là khớp hash
thô. Không có thay đổi nội dung chưa giải thích; các hình nguồn PDF/PNG khớp
hash nhị phân. Chi tiết ở `validation/authenticated_inputs.json`.

## Các số được đối chiếu

| Đại lượng | Giá trị dùng trong bản thảo |
| --- | --- |
| p=0.8: unavailability P2/Greedy/DP | 24.60% / 16.53% / 4.07% |
| J=10→100: tăng objective DP | 11.409% |
| rho=0→0.98: distance DP | 1038.25→31.84 m |
| rho=0→0.98: gain objective DP/P2 | 23.712%→0.155% |
| lambda_ref so với 0: giảm distance DP | 88.370% |
| lambda_ref so với 0: giảm mean usable rate DP | 0.515% |
| Mặc định: gain usable rate DP so P2/Greedy | 4.16% / 2.70% |
| Mặc định: gain objective DP so P2/Greedy | 3.07% / 4.42% |

Table I lấy đúng `configs/manuscript_mobility.json`: HAP/UAV 20/1 km,
1550 nm, full divergence 233 microrad, receiver diameter 0.08 m, beta=0.95,
xi_ch=0.0186 SNU, vùng 1×1 km², J=100, Nt=30, Delta t=20 s, vmax=15 m/s,
Dref=1000 m, 100 missions, p=0.4, ell=250 m, latent rho=0.9. Không dùng khẩu
độ 0.55 m hoặc phân kỳ của thí nghiệm khác.

## Bố cục, xác minh và giới hạn

`main.tex` dùng IEEEtran conference A4, giữ nguyên preamble/font/margins từ
bản nền, không negative spacing hoặc giảm font thân bài. Có một algorithm,
một table, một figure một cột và một figure* hai panel. Cấu trúc nguồn tương
ứng mẫu GLOBECOM; chưa thể xác nhận float placement, tràn dòng hoặc độ dài.

**Biên dịch: NOT_RUN theo lựa chọn người dùng. Không có main.pdf mới.**
Độ dài thực tế phần III.B–V và phương án tối thiểu đọc được: **chưa đo**;
không dùng số 1.674 trang của bản cũ để gán cho bản mới. So sánh trực quan
PDF cũ/mới chưa thực hiện; chỉ PDF cũ và hai hình mới đã được xem.

Lần tải trình biên dịch chính thức bị bộ kiểm duyệt tự động từ chối vì áp dụng
phạm vi “chỉ đọc” của lượt trước. Sau đó người dùng chọn bàn giao nguồn/hình,
không tiếp tục tải hoặc biên dịch; không đi vòng qua từ chối.

Mô hình MI I/Q hai chiều, Holevo điều kiện homodyne, detector ideal trusted,
fading effective moments và catalog exact được giữ nguyên. Kết quả vẫn là
đầu ra có điều kiện của evaluator chưa nhất quán phép đo Bob, không xác nhận
khóa bí mật vật lý. Giữ `UNVALIDATED_SECURITY_MODEL`,
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`, frozen-hash discrepancy và Objective C
USER_STOPPED. Hash spec hiện tại `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
khác hash lịch sử trong AGENTS; chỉ ghi nhận, không sửa spec hoặc dùng để nâng
trạng thái khoa học.

Không chạy SKR/channel/source optimization, Greedy, DP, sinh mây, AP hoặc
thống kê mới; không sửa production/cache/config/frozen spec; không commit/push.

## Tệp bàn giao

- [LaTeX đầy đủ](main.tex), bibliography inlined.
- [ZIP nguồn cho Overleaf](overleaf_III_B_revision.zip).
- [Fig. 2 vector](figures/fig2_cloud_unavailability.pdf), [PNG](figures/fig2_cloud_unavailability.png).
- [Fig. 3 vector](figures/fig3_parameter_sensitivity.pdf), [PNG](figures/fig3_parameter_sensitivity.png).
- [Manifest hình](figure_manifest.csv), [báo cáo kiểm tra](validation_report.md).
