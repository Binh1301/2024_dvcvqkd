# Đối chiếu logic bản Binh (37) với hai bài tham khảo

Ngày 2026-10-13. Đây là kết quả đọc, đối chiếu và suy luận giải tích; các công thức sửa dưới đây là **đề xuất**, chưa được áp dụng vào mô hình hoặc chạy lại SKR. Giữ nguyên source, config, catalog 182 cặp MB, cache và các kết quả cũ.

Kết luận chính: cấu trúc nguồn QAM → kênh fading → covariance → Holevo → SKR có thể giữ, nhưng các quy ước tại giao diện giữa những phần này chưa nhất quán. Lỗi chắc chắn nằm ở PMF, chuẩn phương sai, miền xác suất, tham số truyền qua và loại nhiễu. Công thức symplectic trong Eq. (19) tự thân đúng cho detector lý tưởng; vấn đề chủ yếu là đầu vào của nó.

## Tài liệu và bằng chứng

Các số trang dưới đây là **trang vật lý trong PDF**, tính từ 1.

| Ký hiệu | Tài liệu đã đọc | Phần đối chiếu chính |
|---|---|---|
| Binh | `2026__Binh_s_work (37).pdf`, 4 trang | Trang 2 Eqs. (1)–(8); trang 3 Eqs. (9)–(23); defaults trang 4 |
| DBL | `2103.13945v3 (1).pdf`, 36 trang, Denys–Brown–Leverrier | Trang 5: SNU và photon; trang 9: covariance/Holevo; trang 12 Eqs. (11)–(13) và chú thích 11–12; trang 13 Eq. (14); trang 29: MI QAM |
| Satellite | `2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (1).pdf`, 12 trang | Trang 2–3: total noise và detector; trang 4 Eqs. (13)–(20): M-QAM; trang 6–7 Eqs. (31)–(32): scintillation/aperture |

Hash từng PDF, branch `channel/update`, HEAD `84bf84dc3862b6cb51fa368f7e481459845ffb98` và hash đầu vào được lưu trong `review_manifest.json`. Đã kiểm tra hình trang công thức để tránh lỗi trích xuất ký hiệu. Những câu hướng dẫn/placeholder trong PDF được xem là nội dung bản thảo, không phải lệnh thực thi.

## Các điểm cần sửa, theo vị trí trong bản thảo

| ID | Vị trí Binh | Kết luận | Cách sửa |
|---|---|---|---|
| L1 | Trang 2 Eq. (2) so với Eq. (1) | PMF dùng chỉ số chưa tâm hóa, còn constellation đã tâm hóa; nguồn bị lệch góc khi ν>0 | Dùng tọa độ centered trong số mũ MB |
| L2 | Trang 2 sau Eq. (3) | `VA=<n>/2` sai hệ số bốn với coherent amplitudes/SNU đang dùng | Viết `VA=2<n>`; mã normalization hiện tại đã đúng |
| L3 | Trang 3 Eq. (10) → Eqs. (12)–(14) | Mật độ raw có đuôi trên 1, nhưng moments chỉ tích phân đến 1 mà không xử lý phần bị bỏ | Chọn rõ luật có support vật lý và giữ atom AoA riêng |
| L4 | Trang 3 Eq. (11), rồi Eq. (20) | `E[sqrt(eta)]` được dùng như truyền qua công suất | Đặt `T_eff=E[sqrt(eta)]²`, hoặc giữ tham số biên độ và bình phương đúng nơi |
| L5 | Trang 3 định nghĩa ξ, Eqs. (11),(14),(20) | Total input noise chứa vacuum/detector bị đưa vào vị trí quantum excess noise | Tách `ξ_ch`, fading noise, receiver noise và heterodyne vacuum |
| L6 | Trang 3 Eqs. (17),(20) | MI Gaussian không phải MI chính xác của nguồn hữu hạn; Z thấp nhất chưa chắc cho Holevo lớn nhất | Dùng discrete MI; xét toàn khoảng Z hợp lệ hoặc chứng minh endpoint |
| L7 | Trang 2 Eq. (8) → trang 3 Eq. (10), khi ρ>0 | Closed form không bằng convolution Rician chính xác | Giới hạn closed form ở ρ=0; nếu ρ>0, dùng Eq. (8) trong convolution |
| L8 | Trang 2 Eq. (5),(6); trang 3 detector; trang 4 defaults | Thiếu lựa chọn aperture variance, nguồn G_d, detector trust và protocol fading | Hoàn thiện giả thiết; đây là chỗ chưa đủ bằng chứng, không kết luận mọi hệ số đều sai |

