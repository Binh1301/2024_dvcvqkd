# Hệ phương trình được triển khai

Tài liệu này chỉ liệt kê phương trình có thể truy trực tiếp tới đường thực thi PS–GS.

## 1. QAM và PMF

\[
\alpha^{(0)}_{k,l}=\frac{\alpha_0}{\sqrt{30}}[(k-7.5)+j(l-7.5)],
\quad i=16k+l.
\]

Nguồn: `uav_hap_1/zstar/base.py`, dòng 8–14.

\[
p^U_i=1/256,
\quad
p^{Bin}_{k,l}=\binom{15}{k}\binom{15}{l}/2^{30}.
\]

Nguồn: `uav_hap_1/zstar/base.py`, dòng 17–26.

\[
p^{MB}_{k,l}=\frac{e^{-\tilde\nu(k-7.5)^2}e^{-\tilde\nu(l-7.5)^2}}
{\sum_{r,s}e^{-\tilde\nu(r-7.5)^2}e^{-\tilde\nu(s-7.5)^2}}.
\]

Nguồn: `uav_hap_1/zstar/base.py`, dòng 29–38.

## 2. PS phụ thuộc trạng thái

\[
\sigma_c^2=1+T\epsilon/2,\quad
\mathrm{SNR}=TV_A/\sigma_c^2,
\]

