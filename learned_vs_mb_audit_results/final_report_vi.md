# Audit learned shaping so với Maxwell–Boltzmann QAM

## Kết luận điều hành

**Không tìm thấy bằng chứng learned shaping vượt MB-global-opt trong miền đã khảo sát.**

Kết luận này cố ý không nâng paired evaluation seeds thành independent training seeds. Các checkpoint được cung cấp chỉ đại diện cho một seed huấn luyện; vì vậy tiêu chí “outperform mạnh” của protocol chưa thể được thỏa, bất kể CI đánh giá có dương.

## 1. Xác minh MB

- `QAM_NU_TILDE` hiện tại: `0.1`; MB-fixed dùng `0.1`.
- MB-global-opt chọn trên validation độc lập: `nu* = 0.41` từ grid [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.3, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.5, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.7, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.8].
- Mã hiện tại dùng `exp[-nu_tilde((k-7.5)^2+(l-7.5)^2)]`. Đây là tham số theo chỉ số lưới; nó chỉ tương đương `exp(-nu|c_i|^2)` sau khi quy đổi thang tọa độ.
- Với QAM thô của evaluator, `alpha0^2=12/17`, nên trước bước tái chuẩn hóa `nu_coordinate = 30*nu_tilde/alpha0^2 = 42.5*nu_tilde`: MB-fixed tương ứng 4.25 và MB-global-opt tương ứng 17.425 trên tọa độ thô. Sau chuẩn hóa phụ thuộc PMF, không được đồng nhất hai tham số hóa mà không nêu thang tọa độ.
- Geometry baseline là QAM vuông 16×16 của dự án. Mỗi PMF được đặt tâm và chuẩn hóa lại sao cho `2 E_p|alpha|^2 = V_A`; vì vậy MB và learned dùng cùng `V_A`.
- Trong từng phép so sánh, mọi scheme dùng chung chính xác tensor T và AWGN, cùng cutoff và sample budget.
- MB-fixed trước đây chưa tối ưu theo V_A, T, epsilon hay phân phối kênh.

## 2. Bốn câu hỏi nghiên cứu

| Câu hỏi | So sánh | Mean ΔK | CI 95% | P(ΔK>0) | Nguồn gain |
|---|---|---:|---:|---:|---|
| Q1 | PS − MB-fixed | -5.807854e-15 | [-6.389731e-15, -5.225977e-15] | 0.00 | No positive gain |
| Q1 | GS − MB-fixed | -1.395138e-02 | [-1.479921e-02, -1.310354e-02] | 0.00 | No positive gain |
| Q1 | PS+GS − MB-fixed | +3.689708e-05 | [+3.474383e-05, +3.905034e-05] | 1.00 | Security-driven |
| Q2 | PS − MB-global-opt | -2.226840e-04 | [-7.677664e-04, +3.223984e-04] | 0.40 | No positive gain |
| Q2 | GS − MB-global-opt | -1.417406e-02 | [-1.533131e-02, -1.301681e-02] | 0.00 | No positive gain |
| Q2 | PS+GS − MB-global-opt | -1.857869e-04 | [-7.306544e-04, +3.590805e-04] | 0.40 | No positive gain |
| Q3 | PS − MB-oracle-per-state | -1.411328e-03 | [-1.851490e-03, -9.711664e-04] | 0.00 | No positive gain |
| Q3 | PS+GS − MB-oracle-per-state | -1.374431e-03 | [-1.814100e-03, -9.347626e-04] | 0.00 | No positive gain |
| Q4 | PS+GS − PS | +3.689708e-05 | [+3.474383e-05, +3.905034e-05] | 1.00 | Security-driven |
| Q4 | PS+GS − GS | +1.398827e-02 | [+1.313846e-02, +1.483808e-02] | 1.00 | Joint improvement |

## 3. PS có thực sự thích nghi không?

- PS: max state-to-state L1 = 0.000000e+00; Jacobian logits theo log10(T) = 0.000000e+00; theo epsilon = 0.000000e+00; checkpoint = ps epoch 0.
- PS+GS: max state-to-state L1 = 0.000000e+00; checkpoint = geometry_warmup epoch 70.

Nếu các đại lượng trên bằng hoặc gần 0 và checkpoint PS là epoch 0, kết luận đúng là **PS chưa học cơ chế thích nghi; nó chủ yếu giữ MB initialization**, không phải AI gain.

## 4. Hình học

