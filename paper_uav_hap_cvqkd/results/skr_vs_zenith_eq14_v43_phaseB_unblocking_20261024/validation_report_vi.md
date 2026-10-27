# Phase B unblocking — phục hồi evidence và chẩn đoán Uniform

**PHASE B UNBLOCKING RESULT: BLOCKED. `PHASE_B_STRICT_READY = FALSE`.**

## 1. Trạng thái đầu vào và phạm vi

Nguồn hiện hành là package readiness đã seal trong
`../skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/`. Read-only verifier của
package đó được chạy lại và PASS: 49 artifacts, 9.295 protected files, pilot và
sweep chưa chạy. Các 10 kiểm tra runner cũ được xác minh bằng hash, không trình
bày thành 10 tests mới chạy trong lượt này.

Giữ nguyên v43/direct Eq. (14), homodyne discrete MI, Holevo, RR/beta=0.95,
`VA=Vmod=2*nbar`, `nu_repo=42.5*nu_raw`, channel moments [0,1] và deficit metadata.
Không đổi vật lý, tolerance, Z, nguồn, catalogs hoặc production. Namespace mới
chỉ phục vụ pháp chứng và chẩn đoán, không cập nhật gate đã seal của lượt trước.

## 2. Phục hồi evidence lịch sử

Tái dùng index 1.956 artifact/138 precision candidates đã kiểm tra trước; package
cũ và các payload được xác minh hash. Mở rộng sang:

- **2.826 Git blob** văn bản ở mọi revision reachable của results, khoảng
  829.979.370 bytes; bao gồm cả bản cũ và file đã thay đổi/xóa.
- **7 ZIP archive**, kiểm tra text members tại chỗ, không extract đè file cũ.
- **3 bản ghi execution JSONL** khớp source/array digest; trong đó kiểm tra
  **133 raw tool-output records** có precision/worker/target fields ở lượt cuối
  (lượt tìm đầu có 126; execution log tiếp tục được ghi trong khi làm việc).
- Tìm cả 73 ensemble hashes và PMF/amplitude digests tương ứng; không chỉ tìm
  tên thư mục receipt. Không đọc dataset final-test/held-out hay chạy evaluator cũ.

`expanded_evidence_scan.json`, `git_blob_inventory.json`,
`execution_record_search.json`, `recovered_records/` lưu phạm vi, hash, origin,
candidate checks và bản snapshot. Source-generation logs/checkpoints/metadata
liên quan đã có trong index cũ được dẫn riêng cho từng nguồn trong CSV mới.

Tìm được hai Git blob chứa **cùng evidence Uniform VA=2** đã được chấp nhận:
`ba9b3dfe4ada799ef50e525aed2d5fcb8db3c87e` và
`c8558bed49cd0e55deb5b7b18116e84489a08399`. Chúng khớp exact PMF và amplitude
digests, có full-support rows 1050/1250/1450 và qua checker cũ. Các blob immutable
củng cố truy xuất, **không tạo thêm nguồn được nâng hạng**.

Bốn candidate Git khác chỉ lưu input hashes, C,w, route/rank metadata; không có
precision ladder rows để kiểm tra. Minimum eigenvalue được float hóa thành 0
ở những record này cũng không phải spectrum arbitrary precision. Chúng không
được nâng hạng. Không dùng cùng hash, route FRESH, mã guard hoặc C,w lặp lại để
thay thế accuracy evidence. Không mở rộng nghĩa alternative evidence.

Giới hạn: JSONL/log chứa JSON hoàn chỉnh được giải mã; text không parse được,
truncated terminal output hoặc báo cáo văn xuôi chỉ là metadata, không phải
receipt. Whole execution log có thể tiếp tục được ghi; các record cần dùng đã
được snapshot và hash trong namespace này. Evidence số được chấp nhận mới ở đây
chỉ là bản Git của nguồn đã verified trước, không dựa vào diễn giải hội thoại.

## 3. Trạng thái đầy đủ 81 nguồn

**Số nguồn nâng hạng: 0.**

| Loại | Trước | Sau |
|---|---:|---:|
| VERIFIED_EXACT | 6 | 6 |
| VERIFIED_BY_ALTERNATIVE_EVIDENCE | 1 | 1 |
| INSUFFICIENT_EVIDENCE | 74 | 74 |
| INVALID | 0 | 0 |

Trong 80 nguồn đã có payload, 7 nguồn đủ convergence evidence; **73** vẫn thiếu
(26 Uniform, 47 MB). Thêm **một Uniform chưa có payload** tạo tổng 74 insufficient.
Không tìm thấy xung đột source identity. Missing receipts không chứng minh C,w sai.

`pilot_source_evidence.csv` có đúng 81 hàng, giữ nguyên VA/nu hex, ensemble/payload
hash, C,w, location; thêm nu_repo/hex, identity, source-artifact namespace, job/run
ID nếu có, log/metadata/diagnostic references, source-status changes và yêu cầu còn
thiếu. Không suy diễn original job ID từ tên một bản cache đã sao chép.

## 4. Fixed MB

Fixed MB giữ nguyên VA `1.6249995399703647`, nu_raw `0.25`, nu_repo `10.625`:

