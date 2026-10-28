# Kiểm toán tối ưu toàn cục của quét góc zenith

Ngày 2026-10-21. **Stage 1 đã hoàn tất. Stage 2/3 chưa chạy vì cần duyệt miền
khảo sát số hữu hạn. Không tạo nguồn mới hoặc tính SKR mới.**

## Kết luận chính

Hai đường “Optimized” thực sự là **GLOBAL OPTIMUM OVER THE FINITE TESTED
CATALOG**, theo các giá trị raw SKR của evaluator đã lưu. Kiểm tra độc lập
toàn bộ 6.758 hàng xác nhận đúng argmax ở cả 31 góc × 2 họ nguồn, 0 sai lệch.
Đây không phải cực đại toàn cục trên miền tham số liên tục.

Catalog đúng là **36 Uniform + 182 MB = 218**, không thay bằng catalog mobility
233 nguồn. Uniform có VA∈[0.02,12]; MB có VA∈[0.025,8], nu_raw∈[0.05,0.8].
MB chứa 33 giá trị nu và 57 VA nhưng chỉ 182/1881 tổ hợp (9,676%); đó là tập
điểm không đều. Danh sách đầy đủ, giá trị hex và spacing nằm trong CSV đi kèm.

MB chọn (nu_raw,VA)=(0.125,8) tại mọi góc 24°–60°; Uniform chọn VA=12 tại
42°–60°. Đây là trần catalog, không phải trần năng lượng vật lý đang được áp
dụng. Tham số repo bằng **42.5*nu_raw**; 0.125 raw tương ứng 5.3125 repo.

## Vì sao phải dừng trước pilot

Loader lịch sử đặt min/max VA, average-energy budget và peak-photon cap bằng
None. Bản thảo không cung cấp giới hạn vật lý thay thế đủ rõ. Tập nguồn hình
thức có nu>=0 và VA>0, nhưng không được tự coi miền VA không bị chặn là miền
tối ưu đã được phê duyệt. Re-freeze cho thiết kế Dr=0.55 m là thí nghiệm khác,
không được nhập sang cấu hình 233 urad/Dr=0.08 m này.

Yêu cầu hiện tại quy định: nếu không xác lập được miền liên tục từ ràng buộc
có sẵn, dừng trước khi tạo nguồn và xin duyệt miền khám phá hữu hạn. Vì vậy,
chưa có “new best”, phần trăm cải thiện mới hoặc khoảng cách đến optimum thật.
N/A trong bảng dưới không có nghĩa gain=0.

Đề xuất cụ thể: Uniform VA∈[0.02,48] SNU; MB nu_raw∈[0,1.6], VA∈[0.025,32]
SNU, chỉ là **miền khảo sát số**. Batch đầu tối đa sáu nguồn: Uniform VA=16,
24,48; MB (0.08,16),(0.125,16),(0.2,16), dùng lại cache xác thực trước.
Tối đa 36 lượt rate ở sáu góc 24°,30°,40°,48°,52°,60°. Không quét toàn bộ
rectangle hoặc tự mở rộng. Timeout worker 3600 s/nguồn, tối đa 6 giờ
source-worker cho sáu nguồn mới; dừng sớm khi lỗi precision/provenance.
Đây là batch dò biên ban đầu, chưa là khảo sát multiregion toàn diện hoặc
chứng chỉ tối ưu. Chi tiết ở [parameter_domain_audit.md](parameter_domain_audit.md)
và [proposed_pilot.json](proposed_pilot.json).

## Bảng so sánh tại các góc ưu tiên

| Zenith | Scheme | Old VA | Old nu | New VA | New nu | Old SKR (bits/use) | New SKR | Gain (%) | Optimality status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24° | Uniform | 0.02 | 0 | N/A | N/A | -5.257818732186e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 24° | MB | 8 | 0.125 | N/A | N/A | 1.462124116665e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 30° | Uniform | 0.0475 | 0 | N/A | N/A | -4.850670994797e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 30° | MB | 8 | 0.125 | N/A | N/A | 1.395162885713e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 40° | Uniform | 0.13 | 0 | N/A | N/A | -3.842293543266e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 40° | MB | 8 | 0.125 | N/A | N/A | 3.024230286051e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 48° | Uniform | 12 | 0 | N/A | N/A | 8.293807622100e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 48° | MB | 8 | 0.125 | N/A | N/A | 3.421451103003e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 52° | Uniform | 12 | 0 | N/A | N/A | 1.066259517273e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 52° | MB | 8 | 0.125 | N/A | N/A | 3.221968468174e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 60° | Uniform | 12 | 0 | N/A | N/A | 3.871924701332e-05 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |
| 60° | MB | 8 | 0.125 | N/A | N/A | 2.069729731056e-04 | N/A | N/A | Catalog-global; pilot chờ duyệt miền |

