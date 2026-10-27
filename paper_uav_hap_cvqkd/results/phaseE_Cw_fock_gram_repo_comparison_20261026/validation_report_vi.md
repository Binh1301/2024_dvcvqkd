# PHASE E C,w COMPARISON: INCONCLUSIVE

**DIAGNOSTIC_ONLY; PHASE_B_STRICT_READY = FALSE.** Đã chạy các phương pháp
độc lập và thu được số thực tế. C,w trong các kiểm tra đã hoàn tất khớp rất sát,
nhưng chưa chứng minh hội tụ đủ256 mode của hai nguồn chính trong ngân sách.
Không có bằng chứng về mismatch định nghĩa C,w từ các phép kiểm tra đã thực hiện.

## Bảng đối chiếu

Các delta dùng chính xác giá trị binary64 trong cache làm reference; kết quả
AP được giữ dạng decimal trước khi trừ, tránh mất khác biệt dưới một ulp.

| Source | Method | C | w | delta C vs repo | delta w vs repo | Numerical status |
|---|---|---|---|---|---|---|
| Winner_MB | Repository | 1.067911050328646 | 5.700303183579203e-10 | 0.0 | 0.0 | HISTORICAL_STORED_INSUFFICIENT_EVIDENCE |
| Winner_MB | Fock | 1.06791105032864589 | 5.70030318357920227e-10 | -8.46152e-17 | -3.35948e-26 | INCONCLUSIVE_RETAINED_SUPPORT |
| Winner_MB | Gram | 1.06791105032864589 | 5.70030318357920227e-10 | -8.46152e-17 | -3.35948e-26 | INCONCLUSIVE_RETAINED_SUPPORT |
| Fixed_MB | Repository | 1.2135302410613147 | 2.856493276891121e-10 | 0.0 | 0.0 | HISTORICAL_STORED_INSUFFICIENT_EVIDENCE |
| Fixed_MB | Fock | 1.21353024106131479 | 2.85649327689112083e-10 | 1.08379e-16 | -9.60536e-27 | INCONCLUSIVE_RETAINED_SUPPORT |
| Fixed_MB | Gram | 1.21353024106131479 | 2.85649327689112083e-10 | 1.08379e-16 | -9.60536e-27 | INCONCLUSIVE_RETAINED_SUPPORT |

## Trả lời các câu hỏi

1. **Repository tính gì?** Path tạo cache là weighted coherent-state Gram,
chia bốn sector C4. Nó tính cùng trace C và weighted variance của a_tau đã
chỉ định; không dùng channel/zenith. Backend Fock cũ tồn tại riêng, không phải
producer của hai cache này. Xem repository_Cw_audit.md với27 mục truy xuất
function, dòng mã, input, precision, kích thước, rank và cache/convergence.

2. **Có tương đương Sayat/Denys?** Có về đại số cho ensemble C4 này khi dùng
đủ support và precision: Eq20–22 của bản journal Sayat và định nghĩa MP/variance
của Denys đã được đối chiếu từ PDF. Điều này không chứng minh mọi cutoff hoặc
precision hữu hạn tương đương số. Không thay đổi v43, Eq14, MI hoặc Holevo.

3. **Fock và Gram độc lập có khớp?** Sáu sanity case khớp với full rank của
constellation nhỏ. Hai nguồn256-QAM cho observable C,w khớp rất sát giữa các
phép AP đã xong; xem pairwise_method_differences.csv. Các phép này chưa cùng
giải quyết đầy đủ256 mode, nên đây không phải chứng chỉ full-support.
Cả bốn giá trị C,w best-tested làm tròn về binary64 đều bằng đúng cache.
Delta A−B bằng0 trong CSV chỉ có nghĩa không phân biệt được ở50 chữ số đã lưu.

4. **w cỡ1e-10 có ổn định không?** Có ổn định thực nghiệm trong các mức AP/NF
đã kiểm tra, nhưng chưa có cận sai số toàn support. Float64 trực tiếp và
cutoff phổ tùy tiện không đủ; residual norm không tự khắc phục conditioning.

5. **Yếu tố nào gây chênh?** Fock quá ngắn (ví dụNF24), bỏ mode theo threshold,
eigendecomposition gần roundoff và cancellation đều thấy trong dữ liệu.
Không phát hiện khác biệt input ensemble/normalization. Đã ghi riêng trace,
norm, phổ, rank, backward residual, absolute và relative differences.

6. **Nguồn thắng đã được validated chưa?** Giá trị cache được hỗ trợ mạnh bởi
các cross-check observable độc lập đã hoàn tất, nhưng full-support convergence
vẫn INCONCLUSIVE. Giữ INSUFFICIENT_EVIDENCE và không tạo receipt lịch sử giả.

