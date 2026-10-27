# Giữ receiver 8 cm: geometry, detector và PAT — 2026-10-22

Đã thực hiện yêu cầu mới, giữ **Dr = 0.08 m tại mọi node** và detector **UNTRUSTED**. Không quét lại khẩu độ thu. Regression lịch sử khớp K=-.058724314679977559 trước khi tìm kiếm. Kết quả chính dùng mô hình bounded circular-Gaussian đã chốt và actual pooled fading MI, không dùng effective-Gaussian MI thay thế.

**Detector gốc:** chưa có điểm dương trong miền đã thử. Điểm A gần zero nhất được chọn ở độ cao20/1 km có K=-0.0526131157736. **Detector hỗ trợ:** K_B=0.000178029235292; **nonideal tốt nhất trong shortlist:** K_C=0.00096225853438. Đây là numerical diagnostic; chưa có thiết kế nào được xác nhận hardware/security thực. B và C là hai bộ tham số được đánh giá riêng.

| Cấu hình | HAP/UAV(km) | ζ(độ) | L(km) | Div(µrad) | Jitter(µrad) | σh(m) | ηdet | εdet | VA | νraw | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — Detector gốc | 20/1 | 0 | 19 | 25 | 1 | 0.05 | 0.8 | 0.0135 | 1.8 | 0.21 | -0.0526131157736 |
| B — Có hỗ trợ detector | 20/1 | 15 | 19.6702474278 | 25 | 1 | 0.05 | 0.8 | 0.0005 | 1.62499953997 | 0.25 | 0.000178029235292 |
| C — Nonideal tốt nhất đã thử | 20/1 | 15 | 19.6702474278 | 25 | 1 | 0.05 | 0.95 | 0.0005 | 1.62499953997 | 0.25 | 0.00096225853438 |


Mọi tốc độ theo mỗi lần truyền, gồm outage; giữ K âm nguyên dấu. “Best” là best exact tested trong catalog 233 nguồn, không global optimum. Các ngưỡng giữ nguồn cố định và chỉ có phạm vi nhánh đã có bracket.

## Baseline, provenance và khí quyển

K lịch sử=-.0587243146799775588 được tái tính bằng đúng hàm trial và saved moments. baseline bounded mới có m1=0.000260639768789559, Tf=0.000241936007530533, I=0.000753762353882783, chi=0.0594124373159937, K=-0.058696363079805. Sự khác biệt hai baseline là đổi optical law ở nghiên cứu trước; không ép hai mô hình trả cùng số. regression.json và geometry_regression.json xác minh riêng trước Stage A. DeltaK chính của Table 1 lấy baseline bounded cùng mô hình; delta so historical được lưu thêm và ghi rõ không là causal sensitivity.

Baseline: HAP 20 km, UAV 1 km, ζ30°, L21.9393102292km, lambda1550nm, Dr 8 cm, full-angle divergence 233 µrad, theta_jt 15.61 µrad mỗi trục, sigma_h 1 m, AoA SD1.5mrad, FOVhalf6.25mrad, tau_zen.92, epsilon_ch.0186, eta_det.8, epsilon_det.0135 output quadrature SNU, beta.95, homodyne1D, AO/phaseOFF như giả thiết trước. configs/channel.yaml/default.yaml có223µrad ởtheta_div_rad; không phải angularjitter. Điểm223 được lưu riêng, không thay baseline233.

Bạn cung cấp các cặp(Vkm, tau_zen)=(23,.92),(15,.89),(5,.75), lưu weather_input.json. Dùng eta_atm=tau_zen^secζ trực tiếp, visibility chỉ là nhãn; không nhân thêmKruse. Bảng này **chưa phải vertical extinction profile**. HAP/UAV thay đổi độ cao vẫn được tính lạiHV/diffraction/pointing/fading nhưng giữ zenith optical depth để làm sensitivity. Các điểm này mang HEIGHT_CHANGED_FIXED_TAU_SENSITIVITY_VERTICAL_EXTINCTION_MISSING, không đủ để xác nhận khí quyển hay khả năng bay. Chỉ chọn khuyến nghị ởHAP 20/UAV 1, nơi attenuation có cùng định nghĩa scenario gốc; không root L bằng cách tự thay độ cao.

