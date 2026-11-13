# Mô hình nhị phân nhận biết khả dụng QKD từ suy hao mây

Ngày 2026-11-12. **DIAGNOSTIC_ONLY; OFFICIAL_0P55M_THRESHOLD_PENDING**.
Hoàn tất chuyển đổi xác định trên 1.000 khung đã lưu. Chưa có kết quả khả dụng
QKD được hiệu chuẩn hoặc chứng nhận cho cấu hình 0,55 m.

## 1. Tệp đã đọc và tái sử dụng

Đọc báo cáo `results/ibrahim_continuous_attenuation_20261112/report_vi.md`,
`docs/IBRAHIM_CONTINUOUS_ATTENUATION_README.md`, source/test/plot conventions,
và src/ibrahim_stationary_cloud.py (nguồn sinh G gốc, không chạy lại).
Nguồn chính:

| Tệp | Khóa | Shape | Kiểu/đơn vị |
|---|---|---|---|
| results/ibrahim_stationary_cloud_20261111/cloud_fields.npz | X |1000x50x50|float64, không thứ nguyên |
| results/ibrahim_continuous_attenuation_20261112/cloud_clwc.npz |clwc_g_m3|1000x50x50|float64,g/m3,minh họa |
| cùng thư mục/cloud_attenuation_db.npz |attenuation_db|1000x50x50|float64,dB |
| cùng thư mục/cloud_transmittance.npz |transmittance|1000x50x50|float64,tỷ lệ công suất |

Hash đầy đủ ở input_hashes.json, cấu trúc mọi khóa ở metadata.json/input_npz_structures.
Source arrays cùng time_s=0..999s,dt1s,x_m=y_m=20,60,...,1980m.
Array giữ **[t,y,x]**, khác thứ tự ký hiệu toán b(t,x,y); không đảo trục ngầm.
Giữ seed20261111,gió(-5,0)m/s,chuẩn hóa,CLWC,A,T và thứ tự toàn bộ khung.
Không sinh lại Gaussian, không resample hoặc thêm chuyển động. Phép chia ngưỡng
không thêm wrap; giới hạn finite-Fourier-torus của nguồn vẫn giữ nguyên.
Chỉ chuyển đổi scenario reference có đủ 1.000 mảng đã lưu; sáu sensitivity scenarios
cũ giữ nguyên, không phát sinh field mới cho chúng.

## 2. Đã ưu tiên kiểm tra cấu hình 0,55 m

`configs/redesigned_baseline_global_mb_va.yaml`: ACTIVE_FROZEN_AUTHOR_AUTHORIZED,
D_r=0,55 m, bán kính khẩu độ 0,275 m, w0=0,10 m, tau_zen=0,92,
beta=0,95, epsilon_total=0,0186; AO/phase OFF, direct-Z-minus,
ideal heterodyne theo security freeze tương ứng.
Nhãn config active/frozen không tự chứng minh một ngưỡng theo vị trí đã hội tụ.
Đường SKR raw hiện có: src/cvqkd/secret_key_rate.py::fading_secret_key_rate,
raw=beta*MI-Holevo, positive-part là trường riêng. Holevo dùng implementation
trong src/cvqkd/holevo.py; không sửa hoặc thay bằng công thức Gaussian-modulation.

Đã thực thi **native import probe** cho các module SKR/Holevo trên cấu hình đã
kiểm tra khẩu độ. Kết quả: **BLOCKED_BY_ENVIRONMENT**, returncode
1; traceback thực trong official_055_native_probe.log.
Windows Application Control chặn torch_python.dll/WinError4551.
Đây chỉ là import probe, **không phải đã chạy một phép tính SKR 0,55 m**.
SKR_evaluation_executed=false,threshold_search_executed=false,threshold_validated=false.
Không thay policy OS/DLL, không nạp giả Torch. Đồng thời còn frozen historical-hash
discrepancy và các điều kiện hội tụ/security chưa được đáp ứng độc lập.
Không chạy AP nguồn, tối ưu hoặc publication job để tự vượt các điều kiện này.

Nhánh 0,30 m Eq14 gần nhất dùng homodyne hiệu dụng,xi_det=.005 và C,w chưa được
chứng nhận; nghiên cứu trước có crossing khoảng.093-.099dB nhưng không là ngưỡng
0.55m. Nhánh đó và nhánh 0,55 m không được trộn. Đường catalog trước còn không đơn
điệu toàn dải; không chứng minh một ngưỡng chung toàn miền hoặc secure outage.

**Kết luận PhaseB:** Acrit 0,55 m chưa xác định; không có critical_attenuation_db
được validated để xuất. official_055_status.json giữ giá trị null và trạng thái
unresolved. Không dùng 0,1 dB làm fallback cho cấu hình chính thức.

## 3. Định nghĩa phân loại

