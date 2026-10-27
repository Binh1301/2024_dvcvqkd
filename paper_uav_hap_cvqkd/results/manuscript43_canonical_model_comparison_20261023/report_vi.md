# Đối chiếu mô hình manuscript và repository — 23/10/2026

**Đã hoàn tất các kiểm tra cố định và đối chiếu repository với bản43 đang có; việc ràng buộc nguồn chuẩn v43(2) còn BLOCKED.** Tên người dùng chỉ định là **2026__Binh_s_work (43)(2).pdf**. File này không có trong thư mục đính kèm và chưa tìm thấy trên máy. File đọc được là **2026__Binh_s_work (43).pdf**, SHA-256:

    f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b

Bản sao nguyên byte nằm ở [inputs/available_v43.pdf](inputs/available_v43.pdf). Không suy ra hai phiên bản giống nhau từ tên gần giống. Mọi số thứ tự phương trình và nhận xét về nội dung PDF trong báo cáo này thuộc **bản43 theo hash trên**, cùng các công thức người dùng viết rõ trong yêu cầu. Nếu v43(2) khác, phải đối chiếu phần thay đổi trước khi thông qua. [canonical_model_manifest.json](canonical_model_manifest.json) ghi rõ canonical binding và evaluator adoption đều chưa được thông qua.

Kết quả chính: tại cấu hình Uniform dương gần đây, luật Eq. (10) chỉ giữ mass **0,9013297245653482** trên [0,1]; MI/Holevo/SKR bị chặn. Hai nhãn bounded B và C **cùng một hàm và cùng một luật**, cho **K = 0,10788256029424448 bit/use**. Kết quả đó không chứng minh SKR dương dưới Eq. (10). Không sửa production, frozen specification, cache C,w hay kết quả cũ; không chạy optimization.

## 1. Bảng parameter dễ đọc và nguồn gốc

[parameter_provenance.csv](parameter_provenance.csv) chứa 54 mục gồm giá trị, đơn vị, nguồn và phân loại. [protocol.json](protocol.json) là cấu hình số đã ghi trước phép tính; [fixed_contexts.json](fixed_contexts.json) lưu toàn bộ đại lượng suy ra.

| Parameter | Giá trị dùng ở cấu hình chính | Nguồn / lưu ý |
|---|---:|---|
| Đường truyền | HAP → UAV, 20 → 1 km | Yêu cầu và mục IV bản43 |
| Khoảng cách L | 19 km | (20−1)/cos(0°), mô hình hình học phẳng |
| Bước sóng | 1550 nm | Yêu cầu và bản43 |
| Đường kính thu Dr | 0,30 m | Cấu hình người dùng; default bản43 là 0,08 m |
| Góc thiên đỉnh | 0° | Cấu hình người dùng; default bản43 là 30° |
| Divergence **full-angle** | 10 µrad | Cấu hình người dùng; default bản43 233 µrad |
| Jitter trên mỗi trục | 0,5 µrad | Cấu hình người dùng; default bản43 15,61 µrad |
| SD vị trí UAV trên mỗi trục | 0,03 m | Cấu hình người dùng; default bản43 1 m |
| Boresight ρ | 0 m | Hai offset bằng 0 |
| Bán kính cong F0 | ∞ | Bản43 và provenance quang học cũ |
| τzen | 0,92 | Đường cao độ cố định 1→20 km; visibility tham chiếu 23 km |
| Wind / Cn² ground | 21 m/s / 10⁻¹⁴ m⁻²ᐟ³ | Bản43; công thức HV lấy từ repository |
| FOV **half-angle** | 6,25 mrad | Bản43 và protocol cũ |
| SD AoA σo | 1,5 mrad | Bản43 và protocol cũ |
| VA / n̄ | 3 SNU / 1,5 photon/use | Ensemble thật: VA=2n̄, vacuum variance=1 |
| Modulation / p | Uniform 256-QAM / 1/256 | Exact catalog; không đổi source |
| ξch / ξdet | 0,0186 / 0,005 SNU | Giá trị người dùng chỉ định; PDF định nghĩa ký hiệu, không ghi đủ giá trị số này |
| β / detection / reconciliation | 0,95 / homodyne thực 1D / RR | Yêu cầu |
| ηdet riêng | **Không có** | Đúng quy ước task v43 |
| AO / extra phase noise | OFF / OFF giả định lịch sử | Chưa là xác nhận phần cứng |

Bảng visibility người dùng cung cấp: 23 km→0,92; 15 km→0,89; 5 km→0,75. Đây là bảng τzen theo điều kiện visibility, chưa phải profile extinction theo độ cao. Audit này giữ nguyên cao độ, không ngoại suy suy hao cho đường truyền mới.