## Mô hình và workflow

w0=2lambda/(pi theta_div), wL=w0 sqrt[1+(Llambda/(pi w0²))²], w_eff=wL sqrt(1+Gd), Dtx99=2w0 sqrt(ln100/2). Mọi theta_div làfull angle. HV dùng đúng profile wind21m/s, Cn²ground1e-14; hai tích phân theo độ cao được tính lại trên[h_UAV, h_HAP], cùng secζ factors cũ. L=(h_HAP-h_UAV)/cosζ và sigma_s²=sigma_h²+(Ltheta_jt)². Không chỉ scaleL mà giữ stale turbulence/beam terms.

Kênh thụ động cũ được tái sử dụng: S~N(-v/2, v), random width w=w_eff exp(-S/2), Rayleigh offsetr; circular collection H=F_noncentralChiSquare2(D_r²/w²;4r²/w²), activeT=eta_atm H. Giữ atomP0=exp[-FOV²/(2sigma_AoA²)] tạiT0 riêng; mỗi beam có tổng công suất1, không cógain hay clippingT. m1=E[T], mh=E[sqrtT], Tf=mh².

N_fading=(m1-Tf)VA, N_channel=.0186m1, N_detector=epsilon_det/eta_det;
N_post=eta_det(N_fading+N_channel)+epsilon_det;
a=1+VA, b=1+eta_det Tf VA+N_post.
Vacuum1 xuất hiện một lần; không thêm1-eta_det lần nữa vào excess. Untrusted assignment giữ cảdetector loss/noise choEve. C, w lấy đúng payload/hash của cùng256state ensemble. Full-Z numerical maximization trên giao interval correlation với physical covariance; nu3_hom=sqrt[a(a-z²/b)], không trộn heterodyneMI.

MI chính dùng p(y|x)=E_T Normal(y;2sqrt(eta_det T)x,1+eta_det*.0186T+epsilon_det). Không cộng N_fading lần nữa bên trong conditional variance, khôngCSIconditioning/postselection. K=.95I_actual-chi. I_AB_surrogate/K_surrogate được lưu riêng. Fourier inversion chỉ tăng tốc cùng Gaussianmixture; direct-likelihood và halfspacing checks có receipt.

Stage A giữMB(.165, VA5.475). Stage B stagedtiers và geometry hữu hạn, giữdetector gốc; Stage C nhắm các beam/pointing/noise regions, không Cartesian toàn bộ9tham số. Stage D dùng233 source exact(197MB,36Uniform), targetedalternating4starts, dừngdeltaK1e-8/catalogfixedpoint. Không AP hoặc nội suyC, w/SKR. Các matching8cm nodes từ nghiên cứu trước được reuse theo source hash/parameters/quadrature và hash từng dòng; không reuse số khácreceiver/measurement/detector/weather. Các screened MI128x16 được refinement256x32/512x48/1024x64, observedchange<2e-6 và positive vượt2lần ảnh hưởng quan sát lênK. Đây không phải rigorous errorbound/security certification.

## Q1. Giữ8cm và detector gốc có SKR dương không?

Chưa tìm được, kể cả sau catalog ở các context chọn và wider-beam checks. A dùng đúngeta=.8, epsilon=.0135; K=-0.0526131157736, gap chi-betaI=0.0526131157736 bit/use khiK âm. Không suy ra no-key theorem ngoài miền/tập nguồn đã thử. Sáu geometry/PAT branches trong phase1.json, kể cả các height sensitivity, đều được giữ để kiểm chứng phạm vi.

## Q2. Rút ngắn liên kết giúp bao nhiêu?

GiữHAP 20/UAV 1, nadir rútL từ21.9393 xuống19km; từng nguồn/optics/detector được tính lại tạiζ0,5,...30. Figure 1/2 và Table 1 có số thực, không giả địnhK tăng đơn điệu. Ở nguồn cố định và pointing1m, khoảng cách ngắn hơn có thể tăng relativeoffset/fading và không làmK dương. Sau optics/PAT/detector upgrade, ảnh hưởng phụ thuộc beam và source; các đườngselected cho biết gain thực. HAP17..25/UAV 1..5 sensitivity cóL12..27.7km nhưng attenuationtheo height chưa hiệu chuẩn; không dùng để tuyên bố range hay độ cao vận hành tối ưu.

