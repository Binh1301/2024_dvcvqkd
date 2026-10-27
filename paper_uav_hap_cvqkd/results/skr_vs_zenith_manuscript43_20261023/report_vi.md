# SKR theo góc zenith — manuscript43, receiver30

Đã quét đủ **61 góc0°–60°,bước1°**, lưu183 dòng cho ba scheme. Hình PNG350dpi và vectorPDF dùng đúng title/labels/legend yêu cầu,trục log và line+marker. Không có file ảnh tham chiếu trong đính kèm hiện tại; styling theo mô tả đã cung cấp.

## Kết quả

| Scheme | Số điểm dương | Max raw SKR (bits/use) | Góc max | Khoảng dương trên grid1° |
| --- | --- | --- | --- | --- |
| Optimized Uniform 256-QAM | 0 | -0.0307471464633 | 60° | Không có |
| Fixed MB-shaped 256-QAM | 1 | 1.25954966034e-05 | 5° | 5° |
| Optimized MB-shaped 256-QAM | 11 | 0.000728137251484 | 5° | 5–15° |


Scheme có peak raw cao nhất trong khảo sát: **Optimized MB-shaped 256-QAM**. Đây là so sánh trong catalog exact đã có,không là chứng minh optimum liên tục hoặc toàn cục. Góc maximum chỉ xác định trên grid1°. Khoảng dương chỉ gồm các góc đạt kiểm tra số học và K>0,không ngoại suy qua khoảng loại.

SKR của Optimized MB giảm theo góc trên khoảng dương. Optimized MB tốt nhất tại cả56 góc có PDF đạt gate. Fixed MB chỉ có một điểm dương nên hình biểu diễn bằng marker riêng; Uniform giữ legend theo yêu cầu nhưng không vẽ các giá trị âm. Cực đại tại5° chỉ là maximum trong các điểm đủ điều kiện đánh giá; chưa thể so sánh rate với0°–4° bị BLOCKED.

| Scheme | VA tại peak | nu_raw tại peak | Source hash |
| --- | --- | --- | --- |
| Optimized Uniform 256-QAM | 0.06 | 0 | 9d90d825de1266050f27136524206ae9048a70390ed683cdeffac9fa4750ee5a |
| Fixed MB-shaped 256-QAM | 1.62499953997 | 0.25 | 01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754 |
| Optimized MB-shaped 256-QAM | 1.35833331978 | 0.3 | b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214 |


Tổng 12 điểm được vẽ. Các góc bị loại do PDF normalization: **[0, 1, 2, 3, 4]**. Candidate-source failures: 0; selected numerical-check failures: 0. Raw SKR âm vẫn giữ nguyên trongCSV; không zero clipping. valid_point và plot_point nghĩa là đủ điều kiện xuất hiện trên trục log. numerically_valid riêng cho biết điểm âm có tính hợp lệ số học hay không. NaN dùng để ngắt đường tại điểm bị loại,không nối xuyên các khoảng đó.

## Tham số và evaluator

| Đại lượng | Giá trị | Nguồn |
| --- | --- | --- |
| HAP/UAV | 20/1km | receiver30_configuration_verification_20261023/protocol.json |
| Dr / wavelength | .30m /1550nm | receiver30 và actual optical factory |
| Full divergence / jitter | 35µrad /1.561µrad | receiver30 overrides |
| Position SD / boresight | .1m per axis /0m | receiver30; Rayleigh pointing |
| tau_zen / atmosphere | .92 /tau_zen^sec(zenith) | preserved actual channel code |
| HV wind / ground coefficient | 21m/s /1e-14m^(-2/3) | preserved HV primitives |
| AoA half-FOV / angular SD | 6.25mrad /1.5mrad | preserved P0 formula |
| beta /xi_ch /xi_det | .95 /.0186 /.005SNU | task.txt và protocol.json |
| Detection / reconciliation | real1D homodyne /reverse | Gaussian effective MI |
| Fixed MB | nu_raw=.25,VA=1.6249995399703647 | current receiver30 exact source |
| Optimized Uniform | best trong36 authenticated Uniform VA points | source_catalog.csv |
| Optimized MB | best trong197 authenticated MB(nu_raw,VA) points | source_catalog.csv |
| Source units | VA=2nbar,X=2Re(alpha) | giữ nguyên source/cache convention |
| AO /phase | OFF /OFF | receiver30 historical assumptions |

Không dùng eta_det trong bất kỳ curve nào. Không dùng random-width surrogate hay historical pooled MI. channel_at_angle và optical factory tái tính L,wL,w_eff,Gd,rawRytov,sigma_s,A0,w_eq,atmospheric transmittance cho từng góc; hai HV integrals được gọi lại theo cùng geometry. AtomP0 được bảo toàn.

Với m1=E[eta],mh=E[sqrt(eta)],Tf=mh²:

    E[eta*xi] = .0186*m1 + .005*M0
    N = (m1-Tf)*VA + E[eta*xi]
    xi_f = N/Tf
    sigma_N² = 1+N
    T_Holevo = Tf
    a = 1+VA; b = 1+Tf*VA+N
    Z± = 2*sqrt(Tf)*C ± sqrt(2*N*w)
    nu3_homodyne = sqrt(a*(a-Z²/b))

Cùng T,N và exact source ở MI/bound/covariance/Holevo. Source catalog được xác thực hash và payload trước sweep. Không nội suy C,w hoặc SKR; không newAP và không ghi cache mới. Optimization là exhaustive argmax rawK trong tập exact đã khai báo. Scheme legend giữ nguyên yêu cầu; từ “Optimized” ở đây nghĩa best exact-tested trong catalog. Giá trị nằm trên biên catalog không phải chứng minh optimum theo VA/nu liên tục.

## Loại điểm và kiểm tra

Mass tolerance1e-10 được giữ từ audit trước,không điều chỉnh theo dấu SKR. Góc0 tái lập deficit1.056995513649377e-10; PDF lognormal-product bị thiếu mass do retained support[0,1]. Không renormalize,clipping,chuyển tail sang atom hoặc thay law. Tại góc failed mass,không chạy source optimization/MI/Holevo; rate để trống/BLOCKED,không phải0. Optimized VA/nu để trống khi chưa thể chọn nguồn; Fixed MB vẫn giữ pair đã chỉ định.

Từng angle checkpoint trong angles/ lưu optical coefficients,M0,m1,mh,closed/direct quadrature,upper tail,candidate ranks/failures và selected checks. Mọi candidate được kiểm tra covariance/symplectic/entropy/capacity; selected sources có GH64/128,adaptive MI,256/16,X/P,scaling,16conditional density integrals,full-Z33/129,entropy80/110 và independent quantum matrix checks.

PNG/PDF được render từ đúng CSV đã lưu. No negative/invalid point trên log-axis. source_catalog.csv,protocol.json,startup_manifest.json,execution_history.json,sweep_receipt.json,figure_receipt.json và final_receipt.json giữ producer/input/output hashes. verify.py chỉ đọc saved artifacts; không import evaluator hoặc chạy lại optimization.

Không khẳng định secure default,finite-key/composable security,hardware validation hoặc global optimum. Numeric full-Z max không là rigorous interval enclosure. Gaussian effective MI là moment-matched approximation,không phải exact conditional likelihood của fading. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy và ObjectiveC USER_STOPPED. Hình “publication-friendly” nói về trình bày,không phải lifecycle approval.

Không sửa production code,frozen model,old results hoặc exact caches; không training/test/heldout/publication evaluation,production baseline/threshold approval hay commit/push. Old ledger hashes là snapshot lịch sử; numerical artifacts trước vẫn được bảo vệ bằng hash.
