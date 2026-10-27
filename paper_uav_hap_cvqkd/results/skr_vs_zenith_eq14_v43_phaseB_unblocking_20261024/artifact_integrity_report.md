# Artifact integrity — Phase B unblocking

## Git và dirty state lúc bắt đầu

Repository `C:/Users/HP/Documents/GitHub/2024_dvcvqkd`, branch `feat/image`, HEAD
`9cc25e9f8320542b61adaec05c755e98fe93cdc2`.
`startup_manifest.json` lưu Git status nguyên trạng, hashes của **9.346 file**
được bảo vệ và các ngoại lệ ledger; `startup_git_diff.patch` giữ diff ban đầu.
Đã có năm ledger modified và nhiều package/script untracked trước task. Không
commit, push, reset hay sửa các pre-existing scientific artifacts đó.

## Kiểm tra đã thực hiện

- Read-only verifier của package Phase B readiness cũ: PASS, 49 artifacts và
  9.295 protected files; không chạy scientific evaluator.
- `historical_preservation_check.json`: **CURRENTLY_VERIFIED_PASS**, 9.346/9.346
  hash khớp, không có file bị thay đổi. Phạm vi bổ sung toàn bộ package readiness
  cũ (gồm manifest và verification) và repository instructions liên quan.
- Payloads của 80 nguồn hiện có được xác minh hash trong forensic inventory và
  kiểm tra lại trong focused test. CSV mới giữ nguyên C,w và identity của cả 81
  hàng; Uniform thiếu vẫn để trống C,w và payload hash.
- `focused_checks.json`, `test_unblocking.log`: **5/5 tests PASS** mới cho
  inventory/nu_repo, không nâng hạng thiếu căn cứ, raw-tool decoder, CPU activity
  khác hội tụ và immutable Git evidence. Không gọi C,w kernel hoặc SKR.
- `uniform_diagnostic_checks.json`: PASS cho kiểm tra float64 gate và synthetic
  3×3 diagonal solve; không phải source convergence receipt. Execution history
  giữ cả lỗi parser snapshot ban đầu và sửa lỗi; không đổi scientific tolerance.
- Hai recovered precision artifacts là immutable Git blobs của Uniform VA=2 đã
  được chấp nhận. `recovered_records/` giữ snapshot theo SHA-256; không ghi đè
  nguyên bản trong Git hoặc results lịch sử.

## Frozen references

| Artifact giữ nguyên | SHA-256 |
|---|---|
| `docs/FINAL_MODEL_SPEC.md` hiện tại | `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15` |
| Snapshot frozen lịch sử trong readiness package | `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1` |
| `experiment_spec_v1.json` của readiness package | `4868392f68af9be5b52b684dac1a23d4242e4cf44a871d4e66944349aa874d21` |
| Canonical manuscript PDF | `f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b` |

Truy nguyên sai khác frozen-spec và binding versioned experiment vẫn có hiệu
lực; không overwrite spec và không tắt hash check. Không nâng phạm vi cho mô hình
production hoặc publication/security.

## Delta được phép và kiểm tra cuối

Chỉ thêm namespace chẩn đoán mới và cập nhật EVID-0224/DEC-0207 cùng current state,
next action, handoff. Bốn ledger append giữ toàn bộ nội dung pre-existing; handoff
được thay theo yêu cầu AGENTS, bản cũ lưu trong `startup_ledgers/`.

`artifact_manifest.json` niêm phong file mới; `verification.json` ghi kết quả
read-only verifier cuối, kiểm tra preservation của ledger, Python syntax và
`git diff --check`. Xem các receipt đó để phân biệt PASS về integrity với
**strict readiness FALSE**. Không dùng integrity PASS làm source convergence PASS.

Kiểm tra lại từ project root:

```powershell
.venv/Scripts/python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_phaseB_unblocking_20261024/verify.py
```

Không sửa production/security functional, manuscript, cache/catalog nguồn cũ,
frozen specifications hoặc numerical conventions. Không có expensive source
recomputation, pilot, sweep61, training/test/held-out access, baseline/threshold
approval, hay ObjectiveC restart. Giữ `UNVALIDATED_SECURITY_MODEL` và
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
