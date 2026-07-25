# Phân tích khoa học sáu sweep SKR cho UAV–HAP CV-QKD

## Phạm vi, quy ước và nguồn

Báo cáo này ưu tiên dữ liệu thô và code tạo dữ liệu. Năm sweep đầu dùng các CSV đầy đủ trong `skr_parameter_sweep_results`; sweep khoảng cách dùng `skr_distance_sweep_results_gpu/skr_vs_distance.csv`. Các thư mục `quick`, `smoke` và `_sweep_probe` chỉ là kiểm tra pipeline, không được trộn vào kết luận. Script kiểm toán tái lập là [`analyze_skr_sweeps.py`](analyze_skr_sweeps.py); các bảng dẫn xuất nằm trong [`sweep_audit`](sweep_audit).

Quy ước:

- \(K_{\rm raw}=\beta I_{AB}-\chi_{BE}\), với \(\beta=0.95\).
- \(K_+=\mathbb E[\max(0,K_{\rm raw}(T))]\), không nhất thiết bằng \(\max(0,\mathbb E[K_{\rm raw}])\).
- Hình vẽ biểu diễn trung bình \(K_+\); CSV thô có cả \(K_{\rm raw}\) và \(K_+\).
- “Có ý nghĩa trên evaluation seed” nghĩa là CI Student-\(t\) ghép cặp 95% của chênh lệch giữa hai scheme không chứa 0. Nó không bao phủ uncertainty do huấn luyện vì chỉ có một training seed 2026.
- Mọi giá trị \(T\) trong báo cáo được tái tạo đúng từ `channel_seed`, `fading_samples` và code kênh; bảng nguồn là [`reconstructed_channel_samples.csv`](sweep_audit/reconstructed_channel_samples.csv).

## 1. Tóm tắt điều hành

1. Thứ hạng có ý nghĩa vật lý ổn định trên cả sáu sweep là **PS+GS > MB = PS > Binomial > GS > Uniform**. Không có đảo hạng đáng tin cậy giữa các artifact khác nhau; các “giao cắt” MB/PS chỉ do sai số máy \(10^{-14}\).
2. “PS” không phải PMF học được sau tối ưu: checkpoint tốt nhất là **epoch 0**, trùng Maxwell–Boltzmann đến sai số máy. Do đó dữ liệu chỉ chứng minh lợi ích của **MB cố định**, không chứng minh lợi ích của PS thích nghi trạng thái kênh.
3. PS+GS tốt nhất tại 126/126 điểm trung bình, nhưng gain bổ sung so với PS nhỏ: khoảng \(4.7\times10^{-10}\) đến \(1.69\times10^{-4}\) bit/symbol tùy miền; gần baseline chỉ khoảng **0.14%**.
4. Checkpoint joint được chọn tại epoch 70 của **geometry warm-up**, khi learning rate xác suất bằng 0. PMF joint bằng hệt PMF MB/PS; đây là “MB + chỉnh hình học nhỏ”, chưa phải bằng chứng cho tối ưu đồng thời PS và GS.
5. Gain của PS/MB, GS và joint gần như hoàn toàn đến từ **giảm \(\chi_{BE}\)**. \(I_{AB}\) giữa các scheme gần bằng nhau; dữ liệu không hỗ trợ câu chuyện “shaping thắng chủ yếu vì tăng mutual information”.
6. GS hơn Uniform khoảng 9.3–9.6% quanh baseline dù \(d_{\min}\) giảm từ 0.15339 xuống 0.13469 và peak energy tăng từ 2.6471 lên 2.7032. Cơ chế quan sát được là thay đổi \(Z,w,\mathrm{Tr}C\) và giảm \(\chi_{BE}\), không phải cải thiện khoảng cách cực tiểu hay peak.
7. Về biến thiên kênh, visibility tạo dynamic range SKR lớn nhất trên miền đã chọn; distance có độ nhạy cục bộ chuẩn hóa lớn nhất và là sweep duy nhất đi qua ngưỡng mất khóa.
8. Ở sweep distance, mean \(K_{\rm raw}\) của Uniform cắt 0 khoảng 52.27 km và GS khoảng 59.36 km. Theo từng repetition, trung bình ngưỡng lần lượt là \(52.36\) km (CI 95% 51.71–53.00) và \(59.33\) km (58.88–59.79).
9. MB, Binomial, PS và PS+GS vẫn có mean \(K_{\rm raw}>0\) tại 100 km, nhưng chỉ cỡ \(1.46\)–\(1.50\times10^{-7}\) bit/symbol; đây là miền gần sàn số, không nên diễn giải thành khả năng khóa đường dài đã được chứng minh chắc chắn.
10. Dao động ở sweep excess-noise và beam-waist chủ yếu đi cùng việc mỗi điểm dùng channel seed khác nhau. Chúng không đủ để kết luận cực trị vật lý; cần common channel samples **giữa các điểm x** để tách hiệu ứng tham số khỏi Monte Carlo.
11. Detector efficiency \(\eta=0.95\), electronic noise \(v_{\rm el}=0.001\), và optical factors được ghi trong config nhưng không đi vào đường MI/Holevo đang chạy; pipeline dùng `T_samples`, không dùng `T_samples_with_optics`.
12. Kết quả là asymptotic raw SKR với Holevo covariance bound; chưa có finite-key/composable correction. Kết luận bảo vệ được là “artifact MB cố định bền hơn Uniform trong mô hình này”, không phải “AI/learned shaping luôn tối ưu”.

Nguồn chính: các cột `I_AB`, `chi_BE`, `K_raw`, `K_positive` trong sáu CSV thô; [`comparison.csv`](../experiments/joint_seed2026/comparison.csv); [`scheme_shape_statistics.csv`](sweep_audit/scheme_shape_statistics.csv); metadata checkpoint được ghi trong [`skr_visualization_report.txt`](../skr_parameter_sweep_results/skr_visualization_report.txt).