```text
ensemble_hash = 01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754
VA_hex = 0x1.9ffff84830112p+0
C = 1.2135302410613147
w = 2.856493276891121e-10
source_path = results/exact_mb_test2/exact_source_cache/9ebda470cd3cb1050a9f15a5b943141c82dafe113226c5f1e62b5eaccf308463.json
source_sha256 = f50b7253bc19791fa5e652832fdcb903fc198094e3cc871733a5855977a95018
```

Identity được xác minh; **INSUFFICIENT_EVIDENCE** về hội tụ. Có 551 supporting
records trong index trước, nhưng chưa tìm được full precision history được gắn
với payload hoặc exact arrays. Original computation job ID chưa được ghi nhận.
Giữ C,w hiện có và benchmark ensemble, không thay bằng nguồn khác.

## 5. Timeout Uniform và kiểm tra nhẹ

Chi tiết trong `uniform_timeout_diagnosis.md`. Verified direct cause:
`source_uniform_diagonal.fallback` chờ child `diagonal_solve_worker.py` và vượt
timeout 3.600 s. Không có payload/receipt hay row checkpoint từ attempt đó.

Đã phục hồi **9 snapshot CPU**, cùng worker PID 33676. User CPU tăng từ
535.4375 lên 2380.421875 s. Worker tiếp tục hoạt động; chưa có chứng cứ numerical
convergence hay mức precision đang chạy. Không có stage profile/peak memory;
**root cause sâu bên trong worker vẫn chưa xác định**.

Code xác nhận ba row precision được tính lại tuần tự, bốn eigensystem 64×64 mỗi
row, nhiều matrix operations, không checkpoint; chỉ emit JSON sau toàn bộ ladder.
Diagonal solve đã được tối ưu trước đó, không phải LU nhiều RHS cũ.

Kiểm tra nhẹ: đúng hash Uniform và năng lượng; bốn eigvalsh float64 cho gate
không đủ điều kiện fast path. Đây không phải AP source calculation. Một assert
parser snapshot CPU ban đầu không nhận hàng không có trailing whitespace; đã
sửa parser, chạy lại thành công, không đổi numerical criterion. Có hai lượt
float64 gate, zero C,w evaluations. Một identity check ma trận tổng hợp 3×3,
80 digits xác nhận diagonal solve và từ chối input không chéo. Không dùng dữ
liệu tổng hợp làm evidence hội tụ của source.

## 6. Cơ hội tăng tốc và đường khôi phục

Ưu tiên instrumentation + checkpoint từng row trước. Sau profiling mới xét
hoist invariant matrices trong cùng precision, row/column scaling thay dense
diagonal multiplication hoặc checkpoint sector. Chưa triển khai tối ưu vào
scientific kernel, chưa đo speedup. Không dùng eigensystem từ VA khác, không bỏ
precision, không đổi backend trái Application Control.

`uniform_recovery_plan.md` có exact input, lệnh tham chiếu hiện chạy được trong
một namespace tương lai, giới hạn lệnh đó, đặc tả checkpoint/resume, convergence
criteria, artifacts và xử lý timeout. Wrapper checkpoint chưa có và chưa được
kiểm chứng; không giả vờ đã có runner recovery. Bước tiếp theo an toàn là chuẩn
bị/test wrapper bằng stub rồi mới duyệt một bounded attempt riêng. Không có
attempt mới nào được thực thi trong lượt này.

## 7. Frozen spec và preservation

Spec riêng vẫn có SHA-256
`4868392f68af9be5b52b684dac1a23d4242e4cf44a871d4e66944349aa874d21`;
frozen file hiện tại vẫn `df83ea63...78c15`, bản lịch sử vẫn `561fecc9...a2a7b1`.
Lịch sử Git và versioned experiment binding cũ được giữ nguyên, không bypass
hash check. Xem `artifact_integrity_report.md` và `verification.json` cho kết quả
kiểm tra cuối; không suy rộng thành production/security approval.

## 8. Hai nhóm blocker và quyết định

1. **73 nguồn đã có C,w thiếu bằng chứng hội tụ**, gồm Fixed MB. Cần phục hồi
   đúng per-ensemble precision evidence; metadata/guard code không đủ. Không tự
   tái tính toàn catalog hoặc đổi evidence policy.
2. **Uniform exact VA chưa có payload và receipt**, attempt trước timeout.
   Cần observability/checkpoint được kiểm tra và một bounded source attempt được
   duyệt riêng; sau đó xác minh nguồn bằng standard hiện tại.

`PHASE_B_STRICT_READY = FALSE`. Pilot runner PASS không thay thế hai dependency
nguồn. Chưa có đường diagnostic-pilot evidence yếu hơn được phê duyệt. Không chạy
pilot 9 góc, sweep 61 góc, optimizer hoặc exact-source recomputation đắt tiền.
Năm focused forensic tests mới PASS trong `focused_checks.json`; chúng kiểm tra
inventory, evidence và chẩn đoán, không thay thế convergence receipts còn thiếu.
Task chẩn đoán kết thúc tại báo cáo này.
