# Phase 5D: độ nhạy khả thi của proxy finite-size

Phạm vi: phân tích thăm dò từ **10 SKR thô đã có** của năm điểm pilot Phase 5C,
cho hai trường hợp historical và target. Không gọi lại evaluator SKR, không chọn
quỹ đạo, không đặt thông số mission và không nâng mức bằng chứng bảo mật.

Dữ liệu đầu vào là `results/phase5c_skr_noise_pilot_20261107/summary.json`.
Chương trình kiểm SHA-256 trong `output_manifest.json`, từng checkpoint/seal,
liên kết input-manifest và đối chiếu nguyên bản winner MB với summary trước
khi lấy `K_raw`. Nhãn nguồn vẫn là `INSUFFICIENT_EVIDENCE`,
`security_valid=false`, `paper_admissible=false`, `paper_mode=NOT_RUN`.

## Công thức và ý nghĩa số tín hiệu

Với một block có SKR thô clear không đổi (r), số tín hiệu **đã hợp lệ** (n),
và tham số proxy (0<\epsilon<1), dùng nguyên helper hiện hữu:

\[
L(n)=\max\{0,nr-7\sqrt{n\log_2(2/\epsilon)}\},\qquad
\Delta(n)=7\sqrt{\log_2(2/\epsilon)/n}.
\]

Penalty được trừ **một lần tại cuối block**. Không cắt (r) trước khi cộng và
không nhân thêm clear fraction vào block đã có (n=n_{valid}).
Với (r>0), bình phương bất đẳng thức dương cho:

\[
L(n)>0\iff n>n_{crit}=\frac{49\log_2(2/\epsilon)}{r^2},\qquad
n_{min}=\lfloor n_{crit}\rfloor+1.
\]

Với (r\le0), không có block dương. Với (n=0), key bằng 0 và không định
nghĩa Delta mỗi tín hiệu. `Decimal` 80 chữ số giữ chính xác giá trị float đầu
vào khi lấy floor để tránh làm tròn qua ranh giới nguyên; cột `n_crit_decimal`
giữ kết quả đó. `finite_key` float hiện hữu tính bit. Sát ranh giới, phép trừ
float có thể trả về 0 dù giá trị toán học dương rất nhỏ. Không dùng điều này
để tuyên bố key được chứng nhận. Hàm threshold từ chối ngưỡng vượt miền đếm
nguyên chính xác của float; miền thăm dò hiện tại nằm trong miền đó.

## Năm điểm và hai mức noise

Tại (\epsilon=3\times10^{-8}); bit ở cột cuối dùng **block tham chiếu**

\(n=8\times10^7\), không phải block mission được chọn:

| Điểm | Noise | (r_{clear,raw}), bit/tín hiệu | (n_{crit}), xấp xỉ | (n_{min}) nguyên | (L(8\times10^7)), bit proxy |
|---|---|---:|---:|---:|---:|
| p0 | historical | 0.000796087808086127 | 2,009,500,590.466 | 2,009,500,591 | 0 |
| p1 | historical | 0.000790484394200375 | 2,038,090,585.511 | 2,038,090,586 | 0 |
| p2 | historical | 0.000747067033826848 | 2,281,870,210.772 | 2,281,870,211 | 0 |
| p3 | historical | 0.000796048935176985 | 2,009,696,852.373 | 2,009,696,853 | 0 |
| p4 | historical | 0.000749004693710503 | 2,270,079,178.609 | 2,270,079,179 | 0 |
| p0 | target | 0.004955337789912750 | 51,863,707.009 | 51,863,708 | 77,236.466 |
| p1 | target | 0.004948237183717591 | 52,012,660.251 | 52,012,661 | 76,668.417 |
| p2 | target | 0.004893349597699492 | 53,186,032.561 | 53,186,033 | 72,277.410 |
| p3 | target | 0.004955288516825029 | 51,864,738.432 | 51,864,739 | 77,232.524 |
| p4 | target | 0.004895794346111787 | 53,132,928.205 | 53,132,929 | 72,472.990 |

Không suy ra rằng các giá trị (r) không đổi trong một mission thật.
Với trajectory có rate thay đổi, cần tính \(S_K=\sum_k m_kr_k\) và
\(n_K=\sum_km_k\) bằng evaluator hiện có. Ngưỡng constant-rate là điều kiện
của từng pilot point; nó không tự chứng minh feasibility theo energy/graph/
horizon hoặc cho mọi vị trí chưa tính.
Giá trị `key_fraction=0.8`, (N=10^8), (n=8\times10^7) chỉ được lấy làm
tham chiếu từ `configs/finite_size/ieee_2025_reference.yaml`. Tỷ lệ 0.8 không
tự thay thế `eta_valid` và không nhân vào (n) lần nữa.

## Độ nhạy theo block và epsilon

Các trục sau do phân tích chọn để khảo sát, mang nhãn
`EXPLORATORY_ANALYSIS_AXES_NOT_AUTHOR_SELECTED_MISSION`.

| (n_{valid}) | Delta, bit/tín hiệu; epsilon (3\times10^{-8}) |
|---:|---:|
| (10^5) | 0.112850903880319 |
| (10^6) | 0.0356865892270543 |
| (10^7) | 0.0112850903880319 |
| (8\times10^7), tham chiếu | 0.00398988196984026 |
| (10^8) | 0.00356865892270543 |
| (10^9) | 0.00112850903880319 |
| (10^{10}) | 0.000356865892270543 |

Ví dụ p0, cùng (n=8\times10^7), mỗi noise vẫn dùng đúng (r) tương ứng:

| Epsilon | Delta | (n_{min}) historical | (n_{min}) target | (L) historical | (L) target |
|---:|---:|---:|---:|---:|---:|
| (10^{-6}) | 0.00358058455405134 | 1,618,362,882 | 41,768,736 | 0 | 109,980.259 |
| (3\times10^{-8}) | 0.00398988196984026 | 2,009,500,591 | 51,863,708 | 0 | 77,236.466 |
| (10^{-10}) | 0.00457813385356797 | 2,645,726,906 | 68,284,233 | 0 | 30,176.315 |

`block_sensitivity.csv` chứa đủ (10\times7\times3=210) tổ hợp. Không diễn
giải epsilon tham chiếu (tổng ba epsilon trong YAML) thành chứng minh bảo mật
composable; đây là tham số của proxy được giữ nguyên.

## Mission giữ (f_s) là biến chưa gán

Với clear fraction (c) và thời gian \(T=K\Delta t\), chưa chọn K hay horizon nhiệm vụ:

\[
n=f_s\eta_{valid}cT,\qquad
f_s\eta_{valid}>\frac{n_{crit}}{cT}\quad(c>0).
\]

Để cấp ngân sách nguyên (n_{min}), cần
\(f_s\eta_{valid}\ge n_{min}/(cT)\). Chênh lệch giữa dấu `>` cho ngưỡng liên
tục và `>=` cho ngân sách nguyên được giữ riêng trong CSV. Khi phép nhân cho
số thực, hệ thống thực tế phải bảo đảm số tín hiệu nguyên được giữ lại đạt
ít nhất (n_{min}). `eta_valid` mô tả phần tín hiệu hợp lệ trong thời gian
clear; (c) chỉ loại thời gian bị chặn. Nếu một định nghĩa eta khác đã bao
gồm cloud thì phải tránh tính hai lần trước khi áp dụng ánh xạ này.

Ví dụ **ngưỡng tích**, p0 target, epsilon (3\times10^{-8}), (c=1):

| (T), giây thăm dò | (f_s\eta_{valid}>), tín hiệu/giây | Ngân sách nguyên (f_s\eta_{valid}\ge), tín hiệu/giây |
|---:|---:|---:|
| 1 | 51,863,707.0093 | 51,863,708 |
| 10 | 5,186,370.70093 | 5,186,370.8 |
| 100 | 518,637.070093 | 518,637.08 |
| 300 | 172,879.023364 | 172,879.026667 |
| 1000 | 51,863.7070093 | 51,863.708 |

Giữ (T=100) giây **thăm dò**, cùng điểm/noise/epsilon:

| Clear fraction (c) | Ngưỡng tích strict `>` | Ngân sách nguyên `>=` |
|---:|---:|---:|
| 0 | Không khả thi, (n=0,L=0) | Không có ngưỡng hữu hạn |
| 0.25 | 2,074,548.28037 | 2,074,548.32 |
| 0.5 | 1,037,274.14019 | 1,037,274.16 |
| 0.75 | 691,516.093458 | 691,516.106667 |
| 1 | 518,637.070093 | 518,637.08 |

`mission_sensitivity.csv` chứa đủ (10\times3\times5\times5=750) tổ hợp.
Không có giá trị mission nào cho `f_s`, `eta_valid`, `m0`, hoặc tốc độ bit/s
thực tế. Với (c>0,r>0), `feasible` để null vì chưa có tích thực tế để so
sánh; với (c=0) hoặc (r\le0), `feasible=false`, `key_bits=0`.

## Tái tạo và kiểm tra

Chạy tại `uav_cvqkd_optimization/` với `PYTHONPATH=src`:

```text
python -m pytest tests/test_phase5d_finite_size.py -q
python -m uav_qkd.finite_size_feasibility --output results/phase5d_finite_size_20261108_verified
```

Kiểm thử tập trung hiện tại: **20 passed**, bao gồm ngưỡng strict/rất gần ranh
giới nguyên, miền đầu vào, block rỗng, rate không dương, penalty một lần,
clear fraction không lặp, giữ mission chưa gán, đủ 10 rate pilot thực, và
từ chối sai hash/thiếu coverage manifest và từ chối output không rỗng trước
khi ghi bất kỳ file nào. Không chạy lại cả suite ở subtask
này để tránh tranh tài nguyên với benchmark đang do tác vụ chính quản lý.

Artifacts chính thức của phân tích đã kiểm tra nằm trong
`results/phase5d_finite_size_20261108_verified/`: `summary.json`, hai CSV,
`input_manifest.json` ghi SHA-256 toàn bộ
pilot/config/producer được dùng, và `output_manifest.json` niêm phong các
output. Manifest ghi rõ không tính lại nguồn vật lý gốc. Việc đọc các scalar
đã niêm phong không chứng nhận lại C/w hoặc mô hình bảo mật nguồn.

Thư mục output phải chưa tồn tại hoặc rỗng. Khi tái tạo, chọn một thư mục mới;
chương trình không ghi đè một bộ kết quả có sẵn. Checkpoint phát triển trước đó
ở `results/phase5d_finite_size_20261108/` được giữ nguyên. Producer đã thực thi
cho checkpoint này được lưu nguyên byte ở
`docs/phase5d_validation/finite_size_executed_producer_snapshot.py`, SHA-256
`fc7ff508d7966eab19602f60b02ee45b160b8d45ebfa4ceb53c729b3f4add72f`,
khớp producer hash trong input manifest của checkpoint cũ. Bản verified
niêm phong producer hiện tại có thêm chốt bảo vệ output; các bảng số học và
summary giữ nguyên nội dung.

Chưa kiểm tra tính khả thi mission thực vì `f_s`/`eta_valid` chưa được tác giả
cung cấp. Proxy dương không phải cam kết khóa có bảo mật composable.