Đối chiếu riêng việc chuyển30°→15° ở cùng nguồn, optics và detector cho từng dòng (cả hai node cùng quadrature256x32):

| Cấu hình | K tại30°/21.9393 km | K tại15°/19.6702 km | DeltaK do geometry |
| --- | --- | --- | --- |
| A — Detector gốc | -0.0539833861269 | -0.0529336885997 | 0.00104969752718 |
| B — Có hỗ trợ detector | -0.000596295049866 | 0.000178043947328 | 0.000774338997193 |
| C — Nonideal tốt nhất đã thử | 1.23163800189e-05 | 0.000962275945953 | 0.000949959565934 |



| HAP/UAV(km) | ζ | L(km) | Div | VA | ν | K detector gốc — height sensitivity |
| --- | --- | --- | --- | --- | --- | --- |
| 20/1 | 30 | 21.9393102292 | 10 | 0.741661515149 | 0.2 | -0.0556622120386 |
| 20/1 | 0 | 19 | 10 | 0.741661515149 | 0.2 | -0.0562760481118 |
| 17/1 | 0 | 16 | 10 | 0.60833317999 | 0.25 | -0.0573579217156 |
| 20/3 | 0 | 17 | 10 | 0.60833317999 | 0.25 | -0.056817585576 |
| 20/5 | 0 | 15 | 10 | 0.60833317999 | 0.25 | -0.0576306783602 |
| 17/5 | 0 | 12 | 20 | 0.741661515149 | 0.2 | -0.0559423442584 |



Kết hợp detector noise.001 với hai geometry thay đổi độ cao (chỉ sensitivity, chưa có vertical extinction calibration):

| HAP/UAV(km) | L(km) | Div(µrad) | ηdet | εdet | VA | ν | K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20/5 | 15 | 10 | 0.8 | 0.001 | 0.519444439928 | 0.3 | -0.0100284722225 |
| 17/5 | 12 | 20 | 0.8 | 0.001 | 0.519444439928 | 0.3 | -0.00813823284808 |



## Q3. Tham số nào tác động lớn nhất?

| Tham số | Giá trị cho K lớn nhất trong OFAT | K | DeltaK cùng model |
| --- | --- | --- | --- |
| zenith | 30 | -0.0586963625888 | 4.9100999655e-10 |
| HAP_height | 25 | -0.0585399788908 | 0.000156384188992 |
| UAV_height | 1 | -0.0586963625888 | 4.9100999655e-10 |
| detector_efficiency | 0.8 | -0.0586963625888 | 4.9100999655e-10 |
| detector_noise | 0 | -0.00061181315057 | 0.0580845499292 |
| divergence | 233 | -0.0586963625888 | 4.9100999655e-10 |
| angular_jitter | 1 | -0.0586651852505 | 3.11778292838e-05 |
| position | 0.05 | -0.0584504309855 | 0.000245932094292 |


Detector excess noise có tác động lớn nhất ở baseline nguồn cố định. Các điểmeta=1/noise=0 chỉ là diagnosticreferences. Cải thiệnefficiency riêng không giải quyết geometry/PAT/fading; giảmdivergence không làgain miễn phí. “Ít âm hơn” trên kênh yếu không đồng nghĩa collection tốt hơn, nên shortlist dựa cảmomentquality vàK, không chỉ chọn điểm tối nhất cóHolevonhỏ.

## Q4. Chỉ nâng detector có đủ không?

OFAT không có điểm dương ở nguồn cố định. Catalog detector-only có sẵn ở epsilon.0005 và 0; đây là counterfactual tách riêng ởStage D, không đổi quang học gốc hoặc nguồn trongTable 1. Xem catalog_detector_only_*.csv. Không gọi zero-noise là detector đạt được và không đổi thành trusted để có dương.

| ηdet | εdet | VA | νraw | K best exact tested — optics gốc |
| --- | --- | --- | --- | --- |
| 0.8 | 0.0005 | 0.1 | 0.3 | -0.00337318474961 |
| 0.8 | 0 | 0.025 | 0.3 | -4.00079237878e-05 |



