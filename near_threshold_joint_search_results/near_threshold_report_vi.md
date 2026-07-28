# Tìm kiếm miền Joint PS+GS vượt MB gần ngưỡng tạo khóa

## Kết luận bắt buộc

**3. Joint chỉ vượt MB-fixed; không vượt MB-global-opt một cách xác nhận được.**

MB-global-opt cho miền tìm kiếm dùng nu*=0.32; MB-fixed dùng nu=0.1. Oracle-per-state được chọn bằng AWGN validation riêng rồi mới đánh giá trên test noise.

## Trả lời trực tiếp

- Chênh lệch discovery lớn nhất xuất hiện ở SNR -6.996 dB, thuộc miền **saturation/highest**, với Delta K=+4.762034e-03. Giá trị này chỉ dùng để chọn ứng viên.
- Trong các case final-test, nguồn chênh lệch tốt nhất là **No positive gain**.
- Giảm outage lớn nhất trong fading test là +4.687500e-03 ở deterministic.

## Kiểm tra cơ chế

- PS checkpoint: ps epoch 0; max state L1=0.000e+00.
- Joint checkpoint: geometry_warmup epoch 70; max state L1=0.000e+00.
- Joint geometry drift=1.477e-04, d_min=3.075e-01, peak=1.121e+01.

PMF Joint bất biến theo trạng thái trong checkpoint hiện tại; mọi gain cục bộ không được quy cho adaptive PS.

## Xác nhận ứng viên