Khi có đầu vào threshold dương hợp lệ và clear-sky feasibility đã xác minh:
`b=0` khi `A<threshold`, `b=1` khi `A>=threshold`; bằng ngưỡng là unavailable.
Mô-đun src/ibrahim_binary_qkd.py::classify_attenuation chỉ thực hiện logic cho
đầu vào đã cung cấp, không tự xác minh một mô hình QKD hoặc cấp chứng nhận.
Threshold có thể là scalar hoặc bản đồ[y,x]. Cần kiểm tra monotonicity/first
transition trước khi chuyển dấu Kraw thành quy tắc threshold; chưa xác minh cho 0,55 m.
Nếu Kraw clear<=0 thì clear_sky_state=0: unavailable ngay cả A=0, bất kể threshold.
Clear-sky chưa biết hoặc threshold NaN/Inf/nonpositive không được coi là available.
A đầu vào NaN/Inf/âm ở một khung tạo trạng thái chưa xác định ở khung đó.

| Trường | Mã và diễn giải |
|---|---|
| binary_blockage[t,y,x] uint8 |0available,1unavailable,255unresolved |
| qkd_available[t,y,x] bool |True chỉ khi b=0; False tại unknown, không tự khẳng định đã unavailable |
| resolved_mask[t,y,x] bool |Phân biệt kết quả biết được và unknown |
| clear_sky_available[y,x] uint8 |0known unavailable,1feasible theo scope,255unknown; dùng so sánh==1, không ép bool255 |
| classification_status[y,x] uint8 |0caller-supplied validated input,1clear-unavailable,2unresolved,3diagnostic assumed |

classification_status2D mô tả nguồn threshold; dynamic invalid A được thể hiện
trong resolved_mask và mã255 theo khung. Consumers phải giữ cả mask và scope.
Không gộp unknown thành available hoặc đo toàn bộ unknown như100%blockage.

Kịch bản thực thi duy nhất là **ILLUSTRATIVE scalar threshold A=0.1dB** được
người dùng cho phép rõ ràng. Giả định clear-sky feasible cho mọi cột tham chiếu,
không phải dữ liệu clear-sky 0,55 m đã tính. status=3 toàn bản đồ diagnostic.
Nhánh official-pending dùng status2,b255,resolved_maskfalse; qkd_availableFalse
chỉ mang nghĩa không khẳng định available. Không có official blockage ratio.

## 4. Hình học và transmittance vật lý

A cũ là bản đồ **cột lớp mây tham chiếu chiếu thẳng đứng**, không phải attenuation
đã ray-trace từ HAP tới từng UAV. Để giữ nguyên A, bản đồ diagnostic mới cũng
ở hệ tọa độ tham chiếu này. Các tọa độ trong hình/time-series là tọa độ lưới nguồn,
không được trình bày như link UAV đã xử lý giao tuyến thực tế.
Khi tích hợp thật cần độ cao/bề dày lớp, qc giao tia với lớp và hệ số slant hoặc
path integral phù hợp; không mặc định qc_xy=UAV_xy.

Giữ nguyên T_cloud=10^(-A/10). Cả 596,876
ô-khung diagnostic unavailable đều vẫn có T_cloud>0. unavailable không có nghĩa
quang học bị triệt tiêu hoàn toàn. Không ghi T=0 vì b=1.
API tùy chọn binary_effective_approximations cung cấp Tbinary=(b==0)*Tclear,
Rbinary=(b==0)*Rclear_usable, từ chối unknown. Đây là approximation riêng, không
là continuous-QKD rate. Không xuất Tbinary/Rbinary thực tế vì chưa có clear 0,55 m
maps được xác minh; không bịa Tclear hay Rclear để lấp chỗ thiếu.

## 5. Thống kê và mẫu số

Mỗi khung 2.500 ô, 1.000 khung: **2,500,000 quan sát ô-khung** cùng trọng số.
Không phải 2,5 triệu mẫu iid hoặc số vị trí UAV độc lập. Không gán confidence interval
binomial từ các ô/khung tương quan. Đây là một seed/mission được giữ nguyên.

| Đại lượng diagnostic 0,1 dB | Tử số / mẫu số | Kết quả |
|---|---|---:|
| Blockage theo toàn lưới và toàn thời gian |596,876/2,500,000|23.875040% |
| Available theo giả định diagnostic |1,903,124/2,500,000|76.124960% |
| Cloud-induced given assumed clear feasible |596,876/2,500,000|23.875040% |
| Unavailable trong các ô-khung cloud-affected(A>0) |596,876/601,800|99.181788% |
| Cloud-affected nhưng vẫn diagnostic available |4,924/601,800|0.818212% |

Cloud-affected định nghĩa A>0, không dùng softplus intensity>0 hoặc gọi mọi G>0
là mây. Tỷ lệ given-clear và unconditional trùng nhau vì giả định tất cả 2.500 cột
clear-feasible; không được suy ra hai tỷ lệ đó phải bằng nhau cho cấu hình thật.
Nếu có baseline unavailable, thuật toán loại chúng khỏi tử/mẫu cloud-induced.
Nếu population không xác định hoặc mẫu số 0, lưu null/CSVblank, không gán 0%.
Nếu một ô trong population clear-feasible chưa resolved, tỷ lệ conditional đầy
đủ cũng giữ null thay vì lặng lẽ bỏ nó khỏi mẫu số.