## 2. Xác minh dữ liệu và pipeline

### 2.1 Bảng tham số sweep

| Parameter sweep | Ký hiệu | Đơn vị | Khoảng khảo sát | Baseline | Ý nghĩa vật lý trong active code | Ảnh hưởng trực tiếp |
|---|---:|---:|---:|---:|---|---|
| Receiver aperture radius | \(a\) | m | 0.10–0.30, 21 điểm tuyến tính | 0.20 | Bán kính khẩu độ thu; đổi coupling hình học `T0_power`, đồng thời đi vào phương sai lệch hướng UAV | \(T\) và phân bố fading, không đổi \(\xi\) |
| Atmospheric visibility | \(V\) | km | 5–40, 21 điểm tuyến tính | 10 | Điều khiển hệ số suy hao Kruse \(\xi_{\rm atm}(V)\) | \(T\) |
| Transmitter beam waist | \(W_0\) | m | 0.03–0.12, 21 điểm tuyến tính | 0.0626 | Điều khiển Rayleigh range, bán kính beam ở máy thu và hạng beam wandering do turbulence | \(T\) và phân bố fading |
| Turbulence strength | \(C_n^2\) | m\(^{-2/3}\) | \(10^{-16}\)–\(10^{-14}\), 21 điểm log | \(10^{-15}\) | Điều khiển \(\sigma_{\rm turb}^2\), từ đó dịch tâm beam Rayleigh | \(T\) và phân bố fading |
| Excess noise | \(\xi\) | SNU | 0–0.01, 21 điểm tuyến tính | 0.001 | Đi vào \(\sigma_c^2=1+T\xi/2\), covariance \(b\), \(Z\), MI và Holevo | Noise, không đổi kênh quang |
| Slant link distance | \(L\) | km | 20–100, 21 điểm tuyến tính | 20 | Giữ \(H_{\rm UAV}=0\), \(H_{\rm HAP}=20\) km; đổi horizontal distance và zenith angle để đạt slant range | \(T\): suy hao khí quyển, diffraction và turbulence |

Nguồn: `sweeps`, `baseline_channel_parameters`, `baseline_geometry` trong [`skr_visualization_config.json`](../skr_visualization_config.json); ánh xạ field/đơn vị trong `SWEEP_SPECS` của [`visualize_skr_parameter_sweeps.py`](../visualize_skr_parameter_sweeps.py); công thức kênh trong [`channel_model.py`](../uav_hap_1/channel/channel_model.py).

Active channel tính

\[
T=\eta_{\rm atm}\eta_{\rm point},\qquad
\eta_{\rm atm}=\exp[-\xi_{\rm Kruse}(V)L],
\]

và sinh độ lệch tâm beam theo Rayleigh. “Rayleigh” vì vậy chỉ là fading lệch tâm beam, **không** phải tên của PMF thứ ba. PMF thứ ba trong code và CSV là Binomial.

### 2.2 Sáu scheme, checkpoint và thống kê PMF/hình học

| Scheme | Nguồn | Epoch/phase | \(H(X)\) [bit] | Peak energy | \(d_{\min}\) | \(p_{\min}\) / \(p_{\max}\) | Phụ thuộc trạng thái trong checkpoint |
|---|---|---:|---:|---:|---:|---:|---|
| Uniform QAM | PMF project cố định | — | 8.0000 | 2.6471 | 0.15339 | 0.003906/0.003906 | Không |
| Maxwell–Boltzmann QAM | PMF project cố định | — | 6.4089 | 11.2994 | 0.31692 | \(4.14\times10^{-7}\)/0.03030 | Không |
| Binomial QAM | PMF project cố định | — | 5.9998 | 15.0000 | 0.36515 | \(9.31\times10^{-10}\)/0.03857 | Không |
| GS | `best_gs.pt` | 100 / GS | 8.0000 | 2.7032 | 0.13469 | uniform | Không; geometry chung |
| PS | `best_ps.pt` | 0 / PS | 6.4089 | 11.2994 | 0.31692 | như MB | Không; trùng MB |
| PS+GS | `best_joint.pt` | 70 / geometry warm-up | 6.4089 | 11.2083 | 0.30749 | như MB | Không trong checkpoint được chọn |

Nguồn số: [`scheme_shape_statistics.csv`](sweep_audit/scheme_shape_statistics.csv), được tính từ đúng ba checkpoint trong config. `maximum_PMF_change_over_probe_T` và `maximum_geometry_change_over_probe_T` đều bằng 0 trên dải probe \(T=10^{-6}\)–0.5. Điều này phù hợp với code: PS epoch-zero có weight cuối bằng 0 và bias bằng log PMF khởi tạo; joint warm-up dùng `geometry_warmup_probability_lr=0`.

Hệ quả quan trọng:

- PS không “tăng entropy”; nó dùng MB với entropy thấp hơn Uniform và giảm xác suất dùng điểm biên. Vì chuẩn hóa năng lượng theo PMF, peak coordinate energy lại lớn hơn Uniform.
- Binomial tập trung hơn MB, có entropy thấp hơn và peak lớn hơn; trong mọi sweep nó hơi kém MB.
- Joint giữ nguyên entropy/PMF của MB, giảm peak khoảng 0.8% nhưng cũng giảm \(d_{\min}\) khoảng 3.0%. Gain joint không thể quy hoàn toàn cho peak hoặc minimum distance.

### 2.3 Trung bình, repetition và CI