Joint: d_min=3.074941e-01, E_max=1.120827e+01, D_drift=1.476673e-04, checkpoint=geometry_warmup epoch 70.

## 5. Bản đồ pha và xác nhận độc lập

- Grid exploratory: learned có mean K cao hơn MB-global-opt tại 47/100 ô.
- Số trường hợp selected có CI final-test hoàn toàn dương: 0/6.
- Heatmap là bước discovery với cutoff/budget thấp hơn; chỉ bảng `selected_case_summary.csv` được đánh giá lại ở budget confirmation. Không nội suy hoặc chỉ hiển thị ô đẹp nhất.

| Loại | Điều kiện | Scheme | Mean ΔK | CI 95% | Nguồn gain | Xác nhận |
|---|---|---|---:|---:|---|---|
| best | V_a (40, 0.25) | PS+GS | -3.227854e-04 | [-1.562275e-03, +9.167044e-04] | No positive gain | False |
| best | V_a (22.5, 0.2) | PS+GS | -8.180028e-04 | [-1.941870e-03, +3.058639e-04] | No positive gain | False |
| best | V_a (40, 0.1) | PS+GS | -8.780618e-04 | [-1.758497e-03, +2.373133e-06] | No positive gain | False |
| failure | V_a (31.25, 0.25) | PS+GS | +1.647705e-04 | [-9.951363e-04, +1.324677e-03] | Mixed/none | False |
| failure | V_a (40, 0.15) | PS+GS | -5.246705e-04 | [-2.033921e-03, +9.845803e-04] | No positive gain | False |
| failure | T_epsilon (0.2, 0.0225) | PS+GS | -1.160862e-03 | [-2.105677e-03, -2.160465e-04] | No positive gain | False |

## 6. Phạm vi bằng chứng và ablation

- 8/16 ablation huấn luyện bắt buộc chưa có checkpoint độc lập và không được giả lập bằng smoke run.
- Modulation order 16/64 chưa thể kiểm tra vì implementation learned hiện khóa cứng M=256.
- CIs trong báo cáo là Student-t paired CI trên channel/AWGN repetitions, không phải training-seed CI.
- Sai số cutoff lớn nhất quan sát giữa ncut=120 và 150 trên cùng mẫu: 5.884182e-15 bit/symbol.
- Kết quả là asymptotic raw SKR theo covariance/Holevo bound hiện hành, chưa phải finite-key composable proof.

## 7. Trả lời khoa học cuối cùng

- Learned mechanism mới hay học lại MB? Với PS, `adaptive_pmf_detected=False` và epoch=0. Dữ liệu trực tiếp hiện tại ủng hộ kết luận **học lại/giữ MB**, không chứng minh một cơ chế bảo mật thích nghi mới.
- Độ phức tạp MLP/CSI/joint có được biện minh không? Chưa thể khẳng định. Chỉ geometry warm-up có thể tạo một hiệu chỉnh nhỏ; cần nhiều training seeds và các ablation còn thiếu trước khi đánh đổi độ phức tạp.

## 8. Tái lập

- Config: `E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\learned_vs_mb_audit_config.json`
- Runtime: 624.5 s; device=cuda; quick=False.
- Tất cả grid, seeds, hashes, raw metrics và trạng thái ablation nằm trong thư mục kết quả.

## 9. Kiểm tra modulation variance và đầu ra trường hợp

V_A được sweep trên validation với MB re-optimize nu tại từng V_A. Learned checkpoints chỉ được đánh giá ngoài phân phối huấn luyện V_A=2, không retrain.

| Scheme | V_A tốt nhất | K_raw validation tốt nhất | nu* của MB-global tại cùng V_A |
|---|---:|---:|---:|
| MB-fixed | 4 | +2.671808e-02 | 0.23 |
| MB-global-opt | 4 | +2.709968e-02 | 0.23 |
| PS | 4 | +2.671808e-02 | 0.23 |
| GS | 1 | +1.105288e-02 | 0.63 |
| PS+GS | 4 | +2.674162e-02 | 0.23 |

MB-fixed và PMF của PS/PS+GS vẫn dùng nu=0.1; cột nu* chỉ cho biết baseline MB-global được re-optimize tại cùng V_A.

Ba case discovery tốt nhất và ba case thất bại đều được giữ lại trong `selected_case_details.csv`; PMF và toàn bộ 256 tọa độ nằm trong `selected_case_symbol_data.csv`. Không case nào có CI xác nhận hoàn toàn dương thì `outperformance_domains.csv` ghi rõ không có miền outperform được xác nhận.
