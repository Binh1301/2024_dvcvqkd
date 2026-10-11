# Quy trình tính SKR HAP–UAV 256-QAM từ đầu đến cuối

## 1. Phạm vi và phiên bản

Tài liệu tái dựng đường thực thi tạo kết quả **theta10/D55 không ràng buộc năng lượng**, dùng MI heterodyne xác định và Holevo trực tiếp tại \(Z_-\). Không có mô phỏng mới. Mốc cố định là checkpoint hoàn tất results/theta10_D55_objective_B_numerical_skr_optimization/b2_P1_lower_refinement/minimal_run/objective_checkpoint.json: **151 nguồn MB, 26 khoảng cách, 3926 giá trị mục tiêu**. Snapshot đọc lúc **2026-10-11T03:51:11.024455+00:00** (10:51:11 UTC+7), branch 10-5-2026, HEAD eec4dd114d9f3ab128f82c37be520dafd197caaa. Hash đầu vào và trạng thái Git ban đầu ở [documentation_snapshot.json](documentation_snapshot.json).

Batch full_51_grid_exact_completion được điều khiển riêng. Không ghép nguồn hay checkpoint đang phát sinh từ batch vào mốc 151 này. “Catalog của tài liệu” không có nghĩa catalog sống mới nhất. Tác vụ chỉ đọc kết quả ổn định, ghi tài liệu trong thư mục mới; AP, SKR, AO, training, final-test và regression khoa học đều **NOT_RUN**.

Tham chiếu path:L dưới đây tương đối với paper_uav_hap_cvqkd/, số dòng ở snapshot. Phân loại phát biểu:

- **DIRECTLY IMPLEMENTED** (DI): công thức hoặc phép toán nằm trực tiếp trong mã nêu.
- **DERIVED FROM IMPLEMENTED EQUATIONS** (DE): biến đổi đại số của mã, không là tính lại số khoa học.
- **DOCUMENTED IN THE MANUSCRIPT** (DM): trong LaTeX kết quả đã lưu hoặc hồ sơ audit bản thảo; không tự chứng minh triển khai.
- **ASSUMED BUT NOT VERIFIED** (AV): giả thiết/khẳng định chưa đủ bằng chứng cho phạm vi này.

Lifecycle vẫn **NOT_READY_FOR_PUBLICATION_SCALE_RUNS**. Hash hiện đọc của docs/FINAL_MODEL_SPEC.md là df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15, khác hash lịch sử 561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1. Bất nhất này được ghi nhận, không sửa và không dùng để cấp quyền chạy. CURRENTLY_VERIFIED_PASS chỉ dành cho kiểm tra tài liệu/hash/số học lưu hiện tại; test cũ không trở thành test vừa chạy.

## 2. Ký hiệu, đơn vị và đường gọi

| Ký hiệu | Định nghĩa |
|---|---|
| \(h_H,h_U,L,\zeta\) | độ cao HAP/UAV, chiều dài link (m), góc thiên đỉnh (rad); bảng dùng \(L_{km}\) |
| \(\lambda,k,w_0,w_L,w_{L,eq},D,r_{ap}\) | bước sóng m; \(k=2\pi/\lambda\) m\(^{-1}\); waist/spot/equivalent spot m; đường kính/bán kính khẩu độ m |
| \(\eta,H_{sc},H_p,B\) | atmospheric transmission, scintillation, pointing power loss, cổng AoA |
| \(v,\sigma_X^2,\sigma_{jt},\chi_p,a_p\) | \(v=\mathrm{Var}(\ln H_{sc})\), \(\sigma_X^2=v/4\), jitter một trục m, \(\chi_p=w_{L,eq}/(2\sigma_{jt})\), \(a_p=\chi_p^2\) |
| \(T_{raw},t\) | truyền qua công suất ngẫu nhiên, \(t=T_{eff}\) scalar |
| \(M,p_i,x_i,\alpha_i,V_A,\bar n\) | số ký hiệu, PMF, tọa độ tương đối, coherent amplitude, modulation variance SNU, photon trung bình |
| \(\nu_{raw},\nu_{repo}\) | MB coefficient trên lưới raw và canonical |
| \(\tau,C,w,\hat a\) | source density operator, source correlation, non-Gaussian penalty, annihilation operator |
| \(\epsilon,\beta,I_{AB},\chi_{BE},K\) | excess noise đầu vào SNU, reconciliation efficiency, MI/Holevo/SKR bits/use |

\(\chi_p\) pointing khác \(\chi_{BE}\); \(a_p\) khác \(\hat a\); source \(C,w\) khác hệ số PDF \(C_1,C_2,C_3\). \(\nu_{aperture}\) khác \(\nu_{raw}\). **Adaptive Optics** (AO quang học) OFF; **Alternating Optimization** (AO thuật toán) đã dùng trong lịch sử tối ưu. \(\tau_{zen}\), phase variance \(\tau_\phi^2\), density \(\tau\) là ba đối tượng khác nhau.

Đường thực thi đã đối chiếu:

1. scripts/run_theta10_D55_unconstrained_three_scheme.py:99, unconstrained_config, đọc configs/default.yaml rồi override \(\tau_{zen}=0.92\) và bỏ v_min/v_max/budget/peak.
2. channel_row ở :262 gọi scripts/run_uniform_beam_waist_diagnostic.py:76, _channel_row; gọi derive_physical_inputs và closed_form_channel_moments ở scripts/calculate_channel_pdf_and_moments.py:55,426.
3. make_ensemble/candidate_from_payload ở runner D55:109,140 tạo cùng PMF/amplitudes và tra nguồn exact.
4. scripts/run_skr_vs_link_distance_theta10urad.py:153, evaluate_candidate, nhận source/channel; MI GH8 product; Holevo maximize_full_interval=False; trừ K.
5. scripts/run_theta10_D55_alt_opt.py:97,238,464 cung cấp ExactObjective, tìm một chiều và P1/P2; scripts/run_theta10_D55_alt_opt_distance_sweep.py:128,422 cung cấp sweep/warm start.
6. scripts/analyze_theta10_D55_near_optimal_skr.py:83 kiểm tra nguồn/context; scripts/export_theta10_D55_all_exact_skr_points.py:19 phân loại objective đã lưu.

ExactMBEvaluator.source_moments được dùng như dịch vụ nguồn. **Không** nhầm với ExactMBEvaluator.__call__ ở scripts/run_exact_mb_test2.py:293: đường ấy dùng MI Monte Carlo và có thể có phase noise. D10cm, legacy Kruse smoke, dense-Fock và full-\(Z\) là các đường khác.

