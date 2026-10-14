# Tiếp tục AO từ checkpoint — tăng thời gian tính C,w

**Trạng thái: AO_RESOURCE_LIMITED.** Báo cáo kết thúc lần tiếp tục.

Chỉ L=21.9393102292km; effective_channel_no_fading_noise và objective effective_gaussian_Zstar_diagnostic_SKR. Không chạy lại tám multistart; khôi phục 211 objective exact và các lịch sử đã hoàn tất.

## A. Tính source exact cho ba probe timeout cũ

Tọa độ lấy nguyên từ source_attempts/checkpoint cũ. Đã kiểm tra toàn bộ cache hiện có: không có source hoàn chỉnh của ba điểm trước khi bắt đầu. Lần cũ không lưu intermediate numerical state; lần này bắt đầu mới và journal các precision row đã hoàn tất.

| nu_raw | VA | runtime_seconds | status | C | w | I_AB | chi_BE | SKR |
|---|---|---|---|---|---|---|---|---|
| 0.17000000000000001 | 4.75 | 3510.8589999999967 | COMPLETED_EXACT | 2.8311876840870931 | 4.7215352203420358e-07 | 0.46635521451801232 | 0.38436025832091403 | 0.058677195471197652 |
| 0.17000000000000001 | 5.25 | 3743.0630000000237 | COMPLETED_EXACT | 3.08474029904345 | 7.8992041902476778e-07 | 0.50770285021345707 | 0.42360607322488297 | 0.058711634477901231 |
| 0 | 0.90000000000000002 | 4157.1410000000033 | COMPLETED_EXACT | 0.80231516160608296 | 0.017029525425882673 | 0.10071471988347636 | 0.091227933413186246 | 0.0044510504761162833 |

Toàn lượt: 16 source mới hoàn thành; 1 job chưa hoàn thành. Tổng objective đã lưu: 227.
Job 17 tại (nu,VA)=(0.17125,5.046875) dừng do giới hạn ngân sách toàn lượt, gồm thời gian dự phòng kết thúc: deadline=1616.515000s, thực chạy=1611.515000s, shutdown margin=5s. Các hàng precision được giữ: [1050, 1250]; chưa chấp nhận C,w hoặc tính SKR từ các hàng chưa đủ ladder.

TIMEOUT/gián đoạn là trạng thái tài nguyên, không phải K âm/0 hoặc constellation không physical.
7200s tối đa mỗi candidate (Windows Job có shutdown margin5s); watchdog AP bên trong cũng tăng từ3600s lên7200s chỉ tại wrapper này. Budget continuation43200s, reserve60s, source jobs tuần tự1. Không giảm1050/1250/1450digits hoặc thay acceptance rule.

## B. Nhật ký P1/P2

P1 giữ nu hiện tại; P2 dùng ngay VA sauP1. Chỉ thêm targeted exact neighbors/bracket midpoints, không rectangular sweep/interpolation. Tất cả accepted updates không giảm evaluatedK.

| iteration | nu_before | VA_before | VA_after_P1 | K_after_P1 | nu_after_P2 | K_after_P2 | delta_K | parameter_change |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.17000000000000001 | 5 | 5.046875 | 0.058734859879005397 | 0.17000000000000001 | 0.058734859879005397 | 1.6878114554863544e-06 | 0.046875 |

## C. Best exact đã xác thực

**(nu_raw,VA,K)=(0.17000000000000001,5.046875,0.058734859879005397)**.
Giữ previous best cho đến khi có exact result hợp lệ tốt hơn. Digits là binary64 output, không phải chứng nhận total error17digits.

| quantity | value |
|---|---|
| C | 2.9818069279923307 |
| w | 6.1909456504525073e-07 |
| T_eff | 0.16092029098192165 |
| xi_eff | 0.018599999999999998 |
| a | 6.046875 |
| b | 1.8151377109616496 |
| Z_star | 2.3922351535921544 |
| lambda_1 | 5.2351669529129943 |
| lambda_2 | 1.003429663874646 |
| lambda_3 | 4.014012093223343 |
| I_AB | 0.49104803313043011 |
| beta_I_AB | 0.4664956314739086 |
| chi_BE | 0.4077607715949032 |
| SKR | 0.058734859879005397 |

Source cache key=2f882cd70090cf960b9df07d66291c049da8546c0c06a517e0714fdfb6bc308f; ensemble hash=b2dde0f1bdf8c14fefedc304926b6524b79e0628d577af2b387a55e975f9205b; source=results/ao_effective_channel_no_fading_noise_reference_continuation/exact_source_cache/2f882cd70090cf960b9df07d66291c049da8546c0c06a517e0714fdfb6bc308f.json.
Inherited scientific context=77abb3f0ff944accb850da5f6e8ad68b4fec69dd702bd11b5b897681e6c7193c; continuation context=4fb404abbb81b41cadd49473d5bdfbc39e2da8dca061822b86817171ee6b2d0f.

