# Báo cáo kiểm chứng triển khai

Ngày 2026-11-07. Trạng thái: **CURRENTLY_VERIFIED_PASS** cho phạm vi phần mềm
và demo tổng hợp được mô tả dưới đây.

## Sản phẩm

Gói độc lập `uav_cvqkd_optimization/` triển khai đúng bốn phương pháp:
Stationary, SKR-Greedy, Energy-Aware Greedy và Pareto DP. Hai mục tiêu P1/P2
dùng chung công suất động cơ, năng lượng convex envelope, Gaussian CLWC dịch
liên tục, giao LOS với tầng mây, SKR lookup và finite-size terminal evaluator.
Không có PPO/SAC/MPC. Cấu hình demo và cấu hình paper thiếu đầu vào được tách rõ.

Kết quả bàn giao chính: `../results/final_demo_20261107/`.
Trong đó `results.json`, `summary.csv`, `trajectories.csv`, `scenario.npz`,
`skr_input.csv`, `lambda_calibration.csv`, `approximation_gaps.csv` và
`sensitivities.csv` lưu dữ liệu tính thực tế. `figures/` có 16 cặp PNG300dpi/PDF.
Mọi bảng và hình tổng hợp ghi `SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS`.

## Bằng chứng đã thực thi

- `python -m pytest -q --junitxml=results/tests_20261107.xml`: **34 passed**.
- Tiny-graph DP khớp vét cạn cho P1/P2, có/không dominance pruning, và năm seed
  ngẫu nhiên. Có test hai mục tiêu chọn K khác nhau. Các kiểm thử so sánh nghiệm
  có tolerance số được ghi trong mã; dominance không dùng epsilon dominance.
- Kiểm thử công suất hữu hạn/dương, hover, dịch chuyển không khả thi, convexity,
  speed mixing, tăng mật độ lưới vận tốc và giới hạn năng lượng/quãng đường.
- Mây dịch 5 m/s tại t=0,1,300,1000; giao LOS qua slab, không dùng endpoint;
  so sánh bước lấy mẫu LOS 2 m và 1 m trên demo cho cùng availability.
- Penalty chỉ áp dụng một lần trên block tích lũy; zero signals, scaling sqrt(n),
  epsilon rất nhỏ, zero/complete blockage và tái lập deterministic đều có test.
- `python -m uav_qkd.verify --output results/final_demo_20261107`:
  80 kiểm tra metric quỹ đạo, 41 hash output, 15 hash producer, 1 hash config,
  cùng nhãn CSV: **CURRENTLY_VERIFIED_PASS**. Receipt: `verification.json`.
- Demo chính chạy end-to-end, đủ bốn phương pháp và tám kết quả objective.
- Approximate smoke: `../results/approximate_smoke_20261107/`; không chạy
  uncapped exact DP. So sánh gap thực hiện trong demo exact nhỏ và trong tests.
- Paper CLI trả exit code 2 đúng dự kiến khi thiếu đầu vào khoa học; receipt:
  `../results/paper_fail_closed_20261107.json`. Không có fallback dữ liệu giả.
- Rà soát độc lập phát hiện năm lỗi/case biên; tất cả đã có regression test và
  sửa. Báo cáo gốc và disposition nằm trong independent_review.md,
  review_resolution.md. Không lấy số test cũ của reviewer làm số test hiện tại.
- Kiểm tra trực quan contact sheet của 16 figure; 15 PNG khoa học ở lần chạy
  cuối giống byte với bản đã xem, hình runtime/memory thay đổi theo đo thực tế
  và đã xem riêng. Mọi PDF có nhãn tổng hợp trong text layer. Runtime/RSS không
  được kỳ vọng tái lập bit-for-bit, còn quỹ đạo/giá trị mục tiêu là deterministic.

## Kết quả demo và phạm vi

Đồ thị demo chỉ có 9 waypoint trong vùng con được khai báo, không đại diện
cho toàn bộ bài toán vị trí liên tục. Horizon năng lượng là 8 slot; prediction
cap cấu hình 12 slot không được ép làm K. Lambda=0 được chọn từ một realization
calibration tổng hợp riêng theo tiêu chí P2; không chọn từ realization đánh giá.
Trong demo này, DP và hai greedy cho cùng nghiệm giá trị tốt nhất; không có
khẳng định gain tổng quát. Label cap=1 bỏ 10 nhãn nhưng gap ở cả hai mục tiêu
bằng 0 trên trường hợp demo này; điều đó không bảo đảm gap=0 ở trường hợp khác.

Exact-on-graph chỉ nói về đồ thị, edge energy xấp xỉ số, availability được lấy
mẫu và horizon đã cho. Convex-envelope refinement không phải bound chứng nhận
uniform. LOS lấy mẫu có thể bỏ sót vùng hẹp. Các kênh khác trạng thái được gộp
bằng công thức performance approximation, chưa chứng minh composable security.
DP có thông tin tương lai; mọi phương pháp đều chọn best prefix hồi cứu.

## Đầu vào thật còn thiếu và bước tiếp theo

Chưa chạy thí nghiệm paper: **NOT_RUN**. Cần tác giả cung cấp/thông qua bộ tham
số rotor, vmax, Emax, q0, geometry, m0, epsilon, cloud realization và Lth, độ cao/
độ dày tầng mây, độ phân giải LOS, SKR lookup có provenance và lambda prior.
Repo có lookup receiver30 dạng diagnostic, nhưng gói này không tự nhập hay nâng
trạng thái khoa học của dữ liệu đó. Xem model_audit.md và data/README.md.

Hash nguồn PDF, task và frozen spec được lưu trong source_inputs_manifest.json.
Frozen spec hiện khác hash lịch sử trong AGENTS; không khôi phục hay sửa file.
Không thay đổi scientific production source, security functional, frozen model,
training/test access, production baseline selection, threshold approval hoặc
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Không commit/push/merge. Bộ kiểm thử toàn
repo cũ không được chạy; chỉ suite của gói mới và kiểm tra output có phạm vi.
