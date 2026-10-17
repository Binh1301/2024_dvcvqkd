# Independent Physical Audit of Negative SKR

Ngày2026-10-17. Phạm vi **AUDIT_ONLY**, task d36a98d1. Không sửa production evaluator/config/source, không chạy P1–P3, không commit/push.

**Kết luận:** không phát hiện contradiction entropy vật lý hoặc lỗi MI/Holevo số học tại các điểm đã audit. Hai Holevo reference đều thấp hơn chặn2S(B1). Giả thiết mean eta bậc1e-4 không đúng với cấu hình đang chạy: mean eta hiện tại khoảng.238, W_pre khoảng2.205. Rate âm được giải thích định lượng trong Gaussian surrogate hiện hành; đây chưa là security proof cho protocol DM fading.

**UNVALIDATED_SECURITY_MODEL** và **NOT_READY_FOR_PUBLICATION_SCALE_RUNS** giữ nguyên.

## A. Actual implementation và provenance

### Call graph thực sự chạy

Runner lịch sử scripts/run_trusted_heterodyne_skr.py:45–55 gọi evaluate_candidate cho reference từ đúng config. Probe mới scripts/probe_negative_skr_production.py chạy32 đánh giá có giới hạn, không lấy SKR từ journal. Sys.setprofile ghi lại call graph và entropy returns thật:

1. scripts/probe_negative_skr_production.main -> src/trusted_heterodyne_skr.evaluate_candidate:262 -> evaluate_batch:212.
2. evaluate_batch -> authenticate: scripts/run_ao_effective_channel_no_fading_noise_reference.py:83. Chỉ tải C,w/source metadata đã xác thực, dựng đúng transmitted ensemble.
3. effective_channel:26 tạo m_xi/N/W_pre; receiver:71 tách trusted eta_B,nu_B.
4. trusted_holevo:119 -> symplectic_spectrum:94 và spectral_entropy:111. Production tính S(AB) trừ S(E|Y) qua finite AB purification; khi eta_B<1, đồng thời tạo AFG AppendixA và kiểm tra spectrum. Điều này khác với việc chỉ dùng ideal nu3 cho nonideal receiver.
5. deterministic_mutual_information trong src/cvqkd/mutual_information.py được gọi với implementation=product, GH8/16/32. Không gọi pooled_fading_mixture_MI hoặc Gaussian-input MI. Không gọi _holevo_from_source_moments của mode cũ ở đường này.

[actual_call_graph.json](actual_call_graph.json) ghi file/function/line/count, kernel arguments và hai entropy production thực sự trả về. Tại ideal, MI kernel nhận T=.16092029098192165, epsilon≈2.4420588998314914. Tại trusted, MI kernel nhận gain²=.11264420368734515 và epsilon adapter≈2.681751659122871. Epsilon adapter bao gồm detector cho riêng likelihood MI, không phải xi_f để dùng lại cho W_pre/Z.

Những số đang audit thuộc mode channel_only_fading_trusted_heterodyne_v1; global production default không được đổi thành mode này. Audit xác nhận evaluator của chính reference được trích dẫn, không suy luận từ việc hàm tồn tại.

### Cache và inputs

Tất cả4 producer hashes trong receipt của task trước và các receipt/report liên quan khớp checkout hiện tại. Hai source payload/C,w, source roster và saved fading moments được đọc từ cache có provenance. Cả hai ensemble hashes còn được tính lại độc lập từ chính p/alpha/VA binary64, không dùng production hash helper. Probe đọc0 cached SKR để tạo32 kết quả mới; hai reference so với artifact trước có residual0 trên I,chi,K,W,Z.

