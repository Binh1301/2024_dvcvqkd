# Phase5E — chuẩn bị full lookup, chờ phê duyệt riêng

**Trạng thái: NOT_RUN_PENDING_EXPLICIT_PHASE5E_APPROVAL.** Mục0 trong yêu cầu
tác giả quy định không chạy full computation trước khi có xác nhận Phase5E
rõ ràng. Chưa có xác nhận đó hoặc approval file tương ứng. Không suy việc
gửi bản task có điều kiện này thành phê duyệt; không tạo approval=true thay tác giả.

## Lệnh và input đã chuẩn bị

Chạy từ `uav_cvqkd_optimization/`, **sau khi có phê duyệt và hoàn tất kiểm
equivalence của geometry groups**:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -B -m uav_qkd.lookup_benchmark full `
  --config configs/lookup/phase5d_full_target_radial_2proc.json `
  --output results/phase5d_full_target_radial_2proc_PHASE5E_20261108 `
  --approval-file docs/approvals/phase5e_full_lookup_author_approval.json
```

- Config SHA-256:
  `0671e70ef5a5a78afed6f750859161439153f2030fe6e6b733a216f1f6616111`.
- Candidate pool SHA-256:
  `adb057572d5b22be1718bb7535e402129b16af813cc863d2e62b2028c0c36539`.
- Prepared executor SHA-256:
  `d1fecdae1f2b53dbe58288524b53ea06b7abef3a33edc9722336441304955dbb`.
- Requested mode: radial_exact,2 workers, đủ212 candidates/group. Output là
  namespace mới, chưa tạo; tên bắt đầu phase5d_ để dùng nguyên prepared executor.
- Sáu physical/noise values đã đối chiếu: .30m/35µrad/1.561µrad/.10m,
  detector.005 và channel.0136SNU. Native protocol, geometry/pool và optimized
  setup hashes khớp config; executor khớp hash đã ghi ở Phase5D.
- Gate legacy của prepared executor dùng scope `PHASE5D_FULL_LOOKUP`; approval
  file tương lai cần ghi rõ đây là tác giả cho phép **Phase5E**, đồng thời bind
  đúng scope/config/pool theo contract đó. Hiện file chưa tồn tại.

Machine-readable preparation:
[phase5e_execution_preparation.json](phase5e_execution_preparation.json).

## Những việc chưa được thực hiện

Chưa chạy evaluator, chưa tạo output lookup, chưa thực hiện full geometry
equivalence audit hoặc direct recomputation của Phase5E. Các số2601/294/62328
hiện là planned workload từ evidence Phase5D, không phải completion counts mới.
Trước execution phải kiểm đầy đủ physical inputs/azimuth invariance, dùng exact
keys, lưu mapping2601 positions; vị trí không equivalent phải được tách riêng.
Không dùng clear-sky deduplication cho dynamic cloud.

Sau khi được phép chạy mới có thể báo actual completion/evaluation counts,
runtime/memory, min/max/mean raw SKR, MB-vs-Uniform selection, VA/nu distribution,
five-pilot reproduction và independent direct-check results. Chưa kết luận
lookup mới ready cho dynamic solver khi chưa có dữ liệu và validation đó.

Không có test suite mới vì lượt này chỉ kiểm input hashes/chuẩn bị lệnh và
ghi trạng thái pending. Không sửa Z/w, MB/Holevo, rotor, `paper.yaml`, historical
lookup/pilot hoặc figures; không đổi evidence/readiness, paper-mode, commit/push.
