# Receiver UAV nhỏ và detector cải thiện

Thư mục thí nghiệm đề ngày 2026-10-22; tiếp tục và đóng gói ngày 2026-10-23 (Asia/Bangkok).

Đã hoàn tất nghiên cứu tham số với detector **UNTRUSTED**, homodyne 1D và các công thức cũ giữ nguyên. Ứng viên dương đã qua kiểm tra số nhỏ nhất được tìm thấy có Dr=28.1 cm; receiver nhỏ nhất trong menu chính có ứng viên dương là 0.3 m. Đây là kết quả nhỏ nhất đã thử/cục bộ, chưa chứng nhận receiver nhỏ nhất toàn miền. Chưa xác thực phần cứng hoặc chứng minh bảo mật cho các SKR này.

| Vai trò | Receiver (cm) | Jitter (µrad) | ηdet | εdet (SNU) | K (bit/use) | Độ bền |
| --- | --- | --- | --- | --- | --- | --- |
| A — Ưu tiên receiver nhỏ | 28.1 | 1.561 | 0.95 | 0.005 | 2.1077487382e-05 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |
| B — Tham chiếu cho mục tiêu cân bằng chưa đạt | 30 | 1.561 | 0.95 | 0.005 | 0.00542861294451 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |
| C — Tham chiếu hiệu năng | 30 | 1.561 | 0.95 | 0.005 | 0.00542861294451 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |


Chưa tìm được thiết kế B đáp ứng đồng thời PAT ưu tiên (jitter ≥ 3 µrad) và độ bền 10% trong các điểm đã thử. B dưới đây chỉ là tham chiếu dương có SKR joint+10% tốt nhất trong shortlist, nhưng vẫn âm khi perturb đồng thời; không phải thiết kế cân bằng đạt yêu cầu.

Ba vai trò tương ứng 2 cấu hình vật lý khác nhau. B/C trùng thông số là cùng một cấu hình, không phải hai thiết kế độc lập.

A: chưa đạt K ≥ 10⁻⁴ ở nominal; B: đạt K ≥ 10⁻⁴ ở nominal; C: đạt K ≥ 10⁻⁴ ở nominal. Tiêu chí này chỉ là margin kỹ thuật.

## Bảng tham số A/B/C

| Tham số | Đơn vị | A | B | C |
| --- | --- | --- | --- | --- |
| D_r | m | 0.281 | 0.3 | 0.3 |
| divergence_urad | µrad, full angle | 35 | 35 | 35 |
| jitter_urad | µrad, SD | 1.561 | 1.561 | 1.561 |
| sigma_h_m | m, SD | 0.1 | 0.1 | 0.1 |
| zenith_deg | degree | 0 | 0 | 0 |
| L_km | km | 19 | 19 | 19 |
| eta_det | dimensionless | 0.95 | 0.95 | 0.95 |
| epsilon_det | SNU | 0.005 | 0.005 | 0.005 |
| VA | SNU | 1.3833230303 | 1.62499953997 | 1.62499953997 |
| nu_raw | raw | 0.2 | 0.25 | 0.25 |
| m1 | dimensionless | 0.204314557649 | 0.22893092877 | 0.22893092877 |
| eta_f | dimensionless | 0.199345635282 | 0.223596483261 | 0.223596483261 |
| epsilon_f | SNU | 0.0799467386859 | 0.0813507636742 | 0.0813507636742 |
| I_AB | bit/use | 0.165628224904 | 0.21078485465 | 0.21078485465 |
| beta_I_AB | bit/use | 0.157346813658 | 0.200245611917 | 0.200245611917 |
| chi_BE | bit/use | 0.157325736171 | 0.194816998973 | 0.194816998973 |
| K_raw | bit/use | 2.1077487382e-05 | 0.00542861294451 | 0.00542861294451 |


C,w và ensemble hash chính xác nằm trong selected_designs.csv và selection.json. Bảng trên ghi trực tiếp I_AB, βI_AB, χ_BE và excess noise hiệu dụng.

## Mô hình, regression và phạm vi