## 3. Tham số vật lý và hình học

**DI**, từ default, overrides runner và config trong identity checkpoint:

| Tham số | Giá trị thực dùng |
|---|---|
| \(h_H,h_U\) | 20000 m, 1000 m |
| \(\lambda,\theta_{div}\) toàn phần | \(1.55\times10^{-6}\) m, \(10^{-5}\) rad |
| \(w_0=2\lambda/(\pi\theta_{div})\) | 0.0986760647169751 m |
| \(D,r_{ap},R_c\) | 0.55 m, 0.275 m, curvature \(+\infty\) |
| \(\tau_{zen}\) | 0.92, override; default có null |
| \(v_w,C_g\) | HV wind 21 m/s, ground coefficient \(10^{-14}\) m\(^{-2/3}\) |
| \(\sigma_h,\theta_{jt},\rho\) | 1 m, \(15.61\times10^{-6}\) rad theo một trục, boresight 0 m |
| \(\sigma_o,\theta_{FOV}\) | \(1.5\times10^{-3}\), \(6.25\times10^{-3}\) rad |
| \(\sigma_{turb,AoA}^2\) | 0 rad² |
| \(\epsilon_{ch},\beta\) | 0.0186 SNU, 0.95 |
| AO quang học, phase noise | OFF, OFF |
| peak/budget/fixed variance bounds | OFF/OFF/không có |

**DI** (_channel_row:83, derive_physical_inputs:78), đặt \(\Delta h=h_H-h_U\):

\[
L=\Delta h/\cos\zeta,\qquad
\zeta(L_{km})=\arccos[\Delta h/(1000L_{km})],\qquad \Delta h=19000\ {\rm m}.
\tag{G1}
\]

L<19 km bị từ chối. Sweep 20–40 km giữ hai độ cao, optics và jitter coefficients; thay \(\zeta,\sec\zeta\), attenuation, scintillation, beam width, equivalent width và displacement \(L\theta_{jt}\). Không tích phân trajectory theo thời gian, không curvature Trái Đất. Góc tham chiếu lưu là 29.99999999997386°, không ép lại 30° để tra cache.

configs/baseline_smoke.json tự ghi legacy_uniform_historical_smoke; configs/exact_tau_oracle_v2_1.yaml là oracle protocol ngưỡng lịch sử, không cấu hình SKR này. Re-freeze \(w_0=0.10\) m ở đầu FINAL_MODEL_SPEC thuộc global-MB experiment riêng; không ghép với waist 0.0986760647169751 m của D55.

## 4. FSO channel

### 4.1. Khí quyển và turbulence

**DI** (src/channel/atmospheric_loss.py:48):

\[
\eta=\tau_{zen}^{\sec\zeta}.
\tag{C1}
\]

\(\tau_{zen}\) được coi là MODTRAN zero-zenith input; code không chạy MODTRAN hay dự báo weather. link_length_m được validate, công thức phụ thuộc L qua \(\zeta\). Visibility/Kruse là legacy.

Đặt h là altitude m, \(v_w\) là wind m/s, \(C_g\) là ground coefficient. **DI** (src/channel/scintillation.py:17,45):

\[
C_n^2(h)=0.00594(v_w/27)^2(10^{-5}h)^{10}e^{-h/1000}
+2.7\,10^{-16}e^{-h/1500}+C_ge^{-h/100}.
\tag{C2}
\]
\[
J_R=\int_{h_U}^{h_H}C_n^2(h)(h-h_U)^{5/6}dh,\quad
\sigma_{R0}^2=2.25k^{7/6}\sec^{11/6}\zeta\,J_R.
\tag{C3}
\]
\[
\Phi_m=\left[\frac{\int_{h_U}^{h_H}C_n^2(h)h^2dh}
{\int_{h_U}^{h_H}C_n^2(h)h^{5/6}dh}\right]^{6/7},\quad
A_{ap}=\left[1+1.11\left(\frac{D^2}{\lambda\Phi_m\sec\zeta}\right)^{7/6}\right]^{-1},
\quad v=A_{ap}\sigma_{R0}^2.
\tag{C4}
\]

Tích phân khẩu độ dùng h, Rytov dùng h−h_U; không tự thay tọa độ. Miền hữu hạn [1000,20000] m; scipy.integrate.quad dùng epsrel=2e-13, limit=300; epsabs=1e-24 cho Rytov/mẫu số, 1e-18 cho tử số. physical trả quad-error fields, optical row không giữ tất cả.

**DI** (calculate_channel_pdf_and_moments.py:210,256), với \(s>0\):

\[
\ln H_{sc}\sim{\cal N}(-v/2,v),\qquad
f_{sc}(s)=\frac{\exp[-(\ln s+v/2)^2/(2v)]}{s\sqrt{2\pi v}}.
\tag{C5}
\]

**DE**: \(E[H_{sc}^q]=e^{(q^2-q)v/2}\); mean=1, sqrt moment=\(e^{-v/8}\). Khẩu độ giảm v và tác động riêng lên finite-aperture coupling.

### 4.2. Spot và pointing

Đặt \(z_R=\pi w_0^2/\lambda,\ d_h=h_H-h_U\), R_c curvature. **DI** (src/channel/pointing_error.py:28,96):

\[
w_L=w_0\sqrt{(1-L/R_c)^2+(L/z_R)^2},\quad
\mu_2=\int_{h_U}^{h_H}C_n^2(h)((h-h_U)/d_h)^{5/3}dh.
\tag{P1}
\]

Với R_c=∞, term focusing=1. Đặt \(\Lambda_b=2L/(kw_L^2)\), \(u_{ap}=\sqrt\pi D/(2\sqrt2w_L)\); code gọi u_ap là nu trong pointing helper:

\[
G_d=4.35\Lambda_b^{5/6}k^{7/6}d_h^{5/6}\sec^{11/6}\zeta\,\mu_2,\quad
w_{L,e}=w_L\sqrt{1+G_d},\quad A_0=\mathrm{erf}(u_{ap})^2.
\tag{P2}
\]
\[
w_{L,eq}^2=\frac{w_{L,e}^2\sqrt\pi\,\mathrm{erf}(u_{ap})}{2u_{ap}e^{-u_{ap}^2}},
\quad \sigma_{jt}^2=\sigma_h^2+L^2\theta_{jt}^2,\quad
\chi_p=w_{L,eq}/(2\sigma_{jt}),\quad a_p=\chi_p^2.
\tag{P3}
\]

