# Chẩn đoán nguyên nhân SKR âm trong mô hình HAP–UAV ba mômen

Ngày 2026-10-13. Đúng một candidate: L = 21.9393102292 km, nu_raw = 0.165,
V_A = 5.5, beta = 0.95, xi_ch = 0.0186; ideal heterodyne R = 1,
xi_det = 0, chi_het = 1; phase/AO OFF.

**Trạng thái: CONFIGURATION_MISMATCH.** Đầu vào vật lý nền và source trùng nhau,
nhưng hai mode chuyển các đầu vào đó thành hai luật PDF khác nhau. Historical
cũng bỏ phương sai fading khi dựng covariance. K âm của corrected nhất quán với
đại số hiện có; không phát hiện lỗi triển khai số học tại điểm này. Tỷ lệ attribution
MI/Holevo là chẩn đoán, còn security lower bound chưa được xác lập.

Chẩn đoán dùng C,w từ cache đã kiểm tra bytes/hash, tái dựng ensemble, kiểm tra
lại physics và historical evaluator tại một điểm, tính integral/moment và các
covariance sensitivity có miền vật lý. MI fading-mixture được đọc từ kết quả
4096 mẫu trước đó; không chạy Monte Carlo mới. Không sửa Eq. (10), Eq. (20),
conditioning convention hoặc evaluator/cache/results cũ.

## A. Physical configuration audit

Kiểm tra bằng unconstrained_config, _channel_row, derive_physical_inputs,
các override tại caller và producer hashes của corrected reference:

| Đầu vào thực tế | Historical | Corrected |
|---|---:|---:|
| HAP/UAV altitude | 20000 / 1000 m | 20000 / 1000 m |
| L | 21.9393102292 km | 21.9393102292 km |
| Zenith angle | 29.99999999997386° | 29.99999999997386° |
| Wavelength | 1550 nm | 1550 nm |
| Full divergence angle | 10 µrad | 10 µrad |
| Beam waist w0 | 0.0986760647169751 m | 0.0986760647169751 m |
| Receiver diameter | 0.55 m | 0.55 m |
| Atmospheric tau_zen | 0.92 | 0.92 |
| Cn²(0), wind | 1e-14 m^(-2/3), 21 m/s | giống historical |
| HAP angular jitter, UAV position SD | 15.61 µrad, 1 m | giống historical |
| AoA SD, FOV half-angle | 1.5 mrad, 6.25 mrad | giống historical |
| Boresight rho | 0 | 0 |

L được chuyển thành zeta bằng acos((h_H − h_U)/(1000 L)); không thay đổi altitude.
w0 và aperture là override của thí nghiệm D55, vì default.yaml có beam/aperture
khác. Requested w0 = 0.0986760647 m là giá trị làm tròn; producer dùng số ở bảng.

Source đã xác minh bằng parameter hex, cache provenance, protected payload bytes,
PMF/amplitude hash và computed V_A = 5.5. Cả hai branch dùng cùng ensemble:

| Trường | Giá trị |
|---|---|
| C | 3.2113076519605626 |
| w | 1.0248765983174194e-6 |
| Source cache key | 77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c |
| Ensemble hash | 430914e792382cce5d92b0ff5ba4e8a641e912bce78c8565dbc18540b92b2faa |
| Payload SHA-256 | d0b9a83a625437a6f056e990b3de61aa95c375940ee7a804056ca44c607026e9 |
| PMF bytes SHA-256 | bc3e54b53fd20403f4f78263e51417d627eafaf91c87d7dab2f02f45f3f37839 |
| Amplitude bytes SHA-256 | e3117d922a6ade26f03181f7d96c4bbd45ec406de07efb5c70a9bf78c2665f38 |

Common physical-input SHA-256:
082f9d4180af7650202ac2f5a761a2a8c580876bb1a871f882993ffe6059e35f.
Historical optical row hash:
1a744fc47721ab8d8e9f2117255402793ec6555d84914aa577d6eeda245056c1,
đã tái lập từ producer.
Corrected scientific context hash:
a3be50b6252de33f871227afa2a60b4a98eb2b90a30fa54f7d5f41dbfdbf3c5c.

