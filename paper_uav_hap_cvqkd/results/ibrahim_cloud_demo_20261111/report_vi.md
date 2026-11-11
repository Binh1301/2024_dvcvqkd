# Kết quả mô phỏng mây Gaussian động

Ngày 2026-11-11. Trạng thái: `CURRENTLY_VERIFIED_PASS` trong phạm vi
`SYNTHETIC_CLOUD_DIAGNOSTIC_ONLY`. Đây là một nhiệm vụ mây tổng hợp độc lập,
không phải chứng nhận khí tượng hoặc đánh giá QKD.

Đã đối chiếu Algorithm 1 ở trang PDF 10 và Table 2 ở trang PDF 9 của bài
Ibrahim et al. (2024). Module giữ phép cộng hai thang Gaussian, cập nhật
`G_next=(1-p)*G_adv+P*fine+P*coarse_interp`, mask ngưỡng trước blur và blur trên
trường liên tục. Tài liệu tham số và phân biệt thuật toán/lựa chọn số/kịch bản:
`../../docs/IBRAHIM_CLOUD_README.md`.

## Tham số đã chạy

| Tham số | Giá trị |
|---|---|
| Miền / grid / ô | 2000 x 2000 m / 50 x 50 / 40 x 40 m |
| Grid Gaussian coarse / u | 10 x 10 / 5 |
| Vận tốc / bước thời gian | vx=-5 m/s, vy=0 / 1 s |
| Thời lượng / seed | 1000 s, gồm 1001 khung / 20261111 |
| p / P | 0.002 / 0.05; lựa chọn minh họa, không phải số liệu của bài báo |
| Chọn ngưỡng | Quantile 0.70 của G0 cho độ phủ mục tiêu ban đầu 30% |
| Gamma cố định | 0.6308975316793873 |
| Blur Gaussian | sigma=1 ô; radius=4 ô; kernel chuẩn hóa tổng bằng 1 |
| Chuẩn hóa hiển thị | reference_minmax; khoảng BN tham chiếu [-2.053760466365046, 2.1508505103484716] |
| Thời điểm hình C/D | 0, 40, 80 s |

## Độ phủ đạt được

| Chỉ số | Kết quả |
|---|---:|
| t=0 s | 30.00% |
| t=40 s | 16.00% |
| t=80 s | 13.68% |
| Trung bình 1001 khung, gồm t=0 | 10.8842757243% |
| Nhỏ nhất / lớn nhất | 6.96% / 30.00% |
| t=1000 s | 7.60% |
| Độ lệch chuẩn theo thời gian | 2.8527962517 điểm phần trăm |

Ngưỡng không được tính lại theo slot. Độ phủ giảm khi trường Gaussian thay đổi
biên độ, chịu decay và khuếch tán số; không ép kết quả trở lại 30%. Đây là thống
kê mô tả của một mission có tương quan, không phải khoảng tin cậy độc lập.
CSV lưu đầy đủ raw mean/std, coverage và tỷ lệ clipping của intensity mỗi slot.

## Kiểm chứng chuyển động và kiểm thử

Mẫu xung thử riêng có p=P=0, cùng grid 40 m và dt=1 s:

- Dịch chuyển -0.125 pixel/slot, đúng chiều trái.
- Sau 1 s: trọng số 0.875 tại ô gốc và 0.125 tại ô trái, không làm tròn về 0.
- Trọng tâm sau 8 s dịch **-40.0 m**, đúng giá trị kỳ vọng **-40.0 m**.
- Kiểm thử kiểm tra riêng dấu trục y, dịch nguyên pixel, wrap qua biên và một
  phép dịch 400 s tương ứng một vòng miền.
- **10/10 kiểm thử PASS**; log thực tế nằm ở `unit_tests.log`.
- Hình PNG 400 dpi; năm PDF đã render bằng PDFium và kiểm tra trực quan.
  Cùng hệ tọa độ 0..2 km, cùng thang màu theo thời gian; mask đen=clear,
  trắng=cloud; các mũi tên hướng trái không đè tiêu đề.
- `verify.py` kiểm tra lại hash, mảng lưu, công thức mask/blur/normalization,
  chuỗi thời gian, thống kê, log tests và định dạng PNG; không chạy lại simulation.

## Tệp được tạo

- Module: `../../src/ibrahim_cloud.py`.
- Config: `../../configs/ibrahim_cloud_demo.json`.
- Script: `../../scripts/visualize_ibrahim_cloud.py`.
- Tests: `../../tests/test_ibrahim_cloud.py`.
- Figure A: `figure_A_multiscale.pdf` và `.png`.
- Figure B được tách thành `figure_B_intensity.pdf/.png` và `figure_B_mask.pdf/.png`
  để không dùng chung colorbar cho hai đại lượng khác nhau.
- Figure C: `figure_C_dynamic_intensity.pdf/.png`.
- Figure D: `figure_D_dynamic_masks.pdf/.png`.
- GIF: `cloud_masks.gif` (preview mask lấy mỗi 5 s, tốc độ phát minh họa).
- Dữ liệu: `cloud_snapshots.npz`, `coverage_timeseries.csv`.
- Cấu hình/provenance: `config_used.json`, `run_report.json`,
  `protected_input_hashes.json`, `artifact_hashes.json`, `validation.json`.

## Các giả định và giới hạn

1. PCG64, Gaussian chuẩn độc lập, nội suy bilinear tuần hoàn ở coarse-grid và
   advection tuyến tính bậc một là lựa chọn số được công khai.
2. Dòng 9 của bài báo dùng chỉ số cộng vận tốc theo pixel. Implementation dùng
   vận tốc vật lý và pullback `G(x-vx*dt,y-vy*dt)` theo yêu cầu người dùng;
   không thế trực tiếp -5 m/s vào biểu thức chỉ số của bài báo.
3. Nội suy nhiều bước gây khuếch tán số và kéo giãn cấu trúc theo phương chuyển
   động. Dịch trọng tâm đúng không có nghĩa hình dạng được bảo toàn hoàn toàn.
4. Miền tuần hoàn có chu kỳ hình học 400 s; cấu trúc đi qua trái sẽ trở lại
   từ phải. Trường không lặp y hệt vì có diffusion/decay/nhiễu mới.
5. Chuẩn hóa min-max tham chiếu cố định chỉ tác động intensity, có clipping
   được ghi nhận; không thay BN/raw/mask. Không có hiệu chuẩn độ dày hay CLWC.
6. Chưa triển khai miền mở/new-inflow. Không nối CLWC-attenuation, QKD outage,
   `R_k(q)=[1-b_k(q)]R_clear(q)` hoặc bất kỳ UAV optimization nào.

205 tệp đầu vào production/config/frozen đã theo dõi được hash trước/sau và
không đổi. Git ban đầu sạch, branch `feat/uav-power`, HEAD
`729a15c59eacffd8475de0f2afe310869b34a574`.
Frozen spec không bị sửa; chênh lệch hash lịch sử vẫn được giữ như blocker cũ.
Không thay mô hình kênh, security functional, SKR, finite-size, cache, baseline
hoặc threshold QKD; không training/final-test/held-out/publication-scale.
`UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` và
Objective C `USER_STOPPED` giữ nguyên.
