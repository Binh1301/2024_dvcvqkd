# Thay đổi vật lý tối thiểu để SKR dương — 2026-10-22

Đã chạy tìm kiếm theo giai đoạn với detector untrusted gốc. **Chưa tìm được SKR dương ở receiver 8–30 cm trong các điểm đã thử.** Receiver 40 cm tiến sát ngưỡng nhưng còn âm; tinh chỉnh nhánh này cho điểm báo cáo **40.1 cm**, K=0.0002836738804 bit/use. Đây là điểm gần onset, không bền trước suy giảm pointing. Cấu hình cân bằng **55 cm / 35 µrad / 3 µrad / 0.1 m** có dự trữ tốt hơn. Tất cả receiver được chọn đều thuộc lớp lớn trên30cm; khả năng mang trên UAV chưa được xác minh. Không có kết luận rằng đây là thiết kế đã đủ điều kiện sinh khóa an toàn.

| Cấu hình | Rx (cm) | Divergence (µrad) | Jitter (µrad) | σh (m) | Tx99 (cm) | VA | νraw | K (bit/use) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 40.1 | 25.0785813719 | 1.561 | 0.1 | 11.9411648851 | 1.77777775971 | 0.3 | 0.000283673880404 |
| 2 — Cân bằng, có dự trữ pointing | 55 | 35 | 3 | 0.1 | 8.55621357843 | 2.15 | 0.22 | 0.035149837665 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 55 | 15 | 3 | 0.1 | 19.9644983497 | 2.15 | 0.22 | 0.0804568149166 |


Các tốc độ là raw K có dấu, theo mỗi lần truyền, gồm outage. Dùng MI của likelihood fading thực, không dùng Gaussian surrogate làm kết quả chính. Nhãn chung: BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY, security_valid=false, hardware_validated=false. Đường kính40.1cm là điểm làm tròn lên theo bước1mm trên nhánh cục bộ đã tìm nghiệm, không là cực tiểu toàn cục hay dung sai chế tạo1mm.

## Cấu hình gốc và nơi lấy giá trị parameter

Nguồn baseline manuscript: configs/manuscript_mobility.json và src/manuscript_mobility.py, đã được dùng bởi hai nghiên cứu trước. D_r=.08m; divergence full233µrad; jitter góc mỗi trục15.61µrad; sigma_h=1m; HAP20km/UAV1km; zenith30°; L=21.9393102292058km; lambda1550nm. AoA SD1.5mrad, FOV half6.25mrad, tau_zen=.92; eta_atm30°=0.908208965418144; P0=0.000169856676561411. Channel excess.0186, detector eta.8/excess output.0135, beta.95, homodyne1D, AO OFF và phase OFF theo giả thiết lịch sử. Nguồn cố định StageA–D là MB(nu_raw=.165,VA=5.475), hash a5d615b5c8c3462013117a29d17fa1edee8632a49de0dac23318b504ad059f82.

configs/channel.yaml và configs/default.yaml hiện chứa **223µrad ở theta_div_rad**, không phải angular jitter; theta_jt_rad vẫn15.61e-6. Hai config active có tau_zen=null và mapping phase chưa giải quyết, nên không tự chạy production evaluator. Diagnostic này kế thừa scenario manuscript có provenance và không thay config active. Điểm223µrad được lưu riêng trong BảngA, không đổi baseline233µrad.

Baseline trên mô hình bounded mới: m1=0.000260639768789559, Tf=0.000241936007530533, I_AB=0.000753762353882783, betaI=0.000716074236188644, chi_BE=0.0594124373159937, K=-0.058696363079805. Regression historical trial riêng vẫn K=-.0587243146799775588; sự khác biệt đến từ mô hình quang học đã đổi ở nghiên cứu trước, không phải thay detector.

## Công thức và phương pháp số đã dùng

Với theta_div là **full angle**, w0=2lambda/(pi theta_div), wL=w0 sqrt[1+(Llambda/(pi w0²))²], w_eff=wL sqrt(1+Gd). Dtx99=2w0 sqrt(ln100/2). Tất cả giá trị nằm ở transmitter_apertures.csv; không coi giảm divergence là miễn phí. Beam tròn Gaussian ngẫu nhiên độ rộng w=w_eff exp(-S/2), S~N(-v/2,v), v=0.0539620777961917. Sai lệch tâm Rayleigh có SD mỗi trục sigma_s=sqrt[sigma_h²+(L theta_jt)²]. Mỗi beam tích phân toàn mặt phẳng bằng1; công suất thu tròn dùng CDF noncentral-chi-square chính xác: H(r,w)=F_chi2prime(df2,noncentrality4r²/w²)(D_r²/w²). Trên active T=eta_atm H, cộng atomP0 tạiT=0. H thuộc[0,1], T thuộc[0,eta_atm]; giữ atom riêng, không clip hay normalize một tail phi vật lý.

