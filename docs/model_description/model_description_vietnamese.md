# 2.X. Mô hình tối ưu chòm sao lấy cảm hứng từ Autoencoder cho hệ thống UAV–HAP CV-QKD

## 2.X.1. Mô hình hệ thống tổng quát

Đường thực thi chính của thí nghiệm là `uav_hap_joint_ps_gs.py`. Hệ thống xét điều chế rời rạc \(M=256\), trong đó chỉ số symbol được sắp theo thứ tự \(i=16k+l\), \(k,l\in\{0,\ldots,15\}\). Mã nguồn không tạo chuỗi bit, không định nghĩa phép gán nhãn Gray và không huấn luyện bộ giải điều chế bit. Do đó, đại lượng \(\log_2M=8\) chỉ là giới hạn entropy của nguồn symbol, không phải bằng chứng về một ánh xạ bit cụ thể.

Với trạng thái kênh có độ truyền qua tức thời \(T\) và nhiễu dư \(\epsilon\), bộ phát xác định phân phối \(\mathbf p(T,\epsilon)=[p_0,\ldots,p_{255}]\) và tập biên độ coherent phức \(\boldsymbol\alpha=[\alpha_0,\ldots,\alpha_{255}]\). Kênh cổ điển dùng để tính thông tin tương hỗ là

\[
Y=\sqrt{T}\,\alpha_S+N,\qquad
N\sim\mathcal{CN}(0,\sigma_c^2),\qquad
\sigma_c^2=1+\frac{T\epsilon}{2}.
\]

Đây là **khung tối ưu hóa đầu cuối lấy cảm hứng từ Autoencoder**, không phải autoencoder cổ điển có encoder và decoder nơ-ron. Thành phần nơ-ron duy nhất là mạng sinh logit xác suất ở bộ phát. \(I_{AB}\) được tích phân Monte Carlo bằng mật độ AWGN và \(\chi_{BE}\) được tính từ ma trận mật độ/covariance; không tồn tại mạng bộ thu học hậu nghiệm symbol hoặc bit.

Luồng phụ thuộc đã kiểm chứng là: cấu hình JSON/CLI \(\rightarrow\) mẫu \(T\) của kênh UAV–HAP \(\rightarrow\) đặc trưng trạng thái kênh \(\rightarrow\) xác suất symbol và tọa độ chòm sao \(\rightarrow\) chuẩn hóa có trọng số và đặt \(V_A\) \(\rightarrow\) \(I_{AB}\) và \(\chi_{BE}\) \(\rightarrow\) \(K_{\rm raw}\) \(\rightarrow\) lan truyền ngược, xác thực và checkpoint.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 37–53 và 3329–3502: các phụ thuộc và đường thực thi chính.
- `uav_hap_joint_ps_gs.py`, dòng 56–60 và 285–360: (M=256), đặc trưng kênh và đầu ra mô hình.
- `uav_hap_joint_ps_gs.py`, dòng 389–475: mô hình (Y\mid S,T) và phép tính (I_{AB}).

## 2.X.2. Biểu diễn nguồn symbol và chòm sao tín hiệu

Tập symbol là (\mathcal S=\{0,1,\ldots,255\}). Chòm sao QAM vuông ban đầu được xây dựng bởi

\[
\alpha^{(0)}_{k,l}=\frac{\alpha_0}{\sqrt{30}}
\big[(k-7.5)+\mathrm j(l-7.5)\big],
\quad \alpha_0=\sqrt{12/17}.
\]

Trong mô hình học, mỗi điểm thô được lưu bằng hai tọa độ thực,

\[
\mathbf c_i^{\rm raw}=[I_i,Q_i]^{\mathsf T},\qquad
c_i^{\rm raw}=I_i+\mathrm jQ_i.
\]

Trước mọi phép tính vật lý, chòm sao được lấy tâm theo phân phối đang hoạt động,

\[
\mu=\sum_i p_i c_i^{\rm raw},\qquad
\bar c_i=c_i^{\rm raw}-\mu,
\]

và chuẩn hóa năng lượng có trọng số,

\[
x_i=\frac{\bar c_i}{\sqrt{\sum_jp_j|\bar c_j|^2}},
\qquad \sum_i p_i x_i=0,
\qquad \sum_i p_i|x_i|^2=1.
\]

