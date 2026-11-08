# Bộ rotor IEEE 2019 và Figure 02

## A. File tạo/sửa và phạm vi

| File | Mục đích |
|---|---|
| `configs/rotor/ieee_2019.yaml` | Bộ tham số gốc IEEE 2019, DOI/vị trí nguồn, chính sách v0 và thiết lập tính số; không phải mission config |
| `configs/rotor/arxiv_2018_v1.yaml` | Giữ bộ tham số cũ thành profile riêng, gồm chính sách dùng v0 bảng7.2 m/s |
| `src/uav_qkd/rotor_reference.py` | Dẫn xuất P0/Pi/v0, phân tách công suất và tính ME/MR; tái dùng `propulsion_power` hiện có cho tổng |
| `src/uav_qkd/rotor_power_figure.py` | CLI tái lập Figure02; kiểm nguồn/profile, xuất PDF/PNG/CSV/caption/JSON và từ chối ghi đè |
| `tests/test_rotor_reference.py` | 11 test/case mới về nguồn, hệ số, components, vận tốc tối ưu, version, stability và chống gắn nhãn sai |
| `docs/parameter_provenance.md` | Chỉ bổ sung bảng IEEE 2019 riêng; không viết lại bộ arXiv đã có |
| `README.md` | Bổ sung cách dùng hai profile và lệnh tái lập hình |
| `docs/ieee_2019_rotor_plan.md` | Ghi phạm vi triển khai và quyết định rounding policy |
| `docs/ieee_2019_rotor_verification/` | Source identity/hash, bản render Table I, text các trang nguồn, provenance JSON và kiểm chứng |
| `figures/ieee_2019/fig02_propulsion_power_ieee2019.*` | Hình mới, dữ liệu tính thực tế, caption và manifest |

Không sửa `configs/paper.yaml`, `configs/demo.yaml`, `propulsion.py`, convex
envelope, DP hoặc các producer cũ. Không tích hợp profile mới thành default
của nhiệm vụ QKD. Các file do lần render đầu của chính task này tạo ra được
giữ riêng dưới `ieee_2019_rotor_verification/initial_export/`; thư mục
`figures/ieee_2019/` chứa bản giao cuối.

## B. Xác minh nguồn

Đã trực tiếp tìm và đọc file:

`C:/Users/admin/Downloads/Energy_Minimization_for_Wireless_Communication_With_Rotary-Wing_UAV.pdf`.

Đây là bản journal IEEE TWC, vol.18, no.4, April2019, 17 trang, pp.2329–2345.
Trang đầu ghi DOI **10.1109/TWC.2019.2902559**. SHA256:

`b2c25b3e7cd92ab93c5e31fd824cbfade30d312029557e1a187184495ed81a57`.

Các mục đã đọc trong lượt này:

- Eq.(12), journal p.2332 / PDF p.4: ba thành phần power và tổng.
- Section V, journal p.2339 / PDF p.11: vmax=30 m/s.
- Table I, journal p.2342 / PDF p.14: toàn bộ tham số aircraft theo yêu cầu.
  Bảng là ảnh trong PDF nên đã render và kiểm tra trực quan.
- Eq.(64), cùng p.2342 / PDF p.14: định nghĩa P0/Pi và hovering power.

File [source_identity.json](ieee_2019_rotor_verification/source_identity.json)
gắn cả hash PDF và hash profile đã đối chiếu. Exporter chỉ gắn `READY` khi
profile hiện tại và PDF khớp các snapshot đã kiểm. Thay W hoặc đổi chính sách
v0 mà giữ tên `ieee_2019` sẽ bị từ chối, không chỉ kiểm tra tên và PDF.

Không trộn hệ số rotor k=.1 với NLoS kappa=.2 trong phần RF. Không nhập
altitude100 m, bandwidth, RF power, qI hoặc qF của bài RF vào bài toán QKD.

## C. Kết quả tính số

Tính từ W=20 N, rho=1.225 kg/m³, A=.503 m², s=.05, Utip=120 m/s,
delta=.012, k=.1, với Utip=300*.4. Giữ A=.503 theo bảng, không tự thay bằng
pi*.4²=0.5026548245743669 m².