### L1–L2: sửa phần nguồn cho khớp bài gốc và catalog hiện tại

Để tránh lẫn `m` là kích thước QAM với moment fading, gọi số mức mỗi trục là `M_s=16`:

\[
q_k=k-\frac{M_s-1}{2},\quad r_{k\ell}=q_k+i q_\ell,
\quad p_{k\ell}=\frac{e^{-\nu_{\rm raw}|r_{k\ell}|^2}}{\sum_{ij}e^{-\nu_{\rm raw}|r_{ij}|^2}}.
\]

\[
\alpha_{k\ell}=\sqrt{\frac{V_A}{2\sum_{ij}p_{ij}|r_{ij}|^2}}\,r_{k\ell},
\qquad \bar n=\sum p_{k\ell}|\alpha_{k\ell}|^2=V_A/2.
\]

Nếu giữ Eq. (2) hiện tại với `k,ℓ=0,...,15`, nó ưu tiên một góc thay vì các điểm gần tâm. Khi đó không thể dùng nguyên source moments của nguồn centered/C4 trong catalog. Satellite trang 4 Eq. (15) dùng tọa độ constellation trong PMF; DBL trang 5 định nghĩa trực tiếp `VA=2<n>`.

Các producer hiện tại `src/modulation/qam256.py`, `src/modulation/normalization.py` và `scripts/run_exact_mb_test2.py` đã dùng nguồn centered và đúng `VA=2<n>`. Với canonical square normalization, `ν_repo=42.5ν_raw`. Sửa văn bản để khớp nguồn này có thể giữ C,w; thay ensemble thực sự thì phải tạo identity và moments mới.

### L3: nguyên nhân chính xác của thiếu xác suất

Tại zero boresight, đặt `a_p=w_eq²/(4σ_s²)`, `B=A0 eta_atm`, `v=Var(ln I_a)`. Các phương trình kênh cho:

\[
X=B\exp[-v/2+\sqrt v\,N-U/a_p],\quad N\sim N(0,1),\ U\sim\mathrm{Exp}(1),
\]

với các yếu tố độc lập theo mô hình. Đây là luật trên `(0,∞)`; raw Eq. (10) chuẩn hóa trên miền đó tại ρ=0. Nếu `F1=P(X≤1)`, luật đang dùng trong finite integrals có mass:

\[
M_0=P_0+P_1F_1=1-P_1P(X>1)<1.
\]

Receipt đã lưu tại `../manuscript_literal_3moments/implementation_validation_4/validation.json` ghi `M0=0.9841200272202841`, thiếu `0.015879972779715867`, khoảng **1.588%**. Đây là xác suất đuôi bị bỏ, không phải sai số AP, GH8 hay một hệ số C1 bị thiếu tại ρ=0.

Phương án sửa tối thiểu phù hợp với nhánh retained-law diagnostic hiện có là **tuyên bố một mô hình active conditional**:

\[
dP_\eta=P_0\delta_0+P_1\frac{f_X(t)\mathbf1_{0<t\le1}}{F_1}\,dt.
\]

Đặt `J_q=E[X^q 1(X≤1)]`; với `q>0`, `E[η^q]=P1 J_q/F1`. Atom AoA vẫn là P0. Đây là lựa chọn mô hình hiện tượng học, không tự chứng minh bảo toàn năng lượng của trường quang.