m1=E[T], mh=E[sqrt(T)], Tf=mh². Noise trước detector:
N_fading=(m1-Tf)VA; N_channel=.0186m1; N_detector=.0135/.8=.016875.
N_post=.8(N_fading+N_channel)+.0135; a=1+VA, b=1+.8TfVA+N_post.
Interval discrete-modulation dùng center=2sqrt(.8)mh C, radius=sqrt(2N_post w); chi_BE được numerical maximize trên toàn giao interval với miền covariance vật lý. Eigenvalue homodyne điều kiện là nu3=sqrt[a(a-z²/b)]. Các quy ước detector/C,w/fading đã chốt được giữ nguyên; không mở lại nghiên cứu security.

MI chính tính likelihood pooled: p(y|x)=E_T Normal(y;2sqrt(.8T)x,1+.8*.0186T+.0135); I=Σpx ∫p(y|x)log2[p(y|x)/p(y)]dy. Fading nằm trong mixture, không cộng N_fading lần nữa vào phương sai từngT. Không CSI conditioning hoặc postselection. K=.95I-chi_BE. numeric.py chỉ tăng tốc cùng likelihood qua characteristic-function/Fourier inversion; được đối chiếu trực tiếp với pooled_mi cũ tại cùng node, không thay mô hình. K_surrogate và I_AB_surrogate được giữ riêng trong mọi dòng.

Stages: one-parameter scans nguồn cố định;8cm trước rồi10/12/15/20/25/30/40/55cm; các tier(jitterµrad,sigma_m)=(15.61,1),(12,.75),(10,.5),(7.5,.3),(5,.2),(3,.2),(3,.1),(1.561,.1). Mỗi tier xét10 divergence đã yêu cầu; dừng tăng yêu cầu pointing khi nguồn cố định dương ở một receiver. Các điểm diameter lớn ở StageA là sensitivity độc lập, không được dùng để nhảy qua compact search. StageE xét233 nguồn exact(197MB,36Uniform) trên các context đã chọn; C,w/PMF/energy/hash xác thực, không tạo AP hay nội suy. Chọn context theo moment-quality chỉ là heuristic sàng lọc, không là objectiveSKR hoặc chứng nhận phủ toàn miền. Targeted alternating dùng4 starts, P1 tìmVA trên cùngnu, P2 tìmnu trên cùngVA trong catalog, dừng deltaK<1e-8 hoặc catalog fixed point. Thiếu nguồn cùngVA được đánh dấu MISSING_EXACT_SOURCE_NO_INTERPOLATION.

Screen dùng quadrature128x16; các ứng viên chọn dùng256x32/512x48, tăng1024x64 nếu cần. Dừng khi thay đổiMI giữa hai mức<2e-6 và K lớn hơn hai lần ảnh hưởng quan sát lênK. Đây là quan sát hội tụ, không là error bound nghiêm ngặt. Full-Z33/129, entropy110digits, Fourier half-output-spacing và density-mass checks có receipt. FFT chỉ sửa density âm do roundoff trong budget tích phân1e-12, ghi rõ từng dòng; không sửa transmittance. RegressionA/B khớp sai số cỡ1e-15. Chi numerical không có rigorous global enclosure; giữ giới hạn security trước đó.

## Q1. Tham số gốc nào cản trở SKR dương?

Tín hiệu thu quá yếu so với noise detector untrusted cố định. Baseline N_detector/N_channel=3480.888848; sigma_h=1m lớn hơn dịch góc Ltheta_jt=0.342472633m. Trong sensitivity nguồn cố định, giảm sigma_h giúp tăngK nhiều nhất; riêng giảm divergence hoặc tăngRx không đủ và có thể làm raw bound xấu hơn do fading trong nguồnVA cao.

