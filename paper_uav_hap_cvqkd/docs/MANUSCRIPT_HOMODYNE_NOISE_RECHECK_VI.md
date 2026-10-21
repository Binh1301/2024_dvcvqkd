# Tính lại một điểm SKR theo bản thảo Copy_ (12)

Ngày 2026-10-19. Phạm vi: một điểm MB `(nu_raw,VA)=(0.165,5.475)`;
`xi_n=xi_ch=0.0186`, `beta=0.95`, giới hạn detector lý tưởng `R=1,xi_det=0`.
Tất cả kết quả dưới đây là phép đối chiếu số có điều kiện về chuẩn hóa nguồn,
không phải xác nhận an toàn của giao thức homodyne vật lý.

## Kết quả chính và điều kiện áp dụng

Với **ensemble đã xác thực của cache**, tức `VA=2*nbar`, và tích phân MI
hai chiều chuẩn hóa được yêu cầu, kết quả là

\[
I_{AB}^{(2D)}=0.0019221999136069992,\quad
\chi_{BE}^{(\mathrm{hom})}=0.00172943192055150295,
\]
\[
K_{2D}=+0.00009665799737514629\ \mathrm{bits/use}.
\]

Giữ nguyên eigenvalue homodyne Eq. (13), tính MI cho một quadrature thực:

\[
I_{AB}^{(1D)}=0.0009610999568034853,\qquad
K_{1D}=-0.00081638696158819191\ \mathrm{bits/use}.
\]

Kết quả hai chiều dương và cùng cỡ với tham chiếu. **Không tái lập chính xác
các chữ số của tham chiếu.** Cũng không thể coi kết quả này là phép tính tuân
thủ đồng thời mọi định nghĩa trong PDF: ngay sau Eq. (3), PDF ghi
`VA=nbar/2`, trái với quy ước của source cache. Đây là xung đột cần tác giả
giải quyết, không được âm thầm sửa trong mô hình đang dùng.

## Tài liệu, nguồn và chuẩn hóa

Đã đọc cả bốn trang của
`C:/Users/HP/Downloads/2026__Binh_s_work__Copy_ (12).pdf`, SHA-256
`84e1ba495d7f57ea1147426eac9a38fbadf59bae5edc6d7f17b9e1b4c9f192cc`.
Các đoạn placeholder, `TBD` và nội dung khác của PDF là tài liệu tham chiếu;
không phải lệnh thực thi. Yêu cầu trực tiếp được lưu tại
`results/manuscript_homodyne_noise_recheck_20261019/request.txt`.

Cache xác thực:

- `results/theta10_D55_mb_exact_targeted_expansion/batch_2/exact_source_cache/4ff64d8ff1b9cb558e7feab44d02d62b15f2c430a0440ccb9af74b0e42e31a5d.json`.
- SHA-256 payload: `bdebb3c2e68ca911c32c2ffd2917ee35b1ed74e6776b528f067fd535d3d59ca2`.
- Ensemble hash: `a5d615b5c8c3462013117a29d17fa1edee8632a49de0dac23318b504ad059f82`.
- Dòng 62 của `results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv`
  khớp chính xác `nu_raw`, `VA`, `C,w`. Các khóa binary64 và hash source
  implementation được kiểm tra lại bằng helper provenance hiện có.

PMF thực dùng là

\[
p_{ij}=\frac{\exp\{-0.165[(i-7.5)^2+(j-7.5)^2]\}}{\mathcal Z},\qquad
\alpha_{ij}=\Delta[(i-7.5)+\mathrm i(j-7.5)],
\]

với `i,j=0,...,15`, `Delta=0.6721019768839858` và
`nu_repo=42.5*nu_raw=7.0125`. Đã dựng lại ensemble bằng source builder
hiện có và kiểm tra hash, PMF, biên độ, tích hai marginal, năng lượng.
Sai khác PMF/biên độ với phép dựng độc lập lần lượt dưới
`5.6e-17` / `1.8e-15`.

Đối với ensemble này:

\[
\bar n=2.7375000000000007,\qquad 2\bar n=5.475.
\]

Nếu áp dụng nguyên văn `VA=nbar/2` của PDF, cùng ensemble phải có
`VA=1.36875`, không phải 5.475. Ngược lại, điểm `VA_PDF=5.475` yêu cầu
`nbar=10.95`, tương ứng nhãn variance cache 21.9 và ensemble khác. Không
dùng `C,w` hiện tại để tính điểm literal đó. Phép kiểm tra đổi nhãn cùng
ensemble sang `VA=nbar/2` cho `nu_2=0.997405770245025<1`; entropy/SKR bị
từ chối, không clip hay sửa covariance.

