# Khảo sát SKR với detector untrusted — 2026-10-22

Đã thực thi regression, 140 cấu hình quang học ở nguồn cố định với ba mô hình kênh, catalog exact 233 nguồn, các khảo sát detector/pointing, tìm nghiệm có bracket và năm hình raw có dấu. **Có giá trị dương trong mô hình kênh thụ động mới; chưa có kết quả nào được xác nhận là sinh khóa an toàn trên hệ thống HAP–UAV thực.** Không đổi detector thành trusted, không clip K, không tạo hay nội suy C,w.

## Q1. Vì sao kết quả gốc âm?

Regression dùng nguyên hàm của trial trước tái lập I_AB=0.0007587634870959417, chi_BE=0.0594451399927187034, K=-0.0587243146799775588. Bảng A dưới đây là kết quả trên đúng kênh gốc, không trộn với mô hình mới. Detector excess trước loss là0.016875, lớn gấp3436.14 lần phần channel và chiếm phần lớn N_pre. Fading/channel=22.84. Với eta_f≈2.435e-4, nhiễu detector output0.0135 là quá lớn so với tín hiệu thu.

Hiệu chỉnh loss/noise là nhất quán ở cấp covariance: t=eta_det*mhalf², N_post=eta_det[(m1-mhalf²)VA+epsilon_ch*m1]+epsilon_det, b=1+tVA+N_post. Vacuum1 xuất hiện một lần; không thêm1-eta hay1-eta_det vào excess; epsilon_det là output quadrature SNU, không tự đồng nhất với v_el. Không thấy double count detector trong trial này.

Trong mô hình Gaussian hiệu dụng, N_post>=2t là điều kiện entanglement-breaking; tại liên kết gốc detector0.0135 đã vượt2t nhiều lần ngay trước khi thêm fading. Đây chỉ là chẩn đoán của surrogate Gaussian, không là chứng minh no-key của mọi kênh fading ngoài miền khảo sát.

## Q2. Có dương với detector gốc không?

**Có trong mô hình Gaussian random-width thụ động đã khai báo**, khi tăng thu quang và giảm pointing jitter. Ở phần cứng/quang học gốc, tối ưu catalog chỉ cho K=-0.0584489853; detector sweep kể cả epsilon_det=0 vẫn không có giá trị dương trong catalog đã thử. Không suy ra bất khả thi ngoài catalog/model.

Chỉ quét aperture/divergence/geometry với jitter gốc ở fixed MB cũng không cho giá trị dương trong mô hình thụ động. Tăng aperture không bù được việc beam hẹp thường lệch ra ngoài khẩu độ. Phải xét pointing cùng collection, không chọn một điểm âm gần zero rồi gọi đó là cải thiện liên kết.

## Q3. Ứng viên tốt nhất tìm được

Ứng viên lớn nhất trong các cấu hình đã thử dùng D_r=0.75m, divergence full10µrad, sigma_position=0.1m, angular jitter1.561µrad, VA=8, nu_raw=0.125. Giữ eta_det=.8, epsilon_det=.0135, epsilon_ch=.0186, beta=.95, homodyne1D, AO OFF, phase OFF như giả thiết gốc. Tại zenith0deg/L19km K_surrogate≈0.424068; giữ zenith30deg/L21.9393102292km K_surrogate≈0.402568. Toàn bộ thông số và phân rã ở bảng dưới.

Đây là BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY. VA=8 là biên catalog MB; không có chứng nhận tối ưu liên tục/toàn cục. Không tạo AP mới vì catalog đủ để trả lời câu hỏi positivity trong diagnostic; mở rộng năng lượng không giúp xác thực mô hình vật lý/security.

## Q4. Ngưỡng cải thiện nào?