| Tham số | Giá trị cho K lớn nhất | K | DeltaK so baseline |
| --- | --- | --- | --- |
| divergence | 233 | -0.0586963625888 | 4.9100999655e-10 |
| receiver | 0.08 | -0.0586963625888 | 4.9100999655e-10 |
| angular_jitter | 1.561 | -0.058665373874 | 3.09892058111e-05 |
| position | 0.1 | -0.0584508842118 | 0.000245478867993 |


Không một thay đổi độc lập trong danh sách làm K dương. Các delta cỡ1e-9 của điểm baseline là khác quadrature128x16 so với baseline512x48, không là hiệu quả vật lý.

## Q2. Receiver có giữ8cm được không?

Chưa có điểm dương trong80 context cố định8cm và context được xét233nguồn. Không được suy ra bất khả thi mọi nguồn/mọi beam/PAT. Figure1 giữ8cm, fixedMB; Figure6 hiển thị best sampled ở8–30cm. Không có đườngK=0 trong vùng compact đã thử; không vẽ contour giả hoặc điền node chưa tính.

| Rx(cm) | Divergence | Jitter | σh | VA | νraw | K lớn nhất đã thử ở đúngRx |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 50 | 3 | 0.1 | 2.6666460606 | 0.2 | -0.0576184364254 |
| 10 | 75 | 1.561 | 0.1 | 5.475 | 0.165 | -0.0583275601922 |
| 12 | 25 | 1.561 | 0.1 | 0.60833317999 | 0.25 | -0.057546480345 |
| 15 | 25 | 1.561 | 0.1 | 0.741661515149 | 0.2 | -0.0565988134638 |
| 20 | 25 | 1.561 | 0.1 | 0.741661515149 | 0.2 | -0.053432558953 |
| 25 | 25 | 1.561 | 0.1 | 0.938888879856 | 0.3 | -0.0472740192941 |
| 30 | 25 | 1.561 | 0.1 | 1.11666635998 | 0.25 | -0.0370507692305 |
| 40 | 25.0785813719 | 1.561 | 0.1 | 1.77777775971 | 0.3 | -0.000215838726659 |



## Q3. Nếu giữ8cm thì thay đổi tối thiểu là gì?

Chưa tìm thấy tổ hợp đủ, nên không có maximum admissible divergence, required angular/position threshold hoặc robustness của một thiết kế8cm dương để báo cáo. Ngay cả tiers mạnh nhất trong danh sách vẫn chưa tạo dương ở các điểm đã thử. Dtx99 ở10µrad gần30cm không tự giải quyết thiếu thu quang; beam hẹp tăng nhạy lệch tâm. Không gán một ngưỡng từ thiết kế55/75cm cho8cm.

## Q4. Nếu tăngRx, kích thước nhỏ nhất đã tìm được?

Trong danh sách rời rạc,40cm âm và55cm có dương. Tại40cm, source-catalog best ở25µrad choK=-.000216000397480931; tối ưu divergence cục bộ giữ nguồn cho theta=25.0785813719µrad vẫn K=-.0002158387266592565. Nghiệm tăngRx trên nhánh này: K=0 tạiD=0.400432390522m; K=1e-4 tạiD=0.400632519749m. Chọn điểm làm tròn lênD=0.401m, rồi kiểm tra lại toàn catalog và MI mịn. Cấu hình1 là ứng viên giảm khẩu độ thu trên nhánh này; đòi hỏi PAT tốt, không tối thiểu đồng thời mọi chiều kỹ thuật.

Toàn bộ26 root giữ đúng một nguồn exact và các tham số khác cố định, nằm ở refined_boundary_roots.csv; không phải ngưỡng toàn cục sau tối ưu liên tục. Mỗi trong4 biến của3 ứng viên có sign-change về baseline tại cả2 mục tiêu; thêm2 root của nhánh40cm. Không suy ra root ở các context chưa có bracket. Mốc1e-4 chỉ là engineering comparison target, không là định nghĩa security.

## Q5. Kết hợp divergence/pointing nào cân bằng nhất trong shortlist?

Cấu hình2 dùngRx55cm, full35µrad, jitter3µrad, sigma_h.1m. Nguồn được chọn trong catalog với ràng buộc đồng thời jitter3.6µrad/sigma_h.12m vẫn K>=1e-4, rồi kiểm tra đủ25 tổ hợp±10/20%. Đây là guard robustness trong shortlist, không là nghiệm cost/global tối ưu. Cấu hình1 gần onset và cấu hình3 dùng beam hẹp hơn có thể mất dương khi pointing xấu đi; xem bảng dưới.