\[
\mathbf f=[\log_{10}(\max(T,10^{-12})),\epsilon,
10\log_{10}(\max(\mathrm{SNR},10^{-12}))].
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 285–296.

\[
\boldsymbol\ell=W_2\operatorname{ReLU}(W_1\mathbf f+b_1)+b_2,
\quad p_i=\operatorname{softmax}_i(\operatorname{clip}(\ell_i,-30,30)).
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 220–235, 329–337.

## 3. Chuẩn hóa chòm sao

\[
\mu=\sum_ip_ic_i,\quad \bar c_i=c_i-\mu,\quad
V_{cur}=2\sum_ip_i|\bar c_i|^2,
\]

\[
c_i(V_{target})=\sqrt{V_{target}/V_{cur}}\,\bar c_i.
\]

Với chuẩn hóa đơn vị, (V_{target}=2), do đó (\sum_ip_i|x_i|^2=1). Sau đó (\alpha_i=\sqrt{V_A/2}x_i).

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 153–185, 339–345.

## 4. Kênh quang UAV–HAP

\[
L=\begin{cases}
\sqrt{d_h^2+(H_{HAP}-H_{UAV})^2},&d_h>0,\\
(H_{HAP}-H_{UAV})/\cos\theta,&d_h=0.
\end{cases}
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 10–16.

\[
q(V)=\begin{cases}1.6,&V>50,\\1.3,&6<V\le50,\\0.585V^{1/3},&V\le6,\end{cases}
\]

\[
\xi=\frac{3.912}{V}(\lambda_{nm}/550)^{-q(V)},\qquad
\eta_{atm}=e^{-\xi L_{km}}.
\]

Nguồn: `uav_hap_1/config.py`, dòng 37–50; `channel_model.py`, dòng 32–41.

\[
z_R=\pi W_0^2/\lambda,\qquad W_L=W_0\sqrt{1+(L/z_R)^2}.
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 44–47.

Đặt (x=(2a/W_L)^2), (T_0=\sqrt{1-e^{-2a^2/W_L^2}}), (A=e^{-x}I_0(x)), (B=e^{-x}I_1(x)):

\[
u=1-A,\quad q_r=2T_0^2/u,\quad h=\ln q_r,
\]

\[
\Gamma=\frac{2xB}{uh},\qquad R=a/h^{1/\Gamma}.
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 50–78. Các phép `max(...,EPS)` trong code bảo vệ miền số.

\[
\sigma_{UAV}^2=\sigma_x^2+\sigma_y^2+\sigma_z^2
+a^2(\sigma_\theta^2+\sigma_\phi^2+\sigma_\psi^2).
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 81–95.

\[
\sigma_{turb}^2=1.919C_n^2L^3(2W_0)^{-1/3}
\]

ở baseline `use_hv_turbulence=False`. Nếu bật HV, mã tích phân số

\[
\sigma_{turb}^2=1.919(2W_0)^{-1/3}\cos^{-4}\zeta
\int_{H_{UAV}}^{H_{HAP}}C_n^2(h)(h-H_{UAV})^3dh.
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 97–122; profile (C_n^2(h)) ở `uav_hap_1/config.py`, dòng 53–59.

\[
r\sim\mathrm{Rayleigh}(\sigma_r/\sqrt2),\quad
\eta_{point}=T_0^2e^{-(r/R)^\Gamma},\quad
T=\eta_{atm}\eta_{point}.
\]

Nguồn: `uav_hap_1/channel/channel_model.py`, dòng 141–162.

## 5. (I_{AB}) rời rạc

\[
Y=\sqrt T\alpha_S+N,\qquad N\sim\mathcal{CN}(0,1+T\epsilon/2).
\]

Với (mu_i=\sqrt T\alpha_i),

\[
\widehat I_{AB}=H(S)+\sum_ip_i\frac1{N_A}\sum_n
\log_2\frac{p_i e^{-|y_{i,n}-\mu_i|^2/\sigma_c^2}}
{\sum_jp_j e^{-|y_{i,n}-\mu_j|^2/\sigma_c^2}}.
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 437–475. Mẫu AWGN antithetic: dòng 371–386.

## 6. Ma trận mật độ và Holevo

\[
F_{i,n}=e^{-|\alpha_i|^2/2}\alpha_i^n/\sqrt{n!},\quad
\tau=F^\dagger\operatorname{diag}(p)F.
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 478–483, 554–563.

\[
\operatorname{Tr}C=\operatorname{Tr}(\sqrt\tau a\sqrt\tau a^\dagger),
\quad a_\tau=\sqrt\tau a\tau^{-1/2},
\]

\[
w=\sum_ip_i[\langle\alpha_i|a_\tau^\dagger a_\tau|\alpha_i\rangle
-|\langle\alpha_i|a_\tau|\alpha_i\rangle|^2].
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 565–575.

\[
Z_{raw}=2\sqrt T\operatorname{Tr}C-\sqrt{2T\epsilon w},
\quad Z=\min(Z_{raw},\sqrt{ab}(1-10^{-9})),
\]

\[
a=V_A+1,\quad b=1+TV_A+T\epsilon.
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 577–605.

\[
\Delta=a^2+b^2-2Z^2,\quad D=(ab-Z^2)^2,
\]

\[
\lambda_{1,2}=\sqrt{\frac{\Delta\pm\sqrt{\max(\Delta^2-4D,0)}}2},
\quad
\lambda_3=a-\frac{Z^2}{2+TV_A+T\epsilon}.
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 607–616.

\[
g(x)=(x+1)\log_2(x+1)-x\log_2x,
\]

\[
\chi_{BE}=g((\lambda_1-1)/2)+g((\lambda_2-1)/2)-g((\lambda_3-1)/2).
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 493–499, 617–621.

## 7. SKR và regularization

\[
K_{raw}=\beta I_{AB}-\chi_{BE},\qquad K_+=\max(0,K_{raw}).
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 656–657, 756–768.

\[
L_{sep}=\operatorname{mean}_{i\ne j}e^{-|x_i-x_j|^2/d_0^2},
\quad
L_{peak}=\operatorname{mean}_{i}[\max(|x_i|^2-n_{max},0)]^2,
\]

\[
L_{drift}=\operatorname{mean}_i|x_i-x_i^{(0)}|^2,
\quad
L_{ent}=\operatorname{mean}[\max(H_{min}-H(p),0)]^2,
\]

\[
L=-\operatorname{mean}K_{raw}+\lambda_{sep}L_{sep}+\lambda_{peak}L_{peak}
+\lambda_{drift}L_{drift}+\lambda_{ent}L_{ent}.
\]

Nguồn: `uav_hap_joint_ps_gs.py`, dòng 642–677.

## 8. Gumbel–Softmax tùy chọn

\[
g_i=-\log[-\log U_i],\quad
\tilde s_i=\frac{e^{(\ell_i+g_i)/\tau}}{\sum_je^{(\ell_j+g_j)/\tau}}.
\]

`hard=True` dùng one-hot ở forward và gradient mềm ở backward. Nguồn: `uav_hap_joint_ps_gs.py`, dòng 345–352. Phương trình này mô tả primitive thư viện được gọi; mẫu tạo ra không tham gia objective hiện hành.
