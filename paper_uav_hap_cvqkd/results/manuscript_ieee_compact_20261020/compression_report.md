# Báo cáo rút gọn phần Optimization đến Conclusion

**Hoàn tất bản rút gọn để phản biện nội bộ.** Nguồn đầu vào là
`results/manuscript_ieee_revision_20261020/main.tex`. Bản đầu vào không bị ghi đè.
Kết quả mới nằm riêng trong `results/manuscript_ieee_compact_20261020/`.

## Dung lượng đo trực tiếp trên PDF

Phần cần rút gọn, **kể cả toàn bộ hình ba panel và caption**, chiếm
**1,484223823 trang IEEE tương đương 2,968447646 cột**. Mức này gần 1,5 trang
và không vượt ba cột. Toàn bộ PDF gồm **3 trang A4**, bao gồm cả phần đầu giữ
nguyên và bibliography sau Conclusion; không gọi toàn bộ PDF là 1,5 trang.

| Mốc trên PDF cuối | Trang/cột | Tọa độ từ mép trên trang |
|---|---|---|
| Bắt đầu II. Optimization Problem | Trang 2, cột trái | 52,00635 PDF pt ≈ 18,35 mm |
| V. Conclusion | Trang 3, cột trái | 366,66141 PDF pt ≈ 129,35 mm |
| Kết thúc dòng cuối Conclusion | Trang 3, cột trái | 510,20309 PDF pt ≈ 179,99 mm |
| Hình ba panel | Đầu trang 3, trải hai cột | Khung vector 50,37170–211,91974 PDF pt; caption kết thúc tại 240,54041 pt |

Phương pháp đo không dùng số từ để suy ra số trang:

1. Đọc vị trí glyph của heading Optimization và câu cuối Conclusion trực tiếp
   từ PDF bằng PDFium. Đọc khung vector figure và vị trí caption trên PDF.
2. Lấy kích thước dàn trang thật từ log TeX: `textheight=672 pt`,
   `columnwidth=252 pt`, `textwidth=516 pt`, với 72,27 TeX pt/inch.
   Mỗi cột cao **669,489414695 PDF pt** và rộng **251,058530511 PDF pt**
   (72 PDF pt/inch). Vùng thân trang bắt đầu tại **46,785683686 PDF pt**.
3. Tính hợp các dải diện tích theo từng cột, không đếm lặp phần figure đã nằm
   trong reading flow. Figure trải hai cột nên phải tính cả phần nằm ở cột phải
   trang 3, dù Conclusion kết thúc ở cột trái.

| Dải được tính | Chiều cao phân bổ, PDF pt |
|---|---:|
| Trang 2, cột trái: Optimization đến hết cột | 664,268750725 |
| Trang 2, cột phải | 669,489414695 |
| Trang 3, cột trái: figure, caption, nội dung đến hết Conclusion | 463,417410796 |
| Trang 3, cột phải: phần còn lại của figure và caption | 190,168701172 |

Chia tổng chiều cao các dải cho hai lần chiều cao một cột được
**1,484223823 trang**. Nếu chỉ đo tuyến đọc từ heading đến chữ cuối mà bỏ phần
figure ở cột phải thì được **1,342198649 trang**, một cách đếm thiếu. Báo cáo
và nghiệm thu sử dụng diện tích **đã tính đủ figure/caption**. Khoảng trắng
chuẩn bên trong dòng văn bản, công thức và khung figure được giữ như dàn trang
thật; không nén bằng khoảng cách âm. Bibliography đặt **sau** Conclusion nên
nằm ngoài biên đo; các citation xuất hiện trong phần rút gọn đã nằm trong biên.

Tệp kiểm chứng: `validation/layout_measurement.json` và
`validation/measure_layout.py`. Tọa độ được ràng buộc với SHA-256 PDF cuối.

## Những phần giữ nguyên

- Document class IEEEtran conference A4, lề trang, độ rộng/cao cột và font
  thân bài 10 pt không đổi. Không thêm negative spacing, resizebox hoặc thu
  nhỏ công thức để đạt dung lượng.
