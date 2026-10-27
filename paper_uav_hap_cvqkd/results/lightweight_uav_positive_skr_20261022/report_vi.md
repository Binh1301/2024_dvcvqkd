# Tối ưu tham số với UAV receiver 8 cm — 2026-10-22

**Chưa tìm thấy SKR dương trong miền đã thử.** Detector luôn UNTRUSTED, Dr luôn 0.08 m. Chỉ dùng noise detector 0.0135 và 0.005 SNU; không đánh giá mức thấp hơn. Không thay PDF, moments, optical collection, MI, covariance, Holevo, correlation bounds, chuẩn hóa nguồn hoặc receiver homodyne. K lớn nhất trong tám scenario đã refinement là **-0.0236784908824 bit/use**; gap χ−βI là **0.0236784908824** nếu K âm. Đây là best exact tested, không phải kết luận tối ưu toàn cục hoặc no-key theorem.

## 1. Baseline và mô hình được giữ nguyên

Baseline bounded hiện tại đã tính lại trước tìm kiếm: I_AB=0.000753762353882783, βI_AB=0.000716074236188644, χ_BE=0.0594124373159937, K=-0.058696363079805018. Sai khác với saved baseline nằm trong 1e-12 tại mọi field đã đối chiếu; xem [baseline_regression.json](baseline_regression.json). K lịch sử corrected trial −0.058724314679977559 thuộc optical law lịch sử khác và được xác thực riêng, không dùng thay baseline hiện tại.

HAP/UAV=20/1 km, ζ=30°, L=21.9393102292 km, λ=1550 nm, β=.95, εch=.0186, full-angle divergence233 µrad, angular SD15.61 µrad mỗi trục, residual centering SD1 m, AoA1.5 mrad, FOV half-angle6.25 mrad, τzen=.92, detector(.8,.0135), fixed MB(VA5.475,νraw.165). `configs/channel.yaml` có223 µrad tại `theta_div_rad`; đây cũng là divergence, không phải jitter. `configs/manuscript_mobility.json` ghi233 µrad cho manuscript; nghiên cứu giữ233.

Importer gọi trực tiếp `../positive_skr_without_receiver_enlargement_20261022/numeric.py` và evaluator trước của nó, byte hashes trong [startup_manifest.json](startup_manifest.json). Đây là mô hình passive random-width/circular-Gaussian hiện đã dùng cho diagnostic trước; không trở lại PDF lịch sử khác. Full-Z maximum là tối ưu số trên interval vật lý, chưa có rigorous global enclosure.

Các biểu thức hiện có được giữ nguyên:

\[
T_f=\langle\sqrt T\rangle^2,\quad N_f=(\langle T\rangle-T_f)V_A,\quad N_c=.0186\langle T\rangle,\quad N_d=\epsilon_{det}/\eta_{det},
\]
\[
N_{post}=\eta_{det}(N_f+N_c)+\epsilon_{det},\quad a=1+V_A,\quad b=1+\eta_{det}T_fV_A+N_{post},\quad K=.95I_{AB}-\chi_{BE}.
\]

MI chính là actual pooled fading likelihood, với conditional mean 2√(ηdet T)Reα và variance1+ηdet εch T+εdet. Không cộng fading noise lần nữa trong likelihood, không conditioning theo CSI, không postselection. Effective-channel MI được lưu riêng ở I_AB_surrogate. Outage atom được giữ; không clip K âm hoặc T.

## 2. Ý nghĩa của εdet=0.005 SNU