- Mỗi điểm có 5 repetition với seed `[302026, 303026, 304026, 305026, 306026]`, 256 fading samples/repetition và 128 AWGN samples/symbol; \(n_{\rm cut}=150\).
- Các scheme dùng common channel/AWGN samples **tại cùng điểm và repetition**, nên phép so sánh đúng là paired difference.
- `ci95_low/high` trong `skr_parameter_sweep_summary.csv` là CI Student-\(t\) hai phía 95% của \(K_+\), không phải normal CI.
- Các điểm x khác nhau dùng `channel_seed = base_seed + sweep_offset + point_index*10000`; vì vậy channel Monte Carlo không được giữ chung giữa các giá trị tham số.
- Năm sweep chính có kiểm tra \(n_{\rm cut}=120\) so với 150, max \(|\Delta K_{\rm raw}|=7.85\times10^{-15}\) bit/symbol. Sweep distance đã ghi đủ 630 hàng và hình, nhưng bước kiểm tra phụ cuối cùng thất bại do `chi_BE=NaN`; xem [`skr_distance_gpu_stderr.log`](../skr_distance_gpu_stderr.log). Kết luận distance vì vậy có độ chắc chắn thấp hơn.

## 3. Bảng kết quả tổng hợp

| Parameter | Xu hướng SKR quan sát | Scheme tốt nhất | Miền shaping có lợi | Giao cắt/ngưỡng | Cơ chế qua \(I_{AB},\chi_{BE}\) | Độ chắc chắn |
|---|---|---|---|---|---|---|
| \(a\) | Tăng đơn điệu | PS+GS; MB=PS sát sau | Toàn 0.10–0.30 m | Không | \(\beta I_{AB}\uparrow\) mạnh hơn \(\chi_{BE}\uparrow\); shaping gain do \(\chi_{BE}\downarrow\) so với Uniform | Cao cho evaluation seed; vừa cho tối ưu |
| \(V\) | Tăng đơn điệu rất mạnh | PS+GS | Toàn 5–40 km; absolute gain lớn ở V cao | Chỉ MB/PS giả ở 5.47 km | Cả \(I_{AB}\) và \(\chi_{BE}\) tăng theo T; phần MI tăng trội | Cao/vừa |
| \(W_0\) | Tăng rồi gần bão hòa, có wiggle | PS+GS | Toàn miền | Không có giao cắt có nghĩa | T và hai thành phần tăng; wiggle đồng bộ giữa 6 scheme do sampling | Vừa |
| \(C_n^2\) | Giảm đơn điệu | PS+GS | Toàn \(10^{-16}\)–\(10^{-14}\) | Không | \(I_{AB}\downarrow\) nhanh; \(\chi_{BE}\downarrow\) chỉ bù một phần | Cao/vừa |
| \(\xi\) | Giảm tổng thể, có dao động | PS+GS | Toàn 0–0.01 SNU | Không | Endpoint: \(\beta I_{AB}\downarrow\) nhẹ và \(\chi_{BE}\uparrow\) mạnh; Holevo chi phối | Vừa do channel samples thay giữa x |
| \(L\) | Sụt rất nhanh về gần 0 | PS+GS | Toàn miền; PS/MB mở rộng miền khóa | Uniform 52.27 km; GS 59.36 km | \(I_{AB}\downarrow\) nhanh hơn mức giảm \(\chi_{BE}\) | Vừa-thấp ở tail |

Nguồn: [`point_summary_with_channel.csv`](sweep_audit/point_summary_with_channel.csv), [`paired_delta_decomposition.csv`](sweep_audit/paired_delta_decomposition.csv), [`findings.json`](sweep_audit/findings.json) và sáu hình PNG cùng thư mục với CSV gốc.

## 4. Phân tích chi tiết từng tham số

### 4.1 Receiver aperture radius \(a\)

Nguồn: [`skr_vs_aperture_radius.csv`](../skr_parameter_sweep_results/skr_vs_aperture_radius.csv), các cột `I_AB`, `chi_BE`, `K_raw`, `K_positive`; hình [`skr_vs_aperture_radius.png`](../skr_parameter_sweep_results/skr_vs_aperture_radius.png).

Khi \(a\) tăng 0.10→0.30 m, reconstructed mean \(T\) tăng 0.02104→0.10316. Với PS+GS, \(I_{AB}\) tăng 0.029756→0.140876, \(\chi_{BE}\) cũng tăng 0.020531→0.093911, và

\[
\Delta K=+0.032185
=\underbrace{+0.105564}_{0.95\Delta I_{AB}}
+\underbrace{(-0.073379)}_{-\Delta\chi_{BE}}.
\]

Vì vậy SKR tăng không phải do Eve term giảm; cả Bob và Holevo tăng theo coupling, nhưng phần MI tăng nhanh hơn.

Thứ hạng không đổi: PS+GS > MB=PS > Binomial > GS > Uniform. Gain raw trên toàn miền:

- PS−Uniform: 0.00503–0.02151 bit/symbol.
- GS−Uniform: 0.000376–0.001566.
- joint−PS: \(1.20\times10^{-5}\)–\(5.40\times10^{-5}\).

Tại baseline \(a=0.20\), PS hơn Uniform 0.014831 (130.64%); decomposition là \(+2.68\times10^{-5}\) từ \(0.95\Delta I_{AB}\) và \(+0.014804\) từ \(-\Delta\chi_{BE}\). GS hơn Uniform 0.001083 (9.54%) gần như hoàn toàn nhờ \(\chi_{BE}\). Joint hơn PS \(3.662\times10^{-5}\) (0.140%), CI ghép cặp 95% \([3.469,3.855]\times10^{-5}\), cũng hoàn toàn do \(\chi_{BE}\) giảm.

Không có giao cắt, ngưỡng 0 hay phi đơn điệu trong mean curve. Cả năm loại gain trên bảng audit có CI ghép cặp dương tại 21/21 điểm. Kết luận một câu: **khẩu độ lớn cải thiện phần cứng mạnh hơn mọi gain GS, còn MB/PS chủ yếu cải thiện security term trên toàn miền.**

### 4.2 Atmospheric visibility \(V\)

