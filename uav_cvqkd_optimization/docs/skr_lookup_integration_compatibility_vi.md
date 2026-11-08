# Tương thích lookup SKR với cấu hình Phase 4

## Kết luận có thể sử dụng ngay

Lookup hiện có **không đại diện cho thí nghiệm reference Section IV mới** vì
bốn tham số vật lý khác nhau. Việc này độc lập với quyết định tác giả rằng
công thức Z và w trong code hiện tại đúng. Phase4 giữ nguyên quyết định đó,
không kiểm chứng lại, viết lại hoặc dùng nghi vấn về hai công thức để chặn
triển khai. Những interface còn lại đã được triển khai và kiểm thử.

Không sửa CSV/NPZ gốc, không tái sinh lookup, không đổi
`INSUFFICIENT_EVIDENCE`, `paper_admissible` hoặc bất kỳ trạng thái figure nào.

## Hai tập input phải phân biệt

Nguồn mới:
[hap_uav_mb_reference.yaml](../configs/channel/hap_uav_mb_reference.yaml), từ
bản thảo nhóm tác giả *Performance Analysis of Probabilistically Shaped
CV-QKD in Free-space HAP-to-UAV Systems*, Section IV, PDF page3. Không gọi
bản thảo là một bài đã xuất bản/peer-reviewed.

Lookup cũ: sibling
`paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/skr_map.csv` và NPZ,
cùng `execution_physical_protocol.json`, `source_pool.csv`, producer/receipts.
Đây là2.601 node trên51×51, x/y0..2000m, bits/use, không phải50×50 cloud cells.
Giá trị MB là max trên179 candidate MB trong catalog212 nguồn gồm33 Uniform;
không chứng nhận optimum liên tục trên toàn miền nu/VA.

| Đại lượng | Section IV reference mới | Receiver30 lookup cũ | Kết quả |
|---|---:|---:|---|
| HAP altitude | 20000m | 20000m | Khớp |
| UAV altitude | 1000m | 1000m | Khớp |
| Aperture diameter | .08m | .30m | Khác |
| Beam full divergence | 233µrad | 35µrad | Khác |
| Transmitter jitter mỗi trục | 15.61µrad | 1.561µrad | Khác |
| UAV position SD mỗi trục | 1m | .10m | Khác |
| Wavelength | 1550nm | 1550nm | Khớp |
| tau_zen | .92 | .92 | Khớp |
| Ground Cn² / RMS wind | 1e-14 m^(-2/3) /21m/s | Cùng giá trị | Khớp trong subset |
| FOV half-angle / angular SD | 6.25 /1.5mrad | Cùng giá trị | Khớp trong subset |
| beta | .95 | .95 | Khớp reconciliation efficiency |
| Channel/detector excess noise | Chưa xác định trong reference mới | .0186 /.005 SNU trong protocol cũ | Không tự nhập sang reference mới |
| HAP horizontal coordinates | Chưa chọn cho mission | Lookup dùng projection(1000,1000)m | Không tự chuyển geometry mission |

`phase4_audit.compare_lookup_reference` chỉ báo
`physical_subset_matches`; `full_configuration_compatibility=NOT_ESTABLISHED`.
Beta và normalization được so sánh riêng. Một subset vật lý khớp không được
biến thành full compatibility nếu noise, geometry, conventions hoặc protocol
chưa khớp. JSON thực thi:
[reference_audit.json](phase4_validation/reference_audit_verified/reference_audit.json).

## Effective-channel và modulation boundary

Giữ Source A Eq.(17):

\[
\eta_f=\langle\sqrt\eta\rangle^2,\quad
\eta_f\xi_f=(\langle\eta\rangle-\langle\sqrt\eta\rangle^2)V_{\rm mod}
+\langle\eta\xi\rangle.
\]

Không thay eta_f bằng E[eta] như mean-transmittance reference của IEEE2025.
`FadingMoments.from_existing_v43` chỉ nhận kết quả moment có sẵn từ helper
Eq.(18)–(20) theo contract `m1,mh,M0`, cùng xi_ch/xi_det được khai báo rõ.
Nó chuyển thành E[eta*xi]=xi_ch*m1+xi_det*M0, giữ retained mass, không normalize.
Không sao chép closed-form engine, không nhập noise tổng/vacuum của các model
historical khác vào như excess noise. Interface sẽ báo lỗi nếu thiếu đúng keys
hoặc input scalar không đúng domain; đây không phải xét lại Z/w.

Convention module hiện có là `VA=Vmod=2*nbar`, theo mapping tác giả đã ghi
trong protocol trước đó. Bản in có `Vmod=nbar/2`; hai mô tả được lưu riêng,
không âm thầm đổi source amplitudes, variance hoặc scale. Request/backend phải
khớp source VA, beta và scalar effective input. Không tính lại nbar từ toán tử/
matrix trong Phase4 để mở lại chuyện core. Payload C,w và các toán tử/matrix
được chuyển nguyên cho callback evaluator hiện có, không bị adapter sửa.

Scalar checks dùng domain của power transmissivity[0,1], không phải amplitude:
m1<=mh, mh²<=m1, và khi có retained mass M0 thì mh<=M0, mh²<=M0*m1. Chỉ cho
phép32 machine eps cho arithmetic residual. Nếu m1-mh² âm do roundoff thì
variance được đặt0 với cờ `variance_roundoff_adjustment`; **eta_f vẫn là mh²**,
không thay bằng m1. Không biến việc qua các kiểm tra scalar thành source/
security certificate.

## Cách tái sử dụng hợp lệ trong tương lai

1. Có thể giữ nguyên lookup cũ cho đúng receiver30 diagnostic context và scope
   của nó, với raw signed/potential columns riêng và các nhãn bằng chứng cũ.
2. Không dùng các rate cũ như rate của .08m/233µrad reference mới. Nếu cần
   table mới, phải có input/noise/geometry và quyền cho công việc đó; Phase4
   không chạy hay viết đè table cũ.
3. Nếu chỉ dùng old scalar table trong trajectory, cần adapter schema lossless
   trước generic `SKRLookup`, có manifest và kiểm đơn vị. Không đổi metadata
   để lờ physical mismatch; schema adaptation không giải quyết model mismatch.
4. Unit test chỉ replay một response đã lưu từ **chính context receiver30 của
   nó** qua boundary để kiểm forwarding và valid-signal accounting. Không có
   SKR mới được tính từ core hoặc table mới được giả lập.

## Cloud/trajectory interface liên quan

Graph solver hiện giữ rate tĩnh r[j] và availability z[k,j], phù hợp fixed
clear-sky rate + binary cloud erasure. Mode attenuation liên tục có thể tạo
rate r[k,j]. Interface link-slot mới hỗ trợ channel/SKR request theo post-loss
moments được cung cấp rõ, nhưng không tự chuyển model graph sang time-varying
rates. Cần author decision và integration riêng nếu muốn tối ưu đầy đủ mode đó.
Không nhân SKR scalar với factor attenuation hoặc dùng lại fixed r[j] như thể
đã đánh giá lại kênh; không double-count erasure cho cùng cơ chế cloud.