Giữ M256, beta.95, epsilon_ch.0186SNU, HAP20/UAV1km, tau_zen.92, AO/phaseOFF, đúng PMF/normalization và exact C,w. Không thêm AO/PAT distribution, không đổi loss/noise convention, MI hoặc full-Z Holevo. T_f=E[sqrtT]^2; N_fading=(E[T]-T_f)VA; N_channel=.0186E[T]; N_detector=epsilon_det/eta_det; N_post=eta_det(N_fading+N_channel)+epsilon_det. Vacuum1 xuất hiện một lần. Actual pooled fading MI là chính; MI hiệu dụng được lưu riêng. Không clip K âm; outage atom được giữ.

Parameter adapter gọi propagation và power-conserving collector cũ. Dr chỉ thay vào cùng circular-aperture CDF; code bytecode của hàm MI giống hệt hàm đã lưu, chỉ dependency quadrature nhận khẩu độ thay đổi. Các bytes mô hình lịch sử được hash-bind và giữ nguyên. Bốn fresh regression8cm baseline,8cm gần đây,40.1cm và55cm đã khớp trước search; xem regression.json. Baseline hiện tại K=-0.058696363079805018; historical corrected-trial K=-.05872431468 thuộc optical law khác nên không đánh tráo hai baseline.

Full divergence233µrad ở manuscript khác223µrad tại theta_div_rad của config; cả hai là divergence, không phải jitter15.61µrad. Không sửa production tau_zen=null hoặc phase mapping chưa giải quyết. Quét geometry0/15/30 bằng đúng phương trình; không đổi độ cao hoặc dựng profile khí quyển mới.

Chỉ dùng detector noise.0135/.005SNU, eta.8/.85/.9/.95. .005 là giả định của biến epsilon_det hiện tại, không bằng chứng thực nghiệm hoặc phép đồng nhất với electronic v_el của Villaseñor. Không dùng các kết quả cũ ởnoise.0005 hoặc sigma_h.05m làm nghiệm cho nhiệm vụ này.

## Stage A — Receiver và detector, nguồn cố định

table_A_receiver_detector.csv giữ đủ I_AB,betaI,Holevo,K cho sáu Dr và tám detector scenarios ở optics gốc, optics35urad/jitter3urad/centering.1m tại30deg và nadir. Các delta sau giữ đúng nguồn/optics/geometry trong từng nhóm:

| Optical context | Thay đổi | K gốc | K mới | DeltaK |
| --- | --- | --- | --- | --- |
| original_optics | aperture8to20cm | -0.0586963625888 | -0.0599632530437 | -0.00126689045494 |
| original_optics | efficiency80to95 | -0.0586963625888 | -0.0587423927612 | -4.6030172368e-05 |
| original_optics | noise0135to005 | -0.0586963625888 | -0.025527988987 | 0.0331683736018 |
| original_optics | combined | -0.0586963625888 | -0.0274282695497 | 0.0312680930391 |
| improved_fixed_optics | aperture8to20cm | -0.062648603361 | -0.0753786175526 | -0.0127300141916 |
| improved_fixed_optics | efficiency80to95 | -0.062648603361 | -0.0633910930607 | -0.000742489699676 |
| improved_fixed_optics | noise0135to005 | -0.062648603361 | -0.030678562452 | 0.031970040909 |
| improved_fixed_optics | combined | -0.062648603361 | -0.0495715610678 | 0.0130770422932 |
| improved_nadir | aperture8to20cm | -0.0658674560419 | -0.0874522492221 | -0.0215847931802 |
| improved_nadir | efficiency80to95 | -0.0658674560419 | -0.0671754329481 | -0.00130797690628 |
| improved_nadir | noise0135to005 | -0.0658674560419 | -0.0345043094702 | 0.0313631465717 |
| improved_nadir | combined | -0.0658674560419 | -0.0648028287422 | 0.00106462729968 |


Ở original_optics, thay đổi đơn lẻ có deltaK lớn nhất là noise0135to005. Ở improved_fixed_optics, thay đổi đơn lẻ có deltaK lớn nhất là noise0135to005. Ở improved_nadir, thay đổi đơn lẻ có deltaK lớn nhất là noise0135to005.