**Discrepancy xác nhận:** hai luật fading khác nhau dù đầu vào nền giống nhau.
Không suy ra mismatch chỉ từ hai hash khác schema; các hệ số dưới đây chứng minh
khác biệt. Historical PDF-parameter hash là
1b44fa17187557f552a1768f4651bca66a7d2e82011570c11db9d1e0152c5f40;
corrected Eq. (10) coefficient hash là
866808ff13d6089615aa517b6312bd1b00eb356c4f581e52d868e0ccf84e3039.

## B. PDF và channel moment audit

Hai producer dùng cùng eta_atm = 0.9082089654181673, beam w_L =
0.1475476163187859 m, G_d = 0.029985462238893236 và sigma_jt =
1.0570182137187947 m. Khác biệt nằm ở phép dùng các đại lượng đó:

| Quantity/convention | Historical | Corrected Eq. (10) |
|---|---:|---:|
| Aperture argument nu_ap | dùng w_L chưa broaden | dùng w_Le = w_L sqrt(1+G_d) |
| A0 | 0.9980912504070394 | 0.9977339699934346 |
| w_eq | 1.4111227269002553 m | 1.312921595852572 m |
| B = A0 eta_atm | 0.9064754219251022 | 0.906150936650298 |
| d = (w_eq/(2 sigma_jt))² | 0.4455584043963521 | 0.38570267511254014 |
| Lognormal log-variance v | 0.0015814405801211182 | 0.0539620777961657 |
| Mapping of turbulence | v = A_ap sigma_R0², A_ap = 0.029306517552841305 | v = raw sigma_R0² |
| Moment support used by objective | (0, infinity), untruncated | active conditioned on (0,1] |

Historical sigma_X² = v/4 = 0.00039536014503027954. So sánh trực tiếp số này
với raw sigma_R0² mà bỏ factor 4 và aperture averaging sẽ sai. HV profile,
wind và raw Rytov integral giống nhau; phép map vào scintillation khác nhau.
Trong pointing_error.py:manuscript_pointing_parameters, historical nu_ap
dùng w_L nhưng prefactor w_eq dùng w_Le. Trong
manuscript_literal_3moments.py:LiteralChannel.from_physical, corrected nu_ap
và prefactor đều dùng w_Le.

Các coefficient Eq. (10) hiện hành: C1 = 1.0145250125681322,
C3 = 3.043972119515573, mu = 0.04779435665869496,
x1 = 0.14634374672929093. C1 này là hệ số PDF, khác source operator moment C.
Historical SKR caller không thực thi Eq. (10); nó dùng closed-form moments của
lognormal × pointing × outage. Không được gán coefficient manuscript cho caller đó.

Luật corrected là

$$
dP_{\rm phys}=P_0\delta_0+
P_1\,\frac{f_{\rm active,raw}(\eta)\mathbf{1}_{0<\eta\le1}}{F_1}\,d\eta,
\qquad F_1=\int_0^1 f_{\rm active,raw}(\eta)d\eta.
$$

| PDF quantity | Historical raw law: diagnostic mới, không đổi objective | Corrected raw/physical law |
|---|---:|---:|
| P0 | 0.00016985667656141038 | 0.00016985667656141038 |
| P1 | 0.9998301433234386 | 0.9998301433234386 |
| Raw active mass on (0,1] | 0.9999634578292901 | 0.9841173294426483 |
| Raw total mass on [0,1] | 0.9999634640362218 | 0.9841200272202841 |
| Raw active tail above 1 | 0.00003654217070987845 | 0.015882670557351587 |
| Raw mixed tail above 1 | 0.00003653596377820733 | 0.015879972779715795 |
| Full-support mixed mass | 1 by underlying-law normalization | 0.9999999999999999, quadrature verified |
| Conditioning divisor F1 | không dùng | 0.9841173294426483 |
| Normalized active integral | không áp dụng trong objective | 0.9999999999999999 |
| Physical mixed mass | không dùng trong historical objective | 0.9999999999999999 |