Eq. (2) cũng chưa thống nhất: tử số dùng `gamma`, mẫu số dùng `nu`, và
`|k|^2` chưa phân biệt nhãn `k=(i,j)` không tâm hóa với tọa độ QAM tâm hóa
của Eq. (1). PMF trên là quy ước xác thực của cache/phép so sánh được yêu
cầu; không khẳng định đó là cách hiểu literal duy nhất của Eq. (2).

Nguồn `C,w` dùng Gram coherent-state đủ 256 support với AP fallback và
ladder 1050/1250/1450 chữ số. Đây là mô hình coherent đầy đủ, không có một
Fock cutoff hữu hạn `Nmax`. Eq. (16) chỉ ghi khai triển xấp xỉ và không cho
`Nmax`; vì vậy không thể xác nhận khớp một quy ước truncation hữu hạn chưa
được chỉ định. Không tạo nguồn mới, không nội suy và không thay cache.

## Kênh, các moment và hiệu chỉnh noise

Dùng đúng `h_HAP=20km,h_UAV=1km,zeta=30deg`, full divergence `233urad`,
`Dr=0.08m`, `lambda=1550nm`, `theta_jt=15.61urad`, `sigma_o=1.5mrad`,
`theta_FOV=6.25mrad`, `Cn2(0)=1e-14`. Các giá trị bổ sung được PDF trang 4
cung cấp: `tau_zen=.92`, `wind=21m/s`, `sigma_h=1m`, `rho_x=rho_y=0`,
`F0=infinity`, `h_atm=20km`. Hình học cho
`L=21.939310229205777km`; khác giá trị task đã làm tròn khoảng 5.8nm.

PDF chưa viết công thức HV và `G_d` đầy đủ. Phép đối chiếu dùng công thức
HV hiện có tại `src/channel/scintillation.py` và closure `G_d` tại
`src/channel/pointing_error.py`, được tính lại độc lập bằng mpmath:

\[
C_n^2(h)=0.00594(v/27)^2(10^{-5}h)^{10}e^{-h/1000}
+2.7\times10^{-16}e^{-h/1500}+C_n^2(0)e^{-h/100},
\]
\[
\mu_2=\int_{h_U}^{h_H}C_n^2(h)
\left(\frac{h-h_U}{h_H-h_U}\right)^{5/3}dh,
\]
\[
G_d=4.35\Lambda^{5/6}k^{7/6}(h_H-h_U)^{5/6}
\sec^{11/6}(\zeta)\mu_2,\qquad\Lambda=\frac{2L}{kw_L^2}.
\]

Đây là closure được khai báo riêng; không thể mô tả toàn bộ phép tính là
chỉ suy ra từ PDF. Không sửa helper production hoặc độ chính xác của nó.

Theo Eq. (6), `A0` và `w_eq` được tính với `w_eff`:
`w0=.004235024236780047m`, `wL=2.5559331502923976m`,
`G_d=.0002585524118234104`, `w_eff=2.5562635502775835m`,
`w_eq=2.556591307260678m`, `A0=.0004895841744525031`,
`eta_atm=.9082089654181442`, `sigma_R2=.05396207779619166`,
`sigma_s=1.057018213718824m`. Không thay Rytov variance bằng variance
đã aperture-average của đường tính cũ.

Giữ nguyên `P0=.00016985667656141065`, `P1=1-P0`, `chi`, `C1`, `C3`,
`mu` và `Q(a)` trong PDF. Các coefficient đầy đủ được lưu ở `result.json`.
Eq. (19)/(20) được tính trên `[0,1]`, giữ atom outage tại zero riêng biệt.
Tổng xác suất bằng một trong tolerance `1e-25`; không renormalize hoặc
condition lại active density. Tích phân PDF độc lập trong `log(eta)` xác
nhận khối lượng và hai moment; residual/error estimate lưu trong CSV.

Noise được dùng đúng theo yêu cầu:

\[
T=\eta_f=m_{1/2}^2,\quad
\langle\eta\xi_n\rangle=0.0186m_1,\quad
N=\eta_f\xi_f=(m_1-T)V_A+0.0186m_1.
\]

