# Uniform 256-QAM — khảo sát SKR dương, manuscript-v43

## Kết quả chính và bảng parameter

**PDF Eq. (10) gốc: chưa tìm được Uniform SKR dương trong các điểm hợp lệ đã thử.**
Ứng viên mạnh nhất: K=-0.0244641665795 bit/use tại Dr=0.4 m,
divergence=50.0 µrad, jitter=0.5 µrad,
σh=0.03 m, zenith=0.0°, VA=0.6.
Đây là kết quả âm, không thay bằng 0. Những PDF không đạt mass gate không có MI/Holevo/SKR.

**Mô hình bị chặn độc lập (secondary), tại receiver 30 cm: tìm được Uniform raw SKR dương
K=0.107882560294 bit/use với receiver 30 cm.**
Kết quả này không chứng minh Uniform dương dưới Eq. (10) gốc.
Nó giữ đúng noise-v43, homodyne Gaussian effective/RR nhưng dùng một luật thu công suất khác,
được khai báo và suy ra riêng bên dưới. Không thay production model, không đổi tolerance.

| Parameter | Giá trị |
|---|---|
| HAP / UAV altitude | 20 km / 1 km, giữ cố định |
| Wavelength | 1550 nm |
| Atmospheric zenith transmittance | 0.92; không thay độ cao/profile |
| Wind / Cn² ground | 21 m/s / 1e-14 m^(-2/3), từ receiver30 |
| AoA half FOV / SD | 0.00625 rad / 0.0015 rad |
| Explicit outage atom P0 | 0.00016985667656141065 |
| Channel / detector excess noise | 0.0186 / 0.005 SNU |
| Separate detector efficiency | Không có eta_det trong phép tính v43 này |
| Reconciliation / β | Reverse reconciliation / 0.95 |
| AO / phase / boresight | OFF / OFF / 0 |
| Baseline Dr / full divergence / jitter / σh | 0.30 m / 35 µrad / 1.561 µrad / 0.10 m |
| Secondary best Dr / full divergence / jitter / σh | 0.3 m / 10.0 µrad / 0.5 µrad / 0.03 m |
| Secondary best zenith / slant length / VA | 0.0° / 19.0 km / 3.0 |
| Source energy / probabilities | VA=2 nbar; p=1/256 exactly |
| Uniform source coverage | 33 authenticated exact points in requested VA domain |
| MB source coverage | 197 authenticated exact points, separate ensembles |
| Mass / MI / Holevo numerical tolerance | 1e-10 / 2e-10 / 2e-8 |

## Mô hình và công thức đang thực sự dùng

Với m1=E[η], mh=E[√η], M0 là tổng mass kể cả atom AoA:

\[
T_f=m_h^2,\quad
\langle\eta\xi\rangle=0.0186m_1+0.005M_0,\quad
N=T_f\xi_f=(m_1-T_f)V_A+0.0186m_1+0.005M_0.
\]

Giữ quy ước giới hạn của ηξ tại outage như evaluator manuscript-v43 đã kiểm tra;
không thay bằng một detector plane mới. Phương sai homodyne là 1+N,
trung bình có điều kiện là 2√Tf Re(αk). Tính MI rời rạc thực 1D
bằng tích phân mixture Gaussian; không thay MI bằng Shannon capacity.
Các điểm được chọn được kiểm tra lại GH128, tích phân entropy đầu ra thích nghi,
256 ký hiệu so với 16 mức biên X, X/P và bất biến scaling cổ điển.

Covariance dùng a=1+VA, b=1+Tf VA+N và cùng Tf,N trong khoảng DBL:

\[
Z\in[2\sqrt{T_f}C-\sqrt{2Nw},2\sqrt{T_f}C+\sqrt{2Nw}]
\cap[-Z_{phys},Z_{phys}],
\quad Z_{phys}^2=\min((a-1)(b+1),(a+1)(b-1)).
\]

\[
\nu_{1,2}=\frac{\sqrt{(a+b)^2-4Z^2}\pm|a-b|}{2},
\quad \nu_3=\sqrt{a(a-Z^2/b)},
\quad \chi_{BE}=g((\nu_1-1)/2)+g((\nu_2-1)/2)-g((\nu_3-1)/2).
\]

