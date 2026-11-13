"""Write the Vietnamese report from saved attenuation results, without simulation."""
from pathlib import Path
import argparse
import csv
import json
import math


def report(out):
    meta=json.loads((out/'metadata.json').read_text(encoding='utf-8'))
    cfg=json.loads((out/'configuration.json').read_text(encoding='utf-8'))
    validation=json.loads((out/'validation.json').read_text(encoding='utf-8'))
    receipt=json.loads((out/'design_receipt.json').read_text(encoding='utf-8'))
    scenarios=meta['scenarios'];ref=next(s for s in scenarios if s['name']==cfg['primary_scenario'])
    gamma=meta['gamma_fixed']
    def read(name):
        with (out/name).open(encoding='utf-8') as stream:return list(csv.DictReader(stream))
    space,temporal,wind=read('spatial_correlation.csv'),read('temporal_correlation.csv'),read('wind_lag_correlation.csv')
    def corr(rows,field,**select):
        return next(float(r['pearson_r']) for r in rows if r['field']==field and all(str(r[k])==str(v) for k,v in select.items()))
    parameters='\n'.join(f"| {s['name']} | {s['l0_g_m3']:g} | {s['droplet_cm3']:g} | {s['thickness_km']:g} |" for s in scenarios)
    results='\n'.join(f"| {s['name']} | {s['CLWC']['positive_mean']:.7g} | {s['CLWC']['maximum']:.7g} | {s['attenuation_db']['mean']:.7g} | {s['attenuation_db']['maximum']:.7g} | {s['transmittance']['minimum']:.7g} |" for s in scenarios)
    correlations='\n'.join(f"| {field} | {corr(space,field,axis='x',lag_cells=1):.7f} | {corr(space,field,axis='y',lag_cells=1):.7f} | {corr(temporal,field,lag_slots=1):.7f} | {corr(temporal,field,lag_slots=8):.7f} | {corr(temporal,field,lag_slots=400):.7f} |" for field in ['G','L','A','T'])
    windrows='\n'.join(f"| {field} | "+' | '.join(f"{corr(wind,field,hx_m=h):.7f}" for h in [-80,-40,0,40,80])+' |' for field in ['G','L','A','T'])
    quantiles='\n'.join(f"| {name} | {s['mean']:.8g} | {s['std']:.8g} | {s['q0.5']:.8g} | {s['q0.95']:.8g} | {s['q0.99']:.8g} | {s['maximum']:.8g} |" for name,s in [('G',meta['Gaussian']),('L (g/m3)',ref['CLWC']),('omega (dB/km)',ref['specific_db_km']),('A (dB)',ref['attenuation_db']),('T',ref['transmittance'])])
    fraction=1-ref['CLWC']['zero_fraction']
    independent_gaussian_positive_prob=.5*math.erfc(gamma/math.sqrt(2))
    doc=rf'''# Báo cáo mô hình suy hao mây 2D liên tục theo thời gian

Ngày: 2026-11-12. Phạm vi: **ILLUSTRATIVE_UNCALIBRATED**;
kết quả số **{validation['status']}**, chưa kiểm chứng vật lý khí tượng.
Đây là mô-đun độc lập, không phải thay đổi mô hình kênh/QKD đã đóng băng.

## 1. Dữ liệu sử dụng và phạm vi thực hiện

Đọc trực tiếp `results/ibrahim_stationary_cloud_20261111/cloud_fields.npz`,
khóa `X[k,y,x]`, float64, kích thước 1000 x 50 x 50. Không phát sinh Gaussian,
không gọi RNG; không dùng trường exponential-GRF thay thế trường Ibrahim Stationary.
Hash dữ liệu nguồn trước/sau: `{meta['source_sha256']}`.
Toàn bộ {validation['protected_files']} tệp cũ được đối chiếu hash; dữ liệu,
producer và hình của cả ba gói mây cũ giữ nguyên.

| Tham số nguồn | Giá trị |
|---|---:|
| Miền xuất | 2000 x 2000 m |
| Lưới xuất | 50 x 50, bước 40 m |
| Thời gian | k=0,...,999, dt=1 s; 1000 khung, khung cuối 999 s |
| Tâm ô x,y | 20,60,...,1980 m, y hướng lên |
| Gió vật lý | (-5,0) m/s |
| Seed đã dùng tạo G | 20261111 |
| Thời gian tương quan vật chất | 300 s |
| rho | exp(-1/300) = 0.9966722160545233 |
| Trọng số fine/coarse, hệ số coarse | 0.35/1, u=5 |
| Miền tổng hợp trước khi crop | 9000 x 4200 m, 225 x 105 ô |
| gamma0 | {gamma:.17g}, cố định từ dữ liệu nguồn |
| Wavelength | 1550 nm, tỷ số 1550/550 không thứ nguyên |
| Bản đồ tham chiếu | Zenith = {cfg['reference_zenith_deg']:g} độ, đi qua toàn bề dày |

## 2. Truy nguyên bài báo: phần nào được công bố?

Tài liệu: Ibrahim et al., IEEE TMLCN (2024), DOI
[10.1109/TMLCN.2024.3457490](https://doi.org/10.1109/TMLCN.2024.3457490).
Đã đọc Section II-A (trang PDF 5-6, trang in 1373-1374), Section IV-A,
Algorithm 1 (trang PDF 9-10, trang in 1377-1378), kiểm tra ảnh render các trang liên quan.
PDF cục bộ và SHA-256 có trong `references.json`; IEEE HTML bị chặn xác minh robot,
vì vậy bản PDF người dùng cung cấp là bằng chứng nội dung chính.

Phương trình (5), (6), (7) trong bản PDF cung cấp lần lượt omega theo visibility,
số mũ theo visibility, và visibility theo L,N. Algorithm 1 dùng hai thang Gaussian,
dịch vòng, thêm nhiễu, mask và làm mờ. Dòng 22 và đoạn sau thuật toán nói về
chuẩn hóa **bề dày** theo thống kê khí tượng; không định nghĩa phép đổi G sang
CLWC tính bằng g/m3, không chỉ ra L0 có thể suy ra từ trường Gaussian đã lưu.
Section IV-A còn dùng mức suy hao đơn giản 3 dB/km RF, 300 dB/km FSO cho mô phỏng.
Gói mới không mặc định nhận các mức đó làm kết quả Kim hoặc làm tham số hiệu chuẩn.

Phần cải tiến riêng của Ibrahim Stationary: Gaussian với chuẩn hóa phương sai
biên theo ensemble bằng hệ số tuyến tính cố định; AR(1) stationary;
Fourier interpolation/advection và miền có đệm. Những phần này không phải
phương trình nguyên văn của bài báo. Gói mới chỉ kế thừa G đã xuất.

## 3. Gaussian sang CLWC: giả định bổ sung, không phải định luật khí tượng

Định nghĩa surrogate không âm:

\[
L_k(x,y)=L_0\max(G_k(x,y)-\gamma_0,0)\quad[\mathrm{{g/m^3}}].
\]

L0 mang đơn vị g/m3 cho mỗi đơn vị latent. Hàm positive-part biểu diễn không
có nước lỏng ở phần dưới ngưỡng và lượng nước tăng theo biên độ latent ở trên.
Nó liên tục và Lipschitz trong G, không bảo toàn khối lượng/độ ẩm, không giải
phương trình ngưng tụ, không sinh phổ kích thước giọt. Đây là lựa chọn surrogate
có đơn vị và kiểm soát được tham số, **không phải một phép ánh xạ đã kiểm chứng vật lý**.
Không dùng softplus cũ làm CLWC, không dùng mask cũ để gán loss 0/1.

gamma0 giữ nguyên cho mọi ô, mọi khung và mọi kịch bản. Không min-max,
không chia phương sai từng ảnh, không lấy lại quantile từng thời điểm.
gamma0 xuất phát từ quantile của G0 nên phụ thuộc mẫu G0: phép đổi không tạo ra
bảo đảm stationarity có điều kiện vào ngưỡng ước lượng này. Khi coi gamma là
hằng số ngoại sinh và G~N(0,1), phân phối L có atom Phi(gamma) tại 0 và phần dương
CDF `Phi(gamma+l/L0)`; xác suất dương tham chiếu là
{100*independent_gaussian_positive_prob:.6f}%. Đây không phải khớp lý thuyết có điều kiện
cho seed đã chọn. Tỷ lệ L>0 thực tế gộp cả nhiệm vụ là {100*fraction:.6f}%.
Các ô L=0 là vùng không có nước lỏng của surrogate, không phải optical blockage.

## 4. Visibility và công thức suy hao được thực thi

\[
V=1.002/(LN)^{{0.6473}}\quad[\mathrm{{km}}],\quad
\omega_\lambda=\frac{{3.91}}{{V}}(\lambda_{{nm}}/550)^{{-x(V)}}
\quad[\mathrm{{dB/km}}].
\]

L dùng g/m3, N dùng cm^-3, lambda dùng nm: hằng số thực nghiệm chỉ có nghĩa
với quy ước đơn vị này, không tự ý đổi N sang m^-3 mà giữ 1.002.
Hệ số 3.91 và nhãn dB/km giữ đúng quy ước bài báo/yêu cầu. Không thêm hệ số
đổi Np sang dB, không khẳng định đây là xác minh Mie scattering hoặc hiệu chuẩn
định nghĩa visibility/extinction; cần rà soát quy ước đo khi tích hợp vật lý.

**Phương trình (6) bản in chỉ có ba nhánh sau, không phải công thức Kim năm nhánh thường gặp:**

| Miền V (km) | x(V) thực thi | Nguồn |
|---|---:|---|
| 0<V<6 | 0.585 cbrt(V) | Bản in Eq.(6) |
| V=6 | 1.3 | Bổ sung điểm thiếu, nhận nhánh trên; giả định triển khai công khai |
| 6<V<=50 | 1.3 | Bản in Eq.(6) |
| V>50 | 1.6 | Bản in Eq.(6) |

Tại V=50 dùng 1.3. Giới hạn bên trái V=6 là 0.585*cbrt(6), khác 1.3;
tại V=50 có bước nhảy 1.3 sang 1.6. Vì vậy omega/A **không liên tục toán học
trên toàn miền**, dù mang giá trị thực liên tục và không bị biến thành nhị phân.
Không làm trơn hoặc thay công thức để che bước nhảy này. Kiểm thử kiểm tra liên tục
trong từng nhánh và kiểm tra bước nhảy thật ở biên. Tham số mô phỏng không bị điều
chỉnh để tránh các miền: số lượng ô thuộc từng nhánh lưu trong `metadata.json`.

Tại L=0: V=+infinity theo giới hạn, omega=0, A=0, T=1 chính xác.
Vô cực này chỉ là sentinel toán học của hàm visibility; không ghi vào NPZ/JSON số.
Tất cả các mảng đầu ra hữu hạn. Tính visibility miền dương qua log để tránh LN
underflow/overflow. Tham số làm vượt miền float64 bị từ chối, không clipping.

## 5. Hình học lớp mây và đường truyền

Các ảnh A(x,y,k) là **bản đồ lớp mây tham chiếu chiếu thẳng đứng**, không phải
bản đồ tọa độ UAV. Không gán một độ cao mây thực tế cho hệ thống QKD hiện có.
Với đi xuyên cả lớp và giả sử dùng một CLWC đại diện trên đoạn trong mây:

\[
A=H_c\omega_\lambda/\cos\zeta,\qquad T=10^{{-A/10}}.
\]

Hc tính bằng km, zeta là góc zenith. Cùng một cột đại diện, zenith 30/60 độ
nhân A theo 1.1547005/2 so với thẳng đứng; T ở 60 độ bằng T_vertical^2.
Đây là tách riêng hệ số hình học, không phải hiệu ứng vị trí khi đổi hướng tia.

Hàm `layer_intersection` cắt đoạn thẳng hữu hạn UAV-HAP theo slab [z_base,z_top]
bằng tham số t thuộc [0,1]. Đoạn có giao cắt mới có loss; lớp ở dưới UAV hoặc
ngoài đoạn cho A=0,T=1. Khi chỉ đi qua một phần lớp, dùng chiều dài giao thực,
không dùng toàn Hc/cos(zeta). Tọa độ qc là trung điểm của đoạn nằm trong lớp.
Hàm `sample_clwc` nội suy song tuyến tính CLWC tại qc trong tâm ô đã lưu,
không wrap/extrapolate. Ngoài miền gây lỗi, không tự gán trời quang.

Ví dụ minh họa: UAV=(500,1000,1000)m, HAP=(10000,1000,20000)m,
lớp [2000,2500]m cho qc=(1125,1000,2250)m, khác xy của UAV.
`geometry_examples.json` có cả giao toàn phần, không giao, giao một phần.
Các tọa độ đều là giả định độc lập, không trích từ kênh QKD.
`representative_link_attenuation` dùng omega(L(qc))*chiều dài giao, là
xấp xỉ midpoint cho trường thay đổi theo phương ngang. Nếu độ dịch ngang trong
mây không nhỏ so với thang biến đổi L, cần tích phân dọc tia trước tích hợp thực.

Giao diện tương lai `combine_clear_cloud(T_clear,T_cloud)` chỉ nhân tỷ lệ công suất
trong [0,1]. Không được gọi trong bất kỳ phép tính QKD/SKR hiện hữu nào ở nhiệm vụ này.

## 6. Các kịch bản minh họa và độ hợp lý về cấp độ

Tất cả hàng sau đều **ILLUSTRATIVE_UNCALIBRATED**, không phải giá trị đo hoặc
bộ tham số hiệu chuẩn từ Ibrahim. Mỗi hàng chỉ thay một tham số so với reference.

| Kịch bản | L0 (g/m3) | N (cm^-3) | Hc (km) |
|---|---:|---:|---:|
{parameters}

Tham chiếu cấp độ độc lập:
[OPAC/GEISA, bảng water clouds](https://geisa.aeris-data.fr/opac/)
liệt kê mô hình stratus với L~0.28-0.30 g/m3 và N~80-250 cm^-3;
đây là mô hình microphysics tham chiếu, không phải dữ liệu tại khu vực UAV-HAP.
Các N minh họa cùng cấp độ; L0 không đồng nhất với L trung bình nên không được
đối chiếu trực tiếp L0 với L trong bảng. Cần xét trung bình có nước và phần đuôi
trong bảng kết quả bên dưới. Có cùng cấp độ với một số mô hình không chứng minh
phân phối, khí hậu, nhiệt độ pha lỏng hoặc độ dày minh họa là đúng thực tế.
Không áp dụng quan hệ fog/liquid droplets này cho cirrus băng tùy tiện.

| Kịch bản | E[L\|L>0] (g/m3) | Max L | Mean A (dB) | Max A (dB) | Min T |
|---|---:|---:|---:|---:|---:|
{results}

Phân phối rectified Gaussian có đuôi dương không bị chặn. Không có saturation
để ép hợp lý khí tượng; nếu hiệu chuẩn cần thay phân phối, phải là một mô hình mới
có dữ liệu và quyết định khoa học riêng. L0,N,Hc chưa xác định từ quan trắc.
Độ dày 0.1/0.5/1 km là giả định khảo sát độ nhạy, không lấy từ PDF thickness Figure 5.

## 7. Kết quả phân phối tham chiếu

| Đại lượng | Mean | Std | Median | q95 | q99 | Max |
|---|---:|---:|---:|---:|---:|---:|
{quantiles}

Atom A=0 chiếm {100*ref['attenuation_db']['zero_fraction']:.6f}% số ô-khung;
không được bỏ atom khi báo cáo mật độ/CDF. `empirical_cdf.csv` lưu số đếm CDF chính
xác ở các nút A được lưu; đường nối các nút trên hình chỉ phục vụ hiển thị.
`attenuation_histogram.csv` dùng 100 bins cố định trên [0,maxA], bao gồm atom ở bin đầu.
Thông kê theo thời gian ở `time_statistics.csv`, không lấy các slot làm mẫu iid.
Không báo confidence interval từ 2.5 triệu ô-khung phụ thuộc.

## 8. Tương quan sau ánh xạ phi tuyến

Một hàm cố định theo điểm giữ thứ tự thời gian và quan hệ không gian của mẫu,
không hoán vị, không tạo dịch mới. Nó không giữ nguyên Gaussian covariance.
Với ngưỡng ngoại sinh và Gaussian chuẩn, có thể biểu diễn covariance qua tích phân
Gaussian hai biến của f(G1)f(G2); ở đây đánh giá **thực nghiệm** trên nhiệm vụ đã lưu.
Các hệ số là Pearson tính từ toàn bộ cặp hợp lệ, loại bỏ biên wrap, trừ riêng mean
của mỗi tập cặp và chuẩn hóa bằng phương sai của chính hai tập. Không phải
covariance được bảo đảm bằng rho^lag cho A.

| Trường | spatial x 40m | spatial y 40m | Euler lag1s | Euler lag8s | Euler lag400s |
|---|---:|---:|---:|---:|---:|
{correlations}

So sánh Eulerian khác với material-frame AR(1): tại một tọa độ cố định còn có
tác động gió và hàm covariance đa thang. Không diễn giải tau=300s như correlation
time của A tại mọi tọa độ. Tương quan âm nhỏ ở xa cũng có thể do covariance có
dao động/loại DC của nguồn và nhiễu ước lượng hữu hạn, không sửa hoặc clipping.

Kiểm tra hướng chuyển động qua các cặp `G(k,r),G(k+8,r+h)` và các trường biến đổi:

| Trường | hx=-80m | hx=-40m | hx=0 | hx=40m | hx=80m |
|---|---:|---:|---:|---:|---:|
{windrows}

Gió dự kiến -40m/8s. Các hệ số là chẩn đoán mô tả, không ép đỉnh hoặc kiểm định
Gaussian-covariance sau phi tuyến. Phép biến đổi theo điểm giao hoán với phép
dịch hoán vị của một trường đóng băng; test kiểm tra tính chất này.
Với dịch Fourier phân số và phi tuyến, không khẳng định f(A_vG)=A_v f(G)
trên lưới nội suy; chỉ kế thừa chuyển động của G đã lưu tại từng khung.

## 9. Biên miền và kiểm tra số

Backtrace của miền quan sát nguồn nằm trong miền tổng hợp 9km x 4.2km:
0s x=[1000,3000]m;400s=[3000,5000]m;999s=[5995,7995]m;
horizon đệm 1000s=[6000,8000]m. Biên y=[1000,3000]m.
Đã tính lại từ metadata, guard tối thiểu 1000m. Phép đổi mới theo điểm không
thêm wrap hoặc advection, nên không thêm cloud re-entry. Đây là không tái nhập
hình học qua characteristic, không phải mô hình vô hạn có độc lập compact support:
Fourier interpolation nguồn có support toàn cục và covariance trên torus hữu hạn.

13 kiểm tra công thức/dữ liệu chính cộng kiểm tra hash bảo vệ có trong `validation.json`.
Sai số lớn nhất khi đảo T về A: {validation['max_A_T_inverse_error_db']:.6g} dB.
Không có NaN/Inf trong các mảng L,omega,A,T đã lưu. T thuộc (0,1], không floor T.
API từ chối trường hợp T underflow float64; cần giữ A/logT khi đánh giá loss cực lớn,
không thay số 0 bằng epsilon. Không có attenuation clipping hay saturation.

`regression_tests.log` chứa 16 test mới và 33 test hồi quy của ba mô hình mây;
`artifact_verification.json` là kết quả kiểm tra chỉ đọc cuối cùng.
Thời gian biến đổi, thống kê và nén dữ liệu bảy kịch bản:
{meta['transform_and_analysis_seconds']:.3f} s (Python {meta['Python']}, NumPy {meta['numpy']}).
Không bao gồm render/GIF và không phải chi phí tạo G. Không hứa thời gian thực
trên phần cứng khác; `render_receipt.json` ghi thời gian vẽ riêng.

## 10. Tệp và tái lập

`cloud_clwc.npz`: clwc_g_m3[k,y,x], time_s,x_m,y_m,gamma_fixed,L0,units.
`cloud_attenuation_db.npz`: attenuation_db[k,y,x], specific_db_km[k,y,x], tọa độ/đơn vị.
`cloud_transmittance.npz`: transmittance[k,y,x], tọa độ/đơn vị.
Tất cả số float64, nạp bằng allow_pickle=False; metadata chuỗi/JSON riêng.
Ba tệp chính dành cho reference; bảy kịch bản có snapshots, thống kê toàn 1000 slot
và CDF. Cấu hình cho phép tái tính mảng đầy đủ của bất kỳ hàng nào trong namespace mới.

Hình A-D: 7 snapshots 0,100,200,400,600,800,999s và histogram; mỗi đại lượng có
một thang màu cố định cho toàn nhiệm vụ, không per-frame normalization.
Hình E: mean/max, phân phối, tương quan không gian/thời gian, histogram/CDF.
Hình F: L0/H/N thay riêng từng tham số. Hình G: ba tọa độ lớp mây cố định.
Mỗi hình có PNG400dpi và PDF; E/F/G là vector native text. Bản đồ trong PDF là
raster đúng dữ liệu với trục/chữ vector. GIF có 1000 khung, y hướng lên, 50ms/khung
chỉ là tốc độ phát tăng 20 lần, dt vật lý vẫn 1s.

Lệnh trong README; runner không gọi simulator hoặc QKD, từ chối ghi đè output
đã có dữ liệu. Plotter/report chỉ đọc mảng đã lưu. Seed thuộc dữ liệu nguồn;
tái lập suy hao bằng hash nguồn và biến đổi xác định, không tái chạy 1000 Gaussian.

## 11. Điều kiện trước tích hợp UAV-HAP CV-QKD

Đã sẵn sàng làm **giao diện chẩn đoán phần mềm độc lập** cho các thử nghiệm có
phạm vi mới. Chưa sẵn sàng làm mô hình suy hao mây vật lý đã kiểm chứng hoặc
thay mô hình kênh trong đánh giá QKD công bố. Cần dữ liệu CLWC/N, phân bố giọt,
độ cao/bề dày/nhiệt độ/pha mây và hình học đường truyền thực; hiệu chuẩn mapping;
xác nhận miền áp dụng visibility và quy ước extinction; xử lý biến đổi ngang dọc tia;
đánh giá sai số và tách nguồn suy hao clear/cloud để tránh tính hai lần.

Không thay QKD/channel, SKR, finite-size, tối ưu UAV, mô hình mây cũ, cache, manuscript,
security hoặc publication settings. Không chạy training/final-test/held-out/publication
evaluation. Toàn bộ test repository: **NOT_RUN**, chỉ chạy suite mây liên quan.
Sai khác hash frozen model, E2 INCONCLUSIVE, strictPhaseBfalse,
UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS,
Objective C USER_STOPPED giữ nguyên. Không tự động thực hiện tích hợp tiếp theo.
'''
    (out/'report_vi.md').write_text(doc,encoding='utf-8')
    files=sorted(p.name for p in out.iterdir() if p.is_file())
    (out/'README.md').write_text('# Continuous cloud attenuation diagnostic\n\n'
       'ILLUSTRATIVE_UNCALIBRATED. Read report_vi.md and ../../docs/IBRAHIM_CONTINUOUS_ATTENUATION_README.md.\n\n'
       'Seven PNG400dpi/PDF pairs A-G; 1000-frame GIF; three full reference NPZs.\n'
       'No Gaussian regeneration, no binary blockage, no QKD integration.\n\n'
       'Read-only verification from project root:\n\n'
       '```powershell\n.\\.venv\\Scripts\\python.exe -X utf8 -B scripts/verify_ibrahim_continuous_attenuation.py '
       'results/ibrahim_continuous_attenuation_20261112\n```\n\n'
       'Files (final complete index also recorded in artifact_hashes.json):\n\n'+
       '\n'.join('- '+name for name in files)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    report(p.parse_args().output.resolve())
