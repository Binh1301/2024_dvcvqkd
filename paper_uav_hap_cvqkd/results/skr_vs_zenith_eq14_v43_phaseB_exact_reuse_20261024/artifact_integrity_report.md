# Integrity — exact-source reuse diagnostic

## Git và đầu vào

Branch `feat/image`, HEAD `9cc25e9f8320542b61adaec05c755e98fe93cdc2`.
`startup_manifest.json` ghi dirty state trước task, hashes của **9.388 file** và
năm ledger exceptions. `startup_git_diff.patch` cùng `startup_ledgers/` giữ các
pre-existing edits. Không reset, commit hoặc push.

Verifier read-only của unblocking package đã PASS tại đầu task: 40 artifacts,
9.346 protected files. Kiểm tra mới `historical_preservation_check.json` PASS:
**9.388/9.388 file không đổi**, gồm production, catalogs/source payloads, frozen
specs, canonical reference và toàn bộ các package Phase A/readiness/unblocking cũ.

## Identity và mathematical compatibility

- 238 exact payloads được kiểm tra settings, historical key, code hash hoặc
  alias LF/CRLF đã được phép, reconstructed ensemble hash, PMF, C4 và VA=2*nbar.
- 235 canonical identities sau ba duplicate aliases đã chứng minh; giữ đầy đủ
  raw paths/hashes. Không dedup bằng gần VA/nu hoặc gần C,w.
- 245 catalog/bảng nguồn, 59.439 bound rows đối chiếu không có conflict.
- 81 hàng pilot giữ nguyên evidence classification/C,w/VA/nu/source identity;
  80 có dữ liệu, Uniform còn thiếu để trống. Không có source job mới.
- C,w được kiểm tra ở dạng binary64 hex trong mọi record. Từng source dùng
  cùng C,w qua tất cả các góc; không source interpolation hoặc recomputation.

## Producer và numerical verification

`protocol.json` khóa physical protocol và code lúc chạy pilot diagnostic.
`execution_producers/` giữ đúng bytes code tại thời điểm ấy. Sau lỗi serialization,
chỉ hàm save JSON đổi sang clean helper đã có; numerical evaluator không đổi.
Formatter stdout được sửa cùng cách; snapshot runner đã thực thi vẫn khớp
protocol. Manifest kiểm tra riêng cả snapshot lẫn code đã sửa, không bỏ hash guard.
`available_catalog_protocol.json` khóa code cho phần catalog bổ sung; bản attempt
đầu và nguyên nhân lỗi giữ riêng. Không ghi đè historical producer nào.

- 5 focused reuse checks PASS; hai source regressions khớp canonical evaluator
  ở eta_f,xi_f,Z,MI,Holevo,K. Eq13/Eq14 là cùng function objects.
- 2 postprocessing checks PASS cho numeric CSV ranking và NumPy JSON counts.
- 1.908 unique candidate records qua kiểm tra GH64/128, Eq14/Holevo80/110digits.
- 36 independent adaptive-MI/covariance checks PASS; 27 từ pilot được tái dùng,
  9 check bổ sung. Không dùng chúng làm convergence evidence mới cho C,w.
- 720 pilot rows giữ nguyên số học; bổ sung 1.188 unique rows. Lần mở rộng lỗi
  postprocessing phải lặp lại 1.188 rate attempts; execution_history.json ghi
  riêng các lần thực thi, không trình bày tất cả là unique evaluations.

Kết quả và summary đều được kiểm tra từ saved data. Không rerun scientific
producer để sửa báo cáo/serialization. Năm focused tests ban đầu có import
errors đã được giữ log, sửa import path và chạy lại; không sửa numerical rule.

## Frozen references không đổi

| File | SHA-256 |
|---|---|
| Current FINAL_MODEL_SPEC.md | `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15` |
| Historical frozen snapshot | `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1` |
| Versioned v43 experiment spec | `4868392f68af9be5b52b684dac1a23d4242e4cf44a871d4e66944349aa874d21` |
| Canonical manuscript PDF | `f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b` |

Hash discrepancy vẫn được xử lý bằng provenance/version binding cũ, không tắt
guard hoặc sửa frozen spec. Quyền dùng historical insufficient payloads là quyền
diagnostic mới, không sửa acceptance của strict evaluator hay strict readiness.

## Seal và kiểm tra cuối

`artifact_manifest.json` niêm phong file mới; `verification.json` ghi kết quả
`verify.py`, source-value invariance, preserved pilot values, old-file hashes,
record arithmetic, direct Eq14 check và `git diff --check`. Four ledger sections
chỉ append/prepend, nội dung cũ giữ nguyên; handoff cũ đã snapshot theo AGENTS.

```powershell
.venv/Scripts/python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/verify.py
```

Các kiểm tra integrity PASS không đổi evidence class của nguồn thiếu receipt.
Strict Phase B vẫn FALSE. Không sửa manuscript, production/security functional,
source caches hoặc source definitions; không training/test/held-out/publication,
baseline/threshold promotion, ObjectiveC restart, strict pilot hoặc sweep61.
**New/recomputed exact C,w = 0.**
