# Binary-cloud-aware joint UAV/source optimization

Kiểm tra và bàn giao ngày 2026-10-16; namespace 20261015 giữ theo kế hoạch đã duyệt. PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE.

Đã dùng 16 cấu hình × 100 mission độc lập, 30 slot × 20 s; tổng 1.600 mission và 7.600 lượt DP. Tái sử dụng 19.700 MB + 3.000 Uniform clear-sky evaluations, không dùng hàng cloud cũ. Smoke 30 clear evaluations khớp cache; không tạo C,w/AP/AO mới.

| Nguồn | Scheme | Mean SKR (bits/use) | SD | Availability | Mean flight (m) | Mean objective |
|---|---|---:|---:|---:|---:|---:|
| MB | S1 | 0.0341053753 | 0.014699 | 0.580667 | 0.000 | 0.0341053753 |
| MB | S2 | 0.0612416108 | 0.002633 | 0.992000 | 0.000 | 0.0612416108 |
| MB | S3 | 0.0631935656 | 0.000314 | 0.999667 | 1417.525 | 0.0631935656 |
| MB | S4 | 0.0631039218 | 0.000405 | 0.999667 | 216.482 | 0.0628874397 |
| Uniform | S1 | 0.0026630544 | 0.001148 | 0.580667 | 0.000 | 0.0026630544 |
| Uniform | S2 | 0.0051498017 | 0.000368 | 0.979000 | 0.000 | 0.0051498017 |
| Uniform | S3 | 0.0054320294 | 0.000048 | 0.999667 | 1417.525 | 0.0054320294 |
| Uniform | S4 | 0.0053514393 | 0.000184 | 0.995333 | 90.621 | 0.0052608185 |

S4 giữ 99.858144% SKR trung bình S3 và giảm 84.728161% quãng bay trung bình (tỷ số các mean, không phải mean của tỷ số từng mission).

Cloud tổng hợp: p=0.4, ell=250 m, rho=0.9; PCG64 SeedSequence([20261015, realization_id]). Covariance latent exp(-d/ell), khởi tạo dừng, threshold Phi^-1(p). Ell/rho không phải correlation Bernoulli. Không cloud radius, velocity hoặc phép chiếu độ cao mây. Gong et al. (2020), DOI 10.1109/LWC.2019.2958804, chỉ là bối cảnh network availability, không phải nguồn hiệu chuẩn kernel này.

P1 tối ưu đúng catalog theo vị trí một lần; P2 chọn mean cao nhất; P3 dùng DP sẵn có. S5 là Uniform ghép đủ bốn chính sách. K_min=0.001 bits/use chỉ dùng đánh giá, không điều khiển quỹ đạo. Vị trí đầu tự chọn; lambda=0.001 bits/use, D_ref=1000 m, tốc độ 15 m/s. Bỏ deployment, travel-time interruption, optical reacquisition và switching overhead. HAP 20 km/UAV 1 km, reference index44=(450,450)m giữ L_ref=21.9393102292km.

Dữ liệu đầy đủ: [summary.csv](../results/binary_cloud_skr_20261015/summary.csv), [mission statistics](../results/binary_cloud_skr_20261015/summary_statistics.csv), [paired differences](../results/binary_cloud_skr_20261015/paired_statistics.csv), [lambda statistics](../results/binary_cloud_skr_20261015/lambda_statistics.csv), [cloud matrices](../results/binary_cloud_skr_20261015/cloud_states.npz), [trajectories](../results/binary_cloud_skr_20261015/trajectories.npz), [clear sources](../results/binary_cloud_skr_20261015/clear_winners.csv), [source roster](../results/binary_cloud_skr_20261015/source_roster.csv), [cache reuse](../results/binary_cloud_skr_20261015/cache_reuse_audit.csv). CSV per-slot minh họa chỉ cho default realization0; mọi mission khác tái dựng từ NPZ. Realization0 được chọn trước, không chọn theo gain.

S2 chọn riêng vị trí cố định cho từng mission với toàn bộ lịch cloud biết trước; đây là stationary oracle hindsight, không phải một vị trí được freeze rồi kiểm tra trên mission tương lai. Với horizon30 slot và100 vị trí, selection theo lịch đã biết có thể cho availability rất cao.

Khoảng tin cậy t 95% và SD/SE lấy giữa mission độc lập, không lấy từng cell/slot như mẫu độc lập. Khoảng t không cắt tại0/1 nên cận có thể vượt miền availability; point estimate vẫn nằm trong[0,1]. Common innovations giúp so sánh ghép cặp giữa cấu hình; không gọi 1.600 mission độc lập giữa các cấu hình. Availability dùng >=K_min; nếu mọi clear rate đạt ngưỡng thì bằng tỷ lệ không blockage trên đường đi. Reference bằng0 có improvement phần trăm để trống, vẫn lưu delta tuyệt đối.