Corrected missing-mass residual: (1 − raw total mass) − mixed tail =
7.28583859910259e-17. Full-support quadrature error estimate 8.69067278097562e-12;
tail error estimate 1.7908630047499441e-13. Tail giải thích phần thiếu mass; đây
không phải xác suất bị quadrature làm mất.

Để tách tác động, giữ nguyên một candidate và thay convention theo thứ tự dưới.
Đây là phân rã đại số có thứ tự; không phải bốn protocol hoặc tối ưu mới.

| Stage | m1 | mh | mh² | Change in mh² from previous |
|---|---:|---:|---:|---:|
| Historical full support | 0.2793516597874326 | 0.4484713170554535 | 0.2011265222214531 | — |
| Chỉ đổi A0/w_eq sang broadened-aperture convention | 0.2521792595678971 | 0.41438625441468374 | 0.171715967847831 | −0.02941055437362211 |
| Sau đó đổi log-variance sang raw Rytov | 0.2521792595678971 | 0.4116818905875036 | 0.1694819790377013 | −0.0022339888101297056 |
| Sau đó cắt eta>1, chưa normalize | 0.23413023966620677 | 0.39477740142305245 | 0.1558491966743379 | −0.013632782363363405 |
| Sau đó condition active, giữ atom | 0.23790886783673015 | 0.40114871429673266 | 0.16092029098192165 | +0.005071094307583762 |

Vì vậy 0.1558491966743379 là **square của retained, chưa-normalized integral**,
không phải full-support raw moment. Full-support corrected raw mh² là
0.1694819790377013. Báo cáo phân biệt hai số này để tránh gán toàn bộ thay đổi
cho coefficients hoặc cho normalization. Tổng thay đổi −0.04020623123953146,
tức giảm 19.9905168%; normalization riêng tăng retained mh² lên 3.2538469%.

| Three-moment quantity | Historical | Corrected | Difference |
|---|---:|---:|---:|
| m1 | 0.2793516597874326 | 0.23790886783673015 | −0.04144279195070244 |
| mh | 0.4484713170554535 | 0.40114871429673266 | −0.047322602758720855 |
| mn = mean eta xi_total | không dùng / không lưu | 1.7665162371050331 | không so trực tiếp |
| T_eff = mh² | 0.2011265222214531 | 0.16092029098192165 | −0.04020623123953146 |

Historical auxiliary mean(T epsilon_ch) = 0.0051959408720462456 khác định nghĩa
mn. Nếu chỉ áp dụng identity ideal cho historical full-support m1 thì được
1.7258442810846137; đây là derived comparison, không phải input historical.
Corrected mn = 2 + (xi_ch − 1)m1 = 1.7665162371050331, residual 0.
T_eff − mh² = 0 và 0 <= T_eff <= m1 <= 1.

## C. Noise decomposition

$$
N_{\rm fading}=(m_1-m_h^2)V_A,\quad N_{\rm channel}=m_1\xi_{\rm ch},
\quad N_{\rm eff}=N_{\rm fading}+N_{\rm channel}.
$$

| Quantity | Actual value |
|---|---:|
| Physical xi_ch, giữ nguyên | 0.0186 |
| N_fading | 0.42343717270144676 |
| N_channel | 0.0044251049417631805 |
| N_eff | 0.42786227764320994 |
| xi_eff = N_eff/T_eff | 2.658846035092476 |
| N_eff from (m1−T_eff)VA + mn + m1 − 1 − chi_het | 0.42786227764320994 |
| Dual-noise consistency residual | 0 |
| N_fading/N_eff | 0.9896576417857215 = 98.9657642% |
| N_fading/N_channel | 95.68974708489704 |

Fading noise là variance của random amplitude coupling nhân VA; không phải
noise thiết bị thêm vào. Intrinsic ideal-heterodyne shot noise vẫn có complex
variance 1; chi_het vẫn bằng 1. Historical covariance chỉ dùng output excess
T_old xi_ch = 0.0037409533133190274, thiếu N_fading của pooled fading law.