Không quy gain sau tối ưu nguồn thành hiệu ứng detector/aperture riêng. Tăng efficiency không mặc định cải thiện K đơn điệu trong mọi kênh untrusted. TableA có đủ thông số để kiểm chứng điều này.

## Stage B–D — Optics, PAT, nguồn và ngưỡng

Screen có sáu PAT tiers, năm beam và ba góc cho bốn detector corners, không full Cartesian jitter×centering×source. Eta.85/.9 có trong StageA và detector sensitivity của thiết kế cuối. Ưu tiên nhánhjitter>=3urad;1.561urad là demanding reference. Residual beam-centering SD là sai số quang tại beam/receiver, không đồng nhất với độ chính xác GPS hoặc vị trí thân UAV.

Tối ưu nguồn dùng 233 payload exact (197 MB / 36 Uniform), bốn starts P1/P2 trong catalog; không nội suy C,w/SKR hoặc AP mới. Tất cả coordinate probes thực đều được lưu. Điểm đã cache ở Stage A được đưa lại đúng vào đủ 90 physical contexts mỗi nhánh; source_coverage.json xác minh metadata stage không làm thiếu nhánh đã tính. optimization_phase1.json giữ snapshot trước bổ sung coverage. Đây vẫn là best exact tested, không global/continuous optimum.

| Dr(cm) | ηdet | εdet | Nhánh | Div | Jitter | CenterSD | ζ | VA | ν | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0571676152314 |
| 8 | 0.8 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0569672401938 |
| 8 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0569254615022 |
| 8 | 0.95 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0566874238483 |
| 8 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.35833331978 | 0.3 | -0.0241408693679 |
| 8 | 0.8 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0239253492871 |
| 8 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.35833331978 | 0.3 | -0.0239350067791 |
| 8 | 0.95 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0236784908824 |
| 12 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0555261593747 |
| 12 | 0.8 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.8 | 0.21 | -0.0550751728588 |
| 12 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0549658513872 |
| 12 | 0.95 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.8 | 0.21 | -0.0544276662355 |
| 12 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0227336453541 |
| 12 | 0.8 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0222456946366 |
| 12 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0222481760659 |
| 12 | 0.95 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0216690004811 |
| 15 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0538170654728 |
| 15 | 0.8 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.8 | 0.21 | -0.0531109126609 |
| 15 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0529183797933 |
| 15 | 0.95 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.9 | 0.23 | -0.0520726686149 |
| 15 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.021231297014 |
| 15 | 0.8 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0204837714281 |
| 15 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0204391378087 |
| 15 | 0.95 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0195518069184 |
| 20 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0499789470964 |
| 20 | 0.8 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.925 | 0.24 | -0.048702808189 |
| 20 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.8 | 0.21 | -0.0482967030486 |
| 20 | 0.95 | 0.0135 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.925 | 0.24 | -0.046760718345 |
| 20 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0177703336575 |
| 20 | 0.8 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.8 | 0.21 | -0.0164587072599 |
| 20 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0162474623327 |
| 20 | 0.95 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.8 | 0.21 | -0.014675172478 |
| 25 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.8 | 0.21 | -0.0447285765988 |
| 25 | 0.8 | 0.0135 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.35833331978 | 0.3 | -0.0411595806043 |
| 25 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.9 | 0.23 | -0.0419140974895 |
| 25 | 0.95 | 0.0135 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.35833331978 | 0.3 | -0.0373521863172 |
| 25 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0129598730314 |
| 25 | 0.8 | 0.005 | including_1p561 | 50 | 1.561 | 0.1 | 0 | 1.925 | 0.24 | -0.0108887648249 |
| 25 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.8 | 0.21 | -0.0103650852783 |
| 25 | 0.95 | 0.005 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.3833230303 | 0.2 | -0.00716727498298 |
| 30 | 0.8 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.925 | 0.24 | -0.0378751546209 |
| 30 | 0.8 | 0.0135 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0305805622775 |
| 30 | 0.95 | 0.0135 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.975 | 0.24 | -0.0335227137507 |
| 30 | 0.95 | 0.0135 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.0241194014 |
| 30 | 0.8 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.9 | 0.23 | -0.00651699743268 |
| 30 | 0.8 | 0.005 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | -0.000686768337225 |
| 30 | 0.95 | 0.005 | jitter_at_least3 | 50 | 3 | 0.1 | 0 | 1.9 | 0.23 | -0.00241341474912 |
| 30 | 0.95 | 0.005 | including_1p561 | 35 | 1.561 | 0.1 | 0 | 1.62499953997 | 0.25 | 0.00542861294451 |