Biên độ coherent dùng trong (I_{AB}) và Holevo là

\[
\alpha_i=\sqrt{\frac{V_A}{2}}x_i,
\qquad 2\sum_i p_i|\alpha_i|^2=V_A.
\]

Cấu hình đầy đủ đặt (V_A=2). Chuẩn hóa phụ thuộc đồng thời vào xác suất và hình học, không tách gradient, nên cả PS lẫn GS đều nhận gradient qua phép đặt tâm và co giãn.

**Nguồn triển khai:**

- `uav_hap_1/zstar/base.py`, dòng 8–14: QAM (16\times16) và thứ tự (16k+l).
- `uav_hap_1/config.py`, dòng 21–34: (M), (\alpha_0), (\beta), (\epsilon) và các mặc định.
- `uav_hap_joint_ps_gs.py`, dòng 128–185 và 339–345: chuyển tọa độ, đặt tâm, chuẩn hóa và đặt (V_A).
- `test_uav_hap_joint_ps_gs.py`, dòng 18–36: kiểm thử tâm, năng lượng và gradient.

## 2.X.3. Tạo dạng xác suất

Mạng phân phối nhận véc-tơ trạng thái kênh

\[
\mathbf f(T,\epsilon)=
\left[\log_{10}T,\;\epsilon,\;10\log_{10}
\left(\frac{TV_A}{1+T\epsilon/2}\right)\right]^{\mathsf T}
\]

và thực hiện ánh xạ `Linear(3,128)–ReLU–Linear(128,256)`. Logit (\ell_i) bị chặn trong ([-30,30]) theo mặc định, sau đó

\[
p_i(T,\epsilon)=\frac{e^{\ell_i}}{\sum_je^{\ell_j}}.
\]

`probabilities_safe=max(p_i,10^{-12})` chỉ bảo vệ logarithm; nó không được tái chuẩn hóa và không thay thế phân phối dùng trong kỳ vọng. Trọng số lớp cuối được khởi tạo bằng không, còn bias bằng (\log p_i^{(0)}), vì vậy phân phối ban đầu độc lập trạng thái kênh nhưng có thể trở thành thích nghi theo (T,\epsilon) trong huấn luyện.

Các phân phối cố định gồm:

\[
p^{\rm U}_{k,l}=\frac1{256},
\]

\[
p^{\rm MB}_{k,l}=
\frac{\exp[-\tilde\nu(k-7.5)^2]\exp[-\tilde\nu(l-7.5)^2]}
{\sum_{r,s}\exp[-\tilde\nu(r-7.5)^2]\exp[-\tilde\nu(s-7.5)^2]},
\quad \tilde\nu=0.1,
\]

và baseline nhị thức

\[
p^{\rm Bin}_{k,l}=\frac{\binom{15}{k}\binom{15}{l}}{2^{30}}.
\]

Không có “phân phối xác suất symbol Rayleigh” trong đường thực thi. Hàm Rayleigh xuất hiện ở mô hình kênh để lấy mẫu độ lệch tâm chùm (r), hoàn toàn khác với PMF symbol nhị thức. Đây là một xung đột giữa yêu cầu thuật ngữ và mã nguồn; tài liệu sử dụng định nghĩa của mã nguồn.

**Bảng 1. So sánh sáu phương án được đánh giá trong pipeline sweep**