Đại lượng quang học tính lại: w0=0,09867606472 m; wL=0,13697432514 m; weff=0,13854927602 m; weq=0,27329146062 m; Gd=0,02312850067; σs=0,03146823796 m; d=χ²=18,85590064347; v=σR²=0,04145352708; A0=0,89304082646; B=A0ηatm=0,82159756035; P0=0,00016985667656141065.

HV và Gd có công thức trong repository nhưng bản43 để citation trống []. Vì vậy đây là **closure được ghi rõ nguồn**, không được gọi là toàn bộ công thức đã được PDF xác lập. Divergence 10 µrad còn hàm ý đường kính phát chứa 99% công suất khoảng 0,29947 m; khả năng aperture phát, PAT, jitter, tải trọng UAV và khí tượng chưa được kiểm chứng.

## 2. Ba nhãn, hai luật xác suất

Ký hiệu a=Dr/2, B=A0ηatm, d=weq²/(4σs²), v=σR². AoA độc lập có J~Bernoulli(P1), P0=1−P1.

### A — Eq. (10) giữ nguyên trên [0,1]

Mô hình thành phần: Y=ln Ia~N(−v/2,v), R~Rice(ρ,σs), η=J B exp(Y−2R²/weq²). Khi ρ=0, R là Rayleigh và Q=exp(−2R²/weq²)~Beta(d,1).

Phần liên tục Eq. (10):

\[
f_A(\eta)=\frac{P_1dC_1}{2B^d}\eta^{d-1}
 \operatorname{erfc}\{C_3[\ln(\eta/B)+\mu]\},\quad 0<\eta\le1,
\]

kèm P0δ0, với

\[
\log C_1=\rho^2/\sigma_s^2+\tfrac12vd(1+d),\quad
C_3=(32\rho^2\sigma_s^2/w_{\rm eq}^4+2v)^{-1/2},\quad
\mu=6\rho^2/w_{\rm eq}^2+\tfrac12v(1+2d).
\]

Implementation trực tiếp: [audit_model.py](../manuscript43_homodyne_audit_20261023/audit_model.py), raw_coefficients:221, raw_pdf_moments:233. Không chỉnh hệ số, support, mass, atom hoặc moment. Tại ρ=0, đây là mật độ của tích lognormal×Beta nếu mở rộng lên **(0,∞)**; lognormal không bị chặn nên có xác suất η>1. Chỉ tích phân [0,1] bỏ mất tail. Vì vậy:

- Luật tích không chặn có mass 1 nhưng vi phạm transmittance của kênh suy hao thụ động.
- Biểu thức giữ nguyên trên [0,1] giữ support vật lý nhưng là subprobability.
- Cột mass_above_one trong CSV là tail của **phần mở rộng**; nó không thuộc support của biểu thức đã giữ lại.

Tại cấu hình chính, closed form và tích phân trực tiếp cho cùng tail khoảng 0,09867027543465. Đây là bất tương thích của mô hình/support, không phải quad thiếu độ chính xác. Tăng precision không đưa mass từ 0,90133 lên 1.

### B — historical power_conserving_random_width

Luật thực tế của [model.py](../untrusted_positive_skr_feasibility_20261022/model.py), power_conserving:82:

\[
S\sim N(-v/2,v),\quad W=w_{\rm eff}e^{-S/2},\quad
R\sim{\rm Rayleigh}(\sigma_s),\quad S\perp R,
\]
\[
\eta_B=J\eta_{\rm atm}
 F_{\chi'^2_2((2R/W)^2)}((D_r/W)^2).
\]

Biểu thức CDF là tích phân công suất **chính xác của Gaussian tròn** trên aperture tròn dịch tâm, với mỗi beam được chuẩn hóa tổng công suất bằng 1. Do đó 0≤ηB≤ηatm≤1; tại đây upper bound=0,92. Atom outage vẫn P0. Không clipping, truncation, active conditioning, renormalization, hoặc chuyển tail sang atom. Chuẩn hóa trọng số Gauss–Hermite bằng √(2π) là công thức quadrature của chuẩn tắc, không phải sửa normalization kênh.

Luật này thay **biên độ scintillation độc lập** bằng **độ rộng beam ngẫu nhiên**, và thay collection xấp xỉ A0exp(−2R²/weq²) bằng tích phân aperture tròn. Khi S thay đổi, độ rộng và cường độ đỉnh cùng thay đổi. Đây là thay đổi mô hình vật lý/thống kê, không là phép đổi biến của Eq. (10). Nó bảo toàn công suất theo định nghĩa, nhưng chưa được hiệu chuẩn như một turbulence closure thực nghiệm.

### C — bounded trong Uniform-positive search

[search.py](../uniform_positive_skr_manuscript43_20261023/search.py), Search.context gọi chính a.legacy.power_conserving. [channel_alias_identity.json](channel_alias_identity.json) kiểm tra cả **same module object** lẫn **same function object**, cùng source SHA-256:

    08cf06f0607607f631c067803e2747b53a0cc9896c21c0700b7c84c1959207d6

Do đó **B=C**, không phải hai luật độc lập. Cách gọi “independent bounded” ở kết quả trước nghĩa là được định nghĩa tách khỏi Eq. (10), không nghĩa là khác implementation historical random-width.

### Các phép sửa support khác đang có trong repo

Tên hàm bounded() trong model.py:55 không có nghĩa cùng luật B/C. Hàm này hỗ trợ:

1. **Conditional active**: gọi g là mật độ active chưa nhân P1, F=∫₀¹g. Luật mới là P0δ0+P1 g(η)1(0,1]/F. Sampler production sample_fso_channel cũng reject/resample η>1 trên active gate. Với tập E⊂(0,1], xác suất mới bằng P1∫E g/F, thay vì P1∫E g; hệ số 1/F chứng minh khác luật.
2. **Tail→erasure**: atom mới P0+P1(1−F), density giữ P1g1(0,1]. Moment dương giữ nguyên nhưng outage thay đổi.
3. **Clipping tại 1**, nếu chọn: tạo atom P1(1−F)δ1; moment bậc q>0 tăng thêm cùng tail. Đây là mô tả phép toán để phân biệt, **không phải thao tác B/C hoặc audit đang thực hiện**.
4. Chia **toàn bộ** subdensity cho M0 lại đổi cả P0/M0; khác với conditional active giữ P0.

Không có phép nào tự động được thông qua làm Eq. (10).

## 3. Ba moment và quy ước noise

Với luật đã xác định, dùng:

\[
m_1=\int_0^1\eta f(d\eta),\quad
m_h=\int_0^1\sqrt\eta f(d\eta),\quad
T=m_h^2,
\]
\[
m_\xi=\xi_{\rm ch}m_1+\xi_{\rm det}M_0,\quad
N=T\xi_f=(m_1-T)V_A+m_\xi.
\]

M0=P0+P1C1Q(d). Đây là Eq. (18)–(20), với
\[
\mathcal Q(a)=\tfrac12\left[
 e^{a x_1-a\mu}{\rm erfc}(C_3x_1)+
 e^{a^2/(4C_3^2)-a\mu}{\rm erfc}(a/(2C_3)-C_3x_1)\right],
\quad x_1=\ln(1/B)+\mu.
\]
\[
m_q=P_1B^q\frac{dC_1}{d+q}\mathcal Q(d+q),\quad q=1/2,1.
\]

Không tính ξ(0) là số hữu hạn. Tích ηξ được mở rộng liên tục bằng **ξdet tại η=0**. Vì vậy detector term chứa cả ξdetP0. Đây là quy ước moment; việc detector thực sự tạo noise này trong outage còn cần mô hình vận hành. Nếu noise chỉ tồn tại khi active, moment giảm ξdetP0 — một mô hình khác.

Với A thiếu mass, các m1,mh,mξ dưới đây chỉ là tích phân của subdensity để chẩn đoán. Không diễn giải chúng như kỳ vọng của luật chuẩn hóa. Không thay M0 bằng 1 và không tính SKR sau khi gate fail.

| Đại lượng, cấu hình chính | A Eq. (10) | B historical | C Uniform bounded |
|---|---:|---:|---:|
| M0 | 0,9013297245653482 | 1 | 1 |
| P0 | 0,0001698566765614 | cùng giá trị | cùng giá trị |
| Mass liên tục (0,1] | 0,9011598678887868 | 0,9998301433234386 | như B |
| Tail η>1 của continuation | 0,09867027543465177 | 0 | 0 |
| m1 | 0,6708427108366657 | 0,7796075234117604 | như B |
| mh | 0,7745696939502585 | 0,8821686769408522 | như B |
| T=mh² | 0,5999582107861972 | 0,7782215745755737 | như B |
| mξ | 0,01698432304438872 | 0,01950069993545874 | như B |
| N | 0,22963782319579432 | 0,023658546444018845 | như B |
| ξf=N/T | 0,3827563638055263 | 0,030400784579792377 | như B |
| IAB | **BLOCKED** | 0,8378901900472914 | như B |
| βIAB | **BLOCKED** | 0,7959956805449268 | như B |
| χBE | **BLOCKED** | 0,6881131202506823 | như B |
| raw K | **BLOCKED** | **0,10788256029424448** | như B |

CSV chính [three_model_comparison.csv](three_model_comparison.csv) có đủ các cột yêu cầu và provenance nguồn. Ô thông tin/rate trống là unavailable, không phải 0. Nhãn CURRENTLY_VERIFIED_PASS trong hàng có rate chỉ là **kiểm tra số tại fixture**; requested_PDF_identity_verified và security_valid vẫn false.

Hai control cố định được ghi trước, không tìm kiếm: (Dr=0,30 m, divergence35 µrad, jitter1,561 µrad, σh0,10 m) cho A thiếu mass 1,0569955×10⁻¹⁰ và bị chặn bởi tolerance 10⁻¹⁰; B/C K=−0,09979924800. Control divergence40 µrad, jitter0,5 µrad, σh0,03 m cho A thiếu mass 4,9632×10⁻¹³, qua **gate số**, K=−0,06329901480; B/C K=−0,05283592084. Qua gate số không chứng minh tail bằng 0 hay sửa được bất tương thích vật lý của lognormal. Không thay tolerance để cứu control35.

## 4. Đối chiếu theo từng phương trình

[equation_comparison.csv](equation_comparison.csv) chứa 22 hàng: Eq. (1)–(21), câu Vmod sau Eq. (3), và mục optimization TBD. Mỗi hàng có biểu thức paper, biểu thức/chức năng repo, phân loại, hiệu ứng, số sai khác và hành động. [component_classification.csv](component_classification.csv) ghi **35 component** liên quan, function/class kèm dòng AST và SHA-256 hiện tại. Phân loại này không tuyên bố mọi file lịch sử trong toàn bộ repository đều thuộc một protocol.

Các đường dẫn trong bảng dưới tính từ project; AHelper là results/manuscript43_homodyne_audit_20261023/audit_model.py; Legacy là results/untrusted_positive_skr_feasibility_20261022/model.py; Wrapper là results/uniform_positive_skr_manuscript43_20261023/search.py.

| Eq. | Paper → implementation, phân loại và tác động |
|---|---|
| 1 | Grid Δ[(i−7,5)+j_c(j−7,5)] → src/modulation/qam256.py:square_qam256 và normalization.py:physical_amplitudes. **EQUIVALENT** qua scalar Δ; unit-RMS gauge không đổi ensemble nếu đổi scalar nhất quán. |
| 2 | Numerator γ, denominator ν → qam256.py:maxwell_boltzmann_pmf dùng cùng một ν và centered energy. Biểu thức paper **BLOCKED** khi γ≠ν; tổng PMF không bằng 1. Chuẩn hóa và mean thay đổi, ảnh hưởng MI/C,w/Holevo. Đề xuất ghi γ=ν và centered k. |
| 3 | n̄=Σp|α|² là **EXACT_MATCH** về định nghĩa. Câu Vmod=n̄/2 **BLOCKED** với vacuum1: repo VA=2n̄. Source VA3 có n̄1,5 và Var(2Reα)=3, không phải 0,75. Sửa notation hoặc đổi toàn bộ chuẩn quadrature; không relabel cache. |
| 4 | τzen^secζ → atmospheric_loss.py:atmospheric_transmittance_from_tau_zen, **EQUIVALENT**. Kruse route khác closure; dùng τ từ provenance cố định. |
| 5 | ln Ia~N(−σR²/2,σR²) → src/channel/scintillation.py:hufnagel_valley_scintillation có thêm aperture factor. **DIFFERENT** nếu dùng v_sc thay raw Rytov. Tại fixture v giảm 0,04145353→0,00393937; ảnh hưởng moment. |
| 6 | ν dùng weff → src/channel/pointing_error.py:manuscript_pointing_parameters dùng wL. **DIFFERENT** so với bản43: A0 tăng 0,0051750780, weq tăng 0,00469123525 m; cần proposal fix đối số. Legacy.optical dùng weff đúng biểu thức tham chiếu; B/C lại thay chính luật collection. |
| 7 | Rice(ρ,σs), σs²=σh²+(Lθjt)² → scripts/hap_uav_channel_pdf.py:f_rmis, **EQUIVALENT** khi dùng đúng các thành phần. Extra motion terms không tự tương đương. |
| 8 | Pushforward Rice qua Eq6 với I0 → hap_uav_channel_pdf.py:f_hp, **EQUIVALENT**. Không bỏ I0 khi ρ≠0. |
| 9 | AoA Bernoulli atom → src/channel/aoa.py:aoa_outage_probability, **EQUIVALENT** ở fixed fixture; half-angle, không thêm turbulence AoA. |
| 10 | AHelper:raw_coefficients/raw_pdf_moments tái hiện hệ số và retained integrals. **BLOCKED** về luật chuẩn hóa/physical support tại critical; **DIFFERENT** với B/C và exact Rice product khi ρ≠0. Không sửa density âm thầm. |
| 11 | βI−χ → Wrapper:model, **EQUIVALENT** về raw functional. src/cvqkd/secret_key_rate.py:fading_secret_key_rate dùng mục tiêu statewise khác; không đổi negative K thành0 trong CSV này. |
| 12 | y thực nhưng complex α trong |·|² → AHelper:homodyne_mi dùng Reα như task yêu cầu. Literal paper **BLOCKED**; real-projection là correction được công khai. MI rời rạc, không Shannon capacity. Production src/cvqkd/mutual_information.py là complex heterodyne, **DIFFERENT**. |
| 13 | ν3=√[V(V−Z²/W)] → Legacy:spectrum/full_holevo là homodyne. src/cvqkd/covariance.py:standard_form_covariance dùng a−z²/(b+1), **DIFFERENT**, heterodyne. Không ghép hai kiểu. |
| 14 | Zminus=2√T C−√(2Nw) → Legacy:full_holevo cực đại χ trên interval vật lý, **DIFFERENT** về chính sách tổng quát. Tại critical Zminus vật lý và đúng điểm được chọn, Δχ=ΔK=0. Chưa suy rộng cho mọi input. |
| 15 | τ=Σp|α⟩⟨α| → src/cvqkd/gram_moments.py full-support representation, **EQUIVALENT** cùng ensemble. Fock cutoff trong src/cvqkd/holevo.py:density_operator là xấp xỉ cần error riêng; không gọi threshold-retained rank là exact support. |
| 16 | w với aτ=τ½aτ⁻½ → gram_moments.py và scripts/full_support_c4_worker.py, **EQUIVALENT** theo authenticated exact-source route. Không đổi C,w khi chỉ đổi kênh/noise. |
| 17 | T=mh², N=(m1−T)VA+mξ → Wrapper:model, **EQUIVALENT** với VA convention của task, còn Vmod in paper chờ sửa. src/manuscript_literal_3moments.py:effective_channel là v37 với eta_f=mh và noise cũ: **DIFFERENT**. |
| 18 | Closed m1 → AHelper:raw_pdf_moments, **EQUIVALENT** với tích phân Eq10; residual trực tiếp −1,9984×10⁻¹⁵. Không có nghĩa density hợp lệ. |
| 19 | Closed mh → cùng helper, **EQUIVALENT**, residual −1,9984×10⁻¹⁵. Phải bình phương mh khi tính T. |
| 20 | ξch m1+ξdet M0 → Wrapper:model và audit_fixed.py:effective, **EQUIVALENT** theo extension ηξ(0)=ξdet. Hệ số M0 không được ép1 khi mass fail. |
| 21 | Tích phân ηfη trên [0,1] → AHelper:raw_pdf_moments direct, **EQUIVALENT** với18 qua integration by parts. Atom đóng góp0 cho m1, khác detector limit trong20. |
| III-B | Optimization=TBD trong bản43: **BLOCKED** như đặc tả optimizer. Không chạy hoặc chuẩn hóa historical optimizer thành canonical. |

“EQUIVALENT” luôn có điều kiện ghi trong hàng; không bao hàm giấy phép thay một module trọn vẹn có API/protocol khác. Các classifier xét bản43 hash-bound, chưa xác minh target v43(2).

## 5. Các mâu thuẫn nội tại của manuscript

### Chuẩn quadrature và Vmod

Tại vacuum variance1, X=a+a† và coherent mean X=2Reα. Với source C4 centered, Var(X modulation)=2n̄. VA3 có n̄=1,5. Câu Vmod=n̄/2 lệch hệ số4 với mean Eq12 và V=Vmod+1 của Eq13.

Đổi X′=X/2 sẽ cho modulation variance n̄/2, nhưng vacuum variance=1/4 và [X′,P′]=i/2; covariance, symplectic reference và mean cũng phải đổi đồng bộ. Không được chỉ đổi nhãn VA3→0,75 mà giữ vacuum1, mean2Reα và source moments cũ. [literal_internal_consistency.json](literal_internal_consistency.json) lưu bằng chứng; không tạo SKR giả cho source bị relabel.

### MB và centering

Grid raw i−7,5 có năng lượng trung bình Uniform 42,5. Nếu x_raw được chia √42,5 thành unit-RMS, cùng PMF đòi hỏi νrepo=42,5νraw. Nếu energy dùng physical α=Δk, thì νphys=νraw/Δ². Dùng γ ở numerator và ν khác ở denominator cho tổng Z(γ)/Z(ν), không phải1.

[source_notation_checks.json](source_notation_checks.json) có fixture cố định xác nhận PMF sau conversion trùng trong rounding, γ≠ν làm mass sai, và dùng energy chỉ số chưa centered tạo mean khác0. Không tính C,w/SKR cho các PMF sai này. Geometry shaping hoặc thực sự đổi p/α không phải notation conversion và cần source identity mới.

### Likelihood homodyne

Với y∈R, literal |y−2√Tαk|² chứa thêm 4T(Imαk)². Tích phân likelihood in ra bằng exp[−2T(Imαk)²/σ²], **không bằng1**. Tại source chính, mass các conditional nằm trong 0,04887046…0,98667367.

Task đã chỉ định phép chiếu thực để chẩn đoán:
\[
p(y|k)=\mathcal N(y;2\sqrt T\,{\rm Re}\alpha_k,1+N),\quad
I=\sum_k p_k\int p(y|k)\log_2[p(y|k)/p(y)]dy.
\]
Đây là real1D discrete-input MI. 256 trạng thái gom thành 16 tọa độ X với marginal probability đúng; direct256 và grouped16 đã đối chiếu. Không lấy ½log₂(1+SNR) thay MI; biểu thức Shannon chỉ dùng như upper-bound sanity check.

### Holevo, DBL và physical interval

Dùng Γ=[[aI,Zσz],[Zσz,bI]], a=1+VA, b=1+TVA+N; Δ=a²+b²−2Z²; D=(ab−Z²)²; ν1,2²=(Δ±√(Δ²−4D))/2; ν3=√[a(a−Z²/b)]. Require Γ+iΩ≥0, νj≥1 và entropy argument≥0. Không clipping eigenvalue.

Source cố định cho C=1,9206153338755625; w=0,029240798657568498. Eq14 Zminus=2√TC−√(2Nw). Interval helper xét [2√TC−√(2Nw),2√TC+√(2Nw)]∩[−Zcap,Zcap], với Zcap²=min((a−1)(b+1),(a+1)(b−1)). Việc lấy maximum χ trên interval là chính sách mở rộng thận trọng về số, không phải literal Eq14. Ở fixture chính: interval [3,35141674192;3,42581001007], cap3,43389230333; điểm chọn là lower, ν=(1,83880943152;1,19713270169;1,61922893103). Sai khác rate với direct physical Zminus bằng0 tại đây.

Grid33/129 và local refinement không phải rigorous global enclosure. Security theorem của ensemble/noise/fading/measurement thực tế chưa được chứng minh bằng việc covariance vật lý hay entropy hội tụ.

## 6. Boresight khác0: Eq. (10) không phải tích Rice chính xác

Không chỉ là lỗi support. Với q>0, tích nguyên thủy Eq5×Eq8 trên toàn miền dương có:
\[
M_q^{\rm Rice}=P_1B^q\frac d{d+q}
\exp\left[\tfrac12v(q^2-q)-\frac{\rho^2q}{2\sigma_s^2(d+q)}\right].
\]
Trong khi Eq10 với hệ số in ra cho:
\[
M_q^{(10)}=P_1B^q\frac d{d+q}
\exp\left[\tfrac12v(q^2-q)+\frac{\rho^2}{2\sigma_s^2}
(q^2/d^2-q/d)\right],
\]
\[
\frac{M_q^{(10)}}{M_q^{\rm Rice}}
=\exp\left[\frac{\rho^2q^3}{2\sigma_s^2d^2(d+q)}\right].
\]

Tỷ số=1 khi ρ=0; lớn hơn1 khi ρ≠0,q>0. Đây là chứng minh khác luật, không dựa riêng vào tích phân. Eq10 tương ứng Beta(d,1) nhân lognormal có variance v+λ/d² và mean log −v/2−λ/(2d), λ=ρ²/σs²; nó khớp hai cumulant đầu của log-loss Rice nhưng không khớp các moment cao hơn. Phải công bố approximation nếu dùng khi ρ≠0.

[rician_comparison.csv](rician_comparison.csv) có tích phân noncentral-χ² độc lập và Laplace integral Rice:

| Fixture | ρ | m1 giữ lại Eq10 | m1 giữ lại tích Rice |
|---|---:|---:|---:|
| Critical | 0,03 m | 0,667179065927 | 0,668533909177 |
| Critical | 0,10 m | 0,580284436071 | 0,586606423479 |

Tại baseline paper 8cm/233µrad/jitter15,61µrad/σh1m/zenith30°, ρ0,5m, tỷ số whole-positive-support m1=1,02146806759. Không áp dụng kết quả ρ0 để tuyên bố tổng quát.

## 7. Cô lập nguyên nhân khác SKR

Không tồn tại ΔK hữu hạn hợp lệ từ A bị chặn sang B/C. Vì thế không cộng một “normalization gain” giả vào positive K. [moment_attribution.csv](moment_attribution.csv) dùng các moment tham chiếu **không tính rate**, phân biệt:

| Luật/thao tác chẩn đoán | m1 | T | N |
|---|---:|---:|---:|
| A retained subdensity | 0,67084271084 | 0,59995821079 | 0,22963782320 |
| A conditional active giữ P0 | 0,74429497764 | 0,73853276537 | 0,03613052342 |
| A tích trên (0,∞), còn η>1 | 0,78008702963 | 0,77139821085 | 0,04557607510 |
| Fixed-width aperture tròn × Ia độc lập, còn η>1 | 0,78808945262 | 0,77919071364 | 0,04635468074 |
| B/C random width + aperture tròn | 0,77960752341 | 0,77822157458 | 0,02365854644 |

Conditional active đã có mass1 nhưng m1,T,N vẫn khác B/C. Ngay cả whole-support m1 gần nhau cũng có mh/T/N khác rõ. Do đó khác biệt không do normalization đơn thuần. Thay collection và coupling scintillation tác động riêng lên fading variance.

Các phép so sánh rate có nghĩa giữ cùng source và B/C law ở [controlled_comparisons_final.csv](controlled_comparisons_final.csv):

| Chỉ thay một quy ước so với Gaussian1D/no ηdet | ΔIAB | ΔχBE | ΔK (bit/use) |
|---|---:|---:|---:|
| Detector lịch sử ηdet0,95, εout0,005 | −0,02360834128 | −0,00466224063 | −0,01776568359 |
| Noise chỉ active, thay ηξ(0)=ξdet thành0 | +3,91363×10⁻⁷ | −4,12119×10⁻⁶ | +4,49298×10⁻⁶ |
| Scaling classical y→y/2 đồng bộ mean/noise | 0 | 0 | 0 |
| Direct Eq14 Zminus so với interval max ở fixture này | 0 | 0 | 0 |
| MI fading-mixture 1D thay Gaussian effective, giữ χ | +0,0003047825220 | 0 | +0,0002895433959 |
| Relabel literal Vmod=n̄/2, giữ source/vacuum cũ | **NON-EQUIVALENT** | **Không tính** | **Không tính** |

Detector lịch sử thay cả quantum attenuation/noise theo đúng convention của nó; đây là một thay đổi mô hình detector có định nghĩa, không phải đổi đơn vị của ξdet. Không đưa ηdet của control này vào canonical calculations.

Fading mixture dùng p(y|k)=Eη N(y;2√ηReαk,1+ξchη+ξdet) cùng atom, không conditioning theo CSI. K diagnostic=0,10817210369018393 khi giữ χ của Gaussian covariance. MI của mixture khác MI Gaussian hiệu dụng; moment/covariance giống nhau không quyết định toàn bộ likelihood. Chưa phải phê duyệt security của protocol mixture.

Phép tính mixture lịch sử ở các order128/16,256/32,512/64 **chưa đạt** tolerance2×10⁻⁸; record fail được giữ nguyên ở pooled_MI_precision.json. Không nới tolerance. Addendum [additional_precision_protocol.json](additional_precision_protocol.json) thay biến tích phân tương đương x=R²/(2σs²), tích phân e⁻ˣ trên [0,40], tail≤e⁻⁴⁰, không chuẩn hóa lại weights. Hai level128/32/160 và256/64/320 cho ΔI=−1,05804×10⁻¹³, conditional mass residual≤1,13×10⁻¹³, moment residual<1,1×10⁻¹³. [pooled_MI_refined.json](pooled_MI_refined.json) là bằng chứng hội tụ bổ sung.

## 8. Precision, provenance và phạm vi kiểm tra

- 3 scenario cố định × 3 nhãn =9 hàng. B/C lặp cùng luật nhưng giữ hai nhãn theo yêu cầu.
- 7 hàng có rate ×12 kiểm tra=84 check record: GH64/128, adaptive MI độc lập, grouped16/direct256, X/P, scaling, all16 conditional normalization, Γ/ν, Z33/129, entropy80/110 digits, raw K và absence ηdet. Không diễn giải là84 thử nghiệm vật lý độc lập.
- Raw Eq10 q=0,1/2,1 được đối chiếu closed form với quad log-coordinate. Bounded moments đối chiếu width GH32/64 và radial integration. Nonzero-ρ đối chiếu exact product/Rice Laplace.
- Addendum phát hiện 1−M0 **không đo chính xác tương đối** tail cực nhỏ. Baselineρ0 có stable tail≈4,81913×10⁻²⁴⁶, trong khi subtraction trả≈3,4×10⁻⁸³ do cancellation/precision floor. Cả hai dưới tolerance tuyệt đối10⁻¹⁰, nhưng không được gọi số floor là tail vật lý chính xác. [tail_precision.csv](tail_precision.csv) giữ cả ba cách; critical tail≈0,09867 ổn định.
- Actual source hash: d06c6c3560dcc1173a60c6043f5e4e6d44aee0c64ad465fc624e0f3fc98a5522; payload SHA c2f7fa8af8b0664669231bc3c41461bbf96b9dbeb4e8aacaf9847c3219c741b8. [fixed_source.json](fixed_source.json) ghi exact path/C/w.
- startup_manifest.json bảo vệ9164 file cũ; source/production/frozen/test/config/result byte được kiểm tra lại bằng verifier. Năm ledger là ngoại lệ được ghi sẵn; các block lịch sử được giữ.
- Frozen spec hiện có SHA df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15, khác historical expected561f... trong AGENTS. Không ghi đè/restore tự động.

[numerical_receipt.json](numerical_receipt.json), [refined_precision_receipt.json](refined_precision_receipt.json), [package_receipt.json](package_receipt.json), verification.json và final_seal.json ràng buộc producer/protocol/input/artifact hash. Lệnh đọc lại artifact, không chạy evaluator:

    .venv\Scripts\python.exe -X utf8 -B results/manuscript43_canonical_model_comparison_20261023/verify.py

UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS và ObjectiveC USER_STOPPED được giữ. Không có training, test/held-out access, publication evaluation, AP mới, interpolation, global search, baseline/default/threshold approval, commit hoặc push.

## 9. Khuyến nghị trả lời sáu câu hỏi

1. **Bounded mới có đồng nhất Eq10 không? Không.** B=C về implementation, nhưng khác A. Phân loại DIFFERENT; target PDF identity vẫn BLOCKED.
2. **Khác chính xác ở đâu?** Scintillation chuyển từ amplitude lognormal độc lập sang random width; collection đổi từ equivalent Gaussian exponential sang exact circular aperture; support từ continuation vô hạn/subdensity [0,1] sang [0,ηatm]; không có clipping/conditioning trong B/C. Các conditional/erasure sampler khác được nhận diện riêng.
3. **Cấu hình Uniform dương hiện tại có SKR dương hợp lệ theo luật gốc không? Chưa thể khẳng định; phép đánh giá phải BLOCKED.** A thiếu9,867% mass, nên không có K hợp lệ để so dấu. +0,107883 thuộc B/C. Việc thiếu chứng cứ v43(2) là blocker bổ sung, không được giải bằng bounded thay thế.
4. **Cần đổi gì để repo khớp v43(2)?** Trước hết có đúng PDF và hash. Với bản43 đang có: sửa notation MB/centering, Vmod/quadrature và Reα trong likelihood; chọn cách giải quyết support/lognormal và approximationρ≠0 bằng manuscript correction; tách đường homodyne1D và ν3 đúng khỏi production heterodyne; dùng cùng T,N/no ηdet; đề xuất sửa đối sốν(wL→weff), công bố closure HV/Gd và aperture averaging. Danh sách ở correction_proposal_v1.md là **PROPOSAL_NOT_ADOPTED**, không phải diff production đã áp dụng.
5. **Giữ được exact C,w catalog không? Có**, nếu giữ actual p,α,source settings/hash và full-support provenance. Đổi law/noise/MI không đổi source C,w. Sửa ký hiệu nhất quán không cần AP mới. Thực sự đổi năng lượng hoặc PMF/geometry của constellation cần exact source entry mới; không relabel, nội suy hoặc mượn MB moments cho Uniform.
6. **Evaluator nào cho đồ thị sau này?** Chưa có production evaluator được duyệt là canonical v43(2). Đề nghị một pipeline được định danh theo PDF hash: source-authentication → exact explicit law/atom/mass gate → m1,mh,mξ → một T=mh²,N chung → discrete Gaussian-effective real1D MI → physical homodyne covariance/DBL/Holevo theo chính sáchZ công khai → rawK. Pure helpers AHelper.homodyne_mi/raw_pdf_moments, Wrapper.model và strict Legacy.spectrum minh họa đường chẩn đoán này, nhưng không tự động hợp thức hóa những mâu thuẫn manuscript. Cấm fallback sang bounded để nối đoạn plot bị chặn; mỗi point phải recompute geometry/optics và giữ luật/noise/source provenance. Nếu Eq10 không hợp lệ ở point nào, CSV ghi BLOCKED và figure ngắt đường.

Đề xuất nhỏ nhất là sửa các mâu thuẫn notation đã chứng minh, **giữ A fail-closed**, và để tác giả lựa chọn một corrected physical channel với định nghĩa/provenance riêng. Conditional truncation là một công thức sửa ngắn nhưng thêm giả định điều kiện; nó không bảo toàn luật gốc và không tự động là mô hình vật lý đúng. Không chọn luật theo dấu SKR.

## 10. Nguồn security bên ngoài và giới hạn suy luận

Nguồn gốc DBL là lower bound **asymptotic arbitrary modulation**; không tự chứng nhận mô hình detector/fading ở đây. Xem [Denys–Brown–Leverrier, Quantum 5, 540](https://quantum-journal.org/papers/q-2021-09-13-540/). Nghiên cứu fading finite-size phải xác định parameter estimation/postprocessing và security scope; xem [Hosseinidehaj–Walk–Ralph, PRA103,012605](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.103.012605). Nhận xét rằng chưa có theorem binding cho tổ hợp hiện tại là kết luận audit repository, không phải khẳng định hai bài trên phê duyệt evaluator này.

Còn thiếu: đúng file v43(2), author decision cho các correction, security justification tương ứng và hiệu chuẩn phần cứng/kênh. Đã hoàn tất phần audit độc lập; chưa hoàn tất việc thiết lập v43(2) làm single source of truth.