Uniform ở 24°,30°,40° có baseline âm, vì vậy ngay cả khi có nguồn mới cũng
không tính phần trăm bằng mẫu số này; chỉ báo chênh lệch tuyệt đối và chuyển
trạng thái dấu. Với baseline dương, phần trăm chỉ tính sau khi có K_new exact.

## Bằng chứng định lượng tại biên, chỉ dùng điểm cũ

| Zenith | Scheme | VA cuối | Delta K giữa hai điểm cũ (bits/use) | Secant (bits/use/SNU) |
| --- | --- | --- | --- | --- |
| 24° | Uniform | 8→12 | -3.922811421e-05 | -9.807028554e-06 |
| 24° | MB | 6.5→8 | +8.891826233e-06 | +5.927884155e-06 |
| 30° | Uniform | 8→12 | +1.961315622e-05 | +4.903289056e-06 |
| 30° | MB | 6.5→8 | +2.957704205e-05 | +1.971802803e-05 |
| 40° | Uniform | 8→12 | +9.960524795e-05 | +2.490131199e-05 |
| 40° | MB | 6.5→8 | +5.626867729e-05 | +3.751245152e-05 |
| 48° | Uniform | 8→12 | +1.242817965e-04 | +3.107044911e-05 |
| 48° | MB | 6.5→8 | +6.212042590e-05 | +4.141361727e-05 |
| 52° | Uniform | 8→12 | +1.187580110e-04 | +2.968950274e-05 |
| 52° | MB | 6.5→8 | +5.822111880e-05 | +3.881407920e-05 |
| 60° | Uniform | 8→12 | +7.308351431e-05 | +1.827087858e-05 |
| 60° | MB | 6.5→8 | +3.747016250e-05 | +2.498010834e-05 |

Secant của Uniform dùng hai VA lớn nhất 8 và 12, kể cả khi winner nằm ở VA
nhỏ. Secant MB dùng hai VA cuối trên slice nu của winner từng góc. Vì thế,
không được hiểu các con số này là đạo hàm tại biên, mức tăng vượt catalog,
hoặc một dự đoán cho VA=16. Tại 30°, Uniform dù tăng lại ở đuôi vẫn kém rõ
rệt winner VA=0.0475.

Ở 48°, MB tăng +6.212042590e-5 bits/use từ VA=6.5 lên 8; Uniform tăng
+1.242817965e-4 từ VA=8 lên 12. Tại toàn bộ góc 24°–60°, đuôi MB ở nu=0.125
còn tăng về VA=8. Đuôi Uniform ở 42°–60° cũng tăng về VA=12. Đây là lý do
hợp lý để xin pilot; chưa chứng minh tăng tiếp sau trần sẽ có lợi.

## Trả lời mười câu hỏi

1. **Catalog cũ có tối ưu thật không?** Có, cho tập hữu hạn và giá trị số đã
   lưu: 62/62 argmax khớp. Không chỉ là một nghiệm tối ưu cục bộ.
2. **Có chạm biên không?** Có: MB VA=8 tại 24°–60°; Uniform VA=12 tại
   42°–60°. Nu=0.125 nằm giữa min/max nu nhưng sampling không đều, không
   chứng minh stationary point liên tục.
3. **Có nguồn tốt hơn ngoài biên chưa?** Chưa đánh giá nên chưa biết. Không
   thay chữ “có khả năng” bằng một số phần trăm không có dữ liệu.
4. **Có nhiều cực đại cục bộ không?** Chưa chứng minh trên miền liên tục.
   Uniform có sampled-neighborhood maximum tại VA=0.0475 ở 30°; tại
   48°/52°/60° có đỉnh mẫu nhỏ ở VA=0.2, sau đó giảm rồi tăng về trần12.
   Không được giả định landscape đơn đỉnh chỉ từ catalog này. MB scatter
   thưa không đủ loại trừ các basin khác.