- Source nu_raw=0.17, VA=5.046875: C=2.9818069279923307, w=6.1909456504525073e-07; ensemble SHA256 b2dde0f1bdf8c14fefedc304926b6524b79e0628d577af2b387a55e975f9205b; payload SHA256 e6e1b9ef8be95c72e3328966edde7b7c9e3d9bb885d3171e4927cbcb13d70317; path results/ao_effective_channel_no_fading_noise_reference_continuation/exact_source_cache/2f882cd70090cf960b9df07d66291c049da8546c0c06a517e0714fdfb6bc308f.json.
- Source nu_raw=0.3, VA=0.025: C=0.11249999999999999, w=1.0046087943251475e-16; ensemble SHA256 5a7fa49158c69bb9a79174f926b67f8442dceb126f051c3b1800832de2f71b38; payload SHA256 7d12ec26ad71c2b631d8bb2f69c9cf1aea5d20a024a8f54789d776f54dd00f97; path results/exact_mb_test2/exact_source_cache/87349f16fde4b2bf28859071fc222d91fbddcbf402bb5c46c8eb6083c99a8798.json.

Không chạy worker C,w/AP mới. Source cache authenticity không được gọi là một lần independent full-support source-moment certification mới.

### Physical inputs và tài liệu thực tế

HAP20000m, UAV1000m, reference44 ở(450,450)m, L=21939.3102292m; D_r=.55m; beam waist=.0986760647169751m; eta_atm=.9082089654181673. Raw A0=.9977339699934346, w_eq=1.312921595852572m, sigma_s=1.0570182137187947m, sigma_R²=.0539620777961657; phase/AO OFF; xi_ch=.0186, beta=.95.