| Scheme | Symbol probability | Constellation geometry | Trainable probability | Trainable geometry | Initialization | Objective |
|---|---|---|---:|---:|---|---|
| Uniform QAM | (1/256) | QAM vuông | Không | Không | QAM dự án | Chỉ đánh giá |
| Maxwell–Boltzmann QAM | PMF MB, (\tilde\nu=0.1) | QAM vuông, tái chuẩn hóa theo PMF | Không | Không | Công thức cố định | Chỉ đánh giá |
| Binomial QAM | (\binom{15}{k}\binom{15}{l}/2^{30}) | QAM vuông, tái chuẩn hóa theo PMF | Không | Không | Công thức cố định | Chỉ đánh giá |
| GS | Đều | Học | Không | Có | QAM vuông | Cực đại (K_{\rm raw}) có regularization |
| PS | Mạng softmax theo trạng thái kênh | QAM cố định | Có | Không | Đều hoặc MB; mặc định MB | Cực đại (K_{\rm raw}) |
| PS+GS | Mạng softmax theo trạng thái kênh | Học | Có | Có | PS, GS, combined hoặc PS-preserving | Cực đại (K_{\rm raw}) có regularization |

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 137–146 và 220–235: PMF cố định và khởi tạo mạng logit.
- `uav_hap_joint_ps_gs.py`, dòng 285–337: đặc trưng, clipping và softmax.
- `uav_hap_1/zstar/base.py`, dòng 17–38: PMF nhị thức, đều và MB.
- `visualize_skr_parameter_sweeps.py`, dòng 1–7, 35–42 và 309–329: sáu phương án thực tế và phân biệt Rayleigh.

## 2.X.4. Tạo dạng hình học

`raw_constellation` là một `Parameter` kích thước (256\times2). Ở chế độ PS nó bị đóng băng và đường tiến sử dụng `base_qam`; ở GS và joint nó được cập nhật. Cấu hình mặc định áp đặt đối xứng bốn phần tư. Mỗi điểm lấy trị tuyệt đối của một trong 64 prototype phần tư thứ nhất rồi nhân dấu tương ứng để giữ thứ tự (16k+l). Vì toàn bộ tensor vẫn có `requires_grad=True`, bộ đếm tham số báo 512 số thực, nhưng chỉ 64 cặp prototype được đọc hiệu dụng khi dùng đối xứng bốn phần tư.

Mã không có regularization đối xứng riêng vì đối xứng được áp đặt cấu trúc. Không có ràng buộc PAPR tường minh. Các cơ chế ổn định hình học được triển khai là

\[
\mathcal L_{\rm sep}=\frac{1}{B M(M-1)}
\sum_{b}\sum_{i\ne j}
\exp\left(-\frac{|x_{b,i}-x_{b,j}|^2}{d_0^2}\right),
\]

\[
\mathcal L_{\rm peak}=\frac1{BM}\sum_{b,i}
\left[\max(|x_{b,i}|^2-n_{\max},0)\right]^2,
\]

\[
\mathcal L_{\rm drift}=\frac1{BM}\sum_{b,i}|x_{b,i}-x_i^{(0)}|^2,
\]

với (d_0=0.15), (n_{\max}=5). Ngoài ra, một bước cập nhật bị hủy nếu khoảng cách cặp tối thiểu không vượt (10^{-6}), entropy nhỏ hơn (0.25) bit hoặc năng lượng symbol cực đại đạt từ 100 trở lên.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 237–283 và 298–306: lưu tọa độ, đóng băng theo mode và đối xứng.
- `uav_hap_joint_ps_gs.py`, dòng 642–677: các regularizer separation, peak, drift và entropy.
- `uav_hap_joint_ps_gs.py`, dòng 1583–1603: điều kiện hợp lệ và phục hồi cập nhật.
- `uav_hap_joint_ps_gs.py`, dòng 3166–3179: ngưỡng mặc định.

## 2.X.5. Học đồng thời PS và GS

PS+GS kết hợp cùng một (\mathbf p(T,\epsilon)) và một hình học thô; phép chuẩn hóa có trọng số khiến tọa độ vật lý phụ thuộc cả hai nhóm tham số. Bốn ứng viên epoch 0 được đánh giá: `ps`, `gs`, `combined` và `ps_preserving`. Ứng viên PS-preserving sao chép mạng phân phối và hình học cố định từ mô hình PS; mã kiểm tra đồng nhất xác suất, tọa độ vật lý, (I_{AB}) và (\chi_{BE}) với sai số tuyệt đối (10^{-11}). Vì thế PS là một trường hợp khả thi của không gian joint tại khởi tạo này. Điều đó chỉ chứng minh quan hệ không gian khả thi, không bảo đảm thuật toán joint luôn tìm được nghiệm tốt hơn PS.

