# Correction proposal v1 — PROPOSAL_NOT_ADOPTED

Ngày 23/10/2026. Phạm vi: đề xuất sửa tối thiểu sau audit; không thay production/frozen model hoặc giấy phép security. Target v43(2) chưa tìm thấy; căn cứ tạm thời là bản43 hash f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b và công thức task.

## P0 — Ràng buộc nguồn chuẩn trước khi sửa

Nhận đúng đường dẫn PDF v43(2), lưu bản sao/hash và đối chiếu Eq1–21, defaults, citations. Nếu tác giả chủ động chỉ định bản43 hiện có là canonical, ghi rõ quyết định và hash, không đổi tên file để giả sử nội dung trùng. Giữ historical frozen spec nguyên byte; registry mới phải phân biệt authority được chỉ định với status validated.

## P1 — Sửa notation nhất quán

- Eq2: một shaping parameter trong cả numerator/denominator; k centered. Ghi conversion unit-RMSν=42,5νraw và physicalν=νraw/Δ².
- Với vacuum1/X=a+a†, sửa Vmod=2n̄ và giữ coherent mean2Reα. Nếu chọn convention X/2 phải viết lại vacuum/CCR/Γ/entropy reference đồng bộ; đây không phải chỉ sửa nhãn.
- Eq12: y∈R, mean2√TReα, variance1+N. Dùng discrete-input MI; không dùng capacity thay thế.
- Eq20: ghi extensionηξ(0)=ξdet, đơn vị/noise location và outage handling. Không thêmηdet độc lập.

Các mục này cho phép giữ source catalog **khi actual p,α không đổi**. Không tính source mới cho lỗi notation.

## P2 — Giải quyết mâu thuẫn kênh, không lựa chọn theo dấu SKR

Giữ original Eq10 [0,1] làm reproduction fail-closed; không “repair” trong evaluator cùng tên.

Đối vớiρ≠0, cần chọn rõ: dùng exact Rice pushforward/numerical integral, hoặc giữ Eq10 như approximation có miền sai số công bố. Đặtρ=0 là giới hạn phạm vi, không là chứng minh công thức tổng quát.

Tích independent lognormal amplitude có tailη>1 ở mọi variance dương. Không thể vừa giữ toàn bộ luật tích, vừa giới hạn[0,1], vừa có mass1 mà không thay luật. Các hướng cần tác giả định nghĩa riêng:

1. Conditional active: f_corr=P0δ0+P1g1(0,1]/Factive(1). Đây là correction ngắn về công thức nhưng thêm điều kiện thống kê; không tự chứng minh truyền công suất và không tương đương original.
2. Luật bounded xuất phát từ aperture/field energy chuẩn hóa, kèm turbulence closure hiệu chuẩn. B/C hiện tại là **candidate diagnostic**, chưa có calibration; không tự promote.
3. Luật truncation/clip/erasure khác phải công bố atom/moment và ý nghĩa vật lý.

Không chọn một hướng mặc định trong proposal này. Chưa có correction được adoption, và không đặt mục tiêu ép positiveK.

## P3 — Đường evaluator tách version/protocol

Sau khi P0–P2 được giải quyết, một entrypoint task-specific phải:

1. Authenticate actual source p,α,C,w và full-support route.
2. Xác lập law/support/atom bằng version/hash, reject mass/physicality failure; không fallback sang bounded.
3. Tính ba moment và T=mh²,N=(m1−T)VA+ξchm1+ξdetM0, khôngηdet; truyền cùng T,N cho mọi nhánh.
4. Discrete real1D Gaussian effective MI; pooled-mixture chỉ ở diagnostic có nhãn riêng.
5. Γhomodyne, ν3=√[a(a−Z²/b)], uncertainty/entropy gates. Chọn literal physical Zminus hay conservative full interval bằng policy riêng; không gọi grid max là rigorous global certificate.
6. Giữ rawK, null cho blocked, provenance point-by-point ở plots. Recompute geometry/optics khi đổi L/ζ.

Pure helpers hiện có đủ minh họa fixed diagnostic; không cần viết framework/optimizer mới trong audit. Production heterodyne callers/tests/config cũ tiếp tục thuộc model cũ.

## P4 — Sai khác optical implementation

Nếu v43(2) xác nhận ν dùngweff, đề xuất sửa đúng đối số tại manuscript_pointing_parameters và kiểm tra caller/fixture tương ứng; audit chưa sửa. Phải công bố HV/Gd closure, lựa chọn v=rawRytov hay aperture averaged, hình học/FOV definitions. Không tắt aperture averaging âm thầm trong production để khớp một số.

## Điều kiện chưa được đáp ứng

Đúng targetPDF; author corrections; physical channel calibration; security-theorem binding; lifecycle prerequisites. Approval model/frozen/security/training/test/publication không được suy từ việc thông qua báo cáo audit hoặc proposal này.