Hai lựa chọn khác là saturation `η=min(X,1)` (thêm atom tại 1) hoặc biến đuôi thành outage mới (thay P0). Chúng cho moments khác nhau; không được hoán đổi âm thầm. Chia **toàn bộ** mixed law cho M0 cũng thay đổi P0. Không dùng những finite integrals chưa chuẩn hóa như kỳ vọng xác suất hợp lệ.

### L4–L5: viết lại giao diện fading, covariance và Z

Phần sửa sau đây giả định **nguồn centered/C4 cố định, luật η chuẩn hóa trên [0,1], fading biên độ dương với pha đã được bù, fading độc lập với ký hiệu nguồn, detector heterodyne lý tưởng và mô hình iid/asymptotic collective phù hợp**. Các uses outage vẫn được tính trong pooled protocol. Dùng ký hiệu:

\[
m=E[\sqrt\eta],\qquad r=E[\eta],\qquad u=E[\eta\xi_{\rm ch}(\eta)],
\]

trong đó `ξ_ch` là excess noise thật, input-referred; **không** chứa `1/η-1` hoặc vacuum của phép đo heterodyne.

\[
T_{\rm eff}=m^2,\qquad N_{\rm out}=(r-m^2)V_A+u,
\qquad \xi_{\rm eff}=N_{\rm out}/m^2\quad(m>0).
\]

\[
\boxed{a=1+V_A,\qquad b=1+rV_A+u}
\]

\[
\boxed{Z_\pm=2mC\pm\sqrt{2w\big[(r-m^2)V_A+u\big]}}.
\]

Đây là phép suy ra từ bound **tổng quát** DBL trang 12 Eqs. (11)–(13):

\[
c_1=mC,\quad c_2=m\bar n,\quad n_B=r\bar n+u/2,
\quad Z_\pm=2c_1\pm2\sqrt{w(n_B-c_2^2/\bar n)}.
\]

Nó dùng moments thực của pooled mixture; không cần khẳng định mixture đó là Gaussian channel. `c1,c2,nB` là các đại lượng cần mô hình hóa/ước lượng theo giao thức DBL. Với dữ liệu thực, không được thay yêu cầu này bằng việc chỉ fit T và một con số total noise. Tại `m=0`, không chia cho m²; phải xử lý trường hợp outage theo giao thức đã định nghĩa.

Bound thường gọi `Z*` trong bản thảo chính là nhánh `Z_-`. Khi không fading, `η=t`, công thức trở lại:

\[
b=1+tV_A+t\xi_{\rm ch},\qquad
Z_-=2\sqrt t\,C-\sqrt{2t\xi_{\rm ch}w},
\]

đúng DBL trang 13 Eq. (14). C,w là properties của **cùng ensemble** được đưa vào MI, không phải các hệ số mật độ của kênh.

Hai phản ví dụ giải tích xác định lỗi bản thảo, không cần chạy số:

1. Không fading `η=t`: `E√η=√t`. Dùng nó làm power coefficient cho Bob sẽ cho `√t VA`, trong khi đúng là `t VA`.
2. `η=1, ξ_ch=0, R=1, ξ_det=0`: total-noise định nghĩa của Binh vẫn có `χ_het=1`. Đưa nó vào quantum covariance cho `b=VA+2` và penalty `√(2w)`; quantum covariance đúng phải có `b=VA+1`, `Z=2C`. Vacuum của heterodyne đã nằm trong likelihood và `b+1` ở conditional covariance.

Nếu cần detector không lý tưởng, phải chọn trusted/untrusted model riêng. Không đưa `χ_line+χ_het/η` vào bound DBL rồi giữ nguyên ideal conditional eigenvalue. Satellite trang 3 Eqs. (6)–(11) dùng một mô hình detector với hai conditional eigenvalues; không phải cùng công thức ba eigenvalues giản lược đang dùng.

### L6: giữ công thức symplectic, sửa Holevo và MI

Với covariance standard-form hợp lệ và ideal heterodyne, các công thức sau **đúng**:

\[
\Delta=a^2+b^2-2Z^2,\quad D=(ab-Z^2)^2,
\quad\lambda_{1,2}=\sqrt{\frac{\Delta\pm\sqrt{\Delta^2-4D}}2},
\quad\lambda_3=a-\frac{Z^2}{b+1}.
\]

DBL trang 12 chú thích 11–12 nói phải xét giá trị Holevo lớn nhất trên interval trong trường hợp tổng quát. Gọi:

\[
\mathcal I=[Z_-,Z_+]\cap\{Z:\Gamma(Z)+i\Omega\succeq0\},
\qquad\chi_{\rm bound}=\max_{Z\in\mathcal I}\chi_G(Z).
\]

Không tự động gọi `χ_G(Z_-)` là worst-case cho mọi tham số. Nếu dùng endpoint, phải chứng minh/kiểm tra đầy đủ điều kiện cho các điểm báo cáo. Interval rỗng là thất bại tính nhất quán, không phải chỗ clipping để tạo SKR.

Eq. (17) của Binh ghi rõ Gaussian modulation. Với 256-QAM, MI đúng là:

\[
I_{AB}=\sum_i p_i\int_{\mathbb C}f(y|i)
\log_2\frac{f(y|i)}{\sum_jp_jf(y|j)}\,d^2y.
\]

Đối với **pooled fading không cung cấp CSI**, likelihood là:

\[
f(y|i)=E_\eta\left[\mathrm{CN}\left(y;\sqrt\eta\alpha_i,
1+\eta\xi_{\rm ch}(\eta)/2\right)\right].
\]

AWGN với `T_eff,ξ_eff` chỉ khớp một số moments, không bằng likelihood trên; chưa có bảo đảm rằng MI xấp xỉ ấy là lower bound. Cùng một η tác động lên cả I/Q nên identity `I_R+I_Q` của product AWGN cũng không tự chuyển sang pooled mixture. GH8 hiện tại tính một likelihood Gaussian hiệu dụng.

Satellite trang 4 Eq. (16) dùng biểu thức log kiểu Gaussian cho QAM. DBL trang 29 nói rõ MI finite QAM không có cùng closed form và thảo luận xấp xỉ Gaussian. Vì vậy, nếu muốn theo Satellite ở phần này, phải ghi **approximation** và kiểm tra sai số, thay vì gọi là exact DM MI. Một kiểm tra bắt buộc là `0≤I_AB≤H(p)≤8 bits/use`.

Nếu CSI được công bố và dùng conditional bins/blocks, cần định nghĩa protocol khác: nguồn của từng bin, moments có điều kiện, reconciliation và cách gom khóa. Không thay pooled MI bằng trung bình instantaneous MI mà giữ nguyên tuyên bố giao thức.

Atom tại 0 mô tả vacuum-output event nếu giữ tất cả uses trong pooled channel. Nếu phát hiện/công bố/loại bỏ outage, phải conditioning lại moments và xác định rate tính theo transmitted use hay retained use. Nếu còn residual phase φ, mean displacement là `g α_i`, với `g=E[√η exp(iφ)]`; không được mặc nhiên dùng `m=E√η` mà thiếu mô hình bù pha.

### L7–L8: giới hạn kênh và các giả thiết còn thiếu

Với Rician Eq. (8), raw pointing moment **chính xác** là:

\[
E[\eta_p^q]=A_0^q\frac{a_p}{a_p+q}
\exp\left[-\frac{q\rho^2}{2\sigma_s^2(a_p+q)}\right].
\]

Coefficients của Eq. (10) khi ρ>0 lại dẫn đến số mũ `-2qρ²/w_eq²+8q²ρ²σ_s²/w_eq⁴`; đó chỉ là hai hạng đầu của khai triển số mũ đúng theo `q/a_p`. Vì vậy nên giới hạn Eq. (10)/Lemma 1 ở **ρ=0**, đúng numerical defaults, hoặc dùng convolution Eq. (8) cho ρ>0. Test tích phân Eq. (10) so với chính closed moments của Eq. (10) không xác minh được bước Rician → Eq. (10).