## Q5. Những tổ hợp thay đổi nào tạo dương?

Table 2 chỉ chứa các configuration có actual K>0 sau refinement. Chúng cần đồng thờibeam/PAT/relativecentering và detector; giữDr 8 cm không đồng nghĩa giữ nguyên transmitter hoặc receiver electronics. Các thành phầnthay đổi mức20lần sigma_h, nhiều lần angularjitter/divergence/noise là yêu cầu mạnh, không tự gọi “moderate”. Rawpositive trong Stage C source seed và source catalog được lưu riêng để xác định thay đổi nào đủ.

| Cấu hình | HAP/UAV(km) | ζ(độ) | L(km) | Div(µrad) | Jitter(µrad) | σh(m) | ηdet | εdet | VA | νraw | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — Detector gốc | 20/1 | 0 | 19 | 25 | 1 | 0.05 | 0.8 | 0.0135 | 1.8 | 0.21 | -0.0526131157736 |
| B — Có hỗ trợ detector | 20/1 | 15 | 19.6702474278 | 25 | 1 | 0.05 | 0.8 | 0.0005 | 1.62499953997 | 0.25 | 0.000178029235292 |
| C — Nonideal tốt nhất đã thử | 20/1 | 15 | 19.6702474278 | 25 | 1 | 0.05 | 0.95 | 0.0005 | 1.62499953997 | 0.25 | 0.00096225853438 |



Giữ cả geometry gốc30°/21.9393 km cũng có một điểm dương nhỏ khi tăng efficiency lên.95. Đây là phép tính trực tiếp đã refinement, không phải khuyến nghị có margin:

| Cấu hình | ζ | L(km) | ηdet | εdet | K | Observed MI change |
| --- | --- | --- | --- | --- | --- | --- |
| C0 — Geometry gốc, sát ngưỡng | 30 | 21.9393102292 | 0.95 | 0.0005 | 1.23021472354e-05 | 1.49818774262e-08 |



## Q6. Tập thay đổi tối thiểu và các ngưỡng là gì?

| Cấu hình | Sốthay đổi vật lý | Tham số | Giá trị gốc | Giá trị mới | K |
| --- | --- | --- | --- | --- | --- |
| A — Detector gốc | 4 | zenith_deg; divergence_urad; jitter_urad; sigma_h_m | zenith_deg=30; divergence_urad=233; jitter_urad=15.61; sigma_h_m=1 | zenith_deg=0; divergence_urad=25; jitter_urad=1; sigma_h_m=0.05 | -0.0526131157736 |
| B — Có hỗ trợ detector | 5 | zenith_deg; divergence_urad; jitter_urad; sigma_h_m; epsilon_det | zenith_deg=30; divergence_urad=233; jitter_urad=15.61; sigma_h_m=1; epsilon_det=0.0135 | zenith_deg=15; divergence_urad=25; jitter_urad=1; sigma_h_m=0.05; epsilon_det=0.0005 | 0.000178029235292 |
| C — Nonideal tốt nhất đã thử | 6 | zenith_deg; divergence_urad; jitter_urad; sigma_h_m; eta_det; epsilon_det | zenith_deg=30; divergence_urad=233; jitter_urad=15.61; sigma_h_m=1; eta_det=0.8; epsilon_det=0.0135 | zenith_deg=15; divergence_urad=25; jitter_urad=1; sigma_h_m=0.05; eta_det=0.95; epsilon_det=0.0005 | 0.00096225853438 |
| C0 — Geometry gốc, sát ngưỡng | 5 | divergence_urad; jitter_urad; sigma_h_m; eta_det; epsilon_det | divergence_urad=233; jitter_urad=15.61; sigma_h_m=1; eta_det=0.8; epsilon_det=0.0135 | divergence_urad=25; jitter_urad=1; sigma_h_m=0.05; eta_det=0.95; epsilon_det=0.0005 | 1.23021472354e-05 |