Tại zenith30deg, cùng giảm hai jitter xuống0.1, aperture nhỏ nhất trong grid có ứng viên dương là0.55m;0.40m ở10µrad vẫn âm sau scan catalog. Divergence lớn nhất trong grid có dương tạiD=.75m là50µrad;100µrad vẫn âm sau scan catalog. Các root refinement bên dưới giữ một nguồn exact cố định, không phải ngưỡng tối ưu toàn miền. Ngưỡng detector của link sáng có thể nằm ngoài danh sách0.8..1 hoặc0..0.0135; không được áp các ngưỡng đó cho link gốc. Khoảng cách38km vẫn dương ở nguồn/pointing đã chọn; đây là L lớn nhất đã thử (zenith<=60deg), không là maximum-range certificate.

## Q5. MB giúp bao nhiêu?

Ở link cải thiện30deg, fixed MB(.165,5.475) cho0.378577; catalog-best MB(.125,8) cho0.402568, tăng khoảng0.023991 bit/use,6.34%. Cải thiện optical/pointing đã làm fixed MB dương; source optimization bổ sung sau đó. Catalog-best Uniform cho0.0440529 tạiVA2.05. So sánh Uniform/MB này dùng cùng link/detector/receiver, nhưng mỗi family chọn năng lượng tốt nhất trong catalog: không quy toàn bộ chênh lệch thành shaping gain ở cùng năng lượng.

Alternating P1/P2 đã chạy trên các tọa độ exact có sẵn với bốn starts và deltaK1e-8, dừng ở catalog fixed point. Đây không phải continuous convergence hay global optimum; toàn bộ catalog scan, nguồn thắng và coordinate log được lưu.

Đối chứng cùng năng lượng cũng có sẵn: tạiVA=8, cùng link30deg cải thiện,
Uniform cho0.0212590103957273 còn MB(nu=.125) cho0.402568122114429.
Chênh lệch này là của functional MI–Holevo với bound moment discrete;
không tự suy ra coded throughput hoặc practical shaping gain tương ứng.

## Q6. Khuyến nghị sửa ít hơn

Ứng viên ít đòi hỏi transmitter aperture hơn là D_r=.55m, divergence25µrad, cùng jitter0.1m/1.561µrad, zenith30deg, detector gốc. Catalog chọn VA3.5,nu_raw=.2, cho K_surrogate≈0.101322. Gaussian transmitter chứa99% công suất cần đường kính khoảng0.1198m, so với0.2995m cho10µrad. Đây là yêu cầu hình học lý tưởng, không là xác nhận phần cứng, độ phân kỳ thực hoặc năng lực ổn định UAV/HAP.

Ưu tiên đo/hiệu chuẩn pointing và coupling rồi xác minh antenna/aperture/beam budget. Không đề xuất mua phần cứng chỉ dựa trên surrogate này. Không gán gain AO tùy ý: không có AO/coupling model được kiểm chứng cho trial này; chỉ có sensitivity giảm toàn profile Cn² theo các hệ số khai báo. Phase noise vẫn OFF theo phạm vi lịch sử, không được tuyên bố đã mô hình hóa phần cứng phase tracking thực.

## Q7. Kết quả nào security-valid?

**Chưa có kết quả nào được chứng nhận security-valid/operational.** Detector composition, homodyne conditioning, positivity/normalization, source identity và uncertainty/spectrum được kiểm tra. Công thức DBL dùng c1=sqrt(eta_det)mhalf C, c2=sqrt(eta_det)mhalf VA/2, nB=(b-1)/2; radius=2sqrt[w(nB-c2²/nbar)]=sqrt(2N_post*w). Tính numerical maximum trên toàn giao khoảng correlation với physical uncertainty cap, không giả định endpoint worst-case. 33/65/129 grids và entropy80/110 được đối chiếu, nhưng chưa có rigorous global enclosure.