## D. Covariance comparison

Historical actual output lấy trực tiếp từ _holevo_from_source_moments,
không suy ngược từ chi. Producer dùng
a = 1 + computed_VA,
b_old = 1 + T_old VA + T_old xi_ch,
Z_old = 2 sqrt(T_old) C − sqrt(2 T_old xi_ch w).

Corrected dùng b = 1 + m1(VA + xi_ch) = 1 + T_eff VA + N_eff. Eq. (20) giữ nguyên:

$$
Z^*(T,\xi)=2\sqrt{T}C-\sqrt{2T\xi w}
          =2m_hC-\sqrt{2wN_{\rm eff}}.
$$

| Quantity | Historical | Corrected | Absolute change | Relative change, (new−old)/old |
|---|---:|---:|---:|---:|
| a | 6.5 | 6.5 | 0 | 0 |
| b | 2.109936825531311 | 2.312923878043779 | +0.20298705251246796 | +0.096205274990332 |
| Z_signal | 2.8803587442900187 | 2.576423871590478 | −0.30393487269954056 | −0.10551979794255026 |
| Z_penalty | 0.00008756729419387908 | 0.0009364892264829492 | +0.0008489219322890701 | +9.694509121287997 |
| Z_star | 2.8802711769958247 | 2.575487382363995 | −0.3047837946318297 | −0.10581774281049632 |
| b−1 | 1.109936825531311 | 1.312923878043779 | +0.20298705251246796 | +0.18288162699287067 |
| Z_star² | 8.295962053032913 | 6.633135256716143 | −1.6628267963167698 | −0.20043809092748424 |

Z giảm chủ yếu vì mh giảm: signal-term giảm 0.3039348727; penalty tăng
0.0008489219. Penalty tăng 10.6945 lần nhưng tuyệt đối vẫn nhỏ vì source w nhỏ.

$$
\Gamma_{\rm old}=
\begin{pmatrix}
6.5&0&2.8802711769958247&0\\
0&6.5&0&-2.8802711769958247\\
2.8802711769958247&0&2.109936825531311&0\\
0&-2.8802711769958247&0&2.109936825531311
\end{pmatrix},
$$

$$
\Gamma_{\rm new}=
\begin{pmatrix}
6.5&0&2.575487382363995&0\\
0&6.5&0&-2.575487382363995\\
2.575487382363995&0&2.312923878043779&0\\
0&-2.575487382363995&0&2.312923878043779
\end{pmatrix}.
$$

Cả hai positive definite: eigenvalue thường nhỏ nhất lần lượt
0.6836253301525979 và 1.0874203801558173. Kiểm tra độc lập Gamma + iOmega
và spectrum của iOmega Gamma trong test pass; không clip giá trị.

## E. Symplectic eigenvalues

Dùng Delta = a² + b² − 2Z², D = (ab − Z²)²,
lambda_1,2 = sqrt((Delta ± sqrt(Delta²−4D))/2), và
lambda_3 = a − Z²/(b+1).

| Quantity | Historical | Corrected | Difference |
|---|---:|---:|---:|
| Delta | 30.109909301667322 | 34.33334635219279 | +4.223437050525469 |
| D | 29.361521956329224 | 70.57461592636346 | +41.21309397003424 |
| lambda_1 | 5.394530138863511 | 5.668978112682573 | +0.2744479738190613 |
| lambda_2 | 1.0044669643948223 | 1.4819019907263518 | +0.47743502633152946 |
| lambda_3 | 3.832433898680368 | 4.497800281293246 | +0.6653663826128784 |

Mọi lambda >= 1. Corrected producer có lambda_2 =
1.4819019907263522; công thức Delta/D độc lập cho 1.4819019907263518.
Chênh lệch 4.44e-16 là rounding, không repair.

## F. Holevo decomposition và covariance controls

Với g(n) = (n+1)log2(n+1) − nlog2(n), g(0) = 0:

| Quantity (bits/use) | Historical | Corrected, independent algebra | Difference |
|---|---:|---:|---:|
| g((lambda_1−1)/2) | 2.8658431601679277 | 2.93823091098018 | +0.07238775081225235 |
| g((lambda_2−1)/2) | 0.022894967000458538 | 0.8812071766073466 | +0.858312209606888 |
| S(AB) | 2.888738127168386 | 3.8194380875875265 | +0.9306999604191404 |
| S(A given Y_B) | 2.3642393210817767 | 2.5998484636147245 | +0.23560914253294785 |
| chi_BE | 0.5244988060866094 | 1.219589623972802 | +0.6950908178861925 |

Producer corrected chi = 1.2195896239728028; independent entropy residual
−8.881784197001252e-16. Lambda_2 đóng góp chính: gần vacuum 1 ở historical
nhưng lên 1.481902 ở corrected, làm entropy tăng 0.858312. Entropy điều kiện
tăng và trừ lại 0.235609; net Holevo tăng 0.695091.

Các control dưới chỉ là sensitivity đại số theo thứ tự, đều physical. Không
gán MI, SKR hoặc security cho chúng.

| Covariance sensitivity | b | Z | chi_BE |
|---|---:|---:|---:|
| Historical | 2.109936825531311 | 2.8802711769958247 | 0.5244988060866094 |
| Chỉ đổi T_eff, giữ fixed xi_ch historical | 1.8880547178128329 | 2.576345544379474 | 0.4429134296445705 |
| Sau đó dùng m1 xi_ch, chưa thêm fading | 1.8894867053423323 | 2.5763286330846107 | 0.44982539612874195 |
| Sau đó thêm N_fading vào b, giữ Z trước | 2.312923878043779 | 2.5763286330846107 | 1.2191436805518054 |
| Sau đó đổi Z_penalty sang N_eff corrected | 2.312923878043779 | 2.575487382363995 | 1.219589623972802 |

Chỉ giảm T_eff làm chi giảm khoảng 0.0815854 trong control. Thêm variance
fading vào b làm chi tăng 0.7693182844; điều chỉnh penalty cuối chỉ tăng
0.0004459434. Đây là bằng chứng tại điểm này rằng phần noise bị historical
bỏ là nguyên nhân lớn của chi tăng, không thể quy toàn bộ cho giảm T_eff.

Corrected correlation interval được tái kiểm tra bằng solver hiện hành:

$$
Z\in[2.575487382363995,\ 2.5773603608169613].
$$

Nguồn bound: DBL Eqs. (11)–(13), với c1 = mh C, c2 = mh VA/2,
n_B = m1(VA+xi_ch)/2; intersect physicality cap. Giả định là fixed centered
C4 ensemble, independent phase-compensated fading, pooled observations gồm outage
và asymptotic observed moments. Mapping này được triển khai và hash-bound; chưa
là proof độc lập cho operational protocol/parameter estimation.

Grid257, denser515 và bounded refinement cho numerical maximum tại Z_star,
chi_max = 1.2195896239728028; upper endpoint chi = 1.2185959107733892.
Không giả định monotonicity; invalid covariance evaluations và repairs đều rỗng.
rigorous_global_error_enclosure=false: numerical search chưa chứng nhận
continuous supremum hoặc finite-size/composable security.

## G. Mutual information

Cả ba MI dùng discrete 256-QAM ensemble, không dùng Gaussian-modulation MI.

| MI method | I_AB (bits/use) | Sampling standard error | beta I_AB |
|---|---:|---:|---:|
| Historical deterministic GH8/product | 0.6341892631163653 | N/A | 0.602479799960547 |
| Corrected effective Gaussian, discrete QAM GH32 | 0.4484184676941574 | N/A | 0.42599754430944947 |
| Corrected pooled fading mixture, cached MC | 0.4652637991973034 | 0.019468676410223464 | 0.44200060923743817 |