Khung đầu diagnostic blocked 29.8000%,khung cuối
18.9200%. frame_blockage_statistics.csv có 2.000 dòng:
1.000 diagnostic và 1.000 official-pending. Nhánh official có 2,5 triệu unknown ô-khung,
không có tỷ lệ unavailable/secure availability được xác minh.

Các thống kê continuous đối chiếu dữ liệu cũ: meanA=0.923228323046336dB,
maxA=15.5113807829903dB,Tmin=0.0281100696509578.
Không cắt loss, đổi CLWC, hay sửa phân phối để làm đẹp mask. Mapping L/N/H và
visibility trong nguồn continuous vẫn là giả định chưa hiệu chuẩn khí tượng.

## 6. Datasets và hình

- diagnostic_binary_blockage.npz: binary_blockage,clear_sky_available,
  classification_status,resolved_mask,tọa độ và scope.
- diagnostic_qkd_availability.npz: Boolean availability,masks,tọa độ,scope.
- diagnostic_threshold_0p1db.npz: threshold minh họa riêng, không gọi officialAcrit.
- official_pending_status.npz: unknown state/mask, không có critical threshold giả.
- statistics.json,frame_blockage_statistics.csv,metadata.json,configuration.json,
  official_055_status.json và native-probe log, input/protected/producer hashes.
- Hình A: G gốc/diagnostic/official unknown cùng 3 khung 0, 400, 999.
- B: A/threshold minh họa/mask ở 400 s. C: mask ở 100, 600, 999 s.
- D: ratios theo khung, official unknown riêng. E: histogram/CDF và threshold.
- F: b tại 3 tọa độ tham chiếu, official unknown riêng. G: GIF đủ 1.000 khung, y hướng lên,
  50 ms/khung chỉ là tốc độ xem 20x, dt vật lý vẫn 1 s.

PNG 400 dpi và PDF dùng native-vector cells/text/axes, không rasterize bản đồ.
PDF fonts/export metadata,ảnh render và visual QA lưu riêng. GIF dùng palette
cố định,không thay dữ liệu số. Danh mục đầy đủ nằm trong artifact_hashes.json.

## 7. Kiểm thử và provenance

18 kiểm thử mới + 49 kiểm thử hồi quy mô hình mây = 67 kiểm thử PASS trong tests.log.
Các test kiểm tra equality/nextafter,clear-unavailable,unknown/nonfinite,
axis không vuông,thời gian,1000khung,determinism,NPZroundtrip,conditional
denominators và optionalapproximation tách biệt. Xác minh artifact kiểm tra thêm
input1kG/A/L/T,checksums,thống kê,mask cả 2,5 triệu ô-khung,GIFpixelorientation và
hình khớp dữ liệu. 2,011 tệp cũ được bảo vệ bằng SHA-256.
Toàn repository suite **NOT_RUN**: nativeTorch import bị chặn, QKD-dependent
collection không thực thi được; không ghi 67 tests thành toàn suite.
git diff --check được chạy cuối phiên. Danh mục tệp mới/thay đổi và các thay đổi
có sẵn trước tác vụ được lưu trong git_change_inventory.json và git_status_final.txt.
Không sửa source QKD/SKR, bảo mật, finite-size,
trajectory,caches,Gaussian/continuous hoặc hình cũ. Không training/final-test/
heldout/publication run; không baseline/threshold/security approval.

Lần xuất đầu dừng trước binary export vì primary_scenario metadata là dict,
đã sửa reader và lưu producer/receipt/probe cũ trong preexport_failure/.
Không có Gaussian hoặc binary dataset cũ bị ghi đè; native-probe đã thực thi được
tái sử dụng sau sửa định dạng metadata, không giả vờ chạy lại 0,55 m.

## 8. Đánh giá cuối cùng

**Mô hình binary đã validated chưa?** Logic số và chuyển đổi dữ liệu có kiểm thử,
nhưng khả dụng secure-key generation cho 0,55 m **chưa validated**; official pending.

**Binary có defensible không?** Có thể là surrogate cho feasibility khi threshold,
clearbaseline,geometry và khoảng monotonic/firsttransition đã được xác minh.
Kịch bản 0,1 dB hiện chỉ có giá trị minh họa, không là bằng chứng bảo mật/vật lý.
Nó không mô tả extinction quang học hoặc chính xác thuật toán Ibrahim (2024).

**Tích hợp trajectory an toàn chưa?** Chưa được dùng làm official reward/outage.
Chỉ dùng sandbox diagnostic rõ scope; consumer phải kiểm tra classification_status
và resolved_mask, không cast unknown thành available hoặc physicalT0.

**Còn thiếu gì?** Khôi phục đường chạy 0,55 m, hội tụ nguồn/MI/Holevo và security
evidence tương ứng; clear-sky maps theo vị trí; first-transition/monotonicity,
cloud-layer geometry qc và pathloss thực; hiệu chuẩn CLWC/N/H và đánh giá sai số
surrogate đối với SKR liên tục. Frozen-hash discrepancy,E2INCONCLUSIVE,
strictPhaseBfalse,UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS
và ObjectiveC USER_STOPPED không được nâng trạng thái bởi tác vụ này.