| order | I_AB | SKR |
|---|---|---|
| 8 | 0.49104803310232192 | 0.05873485985230259 |
| 16 | 0.49104803313042966 | 0.058734859879004953 |
| 32 | 0.49104803313043011 | 0.058734859879005397 |

## D. So sánh với kết quả trước

K_previous exact stored=0.05873317206754991 (yêu cầu làm tròn0.05873317206755).
DeltaK=1.6878114554863544e-06 bits/use; relative gain=0.0028736936829244926%.

## E. Hội tụ và bracket

Ngưỡng improvement1e-8, parameter stability1e-6. Không kết luận convergence chỉ vì deltaK nhỏ. Hai local brackets, exact neighbors, boundaries, GH8/16/32 và covariance physicality phải cùng được kiểm tra.
P1: status=INNER_SEARCH_FAILURE, actual range=[2.0, 6.5], bracket=[5.03125, 5.0625], refinement=REFINEMENT_LIMIT_REACHED, boundary=INTERIOR.
P2: status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING, actual range=[0.1675, 0.175], bracket=[0.169375, 0.1725], refinement=SOURCE_MISSING_REFINEMENT, boundary=INTERIOR.
Coordinate brackets complete=False.
P2 còn thiếu exact source tại: [0.17125, 0.0]; VA cố định sau P1=5.046875.
P1 đạt giới hạn bốn lượt refinement; nhãn legacy INNER_SEARCH_FAILURE ở đây không có numerical_failures. P2 chưa hoàn tất refinement/boundary checks. Chưa hội tụ theo tọa độ hoặc trên miền liên tục.

## F. Bảo toàn và provenance

3275 prior files được hash-bound trong startup_manifest; toàn bộ old cache/catalog182/B/C/modes/previousAO results được giữ nguyên.
Transport/deadline/checkpoint wrapper import original AP _row,worker.main,Gram moments,source normalization,discrete MI/Holevo. Completed precision rows hash-bind exact binary64 request,mathproducer,mpmath version,ambient precision,digits và rowdigest. Hash mismatch fail closed.
Source full-support accepted mới lưu vào cache riêng ngay khi hoàn tất; auxiliary fast-gate Infinity được encode losslessly, không biến đổi C,w. Interrupted job có thể tiếp tục precision rows hoàn tất; không reset cumulative candidate7200s hoặc continuation budget.
Elapsed continuation=43136.579000s; restarted multistarts=0.
T_eff=.16092029098192165,xi_ch=.0186,beta=.95,ideal heterodyne/phase/adaptiveopticsOFF giữ nguyên. b=1+T_eff(VA+xi),Z*=2sqrt(T_eff)C-sqrt(2T_eff xi w);K=.95I_AB-chi(Zstar). Eq10/20/PDF/moments/source normalization không sửa.
Đây là Gaussian approximation bỏ fading-induced variance, không phải certified fading security lower bound. Total source/security error enclosure vẫn chưa được thiết lập; numeric agreement không chứng nhận continuous/global optimum.
Frozen actual SHA256=df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15; historicalexpected=561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1;pre-existing promotion blocker giữ nguyên. NOT_READY_FOR_PUBLICATION_SCALE_RUNS;oldObjectiveC USER_STOPPED.
Không newmultistarts/distance/trajectory/heldout/final-test/training/publication evaluation/commit/push.

Artifacts: [checkpoint](../results/ao_effective_channel_no_fading_noise_reference_continuation/checkpoint.json), [source results](../results/ao_effective_channel_no_fading_noise_reference_continuation/exact_source_results.csv), [iterations](../results/ao_effective_channel_no_fading_noise_reference_continuation/continuation_iterations.csv).

## G. Kiểm tra kết thúc

CURRENTLY_VERIFIED_PASS: 0 protected changes trên 3275 file; provenance của toàn bộ cache và journal precision mới khớp.
GH8/16/32 chọn cùng winner trong top10=True; covariance độc lập Gamma+iOmega và domain symplectic pass, repairs=[]; P2 dùng đúng VA mới sau P1.
6 scoped tests đã chạy PASS ở preflight; hash của test/config/controller vẫn khớp bản đã kiểm tra, không chạy lại AP hay AO để lập báo cáo.
Đã dừng toàn lượt theo ngân sách; full source mới được giữ trong namespace riêng. Source timeout không được gán SKR âm/0 hoặc coi là numerically invalid.