Chiến lược mặc định là cập nhật đồng thời hai nhóm. Tùy chọn `alternating` xóa gradient hình học trong các bước PS và xóa gradient PS mỗi bước hình học; chu kỳ mặc định gồm ba bước PS cho một bước hình học. Trong cấu hình đầy đủ, learning rate chính là (10^{-3}) cho xác suất và (10^{-4}) cho tọa độ; refinement dùng lần lượt (10^{-4}) và (10^{-5}).

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 1203–1224: nhóm tham số và optimizer.
- `uav_hap_joint_ps_gs.py`, dòng 1552–1563: cập nhật đồng thời hoặc luân phiên.
- `uav_hap_joint_ps_gs.py`, dòng 1774–1929: bốn khởi tạo và kiểm tra PS-preserving.
- `test_uav_hap_joint_ps_gs.py`, dòng 38–64: PS là trường hợp đặc biệt chính xác.

## 2.X.6. Cơ chế lấy mẫu Gumbel–Softmax

Lớp mô hình có thể tạo one-hot cứng theo Gumbel–Softmax với straight-through estimator qua `torch.nn.functional.gumbel_softmax(..., hard=True)`. Về mặt toán học, phép này tương ứng

\[
g_i=-\log[-\log U_i],\quad U_i\sim\mathcal U(0,1),\qquad
\widetilde s_i=\frac{\exp[(\ell_i+g_i)/\tau]}
{\sum_j\exp[(\ell_j+g_j)/\tau]},
\]

và one-hot ở đường tiến được ghép với gradient của mẫu mềm ở đường lùi. Nhiệt độ có lịch hình học từ 1.0 xuống 0.1.

Tuy nhiên, đường huấn luyện nhiều giai đoạn đang hoạt động (`train_phase`) gọi mô hình mà không bật `use_gumbel`; kể cả trainer cũ có bật tùy chọn này, `gumbel_symbols` cũng không được dùng trong (I_{AB}), (\chi_{BE}) hoặc hàm mất mát. Vì vậy, gradient PS thực tế truyền trực tiếp qua softmax và phép liệt kê chính xác 256 symbol. Không được mô tả Gumbel–Softmax như cơ chế tối ưu đang chi phối kết quả hiện tại.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 308–360 và 364–368: API Gumbel cứng và lịch nhiệt độ.
- `uav_hap_joint_ps_gs.py`, dòng 827–919: trainer cũ tạo nhưng không dùng `gumbel_symbols` trong loss.
- `uav_hap_joint_ps_gs.py`, dòng 1477–1530: đường huấn luyện hiện hành liệt kê symbol trực tiếp.
- `uav_hap_joint_ps_gs.py`, dòng 3181–3183: cờ CLI mặc định tắt.

## 2.X.7. Mô hình kênh UAV–HAP

Khoảng cách liên kết là (L=\sqrt{d_h^2+(H_{\rm HAP}-H_{\rm UAV})^2}) nếu có khoảng cách ngang; nếu không, (L=(H_{\rm HAP}-H_{\rm UAV})/\cos\theta). Baseline dùng (H_{\rm UAV}=0), (H_{\rm HAP}=20\,000\) m, (d_h=0) và (\theta=0).

Suy hao khí quyển Kruse được tính bằng

\[
\xi=\frac{3.912}{V}\left(\frac{\lambda_{\rm nm}}{550}\right)^{-q(V)},
\qquad \eta_{\rm atm}=\exp(-\xi L_{\rm km}),
\]

với (q=1.6) khi (V>50) km, (q=1.3) khi (6<V\le50) km, và (q=0.585V^{1/3}) nếu không. Bán kính chùm Gaussian ở bộ thu là

\[
z_R=\frac{\pi W_0^2}{\lambda},\qquad
W_L=W_0\sqrt{1+(L/z_R)^2}.
\]

Tổn hao hình học và pointing được tính số qua các tham số (T_0,\Gamma,R) chứa hàm Bessel sửa đổi (I_0,I_1); công thức đầy đủ được liệt kê trong `model_equations.md`. Phương sai lệch tâm gồm

\[
\sigma_r^2=\sigma_{\rm turb}^2+\sigma_{\rm UAV}^2,
\]

\[
\sigma_{\rm UAV}^2=\sigma_x^2+\sigma_y^2+\sigma_z^2
+a^2(\sigma_\theta^2+\sigma_\phi^2+\sigma_\psi^2),
\]

