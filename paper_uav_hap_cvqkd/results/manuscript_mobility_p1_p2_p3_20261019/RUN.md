# Chạy và kiểm tra gói P1/P2/P3

Đứng tại thư mục gốc `2024_dvcvqkd`; dùng Python trong môi trường dự án.
Không dùng Python hệ thống vì thiếu các thư viện số.

```powershell
paper_uav_hap_cvqkd/.venv/Scripts/python.exe -X utf8 -B paper_uav_hap_cvqkd/scripts/run_manuscript_mobility.py --stage verify
```

`verify` đọc artifact đã lưu, xác thực nguồn/hash, coverage, quỹ đạo, metric,
thống kê và hình; không đánh giá lại SKR. Đọc `report_vi.md` để xem kết quả.

Thứ tự chạy đã sử dụng: `audit`, `p1`, `cloud`, `compare`, `export`, `verify`.
`--config` mặc định là `configs/manuscript_mobility.json`; `--output` mặc định
là thư mục gói này. Cấu hình được khóa theo kế hoạch đã duyệt; sửa tham số sẽ
bị từ chối, không được dùng để thay hình học hoặc tìm seed đẹp hơn.

Mỗi stage hoàn tất có receipt bất biến và từ chối ghi đè. P1 có checkpoint
theo hình học; resume chỉ chấp nhận cùng input/scientific identity và hash
record. Record chưa commit vào checkpoint khiến chương trình dừng để bảo toàn
bằng chứng. Không xóa receipt để chạy lại trong thư mục đã hoàn tất.

Startup manifest và receipt kiểm thử được chuẩn bị, kiểm tra trước lượt chạy
này. Một thư mục kết quả mới cần preflight riêng theo AGENTS: ghi Git/diff,
bảo vệ tệp cũ, khóa manuscript/input và chạy kiểm thử có receipt trước P1.
Runner chủ động từ chối một thư mục chưa có startup manifest.

Kiểm thử mã mới (fixture hình là dữ liệu tổng hợp trong thư mục tạm):

```powershell
cd paper_uav_hap_cvqkd
.venv/Scripts/python.exe -X utf8 -B -m unittest discover -s tests -p 'test_manuscript_mobility*.py' -v
.venv/Scripts/python.exe -X utf8 -B -m unittest discover -s tests -p test_binary_cloud.py -v
```

Không có AP/AO hoặc nguồn C,w mới. Không truy cập training/test/final-test/
held-out; không sửa manuscript ngoài repo, production evaluator, frozen spec,
cache hoặc kết quả cũ. Giữ UNVALIDATED_SECURITY_MODEL và
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Producer snapshot của từng stage và
input manifest ghi đúng phiên bản đã thực thi; các stage sau có thể có
producer khác khi chỉ sửa orchestration/kiểm chứng, còn scientific identity
phải giữ nguyên.