[Clear-sky spatial variation](../results/binary_cloud_skr_20261015/clear_sky_spatial_variation.csv) và [bản đồ](../results/binary_cloud_skr_20261015/figures/clear_sky_spatial_diagnostic.png) mô tả độ biến thiên nguồn/kênh trong vùng1km. [Fading omission audit](../results/binary_cloud_skr_20261015/fading_omission_audit.csv) tách (mean_eta-T_eff)VA và (mean_eta-T_eff)xi_ch bị bỏ. Đánh giá dùng ideal heterodyne, beta=.95, xi=.0186, phase/adaptive optics OFF, cùng ensemble cho MI/Holevo direct Z_star. Đây không phải lower bound bảo mật fading đã xác lập, finite-size yield, matched-energy PS gain, tối ưu liên tục hay năng lượng đẩy.

Bảy hình có 14 vector PDF/14 PNG 300dpi và plotting CSV. Figure3 là sum(S)/N_t, không phải tổng bit khóa. Figure4 chỉ nối tám penalty đã tính. Không còn hình cloud velocity. LaTeX lexical/path kiểm tra riêng; trạng thái compiler trong export_receipt.json, không mặc nhiên coi bố cục manuscript đã đạt.

Tests:23 primary tests (20 mới và3 normalization cũ) cộng3 regression tests cho verifier. Sửa verifier chỉ để nhận tie vài ULP giữa các cell đối xứng; không đổi source/kênh/DP hoặc kết quả thí nghiệm.

Provenance: startup_manifest.json, audit_receipt.json, correlation_audit.json, test_receipt.json, smoke_receipt.json, experiment_receipt.json, saved_data_validation.json, export_receipt.json và final_validation.json. LF/CRLF chỉ chấp nhận khi hash chứng minh cùng nội dung, payload/ensemble và historical objective key đều xác minh; không sửa artifacts cũ. Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS, frozen-hash discrepancy và ObjectiveC USER_STOPPED giữ nguyên. Không training/test dataset access, publication evaluation, commit hoặc push.

Chạy từ root dự án bằng .venv-binary-cloud/Scripts/python.exe -B; runner scripts/run_binary_cloud_skr_experiment.py có --stage audit/smoke/experiment/export và --output. Lượt hoàn tất từ chối ghi đè; resume chỉ cùng input/producer, checkpoint nguyên tử theo scenario. Bộ kiểm tra: scripts/verify_binary_cloud_skr_results.py --exports. Môi trường hiện dùng system-site packages với packaging lấy offline từ pip-vendored copy trong venv riêng; không sửa Python hệ thống.

## Trạng thái nghiệm thu hiện tại

CURRENTLY_VERIFIED_PASS cho triển khai và kiểm tra số/xuất bản artifact trong phạm vi diagnostic: 23 primary tests + 3 verifier regression tests, 30 smoke evaluations, 22.700 clear rows, 200 P1 maxima, 1.600 cloud seed replays, 7.600 Bellman checks và 1.684 plotting-data checks. 3.639 file cũ giữ nguyên hash. ZIP có 30 thành viên được so byte; 14 PNG chính và bản đồ clear-sky đã kiểm tra trực quan.

Hai lỗi kiểm tra/bố cục được giữ lịch sử: stationary tie lệch 2 ULP (gap 1.3877787807814457e-17 bits/use) và layout Fig1/Fig2/diagnostic title. Chỉ sửa verifier/export; không chạy lại hoặc đổi kết quả khoa học. Initial failure và các export snapshots vẫn có trong namespace mới.

LaTeX compilation: BLOCKED_BY_ENVIRONMENT vì không có pdflatex/tectonic; chỉ lexical/path và figure layout được xác minh. Chưa kiểm tra bố cục trang manuscript. Không sửa file Downloads, commit hoặc push.

Runner: [run_binary_cloud_skr_experiment.py](../scripts/run_binary_cloud_skr_experiment.py). Verifier: [verify_binary_cloud_skr_results.py](../scripts/verify_binary_cloud_skr_results.py). [ZIP Overleaf](../results/binary_cloud_skr_20261015/overleaf_binary_cloud.zip). [Final validation](../results/binary_cloud_skr_20261015/final_validation.json).

```powershell
& .venv-binary-cloud/Scripts/python.exe -B -m unittest tests.test_binary_cloud tests.test_binary_cloud_skr tests.test_binary_cloud_verification tests.test_normalization -v
& .venv-binary-cloud/Scripts/python.exe -B scripts/verify_binary_cloud_skr_results.py --exports
```

Các lệnh trên chạy từ paper_uav_hap_cvqkd. Không chạy lại audit/smoke/experiment/export vào namespace đã hoàn tất. Cache thiếu hoặc provenance không hợp lệ dừng fail-closed; lượt hiện tại có đủ coverage và không tính P1 bổ sung.
