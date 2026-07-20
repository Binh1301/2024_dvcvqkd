# Luồng kiến trúc mô hình UAV–HAP CV-QKD PS–GS

## Luồng tín hiệu chính

```text
Cấu hình vật lý và huấn luyện
  ├─ GeometryParams, ChannelParams → channel(...) → các mẫu T tức thời
  └─ epsilon, V_A, beta, n_cut, seed và sample budgets
                              ↓
Trạng thái kênh [log10(T), epsilon, SNR_dB]
                              ↓
Nguồn xác suất symbol
  ├─ Uniform / MB / Binomial cố định, hoặc
  └─ Linear(3,128) → ReLU → Linear(128,256) → clip logit → softmax
                              ↓
PMF p_i(T,epsilon), i=0,...,255
                              ↓
Chòm sao
  ├─ QAM vuông cố định (Uniform, MB, Binomial, PS), hoặc
  └─ raw_constellation 256×2 + phép chiếu đối xứng (GS, PS+GS)
                              ↓
Đặt tâm có trọng số và chuẩn hóa sum_i p_i |x_i|^2 = 1
                              ↓
Biên độ coherent alpha_i = sqrt(V_A/2) x_i
                    ┌─────────┴─────────┐
                    ↓                   ↓
 Kênh AWGN để tính I_AB       Ma trận mật độ tau và khối Holevo
 Y=sqrt(T)alpha_S+N           → Tr(C), w, Z, Gamma_AB
 → liệt kê 256 symbol         → lambda_1,2,3 → chi_BE
                    └─────────┬─────────┘
                              ↓
                 K_raw = beta I_AB - chi_BE
                              ↓
       loss = -mean(K_raw) + các regularizer được kích hoạt
                              ↓
 Lan truyền ngược → PS, GS hoặc đồng thời → xác thực → checkpoint
```

Không có chuỗi bit cụ thể, bộ gán nhãn Gray hay decoder nơ-ron trong đường này. Nguồn symbol được liệt kê chính xác khi tính kỳ vọng; Gumbel one-hot có thể được tạo bởi API mô hình nhưng không đi vào (I_{AB}), (\chi_{BE}) hoặc loss đang hoạt động.

## Bảng 4. Đầu vào và đầu ra của các mô-đun chính

| Module | Input | Output | Mathematical operation | Source file |
|---|---|---|---|---|
| `channel` | Hình học, visibility, (W_0,a,C_n^2), seed | `T_samples`, (T_{eff}), thống kê beam | Kruse + Gaussian diffraction + Rayleigh beam displacement | `uav_hap_1/channel/channel_model.py`, dòng 125–199 |
| `distribution_net` | ([\log_{10}T,\epsilon,\mathrm{SNR}_{dB}]) | 256 logits | MLP 3–128–256 | `uav_hap_joint_ps_gs.py`, dòng 220–235, 285–336 |
| `effective_raw_constellation` | `raw_constellation`, symmetry | 256 cặp I/Q | Chiếu none/central/fourfold | `uav_hap_joint_ps_gs.py`, dòng 298–306 |
| `normalize_unit_energy_batch` | (p_i,c_i^{raw}) | (x_i) | Đặt tâm và chuẩn hóa năng lượng có trọng số | `uav_hap_joint_ps_gs.py`, dòng 153–185 |
| `discrete_mi_mismatched_awgn_batch` | (p_i,\alpha_i,T,\epsilon,N_A) | (I_{AB}(T)) | Liệt kê symbol + Monte Carlo AWGN antithetic | `uav_hap_joint_ps_gs.py`, dòng 389–475 |
| `differentiable_security_block` | (p_i,\alpha_i,T,\epsilon,V_A,n_{cut}) | (\tau,w,Z,\Gamma,\lambda_i,\chi_{BE}) | Fock truncation, eigendecomposition, symplectic spectrum | `uav_hap_joint_ps_gs.py`, dòng 502–639 |
| `shaping_loss` | (I_{AB},\chi_{BE},x_i,p_i) | Loss và các thành phần | (-K_{raw})+separation+peak+drift+entropy | `uav_hap_joint_ps_gs.py`, dòng 642–685 |
| `train_phase` | Model, phase spec, train/validation samples | Best model, history, checkpoint | Adam/AdamW, scheduler, clipping, recovery | `uav_hap_joint_ps_gs.py`, dòng 1361–1754 |

## Giải thích từng tín hiệu

- (T) là độ truyền qua công suất tức thời sau khí quyển và pointing. Pipeline không dùng `T_samples_with_optics`.
- (p_i) là PMF theo trạng thái trong PS/joint và là PMF cố định trong các baseline/GS.
- (x_i) là chòm sao phức không thứ nguyên có năng lượng trung bình bằng một.
- (\alpha_i) là biên độ coherent sau khi đặt phương sai điều chế (V_A).
- (N) là AWGN phức chỉ dùng để tích phân (I_{AB}); fading (T) được lấy mẫu riêng từ mô hình UAV–HAP.
- (\tau) là hỗn hợp trạng thái coherent bị cắt trong cơ sở Fock; cutoff hữu hạn là xấp xỉ số chính.
- (K_{raw}) là mục tiêu; (K_+=\max(0,K_{raw})) chỉ phục vụ báo cáo.

**Chú thích hình:** *Hình X. Kiến trúc tối ưu đầu cuối PS–GS lấy cảm hứng từ Autoencoder cho hệ thống UAV–HAP CV-QKD.*