Tài liệu lý thuyết gốc: [Denys–Brown–Leverrier 2021, Sections3–5](https://arxiv.org/html/2103.13945). Conditional eigenvalue homodyne sqrt[a(a-z²/b)] được dùng cùng MI1D, không ghép heterodyne. Đây là lý do giữ bound discrete-modulation, không thay bằng công thức Gaussian modulation.

MI Gaussian hiệu dụng của pooled fading không tự là lower bound cho MI discrete-input thực. Vì vậy đã tính thêm actual pooled homodyne likelihood cho các ứng viên chọn, không conditioning theo CSI và không postselection. Các kết quả này vẫn dùng bound moment/frozen-source trong một kênh iid mô phỏng; không thay thế parameter estimation, finite-key, authentication, hardware calibration hay proof cho fading tương quan. Mọi output có security_valid=false và rate-per-transmitted-use, gồm cả outage.

## Mô hình bounded mới và lý do không chỉ normalize PDF cũ

PDF lognormal lịch sử có tail>1. Reference55cm/10µrad trước dùng aperture-averaged v khác với raw-Rytov manuscript; không trộn hai closure. Trong closure reference đã lưu, missing mass≈3.6536e-5. Trong optical manuscript có trường hợp tail lớn hơn nhiều.

Hai mô hình so sánh được tính riêng: conditional-active trên(0,1] giữ P0, và đưa toàn tail invalid về erasure/vacuum. Cả hai tính lại mọi moment, không ghép raw moments với support bị cắt. Conditional-active là lựa chọn distribution mới, không phải cứ lọc sample rồi miễn phí postselect key rate.

Hơn nữa equivalent-beam pointing có thể sai rất lớn khi aperture lớn hơn beam: tạiD=.75m/10µrad/30deg/jitter gốc, conditioning của approximation có thể cho K dương, trong khi tích phân thu Gaussian tròn dự đoán công suất thu rất nhỏ. Các hàng đó chỉ là comparison, không được dùng để kết luận khả thi.

Mô hình primary mới: mỗi realization là Gaussian beam **tổng công suất bằng1**, bán kính w=w_eff exp(-S/2), S~N(-v/2,v), v lấy raw Rytov manuscript. On-axis intensity fluctuation là lognormal, còn aperture collection tính đúng CDF noncentral-chi-square H=F_chi2(df2,nc=4r²/w²)(4a²/w²). Jitter r Rayleigh với sigma_s²=sigma_position²+(L theta_jitter)². T=eta_atm H nằm trong[0,eta_atm], không cần clip hoặc normalize; AoA atom riêng. Mean H theo Rayleigh có tích phân độc lập1-exp[-2a²/(w²+4sigma_s²)]. Đây là passive Gaussian random-width **surrogate mới**, không phải atmospheric closure được đo hay re-freeze của production. G_d/HV được tái tính theo từng angle; distribution mới không giữ nguyên moment lịch sử.

Outage detector full-mixture vẫn phát sinh epsilon_det ở vacuum input; active-only tắt noise khi outage là một receiver hypothesis khác. Cả hai được so sánh, không chia K cho Pactive. Không coi postselection tự động an toàn.

## Validation và provenance

Regression exact so với saved prior trial đã PASS. validate.py kiểm tra19370 saved rows cùng source C,w và homodyne/untrusted assumptions;51 named checks gồm aperture convolution độc lập, MI-GH64/128, width-GH32/64, full-Z33/129, entropy80/110, detector-zero actual covariance và DBL moment identity. Boundary candidates được kiểm tra bổ sung. Actual-fading MI refinement radial128/256/512, width16/32/48 có tolerance diagnostic2e-5 bit/use; surrogate MI tolerance2e-13; không gọi đó là rigorous security enclosure. Dấu dương của các ứng viên lớn không phụ thuộc sai số refinement này.

Lịch sử thực thi được giữ: lần đầu guard phát hiện rounding q0 d/d ở45deg, sửa bằng đồng nhất thức q0 normalization và tăng160digits, không clip probability; partial files ởattempt_1_precision_failure. Lần scan kế tiếp hoàn thành các numerical stage nhưng summary gặp numpy-int64 JSON serialization; đã sửa serializer và tiếp tục từ CSV, không rerun scientific stages. Việc chọn điểm âm gần zero ưu tiên link tối; bright-link extension và boundary refinement được ghi riêng, không xóa các kết quả âm ban đầu.

Không tạo C,w, không interpolation/large source grid, không trusted-detector substitution, không sửa production/cache/frozen/manuscript. Nguồn có support256; VA=2nbar. SHA/input manifests và final receipt bảo vệ cả thay đổi chưa commit của trial trước. Giữ NOT_READY_FOR_PUBLICATION_SCALE_RUNS, UNVALIDATED_SECURITY_MODEL, frozen-hash historical conflict và ObjectiveC USER_STOPPED; không training/test/held-out/publication, commit/push.

Scripts tự chứa trong thư mục này: model.py, run.py, extend_bright.py, refine_boundary.py, validate.py, finish.py. Producer không ghi đè kết quả đã hoàn tất. Không chạy lại trial đã sealed. Bảng C hoàn chỉnh ởtable_C_detector_sensitivity_final.csv; bảng B sorted ởtable_B_optical_feasibility_final.csv. Năm hìnhvectorPDF/350dpiPNG ởfigures/; không smoothing hay nội suy C,w/SKR.

Kiểm tra toàn bộ node dương:5932 node exact khác nhau được đối chiếu GH128.
208 node không đạt tolerance2e-13 khi so GH64/GH128 (sai khác lớn nhất
1.40242e-9); đã giữ bản coarse check FAILED và chỉ refine208 node đó bằng
GH256/GH512. Kết quả ởpositive_MI_refined_nodes.csv vàpositive_MI_verification.json.
Các bảng A/B/C cuối cùng và các ứng viên khuyến nghị không nằm trong208 node
coarse thất bại; không thay số headline. Refinement dùng GH256 và khi cần
GH512, sai khác adjacent lớn nhất sau refinement2.776e-14, không cần GH1024.
Các bảng search thô vẫn giữ GH64 đã
khai báo, và numerical refinement có file riêng. Không nới tolerance để gọi
GH64 PASS. Scriptverify.py chỉ đọc hashes/artifacts, không chạy evaluator;
verify_positive_nodes.py vàrefine_positive_nodes.py là các producer kiểm tra số.

## Bảng A — Chẩn đoán đúng trial lịch sử

| Component | Value | Interpretation |
| --- | --- | --- |
| eta_f | 0.00024354548877266 | Saved historical channel effective transmission before detector |
| fading_excess_output_pre_detector | 0.000112174254196698 | Fading output excess before detector |
| channel_excess_output_pre_detector | 4.91103122871642e-06 | Channel output excess before detector |
| detector_excess_output_pre_detector | 0.016875 | Untrusted output detector excess referred before eta_det |
| eta_f_epsilon_f | 0.0169920852854254 | Total pre-detector excess |
| I_AB | 0.000758763487095942 | Consistent homodyne 1D MI |
| chi_BE | 0.0594451399927187 | Historical diagnostic Holevo |
| K_raw | -0.0587243146799776 | Signed numerical regression only |
| detector_over_channel | 3436.14186391777 | Before-detector noise ratio |
| fading_over_channel | 22.8412830162387 | Before-detector noise ratio |


## Các ứng viên chọn — cùng detector untrusted gốc

| Candidate | D_r (m) | Full divergence (µrad) | L (km) | VA | nu_raw | eta_f | epsilon_f | I_AB | beta I_AB | chi_BE | K_raw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| largest_tested | 0.75 | 10 | 19 | 8 | 0.125 | 0.907727924050081 | 0.0449741026389937 | 1.36402690592205 | 1.29582556062594 | 0.871757486426418 | 0.424068074199525 |
| same_geometry_30deg | 0.75 | 10 | 21.9393102292058 | 8 | 0.125 | 0.891741972964785 | 0.0470568101871645 | 1.35262104950747 | 1.2849899970321 | 0.882421874917668 | 0.402568122114429 |
| smaller_transmitter | 0.55 | 25 | 21.9393102292058 | 3.5 | 0.2 | 0.628553470567713 | 0.087990815749062 | 0.712562907866378 | 0.676934762473059 | 0.575612857399555 | 0.101321905073504 |


## Phân rã nhiễu trước detector

| Candidate | N_fading | N_channel | N_detector | N_pre | N_post |
| --- | --- | --- | --- | --- | --- |
| largest_tested | 0.0070491202326366 | 0.0169001285918724 | 0.016875 | 0.040824248824509 | 0.0326593990596072 |
| same_geometry_30deg | 0.00848141277588255 | 0.0166061199818489 | 0.016875 | 0.0419625327577315 | 0.0335700262061852 |
| smaller_transmitter | 0.0265994808236492 | 0.011832451793508 | 0.016875 | 0.0553069326171572 | 0.0442455460937257 |


## Ngưỡng fixed exact source, model-dependent

| Quantity | Root | Bracket | Configuration/source scope |
| --- | --- | --- | --- |
| epsilon_det | 0.139214372558516 | (0.0, 0.2) | D=.75m/10µrad/0deg or stated pointing root; fixed source |
| eta_det | 0.186994679282274 | (0.05, 1.0) | D=.75m/10µrad/0deg or stated pointing root; fixed source |
| pointing_factor | 0.147953446182774 | (0.1, 1.0) | D=.75m/10µrad/0deg or stated pointing root; fixed source |
| D_r | 0.450385089626777 | (0.4, 0.55) | 30deg, both jitter factors=.1; fixed exact source |
| theta_div_urad | 75.6134189315023 | (50, 100) | 30deg, both jitter factors=.1; fixed exact source |


## Source comparison, cùng optical/detector/receiver

| Configuration | Source group | VA | nu_raw | I_AB | chi_BE | K_raw |
| --- | --- | --- | --- | --- | --- | --- |
| highest_collection | catalog_best_Uniform | 0.02 | 0 | 6.68990715422517e-05 | 0.0645900729524349 | -0.0645265188344698 |
| highest_collection | catalog_best_MB | 0.025 | 0.3 | 8.36059296036832e-05 | 0.06515180676795 | -0.0650723811348265 |
| highest_collection | fixed_MB | 5.475 | 0.165 | 0.0148448557966751 | 0.562617342950072 | -0.54851472994323 |
| pointing_0deg | catalog_best_Uniform | 3 | 0 | 0.803071869062777 | 0.711649122480412 | 0.0512691531292259 |
| pointing_0deg | catalog_best_MB | 8 | 0.125 | 1.36402690592205 | 0.871757486426418 | 0.424068074199525 |
| pointing_0deg | fixed_MB | 5.475 | 0.165 | 1.13999583395403 | 0.686495909228627 | 0.396500133027706 |
| pointing_30deg | catalog_best_Uniform | 2.05 | 0 | 0.629780236331887 | 0.554238349205514 | 0.0440528753097787 |
| pointing_30deg | catalog_best_MB | 8 | 0.125 | 1.35262104950747 | 0.882421874917668 | 0.402568122114429 |
| pointing_30deg | fixed_MB | 5.475 | 0.165 | 1.12953285935608 | 0.69447903828657 | 0.378577178101707 |


## Actual pooled fading MI — highest quadrature order

| Candidate | Actual I_AB | chi_BE | Raw functional with actual MI |
| --- | --- | --- | --- |
| original_fixed | 0.000753762353882732 | 0.0594124373159937 | -0.0586963630798051 |
| recommended_0deg | 1.36421489355668 | 0.871757486426418 | 0.424246662452429 |
| recommended_30deg | 1.3528182970295 | 0.882421874917668 | 0.402755507260361 |
| uniform_30deg | 0.629836831658757 | 0.554238349205514 | 0.0441066408703055 |
| practical | 0.712800243329673 | 0.575612857399555 | 0.101547373763634 |


## Figures

- [fig_aperture PDF](figures/fig_aperture.pdf), [PNG](figures/fig_aperture.png).
- [fig_divergence PDF](figures/fig_divergence.pdf), [PNG](figures/fig_divergence.png).
- [fig_detector_noise PDF](figures/fig_detector_noise.pdf), [PNG](figures/fig_detector_noise.png).
- [fig_detector_efficiency PDF](figures/fig_detector_efficiency.pdf), [PNG](figures/fig_detector_efficiency.png).
- [fig_distance PDF](figures/fig_distance.pdf), [PNG](figures/fig_distance.png).