Historical Y|i = CN(sqrt(T_old) alpha_i, 1+T_old xi_ch/2), complex variance
1.0018704766566595. Corrected Gaussian surrogate dùng sqrt(T_eff) alpha_i,
complex variance 1+N_eff/2 = 1.213931138821605. Signal amplitude ratio new/old
= 0.8944802020574497 và excess variance lớn hơn.

Actual mixture dùng đúng conditional detector law:

$$
p(y|i)=P_0\,{\rm CN}(y;0,1)+
P_1\int_0^1{\rm CN}(y;\sqrt{\eta}\alpha_i,1+\eta\xi_{\rm ch}/2)
f_{\rm active,phys}(\eta)\,d\eta.
$$

Trong mixture không cộng N_fading lần nữa vào conditional noise; random eta đã
có trong likelihood. Gaussian surrogate là moment-matched approximation và
variance fading có thể phụ thuộc symbol nếu xét conditional distribution; không
thể dùng surrogate như một theorem cho actual mixture. Mixture shape không còn
AWGN và pooling chung eta khiến I/Q không factorize.

Historical và Gaussian surrogate chỉ chứa outage gián tiếp qua moments; không
có atom tường minh trong scalar likelihood. Actual mixture giữ đúng P0 trong
likelihood và Bernoulli sampler. Seed20261013 cho 0 outage trong 4096 mẫu là
realization ngẫu nhiên, không phải loại outage khỏi protocol.

MC sampling-only normal 95% interval là [0.42710519343326536,
0.5034224049613414]. Mixture − Gaussian estimate = 0.016845331503145988,
chỉ 0.865253 standard error; không kết luận khác biệt có ý nghĩa thống kê.
Mixture quadrature32→64 difference 5.238964994016047e-10 nhưng MCSE > target
0.002: SAMPLING_PRECISION_NOT_MET. Gaussian GH16→32 difference
8.881784197001252e-16 chỉ kiểm tra quadrature, không bound approximation error.

## H. Exact SKR decomposition

$$
\Delta K=\beta(I_{\rm new}-I_{\rm old})-(\chi_{\rm new}-\chi_{\rm old}).
$$

| Quantity | New = actual-mixture MC estimate | New = Gaussian surrogate |
|---|---:|---:|
| K_historical | 0.07798099387393764 | 0.07798099387393764 |
| K_corrected | −0.7775890147353646 | −0.7935920796633533 |
| delta_I_AB | −0.16892546391906188 | −0.18577079542220787 |
| delta_beta_I_AB | −0.1604791907231088 | −0.17648225565109746 |
| delta_chi_BE | +0.6950908178861934 | +0.6950908178861934 |
| delta_K | −0.8555700086093022 | −0.8715730735372909 |
| Fraction of decline from MI | 18.7569911% | 20.2487044% |
| Fraction of decline from Holevo | 81.2430089% | 79.7512956% |

Đây là attribution của các điểm estimate thuộc các channel statistical models
đã nêu; không trộn chúng thành một validated protocol. Sampling SE của beta I
và K mixture là 0.018495242589712288. Cached sampling-only K interval là
[−0.8138396902112007, −0.7413383392595285], chưa gồm source/security/systematic
errors. Giữ signed negative K, không clip sang 0 hoặc gọi bằng key throughput.

## I. Root-cause conclusion và validation

1. **Vì sao T_eff giảm?** VERIFIED: aperture convention giảm mh²
   0.02941055437362211, raw-Rytov mapping giảm thêm 0.0022339888101297056,
   cắt tail giảm 0.013632782363363405, normalization tăng lại
   0.005071094307583762. Total −0.04020623123953146. Hai mode khác luật PDF.
2. **Fading noise lớn bao nhiêu?** VERIFIED: 98.9657642% N_eff,
   gấp 95.68974708489704 lần physical channel output excess noise.
3. **Vì sao Z_star giảm?** VERIFIED: mh giảm làm signal term giảm
   0.30393487269954056; penalty tăng 0.0008489219322890701.
4. **Entropy nào tăng chi?** VERIFIED: lambda_2 entropy tăng
   0.858312209606888; S(AB) tăng 0.9306999604, entropy điều kiện tăng
   0.2356091425, net chi tăng 0.6950908179. Covariance controls chỉ rõ tác động
   lớn của việc đưa fading variance vào b.