và, ở đường baseline không dùng Hufnagel–Valley,

\[
\sigma_{\rm turb}^2=1.919\,C_n^2L^3(2W_0)^{-1/3}.
\]

Mã lấy (r\sim\mathrm{Rayleigh}(\sigma_r/\sqrt2)), rồi

\[
\eta_{\rm point}=T_0^2\exp[-(r/R)^\Gamma],\qquad
T=\eta_{\rm atm}\eta_{\rm point}.
\]

Rayleigh ở đây là fading do beam displacement. Không có fading Rayleigh của biên độ symbol, không có scintillation log-normal độc lập và không có AWGN trong hàm `channel`; AWGN chỉ được thêm trong mô-đun (I_{AB}). Nhiễu dư (\epsilon) đi vào cả phương sai AWGN và covariance Holevo. `eta_SMF`, (T_T), (T_R) được tính thành `T_samples_with_optics`, nhưng pipeline PS–GS dùng `T_samples`, vì vậy các tổn hao quang cố định này không đi vào đường chính. Các mặc định detector (\eta=0.95), (v_{el}=0.001) được nhập nhưng không dùng trong (I_{AB})/Holevo dịch sang PyTorch.

**Nguồn triển khai:**

- `uav_hap_1/config.py`, dòng 37–104: Kruse, hình học, turbulence, jitter và quang học.
- `uav_hap_1/channel/channel_model.py`, dòng 10–47: (L), góc zenith, khí quyển và nhiễu xạ.
- `uav_hap_1/channel/channel_model.py`, dòng 50–122: tham số aperture/pointing và phương sai beam wandering.
- `uav_hap_1/channel/channel_model.py`, dòng 125–199: lấy mẫu Rayleigh và (T).
- `uav_hap_joint_ps_gs.py`, dòng 1992–2046 và 3336–3348: pipeline dùng `T_samples`.

## 2.X.8. Thông tin tương hỗ và thông tin Holevo

### Thông tin tương hỗ

Mã liệt kê chính xác symbol phát và chỉ lấy mẫu AWGN đối xứng (antithetic). Với (\mu_i=\sqrt T\alpha_i), mẫu (y_{i,n}=\mu_i+n_{i,n}), entropy (H(S)=-\sum_ip_i\log_2p_i), ước lượng là

\[
\widehat I_{AB}=H(S)+\sum_i p_i\frac1{N_A}\sum_{n=1}^{N_A}
\log_2\frac{p_i\exp[-|y_{i,n}-\mu_i|^2/\sigma_c^2]}
{\sum_jp_j\exp[-|y_{i,n}-\mu_j|^2/\sigma_c^2]}.
\]

Đây là tích phân Monte Carlo AWGN với tổng symbol chính xác, không phải biểu thức Gaussian-input giải tích và không phải đầu ra của mạng bộ thu. Chunking 64 ứng viên chỉ giảm bộ nhớ, không thay đổi phép toán.

### Thông tin Holevo

Với trạng thái coherent cắt tại (n_{\rm cut}),

\[
|\alpha_i\rangle\approx e^{-|\alpha_i|^2/2}
\sum_{n=0}^{n_{\rm cut}-1}\frac{\alpha_i^n}{\sqrt{n!}}|n\rangle,
\qquad
\tau=\sum_ip_i|\alpha_i\rangle\langle\alpha_i|.
\]

Sau phân rã riêng Hermitian, trị riêng không vượt (10^{-12}) bị loại trong (\tau^{1/2}) và giả nghịch đảo (\tau^{-1/2}). Mã tính

\[
\operatorname{Tr}C=\operatorname{Tr}(\tau^{1/2}a\tau^{1/2}a^\dagger),
\]

\[
w=\sum_ip_i\left(\langle\alpha_i|a_\tau^\dagger a_\tau|\alpha_i\rangle
-|\langle\alpha_i|a_\tau|\alpha_i\rangle|^2\right),
\quad a_\tau=\tau^{1/2}a\tau^{-1/2},
\]

\[
Z_{\rm raw}=2\sqrt T\operatorname{Tr}C-\sqrt{2T\epsilon w}.
\]

