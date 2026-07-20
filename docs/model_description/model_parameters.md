# Tham số của mô hình

Giá trị baseline dưới đây ưu tiên `ps_gs_full_config.json`; nếu trường không có trong JSON, giá trị mặc định CLI hoặc dataclass được ghi rõ. Đơn vị “không thứ nguyên” được dùng khi mã nguồn xác định trực tiếp; trường không có đơn vị xác minh được ghi “Chưa xác định từ mã nguồn hiện tại”.

## Bảng 2. Các tham số chính

| Mathematical symbol | Code variable | Description | Unit | Baseline value | Trainable/fixed | Source |
|---|---|---|---|---:|---|---|
| (M) | `SYMBOL_COUNT`, `QAM_M` | Số symbol QAM | symbol | 256 | Cố định | `uav_hap_joint_ps_gs.py`:56; `uav_hap_1/config.py`:23 |
| (k,l) | loop indices | Chỉ số trục I/Q | không thứ nguyên | 0…15 | Cố định | `uav_hap_1/zstar/base.py`:10–13 |
| (\alpha_0) | `QAM_ALPHA0_UNIFORM` | Hệ số QAM thô | không thứ nguyên | (\sqrt{12/17}) | Cố định | `uav_hap_1/config.py`:28 |
| (\tilde\nu) | `QAM_NU_TILDE` | Tham số PMF Maxwell–Boltzmann | không thứ nguyên | 0.1 | Cố định | `uav_hap_1/config.py`:29; `uav_hap_1/zstar/base.py`:29–38 |
| (p_i) | `probabilities` | Xác suất symbol | không thứ nguyên | MB lúc khởi tạo | Học trong PS/joint | `uav_hap_joint_ps_gs.py`:229–235, 329–337 |
| (\ell_i) | `logits` | Logit xác suất | không thứ nguyên | (\log p_i^{(0)}) | Học trong PS/joint | `uav_hap_joint_ps_gs.py`:220–235 |
| ((I_i,Q_i)) | `raw_constellation` | Tọa độ chòm sao thô | không thứ nguyên | QAM vuông | Học trong GS/joint | `uav_hap_joint_ps_gs.py`:237–240 |
| (V_A) | `va`, `target_va` | Phương sai điều chế, (2E|\alpha|^2) | SNU theo tên cấu hình; quy ước đơn vị không giải thích thêm | 2.0 | Cố định | `uav_hap_joint_ps_gs.py`:3163; `skr_visualization_config.json`:7 |
| (\beta) | `beta`, `QAM_BETA` | Hiệu suất reconciliation | không thứ nguyên | 0.95 | Cố định | `uav_hap_1/config.py`:31; `ps_gs_full_config.json` dùng mặc định |
| (\epsilon) | `epsilon`, `QAM_EPS` | Nhiễu dư | SNU theo tên cấu hình | 0.001 | Cố định/sweep | `uav_hap_1/config.py`:32; `uav_hap_joint_ps_gs.py`:3165 |
| \(n_{cut}\) | `train_ncut` | Cutoff Fock khi huấn luyện | mức Fock | 64 | Cố định theo phase | `ps_gs_full_config.json`:34 |
| \(n_{cut}^{val}\) | `validation_ncut` | Cutoff xác thực | mức Fock | 150 | Cố định | `ps_gs_full_config.json`:35 |
| \(n_{cut}^{final}\) | `final_ncut` | Cutoff refinement/test | mức Fock | 150 | Cố định | `ps_gs_full_config.json`:36 |
| (H_{UAV}) | `H_UAV_m` | Cao độ UAV | m | 0 | Cố định | `uav_hap_1/config.py`:64 |
| (H_{HAP}) | `H_HAP_m` | Cao độ HAP | m | 20,000 | Cố định | `uav_hap_1/config.py`:65 |
| (d_h) | `d_h_m` | Khoảng cách ngang | m | 0 | Cố định | `uav_hap_1/config.py`:67 |
| (\theta) | `tilt_deg` | Góc nghiêng link | degree | 0 | Cố định | `uav_hap_1/config.py`:66 |
| (\lambda) | `wavelength_m`, `LAMBDA` | Bước sóng quang | m | (1550\times10^{-9}) | Cố định | `uav_hap_1/config.py`:7,73 |
| (W_0) | `beam_waist_m`, `W0_m` | Beam waist phát | m | 0.0626 | Cố định/sweep | `uav_hap_joint_ps_gs.py`:3185; `uav_hap_1/config.py`:74 |
| (a) | `aperture_radius_m`, `a_m` | Bán kính aperture thu | m | 0.20 | Cố định/sweep | `uav_hap_joint_ps_gs.py`:3186; `uav_hap_1/config.py`:75 |
| (V) | `visibility_km` | Tầm nhìn khí tượng | km | 10 | Cố định/sweep | `uav_hap_1/config.py`:76 |
| (C_n^2) | `cn2`, `Cn2` | Hằng số cấu trúc chiết suất | m(^{-2/3}) (được report ghi) | (10^{-15}) | Cố định/sweep | `uav_hap_1/config.py`:78; `uav_hap_joint_ps_gs.py`:2989 |
| (\sigma_x,\sigma_y,\sigma_z) | `sigma_x_m`, etc. | Jitter vị trí UAV | m | 0.0521, 0.0502, 0.0703 | Cố định | `uav_hap_1/config.py`:83–85 |
| (\sigma_\theta,\sigma_\phi,\sigma_\psi) | corresponding fields | Jitter góc UAV | rad | 0.0026, 0.00204, 0.00406 | Cố định | `uav_hap_1/config.py`:86–88 |
| (\eta_{SMF}) | `eta_SMF` | Hiệu suất ghép sợi | không thứ nguyên | 1.0 | Cố định; không vào `T_samples` | `uav_hap_1/config.py`:95; `channel_model.py`:164–175 |
| (T_T,T_R) | `T_T`, `T_R` | Hệ số quang phát/thu | không thứ nguyên | 1.0, 1.0 | Cố định; không vào đường PS–GS | `uav_hap_1/config.py`:96–97 |
| (\eta) | `QAM_ETA` | Hiệu suất detector mặc định | không thứ nguyên | 0.95 | Cố định nhưng không dùng đường chính | `uav_hap_1/config.py`:33; import tại `uav_hap_joint_ps_gs.py`:42 |
| (v_{el}) | `QAM_V_EL` | Nhiễu điện tử detector | SNU theo tên | 0.001 | Cố định nhưng không dùng đường chính | `uav_hap_1/config.py`:34; import tại `uav_hap_joint_ps_gs.py`:45 |
| (d_0) | `separation_scale` | Scale separation penalty | không thứ nguyên | 0.15 | Cố định | `uav_hap_joint_ps_gs.py`:3166 |
| (n_{max}) | `max_photon_number` | Ngưỡng peak penalty trên (|x_i|^2) | không thứ nguyên trong code | 5.0 | Cố định | `uav_hap_joint_ps_gs.py`:3167 |
| (H_{min}) | `entropy_floor` | Sàn entropy penalty | bit | 5.0 | Cố định | `uav_hap_joint_ps_gs.py`:3168 |
| \(\lambda_{sep,peak,drift}\) | config fields | Trọng số regularization | không thứ nguyên | \(10^{-3}\) mỗi loại | Cố định/ramp | `ps_gs_full_config.json`:40–42 |
| \(\lambda_{ent}\) | `lambda_entropy` | Trọng số entropy penalty | không thứ nguyên | 0 | Cố định | `ps_gs_full_config.json`:43 |
| \(\gamma_p\) | `probability_lr` | Learning rate PS | — | \(10^{-3}\) | Hyperparameter | `ps_gs_full_config.json`:13 |
| \(\gamma_g\) | `constellation_lr` | Learning rate GS | — | \(10^{-4}\) | Hyperparameter | `ps_gs_full_config.json`:15 |
| — | `hidden_dim` | Chiều rộng MLP phân phối | neuron | 128 | Cố định | `uav_hap_joint_ps_gs.py`:3122 |
| — | `logit_clip` | Biên clip logit | không thứ nguyên | 30 | Cố định | `uav_hap_joint_ps_gs.py`:3180 |

## Ghi chú đơn vị

- Mã gọi (\epsilon), (v_{el}) và (V_A) theo quy ước SNU, nhưng không có định nghĩa hiệu chuẩn shot-noise chi tiết trong đường PS–GS. Ngoài quy ước tên trường, đơn vị vật lý tuyệt đối: **Chưa xác định từ mã nguồn hiện tại.**
- `max_photon_number` được áp lên năng lượng của chòm sao **đơn vị** (|x_i|^2), không trực tiếp lên (|\alpha_i|^2); tên biến vì thế không đủ để diễn giải như số photon vật lý tuyệt đối.