Nguồn: [`skr_vs_visibility.csv`](../skr_parameter_sweep_results/skr_vs_visibility.csv); hình [`skr_vs_visibility.png`](../skr_parameter_sweep_results/skr_vs_visibility.png).

Visibility 5→40 km làm suy hao Kruse giảm; mean \(T\) tăng 0.002044→0.310974. Với PS+GS:

\[
I_{AB}:0.002946\to0.376494,\quad
\chi_{BE}:0.002067\to0.207453,
\]
\[
\Delta K=+0.149485
=+0.354871-0.205386.
\]

Đây là sweep có dynamic range SKR lớn nhất trong miền đã chọn. Absolute PS−Uniform gain tăng từ 0.000651 đến 0.06350; GS−Uniform từ \(5.01\times10^{-5}\) đến 0.004386; joint−PS từ \(1.45\times10^{-6}\) đến \(1.691\times10^{-4}\). Relative gain ở \(V=5\) km không được dùng vì Uniform chỉ \(7.87\times10^{-5}\), quá gần 0.

Thứ hạng vật lý vẫn cố định. Audit nội suy một giao cắt MB/PS tại 5.47 km, nhưng max \(|K_{\rm PS}-K_{\rm MB}|=2.35\times10^{-14}\); đây chỉ là round-off giữa hai artifact đồng nhất, không phải chuyển miền tối ưu.

Không thấy bão hòa hoàn toàn đến 40 km, dù độ lợi biên của atmospheric attenuation giảm ở visibility cao. Cả 21/21 paired CI của joint−PS, PS−Uniform và GS−Uniform đều dương. Kết luận: **visibility là đòn bẩy tổng thể mạnh nhất trên dải khảo sát; shaping bù được một phần nhưng không thay thế cải thiện suy hao khí quyển.**

### 4.3 Transmitter beam waist \(W_0\)

Nguồn: [`skr_vs_beam_waist.csv`](../skr_parameter_sweep_results/skr_vs_beam_waist.csv); hình [`skr_vs_beam_waist.png`](../skr_parameter_sweep_results/skr_vs_beam_waist.png).

Trong code, \(W_L=W_0\sqrt{1+(L/z_R)^2}\), \(z_R=\pi W_0^2/\lambda\), đồng thời \(\sigma_{\rm turb}^2\propto(2W_0)^{-1/3}\). Trên dải 0.03→0.12 m, mean \(T\) tăng tổng thể 0.04145→0.07868 và endpoint PS+GS:

\[
\Delta K=+0.014919=+0.047470-0.032551.
\]

Các đường tăng nhanh đến khoảng 0.08–0.09 m rồi phẳng hơn. Tuy nhiên các local maxima/minima ở 0.0795, 0.084, 0.093, 0.102, 0.1065 và 0.1155 m xuất hiện đồng bộ ở gần như mọi scheme và đi cùng 5/20 bước mean \(T\) đảo chiều. Vì channel seed đổi theo điểm, đây có xác suất cao là Monte Carlo wiggle trên một xu hướng bão hòa, không đủ chứng minh một \(W_0^\star\) nội tại. Điểm cuối 0.12 m vẫn có mean K lớn nhất cho cả sáu scheme.

Gain raw: PS−Uniform 0.00957–0.01684; GS−Uniform 0.000707–0.001222; joint−PS \(2.30\times10^{-5}\)–\(4.17\times10^{-5}\). Tại điểm gần baseline nhất \(W_0=0.0615\) m, PS gain 130.65%, GS 9.57%, joint−PS 0.140%; gain joint do \(\chi_{BE}\) giảm \(3.633\times10^{-5}\), còn \(0.95\Delta I_{AB}=1.17\times10^{-8}\).

Kết luận: **beam waist cho thấy lợi ích phần cứng rõ và dấu hiệu diminishing returns, nhưng chưa có bằng chứng thống kê cho cực đại nội miền.**

### 4.4 Turbulence \(C_n^2\)

Nguồn: [`skr_vs_turbulence.csv`](../skr_parameter_sweep_results/skr_vs_turbulence.csv); hình [`skr_vs_turbulence.png`](../skr_parameter_sweep_results/skr_vs_turbulence.png).

Tăng \(C_n^2\) từ \(10^{-16}\) lên \(10^{-14}\) m\(^{-2/3}\) làm mean \(T\) giảm 0.10180→0.01465. Với PS+GS:

\[
\Delta K=-0.033721
=\underbrace{-0.113195}_{0.95\Delta I_{AB}}
+\underbrace{+0.079474}_{-\Delta\chi_{BE}}.
\]

Ở đây \(\chi_{BE}\) **giảm** khi kênh xấu hơn, nhưng không đủ bù việc \(I_{AB}\) mất mạnh. Do đó không được giải thích SKR giảm bằng “\(\chi_{BE}\uparrow\)”; cơ chế đúng là Bob mất thông tin nhanh hơn mức Eve term giảm.

Thứ hạng giữ nguyên. PS−Uniform gain 0.00331–0.02140, GS−Uniform \(2.43\times10^{-4}\)–0.001555, joint−PS \(8.04\times10^{-6}\)–\(5.34\times10^{-5}\). Tại baseline \(10^{-15}\), PS gain 131.67%, GS 9.61%, joint 0.140%. Tất cả mean curves đơn điệu và paired CI gain dương 21/21.

Kết luận: **shaping tạo khoảng đệm tương đối nhưng không đảo được suy giảm do beam wandering; turbulence là suy hao vật lý mà modulation chỉ bù một phần.**

### 4.5 Excess noise \(\xi\)

Nguồn: [`skr_vs_excess_noise.csv`](../skr_parameter_sweep_results/skr_vs_excess_noise.csv); hình [`skr_vs_excess_noise.png`](../skr_parameter_sweep_results/skr_vs_excess_noise.png).