Các ngưỡng dưới đây dùng **cùng một nguồn exact**, divergence 35 µrad, zenith 0° và centering 0,1 m. Chỉ Dr và detector/pointing scenario ghi ở bảng thay đổi. Root có bracket đầu tiên trên menu tăng Dr, target 0 hoặc 1e-4. Số chữ số của root là độ chính xác số, không phải tolerance chế tạo. Không gọi đây là global minimum hoặc certified threshold:

| ηdet | εdet | Jitter | TargetK | Dcrit(cm) | RoundedD(cm) | K tại roundedD |
| --- | --- | --- | --- | --- | --- | --- |
| 0.8 | 0.0135 | 3 | 0 | 43.1008399644 | 43.2 | 0.000395047729827 |
| 0.8 | 0.0135 | 3 | 0.0001 | 43.1259609608 | 43.2 | 0.000395047729827 |
| 0.95 | 0.0135 | 3 | 0 | 39.9642729408 | 40 | 0.000160522708326 |
| 0.95 | 0.0135 | 3 | 0.0001 | 39.986518891 | 40 | 0.000160522708326 |
| 0.8 | 0.005 | 3 | 0 | 34.6576006151 | 34.7 | 0.00011847167717 |
| 0.8 | 0.005 | 3 | 0.0001 | 34.6933733732 | 34.7 | 0.00011847167717 |
| 0.95 | 0.005 | 3 | 0 | 32.4806216344 | 32.5 | 5.9580673467e-05 |
| 0.95 | 0.005 | 3 | 0.0001 | 32.5130907682 | 32.6 | 0.00036862030229 |
| 0.8 | 0.0135 | 1.561 | 0 | 39.5560613844 | 39.6 | 0.000169307323832 |
| 0.8 | 0.0135 | 1.561 | 0.0001 | 39.5820018557 | 39.6 | 0.000169307323832 |
| 0.95 | 0.0135 | 1.561 | 0 | 36.4546536518 | 36.5 | 0.000196502192259 |
| 0.95 | 0.0135 | 1.561 | 0.0001 | 36.4777260701 | 36.5 | 0.000196502192259 |
| 0.8 | 0.005 | 1.561 | 0 | 30.4229318768 | 30.5 | 0.000198347365921 |
| 0.8 | 0.005 | 1.561 | 0.0001 | 30.4618161768 | 30.5 | 0.000198347365921 |
| 0.95 | 0.005 | 1.561 | 0 | 28.2846228964 | 28.3 | 4.31550185187e-05 |
| 0.95 | 0.005 | 1.561 | 0.0001 | 28.3201694823 | 28.4 | 0.000325370910645 |


critical_receiver_status.csv giữ NO_SIGN_CHANGE nếu không bracket; không ngoại suy ngoài 45 cm. detector_aperture_savings.csv so sánh deltaDr và clear-area hình học cùng nguồn/optics/PAT. Area giảm không phải mass/power/flight-time saving. Các điểm roundedD được tính trực tiếp, không lấy SKR nội suy. PAT_relaxation.csv và least_demanding_PAT.csv kiểm tra riêng jitter × centering cho các nguồn/optics đã shortlist; đây là tập không bị trội trong menu tại nguồn cố định, không phải ngưỡng PAT tối thiểu toàn cục. Threshold curves ở trên 30 cm chỉ là so sánh fixed-source; fallback optimization used=False, các fallback diameter đã tối ưu=[]. 55 cm giữ làm benchmark regression, không default thiết kế UAV mới.