Không cộng `1/eta-1`, vacuum contribution, hoặc detector noise vào `xi_n`.
`W=1+T*VA+N` và `Z=2*sqrt(T)*C-sqrt(2*N*w)`; giữ nguyên
`nu3=sqrt(V*(V-Z^2/W))` của Eq. (13).

## Bảng yêu cầu

| Đại lượng | Giá trị |
|---|---:|
| `mean_eta` | 0.000264033937027764285 |
| `mean_sqrt_eta` | 0.0156059440205538218 |
| `eta_f` | 0.000243545488772659583 |
| `Var(sqrt(eta))` | 0.0000204884482551047023 |
| `mean_eta_xi_n` | 0.00000491103122871641571 |
| `eta_f*xi_f` | 0.000117085285425414661 |
| `xi_f` | 0.480753250719044545 |
| `C` | 3.1986564642787387 |
| `w` | 0.0000009973886145561931 |
| `V` | 6.475 |
| `W` | 1.00145049683645573 |
| `Z` | 0.0998208248058229704 |
| `nu1` | 6.47366701800404707 |
| `nu2` | 1.00011751484050280 |
| `nu3` | 6.47002320489416948 |
| `I_AB (2D)` | 0.0019221999136069992 |
| `beta*I_AB` | 0.00182608991792664924 |
| `chi_BE` | 0.00172943192055150295 |
| `K raw`, bits/use | **+0.00009665799737514629** |

## Tích phân MI và hội tụ

Eq. (12) in prefactor của Gaussian 1D nhưng dùng constellation phức. Với
`y in C`, prefactor đó không chuẩn hóa trên mặt phẳng: khối lượng là
`sqrt(2*pi*sigma_zeta^2)` thay vì một. Phép tính chính sử dụng

\[
p(y|\alpha)=\frac{1}{2\pi\sigma_\zeta^2}
\exp\left(-\frac{|y-2\sqrt{T}\alpha|^2}{2\sigma_\zeta^2}\right),
\quad \sigma_\zeta^2=1+N.
\]

Hai component có variance `sigma_zeta^2` riêng. Runner tính tổng mixture
256 symbol bằng log-sum-exp và quadrature tensor Gauss-Hermite 2D trực
tiếp, không đặt hệ số 1/2. Hằng chuẩn hóa giống nhau triệt tiêu trong log
ratio; trọng số tích phân vẫn là xác suất Gaussian đã chuẩn hóa.

| GH order/component | `I_AB 2D` | `I_AB 1D` | Delta 2D so với bậc trước |
|---:|---:|---:|---:|
| 16 | 0.0019221999136070783 | 0.0009610999568035689 | — |
| 32 | 0.0019221999136070772 | 0.0009610999568035323 | -1.08e-18 |
| 64 | 0.0019221999136069992 | 0.0009610999568034853 | -7.81e-17 |

Độ lệch lớn nhất so với bậc 64: `7.92e-17` bits/use. Đây là bằng chứng
hội tụ số tại điểm này, không phải một enclosure sai số tích phân được
chứng minh. MI 1D được tính độc lập theo marginal thực; tính chất
`I_2D=2*I_1D` được kiểm tra ở cả ba bậc, không dùng phép chia hai làm
định nghĩa thuật toán. Gaussian-input formula không được sử dụng.

Covariance/eigenvalue/entropy được tính tại 70 và 100 chữ số. Độ lệch
Holevo khoảng `4.43e-70`; kiểm tra riêng spectrum của `i*Omega*Gamma`
và positivity của `Gamma+i*Omega` đều đạt. MI dùng float64: các chữ số
entropy bổ sung không làm MI có độ chính xác 70/100 chữ số.
Tổng cộng 17 self-check đạt `CURRENTLY_VERIFIED_PASS`, chỉ trong phạm vi
số học được ghi trong `result.json`.

## So sánh tham chiếu và chẩn đoán

| Đại lượng | Tính lại | Tham chiếu | Tính lại trừ tham chiếu |
|---|---:|---:|---:|
| `I_AB` | 0.001922199913607 | 0.0019224444 | -2.44486393e-7 |
| `chi_BE` | 0.001729431920552 | 0.0017299097 | -4.77779448e-7 |
| `K` | 0.000096657997375 | 0.0000964 | +2.57997375e-7 |