g(x)=(x+1)log2(x+1)-x log2(x). Lấy max χ trên khoảng Z vật lý bằng solver số
và kiểm tra lưới 33/129, entropy độc lập 80/110 chữ số. Đây không phải bao
chứng nhận toàn cục bằng interval arithmetic. K=0.95 IAB−χBE, giữ mọi K âm.
Không clip eigenvalue hoặc sửa covariance. C,w thuộc đúng ensemble gắn source hash.

## Luật kênh: primary và secondary khác nhau ở đâu

Primary giữ nguyên Eq. (10), tích phân trên 0<η≤1 và atom P0 tại 0.
M0=P0+P1 C1 Q(χ²) được tính closed form và độc lập trong log η.
Mass η>1 được lưu riêng; nếu 1−M0>1e-10, rate bị chặn trước khi tối ưu VA.
Không renormalize, không clip η, không chuyển phần đuôi thành erasure.
Stage A giữ nguyên lỗi mass tại 0°–4°. Đổi Dr/divergence luôn tính lại w0,wL,
turbulence broadening, equivalent beam, pointing và atmospheric/slant geometry.

Secondary là luật Gaussian beam random-width bảo toàn công suất, đã có evaluator chẩn đoán
trong repository. Đặt B~Bernoulli(P1), S~Normal(−v/2,v),
W=w_eff exp(−S/2), R~Rayleigh(σs), các biến độc lập:

\[
F(a,R,W)=F_{\chi'^2_2((2R/W)^2)}((2a/W)^2),\quad
\eta=B\eta_{atm}F(a,R,W),\quad a=D_r/2.
\]

Mỗi beam có tổng công suất 1, nên 0≤η≤ηatm≤1 và tổng probability đúng 1,
atom vẫn là P0. Đây là thu công suất tròn chính xác trong một luật random-width
được định nghĩa mới; không phải truncate/condition/renormalize Eq. (10).

\[
m_1=P_1\eta_{atm}\,E_S[1-\exp(-2a^2/(W^2+4\sigma_s^2))],
\]
\[
m_h=P_1\sqrt{\eta_{atm}}\,E_S\int_0^\infty
e^{-x}\sqrt{F_{\chi'^2_2(8\sigma_s^2x/W^2)}((2a/W)^2)}\,dx.
\]

Tích phân GH32/64 khớp ở ứng viên dương; kiểm tra độc lập GH96×Legendre512
trên x∈[0,40], phần mass bỏ qua ≤exp(−40), sai khác moment dưới 1e-12.
Luật random-width chưa được hiệu chuẩn bằng phép đo turbulence/beam-wander;
đúng support và normalization không chứng minh đây là mô hình khí quyển thực chính xác.

Đối chiếu hai luật tại từng geometry cố định (không đổi noise hoặc nguồn trong một đánh giá):

| physical_setting | channel_law | pdf_mass | mass_deficit | E_eta | E_sqrt_eta | VA | raw_SKR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary_best_geometry | manuscript43_Eq10_retained_0_to_1 | 0.999999999973 | 2.69689766941e-11 | 0.267806800665 | 0.514768920205 | 0.6 | -0.0244641665795 |
| primary_best_geometry | power_conserving_random_width | 1 | 0 | 0.267876629866 | 0.515714233658 | 0.75 | -0.0214319321875 |
| secondary_best_geometry | manuscript43_Eq10_retained_0_to_1 | 0.901329724565 | 0.0986702754347 | 0.670842710837 | 0.77456969395 | BLOCKED | BLOCKED |
| secondary_best_geometry | power_conserving_random_width | 1 | 0 | 0.779607523412 | 0.882168676941 | 3 | 0.107882560294 |


Nếu Eq. (10) thất bại ở geometry secondary tốt, không gán cho nó rate của secondary.

## Stage A/B/C — primary Eq. (10)

| stage | Dr_m | divergence_urad | jitter_urad | sigma_h_m | zenith_deg | VA | raw_SKR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.3 | 35 | 1.561 | 0.1 | 30 | 0.3 | -0.0336748904266 |
| B | 0.3 | 40 | 0.5 | 0.03 | 0 | 0.6 | -0.0260980409363 |
| C | 0.4 | 50 | 0.5 | 0.03 | 0 | 0.6 | -0.0244641665795 |


Stage A dùng 31 góc 0:1:30; coarse VA rồi lấy toàn bộ nguồn chính xác trong
các bracket cực đại cục bộ. Stage B screen 675 geometry ở 0/10/20°, tối đa
5 VA coarse cho kênh hợp lệ, full bank top16 và góc 0:1:20 tại 4 settings tốt nhất.
Đây là sàng lọc có chủ đích; không tối ưu liên tục toàn miền ở mọi geometry.
Stage C dùng 3 divergence lân cận settings B tốt, rồi mở rộng 60 µrad khi
aperture lớn làm mass gate khó đạt; góc fallback 40/50/60° không phải thay độ cao.
Không dùng điểm bị loại để kết luận một thiết kế có positive SKR.

| Dr_m | valid_contexts | blocked_contexts | best_raw_SKR | VA | zenith_deg | divergence_urad |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 341 | 406 | -0.0260980409363 | 0.6 | 0 | 40 |
| 0.35 | 69 | 60 | -0.0271775345566 | 0.6 | 0 | 50 |
| 0.4 | 57 | 72 | -0.0244641665795 | 0.6 | 0 | 50 |
| 0.45 | 24 | 105 | -0.0258234395319 | 0.6 | 0 | 60 |
| 0.5 | 19 | 191 | -0.0258453431014 | 0.6 | 20 | 60 |
| 0.55 | 6 | 204 | -0.0314009405326 | 0.075 | 60 | 60 |
| 0.6 | 0 | 210 | BLOCKED | BLOCKED | BLOCKED | BLOCKED |


Với Dr=0.60 m, chưa có geometry primary hợp lệ trong miền C đã thử;
không kết luận mọi divergence/góc khác đều bất khả thi. Aperture lớn hơn
không khắc phục được tự động giới hạn support của xấp xỉ PDF.
Mọi lựa chọn VA/nu là best exact-tested; không có global bound hoặc chứng nhận minimum liên tục.
Ở ứng viên primary mạnh nhất, βI=0.10001340799 còn χ=0.12447757457;
muốn K>0 phải cải thiện chênh lệch hơn 0.0244641665795 bit/use.
Nếu giữ χ cố định thì MI phải vượt 0.131029025863 bit/use; đây chỉ là
điều kiện đại số, không chứng minh có thể điều khiển MI độc lập với χ bằng VA/geometry.
Cần hoàn tất các nguồn còn thiếu và mở rộng có kiểm soát miền geometry/PDF hợp lệ
trước khi kết luận rộng hơn. Không giảm ξch/ξdet, đổi β hay đổi homodyne để tạo positive.

## Uniform dương và đối chiếu MB trên cùng kênh

| channel_law | scheme | Dr_m | VA | nu_raw | I_AB | beta_I_AB | chi_BE | raw_SKR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| manuscript43_Eq10_retained_0_to_1 | Optimized Uniform 256-QAM | 0.4 | 0.6 | 0 | 0.105277271569 | 0.10001340799 | 0.12447757457 | -0.0244641665795 |
| manuscript43_Eq10_retained_0_to_1 | Fixed MB-shaped 256-QAM | 0.4 | 1.62499953997 | 0.25 | 0.255188725434 | 0.242429289162 | 0.205300889877 | 0.0371283992853 |
| manuscript43_Eq10_retained_0_to_1 | Optimized MB-shaped 256-QAM | 0.4 | 2.6666460606 | 0.2 | 0.38041833266 | 0.361397416027 | 0.318472549874 | 0.0429248661524 |
| power_conserving_random_width | Optimized Uniform 256-QAM | 0.3 | 3 | 0 | 0.837890190047 | 0.795995680545 | 0.688113120251 | 0.107882560294 |
| power_conserving_random_width | Fixed MB-shaped 256-QAM | 0.3 | 1.62499953997 | 0.25 | 0.581003955532 | 0.551953757755 | 0.259423316619 | 0.292530441137 |
| power_conserving_random_width | Optimized MB-shaped 256-QAM | 0.3 | 8 | 0.125 | 1.40787565065 | 1.33748186811 | 0.826896392984 | 0.51058547513 |


Secondary best Uniform tại Dr=30 cm: source hash d06c6c3560dcc1173a60c6043f5e4e6d44aee0c64ad465fc624e0f3fc98a5522;
C=1.92061533388, w=0.0292407986576; source payload results/exact_mb_test2/exact_source_cache/ccd0581ff968d423cd8050e35fed4023300df145147d2fadc1febbbcd9032723.json.
Primary best dùng source riêng ghi trong CSV và source_catalog.json.
Fixed MB cố định (nu_raw,VA)=(0.25,1.6249995399703647), ensemble hash
01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754.
Optimized MB chọn từ 197 nguồn xác thực; không lấy C,w của MB cho Uniform.

Gshaping(primary)=0.0673890327319 bit/use;
Gshaping(secondary)=0.402702914836 bit/use.
Chỉ trừ các rate có cùng law/geometry/noise, không so chéo primary với secondary.

## Cải thiện nào có tác động lớn trong phép đối chiếu cục bộ?

Giữ geometry ứng viên secondary dương rồi trả từng parameter về baseline;
mỗi hàng đều chọn lại VA từ cùng nguồn chính xác:

| ablation | divergence_urad | jitter_urad | sigma_h_m | VA | raw_SKR | K_loss_on_reversion |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 35 | 1.561 | 0.1 | 0.3 | -0.0331805356051 | 0.141063095899 |
| all_improved | 10 | 0.5 | 0.03 | 3 | 0.107882560294 | 0 |
| revert_divergence | 35 | 0.5 | 0.03 | 0.8 | -0.0189661100985 | 0.126848670393 |
| revert_jitter | 10 | 1.561 | 0.03 | 2 | 0.0758048872207 | 0.0320776730735 |
| revert_position | 10 | 0.5 | 0.1 | 0.06 | -0.0589750736476 | 0.166857633942 |


Trong phép đối chiếu này, mất mát lớn nhất khi revert_position,
ΔK=0.166857633942 bit/use.
Đây là xếp hạng cục bộ giữa các bước thay đổi khác độ lớn và có tương tác,
không phải độ nhạy toàn cục hay chứng minh một parameter luôn quan trọng nhất.
Đường Dr trong diameter_comparison.csv giữ cố định mọi geometry còn lại.
Trong toàn bộ các điểm secondary đã thử, K lớn nhất là 0.274588751239
bit/use tại Dr=0.6 m, VA=10.0, zenith=0.0°,
full divergence=10.0 µrad, jitter=0.5 µrad,
σh=0.03 m. Điểm này khác với mục tiêu giữ receiver nhỏ 30 cm;
không mặc định khả thi về tải trọng. Nếu VA tốt nhất chạm nguồn VA lớn nhất đang có,
đỉnh theo VA vẫn chưa được bracket đầy đủ.

## Trả lời Q1–Q6

1. **Uniform có K dương?** Chưa tìm thấy với primary Eq. (10) gốc;
   có với secondary bounded, cùng quy ước noise-v43 và Gaussian-effective homodyne.
2. **Cấu hình nhỏ nhất đã thử cho kết quả dương?** Dr=0.3 m,
   full divergence=10.0 µrad, jitter=0.5 µrad,
   σh=0.03 m, zenith=0.0°, VA=3.0,
   K=0.107882560294. Chỉ là nhỏ nhất trong aperture được thử, thuộc secondary.
3. **Giữ Dr=30 cm được không?** Được trong secondary; chưa có positive primary.
4. **Cải thiện nào lớn nhất?** Bảng ablation định lượng tác động cục bộ; phải cải thiện
   tracking/stabilization để dùng jitter 0.5 µrad và vị trí 3 cm.
   Không suy từ positive secondary sang primary hoặc từ aperture sang khả năng mang tải.
5. **MB còn lợi thế bao nhiêu?** Gshaping secondary=0.402702914836
   bit/use; primary=0.0673890327319 bit/use
   tại đúng geometry tương ứng, với cùng luật kênh cho mỗi phép trừ.
6. **Kết quả nào qua kiểm tra?** Có 135 context/source được kiểm tra chọn lại,
   1620 kiểm tra MI/Holevo/covariance đã lưu; mass gate áp dụng cho tất cả context.
   Positive secondary qua các kiểm tra số và support/normalization của chính luật đó,
   nhưng toàn bộ kết quả vẫn UNVALIDATED_SECURITY_MODEL.

## Giới hạn nguồn tính toán, kỹ thuật và bảo mật

Các điểm mới yêu cầu đã có nguồn chính xác.
Hai lần khởi động backend gmpy2 bị Windows Application Control chặn trước
khi tính C,w. Không vô hiệu hóa hoặc đi vòng policy. Fallback dùng backend Python chuẩn,
giữ nguyên full-support C4 và ladder 1050/1250/1450 chữ số, timeout 3600 s;
trạng thái và thời gian từng tác vụ nằm trong completion_receipt/source_attempts.
Không nội suy, không điền C,w/SKR cho điểm thiếu, không đổi precision để lấy positive.
Exact-source ở đây là nhánh full-support đã xác thực, không phải nghiệm giải tích
vô hạn chữ số. Worker gốc yêu cầu hai mức cuối resolve đủ rank 256 và
|Δx|≤1e-7+1e-6 max(|x1250|,|x1450|), x=C,w; receipt giữ nguyên các hàng precision.
Tolerance xác thực ensemble/VA và tiêu chí hội tụ C,w là hai kiểm tra khác nhau.

Div=10 µrad tương ứng w0≈0.098676 m, đường kính phát chứa 99% công suất
khoảng 0.2995 m ở HAP, tính theo cùng Gaussian optics.
Ở L=19 km, jitter 0.5 µrad cho dịch điểm 1σ=0.0095 m và
σs=√(σh²+(L θjt)²)=0.0314682379551 m khi σh=0.03 m.
Các SD và giả thiết độc lập của motion/jitter/AoA được giữ theo mô hình;
chưa có phép đo để xác nhận tương quan giữa chúng.
Receiver 30 cm và jitter/position cải thiện là giả thiết thiết kế, chưa có bằng chứng
khối lượng, công suất, bandwidth PAT hay tải trọng UAV. Đường Dr lớn không phải chứng nhận
thiết kế bay khả thi; không có dữ liệu phần cứng để bảo đảm yêu cầu này.

Các khoảng full-Z có kiểm tra số, chưa phải enclosure toàn cục. Gaussian effective
fading closure, quy ước noise tại outage, attack class/CSI, parameter estimation,
finite size, reconciliation thực và composable security còn chưa được chứng minh.
Giữ NOT_READY_FOR_PUBLICATION_SCALE_RUNS, ObjectiveC USER_STOPPED và blocker
frozen-hash: actual df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15,
khác historical expected 561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1.
Không đổi scientific source/production code/security functional/frozen spec/config hay cache cũ;
không training, test/held-out/publication evaluation, baseline/threshold approval, commit/push.

## Artifact và đọc hình

- candidate_comparison.csv: 18373 hàng, gồm mọi source evaluation và
  context bị chặn; K âm giữ nguyên, rate thiếu để trống. source_catalog.json liên kết ensemble/payload hash.
  Có 0 source evaluation lỗi covariance/information, lưu riêng
  trong candidate_failures.json và có exclusion_reason trong CSV; không dùng làm positive.
- stage_A_final.csv: VA tốt nhất đã thử theo từng góc và lý do loại.
- diameter_comparison.csv: cùng zenith/divergence/jitter/position cho tất cả aperture;
  primary và secondary có cột channel_law tách biệt.
- three_scheme_comparison.csv, three_scheme_zenith.csv: cùng kênh/noise, fixedMB rõ nguồn.
- Figures 1–3: PNG350dpi/PDF vector, log-y chỉ K>0 đã kiểm tra;
  NaN tạo ngắt tại các khoảng âm/invalid. Figure 1 ghi riêng primary baseline không có positive
  và secondary cải thiện optics; không diễn giải đây là một đường dùng lẫn hai laws.
  Figure 2 có primary mass-blocked và secondary theo cùng geometry.
  Figure 3 chỉ secondary, 3 schemes cùng physical channel.
- selected_validation/, bounded_moment_validation.json, independent_bounded_validation.json,
  guard_checks.json và verification.json chứa kiểm tra; verify.py chỉ đọc artifact, không rerun số.

Các artifact lịch sử được kiểm hash từ startup_manifest trước và sau công việc.
Các hash ledger trong receipt cũ là snapshot lịch sử; không sửa receipt cũ khi cập nhật ledger
cho nhiệm vụ mới. Tái lập các phase vào namespace mới, không ghi đè các receipt đã hoàn tất.