5. **Tham số exact tốt nhất tìm thấy?** Chỉ các tham số lịch sử trong bảng;
   chưa có nguồn exact mới. Đỉnh catalog Uniform là VA=12 ở 52°;
   MB là (0.125,8) ở 48°.
6. **Mỗi góc cải thiện bao nhiêu phần trăm?** N/A: chưa chạy refinement.
7. **Mức cải thiện mới lớn nhất?** Chưa xác định, không báo 0%.
8. **Góc đạt đỉnh có đổi không?** Chưa có bằng chứng để thay đổi. Đỉnh cũ
   vẫn là Uniform52°, fixedMB48°, optimizedMB48° trên lưới 31 góc. Không
   tuyên bố optimum zenith liên tục hoặc optimum mới từ sáu góc chưa tính.
9. **Chứng nhận global continuous được không?** Không, trong audit hiện tại.
   **GLOBAL OPTIMALITY GAP: NOT CERTIFIED**.
10. **Thiếu gì?** Miền vật lý được định nghĩa/miền số được duyệt; exact
    sources mới; kiểm tra biên/basin độc lập; và upper bounds có chứng minh
    trên toàn miền, kể cả tail nếu không bị chặn. Multistart hoặc cùng giá
    trị sau refinement không tự cung cấp chứng chỉ đó.

Đỉnh cũ được xác nhận: Uniform 1.06625951727330e-4 tại52°; fixedMB
2.41357175677000e-4 tại48°; optimizedMB 3.42145110300252e-4 tại48°.

## Hình và artifact

[Danh mục hình](figure_manifest.csv) gồm 8 cặp PDF vector/PNG350dpi: coverage
catalog MB, Uniform/MB theo góc, source parameters theo góc, Uniform K–VA,
MB K–VA, MB K–nu và scatter landscape MB48°. Chỉ marker tại điểm exact đã
lưu; đường nối không phải đánh giá ở điểm trung gian. Không tạo hình gain
giả bằng0 hoặc vẽ đường nối các góc refinement chưa chạy. Xem
[English captions](figure_captions_en.md).

- [Audit 62 argmax](original_catalog_audit.csv),
  [218 nguồn đầy đủ](original_catalog_candidates.csv),
  [bằng chứng biên](boundary_audit.csv), [spacing](parameter_spacing.csv).
- [Bảng new/old N/A](optimality_improvement.csv),
  [new exact candidates, header only](new_exact_candidates.csv),
  [manifest nguồn tái sử dụng](source_manifest.csv).
- [Báo cáo kiểm tra](validation_report.md),
  [machine-readable checks](validation/audit_checks.json).

## Kiểm tra và giới hạn khoa học

Audit producer đạt 42311 kiểm tra, gồm source hash/PMF/geometry/energy,
42+64 receipt members và mọi hàng rate/noise/GH/covariance/argmax. 106 receipt
members có 93 raw-hash match và 13 CRLF-only match; không gán raw-hash PASS cho
13 tệp văn bản này. Hash chung của từng ensemble được dựng lại từ NPZ binary64.
Khoảng cách winner–runner-up nhỏ nhất là 1.003085838912e-09
bits/use; sai khác GH16/32/64 lớn nhất 6.062858548539e-16.
Đây là kiểm tra độ ổn định số lưu, không phải chứng minh cận lỗi toàn miền.

Không chạy lại GH, entropy, C,w, AP, channel, source optimization hoặc solver
trajectory. C,w được xác thực bằng payload/provenance; không có kiểm chứng AP
độc lập mới. K và fading noise chỉ được tái dựng bằng số đã lưu, residual tối
đa 9.758e-19 và 9.758e-19.

Giữ cấu hình lịch sử, VA=2*nbar, ideal detector và mismatch MI2D/Holevo
homodyne. Không xác nhận bảo mật CV-QKD vật lý. Giữ frozen-hash conflict,
ObjectiveC USER_STOPPED, **UNVALIDATED_SECURITY_MODEL** và
**NOT_READY_FOR_PUBLICATION_SCALE_RUNS**. Không sửa production/cache/config,
không commit/push. Stage2 chỉ được tiếp tục sau khi miền/budget trên được duyệt.