mu2 quad: [h_U,h_H], epsabs=1e-18, epsrel=2e-13, limit=300. A0 dùng w_L, equivalent width dùng expanded w_L,e: lựa chọn thực của code. Với \(\rho=0\), displacement hai trục independent Gaussian variance \(\sigma_{jt}^2\); radius r Rayleigh trên [0,∞):

\[
f_r(r)=r\,e^{-r^2/(2\sigma_{jt}^2)}/\sigma_{jt}^2,\quad
H_p=A_0e^{-2r^2/w_{L,eq}^2}.
\tag{P4}
\]

**DE**: \(U=r^2/(2\sigma_{jt}^2)\sim Exp(1)\), \(H_p=A_0e^{-U/a_p}\); Jacobian cho

\[
f_p(u)=a_pu^{a_p-1}/A_0^{a_p},\quad 0<u\le A_0,\qquad
E[H_p^q]=A_0^q a_p/(a_p+q).
\tag{P5}
\]

pointing_pdf:270 dùng generalized form; manuscript branch \(\Gamma=2,R=w_{L,eq}/\sqrt2\) rút về P5. Rician nonzero-boresight có trong diagnostic khác; không phải fixture D55.

### 4.3. AoA và atom tại 0

AoA radius \(\Theta\) Rayleigh scale \(\sigma_o\), miền [0,∞). **DI** (derive_physical_inputs:144):

\[
B={\bf1}_{\Theta\le\theta_{FOV}},\quad
p_{out}=e^{-\theta_{FOV}^2/(2\sigma_o^2)},\quad p_{in}=1-p_{out},\quad
T_{raw}=\eta H_{sc}H_pB.
\tag{A1}
\]

Factorization mômen là **DE** của mô hình independent factors; independence ngoài môi trường là **AV**, không có joint measured fading fit tại mốc này. Outage là atom \(p_{out}\delta_0\), không một giá trị PDF hữu hạn. Với q>0 nó đóng góp 0; mômen nhân p_in. Evaluator nhận một t>0 đã bao gồm p_in trong moments, không đánh giá từng outage realization hoặc nhân p_in lần nữa vào K.

## 5. PDF và fading moments: hai đường phải tách rõ

### 5.1. Raw active product

Đặt \(X=\eta H_{sc}H_p,\ c_0=\eta A_0,\ m=\ln c_0-v/2,\ y=\ln x\), \(Z\sim{\cal N}(0,1)\). **DE**, tương đương kernel với \(\Gamma=2\):

\[
\ln X=m+\sqrt v Z-U/a_p,\quad U\sim Exp(1).
\tag{F1}
\]
\[
f_X(x)=\int_0^{A_0}\frac1{\eta u}f_{sc}(x/(\eta u))f_p(u)du,\quad x>0.
\tag{F2}
\]

Đổi \(U=-a_p\ln(u/A_0)\), convolution trở thành

\[
f_X(x)=\frac1{x\sqrt{2\pi v}}\int_0^\infty e^{-U}
\exp[-(\ln x-m+U/a_p)^2/(2v)]dU.
\tag{F3}
\]

Đây là cận vô hạn của displacement, không đổi cận retained T. Đặt \(S=U/a_p\sim Exp(a_p)\), hoàn bình phương exponent Gaussian-exponential. Dùng
\(\Phi(z)=\tfrac12\mathrm{erfc}(-z/\sqrt2)\),
\(\mathrm{erfc}(z)=2\int_z^\infty e^{-u^2}du/\sqrt\pi\), suy ra

\[
f_Y(y)=a_pe^{a_p(y-m)+a_p^2v/2}
\Phi((m-y)/\sqrt v-a_p\sqrt v),\quad f_X(x)=f_Y(\ln x)/x.
\tag{F4}
\]

**DI** trong scripts/hap_uav_channel_pdf.py:457,487, qua log_ndtr ổn định tail thay gọi erfc trực tiếp. Tệp đó là diagnostic PDF độc lập với scenario riêng: dùng công thức tương đương, không lấy số của scenario ấy cho D55. Generic kernel calculate_channel_pdf_and_moments.py:291,329 dùng Gauss–Laguerre order256 và giữ positive weights; direct convolution dùng quad. Không phải quadrature dùng cho MI.

### 5.2. Retained interval [0,1]

Đặt \(F_1=P(X\le1)\). Config/audit quy định truncated-renormalized active law:

\[
dP_T(t)=p_{out}\delta_0(dt)+p_{in}f_X(t){\bf1}_{0<t\le1}dt/F_1.
\tag{F5}
\]

**DI** tại analyze_product:571 và admitted sampler path, không tạo atom tại 1, không min(X,1). Mômen q>0 của law này:

\[
\mu_q^{[0,1]}=\frac{p_{in}}{F_1}\int_0^1 t^qf_X(t)dt,\qquad
\mu_{T\epsilon}^{[0,1]}=\epsilon\mu_1^{[0,1]}\quad(\epsilon\ {\rm fixed}).
\tag{F6}
\]

Đổi y=ln t giữ cận \(-\infty<y\le0\); Jacobian dt=e^y dy triệt 1/t. Đặt \(J_q=E[X^q{\bf1}_{X\le1}]\). **DI** dạng integral trong _truncated_moment:389; **DE** cách viết rút \(\Gamma=2\):

\[
J_q=c_0^qe^{(q^2-q)v/2}\int_0^\infty
e^{-(1+q/a_p)U}
\Phi\left(\frac{-\ln c_0+U/a_p+v/2-qv}{\sqrt v}\right)dU.
\tag{F7}
\]

CDF trong F7 vẫn áp điều kiện X≤1. quad dùng epsabs2e-13/epsrel2e-12/limit300; log_cdf<−745 trả 0 tránh underflow. \(F_1=J_0\); analyze_product thực lấy F1=1−tail. Diagnostic closed PDF dùng exponential tilting (**DI**, hap_uav_channel_pdf.py:525):