[Hosseinidehaj v1](https://arxiv.org/pdf/2002.03476.pdf), Eq4–7/AppendixA, được kiểm tra từ primary web text. Local2002.03476v1(1).pdf không tìm thấy trong workspace/Downloads. Bản thảo thực có là C:/Users/admin/Downloads/2026__Binh_s_work (38).pdf, SHA2560c60153cb6dcd4f8a3a2e8ecfe0cb245b473463f051837fb46028916eb6be0a0; requested(38)(3).pdf không tìm thấy. Trang3 được render và xem trực quan; các khác biệt homodyne/total-noise vẫn ghi rõ, không coi hai phiên bản là giống nhau. [Denys–Brown–Leverrier2021](https://quantum-journal.org/papers/q-2021-09-13-540/pdf/) Eq11–14 và footnotes11–12 được đối chiếu riêng.

Luật physical hiện hành là active-conditioned0<eta<=1, giữ atom AoA0. Không áp dụng normalization mới. Script audit tự viết PDF trong log eta từ raw parameters và tích phân bằng SciPy, không import physical density/moments helper. Kết quả independent m1=.23790886783673015, mhalf=.40114871429673277; residual so saved moments0 và1.11e-16. Raw active retained mass=.9841173294426485, raw total mass=.9841200272202844; atom P0=.00016985667656141038. Physical conditioned mass1. Các số này xác nhận coherence với luật đang dùng, không chứng minh mô hình đã được hiệu chuẩn ngoài thực địa.

## B. Reference numerical decomposition

Cùng nguồn nu_raw=.17, VA=5.046875 SNU. Bảng dùng ít nhất16 chữ số có nghĩa khi phù hợp. high_precision_decomposition.json lưu arithmetic70 decimal digits; độ chính xác số học không đồng nghĩa70 chữ số chính xác của tham số vật lý.

| Quantity | Ideal | Trusted(.7,.0135) |
|---|---:|---:|
| m1 | 0.23790886783673015 | 0.23790886783673015 |
| mhalf | 0.40114871429673266 | 0.40114871429673266 |
| eta_f | 0.16092029098192165 | 0.16092029098192165 |
| Var(sqrt eta) | 0.076988576854808505 | 0.076988576854808505 |
| xi_ch | 0.018599999999999998 | 0.018599999999999998 |
| m_xi | 0.0044251049417631805 | 0.0044251049417631805 |
| Fading excess output | 0.38855172381411168 | 0.38855172381411168 |
| Channel excess output | 0.0044251049417631805 | 0.0044251049417631805 |
| eta_f xi_f | 0.39297682875587486 | 0.39297682875587486 |
| xi_f | 2.44205889983149 | 2.44205889983149 |
| C | 2.9818069279923307 | 2.9818069279923307 |
| w | 6.1909456504525073e-07 | 6.1909456504525073e-07 |
| V | 6.046875 | 6.046875 |
| W_pre | 2.2051214223052606 | 2.2051214223052606 |
| Z | 2.3915984782847097 | 2.3915984782847097 |
| nu_1 | 5.2830365050269812 | 5.2830365050269812 |
| nu_2 | 1.4412829273322418 | 1.4412829273322418 |
| Conditional eigenvalues | [4.262311319657476] | [1, 1.1101285398235259, 4.4990030151947371] |
| S(AB) terms | [2.8353531905841769, 0.83215255416980305] | [2.8353531905841769, 0.83215255416980305] |
| S(AB) | 3.6675057447539796 | 3.6675057447539796 |
| Conditional entropy terms | [2.5208712618455178] | [0, 0.31190856095551323, 2.6002407451198293] |
| Conditional entropy | 2.5208712618455178 | 2.9121493060753423 |
| chi_BE | 1.1466344829084623 | 0.75535643867863744 |
| I_AB | 0.42157258496112981 | 0.31840443441682093 |
| beta I_AB | 0.40049395571307334 | 0.30248421269597986 |
| K_raw | -0.74614052719538893 | -0.45287222598265758 |
| S(B1) upper | 1.530712989465701 | 1.530712989465701 |
| chi_upper=2S(B1) upper | 3.061425978931402 | 3.061425978931402 |
| Bound margin | 1.9147914960229395 | 2.3060695402527642 |
| Complex noise variance | 1.1964884143779375 | 1.1510418900645563 |
| Variance/real quadrature | 0.59824420718896876 | 0.57552094503227813 |
| Gaussian capacity upper | 0.42157258540843368 | 0.31840443455836692 |

### Các số hạng tạo W_pre và Z

W_pre = 1 + m1*VA + m_xi = 1 + 1.2006963173634975 + 0.0044251049417631805 = 2.2051214223052606.

Tương đương W_pre = 1 + eta_f*VA + N_eff = 1 + 0.81214459354938584 + 0.39297682875587486.

N_eff = fading 0.38855172381411168 + channel 0.0044251049417631805; fading chiếm98.8739527071% N_eff. Z_signal=2.3922960308904271, Z_penalty=0.00069755260571727532, Z=2.3915984782847097. Source-side2C=5.9636138559846614 không bị dùng nhầm làm Z sau kênh.


Không có chi_line/chi_tot/trusted detector trong W_pre hoặc cănZ. Shot noise1 xuất hiện một lần. Fading variance được cộng một lần trong N_eff; regrouping W=1+m1VA+m_xi đã bao gồm nó, không cộng lại fading vào biểu thức này.

### Kiểm tra MI độc lập

Tích phân256-state complex Gaussian likelihood thực hiện trực tiếp ở GH16/32/48. Một implementation khác dùng adaptive quadrature một chiều sau khi tự kiểm tra Cartesian/PMF factorization. Cả hai không gọi production MI. Log-likelihood dùng natural log và chia ln2 đúng một lần.

Max difference adaptive/direct2D=3.9898639947466563e-16 bits/use; max production-independent difference trên tất cả đại lượng so sánh=9.0760732263106547e-15.

Source0: sum p=0.99999999999999978, VA_reconstructed=5.0468749999999982, H(X)=5.6505002234211421<=8, max PMF reconstruction error=2.0816681711721685e-17.

Source1: sum p=1, VA_reconstructed=0.025000000000000001, H(X)=4.8311567491755296<=8, max PMF reconstruction error=1.3877787807814457e-17.


Complex likelihood có hệ số1/(pi sigma_c²); tích phân radial độc lập và second moment xác nhận normalization1, E|N|²=sigma_c², Var(ReN)=Var(ImN)=sigma_c²/2. Gain=sqrt(eta_B eta_f), sigma_c²=1+nu_B+eta_B N_eff/2. Vacuum measurement và electronic noise đều chỉ xuất hiện một lần.

Gaussian-input capacity upper là log2(1+SNR) cho một complex use, SNR=eta_B eta_f*(VA/2)/sigma_c². Không có hệ số1/2 bên ngoài log vì cả hai quadrature đều dùng. Hai MI reference nằm dưới capacity với margin tương ứng khoảng4.47e-10 và1.42e-10 bits/use. Với sourceVA=.025, chênh lệch capacity cỡ1e-16 là integration rounding và nhỏ hơn tolerance đã khai báo; không clip MI theo capacity.

## C. Independent physics checks

### Chặn entropy bắt buộc

Cho rho_B1E trước detector và rho_FG trusted độc lập với BE. Thêm ancilla không đổi I(B1FG:E)=I(B1:E). Local measurement/channel và data processing cho chi(Y:E)=I(Y:E)<=I(B1:E). Araki–Lieb cho I(B1:E)<=2S(B1). Với mean displacement0 và covariance W_pre I2, thermal state tối đa entropy tại variance này, nên S(B1)<=g((W_pre-1)/2). Đây là bound cho mọi one-mode state có covariance đó, không cần Bob thực sự Gaussian.

Do đó0<=chi(Y:E)<=2g((W_pre-1)/2), với điều kiện trusted independence/local processing đúng. Audit dùng W_pre trước detector, không dùng V_B2 hoặc variance của dữ liệu heterodyne để tính bound.

| Detector tại reference | Holevo independent | chi_upper | Margin | Kết quả |
|---|---:|---:|---:|---|
|Ideal|1.1466344829084623|3.061425978931402|1.9147914960229395|PASS|
|Trusted|0.75535643867863744|3.061425978931402|2.3060695402527642|PASS|

Các hypothesis được đáp ứng ở mô hình covariance đã khai báo: SNU vacuum1; B1 là mode lượng tử trước detector; F,G ban đầu nằm trong Bob, độc lập Eve; beam splitter và heterodyne là local operations. Sự độc lập trusted là giả định protocol, không phải kết luận từ detector measurements trong task này.

### Spectrum, uncertainty và arithmetic

Independent script tính closed symplectic formula từ Delta/D bằng mpmath70dps, đồng thời diagonalize trực tiếp iOmegaGamma; không import symplectic helper production. Γ+iOmega được kiểm tra riêng. Ideal conditional là V-Z²/(W+1), không phải sqrt(V(V-Z²/W)) homodyne. Entropy được in từng mode trước khi cộng/trừ; không nhầm source-side correlation, dấu trừ conditional hoặc log base.

Reference S(AB) chỉ khoảng3.67 và conditional khoảng2.52/2.91, hiệu khoảng1.15/.76; đây không phải cancellation của hai entropy lớn gây ra số âm giả. Kết quả70dps và binary64 đồng ý ở mức1e-14. Ở T0/source nhỏ, residual chi khoảng-1.4e-70 được lưu nguyên; analytic value là0. Audit không clip Holevo để qua bound. Vacuum symplectic factor1 có residual70dps được lưu riêng, chỉ entropy-limit của mode vacuum được dùng.

### Tổng kiểm tra và FAIL

-201 independent checks PASS: PMF/energy, PDF moments, W/Z identities, physicality, entropy bound và so production cho32 cases; vacuum/no-modulation limits.
-5 self-checks PASS: g known values, vacuum spectrum, normalized complex likelihood, bound sensitivity và kiểm tra AST không import production numerical helpers.
-7 supplemental checks PASS: ensemble/payload hashes, ΓAB/conditional AFG matrix ordering, trusted->ideal limit.
-40 physical entropy-bound evaluations PASS:32 source/channel/detector cases,4 exact-vacuum cases và4 joint detector limits. Không có FAIL–HOLEVO_PHYSICAL_ENTROPY_BOUND ở cấu hình hợp lệ đã chạy.

Các FAIL/exception vẫn được báo: lần chạy diagnostic đầu thất bại khi xuất vacuum row do duplicate xi_ch keyword; script/log nằm trong attempts/initial_independent/. Chỉ sửa script audit rồi chạy lại, production không sửa. Sensitivity self-check cố tình ghép m1=.00026407446657 với Holevo reference1.1466: W=1.0013376626085486, upper=.016037567950527874, nên bị expected rejection. Đây là kiểm tra phát hiện input mismatch, không phải FAIL của cấu hình thực. Không nâng tolerance hoặc đổi bound.

### Weak-transmission scaling, cùng source và detector

Mỗi bảng dùng fixed non-fading channel, cùng C,w/VA và xi_ch=.0186. CSV giữ đầy đủ precision; bảng này làm tròn để đọc. T0 analytic MI/chi=0, residual70dps nếu có vẫn lưu trong CSV.

Source0, primary_detector:

|T|W|Z|I_AB|chi_BE|2S(B1) upper|K_raw|
|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 1.05065475 | 0.5963462099 | 0.03595045448 | 0.03158403148 | 0.3426272697 | 0.002568900276 |
| 0.001 | 1.005065475 | 0.1885812297 | 0.003635931357 | 0.003232692237 | 0.05100734358 | 0.0002214425525 |
| 0.0001 | 1.000506547 | 0.05963462099 | 0.0003640088125 | 0.0003268357895 | 0.006782616593 | 1.897258232e-05 |
| 1e-05 | 1.000050655 | 0.01885812297 | 3.640504496e-05 | 3.300113122e-05 | 0.0008465247682 | 1.583661495e-06 |
| 1e-06 | 1.000005065 | 0.005963462099 | 3.64054614e-06 | 3.331478445e-06 | 0.0001014795372 | 1.270403881e-07 |
| 0 | 1 | 0 | 0 | 0 | 0 | 0 |

Source0, trusted_detector:

|T|W|Z|I_AB|chi_BE|2S(B1) upper|K_raw|
|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 1.05065475 | 0.5963462099 | 0.02492621363 | 0.02185951629 | 0.3426272697 | 0.00182038666 |
| 0.001 | 1.005065475 | 0.1885812297 | 0.002512235828 | 0.00222878062 | 0.05100734358 | 0.0001578434164 |
| 0.0001 | 1.000506547 | 0.05963462099 | 0.0002514219882 | 0.0002252536986 | 0.006782616593 | 1.359719019e-05 |
| 1e-05 | 1.000050655 | 0.01885812297 | 2.514418516e-05 | 2.274381162e-05 | 0.0008465247682 | 1.143164287e-06 |
| 1e-06 | 1.000005065 | 0.005963462099 | 2.514438382e-06 | 2.296035548e-06 | 0.0001014795372 | 9.268091459e-08 |
| 0 | 1 | 0 | 0 | 0 | 0 | 0 |

Source1, primary_detector:

|T|W|Z|I_AB|chi_BE|2S(B1) upper|K_raw|
|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 1.000436 | 0.02249999981 | 0.0001803088423 | 0.001389650993 | 0.005932319126 | -0.001218357592 |
| 0.001 | 1.0000436 | 0.007115124674 | 1.803340759e-05 | 0.0001698521952 | 0.0007380618074 | -0.0001527204579 |
| 0.0001 | 1.00000436 | 0.002249999981 | 1.803365997e-06 | 2.007450996e-05 | 8.828972553e-05 | -1.836131226e-05 |
| 1e-05 | 1.000000436 | 0.0007115124674 | 1.803368522e-07 | 2.316388945e-06 | 1.027733259e-05 | -2.145068936e-06 |
| 1e-06 | 1.000000044 | 0.0002249999981 | 1.803368783e-08 | 2.625328094e-07 | 1.172569317e-06 | -2.454008059e-07 |
| 0 | 1 | 0 | 0 | -1.414949856e-70 | 0 | 1.414949856e-70 |

Source1, trusted_detector:

|T|W|Z|I_AB|chi_BE|2S(B1) upper|K_raw|
|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 1.000436 | 0.02249999981 | 0.000124540957 | 0.0009111615795 | 0.005932319126 | -0.0007928476704 |
| 0.001 | 1.0000436 | 0.007115124674 | 1.245529949e-05 | 0.0001124438335 | 0.0007380618074 | -0.000100611299 |
| 0.0001 | 1.00000436 | 0.002249999981 | 1.245541988e-06 | 1.337801591e-05 | 8.828972553e-05 | -1.219475103e-05 |
| 1e-05 | 1.000000436 | 0.0007115124674 | 1.245543193e-07 | 1.551176793e-06 | 1.027733259e-05 | -1.43285019e-06 |
| 1e-06 | 1.000000044 | 0.0002249999981 | 1.245543321e-08 | 1.764553519e-07 | 1.172569317e-06 | -1.646226903e-07 |
| 0 | 1 | 0 | 0 | -1.414949856e-70 | 0 | 1.414949856e-70 |


Pure-loss fixed T=.25 có W=1+.25VA, no fading. Exact coherent vacuum với VA0,C0,w0 cho MI0; khi channel excess bằng0, Bob vacuum/chi0. Khi channel noise dương, vacuum input có thể cho Bob thermal noise/chi>0 nhưng MI vẫn0, không được giả định chi0 ở noisy channel có T>0. Với VA->0, kiểm tra MI ở.01,.0001,1e-8,0 bằng scaling coherent amplitudes; đó là MI-only limit, không nội suy C,w hoặc tuyên bố thêm exact source vào catalog. Không vi phạm entropy bound trong các case này.

## D. Ideal so với trusted heterodyne

Audit tự khai triển A,F,G covariance blocks và C_AFG,B2 theo AppendixA, không gọi production trusted_holevo hoặc purification. Quadrature order là(q_A,p_A,q_F,p_F,q_G,p_G); Omega=direct sum[[0,1],[-1,0]]. Beam splitter phases được đối chiếu bằng toàn conditional covariance, không chỉ eigenvalues.

Max conditional AFG element difference với production=4.4408920985006262e-16. Trusted entropy tăng từ2.5208712618455178 lên2.9121493060753423, trong khi S(AB)=3.6675057447539796 giữ nguyên. Holevo giảm0.39127804422982482; beta*MI giảm0.098009743017093476; raw K tăng0.29326830121273134, vẫn âm.


Điều này phù hợp với trusted receiver: một phần thông tin không còn truy cập được bởi Eve, song Bob cũng mất tín hiệu/thêm noise. Không thay ideal nu3 vào nonideal spectrum. Giới hạn eta_B=1-delta,nu_B=delta² với delta từ1e-2 tới1e-8 hội tụ về ideal, bound vẫn PASS; bảng trusted_ideal_limit.csv giữ số. Không có thay đổi detector operating point cho thí nghiệm chính.

## E. Root cause

**Không tìm thấy lỗi arithmetic/noise-accounting hoặc physical entropy contradiction tại reference.** Các biểu thức đang chạy đúng ở src/trusted_heterodyne_skr.py:57 (W=1+m1VA+m_xi),:220 (Z),:81 (complex receiver noise),:171 (S_AB-S_E_cond). Independent MI và Appendix entropy tái lập giá trị âm.

Nguyên nhân định lượng là current m1 và fading spread lớn, tạo output excess chủ yếu từ fading. W_pre lớn hơn1 khoảng1.205, không phải khoảng1e-3. Conditional entropy bị trừ đúng nhưng còn để lại chi lớn hơn beta*MI. Không cần một Holevo vượt2S(B1) để làm K âm.

Nếu dùng m1 bậc1e-4, W_pre và entropy bound sẽ thấp hơn nhiều; ghép những moments đó với Holevo1.1466 là sai input/model identity. Đó là nguồn của nghi vấn không tương thích trong task, không phải phép tính của cấu hình thật. Không suy đoán nguồn gốc các con số minh họa nếu chưa có cùng config/hash.

## F. Security validity

Ba trạng thái phải tách riêng:

| Nội dung | Trạng thái | Phạm vi |
|---|---|---|
| DPI + Araki–Lieb + maximum entropy tại covariance |MATHEMATICALLY_VALIDATED|Dưới các giả thiết B1 quantum/local/trusted independence đã nêu |
| Moment/W/Z algebra, Appendix Gaussian receiver |MATHEMATICALLY_VALIDATED|Declared source-independent phase-tracked fading/constant xi_ch và covariance Gaussian model |
| Reference/boundary numerical MI, spectra/entropy |NUMERICALLY_VALIDATED|Các2 sources/32 cases/giới hạn đã liệt kê |
| Full DM fading key-rate security |SECURITY_PROOF_VALIDATED=False|UNVALIDATED_SECURITY_MODEL |

### Denys constraints: suy ra riêng cho fading

Với input source độc lập fading, phase tracked và E[b|alpha_k]=mhalf*alpha_k, đặt nbar=VA/2. Từ các first/second-moment constraints của Denys, suy ra c1=mhalf*C, c2=mhalf*nbar, nB=m1*nbar+m_xi/2. Do đó nB-c2²/nbar=((m1-mhalf²)VA+m_xi)/2=N_eff/2. Thay vào general Eq13 cho Zlower=2c1-2sqrt(w(nB-c2²/nbar))=2mhalf*C-sqrt(2wN_eff). Đây là derivation từ general constraint, không phải khẳng định Eq14 của Denys viết trực tiếp cho atmospheric fading.

Quan hệ algebra này phù hợp với mô hình và exact C,w đã xác thực. Covariance tại Zlower đã kiểm physicality. Tuy nhiên nguồn thống kê đó được simulator cung cấp, chưa là parameter estimation thực nghiệm. Denys footnotes11–12 còn yêu cầu maximum Holevo trên physical correlation interval khi không có bảo đảm lower endpoint là worst case. Audit này không chứng nhận full-interval optimum hoặc thay security target hiện hành.

Hosseinidehaj covariance/detector analysis được xây dựng trong Gaussian-modulation protocol. MI tính bằng AWGN moment surrogate không phải true pooled-fading mixture MI của nguồn discrete; chưa có lower-bound/error theorem được kiểm chứng cho việc thay thế cụ thể này. Trusted Gaussian conditional entropy khớp toán/số không tự cấp một proof mới cho DM fading. Operational CSI/binning/leakage, attacks, finite-size và composable claims vẫn mở. Passing the entropy upper bound là necessary consistency check, không phải sufficient security certificate hay tightness guarantee.

## G. Recommendation

Không đề xuất sửa công thức production để làm K dương: audit không xác nhận lỗi cần patch ở reference. Thay đổi tối thiểu hữu ích trong một task implementation sau là thêm regression guard chi<=2g((Wpre-1)/2) và Gaussian-capacity check vào diagnostic validation, cùng input/config identity trên mọi bảng; không clip chi/MI khi guard fail.

Ưu tiên khoa học tiếp theo là xác nhận measurement constraints và estimator cho actual fading-mixture MI, kiểm tra worst-case physical Z interval/trusted DM bound trong đúng security scope. Đây là đề xuất, không chạy thêm optimizer/source/22.700 điểm/P1–P3 trong task audit này. Mọi physical redesign hoặc detector tuning phải là nghiên cứu riêng, không sửa đầu vào để cứu dấu SKR.

### Artifacts và bảo toàn

[Independent results](independent_audit.json), [16-digit reference table](reference_entropy_decomposition.csv), [all finite cases](independent_results.csv), [checks](checks.csv), [high precision](high_precision_decomposition.json), [source/ordering/limit checks](supplemental_independent_checks.json).

Chỉ thêm2 scripts chẩn đoán riêng và report/state/evidence artifacts. Không sửa source/evaluator/Cw/config/normalization/security functional/frozen specs hoặc kết quả lịch sử. Không training/test dataset access, publication evaluation, baseline/threshold certification, ObjectiveC restart, external PDF edit, commit/push. Frozen actual hashdf83ea63...78c15 vẫn khác historical hash trong AGENTS, đã giữ nguyên. NOT_READY và ObjectiveC USER_STOPPED không đổi. Audit complete; STOP.
