# Ma trận truy vết mã nguồn

| Scientific concept | Function/class/config field | Source and verified lines | Role in active path |
|---|---|---|---|
| Entry point | `main` | `uav_hap_joint_ps_gs.py`, 3329–3626 | Điều phối train, evaluation và artifact |
| Cấu hình JSON | `parse_args` | `uav_hap_joint_ps_gs.py`, 3105–3240 | JSON ghi đè default argparse |
| QAM 256 | `build_constellation` | `uav_hap_1/zstar/base.py`, 8–14 | Tọa độ (16\times16), thứ tự (16k+l) |
| PMF đều/MB/nhị thức | `build_probs_*` | `uav_hap_1/zstar/base.py`, 17–38 | Baseline và initialization |
| Mạng PS | `JointPSGS256QAM.__init__` | `uav_hap_joint_ps_gs.py`, 188–245 | MLP 3–128–256, bias log-PMF |
| Đặc trưng kênh | `channel_features` | `uav_hap_joint_ps_gs.py`, 285–296 | (log T,\epsilon,\mathrm{SNR}_{dB}) |
| Softmax và logit clip | `forward` | `uav_hap_joint_ps_gs.py`, 308–337 | PMF phụ thuộc kênh |
| Tọa độ GS/đối xứng | `effective_raw_constellation` | `uav_hap_joint_ps_gs.py`, 298–306 | none/central/fourfold |
| Chuẩn hóa có trọng số | `normalize_constellation_batch` | `uav_hap_joint_ps_gs.py`, 153–171 | Tâm 0 và (2E|\alpha|^2=V_A) |
| Gumbel tùy chọn | `forward`, `annealed_gumbel_temperature` | `uav_hap_joint_ps_gs.py`, 345–368 | Tạo one-hot; không nối vào active loss |
| AWGN antithetic | `make_standard_complex_noise` | `uav_hap_joint_ps_gs.py`, 371–386 | Common random numbers cho MI |
| (I_{AB}) | `discrete_mi_mismatched_awgn_batch` | `uav_hap_joint_ps_gs.py`, 389–475 | Liệt kê symbol, Monte Carlo noise |
| Trạng thái coherent | `coherent_state_matrix` | `uav_hap_joint_ps_gs.py`, 478–483 | Fock truncation |
| Holevo | `differentiable_security_block` | `uav_hap_joint_ps_gs.py`, 502–639 | (\tau,w,Z,\Gamma,\lambda_i,\chi) khả vi |
| SKR/loss | `shaping_loss` | `uav_hap_joint_ps_gs.py`, 642–685 | (-K_{raw})+regularization |
| Raw/clipped reporting | `evaluate_output` | `uav_hap_joint_ps_gs.py`, 722–768 | Train raw, report positive part |
| Geometry metrics | `geometry_statistics` | `uav_hap_joint_ps_gs.py`, 1075–1096 | Tâm, năng lượng, khoảng cách, entropy |
| Checkpoint ranking | `checkpoint_rank` | `uav_hap_joint_ps_gs.py`, 1117–1142 | Raw SKR và tie-breakers |
| RNG/checkpoint | `capture_rng_states`, `save/load_training_checkpoint` | `uav_hap_joint_ps_gs.py`, 1058–1200 | Reproducibility và resume |
| Optimizer/scheduler | `build_optimizer`, `build_scheduler` | `uav_hap_joint_ps_gs.py`, 1203–1247 | Adam/AdamW; plateau/cosine |
| Epoch-zero | `train_phase` | `uav_hap_joint_ps_gs.py`, 1393–1471 | Đánh giá/lưu trước update |
| Resampling train | `train_phase` | `uav_hap_joint_ps_gs.py`, 1477–1523 | Pool fading và AWGN mới theo epoch |
| Recovery | `train_phase` | `uav_hap_joint_ps_gs.py`, 1564–1603 | Hủy update lỗi, giảm LR |
| Early stopping | `train_phase` | `uav_hap_joint_ps_gs.py`, 1605–1717 | Fixed validation raw SKR |
| Joint initialization | `initialize_joint_candidate`, `evaluate_joint_initializations` | `uav_hap_joint_ps_gs.py`, 1774–1929 | PS/GS/combined/PS-preserving |
| Independent splits | `independent_channel_splits` | `uav_hap_joint_ps_gs.py`, 2013–2046 | Seed train/val/test riêng |
| Uncertainty | `evaluate_uncertainty` | `uav_hap_joint_ps_gs.py`, 2049–2138 | Repeated independent seeds, normal CI |
| Cutoff convergence | `evaluate_ncut_convergence` | `uav_hap_joint_ps_gs.py`, 2141–2178 | So sánh cutoff |
| Validation | `validate_experiment` | `uav_hap_joint_ps_gs.py`, 2757–2933 | Invariants, determinism, parity |
| Physical defaults | dataclasses/constants | `uav_hap_1/config.py`, 6–104 | Geometry/channel/QKD defaults |
| Link and atmosphere | `link_distance_m`, `_eta_atm` | `uav_hap_1/channel/channel_model.py`, 10–41 | Distance và Kruse loss |
| Diffraction/aperture | `_beam_radius_at_receiver`, `_shape_parameters` | `uav_hap_1/channel/channel_model.py`, 44–78 | (W_L,T_0,\Gamma,R) |
| Beam wandering | `_sigma2_uav`, `_sigma2_turb` | `uav_hap_1/channel/channel_model.py`, 81–122 | Jitter+turbulence |
| Rayleigh channel fading | `channel` | `uav_hap_1/channel/channel_model.py`, 125–199 | (r\) Rayleigh và `T_samples` |
| MI reference | `mismatched_mi_discrete_awgn` | `uav_hap_1_sample/iab/discrete.py`, 31–147 | Đối chiếu active batched MI |
| Six-scheme sweep | `SCHEME_ORDER`, `build_scheme_outputs` | `visualize_skr_parameter_sweeps.py`, 35–42, 309–329 | Uniform/MB/Binomial/GS/PS/PS+GS |
| Sweep uncertainty | `compute_student_t_ci` | `visualize_skr_parameter_sweeps.py`, 560–576 | Student-(t) CI cho repetitions |
| Weighted normalization test | test method | `test_uav_hap_joint_ps_gs.py`, 18–36 | Tâm/năng lượng/gradient |
| PS feasible special case | test method | `test_uav_hap_joint_ps_gs.py`, 38–64 | Joint epoch-zero bằng PS |
| Checkpoint/RNG test | test method | `test_uav_hap_joint_ps_gs.py`, 66–121 | Rank và restore |
| Holevo gradient test | test method | `test_uav_hap_joint_ps_gs.py`, 123–146 | Gradient tới logits/tọa độ |
| Full-cutoff test | test method | `test_uav_hap_joint_ps_gs.py`, 189–206 | Hữu hạn tại 150 |
| Rayleigh/binomial distinction test | test method | `test_visualize_skr_parameter_sweeps.py`, 140–149 | Không gọi PMF là Rayleigh |