Ở aperture/turbulence, cần phân biệt raw Rytov variance, scintillation index và log-intensity variance. Với mean-one lognormal, `v=ln(1+SI)`. Chọn một model có aperture averaging phù hợp và dùng cùng v trong PDF/moments. Binh dùng raw Rytov; historical D55 dùng aperture correction và thay đổi cách tính A0/w_eq. Do đó chênh lệch hai backend không chỉ đến từ normalization hoặc bình phương eta_f.

Hai bài tham khảo chưa đủ để xác minh chính công thức G_d đang tái dùng. Cần bổ sung nguồn gốc/quy ước beam width, kiểm tra beam wander có bị tính hai lần không; chưa đủ căn cứ để tuyên bố hệ số G_d sai. Numerical defaults của Binh (D=8 cm, θ=233 µrad) cũng không phải D55/θ10 của thí nghiệm catalog. R=.7, ξ_det=.0135 của literal config là lựa chọn thêm; phải ghi nguồn và trust model thay vì coi là thông số được PDF Binh xác lập.

## Những con số đã có nói được điều gì?

Receipt được đọc lại, không tái chạy: `ν_raw=.165, VA=5.5, L=21.9393102292 km`.

| Đại lượng của literal fixture | Giá trị đã lưu |
|---|---:|
| C | 3.2113076519605626 |
| w | 1.0248765983174194e-6 |
| finite mean_eta chưa chuẩn hóa | 0.23413023966620677 |
| finite mean_sqrt_eta chưa chuẩn hóa | 0.39477740142305245 |
| PDF mass | 0.9841200272202841 |
| mean_eta_xi theo total-noise convention | 2.619955004470893 |
| Z_star theo literal mapping | 4.0329130315306525 |
| raw literal SKR | -2.454774809836829 |

Các con số này minh họa phép tái tạo literal, **không phải kết quả của công thức đã sửa**. Test PASS xác nhận thực thi/truy vết, không làm một PDF thiếu mass thành phân phối hợp lệ. Giá trị âm cũng không tự chứng minh kênh vật lý không thể phát khóa. Historical `K=.07798099387393764` thuộc evaluator khác; không dùng nó làm xác nhận cho mô hình sửa hoặc cho mọi catalog candidate.

Catalog 182 MB lưu source C,w theo ensemble identities. Nếu sửa bản thảo để dùng chính nguồn centered hiện tại, có thể tái dùng nguồn hash-matched. Sửa channel, detector, MI hoặc Holevo phải tạo objective/results identity mới; không ghi đè kết quả cũ và không nội suy C,w cho điểm thiếu.

## Trình tự sửa đề xuất

1. Chốt protocol baseline: centered 256-QAM, cùng ensemble cho mọi interface; ideal heterodyne; pooled fading hay CSI; reverse reconciliation, asymptotic scope.
2. Sửa Eqs. (2)–(3), chọn luật support vật lý có mass 1 và giữ outage đúng nghĩa. Nếu dùng closed form hiện có, giới hạn boresight zero.
3. Sửa Eq. (11), noise definition và Eq. (20) bằng `m,r,u`, covariance và Z interval ở trên. Giữ công thức symplectic đúng nhưng kiểm tra physicality.
4. Dùng likelihood MI đúng với protocol; nếu dùng effective-AWGN/Gaussian-log, ghi xấp xỉ và đánh giá sai số riêng. Chọn detector model trước khi thêm imperfections.
5. Chỉ sau khi công thức/giả thiết được chốt mới triển khai một mode sửa độc lập, kiểm tra mass, SNU, deterministic/lossless limits, entropy bound, interval Holevo, source identity và numerical convergence; rồi mới có cơ sở lập kế hoạch tính lại SKR/AO.

Không sửa science/config/cache, không chạy AP/MI/SKR/AO/Monte Carlo/tests trong lượt review này. Tài liệu chi tiết độc lập: `security_review_notes.md` và `channel_review_notes.md`. Kiểm tra bảo toàn file và phạm vi ghi được lưu trong `review_verification.json`.