Về mô hình, \(\xi\) không thay đổi \(T\). Tuy nhiên mean \(T\) tái tạo dao động 0.06610–0.07037 giữa các điểm do channel seed khác nhau. So endpoint 0→0.01 SNU cho PS+GS:

\[
\Delta K=-0.004768
=\underbrace{-0.000331}_{0.95\Delta I_{AB}}
+\underbrace{-0.004437}_{-\Delta\chi_{BE}}.
\]

Khoảng 93% độ giảm endpoint đến từ \(\chi_{BE}\) tăng; MI giảm nhẹ. Uniform nhạy hơn nhiều vì Holevo tăng mạnh: raw K giảm 0.01412→0.00237, trong khi PS+GS chỉ giảm 0.02599→0.02122.

Các đỉnh/đáy nhỏ tại 0.0005/0.0015, 0.003/0.0035, 0.007/0.0075 và 0.0085/0.009 SNU không nên xem là hiệu ứng vật lý: chúng đồng bộ giữa MB, Binomial, PS và joint và đi cùng thay đổi channel sample. Xu hướng bao là giảm. Tại baseline 0.001, PS−Uniform = 0.014619 (130.47%), GS−Uniform = 0.001070 (9.55%), joint−PS = \(3.616\times10^{-5}\) (0.140%); decomposition joint là \(-2.07\times10^{-9}\) từ MI và \(+3.616\times10^{-5}\) từ Holevo.

Kết luận: **MB/PS bền hơn Uniform trước excess noise trong active model, nhưng local slope quanh baseline hiện bị confound bởi việc không tái sử dụng cùng channel samples giữa các mức \(\xi\).**

### 4.6 Slant distance \(L\)

Nguồn: [`skr_vs_distance.csv`](../skr_distance_sweep_results_gpu/skr_vs_distance.csv); hình [`skr_vs_distance.png`](../skr_distance_sweep_results_gpu/skr_vs_distance.png); stderr [`skr_distance_gpu_stderr.log`](../skr_distance_gpu_stderr.log).

Distance 20→100 km làm mean \(T\) giảm từ 0.06827 xuống \(4.28\times10^{-7}\). Với PS+GS:

\[
\Delta K=-0.0260538
=-0.0895887+0.0635349.
\]

Giống turbulence, cả \(I_{AB}\) và \(\chi_{BE}\) giảm, nhưng MI giảm nhanh hơn. K+ trên hình làm Uniform/GS trông bằng 0 ở tail; raw CSV cho thấy chúng khác nhau:

| \(L\) | Uniform \(K_{\rm raw}\) | GS | MB=PS | PS+GS |
|---:|---:|---:|---:|---:|
| 52 km | \(1.76\times10^{-7}\) | \(8.51\times10^{-6}\) | \(1.071\times10^{-4}\) | \(1.074\times10^{-4}\) |
| 60 km | \(-3.23\times10^{-6}\) | \(-4.29\times10^{-7}\) | \(3.252\times10^{-5}\) | \(3.260\times10^{-5}\) |
| 100 km | \(-8.43\times10^{-8}\) | \(-6.56\times10^{-8}\) | \(1.492\times10^{-7}\) | \(1.497\times10^{-7}\) |

Nội suy mean curve cho ngưỡng Uniform 52.27 km trong bracket 52–56 km và GS 59.36 km trong bracket 56–60 km. Root từng repetition cho CI đã nêu ở tóm tắt. Như vậy GS dịch ngưỡng khoảng 7.0 km so với Uniform; MB/PS và joint không cắt 0 trong miền. Không nên ngoại suy ngưỡng của chúng vượt 100 km vì giá trị tail rất nhỏ và auxiliary ncut check đã gặp NaN.

Raw Uniform đạt cực tiểu khoảng 60 km rồi tiến dần về 0 từ phía âm; GS tương tự với cực tiểu khoảng 68 km. Đây là hành vi tiệm cận/sàn số của \(K_{\rm raw}\) khi cả MI và Holevo cùng về 0, không phải “kênh phục hồi”. Giao cắt MB/PS nội suy 30.40 km lại chỉ là round-off.

Kết luận: **distance là tham số phá hủy khóa mạnh nhất quanh baseline; probabilistic baseline mở rộng miền raw-positive rõ rệt, nhưng tail 100 km chưa đủ vững để tuyên bố hoạt động thực tế.**

## 5. Cơ chế của PS, GS và PS+GS

### 5.1 PS/MB

Tại test baseline trong [`comparison.csv`](../experiments/joint_seed2026/comparison.csv):

- Uniform: \(I_{AB}=0.0943422\), \(\chi_{BE}=0.0784224\), \(K=0.0112027\).
- MB/PS: \(I_{AB}=0.0943171\), \(\chi_{BE}=0.0636732\), \(K=0.0259281\).

PS thực ra làm \(I_{AB}\) giảm \(2.51\times10^{-5}\), nhưng giảm \(\chi_{BE}\) \(1.4749\times10^{-2}\), nên gain ròng \(1.4725\times10^{-2}\). PMF MB giảm tần suất dùng các điểm outer-energy cao; entropy giảm 8→6.4089 bit. Dữ liệu chứng minh security-covariance gain trong mô hình, không chứng minh entropy tăng hay MI tăng.

### 5.2 GS

GS so với Uniform tại cùng test:

\[
0.95\Delta I_{AB}\approx 2.0\times10^{-7},\qquad
-\Delta\chi_{BE}\approx 1.0792\times10^{-3}.
\]

GS làm \(w\) giảm 0.02654→0.02409, \(Z\) tăng 0.69090→0.69155 và \(\mathrm{Tr}C\) tăng 1.40200→1.40316; Holevo giảm. Đồng thời peak tăng và \(d_{\min}\) giảm. Vì vậy giải thích “GS tăng minimum distance/giảm peak” bị artifact bác bỏ. Có thể geometry đã hội tụ theo objective covariance/Holevo thay vì các proxy hình học; cũng có thể regularizer và learning rate cho nghiệm chưa tối ưu. Phần đầu được dữ liệu hỗ trợ, phần sau chỉ là giả thuyết.

