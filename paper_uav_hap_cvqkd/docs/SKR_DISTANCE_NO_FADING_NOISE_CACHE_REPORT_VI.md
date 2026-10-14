# Vẽ lại SKR theo khoảng cách với mô hình bỏ phương sai fading

Chọn điểm tốt nhất trong cache đã xác thực tại mỗi L, theo yêu cầu người dùng. Giữ ba màu và bố cục log10 của hình gốc.

Cache: 227 ensemble, gồm 30 Uniform và 197 MB. 26 khoảng cách cũ, 78 điểm chọn; 5902 đánh giá hợp lệ, 0 đánh giá không đạt guard được ghi riêng.
Fixed MB giữ nguyên nu_raw=0.2, VA=1.3833230302980657 và đúng ensemble/hash cũ. Các tham số của hai đường tối ưu được chọn riêng ở mỗi L trong ngân hàng cache hữu hạn; không phải nghiệm AO liên tục.

Tính lại Eq. (10), luật PDF vật lý chuẩn hóa và ba mômen tại từng khoảng cách bằng producer hiện hành. T_eff=mean_sqrt_eta², xi_eff=0.0186, N_eff=T_eff*xi_ch; b=1+T_eff(VA+xi_ch), Z*=2sqrt(T_eff)C-sqrt(2T_eff*xi_ch*w). Ideal heterodyne R=1, xi_det=0, chi_het=1; beta=0.95; phase/adaptive optics OFF.
MI discrete 256-QAM tính mới GH8/16/32, Holevo tại direct Z_star; cùng ensemble/noise ở hai nhánh. C,w đọc nguyên từ cache; không AP, AO, source generation, Monte Carlo hay nội suy C,w/SKR.

Tại L=21.9393102292 km: MB tốt nhất (nu,VA)=(0.17,5.046875), K=0.058734859879005397; khớp kết quả continuation đã lưu.
Uniform trên log10: cuối dương=24.0 km; điểm đầu không dương=25.0 km. Giữ nguyên signed K trong CSV, không vẽ K<=0 lên log và không nối qua điểm không dương.

Đây là xấp xỉ Gaussian bỏ phương sai fading, chưa là security lower bound của kênh fading. Optimized trên hình chỉ có nghĩa best in validated cache; không chứng nhận tối ưu liên tục/toàn cục. Frozen model và lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.

Files: [PNG](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme_log10.png), [PDF](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme_log10.pdf), [CSV](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme.csv).