7. **Ảnh hưởng Eq14/SKR?** Chỉ dùng một context primary đã lưu, tại zenith nhỏ
nhất trong lưới; tính Z trực tiếp ở80/110digits. Điều kiện đánh giá lại
Holevo/SKR với hai moment reference đủ tin cậy chưa qua full-support gate,
nên không chạy alternative Holevo/SKR. MI và betaMI tái dùng vì ensemble và
channel giống hệt; SKR repository chỉ đọc cache. Không suy ra chắc chắn dấu
SKR thay thế từ sự gần nhau của Z, và không mở rộng sweep. Delta Z AP khoảng
−7.99985e-17. Nếu làm tròn các moment về binary64 như dữ liệu đang dùng,
đầu vào C,w trùng cache nên không có thay đổi đầu vào để đổi dấu SKR trong
evaluator xác định. Điều đó không chứng nhận dấu SKR của full-support reference
chưa được giải quyết; các trường alternative Holevo/SKR vẫn để trống.

| Method | Z Eq14 | Delta Z | Raw SKR | SKR status |
|---|---|---|---|---|
| Repository | 1.00964229243170303 | 0.0 | 0.0007959663284000662 | REUSED_STORED_NOT_RECOMPUTED |
| Fock | 1.00964229243170295 | -7.99985e-17 | — | NOT_RUN_UNRESOLVED_INDEPENDENT_FULL_SUPPORT |
| Gram | 1.00964229243170295 | -7.99985e-17 | — | NOT_RUN_UNRESOLVED_INDEPENDENT_FULL_SUPPORT |

8. **Bước tiếp theo an toàn?** Giữ cache và trạng thái evidence; lưu checkpoint
eigenspectrum theo sector/precision trước khi cấp ngân sách riêng cho một
nguồn thắng ở precision cao hơn260, có hai mức full-support liên tiếp.
Không mở rộng toàn catalog hoặc chạy lại Uniform bị thiếu.

9. **Số nguồn catalog bị sửa: ZERO.** Hai nguồn MB lịch sử chỉ được đọc làm
input/reference. Các source moment mới chỉ nằm trong namespace kiểm chứng,
không thay cache, production evaluator, manuscript hoặc historical results.

## Thực thi và giới hạn

66 job đã có receipt:63 hoàn tất,3 chạm giới hạn. Sáu sanity labels gồm4/16/64
Uniform/MB; MB4 trùng Uniform4 do năng lượng bằng nhau. Hai nguồn chính là
winner và Fixed MB; không tính thêm source catalog nào, không chạy Uniform256.
Ngân sách worker1200s, tối đa180s/job; Fixed Fock cuối chỉ còn khoảng9.17s.
Polling/termination có sai số thời gian nhỏ; tổng upper-bound đã ghi1200.122s.
Sau sửa launcher, RAM được đo ở tiến trình thực; các mẫu launcher trước đó
được ghi là không đo RAM thực. Không che limitation vận hành này. Ngoài66 job
định danh có một attempt Fock bị gián đoạn khi sửa monitor, sau đó resume một
lần; log gốc được giữ và thời gian đã được tính trong upper-bound ban đầu.
RAM thực đo được sau sửa có peak sampled khoảng146.94MiB, dưới cap1024MiB.
11 focused checks bổ sung (chỉ tối đa16 trạng thái/NF48) qua kiểm tra trong
khoảng0.034s, ngoài batch source jobs; không có thêm phép tính256-QAM.

| Job | Outcome | Runtime s | Assigned time cap s |
|---|---|---|---|
| 49_Winner_MB_B_NNone_d260 | INCONCLUSIVE_TIMEOUT | 180.125 | 180.000 |
| 63_Fixed_MB_B_NNone_d260 | INCONCLUSIVE_TIMEOUT | 180.094 | 180.000 |
| 65_Fixed_MB_A_N256_d260 | INCONCLUSIVE_TIMEOUT | 9.281 | 9.175 |

Tất cả giá trị thiếu để trống, không điền zero. Ba job không hoàn tất không
được coi là numerical pass. Không có Z search, clamp w/eigenvalue, nội suy,
source classification upgrade hoặc thay đổi điều kiện vật lý/bảo mật.
Các formula, dữ liệu đầu vào và tiến trình tái lập nằm trong ba script chính,
protocol.json, job_plan.json, job_receipts.json và inputs/.
Xem artifact_integrity_report.md và verification.json cho kiểm chứng cuối.