| Đại lượng | Giá trị tính được | Đơn vị / ý nghĩa |
|---|---:|---|
| P0 | 79.85628000000001 | W; delta*rho*s*A*Utip³/8 |
| Pi | 88.62793774108202 | W; (1+k)*W^(3/2)/sqrt(2*rho*A) |
| P_hover | 168.48421774108203 | W; P0+Pi |
| v0 dẫn xuất và dùng trong hình | 4.028542624594636 | m/s; sqrt(W/(2*rho*A)) |
| v0 Table I | 4.03 | m/s; giá trị nguồn đã làm tròn, lưu riêng |
| V_ME | 10.211691198388639 | m/s; min P(V) trong[0,30] |
| P(V_ME) | 125.99078026851394 | W |
| V_MR | 18.294480351062063 | m/s; min P(V)/V trong(0,30] |
| P(V_MR) | 161.50995694742937 | W; tọa độ marker trên power curve |
| P(V_MR)/V_MR | 8.828343513897792 | J/m; objective maximum-range |

Chính sách v0 của profile IEEE mới là **derived**, đúng yêu cầu tính từ tham
số gốc. Không giấu việc nó khác số4.03 đã làm tròn trong bảng; caption/profile/
manifest đều ghi cả hai. Profile arXiv cũ vẫn **table_value**, giữ v0=7.2.
Mọi trường `PropulsionParams` arXiv mới khớp `paper.yaml` với absolute tolerance
1e-10; default cũ không đổi.

Các số79.86/88.63/168.48 chỉ là cách làm tròn để trình bày. Không lấy
79.86+88.63=168.49 làm hovering power dẫn xuất mới, và không đổi các constant
demo đã lưu. Metadata lưu nhiều chữ số để replay, không hàm ý dự báo UAV thực
có độ chính xác vật lý tương ứng.

Tổng power dùng evaluator đã có. Induced component dùng biểu thức ổn định
`Pi/sqrt(hypot(1,a)+a)`, với a=V²/(2v0²), tránh phép trừ hai số gần nhau.
Các component cộng lại khớp tổng; induced giảm trên miền kiểm tra0–30 m/s.

### Tìm và kiểm tra ME/MR

Không điền sẵn hai vận tốc. Thuật toán quét20001 điểm (bước.0015 m/s), tìm mọi
cực tiểu cục bộ trên lưới, refine bằng SciPy bounded minimization trong các
bracket lân cận, đồng thời so sánh endpoint hợp lệ. MR loại V=0 vì P(V)/V phân
kỳ khi V tiến về0 trong mô hình này. Xatol=1e-10 m/s là thiết lập solver,
không phải chứng nhận sai số toàn miền.

Objective ME sau refine125.99078026851394 W, tốt hơn grid minimum
125.99078032387413 W tại10.212 m/s. Objective MR sau refine8.828343513897792
J/m, tốt hơn grid minimum8.828343521219857 J/m tại18.294 m/s. Các test kiểm
lại bằng lưới50001 điểm và stationarity; reviewer độc lập kiểm bằng100001
điểm. Đây là nghiệm số kiểm tra trên mô hình tham chiếu, không phải chứng nhận
global optimality cho trajectory, source shaping hoặc security của hệ QKD.

## D. Hình và lệnh tái lập

Hình mới có miền0–30 m/s, bốn curve, hovering/ME/MR markers, font serif, đường
nét phân biệt cả khi in grayscale, source ở caption/metadata. Xuất một cột
3.5 inch, PNG600dpi; PDF giữ vector text/curve/marker.

- [PDF](../figures/ieee_2019/fig02_propulsion_power_ieee2019.pdf)
- [PNG](../figures/ieee_2019/fig02_propulsion_power_ieee2019.png)
- [CSV](../figures/ieee_2019/fig02_propulsion_power_ieee2019.csv)
- [Manifest](../figures/ieee_2019/fig02_propulsion_power_ieee2019.json)
- [English caption](../figures/ieee_2019/fig02_propulsion_power_ieee2019.caption.txt)