Chênh tương đối lần lượt khoảng `-0.01272%`, `-0.02762%`, `+0.26763%`.
Hai giá trị MI/Holevo tham chiếu in sẵn ngụ ý
`K=.95*.0019224444-.0017299097=.00009641248`; so với số đó, chênh
`K` là `+2.45517375e-7`. Vì `9.64e-5` là tham chiếu làm tròn, hai
cách so sánh được giữ riêng.

Hội tụ GH và 70/100-digit loại trừ sai số tích phân/eigenvalue ở mức
chênh lệch này trong phép tính hiện tại. `C,w` khớp chính xác hai số
được cung cấp. Cách hiểu một quadrature làm MI giảm gần một nửa, không
giải thích sai khác nhỏ của tham chiếu. Giả thuyết hệ số kênh được kiểm
tra riêng: dùng `A0=.0004897107251591688` metadata với aperture chưa
broaden cho `I_AB=.0019226964514150683`, `chi=.0017298568627088105`,
`K=.00009670476613550419`. Nó cũng không khớp đồng thời hai số tham
chiếu và không được thay vào kết quả chính. Script sensitivity và CSV
ghi rõ đây là thay đổi công thức Eq. (6) chỉ để chẩn đoán.

Chưa có moment/coefficient/ensemble/producer provenance của lần tính
tham chiếu để xác định duy nhất nguồn chênh lệch. Vì thế không kết luận
chắc chắn rằng chỉ một coefficient cụ thể là nguyên nhân. Kết quả dương
cùng cỡ được tái lập độc lập; các chữ số được báo trước chưa được tái lập.

## Trả lời bốn câu hỏi

1. **Raw SKR hai chiều có dương không?** Có, `+9.6657997375e-5` bits/use,
   với quy ước nguồn cache được công khai ở trên và Eq. (13) homodyne.
2. **Tái lập tham chiếu độc lập được không?** Tái lập dấu và cỡ lớn; chưa
   tái lập đúng các số MI/Holevo/SKR đã báo. Các residual được giữ nguyên.
3. **Đó là tích phân 2D hay homodyne 1D?** Số dương chính là tích phân
   2D chuẩn hóa ghép với Holevo homodyne theo yêu cầu; không phải SKR của
   một phép đo homodyne 1D nhất quán. Phép so sánh 1D cho raw SKR âm.
4. **Còn thiếu gì cho tuyên bố an toàn homodyne trusted?** Cần thống nhất
   `VA/nbar/SNU`, PMF MB và finite-cutoff/Gram convention; chọn measurement,
   quadrature/basis/sifting và đơn vị bits/use nhất quán giữa MI và Holevo;
   chỉ định HV/G_d; chứng minh quan hệ giữa fading mixture thực và kênh
   Gaussian hiệu dụng dùng trong MI/security, xử lý outage/CSI công khai và
   cách gộp key. Mô hình detector không lý tưởng cũng cần covariance/security
   riêng nếu rời `R=1,xi_det=0`; PDF hiện chỉ cho Eq. (13) ở giới hạn lý tưởng.
   Hội tụ số không thiết lập security theorem cho các lựa chọn này.

## Bằng chứng và phạm vi bảo toàn

Runner: `scripts/recheck_manuscript_homodyne_noise.py`. Thư mục kết quả:
`results/manuscript_homodyne_noise_recheck_20261019/`, gồm bảng yêu cầu,
convergence/moment/reference CSV, ensemble NPZ, `result.json`, bản trích PDF,
yêu cầu gốc, startup manifest và validation receipt. Script từ chối ghi đè
`result.json` đã hoàn tất. Producer/input/source hashes được lưu để truy vết.

Git khi bắt đầu: branch `fix/channel`, HEAD
`49597cd766638bf1ab557776b6ff010dc29eb6e4`, worktree sạch. Hash frozen spec
hiện tại `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
khác hash lịch sử trong AGENTS; xung đột đã có trong state và được giữ nguyên.
Không sửa source khoa học đang dùng, evaluator/security functional production,
config, source moments/cache, hoặc frozen spec. Chỉ thêm diagnostic/artifact
và cập nhật hồ sơ nhiệm vụ. Không optimization/AP/AO, training, test-dataset
access, held-out/final-test/publication evaluation, threshold/baseline approval,
Objective C restart, external manuscript edit, commit hoặc push.

`UNVALIDATED_SECURITY_MODEL` và `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` giữ
nguyên. Kết thúc tại phép đối chiếu một điểm và báo cáo; không tự động tối ưu.
