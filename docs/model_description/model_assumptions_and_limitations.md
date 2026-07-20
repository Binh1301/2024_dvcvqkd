# Giả định, xấp xỉ và giới hạn

## Giả định mô hình

1. Nguồn có 256 symbol được sắp theo (i=16k+l). Không có ánh xạ bit, Gray labeling hoặc xác suất bit trong đường chính.
2. Biên độ coherent được đặt tâm và thỏa (2E_p|\alpha|^2=V_A) tại từng trạng thái kênh. Khi PS phụ thuộc (T), hình học vật lý sau chuẩn hóa cũng phụ thuộc (T), ngay cả nếu tọa độ thô cố định.
3. Bộ phát được giả định biết (T) và (\epsilon) đủ để tạo PMF theo trạng thái. Cơ chế ước lượng/feedback CSI, độ trễ và sai số CSI: **Chưa xác định từ mã nguồn hiện tại.**
4. Từng mẫu fading (T) được dùng như trạng thái tức thời trong (I_{AB}) và Holevo. Không có mã hóa theo block fading hoặc mô hình tương quan thời gian.
5. (\beta=0.95) là hằng số. Không có mô hình reconciliation phụ thuộc SNR trong đường PS–GS.

## Xấp xỉ số

- (I_{AB}) liệt kê chính xác 256 symbol nhưng tích phân AWGN bằng Monte Carlo antithetic; do đó còn sai số lấy mẫu.
- Các ứng viên trong log-sum-exp được xử lý theo chunk 64 để giới hạn bộ nhớ. Kiểm thử xác nhận chunking giữ kết quả trong sai số (10^{-12}).
- Trạng thái coherent bị cắt ở (n_{cut}). Huấn luyện đầy đủ dùng 64, xác thực và đánh giá cuối dùng 150; một phép kiểm tra cutoff 120/150 được cấu hình.
- Trị riêng (\tau\le10^{-12}) bị loại khi dựng căn bậc hai và giả nghịch đảo. Đây là regularization số có thể ảnh hưởng gradient gần thay đổi hạng.
- (Z) bị chặn trên bởi (\sqrt{ab}(1-10^{-9})) để giữ covariance trong miền số vật lý. `max`/`clamp` làm gradient từng đoạn.
- Khoảng tin cậy trong `evaluate_uncertainty` dùng hệ số chuẩn 1.96 dù số run mặc định chỉ 5; sweep riêng dùng Student-(t). Không nên xem hai thủ tục là đồng nhất.

## Giả định và giới hạn kênh

- Baseline là link thẳng đứng 20 km từ cao độ 0 m tới 20 km. Việc gọi nút thấp là UAV trong khi `H_UAV_m=0` là một quy ước baseline; kịch bản UAV ở cao độ bay thực tế chưa được cấu hình.
- Suy hao khí quyển dùng Kruse với visibility và bước sóng 1550 nm.
- Nhiễu xạ được biểu diễn qua bán kính chùm Gaussian; aperture và pointing được gói vào (T_0,\Gamma,R).
- Turbulence baseline chỉ đóng góp vào phương sai beam wandering. Không có scintillation log-normal/gamma-gamma độc lập trong đường này.
- Rayleigh chỉ là phân phối của độ lệch tâm (r), không phải PMF symbol hay fading Rayleigh vô tuyến.
- `T_samples` không nhân `eta_SMF*T_T*T_R`; pipeline chính dùng chính tensor này. Do đó hiệu suất ghép sợi và tổn hao quang cố định không ảnh hưởng kết quả hiện tại.
- Hiệu suất detector `QAM_ETA` và nhiễu điện tử `QAM_V_EL` được nhập nhưng không đi vào MI/Holevo hiện hành. File cấu hình sweep cũng ghi chú rõ điều này.
- AWGN được dùng trong mô hình cổ điển để tính MI với phương sai (1+T\epsilon/2). Đơn vị và phép hiệu chuẩn shot-noise thực nghiệm: **Chưa xác định từ mã nguồn hiện tại.**

## Giả định bảo mật