0.005 là giá trị giả định được người dùng cho phép của đúng biến detector excess-noise hiện tại. [Villaseñor et al., arXiv:2005.10465](https://arxiv.org/pdf/2005.10465) dùng electronic-noise υel=.005 và công thức ξdet phụ thuộc coherent efficiency γ (Eq.10); các biến này không tự đồng nhất với εdet của repo. Bài tham khảo không chứng minh phần cứng UAV ở đây đạt .005, không cung cấp phép đổi chuẩn hóa và không thay trust convention. Noise ở .005 vẫn UNTRUSTED.

Các điểm dương của nghiên cứu trước dùngnoise .0005, jitter1 µrad vàσh=.05 m không thuộc miền mới. Chúng không được đưa vào bảng kết quả hoặc dùng làm nghiệm cho yêu cầu này; chỉ artifact lịch sử được xác thực, không chạy lại các mức noise bị cấm.

## 3. Stage A — Chỉ nâng detector

Giữ nguồn và toàn bộ optics/geometry gốc. Mỗi dòng đã tính MI, βMI, Holevo và signed K:

| ηdet | εdet | I_AB | βI_AB | χ_BE | K | Gap χ−βI |
| --- | --- | --- | --- | --- | --- | --- |
| 0.8 | 0.0135 | 0.000753762870735 | 0.000716074727199 | 0.059412437316 | -0.0586963625888 | 0.0586963625888 |
| 0.85 | 0.0135 | 0.000800842986731 | 0.000760800837394 | 0.0594725185159 | -0.0587117176786 | 0.0587117176786 |
| 0.9 | 0.0135 | 0.00084791956888 | 0.000805523590436 | 0.0595325843732 | -0.0587270607827 | 0.0587270607827 |
| 0.95 | 0.0135 | 0.000894992617686 | 0.000850242986801 | 0.059592635748 | -0.0587423927612 | 0.0587423927612 |
| 0.8 | 0.005 | 0.000760134118076 | 0.000722127412172 | 0.0262501163992 | -0.025527988987 | 0.025527988987 |
| 0.85 | 0.005 | 0.00080761192675 | 0.000767231330412 | 0.0263141015788 | -0.0255468702484 | 0.0255468702484 |
| 0.9 | 0.005 | 0.000855086141621 | 0.00081233183454 | 0.0263780715291 | -0.0255657396945 | 0.0255657396945 |
| 0.95 | 0.005 | 0.000902556763207 | 0.000857428925047 | 0.0264420268986 | -0.0255845979736 | 0.0255845979736 |


Không có điểm dương nếu mọi dòng K vẫn âm. Tăng efficiency không được giả định luôn tốt hơn trong mô hình untrusted này; bảng giữ đủ bốn mức η cho mỗi noise. Tỷ lệ giảm noise variance từ .0135 xuống .005 là2.7 lần, không phải phép chuyển sang trusted detector.

## 4. Stage B–D — HAP transmitter, PAT và geometry

Quét divergence233/100/75/50/35/25/20/15 µrad; independent jitter15.61/10/7.5/5/3/1.561 µrad và residual centering1/.5/.3/.2/.1 m. Sau đó dùng sáu PAT tiers kết hợp có chủ đích, ởζ0/15/30 và tám detector scenarios. Đây không phải toàn bộ tích Descartes jitter×centering×source×geometry.

| εdet | Stage | ηdet | ζ | Div | Jitter | Center SD | K lớn nhất fixed source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0135 | Detector only | 0.8 | 30 | 233 | 15.61 | 1 | -0.0586963625888 |
| 0.0135 | Fixed-source physical scan | 0.95 | 0 | 75 | 1.561 | 0.1 | -0.0580920562523 |
| 0.005 | Detector only | 0.8 | 30 | 233 | 15.61 | 1 | -0.025527988987 |
| 0.005 | Fixed-source physical scan | 0.95 | 0 | 75 | 1.561 | 0.1 | -0.0250532796613 |


L=19/cosζ km và toàn bộ diffraction, HV integrals/secant factors, Gd, displacement và fading moments được tính lại bởi hàm hiện có. Không tự thay turbulence hay τzen. Không quét độ cao vì chưa có profile extinction theo độ cao; giữ HAP20/UAV1 km, tránh gán khí quyển chưa hiệu chuẩn cho UAV5 km.

[transmitter_optical_metrics.csv](transmitter_optical_metrics.csv) lưu w0, footprint2wL/2weff, ideal transmitter D99, mean active collection, offset/beam radius, Tf và SKR. Công thức cũ w0=2λ/(πθdiv), Dtx99=2w0√(ln100/2). D99 chỉ là đường kính chứa99% công suất Gaussian lý tưởng, chưa phải thiết kế hard pupil có diffraction/coupling loss. Beam nhỏ hơn làm tăng yêu cầu centering; không suy ra tiết kiệm năng lượng từ divergence nhỏ.

σh là residual optical beam-centering SD theo model, không phải độ chính xác GPS hoặc chuyển động thân UAV. Có thể đặt yêu cầu PAT chủ yếu ở HAP, nhưng beacon, acquisition, latency, field of regard và hợp tác UAV chưa được mô hình hóa. Mứcσh=.1 m là yêu cầu hiệu năng quang, chưa có chứng minh đạt được trên platform cụ thể.

## 5. Stage E — Catalog nguồn exact và joint refinement

Catalog233 nguồn đã xác thực payload/hash:197 MB,36 Uniform. Physical screening giữ nguồn cố định; sau đó rank catalog đầy đủ ở context tốt nhất theo fixed-source K và moment quality cho mỗi detector. Hai baseline-optics η=.8 cũng được rank. Một bước phối hợp kiểm tra winning sources trên các physical contexts rồi rank nguồn lại tại context thắng. Tổng 26 context trong optimization.json; các final context bổ sung nếu có nằm ở catalog_final_*.csv. P1 cố địnhν chọnVA, P2 cố địnhVA chọnν, bốn starts và delta1e-8 trong catalog. Không nội suy C,w/SKR, không tạo AP/moments mới, không khẳng định continuous/global optimum.

Tám kết quả gần zero nhất được chọn và refinement:

| ηdet | εdet | ζ | Div | Jitter | Center SD | VA | ν | I_AB | βI_AB | χ_BE | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.8 | 0.0135 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.00974095390696 | 0.00925390621161 | 0.0662211691134 | -0.0569672629018 |
| 0.85 | 0.0135 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0103451833227 | 0.00982792415656 | 0.066702012406 | -0.0568740882494 |
| 0.9 | 0.0135 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0109488794627 | 0.0104014354896 | 0.0671822529929 | -0.0567808175033 |
| 0.95 | 0.0135 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0115520432443 | 0.010974441082 | 0.0676618918684 | -0.0566874507863 |
| 0.8 | 0.005 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.00982275150863 | 0.0093316139332 | 0.0332569861192 | -0.023925372186 |
| 0.85 | 0.005 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0104320162182 | 0.00991041540729 | 0.0337536295031 | -0.0238432140958 |
| 0.9 | 0.005 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0110407387276 | 0.0104887017912 | 0.0342496220047 | -0.0237609202135 |
| 0.95 | 0.005 | 0 | 50 | 1.561 | 0.1 | 1.62499953997 | 0.25 | 0.0116489199771 | 0.0110664739783 | 0.0347449648607 | -0.0236784908824 |


So sánh cùng optics/geometry/detector, nhưng mỗi family có thể chọn VA khác nhau:

| ηdet | εdet | Nguồn | VA | νraw | I_AB | χ_BE | K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.8 | 0.0135 | Uniform_best_catalog | 0.02 | 0 | 0.000120716479382 | 0.0592622304015 | -0.0591475497461 |
| 0.8 | 0.0135 | MB_fixed | 5.475 | 0.165 | 0.03229218041 | 0.0892739392623 | -0.0585963678728 |
| 0.8 | 0.0135 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.00974095390696 | 0.0662211691134 | -0.0569672629018 |
| 0.85 | 0.0135 | Uniform_best_catalog | 0.02 | 0 | 0.000128259301002 | 0.0593070074037 | -0.0591851610677 |
| 0.85 | 0.0135 | MB_fixed | 5.475 | 0.165 | 0.0342614465337 | 0.0911477972139 | -0.0585994230069 |
| 0.85 | 0.0135 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0103451833227 | 0.066702012406 | -0.0568740882494 |
| 0.9 | 0.0135 | Uniform_best_catalog | 0.02 | 0 | 0.000135801892295 | 0.0593515585477 | -0.0592225467501 |
| 0.9 | 0.0135 | MB_fixed | 5.475 | 0.165 | 0.0362251413169 | 0.0930158361167 | -0.0586019518656 |
| 0.9 | 0.0135 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0109488794627 | 0.0671822529929 | -0.0567808175033 |
| 0.95 | 0.0135 | Uniform_best_catalog | 0.02 | 0 | 0.000143344253272 | 0.0593959020771 | -0.0592597250365 |
| 0.95 | 0.0135 | MB_fixed | 5.475 | 0.165 | 0.0381832956179 | 0.0948780927957 | -0.0586039619587 |
| 0.95 | 0.0135 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0115520432443 | 0.0676618918684 | -0.0566874507863 |
| 0.8 | 0.005 | Uniform_best_catalog | 0.02 | 0 | 0.000121737212997 | 0.0261016498854 | -0.0259859995331 |
| 0.8 | 0.005 | MB_fixed | 5.475 | 0.165 | 0.0325589952469 | 0.0567639577705 | -0.0258329122859 |
| 0.8 | 0.005 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.00982275150863 | 0.0332569861192 | -0.023925372186 |
| 0.85 | 0.005 | Uniform_best_catalog | 0.02 | 0 | 0.000129343797211 | 0.0261515713436 | -0.0260286947362 |
| 0.85 | 0.005 | MB_fixed | 5.475 | 0.165 | 0.0345441309305 | 0.0586804449339 | -0.02586352055 |
| 0.85 | 0.005 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0104320162182 | 0.0337536295031 | -0.0238432140958 |
| 0.9 | 0.005 | Uniform_best_catalog | 0.02 | 0 | 0.000136950147187 | 0.0262013209089 | -0.0260712182691 |
| 0.9 | 0.005 | MB_fixed | 5.475 | 0.165 | 0.0365236051615 | 0.0605908462137 | -0.0258934213103 |
| 0.9 | 0.005 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0110407387276 | 0.0342496220047 | -0.0237609202135 |
| 0.95 | 0.005 | Uniform_best_catalog | 0.02 | 0 | 0.000144556262935 | 0.0262509118088 | -0.0261135833591 |
| 0.95 | 0.005 | MB_fixed | 5.475 | 0.165 | 0.0384974495487 | 0.0624952002039 | -0.0259226231327 |
| 0.95 | 0.005 | MB_best_exact_tested | 1.62499953997 | 0.25 | 0.0116489199771 | 0.0347449648607 | -0.0236784908824 |


Gain giữa fixed MB và optimized MB bao gồm thay đổi cảVA vàν; không gọi toàn bộ là shaping-only gain. Uniform có C,w và ensemble hash riêng. Catalog rời rạc không đủ để kết luận toàn miền liên tục không có nghiệm dương.

## 6. Ba tham chiếu kỹ thuật và bảng parameter

Không có ba thiết kế dương để khuyến nghị. A/B/C dưới đây là các tham chiếu âm/gần ngưỡng đã thử, không phải thiết kế hoạt động. A giữ đúng thông số detector gốc; B giới hạnη≤.9 và dùngnoise .005; C là K lớn nhất đã thử trong tám scenarios. Nếu B và C trùng nhau, đó là cùng một kết quả được nhìn theo hai tiêu chí, không phải hai thiết kế độc lập.

| Cấu hình | Dr(m) | Div(µrad) | Jitter(µrad) | Center SD(m) | ζ(°) | L(km) | ηdet | εdet(SNU) | VA | νraw | I_AB | βI_AB | χ_BE | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — Giữ thông số detector gốc | 0.08 | 50 | 1.561 | 0.1 | 0 | 19 | 0.8 | 0.0135 | 1.62499953997 | 0.25 | 0.00974095390696 | 0.00925390621161 | 0.0662211691134 | -0.0569672629018 |
| B — Tham chiếu cân bằng | 0.08 | 50 | 1.561 | 0.1 | 0 | 19 | 0.9 | 0.005 | 1.62499953997 | 0.25 | 0.0110407387276 | 0.0104887017912 | 0.0342496220047 | -0.0237609202135 |
| C — K lớn nhất đã thử | 0.08 | 50 | 1.561 | 0.1 | 0 | 19 | 0.95 | 0.005 | 1.62499953997 | 0.25 | 0.0116489199771 | 0.0110664739783 | 0.0347449648607 | -0.0236784908824 |


**A — Giữ thông số detector gốc**

\[
\begin{gathered}
D_r=0.08\,\mathrm{m},\quad \theta_{div}=50\,\mu\mathrm{rad},\quad \theta_{jt}=1.561\,\mu\mathrm{rad},\\
\sigma_h=0.1\,\mathrm{m},\quad \zeta=0^\circ,\quad L=19\,\mathrm{km},\\
\eta_{det}=0.8,\quad \epsilon_{det}=0.0135,\quad V_A=1.62499953997,\quad \nu_{raw}=0.25,\\
I_{AB}=0.00974095390696,\quad \beta I_{AB}=0.00925390621161,\quad \chi_{BE}=0.0662211691134,\quad K=-0.0569672629018.
\end{gathered}
\]


**B — Tham chiếu cân bằng**

\[
\begin{gathered}
D_r=0.08\,\mathrm{m},\quad \theta_{div}=50\,\mu\mathrm{rad},\quad \theta_{jt}=1.561\,\mu\mathrm{rad},\\
\sigma_h=0.1\,\mathrm{m},\quad \zeta=0^\circ,\quad L=19\,\mathrm{km},\\
\eta_{det}=0.9,\quad \epsilon_{det}=0.005,\quad V_A=1.62499953997,\quad \nu_{raw}=0.25,\\
I_{AB}=0.0110407387276,\quad \beta I_{AB}=0.0104887017912,\quad \chi_{BE}=0.0342496220047,\quad K=-0.0237609202135.
\end{gathered}
\]


**C — K lớn nhất đã thử**

\[
\begin{gathered}
D_r=0.08\,\mathrm{m},\quad \theta_{div}=50\,\mu\mathrm{rad},\quad \theta_{jt}=1.561\,\mu\mathrm{rad},\\
\sigma_h=0.1\,\mathrm{m},\quad \zeta=0^\circ,\quad L=19\,\mathrm{km},\\
\eta_{det}=0.95,\quad \epsilon_{det}=0.005,\quad V_A=1.62499953997,\quad \nu_{raw}=0.25,\\
I_{AB}=0.0116489199771,\quad \beta I_{AB}=0.0110664739783,\quad \chi_{BE}=0.0347449648607,\quad K=-0.0236784908824.
\end{gathered}
\]


## 7. Gánh nặng UAV, khối lượng và công suất

| Cấu hình | Thay đổi HAP | Thay đổi UAV | Gánh nặng phần cứng | K | Robustness |
| --- | --- | --- | --- | --- | --- |
| A — Giữ thông số detector gốc | HAP transmitter optics; HAP pointing/tracking; residual centering requirement; relative geometry and scheduling | Original detector efficiency/noise and 8cm receiver retained | No new UAV receiver group assumed; cooperative tracking hardware unquantified | -0.0569672629018 | Nominal negative; no positive robustness claim |
| B — Tham chiếu cân bằng | HAP transmitter optics; HAP pointing/tracking; residual centering requirement; relative geometry and scheduling | Detector efficiency/noise requirement improved; no larger receiver | Detector group may change; component count/mass/power unknown | -0.0237609202135 | Nominal negative; no positive robustness claim |
| C — K lớn nhất đã thử | HAP transmitter optics; HAP pointing/tracking; residual centering requirement; relative geometry and scheduling | Detector efficiency/noise requirement improved; no larger receiver | Detector group may change; component count/mass/power unknown | -0.0236784908824 | Nominal negative; no positive robustness claim |


Ưu tiên giữ8 cm và chuyển optics/PAT sang HAP là tiêu chí thiết kế, chưa chứng minh nhẹ hơn theo kg/W. Mô hình không có mass/power cho receiver, detector, ADC, beacon, gimbal hoặc controller; không thể định lượng flight-time hay năng lượng tiết kiệm. Các proxy có trong [table_2_engineering_comparison.csv](table_2_engineering_comparison.csv): Dtx99, tỷ lệ cải thiện jitter/centering/noise, offset/beam radius, nhóm detector có thay yêu cầu hay không. Số linh kiện và điện năng còn thiếu được ghi NOT_AVAILABLE. Nhãn “cân bằng” của B chỉ giới hạn efficiencyη≤.9; không xác nhận yêu cầu PAT là mức cải thiện nhỏ hoặc phần cứng khả thi.

Khi mọi tham chiếu còn âm, thứ tự gần-zero không đủ để biện minh nâng cấp phần cứng. Không khuyến nghị mua detector/PAT hoặc thêm AO nặng, telescope lớn, laser onboard công suất cao để theo đuổi các điểm âm này.

## 8. Robustness với nguồn cố định

| ηdet | εdet | Nominal512 | Jitter+10% | Center+10% | Cả hai+10% | Cả hai+20% | Noise.0135 | Noise.005 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.8 | 0.0135 | -0.0569672629018 | -0.0569824132323 | -0.0571442663482 | -0.0571602779402 | -0.0573824050532 | -0.0569672588088 | -0.0239253680586 |
| 0.85 | 0.0135 | -0.0568740882494 | -0.056890188079 | -0.0570621794486 | -0.0570791934929 | -0.0573152195023 | -0.056874083902 | -0.0238432097118 |
| 0.9 | 0.0135 | -0.0567808175033 | -0.0567978671372 | -0.0569799993965 | -0.0569980160968 | -0.0572479428981 | -0.0567808129016 | -0.0237609155731 |
| 0.95 | 0.0135 | -0.0566874507863 | -0.0567054505303 | -0.0568977263211 | -0.0569167458817 | -0.0571805753818 | -0.0566874459305 | -0.0236784859857 |
| 0.8 | 0.005 | -0.023925372186 | -0.0239420302304 | -0.0241207601153 | -0.0241385077537 | -0.0243856634299 | -0.0569672588088 | -0.0239253680586 |
| 0.85 | 0.005 | -0.0238432140958 | -0.0238609123058 | -0.0240507932957 | -0.0240696473738 | -0.02433219726 | -0.056874083902 | -0.0238432097118 |
| 0.9 | 0.005 | -0.0237609202135 | -0.0237796584987 | -0.0239806885826 | -0.0240006488045 | -0.0242785871812 | -0.0567808129016 | -0.0237609155731 |
| 0.95 | 0.005 | -0.0236784908824 | -0.0236982691567 | -0.0239104463728 | -0.023931512448 | -0.0242248336829 | -0.0566874459305 | -0.0236784859857 |


Các perturbation giữ nguyên VA,ν,Dr,divergence,geometry và detector efficiency. Hai cột noise đổi đúng một biến. Nominal headline dùng512×48, bảng perturbation dùng256×32; sai khác cùng điểm được lưu ở convergence.json, không phải cải thiện thật. Không gọi điểm nominal âm là robust; không dùng perturbation làm nguồn tái tối ưu để che mất margin. Các positive nếu có phải vượt2×.95×observed MI change; đây chỉ là kiểm tra hội tụ quan sát.

## 9. Xác minh số và giới hạn

33 scoped checks CURRENTLY_VERIFIED_PASS trên 9923 logged nodes (9821 mới, 102 reuse đúng source/parameters/orders và hash dòng cũ). Mass/outage, passive support, m1/mh/Tf, noise-once, exact C,w, PSD/symplectic physicality, raw K, full-Z33/129, entropy110 digits, width32/64, direct mixture/Fourier và half output spacing được kiểm tra. Selected MI256×32 so512×48 có max observed difference 5.15439e-09. Không đổi tolerance sau khi thấy dấuK.

Startup bảo vệ6445 files, ngoại trừ năm task ledgers được phép cập nhật. Mô hình được import giữ nguyên bytes. Frozen SHA hiện khớp re-freeze ghi trong repo nhưng khác historical expected ởAGENTS.md; giữ promotion blocker. Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS, security_valid=false/hardware_validated=false, ObjectiveC USER_STOPPED. Không training/test/heldout/publication, không thay production baseline hoặc threshold approval.

Đây là evaluator chẩn đoán, chưa có đầy đủ fading-protocol proof, finite-key/composable security, phase calibration, reconciliation implementation hay measured aperture/PAT/detector. Việc giữ nguyên mô hình không làm các giới hạn cũ biến mất.

## 10. Kết luận và cách tái kiểm tra

Trong các tổ hợp đã thử, receiver8 cm với εdet≥.005 chưa tạo được K dương. Giảmnoise giúp thu hẹp gap nhưng optics/PAT/geometry/source adaptation vẫn chưa đủ trong catalog và miền đã xét. Không hạnoise dưới sàn hoặc thay security để tạo kết quả dương. Điểm K lớn nhất=-0.0236784908824; vẫn phải phân biệt gap số với tuyên bố bảo mật.

Tại điểm C, các thành phần noise trước detector theo đúng convention hiện có là N_fading=0.000267272229721, N_channel=0.000200276440424, N_detector=0.00526315789474; N_post=0.00544417123664. Detector term lớn gấp 26.2795 lần channel term và 19.6921 lần fading term. Với T_f=0.0106030752956, excess noise effective tổng vẫn bằng 0.540475890731 SNU. Đây là chẩn đoán giới hạn chính ở điểm đã chọn, không chứng minh detector là giới hạn duy nhất trên toàn miền.

Không có cơ sở hiện tại để khẳng định UAV nhẹ/công suất thấp tạo secure key dưới các giới hạn này. Giữ A làm đối chứng, B làm cải thiện detector có giới hạn và C làm closest-tested reference cho manuscript; giữ cả số âm và missing hardware evidence. Không promote chúng thành baseline hoạt động.

Đầu ra chính: [table_1_recommended_parameters.csv](table_1_recommended_parameters.csv), [table_2_engineering_comparison.csv](table_2_engineering_comparison.csv), detector_scenario_best.csv, stage_A/B/C/D CSVs, source_comparison.csv, robustness.csv, selected_sensitivity.csv và all_evaluations.csv. Mỗi numerical node có exact source hash, C,w và thông số đầy đủ; JSONL giữ nguồn gốc new/reused. Tám hình vectorPDF/350dpiPNG trong figures/ dùng raw signedK, đườngK=0 và baseline; đoạn nối chỉ nối node đã tính, không nội suy nguồn.

Từ project directory, chạy ` .\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/verify.py ` để kiểm tra saved receipt, không chạy lại khoa học. Producer tái lập được ghi trong README.md; không rerun producer đã hoàn tất hoặc sửa artifact đã seal.