| Cấu hình | K nominal | K thấp nhất trong25 perturbations | K fine ở worst case |
| --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 0.000283673880404 | -0.0418114157861 | -0.0418114652469 |
| 2 — Cân bằng, có dự trữ pointing | 0.035149837665 | 0.000937963193141 | 0.000937824261616 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 0.0804568149166 | -0.0412740854135 | -0.0412740896879 |


Pareto dùng năm chiều: giảmRx, tăng divergence (giảmTx), tăng tolerated angular jitter, tăng tolerated sigma_h, tăngK. Chỉ các điểm đã tính; projection2D không giữ đầy đủ thứ tự dominance. Danh sách final_pareto.csv và figure7 không chứng nhận optimal frontier liên tục. Điểm regression75cm/10µrad được giữ như upper comparison, không chọn làm thiết kế mặc định.

Nguồn cân bằng có guard robustness có thể hy sinh nominalK so với nguồn đứng trên nominal Pareto frontier ở cùng phần cứng. Robustness là tiêu chí bổ sung; không gọi nguồn robust là nominal optimum.

## Q6. Kích thướcTx/Rx và yêu cầu vật lý có hợp lý không?

| Cấu hình | w0(m) | wL(m) | w_eff(m) | Ltheta_jt(m) | σh/w_eff | Ltheta_jt/w_eff | Dtx99(cm) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 0.0393467490261 | 0.277902934449 | 0.279349628562 | 0.0342472632678 | 0.357974343889 | 0.122596415983 | 11.9411648851 |
| 2 — Cân bằng, có dự trữ pointing | 0.0281931613477 | 0.38497167127 | 0.386137116002 | 0.0658179306876 | 0.258975363558 | 0.170452225285 | 8.55621357843 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 0.0657840431447 | 0.177207619284 | 0.179154771981 | 0.0658179306876 | 0.558176591637 | 0.367380282198 | 19.9644983497 |


Các kích thướcTx là yêu cầu encircled-power của Gaussian lý tưởng, không là pupil đã thiết kế. Dtx99 chứa99% Gaussian không chặn;99.99% cần đường kínhsqrt2 lầnDtx99. Mô hình primary chưa đưa hard-pupil diffraction, M² thực, throughput, coupling single-mode, mounting, obscuration và wavefront residual vào. Không đồng nhất cắt1% công suất với cùng Gaussian propagation; không xác nhận khẩu độ tối thiểu phần cứng. Điểm gần onset đặc biệt dễ mất margin do loss/coupling chưa mô hình hóa.

Rx40.1/55cm đều thuộc nhómlarge>30cm, cần platformSWaP riêng: khối lượng quang học/gimbal, tải và mômen lên UAV, mount/cách ly rung, băng thông tracking và receiverattitude. Không có sốmass/power/vibration đo được nên không tuyên bố phù hợp UAV thông thường. 8–15cm là compact;15–30cm intermediate chỉ là phân lớp tìm kiếm exploratory, không phải giới hạn chứng nhận. Chưa tìm được khuyến nghị positive đủ căn cứ cho compactUAV.

