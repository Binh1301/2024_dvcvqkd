# Năng lượng UAV tối thiểu theo quãng đường và thời gian

Nghiên cứu dùng trực tiếp `power`, `derivatives`, `lower_hull` và các hằng số từ
[`../main.py`](../main.py), giữ nguyên mô hình và tham số vật lý. Không chạy hàm
`main()` của nghiên cứu cũ. Mọi tệp mới, bao gồm cache và tệp tạm, nằm trong
`emin_distance_time/`. Không nhập mô-đun của `paper_uav_hap_cvqkd`.

## Chạy lại

Từ thư mục gốc `2024_dvcvqkd`:

```powershell
python -B uav_energy_speed_study/emin_distance_time/main.py
python -B uav_energy_speed_study/emin_distance_time/verify_artifacts.py
```

Dùng các gói đã cài: Python 3.13.7, NumPy 2.2.6, SciPy 1.16.2,
Matplotlib 3.10.5 trong lần chạy này. Bộ kiểm tra tệp xuất dùng thêm Pillow và
pypdf đã cài sẵn. Không cài thêm phụ thuộc. Lệnh tái tạo các
tệp đầu ra của **nghiên cứu con này**; không ghi đè hình hay kết quả nghiên cứu
trước. `validation.json` lưu phiên bản thực tế, SHA-256 mã nguồn và tham số;
`preservation.json` so sánh SHA-256 của cả 24 tệp đã có trong nghiên cứu cha.

## Mô hình và miền khả thi

Mô hình gốc được ghi lại để giải thích; tính toán gọi trực tiếp hàm gốc:

$$
P(V)=P_0\left(1+\frac{3V^2}{U_{\mathrm{tip}}^2}\right)
+P_i\left(\sqrt{1+\frac{V^4}{4v_0^4}}-\frac{V^2}{2v_0^2}\right)^{1/2}
+\frac12d_0\rho s A V^3.
$$

| Tham số | Giá trị giữ nguyên |
|---|---:|
| $P_0$ | 79.85628 W |
| $P_i$ | 88.62794 W |
| $U_{\mathrm{tip}}$ | 120 m/s |
| $v_0$ | 4.02854 m/s |
| $d_0$ | 0.6 |
| $\rho$ | 1.225 kg/m³ |
| $s$ | 0.05 |
| $A$ | 0.503 m² |
| $V_{\max}$ | 30 m/s |

Vì hàm `power` gốc giới hạn $0\leq V\leq30$ m/s, bài toán được giải là

$$
E_{\min}(D,t)=\min_{0\leq V(\tau)\leq30}
\int_0^t P(V(\tau))\,d\tau,
\qquad \int_0^t V(\tau)\,d\tau=D.
$$

Với $D\geq0,t>0$, điều kiện khả thi cần và đủ là $D\leq30t$.
Miền khảo sát: $100\leq D\leq5000$ m, $20\leq t\leq1000$ s;
bước $\Delta D=10$ m, $\Delta t=2$ s: **491 × 491 = 241081 điểm**,
gồm **224727 điểm khả thi** và **16354 điểm không khả thi**.
Các tọa độ không khả thi vẫn có cờ `feasible=False` trong CSV để giữ hình dạng
lưới; trường năng lượng và lịch bay để trống, không gọi $P$ tại tốc độ vượt trần.
Trên hình, miền này có màu xám nhạt hoặc không có bề mặt.

## Bao lồi dưới và nghiệm toàn cục

Đặt $\bar V=D/t$, $H=P(0)=168.48422$ W. Bay đều cho

$$E_{\mathrm{constant}}(D,t)=tP(\bar V).$$

Hàm $P$ không lồi trên toàn miền nên không thể áp dụng bất đẳng thức Jensen
trực tiếp cho $P$. Với thời gian chuyển tốc độ bằng không, không có chi phí
chuyển trạng thái và không ấn định tốc độ đầu/cuối, có thể chia thời gian giữa
các tốc độ. Bao lồi dưới $P_{\mathrm{ce}}$ cho nghiệm chính xác:

$$E_{\min}(D,t)=tP_{\mathrm{ce}}(D/t).$$

Ngưỡng tiếp xúc dương giải từ

$$V_*P'(V_*)-P(V_*)+H=0,$$

cho $V_*=6.301687645299708$ m/s và
$m=[P(V_*)-H]/V_*=-5.192734058403882$ W/(m/s). Khi đó

$$
P_{\mathrm{ce}}(v)=
\begin{cases}
H+mv,&0\leq v<V_*,\\
P(v),&V_*\leq v\leq30.
\end{cases}
$$

Tại $0<\bar V<V_*$, nghiệm đạt được bằng hover và bay ở $V_*$:

$$
t_{\mathrm{fly}}=\frac{D}{V_*},\qquad
t_{\mathrm{hover}}=t-\frac{D}{V_*},\qquad
E_{\min}=H\left(t-\frac D{V_*}\right)+P(V_*)\frac D{V_*}=Ht+mD.
$$

Cả năng lượng hover đều được tính. Thứ tự hai pha không ảnh hưởng năng lượng.
Khi $V_*\leq\bar V\leq30$, bay đều $V=\bar V$ trong toàn bộ thời gian là tối ưu.
Tại ngưỡng, thời gian hover bằng không; tại $D=0$, hover toàn thời gian.

### Vì sao đây là bao lồi liên tục, không chỉ là nghiệm trên lưới

Đặt $x=V^2/(2v_0^2)$, $r=\sqrt{1+x^2}$ và
$q=\exp[-\operatorname{asinh}(x)/2]$. Đây là cách viết tương đương của thành phần
công suất cảm ứng, chỉ dùng để phân tích đạo hàm; hàm công suất gốc không đổi.

$$q''(V)=\frac{q}{2v_0^2r^3}(xr+x^2-1).$$

Với $V\geq V_c=v_0\sqrt{2/\sqrt3}$, $q''\geq0$, do đó $P''>0$.
Với $0\leq x\leq1/\sqrt3$,