- Preamble, title, tác giả/đơn vị, abstract, keywords và hai nhãn trạng thái
  nội bộ giữ nguyên từ bản đầu vào.
- Đoạn hình học/mây mở đầu, công thức raw SKR và phần diễn giải liên quan,
  **toàn bộ** phần Recorded Physical-Layer Model and Security Boundary được
  giữ nguyên văn. Không sửa MI, Holevo, fading, source normalization hoặc noise.
- File `.bib` và bibliography đã biên dịch `.bbl` khớp SHA-256 bản đầu vào;
  giữ đủ bốn tài liệu tham khảo, không thêm nguồn mới.

Bản đầu vào đặt P1–P2–P3 dưới phần System and Problem Formulation. Chỉ các đoạn
**bài toán tối ưu** đó được chuyển sang mục II riêng và rút gọn. Phần mô hình
vật lý/SKR không bị cắt. Đây là thay đổi vị trí nội dung đúng phạm vi yêu cầu,
không phải rút ngắn phần mô hình để che dung lượng Optimization.

## Các phương trình và phương pháp còn lại

- **P1, Eq. (2):** cực đại raw SKR trên catalog exact hữu hạn rồi clipping.
  Giữ 197 MB + 36 Uniform, tối ưu ν và VA trong catalog, dùng đúng source
  moments của mỗi ensemble; không tuyên bố tối ưu liên tục.
- **P2, Eq. (3):** cực đại trung bình `S` trên toàn bộ nhiệm vụ tại một vị trí
  cố định; đây là benchmark offline, distance bằng zero.
- **P3, Eq. (4):** `mean(S) − lambda D/D_ref`, cùng chuẩn hóa như trước;
  giữ miền chỉ số hữu hạn, giới hạn tốc độ, staying, free initial position và
  không có yêu cầu điểm cuối/deployment/return. Distance vẫn là surrogate.
- **DP, Eqs. (5)–(6):** `F1(j)=S(j,1)` và recursion tích lũy với hệ số
  `Nt lambda`; giữ tập predecessor khả thi, backtracking và điều kiện offline.
  Giải thích tương đương với trạng thái lưu `F/Nt` của code, time `O(Nt J²)`
  và bộ nhớ. Không chạy lại recursion.
- **Greedy:** giữ khởi tạo argmax slot đầu và score hiện tại
  `S − Nt lambda d/D_ref`; không đọc tương lai, dùng cùng ràng buộc và mây.
- Giữ các label chính `eq:raw`, `eq:p1`, `eq:p2`, `eq:p3`, `eq:dp_init`,
  `eq:dp`. Các phương trình phụ/backpointer lặp lại và pseudocode dài được
  thay bằng diễn giải; không còn reference trỏ tới label đã bỏ.

Kết quả số được gom thành đúng **ba đoạn văn**, Conclusion **76 từ**. Các
phần trăm chỉ xuất hiện một lần trong phần kết quả; abstract cũ được giữ
nguyên theo yêu cầu không sửa phần đầu.

## Hình giữ và hình không đưa vào bản rút gọn

Hình duy nhất: `figures/compact_sensitivity.pdf`, vector, kích thước gốc
7,16 × 2,25 inch, ba panel dùng **57 điểm** đã lưu:

| Panel | Nguồn dữ liệu final | Nội dung |
|---|---|---|
| (a) | `fig1_candidate_positions_data.csv`, metric U | Objective theo J; P2, Greedy, DP |
| (b) | `fig2_cloud_blockage_data.csv`, metric unavailability_percent | Unavailability theo p; P2, Greedy, DP |
| (c) | `fig3_temporal_correlation_data.csv`, metric D | Distance theo rho; P2, Greedy, DP |

Marker circle/diamond/triangle, màu và nét đặc/đứt phân biệt ba phương pháp.
Giữ nguyên điểm và CI, không smoothing hay sinh điểm nội suy. Font label/tick
gốc tối thiểu 8,5 pt; sau scale thực trong PDF tối thiểu **8,4763 PDF pt**.
Hình rộng hai cột để cả ba panel đọc được; tick rho cuối xoay dọc để không
chồng nhau. Figure và caption nằm ở đầu trang 3, ngay phần Numerical Results
đang tiếp tục; phần diện tích cột phải đã được tính đầy đủ ở trên.