Các count tách source changesVA/nu khỏi hardware/geometry. Đây là tối thiểu trong shortlist/coordinate relaxation đã thử, không chứng minh ít nhất toàn miền. Thresholds giữsource fixed, target0 và1e-4; mốc1e-4 chỉ engineering comparison, không là định nghĩa security. Lcrit chỉ xuất khi bracketζ0..30 ởheights20/1 có signchange; không extrapolate dưới19km hoặc ngoàiheightweather hợp lệ.

B/C đều đòi hỏi divergence giảm 9.32 lần, angular SD giảm 15.61 lần, horizontal SD giảm 20 lần và detector noise variance giảm 27 lần. C nâng efficiency thêm 18.75% tương đối so với0.8. Đây là yêu cầu mạnh; không gọi là cải thiện nhỏ chỉ vì receiver vẫn8cm. B chuyển từ góc30° sang15°, tương ứng khoảng cách ngang tương đối từ10.97km xuống5.09km; chi phí di chuyển/điều khiển platform chưa được mô hình hóa.

necessary_changes.csv kiểm tra bằng cách hoàn nguyên từng biến của B/C về baseline, giữ các biến khác và nguồn cố định. Năm thay đổi vật lý của B đều cần cho dấu dương trên nhánh đó. Với C, hoàn nguyên geometry về30° vẫn còn K dương nhỏ; hoàn nguyên efficiency về.8 cho lại B dương. Do đó rút ngắn link và nâng efficiency là hai cách đánh đổi để tăng margin, không phải cả hai cùng bắt buộc cho mọi điểm dương. Kết luận này chỉ có phạm vi nhánh đã xét, không chứng minh tối thiểu toàn cục.

| Cấu hình | Biến | TargetK | Root | Lcrit(km) | Residual |
| --- | --- | --- | --- | --- | --- |
| B_detector_assisted | eta_det | 0 | 0.765123707179 |  | -2.62442845234e-13 |
| B_detector_assisted | eta_det | 0.0001 | 0.784752809544 |  | -1.53880990524e-13 |
| B_detector_assisted | epsilon_det | 0 | 0.000534930400999 |  | -3.97598620694e-14 |
| B_detector_assisted | epsilon_det | 0.0001 | 0.000515299658258 |  | -3.40324150154e-14 |
| B_detector_assisted | jitter_urad | 0 | 1.17244018653 |  | -9.92261828259e-16 |
| B_detector_assisted | jitter_urad | 0.0001 | 1.07946918497 |  | -4.82862990044e-16 |
| B_detector_assisted | sigma_h_m | 0 | 0.0514290375887 |  | 2.01644256848e-13 |
| B_detector_assisted | sigma_h_m | 0.0001 | 0.0506353607884 |  | -2.2180907027e-11 |
| B_detector_assisted | zenith_deg | 0 | 19.8621975322 | 20.2017517665 | 1.11022302463e-15 |
| B_detector_assisted | zenith_deg | 0.0001 | 17.3451652069 | 19.905165761 | -8.08991003527e-16 |
| C_best_nonideal_tested | eta_det | 0 | 0.765123707179 |  | -2.62442845234e-13 |
| C_best_nonideal_tested | eta_det | 0.0001 | 0.784752809544 |  | -1.53880990524e-13 |
| C_best_nonideal_tested | epsilon_det | 0 | 0.000692956843806 |  | -6.23806561961e-14 |
| C_best_nonideal_tested | epsilon_det | 0.0001 | 0.000672787325666 |  | -5.1684961107e-14 |
| C_best_nonideal_tested | jitter_urad | 0 | 1.63061863655 |  | -8.04911692853e-16 |
| C_best_nonideal_tested | jitter_urad | 0.0001 | 1.57872113655 |  | -1.31553025851e-15 |
| C_best_nonideal_tested | sigma_h_m | 0 | 0.0560523501085 |  | -5.82867087928e-16 |
| C_best_nonideal_tested | sigma_h_m | 0.0001 | 0.0554745171917 |  | -1.81513061959e-15 |
| C_best_nonideal_tested | zenith_deg | 0.0001 | 29.0233425632 | 21.7286360282 | 1.61268296894e-15 |


threshold_status.csv ghi cảNO_SIGN_CHANGE, cùng giá trị hai đầu; không tự gán ηcrit/Lcrit nếu không có bracket. geometry_detector_roots.csv giữ boundary exact noise/zenith cùng source, Figure 7 không nội suy tạo vùng tối ưu.