(Z) được chặn trên bởi (sqrt{ab}(1-10^{-9})), với (a=V_A+1), (b=1+TV_A+T\epsilon). Từ covariance (\Gamma_{AB}=\begin{bmatrix}aI_2&Z\sigma_z\\Z\sigma_z&bI_2\end{bmatrix}), mã tính ba trị riêng symplectic (\lambda_1,\lambda_2,\lambda_3) và

\[
\chi_{BE}=g\!\left(\frac{\lambda_1-1}{2}\right)
+g\!\left(\frac{\lambda_2-1}{2}\right)
-g\!\left(\frac{\lambda_3-1}{2}\right),
\]

trong đó (g(x)=(x+1)\log_2(x+1)-x\log_2x). Vì (\tau,\operatorname{Tr}C,w,Z) đều được dựng từ (p_i,\alpha_i) bằng PyTorch complex128, (\chi_{BE}) khả vi theo cả PS và GS.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 371–475: lấy mẫu AWGN và (I_{AB}).
- `uav_hap_joint_ps_gs.py`, dòng 478–639: trạng thái coherent, ma trận mật độ, covariance và Holevo.
- `uav_hap_1/zstar/base.py`, dòng 41–151: phương trình NumPy/SciPy tham chiếu và (I_{AB}) Gaussian cũ.
- `test_uav_hap_joint_ps_gs.py`, dòng 123–146 và 189–206: gradient Holevo và tính hữu hạn tại (n_{\rm cut}=150).

## 2.X.9. Hàm mục tiêu tốc độ khóa bí mật

Đại lượng tối ưu và tiêu chí checkpoint là

\[
K_{\rm raw}=\beta I_{AB}-\chi_{BE},\qquad \beta=0.95.
\]

Hàm mất mát trung bình trên batch fading là

\[
\mathcal L=-\mathbb E[K_{\rm raw}]
+\lambda_{\rm sep}\mathcal L_{\rm sep}
+\lambda_{\rm peak}\mathcal L_{\rm peak}
+\lambda_{\rm drift}\mathcal L_{\rm drift}
+\lambda_{\rm ent}\mathcal L_{\rm ent},
\]

\[
\mathcal L_{\rm ent}=\frac1B\sum_b[\max(H_{\min}-H(\mathbf p_b),0)]^2.
\]

Cấu hình đầy đủ đặt ba trọng số hình học bằng (10^{-3}), (H_{\min}=5) bit nhưng (\lambda_{\rm ent}=0); do đó entropy penalty được tính song không đóng góp vào gradient tổng. (K_{\rm raw}) không bị clip khi huấn luyện hoặc chọn checkpoint. Chỉ số báo cáo bổ sung là

\[
K_+=\max(0,K_{\rm raw}).
\]

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 642–685: hàm mất mát hoàn chỉnh.
- `uav_hap_joint_ps_gs.py`, dòng 722–768: (K_{\rm raw}) và (K_+).
- `uav_hap_joint_ps_gs.py`, dòng 1099–1142: tiêu chí checkpoint ưu tiên raw SKR.
- `ps_gs_full_config.json`, dòng 40–44: trọng số regularization.

## 2.X.10. Quy trình huấn luyện nhiều giai đoạn

Pipeline joint chạy PS-only và GS-only độc lập, đánh giá bốn khởi tạo joint, rồi chạy geometry warm-up, joint fine-tuning và refinement. Bảng sau mô tả cấu hình đầy đủ.

**Bảng 3. Các giai đoạn huấn luyện**

| Stage | Trainable parameters | Frozen parameters | Learning rate | Objective | Checkpoint criterion |
|---|---|---|---|---|---|
| PS-only, 200 epoch | Mạng phân phối | Hình học QAM | (10^{-3}) | (-K_{\rm raw}); regularizer hình học bằng 0 | Raw SKR xác thực |
| GS-only, 100 epoch | Tọa độ | Mạng phân phối; PMF đều | (10^{-4}) | (-K_{\rm raw})+regularization ramp | Raw SKR xác thực |
| Geometry warm-up, 100 epoch | Tọa độ | Mạng xác suất do LR (=0) | hình học (10^{-4}) | (-K_{\rm raw}); regularization ramp 0→0.25 | So với best joint hiện có |
| Joint fine-tuning, 300 epoch | Mạng xác suất và tọa độ | Không | (10^{-3}), (10^{-4}) | (-K_{\rm raw}); regularization ramp 0→1 | Raw SKR xác thực |
| Full-(n_{\rm cut}) refinement, 100 epoch | Cả hai | Không | (10^{-4}), (10^{-5}) | Như trên, (n_{\rm cut}=150), nhiều mẫu hơn | Raw SKR xác thực |

