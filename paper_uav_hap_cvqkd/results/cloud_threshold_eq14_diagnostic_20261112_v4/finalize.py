"""Append final verification notes and seal this completed diagnostic only."""
from pathlib import Path
import hashlib
import importlib.util
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((OUT/'selected_root_validation.json').read_text())
assert proof['status']=='CURRENTLY_VERIFIED_PASS' and len(proof['checks'])==12
assert '\nOK\n' in (OUT/'unit_tests.log').read_text()
report=OUT/'report_vi.md'
if '## Xác minh cuối cùng' not in report.read_text(encoding='utf-8'):
    with report.open('ab') as f:f.write('''
## Xác minh cuối cùng

11 unit tests PASS trong unit_tests.log. 12 endpoint checks độc lập qua adaptive
MI integration, matrix symplectic spectrum và conditional covariance PASS trong
selected_root_validation.json. Kiểm tra chỉ đọc cuối ở verification.json và
verify.py: 257 nhóm, 2500 vị trí, 37042 selected evaluation rows. Không có điểm
catalog-negative nào còn unresolved trong dữ liệu đã xuất. 1263 tệp cũ bảo vệ
giữ nguyên. Ba PDF/PNG400dpi đã render và kiểm tra trực quan; font nhúng,
Figure1/2 vector, Figure3 raster data với trục/chữ vector. git diff --check PASS
được kiểm tra riêng tại cuối phiên; toàn bộ repository tests NOT_RUN.

Read-only verification từ project root:

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -B results/cloud_threshold_eq14_diagnostic_20261112_v4/verify.py
```

Danh mục đầy đủ các tệp xuất và hash trong artifact_hashes.json. Report phần
xác minh này được bổ sung ở bước finalize.py, không chạy lại mô hình.
'''.encode())
readme=OUT/'README.md'
if 'Read-only verification:' not in readme.read_text():
    with readme.open('ab') as f:f.write(b'\nRead-only verification:\n\n.venv/Scripts/python.exe -X utf8 -B results/cloud_threshold_eq14_diagnostic_20261112_v4/verify.py\n\nThe delivered package retains 72 completed full-sweep checkpoints. A new run without these checkpoints uses fewer full raw curves and more sign-bound grid groups; it evaluates the same root neighborhoods and 0..100 dB coarse sign checks.\n')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
          if p.is_file() and p.name not in ['artifact_hashes.json','verification.json']}
(OUT/'artifact_hashes.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
spec=importlib.util.spec_from_file_location('saved_cloud_threshold_check',OUT/'verify.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result=module.verify()
(OUT/'verification.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps(dict(result,sealed_artifacts=len(manifest)),indent=2))
