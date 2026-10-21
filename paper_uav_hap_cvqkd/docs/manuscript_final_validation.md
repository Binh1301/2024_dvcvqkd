# Kiểm chứng bản thảo IEEE — 2026-10-20

**Hoàn tất bản sửa để phản biện nội bộ; chưa đủ điều kiện nộp như một công bố
khẳng định an toàn lượng tử.** Kết luận bảo mật: `INCONSISTENT_MEASUREMENT_PAIRING`,
`UNVALIDATED_SECURITY_MODEL`. Giữ `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Tệp bàn giao và nguồn bản thảo

Thư mục riêng: `results/manuscript_ieee_revision_20261020/`.

- `main.tex`, `system_and_method.tex`, `numerical_results.tex`,
  `manuscript_refs.bib`: bộ nguồn IEEEtran.
- `main.pdf`: PDF A4, hai cột, 6 trang, dành cho phản biện nội bộ.
- `figures/`: bốn PDF vector được sao chép nguyên byte từ gói kết quả cuối.
- `README.md`: phạm vi sửa, cách biên dịch, các quyết định cần tác giả xử lý.
- `input_manifest.json`, `startup_manifest.json`, `validation/verification.json`,
  `validation/final_receipt.json`: truy vết và bằng chứng kiểm chứng.
- `docs/security_model_consistency_audit.md`: kiểm toán phương trình, bảng phân
  loại, dẫn nguồn sơ cấp và đề xuất sửa **chưa áp dụng**.

Không tìm thấy `.tex` tương ứng đúng với PDF mới nhất sau khi tìm trong repo,
Documents, Desktop, Downloads và tệp đính kèm. Vì vậy, bản sửa được dựng từ
`original/manuscript_latest.pdf` (bản PDF ba trang đã dùng cho thí nghiệm).
Preamble và khối tác giả lấy nguyên từ tệp LaTeX cũ có sẵn
`original/HAP_UAV_Availability_Mobility_Overleaf.tex`. Giữ `TBD`, `XXX` và
University of Aizu; không sáng tác tên hoặc đơn vị. Không nhập mô hình mây tròn
hay mục tiêu availability của bản LaTeX cũ vào nghiên cứu hiện tại.

Độ trung thực của một phép merge theo dòng với `.tex` mới nhất là **NOT VERIFIED**
vì tệp đó chưa được cung cấp. Đây là giới hạn nguồn bản thảo, không phải lỗi
biên dịch. Bản PDF gốc, tệp LaTeX cũ và mọi kết quả lịch sử được bảo toàn.

## Nội dung đã tích hợp

1. Abstract và Conclusion được viết lại theo số liệu thật, ghi rõ tính chất
   provisional/internal review và không khẳng định tạo khóa an toàn vô điều kiện.
2. Phần I giữ bài toán gốc, bổ sung chuẩn hóa nguồn, noise referral, AoA và
   ranh giới mô hình bảo mật. Các công thức lịch sử được mô tả đúng, không sửa
   evaluator để tạo kết quả khác.
3. Phần II làm rõ catalog hữu hạn, chọn raw trước clipping, nguồn exact riêng
   theo ensemble, P2 offline, Greedy chỉ đọc slot hiện tại, hệ số `Nt lambda`,
   DP/Bellman/backtracking và độ phức tạp. Đối chiếu bằng đọc mã, không chạy solver.
4. Phần III có đúng A–F: setup; candidate positions; blockage probability;
   temporal correlation; SKR–mobility tradeoff; discussion/limitations.
5. Bốn hình, Table I và bốn tài liệu tham khảo sơ cấp được tích hợp. Giữ chuỗi
   phương trình có số (1)–(15); các công thức kiểm toán bổ sung không đánh số.

## Biên dịch và kiểm tra PDF

**CURRENTLY_VERIFIED_PASS cho biên dịch và kiểm tra tài liệu trong phạm vi này.**
Portable Tectonic 0.17.0 được tải từ release chính thức, đối chiếu SHA-256
do release công bố. Tool nằm ngoài môi trường khoa học/repo; thông tin trong
`tools/tex_toolchain.json`. IEEEtran v1.8b, lớp
`\documentclass[conference,a4paper]{IEEEtran}` được giữ.

Các sửa cần thiết cho môi trường build:

- Nạp `fontenc` T1 trước IEEEtran để XeTeX dùng đúng họ Times/Courier; không
  thay đổi danh sách package cũ ngoài bổ sung encoding này.
- Đặt tên bibliography `manuscript_refs.bib` để tránh Tectonic trên Windows
  mở nhầm thư mục `references/`. BibTeX kết thúc bình thường, đủ bốn mục.
- Dùng package `balance` đã có để cân hai cột cuối; giảm riêng cỡ chữ hai
  nhãn trạng thái nội bộ để tránh tràn cột.

Kiểm tra log cuối: không lỗi LaTeX/BibTeX, không undefined reference/citation,
không nhãn trùng, không overfull hbox/vbox, không thiếu hình và không còn font
substitution warning. Còn **hai Underfull vbox** do dàn float hai cột và một
cảnh báo UTF-8 của `algorithm.sty` dòng 11. Dòng này là comment bản quyền chứa
byte Latin-1 trong tên Rogério; đã đọc trực tiếp từ bundle, không phải nội dung
thuật toán in ra. Các cảnh báo này được giữ nguyên trong log, không gọi là
warning-free. Không có phương trình bị tràn hoặc ký hiệu bị thiếu khi xem PDF.

Đã render và xem trực tiếp cả sáu trang ở 150 dpi bằng PDFium, gồm trang tiêu
đề, phương trình/thuật toán, bảng tham số, bốn hình, kết luận và bibliography.
`validation/pdf_inspection.json` ràng buộc hash PDF và từng ảnh trang;
`validation/visual_review.json` ghi nhận đánh giá thực tế. Hình dùng toàn bề ngang
hai cột để giữ chữ trục/caption đọc được, không cắt, không rasterize PDF vector.
Hai cột cuối đã cân; không áp đặt page limit chưa được tác giả cung cấp.

## Đối chiếu bốn hình và số liệu

Tất cả số dưới đây được tính lại từ **giá trị đã lưu**, không tạo quan sát,
nguồn, kênh hay quỹ đạo mới. Gói final được kiểm tra hash trực tiếp cùng receipt
base/Stage A/Stage B; không chạy lại các verifier cũ có thể gọi optimizer.

| Hình | Dữ liệu đối chiếu | Kết quả kiểm tra |
|---|---|---|
| 1, candidate positions | DP mean `U`, J=10 và 100 | `1.390037025169202e-4 → 1.5486275251456137e-4` bit/use; tăng `11.409084585866157%` so với J=10. |
| 2, cloud blockage | Unavailability tại p=0.8, P2/Greedy/DP | `24.60% / 16.53333333333333% / 4.066666666666666%`; đây là tỷ lệ `S=0`, không phải cải thiện objective. |
| 3, temporal correlation | DP mean distance, rho=0 và 0.98 | `1038.25040431866 → 31.843766846610823` m; xu hướng quan sát, không gán định lý đơn điệu theo rho. |
| 4, tradeoff | DP, lambda=0 so với lambda_ref trên cùng 100 nhiệm vụ mặc định | Distance `1482.6878339732662 → 172.4329897790698` m, giảm `88.37024316055872%`; mean K `1.5730511911456893e-4 → 1.5649535266182735e-4`, giảm `0.514774380706462%`. Mẫu số lần lượt là distance và K tại lambda=0. |

Các PDF tích hợp:

- `figures/fig1_candidate_positions.pdf` — trang 4.
- `figures/fig2_cloud_blockage.pdf` — trang 4.
- `figures/fig3_temporal_correlation.pdf` — trang 5.
- `figures/fig4_skr_mobility_tradeoff.pdf` — trang 6.

Hash cả bốn bản sao khớp bản final; không tái vẽ, nội suy hay sửa số liệu.
Các label/ref và số hình 1–4 khớp nội dung/caption. Giữ chỉ số lambda theo thứ
tự thật, các điểm trùng/zero, khoảng tin cậy pointwise và 100 paired missions.

Verifier mới đối chiếu 8.700 bản ghi nhiệm vụ và 696 hàng thống kê: mean, sample
SD, median; dựng lại U từ K/D/lambda; kiểm tra số mission ID, availability,
hash nguồn và dữ liệu vẽ. Kiểm tra dominance dùng **U đã lưu**, không chạy
Bellman: DP ≥ P2/Greedy trong dung sai tuyệt đối `1e-12`. Không áp đặt dominance
cho SKR hoặc availability. CI được bảo toàn bằng hash và giá trị đã lưu;
**không** tạo bootstrap draw hoặc tính lại CI. Các kiểm tra độc lập đường đi,
mask, covariance và convergence của lần chạy trước vẫn là bằng chứng lịch sử
đã xác thực hash, không được tính là test khoa học chạy mới trong nhiệm vụ này.

233 payload nguồn được đọc và kiểm tra family/count, hash, `C,w`, hex VA/nu,
support 256 và cache identity. Hash implementation chấp nhận đúng chính sách
LF/CRLF đã có trong `exact_cache_provenance.py`, không chuẩn hóa code hay thay
payload. Không gọi lại hàm sinh nguồn hoặc tính C,w. Cả 100 P1 winners giữ
MB `(0.125,8)`. Không suy ra continuous global optimum hay shaping gain độc lập.

## Kết luận kiểm toán bảo mật

**Mô hình hiện tại không nhất quán về phép đo Bob:** MI dùng cả I/Q, mean
`2 sqrt(eta_f) alpha`, variance `1+N` mỗi thành phần; Holevo dùng điều kiện
homodyne một quadrature. Một phép đo heterodyne nhất quán cần tính cả vacuum
do đo đồng thời và điều kiện Holevo tương ứng; homodyne cần MI một quadrature
với quy tắc basis/sifting rõ ràng. Không tự chọn phương án hoặc sửa số liệu.

Các điểm chưa được chứng minh: endpoint Z-minus là worst case; Gaussian
likelihood thay thế fading mixture cho nguồn rời rạc; tham số ước lượng,
conditioning của AoA/cloud outage và key aggregation. `VA=2 nbar`, identity
nguồn và bookkeeping noise/covariance phù hợp trong phạm vi đã nêu; điều này
không cứu được mâu thuẫn MI–Holevo. Detector không lý tưởng chưa được xác thực
vì các kết quả hiện tại dùng efficiency=1, electronics=0.

Phần đề xuất trong audit tách riêng homodyne và heterodyne, **chưa áp dụng**.
Các kết quả vẫn được giữ như conditional manuscript-style numerical outputs.

## Vấn đề cần tác giả giải quyết trước công bố

1. Chọn phép đo vật lý và phê duyệt một mô hình MI/Holevo/noise nhất quán.
2. Phê duyệt/kiểm chứng miền tương quan và các giả định fading/outage/estimation;
   nếu cần kết quả mới, cấp phép riêng cho implementation và thí nghiệm mới.
3. Giải quyết chênh lệch hash frozen đang tồn tại, không ghi đè lịch sử:
   actual `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
   khác historical expected `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
4. Cung cấp/xác nhận `.tex` mới nhất, hoàn thiện tác giả `TBD`, đơn vị `XXX`,
   venue và page limit. Bản hiện tại bảo toàn thông tin đã có.
5. Giữ rõ các giới hạn catalog/grid hữu hạn, mây/hình học tổng hợp, full-horizon
   oracle, thiếu reacquisition/flight interruptions và chi phí năng lượng thật.

Không sửa scientific source, quantum/security functional, source cache, frozen
specification hoặc cấu hình sản xuất. Không training, final-test/held-out access,
baseline/threshold approval, nâng lifecycle, restart Objective C, sửa bản thảo
ngoài repo, commit hay push. Objective C vẫn `USER_STOPPED`.

Kiểm tra lại bằng `validation/verify_revision.py` của **thư mục revision**;
script chỉ đọc kết quả và artifact build. Receipt cuối chứa số kiểm tra hiện
tại và hash đầu ra; không dùng số test cũ để khẳng định PASS mới về bảo mật.