Optimizer là AdamW với weight decay (10^{-6}) trong cấu hình đầy đủ (Adam ở cấu hình nhanh). `ReduceLROnPlateau` tối đa hóa raw SKR, giảm learning rate một nửa sau số lần chờ bằng một phần tư patience và không thấp hơn (10^{-8}). Gradient được clip theo norm 1.0. Regularization hình học tăng tuyến tính theo epoch; geometry warm-up kết thúc ở 0.25, fine-tuning kết thúc ở 1.0, refinement giữ 1.0.

Mỗi epoch sinh lại pool fading bằng seed xác định và chỉ lấy một batch con; AWGN cũng được sinh độc lập theo epoch. Xác thực dùng tập (T) và tensor AWGN cố định. Early stopping xảy ra sau 40 lần xác thực không cải thiện trong cấu hình đầy đủ. Nếu loss, gradient, ma trận bảo mật hoặc hình học không hợp lệ, mô hình phục hồi trạng thái trước bước cập nhật và giảm một nửa learning rate; quá năm lỗi thì dừng bằng exception.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 1361–1717: vòng huấn luyện, sampling, clip, recovery, scheduler và early stopping.
- `uav_hap_joint_ps_gs.py`, dòng 3243–3310: đặc tả năm giai đoạn.
- `uav_hap_joint_ps_gs.py`, dòng 3425–3494: thứ tự pipeline.
- `ps_gs_full_config.json`, dòng 8–44: epoch, learning rate, sample budget và regularization.

## 2.X.11. Đánh giá, checkpoint và khả năng tái lập

Trước cập nhật đầu tiên của mỗi phase, mô hình được đánh giá tại epoch 0 và lưu checkpoint. Epoch 0 tham gia cạnh tranh với mọi epoch sau; vì vậy một cập nhật hình học làm giảm raw SKR không thể ghi đè nghiệm khởi tạo tốt hơn. Cơ chế này đặc biệt quan trọng với PS+GS: checkpoint PS-preserving bảo toàn chính xác kết quả PS trước mọi cập nhật hình học và giữ PS trong tập nghiệm ứng viên thực nghiệm.

Xếp hạng checkpoint lần lượt dùng raw SKR lớn hơn, (I_{AB}) lớn hơn, (\chi_{BE}) nhỏ hơn, peak energy nhỏ hơn và khoảng cách cặp tối thiểu lớn hơn. Checkpoint chứa model, optimizer, scheduler, cấu hình, thời gian, xác suất/tọa độ chuẩn hóa và trạng thái RNG Python, NumPy, Torch CPU/CUDA. Resume phục hồi các trạng thái này và tiếp tục từ epoch kế tiếp.

Tập train/validation/test dùng seed kênh lần lượt `seed+101`, `seed+202`, `seed+303`; mã xác nhận ba tensor không trùng. Đánh giá bất định tạo lại mẫu kênh và AWGN độc lập theo từng run, báo trung bình, độ lệch chuẩn mẫu và khoảng (\bar x\pm1.96s/\sqrt R). Sweep sáu phương án dùng Student-(t) cho khoảng tin cậy; đây là khác biệt giữa hai script. Kiểm tra hội tụ (n_{\rm cut}), gradient sai phân hữu hạn và tính xác định fixed-seed được chạy sau huấn luyện trừ khi bị tắt.

Kết quả nhanh đã lưu cho thấy PS+GS không vượt PS trong run rút gọn; chính báo cáo đánh dấu đây không phải bằng chứng hội tụ. Không thể suy rộng kết quả này thành kết luận vật lý hoặc thống kê phổ quát.

**Nguồn triển khai:**