Cơ chế có cơ sở để hạ residual: coarse gimbal kết hợp beacon sensor và fine steering mirror; GPS dùng acquisition/coarse, không phải measurement trực tiếp của beam-centering residual. [Carrasco-Casado et al., UAV laser terminal](https://arxiv.org/abs/1506.08854) mô tả GPS-aided gimbal, fine mirror và beacon tracking; [NASA CLICK](https://www.nasa.gov/smallspacecraft/what-is-click/) dùng fine steering mirror cho precisionpointing. Đây là dẫn chứng kiến trúc, không chứng minh jitter1.561/3µrad hoặcsigma.1m đạt được ở liên kết này.

theta_jt là residual transmitter pointing mỗi trục; sigma_h phải được hiểu/đo là residual tương đối độc lập sau coarse/beam steering, không cộng lại cùng một chuyển động đã nằm trongtheta_jt. Receiver attitude/AoA1.5mrad được giữ riêng trongP0/FOV, không dùng cải thiệntheta_jt để xóaoutage. Nếu các residual tương quan, quy tắc cộng variance đang dùng cần hiệu chuẩn lại. Giữ turbulence/HV và atmosphere không đổi. Không tối ưu FOV vì chưa có background noise trade-off; không gán gainAO/coupling hoặc giảm noise tùy ý.

## Q7. MB shaping bổ sung bao nhiêu sau cải thiện quang học?

| Cấu hình | So sánh | Family | VA | νraw | K |
| --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | family_energy_optimized_or_historical_fixed | Uniform | 0.5 | 0 | -0.0649497701751 |
| 1 — Ít thay đổi về khẩu độ thu | family_energy_optimized_or_historical_fixed | MB | 1.77777775971 | 0.3 | 0.000284368412279 |
| 1 — Ít thay đổi về khẩu độ thu | family_energy_optimized_or_historical_fixed | Fixed MB | 5.475 | 0.165 | -0.0580244444111 |
| 1 — Ít thay đổi về khẩu độ thu | same_VA | Uniform | 1.77777775971 |  |  |
| 1 — Ít thay đổi về khẩu độ thu | same_VA | MB | 1.77777775971 | 0.3 | 0.000284368412279 |
| 2 — Cân bằng, có dự trữ pointing | family_energy_optimized_or_historical_fixed | Uniform | 0.6 | 0 | -0.0554517236018 |
| 2 — Cân bằng, có dự trữ pointing | family_energy_optimized_or_historical_fixed | MB | 2.6666460606 | 0.2 | 0.0363188277083 |
| 2 — Cân bằng, có dự trữ pointing | family_energy_optimized_or_historical_fixed | Fixed MB | 5.475 | 0.165 | 0.0120395296597 |
| 2 — Cân bằng, có dự trữ pointing | same_VA | Uniform | 2.15 |  |  |
| 2 — Cân bằng, có dự trữ pointing | same_VA | MB | 2.15 | 0.22 | 0.035150983646 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | family_energy_optimized_or_historical_fixed | Uniform | 0.7 | 0 | -0.0480173726852 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | family_energy_optimized_or_historical_fixed | MB | 2.15 | 0.22 | 0.0804572948122 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | family_energy_optimized_or_historical_fixed | Fixed MB | 5.475 | 0.165 | 0.0184151788435 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | same_VA | Uniform | 2.15 |  |  |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | same_VA | MB | 2.15 | 0.22 | 0.0804572948122 |


Family-energy-optimized so sánh chọnVA khác nhau, nên chênh lệch không được gọi toàn bộ là shaping gain. Dòngsame_VA chỉ dùng nguồn exact có cùngVA; thiếu thì flag. FixedMB(.165,5.475) tách riêng để thấy ích lợi sourceadaptation sau cải thiện kênh. Best nominalMB có thể khác nguồn robust-balanced; không gọi guard robustness là maximizernominal. Catalog gốc sau tối ưu nguồn vẫn K=-0.0584489852306; source optimization không tự cứu kênh gốc. Báo cáo chỉ best exact tested, không global/continuous optimum.

| Cấu hình | K fixedMB | K best nominalMB | Gain do chọn cảVA vàν |
| --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | -0.0580244444111 | 0.000284368412279 | 0.0583088128233 |
| 2 — Cân bằng, có dự trữ pointing | 0.0120395296597 | 0.0363188277083 | 0.0242792980486 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 0.0184151788435 | 0.0804572948122 | 0.0620421159687 |



Để tách riêng hiệu ứng shaping ở cùng năng lượng, dùng VA chung gần nhất có đủ hai nguồn exact trong catalog (không thayVA của ba khuyến nghị):

| Cấu hình | VA chung | K Uniform | K MB | DeltaK cùngVA | νMB |
| --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 2 | -0.112731638427 | -0.000300681158426 | 0.112430957268 | 0.24 |
| 2 — Cân bằng, có dự trữ pointing | 2.05 | -0.0849498256205 | 0.0344895002594 | 0.11943932588 | 0.22 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 2.05 | -0.0989526129146 | 0.0800749279246 | 0.179027540839 | 0.22 |


File same_energy_shaping_comparison.csv giữ hash riêng của hai nguồn. MB ở đây là best exact tested trên cácν có sẵn tại đúngVA đó.

## Q8. Đề xuất đưa gì vào manuscript?

Đưa cấu hình2 làm **kịch bản sensitivity có margin** của mô hình bounded đã khai báo; chỉ gọi là khuyến nghị nghiên cứu, chờ đo/certify optics/PAT/platform và các điều kiện security còn thiếu. Cấu hình1 dùng minh họa onset/giảmRx, không gọi robust. Cấu hình3 minh họa đánh đổi transmitter lớn hơn và nhạy pointing để tăng nominalK. Không thay manuscriptbaseline hoặc tuyên bố UAV phổ thông mang được55cm; giữ baselineâm và kết quảcompactâm trong bài. BenchmarkA75cm/10µrad vàB55cm/25µrad của nghiên cứu trước chỉ là regression/comparison, không tự trở thành thiết kế mặc định.

| Cấu hình | Rx tăng(lần) | Collimation tăng(lần) | Angular stability tăng(lần) | Horizontal stability tăng(lần) | K | Trade-off |
| --- | --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 5.0125 | 9.29079665811 | 10 | 10 | 0.000283673880404 | Local onset; not pointing-robust |
| 2 — Cân bằng, có dự trữ pointing | 6.875 | 6.65714285714 | 5.20333333333 | 10 | 0.035149837665 | Survives sampled joint20percent degradation |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 6.875 | 15.5333333333 | 5.20333333333 | 10 | 0.0804568149166 | Higher collection with larger Tx; pointing-sensitive |



### Phân rã đầy đủ ba cấu hình

| Cấu hình | m1 | Tf | I_AB | betaI_AB | chi_BE | K |
| --- | --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 0.430444752659 | 0.419767462556 | 0.328598187262 | 0.312168277899 | 0.311884604018 | 0.000283673880404 |
| 2 — Cân bằng, có dự trữ pointing | 0.464976880854 | 0.458387780724 | 0.4095515496 | 0.38907397212 | 0.353924134455 | 0.035149837665 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 0.735501596622 | 0.718719200156 | 0.560581251366 | 0.532552188797 | 0.452095373881 | 0.0804568149166 |


| Cấu hình | N_fading | N_channel | N_detector | N_post | AoA outage |
| --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 0.0189818488781 | 0.00800627239945 | 0.016875 | 0.035090497022 | 0.000169856676561 |
| 2 — Cân bằng, có dự trữ pointing | 0.0141665652783 | 0.00864856998388 | 0.016875 | 0.0317521082098 | 0.000169856676561 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 0.0360821524028 | 0.0136803296972 | 0.016875 | 0.05330998568 | 0.000169856676561 |



### Hồ sơ, phạm vi và tái kiểm tra

TableA: table_A_baseline_sensitivity.csv (đủmoment/noise/I/chi/K/delta); TableB: table_B_positive_candidates.csv; TableC: table_C_minimum_improvement.csv. transmitter_apertures.csv và physical_channel_receipt.csv tách yêu cầu hình học/received fractions khỏi hardware chưa đo. final_selection.json, final_source_comparisons.csv, alternating_*.csv, final_robustness.csv, refined_boundary_roots.csv, all_evaluations.csv và evaluations.jsonl giữ đúng các node/evaluator/sourcehash. selection.json giữ shortlist tự động ban đầu; **final_selection.json mới là ba cấu hình cuối sau tinh chỉnh40cm và robustness**.

Bảy hình nằm trong figures/, mỗi hình vectorPDF và350dpiPNG. Dữ liệu figure3/4 nằm ở figure_sensitivity_data.csv; heatmap dùng node cố định, hatch là chưa thử, outline là node dương, không nội suy tạo tối ưu. Các điểm trên đường chỉ nối để đọc xu hướng. SOURCE/physical searches không phủ toànCartesian; thiếu node không chứng minh âm.

checks.json/figure_validation.json/final_convergence.json và final_receipt.json chứa kết quả kiểm tra, hashproducer/input/artifact và preservation manifest. Chạy verify.py để xác minh chỉ từ artifact đã lưu; không chạy lại tìm kiếm. Numeric search nằm ở search.py/refine.py, isolatednumeric.py; không sửa historicalmodel/source/security/config/cache/spec. GitHEAD và dirty work trước task được chụp trongstartup_manifest.json.

Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS, UNVALIDATED_SECURITY_MODEL; discrepancy historicalfrozenhash đã ghi trước và ObjectiveC USER_STOPPED vẫn giữ. Không có training/finaltest/heldout/newAP, productionbaseline selection hoặc thresholdcertification. Không thử finitekey/experimentalhardware; các kết quả dương vẫn là numericaldiagnostic của kênh surrogate chưa đo.