### 5.3 PS+GS

Joint so với PS tại test:

\[
\Delta K=+3.6407\times10^{-5}
=0.95(-5.34\times10^{-8})-(-3.6457\times10^{-5}).
\]

MI xấu đi không đáng kể; \(\chi_{BE}\) giảm tạo toàn bộ gain. Peak giảm 11.2994→11.2083 nhưng \(d_{\min}\) cũng giảm 0.31692→0.30749. PMF và entropy không đổi. Joint vượt PS tại mọi điểm và paired evaluation CI dương, nhưng:

- absolute gain rất nhỏ;
- checkpoint đến từ warm-up, không phải joint-finetune;
- chỉ có một training seed;
- PS itself là epoch-zero MB.

Do đó kết luận đúng là: **một perturbation geometry nhỏ trên MB cho gain Holevo nhất quán trong phép đánh giá cố định**, chưa phải “joint learning bổ sung lợi ích tổng quát”.

## 6. Các trường hợp đặc biệt

| Hiện tượng | Vị trí | Scheme | Quan sát | Nguyên nhân khả dĩ | Kiểm tra bổ sung |
|---|---:|---|---|---|---|
| PS trùng MB | Toàn bộ 126 điểm | MB, PS | max \(|\Delta K|=2.35\times10^{-14}\) | PS checkpoint epoch 0, bias khởi tạo MB | Huấn luyện nhiều seed; yêu cầu checkpoint sau epoch 0 thắng validation |
| “Giao cắt” giả | \(V\approx5.47\) km; \(L\approx30.40\) km | MB, PS | Đổi thứ tự ở mức round-off | Sai số số học | Gộp MB=PS khi \(|\Delta K|<\) tolerance |
| Joint gain nhỏ | Toàn miền | PS+GS, PS | 0.14% quanh baseline; paired CI dương | \(\chi_{BE}\) giảm nhẹ do geometry | Independent training seeds, practical tolerance |
| GS proxy hình học xấu hơn | Mọi sweep | GS, Uniform | peak cao hơn, \(d_{\min}\) thấp hơn nhưng K cao hơn | Objective covariance/Holevo, không phải distance proxy | Ablation \(\lambda_{\rm sep},\lambda_{\rm peak},\lambda_{\rm drift}\) |
| Wiggle excess noise | Nhiều điểm 0–0.01 SNU | Tất cả | Dao động đồng bộ; expected trend vẫn giảm | Channel samples đổi giữa x | Giữ nguyên `channel_seed` theo repetition trên toàn sweep |
| Wiggle/bão hòa beam waist | \(W_0\gtrsim0.08\) m | Tất cả | Local extrema nhưng endpoint vẫn cao nhất | Diminishing returns + Monte Carlo | Dense sweep với common random numbers giữa x |
| Ngưỡng khóa | 52.27/59.36 km | Uniform/GS | \(K_{\rm raw}\) đổi dấu | MI suy giảm nhanh hơn Holevo | Dày điểm 50–62 km; báo raw và clipped |
| Raw âm nhưng plot bằng 0 | Distance tail | Uniform, GS | Hai đường K+ cùng 0 dù raw khác | Clipping theo instantaneous sample | Vẽ panel \(K_{\rm raw}\), log-\(|K|\) có dấu |
| Tail raw “phục hồi” về 0 | 60–100 km | Uniform; 68–100 km GS | Raw bớt âm khi T→0 | Cả MI và Holevo cùng tiến 0; sàn số | Precision/ncut/covariance-stability study |
| Distance validation failure | Auxiliary ncut check | Uniform | `chi_BE=NaN` | Numerical covariance/eigenvalue issue ở probe | Lưu probe seeds; tăng stabilization và kiểm tra ncut |

## 7. Ý nghĩa thống kê

### Được phân biệt trên evaluation seed

- PS−Uniform, GS−Uniform, PS+GS−Uniform, joint−PS và joint−GS có paired Student-\(t\) CI 95% dương tại 21/21 điểm của cả sáu sweep trong audit raw-K.
- Ngưỡng Uniform và GS ở distance xuất hiện trong cả 5/5 repetition, với root spread nhỏ hơn spacing 4 km.
- Xếp hạng MB/PS trên Binomial và GS trên Uniform ổn định tại mọi mean point.

### Có xu hướng nhưng chưa chắc về tối ưu

- Joint hơn PS nhất quán trên evaluation samples, nhưng chỉ một joint training seed và gain nhỏ. CI hiện tại đo Monte Carlo evaluation, không đo “nếu huấn luyện lại”.
- Wiggle của beam waist/excess noise nằm trong một pipeline dùng channel samples khác giữa x; không thể dùng CI tại từng điểm để chứng minh cực trị của hàm vật lý.

### Không phân biệt có ý nghĩa

- MB và PS là cùng một nghiệm; mọi đổi hạng giữa chúng là sai số máy.
- Các đường mean có ordinary CI chồng lấn không tự động nghĩa là bằng nhau; common-random-number paired CI mới là kiểm định phù hợp. Ngược lại, paired CI nhỏ không loại bỏ model bias hoặc training uncertainty.

Nguồn CI và decomposition: [`paired_delta_decomposition.csv`](sweep_audit/paired_delta_decomposition.csv); root: [`threshold_roots_by_repetition.csv`](sweep_audit/threshold_roots_by_repetition.csv).

## 8. Gain tuyệt đối, tương đối và đảo baseline

Tại baseline hoặc điểm grid gần nhất:

| Sweep point | \(\Delta K_{\rm PS-U}\) | Relative | \(\Delta K_{\rm GS-U}\) | Relative | \(\Delta K_{\rm joint-PS}\) | Relative to PS |
|---|---:|---:|---:|---:|---:|---:|
| \(a=0.20\) m | 0.014831 | 130.64% | 0.001083 | 9.54% | \(3.662\times10^{-5}\) | 0.140% |
| \(V=10.25\) km | 0.015515 | 128.05% | 0.001131 | 9.34% | \(3.840\times10^{-5}\) | 0.139% |
| \(W_0=0.0615\) m | 0.014680 | 130.65% | 0.001075 | 9.57% | \(3.635\times10^{-5}\) | 0.140% |
| \(C_n^2=10^{-15}\) | 0.014514 | 131.67% | 0.001060 | 9.61% | \(3.580\times10^{-5}\) | 0.140% |
| \(\xi=0.001\) SNU | 0.014619 | 130.47% | 0.001070 | 9.55% | \(3.616\times10^{-5}\) | 0.140% |
| \(L=20\) km | 0.014756 | 131.04% | 0.001076 | 9.56% | \(3.640\times10^{-5}\) | 0.140% |

Không dùng relative gain ở low-visibility hoặc distance tail vì Uniform gần 0. Ở đó metric đúng là absolute gain và threshold shift.

Không quan sát:

- Uniform > MB;
- Binomial > MB;
- fixed baseline > PS/MB;
- GS > PS;
- PS > PS+GS

ở bất kỳ mean point có ý nghĩa nào. Trường hợp “PS tốt hơn/nhỏ hơn MB” chỉ là round-off của cùng PMF.

## 9. Xếp hạng độ nhạy

Dùng elasticity cục bộ của PS+GS

\[
S_x=\frac{x}{K}\frac{dK}{dx}
\]

từ hai grid points kề baseline; distance dùng đạo hàm một phía vì baseline ở biên. Kết quả:

| Sweep | \(S_x\) quanh baseline | \((K_{\max}-K_{\min})/|K_{\rm baseline}|\) | Diễn giải |
|---|---:|---:|---|
| Distance | -2.665 | 1.000 | Nhạy cục bộ nhất; có ngưỡng khóa |
| Visibility | +2.239 | 5.705 | Dynamic range lớn nhất |
| Aperture | +1.626 | 1.228 | Nhạy mạnh |
| Beam waist | +0.395 | 0.571 | Nhạy vừa, gần bão hòa |
| Turbulence | -0.399 | 1.319 | Local elasticity vừa nhưng hai decade tạo biến đổi lớn |
| Excess noise | +0.031 tại baseline | 0.195 | Dấu local bị Monte Carlo confound; endpoint trend là âm |

Nguồn: [`sensitivity_summary.csv`](sweep_audit/sensitivity_summary.csv). Xếp hạng theo bốn tiêu chí:

1. Toàn miền: visibility > turbulence ≈ aperture > distance > beam waist > excess noise, nhưng phụ thuộc miền do người dùng chọn.
2. Dịch ngưỡng: distance là sweep duy nhất đo được; GS mở rộng khoảng 7 km, MB/PS ít nhất đến biên 100 km.
3. Đổi hạng scheme: không có đổi hạng vật lý trong cả sáu sweep.
4. Cục bộ quanh baseline: distance > visibility > aperture > beam waist ≈ turbulence; excess-noise chưa ước lượng tin cậy.

## 10. Câu chuyện khoa học chung

Kênh làm suy giảm khóa theo hai kiểu. Khi coupling tốt lên nhờ aperture, visibility hoặc beam waist, cả \(I_{AB}\) lẫn \(\chi_{BE}\) đều tăng; SKR tăng vì \(0.95I_{AB}\) tăng nhanh hơn Holevo. Khi turbulence hoặc distance tăng, cả hai cùng giảm về 0; SKR giảm vì Bob mất mutual information nhanh hơn phần “bù” do Holevo giảm. Excess noise khác về bản chất: nó không đổi \(T\), làm MI giảm nhẹ và Holevo tăng, nên \(\chi_{BE}\) chi phối độ giảm.

Trong active artifact, probabilistic shaping hữu ích nhất không phải bằng cách tăng \(I_{AB}\), mà bằng cách thay đổi ensemble/density-matrix correlation để giảm \(\chi_{BE}\). PMF MB giảm xác suất sử dụng điểm outer-energy cao và hạ entropy. Binomial tập trung quá mạnh hơn nữa nhưng kém MB một chút, cho thấy “shaping mạnh hơn” không đồng nghĩa “khóa cao hơn”.

GS đơn lẻ tạo gain nhỏ hơn nhiều PS. Các proxy hình học truyền thống trong artifact—peak energy và \(d_{\min}\)—thậm chí xấu hơn Uniform; gain đến từ thay đổi \(w,Z,\mathrm{Tr}C\) và Holevo. Vì vậy GS có vai trò tinh chỉnh security covariance trong một vùng SNR, không phải cứu một kênh có coupling đã sụp.

Joint shaping chỉ tạo gain bổ sung nhỏ khi geometry được perturb trên nền MB. Vì checkpoint tốt nhất ở warm-up với PMF frozen, dữ liệu chưa chứng minh synergy của hai optimizer. Câu chuyện được dữ liệu hỗ trợ là “MB + geometry correction nhỏ”, không phải một policy PS+GS thích nghi theo kênh.

Khi visibility thấp, turbulence lớn hoặc distance dài, cải thiện phần cứng/kênh quan trọng hơn modulation. Aperture, alignment, beam control và atmospheric path cải thiện \(T\) theo bậc lớn; shaping chỉ tạo khoảng đệm hoặc dịch ngưỡng. Một chiến lược triển khai hợp lý từ dữ liệu hiện tại là chọn MB cố định làm baseline mạnh, chỉ thêm GS nếu chi phí phức tạp được biện minh bởi gain tuyệt đối nhỏ; chưa có cơ sở cho policy chọn scheme theo miền vì thứ hạng không đổi.