5. **K âm có nhất quán không?** VERIFIED về algebra của candidate này:
   reproduction/physicality/identity checks pass. Có mismatch giữa channel
   conventions của hai mode; không thấy configuration input hay arithmetic
   bug trong corrected tại reference. UNRESOLVED: chọn convention phù hợp với
   manuscript/physical experiment, MC precision, assumptions và total-error
   security justification. Không suy từ K âm rằng mọi VA/nu/protocol đều âm.

| Validation requirement | Evidence/residual |
|---|---|
| 1. Geometry | Current physical inputs/hash match; L residual <= 1e-9 m; PDF-convention mismatch ghi rõ |
| 2. Source/PMF/VA/C/w | Bytes/provenance/ensemble checks; computed VA−declared VA = 0 |
| 3. Eq. (10) unchanged | Current producer bytes match previous hash |
| 4. Corrected physical law normalized | Mass−1 = −1.1102230246251565e-16 |
| 5. mn identity | 0 |
| 6. T_eff and ordering | T_eff−mh² = 0; ordering holds |
| 7. Noise decomposition | Dual noise residual = 0 |
| 8. Covariance physicality | Both Gamma+iOmega tests and lambda domain pass |
| 9. Eq. (20) unchanged | Producer hash matches; Z identity residual = 0 |
| 10. Symplectic spectrum | Independent iOmega Gamma spectrum agrees within 1e-13 |
| 11. Entropy output | Historical residual 0; corrected −8.881784197001252e-16 |
| 12. SKR attribution | Delta K identity residual 0 |
| 13. Historical regression | Actual I, betaI, chi, K and T_eff residuals all 0 |
| 14. Protected scientific files | 3663 previous protected hashes and 13 prior ideal output hashes checked current; changes=[] |

Tám tests nhỏ kiểm tra source identity/status, moment/noise, entropy/SKR,
unresolved precision, independent uncertainty/spectrum, full vs retained integrals,
sensitivity interpretation và fail-closed covariance/provenance.
Receipt ghi test count/status/hash hiện hành; không mượn số test của lượt trước.

Frozen spec SHA-256 vẫn
df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15;
khác historical AGENTS expected hash, được giữ như pre-existing promotion blocker.
Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS; không mở training, test hay
optimization từ diagnostic này.

## J. Next step recommendation

Bước nhỏ nhất là author chốt convention aperture và scintillation trong
manuscript dựa trên nguồn/physical model, vì đầu vào giống nhau đang cho hai PDF
khác nhau. Nếu chọn sửa một convention, sửa riêng mode được chỉ định và kiểm tra
lại một điểm với provenance mới. Chưa có cơ sở tự động sửa Eq. (10), Eq. (20)
hoặc conditioning.

Tăng precision actual-mixture MI và kiểm tra security assumptions là việc sau
khi chốt luật channel. Không nới tolerance hoặc khởi động optimization để làm
K dương. Chẩn đoán này không thực hiện khuyến nghị.

Artifacts: [diagnostic_result.json](../results/manuscript_corrected_3moments/negative_skr_diagnostic_20261013/diagnostic_result.json),
[diagnostic_receipt.json](../results/manuscript_corrected_3moments/negative_skr_diagnostic_20261013/diagnostic_receipt.json),
[test_output.txt](../results/manuscript_corrected_3moments/negative_skr_diagnostic_20261013/test_output.txt),
[script](../scripts/run_negative_skr_diagnostic.py), [tests](../tests/test_negative_skr_diagnostic.py).
Input/producer/config/source hashes, actual parameters, coefficient stages,
matrices, spectra, entropy, interval and all signed rates are in JSON.

**FINAL STATUS: CONFIGURATION_MISMATCH. STOP.** Không AP, AO, Objective C restart,
182-candidate/26-distance sweep, new Monte Carlo, publication evaluation,
commit hoặc push; chờ yêu cầu tiếp theo.