Từ thư mục `uav_cvqkd_optimization/`:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -m uav_qkd.rotor_power_figure --profile configs/rotor/ieee_2019.yaml --output figures/ieee_2019_reproduction --column single
```

Output gốc được tạo bằng cùng lệnh với `--output figures/ieee_2019`. Dùng một
thư mục mới vì exporter từ chối nonempty output, không ghi đè lịch sử. Có hỗ
trợ `--column double` cho7.16 inch. Chỉnh profile cần đối chiếu lại snapshot
nguồn trước khi gắn nhãn verified; không có tùy chọn bỏ qua hash check để tạo
READY giả.

Tên Figure02 này theo yêu cầu mới về rotor. Nó **không thay** mục
`fig02_cloud_maps` của catalog trước; `figures/paper/status.json` và chín
manifest BLOCKED vẫn nguyên trạng. Tác giả có thể quyết định numbering khi
tích hợp manuscript, không cần xóa hay đổi nhãn các hình cũ.

## E. Tests và review

Trước thay đổi, suite cũ chạy **59 passed**. Sau triển khai và sửa finding,
toàn suite chạy **70 passed in 5.17s**: 59 cũ và11 test/case mới. Lệnh:

```powershell
python -X utf8 -m pytest -q
```

Các assertions DP, energy model, provenance và figure gates cũ không bị sửa
hoặc làm yếu. Test mới kiểm coefficients/hover/v0, component sum,
nonnegative/finite, monotonic induced, stationarity/dense-grid speeds, version
separation, high-speed arithmetic stress, PNG dimensions/DPI, overwrite guard,
và từ chối profile đã đổi weight/policy nhưng vẫn đòi nhãn IEEE.

Review độc lập lưu ở
[ieee_2019_rotor_independent_review.md](ieee_2019_rotor_independent_review.md).
Finding về kiểm nguồn chỉ dựa vào PDF đã được tái hiện bằng hai test thất bại
và sửa bằng ràng buộc source identity + profile snapshot + v0 policy. Suite
70 test sau sửa đã qua. Không có finding quan trọng còn mở. Review số không
thay thế kiểm nguồn trực tiếp hoặc chứng nhận mô hình vật lý.

## F. Giới hạn khoa học

Đây là bộ tham số **một UAV tham chiếu** trong IEEE2019 và đường cong tính
theo steady-level-flight model, bỏ acceleration/transient theo mô hình gốc.
Không phải measurement của UAV cụ thể trong liên kết HAP–UAV và không chứng
minh mọi UAV đều có cùng power, density hoặc tốc độ tối ưu.

Không nhập thêm fs, valid-signal fraction, m0, epsilon, Emax, q0, horizontal
HAP coordinates, cloud realization/layer/thickness/threshold hoặc prior lambda.
Những input này vẫn thiếu cho nhiệm vụ paper. `paper-mode: NOT_RUN`, trạng
thái lookup `INSUFFICIENT_EVIDENCE` và các giới hạn source/security trước đó
không được nâng bằng một hình power đã tính đúng.

## G. An toàn repository

Default `paper.yaml` vẫn dùng bộ arXiv v1; `demo.yaml` không đổi; không có mô
phỏng lịch sử bị xóa/ghi đè. `propulsion.py` và các producer cũ giữ nguyên để
không làm mất source-hash bindings của dữ liệu cũ. Hai profile mới không chứa
tham số RF/QKD/cloud ngoài phạm vi rotor.

Provenance markdown được cập nhật theo yêu cầu nên hash tài liệu thay đổi.
Bản bytes trước khi bổ sung được giữ tại
`ieee_2019_rotor_verification/parameter_provenance_before.md` với hash
8174ab7f339717903a020563ebcb8560d2ab4dace6d3b92b687d777f0880b7ee.
Các manifest lịch sử không bị viết lại để che sự thay đổi tài liệu; chúng tiếp
tục mô tả snapshot nguồn cũ. Không sửa trạng thái/lifecycle, không chạy lại
paper-mode, trajectory optimization hay source/CV-QKD jobs, không commit/push.