## 11. Cảnh báo mô hình bắt buộc

- Active evaluation dùng `T_samples`, không dùng `T_samples_with_optics`. Trong config hiện tại optical factors đều 1, nhưng pipeline vẫn chưa tích hợp một loss chain riêng.
- \(\eta=0.95\) và electronic noise \(0.001\) SNU chỉ được ghi lại; không có detector term riêng trong MI/Holevo đang chạy.
- \(\beta=0.95\) cố định.
- Kết quả là asymptotic raw SKR/Holevo covariance bound; không có finite-key correction hay composable security proof.
- Mô hình kiến trúc giả định bên phát biết \([\log_{10}T,\xi,\mathrm{SNR}]\). Tuy nhiên checkpoint được chọn không thật sự dùng dependence này vì PMF/geometry output tĩnh.
- GS là geometry chung. Về nguyên tắc PS+GS normalization theo PMF có thể làm physical geometry gián tiếp phụ thuộc \(T\); trong checkpoint hiện tại PMF tĩnh nên hiệu ứng đó bằng 0.
- Gumbel–Softmax chỉ là tùy chọn forward; direct SKR objective dùng exact 256-symbol enumeration và không bật Gumbel.
- Code không đủ để gán chắc homodyne hay heterodyne cho phép đo; báo cáo không giả định loại đo.
- MI là Monte Carlo AWGN; density-matrix/Holevo có Fock cutoff và eigenvalue stabilization.
- CI đánh giá không sửa model bias, không bao phủ hyperparameter/training seed, và không biến gain nhỏ thành ưu thế cơ bản.

## 12. Kết luận có thể bảo vệ

### Được dữ liệu hỗ trợ rõ ràng

- Sáu artifact đúng là Uniform, MB, Binomial, GS, PS, PS+GS; Binomial không phải Rayleigh.
- MB=PS và vượt Uniform trong toàn bộ grid; gain chủ yếu do \(\chi_{BE}\) thấp hơn.
- GS vượt Uniform nhưng gain nhỏ, cũng do \(\chi_{BE}\).
- PS+GS vượt PS ở mọi evaluation point; absolute gain nhỏ và do Holevo.
- Aperture/visibility tăng làm SKR tăng; turbulence/distance tăng làm SKR giảm; excess noise có xu hướng giảm.
- Uniform và GS mất raw key lần lượt quanh 52.3 và 59.4 km trong sweep distance.

### Chỉ là xu hướng, cần thêm kiểm chứng

- Beam-waist bão hòa khoảng 0.08–0.12 m nhưng vị trí optimum chưa xác định.
- Joint geometry có thể tạo gain thực sự ngoài training seed 2026.
- MB/PS có thể duy trì khóa hữu dụng gần 100 km; hiện raw K quá nhỏ và distance ncut probe bị lỗi.
- Excess-noise local sensitivity; hiện channel Monte Carlo thay đổi theo điểm.

### Không được phép kết luận từ dữ liệu hiện tại

- Learned PS thích nghi PMF theo trạng thái kênh.
- Joint PS+GS tối ưu đồng thời tốt hơn PS trong nghĩa tổng quát.
- GS thắng nhờ tăng \(d_{\min}\) hoặc giảm peak.
- Detector/optical efficiency đã được tính đầy đủ.
- Kết quả có finite-key/composable security.
- Một scheme AI luôn tốt nhất hoặc gain sẽ lặp lại khi huấn luyện seed khác.
- Wiggle nhỏ là quy luật vật lý hay một optimum chính xác.

## 13. Thí nghiệm bổ sung ưu tiên

1. **Training uncertainty:** chạy ít nhất 5–10 independent training seeds cho PS, GS và joint; báo paired test gain theo training seed. Yêu cầu PS checkpoint sau epoch 0 thực sự thắng MB trước khi gọi là learned PS.
2. **Common samples giữa x:** với mỗi repetition, tái sử dụng cùng base Rayleigh uniforms/AWGN tensor trên toàn sweep, đặc biệt cho excess noise và beam waist. Điều này cho phép ước lượng local derivative sạch.
3. **Distance threshold:** tăng mật độ 0.5–1 km trong 48–64 km; vẽ cả mean \(K_{\rm raw}\), \(K_+\), outage probability và root theo repetition.
4. **Distance numerical audit:** tái hiện đúng seed gây `chi_BE=NaN`, kiểm tra eigenvalues/covariance stabilization và hội tụ \(n_{\rm cut}=120,150,180,200\).
5. **PS adaptation audit:** lưu entropy, \(p_{\min},p_{\max}\), KL divergence với MB và heatmap PMF tại mỗi point. So checkpoint cố định với retraining/fine-tuning tại từng điều kiện.
6. **Joint ablation:** PS-preserving initialization; geometry warm-up off/on; \(\lambda_{\rm sep},\lambda_{\rm peak},\lambda_{\rm drift}\) sweep; learning-rate PS/GS riêng; tăng sample/epoch budget.
7. **Mechanism audit:** xuất \(w,Z,\mathrm{Tr}C,I_{AB},\chi_{BE}\) theo từng điểm cho cả sáu scheme để xác minh trực tiếp cơ chế Holevo.
8. **Physical completeness:** thêm detector efficiency, electronic noise và optical loss vào active MI/Holevo path; sau đó chạy lại sáu sweep.
9. **Security relevance:** thêm finite-size/finite-key correction và báo blocks needed; không chỉ asymptotic \(K_{\rm raw}\).
10. **Practical significance:** đặt ngưỡng gain tối thiểu theo throughput/complexity để đánh giá liệu joint gain 0.14% có đáng triển khai.