| Case | T | epsilon | SNR dB | Baseline | K_MB | K_Joint | Delta K | CI 95% | Key extension | Nguồn |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 0 | 1.0000e-01 | 0.0300 | -7.00 | MB-fixed | +2.1683e-02 | +2.1841e-02 | +1.5797e-04 | [+1.578e-04, +1.582e-04] | 0.00 | Security-driven |
| 0 | 1.0000e-01 | 0.0300 | -7.00 | MB-global-opt | +2.2664e-02 | +2.1841e-02 | -8.2250e-04 | [-1.578e-03, -6.659e-05] | 0.00 | No positive gain |
| 0 | 1.0000e-01 | 0.0300 | -7.00 | MB-oracle-per-state | +2.2534e-02 | +2.1841e-02 | -6.9305e-04 | [-8.900e-04, -4.961e-04] | 0.00 | No positive gain |
| 1 | 6.8129e-02 | 0.0150 | -8.66 | MB-fixed | +1.9021e-02 | +1.9111e-02 | +9.0016e-05 | [+8.992e-05, +9.011e-05] | 0.00 | Security-driven |
| 1 | 6.8129e-02 | 0.0150 | -8.66 | MB-global-opt | +1.9299e-02 | +1.9111e-02 | -1.8768e-04 | [-6.798e-04, +3.044e-04] | 0.00 | No positive gain |
| 1 | 6.8129e-02 | 0.0150 | -8.66 | MB-oracle-per-state | +1.9400e-02 | +1.9111e-02 | -2.8902e-04 | [-6.356e-04, +5.759e-05] | 0.00 | No positive gain |
| 2 | 3.1623e-02 | 0.0000 | -11.99 | MB-fixed | +1.1932e-02 | +1.1937e-02 | +4.5362e-06 | [+4.516e-06, +4.556e-06] | 0.00 | Security-driven |
| 2 | 3.1623e-02 | 0.0000 | -11.99 | MB-global-opt | +1.2028e-02 | +1.1937e-02 | -9.0789e-05 | [-3.917e-04, +2.101e-04] | 0.00 | No positive gain |
| 2 | 3.1623e-02 | 0.0000 | -11.99 | MB-oracle-per-state | +1.2093e-02 | +1.1937e-02 | -1.5617e-04 | [-6.144e-04, +3.021e-04] | 0.00 | No positive gain |
| 3 | 3.1623e-05 | 0.0300 | -41.99 | MB-fixed | +5.0021e-07 | +6.1409e-07 | +1.1388e-07 | [+1.139e-07, +1.139e-07] | 0.00 | Security-driven |
| 3 | 3.1623e-05 | 0.0300 | -41.99 | MB-global-opt | +1.1397e-06 | +6.1409e-07 | -5.2561e-07 | [-7.534e-07, -2.978e-07] | 0.00 | No positive gain |
| 3 | 3.1623e-05 | 0.0300 | -41.99 | MB-oracle-per-state | +1.0675e-06 | +6.1409e-07 | -4.5340e-07 | [-5.233e-07, -3.835e-07] | 0.00 | No positive gain |
| 4 | 1.4678e-05 | 0.0250 | -45.32 | MB-fixed | +8.6055e-07 | +9.1230e-07 | +5.1752e-08 | [+5.175e-08, +5.176e-08] | 0.00 | No positive gain |
| 4 | 1.4678e-05 | 0.0250 | -45.32 | MB-global-opt | +1.2571e-06 | +9.1230e-07 | -3.4475e-07 | [-4.115e-07, -2.780e-07] | 0.00 | No positive gain |
| 4 | 1.4678e-05 | 0.0250 | -45.32 | MB-oracle-per-state | +1.2400e-06 | +9.1230e-07 | -3.2774e-07 | [-4.041e-07, -2.514e-07] | 0.00 | No positive gain |
| 5 | 1.2115e-05 | 0.0250 | -46.16 | MB-fixed | +5.9474e-07 | +6.3801e-07 | +4.3269e-08 | [+4.327e-08, +4.327e-08] | 0.00 | No positive gain |
| 5 | 1.2115e-05 | 0.0250 | -46.16 | MB-global-opt | +8.9858e-07 | +6.3801e-07 | -2.6058e-07 | [-3.332e-07, -1.880e-07] | 0.00 | No positive gain |
| 5 | 1.2115e-05 | 0.0250 | -46.16 | MB-oracle-per-state | +8.8787e-07 | +6.3801e-07 | -2.4987e-07 | [-3.311e-07, -1.686e-07] | 0.00 | No positive gain |
| 6 | 4.6416e-03 | 0.0250 | -20.32 | MB-fixed | +7.8360e-04 | +7.9360e-04 | +1.0001e-05 | [+9.999e-06, +1.000e-05] | 0.00 | Security-driven |
| 6 | 4.6416e-03 | 0.0250 | -20.32 | MB-global-opt | +8.4378e-04 | +7.9360e-04 | -5.0180e-05 | [-8.173e-05, -1.863e-05] | 0.00 | No positive gain |
| 6 | 4.6416e-03 | 0.0250 | -20.32 | MB-oracle-per-state | +8.4511e-04 | +7.9360e-04 | -5.1509e-05 | [-8.066e-05, -2.235e-05] | 0.00 | No positive gain |
| 7 | 4.6416e-03 | 0.0300 | -20.32 | MB-fixed | +6.1835e-04 | +6.2905e-04 | +1.0700e-05 | [+1.070e-05, +1.070e-05] | 0.00 | Security-driven |
| 7 | 4.6416e-03 | 0.0300 | -20.32 | MB-global-opt | +7.0010e-04 | +6.2905e-04 | -7.1050e-05 | [-1.075e-04, -3.457e-05] | 0.00 | No positive gain |
| 7 | 4.6416e-03 | 0.0300 | -20.32 | MB-oracle-per-state | +6.9963e-04 | +6.2905e-04 | -7.0574e-05 | [-1.086e-04, -3.258e-05] | 0.00 | No positive gain |
| 8 | 2.1544e-03 | 0.0100 | -23.66 | MB-fixed | +5.8821e-04 | +5.9177e-04 | +3.5573e-06 | [+3.556e-06, +3.558e-06] | 0.00 | Security-driven |
| 8 | 2.1544e-03 | 0.0100 | -23.66 | MB-global-opt | +6.1238e-04 | +5.9177e-04 | -2.0612e-05 | [-3.710e-05, -4.122e-06] | 0.00 | No positive gain |
| 8 | 2.1544e-03 | 0.0100 | -23.66 | MB-oracle-per-state | +6.1238e-04 | +5.9177e-04 | -2.0612e-05 | [-3.710e-05, -4.122e-06] | 0.00 | No positive gain |

## Điều kiện để gọi outperform

- Case có paired evaluation CI dương so với MB-global-opt: 0.
- Case key-extension có CI dương: 0.
- Fading distributions có CI dương: 0.
- Independent training seeds hiện có: 1, không phải 10. Vì vậy cột `outperform_allowed` luôn False và không có tuyên bố ưu thế ổn định.
- Effect floor để loại gain thuần số: 1.0e-08 bit/symbol.
- Các ablation training chưa có checkpoint không được thay bằng smoke run.

## Phạm vi và tái lập

- Coarse/fine grid dùng direct conditional T. Một giá trị T không có ánh xạ ngược duy nhất sang L, Cn2, visibility, W0 và aperture; không bịa một cấu hình vật lý duy nhất.
- Synthetic fading giữ cùng mean T nhưng thay variance, deep-fade probability và tail.
- Heatmap discovery đánh dấu K_MB=0 và K_Joint=0; candidate confirmation dùng test noise độc lập và ncut theo config.
- Runtime: 515.1 s initial search + 759.0 s high-AWGN confirmation; quick=False; device=cuda.
- Chi tiết metric của ba case tốt nhất nằm trong `three_best_case_details.csv`; PMF và tọa độ chòm sao theo từng symbol nằm trong `three_best_case_symbol_data.csv`.