Không chèn bốn figure cũ dưới dạng riêng: Fig. 1 gộp vào (a); Fig. 2 chỉ giữ
panel unavailability; Fig. 3 chỉ giữ panel distance. Các panel SKR theo p,
objective theo rho và Fig. 4 tradeoff không chèn, nhưng vẫn giữ nguyên trong
`results/mobility_parameter_sensitivity_final_20261020/figures/`. Kết quả
tradeoff vẫn được tóm tắt bằng số trong văn bản. Không di chuyển/xóa hình gốc.

## Đối chiếu kết quả số từ CSV gốc

| Nhận định | Giá trị kiểm tra trực tiếp | Giá trị trong bản thảo |
|---|---|---|
| DP U gain, J 10→100 | 11,409084585866157% so với mean U tại J=10 | 11,409% |
| p=0,8, unavailability P2/G/DP | 24,60 / 16,53333333333333 / 4,066666666666666% | 24,60 / 16,53 / 4,07% |
| rho 0→0,98, DP distance | 1038,25040431866 → 31,843766846610823 m | 1038,25 → 31,84 m |
| rho 0→0,98, DP U gain/P2 | 23,712310904446344 → 0,15513663024910862% | 23,712 → 0,155% |
| DP lambda0→lambda_ref, distance reduction | 88,37024316055872% | 88,370% |
| Cùng so sánh, usable SKR reduction | 0,514774380706462% | 0,515% |

Các gain theo rho chia cho mean U của P2 ở **cấu hình rho tương ứng**.
Tradeoff dùng cùng 100 nhiệm vụ mặc định; mẫu số giảm distance và giảm K lần
lượt là mean distance và mean K của **DP tại lambda=0**. Giữ lambda_ref tuyệt
đối `9.468026677248516e-6`, không đổi theo cấu hình.

Nguồn authoritative: `tables/statistical_comparison.csv` và
`tables/selected_missions.csv` trong gói final. Verifier đối chiếu mean từ
các bản ghi nhiệm vụ đã lưu, đủ 100 paired IDs, từng row vẽ và CI với CSV gốc;
không chạy bootstrap, P1/P2/P3, MI/Holevo, channel, source C/w hoặc cloud.
Các receipt cũ được xác thực trực tiếp, không gọi verifier cũ có thể chạy solver.

## Build, xem PDF và giới hạn còn lại

Tectonic 0.17.0 đã có ở ngoài repo được kiểm tra identity cho lần build này.
`main.pdf` biên dịch thành công; không lỗi TeX/BibTeX, undefined reference,
overfull/underfull box hoặc font substitution. Còn cảnh báo encoding của
comment bản quyền `algorithm.sty` đã tồn tại từ trước, không in vào nội dung.
Không sửa package gốc để che cảnh báo này.

Đã render và xem cả ba trang PDF cuối tại 150 dpi, kiểm tra phương trình,
caption, marker, tick rho, bố cục hai cột và phần kết luận. Bằng chứng nằm ở
`validation/pdf_inspection.json`, `validation/visual_review.json`,
`validation/verification.json` và receipt cuối. Chỉ các scoped checks hiện tại
được ghi nhận; không dùng số test vật lý cũ làm PASS mới.

Giữ `UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` và
Objective C `USER_STOPPED`. MI 2D và Holevo homodyne vẫn không mô tả cùng một
phép đo Bob; kết quả là conditional manuscript-style outputs. Fading/outage,
correlation-domain security, finite-key estimation, synthetic clouds/grid,
offline information và mobility surrogate vẫn là giới hạn. Hash frozen thực
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
vẫn khác historical expected; không sửa hoặc nâng trạng thái.

Không thay đổi scientific source, evaluator, cache, cấu hình vật lý, frozen
spec, baseline/threshold approval hoặc lifecycle. Không truy cập final-test/
held-out, không commit/push. Các tệp gốc và thư mục tổng hợp 102 hình vẫn nguyên
byte. Đây là hoàn tất công việc biên tập/biên dịch, không xác nhận an toàn QKD.