| Cấu hình | Divergencecrit(µrad) | TargetK | Residual |
| --- | --- | --- | --- |
| B_detector_assisted | 27.1837190931 | 0 | -1.03656666584e-13 |
| B_detector_assisted | 26.12613613 | 0.0001 | -1.40414616783e-14 |
| C_best_nonideal_tested | 32.0134255787 | 0 | 1.80411241502e-16 |
| C_best_nonideal_tested | 31.35527463 | 0.0001 | 4.94335204281e-15 |



## Q7. MB có mở thêm vùng dương không?

| Cấu hình | K fixed MB | K bestUniform (VA khác) | K best MB (VA khác) | Gain chọn cảVA, ν |
| --- | --- | --- | --- | --- |
| A — Detector gốc | -0.0580649910329 | -0.0607195979723 | -0.0526130217257 | 0.00545196930724 |
| B — Có hỗ trợ detector | -0.00688860765311 | -0.00590715801964 | 0.000178110273733 | 0.00706671792684 |
| C — Nonideal tốt nhất đã thử | -0.00714175128788 | -0.00623130528145 | 0.000962354413477 | 0.00810410570136 |


Để tách shaping khỏi việc chọn năng lượng, dùng cùng optics/detector và VA chung gần nhất có đủ hai nguồn exact:

| Cấu hình | VA chung | K Uniform | K MB | DeltaK cùng VA | νMB |
| --- | --- | --- | --- | --- | --- |
| A_original_detector | 2 | -0.0759448895717 | -0.0526364854564 | 0.0233084041154 | 0.24 |
| B_detector_assisted | 1.5 | -0.0116814413566 | -3.22254944564e-05 | 0.0116492158621 | 0.5 |
| C_best_nonideal_tested | 1.5 | -0.0125998865031 | 0.000714988035585 | 0.0133148745387 | 0.5 |


Hash riêng của hai nguồn nằm trong same_energy_shaping.csv; không dùng C, w của MB cho Uniform. So sánh hai family đã chọn VA khác nhau không được gọi toàn bộ là shaping gain. Dấu K của fixed MB so với best MB cho biết source adaptation có chuyển kết quả âm thành dương tại cùng kênh hay không. Nguồn thiếu không được nội suy. Đây là best exact tested, không phải tối ưu toàn cục.

## Q8. Dương có sống sót khi pointing xấu đi10–20% không?

| Cấu hình | K nominal | K nhỏ nhất trong 25 perturbations | Worst fine512x48 |
| --- | --- | --- | --- |
| A — Detector gốc | -0.0526131157736 | -0.0543258751619 | -0.0543258890776 |
| B — Có hỗ trợ detector | 0.000178029235292 | -0.00149136132683 | -0.00149137374407 |
| C — Nonideal tốt nhất đã thử | 0.00096225853438 | -0.00100518203389 | -0.00100519674523 |


| Cấu hình | Chỉ angular+20% | Chỉ horizontal+20% | Cả hai+10% | Cả hai+20% |
| --- | --- | --- | --- | --- |
| A — Detector gốc | -0.0528190768234 | -0.0541016936785 | -0.0534099305009 | -0.0543258751619 |
| B — Có hỗ trợ detector | -3.14796136874e-05 | -0.00125595370523 | -0.000590845472172 | -0.00149136132683 |
| C — Nonideal tốt nhất đã thử | 0.000714977774627 | -0.00072809034141 | 5.53441536632e-05 | -0.00100518203389 |


Mỗi trường hợp giữ nguồn, detector và optics của điểm nominal; nhân hai residual độc lập và đồng thời với các hệ số0.8,0.9,1,1.1,1.2. Không tái tối ưu nguồn để che việc mất margin. B mất dấu dương khi cả hai lỗi tăng10%. C còn dương khi cả hai tăng10%, nhưng K chỉ khoảng5.53e-5, thấp hơn mốc so sánh kỹ thuật1e-4. Cả B và C đều âm khi hai lỗi cùng tăng20%; chưa có ứng viên được chọn nào bền trước mức suy giảm này.