## Cấu hình và báo cáo đã đối chiếu

| File | Nội dung được dùng |
|---|---|
| `ps_gs_fast_config.json`, dòng 1–42 | Lịch smoke/development và artifact đã lưu |
| `ps_gs_full_config.json`, dòng 1–48 | Baseline học thuật chính |
| `skr_visualization_config.json`, dòng 1–64 | Sweep vật lý, detector note, seed/budget |
| `PS_GS_TRAINING.md`, dòng 1–175 | Quy ước, lệnh chạy, ablation và giới hạn diễn giải |
| `ps_gs_results_fast/experiment_report.txt`, dòng 1–130 | Báo cáo run rút gọn và các kiểm tra đã qua |
| `ps_gs_results_fast/comparison.csv`, dòng 1–6 | Quan sát định lượng run nhanh; không dùng làm kết luận phổ quát |

## Các nhánh phụ/xung đột

Các thư mục `project/`, `uav_hap/`, `uav_hap_1/` và `uav_hap_1_sample/` chứa nhiều thế hệ mô hình. Đường PS–GS chỉ nhập `uav_hap_1.channel.channel_model`, `uav_hap_1.config`, `uav_hap_1.zstar.*` và MI tham chiếu từ `uav_hap_1_sample.iab.discrete`. Các công thức ở nhánh khác không được coi là active nếu không có import/truy vết nêu trên.