- Mã triển khai lower-bound kiểu covariance/Holevo qua (\tau,w,Z) cho ensemble discrete coherent-state và dùng (K_{raw}=\beta I_{AB}-\chi_{BE}).
- Không có finite-key correction, parameter-estimation confidence interval, composable security parameter, privacy-amplification overhead hoặc authentication cost trong objective.
- Không có mô hình trusted detector riêng trong đường PyTorch.
- Loại phép đo bộ thu (homodyne/heterodyne) không được khai báo tường minh trong lớp PS–GS; chỉ có quy ước kênh phức và công thức covariance. **Chưa xác định từ mã nguồn hiện tại.**
- Các giả định tấn công (collective/coherent), reverse/direct reconciliation và chứng minh bảo mật đầy đủ không được mã hóa thành metadata trong script. **Chưa xác định từ mã nguồn hiện tại.**

## Giới hạn tối ưu hóa

- Đây không phải autoencoder có decoder. Không có reconstruction loss hoặc neural demapper.
- MLP xác suất phụ thuộc kênh có 33,536 tham số; hình học có tensor 512 số thực. Với đối xứng bốn phần tư, chỉ 128 bậc tự do hình học được đọc hiệu dụng nhưng optimizer vẫn chứa toàn bộ tensor.
- Gumbel–Softmax tùy chọn không tham gia objective active. Vì vậy không thể dùng kết quả hiện tại để đánh giá lợi ích của straight-through sampling.
- `probabilities_safe` chỉ bảo vệ log; xác suất cực nhỏ vẫn có thể xuất hiện do softmax/logit clip.
- Drift penalty so với QAM chuẩn hóa theo PMF đều, trong khi chòm sao hiện hành chuẩn hóa theo PMF đang học; vì thế penalty kết hợp cả dịch chuyển thô và hiệu ứng tái chuẩn hóa.
- Entropy penalty có trọng số bằng 0 trong cấu hình đầy đủ, mặc dù entropy vẫn là điều kiện hard-recovery tối thiểu 0.25 bit.
- Epoch-zero bảo đảm không trả về nghiệm tệ hơn theo tập xác thực trong từng pipeline đã chạy, nhưng không bảo đảm optimum toàn cục hoặc gain test.

## Xung đột và điểm chưa xác định

| Vấn đề | Kết luận đã xác minh |
|---|---|
| “Rayleigh symbol-probability shaping” | Không tồn tại; baseline thực là Binomial. Rayleigh chỉ ở beam displacement. |
| Gumbel–Softmax trong huấn luyện | Primitive tồn tại và trainer cũ có thể gọi, nhưng mẫu không đi vào loss; `train_phase` active không bật nó. |
| Detector (\eta,v_{el}) | Có hằng số dự án và công thức Gaussian cũ, nhưng không dùng trong discrete MI/Holevo active. |
| `T_eff` so với `T_samples` | `T_eff` được report, nhưng train/evaluation dùng mẫu tức thời `T_samples`. |
| “Reference paper” joint shaping | Không tìm thấy bài *Joint Learning of Geometric and Probabilistic Constellation Shaping* trong repository; paper hiện có là bài satellite-to-ground CV-QKD. |
| Kết quả PS+GS | Run nhanh lưu sẵn thấp hơn PS; báo cáo tự đánh dấu chưa hội tụ, không đủ kết luận phổ quát. |
| Đơn vị (V_A,\epsilon,v_{el}) | Tên/config ám chỉ SNU; quy trình hiệu chuẩn vật lý chưa được mã hóa. |

## Phạm vi khảo sát repository

Đã lập danh mục đệ quy toàn bộ tệp và rà soát tất cả mã/cấu hình/tài liệu có liên quan đến đường PS–GS, gồm script chính, hai config PS–GS, config sweep, test PS–GS/sweep/discrete-MI, mô-đun `uav_hap_1` về config/channel/zstar, MI tham chiếu `uav_hap_1_sample`, visualization, hướng dẫn huấn luyện, báo cáo/CSV/checkpoint metadata đã lưu và bài báo văn bản. Các ảnh, PDF kết quả, bytecode, log fading số lượng lớn và checkpoint nhị phân được lập danh mục nhưng không được diễn giải như định nghĩa mô hình; định nghĩa khoa học được truy về nguồn văn bản và mã tạo chúng.