## Q9. Optics, PAT, độ cao và detector có hợp lý không?

| Cấu hình | Dtx99(cm) | wL(m) | w_eff(m) | sigma_s(m) | eta_atm | Pout |
| --- | --- | --- | --- | --- | --- | --- |
| A — Detector gốc | 11.9786990098 | 0.240757480714 | 0.241842619495 | 0.0534883164813 | 0.92 | 0.000169856676561 |
| B — Có hỗ trợ detector | 11.9786990098 | 0.249026004791 | 0.250189655719 | 0.0537300533582 | 0.917297901998 | 0.000169856676561 |
| C — Nonideal tốt nhất đã thử | 11.9786990098 | 0.249026004791 | 0.250189655719 | 0.0537300533582 | 0.917297901998 | 0.000169856676561 |


Dtx99 chỉ là đường kính chứa99% công suất của Gaussian lý tưởng; chứa99.99% cần đường kính lớn hơn sqrt2 lần. Chưa có số đo về hard-pupil diffraction, M², coupling throughput, mount hoặc vibration; không xem receiver 8 cm là toàn bộ tải quang. HAP phải mang transmitter lớn hơn và hệ PAT chính xác hơn. [Walsh et al., coherent drone optical link](https://www.nature.com/articles/s41598-022-22027-0) dùng optical tracking và tip/tilt lồng nhau để giữ coupling. Đây là thí nghiệm truyền tin cổ điển, không chứng minh SKR hoặc các residual1µrad/0.05 m tại khoảng cách và độ cao ở đây. GPS phục vụ acquisition/coarse; độ chính xác GPS không đồng nhất với độ lệch tâm beam còn dư.

theta_jt là residual transmitter pointing; sigma_h là sai lệch vị trí/tâm beam tương đối còn lại. Phép cộng variance giả định hai thành phần độc lập; không đếm cùng chuyển động hai lần. Receiver attitude/AoA được giữ riêng trong P0/FOV, không dùng việc giảm theta_jt để xóa outage. UAV ở5km hoặc HAP17–25 km cần platform và operating envelope riêng, chưa mặc nhiên khả thi. Các khuyến nghị chính giữ độ cao20/1 km để tránh phụ thuộc profile extinction còn thiếu.

epsilon_det là output quadrature excess noise trong SNU của mô hình; không tự đồng nhất với v_el của một bài khác. Nâng efficiency hoặc giảm noise cần hiệu chuẩn tại đúng LO power, bandwidth, shot noise, mode visibility và receiver coupling. Chưa có component specification hoặc số đo mass/power nên chưa cam kết đạt được. [Nghiên cứu kiểm soát excess noise](https://www.nature.com/articles/srep19201) là dẫn chứng về kỹ thuật kiểm soát noise, không xác nhận các mức noise/η của UAV hoặc security untrusted ở đây. Efficiency1 và noise0 chỉ là tham chiếu lý tưởng, không phải khuyến nghị phần cứng.

Với các cặp visibility/transmittance bạn cung cấp, giữ cùng nguồn và PAT:

| Cấu hình | V(km) | tau_zen | eta_atm | K |
| --- | --- | --- | --- | --- |
| B — Có hỗ trợ detector | 23 | 0.92 | 0.917297901998 | 0.000178029235292 |
| B — Có hỗ trợ detector | 15 | 0.89 | 0.886348837411 | 4.00902376908e-05 |
| B — Có hỗ trợ detector | 5 | 0.75 | 0.742427246855 | -0.000587708836987 |
| C — Nonideal tốt nhất đã thử | 23 | 0.92 | 0.917297901998 | 0.00096225853438 |
| C — Nonideal tốt nhất đã thử | 15 | 0.89 | 0.886348837411 | 0.000792244364975 |
| C — Nonideal tốt nhất đã thử | 5 | 0.75 | 0.742427246855 | 1.9157613979e-05 |
| A — Detector gốc | 23 | 0.92 | 0.92 | -0.0526131157736 |
| A — Detector gốc | 15 | 0.89 | 0.89 | -0.0528095274112 |
| A — Detector gốc | 5 | 0.75 | 0.75 | -0.0537206887041 |


Không cộng thêm Kruse, không giảm channel noise hoặc turbulence để tạo K dương. Các kiểm tra weather vẫn dùng HV gốc; không giả định visibility xác định Cn². Còn dương tại một weather case không đồng nghĩa chịu được weather xấu đồng thời với suy giảm pointing.

## Q10. Bộ tham số nào đưa vào manuscript?

Trong manuscript, trình bày B như **ứng viên gần ngưỡng với ít thay đổi hơn**, giữ A âm làm đối chứng và dùng C để minh họa margin bổ sung khi tăng efficiency. Chưa có ứng viên đủ căn cứ để khuyến nghị triển khai thực tế hoặc gọi là bền trước suy giảm pointing20%. Không thay baseline production. Bộ tham số cụ thể của B đã được tính:

\[
\boxed{\begin{gathered}
D_r=0.08\,\mathrm{m},\quad \theta_{\rm div}=25\,\mu\mathrm{rad},\quad \theta_{\rm jt}=1\,\mu\mathrm{rad},\\
\sigma_h=0.05\,\mathrm{m},\quad \zeta=15^\circ,\quad L=19.6702474278\,\mathrm{km},\\
\eta_{\rm det}=0.8,\quad \epsilon_{\rm det}=0.0005\,\mathrm{SNU},\quad V_A=1.62499953997,\quad \nu_{\rm raw}=0.25,\\
K=0.000178029235292\,\mathrm{bit/use}
\end{gathered}}
\]

| Cấu hình | m1 | Tf | epsilon_f | I_actual | I_surrogate | betaI_actual | chi_BE | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — Detector gốc | 0.0408871661735 | 0.0402761076076 | 0.465174214254 | 0.0400845431546 | 0.040084005971 | 0.0380803159969 | 0.0906934317704 | -0.0526131157736 |
| B — Có hỗ trợ detector | 0.0384952046411 | 0.0379257031467 | 0.059760275612 | 0.0346549889958 | 0.034654596378 | 0.032922239546 | 0.0327442103107 | 0.000178029235292 |
| C — Nonideal tốt nhất đã thử | 0.0384952046411 | 0.0379257031467 | 0.0571582352453 | 0.0409617503498 | 0.0409612006916 | 0.0389136628323 | 0.037951404298 | 0.00096225853438 |



## Artifacts, kiểmtra và giới hạn

Table 1: table_1_individual_sensitivity.csv; Table 2: table_2_positive_8cm.csv; Table 3: table_3_minimum_modifications.csv; Table 4: table_4_SKR_decomposition.csv. all_evaluations.csv/evaluations.jsonl giữ noise decomposition, source identity, physicality và nguồn gốc direct/reused. Catalog và alternating logs ghi từng nguồn và bước P1/P2; không tạo số cho nguồn thiếu cache. height_changed_detector_comparisons.csv chỉ là sensitivity chưa có vertical calibration, không là bằng chứng phần cứng. selection_phase2.json giữ lựa chọn trước khi cập nhật A theo nguồn thắng của catalog cuối; selection.json là lựa chọn cuối.

Tám hình trong figures/ là các plot độc lập, có vector PDF và PNG350dpi; giữ K âm và đường K=0. Dữ liệu đều được đánh giá trực tiếp, đường nối chỉ giúp đọc node; không smooth fit hay nội suy source. validation.json và convergence.json chứa kiểm tra full-Z33/129, entropy110digits, width32/64, direct mixture/Fourier, half spacing, mass/support/PSD/spectrum, noise được tính một lần và HV tích phân độc lập. Quan sát hội tụ không phải rigorous security enclosure. Receipt và verify.py xác minh hash từ dữ liệu đã lưu, không chạy lại tìm kiếm.

Không thay scientific source, security code, cache, config, frozen model hoặc kết quả lịch sử. Không chạy receiver-aperture sweep, AP mới, training, final-test hoặc held-out publication evaluation. Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS và UNVALIDATED_SECURITY_MODEL; discrepancy frozen hash lịch sử và ObjectiveC USER_STOPPED giữ nguyên. Chưa xác minh finite-key, authentication, calibration, phase hardware hoặc proof cho fading tương quan; một functional dương chưa tự trở thành secure key rate thực.