## Stage E — Bằng chứng khối lượng và công suất

| Nhóm | Ví dụ / nguồn | Khối lượng(kg) | Công suất điện(W) | Giới hạn |
| --- | --- | --- | --- | --- |
| receiving_optics | [Celestron C6 OTA 150mm](https://www.celestron.com/products/used-c6-optical-tube-assembly-cg-5-dovetail) | 4.54 | UNKNOWN | Astronomical optical tube; excludes PAT/QKD electronics; central obstruction/coatings are not the modeled ideal clear aperture. Not a lower mass bound or recommended1550nm collector. |
| receiving_optics | [Celestron C8 OTA 200mm class](https://www.celestron.com/products/c8-optical-tube-assembly-cge-dovetail) | 5.67 | UNKNOWN | Manufacturer specification table lists12.5lb/5.67kg. Reference existing OTA, not a custom lightweight UAV design or mass scaling law. |
| receiving_optics | [Celestron C9.25 OTA235mm](https://www.celestron.com/products/c9-25-optical-tube-assembly-cge-dovetail) | 9.07 | UNKNOWN | Existing astronomical OTA only; no conversion of this mass to a25/30cm UAV assembly. |
| pointing_stabilization | [Conrad et al.2025 drone/vehicle DV-QKD PAT](https://arxiv.org/html/2505.17587v1) | UNKNOWN | UNKNOWN | Supplement Table6 closed-loop SD107urad differs from sensor resolution3.33urad in Table5; neither proves3urad residual at19-22km. DV656nm prototype, not homodyne1550nm CV-QKD. |
| balanced_detector | [FEMTO HBPR FC balanced receiver](https://www.femto.de/en/silicon-and-ingaas-photoreceivers-photodetectors/dc-up-to-500-mhz-balanced-balanced-photoreceiver-photodetectors-hbpr/) | 0.35 | 3.15 | Manufacturer FC model mass350g; FST410g. Does not establish model eta.95 or epsilon_det.005SNU. Excludes DC conversion and external front-end optics. |
| local_oscillator | [RIO ORION narrow-linewidth OEM laser](https://rio-lasers.com/Product-Briefs/Rio_1550_nm_Orion_Product_Brief_170126.pdf) | UNKNOWN | UNKNOWN | Only optical output10-20mW is grounded here; not electrical draw. TEC/driver/phase-lock total unknown. No new LO or phase-noise model is introduced. |
| ADC_DAQ | [Analog Devices AD9648 dual ADC](https://www.analog.com/en/products/ad9648.html) | UNKNOWN | 0.212 | Chip-level figure only, not full DAQ power. Clock, input drivers, FPGA/data transport/regulators excluded. ADC sample rate is not an authenticated QKD repetition rate. |
| digital_processing | [NVIDIA Jetson Orin Nano Super developer platform](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/) | UNKNOWN | UNKNOWN | Configurable power budget, not measured consumption or demonstrated real-time CV-QKD reconciliation/DSP. Do not add another control processor automatically if functions are shared. |
| control_sync_communications | [Raspberry Pi4 reference supply](https://www.raspberrypi.com/products/type-c-power-supply/?variant=raspberry-pi-psu-uk-w) | UNKNOWN | UNKNOWN | Supply rating is not operating draw. Complete clock/synchronization/radio/control and conversion power unknown. Integrate/shared compute once, not twice. |
| integrated_terminal_comparison | [Mynaric HAWK airborne classical terminal](https://mynaric.com/products/hawk/) | 13 | 110 | Whole classical bidirectional terminal; its mass/power includes integrated functions. Not a CV-QKD receiver, not scaled to modeled aperture, never summed with discrete example components. |



Các reference là linh kiện/prototype rời, không phải BOM đã ghép cho A/B/C. Telescope thiên văn có obstruction/coatings và chưa được xác thực cho clear-aperture1550nm trong mô hình; khối lượng của chúng không phải lower bound cho thiết kế custom. Prototype DV-QKD drone ở656nm không chứng minh detector homodyne1550nm hoặc PAT3urad tại19–22km. Resolution3.33urad không phải closed-loop SD107urad; hai số có chức năng khác nhau.

[Hao et al.](https://arxiv.org/pdf/2101.07482) báo cáo detector efficiency95% trong một receiver phòng thí nghiệm ở1530nm, gồm photodiodeQE99% và visibility98%. Điều này hỗ trợ tính khả dĩ của high-efficiency detection nói chung, nhưng không xác thực bộη=.95/εdet=.005SNU/1550nm/bandwidth/LO/power của UAV ở đây. Không nhập protocol hoặc công thức phase-conjugate receiver của bài đó vào model. Các ví dụ calibration99.5% ở1064nm không được dùng làm bằng chứng1550nm.

FEMTO typical rail power=15(.120+.090)=3.15W, không gồm converter/optics. AD9648 two-channel chip figure=2(.106)=.212W, không gồm DAQ board, clock, FPGA hoặc transfer. RIO10–20mW là optical output, không phải điện tiêu thụ. Jetson7–25W là configurable budget; RaspberryPi15W là supply capacity, không phải operating draw. Không cộng các ví dụ khác nhau thành một hệ thống tưởng tượng. HAWK13kg/110W là whole classical terminal; không cộng thêm thành phần của nó lần nữa.

| Thiết kế | Receiver | Detector | PAT | Gánh nặng payload | Power evidence | K | Robustness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A — Ưu tiên receiver nhỏ | 0.281 | eta0.95; noise0.005 | 1.561urad angularSD; 0.1m optical centeringSD | Custom1550nm optics plus PAT/LO/DAQ/control integration required; no authenticated UAV BOM | Grounded component examples only; not an assembled power budget | 2.1077487382e-05 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |
| B — Tham chiếu cho mục tiêu cân bằng chưa đạt | 0.3 | eta0.95; noise0.005 | 1.561urad angularSD; 0.1m optical centeringSD | Custom1550nm optics plus PAT/LO/DAQ/control integration required; no authenticated UAV BOM | Grounded component examples only; not an assembled power budget | 0.00542861294451 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |
| C — Tham chiếu hiệu năng | 0.3 | eta0.95; noise0.005 | 1.561urad angularSD; 0.1m optical centeringSD | Custom1550nm optics plus PAT/LO/DAQ/control integration required; no authenticated UAV BOM | Grounded component examples only; not an assembled power budget | 0.00542861294451 | NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN |



P_UAV,QKD=P_optics+P_PAT+P_detector+P_LO+P_ADC+P_processing+P_control chỉ được tính khi có BOM đồng bộ và power tại cùng operating point. Hiện cả ba thiết kế cònUNKNOWN tổngmass/power; bộ xử lý/control dùng chung phải chỉ tính một lần. Receiver nhỏ hơn hoặc eta_det cao hơn không tự suy ra ít W hay nhiều W hơn. HAP optics/PAT có thể nhận thêm gánh nặng, nhưng beacon/receiver stabilization/coupling/phase/ADC/DSP trên UAV chưa được chứng minh loại bỏ được.

R_key=f_rep max(0,K), R_useful=p_avail R_key và E_bit=P_UAV,QKD/R_useful được giữ dạng công thức. Không tính số bit/s,J/bit hoặc bits/sortie vì thiếu f_rep, bandwidth/noise calibration, external availability, battery/duty/flight duration của đúng platform. ADC125MSPS không phải f_rep đã xác thực. K đã gồm AoA outage; một p_avail tương lai phải là availability ngoài mô hình, không nhân lại cùng outage. Không mượn thời gian bay từ prototype khác.

## Stage F — Robustness

| Thiết kế | K nominal | Jitter+10% | Center+10% | Joint+10% | Joint+20% | Noise.0135 | Noise.005 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A — Ưu tiên receiver nhỏ | 2.1077487382e-05 | -0.000697801514208 | -0.00808826164584 | -0.00879273390751 | -0.0181303078278 | -0.0298946849729 | 2.1077487382e-05 |
| B — Tham chiếu cho mục tiêu cân bằng chưa đạt | 0.00542861294451 | 0.00453755342443 | -0.004625013944 | -0.00549857192381 | -0.0170795104495 | -0.0241194014 | 0.00542861294451 |
| C — Tham chiếu hiệu năng | 0.00542861294451 | 0.00453755342443 | -0.004625013944 | -0.00549857192381 | -0.0170795104495 | -0.0241194014 | 0.00542861294451 |


Giữ nguồn và mọi biến không được perturb. Các mức10/20% thay residual SD, không đổi distribution. K>=1e-4 là engineering margin, không security proof. “POSITIVE_AT_JOINT20” chỉ có nghĩa số mẫu joint20 vượt1e-4 cùng nguồn; không chứng minh mọi thời tiết/phase/pointing spectrum. Barely-positive không được gọi robust. B có thể giữ nguồn chịu perturbation tốt hơn thay vì nguồn max nominal K; source_selection ghi rõ lựa chọn.

## Q1. Receiver15–20cm có dương với detector cải thiện không?

Chưa tìm thấy điểm dương trong miền/các nguồn đã thử. Best tested trong hai lớp15/20cm có K=-0.014675172478, Dr=20cm, eta=0.95, noise=0.005,div=50urad,jitter=1.561urad,centering=0.1m. Không là no-key theorem ngoài catalog/domain.

## Q2. Receiver25–30cm có robust positive với PAT không quá cực đoan không?

Có 0 shortlisted positive rows dùngjitter>=3urad trong lớp25–30cm; trong đó 0 rows cònK>=1e-4 khi cả hai residual tăng20%. Xem tableB/robustness. “Không quá cực đoan” là ưu tiên tương đối trong menu; chưa có chứng minh hardware3urad/.1m cho HAP–UAV.

## Q3. Giảmnoise.0135→.005 giúp bao nhiêu?

Giảm variance 2,7 lần. Giữ nguyên nguồn và phần cứng khác tại A/B/C: A: deltaK=0.0299157629249 bit/use; B: deltaK=0.029548014955 bit/use; C: deltaK=0.029548014955 bit/use. isolated_parameter_impacts.csv cho deltaK cùng nguồn/optics; detector_sensitivity.csv thay đúng noise tại từng thiết kế cuối. Không thay loss vacuum, trust hoặc SNU. Tại A/B/C, noise-switch K và gap được ghi trong bảng robustness, không suy từ kết quả lịch sử khác.

## Q4. Tăngeta.8→.95 có hiệu quả hơn tăngaperture không?

Kết hợp η=.95 và εdet=.005, so với η=.8/εdet=.0135 tại cùng nguồn/optics: jitter 3 µrad: Dcrit 43.1008 → 32.4806 cm, giảm 10.6202 cm; jitter 1.561 µrad: Dcrit 39.5561 → 28.2846 cm, giảm 11.2714 cm. Đây là tiết kiệm khẩu độ hình học tại hai scenario cố định, không phải mass/power saving. Đối chiếu hiệu ứng efficiency riêng với tăng aperture bằng deltaK ở Stage A và deltaDcrit cùng nguồn trong detector_aperture_savings.csv. Efficiency và receiver diameter tác động khác nhau; không áp một thứ hạng chung cho mọi điểm. Không suy chi phí điện hoặc mass từ eta_det; thiếu device-specific evidence cho cả hai.

## Q5. Receiver nhỏ nhất đã tìm được là bao nhiêu?

Sau shortlist đầu, refine_minimum.py kiểm tra thêm tối đa ba bước source/aperture cục bộ: Dr ban đầu 28.3 cm → 28.1 cm. Nguồn được giữ exact trong từng root; bảng ngưỡng detector ở trên vẫn dùng nguồn chung riêng. selection_phase1/ giữ nguyên các bảng trước bước này; source_refined_minimum.json ghi bracket, nguồn và residual.

Ứng viên đã qua refinement nhỏ nhất có Dr=28.1 cm; menu chính nhỏ nhất có ứng viên dương=0.3 m. Phân biệt với root K=0 cục bộ và điểm làm tròn để tính trực tiếp. A ở bảng đầu có nguồn và K trực tiếp; không dùng machine-epsilon-positive root probe làm thiết kế thực. A chưa đạt K≥1e-4 ở nominal.

## Q6. PAT có thể hỗ trợ trên UAV hay phải chuyển sang HAP?

Đặt thêm transmitter aperture/steering/tracking tạiHAP phù hợp hướng kiến trúc, nhưng hiệu năng còn là requirement chưa được chứng minh. Current prototype/reference data cho thấy sensor resolution, closed-loop jitter, residual centering và full19–22km link khác nhau. Chưa thể loại bỏ UAV stabilization, beacon, optical-mode/LO alignment hoặc control power mà vẫn khẳng định đạt model parameters.

## Q7. Thiết kế cân bằng tốt nhất là gì?

Chưa tìm được thiết kế B đáp ứng đồng thời PAT ưu tiên (jitter ≥ 3 µrad) và độ bền 10% trong các điểm đã thử. B dưới đây chỉ là tham chiếu dương có SKR joint+10% tốt nhất trong shortlist, nhưng vẫn âm khi perturb đồng thời; không phải thiết kế cân bằng đạt yêu cầu. Ba vai trò tương ứng 2 cấu hình vật lý khác nhau. B/C trùng thông số là cùng một cấu hình, không phải hai thiết kế độc lập. Chưa có cơ sở chọn một thiết kế tối ưu năng lượng vì thiếu BOM và công suất hệ thống. A ưu tiên nhỏ hơn nhưng có margin hẹp; C là tham chiếu hiệu năng cao hơn trong menu đã thử, với receiver/PAT/detector demands ghi rõ. B/C vẫn âm khi centering tăng 10% hoặc cả hai residual tăng 10%, nên không gọi là robust.

## Q8. Nếu dưới30cm không có nghiệm, điểm đầu tiên trên30cm là gì?

Fallback optimization used=False; diameters=[]. Nếuprimary đã có dương, không gọi một điểm lớn hơn là “minimum cần thiết”. Bảng threshold vẫn so sánh bốn detector scenarios fixed-source, còn40.1/55cm là matching regression/benchmark. Mọi positive chỉ là candidate model-based SKR, không certified secure-key generation hoặc hardware deployment recommendation.

## Validation, artifact và kết luận

46 CURRENTLY_VERIFIED_PASS scoped checks, 28093 logged nodes (26747 mới/1346 authenticated reuse). Baseline/regression, exact C,w/ensemble/source hash, mixed law/outage normalization, passive T support, covariance/symplectic physicality, noise once, same homodyne measurement, full-Z33/129, entropy110digits, width32/64, direct mixture/Fourier MI, half output spacing và observed convergence có receipt. Source/threshold/global/hardware/security limitations giữ nguyên.

Không sửa frozen/model/security implementation, source cache, config hoặc kết quả lịch sử. Startup bảo vệ 6548 files, ngoại trừ relevant task ledgers. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy và ObjectiveC USER_STOPPED. Không AP/training/test/heldout/publication hoặc production baseline/threshold approval.

TableA: table_A_receiver_detector.csv; TableB: table_B_positive_candidates.csv; TableC: table_C_UAV_engineering.csv; TableD: table_D_critical_receiver_thresholds.csv. Các bảng supplement ghi source comparisons, PAT Pareto, detector savings, hardware evidence và throughput/energy UNKNOWN. Tất cả figures là plot độc lập với vectorPDF và PNG350dpi; nối node chỉ giúp đọc dữ liệu, không nội suy source hay tạo optimum curve.

Các ứng viên cho biết miền dương đã thử và phần mục tiêu nhẹ/cân bằng còn chưa đạt. Xác nhận battery-powered UAV thực vẫn thiếu BOM/operating power, measured optics/PAT/detector/SNU/phase/bandwidth và security protocol evidence; không chuyển raw positive thành chứng nhận triển khai.