$$q'''(V)=\frac{3qV}{4v_0^4r^5}
\big[(1-x^2)r+3x-x^3\big]\geq0.$$

Thành phần cản khí động bậc ba làm $P''$ tăng nghiêm ngặt trên khoảng này.
Kết hợp $P''(0)<0<P''(V_c)$, có đúng một điểm uốn
$V_i=4.06297847589801$ m/s. Hàm
$g(V)=VP'(V)-P(V)+H$ có $g'(V)=VP''(V)$: giảm trước điểm uốn, sau đó tăng và
đổi dấu đúng một lần dương tại $V_*$. Vì thế $(P(V)-H)/V$ đạt cực tiểu toàn cục
tại $V_*$; đường thẳng $H+mV$ nằm dưới toàn bộ $P$.
Đường thẳng nối với nhánh lồi tại $V_*$ có cùng đạo hàm, tạo hàm lồi.
Mọi hàm lồi nằm dưới $P$ đều nằm dưới dây cung giữa hai điểm tiếp xúc, còn trên
$[V_*,30]$ thì bị chặn bởi chính $P$. Do đó đây là bao lồi dưới lớn nhất.

Với mọi lịch tốc độ khả thi đo được,

$$
\frac1t\int_0^t P(V(\tau))\,d\tau
\geq\frac1t\int_0^t P_{\mathrm{ce}}(V(\tau))\,d\tau
\geq P_{\mathrm{ce}}(D/t).
$$

Các lịch bay ở trên đạt đẳng thức nên chứng minh tối ưu toàn cục cho mô hình
lý tưởng. Lưới, quy hoạch tuyến tính và thử nghiệm ngẫu nhiên bên dưới là kiểm
chứng số bổ sung, không thay thế chứng minh liên tục này.

## Đối chiếu và kiểm chứng

| Đại lượng | Tính lại | Tham chiếu yêu cầu |
|---|---:|---:|
| $V_{\mathrm{me}}$ (m/s) | 10.21169000786013 | 10.211690 |
| $V_{\mathrm{mr}}$ (m/s) | 18.294478947026136 | 18.294479 |
| $P_{\min}$ (W) | 125.99075965238123 | 125.990760 |
| $E_{\min}(1000,100)$ (J) | 12601.691755311773 | 12601.691755 |

Sai số so với các giá trị tham chiếu đã làm tròn đều dưới $10^{-6}$ theo đơn vị
tương ứng. So với CSV gốc, năm đại lượng đặc trưng và toàn bộ đường $P(V)$
tái lập với sai khác **0** trong lần chạy này.
Tại $(1000\ \mathrm m,100\ \mathrm s)$, $\bar V=10>V_*$:
bay đều 10 m/s là nghiệm toàn cục, không có tiết kiệm do thay đổi tốc độ.
Chặn dưới $tP_{\min}=12599.075965238122$ J không đạt được ở điểm này vì tốc độ
$V_{\mathrm{me}}$ không cho đúng quãng đường trong đúng 100 s.

Mã chạy **24 kiểm tra có tên**, dừng bằng lỗi nếu một kiểm tra thất bại, cùng
kiểm tra từ chối đầu vào âm/không hữu hạn hoặc thời gian bằng không:

- Đạo hàm giải tích so với sai phân độc lập của hàm công suất gốc: sai khác lớn
  nhất khoảng $5.92\times10^{-10}$ cho đạo hàm bậc một và $9.63\times10^{-7}$
  cho đạo hàm bậc hai.
- Trên toàn bộ lưới khả thi: ràng buộc tốc độ, thời gian, quãng đường, năng lượng
  đạt được bởi lịch bay, $E_{\min}\leq E_{\mathrm{constant}}$ và
  $E_{\min}\geq tP_{\min}$. Dung sai quãng đường $10^{-8}$ m, thời gian
  $10^{-10}$ s, năng lượng $10^{-6}$ J; sai số thực tế lưu trong JSON.
- Các biên hover, $D/t=V_*$, $D/t=30$ và điểm vượt trần tốc độ.
- Bao lồi lấy mẫu độc lập ở 601, 1201, 6001 và 30001 tốc độ. Sai khác công suất
  lớn nhất của lưới mịn nhất so với bao lồi liên tục khoảng $6.77\times10^{-8}$ W.
- Quy hoạch tuyến tính độc lập tại 8 tốc độ trung bình: tối thiểu
  $\sum_j w_jP(v_j)$ với $w_j\geq0$, $\sum_jw_j=1$,
  $\sum_jw_jv_j=\bar V$. Dùng 3001 tốc độ cách đều, bổ sung chính $\bar V$;
  không đưa $V_*$ vào lưới trừ ca kiểm tra tại $\bar V=V_*$.
  Đây là tối ưu toàn cục của bài toán rời rạc; sai khác dương nhỏ do rời rạc hóa.
- 5000 lịch ngẫu nhiên tám mức tốc độ (seed 20261028) không vi phạm chặn dưới.
- Tối ưu theo thời gian độc lập cho năm quãng đường yêu cầu, so với $D/V_{\rm mr}$.
- SHA-256 của 24 tệp nghiên cứu cũ không đổi.

## Xu hướng và mức tiết kiệm

Mức tiết kiệm

$$S(D,t)=100\frac{E_{\mathrm{constant}}-E_{\min}}{E_{\mathrm{constant}}}$$

chỉ phụ thuộc $D/t$. Tiết kiệm dương khi $0<D/t<V_*$; bằng không khi
$D/t\geq V_*$. Cực đại khoảng **3.239806968%** tại
$D/t\approx2.231113475$ m/s, có các điểm thuộc miền khảo sát đạt được tỷ lệ này.
Giá trị cực đại tỷ lệ được tìm bằng tối ưu vô hướng, không chỉ chọn ô lớn nhất.

Với **thời gian cố định**, $E_{\min}$ giảm khi tăng $D$ đến
$D=tV_{\mathrm{me}}$, rồi tăng nếu điểm này nằm trong miền khả thi đang xét.
Đoạn hover–fly có quan hệ tuyến tính $Ht+mD$ với $m<0$: tăng quãng đường thay
thế bớt hover có công suất cao. Vì vậy năng lượng không nhất thiết tăng theo $D$
khi buộc UAV duy trì thời gian bay cố định. Với $t=500$ và $800$ s, điểm cực tiểu
theo $D$ nằm trên 5000 m, nên các đường giảm trên toàn khoảng quãng đường vẽ.

Với **quãng đường cố định**, năng lượng ban đầu giảm theo $t$ khi giảm tốc từ
$V_{\max}$ đến $V_{\mathrm{mr}}$, đạt cực tiểu tại
$t_0=D/V_{\mathrm{mr}}$, rồi tăng khi kéo dài thời gian. Trong miền khảo sát,

$$t_{\mathrm{best}}=\operatorname{clip}(D/V_{\mathrm{mr}},20,1000).$$

Công thức clip ở đây áp dụng cho $100\leq D\leq5000$ m, nơi thời gian cực tiểu
tốc độ $D/30$ không loại nghiệm này. Với các $D$ cố định dùng trong hình:

| $D$ (m) | $t_0$ (s) | $\min_t E_{\min}$ (J) |
|---:|---:|---:|
| 500 | 27.330650 | 4414.171425 |
| 1000 | 54.661300 | 8828.342850 |
| 2000 | 109.322600 | 17656.685700 |
| 3000 | 163.983900 | 26485.028550 |
| 5000 | 273.306499 | 44141.714250 |

Sau $t>D/V_*$, nghiệm hover–fly làm năng lượng tăng tuyến tính theo thời gian
với hệ số $H$. Đây là ràng buộc **bay/hover trong đúng $t$ giây**; không cho phép
hạ cánh rồi tắt động cơ để chờ hết thời gian.

## Hình và tệp được tạo

Các hình dùng Matplotlib, trục và colorbar ghi đơn vị. Hình năng lượng dùng kJ
để dễ đọc; tất cả CSV giữ J. Mỗi tên dưới đây có **cả `.png` và `.pdf`**:

| Tên trong `figures/` | Nội dung |
|---|---|
| `fig01_emin_surface` | Bề mặt 3D $E_{\min}(D,t)$ |
| `fig02_emin_contour` | Đường đồng mức và miền khả thi |
| `fig03_emin_heatmap` | Bản đồ năng lượng tối thiểu |
| `fig04_emin_vs_distance` | Theo $D$, tại $t=100,200,300,500,800$ s |
| `fig05_emin_vs_time` | Theo $t$, tại $D=500,1000,2000,3000,5000$ m |
| `fig06_constant_vs_global` | So sánh hai chiến lược, phần năng lượng tiết kiệm |
| `fig07_savings_heatmap` | Bản đồ tỷ lệ tiết kiệm trên $(D,t)$ |
| `fig08_power_envelope` | Hàm công suất gốc và bao lồi dưới |

PNG được lưu với `dpi=320`; metadata PNG ghi khoảng 319.9892 dpi do làm tròn
pixel trên mét. PDF dùng đường và đa giác vector; mã tắt cả cơ chế tự raster hóa
colorbar của Matplotlib. Bộ kiểm tra xác nhận không có đối tượng ảnh raster
trong cả 8 PDF.
Lưới dữ liệu đầy đủ là 491 × 491; chỉ bề mặt 3D dùng khoảng 125 × 125 điểm để
giữ PDF gọn, không ảnh hưởng dữ liệu và phép tối ưu. Các đường cắt bổ sung chính
xác điểm chuyển chiến lược, biên khả thi và cực tiểu theo thời gian để không bỏ
sót các vị trí này giữa hai điểm lưới.

Các CSV trong `data/`:

- `emin_grid.csv`: toàn lưới, cờ khả thi, năng lượng hai chiến lược, mức tiết kiệm,
  tốc độ bay và thời gian của từng pha.
- `fixed_time_slices.csv`: năm đường theo quãng đường.
- `fixed_distance_slices.csv`: năm đường theo thời gian; cũng cấp dữ liệu so sánh
  hai chiến lược trong hình 6.
- `power_envelope.csv`: 30001 tốc độ, công suất gốc và bao lồi liên tục.
- `hull_convergence.csv`: hội tụ của bao lồi lấy mẫu độc lập.
- `reference_checks.csv`: bốn đối chiếu yêu cầu và dung sai.
- `optimal_duration_by_distance.csv`: thời gian và năng lượng tối ưu trên khoảng
  thời gian cho từng quãng đường của lưới.

Mã và báo cáo: `main.py`, `verify_artifacts.py`, `README.md`, `validation.json`, `preservation.json`,
`artifact_manifest.json` (danh sách tệp, dung lượng, SHA-256; không tự băm chính nó).
`artifact_checks.json` lưu kiểm tra lại tệp xuất; `.cache/visual_review.png` là
ảnh ghép phục vụ rà soát bố cục. Cache và tệp tạm không phải hình để đưa vào bài báo.

`verify_artifacts.py` đọc lại toàn bộ 241081 hàng CSV, kiểm tra lại các ràng buộc
và phép tính tỷ lệ tiết kiệm sau xuất/nhập, xác nhận 8 cặp hình đúng độ phân giải,
PDF một trang có chữ/font vector và không chứa ảnh raster, rồi cập nhật manifest.
Kiểm tra này cũng xác nhận mã nguồn còn khớp SHA-256 của kết quả và các tệp cũ
vẫn nguyên vẹn. Các hình PNG đã được rà soát trực quan bằng ảnh ghép.

## Phạm vi vật lý của kết luận

Nghiệm toàn cục ở đây thuộc mô hình công suất bay ngang, độ cao không đổi,
không gió, cho phép chuyển tốc độ tức thời và không quy định vận tốc đầu/cuối.
Nó không phải lịch điều khiển đã kiểm chứng trên UAV thật.
Chưa xét giới hạn gia tốc/giảm tốc, năng lượng chuyển pha, takeoff/landing,
động lực học rotor, ràng buộc vị trí hover, gió, công suất liên lạc, hiệu suất
pin/động cơ hay hiệu chuẩn phần cứng. Nếu thêm các ràng buộc đó mà vẫn dùng cùng
chi phí $P(V)$, tập nghiệm sẽ hẹp hơn nên bao lồi là chặn dưới; chưa có số liệu
để xác định mức tăng năng lượng hoặc kết luận lịch hover–fly khả thi động lực học.
Số chữ số báo cáo phục vụ tái lập số học, không biểu thị độ chính xác vật lý tương ứng.