- `uav_hap_joint_ps_gs.py`, dòng 1058–1200: lưu/khôi phục RNG và checkpoint.
- `uav_hap_joint_ps_gs.py`, dòng 1393–1471 và 1719–1753: epoch-zero và chọn final từ best xác thực.
- `uav_hap_joint_ps_gs.py`, dòng 2013–2138: split độc lập và đánh giá lặp seed.
- `test_uav_hap_joint_ps_gs.py`, dòng 66–121: xếp hạng epoch-zero và round-trip checkpoint/RNG.
- `ps_gs_results_fast/experiment_report.txt`, dòng 97–113: quan sát run nhanh và khoảng bất định.

## 2.X.12. Quan hệ với tài liệu tham khảo và tóm tắt

Repository có `paper.pdf`/`paper_text.txt` mang tiêu đề *Satellite-to-Ground Continuous Variable Quantum Key Distribution: The Gaussian and Discrete Modulated Protocols in Low Earth Orbit*, không phải *Joint Learning of Geometric and Probabilistic Constellation Shaping*. Không tìm thấy trích dẫn nội bộ xác nhận rằng mã PS–GS được lấy từ bài báo thứ hai. Vì vậy chỉ có thể nói mô hình có **tương đồng khái niệm** với joint constellation shaping: xác suất có thể học, tọa độ có thể học, chuẩn hóa năng lượng có trọng số và không gian joint chứa các nghiệm shaping đơn. Không thể quy kết nguồn gốc trực tiếp từ mã hiện tại.

Khác với autoencoder truyền thông thường tối đa hóa mutual information hoặc tối thiểu hóa cross-entropy ở decoder, dự án tối đa hóa (\beta I_{AB}-\chi_{BE}), không có receiver neural network, và bổ sung kênh quang UAV–HAP cùng khối bảo mật lượng tử. Gumbel–Softmax chỉ là đầu ra tùy chọn không nối vào objective đang hoạt động.

Tóm lại, triển khai là tối ưu đầu cuối ở bộ phát và khối đánh giá bảo mật: PS học PMF phụ thuộc trạng thái kênh; GS học prototype hình học có đối xứng; joint học cả hai qua (I_{AB}) Monte Carlo và (\chi_{BE}) khả vi. Khung joint có miền khả thi rộng hơn về lý thuyết và có tiềm năng vượt PS hoặc GS khi được tối ưu đủ tốt, nhưng mọi khẳng định gain phải dựa trên nhiều seed huấn luyện, đánh giá test độc lập, hội tụ cutoff và khoảng tin cậy.

**Nguồn triển khai:**

- `paper_text.txt`, dòng 4–18: tiêu đề bài báo thực sự có trong repository.
- `uav_hap_joint_ps_gs.py`, dòng 1–13 và 2952–3026: phạm vi thí nghiệm và các quy ước được báo cáo.
- `PS_GS_TRAINING.md`, dòng 168–175: giới hạn diễn giải kết quả joint.

### Luồng kiến trúc dùng cho hình vẽ

Nguồn symbol (S\in\{0,\ldots,255\}) và trạng thái ((T,\epsilon)) → mạng logit xác suất (PS; hoặc PMF cố định) → softmax → chọn toàn bộ 256 symbol bằng phép liệt kê có trọng số, **không lấy mẫu Gumbel trong objective** → tọa độ QAM thô/GS có đối xứng → đặt tâm và chuẩn hóa năng lượng theo (p_i) → (\alpha_i=\sqrt{V_A/2}x_i) → kênh tức thời (Y=\sqrt T\alpha_S+N) cho (I_{AB}), đồng thời ((p_i,\alpha_i,T,\epsilon)) vào khối ma trận mật độ/Holevo → (K_{\rm raw}=\beta I_{AB}-\chi_{BE}) → regularization → lan truyền ngược tới mạng xác suất và/hoặc tọa độ → xác thực và checkpoint.

*Hình X. Kiến trúc tối ưu đầu cuối PS–GS lấy cảm hứng từ Autoencoder cho hệ thống UAV–HAP CV-QKD; đường Gumbel–Softmax là tùy chọn chẩn đoán và không thuộc hàm mục tiêu hiện hành.*