\[
J_q=c_0^qe^{(q^2-q)v/2}\frac{a_p}{a_p+q}F_{Y'}(0),\quad
Y'=m+qv+\sqrt vZ-S',\quad S'\sim Exp(a_p+q).
\tag{F8}
\]

**DE** của survival implementation (:470):

\[
F_Y(y)=\Phi((y-m)/\sqrt v)
+e^{a_p(y-m)+a_p^2v/2}\Phi((m-y)/\sqrt v-a_p\sqrt v).
\tag{F9}
\]

Do đó \(\langle T\rangle,\langle\sqrt T\rangle,\langle T\epsilon\rangle\) retained là \(p_{in}J_1/F_1,p_{in}J_{1/2}/F_1,\epsilon p_{in}J_1/F_1\). F1/tail/Jq cho cấu hình D55 chưa có trong checkpoint tham chiếu: **NOT RECORDED**, không chạy lại để điền.

### 5.3. Mômen thực tạo SKR D55

**DI** (closed_form_channel_moments:461), \(\rho=0\):

\[
\mu_1=p_{in}c_0\frac{a_p}{a_p+1},\quad
\mu_{1/2}=p_{in}\sqrt{c_0}\frac{a_p}{a_p+1/2}e^{-v/8},\quad
\mu_{T\epsilon}=\epsilon\mu_1,\quad t=\mu_{1/2}^2.
\tag{F10}
\]

**DE**: F10 tương ứng **untruncated** moments

\[
\mu_q=p_{in}\int_0^\infty x^qf_X(x)dx
=p_{in}c_0^qe^{(q^2-q)v/2}\frac{a_p}{a_p+q}.
\tag{F11}
\]

F10 thiếu factor \(F_{Y'}(0)/F_1\) của retained law. Helper không gọi _truncated_moment/analyze_product, không tính F1. Đây là **bất nhất**, không mô tả F10 là integral [0,1] chính xác và không tự sửa kết quả bằng F6. Lognormal có tail >1 về toán học khi v>0; chưa có tail/error bound hash-bound tại mốc D55 để kết luận tác động SKR nhỏ bao nhiêu.

Helper còn có rho corrections: \(\mu_1\) nhân \(e^{\rho^2(1-a_p)/(2\sigma_{jt}^2a_p^2)}\), \(\mu_{1/2}\) nhân \(e^{\rho^2(1-2a_p)/(8\sigma_{jt}^2a_p^2)}\). **DI**, nhưng rho=0 ở đây; không tuyên bố chúng là exact general Rician moments đã kiểm chứng.

## 6. Effective channel và noise

**DI** (evaluate_candidate:155, mutual_information.py:396):

\[
t=\langle\sqrt{T_{raw}}\rangle^2,\quad \epsilon=\epsilon_{ch}=0.0186,\quad
\sigma_c^2=1+t\epsilon/2.
\tag{N1}
\]

Brackets ở số D55 là F10, không ngầm là F6. Cả MI và Holevo dùng cùng t,epsilon. **Không cộng** fading noise \((\mu_1-t)V_A/t\); \(\mu_{T\epsilon}\) không được tiêu thụ bởi downstream evaluator này.

**DE**, nhằm giải thích giới hạn chứ không đổi mô hình: nếu khớp Bob second moment của fading nguồn cố định, \(b_{fade}=1+\mu_1V_A+\mu_{T\epsilon}\). Code dùng \(b_{code}=1+tV_A+t\epsilon\). Khớp hai biểu thức sẽ cần

\[
\epsilon_{match}=[(\mu_1-t)V_A+\mu_{T\epsilon}]/t.
\tag{N2}
\]

N2 **không được triển khai trong đường D55** và không được tính lại trong tác vụ này. Vì vậy đây là SKR functional của scalar surrogate, chưa là đầy đủ moment-preserving fading reduction. Scalar MI cũng không bằng fading-average MI hoặc mixture-likelihood MI.

Ideal heterodyne: CN noise có variance mỗi real component \(\sigma_c^2/2\), nền complex 1; covariance optical vacuum 1 SNU và conditional heterodyne có mẫu b+1. Không electronic noise, efficiency khác 1 hay trusted-detector model. Nếu viết \(b=t(a+\chi_{line})\), thì \(\chi_{line}=1/t-1+\epsilon\) là **DE**, không là biến adaptation/lưu riêng.

Phase noise OFF nên \(c_\phi=0,\epsilon_{total}=\epsilon_{ch}\) độc lập VA; module phase tổng quát tồn tại nhưng không dùng để tạo số này. Không suy \(C_{n,\phi}^2\) từ HV để lấp null fields.

## 7. 256-QAM, MB và variance normalization

Đặt \(q_j=j-7.5,\ j=0,\ldots,15\), \(r_{jk}=q_j+\mathrm iq_k\). **DI** (src/modulation/qam256.py:84):

\[
\mathrm{square\_qam256}(\alpha_0)=\alpha_0r_{jk}/\sqrt{30},\quad i=16j+k.
\tag{M1}
\]

Raw với alpha0=√30 là r. **DE**: uniform raw mean energy=42.5, peak energy=112.5; canonical \(x_i=r_i/\sqrt{42.5}\), unit RMS. **alpha0=√30 không phải peak photon constraint 30.**

**DI** (maxwell_boltzmann_pmf:129; run_exact_mb_test2.py:57,93):

\[
p_i=\frac{e^{-\nu_{repo}|x_i|^2}}{Z_x(\nu_{repo})}
=\frac{e^{-\nu_{raw}|r_i|^2}}{Z_r(\nu_{raw})},\quad
\nu_{repo}=42.5\nu_{raw},\quad Z_r=\sum_i e^{-\nu_{raw}|r_i|^2}.
\tag{M2}
\]

**DE**, product normalization:

\[
Z_r=\left(\sum_{j=0}^{15}e^{-\nu_{raw}q_j^2}\right)^2,\quad
p_{jk}=u_ju_k,\quad u_j=e^{-\nu_{raw}q_j^2}/\sum_\ell e^{-\nu_{raw}q_\ell^2}.
\tag{M3}
\]

nu=0 là Uniform; positive nu ưu tiên mức trong. Conversion42.5 được xác nhận từ canonical và raw/canonical PMF guard (:107), không giả định từ lịch sử. Trong LaTeX tối ưu đã lưu nu_MB là nu_raw; PMF primitive nhận nu_repo.

Đặt \(E_x=\sum p_i|x_i|^2\). **DI** (normalization.py:22, Ensemble.computed_va:85):

\[
\alpha_i=\sqrt{V_A/(2E_x)}x_i,\quad {\cal E}=\{p_i,\alpha_i\}_{i=1}^{256},
\quad 2\sum p_i|\alpha_i|^2=V_A,\quad \bar n=V_A/2.
\tag{M4}
\]

C4 identities \(\sum p_i\alpha_i=\sum p_i\alpha_i^2=0\) bảo đảm zero displacement, equal I/Q variance, zero cross covariance; guards kiểm tra tied PMF và rotations. Tăng VA tại nu cố định phóng amplitude theo √VA; đổi nu tại VA cố định đổi PMF,E_x và global amplitude scale. Không weighted centering hoặc GS deformation ở nhánh fixed square MB.

Ví dụ lưu: (nu_raw,VA)=(0.165,5.5), nu_repo=7.0125 giải mã cache hex; photon mean2.75 theo M4 (DE), observed peak51.05066856827034 lưu trong objective. Nguồn (0.165,5.496875) có cùng PMF nhưng amplitude khác, nên C,w/source hash khác; không reuse source moments bằng nu một mình.

Domain dự định nu≥0,VA>0. Wrapper AO thực nhận nu>0,VA>0 (ExactObjective:172); Uniform riêng. Catalog151 ranges nu[0.05,0.8],VA[0.025,8], không full Cartesian product; là coverage, không bounds vật lý/continuous certified search domain.

## 8. Exact source moments C,w

### 8.1. Operator definitions và vai trò

\(\hat a|\alpha_i\rangle=\alpha_i|\alpha_i\rangle\); adjoint là \(\hat a^\dagger\). Đặt \(\tau=\sum p_i|\alpha_i\rangle\langle\alpha_i|\); inverse chỉ trên span nguồn. **DI** qua Gram operations, operator definitions cũng có trong SECURITY_SCOPE_FREEZE:

\[
C=\mathrm{Tr}(\sqrt\tau\,\hat a\sqrt\tau\,\hat a^\dagger),\quad
\hat a_\tau=\sqrt\tau\,\hat a\tau^{-1/2},
\tag{S1}
\]
\[
w=\sum_i p_i\{\langle\alpha_i|\hat a_\tau^\dagger\hat a_\tau|\alpha_i\rangle
-|\langle\alpha_i|\hat a_\tau|\alpha_i\rangle|^2\}.
\tag{S2}
\]

w là sum nonnegative transformed-operator variances; nó tạo penalty rộng correlation bound. C là source correlation kernel, chưa nhân attenuation. Chúng phụ thuộc toàn bộ ensemble (nu và VA); không có L trong S1–S2 nên được reuse qua distances.

### 8.2. Gram/C4 operations thực

**DI** (src/cvqkd/gram_moments.py:28):

\[
G_{ij}=\sqrt{p_ip_j}\exp[-(|\alpha_i|^2+|\alpha_j|^2)/2+\alpha_i^*\alpha_j].
\tag{S3}
\]

Với \(A_i=\sqrt{p_i}|\alpha_i\rangle\), \(G=A^\dagger A,\tau=AA^\dagger\) có cùng positive spectrum. Positive PMF/distinct coherent states cho source span256; không suy rank từ threshold-retained float64. Không cần Fock cutoff cho backend này.

Chọn64 prototypes \((p_k,z_k)\); p_k là probability **một** symbol, orbit mass4p_k. **DI**:

\[
(B_d)_{k\ell}=\sqrt{p_kp_\ell}e^{-(|z_k|^2+|z_\ell|^2)/2+z_k^*\mathrm i^dz_\ell},
\quad G_s=\mathrm{Herm}\!\left(\sum_{d=0}^3\mathrm i^{sd}B_d\right),\ s=0,\ldots,3.
\tag{S4}
\]

Herm(A)=(A+A†)/2. Bốn Hermitian64×64 matrices thay full256×256. Đặt \(s^-=(s-1)\bmod4\), \(D_z=\mathrm{diag}(z_k)\), \(D_p=\mathrm{diag}(1/(2\sqrt{p_k}))\), \(S_s=\sqrt{G_s}\). Fast path (:73):

\[
B_s^{op}=S_sD_zS_{s^-}^{-1},\quad A_s^{op}=G_sD_zG_{s^-}^{-1},
\quad Q_s=S_sD_p,\quad T_s=A_s^{op}Q_{s^-}.
\tag{S5}
\]
\[
C=\sum_s\mathrm{ReTr}(S_sB_s^{op}S_{s^-}(B_s^{op})^\dagger),
\quad d_k=\sum_{s,j}\overline{(Q_s)_{jk}}(T_s)_{jk},
\tag{S6}
\]
\[
w=\sum_k4p_k\sum_{s,j}|(T_s)_{jk}-(Q_s)_{jk}d_k|^2.
\tag{S7}
\]

S5–S7 **DI**, basis representations của S1–S2. Residual S7 tránh catastrophic subtraction; code đối chiếu với \(\sum_s\|A_s^{op}S_{s^-}\|_F^2-\sum_k4p_k|d_k|^2\). Không nhầm B_s^op với AoA Bernoulli.

### 8.3. Arbitrary precision và numerical gates

Fast gate (:50–71) đòi tất cả sector eigenvalues positive; max/min ratio≤1e6; reconstruction residual≤1e-12. Eigensystems detached chỉ kiểm tra; phép fast tính whole-matrix Fréchet sqrt/inverse-sqrt và solves. Residual/subtraction relative discrepancy≤1e-12 và moments finite. Không qua gate thì fallback; threshold1e-12 chỉ metadata diagnostic, không cắt modes.

**DI** (scripts/full_support_c4_worker.py:25,64,208):

1. Nhận exact float.hex của binary64 PMF/prototypes, chuyển mpmath. AP không làm input ban đầu thành số thực vô hạn exact.
2. Với1050/1250/1450 decimal digits, dựng sector overlaps bằng mp.exp, diagonalize bốn sector bằng mp.eighe trong mp.workdps.
3. Đếm256 eigenvalues>0; rung unresolved trả rank/minimum, không tính moments.
4. Eigenbasis \(G_s=U_s\Lambda_sU_s^\dagger\); đặt \(M_s=U_s^\dagger D_zU_{s^-}\), \(R_s=\mathrm{diag}(\sqrt{\lambda_{s,j}})\). Solve từng RHS \(R_{s^-}X=M_s^T\), \(B_s^{op}=R_sX^T\); solve \(R_{s^-}X_2=(R_sB_s^{op})^T\), **\(A_s^{op}=X_2^T\), không nhân thêm R_s**.
5. \(Q_s=R_sU_s^\dagger D_p\); tính trace/residual như S6–S7 bằng mp.fsum. Serialize50 significant digits, final downstream/cache chuyển float64.
6. Hai rung cuối phải full256 và, riêng x=C,w, \(|x_{1250}-x_{1450}|\le10^{-7}+10^{-6}\max(|x_{1250}|,|x_{1450}|)\). Rung1050 có thể unresolved. Đây là tolerance stability, không bound tuyệt đối.
7. Subprocess internal timeout3600s; thất bại fail-closed. Fallback evaluation-only, không gradient.

Chi phí từ exponential rất nhỏ, eigensystems và nhiều matrix RHS/solve ở hàng nghìn digits, conditioning lớn. **Không quadrature cho C,w**: quadrature nằm ở HV/PDF/MI. Dense-Fock là diagnostic riêng, không fallback của cache này.

“Exact” là đúng ensemble/binary64 parameters/full source support với AP hoặc fast validated gate; không symbolic closed form, zero error hay interval proof. Compact payload tham chiếu ghi route ARBITRARY_PRECISION_FALLBACK, support256, FRESH_EXACT_EVALUATION, C=3.2113076519605626,w=1.0248765983174194e-6. Per-rung fallback_rows/minimum/residual/repair log không lưu trong payload: **NOT RECORDED**. Không suy số residual từ route string.

### 8.4. Cache và evidence

ensemble_hash (run_exact_mb_test2.py:82) dùng dtype,shape,hex của p,alpha,declared VA và order labels. Source identity (:183) thêm raw/repo/VA hex, convention, source_implementation hashes của gram_moments/spectral_frechet/worker, numerical settings/precision ladder. exact_cache_provenance.py:42 xác minh schema/key/settings/support/source; cho phép LF/CRLF aliases chứng minh byte-equivalent, không normalize logic, approximate parameters hoặc interpolation. Objective identity (:76) thêm full channel/config, security target, GH order,beta,epsilon và transitive code hashes. Thay L reuse source, không reuse objective context cũ.

results/full_support_c4_gram_evaluation_validation_v1.json hiện **SUPERSEDED_WRONG_AP_W**; không dùng PASS lịch sử. results/ap_worker_corrected_case_A_20260911.json có corrected aa=x2.T và800/900-digit bounded Case A evidence, khác ensemble/precision/source hash; không certify catalog D55. Compact reference cache/provenance hiện mới là căn cứ nguồn D55. Convergence performed trước đây phải giữ scope, không thành fresh convergence run.

## 9. MI heterodyne đầy đủ

Gọi Alice label \(X_A=i\), Bob measurement \(Y\in\mathbb C\), \(m_i=\sqrt t\alpha_i\), \(N\sim{\cal CN}(0,\sigma_c^2)\). **DI** (mutual_information.py:396):

\[
Y=m_i+N,\quad \sigma_c^2=1+t\epsilon/2,\quad
f_i(y)=e^{-|y-m_i|^2/\sigma_c^2}/(\pi\sigma_c^2),\quad f_Y(y)=\sum_jp_jf_j(y).
\tag{I1}
\]

**DE**, miền Bob là toàn complex plane:

\[
I_{AB}=\sum_i p_i\int_{\mathbb R^2}f_i(y)\log_2[f_i(y)/f_Y(y)]\,d^2y.
\tag{I2}
\]

Bayes \(P(i|y)=p_if_i(y)/f_Y(y)\), entropy \(H(p)=-\sum p_i\log_2p_i\), nên

\[
I_{AB}=H(p)+\sum_i p_iE_{Y|i}\log_2P(i|Y).
\tag{I3}
\]

Code dùng I3; likelihood normalizer triệt, logits natural-log, chia ln2 để bits/use. H(p) chỉ là8 ở Uniform, không thay bằng8 cho MB.

Product guard (:14) reshape16×16, kiểm tra PMF outer-product và Cartesian mean, allclose atol/rtol1e-12. Circular noise có real/imag independent nên **DE** \(I_{AB}=I_R+I_Q\), không Gaussian-input approximation.

Gauss–Hermite nodes \(z_\ell\), weights \(w_\ell\) cho \(\int e^{-z^2}g(z)dz\); normalized weights \(\omega_\ell=w_\ell/\sqrt\pi\), noise variance1/2 mỗi trục. Với real levels a_i/probabilities u_i, \(y_{i\ell}=a_i+\sqrt{\sigma_c^2}z_\ell\). **DI** (_deterministic_real_mi:254):

\[
I_R^{(n)}=\frac{-\sum_i u_i\ln u_i+
\sum_{i,\ell}u_i\omega_\ell[\ln u_i-z_\ell^2-
\mathrm{LSE}_j(\ln u_j-(y_{i\ell}-a_j)^2/\sigma_c^2)]}{\ln2}.
\tag{I4}
\]

LSE is ln(sum exp); stable torch.logsumexp. Cộng imaginary counterpart. Caller **n=8**, không default32 của primitive. Full method còn dùng complex grid \(z_\ell+\mathrm iz_m\), weights w_l w_m/π, nhưng D55 gọi product. **Không Monte Carlo/no random samples** cho I_AB lưu ở đây. Discrete mixture đúng mô hình; GH hữu hạn vẫn có numerical quadrature error.

results/exact_mb_test2a/gh_convergence.json có orders8/16/24/32/48/64 ở channel/ensemble khác, MI~3.6765e-4. Không chứng minh GH8 error cho D55 I_AB0.6341892631163653 hay gap3.67e-10. results/mi_convergence.json là Monte Carlo roster riêng, không bound cho GH.

## 10. Holevo direct-Z-minus

Reverse reconciliation lấy key theo Bob, leakage là \(\chi_{BE}\), không \(\chi_{AE}\); beta giảm phần MI, không nhân Holevo. Phạm vi là asymptotic ideal-heterodyne DM covariance functional, không finite-size/composable/fading operational proof.

**DI** (holevo.py:364,403; covariance.py:72):

\[
Z_-=2\sqrt tC-\sqrt{2t\epsilon w},\quad
a=1+V_A,\quad b=1+tV_A+t\epsilon,\quad c=Z_-,
\tag{H1}
\]
\[
\Gamma_{AB}=\begin{pmatrix}a&0&c&0\\0&a&0&-c\\c&0&b&0\\0&-c&0&b\end{pmatrix},
\quad(q_A,p_A,q_B,p_B)\ {\rm order}.
\tag{H2}
\]

VA được lấy ensemble.computed_va đã validate declared VA. Source discrete đi qua C,w,Z, không thay bằng Gaussian-modulation correlation.

Đặt \(\Delta=a^2+b^2-2c^2,D_\Gamma=(ab-c^2)^2\). **DI**:

\[
\lambda_{1,2}=\sqrt{(\Delta\pm\sqrt{\Delta^2-4D_\Gamma})/2},\quad
\lambda_3=a-c^2/(b+1).
\tag{H3}
\]

**DE**: Schur complement heterodyne \(\Gamma_{A|Y}=(a-c^2/(b+1))I_2\), nên một conditional eigenvalue; +1 do ideal heterodyne measurement, không electronic noise mode.

**DI** (bosonic_entropy:156, _evaluate_holevo_for_correlations:344):

\[
g(n)=(n+1)\log_2(n+1)-n\log_2n,\quad g(0)=0,\quad
\chi_{BE}=g((\lambda_1-1)/2)+g((\lambda_2-1)/2)-g((\lambda_3-1)/2).
\tag{H4}
\]

Entropy interpretation là S(AB)−S(A|Y) của Gaussian covariance representative được dùng trong adopted functional. Downstream không dựng density Eve lớn: chỉ invariants, square roots và ba entropies.

Guards **DI**: symmetry tolerance1e-8; physicality1e-10; scale floor1e-15 trong relative quadrature tests. Material negative w/discriminant/lambda-square, lambda<1−tol hay Holevo<−tol fail. Tiny negative w và discriminant clamp0/record; lambda-square clamp0 trước sqrt, uncertainty guard vẫn áp dụng. Lambda trong [1−tol,1) nâng1 cho entropy/record; tiny negative Holevo clamp0/record; nonfinite fail; entropy branch xử lý0ln0. Clamp w/Holevo không clamp K.

Direct branch diagnostic mode=zstar **chỉ Z_-**, không argmax. Caller kiểm tra mode. Full-interval branch với Z_+,physical intersection,maximizer có trong holevo.py:438 nhưng **không dùng** ở catalog. docs/EQUATIONS và audit2026-09-16 mô tả full interval, re-freeze global-MB/LaTeX D55 mô tả direct: phải giữ scope. Không nói Z_- là worst-case đã chứng minh. Direct branch không sửa correlation bằng interval clipping; covariance nonphysical thì fail.

## 11. SKR, phụ thuộc và raw negative values

**DI** (evaluate_candidate:168):

\[
K^{raw}=\beta I_{AB}-\chi_{BE},\quad\beta=0.95.
\tag{K1}
\]

Nguồn \((\nu,VA)\to(p,\alpha)\to(C,w)\), channel \(L\to\mu_{1/2}\to t\); hai branches nhập MI/Holevo rồi K. Channel có thể dựng trước nguồn, reuse trong coordinate search.

| Thay đổi | Cần tính lại về mặt thuật toán | Reuse nếu hash khớp |
|---|---|---|
| L | zeta,eta,v,G_d,w_L,w_eq,sigma_jt,pointing/moments,t; MI,Z,b,lambdas,Holevo,K | source/ensemble/C,w, a; fixed AoA probabilities |
| VA | amplitudes/hash,C,w,means,MI,a,b,Z,lambdas,Holevo,K | channel,t,epsilon,PMF tại nu cố định |
| nu | PMF,E_x,scale/hash,C,w,MI,Z,lambdas,Holevo,K | channel,t,epsilon,a,b tại VA cố định |
| code/settings/target | cache compatibility/context | chỉ identity-bound artifacts |

Raw CSV giữ K<0. Operational nonnegative diagnostic \(K_+=\max(0,K^{raw})\) không ở objective. Log10 renderer scripts/render_theta10_D55_three_scheme_log10.py:68,116 chỉ vẽ finite K>0, ngắt line ở nonpositive, không sửa CSV/đẩy điểm lên0. Linear/symlog renderers phải đọc riêng, không nói mọi plot đều vẽ âm. Tài liệu không render mới.

## 12. Ví dụ tham chiếu

Bảng đầy đủ/path/hash trong [reference_numerical_walkthrough.md](reference_numerical_walkthrough.md).

| Đại lượng | Giá trị lưu |
|---|---:|
| eta_atm | 0.9082089654181673 |
| mean_T_raw, mean_sqrt_T_raw | 0.2793516597874326; 0.4484713170554535 |
| T_eff, epsilon | 0.2011265222214531; 0.0186 |
| nu_raw, VA | 0.165; 5.5 |
| C,w | 3.2113076519605626; 1.0248765983174194e-6 |
| I_AB,beta_I_AB | 0.6341892631163653; 0.602479799960547 |
| chi_BE, K | 0.5244988060866094; 0.07798099387393764 |

Kiểm tra arithmetic binary64 trên số lưu:

\[
0.95(0.6341892631163653)-0.5244988060866094
=0.07798099387393764\ {\rm bits/use}.
\]

Decimal subtraction của hai strings in betaMI và chi là0.0779809938739376; khác phần cuối do serialization operands, không scientific discrepancy. Không suy17-digit accuracy từ17 digits printed. F1/tail, finite-domain moments, covariance/eigenvalues, per-rung source residual và noise correction fading: NOT RECORDED trong mốc chọn.

## 13. Alternating Optimization thực

Đặt r vòng ngoài, \(K_L\) objective scalar fixed L. **DI** về updates; continuous argmax là mục tiêu, actual search hữu hạn:

\[
\mathcal P_1:\max_{V_A>0}K_L(\nu^{(r-1)},V_A),\qquad
\mathcal P_2:\max_{\nu>0}K_L(\nu,V_A^{(r)}).
\tag{O1}
\]

Defaults run_theta10_D55_alt_opt.py:56–61: starts0.10/0.15/0.30/0.80; Rmax6; epsilon_opt1e-8 bits/use; parameter tolerance1e-6; MAX_REFINEMENT_STAGES4; MAX_BOUNDARY_EXPANSIONS3. User term max_inner_refinement_steps tương ứng refinement-stages constant, không field config mới.

Mỗi start dùng smallest available positive VA trên fixed-nu slice, hoặc supplied warm VA nếu hex khớp. Sau distance đầu append previous winner như start thứ5. Original selection lấy largest terminal K ở run có final; max giữ original order khi tie. Catalog ranking độc lập tie-break lowerVA rồi lowernu.

Inner adaptive_maximize_1d:238:

1. Evaluate/reuse mọi exact source values trên slice, fixed coordinate khớp hex. Không fit/interpolation/parabolic optimizer.
2. Endpoint winner: yêu cầu half-value/double-value, tối đa3 attempts. Singleton giảm một phía chưa đóng hai hướng; missing/improving boundary vẫn open.
3. Interior winner z với nearest neighbors z_-<z<z_+: kiểm tra radius≤1e-6 ở **đầu vòng**. Nếu chưa đạt, yêu cầu (z_-+z)/2 rồi (z+z_+)/2. Tối đa4 paired stages; không check tolerance thêm sau stage4.
4. Thiếu C,w hoặc numerical failure giữ status unresolved. Refinement cap→INNER_SEARCH_FAILURE. Không tạo missing SKR bằng interpolation. Chỉ run riêng được phép mới có thể tạo source mới; tài liệu không cấp quyền.

Vòng ngoài đo deltaK=afterP2−before, delta parameters/monotonicity; stopping_status:447:

- Nonfinite/giảm hơn tolerance/monotonic warning/numerical failure → NUMERICAL_FAILURE.
- |deltaK|>1e-8 → tiếp tục nếu chưa hết6.
- |deltaK|≤1e-8 và boundary open → UNRESOLVED_BOUNDARY.
- |deltaK|≤1e-8 nhưng unresolved history/coordinates incomplete → STAGNATED_IN_EXACT_CATALOG.
- Chỉ P1/P2 NUMERICALLY_CLOSED_LOCAL_BRACKET, no missing/failure/open-boundary/history mới CONVERGED_NUMERICALLY.

Unresolved history tích lũy OR, không xóa vì pair đứng yên. Parameter tolerance không thay objective tolerance; epsilon_opt không numerical-error bound. Local numerical closure chưa continuous/global certificate. **DM**: joint_optimization_final.tex lưu algorithm nhưng catalog147, snapshot này151; không sửa bản thảo có sẵn.

## 14. Performance-based near-optimality

Đặt \({\cal C}_{exact}\) finite compatible catalog. **DI** (export_theta10_D55_all_exact_skr_points.py:19):

\[
K_{best}(L)=\max_{(\nu,VA)\in{\cal C}_{exact}}K(L,\nu,VA),\quad
\delta_K^{rel}=(K_{best}-K)/K_{best},\ K_{best}>0.
\tag{O2}
\]

Candidate **đã evaluate** acceptable nếu relative loss≤1e-5=0.001%. CSV delta_K là absolute gap; relative_loss_fraction mới là relative delta; percent=100*fraction. Kbest≤0 → blank/UNDEFINED_NONPOSITIVE_K_BEST, không chia âm. Thresholds absolute1e-6…1e-10 trong near-optimal script khác relative threshold1e-5.

Reference151:9 candidates đạt0.001%, gồm incumbent; thresholds0.0001%/0.001%/0.01% cho4/9/17, nested không cộng. Across26 có39 near rows, dùng own-distance best. Tiêu chí có thể tránh fine AP chỉ để có parameter decimals vô ích; **chưa thay stopping rule AO gốc**, không chứng minh gap với unknown continuous global maximum.

Second reference (0.165,5.496875),K0.07798099350667076; gap3.6726688357191506e-10. Ranking literal binary64 nhưng NUMERICALLY_UNCERTIFIED vì chưa total error enclosure nhỏ hơn gap; gần-flat discrete samples không chứng minh continuous plateau.

## 15. Sweep và numerical results

Grid km:20,21,21.9393102292,22,23,24,25,25.5,26,26.5,27,27.5,28,29,30,30.5,31,31.5,32,32.5,33,34,35,36,38,40.

Mỗi distance dựng channel/context mới, reuse source; tính downstream anew về mặt thuật toán. Tài liệu chỉ đọc stored results. Original sweep chọn best terminal AO; expanded catalog maximum là selection khác. [saved_AO_vs_catalog151.csv](saved_AO_vs_catalog151.csv) so original strict rerun với151:

| L km | Original AO | Catalog151 | Delta bits/use |
|---|---|---|---:|
|22|(0.165,5.5),K0.07661685601911128|(0.165,5.475),K0.07661740491526092|5.488961496435962e-7|
|25 distances khác|cặp/K khớp|cặp/K khớp|0|

Later saved AO checkpoint sau expansion/lower refinement khớp151 ở26/26 theo analysis_verification.json. Đây không phải original strict rerun; không phủ nhận khác biệt22km.

Runner unconstrained selected_rows:353 chọn Uniform best exact VA mỗi distance; Fixed MB giữ(0.2,1.3833230302980657); Optimized MB lấy finite bank maximum. User decimal1.3833230303 khác binary64 nguồn dài; code ghi dùng exact dài, không interpolation. AO sweep có thể copy Uniform/Fixed MB stored rows và thay riêng optimized MB bằng terminal AO.

Grid2D build_theta10_D55_two_level_skr_grid.py:21 gồm A30,B25,giao4→51. Completed grid export ban đầu20 cached/31missing; scatter:127 dùng actual coordinates, K colors, missing dấu×/blank matrix; không interpolated surface. Catalog151 có131 off-grid sources vẫn góp best. Batch đang lấp grid loại khỏi tài liệu; không gọi151 tổng nguồn là full51-grid coverage.

## 16. Traceability và accuracy

[code_equation_traceability.csv](code_equation_traceability.csv) ánh xạ mọi stage tới formula/file/function/line/input/output/consumer/evidence/classification. [skr_pipeline_flowchart.md](skr_pipeline_flowchart.md) có hai branches; [skr_evaluation_pseudocode.md](skr_evaluation_pseudocode.md) có one-point/AO/sweep pseudocode, không executable run authorization.

Source provenance/settings/support,151×26 coverage,identity direct-Z/GH8,K equality và saved export/ranking hỗ trợ literal reproducibility. Chưa bound tổng channel integration/scalar reduction/source AP/GH8/covariance-entropy roundoff. Stability tolerance không zero error; finite catalog maximum không continuous optimum.

[pipeline_consistency_audit.md](pipeline_consistency_audit.md) ghi các bất nhất retained[0,1] versus F10; second-moment noise; peak51.05 versus default30; direct/full-Z scope; source convergence rows absent; GH evidence mismatch; frozen hash; manuscript147/catalog151; original AO22km difference; numerical ordering uncertified và operational-security limitations. Kết luận phù hợp: **BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY**, NUMERICALLY_UNCERTIFIED, không publication/security/continuous-global certification. Dừng sau tài liệu.
